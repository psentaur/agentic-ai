"""Paired diagnostics and immutable pilot-export regression checks."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts import analyze_person3 as p3


def response(identifier, correct, **fields):
    return {'model': 'model', 'language': 'en', 'problem_id': identifier,
            'experiment_id': identifier + str(fields.get('budget', 4)), 'correct': correct,
            'parse_error': None, 'truncated': False, 'step_compliant': True,
            'actual_steps': 4, 'output_tokens': 10, **fields}


class Person3AnalysisTests(unittest.TestCase):
    def test_outcome_transitions_and_net_change(self):
        pairs = [p3.pair_diagnostics(response(str(i), a), response(str(i), b, budget=16))
                 for i, (a, b) in enumerate([(0, 0), (0, 1), (1, 0), (1, 0), (1, 1)])]
        summary = p3.transition_summary(pairs)
        self.assertEqual([summary[k] for k in ('0_to_0', '0_to_1', '1_to_0', '1_to_1')], [1, 1, 2, 1])
        self.assertEqual(summary['net_correct_change'], -1)
        self.assertEqual(sum(p['accuracy_delta'] for p in pairs), -1)

    def test_flags_overlap_and_truncation_does_not_change_correctness(self):
        loss = p3.pair_diagnostics(response('x', True), response('x', False, budget=16,
                                  parse_error='missing_marker', truncated=True, step_compliant=False))
        gain = p3.pair_diagnostics(response('y', False, parse_error='invalid_number'),
                                  response('y', True, budget=16, truncated=True))
        summary = p3.transition_summary([loss, gain])
        for key in ('losses_any_parse_failure', 'losses_any_truncation', 'losses_any_step_noncompliance'):
            self.assertEqual(summary[key], 1)
        self.assertEqual(summary['losses_parse_failure_at_16'], 1)
        self.assertEqual(summary['both_parse_valid_n'], 0)
        self.assertEqual(gain['correct_16'], 1)
        self.assertTrue(gain['truncated_16'])

    def test_pair_identity_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Pair must match'):
            p3.pair_diagnostics(response('x', True), response('y', True))

    def fixture(self):
        return [{'experiment_id': str(i), 'model': m, 'problem_id': 'one', 'split': 'development',
                 'language': lang, 'reasoning_language': expl, 'budget': budget}
                for i, (m, lang, expl, budget) in enumerate(
                    (m, l, e, b) for m in ['a', 'b'] for l in ('en', 'bn', 'te')
                    for b in (0, 2, 4, 8, 16) for e in ([l, 'en'] if l != 'en' and b else [l]))]

    def test_exact_grid_and_duplicate_records(self):
        rows = self.fixture()
        p3.validate_cohort(rows, ['one'], ['a', 'b'])
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'duplicate.jsonl'
            path.write_text('\n'.join(json.dumps(r) for r in rows + [rows[0]]))
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                p3.validate_cohort(p3.audit.read_jsonl(path), ['one'], ['a', 'b'])
        condition_duplicate = copy.deepcopy(rows)
        condition_duplicate[-1] = {**rows[0], 'experiment_id': 'new_unique'}
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            p3.validate_cohort(condition_duplicate, ['one'], ['a', 'b'])

    def test_incomplete_and_unexpected_cohort_rejected(self):
        rows = self.fixture()
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            p3.validate_cohort(rows[:-1], ['one'], ['a', 'b'])
        rows[-1]['split'] = 'test'
        with self.assertRaisesRegex(ValueError, 'Only development'):
            p3.validate_cohort(rows, ['one'], ['a', 'b'])

    def test_real_pilot_exports_are_deterministic_and_denominators_retained(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / 'export'
            args = (p3.ROOT / 'configs/local-nf4.json', p3.ROOT / 'data', p3.ROOT / 'results/local-nf4-v1', output)
            first = p3.run(*args)
            hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()}
            second = p3.run(*args)
            self.assertEqual(first, second)
            self.assertEqual(hashes, {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()})
            self.assertEqual(first['responses'], 2300)
            self.assertEqual(first['transition_rows'], 300)
            english = next(r for r in first['transition_summary'] if r['model'] == 'qwen3-4b' and r['language'] == 'en')
            self.assertEqual((english['n'], english['1_to_0'], english['0_to_1'], english['losses_parse_failure_at_16']), (50, 7, 1, 4))
            self.assertEqual((english['both_parse_valid_n'], english['both_parse_valid_net_correct_change']), (45, -2))

    def test_protected_output_directory_rejected(self):
        with self.assertRaisesRegex(ValueError, 'overwrite protected'):
            p3.run(p3.ROOT / 'configs/local-nf4.json', p3.ROOT / 'data',
                   p3.ROOT / 'results/local-nf4-v1', p3.ROOT / 'study')


if __name__ == '__main__':
    unittest.main()
