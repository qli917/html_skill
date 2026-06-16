# Extract HTML Main

![license](https://img.shields.io/badge/license-MIT-green)
![python](https://img.shields.io/badge/python-3.10%2B-blue)

Extract readable main content from messy HTML, local files, and URLs.

一个用于从杂乱 HTML、本地网页文件和 URL 中提取正文内容的工具，适合 AI 摘要、RAG、网页清洗和 Agent 数据预处理。

---

## 中文

### 项目简介

`Extract HTML Main` 用来从杂乱网页中提取真正的正文内容。

很多网页里，真正有价值的信息只占一小部分，剩下大量内容往往是导航栏、广告、评论区、相关推荐、分享按钮、登录提示、Footer 和各种页面模板噪声。

如果直接把整页 HTML 丢给 AI 摘要、RAG 或 Agent，通常会浪费 token、降低摘要质量、污染检索结果，并干扰后续自动化处理。

这个工具的目标就是：**尽量只保留正文，尽量去掉噪声。**

### 适用场景

- AI 摘要前的数据清洗
- RAG 知识库网页正文提取
- 爬虫采集后的正文清洗
- 批量网页转 Markdown
- AI Agent 处理网页内容前的预处理

### 功能特性

- 支持 raw HTML、本地 HTML 文件、URL
- 支持 Playwright / Chromium 动态页面渲染
- 浏览器不可用时自动退回静态 HTTP 抓取
- 支持手动指定 CSS selector
- 支持 selector 缓存
- 支持输出 `text` / `markdown` / `json`
- 支持生成原 HTML 和提取结果的对比页

### 安装

最小安装：

```bash
bash install.sh
```

如果你要处理动态网页，推荐安装浏览器渲染能力：

```bash
bash install.sh --with-browser
```

### 快速开始

```bash
python3 scripts/extract_html_main.py examples/messy_article.html --format markdown
```

### 示例 1：从本地 HTML 提取正文

```bash
python3 scripts/extract_html_main.py input.html --format markdown
```

作用：输入一个本地 HTML 文件，输出清洗后的 Markdown 正文。

### 示例 2：从 URL 提取正文并输出 JSON

```bash
python3 scripts/extract_html_main.py https://example.com/article --format json
```

作用：从网页地址提取正文，输出正文内容和诊断信息，适合调试或接入自动化流程。

如果你已经知道正文容器，也可以手动指定 selector：

```bash
python3 scripts/extract_html_main.py https://example.com/article --selector ".article-body" --format markdown
```

### 思维流程图

下面是正文提取的核心思路流程图：

```mermaid
flowchart TD
    A[输入 source] --> B{输入类型}
    B -->|URL| C[优先尝试 Playwright 渲染]
    B -->|本地 HTML / raw HTML| D[直接静态解析]

    C --> E{浏览器渲染成功?}
    E -->|是| F[获取渲染后的完整 DOM]
    E -->|否| G[退回静态 HTTP 抓取]

    D --> H[生成 BeautifulSoup DOM]
    G --> H
    F --> H

    H --> I[移除明显噪声节点]
    I --> I1[script/style/nav/header/footer/aside/form]
    I --> I2[hidden/display:none/aria-hidden]
    I --> I3[广告/评论/分享/相关推荐/登录提示]

    I --> J[生成候选正文节点]
    J --> J1[article]
    J --> J2[main]
    J --> J3[role=main]
    J --> J4[content-like class/id]
    J --> J5[大块 div/section/body 节点]

    J --> K[候选节点打分]
    K --> K1[文本长度]
    K --> K2[段落数量]
    K --> K3[标点密度]
    K --> K4[语义标签奖励]
    K --> K5[链接密度惩罚]
    K --> K6[噪声命名惩罚]

    K --> L{是否提供 selector}
    L -->|是且命中| M[直接使用 selector 节点]
    L -->|否| N[选择最高分节点]

    M --> O[清理重复文本和空白]
    N --> O

    O --> P{输出格式}
    P -->|text| Q[纯文本]
    P -->|markdown| R[Markdown]
    P -->|json| S[正文 + 诊断信息]
```

### 常用命令

提取本地 HTML：

```bash
python3 scripts/extract_html_main.py input.html --format markdown
```

提取 URL：

```bash
python3 scripts/extract_html_main.py https://example.com/article --format markdown
```

输出 JSON：

```bash
python3 scripts/extract_html_main.py https://example.com/article --format json
```

写入文件：

```bash
python3 scripts/extract_html_main.py input.html --format markdown --output body.md
```

生成对比页：

```bash
python3 scripts/make_html_compare.py input.html \
  --selector ".article-body" \
  --output compare.html
```

### 主要文件

- `SKILL.md`：Codex skill 指令和工作流
- `scripts/extract_html_main.py`：正文提取主程序
- `scripts/make_html_compare.py`：原 HTML 与提取结果对比页生成器
- `scripts/smoke_test.sh`：本地冒烟测试
- `examples/`：示例 HTML
- `references/heuristics.md`：候选节点评分与清理规则
- `docs/RELEASE_CHECKLIST.md`：发布前检查清单

### 开发检查

```bash
bash scripts/smoke_test.sh
```

或手动运行：

```bash
python3 -m py_compile scripts/extract_html_main.py scripts/make_html_compare.py
python3 scripts/extract_html_main.py examples/messy_article.html --format markdown
```

---

## English

### Overview

`Extract HTML Main` extracts readable main content from messy HTML pages.

In many web pages, the actual article body is only a small part of the DOM. The rest is often noise, such as navigation bars, ads, comments, related links, share widgets, login prompts, footers, and repeated layout templates.

If you pass full-page HTML directly into AI summarization, RAG pipelines, or agents, it often wastes tokens, lowers summary quality, pollutes retrieval results, and adds noise to downstream automation.

This tool aims to **keep the main content and remove as much noise as possible**.

### Use Cases

- Pre-cleaning pages before AI summarization
- Extracting article text for RAG ingestion
- Cleaning HTML after web scraping
- Converting saved pages to Markdown
- Preprocessing webpage content for AI agents

### Features

- Supports raw HTML, local HTML files, and URLs
- Supports Playwright / Chromium rendering for dynamic pages
- Falls back to static HTTP fetching when browser rendering is unavailable
- Supports manual CSS selectors
- Supports selector cache
- Supports `text` / `markdown` / `json` output
- Supports generating original-vs-extracted HTML comparison pages

### Installation

Minimal install:

```bash
bash install.sh
```

For dynamic pages, install browser rendering support:

```bash
bash install.sh --with-browser
```

### Quick Start

```bash
python3 scripts/extract_html_main.py examples/messy_article.html --format markdown
```

### Example 1: Extract main content from a local HTML file

```bash
python3 scripts/extract_html_main.py input.html --format markdown
```

What it does: reads a local HTML file, extracts the readable main content, and outputs cleaned Markdown.

### Example 2: Extract main content from a URL and output JSON

```bash
python3 scripts/extract_html_main.py https://example.com/article --format json
```

What it does: fetches a web page, extracts the readable article body, and returns content plus diagnostics.

If you already know the content container, you can also specify a selector:

```bash
python3 scripts/extract_html_main.py https://example.com/article --selector ".article-body" --format markdown
```

### Thought Process Flowchart

Here is the core extraction logic:

```mermaid
flowchart TD
    A[Input source] --> B{Input type}
    B -->|URL| C[Try Playwright rendering first]
    B -->|Local HTML / raw HTML| D[Parse statically]

    C --> E{Browser rendering succeeded?}
    E -->|Yes| F[Use rendered DOM]
    E -->|No| G[Fallback to static HTTP fetch]

    D --> H[Build BeautifulSoup DOM]
    G --> H
    F --> H

    H --> I[Remove obvious noise]
    I --> I1[script/style/nav/header/footer/aside/form]
    I --> I2[hidden/display:none/aria-hidden]
    I --> I3[ads/comments/share/related/login prompts]

    I --> J[Build candidate content nodes]
    J --> J1[article]
    J --> J2[main]
    J --> J3[role=main]
    J --> J4[content-like class/id]
    J --> J5[large div/section/body nodes]

    J --> K[Score candidates]
    K --> K1[text length]
    K --> K2[paragraph count]
    K --> K3[punctuation density]
    K --> K4[semantic tag bonus]
    K --> K5[link density penalty]
    K --> K6[noisy naming penalty]

    K --> L{Selector provided?}
    L -->|Yes and matched| M[Use selector node]
    L -->|No| N[Pick highest-scoring node]

    M --> O[Deduplicate and normalize whitespace]
    N --> O

    O --> P{Output format}
    P -->|text| Q[Plain text]
    P -->|markdown| R[Markdown]
    P -->|json| S[Content + diagnostics]
```

### Common Commands

Extract from local HTML:

```bash
python3 scripts/extract_html_main.py input.html --format markdown
```

Extract from URL:

```bash
python3 scripts/extract_html_main.py https://example.com/article --format markdown
```

Output JSON:

```bash
python3 scripts/extract_html_main.py https://example.com/article --format json
```

Write result to a file:

```bash
python3 scripts/extract_html_main.py input.html --format markdown --output body.md
```

Generate comparison page:

```bash
python3 scripts/make_html_compare.py input.html \
  --selector ".article-body" \
  --output compare.html
```

### Main Files

- `SKILL.md`: Codex skill instructions and workflow
- `scripts/extract_html_main.py`: main extraction CLI
- `scripts/make_html_compare.py`: comparison page generator
- `scripts/smoke_test.sh`: local smoke test
- `examples/`: sample HTML files
- `references/heuristics.md`: scoring and cleanup rules
- `docs/RELEASE_CHECKLIST.md`: pre-release checklist

### Development Check

```bash
bash scripts/smoke_test.sh
```

Or run manually:

```bash
python3 -m py_compile scripts/extract_html_main.py scripts/make_html_compare.py
python3 scripts/extract_html_main.py examples/messy_article.html --format markdown
```

## License

MIT License. See `LICENSE`.
