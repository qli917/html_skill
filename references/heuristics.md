# HTML Main Content Heuristics

Use these rules when the default script needs adjustment or when manually extracting from difficult pages.

## Candidate Selection

Prefer candidates in this order:

1. `article`, `main`, `[role=main]`
2. Nodes with class/id containing `article`, `content`, `post`, `entry`, `main`, `story`, `detail`, `正文`, `内容`, `文章`
3. Large block containers such as `section`, `div`, `td` with paragraph-rich text
4. Readability output when available

Avoid candidates with class/id containing `nav`, `menu`, `footer`, `header`, `sidebar`, `aside`, `comment`, `reply`, `share`, `social`, `recommend`, `related`, `advert`, `ad-`, `promo`, `cookie`, `login`, `subscribe`.

## Scoring

Reward:

- Long visible text with paragraph breaks
- High punctuation density, including Chinese punctuation
- Multiple sibling paragraphs/lists/headings
- Low link text ratio
- Nearby title or h1/h2 matching page title
- Semantic tags such as `article` and `main`

Penalize:

- High link density
- Many short repeated lines
- Forms, buttons, inputs, menus, breadcrumbs
- Copyright/legal/footer strings
- “related/recommended/latest/hot/search/login/share/comment” markers
- Hidden nodes or nodes positioned off-screen

## Cleanup

Remove these before final text conversion:

- `script`, `style`, `noscript`, `template`, `svg`, `canvas`, `iframe`
- `nav`, `header`, `footer`, `aside`, `form`, `button`, `input`, `select`, `textarea`
- Cookie banners, modal overlays, share bars, comment areas, related-article blocks
- Elements hidden by `display:none`, `visibility:hidden`, `aria-hidden=true`, or `[hidden]`

Preserve:

- Headings that belong to the content block
- Paragraphs, lists, blockquotes, pre/code, tables
- Image alt text when it carries article content

## Chrome/Playwright Notes

Use browser rendering when:

- The raw HTML has little正文 but the rendered page has it
- The page uses `#__next`, `#root`, `app`, or obvious SPA scaffolding
- The user gives a URL rather than saved HTML
- Lazy loading is likely

After load, scroll down and back up once. Then extract from the DOM. Avoid screenshots/OCR unless the text is actually rendered as an image.
