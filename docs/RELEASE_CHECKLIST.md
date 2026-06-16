# Release Checklist

Before publishing a public announcement for this repository:

- [ ] Confirm the README explains the problem in the first 30 seconds.
- [ ] Confirm the installation command works on a clean machine.
- [ ] Confirm the example command works:

```bash
python3 scripts/extract_html_main.py examples/messy_article.html --format markdown
```

- [ ] Confirm the smoke workflow passes.
- [ ] Set the GitHub About description to:

```text
Extract readable main content from messy HTML and URLs for AI agents, RAG pipelines, summarization, and scraping cleanup.
```

- [ ] Add GitHub topics:

```text
html
readability
content-extraction
web-scraping
playwright
beautifulsoup
python
markdown
rag
ai-agent
codex
```

- [ ] Create release `v0.1.0`.

Suggested release notes:

```text
Initial public release.

- Extract readable main content from raw HTML, local files, and URLs.
- Use Playwright/Chromium for dynamic pages with static HTTP fallback.
- Support manual CSS selectors.
- Support reusable selector cache.
- Generate original HTML vs extracted HTML comparison pages.
```
