"""Summarize source, label and duplicate risks without judging label correctness."""
import collections,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    by_source=collections.Counter();by_type=collections.Counter();by_origin=collections.Counter();groups=set();cross=collections.defaultdict(set)
    by_split=collections.Counter();soft=collections.Counter()
    for p in sorted((ROOT/'data').glob('*/*.jsonl')):
        for line in p.read_text(encoding='utf-8').split('\n'):
            if not line.strip():continue
            r=json.loads(line);m=r['metadata'];source=m['source_id'];by_source[source]+=1;by_type[r['task_type']]+=1
            by_origin[m.get('label_origin_kind','unspecified')]+=1;by_split[m['split']]+=1;groups.add(m['group_id'])
            if 'distribution' in r['gold']['q']:soft[source]+=1
            state=' '.join(r['input']['state'].split()).casefold()
            cross[state].add(source)
    repeated=collections.Counter()
    for srcs in cross.values():
        if len(srcs)>1:
            for source in srcs:repeated[source]+=1
    report={'records':sum(by_source.values()),'by_type':dict(by_type),'by_source':dict(sorted(by_source.items())),
            'by_label_origin_kind':dict(by_origin),'by_split':dict(by_split),'with_distribution_by_source':dict(soft),
            'declared_groups':len(groups),'identical_state_text_shared_across_sources':sum(len(s)>1 for s in cross.values()),
            'sources_in_shared_state_texts':dict(repeated),
            'note':'Exact normalized text only. Multiple questions share one case; semantic paraphrases and source-overlap need human audit.'}
    p=ROOT/'reports/integration_audit.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
