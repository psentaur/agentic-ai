# Person 2: local GPU execution

The host RTX 4060 Laptop GPU and driver work. GPU device nodes are hidden inside the tool sandbox, so CUDA commands run outside it. No driver repair is needed.

The local Python 3.12 environment is `.venv-gpu`, with Torch 2.8.0+cu126 and the project's pinned GPU/analysis libraries. Both pinned Qwen checkpoints use NF4 with FP16 compute through `configs/local-nf4.json`. No other scientific settings change. Exact installed packages are saved in the results folder.

To recreate the GPU environment, use Python 3.12 and install Torch before the project extras:

```bash
UV_CACHE_DIR="$PWD/.cache/uv" uv venv .venv-gpu --python 3.12
UV_CACHE_DIR="$PWD/.cache/uv" uv pip install --python .venv-gpu/bin/python torch==2.8.0 --index-url https://download.pytorch.org/whl/cu126
UV_CACHE_DIR="$PWD/.cache/uv" uv pip install --python .venv-gpu/bin/python -e '.[analysis,gpu]' 'torch==2.8.0+cu126'
```

Preserve the saved package freeze for the official run rather than upgrading between stages. Model-download connection errors can be resumed from cached partial files; the local workflow stops on these errors so they can be diagnosed and rerun without changing scientific settings.

From the project root, resume the complete preliminary workflow with:

```bash
systemd-inhibit --what=sleep:idle --mode=block --why='Indic preliminary GPU study' .venv-gpu/bin/python -u scripts/local_run.py
```

The workflow verifies power/CUDA, completes one 23-condition problem per model, expands to 460 smoke responses, then 2,300 pilot responses. Longest budgets run first within each problem. If the larger model fails specifically because of memory, it records the fallback and completes all 100 development IDs on the smaller model. Other errors stop the workflow for diagnosis.

For smaller execution stages, add `--stage preflight`, `--stage feasibility`, or `--stage smoke`. Rerunning preserves completed keys. Use one process at a time and preserve the source/configuration/environment after generating official responses.

Results and execution log are in `results/local-nf4-v1`. `preflight.json` records host/software checks; `execution_report.json` records exact coverage, errors, timings, tokens, memory, and output diagnostics. `HANDOFF.md` contains the Person 2 methods paragraph and handoffs. Scored records, balanced figures, and an error-review sample are generated at completion.

No router fitting or held-out inference runs in this preliminary workflow. Native-language script checks remain proxies; apparent accuracy declines require checking parsing, truncation, and step compliance.
