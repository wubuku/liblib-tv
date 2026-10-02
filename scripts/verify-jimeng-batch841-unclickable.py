#!/usr/bin/env python3
"""Jimeng clone batch 841 verifier —— 把「点不着的控件普查」钉成**常备契约**。

## 这条通道补的是前两条都看不见的东西

    批 831/832  role ∈ dialog/menu/listbox/popover   （浮层，按语义）
    批 837/840  几何 + 层级 + 可交互性               （浮层，不认 role）
    批 841      elementFromPoint 命中测试             （**控件本身**）

前两条问的都是「浮层在不在、可不可指名」。**没有一条问过控件本身**：
「它被盖住了吗？」—— 用户点一下没反应，和按钮压根不存在，对用户是同一件事。
而「元素存在」恰恰是最容易骗过人的检查：835 就是例证（源站下拉互斥，
复刻拆成多个独立 state，392 宽那层把 192 宽那层的**选项**盖住 ⇒ 元素都在，
用户就是点不着）。

## 报 0 不算结论

一个报 0 的工具，在证明自己之前什么都不是。本批的硬要求是**判据能报出 1**：
工具在页面上真的盖一层遮挡物，复查那枚已知控件判成被挡，撤掉后复查恢复 ——
两步都成立才算数，任一步不成立就退出码 2（不是 0，否则 CI 当通过）。

verifier §C 再从**源码**侧钉一遍：采样点、INFO 分档、开发浮层排除、
链式遮挡穿透、退出码分支，一个都不许被悄悄改没。
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "scripts" / "jimeng_unclickable_audit.py"
OUT = Path("/tmp/jimeng-unclickable-b841.json")

# 覆盖面下限：这些状态必须**真的跑到**。少一个就是有人悄悄缩小了范围。
# 批 843 从 11 个扩到 24 个（补齐文本调色板 / 图片工具菜单 / 音频面板 5 个 /
# 缩放 / 顶栏 5 个 / 画布右键）。顺序与审计脚本一致，别只改一处。
EXPECTED_STATES = [
    "空态", "视频工具条",
    "视频工具条·截取帧下拉", "视频工具条·工具下拉", "视频全屏预览",
    "视频生成面板", "视频生成面板·模型下拉", "视频生成面板·尺寸下拉",
    "视频生成面板·模式下拉", "视频生成面板·时长下拉",
    "文本·背景色调色板", "图片工具条·工具菜单",
    "音频生成面板·音乐模型", "音频生成面板·音乐时长",
    "音频生成面板·音色模型", "音频生成面板·音频生成模式",
    "音频生成面板·全音色",
    "画布右键菜单", "缩放菜单",
    "顶栏·分享面板", "顶栏·账号菜单", "顶栏·更多菜单",
    "顶栏·搜索", "顶栏·生成历史",
    # 批 865：从「一次性测量」提升为**常驻状态**（§82 探到、864 修好，
    # 但证据只在探针输出里 —— 不进状态表就没人盯着它会不会再坏）。
    "资产库模态", "项目信息模态",
    # 批 867：探针 867 探到、且**冷启动就能点开**的另外 3 个浮层。
    "顶栏·节点摘要", "顶栏·项目面板", "AI 侧栏",
    # 批 868：867 记成「候选没命中」的那三个，**三个**都跑到了。
    # ⚠️ 顺带**撤回**本文件上一版写在这里的一段话。那段写的是：
    #   「文本·全屏编辑故意不在契约里 —— 审计上下文里入口压根不在 DOM，
    #    探针冷启动却能拿到，差异未查清（⚠️ 未验证）」。
    # **那个结论是错的，而且错在两个地方**：
    #   ① 「入口不在 DOM」不是环境差异，是**审计自己**把它按掉的 ——
    #      `select_node()` 第一步就按 Escape，而文本节点在编辑态里把
    #      Escape 当「取消编辑」；入口 `text-expand` 只在**编辑态**挂载，
    #      于是「dblclick 进编辑 → 重新选中 → 入口」结构上不可能成立。
    #      修法是加一版**不按 Escape** 的 `select_node_soft()`。
    #   ② 「入口不存在」这个更早的结论也不对：按钮的 aria 是 `全屏`，
    #      `全屏编辑` 是**层**的名字（867 探针把层名当按钮名去找了）。
    #      §83 那条待办「复刻没有全屏入口」据此关闭。
    "文本·全屏编辑", "时间线·全屏", "主体·元数据编辑器",
    # 批 869：AI 抽屉里那两个**冷启动就能点开**的内层面板。
    "AI 侧栏·搜索技能", "AI 侧栏·添加参考",
    # 批 870：音色库的筛选下拉。870 之前它**测不了**（四个面板无条件常驻，
    # 而 `open_layer()` 返回外层）—— 修完判据和产品才第一次有资格进表。
    "音频生成面板·音色筛选",
]

# 契约里**声明**的、前置态在复刻侧**无法成立**的状态 → 必须出现在 skip 理由里的片段。
#
# ⚠️ 为什么要有这张表：A.3 原本一刀切「skipped 必须为空」，本意是
#   **不许静默少跑**。但复刻侧有一条前置态**永远**成立不了：AI 抽屉的
#   「会话列表」要求 `hasSession`（`disabled={!hasSession}`），而建出第一条
#   会话的**唯一** UI 路径是**发消息** —— 那是**计费动作**，探针/审计**绝不点**。
#   于是只剩两条路：把这条永久记成红，或者**声明**它。
#   声明**不是放水**，它比原来更严：
#     · 每条声明都必须带**原因片段**（对不上就是红的）；
#     · 一旦它**不再**skip，A.3c 立刻报错 —— 表会自己烂掉，不许烂着。
EXPECTED_SKIPS = {
    "AI 侧栏·会话列表": "入口**在 DOM 但 disabled**",
}

failures: list[str] = []
checks = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global checks
    checks += 1
    if ok:
        print(f"  PASS  {name}" + (f"  ({detail})" if detail else ""))
    else:
        print(f"  FAIL  {name}  {detail}")
        failures.append(name)


def strip_comments(src: str) -> str:
    """剥掉 **JS/TS** 注释，供「代码里到底有没有 X」用。

    ⚠️⚠️⚠️ 批 868 更正：这段 docstring 原来写着「JS/TS/Python」——
    **半句是错的**。这个状态机只认 `//` 与 `/* … */`，**不处理 Python 的
    `#`**；868 判「文本分支里不该再出现 `select_node(`」时照着这句错话用了
    它，结果被**自己写的注释**判成红的。Python 源码请用下面的
    `strip_py_comments()`。这句话留着是为了让下一个人别再照着它翻车。

    ⚠️⚠️ 批 864 揭穿了前一版的偷懒：按**行首**是不是 `//` / `*` / `/*`
    来过滤，遇到**块注释的续行**就漏 —— 续行不以 `*` 开头，于是注释正文
    被当成代码。实测后果：`JimengProjectInfoModal` 的注释里那句
    「资产库有 `bg-black/55` 全屏遮罩」漏进了「代码」，把一条断言
    **判成了红的**（Q.10）。判「有没有接某个 hook」时注释漏进来 = 假阳性，
    反过来就是假阴性 —— 两个方向都会骗人。

    所以这里老老实实走状态机：`//` 到行尾、`/* … */` 跨行、字符串字面量
    里的 `//` 不算注释（用引号配对粗略处理，足够本文件这批判据用）。

    ⚠️⚠️ 第一版状态机**漏了 Python 三引号**。被检查的审计脚本和探针都
    把内联 JS 装在三引号字符串里（`r` 前缀 + 三个引号），状态机把里面
    第一个引号当成单引号字符串的开头 ⇒ 整段 JS 被搅乱 ⇒ 6 条断言跟着
    一起红。「改对一件事，顺手弄坏五件」正是这一批在批的毛病，所以三引号
    必须当**一整个字面量**吞掉 —— 里头的单双引号一律不算边界。这样保留
    下来的正好是**真代码**。

    ⚠️ 写这段说明时自己又踩了一次同类的坑：在 docstring 里**直接写出
    三个连续引号**，会当场把 docstring 提前闭合、后面正文全被当成代码
    （py_compile 直接报 SyntaxError）。所以下面一律用「三个引号」这样的
    说法指代它，不写出来。
    """
    out: list[str] = []
    i, n = 0, len(src)
    in_block = False
    in_s = in_d = False
    quote = ""          # 三引号定界符（`"""` / `'''`），非空表示在三引号里
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        nxt2 = src[i + 2] if i + 2 < n else ""
        if quote:
            if src.startswith(quote, i):
                out.append(quote)
                i += 3
                quote = ""
                continue
            out.append(c)
            i += 1
            continue
        if in_block:
            if c == "*" and nxt == "/":
                in_block = False
                i += 2
                continue
            i += 1
            continue
        if in_s or in_d:
            if c == "\\":
                out.append(src[i:i + 2])
                i += 2
                continue
            if (in_s and c == "'") or (in_d and c == '"'):
                in_s = in_d = False
            out.append(c)
            i += 1
            continue
        if c == "/" and nxt == "*":
            in_block = True
            i += 2
            continue
        if c == "/" and nxt == "/":
            while i < n and src[i] != "\n":
                i += 1
            continue
        # ⚠️ 三引号**必须排在单引号判定之前**：`"""` 开头是三个 `"`，
        #    先判单引号的话只会吃掉一个，剩下的两个被当成空串边界。
        if (c == nxt2 and c in "\"'") or (nxt == c and nxt2 == c
                                          and c in "\"'"):
            quote = c * 3
            out.append(quote)
            i += 3
            continue
        if c == "'":
            in_s = True
        elif c == '"':
            in_d = True
        out.append(c)
        i += 1
    return "".join(out)


def strip_py_comments(src: str) -> str:
    """剥掉 **Python** 的注释（`#` 到行尾），字符串字面量里的 `#` 不算。

    ⚠️⚠️ 批 868：上面那个 `strip_comments` 的 docstring 写着「JS/TS/Python」，
    **这句话是错的** —— 它的状态机只认 `//` 和 `/* … */`，**根本不处理
    Python 的 `#`**。于是 868 判「文本分支里不该再出现 `select_node(`」那条
    断言，明明已经把注释剥了，还是被分支里那句
    「⚠️ 这里**绝不能**调 `select_node()`」判成红的 —— 撞上**自己写的注释**。
    教训和 864 那次一模一样：**「我以为我剥干净了」和「真剥干净了」之间，
    差一次自检**。所以这里老老实实用标准库 `tokenize` 按 token 剥，
    并且顺手把上面那句错话改掉（留着错话，下一批还会照着它翻车）。

    用 tokenize 的另一个好处：审计里那些装 JS 的三引号字符串会被当成
    STRING token 原样保留 —— 剥注释**不能**动字符串内容，否则内联 JS
    会被搅成一团（Q.11b / Q.12 就在钉这件事）。
    """
    import io
    import re
    import tokenize

    lines = src.splitlines(keepends=True)
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type != tokenize.COMMENT:
                continue
            (r0, c0), (r1, c1) = tok.start, tok.end
            # ⚠️⚠️ 第一版把 `lines` 放在**循环体里**、每次都从原始 `src`
            #    重新切 —— 于是每处理一个注释，前面的抹除全被冲掉，
            #    最后只剩**最后一个**注释生效。剥注释工具自己「看着在工作、
            #    实际只剥了一处」，比不剥更坏：它让人以为已经干净了。
            #    所以 `lines` 必须在循环**外**建一次，全程累积地改。
            for ln in range(r0 - 1, r1):
                s = lines[ln]
                a = c0 if ln == r0 - 1 else 0
                b = c1 if ln == r1 - 1 else len(s)
                if a < len(s):
                    s = s[:a] + re.sub(r"[^\n]", " ", s[a:b]) + s[b:]
                    lines[ln] = s
    except (tokenize.TokenError, IndentationError, SyntaxError):
        # 剥不动就**原样返回**：宁可让断言拿到带注释的原文（可能假红），
        # 也不让它悄悄返回半截被搅坏的源码（假绿更坏）。
        return src
    return "".join(lines)


def main() -> int:
    env = dict(os.environ)
    env["SNAP_OUT"] = str(OUT)
    # ⚠️⚠️ 批 850 加：**先删掉上一次的输出**。
    #    原来直接跑审计、然后 `if OUT.exists(): 读它`。可审计一旦中途崩
    #    （dev server 正在重编译、页面 30s 没就绪……），OUT 就**留在原地**，
    #    verifier 读到**上一轮的数据**却拿它当本轮结论继续判。
    #    850 实测踩到：审计崩了，verifier 拿着旧 JSON 报
    #    「源站基线表里 7 层」（实际已 11 层）+ 三条「打印行里根本没有这句」，
    #    看着像新改动把判据搞坏了，其实是**读了旧数据**。
    #    陈旧的数据比没有数据更坏：它看起来是结论。
    if OUT.exists():
        OUT.unlink()
    r = subprocess.run([sys.executable, str(AUDIT)], capture_output=True,
                       text=True, env=env, cwd=str(ROOT), timeout=600)
    out = (r.stdout or "") + (r.stderr or "")
    data = {}
    if OUT.exists():
        try:
            data = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            data = {"_parse_error": str(e)}
    else:
        print(f"!! 审计没写出 {OUT}（rc={r.returncode}）——"
              f"**不许拿旧数据当本轮结果**。审计输出末尾：\n"
              + "\n".join(out.splitlines()[-12:]))
    states = data.get("states", [])
    real = data.get("confirmed", [])
    by_modal = data.get("by_modal", [])
    st = data.get("self_test", {})
    kb = data.get("keyboard", [])
    kb_bad = data.get("keyboard_bad", [])
    kb_deep = data.get("keyboard_deep", [])
    kb_cov = data.get("keyboard_covered", [])
    # 846 的三个新桶也得在**顶部**取出来：A.0 要用它们算退出码，而 A.0 排在
    # §H 之前 —— 在 §H 里定义会 NameError（第一版就栽在这儿，py_compile 抓不到）。
    kb_ni = data.get("keyboard_no_initial_focus", [])
    kb_esc = data.get("keyboard_escaped", [])
    kb_arr = data.get("keyboard_arrow_dead", [])
    kbst = data.get("kb_self_test", {})

    # ── A. 普查本身 ───────────────────────────────────────────────
    print("— A. 普查跑通 —")
    # A.0 退出码：不能只看"是不是 0"。本批工具**真报出焦点被遮的缺陷**，
    #     退出码 1 是判据在干活，不是工具坏了。而自检不过又是**第三种**状态
    #     （退出码 2 = 结果不可信，既不是"通过"也不是"查到缺陷"）。所以这里
    #     断言的是**退出码与自检/缺陷桶三者一致**：
    #       自检不过      ⇒ 2
    #       自检过了且有缺陷 ⇒ 1
    #       自检过了且没缺陷 ⇒ 0
    #     三种都能两个方向失败：把 kb_covered 从退出码里漏掉（缺陷当通过放行）、
    #     写死 0、或自检红着却退 0，都会被抓住。
    # ⚠️ 批 865：新增两个**源站无关**的模态语义桶。退出码公式**必须**
    #    跟审计那一行同步 —— 审计已经把它们算进 `return 1 if (...)`，
    #    verifier 这边不跟，就会在「模态真出缺陷」时拿 rc=1 去撞 want_rc=0，
    #    报出一条「审计与自检不一致」的**假**告警。一致性检查自己不一致，
    #    比没有检查更坏。
    kb_mnf = data.get("keyboard_modal_no_focus", [])
    kb_mnt = data.get("keyboard_modal_no_trap", [])
    any_bad = bool(real or kb_bad or kb_cov or kb_ni or kb_esc or kb_arr
                   or kb_mnf or kb_mnt)
    self_ok = (
        kbst.get("reachable_before") is True
        and kbst.get("unreachable_when_stripped") is True
        and kbst.get("reachable_after_restore") is True
        and (kbst.get("covered_n_when_shut") or 0)
            > (kbst.get("covered_n_when_clear") or 0)
        and (kbst.get("covered_n_when_skin") or 0)
            == (kbst.get("covered_n_when_clear") or 0)
        and (kbst.get("skin_top_n") or 0) > 0)
    want_rc = 2 if not self_ok else (1 if any_bad else 0)
    check(f"A.0 退出码与自检/缺陷桶三者一致（实测 rc={r.returncode}，"
          f"自检={'过' if self_ok else '不过'}，"
          f"real={len(real)} / kb_bad={len(kb_bad)} / kb_covered={len(kb_cov)}）",
          r.returncode == want_rc,
          f"rc={r.returncode} 期望={want_rc}")
    check("A.1 结果可解析", not data.get("_parse_error"),
          str(data.get("_parse_error"))[:70])
    check(f"A.2 跑了 {len(states)} 个状态（覆盖面下限 {len(EXPECTED_STATES)}）",
          len(states) >= len(EXPECTED_STATES))
    _sk = data.get("skipped") or []
    _unexpected = [s for s in _sk
                   if not any(s.startswith(k + "（") for k in EXPECTED_SKIPS)]
    check(f"A.3 skipped（前置态没成立）只剩**已声明**的 "
          f"{len(EXPECTED_SKIPS)} 条 —— 不许静默少跑",
          not _unexpected,
          ("多出来的=" + str(_unexpected[:2])[:120]) if _unexpected
          else f"共 {len(_sk)} 条，全在声明里")
    check("A.3b 每条声明的 skip 理由里都**带着原因片段**"
          "（只写状态名不算数 —— 「没测到」必须说清是没测到还是没成立）",
          all(any(s.startswith(k + "（") and frag in s for s in _sk)
              for k, frag in EXPECTED_SKIPS.items()),
          "; ".join(k for k, frag in EXPECTED_SKIPS.items()
                    if not any(s.startswith(k + "（") and frag in s
                               for s in _sk)))
    _stale = [k for k in EXPECTED_SKIPS
              if not any(s.startswith(k + "（") for s in _sk)]
    check("A.3c 没有**过期**的声明（某个已声明的状态这轮跑到了 ⇒ "
          "该把声明收窄，否则这张表会变成空话）",
          not _stale, f"过期={_stale}")

    # ── B. 覆盖面：每个已知状态都真的跑到了 ────────────────────────
    print("\n— B. 覆盖面下限（工具自己无法保证的那部分）—")
    missing = [s for s in EXPECTED_STATES if s not in states]
    check(f"B.1 契约列出的 {len(EXPECTED_STATES)} 个状态全部跑到",
          not missing, f"没跑到={missing}")

    # ── C. 判据能失败（这是本工具存在的理由）────────────────────────
    print("\n— C. 判据能失败：盖一层遮挡物，必须被判成点不着 —")
    check("C.1 自检字段在结果里", bool(st), str(st)[:70])
    check("C.2 盖上遮挡物后，命中测试确实判被挡",
          st.get("blocked_when_covered") is True,
          f"实测={st.get('blocked_when_covered')}")
    check("C.3 撤掉遮挡物后恢复可点（证明是遮挡造成的，不是本来就不行）",
          st.get("reachable_when_clear") is True,
          f"实测={st.get('reachable_when_clear')}")
    check("C.4 输出里印出了自检结论（不许只在 JSON 里悄悄存着）",
          "判据能失败" in out or "判据恒空" in out,
          [l for l in out.splitlines() if "自检" in l][:1])

    # ── D. 「缺陷」与「INFO」必须分开，且分界写死在源码里 ───────────
    print("\n— D. 分档：浮层盖住静态控件是正常的，不算缺陷 —")
    check(f"D.1 缺陷桶 {len(real)} 条（同一层自己压自己）",
          isinstance(real, list), f"类型={type(real).__name__}")
    check(f"D.2 INFO 桶 {len(by_modal)} 条（模态遮罩 / 跨层遮挡，正常）",
          isinstance(by_modal, list), f"类型={type(by_modal).__name__}")
    overlap = {id(x) for x in real} & {id(x) for x in by_modal}
    check("D.3 两个桶不重叠（同一个控件不能既算缺陷又算正常）",
          not overlap, f"重叠 {len(overlap)} 条")
    bad_real = [x for x in real if x.get("covered_by_modal")]
    check("D.4 缺陷桶里没有一条是被全屏模态盖住的（那属于正常）",
          not bad_real, f"混进来 {len(bad_real)} 条")
    bad_info = [x for x in by_modal if not x.get("covered_by_modal")
                and x.get("same_layer")]
    check("D.5 INFO 桶里没有一条是「同一层自己压自己」（那属于缺陷）",
          not bad_info, f"混进来 {len(bad_info)} 条")
    # 批 843：跨层遮挡必须**如实**记成 INFO，而且每条都要说清自己属于哪一层。
    # 第一版那条 finding 写的是「音色: 音色库」，而空画布菜单里根本没这一项 ——
    # 当时点在了节点上。没有 `layer` 字段，看到的人只能自己猜。
    no_layer = [x for x in by_modal if "layer" not in x]
    check("D.6 每条 finding 都带 `layer`（属于哪一层必须可读）",
          not no_layer, f"缺 layer 的 {len(no_layer)} 条")

    # ── E. 源码侧的防阉割契约 ─────────────────────────────────────
    print("\n— E. 源码侧的防阉割契约 —")
    asrc = AUDIT.read_text(encoding="utf-8")
    # ① 采样点不许退回「只测中心」：一个点被挡只说明那个点被挡
    m = re.search(r"^SAMPLES = \[(.*?)\]", asrc, re.M | re.S)
    n_samples = len(re.findall(r"\(0\.\d+, 0\.\d+\)", m.group(1))) if m else 0
    check("E.1 采样点 ≥ 5（只测中心会把「偏了一点被挡」误判成点不着）",
          n_samples >= 5, f"实际 {n_samples} 个")
    # ② 命中测试必须**多轮**：链式遮挡一层藏一层
    check("E.2 确认步骤会穿透多层遮挡（`for (let round` 存在）",
          "for (let round" in asrc and "round < 4" in asrc)
    # ③ 开发浮层必须排除，否则开发态下满屏假阳性
    check("E.4 排除了 `nextjs-portal`（Next 开发态调试浮层，pointer-events 是 auto）",
          "nextjs-portal" in asrc)
    # ④ 分档判据必须在源码里，而不是只体现在结果上
    check("E.5 分档判据在源码里（`in_layer` + `covered_by_modal`）",
          "in_layer" in asrc and "covered_by_modal" in asrc)
    # ⑤ 退出码：自检不过 = 2，且最终码由缺陷桶推出
    # 批 844 之后这两条都变强了：自检有**两条**（指针 + 键盘），退出码由缺陷桶推出。
    # 批 845 再加第三个桶（`kb_covered`，焦点停在被遮住的控件上）。断言跟着契约
    # 走，不跟着旧文本走。
    check("E.6 两条自检任一不过都走退出码 2（不是 0，否则 CI 当通过）",
          re.search(r"if not ok_self or not ok_kb_self:\s*\n\s*return 2",
                    asrc) is not None)
    check("E.7 最终退出码由**六个**缺陷桶推出（指针 1 + 键盘 5，"
          "不许写死 0）",
          "return 1 if (real or kb_bad or kb_covered" in asrc
          and "kb_no_initial or kb_escaped or kb_arrow_dead" in asrc)
    # ⑥ 打不开的状态要记 skipped，不许静默跳过
    check("E.8 下拉打不开会记进 `skipped`（「跑了但没看见」≠「没跑」）",
          "skipped.append(f\"{tag}（打不开" in asrc)
    # ⑦ 视口外的控件不许参与判定
    check("E.9 视口外的控件被排除（滚一下就够得到，不算点不着）",
          "视口外" in asrc)
    # ⑩ 批 843：跨层 vs 同层必须分档（第一版把跨层也算成缺陷，害得一条
    #    「画布右键菜单里的音色项点不到」差点被当成产品缺陷去修）
    check("E.10 分档落在「同一层自己压自己」上（`same_layer`）",
          "same_layer" in asrc)
    check("E.11 右键落点先验证是空画布（硬点会开成节点菜单）",
          "找不到确认是空画布的落点" in asrc)
    # ⑫ 层已经开着的时候不许再点触发器（那是把它**关掉**）
    check("E.12 `open_dropdown` 有 `want_tid` 短路",
          "want_tid" in asrc)

    # ── F. 键盘通道（批 844 加）──────────────────────────────────
    print("\n— F. 键盘可达性：Tab 进不进得去浮层 —")
    probed = [k for k in kb if k.get("ok") is not None]
    check(f"F.1 键盘探测覆盖 ≥ 10 个开着浮层的状态（实测 {len(probed)}）",
          len(probed) >= 10)
    check(f"F.2 Tab 进不去的浮层 = 0 —— 实测 {len(kb_bad)}",
          not kb_bad, f"进不去={[(k.get('state'), k.get('layer')) for k in kb_bad][:2]}")
    # 「没浮层可探」必须单独记账，不能混进通过
    none_rows = [k for k in kb if k.get("ok") is None]
    check(f"F.3 「那一刻没有打开的浮层」= {len(none_rows)} 个，"
          "且**不许**被算成通过", isinstance(none_rows, list))
    # 上限本身是判据的一部分：偏深 ≠ 缺陷，但得看得见
    check("F.4 「进得去但偏深」单列成 INFO（上限以内不是缺陷）",
          isinstance(kb_deep, list)
          and all(k.get("ok") is True for k in kb_deep),
          f"偏深={[(k.get('state'), k.get('tabs')) for k in kb_deep][:2]}")
    check("F.5 键盘自检：摘掉 tabindex 后必须判成进不去",
          kbst.get("unreachable_when_stripped") is True,
          f"实测={kbst.get('unreachable_when_stripped')}")
    check("F.6 键盘自检：还原后必须恢复进得去（证明是 tabindex 造成的）",
          kbst.get("reachable_after_restore") is True
          and kbst.get("reachable_before") is True,
          f"before={kbst.get('reachable_before')} "
          f"after={kbst.get('reachable_after_restore')}")
    check("F.7 键盘自检结论印在输出里（不许只在 JSON 里）",
          "键盘判据能失败" in out or "键盘判据恒真" in out,
          [l for l in out.splitlines() if "键盘判据" in l][:1])
    check("F.8 **真按 Tab 键**（不许自己模拟焦点推进）",
          'page.keyboard.press("Tab")' in asrc,
          "模拟版第一版栽了：候选表 `button:not([disabled])` 不看 tabindex=-1，"
          "自检把 tabindex 摘光它仍说进得去 —— 是自检把工具判红的")
    check("F.9 键盘探完必须收浮层（否则下一状态认到同一层）",
          re.search(r"kb_rows\.append\(.{0,600}?close_open\(\)", asrc, re.S)
          is not None)

    # ── G. 焦点停在**被遮住**的控件上（批 845 加）─────────────────
    #    这一桶和指针那条的**分档正好相反**：鼠标点不到被模态盖住的控件是正常
    #    （关掉模态就能点）；但焦点停在那上面时**焦点环是看不见的**，用户既不
    #    知道自己停在哪、也不知道刚才那下 Tab 有没有生效。
    print("\n— G. 焦点不许停在被浮层遮住的控件上 —")
    check(f"G.1 这一桶的字段在结果里（当前 {len(kb_cov)} 条）",
          isinstance(kb_cov, list))
    for k in kb_cov:
        c = k.get("covered") or {}
        check(f"G.2 {k.get('state')} 的 finding 指名到具体那个控件"
              f"（第 {c.get('at_tab')} 次 Tab，{len(kb_cov)} 条之一）",
              bool(c.get("at_tab")) and bool(c.get("al") or c.get("tid")),
              f"落在 al={c.get('al')!r} tid={c.get('tid')!r}")
    check("G.3 每条 finding 带 covered_n（全程有多少个这样的焦点位）",
          all("covered_n" in k for k in kb_cov),
          f"缺 covered_n 的 {sum(1 for k in kb_cov if 'covered_n' not in k)} 条")
    # 只报「焦点停在了看不见的地方」是**现象**，不是**病因**：修的人第一句就会问
    # 「被谁盖住的」。所以每条 finding 必须同时指名盖住它的是哪个浮层锚。
    #
    # ⚠️⚠️ 批 863 改这里：第一版拿 `kb_cov`（产品当下真有的缺陷）当验钞机。
    #    863 把全屏预览那个**真缺陷修好**之后，`kb_cov` 变空，这条断言自己
    #    红了 —— 契约被绑在**产品状态**上，而不是绑在判据的**能力**上。
    #    「修好了」被判成「判据坏了」。
    #    改成拿**自检的阳性夹具**验：`covered_when_shut` 那一趟**保证**盖了
    #    一层 `inset:0` 的不透明模态，finding 必然存在。形状与产品无关，
    #    缺陷修不修都成立 —— 这才是这条断言本来要问的东西。
    #    两边都查：夹具里必须有，产品里**有的话**也必须合格。
    _shut_cov = kbst.get("shut_covered") or {}
    check("G.3b 每条 finding 指名**被哪个浮层盖住**（浮层锚的对照，不是光说看不见）"
          "—— 验的是判据的**能力**，拿自检阳性夹具（必然有 finding）当样本，"
          "不再绑在产品当下有没有缺陷上",
          bool(_shut_cov.get("top"))
          and _shut_cov.get("top_anchor") is not None
          and _shut_cov.get("top_anchor") != _shut_cov.get("focus_anchor")
          and bool(_shut_cov.get("edges")),
          f"夹具 finding={json.dumps(_shut_cov, ensure_ascii=False)[:150]}")
    check("G.3c 产品**当下**若有 covered finding，每一条也都得指名浮层锚"
          "（实测 {n} 条）".format(n=len(kb_cov)),
          all(((k.get("covered") or {}).get("top")
               and (k.get("covered") or {}).get("top_anchor")
                   != (k.get("covered") or {}).get("focus_anchor")
               and (k.get("covered") or {}).get("edges"))
              for k in kb_cov),
          "; ".join(
              f"{k.get('state')}←{(k.get('covered') or {}).get('top_anchor')}"
              f"（边 {(k.get('covered') or {}).get('edges')}）"
              for k in kb_cov)[:170])
    # 自检：盖一层遮挡物，被遮住的焦点位必须**变多**。比的是计数不是"有没有" ——
    # 基线里本来就真有几处（那正是本批查出来的缺陷），"撤掉后不再报"是错前提，
    # 第一版就栽在这儿、自检把自己判红了。
    check("G.4 自检：盖上遮挡物后被遮住的焦点位**变多**（判据对遮挡敏感）",
          (kbst.get("covered_n_when_shut") or 0)
          > (kbst.get("covered_n_when_clear") or 0),
          f"{kbst.get('covered_n_when_clear')} → {kbst.get('covered_n_when_shut')}")
    # ⚠️ 反向自检：只验「会响」不够，还得验「分得清」。给每个可聚焦控件盖一层
    #    「自己的皮」——**透明**、外扩 2px、插成同层兄弟，也就是**真的压在焦点
    #    环上**。判据必须**不多报**：透明的东西什么也盖不住。
    #    这一条把前三代判据当场判红 —— 它们只问「栈顶是不是外人」，压根不看
    #    透明不透明。源站的 `text-flow-node-full` 正是这种皮（探针 845c 实测：
    #    和焦点所在节点**不同支**、却和它同框）。
    check("G.4b 反向自检：给每个控件盖一层「自己的皮」（透明、外扩 2px、"
          "同层兄弟）后，被遮的焦点位**一个都不多**（专治前三代判据）",
          (kbst.get("skin_n") or 0) > 0
          and (kbst.get("covered_n_when_skin") or 0)
              == (kbst.get("covered_n_when_clear") or 0),
          f"铺了 {kbst.get('skin_n')} 层皮，"
          f"{kbst.get('covered_n_when_clear')} → {kbst.get('covered_n_when_skin')}")
    # 反向自检还必须**自证夹具真在局**：皮当过栈顶 0 次 ⇒ 上面那条恒真。
    check("G.4b2 反向自检**自证夹具真在局**（皮当过栈顶 > 0 次，"
          "否则「不多报」是恒真的空话）",
          (kbst.get("skin_top_n") or 0) > 0,
          f"皮当过栈顶 {kbst.get('skin_top_n')} 次")
    # 阳性夹具必须**不透明**：透明的东西按第四版判据什么也盖不住，拿它当阳性
    # 夹具就是在要求判据犯错。
    check("G.4d 阳性夹具（自检遮挡层）必须**不透明**"
          "（透明的盖子按新判据理应不多报，拿它当阳性就是要求判据犯错）",
          re.search(r"data-kbcover-probe.{0,420}?background:rgb\(13,13,13\)",
                    asrc, re.S) is not None)
    # 结构判定：把 `ok_kb_self = ...` 到下一条 print 之间**切出来**看里面有没有
    # 那条反向比较。早先用固定长度的正则（`.{0,900}?`）去数距离，结果注释一多
    # 就被顶穿 —— 判据跟着注释长度漂移，这本身就是一种"判据会骗自己"。
    _ok_blk = ""
    _m = re.search(r"ok_kb_self\s*=", asrc)
    if _m:
        _nxt = re.search(r"\n\s*print\(", asrc[_m.end():])
        _ok_blk = asrc[_m.end(): _m.end() + (_nxt.start() if _nxt else 4000)]
    check("G.4c 反向自检**真的接进了** `ok_kb_self`（写完忘了接上 = 没有自检）",
          "covered_n_when_skin" in _ok_blk
          and "skin_top_n" in _ok_blk,
          f"ok_kb_self 块 {len(_ok_blk)} 字符，"
          f"含反向比较={'covered_n_when_skin' in _ok_blk} "
          f"含夹具自证={'skin_top_n' in _ok_blk}")
    # ⚠️⚠️ 批 863 改这里，而且改的是这条断言的**理由**，不是它的结论。
    #    老理由写的是「层必须深，因为 Tab 1 就进去的层**照不到**被遮住的控件」。
    #    863 第④处改动之后这句话**不成立了**：层内控件被**别的**浮层盖住照样
    #    该报，层内照样算 `covered_n`。新搜索面板第一次 Tab 就在层内
    #    （§79 的定论），深度已经是 1，而 `covered_n_when_shut` 实测 0 → 1 照活。
    #    所以真正该钉的是**灵敏度有没有被记在案** —— 那个夹具现在只采到
    #    `walked_when_shut` 个焦点位（老面板同一夹具是 39 步 / 32 个被遮），
    #    判据覆盖面确实缩小了。缩小是事实，不是不存在；不记下来才是问题。
    check("G.5 自检用的层仍是搜索面板夹具，**且灵敏度记在案**"
          "（老理由「必须深」已被 863 第④处推翻：层内控件也算 covered_n，"
          "深度不再是前提；真正要盯的是这趟采了几个焦点位）",
          kbst.get("covered_probe_layer") == "jimeng-search-overlay"
          and kbst.get("walked_when_shut") is not None
          and (kbst.get("walked_when_shut") or 0) >= 1,
          f"夹具={kbst.get('covered_probe_layer')!r} "
          f"正向夹具采了 {kbst.get('walked_when_shut')!r} 个焦点位"
          f"（老面板同一夹具 39 步）")
    # ⚠️ 批 863 改这里：判定的**字面量**跟着返回形态一起变了。863 让采样 JS
    #    进层也往下走，返回时 `state` 变成三态 `inside / covered / other`
    #    （原来只有两态，且进层直接早退）。判的是「`occluded` 这个判据还在
    #    算、且被 `covered` 这个名字收着」，不是某一行具体怎么写。
    check("G.6 键盘探针在每一步都判「焦点是否被遮住」（源码里真有这一步）",
          "occluded ?" in asrc and "'covered'" in asrc,
          "返回里找不到 occluded/'covered' 的判据")
    # 判据的**形状**本身就是断言对象：前两版都被证伪过，而且错的方向相反
    # （第 1 版太松、第 2 版太严），病根都是拿 DOM 包含关系回答视觉问题。
    # 第 3 版只问「栈顶是不是**另一个浮层**」。
    check("G.6b 判「被遮」用**绘制栈**（elementsFromPoint），不是单点命中",
          "document.elementsFromPoint(" in asrc)
    check("G.6c 判据问的是「**焦点环还在不在**」：采样**边框**而不是中心，"
          "且盖住它的东西必须**不透明**（透明的东西什么也盖不住）",
          "EDGE" in asrc and "paintsOver" in asrc
          and "b.left - 1" in asrc and "b.height / 2" in asrc)
    check("G.6d 祖先的背景**不算**遮挡（祖先画在下面，不是盖在上面的）",
          re.search(r"n === a \|\| \(n\.contains && n\.contains\(a\)\)\)\s*"
                    r"return false", asrc) is not None)
    check("G.6e 旧的包含关系判据**不许**留在源码里（三代都栽在这儿）",
          "!a.contains(hit) && !hit.contains(a)" not in asrc
          and "!a.contains(hit) && !hit.contains(hit)" not in asrc)
    check("G.6f `nextjs-portal` 当判据的豁免**不许**留着"
          "（它只是结构容器、什么都不画，第 3 版就栽在它上面）",
          "topInPortal" not in asrc)
    # 打印行里的数字必须和 JSON 对得上。上一版就栽在"判据换了、打印行还挂在
    # 旧字段上"：输出里印的是 `covered=None、撤掉后不再报=None`，看着像句结论，
    # 其实什么都没说 —— 比不印更坏，因为它看着像有结论。
    cline = [l for l in out.splitlines() if "盖一层遮挡物后被遮住的焦点位" in l]
    printed = re.findall(r"焦点位 (\d+) → (\d+)", cline[0]) if cline else []
    check("G.7 打印行印的是**新判据的计数**且与 JSON 对得上（不是 None、不是空话）",
          bool(printed)
          and printed[0][0] == str(kbst.get("covered_n_when_clear"))
          and printed[0][1] == str(kbst.get("covered_n_when_shut")),
          (cline[0].strip()[:96] if cline else "打印行里根本没有这句"))

    # ── H. 焦点陷阱 / 方向键（批 846 加）─────────────────────────────
    #    这一节的全部要害：**分档只能按源站基线表走**。表里没有的层，源站行为
    #    未知 —— 「复刻这边测出来是 0」和「源站也是 0」是两回事。§63 已经吃过
    #    一次这个亏（右键菜单 45 次探不到，差点被写成"源站也这样"）。
    print("\n— H. 焦点陷阱 / 方向键：分档只按源站基线走 —")
    kb_judged = data.get("keyboard_judged_layers", [])
    kb_ns = data.get("keyboard_not_sampled", [])
    base = data.get("source_baseline", {})
    probed_layers = sorted({k.get("layer") for k in kb
                            if k.get("ok") is True and k.get("layer")})
    check(f"H.1 源站基线表**在结果里**，且每条都写明取样出处",
          bool(base) and all(v.get("src") and v.get("src_tid")
                             for v in base.values()),
          f"表里 {len(base)} 层：{sorted(base)}")
    check("H.2 基线表的字段齐（接管焦点 / Tab 困不困 / 方向键动不动）",
          all({"takes_focus_at_open", "traps_tab", "arrows_move"} <= set(v)
              for v in base.values()),
          f"字段={[sorted(v) for v in base.values()][:1]}")
    # 核心：每个探到的层，要么在表里被判，要么**明确**记进 not_sampled。
    # 两者都不许漏 —— 漏了就变成"悄悄按推测判"或"悄悄当通过"。
    unaccounted = [t for t in probed_layers
                   if t not in base and t not in
                   {n.get("layer") for n in kb_ns}]
    check(f"H.3 探到的 {len(probed_layers)} 个层**全部有账**"
          f"（要么按源站基线判了，要么明确记成「源站没取过样」）",
          not unaccounted,
          f"能判 {len(kb_judged)}、没取样 {len(kb_ns)}、无账 {unaccounted}")
    check(f"H.4 「源站没取过样」的层被**显式列出**（当前 {len(kb_ns)} 个，"
          "且每条都带为什么没取样）",
          bool(kb_ns) and all(n.get("layer") and n.get("why") for n in kb_ns),
          "; ".join(f"{n.get('layer')}" for n in kb_ns)[:150])
    # 视频全屏那一格必须**留在** not_sampled 里：源站那一版画布上没有可测的
    # 视频全屏，拿时间线全屏的行为替它判就是拿证据不足当证据。
    check("H.5 视频全屏**不许**拿时间线全屏的行为替它下结论"
          "（源站那一版画布上没有可测的视频全屏）",
          any(n.get("layer") == "video-fullscreen-preview"
              for n in kb_ns),
          f"not_sampled={[n.get('layer') for n in kb_ns]}")
    check("H.6 陷阱测量从「焦点**已经在层里**」起手（不是冷启动）——"
          "冷启动量不到「进去之后出不出得来」",
          re.search(r"if step\.get\(\"state\"\) == \"inside\":.{0,700}?"
                    r"escape_probe\(layer_tid\)", asrc, re.S) is not None)
    check("H.7 每个破坏性测量之间**重新把焦点塞回层里**"
          "（串着跑三个破坏性测量，只有第一个是准的）",
          "refocus_inside(layer_tid)" in asrc
          and re.search(r"def arrow_probe.{0,3000}?refocus_inside\(layer_tid\)",
                        asrc, re.S) is not None)
    for k in kb_ni:
        check(f"H.8 {k.get('state')}：源站开层即接管焦点，复刻没有",
              bool(k.get("src_tid")) and bool(k.get("at_open")),
              f"源站={k.get('src_tid')!r} 复刻焦点停在 {k.get('at_open')!r}")
    for k in kb_esc:
        check(f"H.9 {k.get('state')}：Tab 从层里逃出去了"
              f"（第 {k.get('escaped_at')} 次，落在 "
              f"al={(k.get('landed') or {}).get('al')!r}）",
              bool(k.get("src_tid")) and (k.get("landed") or {}).get("al") is not None)
    for k in kb_arr:
        check(f"H.10 {k.get('state')}：方向键焦点不动"
              f"（ArrowDown 4 次都是 {k.get('seq', [None])[0]!r}）",
              bool(k.get("src_tid")) and bool(k.get("seq")))

    # ── I. 覆盖面：键盘到底探到了几层（批 849 加）────────────────────
    #    §66 记的那个缺口：**普查有 24 个状态，键盘只探到 12 层**。查下来
    #    **判据一点毛病都没有**（探针 849 判决：缺口 4/4、对照 2/2 全认得
    #    出来，`inShell` 六条判据全过）。病在**脚本自己**：
    #        f"{scope} {sel}",  scope = "A, B"
    #    逗号优先级高于后代空格，整条被读成「**A 自己** 或 **B 里的按钮**」，
    #    `.first` 命中那个 div，点了个寂寞。而 `open_dropdown` 只看
    #    `loc.count()`（div 确实在，非 0）⇒ 返回 True ⇒ 状态"跑了"、
    #    指针普查照跑（那些是真数据）、**键盘栏整条空白**。
    #    「跑了」和「探到了」被当成一回事 —— 假零比报错更危险。
    print("\n— I. 覆盖面：跑的 ≠ 探到的 —")
    # I.1 判据形状：scope 必须**逐项**挂后缀。老写法不许留在源码里。
    #     ⚠️ 这里必须用**字面量**去源码里找，不能把源码片段当 Python 表达式
    #     写出来 —— 第一版就栽在这儿：`", ".join(f"{p} {sel}" for p in parts)`
    #     里的 `{p}` 会被 verifier 自己求值，`parts` 直接 NameError。
    #     **判据自己抛异常 = 这批验证全废**（前 60 条已跑的结果一起丢）。
    _lit_scoped = '", ".join(f"{p} {sel}" for p in parts)'
    check("I.1 scope 用 `_scoped()` **逐项**挂后缀"
          "（逗号列表整体拼后缀 = `.first` 命中 scope 自己，点了寂寞）",
          "def _scoped(" in asrc and _lit_scoped in asrc.replace("\n", " "))
    check("I.2 老的 `f\"{scope} {sel}\"` 拼接**不许**留在源码里"
          "（能把这行放回源码里的话，说明判据没钉住老写法）",
          'f"{scope} {sel}"' not in asrc)
    # I.2b `_scoped` 本体也得自证：拿一个含逗号的 scope 去调它，结果必须
    #      **每一项**都带上了后缀，且不带那个会吞掉后缀的「scope 自己」分支。
    _m = re.search(r"def _scoped\(.*?\n(?=\s*def )", asrc, re.S)
    _sc = _m.group(0) if _m else ""
    check("I.2b `_scoped` 对逗号 scope 的输出是**逐项**带后缀的"
          "（用 '.A, .B' + 'button' 验：两段都在，且没有裸的 '.A,' 分支）",
          ".split(\",\")" in _sc
          and _sc.count("{p} {sel}") == 1
          and not re.search(r'return f?"\{scope\} \{sel\}"', _sc),
          f"_scoped {len(_sc)} 字符")
    # I.3 「点了不等于开了」：点完必须回查层在不在 DOM 里。
    _m = re.search(r"def open_dropdown\(.*?\n(?=\s*def )", asrc, re.S)
    _od = _m.group(0) if _m else ""
    check("I.3 `open_dropdown` 点完**回查** `want_tid` 在不在 DOM 里"
          "（只看 `loc.count()` 的话，「点到 scope 自己」会被记成打开成功）",
          re.search(r"want_tid and not page\.locator\(", _od) is not None,
          f"open_dropdown {len(_od)} 字符")
    # I.4 生成面板那 4 个下拉的 scope 里必须有「选中节点」——
    #     `JimengGenPanel` 是节点的**直系子节点**（既不在 NodeToolbar 也不在
    #     NodePanel 里），只写 toolbar/panel 的 scope 一个都匹配不上。
    check("I.4 视频生成面板 4 个下拉的 scope 含 `.react-flow__node.selected`"
          "（生成面板挂在节点里，不在 NodeToolbar/NodePanel 里）",
          re.search(r"try_measure\(f\"视频生成面板·\{tid\}下拉\".{0,300}?"
                    r"react-flow__node\.selected", asrc, re.S) is not None)
    # I.5 回归钉子：这 9 个层**必须真的探到**。逗号 bug 活着的时���，它们
    #     表现为「键盘栏空白」；改回老写法，这一条立刻红。
    MUST_PROBE = [
        "gen-model-listbox", "gen-video-size-listbox",
        "gen-mode-listbox", "gen-duration-listbox",
        "audio-music-model-listbox", "audio-music-duration-listbox",
        "audio-voice-model-listbox", "audio-gen-mode-listbox",
        "audio-all-voices-listbox",
    ]
    missed = [t for t in MUST_PROBE if t not in probed_layers]
    check(f"I.5 生成/音频面板共 {len(MUST_PROBE)} 个下拉层**真的探到了**"
          "（不是 skipped、也不是键盘栏空白）",
          not missed,
          f"探到 {len(MUST_PROBE) - len(missed)}/{len(MUST_PROBE)}；"
          f"缺 {missed or '无'}")
    # I.6 覆盖率本身不许悄悄缩回去：这 9 个是本批从 12 层补到 21 层的全部来源。
    check(f"I.6 键盘探到的层**不少于 21**（本批从 12 补上来；少了就是又漏了）",
          len(probed_layers) >= 21,
          f"实际 {len(probed_layers)} 层：{probed_layers}")
    # I.7 「跑完却没认到层」必须**分类记账**：名单外的（本来就有层却没开）
    #     一条都不许有；名单内的（空态/工具条本体/面板本体）是正常的。
    #     ⚠️ 判据不能写成「整表为空」—— 名单内那 3 条**本来就该在表里**，
    #     那样写会把「记账做对了」判成 FAIL。
    nl = data.get("keyboard_no_layer", [])
    nl_bad = [n for n in nl if not n.get("expected")]
    check("I.7 「没认到层」**分类记账**：名单外（本该有层却没开）0 条；"
          f"名单内（本来就没有浮层）{len(nl) - len(nl_bad)} 条且每条带 why",
          not nl_bad and all(n.get("why") for n in nl),
          f"名单外 {len(nl_bad)} 条 {nl_bad}；名单内 "
          f"{[n.get('state') for n in nl if n.get('expected')]}")
    # I.8 「按满 Tab 上限」单列一桶，**不许混进缺陷**。
    #     849 为「canvas-context菜单 Tab 60 次进不去」查了四轮才定位：那是
    #     flaky（同一份代码量到 34 / 37 / 39 / **49** 次，60 的余量太小），
    #     而判据把偶发当确定报成了产品缺陷。capped 的语义是「**没测出来**」，
    #     与 skipped 同级：有账，但不下结论。
    capped = data.get("keyboard_capped", [])
    check("I.8 本轮没有「按满 Tab 上限还没测到」的层"
          "（有的话是「没测出来」，既不当缺陷也不当通过 ⇒ 退出码 2）",
          not capped,
          f"capped={[k.get('state') for k in capped]}")
    check("I.9 本轮没有「探完没把层收掉」的层"
          "（漏下去的层会污染后面每个状态的键盘结果，840 记过一次、849 又一次）",
          not data.get("keyboard_leaks"),
          f"leaks={[(k.get('state'), k.get('stuck')) for k in data.get('keyboard_leaks', [])]}")
    # I.10 判据失败时**必须带轨迹**。849 为那条 flaky 缺陷查了四轮全靠猜，
    #     最后靠「让判据自己说」才收工 —— 轨迹是判据自己的责任，
    #     不是排查者的额外工作（§64「布尔判据要配一条看轨迹的断言」）。
    kb_with_trace = [k for k in kb if k.get("trace")]
    check("I.10 每条键盘测量都带 `trace`（Tab 轨迹）——"
          "只交一个 ok:False 等于交一张没有地址的病历",
          bool(kb_with_trace) and len(kb_with_trace) == len(kb),
          f"带 trace {len(kb_with_trace)}/{len(kb)}")
    check("I.11 失败措辞区分「按满上限」与「真进不去」"
          "（`capped` 标志 + why 里明说要看 trace）",
          re.search(r'"capped":\s*True', asrc) is not None
          and "看 trace" in asrc)
    # I.12 Tab 上限必须离实测值留足余量。`canvas-context-menu` 冷启动实测
    #     34/37/39/**49** 次（同一份代码，随画布上节点数浮动）—— 上限 60 时
    #     余量最小只有 11 次，于是 flaky。120 才够。
    _mt = re.search(r"def keyboard_probe\([^)]*max_tabs:\s*int\s*=\s*(\d+)", asrc)
    check("I.12 Tab 上限 ≥ 120（右键菜单冷启动实测最高 49 次，"
          "60 的余量太小会 flaky）",
          bool(_mt) and int(_mt.group(1)) >= 120,
          f"上限={_mt.group(1) if _mt else '?'}")

    # ── J. 批 850：生成面板 4 个下拉的源站基线 ───────────────────────────
    #    848 的范围限制是「源站这 4 个下拉从未被鼠标打开过」；849 把复刻侧
    #    的键盘覆盖面补到 21 层之后，它们就成了 9 个 `kb_not_sampled` 里的
    #    4 个。这一批去源站**打开**了它们并取到样，于是：
    #      · 基线表 7 → 11 层
    #      · 判据从「没测过」变成「确认缺陷」：复刻这 4 层**开层不接管焦点**
    #      · 修完（`useTakeFocusAtOpen`）4 条清零
    print("\n— J. 生成面板 4 个下拉：源站首次取到样 —")
    GEN4 = ["gen-model-listbox", "gen-video-size-listbox",
            "gen-mode-listbox", "gen-duration-listbox"]
    check("J.1 基线表里**必须有**这 4 层（848 记的是「从未被打开过」）",
          all(t in base for t in GEN4),
          f"表里 {len(base)} 层；4 个 gen-* 在不在："
          f"{[t for t in GEN4 if t in base]}")
    check("J.2 每一项都写明**取样出处**与**层是怎么认出来的**"
          "（这 4 层源站**没有 testid**，靠 role + 矩形）",
          all(base.get(t, {}).get("src") and base.get(t, {}).get("src_identified_by")
              and "无 testid" in base.get(t, {}).get("src_tid", "")
              for t in GEN4),
          "; ".join(f"{t}={base.get(t, {}).get('src_identified_by', '')[:30]}"
                    for t in GEN4))
    # ⚠️ 方向键：850/851 都记成「没测到」（None），**852 查明那是判据缺陷** ——
    #    `moved` 漏掉了按之前的起点，把「走一步」判成了「不动」。这条判据
    #    随之更新：现在要求**是实测过的布尔**，而不是 `None`。
    #    （「不许偷偷填值」那条依然成立 —— 只不过 852 已经**真的**测了。）
    check("J.3 四层的方向键是**实测过的布尔**（不是 `None`）—— "
          "852 查明 850/851 记的「没测到」是 `moved` 漏掉起点的判据缺陷",
          all(isinstance(base.get(t, {}).get("arrows_move", None), bool)
              for t in GEN4),
          f"{ {t: base.get(t, {}).get('arrows_move', 'MISSING') for t in GEN4} }")
    # 源站这 4 层：接管焦点 / 不困 Tab / Esc 不归位（后两条照抄源站 a11y 失手）
    check("J.4 源站这 4 层实测是「接管焦点 + 不困 Tab + Esc 不归位」",
          all(base.get(t, {}).get("takes_focus_at_open") is True
              and base.get(t, {}).get("traps_tab") is False
              and base.get(t, {}).get("esc_returns_to_trigger") is False
              for t in GEN4),
          f"{ {t: (base.get(t, {}).get('takes_focus_at_open'), base.get(t, {}).get('traps_tab'), base.get(t, {}).get('esc_returns_to_trigger')) for t in GEN4} }")
    # 音频那 5 层：850 当初一条都没取到样，所以 850 的判据是「5 层全都留在
    # kb_not_sampled」。**851 正确地推翻了它** —— 源站能插音频节点，5 层里有
    # 2 层真取到了样。于是这条判据不能原样留着（它会在正确的改动上判红），
    # 改成持续成立的版本：**没取到样的仍在表外，取到样的已进表**。
    # （847 就干过同一件事：两条预设被推翻时，改的是判据不是产品。）
    AUD5 = ["audio-music-model-listbox", "audio-music-duration-listbox",
            "audio-voice-model-listbox", "audio-gen-mode-listbox",
            "audio-all-voices-listbox"]
    ns_layers = {n.get("layer") for n in kb_ns}
    AUD_UNSAMPLED = [t for t in AUD5 if t not in base]
    check("J.5 音频 5 层里**没取到样**的那些仍在 `kb_not_sampled`"
          "（850 断言「5 层全在」已被 851 推翻：源站能插音频节点，2 层取到了样。"
          "「同类 ≠ 同行为」只约束**没实测**的那些）",
          bool(AUD_UNSAMPLED)
          and all(t in ns_layers for t in AUD_UNSAMPLED),
          f"已进表 {[t for t in AUD5 if t in base]}；"
          f"仍在 not_sampled {AUD_UNSAMPLED}")
    # 产品侧：修法必须是**共享**的一个 hook，且四个下拉都接上了
    chrome = (ROOT / "src/components/jimeng/jimengMenuChrome.tsx")
    genp = (ROOT / "src/components/jimeng/JimengGenPanel.tsx")
    csrc = chrome.read_text(encoding="utf-8") if chrome.exists() else ""
    gsrc = genp.read_text(encoding="utf-8") if genp.exists() else ""
    check("J.6 修法收成**一个共享 hook** `useTakeFocusAtOpen`"
          "（不是四处各写一遍 —— 814 的教训就是「同一套值散在 7 个文件里」）",
          "export function useTakeFocusAtOpen" in csrc)
    check("J.7 四个下拉**都**接上了那个 hook（一个漏接就是漏一半）",
          all(f"useTakeFocusAtOpen({v}" in gsrc
              for v in ("modelBoxRef", "ratioBoxRef", "modeBoxRef", "durBoxRef")),
          f"接上 {sum(1 for v in ('modelBoxRef','ratioBoxRef','modeBoxRef','durBoxRef') if f'useTakeFocusAtOpen({v}' in gsrc)}/4")
    check("J.8 四个层都挂了对应的 ref（hook 拿不到节点就等于没接）",
          all(f"ref={{{v}}}" in gsrc
              for v in ("modelBoxRef", "ratioBoxRef", "modeBoxRef", "durBoxRef")))
    # 内联 JS 语法自检：850 里同一个错犯了三次，都是 JS 语法错当场崩
    checker = ROOT / "scripts/jimeng_probe_js_syntax_check.py"
    check("J.9 有**内联 JS 语法自检**脚本（JS 语法错 py_compile 抓不到，"
          "却会让探针当场崩、把已量好的结果一起带走）",
          checker.exists()
          and "node" in checker.read_text(encoding="utf-8"),
          f"{checker.name} 存在={checker.exists()}")
    # 护栏不能太宽：850 第一版 `startswith("生成")` 把「生成模式」也拦了。
    # ⚠️ 护栏在**探针**里（`asrc` 是审计的源码）—— 第一版查错了文件，
    #    判据自己 FAIL 了一次。查判据所在的文件之前先确认它在哪。
    probe = ROOT / "scripts/jimeng_probe850_genpanel_kb.py"
    psrc = probe.read_text(encoding="utf-8") if probe.exists() else ""
    check("J.10 付费护栏**按等值**拦，不按前缀（否则「生成模式」这种"
          "**控件描述**会被当成付费按钮，「测不到」被印成「不许测」）",
          re.search(r"BILLED_EXACT\s*=\s*\(", psrc) is not None
          and re.search(r"if t in BILLED_EXACT or base in BILLED_EXACT", psrc)
          is not None,
          f"{probe.name}: BILLED_EXACT="
          f"{'在' if 'BILLED_EXACT' in psrc else '不在'}")

    # ── K. 批 851：音频面板 —— 「没取到」的三种原因必须各归各的账 ──────
    #    850 结尾写「音频那 5 个下拉仍记 kb_not_sampled」，但**没说清为什么**。
    #    851a 侦察推翻了隐含前提：源站这一版画布**能插音频节点**，那 5 层
    #    **不是 BLOCKED_BY_FIXTURE**。851b 真去取，只取到 **2 层**。
    #    剩下 3 层的「没取到」是**三种完全不同的病**：
    #      · 前置态没成立（音乐分支切不过去）—— 下一步是 dump 选项结构
    #      · 判据量错对象（音色库认成了整页容器）—— 下一步是换认法
    #    笼统写一句「没取过样」会把它们混成一种，而下一步动作完全相反。
    print("\n— K. 音频面板：三种「没取到」各归各的账 —")
    # ⚠️⚠️ 853 之后这三条判据的前提**变了**，必须跟着改（847 定的规矩：
    #    判据被正确推翻时**改判据不改产品**）：
    #    · `audio-music-model-listbox` / `audio-all-voices-listbox` 已**取到样**
    #      ⇒ K.3/K.5/K.7 那三条「不许进基线表 / 伪像 / 不许接 hook」的前提
    #        已经不存在了，继续留着会**逼着代码回到错误的状态**。
    #    · `audio-music-duration-listbox` 仍在 not_sampled，但原因从
    #      「前置态没成立」变成「**源站没有这个入口**」—— 新的、且更硬的病。
    AUD_OK = ["audio-voice-model-listbox", "audio-gen-mode-listbox",
              "audio-music-model-listbox", "audio-all-voices-listbox"]
    AUD_MISS = ["audio-music-duration-listbox"]
    check("K.1 取到样的 4 层**在基线表里**（851b 两层 + 853b 两层）",
          all(t in base for t in AUD_OK),
          f"{[t for t in AUD_OK if t in base]}")
    # ⚠️⚠️ 这里**不能**笼统要求 4 层都是 bool：全音色层的 `arrows_move` 合法地
    #    是 `None`，而这个 `None` 的含义与「判据没测到」**不同** ——
    #    它是「**测到了「测不到」这件事本身**」：焦点自始至终没进过面板，
    #    层内压根没有起点可按。把两者混起来，下一批就会去查错的东西。
    #    所以拆成两条：另外 3 层必须是**实测过的布尔**；全音色层必须是 `None`
    #    **且**它的 `None` 带得出来源（M.8 查那个）。
    AUD_BOOL = [t for t in AUD_OK if t != "audio-all-voices-listbox"]
    check("K.2 除全音色外的 3 层方向键是**实测过的布尔**（852/853 补测；"
          "「不许偷偷填值」依然成立）",
          all(isinstance(base.get(t, {}).get("arrows_move", None), bool)
              for t in AUD_BOOL),
          f"{ {t: base.get(t, {}).get('arrows_move', 'MISSING') for t in AUD_BOOL} }")
    whys = [n.get("why", "") for n in kb_ns
            if n.get("layer") in AUD_MISS]
    check("K.3 没取到样的 1 层**仍留在** `kb_not_sampled`"
          "（实测不到 ≠ 可以按「同类层」推测）",
          all(t not in base and t in {n.get("layer") for n in kb_ns}
              for t in AUD_MISS),
          f"进了基线表的：{[t for t in AUD_MISS if t in base]}")
    whys = [n.get("why", "") for n in kb_ns
            if n.get("layer") in AUD_MISS]
    check("K.4 那一层的 why 写明是「**源站没有这个入口**」"
          "（853 实测：切到音乐分支后 `选择时长` 触发器计数 0，"
          "而同一时刻 `选择模型` 计数 1 ⇒ 源站音乐分支只有模型、没有时长）",
          len(whys) == 1 and "源站没有这个入口" in whys[0],
          f"why={whys[0][:50]!r}" if whys else "没有 why")
    # 产品侧：853b 取到样的**音乐模型**要接接管焦点（源站实测接管）；
    # **全音色**源站实测**不**接管 ⇒ 复刻也**不许**接。
    audp = ROOT / "src/components/jimeng/JimengAudioGenPanel.tsx"
    asrc2 = audp.read_text(encoding="utf-8") if audp.exists() else ""
    check("K.6 复刻接了**取到样且源站接管焦点**的 3 层"
          "（voiceBoxRef / dubBoxRef / musicBoxRef）",
          all(f"useTakeFocusAtOpen({v}" in asrc2
              for v in ("voiceBoxRef", "dubBoxRef", "musicBoxRef"))
          and all(f"ref={{{v}}}" in asrc2
                  for v in ("voiceBoxRef", "dubBoxRef", "musicBoxRef")),
          f"接上 {sum(1 for v in ('voiceBoxRef', 'dubBoxRef', 'musicBoxRef') if f'useTakeFocusAtOpen({v}' in asrc2)}/3")
    # ⚠️ 核心：源站**实测不接管焦点**的层（全音色）**不许**接 ——
    #    接了就是「源站没有的行为也实现」。音乐时长（源站无此入口）同理。
    not_connected = [v for v in ("durBoxRef", "voicesBoxRef")
                     if f"useTakeFocusAtOpen({v}" in asrc2]
    check("K.7 源站**不接管焦点**的全音色层 / 源站**无入口**的音乐时长层"
          "**不许**接那个 hook（接了就是「伪称可用」，比不做更坏）",
          not not_connected, f"误接的：{not_connected or '无'}")
    # 探针侧：重开不许靠「点两下」的状态假设
    lib = ROOT / "scripts/jimeng_kb_probe_lib.py"
    lsrc = lib.read_text(encoding="utf-8") if lib.exists() else ""
    check("K.8 有**共享取样库** `jimeng_kb_probe_lib.py`，850 与 851 共用"
          "（同一套判据必须逐字同款，否则基线表里两批没法比）",
          lib.exists() and "from jimeng_kb_probe_lib import" in
          (ROOT / "scripts/jimeng_probe850_genpanel_kb.py").read_text(encoding="utf-8")
          and "from jimeng_kb_probe_lib import" in
          (ROOT / "scripts/jimeng_probe851b_audiopanel_kb.py").read_text(encoding="utf-8"))
    check("K.9 重开层用 `ensure_open()`（**打标记当探针**），"
          "不用「点两下」的状态假设",
          "def ensure_open(" in lsrc
          and "ensure_open(page, layer" in
          (ROOT / "scripts/jimeng_probe850_genpanel_kb.py").read_text(encoding="utf-8")
          and "ensure_open(page, layer" in
          (ROOT / "scripts/jimeng_probe851b_audiopanel_kb.py").read_text(encoding="utf-8"),
          f"lib 里 ensure_open={'def ensure_open(' in lsrc}")
    check("K.10 `mark_layer` 每次都**先清旧标记**"
          "（源站这些下拉点触发器关不掉，旧标记会让新层被判成「层不见了」）",
          "removeAttribute('data-probe850')" in lsrc)
    check("K.11 认层有**两条路**（role=listbox/dialog + class 特征）——"
          "「音色库」既不是 listbox 也不是 dialog，只走 role 会认不出",
          "[class*=" in lsrc.replace("'", '"') or 'class*=' in lsrc)

    # ── L. 批 852：方向键从「没测到」变成「测到了」──────────────────────
    #    850/851 记的 `arrows_move: None` 是**判据缺陷**，不是产品缺��� ——
    #    两个判据把它盖住了，而两个都是同一类病：**布尔判据不配轨迹**。
    #      ① `moved` 只对「按完之后」的 4 个点去重，**漏掉了按之前的起点**。
    #         源站这六层都是「起点 ≠ 第 1 次之后」：`16:9` → `1` → `1` → `1`
    #         去重后 1 个 ⇒ moved=False，而**第一次移动恰恰在起点→第一次之间**。
    #         §64 记的是「moved=True 会掩盖跳格」；这里是**反向**的同一个病。
    #      ② 判断「层里哪些可聚焦」时**真的调了 `focus()`**，把起点推到了最后
    #         一个能聚焦的项上（音频·音色模型只有 2 项 ⇒ 起点被推到第 2 项
    #         ⇒ 再按无处可去 ⇒ 假阴）。846 早写过：判断可聚焦性不能真的去 focus。
    #    修完的实测：模型 9 项 True / 尺寸 14 项 True / 模式 2 项 True /
    #    音色模型 2 项 True / 时长（slider 吃方向键）False / 生成模式（只 1 项）False。
    print("\n— L. 方向键：`moved` 漏起点，诊断毁起点 —")
    ARROW6 = {"gen-model-listbox": True, "gen-video-size-listbox": True,
              "gen-mode-listbox": True, "gen-duration-listbox": False,
              "audio-voice-model-listbox": True, "audio-gen-mode-listbox": False}
    check("L.1 六层的 `arrows_move` 与 852 实测**逐项相符**"
          "（两个 False 含义不同：时长层是 slider 吃方向键、生成模式只有 1 项）",
          all(base.get(t, {}).get("arrows_move", "MISSING") == v
              for t, v in ARROW6.items()),
          f"{ {t: base.get(t, {}).get('arrows_move', 'MISSING') for t in ARROW6} }")
    p852 = ROOT / "scripts/jimeng_probe852_arrowdiag.py"
    q852 = p852.read_text(encoding="utf-8") if p852.exists() else ""
    check("L.2 探针里 `moved` **把起点算进去**"
          "（`…seq… | {start}`）—— 漏掉它就把「走一步」判成「不动」",
          "| {start}) > 1" in q852 or "| {start})" in q852,
          f"{p852.name} 含起点合并="
          f"{'| {start})' in q852}")
    check("L.3 探针**不许**用 `focus()` 试探可聚焦性"
          "（那会把起点推到最后一个能聚焦的项上；846 早写过同一条）",
          "e.focus();\n          return document.activeElement === e" not in q852
          and "不许真的 focus 来试探" in q852)
    check("L.4 起点在**诊断之前**单独读一次"
          "（诊断会遍历层内所有候选项，起点必须钉在它碰不到的地方）",
          "诊断前起点" in q852 and q852.index("诊断前起点")
          < q852.index("diag = page.evaluate(DIAG_JS, lay)"))
    csrc2 = (ROOT / "src/components/jimeng/jimengMenuChrome.tsx").read_text(
        encoding="utf-8")
    check("L.5 修法是**一个只做方向键**的小 hook `useArrowKeys`"
          "（源站这六层实测 `traps_tab: false`，接整只 `useMenuKeyboard` "
          "会引入一堆没有源站依据的行为）",
          "export function useArrowKeys" in csrc2)
    g2 = (ROOT / "src/components/jimeng/JimengGenPanel.tsx").read_text(
        encoding="utf-8")
    a2 = (ROOT / "src/components/jimeng/JimengAudioGenPanel.tsx").read_text(
        encoding="utf-8")
    check("L.6 视频 3 层 + 音频 2 层接了 `useArrowKeys`",
          sum(f"useArrowKeys({v}" in g2 + a2
              for v in ("modelBoxRef", "ratioBoxRef", "modeBoxRef",
                        "voiceBoxRef", "dubBoxRef")) == 5)
    check("L.7 **时长层刻意没接** `useArrowKeys`"
          "（源站那一层焦点在 `SPAN/slider` 上，方向键被 slider 自己吃掉，"
          "焦点不动；接了就是照抄一个源站没有的行为）",
          "useArrowKeys(durBoxRef" not in g2)
    # 音色模型：症状在键盘、根因是内容缺项
    n_opt = a2.count('aria-label="Seed TTS, 上百个预设音色')
    check("L.8 音色模型层补上了源站那**第 2 项** `Seed TTS`"
          "（症状是「方向键不动」，根因是**内容只有 1 项**——1 项时无处可去；"
          "源站实测 2 项，且方向键在两项间来回）",
          n_opt == 1 and "上百个预设音色，让你玩转人声配音" in a2,
          f"Seed TTS 项 {n_opt} 个")

    # ── M. 批 853：两种「测不到」拆开 + 两条方法论 ─────────────────────────
    #    §70 结尾那 3 层，拆完之后是**三层三种命运**：2 层取到样、1 层是源站事实。
    #    而 853b 中途栽了三次，每一次的教训都比结论更值钱：
    print("\n— M. 853：换判据不解决判据量错对象；③ 必须排在 ② 之前 —")
    p853b = ROOT / "scripts/jimeng_probe853b_audiostruct_kb.py"
    q853b = p853b.read_text(encoding="utf-8") if p853b.exists() else ""
    check("M.1 源站探针**自己 goto 画布 URL**"
          "（853 第一版漏了这行 ⇒ 页面停在 runner 默认的首页/推广浮层，"
          "左栏全是「打开画布/新建画布」，还误判成「夹具不具备」）",
          "page.goto(" in q853b and "64b58cd5-7b04-4312-890a-09f2d1d3399f" in q853b)
    # ⚠️ 判据本身也栽过一次：第一版写 `"text-is" not in q853b` 当条件，
    #    结果**探针注释里引了 851 的 `text-is(` 当反面教材**就把它判红了。
    #    —— **判据自己也可能量错对象**。改成查「有没有把 text-is 用作
    #    **选择器**」（形如 `text-is(` 且前面带 `locator(`/`:`），
    #    而不是查这个字符串在文件里出不出现。
    # ⚠️⚠️ 这条判据自己返工了**三次**：先查「文件里没有 text-is」，
    #    被探针 docstring 里引的 851 反面教材判红；改成「只看 # 注释行」，
    #    又被 docstring（三引号字符串，不是 # 注释）判红。
    #    ⇒ 两次都是**同一个病**：拿「某个字符串在不在」当判据。
    #    按 852 的教训（**判据要可证伪、要量真正要量的东西**），这里只查
    #    **正向证据**：探针是**按 innerText 文本相等**找那个 SPAN 的，
    #    并**沿祖先链找 cursor:pointer** 去点 —— 这两条就是修法的全部内容。
    #    「没有用 text-is」是它的推论，不需要（也不该）单独断言。
    m2_text_find = "innerText||'').trim() === '音乐生成'" in q853b
    m2_pointer = "cursor === 'pointer'" in q853b
    check("M.2 切分支按**innerText 文本相等**找那个 `SPAN`"
          "（851 按 `[role=option]:text-is(…)` 永远数不到它，"
          "因为它**根本不是 role=option**），再沿祖先链找**可点的祖先**"
          "（cursor:pointer）去点",
          m2_text_find and m2_pointer,
          f"按 innerText 文本找={m2_text_find} 找 cursor:pointer 祖先={m2_pointer}")
    check("M.3 音色库层用**专用认法**：标题「全音色」+ ≥8 可见 chip + "
          "面积<半视口的最小祖先（853b 用「最近公共祖先」**又**量到整页："
          "该 class 实测 63 个 chip 散布整个画布节点区 —— **换判据不解决"
          "判据量错对象**）",
          "def mark_voice_panel(" in lsrc
          and "全音色" in lsrc and "min-w-canvas-audio-voice-shrinkable" in lsrc
          and "max_frac" in lsrc)
    # ★ 853c 的方法论：③ 方向键必须排在 ② Tab **之前**
    i3 = lsrc.index('rec["arrow_down"] = {"measured": True, "moved": uniq > 1,')
    i3b = lsrc.index("③ 方向键**先于**② 测") if "③ 方向键**先于**② 测" in lsrc \
        else lsrc.index("③ 方向键**先于**")
    i2 = lsrc.index("# ② Tab 逃出（层还在才谈得上")
    check("M.4 共享库里 **③ 方向键排在 ② Tab 之前**"
          "（① 已经把「焦点自然落在层内」这个最好的起点建好了；"
          "② 那串 Tab 是**破坏性**的，源站这几层第 1 次就逃出。853b 把 ③ 排在"
          "② 之后就得 `focus()` 重建起点，而源站对 `focus()` 反应不稳 —— "
          "音乐模型层、音色库层连着两次白交「没测到」）",
          i3b < i2 < i3 or i3b < i2,
          f"③段 @{i3b} < ②段 @{i2} < moved 赋值 @{i3}")
    check("M.5 `moved` **仍把起点算进去**（852 修正没被 853 改回去）",
          "set(seq) | {start_who}" in lsrc)
    check("M.6 基线表里**音乐模型**方向键 False 的理由写明是"
          "「**内容只有 1 项**」而不是「源站方向键坏了」",
          "只有 1 项" in lsrc or "只有 1 项" in (
              ROOT / "scripts/jimeng_unclickable_audit.py").read_text(encoding="utf-8"))
    check("M.7 基线表里**全音色**记 `takes_focus_at_open: False` 且 why 写明"
          "「焦点自始至终停在触发器上」"
          "（853c：伪像与真结论**碰巧同形** —— 重新认层后才知道这次是真的）",
          base.get("audio-all-voices-listbox", {}).get("takes_focus_at_open")
          is False)
    av2 = base.get("audio-all-voices-listbox", {})
    # ⚠️ 这个 `None` 必须**自带理由**且理由可机读 —— 只写在源码注释里的话，
    #    判据查不到，半年后没人知道它是「测到了测不到」还是「忘了测」。
    awhy = str(av2.get("arrows_move_why", ""))
    check("M.8 全音色层的 `arrows_move` 留 `None`，**且**有可机读的 "
          "`arrows_move_why` 说清是「焦点不在层内 ⇒ 没有层内起点」"
          "—— 这跟「判据没测到」要分清",
          av2.get("arrows_move", "MISSING") is None
          and "焦点" in awhy and "层内" in awhy,
          f"arrows_move={av2.get('arrows_move', 'MISSING')!r} why={awhy[:40]!r}")

    # ── N. 批 855：**按名字**找，不按位置猜 ───────────────────────────────
    #    847c/847d 记的「生成历史层前置态没成立」里，藏着一个从没验证过的前提：
    #    *「生成历史」是顶栏**第 2 个** launcher*。855a 把顶栏 9 个按钮逐个点
    #    了一遍 —— **位置和功能没有对应关系**，第 2 个其实是「Credits」。
    print("\n— N. 855：按名字找，不按位置猜 —")
    p855a = ROOT / "scripts/jimeng_probe855_topbar_recon.py"
    q855a = p855a.read_text(encoding="utf-8") if p855a.exists() else ""
    check("N.1 侦察探针**把顶栏每个按钮都点一遍**并逐个记下开出什么"
          "（按位置猜名字是不可靠的指针：855a 实测第 2 个是「Credits」"
          "而不是「生成历史」）",
          p855a.exists() and "逐个点开" in q855a
          and "for i, b in enumerate(bars)" in q855a)
    check("N.2 探针点坐标**之前先 `elementFromPoint` 验落点**"
          "（843 同病：点坐标前必须验落点，否则点到的不是你想点的那个）",
          "elementFromPoint" in q855a and "hit" in q855a)
    check("N.3 「里面写着」**限定在层内**读，不是从整页抓"
          "（第一版的选择器从 `document` 开始，抓回来的是全页文本 —— "
          "判据量错对象的老毛病，这次量错的是「读的文本」而不是「认的层」）",
          "const root = best || document.body" in q855a
          and "r.x < x - 4 || r.y < y - 4" in q855a)
    hb = base.get("topbar-history-menu", {})
    check("N.4 生成历史层**已进基线表**（855b 实测 320×211 dialog："
          "接管焦点 / 不困 Tab@2 / 方向键不动 / Esc 归位）",
          hb.get("takes_focus_at_open") is True
          and hb.get("traps_tab") is False
          and hb.get("esc_returns_to_trigger") is True
          and hb.get("arrows_move") is False,
          f"{ {k: hb.get(k, 'MISSING') for k in ('takes_focus_at_open', 'traps_tab', 'arrows_move', 'esc_returns_to_trigger')} }")
    check("N.5 它**不在** `kb_not_sampled` 里了"
          "（循环先查 NOT_SAMPLED 再查基线表 —— 留着就会被永远打回去，"
          "而旧文案「前置态没成立」是**假病历**）",
          "topbar-history-menu" not in {n.get("layer") for n in kb_ns},
          f"仍在 not_sampled: "
          f"{'topbar-history-menu' in {n.get('layer') for n in kb_ns}}")
    check("N.6 基线表里写明层是**按 aria-label 找**的、不是按位置"
          "（`按 aria-label=... 找`）",
          "aria-label" in hb.get("src_identified_by", ""))
    check("N.7 方向键 False 的理由写明是「**源站没接方向键漫游**」"
          "（实测 4 次 ArrowDown 全停在同一个 tab 按钮），"
          "**不是**「内容只有 1 项」—— 两者不能混",
          "没接" in (ROOT / "scripts/jimeng_unclickable_audit.py").read_text(
              encoding="utf-8"))
    hm = ROOT / "src/components/jimeng/JimengHistoryMenu.tsx"
    hsrc = hm.read_text(encoding="utf-8") if hm.exists() else ""
    # ⚠️ 又一次「拿字符串在不在当判据」：源文件注释里就写着「刻意不接
    #    `useArrowKeys`」，于是 `"useArrowKeys" not in hsrc` 永远为假。
    #    判「**有没有真的调用**」要查调用形态 `useArrowKeys(`，
    #    而且**必须排除注释行** —— 注释里提到它是**应该的**（写明取舍）。
    hsrc_code = strip_comments(hsrc)
    check("N.8 复刻接了 `useTakeFocusAtOpen`（源站开层即接管焦点）"
          "**且代码里没有** `useArrowKeys(` 调用（源站方向键不动）"
          "—— 注释里**可以**写明「刻意不接」，那是要记录的取舍",
          "useTakeFocusAtOpen(" in hsrc_code
          and "useArrowKeys(" not in hsrc_code,
          f"接了 useTakeFocusAtOpen="
          f"{'useTakeFocusAtOpen(' in hsrc_code} "
          f"误接 useArrowKeys={'useArrowKeys(' in hsrc_code}")

    # ── P. 批 863：判据补齐「层内」那半 + 全屏模态焦点陷阱 ──────────
    # 862 栽在**只盯 `skin_top_n`** 上：把采样早退拆掉、只验了 skin 那一条，
    # 改动就上了桌。863 把剩下三条**逐个**验过才敢留在代码里。P 组把它们
    # 钉死 —— 以后谁再动这四处，会在这里被挡住。
    print("— P. 批 863 判据四改 + 全屏层焦点陷阱 —")
    asrc = AUDIT.read_text(encoding="utf-8")
    # ⚠️ 又一次「拿字符串在不在当判据」：这几处的**注释里就原样写着被删掉的
    #    旧代码**（`原来 \`if (inside) return\``）。判「代码还在不在」必须
    #    **先剥注释行**，否则断言恒为假、看着像回归其实是自己写的注释。
    acode = strip_comments(asrc)
    # ⚠️⚠️ 断言必须打**代码形态**，不能打裸 token。
    # 被检查的审计把内联 JS 装在 Python 三引号字符串里，JS 自己的 `//`
    # 注释因此对 Python 层的剥注释器**不可见** —— 而 863 为了讲清取舍，
    # 正好在注释里写了「原来 `if (inside) return`」这句话。
    # 裸 token 断言会把**自己写的说明**当成**代码还在**。
    # 办法是打一个注释不会写的形态（带 `{` 的完整返回语句）。
    check("P.1 采样 JS 里 `if (inside) return {` 早退**已删**"
          "（焦点一进层就返回 ⇒ 后面全不采样 ⇒ 层内一步都不统计）"
          "—— 打的是**带 `{` 的代码形态**：说明性注释里写着裸 token，"
          "裸 token 断言会把自己写的说明当成代码",
          "if (inside) return {" not in acode,
          f"仍存在={'if (inside) return {' in acode}")
    check("P.2 层内分支用 `edges_covered == edges_total` 计入 `covered_n`"
          "（**不能**只判 `state == 'covered'` —— JS 已把层内标成 `inside`，"
          "那条分支在层内永远进不来，正是 862 卡住的原因）",
          'if (step.get("edges_covered") == step.get("edges_total")' in acode)
    # skin_top 的累加现在有**两处**（层内分支 + 层外分支）。早退拆掉之后
    # 层内那步的皮「采到了却被丢掉」，只留一处会少算。
    check("P.3 `skin_top_n += 1` 有**两处**（层内 + 层外各一）"
          "—— 少一处就等于把进层那一步的皮扔了（§62 版旧版因此少 1 次）",
          acode.count("skin_top_n += 1") == 2,
          f"实测 {acode.count('skin_top_n += 1')} 处")
    # A.0 已经隐含断言了自检，但它是**间接**的（混在退出码公式里）。
    # 863 的教训是「只验自己关心的那一条等于没验」，所以这里把四个条件
    # **摊开逐条**再钉一遍，且**必须双向**：只活正向 = 判据只会报，
    # 只会报不活反向的判据 = 「盖了自己的皮也多报」的坑没人守。
    _shut = kbst.get("covered_n_when_shut")
    _clear = kbst.get("covered_n_when_clear")
    _skin = kbst.get("covered_n_when_skin")
    _skin_top = kbst.get("skin_top_n")
    check("P.4 正向自检活：盖上遮挡物后 `covered_n` 必须涨"
          "（`when_shut > when_clear`）—— 这是 862 塌掉的那一半",
          (_shut or 0) > (_clear or 0), f"shut={_shut} clear={_clear}")
    check("P.5 反向自检活：给每个控件各盖一层「**自己的皮**」后 `covered_n` "
          "必须**回到 clear 的水平**（不多报）",
          _skin is not None and _clear is not None and _skin == _clear,
          f"skin={_skin} clear={_clear}")
    check("P.6 皮必须**真当过栈顶**（`skin_top_n > 0`）"
          "—— 否则「盖了自己的皮也不多报」是恒真的空话",
          (_skin_top or 0) > 0, f"skin_top_n={_skin_top}")
    check("P.7 夹具成色记在案（`skin_n` 真的盖了足够多的控件，不是 1 个）",
          (kbst.get("skin_n") or 0) >= 10, f"skin_n={kbst.get('skin_n')}")
    # 863 把新面板换成第一次 Tab 就在层内（§79 定论），阳性夹具因此从
    # 「39 步里 32 个被遮」缩到「1 步里 1 个被遮」。判据**仍然能失败**
    # （P.4 绿），但覆盖面确实小了 —— 这是缩小，不是缺陷。把它记在结果里，
    # 是为了让下一个人不必重新发现它。
    check("P.7b 自检**灵敏度**记在案（`walked_when_shut` / `walked_when_clear`）"
          "—— 判据覆盖面缩小是事实，不许只写在散文里",
          kbst.get("walked_when_shut") is not None
          and kbst.get("walked_when_clear") is not None
          and (kbst.get("walked_when_shut") or 0) >= 1,
          f"shut={kbst.get('walked_when_shut')!r} "
          f"clear={kbst.get('walked_when_clear')!r}")
    check("P.7c 阳性夹具那条 finding **记下来了**（`shut_covered`）"
          "—— 没有它，「finding 指名被谁盖住」这条契约就只能绑在产品当下"
          "有没有缺陷上，缺陷一修好契约自己就红（863 亲身踩过）",
          bool((kbst.get("shut_covered") or {}).get("top")),
          f"shut_covered="
          f"{json.dumps(kbst.get('shut_covered'), ensure_ascii=False)[:120]}")

    krows = {r.get("layer"): r for r in data.get("keyboard", [])}
    fsr = krows.get("video-fullscreen-preview", {})
    check("P.8 复刻全屏预览层**开层即接管焦点**"
          "（修之前 `focus_at_open.state='other'`，焦点还留在触发器上）",
          (fsr.get("focus_at_open") or {}).get("inside") is True,
          f"focus_at_open="
          f"{json.dumps(fsr.get('focus_at_open'), ensure_ascii=False)[:90]}")
    check("P.9 它**不再**有焦点被自己盖住的控件（实测 22 → 0）"
          "—— ⚠️ 不能写 `covered_n or 0 == 0`：审计没跑出数据时 `None` 会被"
          "当成 0 **假通过**，那正是「没测到写成没发生」",
          bool(fsr) and fsr.get("covered_n") == 0,
          f"covered_n={fsr.get('covered_n')!r} 行存在={bool(fsr)}")
    check("P.10 全屏层按 Tab **进得去**且 `covered` 为空",
          (fsr.get("tabs") or 0) == 1 and fsr.get("covered") is None,
          f"tabs={fsr.get('tabs')} covered={fsr.get('covered')}")

    chrome = ROOT / "src/components/jimeng/jimengMenuChrome.tsx"
    csrc = chrome.read_text(encoding="utf-8") if chrome.exists() else ""
    ccode = strip_comments(csrc)
    vpsrc = (ROOT / "src/components/jimeng/JimengVideoPreview.tsx")
    vcode = (strip_comments(vpsrc.read_text(encoding="utf-8"))
             if vpsrc.exists() else "")
    check("P.11 复刻全屏层**真的调用**了 `useModalFocusTrap(`"
          "（判「有没有接」查调用形态，不查裸名字 —— 注释里提到它是应该的）"
          "；定义侧匹配 `useModalFocusTrap<...>(` 的泛型形态，"
          "直接找 `useModalFocusTrap(` 会**永远匹配不上**",
          "useModalFocusTrap(" in vcode
          and "export function useModalFocusTrap" in ccode,
          f"调用={'useModalFocusTrap(' in vcode} "
          f"定义={'export function useModalFocusTrap' in ccode}")
    # 截出 hook 自己的函数体：只查它接了什么，别把整个文件算进来
    _h = re.search(r"export function useModalFocusTrap.*?\n}\n",
                   csrc, re.S)
    hbody = _h.group(0) if _h else ""
    check("P.12 `useModalFocusTrap` **不接 Esc**"
          "（全屏播放器自己已有一个捕获阶段的 Esc 监听 —— 再接一个只会"
          "双触发 `onClose`）。⚠️ 顺带钉住「函数体**切到了**」："
          "空串里当然没有 `Escape`，切空了就变成假通过",
          bool(hbody.strip()) and "Escape" not in hbody,
          f"函数体 {len(hbody)} 字符，出现 Escape={'Escape' in hbody}")
    check("P.13 它接了 **Tab 陷阱**（`preventDefault` + 认 `shiftKey` 做反向环绕）"
          "—— 只接管焦点不困 Tab 的话，焦点仍会从最后一个按钮漏回页面",
          bool(hbody.strip()) and "preventDefault" in hbody
          and "shiftKey" in hbody)
    # 搜索面板：863 顺手修的高度溢出（硬编码 1084px 会盖住顶栏其余层）
    so = ROOT / "src/components/jimeng/JimengSearchOverlay.tsx"
    ssrc = so.read_text(encoding="utf-8") if so.exists() else ""
    check("P.14 搜索面板高度**不是**硬编码 `1084px`"
          "（源站那个值是「20 个节点撑出来的实测值」，不是布局常量；"
          "照抄会溢出视口、盖掉顶栏其余浮层 —— 实测可开层 13 → 16）",
          "maxHeight: '1084px'" not in ssrc
          and "100vh - 72px" in ssrc)
    check("P.15 分类 tab 有**右翻按钮**且 tablist 右侧留了位"
          "（9 个 tab 在 320px 里放不下，源站靠「Next search categories」；"
          "不留 paddingRight 的话最后一个 tab 被按钮压住）",
          "paddingRight" in ssrc and "分类" in ssrc)

    # ── Q. 批 864：4 个视口级模态「先探再判」+ 两处**修法不同** ────────
    # §81 抓到了全屏预览不困焦点的真缺陷，同批在范围限制里记了 4 个
    # **没探过**的视口级模态，并写下「未测 ≠ 没缺陷」。864 去探了，探完发现
    # **两类问题**、**两种修法** —— Q 组钉的就是这个分岔不许被抹平。
    print("— Q. 批 864 模态焦点：先探再判，两类问题两种修法 —")
    q = ROOT / "scripts/jimeng_probe864_modaltrap.py"
    qsrc = q.read_text(encoding="utf-8") if q.exists() else ""
    qcode = strip_comments(qsrc)
    check("Q.1 探针 864 在库里（§81 记的 4 个模态要有可复跑的取证入口）",
          bool(qsrc) and q.exists(),
          f"{q.relative_to(ROOT) if q.exists() else '缺失'}")
    # 判据**不许**自己另写一份：前三代都是因为各写各的才被证伪三次
    # ⚠️ 断言的是**机制本身**（`paintsOver` 里「走到焦点自己的祖先就停」
    #    那条 `return false`），不是某句注释 —— 第一版这里断言的是一句注释
    #    文本，注释被我自己删掉后断言就红了：把「说明还在不在」当
    #    「行为还在不在」。括号数也按源码逐字抄（三个 `)`：一个闭
    #    `n.contains(a)`、一个闭 `(n.contains && …)`、一个闭 `if (`）。
    _anc = "n.contains(a))) return false"
    check("Q.2 探针的判据与审计**同款**（`paintsOver` + `EDGE` 边框采样 + "
          "「走到焦点自己的祖先就停」豁免 + 4 边全被不透明外人盖住才算 covered）"
          "—— §841 记着这判据被证伪过三次，各写各的等于第四次犯同样的错",
          "paintsOver" in qsrc and "EDGE" in qsrc
          and "elementsFromPoint" in qsrc and _anc in strip_comments(qsrc),
          f"祖先豁免={_anc in strip_comments(qsrc)}")
    check("Q.3 点之前**先验落点**（843 同病：不验落点，点到的不是你想点的）",
          "elementFromPoint" in qcode and "落点已验" in qcode)
    # 「用户点得到吗」不能拿**文本形状**回答。探针前两版都栽在这上面：
    # 第 1 版假阳性（把 prop 传递当入口）、第 2 版假阴性（把 prop 传递
    # 一律当不可达）。所以静态分析只准出**提示**，判定权在浏览器。
    check("Q.4 **浏览器实测才是判定**，静态分析只准当提示"
          "（前两版分别假阳性、假阴性各一次）",
          "static_hints" in qcode and "不是判定" in qsrc
          and "no_ui_path" in qcode and "path_failed" in qcode)
    check("Q.5 三种「没结果」分开记账：`probed` / `no_ui_path` / `path_failed`"
          "—— 把三者揉成一栏，就是「没测到」被写成「没发生」的老路",
          all(k in qcode for k in ("probed", "no_ui_path", "path_failed"))
          and "前置态没成立" in qsrc)
    # ⚠️ 这一条是探针自己的教训：`walk()` 一进层就 break，只回答「几步
    #    进得去」。拿它当「进去之后出不来的」证据 = 用 A 的测量证明 B。
    check("Q.6 `walk`（几步进得去）与 `traps`（进去之后会不会跑出去）"
          "是**两个独立测量**"
          "—— 861 刚被「用 fill() 的实验当焦点证据」坑过，同一类错误不许重犯",
          "def walk(" in qcode and "def traps(" in qcode
          and "traps_tab" in qcode and "跑出去" in qsrc)
    # 两处修法**不同**，而且理由是**测出来的**不是想出来的
    # ⚠️ 变量名**不许**跟 P 组撞：P 组已经用 `asrc`/`acode` 指**审计脚本**
    #    的源码，Q 组再拿来指资产库组件 = 悄悄把 P 组的输入换掉。P 组排在
    #    前面所以这次没出事，可这种复用迟早在某次调换顺序时静默出错 ——
    #    而静默出错的断言比没有断言更坏。
    am = ROOT / "src/components/jimeng/JimengAssetsModal.tsx"
    pi = ROOT / "src/components/jimeng/JimengProjectInfoModal.tsx"
    amsrc = am.read_text(encoding="utf-8") if am.exists() else ""
    amcode = strip_comments(amsrc)
    pisrc = pi.read_text(encoding="utf-8") if pi.exists() else ""
    picode = strip_comments(pisrc)
    check("Q.7 资产库接了 `useModalFocusTrap(`（**有**全屏不透明遮罩 ⇒ 该困）",
          "useModalFocusTrap(" in amcode,
          f"接了={'useModalFocusTrap(' in amcode}")
    check("Q.8 资产库**确有**全屏不透明遮罩（`inset-0` + `bg-black/`）"
          "—— 「该困」的依据要能从代码里核，不能只写在注释里",
          "absolute inset-0 bg-black/" in amsrc.replace("\n", " ")
          or ("inset-0" in amsrc and "bg-black/" in amsrc))
    check("Q.9 项目信息接了 `useTakeFocusAtOpen(`（**开层即接管焦点**）"
          "但**刻意不接** `useModalFocusTrap(`",
          "useTakeFocusAtOpen(" in picode
          and "useModalFocusTrap(" not in picode,
          f"接管={'useTakeFocusAtOpen(' in picode} "
          f"误困={'useModalFocusTrap(' in picode}")
    check("Q.10 项目信息**没有**全屏遮罩（探针实测 `covered_n=0`）"
          "—— 「不该困」的依据同样要能核。两边依据都在，才能说明这**不是**"
          "「一处修了一处忘了」",
          "inset-0" not in picode and "bg-black/" not in picode)

    # ── strip_comments 给**自己**加自检 ────────────────────────────────
    # 它这一批已经坑了我两次：① 按行首过滤漏掉块注释续行（把注释里那句
    # `bg-black/55` 当成代码，Q.10 假红）② 第一版状态机漏了三引号（把
    # 嵌在 Python 字符串里的 JS 搅乱，6 条断言一起红）。一个会把输入搅坏的
    # 工具，**自己**得先证明它没搅坏 —— 拿合成输入验，不拿真实文件验。
    _sc_src = (
        'a = 1  // 行注释里的 SECRET1\n'
        '/* 块注释第一行\n'
        '   续行 SECRET2 不以 * 开头 */\n'
        'b = "字符串里的 // 不是注释 SECRET3"\n'
        'JS = """\n'
        '  const x = 1;  // 这里是 JS 注释 SECRET4，但对 Python 是字面量\n'
        '  SECRET5 = true;\n'
        '"""\n'
    )
    _sc_out = strip_comments(_sc_src)
    check("Q.11 剥注释器**剥得掉**行注释 / 块注释（含不以 `*` 开头的续行）",
          all(t not in _sc_out for t in ("SECRET1", "SECRET2")),
          f"残留={[t for t in ('SECRET1', 'SECRET2') if t in _sc_out]}")
    # ⚠️ 第一版把 SECRET3 也列进「该剥掉」那一栏，红了。查下来是**断言写反**：
    #    SECRET3 在**字符串字面量**里，剥注释器本就不该删字符串内容 ——
    #    删了才是把代码搅坏。它该**在**，而且它的存在恰好证明了
    #    「字符串里的 `//` 没有触发注释模式、没把后面整行吃掉」。
    check("Q.11b 字符串字面量里的 `//` **不触发**注释模式"
          "（SECRET3 必须**在**：它证明整行没被 `//` 之后的内容吃掉；"
          "剥注释器删字符串内容才是把代码搅坏）",
          "SECRET3" in _sc_out
          and "不是注释 SECRET3" in _sc_out,
          f"SECRET3 在={'SECRET3' in _sc_out}")
    check("Q.12 剥注释器**保留**三引号里的内容（被检查的审计/探针正是把内联"
          "JS 装在那儿；连同 JS 自己的 `//` 注释一起保留，因为对 Python 而言"
          "那是字面量）—— 判据 token 就住在里面，搅坏了就是 6 条断言一起红",
          "SECRET4" in _sc_out and "SECRET5" in _sc_out,
          f"SECRET4={'SECRET4' in _sc_out} "
          f"SECRET5={'SECRET5' in _sc_out}")

    # ── R. 批 865：两个模态进**常驻状态** + 源站无关的模态语义判据 ────
    # §82 修好的两处，证据只在探针 864 的输出里 —— 那是一次性测量。
    # 865 做了两件事把它们变成契约：① 加进审计的状态表，从此每次都量；
    # ② 加一条**不依赖源站**的判据，因为「开层没接管焦点 / 不困 Tab」
    # 这两个桶是**基线门控**的，而这两个模态正好在基线表外。
    print("— R. 批 865 常驻模态状态 + 源站无关模态语义判据 —")
    check("R.1 两个模态进了**常驻状态表**"
          "（不进表就只是一次性测量，坏了没人知道）",
          "资产库模态" in EXPECTED_STATES
          and "项目信息模态" in EXPECTED_STATES,
          f"状态表里有没有={('资产库模态' in EXPECTED_STATES, '项目信息模态' in EXPECTED_STATES)}")
    _kbm = {r.get("state"): r for r in data.get("keyboard", [])}
    _am = _kbm.get("资产库模态", {})
    _pi = _kbm.get("项目信息模态", {})
    check("R.2 两个模态**真的量到了**（不是 skipped、也不是键盘栏空白）",
          bool(_am) and bool(_pi) and _am.get("ok") is True
          and _pi.get("ok") is True,
          f"资产库 ok={_am.get('ok')!r} 项目信息 ok={_pi.get('ok')!r}")
    # ⚠️ 这是 865 最要紧的一条：第一版把 `modal_self_test` 直接写进结果
    #    字典的**字面量**里，跑出来是 **null** —— 字面量在**建的时候**
    #    就把当时的 None 拷进去了，而自检在那**之后**才跑。判据看着
    #    接上了、值是空的。钉住「四项输入同时成立」，null 过不了。
    _ms = kbst.get("modal_self_test") or {}
    check("R.3 模态语义判据的**自检能红**（合成阳性夹具的四个条件同时成立："
          "是模态 + 铺满 + 不透明 + **焦点确实不在层内**）",
          _ms.get("ok") is True and _ms.get("is_modal") is True
          and _ms.get("covers") is True and _ms.get("opaque") is True
          and _ms.get("focus_inside") is False,
          f"modal_self_test="
          f"{json.dumps(kbst.get('modal_self_test'), ensure_ascii=False)[:150]}")
    check("R.4 `modal_self_test` **不是 null**"
          "（第一版把它写进字典字面量、自检在其后跑，值恒为 null ——"
          "「看着接上了」不等于「接上了」）",
          kbst.get("modal_self_test") is not None)
    check("R.5 结果里**回填**而不是字面量（源码里是 "
          "`kb_self[\"modal_self_test\"] =`）",
          'kb_self["modal_self_test"]' in asrc)
    check("R.6 两个源站无关的桶**接进了退出码**"
          "（审计那行 `return 1 if (...)` 里真的有它们）"
          "—— 定义了不进退出码 = 「写了但没人看」，下一批就会当死代码删",
          "or kb_modal_no_focus or kb_modal_no_trap" in asrc)
    check("R.7 两个桶在结果里**存在**（不是缺键当成 0）",
          "keyboard_modal_no_focus" in data
          and "keyboard_modal_no_trap" in data,
          f"缺键={[k for k in ('keyboard_modal_no_focus', 'keyboard_modal_no_trap') if k not in data]}")
    # 谓词的两个分支**各有样本守着**，少一条判据就恒真
    check("R.8 谓词要求 `position: fixed|absolute`"
          "（实测：项目信息的祖先里有个 `pos=static 1680×1050 自身不透明`"
          "的页面根；少了这条约束，**每个**层都会被算成模态、判据恒真）",
          "positioned" in asrc and "'fixed' ||" in asrc
          and "p === 'fixed' || p === 'absolute'" in asrc)
    check("R.9 谓词有「**不透明的铺满孩子**」分支"
          "（资产库是 wrapper 无底 + 内含 `bg-black/55` 遮罩，"
          "只看祖先自身不透明会认不出来）",
          "不透明孩子" in asrc and "n.children" in asrc)
    # 产品侧：三个层被判成三种不同的结论，且都不是「全判成模态」
    _mod = sorted({r.get("layer") for r in data.get("keyboard", [])
                   if (r.get("modalish") or {}).get("modalish") is True})
    check("R.10 复刻侧认出的真模态里**包含**全屏预览与资产库"
          "（这两个实测确实有全屏不透明遮罩）",
          "video-fullscreen-preview" in _mod
          and "jimeng-assets-modal" in _mod,
          f"真模态={_mod}")
    check("R.11 项目信息**没有被**算成模态"
          "（它没有全屏遮罩、实测 `covered_n=0`；把它算成模态就会逼出一个"
          "「它该困 Tab」的过度结论）",
          "project-info-modal" not in _mod,
          f"真模态里有没有它={'project-info-modal' in _mod}")
    check("R.12 判据没把**所有**层都算成模态（恒真检查：认出的真模态数"
          f"必须**少于**被量的层数，实测 {len(_mod)} vs "
          f"{len(data.get('keyboard', []))}）",
          0 < len(_mod) < len(data.get("keyboard", [])),
          f"真模态 {len(_mod)} / 被量 {len(data.get('keyboard', []))}")

    # ── S. 批 866：「非全屏浮层盖住画布控件」分档 + 分桶**互斥** ────────
    # §83 记下 4 条「未确认」说「按 §77 没查清就没动判据」。本批查清了：
    # 根因是遮挡物是浮层内部的文本 span / 内容区（**自己没背景**，底色来自
    # 浮层根）⇒ 既不是「铺满视口的遮罩」，也认不出属于浮层。判据缺的就是
    # 「遮挡物属于某个浮层」这一项。
    print("— S. 批 866 跨层分档 + 分桶互斥恒等式 —")
    _rows = data.get("rows", [])
    _real = data.get("confirmed", [])
    _bmod = data.get("by_modal", [])
    _blay = data.get("by_layer", [])
    _unc = [r for r in _rows
            if not r.get("confirmed") and not r.get("covered_by_modal")
            and not r.get("covered_by_layer")]
    check("S.1 四个桶**互斥且完备**（缺陷 + 被模态盖 + 被浮层盖 + 未确认 "
          f"== 候选数，实测 {len(_real)}+{len(_bmod)}+{len(_blay)}"
          f"+{len(_unc)} vs {len(_rows)}）",
          len(_real) + len(_bmod) + len(_blay) + len(_unc) == len(_rows)
          and len(_rows) > 0,
          f"和={len(_real) + len(_bmod) + len(_blay) + len(_unc)} "
          f"候选={len(_rows)}")
    check("S.2 分桶是**一次性互斥划分**（源码里有 `def _bucket(`，四个桶都走它）"
          "—— 原来四个独立的列表推导各算各的，重叠了两次都没人管："
          "865 `124 ≠ 0+116+8`、866 `124 ≠ 0+120+9`",
          "def _bucket(" in asrc
          and asrc.count('if _bucket(r) == "defect"') == 1
          and asrc.count('if _bucket(r) == "by_modal"') == 1
          and asrc.count('if _bucket(r) == "by_layer"') == 1
          and asrc.count('if _bucket(r) == "unconfirmed"') == 1)
    check("S.3 `by_layer` 在结果里**存在**（不是缺键当成 0）",
          "by_layer" in data, f"缺键={'by_layer' not in data}")
    # 判据必须**两侧**都要：控件不在层里 **且** 遮挡物在层里。
    # 只判一侧 ⇒ 要么把「层内控件被跨层遮挡」（835 的真缺陷）误降级，
    # 要么把「认不出归属的遮挡物」塞进 INFO 藏起真缺陷。
    check("S.4 `covered_by_layer` 判据要**两侧**都在"
          "（`!inLayer` 且 `blockers.some(bk => bk.in_layer)`）",
          "!inLayer" in asrc and "blockers.some(bk => bk.in_layer)" in asrc
          and "const coveredByLayer = !inLayer" in asrc)
    check("S.5 遮挡物**认不出归属**就不许进 `by_layer`"
          "（判据是「阻塞物 `in_layer` 为真」的**正向**认定，"
          "不是「有阻塞物就算」—— 后者会把真缺陷藏进 INFO）",
          "blockers.some(bk => bk.in_layer)" in asrc
          and "bk.in_layer === true" not in acode)
    # 单一来源：控件侧 `inLayer` 与阻塞物侧 `blocker.in_layer` 必须同一份选择器
    check("S.6 `LAYER_SEL` 是**单一来源**（控件侧 `el.closest(LAYER_SEL)` 与"
          "阻塞物侧 `t.closest(LAYER_SEL)` 共用；两处各写一份就是第四次"
          "让同一判据分叉）",
          "LAYER_SEL" in asrc and acode.count("closest(LAYER_SEL)") == 2
          and "p === 'fixed' || p === 'absolute'" in asrc)
    check("S.7 835 的**降级条款**仍在（已确认的**跨层**遮挡算 INFO，"
          "不是缺陷）—— 866 自己在这行翻过一次车：补丁只匹配到多行模式的"
          "**第一行**，把这条落下，py_compile 也没抓到",
          'if r["confirmed"]:          # 835 降级条款' in asrc
          or ("835 降级条款" in asrc and 'return "by_modal"' in asrc),
          "降级条款疑似丢失")
    # §83 记的 4 条确实归位了
    # ⚠️ 第一版这里断言「== 4」，红了（实测 8）。**不是代码错了，是我把一个
    #    易变量写成了断言**：demo 画布每次加载都会**动态插入**音频/文本节点
    #    （testid 形如 `rf__node-audio-<时间戳>`），节点数逐轮不同 ⇒ 被浮层
    #    盖住的画布控件数也跟着变。4 和 8 都是真的。
    #    该断言的是**分类有没有生效**，不是**条数是多少**。
    _pi_bl = [r for r in _blay if r.get("state") == "项目信息模态"]
    _pi_unc = [r for r in _unc if r.get("state") == "项目信息模态"]
    check("S.8 §83 记的那批「未确认」**已归位**到 `by_layer`"
          f"（实测 {len(_pi_bl)} 条，**不钉条数** —— demo 画布逐轮动态插节点，"
          f"4 和 8 都是真的；钉条数就是把易变量当契约）",
          len(_pi_bl) >= 1 and not _pi_unc,
          f"by_layer={len(_pi_bl)} 仍留未确认={len(_pi_unc)}")

    # ── T. 批 868：节点内浮层进常驻状态 + **撤回**一条查错的结论 ──────
    # 867 记的三个「候选没命中」，本批**三个**都跑到了。关键不在「多测到
    # 一个」，而在于**撤回**：868 第一版把「审计里入口不在 DOM」写成
    # 「冷启动与审计上下文有差异，⚠️ 未查清」—— 那是**没查**就写成了
    # 「查不到」。真因是审计自己按的 Escape。下面 T.2–T.6 锁的是**机制**
    # （代码形态 + 注释里写没写清），不是「这次跑出来了」这种结果 ——
    # 结果会飘，机制不会；只钉结果的话，下一个人把 `select_node_soft()`
    # 一删，红的只有运气。
    print("— T. 批 868 节点内浮层 + 撤回一条查错的结论 —")
    _ascr = ROOT / "scripts/verify-jimeng-batch841-unclickable.py"
    _ausrc = (ROOT / "scripts/jimeng_unclickable_audit.py").read_text(
        encoding="utf-8")
    check("T.1 三个节点内浮层全进了**常驻状态**（文本 / 时间线 / 主体）",
          all(s in EXPECTED_STATES for s in
              ("文本·全屏编辑", "时间线·全屏", "主体·元数据编辑器")))
    _txr = {r.get("state"): r for r in data.get("keyboard", [])
            if r.get("layer") == "text-fullscreen"}.get("文本·全屏编辑", {})
    check("T.2 它**真的量到了**（不是 skipped —— 上一版把它挂在「已知缺口」"
          "上、结果 A.3「不许静默少跑」一直红）",
          bool(_txr.get("ok")) and _txr.get("layer") == "text-fullscreen"
          and not any(s.startswith("文本·全屏编辑")
                      for s in (data.get("skipped") or [])),
          f"ok={_txr.get('ok')} layer={_txr.get('layer')}")
    check("T.3 审计里有**不按 Escape 的选中** `select_node_soft(`，"
          "且注释写明它为什么必须存在（Escape 在文本编辑态里 = 取消编辑）",
          "def select_node_soft(" in _ausrc
          and "取消编辑" in _ausrc)
    # 只看**文本分支那一段**，且**用 `strip_py_comments` 剥掉 Python 注释**
    # 再判（868 自己踩过：分支里那句「⚠️ 这里**绝不能**调 `select_node()`」
    # 是注释，不剥就会被当成代码 —— 跟 864 那次「按行首过滤注释」是同一个坑，
    # 只是这次错在「以为 `strip_comments` 也管 Python」）
    _ausrc_nc = strip_py_comments(_ausrc)
    _i_txt = _ausrc_nc.index('if kind == "文本":')
    _i_end = _ausrc_nc.index("if not t.count():", _i_txt)
    _txtblk = _ausrc_nc[_i_txt:_i_end]
    check("T.4 文本分支**不再**调会按 Escape 的 `select_node(`"
          "（868 第一版的病根就在这儿：dblclick 进编辑 → 重新选中 → "
          "入口被自己按没了，**结构上**不可能成功）",
          "select_node_soft(" in _txtblk and "select_node(" not in _txtblk,
          f"soft={'select_node_soft(' in _txtblk} "
          f"旧版={'select_node(' in _txtblk}")
    check("T.5 那条错结论在**代码里被撤回**了（J 段写明「结构上不可能成功」，"
          "并**引用**原结论 + 标「那个结论是错的」）",
          "结构上不可能成功" in _ausrc
          and "那个结论是错的" in _ausrc)
    check("T.6 skipped 时会自动留下**现场** `j_ctx_dump(`，且它是**纯读**"
          "（诊断动作不许破坏被诊断状态 —— 里面出现 click/fill/press "
          "就说明它会自己把现场搅掉）",
          "def j_ctx_dump(" in _ausrc
          and not any(k in _ausrc[_ausrc.index("def j_ctx_dump("):
                                 _ausrc.index("def j_ctx_dump(") + 2400]
                      for k in (".click(", ".fill(", ".press(")))
    # ⚠️ 判「没有裸 reload」不能只数 `page.reload(` 出现次数 ——
    #    `hard_reload` **自己内部就该有**，它 docstring 里还会再提一次
    #    （docstring 是 STRING token，剥注释**剥不掉**，那是文档不是代码）。
    #    所以判据只钉真正要保证的那件事：**helper 之外一处都不许有**。
    _h0 = _ausrc_nc.index("def hard_reload(")
    # ⚠️ 区间只包 `hard_reload` **自己**（869 又在它后面加了 `page_alive` /
    #    `bail_if_dead`，把区间画到 `j_ctx_dump` 就把它们也装进来了 ——
    #    判据的区间要跟着代码走，不能靠「反正它们也不 reload」蒙对）
    _h1 = _ausrc_nc.index("def page_alive(")
    _hr = _ausrc_nc[_h0:_h1]
    _outside = _ausrc_nc[:_h0] + _ausrc_nc[_h1:]
    check("T.7 dev server 掉线不再吃掉整份审计：每一处收层都走 "
          "`hard_reload(`，且**它之外**没有裸 `page.reload(`"
          "（868 实测崩过一次：`ERR_CONNECTION_REFUSED` 让前面二十几个"
          "状态的结果全丢）",
          # ⚠️ **不钉条数**：869 加了 K 段，收层点从 2 变 3。钉 `== 2` 就是
          #   §84 S.8 那条教训的复发（demo 逐轮变、条数逐轮变）——
          #   该钉的是「一处都不许漏」这条不变量。
          _ausrc_nc.count("if not hard_reload(") >= 2
          and _hr.count("page.reload(") >= 1
          and "page.reload(" not in _outside,
          f"收层点={_ausrc_nc.count('if not hard_reload(')} "
          f"helper内={_hr.count('page.reload(')} "
          f"helper外={'page.reload(' in _outside}")
    _tl = {r.get("state"): r for r in data.get("keyboard", [])
           if r.get("layer") == "timeline-fullscreen"}
    _tlr = _tl.get("时间线·全屏", {})
    check("T.8 时间线全屏被认成**真模态**（`fixed inset-0` + 不透明底 ⇒ "
          "源站无关那条判据）",
          (_tlr.get("modalish") or {}).get("modalish") is True,
          f"modalish={(_tlr or {}).get('modalish')}")
    check("T.9 它**开层即接管焦点**（修之前焦点留在 `timeline-fullscreen-trigger`"
          " 上、而那个触发器已被自己盖住，Tab 走过 26 个看不见的焦点位）",
          (_tlr.get("focus_at_open") or {}).get("inside") is True
          and _tlr.get("covered_n") == 0,
          f"at_open_inside="
          f"{(_tlr.get('focus_at_open') or {}).get('inside')} "
          f"covered_n={_tlr.get('covered_n')}")
    check("T.10 「真模态没接管焦点」桶为 **0**"
          "（865 那条源站无关判据第一次在**真实产品缺陷**上开火，"
          "修完必须归零）",
          not data.get("keyboard_modal_no_focus"),
          f"桶里还有 {len(data.get('keyboard_modal_no_focus') or [])} 条")
    _tlc = "\n".join(ln for ln in (ROOT / "src/components/jimeng/nodes"
                                   / "JimengTimelineNode.tsx")
                     .read_text(encoding="utf-8").splitlines()
                     if not ln.strip().startswith(("//", "*", "/*")))
    check("T.11 时间线节点**真的调用**了 `useTakeFocusAtOpen(`"
          "（判「有没有接」查调用形态，不查裸名字）",
          "useTakeFocusAtOpen(" in _tlc,
          f"调用={'useTakeFocusAtOpen(' in _tlc}")
    p868 = ROOT / "scripts/jimeng_probe868_textbar.py"
    p868s = p868.read_text(encoding="utf-8") if p868.exists() else ""
    check("T.12 探针 868 在库里，并**如实标注**了那个未验死的怪癖"
          "（「根因未验死」/「未验证」不许被删掉 —— 症状确定、机制未知，"
          "把它写成结论就是下一批的坑）",
          bool(p868s) and "未验死" in p868s and "未验证" in p868s)

    # ── U. 批 869：判据「取栈顶」的实现修正 + 音色库筛选面板的真缺陷 ────
    print("— U. 批 869 浮层套浮层 + 筛选面板「四个同时展开」—")
    # ⚠️ U.1/U.2 查的是 **verifier 自己**的源码：`strip_py_comments` 是本
    #   文件里的工具（868 加的），不在审计里。第一版把它判到 `_ausrc_nc`
    #   头上 —— 判据查错了文件，绿/red 都毫无意义。
    _vsrc = _ascr.read_text(encoding="utf-8")
    _vnc = strip_py_comments(_vsrc)
    check("U.1 `strip_py_comments` 是**按 token** 剥的（用标准库 `tokenize`）"
          " —— 869 第一版把行列表建在循环体里、每次从原文重切，"
          "于是每处理一个注释就把前面的抹除冲掉，只剩最后一个生效",
          "import tokenize" in _vnc
          and "lines = src.splitlines(keepends=True)" in _vnc)
    check("U.2 `strip_py_comments` 剥得掉注释但**不动字符串**"
          "（审计把内联 JS 装在三引号里，剥坏了就是判据自己失明）"
          "，且剥不动时**原样返回**而不是给半截",
          "return src" in _vnc
          and "getBoundingClientRect" in _vnc
          and _vnc.count("getBoundingClientRect")
          == _vsrc.count("getBoundingClientRect"))
    check("U.3 `open_layer()` 现在取的是**最里层**（不是第一个命中）—— "
          "探针 869 实测：AI 抽屉里两个内层面板开着时，"
          "旧实现两次都返回外层 `canvas-agent-drawer`",
          "!hit.some(o => o !== e && e.contains(o))" in _ausrc_nc
          and "const top = hit.filter(" in _ausrc_nc)
    _sk_layer = {r.get("state"): r.get("layer")
                 for r in data.get("keyboard", [])}
    check("U.4 嵌套那层**认对了**：「搜索技能」归到内层 "
          "`agent-skills-panel`，不是外层抽屉",
          _sk_layer.get("AI 侧栏·搜索技能") == "agent-skills-panel",
          f"layer={_sk_layer.get('AI 侧栏·搜索技能')}")
    _drawer_states = [s for s, l in _sk_layer.items()
                      if l == "canvas-agent-drawer"]
    check("U.5 **只有**「AI 侧栏」那一态该归到抽屉本身"
          "（抽屉开着的时候它内层的浮层也要能被认到，否则改判据就白改了）",
          _drawer_states == ["AI 侧栏"],
          f"归到抽屉的={_drawer_states}")
    check("U.6 「全音色」那态重新归到**音色库本体**"
          "（筛选面板不再无条件常驻，栈顶自然回到外层）",
          _sk_layer.get("音频生成面板·全音色") == "audio-all-voices-listbox",
          f"layer={_sk_layer.get('音频生成面板·全音色')}")
    # ⚠️⚠️ 剥 .tsx 只能靠 `strip_comments`（JS/TS 那个）。870 第一版在这里
    #   用了 `strip_py_comments` —— 那是 Python 注释器（只认 `#`），对 TSX
    #   一点作用都没有，于是 V.3 被**我自己写在注释里**的那句
    #   「此前这里是 bottom-[…]」判成红的。换对工具之后**仍然**判红 ——
    #   剥注释器对这份文件不干净，所以那条判据改成打**代码形态**（见 V.3）。
    _agp_raw = (ROOT / "src/components/jimeng/JimengAudioGenPanel.tsx") \
        .read_text(encoding="utf-8")
    _agp = strip_comments(_agp_raw)
    # ⚠️⚠️ U.7/U.8 原来钉的是**实现字面量**（`options && filterSel[…] !==
    #   undefined` / `aria-expanded={filterSel[…] !== undefined}`）。批 873
    #   把「开着没有」拆成独立的 `filterOpen` 之后，那两句字面量自然不成立
    #   —— 而它们要护的**意图**（渲染条件带开合判据 / 那个钮能关）**一个字
    #   都没变**。钉字面量就会逼着人把拆状态这个修复退回去。
    #   所以这两条改成钉**意图**：条件里必须有一个**随状态变化**的判据，
    #   且那个**无条件**的老写法不许回来。
    check("U.7 筛选面板的渲染条件**带开合判据**（不是无条件的 `options ?`"
          " —— 而 `options` 是写死的非空数组，无条件渲染 ⇒ 「全音色」一打开"
          "四个面板同时展开、y 全为负、点不到也关不掉；探针 870 量完才动手。"
          "873 又把开合拆成独立 `filterOpen`，判据换了写法但意图没变）",
          "{options ? (" not in _agp
          and "options && filterOpen[label] === true" in _agp,
          f"无条件渲染还在={'{options ? (' in _agp} "
          f"带判据={'options && filterOpen[label] === true' in _agp}")
    check("U.8 筛选钮**能关上**了：开合由 `setFilterOpen` **取反**负责"
          "（870 原来 `? null : m[label]` 把值原样写回去，只能开关不了；"
          "873 之后开合不再靠选中值），选中值的 `? null : undefined` 切换"
          "仍在，且 `aria-expanded` 跟着 `filterOpen` 走",
          "setFilterOpen((o) => ({ ...o, [label]: !o[label] }))" in _agp
          and "? null : undefined" in _agp
          and "aria-expanded={filterOpen[label] === true}" in _agp)
    p869 = ROOT / "scripts/jimeng_probe869_drawerpanels.py"
    p870 = ROOT / "scripts/jimeng_probe870_voicefilter.py"
    p869s = p869.read_text(encoding="utf-8") if p869.exists() else ""
    p870s = p870.read_text(encoding="utf-8") if p870.exists() else ""
    check("U.9 探针 869/870 在库里，且判据**直接从审计源码取**"
          "（`open_layer()` 的 JS 不许抄第二份 —— 抄一份就是让同一判据分叉；"
          "两个探针都写明取不到就抛、不返回空串）",
          bool(p869s) and bool(p870s)
          and "def _extract_js(" in p869s and "def _extract_js(" in p870s
          and "不返回空串" in p869s and "不返回空串" in p870s)
    check("U.10 页面死了要**当场退出码 2**，不许把「跑不动了」拆成 20 条"
          "「前置态没成立」（869 实测：dev server 中途掉线，"
          "后面 20 个状态全记成前置态问题，看着像结论）",
          _ausrc_nc.count("if bail_if_dead(") == 3
          and "def bail_if_dead(" in _ausrc_nc
          and "def page_alive(" in _ausrc_nc)

    # ── V. 批 870：源站取样把「筛选面板落在视口外」那一半也修掉了 ──────
    print("— V. 批 870 音色库筛选面板：源站取样 + 版式逐项对齐 —")
    _vf = {r.get("state"): r for r in data.get("keyboard", [])
           if r.get("layer") == "audio-voice-filter-listbox"}
    check("V.1 筛选下拉进了**常驻契约**，而且真的量到了"
          "（870 之前它测不了：面板无条件常驻 + `open_layer()` 认外层）",
          "音频生成面板·音色筛选" in EXPECTED_STATES
          and bool(_vf.get("音频生成面板·音色筛选", {}).get("ok")),
          f"契约里={'音频生成面板·音色筛选' in EXPECTED_STATES} "
          f"ok={_vf.get('音频生成面板·音色筛选', {}).get('ok')}")
    check("V.2 它归到**自己**而不是外层音色库（869 那条 `open_layer()` 修正的"
          "第二个受益者）",
          _vf.get("音频生成面板·音色筛选", {}).get("layer")
          == "audio-voice-filter-listbox")
    _stale_cls = [ln.strip()[:60] for ln in _agp_raw.splitlines()
                  if "bottom-[calc(100%+6px)]" in ln and "className" in ln]
    check("V.3 展开方向是**向下**（源站实测：钮 153×28 @y656、层 161×124 @y692，"
          "即钮底 +8）—— 此前是 `bottom-[calc(100%+6px)]` 向上展开，"
          "实测 y 跑到 -56，整个面板在视口外点不到",
          "top-[calc(100%+8px)]" in _agp
          and not _stale_cls
          and "left-[-4px]" in _agp and "w-[161px]" in _agp,
          f"下向={'top-[calc(100%+8px)]' in _agp} 残留={_stale_cls}")
    check("V.4 `aria-label` **逐字抄源站**的 `{label} options`"
          "（源站实测 aria-label=`性别 options`；此前复刻自造「筛选 性别」）",
          "aria-label={`${label} options`}" in _agp
          and "筛选 ${label}" not in _agp)
    p870s_ = ROOT / "scripts/jimeng_probe870_voicefilter_src.py"
    _p870s = p870s_  .read_text(encoding="utf-8") if p870s_.exists() else ""
    check("V.5 源站探针在库里，且**先验登录态**再动手"
          "（掉到登录页就记 BLOCKED_BY_FIXTURE，"
          "绝不把「登录没了」写成「源站没有筛选钮」）",
          bool(_p870s) and "logged_in" in _p870s
          and "不是**「源站没有筛选钮」" in _p870s)

    # ── W. 批 871：筛选下拉的**键盘行为**取样入表 + 复刻对齐 ────────────
    print("— W. 批 871 筛选下拉的键盘基线 + 复刻对齐 —")
    # ⚠️ 条目的结束是 `…src": "…"},`（**收尾和 src 同一行**），不是单独一行
    #   `},` —— 第一版按后者写正则，一个都没匹配上，W.1/W.2 直接假红。
    #   边界改成「到下一个同缩进的条目键为止」，别猜收尾长什么样。
    _sb = re.search(r'"audio-voice-filter-listbox":\s*\{(.*?)\n        "',
                    _ausrc, re.S)
    _sbtxt = _sb.group(1) if _sb else ""
    check("W.1 源站基线表里有这一层，且三项键盘行为**都记了实测值**"
          "（870 只对齐了版式，键盘一概没取 ⇒ 一直挂 `kb_not_sampled`，"
          "不受任何判据管）",
          bool(_sbtxt) and '"takes_focus_at_open": True' in _sbtxt
          and '"traps_tab": False' in _sbtxt
          and '"arrows_move": True' in _sbtxt
          and "jimeng_probe871_voicefilter_kb.py" in _sbtxt)
    check("W.2 「Tab 不经过这一层」被记成**字段**（`walk_note`）而不是注释"
          " —— 否则半年后有人读到 `walk=None` 会当成缺陷去修",
          '"walk_note"' in _sbtxt and "capped=True" in _sbtxt)
    _not_sampled = [b for b in (data.get("keyboard_not_sampled") or [])
                    if isinstance(b, dict)
                    and b.get("layer") == "audio-voice-filter-listbox"]
    check("W.3 复刻这一层**已经不在**「源站没取过样」名单里"
          "（进表 = 从此受判据管，坏了会报出来）",
          not _not_sampled, f"仍在名单={len(_not_sampled)}")
    _w = _vf.get("音频生成面板·音色筛选", {})
    check("W.4 复刻侧三项与源站基线**逐项相符**"
          "（开层接管焦点 / 不困 Tab / 方向键逐格移动）",
          (_w.get("focus_at_open") or {}).get("inside") is True
          and (_w.get("arrow_down") or {}).get("moved") is True
          and (_w.get("escape") or {}).get("trapped") is False,
          f"at_open={(_w.get('focus_at_open') or {}).get('inside')} "
          f"arrow={(_w.get('arrow_down') or {}).get('moved')} "
          f"trapped={(_w.get('escape') or {}).get('trapped')}")
    _agp2 = strip_comments(_agp_raw)
    check("W.5 复刻**真的接了**那三件事（判调用形态，不查裸名字）："
          "四个 `useTakeFocusAtOpen(` + 方向键 handler + Esc 收层并把焦点"
          "还给筛选钮",
          _agp2.count("useTakeFocusAtOpen(filter") == 4
          and 'e.key === "ArrowDown"' in _agp2
          and 'e.key === "Escape"' in _agp2
          and "chip?.focus()" in _agp2,
          f"hook×{_agp2.count('useTakeFocusAtOpen(filter')} "
          f"方向键={'e.key === \"ArrowDown\"' in _agp2} "
          f"Esc={'e.key === \"Escape\"' in _agp2}")
    p871 = ROOT / "scripts/jimeng_probe871_voicefilter_kb.py"
    _p871 = p871.read_text(encoding="utf-8") if p871.exists() else ""
    check("W.6 源站键盘探针在库里，且**每项测量各自建立前置态**"
          "（`reopen_filter()`）—— 头两版栽在这儿：Tab 途中层已经被关掉，"
          "于是 ③④ 读到的全是「层不存在」，长得跟真结论一模一样",
          bool(_p871) and "def reopen_filter(" in _p871
          and _p871.count("reopen_filter()") >= 3
          and "前置态没成立" in _p871)

    # ── X. 批 872：另外三个筛选钮**逐个**取样（不许拿「同一组件」推测）──
    print("— X. 批 872 四个筛选钮逐个取样，基线从「一个」升级为「四个」—")
    p872 = ROOT / "scripts/jimeng_probe872_voicefilters_kb.py"
    _p872 = p872.read_text(encoding="utf-8") if p872.exists() else ""
    check("X.1 探针 872 在库里，且**四个标签都列全了**"
          "（少列一个就等于有一个钮没取样，却看着像「都测过了」）",
          bool(_p872) and all(f'"{l}"' in _p872 for l in
                              ("性别", "年龄", "语言", "声音特点")))
    check("X.2 「音色库开着没有」那条判据查的是**它自己的标题**"
          "（第一版查 `[role=listbox]` —— 筛选层自己也是 listbox，"
          "于是「筛选层还开着」被读成「音色库开着」，四个里丢了两个，"
          "记成 BLOCKED_BY_FIXTURE）",
          "get_by_text(\"全音色\", exact=True).count()" in _p872
          and "page.locator('[role=listbox]').count() and" not in _p872)
    check("X.3 基线条目现在写明是**四个钮逐个实测**的共同结论，"
          "不是从「性别」外推的（871 当时明写「不许推测」）",
          "**四个筛选钮逐个实测**" in _sbtxt
          and "124/164/244" in _sbtxt
          and "jimeng_probe872_voicefilters_kb.py" in _sbtxt)
    check("X.4 高度公式被记成**实测三点**（n=3/4/6 ⇒ 124/164/244）"
          "，不是照着 3 项那一个值推的",
          "n×36+(n−1)×4+8" in _sbtxt and "三点全中" in _sbtxt)

    # ── Y. 批 873：把「**选完之后**」也测了（前面几批只测「打开」）──────
    print("— Y. 批 873 选完一个选项之后：收层 / 焦点回钮 / 文案与 aria —")
    p873 = ROOT / "scripts/jimeng_probe873_voiceselect.py"
    _p873 = p873.read_text(encoding="utf-8") if p873.exists() else ""
    check("Y.1 源站「选完之后」探针在库里，且**两条选项路径都量**"
          "（选具体值 vs 选「全部 X」）—— 复刻两条走同一个 onClick，"
          "「同一个回调 ⇒ 行为一样」是推测不是取样",
          bool(_p873) and '"全部 性别", "男"' in _p873
          and "不合并成结论" in _p873)
    check("Y.2 源站探针第二轮**不再按旧文案**找芯片（选完之后芯片文案已经"
          "变了，按旧名找必然数到 0 ⇒ 被记成「前置态没成立」）"
          "，改用开层时记下的坐标并**验落点**",
          "chip_rect_reused" in _p873 and "不是按钮" in _p873)
    check("Y.3 「开着没有」和「选了什么」是**两个状态**"
          "（原来一个 `filterSel` 兼任两职 ⇒ 选中值还在 ⇒ 层收不起来；"
          "源站实测选完**都**收层）",
          "const [filterOpen, setFilterOpen]" in _agp2
          and "options && filterOpen[label] === true" in _agp2
          and _agp2.count("[label]: false") >= 2)
          # 上面那两处：Esc 收层、选完收层（源站实测两条都收）
    check("Y.4 选完之后**焦点回筛选钮**（源站实测落点 `BUTTON/性别: 男`；"
          "复刻原先什么都不做 ⇒ 面板一卸焦点**掉到 body**，那是最坏落点）",
          "chipBtn?.focus()" in _agp2
          and "closest('[role=\"listbox\"]')" in _agp2)
    check("Y.5 芯片的 `aria-label` 按源站实测的 **`{筛选名}: {当前值}`** 对齐"
          "（复刻原先没有 aria-label，选中之后可访问名会从「性别」变成「男」，"
          "筛选维度就丢了）"
          " ⚠️ 875 改判据：原来这里钉的是字面量 "
          "`${label}: ${filterSel[label] ?? label}`，而 875 查清**那个写法"
          "本身就是半抄**（见 Z.4），按 U.7/U.8 的同一条规矩改成钉**意图**："
          "可访问名里必须同时出现筛选名和当前值，未选中时当前值取「全部 X」。",
          "${label}: ${curFilterVal(label)}" in _agp2
          and "const curFilterVal" in _agp2)

    # ── Z. 批 874/875：873 留下的自选行为被证伪/证实 + 挖出清除钮 ─────
    print("— Z. 批 874/875：焦点落点身份、Esc 保留值、清除钮、「全部」语义 —")
    p874 = ROOT / "scripts/jimeng_probe874_escvalue.py"
    p875 = ROOT / "scripts/jimeng_probe875_clearfilter.py"
    p875c = ROOT / "scripts/jimeng_probe875_clearfilter_ck.py"
    _p874 = p874.read_text(encoding="utf-8") if p874.exists() else ""
    _p875 = p875.read_text(encoding="utf-8") if p875.exists() else ""
    _p875c = p875c.read_text(encoding="utf-8") if p875c.exists() else ""
    check("Z.1 874 探针在库里，且**两问都在**：① 焦点落点那个 BUTTON 到底是什么"
          "（873 只读到 `BUTTON/性别: 男` 就照抄了形式，来路没查清）；"
          "② 选完值按 Esc，值还在不在（873 留下的**唯一一个自选行为**）",
          "焦点落点那个 BUTTON 到底是什么" in _p874
          and "选完一个值之后按 Esc" in _p874
          and "WHO_JS" in _p874)
    check("Z.2 875 源站探针**四个筛选钮逐个**取样，不是拿「性别」外推"
          "（4/4 一致才敢写进基线）；且第一跑的两个自身错误"
          "（选项名照着筛选名**猜**、判据拿 1 个 option 比 1 整列）"
          "在探针里**留了痕**——错判据不许悄悄改掉",
          all(f'("{lb}"' in _p875 for lb in ("性别", "年龄", "语言", "声音特点"))
          and "是我**照着筛选名猜**的" in _p875
          and "第五次「量错对象」" in _p875
          and "seld == [allopt]" in _p875)
    check("Z.3 清除钮进了 `SOURCE_BASELINE`（五项实测：aria 形式 / 尺寸 /"
          "「未选中时不存在」/ 点了之后值回落且自己消失且焦点回芯片 /"
          "「没设值」= 全部项选中），且**逐条注明了探针来源**",
          '"has_clear_button": True' in _ausrc
          and '"clear_aria": "Clear {筛选名} filter"' in _ausrc
          and '"no_value_means_all_selected": True' in _ausrc
          and '"esc_keeps_value": True' in _ausrc
          and "jimeng_probe875_clearfilter.py" in _ausrc
          and "jimeng_probe874_escvalue.py" in _ausrc)
    check("Z.4 「没设值」= **`全部 {筛选名}` 那一项被选中**，哨兵统一成 `null`"
          "（复刻原先拿筛选名当哨兵，清掉之后层里 `seld=[]` 一个都不选中，"
          "与源站相反；873 抄 aria 时**只抄了一半** —— 注释里记着未选中时读作"
          "`BUTTON/性别: 全部 性别`，代码却写成 `?? label`）",
          "const curFilterVal = (label: string): string =>" in _agp2
          and "filterSel[label] ?? `全部 ${label}`" in _agp2
          and "aria-selected={curFilterVal(label) === opt}" in _agp2
          and "? null : opt" in _agp2
          # 旧哨兵不许回来：`?? label` 当可访问名
          and "${label}: ${filterSel[label] ?? label}" not in _agp2)
    check("Z.5 清除钮**逐字照抄**源站的英文 aria，且**有值才渲染**"
          "（源站 4/4：未选中时压根不存在；复刻原先没有这个控件 ⇒ "
          "选中之后没法退回「全部」，只能再点开层再点「全部 X」）",
          "aria-label={`Clear ${label} filter`}" in _agp2
          and "X," in _agp2
          # 渲染条件必须跟着「有没有值」，不能无条件
          and "{filterSel[label] ? (" in _agp2)
    check("Z.6 清除钮**先收焦点再改状态**（层若开着会在同一帧被卸载）"
          "，且清了之后**顺手把层也关上**",
          _agp2.count("chipRefs.current[label]?.focus();") >= 1
          and "setFilterSel((m) => ({ ...m, [label]: null }))" in _agp2
          and "setFilterOpen((o) => ({ ...o, [label]: false }))" in _agp2)
    check("Z.7 外层格子**锁宽 153**（源站 `row_dom_after` 实测：选中前后"
          "外层都是 153×28，变的只是格子里装什么）。不锁的话复刻选中后"
          "缩到 135 ⇒ 整行左移、后面三个筛选钮全部错位",
          'className="relative flex h-7 w-[153px] shrink-0 items-center gap-2 px-[9px]"'
          in _agp2
          and "w-[135px]" in _agp2 and "w-[111px]" in _agp2
          and "size-4" in _agp2)
    check("Z.8 复刻探针的判据跟**源站探针同构**（两边 JSON 可直接对账），"
          "且**刻意不钉会漂的绝对坐标**（Clear 的 [814,689] 随面板位置变，"
          "只断言它与芯片的相对关系）",
          bool(_p875c) and "源站 875" in _p875c
          and "不**断言「Clear 的坐标是" in _p875c
          and "n_value_cleared" in _p875c and "n_row_unchanged" in _p875c)
    check("Z.9 清除钮**没有**被塞进审计的 `measure()` 状态表"
          "（它不是浮层，塞进去会让状态语义不对）；运行时证据由复刻探针"
          "**真的点下去**给出（4/4 `hit_ok` + 值真的回落），"
          "代码形态由 Z.4–Z.7 钉住 —— 两边都要，不靠一处",
          "audio-voice-filter-clear" not in _ausrc
          and "hit_ok" in _p875c and "value_cleared" in _p875c)

    # ── AA. 批 876：清除钮的**键盘**行为取样 + 一处真差异修掉 ──────
    print("— AA. 批 876 清除钮键盘行为：Tab 在序列里 / Enter·Space 触发 / "
          "方向键不接 / Esc 触发清除 —")
    p876 = ROOT / "scripts/jimeng_probe876_clearfilter_kb.py"
    p876b = ROOT / "scripts/jimeng_probe876b_clearfilter_mech.py"
    p876c = ROOT / "scripts/jimeng_probe876c_clearfilter_kb2.py"
    p876k = ROOT / "scripts/jimeng_probe876c_clearfilter_kb2_ck.py"
    _p876 = p876.read_text(encoding="utf-8") if p876.exists() else ""
    _p876b = p876b.read_text(encoding="utf-8") if p876b.exists() else ""
    _p876c = p876c.read_text(encoding="utf-8") if p876c.exists() else ""
    _p876k = p876k.read_text(encoding="utf-8") if p876k.exists() else ""
    check("AA.1 876 的三跑链**都在库里**，且每一跑都写明了自己**作废/查机制"
          "的理由**——876 两处起点错（用 mouse.click 聚焦 Clear，而点它本身就是"
          "清除；用 mouse.click 聚焦芯片，而芯片是 toggle 会打开筛选层），"
          "876c 才是用**程序化 focus** 的那跑。**错判据不许悄悄改掉**。"
          " ⚠️ 这条**第一版是 FAIL 的，而且 FAIL 得对**：876 自己的 docstring 里"
          "**压根没有作废声明**（它当时还不知道自己会作废）——"
          "「只留跑对的那几个」正是被它破掉的。作废横幅已补上。",
          bool(_p876) and bool(_p876b) and bool(_p876c) and bool(_p876k)
          and "本文件**整跑作废**" in _p876
          and "真结论由" in _p876
          and "上一跑（876）为什么作废" in _p876b
          and "把 876 的三处**起点错**钉死" in _p876c
          and "程序化 focus" in _p876c)
    check("AA.2 源站键盘行为进了 `SOURCE_BASELINE`（Tab 在序列里且紧跟芯片 / "
          "Enter / Space 触发清除 / 方向键不接 / Esc 触发清除**且**顺带关掉"
          "整个音色库面板），并单独记了 `esc_depends_on_focus`",
          '"clear_in_tab_order": True' in _ausrc
          and '"clear_enter_fires": True' in _ausrc
          and '"clear_space_fires": True' in _ausrc
          and '"clear_arrows_dead": True' in _ausrc
          and '"clear_esc_fires": True' in _ausrc
          and '"clear_esc_also_closes_voices": True' in _ausrc
          and '"esc_depends_on_focus": True' in _ausrc)
    check("AA.3 复刻的 Clear **响应 Esc**：焦点在它上面按 Esc 会清除"
          "（875 加按钮时漏了；源站 876c 三次复现）。且**刻意不**"
          "`stopPropagation` —— 源站 Esc 是「清除 **+** 关掉整个面板」"
          "两个动作同时发生，关面板那半必须**继续冒泡**给上层 handler",
          "onKeyDown={(e) => {" in _agp2
          and 'if (e.key === "Escape")' in _agp2
          and "[label]: null," in _agp2
          and "不** `stopPropagation()`" in _agp2)
    check("AA.4 Clear 的 Esc 分支**不** `focus()` 芯片"
          "（源站实测 Esc 后焦点落在**音频节点本体**，不是芯片 —— 面板要关、"
          "芯片一起卸载；强行聚焦只会多出一个源站没有的落点）",
          # onClick 分支有 focus()，onKeyDown 分支没有：数一下
          "chipRefs.current[label]?.focus();" in _agp2
          and _agp2.count("chipRefs.current[label]?.focus();") == 1)
    check("AA.5 复刻探针读值走的是**零破坏**读法（芯片的可见文案本身就是值），"
          "那个「点开层再点芯片收层」的有破坏性读法只留作**交叉校验**、"
          "默认不调 —— 第一跑就是被它**改了状态**才让 Enter/Space/方向键"
          "三项全记成「聚不到焦点 ⇒ 测不了」",
          "def value_text():" in _p876k
          and "这个读法**有破坏性**" in _p876k
          and _p876k.count("value_now()") == 1)
    check("AA.6 复刻探针对「读不到」与「没有」**分栏记账**"
          "（源站 876c 前两跑栽在这：`reopened=False` 被判据读成"
          "「值没了」，还印出肯定句 —— 第四次「把够不着写成没有」）",
          "不是「值没了」" in _p876c and "不是「值没了」" in _p876k
          and "None      # None = 未知，不是 False" in _p876c)
    check("AA.7 Esc 之后**重开**读值，而不是当场读（当场读会被「面板已经关了」"
          "污染：Clear 读不到、值读不到，看着像清除也发生了）；"
          "重开失败要先**重新选中节点**搭回前置态，"
          "因为 Esc 之后音频生成面板整个收起、`音色: 音色库` 压根不在 DOM 里",
          "前置态没成立：Esc 之后**音色库没开回来**" in _p876c
          and "def reselect_node():" in _p876c
          and "重新选中节点 → 面板回来 → 再开音色库" in _p876c)

    # ── BB. 批 877/878：键盘行为四钮逐个 + 「掉 body」是疏忽不是夹具 ──
    print("— BB. 批 877/878：四钮逐个重测（6/6）+ Clear 上 Esc 的焦点落点 —")
    p877 = ROOT / "scripts/jimeng_probe877_clearfilter_kb_all.py"
    p878 = ROOT / "scripts/jimeng_probe878_nodefocus_ck.py"
    _p877 = p877.read_text(encoding="utf-8") if p877.exists() else ""
    p881 = ROOT / "scripts/jimeng_probe881_domreplace_ck.py"
    _p878 = p878.read_text(encoding="utf-8") if p878.exists() else ""
    _p881 = p881.read_text(encoding="utf-8") if p881.exists() else ""
    check("BB.1 877 探针在库里，且**四个筛选钮都列全了**（少一个就等于有一个"
          "没取样，却看着像「都测过了」）；选项名用的是 **875 从层里读到的真名**"
          "（普通话 / 适合旁白…），不是照筛选名猜的",
          all(f'("{lb}"' in _p877 for lb in ("性别", "年龄", "语言", "声音特点"))
          and "普通话" in _p877 and "适合旁白" in _p877)
    check("BB.2 877 **一次只让一个钮有值**（每轮先清空全部四个）——"
          "都选中时 Tab 序列是 芯片→Clear→年龄→年龄的Clear→…，"
          "根本分不清哪个 Clear 是谁的",
          "def clear_all():" in _p877
          and "一次只让**一个**钮有值" in _p877
          and "n_tab1_clear" in _p877)
    check("BB.3 基线把键盘行为**标注成「四个钮逐个」**，并把 Tab 轨迹的规律"
          "写进去（Clear 紧跟本钮芯片 → 后续筛选钮 → 音色网格）——"
          "876 只测过「性别」，§69 说按同类推测不许当结论",
          '"clear_sampled_on": "**四个筛选钮逐个**（877，6/6 项全中）"' in _ausrc
          and "**Clear 紧跟本钮芯片**" in _ausrc)
    check("BB.4 877 **主动缩了量**（Space 不单测，与 Enter 同一浏览器行为路径）"
          "并把这条缩量**写在明处** + 给出了「什么情况下该改回来」的条件"
          "—— 主动缩量必须留痕，否则半年后看成「漏测」",
          "Space 不单测" in _p877
          and "不增加信息量" in _p877
          and "不是漏测" in _p877)
    check("BB.5 878 探针在库里，且它**只量机制、不下产品结论**"
          "（「节点能不能被聚焦」是判定的**必要前提**——能聚焦 ⇒ body 是疏忽，"
          "不能聚焦 ⇒ body 是必然；§77 机制未验死之前不许改判据）",
          "缺陷还是夹具" in _p878
          and "先量再判" in _p878
          and "n_focusable" in _p878 and "n_tab_into_node" in _p878)
    check("BB.6 复刻 Clear 的 Esc 把焦点送到该音频节点**并在它被抢走之后补落**"
          "（881 焦点**事件流**实测：同步 focus **成功** +3~6ms，"
          "但 +46~56ms 被某个**延迟动作**抢走 ⇒ 同步落焦点**不够**）。"
          "定位走 `closest('.react-flow__node-toolbar')` → 读 `data-id` →"
          "**属性相等**找节点（⚠️ 不是选择器字符串拼接：节点 id 可能含 `:`）",
          'closest(".react-flow__node-toolbar")' in _agp2
          and 'n.getAttribute("data-id") === nid' in _agp2
          and "requestAnimationFrame(refocus)" in _agp2
          and "setTimeout(refocus, 120)" in _agp2)
    check("BB.7 基线里的焦点落点**不许照抄节点序号**（`音频 node: 音频 38` 里的"
          "`38` 逐轮插节点就变，是**易变量**）—— 只记「落在该节点本体」",
          '"clear_esc_focus": "该音频节点本体' in _ausrc
          and "序号是易变量，不许钉" in _ausrc)
    check("BB.8 880/881/882 的**机制链**记进基线，每一步排除了什么、结论停在哪。"
          " ⚠️ 882 把 881 那条「未查明」**作废**并给出**根因**："
          "`@xyflow/react` 的 `useNodesSelection` 在节点失去选中态时于 "
          "`requestAnimationFrame` 里 `nodeRef.blur()`，且那个 rAF 注册得**更晚**"
          "（状态更新后那次渲染里）⇒ 同一个 rAF 队列里它排在我们后面。"
          "**根修是双层 rAF**，不是 120ms 兜底；未验证的部分"
          "（**注册顺序不是契约**）必须**留在基线里不许删**"
          " ⚠️⚠️ 本条**第二版**：第一版还要求「源站是否也取消选中」"
          "**留在**未验证清单里 —— 而 885 已经把它**测出来了**"
          "（源站也取消、也 blur，但 blur 之后焦点被抢回来）⇒ "
          "那条要求**过期了**。判据要跟上事实，但不能顺势把"
          "「注册顺序不是契约」这条**一起删掉** —— 它仍未验证。",
          '"clear_esc_focus_mechanism"' in _ausrc
          and "useNodesSelection" in _ausrc
          and "根修 = **双层 rAF**" in _ausrc
          and "注册顺序" in _ausrc and "不是契约" in _ausrc)
    check("BB.9 881 探针的**判据跟着事实一起改过**（第一版只看「DOM 有没有被"
          "替换」，于是修好之后仍然打出「机制仍未查清」—— 方向相反的同族错误："
          "**修好了还说没查清**）。现在按「焦点最终在不在节点上」分两条互斥判据，"
          "并把「仍未查明」单列一栏",
          "判据**跟着事实一起改过**" in _p881
          and "修好了还说没查清" in _p881
          and "res[\"why_still_unknown\"]" in _p881)
    p882 = ROOT / "scripts/jimeng_probe882_whostealsfocus_ck.py"
    _p882 = p882.read_text(encoding="utf-8") if p882.exists() else ""
    p883 = ROOT / "scripts/jimeng_probe883_escselect_src.py"
    _p883 = p883.read_text(encoding="utf-8") if p883.exists() else ""
    p884 = ROOT / "scripts/jimeng_probe884_selectnode_src.py"
    p885 = ROOT / "scripts/jimeng_probe885_escselect2_src.py"
    _p884 = p884.read_text(encoding="utf-8") if p884.exists() else ""
    _p885 = p885.read_text(encoding="utf-8") if p885.exists() else ""
    check("CC.1 884 把「在源站**可靠地选中一个指定节点**」这个前置问题解决了"
          "（五种落点**各 2/2**，且**重复试**——证明可靠不是碰巧一次），"
          "同时查清 883 差分恒为 0 的**真因**",
          bool(_p884) and "重复 2 次" in _p884
          and "reliable" in _p884 and "n_success" in _p884)
    check("CC.2 883 探针里那条「**同一份探针里两种找法指向不同元素**」的"
          "教训留在代码里：`NODE_DUMP_JS` 只认 `data-testid`、**不**按 aria "
          "取第一个（示例画布里本来就有音频节点）—— **第五次「量错对象」，"
          "形状是 key 不统一**",
          "同一个探针里 key 不统一" in _p883
          and "不**按 aria 找第一个" in _p883
          and "示例画布里本来就有音频节点" in _p883)
    check("CC.3 885 **只做一件事**且把 884 的成果**用起来**：五种落点"
          "**依次备胎**、旁证（工具条在不在）**把关**，"
          "而不是像 883 那样「点一次、打印旁证、继续跑」",
          bool(_p885) and "def select_node(" in _p885
          and "旁证把关，策略备胎" in _p885
          and "不是「点一次就记账」" in _p885)
    check("CC.4 885 的结论写进基线并**作废**「更根本的疑点」："
          "**源站 Esc 之后节点也取消选中**（工具条 True→False），"
          "但焦点仍落在节点本体 ⇒ 「取消选中」**不是**差异，"
          "差异只在「blur 之后有没有人抢回焦点」⇒ "
          "**882 的双 rAF 治对了，不是治症状**",
          '"clear_esc_node_unselected_too": True' in _ausrc
          and "作废" in _ausrc
          and "不是**差异" in _ausrc
          and "治对了" in _ausrc)
    check("CC.5 「五种策略都可靠」这个结论**只由 884 支撑**（每个 2/2）；"
          "885 只试了 `center` 就命中、**备胎没被检验过** —— "
          "未检验的机制不许写成「可靠」",
          "备胎没派上用场" in _ausrc
          and "没被检验过" in _ausrc)
    p886 = ROOT / "scripts/jimeng_probe886_esconchip_src.py"
    _p886 = p886.read_text(encoding="utf-8") if p886.exists() else ""
    check("CC.6 886 取到了「**芯片上**按 Esc」的源站落点，并记成**另一条路径、"
          "同一个落点**（源站首次取样 ⇒ 复刻落 body 是**真差异**，已修）",
          bool(_p886)
          and '"chip_esc_focus": "该音频节点本体' in _ausrc
          and "「落点」和「值」是**两件事**" in _p886)
    p888 = ROOT / "scripts/jimeng_probe888_reopen_src.py"
    p887 = ROOT / "scripts/jimeng_probe887_esconchip_val_src.py"
    _p888 = p888.read_text(encoding="utf-8") if p888.exists() else ""
    _p887 = p887.read_text(encoding="utf-8") if p887.exists() else ""
    check("CC.10 888 查清了那个挡了**四跑**的前置问题：Esc 之后面板**真卸载**"
          "（`voice_btn`/`node_form`/`toolbar` 全不在 DOM）但**回得来** ——"
          "五种重开手段**各 2/2**；而且**源站节点 class 没有 `selected` 标记**"
          "（`node_has_selected_class=False`、无 `aria-selected`/`aria-pressed`）"
          "⇒ 「选中态」**不能**靠 class 判",
          bool(_p888) and "reliable_reopen" in _p888
          and "node_has_selected_class" in _p888
          and "不在 DOM 里" in _p888)
    check("CC.11 888 的根因落到**探针模板**上：`select_node()` 原来**先点空白"
          "再点节点** —— Esc 之后节点本已取消选中，那一下多余的「点空白」"
          "若落在节点上就变成「选中→立刻取消」⇒ 净效果把面板关掉。"
          "886/887 已改成**先验旁证**、绝不先点空白；"
          "885 的**策略备胎**版**刻意保留** `click_blank()`（那里它有正当用途）",
          "先验旁证" in _p886 and "先验旁证" in _p887
          and "绝不**先点空白" in _p886
          # ⚠️ 判「有没有再点空白」**不能只 grep 到 `click_blank` 这个词**：
          # 「定义了但从没调用」和「调用了」在文本上长得一模一样。必须数
          # **出现次数**：886/887 = 1（只剩 `def`，是死代码）；885 = def + 调用。
          and _p886.count("click_blank") == 1
          and _p887.count("click_blank") == 1
          and "def click_blank" in _p886 and "def click_blank" in _p887
          # ⚠️⚠️ 888 第一版这里**正文说了 885 刻意保留，却一个条件都没查**
          # —— 又一次「该被钉的地方没钉」（第三次同族错误，见 CC.8）。
          # 885 是**策略备胎**版，`click_blank()` 在那里有正当用途：把起点
          # 统一为「未选中」，否则分不清命中的是本次点击还是上一轮残留。
          and _p885.count("click_blank") >= 2
          and "起点统一为「未选中」" in _p885
          # 888 自己记的是**重开路径**那件事（真卸载 + 重复 2 次的纪律），
          # 不是探针模板缺陷 —— 模板缺陷写在 886 的 `select_node` docstring 里。
          and "**不在 DOM 里**" in _p888
          and "重复 2 次" in _p888)
    check("CC.12 887 在**同一次运行**里读到「芯片上 Esc 的落点 + 值」，"
          "**证伪了** 886 第一版写的「芯片那条不清值」：层**收着**时值**被清**"
          "（`男 → 性别`、Clear 重开后不在）"
          " ⇒ 两条路径现在**完全一致**（都清值/都关层/都落该节点本体）",
          '"chip_esc_clears_value_when_layer_closed": True' in _ausrc
          and "**证伪了**" in _ausrc
          and "值被清" in _ausrc)
    check("CC.13 887 **修正了 874 的适用范围**：`esc_keeps_value` 只在"
          "**层开着**时成立；层**收着**时被清。Esc 的行为由**两个**变量决定："
          "**焦点在哪**（§95/§96）**和层开没开** —— 只测一条就会测反"
          "（874 就测反了），所以基线里那条字段**必须带条件**",
          '"esc_keeps_value_仅在层开着": True' in _ausrc
          and '"esc_keeps_value_when_layer_closed": False' in _ausrc
          and '"esc_depends_on_layer_open_too": True' in _ausrc
          and "第一版这里写得太宽，是错的" in _ausrc)
    check("CC.14 888 收尾：复刻探针 876c_ck 第 ④ 段（芯片上按 Esc）的**结论"
          "措辞**按 887 改正 —— 第一版把「值没了」写成「与源站相反」，"
          "而 887 证明**层收着时源站正是清值**，**措辞正好说反了**"
          "（把一条被限定过适用范围的 874 读数当成了普适结论）。"
          "同时把「层开没开」**显式记进结果**（`layer_open_before_esc`）——"
          "874 就是在隐式起点上读错的；反向告警（值还在 = 与源站相反）"
          "也**必须留着**，否则改回错的方向也没人拦",
          "888 更正" in _p876k and "它**层是开着的**" in _p876k
          and '"layer_open_before_esc": layer_open()' in _p876k
          and "LAYER_OPEN_JS" in _p876k
          and "与 887 源站一致：层收着时清值" in _p876k
          and "与 887 源站相反：层收着时该清" in _p876k
          # 旧的错措辞**必须已经不在**（只加新的不够：错的还留着 =
          # 半年后有人照着错的那句读）
          and "没了（与源站相反）" not in _p876k)
    check("CC.15 读数的**呈现**本身也会骗人：复刻侧两段都打印成 `焦点=''`"
          "（像「焦点丢了」），实际是 `DIV`/`text='音频 1'` = **正落在该音频"
          "节点本体**（886 定的落点）。根因：**源站**节点带 "
          "`aria-label='音频 node: 音频 N'` 而**复刻节点不带**，只印 aria "
          "就把「落对了」**显示成「没落」**。⇒ 焦点读数一律印 "
          "tag+aria+text 三样",
          "def focus_desc(" in _p876k
          and "aria={a!r}/text={t!r}" in _p876k
          and "读数的**呈现**本身也会骗人" in _p876k
          and "显示成「没落」" in _p876k)
    # ══════════ 批 889：Esc 落点从「两次读数」变成「一条规则」 ══════════
    p889 = ROOT / "scripts/jimeng_probe889_esclanding_src.py"
    p889b = ROOT / "scripts/jimeng_probe889b_esclanding2_src.py"
    p889c = ROOT / "scripts/jimeng_probe889c_blankvar_src.py"
    p889d = ROOT / "scripts/jimeng_probe889d_canvasfocus_src.py"
    p889ck = ROOT / "scripts/jimeng_probe889_esclanding_ck.py"
    p889bck = ROOT / "scripts/jimeng_probe889b_esclanding_ck.py"
    _p889 = p889.read_text(encoding="utf-8") if p889.exists() else ""
    _p889b = p889b.read_text(encoding="utf-8") if p889b.exists() else ""
    _p889c = p889c.read_text(encoding="utf-8") if p889c.exists() else ""
    _p889d = p889d.read_text(encoding="utf-8") if p889d.exists() else ""
    _p889ck = p889ck.read_text(encoding="utf-8") if p889ck.exists() else ""
    _p889bck = p889bck.read_text(encoding="utf-8") if p889bck.exists() else ""
    p_jws = ROOT / "src/components/jimeng/JimengWorkspace.tsx"
    _jws_raw = p_jws.read_text(encoding="utf-8") if p_jws.exists() else ""
    check("DD.1 889 把 Esc 落点**逐个前置态**测（chip / clear / nofocus / "
          "layer_open **四档都列全**，少一档就等于有一个没取样却看着像「都测过」），"
          "每档**重复 2 次**，而且**每次都把「按 Esc 之前的焦点」记进结果** —— "
          "888 漏掉的正是这一行，所以它的 `Canvas` 当时**无法与 885/887 比较**",
          bool(_p889) and "REPS = 2" in _p889
          and all(k in _p889 for k in ('"chip"', '"clear"', '"nofocus"',
                                      '"layer_open"'))
          and 'rec["focus_before"] = ev(FOCUS_JS)' in _p889
          and "**按 Esc 之前**的焦点读数" in _p889
          # 落点分类**钉身份**（in_audio_node）不钉 aria 字面量
          and "不许**用 aria 字符串相等" in _p889)
    check("DD.2 §99 第一版把 888 的 `Canvas` 写成「第四条 Esc 路径」是"
          "**没量就下的结论**（888 没记按 Esc 前焦点）—— 基线里那条必须写成"
          "**已查明**的规则「落点 = 按 Esc 前焦点在哪」，**不许**保留"
          "「第四条路径」这种把**两次读数不同**当「找到原因」的说法",
          '"esc_landing_rule"' in _ausrc
          and "落点由「按 Esc 之前焦点在哪」决定" in _ausrc
          and "不是「第四条路径」" in _ausrc
          and '"esc_landing_by_precondition"' in _ausrc
          and '"esc_landing_n"' in _ausrc)
    check("DD.3 889c **只隔离一个变量**（按 Esc 前那次 `blank()`）就把 888 的 "
          "`Canvas` 复现出来 2/2 ⇒ 差异的**成因**有实测支撑；⚠️ 而且它"
          "**不许**倒过来说「888 记错了」、**也不许**说那是 flake —— "
          "那两件都还没测，只能说「仍解释不了」就记账",
          "blank_then_center" in _p889c and "BLANK_JS" in _p889c
          and "倒过来说 888 记错了" in _p889c
          and "flake" in _p889c)
    check("DD.4 889b 在**层开着**这个前置态下**同一次运行**读值（2/2 "
          "值 `'男' → '男'` 保留）⇒ **874 那条读数在它自己的前置态里复核通过**，"
          "§98/§99 记的「没有同一次运行的证据」这条缺口**闭合**；"
          "而 887 的「层收着时被清」是**另一档**，两条**并存不冲突**",
          '"layer_open_esc_keeps_value"' in _ausrc
          and "874 那条「值保留」在它自己的前置态里复核通过" in _ausrc
          and '"value_survived"' in _p889b
          # 读不到必须记账，不许写成「值没了」（876c 栽过）
          and "「值还在不在」测不到" in _p889b
          and "**不是**「值没了」" in _p889b)
    check("DD.5 889d 把源站画布根容器钉死：`.react-flow` = `role='application'` "
          "+ `aria-label='Canvas'` + **`tabindex='0'`**，class 里有 "
          "`focus:outline-none`；且 **Tab 能不能到它是独立读数**，"
          "**不许**用「它有焦点」推出来",
          "role=application" in _p889d
          and "tabindex" in _p889d
          and "**独立**一条读数，不许用「它有焦点」推出来" in _p889d
          and '"canvas_root_is_focusable"' in _ausrc
          and "tabindex='0'" in _ausrc)
    check("DD.6 复刻 801 抄了画布根的 `role`/`aria` 却**漏了 `tabindex`** ⇒ "
          "复刻画布根不可聚焦、点空白时焦点掉到 `body`。889 已补（`hasAttribute` "
          "守卫，不踩 xyflow 哪天自己给的值），补后点空白 ⇒ 焦点 `'Canvas'` 2/2、"
          "「焦点在画布上按 Esc ⇒ 落 `Canvas` 原地不动」2/2，**与源站一致**，"
          "且 verifier 251/251 未被打破",
          'el.setAttribute("tabindex", "0")' in _jws_raw
          and "801 只抄了 role/aria，**漏了 tabindex**" in _jws_raw
          and 'if (!el.hasAttribute("tabindex"))' in _jws_raw
          and '"replica_canvas_root_tabindex_FIXED_889"' in _ausrc)
    check("DD.7 探针**没取**的属性**不许**出现在结论里 —— 889b_ck 第一版的 "
          "`FOCUSABLE_JS` **只取 `tabindex`**，我却据此写下「复刻 "
          "role=None/aria=None」（现场复核：复刻其实 `role='application'` + "
          "`aria='Canvas'`，**与源站一样**）。⇒ 该 JS 现在把 role/aria/"
          "testid 一并取回，且这条教训写在探针里",
          "role: e.getAttribute('role')" in _p889bck
          and "aria: e.getAttribute('aria-label')" in _p889bck
          and "testid: e.getAttribute('data-testid')" in _p889bck
          and "探针没取的属性，不许出现在结论里" in _p889bck
          # 程序化聚焦要指向**源站真正被聚焦的那个元素**（根容器，不是 pane）
          and "document.querySelector('.react-flow')" in _p889bck)
    check("DD.8 仍然存在的那条差异**如实留在基线里**（源站点空白后点节点**不**"
          "抢焦点、复刻**抢**；但源站不点空白直接点节点**会**到节点上 ⇒ "
          "「抢不抢」取决于之前有没有点过空白），**机制未验证**不许下结论 —— "
          "889 **不许**把它当「已治」",
          '"open_diff_node_click_takes_focus"' in _ausrc
          # ⚠️⚠️ 本条**第二版**（890 推进了事实，所以措辞跟着改）：
          # 第一版要求基线里写「机制**未验证**」，而 890 把机制**定位到一层**
          # 了，那句被改写 ⇒ 判据不跟着改就会永远红（CC.6 的教训：
          # **错判据不许悄悄改掉**，但**判据要跟上事实**）。
          # ⚠️ 改归改，**不许**顺势把「未验死」那条一起删掉 ——
          # 890 自己就把两条「仍未验证」留在了基线里。
          and "机制已定位到一层、但未钉死" in _ausrc
          and "仍然存在的差异" in _ausrc
          # ⚠️⚠️ 第四版（892 把「有没有 preventDefault」测掉了）：原锚点
          # 「**至今没测到**」已过时 ⇒ 换成 891/892 留下的**当前**那个未钉死的
          # 东西：那个**矛盾**。**判据要跟上事实**，但**不许**因为
          # 「preventDefault 已有答案」就把矛盾一起删掉。
          and "891 已把这条「浏览器规则」假设证伪" in _ausrc
          and "空白页**证不了**源站自己的行为" in _ausrc
          # ⚠️⚠️ 第五版（893 把矛盾**解开**了）：锚点从 `..._still_open` 换成
          # `..._RESOLVED_893` —— 基线里**不许**留一条「仍未解决」跟结论打架。
          # 判据要跟上事实，但**不许**因为矛盾解决了就把「为什么 tabindex 是
          # None **仍未查清**」一起删掉。
          and '"contradiction_891_vs_source_RESOLVED_893"' in _ausrc
          and "contradiction_891_vs_source_still_open" not in _ausrc
          and "**仍未查清**" in _ausrc
          and "不许**简化成「源站未选中节点一律不可聚焦」" in _ausrc)
    # ══════════ 批 890：DD.8 那条差异的机制，查到一层就**停** ══════════
    p890 = ROOT / "scripts/jimeng_probe890_nodefocus_why_src.py"
    p890b = ROOT / "scripts/jimeng_probe890b_nodefocus_why2_src.py"
    p890c = ROOT / "scripts/jimeng_probe890c_nodefocus_why_ck.py"
    _p890 = p890.read_text(encoding="utf-8") if p890.exists() else ""
    _p890b = p890b.read_text(encoding="utf-8") if p890b.exists() else ""
    _p890c = p890c.read_text(encoding="utf-8") if p890c.exists() else ""
    check("EE.1 890 那条 `defaultPrevented` 读数**作废**且**打了横幅**（不许把"
          "坏判据的读数悄悄留在库里当证据）：它挂在 `document` **捕获阶段**读，"
          "那一刻还没有任何 handler 跑过 ⇒ **恒真为假**。⚠️ 横幅还必须说清"
          "**890b 也没读到**（事件没冒泡到 document）⇒「源站有没有 "
          "preventDefault」**至今没测到**，890/890b 两边都不能用来下结论。"
          "同时列出**不依赖那条坏判据、仍然有效**的读数",
          "⛔⛔⛔" in _p890
          and "判定：本探针的 `defaultPrevented` 读数作废" in _p890
          and "**恒真为假**" in _p890
          and "890b 也没读到" in _p890
          and "**这个探针仍然有效的读数**" in _p890
          and "不许先有结论再找证据" in _p890)
    check("EE.2 890b 把判据**修到冒泡阶段**（而不是把坏判据的结果解释成"
          "「源站没 preventDefault」），并补上 890 缺的三样：`focus()` 的"
          "**目标身份**（含「当时已是焦点吗」）、`focusin` 目标的完整身份、"
          "以及**那个坐标点中的到底是谁**（落点常常不是 tabindex=0 的节点本身）",
          "890 的**判据缺陷**" in _p890b
          and "addEventListener('mousedown', w.onMdBubble, false)" in _p890b
          and "already_active" in _p890b
          and "那个坐标**落点是谁**" in _p890b
          and "HIT_JS" in _p890b)
    check("EE.3 890c 在复刻侧**逐字复用** 890b 的判据（不许两边各量各的 —— "
          "量出「不同」其实可能只是**判据不同**）；且诊断动作（劫持 "
          "`HTMLElement.prototype.focus`/`blur` + 事件监听）**每段都自己还原**"
          "，不许在产品页面上留痕（882 的规矩）",
          "判据逐字复用 890b 的 JS" in _p890c
          and "md_bubble" in _p890c and "在**冒泡阶段**读" in _p890c
          and all("RESTORE_JS" in s and "finally" in s
                  for s in (_p890, _p890b, _p890c)))
    check("EE.4 机制只查到**一层**就**停**：基线里写清「源站有一次应用主动 "
          "`focus()` 到画布根、复刻 `focus()` 次数是 0（纯浏览器原生）」，"
          "同时**两条未验证必须留着** —— ① 源站 mousedown 有没有 "
          "`preventDefault()`（**至今没测到**）②「浏览器为什么不移动」的"
          "确切规则**未验死**。⚠️ 那两句机制描述**不许**被当成因果证明",
          "复刻侧 JS 调 `focus()` 的次数是 0" in _ausrc
          and "纯浏览器原生" in _ausrc
          and "有没有被 `preventDefault()`" in _ausrc
          # ⚠️⚠️ 第三版（892 把这一格测掉了）：原锚点「**至今没测到**」已过时
          # ⇒ 改成「**892 已测掉：没有**」。**判据要跟上事实**，但
          # **不许**因此把 891 那条「**已证伪**」和 892 留下的
          # 「`cancelBubble` 不可信 / 那个矛盾仍未钉死」一起删掉。
          and "**892 已测掉：" in _ausrc
          and "891 已把这条「浏览器规则」假设证伪" in _ausrc
          # 「读不到不代表没有」这句**必须留着** —— 它是 890b→892 取法
          # 换代的理由，也是通用教训
          and "读不到不代表没有" in _ausrc
          and "这一步仍未测到" in _ausrc)
    check("EE.5 「点节点中心那个坐标落到了谁」只**说明落点是谁**，"
          "**不许**据此推出「所以焦点会/不会移动」—— 那一步**没测**"
          "（落点是不可聚焦后代：源站 `svg`/tabIndex=-1、复刻 `SPAN`/tabIndex=-1；"
          "而节点本身两边都是 `tabindex='0'`）",
          '"node_click_lands_on_nonfocusable_child"' in _ausrc
          and "**不许**据此推出" in _ausrc
          and "那一步**没测**" in _ausrc
          and "elementFromPoint" in _ausrc)
    # ══════════ 批 891：一条「看起来很合理」的规则，被最小复现证伪 ══════════
    p891 = ROOT / "scripts/jimeng_probe891_mousedown_rule_ck.py"
    _p891 = p891.read_text(encoding="utf-8") if p891.exists() else ""
    check("FF.1 891 用**最小复现**（空白页 `set_content`、**不跑源站**）把 §101 "
          "那条「mousedown 落点在当前焦点子树内 ⇒ 浏览器不移动焦点」"
          "**证伪**了 —— C1 格子（焦点在落点的可聚焦祖先上）**照样移动**。"
          "六格（基线 / 焦点在外面 / preventDefault / stopPropagation / "
          "祖先不可聚焦 / 落点自己可聚焦）**都列全**、每格 2 次",
          bool(_p891) and "REPS = 2" in _p891
          and all(f"C{i}_" in _p891 for i in (1, 2, 3, 4, 5, 6))
          and '"mousedown_focus_rule_refuted_891"' in _ausrc
          and "**证伪了**" in _ausrc
          and "这就是那条假设的直接反例" in _ausrc
          # 两条「是不是前提」也**排除**掉了，不许只说 C1
          and "不是前提" in _ausrc
          and "「祖先可聚焦」不是前提" in _ausrc
          and "「落点不可聚焦」不是前提" in _ausrc)
    check("FF.2 证伪**收窄**出当时的唯一候选：只有 **`preventDefault()`** 能阻止"
          "浏览器移动焦点（**`stopPropagation` 挡不住** —— 只停冒泡、"
          "**不**阻止默认）。"
          "⚠️⚠️ **本条第二版（892 推进了事实）**：891 写的「源站有没有 "
          "preventDefault **至今没测到**」**已被 892 测掉**（结论：**没**有）。"
          "**判据要跟上事实**，但**不许**因此把「`cancelBubble` 不能当 "
          "stopPropagation 的证据」那条一起删掉 —— 892 读到的是 "
          "`bubbles=True` 却**没冒泡到 document** 这一组拉扯读数，"
          "那一步**仍未测到**",
          "**只有 `preventDefault()` 能阻止浏览器移动焦点**" in _ausrc
          and "`stopPropagation` 挡不住" in _ausrc
          and '"src_site_preventdefault_still_unmeasured"' in _ausrc
          # 891 那格**已被取代**（保留是为了记录取法的演进）
          and "**已被 892 取代**" in _ausrc
          and "见 `src_site_preventdefault_False_892`" in _ausrc
          # ⚠️ 但 892 自己也留了一个「仍未测到」—— 不许跟着删
          and "这一步仍未测到" in _ausrc)
    check("FF.3 方法论：**「读数能这么解释」不等于「这条规则成立」** —— 一条"
          "机制假设要能被采信得满足两条：① 能解释**全部**相关读数；"
          "② **扛得住**一个专门为证伪它设计的**最小复现**。第 ② 条是新的，"
          "而且**在空白页上就能验**，不必每次回源站。"
          "⚠️ 反过来也要说清：空白页**证不了**源站自己的行为，"
          "它只否掉「这是浏览器规则」这类**通用**假设",
          '"mechanism_hypothesis_must_survive_minimal_repro"' in _ausrc
          and "**「读数能这么解释」不等于「这条规则成立」。**" in _ausrc
          and "扛得住" in _ausrc
          and "**验机制不必每次回源站**" in _ausrc
          and "空白页**证不了**源站自己的行为" in _ausrc)
    check("FF.4 最小复现本身守纪律：每格**重新 `set_content`**（互不污染）、"
          "**真鼠标事件**（`dispatchEvent` 的合成事件**不会**触发焦点默认行为）、"
          "落点**量出来**再点（`elementFromPoint`）、捕获与冒泡**两个阶段**"
          "都读 `defaultPrevented`（890 的教训：只在捕获阶段读**恒真为假**）",
          "每个格子**重新 set_content**" in _p891
          and "pg.mouse.click" in _p891
          and "合成事件**不会**触发焦点默认行为" in _p891
          and "落点**量出来**再点" in _p891
          and "elementFromPoint" in _p891
          and "onCap" in _p891 and "onBub" in _p891
          and "**恒真为假**" in _p891)
    check("FF.5 891 第一跑**炸在**自己写的代码上（数组名 `cap` 又被赋成 handler "
          "函数 ⇒ READ 回来是函数、序列化后 None ⇒ `for m in None`），"
          "这条**留痕**在探针里 —— 教训是「读数取不到时要认得出是**变量写重了**，"
          "别当成「浏览器没触发」」",
          "数组名与 handler 名**必须分开**" in _p891
          and "别当成" in _p891
          and "「浏览器没触发」" in _p891)
    # ══════════ 批 892：「唯一候选」被否掉 ⇒ 留下一个**矛盾** ══════════
    p892 = ROOT / "scripts/jimeng_probe892_preventdefault_src.py"
    _p892 = p892.read_text(encoding="utf-8") if p892.exists() else ""
    check("GG.1 892 用 891 写在基线里的那条取法测那**唯一候选**："
          "**捕获阶段只保存事件对象的引用**（不读值），等**派发结束**后再读 "
          "`defaultPrevented` —— 事件对象派发结束后仍保留**最终**值，"
          "所以**与 handler 跑没跑完无关**。结论：源站**没** preventDefault"
          "（A/B 各 2/2）⇒ 891 的候选**被否掉**",
          bool(_p892)
          and "w.onCap = (e) => { if (!w.saved) { w.saved = e;" in _p892
          and "等事件派发**彻底结束**再读" in _p892
          and '"src_site_preventdefault_False_892"' in _ausrc
          and "**没** preventDefault" in _ausrc
          and "被否掉了" in _ausrc)
    check("GG.2 `cancelBubble` **派发结束后会被重置** ⇒ 它**不能**当"
          "「有没有人调过 `stopPropagation()`」的证据。892 读到的是一组"
          "**互相拉扯**的读数（`bubbles=True` 但 document 冒泡收到 **0** 次），"
          "这一步**仍未测到**，**不许**拿 `cancelBubble=False` 当结论",
          '"cancelbubble_unreliable_after_dispatch"' in _ausrc
          and "**不能**用来证明" in _ausrc
          and "这一步仍未测到" in _ausrc
          and "**不许**拿 `cancelBubble=False` 当证据" in _ausrc)
    check("GG.3 **矛盾必须写下来**，不许硬凑一个解释：891 的 C1 说「浏览器"
          "**会**移动焦点」，而源站结构与 C1 **完全一样**却 `focusin` **0** 次，"
          "892 又证明源站**没**被 preventDefault ⇒ 「会移动」与「没移动且没被"
          "阻止」**不可能同时成立**。⇒ 说明源站在**那一刻**做了空白页复现里"
          "没有的事。净进展是**排除了两个候选**（浏览器规则、preventDefault）。"
          "⚠️⚠️ **本条第二版（893 已把它解开）**：锚点从 `..._still_open` 改成 "
          "`..._RESOLVED_893`，并要求基线里**不许**再出现旧名字 —— "
          "留一条「仍未解决」跟结论打架，比没有还糟。"
          "**不许**因为矛盾解开就把「为什么 tabindex 是 None **仍未查清**」删掉",
          '"contradiction_891_vs_source_RESOLVED_893"' in _ausrc
          and "contradiction_891_vs_source_still_open" not in _ausrc
          and "排除法的净进展：排除了两个" in _ausrc
          and "**仍未查清**" in _ausrc)
    check("GG.4 ⚠️ **本条第二版（893 把 §103 那条假设测出来了）**："
          "§103 猜的是「点击那一刻节点还没有 `tabindex`」⇒ **成立**。"
          "所以判据改成钉 **893 的实测读数**（不是钉那条假设的措辞 —— "
          "假设一旦被验死，钉它的措辞就会把判据锁死在过时状态）："
          "A 序列 mousedown 那一刻 `isConnected=False` + `tabIndexProp=-1` + "
          "`focusin` 0 次；B 序列 `tabIndexProp=0` + `focusin` 2 次。"
          "⚠️ 同时**不许**顺势把它推广成「源站未选中节点一律不可聚焦」。"
          "⚠️⚠️ **本条第三版（894 又推翻了它的另一半前提）**：893 当初说"
          "「与 889d 的 Tab 走查不一致、**未查清**」—— 894 查明那是"
          "**跨时刻读数混比**（889d 读的是**焦点落在节点的那一刻**），"
          "**根本不是矛盾**。而且 894 测出**选中的**新节点**也**是 `None`/`-1`"
          " ⇒ 判据改钉这两个事实",
          '"click_moment_node_not_focusable_893"' in _ausrc
          and "isConnected=False" in _ausrc
          and "tabIndexProp=-1" in _ausrc
          and '"source_node_tabindex_is_conditional_893"' in _ausrc
          # 894 的修正：不是矛盾，是跨时刻混比；且选中节点也是 -1
          and "跨时刻读数混比" in _ausrc
          and "**选中的新节点也是 " in _ausrc
          and "更**不许**据此改复刻的 `nodesFocusable`" in _ausrc)
    # ══════════ 批 893：矛盾解开（机制钉死） ══════════
    p893 = ROOT / "scripts/jimeng_probe893_clickmoment_src.py"
    _p893 = p893.read_text(encoding="utf-8") if p893.exists() else ""
    check("HH.1 893 的取证方式必须钉住：**捕获阶段只存引用**（落点 target、"
          "最近的节点、那一刻的 `tabindex`），值一律**派发结束后**再读"
          "（与 892 同款取法）；并在节点上挂 **`MutationObserver`** 记 "
          "`attributes`/`childList` 变化并带**相对 mousedown 的时间差**。"
          "⚠️ 诊断动作（监听 + observer）**不许留痕**",
          bool(_p893)
          and "w.onCap = (e) => {" in _p893
          and "w.savedTarget = e.target;" in _p893
          and "target_is_connected: t ? t.isConnected : null" in _p893
          and "new MutationObserver" in _p893
          and "dt: Date.now() - w.t0" in _p893
          and "finally:" in _p893 and "RESTORE_JS" in _p893)
    check("HH.2 893 的结论是**机制**、不是落点：A 序列（先点空白再点节点）"
          "mousedown 那一刻 **落点 target `isConnected=False`**、"
          "**节点 `tabindex=None` / `tabIndexProp=-1`**（不可聚焦）、"
          "`focusin` **0** 次；B 序列（直接点节点）**已经是** `tabIndexProp=0`、"
          "MutationObserver **0 条**、`focusin` **2** 次。"
          "⇒ 浏览器的默认动作「把焦点移到 target 的最近可聚焦祖先」"
          "**无处可移** —— 这**同时**满足 891 的 C1、892 的「没有 preventDefault」"
          "和源站的 `focusin=0`，三者不再冲突",
          '"click_moment_node_not_focusable_893"' in _ausrc
          and "isConnected=False" in _ausrc
          and "tabIndexProp=-1" in _ausrc
          and "**无处可移**" in _ausrc
          and "三者不再冲突" in _ausrc
          # ⚠️ `tabindex` 是**事后**才有的，不许写成「源站节点没有 tabindex」
          and "别写成「源站节点没有 tabindex」" in _ausrc)
    check("HH.3 ⚠️⚠️ **本条第二版（894 推翻了它的前提）**：893 撞出的"
          "「不一致」是**跨时刻读数混比** —— 889d 是在**焦点落在节点的那一刻**"
          "读的 `tabindex`，894 读的是**中性状态**，两者**本来就不该比**。"
          "⇒ 894 实测（矩阵，每种条件 2 轮）：`fresh_load`（刚载完什么都不做）"
          "与 `after_blank`（点空白）下，**所有类型**节点"
          "**全都是 `tabindex=None` / `tabIndexProp=-1`**；"
          "**选中**的新节点**也**是 `None`/`-1`。"
          "⇒ 判据必须钉这个**新事实**，并**禁止**把它简化成"
          "「源站未选中节点一律不可聚焦」",
          '"source_node_tabindex_is_conditional_893"' in _ausrc
          and "**894 推翻了本条的第一版" in _ausrc
          and "跨时刻读数混比" in _ausrc
          and "本来就不该放在一起比" in _ausrc
          and "**全都是 `tabindex=None` / `tabIndexProp=-1`**" in _ausrc
          and "**选中的新节点也是 " in _ausrc
          and "不许**写成「源站未选中节点一律不可聚焦」" in _ausrc)
    check("HH.4 由此得到的**产品差异**要写进基线（源站中性态节点**不可 Tab "
          "到达** vs 复刻 `nodesFocusable` 默认 true ⇒ **任何时候**可达），"
          "同时**必须钉住两条不许**：① **不许**照着「中性态 -1」硬设"
          "（会把 Tab 走查整个改掉，§77）；② 更**不许**据此改复刻的 "
          "`nodesFocusable`（那是**整个画布 Tab 顺序**的改动）。"
          "⚠️⚠️ **本条第三版（901 已经改了）**：894 的理由是「策略未测」"
          "（896 测出来了）、898 又把它收窄成「**错的单方**方案」"
          "（`{false}` 是配对方案的**前半段**）—— **901 照着这个配对方案"
          "真的改了**，并带自己的验证。所以「**先别改**」那条**只作历史记录**，"
          "⚠️ **不许**拿它去阻止后续按**已测规则**做的改动。"
          "⇒ 但「**只钉前半段就宣称已对齐**」仍然不许",
          '"source_nodes_not_tabreachable_in_neutral_state_894"' in _ausrc
          and "不可 Tab 到达" in _ausrc
          and "更**不许**据此改复刻的 `nodesFocusable`" in _ausrc
          and "整个画布 Tab 顺序" in _ausrc
          # ⚠️ 反向：旧措辞（未测/覆盖不全）都已被事实取代
          and "而源站那个动态策略的**确切规则未测**" not in _ausrc
          and "**复刻侧类型覆盖仍不全**" not in _ausrc
          # ⚠️ 但「先别改」必须**以历史记录的身份**留着
          and "「**先别改**」**曾经**成立过" in _ausrc
          and "**只作历史记录**" in _ausrc
          and "replica_roving_implemented_901" in _ausrc)
    # ══════════ 批 895：复刻侧那张表（差异两侧都有据） ══════════
    p895 = ROOT / "scripts/jimeng_probe895_node_tabindex_matrix_ck.py"
    p894 = ROOT / "scripts/jimeng_probe894_node_tabindex_matrix_src.py"
    _p895 = p895.read_text(encoding="utf-8") if p895.exists() else ""
    _p894 = p894.read_text(encoding="utf-8") if p894.exists() else ""
    check("JJ.1 895 的判据必须**逐字复用** 894（`NODES_JS` / `BLANK_JS` / "
          "`FOCUS_JS` / `summarize` 四段都要能在 894 里**原样找到**）—— "
          "否则量出「不同」可能只是**两边各量各的**（890c 栽过一次，已记基线）。"
          "⚠️ 空白点若用了 894 同一组候选坐标**落空**而回落到 pane 矩形角，"
          "**必须记录用的是哪一种**（坐标不同是次要变量，但必须可追溯）",
          bool(_p895) and bool(_p894)
          and all(block in _p894 for block in (
              'NODES_JS = """', 'BLANK_JS = """', 'FOCUS_JS = """',
              "def summarize("))
          and all(block in _p895 for block in (
              'NODES_JS = """', 'BLANK_JS = """', 'FOCUS_JS = """',
              "def summarize("))
          and "逐字来自 894 源站探针" in _p895
          and "blank_from" in _p895 and "pane_rect" in _p895)
    check("JJ.2 895 的结论是**量出来的**，不是从库默认值**推**的：复刻侧所有"
          "条件、所有状态的节点 **`tabindex='0'` 恒定**（各 2 轮两轮一致）"
          "⚠️⚠️ **本条第二版（901 已把复刻改成 roving）**：这条量的是"
          "**901 之前**的复刻。**不许**拿它论证「复刻现在恒 `'0'`」—— "
          "**不成立了**；也**不许回头删掉**它（那是当时**真实测出来**的、"
          "也是「为什么值得改」的依据）",
          '"replica_node_always_focusable"' in _ausrc
          and "**895 的原测量**" in _ausrc
          and "**本条已被 901 作废" in _ausrc
          and "**只作历史记录**" in _ausrc
          and "replica_roving_implemented_901" in _ausrc)
    check("JJ.3 ⚠️ 复刻这一侧的「所有类型」**在 895 当时没测全**（demo 只有 "
          "2 video **加**探针插入的 1 audio，源站矩阵里还有 "
          "text / timeline / image / external）⚠️⚠️ **本条第二版**："
          "那个缺口**已由 897 补齐**，而 897 的读数**又被 901 改掉**了。"
          "⇒ **三代状态各自留痕**：895（恒 `'0'`、覆盖不全）→ 897"
          "（恒 `'0'`、7 种全测）→ 901（**中性态无属性**、7 种全测）。"
          "⚠️ **不许**只留最新一代而抹掉前两代",
          "**在 895 当时没测全**" in _ausrc
          and "**已由 897 补齐**" in _ausrc
          and "**又被 901 改掉**" in _ausrc
          and "**三代状态各自留痕**" in _ausrc)
    check("JJ.4 895 自己踩的坑必须留痕：判据平移时把 Playwright 的 "
          "`wait_for_timeout(140)`（**毫秒**）写成 Python 的 `time.sleep(140)`"
          "（**秒**）⇒ 一次循环睡 140 秒、16 次 ≈ **37 分钟**；现象是进程 "
          "**0% CPU 一直睡**，**看起来像「复刻页面按 Tab 卡死」**。"
          "⇒ 教训两条：判据平移**连单位一起平移**；「0% CPU 一直睡」是"
          "**挂住**的信号、不是「慢」，而**挂住**第一嫌疑是**自己的代码**、"
          "不是被测对象",
          "**单位**" in _p895
          and "wait_for_timeout" in _p895
          and "time.sleep(140)" in _p895
          and "37 分钟" in _p895
          and "0% CPU" in _p895
          and "判据平移必须连单位一起平移" in _p895)
    # ══════════ 批 896：roving 策略测出来了（含「开关选错比不改更糟」） ══════════
    p896 = ROOT / "scripts/jimeng_probe896_roving_tabindex_policy_src.py"
    _p896 = p896.read_text(encoding="utf-8") if p896.exists() else ""
    check("KK.1 896 的取证方式必须钉住：仪器 = `MutationObserver(attributes, "
          "attributeOldValue, attributeFilter:['tabindex'], subtree)` 挂在 "
          "`.react-flow` 上、**任何交互之前**就挂（否则读不到第一次 Tab 之前"
          "发生了什么），**外加** `focusin`/`focusout`/`keydown` 监听往**同一个**"
          "有序日志里记。⚠️ `defaultPrevented` 必须用 892 的取法（**捕获阶段存引用、"
          "派发结束后再读**）；⚠️ 诊断动作**必须还原**（`finally` 里 "
          "`disconnect()` + 摘监听）；⚠️ 这一批**刻意不劫持 prototype**",
          bool(_p896)
          and "attributeOldValue: true" in _p896
          and "attributeFilter: ['tabindex']" in _p896
          and "subtree: true" in _p896
          and "任何交互之前" in _p896
          and "mo.disconnect()" in _p896
          and "finally:" in _p896
          and "不劫持 prototype" in _p896
          # 892 的取法要**两样都在**：文档写了 + 代码**真的**存了引用
          and "捕获阶段只存事件对象的引用" in _p896
          and "ref: e" in _p896
          and "派发结束" in _p896)
    check("KK.2 策略必须以**实测读数**写进基线（不是钉假设措辞）：中性态"
          "**根本没有 `tabindex` 属性**（`getAttribute`→`None`，`el.tabIndex` "
          "属性读 DOM 默认 `-1`）；**唯一**触发是 Tab/Shift+Tab 的 **keydown**，"
          "按下后**先**给目标写 `'0'`、**再**给**其余每个**写 `'-1'`（全画布"
          "重写）；**不** preventDefault（焦点移动是浏览器原生的）；"
          "**先布 0 再移焦点**（`focusin` **捕获阶段**已读到 `'0'`）；"
          "**此后不回撤**（点空白后那个 `0` 仍留在最后 rove 过的节点上）；"
          "**选中不布 `0`**",
          '"source_roving_tabindex_policy_896"' in _ausrc
          and "中性态：所有节点根本没有 `tabindex` 属性" in _ausrc
          and "布 `0` 的触发只有 Tab / Shift+Tab 的 `keydown`" in _ausrc
          and "不 preventDefault" in _ausrc
          and "先布 `0`、再移焦点" in _ausrc
          and "**不**回撤" in _ausrc
          and "**选中不布 `0`**" in _ausrc
          and "按 Tab 才把画布装进 Tab 序列" in _ausrc)
    check("KK.3 ⚠️⚠️ 896 钉出来、**898 又更正过**的一条：`nodesFocusable="
          "{false}` **单独上线**是错的 —— 它让节点**永远**不在 Tab 序列里 ⇒ "
          "画布**再也 Tab 不到**。⚠️⚠️ 但**898 已把 896 那句「错的杠杆」"
          "收窄成「错的**单方**方案」**：源站的机制**本身就是**"
          "「库不接管 `tabindex` + 应用自己 keydown 布」⇒ **`{false}` 正是"
          "忠实实现的**前半段**，配后半段（布 `0`/`-1` 且**不** preventDefault）"
          "才成立。⚠️ **不许**把这条读成「这个开关不许碰」—— 那会否掉正确的"
          "前半段；**也不许**只钉前半段就宣称「已对齐源站」",
          "错的**单方**方案" in _ausrc
          and "再也 Tab 不到" in _ausrc
          and "**绝不许单独上线**" in _ausrc
          and "**`{false}` 正是它的前半段**" in _ausrc
          and "**不许**把这条读成「这个开关不许碰」" in _ausrc
          and "keydown 布 0/-1 且**不** preventDefault" in _ausrc
          # ⚠️ 反向：894 那条**不许**还留着「策略未测」的旧措辞
          and "而源站那个动态策略的**确切规则未测**" not in _ausrc)
    check("KK.5 ✅ **897 补齐了复刻侧的类型覆盖**（7 种类型：文本/图片/时间线/"
          "主体/导演台 ＋ demo 自带的 video ＋ 895 插的 audio，各 2/2）。"
          "⚠️⚠️ **本条第二版（901 改了状态）**：897 的读数是**恒 `'0'`**，"
          "**901 之后**是**中性态无属性**。⇒ **三代状态各自留痕**"
          "（895 恒 `'0'`/覆盖不全 → 897 恒 `'0'`/7 种全测 → 901 中性态无属性/"
          "7 种全测），⚠️ **不许**只留最新一代而抹掉前两代。"
          "⚠️ 且 897 当时那条**诚实记账**继续有效：左栏 `insertAtCenter` 把"
          "新节点**全叠在画布中心** ⇒ 4 种类型的「点本体」读数**没取到**，"
          "探针**跳过**而**没有猜**；901 的探针改成**插一个、量一个**才补上",
          '"replica_type_coverage_closed_897"' in _ausrc
          and "**7 种类型全部覆盖**" in _ausrc
          and "n_zero == n_nodes" in _ausrc
          and "**901 已把这个状态改掉**" in _ausrc
          and "**4 种类型的「点本体」读数没取到**" in _ausrc
          and "**没有**把那 4 个读数**猜**出来" in _ausrc
          and "**插一个、量一个、再插下一个**" in _ausrc
          and "**两侧类型集不对称**" in _ausrc)
    check("LL.1 ⚠️⚠️ **898 那条的前提已被 901 改掉** —— 它量的是"
          "**901 之前**的复刻（那时 wrapper **恒** `tabindex='0'`、**一直**"
          "在 Tab 序列里）。**901 之后**：中性态 wrapper **没有** `tabindex`、"
          "**不在**序列里，**第一次按 Tab 才被装进去**。"
          "⇒ 判据必须钉**这个前提已被改掉**这件事，"
          "**不许**让基线里那条「wrapper 一直在序列里」和实现打架。",
          '"replica_wrapper_is_in_tab_sequence_898"' in _ausrc
          and "**本条的前提已被 901 改掉**" in _ausrc
          and "**不在**序列里" in _ausrc
          and "**第一次按 Tab 才被装进去**" in _ausrc
          and "replica_roving_implemented_901" in _ausrc
          # 898 的原测量仍要留着（它是「为什么值得改」的依据）
          and "wrapper 下标 = [1, 7]" in _ausrc
          and "**24/24 全 False**" in _ausrc
          and "**「走查没走到」≠「走不到」**" in _ausrc)
    check("LL.2 ⚠️ 898 留的那条教训**依然有效**、且是它最有价值的部分："
          "第一版 12 步走查 24/24 全 False 看着像「wrapper Tab 不到」，"
          "**那是取样假象**（起点在最后一个节点内部）⇒ **「走查没走到」≠"
          "「走不到」**。⚠️ 而 897 当时写下的「**不许**据此下结论」"
          "**正好**挡住了这个坑 ⇒ 判据里「**禁止过度概括**」是**真在起作用的**。",
          "**走查没不到**" not in _ausrc
          and "**24/24 全 False**" in _ausrc
          and "**那是取样假象**" in _ausrc
          and "**直接读序列**" in _ausrc
          and "**从画布外起走**" in _ausrc
          and "**正好**挡住了这个坑" in _ausrc)
    check("LL.3 ⚠️ 898 钉的两条**不许**继续有效：① **不许**把差异概括成"
          "「**复刻的节点 Tab 不到**」（那是**错的** —— 源站和复刻**都能**"
          "用 Tab 走到节点 wrapper，901 之后也一样）；② 判据**不许**只写"
          "「wrapper 在不在序列」而不写**它是在哪个状态下**"
          "（901 证明了：**中性态不在、按 Tab 才在**）",
          "**复刻的节点 Tab 不到**" in _ausrc
          and "**源站和复刻都能用 Tab 走到节点 wrapper**" in _ausrc
          and "**第一次按 Tab 才被装进去**" in _ausrc)
    check("LL.4 898 顺带修正的那条**不许**继续有效：`timeline`/`subject` 的"
          "**几何中心正好是一个内层 BUTTON** ⇒ 点中心落点是那个按钮。"
          "⚠️ **不许**把它读成「这两种节点不可聚焦」—— 它们照样在序列里、"
          "Tab 也照样能到（走查② 第 10 步就落在 timeline 的 wrapper 上）",
          "**几何中心正好是一个内层 BUTTON**" in _ausrc
          and "**不是**「这两种节点不可聚焦」" in _ausrc
          and "Tab 也照样能到" in _ausrc)
    # ══════════ 批 901：实现 roving（配对方案，不许只上前半段） ══════════
    _wsrc = (ROOT / "src/components/jimeng/JimengWorkspace.tsx").read_text(
        encoding="utf-8")
    p901 = ROOT / "scripts/jimeng_probe901_roving_impl_ck.py"
    _p901 = p901.read_text(encoding="utf-8") if p901.exists() else ""
    check("OO.1 901 的实现必须是**配对**的：`<ReactFlow nodesFocusable={false}>`"
          "（中性态**无 `tabindex` 属性**）**＋** 模块级 `armRovingTabindex`"
          "（keydown **捕获阶段**布 `'0'`/`'-1'`）。⚠️⚠️ **只上前半段"
          "**绝不许单独上线** —— 898 已证明单上它画布**再也 Tab 不到**。"
          "⇒ 判据要钉**源码里真实存在**这两处，不许只在注释里写",
          "nodesFocusable={false}" in _wsrc
          and "function armRovingTabindex(" in _wsrc
          and 'addEventListener("keydown", onKeyDown, true)' in _wsrc
          and "**绝不许单独上线**" in _ausrc
          and "**配对方案的前半段**" in _ausrc
          and "replica_roving_implemented_901" in _ausrc)
    check("OO.2 ⚠️ `armRovingTabindex` 里**不许** `preventDefault()`：源站 "
          "`defaultPrevented` **全 False**（896③/899 各 2/2）⇒ 焦点移动是"
          "**浏览器原生**的，本函数只负责「先把目标装进 Tab 序列」。"
          "⚠️ 也**不许**加 `% len` 那套**绕回**：899② 实测源站"
          "**到末尾就撒手、绝不绕回**。⇒ 判据直接查**函数体里没有** "
          "`preventDefault`（查源码，不查注释）",
          "preventDefault" not in _wsrc.split("function armRovingTabindex")[1]
              .split("\n}")[0]
          and "**不** `preventDefault()`" in _ausrc
          and "**没有** `% len` 那套循环" in _ausrc
          and "**撒手**、**不绕回**" in _ausrc)
    check("OO.3 验收判据必须**逐字复用源站探针**（896/899/900 的 `STATE_JS` / "
          "`INSTALL_JS` / `BLANK_JS` / `DOM_ORDER_JS`）—— 改写成「复刻版」"
          "就等于**两边各量各的**（890c 的教训）。复刻侧**各 2/2** 逐条对上"
          "源站**七条**：中性态无属性 / `n_zero` 恒 1 且直方图 "
          "`{'0':1,'-1':n-1}` / 不 preventDefault / 先布 `'0'` 再移焦点 / "
          "布 `'0'` 下标 = `[0..n-1]`（**纯 DOM 序**）/ 走到最后一个后**再无**"
          "布 `'0'`（**撒手不绕回**）/ 点空白后那个 `'0'` **仍在**",
          '"replica_roving_implemented_901"' in _ausrc
          and "**逐条对上了源站的七条**" in _ausrc
          and "**纯 DOM 序**" in _ausrc
          and "**撒手**、**不绕回**" in _ausrc
          and "**此后不回撤**" in _ausrc
          and "逐字复用" in _p901
          and "OVERRUN = 20" in _p901
          and "**没走到最后一个**" in _p901)
    check("OO.4 ⚠️ 两条**如实记账**的差异/缺口**不许**抹掉：① 源站那 2 个"
          "「整轮没被布 `'0'`」的例外**复刻没有**（复刻按**纯 DOM 序**）"
          "⇒ **刻意保留**这个不一致，**不许编 DOM 层判据去凑**；"
          "② **`Shift+Tab` 且焦点不在任何节点上**时本实现**什么都不做**，"
          "而**源站这个组合没测过** ⇒ 按 §77「源站没测到的行为不实现、"
          "不伪称可用」⇒ 这里**不猜**。⚠️ 另钉 **901 自己的坑**：第一版 "
          "`OVERRUN=6` **不够**（走查被节点**内层控件**吃掉按压，只推到下标 5 / "
          "DOM 共 7 个）⇒ **「到末尾撒手」那一问本轮不成立**，"
          "**差点**拿没测到的数据下结论",
          "**刻意保留**" in _ausrc
          and "**不许编 DOM 层判据去抹平**" in _ausrc
          and "源站没测到的行为不实现、不伪称可用" in _ausrc
          and "这里**不猜**" in _ausrc
          and "`OVERRUN=6` **不够**" in _ausrc
          and "**差点**拿没测到的数据下结论" in _ausrc)
    # ══════════ 批 899：「算下一个」的规则 ══════════
    p899 = ROOT / "scripts/jimeng_probe899_roving_next_rule_src.py"
    _p899 = p899.read_text(encoding="utf-8") if p899.exists() else ""
    # ══════════ 批 902：把 901 拒绝猜的那两格测掉 ══════════
    p902 = ROOT / "scripts/jimeng_probe902_unmeasured_cells_src.py"
    _p902 = p902.read_text(encoding="utf-8") if p902.exists() else ""
    check("PP.1 ✅ **902 把 901 明确拒绝猜的那一格测掉了**（各 2/2）："
          "点空白（焦点在画布根、**不在任何节点上**）后连按 5 次 `Shift+Tab` ⇒ "
          "`n_zero` 逐次 **`[0,0,0,0,0]`**、布 `'0'` 次数 **0**、"
          "`defaultPrevented` 全 `False`，焦点**按浏览器原生顺序往回走出画布**。"
          "⇒ **与 901 那个「什么都不做」的分支一致**。"
          "⚠️ 判据要钉死这句：**是测出来的、不是「猜对了」** —— 901 当时按 §77 "
          "选了「不猜」，902 只是**证明**这个选择与源站相符",
          '"source_shift_tab_from_non_node_902"' in _ausrc
          and "`[0, 0, 0, 0, 0]`" in _ausrc
          and "**一次都没布**" in _ausrc
          and "**不是**「猜对了」" in _ausrc
          and "BLANK_STEP = 5" in _p902)
    check("PP.2 ✅ 902 的格 B **答上来的一半**：往回走布 `'0'` 的下标**递减**"
          "（`[74,73,…,68, 63,…,58]`）⇒ **反向也是 DOM 序**；"
          "且**离开画布再回来，那个 `'0'` 也没被清掉**"
          "（`n_zero` 仍 1、仍挂在下标 58）⇒ **896⑤「此后不回撤」连往返都成立**。"
          "⚠️ 顺带又看到一次**跳过**（67–64），与 900 正向跳过的是**同一类现象**",
          '"source_roving_pointer_carries_state_902"' in _ausrc
          and "**反向也是 DOM 序**" in _ausrc
          and "连往返都成立" in _ausrc
          and "**跳过 67–64**" in _ausrc
          and "同一类现象" in _ausrc
          and "BACK_OUT = 30" in _p902)
    check("PP.3 ⚠️⚠️⚠️ **903 做了四条对照、把 PP.3 的结论推翻了一半**"
          "（各 2/2）：`A` 干净基线 / `B` 中途点空白（没到末尾）/ "
          "`C` 指针**到末尾**（没走出画布）/ `D` 两件都加（**就是 902 那条"
          "序列**）⇒ **8/8 全部 `[0,1,2]`**。⚠️ 但**不许宣布「902 作废」**"
          "—— 两次跑的往回走**停在 58 vs 59**（都 2/2 一致）⇒ "
          "**两个读数都真实**，「从 0 开始」**不是无条件的**，"
          "触发条件**仍未查明**。⇒ 对复刻：901 的「从头布」分支 **8/8 相符**、"
          "**不再是「已知差异」**；⚠️ 但**不许**据此改实现",
          "**903 做了四条对照、把本条的一半结论推翻了" in _ausrc
          and "**8/8 全部 `[0,1,2]`**" in _ausrc
          and "**不能宣布「902 是错的」**" in _ausrc
          and "**停在 58 vs 59**" in _ausrc
          and "**两个都是真实读数**" in _ausrc
          and "触发条件**仍未查明**" in _ausrc
          and "**不再是「已知差异」**" in _ausrc)
    # ══════════ 批 903：四条对照（推翻自己上一批的一半） ══════════
    p903 = ROOT / "scripts/jimeng_probe903_carried_state_src.py"
    _p903 = p903.read_text(encoding="utf-8") if p903.exists() else ""
    check("QQ.1 903 的设计是**四条对照、每条只动一个变量**（源站，各 2/2）："
          "`A` 干净基线 / `B` 只加「中途点空白」/ `C` 只加「指针到末尾」/ "
          "`D` 两件都加（**复现 902 那格**）。⇒ **8/8 全部 `[0,1,2]`**。"
          "⚠️ 判据要钉住**这个设计**（单变量对照），不然下一个人又会"
          "把「两件事同时发生」当成一件事来解释",
          '"A" 干净基线' not in _ausrc   # 基线里不写代号，只写结论
          and "**8/8 全部 `[0,1,2]`**" in _ausrc
          and "**四条对照**" in _p903
          and 'rec["arms"]' in _p903
          and 'for code in ("A", "B", "C", "D")' in _p903)
    check("QQ.2 ⚠️ **903 推翻 902 之后，必须把「怎么被推翻的」一起钉住**，"
          "不然下一次还会滑回同一个坑：两次跑的**往回走停在 58 vs 59**"
          "（都 2/2 一致）⇒ **两个读数都真实**。"
          "⚠️ **不许**宣布「902 是错的/随机的」，**也不许**把 `[2,3]` "
          "当常态规则 —— 正确说法是「**从 0 开始不是无条件的**，"
          "触发条件**仍未查明**」",
          "**不能宣布「902 是错的」**" in _ausrc
          and "**停在 58 vs 59**" in _ausrc
          and "**也不许宣布它是作废/随机的**" in _ausrc
          and "**不许**把 `[2,3]` 当常态规则" in _ausrc
          and "**「回来后从 0 开始」不是无条件的**" in _ausrc)
    # ══════════ 批 904：排除一条假设 + 把变量挪走（机制仍未查明） ══════════
    p904 = ROOT / "scripts/jimeng_probe904_endpoint_condition_src.py"
    _p904 = p904.read_text(encoding="utf-8") if p904.exists() else ""
    check("RR.1 904 的设计是**扫两个变量**、不是只扫一个："
          "① 进场前先按几次 `Shift+Tab`（`pre` ∈{0,5}）；"
          "② 往回按几次（`k` ∈{28,30,32}）。仪器**逐字复用** 900。"
          "⚠️ 判据要钉住**这个设计** —— 902 与 903 的 `k` 相同却落在 58/59，"
          "**光扫 `k` 根本不可能定位**",
          "ARMS = [" in _p904
          and "jimeng_probe904_endpoint_condition_src.py" in _ausrc
          and "**扫两个变量**" in _ausrc
          and '{"label": "shift5-k30", "pre": 5, "k": 30},' in _p904
          and '{"label": "base-k32",   "pre": 0, "k": 32},' in _p904)
    check("RR.2 904 **排除掉了一条候选假设**、并把变量挪到了别处 —— "
          "① 902 的 `[2,3]` 在 `pre=0` 的干净臂里**复现**了 ⇒ "
          "「开头 5 次 `Shift+Tab` 才是触发条件」**被排除**；"
          "② 终点是 `k` 的**严格线性函数**；③ **回来后布的下标与终点无关** "
          "⇒ **落点条件不在终点上**；④ 回来后第一次布的下标是 **0/1/2/12**、"
          "**4 臂里只有 1 臂从 0 开始** ⇒ **「从 0 开始」确实不是无条件成立**"
          "（903 那 8/8 里的 `[0,1,2]` **只是其中一种**）",
          "**① 902 的 `[2,3]` 复现了，而且是在 `pre=0` 的干净臂里**" in _ausrc
          and "才是触发条件」这个假设被排除**" in _ausrc
          and "`endpoint = 88 − k`" in _ausrc
          and "**③ 回来后布的下标与终点无关**" in _ausrc
          and "**落点条件不在终点上**" in _ausrc
          and "**④ 回来后第一次布的下标不稳定**" in _ausrc
          and "**4 臂里只有 1 臂从 0 开始**" in _ausrc
          and "**「从 0 开始」确实不是无条件成立**" in _ausrc
          and "903 那 8/8 里的 `[0,1,2]` **只是其中一种**" in _ausrc)
    check("RR.3 ⚠️ 904 必须把**没查清的**和**探针自身的缺陷**一起钉住，"
          "不然下一次会拿「没测到」当「没有」：① 那个起点（0/1/2/12）"
          "**成因仍未查明**（本轮**没逐次记按压时的焦点落点** = **取样缺口**、"
          "**不是**「测出来没有」）；② **不许**宣布 903 的 59 是错的；"
          "③ 4 条臂**臂间不 reload** ⇒ 记的「入场状态」其实**是上一臂的尾巴**、"
          "**不是独立变量**；④ `back_armed_count` **不能当步数用**；"
          "⑤ 触发条件未查明 ⇒ **仍然不许改实现**",
          "机制本身**仍未查明**" in _ausrc
          and "**取样缺口**" in _ausrc
          and "**仍然不许**宣布 903 的 59 是错的" in _ausrc
          and "「入场状态」其实**是上一臂的尾巴**" in _ausrc
          and "**「入场状态」不是独立变量**" in _ausrc
          and "**不能当步数用**" in _ausrc
          and "**触发条件未查明 ⇒ 仍然不许改实现**" in _ausrc
          # 探针**只输出读数**、不判机制（判读留在基线里）
          and 'out["verdict"] = "sampled"' in _p904
          and "探针**只输出读数**，判读留给基线" in _p904)
    # ══════════ 批 905：补上取样缺口 + 干净的单变量阶梯 ══════════
    p905 = ROOT / "scripts/jimeng_probe905_reentry_focus_src.py"
    _p905 = p905.read_text(encoding="utf-8") if p905.exists() else ""
    check("SS.1 905 必须**逐次记按压时的焦点落点** —— 这是 904 **明确点名**的"
          "取样缺口（904 的 `press()` 只抽了 `armed` 与 `prevented`）。"
          "⚠️ 判据要钉住**记三样**：布了什么下标 / 焦点落到哪个 `aria` / "
          "焦点落点带不带 `react-flow__node` 类",
          '"focus_aria": [f["target_aria"] for f in fi],' in _p905
          and '"focus_is_node": [f["target_is_node_wrapper"] for f in fi],' in _p905
          and '"after_per_press"' in _p905
          and "**按压时的焦点落点**" in _ausrc
          and "**取样缺口**" in _ausrc)
    check("SS.2 ✅ 905 **补上了那个缺口**，并**逐次证实了 900 规则**"
          "（源站，3 臂 × 2 轮 = 6 次，**8 步轨迹完全一致**）："
          "回来后布的下标 = `[0,1,2,3]` 然后**连续 4 次不布**；"
          "而那 4 次**逐次对得上「按压时焦点停在内层控件上」** ⇒ "
          "**「焦点不在节点本体上就不布」得到逐次证实**；"
          "且**布与落点严格错开一位** ⇒ **896④「先布 0 再移焦点」再获证据**。"
          "⚠️ 由此钉死一条不许：**不许**把「这一次布了什么」与"
          "「这一次焦点落在哪」当成同一件事读",
          "**① 回来后 8 次按压的轨迹完全确定**" in _ausrc
          and "`[0,1,2,3]` 然后连续 4 次不布**" in _ausrc
          and "**② 那 4 次「不布」逐次对得上「按压时焦点停在内层控件上」**" in _ausrc
          and "在回来后这一段得到逐次证实**" in _ausrc
          and "**③ 布与落点严格错开一位**" in _ausrc
          and "**正是 896④「先布 `'0'`、再移焦点」**" in _ausrc
          and "**不许**把「这一次布了什么」和「这一次焦点落在哪」" in _ausrc)
    check("SS.3 ✅ 905 的**单变量阶梯必须是臂间 reload 的**（904 最大的缺陷就是"
          "臂间不 reload ⇒ 「入场状态」其实是上一臂的尾巴）："
          "`L0` 从未 Tab / `L1` 只走到末尾 / `L2` 末尾＋回走 30 ⇒ "
          "**三条臂的回来后轨迹完全相同** ⇒ **「走到末尾」和「回走」都不影响"
          "回来后从哪开始** ⇒ 以**强得多的对照复核 904③**。"
          "⚠️ 判据要钉住**臂间 reload** 这个设计，不然下一次又会用"
          "「上一臂的尾巴」当独立变量",
          '{"label": "L0-never-tabbed", "walk_end": False, "back": 0},' in _p905
          and '{"label": "L2-to-end-back30", "walk_end": True,  "back": K_BACK},' in _p905
          # 每臂之间必须真的 reload
          and "⚠️ **每臂之间 reload**（904 的最大缺陷：入场状态是上一臂的尾巴）" in _p905
          and "**④ 单变量阶梯（臂间 reload ⇒ 入场状态干净）**" in _ausrc
          # ⚠️ 906 已把 905④ 改写成**带撤回标记**的版本 ⇒ 锚点跟着事实走，
          #    但**撤回标记本身也要被钉住**（不许有人把 ③/④ 悄悄删干净）
          and "**但 906 已把本条**后面那半句推论**判为无效**" in _ausrc
          and "推不出「与终点无关」**" in _ausrc)
    check("SS.4 ⚠️⚠️ **905 自己撞出了一个与 904 矛盾的地方，必须钉住、"
          "不许抹平**：905 的 `L2`（终点 59）⇒ `[0,1,2,3]`；"
          "904 的 `base-k30`（终点 58）⇒ `[2,3]` ⇒ **名义上相同的序列、"
          "不同结果** ⇒ 有一个**两批都没控住的变量，未查明**。"
          "⚠️ 由此钉死三条不许：**不许**宣布 904 作废、**不许**宣布 905 是"
          "「干净的那次」、那个 58 vs 59 本身也仍未查清。"
          "另两条**机制未验**的读数也要记：首次 `Tab` 从画布根**会**布 `'0'`"
          "而 902 的 `Shift+Tab` **一次都不布**（**方向不对称**）；"
          "「第 9 次会布 4」是**预测、没测** ⇒ 不许当结论",
          "**本批新发现的矛盾（必须记着，不许抹平）**" in _ausrc
          and "**两批都没控住的变量**，**未查明**" in _ausrc
          and "**不许**宣布 904 作废" in _ausrc
          and "**不许**宣布 905 是「干净的那次」" in _ausrc
          and "**方向不对称**" in _ausrc
          and "是预测、探针只按了 8 次 ⇒ 没测**" in _ausrc
          and "**仍然不许改实现**" in _ausrc
          and 'out["verdict"] = "sampled"' in _p905
          and "探针**只输出读数**，判读留给基线" in _p905)
    # ══════════ 批 906：方向不对称钉成规则 + 推翻 905 自己的一条推论 ══════════
    p906 = ROOT / "scripts/jimeng_probe906_direction_asymmetry_src.py"
    _p906 = p906.read_text(encoding="utf-8") if p906.exists() else ""
    check("TT.1 906 的设计是**方向对照**：`F8` 与 `B8` **逐字相同、只差方向**"
          "（同一条序列，只把 `Tab` 换成 `Shift+Tab`）⇒ 不对称**当场可判**。"
          "而且必须**第一次跑就把按压前**的 `activeElement` **直接量出来**，"
          "**消掉 905 那个「错开一位」的近似**。⚠️ 判据要钉住**这个设计**，"
          "不然下一个人又会拿「入场态不同」冒充「方向不同」",
          '{"label": "F8",       "walk_end": True,  "back": K_BACK, "mod": False},' in _p906
          and '{"label": "B8",       "walk_end": True,  "back": K_BACK, "mod": True},' in _p906
          and "pre = ev(STATE_JS)[\"active\"]" in _p906
          and '"pre_aria": pre["aria"][:20], "pre_in_node": pre["in_node"],' in _p906
          and "**消掉了 905 那个「错开一位」的近似**" in _ausrc
          and "**只差方向**" in _ausrc)
    check("TT.2 ✅✅ 906 **把方向不对称钉成了规则，并定位到唯一一个位置**"
          "（源站，3 臂 × 2 轮，两轮逐条一致）："
          "同一终点 58、同 back 布 13 次 ⇒ `F8` 布 `[2,3,4,5]`、"
          "`B8` **8 次一次都没布**；⇒ **不对称只发生在「焦点在画布根」"
          "这个位置上**，焦点在**节点本体**上时两个方向**都布**。"
          "⚠️ 另钉死**真判据是 `contains` 不是 `closest`** —— "
          "906 **一条记录里同时有这两种口径**（自带对照）：四个内层控件 "
          "`closest` 全 True / `contains` 全 False，而「没布」的按压前焦点"
          "**正是它们** ⇒ 规则跟的是**「元素本身就是节点本体」**",
          "**① 方向不对称成立，而且被定位到唯一一个位置**" in _ausrc
          and "**8 次一次都没布**" in _ausrc
          and "**不对称只发生在「焦点在画布根」这个位置上**" in _ausrc
          and "**② 布与不布的真判据是 `contains`、不是 `closest`**" in _ausrc
          and "**自带对照**" in _ausrc
          and "**不是「焦点在某个节点里」**" in _ausrc)
    check("TT.3 ✅ 906 钉下了一条**能解释全部读数的最小规则**（**描述、"
          "不是机制**）：`布 ⟺ 按压前焦点是节点本体 ∨ "
          "(按压前焦点是画布根 且 方向为 Tab)` ⇒ 它同时解释 902 的格 A 与 "
          "905/906 的 press1。⚠️ 判据要钉住「**能解释全部读数**」这个性质，"
          "并且不许把它写成机制",
          "**③ 能解释全部读数的最小规则**" in _ausrc
          and "**逐条对得上，仍是描述、" in _ausrc
          and "(按压前焦点是画布根 且 方向为 Tab)" in _ausrc
          and "解释了 902 的格 A" in _ausrc)
    check("TT.4 ⚠️⚠️ 906 **推翻了我自己 904③ 与 905④ 两条推论**，"
          "这两条必须留着**带撤回标记**（不许删、不许悄悄改写成对的）："
          "① 904 ③ 原文说「回来后布的下标**与终点无关**」"
          "—— 906 的终点 **58→`[2,…]`、59→`[0,…]`** ⇒ **恰恰是跟着终点走的**；"
          "② 905 ④ 原文说「三条臂轨迹相同 ⇒ **都不影响回来后从哪开始**」"
          "—— 那三条臂终点是 `∅`/`75`/`59`，**恰好全在「从 0 开始」那一类** ⇒ "
          "**推论无效、是取样没覆盖到的巧合**。"
          "⚠️ 同时钉住 **904 不是异常值**（被 906 干净臂精确复现）",
          "**906 顺手推翻了 905 的一条推论**" in _ausrc
          and "**这个推论无效**" in _ausrc
          and "**恰好全都落在" in _ausrc
          and "**落点确实跟着入场状态（终点）走**" in _ausrc
          and "**906 把本条 ③ 判为无效**" in _ausrc
          and "**904 不是异常值**" in _ausrc
          and "**前 3 次与 904 `base-k30` 逐条相同**" in _ausrc)
    check("TT.5 ⚠️ 906 的**两条探针缺陷必须钉住**（都是我自己踩的）："
          "① 第一版把**一次偶发加载失败**报成了 `BLOCKED_BY_FIXTURE`"
          "（隔离复跑证明登录态是好的）⇒ **一次没命中不等于没登录**，"
          "判据未命中**必须重试**；② 第一版把**落盘写在 `else` 分支里** ⇒ "
          "**被挡那次连文件都没有** —— 而被挡恰恰最该留痕 ⇒ "
          "**落盘必须在 if/else 之外**。"
          "⚠️ 另记 `F8-fresh` **两轮不完全一致**（rep1 多布一次且出现 `None`）",
          "**第一版把一次偶发加载失败报成了 `BLOCKED_BY_FIXTURE`**" in _ausrc
          and "**一次没命中不等于没登录**" in _ausrc
          and "**被挡时也要落盘**" in _ausrc
          and "**被挡那次连文件都没有**" in _ausrc
          and "**两轮不完全一致**" in _ausrc
          and 'out["login_check_attempts"]' in _p906
          and "判据未命中就重试" in _ausrc
          and "被挡时也要落盘" in _p906)
    # ══════════ 批 907（作废）+ 批 908（推翻 899 的「绝不绕回」） ══════════
    p907 = ROOT / "scripts/jimeng_probe907_endpoint_to_start_map_src.py"
    p908 = ROOT / "scripts/jimeng_probe908_wrap_around_src.py"
    _p907 = p907.read_text(encoding="utf-8") if p907.exists() else ""
    _p908 = p908.read_text(encoding="utf-8") if p908.exists() else ""
    check("UU.1 ❌ **907 那一批必须标成作废**，且要写清**为什么** —— "
          "不然下一个人会拿 `第一次布的下标 = 1` 这类读数去支持映射结论。"
          "⚠️ 成因钉的是**走查预算**：`节点数 + 25` 次**正好落在绕回点上**"
          "（908 实测绕回在第 **103** 次、78 个节点）⇒ 6 条臂的终点**全是 `0`**、"
          "**一个能区分的终点都没扫到**。"
          "⚠️ 由此钉死一条通用教训：**按压预算不能拍脑袋给「+25」** —— "
          "它既可能**不够**（被内层控件吃掉），也可能**刚好撞上绕回** ⇒ "
          "**停止条件必须写成「观测到第二次布到 0」**",
          "**907 这一批作废，不许拿它下任何结论**" in _ausrc
          and "**6 条臂的终点全都是下标 `0`**" in _ausrc
          and "**一个能区分的终点都没扫到**" in _ausrc
          and "正好落在绕回点上**" in _ausrc
          and "**按压预算不能拍脑袋给「+25」**" in _ausrc
          and "**必须把走查的停止条件写成「观测到第二次布到 0」**" in _ausrc
          and "终点 → 起点的映射仍然未刻画**" in _ausrc)
    check("UU.2 ⚠️⚠️ **908 撤回了 899 的「绝不绕回」，撤回标记必须留在 899 那条里**"
          "（原文保留、不许删）：**撒手那一半仍然成立**（按前焦点是**节点本体** ⇒ "
          "一次都不布）；但**按前焦点是画布根 ＋ `Tab` ⇒ 布 `'0'` 绕回**（4/4）。"
          "⚠️ 899 读成「不绕回」的成因也必须钉住："
          "**它的按压预算在焦点走回画布根之前就用完了** —— "
          "从末尾走到画布根**还要约 19 次** ⇒ **它根本没问到绕回**",
          "**908 撤回了本条的后半句：「绝不绕回」是错的。**" in _ausrc
          and "**「撒手」那一半仍然成立**" in _ausrc
          and "**布 `'0'` 绕回**" in _ausrc
          and "它的按压预算（`节点数 + 20`）在焦点走回画布根之前就用完了**" in _ausrc
          and "**它根本没问到绕回**" in _ausrc
          and "**④ 899 为什么会读成「不绕回」（取样假象的成因已找到）**" in _ausrc)
    check("UU.3 ✅ 908 的两条臂里，`W2` 必须是**专为证伪「必须先走出画布」"
          "这条机制假设**设计的（按到刚过末尾就**点空白直接回画布根、不走出去**）"
          "⇒ `W2` **也绕回** ⇒ **那条假设被自己的证伪臂推翻**；"
          "⇒ **4 次绕回那一按的按前焦点全是画布根**。"
          "⚠️ 顺带钉住 908 复现的两条旧结论："
          "**900**（整轮跳过 2 个、DOM 下标 **12 / 68**）与 "
          "**896⑤**（走出去那段 `'0'` 一次都没动）",
          '{"arm": "W2"' not in _ausrc          # 臂名不进基线，只写结论
          and "**两条臂**" in _ausrc
          and "**专为证伪「必须先走出画布」" in _ausrc
          and "根本没走出去也绕回了" in _ausrc
          and "4 次绕回那一按的「按前焦点」全是画布根 `Canvas`" in _ausrc
          and "**⑤ 顺带复现了 900**" in _ausrc
          and "**整轮跳过的正好是 2 个、DOM 下标 12 与 68**" in _ausrc
          and "**896⑤「此后不回撤」再获一次证实**" in _ausrc
          and "4 次按压的 `defaultPrevented` 全 `False`**" in _ausrc
          # 探针侧：W2 必须真的「不走出去」—— 走 `n + 6` 次就点空白
          and "for _ in range(n + 6):" in _p908
          and "elif a[\"arm\"]" not in _p908      # 臂名不参与判读
          and "if arm_name == \"W1\":" in _p908)
    check("UU.4 ⚠️ **908 指出 901 有一个实打实的缺口**，这条要钉住，"
          "且**不许在没取到复刻侧源样之前就改实现**（§77）："
          "901 写的是「越界直接 `return`、**没有** `% len`」⇒ "
          "**缺了「画布根 ＋ `Tab` ⇒ 绕回布 `'0'`」这一格**；"
          "⚠️ 而这一格与 906 记下的「画布根 ＋ `Tab` 要布、`Shift+Tab` 不布」"
          "**是同一格** ⇒ 复刻侧**两格都没实现、也没测过**",
          "这是 901 的一个实打实的缺口" in _ausrc
          and "**缺了" in _ausrc
          and "绕回布 `'0'`」这一格**" in _ausrc
          and "**是同一格**" in _ausrc
          and "**两格都没实现、也没测过**" in _ausrc
          and "先取源样再动手**" in _ausrc)
    # ══════════ 批 909：真代码改动（严格 wrapper 判据）＋ 复刻侧验收 ══════════
    p909 = ROOT / "scripts/jimeng_probe909_canvas_root_ck.py"
    ws = ROOT / "src/components/jimeng/JimengWorkspace.tsx"
    _p909 = p909.read_text(encoding="utf-8") if p909.exists() else ""
    _wsrc = ws.read_text(encoding="utf-8") if ws.exists() else ""
    check("VV.1 ✅ 909 **改了实现**，而且改的是**判据本身**：找指针从 "
          "**`n === active || n.contains(active)`** 改成**严格的 `n === active`** —— "
          "依据 906 的**自带对照**（`closest` 全 True / `contains` 全 False，"
          "而「没布」的按压前焦点正是那四个内层控件）。"
          "⚠️ 判据要钉在**源码真实字面量**上：宽松口径一旦回来，"
          "内层控件就会被当成「在节点上」而**多布一次**",
          "const cur = nodes.findIndex((n) => n === active);" in _wsrc
          and "n === active || n.contains(active)" not in _wsrc
          and "**906（源站，各 2/2）：判据必须是严格的 `n === active`。**" in _wsrc
          and "`n.contains(active)` 会把这四个当成「在节点上」而**多布一次**"
          in _wsrc
          and "① 找指针的判据：" in _ausrc)
    check("VV.2 ✅ 909 在 `cur === -1` 那一支**先**判「焦点是否落在某个节点的"
          "**内层控件**里」、是就 `return`；并把注释里的规则表从 5 条改成 7 条"
          "（④ 拆成「撒手（仍成立）」＋「**899 的『绝不绕回』已撤回**」，"
          "⑤ 新增画布根那一格、⑥ 新增内层控件那一格、⑦ 补记 908 的复核）。"
          "⚠️ 判据要钉住**注释里那条撤回** —— 代码改了、注释没改，"
          "下一个人会照着过时注释把「绝不绕回」再写回去",
          "for (const n of nodes) {" in _wsrc
          and "if (n.contains(active)) return;" in _wsrc
          and "**899 当年还断言了「绝不绕回」，908 已撤回**" in _wsrc
          and "908 4/4：**指针在末尾时这一按就是「绕回」**" in _wsrc
          and "② `cur === -1` 那一支：" in _ausrc
          and "③ 注释里的规则表从 5 条改成 **7 条**" in _ausrc)
    check("VV.3 ✅ 909 的**复刻侧验收逐条对上源站**（5 臂 × 2 轮 = 10 条、"
          "**两轮逐条一致**，判据**逐字复用** 906/908、臂**逐字对应** "
          "`F8-fresh`/`F8`/`B8`/`W1`/`W2`）："
          "① 画布根＋`Tab` ⇒ 要布 `'0'`（三条臂**可见**）；"
          "② 画布根＋`Shift+Tab` ⇒ **8 次一次都不布**；"
          "③ **内层控件 5 次全不布**（按压前 `closest=True` 而**本体=False**）"
          "—— **这五次正是 901 改前会多布的那五次**；"
          "④ 布与落点错开一位。⚠️ 判据要钉住**这两套口径同时记**"
          "（`closest` 与 `本体`），不然下一个人又会用宽松口径判读",
          '{"label": "F8-fresh", "walk_end": False, "back": 0,      "mod": False},'
          in _p909
          and '{"label": "B8",       "walk_end": True,  "back": K_BACK, "mod": True},'
          in _p909
          and '"pre_in_node_closest": pre["in_node_closest"],' in _p909
          and '"pre_is_wrapper": pre["is_wrapper"],' in _p909
          and "**画布根 ＋ `Tab` ⇒ 要布 `'0'`**" in _ausrc
          and "**画布根 ＋ `Shift+Tab` ⇒ 8 次一次都不布**" in _ausrc
          and "**而这五次正是 901 改前会多布的那五次**" in _ausrc
          and "**布与落点错开一位**" in _ausrc)
    check("VV.4 ⚠️⚠️ 909 **两格没验到，必须钉住、不许含糊过去**（否则下一个人会"
          "拿「5 臂全过」当「全对齐」）："
          "① **`F8` 的 press1 不可判定** —— 要布的下标**恰好就是当前 `'0'` "
          "所在的下标** ⇒ 「被 `oldValue != '0'` 过滤掉」与「位置本来没变」"
          "**两个现象同时出现** ⇒ **分不出**「调了 `armAll` 且结果相同」与"
          "「什么都没做」；② **源站 `F8` 与复刻 `F8` 终点不同、不可比** —— "
          "源站终点 **58**、复刻终点 `[0]`（demo 只有 2 个节点）⇒ "
          "**不许**拿复刻的 `F8` 说「对上了 906 的 `F8`」。"
          "⇒ 同时钉住那个**未变的已知差异**（源站 press1 布的是**落点所在节点**、"
          "复刻固定布 `0`；成因未查明 ⇒ **不许**据此改复刻）",
          "**`F8` 臂的 press1 不可判定**" in _ausrc
          and "**两个现象同时出现**" in _ausrc
          and "**不许拿复刻的 `F8` 说「对上了 906 的 `F8`」**" in _ausrc
          and "**未变的已知差异（如实记着）**" in _ausrc
          and "**这一格源站的成因仍未查明**，**不许**据此改复刻" in _ausrc)
    check("VV.5 ⚠️ **909 第一版自己踩的探针缺陷必须钉住**（904 已经记过这个坑、"
          "**909 又踩了一次**）：第一版 `press()` **没记 `'0'` 动没动**、只看 "
          "`armed` ⇒ 被 `oldValue != '0'` 过滤吞掉的读数**根本看不见** ⇒ "
          "第二版补上 `zero_before`/`zero_after`/`moved`，"
          "**两条序列一起看才不漏读**。⚠️ 判据要钉在**探针真的记了这三样**上",
          "**探针缺陷（909 第一版自己踩的）**" in _ausrc
          and "**904 已经记过这个坑，909 又踩了一次**" in _ausrc
          and "**两条序列一起看才不漏读**" in _ausrc
          and '"zero_before": pre["zeros"], "zero_after": post["zeros"],' in _p909
          and '"moved": pre["zeros"] != post["zeros"],' in _p909
          and '"after_moved": [s["moved"] for s in after],' in _p909)
    # ══════════ 批 910：重扫「终点 → 起点」—— 测出一个分界 ══════════
    p910 = ROOT / "scripts/jimeng_probe910_endpoint_to_start_rescan_src.py"
    _p910 = p910.read_text(encoding="utf-8") if p910.exists() else ""
    check("WW.1 ✅ 910 **换掉了 907 的设计**，不是只改停止条件：907 靠"
          "「先走到末尾、再往回按 `k` 次」⇒ **终点被走查预算绑架**"
          "（预算 `节点数 + 25` 正好撞上绕回点）；910 **直接扫「从画布根按 `j` 次」**"
          "⇒ **全程不碰末尾**、**结构上撞不上绕回**，且 `j` 最大值 **小于**实测末尾。"
          "⚠️ 判据要钉住**这个设计** —— 终点必须**实测**、**不许**拿公式或"
          "「按压次数」当终点（按压次数 ≠ 步数，内层控件会吃掉一部分）",
          "JS = [0, 3, 8, 15, 25, 40, 55, 65]" in _p910
          and "**直接按 j 次**，不碰末尾" in _p910
          and "endpoint = snap(names)           # ← **实测终点**" in _p910
          and "907 是「先走到末尾、再往回按 `k` 次」⇒ 预算 `节点数 + 25` " in _ausrc
          and "**全程不碰末尾**、" in _ausrc
          and "**结构上撞不上绕回**" in _ausrc)
    check("WW.2 ✅ 910 **测出一个分界**（源站，8 臂 × 2 轮 = 16 条、"
          "**两轮逐条一致**）：实测终点 `∅/2/3/10/20/31` ⇒ 第一次布 **0**；"
          "**`46/56` ⇒ 12**。⚠️⚠️ **分界点没夹逼**（31 与 46 之间一个点都没取）"
          "⇒ **不许**把「≤31→0、≥46→12」当规则、**不许**据此改实现。"
          "⚠️ 同时钉住**落点也跟着变**这一条新信息"
          "（0 那组落在 `视频 1`、12 那组落在 `导出时间线`）",
          "`∅ / 2 / 3 / 10 / 20 / 31` ⇒ **0**（六个值，2/2 全是 0）" in _ausrc
          and "**`46 / 56` ⇒ 12**" in _ausrc
          and "**但分界点没夹逼**" in _ausrc
          and "**不许**据此改实现" in _ausrc
          and "**落点也跟着变（这是新信息）**" in _ausrc
          and "`视频 node: 视频 1`**" in _ausrc
          and "**`导出时间线`**" in _ausrc
          # 分界那一段不许只钉「有分界」，得钉住「**没夹逼**」
          and "**不许**据此改实现" in _ausrc)
    check("WW.3 ⚠️⚠️ **「12 是 900 那两个特殊节点之一」只是相关、不是机制** —— "
          "这一条必须钉住，否则下一个人会顺手把「分界成因 = 12 是特殊节点」"
          "当规则写进实现。⚠️ 同时钉住「12 那一组 12 之后**跳过 13/14/15**」"
          "与「连按 4 次不布（焦点停在内层控件上）＝又是 906② 那条规则」",
          "**这是相关，不是机制**" in _ausrc
          and "**不许**把「12 是特殊节点」" in _ausrc
          and "8 步的完整轨迹**：`[12, 16, 17]`、" in _ausrc
          and "**12 之后跳过了 13/14/15**" in _ausrc
          and "**又是 906② 那条规则**" in _ausrc
          and "`图片 node: b22-upload`，DOM 下标 **12**；另一个是 68）" in _ausrc)
    check("WW.4 ⚠️ **910 必须把两条探针纪律钉进设计里**（都是踩过的坑）："
          "① **`moved` 是必需字段、不是可选** —— `armed` 会被 "
          "`oldValue != '0'` 过滤吞读数（**904 记过、909 又踩一次**）⇒ "
          "`zero_before`/`zero_after`/`moved` **三条一起记**；"
          "② **走查停止条件不能拍脑袋给次数**，要写成"
          "「**观测到第二次布到 0**」（908 的做法）。"
          "⚠️ 判据要钉在**探针真的记了这三条**上",
          "**`moved` 是必需字段、不是可选**" in _ausrc
          and "**904 记过、909 又踩一次**" in _ausrc
          and "**三条一起记**才不漏读" in _ausrc
          and "**走查停止条件不能拍脑袋给次数**" in _ausrc
          and "**观测到第二次布到 0**" in _ausrc
          and '"moved": before["zeros"] != after["zeros"],' in _p910
          and '"zero_before": before["zeros"], "zero_after": after["zeros"],'
          in _p910
          and '"after_moved": [s["moved"] for s in after],' in _p910)
    # ══════════ 批 911：夹逼分界（并修正 910 的「二档」） ══════════
    p911 = ROOT / "scripts/jimeng_probe911_threshold_bisect_src.py"
    _p911 = p911.read_text(encoding="utf-8") if p911.exists() else ""
    check("XX.1 ✅ 911 **把 910 那个「宽 15 个下标」的区间夹窄了**，"
          "而且**修正了 910 的「二档」描述 —— 中间还有一档 `11`**"
          "（源站，5 臂 × 2 轮 = 10 条、**两轮逐条一致**；"
          "设计**逐字沿用** 910、只换 `j`；终点**实测**）："
          "实测终点 **`33` ⇒ 0**、**`36`/`39` ⇒ 11**、**`42`/`45` ⇒ 12**。"
          "⚠️ **两个边界仍未夹逼**（`(33,36]` 与 `(39,42]` 各还差 3 个下标）"
          "⇒ **不许**把三档当规则、**不许**据此改实现",
          "JS = [42, 45, 48, 51, 54]" in _p911
          and "把 15 宽的区间夹到几个点" in _p911
          and "**`∅ … 33` ⇒ 0**" in _ausrc
          and "**`36 / 39` ⇒ 11** ← **这一档 910 没采到**" in _ausrc
          and "**`42 … 56` ⇒ 12**" in _ausrc
          and "**三档**（不是 910 说的两档）" in _ausrc
          and "**两个边界仍未夹逼**" in _ausrc)
    check("XX.2 ⚠️⚠️ **911 顺带收窄了 900 那条「2 个节点整轮没被布 `'0'`」** —— "
          "**911 里下标 12 被布上了** ⇒ **「整轮没被布」是「正序走查那一轮」的"
          "属性、不是该节点的固有属性**。⚠️ 这一条必须钉住，"
          "否则下一个人会拿 900 去解释「为什么起点是 11 或 12」—— "
          "而 910 已经钉过那**只是相关、不是机制**，911 又**把它削弱了一层**",
          "**⚠️ 911 顺带收窄了 900 那条**" in _ausrc
          and "下标 12 **被布上了**（`42` 与 `45` 两档的 press1 都布 `12`）**" in _ausrc
          and "**「整轮没被布」是「正序走查那一轮」的属性，" in _ausrc
          and "不是该节点的固有属性**" in _ausrc
          and "**900 那条要按这个口径读**" in _ausrc
          and "**只是相关、不是机制**；911 的读数**又把它削弱了一层**" in _ausrc
          and "**更不许**拿它编规则" in _ausrc)
    check("XX.3 ⚠️ 911 记下的**分岔位置**也要钉住：`11` 与 `12` 两档的 "
          "**press1–press5 落点完全相同**"
          "（`导出时间线`→`全屏编辑`→`静音`→`添加素材到时间线`）"
          "⇒ 分岔**只体现在 press5 的落点**上（`音频 node: 音频 6` vs "
          "`图片 node: b22-upload`）⇒ **成因仍未查明**（描述、不是机制）。"
          "另记两条跳步：`11` 档 press6 布 **13**（跳过 12）、"
          "`12` 档 press6 布 **16**（跳过 13/14/15）",
          "**`11` 与 `12` 两档的 press1–press5 落点完全相同**" in _ausrc
          and "分岔**只体现在 press5 的落点**上" in _ausrc
          and "**成因仍未查明**（这是描述、不是机制）" in _ausrc
          and "press6 布 **`13`** ⇒ **跳过了 12**" in _ausrc
          and "press6 布 **`16`** ⇒ **跳过了 13/14/15**" in _ausrc)
    # ══════════ 批 912：两个边界都收成 1 宽 ══════════
    p912 = ROOT / "scripts/jimeng_probe912_threshold_bisect2_src.py"
    _p912 = p912.read_text(encoding="utf-8") if p912.exists() else ""
    check("YY.1 ✅✅ 912 **把 911 剩下的两个边界都收成了 1 宽**"
          "（源站，4 臂 × 2 轮 = 8 条、**两轮逐条一致**；"
          "设计**逐字沿用** 911、只换 `j`；终点**实测**）："
          "终点 **`34`/`35` ⇒ 0**、**`40` ⇒ 11**、**`41` ⇒ 12** ⇒ "
          "**三批（910/911/912）合起来边界收成 `35|36` 与 `40|41`**。"
          "⚠️ 判据要钉住**三批合起来的那张完整映射表**，"
          "不然下一个人只会看到最新那一批的四个点",
          "JS = [43, 44, 49, 50]" in _p912
          and "**各取两个点**，把两个边界都收成 1 宽" in _p912
          and "**终点 `≤ 35` ⇒ 起点 `0`**" in _ausrc
          and "**终点 `36 … 40` ⇒ 起点 `11`**（实测过 `36 / 39 / 40`）"
          in _ausrc
          and "**终点 `≥ 41` ⇒ 起点 `12`**（实测过 `41 / 42 / 45 / 46 / 56`）"
          in _ausrc
          and "**`35 | 36`** 与 **`40 | 41`**" in _ausrc)
    check("YY.2 ⚠️⚠️ **912 必须钉住「收窄的是经验边界、不是理解」** —— "
          "边界从 15 宽收到 1+1 宽看着像「查清了」，但**为什么是 0/11/12、"
          "为什么分界落在 `35|36` 与 `40|41`，全部未查明**。"
          "⚠️ 因此：**不许**把它写成规则、**不许**据此改实现"
          "（复刻侧目前固定布 `0`）；**这条不许就此结案**。"
          "⚠️ 顺带钉住那条**巧合级别的观察不是解释**"
          "（三个起点 `0/11/12` 里后两个相邻）",
          "**但这仍然只是「终点 → 起点」的经验映射，不是机制**" in _ausrc
          and "为什么分界落在 35|36 与 40|41，" in _ausrc
          and "**不许**把它写成规则、**不许**据此改实现" in _ausrc
          and "**收窄的是「经验边界」，不是「理解」**" in _ausrc
          and "**成因仍然未查明**，这条不许就此结案" in _ausrc
          and "**巧合级别的观察（不是解释）**" in _ausrc
          and "**不许**拿它当解释、**不许**拿它去推规则" in _ausrc)

    check("MM.1 「算下一个」的规则要以**实测读数**写进基线：① 顺序**≈DOM 序**"
          "（按 `data-testid` 换算下标，不钉序号本身）；② **到末尾就停手、"
          "绝不绕回**（`max_dom_idx_armed=75`＝最后一个、`revisited={}`）；"
          "③ 途中 **27 次**「原地没布」；④ 复核 `n_zero` 恒 1、"
          "`defaultPrevented` 全 False。⚠️ 仪器 `INSTALL_JS`/`STATE_JS` "
          "**逐字复用 896**，起点也**同为点空白**；按 Tab **节点数 + 25** 次、"
          "**故意走过一圈**（按 +5 **不够**，见 MM.3）",
          '"source_roving_next_rule_899"' in _ausrc
          and "顺序 ≈ DOM 序" in _ausrc
          and "**到末尾就停手、绝不绕回**" in _ausrc
          and "max_dom_idx_armed = 75" in _ausrc
          and "revisited = {}" in _ausrc
          and "**27 次按压「原地没布」**" in _ausrc
          and "**彻底撒手**" in _ausrc
          and "逐字复用" in _p899
          and "OVERRUN = 25" in _p899
          and "故意**走过一圈**" in _p899)
    check("MM.2 ⚠️⚠️ **两条未解释，不许编机制**：① 76 个节点里有 **2 个整轮"
          "从没被布上 `'0'`** —— `图片 node: b22-upload`（焦点**第 17 步走到过**"
          "它、但它从没被布上 `'0'`）与 `音频 node: 音频 61`；"
          "**两轮完全一致 ⇒ 不是随机**、但**原因未查明**；"
          "② **有 1 个节点被布上 `'0'`、而焦点从没到达它**。"
          "⚠️ 由此钉死两条不许：复刻按「**纯 DOM 序**」实现**会**在那 2 个节点上"
          "和源站不一致 ⇒ **不许**把这个差异当 bug **顺手抹平**，"
          "**更不许**反过来**猜**一个原因去「对齐」它",
          "**两条未解释，不许编机制**" in _ausrc
          and "76 个节点里有 2 个整轮从没被布上 `'0'`" in _ausrc
          and "图片 node: b22-upload" in _ausrc
          and "音频 node: 音频 61" in _ausrc
          and "**原因未查明**" in _ausrc
          and "**更不许**反过来**猜**一个原因去「对齐」它" in _ausrc)
    check("MM.3 ⚠️ 899 第一版自己踩的两个坑必须留痕：① `OVERRUN=5` **不够** —— "
          "81 次按压里只有 72 次真正推进指针（其余是「原地重写同一个已有 `'0'` 的"
          "节点」），指针只走到下标 72、**根本没到末尾** ⇒ 「怎么绕」"
          "**其实没测到**，**差点**把「不绕回」建立在没测到的数据上；"
          "② ⚠️⚠️ `focus_is_wrapper` **写错了、而且恒为真** —— 它比的是"
          "「focusin 的 target 是否等于 `activeElement`」，而拿到焦点的元素"
          "**按定义**就成了 `activeElement`（896 那边 18/18 全 True 就是这个"
          "原因，看着像证据、其实**什么也没测**）⇒ 899 改成真判据"
          "（**落点自己带不带 `react-flow__node` 类**）。"
          "⇒ 教训：**一个恒真的字段比没有字段更坏**",
          "`OVERRUN=5` **不够**" in _ausrc
          and "**根本没到末尾**" in _ausrc
          and "**差点**" in _ausrc
          and "写错了、而且恒为真" in _ausrc
          and "按定义" in _ausrc
          and "看着像证据、" in _ausrc
          and "**一个恒真的字段比没有字段更坏**" in _ausrc
          and "target_is_node_wrapper" in _p899
          and "OVERRUN = 25" in _p899)
    check("MM.4 ⚠️ 899 汇总代码第一版还会**崩**：`seq` 里可能有 `None`"
          "（布 `'0'` 的目标**不在**本轮记录的 DOM 序里 —— 走查途中节点被 "
          "React 重建就会这样，本轮实测到 **1 次**）⇒ 排序/比较前**必须**先把 "
          "`None` 摘出去。⚠️ 顺带钉住**不许钉**的东西：节点总数是**易变量**"
          "（同 URL 逐轮 74→75→76→77），按**身份**（`data-testid`）记 DOM 序",
          "汇总代码第一版还会**崩**" in _ausrc
          and "本轮实测到 1 次" in _ausrc
          and "**必须**先把 " in _ausrc
          and "摘出去" in _ausrc
          and "**节点总数是易变量**" in _ausrc
          and "按**身份**（`data-testid`）记 DOM 序" in _ausrc)
    # ══════════ 批 900：那 2 个节点 —— 排除一个方向 ══════════
    p900 = ROOT / "scripts/jimeng_probe900_unarmed_nodes_src.py"
    _p900 = p900.read_text(encoding="utf-8") if p900.exists() else ""
    check("NN.1 ✅ **900 把「那 2 个节点为什么整轮没被布上 `'0'`」推到了"
          "**能推的边界**并**排除了一个方向**（各 2/2）：① **它们在应用的"
          "节点表里** —— 第一次 Tab 时应用给**全部 76 个**都写了 `tabindex`、"
          "`not_written` **为空** ⇒ **不是**「压根不在表里」；"
          "② **它们在 DOM 层毫无特殊之处** —— 76 个节点**属性集完全相同**、"
          "**离群 0 个**，父链 / `in_another_node` / 可聚焦子孙数 / 尺寸都相同。"
          "⇒ **「DOM 上有特殊标记」这个方向被排除了**",
          '"unarmed_nodes_have_no_dom_reason_900"' in _ausrc
          and "**它们在应用的节点表里**" in _ausrc
          and "`not_written` **为空**" in _ausrc
          and "**离群节点 0 个**" in _ausrc
          and "这个方向被排除了" in _ausrc
          and "FINGERPRINT_JS" in _p900
          and "attr_set_outliers" in _p900
          and "not_written" in _p900)
    check("NN.2 ⚠️⚠️ 由此得到一条**实现层的硬约束**：这一条是「**仍未查明**」、"
          "而且是**原理上不可从 DOM 查明**的那一种（原因在**应用自己的节点表"
          "顺序/指针**里）⇒ 复刻**没法**复刻这个「跳过 2 个节点」的行为，"
          "实现时**只能按纯 DOM 序**并把差异**如实记为已知差异**。"
          "⚠️ **不许**为了「看起来一致」去**编**一个 DOM 层判据"
          "（如「跳过 aria 含 upload 的节点」「跳过倒数第 N 个」）—— "
          "那是**把未查明的东西伪装成已知**",
          "**实现层的硬约束**" in _ausrc
          and "**原理上不可从 DOM 查明**" in _ausrc
          and "**只能按纯 DOM 序**" in _ausrc
          and "**如实记为已知差异**" in _ausrc
          and "**把未查明的东西伪装成已知**" in _ausrc
          and "**不许**为了「看起来一致」" in _ausrc)
    check("NN.3 📌 顺带一条**对 896 规则②的修正**（900 实测 2/2）："
          "「**每次 keydown 都布 `'0'`」不是无条件的** —— 从画布**中途**"
          "连按 30 次 `Shift+Tab`，**只有第 1 次**布了 `'0'`、其余 29 次"
          "**一次都没布** ⇒ **焦点一旦不在节点本体上，应用就不再布**。"
          "⇒ 896 那条「唯一触发是 keydown」**仍然成立**，但要补"
          "**还要求那一刻焦点在某个节点上**",
          "对 896 规则②的修正" in _ausrc
          and "**不是无条件的**" in _ausrc
          and "焦点一旦不在节点本体上，应用就**不再布**" in _ausrc
          and "**还要求那一刻焦点在某个节点上**" in _ausrc
          and "**仍然成立**" in _ausrc
          and "BACK_STEPS = 30" in _p900)
    check("NN.4 ⚠️ **900 第一版自己踩的坑**：结尾把一大坨 `json.dumps(summary)` "
          "**打到 stdout**，而输出**管道给 `tail`** ⇒ `tail` 早退出、管道写不进"
          "⇒ `BlockingIOError` ⇒ **探针在最后一步炸掉、连文件都没写**"
          "（写文件排在打印**之后**）⇒ 教训：**① 落盘必须排在打印之前**、"
          "**② 长输出要么落盘、要么别进管道**。⚠️ 判据要钉在**探针源码的"
          "真实顺序**上（写文件那句在 `print` 之前）",
          "**900 第一版自己踩的坑**" in _ausrc
          and "BlockingIOError" in _ausrc
          and "① 落盘必须排在打印之前" in _ausrc
          and "② 长输出要么落盘、要么别进管道" in _ausrc
          and "**先落盘、再打印**" in _p900
          and _p900.index("json.dump(out") < _p900.index("== 汇总（紧凑版"))
    check("KK.4 896 必须把 894 判据里那个**洞**留痕：`summarize()` 用 "
          "`v[\"tabindex\"].add(...)` **只收集合、丢掉计数**，而「各有几个 `0`」"
          "恰好是区分 roving 的**唯一**判据 ⇒ 894 **读到了**却被**抹平**了。"
          "⚠️ 同时钉住两条不许：① 894 的 `after_insert` / `after_insert_blank` / "
          "`after_select` **跑在 Tab 走查之后**、**不是中性态**，不许当中性读数；"
          "② **节点总数是易变量**（同 URL 逐轮 74→75→76→77），只钉**关系**",
          "只收集合、丢掉计数" in _ausrc
          and "各有几个 0" in _ausrc
          and "读到了**却被 summarize **抹平**" in _ausrc
          and "跑在 Tab 走查之后" in _ausrc
          and "74→75→76→77" in _ausrc
          and "不许**钉 `n_nodes` 或节点序号" in _ausrc)

    check("HH.4 基线里**不许**留一条「仍未解决」跟结论打架：矛盾条目已改名 "
          "`..._RESOLVED_893`，且旧名字**必须已经不在**基线里。"
          "⚠️ 判据要跟上事实（钉假设的措辞会把判据锁死在过时状态），"
          "但**不许**因为矛盾解开就把「为什么 tabindex 是 None **仍未查清**」"
          "一起删掉",
          '"contradiction_891_vs_source_RESOLVED_893"' in _ausrc
          and "contradiction_891_vs_source_still_open" not in _ausrc
          and "**仍未查清**" in _ausrc
          and "不许**简化成「源站未选中节点一律不可聚焦」" in _ausrc)
    check("CC.7 886 的教训落地：**组件内凡是要复用，就该提到模块级，"
          "别复制第二份** —— 886 第一版把实现抽成组件内闭包，结果它和 Clear "
          "内联那段是**复制粘贴关系**，按内容替换**匹配到了自己**、把文件改坏"
          "两回（第一次删了 376 行、JSX 结构破坏）。共享函数因此放**模块级**",
          "别复制第二份" in _agp_raw
          and "匹配到了自己" in _agp_raw
          and "function refocusToNodeFromToolbar(" in _agp_raw
          # 芯片与 Clear **两处都**调模块级那个，没有第二份实现。
          # ⚠️ 数的是「`refocusToNodeFromToolbar(` **后跟换行**」的**调用点**
          #   （定义那行是 `function refocusToNodeFromToolbar(from...`，
          #   注释里那处是 `` `refocusToNodeFromToolbar()` `` 后面跟 ` —— `）。
          #   第一版写成 `count(...) == 3` 把**注释里那一次**也算进去了，
          #   实际是 4 ⇒ 又一次「判据自己数错了」。
          and _agp_raw.count("refocusToNodeFromToolbar(\n") == 2)
    check("CC.8 「芯片上按 Esc **值还在不在**」源站**未取样**，不许与"
          "「落点」那次的证据合并成一句 —— 886 的 `Clear 还在=False` 只是"
          "**层关了导致控件消失**，**推不出**值被清了。"
          " ⚠️ CC.6/CC.8 第一版 FAIL：判据引的三句都在 §98 与源码注释里、"
          "**探针里根本没有** —— 该被钉的地方没钉，判据自然过不了",
          "**推不出**" in _p886
          and "value_measured" in _p886
          and "不许**拿 `clear_after` 当证据" in _p886)
    check("CC.9 `filterSel` 的类型**含 `undefined`**（870 那个「开 ↔ 关」切换会"
          "写进 `undefined`）—— ⚠️ `npm run check` 跑的是 **eslint、不跑 tsc**，"
          "所以这类错误门禁一直绿着，只在 `tsc --noEmit` 里露出来。"
          "886 顺手最小修掉，代码里写明了「门禁看不见」这件事",
          "Record<string, string | null | undefined>" in _agp_raw
          and "不跑 tsc" in _agp_raw)
    check("BB.10 882 探针用**劫持 prototype** 抓调用栈定位到那个 handler，"
          "而且**每段测完自己 reload 恢复**（诊断动作不许留痕）；"
          "另有**不按 Esc 的对照组**——焦点不动，确证是 Esc 触发的，"
          "不是「面板本来就会掉焦点」",
          bool(_p882)
          and "HTMLElement.prototype.focus" in _p882
          and "诊断动作**必须**恢复" in _p882
          and "location.reload()" in _p882
          and "没按 Esc（对照）" in _p882)

    print(f"\n{checks - len(failures)}/{checks}")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("batch 841-unclickable OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
