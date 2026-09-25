"""Normalize frozen, locally staged public evaluation sets. Requires pyarrow for typed-decisions."""
import collections
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from chunked_jsonl import write_rows

ROOT=Path(__file__).resolve().parents[1]
S=ROOT/'sources'
LOCK=json.loads((S/'extended_manifest.json').read_text(encoding='utf-8'))
OUT=collections.defaultdict(list)
PARTS={entry['path']:entry.get('parts') for entry in LOCK['files']}

def source_bytes(path):
    if path.exists():return path.read_bytes()
    relative=path.relative_to(ROOT).as_posix()
    parts=PARTS.get(relative)
    if not parts:raise FileNotFoundError(path)
    return b''.join((ROOT/p['path']).read_bytes() for p in parts)

def lines(path):
    buffer=''
    for line in source_bytes(path).decode('utf-8').splitlines(keepends=True):
        buffer+=line
        try:
            row=json.loads(buffer,strict=False)
        except json.JSONDecodeError:
            continue
        yield row
        buffer=''
    if buffer.strip():raise ValueError('Unparsed trailing JSON record in '+str(path))

def state_text(value):
    return value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,sort_keys=True)

def make(*,id,kind,state,question,label,source_id,source_url,revision,sample_id,group_id,license,label_origin,family,language='en',original_split='test',transform='Wrapped original state and question.',distribution=None,distribution_source=None,label_origin_kind='source_annotation'):
    q=dict(question)
    q['type']=kind
    q['instructions']=str(q.get('instructions') or '').strip()
    if kind=='choice':
        q['criteria']={str(k):str(k if v is None else v) for k,v in q['criteria'].items()}
        label=str(label)
    elif kind=='noul':
        q['criteria']={str(k):str(v) for k,v in q.get('criteria',{'true':'The answer is yes.','false':'The answer is no.'}).items()}
        label=bool(label)
    elif kind=='score':
        q['criteria']=[str(v) for v in q['criteria']]
        label=float(label)
    gold={'label':label}
    if distribution is not None:
        if kind=='score' and isinstance(distribution,list):distribution={str(i):float(v) for i,v in enumerate(distribution)}
        elif kind=='noul' and isinstance(distribution,(float,int)):distribution={'true':float(distribution),'false':1-float(distribution)}
        distribution={str(k):float(v) for k,v in distribution.items()}
        gold.update(distribution=distribution,distribution_source=distribution_source)
    r={'schema_version':'0.1','id':id,'task_type':kind,'input':{'state':state_text(state),'questions':{'q':q}},'gold':{'q':gold},'metadata':{
        'source_id':source_id,'source_url':source_url,'source_revision':revision,'source_sample_id':str(sample_id),'group_id':str(group_id),
        'split':'eval','original_split':original_split,'license':license,'label_origin':label_origin,'label_origin_kind':label_origin_kind,'family':family,'language':language,
        'transformation':transform,'review':{'status':'pending','reviewers':[],'note':'Imported source label; local human verification pending.'}}}
    OUT[(kind,source_id)].append(r)

def prepare_jevify():
    manifest=json.loads((S/'jevify/manifest.json').read_text(encoding='utf-8'))['sources']
    rev=LOCK['jevify_revision']
    for config in sorted(p.name for p in (S/'jevify').iterdir() if p.is_dir()):
        meta=manifest[config]
        path=S/'jevify'/config/'test.jsonl'
        url=f'https://huggingface.co/datasets/Praveenrajus/jev-bench/blob/{rev}/data/{config}/test.jsonl'
        for row in lines(path):
            kind=row['primitive'];q=json.loads(row['question']);state=json.loads(row['state'])
            soft=json.loads(row['soft_label']) if row.get('soft_label') is not None else None
            if kind=='noul':label=str(row['label']).lower() in ('1','true','yes')
            elif kind=='score':label=float(row['label'])
            else:label=row['label']
            source_id='jevify-'+config
            make(id='jevify/'+row['id'],kind=kind,state=state,question=q,label=label,source_id=source_id,source_url=url,revision=rev,
                sample_id=row['id'],group_id='jevify/'+row['id'],license=meta['license'],label_origin='Upstream dataset label; see manifest for source annotation process.',
                family=meta['task_family'],original_split=row['split'],transform='Parsed JSON-encoded state/question; converted label to typed gold; filled absent choice descriptions with option names and absent binary criteria with generic yes/no descriptions.',
                distribution=soft,distribution_source='Human rater vote shares reported by jev-bench; source config '+config if soft is not None else None)

def prepare_frontier():
    rev=LOCK['frontier_revision'];p=S/'jev-frontier-100/items.jsonl';url=f'https://github.com/softpudding/jev-frontier-100/blob/{rev}/data/items.jsonl'
    for row in lines(p):
        options={k:str(v).replace('_',' ') for k,v in row['options'].items()}
        q={'type':'choice','instructions':row['question'],'criteria':options}
        make(id='frontier100/'+row['id'],kind='choice',state=row['state'],question=q,label=row['answer'],source_id='frontier100',source_url=url,revision=rev,
             sample_id=row['id'],group_id='frontier100/'+row['pair_id'],license='MIT',label_origin='Author-generated synthetic oracle',family=row['domain'],original_split='test',
             transform='Mapped A-D option codes and underscored option names to written criteria; kept pair_id for paraphrase grouping.',label_origin_kind='synthetic_author')

def prepare_feishu():
    rev=LOCK['laya_revision'];p=S/'laya-feishu/cases.jsonl';url=f'https://github.com/NandhaKishorM/laya/blob/{rev}/research/benchmarks/feishu_zh/data/cases.jsonl'
    sys.path.insert(0,str(S/'laya-feishu'))
    from prompts import requests_for
    for row in lines(p):
        request=requests_for(row)['choice'];qid=next(iter(request['questions']))
        make(id='laya-feishu/'+row['id'],kind='choice',state=request['state'],question=request['questions'][qid],label=row['expected'],source_id='laya-feishu',
             source_url=url,revision=rev,sample_id=row['id'],group_id='laya-feishu/'+row['id'],license='MIT (benchmark subdirectory)',
             label_origin='AI-assisted synthetic reference label, frozen in upstream case',family=row['family'],language='zh',
             transform='Reconstructed frozen prompt using the pinned upstream prompts.py; serialized state object without including rationale.',label_origin_kind='synthetic_author')

def prepare_typed():
    try:import pyarrow.parquet as pq
    except ImportError as exc:raise SystemExit('typed-decisions conversion requires pyarrow (pip install pyarrow)') from exc
    rev=LOCK['typed_revision'];url=f'https://huggingface.co/datasets/LocalLLaMA/typed-decisions/blob/{rev}/all/test-00000-of-00001.parquet'
    for row in pq.read_table(S/'typed-decisions/test.parquet').to_pylist():
        qs=json.loads(row['questions']);golds=json.loads(row['gold']);state=json.loads(row['state'])
        for qid,q in qs.items():
            kind=q['type'];g=golds[qid]
            if kind=='noul':label=str(g['label']).lower()=='true'
            elif kind=='score':label=float(g['score'])
            else:label=g['label']
            dist=g.get('probabilities')
            if dist is not None:
                dist={k:float(v) for k,v in dist.items()}
                total=sum(dist.values())
                dist={k:v/total for k,v in dist.items()}
            make(id='typed-decisions/'+row['id']+'/'+qid,kind=kind,state=state,question=q,label=label,source_id='typed-decisions',source_url=url,revision=rev,
                 sample_id=row['id']+'/'+qid,group_id='typed-decisions/'+row['id'],license='Apache-2.0',
                 label_origin='Teacher-model reference; mean of three sampled model distributions, not human ground truth',family=row['workflow'],
                 transform='Split five-question case into one-question records sharing group_id; parsed JSON strings; used expected score for score type; retained teacher distribution separately from label.',
                 distribution=dist,distribution_source='Three-sample teacher-model mean from LocalLLaMA/typed-decisions',label_origin_kind='teacher_model')

def prepare_eve():
    url='https://github.com/anthony-maio/eve-rlcd/releases/tag/data-v1'
    licenses={'bitext':'CDLA-Sharing-1.0','banking77':'CC-BY-4.0','boolq':'CC-BY-SA-3.0','triage':'MIT, author-generated synthetic'}
    source_rev={'bitext':'430d1a89bd93bd1fa23c16f29dd53e73f0087443','banking77':'f54121560de48f2852f90be299010d1d6dc612ec','boolq':'35b264d03638db9f4ce671b711558bf7ff0f80d5','triage':LOCK['decision_revision']}
    skipped=collections.Counter()
    for row in lines(S/'eve-rlcd/test-permitted.jsonl'):
        kind=row['primitive'];choices=row['choices'];answer=row['answer'];source=row['source']
        if kind=='score' and ('None of the above' in choices or not row['ordered']):
            skipped['score_with_nota_or_unordered']+=1;continue
        if answer is None or not isinstance(answer,int) or not 0<=answer<len(choices):
            skipped['unlabeled_or_invalid']+=1;continue
        if kind=='choice':
            # The source selects a variable number of candidates per item, so preserve index identity.
            crit={'option_'+str(i):v.replace('_',' ') for i,v in enumerate(choices)};label='option_'+str(answer)
        elif kind=='noul':
            crit={'true':'The answer to the question is yes.','false':'The answer to the question is no.'}
            label=str(choices[answer]).lower()=='true'
        else:
            crit=choices;label=answer
        q={'type':kind,'instructions':row['question'],'criteria':crit}
        sample=row['id'];parent=sample.rsplit('-',1)[0] if source=='triage' else sample
        make(id='eve-rlcd/'+sample,kind=kind,state=row['context'],question=q,label=label,source_id='eve-rlcd-'+source,source_url=url,revision='data-v1',
             sample_id=sample,group_id='eve-rlcd/'+parent,license=licenses[source],label_origin='Upstream source label, or code-generated label for triage',family=source,
             transform='Kept original candidate order; generated stable option-index keys for variable choice lists; excluded score with NOTA.',original_split='test',label_origin_kind='synthetic_code' if source=='triage' else 'source_annotation')
    print('Eve exclusions:',dict(skipped))

def prepare_decision():
    root=S/'jev-decision-bench'; rev=LOCK['decision_revision']
    # Pinned self-contained code-derived probes. The source files were inspected before execution.
    for name in ('probes_fresh_math.py','probes_known_weakness.py'):
        subprocess.run([sys.executable,str(root/'builders'/name)],cwd=root,check=True,timeout=40)
    for path in sorted((root/'tasks').glob('*.json')):
        task=json.loads(path.read_text(encoding='utf-8'))
        for item in task['items']:
            q=item.get('questions',{}).get('q',task.get('question'))
            if q is None:raise ValueError('Missing question in '+str(path))
            label=item['gold']['q'] if isinstance(item['gold'],dict) else item['gold']
            kind=q['type']
            make(id='decision-bench/'+task['id']+'/'+item['id'],kind=kind,state=item['state'],question=q,label=label,
                 source_id='decision-bench-'+task['id'],source_url=f'https://github.com/OmarMujahid/jev-decision-bench/tree/{rev}/builders',revision=rev,
                 sample_id=item['id'],group_id='decision-bench/'+task['id']+'/'+item['id'],license='MIT',
                 label_origin='Code-generated reference answer with pinned seed; not human annotated',family=task['id'],
                 transform='Executed pinned deterministic generator inside this repository; serialized state and wrapped single question.',label_origin_kind='synthetic_code')

def main():
    for f in LOCK['files']:
        p=ROOT/f['path'];assert hashlib.sha256(source_bytes(p)).hexdigest()==f['sha256'],f'Hash mismatch: {p}'
    prepare_jevify();prepare_frontier();prepare_feishu();prepare_typed();prepare_eve();prepare_decision()
    for (kind,source_id),rows in OUT.items():
        p=ROOT/'data'/kind/(source_id+'-eval.jsonl')
        write_rows(p,(json.dumps(r,ensure_ascii=False) for r in rows))
    print('Extended records:',sum(map(len,OUT.values())))
    print('By type:',dict(collections.Counter(k for (k,s),v in OUT.items() for _ in v)))
    by_source=collections.Counter()
    for (kind,source_id),rows in OUT.items():by_source[source_id]+=len(rows)
    print('By source:',dict(by_source))

if __name__=='__main__':main()
