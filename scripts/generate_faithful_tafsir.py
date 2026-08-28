#!/usr/bin/env python3
"""
Extract Tafsir Ibn Kathir text faithfully from PDF with page citations.
No summarization or invented content — only cleaned source text.
Compiles all surahs into a single PDF with table of contents.
"""

import re
import json
import html
from pathlib import Path
from pypdf import PdfReader

PDF_PATH = "/tmp/tafsir_full.pdf"
BOUNDARIES_PATH = Path(__file__).parent / "surah_boundaries.json"
OUTPUT_DIR = Path("/workspace/tafsir_summaries")
COMBINED_HTML = Path("/workspace/tafsir_summaries/Tafsir_Ibn_Kathir_Complete.html")
COMBINED_PDF = Path("/workspace/tafsir_summaries/Tafsir_Ibn_Kathir_Complete.pdf")

SOURCE_CITATION = "Tafsir Ibn Kathir (Abridged), Darussalam English Edition"

# Heading patterns observed in the PDF (section titles in Ibn Kathir)
HEADING_PATTERNS = [
    re.compile(r'^The Tafsir of\b', re.I),
    re.compile(r'^Tafsir of\b', re.I),
    re.compile(r'^The Tafsirof\b', re.I),
    re.compile(r'^The Meaning of\b', re.I),
    re.compile(r'^The Virtues? of\b', re.I),
    re.compile(r'^The Reason\b', re.I),
    re.compile(r'^The Story of\b', re.I),
    re.compile(r'^The (?:Battle|Day|Incident|Command|Prohibition|Warning|Promise|Mercy|Significance|Merit|Description|Explanation|Beginning|End|Introduction) of\b', re.I),
    re.compile(r'^Why (?:there is|Allah|the|it|this|was)\b', re.I),
    re.compile(r'^Encouragement to\b', re.I),
    re.compile(r'^Warning (?:against|about|to|concerning)\b', re.I),
    re.compile(r'^Regarding\b', re.I),
    re.compile(r'^Concerning Allah\'s\b', re.I),
    re.compile(r'^How (?:many|Allah|the)\b', re.I),
    re.compile(r'^What (?:is|does|are|Allah)\b', re.I),
    re.compile(r'^Surat(?:e)? .+ (?:was|is) revealed\b', re.I),
    re.compile(r'^Surah .+ (?:was|is) revealed\b', re.I),
    re.compile(r'^Which was revealed\b', re.I),
    re.compile(r'^The (?:Attributes|Qualities|Rights|Rulings|Tafsir) of\b', re.I),
    re.compile(r'^Reason (?:behind|for)\b', re.I),
    re.compile(r'^In the Name of Allah\b', re.I),
    re.compile(r'^The Tafsir of (?:Ayah|Verse)\b', re.I),
    re.compile(r'^Ayah \d+', re.I),
    re.compile(r'^Verse \d+', re.I),
    re.compile(r'^The Prophet (?:said|jg said)\b', re.I),
]

# Lines to skip (headers, footers, junk)
SKIP_PATTERNS = [
    re.compile(r'^TAFSIR\s+IBN\s+KATHIR', re.I),
    re.compile(r'^IBN\s+KATHIR', re.I),
    re.compile(r'^DARUSSALAM', re.I),
    re.compile(r'^ABRIDGED', re.I),
    re.compile(r'^VOLUME\s+\d+', re.I),
    re.compile(r'^Contents$', re.I),
    re.compile(r'^Publishers?\s+Note', re.I),
    re.compile(r'^In theName ofAllah', re.I),
    re.compile(r'^In the Name ofAllah$', re.I),
    re.compile(r'^\d{1,4}$'),  # isolated page numbers
    re.compile(r'^Part-\d+', re.I),
    re.compile(r'^Surah \d+[\.\s]', re.I),  # page headers
    re.compile(r'^Suralt \d+', re.I),
    re.compile(r'^Siirah \d+', re.I),
    re.compile(r'^\d+\s*Tafsir Ibn', re.I),
    re.compile(r'^Tafsir Ibn Kathir$', re.I),
    re.compile(r'^Tafsir Ibn Kat', re.I),
    re.compile(r'^Tafstr Ibn', re.I),
    re.compile(r'^Tafslr Ibn', re.I),
    re.compile(r'^Tafcir Ibn', re.I),
    re.compile(r'^Tafsir lbn', re.I),
    re.compile(r'^\s*\.?\s*$'),
    re.compile(r'^---+$'),
    re.compile(r'^All rights reserved', re.I),
    re.compile(r'^GLOBAL LEADER', re.I),
]


def load_boundaries():
    with open(BOUNDARIES_PATH) as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}


def is_skip_line(line):
    s = line.strip()
    if len(s) < 2:
        return True
    if re.match(r'^[\d\s\.\,\;\:\|\*\'\"]+$', s):
        return True
    for pat in SKIP_PATTERNS:
        if pat.search(s):
            return True
    return False


def is_heading(line):
    s = line.strip()
    if len(s) < 10 or len(s) > 180:
        return False
    # Must match explicit section-title patterns only (avoid mid-sentence splits)
    for pat in HEADING_PATTERNS:
        if pat.match(s):
            # Reject if line looks like mid-paragraph content
            if s.endswith(',') and not pat.pattern.startswith('^The '):
                continue
            if re.search(r'\b(said|says|stated|recorded|narrated)\b.*\b(said|that)\b', s, re.I):
                continue
            return True
    return False


def clean_line(line):
    """Minimal cleanup — preserve original wording."""
    s = line.strip()
    # Remove isolated footnote markers at end
    s = re.sub(r'\s*\[\d+\s*\*?\s*\]\s*$', '', s)
    s = re.sub(r'\s*\*+\s*$', '', s)
    # Normalize whitespace
    s = re.sub(r'\s+', ' ', s)
    return s


def extract_pages(reader, start, end):
    """Extract text per page with page numbers."""
    pages = []
    for i in range(start - 1, min(end, len(reader.pages))):
        raw = reader.pages[i].extract_text() or ""
        pages.append({"page": i + 1, "raw": raw})
    return pages


def parse_pages_to_sections(pages):
    """Parse pages into sections with headings and paragraphs, preserving order."""
    sections = []
    current_heading = "Opening"
    current_paragraphs = []
    current_start_page = pages[0]["page"] if pages else 0
    current_page = current_start_page

    def flush_section():
        nonlocal current_paragraphs, current_heading, current_start_page
        if current_paragraphs:
            text = "\n\n".join(current_paragraphs)
            if len(text.strip()) > 30:
                sections.append({
                    "heading": current_heading,
                    "text": text.strip(),
                    "start_page": current_start_page,
                    "end_page": current_page,
                })
        current_paragraphs = []

    para_lines = []

    def flush_paragraph():
        nonlocal para_lines
        if para_lines:
            joined = " ".join(para_lines)
            if len(joined) > 15:
                current_paragraphs.append(joined)
        para_lines = []

    for page_data in pages:
        current_page = page_data["page"]
        lines = page_data["raw"].split("\n")
        for line in lines:
            cleaned = clean_line(line)
            if is_skip_line(cleaned):
                continue
            ascii_ratio = sum(1 for c in cleaned if c.isascii()) / max(len(cleaned), 1)
            if ascii_ratio < 0.45 and len(cleaned) < 100:
                continue

            if is_heading(cleaned):
                flush_paragraph()
                flush_section()
                current_heading = cleaned
                current_start_page = current_page
            else:
                para_lines.append(cleaned)

        # End of page — flush paragraph to preserve flow across pages
        flush_paragraph()
    flush_section()
    sections = merge_fragment_sections(sections)
    for sec in sections:
        sec["text"] = trim_index_tail(remove_footnote_paragraphs(sec["text"]))
    return [s for s in sections if len(s["text"].strip()) > 30]


def trim_index_tail(text):
    """Remove PDF back-matter (index, publisher notes) after tafsir ends."""
    markers = [
        r'This is the end of the Tafsir',
        r'INDEX OF SELECTED TOPICS',
        r'INDEXOFSELECTED TOPICS',
    ]
    for marker in markers:
        m = re.search(marker, text, re.I)
        if m:
            end = m.start()
            if re.search(r'end of the Tafsir', marker, re.I):
                tail = text[m.start():]
                close = re.search(r'all that exists\.', tail, re.I)
                if close:
                    end = m.start() + close.end()
            text = text[:end].strip()
    return text


def format_citation(start_page, end_page):
    if start_page == end_page:
        return f"[{SOURCE_CITATION}, PDF p. {start_page}]"
    return f"[{SOURCE_CITATION}, PDF pp. {start_page}–{end_page}]"


def merge_fragment_sections(sections):
    """Merge sections with broken/fragment headings into adjacent sections."""
    if not sections:
        return sections
    merged = []
    for sec in sections:
        h = sec["heading"]
        is_fragment = (
            len(h) < 25
            or h.endswith((' of', ' of Al-', ' the', ' Al-', ' Ar-', ' to', ' in', ' Al'))
            or re.match(r'^The Meaning of Al-?$', h, re.I)
            or re.match(r'^Messenger of Allah', h, re.I)
            or re.match(r'^the Prophet', h, re.I)
            or not re.search(r'[a-z]', h)  # all caps fragments
        )
        if is_fragment and merged:
            prev = merged[-1]
            prev["text"] = prev["text"] + "\n\n" + h + " " + sec["text"]
            prev["end_page"] = sec["end_page"]
        elif is_fragment:
            sec = dict(sec)
            sec["heading"] = "Opening"
            sec["text"] = h + " " + sec["text"]
            merged.append(sec)
        elif is_index_section(sec):
            continue
        else:
            merged.append(sec)
    return merged


def is_index_section(sec):
    """Detect PDF index/back-matter sections mis-parsed as tafsir."""
    h = sec["heading"]
    t = sec["text"]
    if re.search(r'\d+:\s*\d+', h):
        return True
    if re.search(r'INDEX OF SELECTED TOPICS', t, re.I):
        return True
    if len(t) < 200 and re.findall(r'\d+:\s*\d+', t) and len(re.findall(r'\d+:\s*\d+', t)) >= 2:
        return True
    return False


def remove_footnote_paragraphs(text):
    """Remove trailing footnote-only lines from text blocks."""
    paragraphs = text.split("\n\n")
    cleaned = []
    for p in paragraphs:
        # Skip pure footnote lines
        if re.match(r'^[\d\s\.\,\*]+$', p.strip()):
            continue
        if re.match(r'^(?:At-|Al-|Ibn |Ahmad|Muslim|Bukhari|Fath|Tuhfat)', p.strip()) and len(p) < 120:
            continue
        cleaned.append(p)
    return "\n\n".join(cleaned)


def generate_surah_markdown(num, info, sections):
    name = info["name"]
    start = info["start"]
    end = info["end"]
    volumes = info["volumes"]
    vol_str = ", ".join(str(v) for v in volumes)

    lines = [
        f"# Surah {num}: {name}",
        "",
        f"**Source:** {SOURCE_CITATION}",
        f"**Volume(s):** {vol_str}",
        f"**PDF pages:** {start}–{end}",
        "",
        "---",
        "",
    ]

    for sec in sections:
        heading = sec["heading"]
        cite = format_citation(sec["start_page"], sec["end_page"])
        lines.append(f"## {heading}")
        lines.append("")
        lines.append(f"*{cite}*")
        lines.append("")
        # Split into paragraphs for readability
        for para in sec["text"].split("\n\n"):
            p = para.strip()
            if p:
                lines.append(p)
                lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def generate_surah_html(num, info, sections):
    name = info["name"]
    start = info["start"]
    end = info["end"]
    volumes = info["volumes"]
    vol_str = ", ".join(str(v) for v in volumes)
    anchor = f"surah-{num}"

    parts = [
        f'<section class="surah" id="{anchor}">',
        f'<h1 class="surah-title">Surah {num}: {html.escape(name)}</h1>',
        f'<p class="meta"><strong>Source:</strong> {html.escape(SOURCE_CITATION)}<br>',
        f'<strong>Volume(s):</strong> {vol_str}<br>',
        f'<strong>PDF pages:</strong> {start}–{end}</p>',
    ]

    for sec in sections:
        cite = format_citation(sec["start_page"], sec["end_page"])
        parts.append(f'<h2>{html.escape(sec["heading"])}</h2>')
        parts.append(f'<p class="citation"><em>{html.escape(cite)}</em></p>')
        for para in sec["text"].split("\n\n"):
            p = para.strip()
            if p:
                parts.append(f'<p>{html.escape(p)}</p>')

    parts.append('</section>')
    return "\n".join(parts)


def build_combined_html(boundaries, all_sections):
    toc_items = []
    body_parts = []

    for num in sorted(boundaries.keys()):
        info = boundaries[num]
        anchor = f"surah-{num}"
        toc_items.append(
            f'<li><a href="#{anchor}">Surah {num}: {html.escape(info["name"])}</a> '
            f'<span class="toc-pages">(pp. {info["start"]}–{info["end"]})</span></li>'
        )
        body_parts.append(generate_surah_html(num, info, all_sections[num]))

    toc_html = "\n".join(toc_items)
    body_html = "\n".join(body_parts)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Tafsir Ibn Kathir — Complete Abridged English Edition</title>
<style>
  @page {{
    size: A4;
    margin: 2cm 2.2cm 2.5cm 2.2cm;
    @bottom-center {{
      content: counter(page);
      font-size: 9pt;
      color: #666;
    }}
  }}
  body {{
    font-family: Georgia, "Times New Roman", serif;
    font-size: 11pt;
    line-height: 1.55;
    color: #1a1a1a;
    max-width: 100%;
  }}
  h1 {{ font-size: 22pt; margin-top: 0; color: #1a3a5c; border-bottom: 2px solid #1a3a5c; padding-bottom: 6px; }}
  h2 {{ font-size: 13pt; margin-top: 18px; color: #2c5282; }}
  .surah-title {{ page-break-before: always; }}
  .surah:first-of-type .surah-title {{ page-break-before: avoid; }}
  .meta {{ font-size: 10pt; color: #555; margin-bottom: 20px; }}
  .citation {{ font-size: 9pt; color: #777; margin-bottom: 8px; font-style: italic; }}
  p {{ margin: 0 0 10px 0; text-align: justify; }}
  #toc {{ page-break-after: always; }}
  #toc h1 {{ font-size: 26pt; text-align: center; margin-bottom: 30px; }}
  #toc ol {{ columns: 2; column-gap: 30px; font-size: 10pt; line-height: 1.8; }}
  #toc li {{ margin-bottom: 4px; break-inside: avoid; }}
  .toc-pages {{ color: #888; font-size: 9pt; }}
  .title-page {{ text-align: center; page-break-after: always; padding-top: 120px; }}
  .title-page h1 {{ font-size: 28pt; border: none; }}
  .title-page p {{ text-align: center; font-size: 12pt; color: #555; }}
  hr {{ border: none; border-top: 1px solid #ddd; margin: 20px 0; }}
</style>
</head>
<body>

<div class="title-page">
  <h1>Tafsir Ibn Kathir</h1>
  <p>Abridged English Edition (Darussalam)</p>
  <p>Faithful text extraction with PDF page citations</p>
  <p>114 Surahs — 10 Volumes</p>
</div>

<nav id="toc">
  <h1>Table of Contents</h1>
  <ol>
    {toc_html}
  </ol>
</nav>

{body_html}

</body>
</html>"""


def main():
    print("Loading PDF...")
    reader = PdfReader(PDF_PATH)
    boundaries = load_boundaries()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_sections = {}

    for num in sorted(boundaries.keys()):
        info = boundaries[num]
        print(f"  Processing Surah {num}: {info['name']} (pp. {info['start']}-{info['end']})...")
        pages = extract_pages(reader, info["start"], info["end"])
        sections = parse_pages_to_sections(pages)
        all_sections[num] = sections

        md = generate_surah_markdown(num, info, sections)
        filename = f"Surah_{num:03d}_{info['name'].replace(' ', '_').replace('-', '_')}.md"
        primary_vol = info["volumes"][0]
        vol_dir = OUTPUT_DIR / f"Volume_{primary_vol:02d}"
        vol_dir.mkdir(exist_ok=True)
        (vol_dir / filename).write_text(md, encoding="utf-8")
        chapters_dir = OUTPUT_DIR / "chapters"
        chapters_dir.mkdir(exist_ok=True)
        (chapters_dir / filename).write_text(md, encoding="utf-8")

    print("Building combined HTML...")
    html_content = build_combined_html(boundaries, all_sections)
    COMBINED_HTML.write_text(html_content, encoding="utf-8")
    print(f"  Written: {COMBINED_HTML}")

    print("Generating PDF (this may take several minutes)...")
    try:
        from weasyprint import HTML
        HTML(string=html_content).write_pdf(str(COMBINED_PDF))
        print(f"  Written: {COMBINED_PDF} ({COMBINED_PDF.stat().st_size / 1024 / 1024:.1f} MB)")
    except Exception as e:
        print(f"  WeasyPrint failed: {e}")
        print("  Attempting fpdf2 fallback...")
        generate_pdf_fpdf(boundaries, all_sections)

    # Update INDEX
    index_lines = [
        "# Tafsir Ibn Kathir — Faithful Chapter Texts",
        "",
        f"**Source:** {SOURCE_CITATION}",
        "",
        "Each file contains the extracted tafsir text with PDF page citations. "
        "No content has been added beyond conservative OCR cleanup.",
        "",
        f"**Combined PDF:** [Tafsir_Ibn_Kathir_Complete.pdf](Tafsir_Ibn_Kathir_Complete.pdf)",
        "",
        "---",
        "",
    ]
    for num in sorted(boundaries.keys()):
        info = boundaries[num]
        fn = f"Surah_{num:03d}_{info['name'].replace(' ', '_').replace('-', '_')}.md"
        index_lines.append(f"- Surah {num}: {info['name']} — [chapters/{fn}](chapters/{fn}) (PDF pp. {info['start']}–{info['end']})")
    (OUTPUT_DIR / "INDEX.md").write_text("\n".join(index_lines), encoding="utf-8")

    print("Done.")


def generate_pdf_fpdf(boundaries, all_sections):
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 15, "Tafsir Ibn Kathir", ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, "Abridged English Edition (Darussalam)", ln=True, align="C")
    pdf.ln(10)

    for num in sorted(boundaries.keys()):
        info = boundaries[num]
        sections = all_sections[num]
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.multi_cell(0, 8, f"Surah {num}: {info['name']}")
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5, f"PDF pp. {info['start']}-{info['end']}")
        pdf.ln(4)

        for sec in sections[:30]:  # limit sections per surah for fpdf fallback
            pdf.set_font("Helvetica", "B", 11)
            h = sec["heading"][:100]
            pdf.multi_cell(0, 6, h)
            pdf.set_font("Helvetica", "I", 8)
            pdf.multi_cell(0, 4, format_citation(sec["start_page"], sec["end_page"]))
            pdf.set_font("Helvetica", "", 10)
            text = sec["text"][:3000]
            pdf.multi_cell(0, 5, text)
            pdf.ln(3)

    pdf.output(str(COMBINED_PDF))
    print(f"  Written (fpdf fallback): {COMBINED_PDF}")


if __name__ == "__main__":
    main()
