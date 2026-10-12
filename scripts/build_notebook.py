"""Generate the handoff notebook; cells have no saved or invented execution output."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def markdown(source):
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)}


def code(source):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": source.splitlines(keepends=True)}


def main():
    cells = [
        markdown("""# Indic explanation-budget study — GPU execution

**Owner: Person 2.** Open in Google Colab and choose **Runtime → Change runtime type → GPU**.
This notebook executes genuine model inference. It has no saved model results.

Download `dist/indic-study.zip` from the prepared workspace and upload it in the first cell.
Results are checkpointed to your Google Drive, so runtime interruption does not require restarting completed calls.
Use one ordinary interactive notebook; free GPU availability is not guaranteed. Do not rotate accounts to bypass quotas.
"""),
        code("""from pathlib import Path
import os, sys, json, subprocess, zipfile
from google.colab import files

uploaded = files.upload()
archives = [name for name in uploaded if name.endswith('.zip')]
assert len(archives) == 1, 'Upload the single indic-study.zip archive.'
with zipfile.ZipFile(archives[0]) as archive:
    for member in archive.infolist():
        assert (Path('/content') / member.filename).resolve().is_relative_to(Path('/content')), 'Unexpected archive path'
    archive.extractall('/content')
PROJECT = Path('/content/indic-study')
assert (PROJECT / 'configs/study.json').exists(), 'This is not the prepared study bundle.'
os.chdir(PROJECT)
os.environ['HF_HOME'] = '/content/indic-study-model-cache'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
"""),
        markdown("""## Install the pinned libraries

The project pins Transformers, analysis libraries, and model revisions. PyTorch uses the compatible installed version when it meets the requirement; the runner records versions and rejects a changed environment on resume. Installation does not start inference.
"""),
        code("""subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-e', '.[analysis,gpu]'], check=True)
import torch
assert torch.cuda.is_available(), 'No CUDA GPU: select a GPU runtime before proceeding.'
print('GPU:', torch.cuda.get_device_name())
print('GPU memory GiB:', round(torch.cuda.get_device_properties(0).total_memory / 2**30, 2))
"""),
        markdown("""## Persistent results and precision

Keep `USE_4BIT=False` initially. If the larger model does not fit, set it to `True` for BOTH models before official inference. That configuration gets a separate results folder and must not reuse FP16 outputs. Mounting Drive may ask you to authorize your own account.
"""),
        code("""from google.colab import drive
drive.mount('/content/drive')
USE_4BIT = False
SINGLE_MODEL_FALLBACK = False  # Set only if the larger model blocks the preliminary milestone.
RUN_TAG = 'nf4-v1' if USE_4BIT else 'fp16-v1'
RESULTS = Path('/content/drive/MyDrive/indic-reasoning-study') / RUN_TAG / 'results'
RESULTS.mkdir(parents=True, exist_ok=True)
config_path = PROJECT / 'configs/study.json'
config = json.loads(config_path.read_text())
config['generation']['quantization'] = '4bit' if USE_4BIT else 'none'
config_path.write_text(json.dumps(config, indent=2) + '\\n')

def cli(*arguments):
    command = [sys.executable, '-m', 'study', '--results-dir', str(RESULTS), *arguments]
    subprocess.run(command, cwd=PROJECT, check=True)

cli('prepare')
cli('plan', '--phase', 'pilot')
cli('status')
"""),
        markdown("""## First feasibility block: one problem, every condition, both models

This makes 23 new calls per model. Check memory, output lengths, parse failures, and truncation before expanding. The same keys will be reused in smoke, pilot, and development runs.
"""),
        code("""cli('run', '--phase', 'smoke', '--model', 'qwen3-1.7b', '--limit', '23')
if not SINGLE_MODEL_FALLBACK:
    cli('run', '--phase', 'smoke', '--model', 'qwen3-4b', '--limit', '23')
cli('score', '--split', 'development')
cli('status')
"""),
        markdown("""## Complete the 10-ID smoke block and estimate remaining GPU time

The full smoke grid is 460 responses (230 for the smaller-model fallback). Never interpret its small sample as a confirmed cliff. The estimate below uses measured per-model mean latency and adds 30% for interruption/loading overhead; available free GPU time can be lower than the estimate requires.
"""),
        code("""smoke_options = ['--model', 'qwen3-1.7b'] if SINGLE_MODEL_FALLBACK else []
cli('run', '--phase', 'smoke', *smoke_options)
cli('analyze', '--phase', 'smoke', *smoke_options)
from study.common import load_config
from study.data import load_data
from study.results import load_scored
cfg = load_config()
manifest, dataset = load_data(cfg, PROJECT / 'data')
rows = load_scored(cfg, manifest, dataset, RESULTS)
for model in cfg['models']:
    measured = [row for row in rows if row['model'] == model]
    if not measured:
        continue
    seconds = sum(row['latency_seconds'] for row in measured) / len(measured)
    print(model, 'mean seconds/response:', round(seconds, 2),
          'estimated 50-ID model grid GPU-hours:', round(seconds * 1150 * 1.3 / 3600, 2),
          'truncated:', sum(row['truncated'] for row in measured))
"""),
        markdown("""## October 13 preliminary milestone

Default: 50 matched development IDs × both models × 23 conditions = **2,300 responses**.
Fallback: if selected above, finish all 100 development IDs × smaller model × 23 conditions = **2,300 responses**. The size comparison remains pending.

Checkpointing is immediate. If interrupted, reconnect, restore the same bundle/configuration/environment, and rerun the command; completed keys are skipped.
"""),
        code("""if SINGLE_MODEL_FALLBACK:
    cli('run', '--phase', 'development', '--model', 'qwen3-1.7b')
    cli('analyze', '--phase', 'development', '--model', 'qwen3-1.7b')
else:
    cli('run', '--phase', 'pilot')
    cli('analyze', '--phase', 'pilot')
cli('score', '--split', 'development')
cli('review-sample', '--split', 'development')
cli('status')
"""),
        markdown("""## Handoff to Persons 1, 3, and 4

Share the results folder with your teammates yourself. Inspect `analysis/<phase>/<model>/report.md`, `summary.csv`, `paired_contrasts.csv`, and `accuracy_curves.pdf`.
The review CSV is for Person 4. Check script flags as proxies, not native-language fluency judgments.
Insert genuine curves/tables into Overleaf. State the exact coverage and one actual observed insight.

**Stop here for the mid-sem milestone. The remaining cells are for the full study after development completion.**
"""),
        markdown("""## Complete development, validate router, and lock the test design

All 4,600 development responses are required. Router fitting uses grouped folds and training-fold baseline selection.
The freeze records code/config/data hashes, development outputs, and router checksums. Do not change or retrain the study after accessing test results.
"""),
        code("""cli('run', '--phase', 'development')
cli('analyze', '--phase', 'development')
cli('train-router')
print('Frozen router and metrics:', RESULTS / 'router')
"""),
        markdown("""## Held-out evaluation: 6,900 responses

This command is blocked unless the freeze is valid. No prompt, feature, baseline, or tree fitting uses held-out answers.
Final router evaluation selects cached native outputs and adds no model calls.
"""),
        code("""cli('run', '--phase', 'test')
cli('score', '--split', 'test')
cli('analyze', '--phase', 'test')
cli('evaluate-router')
cli('review-sample', '--split', 'test')
cli('status')
"""),
        markdown("""## Final delivery

Person 3 hands off router metrics and paired contrasts. Person 1 audits the numbers and reproduces figures. Person 4 completes the paper, and all four review the PDF.
Keep raw records and the freeze in Drive; the code/source archive alone does not contain the team's GPU outputs.
"""),
        code("""cli('route', '--model', 'qwen3-1.7b', '--language', 'en',
    '--question', 'There are 12 eggs in each of 3 boxes. How many eggs?')
print('Persistent final results:', RESULTS)
""")
    ]
    notebook = {"nbformat": 4, "nbformat_minor": 5, "metadata": {
        "colab": {"name": "Indic reasoning-budget study", "provenance": []}, "accelerator": "GPU",
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"}}, "cells": cells}
    for index, cell in enumerate(cells):
        cell["id"] = f"study-{index:02d}"
    folder = ROOT / "notebooks"
    folder.mkdir(exist_ok=True)
    (folder / "colab.ipynb").write_text(json.dumps(notebook, indent=2) + "\n", encoding="utf-8")
    print(f"Created {len(cells)} clean notebook cells")


if __name__ == "__main__":
    main()
