# Extract HTML Main

![smoke](https://github.com/qli917/html_skill/actions/workflows/smoke.yml/badge.svg)
![license](https://img.shields.io/badge/license-MIT-green)
![python](https://img.shields.io/badge/python-3.10%2B-blue)

<p>
  <a href="#中文">中文</a>
  |
  <a href="#english">English</a>
</p>

## 中文

**Extract HTML Main 是一个给 AI Agent、RAG、网页摘要和爬虫清洗用的 HTML 正文提取工具。**

它可以从杂乱 HTML、本地保存网页和 URL 中提取读者真正要看的正文，尽量去掉导航、广告、评论、分享栏、相关推荐、登录弹窗、footer 等页面噪声，输出纯文本、Markdown 或 JSON 诊断结果。

### 适合什么场景

- AI 摘要前的数据清洗
- RAG 知识库网页正文提取
- 爬虫采集后的正文清洗
- Codex / AI Agent 自动处理网页内容
- 批量网页转 Markdown
- 快速判断一个页面的正文 selector

### 30 秒快速体验

```bash
bash install.sh
python3 scripts/extract_html_main.py examples/messy_article.html --format markdown
```

预期结果：输出只保留文章标题、段落、列表和引用；导航、广告、评论和 footer 会被剔除。

从 URL 提取：

```bash
python3 scripts/extract_html_main.py https://example.com/article --format markdown
```

动态页面推荐安装 Chromium 渲染能力：

```bash
bash install.sh --with-browser
```

### 功能

- 支持 raw HTML、本地 HTML 文件和 URL。
- URL 默认优先使用 Playwright/Chromium 渲染，失败后自动退回静态 HTTP 抓取。
- 支持手动指定 CSS selector，适合正文容器已知的网站。
- 支持按域名或路径缓存可复用 selector。
- 支持输出 `text`、`markdown`、`json`。
- 支持生成浏览器可打开的“原 HTML vs 提取正文 HTML”对比页。
- 保留段落、标题、列表、引用、代码、表格和有意义图片 alt。

### 安装

最小安装：

```bash
bash install.sh
```

等价于：

```bash
python3 -m pip install beautifulsoup4
```

安装 URL 动态渲染能力：

```bash
bash install.sh --with-browser
```

等价于：

```bash
python3 -m pip install beautifulsoup4 playwright
python3 -m playwright install chromium
```

如果 Playwright 或 Chromium 不可用，URL 抽取会自动退回静态 HTTP 抓取。

### 常用命令

从本地 HTML 提取 Markdown：

```bash
python3 scripts/extract_html_main.py input.html --format markdown
```

从 URL 提取 JSON 诊断信息：

```bash
python3 scripts/extract_html_main.py https://example.com/article --format json
```

强制使用静态 URL 抓取：

```bash
python3 scripts/extract_html_main.py https://example.com/article --no-browser --format markdown
```

使用已知正文 selector：

```bash
python3 scripts/extract_html_main.py input.html --selector ".article-body" --format markdown
```

写入输出文件：

```bash
python3 scripts/extract_html_main.py input.html --format markdown --output body.md
```

### Selector 缓存

默认 selector 缓存路径：

```text
~/.codex/html_main_selectors.json
```

为 URL 路径保存 selector：

```bash
python3 scripts/extract_html_main.py "https://example.com/news/123" \
  --selector ".article-body" \
  --save-selector \
  --format markdown
```

为同站点批量页面保存域名级 class selector：

```bash
python3 scripts/extract_html_main.py "https://example.com/news/123" \
  --selector ".article-body" \
  --save-domain-class \
  --format markdown
```

之后处理同域名页面时可以省略 `--selector`；命中缓存规则后脚本会自动使用。

### 对比原 HTML 和正文 HTML

生成浏览器可打开的对比页：

```bash
python3 scripts/make_html_compare.py input.html \
  --selector ".article-body" \
  --output compare.html
```

用 Chrome 打开 `compare.html`。左侧显示原始 HTML，右侧显示清理后的正文 HTML。

### 工作原理

第一性原理：网页正文通常有更高的信息密度，而噪声区通常链接密度高、文本短、class/id 命名偏导航、评论、广告或推荐。

本工具会：

1. 获取尽量完整的 DOM。URL 会优先尝试 Playwright 渲染。
2. 移除明显噪声节点，例如 `script`、`style`、`nav`、`header`、`footer`、`aside`、`form`、隐藏节点、广告、评论和分享区域。
3. 从 `article`、`main`、`[role=main]`、正文命名节点和大块布局节点中生成候选正文容器。
4. 根据文本长度、段落数量、标点密度、语义标签、链接密度和噪声命名打分。
5. 选择最高分节点，清理重复文本和空白，再输出目标格式。

### 示例文件

查看 `examples/`：

```bash
python3 scripts/extract_html_main.py examples/messy_article.html --format markdown
python3 scripts/make_html_compare.py examples/messy_article.html --selector "article.article-body" --output compare.html
```

### 主要文件

- `SKILL.md`：Codex skill 指令和工作流。
- `scripts/extract_html_main.py`：主提取命令行工具。
- `scripts/make_html_compare.py`：原 HTML 与正文 HTML 对比页生成器。
- `examples/`：可直接运行的杂乱 HTML 样例。
- `references/heuristics.md`：候选节点评分与清理规则。
- `docs/PROMOTION.md`：推广文案、发布渠道和 GitHub 仓库设置建议。

### 开发检查

运行语法检查：

```bash
python3 -m py_compile scripts/extract_html_main.py scripts/make_html_compare.py
```

运行一个最小抽取冒烟测试：

```bash
python3 scripts/extract_html_main.py '<html><body><nav>Home</nav><article><p>Main text, with punctuation.</p></article></body></html>' --format markdown
```

### 局限

- 付费墙、图片化正文、canvas 渲染正文、需要登录的页面可能无法直接提取。
- 完全不符合常规 DOM 结构的页面，可能需要手动传入 `--selector`。
- 本工具优先解决“高性价比正文抽取”，不是完整浏览器自动化框架。

### 许可证

MIT License，见 `LICENSE`。

## English

**Extract HTML Main is a Python utility and Codex skill for extracting readable main content from messy HTML, saved pages, and URLs.**

It is designed for AI agents, RAG pipelines, web summarization, and scraping cleanup. It removes navigation, sidebars, ads, comments, share widgets, related links, login prompts, footers, and other page chrome before returning plain text, Markdown, or JSON diagnostics.

### Use Cases

- Clean web pages before AI summarization
- Extract readable content for RAG ingestion
- Post-process scraped HTML
- Let Codex / AI agents work with article content instead of full page noise
- Convert batches of pages into Markdown
- Quickly validate a known main-content selector

### 30-second Demo

```bash
bash install.sh
python3 scripts/extract_html_main.py examples/messy_article.html --format markdown
```

Expected result: the output keeps the article title, paragraphs, lists, and quotes while dropping nav, ads, comments, and footers.

Extract from a URL:

```bash
python3 scripts/extract_html_main.py https://example.com/article --format markdown
```

Install browser rendering for dynamic pages:

```bash
bash install.sh --with-browser
```

### Features

- Accepts raw HTML, local HTML files, and URLs.
- Uses Playwright/Chromium first for URLs, then falls back to static HTTP fetching.
- Supports manual CSS selectors when a site has a known content container.
- Caches reusable selectors by domain or path.
- Outputs `text`, `markdown`, or `json`.
- Generates browser-openable comparison pages for original HTML vs extracted HTML.
- Preserves paragraphs, headings, lists, quotes, code blocks, tables, and useful image alt text.

### Installation

Minimal install:

```bash
bash install.sh
```

Equivalent to:

```bash
python3 -m pip install beautifulsoup4
```

Install dynamic URL rendering support:

```bash
bash install.sh --with-browser
```

Equivalent to:

```bash
python3 -m pip install beautifulsoup4 playwright
python3 -m playwright install chromium
```

If Playwright or Chromium is unavailable, URL extraction automatically falls back to static HTTP fetching.

### Common Commands

Extract Markdown from a local HTML file:

```bash
python3 scripts/extract_html_main.py input.html --format markdown
```

Extract JSON diagnostics from a URL:

```bash
python3 scripts/extract_html_main.py https://example.com/article --format json
```

Force static URL fetching:

```bash
python3 scripts/extract_html_main.py https://example.com/article --no-browser --format markdown
```

Use a known main-content selector:

```bash
python3 scripts/extract_html_main.py input.html --selector ".article-body" --format markdown
```

Write output to a file:

```bash
python3 scripts/extract_html_main.py input.html --format markdown --output body.md
```

### Selector Cache

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

### Compare Original And Extracted HTML

Generate a browser-openable comparison page:

```bash
python3 scripts/make_html_compare.py input.html \
  --selector ".article-body" \
  --output compare.html
```

Open `compare.html` in Chrome. The left pane shows the original HTML, and the right pane shows the cleaned main-content HTML.

### How It Works

First principle: main content usually has higher information density, while page noise usually has high link density, short text, and nav/comment/ad/related naming patterns.

The extractor:

1. Loads the most complete DOM it can get. URLs try Playwright rendering first.
2. Removes obvious noise nodes such as `script`, `style`, `nav`, `header`, `footer`, `aside`, `form`, hidden nodes, ads, comments, and share widgets.
3. Builds candidates from `article`, `main`, `[role=main]`, content-like nodes, and large layout nodes.
4. Scores candidates by text length, paragraph count, punctuation density, semantic tags, link density, and noisy names.
5. Picks the best node, deduplicates text, normalizes whitespace, and outputs the requested format.

### Examples

See `examples/`:

```bash
python3 scripts/extract_html_main.py examples/messy_article.html --format markdown
python3 scripts/make_html_compare.py examples/messy_article.html --selector "article.article-body" --output compare.html
```

### Main Files

- `SKILL.md`: Codex skill instructions and workflow.
- `scripts/extract_html_main.py`: Main extraction CLI.
- `scripts/make_html_compare.py`: Original-vs-extracted HTML comparison page generator.
- `examples/`: Runnable messy HTML samples.
- `references/heuristics.md`: Candidate scoring and cleanup rules.
- `docs/PROMOTION.md`: Promotion copy, launch channels, and GitHub repository setting suggestions.

### Development Checks

Run a syntax check:

```bash
python3 -m py_compile scripts/extract_html_main.py scripts/make_html_compare.py
```

Run a tiny extraction smoke test:

```bash
python3 scripts/extract_html_main.py '<html><body><nav>Home</nav><article><p>Main text, with punctuation.</p></article></body></html>' --format markdown
```

### Limits

- Paywalls, image-only articles, canvas-rendered content, and login-only pages may need custom handling.
- Highly unusual DOM structures may require `--selector`.
- This project focuses on practical, high-signal content extraction rather than full browser automation.

### License

MIT License. See `LICENSE`.
