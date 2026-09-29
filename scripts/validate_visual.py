"""Check the separate, image-backed VLM evaluation pilot."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'visual'


def main():
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    data = (ROOT / 'clevr_val_pilot.jsonl').read_bytes()
    assert hashlib.sha256(data).hexdigest() == manifest['records_sha256']
    rows = [json.loads(line) for line in data.splitlines()]
    assert len(rows) == 32
    ids, images = set(), set()
    for row in rows:
        assert row['id'] not in ids
        ids.add(row['id'])
        inp, gold, meta = row['input'], row['gold'], row['metadata']
        assert set(inp) == {'image_path', 'question', 'options'}
        assert inp['question'].strip() and len(inp['options']) >= 2
        assert len(inp['options']) == len(set(inp['options']))
        assert gold['label'] in inp['options']
        assert row['task_type'] == ('noul' if inp['options'] == ['yes', 'no'] else 'choice')
        assert meta['split'] == 'eval' and meta['original_split'] == 'val'
        assert meta['review']['status'] == 'pending'
        image = inp['image_path']
        assert image.startswith('images/') and '/' not in image[len('images/'):]
        assert image not in images
        images.add(image)
        assert hashlib.sha256((ROOT / image).read_bytes()).hexdigest() == manifest['image_sha256'][Path(image).name]
    assert images == {'images/' + name for name in manifest['image_sha256']}
    print(f'{len(rows)} VLM records and images passed structural and hash checks; human review pending')


if __name__ == '__main__': main()
