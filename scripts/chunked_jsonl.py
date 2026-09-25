"""Write reproducible JSONL shards small enough for ordinary GitHub API uploads."""
from pathlib import Path

LIMIT=200_000

def write_rows(path:Path,rows):
    encoded=[(row+'\n').encode('utf-8') for row in rows]
    if any(len(row)>LIMIT for row in encoded):raise ValueError(f'JSONL row too large: {path}')
    chunks=[];chunk=b''
    for row in encoded:
        if chunk and len(chunk)+len(row)>LIMIT:
            chunks.append(chunk);chunk=b''
        chunk+=row
    if chunk:chunks.append(chunk)
    targets=[path] if len(chunks)<=1 else [path.with_name(path.stem+f'-part{i:03d}'+path.suffix) for i in range(len(chunks))]
    path.parent.mkdir(parents=True,exist_ok=True)
    for target,blob in zip(targets,chunks):target.write_bytes(blob)
    for old in path.parent.glob(path.stem+'-part[0-9][0-9][0-9]'+path.suffix):
        if old not in targets:old.unlink()
    if path not in targets and path.exists():path.unlink()
    return targets
