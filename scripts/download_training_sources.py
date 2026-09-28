"""Download pinned full source splits into ignored local staging for reproducible selection."""
import concurrent.futures
import hashlib
import json
import time
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'.local/train_downloads'
CONFIGS=('banking77','go_emotions','boolq','helpsteer2_helpfulness','measuring_hate_speech')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    lock=json.loads((ROOT/'sources/extended_manifest.json').read_text(encoding='utf-8'))
    existing=ROOT/'training/source_manifest.json'
    known={e['source_url']:e['full_source_sha256'] for e in json.loads(existing.read_text(encoding='utf-8'))['files']} if existing.exists() else {}
    jobs=[]
    for config in CONFIGS:
        for split in ('train','validation'):
            path=f'data/{config}/{split}.jsonl'
            jobs.append((path,f'https://huggingface.co/datasets/Praveenrajus/jev-bench/resolve/{lock["jevify_revision"]}/{path}'))
    path='all/train-00000-of-00001.parquet'
    jobs.append((path,f'https://huggingface.co/datasets/LocalLLaMA/typed-decisions/resolve/{lock["typed_revision"]}/{path}'))

    def fetch(job):
        path,url=job;dest=OUT/path;dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():
            for attempt in range(4):
                try:
                    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'jev-data-guideline'}),timeout=90) as response:
                        blob=response.read()
                    dest.write_bytes(blob)
                    break
                except Exception:
                    if attempt==3:raise
                    time.sleep(2**attempt)
        blob=dest.read_bytes();sha=hashlib.sha256(blob).hexdigest()
        if url in known and sha!=known[url]:raise ValueError('Pinned source changed: '+path)
        return {'path':path,'url':url,'bytes':len(blob),'sha256':sha,
                'lines':None if path.endswith('.parquet') else len([line for line in blob.split(b'\n') if line.strip()])}

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        records=list(pool.map(fetch,jobs))
    (OUT/'download_manifest.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    for row in records:print(row['path'],row['bytes'],row['sha256'])

if __name__=='__main__':main()
