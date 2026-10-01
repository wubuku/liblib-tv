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
