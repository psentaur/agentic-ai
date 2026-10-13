# Four-person execution checklist

Mid-sem deadline: **October 13, 2026**. Internal full-project target: **October 20, 2026**, subject to measured free-GPU capacity. All times and dates are Asia/Kolkata. The guidelines do not give the submission hour: Person 4 checks the course portal immediately.

Fill in names before distributing work:

| Owner | Name | Primary responsibility |
|---|---|---|
| Person 1 | __________ | Data, scoring, coverage, numerical audit |
| Person 2 | __________ | GPU environment, prompt execution, checkpoints |
| Person 3 | __________ | Curves, paired comparisons, router, ablation |
| Person 4 | __________ | Literature, error review, Overleaf integration |

## October 12: parallel work

### Person 1 — data and evaluation

- [x] Original dataset downloaded at a pinned revision; 750 language records prepared.
- [x] Numeric answers agree across translations; 100/150 ID split and nested smoke/pilot IDs saved.
- [x] Unicode numerical scorer and split/grid tests implemented.
- [x] Independently reconstruct original source checksums, all 750 records, and seed-42 nested splits; audit all 2,300 raw/scored responses and their provenance.
- [x] Run `score` and `status` on the local NF4 results: 981 correct, 278 parse failures, 50 complete paired IDs, zero held-out outputs.
- [x] Independently reconcile all 46 summary rows and 26 paired contrasts, including bootstrap intervals; preserve frozen inputs and pipeline fingerprint.
- [x] All 24 software tests pass; duplicate records, altered scores/tables, and malformed input are rejected in temporary audit fixtures. Reruns preserve human review annotations.
- [x] Update the manuscript's dataset, splits, metrics, and planned-versus-completed coverage text.
- [x] Prepare a ten-case numerical review packet and Person 1-only manual guide: `docs/MANUAL_TASKS.md`. Automated audit evidence is in `results/local-nf4-v1/person1-audit`.
- [x] Human reviewer reads scoring tests and independently solves all ten selected questions. Mukthish's numerical answers/name/date/decisions/notes are recorded for all ten cases on 2026-10-13; the user confirmed the remaining Person 1 checks on October 13.
- [x] Human reviewers check rendered plot points, intervals, labels, captions, and integrated tables against audited records; completion confirmed by the user on October 13, 2026. Other reviewer names and individual review dates were not supplied.
- [x] Human reviewers check the dataset/split/metric paragraphs and investigate numerical disagreements; completion confirmed by the user on October 13, 2026. See the Person 1 completion record in `docs/MANUAL_TASKS.md`; historical automated audit evidence remains unchanged.

### Person 2 — inference

- [x] Pinned model revisions, configuration, prompts, resumable runner, and notebook implemented.
- [x] Local alternative selected: RTX 4060 Laptop GPU with NF4 for both models; see `docs/LOCAL_RUN.md`.
- [x] GPU dependencies installed/frozen, CUDA tensor check passed, and both models completed 23-condition local feasibility; persistent `results/local-nf4-v1`.
- [x] Both models completed feasibility and the full 460-response, 10-ID smoke block.
- [x] Smoke and pilot runtime, longest outputs, memory, parsing, step compliance, and truncation exported.
- [x] Complete 50 paired development IDs across both models: 2,300 responses, 1,150 per model. Exact coverage and zero-new-response resume verified; see `results/local-nf4-v1/validation.json`.
- Fallback was unnecessary: both models completed locally without CPU/disk offload or out-of-memory errors.
- [x] Local hardware, precision, libraries, generation details, and checkpoint reuse documented in the manuscript; methodology diagram matches the implemented workflow.

### Person 3 — analysis and routing

- [x] Balanced-cohort plots, paired intervals, fixed baselines, grouped router validation, and freeze implemented.
- [x] Reproduce `analyze --phase pilot` in a temporary raw-results copy; confirm 50 matched IDs, 2,300 responses, 46 condition cells and 26 contrasts against the independent audit.
- [x] Export and inspect the main curve, all 46 diagnostic rows, a six-row native comparison table, and 300 paired transitions; integrate the figure/table into RQ1/RQ2 and provide Person 4 handoff artifacts in `results/local-nf4-v1/person3-analysis`.
- [x] Report the 4B English four-to-sixteen score decline with token cost, count compliance, no truncation, and four missing-marker cases among seven lost correct answers; flags are associations, not causes.
- [x] Write preliminary RQ1/RQ2 quantitative results with all 26 exploratory contrasts exported. Router training, freeze, ablation and held-out evaluation remain pending.
- [x] Automated audit and source/description consistency checks retain the declared scorer, shared-ID split, all-response denominator and fingerprint.
- [x] All 31 tests pass (24 existing plus seven Person 3 checks); exports reproduce deterministically without input mutation.
- [ ] Human reviewer checks Person 1's scorer/split/metrics, Person 3's figures/tables/paired diagnostics and numerical prose; records name/date/decision/notes in `docs/MANUAL_TASKS.md`.
- [ ] Check final rendered figures and tables in Overleaf and sign off interpretation; standalone inspection does not confirm final layout.

### Person 4 — research and report

- [x] Read supplied guidelines, tips, skeleton and formatting requirements; record requirements/evidence checklist.
- [x] Verify primary-source metadata/claims for 15 references and document corrections/access limits in paper/literature-verification.md. Human reading remains pending; mCoT full PDF timed out.
- [x] Refine Introduction/Related Work, separate methodology/setup, integrate genuine results and observable error findings; retain future router work.
- [x] Prepare 40-case observable packet and ten distinct-question double reviews, with blank semantic decisions and independent solutions; preserve original sheet.
- [x] Cross-check technical/numerical descriptions, run all 38 tests and verify protected-input preservation.
- [x] Create [Overleaf project](https://www.overleaf.com/project/6accbd9876b381cd22410e6d), compile with pdfLaTeX, repair errors/layout, and inspect all pages. Current final export: four main-text pages, seven total; PDF/log/source/proof saved in output/pdf/final-report.pdf and results/local-nf4-v1/final-report. Earlier six-page export preserved.
- [x] Resolve all manuscript placeholders except author names; use the user-supplied BITS Pilani affiliation and explicit future-work boundaries.
- [ ] Human reviewers complete semantic/numerical/literature/line-by-line/layout sign-off in docs/MANUAL_TASKS.md.
- [ ] Enter actual author names, invite teammates, confirm cutoff/anonymity/page/source rules through the course portal, and submit manually.

## October 13: submission gate

- [x] Local `status` shows 2,300 genuine completed responses: 50 matched IDs, both models, 20% of 11,500 planned responses. Held-out coverage is zero.
- [x] The manuscript text distinguishes completed preliminary coverage from planned full development and held-out experiments; Person 1's human checks are complete per the user's October 13 confirmation. Other roles' human checks remain pending.
- [x] At least one evidence-supported preliminary insight is described with N=50, exploratory intervals and formatting caveats; human interpretation sign-off remains pending.
- [x] Methodology, objectives, system diagram, setup and limitations are drafted; human approval pending.
- [x] Assisted citation metadata and claim checks recorded; no sample references remain. Human full-paper reading/sign-off remains pending.
- [ ] All four read the abstract and introduction; each reviews their own section and assigned partner's section.
- [x] Overleaf compile succeeds; four main-text pages and readable figures/tables checked in exported PDF. Human final layout approval pending.
- [ ] Person 4 submits before the actual course cutoff and saves a copy of the submitted PDF/source.

If coverage is below the requirement, state the exact count and unmet requirement. Dataset tokenization and software tests must not be counted as model-accuracy experiments.

## October 14–20: finish the study

| Date | Owner and deliverable |
|---|---|
| Oct 14–16 | Person 2 completes all 4,600 development responses; Person 1 audits coverage; Person 3 trains/validates router and creates the freeze. Person 4 refines related work and error review. |
| Oct 17–18 | Person 2 completes all 6,900 held-out responses; Person 3 evaluates cached router choices, ablation, and paired comparisons. |
| Oct 19 | Person 1 reproduces figures and checks claims; Person 4 integrates final evidence and limitations; all four review. |
| Oct 20 | Deliver final paper, source, code, configuration, data provenance, logged outputs, and reproduction commands. |

Keep a daily 15-minute check-in: completed artifact, next artifact, blocker, and owner. Free GPU limits can extend this schedule; update dates using measured throughput rather than reducing coverage silently.
