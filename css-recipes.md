# 配方原文（可直接粘贴）

不想跑脚本，就把下面任意几段直接粘进
**DSH 设置 → 侧边卡片 → 自定义 CSS**，效果和有按钮时完全一样。

顺序无所谓，四块互不冲突，可以只挑其中一两块。

---

## 1. 侧栏顶部紧凑

省 **约 60px**。

```css
/* 顶部品牌行：去掉 logo，只留标题 */
[data-slot="sidebar.brand.mark"] { display: none !important; }
:where([class*="_logoRow"]) {
  height: 40px !important;
  margin-bottom: 0 !important;
  padding-top: 2px !important;
}
/* 新会话按钮（排除内部 label/mask 子节点，避免误伤） */
[class*="_newSession"]:not([class*="Label"]):not([class*="Content"]):not([class*="Shortcut"]) {
  height: 30px !important;
  margin: 0 2px 6px !important;
  font-size: 12px !important;
}
/* 任务 / 频道 分段页签 */
.ima-tabs-wrap { margin-top: 0 !important; margin-bottom: 4px !important; }
.ima-tabs-wrap .ima-segmented-tabs {
  height: 26px !important;
  min-height: 26px !important;
  max-height: 26px !important;
}
.ima-tabs-wrap .ima-segmented-tabs [role="tab"] {
  height: 22px !important;
  font-size: 12px !important;
}
```

---

## 2. 面板行只留图标

省 **约 130px** —— 最有效的一块。

把「插件 / IM助理 / 自动化任务 / 上下文洞察」从四行竖排压成一行图标条。
悬停或当前选中时，文字才展开。

```css
nav:has(> button > span > [data-slot="sidebar.panellist"]) {
  flex-direction: row !important;
  flex-wrap: wrap !important;
  align-content: flex-start !important;
  gap: 2px !important;
  margin-bottom: 6px !important;
}
nav:has(> button > span > [data-slot="sidebar.panellist"]) > button {
  min-height: 26px !important;
  height: 26px !important;
  padding: 0 6px !important;
  margin: 0 !important;
  gap: 0 !important;
  font-size: 12px !important;
  line-height: 16px !important;
}
nav:has(> button > span > [data-slot="sidebar.panellist"]) > button > span:last-child:not(:first-child) {
  display: none !important;
}
nav:has(> button > span > [data-slot="sidebar.panellist"]) > button:hover > span:last-child:not(:first-child),
nav:has(> button > span > [data-slot="sidebar.panellist"]) > button[aria-current="page"] > span:last-child:not(:first-child) {
  display: inline !important;
  margin-left: 6px !important;
}
nav:has(> button > span > [data-slot="sidebar.panellist"]) > button > span:first-child svg {
  width: 14px !important;
  height: 14px !important;
}
```

---

## 3. 费用区悬停展开

省 **约 141px**（静止时），鼠标移上去自动还原。

余额 / 套餐 / 峰谷 / 今日花费默认只留「余额」一行。

```css
[data-slot="sidebar.footer.action"] > div { font-size: 11px !important; }
[data-slot="sidebar.footer.action"] > div > * { display: none !important; }
[data-slot="sidebar.footer.action"] > div > *:first-child {
  display: flex !important;
  height: 22px !important;
}
[data-slot="sidebar.footer.action"] > div:hover > * { display: revert !important; }
```

---

## 4. 工作区行更紧凑

不省固定高度，但每行从 34px 变 26px —— 同样一屏能多塞四到五行。

```css
[data-slot="sidebar.workspaces"] [role="treeitem"] {
  min-height: 26px !important;
  height: 26px !important;
  font-size: 12px !important;
  line-height: 18px !important;
}
[data-slot="sidebar.workspaces"] [role="treeitem"] svg {
  width: 14px !important;
  height: 14px !important;
}
[data-slot="sidebar.workspaces"] {
  font-size: 12px !important;
}
```

---

## 四项全开的效果

| | 改前 | 改后 |
|---|---|---|
| 面板行 | 156px | 26px |
| 页签 | 32px | 26px |
| 品牌行 + 新会话 | 98px | 70px |
| 费用区 | 163px | 22px |
| **工作区可视高度** | **311px** | **634px** |

1440×900 窗口实测。

---

## 想微调？

直接改数值就行。比如觉得面板行 26px 太挤，改成 30px：

```css
nav:has(> button > span > [data-slot="sidebar.panellist"]) > button {
  min-height: 30px !important;
  height: 30px !important;
}
```

想彻底去掉某一项，把对应整段删掉即可 —— 它们互不依赖。
