#!/usr/bin/env python3
"""Extract readable main content from a URL or local HTML file."""

from __future__ import annotations

import argparse
import fnmatch
import html
import json
import re
import sys
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse


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
    if not getattr(node, "attrs", None):
        return getattr(node, "name", "") or ""
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
        if not getattr(tag, "attrs", None):
            continue
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


def extract(raw_html: str, method: str, selector: str | None = None) -> Extraction:
    raw_html = unwrap_embedded_article_html(raw_html)
    soup = soup_from_html(raw_html)
    title = soup.title.get_text(" ", strip=True) if soup.title else ""

    selector_found = False
    if selector:
        best = soup.select_one(selector)
        if best is not None:
            selector_found = True
            remove_noise(best)
            best_score = score_node(best)
            scored = [(best_score, best)]
        else:
            remove_noise(soup)
            scored = sorted(((score_node(node), node) for node in candidates(soup)), key=lambda item: item[0], reverse=True)
            best_score, best = scored[0] if scored else (0.0, soup.body or soup)
    else:
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
            "selector": selector,
            "selector_found": selector_found,
        },
    )


def unwrap_embedded_article_html(raw_html: str) -> str:
    match = re.search(r"window\.DATA\s*=\s*(\{.*?\});\s*</script>", raw_html, re.S)
    if not match:
        return raw_html
    try:
        data = json.loads(match.group(1))
    except Exception:
        return raw_html
    origin = data.get("originContent") or {}
    text = origin.get("text")
    if isinstance(text, str) and len(text) > 100:
        return text
    return raw_html


def default_selector_cache_path() -> Path:
    return Path.home() / ".codex" / "html_main_selectors.json"


def source_rule_fields(source: str) -> dict:
    parsed = urlparse(source)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return {
            "kind": "url",
            "netloc": parsed.netloc.lower(),
            "path": parsed.path or "/",
            "pattern": f"{parsed.netloc.lower()}{parsed.path or '/'}",
        }
    path = Path(source)
    return {
        "kind": "file",
        "netloc": "",
        "path": str(path),
        "pattern": str(path),
    }


def load_selector_cache(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "rules": []}
    return json.loads(path.read_text(encoding="utf-8"))


def write_selector_cache(path: Path, cache: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def selector_rule_matches(rule: dict, source: str) -> bool:
    fields = source_rule_fields(source)
    if rule.get("kind") and rule.get("kind") != fields["kind"]:
        return False
    if fields["kind"] == "url":
        netloc = (rule.get("netloc") or "").lower()
        if netloc and netloc != fields["netloc"]:
            return False
        if rule.get("scope") == "domain_class":
            return bool(rule.get("class_selector") or rule.get("selector"))
        path_prefix = rule.get("path_prefix")
        if path_prefix and not fields["path"].startswith(path_prefix):
            return False
        pattern = rule.get("pattern")
        if pattern and not fnmatch.fnmatch(fields["pattern"], pattern):
            return False
        return bool(netloc or path_prefix or pattern)
    pattern = rule.get("pattern")
    return bool(pattern and fnmatch.fnmatch(fields["path"], pattern))


def find_cached_selector(source: str, cache: dict) -> tuple[str | None, dict | None]:
    matches = [rule for rule in cache.get("rules", []) if selector_rule_matches(rule, source)]
    if not matches:
        return None, None
    matches.sort(
        key=lambda rule: (
            1 if rule.get("scope") == "domain_class" else 0,
            len(rule.get("path_prefix") or rule.get("pattern") or ""),
        ),
        reverse=True,
    )
    selector = matches[0].get("class_selector") or matches[0].get("selector")
    return selector, matches[0]


def save_selector_rule(source: str, selector: str, cache_path: Path, pattern: str | None = None) -> None:
    cache = load_selector_cache(cache_path)
    fields = source_rule_fields(source)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    if fields["kind"] == "url":
        rule = {
            "kind": "url",
            "netloc": fields["netloc"],
            "path_prefix": pattern or path_prefix_for(fields["path"]),
            "selector": selector,
            "created_at": now,
        }
    else:
        rule = {
            "kind": "file",
            "pattern": pattern or fields["path"],
            "selector": selector,
            "created_at": now,
        }

    rules = cache.setdefault("rules", [])
    rules[:] = [
        item
        for item in rules
        if not (
            item.get("kind") == rule.get("kind")
            and item.get("netloc") == rule.get("netloc")
            and item.get("path_prefix") == rule.get("path_prefix")
            and item.get("pattern") == rule.get("pattern")
        )
    ]
    rules.append(rule)
    write_selector_cache(cache_path, cache)


def selector_classes(selector: str) -> list[str]:
    return [match.group(1).replace("\\.", ".") for match in re.finditer(r"\.([_a-zA-Z][-_a-zA-Z0-9]*)", selector)]


def class_selector_from_selector(selector: str) -> str:
    classes = selector_classes(selector)
    if not classes:
        return selector
    return "." + ".".join(classes)


def save_domain_class_rule(source: str, selector: str, cache_path: Path) -> None:
    cache = load_selector_cache(cache_path)
    fields = source_rule_fields(source)
    if fields["kind"] != "url":
        save_selector_rule(source, selector, cache_path)
        return

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    rule = {
        "kind": "url",
        "scope": "domain_class",
        "netloc": fields["netloc"],
        "selector": selector,
        "class_selector": class_selector_from_selector(selector),
        "classes": selector_classes(selector),
        "created_at": now,
    }
    rules = cache.setdefault("rules", [])
    rules[:] = [
        item
        for item in rules
        if not (
            item.get("kind") == "url"
            and item.get("scope") == "domain_class"
            and item.get("netloc") == fields["netloc"]
        )
    ]
    rules.append(rule)
    write_selector_cache(cache_path, cache)


def path_prefix_for(path: str) -> str:
    if not path or path == "/":
        return "/"
    parts = [part for part in path.split("/") if part]
    if len(parts) <= 1:
        return "/"
    return "/" + "/".join(parts[:-1]) + "/"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="URL, local HTML path, or raw HTML string")
    parser.add_argument("--browser", action="store_true", help="render with Playwright/Chromium when available")
    parser.add_argument("--format", choices=["text", "markdown", "json"], default="text")
    parser.add_argument("--output", help="write result to this file")
    parser.add_argument("--timeout-ms", type=int, default=15000)
    parser.add_argument("--selector", help="CSS selector for the main content node")
    parser.add_argument(
        "--selector-cache",
        default=str(default_selector_cache_path()),
        help="JSON cache for reusable CSS selectors",
    )
    parser.add_argument(
        "--save-selector",
        action="store_true",
        help="save --selector into --selector-cache for this source before extraction",
    )
    parser.add_argument(
        "--save-domain-class",
        action="store_true",
        help="save --selector as a domain-level class rule and reuse it for the same domain",
    )
    parser.add_argument(
        "--selector-pattern",
        help="override cached rule pattern/path prefix, for example /rain/a/ or news.qq.com/rain/a/*",
    )
    args = parser.parse_args()

    selector_cache = Path(args.selector_cache).expanduser()
    if (args.save_selector or args.save_domain_class) and not args.selector:
        raise SystemExit("--save-selector/--save-domain-class requires --selector")
    if args.save_domain_class:
        save_domain_class_rule(args.source, args.selector, selector_cache)
    elif args.save_selector:
        save_selector_rule(args.source, args.selector, selector_cache, args.selector_pattern)

    selector = args.selector
    cached_rule = None
    if not selector:
        cache = load_selector_cache(selector_cache)
        selector, cached_rule = find_cached_selector(args.source, cache)

    raw, method = load_source(args.source, args.browser, args.timeout_ms)
    result = extract(raw, method, selector=selector)
    if cached_rule:
        result.diagnostics["selector_rule"] = cached_rule
        result.method += "+selector-cache"
    elif selector:
        result.method += "+selector"

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
