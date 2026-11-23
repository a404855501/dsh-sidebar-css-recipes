#!/usr/bin/env python3
"""给 DSH 工作区侧栏的筛选菜单加「只看置顶」。

直接改官方包 dsh-client-ui-workspace 的 lib/client.js：
  1. 视图 store 增加 pinnedFilter（all / only），持久化随 v5 一起
  2. sessionVisible 增加 pinned 过滤维度
  3. 分组 / 扁平 / 搜索三条派生链一起生效
  4. 筛选菜单加一条「只看已置顶」，可再点一次取消
  5. 空态区分「暂无置顶会话」，按钮同时清掉两个筛选
  6. 中文 / 英文文案

用法：
  python3 pin-filter-patch.py --check     # 只看能不能打（是否已打）
  python3 pin-filter-patch.py             # 打补丁（自动备份）
  python3 pin-filter-patch.py --revert    # 还原
"""

import glob
import os
import shutil
import sys

REL = (
    "Contents/Resources/app/dsh/node_modules/@deepseek-ai/"
    "dsh-client-ui-workspace/lib/client.js"
)


def find_target():
    for app in glob.glob("/Applications/*.app"):
        p = os.path.join(app, REL)
        if os.path.isfile(p):
            return p
    raise SystemExit("没找到 dsh-client-ui-workspace 的 client.js")


# (名称, 原文, 新文)
EDITS = [
    # ---- 1. store: init ----
    (
        "store.init",
        '\t\t\t\t\tsessionOrderByAccount: {},\n'
        '\t\t\t\t\tarchivedFilter: "default"\n'
        "\t\t\t\t}),",
        '\t\t\t\t\tsessionOrderByAccount: {},\n'
        '\t\t\t\t\tarchivedFilter: "default",\n'
        '\t\t\t\t\tpinnedFilter: "all"\n'
        "\t\t\t\t}),",
    ),
    # ---- 2. store: action ----
    (
        "store.action",
        "\t\t\t\t\tsetArchivedFilter: (d, filter) => {\n"
        "\t\t\t\t\t\td.archivedFilter = filter;\n"
        "\t\t\t\t\t}\n",
        "\t\t\t\t\tsetArchivedFilter: (d, filter) => {\n"
        "\t\t\t\t\t\td.archivedFilter = filter;\n"
        "\t\t\t\t\t},\n"
        "\t\t\t\t\tsetPinnedFilter: (d, filter) => {\n"
        "\t\t\t\t\t\td.pinnedFilter = filter;\n"
        "\t\t\t\t\t}\n",
    ),
    # ---- 3. sessionVisible ----
    (
        "sessionVisible.def",
        "\t\tfunction sessionVisible(session, current, archived, archivedFilter) {\n"
        '\t\t\tif (session.origin === "subagent") return false;\n'
        "\t\t\tif (session.blank && session.id !== current) return false;\n",
        "\t\tfunction sessionVisible(session, current, archived, pinned, archivedFilter, pinnedFilter) {\n"
        '\t\t\tif (session.origin === "subagent") return false;\n'
        "\t\t\tif (session.blank && session.id !== current) return false;\n"
        '\t\t\tif (pinnedFilter === "only" && !(pinned.has(session.id) && !archived.has(session.id))) return false;\n',
    ),
    # ---- 4. groupByWorkspace ----
    (
        "groupByWorkspace.def",
        "function groupByWorkspace(list, workspaces, archived, archivedFilter, ungroupedOrder) {",
        "function groupByWorkspace(list, workspaces, archived, pinned, archivedFilter, pinnedFilter, ungroupedOrder) {",
    ),
    (
        "groupByWorkspace.call",
        "\t\t\t\t\tif (!sessionVisible(summary, current, archived, archivedFilter)) continue;",
        "\t\t\t\t\tif (!sessionVisible(summary, current, archived, pinned, archivedFilter, pinnedFilter)) continue;",
    ),
    (
        "groupByWorkspace.emptyGroup",
        '\t\t\t\tif (archivedFilter === "only" && members.length === 0) continue;',
        '\t\t\t\tif ((archivedFilter === "only" || pinnedFilter === "only") && members.length === 0) continue;',
    ),
    (
        "groupByWorkspace.stray",
        "filter((s) => s !== void 0 && !accounted.has(s.id) && sessionVisible(s, current, archived, archivedFilter));",
        'filter((s) => s !== void 0 && !accounted.has(s.id) && sessionVisible(s, current, archived, pinned, archivedFilter, pinnedFilter));',
    ),
    # ---- 5. deriveGroups ----
    (
        "deriveGroups.call",
        "for (const g of groupByWorkspace(list, workspaces, archived, rowState.archivedFilter, view.ungroupedOrder)) {",
        'for (const g of groupByWorkspace(list, workspaces, archived, pinned, rowState.archivedFilter, rowState.pinnedFilter ?? "all", view.ungroupedOrder)) {',
    ),
    # ---- 6. visibleSessionIds ----
    (
        "visibleSessionIds.def",
        "function visibleSessionIds(list, archivedSessionIds, archivedFilter) {\n"
        "\t\t\tconst archived = new Set(archivedSessionIds);",
        "function visibleSessionIds(list, archivedSessionIds, archivedFilter, pinnedSessionIds, pinnedFilter) {\n"
        "\t\t\tconst archived = new Set(archivedSessionIds);\n"
        "\t\t\tconst pinned = new Set(pinnedSessionIds ?? []);",
    ),
    (
        "visibleSessionIds.call",
        "\t\t\t\treturn s !== void 0 && sessionVisible(s, current, archived, archivedFilter);",
        '\t\t\t\treturn s !== void 0 && sessionVisible(s, current, archived, pinned, archivedFilter, pinnedFilter ?? "all");',
    ),
    (
        "sessionMemberIds.call",
        '\t\t\treturn visibleSessionIds(list, [], "show");',
        '\t\t\treturn visibleSessionIds(list, [], "show", [], "all");',
    ),
    # ---- 7. deriveFlat ----
    (
        "deriveFlat.call",
        "return session !== void 0 && sessionVisible(session, current, archived, rowState.archivedFilter) ? [session] : [];",
        'return session !== void 0 && sessionVisible(session, current, archived, pinned, rowState.archivedFilter, rowState.pinnedFilter ?? "all") ? [session] : [];',
    ),
    # ---- 8. deriveSearchResults ----
    (
        "search.def",
        "function deriveSearchResults(list, workspaces, query, archivedSessionIds, archivedFilter, statuses, content, limit) {",
        "function deriveSearchResults(list, workspaces, query, archivedSessionIds, archivedFilter, pinnedSessionIds, pinnedFilter, statuses, content, limit) {",
    ),
    (
        "search.sets",
        '\t\t\tconst archived = new Set(archivedSessionIds);\n'
        "\t\t\tconst current = mainSessionId(list);\n"
        "\t\t\tconst workspaceBySession = /* @__PURE__ */ new Map();",
        '\t\t\tconst archived = new Set(archivedSessionIds);\n'
        '\t\t\tconst pinned = new Set(pinnedSessionIds);\n'
        "\t\t\tconst current = mainSessionId(list);\n"
        "\t\t\tconst workspaceBySession = /* @__PURE__ */ new Map();",
    ),
    (
        "search.local",
        "if (summary === void 0 || summary.blank || !sessionVisible(summary, current, archived, archivedFilter)) continue;",
        "if (summary === void 0 || summary.blank || !sessionVisible(summary, current, archived, pinned, archivedFilter, pinnedFilter)) continue;",
    ),
    (
        "search.content",
        "if (summary !== void 0 && !summary.blank && sessionVisible(summary, current, archived, archivedFilter)) include(summary);",
        "if (summary !== void 0 && !summary.blank && sessionVisible(summary, current, archived, pinned, archivedFilter, pinnedFilter)) include(summary);",
    ),
    # ---- 9. SearchResults 组件 ----
    (
        "SearchResults.props",
        "function SearchResults({ useSessions, useSessionStatus, open, onUnarchive, workspaces, archivedSessionIds, archivedFilter, query, remote, resultLimit, usePanelInfo, t }) {",
        "function SearchResults({ useSessions, useSessionStatus, open, onUnarchive, workspaces, archivedSessionIds, archivedFilter, pinnedSessionIds, pinnedFilter, query, remote, resultLimit, usePanelInfo, t }) {",
    ),
    (
        "SearchResults.call",
        "deriveSearchResults(list, workspaces, query, archivedSessionIds, archivedFilter, statuses, currentRemote, resultLimit), [",
        "deriveSearchResults(list, workspaces, query, archivedSessionIds, archivedFilter, pinnedSessionIds, pinnedFilter, statuses, currentRemote, resultLimit), [",
    ),
    (
        "SearchResults.deps",
        "\t\t\t\tarchivedSessionIds,\n"
        "\t\t\t\tarchivedFilter,\n"
        "\t\t\t\tstatuses,\n"
        "\t\t\t\tcurrentRemote,\n"
        "\t\t\t\tresultLimit\n"
        "\t\t\t]);",
        "\t\t\t\tarchivedSessionIds,\n"
        "\t\t\t\tarchivedFilter,\n"
        "\t\t\t\tpinnedSessionIds,\n"
        "\t\t\t\tpinnedFilter,\n"
        "\t\t\t\tstatuses,\n"
        "\t\t\t\tcurrentRemote,\n"
        "\t\t\t\tresultLimit\n"
        "\t\t\t]);",
    ),
    # ---- 10. 菜单组件 ----
    (
        "menu.props",
        "function ViewOptionsMenu({ groupBy, orderBy, archivedFilter, onGroupPick, onOrderPick, onArchivedFilterPick, t }) {",
        "function ViewOptionsMenu({ groupBy, orderBy, archivedFilter, pinnedFilter, onGroupPick, onOrderPick, onArchivedFilterPick, onPinnedFilterPick, t }) {",
    ),
    (
        "menu.item",
        '\t\t\t\t\t{\n'
        '\t\t\t\t\t\tid: "only-archived",\n'
        '\t\t\t\t\t\tlabel: t("viewOptions.onlyArchived"),\n'
        '\t\t\t\t\t\ticon: (0, react_jsx_runtime.jsx)(_deepseek_ai_dsh_client_ui_primitives.IconArchiveCheckOutlineRegular, {})\n'
        "\t\t\t\t\t}\n"
        "\t\t\t\t],",
        '\t\t\t\t\t{\n'
        '\t\t\t\t\t\tid: "only-archived",\n'
        '\t\t\t\t\t\tlabel: t("viewOptions.onlyArchived"),\n'
        '\t\t\t\t\t\ticon: (0, react_jsx_runtime.jsx)(_deepseek_ai_dsh_client_ui_primitives.IconArchiveCheckOutlineRegular, {})\n'
        "\t\t\t\t\t},\n"
        "\t\t\t\t\t{\n"
        '\t\t\t\t\t\tid: "only-pinned",\n'
        '\t\t\t\t\t\tlabel: t("viewOptions.onlyPinned"),\n'
        '\t\t\t\t\t\ticon: (0, react_jsx_runtime.jsx)(_deepseek_ai_dsh_client_ui_primitives.IconPinFillRegular, {})\n'
        "\t\t\t\t\t}\n"
        "\t\t\t\t],",
    ),
    (
        "menu.selected",
        "\t\t\t\t\t{\n"
        '\t\t\t\t\t\tdefault: "hide-archived",\n'
        '\t\t\t\t\t\tshow: "show-archived",\n'
        '\t\t\t\t\t\tonly: "only-archived"\n'
        "\t\t\t\t\t}[archivedFilter]\n"
        "\t\t\t\t],",
        "\t\t\t\t\t{\n"
        '\t\t\t\t\t\tdefault: "hide-archived",\n'
        '\t\t\t\t\t\tshow: "show-archived",\n'
        '\t\t\t\t\t\tonly: "only-archived"\n'
        "\t\t\t\t\t}[archivedFilter],\n"
        '\t\t\t\t\t...(pinnedFilter === "only" ? ["only-pinned"] : [])\n'
        "\t\t\t\t],",
    ),
    (
        "menu.onSelect",
        '\t\t\t\t\telse if (id === "only-archived") onArchivedFilterPick("only");\n',
        '\t\t\t\t\telse if (id === "only-archived") onArchivedFilterPick("only");\n'
        '\t\t\t\t\telse if (id === "only-pinned") onPinnedFilterPick(pinnedFilter === "only" ? "all" : "only");\n',
    ),
    # ---- 11. 浏览器组件：读取 + 传参 ----
    (
        "browser.store",
        '\t\t\tconst archivedFilter = useStore((s) => s.archivedFilter ?? "default");',
        '\t\t\tconst archivedFilter = useStore((s) => s.archivedFilter ?? "default");\n'
        '\t\t\tconst pinnedFilter = useStore((s) => s.pinnedFilter ?? "all");',
    ),
    (
        "browser.leave",
        "\t\t\tconst leaveArchivedOnly = () => {\n"
        '\t\t\t\tactions.setArchivedFilter("default");\n'
        "\t\t\t};",
        "\t\t\tconst leaveArchivedOnly = () => {\n"
        '\t\t\t\tactions.setArchivedFilter("default");\n'
        '\t\t\t\tactions.setPinnedFilter("all");\n'
        "\t\t\t};",
    ),
    (
        "browser.rowState",
        "\t\t\tconst rowState = (0, react.useMemo)(() => ({\n"
        "\t\t\t\t...orderState,\n"
        "\t\t\t\tarchivedFilter\n"
        "\t\t\t}), [orderState, archivedFilter]);",
        "\t\t\tconst rowState = (0, react.useMemo)(() => ({\n"
        "\t\t\t\t...orderState,\n"
        "\t\t\t\tarchivedFilter,\n"
        "\t\t\t\tpinnedFilter\n"
        "\t\t\t}), [orderState, archivedFilter, pinnedFilter]);",
    ),
    (
        "browser.menu",
        "\t\t\t\t\t\t\t\t\tonArchivedFilterPick: actions.setArchivedFilter,",
        "\t\t\t\t\t\t\t\t\tonArchivedFilterPick: actions.setArchivedFilter,\n"
        "\t\t\t\t\t\t\t\t\tpinnedFilter,\n"
        "\t\t\t\t\t\t\t\t\tonPinnedFilterPick: actions.setPinnedFilter,",
    ),
    (
        "browser.searchProps",
        "\t\t\t\t\t\t\tarchivedSessionIds,\n"
        "\t\t\t\t\t\t\tarchivedFilter,\n"
        "\t\t\t\t\t\t\tquery: normalizedQuery,",
        "\t\t\t\t\t\t\tarchivedSessionIds,\n"
        "\t\t\t\t\t\t\tarchivedFilter,\n"
        "\t\t\t\t\t\t\tpinnedSessionIds,\n"
        "\t\t\t\t\t\t\tpinnedFilter,\n"
        "\t\t\t\t\t\t\tquery: normalizedQuery,",
    ),
    # ---- 12. 空态 ----
    (
        "empty.state",
        "\t\tfunction EmptySessions({ rowState, onLeaveArchivedOnly, t }) {\n"
        '\t\t\tconst archivedOnly = rowState.archivedFilter === "only";',
        "\t\tfunction EmptySessions({ rowState, onLeaveArchivedOnly, t }) {\n"
        '\t\t\tconst archivedOnly = rowState.archivedFilter === "only";\n'
        '\t\t\tconst pinnedOnly = !archivedOnly && rowState.pinnedFilter === "only";',
    ),
    (
        "empty.icon",
        "\t\t\t\t\tarchivedOnly ? (0, react_jsx_runtime.jsx)(_deepseek_ai_dsh_client_ui_primitives.IconArchiveOutlineRegular, { size: 24 }) : (0, react_jsx_runtime.jsx)(_deepseek_ai_dsh_client_ui_primitives.IconQueueOutlineRegular, { size: 24 }),",
        "\t\t\t\t\tarchivedOnly ? (0, react_jsx_runtime.jsx)(_deepseek_ai_dsh_client_ui_primitives.IconArchiveOutlineRegular, { size: 24 }) : pinnedOnly ? (0, react_jsx_runtime.jsx)(_deepseek_ai_dsh_client_ui_primitives.IconPinFillRegular, { size: 24 }) : (0, react_jsx_runtime.jsx)(_deepseek_ai_dsh_client_ui_primitives.IconQueueOutlineRegular, { size: 24 }),",
    ),
    (
        "empty.text",
        '\t\t\t\t\t(0, react_jsx_runtime.jsx)("div", { children: archivedOnly ? t("empty.noneArchived") : t("empty.none") }),\n'
        "\t\t\t\t\tarchivedOnly && (0, react_jsx_runtime.jsx)(\"button\", {",
        '\t\t\t\t\t(0, react_jsx_runtime.jsx)("div", { children: archivedOnly ? t("empty.noneArchived") : pinnedOnly ? t("empty.nonePinned") : t("empty.none") }),\n'
        "\t\t\t\t\t(archivedOnly || pinnedOnly) && (0, react_jsx_runtime.jsx)(\"button\", {",
    ),
    # ---- 13. 文案 ----
    (
        "i18n.zh",
        '\t\t\t"viewOptions.onlyArchived": "仅显示已归档",',
        '\t\t\t"viewOptions.onlyArchived": "仅显示已归档",\n'
        '\t\t\t"viewOptions.onlyPinned": "只看已置顶",',
    ),
    (
        "i18n.zh.empty",
        '\t\t\t"empty.noneArchived": "暂无已归档会话",\n'
        '\t\t\t"empty.viewOthers": "查看其他会话",',
        '\t\t\t"empty.noneArchived": "暂无已归档会话",\n'
        '\t\t\t"empty.nonePinned": "暂无置顶会话",\n'
        '\t\t\t"empty.viewOthers": "查看其他会话",',
    ),
    (
        "i18n.en",
        '\t\t\t"viewOptions.onlyArchived": "Archived only",',
        '\t\t\t"viewOptions.onlyArchived": "Archived only",\n'
        '\t\t\t"viewOptions.onlyPinned": "Pinned only",',
    ),
    (
        "i18n.en.empty",
        '\t\t\t"empty.noneArchived": "No archived sessions yet",\n'
        '\t\t\t"empty.viewOthers": "View other sessions",',
        '\t\t\t"empty.noneArchived": "No archived sessions yet",\n'
        '\t\t\t"empty.nonePinned": "No pinned sessions yet",\n'
        '\t\t\t"empty.viewOthers": "View other sessions",',
    ),
    # ---- 12. 只看已置顶时自动展开分组，置顶会话直接可见 ----
    (
        "deriveGroups.expand",
        "\t\t\t\tconst expanded = expandedGroups.has(g.key);",
        '\t\t\t\tconst expanded = rowState.pinnedFilter === "only" ? true : expandedGroups.has(g.key);',
    ),
    # ---- 13. 切换筛选时重置列表动画（两处渲染分支）----
    (
        "animation.flat",
        "\t\t\t\t\t\t\tsessionIds: orderedFlatSessionIds,\n"
        "\t\t\t\t\t\t\trowState,\n"
        "\t\t\t\t\t\t\tonLeaveArchivedOnly: leaveArchivedOnly,\n"
        '\t\t\t\t\t\t\tworkspaceReady,\n'
        "\t\t\t\t\t\t\tanimationResetKey: `${groupBy}/${orderBy}/${archivedFilter}`,",
        "\t\t\t\t\t\t\tsessionIds: orderedFlatSessionIds,\n"
        "\t\t\t\t\t\t\trowState,\n"
        "\t\t\t\t\t\t\tonLeaveArchivedOnly: leaveArchivedOnly,\n"
        '\t\t\t\t\t\t\tworkspaceReady,\n'
        "\t\t\t\t\t\t\tanimationResetKey: `${groupBy}/${orderBy}/${archivedFilter}/${pinnedFilter}`,",
    ),
    (
        "animation.tree",
        "\t\t\t\t\t\t\tnestWorkspaces: groupBy === \"workspace-tree\",\n"
        "\t\t\t\t\t\t\tanimationResetKey: `${groupBy}/${orderBy}/${archivedFilter}`,",
        "\t\t\t\t\t\t\tnestWorkspaces: groupBy === \"workspace-tree\",\n"
        "\t\t\t\t\t\t\tanimationResetKey: `${groupBy}/${orderBy}/${archivedFilter}/${pinnedFilter}`,",
    ),
]


def main():
    args = set(sys.argv[1:])
    path = find_target()
    src = open(path, encoding="utf-8").read()

    bak = path + ".orig"
    patched = 'pinnedFilter: "all"' in src

    if "--revert" in args:
        if not os.path.isfile(bak):
            print("没有备份，无法还原")
            return 1
        shutil.copy2(bak, path)
        print("已还原:", path)
        return 0

    if "--check" in args:
        print("目标:", path)
        print("已打补丁:", patched)
        if not patched:
            missing = [n for n, old, _ in EDITS if src.count(old) != 1]
            print("可打补丁:", not missing, "缺失/重复:", missing)
        return 0

    if patched:
        print("已经打过补丁，跳过:", path)
        return 0

    # 全部替换前先校验每段唯一命中，避免错位
    bad = [(n, src.count(old)) for n, old, _ in EDITS if src.count(old) != 1]
    if bad:
        print("以下片段未唯一命中，已中止（文件未改动）:")
        for n, c in bad:
            print(f"  {n}: 命中 {c} 次")
        return 2

    if not os.path.isfile(bak):
        shutil.copy2(path, bak)
        print("已备份:", bak)

    out = src
    for _, old, new in EDITS:
        out = out.replace(old, new, 1)

    open(path, "w", encoding="utf-8").write(out)
    print("补丁已写入:", path)
    print("原始大小:", len(src), "→", len(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
