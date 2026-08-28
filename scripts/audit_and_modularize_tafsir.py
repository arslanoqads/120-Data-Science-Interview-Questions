#!/usr/bin/env python3
"""
Audit Tafsir Ibn Kathir chapters:
- Remove Arabic / non-English OCR noise
- Strip isnad (narrator chains); keep story / hadith substance
- Deduplicate redundant narrations of the same story
- Organize into ~50-page modules (one surah per module unless small surahs bundle)
- Split into volumes (max 10 modules each, balanced)
"""

import re
import json
import math
import html
from pathlib import Path
from difflib import SequenceMatcher

BOUNDARIES_PATH = Path(__file__).parent / "surah_boundaries.json"
CHAPTERS_DIR = Path("/workspace/tafsir_summaries/chapters")
OUTPUT_DIR = Path("/workspace/tafsir_summaries/modular")
MODULES_DIR = OUTPUT_DIR / "modules"
VOLUMES_DIR = OUTPUT_DIR / "volumes"
AUDITED_DIR = Path("/workspace/tafsir_summaries/audited")

SOURCE_CITATION = "Tafsir Ibn Kathir (Abridged), Darussalam English Edition"
TARGET_MODULE_PAGES = 50
MAX_MODULES_PER_VOLUME = 10
# Calibrated from raw extraction (~667 words/page); cleaned text is denser
WORDS_PER_PAGE = 840

ARABIC_RE = re.compile(
    r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+"
)
FOOTNOTE_RE = re.compile(
    r"\*?\s*\[\d+\s*\*?\s*\]|\[\d+\s*\*?\s*\]|\*+\s*\d+|\^\s*At-|\^\s*\d+"
)
CITATION_LINE_RE = re.compile(
    r"^(?:\d+\s*)?(?:At-|Al-|Ibn |Ahmad|Muslim|Bukhari|Fath|Tuhfat|Abu Dawud|An-Nas)",
    re.I,
)
DUPLICATE_MARKER_RE = re.compile(
    r"(similar Hadith|also recorded (?:this|the same)|In addition,.*recorded|"
    r"recorded this Hadith|recorded similar wording|There is a similar)",
    re.I,
)
RECORDED_PREFIX_RE = re.compile(
    r"^(?:Also, |In addition, |Further, |Furthermore, )?"
    r"(?:Imam |The )?(?:(?:Two )?Sahihs?|Musnad|Sunan|Mustadrak).*?"
    r"(?:recorded|narrated|related|collected)\s+(?:that\s+)?",
    re.I | re.S,
)
SAID_CHAIN_RE = re.compile(
    r"^[A-Za-z''\-\s]+(?:bin|ibn|Abu|Umm|Al-)[A-Za-z''\-\s]*\s+said\s+that\s+",
    re.I,
)
PROPHET_PREFIX_RE = re.compile(
    r"^(?:the\s+)?(?:Messenger of Allah|Prophet)\s*(?:jg|jg§|0|§|\S+)?\s*(?:said|stated)?[,:\s]*",
    re.I,
)
JUNK_LINE_RE = re.compile(
    r"^[\d\s\.\,\;\:\|\*\'\"«»\^\<\>\{\}\[\]\\\/\-\+\=]+$"
)


def load_boundaries():
    with open(BOUNDARIES_PATH) as f:
        return {int(k): v for k, v in json.load(f).items()}


def estimate_pages(text: str) -> int:
    words = len(text.split())
    return max(1, math.ceil(words / WORDS_PER_PAGE))


def remove_arabic_and_noise(text: str) -> str:
    text = ARABIC_RE.sub("", text)
    text = FOOTNOTE_RE.sub("", text)
    text = re.sub(r"\[\d+\s*\*?\s*\]", "", text)
    text = re.sub(r"\s+\d{1,3}\s+(?:At-|Fath|Tuhfat|Ahmad|Muslim|Bukhari)", "", text, flags=re.I)
    text = re.sub(r"[«»]{1,2}", '"', text)
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    # OCR symbol runs
    text = re.sub(r"[<>]{1,2}[A-Za-z0-9]+", "", text)
    text = re.sub(r"\s*\d+Surah\s+\d+\s*\.", "", text, flags=re.I)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_mostly_english(text: str) -> bool:
    if len(text) < 20:
        return False
    letters = sum(1 for c in text if c.isalpha())
    if letters < 15:
        return False
    ascii_letters = sum(1 for c in text if c.isascii() and c.isalpha())
    return ascii_letters / max(letters, 1) > 0.92


def strip_isnad(text: str) -> str:
    """Remove narrator chains; preserve quoted speech and narrative."""
    text = text.strip()
    text = RECORDED_PREFIX_RE.sub("", text)
    # Peel repeated "X said that" chains (max 6)
    for _ in range(6):
        new = SAID_CHAIN_RE.sub("", text)
        new = PROPHET_PREFIX_RE.sub("", new)
        if new == text:
            break
        text = new
    # Remove trailing bibliographic clutter
    text = re.sub(
        r"\s*(?:Al-Bukhari|Muslim|Ahmad|At-Tirmidhi|An-Nas|Abu Dawud|Ibn Majah|"
        r"Al-Hakim|At-Tabari|Fath Al-Bari|Tuhfat).*?(?:recorded|also recorded).*$",
        "",
        text,
        flags=re.I,
    )
    text = re.sub(r"\s*\d+\s*Al-Bukhari.*$", "", text, flags=re.I)
    return text.strip()


def extract_quotes(text: str) -> list[str]:
    quotes = []
    for pat in [
        r'"([^"]{25,})"',
        r"«([^»]{25,})»",
    ]:
        quotes.extend(re.findall(pat, text))
    return [q for q in quotes if is_mostly_english(q) and is_likely_hadith_quote(q)]


def is_likely_hadith_quote(q: str) -> bool:
    return bool(
        re.match(
            r"^(The |All |Who |O |Our |I |Verily |There |When |If |None |Do |You |"
            r"Allah |Indeed |Say |He |She |They |What |How )",
            q.strip(),
            re.I,
        )
    )


def normalize_for_dedup(text: str) -> str:
    t = text.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(
        r"\b(?:recorded|narrated|said|hadith|messenger|prophet|also|imam|"
        r"authentic|sahih|hasan|muslim|bukhari|ahmad)\b",
        "",
        t,
    )
    t = re.sub(r"\s+", " ", t).strip()
    return t


def similarity(a: str, b: str) -> float:
    na, nb = normalize_for_dedup(a), normalize_for_dedup(b)
    if len(na) < 30 or len(nb) < 30:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def compress_hadith_block(text: str) -> str:
    """Remove isnad; keep narrative prose or clear quoted speech."""
    text = strip_isnad(text)
    quotes = extract_quotes(text)
    if quotes:
        best = max(quotes, key=len)
        best = remove_arabic_and_noise(best)
        if len(best) > 40:
            framing = re.split(r'["«]', text, maxsplit=1)[0].strip()
            framing = strip_isnad(framing)
            framing = remove_arabic_and_noise(framing)
            if framing and 20 < len(framing) < 100 and not framing.endswith(":"):
                return f"{framing}: \"{best}\""
            return best
    return text


def clean_paragraph(p: str) -> str:
    p = remove_arabic_and_noise(p)
    if not p or len(p) < 25:
        return ""
    if JUNK_LINE_RE.match(p):
        return ""
    if CITATION_LINE_RE.match(p) and len(p) < 150:
        return ""
    if not is_mostly_english(p):
        return ""

    # Hadith narrations: strip isnad chains
    if re.search(r"\b(?:recorded|narrated)\b", p, re.I) and re.search(
        r"\b(?:Messenger of Allah|Prophet)\b", p, re.I
    ):
        p = compress_hadith_block(p)
    elif re.search(r"\b(?:recorded|narrated)\b", p, re.I):
        p = strip_isnad(p)
    p = remove_arabic_and_noise(p)
    p = re.sub(r"\s+", " ", p).strip()
    if len(p) < 25:
        return ""
    return p


def dedupe_paragraphs(paragraphs: list[str], threshold: float = 0.82) -> list[str]:
    kept: list[str] = []
    kept_quotes: list[str] = []

    for p in paragraphs:
        if DUPLICATE_MARKER_RE.search(p) and kept:
            if similarity(p, kept[-1]) > 0.45:
                continue

        # Quote-level dedup for hadith
        quotes = extract_quotes(p)
        if quotes:
            qnorm = normalize_for_dedup(max(quotes, key=len))
            if qnorm and any(
                SequenceMatcher(None, qnorm, kq).ratio() > 0.88 for kq in kept_quotes
            ):
                continue

        if any(similarity(p, k) >= threshold for k in kept):
            continue

        kept.append(p)
        for q in quotes:
            kept_quotes.append(normalize_for_dedup(q))

    return kept


def parse_surah_markdown(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    meta = {"num": 0, "name": "", "pdf_start": 0, "pdf_end": 0}
    m = re.match(r"# Surah (\d+): (.+)", lines[0] if lines else "")
    if m:
        meta["num"] = int(m.group(1))
        meta["name"] = m.group(2).strip()
    for line in lines:
        if line.startswith("**PDF pages:**"):
            m_pages = re.search(r"(\d+)\s*[–-]\s*(\d+)", line)
            if m_pages:
                meta["pdf_start"] = int(m_pages.group(1))
                meta["pdf_end"] = int(m_pages.group(2))

    sections = []
    current_heading = "Opening"
    current_cite = ""
    current_paras: list[str] = []

    def flush():
        nonlocal current_paras
        if current_paras:
            cleaned = [clean_paragraph(p) for p in current_paras]
            cleaned = [p for p in cleaned if p]
            cleaned = dedupe_paragraphs(cleaned)
            if cleaned:
                sections.append(
                    {
                        "heading": current_heading,
                        "citation": current_cite,
                        "paragraphs": cleaned,
                    }
                )
        current_paras = []

    for line in lines:
        if line.startswith("## "):
            flush()
            current_heading = line[3:].strip()
            current_cite = ""
        elif line.startswith("*[") and line.endswith("]*"):
            current_cite = line.strip("*")
        elif line.strip() == "---":
            continue
        elif line.startswith("#") or line.startswith("**"):
            continue
        elif line.strip():
            current_paras.append(line.strip())

    flush()
    return {"meta": meta, "sections": sections}


def surah_to_markdown(surah: dict, part_label: str | None = None) -> str:
    meta = surah["meta"]
    title = f"Surah {meta['num']}: {meta['name']}"
    if part_label:
        title += f" ({part_label})"
    lines = [
        f"# {title}",
        "",
        f"**Source:** {SOURCE_CITATION}",
        f"**PDF pages:** {meta['pdf_start']}–{meta['pdf_end']}",
        "",
        "---",
        "",
    ]
    for sec in surah["sections"]:
        lines.append(f"## {sec['heading']}")
        lines.append("")
        if sec["citation"]:
            lines.append(f"*{sec['citation']}*")
            lines.append("")
        for p in sec["paragraphs"]:
            lines.append(p)
            lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def split_surah_into_chunks(surah: dict, target_pages: int) -> list[dict]:
    """Split a large surah into page-sized chunks (sections stay intact when possible)."""
    chunks: list[dict] = []
    current = {
        "meta": dict(surah["meta"]),
        "sections": [],
    }
    current_words = 0
    target_words = target_pages * WORDS_PER_PAGE

    for sec in surah["sections"]:
        sec_words = sum(len(p.split()) for p in sec["paragraphs"])
        if current_words + sec_words > target_words and current["sections"]:
            chunks.append(current)
            current = {"meta": dict(surah["meta"]), "sections": []}
            current_words = 0
        current["sections"].append(sec)
        current_words += sec_words

    if current["sections"]:
        chunks.append(current)
    return chunks


def assign_modules(surahs: list[dict]) -> list[dict]:
    """Build modules: bundle only complete small surahs; never mix partial surahs."""
    modules: list[dict] = []
    i = 0
    module_id = 1

    while i < len(surahs):
        surah = surahs[i]
        full_text = surah_to_markdown(surah)
        pages = estimate_pages(full_text)

        if pages <= TARGET_MODULE_PAGES:
            bundle = [surah]
            bundle_pages = pages
            j = i + 1
            while j < len(surahs):
                next_surah = surahs[j]
                next_pages = estimate_pages(surah_to_markdown(next_surah))
                if bundle_pages + next_pages <= TARGET_MODULE_PAGES:
                    bundle.append(next_surah)
                    bundle_pages += next_pages
                    j += 1
                else:
                    break
            modules.append(
                {
                    "id": module_id,
                    "surahs": bundle,
                    "est_pages": bundle_pages,
                }
            )
            module_id += 1
            i = j
        else:
            parts = split_surah_into_chunks(surah, TARGET_MODULE_PAGES)
            for idx, part in enumerate(parts, 1):
                part_pages = estimate_pages(surah_to_markdown(part))
                modules.append(
                    {
                        "id": module_id,
                        "surahs": [part],
                        "est_pages": part_pages,
                        "part": idx,
                        "total_parts": len(parts),
                    }
                )
                module_id += 1
            i += 1

    return modules


def merge_small_surah_tails(modules: list[dict], min_pages: int = 18) -> list[dict]:
    """Merge undersized final parts of a split surah into the previous part."""
    i = len(modules) - 1
    while i > 0:
        m = modules[i]
        if m.get("part") and m["est_pages"] < min_pages:
            prev = modules[i - 1]
            if (
                prev.get("part")
                and len(prev["surahs"]) == 1
                and len(m["surahs"]) == 1
                and prev["surahs"][0]["meta"]["num"] == m["surahs"][0]["meta"]["num"]
            ):
                prev["surahs"][0]["sections"].extend(m["surahs"][0]["sections"])
                prev["est_pages"] = estimate_pages(surah_to_markdown(prev["surahs"][0]))
                if m.get("total_parts"):
                    prev["total_parts"] = m["total_parts"]
                modules.pop(i)
        i -= 1
    return modules


def renumber_modules(modules: list[dict]) -> list[dict]:
    for i, m in enumerate(modules, 1):
        m["id"] = i
    return modules


def assign_volumes(modules: list[dict]) -> list[dict]:
    n = len(modules)
    vol_count = math.ceil(n / MAX_MODULES_PER_VOLUME)
    base = n // vol_count
    extra = n % vol_count
    sizes = [base + (1 if i < extra else 0) for i in range(vol_count)]

    volumes = []
    idx = 0
    for vnum, size in enumerate(sizes, 1):
        chunk = modules[idx:idx + size]
        volumes.append({"id": vnum, "modules": chunk})
        idx += size
    return volumes


def module_filename(module: dict) -> str:
    surahs = module["surahs"]
    mid = module["id"]
    if len(surahs) == 1:
        meta = surahs[0]["meta"]
        base = f"Module_{mid:02d}_Surah_{meta['num']:03d}_{meta['name'].replace(' ', '_').replace('-', '_')}"
        if module.get("part"):
            base += f"_Part{module['part']}"
        return base + ".md"
    names = "_".join(f"{s['meta']['num']:03d}" for s in surahs)
    return f"Module_{mid:02d}_Surahs_{names}.md"


def module_title(module: dict) -> str:
    surahs = module["surahs"]
    if len(surahs) == 1:
        meta = surahs[0]["meta"]
        title = f"Surah {meta['num']}: {meta['name']}"
        if module.get("part"):
            title += f" (Part {module['part']} of {module['total_parts']})"
        return title
    return ", ".join(f"Surah {s['meta']['num']}: {s['meta']['name']}" for s in surahs)


def build_html(title: str, body_sections: list[str], toc: str | None = None) -> str:
    toc_block = ""
    if toc:
        toc_block = f'<nav id="toc"><h1>Contents</h1>{toc}</nav>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>{html.escape(title)}</title>
<style>
  @page {{ size: A4; margin: 2cm 2.2cm 2.5cm 2.2cm;
    @bottom-center {{ content: counter(page); font-size: 9pt; color: #666; }}
  }}
  body {{ font-family: Georgia, "Times New Roman", serif; font-size: 11pt;
    line-height: 1.55; color: #1a1a1a; }}
  h1 {{ font-size: 20pt; color: #1a3a5c; border-bottom: 2px solid #1a3a5c;
    padding-bottom: 6px; page-break-before: always; }}
  h1:first-of-type {{ page-break-before: avoid; }}
  h2 {{ font-size: 13pt; margin-top: 16px; color: #2c5282; }}
  .meta {{ font-size: 10pt; color: #555; margin-bottom: 16px; }}
  .citation {{ font-size: 9pt; color: #777; font-style: italic; margin-bottom: 8px; }}
  p {{ margin: 0 0 10px 0; text-align: justify; }}
  #toc {{ page-break-after: always; }}
  #toc ol {{ columns: 2; column-gap: 24px; font-size: 10pt; line-height: 1.7; }}
  .title-page {{ text-align: center; page-break-after: always; padding-top: 100px; }}
  .title-page h1 {{ border: none; font-size: 26pt; }}
  .title-page p {{ text-align: center; color: #555; }}
</style>
</head>
<body>
<div class="title-page">
  <h1>{html.escape(title)}</h1>
  <p>{html.escape(SOURCE_CITATION)}</p>
  <p>Audited English narrative — redundant narrations removed</p>
</div>
{toc_block}
{"".join(body_sections)}
</body>
</html>"""


def surah_to_html(surah: dict, part_label: str | None = None) -> str:
    meta = surah["meta"]
    title = f"Surah {meta['num']}: {html.escape(meta['name'])}"
    if part_label:
        title += f" ({html.escape(part_label)})"
    parts = [f'<h1>{title}</h1>',
             f'<p class="meta">PDF pages {meta["pdf_start"]}–{meta["pdf_end"]}</p>']
    for sec in surah["sections"]:
        parts.append(f"<h2>{html.escape(sec['heading'])}</h2>")
        if sec["citation"]:
            parts.append(f'<p class="citation"><em>{html.escape(sec["citation"])}</em></p>')
        for p in sec["paragraphs"]:
            parts.append(f"<p>{html.escape(p)}</p>")
    return "\n".join(parts)


def module_to_html(module: dict) -> str:
    parts = []
    for surah in module["surahs"]:
        label = None
        if module.get("part"):
            label = f"Part {module['part']} of {module['total_parts']}"
        parts.append(surah_to_html(surah, label))
    return "\n".join(parts)


def write_pdf(html_content: str, path: Path):
    from weasyprint import HTML
    HTML(string=html_content).write_pdf(str(path))


def main():
    boundaries = load_boundaries()
    AUDITED_DIR.mkdir(parents=True, exist_ok=True)
    MODULES_DIR.mkdir(parents=True, exist_ok=True)
    VOLUMES_DIR.mkdir(parents=True, exist_ok=True)

    print("Auditing surahs...")
    surahs = []
    for num in sorted(boundaries.keys()):
        info = boundaries[num]
        fn = f"Surah_{num:03d}_{info['name'].replace(' ', '_').replace('-', '_')}.md"
        path = CHAPTERS_DIR / fn
        surah = parse_surah_markdown(path)
        surah["meta"]["num"] = num
        surah["meta"]["name"] = info["name"]
        surahs.append(surah)
        audited_path = AUDITED_DIR / fn
        audited_path.write_text(surah_to_markdown(surah), encoding="utf-8")
        words_before = len(path.read_text().split())
        words_after = len(surah_to_markdown(surah).split())
        print(
            f"  Surah {num:3d}: {info['name']:<18} "
            f"words {words_before:>6} -> {words_after:>6} "
            f"({100*words_after/max(words_before,1):.0f}% retained)"
        )

    print("Assigning modules...")
    modules = assign_modules(surahs)
    modules = merge_small_surah_tails(modules)
    modules = renumber_modules(modules)
    print(f"  {len(modules)} modules (target ~{TARGET_MODULE_PAGES} pages each)")

    # Remove stale module files from prior runs
  valid_names = {module_filename(m) for m in modules}
    for old in MODULES_DIR.glob("*.md"):
        if old.name not in valid_names:
            old.unlink()

    for module in modules:
        fn = module_filename(module)
        md_parts = []
        for surah in module["surahs"]:
            label = None
            if module.get("part"):
                label = f"Part {module['part']} of {module['total_parts']}"
            md_parts.append(surah_to_markdown(surah, label))
        (MODULES_DIR / fn).write_text("\n\n".join(md_parts), encoding="utf-8")
        module["filename"] = fn
        module["title"] = module_title(module)

    volumes = assign_volumes(modules)
    print(f"  {len(volumes)} volumes")

    # Volume PDFs (primary deliverable)
    print("Generating volume PDFs...")
    for vol in volumes:
        toc_items = [
            f"<li>{html.escape(m['title'])}</li>" for m in vol["modules"]
        ]
        toc = f"<ol>{''.join(toc_items)}</ol>"
        body = [module_to_html(m) for m in vol["modules"]]
        title = f"Tafsir Ibn Kathir — Modular Volume {vol['id']}"
        html_content = build_html(title, body, toc)
        pdf_path = VOLUMES_DIR / f"Volume_{vol['id']:02d}.pdf"
        write_pdf(html_content, pdf_path)
        vol["pdf"] = str(pdf_path)

    # Master index PDF
    print("Generating master catalog PDF...")
    master_toc = []
    for vol in volumes:
        master_toc.append(f"<li><strong>Volume {vol['id']}</strong><ol>")
        for m in vol["modules"]:
            master_toc.append(
                f"<li>Module {m['id']}: {html.escape(m['title'])} "
                f"(~{m['est_pages']} pp.)</li>"
            )
        master_toc.append("</ol></li>")
    master_html = build_html(
        "Tafsir Ibn Kathir — Modular Edition Catalog",
        [],
        f"<ol>{''.join(master_toc)}</ol>",
    )
    catalog_pdf = OUTPUT_DIR / "Tafsir_Modular_Catalog.pdf"
    write_pdf(master_html, catalog_pdf)

    metadata = {
        "source": SOURCE_CITATION,
        "target_module_pages": TARGET_MODULE_PAGES,
        "words_per_page_estimate": WORDS_PER_PAGE,
        "module_count": len(modules),
        "volume_count": len(volumes),
        "modules": [
            {
                "id": m["id"],
                "title": m["title"],
                "filename": m["filename"],
                "est_pages": m["est_pages"],
                "surahs": [s["meta"]["num"] for s in m["surahs"]],
                "part": m.get("part"),
            }
            for m in modules
        ],
        "volumes": [
            {
                "id": v["id"],
                "module_ids": [m["id"] for m in v["modules"]],
                "pdf": f"volumes/Volume_{v['id']:02d}.pdf",
            }
            for v in volumes
        ],
    }
    (OUTPUT_DIR / "metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    # INDEX markdown
    index_lines = [
        "# Tafsir Ibn Kathir — Modular Audited Edition",
        "",
        f"**Source:** {SOURCE_CITATION}",
        "",
        "Audited for redundant hadith narrations, isnad chains removed, "
        "Arabic/non-English text stripped. Organized into modules (~50 pages) "
        "and volumes (max 10 modules each).",
        "",
        f"- **Modules:** {len(modules)}",
        f"- **Volumes:** {len(volumes)}",
        f"- **Catalog PDF:** [Tafsir_Modular_Catalog.pdf](Tafsir_Modular_Catalog.pdf)",
        "",
        "## Volumes",
        "",
    ]
    for vol in volumes:
        index_lines.append(f"### Volume {vol['id']}")
        index_lines.append(
            f"- [Volume_{vol['id']:02d}.pdf](volumes/Volume_{vol['id']:02d}.pdf)"
        )
        for m in vol["modules"]:
            index_lines.append(
                f"  - Module {m['id']}: {m['title']} "
                f"([{m['filename']}](modules/{m['filename']}) · ~{m['est_pages']} pp.)"
            )
        index_lines.append("")
    (OUTPUT_DIR / "INDEX.md").write_text("\n".join(index_lines), encoding="utf-8")

    print("Done.")
    print(f"  Modules: {MODULES_DIR}")
    print(f"  Volumes: {VOLUMES_DIR}")


if __name__ == "__main__":
    main()
