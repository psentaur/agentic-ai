"""Create clean Colab/source and Overleaf archives without environments or weights."""
from pathlib import Path
import argparse
import zipfile
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-results", action="store_true")
    args = parser.parse_args()
    output_dir = ROOT / "dist"
    output_dir.mkdir(exist_ok=True)
    for extension in ["pdf", "png"]:
        figure = ROOT / f"data/characterization/input_token_ratios.{extension}"
        if figure.exists():
            (ROOT / "paper/figures").mkdir(parents=True, exist_ok=True)
            shutil.copy2(figure, ROOT / f"paper/figures/{figure.name}")
    included = ["study", "configs", "data", "docs", "tests", "scripts", "notebooks", "paper", "output"]
    if args.include_results:
        included.append("results")
    files = [ROOT / name for name in ["README.md", "TEAM_PLAN.md", "STATUS.md", "PROPOSAL.md", "guidelines-summary.md", "pyproject.toml", "uv.lock", ".gitignore"] if (ROOT / name).exists()]
    for directory in included:
        files += [path for path in (ROOT / directory).rglob("*") if path.is_file()
                  and "__pycache__" not in path.parts and not path.name.endswith((".pyc", ".tmp", ".lock"))]
    with zipfile.ZipFile(output_dir / "indic-study.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(set(files)):
            archive.write(path, Path("indic-study") / path.relative_to(ROOT))
    with zipfile.ZipFile(output_dir / "overleaf-paper.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((ROOT / "paper").rglob("*")):
            if path.is_file() and path.suffix in {".tex", ".sty", ".bst", ".bib", ".pdf", ".png"}:
                archive.write(path, path.relative_to(ROOT / "paper"))
    print(f"Created {output_dir / 'indic-study.zip'}")
    print(f"Created {output_dir / 'overleaf-paper.zip'}")


if __name__ == "__main__":
    main()
