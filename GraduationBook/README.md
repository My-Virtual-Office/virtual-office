# Virtual Office — Graduation Book (LaTeX)

A 65-page graduation book documenting the **Virtual Office** platform: the
microservices backend, the 2D virtual office (SkyOffice), and the web and mobile
clients.

## Structure
```
main.tex            # master file (book class) — \input's everything
preamble.tex        # packages, brand colours, styles, custom macros
chapters/
  00-titlepage.tex  00-abstract.tex
  01-introduction.tex        02-background.tex
  03-requirements.tex        04-architecture.tex
  05-backend.tex             06-skyoffice.tex
  07-web.tex                 08-mobile.tex
  09-testing.tex             10-conclusion.tex
figures/            # (empty — all diagrams are inline TikZ, no external images)
```

All figures are drawn with TikZ, so the project is fully self-contained (no image
assets required).

## How to compile

**Option A — Overleaf (easiest):** upload the whole `GraduationBook` folder, set
`main.tex` as the main document, and compile (pdfLaTeX or XeLaTeX). Run twice so
the table of contents and cross-references resolve.

**Option B — Local TeX Live / MiKTeX:**
```bash
pdflatex main
pdflatex main      # second pass for TOC + refs
```

**Option C — Tectonic (single binary, downloads packages on demand):**
```bash
tectonic -X compile main.tex
```

## Notes
- Book class, 11pt, two-sided. Chapters are numbered; front matter (title,
  abstract, TOC, lists of figures/tables) uses roman page numbers.
- Content reflects the codebase as of July 2026, including the honest state of
  each component (implemented services vs. scaffolds).
- Team/supervisor metadata was intentionally left off the title page — fill it in
  as needed.
