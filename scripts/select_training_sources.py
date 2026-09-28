"""Freeze a small, decontaminated subset of pinned Jevify train/validation files.

Download the pinned upstream files to .local/train_downloads first. The full files
stay local; committed source snapshots contain only selected rows and their hashes.
"""
import hashlib
import gzip
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOWNLOAD=ROOT/'.local/train_downloads'
DEST=ROOT/'training/sources'
CONFIGS=('banking77','go_emotions','boolq','helpsteer2_helpfulness','measuring_hate_speech')
LIMIT=200_000
CAP=2_000

def digest(blob):return hashlib.sha256(blob).hexdigest()

def normalized(value):
    if not isinstance(value,str):value=json.dumps(value,ensure_ascii=False,sort_keys=True)
    return ' '.join(value.split()).casefold()

def source_state(row):return normalized(json.loads(row['state']))

def raw_rows(path):
    for line in path.read_bytes().split(b'\n'):
        if line.strip():
            line=line.removesuffix(b'\r')
            yield json.loads(line),line

def write_parts(base,blob,raw_jsonl):
    base.parent.mkdir(parents=True,exist_ok=True)
    if raw_jsonl:
        units=[line+b'\n' for line in blob.split(b'\n') if line]
        chunks=[];chunk=b''
        for unit in units:
            if len(unit)>LIMIT:raise ValueError(f'Oversized row: {base}')
            if chunk and len(chunk)+len(unit)>LIMIT:chunks.append(chunk);chunk=b''
            chunk+=unit
        if chunk:chunks.append(chunk)
    else:chunks=[blob[i:i+LIMIT] for i in range(0,len(blob),LIMIT)]
    parts=[]
    for index,piece in enumerate(chunks):
        path=base.with_name(base.stem+f'-part{index:03d}'+base.suffix)
        path.write_bytes(piece)
        parts.append({'path':path.relative_to(ROOT).as_posix(),'sha256':digest(piece),'bytes':len(piece)})
    for old in base.parent.glob(base.stem+'-part[0-9][0-9][0-9]'+base.suffix):
        if old.relative_to(ROOT).as_posix() not in {p['path'] for p in parts}:old.unlink()
    if b''.join((ROOT/p['path']).read_bytes() for p in parts)!=blob:raise RuntimeError('Snapshot mismatch')
    return parts

def main():
    prior=json.loads((ROOT/'sources/extended_manifest.json').read_text(encoding='utf-8'))
    meta=json.loads((ROOT/'sources/jevify/manifest.json').read_text(encoding='utf-8'))['sources']
    downloads={e['path']:e for e in json.loads((DOWNLOAD/'download_manifest.json').read_text(encoding='utf-8'))}
    eval_states={normalized(r['input']['state']) for p in (ROOT/'data').glob('*/*.jsonl')
                 for line in p.read_text(encoding='utf-8').split('\n') if line.strip() for r in [json.loads(line)]}
    chosen={};stats={};validation_states=set()
    for config in CONFIGS:
        path=DOWNLOAD/'data'/config/'validation.jsonl'
        source=f'data/{config}/validation.jsonl'
        full=path.read_bytes()
        if digest(full)!=downloads[source]['sha256']:raise ValueError('Download hash changed: '+source)
        eligible=[];excluded_eval=excluded_duplicate=0
        for row,line in raw_rows(path):
            state=source_state(row)
            if state in eval_states:excluded_eval+=1;continue
            if state in validation_states:excluded_duplicate+=1;continue
            validation_states.add(state);eligible.append((row,line))
        chosen[(config,'validation')]=eligible
        stats[(config,'validation')]={'excluded_eval_overlap':excluded_eval,'excluded_duplicate_state':excluded_duplicate}
    training_states=set()
    for config in CONFIGS:
        path=DOWNLOAD/'data'/config/'train.jsonl'
        source=f'data/{config}/train.jsonl'
        full=path.read_bytes()
        if digest(full)!=downloads[source]['sha256']:raise ValueError('Download hash changed: '+source)
        candidates=[];excluded_eval=excluded_validation=excluded_duplicate=0
        for row,line in raw_rows(path):
            state=source_state(row)
            if state in eval_states:excluded_eval+=1;continue
            if state in validation_states:excluded_validation+=1;continue
            candidates.append((row,line,state))
        candidates.sort(key=lambda item:(digest(item[0]['id'].encode('utf-8')),item[0]['id']))
        selected=[]
        for row,line,state in candidates:
            if state in training_states:excluded_duplicate+=1;continue
            training_states.add(state);selected.append((row,line))
            if len(selected)==CAP:break
        if len(selected)<CAP:raise ValueError('Not enough eligible training rows: '+config)
        chosen[(config,'train')]=selected
        stats[(config,'train')]={'excluded_eval_overlap':excluded_eval,'excluded_validation_overlap':excluded_validation,'excluded_duplicate_state_before_cap':excluded_duplicate}
    files=[]
    for config in CONFIGS:
        for split in ('train','validation'):
            source=f'data/{config}/{split}.jsonl'
            rows=chosen[(config,split)]
            blob=b''.join(line+b'\n' for _,line in rows)
            packed=gzip.compress(blob,compresslevel=9,mtime=0)
            folder=DEST/'jevify'/config
            parts=write_parts(folder/(split+'.jsonl.gz'),packed,False)
            for obsolete in folder.glob(split+'-part[0-9][0-9][0-9].jsonl'):
                obsolete.unlink()
            files.append({'source_id':'jevify-'+config,'config':config,'upstream_split':split,
                          'source_url':downloads[source]['url'],'source_revision':prior['jevify_revision'],
                          'full_source_sha256':downloads[source]['sha256'],'full_source_rows':downloads[source]['lines'],
                          'selected_rows':len(rows),'snapshot_sha256':digest(blob),'stored_sha256':digest(packed),
                          'compression':'gzip','parts':parts,
                          'license':meta[config]['license'],**stats[(config,split)]})
    typed_source='all/train-00000-of-00001.parquet'
    typed=(DOWNLOAD/typed_source).read_bytes()
    if digest(typed)!=downloads[typed_source]['sha256']:raise ValueError('Typed download hash changed')
    parts=write_parts(DEST/'typed-decisions/train.parquet',typed,False)
    files.append({'source_id':'typed-decisions','config':'all','upstream_split':'train',
                  'source_url':downloads[typed_source]['url'],'source_revision':prior['typed_revision'],
                  'full_source_sha256':digest(typed),'selected_rows':1200,'snapshot_sha256':digest(typed),
                  'stored_sha256':digest(typed),'compression':'none','parts':parts,
                  'license':'Apache-2.0','label_origin_kind':'teacher_model'})
    manifest={'schema_version':'1','selection':'SHA-256 sort of source row ID, first 2,000 eligible train rows per Jevify config; all eligible official validation rows; exact normalized state exclusion against committed eval and between train/validation; typed cases split by workflow in build_training.py.',
              'files':files}
    (ROOT/'training/source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for entry in files:print(entry['source_id'],entry['upstream_split'],entry['selected_rows'],entry.get('excluded_eval_overlap',0))

if __name__=='__main__':main()
