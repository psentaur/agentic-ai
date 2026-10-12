# Implementation status — October 12, 2026

## Completed locally

- Dataset prepared: 750 translated question records, representing 250 shared IDs.
- Numerical-answer agreement checked across all three languages; seed-42 100/150 split frozen.
- Experiment grid, pinned revisions, matched prompts, resumable inference, scoring, paired analysis, and question-only router implementation prepared.
- Grouped cross-validation, baseline fitting, language ablation, cached held-out comparison, and freeze/tamper checks implemented and exercised with synthetic temporary test fixtures.
- Colab notebook and teammate checklist prepared.
- All 31 pipeline/router/inference/audit/analysis tests pass (24 existing plus seven Person 3 checks); plot exports and notebook code cells checked locally. Local CUDA tensor preflight, both-model feasibility, the full 460-response smoke block, and the 2,300-response pilot are complete.
- Exact pilot grid verified: 50 matched IDs, 1,150 responses per model, all 46 model/condition cells with 50 records, one consistent experiment/environment, no duplicate IDs. A repeated pilot run generated zero new responses; held-out inference was rejected by the freeze gate.
- Raw responses, scored records, balanced plots/paired contrasts, 40-case review sample, hardware/environment records, latency/memory diagnostics, implementation paragraph, and teammate handoff saved in `results/local-nf4-v1`.
- Real input-token characterization completed on all 100 development IDs: mean paired Bengali/English ratio 4.21, Telugu/English 6.36; both pinned tokenizers produced identical counts on this subset.
- ACL draft, unchanged supplied style files, 15 source-checked references, citation audit, and packaging prepared.
- Person 1's separate independent audit passes 169,916 checks: original TSV checksums, all 750 source/record mappings and nested splits, every one of the 2,300 scored responses, all 46 summary rows, and all 26 paired contrasts with bootstrap intervals. No discrepancies were found; the frozen production pipeline and recorded results are preserved. Temporary corruption fixtures were rejected without repairing inputs.
- Person 1's manuscript data/split/metrics and coverage text is updated. A ten-case review packet, editable review sheet, and `docs/MANUAL_TASKS.md` separate automated checks from pending human sign-off.

- Person 3 preliminary analysis is complete: the independent audit passes again and temporary production analysis exactly reproduces 46 condition rows and 26 contrasts. Exported six-row native table, 300 matched transitions, six transition summaries, inspected curve, report and handoff are in `results/local-nf4-v1/person3-analysis`.
- RQ1/RQ2 and the manuscript figure/table are updated. The 4B English four-to-sixteen comparison is −12 percentage points with interval [−24, −2], higher token cost and four missing-marker cases among seven lost correct answers. The pilot does not establish a capacity cliff or stronger Indic decline.
- Person 3 manual checks are added alongside Person 1. No human interpretation/numerical/semantic sign-off is claimed. No new inference or policy training occurred.

## Still required

- The preliminary milestone is complete. The full study remains at 2,300/11,500 responses: 2,300/4,600 development and 0/6,900 held-out. Person 2 stopped at the requested milestone.
- Complete the remaining development responses before fitting/evaluating the actual router and freezing it; synthetic router tests are software verification only.
- Complete human error review on genuine outputs.
- Complete Person 1's independent human numerical review, rendered-figure/caption checks, manuscript sign-off, and investigation of any disagreements using `docs/MANUAL_TASKS.md`. None of the ten review cases has been human-annotated yet.
- Complete Person 3's human table/figure/paired-diagnostic and RQ1/RQ2 interpretation review, including the final Overleaf layout; record reviewer/date/decision/notes in `docs/MANUAL_TASKS.md`.
- Enter real teammate names, complete pending manuscript fields, and verify the exact course cutoff.
- Human reviewers approve the final Overleaf PDF layout and course page-count rules. Automated compilation and visual inspection are now complete; see person4-report/OVERLEAF.md.

## Person 4 completed

- Preliminary manuscript, requirement checklist, 15 source-linked literature/claim records and evidenced metadata corrections complete. Full mCoT PDF access is flagged; human source reading remains pending.
- 40-case observable evidence and ten distinct-question double-review packets prepared; original annotations preserved and semantic fields blank.
- All 38 tests pass, 81 protected files and fingerprint unchanged.
- Signed-in Overleaf project created and compiled with main.tex/pdfLaTeX: zero errors/warnings, four main-text pages, six total. All exported pages visually inspected; PDF and evidence saved locally. Human sign-off and submission remain pending.

## Immediate next action

Persons 1, 3 and 4 complete their human checks in `docs/MANUAL_TASKS.md`. Person 4 obtains independent human reviews, replaces author details, confirms portal rules and arranges final submission. The ten numerical-review cases and 40 error-review cases are sampled artifacts, not completed human annotations.

The preliminary score comparisons come from genuine pilot outputs. No capacity cliff, causal model-size effect, native semantic quality, or router benefit is claimed from these data, input-token characterization or software tests.
