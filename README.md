# Extract HTML Main

Utilities and Codex skill instructions for extracting the readable main body from messy HTML pages, saved browser pages, and URLs.

The extractor treats main content as the text a reader came for. It removes navigation, sidebars, ads, comments, share widgets, empty layout nodes, and other page chrome before returning plain text, Markdown, or JSON diagnostics.

## What It Does

- Extracts article/body content from raw HTML, local files, and URLs.
- Uses Playwright/Chromium first for URLs, then falls back to static HTTP fetching.
- Supports manual CSS selectors when a site has a known content container.
- Caches reusable selectors by domain or path.
- Provides a Chrome DevTools helper and optional extension for picking selectors.
- Generates browser-openable comparison pages for original HTML vs extracted HTML.

## Requirements

Minimum:

```bash
python3 -m pip install beautifulsoup4
```

Recommended for dynamic pages:

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
```

If Playwright or Chromium is unavailable, URL extraction automatically falls back to static HTTP fetching.

## How It Works

The extractor first loads the most complete DOM it can get, then scores likely content containers and cleans the winning node before output.

```mermaid
flowchart TD
    A["Input"] --> B{"Input type"}
    B -->|URL| C["Render with Playwright"]
    B -->|Local HTML / raw HTML| D["Static HTML parsing"]
    C --> E{"Render succeeded?"}
    E -->|Yes| F["Use rendered DOM"]
    E -->|No| D
    D --> F

    F --> G["Remove obvious noise"]
    G --> G1["script/style/nav/header/footer/aside/form"]
    G --> G2["hidden/display:none/aria-hidden"]
    G --> G3["comments, ads, share bars, related links, login prompts"]

    G1 --> H["Build candidate content nodes"]
    G2 --> H
    G3 --> H

    H --> H1["article, main, [role=main]"]
    H --> H2["content-like class/id names"]
    H --> H3["large div/section/td/body nodes"]

    H1 --> I["Score candidates"]
    H2 --> I
    H3 --> I

    I --> I1["Reward text length, paragraphs, punctuation"]
    I --> I2["Reward semantic tags and content-like names"]
    I --> I3["Penalize high link density and short menu-like text"]
    I --> I4["Penalize nav/comment/share/related/ad names"]

    I1 --> J["Pick best node"]
    I2 --> J
    I3 --> J
    I4 --> J

    J --> K{"Selector provided?"}
    K -->|Matched| L["Use selector node"]
    K -->|Missing or unmatched| M["Use best scored node"]

    L --> N["Convert to output"]
    M --> N
    N --> N1["Preserve paragraphs, headings, lists, quotes, code, tables, useful image alt text"]
    N1 --> O["Deduplicate and normalize whitespace"]
    O --> P{"Format"}
    P -->|text| Q["Plain text"]
    P -->|markdown| R["Markdown"]
    P -->|json| S["Content plus confidence and diagnostics"]
```

## Quick Start

Extract Markdown from a local HTML file:

```bash
python3 scripts/extract_html_main.py input.html --format markdown
```

Extract JSON diagnostics from a URL. URLs render through Playwright by default when available:

```bash
python3 scripts/extract_html_main.py https://example.com/article --format json
```

Force static URL fetching:

```bash
python3 scripts/extract_html_main.py https://example.com/article --no-browser --format markdown
```

Use a known正文 selector:

```bash
python3 scripts/extract_html_main.py input.html --selector ".article-body" --format markdown
```

Write output to a file:

```bash
python3 scripts/extract_html_main.py input.html --format markdown --output body.md
```

## Selector Cache

The default selector cache is:

```text
~/.codex/html_main_selectors.json
```

Save a selector for a URL path:

```bash
python3 scripts/extract_html_main.py "https://example.com/news/123" \
  --selector ".article-body" \
  --save-selector \
  --format markdown
```

Save a domain-level class selector for repeated pages from the same site:

```bash
python3 scripts/extract_html_main.py "https://example.com/news/123" \
  --selector ".article-body" \
  --save-domain-class \
  --format markdown
```

On later pages from the same domain, omit `--selector`; the script will use the cached rule when it matches.

## Manual Selector Picking

For manual selection in Chrome DevTools:

1. Open the page.
2. Paste `scripts/pick_main_selector.js` into the Console.
3. Click the outermost正文 node.
4. Use the generated selector with `--selector`.

The repository also includes a small Chrome extension in `selector_picker_extension/`. Start the receiver first:

```bash
python3 selector_receiver.py
```

Then load `selector_picker_extension/` as an unpacked extension in Chrome. Right-click the正文 area and choose "保存为正文 selector" to save the rule locally.

## Compare Original And Extracted HTML

Generate a browser-openable comparison page:

```bash
python3 scripts/make_html_compare.py input.html \
  --selector ".article-body" \
  --output compare.html
```

Open `compare.html` in Chrome. The left pane shows the original HTML, and the right pane shows the cleaned正文 HTML.

## Main Files

- `SKILL.md`: Codex skill instructions and workflow.
- `scripts/extract_html_main.py`: Main extraction CLI.
- `scripts/make_html_compare.py`: Original-vs-extracted HTML comparison page generator.
- `scripts/pick_main_selector.js`: DevTools selector picker.
- `selector_receiver.py`: Local selector cache receiver for the Chrome extension.
- `selector_picker_extension/`: Chrome context-menu selector picker.
- `references/heuristics.md`: Candidate scoring and cleanup rules.

## Development Checks

Run a syntax check:

```bash
python3 -m py_compile scripts/extract_html_main.py selector_receiver.py scripts/make_html_compare.py
```

Run a tiny extraction smoke test:

```bash
python3 scripts/extract_html_main.py '<html><body><nav>Home</nav><article><p>Main text, with punctuation.</p></article></body></html>' --format markdown
```
