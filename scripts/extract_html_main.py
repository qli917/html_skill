#!/usr/bin/env python3
"""Extract readable main content from a URL or local HTML file."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


BAD_RE = re.compile(
    r"(nav|menu|footer|header|sidebar|aside|comment|reply|share|social|"
    r"recommend|related|advert|ad-|promo|cookie|login|subscribe|breadcrumb|"
    r"版权|导航|菜单|评论|推荐|相关|广告|分享|登录|订阅)",
    re.I,
)
GOOD_RE = re.compile(
    r"(article|content|post|entry|main|story|detail|body|text|正文|内容|文章)",
    re.I,
)
PUNCT_RE = re.compile(r"[。！？；：，、,.!?;:]")
BLOCK_TAGS = {
    "article",
    "main",
    "section",
    "div",
    "td",
    "body",
    "content",
}
DROP_TAGS = {
    "script",
    "style",
    "noscript",
    "template",
    "svg",
    "canvas",
    "iframe",
    "nav",
    "header",
    "footer",
    "aside",
    "form",
    "button",
    "input",
    "select",
    "textarea",
}


@dataclass
class Extraction:
    title: str
    text: str
    markdown: str
    confidence: float
    method: str
    diagnostics: dict


def load_source(source: str, use_browser: bool, timeout_ms: int) -> tuple[str, str]:
    if use_browser or source.startswith(("http://", "https://")) and use_browser:
        rendered = render_with_playwright(source, timeout_ms)
        if rendered:
            return rendered, "browser"

    if source.startswith(("http://", "https://")):
        req = urllib.request.Request(source, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=max(5, timeout_ms // 1000)) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            return resp.read().decode(charset, errors="replace"), "url-static"

    path = Path(source)
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace"), "file-static"

    return source, "raw-html"


def render_with_playwright(source: str, timeout_ms: int) -> str | None:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            if source.startswith(("http://", "https://")):
                page.goto(source, wait_until="domcontentloaded", timeout=timeout_ms)
            else:
                path = Path(source)
                if path.exists():
                    page.goto(path.resolve().as_uri(), wait_until="domcontentloaded", timeout=timeout_ms)
                else:
                    page.set_content(source, wait_until="domcontentloaded", timeout=timeout_ms)
            try:
                page.wait_for_load_state("networkidle", timeout=min(timeout_ms, 5000))
            except Exception:
                pass
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(500)
            page.evaluate("window.scrollTo(0, 0)")
            content = page.content()
            browser.close()
            return content
    except Exception:
        return None


def soup_from_html(raw_html: str):
    try:
        from bs4 import BeautifulSoup
    except Exception as exc:
        raise SystemExit("beautifulsoup4 is required for extraction: pip install beautifulsoup4") from exc

    return BeautifulSoup(raw_html, "html.parser")


def node_label(node) -> str:
    parts = [node.name or ""]
    attrs = []
    for key in ("id", "class", "role"):
        value = node.get(key)
        if isinstance(value, list):
            value = " ".join(value)
        if value:
            attrs.append(str(value))
    if attrs:
        parts.append(" ".join(attrs))
    return " ".join(parts)


def remove_noise(soup) -> None:
    for tag in list(soup.find_all(True)):
        label = node_label(tag)
        style = (tag.get("style") or "").replace(" ", "").lower()
        if (
            tag.name in DROP_TAGS
            or tag.has_attr("hidden")
            or tag.get("aria-hidden") == "true"
            or "display:none" in style
            or "visibility:hidden" in style
            or BAD_RE.search(label)
        ):
            tag.decompose()


def clean_lines(text: str) -> list[str]:
    text = html.unescape(text)
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    result = []
    seen = set()
    for line in lines:
        if not line:
            continue
        normalized = re.sub(r"\W+", "", line.lower())
        if len(line) < 3 or normalized in seen:
            continue
        seen.add(normalized)
        result.append(line)
    return result


def link_density(node) -> float:
    text_len = len(node.get_text(" ", strip=True))
    if not text_len:
        return 1.0
    link_text = " ".join(a.get_text(" ", strip=True) for a in node.find_all("a"))
    return len(link_text) / text_len


def score_node(node) -> float:
    text = node.get_text("\n", strip=True)
    lines = clean_lines(text)
    if not lines:
        return -1.0

    chars = sum(len(line) for line in lines)
    paragraphs = len([p for p in node.find_all(["p", "li", "blockquote"]) if len(p.get_text(strip=True)) > 20])
    punct = len(PUNCT_RE.findall(text))
    label = node_label(node)
    links = link_density(node)

    score = chars * 0.45 + paragraphs * 80 + punct * 8
    score *= max(0.15, 1.0 - links)
    if node.name in ("article", "main"):
        score *= 1.35
    if GOOD_RE.search(label):
        score *= 1.25
    if BAD_RE.search(label):
        score *= 0.35
    if len(lines) > 0:
        short_ratio = sum(1 for line in lines if len(line) < 18) / len(lines)
        score *= max(0.35, 1.0 - short_ratio * 0.6)
    return score


def candidates(soup) -> Iterable:
    preferred = soup.select("article, main, [role='main']")
    yielded = set()
    for node in preferred:
        yielded.add(id(node))
        yield node
    for node in soup.find_all(True):
        if id(node) in yielded:
            continue
        label = node_label(node)
        if node.name in BLOCK_TAGS or GOOD_RE.search(label):
            yield node


def html_to_markdown(node) -> str:
    lines = []
    for el in node.descendants:
        name = getattr(el, "name", None)
        if name in ("h1", "h2", "h3"):
            text = el.get_text(" ", strip=True)
            if text:
                lines.append(f"{'#' * int(name[1])} {text}")
        elif name in ("p", "blockquote"):
            text = el.get_text(" ", strip=True)
            if text:
                prefix = "> " if name == "blockquote" else ""
                lines.append(prefix + text)
        elif name == "li":
            text = el.get_text(" ", strip=True)
            if text:
                lines.append(f"- {text}")
        elif name == "pre":
            text = el.get_text("\n", strip=True)
            if text:
                lines.append(f"```\n{text}\n```")
    if not lines:
        lines = clean_lines(node.get_text("\n", strip=True))
    return "\n\n".join(dedupe_keep_order(lines)).strip()


def dedupe_keep_order(lines: Iterable[str]) -> list[str]:
    seen = set()
    out = []
    for line in lines:
        compact = re.sub(r"\s+", " ", line).strip()
        key = re.sub(r"\W+", "", compact.lower())
        if compact and key not in seen:
            seen.add(key)
            out.append(compact)
    return out


def extract(raw_html: str, method: str) -> Extraction:
    soup = soup_from_html(raw_html)
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    remove_noise(soup)

    scored = sorted(((score_node(node), node) for node in candidates(soup)), key=lambda item: item[0], reverse=True)
    best_score, best = scored[0] if scored else (0.0, soup.body or soup)
    markdown = html_to_markdown(best)
    text = "\n\n".join(clean_lines(best.get_text("\n", strip=True)))
    confidence = min(0.99, max(0.05, best_score / 2500))
    return Extraction(
        title=title,
        text=text,
        markdown=markdown,
        confidence=round(confidence, 3),
        method=method,
        diagnostics={
            "candidate_count": len(scored),
            "best_score": round(best_score, 2),
            "best_node": node_label(best)[:160],
            "browser_rendered": method == "browser",
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="URL, local HTML path, or raw HTML string")
    parser.add_argument("--browser", action="store_true", help="render with Playwright/Chromium when available")
    parser.add_argument("--format", choices=["text", "markdown", "json"], default="text")
    parser.add_argument("--output", help="write result to this file")
    parser.add_argument("--timeout-ms", type=int, default=15000)
    args = parser.parse_args()

    raw, method = load_source(args.source, args.browser, args.timeout_ms)
    result = extract(raw, method)
    if args.format == "json":
        payload = json.dumps(result.__dict__, ensure_ascii=False, indent=2)
    elif args.format == "markdown":
        payload = result.markdown
    else:
        payload = result.text

    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
