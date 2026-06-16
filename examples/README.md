# Examples

This directory contains runnable HTML samples for quick validation and demos.

## Messy article

Run:

```bash
python3 scripts/extract_html_main.py examples/messy_article.html --format markdown
```

Expected behavior:

- Keeps the article title, paragraphs, list, and quote.
- Drops navigation, sidebar links, advertisement blocks, comments, and footer text.

Generate a visual comparison page:

```bash
python3 scripts/make_html_compare.py examples/messy_article.html \
  --selector "article.article-body" \
  --output compare.html
```

Then open `compare.html` in a browser.
