"""Refresh all three deliverables and verify current report and every archive member.

This packaging utility does not run inference, scoring, audits, or analysis and
never edits scientific inputs or prior evidence. Run from any working directory.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from study.common import context_hash, load_config, read_json


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    evidence = read_json(ROOT / "results/local-nf4-v1/final-report/verification.json")
    if context_hash(load_config(ROOT / "configs/local-nf4.json"),
                    read_json(ROOT / "data/manifest.json")) != evidence["fingerprint"]:
        raise ValueError("Scientific fingerprint changed")
    for name, digest in evidence["protected_sha256"].items():
        if sha256(ROOT / name) != digest:
            raise ValueError(f"Protected file changed: {name}")
    if sha256(ROOT / "output/pdf/final-report.pdf") != evidence["final_pdf_sha256"]:
        raise ValueError("PDF changed; renew compilation and layout evidence")
    if sha256(ROOT / "paper/main.tex") != evidence["current_main_tex_sha256"]:
        raise ValueError("Manuscript changed; recompile and renew evidence")
    tex = (ROOT / "paper/main.tex").read_text()
    if re.search(r"\\pending|TODO|TBD|FIXME|Replace with|Completion Checklist", tex, re.I):
        raise ValueError("Unresolved manuscript placeholder")
    for name, digest in evidence["source_files"].items():
        if sha256(ROOT / "paper" / name) != digest:
            raise ValueError(f"Overleaf source input changed: {name}")
    with zipfile.ZipFile(ROOT / "results/local-nf4-v1/final-report/overleaf-source.zip") as source:
        if source.testzip() is not None or set(source.namelist()) != set(evidence["source_files"]):
            raise ValueError("Invalid Overleaf source archive")
        for name in source.namelist():
            if source.read(name) != (ROOT / "paper" / name).read_bytes():
                raise ValueError(f"Overleaf/local byte disagreement: {name}")

    subprocess.run([sys.executable, str(ROOT / "scripts/package.py"), "--include-results"],
                   cwd=ROOT, check=True)
    results = ROOT / "results/local-nf4-v1"
    paths = [p for p in results.rglob("*") if p.is_file()
             and "__pycache__" not in p.parts and not p.name.endswith((".tmp", ".lock"))]
    extras = [*ROOT.glob("configs/*.json"), *ROOT.glob("docs/*.md"),
              *ROOT.glob("output/pdf/*.pdf"),
              *[p for p in (ROOT / "paper").rglob("*") if p.is_file()],
              ROOT / "TEAM_PLAN.md", ROOT / "STATUS.md", ROOT / "README.md",
              ROOT / "scripts/package_final_report.py"]
    archive_path = ROOT / "dist/local-preliminary-results.zip"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            archive.write(path, Path("local-nf4-v1") / path.relative_to(results))
        for path in sorted(set(extras)):
            archive.write(path, Path("extras") / path.relative_to(ROOT))

    verification = {"date": "2026-10-13", "fingerprint": evidence["fingerprint"],
                    "all_protected_files_unchanged": True, "archives": {}}
    for name in ["indic-study.zip", "overleaf-paper.zip", "local-preliminary-results.zip"]:
        path = ROOT / "dist" / name
        with zipfile.ZipFile(path) as archive:
            members = archive.namelist()
            if archive.testzip() is not None or len(members) != len(set(members)):
                raise ValueError(f"Archive integrity failure: {name}")
            for member in members:
                parts = Path(member).parts
                if any(p.startswith(".venv") or p == "__pycache__" for p in parts) or member.endswith(".safetensors"):
                    raise ValueError(f"Excluded environment/weight file: {member}")
                if name == "indic-study.zip":
                    current = ROOT / member.removeprefix("indic-study/")
                elif name == "overleaf-paper.zip":
                    current = ROOT / "paper" / member
                elif member.startswith("local-nf4-v1/"):
                    current = results / member.removeprefix("local-nf4-v1/")
                elif member.startswith("extras/"):
                    current = ROOT / member.removeprefix("extras/")
                else:
                    raise ValueError(f"Unrecognized archive member: {member}")
                if archive.read(member) != current.read_bytes():
                    raise ValueError(f"Byte disagreement: {name}: {member}")
            if name == "overleaf-paper.zip":
                if set(members) != set(evidence["source_files"]):
                    raise ValueError("Overleaf package inputs disagree with compiled source")
            else:
                required = (["indic-study/output/pdf/final-report.pdf",
                             "indic-study/results/local-nf4-v1/person1-audit/numerical_review.csv",
                             "indic-study/results/local-nf4-v1/person1-audit/numerical_review_original.csv",
                             "indic-study/docs/MANUAL_TASKS.md", "indic-study/STATUS.md"]
                            if name == "indic-study.zip" else
                            ["extras/output/pdf/final-report.pdf",
                             "local-nf4-v1/person1-audit/numerical_review.csv",
                             "local-nf4-v1/person1-audit/numerical_review_original.csv",
                             "extras/docs/MANUAL_TASKS.md", "extras/STATUS.md"])
                if not set(required).issubset(members):
                    raise ValueError(f"Missing final deliverables: {name}")
        verification["archives"][name] = {
            "files": len(members), "bytes": path.stat().st_size, "sha256": sha256(path),
            "zip_integrity": "passed", "all_members_byte_match_current_files": True}
    output = ROOT / "dist/final-report-package-verification.json"
    output.write_text(json.dumps(verification, indent=2) + "\n")
    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()
