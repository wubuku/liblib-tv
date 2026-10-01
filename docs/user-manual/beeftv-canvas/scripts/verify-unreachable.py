#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「不可达声明」双向核对闸：手册说「这个功能进不去」的，上游是否仍然进不去。

背景（Batch 133）：手册里最难悄悄过期的一类断言，是**否定式断言**——
「画布库没有导入入口」「审美批改在画布上建不出节点」「章节路由访问不到」。
它们不像数值和文案，没有编译期或运行时兜底：上游哪天把那个 `ref.current.click()`
接上、或者把 setter 补上，**手册会继续言之凿凿地告诉用户「找不到」**，
而用户已经在界面上看到了那个按钮。这类过期比过期一个数字更伤害信任。

本闸对每条已登记的「不可达」断言做两件事：

  **方向一（登记项是否仍成立）**：逐条取上游 `origin/main` 的源码，跑该条专属判据。
  判据**不再成立** = 上游可能已修复 → 手册该条断言已过期 → 退出码 1。

  **方向二（登记表是否完整）**：反向扫全库 `web/src`，找
  「`useState` 解构出的 setter 声明后零调用」——这是 Batch 131/132 反复证明
  **信噪比最高**的缺陷模式（setter 侧 3/3 全真，ref 侧 9/9 全假）。
  扫描命中集合必须与登记集合**完全一致**：多出未登记项 = 手册漏了新缺陷；
  少于登记项 = 某条登记已失效或登记名写错。
  **双向都过，才说明这张表既没漏、也没烂。**

Batch 135 新增 **方向三（URL 参数只读不写）**：扫全库每个 `searchParams.get("X")`
的参数 X，统计它在源码里有没有「写出点」。零写出 = **界面上无法产生**这个参数。
这是 prop/查询参数层面的同一类缺陷（Batch 131 登记的是 setter 侧、ref 侧，
Batch 135 补上 URL 侧），同样要求双向一致，但**必须带豁免名单**——
原因见下方 `URL_PARAM_EXEMPT` 的注释：零写出**不足以**判定缺陷。

只检查「不可达是否仍成立」，不判断「不可达本身该不该修」——后者要人读实现。
脚本读的是上游 `origin/main` 的**对象**（`git show`），不是本地工作树，
避免本机 detached HEAD 指向旧版本时误判。

退出码：0 三向均通过；1 有断言已过期，或登记表与扫描结果不一致。

不检查什么（明确声明，避免后来者误以为覆盖面更大）：
  · 不覆盖运行时行为（按钮是否真的不渲染）——本闸只看源码判据；
  · 不覆盖 `pages/projects/` 整目录的死代码量级（Batch 125 已一次性记录，
    不逐条登记，否则登记表会膨胀到无法维护）；
  · 不覆盖 `verify-exclusions.py` 已登记的解禁条件（短剧生产台等），
    本闸只管「不可达声明」，不重复管「解禁条件」，两者刻意不重叠；
  · **方向三不判断「零写出是否就是缺陷」**——它只保证每个零写出参数都被
    显式归类为「已知豁免」或「已登记缺陷」，防止将来上游新增一个无人认领的参数。
"""

import os
import re
import subprocess
import sys

CANDIDATES = [
    os.environ.get("BEEFTV_SRC", ""),
    "/Users/yangjiefeng/Documents/glanderness/BeefTV",
]

# 上游 ref 可用 BEEFTV_REF 覆盖——反向验证（self-test）需要指向一个
# 「缺陷已被修复」的人造 ref，不能改工作树、更不能动别人分支。
REF = os.environ.get("BEEFTV_REF", "origin/main")

# ── 工具 ──────────────────────────────────────────────────────────────


def find_source():
    for c in CANDIDATES:
        if c and os.path.isdir(os.path.join(c, "backend")):
            return os.path.abspath(c)
    return None


def git_show(src, path, ref=REF):
    r = subprocess.run(["git", "show", f"{ref}:{path}"],
                       cwd=src, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def zero_call_setters(src):
    """返回 {文件: [setter 名]}：useState 解构出的 setter 在本文件内零调用。

    判据是**零调用**而不是「少调用」——Batch 132 实测：ref 出现 2 次是常态，
    9/9 全是假警报；setter 零调用 3/3 全真。
    """
    r = subprocess.run(
        ["git", "grep", "-n", "-E",
         r"const \[[A-Za-z_$][A-Za-z0-9_$]*, *(set[A-Za-z0-9_$]*)\] *= *useState",
         REF, "--", "web/src"],
        cwd=src, capture_output=True, text=True)
    hits = {}
    for line in (r.stdout or "").split("\n"):
        if not line.strip():
            continue
        # 形如 origin/main:web/src/...:12:const [a, setFoo] = useState(...)
        m = re.match(rf"^{re.escape(REF)}:(.+?):(\d+):(.*)$", line)
        if not m:
            continue
        path, _lineno, text = m.group(1), m.group(2), m.group(3)
        sm = re.search(r"const \[[A-Za-z_$][A-Za-z0-9_$]*, *(set[A-Za-z0-9_$]*)\] *= *useState", text)
        if not sm:
            continue
        name = sm.group(1)
        body = git_show(src, path)
        if body and len(re.findall(r"\b" + re.escape(name) + r"\b", body)) <= 1:
            hits.setdefault(path, []).append(name)
    return hits


# ── 已登记的「不可达」断言 ───────────────────────────────────────────
# 每条 = (id, 说明, 判据函数)。判据返回 True = 仍然不可达（手册断言仍成立）。


def _canvas_library_index(src):
    return git_show(src, "web/src/pages/canvas/index.tsx")


def p_sort_filter(src):
    """画布库的三套排序与三档筛选：setter 零调用 → 界面上没有任何控件能改动。"""
    body = _canvas_library_index(src)
    if not body:
        return None
    for name in ("setSort", "setProjectFilter"):
        if len(re.findall(r"\b" + name + r"\b", body)) > 1:
            return False
    return True


def p_import_entry(src):
    """画布库导入：隐藏的 zip file input 挂着了，但 inputRef 从未被 click()。"""
    body = _canvas_library_index(src)
    if not body:
        return None
    has_input = "application/zip,.zip" in body
    # 必须同时接受 `inputRef.current.click(` 与 `inputRef.current?.click(`：
    # **可选链正是本仓库的惯用写法**（同文件 :714 的 coverInputRef.current?.click()
    # 就是这么写的），反向验证 Batch 133 正是靠这一点抓出本判据过窄的漏洞。
    no_click = not re.search(r"inputRef\s*\.\s*current\s*\??\s*\.\s*click\s*\(", body)
    return has_input and no_click


def p_join_project(src):
    """「加入项目 / 移出项目」：isLocalWorkspaceMode() 无条件 true → remoteMode 恒假。"""
    wsm = git_show(src, "web/src/services/workspace-mode.ts")
    if not wsm:
        return None
    m = re.search(r"export function isLocalWorkspaceMode\s*\(\s*\)\s*\{(.*?)\n\}", wsm, re.S)
    body = m.group(1) if m else ""
    hardcoded_true = bool(m) and "return true" in body and "return false" not in body \
        and not re.search(r"\bif\b|\?|&&|\|\|", body)
    index = _canvas_library_index(src)
    gated = "remoteMode" in index
    return hardcoded_true and gated


def p_art_critique_entry(src):
    """AI 审美批改：节点已注册，但「添加节点」是写死清单，从不读插件注册表。"""
    menu = git_show(src, "web/src/lib/canvas/tool-registry/definitions/add-node-menu-tools.tsx")
    plugin = git_show(src, "web/src/lib/plugins/builtin/ai-art-critique.ts")
    if not menu or not plugin:
        return None
    in_menu = "ai-art-critique" in menu or "ART_CRITIQUE" in menu
    contributes = "canvasNodes" in plugin
    return contributes and not in_menu


def p_art_critique_autostart(src):
    """审美批改「打开弹窗即自动开始」：setArtCritiqueStartRequest 零调用 → 恒 null。"""
    body = git_show(src, "web/src/pages/canvas/project.tsx")
    if not body:
        return None
    return len(re.findall(r"\bsetArtCritiqueStartRequest\b", body)) <= 1


def p_projects_library_dead(src):
    """34KB 的 pages/projects 项目库：loadProjectsPage 导出但全库零引用。"""
    mod = git_show(src, "web/src/lib/workspace-route-modules.ts")
    if not mod:
        return None
    if "loadProjectsPage" not in mod:
        return False
    r = subprocess.run(["git", "grep", "-l", "loadProjectsPage", REF, "--", "web/src"],
                       cwd=src, capture_output=True, text=True)
    hits = [l for l in (r.stdout or "").split("\n") if l.strip()]
    return len(hits) <= 1


def p_chapter_workflow_routes(src):
    """章节 / 工作流深路由：已注册，但共用入口在 localMode 下先 Navigate 走人。"""
    router = git_show(src, "web/src/router.tsx")
    wsm = git_show(src, "web/src/services/workspace-mode.ts")
    if not router or not wsm:
        return None
    has_routes = "chapters/:chapterId" in router and "workflow/:unitId/:stage" in router
    m = re.search(r"export function isLocalWorkspaceMode\s*\(\s*\)\s*\{(.*?)\n\}", wsm, re.S)
    body = m.group(1) if m else ""
    hardcoded_true = bool(m) and "return true" in body and "return false" not in body \
        and not re.search(r"\bif\b|\?|&&|\|\|", body)
    nav_pos = router.find('<Navigate to={`/canvas/${projectId}`} replace />')
    render_pos = router.find("deferred(<ProjectDetailPage />)")
    nav_first = nav_pos != -1 and render_pos != -1 and nav_pos < render_pos
    return has_routes and hardcoded_true and nav_first


def p_readonly_no_ui_entry(src):
    """只读画布模式：判定完整、透传到位，但全库零处写入 readonly / mode=readonly。

    判据分两半，缺一不可：
      (a) 只读判定仍在（project.tsx 那一行没被删改）；
      (b) 全库**没有任何字符串字面量**里带 `?readonly=` / `&readonly=` /
          `?mode=readonly` / `&mode=readonly` —— 即没有界面动作能产生只读网址。
    缺 (b) 的旧版写法（只 grep `navigate(` / `to=`）已漏过一次真实生产者
    （首页能力卡的 `to: "/canvas?mode=new&add=video"`，URL 存在数据对象里再当 prop 传），
    这次统一用「字符串字面量含 `?参数=`」的保守口径。
    """
    body = git_show(src, "web/src/pages/canvas/project.tsx")
    if not body:
        return None
    judged = bool(re.search(
        r'searchParams\.get\("readonly"\)\s*===\s*"1"\s*\|\|\s*'
        r'searchParams\.get\("mode"\)\s*===\s*"readonly"', body))
    if not judged:
        return False
    r = subprocess.run(["git", "grep", "-I", "-E", r'["`][^"`\n]{0,300}?[?&](readonly|mode)\s*=\s*(1|readonly)',
                        REF, "--", "web/src"], cwd=src, capture_output=True, text=True)
    producers = [l for l in (r.stdout or "").split("\n") if l.strip()]
    return not producers


def p_copy_not_synced(src):
    """画布副本「复制那一刻」不上传：顶栏「复制画布」与只读「复制项目」都只写本地。

    ⚠️ 判据的范围要说准，否则会被误读成「副本永远不落盘」——**这是 Batch 137
    实测纠正过的**：复制后只要**做一次内容编辑**，500ms 防抖的内容保存就会把
    副本 PUT 上去（目标就是副本自己）。所以本条断言的准确表述是
    **「复制这个动作本身不触发上传」**，手册也据此写成「复制完顺手改一笔」，
    而不是「副本永远只在本机」。

    判据要求三者同时成立，缺一即上游已修：
      (a) 两条复制入口都调用 store 的 importProject（纯内存 set，无网络）；
      (b) 两条都只 flushCanvasStorePersistence（IndexedDB），都没有
          syncLocalCanvasProjectToBackend；
      (c) 对照组 createLocalCanvasProject **仍然**带 syncLocalCanvasProjectToBackend
          ——(c) 是关键：没有它就无法区分「漏了一步」与「整体改成不上传的设计」。
    """
    proj = git_show(src, "web/src/pages/canvas/project.tsx")
    store = git_show(src, "web/src/stores/canvas/use-canvas-store.ts")
    repo = git_show(src, "web/src/services/local-workspace-repository.ts")
    if not proj or not store or not repo:
        return None
    for fn in ("duplicateCurrentProject", "duplicateCanvasFromMenu"):
        m = re.search(rf"const {fn} = useCallback\(async.*?\n    \}}, \[", proj, re.S)
        if not m:
            return False
        body = m.group(0)
        if "importCanvasProject" not in body:
            return False
        if "syncLocalCanvasProjectToBackend" in body:
            return False
    m = re.search(r"export async function createLocalCanvasProject.*?\n\}", repo, re.S)
    if not m or "syncLocalCanvasProjectToBackend" not in m.group(0):
        return False
    # importProject 必须是纯 set，不能带网络调用
    m2 = re.search(r"importProject: \(source, workspaceProjectId\) => \{.*?\n            \},", store, re.S)
    if not m2:
        return False
    return "http." not in m2.group(0) and "fetch(" not in m2.group(0)


def p_content_watcher_excludes_title(src):
    """自动保存只盯「画布内容」字段，**title / canvasTitle 不在监视列表里**。

    这是 Batch 135/136 三个缺陷的共同根因：改名不触发保存、复制不触发保存。
    判据要求：
      (a) 内容保存那个 effect 的 snapshot/patch 只含内容字段
          （nodes/connections/chatSessions/activeChatId/appearance/backgroundMode/showImageInfo）；
      (b) snapshot 与 patch 里都**不出现** title / canvasTitle；
      (c) 差异判定存在（stored 全等则 return），这解释了「复制因为内容没变而不保存」。
    """
    body = git_show(src, "web/src/pages/canvas/use-canvas-project-lifecycle.ts")
    if not body:
        return None
    snaps = re.findall(r"const (?:snapshot|patch) = \{([^}]*)\};", body)
    if len(snaps) < 2:
        return False
    for s_ in snaps[:2]:
        if re.search(r"\b(canvasTitle|title)\b", s_):
            return False
    # 外观字段在 snapshot 里是简写 `canvasAppearance`（状态变量名），
    # 在 patch 里是 `appearance: canvasAppearance`（字段名）——**判据不能假设
    # 两处写法一致**，否则会把这个正确成立的断言误报成失效（Batch 137 首轮就踩了）。
    common = {"nodes", "connections", "chatSessions", "activeChatId",
              "backgroundMode", "showImageInfo"}
    for s_ in snaps[:2]:
        keys = {k.strip().split(":")[0].strip() for k in s_.split(",") if k.strip()}
        if not common.issubset(keys):
            return False
        if not ({"appearance", "canvasAppearance"} & keys):
            return False
    return "scheduleLocalCanvasBackendSync" in body and "every(([key, value])" in body


def p_canvas_folders_are_local(src):
    """画布库的文件夹是纯本机概念：store 的 createFolder 写本地，且从不碰 /asset-folders。

    判据要求三件事同时成立：
      (a) 画布库页面从 store 取 createFolder，且新建按钮调它；
      (b) 存在 writeCanvasFolders（本地持久化）而不是任何网络调用；
      (c) 画布库页面**零处**引用 AssetFolder / asset-folders——
          (c) 是关键：服务端的 folderId 只属于素材，没有它才能断言
          「服务端根本没有画布文件夹这个概念」，而不是「这里忘了同步」。
    """
    idx = git_show(src, "web/src/pages/canvas/index.tsx")
    store = git_show(src, "web/src/stores/canvas/use-canvas-store.ts")
    if not idx or not store:
        return None
    if "createFolder" not in idx or "createFolder(" not in idx:
        return False
    if "writeCanvasFolders" not in store or "readCanvasFolders" not in store:
        return False
    return "AssetFolder" not in idx and "asset-folders" not in idx


def p_canvas_cover_is_localstorage(src):
    """画布封面存 localStorage（按画布 id），不是画布内容的一部分。"""
    card = git_show(src, "web/src/components/canvas/canvas-folder-card.tsx")
    if not card:
        return None
    m = re.search(r"const saveCover = async \(\) => \{.*?\n        \};", card, re.S)
    if not m:
        m = re.search(r"localStorage\.setItem\(`beeftv-project-cover:.*?`\);", card, re.S)
    body = m.group(0) if m else card
    return ("localStorage.setItem(`beeftv-project-cover:" in card
            and "localStorage.getItem(`beeftv-project-cover:" in card
            and "updateProject" not in body)


def p_director_scenes_not_synced(src):
    """导演台场景只改本地：updateProject 写 directorScenes，且该文件零同步调用。"""
    body = git_show(src, "web/src/pages/canvas/use-canvas-director.ts")
    if not body:
        return None
    if "updateProject(projectId, { directorScenes" not in body:
        return False
    return not re.search(r"syncLocalCanvasProject|scheduleLocalCanvasBackendSync|"
                         r"persistCanvasDocument|flushCanvasStorePersistence", body)


def p_stay_acceptance_only(src):
    """`?stay=1`：源码注释自认是留给浏览器验收脚本的开关，界面上没有任何入口。"""
    body = git_show(src, "web/src/pages/canvas/index.tsx")
    if not body:
        return None
    return 'searchParams.get("stay")' in body and "验收脚本" in body


def p_rename_two_names(src):
    """一张画布两个名字：顶栏切换器读 canvasTitle，画布库卡片读 title，互不同步。

    判据要求三处同时成立，缺一即上游已改：
      (a) 顶栏把 projectCanvases 的 title 映射为 `canvasTitle?.trim() || 画布 N`；
      (b) 画布库卡片的 aria-label / 标题用 `project.title`；
      (c) 顶栏菜单的「重命名画布」写的是 `canvasTitle`，而库内行内重命名写 `title`
          ——(c) 是关键：只有 (a)(b) 时可能只是两处显示不同源，若写入字段也分开，
          就是「改了一处另一处不跟着变」的双向割裂。
    """
    proj = git_show(src, "web/src/pages/canvas/project.tsx")
    bar = git_show(src, "web/src/pages/canvas/canvas-project-top-bar.tsx")
    card = git_show(src, "web/src/components/canvas/canvas-folder-card.tsx")
    if not proj or not bar or not card:
        return None
    # (a)
    mapped = re.search(r"const canvasProjects = useMemo\(\s*\(\)\s*=>\s*workspaceCanvases\.map\(\(project, index\) => \(\{\s*"
                        r"id: project\.id,\s*title: project\.canvasTitle\?\.trim\(\)", proj, re.S)
    if not mapped:
        return False
    # (b) 库内卡片用 title
    if not re.search(r"aria-label=\{`\$\{project\.title\} 画布操作`\}", card):
        return False
    # (c) 写入字段分开
    m = re.search(r"const renameCanvasFromMenu = useCallback\(async.*?\n    \}, \[", proj, re.S)
    if not m or "canvasTitle" not in m.group(0):
        return False
    m2 = re.search(r"const saveTitle = async \(\) => \{.*?\n    \};", card, re.S)
    if not m2 or "renameProject(project.id" not in m2.group(0) or "canvasTitle" in m2.group(0):
        return False
    return "canvasLabel" in bar and "canvas.title" in bar


def p_rename_not_synced(src):
    """改名同样绕过了带后端同步的保存路径：两处改名都只有 flushCanvasStorePersistence。

    ⚠️ 同样要说准范围（Batch 137 实测）：**画布库改的名会被下一次内容保存顺带存上去**
    （它写的是 title，后端收）；**顶栏改的名永远不会**（它写 canvasTitle，后端不收这个
    字段）。所以本条断言是「改名动作本身不触发上传」，不是「改名永远不落盘」。

    与 p_copy_not_synced 同族但**不是同一条**：复制的问题是新项目没被上传，
    改名的问题是**已有项目的元数据没被上传**，而对照组（createLocalCanvasProject）
    在两处都带 syncLocalCanvasProjectToBackend。判据要求：
      (a) 两处改名函数体内都没有 syncLocalCanvasProjectToBackend；
      (b) 都有 flushCanvasStorePersistence（证明确实写了本地缓存，只差远端那一步）；
      (c) 对照组 createLocalCanvasProject 仍然带同步。
    """
    proj = git_show(src, "web/src/pages/canvas/project.tsx")
    card = git_show(src, "web/src/components/canvas/canvas-folder-card.tsx")
    repo = git_show(src, "web/src/services/local-workspace-repository.ts")
    if not proj or not card or not repo:
        return None
    m = re.search(r"const renameCanvasFromMenu = useCallback\(async.*?\n    \}, \[", proj, re.S)
    if not m:
        return False
    body = m.group(0)
    if "syncLocalCanvasProjectToBackend" in body:
        return False
    if "flushCanvasStorePersistence" not in body:
        return False
    m2 = re.search(r"const saveTitle = async \(\) => \{.*?\n    \};", card, re.S)
    if not m2 or "syncLocalCanvasProjectToBackend" in m2.group(0):
        return False
    if "flushCanvasStorePersistence" not in m2.group(0):
        return False
    m3 = re.search(r"export async function createLocalCanvasProject.*?\n\}", repo, re.S)
    return bool(m3) and "syncLocalCanvasProjectToBackend" in m3.group(0)


def _fn_body(text, header, terminator="\n}"):
    """取出 `export function <header>` 到函数结束的原文（找不到返回空串）。

    ⚠️ **两个写过的坑（Batch 139 自踩，两轮都首轮报失效、理由却是假的）**：
      ① 不要在 header 后面加 `\\b`——header 以 `)` 结尾时，`)` 与其后的空格
         都是非词字符，词边界永远不成立，会让每个以括号收尾的函数都「找不到」；
      ② 不要把前缀写死成 `export function `——`loadAssetLibraryPage` 是
         `export async function`，写死不匹配。
    """
    m = re.search(r"export (?:async )?function " + re.escape(header) + r".*?" + terminator, text, re.S)
    return m.group(0) if m else ""


def p_asset_sync_gated_off(src):
    """素材侧的每个同步出口都挂在写死的常量上；对照组：画布内容那条路没有关卡。

    这是 Batch 139 的头条判据。**只查「素材存本地」是不够的**——那只能说明结果，
    说明不了原因；本判据要钉住的是「三个常量把远端分支全关掉了」这个机制，
    否则上游哪天把常量改回来，手册会继续言之凿凿地说「只在本机」。

    判据要求（缺一即判失效）：
      (a) hasRemoteUserDataSyncSession() 函数体是 return false —— 上传收尾的同步开关；
      (b) isLocalWorkspaceMode() 函数体是 return true —— 「本地工作区」判定；
      (c) workspaceCapabilities() 里 local 是字面量 true —— 页面 remoteMode 的来源；
      (d) 素材页确实按 remoteMode 分叉：列表查询 enabled: remoteMode、
          新建文件夹 if (!remoteMode) 走本地、else 才调 createAssetFolder；
      (e) 那个叫 loadAssetLibraryPage 的「远端」取数函数读的其实是本地 store
          ——**名字叫 remote 却读本地**，这是最容易骗过只看名字的读者的地方；
      (f) 对照组：画布内容保存路径上**没有**这道关卡（syncLocalCanvasProject
          直接 http.put）。少了 (f) 就会把结论写成「什么都不上传」，
          而手册另一处明写画布内容确实会上传——两份说法会互相打架。
    """
    wsm = git_show(src, "web/src/services/workspace-mode.ts")
    sync = git_show(src, "web/src/services/local-workspace-sync.ts")
    idx = git_show(src, "web/src/pages/assets/index.tsx")
    repo = git_show(src, "web/src/services/local-workspace-repository.ts")
    if not wsm or not sync or not idx or not repo:
        return None
    # (a) 同步会话判定恒假
    body = _fn_body(sync, "hasRemoteUserDataSyncSession()")
    if not body or "return false" not in body:
        return False
    # (b) 本地工作区判定恒真
    body = _fn_body(wsm, "isLocalWorkspaceMode()")
    if not body or "return true" not in body:
        return False
    # (c) 能力快照的 local 是写死的字面量
    caps = re.search(r"export function workspaceCapabilities\(\).*?\n\}", wsm, re.S)
    if not caps or not re.search(r"\blocal:\s*true\b", caps.group(0)):
        return False
    # (d) 素材页按 remoteMode 分叉
    if not re.search(r"const remoteMode = Boolean\(userId\) && !localWorkspace", idx):
        return False
    if "enabled: remoteMode" not in idx:
        return False
    save_folder = re.search(r"const saveFolder = async \(\) => \{.*?\n    \};", idx, re.S)
    if not save_folder:
        return False
    sf = save_folder.group(0)
    if not re.search(r"if \(!remoteMode\)", sf):
        return False
    if "createAssetFolder" not in sf:
        return False
    # (e) 「远端」取数函数其实读本地 store
    page = _fn_body(sync, "loadAssetLibraryPage(options: LocalAssetPageOptions)", "\n}")
    if not page or "useAssetStore.getState().assets" not in page:
        return False
    # (f) 对照组：画布内容保存无条件 PUT，没有这道关卡
    canvas_sync = re.search(r"function syncLocalCanvasProject\(.*?\n\}", repo, re.S)
    if not canvas_sync:
        return False
    cs = canvas_sync.group(0)
    if "http.put" not in cs:
        return False
    return "hasRemoteUserDataSyncSession" not in cs


def p_asset_list_endpoint_uncalled(src):
    """服务端的素材列表接口实现完整，但前端零处调用。

    与 p_asset_sync_gated_off 互补：那条钉「远端分支跑不到」，这条钉
    「就算跑到了也没有东西可调」。两条都在，才敢说「素材这一侧没有服务端出口」。

    判据要求：
      (a) 后端注册了 GET /assets，且带分页与筛选（hasUserAssetPageFilters）；
      (b) 前端**没有任何一处**发起该 GET——用 git grep 扫全 web/src，
          只认 http 客户端调用形态，路由路径 "/assets" 不算。
    """
    handler = git_show(src, "backend/internal/handler/user_data.go")
    if not handler:
        return None
    if not re.search(r'r\.GET\("/assets"', handler):
        return False
    if "hasUserAssetPageFilters" not in handler or "UserAssetsPage" not in handler:
        return False
    r = subprocess.run(
        ["git", "grep", "-n", "-E",
         r"http\.(get|request|fetch)<[^>]*>\(\s*[\"\']/assets[\"\']",
         REF, "--", "web/src"],
        cwd=src, capture_output=True, text=True)
    if (r.stdout or "").strip():
        return False
    return True



def p_test_voice_page_no_ui_entry(src):
    """语音录制测试页挂在生产路由里，但界面上没有任何入口，只能手敲网址。

    与 p_stay_acceptance_only 同族：都是「路由能进、界面进不去」，但成因不同——
    `stay` 是一个查询参数，这个是**一整个测试页面**（源码注释自述「验证输入行内联波形录制和
    STT 转写闭环」），却和正式页面一样注册进了生产路由。

    判据要求三件事同时成立：
      (a) router.tsx 确实注册了 /test-voice-recording；
      (b) 页面文件存在且带测试页特征（源码注释里的「测试」字样）；
      (c) **全 web/src 零处导航到它**——只允许 router.tsx 的 import 与页面自身，
          侧栏、命令面板、快捷入口里都不能出现。少了 (c) 就只能证明「没在侧栏里」，
          证明不了「界面上没有入口」。
    """
    router = git_show(src, "web/src/router.tsx")
    page = git_show(src, "web/src/pages/test-voice-recording.tsx")
    if not router or not page:
        return None
    if not re.search(r'path: "/test-voice-recording"', router):
        return False
    if "测试" not in page:
        return False
    r = subprocess.run(
        ["git", "grep", "-n", "-E", r'"/test-voice-recording"', REF, "--", "web/src"],
        cwd=src, capture_output=True, text=True)
    for line in (r.stdout or "").split("\n"):
        if not line.strip():
            continue
        m = re.match(rf"^{re.escape(REF)}:(.+?):(\d+):", line)
        if not m:
            continue
        path = m.group(1)
        if path in ("web/src/router.tsx", "web/src/pages/test-voice-recording.tsx"):
            continue
        return False
    return True



def p_retired_task_skill_pages(src):
    """任务中心与技能页已退场：路由只留重定向，源码模块整体无人引用。

    Batch 139/140 的覆盖度普查量出来的：手册早已写明「旧链接会静默跳回首页」，
    但**没人记下这些模块还有多少行留在仓库里**——本批量出 **2354 行**
    （pages/tasks 1221 行 + pages/skills 1133 行）。

    判据要求四件事同时成立：
      (a) router.tsx 对 /tasks、/skills、/skill、/skills/reference 四个路径
          **一律是 `<Navigate to="/" replace />`**，没有一个是真正的页面；
      (b) router.tsx **不 import** 这些页面（否则就不是「只剩重定向」）；
      (c) 全 web/src **零处 import** @/pages/tasks；
      (d) @/pages/skills 的 import **只发生在它自己目录内部**（自引用不算外部引用）。
          少了 (d) 就会漏判「被别的模块引用的半死代码」。
    """
    router = git_show(src, "web/src/router.tsx")
    if not router:
        return None
    for path in ("/tasks", "/skills", "/skill", "/skills/reference"):
        # ⚠️ path 与 element 之间**可能夹着注释**（`/tasks` 就是：上游写了
        # 「任务页暂不开放，保留路由以避免旧链接进入半成品界面。」）。
        # 用 \s* 匹配会漏掉这种写法，判据首轮就误报失效——Batch 135「判据要覆盖
        # 上游各种写法」的第 N 次应验，这里换成 [\s\S] 并限长。
        if not re.search(r'path: "' + re.escape(path) + r'",[\s\S]{0,200}?element: <Navigate to="/" replace />', router):
            return False
    if re.search(r'import .*@/pages/(tasks|skills)', router):
        return False
    for prefix in ("@/pages/tasks", "@/pages/skills"):
        r = subprocess.run(["git", "grep", "-n", "-F", prefix, REF, "--", "web/src"],
                           cwd=src, capture_output=True, text=True)
        for line in (r.stdout or "").split("\n"):
            if not line.strip():
                continue
            m = re.match(rf"^{re.escape(REF)}:(.+?):(\d+):", line)
            if not m:
                continue
            if m.group(1).startswith("web/src/pages/tasks") or m.group(1).startswith("web/src/pages/skills"):
                continue  # 目录内自引用
            return False
    return True



def p_image_toolbar_omits_tools(src):
    """图片节点工具条上「复制提示词 / 反推提示词 / 质感调整 / 全景图」都点不到。

    手册 90-troubleshooting 有一条用户求助「图片节点工具条上找不到这几项」。
    本判据把那条否定式断言钉住，并且**区分两种不同的「找不到」**——
    这是本条最容易被搞混、也最容易被写错的地方：

      · 「复制提示词 / 反推提示词」在 group **"more"**，
        而 canvas-node-toolbar **全库零处引用这个分组** → **任何节点类型都点不到**；
      · 「质感调整」在 group "portrait"，但图片分支把该组**只保留 emotion**
        → **图片节点上没有，非图片节点上有**；
      · 「全景图」在 group "panorama"，渲染处写的是
        `compact || isImage ? [] : inGroup("panorama")` → **同样只对图片节点隐藏**。

    判据要求：
      (a) 四个 id 确实存在于 imageToolDefinitions；
      (b) copyPrompt / reversePrompt 的 group 是 "more"；
      (c) 工具条**零处**引用 "more" 分组（证明是「永不渲染」而非「渲染了但条件隐藏」）；
      (d) 质感调整（portraitTexture）在 "portrait" 组，且图片分支把该组过滤成只剩 emotion；
      (e) **对照组**：panorama 组**确实有**渲染处，且带 `isImage` 条件。
          少了 (e)，(c) 的「零引用」就可能只是我 grep 写窄了——**而这恰恰是本批
          自己踩过的坑**（两次把正确的手册断言误判成错的，都因为 grep 太窄）。
    """
    defs = git_show(src, "web/src/components/canvas/canvas-image-toolbar-tools.tsx")
    bar = git_show(src, "web/src/components/canvas/canvas-node-toolbar.tsx")
    if not defs or not bar:
        return None
    # (a)(b) 四个 id 及其分组
    for tool_id in ("copyPrompt", "reversePrompt", "portraitTexture", "panorama"):
        if not re.search(r'id: "' + tool_id + r'"', defs):
            return False
    for tool_id in ("copyPrompt", "reversePrompt"):
        m = re.search(r'id: "' + tool_id + r'",(?:(?!\n    \},).)*?group: "([^"]+)"', defs, re.S)
        if not m or m.group(1) != "more":
            return False
    # (c) "more" 分组零渲染点
    if re.search(r'inGroup\("more"\)', bar):
        return False
    # (d) 质感调整在 portrait 组，且图片分支只留 emotion
    m = re.search(r'id: "portraitTexture",(?:(?!\n    \},).)*?group: "([^"]+)"', defs, re.S)
    if not m or m.group(1) != "portrait":
        return False
    if not re.search(r'isImage \? inGroup\("portrait"\)\.filter\(\(tool\) => tool\.id === "emotion"\)', bar):
        return False
    # (e) 对照组：panorama 组有渲染处且带 isImage 条件
    pm = re.search(r'const panoramaTools = ([^;]+);', bar)
    if not pm or "isImage" not in pm.group(1) or 'inGroup("panorama")' not in pm.group(1):
        return False
    return True



def p_audio_panel_never_offers_pitch_volume(src):
    """音频设置面板从不超过声调与音量——尽管这两块的控件代码就在面板里。

    手册 90-troubleshooting 写「音频设置里没有『声调』『音量』，面板从不提供这两项」。
    这条断言的用处在于**防一个具体的误判**：只看 `audio-settings-panel.tsx` 会看到
    `aria-label="声调"` / `aria-label="音量"` 两个 range 输入框，**很容易据此判定手册写错了**——
    本批就差点这么改。真正的机制是这两块各自挂在 `profile.showPitch` / `profile.showVolume`
    条件下，而**全部档位（minimax-speech / minimax-music）这两个开关都是 false**。

    判据要求：
      (a) 面板里确实存在这两块，且各自被 showPitch / showVolume 包着；
      (b) `audio-generation.ts` 里**每一个**档位定义的 showPitch 都是 false；
      (c) 每一个档位的 showVolume 也是 false；
      (d) 对照组：showVoice / showSpeed 在至少一个档位是 true——
          证明「全 false」不是因为这个字段根本没人用，而是被逐档显式关掉的。
    """
    panel = git_show(src, "web/src/components/audio-settings-panel.tsx")
    lib = git_show(src, "web/src/lib/audio-generation.ts")
    if not panel or not lib:
        return None
    if 'aria-label="声调"' not in panel or 'aria-label="音量"' not in panel:
        return False
    if not re.search(r"profile\.showPitch \?", panel) or not re.search(r"profile\.showVolume \?", panel):
        return False
    # 逐档位取 show* 的取值
    def values(flag):
        return re.findall(flag + r":\s*(true|false)", lib)
    for flag in ("showPitch", "showVolume"):
        vals = values(flag)
        if not vals:
            return False
        if any(v == "true" for v in vals):
            return False
    # 对照组
    for flag in ("showVoice", "showSpeed"):
        if "true" not in values(flag):
            return False
    return True



def p_simple_mode_hardcoded(src):
    """「简易模式 / simple 模式」开关被硬编码成 professional，界面上没有这个切换。

    手册 create-nodes.md 与 90-troubleshooting.md 都有「找不到简易模式开关」这一条。
    它和 `canvas-readonly-no-ui-entry` 属同一族，但**成因不同**：只读模式是
    「功能完整但没有入口」，而简易模式是**「入口的取值被一个常量焊死」**——
    所以它连「参数扫描」都扫不到（根本没写成 URL 参数）。

    判据要求：
      (a) project.tsx 里 workspaceMode 是**字面量常量** "professional"；
      (b) 全 web/src **零处**把 workspaceMode 赋成 "simple"；
      (c) **对照组**：组件里 `simpleMode = workspaceMode === "simple"` 这段分支
          代码确实存在，且多个组件的默认值也是 "professional"
          ——证明这不是「压根没写过简易模式」，而是**写了但永远进不去**。
          少了 (c)，(a)(b) 也可能只是「这个功能根本不存在」，那手册该写的
          就是「产品没这个功能」而不是「切换被硬编码」。
    """
    proj = git_show(src, "web/src/pages/canvas/project.tsx")
    composer = git_show(src, "web/src/components/canvas/canvas-config-composer.tsx")
    if not proj or not composer:
        return None
    # (a) 硬编码字面量
    m = re.search(r"const workspaceMode: CanvasWorkspaceMode = \"(\w+)\";", proj)
    if not m:
        return False
    if m.group(1) != "professional":
        return False
    # (b) 全库没有把 workspaceMode 赋成 simple 的地方
    r = subprocess.run(["git", "grep", "-n", "-E",
                        r'workspaceMode[^\n]{0,40}=\s*\{?\s*"?simple"?',
                        REF, "--", "web/src"],
                       cwd=src, capture_output=True, text=True)
    if (r.stdout or "").strip():
        return False
    # (c) 对照组：simpleMode 分支存在，且默认值是 professional
    if 'workspaceMode === "simple"' not in composer:
        return False
    if 'workspaceMode = "professional"' not in composer:
        return False
    return "simpleMode" in composer


def p_canvas_locks_unsupported_message(src):
    """浏览器缺 Web Locks 时会抛那句固定文案——但这个能力全库四处都在用。

    手册 90-troubleshooting.md 有一条症状「当前浏览器不支持跨标签存储锁，已停止画布生成持久化」。
    这是一条**条件性**断言：它只在浏览器没有 `navigator.locks` 时成立。
    登记它是为了防两件事：① 上游删掉这条提示；② 上游把整个锁机制删掉
    ——那时手册应改写成「不再需要现代浏览器」。

    判据要求：
      (a) use-canvas-store.ts 里探测 navigator.locks，且**不支持时抛出该文案**；
      (b) **对照组**：全库至少 3 处使用 navigator.locks
          ——证明这是**在用的机制**而不是残留代码。
          少了 (b)，「不支持时报错」也可能只是一段没人走的死路径。
    """
    store = git_show(src, "web/src/stores/canvas/use-canvas-store.ts")
    if not store:
        return None
    if "navigator.locks" not in store:
        return False
    if "当前浏览器不支持跨标签存储锁，已停止画布生成持久化" not in store:
        return False
    r = subprocess.run(["git", "grep", "-l", "-F", "navigator.locks", REF, "--", "web/src"],
                       cwd=src, capture_output=True, text=True)
    files = [x for x in (r.stdout or "").split("\n") if x.strip()]
    return len(files) >= 3


def p_canvas_folders_not_nested(src):
    """画布库的文件夹是**一级分组**：数据结构里没有表达嵌套的字段。

    手册 manage-canvases.md 写「文件夹是画布库的一级分组，没有嵌套」。
    这条断言的特别之处在于：它**不需要扫调用点**就能判——只要看类型定义。
    上游哪天给 `CanvasFolder` 加了 `parentId`，这句话就过期了。

    判据要求：
      (a) `CanvasFolder` 类型体里**没有任何指向另一个文件夹的字段**
          （不能出现 folderId / parentId / parentFolderId 之类）；
      (b) 层级关系只由**项目侧**的 `folderId` 表达——即挂载点永远是「画布→文件夹」，
          而不是「文件夹→文件夹」；
      (c) **对照组**：素材库的文件夹类型**确实带 `parentId`**，且有递归渲染
          ——证明 (a) 不是「全库都不支持嵌套」这种泛泛事实，
          而是**画布库特有的扁平设计**。少了 (c)，一旦上游哪天给素材库
          也去掉了 parentId，这条判据就会跟着一起失效，两处退化互相掩护。
    """
    store = git_show(src, "web/src/stores/canvas/use-canvas-store.ts")
    if not store:
        return None
    m = re.search(r"export type CanvasFolder = \{(.*?)\n\};", store, re.S)
    if not m:
        return False
    body = m.group(1)
    # (a) 类型体里不得有指向文件夹的引用字段
    if re.search(r"\b(parent\w*Folder\w*|folderId|parentId|children|subfolder\w*)\b", body):
        return False
    # (b) 层级由项目侧 folderId 表达
    if "folderId" not in store:
        return False
    if not re.search(r"project\.folderId", store):
        return False
    # (c) 对照组：素材库文件夹带 parentId，且有递归渲染
    picker = git_show(src, "web/src/components/assets/asset-library-picker-modal.tsx")
    if not picker:
        return None
    if "folder.parentId" not in picker:
        return False
    return "depth" in picker


def p_feature_availability_readonly(src):
    """功能开放配置（features）**只读**：HTTP 层只注册了 GET，没有任何写入路由。

    手册 plugins-management.md 说「分区挂在 `customChannelsEnabled` 特性开关之后……
    这需要管理员开权限」。这句话**在本地部署下会误导读者**：本地用户角色
    确实是 admin（local_identity.go 里 `Role: model.UserRoleAdmin`），
    看起来「自己去开就行」，但界面和 API 上**根本没有写入路由**。

    登记它是为了防上游把写入口补上——那时手册该改写成「可以自己开」。

    判据要求：
      (a) `RegisterDesktopFeatureAvailabilityRoutes` 里**只**注册了 `GET /features`；
      (b) service 层的写入方法 `UpdateFeatureAvailability` 在 handler/cmd 层**零调用**；
      (c) **对照组**：读取侧确实**在用**——GET 路由存在，且 `FeatureEnabled` 守卫
          被多处业务代码调用。
          少了 (c)，(a)(b) 可能只是「features 整套没人用」，那手册该说的是
          「功能开放配置不影响任何行为」而不是「没有写入入口」。
    """
    handler = git_show(src, "backend/internal/handler/feature_availability.go")
    if not handler:
        return None
    # (a) 路由表里只有 GET，没有 POST/PUT/PATCH/DELETE
    methods = re.findall(r'\br\.(GET|POST|PUT|PATCH|DELETE)\(', handler)
    if not methods:
        return False
    if set(methods) != {"GET"}:
        return False
    if "/features" not in handler:
        return False
    # (b) 写入方法在 handler / cmd 层零调用
    r = subprocess.run(["git", "grep", "-n", "-E",
                        r"\.UpdateFeatureAvailability\(",
                        REF, "--", "backend/internal/handler", "backend/cmd"],
                       cwd=src, capture_output=True, text=True)
    if (r.stdout or "").strip():
        return False
    # service 层必须仍然保留该方法——否则这条就不是「没有入口」而是「功能已删」
    bridge = git_show(src, "backend/internal/app/platform_bridge.go")
    if not bridge or "UpdateFeatureAvailability" not in bridge:
        return False
    # (c) 对照组：读取侧在用
    r2 = subprocess.run(["git", "grep", "-l", "-F", "FeatureEnabled", REF, "--", "backend"],
                        cwd=src, capture_output=True, text=True)
    files = [x for x in (r2.stdout or "").split("\n") if x.strip()]
    return len(files) >= 3


def p_art_critique_two_layers(src):
    """审美批改的输入校验**分两层且不一致**：节点取第一张，弹窗要求恰好一张。

    手册 art-critique.md 原写「恰好连 1 张……**不是「取第一张」，是直接判定无效**」——
    而「取第一张」恰恰是**节点内容区的真实行为**，我拿源码的行为当反例去反驳它。

    判据要求：
      (a) 节点侧 `const input = imageInputs[0]`（取第一张）**且**标题栏
          明写「使用第一张」，**且** `canOpen` 只要求「有图」——多张时仍可打开；
      (b) 弹窗侧 `images.length === 1 ? images[0] : undefined`（恰好一张）
          **且**按钮 `disabled` 依赖 `!input` **且**有「请连接且仅连接一张」的报错文案；
      (c) **对照组**：两处**确实都存在**（不是只有一层）。
          少了 (c)，上游哪天统一了两层行为，这条判据应当失效——
          那时手册要改写成「现在节点和面板一致取第一张」，而不是继续说「两层不一致」。
    """
    node = git_show(src, "web/src/components/canvas/nodes/ai-art-critique-node.tsx")
    modal = git_show(src, "web/src/components/canvas/art-critique/ai-art-critique-modal.tsx")
    if not node or not modal:
        return None
    # (a) 节点侧取第一张
    if "const input = imageInputs[0];" not in node:
        return False
    if "使用第一张" not in node:
        return False
    if not re.search(r"const canOpen = Boolean\(state\.report\) \|\| \(enabled && Boolean\(input\)\);", node):
        return False
    # (b) 弹窗侧恰好一张
    if "images.length === 1 ? images[0] : undefined" not in modal:
        return False
    if "请连接且仅连接一张已有图片" not in modal:
        return False
    if "disabled={running || !input || !enabled || !selectedCritiqueModel}" not in modal:
        return False
    return True


def p_style_execution_policy_two_branches(src):
    """画风资产的执行策略是**可切换的两分支**，默认「兼容降级」——不是「恒被挡住」。

    手册 organize-canvas.md 原写「LoRA ❌ **恒被挡住**」，把一个开关的**两个取值**
    压平成了单一结论。源码文案本身就写了两句并列的话：
    「兼容降级会继续执行项目 Prompt；严格策略会在生成前阻止任务」。

    判据要求：
      (a) `executionPolicy` 是**二值枚举**且默认值是 `compatible-fallback`；
      (b) 只有 `strict-assets` 且存在被拦素材时才 `strictBlocked`，
          否则状态是 `degraded`（降级放行）——**证明默认路径不阻止**；
      (c) **对照组**：界面上**能切**这个策略（下拉里有「兼容降级」/「严格阻止」两个选项）。
          少了 (c)，(a)(b) 可能只是两段没人走的死代码；
          那样手册该说的是「策略写死了、切不了」，而不是「默认放行、可以切成阻止」。
    """
    profile = git_show(src, "web/src/lib/canvas/style-profile.ts")
    if not profile:
        return None
    # (a) 二值枚举 + 默认值
    if 'executionPolicy?: "compatible-fallback" | "strict-assets";' not in profile:
        return False
    if 'source.executionPolicy || "compatible-fallback"' not in profile:
        return False
    # (b) 只有严格策略才阻止
    if 'const strictBlocked = profile.executionPolicy === "strict-assets"' not in profile:
        return False
    if 'status: strictBlocked ? "blocked" : warnings.length ? "degraded" : "ready"' not in profile:
        return False
    # (c) 对照组：界面可切
    modal = git_show(src, "web/src/components/canvas/style-asset-binding-modal.tsx")
    if not modal:
        return None
    if '{ value: "compatible-fallback", label: "兼容降级" }' not in modal:
        return False
    return '{ value: "strict-assets", label: "严格阻止" }' in modal


def p_channel_page_three_names(src):
    """模型配置页**三个名字并存**，而「个人渠道」作为大标题的分支永不渲染。

    手册 plugins-management.md 原写「标题随部署形态变化：本地部署显示『本地模型渠道』，
    其他形态显示『**个人渠道**』」——但判断用的 `localMode` 来自
    `workspaceCapabilities().local`，而那个 `local` 在代码里**写死为 `true`**，
    所以 else 分支（个人渠道）**渲染不出来**。

    真正在界面上并存的是**三个名字**：侧栏「模型配置」、设置页内分区「个人渠道」
    （无条件字面量）、面板大标题「本地模型渠道」（因为 localMode 恒 true）。

    判据要求：
      (a) `workspaceCapabilities()` 的 `local` 字段是**硬编码 true**；
      (b) 面板标题是 `localMode ? "本地模型渠道" : "个人渠道"` 这种二选一；
      (c) **对照组**：设置页分区的 label 是**无条件字面量「个人渠道」**
          ——证明「个人渠道」这个词确实出现在界面上，只是不作为大标题出现。
          少了 (c)，(a)(b) 会让读者以为界面上根本没有「个人渠道」二字，那是错的。
    """
    mode = git_show(src, "web/src/services/workspace-mode.ts")
    if not mode:
        return None
    if "export type WorkspaceCapabilities = { local: true;" not in mode:
        return False
    if not re.search(r"return \{\s*\n\s*local: true,", mode):
        return False
    pane = git_show(src, "web/src/pages/settings/channel-settings-pane.tsx")
    if not pane:
        return None
    if "const localMode = workspaceCapabilities().local;" not in pane:
        return False
    if 'localMode ? "本地模型渠道" : "个人渠道"' not in pane:
        return False
    # (c) 对照组：分区 label 是**无条件字面量**——不是三元、不是条件表达式。
    #     第一版这里写的是 `return "侧栏" not in settings`，那是个**语义模糊的字符串检查**：
    #     它既说不清「为什么要查侧栏」，也挡不住任何真实回归
    #     （把 label 改成 `cond ? "个人渠道" : "x"` 它照样通过）。换成有意义的形态判定。
    settings = git_show(src, "web/src/pages/settings/index.tsx")
    if not settings:
        return None
    if '{ key: "channels", label: "个人渠道"' not in settings:
        return False
    return not re.search(r'label:\s*\w+\s*\?[^,]*个人渠道', settings)


# 第 4 个字段 scan_key = (文件, setter 名)，表示该条**同时**能被方向二的
# 全量 setter 扫描覆盖；为 None 表示**只有专属判据**（判据形态不同，
# 例如「ref 零 click」或「路由先 Navigate」，setter 扫描天然照不到）。
# 方向二只对有 scan_key 的条目要求「必须扫到」——否则会把形态不同的判据
# 误判成登记表写错（本闸首次运行就犯了这个错，被自己的双向检查抓出来）。
REGISTRY = [
    ("canvas-library-no-sort-filter", "画布库无排序/筛选控件", p_sort_filter,
     (("web/src/pages/canvas/index.tsx", "setSort"),
      ("web/src/pages/canvas/index.tsx", "setProjectFilter"))),
    ("canvas-library-no-import-entry", "画布库无导入入口", p_import_entry, None),
    ("canvas-library-no-join-project", "「加入项目/移出项目」恒不渲染", p_join_project, None),
    ("art-critique-no-create-entry", "AI 审美批改节点无创建入口", p_art_critique_entry, None),
    ("art-critique-no-autostart", "审美批改「打开即自动开始」路径已死", p_art_critique_autostart,
     (("web/src/pages/canvas/project.tsx", "setArtCritiqueStartRequest"),)),
    ("projects-library-dead", "pages/projects 项目库模块零引用", p_projects_library_dead, None),
    ("chapters-workflow-routes-unreachable", "章节/工作流深路由恒被改写",
     p_chapter_workflow_routes, None),
    ("canvas-readonly-no-ui-entry", "只读画布模式界面上无入口", p_readonly_no_ui_entry, None),
    ("canvas-copy-never-uploaded", "顶栏/只读复制的副本只写本地、从不上传",
     p_copy_not_synced, None),
    ("canvas-stay-acceptance-only", "画布库 `?stay=1` 只为验收脚本存在", p_stay_acceptance_only, None),
    ("canvas-two-names", "一张画布两个名字：顶栏与画布库互不同步",
     p_rename_two_names, None),
    ("canvas-rename-never-uploaded", "画布改名（两处）当次不上传",
     p_rename_not_synced, None),
    ("canvas-autosave-watches-content-only", "自动保存只盯内容字段、不含名字",
     p_content_watcher_excludes_title, None),
    ("canvas-folders-local-only", "画布库文件夹纯属本机（服务端只有素材文件夹）",
     p_canvas_folders_are_local, None),
    ("canvas-cover-localstorage-only", "画布封面只存 localStorage",
     p_canvas_cover_is_localstorage, None),
    ("director-scenes-not-synced", "导演台场景只写本地、从不上传",
     p_director_scenes_not_synced, None),
    ("asset-sync-gated-off", "素材侧每个同步出口都挂在写死的常量上（画布内容没有）",
     p_asset_sync_gated_off, None),
    ("asset-list-endpoint-uncalled", "服务端素材列表接口实现完整但前端零处调用",
     p_asset_list_endpoint_uncalled, None),
    ("test-voice-page-no-ui-entry", "语音录制测试页挂在生产路由但界面无入口",
     p_test_voice_page_no_ui_entry, None),
    ("retired-task-skill-pages", "任务中心与技能页已退场：路由只留重定向、模块整体零引用",
     p_retired_task_skill_pages, None),
    ("image-toolbar-omits-tools", "图片节点工具条上四项点不到（且区分「永不渲染」与「只对图片隐藏」）",
     p_image_toolbar_omits_tools, None),
    ("audio-panel-no-pitch-volume", "音频设置面板从不超过声调与音量（控件存在但全档位关闭）",
     p_audio_panel_never_offers_pitch_volume, None),
    ("simple-mode-hardcoded", "简易模式开关被硬编码为 professional，界面无此切换",
     p_simple_mode_hardcoded, None),
    ("canvas-locks-unsupported-message", "浏览器缺 Web Locks 时抛固定文案（该能力全库在用）",
     p_canvas_locks_unsupported_message, None),
    ("canvas-folders-not-nested", "画布库文件夹是一级分组，类型层就没有嵌套字段（素材库有）",
     p_canvas_folders_not_nested, None),
    ("feature-availability-readonly", "功能开放配置只读：只注册了 GET，写方法在 handler 层零调用",
     p_feature_availability_readonly, None),
    ("art-critique-two-layers", "审美批改输入校验分两层且不一致：节点取第一张、弹窗要求恰好一张",
     p_art_critique_two_layers, None),
    ("style-execution-policy-two-branches", "画风执行策略是可切换两分支，默认兼容降级（不是「恒被挡住」）",
     p_style_execution_policy_two_branches, None),
    ("channel-page-three-names", "模型配置页三个名字并存，「个人渠道」作大标题的分支永不渲染",
     p_channel_page_three_names, None),
]


# ── 方向三：URL 参数「只读不写」 ──────────────────────────────────────
# 全库每个 searchParams.get("X") 的 X，若源码里没有任何「写出点」，
# 就意味着**界面上没有任何动作能产生这个参数**。
#
# 写出点的判定口径（Batch 135 踩了两次坑才定下来，**别再收窄**）：
#   ① `next.set("status", v)`：接收者不叫 searchParams，故任何 `.set(`/`.append(` 都认；
#   ② `to: "/canvas?mode=new&add=video"`：URL 放在**数据对象**里再当 prop 传，
#      源码根本不出现 `to=` / `navigate(`。故最终退到最保守的
#      **「任何字符串字面量里含 `?X=` 或 `&X=` 即算有生产者」**。
#      代价是可能漏报（动态拼 URL），方向是安全的；收窄则会误报「界面进不去」——
#      那等于在手册里写假话，代价不可接受。
URL_WRITE_PATTERNS = [  # 保留给人工查阅；实现已并入 url_params_without_writer 的单遍扫描
    re.compile(r"[\"'`][^\"'`\n]{0,300}?[?&]{P}\s*="),
    re.compile(r"\.\s*(set|append)\s*\(\s*[\"']{P}[\"']"),
]

# 零写出但**不是缺陷**的参数——每个都必须写明理由，且理由要能被抽查。
# 判据是「查过来源」，不是「看起来像」：设计成由外部提供的深链，其生产者
# 本来就不在界面里（粘贴框、外部启动器、别的系统），零写出是正常的。
#
# ⚠️ 本名单只覆盖**严格档扫得到的**参数。`agent` 与 `fixture` 经人工查证同样
# 没有界面入口，但源码注释里出现过 `?agent=` / `?fixture=`，**保守档因此扫不到
# 它们**——闸门不跟踪它们，手册 20-reference 里关于这两个参数的表述只由源码证据
# 支撑。宁可让闸门少管两个，也不放宽判据去迁就名单。
URL_PARAM_EXEMPT = {
    "fixtureMedia": "演示画布数据的媒体资源参数，与 fixture 配套；界面无入口",
    "libtvChrome": "演示用 LibTV 顶栏外观开关，与 fixture 配套；界面无入口",
    "history": "画布库回收站的 URL 变体；界面另有直接按钮打开同一弹窗，不靠 URL",
    "uuid": "projectId 的解析别名；入口是「粘贴 LibTV 项目链接」的输入框，"
            "值来自剪贴板而非导航，故零导航写出属正常",
    "demo": "/create 的固定数据演示模式，页面顶部有明示横幅，属演示设施",
}

# 零写出且**确为缺陷/受限**的参数 → 登记 id（与 REGISTRY 呼应）。
URL_PARAM_DEFECT = {
    "readonly": "canvas-readonly-no-ui-entry",
    "stay": "canvas-stay-acceptance-only",
}


def url_params_without_writer(src, strict=True):
    """返回 {参数: 读次数}：被 searchParams.get 读、却没有任何写出点的参数。

    写出点判定**大小写不敏感**——否则 baseUrl / baseurl、projectId / uuid
    这类别名对会被误报成「零写出」。Batch 135 首次运行就撞上了：我把 `baseurl`
    登记成豁免项，闸门反查却发现它在大小写不敏感口径下**有**写出点——它就是
    `baseUrl` 的同一个参数（读取处刻意同时接受两种大小写）。**宁可让别名一起
    脱零写出，也不要手工豁免**：豁免名单一旦靠「我记得它其实是同一个参数」来
    维持，就等于给闸门开后门。

    实现上**只把全库文本扫一遍**（Batch 135 第一版按参数逐个全量重扫，
    20 个参数 × 2 条正则 × 整份 web/src，反向验证要跑十分钟才跑完 9 例）。

    **strict 分两档，因为「判据太窄」的代价是在手册里写假话：**

      · strict=True（**闸门用这一档**）：`?name=` / `&name=` 出现在**任何位置**
        都算写出点，连注释里提到的也算。宁可漏报、闸门变弱，也不误报。
      · strict=False（**只作提示，不参与判定**）：要求 `?name=` 落在引号对内。
        检测力更强，但会被两件事打穿——
          ① 模板字符串**内嵌反引号**（`tasks/index.tsx:551` 的
             `` `/settings?…&projectId=${…}` ``）整段匹配失败，
             把真实导航写点误报成零写出；
          ② 恰恰相反，注释里一句 `?fixture=libtv-text` 就会让该参数脱零写。
        这两件事 Batch 135 都真撞上过，所以宽松档的结果**只打印、不判定**。
    """
    r = subprocess.run(
        ["git", "grep", "-nE", r'searchParams\.get\("([a-zA-Z0-9_-]+)"\)',
         REF, "--", "web/src"], cwd=src, capture_output=True, text=True)
    reads = {}
    for line in (r.stdout or "").split("\n"):
        if not line.strip():
            continue
        for m in re.finditer(r'searchParams\.get\("([a-zA-Z0-9_-]+)"\)', line):
            reads[m.group(1)] = reads.get(m.group(1), 0) + 1
    if not reads:
        return {}

    gr = subprocess.run(["git", "grep", "-h", "-I", "-e", ".", REF, "--", "web/src"],
                        cwd=src, capture_output=True, text=True)
    all_text = gr.stdout or ""

    strict_written = {m.group(1).lower()
                      for m in re.finditer(r"[?&]([A-Za-z0-9_-]+)\s*=", all_text)}
    strict_written |= {m.group(1).lower() for m in re.finditer(
        r"\.\s*(?:set|append)\s*\(\s*[\"']([A-Za-z0-9_-]+)[\"']", all_text)}

    if strict:
        return {p: n for p, n in reads.items() if p.lower() not in strict_written}

    loose_written = set(strict_written)
    for lit in re.finditer(r"[\"'`][^\"'`\n]{0,300}[\"'`]", all_text):
        for m in re.finditer(r"[?&]([A-Za-z0-9_-]+)\s*=", lit.group(0)):
            loose_written.add(m.group(1).lower())
    return {p: n for p, n in reads.items() if p.lower() not in loose_written}


def main():
    src = find_source()
    if not src:
        print("[skip] 未找到 BeefTV 源码，跳过不可达声明核对")
        return 0

    problems = []
    notes = []

    # —— 方向一：登记的断言是否仍成立 ——
    for rid, desc, pred, _scan_key in REGISTRY:
        try:
            res = pred(src)
        except Exception as exc:  # 判据本身出错也要报，不许静默放过
            problems.append(f"[{rid}] 判据执行异常：{exc}")
            continue
        if res is None:
            notes.append(f"  {rid}：未取到相关源码，本轮未判定")
        elif res:
            notes.append(f"  {rid}：{desc} —— 仍成立")
        else:
            problems.append(
                f"[{rid}] {desc} —— **判据已不成立**，上游可能已修复，"
                f"手册对应断言需回走核实后更新"
            )

    # —— 方向二：登记表是否与全量扫描一致 ——
    try:
        hits = zero_call_setters(src)
    except Exception as exc:
        problems.append(f"[scan] 全量扫描执行异常：{exc}")
        hits = None

    if hits is not None:
        # 反向索引：(文件, setter) -> 登记 id
        by_key = {}
        for rid, _desc, _pred, keys in REGISTRY:
            for key in (keys or ()):
                by_key[key] = rid

        for f, names in sorted(hits.items()):
            for sname in names:
                if (f, sname) not in by_key:
                    problems.append(
                        f"[scan] {f} 的 {sname} 声明后零调用，但**不在登记表里** → "
                        f"手册可能漏写了一处「实现了却没接线」"
                    )
        scan_covered = {k for k in by_key}
        actual = {(f, sname) for f, names in hits.items() for sname in names}
        for key in sorted(scan_covered - actual):
            problems.append(
                f"[scan] 登记表项 {by_key[key]} 的扫描键 {key[1]} 本轮未被扫到 → "
                f"该断言可能已失效或登记键写错，登记与现状不一致"
            )
        notes.append(f"  全量 setter 零调用扫描：{len(actual)} 处命中，"
                     f"与登记表中 {len(scan_covered)} 个可扫描条目双向一致"
                     f"（另有 {len(REGISTRY) - len(scan_covered)} 条为专属判据，setter 扫描照不到）")

    # —— 方向三：URL 参数只读不写，须全部归类 ——
    try:
        dead_params = url_params_without_writer(src)
    except Exception as exc:
        problems.append(f"[url] URL 参数扫描执行异常：{exc}")
        dead_params = None

    if dead_params is not None:
        known = {}
        for k, v in URL_PARAM_EXEMPT.items():
            known[k.lower()] = ("豁免", v)
        for k, v in URL_PARAM_DEFECT.items():
            known[k.lower()] = ("登记", v)
        got = {k.lower() for k in dead_params}
        for p_lower in sorted(got - set(known)):
            real = next(k for k in dead_params if k.lower() == p_lower)
            problems.append(
                f"[url] 参数 `{real}`（读 {dead_params[real]} 次）只有读、没有写，"
                f"但**既不在豁免名单也不在缺陷登记里** → 需人工判定它是外部深链还是新缺陷，"
                f"并同步更新 verify-unreachable.py 的 URL_PARAM_EXEMPT / URL_PARAM_DEFECT"
            )
        for p_lower in sorted(set(known) - got):
            real = next((k for k in list(URL_PARAM_EXEMPT) + list(URL_PARAM_DEFECT)
                         if k.lower() == p_lower), p_lower)
            problems.append(
                f"[url] 名单里的参数 `{real}` 本轮**已被扫到写出点** → "
                f"上游已接上入口，手册对应「无入口」表述需回走更新"
            )
        exempt_n = len(URL_PARAM_EXEMPT)
        defect_n = len(URL_PARAM_DEFECT)
        notes.append(f"  URL 参数只读不写扫描（严格档，闸门用）：{len(dead_params)} 个参数零写出，"
                     f"已全部归类（豁免 {exempt_n} 个：外部深链/演示设施/参数别名；"
                     f"登记为缺陷 {defect_n} 个：readonly、stay）")
        # 宽松档只打印、不判定：它的检测力更强，但会被注释与内嵌反引号打穿
        # （见 url_params_without_writer 的 docstring）。
        try:
            loose = url_params_without_writer(src, strict=False)
            only_loose = sorted(set(loose) - set(dead_params))
            if only_loose:
                notes.append(f"  （宽松档另检出 {len(only_loose)} 个疑似零写出参数，"
                             f"仅作提示不参与判定：{', '.join(only_loose)}）")
        except Exception as exc:
            notes.append(f"  （宽松档扫描异常，未提示：{exc}）")

    for n in notes:
        print(n)
    if problems:
        print(f"不可达声明核对：{len(problems)} 处不一致")
        for p in problems:
            print("  ⚠ " + p)
        return 1

    print(f"不可达声明核对：{len(REGISTRY)} 条断言仍成立，setter 扫描与 URL 参数扫描均双向一致"
          f"（不覆盖运行时行为与 pages/projects 目录级死代码，见脚本头声明）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
