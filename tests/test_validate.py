import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate import check_collection, check_record

def sample(kind):
    return json.loads((ROOT/'data'/kind/'eval.jsonl').read_text(encoding='utf-8').splitlines()[0])

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
        originals={r['id']:r for p in (ROOT/'sources/jevbench').glob('*.jsonl')
                   for line in p.read_text(encoding='utf-8').splitlines() if line.strip()
                   for r in [json.loads(line)]}
        seen=set()
        for p in (ROOT/'data').glob('*/*.jsonl'):
            for line in p.read_text(encoding='utf-8').splitlines():
                r=json.loads(line); original=originals[r['metadata']['source_sample_id']]
                seen.add(original['id'])
                state=r['input']['state']
                self.assertEqual(state if isinstance(original['state'],str) else json.loads(state),original['state'])
                self.assertEqual(r['input']['questions']['q'],original['question'])
                expected=original['expected']
                if r['task_type']=='noul': expected=expected=='yes'
                self.assertEqual(r['gold']['q']['label'],expected)
        self.assertEqual(seen,set(originals))

    def test_export_does_not_include_gold(self):
        lines=(ROOT/'exports/requests.jsonl').read_text(encoding='utf-8').splitlines()
        self.assertEqual(len(lines),231)
        for line in lines:
            row=json.loads(line)
            self.assertEqual(set(row),{'id','input'})
            self.assertEqual(set(row['input']),{'state','questions'})

if __name__=='__main__':
    unittest.main()
