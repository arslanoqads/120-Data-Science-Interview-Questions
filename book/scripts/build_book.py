#!/usr/bin/env python3
"""Assemble and render the AI Engineer / FDE Curriculum print PDF."""

from __future__ import annotations

import html
import re
from pathlib import Path

import markdown as md_lib
from weasyprint import CSS, HTML

ROOT = Path("/workspace")
TEXTBOOK = ROOT / "textbook"
BOOK = ROOT / "book"
OUT = BOOK / "output"
ASSETS = BOOK / "assets" / "diagrams"
STYLES = BOOK / "styles" / "print.css"

CHAPTERS = [
    ("phase-0", "week-01-python-production", 1, "Python for Production, Not for Notebooks"),
    ("phase-0", "week-02-apis-async-testing", 2, "APIs, Async, and Testing Discipline"),
    ("phase-0", "week-03-git-containers-system-design", 3, "Git Discipline, Containers, and System Design Literacy"),
    ("phase-1", "week-04-multi-provider-llm", 4, "Multi-Provider LLM Engineering"),
    ("phase-1", "week-05-prompt-engineering", 5, "Prompt Engineering as a Versioned Artifact"),
    ("phase-2", "week-06-ingestion-chunking", 6, "Ingestion and Chunking Strategy"),
    ("phase-2", "week-07-retrieval-beyond-cosine", 7, "Retrieval Beyond Cosine Similarity"),
    ("phase-2", "week-08-reranking-query-understanding", 8, "Reranking and Query Understanding"),
    ("phase-2", "week-09-rag-failure-taxonomy", 9, "RAG Failure Taxonomy and Debugging"),
    ("phase-2", "week-10-rag-evaluation", 10, "RAG Evaluation"),
    ("phase-3", "week-11-agent-fundamentals", 11, "Agent Fundamentals and Tool Use"),
    ("phase-3", "week-12-mcp", 12, "Model Context Protocol (MCP)"),
    ("phase-3", "week-13-orchestration-multi-agent", 13, "Orchestration and Multi-Agent Systems"),
    ("phase-3", "week-14-domain-agent-side-effects", 14, "Domain Agents and Side Effects"),
    ("phase-3", "week-15-agent-evaluation", 15, "Agent Evaluation"),
    ("phase-4", "week-16-error-analysis-flywheel", 16, "Error Analysis and the Data Flywheel"),
    ("phase-4", "week-17-llm-judge-observability", 17, "LLM-as-Judge and Observability"),
    ("phase-5", "week-18-deployment-infra", 18, "Deployment and Infrastructure"),
    ("phase-5", "week-19-auth-identity-enterprise", 19, "Auth, Identity, and Enterprise Trust"),
    ("phase-5", "week-20-cost-latency-engineering", 20, "Cost and Latency Engineering"),
    ("phase-5", "week-21-legacy-messy-integration", 21, "Legacy and Messy System Integration"),
    ("phase-6", "week-22-capstone-integration", 22, "Capstone Integration"),
    ("phase-6", "week-23-system-design-interview", 23, "System Design Interview Readiness"),
    ("phase-6", "week-24-portfolio-positioning", 24, "Portfolio Positioning"),
    ("phase-7", "week-25-context-engineering", 25, "Context Engineering as a Discipline"),
    ("phase-7", "week-26-fine-tuning", 26, "Fine-Tuning When RAG Isn’t Enough"),
    ("phase-7", "week-27-open-source-self-hosted", 27, "Open-Source and Self-Hosted Models"),
    ("phase-7", "week-28-multimodal", 28, "Multimodal AI"),
    ("phase-7", "week-29-ai-safety-adversarial", 29, "AI Safety, Ethics, and Adversarial Testing"),
]

PHASES = {
    0: ("Phase 0 — Engineering Foundations", "Weeks 1–3 · Production Python, APIs, Git, containers, and system-design literacy."),
    1: ("Phase 1 — LLM Application Engineering Core", "Weeks 4–5 · Multi-provider clients and versioned prompt engineering."),
    2: ("Phase 2 — RAG Systems Built for Production", "Weeks 6–10 · Ingestion, hybrid retrieval, reranking, failure taxonomy, evaluation."),
    3: ("Phase 3 — Agentic Systems", "Weeks 11–15 · Tool use, MCP, orchestration, side effects, agent evals."),
    4: ("Phase 4 — Evals and Observability", "Weeks 16–17 · Error analysis flywheel, LLM-as-judge, tracing dashboards."),
    5: ("Phase 5 — Production, Cost, and Systems", "Weeks 18–21 · Deploy, identity, cost/latency, messy integrations."),
    6: ("Phase 6 — Capstone and Interview Readiness", "Weeks 22–24 · Integration polish, interview drills, portfolio positioning."),
    7: ("Phase 7 — Supplementary Electives", "Weeks 25–29 · Context engineering, fine-tuning decisions, self-hosting, multimodal, safety."),
}

# Insert figures after these chapter numbers (into chapter HTML body start)
FIGURE_INSERTS = {
    1: [("fig-01-curriculum-roadmap.svg", "Curriculum roadmap across seven phases."),
        ("fig-02-week1-packaging-stack.svg", "Week 1 packaging stack: package → locks → types → tests → CI.")],
    2: [("fig-06-test-pyramid.svg", "Practical test pyramid for LLM services.")],
    6: [("fig-03-rag-pipeline.svg", "RAG production pipeline from ingest through evaluation.")],
    11: [("fig-04-agent-loop.svg", "Agent loop with plan, act, observe, and stop conditions.")],
    16: [("fig-05-eval-flywheel.svg", "Error-analysis data flywheel.")],
    20: [("fig-07-model-routing.svg", "Cost and latency routing with cache and cascade.")],
    25: [("fig-08-context-layers.svg", "Context assembly layers under a finite token budget.")],
}


def strip_editorial_meta(text: str) -> tuple[str, str | None]:
    """Remove editorial metadata block; return body and syllabus build line if present."""
    syllabus = None
    m = re.search(r"> \*\*Syllabus Build:\*\* (.+?)(?:\n|$)", text)
    if m:
        syllabus = m.group(1).strip()

    # Drop blockquote meta after H1 until first ---
    text = re.sub(
        r"(# .+?\n)\n(?:> .+\n)+\n---\n*",
        r"\1\n",
        text,
        count=1,
    )
    # Drop remaining editorial-only lines if any
    text = re.sub(r"^> \*\*(Phase|Editorial status|Source of truth|Compilation status):\*\*.+\n", "", text, flags=re.M)
    return text, syllabus


def md_to_html(text: str) -> str:
    return md_lib.markdown(
        text,
        extensions=[
            "markdown.extensions.tables",
            "markdown.extensions.fenced_code",
            "markdown.extensions.nl2br",
            "markdown.extensions.sane_lists",
            "markdown.extensions.smarty",
        ],
    )


def figure_html(filename: str, caption: str) -> str:
    path = ASSETS / filename
    # Inline SVG for reliable print embedding
    svg = path.read_text(encoding="utf-8")
    # strip xml declaration
    svg = re.sub(r"<\?xml[^>]*\?>\s*", "", svg)
    return (
        f'<figure class="book-figure">'
        f'{svg}'
        f'<figcaption>{html.escape(caption)}</figcaption>'
        f"</figure>"
    )


def front_matter_html() -> str:
    toc_items = []
    current_phase = None
    for phase_dir, _slug, num, title in CHAPTERS:
        phase_n = int(phase_dir.split("-")[1])
        if phase_n != current_phase:
            current_phase = phase_n
            pname = PHASES[phase_n][0]
            toc_items.append(f'<li class="phase">{html.escape(pname)}</li>')
        toc_items.append(
            f'<li><a class="chapter-link" href="#chapter-{num}">'
            f'<span>Chapter {num}. {html.escape(title)}</span><span class="dots"></span>'
            f"</a></li>"
        )

    return f"""
<section class="front-matter half-title">
  <h1>AI Engineer / FDE Curriculum</h1>
</section>

<section class="front-matter title-page">
  <h1>From TPM to AI Engineer<br/>&amp; Forward Deployed Engineer</h1>
  <p class="subtitle">A 29-week production systems textbook</p>
  <p class="meta">
    Compiled from the syllabus research corpus<br/>
    Phases 0–6 core plan · Phase 7 supplementary electives<br/>
    Flagship system spine: Deployment Copilot<br/><br/>
    Print edition
  </p>
</section>

<section class="front-matter copyright-page">
  <p><strong>AI Engineer / FDE Curriculum — Print Edition</strong></p>
  <p>This volume is a pedagogical compilation of weekly textbook chapters derived from an
  original and supplementary syllabus research corpus. It is intended for personal study and
  interview preparation.</p>
  <p><strong>Source policy.</strong> Technical claims in this book are grounded in the accompanying
  research notes (official documentation, reputable engineering blogs, open papers, and public talks).
  Unauthorized copyrighted book text is not reproduced.</p>
  <p><strong>Figures.</strong> Process diagrams are original illustrations created for this print edition
  to summarize curriculum structure and weekly build patterns.</p>
  <p><strong>Printer notes.</strong> US Letter · black + spot-friendly teal accents · binding margin on the
  inner edge · designed for digital print / print-on-demand. No full-bleed artwork.</p>
  <p>© Curriculum compilation. All rights in cited third-party trademarks remain with their owners.</p>
</section>

<section class="front-matter toc">
  <h1>Contents</h1>
  <ul>
    <li class="phase">Front matter</li>
    <li><a class="chapter-link" href="#how-to-use"><span>How to use this book</span><span class="dots"></span></a></li>
    {''.join(toc_items)}
    <li class="phase">Back matter</li>
    <li><a class="chapter-link" href="#colophon"><span>Colophon &amp; source policy</span><span class="dots"></span></a></li>
  </ul>
</section>

<section class="front-matter" id="how-to-use">
  <h1>How to use this book</h1>
  <p>This is a <em>course textbook</em>, not a reference encyclopedia. Read chapters in order.
  Each week compounds one flagship system—working title <strong>Deployment Copilot</strong>—so later
  chapters assume earlier packages, APIs, retrieval, agents, and evals already exist.</p>
  <h2>Chapter anatomy</h2>
  <p>Every concept section uses the same six fields:</p>
  <ol>
    <li><strong>Fundamentals</strong> — what it is and why it exists</li>
    <li><strong>The Alternatives</strong> — design space and why this syllabus made its choice</li>
    <li><strong>Failure Modes</strong> — what breaks if you skip or do it naively</li>
    <li><strong>Average vs. Strong Engineer</strong> — default vs senior practice</li>
    <li><strong>Worked Example</strong> — applied to that week’s build</li>
    <li><strong>Apply It</strong> — concrete steps for the build checklist</li>
  </ol>
  <p>Where research left an open question unresolved, the text marks
  <code>[NEEDS MORE RESEARCH]</code> instead of inventing an answer.</p>
  {figure_html("fig-01-curriculum-roadmap.svg", "Figure 0.1 — Curriculum roadmap: Phases 0–6 core, Phase 7 electives.")}
</section>
"""


def phase_divider_html(phase_n: int) -> str:
    title, blurb = PHASES[phase_n]
    return f"""
<section class="phase-divider">
  <h1>{html.escape(title)}</h1>
  <p>{html.escape(blurb)}</p>
</section>
"""


def chapter_html(phase_dir: str, slug: str, num: int, title: str) -> str:
    path = TEXTBOOK / phase_dir / slug / "chapter.md"
    raw = path.read_text(encoding="utf-8")
    body, syllabus = strip_editorial_meta(raw)
    # Ensure single H1
    body = re.sub(r"^# .+?\n", f"# Chapter {num} — {title}\n", body, count=1)
    content = md_to_html(body)

    build_box = ""
    if syllabus:
        build_box = (
            f'<div class="syllabus-build"><strong>Week {num} build.</strong> '
            f"{html.escape(syllabus)}</div>"
        )

    figs = ""
    for i, (fname, caption) in enumerate(FIGURE_INSERTS.get(num, []), start=1):
        figs += figure_html(fname, f"Figure {num}.{i} — {caption}")

    # Insert build box + figures after first h1
    content = re.sub(
        r"(<h1[^>]*>.*?</h1>)",
        r"\1" + build_box + figs,
        content,
        count=1,
        flags=re.S,
    )

    return f'<section class="chapter" id="chapter-{num}">{content}</section>\n'


def back_matter_html() -> str:
    return """
<section class="back-matter" id="colophon">
  <h1>Colophon &amp; source policy</h1>
  <p>Typeset for digital print from Markdown chapter sources using Python Markdown and WeasyPrint.
  Body: DejaVu Serif. Headings and tables: DejaVu Sans. Code: DejaVu Sans Mono.</p>
  <p><strong>Allowed research sources</strong> for the underlying notes: official documentation,
  reputable engineering blogs, open conference talks, arXiv papers, and public YouTube courses/talks.</p>
  <p><strong>Not used:</strong> pirate book or PDF sites, or unauthorized reproduction of copyrighted book text.</p>
  <p>Companion materials live in the repository under <code>research/</code> (raw notes) and
  <code>textbook/</code> (weekly chapters). This PDF is the printer-facing compilation.</p>
  <p style="margin-top:2em;"><em>End of volume.</em></p>
</section>
"""


def build() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)

    parts = [front_matter_html()]
    last_phase = None
    for phase_dir, slug, num, title in CHAPTERS:
        phase_n = int(phase_dir.split("-")[1])
        if phase_n != last_phase:
            parts.append(phase_divider_html(phase_n))
            last_phase = phase_n
        print(f"  + Chapter {num}: {title}")
        parts.append(chapter_html(phase_dir, slug, num, title))
    parts.append(back_matter_html())

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>AI Engineer / FDE Curriculum — Print Edition</title>
</head>
<body>
{''.join(parts)}
</body>
</html>
"""
    html_path = OUT / "ai-engineer-fde-curriculum.html"
    pdf_path = OUT / "AI_Engineer_FDE_Curriculum_Print_Edition.pdf"
    html_path.write_text(doc, encoding="utf-8")
    print(f"Wrote HTML: {html_path}")

    print("Rendering PDF (this may take a few minutes)...")
    HTML(filename=str(html_path), base_url=str(BOOK)).write_pdf(
        str(pdf_path),
        stylesheets=[CSS(filename=str(STYLES))],
    )
    size_mb = pdf_path.stat().st_size / (1024 * 1024)
    print(f"Wrote PDF: {pdf_path} ({size_mb:.1f} MB)")
    return pdf_path


if __name__ == "__main__":
    build()
