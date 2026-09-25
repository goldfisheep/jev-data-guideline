"""Export only request IDs and model-visible input, keeping gold out of requests."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    output = ROOT / 'exports'
    output.mkdir(exist_ok=True)
    count = 0
    with (output/'requests.jsonl').open('w',encoding='utf-8') as target:
        for source in sorted((ROOT/'data').glob('*/*.jsonl')):
            for line in source.read_text(encoding='utf-8').split('\n'):
                if not line.strip():
                    continue
                r = json.loads(line)
                if r['metadata']['review']['status'] == 'rejected':
                    continue
                target.write(json.dumps({'id':r['id'],'input':r['input']},ensure_ascii=False)+'\n')
                count += 1
    print(f'Exported {count} requests; pilot includes pending human-review samples.')

if __name__=='__main__':
    main()
