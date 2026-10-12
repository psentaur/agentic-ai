#!/usr/bin/env python3
"""Independent, read-only audit of the completed preliminary study.

No study modules are imported. Inputs are never repaired or overwritten. The
lexical scoring contract is implemented separately; bootstrap samples are drawn
one replicate at a time rather than by the production analysis implementation.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import importlib.metadata
import io
import json
import math
from pathlib import Path
import random
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
TOLERANCE = 1e-12
HUMAN_FIELDS = ("independent_answer", "gold_agrees", "score_agrees", "reviewer", "date", "decision", "notes")
SCORE_NOTE = "Observable script counts only; not a language or semantic correctness judgment"


def digest(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path, rows):
    with Path(path).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class Checks:
    def __init__(self):
        self.checked = 0
        self.failures = []

    def require(self, condition, label, **details):
        self.checked += 1
        if not condition:
            self.failures.append({"check": label, **details})

    def same(self, actual, expected, label):
        self.require(equal(actual, expected), label, actual=actual, expected=expected)


def equal(actual, expected):
    """Exact discrete comparison; floating-point tolerance is absolute 1e-12."""
    if isinstance(expected, bool):
        return isinstance(actual, bool) and actual == expected
    if isinstance(expected, int):
        return isinstance(actual, int) and not isinstance(actual, bool) and actual == expected
    if isinstance(expected, float):
        return isinstance(actual, (int, float)) and not isinstance(actual, bool) and math.isfinite(actual) and math.isclose(actual, expected, rel_tol=0, abs_tol=TOLERANCE)
    if isinstance(expected, dict):
        return isinstance(actual, dict) and actual.keys() == expected.keys() and all(equal(actual[k], v) for k, v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(equal(a, e) for a, e in zip(actual, expected))
    return actual == expected


def number(text):
    """Normalize a finite decimal without Decimal.normalize rounding its digits."""
    source = unicodedata.normalize("NFKC", text).strip().replace("−", "-")
    source = "".join(str(unicodedata.decimal(c)) if c.isdecimal() else c for c in source)
    sign = ""
    if source.startswith(("+", "-")):
        sign, source = source[0], source[1:]
    if not source or source.count(".") > 1:
        raise ValueError("Expected a decimal")
    parts = source.split(".")
    integer = parts[0]
    fraction = parts[1] if len(parts) == 2 else None
    if fraction is not None and (not fraction or not fraction.isascii() or not fraction.isdigit()):
        raise ValueError("Invalid fractional digits")
    if "," in integer:
        groups = integer.split(",")
        if any(not g or not g.isascii() or not g.isdigit() for g in groups):
            raise ValueError("Invalid grouped digits")
        western = 1 <= len(groups[0]) <= 3 and all(len(g) == 3 for g in groups[1:])
        indian = 1 <= len(groups[0]) <= 2 and len(groups[-1]) == 3 and all(len(g) == 2 for g in groups[1:-1])
        if not western and not indian:
            raise ValueError("Invalid grouping widths")
        integer = "".join(groups)
    if integer and (not integer.isascii() or not integer.isdigit()):
        raise ValueError("Invalid integer digits")
    if not integer and fraction is None:
        raise ValueError("Missing digits")
    value = Decimal(sign + (integer or "0") + ("." + fraction if fraction is not None else ""))
    if not value.is_finite():
        raise ValueError("Non-finite decimal")
    if value == 0:
        return "0"
    rendered = format(value, "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered


def score(row, gold):
    # Whitespace includes line breaks, matching the frozen v1 lexical contract.
    markers = [match.group("value") for match in re.finditer(r"^\s*FINAL_ANSWER:\s*(?P<value>[^\n]*?)\s*$", row["response"], re.MULTILINE)]
    answer, error = None, None
    if len(markers) == 0:
        error = "missing_marker"
    elif len(markers) > 1:
        error = "multiple_markers"
    else:
        try:
            answer = number(markers[0])
        except ValueError:
            error = "invalid_number"
    steps = [match.group("step") for match in re.finditer(r"^\s*[\d]+(?:\.|\))\s+(?P<step>[^\n]+)$", row["response"], re.MULTILINE)]
    scripts = dict.fromkeys(("latin_letters", "bengali_letters", "telugu_letters"), 0)
    for char in "\n".join(steps):
        if unicodedata.category(char)[0] != "L":
            continue
        code = ord(char)
        if 0x980 <= code <= 0x9FF:
            scripts["bengali_letters"] += 1
        elif 0xC00 <= code <= 0xC7F:
            scripts["telugu_letters"] += 1
        elif "LATIN" in unicodedata.name(char, ""):
            scripts["latin_letters"] += 1
    total = sum(scripts.values())
    target = {"en": "latin_letters", "bn": "bengali_letters", "te": "telugu_letters"}[row["reasoning_language"]]
    return {**row, "scorer_version": "1", "answer": answer, "correct": answer is not None and answer == number(gold),
            "parse_error": error, "actual_steps": len(steps), "step_compliant": len(steps) == row["budget"],
            "repeated_step": len({text.strip().casefold() for text in steps}) != len(steps),
            **scripts, "target_script_fraction": scripts[target] / total if total else None,
            "script_check_note": SCORE_NOTE}


def reconstruct_data(config, data_dir, checks):
    manifest = read_json(data_dir / "manifest.json")
    records = read_jsonl(data_dir / "records.jsonl")
    checks.same(config["split_seed"], 42, "fixed split seed")
    checks.same(config["languages"], ["en", "bn", "te"], "fixed languages")
    checks.same(config["budgets"], [0, 2, 4, 8, 16], "fixed budgets")
    checks.same(manifest["dataset_revision"], config["dataset_revision"], "dataset revision")
    ids = [f"mgsm-{i:03d}" for i in range(250)]
    shuffled = ids.copy()
    random.Random(42).shuffle(shuffled)
    splits = {"development": shuffled[:100], "pilot": shuffled[:50], "smoke": shuffled[:10], "test": shuffled[100:]}
    checks.same(manifest["split_seed"], 42, "manifest split seed")
    checks.same(manifest["splits"], splits, "independently reconstructed nested splits")
    source_rows, source_hashes = {}, {}
    for language in ("en", "bn", "te"):
        path = data_dir / "raw" / config["dataset_revision"] / f"mgsm_{language}.tsv"
        source_hashes[language] = file_hash(path)
        checks.same(source_hashes[language], manifest["sources"][language]["sha256"], f"{language} source TSV checksum")
        expected_url = f"https://raw.githubusercontent.com/google-research/url-nlp/{config['dataset_revision']}/mgsm/mgsm_{language}.tsv"
        checks.same(manifest["sources"][language]["url"], expected_url, f"{language} pinned source URL")
        source_rows[language] = list(csv.reader(io.StringIO(path.read_text(encoding="utf-8")), delimiter="\t"))
        checks.require(len(source_rows[language]) == 250 and all(len(r) == 2 and r[0].strip() for r in source_rows[language]), f"{language} 250 two-column questions")
    expected_records = []
    for index, problem_id in enumerate(ids):
        golds = [number(source_rows[language][index][1]) for language in ("en", "bn", "te")]
        checks.require(len(set(golds)) == 1, f"{problem_id} cross-language numerical gold alignment", golds=golds)
        for language in ("en", "bn", "te"):
            expected_records.append({"problem_id": problem_id, "source_row": index + 1, "language": language,
                                     "question": source_rows[language][index][0], "gold": golds[0],
                                     "split": "development" if problem_id in splits["development"] else "test"})
    checks.same(len(records), 750, "record count")
    checks.same(manifest["record_count"], 750, "manifest record count")
    checks.same(records, expected_records, "all 750 source-to-record mappings and order")
    checks.same(manifest["dataset_hash"], digest(expected_records), "independently reconstructed dataset digest")
    return manifest, expected_records, splits, source_hashes


def prompt(question, language, budget, explanation):
    names = {"en": "English", "bn": "Bengali", "te": "Telugu"}
    instruction = "Give a direct answer. Do not show an explanation or numbered steps." if budget == 0 else (
        f"Explain the solution in {names[explanation]} using exactly {budget} numbered steps, "
        "with one step per line in the format '1. ...'. Do not add other explanation paragraphs.")
    return ("Solve the following mathematical word problem.\n" + instruction + "\n"
            f"Give a brief final answer sentence in {names[language]}.\n"
            "Then put only the numerical answer on the last line in the exact format FINAL_ANSWER: <number>. "
            "Do not include units or any other text on that last line.\n\nProblem:\n" + question)


def grid(config, records, ids, context):
    questions = {(r["problem_id"], r["language"]): r["question"] for r in records}
    expected = {}
    for model, model_config in config["models"].items():
        for problem_id in ids:
            for language in ("en", "bn", "te"):
                for budget in (0, 2, 4, 8, 16):
                    for explanation in ([language, "en"] if language != "en" and budget else [language]):
                        key = {"problem_id": problem_id, "language": language, "model": model, "budget": budget,
                               "reasoning_language": explanation, "config_hash": context}
                        identifier = digest(key)
                        expected[identifier] = {**key, "experiment_id": identifier,
                            "model_name": model_config["name"], "model_revision": model_config["revision"],
                            "split": "development", "prompt_version": "1",
                            "prompt": prompt(questions[problem_id, language], language, budget, explanation),
                            "seed": (config["generation"]["seed"] + int(identifier[:8], 16)) % 2**32}
    return expected


def unique_rows(rows, checks, label):
    lookup = {}
    for row in rows:
        identifier = row.get("experiment_id")
        checks.require(isinstance(identifier, str) and identifier not in lookup, label + " unique experiment ID", experiment_id=identifier)
        lookup[identifier] = row
    return lookup


def reconcile_scored(raw, stored, records, checks):
    raw_lookup = unique_rows(raw, checks, "raw")
    stored_lookup = unique_rows(stored, checks, "scored")
    checks.same(sorted(stored_lookup), sorted(raw_lookup), "stored scores have exact raw key set")
    golds = {(r["problem_id"], r["language"]): r["gold"] for r in records}
    recomputed = []
    for row in raw:
        result = score(row, golds[row["problem_id"], row["language"]])
        recomputed.append(result)
        current = stored_lookup.get(row["experiment_id"])
        if current is None:
            continue
        checks.same(sorted(current), sorted(result), row["experiment_id"] + " scored field set")
        for field, value in result.items():
            checks.same(current.get(field), value, row["experiment_id"] + " scored field " + field)
    return recomputed


def interval(values, config):
    import numpy as np
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(config["seed"])
    replicate_means = []
    for _ in range(config["samples"]):
        positions = rng.integers(low=0, high=len(values), size=len(values))
        replicate_means.append(float(np.mean(values[positions])))
    quantiles = np.quantile(np.asarray(replicate_means), (0.025, 0.975))
    return float(quantiles[0]), float(quantiles[1])


def summaries(rows, config):
    groups = defaultdict(list)
    for row in rows:  # Preserve input log order within each summary group.
        groups[row["model"], row["language"], row["reasoning_language"], row["budget"]].append(row)
    output = []
    for (model, language, explanation, budget), group in sorted(groups.items()):
        low, high = interval([int(r["correct"]) for r in group], config["bootstrap"])
        n = len(group)
        output.append({"model": model, "language": language, "reasoning_language": explanation, "budget": budget, "n": n,
                       "accuracy": sum(r["correct"] for r in group) / n, "accuracy_ci_low": low, "accuracy_ci_high": high,
                       "mean_output_tokens": sum(r["output_tokens"] for r in group) / n,
                       "mean_actual_steps": sum(r["actual_steps"] for r in group) / n,
                       "step_compliance": sum(r["step_compliant"] for r in group) / n,
                       "parse_failure_rate": sum(r["parse_error"] is not None for r in group) / n,
                       "truncation_rate": sum(r["truncated"] for r in group) / n})
    return output


def contrasts(rows, config):
    lookup = {(r["model"], r["problem_id"], r["language"], r["reasoning_language"], r["budget"]): int(r["correct"]) for r in rows}
    ids = sorted({r["problem_id"] for r in rows})
    output = []
    for model in sorted({r["model"] for r in rows}):
        effects = {}
        values_by_name = []
        for language in ("en", "bn", "te"):
            effects[language] = {i: lookup[model, i, language, language, 16] - lookup[model, i, language, language, 4] for i in ids}
            values_by_name.append((f"{language}: native 16 minus 4 steps", list(effects[language].values())))
            if language != "en":
                for budget in (2, 4, 8, 16):
                    values_by_name.append((f"{language}: pivot minus native at {budget} steps",
                        [lookup[model, i, language, "en", budget] - lookup[model, i, language, language, budget] for i in ids]))
        for language in ("bn", "te"):
            values_by_name.append((f"{language} minus en: difference in native 16-minus-4 effects",
                                  [effects[language][i] - effects["en"][i] for i in ids]))
        for name, values in values_by_name:
            low, high = interval(values, config["bootstrap"])
            output.append({"model": model, "contrast": name, "n": len(values), "accuracy_difference": sum(values) / len(values),
                "ci_low": low, "ci_high": high,
                "interpretation": "Exploratory paired 95% interval; no multiplicity-adjusted significance claim"})
    return output


def reconcile_table(actual, expected, checks, label, csv_strings=False):
    checks.same(len(actual), len(expected), label + " row count")
    for index, (a, e) in enumerate(zip(actual, expected)):
        checks.same(sorted(a), sorted(e), f"{label} row {index} columns")
        for field, value in e.items():
            current = a.get(field)
            if csv_strings and isinstance(value, (int, float)):
                try:
                    current = int(current) if isinstance(value, int) else float(current)
                except (ValueError, TypeError):
                    pass
            checks.same(current, value, f"{label} row {index} field {field}")


def coverage(raw, expected_grid, splits):
    seen = {r["experiment_id"] for r in raw}
    # Complete IDs require every one of the 46 independently expected keys.
    per_id = defaultdict(set)
    for key, planned in expected_grid.items():
        per_id[planned["problem_id"]].add(key)
    output = {}
    for phase in ("smoke", "pilot", "development", "test"):
        available = sum(len(per_id[i] & seen) for i in splits[phase])
        expected = len(splits[phase]) * 46
        output[phase] = {"expected": expected, "complete": available, "fraction": available / expected,
                         "complete_paired_ids": sum(len(per_id[i]) == 46 and per_id[i] <= seen for i in splits[phase])}
    output["overall"] = {"expected": 11500, "complete": len(seen), "fraction": len(seen) / 11500}
    return output


def review_cases(rows, records):
    slots = []
    for model in sorted({r["model"] for r in rows}):
        predicates = [
            ("correct", lambda r: r["correct"] and r["language"] == "bn" and r["reasoning_language"] == "en"),
            ("valid_wrong", lambda r: r["parse_error"] is None and not r["correct"] and r["language"] == "en"),
            ("missing_marker", lambda r: r["parse_error"] == "missing_marker" and r["language"] == "te" and r["reasoning_language"] == "en" and r["truncated"]),
            ("multiple_markers", lambda r: r["parse_error"] == "multiple_markers"),
            ("invalid_number", lambda r: r["parse_error"] == "invalid_number" and r["language"] == "bn" and r["reasoning_language"] == "bn"),
        ]
        for category, predicate in predicates:
            candidates = sorted((r for r in rows if r["model"] == model and predicate(r)), key=lambda r: r["experiment_id"])
            if not candidates:
                raise ValueError(f"No review candidate for {model}/{category}")
            slots.append((model, category, candidates))
    # Solve scarce categories first so all ten cases have distinct questions.
    priority = sorted(range(len(slots)), key=lambda i: (len(slots[i][2]), slots[i][:2]))
    chosen = {}
    def select(position, used_ids):
        if position == len(priority):
            return True
        index = priority[position]
        for row in slots[index][2]:
            if row["problem_id"] not in used_ids:
                chosen[index] = row
                if select(position + 1, used_ids | {row["problem_id"]}):
                    return True
        chosen.pop(index, None)
        return False
    if not select(0, set()):
        raise ValueError("Could not select ten distinct review problems")
    questions = {(r["problem_id"], r["language"]): r for r in records}
    output = []
    for i, (model, category, _) in enumerate(slots):
        row = chosen[i]
        output.append({"case": i + 1, "category": category, "experiment_id": row["experiment_id"], "problem_id": row["problem_id"],
            "model": model, "question_language": row["language"], "explanation_language": row["reasoning_language"], "budget": row["budget"],
            "english_question": questions[row["problem_id"], "en"]["question"],
            "original_question": questions[row["problem_id"], row["language"]]["question"],
            "benchmark_gold": questions[row["problem_id"], "en"]["gold"], "parsed_answer": row["answer"],
            "scored_correct": row["correct"], "parse_error": row["parse_error"], "truncated": row["truncated"],
            "response": row["response"], **dict.fromkeys(HUMAN_FIELDS, "")})
    return output


def preserve_review(path, selected):
    if not path.exists():
        return selected
    with path.open(encoding="utf-8", newline="") as stream:
        old = list(csv.DictReader(stream))
    if [r["experiment_id"] for r in old] != [r["experiment_id"] for r in selected]:
        raise ValueError("Existing human review case IDs differ; preserve the packet and use a new audit output directory")
    for previous, new in zip(old, selected):
        for field in HUMAN_FIELDS:
            new[field] = previous.get(field, "")
    return selected


def human_packet(rows):
    lines = ["# Person 1: ten-case numerical review", "",
        "Human review is pending. The CSV is the editable source of reviewer annotations; reruns preserve those fields. "
        "Solve each English question independently before checking the benchmark gold and automated decision. "
        "The cases deliberately cover response failures and are not an unbiased accuracy sample. "
        "Native-language translation fidelity and explanation meaning need suitable language expertise.", "",
        "Automated checks verify the frozen marker contract. They do not certify the correctness of the benchmark gold or provide human sign-off.", ""]
    for r in rows:
        lines += [f"## Case {r['case']}: {r['model']} / {r['category']}", "",
            f"Problem: `{r['problem_id']}`. Experiment: `{r['experiment_id']}`.", "",
            f"Question language: {r['question_language']}; explanation language: {r['explanation_language']}; requested steps: {r['budget']}; truncated: {r['truncated']}.", "",
            "**English question**", "", r["english_question"], "", "**Original question**", "", r["original_question"], "",
            "<details>", "<summary>Reveal benchmark and model output after independent solving</summary>", "",
            f"Benchmark gold: `{r['benchmark_gold']}`. Parsed answer: `{r['parsed_answer']}`. Automated correct: `{r['scored_correct']}`. Parse error: `{r['parse_error']}`.", "",
            "**Full logged response**", "", "````text", r["response"], "````", "", "</details>", "",
            "**Human annotations (edit numerical_review.csv)**", ""]
        for field in HUMAN_FIELDS:
            lines.append(f"- {field.replace('_', ' ').capitalize()}: {r[field]}")
        lines.append("")
    return "\n".join(lines) + "\n"


def input_paths(root, data_dir, config_path, results_dir):
    paths = set((root / "study").glob("*.py")) | {config_path, data_dir / "manifest.json", data_dir / "records.jsonl"}
    paths |= set((data_dir / "raw").rglob("*.tsv"))
    paths |= set((results_dir / "raw").glob("*.jsonl"))
    paths |= set((results_dir / "scored").glob("*.jsonl"))
    paths |= {results_dir / "raw/environment.json", results_dir / "environment-freeze.txt", results_dir / "validation.json",
              results_dir / "run_state.json", results_dir / "preflight.json", results_dir / "execution_report.json"}
    paths |= set((results_dir / "analysis/pilot/both-models").glob("*"))
    return sorted(path.resolve() for path in paths if path.is_file())


def run_audit(root=ROOT, data_dir=None, config_path=None, results_dir=None, output_dir=None):
    root = Path(root).resolve()
    data_dir = Path(data_dir or root / "data").resolve()
    config_path = Path(config_path or root / "configs/local-nf4.json").resolve()
    results_dir = Path(results_dir or root / "results/local-nf4-v1").resolve()
    output_dir = Path(output_dir or results_dir / "person1-audit").resolve()
    checks = Checks()
    protected = input_paths(root, data_dir, config_path, results_dir)
    if output_dir in {root, data_dir, results_dir} or any(output_dir == p or output_dir in p.parents for p in protected):
        raise ValueError("Audit output must be a separate directory that cannot overwrite protected inputs")
    hashes_before = {str(p): file_hash(p) for p in protected}
    config = read_json(config_path)
    manifest, records, splits, source_hashes = reconstruct_data(config, data_dir, checks)
    source_hashes_by_file = {p.name: file_hash(p) for p in sorted((root / "study").glob("*.py"))}
    source_fingerprint = digest(source_hashes_by_file)
    context = digest({"config": config, "dataset": manifest["dataset_hash"], "splits": splits, "code": source_fingerprint})
    pilot_grid = grid(config, records, splits["pilot"], context)
    all_grid = grid(config, records, splits["development"] + splits["test"], context)
    metadata = read_json(results_dir / "raw/environment.json")
    checks.same(metadata["config_hash"], context, "raw environment context fingerprint")
    for name in ("run_state.json", "validation.json", "preflight.json", "execution_report.json"):
        checks.same(read_json(results_dir / name)["config_hash"], context, name + " context fingerprint")
    checks.same(read_json(results_dir / "run_state.json")["target"], "balanced-pilot", "balanced pilot target")
    checks.same(read_json(results_dir / "preflight.json")["versions"], metadata["versions"], "preflight environment versions")
    preflight_gpu = read_json(results_dir / "preflight.json")["gpu"]
    frozen_versions = {}
    for line in (results_dir / "environment-freeze.txt").read_text().splitlines():
        if "==" in line:
            package, version = line.split("==", 1)
            frozen_versions[package.lower().replace("_", "-")] = version
    for package, version in metadata["versions"].items():
        checks.same(frozen_versions.get(package.lower().replace("_", "-")), version, package + " frozen installed version")
    raw = []
    for path in sorted((results_dir / "raw").glob("*.jsonl")):
        if path.name.endswith(".errors.jsonl"):
            continue
        for row in read_jsonl(path):
            checks.same(row.get("model"), path.stem, "model matches raw filename")
            raw.append(row)
    raw_by_id = unique_rows(raw, checks, "raw coverage")
    checks.same(len(raw), 2300, "2300 raw responses")
    checks.same(sorted(raw_by_id), sorted(pilot_grid), "exact independently reconstructed pilot experiment IDs")
    checks.same(sorted({r["problem_id"] for r in raw}), sorted(splits["pilot"]), "exact 50 pilot problem IDs")
    checks.same(Counter(r["model"] for r in raw), {m: 1150 for m in config["models"]}, "1150 responses per model")
    checks.same(sum(r.get("split") == "test" for r in raw), 0, "zero held-out inference")
    checks.require(not (results_dir / "freeze.json").exists(), "held-out freeze remains absent")
    gpu_name = raw[0].get("gpu_name") if raw else None
    checks.require(isinstance(gpu_name, str) and bool(gpu_name) and gpu_name in preflight_gpu, "recorded GPU matches preflight")
    for row in raw:
        identifier = row.get("experiment_id")
        planned = pilot_grid.get(identifier)
        if planned is None:
            continue
        for field, value in planned.items():
            checks.same(row.get(field), value, identifier + " planned field " + field)
        checks.same(row.get("environment"), metadata["versions"], identifier + " environment")
        checks.same(row.get("backend"), "transformers", identifier + " backend")
        checks.same(row.get("status"), "complete", identifier + " completion status")
        checks.same(row.get("schema_version"), 1, identifier + " raw schema version")
        checks.same(row.get("gpu_name"), gpu_name, identifier + " consistent GPU name")
        checks.require(isinstance(row.get("response"), str), identifier + " response string")
        for field in ("input_tokens", "output_tokens", "peak_gpu_memory_bytes", "peak_gpu_reserved_bytes"):
            value = row.get(field)
            checks.require(isinstance(value, int) and not isinstance(value, bool) and value >= 0, identifier + " nonnegative " + field)
        checks.require(row["output_tokens"] <= config["generation"]["max_new_tokens"], identifier + " token cap")
        checks.require(isinstance(row.get("truncated"), bool), identifier + " truncation boolean")
        checks.same(row.get("finish_reason"), "length" if row["truncated"] else "eos", identifier + " finish reason")
        checks.require(not row["truncated"] or row["output_tokens"] == config["generation"]["max_new_tokens"], identifier + " truncation reaches cap")
        checks.require(isinstance(row.get("latency_seconds"), (int, float)) and math.isfinite(row["latency_seconds"]) and row["latency_seconds"] >= 0, identifier + " latency")
        try:
            timestamp = datetime.fromisoformat(row["generated_at"])
            checks.require(timestamp.tzinfo is not None, identifier + " timezone-aware timestamp")
        except (ValueError, TypeError, KeyError):
            checks.require(False, identifier + " timestamp")
    validation = read_json(results_dir / "validation.json")
    for filename, expected_hash in validation["files"].items():
        checks.same(file_hash(results_dir / filename), expected_hash, filename + " Person 2 recorded raw hash")
    scored = reconcile_scored(raw, read_jsonl(results_dir / "scored/development.jsonl"), records, checks)
    summary, paired = summaries(scored, config), contrasts(scored, config)
    checks.same(len(summary), 46, "46 summary conditions")
    checks.require(all(r["n"] == 50 for r in summary), "50 responses in every summary condition")
    checks.same(len(paired), 26, "26 paired contrasts")
    computed_coverage = coverage(raw, all_grid, splits)
    analysis_dir = results_dir / "analysis/pilot/both-models"
    analysis = read_json(analysis_dir / "analysis.json")
    checks.same(analysis["config_hash"], context, "analysis fingerprint")
    checks.same(analysis["phase"], "pilot", "analysis phase")
    checks.same(analysis["model_filter"], None, "both-model analysis")
    checks.same(analysis["cohort_ids"], sorted(splits["pilot"]), "analysis matched cohort")
    checks.same(analysis["balanced_responses"], 2300, "analysis balanced responses")
    checks.same(analysis["coverage"], computed_coverage, "analysis coverage")
    checks.same(read_json(results_dir / "execution_report.json")["coverage"], computed_coverage, "execution report coverage")
    reconcile_table(analysis["summary"], summary, checks, "JSON summary")
    reconcile_table(analysis["contrasts"], paired, checks, "JSON contrasts")
    for filename, expected in (("summary.csv", summary), ("paired_contrasts.csv", paired)):
        with (analysis_dir / filename).open(encoding="utf-8", newline="") as stream:
            reconcile_table(list(csv.DictReader(stream)), expected, checks, filename, csv_strings=True)
    review = review_cases(scored, records)
    review = preserve_review(output_dir / "numerical_review.csv", review)
    checks.same(len(review), 10, "ten human review cases")
    checks.same(len({r["problem_id"] for r in review}), 10, "ten distinct review questions")
    hashes_after = {str(p): file_hash(p) for p in protected}
    checks.same(hashes_after, hashes_before, "all protected inputs unchanged during audit")
    models = []
    for model in sorted(config["models"]):
        group = [r for r in scored if r["model"] == model]
        models.append({"model": model, "responses": len(group), "correct": sum(r["correct"] for r in group),
            "accuracy": sum(r["correct"] for r in group) / len(group), "parse_errors": dict(Counter(r["parse_error"] for r in group if r["parse_error"])),
            "parse_failures": sum(r["parse_error"] is not None for r in group), "truncated": sum(r["truncated"] for r in group),
            "step_compliant": sum(r["step_compliant"] for r in group)})
    result = {"audit_schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
        "passed": not checks.failures, "checks_performed": checks.checked, "discrepancies": checks.failures,
        "config_hash": context, "source_fingerprint": source_fingerprint, "dataset_hash": manifest["dataset_hash"],
        "source_tsv_hashes": source_hashes, "study_source_hashes": source_hashes_by_file,
        "audit_script_sha256": file_hash(Path(__file__)), "numpy_version": importlib.metadata.version("numpy"),
        "floating_point_absolute_tolerance": TOLERANCE, "bootstrap": config["bootstrap"],
        "coverage": computed_coverage, "models": models, "gpu_name": gpu_name, "reconciled_scored_records": len(scored),
        "summary_rows": len(summary), "paired_contrast_rows": len(paired),
        "protected_inputs_before": hashes_before, "protected_inputs_after": hashes_after,
        "raw_files_unchanged": all(hashes_before[str(p)] == hashes_after[str(p)] for p in protected if p.parent == results_dir / "raw"),
        "human_review": {"status": "pending", "cases": len(review), "annotated_cases": sum(any(r[f] for f in HUMAN_FIELDS) for r in review),
                         "experiment_ids": [r["experiment_id"] for r in review]},
        "limitations": ["Independent numerical/lexical recomputation does not certify benchmark answers or translation fidelity.",
            "The strict final-marker contract is reproduced as deployed; marker position beyond the anchored matching rule is not added retroactively.",
            "Script and numbered-step measures are observable formatting proxies, not language or semantic judgments.",
            "Bootstrap intervals are exploratory paired 95% intervals without multiplicity adjustment.",
            "This audit uses only the completed 50-ID pilot; full development and all held-out inference remain incomplete."]}
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "audit.json", result)
    write_csv(output_dir / "summary.csv", summary)
    write_csv(output_dir / "paired_contrasts.csv", paired)
    write_csv(output_dir / "numerical_review.csv", review)
    (output_dir / "HUMAN_REVIEW.md").write_text(human_packet(review), encoding="utf-8")
    lines = ["# Person 1 independent preliminary audit", "", f"Automated result: **{'PASS' if result['passed'] else 'FAIL'}**; {checks.checked:,} checks; {len(checks.failures)} discrepancies. Human sign-off remains pending.", "",
        "The audit independently reconstructs the frozen source records, splits, experiment IDs, prompts and seeds; re-parses every raw response; and recomputes every pilot summary and paired contrast. "
        "It imports no production study module. Discrete values agree exactly; floating-point comparisons use absolute tolerance 1e-12. "
        "Bootstrap verification draws 2,000 replacement samples with NumPy seed 42 in the same deterministic input order, one replicate at a time.", "",
        f"Experiment fingerprint: `{context}`.", "", "| Evidence | Expected | Observed |", "|---|---:|---:|",
        f"| Dataset records | 750 | {len(read_jsonl(data_dir / 'records.jsonl'))} |",
        f"| Development / held-out IDs | 100 / 150 | {len(manifest['splits']['development'])} / {len(manifest['splits']['test'])} |",
        f"| Completed raw responses / unique experiments | 2,300 / 2,300 | {len(raw):,} / {len(raw_by_id):,} |",
        f"| Complete matched pilot IDs | 50 | {computed_coverage['pilot']['complete_paired_ids']} |",
        f"| Summary conditions / responses per condition | 46 / 50 | {len(summary)} / {min(r['n'] for r in summary)}–{max(r['n'] for r in summary)} |",
        f"| Paired contrasts | 26 | {len(paired)} |",
        f"| Held-out responses | 0 | {sum(r.get('split') == 'test' for r in raw)} |", "",
        "| Model | Correct | Accuracy | Parsing failures | Truncated | Step compliant |", "|---|---:|---:|---:|---:|---:|"]
    for m in models:
        lines.append(f"| {m['model']} | {m['correct']}/{m['responses']} | {m['accuracy']:.2%} | {m['parse_failures']} | {m['truncated']} | {m['step_compliant']} |")
    integrity_note = ("Source TSV checksums match the locally frozen manifest; numerical answers match across parallel rows, which alone cannot establish semantic alignment. "
        "Raw files, settings, dataset, production code and stored results remained unchanged." if result["passed"] else
        "Automated checks failed. Source checksum, numerical alignment and result-integrity agreement must not be assumed; inspect the discrepancies in audit.json. Inputs were not repaired.")
    lines += ["", "Parsing failures and truncated responses remain in the accuracy denominator. Infrastructure failures are separate logs, not completed responses. "
        + integrity_note, "", "## Deliverables and human follow-up", "",
        "- `audit.json`: machine-readable checks, discrepancies and input hashes.",
        "- `summary.csv` and `paired_contrasts.csv`: independently regenerated values.",
        "- `numerical_review.csv`: ten distinct questions, five per model, with blank editable human fields.",
        "- `HUMAN_REVIEW.md`: full questions and logged responses for numerical/marker review.", "",
        "The review packet covers correct answers, valid wrong answers, missing markers, duplicate markers, invalid numeric markers, all three question languages, English pivots and truncation. "
        "It is a targeted diagnostic sample, not an accuracy estimator. Human reviewers must independently solve the English questions, check benchmark gold/scoring decisions, "
        "verify figure/table/caption consistency and sign off the dataset/split/metric manuscript text. Record name, date, decision and notes. "
        "Use appropriate language expertise for any translation-fidelity judgments.", "", "## Limitations", "", *["- " + value for value in result["limitations"]]]
    if checks.failures:
        lines += ["", "## Discrepancies", "", "Inputs were not repaired. Inspect the full discrepancy list in audit.json."]
        lines.extend(f"- {r['check']}" for r in checks.failures[:50])
    (output_dir / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--results-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    try:
        result = run_audit(args.root, args.data_dir, args.config, args.results_dir, args.output_dir)
    except (ValueError, KeyError, TypeError, OSError, IndexError) as error:
        root = args.root.resolve()
        data_dir = (args.data_dir or root / "data").resolve()
        config_path = (args.config or root / "configs/local-nf4.json").resolve()
        results_dir = (args.results_dir or root / "results/local-nf4-v1").resolve()
        output_dir = (args.output_dir or results_dir / "person1-audit").resolve()
        protected = input_paths(root, data_dir, config_path, results_dir)
        safe_output = output_dir not in {root, data_dir, results_dir} and not any(output_dir == p or output_dir in p.parents for p in protected)
        if safe_output:
            output_dir.mkdir(parents=True, exist_ok=True)
            write_json(output_dir / "audit.json", {"audit_schema_version": 1, "passed": False,
                "complete": False, "created_at": datetime.now(timezone.utc).isoformat(),
                "discrepancies": [{"check": "fatal input or review validation error", "error_type": type(error).__name__, "error": str(error)}],
                "human_review": {"status": "pending", "existing_packet_preserved": True}})
            (output_dir / "REPORT.md").write_text("# Person 1 independent preliminary audit\n\n"
                "Automated result: **FAIL — audit incomplete**. No validation claims are made. Human sign-off remains pending.\n\n"
                f"Fatal input or review validation error: `{type(error).__name__}: {error}`.\n\n"
                "Inputs were not repaired. Existing review CSV and Markdown packet were preserved; any other files from a prior successful run are stale.\n",
                encoding="utf-8")
        print(f"Audit could not complete: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"passed": result["passed"], "checks": result["checks_performed"], "discrepancies": len(result["discrepancies"]),
                      "responses": result["reconciled_scored_records"], "config_hash": result["config_hash"]}, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
