#!/usr/bin/env python3
"""
Generate detailed chapter summaries from Tafsir Ibn Kathir PDF using verified page boundaries.
"""

import re
import json
from pathlib import Path
from pypdf import PdfReader

PDF_PATH = "/tmp/tafsir_full.pdf"
BOUNDARIES_PATH = Path(__file__).parent / "surah_boundaries.json"
OUTPUT_DIR = Path("/workspace/tafsir_summaries")

VOLUME_RANGES = {
    1: (1, 698), 2: (699, 1322), 3: (1323, 1872), 4: (1873, 2540),
    5: (2541, 3166), 6: (3167, 3870), 7: (3871, 4590), 8: (4591, 5284),
    9: (5285, 5946), 10: (5947, 6610),
}


def load_boundaries():
    with open(BOUNDARIES_PATH) as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}


def extract_text_range(reader, start, end):
    parts = []
    for i in range(start - 1, min(end, len(reader.pages))):
        parts.append(reader.pages[i].extract_text() or "")
    return "\n".join(parts)


def extract_section_headings(text):
    """Extract subsection headings from tafsir text."""
    headings = []
    patterns = [
        r'The (?:Meaning|Story|Virtue|Virtues|Reason|Merit|Significance|Tafsir|Explanation|Description) of[^.\n]{8,100}',
        r'Why (?:there is|Allah|the|it|this)[^.\n]{5,90}',
        r'The (?:Story|Battle|Day|Incident|Command|Prohibition|Warning|Promise) (?:of|to|about|against)[^.\n]{5,80}',
        r'(?:Allah|Prophet|Messenger) (?:said|says|commanded|revealed|informed|mentions)[^.\n]{5,60}',
        r'The (?:Tafsir of )?(?:Ayah|Verse) \d+',
        r'Regarding [^.\n]{10,90}',
        r'Encouragement to [^.\n]{10,80}',
        r'Warning (?:against|about|to)[^.\n]{10,80}',
        r'The (?:Creation|Punishment|Reward|Torment|Paradise|Hell)[^.\n]{5,70}',
        r'Ibn [A-Za-z\'\-]+ (?:said|narrated|reported)',
        r'It was narrated (?:that|from)',
        r'Concerning Allah\'s (?:statement|saying)',
        r'The (?:Beginning|End|Introduction) of',
        r'(?:Surat|Surah) [A-Za-z\'\-]+ (?:was|is) revealed',
        r'The (?:Attributes|Qualities|Rights|Rulings) of',
        r'How [^.\n]{10,80}',
        r'What (?:is|does|are)[^.\n]{10,80}',
    ]
    seen = set()
    for line in text.split("\n"):
        line = line.strip()
        if len(line) < 15 or len(line) > 150:
            continue
        for pat in patterns:
            m = re.search(pat, line, re.I)
            if m:
                h = m.group(0).strip()
                key = h.lower()[:60]
                if key not in seen:
                    seen.add(key)
                    headings.append(h)
                break
    return headings[:40]


def extract_stories(text, limit=20):
    """Extract narrative passages with prophet/historical content."""
    story_markers = [
        r'Prophet (?:Muhammad|Ibrahim|Nuh|Musa|Yusuf|Yunus|Isa|Adam|Hud|Salih|Dawud|Sulayman|Lut|Shuayb)',
        r'(?:story|incident|event|battle) of [A-Za-z]+',
        r'It was narrated (?:that|from)',
        r'When (?:the|Allah|Prophet|they|he)',
        r'The (?:people of|nation of|children of) [A-Za-z]+',
        r'(?:Pharaoh|Fir\'awn|Qarun|Abu Jahl|Abu Lahab|Heraclius)',
        r'(?:Battle|Day) of [A-Za-z]+',
        r'Banu [A-Za-z]+',
        r'Allah (?:sent|destroyed|commanded|revealed|saved)',
        r'Messenger of Allah',
        r'Companions of the Prophet',
    ]
    stories = []
    sentences = re.split(r'(?<=[.!?])\s+', text)
    seen_text = set()
    for i, sentence in enumerate(sentences):
        if len(sentence) < 50:
            continue
        for marker in story_markers:
            if re.search(marker, sentence, re.I):
                ctx = " ".join(sentences[i:i + 4])
                key = ctx[:80]
                if key not in seen_text and len(ctx) > 80:
                    seen_text.add(key)
                    stories.append(ctx[:600])
                break
    return stories[:limit]


def extract_key_concepts(text):
    concepts_map = {
        "Tawhid (Oneness of Allah)": r'Tawhid|oneness of Allah|La ilaha|none has the right to be worshipped|worship Allah Alone',
        "Guidance and the Straight Path": r'guidance|straight path|those who went astray|misguidance',
        "Paradise and Hell": r'Paradise|Hell|Jahannam|Garden|eternal|torment|punishment',
        "Prophethood and Revelation": r'Prophet|Messenger|prophethood|revelation|Wahi|revealed',
        "Angels and Jinn": r'angel|Jibril|Gabriel|Mika\'il|Jinn|Shaytan|devil',
        "Day of Judgment": r'Day of (?:Resurrection|Judgment|Reckoning)|Qiyamah|Hereafter',
        "Prayer and Worship": r'prayer|Salah|prostration|Sujud|worship|fasting|Sawm|Zakah',
        "Justice and Rights": r'justice|rights|oppression|inheritance|equity',
        "Family and Social Law": r'marriage|divorce|wife|husband|children|orphan',
        "Stories of Past Nations": r'nation|destroyed|punishment befell|people of',
        "Hypocrisy and Disbelief": r'hypocrite|disbeliev|Nifaq|Kufr',
        "Patience and Trust in Allah": r'patience|Sabr|trust in Allah|Tawakkul',
        "Knowledge and Wisdom": r'knowledge|wisdom|scholar|understanding',
        "Covenant and Obedience": r'covenant|obedience|command|prohibition|forbidden',
        "Mercy and Forgiveness": r'mercy|forgiveness|forgive|Most Merciful|Oft-Forgiving',
    }
    found = []
    for concept, pattern in concepts_map.items():
        count = len(re.findall(pattern, text, re.I))
        if count >= 2:
            found.append((concept, count))
    found.sort(key=lambda x: -x[1])
    return [c for c, _ in found[:12]]


def summarize_by_headings(text, headings):
  sections = []
  if not headings:
    # Fall back to paragraph chunks
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if len(p.strip()) > 100]
    for i, para in enumerate(paragraphs[:15]):
      sentences = re.split(r'(?<=[.!?])\s+', para)
      summary = " ".join(s for s in sentences[:3] if len(s) > 25)[:500]
      if summary:
        sections.append({"heading": f"Section {i+1}", "summary": summary})
    return sections

  for heading in headings[:25]:
    # Find text near heading
    idx = text.lower().find(heading.lower()[:30])
    if idx == -1:
      continue
    chunk = text[idx:idx + 2500]
    sentences = re.split(r'(?<=[.!?])\s+', chunk)
    summary_parts = []
    for s in sentences[1:5]:
      if len(s) > 30:
        summary_parts.append(s.strip())
    if summary_parts:
      sections.append({
        "heading": heading[:120],
        "summary": " ".join(summary_parts)[:650],
      })
  return sections


def get_volume_portion(start, end, vol):
    v_start, v_end = VOLUME_RANGES[vol]
    portion_start = max(start, v_start)
    portion_end = min(end, v_end)
    if portion_start <= portion_end:
        return portion_start, portion_end
    return None


def generate_markdown(num, info, reader):
    name = info["name"]
    start = info["start"]
    end = info["end"]
    volumes = info["volumes"]
    text = extract_text_range(reader, start, end)
    word_count = len(text.split())
    page_count = end - start + 1

    headings = extract_section_headings(text)
    stories = extract_stories(text)
    concepts = extract_key_concepts(text)
    sections = summarize_by_headings(text, headings)

    vol_str = ", ".join(str(v) for v in volumes)

    md = f"""# Surah {num}: {name}

**Volume(s):** {vol_str}  
**PDF pages:** {start}–{end} ({page_count} pages)  
**Approximate length:** {word_count:,} words

---

## Overview

This document summarizes the abridged **Tafsir Ibn Kathir** (Darussalam English edition) for **Surah {name}** (Chapter {num} of the Qur'an). Ibn Kathir explains verse meanings, cites authentic hadiths from Prophet Muhammad, records views of the Companions and early scholars, and provides historical and legislative context.

---

## Main Themes and Key Concepts

"""
    for c in concepts:
        md += f"- {c}\n"
    if not concepts:
        md += "- Quranic exegesis grounded in hadith and scholarly tradition\n"

    md += "\n---\n\n## Detailed Section Summaries\n\n"
    for i, sec in enumerate(sections, 1):
        md += f"### {i}. {sec['heading']}\n\n{sec['summary']}\n\n"

    md += "---\n\n## Stories, Narrations, and Historical Accounts\n\n"
    if stories:
        for i, story in enumerate(stories, 1):
            md += f"**{i}.** {story}\n\n"
    else:
        md += "_See section summaries above for narrative content embedded in the commentary._\n\n"

    md += "---\n\n## Important Points and Takeaways\n\n"
    takeaways = []
    for sec in sections[:10]:
        s = sec["summary"]
        if any(k in s.lower() for k in ["allah", "prophet", "commanded", "revealed", "must", "forbidden", "reward", "punishment", "believer"]):
            takeaways.append(s[:350])
    if not takeaways:
        takeaways = [s["summary"][:300] for s in sections[:6] if s.get("summary")]
    for pt in takeaways[:8]:
        md += f"- {pt}\n"

    if len(volumes) > 1:
        md += "\n\n## Volume Coverage\n\n"
        for vol in volumes:
            portion = get_volume_portion(start, end, vol)
            if portion:
                ps, pe = portion
                md += f"- **Volume {vol}:** pages {ps}–{pe}\n"

    md += f"\n---\n\n*Source: Tafsir Ibn Kathir (Abridged), Darussalam. Volume(s) {vol_str}.*\n"
    return md


def main():
    print("Loading PDF and boundaries...")
    reader = PdfReader(PDF_PATH)
    boundaries = load_boundaries()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for vol in range(1, 11):
        (OUTPUT_DIR / f"Volume_{vol:02d}").mkdir(exist_ok=True)

    index_md = "# Tafsir Ibn Kathir — Chapter Summaries\n\n"
    index_md += "Detailed summaries of all 114 Quranic chapters from the abridged English Tafsir Ibn Kathir (Darussalam), organized by volume.\n\n"
    index_md += "| Volume | Surahs Covered |\n|--------|----------------|\n"
    vol_surah_lists = {
        1: "1 (Al-Fatihah), 2 (partial Al-Baqarah)",
        2: "2 (Al-Baqarah continued), 3 (Al-Imran), 4 (partial An-Nisa)",
        3: "4 (An-Nisa continued), 5 (Al-Maidah), 6 (Al-Anam)",
        4: "7–10 (Al-Araf through Yunus)",
        5: "11–17 (Hud through partial Al-Isra)",
        6: "16–23 (An-Nahl continued through Al-Muminun)",
        7: "24–33 (An-Nur through partial Al-Ahzab)",
        8: "33–44 (Al-Ahzab continued through Ad-Dukhan)",
        9: "45–63 (Al-Jathiyah through Al-Munafiqun)",
        10: "64–114 (At-Taghabun through An-Nas)",
    }
    for v, desc in vol_surah_lists.items():
        index_md += f"| Volume {v} | {desc} |\n"
    index_md += "\n---\n\n"

    for vol in range(1, 11):
        index_md += f"## Volume {vol}\n\n"
        vol_entries = [(n, b) for n, b in sorted(boundaries.items()) if vol in b["volumes"]]
        for num, info in vol_entries:
            print(f"  Surah {num}: {info['name']} (pages {info['start']}-{info['end']})...")
            md = generate_markdown(num, info, reader)
            filename = f"Surah_{num:03d}_{info['name'].replace(' ', '_').replace('-', '_')}.md"
            filepath = OUTPUT_DIR / f"Volume_{vol:02d}" / filename
            filepath.write_text(md, encoding="utf-8")
            rel = f"Volume_{vol:02d}/{filename}"
            index_md += f"- [Surah {num}: {info['name']}]({rel}) (PDF pp. {info['start']}–{info['end']})\n"
        index_md += "\n"

    (OUTPUT_DIR / "INDEX.md").write_text(index_md, encoding="utf-8")
    print(f"\nComplete! {len(boundaries)} surah summaries in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
