import collections
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def read(root):
    return [json.loads(line) for path in root.glob('**/*.jsonl')
            for line in path.read_text(encoding='utf-8').split('\n') if line.strip()]

def state_key(row):return ' '.join(row['input']['state'].split()).casefold()

class TrainingIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.train=read(ROOT/'training/data/train')
        cls.validation=read(ROOT/'training/data/validation')
        cls.eval=read(ROOT/'data')

    def test_counts_and_no_exact_input_leakage(self):
        self.assertEqual((len(self.train),len(self.validation)),(14800,3630))
        train={state_key(r) for r in self.train}
        validation={state_key(r) for r in self.validation}
        evaluation={state_key(r) for r in self.eval}
        self.assertFalse(train & validation)
        self.assertFalse(train & evaluation)
        self.assertFalse(validation & evaluation)

    def test_typed_cases_stay_together_and_are_teacher_labeled(self):
        cases=collections.defaultdict(list)
        for row in self.train+self.validation:
            if row['metadata']['source_id']=='typed-decisions':
                cases[row['metadata']['group_id']].append(row)
                self.assertEqual(row['metadata']['label_origin_kind'],'teacher_model')
                self.assertIn('teacher-model',row['gold']['q']['distribution_source'])
        self.assertEqual(len(cases),1200)
        for rows in cases.values():
            self.assertEqual(len(rows),5)
            self.assertEqual(len({r['metadata']['split'] for r in rows}),1)

    def test_gold_is_separate_from_model_input(self):
        for row in self.train+self.validation:
            self.assertEqual(set(row['input']),{'state','questions'})
            self.assertNotIn('gold',row['input'])
            self.assertNotIn('confidence',row['gold']['q'])
            self.assertEqual(row['metadata']['review']['status'],'pending')

if __name__=='__main__':unittest.main()
