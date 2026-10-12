# Benchmark provenance and licensing

MGSM questions and numerical targets are copied from the original Google Research parallel release:

- Repository: https://github.com/google-research/url-nlp/tree/main/mgsm
- Pinned revision: `3622039cf51f7eeffa58b957332a8e8c337981d7`
- Original files and SHA-256 checksums: `manifest.json`, `raw/<revision>/mgsm_{en,bn,te}.tsv`
- MGSM original license: `LICENSE.mgsm.txt`, from the adjacent source license at the pinned revision.
- Underlying GSM8K source: https://github.com/openai/grade-school-math
- Underlying GSM8K license notice: `LICENSE.gsm8k.txt`.

The records are the published parallel benchmark, not new team-authored translations. The project uses row-based IDs shared across translations and verifies all numerical answers. Development and held-out split membership are fixed in the manifest. No local model-generated answers are included in this folder.

`characterization/` contains actual input-token measurements on the 100 development IDs only. Its report records tokenizer revisions, software versions, and methodology. Those measurements are separate from mathematical answer evaluation and do not satisfy the 2,300-response inference milestone.
