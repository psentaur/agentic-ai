# Implementation status — October 13, 2026

## Current report delivery

The final preliminary report is `output/pdf/final-report.pdf`, with **four main-text pages and seven total**. BITS Pilani is the supplied affiliation; only four author names remain placeholders. The existing Overleaf project contains the same nine source inputs as the local package, verified byte for byte. pdfLaTeX / TeX Live 2026 compilation has zero errors, warnings, or overfull boxes; all seven pages passed visual inspection. See `results/local-nf4-v1/final-report/REPORT.md` and the current package verification in `dist/final-report-package-verification.json`. Historical Person 4 exports and evidence remain unchanged.

The paper is complete for the preliminary milestone. Router/ablation/held-out results are future work; no missing results or semantic categories were invented. Person 1 review completion is recorded below. Blank Person 3/4 review records and course submission tasks remain separate from report preparation.

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
- Person 1's manuscript data/split/metrics and coverage text is updated. All ten numerical cases have completed annotations by Mukthish dated 2026-10-13. The user confirmed on October 13 that all remaining Person 1 manual checks had been performed by all reviewers; those checks are recorded complete in `docs/MANUAL_TASKS.md`. Other reviewer names, individual review dates, and separate decisions were not supplied. Historical automated audit evidence remains unchanged and describes the earlier review state.

- Person 3 preliminary analysis is complete: the independent audit passes again and temporary production analysis exactly reproduces 46 condition rows and 26 contrasts. Exported six-row native table, 300 matched transitions, six transition summaries, inspected curve, report and handoff are in `results/local-nf4-v1/person3-analysis`.
- RQ1/RQ2 and the manuscript figure/table are updated. The 4B English four-to-sixteen comparison is −12 percentage points with interval [−24, −2], higher token cost and four missing-marker cases among seven lost correct answers. The pilot does not establish a capacity cliff or stronger Indic decline.
- Person 3 manual checks are added alongside Person 1's completed checks. Person 3's human interpretation/numerical/semantic sign-off remains pending. No new inference or policy training occurred.

## Still required

- The preliminary milestone is complete. The full study remains at 2,300/11,500 responses: 2,300/4,600 development and 0/6,900 held-out. Person 2 stopped at the requested milestone.
- Complete the remaining development responses before fitting/evaluating the actual router and freezing it; synthetic router tests are software verification only.
- Complete human error review on genuine outputs.
- Complete Person 3's human table/figure/paired-diagnostic and RQ1/RQ2 interpretation review, including the final Overleaf layout; record reviewer/date/decision/notes in `docs/MANUAL_TASKS.md`.
- Enter real teammate names; all other manuscript placeholders are resolved. Verify the exact course cutoff.
- Human reviewers approve the current final PDF and course inclusion rules. Automated compilation and visual inspection are complete; see final-report/REPORT.md. Earlier person4-report evidence documents the previous export.

## Person 4 completed

- Preliminary manuscript, requirement checklist, 15 source-linked literature/claim records and evidenced metadata corrections complete. Full mCoT PDF access is flagged; human source reading remains pending.
- 40-case observable evidence and ten distinct-question double-review packets prepared; original annotations preserved and semantic fields blank.
- All 38 tests pass, 81 protected files and fingerprint unchanged.
- Signed-in Overleaf project created and compiled with main.tex/pdfLaTeX: zero errors/warnings, four main-text pages, six total. All exported pages visually inspected; PDF and evidence saved locally. Human sign-off and submission remain pending.

## Immediate next action

Person 1's preliminary checks are complete: ten numerical cases are annotated, and other checks are recorded from the user's October 13 confirmation. The current report is compiled, checked, and packaged with BITS Pilani; enter author names before submission. Persons 3 and 4 retain their own review records in `docs/MANUAL_TASKS.md`. The 40-case semantic-review sample remains unannotated, and semantic categories are not claimed in the paper. Confirm portal rules and arrange final submission separately.

The preliminary score comparisons come from genuine pilot outputs. No capacity cliff, causal model-size effect, native semantic quality, or router benefit is claimed from these data, input-token characterization or software tests.
