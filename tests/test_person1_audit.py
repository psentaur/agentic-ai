"""Independent audit corruption and annotation-preservation checks.

All altered records/tables are temporary fixtures. These tests import no
production scorer or analysis module and never modify scientific artifacts.
"""
import copy
import csv
from pathlib import Path
import tempfile
import unittest

from scripts.audit_person1 import (Checks, HUMAN_FIELDS, equal, number,
    preserve_review, reconcile_scored, reconcile_table, score, unique_rows,
    write_csv)


def response_row(text="FINAL_ANSWER: 10", **updates):
    return {"experiment_id": "temporary-fixture", "problem_id": "fixture-001", "language": "en",
            "reasoning_language": "en", "budget": 0, "response": text,
            "output_tokens": 10, "truncated": False, **updates}


class Person1AuditTests(unittest.TestCase):
    def test_decimal_unicode_grouping_and_unrounded_large_values(self):
        cases = {
            " ১২,৩৪,৫৬৭.০০ ": "1234567", "−౧౨.౫౦": "-12.5", "1,234,567.000": "1234567",
            "+.50": "0.5", "-0.000": "0", "１０００.００": "1000",
            "1234567890123456789012345678901234567890.0012300": "1234567890123456789012345678901234567890.00123",
            "1000000000000000000000000000000000000000": "1000000000000000000000000000000000000000",
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(number(source), expected)
        for source in ("1,23", "12,345,67", "1,2,345", "1,234.5,6", "5/9", "1e3", "10 units", "NaN", "Infinity", "10."):
            with self.subTest(source=source), self.assertRaises(ValueError):
                number(source)

    def test_marker_failures_and_truncated_responses_remain_incorrect(self):
        cases = [
            ("The answer is 10", "missing_marker"),
            ("Answer: FINAL_ANSWER: 10", "missing_marker"),
            ("FINAL_ANSWER: 10\nFINAL_ANSWER: 10", "multiple_markers"),
            ("FINAL_ANSWER: 5/9", "invalid_number"),
            ("FINAL_ANSWER: 10 dollars", "invalid_number"),
            ("FINAL_ANSWER:   ", "invalid_number"),
        ]
        for text, error in cases:
            with self.subTest(error=error):
                result = score(response_row(text, truncated=True), "10")
                self.assertEqual(result["parse_error"], error)
                self.assertFalse(result["correct"])
                self.assertTrue(result["truncated"])
        result = score(response_row("FINAL_ANSWER: ১০"), "10")
        self.assertTrue(result["correct"])
        self.assertIsNone(result["parse_error"])
        result = score(response_row("FINAL_ANSWER: 10", truncated=True), "10")
        self.assertTrue(result["correct"])
        self.assertTrue(result["truncated"])

    def test_numbered_step_and_script_diagnostics_without_semantic_claims(self):
        row = response_row("১. বাংলা abc\n২) বাংলা abc\nFINAL_ANSWER: 10", reasoning_language="bn", budget=2)
        result = score(row, "10")
        self.assertEqual(result["actual_steps"], 2)
        self.assertTrue(result["step_compliant"])
        self.assertTrue(result["repeated_step"])
        self.assertEqual(result["latin_letters"], 6)
        self.assertGreater(result["bengali_letters"], 0)
        self.assertEqual(result["telugu_letters"], 0)
        self.assertIn("not a language or semantic", result["script_check_note"])

    def test_duplicate_temporary_records_fail_the_audit(self):
        original = [response_row(), response_row()]
        before = copy.deepcopy(original)
        checks = Checks()
        unique_rows(original, checks, "temporary raw")
        self.assertEqual(len(checks.failures), 1)
        self.assertIn("unique experiment ID", checks.failures[0]["check"])
        self.assertEqual(original, before)

    def test_altered_temporary_score_and_raw_field_are_detected(self):
        raw = [response_row()]
        records = [{"problem_id": "fixture-001", "language": "en", "gold": "10"}]
        stored = [score(raw[0], "10")]
        stored[0]["correct"] = False
        stored[0]["response"] = "tampered temporary output"
        checks = Checks()
        recomputed = reconcile_scored(raw, stored, records, checks)
        self.assertTrue(recomputed[0]["correct"])
        failures = [failure["check"] for failure in checks.failures]
        self.assertTrue(any("scored field correct" in failure for failure in failures))
        self.assertTrue(any("scored field response" in failure for failure in failures))
        self.assertEqual(raw[0]["response"], "FINAL_ANSWER: 10")

    def test_temporary_table_tampering_and_absolute_tolerance(self):
        expected = [{"model": "fixture", "n": 50, "accuracy": 0.6, "ci_low": 0.46, "ci_high": 0.74}]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "altered-table.csv"
            changed = copy.deepcopy(expected)
            changed[0]["accuracy"] = 0.62
            write_csv(path, changed)
            with path.open(newline="", encoding="utf-8") as stream:
                actual = list(csv.DictReader(stream))
            checks = Checks()
            reconcile_table(actual, expected, checks, "temporary summary", csv_strings=True)
        self.assertEqual(len(checks.failures), 1)
        self.assertIn("field accuracy", checks.failures[0]["check"])
        self.assertTrue(equal(0.6 + 5e-13, 0.6))
        self.assertFalse(equal(0.6 + 5e-11, 0.6))
        self.assertFalse(equal(50.0, 50))
        self.assertFalse(equal(True, 1))

    def test_resume_preserves_human_annotations(self):
        selected = [{"experiment_id": "fixture-a", "benchmark_gold": "10", **dict.fromkeys(HUMAN_FIELDS, "")}]
        previous = copy.deepcopy(selected)
        previous[0].update(independent_answer="10", gold_agrees="yes", score_agrees="yes", reviewer="Test reviewer",
                           date="2026-10-12", decision="accept", notes="Fixture only; not a real human sign-off")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "numerical_review.csv"
            write_csv(path, previous)
            resumed = preserve_review(path, selected)
            for field in HUMAN_FIELDS:
                self.assertEqual(resumed[0][field], previous[0][field])
            self.assertEqual(resumed[0]["benchmark_gold"], "10")
            original_bytes = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "case IDs differ"):
                preserve_review(path, [{"experiment_id": "fixture-b"}])
            self.assertEqual(path.read_bytes(), original_bytes)


if __name__ == "__main__":
    unittest.main()
