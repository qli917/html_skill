# Extract HTML Main

![license](https://img.shields.io/badge/license-MIT-green)
![python](https://img.shields.io/badge/python-3.10%2B-blue)

Extract readable main content from messy HTML, local files, and URLs.

The tool removes common page noise such as navigation, sidebars, ads, comments, related links, login prompts, and footers before returning text, Markdown, or JSON diagnostics.

## Quick start

```bash
bash install.sh
python3 scripts/extract_html_main.py examples/messy_article.html --format markdown
```

Install browser rendering for dynamic pages:

```bash
bash install.sh --with-browser
```

## Use cases

- Clean pages before summarization.
- Extract article text for RAG ingestion.
- Post-process scraped HTML.
- Convert saved pages to Markdown.

## Features

- Raw HTML, local HTML files, and URLs.
- Playwright/Chromium rendering with static HTTP fallback.
- Manual CSS selector support.
- Reusable selector cache.
- `text`, `markdown`, and `json` output.
- Original HTML vs extracted HTML comparison pages.

## Common commands

```bash
python3 scripts/extract_html_main.py input.html --format markdown
python3 scripts/extract_html_main.py https://example.com/article --format json
python3 scripts/extract_html_main.py input.html --selector ".article-body" --format markdown
python3 scripts/extract_html_main.py input.html --format markdown --output body.md
```

## How it works

The extractor loads the best DOM it can get, removes obvious noise nodes, builds candidate content containers, scores candidates by text length, paragraph count, punctuation density, semantic tags, link density, and noisy names, then outputs the cleaned result.

## Main files

- `SKILL.md`: Codex skill instructions and workflow.
- `scripts/extract_html_main.py`: Main extraction CLI.
- `scripts/make_html_compare.py`: Original-vs-extracted HTML comparison page generator.
- `scripts/smoke_test.sh`: Local syntax and extraction smoke test.
- `examples/`: Runnable messy HTML samples.
- `references/heuristics.md`: Candidate scoring and cleanup rules.
- `docs/RELEASE_CHECKLIST.md`: Pre-release checklist and repository setting suggestions.

## Development checks

```bash
bash scripts/smoke_test.sh
```

Or run checks manually:

```bash
python3 -m py_compile scripts/extract_html_main.py scripts/make_html_compare.py
python3 scripts/extract_html_main.py examples/messy_article.html --format markdown
```

## License

MIT License. See `LICENSE`.
