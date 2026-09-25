"""Download pinned public JevBench data and retain originals. Python 3.10+, stdlib only."""
import hashlib
import json
import urllib.request
from pathlib import Path
from chunked_jsonl import write_rows

ROOT = Path(__file__).resolve().parents[1]
REV = 'f8ce71361165846101d02ebc83ad44e47ae44fc3'
BASE = f'https://raw.githubusercontent.com/fstandhartinger/jevbench/{REV}/'

def main():
    raw = ROOT / 'sources' / 'jevbench'
    raw.mkdir(parents=True, exist_ok=True)
    manifest = []
    old_manifest = ROOT / 'sources/manifest.json'
    old = {e['path']:e for e in json.loads(old_manifest.read_text(encoding='utf-8'))['files']} if old_manifest.exists() else {}
    groups = {t: [] for t in ('choice', 'noul', 'score')}
    for name in ('LICENSE', 'datasets/public/original.jsonl', 'datasets/public/easy.jsonl', 'datasets/public/hard.jsonl'):
        dest = raw / Path(name).name
        if dest.exists():data=dest.read_bytes()
        elif old.get(name,{}).get('parts'):
            data=b''.join((ROOT/p['path']).read_bytes() for p in old[name]['parts'])
        else:
            data = urllib.request.urlopen(BASE + name, timeout=40).read()
            dest.write_bytes(data)
        entry={'path': name, 'url': BASE + name, 'sha256': hashlib.sha256(data).hexdigest()}
        if old.get(name,{}).get('parts'):entry['parts']=old[name]['parts']
        manifest.append(entry)
        if not name.endswith('.jsonl'):
            continue
        for line in data.decode('utf-8').splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            question = row['question']
            kind = question['type']
            label = row['expected']
            if kind == 'noul':
                if label not in ('yes', 'no', True, False):
                    raise ValueError(f'Unknown binary label: {label!r}')
                label = label in ('yes', True)
            elif kind == 'score':
                label = float(label)
            state = row['state'] if isinstance(row['state'],str) else json.dumps(row['state'],ensure_ascii=False,sort_keys=True,indent=2)
            transform = 'Preserve question; yes/no to boolean; score to number; wrap and assign q.'
            transform += ' Preserve string state.' if isinstance(row['state'],str) else ' Serialize structured state as sorted UTF-8 JSON text, preserving all content.'
            record = {
                'schema_version': '0.1', 'id': 'jevbench/' + row['id'],
                'task_type': kind,
                'input': {'state': state, 'questions': {'q': question}},
                'gold': {'q': {'label': label}},
                'metadata': {
                    'source_id': 'jevbench', 'source_url': BASE + name,
                    'source_revision': REV, 'source_sample_id': row['id'],
                    'group_id': 'jevbench/' + (row.get('group') or row['id']), 'split': 'eval',
                    'original_split': row['split'], 'license': row['provenance']['license'],
                    'label_origin': row['provenance']['label_basis'],
                    'family': row['family'], 'language': 'en',
                    'transformation': transform,
                    'review': {'status': 'pending', 'reviewers': [], 'note': 'Upstream label retained; local human review not performed.'}
                }
            }
            groups[kind].append(record)
    for kind, records in groups.items():
        folder = ROOT / 'data' / kind
        folder.mkdir(parents=True, exist_ok=True)
        write_rows(folder/'eval.jsonl',(json.dumps(r,ensure_ascii=False) for r in records))
    (ROOT / 'sources' / 'manifest.json').write_text(json.dumps({'revision': REV, 'files': manifest}, indent=2), encoding='utf-8')
    examples = ROOT / 'examples'
    examples.mkdir(exist_ok=True)
    for kind, records in groups.items():
        (examples/(kind+'.json')).write_text(json.dumps(records[0],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k: len(v) for k,v in groups.items()}))

if __name__ == '__main__':
    main()
