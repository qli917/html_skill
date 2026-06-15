---
name: extract-html-main
description: Extract readable main body content from arbitrary HTML pages, local HTML files, saved browser pages, or URLs where the article/body structure is unknown or inconsistent. Use when Codex needs to remove navigation, ads, boilerplate, comments, sidebars, scripts, hidden text, duplicated menus, or layout chrome and return clean正文/plain text/Markdown/JSON, especially when browser rendering with Chrome or Playwright may be needed for JavaScript-heavy pages.
---

# Extract HTML Main

## Overview

Extract the human-readable正文 from messy HTML with a browser-assisted first pass when possible and deterministic static fallbacks when Chrome is unavailable. Treat “正文” as the content a reader came for, not every visible string on the page.

## Quick Start

Use the bundled script for repeatable extraction:

```bash
python3 scripts/extract_html_main.py input.html --format markdown
python3 scripts/extract_html_main.py https://example.com/article --browser --format json
python3 scripts/extract_html_main.py input.html --output body.txt
python3 scripts/extract_html_main.py https://example.com/article --selector "article" --save-selector
```

Prefer `--browser` for URLs, SPA pages, pages with lazy-loaded text, paywall overlays, or HTML whose useful content is injected by JavaScript. Omit `--browser` for saved HTML when static parsing is enough.

## Manual Selector Cache

Use a local selector cache when a human has already identified the正文 container for a site. The default cache path is `~/.codex/html_main_selectors.json`.

1. Open the page in Chrome and choose the正文 container.
2. Save the selector:

```bash
python3 scripts/extract_html_main.py "https://news.qq.com/rain/a/20260614A05A1300" \
  --selector "div.rich_media_content" \
  --save-selector \
  --selector-pattern "/rain/a/" \
  --format markdown
```

3. On future pages matching the same cached rule, omit `--selector`; the script uses the cached selector automatically:

```bash
python3 scripts/extract_html_main.py "https://news.qq.com/rain/a/20260615A0000000" --format markdown
```

For manual selection in DevTools, paste `scripts/pick_main_selector.js` into the Console, click the正文 node, then use the generated selector in `--selector`.

## Workflow

1. Identify the input type: URL, local `.html`, raw HTML string, or already-rendered DOM dump.
2. If the page likely depends on JavaScript, use Chrome/Playwright through the script’s `--browser` mode.
3. Extract candidate blocks from semantic containers first: `article`, `main`, `[role=main]`, content-like classes/ids.
4. Score candidates by text density, paragraph count, punctuation, link density, boilerplate penalties, and heading proximity.
5. Clean the winning block: remove scripts/styles/nav/footer/aside/forms, hidden nodes, repeated menu text, cookie banners, share widgets, comment areas, and tracking text.
6. Return the result in the user’s requested shape. Default to Markdown or plain text; use JSON when metadata, confidence, or diagnostics matter.

## Output Rules

- Preserve paragraph order, headings, lists, code blocks, blockquotes, tables, and meaningful image alt text when present.
- Do not invent missing article text. If rendering or extraction is incomplete, say what failed and include the best extracted content with low confidence.
- Keep boilerplate out even if it is visible: navigation, related articles, recommended links, comment forms, cookie/privacy banners, ads, social buttons, copyright footers, and login prompts.
- For Chinese pages, favor punctuation-rich continuous text and avoid menu-like short links. Do not split Chinese paragraphs solely because there are no spaces.
- If multiple plausible正文 blocks exist, return the strongest block and include alternatives only when the user asks for diagnostics.

## Browser Strategy

When using Chrome/Playwright:

- Launch headless Chromium unless visual inspection is required.
- Wait for `networkidle` or a short timeout, then scroll once or twice to trigger lazy-loaded正文.
- Remove overlays that block reading only after the page has loaded.
- Prefer DOM text from the rendered page over raw `innerText` for the whole body; whole-body extraction usually over-includes navigation.
- If browser dependencies are missing, fall back to static parsing and tell the user browser rendering was unavailable.

## Resources

- `scripts/extract_html_main.py`: extraction utility for URLs and local HTML.
- `scripts/pick_main_selector.js`: DevTools helper for manually selecting and exporting a正文 CSS selector.
- `references/heuristics.md`: scoring and cleanup details. Read it before modifying the extraction logic or handling a difficult page.

## Dependency Handling

The script works best with:

- `beautifulsoup4` for static parsing.
- `readability-lxml` as an optional extra signal.
- `playwright` plus installed Chromium/Chrome for rendered pages.

Do not install dependencies unless the user allows it. If dependencies are missing, use whatever path is available and report the limitation.
