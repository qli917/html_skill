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
python3 scripts/extract_html_main.py https://example.com/article --format json
python3 scripts/extract_html_main.py input.html --output body.txt
python3 scripts/extract_html_main.py https://example.com/article --no-browser --format markdown
python3 scripts/extract_html_main.py https://example.com/article --selector ".article-body" --save-domain-class
```

URLs use Playwright/Chromium by default, then fall back to static HTTP fetching if browser rendering is unavailable. Use `--no-browser` only for simple pages or when you explicitly want static fetching. Use `--browser` to force rendering for local files or raw HTML whose useful content is injected by JavaScript.

## Manual Selector Cache

Use a local selector cache when a human has already identified the正文 container for a site. The default cache path is `~/.codex/html_main_selectors.json`.

Prefer domain-level class rules for large batches: save a known正文 container class by domain. On later pages from the same domain, if the class exists, use it. If the class is absent or `selector_found` is false, ask for an explicit selector or continue with automatic extraction.

1. Save a known selector:

```bash
python3 scripts/extract_html_main.py "https://news.qq.com/rain/a/20260614A05A1300" \
  --selector ".rich_media_content" \
  --save-domain-class \
  --format markdown
```

3. On future pages matching the same cached rule, omit `--selector`; the script uses the cached selector automatically:

```bash
python3 scripts/extract_html_main.py "https://news.qq.com/rain/a/20260615A0000000" --format markdown
```

Browser-based selector picking is not included. Use an explicit `--selector` when a site needs a known content container.

## Workflow

1. Identify the input type: URL, local `.html`, raw HTML string, or already-rendered DOM dump.
2. For URLs, let the script use Chrome/Playwright first; for local files or raw HTML, add `--browser` when JavaScript rendering is needed.
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
- Render URLs by default so JavaScript, SPA shells, and lazy-loaded正文 are available before extraction.
- Wait for `networkidle` or a short timeout, then scroll once or twice to trigger lazy-loaded正文.
- Remove overlays that block reading only after the page has loaded.
- Prefer DOM text from the rendered page over raw `innerText` for the whole body; whole-body extraction usually over-includes navigation.
- If browser dependencies are missing, fall back to static parsing and tell the user browser rendering was unavailable.

## Resources

- `scripts/extract_html_main.py`: extraction utility for URLs and local HTML.
- `scripts/make_html_compare.py`: original-vs-extracted HTML comparison page generator.
- `references/heuristics.md`: scoring and cleanup details. Read it before modifying the extraction logic or handling a difficult page.

## Dependency Handling

The script works best with:

- `beautifulsoup4` for static parsing.
- `readability-lxml` as an optional extra signal.
- `playwright` plus installed Chromium/Chrome for rendered pages.

Do not install dependencies unless the user allows it. If dependencies are missing, use whatever path is available and report the limitation.
