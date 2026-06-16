// Disabled: Chrome/manual selector picking is no longer used.
/*
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "save-main-selector",
    title: "保存为正文 selector",
    contexts: ["all"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId !== "save-main-selector" || !tab?.id) return;
  chrome.tabs.sendMessage(tab.id, {type: "save-main-selector"});
});
*/
