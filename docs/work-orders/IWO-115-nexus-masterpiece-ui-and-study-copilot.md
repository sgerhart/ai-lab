# IWO-115 — Knowledge Nexus Masterpiece UI & Grounded Study Copilot

**Status:** Complete (unit; not deployed)  
**Priority:** P1  
**Effort:** M  
**Owner:** human / Antigravity  
**Feature:** FEAT-004, FEAT-020  
**Services / Areas:** platform, docs  

Work Order Protocol Level 2 implementation order for elevating the Knowledge Nexus UI into a unified masterpiece: full AI Lab glassmorphic aesthetic, rich book cover gallery across 149+ technical volumes, grounded Qdrant RAG AI Study Copilot, and streamlined dual-format reading workflows.

## Problem

The current Knowledge Nexus interface on `http://mac-mini:8088/nexus/` has several aesthetic and functional deficiencies:
1. **Visual Disconnect & Legacy Styling:** Nexus uses legacy font tokens (`Plus Jakarta Sans`), flat box borders, and older color ramps that clash with the modern AI Lab design system (`Outfit`, `Inter`, `JetBrains Mono`, deep dark glassmorphism, glowing cyan/indigo/emerald accents).
2. **Missing Book Covers Across Library:** Despite `control_app.py` having a high-performance `/v1/nexus/cover?path={rel_path}` endpoint, `renderLibrary()` in `app.js` renders only plain text cards, leaving the 149-book technical library feeling like a flat file directory rather than an executive digital library.
3. **Broken Qdrant RAG Grounding in AI Study Copilot:** In `app.js`, `sendStudyMessage()` previously formatted study prompts as `[Context: Steven Gerhart is currently studying the book "${studyState.bookTitle}"]` without the file path. Because `control_app.py` line 259 explicitly requires `Path: "..."` to extract `rel_path` and invoke `extract_book_context(rel_path, clean_q)`, Qdrant vector retrieval and disk excerpts were bypassed entirely, leaving study answers ungrounded.
4. **Study Assistant UX & Markdown Limitations:** Assistant responses in study mode render raw text without code copy buttons, crisp tables, or structured formatting, and model options include outdated identifiers.
5. **Version Control & Serving Hygiene:** Nexus web assets previously lived only in `~/.ai-lab/nexus/` outside of Git version control, making visual improvements untracked and risking drift.

## Decision Context

- **Unified AI Lab Design System:**
  - Typography: Google Fonts `Outfit` (headings, display, brand), `Inter` (body, cards, messages), and `JetBrains Mono` (code, filenames, paths, badges).
  - Surface Palette: `--bg-primary: #070a12`, `--bg-secondary: #0d1322`, `--bg-card: rgba(15, 23, 42, 0.72)`, glowing borders `rgba(255, 255, 255, 0.08)` and `rgba(99, 102, 241, 0.3)`.
  - Luminous Accent Accents: Cyan (`#38bdf8`), Indigo (`#818cf8`), Emerald (`#10b981`), Violet (`#c084fc`).
- **Dynamic Book Cover Gallery:**
  - Render book cards with real covers via `/v1/nexus/cover?path=${encodeURIComponent(primaryPath)}`.
  - Lazy loading with smooth fade-in and automatic graceful fallback to a bespoke mini-cover with category color gradients and book title when an image is unavailable.
  - Quick action buttons directly on cards: *🎓 Study Copilot*, *📄 PDF*, *📖 EPUB*.
- **Grounded Qdrant RAG Study Copilot:**
  - Fix prompt payload to `[Study Context: Book: "${studyState.bookTitle}", Path: "${studyState.relPath}"]\n\n${cleanText}`.
  - Set `agent: "study"` on conversation creation to trigger `prepare_grounded_turn` in `control_app.py`.
  - Ensure `studyState.relPath` is preserved as the clean relative path for backend RAG indexing while `studyState.pdfPath` is used for viewer frame URL.
  - Elevated split-screen workspace with collapsible viewer, clean model selector (`Auto (Local M4)`, `Qwen 3.6`, `Qwen 3.8`, `GPT-4o-mini`), and quick study prompt chips.
- **Git Version Control & Static Mounting:**
  - Maintain canonical web assets in `platform/src/ai_lab_platform/nexus_web/`.
  - Update `control_app.py`'s `_ICloudStaticFiles` to support an overlay directory so `nexus_web/` assets are served directly while books are served from disk.

## What To Build / Fix

1. **Version Control & Static Mount (`control_app.py`):**
   - Track `nexus_web/` assets in repository.
   - Update `_ICloudStaticFiles` to resolve web assets from `NEXUS_WEB_DIR` overlay if present, serving books from `~/.ai-lab/nexus/`.
2. **HTML Modernization (`nexus_web/index.html`):**
   - Update Google Fonts to `Outfit`, `Inter`, `JetBrains Mono`.
   - Update branding header with AI Lab status indicators and consistent navigation tabs.
   - Refine study workspace layout, quick chips, and model picker.
3. **CSS Design System Overhaul (`nexus_web/styles.css`):**
   - Apply AI Lab dark glass tokens, background ambient glow, modern buttons, and responsive grid.
   - Add rich book cover card styling, hover elevation, cover image wrappers, and fallback covers.
   - Style the split-screen study workspace, chat bubbles, code blocks, and markdown elements.
4. **JavaScript & RAG Logic (`nexus_web/app.js`):**
   - Render book covers in `renderLibrary()` with fallback handling.
   - Fix `openStudyMode()` and `sendStudyMessage()` to pass `[Study Context: Book: "${studyState.bookTitle}", Path: "${studyState.relPath}"]`.
   - Enhance markdown parser with code highlighting, copy buttons, and list formatting.
   - Add direct "Study Copilot" trigger buttons on each book card.
5. **Validation:**
   - Verify repo validation scripts (`./scripts/validate-repo.sh`, `./tests/test_structure.sh`).
   - Run platform unit tests (`python3 -m unittest discover -s tests -v`).

## Expected Change Surface

- `platform/src/ai_lab_platform/nexus_web/index.html`
- `platform/src/ai_lab_platform/nexus_web/styles.css`
- `platform/src/ai_lab_platform/nexus_web/app.js`
- `platform/src/ai_lab_platform/nexus_web/library-sync.js`
- `platform/src/ai_lab_platform/control_app.py`
- `docs/work-orders/IWO-115-nexus-masterpiece-ui-and-study-copilot.md`
- `docs/work-orders/README.md`
