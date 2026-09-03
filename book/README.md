# Print edition — AI Engineer / FDE Curriculum

## Deliverable

**Printer-ready PDF:** [`output/AI_Engineer_FDE_Curriculum_Print_Edition.pdf`](output/AI_Engineer_FDE_Curriculum_Print_Edition.pdf)

Also mirrored at `/opt/cursor/artifacts/AI_Engineer_FDE_Curriculum_Print_Edition.pdf` for download from this agent run.

## Specs for the printer

| Spec | Value |
|------|--------|
| Trim size | US Letter (8.5 × 11 in / 612 × 792 pt) |
| Pages | ~548 (single volume) |
| Color | Black text + teal accent diagrams (grayscale-safe) |
| Margins | ~0.87″ top, 0.71″ right, 0.94″ bottom, 0.87″ left (inner edge for binding) |
| Bleed | None (no full-bleed art) |
| Binding | Perfect bind or coil; leave the inner margin as-is |
| Paper | 50–70 lb opaque white text stock recommended |

## Contents

- Half-title, title, copyright / printer notes  
- Table of contents  
- How to use this book + curriculum roadmap figure  
- Phase dividers (0–7)  
- Chapters 1–29 (edited weekly textbook chapters)  
- Process diagrams for packaging, RAG, agents, evals, routing, context  
- Colophon & source policy  

## Rebuild

```bash
python3 book/scripts/build_book.py
```

Requires: `pandoc` (optional), `weasyprint`, `markdown`, DejaVu fonts.
