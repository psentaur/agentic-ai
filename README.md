# Indic explanation-budget study

This workspace implements the agreed four-person project plan. **Person 2's local preliminary milestone is complete: 2,300 genuine responses across 50 matched IDs and both models.** Both models ran with NF4 on the RTX 4060 Laptop GPU. See [the local handoff](results/local-nf4-v1/HANDOFF.md), [pilot results](results/local-nf4-v1/analysis/pilot/both-models/report.md), and [validation](results/local-nf4-v1/validation.json). No held-out inference or router training has run.

Start with [TEAM_PLAN.md](TEAM_PLAN.md) for ownership and deadlines, [docs/PROTOCOL.md](docs/PROTOCOL.md) for the frozen experimental decisions, and [docs/LOCAL_RUN.md](docs/LOCAL_RUN.md) for local execution. [notebooks/colab.ipynb](notebooks/colab.ipynb) remains an optional alternative.

## What is included

- Original MGSM data at a pinned revision: 750 question records, with 100 development and 150 held-out problem IDs shared across languages.
- Pinned Qwen3-1.7B/4B model revisions, 23 conditions per model/problem, matched prompts, and seeded generation.
- Resumable inference with durable records, numerical scoring, script/step diagnostics, paired bootstrap comparisons, and scientific plots.
- A question-only decision-tree router, grouped development validation, fixed baselines, language-feature ablation, and a checked freeze before test inference.
- An ACL LaTeX draft, source-verified bibliography, Overleaf packaging, and teammate checklists.

## Run locally on this PC

Use [docs/LOCAL_RUN.md](docs/LOCAL_RUN.md) for the isolated CUDA environment, both-model NF4 configuration, persistent results, and one-command preliminary workflow. The RTX 4060 Laptop GPU works outside the sandbox.

Inspect the completed local run with its own configuration and results directory:

```bash
.venv-gpu/bin/python -m study --config configs/local-nf4.json --results-dir results/local-nf4-v1 status
```

The local run contains 1,150 responses per model, all 46 model/condition cells have 50 IDs, and a repeated pilot command generated zero new responses. Parsing failures and truncated outputs remain in the scored denominator. The milestone covers half of development and 20% of the full planned study.

## Person 1 evaluation audit

The separate audit script checks original source files, dataset rows/splits, pilot provenance and coverage, independent numerical scoring, and the saved summary/paired-contrast tables. It does not change the frozen production pipeline or repair discrepancies automatically.

```bash
.venv-gpu/bin/python scripts/audit_person1.py
```

Read [the audit evidence](results/local-nf4-v1/person1-audit/REPORT.md) and [Person 1's manual tasks](docs/MANUAL_TASKS.md). All ten numerical cases now have completed annotations by Mukthish dated October 13, 2026; the user's later confirmation records remaining Person 1 checks complete. The original blank copy and historical automated evidence are preserved. Rerunning the audit preserves existing annotations.

## Run the preliminary experiments on a free GPU

1. Download `dist/indic-study.zip` and `notebooks/colab.ipynb` from this workspace.
2. Open the notebook in Google Colab and select a GPU runtime.
3. Follow its upload, dependency-installation, and Drive-checkpoint cells.
4. Run the two-model smoke test, inspect measured runtime, then run the pilot.
5. Check `status`: the balanced pilot must contain **2,300 completed responses**, covering 50 IDs, to reach 20% of the declared 11,500-response grid.

The fallback is 100 development IDs on Qwen3-1.7B alone, also 2,300 responses. Its size comparison remains pending. Never count failed calls, duplicate records, input-token measurements, or synthetic tests as model evaluation.

## Local commands

Preparation, workload planning, and scoring use the Python standard library. Plotting and routing need the `analysis` extra. Tokenization characterization needs `analysis,tokenizer`. Actual model inference additionally needs `gpu` and a working CUDA device.

```bash
# With uv and a Python 3.12 interpreter:
uv sync --extra analysis --extra tokenizer --python 3.12
source .venv/bin/activate

python -m study prepare
python -m study plan --phase pilot
python -m study status
python -m unittest discover -s tests -v
```

On this machine, the prepared `.venv/bin/python` can run the analysis and tests directly. On another machine, `python -m pip install -e '.[analysis,tokenizer]'` is an alternative. `uv.lock` records the resolved environment.

All global options precede the subcommand:

```bash
python -m study --results-dir /path/to/persistent/results run --phase smoke --model qwen3-1.7b --limit 23
python -m study --results-dir /path/to/persistent/results run --phase smoke --model qwen3-4b --limit 23
python -m study --results-dir /path/to/persistent/results run --phase smoke
python -m study --results-dir /path/to/persistent/results run --phase pilot
python -m study --results-dir /path/to/persistent/results score --split development
python -m study --results-dir /path/to/persistent/results analyze --phase pilot
python -m study --results-dir /path/to/persistent/results review-sample --split development

# Alternative preliminary milestone if the larger model is unavailable:
python -m study --results-dir /path/to/persistent/results run --phase development --model qwen3-1.7b
python -m study --results-dir /path/to/persistent/results analyze --phase development --model qwen3-1.7b

# After the mid-sem submission:
python -m study --results-dir /path/to/persistent/results run --phase development
python -m study --results-dir /path/to/persistent/results train-router
python -m study --results-dir /path/to/persistent/results run --phase test
python -m study --results-dir /path/to/persistent/results analyze --phase test
python -m study --results-dir /path/to/persistent/results evaluate-router
python -m study --results-dir /path/to/persistent/results route --model qwen3-1.7b --language en --question 'There are 12 eggs in each of 3 boxes. How many eggs?'
```

`run` skips already completed keys, so smoke and pilot responses are reused in development. Infrastructure failures are logged separately and stop the runner; rerun the same command after resolving the failure. A partial final JSONL line must be backed up and removed before resuming; malformed files are never silently discarded.

## Outputs and handoffs

| Artifact | Producer | Consumer |
|---|---|---|
| `data/records.jsonl`, `data/manifest.json` | Person 1 | Everyone |
| `results/raw/<model>.jsonl` | Person 2 | Persons 1, 3, 4 |
| `results/scored/*.jsonl` | Person 1 | Person 3 |
| `results/analysis/<phase>/<model>/` | Person 3 | Person 4 |
| `results/analysis/*_review.csv` | Person 4 | Discussion and limitations |
| `results/router/`, `results/freeze.json` | Person 3 | Person 2 and final report |
| `paper/main.tex`, `paper/references.bib` | All four; Person 4 integrates | Overleaf submission |

Pipeline Python files, prompts, generation settings, dataset, and splits contribute to the experiment fingerprint. Finalize scientific code before official runs. A changed experiment must use a new results folder; old responses cannot be silently mixed. Training the router seals development outputs and artifacts. Retraining after freeze is rejected.

Use only one active notebook runtime writing to a results folder. Local writer locks prevent concurrent processes in that runtime; they are not distributed locks across different Colab sessions.

## Paper and delivery

`paper/main.tex` contains genuine preliminary results and future-work boundaries. The current final report is `output/pdf/final-report.pdf`: four main-text pages, seven total, compiled and visually inspected. BITS Pilani is entered; only author names remain placeholders. Remaining role-specific review records and course submission are separate tasks. Read `paper/README.md` and `results/local-nf4-v1/final-report/REPORT.md` for delivery evidence. Refresh all three current archives with `.venv/bin/python scripts/package_final_report.py`.

```bash
python scripts/package.py
# Optional final archive containing this team's genuine recorded outputs:
python scripts/package.py --include-results
```

This writes `dist/indic-study.zip` and `dist/overleaf-paper.zip`; no virtual environment or model weights are included.


## Person 3 preliminary analysis

Reproduce the pilot analysis without inference or changes to frozen inputs:

```bash
.venv-gpu/bin/python scripts/analyze_person3.py
```

The script accepts `--config`, `--data-dir`, `--results-dir`, and `--output-dir`. It verifies the existing Person 1 audit hashes, reruns the independent audit in a temporary directory, and reproduces production analysis from a temporary raw-results copy. See the [Person 3 report](results/local-nf4-v1/person3-analysis/REPORT.md), [handoff](results/local-nf4-v1/person3-analysis/HANDOFF.md), and [remaining human checks for Persons 1 and 3](docs/MANUAL_TASKS.md). The full condition CSV contains fractions for rates, means for tokens/steps, and integer diagnostic counts. Router and held-out evaluation remain pending.


## Person 4 report and Overleaf

[Overleaf project](https://www.overleaf.com/project/6accbd9876b381cd22410e6d) now contains the final preliminary report: four main-text pages, seven total, zero errors/warnings/overfull boxes. [Current execution evidence](results/local-nf4-v1/final-report/REPORT.md) and final PDF are saved; the earlier six-page Person 4 export is preserved. Literature notes/claim map are in paper; [40-case evidence and ten double reviews](results/local-nf4-v1/person4-review/README.md) retain blank semantic judgments. Reproduce packets with `.venv/bin/python scripts/build_person4_packet.py` (configurable input/output paths). All 38 tests passed during Person 4 implementation; this manuscript-only revision preserves frozen scientific files and the fingerprint. [Manual checks](docs/MANUAL_TASKS.md) record completed Person 1 reviews and separate remaining Person 3/4 checks. Only author names remain report placeholders; invitations, portal rules and submission remain separate tasks.
