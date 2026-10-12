import csv, hashlib, json, random, tempfile, unittest
from pathlib import Path
from scripts import build_person4_packet as p4
class PacketTests(unittest.TestCase):
    def sample(self): return list(csv.DictReader((p4.ROOT/'results/local-nf4-v1/analysis/development_review.csv').open()))
    def test_selection(self):
        rows=p4.select(self.sample()); self.assertEqual(len(rows),10); self.assertEqual(len({r['problem_id'] for r in rows}),10)
        self.assertEqual(sum(r['model']=='qwen3-4b' for r in rows),4)
        self.assertEqual([sum(r['question_language']==l for r in rows) for l in ('en','bn','te')],[7,1,2])
    def test_duplicate_rejection(self):
        rows=self.sample()
        with self.assertRaisesRegex(ValueError,'Duplicate'): p4.select(rows+[rows[0]])
    def test_order_independence(self):
        rows=self.sample(); expected=p4.select(rows); random.Random(19).shuffle(rows); self.assertEqual(p4.select(rows),expected)
    def test_incomplete_selection(self):
        rows=[r for r in self.sample() if r['model']!='qwen3-4b']
        with self.assertRaises(ValueError): p4.select(rows)
    def test_annotations_preserved(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/'review.csv'; rows=p4.select(self.sample()); p4.write_reviews(path,rows,True)
            original=list(csv.DictReader(path.open())); original[0]['reviewer1_notes']='human annotation'
            with path.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=original[0]); w.writeheader(); w.writerows(original)
            p4.write_reviews(path,rows,True); self.assertEqual(next(csv.DictReader(path.open()))['reviewer1_notes'],'human annotation')
            with self.assertRaisesRegex(ValueError,'removed'): p4.write_reviews(path,rows[1:],True)
    def test_real_coverage_and_deterministic_rerun(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t); result=p4.run(p4.ROOT/'results/local-nf4-v1',p4.ROOT/'data',out)
            hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}
            self.assertEqual(result['cases'],40); self.assertEqual(result['english_candidates'],12)
            self.assertEqual(result['parse_errors'],{'missing_marker':4,'multiple_markers':1,'invalid_number':1})
            p4.run(p4.ROOT/'results/local-nf4-v1',p4.ROOT/'data',out)
            self.assertEqual(hashes,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()})
    def test_numeric_only_not_semantic_candidate(self):
        self.assertFalse(p4.eligible({'explanation_language':'en','response':'FINAL_ANSWER: 5'}))
