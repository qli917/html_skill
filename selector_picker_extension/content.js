(() => {
  if (window.__codexContextSelectorPickerLoaded) return;
  window.__codexContextSelectorPickerLoaded = true;

  let lastContextTarget = null;

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
        .filter((name) => !name.startsWith("codex-picker-"))
        .slice(0, 3);
      if (classes.length) part += "." + classes.map(cssEscape).join(".");

      const candidate = [part, ...parts].join(" > ");
      if (unique(candidate)) return candidate;

      const sameTag = [...node.parentElement.children].filter((child) => child.tagName === node.tagName);
      if (sameTag.length > 1) part += `:nth-of-type(${sameTag.indexOf(node) + 1})`;
      parts.unshift(part);
      node = node.parentElement;
    }
    return parts.join(" > ");
  };

  const rootFor = (el) => {
    let best = el;
    let bestScore = -1;

    for (let node = el; node && node !== document.body; node = node.parentElement) {
      if (!node.matches || node.matches("html,body,nav,header,footer,aside")) continue;

      const textLen = (node.innerText || "").trim().length;
      const paragraphCount = node.querySelectorAll("p").length;
      const label = `${node.id || ""} ${node.className || ""} ${node.tagName}`.toLowerCase();
      let score = textLen + paragraphCount * 300;

      if (/article|content|main|rich_media|正文|内容/.test(label)) score += 3000;
      if (node.matches("article,main,[role='main']")) score += 2500;
      if (/comment|related|recommend|side|nav|footer|header/.test(label)) score -= 5000;

      if (textLen > 200 && paragraphCount >= 2 && score > bestScore) {
        best = node;
        bestScore = score;
      }
    }

    return best;
  };

  const saveTarget = async (target) => {
    const root = rootFor(target);
    const selector = selectorFor(root);
    const payload = {
      kind: "url",
      scope: "domain_class",
      netloc: location.hostname,
      path_prefix: location.pathname.replace(/[^/]+$/, ""),
      selector,
      class_selector: root.classList.length ? "." + [...root.classList].join(".") : selector,
      classes: [...root.classList],
      sample_url: location.href,
      created_at: new Date().toISOString()
    };

    const resp = await fetch("http://127.0.0.1:8765/save", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const text = await resp.text();
    if (!resp.ok) throw new Error(text);

    root.style.outline = "4px solid #22c55e";
    setTimeout(() => {
      root.style.outline = "";
    }, 2500);
    alert(`已保存正文 selector:\n${selector}`);
  };

  document.addEventListener("contextmenu", (event) => {
    lastContextTarget = event.target;
  }, true);

  chrome.runtime.onMessage.addListener((message) => {
    if (message?.type !== "save-main-selector") return;
    const target = lastContextTarget || document.elementFromPoint(window.innerWidth / 2, window.innerHeight / 2);
    saveTarget(target).catch((error) => {
      alert(`保存正文 selector 失败:\n${error.message || error}`);
    });
  });
})();
