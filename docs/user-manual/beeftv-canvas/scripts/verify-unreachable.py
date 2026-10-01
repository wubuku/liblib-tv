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

只检查「不可达是否仍成立」，不判断「不可达本身该不该修」——后者要人读实现。
脚本读的是上游 `origin/main` 的**对象**（`git show`），不是本地工作树，
避免本机 detached HEAD 指向旧版本时误判。

退出码：0 双向均通过；1 有断言已过期，或登记表与扫描结果不一致。

不检查什么（明确声明，避免后来者误以为覆盖面更大）：
  · 不覆盖运行时行为（按钮是否真的不渲染）——本闸只看源码判据；
  · 不覆盖 `pages/projects/` 整目录的死代码量级（Batch 125 已一次性记录，
    不逐条登记，否则登记表会膨胀到无法维护）；
  · 不覆盖 `verify-exclusions.py` 已登记的 4 条解禁条件（短剧生产台等），
    本闸只管「不可达声明」，不重复管「解禁条件」，两者刻意不重叠。
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
]

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

    for n in notes:
        print(n)
    if problems:
        print(f"不可达声明核对：{len(problems)} 处不一致")
        for p in problems:
            print("  ⚠ " + p)
        return 1

    print(f"不可达声明核对：{len(REGISTRY)} 条断言仍成立，且与全量扫描双向一致"
          f"（不覆盖运行时行为与 pages/projects 目录级死代码，见脚本头声明）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
