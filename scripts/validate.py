"""Validate the pilot contract and basic leakage rules; no external dependencies."""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def check_record(r):
    assert r['schema_version'] == '0.1', 'unsupported schema'
    assert isinstance(r['id'], str) and r['id'], 'missing id'
    kind = r['task_type']
    assert kind in ('choice', 'noul', 'score'), 'unsupported type'
    inp = r['input']
    assert set(inp) == {'state', 'questions'}, 'input must contain state/questions only'
    assert isinstance(inp['state'], str) and inp['state'].strip(), 'empty state'
    assert len(inp['questions']) == 1, 'one question per record in v0.1'
    assert set(inp['questions']) == set(r['gold']), 'gold question ids mismatch'
    qid, q = next(iter(inp['questions'].items()))
    assert q['type'] == kind, 'type mismatch'
    assert isinstance(q['instructions'], str) and q['instructions'].strip(), 'empty instructions'
    c = q['criteria']
    label = r['gold'][qid]['label']
    if kind == 'choice':
        assert isinstance(c, dict) and len(c) >= 2, 'choice needs >=2 options'
        assert all(isinstance(k,str) and k for k in c), 'invalid option key'
        assert isinstance(label, str) and label in c, 'unknown choice label'
        keys = set(c)
    elif kind == 'noul':
        assert isinstance(c, dict) and set(c) == {'true', 'false'}, 'noul criteria keys'
        assert type(label) is bool, 'noul label must be boolean'
        keys = {'true', 'false'}
    else:
        assert isinstance(c, list) and 2 <= len(c) <= 10, 'score needs 2..10 levels'
        assert type(label) in (int, float) and math.isfinite(label), 'score must be finite number'
        assert 0 <= label <= len(c)-1, 'score out of range'
        keys = {str(i) for i in range(len(c))}
    descriptions = c.values() if isinstance(c, dict) else c
    assert all(isinstance(v, str) and v.strip() for v in descriptions), 'empty criterion'
    gold = r['gold'][qid]
    assert 'confidence' not in gold and 'probabilities' not in gold, 'prediction fields are not gold'
    if 'distribution' in gold:
        d = gold['distribution']
        assert set(d) == keys, 'distribution keys mismatch'
        assert all(type(v) in (int,float) and math.isfinite(v) and 0 <= v <= 1 for v in d.values()), 'invalid probability'
        assert abs(sum(d.values()) - 1) <= 1e-6, 'distribution must sum to one'
        assert gold.get('distribution_source'), 'distribution needs independent provenance'
    m = r['metadata']
    for key in ('source_id','source_url','source_revision','source_sample_id','group_id','license','label_origin','transformation','language'):
        assert isinstance(m[key], str) and m[key].strip(), 'missing metadata: ' + key
    assert m['source_url'].startswith('https://'), 'source requires HTTPS URL'
    assert m['split'] in ('train','validation','test','eval'), 'invalid split'
    review = m['review']
    assert review['status'] in ('pending','accepted','rejected'), 'invalid review status'
    assert isinstance(review['reviewers'],list), 'invalid reviewers'
    if review['status'] == 'accepted':
        assert len(set(review['reviewers'])) >= 2, 'acceptance needs two distinct reviewers'
    return kind

def check_collection(rows):
    errors, ids, groups, texts = [], set(), {}, {}
    for r in rows:
        try:
            check_record(r)
            assert r['id'] not in ids, 'duplicate id'
            ids.add(r['id'])
            m = r['metadata']
            for index, key in ((groups, m['group_id']), (texts, ' '.join(r['input']['state'].split()).casefold())):
                assert key not in index or index[key] == m['split'], 'cross-split group/state leakage'
                index[key] = m['split']
        except (AssertionError, KeyError, TypeError, ValueError) as exc:
            errors.append({'id': r.get('id', '?') if isinstance(r,dict) else '?', 'error': str(exc)})
    return errors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release', action='store_true', help='require local human acceptance for every row')
    args = parser.parse_args()
    rows, errors = [], []
    for path in sorted((ROOT / 'data').glob('*/*.jsonl')):
        for lineno, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            try:
                r = json.loads(line)
                if r['task_type'] != path.parent.name:
                    errors.append({'file': str(path.relative_to(ROOT)), 'line': lineno, 'error': 'wrong group directory'})
                rows.append(r)
            except (ValueError, KeyError, TypeError) as exc:
                errors.append({'file': str(path.relative_to(ROOT)), 'line': lineno, 'error': str(exc)})
    errors.extend(check_collection(rows))
    if not rows:
        errors.append({'error': 'no data'})
    manifest = json.loads((ROOT/'sources/manifest.json').read_text(encoding='utf-8'))
    for entry in manifest['files']:
        path = ROOT / 'sources/jevbench' / Path(entry['path']).name
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            errors.append({'error': 'source hash mismatch', 'path': entry['path']})
    pending = sum(r.get('metadata',{}).get('review',{}).get('status') != 'accepted' for r in rows)
    report = {'records': len(rows), 'by_type': dict(collections.Counter(r.get('task_type') for r in rows)),
              'by_family': dict(collections.Counter(r.get('metadata',{}).get('family') for r in rows)),
              'automatic_checks_passed': not errors, 'errors': errors, 'not_human_accepted': pending,
              'release_ready': not errors and pending == 0,
              'note': 'Structural/provenance checks only. No model inference or human label review performed.'}
    folder = ROOT / 'reports'
    folder.mkdir(exist_ok=True)
    (folder/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(1 if errors or (args.release and pending) else 0)

if __name__ == '__main__':
    main()
