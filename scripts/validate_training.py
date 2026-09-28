"""Check committed training data, source hashes, and train/validation/eval isolation."""
import collections
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_training import MANIFEST,source_blob
from validate import check_collection

def load(path):
    rows=[]
    for number,line in enumerate(path.read_text(encoding='utf-8').split('\n'),1):
        if line.strip():
            try:rows.append(json.loads(line))
            except ValueError as exc:raise ValueError(f'{path}:{number}: {exc}') from exc
    return rows

def main():
    errors=[];training=[]
    for entry in MANIFEST['files']:
        try:source_blob(entry)
        except (OSError,ValueError,KeyError) as exc:errors.append(str(exc))
    for path in sorted((ROOT/'training/data').glob('*/*/*.jsonl')):
        split,kind=path.parts[-3:-1]
        for row in load(path):
            if row['metadata']['split']!=split or row['task_type']!=kind:
                errors.append(f'Path/split/type mismatch: {path.name}, {row.get("id")}')
            training.append(row)
    eval_rows=[r for path in (ROOT/'data').glob('*/*.jsonl') for r in load(path)]
    errors.extend(str(e) for e in check_collection(eval_rows+training))
    source_info={e['source_id']:e for e in MANIFEST['files']}
    for row in training:
        m=row['metadata'];entry=source_info.get(m['source_id'])
        if entry is None or m['source_revision']!=entry['source_revision'] or m['license']!=entry['license']:
            errors.append('Source metadata mismatch: '+row['id'])
        if m['review']['status']!='pending':errors.append('Unexpected acceptance status: '+row['id'])
        if m['source_id']=='typed-decisions' and m['label_origin_kind']!='teacher_model':
            errors.append('Typed teacher label misclassified: '+row['id'])
    by_group=collections.defaultdict(list)
    for row in training:
        if row['metadata']['source_id']=='typed-decisions':by_group[row['metadata']['group_id']].append(row)
    for key,rows in by_group.items():
        if len(rows)!=5 or len({r['metadata']['split'] for r in rows})!=1:
            errors.append('Typed case split/size mismatch: '+key)
    counts=collections.Counter((r['metadata']['split'],r['task_type']) for r in training)
    report={'records':len(training),'train':sum(v for (s,_),v in counts.items() if s=='train'),
            'validation':sum(v for (s,_),v in counts.items() if s=='validation'),
            'by_split_type':{s:{k:counts[(s,k)] for k in ('choice','noul','score')} for s in ('train','validation')},
            'source_snapshots_checked':len(MANIFEST['files']),'typed_cases_checked':len(by_group),
            'eval_records_compared':len(eval_rows),'automatic_checks_passed':not errors,'errors':errors[:30],
            'human_review_complete':False,
            'note':'Checks exact normalized input and group overlap, structure, and source hashes. Semantic near-duplicate and label review remain.'}
    expected=json.loads((ROOT/'training/reports/build.json').read_text(encoding='utf-8'))
    if report['by_split_type']!=expected['by_split_type']:
        report['errors'].append('Counts differ from build report');report['automatic_checks_passed']=False
    target=ROOT/'training/reports/validation.json'
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if not report['automatic_checks_passed']:raise SystemExit(1)

if __name__=='__main__':main()
