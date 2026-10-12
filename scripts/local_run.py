"""Execute Person 2's local preliminary milestone, with durable handoffs."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from study.common import context_hash, load_config, read_json, read_jsonl, write_json
from study.data import load_data
from study.inference import environment
from study.results import coverage, load_scored

CONFIG = ROOT / 'configs/local-nf4.json'
RESULTS = ROOT / 'results/local-nf4-v1'


def state_data():
    cfg = load_config(CONFIG)
    manifest, records = load_data(cfg, ROOT / 'data')
    rows = load_scored(cfg, manifest, records, RESULTS)
    return cfg, manifest, records, rows


def cli(*arguments):
    command = [sys.executable, '-u', '-m', 'study', '--config', str(CONFIG),
               '--results-dir', str(RESULTS), *arguments]
    with (RESULTS / 'execution.log').open('a', buffering=1) as log:
        print('Running:', ' '.join(arguments), flush=True)
        log.write('\n' + datetime.now(timezone.utc).isoformat() + ' ' + ' '.join(arguments) + '\n')
        process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, bufsize=1)
        try:
            for line in process.stdout:
                print(line, end='', flush=True)
                log.write(line)
            code = process.wait()
        except BaseException:
            process.terminate()
            process.wait()
            raise
        if code:
            raise subprocess.CalledProcessError(code, command)


def preflight():
    import torch
    assert torch.cuda.is_available(), 'CUDA unavailable: run outside the sandbox.'
    assert torch.__version__ == '2.8.0+cu126', f'Unexpected Torch build: {torch.__version__}'
    value = torch.ones(8, device='cuda').sum().item()
    assert value == 8
    gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.total,memory.free,driver_version,temperature.gpu',
                                   '--format=csv'], text=True)
    supplies = []
    for path in Path('/sys/class/power_supply').glob('*'):
        if (path / 'type').exists() and (path / 'type').read_text().strip() == 'Mains':
            supplies.append((path / 'online').read_text().strip() == '1')
    if supplies and not any(supplies):
        raise RuntimeError('Connect laptop power before starting this run.')
    cfg, manifest, _, _ = state_data()
    payload = {'checked_at': datetime.now(timezone.utc).isoformat(),
               'config_hash': context_hash(cfg, manifest), 'python': sys.version,
               'versions': environment(), 'cuda_runtime': torch.version.cuda,
               'gpu': gpu, 'cuda_tensor_check': value, 'mains_online': supplies,
               'memory': subprocess.check_output(['free', '-h'], text=True),
               'disk_free_bytes': shutil.disk_usage(ROOT).free}
    write_json(RESULTS / 'preflight.json', payload)
    print(gpu, flush=True)


def handoff(stage, target):
    cfg, manifest, records, rows = state_data()
    metrics = []
    for model in cfg['models']:
        selected = [row for row in rows if row['model'] == model]
        if not selected:
            continue
        count = len(selected)
        mean = sum(row['latency_seconds'] for row in selected) / count
        metrics.append({'model': model, 'completed': count,
                        'accuracy': sum(row['correct'] for row in selected) / count,
                        'mean_seconds': mean,
                        'total_generation_seconds': sum(row['latency_seconds'] for row in selected),
                        'mean_output_tokens': sum(row['output_tokens'] for row in selected) / count,
                        'max_output_tokens': max(row['output_tokens'] for row in selected),
                        'peak_allocated_bytes': max(row['peak_gpu_memory_bytes'] for row in selected),
                        'peak_reserved_bytes': max(row['peak_gpu_reserved_bytes'] for row in selected),
                        'parse_failures': sum(row['parse_error'] is not None for row in selected),
                        'truncated': sum(row['truncated'] for row in selected),
                        'step_compliance': sum(row['step_compliant'] for row in selected) / count,
                        'remaining_target_hours_with_30_percent_overhead': mean * max(0, (2300 if target == 'smaller-model-development' and model == 'qwen3-1.7b' else 1150)-count) * 1.3 / 3600})
    report = {'stage': stage, 'target': target, 'config_hash': context_hash(cfg, manifest),
              'recorded_at': datetime.now(timezone.utc).isoformat(),
              'coverage': coverage(cfg, manifest, records, rows), 'models': metrics,
              'errors': {model: read_jsonl(RESULTS / f'raw/{model}.errors.jsonl') for model in cfg['models']}}
    write_json(RESULTS / 'execution_report.json', report)
    lines = ["# Person 2 local execution handoff", '', f'Stage: {stage}. Target: {target}.',
             '', f'Genuine recorded responses: {len(rows)}; configuration: `{report["config_hash"]}`.', '',
             '| Model | Responses | Mean seconds | Peak allocated GiB | Mean tokens | Parse failures | Truncated | Step compliance |',
             '|---|---:|---:|---:|---:|---:|---:|---:|']
    for metric in metrics:
        lines.append(f'| {metric["model"]} | {metric["completed"]} | {metric["mean_seconds"]:.2f} | {metric["peak_allocated_bytes"]/2**30:.2f} | {metric["mean_output_tokens"]:.1f} | {metric["parse_failures"]} | {metric["truncated"]} | {metric["step_compliance"]:.1%} |')
    completed_models = ', '.join(cfg['models'][metric['model']]['name'] for metric in metrics) or 'no models yet'
    lines += ['', '## Implementation-method paragraph', '',
              f'This stage contains {len(rows)} completed responses from {completed_models} on a local NVIDIA RTX 4060 Laptop GPU. '
              'Both used bitsandbytes NF4 weight quantization with double quantization and FP16 compute, batch size one, '
              'Python 3.12, PyTorch 2.8.0 with CUDA 12.6, Transformers 4.57.1, and bitsandbytes 0.48.1, '
              'native thinking disabled, and the preregistered sampling settings and 4,096-new-token cap. '
              'Longest requested budgets ran first within each matched problem block. Each completed response was flushed '
              'to disk immediately; subsequent stages reused the same experiment IDs. CUDA runtime, software versions, '
              'latency, peak memory, output length, termination, and raw text were recorded. '
              'The measured requested explanation budget is not a measurement of hidden reasoning.', '',
              '## Handoffs', '', 'Person 1: verify raw/scored records and coverage.',
              'Person 3: inspect balanced curves and paired contrasts; router remains pending.',
              'Person 4: review the sampled errors and integrate genuine evidence. '
              'Script/step diagnostics do not establish native-language fluency.', '',
              'The JSON report includes exact phase coverage and runner-recorded infrastructure errors. '
              'Partial/incomplete rows are not a completed milestone.', '',
              '## Artifacts', '',
              '- [Execution report and metrics](execution_report.json)',
              '- [Final coverage, provenance, ordering, and resume validation](validation.json)',
              '- [Feasibility/smoke/pilot measurement history](measurement_history.json)',
              '- [Hardware, driver, runtime, RAM, and disk preflight](preflight.json)',
              '- [Installed environment freeze](environment-freeze.txt)',
              '- [Pilot condition tables and interpretation checks](analysis/pilot/both-models/report.md)',
              '- [Pilot plots](analysis/pilot/both-models/accuracy_curves.png)',
              '- [Paired contrasts](analysis/pilot/both-models/paired_contrasts.csv)',
              '- [Scored development records](scored/development.jsonl)',
              '- [40-case review sample; annotations still pending](analysis/development_review.csv)',
              '- Raw responses: `raw/qwen3-1.7b.jsonl` and `raw/qwen3-4b.jsonl`.',
              '- [Recovered model download interruptions](download_notes.md)']
    if target == 'smaller-model-development':
        lines += ['', '**Fallback:** only the smaller model is required to complete 100 development IDs; '
                  'the two-model comparison remains incomplete. Counts for any larger-model attempts are separate.']
    (RESULTS / 'HANDOFF.md').write_text('\n'.join(lines)+'\n')
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=['preflight', 'feasibility', 'smoke', 'pilot', 'all'], default='all')
    args = parser.parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    os.environ['HF_HOME'] = str(ROOT / '.cache/huggingface')
    os.environ['HF_HUB_DISABLE_XET'] = '1'
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    os.environ['MPLCONFIGDIR'] = str(ROOT / '.cache/matplotlib')
    state_path = RESULTS / 'run_state.json'
    cfg, manifest, _, _ = state_data()
    fingerprint = context_hash(cfg, manifest)
    state = read_json(state_path) if state_path.exists() else {'config_hash': fingerprint, 'target': 'balanced-pilot'}
    assert state['config_hash'] == fingerprint, 'Run fingerprint changed.'
    preflight()
    if args.stage == 'preflight':
        return
    write_json(state_path, state)
    try:
        first_id = manifest['splits']['smoke'][0]
        for model in cfg['models']:
            if model == 'qwen3-4b' and state['target'] != 'balanced-pilot':
                continue
            _, _, _, rows = state_data()
            done = sum(row['model'] == model and row['problem_id'] == first_id for row in rows)
            if done < 23:
                try:
                    cli('run', '--phase', 'smoke', '--model', model, '--limit', str(23-done))
                except subprocess.CalledProcessError:
                    errors = read_jsonl(RESULTS / f'raw/{model}.errors.jsonl')
                    memory_failure = errors and any(term in errors[-1]['error'].lower() for term in ['out of memory', 'offloaded to cpu/disk'])
                    if model != 'qwen3-4b' or not memory_failure:
                        raise
                    state['target'] = 'smaller-model-development'
                    write_json(state_path, state)
                    print('Larger model memory failure: using documented smaller-model fallback.', flush=True)
        cli('score', '--split', 'development')
        handoff('feasibility', state['target'])
        if args.stage == 'feasibility':
            return
        options = ['--model', 'qwen3-1.7b'] if state['target'] != 'balanced-pilot' else []
        cli('run', '--phase', 'smoke', *options)
        cli('analyze', '--phase', 'smoke', *options)
        report = handoff('smoke', state['target'])
        print(json.dumps(report['models'], indent=2), flush=True)
        if args.stage == 'smoke':
            return
        phase = 'pilot' if state['target'] == 'balanced-pilot' else 'development'
        cli('run', '--phase', phase, *options)
        cli('score', '--split', 'development')
        cli('analyze', '--phase', phase, *options)
        cli('review-sample', '--split', 'development')
        cli('status')
        report = handoff('completed', state['target'])
        if phase == 'pilot':
            assert report['coverage']['pilot']['complete'] == 2300
            assert report['coverage']['pilot']['complete_paired_ids'] == 50
        else:
            _, _, _, rows = state_data()
            assert sum(row['model'] == 'qwen3-1.7b' for row in rows) == 2300
        print('Person 2 preliminary milestone completed. Held-out inference remains locked.', flush=True)
    except BaseException:
        handoff('interrupted_or_failed', state['target'])
        raise


if __name__ == '__main__':
    main()
