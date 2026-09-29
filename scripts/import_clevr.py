"""Import a small, reproducible CLEVR v1.0 validation pilot using HTTP ranges."""
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://dl.fbaipublicfiles.com/clevr/CLEVR_v1.0.zip'
OUT = ROOT / 'visual'
COLORS = ('gray', 'red', 'blue', 'green', 'brown', 'purple', 'cyan', 'yellow')
SHAPES = ('cube', 'sphere', 'cylinder')


class RangeReader(io.RawIOBase):
    def __init__(self, url, chunk_size=1024 * 1024):
        self.url, self.chunk_size, self.pos, self.cache = url, chunk_size, 0, {}
        with urllib.request.urlopen(urllib.request.Request(url, method='HEAD')) as response:
            self.length = int(response.headers['Content-Length'])
            assert response.headers.get('Accept-Ranges') == 'bytes', 'source lacks HTTP ranges'

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos

    def seek(self, offset, whence=io.SEEK_SET):
        self.pos = (offset if whence == io.SEEK_SET else
                    self.pos + offset if whence == io.SEEK_CUR else self.length + offset)
        return self.pos

    def read(self, size=-1):
        if size < 0: size = self.length - self.pos
        size = min(size, self.length - self.pos)
        result = bytearray()
        while size:
            block = self.pos // self.chunk_size
            if block not in self.cache:
                start = block * self.chunk_size
                end = min(start + self.chunk_size, self.length) - 1
                req = urllib.request.Request(self.url, headers={'Range': f'bytes={start}-{end}'})
                with urllib.request.urlopen(req) as response:
                    assert response.status == 206, 'server ignored range request'
                    self.cache[block] = response.read()
            offset = self.pos % self.chunk_size
            part = self.cache[block][offset:offset + size]
            if not part: raise IOError('short HTTP range response')
            result.extend(part)
            self.pos += len(part)
            size -= len(part)
        return bytes(result)


def options(answer):
    if answer in ('yes', 'no'): return None
    if answer in COLORS: return COLORS
    if answer in SHAPES: return SHAPES
    if answer in ('metal', 'rubber'): return ('metal', 'rubber')
    if answer in ('small', 'large'): return ('small', 'large')
    if answer.isdigit() and 0 <= int(answer) <= 10: return tuple(str(i) for i in range(11))
    raise ValueError(f'unsupported answer: {answer}')


def main():
    reader = RangeReader(URL)
    with zipfile.ZipFile(reader) as archive:
        annotation = 'CLEVR_v1.0/questions/CLEVR_val_questions.json'
        raw_questions = archive.read(annotation)
        questions = json.loads(raw_questions)['questions']
        selected, seen_images = [], set()
        for question in questions:
            image = question['image_filename']
            if image in seen_images: continue
            answer = str(question['answer']).lower()
            opts = options(answer)
            selected.append((question, answer, opts))
            seen_images.add(image)
            if len(selected) == 32: break
        assert len(selected) == 32
        (OUT / 'images').mkdir(parents=True, exist_ok=True)
        rows, image_hashes = [], {}
        for q, answer, opts in selected:
            image_name = q['image_filename']
            image_bytes = archive.read('CLEVR_v1.0/images/val/' + image_name)
            image_hashes[image_name] = hashlib.sha256(image_bytes).hexdigest()
            (OUT / 'images' / image_name).write_bytes(image_bytes)
            kind = 'noul' if opts is None else 'choice'
            rows.append({
                'id': 'clevr-val/' + str(q['question_index']),
                'task_type': kind,
                'input': {'image_path': 'images/' + image_name,
                          'question': q['question'],
                          'options': list(opts) if opts else ['yes', 'no']},
                'gold': {'label': answer},
                'metadata': {'source_id': 'clevr-v1.0', 'source_url': URL,
                             'source_sample_id': str(q['question_index']),
                             'group_id': 'clevr-val/' + image_name,
                             'original_split': 'val', 'split': 'eval',
                             'license': 'CC BY 4.0', 'label_origin': 'program_generated',
                             'review': {'status': 'pending', 'reviewers': []}}
            })
    output = '\n'.join(json.dumps(r, ensure_ascii=False) for r in rows) + '\n'
    (OUT / 'clevr_val_pilot.jsonl').write_bytes(output.encode('utf-8'))
    manifest = {'source_url': URL, 'source_version': 'CLEVR v1.0',
                'archive_content_length': reader.length,
                'annotation_path': annotation,
                'annotation_sha256': hashlib.sha256(raw_questions).hexdigest(),
                'selection': 'first question for each of the first 32 validation images',
                'image_sha256': image_hashes,
                'records_sha256': hashlib.sha256(output.encode()).hexdigest()}
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f'Imported {len(rows)} CLEVR visual evaluation candidates')


if __name__ == '__main__': main()
