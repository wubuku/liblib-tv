#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「不可达声明」双向核对闸：手册说「这个功能进不去」的，上游是否仍然进不去。

背景（Batch 133）：手册里最难悄悄过期的一类断言，是**否定式断言**——
「画布库没有导入入口」「审美批改的入口只取决于插件开关」「章节路由访问不到」。
它们不像数值和文案，没有编译期或运行时兜底：上游哪天把那个 `ref.current.click()`
接上、或者把 setter 补上、或者把某个动态入口补上，**手册会继续言之凿凿地
告诉用户「找不到」**，而用户已经在界面上看到了那个按钮。这类过期比过期一个数字更伤害信任。

⚠️ 反过来也成立，而且更隐蔽：**否定式断言可能是从一开始就错的**。
本闸就抓到过一条——曾断言「审美批改节点无创建入口」，判据只是「写死清单里没有它」，
而真正的入口由插件注册表动态生成、根本不经过那份清单。**判据只覆盖了自己看的那个文件，
于是错误被判据「保护」着活了下来**。改判据时务必确认：它锚的是**事实**，还是**某一份文件的样子**。

本闸对每条已登记的「不可达」断言做两件事：

  **方向一（登记项是否仍成立）**：逐条取上游在**取证基线提交**（`module_ref()`，见下）的源码，
  跑该条专属判据。判据**不再成立** = 上游可能已修复 → 手册该条断言已过期 → 退出码 1。
  （**Batch 328 补**：Batch 327 只改了本文件另一段里描述读取来源的那一句，
  **漏掉了这一句**——**同一个概念在一个文件里有两份抄本，只改一份就等于没改**。）

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
脚本读的是上游在**手册声明的取证基线提交**（经 `baseline.module_ref()` 解析，当前
`bcc3b05` = v1.6.22）上的**对象**（`git show`），不是本地工作树，
避免本机 detached HEAD 指向旧版本时误判。
**Batch 327 更正**：此处原先写「读的是上游 `origin/main` 的对象」——`git show` 那半句一直是对的，
`origin/main` 那半句是 Batch 133 写死 ref 时的实况，Batch 175 改走基线后**这句没跟着改**。
**而这个差异在这里有实际后果**：闸 7 在基线上 32 条断言全成立（rc=0），
指向 `BEEFTV_REF=origin/main` 时有 **4 条**不再成立——**「闸是绿的」取决于它读哪个 ref**。

退出码：0 三向均通过；1 有断言已过期，或登记表与扫描结果不一致。

不检查什么（明确声明，避免后来者误以为覆盖面更大）：
  · 不覆盖运行时行为（按钮是否真的不渲染）——本闸只看源码判据；
  · 不覆盖 `pages/projects/` 整目录的死代码量级（Batch 125 已一次性记录，
    不逐条登记，否则登记表会膨胀到无法维护）；
  · 不覆盖 `verify-exclusions.py` 已登记的解禁条件（短剧生产台等），
    本闸只管「不可达声明」，不重复管「解禁条件」，两者刻意不重叠；
  · **方向三不判断「零写出是否就是缺陷」**——它只保证每个零写出参数都被
    显式归类为「已知豁免」或「已登记缺陷」，防止将来上游新增一个无人认领的参数。
  · **`simple-mode-hardcoded` 只认 `=` 赋值，不认对象属性式**（`{ workspaceMode:
    "simple" }`）。**这是故意保留的局限**：实测把 `=` 放宽成 `[:=]` 会立刻误伤
    `workspaceMode === "simple"`（web/src 里 5 处以上，那是**比较**不是写入）。
    **宁可漏照、不可误报**——误报会逼着人加豁免，越修越乱。方向五（第九道闸）
    盯着的是「模式本身会不会被 git 整条拒绝」，那是另一回事。

关于 `git grep` 的三条硬约束（Batch 157 实测，踩过就别再踩）：
  ① `\s` `\d` `\w` `\b` 是**字面字母**，不是字符类 → 要写 `[[:space:]]` 等；
  ② 方括号里的 `\n` 是「反斜杠 + 字母 n」，**排除的是字母 n**，不是换行；
  ③ `{0,N}` 的 **N 不能超过 255**，`{0,n}?` 惰性量词（PCRE）**根本不支持**——
     ②③会让 git **整条拒绝模式并返回 128、stdout 为空**，而空输出在判据里
     与「零命中」等价 → **断言恒真、闸门永远绿**。
     本闸 `p_readonly_no_ui_entry` 就这样当了很久的死代码。
     兜底是所有 git grep 调用统一走 `_git_grep_run()`：**rc ≥ 128 即抛异常**，
     由 main() 报成「判据执行异常」——**工具失败必须与干净的否定结果可区分**。
     静态那一层由第九道闸方向五盯着。
"""

import os
import re
import subprocess
import sys
import beefsrc
from baseline import announce_fallback
from baseline import resolve_ref, BaselineError, module_ref, baseline_guard


# 上游 ref 可用 BEEFTV_REF 覆盖——反向验证（self-test）需要指向一个
# 「缺陷已被修复」的人造 ref，不能改工作树、更不能动别人分支。
REF = module_ref()

#: **Batch 294：判据要钉「这里有一个把画布同步到后端的调用」这个事实，
#: 而不是某一个函数名。**
#:
#: 原先 `p_copy_not_synced` / `p_rename_not_synced` 到处写死
#: `"syncLocalCanvasProjectToBackend"` 这**一个符号名**，而 origin/main 上
#: **同一个文件里并存两个 sync 符号**（旧的 `syncLocalCanvasProjectToBackend`
#: 仍有 7 处、仍被 canvas-archive-restore 与画布库页使用；新的
#: `syncLocalCanvasProject(id, includeGeneratedAssets, scope)` 由 createLocalCanvasProject 调用）。
#:
#: **实测后果**：那两条断言在 origin/main 上被判「判据已不成立，上游可能已修复」，
#: **而它们要钉的行为一个字都没变**——两个复制入口与两处改名入口里
#: **新旧两个符号都不存在**。闸的结论错，方向错得最贵：**它让人去改正文，
#: 而正文仍然是对的**（纪律 328：判据过宽诱导动作，这里是判据过窄诱导改正文）。
#:
#: 顺带关上一个**假绿**：原先那两处入口只查旧名，**若上游把复制路径改成调新符号，
#: 闸照样报「仍成立」**——而副本其实已经会上传了。
#: 所以这四处的查法要**两边同时换成这个正则**：入口处「有同步调用」即失效，
#: 对照组处「没有同步调用」即失效。
CANVAS_SYNC_CALL = re.compile(r"\bsync[A-Za-z0-9_]*CanvasProject[A-Za-z0-9_]*\s*\(")

# ── 工具 ──────────────────────────────────────────────────────────────


def find_source():
    """**Batch 197：路径解析收敛到 `beefsrc` 单一来源**（含"是否走了兜底"）。

    原先这里各带一张 `CANDIDATES` 表，判真条件还不一样
    （本组问 `isdir(c/"backend")`，`quote-punct`/`shot-drift` 问 `isdir(c/".git")`），
    **而 `baseline.py` 又是第三种**——同一个 `BEEFTV_SRC` 在不同闸里会解析成不同的仓。
    实测缺陷：`.git` 目录式判真在 **git worktree 上必然失败**（那里 `.git` 是文件），
    于是用户显式指定的路径被**静默忽略**、改用兜底那份，而闸一声不吭。
    """
    src, is_fallback = beefsrc.resolve_src()
    if src is None:
        return None
    if is_fallback:
        # **Batch 202：措辞收敛到 `baseline.announce_fallback`**——
        # 纪律 172 要 15 道闸都说出「我读的是哪一份」，
        # **而这份措辞不该被手写 8 遍**（又一次「同一份事实被手写多遍」）。
        announce_fallback()
    return src


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


def _declared_once_never_called(src, name):
    """这个 setter 名在 web/src 下**只被声明过一次**，且**全库零调用**。

    ⚠️ **Batch 295：它量的是与 `zero_call_setters` 不同的作用域，而登记表两种都要。**
    `zero_call_setters` 量的是「**声明所在文件内**零调用」——那是**页内作用域**，
    登记表里 `setSort` / `setProjectFilter` 两条要的正是它。
    而 `setArtCritiqueStartRequest` 那条要的是「**全库**零调用」：
    **实测 origin/main 上它被搬到了 `web/src/pages/canvas/use-canvas-project-dialogs.ts`
    并在同文件第 126 行被 return 出去**——**return 不是调用**，
    可页内扫描只数「出现次数」，于是它从 1 次变成 2 次，扫描不再认它，
    闸便报「登记表项的扫描键本轮未被扫到 → 登记与现状不一致」。
    **而那句话是假的**：实测全库 5 处出现里**没有一处是调用**。

    **为什么不能把 `zero_call_setters` 直接改成全库口径**：
    `setSort` 与 `setProjectFilter` **各有 3 处同名声明**（画布库 / 项目库 / 素材库 / 任务页），
    全库计数会被同名声明撑大，**那两条本来正确的页内断言会一起变成「未被扫到」**——
    **把 1 处误报换成 2 处**。所以两个作用域必须分开量。
    **判「调用」而不是判「引用」**：`name` 后面紧跟 `(` 且前面不是 `.`／词字符才算调用。
    """
    decl = _git_grep_run(
        ["git", "grep", "-n", "-E",
         r"const \[[A-Za-z_$][A-Za-z0-9_$]*, *(" + re.escape(name) + r")\] *= *useState",
         REF, "--", "web/src"], cwd=src, capture_output=True, text=True)
    sites = [x for x in (decl.stdout or "").split("\n") if x.strip()]
    if len(sites) != 1:            # 同名多处声明 → 认不出来，如实说认不出来
        return False
    m = re.match(rf"^{re.escape(REF)}:(.+?):(\d+):", sites[0])
    if not m:
        return False
    home = m.group(1)
    callers = _git_grep_run(
        ["git", "grep", "-n", "-E", r"(^|[^A-Za-z0-9_$.])" + re.escape(name) + r"\(",
         REF, "--", "web/src"], cwd=src, capture_output=True, text=True)
    hits = [x for x in (callers.stdout or "").split("\n") if x.strip()]
    return not hits


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
    """审美批改的创建入口是**动态**的：插件一旦启用，它就出现在「添加节点」菜单里。

    ⚠️ 本判据在 Batch 163 被整体推翻重写过一次，**旧版是错的**，别照着旧版理解：
    旧版断言「『添加节点』是写死清单，从不读插件注册表」，判据是「写死清单里没有它」。
    运行时实测推翻了它——同一台机器、同一块空画布，只把插件中心里「AI 审美批改」的开关
    从停用拨到启用，「添加节点」菜单就在「脚本」之后多出该项，点击即建出节点。

    **旧判据错在结构上，而不是碰巧**：它只看写死清单那一个文件，而真正的入口由
    插件节点注册表动态生成，根本不经过那份清单。于是「写死清单里没有它」这个事实
    被当成了「没有入口」——典型的**从否定观察到全局结论**。

    现在锚的是那条**动态链是否完整**（任一环被摘掉即判失效）：
      registerPlugin → registerPluginCanvasNodes → canvasNodeDefinitionFromPlugin
      （showInCreateMenu=true）→ listCreatableNodeDefinitions → getPluginNodeMenuCommands
      → resolveAddNodeMenuCommands 合并 → applicable 按 enabledPluginIds.has 过滤
    """
    registry = git_show(src, "web/src/lib/canvas/tool-registry/tool-registry.ts")
    defn = git_show(src, "web/src/lib/canvas/node-registry/node-definition.ts")
    nreg = git_show(src, "web/src/lib/canvas/node-registry/node-registry.ts")
    preg = git_show(src, "web/src/lib/plugins/plugin-registry.ts")
    plugin = git_show(src, "web/src/lib/plugins/builtin/ai-art-critique.ts")
    if not (registry and defn and nreg and preg and plugin):
        return None
    return (
        # 插件声明画布节点，且注册器真的会把它接进节点注册表
        "canvasNodes" in plugin
        and "registerPluginCanvasNodes" in preg
        # 插件节点被标成「可创建」，且可创建清单确实按这个标记过滤
        and "showInCreateMenu: true" in defn
        and "showInCreateMenu" in nreg
        # 动态命令生成器存在，并且真的被合并进菜单（带展开运算符，避免命中函数定义本身）
        and "function getPluginNodeMenuCommands" in registry
        and "...getPluginNodeMenuCommands()" in registry
        # 可见性由插件启用态决定——这正是「默认搜不到、开了就有」的原因
        and "enabledPluginIds.has(pluginId)" in registry
    )


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
    r = _git_grep_run(["git", "grep", "-l", "loadProjectsPage", REF, "--", "web/src"],
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


def _git_grep_run(args, cwd, capture_output=True, text=True):
    """`git grep` 的统一入口：**git 自己出错时抛异常，不把空输出冒充成「零命中」**。

    **这是 Batch 157 血的教训换来的。**
    `git grep -E` 的模式一旦不合法（`{0,300}` 超过 255 的重复上限、
    POSIX ERE 不支持的惰性量词 `{0,n}?`、它不认的 `\\s` / `\\xNN` …），
    git 会**直接 fatal 并返回 128、stdout 为空**。而空输出与「确实没找到」
    在这些判据里**完全等价**——于是一条断言可以恒真、闸门一直绿，
    **而它什么都照不到**。

    本闸真实中过：`p_readonly_no_ui_entry` 的模式同时犯了「重复数超 255」
    与「惰性量词」两条，**整条判据从上线起就是死代码**，报的永远是「仍成立」。

    **为什么做成薄包装而不是逐个改写调用点**：调用点有十来个，
    后续用法各不相同（`r.stdout` / `r2.stdout` / 内联判断），
    逐个改写容易改错一处；而薄包装让**所有 `r.stdout` 用法原样不动**，
    一次性把整类静默失败堵死。
    """
    r = subprocess.run(args, cwd=cwd, capture_output=capture_output, text=text)
    if r.returncode >= 128:
        raise RuntimeError(
            "git grep 执行失败（rc=%d），**本次结果不可用**——模式很可能不合法。"
            "git 的原话：%s" % (r.returncode, (r.stderr or "").strip()[:200])
        )
    return r


def git_grep_lines(src, *args):
    """跑 `git grep` 并返回命中行列表；git 出错时抛异常（见 `_git_grep_run`）。"""
    r = _git_grep_run(["git", "grep", *args], src)
    return [l for l in (r.stdout or "").split("\n") if l.strip()]


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
    # 模式在**上线第一天就是死代码**，Batch 157 才发现。三处独立病因：
    #   ① `{0,300}` 超过 git regex 的 255 重复上限 → `maximum repetition exceeds 255`
    #   ② 惰性量词 `{0,300}?` 是 PCRE 语法，POSIX ERE 根本不支持 → `operand invalid`
    #   ③ `\s` 在 git grep 里是字面字母 s
    # ①② 任一都让 git **整条拒绝**并返回 128、stdout 为空；
    # 而「空输出」与「没找到生产者」在这个判据里是同一个结果
    # → **判据恒真、闸门永远绿、实际什么都没照到**。
    # 现在：去掉惰性量词（改贪婪，`[^"`]` 跨不过引号，贪婪照样会回溯）、
    #      重复数降到 120（< 255）、`\s` 换 `[[:space:]]`，
    #      并统一走 git_grep_lines()——**git 报错时抛异常，由 main() 报成问题**。
    producers = git_grep_lines(
        src, "-I", "-E",
        r'["`][^"`]{0,120}[?&](readonly|mode)[[:space:]]*=[[:space:]]*(1|readonly)',
        REF, "--", "web/src")
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
        # **Batch 294：认「有没有同步调用」，不认某一个函数名**（见 CANVAS_SYNC_CALL）。
        if CANVAS_SYNC_CALL.search(body):
            return False
    m = re.search(r"export async function createLocalCanvasProject.*?\n\}", repo, re.S)
    if not m or not CANVAS_SYNC_CALL.search(m.group(0)):
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

    ⚠️ **Batch 294：(a) 认「经某个入口建文件夹」这个事实，(c) 之外补一条 (d)
    直接量「服务端根本没有画布文件夹这个概念」——原先它只靠 (c) 间接推。**
    实测：origin/main 上画布库页不再直调 store 的 `createFolder`，
    改调 `createCanvasLibraryFolder`（`web/src/lib/canvas/canvas-folder-storage.ts`）。
    **旧 (a) 因此为假，这条断言在 origin/main 上报「判据已不成立」——而它的结论碰巧是对的，
    理由是错的**：闸是因为「页面少了那个调用」才报，不是因为服务端多了一整套东西。
    **而那个东西是真的**：origin/main 新增 `backend/internal/handler/canvas_library.go`
    的 GET/PUT/DELETE `/canvas-folders`，**基线上这两个目录合计 0 处**。
    **「结论对、理由错」比「结论错」更贵**：照错误的理由去查，会得出
    「大概是重构，去找新入口」而不是「服务端接上了，手册这句要改」。
    (d) 把这件事变成直接量的事实，也顺带关上一个假绿：
    **旧判据在「页面继续直调 createFolder、同时服务端新增了文件夹端点」的树上会报绿。**
    """
    idx = git_show(src, "web/src/pages/canvas/index.tsx")
    store = git_show(src, "web/src/stores/canvas/use-canvas-store.ts")
    if not idx or not store:
        return None
    # (a) 入口可以是 store 的 createFolder，也可以是后来抽出去的服务函数——
    #     **要认的是「页面确实有一个建文件夹的入口」，不是它写在哪个模块里。**
    if not re.search(r"\bcreateFolder\b", idx) \
            and not re.search(r"\bcreateCanvasLibraryFolder\b", idx):
        return False
    if "writeCanvasFolders" not in store or "readCanvasFolders" not in store:
        return False
    if "AssetFolder" in idx or "asset-folders" in idx:
        return False
    # (d) 服务端**零处**画布文件夹端点——这一条才是「纯本机」的直接依据。
    r = _git_grep_run(["git", "grep", "-l", "-F", "/canvas-folders", REF,
                       "--", "backend", "web/src"], cwd=src, capture_output=True, text=True)
    return not (r.stdout or "").strip()


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
    if CANVAS_SYNC_CALL.search(body):
        return False
    if "flushCanvasStorePersistence" not in body:
        return False
    m2 = re.search(r"const saveTitle = async \(\) => \{.*?\n    \};", card, re.S)
    if not m2 or CANVAS_SYNC_CALL.search(m2.group(0)):
        return False
    if "flushCanvasStorePersistence" not in m2.group(0):
        return False
    m3 = re.search(r"export async function createLocalCanvasProject.*?\n\}", repo, re.S)
    return bool(m3) and bool(CANVAS_SYNC_CALL.search(m3.group(0)))


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
         # 同样修引擎：`\s` 在 git grep 的 ERE 里是字面字母 s，
         # 写 `http.get( '/assets' )`（括号后带空格）就抓不到了。
         # 泛型 `<...>` 改为**可选**：原写法强制要求泛型参数，
         # 而 `http.get('/assets')` 这种不带泛型的调用（完全合法、也确实有人这么写）
         # 会整条漏掉——**泛型是调用习惯，不是「这是接口调用」的判据**。
         r"http\.(get|request|fetch)(<[^>]*>)?\([[:space:]]*[\"\']/assets[\"\']",
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
        r = _git_grep_run(["git", "grep", "-n", "-F", prefix, REF, "--", "web/src"],
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
    r = _git_grep_run(["git", "grep", "-n", "-E",
                        # 引擎修正：`\s` 是字面字母 s、`[^\n]` 排除的是字母 n，两者都失效。
                        #
                        # **`[^\n]` 也不能简单换成 `.`**——闸门首轮跑完立刻自报失效，
                        # 因为 `.` 会吃掉 `=`：`workspaceMode === "simple"` 里
                        # `.{0,40}` 吞掉 ` ==` 之后照样能匹配上，**5 处比较被当成写入**
                        # （canvas-config-composer.tsx:55 等）。旧的 `[^\n]` 只是**碰巧**没误报。
                        # 正确写法是显式排除 `=` 与引号：既跨不过运算符，又跨不过字符串边界。
                        #
                        # 剩下一个**故意保留的局限**：`=` 之外没放宽 `:`，
                        # 所以对象属性式（`{ workspaceMode: "simple" }`）仍照不到——
                        # 实测放宽会立刻误伤那 5 处比较。**宁可漏照、不可误报**
                        # （漏照的后果是这条断言暂时形同虚设，已写进脚本头声明）。
                        r"workspaceMode[^=\"'`]{0,40}=[[:space:]]*\{?[[:space:]]*\"?simple\"?",
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
    r = _git_grep_run(["git", "grep", "-l", "-F", "navigator.locks", REF, "--", "web/src"],
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
    r = _git_grep_run(["git", "grep", "-n", "-E",
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
    r2 = _git_grep_run(["git", "grep", "-l", "-F", "FeatureEnabled", REF, "--", "backend"],
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


def p_short_drama_empty_state_unreachable(src):
    """短剧引导空画布**有完整实现、零入口**：全库没有任何代码把 starterMode 设成 guided。

    手册此前从未提过它——连「这是一套进不去的界面」都没说。而 Batch 141 把
    「短剧 / 小说转视频生产台」登记成 excluded（路由退场），**那是另一件事**：
    生产台是**路由退场**，短剧引导是**画布上的空状态**——组件活着、渲染条件写着，
    唯独没有入口能让画布切过去。

    这比 Batch 145 的「沙箱渲染器」更极端：沙箱那条**入口在外部**（第三方插件可
    声明 `renderer: "sandbox"`），而这条**连外部入口都没有**。

    判据要求：
      (a) `CanvasStarterMode` 确实是二值枚举，且渲染分支按 `starterMode === "guided"` 判断；
      (b) **全 web/src 零处把 starterMode 赋成 "guided"**——能找到的赋值只有 "freeform"
          （那是「从引导退回自由」的按钮）和导入时的原样复制；
      (c) **对照组**：短剧引导的组件与动作**确实都还在**
          （`CanvasShortDramaEmptyState` 存在、且有 createShortDramaPipeline 这个动作）。
          **少了 (c)，(a)(b) 也可能只是「功能已经删干净、只剩类型定义」**，
          那手册该写的是「短剧引导已被移除」，而不是「它还在、只是进不去」。
    """
    starter = git_show(src, "web/src/lib/canvas/canvas-starter.ts")
    router = git_show(src, "web/src/pages/canvas/project.tsx")
    if not starter or not router:
        return None
    # (a) 枚举与分支
    if 'export type CanvasStarterMode = "guided" | "freeform";' not in starter:
        return False
    if 'starterMode === "guided" ? "guided" : "freeform"' not in starter:
        return False
    if 'emptyStateKind === "guided" ?' not in router:
        return False
    # (b) 零处写入 "guided"
    #
    # **这个正则被反验用例 29 当场判失败过一次，修正记录别删**：
    # 第一版写的是 `starterMode[^\n]{0,40}=\s*\{?\s*"guided"`，**只认等号**。
    # 而上游现有的写法恰恰是**冒号属性式**——`project.tsx:2823`
    # `updateProject(projectId, { starterMode: "freeform" })`。
    # 也就是说，**上游将来补上这个入口时最可能用的正是冒号式**，
    # 而那条路径**判据照不到 → 闸门会报「仍成立」→ 手册继续写「进不去」**。
    # **那等于在手册里写假话**，比误报严重得多，所以这里宁可灵敏、不可漏。
    #
    # 仍然**故意不匹配比较式**：`starterMode === "guided"` 里 `[:=]` 只吃第一个
    # `=`，后面紧跟的 `== "guided"` 对不上 `"guided"`，所以比较不会被当成写入。
    # 用例 31（不误伤）就是钉这一条：**放宽正则不等于放宽成什么都能匹配。**
    r = _git_grep_run(["git", "grep", "-n", "-E",
                        r'starterMode[[:space:]]*[:=][[:space:]]*\{?[[:space:]]*\"guided\"',
                        REF, "--", "web/src"], cwd=src, capture_output=True, text=True)
    if (r.stdout or "").strip():
        return False
    # (c) 对照组：组件与动作都还在
    if "CanvasShortDramaEmptyState" not in router:
        return False
    if "createShortDramaPipeline" not in router:
        return False
    r2 = _git_grep_run(["git", "grep", "-l", "-F", "CanvasShortDramaEmptyState",
                         REF, "--", "web/src"], cwd=src, capture_output=True, text=True)
    return bool((r2.stdout or "").strip())


def p_empty_canvas_quickstarts_off(src):
    """空画布上的四个快捷入口被 `const showQuickStarts = false` 写死关闭。

    Batch 157 查「读者打开空画布看到什么」时撞见的。成因与已登记的
    `simple-mode-hardcoded` **完全同型**：不是没有入口，而是**入口的取值被一个
    常量焊死**——所以它连 URL 参数扫描都扫不到（根本没写成参数）。

    与 `short-drama-empty-state-unreachable` 的区别要说清楚，否则容易合并成一条：
      · 短剧引导：**字段存的是 starterMode，没有任何写入点**（入口被摘掉）；
      · 快捷入口：**字段就摆在那儿，值是 false**（入口被关掉）。
    两者在界面上表现相同（都是「找不到」），但一个是「没接线」、一个是「拨到关」。

    判据要求：
      (a) `const showQuickStarts = false` 是**字面量常量**，不是条件表达式——
          与 simple-mode 判据同口径：写成 `cond ? false : true` 就会通过，那不是缺陷；
      (b) **对照组**：四个快捷入口的**实现确实都在**（quickStarts 数组四项 +
          按钮渲染分支 `showQuickStarts ?`）。
          **少了 (b)，(a) 也可能只是「这个功能根本不存在」**，
          那手册该写的是「产品没这个入口」而不是「入口被关掉了」；
      (c) 源码注释自述「实现都还在，等工作流就绪再放出」——**有了它才能说清
          这是有意的关闭而不是漏写**，手册那句话的措辞才对得上。
    """
    entry = git_show(src, "web/src/components/canvas/canvas-short-drama-entry.tsx")
    if not entry:
        return None
    # (a) 字面量常量
    m = re.search(r"const showQuickStarts = (true|false);", entry)
    if not m:
        return False
    if m.group(1) != "false":
        return False
    # (b) 对照组：四项数据与渲染分支都还在
    for label in ("故事脚本生成", "角色三视图", "全能参考生视频", "音频生视频"):
        if label not in entry:
            return False
    if "showQuickStarts ?" not in entry:
        return False
    # (c) 注释自述「等对应工作流就绪再放出」
    return "until their" in entry and "ready for release" in entry


def p_default_config_no_models(src):
    """出厂配置里**一个可用模型都没有**——「先生成再配模型」是走不通的。

    手册 README 原本让读者从首页直接点「生成图片或视频」，而首页「需要先知道的
    几件事」里讲了计费、字幕入口、本地配合，**唯独没讲要先配模型**。
    读者点进去必然撞上「当前没有可用模型」，而**本地部署里没有管理员可找**。

    Batch 156 补了这一条，顺手把它登记成断言——因为它是**出厂常量**，
    上游哪天预置了默认模型，README 那句「默认一个可用模型都没有」就该失效。

    判据要求：
      (a) `defaultConfig` 里渠道数组为空、四个模型字段为空串、apiKey 为空串；
      (b) **对照**：源码注释明写「不能内置供应商模型」——
          证明 (a) 是**有意的产品决定**而不是初始化代码漏写。
          少了 (b)，上游哪天补上预置渠道，(a) 也可能只是「还没初始化完」。
      (c) 那句空态文案确实存在（手册要原样引用它）。
    """
    store = git_show(src, "web/src/stores/use-config-store.ts")
    if not store:
        return None
    m = re.search(r"export const defaultConfig: AiConfig = \{(.*?)\n\};", store, re.S)
    if not m:
        return False
    body = m.group(1)
    for field, empty in ((r"channels:", r"\s*\[\]"),
                         (r"apiKey:", r'\s*""'),
                         (r"model:", r'\s*""'),
                         (r"imageModel:", r'\s*""'),
                         (r"videoModel:", r'\s*""'),
                         (r"textModel:", r'\s*""')):
        fm = re.search(field + empty, body)
        if not fm:
            return False
    # (b) 对照组：注释说明这是有意决定
    if "不能内置供应商模型" not in store:
        return False
    # (c) 空态文案
    r = _git_grep_run(["git", "grep", "-l", "-F", "当前没有可用模型，请联系管理员或检查模型配置",
                        REF, "--", "web/src"], cwd=src, capture_output=True, text=True)
    return bool((r.stdout or "").strip())


DEV_ROUTE_FOLDERS = "/dev/folders"
DEV_ROUTE_REPRO = "/dev/director-repro"


def p_dev_lab_routes_no_entry(src):
    """`/dev/folders` 与 `/dev/director-repro` 是开发调试台，**界面上零入口**。

    Batch 155 查 20-reference 的路由表覆盖度时发现：上游 `router.tsx` 注册了 22 条路径，
    手册只覆盖 15 条，漏掉的里有**这两个开发调试台**——它们与已在闸的
    `/test-voice-recording`（`test-voice-page-no-ui-entry`）**完全同型**。

    而且比那条更值得记：`app-providers.tsx` 里给导演台复现台写了专门的**隔离**逻辑
    （跳过工作区启动，免得没后端时打出 502 污染判据），**但判断被 `import.meta.env.DEV`
    包着**——源码注释自己写着「生产构建中本分支被摇树删除」。
    **也就是说线上这两页照样会去打后端**，而手册原本一个字都没提。

    判据要求：
      (a) 两条路由在 `router.tsx` 里**都在**，且都指向 `pages/dev/` 下的组件；
      (b) 两个页面组件**除 router 外零引用**——即界面上没有任何导航能到它们；
      (c) **对照组**：隔离那段确实被 `import.meta.env.DEV` 包着。
          少了 (c)，(a)(b) 只说明「它们是挂在路由上的冷页面」，
          手册该写「开发调试台，线上可能打后端」；有了 (c) 才能断言
          **「那段隔离在生产构建里不生效」**——这是手册那句话的依据。
    """
    router = git_show(src, "web/src/router.tsx")
    if not router:
        return None
    # (a) 两条路由都在，且指向 pages/dev 组件
    for route, comp in ((DEV_ROUTE_FOLDERS, "FolderPreviewLab"),
                        (DEV_ROUTE_REPRO, "DirectorReproLab")):
        if ('path: "' + route + '"') not in router:
            return False
        if comp not in router:
            return False
    # (b) 两个页面**零处导航入口**。
    #
    # **第一版写成「grep 组件名零额外引用」，被自己的反验用例 27 打回**：
    # 反验往侧栏注入 `to: "/dev/folders"`，闸门却没报失效。
    # 真因：**导航写的是路径，不是组件名**——`git grep FolderPreviewLab`
    # 根本照不到 `to: "/dev/folders"`，因为侧栏**不需要 import 那个组件**。
    # 这与 Batch 154 刚栽的「假通过」是同一类错误的镜像：
    # 那次是注入没生效却被当成通过，这次是**判据管不到那个形态**。
    #
    # 正解就在隔壁 `p_test_voice_page_no_ui_entry` ——它 (c) 查的是
    # **「全 web/src 零处导航到该路径」**。照它改：grep 路径字符串，
    # 只允许 router.tsx 与页面自身命中。
    #
    # 教训：**判「有没有入口」要 grep 用户/代码实际会写的那一样**——
    # 导航代码里出现的是 URL，不是组件标识符。
    for route, page in ((DEV_ROUTE_FOLDERS, "web/src/pages/dev/folder-preview-lab.tsx"),
                        (DEV_ROUTE_REPRO, "web/src/pages/dev/director-repro-lab.tsx")):
        r = subprocess.run(
            ["git", "grep", "-n", "-E", '"' + re.escape(route) + '"', REF, "--", "web/src"],
            cwd=src, capture_output=True, text=True)
        for line in (r.stdout or "").split("\n"):
            if not line.strip():
                continue
            m = re.match(rf"^{re.escape(REF)}:(.+?):(\d+):", line)
            if not m:
                continue
            path = m.group(1)
            # 允许 router、页面自身，以及 app-providers.tsx。
            #
            # 最后一处豁免**不是放宽，是纠正一个真实的过严**：
            # `app-providers.tsx:39` 有 `window.location.pathname === "/dev/director-repro"`
            # ——那是 **isolateDevRepro 的判断条件**，用来**决定要不要隔离**，
            # **它不是任何导航到该页面的入口**。第一版把它当「别处导航」直接 return False，
            # 于是判据在**真实 origin/main 上就不成立**（连续第 N+1 次「判据过严」）。
            #
            # **判别依据**：导航入口会出现在 `to:` / `href` / `navigate(` 这类**动作**里；
            # 而这里是**读取当前位置**做判断，动作方向相反。
            if path in ("web/src/router.tsx", page, "web/src/components/layout/app-providers.tsx"):
                continue
            return False
    # 同时确认组件名本身也没有被别处 import（两条独立证据）
    for comp in ("FolderPreviewLab", "DirectorReproLab"):
        r = _git_grep_run(["git", "grep", "-l", "-F", comp, REF, "--", "web/src"],
                           cwd=src, capture_output=True, text=True)
        files = [x.split(":")[-1] if ":" in x else x for x in (r.stdout or "").split("\n") if x.strip()]
        if len(files) > 2:
            return False
    # (c) 对照组：隔离被 DEV 包着
    providers = git_show(src, "web/src/components/layout/app-providers.tsx")
    if not providers:
        return None
    if 'const isolateDevRepro = import.meta.env.DEV' not in providers:
        return False
    # **Batch 294：认「隔离判断里比对了那个路径」这个事实，不认取得 pathname 的写法。**
    # 原式写死 `'pathname === "/dev/director-repro"'`，而 origin/main 把
    # `window.location.pathname` 换成了 `appPathname()`——**判定对象一个字没变，
    # 只是取法换了**，旧字面量因此不在，于是这条断言被判「判据已不成立」，
    # 而「隔离被 DEV 包着、线上照样打后端」这个要写进手册的结论**仍然成立**。
    # 取法不止一种（window.location.pathname / appPathname() / useLocation().pathname），
    # **而事实只有一个：isolateDevRepro 的定义里比对了那个路径。**
    m_iso = re.search(r"const isolateDevRepro\s*=(.*?);", providers, re.S)
    if not m_iso or DEV_ROUTE_REPRO not in m_iso.group(1):
        return False
    return "WorkspaceBootstrapHydrator" in providers


# 第 4 个字段 scan_key = (文件, setter 名)，表示该条**同时**能被方向二的
# 全量 setter 扫描覆盖；为 None 表示**只有专属判据**（判据形态不同，
# 例如「ref 零 click」或「路由先 Navigate」，setter 扫描天然照不到）。
# 方向二只对有 scan_key 的条目要求「必须扫到」——否则会把形态不同的判据
# 误判成登记表写错（本闸首次运行就犯了这个错，被自己的双向检查抓出来）。
# 下面这条曾长期成立、并已被上游修掉，Batch 178 移除：
#   ("canvas-library-no-import-entry", "画布库无导入入口", …)
# 判据核的是「有 zip file input，但 inputRef 从未被 click()」——
# v1.6.22 的 `522cd03`「恢复画布备份导入入口」给项目库加了
# `<Button icon={<Upload/>} onClick={() => inputRef.current?.click()}>导入画布</Button>`，
# **判据因此正确地报出「上游已修复」——这正是它建起来要抓的那件事**，
# 也是闸 7 建库以来第一次真的因「上游修复」而变红（此前 30+ 个批次全是绿的）。
# 手册对应断言已在 manage-canvases.md 与 90-troubleshooting.md 改掉。
REGISTRY = [
    ("canvas-library-no-sort-filter", "画布库无排序/筛选控件", p_sort_filter,
     (("web/src/pages/canvas/index.tsx", "setSort"),
      ("web/src/pages/canvas/index.tsx", "setProjectFilter"))),
    ("canvas-library-no-join-project", "「加入项目/移出项目」恒不渲染", p_join_project, None),
    ("art-critique-dynamic-entry", "AI 审美批改的创建入口由插件启用态动态生成", p_art_critique_entry, None),
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
    ("dev-lab-routes-no-entry", "两个 /dev 调试台挂在生产路由但界面零入口，且隔离逻辑是 DEV-only",
     p_dev_lab_routes_no_entry, None),
    ("default-config-no-models", "出厂配置零可用模型：先配模型是所有生成动作的前置条件",
     p_default_config_no_models, None),
    ("short-drama-empty-state-unreachable", "短剧引导空画布有完整实现但零入口：全库无一处写入 guided",
     p_short_drama_empty_state_unreachable, None),
    ("empty-canvas-quickstarts-off", "空画布四个快捷入口被常量写死关闭（与短剧引导同型不同因：关掉 vs 摘掉）",
     p_empty_canvas_quickstarts_off, None),
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
# ⚠️ Batch 170 的变化：`agent` 与 `fixture` **原先进不来这个名单**——
# 源码注释里各有一句 `?agent=1` / `?fixture=libtv-generating`，
# 而写出点扫描**把注释也当代码**，于是这两个参数永远「有写出点」、
# 永远脱零写、**闸门从不跟踪它们**，本文件原来还专门写了一段坦白这件事。
# 现在写出点只看**代码**（`_strip_line_comment`），它们才终于归位。
# **教训：那场坦白本身就是判据缺陷的自供**——闸门在旁边写「这两个我不管」，
# 却没人把这句话当成待办；**写下来不等于有人修，而「不写」连线索都没了。**
URL_PARAM_EXEMPT = {
    "fixtureMedia": "演示画布数据的媒体资源参数，与 fixture 配套；界面无入口",
    "libtvChrome": "演示用 LibTV 顶栏外观开关，与 fixture 配套；界面无入口",
    "history": "画布库回收站的 URL 变体；界面另有直接按钮打开同一弹窗，不靠 URL",
    "uuid": "projectId 的解析别名；入口是「粘贴 LibTV 项目链接」的输入框，"
            "值来自剪贴板而非导航，故零导航写出属正常",
    "demo": "/create 的固定数据演示模式，页面顶部有明示横幅，属演示设施",
    "agent": "旧内置 Agent 的深链参数（?agent=1），只被读并原样转发到画布页；"
             "旧 Agent 已下线，**没有任何界面动作会产出它**（源码里那一处 "
             "?agent= 在注释中，已被代码档排除）",
    "fixture": "演示画布数据选择器，共 10 种取值；只被 searchParams.get 读 "
               "14 处，**无任何界面写出点**（源码里那一处 ?fixture= 在注释中）",
}

# 零写出且**确为缺陷/受限**的参数 → 登记 id（与 REGISTRY 呼应）。
URL_PARAM_DEFECT = {
    "readonly": "canvas-readonly-no-ui-entry",
    "stay": "canvas-stay-acceptance-only",
}


def _strip_line_comment(s):
    """删掉一行里的注释，**但不碰字符串内部的 `//`**（如 `"https://…"`）。

    Batch 170 新增。此前判据把**注释里的一句 `?fixture=libtv-text` 也算成界面写出点**，
    于是 `fixture` / `agent` 永远脱零写、永远没人看守——**闸门在一个自己都承认的
    缺口旁边写着「闸门不跟踪它们」**。而这跟判据的初衷正好相反：
    判据选严格档是为了「宁可漏报也不误报」，可**把注释当写出点只会让闸门变弱**
    （多认一个不存在的生产者 → 少报一个真缺口），它换不来任何安全。

    **跨行块注释（`/* … */`）刻意不跟踪**，理由不是省事而是**做不到**：
    写出点扫描原本吃的是 `git grep -h` 的拼接文本，**`-h` 会丢掉文件名**，
    没有文件边界就无法维护注释状态。第一版探针正是在这里翻车——
    某处字符串里的 `/*` 让状态机误进块注释模式，**后面几万行被整段清空**，
    于是它报告 `tab` 参数「代码内零写出点」，而 `assets/index.tsx` 里明明有
    两个按钮在 `navigate("/assets?tab=history")`。**那个错误结论差一点就写进手册。**
    所以现在按**带文件名的逐行**处理，且只删**单行**注释。
    """
    out = []
    i = 0
    quote = None
    while i < len(s):
        c = s[i]
        if quote:
            out.append(c)
            if c == "\\" and i + 1 < len(s):
                out.append(s[i + 1])
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c in "'\"`":
            quote = c
            out.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < len(s) and s[i + 1] == "/":
            break                      # 行注释到此为止，后面的不是代码
        if c == "/" and i + 1 < len(s) and s[i + 1] == "*":
            j = s.find("*/", i + 2)
            if j == -1:
                break                  # 跨行块注释：本行剩余全丢，**不进入状态**
            i = j + 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _code_only_lines(src):
    """返回 web/src 的**代码行**列表（逐行剥掉单行注释），**每个非空源行对应一项**。

    逐文件处理：`-n` 保留 `路径:行号:` 前缀，用它切出文件边界，
    这样即便将来要扩展到跨行注释也有边界可用。
    **列表长度必须等于源文件的非空行数**——这一点由调用方的自检守着。
    """
    r = _git_grep_run(["git", "grep", "-n", "-I", "-e", ".", REF, "--", "web/src"],
                      cwd=src, capture_output=True, text=True)
    raw = r.stdout or ""
    by_file = {}
    for line in raw.split("\n"):
        if not line.strip():
            continue
        path, _, rest = line.partition(":")
        _ln, _, body = rest.partition(":")
        by_file.setdefault(path, []).append(body)
    out = []
    for path in sorted(by_file):
        for body in by_file[path]:
            out.append(_strip_line_comment(body))
    return out


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

      · strict=True（**闸门用这一档**）：`?name=` / `&name=` 出现在**代码的任何位置**
        都算写出点。**注释不算**（Batch 170 起，见 `_strip_line_comment`）——
        「注释里写了 `?fixture=`」不是「界面上有个按钮会产出它」。
        ⚠️ 改这一档前**必须先量反向变化**（有没有参数从「有写出点」变成「零写出」）：
        本批实测 **+2（agent、fixture）、反向 0**，即只可能让闸门变严。
      · strict=False（**只作提示，不参与判定**）：要求 `?name=` 落在引号对内。
        它的**唯一**已知弱点是模板字符串**内嵌反引号**
        （`tasks/index.tsx:551` 的 `` `/settings?…&projectId=${…}` ``）整段匹配失败，
        把真实导航写点误报成零写出。
        原来它还有第二个弱点「注释里一句 `?fixture=libtv-text` 就会让该参数脱零写」——
        **那个弱点已由代码档的剥注释根治**，故只剩一条，且这条正是**不能拿它当判据**
        的理由（宁可漏报，也不能在手册里写假话）。
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

    gr = _git_grep_run(["git", "grep", "-h", "-I", "-e", ".", REF, "--", "web/src"],
                        cwd=src, capture_output=True, text=True)
    all_text = gr.stdout or ""
    # **写出点只看代码**（Batch 170）。宽松档仍用原文，因为它要的正是「出现在任何位置」。
    code_lines = _code_only_lines(src)
    n_raw = len([l for l in all_text.split("\n") if l.strip()])
    if not code_lines:
        # 剥完一行都不剩 = 判据自己出错了，绝不能当成「没有写出点」（那会让闸门变绿）
        raise RuntimeError("剥注释后代码行为空，无法判定写出点")
    if len(code_lines) != n_raw:
        # 这个自检当场抓过一次真 bug：git grep 输出带尾随换行，两边口径差一行。
        # **判据自己的实现出错时，必须表现为失败而不是沉默**（纪律 101）。
        raise RuntimeError(
            "剥注释前后行数不一致（%d vs %d），剥注释实现有 bug"
            % (len(code_lines), n_raw))
    code_text = "\n".join(code_lines)

    strict_written = {m.group(1).lower()
                      for m in re.finditer(r"[?&]([A-Za-z0-9_-]+)\s*=", code_text)}
    strict_written |= {m.group(1).lower() for m in re.finditer(
        r"\.\s*(?:set|append)\s*\(\s*[\"']([A-Za-z0-9_-]+)[\"']", code_text)}

    if strict:
        return {p: n for p, n in reads.items() if p.lower() not in strict_written}

    loose_written = set(strict_written)
    for lit in re.finditer(r"[\"'`][^\"'`\n]{0,300}[\"'`]", all_text):
        for m in re.finditer(r"[?&]([A-Za-z0-9_-]+)\s*=", lit.group(0)):
            loose_written.add(m.group(1).lower())
    return {p: n for p, n in reads.items() if p.lower() not in loose_written}


@baseline_guard
def main():
    src = find_source()
    if not src:
        print("[skip] 未找到 BeefTV 源码，跳过不可达声明核对")
        return 2

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
        # **Batch 295：页内扫描认不出来的键，再用「全库零调用」复核一遍。**
        # **原式直接把它算成「登记与现状不一致」**——而登记表里两种作用域都有
        # （setSort / setProjectFilter 是页内，setArtCritiqueStartRequest 是全库），
        # **原来只有一种口径，于是另一种作用域的键一被上游重构就必然误报。**
        resolved, still_missing = [], []
        for key in sorted(scan_covered - actual):
            if _declared_once_never_called(src, key[1]):
                resolved.append(key)
            else:
                still_missing.append(key)
        for key in still_missing:
            problems.append(
                f"[scan] 登记表项 {by_key[key]} 的扫描键 {key[1]} 本轮未被扫到 → "
                f"该断言可能已失效或登记键写错，登记与现状不一致"
            )
        for key in resolved:
            notes.append(
                f"  [scan] 登记表项 {by_key[key]} 的扫描键 {key[1]} 页内扫描认不到，"
                f"**全库零调用复核成立**（声明唯一、无任何调用点）→ 断言仍成立；"
                f"**注意键里那个文件已过时**（上游把声明搬了家）")
        notes.append(f"  全量 setter 零调用扫描：{len(actual)} 处命中；"
                     f"登记表中 {len(scan_covered)} 个可扫描条目 = "
                     f"页内命中 {len(actual & scan_covered)} + 全库复核 {len(resolved)}"
                     f" + 对不上 {len(still_missing)}"
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

        # —— 方向三之二：手册声明的「只读不写参数个数」必须等于实测 ——
        # **为什么这条要放在同一个进程里比**（Batch 170）：这个数是**判据自己算出来的**，
        # 放到别的闸去比就得让那个闸再跑一遍扫描，或者去读某个「上次的结果」——
        # **那正是誊抄副本**（规则 100）。同进程比较，手册里那个数要么对要么构建失败。
        #
        # **它此前一直对不上而无人知道**：手册写「共有 10 个」，实测两种口径分别是
        # **7（把注释当代码）/ 9（只看代码）**，**10 复现不出来**（浅克隆取不到历史，
        # 按纪律只能说「无法定位」，不能编一个原因）。现在口径写进手册、数由闸门守着。
        manual = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "20-reference.md")
        try:
            with open(manual, encoding="utf-8") as fh:
                mtext = fh.read()
        except OSError as exc:
            notes.append(f"  [skip] 读不到 {manual}（{exc}），手册声明的零写出参数个数本轮未能核对")
        else:
            m = re.search(r"共有\s*\*\*(\d+)\*\*\s*个查询参数", mtext)
            if not m:
                problems.append("[url] 20-reference.md 里找不到「共有 **N** 个查询参数」这句声明 → "
                                "手册与本判据的对应关系断了（要么声明被改写，要么本闸换了口径）")
            elif int(m.group(1)) != len(dead_params):
                problems.append(
                    f"[url] 手册声明「共有 **{m.group(1)}** 个查询参数只有读取」，"
                    f"本轮实测 **{len(dead_params)}** 个 → 声明与现场脱节，"
                    f"零写出参数集合：{sorted(dead_params)}")
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
