"""Rebuild single-turn train/validation records from committed source snapshots.

Requires pyarrow only to read the pinned typed-decisions Parquet source.
No evaluation file is used as a training label or modified by this script.
"""
import collections
import gzip
import hashlib
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from chunked_jsonl import write_rows
from prepare_extended import OUT,make,state_text
from validate import check_collection

MANIFEST=json.loads((ROOT/'training/source_manifest.json').read_text(encoding='utf-8'))
JEVIFY=json.loads((ROOT/'sources/jevify/manifest.json').read_text(encoding='utf-8'))['sources']

def digest(blob):return hashlib.sha256(blob).hexdigest()

def source_blob(entry):
    pieces=[]
    for part in entry['parts']:
        blob=(ROOT/part['path']).read_bytes()
        if digest(blob)!=part['sha256']:raise ValueError('Source part hash mismatch: '+part['path'])
        pieces.append(blob)
    joined=b''.join(pieces)
    if digest(joined)!=entry['stored_sha256']:raise ValueError('Stored snapshot hash mismatch: '+entry['source_id'])
    raw=gzip.decompress(joined) if entry['compression']=='gzip' else joined
    if digest(raw)!=entry['snapshot_sha256']:raise ValueError('Source snapshot hash mismatch: '+entry['source_id'])
    return raw

def prepare_jevify(entry):
    config=entry['config'];split=entry['upstream_split'];meta=JEVIFY[config]
    blob=source_blob(entry)
    lines=[line for line in blob.decode('utf-8').split('\n') if line.strip()]
    if len(lines)!=entry['selected_rows']:raise ValueError('Selected source row count changed')
    for line in lines:
        row=json.loads(line,strict=False)
        if row['split']!=split or row['source']!=config:raise ValueError('Source split/config mismatch')
        kind=row['primitive'];question=json.loads(row['question']);state=json.loads(row['state'])
        soft=json.loads(row['soft_label']) if row.get('soft_label') is not None else None
        label=(str(row['label']).lower() in ('1','true','yes')) if kind=='noul' else float(row['label']) if kind=='score' else row['label']
        make(id='jevify/'+row['id'],kind=kind,state=state,question=question,label=label,
             source_id='jevify-'+config,source_url=entry['source_url'],revision=entry['source_revision'],
             sample_id=row['id'],group_id='jevify/'+row['id'],license=entry['license'],
             label_origin='Upstream dataset annotation; group review pending.',family=meta['task_family'],
             original_split=split,split=split,
             transform='Pinned Jevify row; parsed JSON-encoded state/question; preserved label and available human vote distribution.',
             distribution=soft,distribution_source='Human rater vote shares reported by jev-bench; config '+config if soft is not None else None)

def prepare_typed(entry):
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:raise SystemExit('Install pyarrow to rebuild typed-decisions training records') from exc
    rows=pq.read_table(pa.BufferReader(source_blob(entry))).to_pylist()
    if len(rows)!=entry['selected_rows']:raise ValueError('Typed source row count changed')
    eval_states={normalized(r['input']['state']) for p in (ROOT/'data').glob('*/*.jsonl')
                 for line in p.read_text(encoding='utf-8').split('\n') if line.strip() for r in [json.loads(line)]}
    by_workflow=collections.defaultdict(list);excluded_eval=0
    for row in rows:
        if row['split']!='train':raise ValueError('Unexpected typed source split')
        state=json.loads(row['state'])
        if normalized(state_text(state)) in eval_states:excluded_eval+=1;continue
        by_workflow[row['workflow']].append(row)
    selected={};validation_states=set()
    for workflow,items in sorted(by_workflow.items()):
        items.sort(key=lambda row:(digest(row['id'].encode('utf-8')),row['id']))
        if len(items)<60:raise ValueError('Not enough typed cases for validation: '+workflow)
        for row in items[:60]:
            selected[row['id']]='validation'
            validation_states.add(normalized(state_text(json.loads(row['state']))))
        for row in items[60:]:selected[row['id']]='train'
    excluded_validation=0
    for row in rows:
        split=selected.get(row['id'])
        if split is None:continue
        state=json.loads(row['state'])
        if split=='train' and normalized(state_text(state)) in validation_states:
            excluded_validation+=1;continue
        questions=json.loads(row['questions']);golds=json.loads(row['gold'])
        if len(questions)!=5:raise ValueError('Typed case no longer has five questions')
        for qid,q in questions.items():
            g=golds[qid];kind=q['type']
            label=(str(g['label']).lower()=='true') if kind=='noul' else float(g['score']) if kind=='score' else g['label']
            dist=g.get('probabilities')
            if dist is not None:
                dist={str(k):float(v) for k,v in dist.items()}
                total=sum(dist.values())
                dist={k:v/total for k,v in dist.items()}
            make(id='typed-decisions/'+row['id']+'/'+qid,kind=kind,state=state,question=q,label=label,
                 source_id='typed-decisions',source_url=entry['source_url'],revision=entry['source_revision'],
                 sample_id=row['id']+'/'+qid,group_id='typed-decisions/'+row['id'],license=entry['license'],
                 label_origin='Teacher-model reference; mean of three sampled model distributions, not human ground truth',
                 family=row['workflow'],original_split='train',split=split,
                 transform='Official train case split by stable case-ID hash; five questions share group_id; teacher distribution retained separately.',
                 distribution=dist,distribution_source='Three-sample teacher-model mean from LocalLLaMA/typed-decisions',
                 label_origin_kind='teacher_model')
    return {'cases_by_workflow':{k:len(v) for k,v in by_workflow.items()},'excluded_eval_overlap':excluded_eval,
            'excluded_validation_state_overlap':excluded_validation,
            'validation_cases':sum(1 for v in selected.values() if v=='validation')}

def normalized(text):return ' '.join(text.split()).casefold()

def main():
    OUT.clear()
    typed_report={}
    for entry in MANIFEST['files']:
        if entry['source_id']=='typed-decisions':typed_report=prepare_typed(entry)
        else:prepare_jevify(entry)
    records=[r for rows in OUT.values() for r in rows]
    eval_rows=[json.loads(line) for p in (ROOT/'data').glob('*/*.jsonl')
               for line in p.read_text(encoding='utf-8').split('\n') if line.strip()]
    errors=check_collection(eval_rows+records)
    if errors:raise ValueError('Training/eval validation failed: '+json.dumps(errors[:5],ensure_ascii=False))
    grouped=collections.defaultdict(list)
    for record in records:
        m=record['metadata'];grouped[(m['split'],record['task_type'],m['source_id'])].append(record)
    for (split,kind,source_id),rows in grouped.items():
        path=ROOT/'training/data'/split/kind/(source_id+'.jsonl')
        write_rows(path,(json.dumps(row,ensure_ascii=False) for row in rows))
    counts=collections.Counter((r['metadata']['split'],r['task_type']) for r in records)
    report={'records':len(records),'by_split_type':{split:{kind:counts[(split,kind)] for kind in ('choice','noul','score')}
                                                 for split in ('train','validation')},
            'by_source':dict(collections.Counter(r['metadata']['source_id'] for r in records)),
            'label_origin_kind':dict(collections.Counter(r['metadata']['label_origin_kind'] for r in records)),
            'typed_decisions':typed_report,'cross_split_or_eval_errors':errors,
            'automatic_checks_passed':True,'human_review_complete':False,
            'note':'No model training or human label review performed. Exact normalized state/group checks only; semantic near-duplicates may remain.'}
    path=ROOT/'training/reports/build.json';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
