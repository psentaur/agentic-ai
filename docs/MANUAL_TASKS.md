# Manual tasks — executed roles

This document covers **Persons 1, 3, and 4**. Sections for other teammates will be added when their work is executed. Automated checks and manuscript updates do not count as independent human review.

## Person 1

**Completed for the preliminary pilot.** On October 13, 2026, the user confirmed that all remaining Person 1 checks had been performed by all reviewers. The ten numerical cases have individual records by Mukthish dated 2026-10-13. Other reviewers' names, individual review dates, and separate decisions were not supplied; the remaining rows record the user's confirmation rather than inventing those details. No language expertise or translation-fidelity certification is inferred.

The original automated audit report, machine-readable audit, verification record, and review packet are preserved as historical evidence. Their statements about pending review or blank fields describe the state when they were generated. This completion record and the annotated review CSV document the later human checks.

## Start here

- Read the [automated audit report](../results/local-nf4-v1/person1-audit/REPORT.md) and [machine-readable evidence](../results/local-nf4-v1/person1-audit/audit.json).
- Use the [ten-case review packet](../results/local-nf4-v1/person1-audit/HUMAN_REVIEW.md) to locate questions and full model responses.
- Read the completed decisions in [numerical_review.csv](../results/local-nf4-v1/person1-audit/numerical_review.csv): all ten cases include independent answers, agreement decisions, reviewer, date, decision, and calculation notes. The [original blank review copy](../results/local-nf4-v1/person1-audit/numerical_review_original.csv) is preserved. Keep experiment IDs and UTF-8 encoding when saving any later annotations.

The ten cases are selected to expose different scoring situations, with five per model. They are a diagnostic sample, not a random sample for estimating overall error rates. The existing 40-case error-analysis sheet belongs to a later role and does not substitute for these ten numerical checks.

## 1. Independently check all ten numerical cases

For each case:

1. Read the **English benchmark question first**, keeping the benchmark answer, recorded answer, and model response covered until you have solved it. Write your calculation and independently obtained answer in the review fields/notes.
2. Compare your answer with the benchmark gold answer. Record whether they agree. If the gold appears wrong or the question is ambiguous, explain the issue; do not silently alter the dataset.
3. Inspect the full original model response and the exact `FINAL_ANSWER:` line. Check whether there is exactly one standalone marker and whether its payload is a permitted finite decimal number.
4. Compare your expected parsing decision and numerical correctness with the automated decision. A readable number inside a numbered explanation, an expression, a fraction, units, or multiple markers can still fail the declared answer format. Do not substitute an intermediate number for the final answer.
5. Fill in your name, review date, agreement decisions, and notes. Record disagreements explicitly, including the experiment ID and the relevant original text.

The declared scorer accepts signed decimals, equivalent trailing zeros, Unicode decimal digits, and correctly grouped western/Indian comma notation. It rejects missing/duplicate markers, malformed grouping, units, fractions, expressions, exponents, and nonfinite/ambiguous values. Parse failures remain incorrect in the evaluation denominator. Truncation is recorded separately and does not automatically decide numerical correctness.

Review completion means **all ten** cases have a recorded independent answer and reviewer/date/decision, with a reason for every disagreement. Automated suggestions in the packet are evidence to inspect, not human annotations.

## 2. Read the scoring rules and tests

Read [the scoring implementation](../study/scoring.py) and the `ScoringTests` cases in [test_pipeline.py](../tests/test_pipeline.py). Check that the manuscript describes the same policy. Pay particular attention to Bengali/Telugu digits, decimal equality, comma grouping, marker position/count, and invalid payloads.

Record whether the policy is accurately described, even if you would personally prefer a different policy. These settings were fixed before inference. Any proposed change needs a separately documented evaluation; it must not silently replace the completed run's scores.

## 3. Check rendered plots and captions

Open the [pilot curve PNG](../results/local-nf4-v1/analysis/pilot/both-models/accuracy_curves.png) and its [PDF export](../results/local-nf4-v1/analysis/pilot/both-models/accuracy_curves.pdf). Compare each series with the [audited summary](../results/local-nf4-v1/analysis/pilot/both-models/summary.csv), and check the [paired contrasts](../results/local-nf4-v1/analysis/pilot/both-models/paired_contrasts.csv).

- Check both model names, all three question languages, native versus English-pivot labels, requested budgets, axis units, plotted points, and interval endpoints.
- Confirm that each condition has **50 matched IDs**, and that accuracy and intervals are displayed as percentages where appropriate.
- Read captions at their intended size. Ensure captions distinguish requested visible steps from internal reasoning and identify exploratory paired intervals without claiming adjusted statistical significance.
- Check the integrated manuscript figures/tables and their final labels and captions against the audited files. This final integration check is recorded complete from the user's October 13 confirmation.

Machine agreement among JSON/CSV files cannot establish that a rendered figure, its caption, or a later manuscript copy is correct.

## 4. Review Person 1's manuscript text and counts

Read the Data and models, evaluation-grid table, and Metrics sections in [main.tex](../paper/main.tex). Verify these distinctions:

| Claim | Expected value |
|---|---:|
| Dataset | 250 shared IDs; 750 records across EN/BN/TE |
| Fixed split | 100 development / 150 held-out IDs, seed 42 |
| Nested preliminary subsets | 10 smoke / 50 pilot development IDs |
| Completed pilot | 2,300 responses; 1,150 per model; 46 model/condition cells × 50 IDs |
| Full development coverage | 2,300 / 4,600 responses |
| Held-out evaluation coverage | 0 / 6,900 responses |
| Full study coverage | 2,300 / 11,500 responses = 20% |

Smoke and feasibility records are reused within the pilot, not additional responses. Input-token characterization and temporary synthetic tests are not model-accuracy responses. Parsing failures and truncated completed responses remain visible in evaluation; download/infrastructure errors are separate.

Checking source rows and equal numerical gold answers does not prove translation fidelity. Review native-language meaning only if you have appropriate expertise; otherwise record that semantic alignment/fluency was not assessed. English-question numerical review and observable formatting checks can still be completed.

## Person 1 sign-off

The numerical-review row is supported by the saved case-level annotations. The remaining checks are recorded complete from the user's October 13, 2026 confirmation in this conversation; the confirmation date is not an inferred date of each review.

| Manual check | Status | Reviewer | Review date / confirmation date | Evidence / unresolved issue |
|---|---|---|---|---|
| Ten independent numerical cases | Complete | Mukthish | Reviewed 2026-10-13 | Ten saved independent answers; gold/score agreements and accept decisions recorded in numerical_review.csv. |
| Scoring policy and tests read | Complete (user-confirmed) | Unnamed reviewers | Confirmed 2026-10-13 | User confirmed all remaining Person 1 checks were performed. |
| Existing pilot plots checked against tables | Complete (user-confirmed) | Unnamed reviewers | Confirmed 2026-10-13 | User confirmation; individual reviewer details not supplied. |
| Dataset, split, metrics, and count text checked | Complete (user-confirmed) | Unnamed reviewers | Confirmed 2026-10-13 | User confirmation; individual reviewer details not supplied. |
| Final integrated figures/tables checked | Complete (user-confirmed) | Unnamed reviewers | Confirmed 2026-10-13 | User confirmation; individual reviewer details not supplied. |
| Any numerical disagreement investigated | Complete (user-confirmed) | Unnamed reviewers | Confirmed 2026-10-13 | All ten saved cases record gold/score agreement; remaining checks confirmed by the user. |

### Calculation-note housekeeping

The previously reported case 7 typo was already corrected in the saved review before this completion record: the note now reads `60 + 180 + 126 = 366`. The answer remains 366. The annotated CSV and its original blank copy are preserved without further edits during this recording update.

For any disagreement, save the experiment ID, independent arithmetic, benchmark gold, raw marker text, expected decision, and reviewer rationale. Report it separately; retain original inputs and outputs. Agreement with the automated audit is useful, but a disagreement must remain visible until resolved.


## Person 3 — review the preliminary quantitative analysis

Automated Person 3 analysis is complete. All checks below require a human reviewer and remain pending. Read the [analysis report](../results/local-nf4-v1/person3-analysis/REPORT.md), [provenance and validation](../results/local-nf4-v1/person3-analysis/analysis.json), and [handoff](../results/local-nf4-v1/person3-analysis/HANDOFF.md).

### 1. Check figures and tables

Compare the [curve PNG](../results/local-nf4-v1/person3-analysis/accuracy_curves.png) and PDF with the [full 46-condition table](../results/local-nf4-v1/person3-analysis/condition_table.csv). Check checkpoint/question-language labels, native versus pivot legends, requested budgets, percentage axes, all points and interval endpoints. Each condition has 50 matched IDs.

Check the [six-row native table](../results/local-nf4-v1/person3-analysis/compact_native_table.csv) and manuscript copy: arrows mean four-step then sixteen-step values, accuracy/parse/count/truncation are percentages, and tokens/steps are means. CSV rates and intervals are fractions. Check captions and readability again in the current final Overleaf PDF; source and standalone curve inspection do not verify final page layout. Automated compilation and visual inspection are complete: four main-text pages and seven total. Human layout approval remains separate.

### 2. Check paired diagnostic interpretation

Use [paired transitions](../results/local-nf4-v1/person3-analysis/paired_transitions.csv), [six transition summaries](../results/local-nf4-v1/person3-analysis/transition_summary.csv), and [all 26 contrasts](../results/local-nf4-v1/person3-analysis/paired_contrasts.csv). Locate exact experiment IDs for the seven 4B English correct-to-incorrect pairs; inspect missing markers in the four flagged sixteen-step outputs.

Confirm that the primary result uses all 50 IDs: 43 correct at four steps, 37 at sixteen, −12 percentage points with exploratory interval [−24, −2]. Check the token increase (118.88 to 318.56), 49/50 numbered-count matches at both budgets, no truncation, and parsing increase from 1/50 to 5/50. Diagnostic flags overlap and must not be summed as separate causes. The both-parseable subset has 45 pairs and a net loss of two correct answers; it is selected supplementary evidence, not replacement accuracy.

Check all six native comparisons, not just the lead example. Review the pivot examples against all 26 exported comparisons and keep exploratory, unadjusted interval wording. Do not claim a demonstrated capacity cliff, a causal parameter-count effect, hidden reasoning length, or a semantic explanation from these diagnostics. Translation fidelity and native-language meaning require suitable expertise; otherwise record that they were not assessed.

### 3. Review scorer, split and manuscript claims

Read Person 1's dataset/split/metric paragraphs and [scorer](../study/scoring.py) alongside the declared [protocol](PROTOCOL.md). Confirm the 100/150 shared-ID split, nested 50-ID pilot, and all-response denominator. Missing/duplicate/invalid markers are incorrect; truncation alone does not force incorrectness. Last-line placement is a prompt requirement: the scorer accepts a unique anchored numeric marker regardless of its position.

Review RQ1/RQ2 in [main.tex](../paper/main.tex), including every numerical claim, direction of differences, interval endpoints and interpretation caveat. The four Indic-minus-English effect intervals include zero. Numbered-line compliance is observable count compliance, not semantic compliance. Router training/ablation/test results remain pending; synthetic tests and preliminary summaries do not complete them.

### Person 3 sign-off

Record reviewer name, date, decision and notes after each check. For disagreements, include the table row, contrast or experiment ID and exact manuscript claim; retain the original responses and report the issue separately.

| Manual check | Status | Reviewer | Date | Decision | Notes / evidence |
|---|---|---|---|---|---|
| Standalone curve points, intervals and labels | Pending | | | | |
| Six-row and full condition tables, units and rounding | Pending | | | | |
| Paired transitions and overlapping flags | Pending | | | | |
| Scorer, split and denominator descriptions | Pending | | | | |
| RQ1/RQ2 numerical claims and interpretation | Pending | | | | |
| Final Overleaf figure/table/caption layout | Pending human review; compilation complete | | | | |
| Disagreements investigated and interpretation signed off | Pending review | | | | |


## Person 4 — report and submission review

Automated report preparation is complete; human sign-off remains pending. Use [requirements](../results/local-nf4-v1/person4-report/requirements.md), [literature notes](../paper/literature-verification.md), and [observable evidence](../results/local-nf4-v1/person4-review/README.md).

1. Two reviewers independently solve all ten English questions in [DOUBLE_REVIEW.md](../results/local-nf4-v1/person4-review/DOUBLE_REVIEW.md), before reading gold/parsed answers and raw explanations. Record solutions, answers, exact evidence quotes, categories, names, dates, decisions and notes in [double_review.csv](../results/local-nf4-v1/person4-review/double_review.csv). Resolve disagreements separately after independent reviews. Review all 40 cases with single_review.csv as expertise permits. Leave unassessed native-language meaning explicit; numeric-only outputs do not support semantic explanation judgments.
2. Manually read the cited original papers and verify every claim/author/title/venue/year against the source map. mCoT full PDF could not be fetched and requires reading manually. Confirm ICLR published-version metadata using canonical records where accessible. Assisted verification is not your literature sign-off.
3. Read every manuscript sentence and check numerical claims against audited tables. Check figures, table units, captions, diagram, citations, limitations and AI-use statement in the final Overleaf PDF. Confirm requested language versus scripts, all-response denominators, exploratory intervals, and absence of causal capacity claims. Record final page-layout approval even after automated visual inspection.
4. Replace the four author-name placeholders. The supplied affiliation BITS Pilani is already entered; email is optional and no address was invented. Confirm anonymity, whether limitations/AI statements/appendices/references count toward the course page limit, exact October 13 cutoff and timezone, filename and source/PDF requirements through the course portal. No portal URL or access is supplied yet.
5. Invite teammates in Overleaf manually after confirming names/emails and intended access. Obtain all authors’ sign-off, perform final recompile/download, and submit through the course portal. Creation and compilation do not mean submission.

| Check | Status | Reviewer | Date | Decision | Notes / evidence |
|---|---|---|---|---|---|
| Ten independent double reviews and resolution | Pending | | | | |
| Forty-case review / language expertise limits | Pending | | | | |
| Original literature and inaccessible full source | Pending | | | | |
| Numerical prose, figures/tables/captions | Pending | | | | |
| Line-by-line manuscript and AI-use statement | Pending | | | | |
| Final PDF layout and page-limit rules | Pending human approval | | | | |
| Author names and course portal rules | Pending; BITS Pilani affiliation entered | | | | |
| Teammate invitations and all-author sign-off | Pending | | | | |
| Final compile/download and course submission | Compile/download complete; submission pending | | | | Current final export has four main-text pages, seven total; see final-report/REPORT.md. |
