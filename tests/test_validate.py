import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate import check_collection, check_record
from export_inputs import main as export_inputs

def sample(kind):
    path=ROOT/'data'/kind/'eval.jsonl'
    if not path.exists():path=next((ROOT/'data'/kind).glob('eval-part*.jsonl'))
    return json.loads(path.read_text(encoding='utf-8').splitlines()[0])

def original_lines(entry):
    p=ROOT/'sources/jevbench'/Path(entry['path']).name
    blob=p.read_bytes() if p.exists() else b''.join((ROOT/part['path']).read_bytes() for part in entry['parts'])
    return blob.decode('utf-8').splitlines()

class ValidationTests(unittest.TestCase):
    def test_valid_types(self):
        for kind in ('choice','noul','score'):
            self.assertEqual(check_record(sample(kind)),kind)

    def test_unknown_choice(self):
        r=sample('choice'); r['gold']['q']['label']='UNKNOWN'
        self.assertTrue(check_collection([r]))

    def test_boolean_is_not_score(self):
        r=sample('score'); r['gold']['q']['label']=True
        self.assertTrue(check_collection([r]))

    def test_noul_string_is_not_boolean(self):
        r=sample('noul'); r['gold']['q']['label']='false'
        self.assertTrue(check_collection([r]))

    def test_bad_distribution(self):
        r=sample('noul'); r['gold']['q'].update(distribution={'true':0.8,'false':0.8},distribution_source='review votes')
        self.assertTrue(check_collection([r]))

    def test_cross_split_leakage(self):
        a=sample('choice'); b=copy.deepcopy(a); b['id']+='-copy'; b['metadata']['split']='train'
        self.assertTrue(check_collection([a,b]))

    def test_duplicate_id(self):
        r=sample('choice'); self.assertTrue(check_collection([r,r]))

    def test_unreviewed_cannot_claim_acceptance(self):
        r=sample('choice'); r['metadata']['review']['status']='accepted'
        self.assertTrue(check_collection([r]))

    def test_all_source_content_preserved(self):
        manifest=json.loads((ROOT/'sources/manifest.json').read_text(encoding='utf-8'))
        originals={r['id']:r for e in manifest['files'] if e['path'].endswith('.jsonl')
                   for line in original_lines(e) if line.strip()
                   for r in [json.loads(line)]}
        seen=set()
        for p in (ROOT/'data').glob('*/*.jsonl'):
            for line in p.read_text(encoding='utf-8').split('\n'):
                if not line.strip(): continue
                r=json.loads(line)
                if r['metadata']['source_id']!='jevbench': continue
                original=originals[r['metadata']['source_sample_id']]
                seen.add(original['id'])
                state=r['input']['state']
                self.assertEqual(state if isinstance(original['state'],str) else json.loads(state),original['state'])
                self.assertEqual(r['input']['questions']['q'],original['question'])
                expected=original['expected']
                if r['task_type']=='noul': expected=expected=='yes'
                self.assertEqual(r['gold']['q']['label'],expected)
        self.assertEqual(seen,set(originals))

    def test_export_does_not_include_gold(self):
        export_inputs()
        lines=(ROOT/'exports/requests.jsonl').read_text(encoding='utf-8').split('\n')
        lines=[line for line in lines if line.strip()]
        expected=sum(1 for p in (ROOT/'data').glob('*/*.jsonl') for line in p.read_text(encoding='utf-8').split('\n') if line.strip())
        self.assertEqual(len(lines),expected)
        for line in lines:
            row=json.loads(line)
            self.assertEqual(set(row),{'id','input'})
            self.assertEqual(set(row['input']),{'state','questions'})

    def test_teacher_reference_is_distinct_from_human_votes(self):
        r=json.loads(next((ROOT/'data/score').glob('typed-decisions-eval*.jsonl')).read_text(encoding='utf-8').splitlines()[0])
        self.assertEqual(r['metadata']['label_origin_kind'],'teacher_model')
        self.assertIn('teacher-model',r['gold']['q']['distribution_source'])
        self.assertEqual(r['input']['questions']['q']['type'],'score')

    def test_frontier_pairs_and_original_answers(self):
        manifest=json.loads((ROOT/'sources/extended_manifest.json').read_text(encoding='utf-8'))
        entry=next(e for e in manifest['files'] if e['path']=='sources/jev-frontier-100/items.jsonl')
        original_path=ROOT/entry['path']
        blob=original_path.read_bytes() if original_path.exists() else b''.join((ROOT[p['path']]).read_bytes() for p in entry['parts'])
        original={r['id']:r for line in blob.decode('utf-8').splitlines() if line.strip() for r in [json.loads(line)]}
        records=[json.loads(line) for p in (ROOT/'data/choice').glob('frontier100-eval*.jsonl') for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]
        self.assertEqual(len(records),100)
        self.assertEqual(len({r['metadata']['group_id'] for r in records}),50)
        for r in records:
            row=original[r['metadata']['source_sample_id']]
            self.assertEqual(r['gold']['q']['label'],row['answer'])

    def test_typed_cases_keep_five_questions_together(self):
        records=[json.loads(line) for kind in ('choice','noul','score') for p in (ROOT/'data'/kind).glob('typed-decisions-eval*.jsonl') for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]
        self.assertEqual(len(records),2000)
        by_case={}
        for r in records:by_case[r['metadata']['group_id']]=by_case.get(r['metadata']['group_id'],0)+1
        self.assertEqual(len(by_case),400)
        self.assertEqual(set(by_case.values()),{5})

if __name__=='__main__':
    unittest.main()
