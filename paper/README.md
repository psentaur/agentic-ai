# Preliminary ACL manuscript

[Overleaf project](https://www.overleaf.com/project/6accbd9876b381cd22410e6d) is created and compiled with main.tex, pdfLaTeX and TeX Live 2026. The saved output is output/pdf/preliminary-mgsm-study.pdf: four main-text pages and six total, with all pages visually inspected. Zero errors/warnings and four informational underfull-box messages are saved in results/local-nf4-v1/person4-report. Supplied ACL style files remain byte-identical.

The manuscript reports 2,300 genuine pilot responses on 50 matched development IDs, with human review and router/held-out evaluation pending. Author names/institution/contact remain explicit placeholders. See docs/MANUAL_TASKS.md before submission; no invitations or course submission occurred.

Literature verification is documented in literature-verification.md and claim-source-map.json. Fifteen cited references include two preprints (13.3%); source-access limitations and human reading requirements remain explicit. citation-provenance.json retains original retrieval evidence; the claim map records current edited entries.

Regenerate source archives with `python scripts/package.py --include-results`. Do not add the compiled report PDF inside paper/, since figure PDFs are the only PDF inputs needed by Overleaf. The standalone output is packaged separately.
