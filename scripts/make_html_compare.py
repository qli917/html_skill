#!/usr/bin/env python3
"""Generate a browser-openable comparison page for original vs extracted HTML."""

from __future__ import annotations

import argparse
import html
from pathlib import Path

from bs4 import BeautifulSoup

from extract_html_main import remove_noise


def page_shell(source_label: str, selector: str, original_html: str, extracted_html: str) -> str:
    original_srcdoc = html.escape(original_html, quote=True)
    extracted_srcdoc = html.escape(extracted_html, quote=True)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HTML 正文提取对比</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f6f7f9;
      color: #1f2937;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; }}
    header {{
      padding: 16px 20px;
      border-bottom: 1px solid #d8dee8;
      background: #fff;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 20px;
      line-height: 1.35;
      font-weight: 650;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px 16px;
      font-size: 13px;
      color: #4b5563;
    }}
    .meta code {{
      padding: 2px 6px;
      border: 1px solid #d8dee8;
      border-radius: 4px;
      background: #f9fafb;
      color: #111827;
    }}
    main {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 12px;
      height: calc(100vh - 86px);
      padding: 12px;
    }}
    section {{
      display: grid;
      grid-template-rows: auto minmax(0, 1fr);
      min-width: 0;
      border: 1px solid #d8dee8;
      background: #fff;
    }}
    h2 {{
      margin: 0;
      padding: 10px 12px;
      border-bottom: 1px solid #d8dee8;
      font-size: 15px;
      line-height: 1.3;
      font-weight: 650;
    }}
    iframe {{
      width: 100%;
      height: 100%;
      border: 0;
      background: #fff;
    }}
    @media (max-width: 900px) {{
      main {{
        grid-template-columns: 1fr;
        height: auto;
      }}
      section {{
        height: 70vh;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>HTML 正文提取对比</h1>
    <div class="meta">
      <span>source: <code>{html.escape(source_label)}</code></span>
      <span>selector: <code>{html.escape(selector)}</code></span>
    </div>
  </header>
  <main>
    <section>
      <h2>原 HTML</h2>
      <iframe title="原 HTML" srcdoc="{original_srcdoc}"></iframe>
    </section>
    <section>
      <h2>正文提取 HTML</h2>
      <iframe title="正文提取 HTML" srcdoc="{extracted_srcdoc}"></iframe>
    </section>
  </main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("--selector", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source_path = Path(args.source)
    original_html = source_path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(original_html, "html.parser")
    node = soup.select_one(args.selector)
    if node is None:
        raise SystemExit(f"selector not found: {args.selector}")
    remove_noise(node)
    extracted_html = str(node)
    output = Path(args.output)
    output.write_text(
        page_shell(str(source_path), args.selector, original_html, extracted_html),
        encoding="utf-8",
    )
    print(output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
