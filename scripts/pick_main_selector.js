// Disabled: Chrome DevTools manual selector picking is no longer used.
/*
(() => {
  const style = document.createElement("style");
  style.textContent = `
    .codex-selector-hover { outline: 3px solid #0ea5e9 !important; cursor: crosshair !important; }
    .codex-selector-picked { outline: 4px solid #22c55e !important; }
  `;
  document.documentElement.appendChild(style);

  const cssEscape = (value) => {
    if (window.CSS && CSS.escape) return CSS.escape(value);
    return String(value).replace(/[^a-zA-Z0-9_-]/g, "\\$&");
  };

  const unique = (selector) => document.querySelectorAll(selector).length === 1;

  const selectorFor = (el) => {
    if (el.id && unique(`#${cssEscape(el.id)}`)) return `#${cssEscape(el.id)}`;
    const parts = [];
    let node = el;
    while (node && node.nodeType === Node.ELEMENT_NODE && node !== document.documentElement) {
      let part = node.tagName.toLowerCase();
      const classes = [...node.classList]
        .filter((name) => !name.startsWith("codex-selector-"))
        .slice(0, 3);
      if (classes.length) part += "." + classes.map(cssEscape).join(".");
      const candidate = [part, ...parts].join(" > ");
      if (unique(candidate)) return candidate;
      const siblings = [...node.parentElement.children].filter((child) => child.tagName === node.tagName);
      if (siblings.length > 1) part += `:nth-of-type(${siblings.indexOf(node) + 1})`;
      parts.unshift(part);
      node = node.parentElement;
    }
    return parts.join(" > ");
  };

  let hover;
  const cleanup = () => {
    document.removeEventListener("mouseover", onMouseOver, true);
    document.removeEventListener("mouseout", onMouseOut, true);
    document.removeEventListener("click", onClick, true);
    if (hover) hover.classList.remove("codex-selector-hover");
  };
  const onMouseOver = (event) => {
    if (hover) hover.classList.remove("codex-selector-hover");
    hover = event.target;
    hover.classList.add("codex-selector-hover");
  };
  const onMouseOut = (event) => {
    event.target.classList.remove("codex-selector-hover");
  };
  const onClick = async (event) => {
    event.preventDefault();
    event.stopPropagation();
    cleanup();
    const selector = selectorFor(event.target);
    event.target.classList.add("codex-selector-picked");
    const payload = {
      kind: "url",
      netloc: location.hostname,
      path_prefix: location.pathname.replace(/[^/]+$/, ""),
      selector,
      sample_url: location.href,
      created_at: new Date().toISOString(),
    };
    const text = JSON.stringify(payload, null, 2);
    try {
      await navigator.clipboard.writeText(text);
      console.log("Copied selector JSON to clipboard:", payload);
    } catch {
      console.log("Selector JSON:", text);
    }
    const blob = new Blob([text + "\n"], { type: "application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "html-main-selector.json";
    link.click();
  };

  document.addEventListener("mouseover", onMouseOver, true);
  document.addEventListener("mouseout", onMouseOut, true);
  document.addEventListener("click", onClick, true);
  console.log("正文选择器已启动：点击正文最外层节点，selector JSON 会复制到剪贴板并下载。");
})();
*/
