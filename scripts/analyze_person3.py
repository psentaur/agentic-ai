#!/usr/bin/env python3
"""Read-only pilot inputs; reproducible Person 3 tables and paired diagnostics.

No inference, policy fitting, score repair, or production-source changes.
CSV rates are fractions, token/step fields are means, and counts are integers.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import audit_person1 as audit


def hash_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_cohort(rows, ids, models):
    expected = {(m, i, lang, explanation, budget)
                for m in models for i in ids for lang in ('en', 'bn', 'te')
                for budget in (0, 2, 4, 8, 16)
                for explanation in ([lang, 'en'] if lang != 'en' and budget else [lang])}
    keys = [(r['model'], r['problem_id'], r['language'], r['reasoning_language'], r['budget']) for r in rows]
    if len({r['experiment_id'] for r in rows}) != len(rows) or len(set(keys)) != len(keys):
        raise ValueError('Duplicate experiment ID or condition')
    if set(keys) != expected or len(rows) != len(expected):
        raise ValueError('Incomplete or unexpected matched pilot cohort')
    if any(r['split'] != 'development' for r in rows):
        raise ValueError('Only development pilot outputs are allowed')


def pair_diagnostics(short, long):
    if short['problem_id'] != long['problem_id'] or short['model'] != long['model'] or short['language'] != long['language']:
        raise ValueError('Pair must match problem, model and question language')
    return {'model': short['model'], 'language': short['language'], 'problem_id': short['problem_id'],
            'experiment_id_4': short['experiment_id'], 'experiment_id_16': long['experiment_id'],
            'correct_4': int(short['correct']), 'correct_16': int(long['correct']),
            'transition': f"{int(short['correct'])}_to_{int(long['correct'])}",
            'accuracy_delta': int(long['correct']) - int(short['correct']),
            **{f'{key}_{budget}': row[key] if row[key] is not None else ''
               for budget, row in ((4, short), (16, long))
               for key in ('parse_error', 'truncated', 'step_compliant', 'actual_steps', 'output_tokens')},
            'any_parse_failure': short['parse_error'] is not None or long['parse_error'] is not None,
            'any_truncation': short['truncated'] or long['truncated'],
            'any_step_noncompliance': not short['step_compliant'] or not long['step_compliant']}


def transition_summary(pairs):
    if not pairs:
        raise ValueError('No matched pairs')
    losses = [p for p in pairs if p['transition'] == '1_to_0']
    gains = [p for p in pairs if p['transition'] == '0_to_1']
    valid = [p for p in pairs if not p['any_parse_failure']]
    return {'model': pairs[0]['model'], 'language': pairs[0]['language'], 'n': len(pairs),
            **{name: sum(p['transition'] == name for p in pairs) for name in ('0_to_0', '0_to_1', '1_to_0', '1_to_1')},
            'net_correct_change': len(gains) - len(losses),
            'losses_parse_failure_at_16': sum(bool(p['parse_error_16']) for p in losses),
            'gains_parse_failure_at_4': sum(bool(p['parse_error_4']) for p in gains),
            **{f'losses_{flag}': sum(bool(p[flag]) for p in losses)
               for flag in ('any_parse_failure', 'any_truncation', 'any_step_noncompliance')},
            'both_parse_valid_n': len(valid),
            'both_parse_valid_net_correct_change': sum(p['accuracy_delta'] for p in valid)}


def markdown_table(rows, fields):
    return '\n'.join(['| ' + ' | '.join(fields) + ' |', '| ' + ' | '.join(['---'] * len(fields)) + ' |'] +
                     ['| ' + ' | '.join(str(r[k]) for k in fields) + ' |' for r in rows])


def compact_table(summary, contrasts):
    lookup = {(r['model'], r['language'], r['reasoning_language'], r['budget']): r for r in summary}
    result = []
    for model in sorted({r['model'] for r in summary}):
        for lang in ('en', 'bn', 'te'):
            a, b = (lookup[model, lang, lang, budget] for budget in (4, 16))
            contrast = next(r for r in contrasts if r['model'] == model and r['contrast'] == f'{lang}: native 16 minus 4 steps')
            result.append({'model': model, 'language': lang, 'n': a['n'],
                           **{f'{key}_{budget}': row[key] for budget, row in ((4, a), (16, b))
                              for key in ('accuracy', 'mean_output_tokens', 'mean_actual_steps', 'step_compliance', 'parse_failure_rate', 'truncation_rate')},
                           **{key: contrast[key] for key in ('accuracy_difference', 'ci_low', 'ci_high')}})
    return result


def tex_table(rows):
    lines = [r'\begin{table*}[t]', r'\centering', r'\small', r'\setlength{\tabcolsep}{4pt}',
             r'\begin{tabular}{llrrrrrr}', r'\toprule',
             r'Model & Language & \shortstack{Accuracy\\(\%)} & \shortstack{Mean\\tokens} & \shortstack{Mean\\steps} & \shortstack{Count match\\(\%)} & \shortstack{Parse fail\\(\%)} & \shortstack{Truncated\\(\%)} \\', r'\midrule']
    for r in rows:
        cells = [r['model'].replace('qwen3-', 'Qwen3-'), r['language'].upper()]
        for key, scale, precision in [('accuracy', 100, 0), ('mean_output_tokens', 1, 1), ('mean_actual_steps', 1, 1),
                                      ('step_compliance', 100, 0), ('parse_failure_rate', 100, 0), ('truncation_rate', 100, 0)]:
            cells.append(f"{r[key + '_4'] * scale:.{precision}f}$\\to${r[key + '_16'] * scale:.{precision}f}")
        lines.append(' & '.join(cells) + r' \\')
    lines += [r'\bottomrule', r'\end{tabular}',
              r'\caption{Native four- to sixteen-step comparisons on the same 50 development IDs per row. Arrows show four-step then sixteen-step values. Accuracy retains parse failures and truncated outputs. Steps are mean numbered-line counts; count match does not establish semantic compliance.}',
              r'\label{tab:pilot-native}', r'\end{table*}']
    return '\n'.join(lines) + '\n'


def run(config_path, data_dir, results_dir, output_dir):
    results_dir, output_dir = Path(results_dir).resolve(), Path(output_dir).resolve()
    source = results_dir / 'analysis/pilot/both-models'
    protected = set(audit.input_paths(ROOT, data_dir, config_path, results_dir))
    protected |= {p for d in ('raw', 'scored', 'analysis', 'person1-audit') for p in (results_dir / d).rglob('*') if p.is_file()}
    if output_dir in (ROOT, results_dir, Path(data_dir).resolve()) or any(output_dir == p or output_dir in p.parents for p in protected):
        raise ValueError('Output directory could overwrite protected inputs')
    before = {str(p): hash_file(p) for p in sorted(protected)}
    recorded_audit = audit.read_json(results_dir / 'person1-audit/audit.json')
    if not recorded_audit['passed']:
        raise ValueError('Existing Person 1 audit did not pass')
    # Locate recorded inputs even when this immutable run is copied elsewhere.
    for original_path, expected_hash in recorded_audit['protected_inputs_after'].items():
        path = Path(original_path)
        if path.is_relative_to(ROOT / 'results/local-nf4-v1'):
            path = results_dir / path.relative_to(ROOT / 'results/local-nf4-v1')
        elif path.is_relative_to(ROOT / 'data'):
            path = Path(data_dir) / path.relative_to(ROOT / 'data')
        elif path == ROOT / 'configs/local-nf4.json':
            path = Path(config_path)
        if hash_file(path) != expected_hash:
            raise ValueError('Input differs from the recorded Person 1 audit: ' + str(path))
    with tempfile.TemporaryDirectory(prefix='person3-reproduce-') as temp:
        temp = Path(temp)
        fresh_audit = audit.run_audit(ROOT, data_dir, config_path, results_dir, temp / 'audit')
        if not fresh_audit['passed']:
            raise ValueError('Independent audit failed; results were not repaired')
        copy = temp / 'results'
        shutil.copytree(results_dir / 'raw', copy / 'raw')
        command = [sys.executable, '-m', 'study', '--config', str(config_path), '--data-dir', str(data_dir),
                   '--results-dir', str(copy), 'analyze', '--phase', 'pilot']
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
        original = audit.read_json(source / 'analysis.json')
        reproduced = audit.read_json(copy / 'analysis/pilot/both-models/analysis.json')
        if not audit.equal(original, reproduced):
            raise ValueError('Reproduced production analysis disagrees')
        for name in ('summary.csv', 'paired_contrasts.csv'):
            if (source / name).read_bytes() != (copy / 'analysis/pilot/both-models' / name).read_bytes():
                raise ValueError('Reproduced table differs: ' + name)
    rows = audit.read_jsonl(results_dir / 'scored/development.jsonl')
    manifest = audit.read_json(data_dir / 'manifest.json')
    config = audit.read_json(config_path)
    validate_cohort(rows, manifest['splits']['pilot'], config['models'])
    summary, contrasts = original['summary'], original['contrasts']
    if len(summary) != 46 or len(contrasts) != 26 or any(r['n'] != 50 for r in summary + contrasts):
        raise ValueError('Expected 46 summary and 26 contrast rows, each N=50')
    groups = defaultdict(list)
    for r in rows:
        groups[r['model'], r['language'], r['reasoning_language'], r['budget']].append(r)
    full = []
    for r in summary:
        group = groups[r['model'], r['language'], r['reasoning_language'], r['budget']]
        full.append({**r, 'correct_count': sum(x['correct'] for x in group),
                     'parse_failure_count': sum(x['parse_error'] is not None for x in group),
                     **{f'{kind}_count': sum(x['parse_error'] == kind for x in group)
                        for kind in ('missing_marker', 'multiple_markers', 'invalid_number')},
                     'step_compliant_count': sum(x['step_compliant'] for x in group),
                     'truncated_count': sum(x['truncated'] for x in group)})
    compact = compact_table(summary, contrasts)
    lookup = {(r['model'], r['language'], r['reasoning_language'], r['budget'], r['problem_id']): r for r in rows}
    pairs, transitions = [], []
    for model in sorted(config['models']):
        for lang in ('en', 'bn', 'te'):
            selected = [pair_diagnostics(lookup[model, lang, lang, 4, i], lookup[model, lang, lang, 16, i])
                        for i in sorted(manifest['splits']['pilot'])]
            transitions.append(transition_summary(selected))
            pairs += selected
    after = {str(p): hash_file(p) for p in sorted(protected)}
    if before != after:
        raise ValueError('Protected input changed during analysis')
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, values in [('condition_table', full), ('compact_native_table', compact), ('paired_transitions', pairs),
                         ('transition_summary', transitions), ('paired_contrasts', contrasts)]:
        audit.write_csv(output_dir / f'{name}.csv', values)
    (output_dir / 'compact_native_table.tex').write_text(tex_table(compact))
    for ext in ('png', 'pdf'):
        shutil.copy2(source / f'accuracy_curves.{ext}', output_dir / f'accuracy_curves.{ext}')
    evidence = {'passed': True, 'config_hash': original['config_hash'], 'responses': len(rows), 'matched_ids': 50,
                'per_model': dict(sorted(Counter(r['model'] for r in rows).items())), 'held_out_responses': 0,
                'summary_rows': 46, 'paired_contrast_rows': 26, 'transition_rows': len(pairs),
                'independent_audit_checks': fresh_audit['checks_performed'], 'discrepancies': [],
                'production_reproduction': {k: json.loads(completed.stdout)[k] for k in ('cohort_ids', 'responses')},
                'floating_point_tolerance': audit.TOLERANCE,
                'protected_inputs_unchanged': True, 'protected_input_hashes': before,
                'human_sign_off': 'pending', 'router': 'pending: remaining 2300 development responses required',
                'transition_summary': transitions, 'compact_native_table': compact}
    audit.write_json(output_dir / 'analysis.json', evidence)
    report = """# Person 3 preliminary quantitative analysis

Automated analysis is complete. Human interpretation, numerical and rendered-manuscript sign-off remain pending.
The cohort contains 2,300 responses, 50 matched development IDs, 1,150 per model, 46 condition cells with N=50, and zero held-out outputs.
The independent audit and temporary production-analysis reproduction agree. No inputs were repaired and no inference or router fitting occurred.

## RQ1: requested budgets and diagnostic interpretation

For Qwen3-4B English native explanations, four to sixteen requested steps changes accuracy from 43/50 (86%) to 37/50 (74%): −12 percentage points, exploratory paired 95% interval [−24, −2]. Mean generated tokens rise from 118.88 to 318.56 (2.68 times), mean numbered steps from 4.04 to 15.92, and count compliance is 49/50 (98%) at both budgets. Neither condition is truncated.

The matched outcomes comprise 36 correct at both budgets, seven correct-to-incorrect, one incorrect-to-correct, and six incorrect at both. Four of the seven losses have a missing-marker parse failure at sixteen steps. Parse failures rise from 1/50 to 5/50. These associations qualify interpretation of the numerical-score decline; they do not prove a causal explanation. The primary comparison retains all 50 IDs.

Among the 45 pairs parseable at both budgets, correct counts change from 39 to 37. This is a selected diagnostic subset, not a replacement accuracy estimate or hypothesis test. Flag overlaps are retained in the paired file and must not be summed as mutually exclusive causes.

The smaller model's English native curve is nonmonotone: 14%, 54%, 34%, 28%, 44% at 0/2/4/8/16 requested steps. Its four-to-sixteen difference is +10 points with interval [−8, 26.05]; parse failures are 42% and 34%, while numbered-step compliance falls from 84% to 10%. Requested and actual explanation length therefore differ substantially.

## RQ2: language, pivot and checkpoint comparisons

Native sixteen-minus-four differences (EN, BN, TE) are +10, +2, +16 points for 1.7B and −12, −8, −10 for 4B. All four Indic-minus-English difference-in-effect intervals include zero; these pilot data do not establish a stronger Indic decline. Larger-checkpoint scores are descriptively higher in all matched cells, but checkpoint differences cannot be attributed solely to parameter count.

English pivot does not show a uniform accuracy advantage. For 1.7B Bengali at four steps, pivot minus native is −18 points [−30, −6], while 1.7B Telugu at four steps is +16 [4, 28]. All 26 prespecified contrasts are exported, with 2,000 shared-ID bootstrap resamples and seed 42. Intervals are exploratory and have no multiplicity adjustment. Parsing, truncation and actual counts remain visible for every condition; script counts do not measure fluency or semantic quality.

## Tables and evidence

CSV rates and intervals are fractions; counts are integers; token and step values are means. Only Markdown/LaTeX displays round numbers. `condition_table.csv` has all 46 cells and diagnostic counts. `compact_native_table.csv` and `.tex` compare four versus sixteen native steps in six model/language rows. `paired_transitions.csv` has 300 matched pairs with exact experiment IDs and overlapping flags. `transition_summary.csv` aggregates six comparisons. `paired_contrasts.csv` contains all 26 audited comparisons. `analysis.json` records source hashes, audit/reproduction checks and coverage. The PNG/PDF curves are byte-identical exports of the audited original.

"""
    report += markdown_table(transitions, ['model', 'language', 'n', '0_to_0', '0_to_1', '1_to_0', '1_to_1', 'losses_parse_failure_at_16'])
    readable = [{'Model': r['model'], 'Question': r['language'], 'Explanation': r['reasoning_language'],
                 'Budget': r['budget'], 'N': r['n'],
                 'Accuracy % [95% CI]': f"{100*r['accuracy']:.1f} [{100*r['accuracy_ci_low']:.1f}, {100*r['accuracy_ci_high']:.1f}]",
                 'Mean tokens': f"{r['mean_output_tokens']:.1f}", 'Mean steps': f"{r['mean_actual_steps']:.2f}",
                 'Count match %': f"{100*r['step_compliance']:.1f}", 'Parse fail %': f"{100*r['parse_failure_rate']:.1f}",
                 'Truncated %': f"{100*r['truncation_rate']:.1f}"} for r in full]
    report += '\n\n## Full condition table\n\n' + markdown_table(readable, list(readable[0])) + '\n'
    readable_contrasts = [{'Model': r['model'], 'Comparison': r['contrast'], 'N': r['n'],
                          'Difference pp': f"{100*r['accuracy_difference']:.2f}",
                          '95% interval pp': f"[{100*r['ci_low']:.2f}, {100*r['ci_high']:.2f}]"} for r in contrasts]
    report += '\n\n## All prespecified paired contrasts\n\n' + markdown_table(readable_contrasts, list(readable_contrasts[0])) + '\n'
    (output_dir / 'REPORT.md').write_text(report, encoding='utf-8')
    (output_dir / 'HANDOFF.md').write_text("""# Person 3 handoff to Person 4

Use `REPORT.md`, all 46 condition rows, all 26 contrasts and six transition summaries when checking claims. `compact_native_table.tex` and `accuracy_curves.pdf` are ready for the manuscript. Figure caption: Numerical accuracy on 50 matched development IDs per condition. Rows are checkpoints and columns question languages. Solid lines are native explanations; dashed lines English pivots. Budgets request visible numbered steps. Error bars are exploratory 95% shared-ID bootstrap intervals, 2,000 resamples, seed 42; no multiplicity-adjusted significance is claimed.

Lead observation: 4B English four-to-sixteen accuracy falls 86% to 74% with higher token cost; four of seven lost correct answers have missing final-answer markers. Keep the formatting caveat and avoid a demonstrated capacity-cliff claim. Human English semantic error review belongs to Person 4 and is not completed here.

Reproduce from the project root:
```bash
.venv-gpu/bin/python scripts/analyze_person3.py
```
Options: `--config`, `--data-dir`, `--results-dir`, `--output-dir`. The existing production analyze command runs only against a temporary raw-results copy. Outputs are deterministic apart from the separate independent audit's temporary timestamp, which is not exported. Inputs and existing human annotations are preserved.

Human sign-off uses `docs/MANUAL_TASKS.md`. Full router work requires the remaining 2,300 development outputs, grouped validation/freeze, and then 6,900 held-out responses. No policy or held-out result is available. Multi-file Overleaf compilation, four-page main-text layout and final captions remain pending.
""", encoding='utf-8')
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/local-nf4.json')
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'data')
    parser.add_argument('--results-dir', type=Path, default=ROOT / 'results/local-nf4-v1')
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    try:
        result = run(args.config.resolve(), args.data_dir.resolve(), args.results_dir,
                     args.output_dir or args.results_dir / 'person3-analysis')
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print(f'Person 3 analysis failed without repairing inputs: {error}', file=sys.stderr)
        return 1
    print(json.dumps({k: result[k] for k in ('passed', 'responses', 'matched_ids', 'summary_rows', 'paired_contrast_rows', 'transition_rows', 'config_hash')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
