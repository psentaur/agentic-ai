"""Fetch exact publisher BibTeX; use original-author metadata for ICLR/arXiv entries.

This records source URLs/checksums for the team to audit. Never substitutes metadata
from a different paper when a source fails. Run only when refreshing the bibliography.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import urllib.request
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]


def fetch(url):
    cache = Path('/tmp/indic-study-citation-cache') / datetime.now(timezone.utc).strftime('%Y-%m-%d')
    cache.mkdir(parents=True, exist_ok=True)
    path = cache / (hashlib.sha256(url.encode()).hexdigest() + '.txt')
    if path.exists():
        return path.read_text(encoding='utf-8')
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (academic citation verification)"})
    with urllib.request.urlopen(request, timeout=40) as response:
        text = response.read().decode("utf-8")
    path.write_text(text, encoding='utf-8')
    return text


def arxiv_metadata(identifier):
    source = f"https://arxiv.org/abs/{identifier}"
    page = fetch(source)
    def values(field):
        return [html.unescape(value) for value in re.findall(r'<meta name="citation_' + field + r'" content="([^"]*)"', page)]
    return values("title")[0], values("author"), values("date")[0][:4], source, page


def resolve(item):
    key, kind, identifier, expected_title = item
    if kind == "acl":
        source = f"https://aclanthology.org/{identifier}.bib"
        bib = fetch(source)
        sources = [source]
    elif kind == "neurips":
        source = identifier
        page = fetch(source)
        link = re.findall(r'href="([^"]*[Bb]ib[^"]*)"', page)[0]
        source = urljoin(source, link)
        bib = fetch(source)
        sources = [identifier, source]
    elif kind == "pmlr":
        source = identifier
        page = fetch(source)
        pres = re.findall(r"<(?:pre|code)\b[^>]*>(.*?)</(?:pre|code)>", page, re.S)
        texts = [html.unescape(re.sub(r"<[^>]+>", "", value)).strip() for value in pres]
        bib = next(value for value in texts if value.startswith("@InProceedings"))
        # An abstract is not necessary in a bibliographic entry; preserve all other metadata.
        bib = re.sub(r",\s*abstract\s*=\s*\{.*?\}\s*(?=\n?\})", "", bib, flags=re.S)
        sources = [source]
    elif kind == "qwen":
        source = "https://huggingface.co/Qwen/Qwen3-1.7B/raw/70d244cc86ccca08cf5af4e1e306ecf908b1ad5e/README.md"
        page = fetch(source)
        bib = re.search(r"@misc\{qwen3technicalreport,.*?\n\s*\}", page, re.S).group(0)
        bib = bib.replace("author={Qwen Team}", "author={{Qwen Team}}")
        sources = [source, "https://arxiv.org/abs/2505.09388"]
    else:
        title, authors, year, source, page = arxiv_metadata(identifier)
        if title.casefold() != expected_title.casefold():
            raise ValueError(f"Unexpected paper at {source}: {title}")
        fields = {"title": title, "author": " and ".join(authors)}
        if kind == "iclr2023":
            # Venue/year are checked against the conference's official downloads page.
            conference_source = "https://iclr.cc/Downloads/2023"
            conference_page = fetch(conference_source)
            plain = html.unescape(re.sub(r"<[^>]+>", " ", conference_page))
            if " ".join(title.casefold().split()) not in " ".join(plain.casefold().split()):
                raise ValueError(f"Title missing from official ICLR 2023 listing: {title}")
            forum = {"shi2023mgsm": "fR3wGCk-IXp", "wang2023selfconsistency": "1PL1NIMMrw",
                     "zhou2023leasttomost": "WZH7099tgfM"}[key]
            fields.update(booktitle="International Conference on Learning Representations", year="2023",
                          url=f"https://openreview.net/forum?id={forum}")
            bib_type = "inproceedings"
            sources = [source, conference_source, fields["url"]]
        else:
            fields.update(year=year, eprint=identifier, archivePrefix="arXiv", url=source,
                          doi=f"10.48550/arXiv.{identifier}")
            bib_type = "misc"
            sources = [source]
        bib = "@" + bib_type + "{" + key + ",\n" + ",\n".join(f"  {field} = {{{value}}}" for field, value in fields.items()) + "\n}"
    def canonical(value):
        value = re.sub(r"\\textquotesingle\s*", "'", value)
        return " ".join(re.sub(r"[{}]", "", value).replace("’", "'").casefold().split())
    if not bib.lstrip().startswith("@") or canonical(expected_title) not in canonical(bib):
        raise ValueError(f"Cannot validate fetched BibTeX for {key}")
    bib = re.sub(r"^(@\w+\s*\{)[^,]+,", rf"\g<1>{key},", bib.strip(), count=1)
    return key, bib, {"key": key, "source_urls": sources, "source_kind": kind,
                      "title": expected_title, "bibtex_sha256": hashlib.sha256(bib.encode()).hexdigest()}


ITEMS = [
    ("wei2022cot", "neurips", "https://papers.neurips.cc/paper_files/paper/2022/hash/9d5609613524ecf4f15af0f7b31abca4-Abstract-Conference.html", "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"),
    ("kojima2022zeroshot", "neurips", "https://proceedings.neurips.cc/paper/2022/hash/8bb0d291acd4acf06ef112099c16f326-Abstract-Conference.html", "Large Language Models are Zero-Shot Reasoners"),
    ("turpin2023faithfulness", "neurips", "https://proceedings.neurips.cc/paper_files/paper/2023/hash/ed3fea9033a80fea1376299fa7863f4a-Abstract-Conference.html", "Language Models Don’t Always Say What They Think: Unfaithful Explanations in Chain-of-Thought Prompting"),
    ("gao2023pal", "pmlr", "https://proceedings.mlr.press/v202/gao23f.html", "PAL: Program-aided Language Models"),
    ("hu2020xtreme", "pmlr", "https://proceedings.mlr.press/v119/hu20b.html", "XTREME: A Massively Multilingual Multi-task Benchmark for Evaluating Cross-lingual Generalisation"),
    ("han2025tale", "acl", "2025.findings-acl.1274", "Token-Budget-Aware LLM Reasoning"),
    ("mcot2024", "acl", "2024.acl-long.649", "mCoT: Multilingual Instruction Tuning for Reasoning Consistency in Language Models"),
    ("linguafranca2026", "acl", "2026.eacl-short.25", "The Reasoning Lingua Franca: A Double-Edged Sword for Multilingual AI"),
    ("lang2026", "acl", "2026.acl-long.2029", "LANG: Reinforcement Learning for Multilingual Reasoning with Language-Adaptive Hint Guidance"),
    ("press2023compositionality", "acl", "2023.findings-emnlp.378", "Measuring and Narrowing the Compositionality Gap in Language Models"),
    ("shi2023mgsm", "iclr2023", "2210.03057", "Language Models are Multilingual Chain-of-Thought Reasoners"),
    ("wang2023selfconsistency", "iclr2023", "2203.11171", "Self-Consistency Improves Chain of Thought Reasoning in Language Models"),
    ("zhou2023leasttomost", "iclr2023", "2205.10625", "Least-to-Most Prompting Enables Complex Reasoning in Large Language Models"),
    ("cobbe2021gsm8k", "arxiv", "2110.14168", "Training Verifiers to Solve Math Word Problems"),
    ("qwen2025", "qwen", "2505.09388", "Qwen3 Technical Report")
]


def main():
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(resolve, ITEMS))
    paper = ROOT / "paper"
    paper.mkdir(exist_ok=True)
    (paper / "references.bib").write_text("\n\n".join(bib for _, bib, _ in results) + "\n", encoding="utf-8")
    provenance = {"retrieved_at": datetime.now(timezone.utc).isoformat(), "entries": [record for _, _, record in results],
                  "preprints": 2, "reference_count": len(results),
                  "note": "ICLR authors/titles checked in original author uploads; venue/year checked in the official ICLR listing. Direct OpenReview access was challenged; team should inspect canonical pages before submission."}
    (paper / "citation-provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(results)} verified source entries; two preprints ({2 / len(results):.1%}).")


if __name__ == "__main__":
    main()
