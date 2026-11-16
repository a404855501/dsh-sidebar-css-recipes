#!/usr/bin/env node
/**
 * 给 dsh-better-sidebar 的「自定义 CSS」加一组可点选配方按钮。
 *
 * 为什么用脚本而不是直接改 node_modules：插件更新会覆盖 lib/client.js，
 * 这里做成幂等补丁（重复运行不叠加），更新插件后重跑一次即可恢复功能。
 *
 * 用法：
 *   node apply-css-presets.mjs            # 打补丁（幂等）
 *   node apply-css-presets.mjs --revert   # 还原本地安装的插件文件
 *   node apply-css-presets.mjs --check    # 只检查是否已打过
 */

import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';

/** 插件文件位置：desktop profile 下的 dsh-better-sidebar。 */
const TARGET = path.join(
  os.homedir(),
  '.dsh/profiles/desktop/node_modules/dsh-better-sidebar/lib/client.js'
);
/**
 * 备份放在原文件旁边，按插件实际版本命名 —— 换版本后再打补丁不会覆盖旧备份，
 * 也不会因为文件名写死而在升级后找不到。
 */
function backupPath() {
  let version = 'unknown';
  try {
    const pkg = JSON.parse(
      fs.readFileSync(path.join(path.dirname(TARGET), '..', 'package.json'), 'utf8')
    );
    if (typeof pkg.version === 'string' && pkg.version !== '') version = pkg.version;
  } catch {
    /* 读不到版本就用 unknown，备份仍然有效 */
  }
  return path.join(path.dirname(TARGET), `client.js.orig-${version}`);
}

const MARK = 'dsh-sidebar-preset:';

/** 四个配方的 CSS 正文。表结构与插入位置见 patchSource()。 */
const PRESET_SOURCE = String.raw`
		/**
		* Built-in custom-CSS presets: composable, marker-delimited fragments the
		* settings section appends into the user's own stylesheet. Each fragment
		* owns a marker block so a second click replaces its own block instead of
		* duplicating it, and the user's hand-written CSS is never touched. The
		* selectors anchor on data-slot attributes and :has() rather than on the
		* sidebar's hashed CSS-module class names, which change with every host
		* release.
		*/
		const CSS_PRESET_MARK_OPEN = (id) => ` + "`/* >>> dsh-sidebar-preset:${id} */`" + String.raw`;
		const CSS_PRESET_MARK_CLOSE = (id) => ` + "`/* <<< dsh-sidebar-preset:${id} */`" + String.raw`;
		const CSS_PRESETS = [
			{
				id: "sidebar-compact",
				label: "侧栏紧凑（推荐）",
				labelEn: "Compact sidebar (recommended)",
				title: "压缩顶部品牌行、新会话按钮与「任务 / 频道」分段页签，把高度让给会话列表",
				titleEn: "Tighten the brand row, the new-session button and the Tasks/Channels tabs so the session list gets the height",
				css: [
					"/* 顶部品牌行：去掉 logo，只留标题 */",
					'[data-slot="sidebar.brand.mark"] { display: none !important; }',
					":where([class*=\"_logoRow\"]) {",
					"  height: 40px !important;",
					"  margin-bottom: 0 !important;",
					"  padding-top: 2px !important;",
					"}",
					"/* 新会话按钮（排除内部 label/mask 子节点，避免误伤） */",
					'[class*="_newSession"]:not([class*="Label"]):not([class*="Content"]):not([class*="Shortcut"]) {',
					"  height: 30px !important;",
					"  margin: 0 2px 6px !important;",
					"  font-size: 12px !important;",
					"}",
					"/* 任务 / 频道 分段页签 */",
					".ima-tabs-wrap { margin-top: 0 !important; margin-bottom: 4px !important; }",
					".ima-tabs-wrap .ima-segmented-tabs {",
					"  height: 26px !important;",
					"  min-height: 26px !important;",
					"  max-height: 26px !important;",
					"}",
					'.ima-tabs-wrap .ima-segmented-tabs [role="tab"] {',
					"  height: 22px !important;",
					"  font-size: 12px !important;",
					"}"
				].join("\n")
			},
			{
				id: "panel-rail",
				label: "面板行只留图标",
				labelEn: "Panels as an icon strip",
				title: "把「插件 / IM助理 / 自动化任务 / 上下文洞察」从四行竖排压成一行图标条，悬停或选中才显示文字",
				titleEn: "Collapse the four stacked panel rows into one icon strip; the label appears on hover or when active",
				css: [
					'nav:has(> button > span > [data-slot="sidebar.panellist"]) {',
					"  flex-direction: row !important;",
					"  flex-wrap: wrap !important;",
					"  align-content: flex-start !important;",
					"  gap: 2px !important;",
					"  margin-bottom: 6px !important;",
					"}",
					'nav:has(> button > span > [data-slot="sidebar.panellist"]) > button {',
					"  min-height: 26px !important;",
					"  height: 26px !important;",
					"  padding: 0 6px !important;",
					"  margin: 0 !important;",
					"  gap: 0 !important;",
					"  font-size: 12px !important;",
					"  line-height: 16px !important;",
					"}",
					'nav:has(> button > span > [data-slot="sidebar.panellist"]) > button > span:last-child:not(:first-child) {',
					"  display: none !important;",
					"}",
					'nav:has(> button > span > [data-slot="sidebar.panellist"]) > button:hover > span:last-child:not(:first-child),',
					'nav:has(> button > span > [data-slot="sidebar.panellist"]) > button[aria-current="page"] > span:last-child:not(:first-child) {',
					"  display: inline !important;",
					"  margin-left: 6px !important;",
					"}",
					'nav:has(> button > span > [data-slot="sidebar.panellist"]) > button > span:first-child svg {',
					"  width: 14px !important;",
					"  height: 14px !important;",
					"}"
				].join("\n")
			},
			{
				id: "footer-hover",
				label: "费用区悬停展开",
				labelEn: "Collapse the cost strip",
				title: "费用区（余额 / 套餐 / 峰谷 / 今日花费）默认只留余额一行，鼠标移上去再完整展开",
				titleEn: "The cost block keeps only the balance line until the pointer enters it",
				css: [
					'[data-slot="sidebar.footer.action"] > div { font-size: 11px !important; }',
					'[data-slot="sidebar.footer.action"] > div > * { display: none !important; }',
					'[data-slot="sidebar.footer.action"] > div > *:first-child {',
					"  display: flex !important;",
					"  height: 22px !important;",
					"}",
					'[data-slot="sidebar.footer.action"] > div:hover > * { display: revert !important; }'
				].join("\n")
			},
			{
				id: "tree-compact",
				label: "工作区行更紧凑",
				labelEn: "Denser workspace rows",
				title: "工作区与会话树行高 34px → 26px、字号 14px → 12px、图标 16px → 14px，一屏多显示四到五行",
				titleEn: "Workspace/session rows drop from 34px to 26px with 12px text and 14px icons, fitting 4-5 more rows per screen",
				css: [
					'[data-slot="sidebar.workspaces"] [role="treeitem"] {',
					"  min-height: 26px !important;",
					"  height: 26px !important;",
					"  font-size: 12px !important;",
					"  line-height: 18px !important;",
					"}",
					'[data-slot="sidebar.workspaces"] [role="treeitem"] svg {',
					"  width: 14px !important;",
					"  height: 14px !important;",
					"}",
					'[data-slot="sidebar.workspaces"] {',
					"  font-size: 12px !important;",
					"}"
				].join("\n")
			}
		];
		function presetBlock(id, css) {
			return [CSS_PRESET_MARK_OPEN(id), css, CSS_PRESET_MARK_CLOSE(id)].join("\n");
		}
		function hasPreset(css, id) {
			return css.indexOf(CSS_PRESET_MARK_OPEN(id)) >= 0;
		}
		/**
		* Insert or replace one preset block inside the user's stylesheet, leaving
		* every hand-written line intact. Replacing keeps the block where the user
		* first put it instead of appending a second copy at the end.
		*/
		function mergePreset(css, id, body) {
			const open = CSS_PRESET_MARK_OPEN(id);
			const close = CSS_PRESET_MARK_CLOSE(id);
			const at = css.indexOf(open);
			const block = body === null ? "" : presetBlock(id, body);
			if (at < 0) {
				if (body === null) return css;
				const base = css.replace(/\s+$/, "");
				return base === "" ? block : ` + "`${base}\\n\\n${block}`" + String.raw`;
			}
			const end = css.indexOf(close, at);
			const tail = end < 0 ? "" : css.slice(end + close.length);
			const head = css.slice(0, at);
			return ` + "`${head}${block}${tail}`" + String.raw`.replace(/\n{3,}/g, "\n\n").replace(/^\s+|\s+$/g, "");
		}
`;

function patchSource(source) {
  if (source.includes(MARK)) return { ok: true, skipped: true };

  // 1) 在 CssDraft 之前插入预设表与合并函数
  const anchor = 'function CssDraft(props) {';
  if (!source.includes(anchor)) throw new Error('找不到 CssDraft 定义，插件版本可能已变化');
  source = source.replace(anchor, PRESET_SOURCE + '\n\t\t' + anchor);

  // 2) 设置段里插入提示文案 + 按钮组
  const cssGroup = `\t\t\t\t\t/* @__PURE__ */ (0, react_jsx_runtime.jsxs)("div", {
						className: SideCardSection_module_css_default.group,
						children: [/* @__PURE__ */ (0, react_jsx_runtime.jsx)("div", {
							className: SideCardSection_module_css_default.groupHeading,
							children: t("settingsCustomCssTitle")
						}), /* @__PURE__ */ (0, react_jsx_runtime.jsx)(CssDraft, {`;
  if (!source.includes(cssGroup)) throw new Error('找不到自定义 CSS 设置块，插件版本可能已变化');
  source = source.replace(cssGroup, `\t\t\t\t\t/* @__PURE__ */ (0, react_jsx_runtime.jsxs)("div", {
						className: SideCardSection_module_css_default.group,
						children: [
							/* @__PURE__ */ (0, react_jsx_runtime.jsx)("div", {
								className: SideCardSection_module_css_default.groupHeading,
								children: t("settingsCustomCssTitle")
							}),
							/* @__PURE__ */ (0, react_jsx_runtime.jsx)("div", {
								className: SideCardSection_module_css_default.desc,
								children: t("cssPresetHint")
							}),
							/* @__PURE__ */ (0, react_jsx_runtime.jsx)("div", {
								className: SideCardSection_module_css_default.cssPresetGrid,
								role: "group",
								"aria-label": t("cssPresetGroup"),
								children: CSS_PRESETS.map((preset) => {
									const on = hasPreset(prefs.customCss, preset.id);
									return /* @__PURE__ */ (0, react_jsx_runtime.jsxs)("button", {
										type: "button",
										className: clsx(SideCardSection_module_css_default.pluginTopicBtn, on && SideCardSection_module_css_default.pluginTopicBtnOn),
										"aria-pressed": on,
										title: activeLocaleIsEn ? preset.titleEn : preset.title,
										onClick: () => {
											commitCustomCss(mergePreset(prefs.customCss, preset.id, on ? null : preset.css));
										},
										children: [on ? "✓ " : "+ ", activeLocaleIsEn ? preset.labelEn : preset.label]
									}, preset.id);
								})
							}),
							/* @__PURE__ */ (0, react_jsx_runtime.jsx)(CssDraft, {`);

  // 3) 组件开头声明 activeLocaleIsEn
  const compHead = `\t\tfunction SideCardSection({ store, service }) {
			const [prefs, setPrefs] = (0, react.useState)(() => store.getPrefs());`;
  if (!source.includes(compHead)) throw new Error('找不到 SideCardSection 头部');
  source = source.replace(compHead, compHead + `
			/** Whether the active UI locale is English (the preset chips carry both). */
			const activeLocaleIsEn = String(activeLocale()).toLowerCase().startsWith("en");`);

  // 4) 样式：网格 + 选中态。锚点是原版已有的 pluginTopicBtn 规则（它同时是
  //    宽度 100% 的来源，网格内要覆盖回 auto）。
  const btnRule = '._2vuxea_pluginTopicBtn{';
  if (!source.includes(btnRule)) throw new Error('找不到 pluginTopicBtn 样式锚点');
  source = source.replace(
    btnRule,
    '._2vuxea_cssPresetGrid{grid-template-columns:repeat(auto-fit,minmax(min(220px,100%),1fr));gap:6px;display:grid}' +
    '._2vuxea_cssPresetGrid>._2vuxea_pluginTopicBtn{width:auto}' +
    '._2vuxea_pluginTopicBtn._2vuxea_pluginTopicBtnOn,._2vuxea_pluginTopicBtn._2vuxea_pluginTopicBtnOn:hover{border-color:var(--dsw-alias-state-business-primary);background:color-mix(in srgb,var(--dsw-alias-state-business-primary) 12%,transparent);color:var(--dsw-alias-state-business-primary)}' +
    btnRule
  );

  // 5) 类名映射（原版只有 pluginTopicBtn，选中态类名由本补丁一并登记）
  const mapAnchor = '\t\t\t"pluginTopicBtn": "_2vuxea_pluginTopicBtn",';
  if (!source.includes(mapAnchor)) throw new Error('找不到类名映射表锚点');
  source = source.replace(
    mapAnchor,
    mapAnchor + '\n\t\t\t"pluginTopicBtnOn": "_2vuxea_pluginTopicBtnOn",\n\t\t\t"cssPresetGrid": "_2vuxea_cssPresetGrid",'
  );

  // 6) 中英文文案
  for (const [k, v] of [
    ['zh', ['点一下即可把整块配方并入下方输入框，再点一次撤销；手写的 CSS 不会被覆盖。', 'CSS 配方']],
    ['en', ['One click merges a whole recipe into the editor below; click again to remove it. Your own CSS is never overwritten.', 'CSS recipes']]
  ]) {
    const key = k === 'zh' ? 'settingsCustomCssPlaceholder: "/* 例：' : 'settingsCustomCssPlaceholder: "/* e.g.';
    const at = source.indexOf(key);
    if (at < 0) throw new Error('找不到 ' + k + ' 文案锚点');
    const lineEnd = source.indexOf('\n', at);
    source = source.slice(0, lineEnd) + `\n\t\t\tcssPresetHint: "${v[0]}",\n\t\t\tcssPresetGroup: "${v[1]}",` + source.slice(lineEnd);
  }

  return { ok: true, skipped: false, source };
}

const mode = process.argv.includes('--revert') ? 'revert'
  : process.argv.includes('--check') ? 'check'
  : 'apply';

if (!fs.existsSync(TARGET)) {
  console.error('找不到插件文件：' + TARGET);
  process.exit(1);
}

if (mode === 'check') {
  const src = fs.readFileSync(TARGET, 'utf8');
  console.log(src.includes(MARK) ? '已打过补丁' : '未打补丁');
  process.exit(0);
}

if (mode === 'revert') {
  const BACKUP = backupPath();
  if (!fs.existsSync(BACKUP)) {
    console.error('找不到备份文件：' + BACKUP);
    process.exit(1);
  }
  fs.copyFileSync(BACKUP, TARGET);
  console.log('已还原：' + TARGET);
  process.exit(0);
}

const original = fs.readFileSync(TARGET, 'utf8');
const BACKUP = backupPath();
if (!fs.existsSync(BACKUP)) fs.writeFileSync(BACKUP, original);

const result = patchSource(original);
if (result.skipped) {
  console.log('已打过补丁，跳过。要重来先 --revert');
  process.exit(0);
}
fs.writeFileSync(TARGET, result.source);
console.log('补丁已应用：' + TARGET);
console.log('重启 DSH 或刷新页面后，在 设置 → 侧边卡片 → 自定义 CSS 里可见四个配方按钮。');
