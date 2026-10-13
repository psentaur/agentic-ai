# Final preliminary ACL report

The [Overleaf project](https://www.overleaf.com/project/6accbd9876b381cd22410e6d) contains the current `main.tex` and compiles with pdfLaTeX / TeX Live 2026. The final export is `output/pdf/final-report.pdf`: **four main-text pages, seven total**. All seven pages were rendered and visually inspected. Compilation has zero errors, zero warnings, and zero overfull boxes; informational underfull-box entries do not clip content. The downloaded nine-file Overleaf source matches local inputs byte for byte. Supplied ACL styles remain unchanged.

The title is **Explanation Budgets for Small Multilingual Language Models: A Preliminary MGSM Study**. The affiliation is **BITS Pilani**, as supplied by the user. Only the four author names remain placeholders. No campus, postal address, or email was invented.

The report contains the audited 2,300-response pilot, completed ten-case human numerical review, observable error evidence, limitations, exact prompts, and reproducibility details. Router training, ablation, and held-out evaluation are explicitly future work. Blank semantic-review packets are preserved; the report does not claim semantic categories or completed double reviews.

Current compilation, preservation, requirement checks, and delivery evidence are in `results/local-nf4-v1/final-report`. The earlier `preliminary-mgsm-study.pdf` and Person 4 compilation evidence remain unchanged as historical artifacts. Person 1's human checks are recorded complete from the user's October 13 confirmation; remaining role-specific records and submission steps are documented in `docs/MANUAL_TASKS.md`.

Fifteen cited references include two preprints (13.3%). Source-linked metadata and claim verification are in `literature-verification.md` and `claim-source-map.json`; the full mCoT PDF access limitation remains explicit. The abstract has 162 words, the Introduction ends with three contribution bullets, and all citation keys resolve.

Refresh and verify all three deliverable archives with:

```bash
.venv/bin/python scripts/package_final_report.py
```

`dist/overleaf-paper.zip` contains only source and figure inputs. Both results packages include the current final PDF, status documents, completed Person 1 annotations, and preserved original review sheets. No course submission or teammate invitation is claimed.
