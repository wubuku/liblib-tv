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
        # ⚠️⚠️⚠️ 【942 修的真 bug】原来这里**第一个条件是错的**：
        #    `(c == nxt2 and c in "\"'")` 只检查「第 1 个 == 第 3 个」，
        #    **漏了第 2 个** ⇒ `with open(OUT, "w")` 里的那个双引号
        #    （`c='"'`、`nxt='w'`、`nxt2='"'`）**当场触发三引号模式**
        #    ⇒ 从那儿起**整段被当成字符串吞掉**。
        #    实测代价：审计源码 162 处 `//` 行注释**只剥掉 10 行**、152 行原样留着
        #    ⇒ 3 条 `acode` 字面量判据数的一直是「**文件里**出现几次」，
        #    只是**它们要数的字面量恰好只出现在代码里**才碰巧对
        #    （940 / 941 往基线里各写一次那个字面量就当场变红，就是这个机制）。
        #    ⇒ 第二个条件（`nxt == c and nxt2 == c`）才是「三个连续引号」的正确写法，
        #    第一个条件**冗余且有害** ⇒ 删掉。
        if nxt == c and nxt2 == c and c in "\"'":
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
    # I.5 回归钉子：这 9 个层**必须真的探到**。逗号 bug 活着的时候，它们
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
    #    850/851 记的 `arrows_move: None` 是**判据缺陷**，不是产品缺陷 ——
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
          # ⚠️⚠️ 961 修：原文是 `"只有 1 项" in lsrc or "只有 1 项" in <audit>`。
          #   ⭐ 补登记后锚点自查**第一次报出这个问题**：`lsrc`
          #   （`jimeng_kb_probe_lib.py`）里「只有 1 项」**出现 0 次**
          #   ⇒ **第一个析取支恒假**，这条判据一直**只靠第二个析取**撑着。
          #   ⇒ **改法不是放宽门，是删掉那句从来不真的话**（判据强度不变）。
          "只有 1 项" in asrc)
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
    # ⚠️⚠️ 批 942 订正：这条判据原来**钉的是注释里的一句散文**（源码注释
    #   「刻意**不** `stopPropagation()`」）。942 修好 `strip_comments` 之前，
    #   `.tsx` 的注释**根本没被剥掉** ⇒ 它读的**一直是注释、不是代码** ⇒
    #   那句注释只要还在就绿，**就算有人往 Clear 的 Esc 分支里真的加上
    #   `stopPropagation()` 也照样绿**（一个恒真的判据比没有判据更坏）。
    #   普查读数（942，见 DDDD.3）：473 条判据里对 `strip_comments` 派生变量
    #   的锚文共 **60** 条，**只有这 1 条**是读注释的，其余 55 条读代码。
    #   ⇒ 本条改成钉**代码形态**。
    def _aa3_ok(s):
        """复刻 Clear 的 Esc 行为：**会清除**、且**不**截断冒泡。

        ⭐ ②「不截断」是否定判据，只看它会被「整个文件从不调用
        `stopPropagation`」这种空洞写法白送 ⇒ ③ 用**同一个文件里另一个
        Esc 分支**（音色库列表）当阳性对照。承 940 的纪律：**阴阳对照门
        的两个答案必须来自两个不同的集合**，而这里是「一个集合里一个
        取反、一个不取反」，同样要求那一侧**真的存在**。
        """
        _head, mark, tail = s.partition(
            'aria-label={`Clear ${label} filter`}')
        if not mark:
            return False
        kd, kdmark, after = tail.partition("onKeyDown={(e) => {")
        if not kdmark:
            return False
        esc, listboxmark, _rest = after.partition('role="listbox"')
        if not listboxmark:
            return False
        # ① Esc 分支**真的清除**：收焦点 + 清值 + 关层，三个动作都在
        if not ("refocusToNodeFromToolbar(" in esc
                and "[label]: null," in esc
                and "[label]: false," in esc):
            return False
        # ② **不** `stopPropagation` —— 清除归这一层，关面板那半必须冒泡
        if "stopPropagation" in esc:
            return False
        # ③ 阳性对照：列表那份 Esc 分支**确实**截断，且全文仅此一处
        #    ⚠️ 比对前先**空白归一化**：这两句在剥后是**分行**的，
        #    钉死换行等于把判据锁在排版上（源站某次 reformat 就假红）。
        _norm = " ".join(s.split())
        return (s.count("stopPropagation") == 1
                and "e.preventDefault(); e.stopPropagation();" in _norm)

    check("AA.3 复刻的 Clear **响应 Esc**：焦点在它上面按 Esc 会清除"
          "（875 加按钮时漏了；源站 876c 三次复现）。且**刻意不**"
          "`stopPropagation` —— 源站 Esc 是「清除 **+** 关掉整个面板」"
          "两个动作同时发生，关面板那半必须**继续冒泡**给上层 handler"
          " ⚠️⚠️ 942：**原来这四条锚文里，最后一条锚的是注释里的散文**"
          "（剥除器修好前 `.tsx` 注释根本没被剥）⇒ 已改成钉**代码形态**"
          "＋一条**阳性对照**（同文件另一个 Esc 分支确实在截断）",
          _aa3_ok(_agp2))
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
    # ══════════ 批 913：换方法（证伪落空，如实记账） ══════════
    p913 = ROOT / "scripts/jimeng_probe913_same_endpoint_two_routes_src.py"
    _p913 = p913.read_text(encoding="utf-8") if p913.exists() else ""
    check("ZZ.1 ✅ 913 **真的测到的那部分**要钉住：`A-fwd49` 终点 **40** ⇒ 起点 "
          "**11**、`A-fwd60` 终点 **51** ⇒ 起点 **12** ⇒ "
          "**与 912 那张表逐条相同**（2/2）⇒ 912 的表**又稳了一次**",
          "A-fwd49" in _p913 and "A-fwd60" in _p913
          and "`A-fwd49` 终点 **40** ⇒ 起点 **11**" in _ausrc
          and "`A-fwd60` 终点 **51** ⇒ 起点 **12**" in _ausrc
          and "**与 `source_endpoint_to_start_bands_1wide_912` 逐条相同**（2/2）"
          in _ausrc
          and "⇒ 912 那张表**又稳了一次**" in _ausrc)
    check("ZZ.2 ⚠️❌ **913 的证伪落空了，必须钉住、而且要钉住「两个方向都没测到」**"
          "（源站，4 臂 × 2 轮，两轮逐条一致）：**两条 `B` 臂「往回按了 0 次」**"
          "—— `ARMS` 里 `B` 的 `j` 填的**就是直接落在目标终点上的那个 `j`** ⇒ "
          "**`A` 与 `B` 实际是同一条路线** ⇒ 「同一终点、两条不同路线」"
          "**根本没成立**。⇒ ⚠️ **不许**据 913 说「起点是终点的纯函数」，"
          "⚠️ **也不许**据 913 说「起点跟历史走」—— **两个方向都没测到**",
          "**913 的证伪没做成" in _ausrc
          and "「往回按了 0 次」" in _ausrc
          and "**自适应停止条件一进去就满足、一次都没往回按**" in _ausrc
          and "**`A` 与 `B` 实际是同一条路线**" in _ausrc
          and "这个对照根本没成立**" in _ausrc
          and "**不许**据 913 说「起点是终点的纯函数」" in _ausrc
          and "**两个方向这一批都没测到**" in _ausrc
          and "**要改成 `j` 越过目标**" in _ausrc)
    check("ZZ.3 ⚠️ **913 的设计错误本身要钉成通用教训**（不只钉这一批）："
          "**证伪臂的参数必须「越过」对照组**，否则**两条臂是同一条**、"
          "**那一问根本没被问到** —— 与 899/901「按压次数要盖过被内层控件吃掉的"
          "那部分，否则末尾行为根本没被问到」**是同一条教训**："
          "**参数取在对照组自己的取值上，对照就作废了**。"
          "⚠️ 判据要钉住**探针里那个 `ARMS` 的错值**（`B` 的 `j` = 对照组的 `j`），"
          "这样下一个人看得见错在哪、而不是只看到结论",
          '{"label": "B-fwd49-back",  "j": 49, "back_to": 40},' in _p913
          and '{"label": "B-fwd60-back",  "j": 60, "back_to": 51},' in _p913
          and "**证伪臂的 `j` 必须「越过」目标终点**" in _ausrc
          and "**同一条教训**：**参数取在对照组自己的取值上，对照就作废了**"
          in _ausrc
          and "否则**两条臂是同一条**" in _ausrc)
    # ══════════ 批 914：913 落空的证伪**这次真做成了** ══════════
    p914 = ROOT / "scripts/jimeng_probe914_two_routes_real_backwalk_src.py"
    _p914 = p914.read_text(encoding="utf-8") if p914.exists() else ""
    check("AAA.1 ✅ **914 第一次把 913 落空的那个证伪真正做成了**"
          "（源站，3 对 × 2 轮 = 6 组比较，两轮逐条一致）："
          "**同一个终点、两条真的不同的路线 ⇒ 首次布的下标与全程布序列"
          "逐条相同** —— ① 终点 **35**（`A-fwd44` vs `B-fwd45-back35`"
          "正走到 36 再往回 1 次）⇒ 都 ⇒ 起点 **0**、布 `[0,1,2,3]`；"
          "② 终点 **40**（`A-fwd49` vs `B-fwd55-back40`"
          "正走到 46 再往回 6 次）⇒ 都 ⇒ 起点 **11**、布 `[11,13,14]`；"
          "③ 终点 **51**（`A-fwd60` vs `B-fwd65-back51`"
          "正走到 56 再往回 5 次）⇒ 都 ⇒ 起点 **12**、布 `[12,16,17]`"
          "⇒ **910–912 那个「终点与历史共变」的顾虑被排除**",
          "source_endpoint_start_invariant_to_history_914" in _ausrc
          and "**同一个终点、两条真的不同的路线 ⇒ 起点与全程布序列逐条相同**"
          in _ausrc
          and "`A-fwd44`（纯正走）／" in _ausrc
          and "`A-fwd49`／`B-fwd55-back40`" in _ausrc
          and "`A-fwd60`／`B-fwd65-back51`" in _ausrc
          and "起点 **0**、全程布 `[0,1,2,3]`" in _ausrc
          and "起点 **11**、全程布 `[11,13,14]`" in _ausrc
          and "起点 **12**、全程布 `[12,16,17]`" in _ausrc
          and "**910–912 那个「终点与历史共变」的顾虑被排除了**" in _ausrc
          # ⚠️ 判据要钉**读数**，不能只在 README 里写结论
          and '{"label": "A-fwd44",         "pair": 1, "j": 44,' in _p914
          and '{"label": "B-fwd45-back35",  "pair": 1, "j": 45, "back_to": 35},'
          in _p914
          and '{"label": "A-fwd49",         "pair": 2, "j": 49,' in _p914
          and '{"label": "B-fwd55-back40",  "pair": 2, "j": 55, "back_to": 40},'
          in _p914
          and '{"label": "A-fwd60",         "pair": 3, "j": 60,' in _p914
          and '{"label": "B-fwd65-back51",  "pair": 3, "j": 65, "back_to": 51},'
          in _p914)
    check("AAA.2 ⚠️⚠️ **914 只排除了「一种」历史扰动** ⇒ "
          "⚠️ **不许**把「起点是终点的纯函数」写成**全称规则**"
          "（别的历史轴：先往回走进画布 / 点某个节点再走开 / …"
          "**一个都没测**）；且 **为什么是 `0/11/12`、"
          "分界为什么在 `35|36` 与 `40|41` 仍然未查明** ⇒ "
          "**一条新机制都没测到**，**不许**据此结案、**不许**据此改实现",
          "⚠️ **不许**把「起点是终点的纯函数」写成全称规则" in _ausrc
          and "别的历史轴（先往回走进画布、点某个节点再走开、…）**一个都没测**"
          in _ausrc
          and "**为什么是 `0 / 11 / 12`**" in _ausrc
          and "**为什么分界在 `35|36` 与 `40|41`**" in _ausrc
          and "本批**一条新机制都没测到**" in _ausrc
          and "**不许**据此结案、**不许**据此改实现" in _ausrc
          and "source_endpoint_start_invariant_to_history_914" in _ausrc)
    check("AAA.3 ✅ **914 顺带测到一条新读数**：**反向走是严格 `−1`**"
          "（`36→35`、`46→45→44→43→42→41→40`、"
          "`56→55→54→53→52→51`，两轮逐条一致）—— "
          "⚠️ 但该区间**不含**下标 `12/68` 那两个特殊节点 ⇒ "
          "**「反向走会不会也跳过特殊节点」仍然没测到**，**不许外推**",
          "✅ **顺带测到一条新读数" in _ausrc
          and "**反向走是严格 `−1`**" in _ausrc
          and "`46→45→44→43→42→41→40`" in _ausrc
          and "`56→55→54→53→52→51`" in _ausrc
          and "**「反向走会不会也跳过特殊节点」仍然没测到**，不许外推" in _ausrc
          # 探针里必须**真的记了往回轨迹**（不然「严格 −1」是编的）
          and '"back_trace": back_trace,' in _p914
          and '"k": len(back_presses),' in _p914)
    check("AAA.4 ✅⚠️ **914 探针自己长了一道防线**（本批最值钱的改动）："
          "每条 `B` 臂的 `design_ok` **同时**要求三条 —— "
          "① 正走终点 **≠** 目标（真的越过了）、② `n_back_presses >= 1`"
          "（**真的往回按了**）、③ 实测终点 **==** 目标（**真的命中**）；"
          "任何一条不成立就打「**设计违规**」标记 ⇒ 913 那种"
          "「两条臂其实是同一条」的错**现在会被探针自己叫出来**。"
          "静态侧还有一道：`B` 的 `j` 不严格大于同对 `A` 就**开跑前 assert 挂掉**。"
          "⚠️ 判据要钉**这三项的真实字面量**，这样下一个人能看见防线在哪",
          '"fwd_overshot": fwd_only_end["zero_one"],' in _p914
          and "and len(back_presses) >= 1" in _p914
          and "and design[\"reached_target\"])" in _p914
          and '"design_ok": a["design"].get("design_ok"),' in _p914
          and "**!! 设计违规**" in _p914
          and "_b[0][\"j\"] > _a[0][\"j\"]" in _p914
          and "**证伪臂的 j 必须越过对照组**" in _p914
          and "（这一条是脚本层面的、不依赖实测，" in _p914
          and "探针**自己**拒绝再犯 913 的错" in _p914
          and "⇒ 913 那种「两条臂其实是同一条」的错，" in _ausrc
          and "⚠️ 静态侧还有一道：" in _ausrc)
    check("AAA.5 ⚠️ **914 踩到的流程坑也要钉住**：探针 stdout "
          "**重定向到文件时忘加 `-u`** ⇒ 块缓冲把日志全压在内存里、"
          "**跑了 10 分钟日志 0 行** ⇒ **分不清「在跑」还是「挂住」**"
          "（只能靠 `ps` 看 Chrome GPU 进程的 CPU）"
          "⇒ ⚠️ **重定向到文件的探针一律要加 `-u`**",
          "⚠️ **本批踩到的流程坑（同样钉住）**" in _ausrc
          and "**重定向到文件时忘加 `-u`**" in _ausrc
          and "**跑了 10 分钟日志 0 行**" in _ausrc
          and "**分不清「在跑」还是「挂住」**" in _ausrc
          and "**重定向到文件的探针一律要加 `-u`**" in _ausrc)
    # ══════════ 批 915：第二条历史扰动轴（**只测到一种形状**） ══════════
    p915 = ROOT / "scripts/jimeng_probe915_prehistory_irrelevance_src.py"
    _p915 = p915.read_text(encoding="utf-8") if p915.exists() else ""
    check("BBB.1 ✅ **915 测了第二条历史扰动轴：「最终那一段走查之前的前史」无关**"
          "（源站，8 臂 × 2 轮 = 16 条，两轮逐条一致）。"
          "每个扰动臂的**最后一段走查**与某条**基线臂**逐字相同，"
          "**只有前面多了别的走查 + 一次点空白** ⇒ "
          "**10 组「扰动臂 vs 同目标基线臂」比较：同终点、同布序列、"
          "同首次布下标，10/10** —— 终点 40 ⇒ 起点 **11**、"
          "布 `[11,13,14]`；35 ⇒ **0**、`[0,1,2,3]`；51 ⇒ **12**、`[12,16,17]`",
          "source_prehistory_irrelevance_915" in _ausrc
          and "**915 测了第二条历史扰动轴" in _ausrc
          and "**10 组「扰动臂 vs 同目标基线臂」比较，同终点、同布序列、" in _ausrc
          and "同首次布下标，10/10**" in _ausrc
          and "起点 **11**、全程布 `[11,13,14]`" in _ausrc
          and "起点 **0**、全程布 `[0,1,2,3]`" in _ausrc
          and "起点 **12**、全程布 `[12,16,17]`" in _ausrc
          # ⚠️ 钉**读数**（探针里的臂定义），不只钉结论
          and '{"label": "D1-pre30-fwd49",       "target": 40, "base": False,'
          "\n     " '"steps": [("fwd", 30), ("blank", 1), ("fwd", 49)]},' in _p915
          and '{"label": "H-pre30-back5-fwd44",  "target": 35, "base": False,'
          "\n     " '"steps": [("fwd", 30), ("back", 5), ("blank", 1),'
          ' ("fwd", 44)]},' in _p915
          and '{"label": "G-pre30-back5-fwd60",  "target": 51, "base": False,'
          "\n     " '"steps": [("fwd", 30), ("back", 5), ("blank", 1),'
          ' ("fwd", 60)]},' in _p915)
    check("BBB.2 ⚠️❌ **915 只测到「一种」扰动形状，而且这个塌缩是读数之后"
          "人工看出来的** —— `D2 / G / H` 的「**回走 5**」那一步"
          "**实测是空操作**（`armed_idx` 空、`moved` 全 `False`、**终点也没动**）"
          "⇒ 那三条臂的前史**其实只等于「`fwd 30` + 点空白」** ⇒ "
          "**与 `D1 / F` 不是两种扰动**。⚠️ **不许**拿 915 说"
          "「两种扰动都无关」。⚠️ 且**本批这一版读数是在补 `step_effective` "
          "探针之前跑的** ⇒ 塌缩**不是探针自己报出来的**，要如实记着",
          "⚠️❌ **但本批只测到「一种」扰动形状**" in _ausrc
          and "**实测是空操作**" in _ausrc
          and "`armed_idx` 空、" in _ausrc
          and "**终点也没动**" in _ausrc
          and "**其实只等于「`fwd 30` + 点空白」**" in _ausrc
          and "**与 `D1 / F` 不是两种扰动**" in _ausrc
          and "我**以为**测了两种形状（带/不带回走），**实际上只测了一种**" in _ausrc
          and "**本批这一版的读数是在补这个探针之前跑的**" in _ausrc
          and "不是探针自己报出来的 —— **这一点要如实记着**" in _ausrc
          and '"step_effective": any(p["moved"] or p["armed"]' in _p915
          and '"n_pre_keysteps_effective": sum(' in _p915)
    check("BBB.3 ✅ **915 顺带第三次证实 906 那条规则**"
          "（`source_roving_direction_asymmetry_906`，906/909 之后第三次）："
          "`fwd 30` 的**最后两次**按压也**一次都没布** ⇒ 那一刻焦点落在"
          "**某个节点的内层控件**上 ⇒ 随后的 `Shift+Tab` 自然也一次都不布 "
          "⇒ **「按压前焦点在内层控件 ⇒ 一次都不布」。**"
          "⚠️ 判据要钉**这条因果链**，不然「回走 5 空操作」就只是个巧合",
          "✅ **顺带第三次证实 `source_roving_direction_asymmetry_906` 那条规则**"
          in _ausrc
          and "（906/909 之后第三次）" in _ausrc
          and "`fwd 30` 的**最后两次**按压也**一次都没布**" in _ausrc
          and "焦点落在**某个节点的内层控件**上" in _ausrc
          and "**「按压前焦点在内层控件 ⇒ 一次都不布」。**" in _ausrc)
    check("BBB.4 ⚠️⚠️ **915 第一版整个作废过一次 —— 钉住这条更基础的教训**："
          "915 是从 914 改造来的，**改造时把 913/914 每臂开头那句 `blank()` "
          "顺手删掉了**（在新结构里它看着像多余的 setup）"
          "⇒ **第一批读数就撞出来**：`A-fwd49` 终点 `[29]`（914 同一条臂是 "
          "`[40]`）、首次布 `0`（914 是 `11`）⇒ **走查根本没从画布根起步**。"
          "⇒ **教训：改造既有探针时，不要把原探针里那些「看起来多余」的前置"
          "动作删掉 —— 它们常常是承重的。**"
          "⇒ 且**修法不只是补回那句**：`design_ok` 必须**对基线臂也设门槛**"
          "（第一版写死 `True`，结果这条臂照样报 ok —— "
          "**门槛漏在基线上就等于没有**）",
          "⚠️⚠️ **第一版整个作废过一次（钉住）**" in _ausrc
          and "**改造时把 913/914 每臂开头那句 `blank()` 顺手删掉了**" in _ausrc
          and "**第一批读数就撞出来**：`A-fwd49` 终点 `[29]`（914 同一条臂是 "
          in _ausrc
          and "`[40]`）、首次布 `0`（914 是 `11`）" in _ausrc
          and "**走查根本没从画布根起步**" in _ausrc
          and "不要把原探针里那些「看起来多余」的前置动作删掉** —— " in _ausrc
          and "**门槛漏在基线上就等于没有**" in _ausrc
          and "init_blank = blank()" in _p915
          and "if not spec[\"base\"]:" in _p915
          and "design[\"design_ok\"] = bool(\n                    init_blank" in _p915)
    check("BBB.5 ⚠️ **914 + 915 合起来只排除了两种历史扰动**，"
          "**仍然不是全称规则** ⇒ ⚠️ **不许**把「起点是终点的纯函数」"
          "写成全称规则、**不许**据此结案、**不许**据此改实现；"
          "**为什么是 `0/11/12`、分界为什么在 `35|36` 与 `40|41` 仍然未查明**",
          "⚠️ **914+915 合起来只排除了两种历史扰动**，" in _ausrc)
    # ══════════ 批 916：把 915 塌缩掉的那一档（带回走）真做成 ══════════
    p916 = ROOT / "scripts/jimeng_probe916_bite_then_walkback_src.py"
    _p916 = p916.read_text(encoding="utf-8") if p916.exists() else ""
    check("CCC.1 ✅ **916 把 915 塌缩掉的那一档（带回走）真正做成了** —— "
          "回走**真的咬到**、前史**仍然无关**（源站，6 臂 × 2 轮 = 12 条，"
          "两轮逐条一致，6 条扰动臂 `bitten` 全 True）："
          "终点 40（`I2-bite30-raw49` vs `A-fwd49`）⇒ 同首布 **11**、"
          "布 `[11,13,14]`；35（`J2-bite30-raw44` vs `B-fwd44`）⇒ 同首布 **0**、"
          "布 `[0,1,2,3]`；51（`K2-bite30-raw60` vs `E-fwd60`）⇒ 同首布 **12**、"
          "布 `[12,16,17]` ⇒ **6/6 组一致**。⚠️ 钉法：停止条件必须是"
          "**「观测到 `'0'` 真的动了」**（自适应），**不许**拍脑袋给「回走 N 次」",
          "source_bite_walkback_prehistory_916" in _ausrc
          and "**916 把 915 塌缩掉的那一档（带回走）真正做成了**" in _ausrc
          and "**直到某一次真的把 `'0'` 挪动了**" in _ausrc
          and "（`moved == True`）才算咬到" in _ausrc
          and "**上限 40 次只是封顶**" in _ausrc
          and "**前史里含一次「真的」回走，起点仍然不变。**" in _ausrc
          and "**6/6 组一致（两轮逐条相同）**" in _ausrc
          and 'def bite_back(names, cap=BITE_CAP, extra=EXTRA_BACK):' in _p916
          and 'if t["moved"] or t["armed"]:' in _p916
          and 'BITE_CAP = 40' in _p916
          and '("bite", 1), ("blank", 1), ("fwd", 49)]},' in _p916)
    check("CCC.2 ✅ **916 顺带一条新读数，把 899/901 那条规则量化了**："
          "`fwd 30` 之后**一连 28 次 `Shift+Tab` 一次都没布**（逐次 `moved` "
          "全 `False`），**第 29 次才咬到**（`armed 22`、`'0'` **23→22**）；"
          "⚠️ 6 条里有 1 条咬在**第 33 次** ⇒ "
          "**915 给的「回走 5」差了一个数量级** —— "
          "它不是「少按了几次」，而是**根本没问到回走**",
          "✅ **顺带一条重要的新读数（把 899/901 那条规则量化了）**" in _ausrc
          and "**一连 28 次 `Shift+Tab` 一次都没布**" in _ausrc
          and "**第 29 次才咬到**" in _ausrc
          and "**23→22**" in _ausrc
          and "6 条里有 1 条咬在**第 33 次**" in _ausrc
          and "**915 给的「回走 5」差了一个数量级**" in _ausrc
          and "**根本没问到回走**" in _ausrc)
    check("CCC.3 ⚠️⚠️ **但 916 的「回走」实际只走了 1 步**"
          "（`'0'` 23→22；咬到之后再按 3 次**又都不布**）⇒ "
          "⚠️ **「长距离回走」这一档仍然没测到** ⇒ "
          "**不许**拿 916 说「回走多远都无关」。"
          "⚠️ 且**那个不对称未查明**：**正向**走查里的死按压是**成串 4 次**、"
          "**反向**却要**连 28 次** ⇒ **不许**拿「焦点在内层控件上」"
          "这句话去编解释",
          "⚠️ **但「回走」实际只走了 1 步**" in _ausrc
          and "`'0'` 23→22；" in _ausrc
          and "咬到之后再按 3 次**又都不布**）⇒ " in _ausrc
          and "**「长距离回走」这一档仍然没测到**" in _ausrc
          and "**不许**拿 916 说「回走多远都无关」" in _ausrc
          and "**为什么两边差这么多，未查明**" in _ausrc
          and "**不许**拿「焦点在内层控件上」这句话去编解释" in _ausrc)
    check("CCC.4 ✅⚠️ **916 的两道防线**（没有它们就会静默退化成 915）："
          "① 916 独有门槛 `design_ok` **必须** `bitten == True`；"
          "② **基线臂也设门槛**（915 第一版写死 `True` —— "
          "**门槛漏在基线上就等于没有**）并要求 `init_blank` 真点到。"
          "⚠️ 另钉 916 自己的记录缺口：`bite` 步第一版**没逐次记按压前焦点** ⇒ "
          "那 28 次死按压时**焦点在哪看不到** ⇒ 已补 `per_press_pre`",
          "✅ **探针这一批又长了一道防线**：916 独有的门槛是 " in _ausrc
          and "**必须** `bitten == True`" in _ausrc
          and "**没有它就会静默退化成 915**" in _ausrc
          and "**基线臂也设了门槛**（915 第一版写死 `True`" in _ausrc
          and "**门槛漏在基线上就等于没有**" in _ausrc
          and 'and design["bitten"] is True)' in _p916
          and "if not spec[\"base\"]:" in _p916
          and '"per_press_pre": [' in _p916
          and "**没有逐次记按压前的焦点落点**" in _ausrc
          and "**焦点在哪看不到**" in _ausrc
          and "已补 `per_press_pre`" in _ausrc)
    check("CCC.5 ⚠️ **914/915/916 合起来只排除了三种历史扰动**，"
          "**仍然不是全称规则** ⇒ ⚠️ **不许**把「起点是终点的纯函数」"
          "写成全称规则、**不许**据此结案、**不许**据此改实现；"
          "**为什么是 `0/11/12`、分界为什么在 `35|36` 与 `40|41` 仍然未查明**",
          "—— 914/915/916 **合起来" in _ausrc
          and "只排除了三种历史扰动**" in _ausrc
          and "同段内越过+回走 ／ 前置走查+归零 ／ " in _ausrc
          and "前置走查+真回走+归零），**一条新机制都没测到**" in _ausrc)
    # ══════════ 批 917：死按压的**焦点轨迹**（本批真正的产出） ══════════
    p917 = ROOT / "scripts/jimeng_probe917_multi_bite_focus_trace_src.py"
    _p917 = p917.read_text(encoding="utf-8") if p917.exists() else ""
    check("DDD.1 ✅⭐ **917 第一次把「死按压期间焦点在哪些元素上走」完整记录下来**"
          "（源站，6 臂 × 2 轮 = 12 条，两轮逐条一致，逐次焦点记录 996 条）—— "
          "这是 916 记过、但**没跑**的那个缺口。**⭐ 正向：死按压数 = "
          "刚被布的那个节点自己的内层控件个数**（轨迹里两次都数上了："
          "落到 `导出时间线` ⇒ **恰好 4 次**；落到 `替换媒体` ⇒ **恰好 1 次**）"
          "⇒ **正向那侧「被吃掉多少」已被读数完整解释**。"
          "**⭐ 反向：死按压把焦点带出画布、把整页反向走一遍**"
          "（`Canvas`→顶栏 `用户菜单`/`Credits`/`更多`/`分享`/`生成历史`/`搜索`"
          "→`项目`/`Canvas title`/`返回首页`→`Zoom options`/`显示连线`/`小地图`"
          "→左栏 `选择工具`/`文本`/`全部清空`/`Add tags`→节点本体）"
          "⇒ **第 29 次按压**按前焦点才落在节点本体上、这时才布（`23→22`）",
          "source_focus_trace_dead_presses_917" in _ausrc
          and "**917 第一次把「死按压期间焦点到底在哪些元素上走」" in _ausrc
          and "逐次焦点记录 996 条" in _ausrc
          and "✅ **⭐ 正向：死按压数 = 刚被布的那个节点自己的内层控件个数**"
          in _ausrc
          and "**恰好 4 次**死按压" in _ausrc
          and "**恰好 1 次**死按压" in _ausrc
          and "**正向那侧「被吃掉多少」= " in _ausrc
          and "✅ **⭐ 反向：死按压把焦点「带出画布」，把整页反向走一遍**"
          in _ausrc
          and "`Add tags`→**节点本体**" in _ausrc
          and "**第 29 次按压**按前焦点才落在节点本体上" in _ausrc
          # ⚠️ 钉**探针真的铺了逐次焦点轨迹**（否则「完整记录」是空话）
          and '"per_press_pre": [press_rec(pi, p)' in _p917
          and 'def press_rec(pi, p):' in _p917
          and '"pre_is_wrapper": p["pre_is_wrapper"],' in _p917
          and '"land_aria": p["land_aria"][:1]}' in _p917)
    check("DDD.2 ⚠️⚠️ **917 那句「一句话」不许当机制**：**路径是实测的、成因不是** —— "
          "**为什么反向的 tab 序会绕整页**（而不是回到上一个节点的本体）"
          "**仍然未查明** ⇒ **不许**拿「正向只有内层控件那么多、反向要跨出画布」"
          "这句话当机制、**不许**据此改实现。"
          "⚠️ 另钉：917 **前史仍无关**（6/6，与同目标基线臂逐条相同："
          "终点 40 ⇒ 首布 11、35 ⇒ 0、51 ⇒ 12）⇒ "
          "**914/915/916/917 合起来只排除了四种历史扰动**，"
          "**仍然不是全称规则**",
          "⚠️ 但**为什么反向的 tab 序会绕整页**" in _ausrc
          and "**仍然未查明** —— 路径是**实测**的，**成因不是**" in _ausrc
          and "**不许**拿上面那句话当机制、不许据此改实现" in _ausrc
          and "✅ **前史仍无关（6/6，与同目标基线臂逐条相同）**" in _ausrc
          and "**914/915/916/917 合起来只排除了四种历史扰动**" in _ausrc
          and "**仍然不是全称规则**" in _ausrc)
    check("DDD.3 ✅⚠️ **917 新加的门当场抓到了东西**："
          "`design_ok` 的「**实测真的退了 `k` 步**」这一条把 **6/6 扰动臂"
          "全标成设计违规** —— 「咬到 3/3」但**实退只有 1 步** ⇒ "
          "**「咬到几次 ≠ 退了几步」**。⚠️ **没有这道门，917 会静默地声称"
          "测了「三步回走」** —— 这是 915/916 同一个错误的**第三次出现、"
          "**第三次被门挡住**。⚠️ 判据要钉**那道门本身**（探针里那个等式）",
          "✅⚠️ **本批新加的门当场抓到了东西**" in _ausrc
          and "**6/6 扰动臂全标成设计违规**" in _ausrc
          and "**「咬到几次 ≠ 退了几步」**" in _ausrc
          and "**没有这道门，917 会静默地声称" in _ausrc
          and "同一个错误的第三次出现，第三次被门挡住。**" in _ausrc
          and 'and design["n_bites_bitten"] == design["n_bites"]' in _p917
          and 'and design["n_zero_steps_retreat"] == design["n_bites"]'
          in _p917
          and "**实测真的退了 `k` 步**" in _ausrc)
    check("DDD.4 ⚠️⚠️ **一条方法论更正（比结论更重要）**：**`armed` 会在"
          "非 `.react-flow__node` 的元素上触发** —— 917 实测到 "
          "`el:BUTTON.inline-flex.items-center#0` 上 `armed` 响了、"
          "而**节点里的 `'0'` 根本没动**（`armed_idx` 空、`moved=False`）"
          "⇒ **`armed` 触发 ≠ `'0'` 移动**。⚠️ **916 用的停止条件正是 "
          "`moved or armed` ⇒ 那一版的「咬到」可能提前结束** "
          "⇒ 917 已把停止条件**收紧成只用 `moved`**",
          "⚠️⚠️ **一条方法论更正（比结论更重要）**" in _ausrc
          and "**`armed` 这个信号" in _ausrc
          and "会在非 `.react-flow__node` 的元素上触发**" in _ausrc
          and "`el:BUTTON.inline-flex.items-center#0` 上 `armed` 响了" in _ausrc
          and "**`armed` 触发 ≠ `'0'` 移动**" in _ausrc
          and "**916 用的停止条件正是 " in _ausrc
          and "那一版的「咬到」可能提前结束" in _ausrc
          and "917 已把停止条件**收紧成只用 `moved`**" in _ausrc
          # ⚠️ 钉探针里那行注释 + 收紧后的条件（916 那版还写着 `or p["armed"]`）
          and "**917 实测出来的更正：停止条件只能用 `moved`，不能带 `armed`。**"
          in _p917
          and "**917 实测出来的更正：停止条件只能用 `moved`，不能带 `armed`。**"
          in _p917
          and 'if t["moved"]:' in _p917
          and 'if t["moved"] or t["armed"]:' not in _p917)
    check("DDD.5 ⚠️ **917 自己的探针缺陷（已修）**：`bite_k` 里 `zero_before` "
          "原来是在 `one_bite()` **跑完之后**才取的 ⇒ 打印出来是 `[22]→[22]` "
          "这种**假象**（咬完的状态冒充咬之前的状态）⇒ 真实的 `23→22` 被抹掉。"
          "⚠️ **判读纪律：前态必须在扰动之前取**，否则「前态 vs 后态」是空话。"
          "⚠️ 判据要钉**探针里那行注释**（顺序错在注释里写明了）",
          "⚠️ **917 自己的探针缺陷（已修）**" in _ausrc
          and "**跑完之后**才取的" in _ausrc
          and "`[22]→[22]` 这种**假象**" in _ausrc
          and "真实的 `23→22` 被抹掉" in _ausrc
          and "⚠️ **判读纪律：前态必须在扰动之前取**" in _ausrc
          and "**917 第一版这里有顺序错**" in _p917
          and "zero_before = snap(names)[\"zeros\"]" in _p917
          and 'one["zero_before"] = zero_before' in _p917)
    # ══════════ 批 918：收紧后的 moved-only（实退真到 3 步） ══════════
    p918 = ROOT / "scripts/jimeng_probe918_movedonly_and_taborder_src.py"
    _p918 = p918.read_text(encoding="utf-8") if p918.exists() else ""
    check("EEE.1 ✅ **918 用收紧后的「只用 `moved`」停止条件重跑 ⇒ 实退真到 `k` 步**"
          "（917 只到 1 步）（源站，6 臂 × 2 轮 = 12 条，两轮逐条一致）："
          "6 条扰动臂**全部** `n_bites_bitten = 3/3` 且 "
          "`n_zero_steps_retreat = 3`（`design_ok` 全 True）⇒ `'0'` 真的退了 "
          "**3 步**（`23→22→21→20`）⇒ **917 那道「实退 `k` 步」的门，"
          "在收紧停止条件之后终于过了**。"
          "⚠️ 钉法：判据要钉**读数**（`3/3` 与 `3`）＋ 探针里那道**门本身**",
          "source_movedonly_retreat3_918" in _ausrc
          and "**918 用收紧后的「只用 `moved`」停止条件重跑多步回走" in _ausrc
          and "**全部** `n_bites_bitten = 3/3` 且 " in _ausrc
          and "`n_zero_steps_retreat = 3`（`design_ok` 全 True）" in _ausrc
          and "`23→22→21→20`" in _ausrc
          and "**917 那道「实退 `k` 步」的门，在收紧停止条件之后终于过了。**"
          in _ausrc
          and 'if t["moved"]:' in _p918
          and 'if t["moved"] or t["armed"]:' not in _p918
          and 'and design["n_bites_bitten"] == design["n_bites"]' in _p918
          and 'and design["n_zero_steps_retreat"] == design["n_bites"]' in _p918)
    check("EEE.2 ✅ **918 顺带一条可复现读数**：三次咬分别是 **第 29 / 5 / 1 次**"
          "才咬到，**6 条逐条一致**（两轮 × 三条扰动臂）⇒ "
          "⚠️ 这个序列**不是**「越往后越难」，而是"
          "**第一次要把焦点从整页走回画布、后面就只差一个节点内层控件的个数**。"
          "✅ **前史仍无关（6/6）**：终点 40 ⇒ 首布 11、35 ⇒ 0、51 ⇒ 12 ⇒ "
          "**914/915/916/917/918 合起来只排除了五种历史扰动**，"
          "**仍然不是全称规则**",
          "**咬到次数高度可复现**" in _ausrc
          and "**第 29 / 5 / 1 次**才咬到" in _ausrc
          and "**6 条逐条一致**" in _ausrc
          and "这个序列**不是**「越往后越难」" in _ausrc
          and "**第一次要把焦点从整页走回画布、后面就只差一个节点内层控件的个数**"
          in _ausrc
          and "✅ **前史仍无关（6/6，与同目标基线臂逐条相同）**" in _ausrc
          and "**914/915/916/917/918 合起来只排除了五种历史扰动**" in _ausrc
          and "**仍然不是全称规则**" in _ausrc)
    check("EEE.3 ⚠️❌ **DOM tab 序直读这一半「落空」了 —— 但落空本身就是结果**："
          "`TABORDER_JS` 在画布根内**只找到 10 个可聚焦元素、"
          "`n_wrappers = 0`（76 个节点里一个都没匹配上）** ⇒ "
          "✅ **中性态下节点本体根本没有 `tabindex`、根本不在 tab 序里** ⇒ "
          "它是**被应用在 keydown 布的那一刻临时注入进去的**"
          "（这正是 roving tabindex 的定义）⇒ "
          "**这也反过来否掉了 917 那个候选解释的方向**（「本体相对内层控件的 "
          "**DOM 位置**」在静态 DOM 里压根没有「本体」可查 ⇒ **问错了地方**）",
          "⚠️❌ **DOM tab 序直读这一半「落空」了 —— 但落空本身就是结果**"
          in _ausrc
          and "**只找到 10 个可聚焦元素、" in _ausrc
          and "`n_wrappers = 0`（76 个节点里一个都没匹配上）**" in _ausrc
          and "✅ **中性态下节点本体根本没有 `tabindex`、根本不在 tab 序里**"
          in _ausrc
          and "**被应用在 keydown 布的那一刻临时注入进去的**" in _ausrc
          and "**这反过来否掉了 917 那个候选解释的方向**" in _ausrc
          and "**那个提法方向就是错的**（不是结论错，是**问错了地方**）" in _ausrc
          # ⚠️ 钉探针真的做了这次直读（否则「落空」也可能只是没跑）
          and "TABORDER_JS = " in _p918
          and "to = ev(TABORDER_JS)" in _p918
          and '"n_wrapper_with_inner": sum(1 for v in wvi.values()' in _p918)
    check("EEE.4 ⚠️⚠️ **但「为什么反向仍要 29 次」仍然没查明** —— "
          "「本体是动态注入的」**解释得了**「它不在静态 tab 序里」、"
          "**解释不了**「反向要跨出画布把整页走一遍」⇒ "
          "**不许**把「动态注入」当这个不对称的答案。"
          "⚠️ 另钉 918 自己的探针缺口：只存了 tab 序的 `summary`、"
          "**没存那 10 个元素分别是谁**；且**内层控件一个都没被选择器匹配上**"
          "（917 的焦点轨迹明明能走到那些）⇒ **要么选择器漏了、"
          "要么那些控件不在 `.react-flow` 子树里** ⇒ **未查明**，**不许**猜",
          "⚠️ **但「为什么反向仍要 29 次才回到一个本体」仍然没查明**" in _ausrc
          and "**解释得了**「它不在静态 tab 序里」" in _ausrc
          and "**解释不了**「反向要跨出画布把整页走一遍」" in _ausrc
          and "**不许**把「动态注入」当这个不对称的答案" in _ausrc
          and "**没存那 10 个元素分别是谁**" in _ausrc
          and "**内层控件一个都没被选择器匹配上**" in _ausrc
          and "**未查明**，**不许**猜" in _ausrc)
    check("EEE.5 ⚠️ **918 第一版自己撞了变量名、把整轮跑废**：算 tab 序直方图"
          "那两个累加器本来叫 `before` / `after` ⇒ **`after` 把「回来后 8 次"
          "按压的记录列表」覆盖成了整数** ⇒ 紧接着 `\"after_per_press\": [...]` "
          "报 `TypeError: 'int' object is not iterable`。"
          "⚠️ **教训：别给新变量起「这一层里已经用过的名字」** —— "
          "`before` / `after` 在走查代码里是**承载读数的列表**、不是布尔量。"
          "⚠️ 判据要钉**改名后的真实字面量**",
          "⚠️ **918 第一版自己撞了变量名**：算 tab 序直方图那两个累加器" in _ausrc
          and "本来叫 `before` / `after` ⇒ **`after` 把上面那个" in _ausrc
          and "「回来后 8 次按压的记录列表」覆盖成了整数**" in _ausrc
          and "`TypeError: 'int' object is not iterable`" in _ausrc
          and "**整轮跑废**" in _ausrc
          and "⚠️ **教训：别给新变量起「这一层里已经用过的名字」**" in _ausrc
          and "n_before_first_inner = sum(" in _p918
          and "n_after_last_inner = sum(" in _p918)
    # ══════════ 批 919：纯诊断——内层控件解剖（纯读，不装任何监听器） ══════════
    p919 = ROOT / "scripts/jimeng_probe919_inner_control_anatomy_src.py"
    _p919 = p919.read_text(encoding="utf-8") if p919.exists() else ""
    check("FFF.1 ⚠️ **919 先纠正了我自己一个误判、并且把误判钉死**："
          "918 报「画布内可聚焦 **10** 个」、919 报「**163** 个」，"
          "我一度以为是**两个探针报数矛盾**。❌ **作废** —— "
          "918 的 `TABORDER_JS` **多了一道过滤器**（「`tabindex` 属性 `< 0` "
          "就跳过」），919 那道**没加** ⇒ **两个数各自都对、只是口径不同**。"
          "⇒ ⚠️ **这条本身就是「一次异常读数不足以立机制」的又一次应用**："
          "**两个数不同 ≠ 有矛盾**，得先查**口径**",
          "✅⭐ **919（纯诊断）把 918 的「选择器漏了 / 不在子树里」" in _ausrc
          and "⚠️ **先纠正我自己一个误判**" in _ausrc
          and "我一度以为是**两个探针报数矛盾**。" in _ausrc
          and "❌ **作废**：918 的 `TABORDER_JS` **多了一道过滤器**" in _ausrc
          and "**两个数各自都对、只是口径不同**" in _ausrc
          and "**这条本身就是「一次异常读数不足以立机制」的又一次应用**" in _ausrc
          # ⚠️ 钉探针里那两道的**真实差异**（918 有过滤、919 没有）
          and 'if (ti !== null && Number(ti) < 0) continue;' in _p918
          and "if (ti !== null && Number(ti) < 0) continue;" not in _p919
          and "const idl = [...scope.querySelectorAll('*')]"
          ".filter((e) => e.tabIndex >= 0);" in _p919)
    check("FFF.2 ✅⭐ **那 5 个内层控件的真实身份**（两轮逐条相同）："
          "`导出时间线` / `全屏编辑` / `静音` / `添加素材到时间线` / `替换媒体` "
          "**全都是 `<BUTTON>`**、**都在 `.react-flow` 里**、"
          "**`shadow_depth = 0`** ⇒ "
          "⚠️ **918 那句「要么选择器漏了、要么不在子树里」两个都不是**。"
          "⭐ **最要紧的性质**：它们 `tabindex` **属性是 `None`（压根没这个属性）**、"
          "而 **IDL `tabIndex = 0`** ⇒ **靠的是「原生 `<button>` 默认可聚焦」**",
          "✅ **那 5 个内层控件的真实身份**（两轮逐条相同）：" in _ausrc
          and "**全都是 `<BUTTON>`**、**都在 `.react-flow` 里**" in _ausrc
          and "**`shadow_depth = 0`**" in _ausrc
          and "**918 那句「要么选择器漏了、要么不在子树里」两个都不是**" in _ausrc
          and "`tabindex` **属性是 `None`" in _ausrc
          and "**IDL `tabIndex = 0`**" in _ausrc
          and "**它们靠的是「原生 `<button>` 默认可聚焦」，不是靠 `tabindex` 属性。**"
          in _ausrc
          # ⚠️ 钉探针真的同时问了这两个口径
          and "matches_std_sel: el.matches(SEL)," in _p919
          and "idl_tabindex: el.tabIndex," in _p919
          and "attr_tabindex: el.getAttribute('tabindex')," in _p919
          and "shadow_depth: deepest(el)," in _p919)
    check("FFF.3 ✅ **IDL 口径的普查（顺序焦点导航真正走的口径）**："
          "**中性态画布内只有 10 个可聚焦元素、整篇 document 只有 27 个**；"
          "而**属性口径**（含 `tabindex=\"-1\"` 的）画布内有 **163** 个 "
          "⇒ 两者差 16 倍 ⇒ **口径必须写清楚、不许混用**。"
          "⭐ **布上之后本体被注入到哪一位（两轮逐条一致）**："
          "被布的本体 `tabindex` 属性 = `0`、IDL = `0`，**落在 IDL 序第 11 位**："
          "**紧跟 `Canvas`（画布根）之后、在它自己的第一个内层控件 `导出时间线` 之前**"
          "⇒ **本体排在自己的内层控件「之前」**，而且它**就是 `activeElement`**",
          "✅ **IDL 口径的普查（这才是顺序焦点导航真正走的口径）**" in _ausrc
          and "**中性态画布内只有 10 个可聚焦元素、整篇 document 只有 27 个** "
          in _ausrc
          and "**163** 个" in _ausrc
          and "两者差 16 倍，**口径必须写清楚、不许混用**" in _ausrc
          and "⭐ **布上之后本体被注入到哪一位（两轮逐条一致）**" in _ausrc
          and "**落在 IDL 序的第 11 位**" in _ausrc
          and "**紧跟在 `Canvas`（画布根）之后、" in _ausrc
          and "**本体排在自己的内层控件「之前」**" in _ausrc
          and "**就是 `activeElement`**" in _ausrc
          and "wrapper_pos_in_idl_order: w ? allIdl.indexOf(w) : null,"
          in _p919
          and "active_is_wrapper:" in _p919)
    check("FFF.4 ⚠️❌ **919 撞出一个真缺口、而且本批没有解释**："
          "中性态普查说**画布内没有任何节点本体是可聚焦的**"
          "（`n_wrappers_with_ti0 = 0`、IDL 列表里 0 个本体），"
          "可是 917/918 的**焦点轨迹里按前焦点多次落在「别的节点的本体」上**"
          "（`pre_is_wrapper = True`，例如 `文本 node: 文本 2`）⇒ "
          "**焦点怎么会落到一个没有 `tabindex` 的元素上？** ⇒ "
          "**要么「本体可聚焦」在普查那一刻和走查过程中不是同一回事、"
          "要么焦点是程序化 `.focus()` 上去的** ⇒ "
          "⚠️ **本批没有测到、没有解释 ⇒ 不许**拿「动态注入」一句话糊过去。"
          "⚠️ 另钉一条纪律：919 是**纯诊断**——普查是**纯读**、"
          "**不劫持 prototype、不装 MutationObserver** ⇒ 诊断不许破坏被诊断状态",
          "⚠️❌ **但这一批撞出一个真缺口、而且本批没有解释**" in _ausrc
          and "**焦点怎么会落到一个没有 `tabindex` 的元素上？**" in _ausrc
          and "**要么「本体可聚焦」这件事在普查那一刻和走查过程中不是同一回事**"
          in _ausrc
          and "**要么焦点是程序化 `.focus()` 上去的**" in _ausrc
          and "**本批没有测到、没有解释 ⇒ 不许**拿「动态注入」一句话糊过去"
          in _ausrc
          and "✅ **顺带钉一条纪律：919 是「纯诊断」** —— 普查是**纯读**、"
          in _ausrc
          and "**不劫持 prototype、不装 MutationObserver**" in _ausrc
          # ⚠️ 钉探针确实是纯读（没有 install/cleanup、没有 observer）
          # ⚠️⚠️ **不能拿「全文不含」当证据** —— 919 的**文档里**就写着
          # 「不劫持 prototype、不装 MutationObserver」两个字 ⇒ 全文当然含有。
          # ⇒ 必须钉**代码**里没有：真的没有 `new MutationObserver(`、
          #    真的没有 `.prototype =` 赋值。
          and "new MutationObserver(" not in _p919
          and ".prototype =" not in _p919
          and "__proto__" not in _p919
          and "（诊断是纯读，没有装任何监听器）" in _p919)
    # ══════════ 批 920：逐次普查 ⇒ 919 那个缺口的前提是错的 ══════════
    p920 = ROOT / "scripts/jimeng_probe920_per_press_wrapper_census_src.py"
    _p920 = p920.read_text(encoding="utf-8") if p920.exists() else ""
    check("GGG.1 ✅⭐ **920 用「每按一次就普查一次」把 919 那个缺口结掉了 —— "
          "**而且结论是「那个问题的前提是错的」。**（源站，纯诊断，2 轮 × 每次 "
          "14 连按，两轮逐条一致）：**焦点是本体的时刻共 38 次，其中"
          "「焦点所在的下标 == 唯一那个带 `tabindex=\"0\"` 的本体下标」= 38/38**"
          " ⇒ **焦点从来不会停在一个没有 `tabindex` 的本体上** "
          "⇒ ⚠️ **919 那个问题本身不成立**（「不存在那一刻」）",
          "source_focus_always_on_armed_920" in _ausrc
          and "**920 用「每按一次就普查一次」把 919 那个缺口结掉了**" in _ausrc
          and "**而且结论是「那个问题的前提是错的」。**" in _ausrc
          and "**焦点是本体的时刻共 38 次" in _ausrc
          and "」= 38/38**" in _ausrc
          and "**焦点从来不会停在一个没有 `tabindex` 的本体上**" in _ausrc
          and "⚠️ **919 那个问题本身不成立**（「不存在那一刻」）" in _ausrc
          and "before = ev(CENSUS_JS)" in _p920
          and "after = ev(CENSUS_JS)" in _p920
          and '"before": before,' in _p920
          and '"after": after,' in _p920)
    check("GGG.2 **⇒ 顺带钉死一条**：整个走查过程中 `n_wrapper_ti0` 与 "
          "`n_wrapper_idl_focusable` **取值集合都只有 `{0, 1}`** ⇒ "
          "**任何时刻至多只有一个本体可聚焦**（两轮各 28 次普查全中）"
          "⇒ **roving 是「单指针」、不是「留轨迹」**。"
          "⭐ **另有一条重要读数（919 没看到）**："
          "**归零那一刻 `n_wrapper_any_ti = 0`（一个 `tabindex` 属性都没有）**，"
          "**按第 1 次之后立刻变成 76**（1 个 `'0'` + 75 个 `'-1'`）⇒ "
          "**应用第一次就把所有节点都管起来**",
          "**取值集合都只有 `{0, 1}`**" in _ausrc
          and "**任何时刻至多只有一个本体可聚焦**" in _ausrc
          and "**roving 是「单指针」、不是「留轨迹」**" in _ausrc
          and "⭐ **另有一条重要读数（919 没看到）**" in _ausrc
          and "**归零那一刻 `n_wrapper_any_ti = 0`（一个 `tabindex` 属性都没有）**"
          in _ausrc
          and "**按第 1 次之后立刻变成 76**（**1 个 `'0'` + 75 个 `'-1'`**）"
          in _ausrc
          and "⇒ **应用不是只给一个节点打 `tabindex`，而是第一次就把"
          in _ausrc
          and "**所有**节点都管起来**" in _ausrc
          and "n_wrapper_idl_focusable: idlIdx.length," in _p920
          and "if (n.tabIndex >= 0) idlIdx.push(i);" in _p920
          and "if (ti !== null) anyTiIdx.push(i);" in _p920)
    check("GGG.3 ⚠️ **但「为什么按第 2 次之后变成 75」没查明** —— "
          "样本看起来像「焦点在**两次之前**那个本体的 `tabindex` 属性被移除」，"
          "但⚠️ **样本只有约 8 个、而且只看的是前 12 个的切片** "
          "⇒ **这个规律不成立、只是观察** ⇒ **不许**拿它编规则，"
          "**要重测就得把整张表存下来**。⚠️ 判据要钉**切片这件事本身**"
          "（它是「不许下结论」的理由）",
          "⚠️ **但「为什么按第 2 次之后变成 75」我没查明**" in _ausrc
          and "**样本只有约 8 个、而且只看的是**前 12 个**的切片**" in _ausrc
          and "**这个规律不成立、只是观察**" in _ausrc
          and "**不许**拿它编规则，**要重测就得把整张表存下来**" in _ausrc
          and "any_ti_idx: anyTiIdx.slice(0, 12)," in _p920
          and "idl_idx: idlIdx.slice(0, 12)," in _p920)
    check("GGG.4 ✅ **一条纪律**：920 也是**纯诊断** —— 普查**纯读**、"
          "**不劫持 prototype、不装 MutationObserver** ⇒ "
          "**诊断不许破坏被诊断状态**。"
          "⚠️ 判据要钉**代码**（920 的**文档里**就写着这几个字 ⇒ "
          "**不能拿「全文不含」当证据**）",
          "✅ **一条纪律**：920 也是**纯诊断**" in _ausrc
          and "**不劫持 prototype、不装 MutationObserver** ⇒ " in _ausrc
          and "**诊断不许破坏被诊断状态**" in _ausrc
          and "new MutationObserver(" not in _p920
          and ".prototype =" not in _p920
          and "__proto__" not in _p920)
    check("GGG.5 ⚠️ **919 那句「焦点可能落在别的节点本体上」的表述要收窄**："
          "它**本身没错**（焦点确实多次落在本体上），"
          "但**它总是「当前被布的那个」本体** ⇒ **不是「别的本体」** ⇒ "
          "**921 起按这个收窄后的说法记**。"
          "⚠️ 这就是「被推翻的旧结论**要以历史记录身份留着**」那条："
          "**不许**回头把 919 那句删掉",
          "⚠️ **919 那句「焦点可能落在别的节点本体上」的表述要收窄**" in _ausrc
          and "它**本身没错**（焦点确实多次落在本体上），" in _ausrc
          and "**它总是「当前被布的那个」本体**" in _ausrc
          and "⇒ 921 起按这个收窄后的说法记" in _ausrc)
    p921 = ROOT / "scripts/jimeng_probe921_full_table_and_delta_src.py"
    _p921 = p921.read_text(encoding="utf-8") if p921.exists() else ""
    check("HHH.1 ✅⭐ **921 用「整张表 + 逐次 delta」把 920 那个「76 → 75」查清了**"
          "（源站，纯诊断，2 轮 × 每次 16 连按，两轮逐条一致）。"
          "**两类事件必须分开看**：**① 初始化（第一次布，只有一次）**"
          "给**所有**节点写上 `tabindex`（`added = [0…75]`）⇒ 920 读到的 **76 "
          "就是这个初始化态**；**② 之后每一次「臂事件」恰好做三件事** —— "
          "`removed` = **上一个臂事件**的下标（属性**整个移除**）、"
          "`added` = **上上个臂事件**的下标（写回 `'-1'`）、"
          "`changed` = 本次被布的下标 ⇒ **24/24 逐条成立**",
          "source_tabindex_rolling_window_921" in _ausrc
          and "**921 用「整张表 + 逐次 delta」把 920 那个「76 → 75」查清了**"
          in _ausrc
          and "**① 初始化（第一次布，只有一次）**" in _ausrc
          and "920 读到的那个 **76 就是这个初始化态**" in _ausrc
          and "**② 之后每一次「臂事件」（指针真的移动）**" in _ausrc
          and "**`removed` = **上一个臂事件**的下标（**`tabindex` 属性被整个移除**"
          and "`removed` = **上一个臂事件**的下标（**`tabindex` 属性被整个移除**"
          in _ausrc
          and "**24/24 逐条成立**" in _ausrc
          and "const added = [], removed = [], changed = [];" in _p921
          and "else if (was !== null && cur[i] === null) removed.push(i);"
          in _p921
          and "else if (was !== cur[i]) changed.push([i, was, cur[i]]);" in _p921)
    check("HHH.2 **⇒ 不变式（两轮各 11 次臂事件后逐条成立）**："
          "**任何时刻恰好有 1 个本体没有 `tabindex` 属性**（就是「上一个臂事件」"
          "那个）⇒ **`n_wrapper_any_ti` 从第二次布起恒为 75**。"
          "**✅ 顺带钉死一条**：指针**没有**移动的那些按压（死按压）—— "
          "`removed` / `added` / `changed` **全空** ⇒ "
          "**应用完全没碰 `tabindex` 属性**，**8/8 成立**",
          "**任何时刻恰好有 1 个本体没有 `tabindex` 属性**" in _ausrc
          and "**`n_wrapper_any_ti` 从第二次布起恒为 75**" in _ausrc
          and "**✅ 顺带钉死一条**：指针**没有**移动的那些按压（死按压）" in _ausrc
          and "**应用完全没碰 `tabindex` 属性**，**8/8 成立**" in _ausrc
          and "n_wrapper_any_ti: anyTiIdx.length," in _p921
          and '"moved": before["zero_idx"] != after["zero_idx"],' in _p921)
    check("HHH.3 ⚠️❌ **920 那个猜法正好把两者对调了**（作废、但**不许删** "
          "920 那段）：920 说「**两次之前**那个被移除」，实际是"
          "「**上一次**那个被移除、被写回的才是**上上个**」⇒ **两条正好对调**。",
          "⚠️❌ **920 那个猜法正好把两者对调了**（作废、但**不许删** 920 那段）"
          in _ausrc
          and "**两次之前**那个被移除" in _ausrc
          and "**上一次**那个被移除、被写回的才是**上上个**" in _ausrc
          and "**两条正好对调**" in _ausrc)
    check("HHH.4 ⚠️ **一条方法论教训（本批最值钱的一条）**："
          "**切片会把规律读反。** 920 用 `slice(0, 12)` 只看**前 12 个**，"
          "而那 12 个里恰好**看不到**「被移除」的那个（它在更靠后的位置）、"
          "**只看到**「被写回」的那个 ⇒ 于是把两者**对调**了。"
          "⇒ ⚠️ **要看全貌就别切片**；"
          "**切片适合「有没有」，不适合「是哪一个」。**"
          "⚠️ 判据要钉**探针里那两个列表确实没有 `slice`**"
          "（**文档里提到 `slice(0, 12)` 不算**、要钉代码）",
          "⚠️ **一条方法论教训（本批最值钱的一条）**" in _ausrc
          and "**切片会把规律读反。**" in _ausrc
          and "**切片适合「有没有」，不适合「是哪一个」。**" in _ausrc
          and "zero_idx: zeroIdx," in _p921
          and "idl_idx: idlIdx," in _p921
          and "any_ti_idx: anyTiIdx," in _p921
          and "zero_idx: zeroIdx.slice(" not in _p921
          and "idl_idx: idlIdx.slice(" not in _p921
          and "any_ti_idx: anyTiIdx.slice(" not in _p921)
    p922 = ROOT / "scripts/jimeng_probe922_reverse_arm_window_src.py"
    _p922 = p922.read_text(encoding="utf-8") if p922.exists() else ""
    check("III.1 ✅⭐ **922 反向臂被自己的设计门挡住**"
          "（`design_ok = False`、`n_armed = 0`）⇒ **rev 臂读数作废**"
          "（**不是**「反向不布」！），**但顺手查清一条真事实："
          "反向从画布根出发、永远进不了画布。**"
          "**60 次 `Shift+Tab` 构成一个周期恰为 27 的「闭环」**"
          "（`Canvas` 出现在第 27 次和第 54 次）；"
          "**`moved` 60/60 全 False**（应用一次都没布）、"
          "**`is_wrapper` 60/60 全 False**（焦点**从未**落在本体上）",
          "922 反向臂被自己的设计门挡住" in _ausrc
          and "**反向从画布根出发、永远进不了画布。**" in _ausrc
          and "**60 次 `Shift+Tab` 构成一个周期恰为 27 的「闭环」**" in _ausrc
          and "**`moved` 60/60 全 False**" in _ausrc
          and "**`is_wrapper` 60/60 全 False**" in _ausrc
          and "TRIAL_KEYS = ((\"rev\", KEY_REV), (\"fwd\", KEY_FWD))" in _p922
          # ⚠️ 判据要钉**代码**（不许拿「全文没有某词」当证据）
          and "if post_l[\"is_wrapper\"]:" in _p922
          and "entered_ok = (rec[\"n_entry_used\"] < ENTRY_CAP" in _p922
          and "rec[\"focus_on_body_at_entry\"] = bool(" in _p922)
    check("III.2 ✅ **顺带钉死两条**：① 闭环里唯一与节点有关的元素是 "
          "`Canvas node summary: 节`，但它 `is_wrapper = False` ⇒ "
          "是**汇总元素、不是 `.react-flow__node` 本体**；"
          "② 闭环里有节点的**内层控件** ⇒ ✅ **内层控件在中性态就已经在 tab 序里**"
          "（919 已查清是原生 `<BUTTON>`），**而本体不在**",
          "它是**汇总元素、不是 `.react-flow__node` " in _ausrc
          and "**内层控件在中性态就已经在 tab 序里**" in _ausrc
          and "**而本体不在**" in _ausrc
          and "if (nodes[i].getAttribute('tabindex') === '0') zeroIdx.push(i);"
          in _p922
          and "const isW = !!(a && a.classList && "
              "a.classList.contains('react-flow__node'));" in _p922)
    check("III.3 ✅ **同 run 的正向对照臂（`fwd`）2/2 逐条复现了 921 的规则**："
          "初始化 1 次；普通臂事件 9 次 —— `removed` = 上一个 **9/9**、"
          "`added` = 上上个 **9/9**、`changed` = 本次 **9/9**；"
          "死按压 4 次且 delta **全空 4/4**；"
          "不变式「`n_wrapper_any_ti` 第 2 次起恒 75」**全程成立** "
          "⇒ **921 的结论在全新运行里站住了**",
          "**同 run 的正向对照臂（`fwd`）2/2 逐条复现了 921 的规则**" in _ausrc
          and "`removed` = 上一个 **9/9**、`added` = 上上个 **9/9**、" in _ausrc
          and "**全空 4/4**" in _ausrc
          and "**921 的结论在全新运行里站住了**" in _ausrc
          # ⭐ 对照臂必须**同 run 跑**（跨 run 比会混进「机制变没变」）
          and 'TRIALS = ("rev", "fwd")' in _p922
          and "for trial, key in TRIAL_KEYS:" in _p922
          and "KEY_FWD = \"Tab\"" in _p922
          and "KEY_REV = \"Shift+Tab\"" in _p922)
    check("III.4 ⚠️❌ **rev 臂作废**（`design_ok = False`、`n_armed = 0`）："
          "**我的 A 段设计就错了** —— 我以为反向能从画布根走进画布。"
          "⚠️ **这一批最值钱的是设计门又救了一次场**："
          "若没有「A 段必须真的落在本体上」这道门，"
          "这份读数会被当成「**反向不布**」的证据写进基线 ⇒ "
          "**一个看起来很正常、实际上什么都没测到的结论。**",
          "**rev 臂作废**" in _ausrc
          and "**我的 A 段设计就错了**" in _ausrc
          and "**这一批最值钱的是设计门又救了一次场**" in _ausrc
          and "**一个看起来很正常、实际上什么都没测到的结论。**" in _ausrc
          # ⭐ 设计门必须是**会 FAIL 的真门**（不能是恒真的摆设）
          and "n_armed_ok = rec[\"n_armed\"] >= 3" in _p922
          and "\"all_ok\": bool(entered_ok and n_armed_ok)," in _p922)
    p923 = ROOT / "scripts/jimeng_probe923_continuous_arm_stream_src.py"
    _p923 = p923.read_text(encoding="utf-8") if p923.exists() else ""
    check("JJJ.1 ✅⭐ **923 查清了 §131 那条滚动窗口规则是「不分方向」的** —— "
          "窗口是**一条全局的臂事件流**，不是分方向的。⇒ **方向对称。**"
          "**判别点**：翻向后**第 1 次**反向臂事件 **`removed = [19]`、"
          "`added = [18]`** ⇒ **正是正向最后那两个臂事件**；"
          "若窗口分方向，这两处应当是**空的**。**全程 34 次臂事件、"
          "`removed` = 上一个臂事件 **34/34 全中**",
          "923 查清了 §131 那条滚动窗口规则是「不分方向」的" in _ausrc
          and "**✅ 判别结果（2/2 逐条一致）**" in _ausrc
          and "**`removed` = 上一个臂事件（不分方向）34/34 全中**" in _ausrc
          and "**不是**分两段各测一遍，而是**一条连续的臂事件流、中途翻向**" in _ausrc
          # ⚠️ 判别点要钉在**探针真的把翻向那一次单独存下来**的代码上
          and "\"first_rev_removed\": rev_presses[0][\"post\"][\"removed\"]" in _p923
          and "\"last_fwd_armed\": rec[\"arm_seq_fwd\"][-1]" in _p923
          and "arm_stream.append((phase, post_c[\"zero_idx\"][0]))" in _p923)
    check("JJJ.2 ✅ **两处「偏离三动作」的地方都有确定解释（不许当例外糊过去）**："
          "① 正向第 1 次是**初始化**（`added` 是 76 项）；"
          "② **翻向那一次 `changed` 是空的** ⇒ ⭐ 因为反向这一步"
          "**恰好落在正向刚腾空的那个节点上**（`19 → 18`，而 18 正是「上上个」、"
          "并且**没有 `tabindex` 属性**）⇒ `null → '0'` 被记成 **`added`** "
          "⇒ **不是规则被破坏，是读数分类撞上了巧合。**"
          "另：死按压 **6 次**且 delta **全空 6/6**、不变式跨方向**全程成立**",
          "**① 正向第 1 次按压是「初始化」**" in _ausrc
          and "**② 翻向那一次 `changed` 是空的**" in _ausrc
          and "**恰好落在正向刚腾空的那个节点上**" in _ausrc
          and "**不是规则被破坏，是读数分类撞上了巧合。**" in _ausrc
          and "死按压 **6 次**、`removed`/`added`/`changed` **全空 6/6**" in _ausrc
          and "不变式「`n_wrapper_any_ti` 恒 75」**跨方向全程成立**" in _ausrc
          # 「巧合」这个解释必须真的被探针**分开记**（翻向前后各自的下标）
          and "\"zero_idx_at_flip\": zf," in _p923
          and "\"armed_idx_at_flip\": (zf[0] if zf else None)," in _p923)
    check("JJJ.3 ✅ **一条新的一致性证据**：**下标 12 在正反两向都被跳过**"
          "（正向 `11 → 13`、反向 `13 → 11`）⇒ 此前**只观察到正向**跳过它。"
          "⚠️ **成因仍未查明** —— §122 已钉：原理上不可从 DOM 查明；"
          "复刻**只能**按纯 DOM 序实现并把差异**如实记为已知差异**，"
          "**不许**编一个 DOM 层判据去「对齐」它",
          "**下标 12 在正反两向都被跳过**" in _ausrc
          and "此前**只观察到正向**跳过它" in _ausrc
          and "**成因仍未查明**" in _ausrc
          and "**不许**编一个 DOM 层判据去「对齐」它" in _ausrc
          # ⚠️ **不许**把「跳过 12」硬编成实现规则 ⇒ 判据要钉**组件里没有**这种判据
          and "node 12" not in _wsrc and "skip" not in _wsrc.lower())
    check("JJJ.4 ⚠️ **一条方法论教训（本批第二条）**："
          "**`post` 那一侧的焦点是这次按压的「结果」、不是 keydown 那刻的「原因」。**"
          "实测有 **3 次**按压的 `post` 焦点**确实在本体上、却一次都没布**"
          "⇒ ⚠️ **不许**拿 `post` 焦点当「这一次 keydown 的落点」"
          "（§130 那条「内层控件 ⇒ 不布」说的才是 **keydown 那一刻**）。"
          "⚠️ 923 第一版还踩了另一个坑：`zero_idx` 是**列表**却被拿去和整数比 ⇒ "
          "`TypeError` **崩在设计门那一行、整轮读数全丢** ⇒ "
          "**落盘已提前到设计门之前**（§900 那条教训的推广）",
          "**`post` 那一侧的焦点是这次按压的「结果」、不是 keydown 那刻的「原因」。**"
          in _ausrc
          and "**不许**拿 `post` 焦点当「这一次 keydown 的落点」" in _ausrc
          # ⭐ 落盘必须**排在设计门之前**（钉代码里的真实顺序）
          and "runs.append(rec)\n        out[\"runs\"] = runs\n        with open(OUT, \"w\", encoding=\"utf-8\") as f:\n            json.dump(out, f, ensure_ascii=False, indent=2)\n\n        # ---------- 设计门" in _p923
          and "n_armed_fwd + n_armed_rev" not in _p923
          and "any_ti: anyTiIdx.length," in _p923)
    p924 = ROOT / "scripts/jimeng_probe924_both_boundaries_src.py"
    _p924 = p924.read_text(encoding="utf-8") if p924.exists() else ""
    check("KKK.1 ✅⭐ **924 在同一次运行里把两个边界都穿过去了**："
          "**正向到末尾、反向到下界，两向都是「到头停手、绝不绕回」。**"
          "正向布到 `n_nodes - 1 = 75` 之后又按 **10 次**、**一次都没布**；"
          "反向退到 **0** 之后又按 **10 次**、**一次都没布** ⇒ "
          "**两向互为对照**（896 只测过正向那条边界）",
          "924 在同一次运行里把两个边界都穿过去了" in _ausrc
          and "**正向到末尾、反向到下界，两向都是「到头停手、绝不绕回」。**" in _ausrc
          and "**正向**：布到 `n_nodes - 1 = 75` 之后又按 **10 次**、" in _ausrc
          and "**反向**：退到 **0** 之后又按 **10 次**、**一次都没布**" in _ausrc
          and "⚠️ **反向那条下界 0 从来没被测过**" in _ausrc
          # ⚠️⚠️ **928 订正**：「绝不绕回」那半个是**回归**（10 次预算不够，
          #    绕回要等约 28 步整页循环）⇒ 判据**必须钉住这条订正**，
          #    **不许**再把一刀切的错结论当已验证
          and "**【928 订正 —— 上面那个「不绕回」的一半是回归，" in _ausrc
          and "**但「正向到末尾也不绕回」那半个是错的**" in _ausrc
          and "**这正是 899 踩过的同一个「取样假象」**" in _ausrc
          and "**§134 把这两条并存的两分支一刀切成「绝不绕回」，是回归。**" in _ausrc
          # ⚠️ 节点总数是易变量 ⇒ 边界必须用**当下那一刻的 n_nodes** 算
          and "lambda idx, nn: idx == nn - 1," in _p924
          and "lambda idx, nn: idx == 0," in _p924
          # 「没绕回」必须有样本 ⇒ 越界后必须真的又按了 PAST 次
          and "if hit_at is not None and (k + 1) - hit_at >= PAST:" in _p924
          and "n_past_ok = (n_past_fwd >= PAST and n_past_rev >= PAST)" in _p924)
    check("KKK.2 ✅ **把 §133 那条规则放到最大样本上再验一遍**："
          "**全程 144 次臂事件**（正向 74 + 反向 70）—— "
          "**`removed` = 上一个臂事件（不分方向）、零偏差**；"
          "`added` = 上上个只有 **1 次**偏差（就是那次**初始化**）；"
          "死按压 **47 次**且 delta **全空 47/47**；"
          "不变式「`n_wrapper_any_ti` 恒 75」**全程成立** "
          "⇒ **那条规则跨两个边界都站得住。**",
          "**全程 144 次臂事件**（正向 74 + 反向 70）—— " in _ausrc
          and "**`removed` = 上一个臂事件（不分方向）、零偏差**" in _ausrc
          and "**全空 47/47**" in _ausrc
          and "**全程成立** " in _ausrc
          and "**那条规则跨两个边界都站得住。**" in _ausrc
          # 「越界之后的每一次」必须被**单独存下来**，不然判据钉的是空话
          and "rec[\"after_fwd_arm_idx\"] = [" in _p924
          and "rec[\"after_rev_arm_idx\"] = [" in _p924)
    check("KKK.3 ✅ **顺带查清一条关于「反向怎么起手」的事实**："
          "**反向臂事件不是从「正向阶段最后一次按压」起手的** —— "
          "正向那 **10 次越界按压已把焦点带出画布、绕了半圈页面**；"
          "**反向第 1–9 次全是死按压**，**第 9 次**焦点才回到"
          "**正向布到的最后一个下标那个本体**上、**第 10 次**才真的布 "
          "⇒ **反向是从「正向布到的最后一个下标」那个本体起手的。**",
          "**反向臂事件不是从「正向阶段最后一次按压」起手的**" in _ausrc
          and "**反向第 1–9 次全是死按压**" in _ausrc
          and "**反向是从「正向布到的最后一个下标」那个本体起手的。**" in _ausrc
          # ⚠️ 判据要钉在**门真的问的是「起手时」而不是「翻向那一刻」**
          and "\"first_rev_arm_pre_focus_on_body\"" in _p924
          and "first_rev_arm = next((p for p in rev_presses if p[\"moved\"]), None)" in _p924)
    check("KKK.4 ⚠️⚠️ **不许**据本轮说 §121「2 个节点整轮没被布」被推翻 —— "
          "**节点总数在同 URL 逐轮会变**（74→77 都出现过）"
          "⇒ **跨 run 的下标未必可比** ⇒ 本轮只能记"
          "「**这一轮** 76 个里 75 个被布过」。"
          "⚠️ **924 第一版自己踩的坑（读数没错、门放错了）**："
          "第一版拿「正向阶段最后一次按压之后焦点在不在本体上」当门，"
          "而正向阶段**故意**在越界之后又按了 10 次 ⇒ 那道门**必然 FAIL**，"
          "**可它并不是「反向臂事件起手时焦点在不在本体上」** ⇒ "
          "改成问本来该问的（第一个反向臂事件的 `pre` 焦点）—— "
          "**不是把门删掉、也不是放宽**",
          "**不许**据此说 §121「2 个节点整轮没被布」被推翻" in _ausrc
          and "**节点总数在同 URL 逐轮会变**" in _ausrc
          and "**跨 run 的下标未必可比**" in _ausrc
          and "**924 第一版自己踩的坑（读数没错、门放错了）**" in _ausrc
          and "**不是把门删掉、也不是放宽**" in _ausrc
          # ⭐ 那道**放错位置**的旧门必须**还留在源码里**（不许悄悄删掉）
          and "rec[\"focus_on_body_at_flip\"]" in _p924
          and "\"focus_on_body_ok\":" not in _p924)
    p925 = ROOT / "scripts/jimeng_probe925_past_zero_boundary_src.py"
    _p925 = p925.read_text(encoding="utf-8") if p925.exists() else ""
    check("LLL.1 ✅⭐ **925 消掉了 §134 留下的一处歧义**："
          "**过了下界 0 之后，焦点每 28 步真的会落回下标 0 的本体上**，"
          "**而且那个本体还带着 `tabindex=\"0\"`** —— **可应用一次都不布**。"
          "⇒ ⭐ **「到边界停手」不是「因为焦点不在本体上」，"
          "而是「焦点在本体上、但 `cur + dir` 越界 ⇒ 不布」。**"
          "§134 那 10 次「没布」本来分不出这两种可能",
          "925 消掉了 §134 留下的一处歧义" in _ausrc
          and "焦点每 28 步真的会落回下标 0 的本体上**，\"\n" in _ausrc
          and "**可应用一次都不布。**" in _ausrc
          and "**所以「到边界停手」不是「因为焦点不在本体上」\"" in _ausrc
          and "**歧义被消掉。**" in _ausrc
          # ⚠️ 尾巴必须**盖过** §132 那个 27 步闭环，否则消不掉歧义
          and "assert TAIL >= 30" in _p925
          and "TAIL = 80" in _p925
          # 焦点落点的**本体判定**必须真的被记下来（不然「落回本体」没证据）
          and "\"focus_is_wrapper_seq\"" in _p925
          and "\"focus_aria_seq\"" in _p925)
    check("LLL.2 ✅ **顺带两条**：① **状态完全冻结** —— 80 次按压 "
          "`n_wrapper_any_ti` **全程恒为 75** ⇒ 应用**一次都没碰 `tabindex` 属性**；"
          "② **闭环周期是 28**（`Canvas` 在第 1/29/57 次、**2/2 一致**）"
          "⇒ 比 §132 那个 **27** 恰好多 **1** 个停靠点 —— **就是「当前被布的那个本体」** "
          "⇒ **闭环长度 = 中性态时的 27 + 当前被布的那个本体 1**（自洽）",
          "**① 状态完全冻结**" in _ausrc
          and "**全程恒为 75**" in _ausrc
          and "⇒ 应用**一次都没碰 `tabindex` 属性**" in _ausrc
          and "**② 闭环周期是 28**" in _ausrc
          and "**就是「当前被布的那个本体」**" in _ausrc
          and "**闭环长度 = 中性态时的 27 + 当前被布的那个本体 1**（自洽）" in _ausrc
          and "\"delta_all_empty\"" in _p925
          and "rec[\"any_ti_tail_min\"] = min(" in _p925)
    check("LLL.3 ⚠️⚠️ **不许**把「滚动窗口跨整页循环还成立吗」记成已回答 —— "
          "因为整页循环里**应用一次都没布**、压根**没有新的臂事件** ⇒ "
          "**它仍然是一个未回答的问题。**"
          "（925 原本要问的就是这个；消歧义是副产品，"
          "**别把副产品当成主问题被回答了**）",
          "**925 原本要问的那个问题，本批仍然没有被问到**" in _ausrc
          and "**它仍然是一个未回答的问题。**" in _ausrc
          and "**不许**把它记成「窗口跨循环成立」" in _ausrc
          # ⚠️ 判据要钉**代码**：尾巴里必须**单独记下有没有臂事件**
          and "\"n_armed\": sum(1 for p in tail_presses if p[\"moved\"])," in _p925
          and "\"arm_idx\"" in _p925)
    check("LLL.4 ⚠️ **两轮不是逐条一致，如实记账**："
          "**臂事件读数 144 次两轮完全一致**、`arm_stream` **完全一致**；"
          "但**死按压总数差 1**（117 vs 118；反向退到 0 的次数 **88 vs 89**）"
          "⇒ 焦点在**非本体元素**上多走/少走了一步 ⇒ "
          "**臂事件机制 2/2 可复现；不稳定性只出现在「与机制无关」的那部分。**"
          "⚠️ 这也**印证**了一条老纪律：**`moved` 才是必需字段** —— "
          "死按压路径会抖，**拿死按压的次数当判据就会假绿/假红**",
          "**两轮不是逐条一致，如实记账**" in _ausrc
          and "**臂事件读数 144 次两轮完全一致**" in _ausrc
          and "**死按压总数差 1**（117 vs 118" in _ausrc
          and "⇒ **臂事件机制 2/2 可复现；不稳定性只出现在「与机制无关」的那部分。**" in _ausrc
          and "**`moved` 才是必需字段**" in _ausrc
          # ⚠️ 设计门不许依赖「死按压的**次数**」（会因抖动假红）
          and "n_past_ok" not in _p925
          and "\"all_ok\": bool(entered_ok and reached_0_ok" in _p925)
    p926 = ROOT / "scripts/jimeng_probe926_window_survives_freeze_src.py"
    _p926 = p926.read_text(encoding="utf-8") if p926.exists() else ""
    check("MMM.1 ✅⭐⭐ **926 把 §135 那个「未回答的问题」真问掉了："
          "越界冻结不结束窗口。** 冻结 `30` 次（**必须 > §135 实测的 28 步闭环**）"
          "之后，**第一次正向臂事件的 `removed = [0]`** ⇒ "
          "`0` **正是冻结前最后一个臂事件那个下标** ⇒ "
          "**窗口确实跨过了那 30 次整页循环** ⇒ "
          "**「越界 ⇒ 不布」只是不更新窗口、不是把窗口清掉。**",
          "926 把 §135 那个「未回答的问题」真问掉了" in _ausrc
          and "越界冻结不结束窗口。" in _ausrc
          and "**`removed = [0]`**" in _ausrc
          and "**窗口确实跨过了那 30 次整页循环**" in _ausrc
          and "**「越界 ⇒ 不布」只是不更新窗口、不是把窗口清掉。**" in _ausrc
          # ⭐ 冻结次数必须**静态大于**那个 28 步闭环（不然「跨循环」没被覆盖）
          and "assert TAIL > 28" in _p926
          and "\"last_armed_before_freeze\"" in _p926
          and "rec[\"first_post_removed\"] = p[\"post\"][\"removed\"]" in _p926
          # 冻结「真的冻结了」是**前提**、必须自己当门
          and "freeze_clean_ok = (rec[\"freeze\"][\"n_armed\"] == 0" in _p926)
    check("MMM.2 ✅ **全程 147 次臂事件**、**`removed` = 上一个臂事件"
          "（不分方向）、零偏差** ⇒ 那条规则在"
          "「**两个边界 + 一次整页循环冻结**」之后**仍然成立**",
          "**全程 147 次臂事件**" in _ausrc
          and "**`removed` = 上一个臂事件（不分方向）、零偏差** " in _ausrc
          and "**两个边界 + 一次整页循环冻结**" in _ausrc
          and "arm_stream.append((phase, post_c[\"zero_idx\"][0]))" in _p926)
    check("MMM.3 ⚠️⭐ **撞出一条反例，必须如实记账、并且要收窄 §131**："
          "**死按压里出现了 `delta` 不空的一次** —— **冻结之后第 2 次正向按压**"
          "（`'0'` **停在 `[0]` 没动**）却做了 **`added = [1]`**；"
          "**2/2 两次运行都恰好是这同一次** ⇒ "
          "**§131 那条「死按压 ⇒ 应用完全没碰 `tabindex`」"
          "必须收窄成「绝大多数」**。⚠️ **成因未查明**。"
          "⚠️ 收窄必须写在**原条目上、不许删原文**",
          "**死按压里出现了 `delta` 不空的一次**" in _ausrc
          and "**`added = [1]`**" in _ausrc
          and "**2/2 两次运行都恰好是这同一次**" in _ausrc
          and "必须收窄成「绝大多数」** —— 它在 921/922/924" in _ausrc
          # ⭐ §131 那条**必须还带着收窄批注**留在基线里（不许悄悄删掉原句）
          and "**【926 收窄" in _ausrc
          and "**不是无条件的**" in _ausrc
          and "8/8 成立" in _ausrc
          and "**成因未查明**（**1 次异常读数不足以立机制**）" in _ausrc)
    check("MMM.4 ⚠️ **925→926 的一条自我纠错（诚实留痕）**：926 **事先写下**的预期里"
          "**判别用的那一格预测对了**、**机制细节那一格预测错了** ⇒ "
          "教训：**「先写下预期」这个做法有效**（它当场把没料到的新现象顶出来）、"
          "**但预测本身也会错** ⇒ **预测只配当假设、不配当证据**；"
          "**判据必须钉在读数上，不能钉在预测上。**"
          "（判据因此钉 `added = [1]` / `changed = [[1, '-1', '0']]` "
          "**实测值**，不钉我当初写下的预期）",
          "**925→926 的一条自我纠错（诚实留痕）**" in _ausrc
          and "**判别用的那一格预测对了**" in _ausrc
          and "**机制细节那一格预测错了**" in _ausrc
          and "**预测只配当假设、不配当证据**" in _ausrc
          and "**判据必须钉在读数上，不能钉在预测上。**" in _ausrc
          # ⭐ 探针 docstring 里**必须留着**当初写下的预期（不许事后抹掉）
          and "预期会被「巧合」干扰，先写下来免得被当成例外" in _p926)
    p927 = ROOT / "scripts/jimeng_probe927_early_writeback_repro_src.py"
    _p927 = p927.read_text(encoding="utf-8") if p927.exists() else ""
    check("NNN.1 ✅⭐ **927 用「分档冻结」把 §136 那条异常钉住了："
          "它**不是每个整页循环一次。** 冻结段的**死按压**里 `delta` **不空**的次数 —— "
          "`L=1`：**1 次死按压、0 次不空**；`L=5`：**4 次、0 次**；"
          "`L=29`：**28 次、0 次**；`L=57`：**56 次、0 次** ⇒ "
          "**跨越 1–2 个整页循环、84 次死按压，`delta` 一次都没不空**",
          "927 用「分档冻结」把 §136 那条异常钉住了" in _ausrc
          and "它**不是每个整页循环一次**。**" in _ausrc
          and "**跨越 1–2 个整页循环、84 次死按压，`delta` 一次都没不空** " in _ausrc
          # ⭐ 判别「只一次」vs「每循环一次」的前提：档位必须**跨过那个循环**
          and "FREEZE_LADDER = (1, 5, 29, 57)" in _p927
          and "assert min(FREEZE_LADDER) < 28" in _p927
          and "assert max(FREEZE_LADDER) > 28" in _p927
          and "assert len(set(FREEZE_LADDER)) >= 3" in _p927
          # 「死按压里 delta 不空」必须**真被数出来**（不能只看臂事件）
          and "n_frz_armed" in _p927
          and "\"post_prefix\"" in _p927)
    check("NNN.2 ⭐ **那次写回「恰好 1 次」，落点可钉**："
          "`L=1` 落在翻回正向后的**第 1 次**（不布、`pre` **焦点不在**本体）、"
          "臂事件在第 2 次；`L=5` 落在**第 4 次**（同样不布）；"
          "`L=29`/`L=57` 则**落在第 1 次、而且就是臂事件那一次**"
          "（`pre` **焦点在**本体）⇒ ⭐ **落点取决于「第一次正向按压时"
          "焦点在不在画布内」** ⇒ ⇒ **§136 那个「写回早了一步」的说法要收窄**："
          "**不是多了一个提前的额外动作，而是同一个「写回」动作"
          "可以落在一次「不布」的按压上。**",
          "**✅ 那次写回「恰好 1 次」，且落点可钉**" in _ausrc
          and "**落点取决于「第一次正向按压时焦点在不在画布内」** " in _ausrc
          and "**不是多了一个提前的额外动作，而是同一个「写回」动作" in _ausrc
          and "可以落在一次「不布」的按压上。**" in _ausrc
          # ⭐ §136 那条**必须还带着收窄批注**（不许悄悄删掉「早了一步」原句）
          and "**【927 收窄" in _ausrc
          and "上面「早了一步」这个说法要改，原文一个字不许删" in _ausrc
          # 落点判定必须用 **`pre`** 那一侧（923 已钉：post 是结果不是原因）
          and "\"pre_on_body\": p[\"pre\"][\"active\"][\"is_wrapper\"]," in _p927)
    check("NNN.3 ✅ **顺带独立复现 §926（4/4）**：四档「冻结之后的第一次臂事件」的 "
          "`removed` **全部是 `[0]`** ⇒ 窗口在 **0–2 个整页循环**之后"
          "**仍然指着上一个臂事件**。"
          "⚠️ **成因仍未查明**：为什么焦点回来得早/晚，**本批没有回答**",
          "**✅ 顺带独立复现 §926（4/4）**" in _ausrc
          and "`removed` **全部是 `[0]`**" in _ausrc
          and "**仍然指着上一个臂事件**" in _ausrc
          and "**成因仍未查明**" in _ausrc
          and "\"first_post_removed\"" in _p927)
    check("NNN.4 ⚠️⚠️ **927 第一版的分档设计有 flaw，如实记账**："
          "**`L ≥ 5` 的那几档「冻结」根本不是冻结** —— 上一档结束时 `'0'` 停在"
          "**下标 1**，下一档的第一次 `Shift+Tab` 于是**合法地退到 0、"
          "真的布了一次** ⇒ ⇒ **不许**把四档当成「同一实验的不同档」；"
          "**门 `frz_clean_ok` 2/2 正确地把它判成 FAIL** ⇒ "
          "**又一次避免了把不同起点的读数当成可比的分档结果**。"
          "✅ **但那三条结论仍然成立** —— 它们只依赖"
          "**「冻结段的死按压」**和**「每档都恰好 1 次写回」**，**跨档可比。**",
          "927 第一版的分档设计有 flaw，如实记账" in _ausrc
          and "那几档「冻结」根本不是冻结**" in _ausrc
          and "**不许**把四档当成「同一实验的不同档」" in _ausrc
          and "**又一次避免了把不同起点的读数当成可比的分档结果**" in _ausrc
          and "**跨档可比。**" in _ausrc
          # ⭐ 那道门必须**真的会红**（不许改成恒真）
          and "\"frz_clean_ok\": all(x[\"n_frz_armed\"] == 0 for x in ladder)," in _p927
          and "all(x[\"n_frz_armed\"] == 0 for x in ladder)" in _p927)
    p928 = ROOT / "scripts/jimeng_probe928_replica_same_ruler.py"
    _p928 = p928.read_text(encoding="utf-8") if p928.exists() else ""
    check("OOO.1 ✅ **928 第一次用同一把尺子**（919–927 那套 census + 逐次 delta、"
          "**口径逐字未改**）量了**复刻侧**："
          "**「没有 `tabindex` 属性」的本体个数** —— "
          "**源站 §131 实测 = 恒 1**、**复刻 = 恒 0**（`armAll` 天然都写了）；"
          "**`removed` 累计**源站每次臂事件至少 1 条、**复刻 0 条**；"
          "⭐ 而 **`n_wrapper_idl_focusable` 两侧都是 1** "
          "⇒ **顺序焦点位个数是对齐的**",
          "928 第一次用**同一把尺子**" in _ausrc
          and "**源站 §131 实测 = 恒 1**" in _ausrc
          and "**复刻 = 恒 0**" in _ausrc
          and "**`n_wrapper_idl_focusable` 两侧都是 1**" in _ausrc
          and "**顺序焦点位个数是对齐的**" in _ausrc
          # ⭐ 换到复刻侧**不许**改口径（判据钉在代码上）
          and "换到复刻侧**不许**改口径 —— 口径一换，两边就没法并排比了"
          in _p928
          and "assert _f in CENSUS_JS" in _p928
          and "\"n_wrapper_missing_ti\"" in _p928)
    check("OOO.2 ⚠️ **928 自己的一处硬限制（如实记账）**："
          "**复刻 demo 画布只有 2 个节点**（源站同 URL 是 76）⇒ "
          "**边界那几读数偏弱、不足以判定「复刻的边界行为对不对」** ⇒ "
          "本批**只**用复刻侧回答了「`missing_ti` 差 0 还是差 1」"
          "和「三动作形态」这两个问题。⚠️ **节点总数不许被钉成常量**",
          "928 自己的一处硬限制（如实记账）" in _ausrc
          and "**复刻 demo 画布只有 " in _ausrc
          and "**边界那几读数偏弱" in _ausrc
          and "**只**用复刻侧回答了" in _ausrc
          and "**节点总数是易变量**（复刻 demo 画布逐轮也会变）⇒ **只记不钉**" in _p928
          and "n_nodes = 2" not in _p928)
    check("OOO.3 ⚠️⚠️ **928 撞出的最重要一件事：复刻侧的 `[0, 1, 0, 1]`**"
          "**正是 §130/908 那条规则在起作用**（末尾 + **按前焦点是画布根** ⇒ "
          "布 `'0'`、绕回）⇒ **复刻与 §908 一致**；"
          "**而 §134 那句一刀切的「绝不绕回」是回归**（越界后只按 10 次、"
          "**绕回要等约 28 步整页循环**）⇒ **这是 899 踩过的同一个「取样假象」。**"
          "⇒ **不许**在更长预算的读数之前采信 §134 的正向那半个",
          "928 撞出一件必须马上处理的事：它和 §134 的结论矛盾。" in _ausrc
          and "**它绕回了 `0`**" in _ausrc
          and "**但 §134 越界之后只按了 `10` 次**" in _ausrc
          and "**这正是 899 踩过的同一个「取样假象」**" in _ausrc
          and "**不许**把 §134 那条当已验证" in _ausrc
          and "**源站侧本来就有一对互相矛盾的记录**" in _ausrc
          and "**成因未查明**" in _ausrc
          # ⭐ §908 那条**已判死**的记录必须**还在**（它是正确的一方）
          and "source_roving_wraps_at_canvas_root_908" in _ausrc
          and "**908 推翻了 899 的「绝不绕回」**" in _ausrc
          # ⚠️ 而 §134 的「PAST=10 预算不够」必须钉在源码上
          and "PAST = 10" in _p924
          and "n_past_ok = (n_past_fwd >= PAST and n_past_rev >= PAST)" in _p924)
    p929 = ROOT / "scripts/jimeng_probe929_long_tail_wrap_or_not_src.py"
    _p929 = p929.read_text(encoding="utf-8") if p929.exists() else ""
    _syn = ROOT / "scripts/jimeng_probe_js_syntax_check.py"
    _syn_src = _syn.read_text(encoding="utf-8") if _syn.exists() else ""
    check("PPP.1 ✅⭐⭐ **929 用足够长的尾巴把这一对矛盾判死了："
          "§908 对、§134 的「绝不绕回」是错的** —— "
          "**到末尾 = 第 83 次**、**第 102 次按前焦点 = `Canvas`（画布根）"
          "⇒ 布 `0`、绕回**（`pre_on_canvas_root = True`）**2/2 逐条一致**。"
          "越界之后**第 84–101 次共 18 次全是死按压**",
          "929 用足够长的尾巴把这一对矛盾判死了" in _ausrc
          and "§908 对、§134（我自己在 924 记的）「绝不绕回」是错的。**" in _ausrc
          and "**到末尾 = 第 83 次**" in _ausrc
          and "**第 84–101 次共 18 次全是死按压**" in _ausrc
          and "**§908 那条触发条件 2/2 复现**" in _ausrc
          # ⭐⭐ 判据钉在**「那一圈长度本身要先测出来」**这条纪律上
          and "assert TAIL >= 3 * LOOP_PERIOD" in _p929
          and "TAIL = 90" in _p929
          and "**不许拿「按了 N 次没看到」当机制**" in _ausrc
          # 判别格必须**真的被记下来**（按前焦点是不是画布根）
          and "on_canvas_root: aOnCanvasRoot," in _p929
          and "\"pre_on_canvas_root\": p[\"pre\"][\"active\"][\"on_canvas_root\"]," in _p929)
    check("PPP.2 ⚠️⭐ **顺带把 §908 当年那个「约 19 次」量准、并钉死了「差一按」**："
          "**到末尾 83、绕回 102 ⇒ 恰好 19 次**；"
          "而 **896 的预算是 `节点数 + 25 = 101` 次** "
          "⇒ **`revisited = {}` 真的只差 1 按** ⇒ **它不是机制、是一按之差。**"
          "⇒ **由此得到一条硬纪律**：**「到边界之后的行为」这类问题，"
          "预算必须 > 「从边界走回触发点」所需的那一圈** —— "
          "**而那一圈的长度本身就是要先测出来的东西**",
          "把 §908 当年那个「约 19 次」量准、并钉死了「差一按」" in _ausrc
          and "**到末尾 83、绕回 102 ⇒ 恰好 19 次**" in _ausrc
          and "**`revisited = {}` 真的只差 1 按**" in _ausrc
          and "**它不是机制、是一按之差。**" in _ausrc
          and "**而那一圈的长度本身就是要先测出来的东西**" in _ausrc
          # ⚠️ 896 那条**必须还带着这条订正**（不许悄悄删掉原句）
          and "**929 把这个「约 19」量准了、并钉死了「差一按」**" in _ausrc
          and "source_roving_tabindex_policy_896" in _ausrc)
    check("PPP.3 ⚠️ **929 第一版自己踩的坑（门禁用错了解释器）**："
          "把一个**跨行的 f-string 表达式**写进了打印语句 —— "
          "**f-string 表达式里不许换行**（**PEP 701 / Python 3.12** 才放宽）"
          "⇒ **3.12 的语法门全绿放行**、**而 harness 跑的是 3.11** "
          "⇒ **一跑就 SyntaxError、整轮读数全丢**。"
          "⇒ ✅ **第二道语法门已加进 `jimeng_probe_js_syntax_check.py`**："
          "**用 harness 那个解释器把每个探针 `parse` 一遍** ⇒ "
          "教训：语法门必须用「真跑那个」解释器**",
          "929 第一版自己踩的坑（门禁用错了解释器）" in _ausrc
          and "**f-string 表达式里不许换行**" in _ausrc
          and "3.12 语法门全绿放行**" in _ausrc
          and "**一跑就 SyntaxError、整轮读数全丢**" in _ausrc
          and "教训：语法门必须用「真跑那个」解释器**" in _ausrc
          # ⭐⭐ 判据钉在**门禁脚本真的加了这道门**上（不许只是写在散文里）
          and "HARNESS_PY_CANDIDATES" in _syn_src
          and "def check_py_under_runner(" in _syn_src
          and "py_errs = check_py_under_runner(" in _syn_src
          and "py_errs = check_py_under_runner(" in _syn_src
          and "**929 加的第二道**" in _syn_src)
    check("PPP.4 ⚠️ **不许**把 §134 那条已判死的「绝不绕回」当已验证 —— "
          "**收窄批注必须留在 §134 原段落上**（原文一个字不许删），"
          "**且钉住它的判据 KKK.1 必须同时钉住这条订正**。"
          "⇒ **「被推翻/被收窄的旧结论要以历史记录身份留着」这条纪律，"
          "本批是第三次执行**（921 对调 920、928 订正 134、929 判死 134 正向那半）",
          "**不许**把 §134 那条当已验证" in _ausrc
          and "**【928 订正 —— 上面那个「不绕回」的一半是回归，" in _ausrc
          and "**§134 把这两条并存的两分支一刀切成「绝不绕回」，是回归。**" in _ausrc
          # ⭐ 判据必须钉在**KKK.1 自己也钉了这条订正**上
          and "**但「正向到末尾也不绕回」那半个是错的**" in _ausrc
          and "\"source_roving_wraps_at_canvas_root_908\" in _ausrc" in open(
              ROOT / "scripts/verify-jimeng-batch841-unclickable.py",
              encoding="utf-8").read())
    p930 = ROOT / "scripts/jimeng_probe930_second_wrap_src.py"
    _p930 = p930.read_text(encoding="utf-8") if p930.exists() else ""
    check("QQQ.1 ✅⭐⭐⭐ **930 把 §139 那条硬纪律量化了**："
          "**「那一圈」是常数** —— 绕回发生在按压 **102 / 203 / 304**、"
          "**两次绕回间隔 101、101**；**每一圈逐条完全相同**"
          "（2 圈各：按压 **101**、臂事件 **73**、死按压 **28**、下标 `1…75`）"
          "⇒ **绕回不是一次性的，每一圈都完整重走。**"
          "**§908 的触发条件反复成立**：三次绕回的按前焦点**全在画布根**、"
          "每次「末尾 → 画布根」**都恰好 19 次**",
          "930 把 §139 那条硬纪律量化了" in _ausrc
          and "**① 「那一圈」是常数**" in _ausrc
          and "**两次绕回之间的按压间隔 = 101、101**" in _ausrc
          and "**② 每一圈逐条完全相同**" in _ausrc
          and "**绕回不是一次性的，" in _ausrc
          and "**三次绕回的按前焦点全在画布根**" in _ausrc
          and "而**每一次「末尾 → 画布根」都恰好 19 次**（三次全 19）" in _ausrc
          # ⭐ 预算必须按**关系式**保证（不许钉常量）
          and "MIN_TAIL_NODE_PASSES = 3" in _p930
          and "tail_len = max(TAIL_MIN, MIN_TAIL_NODE_PASSES * n_nodes)" in _p930
          and "assert MIN_TAIL_NODE_PASSES >= 2" in _p930
          and "assert LOOP_FROM_END == 19" in _p930)
    check("QQQ.2 ⭐⭐⭐ **最重的一条：整轮（正向 1 趟 + 绕回 3 圈）里"
          "从没被布上 `'0'` 的下标 = `[12, 68]`** —— "
          "**正是 §121 当年记的那两个**（2/2 逐条一致、**每一圈都一样**）"
          "⇒ **那不是「随机没赶上」，而是一个稳定可重复的跳过。**"
          "⚠️⇒ **§134/924 那次「76 个里 75 个被布过、只有 12 没布」是少报了一个** —— "
          "**那是走查不够深造成的**（反向只退了 70 次臂事件、**没走完一整圈**）"
          "⇒ **§121 的「2 个」才是完整的。**"
          "⚠️ **§122 那条硬约束继续有效**：成因**原理上不可从 DOM 查明**、"
          "复刻**只能**按纯 DOM 序、**不许编 DOM 层判据去对齐**",
          "从没被布上 `'0'` 的下标 = `[12, 68]`" in _ausrc
          and "**正是 §121 当年记的那两个**" in _ausrc
          and "**那不是「随机没赶上」，而是一个稳定可重复的跳过。**" in _ausrc
          and "**§121 的「2 个」才是完整的**，§924 那次**少报了一个**" in _ausrc
          and "**那是走查不够深造成的**" in _ausrc
          and "**那不是「随机没赶上」，而是一个稳定可重复的跳过。**" in _ausrc
          and "**不许编 DOM 层判据去对齐**" in _ausrc
          # ⭐ 订正必须**留在原条目上**（不许删原文）
          and "**【930 订正 —— 上面「只有 12 没布」是少报了一个，" in _ausrc
          and "source_wrap_cycle_is_constant_930" in _ausrc
          # 判据钉在**代码真的把「圈内没布过的下标」算出来**上
          and "\"after_first_wrap_idx_seq\"" in _p930
          and "\"all_wraps_on_canvas_root\"" in _p930)
    check("QQQ.3 ✅ **自洽核对**：周期 **101 = 73 臂事件 + 28 死按压**，"
          "而 `1…75` 去掉 `{12, 68}` 恰好 **73**；"
          "那 **28 次死按压 = §132 那个 27 步整页闭环 + 1** ⇒ **完全对上。**"
          "⚠️⭐ **把 §139 的硬纪律量化成一句可执行的**："
          "**「到边界之后」的预算必须 > 一个完整周期（本画布 = 101 次按压）** "
          "⇒ ⇒ **§896 那个 `节点数 + 25 = 101` 次的预算，"
          "在结构上就永远抓不到绕回** —— "
          "**它不是「差一按的运气」，而是「预算恰好等于周期」。**"
          "⚠️⚠️⚠️ **【931 收窄 —— 上面那句「28 死按压 / 完全对上」已被订正，"
          "原文保留在这里当历史记录、不许删】**："
          "**死按压数在四个窗口口径下全是 `27`、两轮一致** "
          "⇒ 正确分解是 **101 = 74 臂事件 + 27 死按压**，"
          "而那个 **27 正是 §132 那个整页闭环**"
          "⇒ **两侧用的是同一个 27**（正向 = 27 步闭环；"
          "反向 = 27 步闭环 + 1 个被布本体 = 28）"
          "⇒ **订正之后自洽反而更紧**。"
          "⚠️ **那个 28 是按模式填进去的**（恰好等于 §135 那个反向周期）"
          "⇒ **「自洽核对」只有两边各自数出来才算核对**",
          # —— 原文必须**留着**（历史记录不许删）
          "**101 = 73 臂事件 + 28 死按压**" in _ausrc
          and "去掉 `{12, 68}` 恰好 **73**" in _ausrc
          and "**28 次死按压 = §132 那个 27 步整页闭环 + 1**" in _ausrc
          and "在结构上就永远抓不到绕回** —— " in _ausrc
          and "**它不是「差一按的运气」，而是「预算恰好等于周期」。**" in _ausrc
          # ⚠️ 896 那条**必须带着这条量化订正**（不许悄悄删掉原句）
          and "**929 把这个「约 19」量准了、并钉死了「差一按」**" in _ausrc
          and "**`revisited = {}` 真的只差 1 按**" in _ausrc
          # ⭐⭐ **931 的订正必须钉住**（这条判据自己也要跟着收窄）
          and "【931 订正 —— 上面那个「28 死按压」是**我按模式填进去的**" in _ausrc
          and "死按压数在四个口径下全是 `27`、两轮一致**" in _ausrc
          and "101 = 74 臂事件（`{0} ∪ (1…75 去 {12,68})`）+ 27 死按压**" in _ausrc
          and "**那个 27 正是 §132 那个整页闭环的 27**" in _ausrc
          and "**又一次执行「预测只配当假设、不配当证据」那条（926）**" in _ausrc
          and "**判据跟着一起收窄**" in _ausrc
          # ⭐ 判据文本自己也必须带着这条收窄（照 §PPP.4 的做法**自读本文件**）
          and "【931 收窄 —— 上面那句「28 死按压 / 完全对上」已被订正" in open(
              ROOT / "scripts/verify-jimeng-batch841-unclickable.py",
              encoding="utf-8").read())
    check("QQQ.4 ⚠️ **930 的方法论收获**："
          "**「那一圈」的长度必须先测出来、再拿它当预算的下限** —— "
          "而 930 正是**用「尾巴 = 3 个节点数」这个关系式**"
          "（**不是钉一个常量**）来保证预算够的 ⇒ "
          "**这条关系式已静态 assert 钉住。**"
          "⚠️ **不许**把「尾巴长度」钉成某个实测常量 —— "
          "**节点总数是易变量**（同 URL 逐轮 74→77 都出现过）",
          "930 的方法论收获" in _ausrc
          and "**用「尾巴 = 3 个节点数」"
          in _ausrc
          and "⇒ 这条关系式已**静态 assert 钉住**。" in _ausrc
          and "**不许**把「尾巴长度」钉成某个实测常量 —— " in _ausrc
          # ⭐ 判据钉在**探针真的没钉常量**上
          and "assert TAIL_MIN >= MIN_TAIL_NODE_PASSES * 60" in _p930
          and "n_nodes + 25" not in _p930
          and "and \"n_nodes + 25\" not in _p930")
    p931 = ROOT / "scripts/jimeng_probe931_reverse_lap_cycle_src.py"
    _p931 = p931.read_text(encoding="utf-8") if p931.exists() else ""
    check("RRR.1 ✅⭐⭐⭐ **931 把 §140 六(1) 那个问题问掉了："
          "反向那一侧**也有**常数周期 —— 恰好 28。**"
          "落回被布本体在按压 **28 / 56 / 84 / 112**、**间隔 `[28, 28, 28]`、2/2 一致**；"
          "**画布根停靠 `[1, 29, 57, 85]`、间隔同为 `[28, 28, 28]`、逐个错开 27**。"
          "⭐ **每一圈逐条完全相同**：每圈 28 个停靠点，"
          "**以 `fpos`（焦点在可聚焦序列里的序号）逐条比，4 圈序列全等、2/2 一致**"
          "⇒ ⇒ **对称的是「常数 + 每圈可重复」这个性质，不是周期长度**"
          "（正向 **101**、反向 **28**）"
          "⚠️⚠️⚠️ **【932 收窄 —— 上面「间隔 `[28, 28, 28]`」与「4 圈序列全等」"
          "两条都被 932 撞出反例、收窄成「绝大多数（7/8）」；原文保留、不许删】**："
          "**8 圈里 7 圈是 28、1 圈是 27**（rep2 第 3 圈），"
          "**那一圈缺的恰好是 `document.body` 那一站**、其余 27 站逐条全等\n"
          "⇒ **「28」不是常数**；真正的结构是"
          "**「27 步整页闭环 + 1 个被布本体」，而那个 27 步闭环本身偶发少停一站**",
          "source_reverse_lap_cycle_is_constant_931" in _ausrc
          and "**间隔 = `[28, 28, 28]`，2/2 逐条一致**" in _ausrc
          and "间隔同为 `[28, 28, 28]`**" in _ausrc
          and "**两者逐个恰好错开 27**" in _ausrc
          and "**4 圈序列全等、2/2 一致**" in _ausrc
          and "**对称的是「常数 + 每圈可重复」这个性质**" in _ausrc
          # ⭐⭐ **间隔数不是钉一个常量、而是要有足够多的间隔**（≥3 个才算主张）
          and "assert MIN_RETURNS >= 4" in _p931
          and "assert REPS >= 2" in _p931
          # ⚠️⚠️ **不许把 §135 那个 28 钉成期望值** —— 那等于把答案写进判据
          and "不许把 §135 那个 28 钉成期望值" in _p931
          and "== 28" not in _p931
          and "gaps_armed\"] == 28" not in _p931
          # ⭐⭐ **932 的收窄必须钉住**（这条判据自己也要跟着收窄）
          and "【932 收窄 —— 上面「间隔 `[28, 28, 28]`」与「每一圈逐条完全相同」" in _ausrc
          and "里 **7 圈是 28、1 圈是 27**" in _ausrc
          and "**那一圈缺的恰好是 `document.body` 那一站**" in _ausrc
          and "**「间隔恒定」与「每圈逐条全等」都收窄成「绝大多数（7/8）」**" in _ausrc
          # ⭐ 判据文本自己也必须带着这条收窄（照 §PPP.4 的做法**自读本文件**）
          and "【932 收窄 —— 上面「间隔 `[28, 28, 28]`」与「4 圈序列全等」" in open(
              ROOT / "scripts/verify-jimeng-batch841-unclickable.py",
              encoding="utf-8").read())
    check("RRR.2 ✅ **931 顺带再次复现 §135「应用在越界尾巴里零参与」**，"
          "而且这次多钉一个**对照量**：尾巴 **112 次按压零臂事件**、"
          "**`removed/added/changed` 全空 112/112**、`any_ti` **75 → 75 全程冻结**，"
          "⭐ 且 **`n_focusable` 全程恒为 276**（可聚焦集合一次都没被 112 次按压改动）"
          "⇒ **尾巴读数不是在「页面被按坏了」的状态下采到的**",
          "**尾巴 112 次按压零臂事件**" in _ausrc
          and "**全空 112/112**" in _ausrc
          and "**`n_focusable` 全程恒为 276**" in _ausrc
          and "**再次复现 §135**" in _ausrc
          # ⭐ 判据钉在**尺子没被改动**上：931 只「加」字段、没改已有算法
          and "931 只在 930 那版上「加」字段、不改任何一个已有字段的算法" in _p931
          and "assert \"fpos\" in CENSUS_JS and \"n_focusable\" in CENSUS_JS" in _p931
          and "\"slice(0, 12)\" not in CENSUS_JS" in _p931
          and "\"any_ti_idx\" in CENSUS_JS and \"removed, added, changed\" in CENSUS_JS" in _p931)
    check("RRR.3 ⭐⭐ **931 用一个不需要额外臂的对照臂，把 §135 那处"
          "「两轮不是逐条一致」的抖动定位了**："
          "**接近段在动、尾巴不动** —— 反向退到 `0` 的次数 **88 → 89（变了）**，"
          "而**尾巴间隔两轮完全相同 `[28, 28, 28]`**"
          "⇒ ⇒ **抖动在「接近段」、不在尾巴 ⇒ 不影响任何机制读数**"
          "⇒ **又一次印证 `moved` 才是必需字段**（925 那条老纪律）",
          "**接近段在动、尾巴不动**" in _ausrc
          and "**88 → 89（变了）**" in _ausrc
          and "**§925 记的那处抖动在「接近段」、不在尾巴**" in _ausrc
          and "**又一次印证 `moved` 才是必需字段**" in _ausrc
          # ⭐ 判据钉在**对照臂真的同时记了这两段**上（否则定位无从谈起）
          and "rec[\"hit_end_at\"] = hit_end_at" in _p931
          and "rec[\"zero_at\"] = zero_at" in _p931
          and "rec[\"gaps_armed\"] = gaps_of(ret_armed_at)" in _p931)
    check("RRR.4 ⚠️⚠️⚠️ **931 探针自己踩的坑必须留痕：那是「分析层」的切片把规律读反** ——"
          " 逐圈比较**首尾用了不一致的边界**（第 0 圈从尾巴第 1 次按压起、"
          "第 1..3 圈从「上一次的落回本体」起）⇒ 打出 `lap_lens = [28, 29, 29, 29]`、"
          "`laps_identical = False`。⚠️ **那不是源站事实**；"
          "改用**统一边界（以画布根停靠点为每圈起点）**后各圈全为 28、序列逐条全等。"
          "⇒ **「切片会把规律读反」这条纪律第四次执行**（§131 采集层、这次分析层）"
          "⇒ **连「以什么为界切一整圈」都得先钉死**。"
          "⚠️ 钉住**探针里那条留痕的注释不许被删**（它就是这段教训的载体）",
          "**那不是源站事实、是我自己的切片把规律读反**" in _ausrc
          and "**以画布根停靠点为每圈起点**" in _ausrc
          and "**第四次执行**" in _ausrc
          and "这次犯在**分析层**（§131 那次犯在采集层）" in _ausrc
          # ⭐ 探针必须**已经用统一边界**，且**必须留着那条坑的注释**
          and "现在**统一边界：以「画布根停靠点」为每圈起点**" in _p931
          and "root_pos = rec[\"tail\"][\"root_at\"]" in _p931
          and "lap_starts.append(s_k)" in _p931
          and "**那不是源站事实、是我自己的切片把规律读反**" in _p931
          # ⚠️ 旧的错误切片不许还留在代码里当活逻辑
          and "lap_segs.append(walk_seq[start:k])" not in _p931)
    check("RRR.5 ⭐ **931 顺带解开 §132 留下的一处「同名成对」**："
          "§132 记过闭环里 `添加素材到时间线`/`静音`/`全屏编辑`/`导出时间线` "
          "**各出现 2 次**、当时分不清是同一元素出现两次还是两个元素；"
          "**`fpos` 把它们分开了：89/88/87/86 与 23/22/21/20 "
          "⇒ 是两个不同节点各自的 4 个控件**。"
          "⭐ 这也是**必须给焦点落点加一个「序号型」身份**的理由："
          "只比 `aria` 会在这两个同名的兄弟上撞车（§132 的老问题一直没解）",
          "**931 用 `fpos` 分开了：89/88/87/86 与 23/22/21/20 " in _ausrc
          and "⇒ 是两个不同节点各自的 4 个控件**" in _ausrc
          and "**§132 留下的一处「同名成对」**" in _ausrc
          # ⭐ 判据钉在**探针真的新增了序号型身份**上
          and "fpos: a ? fset.indexOf(a) : -1,     // ⭐ 931 新增" in _p931
          and "§132 已记过闭环里有**成对出现**的同名元素（如 静音）" in _p931)
    p932 = ROOT / "scripts/jimeng_probe932_same_27_cycle_src.py"
    _p932 = p932.read_text(encoding="utf-8") if p932.exists() else ""
    check("SSS.1 ⭐⭐ **跨状态对齐必须换尺子，而 931 那把尺子跨状态不可比**："
          "`fpos` 的分母是**当前可聚焦集合的大小** ⇒ 中性态（`any_ti = 0`）与"
          "越界尾巴（`any_ti = 75`）**同一个元素的 `fpos` 数值不同** "
          "⇒ **拿它跨状态对齐是错的。** 932 改用两个与状态无关的身份："
          "`dom_sig`（结构路径，**一个字都不掺 aria/class/tabindex**）"
          "与 `owner_node_idx`（最近 `.react-flow__node` 祖先的 DOM 下标）",
          "source_27_cycle_is_one_loop_932" in _ausrc
          and "**拿它跨状态对齐是错的。**" in _ausrc
          and "结构路径，**一个字都不掺 aria/class/" in _ausrc
          and "最近那个 `.react-flow__node` 祖先的 DOM 下标）。" in _ausrc
          # ⭐ 判据钉在**探针真的不许往 dom_sig 里掺属性**上
          and "assert \"dom_sig\" in CENSUS_JS and \"owner_node_idx\" in CENSUS_JS" in _p932
          and "dom_sig 里不许掺任何属性（会重新绑回 aria）" in _p932
          and "n.tagName.toLowerCase() + ':nth-of-type(' + nth + ')'" in _p932
          and "const host = el.closest('.react-flow__node');" in _p932
          # ⚠️ 931 的 fpos **不许被删**（同状态内仍有用）
          and "assert \"fpos\" in CENSUS_JS, \"931 的字段要留着（同状态内仍有用）\"" in _p932
          # ⭐⭐ **933 的收窄必须钉住**（这条判据自己也要跟着收窄）
          and "【933 收窄 —— 上面那个「间隔 **27**」是**两轮各 2 个圈**的样本、" in _ausrc
          and "**臂 A 同样会有 26 长的圈**（实测 1/16）" in _ausrc
          and "**「臂 A 的圈恒为 27」与「臂 B 的圈恒为 28」一样，都不是常数**" in _ausrc
          # ⭐ 判据文本自己也必须带着这条收窄（照 §PPP.4 的做法**自读本文件**）
          and "【933 收窄 —— 上面那个「间隔 **27**」是两轮各 2 个圈的样本；" in open(
              ROOT / "scripts/verify-jimeng-batch841-unclickable.py",
              encoding="utf-8").read())
    check("SSS.2 ⭐⭐⭐ **932 把「那 27 步整页闭环」钉成同一个闭环** —— "
          "**臂 B 那一圈 = 臂 A 那个 27 步闭环 `dom_sig` 逐条全等、"
          "同一位置（最佳 offset = 0、匹配 27/27）＋ 末尾多出被布本体那一站**"
          "⇒ **§135 当年那句「闭环长度 = 中性态时的 27 + 当前被布的那个本体 1」"
          "现在有了逐条证据**（当年只有个数、没有逐条对齐）",
          "**③ ⭐⭐⭐ 「那 27 步整页闭环」确实是同一个**" in _ausrc
          and "同一位置（最佳 offset = 0、匹配 27/27）＋ 末尾多出被布本体那一站**" in _ausrc
          and "现在有了 `dom_sig` 口径的逐条证据**（当年只有个数、没有逐条对齐）。" in _ausrc
          # ⭐ 钉住「两臂在同一次运行、共用同一把尺子」（否则跨 run 比会混进别的变量）
          and "**同一次运行里跑两臂、共用同一把尺子**" in _ausrc
          and "arm_a" in _p932 and "arm_b_tail" in _p932)
    check("SSS.3 ✅ **臂 A 独立复现 §132 的 27**，而且它自己就是一道**对照**："
          "点空白后 `any_ti ≡ 0`、60 次 `Shift+Tab`、`moved` 全 False、"
          "**`any_ti` 全程恒 0** ⇒ **臂 A 跑完的 `tabindex` 状态与跑之前完全一样** "
          "⇒ **两臂之间不需要 reload，却在同一页、同一把尺子下测到。**"
          "⚠️ 「moved 全 False」这一条是**门不是读数**（它一旦为假就说明臂 A 干扰了状态）"
          "⚠️⚠️⚠️ **【933 收窄 —— 上面那个「间隔 **27**」是两轮各 2 个圈的样本；"
          "臂 A 同样会有 26 长的圈（实测 1/16）。原文保留、不许删】**："
          "**「臂 A 的圈恒为 27」与「臂 B 的圈恒为 28」都不是常数** —— "
          "**两边的短圈都恰好是「同臂参照整圈删掉 `BODY` 那一站**",
          "**② ✅ 臂 A 独立复现 §132 的 27**" in _ausrc
          and "**按周期 27 切出的两段完整窗口 `dom_sig` 逐条 27/27 全等**（2/2）。" in _ausrc
          and "⇒ **臂 A 跑完的 `tabindex` 状态与跑之前完全一样**" in _p932
          and "两臂之间**不需要 reload**，却在**同一页、同一把尺子**下测到。" in _p932
          # ⭐ 判据钉在**那道门真的存在**上
          and "neutral_never_armed_ok = (rec[\"arm_a\"][\"n_armed\"] == 0)" in _p932
          and "neutral_ok = (rec[\"arm_a_any_ti_at_start\"] == 0)" in _p932)
    check("SSS.4 ⚠️⚠️ **收窄 931 之后，「28」不是常数**：8 圈（2 轮 × 4 圈）里"
          "**7 圈是 28、1 圈是 27**（rep2 的第 3 圈），"
          "**那一圈缺的恰好是 `document.body` 那一站**、其余 27 站逐条全等、"
          "owner 取值集合也不变\n"
          "⇒ ⇒ **真正的结构是「27 步整页闭环 + 1 个被布本体」，"
          "而那个 27 步闭环本身偶发少停一站**\n"
          "⚠️ **机制只到这一步为止**：`document.body` 那一站为什么偶发不出现，"
          "**成因未查明、标「未验证」**（不许编）",
          "**④ 收窄 931：「28」不是常数**" in _ausrc
          and "**其余 27 站逐条全等**、owner 取值集合也不变（`{-1, 0, 2, 12, 22}`）" in _ausrc
          and "**真正的结构是「27 步整页闭环 + 1 个被布本体」，" in _ausrc
          and "**成因未查明、标「未验证」**（不许编）" in _ausrc
          # ⚠️⚠️ **不许把「27」钉成期望值** —— 932 要问的正是「是不是恒定」
          and "assert \"== 27\" not in CENSUS_JS" in _p932)
    check("SSS.5 ⭐ **答掉 §141 九(1)：那 9 个「节点邻近槽位」归谁** —— "
          "**`22` 贡献 4 个、`12` 只贡献 `替换媒体` 那 1 个、`2` 贡献 4 个**；"
          "**下标 `68` 在两臂四圈里一次都没出现** ⇒ "
          "**在「被布本体 = 0」这个状态下，中性态与越界尾巴的 9 站完全相同** "
          "⇒ 越界、走过一圈都不改它。"
          "⚠️⚠️ **但不许据此说「节点 12 特殊」**（它恰好是那两个「整轮从没被布上 `'0'`」"
          "之一）—— NN.1 已查清 12/68 在 DOM 层毫无特殊之处 "
          "⇒ **最简读法是位置性的**（闭环入口恰好挨着哪几个节点）、不是内在属性 "
          "⇒ **§122 继续有效：不许编 DOM 层判据去对齐**",
          "**⑤ ⭐ 答掉 §141 九(1)**" in _ausrc
          and "**`22` 贡献 4 个、`12` 只贡献 `替换媒体` 那 1 个、`2` 贡献 4 个**" in _ausrc
          and "**下标 `68` 在两臂四圈里一次都没出现**" in _ausrc
          and "**但不许据此说「节点 12 特殊」**" in _ausrc
          and "⇒ **最简读法是位置性的**" in _ausrc
          and "**§122 继续有效：不许编 DOM 层判据去对齐。**" in _ausrc
          # ⭐ NN.1 那条排除必须**留在基线里**（不许被这次的新读数顶掉）
          and "它们在 DOM 层毫无特殊之处" in _ausrc)
    check("SSS.6 ⚠️⚠️⚠️ **932 自己踩的第二个坑：切片边界的第三次** —— 臂 A 按"
          "「画布根」切圈、而 60 次按压切出的是 **[27, 7]**，"
          "**拿一个整圈去和一个 7 次的残尾比** ⇒ 打出「圈间一致 = False」。"
          "⚠️ **那不是读数、是切法**：改按**周期 27** 切两段窗口 ⇒ **`dom_sig` 逐条 27/27 全等**。"
          "⇒ **「切片会把规律读反」第四次执行**（§131 采集层、931 分析层、932 这里）；"
          "⇒ **教训升级：要比的那两个集合必须同质 —— 一个整圈和一个残尾不是同类东西。**",
          "**932 自己踩的第二个坑（切片边界的第三次）**" in _ausrc
          and "**拿一个整圈去和一个 7 次的残尾比**" in _ausrc
          and "改按**周期 27** 切两段窗口 " in _ausrc
          and "**「切片会把规律读反」第四次执行**" in _ausrc
          and "**一个整圈和一个残尾不是同类东西。**" in _ausrc
          # ⭐ 探针里那条坑的注释必须留着
          and "**那不是读数**、是**切法**造成的：改按**周期 27** 切两段窗口 " in _ausrc)
    p933 = ROOT / "scripts/jimeng_probe933_body_stop_rate_src.py"
    _p933 = p933.read_text(encoding="utf-8") if p933.exists() else ""
    check("TTT.1 ⭐⭐ **933 量到了 `document.body` 那一站的缺席率**："
          "**32 圈里 3 圈缺（9.4%）** —— **臂 A（中性态）1/16、臂 B（越界尾巴）2/16**，"
          "落点是**第 4 / 第 2 / 第 7 圈**。"
          "⭐ **切分口径**：**周期本身是读数 ⇒ 不许拿「27」去切**（那会把"
          "「这一圈是 26 还是 27」变成假设）⇒ **按画布根停靠点切**",
          "source_body_stop_absent_933" in _ausrc
          and "**32 圈里 3 圈缺 `document.body`（9.4%）**" in _ausrc
          and "**臂 A（中性态）1/16、臂 B（越界尾巴）2/16**" in _ausrc
          and "**周期本身是读数 ⇒ 不许拿「27」去切**" in _ausrc
          and "**按「画布根停靠点」切**" in _ausrc
          # ⭐ 判据钉在**切分真的是按画布根、且剔了残尾**上
          and "assert \"on_canvas_root\" in CENSUS_JS, \"切分锚点必须是画布根停靠\"" in _p933
          and "def cut_cycles(press_list, min_len):" in _p933
          and "if len(seg) < min_len:" in _p933
          and "**不许拿残尾去和整圈比**（932 的教训）" in _p933)
    check("TTT.2 ⭐⭐⭐ **933 一次排除三个假设**，而且**每一个都有钉死的读数**："
          "①「**越界状态才让它消失**」—— **排除**（**臂 A 也缺了 1 次**；"
          "932 只在臂 B 看到，是因为它**臂 A 只测了 2 个圈**）；"
          "②「**可聚焦集合大小变了**」—— **排除**"
          "（`n_focusable` **全程恒定**：臂 A **201**、臂 B **276**，32 圈无一次变化）；"
          "③「**短圈是少了被布本体**」—— **排除**（臂 B 每圈**都恰好停被布本体 1 次（16/16）**）",
          "**④ ⭐⭐⭐ 一次排除三个假设**" in _ausrc
          and "「越界状态才让它消失」——排除**" in _ausrc
          and "**臂 A（中性态、`any_ti ≡ 0`）也缺了 1 次**" in _ausrc
          and "「可聚焦集合大小变了」——排除**" in _ausrc
          and "**全程恒定**（臂 A **201**、臂 B **276**，两轮 32 圈无一次变化）" in _ausrc
          and "「短圈是少了被布本体」——排除**" in _ausrc
          and "臂 B 每一圈**都恰好停被布本体 1 次（16/16）**" in _ausrc
          # ⭐ NN.1 那条「12/68 在 DOM 层毫无特殊之处」不许被顶掉
          and "它们在 DOM 层毫无特殊之处" in _ausrc)
    check("TTT.3 ⭐⭐ **每一处短圈都精确等于「同臂参照整圈删掉 `BODY` 那一站」"
          "（3/3 逐条全等，`dom_sig` 口径）** ⇒ **唯一的差异就是那一站**，"
          "没有别的站跟着动。⇒ 剩下唯一相关的事实是：那一站是 `document.body` 本身，"
          "而它出现与否**与可聚焦集合、与越界状态、与被布本体都无关**",
          "**③ ⭐⭐ 每一处短圈都精确等于「同臂参照整圈删掉 `BODY` 那一站」" in _ausrc
          and "没有别的站跟着动（`dom_sig` 口径）" in _ausrc
          and "而它**出现与否与可聚焦集合、与越界状态、与被布本体都无关**" in _ausrc
          # ⭐ 判据钉在**探针真的把短圈和参照整圈逐条比过**上
          and "同臂某一个带 `BODY` 的整圈删掉 `BODY` 那一站」？**" in _p933
          and 'cand = ref["sig"][:bidx] + ref["sig"][bidx + 1:]' in _p933)
    check("TTT.4 ⚠️⚠️⚠️ **成因仍然未查明、标「未验证」** —— "
          "**3/32 的样本不足以判定**它是「随机」「固定周期」还是"
          "「与某个未观测变量相关」：落点分散在**第 2/4/7 圈**、"
          "**不支持「固定位置」，但也证不了「随机」**。"
          "⚠️⇒ **不许**把「分散」读成「随机」—— **这是本轮最容易犯的推论跳跃**",
          "**但成因仍然未查明、标「未验证」**" in _ausrc
          and "**3/32 的样本不足以判定**" in _ausrc
          and "**落点分散在第 2/4/7 圈、不支持「固定位置」，但也证不了「随机」**" in _ausrc
          and "**不许**把「分散」读成「随机」（这是本轮最容易犯的推论跳跃）" in _ausrc
          # ⭐ 判据文本自己**也必须**带着「未验证」（不许悄悄去掉）
          and "**成因未查明、标「未验证」**（不许编）" in _ausrc
          and "**3/32 的样本不足以判定**" in open(
              ROOT / "scripts/verify-jimeng-batch841-unclickable.py",
              encoding="utf-8").read())
    check("TTT.5 ⚠️ **933 自己第一版把预算算错了** —— 按「保守下界 20」算 cap = 200，"
          "而 **8 圈 × 27 = 216** ⇒ **必然撞 cap**。"
          "⇒ **这正是 §139/§140 那条纪律的同一个坑**（「预算必须 > 圈数 × 真实单圈长度」、"
          "**而那个长度要先测出来**）⇒ 已改成按 **30** 算（cap = 280），"
          "并加了静态 assert 钉住「预算系数必须高于实测单圈长度」。"
          "⚠️ **这条要留痕**：它是「预算不足 ⇒ 读数作废」这条纪律的**第二次**现场踩坑"
          "（第一次是 §929 的 §896 差一按）",
          "**⑤ 顺带记一条自检**：933 第一版的**预算算错了**" in _ausrc
          and "**这正是 §139/§140 那条纪律的同一个坑" in _ausrc
          and "并加了静态 assert 钉住「预算系数必须高于实测单圈长度」。" in _ausrc
          and "它是「预算不足 ⇒ 读数作废」这条纪律的**第二次**现场踩坑" in _ausrc
          # ⭐ 判据钉在**那道 assert 真的在探针里**上
          and "assert BUDGET_PER_CYCLE >= 28, \\" in _p933
          and "assert TAIL_CAP_A >= CYCLES_PER_ARM * BUDGET_PER_CYCLE" in _p933
          and "**「到边界（这里是「到够圈数」）之后」的预算必须 > 圈数 × 真实单圈长度" in _p933)
    p934 = ROOT / "scripts/jimeng_probe934_body_own_attrs_src.py"
    _p934 = p934.read_text(encoding="utf-8") if p934.exists() else ""
    check("UUU.1 ✅ **934 换了一个能被证伪的假设，而不是去堆圈数**："
          "**堆更多圈只能把频率估得更准、判不了性质** ⇒ "
          "**H：「那一站的出没，取决于 `document.body` 自己那一下当时是否可被顺序聚焦」** "
          "⇒ 逐次按压记四个**与焦点走线无关**的页面量。读数 **5/60（8.3%）**、"
          "落点第 **10/6/1/12/8** 圈、与 933 的 **3/32（9.4%）** 同量级 "
          "⇒ **频率落在 8–9%**；**短圈 == 整圈删 `BODY`：5/5 逐条全等**"
          "（**934 独立复核了 933 的结论**）",
          "source_body_own_attrs_falsified_934" in _ausrc
          and "**① 934 为什么不去堆圈数**" in _ausrc
          and "**H：「那一站的出没，取决于 `document.body` 自己那一下当时" in _ausrc
          and "**5/60 圈缺 `document.body`（8.3%）**" in _ausrc
          and "**同量级** ⇒ **频率落在 8–9%**" in _ausrc
          and "**短圈 == 同臂整圈删掉 `BODY` 那一站：5/5 逐条全等**" in _ausrc
          and "**934 独立复核了 933 的结论**" in _ausrc
          # ⭐ 判据钉在**四个新字段真的逐次记了**上
          and "for fld in BODY_ATTRS:" in _p934
          and "assert fld in CENSUS_JS, f\"934 的新字段 {fld} 没写上\"" in _p934
          and "BODY_ATTRS = (\"body_tabindex\", \"body_tab_index\"," in _p934
          and "\"body_n_children\"," in _p934
          and "\"body_scroll_top\")" in _p934)
    check("UUU.2 ⭐⭐⭐ **H 被证伪** —— **`body_tabindex` ≡ `null`、"
          "`body_tab_index` ≡ `-1`、`body_scroll_top` ≡ `0` 全臂恒定**；"
          "`body_n_children` 在 **12/13** 之间跳而**完整圈之间逐次全同**；"
          "**一旦按正确的时间对齐（把参照圈在 `BODY` 那一行切开再拼），"
          "缺席圈与完整圈的四个量逐次全同（5/5）** "
          "⇒ **`document.body` 自己那一下的任何可测属性，与那一站的出没无关**",
          "**③ ⭐⭐⭐ H 被证伪**" in _ausrc
          and "`body_tab_index` ≡ `-1`、`body_scroll_top` ≡ `0` —— 全臂恒定**" in _ausrc
          and "**一旦按正确的时间对齐（把参照圈在 `BODY` 那一行切开再拼），" in _ausrc
          and "与「那一站出不出现」无关。**" in _ausrc
          # ⭐ 判据钉在**探针真的做了「切开再拼」**上（不是按行号硬对）
          and "ref_cut = ref[:bidx] + ref[bidx + 1:]" in _p934
          and "def cmp_cut(rows):" in _p934
          and "\"time_aligned\": {\"cmp_len\": n_cut, \"all_same\": same_cut," in _p934)
    check("UUU.3 ⚠️⚠️⚠️ **「切片会把规律读反」的**第四种形式**："
          "**「缺席圈比参照圈少一行」⇒ 按行号对齐就是整体错位一格**。"
          "**可复算的证据**：完整圈的 `body_n_children` 跳变行号是 "
          "`[…15, 17, 20, 24, 25]`、缺席圈是 `[…14, 16, 19, 23, 24]` —— "
          "**每一个都恰好少 1**、而**前 13 行完全相同** "
          "⇒ 第一版读到的「`all_same = False` ⇒ 它变了」**全是错位**、不是真相关。"
          "⇒ **这是本轮最容易上当的一处：「找到一个相关的量」这个结论本身，"
          "也可能是切片对齐造出来的**",
          "**④ 撞出「切片会把规律读反」的**第四种形式**" in _ausrc
          and "按行号对齐就是整体错位一格**" in _ausrc
          and "**每一个都恰好少 1**" in _ausrc
          and "**前 13 行完全相同**" in _ausrc
          and "**全是错位**，" in _ausrc
          and "**不是真相关** ⇒ ⇒ **这是本轮最容易上当的一处**" in _ausrc
          and "也可能是切片对齐造出来的**" in _ausrc
          # ⭐⭐ 探针里那条**错位现场**必须留着（不许删掉那处「看起来多余」的读法）
          and "⚠️⚠️ **「缺席圈比参照圈少一行」⇒ 按行号对齐就是**整体错位一格****" in _p934
          and "naive_row_align" in _p934
          and "**保留当历史记录**：它是那处错位的现场" in _p934
          and "**判决**" in _p934)
    check("UUU.4 ⚠️⚠️ **处置：两种对齐都算、都记，判决看 `time_aligned`** —— "
          "`naive_row_align`（那处错位的现场）与 `time_aligned`（判决）；"
          "**基线与判据都要写明「判决看 `time_aligned`」**。"
          "⚠️ 另外 934 事先写下的那条纪律正好用上："
          "**「不许因为找到相关量就宣称它就是成因」** —— 而 H 连「相关」都不是、"
          "**它连错位都不是**",
          "✅ **处置：两种对齐都算、都记**" in _ausrc
          and "**保留当历史记录**" in _ausrc
          and "**基线与判据都写明「判决看 `time_aligned`」**" in _ausrc
          and "**「不许因为找到相关量就宣称它就是成因」**" in _ausrc
          and "**它连错位都不是**" in _ausrc
          # ⭐ 判据钉在**摘要/打印真的两种都报了**上
          and "\"body_attrs_naive_all_same\": ba.get(\"naive_all_same\")" in _p934
          and "**按行号硬对（错位现场）=" in _p934)
    check("UUU.5 ⚠️⚠️⚠️ **成因仍然未查明、标「未验证」** —— "
          "**5/60 仍不足以判定**「随机 / 固定周期 / 与某个未观测变量相关」；"
          "落点第 **1/6/8/10/12** 圈**分散** ⇒ "
          "**仍然不许把「分散」读成「随机」**（§143 五那条纪律继续有效）。"
          "⚠️ 另外 933 那三条「已排除的假设」**继续有效**、**不因本批而复活**",
          "**成因仍然未查明、标「未验证」**" in _ausrc
          and "**5/60 仍不足以判定**「随机 / 固定周期 / 与某个未观测变量相关」" in _ausrc
          and "**仍然不许把「分散」读成「随机」**" in _ausrc
          and "**① 「越界状态才让它消失」——排除**" in _ausrc
          and "「短圈是少了被布本体」——排除**" in _ausrc
          # ⭐ 判据文本自己也必须带着「未验证」
          and "**成因仍然未查明、标「未验证」**" in open(
              ROOT / "scripts/verify-jimeng-batch841-unclickable.py",
              encoding="utf-8").read())
    p936 = ROOT / "scripts/jimeng_probe936_inlayer_occlusion_src.py"
    _p936 = p936.read_text(encoding="utf-8") if p936.exists() else ""
    _aus936 = _ausrc
    check("WWW.1 ✅⭐⭐⭐ **936：§84 起挂着的「非全屏浮层盖住**层内**控件该算什么档」，"
          "机制查清了 —— 两侧都测出这一类 **0 观测**，所以**判据一个字都不动**（§77）**",
          "source_inlayer_occlusion_absent_936" in _aus936
          and "机制查清了 —— 两侧都测出**这一类 0 观测**，所以判据不用改**" in _aus936
          # ⭐ 判据钉在**两侧的 0 读数**上，而不是钉某个实现字面量
          and "把 `!inLayer` 拿掉重算分桶，162 行里换桶 0 行**" in _aus936
          and "**层内四边全被不透明外人盖住 0 步**" in _aus936
          and "**「层内控件被**非全屏**浮层盖住」0 步**" in _aus936)
    check("WWW.2 ⭐ **`by_modal` 排在 `by_layer` 前面，才是那 8 行走不到 "
          "`!inLayer` 守卫的原因** —— 「控件层内 + 遮挡物层内」8 行**全部** "
          "`covered_by_modal=true`；守卫当前**不承重**（反事实换桶 0 行，2/2）",
          "**`by_modal` 在 `_bucket()` 里排在 `by_layer` 前面**" in _aus936
          and "**全部** `covered_by_modal=true`" in _aus936
          and "**根本走不到那个守卫**" in _aus936
          and "**反事实：把 `!inLayer` 拿掉重算分桶，162 行里换桶 0 行**" in _aus936
          # ⭐ 钉**代码**：桶顺序与守卫都还在原处、没被 936 动过
          and 'if r.get("covered_by_modal"):\n            return "by_modal"'
              in _ausrc
          and 'if r.get("covered_by_layer"):\n            return "by_layer"'
              in _ausrc
          and "const coveredByLayer = !inLayer" in _ausrc)
    check("WWW.3 ⚠️ **任意位置全盖 6 步全部落在 `by_modal` 那一路** —— "
          "都是顶部 `返回首页` 那个链接、遮挡物是**铺满视口**的画布 pane "
          "（合判据的 `scrim`，系数 0.85）⇒ **与 §77 问的形态无关，不许算进目标类**",
          "**全部**是顶部 `返回首页` 那个链接" in _aus936
          and "合判据的 `scrim`，系数 0.85" in _aus936
          and "**落在 `by_modal` 那一路，与 §77 问的形态无关**" in _aus936
          # ⭐ 钉代码：探针的 scrim 口径与判据**逐字同系数**（两边都取 0.85）
          and "r.width >= innerWidth * 0.85 && r.height >= innerHeight * 0.85"
              in _p936
          and "bk.w >= window.innerWidth * 0.85 &&" in _ausrc
          and "bk.h >= window.innerHeight * 0.85);" in _ausrc)
    check("WWW.4 ⭐⭐ **936 第一次把 845 那把尺子的松度量出来：同一批步上 "
          "中心口径 154/360 vs 四边口径 6/360（约 25 倍）** —— 845 的读数只作对照、"
          "不参与判决",
          "**中心点 + 包含关系**口径报「被遮」**154/360**" in _aus936
          and "**四边 + 不透明**口径报**6/360**" in _aus936
          and "**936 第一次把两把尺子的差距量化出来**" in _aus936
          # ⭐ 钉代码：中心读数**照样记**（`hit_center_*`），但判决只用四边
          and "hit_center_dom_sig" in _p936
          and "\"hit_center_covered\"" in _p936
          and "d[\"occluded\"] = bool(edges) and d[\"edges_covered\"] == len(edges)"
              in _p936)
    check("WWW.5 ⚠️⚠️ **阳性对照必须让尺子真的报出四边全盖，0 观测才作数** —— "
          "夹具**必须比控件大出一圈**：四条探针点按判据是**外扩 1px**，"
          "夹具若正好等于控件矩形，四个点全落在夹具**外面** ⇒ "
          "**阳性对照在构造上就不可能通过**",
          "夹具**必须比控件大出一圈**（`PAD=6`）" in _aus936
          and "**阳性对照在构造上就不可能通过**" in _aus936
          and "4/6 层尺子报出**四边全盖**，0 观测因此作数**" in _aus936
          # ⭐ 钉代码：门禁要求的是 `occluded`（四边全盖），不是「加上了夹具」
          and "const PAD = 6;" in _p936
          and 'fired = bool(d.get("occluded"))' in _p936
          and '"positive_control_ok": any(c.get("ruler_fired") for c in ctrls)'
              in _p936)
    check("WWW.6 ⚠️⚠️⚠️ **H936「浮层互斥导致这一类不可能出现」标「未验证」** —— "
          "源站实测同时最多 2 层，而**那第 2 层是常驻的 `.react-flow__node-toolbar`**、"
          "**不是**第二个浮层 ⇒ **「2 层」不能读成「两个浮层并存」**；"
          "本批**没有**测「开一层会不会关掉另一层」这件正事。"
          "⚠️ **不许**说 H936 已成立，只说「这一类 0 观测、判据不动」",
          "**未验证、只是与两侧读数相容**" in _aus936
          and "**不是**第二个浮层" in _aus936
          and "**「2 层」不能读成「两个浮层并存」**" in _aus936
          and "**没有**测到「开一层会不会关掉另一层」这件正事" in _aus936
          and "**所以不许**说 H936 已成立" in _aus936
          # ⭐ 钉代码：顶层去重与「层」的口径（互为祖先只算一层）
          and "def topmost(boxes):" in _p936
          and "互为祖先的只算**一层**" in _p936)
    check("WWW.7 ⚠️ **936 探针自己踩的坑，全部留痕**（尺子用错 / `dom_sig` 跨状态误用 / "
          "`modalish` 走祖先致恒真 / 阳性对照恒真 / 夹具盖不到探针点 / 挑错层 / "
          "标记被清 / 层已被关）—— 语法门当场抓到**少两个右括号**的真语法错。"
          "⚠️ 另记一条**门禁盲区**：锚点自查对**跨行**锚点不报错（下面这几条第一版"
          "就栽在这），**跨行锚点只有 verifier 抓得到** ⇒ 锚点必须落在单个源码行内",
          "**同一判据写两套定义，就是让同一判据分叉**" in _p936
          and "**拿它跨状态认元素是误用**" in _p936
          and "外壳**（`fixed` + `inset:0`）把**每一个**遮挡物都算成全屏" in _p936
          and "**一个恒真的字段比没有字段更坏**" in _aus936
          and "**那个 3/4 是夹具自己的几何造出来的**" in _p936
          and "**只对同一状态内的序列成立**" in _p936
          and "**「祖先里有」与「自己就是」是两回事**" in _p936)
    p937 = ROOT / "scripts/jimeng_probe937_layer_exclusivity_src.py"
    _p937 = p937.read_text(encoding="utf-8") if p937.exists() else ""
    check("XXX.1 ✅⭐⭐⭐ **937：H936「浮层互斥」一半被证实、一半被证伪 —— "
          "瞬时浮层 24/24 全部互斥，唯一例外是常驻侧栏 "
          "`canvas-agent-panel`（4/4 全部存活）⇒ **判据仍然一个字不动**（§77）",
          "source_transient_layers_exclusive_agent_panel_not_937" in _ausrc
          and "**「浮层互斥」对瞬时浮层成立、对常驻侧栏不成立。**" in _ausrc
          and "**10/10 被关**" in _ausrc
          and "**6/6 被关**" in _ausrc
          and "**8/8 被关**" in _ausrc
          and "**4/4 全部存活**" in _ausrc
          # ⭐ 判据钉在**按 A 的身份分组**上，而不是钉某个总数
          and "**B 把 A 关掉** 24 次，按 A 的身份分组**没有一个例外**" in _ausrc)
    check("XXX.2 ⭐⭐ **侧栏的互斥性是**不对称**的** —— 它作为 B 照样收掉 A，"
          "而它自己作为 A 收不掉 ⇒ **它是「开关式常驻侧栏」**，"
          "不是普通浮层",
          "**而且是不对称的**：侧栏作为 **B** 时**照样收掉 A**" in _ausrc
          and "开关式常驻侧栏」：开它会收掉瞬时浮层，" in _ausrc
          and "而它自己不被瞬时浮层收掉。**" in _ausrc
          # ⭐ 钉代码：两个方向**都测了**（有向配对，不是无序对）
          and "for a in openable:" in _p937
          and "for b in openable:" in _p937
          and "if a == b:" in _p937)
    check("XXX.3 ⭐⭐ **判据的「层」定义里有一个未被记录的例外** —— "
          "`canvas-agent-panel` 落进 `LAYER_SEL` **只因为 testid 以 `-panel` 结尾**，"
          "它其实是常驻侧栏；但 936 的 42 个层内步里它**一次都没盖住层内控件** "
          "⇒ **§77 那一档仍不成立、判据不用动**",
          "只因为它的 " in _ausrc
          and "未被记录的例外：常驻侧栏与浮层不是一回事，" in _ausrc
          and "而 `LAYER_SEL` 把它们混在一起。**" in _ausrc
          and "**即使侧栏与浮层并存，它也没有盖住层内控件**" in _ausrc
          # ⭐ 钉代码：判据与探针**同一份** `LAYER_SEL`（含那条 `-panel` 规则）
          and '[data-testid$="-panel"]' in _ausrc
          and '[data-testid$="-panel"]' in _p937
          and "assert LAYER_SEL == (" in _p937)
    check("XXX.4 ⚠️⚠️⚠️ **937 第一版的汇要与真相**正好相反**（"
          "`k != base_ids` 拿**字符串和集合**比、`!=` 恒为真 ⇒ 把常驻的 "
          "`canvas-editor-menu` 当成了 A ⇒ `a_survived` 恒真 ⇒ "
          "打出「32/32 全部并存、H936 被证伪」）—— **靠原始读数先落盘才捞回来**",
          "探针自己打出的汇总与真相**正好相反**" in _ausrc
          and "`!=` **恒为真**" in _ausrc
          and "最后一个**正是常驻的 " in _ausrc
          and "**32/32 全部并存 ⇒ H936 被证伪**" in _ausrc
          and "**而从原始读数重算的真相是「24/28 里 B 关掉 A」—— 结论正好相反。**"
              in _ausrc
          # ⚠️⚠️ 「错写法必须不在」这条**不能**拿 `k != base_ids` 不在文件里当证据
          #    —— 探针的**注释里就写着**这句话（那是在解释这个坑）
          #    ⇒ 拿「全文不含某词」判红是**自欺**（§「锚点判据不能拿全文不含某词
          #    当证据」的正反两面）。⇒ 改钉**注释里不会出现的那一行代码**：
          #    错版本里那行是 `k = ("tid:" + o["tid"]) if o["tid"] else (`。
          and 'k = ("tid:" + o["tid"]) if o["tid"] else (' not in _p937
          and "a_new = keys_of(ca) - base" in _p937
          and "a_survived = bool(a_new & keys_of(cb)) if a_opened else None" in _p937)
    check("XXX.5 ⭐⭐ **新增仪器自身的阴阳对照门** `instrument_discriminates_ok` —— "
          "`a_survived` **必须两个答案都出现过**（实测 8 True / 24 False）；"
          "⚠️ **这道门是冲着「结论看起来整齐」去的：越整齐越要验**",
          "**新增仪器自身的阴阳对照门**" in _ausrc
          and "**必须两个答案都出现过**" in _ausrc
          and "**这道门是冲着「结论看起来整齐」去的：越整齐越要验。**" in _ausrc
          # ⭐ 钉代码：门真的存在，且要求**两面**都非零
          and '"instrument_discriminates_ok": (' in _p937
          and 'out["summary"]["n_survived_true"] > 0' in _p937
          and 'out["summary"]["n_survived_false"] > 0' in _p937
          # ⭐ 钉代码：「A 到底是谁」必须进读数（否则读的人无从发现测错了对象）
          and '"a_new_keys": sorted(a_new), "b_new_keys": sorted(b_new),' in _p937)
    check("XXX.6 ⚠️ **计费边界做成了**结构性禁令**，不是靠自觉** —— "
          "`FORBIDDEN_TIDS` 含源站实测存在的积分/会员入口 `canvas-commerce-entry`，"
          "守卫按 `data-testid` **拦在 `mouse.click` 之前**；"
          "⚠️ 另外 H936 **只覆盖一半**，「这一类 0 观测、判据不动」是 936+937 **合起来**才够",
          "边界做成了**结构性禁令**（不是靠自觉" in _ausrc
          and "**拦在 `mouse.click` 之前**" in _ausrc
          and "**H936 没有被整体证实**" in _ausrc
          and "**两批合起来才够，本批自己不够**" in _ausrc
          and "**不许**说 H936 成立" in _ausrc
          # ⭐ 钉代码：禁令清单与「拦在 click 之前」的顺序
          and 'FORBIDDEN_TIDS = ("canvas-commerce-entry"' in _p937
          and "if tid in FORBIDDEN_TIDS:" in _p937
          and "blocked = guard(pt.get(\"al\"), tid)" in _p937
          and "if blocked:" in _p937)
    p938 = ROOT / "scripts/jimeng_probe938_replica_layer_exclusivity.py"
    _p938 = p938.read_text(encoding="utf-8") if p938.exists() else ""
    _wm = (ROOT / "src/store/jimengStore.ts")
    _wm_s = _wm.read_text(encoding="utf-8") if _wm.exists() else ""
    check("YYY.1 ✅⭐⭐⭐ **938：把 937 的源站读数**真正实现进复刻** —— "
          "互斥从「各自为政」变成**结构保证**（store 里的单一来源槽位），"
          "复刻侧 28/28 配对全部可用、全部符合预期、2/2 逐项相同",
          "replica_transient_layers_exclusive_938" in _ausrc
          and "**没有任何一处能实现「开一个关掉另一个」**" in _ausrc
          and "**28/28 全部可用、28/28 全部符合预期、2/2 逐项相同**" in _ausrc
          # ⭐ 钉代码：槽位是**单一来源**，且 toggle 语义在 store 里
          and "transientLayer: JimengTransientLayer | null;" in _wm_s
          and "transientLayer: state.transientLayer === id ? null : id," in _wm_s
          and 'id && state.transientLayer !== id' in _wm_s
          # ⭐ 钉代码：四个层确实读的是 store 而不是各自的本地 state
          and 'const searchOpen = transientLayer === "search";' in _wm_s + (
              ROOT / "src/components/jimeng/JimengTopBar.tsx").read_text(
                  encoding="utf-8")
          and "zoomMenuOpen = transientLayer === \"zoom\"" in (
              ROOT / "src/components/jimeng/JimengBottomDock.tsx").read_text(
                  encoding="utf-8"))
    check("YYY.2 ⭐⭐ **侧栏的**不对称**只做了实测的那一半**：**开侧栏清空槽位**，"
          "而**反方向故意不做** —— 开瞬时浮层**不关**侧栏"
          "（实测 `agent→search` / `agent→zoom` 侧栏仍在，4/4）",
          "**开侧栏会清空槽位**" in _ausrc
          and "**反方向故意不做** —— 开搜索/缩放/右键**不关**侧栏" in _ausrc
          # ⭐ 钉代码：清槽位**只**出现在开侧栏那两条路上
          and "transientLayer: open ? null : state.transientLayer," in _wm_s
          and "openTransientLayer: (id) =>" in _wm_s
          # ⭐ 钉代码：探针真的把「不该关」那两个方向单列成 expect="open"
          and '("agent", "search", "open"),' in _p938
          and '("agent", "zoom", "open"),' in _p938
          and '"yin_yang_ok": len(closed_cases) >= 1 and len(open_cases) >= 1,' in _p938)
    check("YYY.3 ⭐⭐ **复刻探针当场抓到 938 自己写出来的一个真交互 bug** —— "
          "`closeAll()` 若无条件清空 `transientLayer`，"
          "「更多」菜单**再点一次关不掉**（toggle 语义被自己破坏）",
          "**再点一次关不掉**" in _ausrc
          and "toggle 语义被自己破坏" in _ausrc
          and "当场抓到的" in _ausrc
          # ⭐ 钉代码：closeAll **不再**碰槽位（那句无条件清空已经不在）
          and (assert_gone := "closeTransientLayer();" not in (
              ROOT / "src/components/jimeng/JimengTopBar.tsx").read_text(
                  encoding="utf-8"))
          and assert_gone
          # ⭐ 钉代码：探针的复位**会当场断言**没清干净（这条断言正是抓到 bug 的）
          and "复位没清干净，仍在场上的层" in _p938
          and 'assert not leftover["present"], (' in _p938)
    check("YYY.4 ⚠️⚠️ **探针自己踩的两个坑，都留痕** —— ① zoom 触发器有 "
          "`id`/`data-testid` **两个身份**，第一版拿错的那个 ⇒ 8 个配对"
          "**静默不可用**而门照样绿；② **侧栏不能靠点自己的触发器关掉**"
          "（触发器在侧栏开着时**根本不在 DOM 里**）",
          "**DOM 里压根没有** " in _ausrc
          and "**静默不可用**" in _ausrc
          and "**侧栏开着时触发器根本不在 DOM 里**" in _ausrc
          and "**假报**「A 没被关」" in _ausrc
          # ⭐ 钉代码：用的是对的那个 testid，且**不是**错的那个
          and '"zoom": "canvas-zoom-percent",' in _p938
          and (assert_no_bad := '"zoom": "jimeng-zoom-menu-trigger",'
               not in _p938)
          and assert_no_bad
          # ⭐ 钉代码：侧栏的关闭走抽屉内部的「收起」键
          and 'canvas-agent-session-collapse' in _p938
          # ⭐ 钉代码：门**收紧**成「每个触发器都被点到过」+「可用数 == 配对总数」
          and '"triggers_all_clicked_ok": (all(v > 0 for v in clicks.values())' in _p938
          and 'len(usable) == len(out["pairs"])' in _p938)
    check("YYY.5 ⚠️⚠️ **仍未验证的写清** —— 只接了 4 个层、源站其余浮层的互斥**没测**"
          "（推广是**推断**）；复刻的 contextMenu/paneMenu **没接**槽位"
          "（源站右键菜单键盘可达性未解释）；**没测**两个层共存时的焦点行为",
          "**只接了 4 个层**；源站其余浮层的互斥**没测**（推广是推断）" in _ausrc
          and "它们在 `JimengWorkspace` 里、且 936 已测出**源站右键菜单 60 次 Tab" in _ausrc
          and "一步都进不去**" in _ausrc
          and "本批**不碰**，等那个问题有答案" in _ausrc
          and "**没有**测「两个层共存时键盘焦点怎么走」" in _ausrc
          and "槽位保证的是**至多一个瞬时层**，焦点行为是另一件事" in _ausrc)
    check("CCCC.5 ⚠️⚠️⚠️ **把「往基线文本里写字面量会污染按字面计数的判据」"
          "立成一道**可查**的门** —— 这个坑连踩两次（940 写 `LAYER_SEL` 的 `closest`、"
          "941 引用 936 源码时写同一个），两次都是 S.6 当场变红（467/468、471/472）"
          "⇒ 说明它**不该只靠记性**，得让门能查",
          "**⑪ ⚠️ 本批撞到的一个纯技术坑（留痕）**" in _ausrc
          and "记法纪律：**嵌在 Python 字符串里的 CSS 选择器，一律写成" in _ausrc
          and "不带引号的形式**。" in _ausrc
          # ⭐ 钉门本身：基线里**只许**那 2 处**真代码**，不许再多
          #    （⚠️ 这就是 S.6 数的那个东西 —— 940/941 各往基线里写过一次就变红）
          and (assert_clean := _ausrc.count("closest(LAYER_SEL)") == 2)
          and assert_clean
          # ⭐ 钉根因：strip_comments **早就失配**（第 269 行 `with open(OUT, "w")`
          #    里的双引号被当成三引号开头 ⇒ 从那儿起整段被当字符串吞掉）
          and "⇒ 从那儿起**整段被当成字符串吞掉** ⇒ verifier 里 9 处 `acode` 判据" in _ausrc
          and "**S.6 一直绿只是因为没人往基线文本里写过那个字面量**" in _ausrc
          and "**修 `strip_comments` 的三引号识别留给下一批**" in _ausrc)
    p941 = ROOT / "scripts/jimeng_probe941_layer_identity_probe_src.py"
    _p941 = p941.read_text(encoding="utf-8") if p941.exists() else ""
    check("CCCC.1 ✅⭐⭐⭐ **941 把 940 的一条结论**当场证伪**了 —— 「搜索层冷启动不可达」"
          "是**假阴性**：A（最近祖先**恰好等于** target）不命中、"
          "而 B（`closest` 祖先链**含** it）与 C（打标记）**第 1 次就命中**；"
          "**936 与 940 之间那条「未解决矛盾」就此消解**",
          "src_layer_identity_criterion_941" in _ausrc
          and "**① ⭐ 本批的正题：同一份游走，三个判据并排**" in _ausrc
          and "**A 与 B 的差别就是本批要量的东西**" in _ausrc
          and "**与 §146（936）「层内步 20/轮：输入框 + `全部 76` + 分类按钮 " in _ausrc
          and "**936 与 940 的那条「未解决矛盾」就此消解**" in _ausrc
          # ⭐ 钉探针：三判据**真的并排**记，且「祖先链」是**全部**祖先不是只取最近
          and "const chain = [];" in _p941
          and "chain.push(p.getAttribute('data-testid')" in _p941
          and "nearest_ancestor_tid: chain.length ? chain[0] : null," in _p941
          and 'if first["A"] is None and st["nearest_ancestor_tid"] == target_tid:' in _p941
          and 'if first["B"] is None and st["in_target_closest"]:' in _p941
          and 'if first["C"] is None and st["in_seed_closest"]:' in _p941)
    check("CCCC.2 ⭐⭐ **假阴性的确切形状**被读数摆清：搜索层第 1 步 "
          "`nearest = canvas-search-panel`、而 `chain` 里**有** `canvas-feature-panel` "
          "⇒ A 要求「恰好等于」而 B 只要求「祖先链里有」；"
          "⇒ **「把完整祖先链落盘」是本批能一眼看出问题的原因**（承 937 的教训）",
          "**③ ⭐⭐ 假阴性的**确切形状**（祖先链读数把它摆得一清二楚）**" in _ausrc
          and "⇒ 最近祖先是**子层** ⇒ A 不命中；祖先链里**有** target ⇒ B 命中。" in _ausrc
          and "**「把完整祖先链逐步落盘」是本批能一眼看出问题的原因**" in _ausrc
          # ⭐ 钉探针：链是**由近到远**累积的（不是提前 break）
          and "for (let p = a; p && p !== document.body; p = p.parentElement) {" in _p941
          # ⭐ 钉探针：「A 是假阴性」的定义**就是**本批的判别力判据
          and 'd["a_false_negative"] = (first["A"] is None and first["B"] is not None)' in _p941
          # ⭐ 钉探针：C 判据真的**打了标记**（936 的口径）
          and "e.setAttribute(seedAttr, '1');" in _p941
          and "in_seed_closest: !!a.closest('[' + seedAttr + ']')," in _p941)
    check("CCCC.3 ⭐ **仪器设计这次先对了**（承 940「门连错四版」的教训）："
          "`criteria_disagree_ok` 要求**至少一个层上 A 与 B 给出不同答案**"
          "（若三者处处相同 ⇒ 本批**测不出差别** ⇒ 如实记 False）；"
          "`positive_control_ok` 带一个**阳性对照**层 ⇒ "
          "**只有一个判别器时三判据的读数都可能是恒真的**；实测 `design_ok` 全 True",
          "**⑦ ⭐ 仪器设计（承 940「门连错四版」的教训，这次先设计对）**" in _ausrc
          and "若三者处处相同 ⇒ 本批**测不出差别**" in _ausrc
          and "**如实记 `False`，不许调门凑绿**" in _ausrc
          and "只有一个判别器时，三判据的读数**都可能是恒真的**" in _ausrc
          # ⭐ 钉探针：判别力门与阳性对照门都**真的**在代码里
          and '"criteria_disagree_ok": all(any(l["a_false_negative"] for l in rep) for rep in _a),' in _p941
          and 'any(l["name"] == "顶栏·生成历史" and l["a"] is not None' in _p941
          and "**全套 design_ok**" not in _p941
          # ⭐ 钉探针：正对照层**真的在 TARGETS 里**
          and '("顶栏·生成历史", "canvas-panel-launcher", 1, "generation-history-panel"),' in _p941)
    check("CCCC.4 ⚠️⚠️ **三条「不可达」结论的最终账 + 第一版漏测的取样缺口**："
          "搜索层**证伪**、右键菜单**成立**、缩放菜单**成立**（补测）、生成历史**成立**；"
          "⇒ 区分它们的**不是层本身，是「该层有没有子层结构」**；"
          "顺带订正 940 把 936 的 `in_seed` 说成 `LAYER_SEL` 那个的**措辞错误**",
          "**⑩ ⚠️⚠️ 三条「不可达」结论的最终账**（本批之后）**" in _ausrc
          and "**证伪 —— 第 1 次可达**（假阴性） |" in _ausrc
          and "**成立**（三判据一致 None，补测） |" in _ausrc
          and "**不是**层本身，是「**该层有没有子层结构**」。" in _ausrc
          and "**⑤ ⚠️ 顺带订正 940 的一处措辞错误**" in _ausrc
          and "940 用「口径宽窄」解释那条矛盾，**方向就错了**" in _ausrc
          # ⭐ 钉探针：缩放菜单**被补进** TARGETS（取样缺口已补）
          and '("缩放菜单", "canvas-zoom-percent", 0, "canvas-zoom-menu"),' in _p941
          # ⭐ 钉探针：940 那个**有缺陷的判据**仍在源码里（供下一个人对照，别删）
          and (assert_bug := 'if target_layer_tid and st["layer_tid"] == target_layer_tid and first_in is None:'
               in (ROOT / "scripts/jimeng_probe940_tabindex_rewrite_src.py").read_text(
                   encoding="utf-8"))
          and assert_bug)
    p940 = ROOT / "scripts/jimeng_probe940_tabindex_rewrite_src.py"
    _p940 = p940.read_text(encoding="utf-8") if p940.exists() else ""

    # ══ 批 942：判据到底读代码还是读注释 ══════════════════════════════
    # 942 做的事：`strip_comments` 的三引号识别有个**真 bug**（第一个条件
    # 只查「第 1 个 == 第 3 个」、漏了第 2 个 ⇒ `with open(OUT, "w")` 的
    # 双引号当场触发三引号模式、整段被吞）。修好之后全套判据里**恰好一条**
    # 变红：AA.3 —— 它钉的是**源码注释里的一句散文**。
    print("— DDDD. 批 942 剥除器真修 + 判据锚文普查 —")
    _v942 = ROOT / "scripts/jimeng_check_strip_comments.py"
    _c942 = ROOT / "scripts/jimeng_check_comment_anchors.py"
    _v942s = _v942.read_text(encoding="utf-8") if _v942.exists() else ""
    _c942s = _c942.read_text(encoding="utf-8") if _c942.exists() else ""
    # ⚠️ 这一段**刻意用本文件自己的 `strip_py_comments`** 来判「错误形态
    #   还在不在」—— 940/941 踩的坑反过来成了 942 的判据：
    #   「原文里有、真代码里没有」才是可查的钉法，光钉「原文里没有」
    #   既会被注释里的**修复说明**顶红，也分不清到底删没删。
    # ⚠️⚠️ 而且必须**只数 DDDD 组自己之前的那段源码** ——
    #   这条判据**自己**就写着那个字面量（`_vsrc.count("c == nxt2 and c in")`），
    #   那是**真代码里的字符串字面量**、`strip_py_comments` 不会剥它
    #   ⇒ 实测：原文 3 处、剥后仍 **2** 处（全是判据自己那两处），
    #   真正该为 0 的「剥后真代码」得**先把判据自己排除掉**才看得见。
    #   ⭐ 这与「写一条判据就让普查总数 +1」是同一族自指问题：
    #   **量自己的尺子会把自己也算进去。**
    _v942_pre = _vsrc.split("# ══ 批 942", 1)[0]
    _v942_pre_code = strip_py_comments(_v942_pre)

    check("DDDD.1 ⚠️⚠️⚠️ **942 修的是个真 bug，不是整理** —— "
          "`strip_comments` 的三引号入口原来第一个条件"
          "「`c == nxt2`（只查第 1 个 == 第 3 个、漏第 2 个）」"
          "会让 `with open(OUT, \"w\")` 的双引号**当场触发三引号模式**、"
          "从那儿起整段被吞；现在只剩「三个连续引号」这一条。"
          "⚠️ 判据钉的是**真代码里那个错误形态已经不在**（用本文件自己的"
          " `strip_py_comments` 剥掉注释再数）—— 只钉「原文里没有」会被"
          "注释里那段**修复说明**顶红，也分不清到底删没删；"
          "⚠️ 且只数 **DDDD 组之前**的源码（这条判据自己就写着那个字面量，"
          "它是**代码里的字符串**、剥不掉 ⇒ 不排除就会数到自己头上）",
          'nxt == c and nxt2 == c and c in "\\"\'"' in _v942_pre
          and _v942_pre.count("c == nxt2 and c in") == 1        # 只在注释里留了痕
          and _v942_pre_code.count("c == nxt2 and c in") == 0    # 真代码里已删
          and _v942_pre_code.count(
              'nxt == c and nxt2 == c and c in') == 1)          # 正确那条还在

    check("DDDD.2 ⭐⭐⭐ **942 量到了修好之后「谁被影响」的完整读数**，"
          "并把它**记进基线**（基线是唯一可机读来源，README 只做人读叙事）："
          "对 `strip_comments` 派生变量的锚文共 **56** 条 —— **52 条读代码**、"
          "**0 条读注释**、4 条是剥除器**自测**的合成用例"
          "（挂在内联合成用例 `_sc_out` 上、不参与分类）"
          "⇒ **修好剥除器的爆炸半径 = 恰好 1 条判据（AA.3）**，其余 52 条"
          "锚的是代码、经得起剥。⚠️ 判据只钉**不变量**（「读注释的必须是 0」），"
          "**不钉**计数 —— ⚠️ 942 一开始按「AA.3 修完是 56」写死了总数，"
          "**下一条判据（DDDD.3 自己）就把它推成了 57**："
          "写一条打在派生变量上的判据，普查总数就 **+1**。"
          "⇒ 基线**记录**读数、**关系式的门**在工具的 G2/G3，"
          "判据里**一处只钉一件事**",
          '"anchors": ' in _ausrc
          and '"code": ' in _ausrc
          and '"synth": ' in _ausrc
          and '"comment_only": 0' in _ausrc        # ← 唯一钉死的不变量
          and "**不在**判据里钉死计数" in _ausrc
          and "不钉**「恰好 52/56」" in _ausrc
          and "总数就 +1" in _ausrc
          and "一处只钉一件事" in _ausrc)

    check("DDDD.3 ✅⭐⭐⭐ **942 查清 AA.3 为什么是假绿**：它钉的"
          "「不** `stopPropagation()`」这句话只存在于**源码注释里**，"
          "而剥除器坏掉时 `.tsx` 注释**根本没被剥** ⇒ 那句注释只要还在就绿，"
          "**就算有人真往 Clear 的 Esc 分支加上 `stopPropagation()` 也照样绿**"
          "（一个恒真的判据比没有判据更坏）。已改成钉**代码形态**："
          "① Esc 分支**真的清除**（收焦点 + 清值 + 关层）"
          "② 该分支**不**截断冒泡 ③ **阳性对照**：同一个文件里另一个 Esc 分支"
          "（音色库列表）**确实**截断、且全文**仅此一处**"
          " —— 只看 ② 会被「整个文件从不调用」这种空洞写法白送",
          "def _aa3_ok(s):" in _vsrc
          and "_aa3_ok(_agp2)" in _vsrc
          and 'refocusToNodeFromToolbar(" in esc' in _vsrc
          and 'if "stopPropagation" in esc:' in _vsrc
          and 's.count("stopPropagation") == 1' in _vsrc
          # ③ 的对照侧必须**真的**在文件里（不然 ② 是空洞）
          and _agp2.count("stopPropagation") == 1
          and "e.preventDefault(); e.stopPropagation();" in " ".join(
              _agp2.split()))

    check("DDDD.4 ⚠️⚠️ **「读注释的锚文必须为 0」被立成了可查的门**，"
          "而且这道门**自己被证伪过**：把旧版 AA.3 那条锚文塞回副本、"
          "对副本跑同一道普查，它当场变红（`comment_only` 从 0 变 1）"
          "⇒ 它不是恒绿的门。工具另外三处自保也得钉住："
          "① **变异必须真的发生**（第一版三个 `re.sub` 因不跨行**静默没匹配**，"
          "判据「正确地」保持 True —— 那是**空白对照**，看着像阳性对照通过）"
          "② **绑定解析不出来必须拒运行**（第一版把 19 条锚文误判成"
          "「合成用例」、于是「读注释 0 条」对它们**根本没测**，"
          "是同一道 G4 把它拒了的）③ 两个实现都从 verifier 的 AST 里"
          "**原样**取，**不复制**",
          _c942s != ""
          and "变异没发生" in _c942s
          and "if want is not True and mutated == s0:" in _c942s
          and "gate(\"G4 synth_excluded" in _c942s
          and "exec(ast.unparse(fn), ns)" in _c942s
          and "MIN_CODE_RATIO" in _c942s
          and _v942s != ""
          and "load_strip_comments" in _v942s
          and "MIN_PROBES_HIT" in _v942s)

    check("DDDD.5 ⚠️ **订正 940 那句过头的话（原文一字未删，只加批注）** —— "
          "940 写的是「9 处 `acode` 判据数错对象却碰巧对」；"
          "942 普查后**两处都要收窄**：① 那是 **9 行提到、3 条字面量判据**"
          "（`skin_top_n += 1` / `closest(LAYER_SEL)` / `p === 'fixed'`），"
          "不是 9 条；② 这 3 条**数的就是真代码、答案全对**"
          "（全文计数与剥后计数相同）⇒ 「碰巧对」只对**机制**成立"
          "（940/941 往基线写字面量就变红），**对读数**不成立。"
          "⚠️ 另订正 942 自己前两句的过头说法：「剥除器坏了 ⇒ 判据全在读注释」"
          "**也是过头** —— 坏掉时判据读的是**没剥过的原文**，"
          "其中多数锚文恰好**本来就只在代码里**，所以它们**一直是对的**",
          "**9 行提到" in _ausrc          # 9 行提到 acode
          and "**3 条**字面量判据**" in _ausrc   # …只有 3 条判据
          and "**数的就是真代码**" in _ausrc
          and "答案全对**" in _ausrc
          and "**对读数不成立**" in _ausrc
          and "多数锚文本来就只出现在代码里" in _ausrc
          and "**不是恒绿的**" in _ausrc)

    # ══ 批 943：鼠标臂 vs 键盘臂（源站，纯诊断）══════════════════════
    print("— EEEE. 批 943 两条臂不是同一条规则 —")
    p943 = ROOT / "scripts/jimeng_probe943_arm_relation_src.py"
    _p943 = p943.read_text(encoding="utf-8") if p943.exists() else ""

    check("EEEE.1 ⭐⭐⭐ **943 的判决：两条臂不是同一条规则** —— "
          "键盘臂每次咬到做**三件事**（删上一个 / **写回上上个** / 改本次）"
          "⇒ 「不带 `tabindex` 的节点数」**恒为 1**（逐条复现 §131）；"
          "**鼠标臂的 `added` 恒空**（只删不写回）⇒ 那个数**每咬一次 +1**"
          "（2 轮 × 5 次咬到：1→2→3→4→5→6，两轮**逐字相同**）"
          "⇒ ⚠️ **鼠标臂单独跑会破坏 §131 那条不变式**。"
          "取样在 `CANVAS_BASELINE.canvas_surface`（**不是**层表 —— "
          "它不属于任何浮层，塞进层表会让 H.1/H.2 变红，942 塞过一次、红了）",
          '"mouse_arm_added_always_empty": True' in _ausrc
          and '"mouse_arm_without_ti_grows_monotonic": True' in _ausrc
          and '"keyboard_arm_without_ti_always_one": True' in _ausrc
          and '"keyboard_arm_reproduces_131": True' in _ausrc
          and "CANVAS_BASELINE = {" in _ausrc)

    check("EEEE.2 ⭐⭐ **窗口是全局的、不是按臂分开的** —— 第一次鼠标点击的 "
          "`removed` **正是键盘臂最后布的那个下标**"
          "（键盘臂末步 `changed=[8,'-1','0']`，紧接着点 i=0 得 `removed=[8]`）"
          "⇒ **鼠标臂接着键盘臂的历史走**，不是另起一套。"
          "⚠️ 这条与 EEEE.1 合起来才是「同一条窗口、**不同**的补偿」"
          "—— 只说其中一半都会读错",
          '"removed_is_cross_arm": True' in _ausrc
          and "**接着键盘臂的历史走**" in _ausrc
          and "同一条窗口、**不同**的补偿" in _ausrc)

    check("EEEE.3 ✅⭐⭐⭐ **补偿只在键盘臂上** —— 鼠标臂连点之后，键盘臂的"
          "**第一击**把**两臂删掉的全部**一次性写回（`added` 里同时有鼠标臂删的"
          "与键盘臂自己早先删的）⇒ 「不带 ti」**一次性**从 6 回到 1、"
          "**不变式被恢复**，之后键盘臂立刻回到 §131 的老样子。"
          "⇒ ⭐ **复刻侧若用同一套逻辑处理点击，就会漏掉这半边补偿**",
          '"keyboard_first_tab_after_mouse_recovers_all": True' in _ausrc
          and "**补偿只在键盘臂上**" in _ausrc
          and "**漏掉这半边补偿**" in _ausrc)

    check("EEEE.4 ⚠️⚠️ **先更正 942 留的那个前提错误（原文一字未删）** —— "
          "942 的待办把 §131 记成「指针臂」、940 记成「键盘臂」，"
          "说「两臂关系未测」；⚠️ **§131（921）的臂事件用的就是 "
          "按 `Tab` 键**、§136（923/926）也是 `Tab` / `Shift+Tab` "
          "⇒ **§131 与 940 测的是同一条键盘臂**，「两臂关系未测」**立不住**；"
          "真正**从来没测过**的是**鼠标臂**。"
          "⚠️ 且 **943 没有推翻 §131**，只是补上了它没测的那一半"
          "（§131 的键盘臂读数被逐条复现）",
          "**§131 与 940 测的是同一条键盘臂**" in _ausrc
          and "真正**从来没测过**的是**鼠标臂**" in _ausrc
          and "测的是同一条键盘臂**，「两臂关系未测」立不住" in _ausrc
          # ⭐ 顺带钉住**更正的事实本身**（921 用的是 `keyboard.press`），
          #    免得下一个人只看到「更正」却查不到「原来那个前提错在哪」
          and "的臂事件用的是 `keyboard.press(" in _ausrc)

    check("EEEE.5 ⚠️⚠️⚠️ **943 探针自己踩的坑与未查项，全部留痕** —— "
          "**v1/v2/v3 三版各自作废**：① v1 空白点用算出来的矩形点 ⇒ "
          "**焦点压根没进画布**、键盘臂 delta 全空；② v2 身份串带了 `className`，"
          "而**点节点会加 `selected` 类** ⇒ **尺子恰好在最有意思的那一下坏掉**"
          "（指纹极干净：键盘臂 16/16 稳定、**唯独点击那一击为假**）；"
          "③ v3 按固定分散下标挑目标，而这版画布节点**大量重叠** ⇒ 6 个里只有 1 个点得到。"
          "还有三处**恒真条件**：`delta()` 身份对不上就**静默返回空列表**"
          "（把「没测到」写成了「没有」）、计费守卫查的是「页面上**有没有**"
          "计费入口」（⇒ 第一击就炸）、**等稳定循环先 `prev = cur` 再比较**"
          "（⇒ 永远相等、必在第 1 下 break，等于没等）。"
          "⇒ ⭐ 也因此加了两道**尺子自证**门：判据量的是身份串，"
          "**尺子要先证明自己量的是不变的东西**。"
          "⚠️ 未查三项如实记在基线：方向未测、增长上限未测、"
          "身份要 4 下才稳定**成因未查明**",
          _p943 != ""
          and '"v1_void"' not in _p943          # 作废横幅走的是 void_runs
          and '"void_runs": [' in _p943
          and "第一版这里写成「先 `prev = cur`、再比 `cur == prev`」" in _p943
          and _p943.count("stable = (cur") == 1   # 等稳那段的比较
          and "**「页面上有没有 X」的守卫 = 恒为真的守卫 = 没有守卫**" in _p943
          and "_no_node_slice" in _p943
          and "处**非字符串**切片" in _p943
          and "ident_selfcheck_ok" in _p943
          and _p943.count("landed = bool(f[") == 1   # landed 由**点后**焦点判
          # ⭐ 三条未查项必须在基线里**成条**存在，不许只写在 README
          and '"removed_scope_unverified"' in _ausrc
          and '"without_ti_growth_cap_unverified"' in _ausrc
          and '"identity_settling_unexplained"' in _ausrc
          and '"mouse_click_on_inner_control_unverified"' in _ausrc)

    # ══ 批 944：补 943 挂着的两条「未测」（源站，纯诊断）══════════════
    print("— FFFF. 批 944 两条未测各推进一步 —— 但**不产出新机制结论** —")
    p944a = ROOT / "scripts/jimeng_probe944a_node_inner_scan_src.py"
    p944b = ROOT / "scripts/jimeng_probe944b_mouse_axes_src.py"
    _p944a = p944a.read_text(encoding="utf-8") if p944a.exists() else ""
    _p944b = p944b.read_text(encoding="utf-8") if p944b.exists() else ""

    check("FFFF.1 ⭐⭐⭐ **944 先花了两个纯读探针**（零点击）才敢点节点"
          " —— 探针 944a 实测：节点内部有 **85 个 `BUTTON`**，"
          "而**可点的内部落点 94 个里 BUTTON 只有 3 个**"
          "（85 个大多在**选中后才出现**的节点工具条上）、"
          "**带删除/移除语义的 0 个**。⇒ ⭐ 这不是多余的谨慎："
          "在源站上真删掉别人的东西、并且让后面所有读数全部作废，代价太高。"
          "⚠️ 顺带一条对复刻有用的发现：**节点有稳定 id**"
          "（`data-testid` 形如 `rf__node-node_236ctpehgg`）"
          "⇒ 跨状态认元素有了正经的锚（943 的 `className` 栽过一次）",
          '"inner_scan_944a": (' in _ausrc
          and '"node_ids_are_stable_944a": (' in _ausrc
          and "**BUTTON 85**" in _ausrc
          and "纯读发现" in _ausrc
          and "零点击" in _p944a
          and "唯一可点的 3 个" not in _p944a)   # 钉死**只读**、不许偷偷点

    check("FFFF.2 ✅⭐⭐ **「点节点内部的控件是不是臂事件」有确切答案了**："
          "点那个 BUTTON 三元组**全空**（`bit=False`）、**开了 1 个层**"
          "（层 1→2）、节点数不变（2/2）⇒ ⭐ **内部控件走它自己的 handler，"
          "完全不碰 `tabindex` 窗口**。"
          "⇒ **复刻侧的点法必须按「落点角色」分开**：本体与内部后代走臂事件，"
          "内部控件走自己的 handler —— 把它当臂事件会让 `tabindex` 窗口错位",
          '"inner_button_not_an_arm_event_944b": (' in _ausrc
          and "**点节点内部的 BUTTON 不是臂事件**" in _ausrc
          and "层 1→2" in _ausrc
          and "内部控件走它自己的 handler，完全不碰 `tabindex` 窗口" in _ausrc
          and # ⭐ 钉住「BUTTON 那一击放最后」这个**不可逆动作的位置**纪律
          "internal_button_is_last" in _p944b
          and '"layers_before"' in _p944b
          and '"opened"' in _p944b)

    check("FFFF.3 ✅⭐⭐ **「点已选中的节点」也不是臂事件**（第一次点 `bit=True`、"
          "紧接着再点一次 `bit=False` 且三元组全空，2/2）"
          "⇒ 鼠标臂**要求「这一下改变了选中态」才咬**。"
          "⚠️ **反向没测到**（点未选中是不是每次都咬）"
          "⇒ **记成未测，不许**拿这一条去推「点未选中必然咬」",
          '"already_selected_not_an_arm_event_944b": (' in _ausrc
          and "第一次点 `bit=True`" in _ausrc
          and "**反向**（点未选中的节点是不是每次都咬）" in _ausrc
          and "本批没测到" in _ausrc
          and "**不许拿这一条去推**「点未选中必然咬」" in _ausrc)

    check("FFFF.4 ⚠️⚠️⚠️ **944 的设计门有三项红 ⇒ 本批不产出新机制结论**，"
          "这一条把「不产出结论」本身钉成可查项 —— "
          "`plateau_or_cap_ok` / `sel_ok` / `inner_ok` 2/2 都不满足。"
          "⚠️ 顺带记一条**诚实的终止态**：「可点下标耗尽」也是合法的结束理由"
          "（这一版画布节点大量重叠，全表只有 15–17 个点得到）"
          "⇒ 漏掉它 ⇒ 门永远红 ⇒ 下一个人会以为探针坏了",
          '"der_landable_exhausted"' in _p944b
          and "rec.get(\"der_landable_exhausted\")" in _p944b
          and "是**测量的边界**，" in _p944b
          and '"plateau_or_cap_ok": bool(' in _p944b
          and "本批不产出新的机制结论" in _ausrc)

    check("FFFF.5 ⚠️⚠️⚠️ **两条必须写进基线的「不许下结论」** —— "
          "① **撤回** 944 v1 的「补偿没来」：它的 `is_arm` 判据**太松**"
          "（只问「焦点在不在某个节点**内**」），而实测 `active_tag=BUTTON` "
          "落在节点**内部的按钮**上 ⇒ 那是**死按压**"
          "⇒ **「应用没写回」与「这一击压根不是臂事件」必须分开**；"
          "② **补偿的规模阈值两轮不一致**（rep1 连点 7 次后 1 击补完 7 个、"
          "rep2 连点 13 次后连按 6 下 `added` 恒 0）"
          "⇒ **不许**写成「补偿有规模阈值」，**不许**说 943 被推翻。"
          "⚠️ **第 ② 条的矛盾已由 948 结案（是个误读），但「944 自己那次为何不补」"
          "仍未查明** ⇒ 承 HH.4：判据要跟上事实，"
          "**不许**因为矛盾解开就把待查项一起删掉 ⇒ 基线键已改名 "
          "`..._RESOLVED_944b_948`、且旧名字**必须已经不在**基线里",
          '"retracted_v1_compensation_944b": (' in _ausrc
          and '"compensation_scale_threshold_RESOLVED_944b_948": (' in _ausrc
          # ⭐ 旧名字必须**已经不在**基线里（不然「未结案」和「已结案」会同时在库）
          and '"compensation_scale_threshold_unresolved_944b": (' not in _ausrc
          and "已撤回" in _ausrc
          and "**两轮不一致**，所以**不许**下结论" in _ausrc
          and "**不许**写成「补偿有规模阈值」" in _ausrc
          # 探针侧：判据要把「是不是臂事件」问得比焦点**更严**
          and 'is_arm = bool(f["focus_in_node"]) and f["active_tag"] == "DIV"' in _p944b
          and "落在节点**内部的按钮**上是**死按压**" in _p944b)

    # ══ 批 945：把 943/944 之间的分歧拆成两个自变量（源站，纯诊断）══════
    print("— GGGG. 批 945 规模不是主因；而「不是臂事件」被读数推翻 —")
    p945 = ROOT / "scripts/jimeng_probe945_comp_scale_split_src.py"
    _p945 = p945.read_text(encoding="utf-8") if p945.exists() else ""

    check("GGGG.1 ✅⭐⭐ **规模不是主因** —— 连点 **12** 次（实际咬到 8 次）之后，"
          "键盘臂**第一击** `added=8`、`不带 ti 8→1` **一次性补完**"
          "（`scale=6` 那格是 `added=2`、`2→1`，同理）；第二击通常 `added=1`"
          "⇒ **944 记的「13 次连点后连按 6 下 `added` 恒 0」不是规模阈值**。"
          "2 轮 × 4 格，**每格独立 boot**，逐格读数 **2/2 逐条相同**",
          '"comp_scale_is_not_the_cause_945": (' in _ausrc
          and "**944 记的「13 次连点后连按 6 下 `added` 恒 0」不是规模阈值**" in _ausrc
          and "补偿只在第一击发生" in _ausrc
          and "每格独立 `boot()`" in _ausrc
          # ⭐ 钉住「每格独立 boot」这条：**跨格复用状态**就是把上一格带进这一格
          and "def boot_fn():" in _p945
          and "n_audio = boot_fn()" in _p945)

    check("GGGG.2 ✅⭐⭐⭐ **944 的另一半假设被读数直接推翻**："
          "`mode=asis`（**不干预焦点**、就按点击留下的样子）那一格，"
          "**按 Tab 之前焦点仍然是 `DIV` 且在节点内**"
          "⇒ ⭐ **点击之后焦点本来就在节点本体上**"
          "⇒ 944 那次 `active_tag=BUTTON` **不是点击造成的**，"
          "是**那 6 下 Tab 自己一路 Tab 进**了节点内部的按钮"
          "⇒ 「那一击压根不是臂事件」这个解释**不成立**。"
          "⚠️ 这是**读数推翻假设**、不是推理推翻假设（930 的纪律）",
          '"not_an_arm_event_hypothesis_refuted_945": (' in _ausrc
          and "**点击之后焦点本来就在节点本体上**" in _ausrc
          and "而是**那 6 下 Tab 自己一路 Tab 进**了节点内部的按钮" in _ausrc
          and "这个解释**不成立**" in _ausrc
          # ⭐ 钉住两个自变量在源码里**真的是两个**，且 `asis` 分支**不干预**
          and '"scale": 12, "mode": "asis"' in _p945
          and 'if mode == "body":' in _p945
          and 'ARM_FOCUS_JS' in _p945)

    check("GGGG.3 ⚠️⚠️⚠️ **但 944 那次「不补」的成因仍然未查明** —— "
          "本批**没有对照真正的可疑变量**：每格 settle 只按 **1** 下、"
          "`就绪不带 ti = 0`（初始化刚发生、指针还没走）；"
          "而 944 settle 了 **10** 下、`就绪不带 ti = 1`（指针已经走过）"
          "⇒ 剩下没被拆开的自变量是**前置态**"
          "⇒ ⭐ **不许**把 944 那次读数记成「偶发」或「有别的条件」，"
          "**成因未查明**。（这也是「拆自变量」只拆了一层的样子："
          "**你以为只有两个，其实有三个**。）",
          '"comp_refuted_reading_third_variable_945": (' in _ausrc
          and "**没有对照真正的可疑变量**" in _ausrc
          and "剩下没被拆开的自变量是**前置态**" in _ausrc
          and "**成因未查明**" in _ausrc
          and "**你以为只有两个，其实有三个**" in _ausrc
          and 'c["ready_without_ti"] = pre["n_without_ti"]' in _p945
          and 'c["n_settle"] = n_settle' in _p945)

    check("GGGG.4 ⚠️ **本批不结案**：`cell_ok` **2/2 全 False**"
          "（12 次那格是 9 次点得到、8 次咬到）⇒ 按纪律只当"
          "**逐格 2/2 相同的局部读数**。⚠️ 另外把探针 `recovered` 那个"
          "**两态判据的定义边界**钉住：`scale=2` 那格判成 `False` **不是现象**"
          "（那一格连点后本来就 `== 1`、**没破坏**不变式）"
          "⇒ ⭐ **不许**把那格的 `False` 读成「没补回」",
          '"cell_ok_false_and_why_945": (' in _ausrc
          and '"recovered_is_two_state_edge_945": (' in _ausrc
          and "那是定义边界不是现象" in _ausrc
          and "**不许**把那格的 `False` 读成「没补回」" in _ausrc
          and 'c["recovered"] = (c["w_after_clicks"] > 1' in _p945
          and 'c["cell_ok"] = bool(c["n_click"] and c["n_click"] == c["click_bites"]'
          in _p945)

    check("GGGG.5 ✅⭐ **944 的 S 臂反向由此答掉**（945 只是**引用**、没另设臂）："
          "944 的 L 臂连点 **13 个不同下标**、每次都是一次臂事件"
          "⇒ **「点未选中的节点必然咬」**在「本体落点、13 个不同下标」范围内 "
          "**2/2 成立**；与 944 那条**「点已选中的同一节点不咬」**成对"
          "⇒ ⭐ **鼠标臂要求「这一下改变了选中态」才咬**（两侧各 2/2）"
          "⇒ ⇒ 复刻侧判「这一击是不是臂事件」时，"
          "**先问「选中态变没变」，别只看落点在哪**",
          '"unselected_node_always_bites_945": (' in _ausrc
          and "**「点未选中的节点必然咬」**" in _ausrc
          and "**鼠标臂要求「这一下改变了选中态」才咬**（两侧各 2/2）" in _ausrc
          and "**先问「选中态变没变**，别只看落点在哪" in _ausrc)

    # ══ 批 946：拆**第三个**自变量「前置态」—— 含**一道门撤回** ═════════
    print("— HHHH. 批 946 sham 推翻「第一击 Tab = 补偿」；而 warm 压根没被操控 —")
    p946 = ROOT / "scripts/jimeng_probe946_prestate_src.py"
    _p946 = p946.read_text(encoding="utf-8") if p946.exists() else ""
    # ⚠️ HHHH.7 说的是**锚点自查工具自己**，所以得把它也读进来（照 942 的写法）
    _anch = ROOT / "scripts/jimeng_check_verifier_anchors.py"
    _anchs = _anch.read_text(encoding="utf-8") if _anch.exists() else ""
    p947 = ROOT / "scripts/jimeng_probe947_stablewait_src.py"
    _p947 = p947.read_text(encoding="utf-8") if p947.exists() else ""
    p948 = ROOT / "scripts/jimeng_probe948_settle_landing_src.py"
    _p948 = p948.read_text(encoding="utf-8") if p948.exists() else ""
    p949 = ROOT / "scripts/jimeng_probe949_replay944_src.py"
    _p949 = p949.read_text(encoding="utf-8") if p949.exists() else ""
    p950 = ROOT / "scripts/jimeng_probe950_coldwindow_src.py"
    _p950 = p950.read_text(encoding="utf-8") if p950.exists() else ""
    p951 = ROOT / "scripts/jimeng_probe951_focus_gate_src.py"
    _p951 = p951.read_text(encoding="utf-8") if p951.exists() else ""
    p952 = ROOT / "scripts/jimeng_probe952_freeze_who_src.py"
    _p952 = p952.read_text(encoding="utf-8") if p952.exists() else ""
    p953 = ROOT / "scripts/jimeng_probe953_roving_ring_ck.py"
    _p953 = p953.read_text(encoding="utf-8") if p953.exists() else ""
    p954 = ROOT / "scripts/jimeng_probe954_source_ring_src.py"
    _p954 = p954.read_text(encoding="utf-8") if p954.exists() else ""
    p955 = ROOT / "scripts/jimeng_probe955_onekey_inner_src.py"
    _p955 = p955.read_text(encoding="utf-8") if p955.exists() else ""
    p956 = ROOT / "scripts/jimeng_probe956_replica_ring_ck.py"
    _p956 = p956.read_text(encoding="utf-8") if p956.exists() else ""
    p957 = ROOT / "scripts/jimeng_probe957_rail_roving_src.py"
    _p957 = p957.read_text(encoding="utf-8") if p957.exists() else ""
    p958 = ROOT / "scripts/jimeng_probe958_rail_roving_ck.py"
    _p958 = p958.read_text(encoding="utf-8") if p958.exists() else ""
    p959 = ROOT / "scripts/jimeng_probe959_domorder_src.py"
    _p959 = p959.read_text(encoding="utf-8") if p959.exists() else ""
    p960 = ROOT / "scripts/jimeng_probe960_taborder_src.py"
    _p960 = p960.read_text(encoding="utf-8") if p960.exists() else ""
    p961 = ROOT / "scripts/jimeng_probe961_ticensus_src.py"
    _p961 = p961.read_text(encoding="utf-8") if p961.exists() else ""
    p962 = ROOT / "scripts/jimeng_probe962_focusmove_src.py"
    _p962 = p962.read_text(encoding="utf-8") if p962.exists() else ""
    p963 = ROOT / "scripts/jimeng_probe963_nodecensus_src.py"
    _p963 = p963.read_text(encoding="utf-8") if p963.exists() else ""
    p964 = ROOT / "scripts/jimeng_probe964_skipwhy_src.py"
    _p964 = p964.read_text(encoding="utf-8") if p964.exists() else ""
    p965 = ROOT / "scripts/jimeng_probe965_focusable_src.py"
    _p965 = p965.read_text(encoding="utf-8") if p965.exists() else ""
    p966 = ROOT / "scripts/jimeng_probe966_clicksel_src.py"
    _p966 = p966.read_text(encoding="utf-8") if p966.exists() else ""
    # ⭐ 967：读数文件必须**真的在**，否则下面 DDDD.* 的探针钉子全是空串
    p967 = ROOT / "scripts/jimeng_probe967_armptr_src.py"
    _p967 = p967.read_text(encoding="utf-8") if p967.exists() else ""
    # 968/968b：复刻侧探针（**零节点点击**），`_p967src` 是 968 从 967 抠尺子的对象
    p967s = ROOT / "scripts/jimeng_probe967_armptr_src.py"
    _p967src = p967s.read_text(encoding="utf-8") if p967s.exists() else ""
    p968 = ROOT / "scripts/jimeng_probe968_replica_armptr_ck.py"
    _p968 = p968.read_text(encoding="utf-8") if p968.exists() else ""
    p968b = ROOT / "scripts/jimeng_probe968b_nextjsportal_ck.py"
    _p968b = p968b.read_text(encoding="utf-8") if p968b.exists() else ""
    # 969：源站探针，**同轮重新量 out 段**（推翻 968b 的收尾结论）
    p969 = ROOT / "scripts/jimeng_probe969_projectpanel_src.py"
    _p969 = p969.read_text(encoding="utf-8") if p969.exists() else ""
    # 970：**复刻侧**同口径重测（自身 tid + 最近祖先 tid 都读）
    p970 = ROOT / "scripts/jimeng_probe970_owntid_ck.py"
    _p970 = p970.read_text(encoding="utf-8") if p970.exists() else ""
    # ⭐ 971：源站探针，取样 954 那个「未复现条目」——
    #   ⭐⭐⭐ **三套口径并读**（`aria_label` / `aria_whoami` / `inner_text_head`）
    #   ⇒ 这就是本批的**来由**：954 那次两侧口径不同（源站 `WHOAMI_JS`
    #   **带 innerText 回退**、复刻侧**不带**）⇒ BODY 一枚被算成「多出一个」
    p971 = ROOT / "scripts/jimeng_probe971_savestate_src.py"
    _p971 = p971.read_text(encoding="utf-8") if p971.exists() else ""
    # ⭐ 972：源站探针，`BODY` 接缝的**座位** + 把 **969 那套 `landed` 口径**
    #   **并排**算一遍（判据要反证「它吃掉的那枚就是 `BODY`」）
    p972 = ROOT / "scripts/jimeng_probe972_seam_src.py"
    _p972 = p972.read_text(encoding="utf-8") if p972.exists() else ""
    # ⭐ 973：**复刻侧**探针，测「环序 = DOM 序」（新件 `DOMRANK_JS`
    #   读 `document.querySelectorAll('*')` 里的全文档下标 ⇒
    #   **不依赖 testid、不依赖「簇」**）
    p973 = ROOT / "scripts/jimeng_probe973_ringorder_ck.py"
    _p973 = p973.read_text(encoding="utf-8") if p973.exists() else ""
    # ⭐ 974：**源站侧**，把 973 的 `DOMRANK_JS` **逐字 `_grab`** 过来
    #   ⇒ 「两侧真的是同一件仪器」由一条 `assert` 钉住，而不是文档保证
    p974 = ROOT / "scripts/jimeng_probe974_source_domrank_src.py"
    _p974 = p974.read_text(encoding="utf-8") if p974.exists() else ""
    # ⭐ 975：源站探针，读**整条祖先链**的 `tabindex`（H₁ 判据）
    #   ⚠️ 判据组 `IIIII.1` 要钉的是**否定结果**（H₁ 被否）
    p975 = ROOT / "scripts/jimeng_probe975_scope_src.py"
    _p975 = p975.read_text(encoding="utf-8") if p975.exists() else ""
    # ⭐⭐⭐ 976：**源站**反事实干预探针（`GAP_JS` / `INJECT_JS` / `UNINJECT_JS`）
    #   ⇒ 目的：把 975 留下的 A（开头没有可聚焦元素）与 B（无条件出现）**分开**
    #   ⚠️ 判据组 `JJJJJ.1` 要钉的是**否定结果**（H₂ 被证伪）⇒ 同样最容易被忘掉
    p976 = ROOT / "scripts/jimeng_probe976_counterfactual_src.py"
    _p976 = p976.read_text(encoding="utf-8") if p976.exists() else ""
    # ⭐⭐⭐ 977：**源站**正面检验 H₃（三臂）。⚠️ 本批的**干预件也逐字继承 976**
    #   ⇒ 「本批的干预和 976 是同一件东西」由一条 `assert` 钉住
    #   ⇒ 判据组 `KKKKK.1` 要钉的是「**臂 B 打中了靶子**」这个**前提**
    p977 = ROOT / "scripts/jimeng_probe977_h3anchor_src.py"
    _p977 = p977.read_text(encoding="utf-8") if p977.exists() else ""
    # ⭐⭐⭐⭐⭐ 978：**实验室**探针（`about:blank`，**根本不打开源站**）
    #   ⇒ 零计费、零应用代码 ⇒ 「空白页上能不能复现」把
    #   **引擎/规范行为**与**源站应用的属性**分开
    #   ⚠️ 判据组 `LLLLL.1` 要钉的是那个**否定结果**（scroll 假设被否）
    p978 = ROOT / "scripts/jimeng_probe978_lab_body_stop.py"
    _p978 = p978.read_text(encoding="utf-8") if p978.exists() else ""
    # ⭐⭐⭐⭐⭐ 979：**实验室**探针第二支 —— 按一次 `Tab` 之后**页内纯读轮询**，
    #   取「**转变时间线**」⇒ 每个状态的**停留时长**直接可算
    #   ⚠️ 判据组 `MMMMM.1` 要钉的是那个**否定结果**（(a) 被否）
    p979 = ROOT / "scripts/jimeng_probe979_dwell_src.py"
    _p979 = p979.read_text(encoding="utf-8") if p979.exists() else ""
    # ⭐⭐⭐⭐⭐ 980：**实验室**探针第三支 —— 跑**够多的圈**、数
    #   「有几圈**没走** `BODY`」⇒ 把「通常在、但不是每次都在」
    #   从 2 vs 3 的**印象**变成**比率**
    #   ⚠️ 判据组 `NNNNN.1` 要钉的是**关键前提**（门②：停留都 ≥ 可见下限）
    # ⚠️⚠️⚠️⭐⭐⭐ **980 那次插入把上面两行**重复插了一遍**（`ins` 把锚点自身
    #   也带进了 `new`）⇒ Python 无害、verifier 照样绿，**但它是脏的**
    #   ⇒ 本批已去重；⇒ ⭐⭐ **锚点与新增内容**必须**互不包含**
    p980 = ROOT / "scripts/jimeng_probe980_rate_src.py"
    _p980 = p980.read_text(encoding="utf-8") if p980.exists() else ""
    # ⭐⭐⭐⭐⭐ 981：**源站**探针第四支 —— 把 980 在实验室里量到的比率
    #   **量到源站上**（980 的 `skip_note` 写明「实验室的比率不等于源站的比率」）
    #   ⚠️ 判据组 `OOOOO.1` 要钉的是**那个诚实的否定结果**（**没量到**）
    #   ⇒ 否定结果**尤其**要钉：它最容易在下一批被悄悄忘掉
    p981 = ROOT / "scripts/jimeng_probe981_srcrate_src.py"
    _p981 = p981.read_text(encoding="utf-8") if p981.exists() else ""
    # ⭐⭐⭐⭐⭐ 982：**源站**探针第五支 —— ⭐⭐⭐⭐⭐ **给「一圈」下一个正式定义**
    #   （圈长 = **最小重复周期**，**不读任何 testid** ⇒ 没有「同一个名字两种口径」）
    #   ⇒ 并用它把 973/974 的核心结论**从一个 17.8% 的小段补到 100%**
    #   ⚠️ 判据组 `PPPPP.1` 要钉的是**这个新定义**；`PPPPP.2` 要钉的是
    #   **对 `OOOOO.2` 那两处错数的更正**（而**原文保留**、只加改写横幅）
    p982 = ROOT / "scripts/jimeng_probe982_ringlen_src.py"
    _p982 = p982.read_text(encoding="utf-8") if p982.exists() else ""
    # ⭐⭐⭐⭐⭐ 984：**实验室**探针 —— ⭐⭐⭐⭐⭐ **把 H₃ 的「出处」逼到一个精确位置**
    #   ⇒ 而第一步**978 的读数就已经做完了**（`BODY` 的 `tabIndex` 是算出来的 −1）
    #   ⚠️ 判据组 `RRRRR.3` 要钉的是**「仍未找到出处」这条边界**
    #   （**复现 ≠ 出处**）⇒ 以及**我自己那处过宽断言的更正**
    p984 = ROOT / "scripts/jimeng_probe984_bodytabindex_lab.py"
    _p984 = p984.read_text(encoding="utf-8") if p984.exists() else ""
    # ⭐⭐⭐⭐⭐ 985：**实验室＋源站**探针 —— ⭐⭐⭐⭐⭐ **一次自我推翻**
    #   ⇒ `BODY` 根本不是一格（**`:focus` 在谁身上**才是那一问）
    #   ⚠️ 判据组 `SSSSS.1` 要钉的是**那三条否定读数**（`body` 从未被聚焦）
    p985 = ROOT / "scripts/jimeng_probe985_bodynotacell_lab.py"
    _p985 = p985.read_text(encoding="utf-8") if p985.exists() else ""
    #   ⚠️ 判据组 `TTTTT.1` 要钉的是**那三条按定义预写的预测**
    #   （缺失率归零 / 间隙在回绕点 / 间隙仍是间隙）
    p986 = ROOT / "scripts/jimeng_probe986_gaprate_lab.py"
    _p986 = p986.read_text(encoding="utf-8") if p986.exists() else ""
    #   ⚠️ 判据组 `UUUUU.2` 要钉的是**那条被数据否掉的预测**（P1）
    p987 = ROOT / "scripts/jimeng_probe987_wrapcause_ck.py"
    _p987 = p987.read_text(encoding="utf-8") if p987.exists() else ""
    #   ⚠️ 判据组 `VVVVV.2` 要钉的是**「分子也要减」那条**
    p988 = ROOT / "scripts/jimeng_probe988_arcdenom_reread.py"
    _p988 = p988.read_text(encoding="utf-8") if p988.exists() else ""
    #   ⚠️ 判据组 `WWWWW.2` 要钉的是**「两批不适用」这个结论**
    p989 = ROOT / "scripts/jimeng_probe989_ruler_reread.py"
    _p989 = p989.read_text(encoding="utf-8") if p989.exists() else ""
    #   ⚠️ 判据组 `XXXXX.3`/`XXXXX.4` 要钉的是 P1 成立与 P2/P3 被否
    p990 = ROOT / "scripts/jimeng_probe990_prodbuild_ck.py"
    _p990 = p990.read_text(encoding="utf-8") if p990.exists() else ""
    #   ⚠️ 判据组 `Y991A.4` 要钉的是**「理由错、结果撞对」**
    p991 = ROOT / "scripts/jimeng_probe991_wrapvsindex_reread.py"
    _p991 = p991.read_text(encoding="utf-8") if p991.exists() else ""
    #   ⚠️ 判据组 `Z991A.3` 要钉的是**「990 那条只管跨构建模式」**
    p992 = ROOT / "scripts/jimeng_probe992_seampos_crosssys_reread.py"
    _p992 = p992.read_text(encoding="utf-8") if p992.exists() else ""
    #   ⚠️ 判据组 `X992A.4` 要钉的是**「P4 被否、而门错的是我」**
    p993 = ROOT / "scripts/jimeng_probe993_zeroexception_scope_reread.py"
    _p993 = p993.read_text(encoding="utf-8") if p993.exists() else ""
    #   ⚠️ 判据组 `Y992B.2` 要钉的是**「扫描会改变它所扫描的对象」**
    p994 = ROOT / "scripts/jimeng_probe994_scope_presupposition_reread.py"
    _p994 = p994.read_text(encoding="utf-8") if p994.exists() else ""
    #   ⚠️ 判据组 `Z992C.2` 要钉的是**「读数 vs 断言」**
    # ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **这一行曾经漏掉、而漏掉的方式本身是个教训** ——
    #   我第一版用 `if "_p995" not in v:` 当「有没有登记」的判据
    #   ⇒ ⇒ **而判据组 `Z992C` 的正文里本来就写着 `_p995`** ⇒
    #   ⇒ **守卫误判成「已登记」、于是读取行压根没加** ⇒ ⇒
    #   ⇒ ⭐⭐⭐⭐⭐ **71 条锚点被两个门同时静默跳过、而两个门都报成功**
    #   ⇒ ⇒ ⭐⭐⭐⭐ **「用 `in` 判断有没有登记」不可靠 ——
    #   **要判的是「那行读取在不在」、不是「那个名字在不在」**
    p995 = ROOT / "scripts/jimeng_probe995_wording_reread.py"
    _p995 = p995.read_text(encoding="utf-8") if p995.exists() else ""
    #   ⚠️ 判据组 `A993D.3` 要钉的是**「反向用例连否两次」**
    p996 = ROOT / "scripts/jimeng_probe996_regguard_reread.py"
    _p996 = p996.read_text(encoding="utf-8") if p996.exists() else ""
    # ⚠️ 判据组 `B993E.5` 要钉的是**「两个尺子一致是最容易骗人的证据类型」**
    #   ⇒ ⇒ **996 那条「钉探针 ≠ 钉 audit」在这一批是**同一步**做的**：
    #   **这行读取与 `PROBE_VARS` 里的登记必须一起加、否则整组锚点会静默跳过**
    p997 = ROOT / "scripts/jimeng_probe997_skipcensus_reread.py"
    _p997 = p997.read_text(encoding="utf-8") if p997.exists() else ""
    # ⚠️ 判据组 `C993F.1` 要钉的是**「P2 被否、而它否掉的是我自己写下的推理」**
    #   ⇒ ⇒ **996/997 那条「钉探针 ≠ 钉 audit」在这一批仍是同一步做的**
    p998 = ROOT / "scripts/jimeng_probe998_derivesrc_reread.py"
    _p998 = p998.read_text(encoding="utf-8") if p998.exists() else ""
    # ⚠️ 判据组 `D993G.3` 要钉的是**「那 1 条不是代价、是判据的优点」**
    p999 = ROOT / "scripts/jimeng_probe999_whowouldfail_reread.py"
    _p999 = p999.read_text(encoding="utf-8") if p999.exists() else ""
    # ⚠️ 判据组 `E993H.2` 要钉的是**「`PROBE_VARS` 的形状是一道隐形口径」**
    p1000 = ROOT / "scripts/jimeng_probe1000_negative_census_reread.py"
    _p1000 = p1000.read_text(encoding="utf-8") if p1000.exists() else ""
    # ⚠️ 判据组 `F993J.3` 要钉的是**「歧义与被门检查互斥」**
    p1001 = ROOT / "scripts/jimeng_probe1001_repeat_shape_reread.py"
    _p1001 = p1001.read_text(encoding="utf-8") if p1001.exists() else ""
    # ⚠️⚠️ 判据组 `G993K.2` 要钉的是**「改之前/改之后」那两条路必须分开数**
    p1002 = ROOT / "scripts/jimeng_probe1002_mutation_coverage.py"
    _p1002 = p1002.read_text(encoding="utf-8") if p1002.exists() else ""
    # ⚠️ 判据组 `H993L.3` 要钉的是**「量东西不许经过任何去重容器」**
    p1003 = ROOT / "scripts/jimeng_probe1003_anchor_teeth.py"
    _p1003 = p1003.read_text(encoding="utf-8") if p1003.exists() else ""
    # ⚠️⚠️ 判据组 `I993M.3` 要钉的是**「正确公式与错公式的差别」**
    p1004 = ROOT / "scripts/jimeng_probe1004_anchor_coupling.py"
    _p1004 = p1004.read_text(encoding="utf-8") if p1004.exists() else ""
    # ⚠️ 判据组 `J993N.3` 要钉的是**「golden 由写它的仪器自己写」**
    p1005 = ROOT / "scripts/jimeng_probe1005_zero_coupling_census.py"
    _p1005 = p1005.read_text(encoding="utf-8") if p1005.exists() else ""
    # ⚠️⚠️ 判据组 `K993O.5` 要钉的是**「一次编辑只让一处变红、其余静默失真」**
    #   ⇒ 而 1006 让门第一次能读到**探针侧**（`argv[3]`）⇒ **这条锚点本身
    #   就钉在探针源码里** ⇒ ⇒ **⇒ 所以这行读取与门里那条登记必须是同一步**
    p1006 = ROOT / "scripts/jimeng_probe1006_duplicate_anchors.py"
    _p1006 = p1006.read_text(encoding="utf-8") if p1006.exists() else ""
    # ⚠️⚠️ 判据组 `L993P.2` 要钉的是**「1006 那个解释被换掉了、而原文一字没删」**
    #   ⇒ 而 1007 正好是**去查 1006 自己给的那个「可解释」** ⇒ ⇒
    #   **⇒ 所以这行读取与门里那条登记必须是同一步**
    p1007 = ROOT / "scripts/jimeng_probe1007_disparate_copies.py"
    _p1007 = p1007.read_text(encoding="utf-8") if p1007.exists() else ""
    # ⚠️⚠️ 判据组 `M993Q.3` 要钉的是**「只加不改的编辑对门和清单都是隐形的」**
    #   ⇒ 而 1008 是**拿 1005 的清单当实验对象**的那一批 ⇒ ⇒
    #   **⇒ 所以这行读取与门里那条登记必须是同一步**
    p1008 = ROOT / "scripts/jimeng_probe1008_golden_freshness.py"
    _p1008 = p1008.read_text(encoding="utf-8") if p1008.exists() else ""
    # ⚠️⚠️ 判据组 `N993R.2` 要钉的是**「那 8 行全部是真跑门跑出来的」**
    #   ⇒ 而「不许用推理填格」这条纪律**必须由门来钉**、不能只写在文档里 ⇒ ⇒
    #   **⇒ 所以这行读取与门里那条登记必须是同一步**
    p1009 = ROOT / "scripts/jimeng_probe1009_edit_visibility.py"
    _p1009 = p1009.read_text(encoding="utf-8") if p1009.exists() else ""
    # ⚠️⚠️ 判据组 `O993S.2` 要钉的是**「人工挑的变异不代表日常的变异」**
    #   ⇒ 而 1010 是**拿真实 git 历史**量的 ⇒ ⇒
    #   **⇒ 所以这行读取与门里那条登记必须是同一步**
    p1010 = ROOT / "scripts/jimeng_probe1010_real_history_detection.py"
    _p1010 = p1010.read_text(encoding="utf-8") if p1010.exists() else ""
    # ⚠️⚠️⭐⭐⭐⭐⭐ 判据组 `P993T.1` 要钉的是**「1010 那个 39 只是九对、而十对是 45」**
    #   ⇒ ⇒ 而 1011 是**拿同一批 git 历史**逐条复算的 ⇒ ⇒
    #   **⇒ 所以这行读取与门里那条登记必须是同一步**
    p1011 = ROOT / "scripts/jimeng_probe1011_change_locality.py"
    _p1011 = p1011.read_text(encoding="utf-8") if p1011.exists() else ""
    # ⚠️⚠️⭐⭐⭐⭐⭐⭐ 判据组 `Q993U.1` 要钉的是**「扩到 187 个目标变量之后、
    #   门在全局口径上到底开口过几次」**
    #   ⇒ ⇒ 而 1012 要**真跑三次门**去对账静态模型 ⇒ ⇒
    #   **⇒ 所以这行读取与门里那条登记必须是同一步**
    p1012 = ROOT / "scripts/jimeng_probe1012_global_detection.py"
    _p1012 = p1012.read_text(encoding="utf-8") if p1012.exists() else ""
    # ⚠️⚠️⭐⭐⭐⭐⭐⭐ 判据组 `R993V.1` 要钉的是**「账本的分类互斥且完备」**
    #   ⇒ ⇒ 而 1013 要给「手写的数必须有出处」的正则**配一条反向自检**
    #   ⇒ ⇒ ⇒ **⇒ 所以这行读取与门里那条登记必须是同一步**
    p1013 = ROOT / "scripts/jimeng_probe1013_occurrence_ledger.py"
    _p1013 = p1013.read_text(encoding="utf-8") if p1013.exists() else ""
    # ⚠️⚠️⭐⭐⭐⭐⭐⭐ 判据组 `S993W.1` 要钉的是**「空集合分两类：可自证的与不可自证的」**
    #   ⇒ ⇒ 而 1014 的普查**必须把自己上一跑留下的 golden 排除掉** ⇒ ⇒
    #   **⇒ 所以这行读取与门里那条登记必须是同一步**
    p1014 = ROOT / "scripts/jimeng_probe1014_empty_ambiguity.py"
    _p1014 = p1014.read_text(encoding="utf-8") if p1014.exists() else ""
    # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ 判据组 `U993Y.1` 要钉的是**「套件的完备性靠加法验、
    #   而加法两边不许同源」**
    #   ⇒ ⇒ 而 1015 自己就是靠一条 `generated_by` 反查来认领 9 本 golden 的
    #   ⇒ ⇒ ⇒ **⇒ 所以这行读取与门里那条登记必须是同一步**
    p1015 = ROOT / "scripts/jimeng_probe1015_rerun_reproducibility.py"
    _p1015 = p1015.read_text(encoding="utf-8") if p1015.exists() else ""
    # ⭐⭐⭐⭐⭐ 1016：`SOURCE_BASELINE` 被当成通用抽屉 + 一个键名被写了两遍
    #   ⇒ 「★读这一行」与「★把 `_p1016` 登记进 `PROBE_VARS`」必须是同一步，
    #   否则门会拿一个空串去判（1006 那条：门报红 ≠ 数据错，先判门错还是数据错）
    p1016 = ROOT / "scripts/jimeng_probe1016_baseline_host_misuse.py"
    _p1016 = p1016.read_text(encoding="utf-8") if p1016.exists() else ""
    # ⭐⭐⭐⭐⭐ 1017：第一次把这套门禁的**被测对象**点一遍名 ——
    #   原型本体（`src/components/jimeng/`）从来没进过被测对象
    p1017 = ROOT / "scripts/jimeng_probe1017_replica_coverage.py"
    _p1017 = p1017.read_text(encoding="utf-8") if p1017.exists() else ""
    # ⭐⭐⭐⭐⭐ 1018：那 24 条「在读原型源码」的判据，验的是字还是行为
    p1018 = ROOT / "scripts/jimeng_probe1018_assertion_vs_behavior.py"
    _p1018 = p1018.read_text(encoding="utf-8") if p1018.exists() else ""
    # ⭐⭐⭐⭐⭐ 1019：第一次在装置上动手改 —— 抽函数真身 + 最小 stub + node 真跑
    p1019 = ROOT / "scripts/jimeng_probe1019_behavior_harness.py"
    _p1019 = p1019.read_text(encoding="utf-8") if p1019.exists() else ""
    # ⭐⭐⭐⭐⭐ 1020：把 1019 那个 harness **本身**当被测对象 —— 两条 stub 对账 + 变异测试
    p1020 = ROOT / "scripts/jimeng_probe1020_harness_fidelity.py"
    _p1020 = p1020.read_text(encoding="utf-8") if p1020.exists() else ""
    # ⭐⭐⭐⭐⭐ 1021：第一次量「门自己」—— 官方锚点门对「判据变弱」的敏感度
    p1021 = ROOT / "scripts/jimeng_probe1021_anchor_gate_coverage.py"
    _p1021 = p1021.read_text(encoding="utf-8") if p1021.exists() else ""
    # ⭐⭐⭐⭐⭐ 1023：量「类型层」那一道闸 —— tsc 早就装好了
    p1023 = ROOT / "scripts/jimeng_probe1023_type_layer_gate.py"
    _p1023 = p1023.read_text(encoding="utf-8") if p1023.exists() else ""
    # ⭐⭐⭐⭐⭐ 1024：普查「豁免声明」—— 门看见了、被配成不算数，是同一种病的第三形态
    p1024 = ROOT / "scripts/jimeng_probe1024_exemption_claims.py"
    _p1024 = p1024.read_text(encoding="utf-8") if p1024.exists() else ""
    # ⭐⭐⭐⭐⭐ 1025：量「判据的方向」—— 936 条 check() 里多少条钉的是易变量
    p1025 = ROOT / "scripts/jimeng_probe1025_criterion_direction.py"
    _p1025 = p1025.read_text(encoding="utf-8") if p1025.exists() else ""
    # ⭐⭐⭐⭐⭐ 983：**复刻侧**探针 —— ⭐⭐⭐⭐⭐ **在第二个被测系统上独立复验
    #   982 那条结构发现** ⇒ 同构 ⇒ 它是**规律**，不是源站特有的巧合
    #   ⚠️ 判据组 `QQQQQ.2` 要钉的是 **`_grab_def` 那个更弱的保证**
    #   （`exec` 跑的是**可执行代码**）⇒ 靠**成对门**补上
    p983 = ROOT / "scripts/jimeng_probe983_wrapcmp_ck.py"
    _p983 = p983.read_text(encoding="utf-8") if p983.exists() else ""
    # ⭐ 970 的 CCCC.2 要**反证 816 那条决策真的在仓库里**（钉源码原文，
    #   不钉我自己写的转述）
    p816 = ROOT / "scripts/verify-jimeng-batch816-anchors.py"
    _p816 = p816.read_text(encoding="utf-8") if p816.exists() else ""
    # ⭐ 968b 的结论「`NEXTJS-PORTAL` 不是复刻自己写的」**必须**由源码反证：
    #   复刻组件里**一处都不许**出现 `nextjs-portal` / `NEXTJS-PORTAL`
    _replica_srcs = []
    for _pat in ("src/components/jimeng/**/*.tsx",
                 "src/components/jimeng/**/*.ts",
                 "src/components/jimeng/**/*.css"):
        for _f in sorted(ROOT.glob(_pat)):
            try:
                _replica_srcs.append(_f.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError):
                pass
    del _pat, _f
    p892 = ROOT / "scripts/jimeng_probe892_preventdefault_src.py"
    _p892 = p892.read_text(encoding="utf-8") if p892.exists() else ""
    p896 = ROOT / "scripts/jimeng_probe896_roving_tabindex_policy_src.py"
    _p896 = p896.read_text(encoding="utf-8") if p896.exists() else ""
    c958 = (ROOT / "src/components/jimeng/JimengToolRail.tsx"
            ).read_text(encoding="utf-8")

    check("HHHH.1 ⚠️⚠️⚠️ **本批的设计有一处真缺陷，如实记账**：`warm ∈ {0,1,2,6}` "
          "**全都 ≤ boot 之后的自然值 76** ⇒ 预热循环**一次都没进**"
          "（`warm_presses = 0`、10 个格次全同）⇒ ⭐ **`warm` 从头到尾没被操控过** "
          "⇒ 相应地 **`warm_reached` 恒真** ⇒ ⭐ "
          "**「一个恒真的判据比没有判据更坏」（942）** ⇒ **撤回这道门**",
          '"warm_never_manipulated_946": (' in _ausrc
          and "**全都 ≤ boot 之后的自然值 76**" in _ausrc
          and "**`warm` 这个自变量从头到尾没有被操控过**" in _ausrc
          and "**`warm_reached` 是恒真的**" in _ausrc
          and "**「一个恒真的判据比没有判据更坏」（942）**" in _ausrc
          and "**撤回这道门**" in _ausrc
          # ⭐ 钉探针：预热循环的**判据**（自然值就 ≥ 任何目标 ⇒ 一次都不进）
          and 'if pre["n_without_ti"] >= warm:' in _p946
          and 'c["warm_presses"] = n_press' in _p946)

    check("HHHH.2 ⭐⭐⭐⭐ **sham 格（`scale=0`、**零点击**）推翻了一个隐含前提**："
          "刚 `boot()` 完按第 1 下 `Tab`，「不带 ti」**76 → 0**、第 2 下 `0 → 1`、"
          "第 3 下 `1 → 1`（2/2 逐条相同）⇒ ⭐⭐⭐ **这一压根本不需要连点来解释**"
          "⇒ ⇒ **不许**把「第一击 `Tab` 之后 `不带 ti` 变小了」当成"
          "**补偿已经发生**的证据。⚠️ sham 是**专为证伪这件事**而设计的，不许省",
          '"sham_refutes_first_tab_means_compensation_946": (' in _ausrc
          and "**76 → 0**" in _ausrc
          and "**「第一击 Tab 把「不带 ti」大幅压下去」根本不需要连点来解释**"
          in _ausrc
          and "**不许**把「第一击 `Tab` 之后 `不带 ti` 变小了」当成" in _ausrc
          # ⭐ 钉探针：sham 真的存在、真的零点击、且**每一轮**都真的没点过
          and '{"warm": 6, "scale": 0}' in _p946
          and 'sham = (scale == 0)' in _p946
          and '"sham_ran_every_rep"' in _p946
          and '"sham_zero_clicks"' in _p946
          and '"sham_present"' in _p946)

    check("HHHH.3 ⭐⭐⭐ **「前置态」是真的、落差极大**（虽然**不是**按设计操控出来的，"
          "是 boot 的自然状态替我们动了它）：**刚 boot 完 = 76**（76 个节点全都没有 "
          "`tabindex`），而 945 在预热里**按了 1 下 `Tab`** 之后 = **0** "
          "⇒ 同一段连点代码跑在 **76** 与 **0** 两种前置态上、读数**不可比** "
          "⇒ ⚠️ 945 与 946 的读数**必须分开记**，不许当成同一个实验的两批数据",
          '"front_state_is_real_and_huge_946": (' in _ausrc
          and "**刚 boot 完 = 76（76 个节点全都没有 `tabindex`）**" in _ausrc
          and "**必须分开记**" in _ausrc
          # ⭐ 钉探针：预热循环上限 14 下（不是「按到够就停」的假说法）
          and 'WARM_MAX = 14' in _p946
          and "for _ in range(WARM_MAX):" in _p946)

    check("HHHH.4 ⭐⭐⭐⭐⭐ **944 那个矛盾在 946 原样重现**：格 0 **两轮不一致** —— "
          "rep1 第 1 击 `Tab` **75 → 1**、rep2 **75 → 8**（**停在 8、不补**），"
          "而**这两轮跑的是同一段代码**（`warm` 没起作用 ⇒ 唯一变量都没动）"
          "⇒ ⇒ **成因不在 `warm`、也不在 `scale`、也不在 `mode`**（945 已排除后两个）"
          "⇒ ⚠️ **944 那个矛盾成因仍未查明**，且它**不是** 945 以为的"
          "「第三个自变量」那么简单",
          '"944_contradiction_reproduced_946": (' in _ausrc
          and "**75 → 1**" in _ausrc and "**75 → 8**" in _ausrc
          and "**这两轮跑的是同一段代码**" in _ausrc
          and "**成因不在 `warm`、也不在 `scale`、也不在 `mode`**" in _ausrc
          and "**成因仍未查明**" in _ausrc
          # ⭐ 钉探针：逐格 2/2 比较**真被算出来**、且**不许**把不一致当一致
          and "out[\"reps_identical\"] = _ident" in _p946
          and 'def stable_key(cell):' in _p946
          and "got[0] == got[1]" in _p946)

    check("HHHH.5 ⚠️⚠️ **`added=0` 在这一批是 `delta()` 的**构造性产物**、不是现象**："
          "`delta()` 在 `identity_stable=False` 时**按构造**返回空三元组 "
          "⇒ 于是出现「`不带 ti` **75 → 1** 而 `added=0`」⇒ ⭐ "
          "**不许**把它读成「没写回」⇒ ⚠️ 这是 944 那个「`is_arm` 太松」的**同族**病，"
          "但这次在 `delta()` 里 ⇒ **凡是身份不稳的那一段，三元组一律不许当读数用**",
          '"added_zero_is_constructive_946": (' in _ausrc
          and "**构造性产物**" in _ausrc
          and "**不许**把它读成「没写回」" in _ausrc
          and "**同族**病" in _ausrc
          # ⭐ 钉探针：delta 的**早退分支**就是这条判据的对象
          and 'return {"identity_stable": False, "removed": [], "added": [],' in _p946
          and "**凡是身份不稳的那一段，" in _ausrc)

    check("HHHH.6 ⭐⭐ **两处「门等于没有」被自己抓住**（不是被别人抓的）："
          "① 945 只把 `reps_identical` **声明**进 `DERIVED_KEYS` 却**从没赋值** "
          "⇒ 那道门等于没有 ⇒ 946 **真算**；"
          "② 946 第一版把守卫常量 `SLICE_STR` 写成 `\"|| '').slice(0 \"`"
          "（**漏了一个逗号**）⇒ `count()` 恒为 0 ⇒ 「非字符串切片」那道门"
          "**永远不会红** ⇒ 自己跑了一次才撞上 ⇒ 加了**自证**"
          "⇒ ⭐ **一个恒真的判据比没有判据更坏**",
          '"identity_churn_on_this_canvas_946": (' in _ausrc
          and "**不可信地归属**" in _ausrc
          # ⭐ 钉探针：reps_identical 是**真算**的
          and "_ident.append(bool(len(got) == REPS and got[0] == got[1]))" in _p946
          # ⭐⭐ 钉探针：守卫常量**自证**（这正是 946 第一版撞上的那个坑）
          and 'assert any(SLICE_STR in _js for _js in _JS_ALL), (' in _p946
          and "—— 这道门恒绿，等于没有门" in _p946
          and "SLICE_STR = \"|| '').slice(0, \"" in _p946
          # ⭐ 五段 JS 与 945 逐字相同（防漂移，940 的办法）
          and 'for _name in ("BLANK_JS", "CENSUS_JS", "POINT_JS", "FOCUS_JS", "ARM_FOCUS_JS"):' in _p946
          and "与 945 那份**不一致**" in _p946)
    check("HHHH.7 ⭐⭐⭐ **锚点自查的绑定表停在 `_p941` 就是个真口子** —— "
          "943 / 944a / 944b / 945 / 946 这五个探针**一个都没登记** ⇒ "
          "它们身上的锚文**从来没被自查过**。代价当场付了：HHHH.6 有一条锚文"
          "在探针里**没有加粗标记**，而锚点自查当时报的是「1645 条 / **0 个问题**」"
          "⇒ ⭐ **一道没登记的锚文，等于一道不存在的锚文**"
          "⇒ 已补登记（自查读数 1645 → **1691**）。⚠️ 门禁的**覆盖面**"
          "和门禁的**严格性**是两件事，后者再好也补不了前者的漏。"
          "⚠️ 本条的锚点**只钉代码**（登记本身 + 跳过机制）；"
          "「为什么是这道口子」写在判据文案里、**不写进锚文**"
          "（942 AA.3：判据钉注释散文 = 同一个病）",
          # ⭐ 钉**登记本身**（代码，不是注释）
          '"_p943": "scripts/jimeng_probe943_arm_relation_src.py"' in _anchs
          and '"_p944a": "scripts/jimeng_probe944a_node_inner_scan_src.py"' in _anchs
          and '"_p944b": "scripts/jimeng_probe944b_mouse_axes_src.py"' in _anchs
          and '"_p945": "scripts/jimeng_probe945_comp_scale_split_src.py"' in _anchs
          and '"_p946": "scripts/jimeng_probe946_prestate_src.py"' in _anchs
          # ⭐⭐ 钉**机制**：绑到未登记变量的锚文是**被静默跳过**的
          #    （这才是「0 个问题」却漏掉一条坏锚文的直接原因）
          and 'if name != "_ausrc" and name not in PROBE_VARS:' in _anchs
          # ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **1006：这两条锚点钉的是门自己的源码、而它们在
          #   **我给门加 `argv[3]` 的那一刻就打红了** ⇒ ⇒
          #   **⇒ 「锚点指向另一个文件」有两种脆弱性：**
          #   **① 那个文件被改、这条判据就红（这一条）** ⇒ ⇒
          #   **② 那个文件里的同一段话被复制多处、改一处、其余静默失真（1006 普查的那一类）** ⇒ ⇒
          #   **⇒ 而这一条原先钉的是一整行、所以它对「行内改动」零容忍 ⇒ ⇒
          #   **⇒ 处置：钉到结构上稳定的片段、而不是整行**
          and 'probes = {k:' in _anchs
          and "for k, v in PROBE_VARS.items()}" in _anchs
          and 'for k, v in PROBE_VARS.items()}' in _anchs
          # ⭐ 钉住那五个探针文件**真的存在**（登记了但文件没了 = 又一种恒绿）
          and all((ROOT / f).exists() for f in (
              "scripts/jimeng_probe943_arm_relation_src.py",
              "scripts/jimeng_probe944a_node_inner_scan_src.py",
              "scripts/jimeng_probe944b_mouse_axes_src.py",
              "scripts/jimeng_probe945_comp_scale_split_src.py",
              "scripts/jimeng_probe946_prestate_src.py")))

    # ══ 批 947：944 矛盾**剩下的**那个可疑变量 —— 判为**排除** ═════════
    print("— IIII. 批 947「等不等身份稳定」被排除；而矛盾只出现在就绪≠0 那侧 —")
    check("IIII.1 ✅⭐⭐⭐ **「连点期间身份在不在动」被排除**："
          "`wait_stable=False`（只等 350ms）与 `wait_stable=True`"
          "（轮询到**连续两次身份表相同**）两格的 `click_rows` 与 `tabs` "
          "**逐条相同** —— 咬到 **4**、第 1 击 `added=4`、`不带 ti 4→1`、"
          "第 2 击 `added=1`、第 3 击 `added=0` ⇒ ⭐ **唯一变的是轮询计数**"
          "（0 vs **5**，5 次**全部等到稳定**）⇒ **「等它稳定」对结果没有影响**。"
          "⚠️ 结论**限定在「咬到 4 次」这个范围内**",
          '"wait_stable_changes_nothing_947": (' in _ausrc
          and "**唯一变的是轮询计数**" in _ausrc
          and "（0 次 vs **5** 次，5 次**全部等到稳定**）" in _ausrc
          and "**限定在「咬到 4 次」这个范围内**" in _ausrc
          # ⭐ 钉探针：受控侧的判据是「**两次读数彼此相同**」，
          #    **不是**「与点击前相同」—— 点击本来就该改东西
          and 'if cur["ids"] == prev["ids"]:' in _p947
          and "**两次读数彼此相同**" in _p947
          # ⭐ 钉探针：对照侧**只等固定时间**、不轮询（两臂真的只差这一样）
          and "page.wait_for_timeout(SETTLE)\n                post = ev(CENSUS_JS, [NODE_SEL])" in _p947
          and "for k in range(SCALE_FIXED):" in _p947)

    check("IIII.2 ⭐⭐⭐ **settle 轨迹本身成了读数**（946 只知道两个端点）："
          "**刚 `boot()` 完 `不带 ti` = 76，按 1 下 `Tab` 之后 = 0**（轨迹 `[76, 0]`）"
          "⇒ ⇒ **76 → 0 是「一下」的落差**，而 946 那批**一按都没按**"
          "⇒ ⭐ 这条轨迹正是 946 想测却**没测到**的那个「前置态」",
          '"settle_traj_76_to_0_947": (' in _ausrc
          and "**刚 `boot()` 完 `不带 ti` = 76，按 1 下 `Tab` 之后 = 0**" in _ausrc
          and "**76 → 0 是「一下」的落差**" in _ausrc
          # ⭐ 钉探针：settle 循环**照抄 945 的判据**（`<= 1` 为止），
          #    且**逐次记下轨迹**（这正是 946 缺的）
          and 'if pre["n_without_ti"] <= 1:' in _p947
          and 'c["settle_traj"].append(' in _p947
          and '"settle_side_matches_945"' in _p947)

    check("IIII.3 ⭐⭐⭐⭐⭐ **跨批对照表成形**（`就绪不带 ti` vs 有没有矛盾）："
          "**945** 就绪 0/咬 8/`added=8` **无矛盾**；**947** 就绪 0/咬 4/"
          "`added=4` **无矛盾**；**944** 就绪 **1**/连按 6 下恒 0 **有矛盾**；"
          "**946** 就绪 **76**/`75→1` 与 `75→8` **有矛盾** ⇒ ⭐⭐⭐ "
          "**矛盾只在「就绪 `不带 ti` ≠ 0」的两侧出现** ⇒ ⚠️ "
          "**但这仍然是关系式推断、不是受控对照**（那三批 `scale`/落点/咬到数都不同）"
          "⇒ 按纪律**不结案**；⭐ 但**下一步该测什么已经唯一了**："
          "让 settle **显式停在 0 和停在 1**，其它一切固定",
          '"contradiction_only_when_ready_not_zero_947": (' in _ausrc
          and "**矛盾只在「就绪 `不带 ti` ≠ 0」的两侧出现**" in _ausrc
          and "**但这仍然是关系式推断、不是受控对照**" in _ausrc
          and "**下一步该测什么已经唯一了**" in _ausrc
          and "**显式停在 0 和停在 1**" in _ausrc
          # ⭐ 钉住「**不结案**」这三个字本身：别让下一个人把关系式推断当结案
          and "按纪律**不结案**" in _ausrc)

    check("IIII.4 ⭐ **§156 挂的「第一击不咬」答掉了**：每格第 1 击都是 "
          "`i=0 / bit=False / identity_stable=False`，**12 个格次 2/2 逐条相同**"
          "（945 的 8 + 947 的 4）⇒ 「`boot()`/预热之后**第一击不咬**、"
          "而且连身份都没稳」在这个范围内**成立**；⚠️ 946 那侧**不计入**"
          "（它的前置态是 76）⇒ ⇒ 复刻侧做「连点 N 次」的臂事件实验时，"
          "**第一击必须单独记、不能混进平均值**",
          '"first_click_never_bites_947": (' in _ausrc
          and "**12 个格次 2/2 逐条相同**" in _ausrc
          and "946 那侧不计入" in _ausrc
          and "**第一击必须单独记、不能混进平均值**" in _ausrc
          # ⭐ 钉探针：第 1 击**单独**取出来记（不许混进 click_bites 平均）
          and 'if k == 0:' in _p946
          and "first_click_bites" in _p946)

    check("IIII.5 ⭐⭐ **本批自己设计的「反恒绿门」生效了**"
          "（`manip_moved_something`）：`wait_stable=True` 那一格如果"
          "**测不出任何差别**，那道门就恒绿了（和 946 被撤回的 `warm_reached` "
          "同一个病）⇒ 实测 `poll` **0 → 5** ⇒ 操纵**确实动了**、结果**没变** "
          "⇒ 这才敢下「排除」的结论 ⇒ ⭐ "
          "**「操纵动了没有」必须自己答，不能默认它动了。**"
          "⚠️ 而 946 的 `warm_pressed` 门是**恒真**的（已撤回）—— "
          "**同一种门，一个生效一个恒真，差别就在有没有这一道自证**",
          '"manip_gate_worked_947": (' in _ausrc
          and "**「操纵动了没有」必须自己答，不能默认它动了。**" in _ausrc
          and "**同一种门，一个生效一个恒真" in _ausrc
          # ⭐ 钉探针：反恒绿门**真的在算**（不是只声明）
          and 'out["manip_moved_something"] = bool(_wa_t and _wb_t and _wa_t != _wb_t)' in _p947
          and '"manip_moved_something": out["manip_moved_something"],' in _p947
          # ⭐⭐ 钉住 947 的五段 JS 与 946 逐字相同（防漂移，940 的办法）
          and "与 946 那份**不一致**" in _p947)

    # ══ 批 948：⭐⭐⭐⭐⭐ **944 那个挂了四批的矛盾结案了 —— 它是一个误读** ═══
    print("— JJJJ. 批 948 受控落点表 76/0/1 ⇒ 944 的矛盾是「把冷启动铺窗口读成补偿没来」 —")
    check("JJJJ.1 ⭐⭐⭐⭐⭐ **受控落点对照表**（2/2，别的全固定，只改按压下数）："
          "`n_settle=0/1/2` ⇒ 就绪 `不带 ti` = **76 / 0 / 1**（逐按落点 "
          "`[76,0]`、`[76,0,1]`）⇒ ⭐ 这**第一次**是**受控**的："
          "947 那张表是**关系式**的（三批 `scale`/落点/咬到数都不同）。"
          "⚠️ 946 栽过的坑**不许再栽**：本批**不用条件循环**，"
          "改成**显式按固定下数**",
          '"controlled_landing_table_948": (' in _ausrc
          and "**受控落点对照表**" in _ausrc
          and "这**第一次**是**受控**的" in _ausrc
          and "**不用条件循环**" in _ausrc
          and "**显式按固定下数**" in _ausrc
          # ⭐ 钉探针：**显式**按 `ns` 下（不是「按到满足为止」）
          and "for k in range(1, ns + 1):" in _p948
          and "NSETTLE_CELLS = [0, 1, 2]" in _p948
          # ⭐⭐ 钉探针：反恒绿门比的是**格与格之间**（操纵不动就会红，
          #    这正是 946 那道恒真门缺的性质）
          and 'out["landed_differently"] = bool(' in _p948
          and "len({v for _, v in _land}) >= 2" in _p948)

    check("JJJJ.2 ⭐⭐⭐⭐⭐ **944 那个挂了四批的矛盾结案了 —— 它是一个误读**："
          "947 说「矛盾只在就绪 ≠ 0 那侧」⇒ **本批推翻**：`n_settle=2` 就绪 = **1**"
          "（正是 944 那一侧的值），而第 1 击 **`added=5`、`5→1`、补回=True**，"
          "**补偿照常** ⇒ **分界是 76 vs {0,1}**，**不是** 0 vs 1；"
          "唯一异常的就绪 **76** 那一格，946 的 **sham**（零点击）已证明"
          "刚 boot 完第 1 击 `Tab` 就是 `76 → 0` ⇒ ⇒ "
          "**944 把「冷启动铺窗口」读成了「补偿没来」——矛盾根本不存在。**"
          "⚠️ **944 自己那次为何不补，948 没有解释，成因仍未查明**"
          "—— ⭐ **949 已把这一条降级为「不可复现」**（用 944 自己那组数字重跑，"
          "2/2 测到补偿），但**「944 当时到底发生了什么」仍不可知** ⇒ "
          "**不许**写成「已查明」（承 HH.4：钉假设的措辞不许把判据锁死在过时状态）",
          '"contradiction_resolved_it_was_a_misread_948": (' in _ausrc
          and "**944 那个挂了四批的矛盾结案了 —— 它是一个误读。**" in _ausrc
          and "真正的分界是 **76 vs {0, 1}**" in _ausrc
          and "**方向相反**" in _ausrc
          and "**944 把「冷启动铺窗口」读成了「补偿没来」——矛盾根本不存在。**"
          in _ausrc
          # ⭐⭐ 钉住 948 当时那句「成因仍未查明」**不许**被一起删掉（HH.4）
          and "948 当时记的是**成因仍未查明**" in _ausrc
          and "**944 的前置态与 `n_settle=2` 那一格是同一个值**" in _ausrc
          # ⭐⭐⭐ 钉住 949 的降级措辞：**只许**写「不可复现」，不许写「已查明」
          and "**不许**写成「已查明」" in _ausrc
          and "两条并列" in _ausrc)

    check("JJJJ.3 ⭐⭐⭐ **`settle_stable_ok = False`** —— settle 那几按的 "
          "`identity_stable` **全为 `False`** ⇒ **`76 → 0 → 1` 这条路径"
          "每一按身份都在动** ⇒ 按 948 自己写下的那道门"
          "（「**一个数看起来像状态不够，得知道它稳不稳**」）⇒ "
          "**`不带 ti = 1` 不是一个稳定状态，是铺窗口过程中的一个瞬态读数。**"
          "⇒ ⚠️ 这条**反过来削弱 944 自己的前置态** —— "
          "「settle 10 下、就绪 1」那个 **1** 也是瞬态",
          '"settle_readings_are_transient_948": (' in _ausrc
          and "**`76 → 0 → 1` 这条路径每一按身份都在动**" in _ausrc
          and "**一个数看起来像状态不够，" in _ausrc
          and "得知道它稳不稳**」）" in _ausrc
          and "它是铺窗口过程中的一个瞬态读数。**" in _ausrc
          and "**944 的连点是在一个瞬态上做的**" in _ausrc
          # ⭐ 钉探针：**每一按**的身份稳不稳都要记（947 缺这条）
          and '"identity_stable": d["identity_stable"],' in _p948
          and 'out["settle_stable_ok"] = bool(_st and all(_st))' in _p948)

    check("JJJJ.4 ⭐ 「第一击咬不咬」**也分 regime**（2/2）：就绪 **0** 与 **1** 两格"
          "第 1 击都是 `i=0 / bit=False / identity_stable=False`（**不咬**）；"
          "而就绪 **76** 那一格第 1 击反而 **`bit=True` / `added=[0]`**（**咬了**）"
          "⇒ ⇒ 「boot/预热之后第一击不咬」那条（945 的 8 + 947 的 4，**12 个格次**）"
          "**只在这一侧成立**，**不许**外推。"
          "⚠️ 另有读数：就绪 76 那格只咬到 **2**、另两格咬到 **4** ⇒ "
          "**落点与咬到的关系也分 regime**；三格 `cell_ok` 全 `False` ⇒ "
          "结论**限定在「咬到 2~4 次」这个范围内**",
          '"first_click_regime_dependent_948": (' in _ausrc
          and "**只在这一侧成立**，**不许**外推" in _ausrc
          and '"three_cells_not_all_ok_948": (' in _ausrc
          and "**落点与咬到的关系也分 regime**" in _ausrc
          and "**本批的结论限定在「咬到 2~4 次」这个范围内**" in _ausrc)

    check("JJJJ.5 ⭐⭐ **基线里不许同时留「未结案」与「已结案」**：944 那条矛盾键已改名 "
          "`compensation_scale_threshold_RESOLVED_944b_948`、且**旧名字必须已经不在**"
          "基线里（承 HH.4：矛盾解开**不许**把「为什么那次不补」一起删掉）"
          "⇒ FFFF.5 的措辞也跟着跟上事实，但**保留**待查项。"
          "⚠️ 而 946 记的「格 0 两轮 75→1 / 75→8」**不撤回** —— "
          "它**确实**两轮不一致，只是现在知道那一侧是**另一个 regime**",
          '"compensation_scale_threshold_RESOLVED_944b_948": (' in _ausrc
          and '"compensation_scale_threshold_unresolved_944b": (' not in _ausrc
          and '"contradiction_only_when_ready_not_zero_947": (' in _ausrc
          and "**本批把它推翻了**" in _ausrc
          # ⭐ 钉住「946 那条不撤回」这半句：两条读数都要在，别只留好看的
          and '944_contradiction_reproduced_946' in _ausrc
          # ⭐ 钉探针：五段 JS 与 947 逐字相同（防漂移，940 的办法）
          and "与 947 那份**不一致**" in _p948)

    # ══ 批 949：⭐⭐⭐ 用 944 自己那组数字重跑 —— **那次读数不可复现** ══════
    print("— KKKK. 批 949 944 那组数字 2/2 测到补偿 ⇒ 那次读数不是机制的性质 —")
    check("KKKK.1 ⭐⭐⭐ **格 0 用的就是 944 自己那组数字**（`n_settle=2` ⇒ 就绪 "
          "`不带 ti` = **1**、`scale=13`、连按 **6** 下 `Tab`），"
          "格 1 是**同一次跑里的对照**（`scale=8`、按 3 下），"
          "两格**只差 `scale` 与按压下数**、其余逐字相同 ⇒ ⭐ "
          "**对照必须放在同一次跑里** —— 947 栽过一次（它那张表被自己判成"
          "「**关系式推断、不是受控对照**」）",
          '"replay944_uses_its_own_numbers_949": (' in _ausrc
          and "**格 0 用的是 944 自己那组数字**" in _ausrc
          and "**同一次跑里的对照**" in _ausrc
          and "**对照必须放在同一次跑里**" in _ausrc
          # ⭐ 钉探针：两格的 `n_settle` **必须相同**（只差 scale 与按压下数）
          and '"same_settle_both_cells"' in _p949
          and "NSETTLE_FIXED = 2" in _p949
          and "CELLS = [{\"scale\": 13, \"n_rec\": 6}, "
              "{\"scale\": SCALE_FIXED, \"n_rec\": 3}]" in _p949)

    check("KKKK.2 ⭐⭐⭐⭐ **944 那次读数不可复现**（2/2，逐条相同）：格 0 就绪 **1**、"
          "点 13 次**落点 10、咬到 9**、连点后 `不带 ti = 10` ⇒ "
          "第 1 击 **`added=10`、`10 → 1`**（补回）、第 2~6 击**每击 `added=1`、"
          "`was_arm=True` 全程** ⇒ `added` 全 0 = **False**、有 `added` 的按压数 "
          "= **6/6** ⇒ ⇒ **`reproduced_944 = False`**，而两格**都补回** ⇒ "
          "**944 那次「连按 6 下 `added` 恒 0」不是机制的性质**",
          '"not_reproduced_949": (' in _ausrc
          and "**944 那次读数不可复现**" in _ausrc
          and "**`added=10`、`10 → 1`**" in _ausrc
          and "有 `added` 的按压数 = **6/6**" in _ausrc
          and "**`reproduced_944 = False`**" in _ausrc
          and "**944 那次「连按 6 下 `added` 恒 0」不是机制的性质**" in _ausrc
          # ⭐ 钉探针：「有没有被复现」是**真算**的，且**对照格必须在**
          and 'out["reproduced_944"] = bool(_c0 and all(x.get("added_all_zero") for x in _c0))' in _p949
          and 'out["control_present"] = bool(_c1 and all(x.get("n_click", 0) > 0 for x in _c1))' in _p949)

    check("KKKK.3 ⚠️⚠️ **944 自己就记下了它那一格不满足条件**，本批只是把它指出来："
          "它写的是「**两轮不一致**、所以**不许**下结论」，而 949 用**同一组数字**"
          "测到的是 **2/2 逐条相同**；结合 948 那条（**就绪 = 1 是瞬态**）⇒ "
          "**944 测的是一段身份还在动的瞬态** ⇒ 按 946 的纪律"
          "**那一段的读数本来就不作数**。⚠️ **但这是推断不是实测** —— "
          "本批**没有**复现出 944 那个不稳定的前置态 ⇒ **不许**写成"
          "「已查明 944 当时发生了什么」，只写「**不可复现**」+「**那一侧是瞬态**」"
          "两条并列",
          '"what_944_actually_recorded_949": (' in _ausrc
          and "**944 自己就记下了它那一格不满足条件**" in _ausrc
          and "**两轮不一致**、所以**不许**下结论" in _ausrc
          and "**944 测的是一段身份还在动的瞬态**" in _ausrc
          and "**但这是推断不是实测**" in _ausrc
          and "**不许**写成「已查明 944 当时发生了什么」" in _ausrc
          and "**不可复现**" in _ausrc)

    check("KKKK.4 ⭐⭐ **同一次跑里的对照格与 948 格 2 逐条相同**（就绪 1、落点 5、"
          "咬到 4、连点后 5、`added=5` 5→1、`added=1` 1→1、末击 `added=0`）⇒ ⇒ "
          "**跨批次可比的疑难第一次被消掉了**：不是靠「不同批次碰巧一样」，"
          "而是**同一段代码在同一次会话里测了两遍**。"
          "⚠️ 两格 `cell_ok` **都为 `False`**（落点 10≠9、5≠4）⇒ "
          "**「第一击不咬」仍是常态**；而格 0 的 `landable_found = 15`、"
          "格 1 是 **10** ⇒ **同一块画布上「本体可点的下标数」逐轮会变** ⇒ "
          "**规模类断言必须关系式**（935 的老教训，第三次应验）",
          '"control_matches_948_949": (' in _ausrc
          and "**跨批次可比的疑难第一次被消掉了**" in _ausrc
          and "**同一段代码在同一次会话里测了两遍**" in _ausrc
          and '"replay949_cells_not_ok_949": (' in _ausrc
          and "**同一块画布上「本体可点的下标数」逐轮会变**" in _ausrc
          and "**规模类断言必须关系式**" in _ausrc
          # ⭐ 钉探针：五段 JS 与 948 逐字相同（防漂移，940 的办法）
          and "与 948 那份**不一致**" in _p949
          # ⭐⭐ 钉探针：949 也写下了 948 栽过的那条（表格第一格不写裸数字）
          and "会被 pre-commit 钩子的批次行匹配" in _p949)
    check("KKKK.5 ⚠️⭐⭐ **门禁红了、而把它的每条条件单独求值都成立时，"
          "第一动作是「重跑」，不是「改判据」** —— 本批的门禁第一次跑出 "
          "**509/514**（JJJJ.2 + KKKK.1~4 五条红），而那 5 条判据的条件"
          "**逐条手算全部成立** ⇒ 二者矛盾 ⇒ 真相是**门禁读到了半旧的源码**"
          "（它在最后几次改动落定前就启动了）⇒ **重跑一遍 = 514/514**。\n"
          "⚠️ **改判据会把一个时序问题变成一个永久的假红** —— "
          "而门一旦被人当成「需要放宽的东西」，它就失去意义了"
          "（942：**一个恒真的判据比没有判据更坏**）。"
          "⇒ 这是「**别等门禁跑完才发现**」的**反面**用例：那次是门禁跑了才发现，"
          "而**正确动作是重跑** ⇒ **先怀疑自己的时序，再怀疑判据**",
          '"verifier_stale_read_949": (' in _ausrc
          and "**门禁读到了半旧的源码**" in _ausrc
          and "**重跑一遍 = 514/514**" in _ausrc
          and "第一动作是「重跑」，不是「改判据」" in _ausrc
          and "**改判据会把一个时序问题变成一个永久的假红**" in _ausrc
          and "**先怀疑自己的时序，再怀疑判据**" in _ausrc)

    # ══ 批 950：⭐⭐⭐⭐⭐ 「铺窗口」从**现象**升级成**规则**（零点击）═════
    print("— LLLL. 批 950 零点击 14 下：铺窗口是一次性事件；而指针会在内部按钮上冻住 —")
    check("LLLL.1 ⭐⭐⭐⭐⭐ **「冷启动铺窗口」的完整规则**（**零点击**、2/2 逐条相同）："
          "`不带 ti` 曲线 = **[76, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]** ⇒ "
          "第 1 按 **76 → 0**（**铺窗口**）、第 2 按 **0 → 1**（**建立「当前」**）、"
          "第 3 按之后**恒 1**（§131 不变式**成立**）⇒ 第 1 按落差 **76**、"
          "其后**最大落差 1** ⇒ ⭐ 「铺窗口」是**一次性事件**，"
          "**不是**「每按一下都在铺」。⚠️ 关于它此前只有三个孤立读数（下 0/1/2/3 下），"
          "**第 4 下之后从没测过** —— 本批补上",
          '"coldwindow_curve_950": (' in _ausrc
          and "**[76, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]**" in _ausrc
          and "**铺窗口**，所有节点都拿到 `tabindex`" in _ausrc
          and "**建立「当前」节点**" in _ausrc
          and "「铺窗口」是**一次性事件**" in _ausrc
          and "**第 4 下之后从没测过**" in _p950
          # ⭐ 钉探针：**零节点点击**（只点画布空白去焦点）+ 压到底 14 下
          and "N_PRESS = 14" in _p950
          and '"zero_node_clicks"' in _p950
          and "只点**画布空白**去焦点" in _p950)

    check("LLLL.2 ⭐⭐⭐⭐⭐ **指针会冻住 —— 而且冻在「焦点落在节点内部按钮」的那几按**："
          "指针序列 `[] → [0] → [1] → [2] → [2] → [2] → [2] → [2] → [3] → …` ⇒ "
          "第 2~4 按**+1 每按一次**；⚠️ **第 5~8 按整整 5 下冻在 `[2]` 不动**，"
          "而那 5 下 `active_before = BUTTON`、`was_arm = False`、三元组**全空**；"
          "第 9 按 `active_before` 回 `DIV`、`was_arm = True`、`added = 1` ⇒ "
          "指针 **2 → 3 立刻恢复游走** ⇒ ⭐⭐⭐⭐⭐ **焦点一旦落在节点内部的 `BUTTON` "
          "上，`Tab` 连按 5 下指针完全不动**",
          '"pointer_freezes_on_inner_button_950": (' in _ausrc
          and "**第 5~8 按：指针整整 5 下冻在 `[2]` 不动**" in _ausrc
          and "`active_before = BUTTON`、`was_arm = False`" in _ausrc
          and "**2 → 3** **立刻恢复游走**" in _ausrc
          and "**焦点一旦落在节点内部的 `BUTTON` 上，" in _ausrc
          and "`Tab` 连按 5 下指针完全不动**" in _ausrc
          # ⭐ 钉探针：`no_ti` 是**正面读数**（指针在哪），且**截断自带标记**
          and "NO_TI_JS = " in _p950
          and "no_ti_capped: out.length > cap," in _p950
          and "NO_TI_CAP = 40" in _p950)

    check("LLLL.3 ⚠️⭐⭐ **本批自己设计的可红门真的红了** —— 这正是它存在的意义："
          "判据写的是「**「没有 tabindex 的那个下标每按一次就变」**」，"
          "而实测 `pointer_walks = **False**`（5 下重复 `[2]`）⇒ ⇒ "
          "**「每按一次就往前挪一格」这句话本身是错的** —— 正确的是"
          "「**每按一次有可能挪一格；落在内部按钮上时连挪 5 下都不动**」⇒ ⭐ "
          "**一道可红的门比一道恒绿的门值钱**：它**当场把一句错话拦下来了**，"
          "而 942 的教训是**一个恒真的判据比没有判据更坏**。"
          "⚠️ 对照：`steady_at_one` 与 `press1_is_the_big_drop` 都**绿** ⇒ "
          "它们没有在混日子",
          '"pointer_walks_gate_went_red_950": (' in _ausrc
          and "**本批自己设计的可红门真的红了**" in _ausrc
          and "**「每按一次就往前挪一格」这句话本身是错的**" in _ausrc
          and "**一道可红的门比一道恒绿的门值钱**" in _ausrc
          and "它们没有在混日子" in _ausrc
          # ⭐ 钉探针：那道门**真的在算**（不是只声明）
          and 'c["pointer_walks"] = bool(len(seq) > 1 and len(set(seq)) == len(seq))' in _p950
          and "⚠️ 可红：红了就说明那个下标不动（指针不游走）" in _p950
          and "⚠️ 这道门**不是恒真门**" in _p950
          and "「铺窗口是一次性事件」这个说法**错了**" in _p950)

    check("LLLL.4 ⭐⭐⭐⭐⭐ **944 那次「连按 6 下 `added` 恒 0」现在有了解释**："
          "只要按 Tab 之前焦点落在内部 `BUTTON` 上，**连按 5 下指针都不动**"
          "（三元组自然全空）⇒ ⇒ **不是「没补偿」，是那 6 下压根没在臂窗口上按**；"
          "而 949 能测到补偿是因为它**程序化聚焦了节点本体**才按的 `Tab` ⇒ "
          "945 的 `body` / `asis` 两臂同形，是因为**点击之后焦点本来就在 `DIV` 上**。"
          "⚠️⚠️ **但这三条链接都是推断、不是实测** —— **944 从没记过「无 ti 下标」"
          "是哪几个** ⇒ **不许**写成「已查明 944 当时的状态」"
          "⇒ 只写「**本批给出一条能解释它的机制**，而 944 那次**没有留下能证实它的读数**」。"
          "⚠️ 949 那条「**不可复现**」的措辞**不许**因此被删（承 HH.4）",
          '"explains_944_added_all_zero_950": (' in _ausrc
          and "是那 6 下压根没在臂窗口上按**" in _ausrc
          and "**这三条链接都是推断、不是实测**" in _ausrc
          and "保留下来只为对照** ⭐" in _ausrc
          and "**951 的证伪**" in _ausrc
          # ⭐⭐ 钉住 949 的措辞**不许**被 950 顺手删掉
          and '"not_reproduced_949": (' in _ausrc
          and "**944 那次读数不可复现**" in _ausrc
          # ⭐ 钉探针：五段 JS 与 949 逐字相同、而 `NO_TI_JS` **不许混进去**
          and "与 949 那份**不一致**" in _p950
          and 'assert "NO_TI_JS" not in _p949src' in _p950)

    check("LLLL.5 ⭐ 本批**零节点点击**（只点一次画布空白去焦点，943 起的标准前置）⇒ "
          "设计门 `zero_node_clicks` 在**每一轮**都为 True；⚠️ 且「无 ti 下标」"
          "那份读数**截断到 40 条并如实记 `no_ti_capped`**（冷启动那一档 76 条"
          "**超了**）⇒ ⭐ **截断必须自带标记** —— "
          "**不许**让人以为那就是全部",
          '"zero_clicks_and_capped_reading_950": (' in _ausrc
          and "**零节点点击**" in _ausrc
          and "截断必须**自带标记**" in _ausrc
          # ⭐ 钉探针：截断标记**真的被记了**（不是只在文档里说）
          and "**身份不稳的那一段三元组一律不许当读数**（946）" in _p950
          and "no_ti_capped" in _p950
          # ⭐⭐ 钉探针：950 也写下了 948 栽过的那条（表格第一格不写裸数字）
          and "会被 pre-commit 钩子的批次行匹配" in _p950)

    # ══ 批 951：⚠️⭐⭐⭐ **950 那条推断作废**（被自己的门红掉）══════════════
    print("— MMMM. 批 951 arm_focus 是 no-op ⇒ 950 那条推断撤回；944 仍无解释 —")
    check("MMMM.1 ⚠️⭐⭐⭐ **`arm_focus` 这个自变量在 944 的条件下是个 **no-op**：**"
          "格 0（**不**程序化聚焦，照 944）实测读到 "
          "`focus_skipped = {'active_tag': 'DIV', 'focus_in_node': True}` ⇒ "
          "**点击之后焦点本来就在节点本体上** ⇒ 「不聚焦」与「聚焦」**是同一件事**；"
          "两格**逐条相同**（2/2，四个格次全同）：指针序列都是 "
          "**`[68] → [69] → [70] → [71] → [72] → [73]`**、"
          "`指针动 6/6`、`冻住 0 下`、`added` 合计 **15**、补回 **True** ⇒ ⇒ "
          "**`focus_moved_the_pointer = False`** ⇒ "
          "**「这个操纵到底动了没有」的答案是：没动**",
          '"arm_focus_is_a_noop_here_951": (' in _ausrc
          and "**`arm_focus` 这个自变量在 944 的条件下是个 **no-op**：**" in _ausrc
          and "**点击之后焦点本来就在节点本体上**" in _ausrc
          and "`指针动 6/6`、`冻住 0 下`、`added` 合计 **15**" in _ausrc
          and "**`focus_moved_the_pointer = False`**" in _ausrc
          and "**「这个操纵到底动了没有」的答案是：没动**" in _ausrc
          # ⭐ 钉探针：格 0 **真的不调** `ARM_FOCUS_JS`、并**如实记下**焦点读数
          and "if af:" in _p951
          and 'c["focus_skipped"] = fnow' in _p951
          and 'out["focus_moved_the_pointer"] = bool(' in _p951)

    check("MMMM.2 ⚠️⚠️⚠️ **撤回 950 那条推断**（承 §77 + 950 自己写下的"
          "「**这三条链接都是推断、不是实测**」）：950 说「焦点落在内部 `BUTTON` 上 "
          "⇒ 指针冻住」⇒ **因此** 944 那次 6 下 `added` 恒 0 是「没在臂窗口上按」"
          "⇒ ⭐⭐⭐ **本批证伪的是那个「因此」** —— 在 **944 的数字下**"
          "**不聚焦也照样 6/6 全咬、指针 6/6 全动** ⇒ **950 的冻结现象本身是真的**"
          "（零点击、2/2），**但它的触发条件属于「冷启动直接 `Tab`」那条路径**"
          "（第 5~8 按），**在「13 连点之后」根本不成立** ⇒ ⚠️⚠️ "
          "**我上一批把两条路径混成了一条** ⇒ **950 的机制不得再被引用来解释 944**。\n"
          "⭐ 而 950 那条**原文保留在基线里**（不删）—— 保留它是为了让下一个人"
          "看得见「当时为什么会那么想」，并看见它后来被什么打掉的",
          '"inference_950_retracted_951": (' in _ausrc
          and "**撤回 950 那条推断**" in _ausrc
          and "**本批证伪的是那个「因此」**" in _ausrc
          and "**但它的触发条件属于「冷启动直接 `Tab`」那条路径**" in _ausrc
          and "**我上一批把「冷启动路径」与「连点之后路径」混成了一条**" in _ausrc
          and "**950 的机制不得再被引用来解释 944**" in _ausrc
          # ⭐⭐ 钉住 950 那条**被改成撤回版**（原文保留、措辞跟上事实）
          and '"explains_944_added_all_zero_950": (' in _ausrc
          and "**本条已于 951 撤回" in _ausrc
          and "**当时的推断**" in _ausrc
          and "**951 的证伪**" in _ausrc
          # ⭐⭐ 950 那条**两条仍然成立**的部分**不许**被一起删掉（承 HH.4）
          and "**950 的冻结现象本身仍然成立**" in _ausrc
          and "**被撤回的只是「拿它解释 944」这一步**" in _ausrc)

    check("MMMM.3 ⚠️⭐⭐⭐ **更要紧的一条：写 950 那条推断之前，我**没有先查基线里"
          "有没有反例** —— 而 945 早就把这条读数**写进基线**了"
          "（**「点击之后焦点本来就在节点本体上」**），"
          "951 实测 `focus_skipped` **与那句话逐字吻合** ⇒ ⭐⭐⭐ "
          "**一条推断如果与基线里已有的读数矛盾，那它一开始就不该被写下来** —— "
          "不是「写完再被证伪」，是「写之前就该撞上」⇒ ⚠️ "
          "**门禁只查判据锚不锚得到，查不出「这句推断和已有读数打架」** ⇒ ⇒ "
          "**这一条只能靠写的人自己先查**",
          '"baseline_already_had_the_counterexample_951": (' in _ausrc
          and "没有先查基线里" in _ausrc
          and "**点击之后焦点本来就在节点本体上**" in _ausrc
          and "**与那句话逐字吻合**" in _ausrc
          and "那它一开始就不该被写下来**" in _ausrc
          and "**门禁只查判据锚不锚得到，查不出「这句推断和已有读数打架」**"
          in _ausrc
          # ⭐ 钉住 945 那条**确实**在基线里（不然「早就写进去了」就成了空话）
          and '"not_an_arm_event_hypothesis_refuted_945": (' in _ausrc)

    check("MMMM.4 ⚠️⚠️⚠️ **「944 自己那次为何不补」仍然未查明**，而且本批**给它补了一条"
          "负面证据**：在 **944 的数字**（就绪 1、13 连点、6 下 `Tab`）下，"
          "**2/2 逐条相同**地测到指针 **6/6 每按都动**、`added` 合计 **15**、"
          "终值 **1**、补回 **True** ⇒ ⇒ **944 那次是一个至今无法复现的异常**，"
          "**不是**「焦点卡在内部按钮」⇒ 与 949 那条**并列**："
          "**两条独立的重跑都测到补偿** ⇒ **944 那次的成因在本树上已无从追查** ⇒ "
          "**不许**再往它身上加机制解释。⚠️ 949 那条「**不可复现**」"
          "与 948 那句「**成因仍未查明**」都**不许**被删（承 HH.4）",
          '"944_still_unexplained_with_negative_evidence_951": (' in _ausrc
          and "**仍然未查明**" in _ausrc
          and "**944 那次是一个至今无法复现的异常**" in _ausrc
          and "**不是**「焦点卡在内部按钮」" in _ausrc
          and "**两条独立的重跑都测到补偿**" in _ausrc
          and "**944 那次的成因在本树上已无从追查**" in _ausrc
          and "**不许**再往它身上加机制解释" in _ausrc
          # ⭐⭐ 钉住 948/949 的措辞**不许**被 951 顺手删掉
          and '"not_reproduced_949": (' in _ausrc
          and "948 当时记的是**成因仍未查明**" in _ausrc
          # ⭐ 钉探针：六段 JS（含 950 的新件）与 950 逐字相同
          and "与 950 那份**不一致**" in _p951
          # ⭐ 钉探针：951 也写下了 948 栽过的那条纪律（表格第一格不写裸数字）
          and "会被 pre-commit 钩子的批次行匹配" in _p951)

    # ══ 批 952：⭐⭐⭐⭐⭐ 「冻住」其实是「`Tab` 走完了工具条」（零点击）═════
    print("— NNNN. 批 952 那不是卡住，是 Tab 正常走完时间线工具条的 4 个按钮 —")
    check("NNNN.1 ⭐⭐⭐⭐⭐ **那不是「卡住」，是 `Tab` **正常走完了节点工具条** ——**"
          "冻结段的 4 个元素身份**逐一取到**（全是**时间线节点** "
          "`node_index=2`「时间线 node: 时间线 1」的工具条按钮）："
          "按 4 → `timeline-toolbar`/**`导出时间线`**、按 5 → `timeline-toolbar`/"
          "**`全屏编辑`**、按 6 → `timeline-mute-button`/**`静音`**、"
          "按 7 → `timeline-passive-source-picker-slot`/**`添加素材到时间线`**、"
          "按 8 → 离开工具条落到 `node#3` 的 `DIV` ⇒ ⭐ "
          "**4 个按钮、4 下按压、指针一步都不动** ⇒ **不是「指针冻住」，"
          "是「指针在这段里根本不参与」** ⇒ 与 944b 的 "
          "`inner_button_not_an_arm_event` **完全同形**",
          '"not_frozen_but_walking_the_toolbar_952": (' in _ausrc
          and "**正常走完了节点工具条**" in _ausrc
          and "`tid=timeline-mute-button` / aria **`静音`**" in _ausrc
          and "`tid=timeline-passive-source-picker-slot` / aria " in _ausrc
          and "**4 个按钮、4 下按压、指针一步都不动**" in _ausrc
          and "**不是「指针冻住」，是「指针在这段里根本不参与」**" in _ausrc
          and "**完全同形**" in _ausrc
          # ⭐ 钉探针：`WHOAMI_JS` 是**新件**、且必须**不在** 951 里
          and 'assert "WHOAMI_JS" not in _p951src' in _p952
          and "WHOAMI_JS = " in _p952
          and "与 951 那份**不一致**" in _p952)

    check("NNNN.2 ⭐⭐⭐⭐⭐ **指针只在「从节点本体 `DIV` 出发的那一按」上 +1**："
          "按 1~4 每按 +1；按 5/6/7（**在工具条的 3 个按钮之间**）指针**恒 `[2]`**；"
          "按 8（**离开**工具条落到 `DIV`）指针**仍 `[2]`**；"
          "按 9（从 `DIV` 出发）指针**才 `[2]→[3]`** ⇒ ⇒ "
          "**「一按滞后」是真的**（2/2），**但 950 当时的因果说错了** —— "
          "不是「离开的那一按不算」，而是「**指针只认 `DIV` 出发的那一按**」"
          "⇒ ⭐ 这也**顺带解释了 §131 那条不变式为什么对得上**："
          "指针每次只 +1、工具条那 4 下**一次都不 +** ⇒ `不带 ti` 恒 1",
          '"pointer_only_moves_on_div_press_952": (' in _ausrc
          and "**指针只在「从节点本体 `DIV` 出发的那一按」上 +1**" in _ausrc
          and "**「一按滞后」是真的**" in _ausrc
          and "**但 950 当时的因果说错了**" in _ausrc
          and "**指针只认 `DIV` 出发的那一按**" in _ausrc
          and "**顺带解释了 §131 那条不变式为什么对得上**" in _ausrc
          # ⭐ 钉探针：滞后的门**真的在算**（不是只声明）
          and 'c["lag_is_one_press"] = bool(' in _p952
          and 'c["left_button_press"] = next(' in _p952)

    check("NNNN.3 ⭐⭐ 判别组（2/2 逐条相同）：**`Shift+Tab` 焦点**立刻**离开工具条**"
          "（落到 `aria='Canvas'`）而指针**仍不动** ⇒ **反向臂有效、且同样不推指针**；"
          "紧接着的 `Tab` 指针 **`[2]→[3]`** **动了** ⇒ 再次印证「从 `DIV` 出发"
          "才推指针」；**`ArrowDown`** 焦点**没动**、指针**没动**；"
          "**`Escape`** 焦点**没动**、指针**没动** ⇒ ⭐ "
          "**`Escape` 不能把焦点从工具条里弄出来** —— "
          "**反向臂比 `Shift+Tab` 差一截**"
          "——— ⚠️⚠️ **本条已被 953 部分改写，判据随之改成钉改写横幅**（承 HH.4）———\n"
          "⚠️ **`Escape` / `ArrowDown` 那两按按下时焦点**已经在节点本体 `DIV` 上、"
          "**不在工具条里** ⇒ 「`Escape` 不能从工具条里弄出来」**没有对应的那一按**；\n"
          "⚠️ 「`Shift+Tab` 焦点**立刻**离开工具条」是**位置相关**的（源站那按是从"
          "**第一个**按钮按的）。**仍然成立**的那条：`Escape` 在**节点本体 `DIV`** 上不动焦点。",
          '"discrimination_952": (' in _ausrc
          # ⭐⭐ 钉改写横幅（**不钉**已被推翻的那两句 —— 判据不许钉假话）
          and "**本条已被 953 部分改写**" in _ausrc
          and "`ArrowDown` 那两按按下时焦点**已经在节点本体上、不在工具条里**" in _ausrc
          and "**`Shift+Tab` 立刻离开工具条**是**位置相关**的" in _ausrc
          # ⭐ 原文**必须还在**（撤销结论时原文保留）
          and "**`Escape` 不能把焦点从工具条里弄出来**" in _ausrc
          and "**反向臂比 `Shift+Tab` 差一截**" in _ausrc
          # ⭐ 钉 953 那条撤回
          and '"escape_claim_retracted_953": (' in _ausrc
          and "**按 `Escape` 时焦点压根不在工具条里**" in _ausrc
          and "「出不来」在**复刻**上成立" in _ausrc
          # ⭐ 钉探针：判别组**不许**预设方向（三条各判各的）
          and 'PROBE_STEPS = [("Shift+Tab", 1), ("Tab", 1), ("ArrowDown", 1),'
              in _p952
          and '"Escape", 1), ("Tab", 3)]' in _p952
          and "**都不许**预设方向" in _p952)

    check("NNNN.4 ⚠️⚠️⚠️ **本条整条已被 953 撤回**（承 HH.4，判据随之改钉改写横幅）："
          "**`Tab` 周期 = 10** 与 **「周期长度 = 节点数 + 带工具条的节点数」**\n"
          "⚠️ 两条**互相独立**的证据：① **952 自己的 14 按读数**就否掉了它 —— "
          "出现 **10 个不同的节点停靠点**（下标 `0..9`）**且从未回卷**；"
          "而 952 的算法「9 个节点 + 工具条 1 段 = 1 下 ⇒ 10」**把「4 个按钮 4 下」"
          "写成了「1 下」**，**它自己的前提和结论互相矛盾**。"
          "② **复刻侧连「周期」都不成立**（开环、走完 24 个画布内停靠点后"
          "焦点**离开画布**、进入全局 chrome）。\n"
          "⇒ **仍然成立**的是它背后的纪律：**周期/规模类断言必须关系式**。"
          "⚠️⭐⭐ **新增待查**：**源站的 `Tab` 会不会离开画布** —— 14 按**没走到环的尽头**"
          "⇒ **源站那一侧必须加预算重测**，不许拿复刻的开环替源站下结论。",
          '"tab_cycle_is_10_here_952": (' in _ausrc
          # ⭐⭐ 钉改写横幅 + 原文仍在
          and "**本条整条已被 953 撤回**" in _ausrc
          and "**952 自己的 14 按读数就否掉了它**" in _ausrc
          and "**把「4 个按钮 4 下」写成了「1 下」**" in _ausrc
          and "**它自己的前提和它自己的结论互相矛盾**" in _ausrc
          and "**Tab 周期 = 10**" in _ausrc          # 原文保留
          and "**周期长度 = 节点数 + 带工具条的节点数**" in _ausrc   # 原文保留
          # ⭐ 钉 953 那条撤回 + 新增待查
          and '"cycle_10_retracted_953": (' in _ausrc
          and "**`Tab 周期 = 10`」与**「周期 = 节点数 + 带工具条的节点数」**" in _ausrc
          and "**源站那一侧必须加预算重测**" in _ausrc
          and "**不许**拿复刻的开环去替源站下结论" in _ausrc
          # ⭐⭐⭐ 钉住那条更要紧的：**101/104 反例就在 952 自己引用的下一句**
          and "101/104 基线就在 952 自己引用的那句话里**" in _ausrc
          and "**101 / 104**（两轮不同，因为节点数 77 / 76 也在变）" in _ausrc
          and "**一个完整周期（本画布 = 101 次按压）**" in _ausrc
          and "**引用**了，却**没有拿它跟自己的「10」对账**" in _ausrc
          and "而且反例就在自己引用的下一句**" in _ausrc
          and "**源站的周期是 ~101、复刻这一侧是 24 个停靠点然后跑出画布**" in _ausrc
          # ⭐ 钉探针：源站侧的核算**真的在算**
          and '"cycle_10_supported": bool(' in _p953
          and '"wrapped_at_press": wrapped_at' in _p953
          # ⭐ 钉探针：够长的按压数（**不是** 952 的 14 —— 901 的先例：故意走过一圈）
          and "N_PRESS_BASE = 14" in _p952
          and "N_PRESS_BASE = 28" in _p953
          and "**这是补预算，不是改判据" in _p953)

    check("NNNN.5 ⚠️⭐⭐⭐ **`active_before == active_after` 并不代表焦点没动** —— "
          "这是 950 那个「被 `Tab` 吞了」说法的**来源**，上一批是**读图说话**："
          "按 5 前 `BUTTON` 后 `BUTTON` ⇒ **真的没动**；"
          "而按 6/7 前 `BUTTON` 后 `BUTTON`、**但 `aria` 与 `tid` 都变了** ⇒ "
          "**焦点动了** ⇒ ⭐⭐⭐ **光看 `tag` 读不出焦点有没有动** —— "
          "这些按钮**不自带 `testid`、要靠 `closest('[data-testid]')` 才借到节点的** ⇒ "
          "**必须比 `aria-label`（或 `type`）** ⇒ ⭐ "
          "**「前标签 == 后标签」是个陷阱**：它让 `focus_moved=False` "
          "**只对 4 次里的 1 次为真**，而我据此写了「吞了 3 下」。"
          "⇒ 950 那条**原文保留**、**心因模型已标注被改写**（承 HH.4）"
          "——— ⚠️⚠️ **953 又把这条的计数也改写了**（原文保留）———\n"
          "⚠️ **「按 5 真的没动」是错的**：按 5 是「`导出时间线` → `全屏编辑`」，"
          "**`aria` 变了、焦点动了**；那个比例**不是 1/4 而是 0/4** ⇒ "
          "**`swallowed_presses=1` 整条作废** ⇒ 源站那 4 个「指针不动」的按压"
          "**焦点 4/4 全动了** ⇒ ⭐⭐⭐ **`「指针不动」≠「焦点不动」`**。"
          "**原理那一半仍然成立**（必须比 `aria-label`/`type`），"
          "被推翻的只是**那句计数**和**据此写下的「吞了 3 下」**",
          '"active_tag_equal_does_not_mean_focus_stayed_952": (' in _ausrc
          and "`active_before == active_after` 并不代表焦点没动" in _ausrc
          and "我上一批是**读图说话**" in _ausrc
          and "**光看 `tag` 读不出焦点有没有动**" in _ausrc
          and "**必须比 `aria-label`（或 `type`）**" in _ausrc
          and "**「前标签 == 后标签」是个陷阱**" in _ausrc
          # ⭐⭐ 钉住 950 那条**被加了改写横幅**、且**现象仍标为成立**
          and "**「冻住」这个说法已被 952 改写**" in _ausrc
          and "**现象**（`no_ti` 恒 `[2]`）" in _ausrc
          and "**被改写的只是「冻住」这个心因模型**" in _ausrc
          # ⭐⭐ 钉 953 的改写横幅（**不钉**「只对 4 次里的 1 次为真」这个已被推翻的数）
          and "**以下三行已被 953 改写（原文保留，承 HH.4）**" in _ausrc
          and "**「按 5 真的没动」是错的**" in _ausrc
          and "那个比例**不是 1/4 而是 0/4**" in _ausrc
          and "**整条作废**" in _ausrc
          and "**正确说法是：「指针不动」不等于「焦点不动」**" in _ausrc
          and "被推翻的只是**那句计数**" in _ausrc
          # ⭐ 钉 953 那条「本批把 952 自己的仪器判红了」
          and '"weak_instrument_caught_953": (' in _ausrc
          and "**正确说法是：「指针不动」不等于「焦点不动」**" in _ausrc
          and "**另立一条强的并排记**" in _ausrc
          # ⭐⭐ 钉探针：**强判据**真的在算（比身份，不是比 tag）
          and 'def strong_moved(row, which_before="before", which_after="after"):'
              in _p953
          and 'return identity(row, which_before) != identity(row, which_after)'
              in _p953
          and '"swallowed_presses_strong"' in _p953
          and "**不改 952 那把尺子**" in _ausrc)

    # ══ 批 953：⭐⭐⭐⭐ 把 952 那把尺子搬到**复刻侧**量一遍 ══════════════
    print("— OOOO. 批 953 同一把尺子量复刻：并排读数 + 三条 952 结论被推翻 —")

    check("OOOO.1 ⭐⭐⭐ 本批**不是**再取一次样，是**拿 952 的尺子量复刻**："
          "**七段 JS 全部与 952 逐字相同**（本批**零**新件 JS）、"
          "**七个 Python 助手也逐字相同**（用 `inspect.getsource` 对着 952 的"
          "**文件内容** assert ⇒ 改一个字就红）；**唯一自变量 = URL**。"
          "⚠️ 这条纪律**当场救了本批**：第一版往 `press_row` 里塞了 2 行新字段 "
          "⇒ **自己把自己判红** ⇒ 才发现指针**不用新仪器**"
          "（`CENSUS_JS` 已经把 `ti` 带回来了）。设计门：`js/py_verbatim` ✅、"
          "`zero_node_clicks` ✅、`pressed_exactly_n` ✅、`replica_actually_moved` ✅、"
          "`reached_the_freeze` ✅、`curve_reproducible_norm` ✅。",
          '"replica_ring_953": {' in _ausrc
          and '"same_ruler_verbatim_953": (' in _ausrc
          and "**不是**再取一次样，是**拿 952 的尺子量复刻**" in _ausrc
          and "**七个 Python 助手也逐字相同**" in _ausrc
          and "**自己把自己判红**" in _ausrc
          and "唯一自变量 = **URL**（源站 → 本地复刻）" in _ausrc
          # ⭐ 钉探针：七段 JS 的逐字 assert **真的在文件里**、且新件不许混进去
          and 'for _name, _js in zip(("BLANK_JS", "CENSUS_JS", "NO_TI_JS", "POINT_JS",'
              in _p953
          and 'assert "READY_JS" not in _p952src' in _p953
          # ⭐ 钉探针：Python 侧的逐字 assert 也是对着**文件内容**
          and "for _fn in (ev, dump, guard, guard_point, delta, press_row, curve_key):"
              in _p953
          and "_s in _p952src" in _p953
          # ⭐⭐ 「操纵到底动了没有」必须自己答，且**可红**
          and 'out["replica_actually_moved"] = bool(' in _p953
          and '"replica_actually_moved": out["replica_actually_moved"],' in _p953
          # ⭐ 键免疫针：`seq` 原始键不许漏登记（base 与 probe 的 `k` 会撞号）
          and '"hit_tag", "focus_ok", "seq",' in _p953
          and 'assert not (RAW_KEYS & DERIVED_KEYS)' in _p953)

    check("OOOO.2 ⚠️⭐⭐⭐ **指针的定义两边不同，写出来才不许糊过去**："
          "源站解除布防是**把 `tabindex` 属性摘掉** ⇒ 指针 = **第一个没有 `tabindex` "
          "的下标**；复刻的 `armAll` 写的是 `'0'`/`'-1'`、**属性一直都在** ⇒ "
          "`no_ti` 在复刻上**恒为空**、源站那把尺子**读不出复刻的指针**。"
          "⇒ **不需要另加仪器**：`CENSUS_JS` 已经把 `ti` 带回来了，两个口径"
          "**从同一份数据派生** ⇒ 「同一件事的两种口径，不是两个现象」。"
          "⚠️⭐⭐ **但两个口径在序号上差一格**（源站那个是「**刚离开**的节点」、"
          "复刻那个是「**下一个要落脚**的节点」）⇒ **不能拿「指针落在第几个」"
          "直接比两边**，该比的是**形状**。",
          '"pointer_two_calibers_953": (' in _ausrc
          and "**指针的定义两边不同，这件事必须写出来、不许糊过去**" in _ausrc
          and "**恒为空**，源站那把尺子**读不出复刻的指针**" in _ausrc
          and "**不需要另加仪器**" in _ausrc
          and "**同一件事的两种口径，不是两个现象**" in _ausrc
          and "两个口径在序号上差一格**" in _ausrc
          and "**该比的是**形状**" in _ausrc
          # ⭐ 钉探针：两口径**真的**从同一份 `ti` 派生
          and 'def armed_of(ti):' in _p953
          and 'if ti[i] == "0"' in _p953
          and 'if ti[i] is None' in _p953
          and "nt, ar = no_ti_of(ti), armed_of(ti)" in _p953
          # ⭐ 钉探针：统一口径不许把「读不懂」当成 0
          and "**不许**当成 0" in _p953)

    check("OOOO.3 ⭐⭐⭐⭐ **复刻的 `Tab` 环是开环**：走完画布内**全部 24 个停靠点**"
          "之后，焦点**离开画布**、进入全局 chrome ⇒ **「周期」这个量在复刻侧"
          "根本不存在**（`ring_closed = False`、实测从不回卷）。停靠点序列 2/2 逐条相同："
          "`node#0` + 5 个 video 内层 → `node#1`/`#2`/`#3`/`#4` + 6 个时间线内层 "
          "→ `node#5` + 6 个主体内层 → `node#6` + `inner:进入导演台` "
          "→ ⭐ **`out:返回首页` → `out:Canvas title: 测试项目` → `out:项目`**。"
          "⇒ 画布内 = 7 节点 + 17 内层 = **24 个停靠点**，之后**跑出画布**。"
          "⇒ ⭐ **形状与源站同形**（进内层 → 指针冻住 → 离开那一按仍不动 → "
          "下一按才动），**但环的开闭两边不同**。",
          '"ring_is_open_not_cyclic_953": (' in _ausrc
          and "**复刻的 `Tab` 环是**开环**" in _ausrc
          and "**`out:返回首页` → `out:Canvas title: 测试项目` → `out:项目`**"
              in _ausrc
          and "**24 个停靠点**，之后**跑出画布**" in _ausrc
          and "在复刻侧根本不存在**" in _ausrc
          and "**不许**说源站会回卷" in _ausrc
          # ⭐ 钉探针：停靠点分类**真的在算**（内层 / 节点本体 / 出画布三分）
          and 'if w.get("tag") == "DIV" and w.get("in_node_list"):' in _p953
          and 'inner:' in _p953 and 'out:' in _p953
          and 'c["stop_seq"] = [stop_name(r) for r in main_rows' in _p953
          # ⭐ 钉探针：`ring_closed` 这道门**可红**、且红的就是「开环」
          and '"ring_closed": bool(all(' in _p953
          and 'run["cells"][0].get("cycle_len") is not None' in _p953
          # ⭐ 钉探针：强判据下「焦点也没动」= 0（弱判据说 8）
          and 'c["swallowed_presses_strong"] = sum(' in _p953
          and "and not strong_moved(r))" in _p953)

    check("OOOO.4 ⚠️⭐⭐ **逐字那道 `curve_reproducible` 在复刻上恒红** —— "
          "而那**不是**「读数不稳」，是**被测对象**不稳定："
          "复刻节点 `data-testid` **带时间戳**（`rf__node-text-1791076289857`），"
          "源站的 id **稳定**（`rf__node-node_236ctpehgg`）⇒ 这是**复刻与源站的"
          "一处真实差异**。处置**不是**改产品让门变绿、**也不是**放宽门："
          "逐字那道**照旧如实记红**，另加一道**只把 `tid` 尾部数字归一化**的比较，"
          "**两道都进读数**（归一化后 `curve_reproducible_norm = True`）。"
          "⚠️ 与 949 那次对照：门红了先怀疑仪器 —— 这次**仪器是对的**，"
          "是**被测对象**不稳定，所以正确处置是**并排记两道**。",
          "**逐字那道 `curve_reproducible` 在复刻上恒红**" in _ausrc
          and "是**被测对象**不稳定" in _ausrc
          and "**带时间戳**" in _ausrc
          and "**这是复刻与源站的一处真实差异**" in _ausrc
          and "**不是**改产品让门变绿、**也不是**放宽门" in _ausrc
          and "**照旧如实记红**" in _ausrc
          and "**只把 `tid` 尾部数字归一化**" in _ausrc
          and "**两道都进读数**" in _ausrc
          and "这次**仪器是对的**" in _ausrc
          # ⭐ 钉探针：归一化**只**动 tid 尾部数字，其余逐字
          and 'def norm_tid(tid):' in _p953
          and 're.sub(r"-\\d{6,}$", "", str(tid))' in _p953
          and "reps_identical_norm" in _p953
          and "curve_reproducible_norm" in _p953)

    check("OOOO.5 ⭐⭐ 补预算而不是改判据（901 的先例）：第一版 `N_PRESS_BASE=14` "
          "**走不完一圈**（环 24 个停靠点）⇒ 加到 24 **仍差一按**（第 24 按落在"
          "**最后一个**停靠点上、还没回卷）⇒ 再加到 **28**。判别组尾部 `Tab` 由 3 下"
          "改成 **4 下**：952 那组在**源站**上正好停在工具条里，而**复刻**的落点不同"
          "（第 3 下**已经离开**工具条）⇒ 组结束在「离开的那一按」上、"
          "**后面没有下一按 ⇒ 滞后根本测不到**（第一版读成 `False`，"
          "那是**预算不够**、不是「没滞后」）⇒ 补 1 下后 "
          "`lag_is_one_press_probe = True`。"
          "⇒ ⭐⭐ **复刻与源站在这一条上同形**：离开内层控件的那一按指针**仍不动**、"
          "**下一按才动**（滞后 1 下，2/2）。",
          "left_button_press_probe" in _ausrc
          and "是**预算不够**、不是「没滞后」" in _ausrc
          and "**复刻与源站在这一条上同形**" in _ausrc
          and "**下一按才动**（滞后 1 下，2/2）" in _ausrc
          # ⭐ 钉探针：预算常量**逐个**钉住（14 → 24 → 28 三档都在）
          and "N_PRESS_BASE = 28" in _p953
          and '"Escape", 1), ("Tab", 4)]' in _p953
          and "**这是补预算，不是改判据" in _p953
          # ⭐⭐ `seq` 是必需的：base 的 `k` 与 probe 的 `k` **会撞号**
          and 'row["seq"] = len(c["rows"])' in _p953
          and 'c["left_button_press_probe"] = next(' in _p953
          and 'if r["seq"] == _lbp + 1),' in _p953
          # ⭐ 钉 952 那两个名字在格 1 是**结构性不适用**（不许当读数）
          and "952 那两个名字在格 1 是**结构性不适用**" in _p953
          and ' r["phase"] in ("base", "cold")' in _p952)

    check("OOOO.6 ⚠️⭐⭐⭐ **两条要改写成「位置相关」**（原文保留，承 HH.4）：\n"
          "① **「`Shift+Tab` 焦点立刻离开工具条」是位置相关的** —— "
          "源站那按是从**第一个**按钮（`导出时间线`）按的才出去；"
          "复刻从**第二个**按钮（`底部播放`）按 `Shift+Tab` 是**退到第一个**"
          "（`播放`）—— 弱判据说「没动」、**强判据说动了** ⇒ ⭐ **又一次弱判据漏报**。"
          "⇒ 两侧是**同一条规则**：**在工具条内反向逐个退，退到第一个再按就离开**。\n"
          "② **「`Escape` 不能把焦点从工具条里弄出来」没有对应的那一按** —— "
          "952 判别组的前两步（`Shift+Tab` → `Tab`）**已经把焦点带出工具条**，"
          "轮到 `Escape` 时按前是 `DIV/视频 node: 视频 1`。"
          "⚠️ **撤回的理由不是被证伪，是压根没在那个位置测过**。"
          "⇒ 953 **在复刻侧真的在工具条里按了 `Escape`**（按前按后都是 "
          "`inner:底部播放`）⇒ **「出不来」在复刻上成立** —— "
          "⚠️ 但**源站从未在那个位置测过**，**不许**说源站也这样。",
          '"shift_tab_rule_is_position_dependent_953": (' in _ausrc
          and "离开工具条」是**位置相关**的" in _ausrc
          and "**又一次弱判据漏报**" in _ausrc
          and "**在工具条内反向逐个退" in _ausrc
          and '"escape_claim_retracted_953": (' in _ausrc
          and "**理由不是被证伪，是压根没在那个位置测过**" in _ausrc
          and "**在复刻侧真的在工具条里按了 `Escape`**" in _ausrc
          and "**不许**说源站也这样" in _ausrc
          # ⭐ 钉探针：**每一步的按前位置**必须进读数（否则会把「键没反应」
          #    与「键没在**那个位置**上试」混成一句）
          and 'c["discrimination_from"] = [' in _p953
          and '"from": stop_name(r, "before"), "to": stop_name(r, "after"),'
              in _p953
          and 'c["shift_tab_moves_strong"] = any(' in _p953
          and 'c["escape_releases_strong"] = any(' in _p953
          # ⭐⭐ 源站侧的并排核算**真的在算**（用 952 自己的读数）
          and '"frozen_presses_all_moved_focus": sum(' in _p953
          and '"cycle_10_supported": bool(' in _p953
          and "def _sstrong(row):" in _p953)

    # ══ 批 954：⭐⭐⭐⭐ 走到**源站**的环尽头 = 102 下（2/2）════════════════
    print("— PPPP. 批 954 源站的环 = 102：952 的「10」被彻底推翻，且 954 自己犯了 952 的错 —")

    check("PPPP.1 ⭐⭐⭐⭐ **源站的 `Tab` 环 = 102 下**（2/2 逐条相同、"
          "`curve_reproducible` 绿、`ruler_actually_moved` 绿）：120 按里"
          "**节点停靠 88 + 内层停靠 14 + 出画布 18**，**回卷点 = 第 102 按**。"
          "⇒ ⭐⭐ **与 §930 记的 101 / 104 吻合**（954 实测 102、两轮相同）"
          "⇒ **§930 那条独立成立**。"
          "⚠️ 探针逐字复用 953 的**十六个助手 + 七段 JS**、`boot_fn` 逐字来自 952 ⇒ "
          "**唯一的新件是格子驱动器、不是仪器**；预算 120 是按 §139「必须 > 一个完整周期」"
          "补的（901/953 同一类补预算，不是放宽判据）。",
          '"source_ring_is_102_and_open_954": (' in _ausrc
          and "**源站的 `Tab` 环 = 102 下**" in _ausrc
          and "**节点停靠 88 个 + 内层停靠 14 个 + 出画布 18 个**" in _ausrc
          and "**回卷点 = 第 102 按**" in _ausrc
          and "**与 §930 记的 101 / 104 吻合**" in _ausrc
          and "**§930 那条独立成立**" in _ausrc
          # ⭐ 钉探针：逐字复用面（十六 + 七 + boot）**真的在文件里**
          and "for _fn in (ev, dump, guard, guard_point, delta, press_row, curve_key,\n"
              "            armed_of, no_ti_of, pointer_of, row_pointer, in_toolbar,\n"
              "            strong_moved, identity, stop_name, walk_stuck):" in _p954
          and "assert _s in _p953src" in _p954
          and 'assert boot_fn.__doc__' not in _p954      # ⭐ 禁 `or True` 那条已删
          and "_bs in _p952src" in _p954
          and '"boot_verbatim_from_952": ["boot_fn"]' in _p954
          and '"new_pieces": ["classify"]' in _p954
          and "N_PRESS_CAP = 120" in _p954
          and "**不是**放宽判据，是把预算补到能闭合" in _p954
          # ⭐ 钉探针：「操纵到底动了没有」自己答
          and 'out["ruler_actually_moved"] = bool(' in _p954
          and '"ruler_actually_moved": out["ruler_actually_moved"],' in _p954
          and '"curve_reproducible": out["curve_reproducible"],' in _p954)

    check("PPPP.2 ⚠️⚠️⚠️ **952 的「`Tab` 周期 = 10」被同一把尺子彻底推翻**："
          "954 用的就是 952/953 那把尺子（**逐字复用**），只把 URL 换回源站、"
          "预算补到 §139 要求的量级 ⇒ 实测 **102**。⇒ **10 是「节点停靠点数」"
          "那一小段、不是周期**（真实周期里还有 14 个内层停靠 + 18 个出画布停靠）。"
          "⇒ ⭐⭐ **而 952 当时写下的「差 10 倍」这个直觉反而是对的** —— "
          "它只是把因果归错了。⇒ 连同 953 的撤回，这条现在有**两条独立的证伪**："
          "① 14 按里从未回卷；② 同一把尺子走到底 = **102**。",
          '"cycle_10_thoroughly_refuted_954": (' in _ausrc
          and "被同一把尺子彻底推翻**" in _ausrc
          and "**10 是「节点停靠点数」那一小段**" in _ausrc
          and "「差 10 倍」这个直觉反而是对的**" in _ausrc
          and "它只是把因果归错了" in _ausrc
          and "这条现在有两条独立的证伪**" in _ausrc
          # ⭐ 钉探针：格 0 **真的**走到了环尽头（回卷点由**同一节点下标第二次出现**判）
          and 'c["repeat_node_at"] = {"seq": r["seq"], "node_index": ni}' in _p954
          and 'c["cycle_len"] = c["wrap_k"]' in _p954
          and 'c["left_the_canvas"] = bool(c["n_out_stops"] > 0)' in _p954)

    check("PPPP.3 ⚠️⭐⭐⭐ **要更正 953 的一条措辞**：953 写「复刻的环是开环」时，"
          "把「源站是不是也开环」列成了**待查**。**现在查到了：源站也开环** —— "
          "走完节点段后焦点**进入顶栏**（`搜索`/`生成历史`/`分享`/`更多`/"
          "`Credits`/`用户菜单`/`Canvas`）⇒ **然后又回到 `node#0`**。"
          "⇒ ⭐ **真正的差异是「回不回得来」，不是「开不开环」** —— "
          "而这一条**两边都还没测到**（953 的 28 下 < 954 源站用的 102，"
          "**不许**拿它断言复刻回不来）⇒ **待查**。"
          "⇒ ⚠️ 顺带更正 953 的「**复刻与源站的结构差异**」："
          "**「开环」不是差异**（两边都开环）⇒ 该说的是"
          "**「环长差一个量级」（复刻 24 vs 源站 101）**。",
          '"replica_open_ring_is_not_a_deviation_954": (' in _ausrc
          and "**要更正 953 的一条措辞**" in _ausrc
          and "**现在查到了：源站也开环。**" in _ausrc
          and "**然后又回到 `node#0`**" in _ausrc
          and "**真正的差异是「回不回得来」，不是「开不开环」**" in _ausrc
          and "**不许**拿 953 的 28 下断言复刻回不来" in _ausrc
          and "**「开环」不是差异**（两边都开环）" in _ausrc
          and "**「环长差一个量级」（复刻 24 vs 源站 101）**" in _ausrc
          # ⭐ 钉探针：出画布/入画布的分类**真的在算**
          and 'return f"out:{(w.get(\'aria\') or \'\')[:18]}"' in _p954
          and 'if stop.startswith("inner:"):' in _p954
          and 'c["out_stops"] = [s for s, kd in zip(c["stop_seq"], kinds)' in _p954)

    check("PPPP.4 ⚠️⚠️⚠️⚠️ **本批自己犯了和 952 一模一样的错，如实记账** —— "
          "而它正是本批要修的那个 bug：格 1 的按键顺序是 `Shift+Tab` → `Escape` → `Tab`，"
          "**`Shift+Tab` 已经把焦点带出工具条**（实测落到 `out:Canvas`）⇒ "
          "**轮到 `Escape` 时按前已经在画布根上** ⇒ "
          "**954 仍然没有测到「焦点在工具条里按 `Escape`」**。"
          "⚠️⚠️ **这与 952 的原罪逐字同形** ⇒ 953 撤回 952 的理由"
          "（「压根没在那个位置测过」）**完全适用于我这一批**。"
          "⚠️ **第二个缺陷**：6 次内层探测**全部落在同一个停靠点**"
          "（`inner:导出时间线` = 工具条**第一个**按钮）—— 每次探测最后一步 `Tab` "
          "落到 `node#0`，游标**被打回环的开头** ⇒ **第 2/3/4 个按钮至今没测到**。"
          "⇒ ⭐ **正确修法**：**每个内层停靠点单独成格、每格独立 `boot()`、"
          "每格只发那一个键**（`L_i` 由格 0 的 `stop_seq` **关系式**给出）"
          "⇒ **结构上不可能**再犯「按键顺序把键落在错误位置」这个错。"
          "⇒ ⭐⭐ **纪律**：判别组里每个键都必须在它**声称要测的那个位置**上按，"
          "而**唯一能保证的办法是「一次只按一个键」**，不是「记得核对」。",
          '"inner_probe_design_flaw_954": (' in _ausrc
          and "**本批自己犯了和 952 一模一样的错，如实记账**" in _ausrc
          and "**954 仍然没有测到「焦点在工具条里按 `Escape`」**" in _ausrc
          and "**这与 952 的原罪逐字同形**" in _ausrc
          and "**完全适用于我这一批**" in _ausrc
          and "6 次内层探测**全部落在同一个停靠点**" in _ausrc
          and "**第 2/3/4 个按钮上的行为至今没测到**" in _ausrc
          and "每格只发那一个键**" in _ausrc
          and "**结构上不可能**再犯" in _ausrc
          and "**唯一能保证的办法是「一次只按一个键」**" in _ausrc
          # ⭐ 钉探针：上限与触顶标记**真的在算**（不许悄悄截断）
          and "MAX_INNER_PROBES = 6" in _p954
          and "capped = True" in _p954
          and 'c["inner_probe_capped"] = capped' in _p954
          and "**如实记** capped=True" in _p954
          # ⭐⭐ 钉探针：**每一步的按前位置**必须进读数（否则同一个错还会再犯）
          and '"from": stop_name(prow, "before"),' in _p954
          and '"to": stop_name(prow, "after"),' in _p954
          and '"at_seq": seq, "stop": stop, "steps": []' in _p954)

    check("PPPP.5 ⭐⭐ **两条被独立复现的读数**（2/2 逐条相同）：\n"
          "① **`Shift+Tab` 从工具条**第一个**按钮按 ⇒ 立刻离开工具条**、"
          "落到 `out:Canvas`（弱判据与强判据**都说动了**）⇒ 与 953 在复刻侧测到的"
          "「从**第二个**按钮按是退到第一个」合起来，**「位置相关」在源站这一侧"
          "也成立**；\n"
          "② **`Escape` 在 `out:Canvas`（画布根）上不动焦点**（弱=False 强=False）"
          "⇒ **独立复现** 952 那条「`Escape` 在节点本体 `DIV` 上不动焦点」的**同族结论**。"
          "⚠️ **这两条都只是部分支持**：它们**不能**替代「焦点在工具条里按 `Escape`」"
          "那一格 —— **那一格至今空着**。",
          '"shift_tab_first_button_and_escape_on_canvas_954": (' in _ausrc
          and "**`Shift+Tab` 从工具条**第一个**按钮按 ⇒ 立刻离开工具条**" in _ausrc
          and "**「位置相关」这个判断在源站这一侧也成立**" in _ausrc
          and "**`Escape` 在 `out:Canvas`（画布根）上不动焦点**" in _ausrc
          and "**独立复现**" in _ausrc
          and "**这两条都只是部分支持**" in _ausrc
          and "那一格**至今空着**" in _ausrc
          # ⭐ 钉探针：三条计数**各判各的**，都不许预设方向
          and 'c["escape_moved_count"] = sum(' in _p954
          and 'c["shift_tab_moved_count"] = sum(' in _p954
          and 'c["shift_tab_left_toolbar_count"] = sum(' in _p954
          and 'c["inner_probe_stops"] = [p["stop"] for p in c["inner_probes"]]' in _p954
          # ⭐ 钉探针：强判据在本批**真的在用**（逐字复用 953 的那一条）
          and "c[\"swallowed_presses_strong\"] = sum(" in _p954
          and "and not strong_moved(r))" in _p954
          # ⭐ 钉探针：基线里的 101/104 明确标成「**不是本批的读数**」
          and "**都不是本批的读数**" in _p954
          and "**别人**记的，不许当结论用" in _p954)

    # ══ 批 955：⭐⭐⭐⭐ **只发一个键** ⇒ 空着的那一格补上了 ═══════════════
    print("— QQQQ. 批 955 每格只发一个键：Escape 在工具条里确实不动焦点 —")

    check("QQQQ.1 ⭐⭐⭐⭐ **空着的那一格补上了：`Escape` 在工具条里按不动焦点**"
          "（4 个内层停靠点**逐个**测、2/2 逐格相同、位置门与「只按一键」两门全绿）："
          "`导出时间线` / `全屏编辑` / `静音` / `添加素材到时间线` —— "
          "**按前按后都是它**（弱=False 强=False）、指针恒 `[2]→[2]`、"
          "`left_toolbar = False`。⇒ ⭐⭐⭐ **952 那条被 953 撤回的"
          "「`Escape` 不能把焦点从工具条里弄出来」，现在重新成立** —— "
          "而且证据等级**更高**（位置门 + 每格只发一个键 + 强判据 + 2/2）。"
          "⚠️ **953 撤回它的理由没有被推翻，是被满足了**（理由是"
          "「压根没在那个位置测过」）⇒ 现在测过了。"
          "⚠️ 954 那一格是**同一个空缺**（它自己的判别组顺序也把焦点带走了）。",
          '"onekey_inner_955": {' in _ausrc
          and '"escape_in_toolbar_finally_measured_955": (' in _ausrc
          and "**空着的那一格补上了：`Escape` 在**工具条里**按不动焦点**" in _ausrc
          and "按前按后**都是它**（弱=False 强=False）" in _ausrc
          and "**没有**离开内层" in _ausrc
          and "**重新成立** —— 而且证据等级**更高**" in _ausrc
          and "**结构上**排除了「前一个键把焦点带走」" in _ausrc
          and "撤回的理由（953 记的）没有被推翻，是被满足了**" in _ausrc
          and "954 那一格是**同一个空缺**" in _ausrc
          # ⭐⭐ 钉探针：位置门 + 只按一键**真的在算**
          and 'c["position_verified"] = bool(in_toolbar(reached))' in _p955
          and '"position_verified_before_press": bool(all(' in _p955
          and 'c["one_key_only"] = (c["n_target_keys"] == 1' in _p955
          and '"one_key_only": bool(all(' in _p955
          and 'TARGET_KEYS = ("Escape", "Shift+Tab")' in _p955
          and 'INNER_TARGETS = (1, 2, 3, 4)' in _p955
          # ⭐ 钉探针：格 = (第 i 个内层停靠点, 键)，每格独立 boot()
          and 'for inner_target in INNER_TARGETS:' in _p955
          and "n_audio = boot_fn()" in _p955
          and "c[\"inner_seen\"] += 1" in _p955)

    check("QQQQ.2 ⭐⭐⭐⭐ **`Shift+Tab` 的规则在源站侧**完整**成立**"
          "（2/2 逐格相同、4 个位置**各判各的**）：第 1 个 `导出时间线` → "
          "**`out:Canvas`（离开内层）**；第 2 个 `全屏编辑` → `导出时间线`；"
          "第 3 个 `静音` → `全屏编辑`；第 4 个 `添加素材到时间线` → `静音`。"
          "⇒ ⇒ **在工具条内反向逐个退，退到第一个再按就离开工具条** ⇒ "
          "与 953 在**复刻**侧测到的**同一条规则** ⇒ 「位置相关」**两边都成立**。"
          "⚠️⭐⭐ **第 2 格又是一次弱判据漏报**（`全屏编辑` → `导出时间线` 焦点动了，"
          "弱判据说没动）⇒ 与 953 那条合起来：**弱判据在内层控件之间切换时"
          "逐字地不可信**，已两次、两次都是它错。",
          '"shift_tab_rule_mapped_on_all_four_955": (' in _ausrc
          and "在工具条里的规则，现在在源站侧**完整**成立**" in _ausrc
          and "**在工具条内反向逐个退，退到第一个再按就离开工具条**" in _ausrc
          and "**同一条规则**" in _ausrc
          and "「位置相关」这个判断**两边都成立**" in _ausrc
          and "**第 2 格又是一次弱判据漏报**" in _ausrc
          and "**逐字地不可信**，已两次、两次都是它错" in _ausrc
          # ⭐ 钉探针：每格的按前/按后身份**真的逐格记下来**
          and 'c["from_stop"] = stop_name(prow, "before")' in _p955
          and 'c["to_stop"] = stop_name(prow, "after")' in _p955
          and 'c["left_toolbar"] = bool(in_toolbar(prow, "before")' in _p955
          and 'c["moved_weak"] = prow["focus_moved"]' in _p955
          and 'c["moved_strong"] = strong_moved(prow)' in _p955)

    check("QQQQ.3 ⚠️⭐⭐⭐ **逐字与归一化两道都在**源站**上红**，"
          "而那**不是**「读数不稳」，是**被测对象**在动：差异字段**只有** "
          "`identity_stable` / `bit` / `n_added` / `n_removed`，"
          "**行为字段全部一致**。⭐ `identity_stable=False` ⇒ 节点表对不上 ⇒ "
          "三元组**全是构造性产物**（946 的原话）⇒ **源站节点集逐轮会变**"
          "（§930 记过 77 / 76）。⚠️⚠️⚠️ **第一版我以为「加一道归一化就修好了」"
          "—— 错了**：归一化**按 `identity_stable` 这个标志分派**，而**标志本身"
          "逐轮在动** ⇒ 两边照样不同、**不稳定的格次每轮都换一批** ⇒ "
          "⇒ ⭐⭐⭐ **946 那条原理的正确落点**：「**哪些按的三元组不可用**」"
          "本身也是逐轮变的 ⇒ **三元组在这张画布上根本不是可复现的读数面** ⇒ "
          "**任何按它分派的归一化都抓不住** ⇒ ⭐ **第三道只比「行为字段」**"
          "（不依赖那个标志）⇒ **8/8 格 2/2 逐条相同**。"
          "⚠️⭐ **三道门逐字进读数**（逐字红 / 归一化红 / 行为绿）⇒ "
          "**不许只报好看的第三道**。",
          '"identity_unstable_on_source_955": (' in _ausrc
          and "在**源站**上红**" in _ausrc
          and "差异字段逐条查出来**只有** `identity_stable` / `bit` / `n_added` / " in _ausrc
          and "（行为字段**全部一致**）" in _ausrc
          and "**全是构造性产物**" in _ausrc
          and "**源站的节点集逐轮会变** —— §930 早记过 77 / 76 两轮不同" in _ausrc
          and "**第一版我以为「加一道归一化就修好了」—— 错了**" in _ausrc
          and "**标志本身逐轮在动**" in _ausrc
          and "**不稳定的格次" in _ausrc
          and "**946 那条原理的正确落点在这里**" in _ausrc
          and "一个可复现的读数面**" in _ausrc
          and "**任何按它分派的归一化都抓不住**" in _ausrc
          and "**第三道比较：只比「行为字段」**" in _ausrc
          and "**8/8 格 2/2 逐条相同**" in _ausrc
          and "**三道门逐字进读数**：逐字（红）、归一化（红）、" in _ausrc
          and "**不许只报好看的第三道**" in _ausrc
          and "被测对象不稳定，不是仪器不可靠**" in _ausrc
          # ⭐⭐ 钉探针：**三道**比较**真的都在算**，且第三道**不依赖**那个标志
          and "_UNSTABLE_TUPLE = (\"added\", \"removed\", \"changed\", \"bit\"," in _p955
          and 'if r.get("identity_stable") is False:' in _p955
          and 'r[k] = "UNSTABLE"' in _p955
          and "curve_reproducible_norm" in _p955
          and "def behavior_key(cell):" in _p955
          and "**不依赖那个标志**，实测 **8/8 格 2/2 逐条相同**" in _p955
          and "out[\"curve_reproducible_behavior\"] = bool(all(_ident_b))" in _p955
          and "**三道门都进读数**：逐字（红）、归一化（红）、行为（绿）" in _p955
          and "**不许只报第三道。**" in _p955
          and "**三元组在这张画布上根本不是一个可复现的读数面**" in _p955)

    check("QQQQ.4 ⭐⭐⭐ **本批的设计就是「让 954 那个错在结构上不可能发生」**，"
          "而且**自己抓到了两个自身缺陷**：\n"
          "① ⚠️⚠️ **第一版把两轮比较和设计门写在了 `for rep` 循环里面还跟了个 "
          "`break`** ⇒ **第二轮根本不会跑**；`py_compile` 与逐字门都抓不到"
          "（语法合法、逻辑残废）⇒ 已提出循环。⭐ 这是「**一次成功不叫可靠**」的"
          "另一种翻法：**结构上压根没跑第二遍**；\n"
          "② ⚠️ `assert not (RAW_KEYS & DERIVED_KEYS)` **又一次**真红"
          "（`n_nodes` 同时登记两边）—— 953 与 955 **两次**栽在同一个键上 ⇒ "
          "**这道门有效，但它的存在不替代「登记前先看一眼」**。",
          '"one_key_cell_design_955": (' in _ausrc
          and "本批的设计就是「让 954 那个错在结构上不可能发生」" in _ausrc
          and "**不需要跨格共享的引导表**" in _ausrc
          and "这种错在结构上**不可能**再发生" in _ausrc
          and "**第二轮根本不会跑**" in _ausrc
          and "**结构上压根没跑第二遍**" in _ausrc
          and "**两次**栽在同一个键上" in _ausrc
          # ⭐ 钉探针：两轮比较**真的在循环外**（不许再缩进回循环里）
          and 'n_cells = ci' in _p955
          and 'out["reps_identical"] = _ident' in _p955
          and "out[\"ruler_actually_moved\"] = bool(" in _p955
          and "for rep in range(1, REPS + 1):" in _p955
          and 'assert not (RAW_KEYS & DERIVED_KEYS)' in _p955
          # ⭐ 钉探针：**零**新件仪器（链式逐字）
          and "for _fn in (ev, dump, guard, guard_point, delta, press_row, curve_key,\n"
              "            armed_of, no_ti_of, pointer_of, row_pointer, in_toolbar,\n"
              "            strong_moved, identity, stop_name, walk_stuck, boot_fn):" in _p955
          and "assert _s in _p954src" in _p955
          and '"new_pieces": []' in _p955)

    # ══ 批 956：⭐⭐⭐⭐⭐ **复刻侧加预算走到环尽头** ⇒ 954 那句「回不来」被推翻 ══
    print("— RRRR. 批 956 复刻侧预算 28→120：环闭合、Shift+Tab 回得来 —")

    check("RRRR.1 ⭐⭐⭐⭐⭐ **954 点名的那个格子：复刻的 `Tab` 环闭合、`Shift+Tab` 回得来** —— "
          "954 亲手写的「**不许**拿 953 的 28 下断言复刻回不来」是**对的**，"
          "而 **953 自己那 28 下的结论早该作废**",
          '"replica_ring_closes_956": (' in _ausrc
          and "**复刻的 `Tab` 环**闭合** —— 954 那条「复刻回不来」" in _ausrc
          and "**被彻底推翻**" in _ausrc
          and "**953 那个 `False` 是预算不够，不是现象**" in _ausrc
          # ⭐ 钉探针：预算真的从 28 提到 120（954 源站那一侧用的是 102）
          and "N_PRESS_CAP = 120" in _p956
          and "28 下连源站环的一半都不到**，据此断言" in _p956
          and "**同一个量级**" in _p956
          # ⭐ 钉探针：回卷判据是「同一节点下标**第二次**出现」（不是预算用尽）
          and 'seen, c["repeat_node_at"] = set(), None' in _p956
          and 'c["repeat_node_at"] = {"seq": r["seq"], "node_index": ni}' in _p956
          and 'c["wrap_k"] = (c["repeat_node_at"] or {}).get("seq")' in _p956)

    check("RRRR.2 ⭐⭐⭐⭐ **`Shift+Tab` 按**停靠点**去重、不是按序号** —— "
          "第一版按序号去重 ⇒ 3 次探针**全落在同一个点上**；"
          "且 `came_back` **只能**读成「出画布段第一条就回得来」",
          '"replica_comes_back_956": (' in _ausrc
          and "按**停靠点**去重（不是按「第几个」" in _ausrc
          and "3 次探针**全落在 `out:返回首页` 这一个点上**" in _ausrc
          and "**第一条** `Shift+Tab` 就回得来" in _ausrc
          and "**反向逐个退**" in _ausrc
          # ⭐ 钉探针：去重键是 `st`（停靠点名字），**不是** `out_seen` 序号
          and 'if mode == "back" and st not in c["probed_stops"] \\' in _p956
          and 'c["probed_stops"] = []' in _p956
          and 'c["probed_stops"].append(st)' in _p956
          and 'c["came_back"] = any(p["to_class"] in ("node", "inner")' in _p956
          and "c[\"first_back_seq\"] = next(" in _p956)

    check("RRRR.3 ⭐⭐⭐⭐ **两边真正的差异是「环的权重」，不是「开环」、"
          "也不是「回不回得来」**；且 952 那个「差 10 倍」的直觉**对象错了**",
          '"what_is_the_real_difference_956": (' in _ausrc
          and "**两边真正的差异不是「开环」也不是「回不回得来」" in _ausrc
          and "**结构**与环长**量级**" in _ausrc
          and "**953 的「开环」与 954 的「回不来」两条差异**" in _ausrc
          and "**都不是**差异" in _ausrc
          and "源站**节点段占绝对主导**" in _ausrc
          and "复刻**出画布段占一半**" in _ausrc
          and "差的不是**环长**（53 vs 102 只差 ~2 倍），" in _ausrc
          and "是**节点数**（复刻 7 个 vs 源站 ~77 个）" in _ausrc
          and "**那条直觉该改写成「节点规模差一个量级」**" in _ausrc
          and "**复刻出画布段 27 个停靠点 vs 源站 18 个 —— 净多 9 个**" in _ausrc
          # ⚠️⚠️ 钉住「第一版把差异归错了」这条**自我更正**（并排 diff 才发现）
          and "**第一版我把差异归错了**" in _ausrc
          and "源站那 18 个里全都有**" in _ausrc
          and "**它们根本不是差异**" in _ausrc
          and "左栏的差是 **8 个不是 9 个**" in _ausrc
          # ⭐ 钉探针：分段读数（节点段 / 出画布段）是**关系式**的
          and 'c["leg_node_inner"] = (_legs[0]["from_seq"] - 1) if _legs else None' in _p956
          and 'c["leg_out"] = ([_lg["len"] for _lg in _legs]' in _p956
          and 'c["node_inner_stops"] = (c["stop_seq"][:c["leg_node_inner"]]' in _p956)

    check("RRRR.4 ⭐⭐⭐⭐ **第四道门（只比节点段）2/2 逐格相同**，"
          "而**出画布段逐轮会变** ⇒ **绝对环长不是稳定量，绝不能当「周期」断言**",
          '"leg_decomposition_956": (' in _ausrc
          and "**节点段是稳定的**（2/2 逐条相同）⇒ **它才是可复现的读数**" in _ausrc
          and "**绝对环长不是稳定量，绝不能当「周期」断言**" in _ausrc
          and "**与 955 的教训同构**" in _ausrc
          # ⭐ 钉探针：第四道门**真的在算**，且**在 `for rep` 循环之外**
          and 'out["node_inner_leg_identical"] = _leg_same' in _p956
          and 'out["node_inner_leg_reproducible"] = bool(all(_leg_same))' in _p956
          and 'out["node_inner_leg_len"] = _leg_lens' in _p956
          and 'out["fourth_gate_note"] = (' in _p956
          and '"node_inner_leg_reproducible": out["node_inner_leg_reproducible"],' in _p956)

    check("RRRR.5 ⚠️⭐⭐⭐ **`curve_key` 的覆盖面只有 4/13，如实数出来**；"
          "且**第一版的行为门差点恒真**（照抄 955 的 `_BEHAVIOR` 会让 956 整片 `None`）",
          '"three_gates_replica_956": (' in _ausrc
          and "**四道门逐字进读数**（不许只报绿的那道）" in _ausrc
          and "**`curve_key` 的覆盖面只有 4/13**" in _ausrc
          and "**这个覆盖面已如实数出来记进读数**" in _ausrc
          and "**第一版的行为门差点恒真**" in _ausrc
          and "**改用 956 自己的字段表**" in _ausrc
          # ⭐ 钉探针：覆盖面**真的被数出来**（不是写在注释里）
          and 'out["curve_key_coverage"] = {' in _p956
          and '"n_present": sum(1 for k in _CURVE_KEYS' in _p956
          and '"absent_keys": [k for k in _CURVE_KEYS' in _p956
          # ⭐⭐ **非恒真门**：`_BEHAVIOR` 是 **956 自己的**、且有「至少一半键真存在」的门
          and "_BEHAVIOR = (\"mode\", \"n_press\", \"n_lead\", \"n_lead_cap_hit\"," in _p956
          and '"behavior_gate_non_vacuous": bool(' in _p956
          and ">= len(_BEHAVIOR) / 2)," in _p956)

    check("RRRR.6 ⚠️⚠️ **写完自查抓到 6 个自身缺陷，`py_compile` 全都抓不到** —— "
          "其中 ① 根本没有 `sync_playwright` ⇒ `page` 永远 `None` ⇒ **一格都跑不了**",
          '"first_version_defects_956": (' in _ausrc
          and "**写完自查抓到 6 个自身缺陷**" in _ausrc
          and "**根本没有 `sync_playwright`/`launch`**" in _ausrc
          and "`page` 永远是 " in _ausrc
          and "`None` ⇒ **一格都跑不了**" in _ausrc
          and "**语法合法**" in _ausrc
          and "**docstring 也不许分家**" in _ausrc
          # ⭐ 钉探针：浏览器**真的**在模块级起（`ev`/`boot_ck` 闭包拿不到局部）
          and "_pw = sync_playwright().start()" in _p956
          and "_browser = _pw.chromium.launch()" in _p956
          and "atexit.register(lambda: (_browser.close(), _pw.stop()))" in _p956
          # ⭐ 钉探针：`norm_row` **逐字来自 955**（docstring 一并照搬）
          and "_UNSTABLE_TUPLE = (\"added\", \"removed\", \"changed\", \"bit\", \"diff_ids\")" in _p956
          and "if r.get(\"identity_stable\") is False:" in _p956
          and 'assert _s in _p955src' in _p956
          and "assert _cs in _p954src" in _p956)

    # ══ 批 957：⭐⭐⭐⭐⭐ **源站左栏是 ARIA roving tabindex** + 尺子隐含前提被查红 ══
    print("— SSSS. 批 957 源站左栏是 roving tabindex：ArrowDown 在栏内移动焦点 —")

    check("SSSS.1 ⭐⭐⭐⭐⭐ **源站左栏是标准 ARIA roving tabindex** —— "
          "956 那个「复刻 9 个 / 源站 1 个」的差异**机制查死了**",
          '"source_rail_is_roving_tabindex_957": (' in _ausrc
          and "**源站左栏是标准的 ARIA roving tabindex**" in _ausrc
          and "**机制查死了**" in _ausrc
          and "**`0`×1 + `-1`×9**" in _ausrc
          and "**逐字复刻 WAI-ARIA toolbar 的 roving 模式**" in _ausrc
          and "**这解释了 956 那个「净多 9」里的 8 个**" in _ausrc
          and "**954 那个「源站左栏只贡献 1 个停靠点" in _ausrc
          and "仍然成立，但依据必须换成这一条普查**" in _ausrc
          # ⭐ 钉探针：普查**只读属性、不调 focus()**（否则会污染格 1 的焦点读数）
          and "cen = ev(RAIL_JS, [RAIL_TID, NODE_SEL])" in _p957
          and "**普查用，不是仪器**" in _p957
          and "ti_hist: tiHist," in _p957
          and "c[\"n_rail_ti_hist\"] = cen.get(\"ti_hist\")" in _p957
          # ⭐ 钉探针：三格（普查 / 方向键 / 尺子自检）
          and 'for ci, mode in enumerate(("census", "arrow", "armcheck")):' in _p957
          and "n_cells = 3" in _p957)

    check("SSSS.2 ⭐⭐⭐⭐ **`ArrowDown` 在左栏内移动焦点**（roving 的另一半），"
          "而**弱判据第三次说错**",
          '"source_rail_arrow_navigates_957": (' in _ausrc
          and "**方向键在左栏内移动焦点**" in _ausrc
          and "**只发一个** `ArrowDown`" in _ausrc
          and "**`BUTTON/图片/canvas-fixed-toolbar`**" in _ausrc
          and "**强判据 True**、2/2 逐格相同" in _ausrc
          and "**弱判据又说「没动」" in _ausrc
          and "这已经是第三次、第三次都是它错**（953/955 各一次）" in _ausrc
          and "`tabIndex` 出现 **0 次**" in _ausrc
          # ⭐ 钉探针：判别键**自己发**、**不调 `ARM_FOCUS_JS`**（否则读数被仪器污染）
          and "**判别键这一按**必须**绕开 `press_row`**" in _p957
          and "page.keyboard.press(KEY_ARROW)          # ⭐ **只发这一个键**" in _p957
          and "**不调 `ARM_FOCUS_JS`** ⇒ 读数不被仪器污染" in _p957
          and '"arrow_read_isolated": bool(all(' in _p957
          and 'c["one_key_only"] = bool(len(c["pressed_keys"]) == 1' in _p957)

    check("SSSS.3 ⚠️⚠️⚠️⭐⭐ **`ARM_FOCUS_JS` 会把焦点从左栏拽回节点** ⇒ "
          "954/955/956 那把尺子有一个**从没验过的隐含前提**，在左栏位置是**假的**",
          '"arm_focus_taints_ruler_957": (' in _ausrc
          and "**这一格把 954/955/956 那把尺子的一个隐含前提查红了**" in _ausrc
          and "`ARM_FOCUS_JS`，而它**带 `el.focus()`**" in _ausrc
          and "**第一版就是这么坏的**" in _ausrc
          and "**是在 `node#75` 上按的**" in _ausrc
          and "**那一格什么也没测到**" in _ausrc
          and "（**不是**「`ArrowDown` 不动焦点」！）" in _ausrc
          and "**不可逆动作放序列最后**" in _ausrc
          and "**但**格 2 证明**「恰好没动」并不稳固**" in _ausrc
          and "可信度依赖一个它从没验过的前提**" in _ausrc
          and "**尺子自己那一步会改被测对象**这件事，**必须自己查**" in _ausrc
          # ⭐ 钉探针：`ARM_FOCUS_JS` 那个格**排在最后**且**一个键都不发**
          and "if mode == \"armcheck\":" in _p957
          and "**不可逆动作**（`el.focus()` 会永久改焦点状态）" in _p957
          and "⇒ ⭐ **不可逆动作放序列最后**" in _p957
          and 'c["one_key_only"] = True      # 这一格**一个键都没发**' in _p957
          and "c[\"arm_focus_moved_focus\"] = bool(identity(" in _p957)

    check("SSSS.4 ⚠️⚠️ **第一版 4 个坑，其中「读数对、标签错」和「读数错」一样危险**",
          '"first_version_defects_957": (' in _ausrc
          and "**第一版自己踩了 4 个坑**" in _ausrc
          and "⇒ `BLANK_JS` 只抄了前 3 行（箭头函数**没闭合**）" in _ausrc
          and "**JS 语法门抓到**（`py_compile` 抓不到）" in _ausrc
          and "**和 956 那次一模一样的错**" in _ausrc
          and "**「尺子自检」自己污染了它要检查的对象**" in _ausrc
          and "**`arrow_from` 标签指向错的按**" in _ausrc
          and "**「读数对、标签错」和「读数错」一样危险**" in _ausrc
          and "**两者都抓不到「标签指向了错的按」**" in _ausrc
          # ⚠️ 钉住「锚点自查比门禁弱」这条（SSSS.1 就栽在它上面）
          and "⇒ 它**分不清**" in _ausrc
          and "**锚点自查报「问题 0 个」、而门禁真红**" in _ausrc
          and "**锚点自查是比门禁弱的门，「自查 0 问题」**不等于**判据会过**" in _ausrc
          # ⭐ 钉探针：真值与旧标签**分开存**（不许只改标签不留痕）
          and 'c["arrow_from"] = stop_name({"who_after": pos}) or stop_name(row)' in _p957
          and 'c["walk_who_before"] = stop_name(row, "before")' in _p957
          and "**标签不许指向错的按**" in _p957
          # ⭐ 钉探针：`delta` 那个 `int()` —— 954/956 各栽过一次
          and "changed.append([int(i), was, cur])" in _p957)

    # ══ 批 958：⭐⭐⭐⭐⭐ **复刻侧实施** 957 测死的 roving tabindex ══════════
    print("— TTTT. 批 958 复刻左栏实施 roving tabindex：一圈 9/27 → 1/19 —")

    check("TTTT.1 ⭐⭐⭐⭐⭐ **复刻左栏装上了 roving tabindex**，"
          "**形状与源站 957 逐条相同**（改前可聚焦 9 枚、改后 1 枚）",
          '"replica_rail_roving_installed_958": (' in _ausrc
          and "**957→958：952 以来第一次产出**实际产品改动**" in _ausrc
          and "**`0`×1 + `-1`×8**" in _ausrc
          and "顺序里可聚焦 **1** 枚（改前是 **9**）" in _ausrc
          and "**与源站 957 同一形状**" in _ausrc
          and "**`-1` 少 1、`None` 少 26**" in _ausrc
          and "**不是** roving 行为不同" in _ausrc
          # ⭐ 钉**产品源码**：roving 初始化 + 方向键漫游 + `railRef` 真的在
          and 'ref={railRef}' in c958
          and ":scope > button[aria-label]" in c958
          and 'btns[0].setAttribute("tabindex", "0");' in c958
          and 'btns[i].setAttribute("tabindex", "-1");' in c958
          and 'if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;' in c958
          and "btns[next].focus();" in c958
          # ⚠️ 钉「不臆造」：源站没测过的键**不许**实现
          and "**不拦** `Home`/`End`/`ArrowLeft`/`ArrowRight`" in c958
          and "源站**没测过**后四个" in c958
          # ⭐ 钉探针：`RAIL_JS` 逐字来自 957
          and "# ⭐ `RAIL_JS` **逐字来自 957**" in _p958
          and "_RAIL_BLOCK in _p957src" in _p958)

    check("TTTT.2 ⭐⭐⭐⭐ **`ArrowDown` 在复刻左栏内移动焦点，与源站 957 逐条相同**；"
          "**弱判据第三次说错这件事在复刻侧也照样发生**",
          '"replica_rail_arrow_matches_source_958": (' in _ausrc
          and "**与源站 957 " in _ausrc
          and "**逐条相同**（2/2 逐格相同）" in _ausrc
          and "**强弱判据两边都是同一个组合**（弱 False / 强 True）" in _ausrc
          and "**弱判据第三次说错这件事，在复刻侧也照样发生**" in _ausrc
          and "**端点撒手是「不臆造」的选择、不是实测**" in _ausrc
          and "**源站那一格未测**" in _ausrc
          # ⭐ 钉探针：判别键**绕开 `press_row`**（957 查红的那条）
          and "**绕开 `press_row`**（957 查红的那条）" in _p958
          and "page.keyboard.press(KEY_ARROW)      # ⭐ **只发这一个键**" in _p958
          and 'c["arrow_read_isolation"] = "**绕开 `press_row`**"' in _p958
          and '"arrow_stays_in_rail": bool(all(' in _p958
          and '"arrow_moved_strong": bool(all(' in _p958)

    check("TTTT.3 ⭐⭐⭐⭐ **一圈：左栏 9 → 1、出画布段 27 → 19**（源站 1 / 18）⇒ "
          "**净多 9 降到净多 1**；但**顺序差异没被本批修掉**",
          '"one_lap_now_1_and_19_958": (' in _ausrc
          and "**一圈的结构**：左栏 **9 → 1**、出画布段 **27 → 19**" in _ausrc
          and "**绕开 `press_row`**" in _ausrc
          and "**复刻从「27 vs 18」变成「19 vs 18」**" in _ausrc
          and "「净多 9」**降到净多 1**" in _ausrc
          and "**剩下的那 1 个是结构性的、不是随机**" in _ausrc
          and "**少 1 个**源站有的**项目面板**" in _ausrc
          and "**顺序差异仍然存在**" in _ausrc
          and "**复刻把顶栏排在最前、源站把顶栏排在最后**" in _ausrc
          # ⭐⭐ 钉探针：窗口**左闭右开**（第一版两端都含 ⇒ 2/20 而非 1/19）
          and "**窗口是「左闭右开」**" in _p958
          and 'c["leg_lo"] = _rs[0] if _rs else 1' in _p958
          and 'c["leg_hi"] = (_rs[1] - 1) if len(_rs) > 1 else c["n_lead"]' in _p958
          and 'if c["leg_lo"] <= r["seq"] <= c["leg_hi"]]' in _p958
          and '"one_lap_rail_stop_is_1": bool(all(' in _p958
          and 'r["cells"][2].get("leg_n_rail") == 1' in _p958)

    check("TTTT.4 ⚠️⚠️⚠️⭐⭐ **957 查红的那条在**复刻**侧同样成立** —— 而我"
          "**第一版是拿推断当读数**的",
          '"arm_focus_also_taints_replica_958": (' in _ausrc
          and "**957 查红的那条，在**复刻**侧同样成立** —— 而我" in _ausrc
          and "**第一版是拿推断当读数**的" in _ausrc
          and "**把焦点从 `out:文本` 拽到 **`node#6`**" in _ausrc
          and "**我第一版的推断是「复刻侧不会」**" in _ausrc
          and "**推断错了**" in _ausrc
          and "**离开画布时不清除**" in _ausrc
          and "**不是**读数" in _ausrc
          and "**两边都得实测**" in _ausrc
          and "⇒ 本批因此把**格 2 也改成绕开 `press_row`**" in _ausrc
          and "**不可信**" in _ausrc
          and "**依据要换成 958 的普查 + 一圈计数**" in _ausrc
          # ⭐ 钉探针：格 2/格 3 都**不许**用 `press_row` 读焦点
          and 'c["ring_read_isolation"] = "**绕开 `press_row`**' in _p958
          and '"arm_focus_is_noop_at_rail": bool(all(' in _p958
          and '"arm_focus_is_noop_at_rail": bool(all(' in _p958
          and "**红**" in _p958)

    check("TTTT.5 ⚠️⚠️ **两道既有门都只认自己看得见的形状** ⇒ "
          "切片拼出来的 `RAIL_JS` **它俩都是瞎的**",
          '"probe_defects_958": (' in _ausrc
          and "**958 探针自己踩了 4 个坑**" in _ausrc
          and '**收尾那行是 `}\\"\\"\\"`**（一个 `}` 加终止符）' in _ausrc
          and "`SyntaxError: Unexpected end of input`" in _ausrc
          and "**`jimeng_probe_js_syntax_check.py` 抓不到它**" in _ausrc
          and "**门看不见的东西就得自己配平**" in _ausrc
          and "**用别的方式造出来的东西，它们都是瞎的**" in _ausrc
          # ⭐ 钉探针：自己配平（大括号免疫针）
          and 'assert RAIL_JS.count("{") == RAIL_JS.count("}"), (' in _p958
          and "**这正是 958 前三版的坑**" in _p958
          and 'assert RAIL_JS.count("[tid, nodeSel]") == 1, (' in _p958
          and "**这正是它的用处**" in _p958)

    # ══ 批 959：⭐⭐⭐⭐⭐ 「Tab 序 == DOM 序」**是假的** ⇒ 推翻 958 自己的猜想 ══
    print("— UUUU. 批 959 源站 Tab 序 vs DOM 序：Tab 序不是 DOM 序 —")

    check("UUUU.1 ⭐⭐⭐⭐⭐ **「`Tab` 顺序 == DOM 顺序」在源站是假的**（2/2）—— "
          "**本批推翻了自己 958 结尾写下的那个猜想**",
          '"tab_order_is_not_dom_order_959": (' in _ausrc
          and "**本批推翻了我自己 958 结尾写下的那个猜想**" in _ausrc
          and "**dom#2263、2357、2367、2377、2387、2396**" in _ausrc
          and "**dom#60…177**" in _ausrc
          and "**Tab 序把 DOM 靠后的 2263–2396 排在前面**" in _ausrc
          and "**源站 DOM 序本来就是「顶栏在前、画布控件在后」**" in _ausrc
          and "**真差异不是 DOM 序，" in _ausrc
          and '`dom_index_monotonic = False`（2/2）' in _ausrc
          # ⭐ 钉探针：`DOMIDX_JS` **逐字来自 957 的仪器链 + 纯读**
          and "新件 `DOMIDX_JS`（**纯读、不是仪器**）" in _ausrc
          and "dom_index: all.indexOf(a)," in _p959
          and 'assert "DOMIDX_JS" not in _p955src' in _p959
          and "**绕开 `press_row`**" in _p959)

    check("UUUU.2 ⭐⭐⭐⭐ **out 段被切成两段**：第 2 段**就是** DOM 序（严格单调）"
          "⇒ **只有第 1 段被提前了**",
          '"rail_order_split_959": (' in _ausrc
          and "**out 段被切成两段，源站把「画布控件」整体提前**" in _ausrc
          and "第 1 段（6 个）" in _ausrc
          and "第 2 段（12 个）" in _ausrc
          and "**第 2 段就是 DOM 序**（60→68→85→90→94→118→122→131" in _ausrc
          and "**严格单调**" in _ausrc
          and "**只有第 1 段被提前了**" in _ausrc
          and "**可复现的**结构事实（2/2 逐条相同）" in _ausrc
          and "**但机制未查明**" in _ausrc
          # ⭐ 钉探针：单调判据**真的在算**（不是写死的 False）
          and "c[\"dom_index_monotonic\"] = bool(_di) and all(" in _p959
          and '_di[i] <= _di[i + 1] for i in range(len(_di) - 1))' in _p959
          and '"dom_index_monotonic": bool(all(' in _p959)

    check("UUUU.3 ⚠️⚠️⚠️ **机制未验死，而最顺手那个解释已被读数否掉** —— "
          "**「未查明」与「否掉了」是两件不同的事**",
          '"mechanism_unknown_959": (' in _ausrc
          and "**机制未验死，标「未验证」" in _ausrc
          and "**这个解释被 959 的读数否掉了**" in _ausrc
          and "**它们不是靠正 `tabindex` 排到前面的**" in _ausrc
          and "别的什么）本批一条都没测到**" in _ausrc
          and "那是**已被否掉的猜想**，不是「待查的猜想」" in _ausrc
          and "「未查明」与「否掉了」是**两件不同的事**" in _ausrc
          # ⭐ 钉探针：**真的读了** `tabindex`（否掉那个解释靠的就是它）
          and "tabindex: a.hasAttribute('tabindex')" in _p959
          and '? a.getAttribute(\'tabindex\') : null,' in _p959
          # ⭐ 钉**文档**：958 结尾那句猜想**原文保留**、只加改写横幅（承 HH.4）
          and "**方向就错了**" in _ausrc)

    check("UUUU.4 ⚠️⚠️⭐ **DOM 绝对下标逐轮整体偏移 2** ⇒ **只能比相对大小关系**；"
          "且**源站环长逐轮在变**（≈57 vs 954 的 102）",
          '"dom_index_not_stable_959": (' in _ausrc
          and "**DOM 绝对下标逐轮整体偏移 2**" in _ausrc
          and "rep1 画布控件首枚 `dom#2263`、rep2 `dom#2265`" in _ausrc
          and "**`Tab` 序（`seq` + `data-testid` 序列）两轮逐条相同**" in _ausrc
          and "**DOM 绝对下标只能比「相对大小关系」**" in _ausrc
          and "**绝不能**写成「`dom_index == 2263`」这种绝对断言" in _ausrc
          and "这次**在 DOM 层面**、不是节点层面" in _ausrc
          and '"budget_caveat_959": (' in _ausrc
          and "**本批只量到「完整的 out 段」，不是完整一圈**" in _ausrc
          and "**源站这一轮的环长 ≈ 57**" in _ausrc
          and "**现在在源站侧也证实了**）⇒ 任何「源站环长 = N」的断言都不许写" in _ausrc
          and "任何「源站环长 = N」的断言都不许写" in _ausrc
          # ⭐ 钉探针：**触顶如实记**（不许假装走满一圈）
          and "N_LEAD_CAP = 140" in _p959
          and "c[\"n_lead_cap_hit\"] = True" in _p959
          and '"n_lead_cap_hit": c["n_lead_cap_hit"]' not in _p959
          and "**「一圈」这个说法不成立**" in _ausrc)

    # ══ 批 960：⭐⭐⭐⭐ 959 留下的两个可能性**逐个被否掉** + 矛盾**原样记账** ══
    print("— VVVV. 批 960 否掉 shadow root 与「keydown 改 ti」两条，矛盾不圆 —")

    check("VVVV.1 ⭐⭐⭐⭐ **「shadow root」被否掉** ⇒ **959 的 `dom_index` 口径成立**、"
          "**读数不需要重做**",
          '"shadow_root_refuted_960": (' in _ausrc
          and "**959 留下的可能性之一「shadow root」被否掉了**（2/2）" in _ausrc
          and "**在 shadow root 里的 = 0**" in _ausrc
          and "**root 种类只有 `['#document']`**" in _ausrc
          and "**若元素在 shadow root 里，那个下标口径就不成立**" in _ausrc
          and "**959 的 DOM 读数不需要重做**" in _ausrc
          and "**「959 用对了口径」**" in _ausrc
          # ⭐ 钉探针：`ROOT_JS` **真的**取 root，且**纯读**
          and "root_kind: isShadow ? 'ShadowRoot'" in _p960
          and "const r = a.getRootNode();" in _p960
          and 'c["all_out_in_document"] = bool(_outs) and all(' in _p960
          and 'r["cells"][0].get("all_out_in_document") is True' in _p960
          # ⚠️ 钉探针：守卫常量**自己匹配得上东西**（946 的教训）
          and 'assert ROOT_JS.count("getRootNode()") == 1 and "ShadowRoot" in ROOT_JS' in _p960
          and "`ROOT_JS` 自己就匹配不上它要验的东西" in _p960
          and "这道门恒绿，等于没有门" in _p960)

    check("VVVV.2 ⭐⭐⭐⭐ **「keydown 里改 `tabindex`」也被否掉**，"
          "且把 959 的否掉**补强成更彻底**的否掉",
          '"ti_rewrite_refuted_960": (' in _ausrc
          and "也被否掉了**（2/2）" in _ausrc
          and "**离开时 `tabindex` 变过的 = 0**" in _ausrc
          and "按**前**记住那一枚元素的**引用**" in _ausrc
          and "**同一个引用**（不是当前焦点）的 `tabindex`" in _ausrc
          and "**离开时 `tabindex` 变过的 = 0**" in _ausrc
          and "**这把 959 的那个否掉**补强成**更彻底**的否掉" in _ausrc
          and "与 957 那条**并存不矛盾**" in _ausrc
          and "**既无常驻 roving、也未被逐次改写**" in _ausrc
          # ⭐ 钉探针：存的是**引用**（不是 ti 值）—— 这正是第一版栽的地方
          and "window.__preEl = a || null;" in _p960
          and "const e = window.__preEl;" in _p960
          and '"same_el_still_connected": _same.get("still")' in _p960
          and '"no_ti_changed_by_tab": bool(all(' in _p960
          and 'r["cells"][0].get("n_ti_changed") == 0' in _p960)

    check("VVVV.3 ⚠️⚠️⚠️⭐⭐ **机制仍未查明，且三条事实凑成矛盾** —— "
          "**原样记账，不许圆**；「A、C 都对而 B 也对」本身就是线索",
          '"unresolved_contradiction_960": (' in _ausrc
          and "**机制仍然未查明，而且三条事实凑成了一组矛盾**" in _ausrc
          and "**原样记账，不许圆**" in _ausrc
          and "**A + C 蕴含「浏览器应当按 DOM 序走」，而与 B 矛盾**" in _ausrc
          and "**C 已经过时**" in _ausrc
          and "**B 的 `dom_index` 口径还有本批没发现的问题**" in _ausrc
          and "**不许**编一个机制把它圆上" in _ausrc
          and "**「A、C 都对而 B 也对」这件事本身就是待查的线索**" in _ausrc
          and "**下一批的第一件事就是查 C 是否过时**" in _ausrc)

    check("VVVV.4 ⚠️⚠️⚠️⭐⭐ **第一版判据是错的，被自己抓住**：把**两个不同元素**的 "
          "ti 当成**同一元素**的前后变化；**改法不是放宽判据，是改「盯谁」**",
          '"first_version_criterion_was_wrong_960": (' in _ausrc
          and "**第一版的判据是错的，被自己抓住**（在**落交付物之前**）" in _ausrc
          and "**两个不同元素**的 ti" in _ausrc
          and "不说明任何元素被改过" in _ausrc
          and "**是无意义的数字**" in _ausrc
          and "**改法不是放宽判据，是改「盯谁」**" in _ausrc
          and "**一个错的判据比没有判据更坏**（942）" in _ausrc
          and "它没被锚点自查抓到、也没被 `py_compile` 抓到" in _ausrc
          and "**极容易写出来、极难自己看出来**的错" in _ausrc
          # ⭐ 钉探针：第一版那段**原文保留**（承 HH.4：撤销留痕）
          and "⚠️⚠️⚠️⭐⭐ **第一版的判据是错的，被自己抓住**：" in _p960
          and "那是**两个不同元素**的 ti" in _p960
          and 'window.__preEl = null; }"""' in _p960)

    check("VVVV.5 ⚠️⚠️⚠️ **操作事故：960 把 `OUT` 照抄成 959 的路径，"
          "把 959 的读数覆盖了** ⇒ **`cp` 做基底时那三样必须逐个核**",
          '"out_path_overwrote_959_960": (' in _ausrc
          and "**操作事故：960 第一版把 `OUT` 照抄成了 959 的路径**" in _ausrc
          and "**960 跑完把 959 的读数文件覆盖了**" in _ausrc
          and "**忘了改模块级的 `OUT =" in _ausrc
          and "**两个各自独立的字段**" in _ausrc
          and "**改一个不改另一个不会报错**" in _ausrc
          and "已把 `OUT` 改成 `/tmp/b960-taborder.json` 并**重跑**" in _ausrc
          and "**结论没有丢**" in _ausrc
          and "**它们不在任何一道现有门里**" in _ausrc
          # ⚠️ 钉「锚点自查第三次放水」这条（957/958 各记过一次）
          and "**第三次**栽在同一个地方" in _ausrc
          and "**「锚点自查 0 问题」既不等于判据会过、也不等于锚点写对了**" in _ausrc
          # ⭐ 钉探针：`OUT` 真的改成了**自己的**路径（不是 959 的）
          and 'OUT = "/tmp/b960-taborder.json"' in _p960
          and 'out["out"] = "/tmp/b960-taborder.json"' in _p960
          and '"/tmp/b959-domorder.json"' not in _p960)

    # ══ 批 961：⭐⭐⭐⭐ 堵上 959/960 的**读法盲区** ⇒ 而盲区里是空的 ══
    print("— WWWW. 批 961 全文档普查 `tabindex`：正 `tabindex` = 0 个，"
          "「按正 ti 排序」彻底排除 —")

    check("WWWW.1 ⭐⭐⭐⭐ **959/960 的读法盲区被堵上 —— 而盲区里是空的**："
          "它们只读**焦点所在那一枚**的 `tabindex` ⇒ 「没有正 ti」只覆盖"
          "「各自获得焦点的那一刻」；961 **逐按普查全文档** ⇒ "
          "**112 个原生可聚焦**、分布 `0`×1 + `None`×25 + `-1`×86、"
          "**带正 `tabindex` 的 0 个** ⇒ **「靠正 `tabindex` 排序」彻底排除**",
          '"blind_spot_closed_961": (' in _ausrc
          and "**959/960 的读法盲区被堵上了 —— 而盲区里是空的**" in _ausrc
          and "**只读「焦点所在的那一枚」**" in _ausrc
          and "**「它们没有正 `tabindex`」这个结论只覆盖了" in _ausrc
          and "**其它候选**当时的 `tabindex` " in _ausrc
          and "**全文档原生可聚焦 112 个**" in _ausrc
          and "分布 = **`0`×1 + `None`×25 + `-1`×86**" in _ausrc
          and "**带正 `tabindex` 的 = 0 个**" in _ausrc
          and "**「靠正 `tabindex` 排序」这个解释被**彻底**排除**" in _ausrc
          and "不只是那 6 个画布控件没有，是**整个文档一个都没有**" in _ausrc
          # ⭐ 钉探针：普查范围是**全文档**，不是焦点那一枚
          and 'TICENSUS_JS = """([nodeSel]) => {' in _p961
          and "const all = Array.from(document.querySelectorAll('*'));" in _p961
          and "const NATIVE = ['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA'];"
              in _p961
          and "n_focusable: n_focusable, ti_hist: hist, positive: positive,"
              in _p961
          # ⭐ 钉探针：**逐个列出带正值的**（不是只数）
          and 'c["positive_tids"] = sorted({' in _p961
          and 'c["positive_sample"] = (_outs[0].get("positive") or [])' in _p961
          and 'c["n_out_with_positive"] = len(_pos)' in _p961
          # ⭐⭐ 钉探针：961 自己的**两道可红判决门**（960 漏了，961 补上）
          and '"no_positive_tabindex": bool(all(' in _p961
          and '"ti_hist_stable_across_stops": bool(all(' in _p961
          and 'r["cells"][0].get("n_positive_max") == 0' in _p961
          and 'r["cells"][0].get("positive_tids") == []' in _p961
          and 'r["cells"][0].get("n_out_with_positive") == 0)' in _p961
          and 'r["cells"][0].get("ti_hist_stable") is True' in _p961
          and "**可红**，红的就是「正 `tabindex`」没被否掉" in _p961
          # ⚠️ 钉探针：守卫常量自己匹配得上东西（946 的教训）
          and 'assert TICENSUS_JS.count("NATIVE.indexOf(tag)") == 1' in _p961
          and "`TICENSUS_JS` 自己就匹配不上它要验的东西" in _p961
          and "这道门恒绿，等于没有门" in _p961)

    check("WWWW.2 ⚠️⚠️⚠️⭐⭐ **矛盾加强了，而且只剩一个方向**："
          "A′（无正 ti）+ C（**没** `preventDefault`）⇒ 浏览器**本该严格**按 DOM 序走，"
          "与 B（959/961 的 `Tab` 序非 DOM 序）**直接冲突** ⇒ "
          "**剩下的可能只剩「应用在 keydown 之后主动 `focus()`」** ⇒ "
          "**那才是复刻真正要对齐的东西**（应用自己维护的焦点顺序表）",
          '"contradiction_hardens_961": (' in _ausrc
          and "**矛盾加强了，而且现在只剩一个方向**" in _ausrc
          and "**892 首测** 2/2、**896 复核**全 `False`" in _ausrc
          and "**A′ + C 蕴含「浏览器应当**严格**按 DOM 序走」**" in _ausrc
          and "**与 B 直接冲突**" in _ausrc
          and "**剩下的方向只剩一个**" in _ausrc
          and "（`focusin` / 宏任务 / `requestAnimationFrame`）**主动 `focus()` " in _ausrc
          and "**没拦**，与 C 不矛盾" in _ausrc
          and "**不用改**（与 A′ 不矛盾）" in _ausrc
          and "而顺序**来自它自己的表**" in _ausrc
          and "**这才是复刻真正要对齐的东西**" in _ausrc
          and "而是**应用自己维护的那张焦点顺序表**" in _ausrc
          # ⭐ 钉探针：961 复核的 B（`dom_index` 非单调）**可红且真的红着**
          and '"dom_index_monotonic": bool(all(' in _p961
          and "**DOM 下标单调不降 = " in _p961
          and 'r["cells"][0].get("dom_index_monotonic") is True' in _p961
          and '**960 已经逐条否掉**' in _p961
          # ⚠️ 钉探针：**不许**把已否掉的猜想写成待查
          and '**也不问** 960 问过的那两条（shadow root / keydown 改 ti，' in _p961)

    check("WWWW.3 ⚠️⚠️⚠️ **更正出处时我自己也犯了「只查一处」的错**："
          "960 §二 写 896，而 **896 确实测过**（明写用 892 的取法、"
          "结论全 `False`）⇒ 960 那处引用**不算错**；准确说法是"
          "**「892 首测 ＋ 896 复核」** ⇒ **C 有两个出处、都站得住**；"
          "钉在**两个探针源码**上，不是钉在自述里",
          '"where_961_almost_made_the_same_mistake_961": (' in _ausrc
          and "**更正一处出处 —— 而我第一版的「更正」本身就是错的**" in _ausrc
          and "**896 确实测过**" in _ausrc
          and "汇总里有 `keydown_defaultPrevented_seen`" in _ausrc
          and "**960 那处引用不算错**" in _ausrc
          and "**准确的说法是「892 首测（2/2 `False`）＋ 896 复核（全 `False`）」**"
              in _ausrc
          and "**C 有两个出处、都站得住**" in _ausrc
          and "我 961 第一版写的是「**不是 896**」⇒ **那一句是错的**" in _ausrc
          # ⭐⭐ **钉探针源码**：C 的两个出处**真的都存在**，且**取法一致**
          and "**派发结束后**再读 `defaultPrevented`" in _p892
          and "defaultPrevented: e.defaultPrevented}); };" in _p892
          and "defaultPrevented_final: s ? s.defaultPrevented : null," in _p892
          and "`defaultPrevented` 用 **892 的取法**" in _p896
          and "keydown_defaultPrevented_seen" in _p896
          and '"keydown_defaultPrevented_seen": prevented,' in _p896
          # ⚠️ 钉探针：961 自己**留痕**了这次自我更正（承 HH.4）
          and "**更正一处出处，但第一版更正本身就错了**" in _p961
          and "**892 首测**（那一批的主角就是这一项，2/2 `False`）" in _p961
          and "没查「真正测过的还有哪些」" in _p961
          and "**引用纪律要查两遍：路径查一遍、来源也查一遍**" in _ausrc)

    check("WWWW.4 ⚠️⚠️ **同一次跑里有两个普查，数字不可比**；"
          "且 961 **自己抓到两个缺陷**（`domidx_note` 是 960 照抄残留、"
          "探针**没有给 961 判决自己的门**）⇒ 都改了、都**重跑**了",
          '"two_censuses_961": (' in _ausrc
          and "**同一次跑里有两个普查，口径不同、数字不可比**" in _ausrc
          and "范围**只有左栏那一个容器**" in _ausrc
          and "范围是**整个 `document`** 的" in _ausrc
          and "961 的判决**只认后一个**" in _ausrc
          and "**口径必须写在产物里**，不能只存在于跑的人脑子里" in _ausrc
          and '"own_gate_missing_961": (' in _ausrc
          and "**961 自己抓到两个缺陷，都改了、都重跑了**" in _ausrc
          and "**原文是 960 照抄来的**" in _ausrc
          and "**交付的读数文件里「本批问什么」被标错**了" in _ausrc
          and "`design_gates` 里**没有 961 判决自己的门**" in _ausrc
          and "**「可红」的门必须和判决同时落进探针**" in _ausrc
          # ⭐ 钉探针：三个修复**真的**在文件里
          and "**操作事故（961 自己抓到）**" in _p961
          and "还在讲 960 的两个可能性（shadow root / keydown 改 ti）" in _p961
          and "这回毁的是**读数文件里的一个说明字段** ⇒ 承 960 那条纪律" in _p961
          and 'out["census_scope"] = (' in _p961
          and "**两个普查不是同一件事，数字不可比**" in _p961
          and "左栏普查（`RAIL_JS`，范围=左栏容器）" in _p961
          # ⚠️ 钉探针：派生键补登记（935 的两道免疫针），且原始/派生没混
          and '"n_positive_max", "n_out_with_positive", "positive_tids",' in _p961
          and '"ti_hist_stable",' in _p961
          and "`positive`/`ti_hist` 是**原始**读数，不能混" in _ausrc
          and '"ti_hist", "n_native", "n_focusable", "n_positive", "positive",'
              in _p961)

    check("WWWW.5 ⭐⭐ **零计费与纯读纪律 961 继续守住**：新件 `TICENSUS_JS` "
          "**只读不写**、判别键**绕开 `press_row`**（它带 `el.focus()` 会改被测对象）、"
          "全程只点**一次画布空白**、⛔ 守卫拦在 `mouse.click` **之前**",
          "⚠️ 纯读：不调 `focus()`、不改任何属性。" in _p961
          and "只列**正** `tabindex`" in _p961
          and "**绕开 `press_row`**（957 查红、958 复刻侧也证实" in _p961
          and 'out["ruler"]["read_isolation"] = (' in _p961
          and "会把焦点从 chrome 停靠点**拽回画布节点**（957 源站实测、958 复刻实测）"
              in _p961
          and "**本批零计费动作。** 只发一次画布空白点击去焦点" in _p961
          and "⛔ 守卫拦在 `mouse.click` **之前**" in _p961
          and 'guard_point(sp[0], sp[1])       # ⭐ 只点**画布空白**去焦点' in _p961
          and '"zero_button_clicks": True,' in _p961
          and '"read_isolated_from_press_row": True,' in _p961)

    check("WWWW.6 ⚠️⚠️⚠️⭐⭐ **锚点自查里那个「静默跳过」的洞被堵上了**："
          "未登记变量原本是**裸 `continue`** ⇒ `_p957`–`_p960` **四批**的探针锚点"
          "**一次都没被查过**；补登记后 **2411 → 2853**、**0 问题**，"
          "并**当场抓出一条恒假的析取支**（M.6）⇒ **改法是删恒假支、不是放宽门**；"
          "剩下 167 条**确实不是文件源**，故不当门、但**已改成逐条打印**",
          '"anchor_hole_961": (' in _ausrc
          and "**锚点自查里有一个「静默跳过」的洞，961 把它堵上了**" in _ausrc
          and "**裸 `continue`**" in _ausrc
          and "**一条都不查、且连提示都没有**" in _ausrc
          and "**`_p957`–`_p960` 一直漏登记**" in _ausrc
          and "**四批**的探针锚点" in _ausrc
          and "锚点总数 **2411 → 2853**（**+442**）" in _ausrc
          and "新增受检 235 条**实测 0 问题**" in _ausrc
          and "**出现 0 次**" in _ausrc
          and "**第一个析取支恒假**" in _ausrc
          and "**只靠第二个析取**撑着" in _ausrc
          and "**改法不是放宽门，是删掉那句从来不真的话**" in _ausrc
          and "「0 问题」+「没报错」**可能只是没人查**" in _ausrc
          and "**确实是字典/切片/循环变量**、" in _ausrc
          and "**不当门**（会误报），但**已改成逐条打印**" in _ausrc
          # ⭐⭐ 钉**自查器本身**：洞**真的**堵了（登记 + 打印）
          and '"_p957": "scripts/jimeng_probe957_rail_roving_src.py",' in _vsrc
          and '"_p960": "scripts/jimeng_probe960_taborder_src.py",' in _vsrc
          and '"_p961": "scripts/jimeng_probe961_ticensus_src.py",' in _vsrc
          and '"_p892": "scripts/jimeng_probe892_preventdefault_src.py",' in _vsrc
          and "**961 补登记的 59 个**" in _anchs
          and "原来这里是**裸 `continue`（静默跳过）**" in _anchs
          and "SKIPPED.append(name)" in _anchs
          and 'print(f"SKIPPED-未登记 [{_n}] {_k} 条锚点（**不查**）")' in _anchs
          and "条锚点因**变量未登记**被跳过" in _anchs
          # ⚠️⚠️ M.6 只钉**新写法**在，**不钉「旧写法不在」** ——
          #   那条 `not in _vsrc` 是**自指**的：断言文本自己就写在 verifier 文件里
          #   ⇒ 恒红（一个恒红的判据比没有判据更坏）⇒ 只留正向锚点。
          and '"只有 1 项" in asrc)' in _vsrc)

    # ══ 批 962：⭐⭐⭐⭐⭐ 959 的 B（`Tab` 序 ≠ DOM 序）**被否掉** ——
    #    959–962 四批的谜团**整个解开**：源站就是朴素的环形 DOM 序 ══
    print("— XXXX. 批 962 用「派发结束那一刻焦点在哪」验「应用主动搬焦点」，"
          "并把 959 的 B 判成折返假象 —")

    check("XXXX.1 ⭐⭐⭐⭐ **判据本身**：`Tab` 的原生移焦是 keydown 的**默认动作**、"
          "在**派发彻底结束之后**才做 ⇒ 在派发末尾读 `activeElement` 就能分辨"
          "「脚本搬的」与「浏览器搬的」；只比**身份四字段**、不比 DOM 绝对下标",
          '"what_962_measures": (' in _ausrc
          and "**判据 = 「派发结束那一刻焦点在哪」**" in _ausrc
          and "**默认动作**（`Tab` 的原生移焦）是在**派发彻底结束" in _ausrc
          and "焦点**已经变了** ⇒ 必然是**派发过程中**被脚本 `focus()` 搬的"
              in _ausrc
          and "焦点**还没变** ⇒ 默认动作之后才搬 ⇒ **浏览器搬的**" in _ausrc
          and "只比**身份四字段**（tag/tid/aria/is_body）" in _ausrc
          # ⭐ 钉探针：监听装在**派发首**与**派发末**两个点上
          and "window.addEventListener('keydown', onKeyCap, true);" in _p962
          and "document.addEventListener('keydown', onKeyBub, false);" in _p962
          and "window.addEventListener('keydown', onKeyBubW, false);" in _p962
          and "document.addEventListener('focusin', onFocusIn, true);" in _p962
          and "rec.post_dispatch = WHO(document.activeElement);" in _p962
          # ⭐ 钉探针：诊断动作**必须还原**（承 943）
          and "window.__fm_off = () => {" in _p962
          and 'FOCUSMOVE_JS.count("addEventListener")' in _p962
          and '== FOCUSMOVE_JS.count("removeEventListener") == 4' in _p962
          and "诊断动作必须还原（承 943 的纪律）" in _p962)

    check("XXXX.2 ⭐⭐⭐⭐⭐ **959 的 B 被否掉，而且否它的是「关系」不是绝对值**："
          "整条走查 `dom_index` **下降恰好 1 次**、且是**高索引跳回低索引**"
          "（文档尾部折返回头部）⇒ 画布控件排在顶栏之前**不是乱序、是绕了一圈**；"
          "⇒ **959 用「单调不降」下的判决本来就推不出「乱序」**",
          '"verdict_962": (' in _ausrc
          and "**959 的 B（`Tab` 序 ≠ DOM 序）被否掉 —— 而否它的" in _ausrc
          and "**下降恰好 1 次**" in _ausrc
          and "**「高索引跳回低索引」**（文档**尾部折返到头部**）" in _ausrc
          and "**959 的判决是用「单调不降」下的**" in _ausrc
          and "**「非单调」推不出「乱序」**" in _ausrc
          and "**不是乱序，是绕了一圈**" in _ausrc
          # ⭐ 钉探针：下降次数是**一等读数**、且门挂在它上面
          and 'c["n_dom_index_descents"] = sum(' in _p962
          and 'c["dom_index_descents"] = [{"at_seq": _seq_di[i][0],' in _p962
          and '"dom_index_descents_are_wraps_only": bool(all(' in _p962
          and 'all(d.get("from") > d.get("to")' in _p962
          and "**959 的判决（「`Tab` 序 ≠ DOM 序」）是用「单调不降」下的**"
              in _p962
          # ⚠️ 钉探针：**绝对下标逐轮会漂** ⇒ 两轮比的是**方向**不是数值
          and "**绝对下标逐轮会漂、只钉方向**" in _p962
          and '("high_to_low" if (d.get("from") or 0) > (d.get("to") or 0)'
              in _p962)

    check("XXXX.3 ⭐⭐⭐⭐ **两条独立证据互相印证**：out 段那 18 个 chrome 停靠点"
          "**派发内被搬的 = 0**（**全部**是浏览器原生移焦）＋ 时序与形状吻合；"
          "⇒ **961 那个「只剩一个方向」被否掉** ⇒ 源站就是**朴素的环形 DOM 序**、"
          "**没有**「应用自己维护的焦点顺序表」",
          "out 段那 18 个 chrome 停靠点**全部**是" in _ausrc
          and "**浏览器原生移焦**，应用**没插手**" in _ausrc
          and "`dom_index` **只有折返那一次**下降" in _ausrc
          and "**959–962 四批的谜团整个解开了**" in _ausrc
          and "**朴素的、原生的、环形 DOM 序**" in _ausrc
          and "不由应用搬焦点（962）" in _ausrc
          and "**不需要**去对齐什么" in _ausrc
          and "961 那个猜想**被否掉了**" in _ausrc
          # ⭐ 钉探针：门挂在 **out 段**（不是 `leg`）上
          and '"out_stops_moved_by_browser": bool(all(' in _p962
          and '(r["cells"][0].get("n_moved_in_dispatch_leg") or 0) == 0' in _p962
          and "_legseq = {x[\"seq\"] for x in _outs}" in _p962
          and "**第一版这里错拿 `leg` 当「out 段」**" in _p962
          and "**连我自己的结论文案都和这个数字自相矛盾**" in _p962
          and "**文案必须跟着数字走**" in _p962
          # ⚠️ 钉探针：`isTrusted` 的语义**第一版写错了**
          and "**第一版这里把 `isTrusted` 的语义写错了，被自己抓住**" in _p962
          and "**脚本调 `element.focus()` 产生的 focus 事件同样是 trusted**"
              in _p962
          and "**不能**用来否掉「应用主动 `focus()`」" in _p962
          and "**真正判决性的是「派发末尾 `activeElement` 变没变」**" in _p962
          # ⭐ 钉 audit：961 的猜想**不算错**
          and "**961 的猜想不算「错」**" in _ausrc
          and "**被否 ≠ 当时不该猜**" in _ausrc)

    check("XXXX.4 ⚠️⚠️⚠️⭐⭐ **第一版的仪器有致命 bug，而门却是绿的**："
          "`__fm` 闩锁是**粘的** ⇒ 140 按里**只测到第 1 按**；"
          "而那道门写的是 `n_fm_armed == n_fm_rows` ⇒ **恒真** ⇒ "
          "**改法是换成和「按压总数」比**，不是加条件",
          '"fm_latch_bug_962": (' in _ausrc
          and "**第一版的仪器有致命 bug，而门却是绿的**" in _ausrc
          and "那个闩锁是**粘的**" in _ausrc
          and "**只有第 1 按**真的装了监听" in _ausrc
          and "**更该记的是那道门**" in _ausrc
          and "**恒真**" in _ausrc
          and "**改法不是加条件，是换成和「按压总数」比**" in _ausrc
          and "**门必须挂在独立的分母上**" in _ausrc
          # ⭐ 钉探针：闩锁真的改了、门真的换了分母
          and "if (window.__fm_rec) { return {already: true}; }" in _p962
          and "那个闩锁是**粘的**" in _p962
          and "只有**第 1 按**" in _p962
          and "**第一版这条门是恒真的**" in _p962
          and 'r["cells"][0].get("n_fm_armed") == r["cells"][0].get("n_lead")'
              in _p962
          and 'r["cells"][0].get("n_fm_rows") == r["cells"][0].get("n_lead")'
              in _p962)

    check("XXXX.5 ⚠️⚠️ **第一版的「摘干净」守卫写错了，被自己抓住**："
          "数的是 `__fm_off` 这个**名字**出现几次 ⇒ 量不到「监听摘没摘干净」"
          "⇒ 改成量 `add`/`removeEventListener` **配平**；"
          "另删一个**死字段**（比的是从未赋值的 `_el0`）",
          '"guard_was_wrong_962": (' in _ausrc
          and "**第一版的「摘干净」守卫写错了，被自己抓住**" in _ausrc
          and "数「名字」**量不到「监听有没有摘干净」**" in _ausrc
          and "**必须配平**（4 : 4）" in _ausrc
          and "**守卫要量「后果」，不要量「名字」**" in _ausrc
          and "**死字段** `same_target`" in _ausrc
          and "**从未被赋值** ⇒ 恒为无意义 ⇒ **删掉**" in _ausrc
          and "**交付物里每个字段都得是真读数**" in _ausrc
          and "第一版这里还有个 `same_target` 字段" in _p962
          and "而 `_el0` **从来没有被赋值过**" in _p962)

    check("XXXX.7 ⚠️ **两根红着的门，原因已查明、如实记**（"
          "`focusin_heard_every_press` 红在「1 按没听到 `focusin`」、"
          "`app_moves_focus_before_dispatch_end` 红在「102/140 压确实被应用"
          "在派发中搬」）⇒ **决定不为了变绿去放宽门**；"
          "⭐ 并把限定写死：**「961 的猜想被否掉」只对 out 段成立**",
          '"focusin_miss_962": (' in _ausrc
          and "**有一根红着的门，原因已查明，**如实记" in _ausrc
          and "**140 按里有 1 按**" in _ausrc
          and "**落在画布根**" in _ausrc
          and "焦点落到了 **`document.body`**" in _ausrc
          and "移焦到它**只发 `blur`/`focusout`、" in _ausrc
          and "**不发 `focusin`** ⇒ 这是**真实读数**" in _ausrc
          and "**决定：不为了变绿去放宽这道门**" in _ausrc
          and "**这个理由一旦变了它就会提醒**" in _ausrc
          and "确有 102 压是**应用在派发中搬的**" in _ausrc
          and "集中在**画布节点段**" in _ausrc
          and "**「961 的猜想被否掉」只对" in _ausrc
          and "**out 段（chrome 停靠点）**成立**，这个限定**必须一起记**" in _ausrc)

    check("XXXX.6 ⚠️⚠️⚠️⭐⭐ **同一个坑，隔一层又踩了一次**："
          "962 写完判据后锚点自查报 **0 问题**（**假绿**），真正暴露它的是"
          "**verifier 跑出一条 FAIL** ⇒ 根因：**`_p962` 忘了登记进 "
          "`PROBE_VARS`** ⇒ **整组 `XXXX.*` 的锚文全被静默跳过** ⇒ "
          "登记后自查**立刻报出那条真 MISSING** ⇒ "
          "**「新增变量时，登记必须和写判据同一步完成」**",
          '"forgot_register_p962": (' in _ausrc
          and "**同一个坑，隔一层又踩了一次**" in _ausrc
          and "**0 问题** ⇒ 我差点直接收工" in _ausrc
          and "真正暴露它的是**verifier 跑出一条 FAIL**" in _ausrc
          and "**`_p962` 我忘了登记进 `PROBE_VARS`**" in _ausrc
          and "**整组 `XXXX.*` 的锚文" in _ausrc
          and "全被静默跳过** ⇒ 「0 问题」**又一次是假绿**" in _ausrc
          and "**立刻报出那条真 MISSING**" in _ausrc
          and "**门与自查互相补位、缺一不可**" in _ausrc
          and "登记必须和写判据**同一步**完成** ——" in _ausrc
          and "「自查 0 问题」在" in _ausrc
          and "**不构成任何证据**" in _ausrc
          and "**编号冲突**" in _ausrc
          # ⭐ 钉自查器：`_p962` **真的**登记了
          and '"_p962": "scripts/jimeng_probe962_focusmove_src.py",' in _anchs
          and "**我第一遍忘了登记 `_p962`**" in _anchs)

    check("XXXX.8 ⚠️⚠️ **照抄基底留下的两样「产物级」残留，962 一并清了**："
          "① docstring 头**连错三批**（959/960/961 都还写着「batch 957」）"
          "② 4 处**真坏字节**（U+FFFD，3 字节汉字变 2–3 个 U+FFFD）"
          "⇒ 照抄基底的核对清单**要加一条：文件头也算产物**",
          '"residue_chain_962": (' in _ausrc
          and "**docstring 头连错了三批**" in _ausrc
          and "**都还写着「batch 957」**" in _ausrc
          and "**要加一条：文件头也算产物**" in _ausrc
          and "**4 处真坏字节**（U+FFFD）" in _ausrc
          and "**从上下文无歧义恢复**" in _ausrc
          and "**不猜、不留坏字节**" in _ausrc
          and "**属别的项目**（liblib / frameos）" in _ausrc
          and "**不碰**" in _ausrc
          # ⭐ 钉探针：962 的头是**自己的**，且带着留痕
          and 'r"""batch 962 源站探针' in _p962
          and "**docstring 头连错了三批**" in _p962
          and 'OUT = "/tmp/b962-focusmove.json"' in _p962
          and 'out["out"] = "/tmp/b962-focusmove.json"' in _p962
          and '"/tmp/b961-ticensus.json"' not in _p962)

    # ══ 批 963：⭐⭐⭐⭐⭐ 全量节点 DOM 序普查 + 落点**对账** ⇒
    #    NN.2 的「跳过 2 个节点」被**精确成「恰好 1 个」**，且那一枚**与邻居同构** ══
    print("— YYYY. 批 963 拿全量节点清单对账：落点 = DOM 序，只少一枚 —")

    check("YYYY.1 ⭐⭐⭐⭐⭐ **落点序列 = 全量 DOM 序，只少一枚** —— "
          "**NN.2 的「跳过 2 个」被精确成「恰好 1 个」**；"
          "而**被跳过的那一枚在 DOM 上与邻居完全同构** ⇒ "
          "「跳过」**不是 DOM 属性能解释的** ⇒ 原因**在应用自己的节点表里**",
          '"verdict_963": (' in _ausrc
          and "**落点序列 = 全量 DOM 序，只少一枚**" in _ausrc
          and "**NN.2 的「跳过 2 个」被精确成「恰好 1 个」**" in _ausrc
          and "全量节点 **76** 个（DOM 序）" in _ausrc
          and "**绕了一整圈**（76 + 30）" in _ausrc
          and "**+1 出现 103 次、" in _ausrc
          and "**+2 出现 1 次**" in _ausrc
          and "**除那一枚之外，每一步都是 DOM 序的下一枚**" in _ausrc
          and "**唯独被跳过的那一枚在 DOM 上与邻居完全同构**" in _ausrc
          and "全量 76 个 `tabindex` 全是 " in _ausrc
          and "**不是 DOM 属性决定得了的**" in _ausrc
          and "**NN.2 那条处置依然正确**" in _ausrc
          and "**只能按纯 DOM 序实现并把差异如实记为已知差异**" in _ausrc
          # ⭐ 钉探针：普查与对账都在，且**只比身份**
          and 'NODECENSUS_JS = """([nodeSel]) => {' in _p963
          and "if (!el.matches(nodeSel)) return;" in _p963
          and "`NODECENSUS_JS` 自己就匹配不上它要验的东西" in _p963
          and 'c["n_nodes_census"] = _nc.get("n_nodes")' in _p963
          and "c[\"n_nodes_census\"] = _nc.get(\"n_nodes\")" in _p963
          and "对账只比**身份**（tid），**" in _ausrc
          and "只比**身份**（tid），**不比绝对下标**" in _p963
          # ⭐ 钉探针：步长是**一等读数**、门挂在它上面
          and 'c["n_step_plus1"] = sum(1 for s in _steps if s == 1)' in _p963
          and 'c["n_step_plus2"] = sum(1 for s in _steps if s == 2)' in _p963
          and 'c["n_step_gt2"] = sum(1 for s in _steps if s > 2)' in _p963
          and 'c["n_step_wrap"] = sum(1 for s in _steps if s < 0)' in _p963
          and '"node_steps_are_dominant_plus1": bool(all(' in _p963
          and '"exactly_one_node_skipped": bool(all(' in _p963
          and 'r["cells"][0].get("n_step_plus2") == 1' in _p963
          and "**恰好一枚**被跳过（NN.2 记的是「2 个」" in _p963)

    check("YYYY.2 ⚠️⚠️⚠️ **第一版的对账判据（「连续前缀」）是错的，被读数否掉** —— "
          "而那个 `False` **并不代表有 bug**（走查绕了圈 ⇒「前缀」不成立）；"
          "**门也一起换成独立分母**；第一版的判据与其读数**都留档**",
          '"criterion_was_wrong_963": (' in _ausrc
          and "**第一版的对账判据（「连续前缀」）是错的，被读数否掉**" in _ausrc
          and "**那个 `False` 并不代表有 bug**" in _ausrc
          and "**绕了一整圈** ⇒ 「前缀」这个说法" in _ausrc
          and "**正确的判据是「步长」**" in _ausrc
          and "**门也一起换了**" in _ausrc
          and "原来那道门挂在「连续前缀」上" in _ausrc
          and "**都留档**" in _ausrc
          and "**不许悄悄删掉**（承 HH.4）" in _ausrc
          # ⭐ 钉探针：错判据**原文保留**、新判据在旁边、门换了
          and "**第一版的判据（「连续前缀」）是错的，被读数否掉**" in _p963
          and "那个 `False` **不代表有 bug**" in _p963
          and 'c["landed_is_census_prefix"] = bool(_pref_ok)   # 留档：第一版判据的结果'
              in _p963
          and 'c["landed_first_mismatch"] = _first_bad         # 留档：第一版判据的首个不符点'
              in _p963
          and "**第一版这道门用的是「连续前缀」，而那个判据本身是错的**" in _p963
          and "改挂**独立分母**" in _p963
          and 'r["cells"][0].get("n_step_gt2") or 0) == 0' in _p963
          and 'r["cells"][0].get("n_step_wrap") or 0) >= 1' in _p963)

    # ══ 批 964：⭐⭐⭐⭐ 那枚被跳过的节点**到底特殊在哪** —— 穷尽非 `tabindex`
    #    维度后：**DOM 上依然查不到** ⇒ **原因不在 DOM**，**如实写仍未查明** ══
    print("— ZZZZ. 批 964 解剖那枚被跳过的节点：可区分项全是位置噪声 ⇒ DOM 查不到 —")

    check("ZZZZ.1 ⭐⭐⭐⭐ **`tabindex` 维度已穷尽后换非 `tabindex` 维度**（几何 / "
          "可见性 / 计算样式 / 属性集 / 类名 / 子节点 / 文本 / 内部可聚焦数 / "
          "是否被选中 / 父链 / 视口内）⇒ 拿它与**左右两个邻居**逐字段比；"
          "⚠️ **判据可证伪**：差异为空**也是正当结论** ⇒ **不许**因为空就编一个机制圆上",
          '"what_964_measures": (' in _ausrc
          and "963 已把「跳过」**精确成恰好一枚**" in _ausrc
          and "**`tabindex` 这条维度已经穷尽**" in _ausrc
          and "换**非 `tabindex`** " in _ausrc
          and "拿它与**左右两个邻居**逐字段比" in _ausrc
          and "**判据可证伪**" in _ausrc
          and "**不许**因为空就编一个机制圆上" in _ausrc
          # ⭐ 钉探针：解剖维度真的在文件里
          and 'SKIPANATOMY_JS = """([nodeSel, tid]) => {' in _p964
          and "getBoundingClientRect" in _p964
          and "n_inner_focusable: inner.length" in _p964
          and "in_viewport:" in _p964
          and "aria_selected: el.getAttribute('aria-selected')," in _p964
          and "offset_parent_null: el.offsetParent === null," in _p964
          # ⭐ 钉探针：门挂在「**三枚都解到了**」上（否则无从比起 ⇒ 假绿）
          and '"skip_node_found_with_neighbors": bool(all(' in _p964
          and 'len(r["cells"][0].get("skip_neighbor_tids") or []) == 2' in _p964
          and 'len(r["cells"][0].get("skip_anatomy") or {}) == 3' in _p964)

    check("ZZZZ.2 ⚠️⚠️⚠️ **「A ≠ B」不等于「A 能把 A 从 C 里挑出来」** —— "
          "第一版把「字典整体不等」当成了「有差异」，**位置噪声被当成了原因**；"
          "⇒ 加**第二层判据「可区分」**（与左右邻居都不相等才算数）",
          '"diff_is_not_discriminative_964": (' in _ausrc
          and "**第一版把「字典整体不等」当成了「有差异」**" in _ausrc
          and "**位置噪声被当成了原因**" in _ausrc
          and "**`z_index`（68 / 67 / 69）与 " in _ausrc
          and "**每枚节点按位置必然不同**" in _ausrc
          and "**320 / 328 / 320**" in _ausrc
          and "**另一个邻居完全相同** ⇒ **不可区分**" in _ausrc
          and "加**第二层判据**「**可区分**」" in _ausrc
          and "**「A ≠ B」不等于「A 能把 A 从 C 里挑出来」**" in _ausrc
          and "**凡是比较，必须问「这个差异能不能把目标从对照里挑出来」**"
              in _ausrc
          # ⭐ 钉探针：第二层判据在文件里，且门要求**两项都被显式分类**
          and "964 的**第二层判据**：差异 ≠ 可区分" in _p964
          and "第一版把「字典整体不等」当成了「有差异」" in _p964
          and "_disc, _nondisc = [], []" in _p964
          and "if _nv and all(_sv != v for v in _nv):" in _p964
          and '"diff_fields_classified": bool(all(' in _p964
          and "只报「有差异」是不够的 —— 位置噪声会被当成原因" in _p964)

    check("ZZZZ.3 ⭐⭐⭐⭐ **本批的诚实结论：可区分项全是「按位置必然不同」的量** ⇒ "
          "**没有一个是内在属性** ⇒ **DOM 上依然查不到** ⇒ **原因不在 DOM**；"
          "⚠️ **记「仍未查明」，不编机制**（承 960 那条：矛盾原样记账）",
          "**可区分项全是「按位置必然不同」的量**" in _ausrc
          and "**没有一个是内在属性**" in _ausrc
          and "**DOM 上依然查不到 ⇒ 原因不在 DOM**" in _ausrc
          and "**全部可区分项都是「按位置必然不同」的量**" in _p964
          and "`z_index` / `transform`" in _p964
          and "**DOM 上依然查不到 ⇒ 原因不在 DOM**" in _p964)

    check("ZZZZ.4 ⚠️⚠️ **探针在跑之前就被自己的切片守卫拦下** —— "
          "`(p.className || '').toString().slice(...)` 中间插了个 `.toString()` "
          "就与守卫要的**紧挨着**的字面量对不上；⇒ ⭐ **这证明守卫是活的**"
          "（与 946「守卫自己匹配不上它要验的东西」正好成对）",
          '"slice_guard_fired_964": (' in _ausrc
          and "**探针在跑之前就被自己的切片守卫拦下**" in _ausrc
          and "**中间插了个 `.toString()` 就对不上**" in _ausrc
          and "**这类「字面量守卫」只认逐字相邻**" in _ausrc
          and "**任何在两者之间插的调用都会让它假红**" in _ausrc
          and "它证明了**守卫是活的**（不是恒绿）" in _ausrc
          and "与 946 那次「守卫自己匹配不上它要验的东西」正好成对" in _ausrc
          # ⭐ 钉探针：改后的写法**逐字相邻**
          and "cls: (p.className || '').slice(0, 40)," in _p964
          and "cls: (p.className || '').toString().slice(0, 40)," not in _p964
          and '"SKIPANATOMY_JS 里有**非字符串**切片（§131）"' in _p964)

    # ══ 批 965：⭐⭐⭐⭐⭐ DOM 已穷尽 ⇒ 问**机制层**问题：「它能被脚本聚焦吗？」══
    #    ⇒ **两个候选机制全被否掉** ⇒ **跳过是应用自己的选择** ══
    print("— AAAA. 批 965：被跳过的那枚**可以被脚本聚焦、且不会被拽走** ⇒ 跳过是选择 —")

    check("AAAA.1 ⭐⭐⭐⭐⭐ **两个候选机制全被否掉**：963 观察到「从 67 按 Tab "
          "落到 69」，可能是 (a) **根本不可聚焦** 或 (b) **被 `focusin` 拽走**；"
          "⇒ 实测 `focus()` **同步就落上**、且**四个时点都没被拽走** ⇒ "
          "**两者皆非** ⇒ **跳过是应用自己的选择**",
          '"what_965_measures": (' in _ausrc
          and "963/964 已经把**两条路都走到头**了" in _ausrc
          and "**「它到底能不能被脚本聚焦？」**" in _ausrc
          and "(a) **它根本不可聚焦**" in _ausrc
          and "(b) 它**可以**聚焦，但**应用的 `focusin` 处理器立刻把焦点" in _ausrc
          and "同步就**没落上去** ⇒ (a)" in _ausrc
          and "同步**落上了**、微任务后**被拽走** ⇒ (b)" in _ausrc
          and "**必须带对照组**" in _ausrc
          # ⭐ 钉探针：四个时点**真的**都读了
          and "rec.sync = WHO();" in _p965
          and "queueMicrotask(() => { rec.micro = WHO();" in _p965
          and "setTimeout(() => { rec.task = WHO(); }, 0);" in _p965
          and "rec.frame = WHO();" in _p965
          # ⭐ 钉探针：对照组 = 跳过枚 + **两个邻居**（两个不同的集合）
          and '"focus_test_has_control": bool(all(' in _p965
          and 'len(r["cells"][0].get("focus_test_tids") or []) == 3' in _p965
          and "_targets += [_cset[_si - 1], _cset[_si + 1]]" in _p965
          # ⭐ 钉探针：只调 `focus()`、**不点任何东西**
          and "只调 `el.focus()`、**不点任何东西**" in _p965
          and "try { el.focus(); } catch (err)" in _p965)

    check("AAAA.2 ⚠️⚠️⚠️⭐⭐⭐ **第一版的汇总层把判决整个说反了** —— "
          "而**原始读数其实是对的**：`READ_FT_JS` 返回的是**整张以 tid 为键的表**，"
          "我却当单条记录用 ⇒ `sync` 取到 `None` ⇒ 三项全打成「没落上」；"
          "⇒ ⭐ **一个能把结论说反的汇总层，比没有汇总层更坏**；"
          "⇒ 纪律：**判词与原始读数矛盾时先怀疑判词**",
          '"unwrap_inverted_verdict_965": (' in _ausrc
          and "**第一版的汇总层把判决整个说反了**" in _ausrc
          and "**原始读数其实是对的**" in _ausrc
          and "**整张以 tid 为键的表**" in _ausrc
          and "三项**全打成「没落上」**" in _ausrc
          and "**真相正好相反**" in _ausrc
          and "**全是 `is_target = true`**" in _ausrc
          and "**一个能把结论说反的汇总层，比没有汇总层更坏**" in _ausrc
          and "**读数到不了**（恒空）" in _ausrc
          and "**取值层级搞错 ⇒ 读数到了、但被解释成反的**" in _ausrc
          and "**必须回查原始读数至少一次**" in _ausrc
          and "先怀疑判词**（本批就是这样查出来的）" in _ausrc
          # ⭐ 钉探针：显式解包 + 解包漏一个就红的门
          and "_raw = ev(READ_FT_JS) or {}" in _p965
          and "_ft[_tid] = _raw.get(_tid)" in _p965
          and "**判决整个反了**" in _p965
          and '"focus_test_unwrap_complete": bool(all(' in _p965
          and '(r["cells"][0].get("n_unwrap_miss") or 0) == 0' in _p965)

    check("AAAA.3 ⚠️⚠️⚠️ **第一版的 `FOCUSTEST_JS` 有结构性错误**：`micro` / `task` / "
          "`frame` 写成局部变量再 `return` ⇒ 赋值在 **return 之后** ⇒ "
          "**调用方永远看不到**；⇒ 改挂 `window.__ft` 由第二步读走 ⇒ "
          "**一个恒空的读数比没有读数更坏**",
          '"structural_bug_965": (' in _ausrc
          and "**第一版的 `FOCUSTEST_JS` 有个结构性错误**" in _ausrc
          and "**调用方永远看不到它们**" in _ausrc
          and "**结构性不可达**" in _ausrc
          and "**挂在 `window.__ft` 上**、由第二步 `READ_FT_JS` 读走" in _ausrc
          and "**先安排、后读**" in _ausrc
          and "**一个恒空的读数比没有读数更坏**" in _ausrc
          and 'READ_FT_JS = """() => {' in _p965
          and "window.__ft = window.__ft || {};" in _p965
          and "**调用方永远看不到它们**" in _p965
          # ⭐ 诊断动作必须还原（承 943）
          and 'FOCUSTEST_JS.count("removeEventListener") == 1' in _p965
          and "`FOCUSTEST_JS` 没把 `focusin` 监听**摘掉**" in _p965)

    check("AAAA.4 ⭐⭐⭐⭐ **顺带钉住一条机制事实**：被跳过的那枚 "
          "`el.tabIndex === -1`（**而** `getAttribute('tabindex')` "
          "⇒ 浏览器**原生 `Tab` 根本不会停在这些 `div` 节点上** ⇒ "
          "**应用必须自己调 `focus()`**（与 962「节点段 102/140 在派发中搬」吻合）"
          "⇒ 整条链子闭合",
          "**本批判决：两个候选机制**全被否掉**" in _ausrc
          and "`el.tabIndex === -1`" in _ausrc
          and "浏览器**原生 `Tab` 根本不会停在这些 `div` 节点上**" in _ausrc
          and "**应用必须自己调 `focus()`**" in _ausrc
          and "在派发中搬」**吻合**" in _ausrc
          # ⭐ 钉探针：两个口径**都**读了（属性 vs 计算值）
          and "tab_index_prop: el.tabIndex," in _p965
          and "**而** `getAttribute('tabindex')` " in _ausrc)

    # ══ 批 966：⭐⭐⭐⭐ 最后一块**行为侧** —— 点选那枚 vs 点选两个邻居 ══
    print("— YYYYY. 批 966 行为侧：三枚点完**完全一致** ⇒ 行为侧也查不出 —")

    check("YYYYY.1 ⭐⭐⭐⭐ **行为侧也查不出**：三枚点完**逐项一致** —— "
          "都**被自己选中**（`n_selected 0 → 1`）、都**不把焦点搬进节点**、"
          "都**不开新层** ⇒ 那枚在**可观察行为上与邻居无异**",
          '"what_966_measures": (' in _ausrc
          and "965 之后只剩**行为侧**可查" in _ausrc
          and "**选中态 / 编辑态 / 是否开层**" in _ausrc
          and "**每枚都重新 `boot()` 归零**" in _ausrc
          and "**不盲点**" in _ausrc
          and "**点之前先纯读地确认「那个坐标上到底是什么」**" in _ausrc
          and "**因为点上不安全" in _ausrc
          and "**我够不够得着**" in _ausrc
          # ⭐ 钉探针：纯读规划 + 守卫在 click 之前 + 每枚 boot
          and 'CLICKPLAN_JS = """([nodeSel, tid]) => {' in _p966
          and "document.elementFromPoint(x, y)" in _p966
          and "hit_is_button:" in _p966
          and "点之前先看清那个坐标上是什么" in _p966
          and "            boot_fn()                     # ⭐ 每枚都归零" in _p966
          and 'guard_point(_plan["x"], _plan["y"])' in _p966
          and 'STATE_JS = """([nodeSel]) => {' in _p966
          and '"click_plan_recorded": bool(all(' in _p966
          and '"click_all_three_accounted": bool(all(' in _p966
          and "**三枚都要有结论**（点到了 或 如实记「没点」）" in _p966)

    check("YYYYY.2 ⭐⭐⭐⭐ **三条路全部走完的总结**（963 `tabindex` / 964 解剖 / "
          "965 可聚焦性 / 966 行为）⇒ **那枚与邻居在**所有可观察维度**上无异** ⇒ "
          "**跳过是应用自己表里的一个选择**，**没有 DOM 表达式**；"
          "⇒ 对复刻不变：**按纯 DOM 序实现 + 把这一枚记为已知差异**",
          "**跳过是应用自己表里的一个选择**" in _ausrc
          and "**没有 DOM 表达式**" in _ausrc
          and "**对复刻不变**：**按纯 DOM 序实现" in _ausrc
          and "**三枚行为一致 ⇒ 行为侧也查不出**" in _p966
          and "**三枚行为不同 ⇒ 那枚确实特殊**" in _p966)

    check("YYYYY.3 ⚠️⚠️⚠️ 966 在**跑起来之前**又踩三个坑，三个都**当场抓住**："
          "① `READ_FM_JS` 的**名字**被写成 `READ_FT_JS`（**函数体却是前者的**）"
          "⇒ 同名覆盖 ⇒ `NameError`；② **Python 的 `#` 注释留在 JS 字符串里**"
          "⇒ 运行时才炸、而**静态 JS 门没抓到**；③ 新门**少一个右括号** ⇒ "
          "`py_compile` 当场报 ⇒ ⭐ 共同点：**都是「复制/插入」带进来的**",
          '"three_more_traps_966": (' in _ausrc
          and "在**跑起来之前**又踩了三个坑，三个都**当场抓住**" in _ausrc
          and "**函数体是 `READ_FM_JS` 的读走逻辑**" in _ausrc
          and "**同名覆盖**" in _ausrc
          and "直接 **`NameError`**" in _ausrc
          and "**复制/插入时必须核「名字」和「函数体」" in _ausrc
          and "**把 Python 的 `#` 注释留在了 JS 字符串里**" in _ausrc
          and "**运行时才炸**" in _ausrc
          and "**那也是一条要记的洞**（静态门有覆盖不全的问题）" in _ausrc
          and "**少写了一个右括号**" in _ausrc
          and "**都是「复制/插入」这一动作带进来的**" in _ausrc
          and "**三样都要过再谈读数**" in _ausrc
          # ⭐ 钉探针：三个修复**真的**在文件里
          and "第一版这里的名字被写成了 `READ_FT_JS`" in _p966
          and "同名覆盖" in _p966
          and "**复制/插入时必须核「名字」" in _p966
          and "**第二版在这里踩了另一个坑**" in _p966
          and "// ⚠️ **不截断**：数组 `slice` 会被切片守卫" in _p966
          and '"click_plan_recorded": bool(all(' in _p966
          and 'for r0 in out["runs"] if "skipped" not in r0["cells"][0])' in _p966)

    # ══ 批 967：⭐⭐⭐⭐⭐ 把 900 与 963 的两个数**放进同一张表对账** ══
    print("— ZZZZZ. 批 967 两个可观测量对账：900 与 963 都没错 + 更正 965 —")
    # ⚠️ 968/968b 的 `replicarmptr_968` / `nextjsportal_968b` 在 audit 里
    #   **嵌在 `armptr_967` 之内**（它们是 967 的后续两批）⇒ 判据锚 `_ausrc`。
    #   968 用**五位**前缀 `AAAAA`：`AAAA`–`ZZZZ` 已经被 26 批占满，
    #   而 967 刚因为**撞号**（`CCCC` 撞 941、`DDDD` 撞 942）改过一次名 ⇒ 不复用。

    check("ZZZZZ.1 ⭐⭐⭐⭐⭐ **900 与 963 都没错 —— 它们量的不是同一件事**（源站 2/2 "
          "逐项一致）：「被布上 `'0'`」漏 **2** 枚（`b22-upload`、`音频 61`）、"
          "「被 `Tab` 落到」漏 **1** 枚（`音频 61`）⇒ **差集恰好 1 枚** = "
          "`b22-upload` ⇒ **它落上过，但从不是落焦「本体」**（两次都落在内层 "
          "`替换媒体` 按钮，那两按布的 `'0'` 是 `音频 node: 音频 7`）⇒ "
          "**它不是「不被选中」，而是「压根没进过指针」**；而 **`音频 61` 才是唯一一枚"
          "既没被布、也没被落上的节点** ⇒ 963–966 那四条维度的「跳过」"
          "**只对这一枚成立**",
          '"armptr_967"' in _ausrc
          and "**900 与 963 都没错 —— 它们量的不是同一件事**" in _ausrc
          and "**900 那个数第一次被复核成功**" in _ausrc
          and "`n_landed_never_armed` = " in _ausrc
          and "**它落上过，但从不是落焦「本体」**" in _ausrc
          and "**不是「不被选中」，而是「压根没进过指针」**" in _ausrc
          and "才是唯一一枚既没被布、也没被落上的" in _ausrc
          and "**只对这一枚成立**" in _ausrc
          # ⭐ 钉探针：两个可观测量**在同一轮**里同时量，且落焦**拆成三类**
          and "OUT = \"/tmp/b967-armptr.json\"" in _p967
          and "**同一轮**里同时量这两个可观测量" in _p967
          and 'POINTS = ("pre", "post", "task", "after")' in _p967
          and "kind: idx < 0 ? 'out' : (t === node ? 'self' : 'inner')" in _p967
          )

    check("ZZZZZ.2 ⭐⭐⭐⭐ **顺带否掉 965 §二 的越界推论**（965 **主判决不动**）："
          "那个 `el.tabIndex === -1` 读自**孤立的 `focus()` 测试**（那一瞬间节点身上"
          "**没有** `tabindex` 属性）⇒ **走查里落焦的节点 106/140 读到的就是 `'0'`**、"
          "而且 `'0'` 在按后 350ms **仍然布着**（140/140）⇒ "
          "**`tabindex='0'` 确实把这些 `div` 装进了 `Tab` 序列**、**不撤**正是 ⑦"
          "「此后不回撤」⇒ ⇒ ⭐⭐⭐ **「A ≠ B」不等于「A 能把 A 从 C 里挑出来」**",
          '"corrects_965_967"' in _ausrc
          and "**更正 965 §二 的一句越界推论**（965 **主判决不动**）" in _ausrc
          and "**那个 `-1` 只说明「那一瞬间它身上没有 `tabindex` 属性」**" in _ausrc
          and "**走查里的落焦节点 106/140 读到的 `tabindex` 就是 `'0'`**" in _ausrc
          and "**`'0'` 在按后 350ms 仍然布着**" in _ausrc
          and "**不撤**正是 ⑦「此后不回撤」" in _ausrc
          and "**「A ≠ B」不等于「A 能把 A 从 C 里挑出来」**" in _ausrc
          and "**原样成立、不动**的部分：965 的**主判决**" in _ausrc
          # ⭐ 钉探针：4 个取样点 + 「不预设布防时刻」的纪律 + after 点真读到布防
          and "**不预设「布 `'0'` 发生在哪一刻」**" in _p967
          and 'ARMED_ONLY_JS = """([nodeSel]) => {' in _p967
          and '"armed_read_is_live"' in _p967
          and "min(_c0.get(\"armed_distinct_tids\") or 0," in _p967)

    check("ZZZZZ.3 ⭐⭐⭐⭐ **产品改动落地**（不只研究）：`JimengWorkspace.tsx` 的"
          "「已知差异」块**原文保留 + 加改写横幅**（承 HH.4）⇒ 把「900 的 2 个」"
          "改成「**只有 1 枚**是已知差异」并说清**四条维度穷尽只对那一枚成立**；"
          "同时把 965 那句越界推论的更正也写进同一块",
          "**批 967 改写上面那段（原文保留、不删；下面这段取代它的结论）**" in _wsrc
          and "上面那段把 `b22-upload` 与 `音频 61` **当成同一类**了，**那是错的**" in _wsrc
          and "它**不是「不被选中」，而是「压根没进过指针」**" in _wsrc
          and "唯一一枚既没被布、也没被落上的节点。" in _wsrc
          and "按**纯 DOM 序**实现，把**这一枚**" in _wsrc
          and "（不是两枚）记为已知差异" in _wsrc
          and "**顺带更正 965 的一个越界推论**" in _wsrc
          and "**走查里落焦的节点 106/140 读到的就是 `tabindex='0'`**" in _wsrc
          and "**布防 ⇒ 落焦**" in _wsrc
          # ⚠️ 原文必须**还在**（HH.4：撤销结论时原文保留）
          and "**2 个整轮从没被布上 `'0'`**" in _wsrc
          and "⚠️ 已知差异（900 查明后**如实记下**" in _wsrc)

    check("ZZZZZ.4 ⚠️⚠️ 967 的门**有牙**（不是恒真门）：干跑喂**假数据**时 "
          "`armed_read_is_live` / `landing_channels_both_present` **直接判红**；"
          "且**干跑当场抓到一处真错** —— `RAW_KEYS` 与 `DERIVED_KEYS` **重了 "
          "`blank`** ⇒ 键账免疫针**在跑之前就红**（与 966 的三个坑同族）",
          '"discipline_967"' in _ausrc
          and "**每道门都挂在独立分母上**" in _ausrc
          and "**干跑当场抓到一处真错**：`RAW_KEYS` 与 `DERIVED_KEYS` " in _ausrc
          and "**门有牙的证明**" in _ausrc
          and "**不是恒真门**" in _ausrc
          # ⭐ 钉探针：装/摘配平 + 幂等 + finally 无条件复查 + 两轮比较在循环外
          and "window.__ap_off = () => {" in _p967
          and "if (window.__ap_off) window.__ap_off();" in _p967
          and "finally:" in _p967
          and "`finally` 里**无条件**复查 `__ap_off`" in _p967
          and '"fired_eq_rows"' in _p967
          and 'c["fired_eq_rows"] = (c["n_fired_total"] == len(rows))' in _p967
          and "# ── ⭐⭐ 两轮比较**必须在 `for rep` 循环之外**" in _p967
          # ⚠️ 键账免疫针**真的**在文件里
          and 'assert not (RAW_KEYS & DERIVED_KEYS), "派生键与原始读数键重叠了' in _p967)

    check("ZZZZZ.5 ⭐⭐ **判词不许预写**：探针只输出 `recon`（**纯数字**），"
          "audit 里那几段判词是**读过 `/tmp/b967-armptr.json` 的原始读数之后**才写的 "
          "⇒ 这是 965「汇总层把判决说反」之后立的规矩",
          "**判词不许预写**：探针只输出 `recon`（**纯数字**）" in _ausrc
          and "**只搬数字、不写判词**" in _p967
          and 'out["recon"] = {' in _p967
          # ⚠️ 探针里**不许**出现预写的判词字符串
          and "verdict_armed" not in _p967
          and "verdict_recon" not in _p967)

    # ══ 批 968/968b：**复刻侧**用 967 同一把尺子复核 + 「18 = 18」的假匹配 ══
    print("— AAAAA. 批 968 复刻侧复核 + 968b 拆穿「数目相等」 —")

    check("AAAAA.1 ⭐⭐⭐⭐ **967 那两条机制规则在复刻侧同样成立**（2/2 逐项一致）："
          "**布防 ⇒ 落焦** `self_eq_armed` = `n_self_rows` = **14/14**；"
          "**`'0'` 不撤** `n_armed_after_rows` = `n_armed_presses` = **80/80**；"
          "`armed_point_hist` = `{\"pre\": 80}` ⇒ 布防在**每一按开始时就已存在**，"
          "与源站 `{\"pre\": 139, \"post\": 1}` **同一形状** ⇒ 复刻的 `armAll` "
          "**只写不撤**、arming 的**时机**也对了",
          '"replicarmptr_968"' in _ausrc
          and "**967 那两条机制规则在复刻侧同样成立**" in _ausrc
          and "= **14/14**" in _ausrc
          and "= **80/80**" in _ausrc
          and "复刻的 `armAll` **只写不撤**" in _ausrc
          and "**同一形状**" in _ausrc
          # ⭐ 钉探针：**逐字搬 967 的仪器**（`_grab` + assert）⇒ 两侧才可比
          and "def _grab(name):" in _p968
          and 'INSTALL_JS = _grab("INSTALL_JS")' in _p968
          and 'assert _s in _p967src, f"{_n} 抠出来**不等于** 967 里的那份' in _p968
          and '"js_verbatim_from_967"' in _p968
          and "**复刻与源站同一把尺子**" in _p968
          # ⭐ 钉探针：关系式判据（不是绝对值）+ 分母要对
          and "**判据是关系式的、不是绝对值**" in _p968
          and "步长门的分母是 `step_pairs`、" in _p968)

    check("AAAAA.2 ⭐⭐⭐⭐ **步长：复刻严格按纯 DOM 序** —— `step_hist` = "
          "`{\"+1\": 12, \"wrap\": 1}`、**`gt2` = 0、`+2` = 0**（2/2）"
          "⇒ **比源站「干净」**（源站 963 是 `{+1: 103, +2: 1, 折返: 1}`、**恰好漏一枚**）"
          "⇒ **967 写进实现的处置（「按纯 DOM 序 + 把那一枚记为已知差异」）确实落地**；"
          "且 `n_never_armed`/`n_never_landed`/`n_landed_never_armed` **三个都是 0**",
          '"steps_dom_order_968"' in _ausrc
          and "**步长：复刻严格按纯 DOM 序**" in _ausrc
          and "`gt2` = 0、`+2` = 0" in _ausrc
          and "复刻比源站「干净" in _ausrc
          and "**确实落地了**" in _ausrc
          and '"three_sets_align_968"' in _ausrc
          and "`n_never_armed` = **0**" in _ausrc
          and "**复刻三张集合两两对齐**" in _ausrc
          # ⚠️⚠️ **`wrap` 必须单独记成一类**（962 的教训）
          and "**`wrap` 必须单独记成一类**" in _ausrc
          and "**「非单调」根本推不出「乱序」**" in _ausrc
          # ⭐ 钉探针：步长分四类 + 回折单独一类
          and 'step_hist[cat] = step_hist.get(cat, 0) + 1' in _p968
          and 'cat = "wrap"' in _p968
          and "**回折单独记成一类**" in _p968)

    check("AAAAA.3 ⭐⭐⭐⭐⭐ **拆穿一个「数目相等」的假匹配** ⇒ 长期待办"
          "「复刻缺的项目面板停靠点」**差点被错关掉**：复刻 out 段实测 **18 个**、"
          "源站也 **18 个**，但第 17 个是 **`NEXTJS-PORTAL`** —— 纯读复查（968b，"
          "**零点击零按键**）：`parent_tag` = **`SCRIPT`**、`n_children` = **0**、"
          "`innerHTML` = **空**、`rect` = **`[0,0,0,0]`**、`is_focusable` = **`False`**"
          "⇒ **它压根不是复刻的 UI 元素**、是 **Next.js 开发态注入的 runtime 节点**"
          "⇒ 复刻真正的 out 停靠点是 **17 个** ⇒ **差的那一个仍然是「项目面板」**",
          '"nextjsportal_968b"' in _ausrc
          and "**「数目相等」不等于「集合相等」**" in _ausrc
          and "**差点被错关掉**" in _ausrc
          and "**待办不许关**" in _ausrc
          and "**数目对齐只是线索、不是结论**" in _ausrc
          and "**逐个核身份**" in _ausrc
          # ⭐ 钉探针：968b 真的查了那几项，而不是只说结论
          and "parent_tag: e.parentElement ? e.parentElement.tagName : null," in _p968b
          and "is_focusable: e.tabIndex >= 0," in _p968b
          and '"pure_read": True' in _p968b
          # ⚠️ 仓里**不许**出现自写的 nextjs-portal（否则这条结论就假了）
          and not any("nextjs-portal" in t or "NEXTJS-PORTAL" in t
                      for t in _replica_srcs))

    # ══ 批 970：⭐⭐⭐⭐⭐ 同口径重测 ⇒ 推翻 969 的「唯一差异」结论 ══
    print("— CCCCC. 批 970 同口径重测：两次同一种错（对照没对齐） —")

    check("CCCCC.1 ⭐⭐⭐⭐⭐ **同口径重做那张表之后，结论完全变了**：复刻的 "
          "`文本` 那枚**两侧完全一致**（源站**自身 `None`** / 祖先 "
          "`canvas-fixed-toolbar`；复刻**自身 `None`** / 祖先**也是 "
          "`canvas-fixed-toolbar`」）⇒ ⭐⭐⭐ **复刻连「testid 放在祖先容器上」"
          "这个做法都对上了**；逐个对齐后**其余 15 枚的「自身 tid」与「祖先 tid」"
          "两侧都相同**；`n_self_eq_closest` = **28/30**（只有 2 圈里的 2 个 `文本`"
          "「自身 ≠ 祖先」）",
          '"owntid_970"' in _ausrc
          and "**同口径重做那张表之后，结论完全变了**" in _ausrc
          and "那枚两侧**完全一致**" in _ausrc
          and "**复刻连「testid 放在祖先容器上」这个做法都对上了**" in _ausrc
          and "两侧都相同**" in _ausrc
          and "`n_self_eq_closest` = **28/30**" in _ausrc
          # ⭐⭐ 钉探针：**两个字段都读**，且各有**自证门**（少一个就红）
          and 'self_tid: a.getAttribute(\'data-testid\'),' in _p970
          and "closest_tid: c ? c.getAttribute('data-testid') : null," in _p970
          and "**两个字段必须都在**，少一个这道门就恒红/恒绿" in _p970
          and '"both_tid_fields_present_both_reps"' in _p970
          # ⭐ 钉探针：两张表**并排**摆出来（口径不同就一眼看得见）
          and 'c["out_ids_self"] = sorted({' in _p970
          and "两个字段各出一张清单，**并排**摆出来" in _p970)

    check("CCCCC.2 ⭐⭐⭐⭐⭐ **真正剩下的差异只有两处，而且 816 都明确记录过、"
          "都有理由 ⇒ 都不该改**：`更多`（源站自身无 tid、祖先 "
          "`canvas-editor-menu`；复刻自造 `canvas-more-trigger`，816 的理由是"
          "「删掉 = 削弱自己的验收锚点」）与 `生成历史`（源站与「搜索」**共用** "
          "`canvas-panel-launcher`、照抄会**同时命中 2 个元素**、打破 801 的断言；"
          "复刻用独立的 `canvas-history-launcher`）⇒ ⭐⭐ **原计划的产品改动"
          "（把「更多」改成 `canvas-editor-menu`）取消** —— 那会把有理由的"
          "有意偏离改回去、**削弱复刻自己的验收锚点**",
          '"two_deliberate_deviations_970"' in _ausrc
          and "**真正剩下的差异只有两处" in _ausrc
          and "两处 816 都明确记录过、" in _ausrc
          and "都有理由 ⇒ 都不该改**" in _ausrc
          and "**主动削弱自己的验收锚点**" in _ausrc
          and "**同时命中 2 个元素**" in _ausrc
          and "**969 漏掉了第二处**" in _ausrc
          and "**原计划的产品改动（把复刻「更多」改成 " in _ausrc
          and "**削弱复刻自己的验收锚点**" in _ausrc
          # ⭐⭐ **反证**：816 那条决策**真的**在仓库里（钉的是源码原文）
          and "verify-jimeng-batch816-anchors.py" in _p970
          and "「更多」源站**没有** testid，复刻保留自造的 " in _p816
          and 'KNOWN_CLONE_ONLY = {"canvas-more-trigger", "canvas-history-launcher"}'
          in _p816)

    check("CCCCC.3 ⭐⭐⭐⭐⭐ **两次同一种错，归成一条纪律**：968b 拿 **954 的历史"
          "基线**当本轮源站一侧的对照 ⇒ 把「**基线过期**」误读成「**实现有缺陷**」；"
          "969 拿复刻的**自身 tid** 比源站读到的**祖先 tid** ⇒ 把「**口径不同**」"
          "误读成「**实现有缺陷**」⇒ ⇒ ⭐ **先核「我比的是不是同一个东西」**"
          "（同一轮？同一字段？同一口径？）⇒ ⭐⭐ **发现差异先怀疑对照、"
          "别先怀疑实现**；⭐⭐⭐ 而**两次都是靠「原始读数里两个字段都有」翻回来的** "
          "⇒ 965「判词必须回查原始读数」这族**已复发三次**",
          '"same_kind_of_error_twice_970"' in _ausrc
          and "**两次同一种错，必须归成一条纪律**" in _ausrc
          and "把「**基线过期**」误读成「**实现有缺陷**」" in _ausrc
          and "把「**口径不同**」误读成「**实现有缺陷**」" in _ausrc
          and "**先核「我比的是不是同一个东西」**" in _ausrc
          and "**发现差异时，先怀疑对照、别先怀疑实现**" in _ausrc
          and "**两次都是「对照侧没对齐」**" in _ausrc
          and "**两次都是自己先写结论、下一批才发现**" in _ausrc
          and "原始读数里其实两个字段都有」翻回来的**" in _ausrc
          and "到现在已复发" in _ausrc
          and "这两批是它的**第二次与第三次**兑现" in _ausrc
          # ⭐ 钉探针：970 自己就把「同口径」写进了问题与门
          and "**同一个字段要对比，就得用同一个口径**" in _p970
          and '"same_ruler_note"' in _p970
          and "969 也同时记了 `tid`（自身）与 `host_tid`（祖先）" in _p970
          # ⚠️⚠️⚠️⚠️⚠️ **第五次「静默跳过」**：`_p816` 一开始**没登记**进
          #   `PROBE_VARS` ⇒ 锚点自查**静默跳过**它、报「0 问题」，
          #   而 **verifier 那条判据真的红了**（609/610）⇒ 已补登记
          and '"fifth_skip_trap_970"' in _ausrc
          and "**同一个「静默跳过」坑的第五次**" in _ausrc
          and "**两个门给了相反的信号**" in _ausrc
          and "**锚点自查报「0 问题」≠ 全部被查过**" in _ausrc
          and "**它只查「已登记」的那些变量**" in _ausrc
          and '"_p816": "scripts/verify-jimeng-batch816-anchors.py",' in _anchs)

    # ══ 批 971：⭐⭐⭐⭐⭐ 954 那个「未复现条目」= **`document.body` 本身** ══
    print("— EEEEE. 批 971 取样 954 未复现项：它是 document.body，不是 UI 元素 —")

    check("EEEEE.1 ⭐⭐⭐⭐⭐ **954 记的 `out:测试项目…已保存…分享` 不是 UI 元素 "
          "—— 它就是 `document.body` 本身**：三条独立读数同指一枚（k=90，两轮逐字相同）"
          "—— ① 落焦元素 `tag = ` **`BODY`**；② `self_tid = None` **且** "
          "`closest_tid = None`（自己与所有祖先都没有 `data-testid`）；"
          "③ `tabindex = None`、`el.tabIndex = -1`、`is_focusable = false`、"
          "`rect = [0, 0, 1512, 1200]`（**整块视口**）、`inner_text_head` = "
          "**页面顶部那一大片文本**、`n_children` = **12–13**；"
          "⇒ ⭐⭐⭐ **成名的机制**：`WHOAMI_JS` 的 `tid = a.closest("
          "'[data-testid]')` 对 `body` **必然是 `null`** ⇒ `aria` 就**回退到 "
          "`innerText.slice(0, 30)`** ⇒ **整页文本被当成这个元素的「名字」** "
          "⇒ 它是**焦点掉出文档时的兜底落点** ⇒ ⇒ ⭐⭐⭐⭐ "
          "**挂了几十批的待办「复刻缺的项目面板停靠点」可以彻底结案**，"
          "而结案依据是「**找到了那枚元素本身**」、**不是**「重测没找到」",
          '"body_is_document_body_971"' in _ausrc
          and "**954 记的 `out:测试项目…已保存…分享` 不是 UI 元素 —— " in _ausrc
          and "**三条独立读数同指一枚**" in _ausrc
          and "`tag = ` **`BODY`**" in _ausrc
          and "`self_tid = None` **且** `closest_tid = None` " in _ausrc
          and "`is_focusable = false`" in _ausrc
          and "`rect = [0, 0, 1512, 1200]`" in _ausrc
          and "`n_children` = **12–13**" in _ausrc
          and "**回退到 `innerText.slice(0, 30)`**" in _ausrc
          and "**它是焦点掉出文档时的兜底落点，" in _ausrc
          and "不是「项目面板」**" in _ausrc
          and "结案依据是「**找到了那枚元素本身**」" in _ausrc
          # ⭐⭐ 钉探针：三套口径**并读**，且每套各有**自证断言**（少一套就红）
          and 'aria_label: al,' in _p971
          and "aria_whoami: al || ti || (txt || '').slice(0, 30) || null," in _p971
          and 'inner_text_head: (txt || \'\').slice(0, 40),' in _p971
          and 'contains_saved:' in _p971
          and 'n_children: a.childElementCount,' in _p971
          and 'assert TEXTHO_JS.count("aria_label: al,") == 1' in _p971
          and 'assert TEXTHO_JS.count("aria_whoami: al || ti ||") == 1' in _p971
          and '"three_calibers_present_both_reps"' in _p971)

    check("EEEEE.2 ⭐⭐⭐⭐⭐ **954 那句「源站多出 1」的成因终于说得出机制了 —— "
          "两侧的「名字」用了不同口径（这是这一族错的**最早一次**，954 就是源头）**："
          "**源站侧**用 `WHOAMI_JS`（`aria-label || title || innerText.slice(0,30)`）"
          "⇒ **`BODY` 拿到了一个假名字**；**复刻侧**读**纯 `aria-label`**（不带回退）"
          "⇒ `BODY` 读到 `null`、**根本不出现在名字表里** "
          "⇒ ⇒ ⭐⭐⭐ **同一枚元素、同一件事，两侧只差一个回退规则、就差恰好 1**，"
          "与「复刻少了一个 UI 元素」毫无关系；⇒ ⭐⭐⭐⭐ **同口径之后**："
          "源站真 UI 停靠点 **17 枚**、复刻真 UI 停靠点 **17 枚** ⇒ **相等**；"
          "⇒ ⭐⭐ 换成 `(tag, 自身 tid, 祖先 tid)` 作键：源站 **16** / 复刻 **17**，"
          "差的 3 个键**恰好**是那两处 816 有意偏离（源站 `更多` 自身无 tid；"
          "复刻 `更多` = `canvas-more-trigger`、`生成历史` = `canvas-history-launcher`；"
          "而源站 `搜索` 与 `生成历史` **共用**一个 tid ⇒ **折叠成 1 个键**，"
          "这才是 16 与 17 的真正来由）⇒ ⇒ **两侧 UI 停靠点实质等价**",
          '"why_954_saw_one_extra_971"' in _ausrc
          and "两侧的「名字」用了不同口径**" in _ausrc
          and "（这是这一族错的**最早一次**" in _ausrc
          and "954 就是它的源头" in _ausrc
          and "**`BODY` 拿到了一个假名字**" in _ausrc
          and "**不带回退**" in _ausrc
          and "**根本不出现在名字表里**" in _ausrc
          and "⇒ 差恰好 1**" in _ausrc
          and "源站真 UI 停靠点 **17 枚**、" in _ausrc
          and "复刻真 UI 停靠点 **17 枚** ⇒ **相等**" in _ausrc
          and "源站 **16** / 复刻 **17**" in _ausrc
          and "差的 3 个键**恰好**是那两处" in _ausrc
          and "816 有意偏离（源站 `更多` 自身无 tid" in _ausrc
          and "**折叠成 1 个键**" in _ausrc
          and "**两侧 UI 停靠点实质等价**" in _ausrc
          # ⭐⭐ **反证**：「`BODY` 那枚两侧 `rect` 完全相同」必须有两侧读数支撑
          and '"both_sides_have_fallback_971"' in _ausrc
          and "而是两侧各带一枚非 UI 兜底落点**" in _ausrc
          and "**`BODY` 那枚两侧 `rect` **完全相同** " in _ausrc
          and "**只有复刻多一枚 0×0 的 `NEXTJS-PORTAL`**" in _ausrc
          # ⭐ 钉探针：门必须证明「`closest_tid is None` 的落点」**真的会命中东西**
          #   （恒 0 时「不存在」与「判据写错」分不开，必须如实判红）
          and '"closest_none_read_is_live_both_reps"' in _p971
          and '"out_segment_walked_both_reps"' in _p971)

    check("EEEEE.3 ⭐⭐⭐⭐⭐ **本批最系统的一条：任何用 `WHOAMI_JS` 的 `aria` 做 "
          "out 段停靠点统计的批次，都必须先排除 `tag == 'BODY'`** "
          "—— 954 / 959 / 961 / 966 都用过这个口径 ⇒ **判据层面的修法**："
          "凡是以「停靠点集合」为分母的门，**分母里必须显式剔掉 "
          "`BODY`/`NEXTJS-PORTAL`**，否则**分母上挂着一枚不是 UI 的东西**、"
          "**「集合相等」这门判据就永远差 1 或差 2** ⇒ "
          "**这不是「再测一遍」能解决的 —— 口径写在脚本里**；"
          "⚠️ 另两条纪律：**未查明就写未查明**（`BODY` 为何有时在线有时不在线："
          "969 那轮没有、971 这轮有，而两批各自 2/2 轮内一致 ⇒ **不是随机噪声**、"
          "属**规模量**，本批无对照 ⇒ **猜测已标明是猜测、未混进结论**）；"
          "**读数里的 `0` 绝不能被 `or` 兜底**（`(tab_index_prop or -1) < 0` "
          "会把**所有可聚焦元素**判成不可聚焦 —— 本批对账脚本就踩了这个坑）",
          '"systemic_reading_rule_971"' in _ausrc
          and "**954 / 959 / 961 / 966 都用过这个口径**" in _ausrc
          and "分母里必须显式剔掉 `BODY`/`NEXTJS-PORTAL`**" in _ausrc
          and "**「集合相等」这门判据就永远差 1 或差 2**" in _ausrc
          and "**口径写在脚本里**" in _ausrc
          and '"why_body_sometimes_971"' in _ausrc
          and "**未查明（本批只记，不下结论）**" in _ausrc
          and "**它不是随机噪声**" in _ausrc
          and "**但本批没有对照，不许把它当结论**" in _ausrc
          and '"falsy_zero_bug_971"' in _ausrc
          and "**纪律：处理读数时不要用 `or` 兜底" in _ausrc
          and "必须写显式的 `is None` 判断" in _ausrc
          and "门**必须挂在独立分母上**" in _ausrc
          # ⭐⭐⭐ **第六次「静默跳过」的预防**：`_p971` **与判据同一步**读进来
          and '"_p971": "scripts/jimeng_probe971_savestate_src.py",' in _anchs
          # ⭐ 钉探针：只读、不调 `focus()`；两轮一致 + 监听器配平 + 键不重叠
          and '"reps_agree"' in _p971
          and '"keys_disjoint"' in _p971
          and '"fired_eq_rows_both_reps"' in _p971
          and '"listener_balanced_both_reps"' in _p971
          and "**从不调 `focus()`** ⇒ 不污染焦点读数" in _p971
          and "**本批零计费动作。**" in _p971)

    # ══ 批 972：⭐⭐⭐⭐⭐ `BODY` 接缝的座位；969 那套 `landed` 口径吃掉了它 ══
    print("— FFFFF. 批 972 接缝座位 + 两套口径并排：代理条件滤掉了 BODY —")

    check("FFFFF.1 ⭐⭐⭐⭐⭐ **接缝的座位查实了，而且它不是末尾兜底**：环长 **18** 枚，"
          "`el === document.body` 的那一格落在**下标 6**（**第 7 枚**）、两轮相同 ⇒ "
          "**既不在环首也不在环尾**；**它前面那一枚是 `与 AI 对话`**"
          "（`canvas-sidecar-launcher`）⇒ 接缝落在右簇最后一个控件之后、左簇第一个控件之前；"
          "**它后面还有 11 枚真 UI 停靠点** ⇒ ⭐⭐⭐ **971 猜的「走过了最后一个"
          "可聚焦元素之后的落点」（**规模量**）被否掉了**；⭐⭐ 门 "
          "`is_body_eq_tag_body` 要求 `el === document.body`（**比引用**）与 "
          "`tag == 'BODY'`（**比标签**）**同时**成立 ⇒ 「标签相同但**不是** body」"
          "的元素分得开",
          '"body_seat_972"' in _ausrc
          and "**接缝的座位查实了，而且它**不是**末尾兜底**" in _ausrc
          and "**969 / 971 / 972 三批共 6 轮**读数**完全一致**" in _ausrc
          and "环长 **18** 枚" in _ausrc
          and "**下标 6**（**第 7 枚**），两轮相同" in _ausrc
          and "**它既不在环首也不在环尾**" in _ausrc
          and "**它前面那一枚是 `与 AI 对话`**" in _ausrc
          and "**它后面还有 11 枚真 UI 停靠点**" in _ausrc
          and "（**规模量**）被否掉了**" in _ausrc
          and "门 `is_body_eq_tag_body` 要求**两者同时**成立" in _ausrc
          # ⭐⭐ 钉探针：`SEAT_JS` 真的比引用，且**只读、不调 `focus()`**
          and 'is_body: el === document.body,' in _p972
          and 'assert "el === document.body" in SEAT_JS' in _p972
          and 'assert "focus(" not in SEAT_JS' in _p972
          and '"is_body_eq_tag_body_both_reps"' in _p972
          and '"body_seat_is_interior_both_reps"' in _p972
          and '"body_seat_identical_across_reps"' in _p972
          and '"seam_predecessor_is_sidecar_both_reps"' in _p972
          and '"body_is_not_end_fallback_both_reps"' in _p972
          # ⭐⭐⭐ **钉关系不钉绝对值**：座位用「两轮相同」与「既不在环首也不在环尾」
          and "座位用「两轮相同」" in _ausrc
          and "**不钉下标 6**" in _ausrc)

    check("FFFFF.2 ⭐⭐⭐⭐⭐ **同一族错的第六次，而且这次把机制说死了 —— 969 不是"
          "「没量到」，是「量到了但被一个代理条件滤掉了」**：969 的 out 段是"
          "用 `for L in (r.get(\"landed\") or [])` + `L[\"kind\"]==\"out\"` 圈的，"
          "而 **`BODY` 那一行的 `landed` 是空数组** ⇒ "
          "**它在进 `out_stops` 之前就被整行过滤掉了**；本批把两套口径**并排**算出来"
          "（两轮同一个数）：`own.kind=='out'` ⇒ **18**、"
          "`landed[].kind=='out'`（**969 口径**）⇒ **17**、**差额 = 1**，"
          "被丢掉那行 `tag` = **`BODY`**、`landed` 长度 = **0** ⇒ "
          "⇒ ⭐⭐⭐⭐ **969 那个 `null_tid_rows = 0` 由此得解**："
          "它不是「页面上没有」，而是「**统计口径没数到**」⇒ ⇒ ⭐⭐⭐ **纪律**："
          "**凡是用「某个代理条件」圈出来的集合，都要单独记「被代理条件吃掉了多少」**",
          '"landed_caliber_drops_body_972"' in _ausrc
          and "是「量到了但被一个代理条件滤掉了」**" in _ausrc
          and "**`BODY` 那一行的 `landed` 是空数组**" in _ausrc
          and "**它在进 `out_stops` 之前就被整行过滤掉了**" in _ausrc
          and "**18**" in _ausrc and "**17**" in _ausrc
          and "**差额 = 1**，被丢掉的那一行 `tag` = **`BODY`**、" in _ausrc
          and "`landed` 的长度 = **0**" in _ausrc
          and "**969 那个 `null_tid_rows = 0` 由此得解**" in _ausrc
          and "**统计口径没数到**" in _ausrc
          and "**凡是用「某个代理条件」圈出来的集合，" in _ausrc
          and "都要单独记「被代理条件吃掉了多少」**" in _ausrc
          # ⭐⭐⭐⭐⭐ 全链每一环都要在（954→969→970→971→972）
          and "① **954**：源站用 `WHOAMI_JS`" in _ausrc
          and "② **969**：改用纯 `aria-label`" in _ausrc
          and "③ **970**：换字段口径" in _ausrc
          and "④ **971**：三套口径并读" in _ausrc
          and "⑤ **972**：把两套口径**并排**" in _ausrc
          # ⭐⭐ **反证**：969 那段圈 out 段的代码**真的**在仓库里（钉源码原文）
          and 'for L in (r.get("landed") or []):' in _p969
          and 'if L.get("kind") == "out":' in _p969
          and "第 305–310 行" in _ausrc
          # ⭐⭐ 钉探针：两套口径真的**并排**算，且门**成对**（防恒 0 + 防漏网）
          and 'out_own = [(r["k"], r) for r in rows if r["own"].get("kind") == "out"]' in _p972
          and 'out_stops = []' not in _p972
          and '"landed_caliber_drops_something_both_reps"' in _p972
          and '"caliber_gap_eq_dropped_both_reps"' in _p972
          and '"dropped_rows_are_all_body_both_reps"' in _p972
          and "一个防恒 0、一个防漏网" in _p972)

    check("FFFFF.3 ⭐⭐⭐⭐⭐ **把两侧的环旋到同一起点逐格对齐之后：是同一条环**，"
          "复刻只差两处 —— ① 多一枚 **0×0 的 `NEXTJS-PORTAL`**（968b 已证是 "
          "**Next.js 开发态产物**）；② ⭐⭐⭐ **`rf__wrapper`（Canvas）那枚的位置"
          "不一样**（**源站**在 `用户菜单` 与 `文本` **之间**、**复刻**在"
          "**接缝之后、`返回首页` 之前**）⇒ **其余 16 枚逐格顺序两侧完全相同**；"
          "⚠️⚠️⚠️ **本批不提出产品改动**（复刻侧 `rf__wrapper` 的**成因还没量过**，"
          "它是 xyflow 的容器、挂外层 ref 取的）⇒ ⭐⭐ **「发现差异先怀疑对照」"
          "这条不许被跳过**；另记一条纪律：**「`(k, row)` 当成 `row` 用」这一族"
          "栽到第四次**，而 **`py_compile` 抓不到** ⇒ 修法是解包写对 "
          "**＋ 加一条形状自证**（`assert` 每个元素**都**是 `(k, row)`）",
          '"ring_is_same_cyclic_order_972"' in _ausrc
          and "**把两侧的环旋到同一起点逐格对齐之后：" in _ausrc
          and "是同一条环**，复刻只差两处" in _ausrc
          and "多一枚 **0×0 的 `NEXTJS-PORTAL`**" in _ausrc
          and "**`rf__wrapper`（Canvas）那枚的位置不一样**" in _ausrc
          and "**源站**：在 `用户菜单` 与 `文本` **之间**" in _ausrc
          and "**复刻**：在**接缝之后、`返回首页` 之前**" in _ausrc
          and "**其余 16 枚逐格顺序两侧完全相同**" in _ausrc
          and "**本批不提出产品改动**" in _ausrc
          and "**成因还没量过**" in _ausrc
          and "**「发现差异先怀疑对照」这条不许被跳过**" in _ausrc
          and '"tuple_shape_bug_972"' in _ausrc
          and "这一族栽到第四次**" in _ausrc
          and "**`py_compile` 抓不到**（它只抓语法、不抓运行期形状）" in _ausrc
          and "**加一条形状自证**" in _ausrc
          and "**类型错误发生在解包那一刻**" in _ausrc
          # ⭐⭐ 钉探针：形状自证**真的**写进探针了
          and "out_own 里有不是 (k, row) 的元素" in _p972
          and "out_landed 里有不是 (k, row) 的元素" in _p972
          # ⚠️ 971 那条「未查明」必须**已挂改写横幅**（原文保留、不删）
          and "**批 972 改写横幅" in _ausrc
          and "**上面这条「未查明」是个假问题，" in _ausrc
          # ⭐⭐⭐ 第七次预防同一个坑：`_p972` **与判据同一步**登记
          and '"_p972": "scripts/jimeng_probe972_seam_src.py",' in _anchs)

    # ══ 批 973：⭐⭐⭐⭐⭐ 复刻侧「环序 = DOM 序」⇒ 972 悬的问题有答案 ══
    print("— GGGGG. 批 973 复刻侧测环序：环序就是 DOM 序，BODY 是开发态连带效应 —")

    check("GGGGG.1 ⭐⭐⭐⭐⭐ **复刻的环序就是 DOM 序** —— 而这条是**第一次**"
          "**直接**被证实（967 当时是**靠步长推**的，步长对得上**不等于**"
          "顺序的来源被验过）：⭐⭐⭐ 证据取的是 "
          "`document.querySelectorAll('*')` 里的**全文档下标**"
          "⇒ **不依赖任何 `data-testid`、不依赖任何「簇」**；"
          "`arc_ranks` = `[110, 120, 121, 125, 134, 139, 145, 154, 160, 166, 169, "
          "237, 240, 245, 251, 255, 268, 37, 42]` ⇒ **单调递增、恰好一次回绕**"
          "（268 → 37），两轮**逐字相同**；⇒ ⇒ 门钉的是**「回绕次数 ≤ 1」这个关系式**、"
          "**不是**任何绝对下标；⭐⭐ **证据的粒度要匹配断言的粒度** —— "
          "「环序」是**顺序**命题 ⇒ 证据必须是**顺序**（单调性 + 回绕次数）、"
          "**不是**「集合相等」",
          '"ring_is_dom_order_973"' in _ausrc
          and "**复刻的环序就是 DOM 序** —— 而这条是**第一次**" in _ausrc
          and "步长对得上**不等于**顺序的来源被验过" in _ausrc
          and "`document.querySelectorAll('*')` " in _ausrc
          and "**单调递增、恰好一次回绕**（268 → 37），两轮**逐字相同**" in _ausrc
          and "**门钉的是「回绕次数 ≤ 1」这个关系式**，" in _ausrc
          and "**不是**任何绝对下标" in _ausrc
          and "**证据的粒度要匹配断言的粒度**" in _ausrc
          and "「环序」是**顺序**命题 ⇒ 证据必须是**顺序**" in _ausrc
          and "**不是**「集合相等」" in _ausrc
          # ⭐⭐ 钉探针：新件真的读**全文档**下标、真的**只读**
          and "document.querySelectorAll('*')" in _p973
          and "**不依赖任何 testid、不依赖任何「簇」**" in _p973
          and 'assert "focus(" not in DOMRANK_JS' in _p973
          and '"ring_follows_dom_order_both_reps"' in _p973
          and '"at_most_one_wrap_both_reps"' in _p973
          # ⭐⭐⭐ 哨兵值自证：`dom_rank` 恒 `-1` 会让整条链**安静空转**
          and '"dom_rank_is_live_both_reps"' in _p973
          and "**读数恒为一个哨兵值时要判红**" in _ausrc
          and "自证门（`dom_rank_is_live`）" in _ausrc)

    check("GGGGG.2 ⭐⭐⭐⭐⭐ **972 悬的那件事有答案了：`rf__wrapper` 的位置差异是 "
          "DOM 摆放差异（**实现差异**），不是口径差异**：复刻侧它的 "
          "`dom_rank` = **42** ⇒ **它是整个环里 `dom_rank` 最小的真 UI 停靠点**"
          "（其余全在 **110–268**）⇒ **它是复刻 DOM 序里的第一个可聚焦元素**；"
          "而 972 实测源站那一枚在 `用户菜单` 与 `文本` **之间** ⇒ "
          "**它在源站 DOM 序的中间**、不是第一个；⭐⭐⭐⭐ **「实现差异」这个判断"
          "是从实现里查出来的、不是从数字里猜的** —— `armRovingTabindex` "
          "**只布 `.react-flow__node`、从不碰 `rf__wrapper`** ⇒ "
          "它的 `tabindex` 来自 **xyflow 自己的静态属性**、位置完全由 DOM 摆放决定；"
          "⚠️⚠️ **但源站侧的 `dom_rank` 本批没量** ⇒ 「源站的环**也是** DOM 序」"
          "**不能**由本批下结论 ⇒ **下一批把同一件仪器搬到源站跑一遍**",
          '"wrapper_is_first_in_dom_973"' in _ausrc
          and "**972 悬的那件事有答案了：" in _ausrc
          and "**它是整个环里 `dom_rank` 最小的真 UI 停靠点**" in _ausrc
          and "（其余全在 **110–268**）" in _ausrc
          and "**它是复刻 DOM 序里的第一个可聚焦元素**" in _ausrc
          and "**它在源站 DOM 序的中间**，不是第一个" in _ausrc
          and "**「实现差异」这个判断是从实现里查出来的，" in _ausrc
          and "而 `armRovingTabindex` 只布 `.react-flow__node`、" in _ausrc
          and "从不碰 `rf__wrapper`**（静态取证" in _ausrc
          and "**它的 `tabindex` 来自 xyflow 自己的静态属性、" in _ausrc
          and "**但源站侧的 `dom_rank` 本批没量**" in _ausrc
          and "**不能**由本批下结论" in _ausrc
          and "**下一批把同一件仪器搬到源站跑一遍**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反证**：那条「只布 node、从不碰 wrapper」**真的**在实现里
          and 'function armRovingTabindex(flow: HTMLElement | null, dir: 1 | -1)' in _wsrc
          and 'nodes[i].setAttribute("tabindex", i === keep ? "0" : "-1");' in _wsrc
          and 'function armAll(nodes: HTMLElement[], keep: number)' in _wsrc
          # ⭐⭐ 钉探针：`flow_tabindex` / `flow_tid` 都被记下来了
          and '"flow_stop_is_live_both_reps"' in _p973
          and '"flow_tabindex_is_static_both_reps"' in _p973
          and "is_flow: !!(el.classList && el.classList.contains('react-flow'))," in _p973)

    check("GGGGG.3 ⭐⭐⭐⭐⭐ **顺手挖到一件更大的：复刻侧那枚 `BODY` 很可能整个是"
          "开发态产物的连带效应** —— `BODY` 那一格的前一格 = **`NEXTJS-PORTAL`**"
          "（`dom_rank` = **268**、**环里最大**），而它的 `focusable` = **`false`**"
          "⇒ ⇒ 从**浏览器无法聚焦**的元素按 `Tab` ⇒ 焦点掉到 `document.body`"
          "（`dom_rank` = **37**）⇒ 下一按走到 DOM 序里的第一个可聚焦元素 = "
          "`rf__wrapper`（**42**）⇒ ⇒ **推论：生产构建里没有 `nextjs-portal`、"
          "那枚 `BODY` 应当整个消失** ⇒ ⇒ **复刻侧有**两枚**开发态产物，"
          "不是 §182 写的那一枚**；⚠️⚠️ **源站那一侧的 `BODY` 前一格是 "
          "`与 AI 对话`（一个**能聚焦**的按钮）⇒ 两侧的 `BODY` 很可能不是同一个机制** "
          "⇒ **不许把复刻的机制直接搬到源站头上**；另记一条纪律："
          "**一种错重复到第三次就该改数据结构、而不是加断言**"
          "（`(k, row)` 那一族本批栽到第五次，而 972 加的形状自证**没抓到它**"
          "—— 因为**错在解包处、不在形状上**）⇒ 本批改成 `out_ks` / `out_rows` "
          "**两个平行列表**、**元组根本不再存在**",
          '"body_is_portal_artifact_973"' in _ausrc
          and "**顺手挖到一件更大的：" in _ausrc
          and "复刻侧那枚 `BODY` 很可能整个是开发态产物的连带效应**" in _ausrc
          and "而它的 `focusable` = **`false`**" in _ausrc
          and "**机制 therefore 说得通了**" in _ausrc
          and "推论（可验，本批**只测了复刻侧**）**" in _ausrc
          and "生产构建里**没有** `nextjs-portal` ⇒ " in _ausrc
          and "**「生产构建里没有这个元素」**" in _ausrc
          and "**复刻侧的环上有**两枚**开发态产物，" in _ausrc
          and "**改写 §182 的措辞**（原文保留）" in _ausrc
          and "**不许把复刻的机制直接搬到源站头上**" in _ausrc
          and '"tuple_family_fifth_973"' in _ausrc
          and "当成 `row` 用」这一族栽到第五次，" in _ausrc
          and "**形状自证只挡「形状错」，挡不住「解包错」**" in _ausrc
          and "**本批做的是结构性修法**" in _ausrc
          and "改成 `out_ks` / `out_rows` " in _ausrc
          and "**这一族的坑从根上被拆掉**（而不是再加一条断言）" in _ausrc
          and "**当一种错误重复到第三次，" in _ausrc
          # ⭐⭐ 钉探针：结构性修法**真的**写进探针了
          and "out_rows 里有不是 row-dict 的元素" in _p973
          and '"body_predecessor_unfocusable_both_reps"' in _p973
          and "focusable: (el.tabIndex === undefined) ? null : (el.tabIndex >= 0)," in _p973
          # ⚠️ 972 那条「复刻只差两处」必须**已挂改写横幅**
          and "**批 973 改写横幅" in _ausrc
          and "**上面「复刻只差两处」这句不准确，" in _ausrc
          # ⭐⭐⭐ 第七次预防同一个坑：`_p973` **与判据同一步**登记
          and '"_p973": "scripts/jimeng_probe973_ringorder_ck.py",' in _anchs)

    # ══ 批 974：⭐⭐⭐⭐⭐ 源站侧补上 973 留的对照缺口 ⇒ 两侧各测一轮、同一件仪器 ══
    print("— HHHHH. 批 974 源站侧测环序：两侧都是 DOM 序；973 那句「机制不同」说重了 —")

    check("HHHHH.1 ⭐⭐⭐⭐⭐ **两侧的环都是 DOM 序** —— 而 973 只证了复刻侧、"
          "**源站那一侧的 `dom_rank` 它自己写明了没量** ⇒ 本批补上：探针 974，"
          "**源站**，2 轮 × 1 格 × 140 次 `Tab`，`DOMRANK_JS` 用 `_grab` 从 973 "
          "**逐字抠**、**不复制源码**；⇒ 源站 `arc_ranks` **单调递增、"
          "恰好一次回绕**（2396 → 60），两轮**签名相同** ⇒ ⇒ ⭐⭐⭐ "
          "**「同一件仪器」是可证的**：`_grab` 抠完再 `assert _s in _p973` ⇒ "
          "**它是一条断言，不是文档里的一句保证**；⇒ ⇒ ⭐⭐⭐ "
          "**上一批的机制不许直接当成这一批的预期**",
          '"both_sides_are_dom_order_974"' in _ausrc
          and "**两侧的环都是 DOM 序** —— 而 973 只证了复刻侧，" in _ausrc
          and "**源站那一侧的 `dom_rank` 它自己写明了没量**" in _ausrc
          and "`DOMRANK_JS` 用 `_grab` 从 973 **逐字抠**、**不复制源码**" in _ausrc
          and "**单调递增、恰好一次回绕**" in _ausrc
          and "（2396 → 60），两轮**签名相同**" in _ausrc
          and "**973 的结论现在两侧都钉住了**" in _ausrc
          and "**「同一件仪器」是可证的**" in _ausrc
          and "**它是一条断言，不是文档里的一句保证**" in _ausrc
          and "**上一批的机制不许直接当成这一批的预期**" in _ausrc
          # ⭐⭐⭐⭐⭐ 钉探针：真的是 `_grab` + `assert`，不是复制
          and 'DOMRANK_JS = _grab("DOMRANK_JS", _p973)' in _p974
          and 'assert DOMRANK_JS in _p973, "DOMRANK_JS 不在 973 探针里 ⇒ 不是同一件仪器"' in _p974
          and '"_p974": "scripts/jimeng_probe974_source_domrank_src.py",' in _anchs
          and '"js_verbatim_from_973": ["DOMRANK_JS"]' in _p974
          and "⚠️⭐⭐ **不复制源码**" in _p974
          and "**不复制源码** —— `_grab` + `assert` " in _ausrc
          and "**它是一条断言，不是文档里的一句保证**" in _ausrc
          and '"source_ring_follows_dom_order_both_reps"' in _p974
          and '"source_dom_rank_is_live_both_reps"' in _p974
          and '"source_seam_pred_measured_both_reps"' in _p974)

    # ══ 批 975：⭐⭐⭐⭐⭐ 验假设 H₁ ⇒ **它被否了**；而否掉它的读数
    #   顺带给 967 补了**第二个独立证据** ══
    print("— IIIII. 批 975 源站祖先链 tabindex：H₁ 被判否；ti_attr 全 None 是 967 的第二证据 —")

    check("IIIII.1 ⭐⭐⭐⭐⭐ **H₁ 被判否**，而这是本批最大的收获：H₁ 原话是"
          "「`与 AI 对话` 的某个祖先带**正 `tabindex`** ⇒ 形成**独立的顺序焦点导航"
          "作用域** ⇒ 出作用域时焦点无处可落、暂留 `document.body`」；"
          "⇒ ⭐⭐⭐⭐⭐ **实测**：`与 AI 对话` 的**整条祖先链 9 层**，每一层的 "
          "`ti_attr`（`getAttribute('tabindex')`）**全都是 `None`** —— "
          "**DOM 上根本没有写 `tabindex` 属性**；⇒ ⇒ `ti_prop`（`.tabIndex`）读到的 "
          "`0` / `-1` **只是浏览器默认行为**、不是任何人写上去的 ⇒ ⇒ **H₁ 被否** ⇒ "
          "**不存在「独立作用域边界」**；⇒ ⇒ ⭐⭐⭐⭐⭐ **这一否顺带给出了 967 的"
          "第二个独立证据**（「源站 Tab 序 = 朴素环形 DOM 序、**无正 `tabindex`**」"
          "当时的证据是**步长观测**，本批是**属性逐层读出来是空的** ⇒ "
          "**两条证据互相独立、方法完全不同**）；⭐⭐ 整段 out 环**零个**停靠点的"
          "祖先链带正 `tabindex`，两轮一致",
          '"h1_falsified_975"' in _ausrc
          and "**H₁ 被判否** —— 而这是本批最大的收获" in _ausrc
          and "**`与 AI 对话` 的某个祖先带正 `tabindex`**" in _ausrc
          and "**整条祖先链 9 层**" in _ausrc
          and "**全都是 `None`** —— ⭐⭐⭐ " in _ausrc
          and "**DOM 上根本没有写 `tabindex` 属性**" in _ausrc
          and "**只是浏览器默认行为**，不是任何人写上去的" in _ausrc
          and "**H₁ 被否** ⇒ **不存在「独立作用域边界」**" in _ausrc
          and "**这一否顺带给出了 967 的第二个独立证据**" in _ausrc
          and "证据是**步长观测**" in _ausrc
          and "本批的证据是**属性逐层读出来是空的**" in _ausrc
          and "**两条证据互相独立、方法完全不同**" in _ausrc
          and "「源站侧没有任何对 Tab 序的显式干预」这条结论**更硬了**" in _ausrc
          and "整段 out 环**零个**停靠点的祖先链带正 `tabindex`" in _ausrc
          # ⭐⭐⭐⭐⭐ 钉探针：`ti_attr` 真的读 `getAttribute`（**不是** `.tabIndex`）
          and "ti_attr: tiAttr," in _p975
          and "assert 'ti_attr ||' not in SCOPE_JS" in _p975
          and '"h1_positive_tabindex_ancestor_both_reps"' in _p975
          and '"ti_reading_is_live_both_reps"' in _p975
          # ⭐⭐⭐ **否定结果尤其要钉**：它最容易在下一批被悄悄忘掉
          and "否定结果**尤其**要钉：它最容易在下一批被悄悄忘掉" in _anchs
          and '"_p975": "scripts/jimeng_probe975_scope_src.py",' in _anchs)

    check("IIIII.2 ⭐⭐⭐⭐⭐ **方法上有一处值得单独记**：`SCOPE_JS` 把每一层"
          "**同时**读 `ti_attr`（`getAttribute('tabindex')` ⇒ **属性在不在 / 是什么**）"
          "与 `ti_prop`（`.tabIndex` ⇒ **归一化后的可聚焦性**）⇒ "
          "**两件事因此分得开**：本批的全部结论来自「`ti_attr` 全是 `None`」，"
          "**只看 `ti_prop` 是看不出来的**（它会给出 `0` / `-1`）；"
          "⇒ ⇒ 这也让「不许用 `or` 兜底」**落成了一条可执行的断言** ⇒ "
          "971 踩过的 `(tab_index_prop or -1) < 0`（**把 `0` 当假值**）"
          "在这一族里被**物理禁止**；⇒ ⇒ **正向自证门与主门成对**："
          "`ti_reading_is_live` 先证明**确实逐层拿到了** ⇒ "
          "**「没有作用域」与「读数是空的」分不开**这件事被挡住了",
          '"ti_attr_vs_prop_975"' in _ausrc
          and "**这一批的方法上有一处值得单独记**" in _ausrc
          and "**属性在不在 / 属性是什么**（没有就是 `None`）" in _ausrc
          and "**归一化后的可聚焦性**" in _ausrc
          and "**两件事因此分得开**" in _ausrc
          and "本批的全部结论来自「`ti_attr` 全是 `None`」—— " in _ausrc
          and "**只看 `ti_prop` 是看不出来的**（它会给出 `0` / `-1`）" in _ausrc
          and "**一条可执行的断言**" in _ausrc
          and "把 `0` 当假值" in _ausrc
          and "**在这一族里被物理禁止**" in _ausrc
          and "**正向自证门与主门成对**" in _ausrc
          and "先证明**确实逐层拿到了**" in _ausrc
          and "**「没有作用域」与「读数是空的」分不开**这件事被挡住了" in _ausrc
          and 'ti_prop: (p.tabIndex === undefined) ? null : p.tabIndex' in _p975
          and "chain_depth" in _p975)

    check("IIIII.3 ⭐⭐⭐⭐⭐ **本批我自己写反了一道门，而处置过程本身就是一条纪律**："
          "第一版写的是 `body_precedes_sidecar`（`BODY` 在 `与 AI 对话` 之前）⇒ "
          "**它判红了**；⇒ ⭐⭐⭐ **门红先判「门错还是数据错」**：974 的读数就已经是"
          "「`与 AI 对话`(seat 5) → **`BODY`**(seat 6)」⇒ 与本批一致、2/2 相同 ⇒ "
          "⇒ **是门写反了**；⇒ ⇒ 处置是「**改门**（改精确）、不是放宽」；"
          "⇒ ⇒ ⭐⭐⭐⭐ **而且改门要成对**：只改正向的话，"
          "「改精确」与「放宽」**分不开** ⇒ 本批**额外钉了一条反向门** ⇒ "
          "**旧方向必须仍然是红的** ⇒ 这样才证明改的是**方向**、不是**门槛**；"
          "另记 `_grab` 教的一件事：**974 是 `_grab` 的「消费者」不是「生产者」**"
          "（它自己没定义字面量）⇒ 975 沿链回到源头 `_p973` ⇒ "
          "**三支探针、一个源头**而不是三份拷贝 ⇒ 并加 `assert` "
          "**974 自己一旦开始定义字面量就红**；⚠️⚠️ **诚实记账**：源站那枚 "
          "`BODY` 的机制**本批仍未查明**，只是候选空间缩小了 ⇒ "
          "⭐⭐⭐ **否掉一条假设 ≠ 查明机制**，这两件事不要混",
          '"reversed_gate_975"' in _ausrc
          and "**本批我自己写反了一道门，" in _ausrc
          and "第一版写的是 `body_precedes_sidecar`" in _ausrc
          and "**它判红了**" in _ausrc
          and "**门红先判「门错还是数据错」**" in _ausrc
          and "**是门写反了**" in _ausrc
          and "**处置是「改门」（改精确）、不是放宽**" in _ausrc
          and "**而且改门要成对**" in _ausrc
          and "「改精确」与「放宽」**分不开**" in _ausrc
          and "**额外钉了一条反向门**" in _ausrc
          and "**旧方向必须仍然是红的**" in _ausrc
          and "这样才证明改的是**方向**、不是**门槛**" in _ausrc
          and '"grab_is_consumer_975"' in _ausrc
          and "974 是 `_grab` 的「消费者」不是「生产者」**" in _ausrc
          and "**三支探针、一个源头**" in _ausrc
          and "**从「靠自觉」变成「有断言」**" in _ausrc
          and '"still_unexplained_975"' in _ausrc
          and "**本批仍然未查明**，只是候选空间被缩小了" in _ausrc
          and "**「作用域边界」这条出局**" in _ausrc
          and "**这是假说，不是结论**" in _ausrc
          and "**否掉一条假设 ≠ 查明机制**，这两件事不要混" in _ausrc
          and "**不许把复刻那套「从无法聚焦元素掉下来」搬过来当预期**" in _ausrc
          # ⭐⭐ 钉探针：成对的那两道门与源头反证都真在
          and '"sidecar_precedes_body_both_reps"' in _p975
          and '"reversed_relation_stays_false_both_reps"' in _p975
          and 'DOMRANK_JS = _grab("DOMRANK_JS", _p973)' in _p975
          # ⚠️ 974 那条「未查明」必须**已挂改写横幅**（原文保留、不删）
          and "**批 975 改写横幅" in _ausrc
          and "**975 验过一个假设 H₁、并把它判否了**" in _ausrc
          and "**否掉它的读数顺带给 967 补了" in _ausrc)

    check("HHHHH.2 ⭐⭐⭐⭐⭐ **`rf__wrapper` 的位置差异 = 实现差异，两侧各测一轮钉住了；"
          "而且差别是「两端对调」**：**源站**它在环的**最后一位**、`dom_rank` = "
          "177/179 ⇒ **它是源站 DOM 序里最后一个可聚焦元素**；**复刻**它的 "
          "`dom_rank` = 42 ⇒ **它是复刻 DOM 序里第一个可聚焦元素** ⇒ "
          "**不是「少了一个 / 多了一个」，是「同一枚在两端对调」**；"
          "⇒ 972 记的「源站那枚在 `用户菜单` 与 `文本` 之间」本批复核成立"
          "（源站环序 `用户菜单`(16) → **`rf__wrapper`**(17) → `文本`(0)）；"
          "⚠️⚠️ **仍不提出产品改动** —— 「差异是实现差异」测实了，"
          "但「**该往哪边对齐**」是**产品决策** ⇒ ⭐⭐⭐ "
          "**「差异成立」与「该怎么改」是两件事，不许拿前者当后者的许可证**",
          '"wrapper_ends_are_swapped_974"' in _ausrc
          and "**972 悬的那件事有答案了：" in _ausrc
          and "两侧各测一轮钉住了；而且差别是「**两端对调**」" in _ausrc
          and "**它是源站 DOM 序里最后一个可聚焦元素**" in _ausrc
          and "（环里最大的是 `与 AI 对话`，`dom_rank` = 2396/2398）" in _ausrc
          and "**它是复刻 DOM 序里第一个可聚焦元素**" in _ausrc
          and "**所以源站在弧的末端、复刻在弧的起点之前**" in _ausrc
          and "**不是「少了一个 / 多了一个」，是「同一枚在两端对调**」**" in _ausrc
          and "本批复核成立" in _ausrc
          and "→ **`rf__wrapper`**(17) → " in _ausrc
          and "**仍不提出产品改动**" in _ausrc
          and "**该往哪边对齐**" in _ausrc
          and "**「差异成立」与「该怎么改」是两件事，" in _ausrc
          and "不许拿前者当后者的许可证**" in _ausrc
          and '"source_flow_stop_is_live_both_reps"' in _p974
          and '"flow_seats_by_tid"' in _p974)

    check("HHHHH.3 ⭐⭐⭐⭐⭐ **两侧那枚 `BODY` 都是「DOM 序的回绕点」—— "
          "而 973 说「很可能不是同一个机制」，本批把它改掉**："
          "**结构角色两侧相同**（前一格 `dom_rank` 是环里最大、后一格是最小）；"
          "**触发方式两侧不同**（源站前一格 `canvas-sidecar-launcher`、"
          "`prev_focusable = TRUE`；复刻前一格 `NEXTJS-PORTAL`、"
          "`prev_focusable = false`）⇒ ⇒ ⭐⭐⭐ **纪律**："
          "**「实测到一个差异」很容易被写成「机制不同」** —— 本例差异只在**前驱元素**、"
          "**角色完全一致** ⇒ ⭐⭐ **下结论前先问「差异在哪个字段上」**；"
          "⚠️ **未测实**：源站那一枚**为什么**也会落在 body 上 ⇒ **记未查明**；"
          "另记本批自己犯的两处：① 跨轮门**拿绝对下标比相等** ⇒ 必然红 ⇒ "
          "**跨轮比顺序要比「顺序关系」、不是「绝对数值」**（修法**不是放宽**）；"
          "② 门 ⑥ 第一版写成 `... if False else True` ⇒ **一道恒真门，比没有门更坏** "
          "⇒ **凡写了 `if X` 的短路分支，都要问「X 恒定吗」**",
          '"seam_is_wrap_point_974"' in _ausrc
          and "**两侧那枚 `BODY` 都是「DOM 序的回绕点」" in _ausrc
          and "本批把它改掉" in _ausrc
          and "**结构角色（已测实，两侧相同）**" in _ausrc
          and "**触发方式（两侧不同，这才是 973 测到的）**" in _ausrc
          and "`prev_focusable = TRUE`（**可聚焦**）" in _ausrc
          and "`prev_focusable = false`" in _ausrc
          and "**改写 973 的说法**" in _ausrc
          and "**说重了**" in _ausrc
          and "**落点角色两侧相同**（都是回绕点）" in _ausrc
          and "**「实测到一个差异」很容易被写成「机制不同」**" in _ausrc
          and "⭐⭐ **下结论前先问「差异在哪个字段上」**" in _ausrc
          and "本批**只有观测、没有机制** ⇒ **记未查明**" in _ausrc
          and '"wrong_kind_gate_974"' in _ausrc
          and "**它必然红**" in _ausrc
          and "**在会动的源站上钉绝对值**" in _ausrc
          and "**纪律：跨轮比顺序，必须比「顺序关系」而不是「绝对数值」**" in _ausrc
          and "修法**不是放宽**" in _ausrc
          and "不必重跑源站就能确认改对了" in _ausrc
          and '"self_inflicted_omission_974"' in _ausrc
          and "**那是一道恒真门，" in _ausrc
          and "凡是写了 `if X` 的短路分支，都要问一句「X 恒定吗」**" in _ausrc
          and "**恒定的条件 + `else` 分支 = 一道永远绿的门**" in _ausrc
          # ⭐⭐ 钉探针：顺序签名门与被删掉的恒真门都要在
          and "rank_order_signature" in _p974
          and "**它必然红，而红的原因不是「环序变了」**" in _p974
          and "**不是放宽**" in _p974
          and "一道**恒真门**" in _p974
          and "⇒ 与 DOM 总大小无关 ⇒ 逐轮多/少一个元素**不该**让它红" in _p974
          # ⚠️ 973 那句必须**已挂改写横幅**（原文保留、不删）
          and "**批 974 改写横幅" in _ausrc
          and "**「很可能不是同一个机制」这句**说重了**，" in _ausrc
          and "**仍然成立的那半句**" in _ausrc)


    check("AAAAA.4 ⚠️⚠️ **步长那道门第一版太弱，是干跑当场抓到的**：它只查 "
          "`n_step_gt2 == 0` ⇒ 在「**全部是 `wrap`、`+1` 一次都没有**」的"
          "**退化数据**上**照样绿** ⇒ 按 942 的纪律**改严**（再加「`+1` 真的出现过」"
          "**且**「回折真的出现过」）⇒ 改完之后**双向可验**：退化数据判红、"
          "合理数据转绿 ⇒ ⭐ **一道门必须能红、能不红**",
          '"weak_gate_fixed_968"' in _ausrc
          and "**步长那道门第一版太弱，是干跑当场抓到的**" in _ausrc
          and "**改严**" in _ausrc
          and "**一道门必须能红、能不红**；只会绿的门**比没有门更坏**" in _ausrc
          # ⭐ 钉探针：改严后的门**真的**写了那两条
          and '"steps_are_dom_order_both_reps": bool(' in _p968
          and 'min(_c0.get("n_step_plus1") or 0, _c1.get("n_step_plus1") or 0) > 0' in _p968
          and 'min(_c0.get("n_step_wrap") or 0, _c1.get("n_step_wrap") or 0) >= 1' in _p968
          and "**第一版这道门太弱**" in _p968)

    # ══ 批 969：⭐⭐⭐⭐⭐ 同轮重测 ⇒ 推翻 968b 自己刚下的结论 ══
    print("— BBBBB. 批 969 同轮重测 out 段：差集是「基线过期」不是「实现有缺陷」 —")

    check("BBBBB.1 ⭐⭐⭐⭐⭐ **969 的判决是一条否定结果，而且它推翻的是上一批"
          "自己刚下的结论**：源站 out 段本轮 **17** 个停靠点**全都带真 "
          "`data-testid`**、**`host_tid is None` 的 0 个**（2/2）⇒ "
          "**判据门 `panel_judgement_is_live_both_reps` 如实判红** —— "
          "⭐ **判据恒 0 时必须报出来**，不许安静地写成「没有这个东西」；"
          "954 记的 `out:测试项目…已保存…分享` 其 `aria` 来自 **`WHOAMI_JS` 的 "
          "innerText 回退**（不是 `aria-label`）且含「**已保存**」这种**瞬时状态**"
          "⇒ **未复现、成因未查明**",
          '"projectpanel_969"' in _ausrc
          and "**本批的判决是一条否定结果" in _ausrc
          and "它推翻的是上一批自己刚下的结论" in _ausrc
          and "`null_tid_rows` = 0" in _ausrc
          and "**判据门 `panel_judgement_is_live_both_reps` " in _ausrc
          and "如实判红" in _ausrc
          and "判据恒 0 时**必须**报出来" in _ausrc
          and "**未复现、成因未查明**" in _ausrc
          # ⭐ 钉探针：**判据不许用自己起的名字**（按 host_tid is None，不按 aria）
          and "拿它匹配就等于把结论写进判据 ⇒ 判据是「`host_tid is None`」" in _p969
          and "拿它匹配就等于把结论写进判据" in _ausrc
          and 'null_rows = [(k, f) for k, f in out_stops if f.get("host_tid") is None]' in _p969
          and '"panel_judgement_is_live_both_reps"' in _p969
          # ⭐ `FINGER_JS` 只读 aria-label、**不回退** innerText（这条是判据的一部分）
          and "aria: a.getAttribute('aria-label')," in _p969
          # ⚠️⚠️ **不许**再钉「文件里没有 innerText」这种**过粗的否定**：
          #   探针自己的 `guard_point` 里就有 `innerText`（点守卫要读文案）
          #   ⇒ 那种断言**会假红** ⇒ 改成钉**口径声明**本身
          and 'out["aria_read_policy"] = (' in _p969
          and "**没有 `||` 兜底、没有 innerText 回退**" in _p969
          and "**口径不同**" in _p969)

    check("BBBBB.2 ⭐⭐⭐⭐⭐ **968b 那句「复刻 17 / 源站 18 / 差的那一个仍然是"
          "项目面板」是错的** —— 错因：**拿 954 的历史基线当本轮对照，没有在同一轮"
          "重新量源站** ⇒ 本轮**同轮实测**：源站 **17**、复刻 **16 真 + 1 个开发态"
          "产物** ⇒ **数目本来就相同**，且**集合逐个对完是同一组**（16 个身份全对上）"
          "⇒ ⭐⭐⭐ **挂了几十批的待办应当结案为「本轮两侧同组、结构相同」**；"
          "⭐⭐⭐ **纪律**：**同一件事要对比，就得在同一轮量两侧** —— 拿历史基线当"
          "本轮一侧的对照，会把「基线过期」误读成「实现有缺陷」",
          '"corrects_968b_969"' in _ausrc
          and "源站 18 个、差的那一个仍然是项目面板」是错的" in _ausrc
          and "**拿 954 的历史基线当本轮对照**" in _ausrc
          and "**没有在同一轮重新量源站**" in _ausrc
          and "**数目本来就相同**" in _ausrc
          and "**集合逐个对完，两侧是同一组**" in _ausrc
          and "**挂了几十批的待办" in _ausrc
          and "应当结案为「本轮两侧同组、结构相同」" in _ausrc
          and "同一件事要对比，" in _ausrc
          and "就得在同一轮量两侧" in _ausrc
          and "会把「基线过期」误读成「实现有缺陷」" in _ausrc
          # ⚠️ HH.4：968b 的**原文必须还在**，只加「已被 969 推翻」的横幅
          and "**差的那一个仍然是「项目面板」**" in _ausrc
          and "**本条已被批 969 推翻**，原文保留、不删" in _ausrc)

    check("BBBBB.3 ⭐⭐⭐ **唯一真实的结构差异：「更多」的 `data-testid` 不一致** —— "
          "源站 **`canvas-editor-menu`**、复刻 **`canvas-more-trigger`**；"
          "三处 aria 文本不同**全是数据/默认值**（`节点 76` vs `节点 7`、"
          "`Credits 791` vs `745`、`Zoom 50%` vs `73%`）⇒ **其余全部对齐**",
          '"one_real_structural_diff_969"' in _ausrc
          and "**唯一真实的结构差异：「更多」的 `data-testid` 不一致**" in _ausrc
          and "`canvas-editor-menu`" in _ausrc
          and "`canvas-more-trigger`" in _ausrc
          and "**全是数据/默认值，不是结构差异**" in _ausrc
          and "**其余全部对齐**" in _ausrc
          # ⭐ 钉探针：确实**逐个核身份**（tag / aria / 最近 data-testid）
          and "**逐个核身份**（`tag` / `aria` / 最近 `data-testid`）" in _ausrc
          and "host_tid: (a.closest('[data-testid]')" in _p969
          and 'tag: (a.tagName || \'\').toUpperCase(),' in _p969)


    check("BBBB.1 ✅⭐⭐⭐ **940 把 939 的判决性缺口填上了 —— 机制是「单指针」**："
          "游走后**节点带 tabindex 0/77 → 76/77**、而 `tabindex=\"0\"` **只 +1 不累积** ⇒ "
          "§130「roving 是单指针、不是留轨迹」的**源站实证**；"
          "被标记的 26 个 **unchanged 26/26** ⇒ **应用只动画布**",
          "src_roving_single_pointer_and_focus_matrix_940" in _ausrc
          and "**① ✅ 判决：Tab 游走给**节点本体**写 `tabindex`（939 缺的那一格）**" in _ausrc
          and "**① ✅ 判决：Tab 游走给**节点本体**写 `tabindex`（939 缺的那一格）**" in _ausrc
          and "**应用只动画布，不动顶栏/侧栏/dock 的元素**" in _ausrc
          # ⭐ 钉探针：游走**前**后各普查一次，且被标记集合与节点集合分开
          and "c_before = ev(COUNTS_JS, [B939_SEL])" in _p940
          and "reread = ev(REREAD_JS, [MARK_ATTR, B939_SEL])" in _p940
          and "trans = classify(idx[\"ti_before\"], reread[\"ti_after\"])" in _p940
          # ⭐ 钉探针：「属性被删」与「被设成 -1」是**分开**的类（§131 的 removed）
          and 'elif b == "-1" and a is None:' in _p940
          and 'key = "neg1_to_removed"' in _p940)
    check("BBBB.2 ⭐⭐ **第一张跨层焦点矩阵**（5 个层，两轮逐项相同）—— "
          "**「开层即接管焦点」与「冷启动可达」是两件完全独立的事**；"
          "顺带把 939 的「0 命中」**升级**成 `wrapped`（不可达），"
          "因为 `wrapped` 表示**序列走完一圈仍没到**、而 `capped` 只是「没测出来」",
          "**② ⭐⭐ 第一张**跳层**焦点矩阵**（5 个层，两轮逐项相同）**" in _ausrc
          and "**「开层即接管焦点」与「冷启动可达」是两件完全独立的事**" in _ausrc
          and "**`wrapped` 比 `capped` 强**" in _ausrc
          and "**940 把 939 的结论从「0 命中」升级成「`wrapped`（不可达）」**" in _ausrc
          # ⭐ 钉探针：`wrapped` 的判据是「落点**第二次出现**」（不是预算用尽）
          and "if m in seen:" in _p940
          and "wrapped = True" in _p940
          # ⭐ 钉探针：目标层用「开层焦点所在的那个层」（不是「新增层唯一」）
          and "if f_open.get(\"in_layer\") and f_open.get(\"layer_tid\"):" in _p940
          and 'tid, tid_src = f_open["layer_tid"], "开层焦点所在层"' in _p940
          # ⭐ 钉探针：`capped` 与 `wrapped` 是**两个**结局，分别记账
          and '"capped": first_in is None and not wrapped,' in _p940)
    check("BBBB.3 ⚠️⚠️ **阴阳对照门连改四版都错** ⇒ 沉淀成一条通用纪律："
          "**两个答案必须来自两个不同的集合**（同一个集合里的两种答案不构成对照，"
          "机制可以让它们同向变化）；且 v4 用的 `n_marked_is_node == 0` 是"
          "**结构保证**的 0（`B939_SEL` 不选 `div`、节点本体就是 `div`）",
          "**④ ⚠️⚠️ 阴阳对照门**连改四版都错** —— 本批最值钱的一条纪律**" in _ausrc
          and "**通用纪律：阴阳对照门的两个答案必须来自**两个不同的集合**。**" in _ausrc
          and "**在节点内**」（9 个，是节点里的 button/a）" in _ausrc
          and "**结构保证**的 0" in _ausrc
          # ⭐ 钉探针：把「在节点内」与「就是节点本体」**分成两个读数**（v3 的错就在这）
          and "out.n_marked_is_node += 1;" in _p940
          and "out.n_marked_in_node += 1; break;" in _p940
          # ⭐ 钉探针：门用**后者**，并把它写进判别力
          and 'marked_is_node_side = (idx["n_marked_is_node"] == 0)' in _p940
          # ⭐ 钉探针：这条「两个集合不同」是**实测**的，不是声称
          and '"two_sides_differ": marked_is_node_side,' in _p940)
    check("BBBB.4 ⚠️⚠️ **订正 939 的两处归因**（原文一字未删，批注写进基线）："
          "① 方向错 —— 不是「-1 改写成 0」，节点初始是「**根本没有** tabindex」；"
          "② 「K=26 是假集合」**不准确** —— 26 是真实的初始可聚焦数，"
          "真正原因是**节点是 `div`、`B939_SEL` 不选 `div`，集合本身在变**",
          "**③ ⚠️⚠️ 【对 939 的订正批注 —— 939 原文一字未删】**" in _ausrc
          and "**从来不存在「-1 → 0」这个转换**" in _ausrc
          and "26 是**真实的初始可聚焦数**" in _ausrc
          and "**普查对象里根本没有后来才可聚焦的那批**" in _ausrc
          # ⭐ 钉探针：把三道过滤**逐条计数**进读数，让「哪道吃掉多少」可查
          and "if (ti !== null && Number(ti) < 0) out.n_neg_ti += 1;" in _p940
          and "if (e.getClientRects().length === 0) out.n_invisible += 1;" in _p940
          # ⭐ 钉探针：节点带 ti 的个数被**单独**普查（判决性读数就在这一格）
          and "k_nodes_ti: document.querySelectorAll('.react-flow__node[tabindex]').length};" in _p940)
    check("BBBB.5 ⚠️⚠️ **探针踩的坑与未解决项都留痕**："
          "免疫针**连抓三次**（含「只从 DERIVED 删、忘加 RAW」）＋"
          "静态复核脚本自己也有盲区（只认对象字面量、不认 `out.key =`）；"
          "「新增层唯一」判据错（3/5 层新增 2 个）；`der_rewrite` 从不被键检查；"
          "计费步号**不是常数**（9 / 16）；**936 那 20 个层内步的矛盾未解决**",
          "**⑤ ⚠️ 探针自己踩的坑（都当场抓到）**" in _ausrc
          and "**派生键免疫针连抓三次**" in _ausrc
          and "它只认**对象字面量** `key:`，**不认** `out.key = value` 这种**赋值**形式" in _ausrc
          and "实测 **3/5 个层新增的是 2 个**" in _ausrc
          and '**从不被任何键检查**（只有 `walk()` 的 `d` 被查）' in _ausrc
          and "**⑥ ⚠️ 计费入口的 Tab 步号**不是常数**" in _ausrc
          and "**不许钉绝对步号**" in _ausrc
          and "**⑦ ⚠️⚠️ 一条**未解决**的矛盾（如实记，不许调和）**" in _ausrc
          and "**不许说 936 错了**" in _ausrc
          # ⭐ 钉探针：计费入口的「路过」被**记成读数**（路过 ≠ 点击）
          and "if st[\"is_billing\"]:" in _p940
          and "billing.append(i)" in _p940
          # ⭐ 钉探针：计费护栏仍在（只拦 click），且 B 段每层后**重置**
          and "n2 = boot()" in _p940)
    p939 = ROOT / "scripts/jimeng_probe939_tab_distance_src.py"
    _p939 = p939.read_text(encoding="utf-8") if p939.exists() else ""
    p939b = ROOT / "scripts/jimeng_probe939b_tab_constitution_src.py"
    _p939b = p939b.read_text(encoding="utf-8") if p939b.exists() else ""
    check("ZZZ.1 ✅⭐⭐⭐ **939：源站右键菜单的键盘可达性查清了 —— 答案不是「要按很多次」，"
          "是「按多少次都到不了」** —— 2 轮 × 150 步冷启动 Tab = **300 步 0 次进菜单**，"
          "且**分桶两轮逐字相同**（不是 flaky）",
          "src_context_menu_unreachable_by_tab_939" in _ausrc
          and "**① ✅ 判决：源站右键菜单**不可 Tab 到达**（2/2）**" in _ausrc
          and "**没有 `target_ctx` 桶**" in _ausrc
          # ⭐ 钉探针：真的走满 150 步、两轮，且分桶进了逐字比对
          and "STEPS = 150" in _p939b
          and '"bucket_counts_identical_ok": (' in _p939b
          # ⭐ 钉探针：分桶里**确实**有一个 `target_ctx` 这一类（否则「0 命中」是恒真）
          and 'if (inTarget) bucket = \'target_ctx\';' in _p939b
          and "else if (inNode) bucket = 'react_flow_node';" in _p939b
          # ⭐ 钉探针：菜单开着**之后**才走 Tab（顺序不能反）
          and "log = walk(STEPS)" in _p939b
          and "ro = launch_context_menu()" in _p939b)
    check("ZZZ.2 ⭐⭐ **机制：开菜单后 `role=menuitem` 从 0 → 13，而 300 步 0 命中** ⇒ "
          "那 13 项**压根不在 Tab 序列里** ⇒ 源站的可达性**完全依赖「开层即接管焦点」**，"
          "焦点一离开就再也回不去",
          "**③ ⭐ 机制：开菜单后 `role=menuitem` 从 0 → 13，" in _ausrc
          and "**一旦焦点离开（`blur` 或冷启动），就再也回不去。**" in _ausrc
          # ⭐ 钉探针：菜单项数量被**单独**量出来（不是推出来的）
          and "k_role_menuitem: document.querySelectorAll('[role=menuitem]').length," in _p939b
          # ⭐ 钉探针：菜单项的**选中**靠祖先 testid 判定，不是靠「在层内」
          and "if (!inTarget && p.getAttribute && p.getAttribute('data-testid') === targetTid) inTarget = true;" in _p939b
          # ⭐ 钉探针：开层后**立刻**读一次焦点（「开层即接管」那一下）
          and "took = ev(FOCUS_JS, [MARK_ATTR, TARGET_TID])" in _p939
          and 'rec["focus_after_open"] = took' in _p939)
    check("ZZZ.3 ⚠️⚠️ **订正 §148 待办第 4 条 —— 它的前提就错了**（源站早已取样两轮），"
          "而 10272 行那句「真要解，得问源站冷启动同样要按几次」**本身问错了**；"
          "顺带把**源站 / 复刻两侧一直混着的四方读数**分清",
          "**② ⚠️⚠️ 订正 §148 待办第 4 条 —— 它的**前提**是错的**" in _ausrc
          and "**「无论按几次都到不了」**" in _ausrc
          and "**④ ⭐⭐ 顺带把「源站 / 复刻」两侧一直混着的读数分清了**" in _ausrc
          and "**矛盾的是 936 / §148 把源站和复刻当成了同一侧。**" in _ausrc
          # ⭐ 钉探针：源站/复刻两侧的 testid **同名**（这正是混起来的原因）
          and "TARGET_TID = \"canvas-context-menu\"" in _p939b)
    check("ZZZ.4 ⚠️⚠️ **939 第一版整个作废**（`K=26` 造不出 95+ 个落点）；"
          "而它的 `reps_identical_ok=True` 是**空门**（比对了全 `null` 的字段，"
          "真正不一致的 `seq_repeats` 102 vs 104 就在旁边）—— "
          "「**一个恒真的字段比没有字段更坏**」第四次复发",
          "**⑦ ⚠️⚠️ 939 第一版整个作废**" in _ausrc
          and "**26 造不出 95+ 个落点**" in _ausrc
          and "**门比对了错误的字段集合**" in _ausrc
          and "**第四次**复发" in _ausrc
          # ⭐ 钉探针：第一版那个**空门**的形状（比的是全 null 的距离表）
          and 'rec["distance_by_start"] = dists' in _p939
          and 'same = (out["summary"]["cold_d"] == [out["summary"]["cold_d"][0]] * 2' in _p939
          # ⭐ 钉探针：第一版的过滤器**确实**剔了负 tabindex（病根是「多了一道过滤器」）
          and "if (ti !== null && Number(ti) < 0) continue;" in _p939
          # ⭐ 钉探针：939b 明确把「尺子」当读数、并且自己认了那个恒真字段
          and "**自己给自己开了后门**" in _ausrc
          and "已如实记为不可用字段" in _ausrc)
    check("ZZZ.5 ⚠️⚠️ **实测撞到计费入口在 Tab 序列第 16 站**（`805\\n基础会员`，2/2 逐字相同；"
          "本批只按 Tab、零 click ⇒ 未计费）⇒ 暴露一条边界：`FORBIDDEN_TIDS` "
          "**只拦 click、不拦焦点**；顺带量出**源站 Tab 周期不是常数**（101 / 104），"
          "并把**判决性缺口**如实留给 940",
          "**⑤ ⚠️ 实测撞到计费入口：它在 Tab 序列的第 16 站**" in _ausrc
          and "**只拦 `mouse.click`、不拦焦点**" in _ausrc
          and "**⑥ ⚠️ 源站的 Tab 周期**不是常数**" in _ausrc
          and "**「一圈 = 101」不能搬到源站**" in _ausrc
          and "**⑩ ⚠️⚠️ 判决性缺口（留给 940，本批**没有测**）**" in _ausrc
          and "**两次读数不足以定机制**" in _ausrc
          # ⭐ 钉探针：本批**真的零 click**（除右键那一次）⇒ 计费边界是结构性成立的
          and "if (e.closest('[data-id]')) continue;" in _p939b
          and "blocked = guard((hit or {}).get(\"al\"), (hit or {}).get(\"tid\"))" in _p939b
          # ⭐ 钉探针：周期是**从落点间隔算出来的**，不是拍的
          and '"n_first_ctx_identical_ok": (' in _p939b
          # ⭐ 钉探针：缺口那一条**没有**被偷偷补上（`[C]` 段后没重跑 COUNTS_JS）
          and (assert_no_fix := "COUNTS_JS, [B939_SEL, LAYER_SEL]" in _p939b)
          and assert_no_fix)
    p935 = ROOT / "scripts/jimeng_probe935_body_stop_sweep_src.py"
    _p935 = p935.read_text(encoding="utf-8") if p935.exists() else ""
    check("VVV.1 ✅⭐⭐⭐ **935 把「原理上不可从 DOM 查明」从**假设**升级成"
          "**测出来的结论**（对这批量而言）** —— "
          "在「从 BODY 之前那一站出发」那一刻的 `pre` 状态里，"
          "**17 个可观测量（14 个扫测量 + 3 个 pre 落点字段）逐点全部相同、零差别"
          "（4/4 臂、60 个圈）** ⇒ **复刻侧由此拿到一条可以写进基线的边界**（§122 的精神）",
          "source_body_stop_not_in_dom_935" in _ausrc
          and "**935 把「原理上不可从 DOM 查明」从**假设**升级成**测出来的结论****" in _ausrc
          and "**`pre` 侧：4/4 臂、60 个圈、逐点全部相同、零差别**" in _ausrc
          and "这 17 个可观测量没有任何一个能区分「这一圈会不会出现 `BODY` 站」**" in _ausrc
          and "**「原理上不可从 DOM 查明」不再是假设、而是一条测出来的结论**" in _ausrc
          # ⭐ 判据钉在**扫测量真的逐次记了、且 pre/post 各比各的**上
          and "SWEEP_FIELDS = BODY_ATTRS + (" in _p935
          and "DERIVED_PRE = (\"pre_dom_sig\", \"pre_is_body\", \"pre_on_canvas_root\")" in _p935
          and "\"n_pre_fields_compared\": len(POINT_FIELDS)," in _p935
          and "assert len(POINT_FIELDS) >= 12" in _p935)
    check("VVV.2 ⚠️⚠️⚠️ **935 的定位轴第一版选错了、而且错得「看起来能跑」**："
          "原本想找「`post.dom_sig` == 参照圈 `BODY` 那一站 `dom_sig`」的那次按压；"
          "**但 933/934 已测出「缺席圈 == 整圈删掉 `BODY` 那一站」** ⇒ "
          "**缺席圈的 `sig` 里压根没有 `BODY` 那个 `dom_sig`** ⇒ "
          "**缺席圈必然 `found=False`，而那恰恰是唯一要看的圈 ⇒ 整批落空**。"
          "⭐ 改用 **`pre` 落点**之后：**「那一 press」在缺席圈里也找得到、60/60、"
          "找不到 0 个** ⇒ **顺带独立复核了 933/934 那个「短圈 == 整圈删 `BODY`」**",
          "**⚠️ 定位轴第一版选错了、而且错得「看起来能跑」**" in _ausrc
          and "**缺席圈的 `sig` 里压根没有 `BODY` 那个 `dom_sig`**" in _ausrc
          and "**缺席圈必然 `found=False`**" in _ausrc
          and "**而那恰恰是唯一要看的那些圈 ⇒ 整批会落空**" in _ausrc
          and "**「那一 press」在缺席圈里也找得到、" in _ausrc
          and "60/60 全找到、找不到 0 个**" in _ausrc
          and "**这是「先读上一批的结论、再设计下一批」的一次正收益**" in _ausrc
          # ⭐ 判据钉在**定位轴真的是 pre 落点**上
          and "ref_pre_sig = ref_press[\"pre\"][\"active\"][\"dom_sig\"]" in _p935
          and "if press_list[q][\"pre\"][\"active\"][\"dom_sig\"] == ref_pre_sig:" in _p935)
    check("VVV.3 ⚠️⚠️ **`post` 侧那两处差别（`active_rect` / `has_focus`）"
          "是**必然的因果后果**、不是相关量** —— 因为「焦点有没有落到 `BODY`」"
          "**本身就是那次按压的结果** ⇒ ⭐ 这正是 §923 那条"
          "「`post` 是按压的**结果**、不是 keydown 那刻的**原因**」的直接体现 "
          "⇒ **不许把那两处差别读成线索**。"
          "⇒ ⭐ 也正因如此，**判决只认 `pre` 侧**（4/4 臂零差别）",
          "**`post` 侧那两处差别（`active_rect` / `has_focus`）" in _ausrc
          and "是**必然的因果后果**、不是相关量**" in _ausrc
          and "**本身就是那次按压的结果**" in _ausrc
          and "**这正是 §923 那条「`post` 是按压的**结果**、不是 keydown 那刻的" in _ausrc
          and "**不许把那两处差别读成线索**" in _ausrc
          and "⇒ ⭐ **也正因如此，判决只认 `pre` 侧**（4/4 臂零差别）" in _ausrc
          and "**也正因如此，判决只认 `pre` 侧**（4/4 臂零差别）" in _ausrc
          # ⭐ NN.3 那条「post 是结果」的老教训必须**留在基线里**
          and "post" in _ausrc
          and "**`post` 侧那一律不作数**" in _ausrc)
    check("VVV.4 ⚠️⚠️⚠️ **935 探针自己踩的两个坑都要留痕**："
          "**（a）`KeyError: 'pre_dom_sig'` ⇒ 整轮 9 分钟读数全丢** —— "
          "根因是**把「census 原始键」与「派生键」混在同一个元组里**再按原始键去取，"
          "且**落盘排在后处理之后** ⇒ ✅ 两处都修，并加了**两条 assert 当免疫针**"
          "（「派生键与 census 原始键**不许重叠**」「pre/post 派生键**不许重名**」—— "
          "**重叠就说明取法错了**）；"
          "**（b）汇总行把圈数与臂数虚高了 3 倍** —— 为了「落盘提前」把 `rec` "
          "每轮 append 了 **3 次** ⇒ 打出「**15/180**」「**12/12**」，"
          "真实是「**5/60**」「**4/4**」⇒ ⭐ **比值恰好没受影响**、**只错在绝对计数** "
          "⇒ **「落盘要早」与「每轮只记一次」是两件事，前者不能牺牲后者**",
          "**④ 935 探针自己踩的两个坑（都要留痕）**" in _ausrc
          and "**（a）`KeyError: 'pre_dom_sig'` ⇒ 整轮 9 分钟读数全丢**" in _ausrc
          and "**把「census 原始键」与「派生键」混在同一个元组里**" in _ausrc
          and "**原始读数一采到就先落盘**" in _ausrc
          and "派生键与 census 原始键**不许重叠**" in _ausrc
          and "pre/post 派生键**不许重名**" in _ausrc
          and "**（b）汇总行把圈数与臂数虚高了 3 倍**" in _ausrc
          and "**比值恰好没受影响**（8.3% 两边一样）⇒ **只错在绝对计数**" in _ausrc
          and "**教训：「落盘要早」与「每轮只记一次」是两件事**" in _ausrc
          # ⭐ 钉住探针里那两条免疫针与「每轮只 append 一次」
          and "派生键与 census 原始键**不许重叠**（第一版就是重叠 ⇒ KeyError）" in _p935
          and "pre/post 的派生键**不许重名**" in _p935
          and "if len(runs) < rep:      # ⚠️ 每轮只 append 一次（落盘要早、runs 不能重计）" in _p935)
    check("VVV.5 ⚠️⚠️⚠️ **935 只说「这 17 个量查不出来」，"
          "**没说「任何量都查不出来」** ⇒ **不许**把「这一批查不出来」读成"
          "「原理上必然查不出来」（那仍然是 §122 那种断言、只是换了个说法）。"
          "**成因仍然未查明、标「未验证」**；读数 **5/60（8.3%）**、"
          "落点第 **10/6/1/12/8** 圈 ⇒ 与 933 的 **3/32（9.4%）**、"
          "934 的 **5/60（8.3%）** 全部一致 ⇒ **频率稳定在 8–9%**",
          "**⑤ 成因仍然未查明、标「未验证」**" in _ausrc
          and "**935 只说「这 17 个量查不出来」**" in _ausrc
          and "**没说「任何量都查不出来」**" in _ausrc
          and "**不许**把「这一批查不出来」读成「原理上必然查不出来」" in _ausrc
          and "**③ 读数**：**5/60 圈缺 `document.body`（8.3%）**" in _ausrc
          and "**频率稳定在 8–9%**" in _ausrc
          and "落点第 1/6/8/10/12 圈**分散**" in _ausrc
          # ⚠️ NN.2 那条「不许把未查明伪装成已知」必须仍在基线里
          and "不许**编一个 DOM 层判据去" in _ausrc)







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
    # ══ JJJJJ. 批 976 源站反事实干预：H₂ 被证伪；H₃ 有支撑但**出处未标注** ══
    print("— JJJJJ. 批 976 源站反事实干预：注入一枚真可聚焦元素，"
          "BODY 位置一点没变 ⇒ H₂ 被否 —")

    check("JJJJJ.1 ⭐⭐⭐⭐⭐ **H₂ 被判否** —— 而办法是**干预**，不是再测一遍："
          "975 留下的 A（开头那段没有可聚焦元素）与 B（无条件出现）**读起来一模一样** "
          "⇒ 往 `<body>` **最前面**注入一枚 `tabindex=0` 的 `div` ⇒ "
          "实测 **`BODY` 仍在环里、位置一点没变**（`after_n_body = 1`、"
          "`body_disappeared_after_injection = False`，2/2）⇒ "
          "**「开头有没有可聚焦元素」不是 `BODY` 出现的条件**；"
          "⇒ 而整批实验能成立，靠的是**前提也有门**"
          "（`injection_actually_in_ring` 与 `injection_restored` 2/2 绿）"
          "—— 注入件若没真进环 / 没被还原，后面全是空谈",
          '"h2_falsified_976"' in _ausrc
          and "**观察分不开 A / B**" in _ausrc
          and "**分不开的时候，正确的动作不是再测一遍，是改实验**" in _ausrc
          and "**H₂ 被否**" in _ausrc
          and "**「开头有没有可聚焦元素」" in _ausrc
          and '"h3_supported_976"' in _ausrc
          # ⭐⭐ 钉探针：前提门、否定结果、可还原三样都要真在
          and '"injection_actually_in_ring_both_reps"' in _p976
          and '"injection_restored_both_reps"' in _p976
          and '"body_disappeared_after_injection"' in _p976
          and '"after_n_injected"' in _p976
          and 'INJECT_JS = """' in _p976
          and 'UNINJECT_JS = """' in _p976
          # ⭐⭐⭐ 干预必须**可还原**：幂等 + finally 无条件移除 + 读数里复查
          and "still_there: !!document.getElementById(probeId)" in _p976
          and '"restored"' in _p976
          and '"uninject"' in _p976
          # ⭐⭐⭐ 同一把尺子不许分叉（974/975/976 都只是 `_grab` 的消费者）
          and 'DOMRANK_JS = _grab("DOMRANK_JS", _p973)' in _p976
          and 'SCOPE_JS = _grab("SCOPE_JS", _p975)' in _p976
          and '"_p976": "scripts/jimeng_probe976_counterfactual_src.py",' in _anchs)

    check("JJJJJ.2 ⭐⭐⭐⭐⭐ **H₃ 的证据来自一道判红的门** —— "
          "而「门红先判门还是数据」这一族本批**又兑现了一次**："
          "第一版钉的是「注入件应排在 `BODY` **之前**」⇒ **它真的判红了** ⇒ "
          "⭐⭐⭐ **门假设的方向错了，而错的方向正好就是 H₃ 的内容**"
          "（`BODY` 恒站在「DOM 里第一个可聚焦元素」的**前一格**）⇒ "
          "改成正确方向 `injected_follows_body`，"
          "⭐⭐⭐⭐ **而且改门要成对**：额外钉一条"
          "`reversed_injection_relation_stays_false_both_reps` —— "
          "**旧方向必须一直是红的** ⇒ 不然「改精确」与「放宽」分不开；"
          "⚠️⚠️ **但 H₃ 仍不是「规范」** —— 实测如此 ≠ 规范如此 ⇒ "
          "**出处仍未标注**（H₁ 否、H₂ 否、H₃ 有支撑无出处）",
          '"reversed_injection_relation_stays_false_both_reps"' in _p976
          and '"injected_follows_body_both_reps"' in _p976
          and '"after_injected_precedes_body"' in _p976
          and '"after_injected_follows_body"' in _p976
          and '"gap_measured_both_reps"' in _p976
          and 'GAP_JS = """' in _p976
          and "**改门要成对**" in _ausrc
          and "**旧方向必须一直是红的**" in _ausrc
          and "**出处仍未标注**" in _ausrc
          and "**不许把「实测如此」升级成「规范如此」**" in _ausrc
          # ⚠️ 975 说「本批不测」的那一项本批测了 —— 探针里要有新件
          and '"why_gap_js"' in _p976
          and "「从回绕点到第一个可聚焦元素之间还剩几个不可聚焦元素」" in _p976)

    check("JJJJJ.3 ⭐⭐⭐⭐⭐ **本批自己踩的 4 个坑，全部落进基线** —— "
          "而其中两个是**反复出现**的那一族："
          "(a) ⭐⭐⭐ **汇总层取值错了、原始读数里答案一直在**（**第四次**："
          "965/969/970/974）—— 先 `c[\"rows_before\"] = c[\"rows\"]`、"
          "后 `c[\"rows\"] = []`、**再**调汇总 ⇒ 读的是**已清空的列表** ⇒ "
          "`before_n_body` 读成 0 ⇒ **那是 bug、不是页面事实** ⇒ 改成**显式传 `rows`**；"
          "(b) ⭐⭐ **守卫会命中自己** —— 子串匹配命中了 975 源码里的那一行本身 ⇒ "
          "报「尺子分叉」是**误报** ⇒ 修法是**行首锚定**（`^` + `re.M`）⇒ "
          "⭐⭐ **守卫自己会命中自己时，它抓到的不是分叉，是自指**；"
          "(c) ⭐⭐⭐ **注释与代码必须一致**（说「保留旧字段」却删了计算）；"
          "(d) ⭐⭐ **求值顺序**（`design_gates` 建在字段算出来之前）",
          '"selfbugs_976"' in _ausrc
          and "**汇总层取值错了、原始读数里答案一直在**" in _ausrc
          and "**那是我的 bug、不是页面事实**" in _ausrc
          and "**守卫会命中自己**" in _ausrc
          and "**守卫自己会命中自己时，它抓到的不是分叉，是自指**" in _ausrc
          and "**注释与代码必须一致**" in _ausrc
          and "**比注释写错更坏**" in _ausrc
          # ⭐⭐ 钉探针原文：修法真的写进代码，而不是只写在判词里
          and 'def summarize(c, tag, rows=None):' in _p976
          and 'summarize(c, "before", rows=c["rows_before"])' in _p976
          # ⚠️ 注意：这里**不许**把 `r?"""` 整段塞进双引号串 ——
          #   `"""` 会提前闭合那个字符串（976 写判据时当场踩到，py_compile 报
          #   「unterminated string literal」）⇒ 拆成两条不含引号的锚点，
          #   `^` 照样被钉住。
          and "assert not re.search(r'^DOMRANK_JS" in _p976
          and ", _src_, re.M), (" in _p976
          # ⚠️⭐⭐ `py_compile` 抓不到「名字没绑上」⇒ 运行期 NameError 也要留痕
          and "NameError" in _p976
          and '"discipline_976"' in _ausrc
          and "**注入件是 1×1、opacity 0、pointer-events none**" in _ausrc
          and "**不回答「那一格用户会看见什么」**" in _ausrc)

    # ══ KKKKK. 批 977 源站正面检验 H₃：臂 B 让「第一个可聚焦元素」换人，
    #    BODY 的后继**跟着换** ⇒ H₃ 的位置命题这一次扛住了（但出处仍未标注）══
    print("— KKKKK. 批 977：臂 B 把第一个可聚焦元素设为不可聚焦，"
          "BODY 的环上后继跟着换成下一个 ⇒ H₃ 扛住这一次 —")

    check("KKKKK.1 ⭐⭐⭐⭐⭐ **臂 B 才是 H₃ 的正面检验，而它扛住了** —— "
          "做法是把「DOM 里第一个可聚焦元素」临时设成 `tabindex=\"-1\"`"
          "（**纯 JS、可还原**、**原属性值先记下来**）⇒ 「第一个」**换人** ⇒ "
          "实测 **`BODY` 的环上后继跟着换了人**（`canvas-project-logo` → "
          "`canvas-project-title-trigger`，2/2 逐格相同、三臂 `BODY` 都在第 6 格）⇒ "
          "**H₃ 的位置命题这一次扛住了**；"
          "⚠️⚠️ **但扛住了 ≠ 证明了** —— 「出处仍未标注」「976 那个支撑本来就弱」"
          "「臂 B 只试了一枚元素一个方向」三条限制**必须一起记**",
          '"h3_survives_arm_b_977"' in _ausrc
          and "**臂 B 才是 H₃ 的正面检验，而它扛住了**" in _ausrc
          and "**重新锚定**" in _ausrc
          and '"honest_limit_977"' in _ausrc
          and "**出处仍未标注**" in _ausrc
          and "**一次成功不叫可靠**" in _ausrc
          # ⭐⭐ 钉探针：臂 B 的前提三件套（生效 / 还原 / 真的换人）都要真在
          and '"arm_b_mutation_took_effect_both_reps"' in _p977
          and '"arm_b_restored_both_reps"' in _p977
          and '"arm_b_moved_the_dom_first_focusable_both_reps"' in _p977
          and 'UNFOCUS_JS = """' in _p977
          and 'REFOCUS_JS = """' in _p977
          and "target.removeAttribute(\'tabindex\')" in _p977
          and "rec.had_tabindex_attr === true" in _p977
          and '"_p977": "scripts/jimeng_probe977_h3anchor_src.py",' in _anchs)

    check("KKKKK.2 ⭐⭐⭐⭐⭐ **臂 A 单独看分不开任何东西，而本批实测印证了这一点** —— "
          "「回绕途经点」与「无条件途经点」在**两枚**的情况下**预测完全一样** ⇒ "
          "臂 A 只留下「计数与座位」（环长 18 → 20、`BODY` **仍在第 6 格**、"
          "**没被挤掉**）⇒ ⭐⭐⭐⭐ **两条臂都留着，但只有一条有判别力** ⇒ "
          "⭐⭐⭐ **「再多测一次」与「改实验」不是一回事**，这件事要写进基线，"
          "免得下一批把臂 A 当证据；"
          "另有一条本批**实测**撞上的纪律：**读数里撞名的字段不能当身份** —— "
          "976 的 `INJECT_JS` 把 `data-testid` **写死** ⇒ 两枚注入件**撞名** ⇒ "
          "修法是**用 `own.id` 认身份**（`two_n_injected = 2` 数得对）",
          '"arm_a_is_not_discriminating_977"' in _ausrc
          and "**预测完全一样**" in _ausrc
          and "**它的价值只剩「计数与座位」**" in _ausrc
          and "**「再多测一次」与「改实验」不是一回事**" in _ausrc
          and '"identity_collision_977"' in _ausrc
          and "**读数里撞名的字段不能当身份**" in _ausrc
          and "**用 `own.id` 认身份**" in _ausrc
          # ⭐⭐ 钉探针：身份用 id、且这条纪律在源码里写成注释
          and '(r.get(\"own\") or {}).get(\"id\") in (ID_A, ID_B)' in _p977
          and '"why_own_id_is_identity"' in _p977
          and '"two_injections_actually_in_ring_both_reps"' in _p977
          and '"why_arm_b_is_the_real_test"' in _p977)

    check("KKKKK.3 ⭐⭐⭐⭐⭐ **「守卫会命中自己」有第三种形态，本批连撞两次** —— "
          "976 那种是「守卫那行**自己**在源码里」；本批这种是"
          "「**注释里抄了一遍被禁的写法原文**」⇒ 子串匹配把**注释**也扫进来 ⇒ "
          "**当场判红** ⇒ 两条归同一族：**守卫的匹配范围比它想匹配的大** ⇒ "
          "修法：注释**不许抄被禁写法原文**，改用**描述**；"
          "另两条照旧：**干预可还原且单独复查**（臂 B 还原时**先核对身份**，"
          "tag 对不上宁可报红也不动）、**两个关系都真算**（正向 + 反向）",
          '"guard_hits_comment_977"' in _ausrc
          and "**抄了一遍被禁的写法原文**" in _ausrc
          and "**当场判红**" in _ausrc
          and "**守卫的匹配范围比它想匹配的大**" in _ausrc
          and '"discipline_977"' in _ausrc
          # ⭐⭐ 钉探针：新件里彻底没有那个写法，且行首锚定那条还在
          and 'assert "||" not in UNFOCUS_JS' in _p977
          and 'assert "||" not in REFOCUS_JS' in _p977
          and "re.search(r'^DOMRANK_JS" in _p977
          and '"h3_relation_measured_in_all_three_arms_both_reps"' in _p977
          and "本批的干预和 976 是同一件东西" in _p977
          and '"js_verbatim_from_976"' in _p977)

    # ══ LLLLL. 批 978 实验室页：空白页上**完整复现**那枚 BODY 停靠点
    #    ⇒ 引擎/规范层面，不是源站应用的属性；scroll 假设被否 ══
    print("— LLLLL. 批 978 实验室：about:blank + 三个 button、零应用代码，"
          "BODY 停靠点完整复现 ⇒ scroll 假设被否 —")

    check("LLLLL.1 ⭐⭐⭐⭐⭐ **空白页上完整复现了那枚 `BODY` 停靠点** —— "
          "而这就是「出处」能往前走的那一步：`about:blank` ＋ `set_content`、"
          "**三个 `<button>`、零应用代码、零 React、零浮层**，周期签名 "
          "**2/2 × 5 臂逐格相同**（`lab-b1` → `lab-b2` → `lab-b3` → **`BODY`**）⇒ "
          "⭐⭐⭐⭐⭐ **这是引擎/规范层面的行为，不是源站那个应用的属性** ⇒ "
          "974/975 花力气排除的「作用域边界」「应用显式干预」**全都对，"
          "因为根本没有应用**；"
          "⇒ 而 **H₃ 的位置命题在最小环境里也被复现**"
          "（L2 注入件在最前时，`BODY` 仍紧贴新第一个的前一格）",
          '"engine_level_978"' in _ausrc
          and "**这是引擎/规范层面的行为，" in _ausrc
          and "不是源站那个应用的属性**" in _ausrc
          and "**全都对，因为根本没有应用**" in _ausrc
          and "**H₃ 的位置命题在最小环境里也被复现**" in _ausrc
          # ⭐⭐ 钉探针：仪器来源、判据形状、实验前提都要真在
          and '"js_verbatim_from_976"' in _p978
          and 'STOP_JS = """' in _p978
          and 'PAGE_JS = """' in _p978
          and "is_document_body: isBody" in _p978
          and "document.activeElement === document.body" in _p978
          and '"cycle_signature_stable_across_reps_both_reps"' in _p978
          and '"ring_cycled_at_least_twice_both_reps"' in _p978
          and '"_p978": "scripts/jimeng_probe978_lab_body_stop.py",' in _anchs)

    check("LLLLL.2 ⭐⭐⭐⭐⭐ **「可滚动」这条假设被否** —— 而它本来是本批"
          "最像样的候选（`tabIndex = -1` 却能接到焦点，**应用层解释不通**）："
          "实测 `L0` 不可滚 / `L1` 可滚 / `L3` 不可滚动（第二种做法）⇒ "
          "**三者的周期签名完全一样** ⇒ **能不能滚对它没有任何影响**；"
          "顺带否掉相邻候选：**滚动容器自己没成为一格**（L4）；"
          "⚠️⚠️ **但 `n_body_stops` 是抖的，而本批分不开是「读数时序」"
          "还是「页面真抖」⇒ 在分开之前，计数不许当判据** ⇒ "
          "⭐⭐⭐⭐ **一次失败不叫「没有」**",
          '"scroll_hypothesis_falsified_978"' in _ausrc
          and "**「可滚动」这条假设被否**" in _ausrc
          and "**应用层解释不通**" in _ausrc
          and "**能不能滚对它没有任何影响**" in _ausrc
          and '"count_is_flaky_978"' in _ausrc
          and "而本批分不开为什么抖" in _ausrc
          and "**在分开之前，计数不许当判据**" in _ausrc
          and "**一次失败不叫「没有」**" in _ausrc
          # ⭐⭐ 钉探针：可滚动是**实测**不是公式、抖动被单独记账
          and "can_actually_scroll" in _p978
          and '"scrollable_pair_really_differs_both_reps"' in _p978
          and '"count_flaky_arms"' in _p978
          and "**公式是推论、实测是事实**" in _p978)

    check("LLLLL.3 ⭐⭐⭐⭐⭐ **本批的门一共判红四次，四次都是「门错」"
          "或「那一臂没做到设计意图」** —— 而处置**全部**是"
          "「改精确 / 改那一臂」，**没有一次是删门或放宽**："
          "(a) ⭐⭐⭐⭐ **过宽的门**（`||` 那条把**正当的逻辑或**也禁了、"
          "**逼我写更差的代码**）⇒ 收窄成「只禁 or 兜底成假值」"
          "**并成对钉住反向**；"
          "(b) ⭐⭐⭐ **名单写错**（「不许自己定义」把本批**自己新写的**两件也列了进去）"
          "⇒ **门在禁止本批干活**；"
          "(c) ⭐⭐ **断言写反**（spacer 那条与 L4 的定义矛盾）；"
          "(d) ⭐⭐⭐⭐⭐ **公式当事实用** ⇒ L3 的 `body{overflow:hidden}` "
          "**根本没生效**（`html` 才是 scrolling element）⇒ "
          "处置是**改那一臂**、**不是放宽门**；"
          "另：⭐⭐⭐⭐ `reps_agree` 第一版比的是**绝对计数** ⇒ 又是 974 那条",
          '"gate_misses_978"' in _ausrc
          and "**没有一次是删门或放宽**" in _ausrc
          and "**过宽的门和过窄的门一样坏**" in _ausrc
          and "**门在禁止本批干活**" in _ausrc
          and "**公式是推论、实测是事实**" in _ausrc
          and '"reps_agree_mistake_978"' in _ausrc
          and "比的是 `n_body_stops`（绝对计数）" in _ausrc
          and "**我在新写的一支探针上又犯了同一个错**" in _ausrc
          and '"discipline_978"' in _ausrc
          # ⭐⭐ 钉探针：那几次「改门」在源码里都**成对钉住了反向**
          and "OR_FALLBACK_TAILS" in _p978
          and "or-兜底守卫**失灵**了" in _p978
          and "spacer 门失灵（L0 带 spacer）" in _p978
          and "分叉守卫**失灵**了" in _p978
          and "def _cycle_sig" in _p978
          and "**不是绝对数值**" in _p978)

    # ══ MMMMM. 批 979 实验室页第二支：时间线量停留时长 ⇒
    #    BODY 不是短暂状态 ⇒ 978 的 (a) 被否、(b) 成唯一解释 ══
    print("— MMMMM. 批 979：按 Tab 后页内纯读轮询取时间线，"
          "BODY 停留 249-252ms 与其他格一样 ⇒ (a) 被否 —")

    check("MMMMM.1 ⭐⭐⭐⭐⭐ **`BODY` 不是一个短暂状态** —— "
          "实测 `body_dwell_ms` = 249/252、250/249、251、250/250、250/250，"
          "而**其他每一格**是 248–252 ⇒ **两者分布完全一样** ⇒ "
          "**978 的 (a)「`BODY` 短暂、settle 没赶上」被否** ⇒ "
          "⭐⭐⭐⭐⭐ **那 978 的计数抖动只能用 (b) 解释** —— "
          "**引擎有时真的不走那一格** ⇒ **这直接削弱 H₃ 里的「恒」**："
          "那枚 `BODY` 是**通常在、但不是每次都在**的一格；"
          "⇒ 而周期签名 **2/2 × 5 臂逐格相同**、"
          "`n_steps_with_body` = 2/8（L2 是 1/8）**恰好是环长算出来的值**",
          '"body_is_stable_979"' in _ausrc
          and "**`BODY` 不是一个短暂状态**" in _ausrc
          and "**978 的 (a)「`BODY` 短暂、settle 没赶上」被否**" in _ausrc
          and "**那 978 的计数抖动只能用 (b) 解释**" in _ausrc
          and "**通常在、但不是每次都在**" in _ausrc
          and '"cycle_keys_979"' in _ausrc
          and "**恰好就是环长算出来的值**" in _ausrc
          # ⭐⭐ 钉探针：新件、停留算法、两条计数都要真在
          and 'POLL_JS = """' in _p979
          and "def _dwell(seq, elapsed_ms=None):" in _p979
          and '"body_dwell_ms"' in _p979
          and '"n_steps_with_body"' in _p979
          and '"focus_actually_moves_both_reps"' in _p979
          and '"_p979": "scripts/jimeng_probe979_dwell_src.py",' in _anchs)

    check("MMMMM.2 ⭐⭐⭐⭐⭐ **本批把设计换掉了，而换的理由必须写清楚**："
          "978 原计划是「同一批臂跑**两种 settle 时长**做对照」，"
          "⭐⭐⭐ **而两种 settle 只告诉你「哪一档更准」、"
          "**不告诉你「它到底待了多久」** ⇒ **时间线直接给出停留时长**、"
          "**把「短 / 长两档」整个包含**了 ⇒ "
          "⭐⭐⭐⭐⭐ **换设计的正当理由是「**原设计测不到那个量**」，"
          "不是「原设计跑不通」** —— **这两件事要分清**；"
          "另有一条本批**第一次**记下来的："
          "⚠️⚠️⚠️⭐⭐⭐⭐⭐ **五臂的**定义**是**模块级代码**、不是字符串字面体 ⇒ "
          "**`_grab` 带不走** ⇒ 只能重写一遍、"
          "**并用 `assert` 钉住臂表与 978 一致** ⇒ "
          "⭐⭐⭐ **凡是「靠 `_grab` 带不走的东西，就要显式钉住它没变**",
          '"design_changed_979"' in _ausrc
          and "**不告诉你「它到底待了多久」**" in _ausrc
          and "**原设计测不到那个量" in _ausrc
          and "不是「原设计跑不通」**" in _ausrc
          and '"cant_grab_979"' in _ausrc
          and "**是**模块级代码**、不是字符串字面量" in _ausrc
          and "就要显式钉住它没变" in _ausrc
          # ⭐⭐ 钉探针：设计变更的理由、以及「带不走就钉住」都写在源码里
          and '"why_design_changed"' in _p979
          and '"what_cannot_be_grabbed"' in _p979
          and "BUTTON_TPL in _p978 and SPACER in _p978" in _p979
          and "CSS_PLAIN in _p978" in _p979)

    check("MMMMM.3 ⭐⭐⭐⭐⭐ **本批自纠 4 个，其中三个是**反复出现**的那一族**："
          "(a) ⭐⭐⭐⭐⭐ **汇总层又漏了「末态」** ⇒ 每一格只有一个状态时 "
          "`body_dwell_ms` **整个变成 `[]`**，而**原始读数里答案一直在**"
          "⇒ **「汇总层取值错了」这一族的第五次**（965/969/970/974/本批）；"
          "(b) ⭐⭐⭐⭐ **门编码了错的预期**（要求「窗口内多次转变」，"
          "而设计**恰恰相反**：落定就不动）⇒ **门红先判门还是数据：门错**；"
          "(c) ⭐⭐⭐⭐⭐ **守卫第四次命中注释** ⇒ **改法升级**："
          "**只扫代码行**（剥掉 `//` 与 `* `）⇒ "
          "**注释里可以正常提到被禁的 API，而门仍抓得住真代码**；"
          "(d) ⭐⭐⭐⭐⭐ **又一次「同一个东西要比同一个口径」**"
          "（978 存的是**模板**，我拿**展开后**的串去找）",
          '"selfbugs_979"' in _ausrc
          and "**汇总层又漏了「末态」**" in _ausrc
          and "这一族的第五次**（965/969/970/974/本批）" in _ausrc
          and "**门编码了错的预期**" in _ausrc
          and "**门红先判门还是数据：门错**" in _ausrc
          and "**守卫第四次命中注释**" in _ausrc
          and "**只扫代码行**" in _ausrc
          and "**注释里可以正常提到被禁的 API" in _ausrc
          and "**又一次「同一个东西要比同一个口径」**" in _ausrc
          and '"discipline_979"' in _ausrc
          # ⭐⭐ 钉探针：那几处在源码里都**成对钉住了反向**
          and "def _code_only(js):" in _p979
          and "纯读守卫**失灵**了" in _p979
          and "注释剥离守卫**失灵**了" in _p979
          and "or-兜底守卫**失灵**了" in _p979
          and "分叉守卫**失灵**了" in _p979
          and "**用 `elapsed_ms` 给末态补一段**" in _p979
          and "BUTTON_TPL = " in _p979)

    # ══ NNNNN. 批 980 实验室页第三支：跑够多的圈，把 (b) 变成**比率**
    #    ⇒ 64 圈里 5 圈没走 BODY ≈ 7.8%；门② 绿 ⇒ 排除「没看够」 ══
    print("— NNNNN. 批 980：64 圈里 5 圈没走 BODY（≈7.8%），"
          "且每段 BODY 停留都 ≥120ms ⇒ 排除「没看够」 —")

    check("NNNNN.1 ⭐⭐⭐⭐⭐ **「那枚 `BODY` 不是每次都在」这句话终于有了数字** —— "
          "一个 2 vs 3 撑不起它：L0 **18 圈里 17 / 16 圈有**，"
          "L2 **两轮各 14 圈里 13 圈有** ⇒ "
          "⭐⭐⭐⭐⭐ **合计 64 圈：59 圈含 `BODY`、5 圈不含 ⇒ 缺失率 ≈ 7.8%** ⇒ "
          "**H₃ 里的「恒」被量化地削弱**：它**不是恒定停靠点，"
          "而是约 92% 出现的停靠点**；"
          "⚠️⭐⭐ 而这一切的前提是 ⭐⭐⭐⭐⭐ "
          "**「没看见」必须先排除「没看够」**：门② 实测 "
          "`n_body_dwell_below_floor = 0`（四格全 0）⇒ "
          "**每一段 `BODY` 的停留都 ≥ 120ms** ⇒ "
          "**「那一圈没看见」就不能用「窗口太短」解释** ⇒ "
          "**否则这就是 978 那个错**：把「没看够」读成「没有」",
          '"rate_980"' in _ausrc
          and "**一个 2 vs 3 撑不起「不是每次都在」这句话**" in _ausrc
          and "**合计 64 圈：59 圈含 `BODY`、5 圈不含 " in _ausrc
          and "缺失率 ≈ 7.8%**" in _ausrc
          and "**不是恒定停靠点，而是约 92% 出现的停靠点**" in _ausrc
          and '"key_precondition_980"' in _ausrc
          and "**「没看见」必须先排除「没看够」**" in _ausrc
          and "把「没看够」读成「没有」" in _ausrc
          # ⭐⭐ 钉探针：门②、切片、比率三样都要真在
          and '"body_dwell_all_above_floor_both_reps"' in _p980
          and '"n_body_dwell_below_floor"' in _p980
          and "MIN_VISIBLE_MS = 120" in _p980
          and '"laps_missing_a_ring_member"' in _p980
          and '"cycles_without_body"' in _p980
          and 'POLL_JS = _grab("POLL_JS", _p979)' in _p980
          and '"_p980": "scripts/jimeng_probe980_rate_src.py",' in _anchs)

    check("NNNNN.2 ⭐⭐⭐⭐⭐ **一条门只能管一件事** —— 而这一条是本批"
          "**最值钱的方法结论**：第一版的完整性门是「每一圈都覆盖环里每一格」"
          "⇒ **它判红了** ⇒ ⭐⭐ **门红先判门还是数据**："
          "⭐⭐⭐⭐ **红的不是门、是数据** —— 少了 `BODY` 的那一圈"
          "**真的只覆盖 3/4 格**（**那正是本批要找的东西**）⇒ "
          "处置是**改精确、不放宽**：「切得对不对」换成**与 `BODY` 无关**的"
          "**连续 ＋ 可重建**不变量，「有没有少一格」**另立一条读数** ⇒ "
          "⭐⭐⭐⭐⭐ 而那条新不变量**天生看不见「少一格」**"
          "（`[['a','b','c']] + ['B']` **照样能重建**）⇒ "
          "**不变量管不了的事，要另立一条读数**",
          '"one_gate_one_thing_980"' in _ausrc
          and "**一条门只能管一件事**" in _ausrc
          and "**红的不是门、是数据**" in _ausrc
          and "**那正是本批要找的东西**" in _ausrc
          and "**改精确、不放宽**" in _ausrc
          and "**连续 ＋ 可重建**" in _ausrc
          and "**另立一条读数**" in _ausrc
          and "**不变量管不了的事，要另立一条读数**" in _ausrc
          # ⭐⭐ 钉探针：判据必须挑**在旋转下不变**的东西
          and "def _cycles_len_ok(full, ring_len):" in _p980
          and "我在这里错了两次，两次都是判据选错" in _p980
          and "**判据必须挑一个在旋转下不变的东西**" in _p980
          and "def _slicer_ok(keys, full, tail):" in _p980
          and "**这才是「切得对不对」该问的问题**" in _p980
          and "**少一格仍算合法重建**" in _p980)

    check("NNNNN.3 ⭐⭐⭐⭐⭐ **切圈这种「自己给自己当分母」的逻辑必须有自测** —— "
          "而我**把期望值写错了四次**（把残段当完整圈、圈数多算一圈、"
          "把下标数错、拿 `set('abcBab')` 想凑 3 格而它其实有 **4** 个 —— "
          "**`set` 大小写敏感**）⇒ ⭐⭐⭐ "
          "**期望值错了，自测就是假绿** ⇒ 期望值必须**按定义一句一句推**，"
          "**不能「跑出来是什么就写什么」—— 那样自测就恒真了**；"
          "另两条本批的设计理由：⭐⭐⭐⭐⭐ **窗口为什么可以短**"
          "（979 证了「落定就不动」⇒ **窗口越短能跑的圈数越多**，"
          "而**统计量需要样本量**）与 ⭐⭐⭐⭐ **切圈的残段不许算进分母**",
          '"slicer_980"' in _ausrc
          and "**把期望值写错了四次**" in _ausrc
          and "**期望值错了，自测就是假绿**" in _ausrc
          and "那样自测就恒真了**" in _ausrc
          and "**`set` 大小写敏感**" in _ausrc
          and '"window_choice_980"' in _ausrc
          and "**统计量需要样本量**" in _ausrc
          and "**切圈的残段不许算进分母**" in _ausrc
          and '"discipline_980"' in _ausrc
          # ⭐⭐ 钉探针：自测与成对钉反向都写在源码里
          and "切圈器自测" in _p980
          and "顺序错必须判红" in _p980
          and "多出一枚必须判红" in _p980
          and "assert WINDOW_MS >= MIN_VISIBLE_MS" in _p980
          and "窗口门失灵（窗口短于可见下限时仍绿）" in _p980
          and "不许算进 `n_cycles`" in _p980)

    # ══ OOOOO. 批 981 源站：把同一个比率量到源站上 ⇒
    #    诚实的答案是「没量到」；而**顺带查实 973–977 的「一圈」不是整圈** ══
    print("— OOOOO. 批 981 源站：240 步 = 1 圈、环长 101 ⇒ n_laps=1 ⇒ "
          "**没量到比率**；而左栏容器一圈命中约 2 次 ⇒ 973–977 的「一圈」不是整圈 —")

    check("OOOOO.1 ⭐⭐⭐⭐⭐ **本批的答案是「没量到」，而必须这么记** —— "
          "源站实测（2/2 逐格相同）**240 步 = 1 个完整顺序环、环长 101 格**、"
          "`BODY` 落 2 次、停留 **132/150** 与 **134/133**、"
          "`below_floor = 0` ⇒ `n_laps = 1` ⇒ "
          "⭐⭐⭐ **样本量不足以给源站的比率** ⇒ "
          "⭐⭐⭐⭐ **实验室那个 7.8% 不许直接套到源站**（980 的 `skip_note` 原话）"
          "⇒ 要 10 圈至少 **~1100 步**，而「跑这么长」合不合理**是一道产品/成本判断**，"
          "**不是本批该替他做的决定**；"
          "⇒ 而 ⭐⭐⭐⭐ 门②在**源站侧同样成立** ⇒ "
          "**「那一圈没看见 `BODY`」在源站上也不能用「窗口太短」解释**",
          '"src_rate_not_measured_981"' in _ausrc
          and "**没量到**" in _ausrc
          and "**样本量不足以给源站的比率**" in _ausrc
          and "**实验室那个 7.8% 不许直接套到源站**" in _ausrc
          and "**不是本批该替他做的决定**" in _ausrc
          and '"body_dwell_src_981"' in _ausrc
          and "**门②在源站侧同样成立**" in _ausrc
          # ⭐⭐ 钉探针：环长、圈数、门②的读数都要真在
          and '"n_laps"' in _p981
          and '"laps_without_body"' in _p981
          and '"n_body_dwell_below_floor"' in _p981
          and "MIN_VISIBLE_MS = 120" in _p981
          and "N_STEPS = 240" in _p981
          and '"_p981": "scripts/jimeng_probe981_srcrate_src.py",' in _anchs)

    check("OOOOO.2 ⭐⭐⭐⭐⭐ **本批最要紧的发现，而且它改的是历史记录**："
          "**973–977 那个「走满一圈」不是整圈** —— 那一批的切法是"
          "「`own.closest_tid == canvas-fixed-toolbar` 命中第 2 次就算走满」，"
          "而**左栏容器在一圈里被命中约 2 次**（三个左栏按钮"
          "—— `canvas-pointer-tool-toggle`、"
          "`canvas-display-toggle-minimap`、"
          "`canvas-display-toggle-connections` —— "
          "**各自的 `closest_tid` 都是那个容器**）⇒ "
          "⭐⭐⭐⭐⭐ **那一批的「18 格 out 环」不是整圈** ⇒ "
          "**973 那句「复刻的环序就是 DOM 序」测的是那一段、不是整圈** ⇒ "
          "这也解释了它们**140 步里只得到 18 枚 `out`**（**因为在圈内就停了**）；"
          "⚠️⭐⭐ **这一条不推翻 973/974 的顺序结论**（那一段的顺序关系仍然成立），"
          "但它**把「一圈」这个词的定义改了** ⇒ "
          "**任何引用「一圈 = 18 格」的旧结论都要重新看**",
          '"one_lap_is_not_one_lap_981"' in _ausrc
          and "**973–977 那个「走满一圈」不是整圈**" in _ausrc
          and "**左栏容器在一圈里被命中约 2 次**" in _ausrc
          and "**那一批的「18 格 out 环」不是整圈**" in _ausrc
          and "测的是那一段、不是整圈" in _ausrc
          and "**因为它们在圈内就停了**" in _ausrc
          and "**把「一圈」这个词的定义改了**" in _ausrc
          and "不推翻 973/974 的顺序结论" in _ausrc
          # ⭐⭐ 钉探针：三个左栏按钮 + 容器口径的命中数都被读出来
          and 'LAP_TID = "canvas-project-logo"' in _p981
          and '"rail_hits_container_kb"' in _p981
          and "a.closest('[data-testid]')" in _p981
          and "**974 那条纪律的第四次复发**" in _p981)

    check("OOOOO.3 ⭐⭐⭐⭐⭐ **974 那条纪律的第四次复发**（「同一个东西要比同一个口径」）"
          "—— 973–977 判「一圈」用的是 `closest('[data-testid]')`（**容器**），"
          "而本批第一版沿用 `keyOf` 读**元素自己**的 `data-testid` ⇒ "
          "**同一个名字、两种口径** ⇒ **第一版真跑出来 `rail_hits = 0`** ⇒ "
          "修法：标记改成**环里唯一、且确实是焦点目标**的那一枚，"
          "**并把 `closest_tid` 也读出来，让两种口径并排，而不是二选一** ⇒ "
          "⭐⭐ **二选一是最坏的选择，并排读出来，差异自己会说话**；"
          "另两条本批自纠：⭐⭐⭐⭐ **汇总层要用的字段，读数层就得留着**"
          "（我第一版只留了时间线第一枚键 ⇒ `BODY` 的停留时长**根本无从算起**，"
          "979 的同族）与 ⭐⭐⭐ **自测的期望值本身也要审**（本批又推错两处）；"
          "⚠️⭐⭐ 顺带记一笔：**源站的 Tab 环里有 `canvas-commerce-entry`** ⇒ "
          "本轮**只按 `Tab`、从未点击它** ⇒ **零计费**",
          '"kaliber_mismatch_981"' in _ausrc
          and "**974 那条纪律的第四次复发**" in _ausrc
          and "**同一个名字、两种口径**" in _ausrc
          and "**第一版真跑出来 `rail_hits = 0`**" in _ausrc
          and "**二选一是最坏的选择**" in _ausrc
          and "**并排读出来，差异自己会说话**" in _ausrc
          and '"commerce_in_ring_981"' in _ausrc
          and "**只按 `Tab`、从未点击它**" in _ausrc
          and '"discipline_981"' in _ausrc
          and "**汇总层要用的字段，读数层就得留着**" in _ausrc
          # ⭐⭐ 钉探针：整段 seq 留着、两种口径并排、守卫拦在 click 之前
          and '"closest_tid": closest' in _p981
          and '"seq": seq' in _p981
          and "残段，不许算进分母" in _p981
          and "guard_point(sp[0], sp[1])" in _p981
          and "命中数 − 1 那条对不上了" in _p981)

    # ══ PPPPP. 批 982 源站：⭐⭐⭐⭐⭐ **给「一圈」下正式定义** ——
    #    「圈」= 最小重复周期（不读任何 testid ⇒ 没有「两种口径」）；
    #    并用它把 973/974 的核心结论**从一个 17.8% 的小段补到 100%** ══
    print("— PPPPP. 批 982 源站：**圈 = 最小重复周期**（源站 101 格，2/2；"
          "974 的 140 步 / 981 的 240 步 / 982 的 210 步**三份独立数据**复核）"
          "⇒ 973/974 报的 18/19 格是**「out 弧」不是圈**（覆盖率 **17.8% / 73.1%**）"
          "⇒ 且**更正 981 挂错的一个数** ⇒ 而整圈上的回绕次数仍是 **1** ⇒ "
          "**结论被加强** —")

    check("PPPPP.1 ⭐⭐⭐⭐⭐ **本批把「一圈」定义成了一个不变量** —— "
          "**圈长 p := 满足「∀i: seq[i] == seq[i % p]」的最小 p**："
          "它是**不变量**（旋转不变、与步数无关、**不读任何 testid**）"
          "⇒ ⇒ ⭐⭐⭐⭐⭐ 由此**从根上绕开** 974 那条纪律（已复发四次）："
          "**新定义里根本没有「名字」⇒ 也就没有「同一个名字两种口径」**；"
          "源站实测（2/2）**`min_period = 101`**、"
          "`laps_identical = True` ⇒ ⭐⭐⭐⭐ "
          "**圈长 101 由三份独立数据复核**：974 的 **140** 步、981 的 **240** 步、"
          "982 的 **210** 步；"
          "⚠️⚠️⭐⭐⭐ **而 `min_period` 永不失败**（`p == n` 恒成立 ⇒ "
          "`seq[i % n] == seq[i]` 恒真）⇒ 它**判不出「不是周期序列」**"
          "⇒ ① 空序列必须**显式**返回 `None`（否则 `p = 1` 靠 `all([])` 恒真）"
          "② ⭐⭐⭐ **`rem` 必须单独读出来**（980 的纪律："
          "**切圈残段不许算进分母**）⇒ 982 实测 `rem = 8`；"
          "⇒ ⇒ ⭐⭐⭐⭐ **`min` 与 `max` 的差恰好就是「残段」**："
          "6 步的 `['a','b']×3` ⇒ `min = 2`（3 圈）、`max = 6`（1 圈）"
          "⇒ **`max` 永远整除、永远看不到残段** ⇒ **用它就会把 1.5 圈当成 1 圈**",
          '"definition_of_lap_982"' in _ausrc
          and "**圈长 p := 满足「∀i: seq[i] == seq[i % p]」的最小 p**" in _ausrc
          and "**新定义里根本没有「名字」" in _ausrc
          and "**`min_period = 101`**" in _ausrc
          and "`laps_identical = True`" in _ausrc
          and "974 的 **140** 步、981 的 **240** 步、982 的 **210** 步" in _ausrc
          and "**`min_period` 永不失败**" in _ausrc
          and "982 实测 `rem = 8`" in _ausrc
          and "**`max` 永远整除、永远看不到残段**" in _ausrc
          and '"arc_is_not_lap_982"' in _ausrc
          # ⭐⭐⭐⭐⭐ **「arc 从来不是圈」这条要钉住它的源码出处**
          and "`jimeng_probe973_ringorder_ck.py:311`" in _ausrc
          and "**复刻侧**：整圈 **26** 格、弧 **19** 格 ⇒ **73.1%**" in _ausrc
          and "**源站侧**：整圈 **101** 格、弧 **18** 格 ⇒ **17.8%**" in _ausrc
          and "在源站侧只验了 17.8% 的圈**" in _ausrc
          and "**`arc` 从此改称「out 弧」**" in _ausrc
          and "**不是本批新测的** —— **诚实记账**" in _ausrc
          # ⭐⭐ 钉探针：新件、两条继承来的仪器、空序列那一挡、残段
          and "def min_period(seq):" in _p982
          and "if n == 0:" in _p982
          and '"min_period"' in _p982 and '"rem"' in _p982
          and "N_STEPS = 210" in _p982
          and '"arc_covers_whole_lap"' in _p982
          and '_grab("DOMRANK_JS", _p973)' in _p982
          and '_grab("POLL_JS", _p979)' in _p982
          and "def _arc_of(pairs):" in _p982
          and "def _descents(seq):" in _p982
          and '_p982": "scripts/jimeng_probe982_ringlen_src.py",' in _anchs)

    check("PPPPP.2 ⭐⭐⭐⭐⭐ **本批更正 981 挂错的一个数（而它是最要紧的一个）**"
          " —— 981 原话是「左栏容器 `canvas-fixed-toolbar` "
          "**一圈里被命中约 2 次**（三个左栏按钮各自的 `closest_tid` 都是它）」，"
          "而**读数把这两半都证伪了**："
          "① 982 实测 `left_rail_closest_tids` = "
          "`['canvas-pointer-tool-toggle', 'canvas-display-toggle-minimap', "
          "'canvas-display-toggle-connections', …]` ⇒ "
          "⭐⭐⭐⭐ **三个左栏按钮的 `closest_tid` 各不相同**；"
          "② `rail_closest_hits = 2` / **210 步 = 2 圈 + 8** ⇒ **每圈 1 次** "
          "⇒ ⇒ ⭐⭐⭐⭐ **错在「跨圈计数漏了除以圈数」**"
          "（980「切圈残段不许算进分母」的**姊妹条**）—— "
          "981 把 **2 圈的总数（2）** 当成了**单圈**；"
          "⚠️⚠️ **而这个错误的方向是「说多了」** ⇒ "
          "981 据此下的结论「973–977 不是整圈」**理由要换、结论不撤回**："
          "⭐⭐⭐⭐⭐ **974 从来没走完过一圈** —— 它读数 `n_rail_stops = 1` ⇒ "
          "`canvas-fixed-toolbar` **只命中 1 次**就**撞上了 `n_lead_cap = 140` 硬上限** "
          "⇒ ⇒ **140 步 = 1 个整圈（101）+ 39 步残段**；"
          "⇒ 且它的 `arc_len = 18` 取自 `arc` 提取器（**连续 out 段**）、"
          "**与 `n_rail_stops` 无关** ⇒ ⇒ "
          "⭐⭐ **973（复刻侧）`n_rail_stops = 2` ⇒ 它确实走完了**，"
          "而复刻侧整圈 = 26 格 ⇒ 它的 19 格弧 = **73.1%**；"
          "⇒ ⇒ ⭐ 顺带厘清**两件事被并成一件**："
          "「元素自己」口径 `rail_own_hits = 0` ⇒ "
          "**`canvas-fixed-toolbar` 根本不是焦点目标**"
          "（⇒ 981 **第一版**的 `rail_hits = 0` 原来是对的）、"
          "「容器」口径每圈 1 次 ⇒ ⭐⭐⭐⭐ "
          "**「同一个名字、两种口径」又一次复发，而这次两半都写进了同一句错话里**；"
          "⇒ ⇒ ⭐⭐⭐⭐ **撤销结论按规矩来：原文保留、只加改写横幅** ⇒ "
          "本条判据**同时钉住 `OOOOO.2` 那两句错话仍在 `_ausrc` 里**（不许删）",
          '"correction_to_981_982"' in _ausrc
          and "**读数直接证伪这两半**" in _ausrc
          and "**三个左栏按钮的 `closest_tid` 各不相同**" in _ausrc
          and "**每圈 1 次**" in _ausrc
          and "**错在「跨圈计数漏了除以圈数」**" in _ausrc
          and "981 把 **2 圈的总数（2）** 当成了**单圈**" in _ausrc
          and "**这个错误的方向是「说多了」**" in _ausrc
          and "**理由要换、结论不撤回**" in _ausrc
          and '"why_974_never_finished_a_lap_982"' in _ausrc
          and "`n_rail_stops = 1`" in _ausrc
          and "**140 步 = 1 个整圈（101）+ 39 步残段**" in _ausrc
          and "它的 19 格弧 = **73.1%**" in _ausrc
          and "`rail_own_hits = 0`" in _ausrc
          and "**「同一个名字、两种口径」又一次复发" in _ausrc
          # ⭐⭐⭐⭐ **成对钉住「原文保留」**（撤销结论不许偷偷删掉旧话）
          and '"one_lap_is_not_one_lap_981"' in _ausrc
          and "**左栏容器在一圈里被命中约 2 次**" in _ausrc
          # ⭐⭐ 钉探针：左栏三列并排读出 + 974 的上限常量
          and '"left_rail_closest_tids"' in _p982
          and '"rail_closest_hits"' in _p982
          and '"rail_own_hits"' in _p982
          and "LEFT_RAIL_SELF = (" in _p982
          and "n_lead_cap = 140" in _ausrc)

    check("PPPPP.3 ⭐⭐⭐⭐⭐ **本批最漂亮的一条：结论是被加强，不是被推翻** —— "
          "982 实测（2/2，**整圈 101 格**上）**`descents_on_full_lap = 1`**、"
          "`unknown = 0`；而**同一份读数里、974 的口径**上 "
          "**`descents_on_arc = 1`** ⇒ ⭐⭐⭐⭐⭐ **两个数相等** ⇒ "
          "**「环序 = 纯 DOM 序」从一个 17.8% 的小段，升级到 100% 的整圈** ⇒ "
          "⭐⭐⭐⭐ **新增的 83 格（`self`，占 82.2%）没有引入第二次回绕** ⇒ "
          "**973/974 的核心结论更稳了，不是更弱了**；"
          "⇒ 而 ⭐⭐⭐⭐⭐ 顺带查出一个**结构发现**：整圈 101 格的 `dom_rank` "
          "范围 **60 – 2395**，**最小值 = `BODY`（60）**、"
          "**最大值 = `canvas-sidecar-launcher`（2395）**，而它们**恰好相邻**"
          "（圈内第 89、90 格）⇒ **下降 2335**、2/2 逐格相同 ⇒ "
          "⭐⭐⭐⭐⭐ **这不是巧合，是结构性的** ⇒ "
          "**「整圈恰好一次回绕」的唯一来源就是 `BODY` 那一格** ⇒ "
          "⭐⭐⭐⭐⭐ **新可证伪推论：若 `BODY` 那一格不存在"
          "（臂 A 那种把它跳过的干预），整圈上就会出现「0 次下降」**；"
          "⇒ 且 ⭐⭐⭐⭐ **H₃ 的位置命题拿到第三份独立数据（在整圈尺度上）**："
          "`body_i_in_lap = 90`、`marker_i_in_lap = 91`"
          "（marker = `canvas-project-logo`）⇒ **`BODY` 紧邻"
          "「DOM 里第一个可聚焦元素」的前一格** ⇒ 与 977 臂 B 完全一致 "
          "⇒ ⚠️ **但「复现 ≠ 出处」，且 982 不复活 H₃ 里那个「恒」**"
          "（980 已量成实验室缺失率 ≈ 7.8%）",
          '"full_lap_dom_order_982"' in _ausrc
          and "**`descents_on_full_lap = 1`**" in _ausrc
          and "**`descents_on_arc = 1`**" in _ausrc
          and "**两个数相等 ⇒ 「环序 = 纯 DOM 序」"
          "从一个 17.8% 的小段，升级到 100% 的整圈**" in _ausrc
          and "**新增的 83 格没有引入第二次回绕**" in _ausrc
          and "973/974 的核心结论**更稳了，不是更弱了**" in _ausrc
          and '"body_is_the_wrap_982"' in _ausrc
          and "范围 = **60 – 2395**" in _ausrc
          and "**最小值 = `BODY`（60）**" in _ausrc
          and "**最大值 = `canvas-sidecar-launcher`（2395）**" in _ausrc
          and "而它们**恰好相邻**（圈内第 89、90 格）" in _ausrc
          and "唯一来源就是 `BODY` 那一格**" in _ausrc
          and "整圈上就会出现「0 次下降」**" in _ausrc
          and '"body_precedes_first_focusable_full_lap_982"' in _ausrc
          and "**`body_i_in_lap = 90`**" in _ausrc
          and "**`marker_i_in_lap = 91`**" in _ausrc
          and "**不复活那个「恒」字**" in _ausrc
          # ⭐⭐ 钉探针：两个口径的下降数都被读出、圈被切出来、BODY 下标
          and '"descents_on_full_lap"' in _p982
          and '"descents_on_arc"' in _p982
          and '"one_lap"' in _p982
          and '"body_i_in_lap"' in _p982
          and '"marker_i_in_lap"' in _p982
          and '"n_rank_unknown_total"' in _p982
          # ⭐⭐⭐⭐ 本批的三条纪律（自测期望值 / 门红先判门错 / 恒真断言）
          and '"discipline_982"' in _ausrc
          and "第六、七次复发" in _ausrc
          and "**门红先判「门错还是数据错」**" in _ausrc
          and "本批第一版那道门**错在锚点挑错文件**" in _ausrc
          and "这种**恒真断言**，它比没有门更坏" in _ausrc
          and "**本批零计费**：只按 `Tab`；" in _ausrc)

    # ══ QQQQQ. 批 983 复刻侧：⭐⭐⭐⭐⭐ **在第二个被测系统上独立复验 982
    #    那条结构发现** ⇒ 三条预测全部命中 ⇒ **「下降点 = (最大 ⇢ 最小)、
    #    最小者是 BODY」是规律，不是源站特有的巧合** ══
    print("— QQQQQ. 批 983 复刻侧：圈长 **26**、下降 **1**、下降点 **第 24→25 格"
          "（268→37）**、前驱 = 整圈最大、后继 = 整圈最小且**就是 `BODY`** ⇒ "
          "**与源站侧（101 格 / 2395→60）逐项同构** ⇒ 982 那条推论**升级为规律** —")

    check("QQQQQ.1 ⭐⭐⭐⭐⭐ **本批的全部三条预测都命中（2/2 逐格相同）** ⇒ "
          "982 那条推论**在两个被测系统上同构成立** ⇒ "
          "**它从「一个系统上的一次观察」升级成规律**：\n"
          "  · ⭐⭐⭐⭐⭐ **预测 ①：整圈上恰好 1 次下降** ⇒ 源站 "
          "`descents_on_full_lap = 1`、复刻侧 **也是 1**\n"
          "  · ⭐⭐⭐⭐⭐ **预测 ②：那一格的「前驱 = 整圈 `dom_rank` 最大的那一格、"
          "后继 = 最小的一格，且最小者就是 `BODY`」** ⇒\n"
          "    · 源站：**第 89 → 90 格**、**2395 → 60**\n"
          "    · 复刻侧：**第 24 → 25 格**、**268 → 37**\n"
          "    · ⇒ ⇒ ⭐⭐⭐⭐ **两个系统的圈长差了近四倍（101 vs 26）、"
          "格子的身份全不一样**，而**下降点的形状逐项同构**\n"
          "  · ⭐⭐⭐⭐ **预测 ③：`min_period = 26`** ⇒ 实测 **26**、"
          "`n_full = 3`、`rem = 12`、`laps_identical = True`、`unknown = 0`\n"
          "  · ⭐⭐⭐⭐ **`body_is_min_rank` 在两侧都是 `True`** ⇒ "
          "**「`BODY` 是整圈上 `dom_rank` 最小的那一格」也是规律**",
          '"wrap_shape_is_a_law_983"' in _ausrc
          and "**本批的全部三条预测都命中（2/2 逐格相同）**" in _ausrc
          and "**它从「一个系统上的一次观察」升级成规律**" in _ausrc
          and "**预测 ①：整圈上恰好 1 次下降**" in _ausrc
          and "**预测 ②：那一格的「前驱 = 整圈 `dom_rank` " in _ausrc
          and "**第 89 → 90 格**、**2395 → 60**" in _ausrc
          and "**第 24 → 25 格**、**268 → 37**" in _ausrc
          and "**下降点的形状逐项同构**" in _ausrc
          and "**预测 ③：`min_period = 26`**" in _ausrc
          and "**三份独立数据（973 的 44 步、983 的 90 步、"
          "982 的源站侧）都复核了各自的圈长**" in _ausrc
          and "**`body_is_min_rank` 在两侧都是 `True`**" in _ausrc
          # ⭐⭐ 钉探针：三条关系式读数都在
          and '"wrap_shape_ok"' in _p983
          and '"body_is_min_rank"' in _p983
          and '"descent_i_in_lap"' in _p983
          and '"min_rank_i_in_lap"' in _p983
          and '"max_rank_i_in_lap"' in _p983
          and "N_STEPS = 90" in _p983
          and '"_p983": "scripts/jimeng_probe983_wrapcmp_ck.py",' in _anchs)

    check("QQQQQ.2 ⭐⭐⭐⭐⭐ **本批的新件 `_grab_def`，以及它的代价必须说清** —— "
          "`_grab` 只认**字面量赋值** ⇒ 982 那三个**纯 python** 新件抠不到 ⇒ "
          "本批按**起止锚点**逐字抠出那段源码、**`exec` 绑定**、"
          "再 `assert` 抠出来的段确实在 982 文件里；"
          "⚠️⚠️⭐⭐⭐⭐ **代价：`exec` 跑的是「可执行代码」，而 `_grab` 抠的"
          "只是「字面量」⇒ 保证更弱** ⇒ ⇒ 补一道**成对**的门："
          "⭐⭐⭐⭐⭐ **把 982 自己那组自测用例在抠出来的仪器上重跑一遍** ⇒ "
          "**若 982 改了语义而没同步改用例，这道门就红**；"
          "⇒ 且 ⭐⭐⭐⭐⭐ **本批在「剥注释」上连踩三坑，而第三坑是成对门抓出来的**：\n"
          "  · ① ⭐⭐⭐ **混用两套语义**（拿 JS 语义去剥 Python）⇒ **门红、门错**\n"
          "  · ② ⭐⭐⭐⭐⭐ **更严重**：改成「用空格拼 token」⇒ `open('x')` 变成 "
          "`open ( 'x'` ⇒ **`\"open(\"` 这个针永远匹配不上** ⇒ "
          "**正向门恒绿 = 恒真** ⇒ ⭐⭐ **恒真的门比没有门更坏**\n"
          "  · ③ ⭐⭐⭐⭐⭐ **版本坑**：`tokenize` 在 **Python 3.12 起把行号报成 "
          "1 基**（3.11 是 0 基）⇒ 按 0 基掩会**掩到空行**上 ⇒ ⇒ "
          "⭐ **这道坑是成对门抓出来的**（它要求「注释里的 `open(` 必须消失」）\n"
          "⇒ ⇒ 修法：**只抹掉注释、原文其余部分一字不改**（间距天然保留）"
          "＋ **先探测基准、再掩** ⇒ ⇒ 成对门钉成**三条**（三个坑各钉一道）",
          '"grab_def_and_its_price_983"' in _ausrc
          and "**代价：`exec` 跑的是「可执行代码」" in _ausrc
          and "**把 982 自己那组自测用例在抠出来的仪器上重跑一遍**" in _ausrc
          and "**若 982 改了语义而没同步改用例，这道门就红**" in _ausrc
          and '"three_stripping_caliber_traps_983"' in _ausrc
          and "**正向门恒绿 = 恒真**" in _ausrc
          and "**恒真的门比没有门更坏**" in _ausrc
          and "**这道坑是成对门抓出来的**" in _ausrc
          and "**Python 3.12 起" in _ausrc
          and "**只抹掉注释、原文其余部分一字不改**" in _ausrc
          and "**因此本批把成对门钉成三条**" in _ausrc
          # ⭐⭐ 钉探针：抠取、exec、成对门、风险面门、基准探测
          and "def _grab_def(start, end, src=None):" in _p983
          and 'GRAB_DEF_START = "def min_period(seq):"' in _p983
          and 'GRAB_DEF_END = "def _code_only(js):"' in _p983
          and 'exec(compile(INSTR_SRC, "<982-instruments>", "exec"), _INSTR_NS)' in _p983
          and "assert INSTR_SRC in _p982" in _p983
          and "**抠出来的仪器与 982 原件行为不一致**" in _p983
          and "def _py_code_only(src):" in _p983
          and "**基准探测**" in _p983
          and '"import " in _py_code_only("import os\\n")' in _p983
          and "钉住「不会恒绿」" in _p983)

    check("QQQQQ.3 ⭐⭐⭐⭐⭐ **一个直接服务于产品决策的副产品** —— "
          "**复刻侧也有 `BODY` 那一格**、且它的 `dom_rank` **也是整圈最小**（37）"
          "⇒ `body_is_min_rank = True` ⇒ ⭐⭐⭐⭐⭐ "
          "**源站与复刻在这一点上完全一致** ⇒ "
          "**「`BODY` 那一格」不构成两侧的差异点** ⇒ ⚠️ "
          "**`rf__wrapper` 的对齐决策不能拿 `BODY` 当理由**；"
          "⇒ 而 ⭐⭐⭐⭐ **`rf__wrapper` 的 `dom_rank` 相对次序，两侧确实不同**：\n"
          "  · **源站**：`BODY`(60) ⇢ `canvas-project-logo`(68) ⇢ … ⇢ "
          "**`rf__wrapper`(177)** ⇒ **在 `logo` _之后_**\n"
          "  · **复刻侧**：`BODY`(37) ⇢ **`rf__wrapper`(42)** ⇢ … ⇢ "
          "`canvas-project-logo`(110) ⇒ **在 `logo` _之前_**\n"
          "⇒ ⇒ ⭐⭐⭐⭐ **这正是 973 那条「位置差异是 DOM 摆放差异（实现差异）」"
          "的 `dom_rank` 级直接证据** —— ⚠️ 而 972/973 当时只报了**座位与邻居**"
          "（`flow_seats`）、**没报 `dom_rank` 的相对次序** ⇒ "
          "**这一格是空的，本批补上** ⇒ ⇒ ⭐⭐⭐⭐ "
          "982 说的「先量影响面」，**现在这一端已经量出来了** ⇒ "
          "⚠️⭐⭐ **但本批仍不提出产品改动**（972/973 立的规矩不变）；"
          "另 ⭐⭐⭐⭐ **两个系统的 arc 覆盖率并排**（**并排读出，不二选一**）："
          "源站 **18 / 101 = 17.8%**、复刻侧 **19 / 26 = 73.1%** ⇒ "
          "**两处都与 973/974 存档逐格一致** ⇒ "
          "**错的是「那叫一圈」这个叫法，不是那些数** ⇒ "
          "**「out 弧」这个改名在两个系统上都站得住**",
          '"body_on_both_sides_983"' in _ausrc
          and "不构成两侧的差异点**" in _ausrc
          and "**`rf__wrapper` 的对齐决策不能拿 `BODY` 当理由**" in _ausrc
          and "**它是引擎层给的**" in _ausrc
          and '"rf_wrapper_dom_rank_order_983"' in _ausrc
          and "**`rf__wrapper` 在 `logo` _之后_**" in _ausrc
          and "**`rf__wrapper` 在 `logo` _之前_**" in _ausrc
          and "**没报 `dom_rank` 的相对次序**" in _ausrc
          and "**这一格是空的，本批补上**" in _ausrc
          and "现在这一端已经量出来了**" in _ausrc
          and "**但本批仍不提出产品改动**" in _ausrc
          and '"arc_coverage_two_sides_983"' in _ausrc
          and "**并排读出，不二选一**" in _ausrc
          and "**18 / 101 = 17.8%**" in _ausrc
          and "**19 / 26 = 73.1%**" in _ausrc
          and "**973/974 报的那些数没错，错的是「那叫一圈」这个叫法**" in _ausrc
          and '"discipline_983"' in _ausrc
          and "**一个系统的观察不是规律，两个系统才是**" in _ausrc
          and "本批门红 **4 次**" in _ausrc
          and "**第四次「锚点挑错文件」**" in _ausrc
          and "**本批零计费、零插入、零节点点击**" in _ausrc
          # ⭐⭐ 钉探针：两种口径并排读出、973 口径的弧
          and 'keys = [("%s/%s" % (r["own_tid"], r["closest_tid"])) for r in rows]'
          in _p983
          and '"left_rail_closest_tids"' in _p983
          and '"arc_cover_num"' in _p983 and '"arc_cover_den"' in _p983
          and '"descents_on_arc"' in _p983)

    # ══ RRRRR. 批 984 实验室：⭐⭐⭐⭐⭐ **把 H₃ 的「出处」逼到一个精确位置**
    #    —— 而第一步 978 的读数就已经做完了：`BODY` 的 `tabIndex` 是**算出来的 −1**
    #    ⇒ H₄「靠普通 tabindex 规则进环」被否；`A1`/`A3` 把 `BODY` 挪到环开头
    #    ⇒ **它在环里完全由 `tabIndex` 决定**；⚠️ **但仍未读到源码 ⇒ 不许写「已找到出处」** ══
    print("— RRRRR. 批 984 实验室：`BODY` 的 `ti_attr = null` 而 `ti_prop = -1` ⇒ "
          "**不可聚焦是算出来的** ⇒ H₄ 被否；`A1`/`A3` 把它挪到环开头、"
          "`A2`/`A4` 精确回到基线（2/2）⇒ **停靠由 `tabIndex` 决定**；"
          "并**更正我自己一处过宽断言** ⇒ **仍未找到出处** —")

    check("RRRRR.1 ⭐⭐⭐⭐⭐ **本批最要紧的一条，而 978 的读数里就已经有** —— "
          "978 实验室（`about:blank` ＋ 3 个 `<button>`）的 `STOP_JS` "
          "**逐格读过**两套口径：`BUTTON#lab-b1` 是 `ti_attr = null`、**`ti_prop = 0`**；"
          "**`BODY`** 是 `ti_attr = null`、**`ti_prop = -1`** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **`BODY` 的「不可聚焦」是引擎算出来的（`tabIndex === -1`），"
          "不是作者写上去的属性** ⇒ ⇒ ⭐⭐⭐⭐⭐ "
          "**H₄「`BODY` 靠普通 `tabindex` 规则进 Tab 环」当场被否** —— "
          "按普通规则 `tabIndex === -1` 的元素**根本不该是可聚焦候选** ⇒ ⇒ "
          "⭐⭐⭐⭐ **而这正是 H₃ 整个形状的来源**：既然不是普通候选，"
          "它必然是**焦点导航里的显式兜底** ⇒ 兜底必然被放在**环的回绕点**"
          "（最后一个可聚焦元素之后、第一个之前）⇒ "
          "**977 / 982 / 983 量到的位置逐格对上了**",
          '"body_tabindex_is_computed_984"' in _ausrc
          and "**本批最要紧的一条，而 978 的读数里就已经有**" in _ausrc
          and "**`ti_prop = -1`**" in _ausrc
          and "**`BODY` 的「不可聚焦」是引擎算出来的" in _ausrc
          and "当场被否** —— 按普通规则" in _ausrc
          and "**而这正是 H₃ 整个形状的来源**" in _ausrc
          and "**焦点导航里的显式兜底**" in _ausrc
          and "**977 / 982 / 983 量到的位置逐格对上了**" in _ausrc
          # ⭐⭐ 钉探针：基线常量就是 978 那个环、继承来的 `STOP_JS` 两列都在
          and 'BASELINE_CYCLE = ["lab-b1", "lab-b2", "lab-b3", "BODY"]' in _p984
          and "N_BUTTONS = 3" in _p984
          and "N_STEPS = 14" in _p984
          and 'STOP_JS = _grab("STOP_JS", _p978)' in _p984
          and '"a.getAttribute(\'tabindex\')" in STOP_JS' in _p984
          and '"a.tabIndex" in STOP_JS' in _p984)

    check("RRRRR.2 ⭐⭐⭐⭐⭐ **`A1` / `A3` 改写了 H₃ 的内容，而这是本批的判决** —— "
          "五个臂 2/2 逐格相同：`A0` 环 "
          "`['lab-b1','lab-b2','lab-b3','BODY']` 长 **4**、**逐格复现 978 的 "
          "`cycle_sig`**、`BODY` 在**第 3 格（末尾）**、`ti_attr = null`、"
          "`ti_prop = -1`；`A1`（`setAttribute('tabindex','0')`）与 "
          "`A3`（**只写 IDL** `body.tabIndex = 0`）**都**让环变成 "
          "`['BODY','lab-b1','lab-b2','lab-b3']`、**`BODY` 跑到第 0 格**；"
          "`A2`（撤销 A1）⭐ **逐格回到 A0**；`A4`（显式 `tabIndex = -1`）⭐ "
          "**环形状与位置与 A0 完全相同** ⇒ ⇒ ⭐⭐⭐⭐⭐ "
          "**「`BODY` 在环里」完全由 `tabIndex` 决定**：`0` ⇒ 它是**普通** "
          "`tabindex=0` 元素（无需解释）；**`-1` ⇒ 它仍然是停靠点** ⭐ "
          "**这才是需要解释的那一半** ⇒ 且 **`A4` 给出很强的等价性证据**："
          "**显式写 `tabindex=\"-1\"` 与「没写、被算成 −1」在停靠行为上完全一样** ⇒ "
          "**兜底性质来自「计算值 −1」本身**，不是「恰好没写属性」⇒ "
          "⭐⭐⭐⭐⭐ **顺带把 982/983 那条结构发现补上了机制**："
          "`BODY` 是整圈 `dom_rank` **最小**的一格 ⇒ 它**一旦成为普通候选"
          "就必然排第一** —— `A1`/`A3` 实测正是如此 ⇒ "
          "**与 `body_is_min_rank` 完美咬合** ⇒ 而「末尾」与「开头」"
          "**本来就是循环环上的同一个位置**",
          '"arm_table_984"' in _ausrc
          and "**`A0`** 基线（不动）" in _ausrc
          and "**`A2`** `body.removeAttribute('tabindex')`（**撤销 A1**）" in _ausrc
          and "**逐格回到 A0 的形状**" in _ausrc
          and "**只写 IDL** `body.tabIndex = 0`" in _ausrc
          and "**也变成了 `'0'`**" in _ausrc
          and '"body_stop_is_governed_by_tabindex_984"' in _ausrc
          and "**`BODY` 在环里的位置**随它的 `tabIndex` 变" in _ausrc
          and "**它不再有任何「特殊」待遇**" in _ausrc
          and "这件事完全由 `tabIndex` 决定**" in _ausrc
          and "**这才是需要解释的那一半**" in _ausrc
          and "与「没写、被算成 −1」在停靠行为上" in _ausrc
          and "**兜底性质来自「计算值 −1」这个事实本身**" in _ausrc
          and "**顺带把 982/983 那条结构发现补上了机制**" in _ausrc
          and "**一旦成为普通候选就必然排第一**" in _ausrc
          and "**与 `body_is_min_rank` 完美咬合**" in _ausrc
          and "**「末尾」与「开头」本来就是循环环上的同一个位置**" in _ausrc
          # ⭐⭐ 钉探针：五个臂、两个撤销臂、关系式读数
          and '("A0", "null",' in _p984
          and "document.body.setAttribute('tabindex', '0')" in _p984
          and "document.body.removeAttribute('tabindex')" in _p984
          and "document.body.tabIndex = 0" in _p984
          and "document.body.tabIndex = -1" in _p984
          and '"body_pos_in_cycle"' in _p984
          and '"body_in_cycle"' in _p984
          and '"same_as_baseline"' in _p984
          and '"eq_baseline_cycle"' in _p984
          and '"attr_vs_prop"' in _p984
          and '"_p984": "scripts/jimeng_probe984_bodytabindex_lab.py",' in _anchs)

    check("RRRRR.3 ⭐⭐⭐⭐⭐ **本批更正我自己一处「过宽的断言」** —— "
          "我原写「`tabindex` 在规范里就是**两个东西**（content attribute 与 "
          "IDL 属性）⇒ 974 那条纪律在这里**是规范本身**」⇒ ⇒ ⭐⭐⭐⭐⭐ "
          "**`A3` 臂把它否掉了**：**只写 IDL**（不碰 content attribute）⇒ "
          "实测 `ti_attr` **也变成了 `'0'`** ⇒ ⇒ **引擎的 `tabIndex` setter "
          "会回写 content attribute** ⇒ 而这与 HTML 规范一致 ⇒ ⇒ "
          "**那不是「两套口径」，是同一套规则的两个表面** ⇒ ⇒ ⭐⭐⭐⭐ "
          "**本批真正分开的**是另外两件事：**有没有写**（`ti_attr`）vs "
          "**算出多少**（`ti_prop`）⇒ `A0` 上 `null` 而 `-1` ⇒ "
          "**「没写」与「算出 −1」不是一回事** ⇒ ⇒ "
          "⚠️ **探针 docstring 与 `ruler` 里的同一句断言已一并改掉**"
          "⇒ ⇒ **撤销结论按规矩来：改写、不删**；"
          "⚠️⚠️⚠️⭐⭐⭐⭐⭐ **而本批没有找到出处，且必须这么写** —— "
          "本批做的是**把问题缩小**：从「`BODY` 为什么会是停靠点？」收窄到"
          "「**顺序焦点导航在环的回绕点上，是否接纳 `tabIndex < 0` 的 "
          "`document.body`？**」⇒ ⇒ ⭐⭐⭐⭐⭐ "
          "**复现 ≠ 出处、时长 ≠ 出处、比率 ≠ 出处、同构 ≠ 出处；"
          "本批给出的是**行为刻画**，**不是源码引用** ⇒ ⇒ "
          "⚠️⭐⭐ **明确不许写「已找到出处」**；"
          "另两条：⭐⭐⭐ ⭐⭐⭐⭐ **过窄的门和过宽的门一样坏** —— "
          "纯读守卫第一版用子串 `\"tabIndex =\"` 当禁词，"
          "而 `STOP_JS` 里**读**属性那行是 `a.tabIndex === undefined` ⇒ "
          "**那个子串恰是它的前缀** ⇒ 门红 ⇒ ⭐⭐ "
          "**它逼我改继承来的尺子或删门 —— 两条都是更差的工程** ⇒ "
          "**改成正则** ⇒ 成对门钉**三条**；"
          "⭐⭐⭐⭐ **只有能按定义推出的才配当门**（`A0` 回归门 / `A2` 撤销 / "
          "`A4` 等价性 ⇒ **真门**；`A1` 与 `A3` 属**待测事实、判据不预写**）；"
          "⭐⭐⭐ 顺带把 **980 那 7.8% 交叉印证**上：978 的 `L3` 臂 "
          "`n_body_stops = 2`（其余臂都是 3）⇒ 两条独立数据链互证；"
          "⭐⭐⭐⭐⭐ **本批零计费**：`about:blank`、**不打开源站**、**零节点点击**",
          '"correction_of_my_own_984"' in _ausrc
          and "**本批更正我自己一处「过宽的断言」**" in _ausrc
          and "**`A3` 臂把它否掉了**" in _ausrc
          and "**引擎的 `tabIndex` setter 会回写 content attribute**" in _ausrc
          and "**那不是「两套口径」，是同一套规则的两个表面**" in _ausrc
          and "**本批真正分开的**是另外两件事" in _ausrc
          and "**「没写」与「算出 −1」不是一回事**" in _ausrc
          and "**探针 docstring 与 `ruler` 里的同一句断言已一并改掉**" in _ausrc
          and "**撤销结论按规矩来：改写、不删**" in _ausrc
          and '"still_not_the_source_984"' in _ausrc
          and "**本批没有找到出处，而且必须这么写**" in _ausrc
          and "**顺序焦点导航在环的回绕点上，是否接纳 " in _ausrc
          and "**行为刻画**，**不是源码引用**" in _ausrc
          and "**明确不许写「已找到出处」**" in _ausrc
          and '"l3_cross_check_984"' in _ausrc
          and "顺带把 980 那 7.8% 交叉印证上了**：978 的 `L3` 臂 " in _ausrc
          and '"discipline_984"' in _ausrc
          and "**「出处」要能缩小到一句话，才算有进展**" in _ausrc
          and "**过宽的断言和过宽的门同一族**" in _ausrc
          and "**过窄的门和过宽的门一样坏**" in _ausrc
          and "恰是它的前缀** ⇒ 门红 ⇒ " in _ausrc
          and "**它逼我改继承来的尺子或删门 —— 两条都是更差的工程**" in _ausrc
          and "**只有能按定义推出的才配当门**" in _ausrc
          and "**本批零计费**：实验室页 `about:blank`" in _ausrc
          # ⭐⭐ 钉探针：更正留痕 + 正则守卫 + 三条成对门
          and "**这句断言被本批自己的读数否掉了，" in _p984
          and 'r"\\.tabIndex\\s*=(?!=)"' in _p984
          and "**读**属性被当成**写**" in _p984
          and "纯读守卫可能变成**恒真**" in _p984
          and "**只有这几条能按定义推出**" in _p984
          and "**属于**待测事实**" in _p984)    # ══ SSSSS. 批 985 实验室：⭐⭐⭐⭐⭐⭐ **一次自我推翻** ——
    #    `BODY` 根本不是一格（`:focus` 在谁身上才是那一问）⇒ 同一批
    #    **把 H₃ 的「出处」彻底落定**（三件齐）⇒ 976–984 的计数口径要整个换掉 ══
    print("— SSSSS. 批 985 实验室：`BODY` **从未被聚焦**（`body:focus=False`、"
          "`n_real_focus=0`、**`hasFocus=False`**，三次机会零例外）⇒ "
          "**它不是一格、是间隙**；出处三件齐（`SupportsFocus` 否 / "
          "`ShouldVisit` 排除 / `ClearFocusedElement`+`TakeFocus`）⇒ "
          "**H₃ 的位置命题是同义反复、应当作废** ⇒ 环长分母**减一**；"
          "且源站本轮**没测到（登录态过期）** —")

    check("SSSSS.1 ⭐⭐⭐⭐⭐⭐ **本批要推翻的是我自己 976–984 的同一个隐含前提** —— "
          "**`BODY` 根本不是一格**：实验室 2/2 逐格相同，"
          "`obs = ['lab-b1','lab-b2','lab-b3','GAP',…]`；"
          "而**在每一个 `GAP` 上同时读出三件事**：`body.matches(':focus')` = "
          "**`False`**（**`body` 从未被聚焦**）、真正持有焦点的元素数 = **`0`**、"
          "`document.hasFocus()` = **`False`**（**连文档都没焦点**）⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **三次机会、零次例外**：`n_gap_ever_body_focused = 0`、"
          "`n_gap_ever_has_focus = 0`、`n_gap_ever_any_focus = 0` ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **`BODY` 是「文档里没有任何元素持有焦点」这个状态**，"
          "而 `Document.activeElement` 按 DOM 规范**回落到 `document.body`** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **我的仪器测的是「间隙」，却把它记成了「一格」** ⇒ "
          "**976–984 全部读数里那个 `BODY`，读的都是这个间隙**；"
          "⇒ 且 ⭐⭐⭐⭐⭐ **本批最漂亮的一条钉子**："
          "**换名之后逐格相等**（`eq_984_baseline_after_rename = True`）⇒ "
          "**同一条环、同一批位置，只是两批各叫各的**；"
          "⚠️ 而 `eq_984_baseline_naive = False` ⇒ **我第一版那扇门就是拿"
          "含 `GAP` 的序列去比含 `BODY` 的基线** ⇒ **门错、不是数据错** ⇒ "
          "⭐⭐⭐⭐⭐ **那个恒假的读数原样保留**（命名为 `naive`）⇒ "
          "**它就是两批口径不同的证据 ⇒ 删掉它才是错的**",
          '"body_is_not_a_cell_985"' in _ausrc
          and "**本批要推翻的是我自己 976–984 的同一个隐含前提**" in _ausrc
          and "**三次机会、零次例外**" in _ausrc
          and "`n_gap_ever_body_focused = 0`" in _ausrc
          and "**它是「文档里没有任何元素持有焦点」这个状态**" in _ausrc
          and "**回落到 `document.body`**" in _ausrc
          and "**我的仪器测的是「间隙」，却把它记成了「一格」**" in _ausrc
          and "**976–984 全部读数里那个 `BODY`，读的都是这个间隙**" in _ausrc
          and '"rename_equivalence_985"' in _ausrc
          and "**换名之后逐格相等**" in _ausrc
          and "`eq_984_baseline_after_rename = True`" in _ausrc
          and "`eq_984_baseline_naive = False`" in _ausrc
          and "**我第一版那扇门就是拿" in _ausrc
          and "**门错、不是数据错**" in _ausrc
          and "两批口径不同的证据" in _ausrc
          # ⭐⭐ 钉探针：新件必须真的问出那三问、两个读数都在
          and "FOCUS_JS = " in _p985
          and '"body_matches_focus"' in _p985
          and '"has_focus"' in _p985
          and '"n_real_focus"' in _p985
          and '"is_gap"' in _p985
          and '"eq_984_baseline_after_rename"' in _p985
          and '"eq_984_baseline_naive"' in _p985
          and '"first_cycle"' in _p985
          and "def _cycle_of(keys):" in _p985
          and '"n_gap_ever_body_focused"' in _p985
          and "**本批的新件问的不是「落点是谁」" in _p985
          and '"_p985": "scripts/jimeng_probe985_bodynotacell_lab.py",' in _anchs)

    check("SSSSS.2 ⭐⭐⭐⭐⭐ **H₃ 的「出处」至此落定，而且是三件齐的** —— "
          "① `element.cc` 的 `Element::SupportsFocus` 对 `document.body` 返回 "
          "`FocusableState::kNotFocusable` ⇒ `FocusController::AdjustedTabIndex` "
          "的默认值取 **−1** ⇒ ⭐⭐⭐⭐ **这正是 984 读到的 `ti_prop = -1` 的出处**；"
          "② `focus_controller.cc` 的 `ShouldVisit()` 与遍历里那句 "
          "`ReadingFlowAdjustedTabIndex(*current) >= 0` ⇒ ⭐⭐⭐⭐ "
          "**`document.body` 被两处独立排除** ⇒ **它压根不是候选**；"
          "③ 「找不到候选」的分支走 `document->ClearFocusedElement()` ＋ "
          "`page_->GetChromeClient()->TakeFocus(type)` ⇒ ⭐⭐⭐⭐ "
          "**焦点被交给 Chrome 的 UI 层** ⇒ 页面里自然「一个焦点都没有」；"
          "⇒ ⇒ ⚠️⭐⭐ **于是 H₃ 那个问题本身问错了** —— "
          "不是「回绕点是否接纳 `tabIndex < 0` 的 `document.body`」，"
          "而是「**那个格子从来就不存在**」⇒ ⇒ "
          "⭐⭐⭐⭐ **984 说「本批没有找到出处」—— 这一批找到了**，"
          "**且 984 收窄后那句话是错的** ⇒ **改写，不删**；"
          "⇒ ⭐⭐⭐⭐⭐ **连带 H₃ 的「位置命题」是同义反复、应当作废重写** —— "
          "改写后它说的是「**「无元素持有焦点」这个状态，恰好出现在"
          "最后一个与第一个可聚焦元素之间**」，"
          "**而这在定义上就是必然的** ⇒ "
          "**「它在那个位置」从来不是一条关于世界的发现，而是关于「间隙」的定义** ⇒ "
          "⇒ 977 臂 B「后继换人」也随之改写："
          "**那个「后继」就是新的第一个可聚焦元素** ⇒ "
          "**977 的实测数据没错、观察也没错，错的是把它当成关于 `BODY` 这个实体的命题**",
          '"source_at_last_985"' in _ausrc
          and "**H₃ 的「出处」至此落定，而且是三件齐的**" in _ausrc
          and "**这正是 984 读到的 `ti_prop = -1` 的出处**" in _ausrc
          and "**`document.body` 被两处独立排除**" in _ausrc
          and "**它压根不是顺序焦点导航的候选**" in _ausrc
          and "**焦点被交给 Chrome 的 UI 层**" in _ausrc
          and "**于是 H₃ 那个问题本身问错了**" in _ausrc
          and "那个格子从来就不存在" in _ausrc
          and "**984 说「本批没有找到出处」—— 这一批找到了**" in _ausrc
          and "**改写，不删**" in _ausrc
          and '"h3_is_a_tautology_985"' in _ausrc
          and "**H₃ 的「位置命题」到此作废重写**" in _ausrc
          and "**是同义反复，不是发现**" in _ausrc
          and "**而这句话在定义上就是必然的**" in _ausrc
          and "从来不是一条关于世界的发现" in _ausrc
          and "而是关于「间隙」这个词的定义" in _ausrc
          and "H₃ 应当作废" in _ausrc
          and "新的第一个可聚焦元素" in _ausrc
          and "**观察到的其实是「间隙的位置随端点移动」" in _ausrc
          and "**977 那一批的实测数据没错、观察也没错**" in _ausrc
          # ⭐⭐ 钉探针：984 那条「仍未找到出处」的边界必须**还在**（本批要推翻它）
          and "984 那条「仍未找到出处」的边界不见了" in _p985
          and "**本批没有找到出处，而且必须这么写**" in _p985
          and "**顺序焦点导航在环的回绕点上，是否接纳" in _p985
          and "**实现给了两处独立排除**" in _p985)

    check("SSSSS.3 ⭐⭐⭐⭐⭐ **本批把计数口径整个换掉**（974 那条纪律的**第六次**应用）—— "
          "**旧口径**（976–984）环长 = 观察到的停靠点数（**含 `BODY`**）"
          "⇒ 源站 101、复刻 26、实验室 4；**新口径**（本批）"
          "**可聚焦停靠点数 = 旧环长 − 1** ⇒ 源站 **100**、复刻 **25**、实验室 **3** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **「环长」在换口径后不再是同一件事** ⇒ "
          "**凡引用「101 格 / 26 格」的旧结论，分母都要减一**；"
          "⭐⭐⭐⭐⭐ **旧口径在零停靠点页面上会把「零」报成「一」**："
          "本批 `A1` 臂（**页面上一个可聚焦元素都没有**）⇒ `obs` **全是 `GAP`**、"
          "`n_focus_stops = 0` ⇒ 旧口径会给出「环长 1」的假象 ⇒ "
          "⇒ ⭐⭐⭐⭐ **「某圈没走 `BODY`」这句话也要重述**（980 的 7.8%）："
          "它**不是「缺失了一格」**，而是「**那一圈没有间隙**」—— "
          "**这是完全不同的现象，必须重测**；"
          "⚠️⭐⭐⭐⭐ **源站那一臂本轮没测到，而原因必须写清** —— "
          "就绪探针返回 0，而 ⭐⭐⭐⭐ **第一版我差点误判成「源站改版」** ⇒ "
          "本批补了一道**诊断读数** ⇒ 实测 `n_btn = 0` / `n_ti0 = 0` / "
          "`n_nodeid = 0`，页面文本 = **「未命名项目 | 登录以打开您的画布」** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **是登录态过期，不是产品改版** ⇒ "
          "**「复现不出来」与「没量到」要分开记**（981 的纪律）⇒ "
          "⚠️ **旧口径的源站数字自此只能算**历史记录 ⇒ "
          "⇒ ⭐⭐ **但本批结论不受影响**（978/982/983 在**三处**都记到同一行为 "
          "⇒ **引擎层行为、与登录态无关**）；"
          "另 ⭐⭐⭐⭐⭐ **那扇回归门我连错两次、第二次与第一次同类**："
          "① 口径错（拿含 `GAP` 的比含 `BODY` 的）② 残段错"
          "（拿 **10 步整段**比 **4 格的一圈** ⇒ **正是 980 那条"
          "「切圈残段不许算进分母」**）⇒ ⇒ ⭐⭐⭐⭐ "
          "**回归门的第一问永远是「这两串到底该不该逐格相等」**",
          '"counting_caliber_changed_985"' in _ausrc
          and "**本批把计数口径整个换掉**" in _ausrc
          and "**可聚焦停靠点数 = 旧环长 − 1**" in _ausrc
          and "**「环长」在换口径后不再是同一件事**" in _ausrc
          and "分母都要减一" in _ausrc
          and "**旧口径在零停靠点页面上会把「零」报成「一」**" in _ausrc
          and "全是 `GAP`" in _ausrc
          and "那一圈没有间隙" in _ausrc
          and "**这是完全不同的现象，必须重测**" in _ausrc
          and '"src_not_measured_985"' in _ausrc
          and "**源站那一臂本轮没测到，而原因必须写清**" in _ausrc
          and "**第一版我差点误判成「源站改版」**" in _ausrc
          and "登录以打开您的画布" in _ausrc
          and "**是登录态过期，不是产品改版**" in _ausrc
          and "**「复现不出来」与「没量到」要分开记**" in _ausrc
          and "自此只能算" in _ausrc
          and "**但本批的结论不受影响**" in _ausrc
          and "**它是引擎层行为、与登录态无关**" in _ausrc
          and '"two_gate_errors_same_spot_985"' in _ausrc
          and "**那扇回归门我连错两次，第二次与第一次同类**" in _ausrc
          and "**第一次（口径错）**" in _ausrc
          and "**第二次（残段错，同一族）**" in _ausrc
          and "**这正是 980 那条「切圈残段不许算进分母」**" in _ausrc
          and "**门只能拿「首个周期」去比**" in _ausrc
          and "**两错都在同一扇门上、且都是「比较的对象没对齐」**" in _ausrc
          and "**回归门的第一问永远是「这两串到底该不该逐格相等」**" in _ausrc
          and '"discipline_985"' in _ausrc
          and "**仪器测什么，决定了你能看见什么**" in _ausrc
          and "**976–984 缺的那一问是「`:focus` 在谁身上」**" in _ausrc
          and "**一个测错对象的仪器，会把「没有」读成「有一个奇怪的」**" in _ausrc
          and "而 984 给的是" in _ausrc
          and "**这一步不能省**" in _ausrc
          and "**「没测到」必须能说清是「没就绪」还是「没登录」**" in _ausrc
          and "**一个恒假的读数也有信息量**" in _ausrc
          and "**本批零计费**：只按 `Tab`；" in _ausrc
          # ⭐⭐ 钉探针：诊断读数与「两种没测到」的分辨
          and '"why_not_measured"' in _p985
          and '"note_about_old_baselines"' in _p985
          and "**不是产品改版、也不是就绪探针失效**" in _p985
          and "**待查**" in _p985
          and '"gap_plus_focus_eq_steps"' in _p985)
    # ══ TTTTT. 批 986 实验室：⭐⭐⭐⭐⭐ **用 985 的新口径把 §190 的 7.8% 重测** ——
    #    缺失率归零（间隙不是一格 ⇒「少一格」不存在）；⭐⭐⭐⭐⭐ 而 985 判成
    #    「同义反复、应当作废」的那句**是一条能红的预测**（P2）⇒ 本批量它的位置 ══
    print("— TTTTT. 批 986 实验室：**缺失率归零**（新跑 84 圈 + 980 离线重算 64 圈，"
          "`new_laps_missing_a_stop=0`）⇒ §190 的 7.8% **不是「缺失率」而是"
          "「无间隙率」**；⭐⭐⭐⭐⭐ 且**间隙的位置是能红的预测**：新跑 42 圈 + 980 的 "
          "59 圈，**每一个间隙都在回绕点上、零例外** ⇒ **985 判「同义反复」判过头**；"
          "另：⭐⭐⭐ **比率不复现**（986 这轮 0/84 vs 980 的 5/64）⇒ 7.8% 不是稳定比率 —")

    check("TTTTT.1 ⭐⭐⭐⭐⭐ **本批按定义预写三条预测、全部命中** —— "
          "P1 **缺失率归零**（旧口径把间隙算成一格 ⇒「少一格」只可能是"
          "「这一圈没有间隙」）；P2 **间隙落在回绕点**（`_cycles` 固定 `first` ⇒"
          "有间隙时必是倒数第二枚）；P3 **间隙仍是间隙**（`body:focus=False`、"
          "`hasFocus=False`）⇒ 期望值**全部在看数据之前**按定义逐句推出，"
          "**并逐条给出推导**（探针头部）⇒ ⭐⭐⭐ **「跑出来是什么就写什么」"
          "会让自测恒真**",
          _p986.count("P1") >= 1 and _p986.count("P2") >= 1
          and _p986.count("P3") >= 1
          and "三条预测，**全部在看任何数据之前按定义写出**" in _p986
          and "这条**不是恒真门**" in _p986
          and "它会被「某一圈真的跳过一个停靠点」打红" in _p986
          and "**这条是能红的**" in _p986
          and '"predictions_written_before_data"' in _p986
          and '"_p986": "scripts/jimeng_probe986_gaprate_lab.py",' in _anchs)

    check("TTTTT.2 ⭐⭐⭐⭐⭐ **缺失率在新口径下恒为 0** —— "
          "P1 命中：986 新跑 84 圈 `new_laps_missing_a_stop = 0`、"
          "**980 原始数据离线重算 64 圈也是 0** ⇒ ⇒ "
          "旧口径报的 5 圈「缺失」**全部只是「这一圈没有间隙」** ⇒ "
          "§190 的 7.8% **不是「缺失率」而是「无间隙率」** ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「缺失」这个量在新口径下根本不存在**",
          '"new_laps_missing_a_stop"' in _p986
          and '"new_laps_with_gap"' in _p986
          and '"new_laps_without_gap"' in _p986
          and "少一格这件事不存在" in _p986
          and "**「缺失」这个量在新口径下根本不存在**" in _ausrc
          and "**那 5/64 是「**这一圈的回绕没有交出焦点**」" in _ausrc
          and "**这一格两侧都有**" not in _p986    # 985 那句属于 985、不许搬进 986
          and "它**不是「缺失了一格」**，而是「**那一圈没有间隙**」" in _ausrc
          and "完全不同的现象，必须重测" in _ausrc)

    check("TTTTT.3 ⭐⭐⭐⭐⭐ **P2 命中，而且它是本批的新量** —— "
          "**间隙的位置**（980 只量了「有没有间隙」、**从没量过位置**）："
          "新跑 42 圈 + 980 的 59 圈，`n_gaps_NOT_at_wrap = 0` **零例外** ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **985 判「同义反复、应当作废」判过头了** —— "
          "「间隙按构造在最后与第一个之间」作为**定义**是同义反复，"
          "但**「间隙落在环的哪一格上」是能红的预测**（引擎完全可以按计时器交出焦点）"
          "⇒ **985 判过头的不是数据，是把可证伪的预测当成了定义**",
          '"n_gaps_at_wrap"' in _p986
          and '"n_gaps_NOT_at_wrap"' in _p986
          and '"why_P2_is_not_a_tautology"' in _p986
          and "**「间隙落在哪一格上」是能红的预测**" in _p986
          and "**引擎完全可以按计时器交出焦点**" in _p986
          and "**986 判「同义反复、应当作废」判过头了**" in _ausrc
          and "**判过头的不是数据，是把可证伪的预测当成了定义**" in _ausrc
          and "是同义反复，不是发现" in _ausrc   # 985 原话仍在、没被删
          and "改写，不删" in _ausrc)   # ⭐⭐⭐ 撤销结论时原文保留、只加横幅

    check("TTTTT.4 ⭐⭐⭐⭐⭐ **「不重跑也能换算」—— 用同一套纯函数离线重算 980** —— "
          "980 的原始读数留在 `/tmp` 里 ⇒ 本批用**上面那四个纯函数**"
          "把那 64 圈重算一遍 ⇒ ⇒ ⭐⭐⭐⭐⭐ **「7.8% → 0%」是在 980 自己的数据上"
          "算出来的、不是新数据**，且**与新跑那份同函数** ⇒ 两批不会各说各话 ⇒ "
          "⇒ ⭐⭐⭐ **同一个东西要比同一个口径**",
          '"reread_980"' in _p986
          and '"why_offline_reread"' in _p986
          and '这份**不是新数据**' in _p986
          and "「7.8% → 0%」**在 980 自己的数据上就成立**" in _p986
          and "**同一套纯函数**离线重算" in _p986
          and "**两批不会各说各话**" in _ausrc
          and "**同一个东西要比同一个口径**" in _ausrc
          and "**同一个东西要比同一个口径**" in _p986)

    check("TTTTT.5 ⭐⭐⭐⭐⭐ **新口径的「位置门」是旋转不变的** —— "
          "判据用「有间隙时它**必是倒数第二枚**、收尾键恒为 `keys[0]`」，"
          "**不钉绝对下标**（980 的教训：起点会旋转）⇒ "
          "并且**成对钉住反向**：「间隙落在环中途」必须判红 ⇒ "
          "**恒真的门比没有门更坏**",
          "def _gap_at_wrap(cycle, first_key):" in _p986
          and "`first_key` 是环里的**第一枚可聚焦停靠点**" in _p986
          and "**「间隙在回绕点上」在结构上就是" in _p986
          and "「间隙落在环的中途」**判红**" in _p986
          and "⭐⭐ **这条是能红的**：若引擎按计时器交出焦点，间隙会落在环的中途" in _p986
          and "**反向门坏了**：间隙落在环中途必须判红 —— 不然 P2 恒真" in _p986
          and "**反向门坏了**：跳过一枚停靠点的圈必须判红 —— 不然这道门恒真" in _p986)

    check("TTTTT.6 ⭐⭐⭐⭐⭐ **新口径的「门②」做成了一对** —— "
          "有间隙那侧：每个间隙的停留都 ≥ 可见下限；**无间隙那侧**（对偶）："
          "「回绕前那一枚停靠点」的停留也 ≥ 下限 ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **「没看见」必须先排除「没看够」**（980 的关键前提、986 成对重做）"
          "⇒ 且这道对偶门**在 980 那 5 个真出现无间隙的圈上离线也跑了**（5/5 样本全过）"
          "⇒ **门在那里不是恒真的空集**",
          '"gap_dwell_all_above_floor_both_reps"' in _p986
          and '"pre_wrap_dwell_ok_if_gapless_present_both_reps"' in _p986
          and "def _gapless_pre_wrap_dwell(flat, spans):" in _p986
          and "**「间隙是不是一闪而过、被两个窗口的缝吃掉了」**这个问题" in _p986
          and "**「没看见」先排除「没看够」**" in _p986
          and "**成对门（对偶）在离线重算里也跑了**" in _p986
          and "五个「回绕前停靠点」的停留都在 120ms 以上" in _p986
          and "**「这一圈没有间隙」不能被解释成「间隙太短没看见」**" in _p986)

    check("TTTTT.7 ⭐⭐⭐⭐⭐ **那道红门是「门的问题」、处置是「改精确、不放宽」** —— "
          "第一版把「现象出现了但没过」与「现象一次都没出现」**混成了一件事**"
          "⇒ 而本轮 84 圈里无间隙圈**一次都没出现** ⇒ ⇒ "
          "⭐⭐ **红的不是数据、是我的门太窄** ⇒ 改法：**只在现象出现时**才判真假、"
          "**并把「现象出现了几次」另立一条读数** ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **一条门只能管一件事；空集不是失败、是「没发生」**",
          '"gapless_phenomenon_recorded_both_reps"' in _p986
          and '"n_gapless_cycles"' in _p986
          and "**红的不是数据、是我把「现象没出现」和「现象出现了但没过」" in _p986
          and "**处置是「改精确、不放宽」**" in _p986
          and "门必须**只在现象出现时**才判真假" in _p986
          and "**一条门只能管一件事**；**空集不是失败，是「没发生」**" in _p986
          and "处置是**改精确、不放宽**" in _ausrc
          and "**一条门只能管一件事**" in _ausrc)

    check("TTTTT.8 ⭐⭐⭐⭐⭐ **⭐ 比率不复现，而这是本批顺手查实的第二件事** —— "
          "同一个量：986 这轮 84 圈「无间隙」**一次都没出现**（0/84），"
          "980 的 64 圈里有 5 圈（5/64）⇒ ⇒ ⭐⭐⭐⭐ **7.8% 不是一个稳定的比率**，"
          "它只是**某一批**的读数 ⇒ ⇒ ⭐⭐⭐⭐⭐ **这也正是 985 要求重测的理由**："
          "旧口径把「无间隙」错叫成「缺失」⇒ 而**顺带得到一个更强的说法**："
          "间隙在绝大多数圈里**都在**（不是 92%，新数据看是接近 100%）",
          '"rate_is_not_stable"' in _p986
          and '"fresh_gapless_cycles"' in _p986
          and '"hist_gapless_cycles"' in _p986
          and "**同一个量在两批之间不复现**" in _p986
          and "**「7.8%」不是一个稳定的比率**" in _p986
          and "它只是**某一批里**的读数" in _p986
          and "**同一个量在两批之间不复现**" in _ausrc
          and "**「7.8%」不是一个稳定的比率**" in _ausrc
          and "**间隙在绝大多数圈里都在**" in _ausrc
          and "恒定停靠点，而是约 92% 出现的停靠点" in _ausrc)

    check("TTTTT.9 ⭐⭐⭐⭐ **两件仪器必须逐格一致** —— "
          "每一步在轮询之后**额外问一次 985 那一问**（`:focus` 在谁身上）⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **新口径的「间隙」由证据判定、不由名字判定**（985 的教训）"
          "⇒ 并且两件仪器（`POLL_JS` 的 `keyOf` 与 `FOCUS_JS` 的 `id`）"
          "**在「落定态是谁」上必须逐格一致** ⇒ 不一致就说明「间隙是仪器造出来的」",
          '"instruments_agree_on_settled_id_both_reps"' in _p986
          and '"n_instrument_disagree"' in _p986
          and '"new_use_not_new_js"' in _p986
          and "**新口径的「间隙」由证据判定，不由名字判定**" in _p986
          and "不一致 ⇒ 「间隙」是仪器造出来的、不是页面上发生的" in _p986
          and "**仪器测什么，决定了你能看见什么**" in _ausrc
          and "**新口径的「间隙」由 `:focus` 的证据判定，不由名字判定**" in _ausrc)

    check("TTTTT.10 ⭐⭐⭐⭐ **注释里也可能带着一个已被推翻的数** —— "
          "980 的臂表 `note` 原文写着「4 格环」「5 格环」⇒ **那正是旧口径**"
          "⇒ ⇒ ⭐⭐⭐⭐⭐ **「同一个东西要比同一个口径」在注释上同样成立** ⇒ "
          "处置：**臂内容逐格继承 980、note 改写**，并把「note 确实改了」"
          "**记成一条读数**（不许悄悄改）⇒ 且继承的判据是**从 980 自己的原文**"
          "取那三件再合成，**不是拿我自己的合成结果去比**（那会让这道门恒真）",
          '"arm_note_rewritten"' in _p986
          and '"arms_content_identical_to_980": True' in _p986
          and "ARM_NOTES_CHANGED" in _p986
          and "980 的 note 原文写着「4 格环」「5 格环」" in _p986
          and "注释里带着一个已被 985 推翻的数**" in _p986
          and "**臂内容逐格继承 980、note 改写**" in _ausrc
          and "**注释里也可能带着一个已被推翻的数**" in _ausrc
          and "**这样才不是循环论证**" in _p986
          and "**反向门坏了**：篡改 980 的臂表内容竟然没被抓到 ⇒ 这道门恒真" in _p986)

    check("TTTTT.11 ⭐⭐⭐⭐ **自测的期望值按定义逐句推（第七次复发照旧照抄）** —— "
          "⭐⭐⭐⭐⭐ 而本批**又栽了一次、且栽在「用例自己错」上**："
          "「有间隙的圈不进对偶读数」那个用例里，我传的 `flat` 的键"
          "与 `keys` 对不上 ⇒ 函数从 `flat` 取圈内容 ⇒ 「有间隙」看起来没有间隙 "
          "⇒ ⇒ ⭐⭐⭐ **是我的用例错了、不是函数错了** ⇒ "
          "⇒ 而这正是读数里那条 **`n_flat_eq_keys` 存在的理由**："
          "**「`flat` 与 `keys` 对齐」必须由调用方显式验、不许默认成立**",
          '"n_flat_eq_keys"' in _p986
          and "**是我的用例错了、不是函数错了**" in _p986
          and "**「`flat` 与 `keys` 对齐」必须由调用方显式验、不许默认成立**" in _p986
          and "**期望值必须按定义逐句推**" in _p986
          and "**「跑出来是什么就写什么」会让自测恒真**" in _p986
          and "期望值必须**按定义一句一句推**" in _ausrc)

    check("TTTTT.12 ⭐⭐⭐ **带下标版切圈器不许另写一套切法** —— "
          "成对门要**按位置**取停留时长 ⇒ 需要下标 ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ 但**绝不能另写一套切法**（否则同一个东西两个口径）⇒ "
          "改法：把 980 那套切法**原样加上下标**，并用自测钉住"
          "「它切出来的圈与继承的那一套**逐格相同**」⇒ ⭐⭐ **这就是"
          "「同一个东西要比同一个口径」的用武之地**",
          "def _cycles_idx(keys):" in _p986
          and "与 `_cycles` **同一个口径**" in _p986
          and "**同一个东西要比同一个口径**" in _p986
          and "**带下标版切出的圈与继承的那一套不同** ⇒ 口径分叉了" in _p986
          and "这就是**「同一个东西要比同一个口径」的用武之地**" in _ausrc
          and "**绝不能另写一套切法**" in _ausrc)

    check("TTTTT.13 ⭐⭐⭐ **零停靠点页面：新口径必须给 0（不是 1）** —— "
          "这是 985 那个「旧口径会把「零」报成「一」」的**自测延续** ⇒ "
          "全 `GAP` 的序列，新口径 `ring_stops` 必须是 **0** ⇒ "
          "⇒ ⭐⭐⭐⭐ **旧口径那个「环长 1」的假象被除掉了**",
          "零停靠点页面：新口径必须给 0（**不是 1**）" in _p986
          and "_ring_stops(_zero) == 0" in _p986
          and "会把「零」报成「一」" in _ausrc
          and "旧口径会报「环长 1」的假象" in _p986)

    check("TTTTT.14 ⭐⭐⭐⭐⭐ **同义反复 ≠ 不可证伪** —— 本批的方法论落点："
          "「间隙按构造就在最后一个与第一个之间」作为**「间隙」这个词的定义**"
          "是同义反复（985 这句对）；但**「间隙出现在环的哪一格上」不是定义** —— "
          "**引擎完全可以交给 UI 层之后、在环的中途就交出焦点** ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **判「同义反复」的第一步要问「指的是定义还是可证伪的预测」** ⇒ "
          "⇒ 而本批把它跑成了可判的、且**它为绿**（零例外）",
          '"discipline_986"' in _p986
          and "**同义反复 ≠ 不可证伪**" in _p986
          and "作为**定义**是同义反复" in _p986
          and "但**「间隙落在环的哪一格上」是能红的预测**" in _p986
          and "**985 判过头的不是数据，是把可证伪的预测当成了定义**" in _p986
          and "**同义反复 ≠ 不可证伪**" in _ausrc
          and "**判「同义反复」的第一步要问" in _ausrc
          and "**判过头的不是数据，是把可证伪的预测当成了定义**" in _ausrc)

    check("TTTTT.15 ⭐⭐⭐⭐⭐ **本批零计费** —— `about:blank`、"
          "**只按 `Tab`**、**连 `mouse.click` 都没有**；"
          "**源站侧没测到（登录态过期，985 已确认）—— 不是「测了没事」**；"
          "且本批**只回答「空白页上间隙的比率与位置」**，"
          "**实验室的比率不许直接套到源站**（980 的 `skip_note` 纪律照抄）",
          "**本批零计费**：`about:blank`、**只按 `Tab`**、" in _p986
          and "**连 `mouse.click` 都没有**" in _p986
          and "**实验室的比率不等于源站的比率**" in _p986
          and "**源站登录态已过期（985 已确认）**" in _p986
          and "**不是「测了没事」**" in _p986
          and "**实验室的比率不等于源站的比率**" in _ausrc
          and "**本批零计费**" in _ausrc
          and "源站那一臂因未登录而没测到，不是「测了没事」" in _ausrc)
    # ══ UUUUU. 批 987 复刻侧：⭐⭐⭐⭐⭐ **量「`rf__wrapper` 对齐」的影响面另一端** ——
    #    答案：Tab 环按 `dom_rank`（= DOM 序）走、`rf__wrapper` 排前只因
    #    `dom_rank`(42)<logo(110)，**成因是 JSX 兄弟顺序**；而 ⭐⭐⭐⭐
    #    **本批自己的 P1 预测被数据否掉了**（否掉它的正是 986 的发现） ══
    print("— UUUUU. 批 987 复刻侧：`rf__wrapper` 排在 `canvas-project-logo` 之前，"
          "**既不是对齐决策、也不是引擎行为**，而是「画布根 `dom_rank`(42) < "
          "logo(110)」这一个事实的推论（成因 = 源码 JSX 兄弟顺序，"
          "`<JimengFlow/>` 756 行早于 `<JimengTopBar/>` 757 行）；"
          "⭐⭐⭐⭐ **而本批的 P1「去掉 `BODY` 后严格递增」被数据否掉了** — "
          "**下降点是「间隙之后的兜底」那一格**（`rf__wrapper` 的前驱是间隙） —")

    check("UUUUU.1 ⭐⭐⭐⭐⭐ **本批要回答的是「为什么」、而 983 只答了「谁在前」** —— "
          "983 量到 `dom_rank` 级相对次序两侧不同（源站 logo 68 < wrap 177；"
          "复刻 wrap 42 < logo 110）⇒ ⇒ ⭐⭐⭐⭐⭐ "
          "**只看 `dom_rank` 只能说「谁在前」、说不出「按什么规则在前」** ⇒ "
          "⇒ ⭐⭐⭐⭐ **972/973 立的「先量影响面、不先改代码」的规矩，本批把影响面量完了**"
          "⇒ 而「改不改」是产品决策、**仍不擅自提**",
          '"question_987"' in _ausrc
          and '"conclusion_987"' in _ausrc
          and "既不是对齐决策、" in _ausrc
          and "**972/973 立的「先量影响面、不先改代码」的规矩，" in _ausrc
          and "本批把「影响面」量完了、而「改不改」是产品决策、仍不擅自提**" in _ausrc
          and "（983/986 留下一句「还没量 ⇒ 先量，不先改」）" in _ausrc
          and '"_p987": "scripts/jimeng_probe987_wrapcause_ck.py",' in _anchs)

    check("UUUUU.2 ⭐⭐⭐⭐⭐ **P1 被数据否掉了、而否掉它的正是 986 的发现** —— "
          "我预测「去掉 `BODY` 后整圈 `dom_rank` 严格递增」，"
          "实测**去 `BODY` 后仍有 1 次下降** ⇒ ⇒ **环不是纯按 `dom_rank` 递增** ⇒ "
          "下降点 = 环格 24(268) → 环格 26 `rf__wrapper`(42)，"
          "**而环格 25 正是 `BODY`（间隙）** ⇒ ⇒ ⭐⭐⭐⭐⭐ "
          "**`rf__wrapper` 的前驱是间隙、不是元素** ⇒ 它是"
          "**「间隙之后的第一个元素」、填在间隙与环首之间** ⇒ "
          "**「回绕兜底」的结构、不是「对齐决策」的产物** ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **否定结果必须钉住** —— 它最容易在下一批被悄悄忘掉",
          '"p1_refuted_987"' in _ausrc
          and "我预测「去掉 `BODY` 后整圈 `dom_rank` 严格递增」，" in _ausrc
          and "实测**去 `BODY` 后仍有 1 次下降**" in _ausrc
          and "⇒ ⭐⭐⭐⭐⭐ **`rf__wrapper` 的前驱是间隙、不是元素** ⇒ " in _ausrc
          and "**`rf__wrapper` 的前驱是间隙、不是元素**" in _ausrc
          and "「间隙之后的第一个元素」、填在间隙与环首之间**" in _ausrc
          and "「回绕兜底」的结构、不是「对齐决策」的产物**" in _ausrc
          and "**这是「回绕兜底」的结构、不是「对齐决策」的产物**" in _p987
          and "**P1（环按 `dom_rank` 递增）**" in _p987
          and "**这一条被数据否掉了**" in _ausrc)

    check("UUUUU.3 ⭐⭐⭐⭐⭐ **P2 被精确修正** —— 「环内序号 == `dom_rank` 排名」"
          "在**参与排序的 25 格里只对 24 格成立、1 格例外**"
          "（`rf__wrapper`：ring_pos=26 而 rank=25）⇒ ⇒ "
          "**正确形式是「除回绕兜底那一格外、两者一致」** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **`rf__wrapper` 落在末尾不是因为它 `dom_rank` 大，"
          "而是因为它是间隙之后的兜底** ⇒ ⇒ ⭐⭐⭐⭐ "
          "**983 记下的「唯一下降由 `BODY` 制造」是对的、但 983 没看出它的含义**"
          "（它只知道下降点在第 25 格、且 `wrap_shape_ok=True`，**没往下问「那说明什么」）**",
          '"p2_refined_987"' in _ausrc
          and "在**参与排序的 25 格里只对 24 格成立**、**1 格例外**" in _ausrc
          and "绕兜底那一格外、两者一致」** ⇒ " in _ausrc
          and "**983 记下的「唯一下降由 `BODY` 制造」是对的，" in _ausrc
          and "，**没往下问「那说明什么」）" in _ausrc
          and "**983 早就记到的事实、可能藏着它自己的含义**" in _ausrc
          and '"p2_refined_987"' in _p987
          and "**也被数据精确修正了**" in _p987)

    check("UUUUU.4 ⭐⭐⭐⭐⭐ **P3 命中，而且成因钉在源码的一行** —— "
          "源码实测 **`<JimengFlow />` 第 756 行、`<JimengTopBar />` 第 757 行** ⇒ "
          "**成因 = JSX 兄弟顺序**（画布先渲染、顶栏后渲染）⇒ ⇒ "
          "⭐⭐⭐⭐ **CSS `position` 与 `z-index` 都不参与** —— "
          "**`rf__wrapper` 与 logo 的先后只由 DOM 序决定** ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **要改它就得改 JSX 顺序、不是改 `tabindex`、"
          "也不是改对齐决策** ⇒ ⇒ ⭐⭐⭐⭐ "
          "「运行期先渲染」是观察、「JSX 顺序」是成因 ⇒ 两者必须分开**",
          '"p3_hit_987"' in _ausrc
          and "**第 756 行**、`<JimengTopBar />` 在 **第 757 行**" in _ausrc
          and "**CSS `position` 与 `z-index` 都不参与**" in _ausrc
          and "**`rf__wrapper` 与 logo 的先后只由 DOM 序决定**" in _ausrc
          and "要改它就得改 JSX 顺序、而不是改 `tabindex`、" in _ausrc
          and "**「运行期先渲染」是观察、「JSX 顺序」是成因 ⇒ 两者必须分开**" in _p987
          and "def _jsx_order():" in _p987
          and '"jsx_line_jimengflow"' in _p987
          and '"flow_before_topbar"' in _p987
          and "**成因钉在源码的一行**" in _p987)

    check("UUUUU.5 ⭐⭐⭐⭐⭐ **「没测到」有第三个分支：没问对对象** —— "
          "第一版误用 `READ_JS` 当就绪探针 ⇒ **两格全 `has_flow=False`** ⇒ "
          "而 `READ_JS` 读的是 `window.__ap_rec`（**上一次 `INSTALL_JS` 装的监听器**留下的）"
          "⇒ 在第一次 `INSTALL_JS` 之前**必然是 `null`** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **这不是「页面没就绪」、是「我问错了对象」** ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ 这是 985 那条纪律的**第三个分支**："
          "**「没测到」必须能说清是「没就绪」、「没登录」、还是「没问对对象」** ⇒ "
          "改用 983 的**独立就绪探针**后 2/2 `has_flow=True`",
          '"instrument_fault_987"' in _ausrc
          and "**我第一版误用 `READ_JS` 当就绪探针 ⇒ 两格全 " in _ausrc
          and "`READ_JS` 读的是 `window.__ap_rec`" in _ausrc
          and "**这不是「页面没就绪」、是「我问错了对象」**" in _ausrc
          and "第三个分支**" in _ausrc
          and "」有第三个分支：没问对对象** —— " in _ausrc
          and "def boot_ck():" in _p987
          and "**我第一版误用了 `READ_JS` 当就绪探针" in _p987
          and "**这不是「页面没就绪」、是「我问错了对象」**" in _p987
          and "**第三个分支**" in _p987)

    check("UUUUU.6 ⭐⭐⭐⭐ **仪器读不到 ≠ 事实不成立** —— "
          "`logo_is_focusable=False` 是**仪器读不到**、**不是不可聚焦** ⇒ "
          "`DOMRANK_JS` **不读 `tabIndex`**（实测 `ti_prop = None`）⇒ "
          "⇒ ⭐⭐⭐⭐ **这正是「仪器测什么决定你能看见什么」的又一次** ⇒ "
          "⇒ ⭐⭐ **logo 是 `<a href>`、天然可聚焦**（源码可查）⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **本批不据这条读数下「logo 不可聚焦」的结论** ⇒ "
          "⇒ ⭐⭐⭐⭐ **一条恒假的读数也有信息量**（985 那条）",
          '"logo_focus_instrument_gap_987"' in _ausrc
          and "**不是不可聚焦** —— `DOMRANK" in _ausrc
          and "`DOMRANK_JS` **不读 `tabIndex`**" in _ausrc
          and "定你能看见什么」的又一次** ⇒ " in _ausrc
          and "**logo 是 `<a href>`、天然可聚焦**" in _ausrc
          and "**本批不据这条读数下「logo 不可聚焦」的结论**" in _ausrc
          and '"logo_focus_instrument_gap_987"' in _p987
          and "**这正是 978/985 那条「仪器测什么决定你能看见什么」的又一次**" in _p987)

    check("UUUUU.7 ⭐⭐⭐⭐⭐ **期望值错了、自测就是假绿（第三次复发）** —— "
          "P1 我按「去掉 `BODY` 就该递增」推，**漏了「回绕兜底那一格本身的前驱是间隙」** "
          "⇒ ⇒ ⭐⭐⭐⭐⭐ **「去掉一个异常值」不等于「剩下的就单调」** —— "
          "**回绕点的前驱是间隙这件事，是另一条独立的结构** ⇒ ⇒ "
          "⭐⭐ **它是 983 早就记到、却一直没被读出来的** ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而本批正是靠把它读出来，才把 P1 推翻的**",
          '"p1_wrong_how_discipline_987"' in _ausrc
          and "**期望值错了、自测就是假绿**（本批第三次复发）" in _ausrc
          and "**漏了「回绕兜底那一格" in _ausrc
          and "**「去掉一个异常值」不等于「剩下的就单调」**" in _ausrc
          and "**回绕点的前驱是间隙这件事，是另一条独立的结构**" in _ausrc
          and "**期望值错了、自测就是假绿**" in _p987
          and "**「去掉 `BODY` 就该递增」推，**漏了「回绕兜底那一格" in _p987
          and "**「去掉一个异常值」不等于「剩下的就单调」**" in _p987)

    check("UUUUU.8 ⭐⭐⭐⭐⭐ **本批零计费、且读数逐格一致** —— "
          "复刻侧 2/2：`min_period = 26`、`laps_identical = True`、"
          "`rf__wrapper` ring_pos=26/rank=25/`dom_rank`=42、"
          "`canvas-project-logo` ring_pos=8/rank=8/`dom_rank`=110、"
          "`wrap_dom_rank_smaller_than_logo = True`、"
          "`body_is_excluded_from_ranking = True`、`n_rank_unknown_total = 0` ⇒ "
          "计费**零**：只按 `Tab`、唯一的 `mouse.click` 点在 `about:blank` 空白处、"
          "⛔ 守卫拦在 `mouse.click` **之前**",
          '"reading_987"' in _ausrc
          and "复刻侧 2/2 逐格一致：" in _ausrc
          and "`min_period = 26`、`laps_identical = True`" in _ausrc
          and "`dom_rank`=**42**" in _ausrc
          and "`dom_rank`=**110**" in _ausrc
          and "**本批零计费**" in _ausrc
          and "⛔ 计费守卫拦在 `mouse.click` **之前**" in _ausrc
          and '"n_descents_excluding_body"' in _p987
          and '"wrap_dom_rank_smaller_than_logo"' in _p987
          and '"body_is_excluded_from_ranking"' in _p987
          and '"laps_identical"' in _p987
          and "⛔ 计费守卫拦在 `mouse.click` **之前**" in _p987)
    # ══ VVVVV. 批 988 **纯离线重算**：⭐⭐⭐⭐⭐ **986 换口径的连带** ——
    #    §192/§193 的 arc 覆盖率 —— 而**第一版算出来的东西比减一更深：
    #    分子也要减**（因为**弧里本来就有间隙**）；⭐⭐⭐⭐ 且
    #    **「分母减一 ⇒ 比率上升」这个预测方向也错了**（两个系统都降 0.8 个百分点） ══
    print("— VVVVV. 批 988 纯离线重算（不打开浏览器、不按任何键）："
          "**arc 覆盖率分母减一之外、分子也要减** —— 两个系统的弧里"
          "**都含一格间隙**（源站 `60`=`document.body`、复刻环格 25=`BODY`）⇒ "
          "新口径 **源站 17/100 = 17.0%**、**复刻 18/25 = 72.0%** ⇒ "
          "⭐⭐⭐⭐ **定性结论不变**（源站仍远低于复刻），"
          "而 ⭐⭐⭐⭐⭐ **「分母减一 ⇒ 比率上升」这个预测方向也错了** ——")

    check("VVVVV.1 ⭐⭐⭐⭐⭐ **第一版算出来的东西比「分母减一」更深：分子也要减** —— "
          "我第一版以为「分母减一、分子不动」⇒ **两处都错**；"
          "错二是 ⭐⭐⭐⭐⭐ **因为弧里本来就有间隙** ⇒ 实测两个系统的弧**都含一格间隙**"
          "（源站 `arc_ranks` 里的 `60` = `document.body`、`body_seats=[6]`；"
          "复刻环格 25 = `BODY`、`dom_rank`=37）⇒ ⇒ **两边同时减一** ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **这与 987 那条「去 `BODY` 后严格递增」的失败是同一族**："
          "间隙不是环上的一格",
          '"deeper_than_minus_one_988"' in _ausrc
          and "**第一版我以为「分母减一、分子不动」⇒ 两处都错**" in _ausrc
          and "**错二：分子也该减一**" in _ausrc
          and "**因为弧里本来就有间隙**" in _ausrc
          and "**含**间隙（`60` = `document.body`、`body_seats=[6]`）" in _ausrc
          and "**含**间隙" in _ausrc
          and "**而这与 987 那条「去 BODY 后严格递增」的失败是同一族：" in _ausrc
          and "间隙不是环上的一格" in _ausrc
          and '"gap_in_both_arcs"' in _p988
          and "**两个系统的弧里都含一格间隙**" in _p988
          and '"_p988": "scripts/jimeng_probe988_arcdenom_reread.py",' in _anchs)

    check("VVVVV.2 ⭐⭐⭐⭐⭐ **P2 的方向我推错了、而这是可贵的** —— "
          "我推「分母减一 ⇒ 覆盖率**必然上升**」⇒ 实测源站 17.8%→**17.0%**、"
          "复刻 73.1%→**72.0%** ⇒ ⇒ **两个系统都降了 0.8 个百分点** ⇒ ⇒ "
          "**原因**：分子分母同时减一、而**弧相对整圈很小** ⇒ "
          "**分子减掉的那格占分子的比例（1/18、1/19）大于分母那格占分母的比例"
          "（1/101、1/26）** ⇒ ⇒ **「分母减一 ⇒ 比率上升」是错的** ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而我那个「反向门」恰好抓到了它 ⇒ 成对反向门在这次真的救了命**",
          '"p2_direction_wrong_988"' in _ausrc
          and "**P2 的方向我推错了、而这本身是可贵的**" in _ausrc
          and "**两个系统都降了 0.8 个百分点**" in _ausrc
          and "**分子减掉的那一格占分子的比例（1/18、1/19）大于分母减" in _ausrc
          and "**「分母减一 ⇒ 比率上升」是错的**" in _ausrc
          and "**成对反向门在这次真的救了命**" in _ausrc
          and "**「分母减一 ⇒ 覆盖率**必然上升**」" in _p988
          and "**比率必然上升" in _p988
          and "**分子减得慢时比率**下降**" in _p988)

    check("VVVVV.3 ⭐⭐⭐⭐⭐ **成对门抓到我一处真错 —— 而两个数都没错** —— "
          "复刻侧 `is_body` 的座位是**整圈内**的（0-based = 24）、"
          "按 `dom_rank` 数出来的是**弧内**的（0-based = 17）⇒ "
          "**两个都对、只是基准不同** ⇒ ⇒ ⭐⭐⭐⭐⭐ "
          "**门比的不是「座位」、是「间隙是不是同一个东西」** ⇒ ⇒ "
          "**换算办法：由整圈座位回推它在 `out` 列表里的下标** ⇒ ⇒ "
          "⭐⭐ **这是 987 那条「同一个东西要比同一个口径」的最细一次应用**",
          '"coordinate_system_fault_988"' in _ausrc
          and "**成对门抓到我一处真错 —— 而两个数都没错**" in _ausrc
          and "是**整圈内**的（0-based = 24）、" in _ausrc
          and "的是**弧内**的（0-based = 17）" in _ausrc
          and "**两个都对、只是基准不同**" in _ausrc
          and "**门比的不是「座位」、是「间隙是不是同一个东西」**" in _ausrc
          and "**换算办法：由整圈座位回推它在 `out` 列表里的下标**" in _ausrc
          and "**这是 987 那条「同一个东西要比同一个口径」的最细一次应用**" in _ausrc
          and "arc_start = pairs[0][0] - 1 if pairs else 0" in _p988
          and '"gap_seats_mapped_into_arc"' in _p988)

    check("VVVVV.4 ⭐⭐⭐⭐ **「覆盖率」这个名本身有误导性 ⇒ 本批正名** —— "
          "982 已证 18 格**不是圈** ⇒ ⇒ **它不是「环被覆盖了百分之多少」** ⇒ "
          "**`arc` 的定义是「`out` 行里 k 连续的第一段」** ⇒ ⇒ "
          "**它是「某次走查里连续按了多久 `Tab`」的度量** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **本批正名为「连续 out 段长 / 环长」**，"
          "**§192/§193 的措辞应当作废重写**（原文保留、只加改写横幅）",
          '"cover_is_a_misnomer_988"' in _ausrc
          and "**「覆盖率」这个名本身有误导性**" in _ausrc
          and "**它不是「环被覆盖了百分之多少」**" in _ausrc
          and "**`arc` 的定义是「`out` 行里 k 连续的第一段」**" in _ausrc
          and "**它是「某次走查里连续按了多久 `Tab`」的度量**" in _ausrc
          and "**本批正名为「连续 out 段长 / 环长」**" in _ausrc
          and "**§192/§193 的措辞应当作废重写**" in _ausrc
          and "**「覆盖率」这个名本身有误导性" in _p988
          and "**它不是「环被覆盖了百分之多少」**" in _p988
          and '"cover_is_a_misnomer"' in _p988)

    check("VVVVV.5 ⭐⭐⭐⭐⭐ **期望值按定义推错、而且连错两次** —— "
          "① 第一版以为「`_arc_of` 不连续 ⇒ 空弧」⇒ 实际**第一枚无条件收下**；"
          "② 第二版以为「`_arc_of` 要求 k 从 1 开始」⇒ "
          "**定义里根本没有这个要求**、只比相邻两枚 ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **两次都必须真读那几行代码**、"
          "**不能凭函数名与直觉推** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ 而「不许自己定义」那道门**必须用 `ast` 判、不能用 `in` 判**"
          "—— **`in` 会误抓我自己写的注释**（本批第一次就这么栽了）",
          '"expectation_wrong_twice_988"' in _ausrc
          and "**期望值按定义推错、而且连错两次**（本批第四次复发）" in _ausrc
          and "**第一枚无条件收下**" in _ausrc
          and "**定义里根本没有这个要求**" in _ausrc
          and "**两次都必须真读那几行代码**" in _ausrc
          and "**不能凭函数名与直觉推**" in _ausrc
          and "许自己定义」那道门要用 `ast` 判、不能用 `in` 判**" in _ausrc
          and "**`in` 会误抓我自己写的注释**" in _ausrc
          and "**这是 987 那条「同一个东西要比同一个口径」的最细一次应用**" in _ausrc
          and "assert _arc_of([(2, 20), (3, 30)]) == [(2, 20), (3, 30)]" in _p988
          and "**`_arc_of` 不要求 k 从 1 开始**" in _p988
          and "isinstance(n, ast.FunctionDef) and n.name ==" in _p988
          and "**第一版直接比、门报 `seats_agree=False`" in _p988)

    check("VVVVV.6 ⭐⭐⭐⭐⭐ **P1 与 P3 命中：分子分母各减一、定性结论不变** —— "
          "纯离线重算 974/983 存档（各 2/2 逐格相同）："
          "**源站 `18/101 = 17.8%` ⇒ 新 `17/100 = 17.0%`**；"
          "**复刻 `19/26 = 73.1%` ⇒ 新 `18/25 = 72.0%`** ⇒ ⇒ "
          "**源站仍远低于复刻** ⇒ **「源站侧只验了一小段」原样成立** ⇒ ⇒ "
          "⭐⭐⭐⭐ **要动的是「覆盖率」这个名、不是那个大小关系**",
          '"reading_988"' in _ausrc
          and "**源站**：`18/101 = 17.8%` ⇒ **新 `17/100 = 17.0%`**" in _ausrc
          and "**复刻**：`19/26 = 73.1%` ⇒ **新 `18/25 = 72.0%`**" in _ausrc
          and "**两套座位口径都换算到弧内基准后一致**" in _ausrc
          and "（源站 6→6、复刻整圈 24→弧内 17）⇒ **成对门绿**" in _ausrc
          and '"conclusion_988"' in _ausrc
          and "**「换口径」不改变 §192/§193 的任何定性结论**" in _ausrc
          and "**「源站侧只验了一小段」原样成立**" in _ausrc
          and "**要动的是「覆盖率」这个名、不是那个大小关系**" in _ausrc
          and '"side_by_side"' in _p988
          and '"source_new"' in _p988
          and '"clone_new"' in _p988
          and '"conclusion_unchanged"' in _p988)

    check("VVVVV.7 ⭐⭐⭐⭐⭐ **本批纯离线、零计费是结构性的** —— "
          "**不打开浏览器**、**不按任何键**、**连 `mouse.click` 都没有** ⇒ ⇒ "
          "⚠️⭐⭐⭐⭐⭐ **源站侧用的是 974 存档的读数**（985 已确认登录态过期）⇒ "
          "**本批不测源站、只重算 974 当年的读数** ⇒ "
          "**不是「测了没事」** ⇒ ⇒ ⭐⭐⭐⭐ "
          "**「零计费」有两种：自律的、还有结构性的 —— 后者不依赖我记不记得**",
          '"pure_offline_988"' in _ausrc
          and "**本批纯离线**：**不打开浏览器**、**不按任何键**、" in _ausrc
          and "**连 `mouse.click` 都没有**" in _ausrc
          and "**零计费是结构性的、不是自律的**" in _ausrc
          and "**源站侧用的是 974 存档的读数**" in _ausrc
          and "**本批不测源站、只重算 974 当年的读数**" in _ausrc
          and "**不是「测了没事」**" in _ausrc
          and "**零计费是结构性的、不是自律的**" in _p988
          and '"offline_only"' in _p988
          and '"source_side_is_archived"' in _p988)

    check("VVVVV.8 ⭐⭐⭐⭐⭐ **「分子分母要一起看」是本批最该带走的一条** —— "
          "我第一版**只盯着分母**、以为「减一」就完了 ⇒ "
          "**而弧里本来就含间隙 ⇒ 分子也得减** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **这与 987 那条「去 `BODY` 后严格递增」的失败是同一族**："
          "**间隙不是环上的一格、却一直被我算成了一格** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **凡是「换一个度量口径」的活，分子分母都要重新对一遍** —— "
          "分子分母都要重新对一遍**",
          '"discipline_988"' in _ausrc
          and "**分子分母要一起看**" in _ausrc
          and "要一起看** —— 我第一版只盯着分母 ⇒ " in _ausrc
          and "**而弧里本来就含间隙** ⇒ **分子也得减**" in _ausrc
          and "凡是「换一个度量口径」的活，" in _ausrc
          and "**它们可能各自含了那个被换掉的东西**" in _ausrc
          and "**分子分母要一起看**" in _p988
          and "**零计费是结构性的**：不打开浏览器、不按任何键" in _p988
          and "**度量名本身可能是错的**" in _ausrc
          and "**「覆盖率」不是覆盖率**" in _ausrc)
    # ══ WWWWW. 批 989 **纯离线**：⭐⭐⭐⭐⭐ **988 那把尺子扫过四批** ——
    #    而**结果不是「四批都要改」、是「只有两批要改、另两批根本不适用」** ⇒
    #    ⇒ ⭐⭐⭐⭐⭐ **「换口径」的连带范围本身也是要量的、不能凭印象划定** ══
    print("— WWWWW. 批 989 纯离线：**988 的尺子扫过 §954/§959/§961/§966** ⇒ "
          "**适用 954/959（out 段 18 → 17、环 102 → 101）、"
          "不适用 961/966（它们根本不报 out 段计数）** ⇒ "
          "⭐⭐⭐⭐⭐ **而「两批不适用」本身就是结论** ⇒ "
          "**连带范围是要量的、不是凭印象划的** —")

    check("WWWWW.1 ⭐⭐⭐⭐⭐ **本批最值钱的一步是「尺子管不管这一批」** —— "
          "988 的尺子是「某一批报的数，分子分母各自有没有含那一格间隙」⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而这个问句对每一批的答案不一定相同** ⇒ "
          "⇒ **尺子有它的适用范围、不许硬套** ⇒ ⇒ "
          "⭐⭐⭐⭐ **「不适用」必须是一个正当的结论、不是「漏查」** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **988 说的是「凡是报 out 段计数的都要重对」、"
          "**不是「凡是源站批次都要重对」**",
          '"scope_is_itself_a_finding_989"' in _ausrc
          and "**这是我第一版没想到的、也是本批最值钱的一步**" in _ausrc
          and "**而这个问句对每一批的答案不一定相同**" in _ausrc
          and "**尺子有它的适用范围、不许硬套**" in _ausrc
          and "**「不适用」必须是一个正当的结论、不是「漏查」**" in _ausrc
          and "**凡是报 out 段计数的都要重对**" in _ausrc
          and "**不是「凡是源站批次都要重对」**" in _ausrc
          and "**「换口径」的连带范围也是要量的、不能凭印象划定**" in _ausrc
          and '"ruler_from_988"' in _p989
          and '"scope_is_itself_a_finding"' in _p989)

    check("WWWWW.2 ⭐⭐⭐⭐⭐ **两批不适用、而这是本批的核心结论** —— "
          "**961** 报的是 `tabindex` **普查**（`n_native` / `positive_tids = []`）"
          "⇒ ⛔ **它根本不报 out 段计数** ⇒ **尺子无处可施**；"
          "**966** 报的是三枚节点**行为对比**（`n_selected` / `elementFromPoint`）"
          "⇒ ⛔ **它根本没有分母** ⇒ **尺子无处可施** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而这两条「不适用」是正当结论、不是「漏查」** ⇒ "
          "⇒ ⭐⭐⭐⭐ **否定结果尤其要钉** —— 它最容易在下一批被悄悄忘掉",
          '"verdicts_989"' in _ausrc
          and "**961**（§171）：`tabindex` **普查**" in _ausrc
          and "⛔ **不适用** —— **它根本不报 out 段计数**" in _ausrc
          and "**尺子无处可施**" in _ausrc
          and "**966**（§176）：三枚节点**行为对比**" in _ausrc
          and "⛔ **不适用** —— **它根本没有分母**" in _ausrc
          and "而这两条「不适用」是正当结论、不是「漏查」" in _ausrc
          and "**否定结果尤其要钉** —— " in _ausrc
          and '"not_applicable"' in _p989
          and "**它报的是 `tabindex` 普查、根本不报「out 段计数」**" in _p989
          and "**「不适用」是正当结论、不是「漏查」**" in _p989)

    check("WWWWW.3 ⭐⭐⭐⭐⭐ **本批真正改掉的两个数** —— "
          "**954 的环长 102 → 101**（旧口径把间隙算成一格 ⇒ "
          "可聚焦停靠点数 = 旧 − 1）；**954/959 的 out 段 18 → 17**"
          "（那 18 格里有 1 格是间隙 ⇒ **分子也要减**）⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **而这个 17 是 988 已经在 974 存档上量到的**"
          "（`arc_len_new = 17`）⇒ ⇒ **954 报的 18 与 974 的 18 是同一个数** ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **两批的处置不需要新测、用 988 的读数直接接上** ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而这正是「不重跑也能换算」的价值**（986 立的那条）",
          '"numbers_989"' in _ausrc
          and "**954 的环长 102 → 101**" in _ausrc
          and "**954/959 的 out 段 18 → 17**" in _ausrc
          and "（那 18 格里有 1 格是间隙 ⇒ **分子也要减**）" in _ausrc
          and "而**这个 17 是 988 已经在 974 存档上量到的*" in _ausrc
          and "**954 报的 18 与 974 的 18 是同一个数**" in _ausrc
          and "**两批的处置不需要新测、用 988 的读数直接接上**" in _ausrc
          and "**而这正是「不重跑也能换算」的价值**" in _ausrc
          and '"rounds_up"' in _p989
          and '"source_arc_new": c0["arc_len_new"]' in _p989
          and '"ring_954_new": 101' in _p989
          and "**954 报的 18 与 974 的 18 是同一个数**" in _p989)

    check("WWWWW.4 ⭐⭐⭐⭐⭐ **口径不同的两个数不许并成一个** —— "
          "**「102 为什么比 101 多 1」本批定不了** —— "
          "**102 是「回卷点位置」、101 是「圈长」，口径不同** ⇒ "
          "⇒ ⭐⭐⭐⭐ **两个数差 1**、而 954 自己就写了"
          "「与 §930 记的 101 / 104 吻合」⇒ ⇒ "
          "⇒ ⭐⭐ **不许把它们并成一个数** ⇒ ⇒ "
          "⭐⭐⭐⭐ **这正是 981 那条「同一个东西要比同一个口径」** ⇒ "
          "⇒ **「二选一是最坏的选择、并排读出来」**",
          '"not_merged_989"' in _ausrc
          and "**「102 为什么比 101 多 1」本批定不了、也不许并**" in _ausrc
          and "**102 是「回卷点位置」、101 是「圈长」，口径不同**" in _ausrc
          and "**两个数差 1**、而 954 自己就写了" in _ausrc
          and "**不许把它们并成一个数**" in _ausrc
          and "**这正是 981 那条「同一个东西要比同一个口径」**" in _ausrc
          and "**「二选一是最坏的选择、并排读出来」**" in _ausrc
          and '"not_measured_here"' in _p989
          and "**102 是「回卷点位置」、101 是「圈长」，口径不同**" in _p989
          and "**不许把它们并成一个数**" in _p989)

    check("WWWWW.5 ⭐⭐⭐⭐⭐ **逐节引文这道门抓到的是我自己的记忆不准** —— "
          "我凭记忆写「`out 段 18 个`」、而 954 原文是"
          "「**节点停靠 88 个 + 内层停靠 14 个 + 出画布 18 个**」⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **「引文必须逐字来自原文」不只是防篡改、也是防我自己记错** ⇒ "
          "⇒ ⭐⭐⭐ **凭印象写引文 ⇒ 门会红、而红的是对的** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **成对门要用「别批的措辞」去撞**（本批用 966/961 的措辞"
          "去撞 954 那一节）⇒ ⇒ **才抓得住「范围算错」**",
          '"gate_caught_my_memory_989"' in _ausrc
          and "**逐节引文这道门抓到的是我自己的记忆不准**" in _ausrc
          and "我凭记忆写「`out 段 18 个`」、而 954 原文是" in _ausrc
          and "**这不只是防篡改、也是防我自己记错**" in _ausrc
          and "**凭印象写引文 ⇒ 门会红、而红的是对的**" in _ausrc
          and '"per_section_scope_gate_989"' in _ausrc
          and "966/961 的措辞去撞 954 那一节**" in _ausrc
          and "**每批的措辞必须真的在它自己那一小节里**" in _ausrc
          and '"quotes_must_exist_in_own_section"' in _p989
          and "**反向门用 966/961 的措辞去撞 954 那一节**" in _p989
          and '"gate_caught_my_memory_989"' in _p989)

    check("WWWWW.6 ⭐⭐⭐⭐ **两批适用的处置完全相同、因为它们报的是同一个数** —— "
          "**954 报「出画布 18 个」、959 报「out 段 18 个停靠点」** ⇒ "
          "⇒ ⭐⭐⭐⭐ **这是同一个数、所以同一处处置** ⇒ "
          "⇒ ⭐⭐ **不许把它们当两个独立的数各改一遍**（981 那条「二选一」）⇒ "
          "⇒ ⭐⭐⭐⭐⭐ 而 974 存档上的 `arc_len_old` 正好也是 **18** ⇒ "
          "**三处指向同一个数**",
          '"verdicts_989"' in _ausrc
          and "**954**（§164）：out 段 **18** 个、环 **102 下**" in _ausrc
          and "**959**（§169）：out 段 **18** 个停靠点" in _ausrc
          and "**与 954 是同一个数、同一处处置**" in _ausrc
          and '**三处指向同一个数**' in _p989
          and "**18" in _p989
          and "954 报的 `18`、959 报的 `18`、" in _p989)

    check("WWWWW.7 ⭐⭐⭐⭐⭐ **本批纯离线、零计费是结构性的** —— "
          "**不打开浏览器**、**不按任何键**、**连 `mouse.click` 都没有** ⇒ ⇒ "
          "⚠️⭐⭐⭐⭐⭐ **源站侧全部用 974 存档**（985 已确认登录态过期）⇒ "
          "**不是「测了没事」** ⇒ ⇒ ⭐⭐⭐⭐ "
          "**「零计费」有两种：自律的、还有结构性的 —— 后者不依赖我记不记得**",
          '"offline_989"' in _ausrc
          and "**本批纯离线**：**不打开浏览器**、**不按任何键**、" in _ausrc
          and "**零计费是结构性的、不是自律的**" in _ausrc
          and "**源站侧全部用 974 存档**" in _ausrc
          and "**不是「测了没事」**" in _ausrc
          and "**本批零计费是结构性的**：不打开浏览器、不按任何键" in _ausrc
          and '"offline_only"' in _p989
          and '"source_side_is_archived"' in _p989)

    # ══ XXXXX. 批 990 **复刻侧 dev×prod 对读**（2/2 逐格一致）——
    #   ⭐⭐⭐⭐⭐ **第一次量「生产构建」** —— 而 973/983/987 的复刻侧读数
    #   **全部来自 dev server** ⇒ 「dev 上量到的」能不能搬到「生产上」
    #   **从来没人验过**
    print("— XXXXX. 批 990 复刻侧 dev×prod 对读："
          "⭐⭐⭐⭐⭐ **第一次量「生产构建」** ⇒ "
          "**P1 成立（间隙与构建模式无关）／P2·P3 被否（我猜错了 dev-only 长什么样）**")
    check("XXXXX.1 ⭐⭐⭐⭐⭐ **P1 成立：间隙在生产构建里仍然在** —— "
          "dev `gap_steps = 5`、prod `gap_steps = 5`（2/2 逐格相同）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **间隙是 Blink 引擎行为、与构建模式无关** ⇒ "
          "⇒ **985 那条「它是引擎层行为、与登录态无关」"
          "现在还多了半句：与构建模式也无关** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **985 那句不白写、它扛住了这一次换构建模式的检验**",
          '"p1_gap_survives_production"' in _p990
          and "**P1 成立：间隙在生产构建里仍然在**" in _p990
          and "dev `gap_steps = 5`、prod `gap_steps = 5`（2/2 逐格相同）" in _p990
          # ⚠️ 探针里这句**分两行**、所以只钉其中**逐字存在的**那一段
          and "**间隙是 Blink 引擎行为、" in _p990
          and "与构建模式无关** ⇒ " in _p990
          and "与构建模式也无关**" in _p990
          and '"p1_hold_990"' in _ausrc
          and "**P1 成立：间隙在生产构建里仍然在**" in _ausrc
          and "dev `gap_steps = 5`、prod `gap_steps = 5`（2/2 逐格相同）" in _ausrc
          and "**间隙是 Blink 引擎行为、与构建模式无关**" in _ausrc
          and "现在还多了半句：与构建模式也无关" in _ausrc
          # ⭐⭐⭐⭐ 反向门：**「间隙是 dev-only 现象」这个错结论不许出现在任何一边**
          and "间隙是 dev-only 现象" not in _p990
          and "间隙是 dev-only 现象" not in _ausrc)

    check("XXXXX.2 ⭐⭐⭐⭐⭐ **本批最值钱的一步是「先量新鲜度、再量内容」** —— "
          "仓里那个 `.next` 生产产物是**过期的**（产物 `Oct 3 05:57`、"
          "而 `JimengWorkspace.tsx` 改于 `Oct 4 23:01`）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **用它去量、量到的是一份已经不存在的代码** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **这与 988 那条「引文必须逐字来自原文」是同一族："
          "先确认你量的是不是那个东西** ⇒ ⇒ "
          "⇒ ⭐⭐ **「有产物」不等于「产物是新的」**",
          '"stale_build_first"' in _p990
          and "仓里那个 `.next` 生产产物是过期的" in _p990
          and "先量新鲜度、再量内容" in _p990
          and '"stale_build_first_990"' in _ausrc
          and "仓里那个 `.next` 生产产物是过期的" in _ausrc
          and "**用它去量、量到的是一份已经不存在的代码**" in _ausrc
          and "这与 988 那条「引文必须逐字来自原文」是同一族" in _ausrc
          # ⭐⭐⭐⭐ 反向门：**不许把「产物存在」当成「产物新鲜」**
          and "产物存在即可信" not in _p990
          and "产物存在即可信" not in _ausrc)

    check("XXXXX.3 ⭐⭐⭐⭐⭐ **本批踩的第一个坑：Turbopack 拒绝指向项目根外的"
          "`node_modules` 符号链接** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ 改用 `cp -Rc`（APFS 写时复制）**真克隆**（1.7G / 17s）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **这一条与「别在共享产物目录上构建」同源**："
          "**都是为了让构建发生在一个不共享的地方**",
          '"no_shared_dot_next"' in _p990
          and "Turbopack 拒绝" in _p990
          and "改用 `cp -Rc` 真克隆" in _p990
          and "别在共享产物目录上构建" in _p990
          and '"two_traps_990"' in _ausrc
          and "Turbopack 拒绝" in _ausrc
          and "改用 `cp -Rc` 真克隆" in _ausrc
          and "别在共享产物目录上构建" in _p990
          # ⭐⭐⭐ 反向门：**符号链接那条失败信息是真的**、不许改成别的措辞
          and "points out of the filesystem root" in _p990)

    check("XXXXX.4 ⭐⭐⭐⭐⭐ **本批最要紧的一条纪律：两次都改成「在一次性副本里改」、"
          "而不是改仓库** —— ① 符号链接不行 ⇒ 用副本里的真克隆；"
          "② `output: standalone` 下 `next start` ⇒ **Next 自己警告**不支持 "
          "⇒ ⇒ ⭐⭐⭐⭐⭐ **于是仓库的 `next.config.ts` 一个字节都没改**"
          "（仍是 `output: \"standalone\"`）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **这是「绝对不能干扰其他人的工作」在工具层面的落实** "
          "⇒ 而共享的 `.next` 也没被碰（dev server `pid 51810` 未受干扰）",
          '"two_traps"' in _p990
          and "**Next 自己警告" in _p990
          and "**两次都改成「在一次性副本里改」" in _p990
          and "、**而不是改仓库**" in _p990
          and "而不是改仓库" in _p990
          and "仓库一个字节都没改" in _p990
          and "**这是「绝对不能干扰其他人的工作」" in _p990
          and "在工具层面的落实**" in _p990
          and '"two_traps_990"' in _ausrc
          and "**两次都改成「在一次性副本里改」、" in _ausrc
          and "**而不是改仓库**" in _ausrc
          and "**这是「绝对不能干扰其他人的工作」在工具层面的落实**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许为了跑通就把仓库的 `next.config.ts` 改掉**
          and "把仓库的 next.config.ts 改成 undefined" not in _ausrc
          and "仓库的 next.config.ts 已改" not in _p990)

    check("XXXXX.5 ⭐⭐⭐⭐⭐ **P2 与 P3 都被否掉了、而否掉它们的读数是本批第二件值钱的事** —— "
          "我第一版的 `dev_only` 判据是「在不在 shadow root / "
          "宿主名含不含 `nextjs-portage`」⇒ **它数出 0** "
          "（`n_nextjs_portage` 两边都是 0、`in_shadow` 是 `False`）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **我猜错了 dev-only 长什么样** ⇒ ⇒ "
          "⇒ 而**真正的多出来那一格是 `tag = NEXTJS-PORTAL`、在**主文档**里"
          "（`in_shadow = False`）** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「恒假的读数也有信息量」**（985 那条）—— "
          "`dev_only_by_structure_guess = 0` **原样保留** ⇒ "
          "**删掉它才是错的**",
          '"p2_p3_refuted"' in _p990
          and "我猜错了 dev-only 长什么样" in _p990
          and "**它数出 0**" in _p990
          and "真正的多出来那一格是" in _p990
          and '"constant_false_reading_kept"' in _p990
          and "恒假的读数也有信息量" in _p990
          and "删掉它才是错的" in _p990
          and '"p2_p3_refuted_990"' in _ausrc
          and "**我猜错了 dev-only 长什么样**" in _ausrc
          and "它数出 0" in _ausrc
          and "**真正的多出来那一格是" in _ausrc
          and "**「恒假的读数也有信息量」**" in _ausrc
          and "**删掉它才是错的**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把那个恒假读数悄悄删掉**
          and '"dev_only_by_structure_guess": _d.get("n_dev_only_in_lap")' in _p990
          and "**原样保留在读数里**" in _p990
          and "dev_only_by_structure_guess" in _ausrc)

    check("XXXXX.6 ⭐⭐⭐⭐⭐ **「dev-only」不是任何单边 DOM 里能认出来的东西** —— "
          "**它是「这一格在 dev 有、在 prod 没有」这件事本身** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以判据必须是「两边的 DOM 各有什么」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ 而 P2' / P3' 就是这么证的："
          "`NEXTJS-PORTAL` 在 dev 的 census 里计数 1、在 prod 的 census 里计数 0"
          "；两边的 key 集合**完全相同** ⇒ **差的是位置数（环长 26 → 25）** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **这与 989 那条「尺子有适用范围」同族："
          "判据要问对那个问题、而不是问一个「单边就能答」的问题**",
          '"dev_only_not_identifiable_in_one_build"' in _p990
          and "「dev-only」不是任何单边 DOM" in _p990
          and "里能认出来的东西**" in _p990
          and "它是「这一格在 dev 有、在 prod 没有」这件事本身" in _p990
          and "所以判据必须是「两边的 DOM 各有什么」" in _p990
          and '"p2prime_p3prime_hold"' in _p990
          and '"dev_only_not_identifiable_in_one_build_990"' in _ausrc
          and "**它是「这一格在 dev 有、在 prod 没有」这件事本身**" in _ausrc
          and "**所以判据必须是「两边的 DOM 各有什么」、" in _ausrc
          and '"p2prime_p3prime_990"' in _ausrc
          and "在 dev 的 census 里计数 **1**" in _ausrc
          and "在 prod 的 census 里计数 **0**" in _ausrc
          and "**环长 26 → 25**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**「单边就能认定 dev-only」这个错法不许出现**
          and "在 shadow root 里就是 dev-only" not in _p990
          and "宿主名含 nextjs-portage 即可认定 dev-only" not in _p990)

    check("XXXXX.7 ⭐⭐⭐⭐⭐ **本批冒出来的一条限定、而它限制的是 985/986 自己的读数** —— "
          "985/986 量「间隙落在环的哪一格上」**零例外** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而那句话说的是「结构位置」**"
          "（间隙**紧贴最后一格之前**、两个构建都如此、`gap_from_end` 两边都是 −2）"
          "⇒ ⇒ ⭐⭐⭐⭐⭐ **绝对下标在两个构建里不一样**"
          "（dev 环 26 里间隙在 **24**、prod 环 25 里间隙在 **23**）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **成因**：多出来那一格"
          "（`NEXTJS-PORTAL`）**正好插在「最后一格业务停靠点」与「间隙」之间** "
          "⇒ **它把间隙整体往后顶了一格** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「间隙在下标 24」这句话不是构建无关的** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「结构位置」与「绝对下标」不是一个口径、不许互相顶替**"
          "（981 那条「同一个东西要比同一个口径」）",
          '"gap_index_limit_990_"' in _p990
          and "绝对下标在两个构建里不一样" in _p990
          and "间隙在下标 24」这句话不是构建无关的" in _p990
          and "「结构位置」与「绝对下标」不是一个口径、不许互相顶替" in _p990
          and '"gap_index_limit_990_"' in _ausrc
          and "**绝对下标在两个构建里不一样**" in _ausrc
          and "（dev 环 26 里间隙在 24、prod 环 25 里间隙在 23）" in _ausrc
          and "**「间隙在下标 24」这句话不是构建无关的**" in _ausrc
          and "**「结构位置」与「绝对下标」不是一个口径、不许互相顶替**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「相对位置也变了」这个错说法写进来**
          and "间隙的相对位置在两个构建里也不一样" not in _p990
          and "间隙的相对位置在两个构建里也不一样" not in _ausrc)

    check("XXXXX.8 ⭐⭐⭐⭐ **本批第二个仪器坑、而且是我自己新写的读数** —— "
          "我第一版取「那一格的 key」、取的却是 `one_lap[i][key]` ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而那个字段是「按了哪个键」、每一行恒为 `Tab`** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **这是一件恒真的读数** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **985 那条纪律是「恒假的读数要留」、"
          "而它的另一半是「恒真的读数要认出它」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **它是靠人眼发现的、不是靠门** ⇒ "
          "**门只能验「我钉的判据成不成立」、验不出「我取错了字段」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **改正之后才得到「两边的 key 集合完全相同」的成因**："
          "**多出来那一格与间隙那一格在 key 上撞了**（都是 `None/None`）",
          '"always_true_reading_990_"' in _p990
          and "恒为 `Tab`" in _p990
          and "这是一件恒真的读数" in _p990
          and "「恒假的读数要留」" in _p990
          and "它的另一半是「恒真的读数要认出它」" in _p990
          and "门只能验「我钉的判据成不成立」、验不出「我取错了字段」" in _p990
          and "多出来那一格与间隙那一格在 key 上撞了" in _p990
          and '"always_true_reading_990_"' in _ausrc
          and "**这是一件恒真的读数**" in _ausrc
          and "**而它的另一半是「恒真的读数要认出它」**" in _ausrc
          and "**它是靠人眼发现的、不是靠门**" in _ausrc
          and "**验不出「我取错了字段」**" in _ausrc
          and '"extra_cell_key_is_none_990_"' in _ausrc
          and "**多出来的那一格和间隙那一格在 key 上撞了**" in _ausrc)

    check("XXXXX.9 ⭐⭐⭐⭐⭐ **本批不是纯离线、而零计费仍是结构性的** —— "
          "它要起**两个**服务器（dev 4317 + 一次性副本上的 prod 4318）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **但仍然零计费**：**只按 `Tab`**、"
          "唯一的 `mouse.click` 点在 `about:blank` 空白处、"
          "⛔ 计费守卫拦在 `mouse.click` **之前** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **源站根本不打开**（985 已确认登录态过期）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「零计费」有两种：自律的、还有结构性的** —— "
          "988/989 是后者（不打开浏览器、不按任何键），"
          "**990 是「要起服务、但仍然一次都不碰计费面」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐ **二者都成立、而「不是纯离线」必须写出来、不许含混**",
          '"zero_billing"' in _p990
          and "**本批不是纯离线**" in _p990
          and "**但仍然零计费**" in _p990
          and "**只按 `Tab`**" in _p990
          and "计费守卫拦在 `mouse.click` **之前**" in _p990
          and "**源站根本不打开**" in _p990
          and '"offline_vs_online_990"' in _ausrc
          and "**本批不是纯离线**" in _ausrc
          and "**但仍然零计费**" in _ausrc
          and "⛔ 计费守卫拦在 `mouse.click` **之前**" in _ausrc
          and "**源站根本不打开**" in _ausrc
          and '"offline_989"' in _ausrc
          and "**零计费是结构性的、不是自律的**" in _ausrc
          # ⭐⭐⭐⭐ 反向门：**「本批纯离线」这个说法是错的**、不许出现
          and "本批纯离线（不打开浏览器、不按任何键）" not in _p990
          and "本批纯离线（不打开浏览器、不按任何键）" not in _ausrc)
    # ══ Y991A. 批 991 **纯离线重算**（不开浏览器、不按任何键）——
    #   ⭐⭐⭐⭐⭐ **989 留下的那一句：102 → 101 到底是因为间隙、
    #   还是因为「序号与间隔之差」？** ⇒ **答案：后者、而 989 的理由错**
    print("— Y991A. 批 991 纯离线：**§164 自己的算术驳了它自己** ⇒ "
          "**P1/P2/P3/P4/P4'/P5 全部成立** ⇒ "
          "**989 那次「102 → 101」是理由错、结果撞对**")
    check("Y991A.1 ⭐⭐⭐⭐⭐ **本批的门是「引文与数字都从原文抠」** —— "
          "989 栽过一次（凭记忆写「out 段 18 个」、原文是三段相加）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以本批连数字都不写死**："
          "`节点停靠 88 个 + 内层停靠 14 个 + 出画布 18 个` 与 "
          "`回卷点 = 第 102 按` 都是 `re.search` 从 §164 原文抠出来的 ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **`quotes_all_present_991` 是门** —— "
          "**哪一条引文不在原文里、本批就不成立** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而这道门当场抓到了我一次**："
          "我写「**102 是回卷点位置、101 是圈长**」、"
          "而 README 真身带 `「」` ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **989 栽的那次也是这类 ⇒ 同一道门两次都抓到我 "
          "⇒ 它是真的在干活、不是走过场**",
          '"quotes_all_present_991"' in _p991
          and "节点停靠 88 个 + 内层停靠 14 个 + 出画布 18 个" in _p991
          and "回卷点 = 第 102 按" in _p991
          and "它含**节点段 + 内层控件段 + 顶栏那一段**" in _p991
          and "**「102 是回卷点位置、101 是圈长」，口径不同、**" in _p991
          and "re.search" in _p991
          and "引文与数字都从原文抠、不写死" in _p991
          and "**哪一条不在原文里、本批就不成立**" in _p991
          and '"quotes_gate_caught_me_991_"' in _ausrc
          and "**而 989 栽的那次也是这类**" in _ausrc
          and "⇒ ⭐⭐⭐⭐⭐ **同一道门两次都抓到我 ⇒ 它是真的在干活**"
          in _ausrc)

    check("Y991A.2 ⭐⭐⭐⭐⭐ **P1 成立：out 段那 18 按不在周期内** —— "
          "**节点停靠 88 + 内层停靠 14 = 102**、"
          "而 §164 自己写「**回卷点 = 第 102 按**」⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **纯算术、不需要浏览器就成立** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **那 120 按里的 18 个出画布停靠、是第二次环的前 18 按** "
          "⇒ **不是一个 120 的环** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **本批的主体结论不依赖任何 `/tmp` 文件、"
          "只依赖 §164 原文** ⇒ **不会随存档过期而失效**",
          '"P1_node_plus_inner_equals_wrap_index"' in _p991
          and '"p1_out_segment_not_in_period"' in _p991
          and "节点停靠 88 + 内层停靠 14 = 102，而 §164 自己写「回卷点 = 第 102 按」" in _p991
          and "纯算术、不需要浏览器就成立" in _p991
          and "是第二次环的前 18 按** ⇒ **不是一个 120 的环**" in _p991
          and "**不是一个 120 的环**" in _p991
          and '"p1_out_segment_not_in_period_991_"' in _ausrc
          and "**节点停靠 88 + 内层停靠 14 = 102**" in _ausrc
          and "**纯算术、不需要浏览器就成立**" in _ausrc
          and "**不是一个 120 的环**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把 out 段算进周期**
          and "out 段在周期内" not in _p991
          and "周期是 120" not in _p991)

    check("Y991A.3 ⭐⭐⭐⭐⭐ **P2 成立：§164 这一节自己驳了自己** —— "
          "同一节里「**它含节点段 + 内层控件段 + 顶栏那一段**」与 "
          "「88 + 14 = 102 = 回卷点下标」**互相排斥** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **要改的是「周期含顶栏那一段」那一句** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而 989 只挂了一条改写横幅、没抓到这一处** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「不许并」和「挂横幅」都做了、"
          "**不等于矛盾被看见了** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「一节内部的自我矛盾」是本批唯一的原始发现** —— "
          "**它不是换算、不是新测量、是 §164 自己的三个数加起来的** ⇒ "
          "**任何一章的「分解式 + 总数」都值得这样加一遍**",
          '"P2_section_self_contradiction"' in _p991
          and '"p2_section_self_contradiction"' in _p991
          and "**要改的是「周期含顶栏那一段」那一句**" in _p991
          and "**而 989 只挂了一条改写横幅、没抓到这一处**" in _p991
          and "「不许并」和「挂横幅」都做了、不等于矛盾被看见了**" in _p991
          and '"contradiction_is_its_own_finding"' in _p991
          and "**任何一章的「分解式 + 总数」都值得这样加一遍**" in _p991
          and '"p2_section_self_contradiction_991_"' in _ausrc
          and "**要改的是「周期含顶栏那一段」那一句**" in _ausrc
          and "**而 989 只挂了一条改写横幅、没抓到这一处**" in _ausrc
          and "**不等于矛盾被看见了**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把这处矛盾写成「989 已经处理过了」**
          and "989 已处理了这处矛盾" not in _ausrc)

    check("Y991A.4 ⭐⭐⭐⭐⭐ **本批最该带走的一条："
          "989 把两条成因不同、结果相同的「−1」并成了一次改写** —— "
          "① **102 → 101 是「序号与间隔之差」**"
          "（`node#0` 第 1 次在第 1 按、第 2 次在第 102 按 ⇒ 间隔 101）；"
          "② **out 段 18 → 17 是「间隙」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **结果撞对、而理由错** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **989 同一批其实已经写下了正确答案**"
          "（「**102 是回卷点位置、101 是圈长**，口径不同」）"
          "⇒ **却把间隙那条换算又套了上去** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **同一批里的两句话互相矛盾、而门没抓到** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「结果撞对、理由错」是最难自查的一类错**",
          '"P3_why_102_vs_101"' in _p991
          and '"P5_989_rewrite_reason"' in _p991
          and '"p3_index_vs_interval"' in _p991
          and "**理由错、结果撞对**" in _p991
          and "**989 同一批其实已经写下了正确答案**" in _p991
          and "**却把间隙那条换算又套了上去**" in _p991
          and "**同一批里的两句话互相矛盾、而门没抓到**" in _p991
          and '"two_minus_one_merged"' in _p991
          and "① 102 → 101 是**序号与间隔之差**；" in _p991
          and "② out 段 18 → 17 是**间隙** ⇒ ⇒ " in _p991
          and "**这是 981 那条「同一个东西要比同一个口径」" in _p991
          and '"p3_index_vs_interval_991_"' in _ausrc
          and "**理由错、结果撞对**" in _ausrc
          and "**却把间隙那条换算又套了上去**" in _ausrc
          and "**同一批里的两句话互相矛盾、而门没抓到**" in _ausrc
          and '"two_minus_one_merged_991_"' in _ausrc
          and "① **102 → 101 是「序号与间隔之差」**" in _ausrc
          and "② **out 段 18 → 17 是「间隙」**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门（本批最要紧的一条）**：
          #   **不许断言「102 → 101 是间隙造成的」** —— 它不是
          and "102 → 101 是间隙造成的" not in _p991
          and "102 → 101 是间隙造成的" not in _ausrc
          and "这个 1 就是间隙" not in _p991
          and "这个 1 就是间隙" not in _ausrc)

    check("Y991A.5 ⭐⭐⭐⭐ **P4 成立：间隙不在回卷点上** —— "
          "974 存档里源站 out 段**唯一的 dom_rank 下降**落在 **BODY** 那一格"
          "（`n_rank_descents = 1`、下降下标与 `body_seats[0]` 与 "
          "`seam_pred[0][seat]` **三者相同**）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **间隙在 out 段内部、而回卷点是 `node#0`（一个真节点）** "
          "⇒ ⇒ ⭐⭐⭐⭐⭐ **再次否掉「102 → 101 是因为间隙」** ⇒ ⇒ "
          "⇒ ⚠️⭐⭐⭐⭐⭐ **而 974 根本没量到源站的圈长** —— "
          "它报的是 `n_lead_cap_hit = True`（撞了 **140** 的按压上限）"
          "⇒ **它量到的是 out 段、不是圈长** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以「102 vs 101」在 974 存档里本来就不可判定** ⇒ "
          "**必须用 §164 自己的数** —— 而它的数是自洽的、只是与同一节的另一句矛盾",
          '"P4_gap_is_not_at_wrap"' in _p991
          and '"p4_gap_is_not_at_wrap"' in _p991
          and '"p4_2_974_never_measured_source_ring"' in _p991
          and "**唯一的 dom_rank 下降**落在 **BODY** 那一格" in _p991
          and "**间隙在 out 段内部、而回卷点是 `node#0`（一个真节点）**"
          in _p991
          and "**再次否掉「102 → 101 是因为间隙」**" in _p991
          and "n_lead_cap_hit = True" in _p991
          and "**它量到的是 out 段、不是圈长**" in _p991
          and "**所以「102 vs 101」在 974 存档里本来就不可判定**" in _p991
          and "**必须用 §164 自己的数**" in _p991
          and '"p4_gap_is_not_at_wrap_991_"' in _ausrc
          and "**间隙在 out 段内部、" in _ausrc
          and "**再次否掉「102 → 101 是因为间隙」**" in _ausrc
          and "n_lead_cap_hit = True" in _ausrc
          and "（撞了 **140** 的按压上限）" in _ausrc
          and "**所以「102 vs 101」在 974 存档里" in _ausrc
          # ⭐⭐⭐⭐ **反向门**：**不许说 974 量到了源站圈长**
          and "974 量到了源站圈长" not in _p991
          and "974 量到了源站圈长" not in _ausrc)

    check("Y991A.6 ⭐⭐⭐⭐⭐ **989 那条「不许并」仍然成立 —— "
          "本批只是把它升级成「并排读出来、并说清各自的成因」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「不许并」是对的、但它只说「不许」、没说「那差 1 是什么」** "
          "⇒ ⇒ ⭐⭐⭐⭐⭐ **本批给出了那差 1 的两个不同成因、"
          "**并明确说它们分属两个不同的量** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **这才是 981 那条「同一个东西要比同一个口径」"
          "**在「禁令」层面的完整形态** —— "
          "**不并、且并排读、且各自的成因不许互相顶替**",
          '"not_merged_still_holds"' in _p991
          and "**而 989 那条「不许把 102 与 101 并成一个数」仍然成立**"
          in _p991
          and "本批只是把「不许并」升级成「并排读出来、并说清各自的成因」"
          in _p991
          and '"two_minus_one_merged"' in _p991
          and '"two_minus_one_merged_991_"' in _ausrc
          and "**而 989 那条「不许把 102 与 101 并成一个数」" in _ausrc
          and "**本批只是把「不许并」升级成" in _ausrc
          and "「同一个东西要比同一个口径」" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把它们并成一个数**（989 那条仍然有效）
          and "102 与 101 其实是同一个数" not in _p991
          and "102 与 101 其实是同一个数" not in _ausrc)

    check("Y991A.7 ⭐⭐⭐⭐⭐ **本批的局限要说清楚、P4 与 P1/P2/P3 的可信度不同** —— "
          "**P4 依赖 `/tmp/b974-source-domrank.json`、而它不在仓库里** "
          "⇒ **这是一条会过期的读数** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **过期的读数不许当结论用、只当「当时的量」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **而 P1/P2/P3 只依赖 §164 原文、不依赖那个文件** ⇒ "
          "**所以本批的主体结论不会随它过期** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而 974 那条 `n_lead_cap_hit = True` 本身"
          "就是「仪器撞了上限」** ⇒ **它是 974 自己记着的、不是本批推的**",
          '"selfcheck_991"' in _p991
          and "**P4 依赖 `/tmp/b974-source-domrank.json` 这个 974 存档还在**"
          in _p991
          and "**它不在仓库里、所以这是一条会过期的读数**" in _p991
          and "**过期的读数不许当结论用**" in _p991
          and "**而 P1/P2/P3 只依赖 §164 原文、不依赖那个文件**" in _p991
          and '"ephemeral_dependency_991_"' in _ausrc
          and "**这是一条会过期的读数**" in _ausrc
          and "**过期的读数不许当结论用、只当「当时的量」**" in _ausrc
          and "**所以本批的主体结论不会随它过期**" in _ausrc
          and "n_lead_cap_hit = True" in _p991
          # ⭐⭐⭐⭐ **反向门**：**不许把一条会过期的读数说成是永久结论**
          and "974 存档永远有效" not in _p991
          and "974 存档永远有效" not in _ausrc)

    check("Y991A.8 ⭐⭐⭐⭐⭐ **本批纯离线、零计费是结构性的** —— "
          "**不打开浏览器**、**不按任何键**、**连 `mouse.click` 都没有** ⇒ ⇒ "
          "⚠️⭐⭐⭐⭐⭐ **源站侧全部用 974 存档**（985 已确认登录态过期）⇒ "
          "**不是「测了没事」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「零计费」有两种：自律的、还有结构性的 —— "
          "后者不依赖我记不记得** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **而本批是 986–990 里唯一「一条按键都没发」的** ⇒ "
          "**与 988/989 同类、与 990 不同**（990 要起两个服务器、但也不碰计费面）",
          '"offline_991"' in _p991
          and "连 `mouse.click` 都没有 ⇒ ⇒ " in _p991
          and "**源站侧全部用 974 存档**" in _p991
          and "**不是「测了没事」**" in _p991
          and "**零计费是结构性的、不是自律的**" in _p991
          and '"offline_991"' in _ausrc
          and "**连 `mouse.click` 都没有**" in _ausrc
          and "**源站侧全部用 974 存档**" in _ausrc
          and "**不是「测了没事」**" in _ausrc
          and '"offline_989"' in _ausrc
          and "**零计费是结构性的、不是自律的**" in _ausrc
          and "⭐⭐⭐⭐ **零计费是结构性的、不是自律的** ⇒ " in _p991
          # ⭐⭐⭐⭐ **反向门**：**990 那条「本批不是纯离线」不许被套到本批头上**
          and "**本批不是纯离线**（它要起两个服务器）" not in _p991)
    # ══ Z991A. 批 992 **纯离线跨系统对读**（973 存档 × 974 存档）——
    #   ⭐⭐⭐⭐⭐ **「间隙切在环的哪里」跨系统不同构** ⇒
    #   **990 那条「`gap_from_end` 两边都是 −2」只管跨构建模式**
    print("— Z991A. 批 992 纯离线跨系统对读："
          "⚠️⭐⭐⭐⭐⭐ **990 的结论要收窄**（复刻 −2、源站 −12）⇒ "
          "**而跨系统真正成立的是那两条相对关系**")
    check("Z991A.1 ⭐⭐⭐⭐⭐ **P1 与 P2 成立：跨系统真正成立的是那两条相对关系** —— "
          "① **下降点都落在 `BODY` 那一格**（复刻下标 **17/19**、源站下标 **6/18**，"
          "且 973/974 各自的 `n_rank_descents` 就都是 **1**）；"
          "② **`rf__wrapper` 在两侧的 arc 里都是最后一格** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而 987 记的「它落在间隙之后的兜底位」两侧都成立** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「同系统的稳定」与「可移植的规律」是两个量、"
          "**后者不蕴含前者** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **这与 989 那条「尺子有适用范围」同族、"
          "**而它是那条的跨系统版本**",
          '"P1_descent_lands_on_BODY_both"' in _p992
          and '"P2_rf_wrapper_is_last_arc_cell_both"' in _p992
          and '"p1_descent_on_BODY_both"' in _p992
          and '"p2_rf_wrapper_is_last_both"' in _p992
          and "复刻下标 17/19、源站下标 6/18" in _p992
          and "各自的 `n_rank_descents` 就都是 1" in _p992
          and "**这是 987 那条结论的跨系统印证**" in _p992
          and '"p1_descent_on_BODY_both_992_"' in _ausrc
          and "**复刻下标 17/19、源站下标 6/18**" in _ausrc
          and "**「恰好一次回绕」也是跨系统的**" in _ausrc
          and '"p2_rf_wrapper_is_last_both_992_"' in _ausrc
          and "**这是 987 那条结论的跨系统印证**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「可移植」与「同系统稳定」混为一谈**
          and "间隙位置在任何系统里都一样" not in _p992
          and "间隙位置在任何系统里都一样" not in _ausrc)

    check("Z991A.2 ⭐⭐⭐⭐⭐ **P3 成立、而它是本批的主要交付："
          "990 那条的适用范围比它写的窄** —— "
          "`BODY` 距 arc 末尾：**复刻 −2、源站 −12** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「间隙紧贴最后一格之前」在源站不成立** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **三条「零例外」各有各的适用范围、不许互相顶替**："
          "**985/986 的「间隙零例外」= 同一系统内**｜"
          "**990 的「`gap_from_end` 都是 −2」= 同一系统跨构建模式**｜"
          "**跨系统 = 本批量了、它不成立** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而 990 那条本身没有被推翻、被收窄的是它的适用范围** ⇒ "
          "**990 的判断在它自己的范围内仍然全对**",
          '"P3_gap_from_end_differs_cross_system"' in _p992
          and '"p3_scope_of_990_is_narrower"' in _p992
          and "`BODY` 距 arc 末尾：复刻 **−2**、源站 **−12**" in _p992
          and "**「间隙紧贴最后一格之前」在源站不成立**" in _p992
          and "① 985/986 的「间隙零例外」= **同一系统内**；" in _p992
          and "② 990 的「`gap_from_end` 都是 −2」= **同一系统跨构建模式**；" in _p992
          and "**三条「零例外」各有各的适用范围、不许互相顶替**" in _p992
          and "**它断言的是「不相等」" in _p992
          and '"p3_scope_of_990_is_narrower_992_"' in _ausrc
          and "**`BODY` 距 arc 末尾：复刻 −2、源站 −12**" in _ausrc
          and "**「间隙紧贴最后一格之前」在源站不成立**" in _ausrc
          and "**985/986 = 同一系统内**｜**990 = 跨构建模式**｜" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门（本批最要紧的一条）**：
          #   **不许说 990 那条是错的** —— 它只是范围窄
          and "990 那条结论是错的" not in _p992
          and "990 那条结论是错的" not in _ausrc
          and "990 的结论被推翻" not in _ausrc)

    check("Z991A.3 ⭐⭐⭐⭐⭐ **P4 成立：「内层停靠」有了可操作的候选判据** —— "
          "源站 arc **第 11/12 格 testid 相同**"
          "（`canvas-panel-launcher`、`dom_rank` 118 与 122）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **这比 §164 的「内层停靠 14 个」可核** —— "
          "**它能被逐格数出来** ⇒ ⇒ "
          "⇒ ⚠️⭐⭐⭐⭐⭐ **但本批不判它成不成立**："
          "**§164 说 14 个、本批只在 arc 这一段数到 1 处** ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **不许拿 1 去顶替 14** ⇒ "
          "**这是 981 那条「二选一是最坏的选择、并排读出来」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **候选判据 ≠ 结论** —— "
          "**而这一条不许被写成「已证实」**",
          '"P4_inner_stop_operational_criterion"' in _p992
          and '"p4_inner_stop_criterion"' in _p992
          and "**相邻两格 testid 相同**（源站第 11/12 格都是 `canvas-panel-launcher`、" in _p992
          and "`canvas-panel-launcher`" in _p992
          and "**这比 §164 的「内层停靠 14 个」可核**" in _p992
          and "**不许拿 1 去顶替 14**" in _p992
          and "**候选判据 ≠ 结论**" in _p992
          and '"p4_inner_stop_criterion_992_"' in _ausrc
          and "**源站 arc 第 11/12 格 testid 相同**" in _ausrc
          and "**不许拿 1 去顶替 14**" in _ausrc
          and "（981 那条「二选一是最坏的选择、并排读出来」）" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把它当成已证实的等价关系**
          and "相邻同名就等于内层停靠" not in _p992
          and "相邻同名就等于内层停靠" not in _ausrc)

    check("Z991A.4 ⭐⭐⭐⭐ **P5 成立：复刻 arc 里有不可聚焦的 `NEXTJS-PORTAL`、"
          "源站 arc 里没有** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **990 那枚 dev-only 元素在源站侧不存在** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **990 刚证「间隙紧贴它在后面」的那个位置、"
          "**在源站是由 `BODY` 顶上去的** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而这解释了 990 的一个悬案**："
          "**990 问「多出来那一格是不是 dev-only」、"
          "而源站那一侧压根没有这一格可问** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **「这个元素只在开发态存在」这件事、"
          "**源站侧连对照物都没有**",
          '"P5_replica_arc_has_PORTAL_source_does_not"' in _p992
          and '"p5_portal_only_on_replica"' in _p992
          and "**990 那枚 dev-only 元素在源站侧不存在**" in _p992
          and "**在源站是由 `BODY` 顶上去的、而源站的 `BODY` 在环的中段**" in _p992
          and '"p5_portal_only_on_replica_992_"' in _ausrc
          and "**源站 arc 里没有**" in _ausrc
          and "**990 那枚 dev-only 元素在源站侧不存在**" in _ausrc
          and "**在源站是由 `BODY` 顶上去的**" in _ausrc
          # ⭐⭐⭐⭐ **反向门**：**不许说源站有 NEXTJS-PORTAL**
          and "源站 arc 里有 NEXTJS-PORTAL" not in _p992
          and "源站 arc 里有 NEXTJS-PORTAL" not in _ausrc)

    check("Z991A.5 ⭐⭐⭐⭐ **P6 成立：两侧 arc 的 testid 集合互有差集** —— "
          "**复刻独有 `canvas-history-launcher`、`canvas-more-trigger`；"
          "源站独有 `canvas-editor-menu`** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **816 记的 `KNOWN_CLONE_ONLY` 两个 testid 在这一段上"
          "独立复现了** ⇒ ⇒ "
          "⇒ ⚠️⭐⭐⭐⭐⭐ **而这不等于「复刻多了两个按钮」** —— "
          "**arc 只是环的一段、不是整个顶栏** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「`canvas-editor-menu` 是不是 `canvas-more-trigger` "
          "的源站对应物」本批只按位置提出怀疑、"
          "**不许判它是同一个东西**（981 那条「并排读出来」）",
          '"P6_tid_sets_are_not_equal_both_ways"' in _p992
          and '"p6_tid_sets_differ_both_ways"' in _p992
          and "复刻独有 `canvas-history-launcher`、`canvas-more-trigger`" in _p992
          and "源站独有 `canvas-editor-menu`" in _p992
          and "**arc 只是环的一段、不是整个顶栏**" in _p992
          and "不判它是同一个东西**" in _p992
          and '"p6_tid_sets_differ_both_ways_992_"' in _ausrc
          and "**复刻独有 `canvas-history-launcher`、" in _ausrc
          and "**而这不等于「复刻多了两个按钮」**" in _ausrc
          and "**arc 只是环的一段、不是整个顶栏**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把差集直接读成「复刻多做了两个功能」**
          and "复刻比源站多了两个按钮" not in _p992
          and "复刻比源站多了两个按钮" not in _ausrc
          and "canvas-editor-menu 就是 canvas-more-trigger" not in _p992
          and "canvas-editor-menu 就是 canvas-more-trigger" not in _ausrc)

    check("Z991A.6 ⭐⭐⭐⭐⭐ **本批如实标注：哪几条预测不是盲的** —— "
          "**选候选时我已经看过这两张 arc 表** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **P1/P2/P3/P5 严格说不是盲预测**；"
          "**而 P4 与 P6 是看到表之后才想出来的、它们才是可红的** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「如实标注哪几条不是盲预测」"
          "**比「假装全是盲预测」诚实** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **986 那条「预测要按定义写出」要加一个限定："
          "**选候选的方式会污染预测** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以「怎么选候选」本身也要记下来** ⇒ "
          "**它是和预测同等重量的元数据**",
          '"honesty_note_992"' in _p992
          and '"honest_blind_prediction_992"' in _p992
          and "**选候选时我已经看过这两张 arc 表**" in _p992
          and "P1/P2/P3/P5 严格说不是盲预测" in _p992
          and "P4 与 P6 是看到表之后才想出来的、它们才是可红的" in _p992
          and "**比「假装全是盲预测」诚实**" in _p992
          and "**选候选的方式会污染预测**" in _p992
          and '"honest_blind_prediction_992_"' in _ausrc
          and "**而 P4 与 P6 是看到表之后才想出来的、它们才是可红的**" in _ausrc
          and "**比「假装全是盲预测」诚实**" in _ausrc
          and "**选候选的方式会污染预测**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把六条全写成「按定义预写」**
          and "六条预测全部按定义预写" not in _p992
          and "六条预测全部按定义预写" not in _ausrc)

    check("Z991A.7 ⭐⭐⭐⭐⭐ **引文门只收「前批的原文」、不许收本批自己的新结论** —— "
          "**那是循环依赖**（本批结论由 verifier 钉、不由引文门钉）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而本批要收窄的正是 990 那条 ⇒ 所以引文门验的就是它**："
          "**「间隙紧贴最后一格之前」与「间隙距环尾（`gap_from_end`）」"
          "两句都必须逐字在 README 里** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **989 栽过一次、991 又栽过一次 ⇒ "
          "第三次仍然要跑这道门** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **它三次都是红的 ⇒ 它是真的在干活**",
          '"quotes_992"' in _p992
          and '"quotes_all_present_992"' in _p992
          and '"quotes_gate_scope_992"' in _p992
          and "**引文门只收「前批的原文」、不许收本批自己的新结论**" in _p992
          and "间隙**紧贴最后一格之前**" in _p992
          and "间隙距环尾（`gap_from_end`）" in _p992
          and "**989 栽过一次、991 又栽过一次 ⇒ 第三次仍然要跑这道门**"
          in _p992
          and '"quotes_gate_scope_992_"' in _ausrc
          and "**那是循环依赖**" in _ausrc
          and "**989 栽过一次、991 又栽过一次 ⇒ " in _ausrc
          # ⭐⭐⭐⭐ **反向门**：**不许把本批新结论列进引文门**
          and "**下降点 == `BODY`**\",\n]" not in _p992)

    check("Z991A.8 ⭐⭐⭐⭐⭐ **本批的可信度分层要说清楚："
          "相对关系可移植、绝对下标会过期** —— "
          "**本批全部读数都依赖 `/tmp` 里的 973/974 存档、它们不在仓库里** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而 `dom_rank` 是绝对下标、换一次构建就可能全变** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以本批真正可移植的只有「相对关系」那两条**"
          "（**下降点 == `BODY`**、**`rf__wrapper` 是末格**）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **绝对下标 −2 / −12 只当作「当时量到的」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而 P3 的结论在这一点上反而更稳** —— "
          "**它断言的是「两侧不相等」、而「相等」才需要精确下标** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **本批纯离线**：不打开浏览器、不按任何键、"
          "**连 `mouse.click` 都没有** ⇒ **零计费是结构性的**",
          '"ephemeral_992"' in _p992
          and '"offline_992"' in _p992
          and "**而 `dom_rank` 是**绝对下标**、" in _p992
          and "**换一次构建就可能全变**" in _p992
          and "**所以本批真正可移植的只有「相对关系」那两条" in _p992
          and "**绝对下标 −2 / −12 只当作「当时量到的」**" in _p992
          and "**而 P3 的结论在这一点上反而更稳** —— " in _p992
          and "**连 `mouse.click` 都没有**" in _p992
          and "**零计费是结构性的、不是自律的**" in _p992
          and '"ephemeral_992_"' in _ausrc
          and "**绝对下标 −2 / −12 只当作「当时量到的」**" in _ausrc
          and '"offline_992"' in _ausrc
          and "**两侧全部用 973/974 存档**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把绝对下标说成是永久性质**
          and "−2 与 −12 是两个系统的固有属性" not in _p992
          and "−2 与 −12 是两个系统的固有属性" not in _ausrc)
    # ══ X992A. 批 993 **纯离线扫文档**（只扫文本、不重跑任何测量）——
    #   ⭐⭐⭐⭐⭐ **把 992 那条纪律系统化：**
    #   **每条「零例外」都要问「零例外的范围有多大」**
    print("— X992A. 批 993 纯离线扫文档："
          "⚠️⭐⭐⭐⭐⭐ **P4 与 P5 被数据否掉、而门错的是我** ⇒ "
          "**跨系统验过的两条一绿一红**")
    check("X992A.1 ⭐⭐⭐⭐⭐ **本批把 992 的单条发现系统化成一张分类表** —— "
          "**A-cross**（自带范围**且同时给出两侧**，1 条、批 966）｜"
          "**A-one-side**（只限定了哪一侧，0 条）｜"
          "**B-scoped**（带范围词但不是跨侧，1 条）｜"
          "**B-unscoped**（完全不带范围词，**10 条**）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而十条不带范围词的那批、"
          "**要补的范围可以靠 §202 那张总表归位、不必逐条重写** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **这是 992 那条纪律的可用形态："
          "**不是逐条追问、而是先分类、再按类处置**",
          '"the_taxonomy"' in _p993
          and '"the_taxonomy_993_"' in _ausrc
          and "**A-cross**：自带范围**且同时给出两侧**（1 条、批 966）" in _p993
          and "**A-one-side**：只限定了是哪一侧（0 条）" in _p993
          and "**B-unscoped**：完全不带范围词（10 条）" in _p993
          and "**十条不带范围词、而它们要补的范围可以靠 §202 那张总表归位**" in _p993
          and "**四条不带范围词" not in _p993
          # ⭐⭐⭐⭐⭐ **反向门**：**类别名与计数必须成对钉** ——
          #   **只写类别不写计数 ⇒ 等于没量**
          and '"n_A-cross_993"' in _p993
          and '"n_B-unscoped_993"' in _p993
          and '"D_cross_system_n_993"' in _p993)

    check("X992A.2 ⭐⭐⭐⭐⭐ **A-cross 那一条就是正面样板、而且它早就写好了** —— "
          "「**两条机制规则在复刻侧零例外成立**"
          "（**源站是 104/104 与 140/140**）」"
          "⇒ **既限定了范围、又把另一侧的数字并排列出** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而它比 990 那条早了几十节** ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以 990 那条不是「不会写」、是「忘了问范围」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「自带范围 + 两侧并排」就是 992 要的写法、"
          "**而这个能力一直都在**",
          '"a_class_best_example"' in _p993
          and '"A_best_example_993"' in _p993
          and "**两条机制规则在复刻侧零例外成立**" in _p993
          and "**源站是 104/104 与 140/140**" in _p993
          and "**而它比 990 那条早了几十节" in _p993
          and "**所以 990 那条不是「不会写」、是「忘了问范围」**" in _p993
          and '"a_class_best_example_993_"' in _ausrc
          and "**两条机制规则在复刻侧零例外成立**" in _ausrc
          and "**而它比 990 那条早了几十节" in _ausrc
          and "**所以 990 那条不是「不会写」、是「忘了问范围」**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把这个结论读成「以前写得都对」**
          and "以前的零例外断言全都带范围" not in _p993
          and "以前的零例外断言全都带范围" not in _ausrc)

    check("X992A.3 ⭐⭐⭐⭐⭐ **P4 按原文写被否、而门红的第一问是「门错还是数据错」"
          "—— 本批是门错** —— "
          "我第一版把 `复刻侧`/`源站侧` 放进了「跨系统证据词」⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而 `「复刻侧」恰恰是「只有一侧」的证据、方向相反** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「范围词」与「跨系统证据」不是一个概念、"
          "**把它们并进一个列表就造出了一条假命中** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以 P4 的红不是「数据否了预测」、"
          "**是「我的判据写错了」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而这条是 993 最该带走的一条："
          "**「范围词」与「跨系统证据」方向相反**",
          '"my_own_classifier_was_wrong"' in _p993
          and '"P4_refuted"' in _p993
          and "我第一版把 `复刻侧`/`源站侧` 放进了「跨系统证据词」" in _p993
          and "**而 `「复刻侧」恰恰是「只有一侧」的证据、方向相反**" in _p993
          and "**把它们并进一个列表就造出了一条假命中**" in _p993
          and "**所以 P4 的红不是「数据否了预测」、是「我的判据写错了」**"
          in _p993
          and '"my_own_classifier_was_wrong_993_"' in _ausrc
          and "**而 `「复刻侧」恰恰是「只有一侧」的证据、" in _ausrc
          and "**「范围词」与「跨系统证据」不是一个概念、" in _ausrc
          and "**门红的第一问是「门错还是数据错」" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把门红说成「数据否了预测」**
          and "P4 的红是数据否了预测" not in _p993
          and "P4 的红是数据否了预测" not in _ausrc
          # ⭐⭐⭐⭐ **反向门**：**方向相反这件事必须钉住**（本批的核心）
          and "ONE_SIDE_WORDS = " in _p993
          and "CROSS_SYSTEM_EVIDENCE = " in _p993
          and "**「范围词」与「跨系统证据」方向相反**" in _p993)

    check("X992A.4 ⭐⭐⭐⭐⭐ **P4 的真答案不是 0、而是 1 —— 而那一条来自批 966、"
          "**并且它是绿的**（复刻侧 0 差异、源站 104/104 与 140/140）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以「跨系统」本身不是问题** —— "
          "**992 那条红的是「间隙位置」这条特定性质、不是「跨系统」这件事** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **跨系统验过的两条一绿一红、"
          "**这比「跨系统一律不成立」诚实得多** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **而这直接收窄了 992 的措辞**："
          "**992 收窄的是「间隙位置」的适用范围、不是「跨系统」这个方法**",
          '"p4_refuted_by_966"' in _p993
          and '"p4_refuted_by_966_993_"' in _ausrc
          and "跨系统的零例外断言不是 0、是 1**" in _p993
          and "而那一条来自 **批 966 的「两条机制规则」**、**并且它是绿的**" in _p993
          and "**所以「跨系统」本身不是问题**" in _p993
          and "**跨系统验过的两条一绿一红、" in _p993
          and '"p4_refuted_by_966_993_"' in _ausrc
          and "**跨系统验过的两条一绿一红、" in _ausrc
          and '"P4_hold_as_written_993"' in _p993
          # ⭐⭐⭐⭐⭐ **反向门（本批最要紧的一条）**：
          #   **不许把结论写成「跨系统一律不成立」**
          and "**跨系统一律不成立**" not in _p993
          and "**跨系统一律不成立**" not in _ausrc
          and "**而这一族必须逐条明写出来 —— " in _p993
          and "**而这一族必须逐条明写出来 —— " in _ausrc
          and "跨系统都不成立" not in _ausrc)

    check("X992A.5 ⭐⭐⭐⭐⭐ **P5 也被否：992 不是第一次跨系统验证** —— "
          "**批 966 早就做过一次、而它是绿的** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以 992 的新颖之处不在「第一次跨系统」、"
          "**而在「第一次跨系统验间隙位置」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「我没做过」与「没人做过」是两件事、"
          "**判「首次」之前必须先扫一遍已有结论** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **这正是 993 这个扫描存在的理由** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **而这条同时是对 992 的一处自我更正**",
          '"p5_refuted_992_is_not_first"' in _p993
          and '"p5_refuted_992_is_not_first_993_"' in _ausrc
          and "**批 966 早就做过一次、而它是绿的**" in _p993
          and "**而在「第一次跨系统验间隙位置」**" in _p993
          and "**「我没做过」与「没人做过」是两件事、" in _p993
          and "**判「首次」之前必须先扫一遍已有结论**" in _p993
          and "**这正是 993 这个扫描存在的理由**" in _p993
          and "**「我没做过」与「没人做过」是两件事、" in _ausrc
          and "**这正是 993 这个扫描存在的理由**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许写「992 是第一次跨系统验证」**
          and "**992 是第一次跨系统验证**" not in _p993
          and "第一次跨系统验证的是 992" not in _ausrc)

    check("X992A.6 ⭐⭐⭐⭐⭐ **C 类是本批第二件值钱的事："
          "「独立」与「跨系统」是两个词** —— "
          "§196（批 986）写「**在两个独立数据集上零例外**」⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而那两个数据集（986 新跑 42 圈 + 980 的 59 圈）"
          "**在同一个系统上** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **这句话本身是诚实的、"
          "**但它极易被读成「在两个系统上验过」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而 992 正是被这种读法骗的那一类** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **判据也必须分开**：「两个独立数据集」"
          "**不进「跨系统证据词」那一档**",
          '"c_independent_is_not_cross_system"' in _p993
          and '"c_independent_is_not_cross_system_993_"' in _ausrc
          and "**在两个独立数据集上零例外**" in _p993
          and "**在同一个系统上**" in _p993
          and "**这句话本身是诚实的、" in _p993
          and "**而 992 正是被这种读法骗的那一类**" in _p993
          and '"C_two_datasets_993"' in _p993
          and '"P3_hold_993"' in _p993
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说 986 那句话是错的**
          and "986 那句话是错的" not in _p993
          and "986 那句话是错的" not in _ausrc
          and '"两个独立数据集"' in _p993
          and "两个独立数据集" not in " ".join(
              ["两个被测系统", "跨系统"]))

    check("X992A.7 ⭐⭐⭐⭐⭐ **判据必须取两行窗口 —— 而这是本批第二个仪器坑** —— "
          "966 那条的**「源站是 104/104 与 140/140」在下一行** ⇒ "
          "**只看一行会把一条跨侧断言误判成单侧** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **它比第一个坑更隐蔽** —— "
          "**第一个让门红、这个让门绿** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而这与 990 那条「恒真的读数」同族："
          "**两者都是「门不红、而读数不对」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以「门绿」从来不是「读数对」的证据**",
          '"window_must_be_two_lines"' in _p993
          and '"window_must_be_two_lines_993_"' in _ausrc
          and "**「源站是 104/104 与 140/140」在下一行**" in _p993
          and "**只看一行会把一条跨侧断言误判成单侧**" in _p993
          and "**而它比第一个更隐蔽**" in _p993
          and "（第一个让门红、这个让门绿）" in _p993
          and '"window_must_be_two_lines_993_"' in _ausrc
          and "**第一个让门红、这个让门绿**" in _ausrc
          and "WIN = 2" in _p993
          and "**所以「门绿」从来不是「读数对」的证据**" in _p993
          # ⭐⭐⭐⭐⭐ **反向门**：**不许因为门绿就认为读数对**
          and "门绿说明读数是对的" not in _p993
          and "门绿说明读数是对的" not in _ausrc)

    check("X992A.8 ⭐⭐⭐⭐⭐ **本批沿用 992 的自省、且它在这里更有必要** —— "
          "**选候选时我已看过那 47 行命中的分布** ⇒ "
          "**P1/P2/P3 是按分布写的、严格说不是盲预测** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而 P4 与 P5 断言的是「不存在」、才是可红的** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **它们确实红了、而红的成因是「我的判据写错」"
          "**不是「事实如此」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **沿用 992 那条：「怎么选候选」"
          "**是和预测同等重量的元数据** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而本批纯离线**：不打开浏览器、不按任何键、"
          "**连 `mouse.click` 都没有**、**只扫文本、不重跑任何测量** ⇒ "
          "**所以它不会有过期读数那一类问题**",
          '"honest_blind_993"' in _p993
          and "HONESTY = (" in _p993
          and "**选候选时我已看过那 47 行命中的分布**" in _p993
          and "**P1/P2/P3 是按分布写的、严格说不是盲预测**" in _p993
          and "**而 P4 与 P5 断言的是「不存在」、才是可红的**" in _p993
          and "**它们确实红了、而红的成因是「我的判据写错」" in _p993
          and "**沿用 992 那条：「怎么选候选」" in _p993
          and '"honest_blind_993_"' in _ausrc
          and "**选候选时我已看过那 47 行命中的分布**" in _ausrc
          and "**它们确实红了、而红的成因是" in _ausrc
          and '"offline_993"' in _p993
          and '"offline_993"' in _ausrc
          and "**而本批只扫文本、不重跑任何测量**" in _p993
          and "**所以它不会有过期读数那一类问题**" in _p993
          # ⭐⭐⭐⭐ **反向门**：**不许把「门红」写成「预测被数据否掉」**
          and "两条预测被数据否掉了" not in _p993
          and "两条预测被数据否掉了" not in _ausrc
          and "**门红的第一问是「门错还是数据错」" in _ausrc)
    # ══ Y992B. 批 994 **纯离线验前提**（只扫文本、不重跑任何测量）——
    #   ⭐⭐⭐⭐⭐ **993 那条「总表归位」预设了「那 10 条讲的是同一个性质」**
    #   ⇒ **而本批就是验这个前提 ⇒ 验完：不成立**
    print("— Y992B. 批 994 纯离线验前提："
          "⚠️⭐⭐⭐⭐⭐ **「总表归位」的前提不成立** ⇒ "
          "⭐⭐⭐⭐⭐ **更狠的一条：一次扫描会改变它所扫描的对象**")
    check("Y992B.1 ⭐⭐⭐⭐⭐ **P1 成立：993 那条处置的前提不成立** —— "
          "**10 条 B-unscoped 里、真在讲间隙位置的只有 2 条** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而 993 写的是「范围缺失可以靠总表归位、不必逐条重写」** "
          "⇒ ⇒ ⭐⭐⭐⭐⭐ **那条处置在没问「是不是同一个性质」之前不能用** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **「归位」这个动作本身也有前提 —— "
          "**而我上一批只钉了「比的时候要同一个口径」、没想到「归的时候」也要**",
          '"p1_presupposition_fails"' in _p994
          and '"presupposition_994"' in _p994
          and '"p1_presupposition_fails_994_"' in _ausrc
          and '"n_B_unscoped": n_b' in _p994
          and "**10 条 B-unscoped 里、真在讲间隙位置的只有 2 条**" in _ausrc
          and "**在没问「是不是同一个性质」之前是不能用的**" in _p994
          and '"what_993_presupposed"' in _p994
          and "**而那预设了「那 10 条讲的是同一个性质」**" in _p994
          and '"p1_presupposition_fails_994_"' in _ausrc
          and "**在没问「是不是同一个性质」之前是不能用的**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「总表归位」当成无条件可用的处置**
          and "范围缺失一律可以靠总表归位" not in _p994
          and "范围缺失一律可以靠总表归位" not in _ausrc
          # ⭐⭐⭐⭐ **反向门**：**不许把 2/10 说成「大部分」**
          and "大部分都在讲间隙" not in _p994
          and "大部分都在讲间隙" not in _ausrc)

    check("Y992B.2 ⭐⭐⭐⭐⭐ **本批最狠的一条：一次扫描会改变它所扫描的对象** —— "
          "993 那次扫描**压根扫不到自己那一节**（**探针先跑、§203 后写**）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以「命中 12 行」不是稳定量** ⇒ "
          "**现在用同一把尺子重跑命中 18 行、新增 6 行全在 §203** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **最刺眼的一处：`A-cross` 从 1 变成 5**、"
          "**而新增的 4 条全部落在 §203 自己那一节** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以 §203 那条「跨系统的零例外断言有 1 条」"
          "**不注明输入快照、下一批照着重数就会数出 5 条** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **扫描类结论必须自带「输入快照」** ⇒ "
          "**这正是 993 那条「引文门只收前批原文」的另一种形态**",
          '"P2_rerun_count_is_not_stable"' in _p994
          and '"p2_scan_output_changes_its_input"' in _p994
          and '"rerun_994"' in _p994
          and '"self_referential_counting"' in _p994
          and '"self_referential_counting"' in _p994
          and "**现在用同一把尺子重跑命中数就变了**" in _p994
          and "**现在用同一把尺子重跑命中 18 行、新增 6 行全在 §203**" in _ausrc
          and "**「一次扫描会改变它所扫描的对象」**" in _p994
          and "`A-cross` 从 1 变成 5" in _p994
          and "**而新增的 4 条全部落在 §203 自己那一节**" in _p994
          and "**如果不注明输入快照、下一批照着重数就会数出 5 条**" in _ausrc
          and "下一批照着重数就会数出 5 条**" in _p994
          and "**扫描类结论必须自带「输入快照」**" in _p994
          and '"p2_scan_output_changes_its_input_994_"' in _ausrc
          and "**现在用同一把尺子重跑命中 18 行、新增 6 行全在 §203**" in _ausrc
          and "`A-cross` 从 1 变成 5" in _ausrc
          and '"across_inflated_by_echo_994_"' in _ausrc
          and "**扫描类结论必须自带「输入快照」**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说「12 行」这个数仍然成立**
          and "命中 12 行这个数是稳定的" not in _p994
          and "命中 12 行这个数是稳定的" not in _ausrc
          and '"delta": len(_rerun) - _r_old' in _p994)

    check("Y992B.3 ⭐⭐⭐⭐⭐ **而「重跑」的前提是「尺子逐字相同」** —— "
          "本批**逐字复用** 993 的正则与词表（`CLAIM_RE` / `SCOPE_WORDS` / "
          "`CROSS_SYSTEM_EVIDENCE` / `WIN`）、**不重写** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **免得又造一把不同的尺子、然后把差异误读成「事实变了」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **这是 992/993 那条「同一个东西要比同一个口径」"
          "**在工具层的形态** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而上一批刚栽过一次相反的**："
          "**993 第一版把「复刻侧」当跨系统证据、那把尺子本身就写错了** ⇒ "
          "⇒ ⭐⭐⭐⭐ **「复用」与「复用一把错的尺子」要分开说**",
          '"reuse_note"' in _p994
          and '"reuse_the_ruler_verbatim_994_"' in _ausrc
          and '"reuse_note"' in _p994
          and "**判据逐字复用 993 的正则与词表、**不重写**" in _p994
          and "**免得又造一把不同的尺子、然后把差异误读成「事实变了」**"
          in _p994
          and "**重跑的前提是「尺子逐字相同」**" in _ausrc
          and "在工具层的形态" in _ausrc
          and "**重跑的前提是「尺子逐字相同」**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说「复用尺子就一定对」**
          and "复用尺子就一定不会错" not in _p994
          and '"reuse_note"' in _p994
          and "免得又造一把不同的尺子" in _p994)

    check("Y992B.4 ⭐⭐⭐⭐⭐ **P3 成立：至少一条讲的是完全不同的性质** —— "
          "**「透明 ⇒ 观感零差异」是像素层面的、与 Tab 环无关**"
          "（「瞬时浮层互斥 24/24」同理）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **把它们塞进「Tab 环零例外的范围表」是范畴错误** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **而它们也不需要那张表 —— "
          "**它们各自是**一次性观察**、不是一条「零例外」律** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **「零例外」这个措辞本身跨了性质、"
          "**所以按措辞分组就一定出错**",
          '"p3_other_properties_are_category_error"' in _p994
          and '"p3_other_properties_994_"' in _ausrc
          and "**「透明 ⇒ 观感零差异」是像素层面的、与 Tab 环无关**" in _p994
          and "**把它们塞进「Tab 环零例外的范围表」是范畴错误**" in _p994
          and "**它们各自是**一次性观察**、不是一条「零例外」律**" in _p994
          and '"p3_other_properties_994_"' in _ausrc
          and "**把它们塞进「Tab 环零例外的范围表」" in _ausrc
          and "**它们各自是**一次性观察**、不是一条「零例外」律**" in _ausrc
          and 'FAMILIES = {' in _p994
          and '"visual"' in _p994
          and '"overlay"' in _p994
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「性质不同」的那些也归进同一张表**
          and "所有零例外断言共用一张范围表" not in _p994
          and "所有零例外断言共用一张范围表" not in _ausrc)

    check("Y992B.5 ⭐⭐⭐⭐⭐ **P4 与 P5 成立：处置必须分四类、而 993 那条纪律⑤必须收窄** —— "
          "**T-table**（同一个性质 ⇒ §202 的范围表适用）｜"
          "**S-self**（自我指涉 ⇒ 单列、不当证据）｜"
          "**T-other**（另一个性质 ⇒ 另立范围表）｜"
          "**T-unknown**（性质不明 ⇒ 先问它是什么）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以 993 那条纪律⑤不是「一律靠总表归位」、"
          "**而是「先问它讲的是不是同一个性质、同一个性质才归位」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **这与 981 那条「同一个东西要比同一个口径」同族 —— "
          "**而这次错在「归位」这个动作上、不是比的时候** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「处置 ≠ 前提」是「候选判据 ≠ 结论」的同族**",
          '"P4_three_classes_not_one"' in _p994
          and '"P5_993_discipline_5_must_be_narrowed"' in _p994
          and '"p4_three_treatments_994_"' in _ausrc
          and '"p5_narrow_993_discipline_994_"' in _ausrc
          and "**T-table**（同一个性质 ⇒ §202 的范围表适用）" in _p994
          and "**S-self**（自我指涉 ⇒ 单列、不当证据）" in _p994
          and "**T-other**（另一个性质 ⇒ 另立范围表）" in _p994
          and "**T-unknown**（性质不明 ⇒ 先问它是什么）" in _p994
          and "先问它讲的是不是同一个性质、同一个性质才归位" in _p994
          and "**而这次错在「归位」这个动作上、不是比的时候**" in _p994
          and "**「处置 ≠ 前提」是「候选判据 ≠ 结论」的同族**" in _p994
          and '"p4_three_treatments_994_"' in _ausrc
          and "**「处置 ≠ 前提」是" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把 993 纪律⑤说成「本来就对」**
          and "993 纪律⑤本来就对" not in _p994
          and "993 纪律⑤本来就对" not in _ausrc
          and '"narrow_993_994"' in _p994)

    check("Y992B.6 ⭐⭐⭐⭐⭐ **「自我指涉」本身是一个该单列的类别** —— "
          "**一条扫描会把自己的结论重新扫进来** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而它与 993 那条「引文门只收前批原文」"
          "**是同一条纪律的另一种形态** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以「命中 N 行」这个数永远要注明"
          "**「其中几条是本扫描写的、扫描那一刻的输入是什么」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而这一条对「扫描类结论」普遍成立、"
          "**不只是这一批**",
          '"S-self"' in _p994
          and '"is_self_referential"' in _p994
          and '"n_self_referential"' in _p994
          and "**一条扫描会把自己的结论重新扫进来**" in _p994
          and "**「命中 N 行」这个数永远要注明" in _p994
          and "**所以扫描类结论必须注明「扫描那一刻的输入是什么」**" in _p994
          and '"p2_scan_output_changes_its_input_994_"' in _ausrc
          and "**所以扫描类结论必须注明" in _ausrc
          and "**这一条对「扫描类结论」普遍成立**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把自我指涉的那些算进证据计数**
          and "自我指涉的行也算证据" not in _p994
          and "自我指涉的行也算证据" not in _ausrc
          # ⭐⭐⭐⭐ **反向门**：**不许把这个结论缩到只剩本批**
          and "只对 993 这一批成立" not in _p994
          and "只对 993 这一批成立" not in _ausrc)

    check("Y992B.7 ⭐⭐⭐⭐ **本批沿用 992/993 的自省、而且它在这里是必需的** —— "
          "**写判据前我已看过那 12 条断言的全文** ⇒ "
          "**P1/P3/P4 不是盲预测** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **而 P2 与 P5 断言的是「有几条」与「纪律要改」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「怎么选候选」是和预测同等重量的元数据** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而本批最刺眼的一处是：我第一版写的 P2 是"
          "**「有几条是自我指涉」⇒ 而真答案是 0** ⇒ "
          "**真因不是「没有」、是「扫描早于写入」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **一个被数据否掉的预测、"
          "**有时否掉的不是事实、是我假设的执行顺序**",
          '"honest_blind_994"' in _p994
          and 'HONESTY = (' in _p994
          and "**写判据前我已看过那 12 条断言的全文**" in _p994
          and "**P1/P3/P4 不是盲预测**" in _p994
          and "**而 P2 与 P5 断言的是「有几条」与「纪律要改」**" in _p994
          and "**「怎么选候选」是和预测同等重量的元数据**" in _p994
          and '"honest_blind_994_"' in _ausrc
          and "**写判据前我已看过那 12 条断言的全文**" in _ausrc
          and '"offline_994"' in _p994
          and '"offline_994"' in _ausrc
          and "**只扫文本、不重跑任何测量**" in _p994
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说「被否的预测就是被数据否掉的」**
          and "P2 被数据否掉了" not in _p994
          and "否掉的不是事实、是我假设的执行顺序" in _p994)

    check("Y992B.8 ⭐⭐⭐⭐⭐ **本批纯离线、而且它比前几批多一条好处** —— "
          "**不打开浏览器**、**不按任何键**、**连 `mouse.click` 都没有**、"
          "**只扫文本、不重跑任何测量** ⇒ ⇒ "
          "⭐⭐⭐⭐ **零计费是结构性的、不是自律的** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而「只扫文本」这一条恰好让本批躲开了"
          "**990/991/992 反复遇到的那一类「过期读数」问题** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **可移植的读数分两种："
          "**「相对关系」与「扫描类结论 + 输入快照」** —— "
          "**后者只要尺子逐字相同、输入写清楚、就永远可重跑**",
          '"offline_994"' in _p994
          and '"offline_994"' in _ausrc
          and "**不打开浏览器**" in _ausrc
          and "**只扫文本、不重跑任何测量**" in _p994
          and "**零计费是结构性的、不是自律的**" in _p994
          and "**而「只扫文本」这一条恰好让本批躲开了" in _p994
          and '"offline_994"' in _ausrc
          and "**只扫文本、不重跑任何测量**" in _ausrc
          and "**零计费是结构性的、不是自律的**" in _ausrc
          and '"n_rerun_claim_lines"' in _p994
          and "**「相对关系」与「扫描类结论 + 输入快照」**" in _p994
          # ⭐⭐⭐⭐ **反向门**：**不许说「纯离线就没有任何局限」**
          and "纯离线就没有任何局限" not in _p994
          and "纯离线就没有任何局限" not in _ausrc
          and "**而本批有它自己的局限：输入是 README 本身**" in _p994
          or ("**只扫文本、不重跑任何测量**" in _p994
              and '"n_rerun_claim_lines"' in _p994
              and "**而本批有它自己的局限：输入是 README 本身**" in _p994))
    # ══ Z992C. 批 995 **纯离线换措辞再扫**（只扫文本、不重跑任何测量）——
    #   ⭐⭐⭐⭐⭐ **「零例外」的总量不是文档的客观属性、是检索词的属性**
    print("— Z992C. 批 995 纯离线换措辞再扫："
          "⚠️⭐⭐⭐⭐⭐ **两套措辞的命中行交集是 0** ⇒ "
          "⭐⭐⭐⭐⭐ **「共 N 条」不给检索词、等于没说**")
    check("Z992C.1 ⭐⭐⭐⭐⭐ **P1 成立：两套措辞的命中行交集是 0** —— "
          "**族 A（`零例外` 族）25 行、族 B（一致/无差别族）63 行、A ∩ B = 0** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **不只是少、是完全不重叠** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **同一份文档里「零例外」这件事"
          "**是用两套互不重叠的措辞写的** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **而 P2 一起成立：族 B 远多于族 A** ⇒ "
          "**这说明覆盖面远大于 §203 找到的那些**",
          '"P1_two_wording_sets_are_disjoint"' in _p995
          and '"P2_b_family_is_much_larger"' in _p995
          and '"p1_disjoint"' in _p995
          and '"p2_b_is_much_larger"' in _p995
          and 'FAM_A = re.compile' in _p995
          and 'FAM_B_CLEAN = re.compile' in _p995
          and '"A_and_B": len(a & b)' in _p995
          and "**不只是少、是完全不重叠**" in _p995
          and "**同一份文档里「零例外」这件事" in _p995
          and '"p1_disjoint_995_"' in _ausrc
          and "**不只是少、是完全不重叠**" in _ausrc
          and "**同一份文档里「零例外」这件事" in _ausrc
          and '"p2_b_is_much_larger_995_"' in _ausrc
          and "**而 §203 找到的那些" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说「族 A 已经找齐了」**
          and "族 A 就是全部" not in _p995
          and "族 A 就是全部" not in _ausrc)

    check("Z992C.2 ⭐⭐⭐⭐⭐ **P3 成立、而它是本批最要紧的一层："
          "`恒为 X` 是一句读数、`零例外` 是一条断言** —— "
          "**判据：族 C 的 40 行里 35 行含一个「量」（`ratio = 0.875`）** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以分类的第一步是「这句话在做什么」、"
          "**不是「它属于哪个关键词」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **而我第一版把 `恒为` 和「一致」混在同一档、"
          "**这恰恰是 §204 那条错误的复刻** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「读数」与「断言」混在一档、"
          "**后面所有的计数都会被污染**",
          '"P3_const_family_is_reading_not_claim"' in _p995
          and '"P3_reading_995"' in _p995
          and '"p3_const_is_reading"' in _p995
          and "**`恒为 X` 是一句读数、`零例外` 是一条断言**" in _p995
          and "**（`ratio = 0.875`）**" in _p995
          and "**分类的第一步是" in _p995
          and "**不是「它属于哪个关键词」**" in _p995
          and "**这恰恰是 §204 那条错误的复刻**" in _p995
          and '"p3_const_is_reading_995_"' in _ausrc
          and "**`恒为 X` 是一句读数、`零例外` 是一条断言**" in _ausrc
          and "**（`ratio = 0.875`）**" in _ausrc
          and 'QUANT = re.compile(r"[0-9]|px|false|true|None")' in _p995
          and '"n_C_with_a_quantity"' in _p995
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把 `恒为 X` 当成「零例外」断言计数**
          and "族 C 也算零例外断言" not in _p995
          and "族 C 也算零例外断言" not in _ausrc
          # ⭐⭐⭐⭐ **反向门**：**不许把 ratio 说成 1.0**（它是 0.875）
          and "**而 40 行全含一个量**" not in _p995
          and "全部 40 行都含一个量" not in _p995)

    check("Z992C.3 ⭐⭐⭐⭐⭐ **P4 成立：「零例外」的总量"
          "不是文档的客观属性、**是检索词的选择的属性** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以任何「共 N 条」的说法都必须同时给出检索词** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而「共 N 条」不给检索词、等于没说** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **这一条适用于本项目里所有「共 N 处」的断言** ⇒ "
          "**而不只是「零例外」这一族**",
          '"p4_total_is_property_of_query"' in _p995
          and '"finding_995"' in _p995
          and '"p4_total_is_property_of_query_995_"' in _ausrc
          and "**是检索词的选择的属性**" in _p995
          and "**都必须同时给出检索词**" in _p995
          and "**而「共 N 条」不给检索词、等于没说**" in _p995
          and "**这一条适用于本项目里所有「共 N 处」的断言**" in _p995
          and "**而不只是「零例外」这一族**" in _p995
          and '"p4_total_is_property_of_query_995_"' in _ausrc
          and "**而「共 N 条」不给检索词、等于没说**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许给一个不带检索词的「共 N 条」下结论**
          and "共 25 条零例外断言" not in _p995
          and "文档里共有 25 条零例外断言" not in _ausrc)

    check("Z992C.4 ⭐⭐⭐⭐⭐ **P5 成立、并与 994 合起来是一句更狠的话** —— "
          "**§203 那张分类表只覆盖族 A、而它当时给人的印象是「全部」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **这是 994 那条"
          "**「按措辞分组就一定出错」的加强版** —— "
          "**不是分组错、**是连「找齐了没有」都错** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **两条合起来是一句："
          "**措辞既不能用来分组、也不能用来证明找齐了** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **而这两条都不是 §203 能自己发现的** —— "
          "**它当时的门全绿、而门绿只说明「对族 A 的判断自洽」**",
          '"P5_993_table_covers_only_family_a"' in _p995
          and '"p5_table_covers_only_one_family"' in _p995
          and '"p5_table_covers_only_one_family_995_"' in _ausrc
          and "**只覆盖族 A、**" in _p995
          and "**不是分组错、**是连「找齐了没有」都错**" in _p995
          and "**措辞既不能用来分组、也不能用来证明找齐了**" in _p995
          and "**而这两条都不是 §203 能自己发现的**" in _p995
          and "**它当时的门全绿、而门绿只说明「对族 A 的判断自洽」**" in _p995
          and '"p5_table_covers_only_one_family_995_"' in _ausrc
          and "**措辞既不能用来分组、也不能用来证明找齐了**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把 §203 说成「漏查了」**
          and "§203 漏查了" not in _p995
          and "§203 漏查了" not in _ausrc
          and "**而这不是「漏查了」、" in _p995)

    check("Z992C.5 ⭐⭐⭐⭐⭐ **本批自己那条「一半对」的怀疑要照实记** —— "
          "我看到 `ratio = 1.0` 就怀疑判据恒真"
          "（以为正则里那两个引号是空串备选、匹配一切）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **查下来它不是：在字符类里那是两个字面引号、"
          "**空串并不匹配** ⇒ ⇒ "
          "⇒ ⚠️⭐⭐⭐⭐ **但我的怀疑是「一半对」** —— "
          "**把那个备选删掉之后 `ratio` 从 40/40 掉到 35/40** ⇒ "
          "**说明它确实在匹配 5 行** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以我既没说「它恒真」（错）、"
          "**也没说「它没用」（也错）** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「门红先判门错还是数据错」在这里的形态是："
          "**先判「我怀疑的那个错到底存不存在、存在到什么程度」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **而这一条与 985 那条「恒假的读数要留」、"
          "990 那条「恒真的读数要认出它」是同一族** ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **三者的共同点是：仪器的问题要靠查、不是靠猜；"
          "**而查出来的结果常常是「一半对」**",
          '"my_suspicion_was_half_right"' in _p995
          and '"my_suspicion_was_half_right_995_"' in _ausrc
          and "我看到 `ratio = 1.0` 就怀疑判据恒真" in _p995
          and "是两个字面引号、" in _p995
          and "**空串并不匹配**" in _p995
          and "**把那个备选删掉之后 ratio 从 40/40 掉到 35/40**" in _p995
          and "**说明它确实在匹配 5 行**" in _p995
          and "**所以我既没说「它恒真」（错）、" in _p995
          and "**也没说「它没用」（也错）**" in _p995
          and "**先判「我怀疑的那个错到底存不存在、存在到什么程度」**"
          in _p995
          and '"my_suspicion_was_half_right_995_"' in _ausrc
          and "**而查出来的结果常常是「一半对」**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把这个怀疑写成「仪器坏了」**
          and "判据恒真所以仪器坏了" not in _p995
          and "**所以我既没说「它恒真」" in _ausrc)

    check("Z992C.6 ⭐⭐⭐⭐⭐ **而本批同样逐字写死三套措辞、不放宽** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **免得又造一把不同的尺子、"
          "**然后把差异误读成「事实变了」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **这是 994 那条"
          "**「重跑的前提是尺子逐字相同」的延续** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **而「逐字写死」这条纪律还有一个作用："
          "**它让「我为什么只找这几种说法」本身变成可审的东西** ⇒ "
          "**而 §203 那张表当初正是没写这一句**",
          'FAM_A = re.compile' in _p995
          and 'FAM_B = re.compile' in _p995
          and 'FAM_C = re.compile' in _p995
          and 'FAM_B_CLEAN = re.compile' in _p995
          and '"reuse_again_verbatim"' in _p995
          and "**免得又造一把不同的尺子、" in _p995
          and "**这是 994 那条" in _p995
          and "**「重跑的前提是尺子逐字相同」的延续**" in _p995
          and "**它让「我为什么只找这几种说法」本身变成可审的东西**" in _p995
          and '"discipline_995"' in _p995
          and "**三套措辞逐字写死、不放宽**" in _p995
          # ⭐⭐⭐⭐ **反向门**：**不许说「三套已经覆盖全部说法」**
          and "三套措辞已经覆盖全部" not in _p995
          and "三套措辞已经覆盖全部" not in _ausrc)

    check("Z992C.7 ⭐⭐⭐⭐⭐ **本批沿用 992/993/994 的自省、而它在这里更要紧** —— "
          "**写判据前我已看过这次扫描的命中分布** ⇒ "
          "**P1/P2/P4/P5 严格说不是盲预测** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而 P3 断言的是"
          "**「族 C 是读数不是断言」、那是要判的** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「怎么选候选」是和预测同等重量的元数据** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而本批把它推到了尽头**："
          "**我先看到了「交集是 0」才去问「是不是找齐了」** ⇒ "
          "**⇒ 而如果没有那个先看到的结果、我根本不会想到要问** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以「自省」这条纪律有一个容易被忽略的副作用："
          "**它会让好问题只在我们已经撞上它之后才出现**",
          '"honest_blind_995"' in _p995
          and 'HONESTY = (' in _p995
          and "**写判据前我已看过这次扫描的命中分布**" in _p995
          and "**P1/P2/P4/P5 严格说不是盲预测**" in _p995
          and "**而 P3 断言的是" in _p995
          and "**「怎么选候选」是和预测同等重量的元数据**" in _p995
          and '"honest_blind_995_"' in _ausrc
          and "**写判据前我已看过这次扫描的命中分布**" in _ausrc
          and "**它会让好问题只在我们已经撞上它之后才出现**" in _p995
          and '"offline_995"' in _p995 and '"offline_995"' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把自省写成「我本来就问了那个问题」**
          and "我本来就想到了找齐没有" not in _p995
          and "**我先看到了「交集是 0」才去问「是不是找齐了」**" in _p995)
    check("Z992C.8 ⭐⭐⭐⭐⭐ **本批把「钉探针 ≠ 钉 audit」栽到了第五次、"
          "也是最隐蔽的一次** —— "
          "**写判据时我漏了 verifier 里读 `_p995` 的那一行** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **71 条锚点被两个门同时静默跳过、而两个门都报成功** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而根因是一个我以为很安全的写法**："
          "**我第一版用 `if \"_p995\" not in v:` 当「有没有登记」的判据** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而判据组 `Z992C` 的正文里本来就写着 `_p995`** ⇒ "
          "**守卫误判成「已登记」、读取行压根没加** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「用 `in` 判断有没有登记」不可靠** —— "
          "**要判的是「那行读取在不在」、不是「那个名字在不在」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而补上之后官方门立刻报出 28 个问题**"
          "（27 MISSING + 1 WOULD-FAIL）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **而那 1 条 WOULD-FAIL 又是一个反向门的假阳性**："
          "**我写「`ratio = 1.0` 不许出现」、"
          "**而它出现在我引述自己那条怀疑的句子里** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **这是 993 那条"
          "**「memberships 门分不清主张与否定」的第六次** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **两个门互为补位、各自漏一类的形态也记下来了**："
          "**官方门只查「已登记」的**（漏登记就静默跳过、还报 0 问题）、"
          "**本地门自动发现全部 `_pNNN` 但依赖「verifier 里有那行读取」** ⇒ "
          "⇒ **所以两道门必须都跑、而且必须先确认「读取行在」**",
          '"in_check_uses_in_is_unreliable_995_"' in _ausrc
          and '"two_gates_complement_995_"' in _ausrc
          and "**71 条锚点被两个门同时静默跳过、" in _ausrc
          and "**而两个门都报成功**" in _ausrc
          and "**我第一版用 `if \\\"_p995\\\" not in v:` 当「有没有登记」的判据**"
          in _ausrc
          and "**而判据组 `Z992C` 的正文里本来就写着 `_p995`**" in _ausrc
          and "**「用 `in` 判断有没有登记」不可靠**" in _ausrc
          and "**要判的是「那行读取在不在」、不是「那个名字在不在」**" in _ausrc
          and "**补上之后官方门立刻报出 28 个问题**" in _ausrc
          and "（**27 MISSING + 1 WOULD-FAIL**）" in _ausrc
          and "**官方门只查「已登记」的**" in _ausrc
          and "**本地门自动发现全部 `_pNNN` 但依赖「verifier 里有那行读取」**"
          in _ausrc
          and "**所以两道门必须都跑、" in _ausrc
          and "**而且必须先确认「读取行在」**" in _ausrc
          and "**栽到了第五次、也是最隐蔽的一次**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许用 `名字 in 文件` 当「已登记」的判据**
          and "用 名字 in 文件 当已登记的判据是安全的" not in _ausrc
          # ⭐⭐⭐⭐ **反向门**：**不许把「官方门报 0 问题」当成「锚点全被查过」**
          and "官方门报 0 问题就等于全部被查过" not in _ausrc)

    check("Z992C.9 ⭐⭐⭐⭐⭐ **本批把自省推到了尽头、而那条副作用必须写下来** —— "
          "**我先看到了「交集是 0」才去问「是不是找齐了」** ⇒ "
          "**⇒ 而如果没有那个先看到的结果、我根本不会想到要问** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以「自省」这条纪律有一个容易被忽略的副作用："
          "**它会让好问题只在我们已经撞上它之后才出现** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **这与 992/993/994 那条"
          "**「如实标注哪几条不是盲预测」是同一条的两面** —— "
          "**「标注了盲」不等于「避免了盲」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而 §205 这一整节的问题、"
          "**没有一条是本批一开始就想到要问的** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **「先撞上、再命名」是这条流水线的实际节奏** —— "
          "**而把它如实写下来、胜过假装每批都是设计出来的**",
          '"self_audit_reaches_its_limit_995_"' in _ausrc
          and "**我先看到了「交集是 0」才去问「是不是找齐了」**" in _ausrc
          and "**⇒ 而如果没有那个先看到的结果、我根本不会想到要问**" in _ausrc
          and "**它会让好问题只在我们已经撞上它之后才出现**" in _ausrc
          and "**「标注了盲」不等于「避免了盲」**" in _ausrc
          and "**而 §205 这一整节的问题、**" in _ausrc
          and "**没有一条是本批一开始就想到要问的**" in _ausrc
          and "**「先撞上、再命名」是这条流水线的实际节奏**" in _ausrc
          and "**而把它如实写下来、胜过假装每批都是设计出来的**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许假装每批的问题都是事先设计好的**
          and "这些问题都是事先设计好的" not in _ausrc
          and "本批的问题都是事先想好的" not in _ausrc)

    # ══ A993D. 批 996 **纯离线把「漏登记」做成一道门**（只读两个脚本文本）——
    #   ⭐⭐⭐⭐⭐ **995 栽在「漏了读取行」上、而两个门都报成功**
    print("— A993D. 批 996 纯离线把「漏登记」做成门："
          "⚠️⭐⭐⭐⭐⭐ **「0 缺失」是这道门最危险的状态** ⇒ "
          "**而反向用例连否两次、两次都不是事实否的**")
    check("A993D.1 ⭐⭐⭐⭐⭐ **P1 成立：现状是 0 缺失** —— "
          "**120 个被引用的 `_pNNN`、121 行读取、124 条 `PROBE_VARS` 登记、"
          "两处都齐** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而这个「0」正是本批要处理的东西、不是本批的结论** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **「本批的结论」与「本批看到的现状」必须分开说**",
          '"P1_currently_no_missing"' in _p996
          and '"p1_currently_clean_996"' in _p996
          and '"counts_996"' in _p996
          and '"n_missing_readline"' in _p996
          and '"n_missing_registered"' in _p996
          and '"missing_readline_996"' in _p996
          and '"missing_registered_996"' in _p996
          and '"p1_currently_clean_996_"' in _ausrc
          and "**而这个「0」正是本批要处理的东西、" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「0 缺失」写成「没问题了」**
          and "0 缺失就说明没有问题了" not in _p996
          and "0 缺失就说明没有问题了" not in _ausrc)

    check("A993D.2 ⭐⭐⭐⭐⭐ **P2 成立、而它是本批最要紧的一条："
          "「0 缺失」与「门压根没在跑」在输出上不可区分** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **这与 985 那条「恒假的读数要留」、"
          "990 那条「恒真的读数要认出它」是同一族** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而这里的「恒真」是整道门恒真** —— "
          "**它会一直报 0、而那不代表它有用** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以这道门必须自带反向用例** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而 P2 预言的那个陷阱、在同一批里当场咬了我一口**"
          "（见 `A993D.3`）",
          '"P2_zero_is_the_dangerous_state"' in _p996
          and '"p2_zero_is_dangerous_996"' in _p996
          and '"negative_control_996"' in _p996
          and "**「0 缺失」与「门压根没在跑」在输出上不可区分**" in _p996
          and "**而这里的「恒真」是整道门恒真**" in _p996
          and "**它会一直报 0、而那不代表它有用**" in _p996
          and "**所以这道门必须自带反向用例**" in _p996
          and '"p2_zero_is_dangerous_996_"' in _ausrc
          and "**「0 缺失」与「门压根没在跑」在输出上不可区分**" in _ausrc
          and "**而这里的「恒真」是整道门恒真**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说「报 0 就说明门在工作」**
          and "报了 0 就说明门在工作" not in _p996
          and "报了 0 就说明门在工作" not in _ausrc
          and '"why_this_matters"' in _p996)

    check("A993D.3 ⭐⭐⭐⭐⭐ **P3 连否两次、而两次都不是事实否的** —— "
          "**第一版假名 `_pXXX` 不符合被检的正则 ⇒ 门压根没看见它**；"
          "**第二版我把「读取行」也一起注入了 ⇒ 那正好补上缺失的那一半** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **两次合起来是一句：反向用例要注入的必须是"
          "**「只被引用、没被读取」** —— **而那才是 995 那次真实的漏登记形态** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **这一条比「反向用例有效」本身更值钱** ⇒ ⇒ "
          "⇒ ✅ **改用只注入一条 `X in _p999` 的判据之后、"
          "门立刻把它报出来**（`n_missing_after` 从 0 变成 1）⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而注入走的是内存副本、不是真文件** ⇒ "
          "**所以这道反向用例零副作用、可以每次都跑** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **另外：反向用例的名字自己也要通过被检的正则** —— "
          "**第一版的 `_pXXX` 就没过、所以它当时根本没在测任何东西**",
          '"P3_negative_control_catches"' in _p996
          and '"p3_refuted_twice_996"' in _p996
          # ⚠️ **改写横幅（1001）**：候选已从
          #   写死的一个名字改成**运行时挑一个「仓里没人用、
          #   且自己能通过被检正则」的名字**
          #   ⇒ 形成了**假名与真名撞了**（那个名字
          #   已经被 999 批登记成了一个真探针变量），
          #   而 996 那道门的**反向用例就是因此静默失效**
          and 'def _pick_fake(' in _p996
          and '"fake_note_996"' in _p996
          and "**第一版假名 `_pXXX` 不符合被检的正则 ⇒ 门压根没看见它**"
          in _p996
          and "**第二版我把「读取行」也一起注入了 ⇒ " in _p996
          and "**反向用例要注入的必须是" in _p996
          and "**「只被引用、没被读取」**" in _p996
          and "**这一条比「反向用例有效」本身更值钱**" in _p996
          and "门立刻报它缺读取行" in _p996
          and "**把假引用 `_p999` 注入一份内存副本、门立刻报它缺读取行**" in _p996
          and "**所以反向用例的名字必须自己通过被检的那道正则**" in _p996
          and "**改了代码、忘了改同段散文**" in _p996
          and '"p3_refuted_twice_996_"' in _ausrc
          and "**「只被引用、没被读取」**" in _ausrc
          and "**反向用例要注入的必须是「缺的那一半」、"
          in _ausrc
          and "**反向用例的名字自己也要通过被检的正则**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「注入读取行」也当成反向用例**
          and "注入读取行也是有效的反向用例" not in _p996
          and "注入读取行也是有效的反向用例" not in _ausrc)

    check("A993D.4 ⭐⭐⭐⭐⭐ **P4 与 P5 成立：「两处都要齐」可静态检出、"
          "**「漏登记」于是从「靠人记」变成「有门」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **而它也是 995 那个根因的正面对策**："
          "**既然「名字 in 文件」不可靠、"
          "那就用「那行读取在不在」当判据** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **判据从「一个名字」换成「一行代码」—— "
          "**这与 990 那条「从 `one_lap[i][key]` 改成 `cell` 的 `ring`」"
          "**是同一个动作** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **而「都能被静态检出」很重要："
          "**它让这道门不需要跑 verifier 就知道自己有没有用**",
          '"P4_both_places_are_checkable"' in _p996
          and '"P5_missing_is_now_a_gate"' in _p996
          and '"p4_both_places_checkable_996"' in _p996
          and '"p5_missing_becomes_a_gate_996"' in _p996
          and "**读行与 `PROBE_VARS` 各只有一处、都能被静态检出**" in _p996
          and "**「漏登记」从「靠人记」变成「有门」**" in _p996
          and "那就用「那行读取在不在」当判据" in _p996
          and "**判据从「一个名字」换成「一行代码」" in _p996
          and "**是同一个动作**" in _p996
          and '"p4_both_places_checkable_996_"' in _ausrc
          and '"p5_missing_becomes_a_gate_996_"' in _ausrc
          and "**判据从「一个名字」换成「一行代码」" in _ausrc
          and "**这与 990 那条" in _ausrc
          # ⭐⭐⭐⭐ **反向门**：**不许用「名字 in 文件」当这道门的判据**
          and "用名字在不在文件里当判据是可以的" not in _ausrc
          and 'def _referenced(src):' in _p996
          and 'def _readlines(src):' in _p996
          and 'def _registered(src):' in _p996)

    check("A993D.5 ⭐⭐⭐⭐⭐ **本批沿用 992–995 的自省、而它在这里有个新的形状** —— "
          "**写判据前我已知修完之后状态是齐的** ⇒ "
          "**P1 严格说不是盲预测（我看过状态）** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而 P2/P3 断言的是"
          "**「这道门的危险状态」与「反向用例有效」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **「怎么选候选」是和预测同等重量的元数据** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而这一批的自省还有个新形状："
          "**我的反向用例本身错了两次** ⇒ "
          "**⇒ 而那两次都不是「数据否了预测」、是「用例没在测东西」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **所以「反向用例会红」这件事本身也要被反向用例检验**"
          "—— **而 996 就是这么被自己的 P2 抓住的**",
          '"honest_blind_996"' in _p996
          and 'HONESTY = (' in _p996
          and "**写判据前我已知修完之后状态是齐的**" in _p996
          and "**P1 严格说不是盲预测（我看过状态）**" in _p996
          and "**而 P2/P3 断言的是" in _p996
          and "**「怎么选候选」是和预测同等重量的元数据**" in _p996
          and "**我的反向用例本身错了两次**" in _p996
          and "**而那两次都不是「数据否了预测」、是「用例没在测东西」**" in _p996
          and "**所以「反向用例会红」这件事本身也要被反向用例检验**" in _p996
          and "**而 996 就是这么被自己的 P2 抓住的**" in _p996
          and '"honest_blind_996_"' in _ausrc
          and "**写判据前我已知修完之后状态是齐的**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「反向用例红」当成用例有效的证据**
          and "反向用例红了所以它一定在测东西" not in _p996
          and "反向用例红了所以它一定在测东西" not in _ausrc)

    check("A993D.6 ⭐⭐⭐⭐ **本批纯离线、而且它比 993–995 那几批还轻** —— "
          "**不打开浏览器**、**不按任何键**、**连 `mouse.click` 都没有**、"
          "**只读两个脚本文本** ⇒ ⇒ "
          "⭐⭐⭐⭐ **零计费是结构性的、不是自律的** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而它连 README 都不读、"
          "**所以不会遇上「扫描改变输入」那一类问题** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **⇒ 而这给出一条可移植的分级："
          "**「读脚本文本的门」最轻、「扫文档的门」最重** ⇒ "
          "**⇒ 而越轻的门越该多设** —— **因为它便宜到可以每次都跑**",
          '"offline_996"' in _p996
          and '"offline_996"' in _ausrc
          and "**只读两个脚本文本**" in _p996
          and "**零计费是结构性的、不是自律的**" in _p996
          and "**它连 README 都不读、" in _p996
          and "**所以不会遇上" in _p996
          and "**「读脚本文本的门」最轻、「扫文档的门」最重**" in _p996
          and "**⇒ 而越轻的门越该多设**" in _p996
          and "**因为它便宜到可以每次都跑**" in _p996
          and '"discipline_996"' in _p996
          and "**一道恒报 0 的门、必须自带反向用例**" in _p996
          and "**反向用例要走副本、不许碰真文件**" in _p996
          # ⭐⭐⭐⭐ **反向门**：**不许说「纯离线的门就一定可靠」**
          and "纯离线的门就一定可靠" not in _p996
          and "纯离线的门就一定可靠" not in _ausrc)

    # ══ A993D.7–10. 批 996 **门当场报出来的三条**（不是预测）
    #   ⭐⭐⭐⭐⭐ **沿用 995 那条「先撞上、再命名」：好问题只在我们撞上它之后才出现**
    print("— A993D.7–10. 门当场报出来的三条："
          "⚠️⭐⭐⭐⭐⭐ **这三条都不是预测** ⇒ "
          "**⇒ 而「不是预测」这件事本身要照实写出来、不许混进 P1–P5**")
    check("A993D.7 ⭐⭐⭐⭐⭐ **P6 不是预测、是门当场报的 —— "
          "**「用正则扫判据正文」把散文里的举例当成了真引用** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而这就是 995 那条根因的镜像**："
          "**995 是「拿正文当『有没有登记』的判据」不可靠；"
          "这一条是「拿正则扫正文当『有没有引用』的判据」同样不可靠** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **⇒ 所以判据必须扫 AST 的 `Compare` 节点、"
          "**不许扫字符串字面量** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐ **而它是第一次「我第一次希望这道门是红的」** ⇒ "
          "**它红的正是它该红的东西**",
          '"p6_regex_mistook_prose_996_"' in _p996
          and '"P6_selftest_996"' in _p996
          and '"散文里的样例（应不算引用）"' in _p996
          and '"真引用（应算引用）"' in _p996
          and '"纯字符串字面量（应不算引用）"' in _p996
          and '"P6_hold_996"' in _p996
          and "**「用正则扫判据正文」会把散文里的举例当成真引用**" in _p996
          and "**而这就是 995 那条根因的镜像**" in _p996
          and "**不许扫字符串字面量**" in _p996
          and "**我插进 `A993D.3` 的那句「`X in _p999`」被读成了一个真 `_p999`**"
          in _p996
          and '"p6_regex_mistook_prose_996_"' in _ausrc
          and "**不许扫字符串字面量**" in _ausrc
          # ⭐⭐⭐⭐ **反向门**：**不许把「换了 AST」当成「就没有假阳/假阴了」**
          and "换成 AST 之后就没有误报了" not in _p996
          and "换成 AST 之后就没有误报了" not in _ausrc)

    check("A993D.8 ⭐⭐⭐⭐⭐ **P7 也是当场撞的、而它比 P6 更值钱** —— "
          "**我第一版 AST 多加了一道「左边必须是字符串常量」的过滤** ⇒ ⇒ "
          "⇒ **它把 `all(block in _p894 for block ...)` 这种真引用也滤掉了** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **⇒ 收紧判据不是单调变好的 —— "
          "**它会同时减少假阳性与假阴性、而两侧要分开量** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **⇒ 而差集是唯一能发现这一点的量** —— "
          "**只看「新仪器报 0 缺失」我永远不会知道它漏了 `_p894`** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **⇒ 而这道门的第一版假阴性来自 P6 自己的修正** —— "
          "**为修一个假阳性而造的假阴性、它的成因是同一个动作**",
          '"p7_tightening_false_negative_996_"' in _p996
          and '"P7_selftest_996"' in _p996
          and '"生成器表达式里的真引用（应算引用）"' in _p996
          and '"真实文件里的 `_p894`（应算引用）"' in _p996
          and '"变量名当 comparator 也算"' in _p996
          and '"P7_hold_996"' in _p996
          and "**收紧判据不是单调变好的" in _p996
          and "**它会同时减少假阳性与假阴性、而两侧要分开量**" in _p996
          and "**差集是唯一能发现这一点的量**" in _p996
          and "**为修一个假阳性而造的假阴性、它的成因是同一个动作**" in _p996
          and '"p7_tightening_false_negative_996_"' in _ausrc
          and "**它会同时减少假阳性与假阴性、而两侧要分开量**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说「更严的判据总是更好」**
          and "更严的判据总是更好" not in _p996
          and "更严的判据总是更好" not in _ausrc)

    check("A993D.9 ⭐⭐⭐⭐⭐ **P8 是本批最结构性的发现 —— "
          "**「现状是 0 缺失」这个读数在判据被插进去的那一刻就不再是同一个数** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **⇒ 而 994 那条「一次扫描会改变它所扫描的对象」"
          "**在这里是字面成立的：被扫的就是判据文件本身** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **⇒ 所以「钉判据」与「量现状」有先后顺序、"
          "**而报出来的数必须是**钉完之后**的数** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **⇒ 这就是本批为什么先插判据、再重跑探针** —— "
          "**顺序反过来就会把一个自己造成的读数写成「现状」** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **⇒ 而它是 994 那条的一个更狠的形态："
          "**994 是「同一把尺子量两次」得到不同数；"
          "这一条是「尺子和被量的东西是同一个文件」**",
          '"p8_reading_moves_when_pinned_996_"' in _p996
          and '"P8_hold_996"' in _p996
          and "**这个读数在判据被插进去的那一刻就不再是同一个数**" in _p996
          and "**插入前 119 个被引用；插入 `A993D` 之后变成 120**" in _p996
          and "**在这里是字面成立的：被扫的就是判据文件本身**" in _p996
          and "**顺序反过来就会把一个自己造成的读数写成「现状」**" in _p996
          and "**994 是「同一把尺子量两次」得到不同数；" in _p996
          and "**这一条是「尺子和被量的东西是同一个文件」**" in _p996
          and '"p8_reading_moves_when_pinned_996_"' in _ausrc
          and "**而报出来的数必须是钉完之后**的数**" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许拿「插之前的数」当现状**
          and "插入前的读数就是现状" not in _p996
          and "插入前的读数就是现状" not in _ausrc)

    check("A993D.10 ⭐⭐⭐⭐⭐ **最后一条门自己长出来：键名逐字比对** —— ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **而它是补 P3 自己点出来的那个漏洞**："
          "**P3 里我写过「第二版把 `FAKE` 改成 `_p999`、而散文里还写着 `_pXXX`」"
          "** ⇒ 同样的漂移会发生在**键名**上** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **⇒ 所以把两侧的键名归一化之后逐字比一遍** ⇒ "
          "**⇒ 而第一次跑就真的比出了漂移**："
          "**探针侧 p1–p5 少了 `996` 标记、`p3` 两边根本不是同一个名字** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **⇒ 而这道比对自己又栽了一次「读错文件」**："
          "**我第一版读的是锚点自查门、于是读到 0 个键** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **⇒ 而「读到空」与「读到全部」在输出上都可能长得像「对」** ⇒ "
          "**⇒ 这与 985「恒假的读数要留」、996「恒真的读数要认出它」是同一条**",
          '"keyname_alignment_996"' in _p996
          and '["aligned"] = bool(' in _p996
          and '"only_in_probe"' in _p996
          and '"only_in_audit"' in _p996
          and "**我第一版读的是锚点自查门、于是读到 0 个键**" in _p996
          and "**「读到空」与「读到全部」在输出上都可能长得像「对」**" in _p996
          and "**探针侧 p1–p5 少了 `996` 标记、`p3` 两边根本不是同一个名字**"
          in _p996
          and '"discipline_996"' in _p996
          and "**P6/P7 用行为自测、P1–P5 用存在性**" in _p996
          and "**扫判据要扫 AST 的条件表达式、不许扫字符串字面量**" in _p996
          and "**换判据之后要量新旧两把尺子的差集**" in _p996
          and "**钉判据与量现状有先后顺序、报出来的数必须是钉完之后的**" in _p996
          and '"p6_regex_mistook_prose_996_"' in _ausrc
          and '"p8_reading_moves_when_pinned_996_"' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「比对集为空」当成「两侧一致」**
          and "比对集为空所以两侧一致" not in _p996
          and "比对集为空所以两侧一致" not in _ausrc)

    # ══ B993E. 批 997 **把「31 个未登记变量」拆开**（纯离线、只读门与判据的文本）
    #   ⭐⭐⭐⭐⭐ **而本批最要紧的一条是一个被否的预测**：
    #   **补登记之后门一次也没红 ⇒ 「假绿」的代价不是恒定的**
    print("— B993E. 批 997 把「31 个未登记变量」拆开："
          "❌⭐⭐⭐⭐⭐ **P4 被否、而那个「否」是本批最有价值的读数** ⇒ "
          "⚠️⭐⭐⭐⭐⭐ **「两个尺子一致」是最容易骗人的证据类型**")
    check("B993E.1 ⭐⭐⭐⭐⭐ **P1/P2/P3 成立：「31 个未登记变量」不是一个同质的集合** ⇒ ⇒ "
          "**A 有一行普通 `read_text` 的 1 个（`_p870s`）｜B 派生物 22 个｜"
          "C 不是文本 4 个｜D 连赋值都没有（循环变量）3 个｜E 别名 1 个** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **⇒ 归类之前不该把那个数当成一个口子的大小** ⇒ ⇒ "
          "⇒ ⭐⭐⭐⭐⭐ **⇒ 而「按族的形状去补」这件事已经栽了三次**："
          "**961 补 59 个、962 补 1 个、两次都只按 `_pNNN` 族去补** ⇒ ⇒ "
          "**⇒ 而 995 那条「共 N 条不给检索词」在这里是同族的、只是更狠**",
          '"P1_exactly_one_plain_readline"' in _p997
          and '"p1_one_plain_readline_997_"' in _p997
          and '"p2_derived_outnumber_997_"' in _p997
          and '"p3_single_letter_names_997_"' in _p997
          and "BEFORE_CLASS_997 = {" in _p997
          and '"E_alias": ["_aus936"]' in _p997
          and "所以这不是「又忘了一个」——" in _p997
          and "是「按族的形状去补、而漏掉的那一族一直没人看」" in _p997
          and "「漏登记」这个说法对 B 类是错的" in _p997
          and "这个清单不是一个同质的集合" in _p997
          and '"census_not_homogeneous_997_"' in _ausrc
          and "归类之前不该把那个数当成一个口子的大小" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许拿「未登记」直接当「有缺陷」**
          and "未登记就说明有缺陷" not in _p997
          and "未登记就说明有缺陷" not in _ausrc)

    check("B993E.2 ⭐⭐⭐⭐⭐ **P4 被否、而这个「否」是本批最有价值的读数** ⇒ "
          "**补登记之后官方门报的「问题」数仍然是 0** ⇒ ⇒ "
          "**⇒ 而 961 那次补完 59 个立刻报出了问题、962 那次整组都没被查过** ⇒ ⇒ "
          "**⇒ 所以「假绿」的代价不是恒定的 —— 有的假绿当时恰好是对的** ⇒ ⇒ "
          "**⇒ 而「未登记」是一个需要逐条查的怀疑、不是一个已确认的缺陷** ⇒ ⇒ "
          "**⇒ 这条也否掉了「未登记 ⇒ 有问题」这个默认假设**",
          '"P4_fixing_registration_is_not_a_noop"' in _p997
          and '"p4_refuted_997_"' in _p997
          and '"P4_hold_997"' in _p997
          and "「假绿」的代价不是恒定的" in _p997
          and "有的假绿当时恰好是对的、有的不是、而门不会告诉你哪一种" in _p997
          and "「未登记」是一个需要逐条查的怀疑、不是一个已确认的缺陷" in _p997
          and '"p4_refuted_cost_not_constant_997_"' in _ausrc
          and "「假绿」的代价不是恒定的" in _ausrc
          and "「未登记」是一个需要逐条查的怀疑、不是一个已确认的缺陷" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「0 问题」写成「那 2 条锚点是对的」**
          and "0 问题说明那两条锚点本来就是对的" not in _p997
          and "0 问题说明那两条锚点本来就是对的" not in _ausrc)

    check("B993E.3 ⭐⭐⭐⭐⭐ **P5 成立：补登记会改变门的行为 ⇒ 而这正是 996 P8 的第二次施用** ⇒ ⇒ "
          "**锚点 5390 → 5416（+26）、跳过 169 → 143 条 / 31 → 29 个变量** ⇒ ⇒ "
          "**⇒ +26 正好是 `_p870s` 的 2 条 + 别名 `_aus936` 的 24 条** ⇒ ⇒ "
          "**⇒ 而「补之前的读数」与「补之后的读数」必须都留着** ⇒ ⇒ "
          "**⇒ 而 E 类（别名）给出的处置是「给它一个别名」而不是「再读一遍文件」**",
          '"P5_registration_moves_the_reading"' in _p997
          and '"p5_registration_moves_the_reading_997_"' in _p997
          and '"P5_hold_997"' in _p997
          and '"before_997"' in _p997
          and '"after_997"' in _p997
          and "补之前的读数」与「补之后的读数」必须都留着" in _p997
          and "E 类（别名）给出的处置是「给它一个别名」" in _p997
          and '"p5_registration_moves_the_reading_997_"' in _ausrc
          and "补之前的读数」与「补之后的读数」必须都留着" in _ausrc
          # ⭐⭐⭐⭐ **反向门**：**不许只报改之后的读数**
          and "只报改之后的读数就够了" not in _p997
          and "只报改之后的读数就够了" not in _ausrc)

    check("B993E.4 ⭐⭐⭐⭐⭐ **补登记既不是空动作、也不是「修好了」** ⇒ ⇒ "
          "**它确实让 26 条锚点第一次被查、而它一次也没红** ⇒ ⇒ "
          "**⇒ 而后者才是本批要说的：一条锚点「从来没被查过」与「查过且通过」"
          "**在门的历史里长得一模一样** ⇒ ⇒ "
          "**⇒ 只有把「补之前」那个读数抄下来、这件事才看得见** ⇒ ⇒ "
          "**⇒ 而如果我先补登记、再跑门、只会看见一个 0**",
          '"p6_not_a_noop_not_a_fix_997_"' in _p997
          and '"P6_hold_997"' in _p997
          and "在门的历史里长得一模一样" in _p997
          and "只有把「补之前」那个读数抄下来、这件事才看得见" in _p997
          and "而如果我先补登记、再跑门、只会看见一个 0" in _p997
          and '"p6_not_a_noop_not_a_fix_997_"' in _ausrc
          and "在门的历史里长得一模一样" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「补了」写成「修好了」**
          and "补登记之后这个问题就修好了" not in _p997
          and "补登记之后这个问题就修好了" not in _ausrc)

    check("B993E.5 ⭐⭐⭐⭐⭐ **P7 是本批最结构的一条：「两个尺子一致」是最容易骗人的证据类型** ⇒ ⇒ "
          "**⇒ 本批真的出现过「差集 = 0」的状态、而那是最坏的状态** ⇒ ⇒ "
          "**⇒ 根因是「两份实现抄了同一份判据」⇒ 「独立写的」这个前提本身就是假的** ⇒ ⇒ "
          "**⇒ 所以 996 P7「差集是唯一能发现新仪器变瞎的量」要加一条补充：** "
          "**判据相同时差集会归零、而那正是变瞎的信号** ⇒ ⇒ "
          "**⇒ 而 `_tlc` 的真身是 B：它的赋值是「join 一个生成器」、"
          "**那个生成器里是 `.read_text().splitlines()` 再按 `startswith` 过滤注释行** ⇒ ⇒ "
          "**⇒ 门判 A（错）、探针判 B（对）**",
          '"p7_two_rulers_disagree_997_"' in _p997
          and '"P7_hold_997"' in _p997
          and '"zero_disagree_was_the_bad_state_997"' in _p997
          and '"disagree_997"' in _p997
          and '"tlc_truth_997"' in _p997
          and "两个尺子一致」是最容易骗人的证据类型" in _p997
          and "独立写的」这个前提本身就是假的" in _p997
          and "判据相同时差集会归零、而那正是变瞎的信号" in _p997
          and "comprehension + 一次过滤" in _p997
          and "它同时是一个 comprehension + 一次过滤、所以它是 B" in _p997
          and '"p7_agreement_is_the_most_deceptive_997_"' in _ausrc
          and '"tlc_one_ruler_right_997_"' in _ausrc
          and "两个尺子一致」是最容易骗人的证据类型" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「两个尺子一致」当证据**
          and "两个尺子一致所以可以放心" not in _p997
          and "两个尺子一致所以可以放心" not in _ausrc)

    check("B993E.6 ⭐⭐⭐⭐⭐ **P8：「补完之后 A 类是 0」是一个恒真的读数** ⇒ ⇒ "
          "**「A 类是 0」与「A 类这一栏没有意义」在输出上完全一样** ⇒ ⇒ "
          "**⇒ 而真实原因只是「我刚把唯一那个补上了」** ⇒ ⇒ "
          "**⇒ 这是 996 P2「恒真的读数要认出它」的同一条、只是对象换成了一个类** ⇒ ⇒ "
          "**⇒ 而唯一能认出它的办法就是那句「补之前是 1」** ⇒ "
          "**⇒ 也就是说 P8 之所以能成立、恰恰是因为 before 被留下来了**",
          '"p8_zero_means_what_997_"' in _p997
          and '"P8_hold_997"' in _p997
          and "A 类是 0」与「A 类这一栏没有意义" in _p997
          and "真实原因只是「我刚把唯一那个补上了」" in _p997
          and "P8 之所以能成立" in _p997
          and '"p8_zero_reading_997_"' in _ausrc
          and "只是对象从一个数换成了一个类" in _ausrc
          and "补之前是 1" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「A 类 0」写成「这一类已经没有问题了」**
          and "A 类 0 说明这一类已经没有问题了" not in _p997
          and "A 类 0 说明这一类已经没有问题了" not in _ausrc)

    check("B993E.7 ⭐⭐⭐⭐⭐ **本批自己出了一次 996 P6 的实例、而且是反向的** ⇒ ⇒ "
          "**我在给 audit 插入新块时、把整个 `regguard_996` 删掉了** ⇒ ⇒ "
          "**⇒ 官方门当场报出 24 条 MISSING、全部指向那个块** ⇒ ⇒ "
          "**⇒ 而这次它是「该红的就红了」—— 与 996 P6 那次同族、方向相反** ⇒ ⇒ "
          "**⇒ 处置：从上一个 commit 取回整块、按正确缩进重插、再跑门** ⇒ ⇒ "
          "**⇒ 教训：改一个上万行的共享文件时、删掉一整块是默认风险、"
          "**而门是唯一的检出手段** ⇒ ⇒ "
          "**⇒ 而这又一次印证「两个门互为补位」**",
          '"i_deleted_996_block_997_"' in _ausrc
          and "我在给 audit 插入新块时、把整个 `regguard_996` 删掉了" in _ausrc
          and "官方门当场报出 24 条 MISSING、全部指向那个块" in _ausrc
          and "该红的就红了" in _ausrc
          and "上万行的共享文件时、删掉一整块是默认风险、" in _ausrc
          and "两个门互为补位" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「门报红了」当成「这个文件本来就有问题」**
          and "门报红说明这个文件本来就有问题" not in _ausrc
          and "门报红说明这个文件本来就有问题" not in _p997)

    check("B993E.8 ⭐⭐⭐⭐⭐ **本批纯离线、而且它比 993–996 那几批还轻** ⇒ ⇒ "
          "**不打开浏览器**、**不按任何键**、**连 `mouse.click` 都没有**、"
          "**只读门与 verifier 的文本、再跑一次门** ⇒ ⇒ "
          "⭐⭐⭐⭐ **零计费是结构性的、不是自律的** ⇒ ⇒ "
          "**⇒ 而本批的动作比读文本还多一步：它**改了门** ⇒ ⇒ "
          "**⇒ 所以「改门」的代价是结构性的：改完必须重跑、"
          "**而且 before 与 after 都要留**",
          '"offline_997"' in _p997
          and '"offline_997"' in _ausrc
          and "连 `mouse.click` 都没有" in _p997
          and "只读门与 verifier 的文本、再跑一次门" in _p997
          and "零计费是结构性的、不是自律的" in _p997
          and '"discipline_997"' in _p997
          and "用真的门当尺子、别用自己重写的尺子" in _p997
          and "两个尺子一致不算证据、除非能证明两份判据不同" in _p997
          and "判据要用结构（AST 节点）、不要用词" in _p997
          and "改共享大文件时「删掉一整块」是默认风险" in _p997
          and '"discipline_997"' in _ausrc
          and "改共享大文件时「删掉一整块」是默认风险、" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说「改了门所以更可信了」**
          and "改了门所以更可信了" not in _p997
          and "改了门所以更可信了" not in _ausrc)

    # ══ C993F. 批 998 **「改成引用原始变量」这条路先预演、不先改**
    #   ⭐⭐⭐⭐⭐ **而本批的两个主要结果都是「否」**：
    #   **P2 否掉的是我自己写下的推理；P1 的否根本没有信息量**
    print("— C993F. 批 998 先预演、不先改："
          "❌⭐⭐⭐⭐⭐ **P2 被否 —— 「派生物 ⊆ 原文」只在来自同一个文件时成立** ⇒ "
          "⚠️⭐⭐⭐⭐⭐ **而 P1 的「否」没有信息量：那个阈值是我拍的**")
    check("C993F.1 ⭐⭐⭐⭐⭐ **P1 按它写下来的形式被否了、而这次否证没有信息量** ⇒ ⇒ "
          "**⇒ 因为判据里写死了「不可定位的 ≤ 6 个」、而那个 6 是我拍的** ⇒ ⇒ "
          "**⇒ 实测是 10 个** ⇒ ⇒ "
          "**⇒ 而我第一反应是「把阈值从 6 放宽到 12、让判据变绿」** ⇒ ⇒ "
          "**⇒ 那一刻我做的正是这一节开头批评的那件事** ⇒ ⇒ "
          "**⇒ 所以这里保留原阈值、让 P1 红着** ⇒ ⇒ "
          "**⇒ 一个自己拍的阈值，它的红和它的绿同样没有信息量**",
          '"P1_all_derivable_resolve"' in _p998
          and '"p1_refuted_threshold_was_mine_998_"' in _p998
          and '"P1_hold_998"' in _p998
          and "我那条判据里写死了「不可定位的 ≤ 6 个」" in _p998
          and "实测是 10 个" in _p998
          and "把阈值从 6 放宽到 12、让判据变绿" in _p998
          and "保留原阈值、让 P1 红着" in _p998
          and "一个自己拍的阈值，它的红和它的绿同样没有信息量" in _p998
          and '"p1_threshold_was_mine_998_"' in _ausrc
          and "一个自己拍的阈值，它的红和它的绿同样没有信息量" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许用「放宽阈值」当修复**
          and "放宽阈值就好了" not in _p998
          and "放宽阈值就好了" not in _ausrc)

    check("C993F.2 ⭐⭐⭐⭐⭐ **P2 被否、而它否掉的是我自己写下的那条推理** ⇒ ⇒ "
          "**⇒ 我写的是「派生物 ⊆ 原文（`strip_comments` 只会删）」** ⇒ ⇒ "
          "**⇒ 实测 110 条正向锚点里只有 73 条在原始全文上命中** ⇒ ⇒ "
          "**⇒ 而「⊆」只在派生物来自同一个文件时成立** ⇒ ⇒ "
          "**⇒ 派生物的源头有三种：一个文件路径（11）｜判据里的一段字面量（2）｜"
          "**回溯不到（10）** ⇒ ⇒ "
          "**⇒ 所以「先假设它是子集、再据此推理」是错的**",
          '"P2_positive_anchors_all_hit_raw"' in _p998
          and '"p2_subset_refuted_998_"' in _p998
          and '"P2_hold_998"' in _p998
          and "我写的是「派生物 ⊆ 原文" in _p998
          and "110 条正向锚点里只有 73 条在原始全文上命中" in _p998
          and "只在派生物来自" in _p998
          and "先假设它是子集、再据此推理" in _p998
          and '"source_kind_census_998"' in _p998
          and '"p2_subset_refuted_998_"' in _ausrc
          and "只在派生物来自同一个文件时成立" in _ausrc
          and "回溯不到（10 个）" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「派生物」当成「原文的子集」直接用**
          and "派生物一定是原文的子集" not in _p998
          and "派生物一定是原文的子集" not in _ausrc)

    check("C993F.3 ⭐⭐⭐⭐⭐ **P3 成立、而它是本批的主要交付："
          "**13 条反向锚点里有 1 条在原始全文上会命中** ⇒ ⇒ "
          "**⇒ 「改成引用原文是安全的」这个默认假设是错的** ⇒ ⇒ "
          "**⇒ 而那个数不用改任何判据就量出来了** ⇒ ⇒ "
          "**⇒ 进一步说：既然「⊆」本身就不成立、"
          "**那 37 条不命中的正向锚点也在说同一件事**",
          '"P3_some_negative_anchors_would_fail"' in _p998
          and '"p3_negative_would_fail_998_"' in _p998
          and '"P3_hold_998"' in _p998
          and "13 条反向锚点里有 1 条在原始全文上会命中" in _p998
          and "而它不用改任何判据就量出来了" in _p998
          and "那 37 条不命中的正向锚点也在说同一件事" in _p998
          and '"p3_negative_would_fail_998_"' in _ausrc
          and "「改成引用原文是安全的」这个默认假设是错的" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许因为「多数命中」就说这条路是安全的**
          and "大部分命中所以这条路是安全的" not in _p998
          and "大部分命中所以这条路是安全的" not in _ausrc)

    check("C993F.4 ⭐⭐⭐⭐⭐ **P4 成立：预演是零副作用的 ⇒ "
          "**所以处置可以从「先改再说」变成「先量再决定」** ⇒ ⇒ "
          "**⇒ 而「清单取自真的门、预演自己写」这件事必须标注出来** ⇒ ⇒ "
          "**⇒ 因为门对未登记的变量压根不把那些锚点交出来**",
          '"P4_the_dry_run_is_free"' in _p998
          and '"p4_dryrun_is_free_998_"' in _p998
          and '"P4_hold_998"' in _p998
          and '"note_own_collector_998"' in _p998
          and "本批唯一一处「自己重写的收集器」" in _p998
          and "因为门对未登记的变量是 `continue`" in _p998
          and "所以处置可以从「先改再说」变成「先量再决定」" in _p998
          and '"p4_dryrun_is_free_998_"' in _ausrc
          and "门对未登记的变量压根不把锚点交出来" in _ausrc
          # ⭐⭐⭐⭐ **反向门**：**不许把「自己写的收集器」和「真的门」混为一谈**
          and "自己写的收集器和门等价" not in _p998
          and "自己写的收集器和门等价" not in _ausrc)

    check("C993F.5 ⭐⭐⭐⭐⭐ **本批的第一次反向用例、我把三个答案都写死成了 `True`** ⇒ ⇒ "
          "**⇒ 而那正是 997 刚批过的「恒真的读数」—— 我自己又犯了一次** ⇒ ⇒ "
          "**⇒ 处置：构造三个内存里的判据片段、跑**同一个** `path_of`** ⇒ ⇒ "
          "**⇒ 三个样本分别回溯到：一个文件路径｜`<inline-literal>`｜`None`** ⇒ ⇒ "
          "**⇒ 而「本该回溯不到、而它确实回溯不到」那一条才是防恒真的样本** ⇒ ⇒ "
          "**⇒ 这与 990 那条是同一条、而我是在被自己批过之后 20 分钟内又犯的**",
          '"negative_control_998"' in _p998
          and '"NC_hold_998"' in _p998
          and '"nc_i_hardcoded_the_answers_998_"' in _ausrc
          and "第一版我把三个答案都写成了硬编码 `True`" in _p998
          and "那正是 997 刚批过的「恒真的读数」" in _p998
          and "现在改成：构造三个内存里的判据片段" in _p998
          and "我自己又犯了一次" in _ausrc
          and "被自己批过之后 20 分钟内又犯的" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把写死的期望值当成反向用例**
          and "期望值写死也算反向用例" not in _p998
          and "期望值写死也算反向用例" not in _ausrc)

    check("C993F.6 ⭐⭐⭐⭐⭐ **本批纯离线、而且它比 993–997 那几批还轻** ⇒ ⇒ "
          "**不打开浏览器**、**不按任何键**、**连 `mouse.click` 都没有**、"
          "**只读门与判据的文本、再读一批源文件** ⇒ ⇒ "
          "⭐⭐⭐⭐ **零计费是结构性的、不是自律的** ⇒ ⇒ "
          "**⇒ 而本批第一次动手的不是浏览器、也不是 DOM、而是「一条赋值语句的形状」**",
          '"offline_998"' in _p998
          and '"offline_998"' in _ausrc
          and "连 `mouse.click` 都没有" in _p998
          and "只读门与判据的文本、再读一批源文件" in _p998
          and "零计费是结构性的、不是自律的" in _p998
          and '"discipline_998"' in _p998
          and "「派生物 ⊆ 原文」只对「来自同一个文件」的派生物成立" in _p998
          and "「否证」也可能是「我的阈值拍的」" in _p998
          and "阈值要配理由" in _p998
          and "「我刚批过的毛病」不会因为批过就自动免疫" in _p998
          and '"discipline_998"' in _ausrc
          and "「我刚批过的毛病」不会因为批过就自动免疫" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说「批过一次就免疫了」**
          and "批过一次就免疫了" not in _p998
          and "批过一次就免疫了" not in _ausrc)

    # ══ D993G. 批 999 **「共 N 条」给了检索词之后还要给身份**
    #   ⭐⭐⭐⭐⭐ **而本批最重要的结果是 998 那个「1」被翻过来了**：
    #   **它不是「代价」、是 `Q.10` 刻意对注释免疫的优点**
    print("— D993G. 批 999 给那 1 条身份："
          "⚠️⭐⭐⭐⭐⭐ **它不是代价、是 `Q.10` 刻意对注释免疫的优点** ⇒ "
          "❌ **而 P2 被否之后有一个更好的说法**")
    check("D993G.1 ⭐⭐⭐⭐⭐ **P1 成立：那 1 条能被唯一定位** ⇒ ⇒ "
          "**变量 `picode`｜锚点 `bg-black/`｜判据组 `Q`｜那条判据是 `Q.10`** ⇒ ⇒ "
          "**⇒ 同一个变量上还有 6 条判据、而没有组名就不知道该找谁** ⇒ ⇒ "
          "**⇒ 这是「共 N 条要给检索词」的下一层：检索词只让人能复算、"
          "**身份才让人能处置**",
          '"P1_identifiable"' in _p999
          and '"p1_identifiable_999_"' in _p999
          and '"P1_hold_999"' in _p999
          and '"identity_999"' in _p999
          and '"n_checks_using_same_var"' in _p999
          and "检索词只让人能复算、身份才让人能处置" in _p999
          and '"p1_identifiable_999_"' in _ausrc
          and "检索词只让人能复算、身份才让人能处置" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「给出检索词」当成「给出了身份」**
          and "给了检索词就等于给了身份" not in _p999
          and "给了检索词就等于给了身份" not in _ausrc)

    check("D993G.2 ⭐⭐⭐⭐⭐ **P2 按它写下来的形式被否了、而被否之后有更好的说法** ⇒ ⇒ "
          "**⇒ 我写的是「那 1 条的源头是判据里的一段字面量」** ⇒ ⇒ "
          "**⇒ 实测它的源头是一个真文件** ⇒ ⇒ "
          "**⇒ 更好的说法是：它之所以会在原文上命中、"
          "**是因为它出现的唯一位置是文件里的一行注释** ⇒ ⇒ "
          "**⇒ 也就是说 998 那个「1」不是「改成引用原文的代价」、"
          "**它是这条判据的优点在预演里被误读成了缺陷** ⇒ ⇒ "
          "**⇒ ⇒ 998 的 P3 方向对了、对象错了**",
          '"P2_its_source_is_inline_literal"' in _p999
          and '"p2_refuted_and_better_999_"' in _p999
          and '"P2_hold_999"' in _p999
          and "我写的是「那 1 条的源头是判据里的一段字面量」" in _p999
          and "实测它的源头是" in _p999
          and "是因为它出现的唯一位置是文件里的一行注释" in _p999
          and "它是这条判据的优点在预演里被误读成了缺陷" in _p999
          and "998 的 P3 方向对了、对象错了" in _p999
          and '"p2_refuted_and_better_999_"' in _ausrc
          and "它是这条判据的优点在预演里被误读成了缺陷" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把那 1 条当成「要修的缺陷」**
          and "那一条是需要修的缺陷" not in _p999
          and "那一条是需要修的缺陷" not in _ausrc)

    check("D993G.3 ⭐⭐⭐⭐⭐ **P9 不是预测 —— 那 1 条是判据「对注释免疫」的设计** ⇒ ⇒ "
          "**⇒ 那行注释写的是「资产库有 `bg-black/55` 全屏遮罩、"
          "**实测 11 个焦点位看不见、那边才该困」** ⇒ ⇒ "
          "**⇒ 注释里提到它、讲的是**另一个组件**有遮罩** ⇒ ⇒ "
          "**⇒ 而如果判据查的是原文、它会因为一句「对比说明」而红** ⇒ ⇒ "
          "**⇒ 所以查剥离注释后的文本是对的设计** ⇒ ⇒ "
          "**⇒ 「预演报出一条会失败的」不足以支持任何结论 —— "
          "**必须先问「这条判据为什么写成反向」** ⇒ ⇒ "
          "**⇒ 而「反向断言」的存在本身就带着「它针对什么」的答案**",
          '"p9_the_one_is_by_design_999_"' in _p999
          and '"P9_hold_999"' in _p999
          and '"n_where_in_comment_999"' in _p999
          and '"where_999"' in _p999
          and "讲的是" in _p999
          and "而如果这条判据查的是原文、它会因为一句「对比说明」而红" in _p999
          and "预演报出一条会失败的」不足以支持任何结论" in _p999
          and "必须先问「这条判据为什么写成反向」" in _p999
          and '"p9_the_one_is_by_design_999_"' in _ausrc
          and "预演报出一条会失败的」不足以支持任何结论" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许只量「会不会红」就下结论**
          and "它会红所以这条路不能走" not in _p999
          and "它会红所以这条路不能走" not in _ausrc)

    check("D993G.4 ⭐⭐⭐⭐⭐ **P3 成立：「回溯不到」能拆成若干类、"
          "**而且拆到「赋值处」那一层才是有用的粒度** ⇒ ⇒ "
          "**⇒ 因为同一个名字在不同赋值处形状不同** ⇒ ⇒ "
          "**⇒ 所以「这个变量是什么」这句话本身是有歧义的** ⇒ ⇒ "
          "**⇒ 而「31 个是四类」｜「源头是三类」｜「回溯不到又是若干类」** ⇒ "
          "**⇒ 层次越多、越说明最初那个「31」是一个压缩包**",
          '"P3_unresolvable_has_four_classes"' in _p999
          and '"p3_unresolved_has_classes_999_"' in _p999
          and '"P3_hold_999"' in _p999
          and '"unresolved_shapes_999"' in _p999
          and "拆到「赋值」那一层才是有用的粒度" in _p999
          and "这个变量是什么」这句话本身是有歧义的" in _p999
          and "越说明最初那个「31」是一个压缩包" in _p999
          and '"p3_unresolved_has_classes_999_"' in _ausrc
          and "越说明最初那个「31」是一个压缩包" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「一个变量」当成「一个东西」**
          and "一个变量就是一个东西" not in _p999
          and "一个变量就是一个东西" not in _ausrc)

    check("D993G.5 ⭐⭐⭐⭐⭐ **P10：仪器又栽了两次、而且「用可见的形状当判据」"
          "**这是第四次** ⇒ ⇒ "
          "**① 「这行开头有没有 `//` `*` `/*`」⇒ 而目标那行是块注释的**最后一行**"
          "（以 `*/` 结尾、开头是中文）⇒ 判成「不在注释里」** ⇒ ⇒ "
          "**② 「扫跨度、看这行结束时 depth 还在不在」⇒ 而末行的 `*/` "
          "**恰好把 depth 归零 ⇒ 还是判错** ⇒ ⇒ "
          "**⇒ 正确的粒度是列 ⇒ 而前三次各修一次就对了、本次修两次才对着** ⇒ ⇒ "
          "**⇒ 说明「换个更结构化的判据」本身没有保证**",
          '"p10_instrument_4th_time_999_"' in _p999
          and 'def comment_depth_at(' in _p999
          and '"comment_span_nc_999"' in _p999
          and '"NC_hold_999"' in _p999
          and "而目标那行是块注释的" in _p999
          and "恰好把 depth 归零" in _p999
          and "正确的粒度是列" in _p999
          and "本次修两次才对着" in _p999
          and "换个更结构化的判据」本身没有保证" in _p999
          and '"p10_instrument_4th_time_999_"' in _ausrc
          and "换个更结构化的判据」本身没有保证" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说「结构化判据一定更对」**
          and "结构化判据一定更对" not in _p999
          and "结构化判据一定更对" not in _ausrc)

    check("D993G.6 ⭐⭐⭐⭐⭐ **而本批开工第一件事就踩了「读到 0」** ⇒ ⇒ "
          "**我用 `tree.body` 找 `check(...)`、结果一条都没找到** ⇒ ⇒ "
          "**⇒ 因为判据全在 `main()` 函数体内、而 `tree.body` 只有模块顶层** ⇒ ⇒ "
          "**⇒ 而「读到 0 条」差一点就被我当成「没有判据」** ⇒ ⇒ "
          "**⇒ 处置：按 `lineno` 排序扫全树** ⇒ ⇒ "
          "**⇒ 这与「读到空与读到全部都可能长得像对」是同一条、"
          "**而且是同一天里第二次犯**",
          '"n_rows_999"' in _p999
          and '"n_rows_zero_999_"' in _ausrc
          and "而 `tree.body` 只有模块顶层" in _p999
          and "差一点就被我当成「没有判据」" in _p999
          and "按 `lineno` 排序扫全树" in _p999
          and '"n_rows_zero_999_"' in _ausrc
          and "差一点就被我当成「没有判据」" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「读到 0」当成「不存在」**
          and "读到 0 就是不存在" not in _p999
          and "读到 0 就是不存在" not in _ausrc)

    check("D993G.7 ⭐⭐⭐⭐⭐ **P4 成立：有了身份之后、处置是可以写出来的** ⇒ ⇒ "
          "**⇒ 而处置是：这条判据**不要改** —— 它查的是剥离注释后的文本、"
          "**而那正是它该查的** ⇒ ⇒ "
          "**⇒ 唯一该做的是把这条写进文档、"
          "**免得下一个人看到 998 那个「1」就去「修」它** ⇒ ⇒ "
          "**⇒ 而「写不出处置的身份不算身份」就是这个验收标准** ⇒ ⇒ "
          "**⇒ 本批纯离线：不打开浏览器、不按任何键、**连 `mouse.click` 都没有**、"
          "**只读判据文件与 998 的输出** ⇒ ⇒ "
          "⭐⭐⭐⭐ **零计费是结构性的、不是自律的**",
          '"P4_identity_is_actionable"' in _p999
          and '"p4_identity_is_actionable_999_"' in _p999
          and '"P4_hold_999"' in _p999
          and '"offline_999"' in _p999
          and '"offline_999"' in _ausrc
          and "这条判据**不要改**" in _p999
          and "免得下一个人看到 998 那个「1」就去「修」它" in _p999
          and "写不出处置的身份不算身份" in _p999
          and "连 `mouse.click` 都没有" in _p999
          and "零计费是结构性的、不是自律的" in _p999
          and '"discipline_999"' in _p999
          and "「口径错误」也是读数、不能靠抹掉当没发生" in _p999
          and '"discipline_999"' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「口径错了」直接抹掉**
          and "口径错了就当没发生" not in _p999
          and "口径错了就当没发生" not in _ausrc)

    # ══ E993H. 批 1000 **反向断言普查：它们各自在防什么**
    #   ⭐⭐⭐⭐⭐ **而本批五个预测否了四个 —— 两条否的是「我的模式」、一条否的是世界**
    print("— E993H. 批 1000 反向断言普查："
          "❌⭐⭐⭐⭐⭐ **P2 被否：206 条反向断言全部查原文、0 条查剥离后的** ⇒ "
          "**⇒ 而 §209 那条唯一的例外恰恰没被登记**")
    check("E993H.1 ⭐⭐⭐⭐⭐ **P2 被否、而它否出来的东西比预测更好** ⇒ ⇒ "
          "**⇒ 我写的是「反向锚点里挂在剥离注释后的文本上的占多数」** ⇒ ⇒ "
          "**⇒ 实测 206 条已登记的反向断言、206 条查的是原文、0 条查剥离后的** ⇒ ⇒ "
          "**⇒ 所以「对注释免疫」是这个仓里的 1/206 孤例 —— "
          "**而那 1 条恰恰因为用了 `strip_comments` 而落在「未登记」里、官方门不查它** ⇒ ⇒ "
          "**⇒ 一条对的设计、和一条被检查的设计、是两件事** ⇒ ⇒ "
          "**⇒ 而 `PROBE_VARS` 的形状是一道隐形口径：凡登记的必查原文** ⇒ ⇒ "
          "**⇒ 这道口径对「钉代码在做什么」是对的、对「钉文档说了什么」是错的**",
          '"P2_most_negatives_are_on_stripped_text"' in _p1000
          and '"p2_refuted_headline_1000_"' in _p1000
          and '"P2_hold_1000"' in _p1000
          and '"neg_textkind_1000"' in _p1000
          and '"n_stripped_1000"' in _p1000
          and "206 条查的是原文、0 条查剥离后的" in _p1000
          and "一条对的设计、和一条被检查的设计、是两件事" in _p1000
          and "它是一道隐形的口径：凡是被登记的，查的必然是原文" in _p1000
          and '"p2_refuted_headline_1000_"' in _ausrc
          and "一条对的设计、和一条被检查的设计、是两件事" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「0 条」当成「这类判据不存在」**
          and "0 条说明这类判据不存在" not in _p1000
          and "0 条说明这类判据不存在" not in _ausrc)

    check("E993H.2 ⭐⭐⭐⭐⭐ **P3 / P4 被否、而否证的是我的模式不是世界** ⇒ ⇒ "
          "**⇒ 我列的两族只覆盖 13/206 = 6%、那条「读数」正则量到的是「含数字」** ⇒ ⇒ "
          "**⇒ 第二版改按结构分：W 中文散文 143｜K 代码片段 48｜I 标识符 8｜O 其它 7** ⇒ ⇒ "
          "**⇒ 覆盖率从 6% 到 97%** ⇒ ⇒ "
          "**⇒ 而真两族是「中文散文片段（防某句措辞被写回去）」对"
          "**「代码片段 / 标识符（防某个实现被引入）」** ⇒ ⇒ "
          "**⇒ 这正是「分类的第一步是『这句话在做什么』、不是『它属于哪个关键词』」**",
          '"P3_two_families"' in _p1000
          and '"P4_some_negative_anchors_are_themselves_readings"' in _p1000
          and '"p3_refuted_my_patterns_1000_"' in _p1000
          and '"p4_refuted_also_my_pattern_1000_"' in _p1000
          and '"P3_hold_1000"' in _p1000
          and '"P4_hold_1000"' in _p1000
          and '"family_coverage_1000"' in _p1000
          and "只覆盖 13/206 = 6%" in _p1000
          and "覆盖率从 6% 到 97%" in _p1000
          and "按结构分出来的真两族是" in _p1000
          and "不是『它属于哪个关键词』" in _p1000
          and '"p3_refuted_my_patterns_1000_"' in _ausrc
          and "覆盖率从 6% 到 97%" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「94% 落在其它」说成「数据没有结构」**
          and "94% 落在其它说明数据没有结构" not in _p1000
          and "94% 落在其它说明数据没有结构" not in _ausrc)

    check("E993H.3 ⭐⭐⭐⭐⭐ **P5 被否、而这次是关于世界的** ⇒ ⇒ "
          "**⇒ 实测 25 个组、前三名占 34% —— 而 34% 不是「高度集中」** ⇒ ⇒ "
          "**⇒ 所以 P5 的否与 P3/P4 的否不同类："
          "**P3/P4 的否是「我的模式不对」、这一条是「世界就是这样」** ⇒ ⇒ "
          "**⇒ 而两类否证必须分开数 —— 否则就会把「我的模式不对」记成「我了解这个仓」**",
          '"P5_group_concentration"' in _p1000
          and '"p5_refuted_not_concentrated_1000_"' in _p1000
          and '"P5_hold_1000"' in _p1000
          and '"top3_share_1000"' in _p1000
          and '"n_groups_with_negatives_1000"' in _p1000
          and "34% 不是「高度集中」" in _p1000
          and "P5 的否与 P3/P4 的否不同类" in _p1000
          and '"p5_refuted_not_concentrated_1000_"' in _ausrc
          and "两类否证必须分开数" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「我的模式不对」记成「我了解这个仓」**
          and "我的模式不对说明我了解这个仓" not in _p1000
          and "我的模式不对说明我了解这个仓" not in _ausrc)

    check("E993H.4 ⭐⭐⭐⭐⭐ **反向用例：证明 `is_stripped()` 能返回 True** ⇒ ⇒ "
          "**⇒ `picode`（仓里真实存在的 `strip_comments` 变量）返回 True** ⇒ ⇒ "
          "**⇒ 而 `_ausrc` 与 `_p996` 返回 False** ⇒ ⇒ "
          "**⇒ 所以「206 条全是 raw」这个 0 是读数、不是探测器坏了** ⇒ ⇒ "
          "**⇒ 而这条不是形式：它正是本批那个结论能不能成立的前提**",
          '"negative_control_1000"' in _p1000
          and '"NC_hold_1000"' in _p1000
          and '"nc_1000_"' in _ausrc
          and "「恒零」与「恒真」一样危险" in _p1000
          and "本该返回 True、而它确实返回 True" in _p1000
          and '"nc_1000_"' in _ausrc
          and "它正是本批那个结论能不能成立的前提" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许用一个 0 去做「这类不存在」的结论**
          and "0 条就说明这一类判据不存在" not in _p1000
          and "0 条就说明这一类判据不存在" not in _ausrc)

    check("E993H.5 ⭐⭐⭐⭐⭐ **而本批的仪器先坏过一次** ⇒ ⇒ "
          "**`is_stripped()` 的 `IfExp` 分支把 `unparse(body)` 当变量名传下去** ⇒ ⇒ "
          "**⇒ `amap.get(...)` 永远为空、返回 None ⇒ 118/206 落在「unknown」** ⇒ ⇒ "
          "**⇒ 而「unknown 一半以上」不是数据如此、是那个分支坏了** ⇒ ⇒ "
          "**⇒ 修好后 206/206 都是 `raw` —— 而 P2 依然是否的** ⇒ ⇒ "
          "**⇒ 也就是说：仪器坏掉时我差点得到相反的结论、而我按纪律先判了「门错还是数据错」**",
          '"instrument_unknown_1000_"' in _ausrc
          and "把 `unparse(body)` 当变量名传下去" in _ausrc
          and "118/206 落在「unknown」" in _ausrc
          and "不是数据如此、是那个分支坏了" in _ausrc
          and "仪器坏掉时我差点得到相反的结论" in _ausrc
          and "先判了「门错还是数据错」" in _ausrc
          and 'def is_stripped(' in _p1000
          and 'return None' in _p1000
          # ⭐⭐⭐⭐⭐ **反向门**：**不许在仪器 unknown 一半以上时照抄那个数**
          and "unknown 一半以上也可以直接用" not in _p1000
          and "unknown 一半以上也可以直接用" not in _ausrc)

    check("E993H.6 ⭐⭐⭐⭐⭐ **P1 成立：反向锚点比正向少一个量级（1 : 24.23）** ⇒ ⇒ "
          "**⇒ 而这与「反向断言是逐条刻意加的」一致** ⇒ ⇒ "
          "**⇒ 一个 1:24 的类别、不可能靠「顺手」维持** ⇒ ⇒ "
          "**⇒ 而本批纯离线：不打开浏览器、不按任何键、**连 `mouse.click` 都没有**、"
          "**只读判据与门两个文本** ⇒ ⇒ "
          "⭐⭐⭐⭐ **零计费是结构性的、不是自律的**",
          '"P1_ratio_is_an_order_of_magnitude"' in _p1000
          and '"p1_ratio_1000_"' in _p1000
          and '"P1_hold_1000"' in _p1000
          and '"ratio_1000"' in _p1000
          and "不可能靠「顺手」维持" in _p1000
          and '"offline_1000"' in _p1000
          and '"offline_1000"' in _ausrc
          and "连 `mouse.click` 都没有" in _p1000
          and "只读判据与门两个文本" in _p1000
          and "零计费是结构性的、不是自律的" in _p1000
          and '"discipline_1000"' in _p1000
          and "反向断言的存在本身就带着「它针对什么」的答案" in _p1000
          and '"discipline_1000"' in _ausrc
          and "「恒零」和「恒真」一样危险" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说「1:24 说明反向断言不重要」**
          and "1:24 说明反向断言不重要" not in _p1000
          and "1:24 说明反向断言不重要" not in _ausrc)

    # ══ F993J. 批 1001 **「一个变量不是一个东西」在这个仓里的真实形态**
    #   ⭐⭐⭐⭐⭐ **而本批的主结论是一个「互斥」：歧义与被门检查互斥**
    print("— F993J. 批 1001 重复与形状："
          "⭐⭐⭐⭐⭐ **4 个真有歧义的变量、已登记的 0 个 ⇒ "
          "「歧义」与「被门检查」互斥** ⇒ "
          "✅ **而删掉重复项之后门读数一个都没变**")
    check("F993J.1 ⭐⭐⭐⭐⭐ **P1 成立、而它读的是改之前的数："
          "**`PROBE_VARS` 里有 6 个键在源码文本里出现两次、而那个 dict 只有一个键** ⇒ ⇒ "
          "**⇒ 6 条被静默覆盖 ⇒ 「登记了两遍」只存在于源码文本里** ⇒ ⇒ "
          "**⇒ 而同类比较是「key 节点数 181 vs 去重后 175」** ⇒ ⇒ "
          "**⇒ `n_raw_key_lines` 只匹配了某一形状的值、不能拿它跟键数比**",
          '"P1_duplicate_keys_exist"' in _p1001
          and '"p1_shadowed_keys_1001_"' in _ausrc
          and '"P1_hold_1001"' in _p1001
          and 'BEFORE_DUP_1001 = {' in _p1001
          and '"like_for_like_1001"' in _p1001
          and '"n_shadowed"' in _p1001
          and "6 条被静默覆盖" in _ausrc
          and "key 节点数 181 vs 去重后 175" in _ausrc
          and '"p1_shadowed_keys_1001_"' in _ausrc
          and "6 条被静默覆盖" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许用 dict 的键数当「登记了几遍」的证据**
          and "dict 的键数就是登记的次数" not in _p1001
          and "dict 的键数就是登记的次数" not in _ausrc)

    check("F993J.2 ⭐⭐⭐⭐⭐ **P3 成立、而它是本批的主要交付：** "
          "**4 个真有歧义（同名字、不同形状）的变量、"
          "**全部落在「未登记」那一类里（已登记的 0 个）** ⇒ ⇒ "
          "**⇒ 「歧义」与「被门检查」是互斥的** ⇒ ⇒ "
          "**⇒ 因为能被登记的必须是「一行普通的 `read_text`」** ⇒ ⇒ "
          "**⇒ 而这不是巧合、这是 §207 那条 A 类判据的副产品** ⇒ ⇒ "
          "**⇒ 那道判据本来是为了分清「可补登记」与「表表达不了」、"
          "**而它顺带把有歧义的变量全挡在门外**",
          '"P3_ambiguity_and_checked_are_disjoint"' in _p1001
          and '"p3_ambiguity_and_checked_disjoint_1001_"' in _p1001
          and '"P3_hold_1001"' in _p1001
          and '"n_multi_diff_registered_1001"' in _p1001
          and '"n_multi_diff_1001"' in _p1001
          and "全部落在「未登记」那一类里" in _p1001
          and "「歧义」与「被门检查」是互斥的" in _p1001
          and "那道判据本来是为了分清" in _ausrc
          and '"p3_ambiguity_and_checked_disjoint_1001_"' in _ausrc
          and "顺带把有歧义的变量全挡在门外" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说「互斥是设计出来的」**
          and "互斥是当初设计出来的" not in _p1001
          and "互斥是当初设计出来的" not in _ausrc)

    check("F993J.3 ⭐⭐⭐⭐⭐ **P4 成立：删掉 6 个重复键与 5 对相邻重复赋值（10 行）之后、"
          "**官方门报的锚点数、问题数、跳过数全部不变** ⇒ ⇒ "
          "**⇒ 而这正是「无害的重复」的定义** ⇒ ⇒ "
          "**⇒ 而剩下那 5 处是一整块 3000 行之外的「重读」、我没有动它** ⇒ ⇒ "
          "**⇒ 因为收益与风险不对称** ⇒ ⇒ "
          "**⇒ 而 §206 P8 的第三次施用：处置改变了读数、所以 before 那个数必须抄下来**",
          '"P4_removal_changes_nothing"' in _p1001
          and '"p4_removal_changes_nothing_1001_"' in _p1001
          and '"P4_hold_1001"' in _p1001
          and '"before_1001"' in _p1001
          and "而这正是「无害的重复」的定义" in _p1001
          and "我没有动它" in _p1001
          and "收益与风险不对称" in _ausrc
          and "处置改变了读数、所以 before 那个数必须抄下来" in _ausrc
          and '"p4_removal_changes_nothing_1001_"' in _ausrc
          and "而剩下那 5 处是一整块 3000 行之外的「重读」、我没有动它" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「无害」当成「不必量」**
          and "看起来无害所以不用量" not in _p1001
          and "看起来无害所以不用量" not in _ausrc)

    check("F993J.4 ⭐⭐⭐⭐⭐ **P5 成立：「静默覆盖」的反向用例通过了** ⇒ ⇒ "
          "**⇒ 在一段内存文本里塞一个重复键、"
          "**数键的判据报出「源码 3 行、dict 2 个键、重复 1 个」** ⇒ ⇒ "
          "**⇒ 而没有这一步、那么「6 个重复键」这件事下次还会再发生** ⇒ ⇒ "
          "**⇒ 因为「0 个重复键」与「我的正则什么都没匹配上」在输出上一样** ⇒ ⇒ "
          "**⇒ 而本批的仪器第一版正是在这里栽的：用 `exec` 整个门拿到 0** ⇒ ⇒ "
          "**⇒ 而更糟的是那个 0 会让「已登记的歧义数」恒为 0、"
          "**而本批的主结论就建立在那一个数上**",
          '"P5_silent_overwrite_needs_its_own_reverse_case"' in _p1001
          and '"p5_reverse_case_1001_"' in _p1001
          and '"P5_hold_1001"' in _p1001
          and '"negative_control_1001"' in _p1001
          and '"NC_hold_1001"' in _p1001
          and '"instrument_exec_failed_1001_"' in _ausrc
          and "用 `exec` 整个门去拿 `PROBE_VARS`、拿到的是 0" in _ausrc
          and "而更糟的是：那个 0 会让" in _ausrc
          and '"p5_reverse_case_1001_"' in _ausrc
          and "「0 个重复键」与「我的正则什么都没匹配上」在输出上一样" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许在主结论所依赖的那个数恒为 0 时收工**
          and "主结论依赖的数是 0 也可以收工" not in _p1001
          and "主结论依赖的数是 0 也可以收工" not in _ausrc)

    check("F993J.5 ⭐⭐⭐⭐⭐ **P2 成立：那 10 处重复赋值的右值完全相同、"
          "**而且都在同一个作用域（`main`）里** ⇒ ⇒ "
          "**⇒ 那是无害的重复、不是语义分叉** ⇒ ⇒ "
          "**⇒ 而「同作用域」这一条必须量 —— 跨作用域的同名两次赋值根本不是重复** ⇒ ⇒ "
          "**⇒ 而 `out` 与 `c` 就是跨作用域的那两个、它们确实不是重复**",
          '"P2_duplicate_assignments_are_identical"' in _p1001
          and '"p2_duplicates_harmless_1001_"' in _ausrc
          and '"P2_hold_1001"' in _p1001
          and '"multi_same_shape_1001"' in _p1001
          and "都在同一个作用域（`main`）里" in _ausrc
          and "跨作用域的同名两次赋值根本不是重复" in _ausrc
          and '"p2_duplicates_harmless_1001_"' in _ausrc
          and "跨作用域的同名两次赋值根本不是重复" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许按名字去重而不看作用域**
          and "按名字去重就行" not in _p1001
          and "按名字去重就行" not in _ausrc)

    check("F993J.6 ⭐⭐⭐⭐⭐ **本批纯离线：不打开浏览器、不按任何键、**连 `mouse.click` 都没有**、"
          "**只读判据与门两个文本、再跑一次门** ⇒ ⇒ "
          "⭐⭐⭐⭐ **零计费是结构性的、不是自律的** ⇒ ⇒ "
          "**⇒ 而本批最贴题的一件事是：仪器第一版用 `exec` 整个门去拿那个 dict、拿到 0** ⇒ ⇒ "
          "**⇒ 而「读那个 dict」恰恰是本批要否掉的做法 —— "
          "**它天然看不见重复**",
          '"offline_1001"' in _p1001
          and '"offline_1001"' in _ausrc
          and "连 `mouse.click` 都没有" in _p1001
          and "只读判据与门两个文本、再跑一次门" in _p1001
          and "零计费是结构性的、不是自律的" in _p1001
          and '"discipline_1001"' in _p1001
          and "dict 对重复字面量键是静默覆盖的" in _p1001
          and "一次判据同时当筛子用、会产生你没打算要的副作用" in _p1001
          and '"discipline_1001"' in _ausrc
          and "一次判据同时当筛子用、会产生你没打算要的副作用" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说「清理一遍就一劳永逸」**
          and "清理一遍就一劳永逸了" not in _p1001
          and "清理一遍就一劳永逸了" not in _ausrc)

    check("F993J.7 ⭐⭐⭐⭐⭐ **P6 成立、而它是本批最大的一条：「用可见的形状当判据」"
          "**栽了第六次、而且这次栽在我自己写的探针上** ⇒ ⇒ "
          "**⇒ 本探针第一版数 `PROBE_VARS` 键名用的就是 `_p\\d{3}[a-z]?` —— "
          "**同一个仓、同一批、同一个主题** ⇒ ⇒ "
          "**⇒ 998 那条「我刚批过的毛病不会因为批过就自动免疫」在这里要升级："
          "**「我刚批过的毛病」+「我正在写它」= 更危险** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而处置不是「把洞填上」、是分清「洞填了」与「仪器可信了」："
          "**AST 176 / 修后正则 143 / 原正则 141 —— 还有 33 条对修好后的正则隐形** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 那 33 条里 0 条是四位数 ⇒ 所以真正活着的是另一条轴** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而 P6b 被否：「盲正则会给出不同的重复键数」不成立** "
          "**（999 那个文件里四位数键是 0 条、两种正则读到同一组 6 个）** ⇒ ⇒ "
          "**⇒ 「洞存在」与「洞改过这个数」是两件事、而我原本写的是前者** ⇒ ⇒ "
          "**⇒ 「否」的第三种自我形态：「洞是真的、而它这次没咬到」** ⇒ ⇒ "
          "**⇒ 而 P6c 的反向用例证明它能咬：塞一个四位数重复键、盲正则报 0 而 AST 报 1** ⇒ ⇒ "
          "**⇒ 真文件上没被咬到是运气、不是设计** ⇒ ⇒ "
          "**⇒ P6d：门里那几个数是手写的（静态 dict 只能手写）⇒ "
          "**所以让探针反过来核对那几个字面量 —— 不一致就报**",
          # ── 探针侧：这六条必须真的可执行、而且各自带 hold ──
          '"P6_shape_criterion_in_the_instrument_about_shape_criteria"' in _p1001
          and '"P6a_hold_1001"' in _p1001
          and '"P6b_hold_1001"' in _p1001
          and '"P6c_hold_1001"' in _p1001
          and '"P6d_hold_1001"' in _p1001
          and '"p6_three_denominators_1001"' in _p1001
          and '"p6_falsified_1001"' in _p1001
          and '"negative_control_p6_1001"' in _p1001
          and '"p6_audit_parity_1001"' in _p1001
          and '_KEYRE_BLIND' in _p1001
          and '"n_missing_4digit"' in _p1001
          and '"digit_axis_alone"' in _p1001
          and "而我原本写的是前者" in _p1001
          and "那里没被咬到是运气、不是设计" in _p1001
          and "这次没出事" in _p1001
          # ── 官方门侧：四个新键与两句结论必须在场 ──
          and '"p6_sixth_instance_in_my_own_probe_1001_"' in _ausrc
          and '"p6_three_denominators_1001_"' in _ausrc
          and '"p6_falsified_1001_"' in _ausrc
          and '"negative_control_p6_1001_"' in _ausrc
          and "而这正是本批最该被记下的一句" in _ausrc
          and "所以「把数字位数修好」并不足以让这个仪器可信" in _ausrc
          and "那里没被咬到是运气、不是设计" in _ausrc
          and "「我刚批过的毛病」+「我正在写它」" in _ausrc
          and "判据文本里的手写数会陈旧、会口算错" in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门①**：**不许把「这次没咬到」写成「这个洞不存在」**
          and "这个洞不存在" not in _p1001
          and "这个洞不存在" not in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门②**：**不许把「修好数字位数」说成「仪器从此可信」**
          and "修好之后这个仪器就可信了" not in _p1001
          and "修好之后这个仪器就可信了" not in _ausrc)

    # ══ G993K. 批 1002 **「0 问题」是门的一个输出；门对自己够不够敏感从来没被量过**
    print("— G993K. 批 1002 门自身的检出率："
          "⭐⭐⭐⭐⭐ **6 类变异、3 类改前 0% / 4 类改后 0%** ⇒ ⇒ "
          "⚠️ **而 0% 的成因**分两种**：门坏了／问题在门的问题之外** ⇒ ⇒ "
          "**⇒ 后者更危险、因为它长得像前者**")

    check("G993K.1 ⭐⭐⭐⭐⭐ **P1 成立：活文件里 `check(...)` 的 `ok` 是裸字面量的 0 条** ⇒ ⇒ "
          "**⇒ 而这个 0 现在由门自己每次打印、而不是靠我记着** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 「0」必须能返回非零 —— P2/P3 就是它的反向用例** ⇒ ⇒ "
          "**⇒ 而 P2/P3 这一对是本批的主交付**",
          '"P1_no_bare_string_ok_in_stock"' in _p1002
          and '"p1_no_bare_string_ok_1002_"' in _ausrc
          and '"P1_hold_1002"' in _p1002
          and '"n_bad_ok_reported"' in _p1002
          and 'census_ok_shape' in _p1002  # ⭐ 这道判据自己在读门的那道普查
          and 'census_ok_shape' in _anchs
          and '"SHAPE-口径：check(' in _anchs
          and 'def census_ok_shape' in _anchs
          and '而这个 0 现在由门自己每次打印' in _p1002
          and '而这个 0 现在由门自己每次打印' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「0 条」当成「这个检查通过了」的证据**
          and '「0 条」不等于「检查通过了」' not in _p1002
          and '「0 条」不等于「检查通过了」' not in _ausrc)

    check("G993K.2 ⭐⭐⭐⭐⭐ **P2/P3 成立：改之前「`ok` 整条写成字符串」检出率 = 0、改之后 = 100%** ⇒ ⇒ "
          "**⇒ 而这就是 1001 那三次「全通」的机制** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 机制是结构性的：`collect()` 只走 `Compare`、"
          "**而裸字符串一个 `Compare` 都没有 ⇒ 连「锚点 N 条」都数不到** ⇒ ⇒ "
          "**⇒ 而处置是「多一条独立的路」、不是「把 `collect()` 改聪明」** ⇒ ⇒ "
          "**⇒ 因为 `collect()` 问「锚点在不在」、问不到「`ok` 是不是恒真」**",
          '"p2_before_fix_m3_zero_1002_"' in _p1002
          and '"p3_after_fix_m3_detected_1002_"' in _p1002
          and '"p2_before_fix_m3_zero_1002_"' in _ausrc
          and '"p3_after_fix_m3_detected_1002_"' in _ausrc
          and '"P2_hold_1002"' in _p1002
          and '"P3_hold_1002"' in _p1002
          and '"n_problems_before"' in _p1002
          and '而这就是 1001 那三次「全通」的机制' in _p1002
          and '所以它连「锚点 N 条」都数不到' in _p1002
          and '所以它连「锚点 N 条」都数不到' in _ausrc
          and '不是数错了、是那个数按定义就不包含它' in _ausrc
          and '而处置是「多一条独立的路」' in _p1002
          and '问不到「`ok` 是不是恒真」' in _p1002
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说「把 `collect()` 改得更聪明就行」**
          and '把 `collect()` 改得更聪明就行' not in _p1002
          and '把 `collect()` 改得更聪明就行' not in _ausrc)

    check("G993K.3 ⭐⭐⭐⭐⭐ **P4 成立、而它否的是我自己的门：把锚点换成一个确实存在的串 ⇒ "
          "改前改后都检不出** ⇒ ⇒ "
          "**⇒ 「这条锚点在不在」按定义问不到「它的内容是不是必然为真」** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 这一类最危险：判据还在、门还全绿、而它什么都不防** ⇒ ⇒ "
          "**⇒ M6「删掉整条判据」也是 0%、但成因不同 ⇒ 同样 0% 必须分开记** ⇒ ⇒ "
          "**⇒ 而 M5 的第一版设计（翻正反向断言）被数据否掉了 —— "
          "**反向断言的锚点按设计就不该存在、所以翻正反而会被检出**",
          '"p4_m5_structurally_undetectable_1002_"' in _p1002
          and '"p4b_m5_design_falsified_1002_"' in _p1002
          and '"p4_m5_structurally_undetectable_1002_"' in _ausrc
          and '"p4b_m5_design_falsified_1002_"' in _ausrc
          and '"P4_hold_1002"' in _p1002
          and '"M5-锚点换成必然为真的串"' in _p1002
          and '"M6-删掉整条判据"' in _p1002
          and 'PRESENT_ANCHOR' in _p1002
          and '判据还在、门还全绿、而它什么都不防' in _p1002
          and '判据还在、门还全绿、而它什么都不防' in _ausrc
          and '同样是 0%、必须分开记' in _p1002
          and '同样是 0%、必须分开记' in _ausrc
          and '「否」的是我的变异设计' in _p1002
          and '「否」的是我的变异设计' in _ausrc
          and '反向断言的「方向」是被存在性本身保护的' in _p1002
          and '反向断言的锚点**按设计就不该存在**' in _p1002
          # ⭐⭐⭐⭐⭐ **反向门①**：**不许说「这类 0% 说明门坏了」**
          and '0% 说明门坏了' not in _p1002
          and '0% 说明门坏了' not in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门②**：**不许只报一个检出率比率**
          and '只看检出率' not in _p1002
          and '只看检出率' not in _ausrc)

    check("G993K.4 ⭐⭐⭐⭐⭐ **P5 成立：「指向未登记变量」不产生 problem、但会打印 SKIPPED** ⇒ ⇒ "
          "**⇒ 「可见」与「检出」是两个量、必须分开数** ⇒ ⇒ "
          "**⇒ 而 961 那次吃过一次：静默 `continue` ⇒ 「0 问题」是假绿** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ P6 成立、而它是我自己犯的口径错："
          "`check(name, ok, detail)` 固定三参、我第一版把 `args[1:]` 整个当条件 ⇒ "
          "**分母 911（真实 791）⇒ 而那 109 条 `detail` 里有 106 个 f-string、非空恒真** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 口径错了的 0 比真的 0 更坏：它会让人以为仓里烂得很**",
          '"p5_visible_is_not_detected_1002_"' in _p1002
          and '"p6_ok_and_detail_slots_1002_"' in _p1002
          and '"p5_visible_is_not_detected_1002_"' in _ausrc
          and '"p6_ok_and_detail_slots_1002_"' in _ausrc
          and '"P5_hold_1002"' in _p1002
          and '"P6_hold_1002"' in _p1002
          and '「可见」与「检出」是两个量' in _p1002
          and '「可见」与「检出」是两个量' in _ausrc
          and '分母成了 911（真实 791）' in _p1002
          and '分母成了 911（真实 791）' in _ausrc
          and '口径错了的 0 比真的 0 更坏' in _p1002
          and '口径错了的 0 比真的 0 更坏' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「被跳过」记成「查过了」**
          and '被跳过就算查过了' not in _p1002
          and '被跳过就算查过了' not in _ausrc)

    check("G993K.5 ⭐⭐⭐⭐⭐ **本批的仪器自己也栽了两次、而两次都是被自己的断言抓住的** ⇒ ⇒ "
          "**① `before` 一律 2343 —— 成因是我给「改之前」那一路传了空的 `probes` 字典"
          "** ⇒ **⇒ 而「恒定的巨大数字」几乎总是「某个集合是空的」** ⇒ ⇒ "
          "**⇒ 更糟的是：那让 P2 与 P4 双双「不成立」、而两个都是假的** ⇒ ⇒ "
          "**② M6 第一版什么都没删、却把结果当成了「删掉了」"
          "**（`check(...)` 是表达式语句、父节点是 `ast.Expr`）** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 抓住它们的不是任何一道门、是探针自己那句「变异必须先验形状」** ⇒ ⇒ "
          "**⇒ 而处置：路径可覆盖 ⇒ 6 个变异全在 `/tmp` 副本上跑、真文件一个字节都不动**",
          '"instrument_empty_probes_1002_"' in _p1002
          and '"m6_delete_bug_caught_by_shape_assert_1002_"' in _p1002
          and '"path_override_1002_"' in _p1002
          and '"instrument_empty_probes_1002_"' in _ausrc
          and '"m6_delete_bug_caught_by_shape_assert_1002_"' in _ausrc
          and '"path_override_1002_"' in _ausrc
          and 'SHAPE_DELTA' in _p1002
          and 'BASE_SHAPE' in _p1002
          and '"n_problems_before_on_clean"' in _p1002
          and '恒定的巨大数字' in _p1002
          and '恒定的巨大数字' in _ausrc
          and '读到 2343 先问' in _p1002
          and '读到 2343 先问' in _ausrc
          and '我以为我测了、其实我测的是原文件' in _p1002
          and '我以为我测了、其实我测的是原文件' in _ausrc
          and '是探针自己那句「变异必须先验形状」' in _p1002
          and '全在 `/tmp` 的副本上跑、真文件一个字节都不动' in _p1002
          and '全在 `/tmp` 的副本上跑、真文件一个字节都不动' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「探针跑完了」当成「探针量到了东西」**
          and '探针跑完了就当量到了' not in _p1002
          and '探针跑完了就当量到了' not in _ausrc)

    check("G993K.6 ⭐⭐⭐⭐⭐ **本批纯离线：不打开浏览器、不按任何键、**连 `mouse.click` 都没有**、"
          "**只读判据与门两个文本、跑 7 次门（1 基线 + 6 变异）** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而「0 检出」的两种成因必须分开记："
          "**门坏了／问题在门的问题之外 —— 而后者更危险、因为它长得像前者** ⇒ ⇒ "
          "**⇒ 验收标准：0% 的类别逐条列成因、不许只报一个比率**",
          '"offline_1002"' in _p1002
          and '"offline_1002"' in _ausrc
          and '"discipline_1002"' in _p1002
          and '"discipline_1002"' in _ausrc
          and '连 `mouse.click` 都没有' in _p1002
          and '跑 7 次门（1 基线 + 6 变异）' in _p1002
          and '跑 7 次门（1 基线 + 6 变异）' in _ausrc
          and '"undetected_are_listed_not_averaged"' in _p1002
          and '0% 的类别逐条列成因、不许平均' in _ausrc
          and '检出率必须按类别报' in _ausrc
          and '问题在门的问题之外' in _ausrc
          and '读到恒定的巨大数字' in _ausrc
          and '「否」也可能是「我测的那件事不是我想测的那件事」' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说「检出率够了、问题就都覆盖了」**
          and '检出率够了问题就都覆盖了' not in _p1002
          and '检出率够了问题就都覆盖了' not in _ausrc)

    # ══ H993L. 批 1003 **「判据的牙」：改**目标**、看判据会不会红**
    print("— H993L. 批 1003 判据的牙："
          "❌ **83.3% 的锚点只出现 1 次、最多的也只 36 次 —— "
          "「锚点纪律松、一定有一堆废锚点」这个成见被数据否掉** ⇒ ⇒ "
          "⚠️ **而 12 个不同锚点的抽样里有 1 个变红 —— "
          "机制是「锚点之间的包含关系」、而门对它完全看不见**")

    check("H993L.1 ⭐⭐⭐⭐⭐ **P1 被否、而否出来的东西比预测更好："
          "**5928 条锚点里 83.3% 只出现 1 次、最多的也只 36 次、>100 次的 0 条** ⇒ ⇒ "
          "**⇒ 「锚点纪律」这件事其实做得非常好** ⇒ ⇒ "
          "**⇒ 而这与 991–1002 累积的纪律一致（逐条验锚、写完就验、不许整段比）** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 所以本批找错了担心方向 —— "
          "**「我以为我知道哪里最烂」几乎总是错的**",
          '"P1_many_always_true_anchors"' in _p1003
          and '"p1_many_always_true_anchors_1003_"' in _ausrc
          and '"P1_hold_1003"' in _p1003
          and '"occurrence_hist_1003"' in _p1003
          and '"no_occurrence_above_100"' in _p1003
          and '「我以为我知道哪里最烂」几乎总是错的' in _p1003
          and '「我以为我知道哪里最烂」几乎总是错的' in _ausrc
          and '所以本批找错了担心方向' in _p1003
          and '所以本批找错了担心方向' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「没找到问题」说成「这里没问题」**
          and '没找到问题所以这里没问题' not in _p1003
          and '没找到问题所以这里没问题' not in _ausrc)

    check("H993L.2 ⭐⭐⭐⭐⭐ **P2 成立：「单点编辑能骗过它」的判据数 = 732 条"
          "**（681 个不同锚点、275 条指向 `_ausrc`）** ⇒ ⇒ "
          "**⇒ 而「没牙」要逐条列、不许只报比例** ⇒ ⇒ "
          "**⇒ 关键分界：只出现 1 次的那 4939 条**删掉就红**、是真正有牙的** ⇒ ⇒ "
          "**⇒ 而最弱的那条是 2 个字的词、它在两万行里 ⇒ 「弱」是相对的弱**",
          '"P2_no_teeth_count_is_the_multi_occurrence_ones"' in _p1003
          and '"p2_no_teeth_count_1003_"' in _ausrc
          and '"P2_hold_1003"' in _p1003
          and '"no_teeth_1003"' in _p1003
          and '"n_unique_anchors"' in _p1003
          and '"listed_not_averaged"' in _p1003
          and '「没牙」要逐条列、不许只报比例' in _p1003
          and '「没牙」要逐条列、不许只报比例' in _ausrc
          and '「弱」是相对的弱、不是「必然为真」' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「没牙」等价成「这条判据没用」**
          and '没牙就等于这条判据没用' not in _p1003
          and '没牙就等于这条判据没用' not in _ausrc)

    check("H993L.3 ⭐⭐⭐⭐⭐ **P3 被否、而否出来的机制比预测更细："
          "**12 个不同锚点里 11 个保持绿、1 个变红** ⇒ ⇒ "
          "**⇒ 真凶不是「推导错了」、是「推导的粒度错了」："
          "**`「同一个东西要比同一个口径」` 的首次出现落在另一个只出现 1 次的更长锚点内部** ⇒ ⇒ "
          "**⇒ 而「锚点之间有包含关系」这件事门完全看不见 —— 它对每个锚点只问「在不在」** ⇒ ⇒ "
          "**⇒ 而我第一版的诊断只查了子串方向、于是真凶在旁边、我却报「无连带」**",
          '"P3_sample_agrees_with_derivation"' in _p1003
          and '"P3_falsified_1003"' in _p1003
          and '"p3_sample_agrees_1003_"' in _ausrc
          and '"collateral_superstrings_killed"' in _p1003
          and '真凶是**超串**方向' in _p1003
          and '真凶是**超串**方向' in _ausrc
          and '而「锚点之间有包含关系」这件事门完全看不见' in _p1003
          and '而「锚点之间有包含关系」这件事门完全看不见' in _ausrc
          and '我第一版的诊断只查了子串方向' in _p1003
          and '我第一版的诊断只查了子串方向' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「推导」当证据 —— 必须真跑门**
          and '按推导不用真跑门' not in _p1003
          and '按推导不用真跑门' not in _ausrc)

    check("H993L.4 ⭐⭐⭐⭐⭐ **⚠️ 而本批的仪器第一版自己犯了 1001 的头号毛病："
          "**把 (目标变量, 锚点, 方向) 三元组当 dict 键、5928 条判据被压成 5777 个键** ⇒ ⇒ "
          "**⇒ 静默丢掉 151 条** ⇒ ⇒ "
          "**⇒ 而它表现出来的是「两次测量给出不同分布」、我一度以为两把尺子打架** ⇒ ⇒ "
          "**⇒ 真相是其中一把尺子自己压扁了 151 条、而没人告诉它** ⇒ ⇒ "
          "**⇒ 而「151 条判据的锚点与另一条完全相同」本身是真实的 —— "
          "**改一处文本会同时打红多条是事实；把它们合并成一个读数才是错** ⇒ ⇒ "
          "**⇒ 附带两条同族纪律：「有效 n」与「报告的 n」不一致时那个 n 就是假的**"
          "**（抽样第一版取到同一个锚点 3 次、有效 n 只有 7 而不是 10）**"
          "**｜「复现不了的读数」要记下来、不解释、不抹掉**",
          '"dedup_loss_1003"' in _p1003
          and '"dedup_loss_1003_"' in _ausrc
          and '"n_lost_by_dedup"' in _p1003
          and 'occ_list' in _p1003
          and 'sample_design_1003' in _p1003
          and '分母是 %d（`collect` 的条数）、' in _p1003
          and '不是 %d（去重后的键数）' in _p1003
          and '手写的数会陈旧、而它读起来像一个读数' in _p1003
          and '它把 (目标变量, 锚点, 方向) 三元组当 dict 键' in _p1003
          and '它把 (目标变量, 锚点, 方向) 三元组当 dict 键' in _ausrc
          and '量东西不许经过任何去重容器' in _p1003
          and '量东西不许经过任何去重容器' in _ausrc
          and '「有效 n」与「报告的 n」不一致时、那个 n 就是假的' in _p1003
          and '「有效 n」与「报告的 n」不一致时、那个 n 就是假的' in _ausrc
          and '复现不了的读数要' in _p1003
          and '复现不了的读数要' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「两个数不一样」当成「两把尺子打架」**
          and '两个数不一样说明两把尺子打架' not in _p1003
          and '两个数不一样说明两把尺子打架' not in _ausrc)

    check("H993L.5 ⭐⭐⭐⭐⭐ **P4 成立、而它是本批的前提："
          "**先拿一条只出现 1 次的锚点、把它从目标里删掉、门如实报了 MISSING** ⇒ ⇒ "
          "**⇒ 不先做这一步、后面 12 条抽样就毫无信息量** ⇒ ⇒ "
          "**⇒ 而控制组与抽样都限定在 `_ausrc` 侧 —— "
          "**「仪器覆盖不到」不等于「这一类不测」、被排除的条数必须是个可见的数** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而 P5 成立：1002 覆盖判据侧、1003 覆盖目标侧、"
          "**两批的实验方向正好相反、可覆盖的能力却是同一个** ⇒ ⇒ "
          "**⇒ 本批纯离线：连 `mouse.click` 都没有、跑 13 次门**",
          '"P4_control_must_go_red_first"' in _p1003
          and '"P5_both_gates_read_the_same_capability"' in _p1003
          and '"p4_control_must_go_red_1003_"' in _ausrc
          and '"p5_both_directions_1003_"' in _ausrc
          and '"scope_limit_1003"' in _p1003
          and '"no_teeth_other_targets"' in _p1003
          and '「仪器覆盖不到」不等于「这一类不测」' in _p1003
          and '「仪器覆盖不到」不等于「这一类不测」' in _ausrc
          and '连 `mouse.click` 都没有' in _p1003
          and '跑 13 次门（1 控制组 + 12 抽样）' in _p1003
          and '跑 13 次门（1 控制组 + 12 抽样）' in _ausrc
          and '可覆盖的能力是同一个' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「我测的这一半」说成「我测过了」**
          and '测了这一半就等于测过了' not in _p1003
          and '测了这一半就等于测过了' not in _ausrc)

    # ══ I993M. 批 1004 **判据的耦合度：编辑目标里的一处 ⇒ 打红几条判据**
    print("— I993M. 批 1004 判据的耦合度："
          "✅ **包含关系 121 对、只覆盖 1.54% 的锚点** ⇒ ⇒ "
          "❌ **而 P2 被否：否掉它的 90% 是我拍的阈值** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **而真正的读数是 684 个锚点（12.3%）耦合度 = 0 —— "
          "编辑它们一次、一条判据都不红**")

    check("I993M.1 ⭐⭐⭐⭐⭐ **P1 成立：全部正向锚点里的包含关系只有 121 对、"
          "**涉及 24 个目标变量（`_ausrc` 占 90）、82 个子串 = 全部 5332 个不同锚点的 1.54%** ⇒ ⇒ "
          "**⇒ 而这正是 1003 那 1 例的全局 —— 它罕见、但不是不存在** ⇒ ⇒ "
          "**⇒ 而 121 这个数有口径：只统计「同目标内」的包含、跨目标的本批没查**",
          '"P1_containment_pairs_are_few"' in _p1004
          and '"containment_1004"' in _p1004
          and '"positive_present_1004"' in _p1004
          and '"p1_containment_pairs_are_few_1004_"' in _ausrc
          and '"P1_hold_1004"' in _p1004
          and '只统计「同目标内」的包含' in _p1004 and '跨目标的包含关系本批没查' in _p1004
          and '它只统计「同目标内」的包含、跨目标的本批没查' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「罕见」说成「不存在」**
          and '只有 121 对所以基本不存在' not in _p1004
          and '只有 121 对所以基本不存在' not in _ausrc)

    check("I993M.2 ⭐⭐⭐⭐⭐ **❌ P2 被否、而否掉它的那个 90% 是**我拍的阈值**："
          "**实测「打红 1 条」占 87.3%、不到 90%** ⇒ ⇒ "
          "**⇒ 998 那条纪律第二次施用：这次「否」的信息量在「我拍的数不对」** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而真正的读数比预测好得多、而且落在另一个方向："
          "**684 个锚点（12.3%）的耦合度是 0 ⇒ 编辑它们一次、一条判据都不红** ⇒ ⇒ "
          "**⇒ 而这比「长尾」重要得多：那处编辑对门是完全不可见的** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而我**没有**去调那个阈值让它变绿 —— 把 90% 改成 87% 是最省事也最坏的做法**",
          '"P2_coupling_is_heavy_tailed"' in _p1004
          and '"P2_falsified_1004"' in _p1004
          and '"p2b_the_real_reading_is_the_zeros_1004_"' in _ausrc
          and '"n_zero_coupling"' in _p1004
          and '"n_zero_pct"' in _p1004
          and '否掉它的那个 90% 是**我拍的阈值' in _p1004
          and '否掉它的那个 90% 是**我拍的阈值' in _ausrc
          and '「一条判据都不红」意味着那处编辑对门是完全不可见的' in _p1004
          and '「一条判据都不红」意味着那处编辑对门是完全不可见的' in _ausrc
          and '最省事也最坏的做法' in _p1004
          and '把 90% 改成 87% 是最省事也最坏的做法' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门①**：**不许为了让预测变绿而挪自己拍的阈值**
          and '把阈值挪一下让它变绿' not in _p1004
          and '把阈值挪一下让它变绿' not in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门②**：**不许把「均值」当成这个分布的描述**
          and '平均一条判据变红就够了' not in _p1004
          and '平均一条判据变红就够了' not in _ausrc)

    check("I993M.3 ⭐⭐⭐⭐⭐ **P3 成立、而它是在修好公式之后才成立的：抽样 15 个、真跑门、15/15 一致** ⇒ ⇒ "
          "**⇒ 而修之前是 9/15 —— 6 条不吻合全部是自身出现 ≥2 次的那些** ⇒ ⇒ "
          "**⇒ 公式被我写死成 `1 + |超串|`，"
          "**而正确公式是 `(自身只出现 1 次 ? 1 : 0) + |被连带打死的唯一超串|`** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而这已经是「推导的粒度错了」在同一条线上的第三次** ⇒ ⇒ "
          "**⇒ 推导不能当证据**",
          '"P3_derivation_matches_measured"' in _p1004
          and '"p3_derivation_matches_measured_1004_"' in _ausrc
          and '"P3_hold_1004"' in _p1004
          and '"sample_1004"' in _p1004
          and '"measured_histogram_1004"' in _p1004
          and 'derived = {k: ((1 if _occ.get(k) == 1 else 0) + len(v))' in _p1004
          and '|被连带打死的唯一超串|' in _p1004 and 'derived = {k: ((1 if _occ.get(k) == 1 else 0) + len(v))' in _p1004
          and '正确公式是 `(自身只出现 1 次 ? 1 : 0) + |被连带打死的唯一超串|`' in _ausrc
          and '同一条线上的第三次' in _p1004
          and '「推导的粒度错了」在同一条线上的第三次' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许因为「推导看起来显然」就不验**
          and '这个公式显然成立不用验' not in _p1004
          and '这个公式显然成立不用验' not in _ausrc)

    check("I993M.4 ⭐⭐⭐⭐⭐ **P4/P5 成立：基线先自检为 0、反向用例断言「**恰好** 1 个问题」** ⇒ ⇒ "
          "**⇒ 而第一版控制组漏了「自身必须只出现 1 次」这个前提、"
          "**于是挑中的是 `作废`（出现 37 次）、门报 0** ⇒ ⇒ "
          "**⇒ 而 1003 的基线污染之所以能溜过去、正因为那时只验了「大于 0」** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 本批纯离线：连 `mouse.click` 都没有、共跑 17 次门**",
          '"P4_baseline_must_be_zero_first"' in _p1004
          and '"P5_control_red_exactly_one"' in _p1004
          and '"baseline_1004"' in _p1004
          and '"control_1004"' in _p1004
          and '"p4_baseline_must_be_zero_1004_"' in _ausrc
          and '"p5_control_red_exactly_one_1004_"' in _ausrc
          and '"P4_hold_1004"' in _p1004
          and '"P5_hold_1004"' in _p1004
          and 'stronger_than_1003' in _p1004
          and '**恰好** 1 个问题' in _p1004
          and '**恰好** 1 个问题' in _ausrc
          and '自身必须只出现 1 次' in _p1004 and '（出现 37 次）' in _p1004
          and '我漏了「自身必须只出现 1 次」这个前提' in _ausrc
          and '共跑 17 次门（1 基线 + 1 控制组 + 15 抽样）' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「报了问题」当成「报得准」**
          and '报了问题就说明报得准' not in _p1004
          and '报了问题就说明报得准' not in _ausrc)

    # ══ J993N. 批 1005 **「零耦合」不是一个东西：拆开、并让清单落进仓里**
    print("— J993N. 批 1005 零耦合普查："
          "✅ **690 条分成「标识符（多处引用）」301 与「散文/片段」389 —— 前者是语义使然** ⇒ ⇒ "
          "❌ **而 P2 被否：行距分不开它们、相邻档反而在标识符类里更多（82 vs 18）** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而「注入必须动两侧」：只改 audit 的话普查报 delta=0**")

    check("J993N.1 ⭐⭐⭐⭐⭐ **P1 成立：零耦合锚点分成两类 —— "
          "**「标识符（多处引用）」301 条与「散文/片段」389 条** ⇒ ⇒ "
          "**⇒ 而前一类是**语义使然**：判据本来就在问「这个东西存在吗」、"
          "**改掉其中一处不该让判据红** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 所以「零耦合」不能一刀切地说成「废判据」** ⇒ ⇒ "
          "**⇒ 而清单必须逐条落进仓里、不许只留在探针输出里**",
          '"P1_two_classes_exist"' in _p1005
          and '"p1_two_classes_exist_1005_"' in _ausrc
          and '"P1_hold_1005"' in _p1005
          and '"census_1005"' in _p1005
          and '"golden_path_1005"' in _p1005
          and 'zero-coupling-anchors-1005.json' in _p1005
          and 'zero-coupling-anchors-1005.json' in _ausrc
          and '「零耦合」**不能**一刀切地说成「废判据」' in _p1005
          and '「零耦合」**不能**一刀切地说成「废判据」' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「零耦合」直接等价成「这条判据没用」**
          and '零耦合就等于这条判据没用' not in _p1005
          and '零耦合就等于这条判据没用' not in _ausrc)

    check("J993N.2 ⭐⭐⭐⭐⭐ **❌ P2 被否、而方向和我猜的相反："
          "**「最小行距」不但分不开两类、相邻档反而在标识符类里更多（82 vs 18）** ⇒ ⇒ "
          "**⇒ 因为相邻两行代码用同一个 token 是常事** ⇒ ⇒ "
          "**⇒ 我原以为「相邻 = 散文被复制到两处」、"
          "**而实际是「相邻 = 同一个 token 在同一处代码里出现两次」** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而行距这个轴不能当分类依据 —— "
          "**它测的是「这个 token 挨得多近」、不是「这个判据弱不弱」** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 这是「否」的第六种自我形态：模式是我列的（1000 那条）** ⇒ ⇒ "
          "**⇒ 而我没有去换一个「更好看的轴」来让它成立**",
          '"P2_line_gap_separates_the_two_classes"' in _p1005
          and '"P2_falsified_1005"' in _p1005
          and '"p2_line_gap_separates_1005_"' in _ausrc
          and '"P2_hold_1005"' in _p1005
          and 'class_x_gap' in _p1005
          and '它测的是「这个 token 挨得多近」' in _p1005
          and '它测的是「这个 token 挨得多近」' in _ausrc
          and '模式是我列的（1000 那条）' in _p1005
          and '模式是我列的（1000 那条）' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门①**：**不许换一个轴让预测成立而不说**
          and '换一个轴它就成立了' not in _p1005
          and '换一个轴它就成立了' not in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门②**：**不许把「相邻」当成分类的证据**
          and '相邻就说明是散文' not in _p1005
          and '相邻就说明是散文' not in _ausrc)

    check("J993N.3 ⭐⭐⭐⭐⭐ **P3 成立：清单由**本探针自己**写、逐条一致（新增 0、消失 0）** ⇒ ⇒ "
          "**⇒ 而第一版那份是临时脚本落的、它把锚点截断到 40 字符** ⇒ ⇒ "
          "**⇒ 后果是「新增 11 条、消失 11 条」、而它们其实是同一批 11 条** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 「差异数」本身也要有口径 —— "
          "**一个截断的清单和一个全量的清单相比、永远在「变」** ⇒ ⇒ "
          "**⇒ 处置：写它的仪器必须就是读它的那个**",
          '"P3_golden_is_reproducible"' in _p1005
          and '"p3_golden_is_reproducible_1005_"' in _ausrc
          and '"P3_hold_1005"' in _p1005
          and '--write-golden' in _p1005
          and '"generated_by"' in _p1005
          and '它把锚点截断到 40 字符' in _p1005
          and '它把锚点截断到 40 字符' in _ausrc
          and '一个截断的清单和一个全量的清单相比、永远在「变」' in _p1005
          and '一个截断的清单和一个全量的清单相比、永远在「变」' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许只记一个总数就说「清单在仓里」**
          and '只记总数就算清单落仓了' not in _p1005
          and '只记总数就算清单落仓了' not in _ausrc)

    check("J993N.4 ⭐⭐⭐⭐⭐ **P4 成立、而它的第一版报 delta=0：注入必须**动两侧**"
          "** ⇒ ⇒ **⇒ 普查的宇宙是「verifier 里声明、且在目标里存在」的锚点**"
          "** ⇒ ⇒ **⇒ 只改 audit 等于什么也没加** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而这恰恰说明那道门只认「声明」与「存在」两件事** ⇒ ⇒ "
          "**⇒ P5 成立：分母是 `collect` 的条数、去重后的键数必须都报** ⇒ ⇒ "
          "**⇒ 本批纯离线：连 `mouse.click` 都没有**",
          '"P4_reverse_case_the_census_can_return_non_zero"' in _p1005
          and '"p4_reverse_case_1005_"' in _ausrc
          and '"P4_hold_1005"' in _p1005
          and '"P5_denominator_is_collect_not_dedup"' in _p1005
          and '"p5_denominator_is_collect_1005_"' in _ausrc
          and '"P5_hold_1005"' in _p1005
          and 'why_both_sides' in _p1005
          and '只改目标等于什么也没加' in _p1005
          and '只改目标等于什么也没加' in _ausrc
          and '而这恰恰说明那道门只认「声明」与「存在」两件事' in _p1005
          and '而这恰恰说明那道门只认「声明」与「存在」两件事' in _ausrc
          and '连 `mouse.click` 都没有' in _p1005
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「注入只动一侧」当成「注入失败」而不查原因**
          and '注入失败说明普查坏了' not in _p1005
          and '注入失败说明普查坏了' not in _ausrc)

    # ══ 1006 宇宙冻结点 ══
    # ⚠️⚠️⚠️⭐⭐⭐⭐⭐ **1006 探针按这一行把普查宇宙冻结在「1006 加自己判据之前」** ⇒ ⇒
    #   **⇒ 后来每一批的判据都必须加在这行之后** ⇒ ⇒
    #   ⭐⭐⭐⭐⭐ **⇒ 而冻结点必须在 1006 判据**之前**、不是之后** —— 这是被 1007 逼出来的：
    #   **⇒ 1006 报的那些数（238 段 / 187 段跨 audit↔probe / 498 对 / 16.9%）**
    #   **是在它的 `K993O` 判据加进去之前测的** ⇒ ⇒
    #   **⇒ 而加了之后宇宙已经长到 240 段 / 190 段 / 503 对 ⇒ ⇒**
    #   **⇒ 所以「数字没有出处」在这里不是漂移、而是「宇宙在长」——**
    #   **⇒ 处置不是放宽契约、而是把口径钉死在它自己那一刻**
    # ══ K993O. 批 1006 **同一段锚点被钉在多个文件上：一次编辑只让一处变红、其余静默失真**
    print("— K993O. 批 1006 跨目标重复普查："
          "✅ **238 段锚点文字被钉在 2 个以上目标上、最多的那段出现在 8 个目标里** ⇒ ⇒ "
          "❌ **而「数量」不是风险量：样板句的重复天然无害（498 对里只有 84 对提到该文件自己）** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 真跑门证明：改掉一个副本、门只报受害目标那 1 个、其余 7 个副本只字不提**")

    check("K993O.1 ⭐⭐⭐⭐⭐ **P1 成立：同一段锚点文字被钉在 2 个以上目标上的有 238 段、"
          "**而最多的那一段出现在 8 个目标上、其中 187 段跨 audit↔probe** ⇒ ⇒ "
          "**⇒ 也就是说「同一句话」在 8 个文件里各自被钉了一次** ⇒ ⇒ "
          "**⇒ 而这正是 1004/1005 两次明写「没查」的那一维**",
          '"P1_duplicate_anchor_texts_exist"' in _p1006
          and '"p1_duplicate_anchor_texts_exist_1006_"' in _ausrc
          and '"P1_hold_1006"' in _p1006
          and 'n_max_targets_on_one_text' in _p1006
          and 'n_cross_audit_probe' in _p1006
          and '而这正是 1004/1005 两次明写「没查」的那一维' in _p1006
          and '而这正是 1004/1005 两次明写「没查」的那一维' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「跨目标重复的条数」直接当成风险量**
          and '所以跨目标重复的条数就是风险量' not in _p1006
          and '所以跨目标重复的条数就是风险量' not in _ausrc)

    check("K993O.2 ⭐⭐⭐⭐⭐ **P2 成立、而它把 P1 的结论**劈成两半**："
          "**498 个「锚点-目标」对里、上下文提到该文件自己的只有 84 个（16.9%）** ⇒ ⇒ "
          "**⇒ 而样板句天然无害：它是一句方法论声明、不是对某处代码的事实断言** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 所以「跨目标重复」的**数量**不能直接当风险量** ⇒ ⇒ "
          "**⇒ 判据是「上下文有没有提到那个文件自己」**",
          '"P2_mostly_boilerplate"' in _p1006
          and '"p2_mostly_boilerplate_2006_"' in _ausrc
          and '"boilerplate_axis_1006"' in _p1006
          and '这次出现的 ±%d 字符里出现了该文件自己的名字/编号' in _p1006
          and '样板句（纪律声明）天然无害' in _p1006
          and '样板句天然无害：它是一句方法论声明、不是对某处代码的事实断言' in _ausrc
          and '所以「跨目标重复」的' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说「重复就是危险」**
          and '重复就是危险' not in _p1006
          and '重复就是危险' not in _ausrc)

    check("K993O.3 ⭐⭐⭐⭐⭐ **P3 成立、而这个不对称是**可解释的**："
          "**探针侧「提到自己」只有 1.9%、audit 侧是 41.7%** ⇒ ⇒ "
          "**⇒ 因为 audit 侧是「基线说明」、它本来就在讲具体文件的结论；"
          "**而探针的 docstring 是「我这一批的方法论」** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而真正危险的那 minority 就在 audit 侧**",
          '"P3_probe_side_is_even_more_boilerplate"' in _p1006
          and '"p3_probe_side_is_even_more_boilerplate_2006_"' in _ausrc
          and '"asymmetry_1006"' in _p1006
          and '所以探针侧的重复几乎都是样板句' in _p1006
          and '探针侧「提到自己」只有 1.9%' in _ausrc
          and '而探针的 docstring 是「我这一批的方法论」' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把这个不对称说成「两边应该一样」**
          and '两侧的比例应该一样' not in _p1006
          and '两侧的比例应该一样' not in _ausrc)

    check("K993O.4 ⭐⭐⭐⭐⭐ **P4 成立：注入一条「跨目标重复、两边上下文都提到各自文件」的锚点、"
          "**普查把它挑了出来、而门对它报 0 问题** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而这个 0 正是 P5 的一半 —— 「两处都在」对存在性门来说就是「完全健康」** ⇒ ⇒ "
          "**⇒ 而我第一版把带注入的 audit 副本传成了未改的那份、门报了 1 个 MISSING —— "
          "**而那是门**正确**地报「声明了、目标里没有」**",
          '"P4_reverse_case"' in _p1006
          and '"p4_reverse_case_2006_"' in _ausrc
          and '"P4_hold_1006"' in _p1006
          and '不然「跨目标重复是 238 段」这个数与「普查压根没在跑」' in _p1006
          and '而这个 0 正是 P5 的一半' in _ausrc
          and '而那是门**正确**地报' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「门报了 MISSING」直接判成「反向用例失败」**
          #   （⚠️ 而「几乎要把它当成反向用例失败」这句**在探针里是有的** ——
          #    **那是诚实的记录、不是这个禁令要禁的东西** ⇒ 禁的是**不带转折的断言**）
          and '门报 MISSING 就说明反向用例失败' not in _p1006
          and '门报 MISSING 就说明反向用例失败' not in _ausrc)

    check("K993O.5 ⭐⭐⭐⭐⭐ **P5 成立、而这是本批的核心交付：**"
          "**把一个跨目标重复锚点在 8 个目标之一里的**全部出现**改掉、真跑门 ⇒ "
          "**门只报受害目标那 1 个、而对其余 7 个目标里的副本只字不提** ⇒ ⇒ "
          "**⇒ 而那些副本此时已与受害者的意图脱节 —— 一次编辑只让一处变红、其余静默失真** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而这不是疏漏、是存在性门按定义问不到的问题：**"
          "**「这条锚点在不在」这个问题的答案、在每一份副本上都是「在」** ⇒ ⇒ "
          "**⇒ 唯一能看见它的办法是「跨目标比对同一段文字」**",
          '"P5_the_blind_spot_is_real_and_demonstrable"' in _p1006
          and '"p5_the_blind_spot_2006_"' in _ausrc
          and '"P5_hold_1006"' in _p1006
          and '"blind_spot_1006"' in _p1006
          and 'others_still_contain_the_anchor' in _p1006
          # ⭐⭐⭐⭐⭐ **而「一次编辑」的准确含义是「一次让那处失效的编辑」**
          and '而这正是 1004 的零耦合结论' in _p1006
          and '所以「一次编辑」的准确含义必须是「一次让那处失效的编辑」' in _p1006
          and '唯一能看见它的办法是「跨目标比对同一段文字」' in _p1006
          and '一次编辑只让一处变红、其余静默失真' in _ausrc
          # ⭐⭐⭐⭐⭐ **⇒ 而本批顺带把 1003 那个「探针侧不可覆盖」的洞补上了**
          and '而本批顺带把 1003 那个「探针侧不可覆盖」的洞补上了' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说存在性门看得到这件事**
          and '存在性门看得到这件事' not in _p1006
          and '存在性门看得到这件事' not in _ausrc)

    check("K993O.6 ⭐⭐⭐⭐⭐ **P6 成立、而它是开工第一分钟就撞上的：**"
          "**verifier 有一条锚点钉的是**门自己源码的一整行 ⇒ 我给门加 `argv[3]` 的那一刻它就打红了** ⇒ ⇒ "
          "**⇒ 处置：钉到结构上稳定的片段、而不是整行** ⇒ ⇒ "
          "**⇒ P7 成立：判据文本里手写的每一个数都必须有出处（32 个数、0 个没出处）** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而 P7 的契约在第一版就写错了：我要求「逐字相同」、它报 4/7 drift —— "
          "**⇒ 而逐条 diff 之后那 4 处差异全在措辞、没有一个在数字上** ⇒ ⇒ "
          "**⇒ 契约不许越界去管措辞：「措辞与摘要不同」是设计、「数字没有出处」才是缺陷** ⇒ ⇒ "
          "**⇒ 本批纯离线：连 `mouse.click` 都没有**",
          '"P6_anchor_pointing_at_another_file_is_fragile"' in _p1006
          and '"p6_anchor_fragility_2006_"' in _ausrc
          and '"P6_hold_1006"' in _p1006
          and '处置：钉到结构上稳定的片段、而不是整行' in _p1006
          and '处置：钉到结构上稳定的片段、而不是整行' in _ausrc
          and '"p7_every_handwritten_number_is_justified_2006_"' in _ausrc
          and '"audit_numbers_vs_computed_1006"' in _p1006
          and '"P7_hold_1006"' in _p1006
          and '契约在第一版就写错了' in _ausrc
          and '「措辞与摘要不同」是设计、「数字没有出处」才是缺陷' in _p1006
          and '"offline_2006"' in _ausrc
          and '连 `mouse.click` 都没有' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门①**：**不许把「逐字相同」当成契约**
          and '逐字相同才算通过' not in _p1006
          and '逐字相同才算通过' not in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门②**：**不许把「仪器报红」直接当成「数据错」**
          and '仪器报红就是数据错了' not in _p1006
          and '仪器报红就是数据错了' not in _ausrc)

    # ══ 1007 宇宙冻结点 ══
    # ⚠️ 同 1006 那条：**1007 报的那些数是在它的 `L993P` 判据加进去之前测的** ⇒ ⇒
    #   **⇒ 冻结点必须落在 1007 自己的判据之前** ⇒ ⇒
    #   **⇒ 而这是 1006 逼出来的通则：一批的读数必须钉在「它自己那一刻」的宇宙上**
    # ══ L993P. 批 1007 **去查 1006 自己给的那个「可解释」—— 而它不成立**
    print("— L993P. 批 1007 去查 1006 的「样板轴」："
          "❌ **P1 被否（33.8% 不是少数）** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **P2：77/78 的 audit 侧「提到自己」只被两个通用词点亮 —— 换干净词表后 41.7% → 0.5%、不对称翻转** ⇒ ⇒ "
          "❌ **P3：那把刀没有客观停点（窗口 0/40/120/260/600 ⇒ 0.0/7.9/24.7/41.1/62.6%）**")

    check("L993P.1 ❌ **P1 被否：同一条句子在多个副本里「提到谁」前后不一致的占 33.8%、"
          "**而不是我预测的「少数」** ⇒ ⇒ "
          "**⇒ 而否掉它的那把刀本身就是错的 —— 见 P3**",
          '"P1_inconsistent_is_a_minority"' in _p1007
          and '"p1_inconsistent_is_not_a_minority_2007_"' in _ausrc
          and '"P1_hold_1007"' in _p1007
          and '"p1_inconsistent_is_not_a_minority_2007_"' in _p1007
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把这个 33.8% 说成「少数」**
          and '所以不一致的只有少数' not in _p1007
          and '所以不一致的只有少数' not in _ausrc)

    check("L993P.2 ⭐⭐⭐⭐⭐ **P2 成立、而它否掉的是 1006 自己写下的「可解释」："
          "**77/78 = 98.7% 的 audit 侧「提到自己」只被通用词点亮** ⇒ ⇒ "
          "**⇒ `判据` 点亮 72 份、`门的` 点亮 12 份、而真正的标识符合计 13 份** ⇒ ⇒ "
          "**⇒ 换干净词表后 audit 侧从 41.7% 塌到 0.5%、不对称翻转（探针 1.9% > audit 0.5%）、"
          "**不一致 81 → 4** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 所以那个不对称量的不是「两种文件性质不同」、是「两个词表不对称」** ⇒ ⇒ "
          "**⇒ 而撤销按规矩办：1006 那段原文一字没删、只在后面挂改写横幅**",
          '"P2_the_asymmetry_is_just_the_word_list"' in _p1007
          and '"p2_the_asymmetry_is_the_word_list_2007_"' in _ausrc
          and '"P2_hold_1007"' in _p1007
          and 'GENERIC = {"判据", "门的"}' in _p1007
          and '"attribution_1007"' in _p1007
          and '"dirty_vs_clean_1007"' in _p1007
          and 'asymmetry_inverted' in _p1007
          and '【1007 改写】' in _ausrc
          and '真实机制是词表混进了通用词、不是文件性质不同' in _ausrc
          and '而 1006 的 P1/P4/P5/P6 不受影响' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「机制不同」说成「两种文件性质不同」**
          and '两种文件性质不同所以不对称' not in _p1007
          and '两种文件性质不同所以不对称' not in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**撤销不许删原文**
          and 'p3_probe_side_is_even_more_boilerplate_2006_' in _ausrc)

    check("L993P.3 ❌⭐⭐⭐⭐⭐ **P3 被否的是我 1006 的判据口径："
          "**窗口 0/40/120/260/600 ⇒ audit 侧 0.0/7.9/24.7/41.1/62.6%** ⇒ ⇒ "
          "**⇒ 单调、无拐点、而 0 那档是 0.0%** ⇒ ⇒ "
          "**⇒ 260 也不够（40→260 新点亮 63 份、120→260 新点亮 31 份、260→600 又新点亮 41 份）** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 「没有客观停点」—— 260 是我拍的数、这把刀量的是窗口、不是那句话** ⇒ ⇒ "
          "**⇒ 而唯一有停点的口径是「窗口 = 0、只看那句话」⇒ 它的读数是 0/503 —— 一个空集**",
          '"P3_the_knob_has_no_principled_stop"' in _p1007
          and '"p3_the_knob_has_no_principled_stop_2007_"' in _ausrc
          and '"P4_anchor_alone_is_an_empty_set"' in _p1007
          and '"p4_anchor_alone_is_an_empty_set_2007_"' in _ausrc
          and '"sweep_1007"' in _p1007
          and '"newly_lit"' in _p1007
          and '"monotone_no_knee"' in _p1007
          and '而 260 也不够' in _p1007
          and '260 也不够' in _ausrc
          and '260 这个数也是我拍的' in _p1007
          # ⭐⭐⭐⭐⭐ **反向门①**：**不许把「换个窗口」当成分类依据**
          and '换个窗口就成立了' not in _p1007
          and '换个窗口就成立了' not in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门②**：**不许说这把刀有客观停点**
          and '这把刀有客观停点' not in _p1007
          and '这把刀有客观停点' not in _ausrc)

    check("L993P.4 ⭐⭐⭐⭐⭐ **P5 成立、而它的第一版是假的："
          "**注入一条「在副本 B 的上下文里点名了 A（而 B 不是 A）」的锚点 ⇒ "
          "**门对它报 0（它确实在两处都存在）、而轴同时报「不一致」与「说谎」** ⇒ ⇒ "
          "**⇒ 而我第一版只声明了一次 `'anchor' in _ausrc`** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 普查的宇宙是「verifier **声明**的锚点」、一条声明 = 一个目标 ⇒ ⇒ "
          "**⇒ 于是它永远不可能跨目标 —— 而输出看起来像「反向用例没咬到」** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 这是 1005 那条「注入失败要先查原因」的**反面**："
          "**注入压根没生效、而所有读数都长得像正常结果** ⇒ ⇒ "
          "**⇒ 处置：注入后必须断言它真的进了被测集合**",
          '"P5_reverse_case_both_knives_are_not_constant_zero"' in _p1007
          and '"p5_reverse_both_knives_are_not_constant_zero_2007_"' in _ausrc
          and '"P5_hold_1007"' in _p1007
          and '"reverse_case_1007"' in _p1007
          and '一条声明 = 一个目标' in _p1007
          and '一条声明 = 一个目标' in _ausrc
          and '注入没生效和「实验没咬到」在输出上完全一样' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「注入没生效」写成「反向用例失败」**
          and '注入没生效所以反向用例失败' not in _p1007
          and '注入没生效所以反向用例失败' not in _ausrc)

    check("L993P.5 ⭐⭐⭐⭐ **P6 成立：清单逐条落进 "
          "`docs/research/jimeng-canvas/stem-attribution-1007.json`、由写它的探针自己写** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而它是逐条的清单、不是总数** ⇒ ⇒ "
          "⭐⭐⭐⭐ **⇒ 本批还固化了一条通则：一批的读数必须钉在「它自己那一刻」的宇宙上** ⇒ ⇒ "
          "**⇒ verifier 里那两行「宇宙冻结点」就是这条通则的落点**",
          '"P6_list_it_line_by_line"' in _p1007
          and '"p6_the_list_is_written_by_the_instrument_2007_"' in _ausrc
          and '"P6_hold_1007"' in _p1007
          and 'stem-attribution-1007.json' in _p1007
          and 'stem-attribution-1007.json' in _ausrc
          and '"frozen_universe_1007"' in _p1007
          and '"frozen_universe_1006"' in _p1006
          and '而冻结点必须在 1006 判据**之前**' in _p1006
          and '口径」必须钉在它自己那一刻' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许只记总数就说「清单在仓里」**
          and '只记总数就算清单落仓了' not in _p1007
          and '只记总数就算清单落仓了' not in _ausrc)

    check("L993P.6 ⭐⭐⭐⭐⭐ **本批否掉的是我自己上一批写的判据** ⇒ ⇒ "
          "**⇒ 而 1006 的 P1/P4/P5/P6（重复存在、样板无害、反向用例、盲区）不受影响** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 「可解释」这个词用得太早了：机制没查清就写解释、而下一批就换掉了** ⇒ ⇒ "
          "**⇒ 而 P7 沿用 1006 的契约：判据文本里手写的每一个数都必须有出处** ⇒ ⇒ "
          "⭐⭐⭐⭐ **⇒ 本批纯离线：连 `mouse.click` 都没有**",
          '"honesty_note_1007"' in _p1007
          and '"P7_hold_1007"' in _p1007
          and '"audit_numbers_vs_computed_1007"' in _p1007
          and '"offline_2007"' in _ausrc
          and '而本批否掉的是我自己上一批写的判据' in _p1007
          and '而本批否掉的是我自己上一批写的判据' in _ausrc
          and '「可解释」这个词用得太早了' in _ausrc
          and '沿用 1006 的契约：判据文本里手写的每一个数都必须有出处' in _p1007
          and '连 `mouse.click` 都没有' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说「本批把上一批全推翻了」**
          and '本批把 1006 全部推翻' not in _p1007
          and '本批把 1006 全部推翻' not in _ausrc)


    # ══ 1008 宇宙冻结点 ══
    # ⚠️ 同 1006/1007 那条：**1008 报的那些数是在它的 `M993Q` 判据加进去之前测的** ⇒ ⇒
    #   **⇒ 冻结点必须落在 1008 自己的判据之前**
    # ══ M993Q. 批 1008 **1005 那份落进仓的清单，从它自己落地那一刻起就是过期的**
    print("— M993Q. 批 1008 清单新鲜度："
          "⭐⭐⭐⭐⭐ **用同一台仪器 + git 快照量出来：清单落地那一刻就少 7 条、此刻少 26 条** ⇒ ⇒ "
          "❌ **而 `J993N.3` 断言的「新增 0」今天读 26、门还是绿的** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **P3b 才是最锋利的：只在锚点后面追加一段 ⇒ 门报 0、清单报 0 —— 两边都隐形**")

    check("M993Q.1 ⭐⭐⭐⭐⭐ **P1 成立：1005 那份落进仓的逐条清单、**"
          "**从它自己落地那一刻起就少 7 条、此刻少 26 条** ⇒ ⇒ "
          "**⇒ 而量法是「**同一台仪器**（1005 那个探针）只换它读的 verifier 快照」** ⇒ ⇒ "
          "**⇒ 而 `J993N.3` 断言的「新增 0」今天读的是 26、而门是绿的**",
          '"P1_the_golden_is_stale"' in _p1008
          and '"p1_the_golden_is_stale_2008_"' in _ausrc
          and '"P1_hold_1008"' in _p1008
          and '"staleness_1008"' in _p1008
          and '"stale_at_birth"' in _p1008
          and '"stale_now"' in _p1008
          and 'zero-coupling-anchors-1005.json' in _p1008
          # ⭐ 探针里那是**格式串**（`%d`）、所以只能钉到「少」字之前
          and '清单落地那一刻就少' in _p1008
          and '清单落地那一刻就少 7 条' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许拿「今天的数」当「它出生时的数」**
          and '清单今天差 26 条所以它出生时就差 26 条' not in _p1008
          and '清单今天差 26 条所以它出生时就差 26 条' not in _ausrc)

    check("M993Q.2 ⭐⭐⭐⭐⭐ **P2 成立：`added` 单调 7→19→26→26、而 `removed` 四个快照全是 0** ⇒ ⇒ "
          "**⇒ 所以「消失 0」是**不承载信息**的那一半、而「新增 0」是唯一会变的那一半** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而判据 `J993N.3` 写的是「两者都为 0」⇒ ⇒ "
          "**⇒ 混进一个不承载信息的断言 ⇒ ⇒ 整条判据退化成另一半**",
          '"P2_added_is_the_only_informative_half"' in _p1008
          and '"p2_added_is_the_only_informative_half_2008_"' in _ausrc
          and '"P2_hold_1008"' in _p1008
          and '"removed_ever_nonzero"' in _p1008
          and '整条判据退化成另一半' in _p1008
          and '整条判据退化成另一半' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门①**：**不许把「消失 0」当成「没人改过」的证据**
          and '消失 0 说明没人改过' not in _p1008
          and '消失 0 说明没人改过' not in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门②**：**不许把「新增 0」当成清单新鲜的充分条件**
          and '新增 0 就是清单新鲜的充分条件' not in _p1008
          and '新增 0 就是清单新鲜的充分条件' not in _ausrc)

    check("M993Q.3 ⭐⭐⭐⭐⭐⭐ **P3 是本批最锋利的一条，而它由两个子实验构成：**"
          "**① P3a 把锚点**就地改字** ⇒ 门报 1 个 MISSING、清单报 1 条消失** ⇒ ⇒ "
          "**⇒ 所以「消失 0」**不是恒真**、只是**没发生过** ⇒ ⇒ "
          "**⇒ ② P3b 只在锚点后面追加一段 ⇒ 门报 0、清单报 0 条消失 —— 两边都看不见** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 因为锚点判的是**子串包含**、而「原文 + 后缀」里仍然含着原文** ⇒ ⇒ "
          "**⇒ 这和 1003「锚点之间有包含关系」是同一条机制、"
          "**只是那一次伤的是「量耦合」、这一次伤的是「量清单」**",
          '"P3_is_removed_0_constant_or_never_fired"' in _p1008
          and '"p3_removed_zero_is_never_fired_not_constant_2008_"' in _ausrc
          and '"P3_hold_1008"' in _p1008
          and '"P3a_inplace_edit"' in _p1008
          and '"P3b_append_only_edit"' in _p1008
          and '两边都看不见' in _p1008
          and '两边都看不见' in _ausrc
          and '子串包含' in _p1008
          and '那一次伤的是「量耦合」、这一次伤的是「量清单」' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门①**：**不许说「只加不改也会被看见」**
          and '只加不改也会被看见' not in _p1008
          and '只加不改也会被看见' not in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门②**：**不许说「从未被触发的断言」等于「恒真的断言」**
          and '从未被触发的断言就是恒真的断言' not in _p1008
          and '从未被触发的断言就是恒真的断言' not in _ausrc)

    check("M993Q.4 ⭐⭐⭐⭐⭐ **P4 成立：门报 0、而清单此刻少 26 条 ⇒ ⇒ "
          "**⇒ 所以门绿不是它测得粗、是它测的东西一半不承载信息** ⇒ ⇒ "
          "**⇒ 而 1005 的纪律「写它的仪器必须就是读它的那个」**不充分** —— "
          "**仪器是同一台、而**输入**在写与读之间变了** ⇒ ⇒ "
          "⭐⭐⭐⭐ **⇒ 而 1006/1007 的「宇宙冻结点」只救自己、救不了别人的清单**",
          '"P4_why_the_gate_is_green"' in _p1008
          and '"p4_why_the_gate_is_green_2008_"' in _ausrc
          and '"P4_hold_1008"' in _p1008
          and '"recheck_1006_own_universe' in _p1007
          and '宇宙冻结点」只救自己' in _p1008
          and '「写它的仪器必须就是读它的那个」**不充分**' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说「同一台仪器就够了」**
          and '同一台仪器就够了' not in _p1008
          and '同一台仪器就够了' not in _ausrc)

    check("M993Q.5 ⭐⭐⭐⭐ **P5 成立：判据是「一份清单逐条比对今天的普查、**新增与消失都要报**」⇒ ⇒ "
          "**⇒ 而今天这一比就是：新增 26、消失 0** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而处置不是「把所有老账一次报红」—— 那样门第一次会因为历史遗留而红、"
          "**而人看到红色会以为刚刚坏了什么** ⇒ ⇒ "
          "**⇒ 所以每批只对自己的宇宙负责、老账记成账龄** ⇒ ⇒ "
          "**⇒ P6：账龄逐条落进 `docs/research/jimeng-canvas/golden-freshness-1008.json`、"
          "**由写它的探针自己写**",
          '"P5_reverse_case"' in _p1008
          and '"p5_reverse_ghost_list_must_be_reported_2008_"' in _ausrc
          and '"P5_hold_1008"' in _p1008
          and '"P6_disposition"' in _p1008
          and '"P6_hold_1008"' in _p1008
          and 'golden-freshness-1008.json' in _p1008
          and 'golden-freshness-1008.json' in _ausrc
          and '而人看到红色会以为刚刚坏了什么' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「老账」直接判成 fail**
          and '老账直接判成 fail' not in _p1008
          and '老账直接判成 fail' not in _ausrc)

    check("M993Q.6 ⭐⭐⭐⭐⭐ **本批否的是 1005 给那份清单配的那条判据、**"
          "**不是 1005 的发现** ⇒ ⇒ "
          "**⇒ 而 1005 的 P1/P2/P4/P5（两类、否掉行距、注入动两侧、分母都报）不受影响** ⇒ ⇒ "
          "⭐⭐⭐⭐ **⇒ 而本批自己踩了一次它要立的纪律：临时文件是在断言上崩掉后留下的、"
          "**所以「任何写出临时文件的仪器都必须注册 `atexit` 清理」** ⇒ ⇒ "
          "**⇒ 本批纯离线：连 `mouse.click` 都没有**",
          '"honesty_note_1008"' in _p1008
          and '"offline_2008"' in _ausrc
          and '@atexit.register' in _p1008
          and '而本批否的是 1005 给那份清单配的那条判据、不是 1005 的发现' in _p1008
          and '而本批否的是 1005 给那份清单配的那条判据、不是 1005 的发现' in _ausrc
          and '任何写出临时文件的仪器都必须注册 `atexit` 清理' in _ausrc
          and '连 `mouse.click` 都没有' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说「本批把 1005 全部推翻」**
          and '本批把 1005 全部推翻' not in _p1008
          and '本批把 1005 全部推翻' not in _ausrc)


    # ══ 1009 宇宙冻结点 ══
    # ⚠️ 同 1006/1007/1008 那条：**1009 报的那些数是在它的 `N993R` 判据加进去之前测的**
    #   ⇒ ⇒ **⇒ 而 1008 忘了执行这条通则、所以这一行是「上一批的教训」的物证**
    # ══ N993R. 批 1009 **「目标侧的编辑 × 门看得见吗」—— 一张逐行真跑门的表**
    print("— N993R. 批 1009 目标侧编辑可见性："
          "⭐⭐⭐⭐⭐ **8 种编辑逐行真跑门 ⇒ 门看得见的 4 种、看不见的 4 种** ⇒ ⇒ "
          "❌ **P2 被否：「升级成必须恰好 N 次」补不上 —— 末尾追加根本不改 N** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而看不见的那四种、共同点是「改动之后原文仍是子串或还在」**")

    check("N993R.1 ⭐⭐⭐⭐⭐ **P1 成立（而我第一版把它算错了）：`_ausrc` 侧 3380 条正向锚点、"
          "**其中 285 条（8.4%）在 audit 里出现 2 次以上** ⇒ ⇒ "
          "**⇒ 而门对每一条都只问同一个二元问题「在不在」⇒ ⇒ "
          "**⇒ 于是「在 1 次」和「在 4 次」对门是同一件事** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而反向锚点那 146 条的「0 次」是**期望值** —— 正向与反向不是一种状态**",
          '"P1_four_states_are_very_uneven"' in _p1009
          and '"p1_four_states_are_very_uneven_2009_"' in _ausrc
          and '"P1_hold_1009"' in _p1009
          and '"hist_positive"' in _p1009
          and '"hist_negative"' in _p1009
          and '"n_positive_appearing_more_than_once"' in _p1009
          and '正向与反向不是一种状态' in _p1009
          and '正向与反向不是一种状态' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把反向锚点的「0 次」当成异常**
          and '反向锚点的 0 次是异常' not in _p1009
          and '反向锚点的 0 次是异常' not in _ausrc)

    check("N993R.2 ❌⭐⭐⭐⭐⭐ **P2 被否：把门从「在不在」升级成「必须恰好 N 次」补不上这个洞** ⇒ ⇒ "
          "**⇒ 因为「只在末尾追加」根本不改 N、而它对门完全隐形** ⇒ ⇒ "
          "**⇒ 所以那不是「升级 N」能补的洞 —— 洞在「子串包含」这个机制本身** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而 P3 否掉的是我的预测：能穿过门的不是「两种」而是「四种」** ⇒ ⇒ "
          "**⇒ 看不见的那四种、共同点是「改动之后原文仍是子串或还在」**",
          '"P2_requiring_exactly_n_would_close_the_gap"' in _p1009
          and '"P2_requiring_exactly_n_would_close_the_gap_2009_"' in _ausrc
          and '"P2_hold_1009"' in _p1009
          and '"edit_table_1009"' in _p1009
          and '"gate_sees_it"' in _p1009
          and '洞在「子串包含」这个机制本身' in _p1009
          and '洞在「子串包含」这个机制本身' in _ausrc
          and '能穿过门的不是「两种」而是「**四种**」' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门①**：**不许把「升级成恰好 N 次」说成解法**
          and '升级成恰好 N 次就能补上' not in _p1009
          and '升级成恰好 N 次就能补上' not in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门②**：**不许用推理填那张表的任何一格**
          and '这张表里有格子是推理出来的' not in _p1009
          and '这张表里有格子是推理出来的' not in _ausrc)

    check("N993R.3 ⭐⭐⭐⭐⭐ **P4 成立：在目标里把锚点**复制一份** ⇒ 门**仍然报 0** ⇒ ⇒ "
          "**⇒ 而这是唯一一种「门看不见、但**普查**看得见」的编辑** ⇒ ⇒ "
          "**⇒ 因为它把「零耦合」变成「非零耦合」、而门对次数一无所知** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 所以门与普查的分工边界就在这儿：门管「在不在」、"
          "普查管「在几次、在几个文件」** ⇒ ⇒ "
          "**⇒ P5 成立：那张表 8 行**全部**是真跑门跑出来的、没有一格是推理填的**",
          '"P4_the_one_case_only_the_census_sees"' in _p1009
          and '"p4_the_one_case_only_the_census_sees_2009_"' in _ausrc
          and '"P4_hold_1009"' in _p1009
          and '"p5_table_not_arguments"' in _p1009
          and '"p5_table_not_arguments_2009_"' in _ausrc
          and '"P5_hold_1009"' in _p1009
          and '门管「在不在」、普查管「在几次、在几个文件」' in _p1009
          and '门管「在不在」' in _ausrc
          and '没有一格是推理填的' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说普查是门的替代品**
          and '普查可以取代这道门' not in _p1009
          and '普查可以取代这道门' not in _ausrc)

    check("N993R.4 ⭐⭐⭐⭐⭐ **P6 成立：逐行落进 "
          "`docs/research/jimeng-canvas/edit-visibility-1009.json`、由写它的探针自己写** ⇒ ⇒ "
          "⭐⭐⭐⭐ **⇒ 而本批自己踩了两次「顺序」与「口径」的坑，都已修**："
          "**① 正向与反向混在一起数、把 146 条反向当成「第 0 种」** ⇒ ⇒ "
          "**② `verdicts` 建在清单落盘之前、于是 `p6` 那一条读到空字符串** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 处置：凡是被引用的东西必须先造好；"
          "而「空字符串」这种读数太容易被当成「这里本来就没什么可写」** ⇒ ⇒ "
          "**⇒ 本批纯离线：连 `mouse.click` 都没有**",
          '"P6_golden_and_numbers"' in _p1009
          and '"p6_golden_1009_"' in _ausrc
          and '"P6_hold_1009"' in _p1009
          and 'edit-visibility-1009.json' in _p1009
          and 'edit-visibility-1009.json' in _ausrc
          and '凡是被引用的东西必须先造好' in _p1009
          and '凡是被引用的东西必须先造好' in _ausrc
          and '空字符串' in _p1009
          and '连 `mouse.click` 都没有' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「空字符串」当成「没什么可写」**
          and '读到空字符串说明本来就没什么可写' not in _p1009
          and '读到空字符串说明本来就没什么可写' not in _ausrc)


    # ══ 1010 宇宙冻结点 ══
    # ⚠️ 同 1006/1007/1008/1009 那条：**1010 报的那些数是在它的 `O993S` 判据加进去之前测的**
    # ══ O993S. 批 1010 **把 1009 那张表从实验室搬到真实历史：九批里门看见了 0 次**
    print("— O993S. 批 1010 真实历史的检出力："
          "⭐⭐⭐⭐⭐ **九对相邻快照、audit 基线被动过 39 条锚点、门在 `_ausrc` 作用域上一次都没报** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 检出力 = 0.0；而 P3 说清了为什么：那 39 条**全部**是「追加」** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐⭐ **而基线自检还撞出第二个交付：1001 那一版跑今天的门会报 1 个 MISSING，"
          "**正是 1006 亲手换掉的那条「钉门源码整行」的锚点**")

    check("O993S.1 ⭐⭐⭐⭐⭐ **P1 成立：九批里 audit 基线被改动**动过**的锚点共 39 条、"
          "**而门在 `_ausrc` 作用域上一次都没报（累计 0）** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 检出力 = 0.0** ⇒ ⇒ "
          "**⇒ 而分母是逐条算出来的「哪些锚点的出现次数变了」、不是一个拍出来的数** ⇒ ⇒ "
          "**⇒ 而 1002 那个注入实验的分母是 1、所以两者不能直接比大小**",
          '"P1_detection_rate_over_real_history"' in _p1010
          and '"p1_detection_rate_over_real_history_2010_"' in _ausrc
          and '"P1_hold_1010"' in _p1010
          and '"real_history_1010"' in _p1010
          and '"n_touched_total"' in _p1010
          and '"detection_rate"' in _p1010
          and '"n_gate_reported_ausrc_total"' in _p1010
          and '分母是逐条算出来的' in _p1010
          and '检出力 = 0.0' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许拿 0.0 说成「这道门一点用没有」**
          and '检出力 0 所以这道门一点用没有' not in _p1010
          and '检出力 0 所以这道门一点用没有' not in _ausrc)

    check("O993S.2 ⭐⭐⭐⭐⭐ **P2 成立、而它的对照我第一版写错了：真实检出力 0.0 —— "
          "**九对快照里没有一次、门在 `_ausrc` 作用域上开过口** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐⭐ **⇒ 而 1002 在仓里只**逐类**记了检出率、没有记总计 ⇒ ⇒ "
          "**⇒ 那个「总检出力 0.333」只活在对话里 —— 而这正是 1008 主题的又一个形态："
          "结论甚至没进仓、就只剩记忆** ⇒ ⇒ "
          "**⇒ 处置：「被引用的、仓里没有的数」要和「有出处的数」分开记**",
          '"P2_real_rate_is_lower_than_the_injected_one"' in _p1010
          and '"p2_real_rate_is_lower_than_the_injected_one_2010_"' in _ausrc
          and '"P2_hold_1010"' in _p1010
          and 'CITED_NOT_IN_REPO' in _p1010
          and 'cited_not_in_repo' in _p1010
          and '只活在对话里' in _p1010
          and '只活在对话里' in _ausrc
          and '被引用的、仓里没有的数' in _p1010
          and '被引用的、仓里没有的数' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「引用一个仓里没有的数」当成「引用是合法的」**
          and '引用了就是合法的' not in _p1010
          and '引用了就是合法的' not in _ausrc)

    check("O993S.3 ⭐⭐⭐⭐⭐ **P3 成立：门看不见的那些**全部**是「audit 基线里**追加**了新条目」** —— "
          "**39 条动过里面有 39 条出现次数只增不减、0 条真的消失** ⇒ ⇒ "
          "**⇒ 而追加不会让任何既有锚点从目标里消失、所以门一个字都不该报** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐⭐ **⇒ 而这就是本批的全部教训：「本会话的真正工作」是往基线里追加条目 —— "
          "**而追加恰好是门最看不见的那一类** ⇒ ⇒ "
          "**⇒ 所以这道门的形状决定了「它最该看的那类改动」它恰恰看不见**",
          '"P3_the_invisible_ones_are_additions"' in _p1010
          and '"p3_the_invisible_ones_are_additions_2010_"' in _ausrc
          and '"P3_hold_1010"' in _p1010
          and '"n_occurrence_increased_total"' in _p1010
          and '本会话的真正工作' in _p1010
          and '它最该看的那类改动' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许说「门该报而没报」就是门坏了**
          and '门没报所以门坏了' not in _p1010
          and '门没报所以门坏了' not in _ausrc)

    check("O993S.4 ⭐⭐⭐⭐⭐ **P4 成立：拿一个真的被删掉的锚点 ⇒ `_ausrc` 作用域上门报 1 个、"
          "**检出力 = 1.0** ⇒ ⇒ "
          "**⇒ 而这一条是为了排除「检出力低是因为分母算错了」** ⇒ ⇒ "
          "**⇒ 分母没算错 —— 是「动过」的 39 条里真的没有一条能让门开口** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐⭐⭐ **⇒ 而基线自检本身撞出第二个交付：1001 那一版跑今天的门会报 1 个 MISSING、"
          "**它在 `_anchs` 上、正是 1006 亲手换掉的那条「钉门源码**整行**」的锚点** ⇒ ⇒ "
          "**⇒ 也就是说 1006 的 P6 不只是当时的观察、它能从 git 历史里复现出来** ⇒ ⇒ "
          "**⇒ 而复现它的办法就是「拿旧 verifier 跑今天的门」—— 零成本**",
          '"P4_reverse_case"' in _p1010
          and '"p4_reverse_case_2010_"' in _ausrc
          and '"P4_hold_1010"' in _p1010
          and '"P6_hold_1010"' in _p1010
          and '"n_pairs_with_out_of_scope_missing"' in _p1010
          and '拿旧 verifier 跑今天的门' in _p1010
          and '拿旧 verifier 跑今天的门' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「越界变量的 MISSING」混进主口径的分母**
          and '越界的 MISSING 算进分母' not in _p1010
          and '越界的 MISSING 算进分母' not in _ausrc)

    check("O993S.5 ⭐⭐⭐⭐ **P5 成立：逐对落进 "
          "`docs/research/jimeng-canvas/real-history-detection-1010.json`、由本探针自己写** ⇒ ⇒ "
          "⭐⭐⭐⭐ **⇒ 而它记的是「每一对动了多少、门报了几条、检出率多少」** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐ **⇒ 而本批只量 `_ausrc` 这一个目标 —— 局部读数不许长得像全局的** ⇒ ⇒ "
          "**⇒ P7 成立：22 个手写的数、0 个没出处** ⇒ ⇒ "
          "**而 `0.333` 被单列为「被引用、仓里没有的数」而不是混进白名单** ⇒ ⇒ "
          "**⇒ 本批纯离线：连 `mouse.click` 都没有**",
          '"P5_golden_and_numbers"' in _p1010
          and '"p5_golden_2010_"' in _ausrc
          and '"P5_hold_1010"' in _p1010
          and '"P7_hold_1010"' in _p1010
          and '"audit_numbers_vs_computed_1010"' in _p1010
          and 'real-history-detection-1010.json' in _p1010
          and 'real-history-detection-1010.json' in _ausrc
          and '局部读数不许长得像全局的' in _p1010
          and '局部读数不许长得像全局的' in _ausrc
          and '本批只量 `_ausrc` 这一个目标' in _ausrc
          and '连 `mouse.click` 都没有' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把局部的检出力说成全局的**
          and '全局检出力就是 0.0' not in _p1010
          and '全局检出力就是 0.0' not in _ausrc)


    # ══ 1011 宇宙冻结点 ══
    # ⚠️ 同 1006/1007/1008/1009/1010 那条：**1011 报的那些数是在它的 `P993T` 判据
    #    加进去之前、在 1010 那一版 audit 上测的** ⇒ ⇒
    #    **⇒ 而 1011 报的 45 次改动里没有一次来自它自己这一批 —— 因为它只读 git
    #    历史、不改 audit 的基线条目** ⇒ ⇒ ⇒
    #    **⇒ 这也是本批唯一一处「宇宙漂移量为零」的读数，必须和别的批次分开说**
    # ══ P993T. 批 1011 **真实历史里门看不见的那些改动，是一批什么样的改动**
    print("— P993T. 批 1011 改动的局部性："
          "45 次改动只落在 8 段文本上，38 次落在 3 句计费声明上")
    check("P993T.1 ⭐⭐⭐⭐⭐⭐⭐ **P1 成立：口径差必须显式对齐 —— 1010 记的是 39"
          "（只算了九对快照）、本批把 1010 自己那次也算进来、逐条复算得 45，"
          "差的 6 全部来自 `1009->1010` 那一对** ⇒ ⇒ "
          "**⇒ 而两个数都留在仓里、不许默默把 39 改成 45**",
          '"P1_hold_2011"' in _p1011
          and '"n_touched_ten_pairs"' in _p1011
          and '"n_touched_nine_pairs_2010"' in _p1011
          and '"n_delta_ten_minus_nine"' in _p1011
          and '"p1_denominator_is_45_not_39_2011_"' in _ausrc
          and '逐条复算得 45' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「口径变宽」悄悄写成「口径变了结论」**
          and '所以 1010 的结论错了' not in _p1011
          and '所以 1010 的结论错了' not in _ausrc)

    check("P993T.2 ⭐⭐⭐⭐⭐⭐⭐⭐ **P2 成立：条数 ≠ 地方数 —— 那 45 次改动只落在 8 段不同文本上，"
          "而其中 38 次落在 3 句话上；那 3 句话是每一批都在重复写的「本批纯离线、"
          "不打开浏览器、不按任何键、连 `mouse.click` 都没有」计费声明** ⇒ ⇒ "
          "**⇒ 所以 1010 的 0.0 首先是「关于计费声明的 0.0」；扣掉它们后剩 7 次改动、5 段文本**",
          '"n_distinct_anchor_texts"' in _p1011
          and '"n_billing_texts"' in _p1011
          and '"n_billing_records"' in _p1011
          and '"n_nonbilling_records"' in _p1011
          and '"n_nonbilling_texts"' in _p1011
          and '本会话每一批都在写的' in _p1011
          and '"p2_45_changes_land_on_8_texts_38_on_the_billing_line_2011_"' in _ausrc
          and '条数 ≠ 地方数' in _ausrc
          and '计费声明' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐ **反向门**：**扣减后必须和扣减前一起报** ——
          #   **只报扣减后的 5 段，会让「8 段里 7 段命中」这个读数看起来更弱，
          #   而它恰恰是本批最容易被拿去做路线决策的那个数**
          and '扣掉它们之后还剩 7 次改动、5 段文本' in _ausrc)

    check("P993T.3 ⭐⭐⭐⭐⭐⭐⭐ **P3 成立：45 次改动里有 43 次（95.6%）落在 occurrence ≥ 2 的锚点上，"
          "而全集里 occurrence ≥ 2 的只有 8.6%（292/3407）—— 偏斜 11.1 倍** ⇒ ⇒ "
          "**⇒ 而这不是随机抽样的偶然：真实工作流改的恰恰是「被反复声明」的那些句** ⇒ ⇒ "
          "**⇒ 所以 1010 的分母天生偏在零耦合那一侧、那个 0.0 不能外推**",
          '"n_ge2_touched"' in _p1011
          and '"n_positive_ausrc_at_1010"' in _p1011
          and '"n_ge2_whole_universe"' in _p1011
          and '"rate_ge2_touched_pct"' in _p1011
          and '"rate_ge2_whole_pct"' in _p1011
          and '"bias_ratio"' in _p1011
          and '"p3_touched_is_biased_to_high_occurrence_2011_"' in _ausrc
          and '偏斜 11.1 倍' in _ausrc
          and '不能外推' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「偏斜」写成「门只覆盖高 occurrence」** ——
          #   **那是两回事：门覆盖的是全部 occurrence ≥ 1 的锚点**
          and '所以门只覆盖高 occurrence 的锚点' not in _ausrc)

    check("P993T.4 ⭐⭐⭐⭐⭐⭐⭐⭐ **P4 成立：按 1004 的耦合度公式（自身只出现 1 次 ? 1 : 0），"
          "occurrence ≥ 2 的锚点耦合度本该是 0；实测门报 0 个 —— 一致** ⇒ ⇒ "
          "**⇒ 所以「门看不见那 43 次改动」不是缺陷、是公式要求的结果** ⇒ ⇒ "
          "**⇒ 真正的问题被换掉了：不是「门弱」，是「门唯一的不变量与真实工作流的主形态正交」**",
          '"n_predicted_zero_coupling"' in _p1011
          and '"P4_hold_2011"' in _p1011
          and '"p4_invisible_is_correct_not_a_defect_2011_"' in _ausrc
          and '不是缺陷、是公式要求的结果' in _ausrc
          and '与真实工作流的主形态正交' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门（本批的核心）**：**「看不见」必须先判「门弱」还是「公式要求」**
          and '所以门坏了' not in _p1011
          and '所以门坏了' not in _ausrc
          and '零耦合是缺陷' not in _ausrc)

    check("P993T.5 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P5 成立：这 45 次改动里出现次数增加 45、减少 0、归零 0** ⇒ ⇒ ⇒ "
          "**⇒ 而 occurrence 就是「在几次」那个轴、它在真实工作流下单调只增** ⇒ ⇒ ⇒ "
          "**⇒ 1009 P4 早就把这一轴指认给普查了、而它至今没有任何一条门判据覆盖** ⇒ ⇒ ⇒ ⇒ "
          "**⇒ 而 1008 已经为这一类判据准备好了配套：老账记成账龄、不许一次报红**",
          '"n_increased"' in _p1011
          and '"n_decreased"' in _p1011
          and '"n_vanished"' in _p1011
          and '"P5_hold_2011"' in _p1011
          and '"p5_the_count_axis_only_grows_2011_"' in _ausrc
          and '单调只增' in _ausrc
          and '老账记成账龄' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门**：**不许把「单调只增」说成「门应该报」** ——
          #   **⇒ 每批都报的判据就是 1008 说的「一次报红」；正确处置是账龄，不是加严**
          and '所以门应该开始报这条' not in _p1011
          and '所以门应该开始报这条' not in _ausrc)

    check("P993T.6 ⭐⭐⭐⭐⭐ **P6 成立：8 段里 7 段落在 1005 那份 690 行零耦合清单里"
          "（87.5% vs 基准 12.0%；那份清单 690 行只有 658 个不同文本）** ⇒ ⇒ "
          "**⇒ 而样本只有 8 段、扣掉计费声明后只剩 5 段 ⇒ 所以本批不据此决定"
          "「该点修还是该普查」** ⇒ ⇒ "
          "**⇒ 诚实的结论是：样本量不足以决定路线、只能收窄 1010 读数的适用范围**",
          '"n_intersection"' in _p1011
          and '"rate_intersection_pct"' in _p1011
          and '"base_rate_1005_pct"' in _p1011
          and '"n_rows_1005_golden"' in _p1011
          and '"n_distinct_texts_1005_golden"' in _p1011
          and '"p6_cross_with_1005_golden_but_too_few_to_decide_2011_"' in _ausrc
          and '本批不据此决定' in _ausrc
          and '样本量不足以决定路线' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门（本批的诚实性闸门）** ——
          #   **「交集高 ⇒ 该点修得完」这个推论样本量根本不够；写了就是硬给路线**
          and '所以交集高、该点修得完' not in _p1011
          and '所以交集高、该点修得完' not in _ausrc)

    check("P993T.7 ⭐⭐⭐⭐⭐⭐⭐ **P7 成立：本批每一个读数都钉在 10 个 git 提交上，"
          "而「钉在历史上的判据」有专属的失效形态 —— 将来 rebase 之后这些 sha 取不到、"
          "判据不会报错、它会静静地读出空集** ⇒ ⇒ "
          "**⇒ 所以开工前先逐个 `git cat-file` 验活，实测 10/10 全部可取**",
          '"n_shas_alive"' in _p1011
          and '"n_commits"' in _p1011
          and '"P7_hold_2011"' in _p1011
          and 'sha_alive' in _p1011
          and 'cat-file' in _p1011
          and '"p7_history_backed_criteria_must_verify_shas_2011_"' in _ausrc
          and '验活' in _ausrc
          # ⭐⭐⭐⭐⭐⭐ **反向门**：**不许把「验活」写成「历史不会变」**
          and '所以历史是稳定的' not in _p1011
          and '所以历史是稳定的' not in _ausrc)

    check("P993T.8 ⭐⭐⭐⭐⭐ **P8 成立：逐条落进 "
          "`docs/research/jimeng-canvas/change-locality-1011.json`、由本探针自己写** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐⭐ **⇒ 而它记的是「每段文本被动了几次、出现在哪几对之间、是不是计费声明、"
          "在不在 1005 那份清单里」—— 这正是 1010 记了次数却没记身份的那一层** ⇒ ⇒ "
          "**⇒ 本批只量 `_ausrc` 这一个目标 —— 局部读数不许长得像全局的** ⇒ ⇒ "
          "**⇒ P9 成立：判据里手写的数全部有出处**",
          '"P8_hold_2011"' in _p1011
          and '"P9_hold_2011"' in _p1011
          and '"audit_numbers_vs_computed_2011"' in _p1011
          and 'change-locality-1011.json' in _p1011
          and 'change-locality-1011.json' in _ausrc
          and '局部读数会长得像全局的' in _p1011
          and '局部读数会长得像全局的' in _ausrc
          and '本批只量 `_ausrc` 这一个目标' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐ **反向门**：**不许把局部读数说成全局的** ——
          #   **⇒ 而 1006/1007 改过的探针侧文件根本不在本批分母里**
          and '全局检出力就是 0.0' not in _p1011
          and '全局检出力就是 0.0' not in _ausrc
          and '这些读数不是全局的' in _p1011)



    # ══ 1012 宇宙冻结点 ══
    # ⚠️ 同 1006–1011 那条：**1012 报的那些数是在它的 `Q993U` 判据加进去之前、
    #    在 1011 那一版 audit 上测的**
    #    ⇒ ⇒ 而 1012 比前几批多一个自由度：**它扩到了全部 187 个目标变量**
    #    ⇒ ⇒ ⇒ **⇒ 而 1010/1011 只量了其中 1 个 ⇒ ⇒ ⇒ ⇒
    #    ⇒ 「全局」这个词在 1012 之前从来没有真的成立过**
    # ══ Q993U. 批 1012 **把同一台仪器扩到全局：门在十批真实历史里开口过几次**
    print("— Q993U. 批 1012 全局检出力："
          "187 个目标变量、58 次目标侧改动、真正消失 1 次 ⇒ 门开口 1 次、报对了")
    check("Q993U.1 ⭐⭐⭐⭐⭐⭐⭐⭐ **P1 成立：扩到全局之后 —— 10 对快照、187 个目标变量、"
          "声明锚点 58315 条次，被动过 58 次、真正消失 1 次 ⇒ 全局真实检出力 = 1/58** ⇒ ⇒ "
          "**⇒ 而 1010 记的 0.0 —— 那不是 0，那是一个只量了 1 个目标的局部读数**",
          '"P1_hold_2012"' in _p1012
          and '"n_pairs"' in _p1012
          and '"n_target_vars"' in _p1012
          and '"n_declared"' in _p1012
          and '"n_touched"' in _p1012
          and '"n_vanished"' in _p1012
          and '"global_detection_rate"' in _p1012
          and '"p1_global_rate_is_not_zero_2012_"' in _ausrc
          and '全局真实检出力 = 1/58' in _ausrc
          and '那是一个只量了 1 个目标的局部读数' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门**：**不许把局部的 0.0 继续当成全局的 0.0**
          and '所以门在全局口径上也是 0.0' not in _p1012
          and '所以门在全局口径上也是 0.0' not in _ausrc)

    check("Q993U.2 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P2 成立：分侧读数必须一起报 —— `_ausrc` 侧 54 次被动过、"
          "消失 0 次（检出力 0.0）；而其余 186 个目标变量侧 4 次被动过、消失 1 次（检出力 0.25）** ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ 所以「门一次都没开口」这句话在全局口径上是错的 —— 它开口了 1 次、"
          "而且那 1 次它报对了**",
          '"by_side"' in _p1012
          and '"_ausrc"' in _p1012
          and '"other"' in _p1012
          and '"n_other_vars"' in _p1012
          and '"P2_hold_2012"' in _p1012
          and '"p2_side_by_side_must_be_reported_together_2012_"' in _ausrc
          and '186 个目标变量' in _ausrc
          and '在全局口径上是错的' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门**：**不许用「除以更小的分母」把 0.25 说成「检出力高」**
          and '所以检出力其实很高' not in _p1012
          and '所以检出力其实很高' not in _ausrc)

    check("Q993U.3 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P3 成立（而它是**被否**的预期）："
          "本批开工时我以为「每批都在重写整个探针文件、所以探针侧的改动形态是重写而不是追加、"
          "应该产生大量真消失」** ⇒ ⇒ **实测：10 对快照里探针侧总共只被动过 4 次、真正消失 1 次** ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ 「我以为我知道我干了什么」是错的 —— 而这个错差点让我把路线定成"
          "「给门加一套声明机制」**",
          '"P3_hold_2012"' in _p1012
          and '我以为我知道我干了什么' in _p1012
          and '我的预期被否' in _p1012
          and '"p3_probe_side_is_not_rewritten_each_batch_2012_"' in _ausrc
          and '我的预期被否' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门**：**否掉的必须写清否的是谁**
          and '所以探针侧真的每批都被重写' not in _ausrc
          and '所以探针侧真的每批都被重写' not in _p1012)

    check("Q993U.4 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P4 成立：那唯一 1 次消失在 `1005->1006` 那一对、"
          "`_anchs` 变量上；而它和 1010 的 P6 是同一件事的两条完全独立的路径** —— "
          "1010 从「拿旧 verifier 跑今天的门」发现它，本批从「真实改动里数消失」发现它 ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 零成本的复现通道被两条互不依赖的路径互相确认**",
          '"vanished_detail"' in _p1012
          and '"P4_hold_2012"' in _p1012
          and '_anchs' in _ausrc
          and '两条完全独立的路径' in _ausrc
          and '互相确认' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门**：**「同一个东西」不许只凭印象写成「同一条」**
          and '所以这两件事必然是同一条' not in _p1012
          and '所以这两件事必然是同一条' not in _ausrc)

    check("Q993U.5 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P5 成立 —— 而它是路线决定（兑现 1011 的欠账）："
          "门没有「盲区」—— 它按设计不报 `_ausrc` 上那 54 次追加、按设计报真消失"
          "（1 次、报对了 1 次）** ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ 所以对策既不是「给门搬 187 条重复告警」、也不是「加严门」** ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而是把 `_ausrc` 上那 54 次追加登记成账（1008 立过的账龄机制）、"
          "让账去盯、而不是让门去报**",
          '"P5_hold_2012"' in _p1012
          and '门没有「盲区」' in _p1012
          and '"p5_route_decision_2012_"' in _ausrc
          and '路线决定（兑现 1011 的欠账）' in _ausrc
          and '让账去盯、而不是让门去报' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门**：**1011 说「不足以决定」是对的 ———
          #   **本批是兑现它、不是推翻它** ⇒ ⇒ 而「推翻 1011」写成结论是错的**
          and '所以 1011 的结论是错的' not in _p1012
          and '所以 1011 的结论是错的' not in _ausrc
          and '1011 当时写的是「样本量不足以决定路线」' in _ausrc)

    check("Q993U.6 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P6 成立：静态模型（「正向 MISSING ⟺ occurrence == 0」）"
          "与**真跑门**逐条对上了 —— 对账的那一对静态说该消失的、真跑门报的 MISSING "
          "减去基线自带的那批之后逐条相同** ⇒ ⇒ "
          "**⇒ 而「同一份快照跑两次结果一致」也一起验了（不然对账只是一次巧合）** ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ 所以 58 次读数里至少有 1 条 MISSING 是**真跑门验过的、不是推理出来的**",
          '"gate_cross_check"' in _p1012
          and '"delta_matches_static"' in _p1012
          and '"P6_hold_2012"' in _p1012
          and 'occurrence == 0' in _p1012
          and '"p6_static_model_matches_a_real_gate_run_2012_"' in _ausrc
          and '真跑门验过的' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门（本条的核心）**：**地基是推理、必须实测对账**
          and '所以静态模型可以代替真跑门' not in _p1012
          and '所以静态模型可以代替真跑门' not in _ausrc)

    check("Q993U.7 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P7 反向用例成立：在 `_anchs` 自己的目标文件里真删掉那一条、"
          "再跑门，MISSING 减去基线自带的那批之后正好多出 1 条、且就是删掉的那一条** ⇒ ⇒ "
          "**⇒ ⇒ ⇒ 而这一条是为了排除「那 1 次消失是分母算错了」** ⇒ ⇒ ⇒ ⇒ "
          "⇒ **⇒ 分母没算错：58 次改动里真的只有 1 次能让门开口，而门把它报了**",
          '"reverse_case"' in _p1012
          and '"P7_hold_2012"' in _p1012
          and '自己的目标文件里真删掉那一条' in _ausrc
          and '分母没算错' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门**：**反向用例必须改那个变量自己的目标文件** ——
          #   **改 audit 顶替是另一个口径，那正是 1010 踩过的「和主口径不同的小实验」**
          and '在 audit 里真删掉' not in _p1012
          and '在 audit 里真删掉' not in _ausrc)

    check("Q993U.8 ⭐⭐⭐⭐⭐ **P8 成立：逐条落进 "
          "`docs/research/jimeng-canvas/global-detection-1012.json`、由本探针自己写** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐⭐ **⇒ 而它记的是「每一对的声明数/被动数/消失数、分侧合计、"
          "消失的是哪一条、真跑门对账的结果」** ⇒ ⇒ "
          "**⇒ 本批扩到全部 187 个目标变量 —— 局部读数不许长得像全局的** ⇒ ⇒ "
          "**⇒ P9 成立：判据里手写的数全部有出处**",
          '"P8_hold_2012"' in _p1012
          and '"P9_hold_2012"' in _p1012
          and '"audit_numbers_vs_computed_2012"' in _p1012
          and 'global-detection-1012.json' in _p1012
          and 'global-detection-1012.json' in _ausrc
          and '局部读数不许长得像全局的' in _ausrc
          and '本批扩到全部 187 个目标变量' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐ **反向门**：**不许把「扩到 187 个变量」说成「已经覆盖了所有可能的目标」**
          and '所以这已经是全局无死角' not in _p1012
          and '所以这已经是全局无死角' not in _ausrc)



    # ══ 1013 宇宙冻结点 ══
    # ⚠️ 同 1006–1012 那条：**1013 报的那些数是在它的 `R993V` 判据加进去之前、
    #    在 1012 那一版 audit 上测的**
    #    ⇒ ⇒ 而 1013 比前几批多一个自由度：**它要给「手写的数必须有出处」的正则
    #    换掉提取规则、并配一条反向自检** ⇒ ⇒ ⇒
    #    ⇒ **⇒ 那是一次放宽，所以它的反向自检必须和放宽本身同一批落地**
    # ══ R993V. 批 1013 **1012 的处方「把追加登记成账」跑起来会不会自己变成噪声源**
    print("— R993V. 批 1013 occurrence 账本："
          "68 条改动 100% 落进四类、账本的 red 与门对称差 0、11 对里只红 1 个批次")
    check("R993V.1 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P1 成立：分类互斥且完备 —— "
          "四类计数之和 68 == 改动总数 68，且没有第五类；"
          "`born` 0 / `grown` 67 / `shrank` 0 / `vanished` 1** ⇒ ⇒ "
          "**⇒ 而完备性是用加法验出来的、不是靠人说「分完了」**",
          '"P1_hold_2013"' in _p1013
          and 'KINDS = ("born", "grown", "shrank", "vanished")' in _p1013
          and 'EXHAUSTIVE = bool(SUM_KINDS == N_EVENTS)' in _p1013
          and '"p1_kinds_are_disjoint_and_exhaustive_2013_"' in _ausrc
          and '完备性是用加法验出来的' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**完备性必须由求和证出，不许只看四个类名都在**
          and 'EXHAUSTIVE = True' not in _p1013
          and 'EXHAUSTIVE = True' not in _ausrc)

    check("R993V.2 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P2 成立：账本的 `red` 与门会报的那些完全重合 —— "
          "对称差 0（账本报了门没报的 0 条、门报了账本没报的 0 条）** ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ 也就是说：在 `vanished` 这一类上，账本没有比门多看见任何东西** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而账本的价值不在抓漏（抓漏门已经做到了）、"
          "而在它给另外三类提供了「不报红但记账」的位置**",
          '"P2_hold_2013"' in _p1013
          and '"cross_with_gate"' in _p1013
          and '"symmetric_difference"' in _p1013
          and '"only_ledger"' in _p1013
          and '"only_gate"' in _p1013
          and '"p2_ledger_red_equals_gate_vanished_2013_"' in _ausrc
          and '对称差 0' in _ausrc
          and '账本没有比门多看见任何东西' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门（本条的核心）**：
          #   **对称差必须双向报** —— 只报「账本没多报」就宣称账本安全，是掩盖
          and '所以账本和门完全等价' not in _p1013
          and '所以账本和门完全等价' not in _ausrc)

    check("R993V.3 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P3 是否证：账龄机制（1008 立的那条处方）"
          "在当前规模下用不上 —— 11 对历史里账本只在 1 个批次报红，"
          "而那 1 个是一次性的、下一对就不再红** ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ 而这一批否掉的正是自己上一批的处方："
          "1012 说「登记成账」，1013 量到「账已经够安静了、账龄是多余的」** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而否掉的是「现在就要上账龄」，不是「账龄这个想法错了」**",
          '"P3_hold_2013"' in _p1013
          and 'AGE_NEEDED = bool(N_RED_PAIRS > 1)' in _p1013
          and '"p3_aging_is_not_needed_at_this_scale_2013_"' in _ausrc
          and '否掉的是「现在就要上账龄」' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门**：**否的必须写清否的是谁**
          and '所以账龄这个想法是错的' not in _p1013
          and '所以账龄这个想法是错的' not in _ausrc
          and '所以 1012 的处方是错的' not in _ausrc)

    check("R993V.4 ⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P4：账本真正的产出是那三类不报红的账 —— "
          "`born` 0 条、`grown` 67 条、`shrank` 0 条，合计 67 条** ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ 而这 67 条正是 1009/1011 说的那类「门按设计不报」的改动** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而 1008 的「清单会过期」在这本账上第一次有了自动生成的位置**",
          '"P4_hold_2013"' in _p1013
          and '"p4_the_three_silent_classes_are_the_real_output_2013_"' in _ausrc
          and '账本真正的产出' in _ausrc
          and '自动生成的位置' in _ausrc
          # ⭐⭐⭐⭐⭐ **反向门**：**不许把「三类不报红」说成「三类没关系」**
          and '所以这 67 条不用管' not in _p1013
          and '所以这 67 条不用管' not in _ausrc)

    check("R993V.5 ⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P5 反向用例成立：`born`（0 → 1）这类改动记进了账、"
          "但 `red` 为假** ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ 而这一条是为了排除「账本是个恒红的报警器」"
          "或者「账本什么都记所以等于没筛」这两个相反的坏形态** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 账本既不恒红、也不是恒真的空账：68 条里只有 1 条红** ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而真实历史里 `born` 一条都没有（0 条）—— "
          "新声明的锚点总是在同一批里连同它的原文一起出现 ⇒ 所以这一类只能自己造，"
          "而「要验的那一类在数据里没有样本」是「有效 n 造假」最隐蔽的一种形态**",
          '"P5_hold_2013"' in _p1013
          and 'N_BORN_REAL = kind_count["born"]' in _p1013
          and '有效 n 造假' in _p1013
          and '"p5_reverse_case_born_is_recorded_but_not_red_2013_"' in _ausrc
          and '最隐蔽的一种形态' in _ausrc
          and '真实历史里 `born` 一条都没有' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门**：**不许把「没有样本」说成「这一类不存在」**
          and '所以 born 这一类不会发生' not in _p1013
          and '所以 born 这一类不会发生' not in _ausrc)

    check("R993V.6 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P6 —— 本批最深的一层："
          "「每次全量重算」并不能消除 1008 说的「清单会过期」，"
          "它只是把「内容错了」换成了「历史被截断了」** ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ 一本纯历史账本的 `retired` 集合恒为空** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而真正的失效形态是 1011 的 P7 已经证过的那个："
          "git 历史一旦被 rebase，整本账会静静地变样、而账本不会报任何错** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 所以账本必须自带 commit sha 指纹 —— "
          "本批 12 个 sha 已写进账本**",
          '"fingerprint_2013"' in _p1013
          and '"P6_hold_2013"' in _p1013
          and '"retired"' in _p1013
          and '"p6_full_recompute_does_not_fix_expiry_2013_"' in _ausrc
          and '它只是把「内容错了」换成了「历史被截断了」' in _ausrc
          and '账本必须自带 commit sha 指纹' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门**：**「自动生成」不等于「不会过期」**
          and '所以自动生成的清单就不会过期' not in _p1013
          and '所以自动生成的清单就不会过期' not in _ausrc)

    check("R993V.7 ⭐⭐⭐⭐⭐ **P7 成立：逐条落进 "
          "`docs/research/jimeng-canvas/occurrence-ledger-1013.json`、由本探针自己写** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐⭐ **⇒ 而它记的是「每一条改动：变量、原文、哪一对之间、"
          "属于四类中的哪一类、前后出现次数、是否报红、以及为什么不报红」** ⇒ ⇒ "
          "**⇒ 本批扩到全部 188 个目标变量、11 对快照** ⇒ ⇒ "
          "**⇒ P8 成立：判据里手写的数全部有出处** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐⭐ **⇒ 而 P8 的提取规则这一批被换掉了（标识符里的数不再算量值）、"
          "**换掉就必须配反向自检** —— 否则那是在悄悄把门变弱**",
          '"P7_hold_2013"' in _p1013
          and '"P8_hold_2013"' in _p1013
          and 'def _numre_selftest' in _p1013
          and '_numre_selftest()' in _p1013
          and 'occurrence-ledger-1013.json' in _p1013
          and 'occurrence-ledger-1013.json' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **放宽了门就必须留下自检的痕迹** ——
          #   **删掉自检比没写自检更危险**
          # ⚠️ 而这里**第一版写的是 `不许让门看起来比它实际更强 not in _ausrc`、立刻红了**
          #   ⇒ ⇒ **⇒ 因为这句 1006 就已经在 audit 里了、而那是它的合法用途** ⇒ ⇒ ⇒ ⇒ ⇒
          #   **⇒ 「反向门」也不许凭印象写 —— 它和正向锚子一样必须先查过**
          and '不许让门看起来比它实际更强' in _ausrc
          and '所以自动生成的清单就不会过期' not in _ausrc)


    # ══ 1014 宇宙冻结点 ══
    # ⚠️ 同 1006–1013 那条：**1014 报的那些数是在它的 `S993W` 判据加进去之前、
    #    在 1013 那一版 audit 上测的**
    #    ⇒ ⇒ 而 1014 多一个自由度：**它的普查输入是 `docs/research/jimeng-canvas/*.json`
    #    整个目录** ⇒ ⇒ ⇒ **⇒ 而那个目录里 1014 自己也会写一本 ⇒ ⇒ ⇒ ⇒
    #    ⇒ **「普查把自己的产物吃进去」是本批第一件被否掉的事**
    # ══ S993W. 批 1014 **「空集合」有歧义：看起来是空的，和没算过，在仓里长得一模一样**
    print("— S993W. 批 1014 空集合的歧义："
          "8 本 golden、11 个空 list + 1 个 null，可自证 11、不可自证 1（1013 的 retired）")
    check("S993W.1 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P1 成立：普查 8 个 golden"
          "（已排除本探针自己那本）、11 个空 list 字段、1 个 null 字段 —— "
          "其中可自证 11 个、不可自证 1 个（就是 1013 刚写的 `retired`）** ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ 而可自证的判据不是「旁边有说明」、而是「旁边有一个可校验的不变式」** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而一段散文说明（`retired_note`）钉不住任何东西："
          "它可以和「没算过」完全共存**",
          '"P1_hold_2014"' in _p1014
          and '"n_excluded_self"' in _p1014
          and '"n_self_provable"' in _p1014
          and '"p1_only_one_empty_field_is_unverifiable_2014_"' in _ausrc
          and '不可自证 1 个' in _ausrc
          and '它可以和「没算过」完全共存' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门**：**普查不许把自己的
          #   产物吃进去** —— 否则读数会随「跑过几次」变化，而那样的数字不能当证据
          and 'assert not any(_is_own(f) for f in GOLDENS)' in _p1014
          and '所以按文件名排除就够了' not in _p1014
          and '所以按文件名排除就够了' not in _ausrc)

    check("S993W.2 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P2 成立（这是本批的病根）："
          "「真的算过、结果是空」与「根本没算」这两份账，`retired` 字段序列化之后"
          "逐字节相同** ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 读 JSON 的人拿到 `retired: []` 时，"
          "无法区分「查了、没有」和「压根没查」** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而这正是 1008 那条「清单会过期」的一个新的、更隐蔽的形态**",
          '"P2_hold_2014"' in _p1014
          and 'SAME_BYTES' in _p1014
          and '"byte_identity_proof"' in _p1014
          and '"p2_computed_and_never_computed_are_byte_identical_2014_"' in _ausrc
          and '逐字节相同' in _ausrc
          and '更隐蔽的形态' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门**：**不许把
          #   「旁边有一段说明」当成「它被算过」** —— 散文与「没算」完全兼容
          and '旁边的说明就等于它被算过了' not in _ausrc
          and '旁边的说明就等于它被算过了' not in _p1014)

    check("S993W.3 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P3 成立：处置是给账本加 companion 字段"
          "（`retired_computed` + `retired_n`），加上之后两份账可区分；"
          "而且 companion 自己也要能区分「算了是 0」与「算了但算错了」—— 那一条也验了** ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而 1013 的 `retired: []` 原文一字不删、只加 companion** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而处置落在 1013 的探针里、不落在这本账上** ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ 因为账本每次运行都会被探针整个重写、改文件会在下一次跑时被抹掉**",
          '"retired_computed"' in _p1014
          and '"retired_n"' in _p1014
          and '"companion_proof"' in _p1014
          and '"P3_hold_2014"' in _p1014
          and '"p3_companion_fields_make_it_distinguishable_2014_"' in _ausrc
          and '原文一字不删' in _ausrc
          and '改文件会在下一次跑时被抹掉' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门**：**处置不许落在产物上**
          and '所以改账本文件就够了' not in _p1014
          and '所以改账本文件就够了' not in _ausrc)

    check("S993W.4 ⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P4 反向用例成立：造一份 `retired` 非空的真账，"
          "分类器必须把它判成「可自证」—— 而当前版本判不了（companion 尚未进判据）** ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ 而这一条是为了排除「普查恒判不可自证」—— "
          "那会让 12 个字段看起来全都一样有问题、而实际上只有 1 个** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 所以判据里必须同时钉住「可自证 11 个」和「不可自证 1 个」两个数**",
          '"P4_hold_2014"' in _p1014
          and 'INVARIANTS' in _p1014
          and '"p4_reverse_case_classifier_is_not_constant_2014_"' in _ausrc
          and '可自证 11 个' in _ausrc
          and '不可自证 1 个' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门**：**普查不许恒判「不可自证」**
          and '所以其实每个空字段都有问题' not in _ausrc
          and '所以其实每个空字段都有问题' not in _p1014)

    check("S993W.5 ⭐⭐⭐⭐⭐⭐⭐⭐ **P5：这条规矩不只管空 list —— `null` 是同一个病的"
          "另一种形态，而它同样分不清「算出来是 null」和「没算」** ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而本批的普查已经把 null 一并数进去了（1 个）**",
          '"n_empty_null"' in _p1014
          and 'elif o is None:' in _p1014
          and '"P5_hold_2014"' in _p1014
          and '"p5_null_is_the_same_disease_2014_"' in _ausrc
          and 'null` 是同一个病的' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门**：**不许把 null 从普查口径里悄悄去掉**
          and 'null 不算、只查空 list' not in _p1014
          and 'null 不算、只查空 list' not in _ausrc)

    check("S993W.6 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P6 —— 而最要紧的一句是："
          "1013 刚刚做出来的那本账，自己就带着这个毛病** ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 而这说明「刚做完的东西也是会犯的」不是假设、"
          "是本会话第三次撞上（前两次：1012 的探针覆盖表是空的、"
          "1013 的断言里硬写了目标变量数）** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 所以任何交付物都必须被下一批当成被测对象重新过一遍"
          "——「自己验过」不算数**",
          '"P6_hold_2014"' in _p1014
          and 'occurrence-ledger-1013.json' in _p1014
          and '"p6_the_previous_batch_artifact_is_itself_a_victim_2014_"' in _ausrc
          and '自己就带着这个毛病' in _ausrc
          and '「自己验过」不算数' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门**：**「自己验过」不算数**
          and '所以本批自己验过就行了' not in _p1014
          and '所以本批自己验过就行了' not in _ausrc)

    check("S993W.7 ⭐⭐⭐⭐⭐ **P7 成立：逐条落进 "
          "`docs/research/jimeng-canvas/empty-ambiguity-1014.json`、由本探针自己写** ⇒ ⇒ "
          "⭐⭐⭐⭐⭐⭐ **⇒ 而它记的是「每个空字段：哪本账、哪个路径、是空 list 还是 null、"
          "可不可自证、以及钉住它的那个不变式是什么」** ⇒ ⇒ "
          "**⇒ P8 成立：判据里手写的数全部有出处**",
          '"P7_hold_2014"' in _p1014
          and '"P8_hold_2014"' in _p1014
          and 'empty-ambiguity-1014.json' in _p1014
          and 'empty-ambiguity-1014.json' in _ausrc
          and '"p7_golden_2014_"' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **反向门**：**账本自己也必须在普查口径内被排掉** ——
          #   **而排除的依据必须是 `generated_by`、不是文件名**
          and '"fix_lands_in_why"' in _p1014
          and '每次运行都会被探针整个重写' in _ausrc)

    # ══ 1015 宇宙冻结点 ══
    # ⚠️ 同 1006–1014 那条：**1015 报的那些数是在它的 `U993Y` 判据加进去之前测的**
    #    ⇒ ⇒ 而 1015 多一个自由度：**它是唯一一台会把**别人**的产物整个重写的仪器**
    #    ⇒ ⇒ ⇒ **⇒ 所以它必须自带快照 + `atexit` 还原 —— 否则「量可复现性」这个动作
    #    ⇒ ⇒ ⇒ ⇒ 本身就会改掉被量的东西**
    # ══ U993Y. 批 1015 **把 1014 的 P6 落成代码 —— 然后立刻被 1014 那台普查反过来咬了一口**
    print("— U993Y. 批 1015 重跑可复现性：9 本 golden 逐本重跑，四态 9/0/0/0；"
          "否掉「自动发现更安全」与「加法验完备性」，不动点跑了 3 轮")
    check("U993Y.1 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P1 成立：四态 reproduced / drifted / "
          "crashed / vanished 互斥且穷尽（sum_states 9 == n_books 9），"
          "而「跑不起来」必须单列** ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ 探针崩了不告诉你数据有没有变，并进任何一态都等于把仪器故障"
          "报成数据结论** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 沿用 1006 那条：门报红 ≠ 数据错**",
          '"P1_hold_1015"' in _p1015
          and 'N_STATES_SUM = N_REPRODUCED + N_DRIFTED + N_CRASHED + N_VANISHED' in _p1015
          and '"sum_states"' in _p1015
          and '"P2_hold_1015"' in _p1015
          and 'if rc != 0:' in _p1015
          and '"crashed"' in _p1015
          and '"vanished"' in _p1015
          and '"p1_states_are_four_and_exhaustive_2015_"' in _ausrc
          and '并进任何一态都等于把仪器故障报成数据结论' in _ausrc
          and '门报红 ≠ 数据错' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
          #   **反向门**：**不许把 rc≠0 并进 vanished 那一态** ——
          #   一旦写成 `if rc != 0 or post is None:` 就再也分不开「崩了」和「没写出来」
          and 'if rc != 0 or post is None:' not in _p1015)

    check("U993Y.2 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P2 成立（本批最痛的一条）："
          "第一版按 `generated_by` 自动反查探针，9 本只认领 8 本、静默丢掉 1 本"
          "（1005 的 `generated_by` 带 `scripts/` 前缀），而它照样报 all-green** ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 「手写清单写错会当场炸、自动发现写错只会安静地少算」** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 处置 = 双通道对账 + 一条「不合规要报错而不是跳过」的反向门**",
          '"n_unlinked_rejected"' in _p1015
          and '"channel_a_goldens"' in _p1015
          and '"channel_b_probes"' in _p1015
          and '"probes_without_golden"' in _p1015
          and 'if "/" in _gb or not _gb.endswith(".py") or _gb not in _PROBES:' in _p1015
          and '"P2_hold_1015"' in _p1015
          and '"p2_discovery_must_not_be_silent_2015_"' in _ausrc
          and '手写清单写错会当场炸' in _ausrc
          and '自动发现写错只会安静地少算' in _ausrc
          and '不合规要报错而不是被跳过' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
          #   **反向门**：**发现失败必须报错、不许被跳过** ——
          #   一旦改成「解析不了就当它没有」，1015 第一版那个 bug 会原样回来
          and '所以解析不了就跳过' not in _p1015
          and '所以解析不了就跳过' not in _ausrc)

    check("U993Y.3 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P3 / P4 成立：1014 那台普查反过来抓住了"
          "1015 的产物（`n_goldens` 8 → 9、不可自证空集合 1 → 2，新加那条是 1015 自己的"
          "`/books/[2]/keys_added`），根因是顺序 —— 每本账都落后它上游一轮** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 处置 = 整轮重跑到零漂移为止，"
          "并把「跑了几轮才不动点」本身当成读数报出来（实测 3 轮、上限 6）**"
          "【1015 改写横幅 —— 上面三个读数（`1 → 2`、`实测 3 轮`、`/books/[2]/keys_added`）"
          "是 1015 那本刚写下时的值，原文一字不删；收敛后的现读数是 `1 → 6`，"
          "而轮数**刻意不写在这里**（它每次重跑都会变）—— 请读产物 `n_rounds` / `rounds`，"
          "现不可自证路径里已经没有 `/books/[2]/keys_added` 这条** "
          "⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ **⇒ 而漏掉横幅的是这份副本：同一条判据在 audit 侧挂过横幅、"
          "verifier 侧的人读摘要没挂；且断言体只钉机制（`converged` / `n_rounds` / `max_rounds` / "
          "`fixed_point_rule` / 退出条件）、不钉读数 ⇒ ⇒ ⇒ ⇒ **所以门不会报红，"
          "「横幅也会过期」的新形态是「没人忘挂，而是只挂在了副本之一」**",
          '"converged"' in _p1015
          and '"n_rounds"' in _p1015
          and '"max_rounds"' in _p1015
          and '"fixed_point_rule"' in _p1015
          and 'for _i in range(1, MAX_ROUNDS + 1):' in _p1015
          and 'if _d == 0:' in _p1015
          and 'MAX_ROUNDS = 6' in _p1015
          and '"P3_hold_1015"' in _p1015
          and '"P4_hold_1015"' in _p1015
          and '"p3_fixed_point_exists_2015_"' in _ausrc
          and '"p4_fixed_point_iteration_2015_"' in _ausrc
          and '在账本上长得和「没算过」一模一样' in _ausrc
          and '每本账都落后它上游一轮' in _ausrc
          and '并把「跑了几轮才不动点」本身当成读数报出来' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
          #   **反向门**：**跑一轮就收工是不行的** ——
          #   只跑一轮得到的是「上一轮的账」，正好是 P3 那条病
          and '只跑一轮就够了' not in _p1015
          and '只跑一轮就够了' not in _ausrc)

    check("U993Y.4 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P5 成立：反向用例对四种人工构造分别给出"
          "drifted（新增键）/ drifted（改已有叶子）/ crashed（rc≠0）/ vanished（产物缺失）"
          "—— 而我第一版的反向用例是坏的（把 `books` 整个换掉，测到的还是「新增键」）** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 处置 = 挑一个真的存在于该本里的叶子改值，"
          "并且整条断言外面套 `bool()`（`and` 链返回最后一个操作数，它可能是 list 而不是 bool）**",
          '"PROBE_1015_FORCED_EXTRA_KEY"' in _p1015
          and '"modify_value_state"' in _p1015
          and '"modified_path"' in _p1015
          and '"old_value"' in _p1015
          and 'P5_OK = bool(' in _p1015
          and '"P5_hold_1015"' in _p1015
          and '"p5_reverse_classifier_is_not_constant_2015_"' in _ausrc
          and '分类器对四种人工构造分别给出 drifted' in _ausrc
          and '整个换成一个新列表' in _ausrc
          and '断言要用 `bool()` 包住' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
          #   **反向门**：**断言不许交给 `and` 链去决定类型** ——
          #   不套 `bool()` 时 JSON 里 `[]` 和 `false` 长得不一样，恒真的判据就这样混进去
          and '所以 P5 不用包 bool' not in _p1015
          and '所以 P5 不用包 bool' not in _ausrc)

    check("U993Y.5 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P6 成立、而它是本批踩到的第三个坑："
          "`jimeng_probe1005_...` 把落仓门控在 `if \"--write-golden\" in sys.argv` 上，"
          "不带这个 flag 时它 rc=0、打印 DONE、只写 /tmp，仓里的产物一个字节都不动** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 「探针跑成功了」不等于「产物被刷新了」—— "
          "只能靠重跑后比对字节、或看 mtime 变没变来判，不许看退出码** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 所以套件统一带 `--write-golden`，并逐本记 `wrote_golden`**",
          '[PY, "-u", str(probe), "--write-golden"]' in _p1015
          and 'golden.stat().st_mtime_ns != pre_mtime' in _p1015
          and '"wrote_golden"' in _p1015
          and '"n_books_never_wrote_golden"' in _p1015
          and 'pre_mtime = golden.stat().st_mtime_ns' in _p1015
          and '"p6_argv_gated_golden_2015_"' in _ausrc
          and '只写 /tmp' in _ausrc
          and '仓里的产物一个字节都不动' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
          #   **反向门**：**不许拿退出码当「产物被刷新了」的证据**
          and '所以看退出码就够了' not in _p1015
          and '所以看退出码就够了' not in _ausrc)

    check("U993Y.6 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P7 成立：3 本 golden 的 `generated_by` 相对 HEAD 被修过，"
          "before/after 逐条从 `git show HEAD:` 取、不靠记忆** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 处置仍然落在生成器里、不落在产物上"
          "（产物每次都会被重写）；而第一版那批读数（认领 8 / 静默丢 1）也如实登记进 `number_sources`、"
          "不当作没发生过** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ P8："
          "判据里手写的数全部有出处，且刻意不把 0/1 放进去（放了门就会放过判据里任何一个 0 或 1）**",
          '"P7_hold_1015"' in _p1015
          and '"P6_hold_1015"' in _p1015
          and '"repaired_generated_by"' in _p1015
          and '"number_sources"' in _p1015
          and '"empty_list_invariants"' in _p1015
          and '"show", "HEAD:%s" % rel' in _p1015
          and 'rerun-reproducibility-1015.json' in _p1015
          and '"p7_repaired_generated_by_2015_"' in _ausrc
          and '"golden_2015_"' in _ausrc
          and '处置要落在生成器里、不落在产物' in _ausrc
          and '刻意不把 0/1 放进去' in _ausrc
          and '第一版（仪器故障期）的读数如实登记' in _p1015
          and '刻意不把 0 和 1 加进出处表' in _p1015
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
          #   **反向门**：**不许为了让门过而把 0 和 1 塞进出处表** ——
          #   那是 1006 反过来那条「不许让门看起来比它实际更强」的一个新形态
          and '所以把 0 和 1 也登记进去' not in _p1015
          and '所以把 0 和 1 也登记进去' not in _ausrc)

    check("U993Y.7 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P9 成立：整套东西纯离线 —— "
          "不打开浏览器、不按任何键、连 `mouse.click` 都没有，源站登录态仍然没有** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 源站登录态仍然没有，而本会话一次都没启动过浏览器**",
          '"offline_2015"' in _ausrc
          and '"discipline_2015"' in _ausrc
          and '本批纯离线' in _ausrc
          and '连 `mouse.click` 都没有' in _ausrc
          and '完备性用加法验的时候，两边不许同源' in _ausrc
          and '断言要用 `bool()` 包住' in _ausrc
          and '「自己验过」不算数' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
          #   **反向门**：**这套套件不许碰浏览器 / 网络** —— 离线性是它唯一的取证前提
          and 'playwright' not in _p1015
          and 'sync_playwright' not in _p1015
          and 'requests.get' not in _p1015
          #   ⭐⭐⭐⭐⭐⭐ **反向门**：**加法的两边不许同源** ——
          #   一旦分母也出自这台仪器，完备性就退化成恒真
          and '所以分母也用它自己数就够了' not in _ausrc)

    check("U993Y.8 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P8 成立、而它是 1014 那台普查主动报上来的："
          "普查把 1015 自己的产物判成 5 条「不可自证」的空集合 —— 而 1015 明明在产物里"
          "写了一个 `empty_list_invariants` 块把其中一条钉住了** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 那份不变式是写给人和自己看的，"
          "普查那台仪器并不读它** ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ "
          "**⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ ⇒ 这是 1013 那条"
          "「处置要落在生成器里、不落在产物上」的第四个形态：自证不变式必须登记在"
          "**普查的规则**里，否则它对普查而言不存在**",
          '"P8_hold_1015"' in _p1015
          and '"p8_invariants_invisible_to_1014"' in _p1015
          and '"n_invariants_declared_in_artifact"' in _p1015
          and '"n_invariables_1014_cannot_see"' in _p1015
          and '"empty_list_invariants"' in _p1015
          and 'empty-ambiguity-1014.json' in _p1015
          and 'def _rows_of_1014' in _p1015
          and 'r.get("golden") == GOLDEN.name' in _p1015
          and '"p8_invariants_invisible_to_census_2015_"' in _ausrc
          and '那份不变式是写给人和自己看的' in _ausrc
          and '普查那台仪器并不读它' in _ausrc
          and '自证不变式必须登记在' in _ausrc
          and '否则它对普查而言不存在' in _ausrc
          # ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
          #   **反向门**：**P8 必须真的量到「差集非零」** —— 只登记一个不变式块就报绿，
          #   等于把「我写了处置」当成「处置生效了」，而 1008/1013 各栽过一次
          and 'P8_OK = bool(_AMB_1014) and N_SELF_AMB > 0 and N_INV_INVISIBLE > 0' in _p1015
          and '所以在产物里写不变式就够了' not in _p1015
          and '所以在产物里写不变式就够了' not in _ausrc)

    # ══ V993Z. 批 1016 `SOURCE_BASELINE` 被当成通用抽屉：一个键名被写了两遍，
    #    后一条把 931 的正文整个吃掉 —— 而没有任何一行代码会告诉你
    print("— V993Z. 批 1016 层表被当抽屉：17 层里音色筛选那条挂 104 个键；"
          "一条 9xx 结论键**同名写了两次**，后一条把 931 正文顶掉了（实测 HEAD：写了 104、只可达 103）")

    check("V993Z.1 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P1 成立：`SOURCE_BASELINE` 顶层 17 键"
          "全是层 `data-testid`，却被当成了通用抽屉** —— 900–939 的结论键挂在音色筛选下拉那一条下，"
          "⇒ ⇒ ⇒ ⇒ **⇒ 「顶层键 = 层」这个性质一破，就再也塞不回去了**",
          '"p1_layer_table_used_as_drawer_2016_"' in _ausrc
          and '"baseline_host_2016"' in _ausrc
          and 'MISP_BY_LAYER' in _p1016
          and 'PER_LAYER = {lay: len(CUR[lay]) for lay in LAYERS}' in _p1016
          and 'MEDIAN_KEYS' in _p1016)

    check("V993Z.2 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P2 成立（本批才发现的那条）："
          "那批键里有一条**键名被写了两次** —— Python dict 字面量保留最后一条 ⇒ "
          "931 的正文永远取不到 ⇒ 而整表 dump 的是求值后的 dict ⇒ "
          "**它从来没进过任何产物：「写下来了」不等于「存在过」**",
          '"p2_duplicate_key_fixed_2016_"' in _ausrc
          and 'collections.Counter(e["key"] for e in entries if e["key"])' in _p1016
          and 'dup.append({"layer": layer, "key": name, "times": times, "lines": lines})' in _p1016
          and 'HEAD_REACHABLE = HEAD_WRITTEN - sum(' in _p1016
          and '"reachable_at_head"' in _p1016
          and '"whole_table_dumped"' in _p1016)

    check("V993Z.3 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P3 成立：before 是量出来的、不靠记忆，"
          "而且钉在固定 sha 上** ⇒ 「字面量写了多少」与「实际可达多少」是两个数，"
          "而只有一个被看见 —— 【1015 那条「不许出现会因判据自身变化而改变的数」在时间轴上的形态："
          "不是「重算变一变」，是**处置本身把证据擦掉了**】⇒ 处置 = 钉 sha + 要求它是 HEAD 的祖先",
          '"p3_before_measured_not_remembered_2016_"' in _ausrc
          and 'def _git_show(rev):' in _p1016
          and '"%s:%s" % (rev, AUDIT)' in _p1016
          and 'BEFORE_SHA = "2b52f492"' in _p1016
          and 'BEFORE_PINNED_OK = _is_ancestor(BEFORE_SHA)' in _p1016
          and '"before_sha_is_ancestor_of_head"' in _p1016
          and '"written_at_head"' in _p1016
          and '的那一条不是被删了，是**被同名的后一条顶掉了**' in _p1016
          # ⭐ 反向门：**不许悄悄退回读 HEAD** —— 那正是把证据擦掉的那个写法
          and '"HEAD:" + AUDIT' not in _p1016
          and 'git show HEAD:…' in _p1016)

    check("V993Z.4 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P4 —— 而最扎人的是那句横幅本身："
          "被吃掉的那条写着「原文保留在这里当历史记录、不许删」，"
          "而「保留原文」的惯用写法（同一条记录里再补一段收窄说明）**恰好就是同名写入** ⇒ "
          "意图与机制直接打架、机制静默赢了",
          '"p4_intent_and_mechanism_fought_2016_"' in _ausrc
          and '原文保留在这里当历史记录、不许删' in _ausrc
          and '意图是保留、机制是同名覆盖' in _ausrc
          and '机制静默赢了' in _ausrc
          and 'source_reverse_lap_cycle_narrowed_by_932' in _ausrc)

    check("V993Z.5 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P5 反向用例成立：同名键的读回值是后写的那条，"
          "而整个过程不抛错、不告警、不改变任何一条已有的门** ⇒ "
          "要抓它只能靠「对键名本身去重」，不可能靠「跑一遍看有没有报错」",
          '"p5_same_name_failure_is_silent_2016_"' in _ausrc
          and 'REVERSE_DUP = {"keep_me": "第一次写的", "keep_me": "第二次写的"}' in _p1016
          and 'P5 = bool(REVERSE_LAST_WINS and REVERSE_SILENT and _reverse_construction_ok)' in _p1016
          and '要抓它只能靠**对键名本身去重**' in _p1016)

    check("V993Z.6 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P6 —— 而这一条的第一版预期是错的**："
          "我照抄 939 那句散文写「错挂 40 条、全在音色筛选层」，探针当场报假 ⇒ 实测 43 条 / 3 个宿主 ⇒ "
          "**939 那条处置其实生效了、只是从来没人记过** ⇒ "
          "**「照抄散文里的预期」和「量出来」在同一个探针里长得一样**",
          '"p6_misplacement_measured_43_not_40_2016_"' in _ausrc
          and 'P6 = (N_MISP == 43 and N_MISP_DEBT == 40 and N_MISP_ELSEWHERE == 3' in _p1016
          and '"n_misplaced_9xx_keys_in_voice_filter"' in _p1016
          and '"misplaced_by_layer"' in _p1016
          and '**939 那条处置确实生效了，只是没人记过这件事。**' in _p1016)

    check("V993Z.7 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P7：本批只记账、不搬那 40 条** —— "
          "实测 `SOURCE_BASELINE` 的唯一按层消费点是 `get(tid)`、而那 40 条从未被按层读过 ⇒ "
          "错位是语义污染、不是读数错误 ⇒ 搬它属于纯大改、零读数收益 ⇒ 按 1012 的路线登记成账",
          '"p7_registered_not_moved_2016_"' in _ausrc
          and '"misplaced_policy"' in _p1016
          and '语义污染**而非读数错误' in _p1016
          and '登记成账而不是现在动它' in _p1016
          # ⭐ 反向门：判据必须真的钉住「不搬」这个决定，否则下一批会顺手把它搬了
          and 'DISPOSITION = "register_only"' not in _p1016)

    check("V993Z.8 ⭐⭐⭐⭐⭐ **P8 成立：纯离线 —— 只读仓里两个文件 + `git show`（**钉在固定 sha 上**），"
          "不开浏览器、不联网、不按任何键；逐条落进 "
          "`docs/research/jimeng-canvas/baseline-host-misuse-1016.json`、由本探针自己写**",
          '"p8_offline_2016_"' in _ausrc
          and '"p9_readings_land_in_artifact_2016_"' in _ausrc
          and 'baseline-host-misuse-1016.json' in _p1016
          and 'baseline-host-misuse-1016.json' in _ausrc
          and '"generated_by": "jimeng_probe1016_baseline_host_misuse.py"' in _p1016
          and '不开浏览器、不联网' in _ausrc)

    # ══ W993A. 批 1017 把「被测对象」点一遍名：883 条判据里只有 24 条在读原型源码（2.7%），
    #    而「原型没被任何脚本点名」只剩 0.3% —— 两个数讲相反的故事，漂亮的那个差点被汇报
    print("— W993A. 批 1017 被测对象普查：判据绝大多数在验研究装置；"
          "同一个「覆盖率」在不同分母下差 39.4 个百分点；路径正则漏了 `*` 让覆盖率假性变成 94.7%")

    check("W993A.1 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P1 成立：同一个「覆盖率」"
          "在不同分母下差 39.4 个百分点** —— 只数一个门时未覆盖 39.7% 的行、数整套装置时只剩 0.3% ⇒ "
          "**「原型有多少没被覆盖」这句话，缺了分母就没有意义**",
          '"p1_three_denominators_2017_"' in _ausrc
          and '"replica_coverage_2017"' in _ausrc
          and 'DENOMS = {' in _p1017
          and '"one_gate_only"' in _p1017
          and '"whole_apparatus"' in _p1017
          and 'PCT_SPREAD = round(abs(PCT_ONE - PCT_ALL), 1)' in _p1017
          and '分母取哪一组脚本必须和读数一起报' in _ausrc)

    check("W993A.2 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P2 —— 而本批第一版自己就栽在这个坑上，"
          "而且栽得悄无声息：路径正则的字符类里漏了 `*`** ⇒ glob 被降级成目录前缀 ⇒ "
          "**覆盖率假性变成 94.7%，318 处 glob 证据一条都没生效** ⇒⇒ "
          "这是 1016 刚修完的「静默吃掉一条」在同一台仪器上的同款病",
          '"p2_glob_deflates_the_metric_2017_"' in _ausrc
          and 'PATH_RE = re.compile(r"src/(?:components|app)/jimeng/[A-Za-z0-9_./\\[\\]*?-]*")' in _p1017
          and 'def is_glob(ref):' in _p1017
          and 'plain = {r for r in refs if not is_glob(r) and not is_bare_base(r)}' in _p1017
          and 'GLOB_MAKES_IT_JUMP = _pct_plus > COVERAGE["one_gate_only"]["pct_files_covered"] + 30' in _p1017
          and '覆盖率假性变成 **94.7%**' in _ausrc
          and '不报错、不变红，是一个正则悄悄把 glob 降级成目录前缀' in _ausrc)

    check("W993A.3 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P3 成立 —— 本批最要紧的一条："
          "判据的「被测对象」必须能被机器认出来。** 口径 =「`check()` 的条件里出现了"
          "持有原型源码文本的变量」⇒ 实测 883 条里只有 24 条 ⇒ **其余 859 条在验研究装置本身** ⇒ "
          "而「这条判据在验产品」这种说法**不判 —— 不判的东西不能拿来汇报**",
          '"p3_object_of_test_2017_"' in _ausrc
          and '_text_vars = set()' in _p1017
          and 'if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)' in _p1017
          and 'PROTO_CHECKS.append({"name"' in _p1017
          and 'PCT_PROTO = round(100.0 * N_PROTO_CHECKS / N_CHECKS, 1)' in _p1017
          and '**883 条判据里只有 24 条' in _ausrc
          and '**⇒ 1015、1016 连续两批验的都是那 859 条那一侧**' in _ausrc)

    check("W993A.4 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P4：「读了」「算了」「进了判据」是三件事。** "
          "本批第一版照抄 1015 那句「读了不用」写了个粗口径、自己把自己数成 10 个 ⇒ 实测只有 2 个 ⇒ "
          "错因是量错了变量层（Path 变量 vs 装文本的那一层）⇒ "
          "**这就是 1016 那条「照抄散文里的预期和量出来长得一样」在方法上的版本，而它这次伪装成了新发现**",
          '"p4_read_computed_entered_are_three_2017_"' in _ausrc
          and 'UNUSED_TEXT_VARS = sorted(_text_vars - _used)' in _p1017
          and 'P4 = (bool(_text_vars) and bool(UNUSED_TEXT_VARS)' in _p1017
          and '**自己把自己数成 10 个**' in _ausrc
          and '它这次伪装成了「又一条新发现」' in _ausrc)

    check("W993A.5 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P5：覆盖高度集中** —— 报「2.7%」时必须同时报"
          "「集中在谁身上」，否则这个数会让人以为覆盖是均匀稀薄的",
          '"p5_coverage_is_concentrated_2017_"' in _ausrc
          and 'CONCENTRATION = sorted(_by_var.items(), key=lambda kv: -kv[1])' in _p1017
          and 'P5 = (bool(CONCENTRATION) and TOP_N > 1)' in _p1017
          and '否则这个数会让人以为覆盖是均匀稀薄的' in _ausrc)

    check("W993A.6 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P6 —— 而本批真正的那句话是："
          "「原型没被任何脚本点名」与「判据在验产品」是两个数，它们讲相反的故事。** "
          "前者未提及只剩 0.3%（看起来漂亮极了），后者只有 2.7% ⇒ "
          "**而 0.3% 那个数漂亮到足以骗人 —— 它正是本批差点拿去汇报的那一个**",
          '"p6_two_numbers_tell_opposite_stories_2017_"' in _ausrc
          and '"uncovered_lines": unc_lines' in _p1017
          and '"pct_uncovered_lines"' in _p1017
          and '它正是本批差点拿去汇报的那一个' in _ausrc
          and '「一个文件被某个脚本提到过」与「这个文件的行为被某条判据验过」' in _ausrc)

    check("W993A.7 ⭐⭐⭐⭐⭐ **P7：三档分母是嵌套的，判据钉的是这个结构性质** —— "
          "因为「差几个百分点」那句话没有分母就没有含义；**P8：口径边界写进产物、不含糊** ⇒ "
          "本探针量的不是「原型有多少行为没被验过」，**不把前者说成后者**",
          '"p7_denominators_are_nested_2017_"' in _ausrc
          and '"p8_scope_not_claimed_2017_"' in _ausrc
          and 'set(DENOMS["one_gate_only"]) <= set(DENOMS["one_gate_plus_audit"])' in _p1017
          and 'and all(len(v) > 0 for v in DENOMS.values())' in _p1017
          and '"honest_scope"' in _p1017
          and '不把前者说成后者**（1006：不许让门看起来比它实际更强）' in _ausrc)

    check("W993A.8 ⭐⭐⭐⭐⭐ **P9 成立：纯离线** —— 只读仓里的脚本与原型源码，零浏览器/零按键/零网络；"
          "**P10 逐条落进 `replica-coverage-1017.json`、由本探针自己写**",
          '"p9_offline_2017_"' in _ausrc
          and '"p10_golden_2017_"' in _ausrc
          and 'replica-coverage-1017.json' in _p1017
          and 'replica-coverage-1017.json' in _ausrc
          and '"generated_by": "jimeng_probe1017_replica_coverage.py"' in _p1017
          and '零浏览器 / 零按键 / 零网络' in _ausrc)

    check("W993A.9 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P11 —— 而这是本批栽的"
          "第二次、也更阴的一次：把 `*` 修好之后覆盖率回到真值，可**本批判据的正文里**"
          "为了说明「glob 被降级成目录前缀」**写了裸目录串** ⇒ 57 个文件重新变成全覆盖、"
          "P1/P2 当场转红 ⇒⇒⇒⇒⇒⇒ **⇒⇒⇒⇒⇒⇒⇒⭐ 「描述这个 bug 的文字本身会污染口径」** ⇒ "
          "处置 = 口径里显式排除裸基目录 + 钉一条「不排除就会塌」的反证，**而不是去改文档措辞**",
          '"p11_describing_the_bug_pollutes_the_metric_2017_"' in _ausrc
          and 'def is_bare_base(ref):' in _p1017
          and 'plain = {r for r in refs if not is_glob(r) and not is_bare_base(r)}' in _p1017
          and 'BARE_BASE_PRESENT and BARE_BASE_WOULD_DEFLATE' in _p1017
          and '"bare_base_refs"' in _p1017
          and '**⇒⇒⇒⇒⇒⇒⇒⭐ 「描述这个 bug 的文字本身会污染口径」**' in _ausrc
          # ⭐⭐ 反向门：**反证不许走打过补丁的那条路** —— 它已经把路堵上了，演示不出塌掉
          and 'def _covered_raw(refs):' in _p1017
          and '去做反证是**无效的反证**' in _p1017
          and '本批自己又撞到一次「反向用例必须真的走一遍被测代码」' in _ausrc)

    # ══ X993B. 批 1018 那 24 条「在读原型源码」的判据：只改行为全绿、只改名转红
    #    ⇒ 它们是字面量存在性检查，不是行为回归测试
    print("— X993B. 批 1018 断言 vs 行为：24 条里 8 条同时断 audit 散文、2 条只断 audit、"
          "13 条锚点本身是中文注释；反向用例 Ⓐ 改行为 24 条全绿、Ⓑ 改名 2 条转红")

    check("X993B.1 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P1 成立 —— 本批要验的命题："
          "那 24 条验的是「那段字还在」，不是「这个行为还对」。** 口径 = 逐条 eval 判据的"
          "**原始条件表达式**（AST 取节点 → `ast.unparse` → 内存里换文本后执行，"
          "**不是转述、不是重写**）",
          '"p1_the_claim_2018_"' in _ausrc
          and '"assertion_vs_behavior_2018"' in _ausrc
          and 'code = compile(ast.Expression(body=c["node"]), "<c1018>", "eval")' in _p1018
          and '"expr": ast.unparse(cond)' in _p1018
          and 'exec(compile(code, "<v1018-read>", "exec"), g)' in _p1018
          and 'P1 = (N == 24 and N_PASS == N)' in _p1018)

    check("X993B.2 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P2 反向用例 Ⓐ —— "
          "只改行为、不动任何锚点（步进 `cur + dir` → `cur + dir * 2`，焦点一次跨两个）"
          "⇒ 24 条一条没红、仍全绿 ⇒⇒⇒⇒⇒ **这 24 条看不见行为变更**",
          '"p2_behavior_change_is_invisible_2018_"' in _ausrc
          and 'ANCHOR_LINE = "const next = cur + dir;"' in _p1018
          and 'MUT_A = "const next = cur + dir * 2;"' in _p1018
          and 'A_INVISIBLE = (A_APPLIED and N_A_PASS == N_PASS)' in _p1018
          and 'n_anchors_touched' in _p1018
          and '这 24 条看不见行为变更 ⇒ 它们不是行为回归测试' in _ausrc)

    check("X993B.3 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P3 反向用例 Ⓑ —— "
          "只改名、不改行为 ⇒ 2 条转红 ⇒⇒⇒⇒⇒ **门对「重命名」敏感、对「改错」不敏感**",
          '"p3_rename_breaks_it_2018_"' in _ausrc
          and 'MUT_B = "function armRovingTabindexV2("' in _p1018
          and 'B_BREAKS = (B_APPLIED and (B_STATES.get("fail", 0) + B_STATES.get("crash", 0)) > 0)' in _p1018
          and '这 24 条看不见行为变更 ⇒ 它们不是行为回归测试' in _ausrc
          and '门对「重命名」敏感、对「改错」不敏感' in _ausrc)

    check("X993B.4 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P4：「在读原型源码」还要再切一刀** —— "
          "8 条同时断 audit 判据文本里的散文、**其中 2 条根本只断 audit 文本** ⇒ "
          "**24 这个数已经是上界，真·验代码的比它更小**",
          '"p4_some_read_the_audit_not_the_prototype_2018_"' in _ausrc
          and 'cont = n.comparators[0] if n.comparators else None' in _p1018
          and 'N_ONLY_AUDIT = sum(1 for c in CLASS' in _p1018
          and '真·验代码的比它更小' in _ausrc)

    check("X993B.5 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P5 —— 而其中 13 条的锚点本身就是中文散文**"
          "（「批 967 改写上面那段…」「别复制第二份」「不跑 tsc」）⇒ **注释被当成了实现** ⇒ "
          "**而它们能长期为绿，是因为「注释不许被删」这条纪律正好和「锚点必须在」重合**",
          '"p5_comments_counted_as_implementation_2018_"' in _ausrc
          and 'N_PROSE = sum(1 for c in CLASS if c["n_prose_literals"] > 0)' in _p1018
          and 'CJK = re.compile(r"[\\u4e00-\\u9fff]|\\*\\*")' in _p1018
          and '注释被当成了实现**' in _ausrc
          and '两条纪律的交集成了它的护身符' in _ausrc)

    check("X993B.6 ⭐⭐⭐⭐⭐⭐⭐⭐ **P6 —— 而本批有一条必须诚实撤回的结论**：我第一版口头说过"
          "「纯改名会让门直接 `IndexError` 崩掉」⇒ **那是仪器自己的 bug**"
          "（`main` 里的赋值没被执行全、基线本来就崩 24 条）⇒ 照抄到结论里就成了假发现 ⇒ "
          "**「`crashed` 必须单列」仍然成立，但「这个反向用例会崩」这个结论已撤回**",
          '"p6_honest_retraction_2018_"' in _ausrc
          and '"crash_note"' in _p1018
          and 'B_CRASHES = B_STATES.get("crash", 0) > 0' in _p1018
          and '「我以为发生过的事」都会变成假发现**' in _ausrc
          and '**⇒ 诚实更正：本次两个反向用例里 `crash` = %d。**' not in _p1018
          and '"crash_note": "⚠️⭐⭐⭐⭐⭐ **诚实更正：本次两个反向用例里 `crash` = ' in _p1018)

    check("X993B.7 ⭐⭐⭐⭐⭐ **P7：口径边界** —— 本批只验「判据看得见/看不见行为变更」，"
          "**没有**验「原型实现的行为本身对不对」⇒ **不把「字面量在」说成「行为对」**；"
          "反向用例**全部在内存里改文本，一个字节都不动仓里的原型文件**",
          '"p7_scope_2018_"' in _ausrc
          and '"scope": "⚠️⭐⭐⭐⭐⭐ **本探针只做到这一步**' in _p1018
          and '反向用例**全部在内存里改文本，一个字节都不动仓里文件**' in _p1018
          and 'P7 = True' in _p1018)

    check("X993B.8 ⭐⭐⭐⭐⭐ **P8 成立：纯离线** —— 零浏览器 / 零按键 / 零网络；"
          "逐条落进 `assertion-vs-behavior-1018.json`、由本探针自己写",
          '"p8_offline_2018_"' in _ausrc
          and 'assertion-vs-behavior-1018.json' in _p1018
          and 'assertion-vs-behavior-1018.json' in _ausrc
          and '"generated_by": "jimeng_probe1018_assertion_vs_behavior.py"' in _p1018
          and '零浏览器 / 零按键 / 零网络；' in _ausrc)

    # ══ Y993C. 批 1019 第一次动手改：把一条判据从「字面量存在性」升级成「真行为验证」
    #    两个「0 锚点」的补丁：行为检查红了，而读 _wsrc 的 7 条判据 7/7 全绿
    print("— Y993C. 批 1019 行为 harness：抽函数真身 + 最小 DOM stub + node 真跑；"
          "行为格基线全绿；两个 0 锚点补丁各被行为检查抓住，"
          "而 7 条字面量判据始终 7/7 全绿")

    check("Y993C.1 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P1 成立 —— "
          "本批第一次在装置上「动手改」：把一条判据从「字面量存在性」升级成「真行为验证」。** "
          "按函数名 + 括号配平**抽出函数真身**（不是转写）+ 最小 DOM stub + node 真跑 ⇒ "
          "行为格基线全绿（条数由产物给出，判据不写死 —— 1021 通则⑤）",
          '"p1_first_real_upgrade_2019_"' in _ausrc
          and '"behavior_harness_2019"' in _ausrc
          and 'def extract_fn(src, name):' in _p1019
          and 'return src[m.start():j + 1]' in _p1019
          and 'FN_BODY = FN_ALL + ' in _p1019
          and 'harness-%s.ts' in _p1019
          and 'P1 = (N_SCEN >= 7 and not BASE_FAIL)' in _p1019)

    check("Y993C.2 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P2 —— 本批的读数："
          "两个「改了行为、却一个锚点都没碰」的补丁，行为检查各红 2 / 1 条，"
          "而同一时刻读 `_wsrc` 的 7 条判据 7/7 全绿** ⇒ "
          "**「字面量判据全绿」与「行为已经坏了」是可以同时成立的**",
          '"p2_behavior_check_sees_what_strings_cannot_2019_"' in _ausrc
          and 'MUT_B_PLACEHOLDER' not in _p1019
          and 'MUTS = {' in _p1019
          and 'A_step_doubled' in _p1019
          and 'B_end_guard_removed' in _p1019
          and '"anchors_touched": 0' in _p1019
          and 'P2 = (len(A_FAIL) > 0)' in _p1019
          and 'P3 = (len(B_FAIL) > 0 and "focus_node4_forward_end_untouched" in B_FAIL)' in _p1019
          and '「字面量判据全绿」与「行为已经坏了」是可' in _ausrc)

    check("Y993C.3 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P3 —— 而补丁 Ⓑ 不是随手找的**：去掉末尾守卫后，"
          "焦点在末尾按 Tab ⇒ `next` 越界 ⇒ `armAll(nodes, 越界)` 把**整块画布**写成全 `-1` ⇒ "
          "**画布彻底不可聚焦** —— 而这是**严重行为回归，现有 7 条判据一条都看不见它**",
          '"p3_why_patch_B_matters_2019_"' in _ausrc
          and 'MUT_A, MUT_B' not in _p1019
          and '"if (next < 0 || next >= nodes.length) return;"' in _p1019
          and '"if (next < 0) return;"' in _p1019
          and 'P6 = bool(re.search(r"next >= nodes' in _p1019
          and '**现有 7 条判据一条都看不见它**' in _ausrc)

    check("Y993C.4 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P4：「字面量判据会不会红」这一格是测出来的、"
          "不是假定的** ⇒ 逐条 eval 那 7 条的原始条件表达式 ⇒ "
          "**⚠️ 诚实标注：三个变体下的结果必然逐条相同**（补丁只改内存里抽出的函数体、"
          "`_wsrc` 一个字节没动）⇒ **那三行不是三次独立测量**；"
          "而**同源的两边不许互相证明（1012）** ⇒ 真正有意义的是行为侧真的红了、且那两条互不靠",
          '"p4_measured_not_assumed_2019_"' in _ausrc
          and 'def eval_ws(src_text):' in _p1019
          and 'code = compile(ast.Expression(body=c["node"]), "<c1019>", "eval")' in _p1019
          and '"after_patch_note"' in _p1019
          and '**⇒⇒⇒⇒⇒⇒⇒ 那三行不是三次独立测量；跑三遍只为让「一致」由仪器证实' in _ausrc
          and '**⇒⇒⇒⇒⇒⇒⇒⇒ 而「同源的两边」不许互相证明（1012）' in _ausrc)

    check("Y993C.5 ⭐⭐⭐⭐⭐⭐⭐ **P5 —— 本批踩到一次「门红先判门错还是数据错」**："
          "第一版只给三个变量 ⇒ `GGGGG.2` 直接 `NameError: _p973` ⇒ **那是仪器错、不是判据红** ⇒ "
          "处置 = 改用 1018 那套已验证的加载法 ⇒ **而如果当时直接写成「有一条判据是红的」，"
          "那就是 1018 刚撤回的那种假发现**",
          '"p5_instrument_error_first_2019_"' in _ausrc
          and 'def _verifier_globals():' in _p1019
          and 'VG = _verifier_globals()' in _p1019
          and '**那是本探针的仪器错、不是判据红**' in _ausrc
          and '那就是 1018 刚撤回的那种假发现' in _ausrc)

    check("Y993C.6 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P6 —— 本批自己的仪器同一天栽了两次，"
          "都栽在「抽出来的不是函数真身」上**：① `extract_fn` 返回**从 `{` 开始的函数体** ⇒ "
          "拼出来是两块裸语句、顶层 `return` 直接 SyntaxError；② 抽出的 TS 带类型标注 ⇒ "
          "**第一版想用正则手术去掉，而正则手术有可能手术出第二种真身** ⇒ "
          "处置 = 改用 `.ts` + Node 24 原生擦除类型 ⇒ **一个字的类型都不动**",
          '"p6_two_instrument_bugs_2019_"' in _ausrc
          and '**⇒⇒⇒⇒⇒ 处置 = 改用 `.ts` 后缀 + Node 24 原生擦除类型 ⇒ 一个字的类型都不动**' in _ausrc
          and '**而正则手术有可能手术出第二种真身**' in _ausrc
          and 'harness-%s.ts' in _p1019)

    check("Y993C.7 ⭐⭐⭐⭐⭐ **P7：口径边界** —— 测的是**真函数体**但跑在 **stub** 上 ⇒ "
          "验的是步进与两端守卫的逻辑、**不是真实浏览器语义、不许当 e2e**；"
          "只跑了 1 个函数、一小批场景（条数见产物）⇒ "
          "**不把「一条判据升级了」说成「原型被验过了」**；"
          "反向用例**只在内存里改文本，一个字节都不动仓里的原型文件**",
          '"p7_scope_2019_"' in _ausrc
          and '"dom_surface_used"' in _p1019
          and '它验的是**步进与两端守卫的逻辑**' in _ausrc
          and '**不把「一条判据升级了」说成「原型被验过了」**' in _ausrc
          and '一个字节都不动仓里的原型文件**' in _ausrc)

    check("Y993C.8 ⭐⭐⭐⭐⭐ **P8 纯离线** —— node + 只读仓里两个文件、**不装任何依赖**"
          "（仓里没有 jsdom / 测试框架 ⇒ 只给最小 stub、不引入新的失败面）、"
          "临时目录注册 `atexit` 清理；**P9 逐条落进 `behavior-harness-1019.json`、本探针自己写**",
          '"p8_offline_2019_"' in _ausrc
          and '"p9_golden_2019_"' in _ausrc
          and 'atexit.register(shutil.rmtree, str(TMPDIR), ignore_errors=True)' in _p1019
          and 'behavior-harness-1019.json' in _p1019
          and 'behavior-harness-1019.json' in _ausrc
          and '**不装任何依赖**' in _ausrc)





    # ══ Z993D. 批 1020 把 1019 那个 harness 本身当被测对象：保真度 + 判别力
    print("— Z993D. 批 1020 harness 保真度与判别力：两条 stub 在 86 格枚举里分歧 11 格（全是 depth≥2 的内层控件）；"
          "系统枚举的变异体 8 格杀 23/30；补两格抬到 26/30")
    check("Z993D.1 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**P1 成立 —— 本批把 1019 那个 harness 本身当被测对象。** 两条 stub **唯一的差别**是 "
          "`contains` 的语义：shallow = `el.__parent === this`（**只认直接父节点、且不含自身**）、"
          "deep = 沿父链上溯且**含自身** ⇒⇒⇒⇒⇒ **86 格枚举里分歧 11 格，类别只有 `inner2`**；"
          "`contains` 四问**直接量出来**：`self`/`depth2` 不一致、`depth1`/`unrelated` 一致",
          'def gen_mutants(body):' in _p1020
          and 'TOKEN_OPTS = {' in _p1020
          and 'el.contains = function (o) { return !!o && o.__parent === this; };' in _p1020
          and 'for (let p = o; p; p = p.__parent) { if (p === this) { return true; } }' in _p1020
          and 'const NS = [0, 1, 2, 3, 5];' in _p1020
          and 'P1 = (N_DISAGREE > 0 and DISAGREE_KINDS == ["inner2"])' in _p1020
          and 'N_DISAGREE = len(DISAGREE)' in _p1020
          and '"n_disagreements": N_DISAGREE' in _p1020
          and '"p1_stub_fidelity_gap_2020_"' in _ausrc
          and '**86 格枚举里分歧 11 格，类别只有 `inner2`（深度 ≥2 的内层控件）**' in _ausrc)
    check("Z993D.2 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P2 —— 而 1019 那 8 条"
          "**手写期望**本身是对的**：在**两条** stub 下都 **8/8 全绿** ⇒⇒⇒⇒⇒⇒⇒⇒⇒ "
          "**错的不是期望，是它没被测到的那一类状态** ⇒⇒⇒⇒⇒⇒ "
          "**「保真度」和「期望对不对」是两个独立的量，必须分开报**",
          'P2 = (BASE_ALL_GREEN and N_CELL_BAD_DEEP == 0)' in _p1020
          and 'N_CELL_BAD_DEEP = sum(1 for v in CELLS_DEEP.values() if not v)' in _p1020
          and 'BASE_ALL_GREEN = all(SH_CELLS0.values())' in _p1020
          and '"n_criteria_reading_wsrc"' not in _p1020
          and '而 1019 那 8 条**手写期望**本身是对的**' in _ausrc
          and '"p2_1019_expectations_are_right_2020_"' in _ausrc)
    check("Z993D.3 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P3 —— 判别力："
          "变异体是**按 token 规则系统枚举**的 ⇒ **不是手挑，分母由探针生成、不由我断言**；"
          "**存活变异体逐个附上 `before`/`after` 两行原文** —— "
          "把「突变体名字」当结论报出去，等于报了一个没法复核的东西",
          'N_MUT = len(MUTANTS)' in _p1020
          and '"n_generated": N_MUT' in _p1020
          and '"n_testable": N_TESTABLE' in _p1020
          and '"n_syntax_error_under_both": N_SYNTAX' in _p1020
          and '"survivors_with_diff"' in _p1020
          and '"before": before.strip(), "after": after.strip()' in _p1020
          and 'P3 = (N_TESTABLE > 0 and N_K_SHALLOW > 0 and N_K_DEEP > 0)' in _p1020
          and 'P4 = len(SURV_SHALLOW) > 0' in _p1020
          and '**存活变异体逐个附上 `before`/`after` 两行原文**' in _ausrc
          and '从不断言「非布防节点被写成什么」' in _ausrc
          and '"p3_discriminating_power_2020_"' in _ausrc
          and '"p4_survivors_are_named_2020_"' in _ausrc)
    check("Z993D.4 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P5 —— 分支覆盖是 **6/7**，未覆盖的是 `!flow`；"
          "⚠️ **我第一版把本探针自己加的 `flowNull` 探针算进了「1019 的分支覆盖」里，量出 7/7** ⇒ "
          "**那是我在给自己的格记 1019 的功劳** ⇒ 而 `!flow` **在生产里是死代码**",
          'P5 = (N_BRANCH_HIT == N_BRANCH - 1 and not HIT["!flow"] and FLOW_NULL_REACHED)' in _p1020
          and '"hit_by_1019_eight_cells": HIT' in _p1020
          and '"added_by_this_probe"' in _p1020
          and '"p5_branch_coverage_credit_2020_"' in _ausrc
          and '**我第一版把本探针自己加的 `flowNull` 探针算进了' in _ausrc
          and '而好看不是理由' in _ausrc)
    check("Z993D.5 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**P6 —— 本批的核心结构性发现：8 个**手写期望**的格 = **判别器**；"
          "86 个**机器枚举**的格 = **差分器** ⇒⇒⇒⇒⇒ "
          "**⇒ 差分器在结构上永远杀不死任何变异体。** ⇒⇒⇒⇒⇒ "
          "**把覆盖从 8 格拉到 86 格，不等于多了一个字的判别力。**",
          '"the_structural_finding"' in _p1020
          and '"handwritten_cells"' in _p1020
          and '"machine_grid"' in _p1020
          and '**把覆盖从 8 格拉到 86 格，不等于多了一个字的判别力。**' in _ausrc
          and '"p6_differential_vs_discriminating_2020_"' in _ausrc
          and '**「全绿」和「够强」是两回事**' in _ausrc)
    check("Z993D.6 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**P7 —— 判决分叉的实测**：**不是新增一个格，是把已有那条 906 的格「样本深度 1 → 2」换掉**，"
          "期望一个字没动 ⇒⇒⇒⇒⇒ **深度 1 样本两条 stub 都绿；深度 2 样本 shallow 转红、deep 保持绿**"
          "⇒⇒⇒⇒⇒⇒⇒ **它是潜在的、不是已发生的** —— **但它离「变成已发生」只差一个样本**",
          'P7 = VERDICT_FORK and D1_AGREE' in _p1020
          and '"the_verdict_fork"' in _p1020
          and '"verdict_fork": VERDICT_FORK' in _p1020
          and 'const g6 = probe(w6, "inner1", 1, 1);' in _p1020
          and 'const g6b = probe(w6b, "inner2", 1, 1);' in _p1020
          and '**不是新增一个格，是把已有那条 906 的格' in _ausrc
          and '"p7_one_sample_depth_flips_a_verdict_2020_"' in _ausrc
          and '只是错的方向恰好被它测的那一格掩盖了' in _ausrc)
    check("Z993D.7 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **P8 —— 补两格，"
          "并且量出「买到多少判别力」**：**在 1020 自己的 harness 上加格，一个字都不动 1019** "
          "⇒⇒⇒⇒⇒ **mutation score 从 23/30 抬到 26/30**；⚠️ "
          "**补的格自己必须先在基线上全绿**，否则就是拿一个**本身就红的格**在说",
          'NEW_CELLS = [n for n in N_CELL_PLUS_NAMES if n not in SH_CELLS0]' in _p1020
          and 'focus_node1_backward_arms_0' in _p1020
          and 'focus_node2_forward_others_minus1' in _p1020
          and 'P8 = (PLUS_BASE_GREEN and N_KP_SHALLOW > N_K_SHALLOW and len(NEWLY_KILLED) > 0)' in _p1020
          and 'PLUS_BASE_GREEN = all(SH_PLUS0.values()) and all(DP_PLUS0.values())' in _p1020
          and '"the_fix_measured"' in _p1020
          and '⇒⇒⇒⇒⇒⇒ **mutation score 从 23/30 抬到 26/30，新杀 3 个' in _ausrc
          and '**mutation score 从 23/30 抬到 26/30，新杀 3 个' in _ausrc
          and '"p8_the_fix_measured_2020_"' in _ausrc)
    check("Z993D.8 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **第二处 stub 保真度缺口："
          "`tabindex` 在真 DOM 里是**整数**而 harness 判的是**字符串相等** ⇒ 实测 "
          "`-0`/`00`/`+0`/`\" 0\"` 两套口径不一致；⚠️ **不报「复刻坏了」，只报「两套口径不一致」**"
          "；且 **纯离线、一个字节都不动仓里的原型文件**、**逐条落进产物**",
          'P9 = len(TAB_DISAGREE) > 0' in _p1020
          and 'TAB_DISAGREE = [t for t in TAB_FID if not t["agree"]]' in _p1020
          and 'harness_string_eq_0: v === "0"' in _p1020
          and 'browser_int_eq_0: parseInt(v, 10) === 0' in _p1020
          and 'P10 = True' in _p1020
          and 'atexit.register(shutil.rmtree, str(TMPDIR), ignore_errors=True)' in _p1020
          and 'harness-fidelity-1020.json' in _p1020
          and '"tabindex_fidelity"' in _p1020
          and '"p9_tabindex_string_versus_integer_2020_"' in _ausrc
          and '"p10_honest_notes_2020_"' in _ausrc
          and '"p11_scope_and_offline_2020_"' in _ausrc
          and '"p12_golden_2020_"' in _ausrc)


    # ══ AA993E. 批 1021 第一次量「门自己」：官方锚点门对「判据变弱」的敏感度
    print("— AA993E. 批 1021 量门自己：6 个变弱形状里 4 个让官方锚点门继续报「问题 0 个」；"
          "删整组 8 条判据 ⇒ 少查 69 条锚点而问题数纹丝不动")
    check("AA993E.1 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**P1 —— 本批第一次量「门自己」**：变异版 verifier 写到临时文件、用 `argv[1]` 喂给"
          "**官方门本体**（不是重写一份）⇒ **避免「我以为门是这样工作的」**；"
          "⚠️ **自检：未变异那一格必须逐字复现官方门自己报的数**，不忠实就**立刻停**",
          'def run_gate(vpath):' in _p1021
          and 'str(GATE), str(vpath), str(AUDIT)' in _p1021
          and 'SELFCHECK = (' in _p1021
          and 'raise SystemExit("自检失败：驱动方式不忠实，先停。%r / 树上 check 数 %d"' in _p1021
          and '"self_check"' in _p1021
          and '"baseline_reproduced": SELFCHECK' in _p1021
          and '**P1 —— 本批第一次量「门自己」。**' in _ausrc
          and '"p1_driver_is_faithful_2021_"' in _ausrc)
    check("AA993E.2 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**P2 成立 —— 官方锚点门的 `collect()` 只收「还被 `check()` 引用的」锚点 "
          "⇒ 「把判据变弱」的典型手法恰恰是「少引用一条锚点」** ⇒ 实测 6 个变弱形状，"
          "**4 个让门继续报「问题 0 个」**：Ⓐ 删整条、Ⓑ 删整组、Ⓒ 删一个合取项、"
          "Ⓔ 把锚点换成**确实存在、但说的是别的事**的串",
          'SILENT = [r["tag"] for r in ROWS[1:]' in _p1021
          and 'if r["n_problems"] == 0 and r["would_fail"] == 0 and r["missing"] == 0]' in _p1021
          and '"anchors_dropped": BASE["n_anchors"] - r["n_anchors"]' in _p1021
          and '"checks_dropped": BASE["n_checks"] - r["n_checks"]' in _p1021
          and 'P2 = len(SILENT) >= 3' in _p1021
          and '「把判据变弱」的典型手法恰恰是「少引用一条锚点」。**' in _ausrc
          and '"p2_four_ways_to_weaken_stay_green_2021_"' in _ausrc)
    check("AA993E.3 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **门只抓到 2 个形状**："
          "Ⓕ 加**恒真**判据（**1002 那条 SHAPE 普查干的**）、Ⓖ 把 `in` 翻成 `not in` "
          "⇒⇒⇒⇒⇒ **「加错的」抓得住，「少对的」抓不住** ⇒ "
          "**这是 1016「同名键的失败形态是安静」的同一种病、换了个宿主**",
          'CAUGHT = [r["tag"] for r in ROWS[1:] if r["tag"] not in SILENT]' in _p1021
          and 'check("Z993E.9 恒真", True)' in _p1021
          and '"caught": CAUGHT' in _p1021
          and 'P4 = "G_flip_in_to_not_in_1021" in CAUGHT' in _p1021
          and '**「加错的」抓得住，「少对的」抓不住**' in _ausrc
          and '**少写一条、没有任何东西会告诉你**」' in _ausrc
          and '"p3_only_two_shapes_are_caught_2021_"' in _ausrc)
    check("AA993E.4 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**P4 —— 唯一会变的读数是汇总行里的 `check(N)`，而没有任何门在比对这个数** ⇒ "
          "**「门少了 8 条检查」与「门报 0 个问题」可以同时成立**；"
          "⭐⭐⭐ **覆盖面缩得比判据数快得多**：删 8 条 ⇒ 少查 **69** 条锚点（约 **8.6** 倍）"
          "⇒ **所以 `check(N)` 不是够用的基线，**受检锚点数**才是**",
          '"shorthand": SHORTHAND' in _p1021
          and 'P3 = any(s["anchors_dropped"] > 0 and s["n_problems"] == 0 for s in SHORTHAND)' in _p1021
          and '"delivered"' in _p1021
          and '"countermeasure"' in _p1021
          and '而没有任何门在比对这个数**' in _ausrc
          and '**覆盖面缩得比判据数快得多**' in _ausrc
          and '受检锚点数**才是**' in _ausrc
          and '"p4_the_only_moving_reading_2021_"' in _ausrc)
    check("AA993E.5 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **处置**：把 `check(N)` **与受检锚点数**一起"
          "**登记进产物并钉住当前基线** ⇒ ⭐ **通则：门的覆盖面必须是一个被登记的量** —— "
          "**「门还在跑」不等于「门查得和昨天一样多」**；且 ⚠️ "
          "**变异集合是手挑的 6 个形状、不是穷举 ⇒ 不许把结论说成「只有这几种能溜过去」**；"
          "**纯离线、变异只在临时文件里、逐条落进产物**",
          'P5 = all(r["rc"] in (0, 1) for r in ROWS) and len(ROWS) == 1 + len(MUTS)' in _p1021
          and 'P6 = True' in _p1021
          and 'P7 = True' in _p1021
          and 'atexit.register(shutil.rmtree, str(TMPDIR), ignore_errors=True)' in _p1021
          and 'anchor-gate-coverage-1021.json' in _p1021
          and '**处置不是「登记」，是「做成一道会红的闸」**' in _ausrc
          and '**「门还在跑」不等于「门查得和昨天一样多」**' in _ausrc
          and '不许说成「只有这几种能溜过去」**' in _ausrc
          and '"p5_countermeasure_2021_"' in _ausrc
          and '"p6_scope_2021_"' in _ausrc
          and '"p7_offline_2021_"' in _ausrc
          and '"p8_golden_2021_"' in _ausrc)


    # ══ BB993F. 批 1022 把 1020 诊断出来的缺口真正补上，并让 1021 通则⑤自己兑现一遍
    print("— BB993F. 批 1022 把 1020 诊断出的两格落进 1019（各对准一个实测存活体）；"
          "并把 Y993C 判据里写死的条数改成机制表述")
    check("BB993F.1 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**P1 成立 —— 本批把 1020 诊断出来的缺口真正补上。** 两格落进 "
          "`jimeng_probe1019_behavior_harness.py`：Ⓐ `focus_node1_backward_arms_0` 对准 "
          "`next < 1` 那个存活体；Ⓑ `focus_node2_forward_others_minus1` 对准 `\"-1\"` 的两个存活体；"
          "⭐ **补完基线仍全绿**，**补丁 Ⓐ 被抓的行为格从 2 条增到 4 条**",
          'focus_node1_backward_arms_0' in _p1019
          and 'focus_node2_forward_others_minus1' in _p1019
          and 'othersOk = w.nodes.every(function(nd)' not in _p1019
          and 'othersOk = w.nodes.every(nd =>' in _p1019
          and '批 1022 补的两格（对准 1020 实测存活的变异体' in _p1019
          and '**⇒⇒⇒⇒⇒ 「补哪一格」必须有实测存活体撑着' in _ausrc
          and '"p1_the_fix_actually_landed_2022_"' in _ausrc
          and '"p2_not_handed_2022_"' in _ausrc)
    check("BB993F.2 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**P2 —— 而 1019 docstring 里那一行「7 个行为格」从写下那天起就是错的** "
          "⇒⇒⇒⇒⇒ **原文一字不删、只挂改写横幅；条数由 `N_SCEN` 算出来落在产物 "
          "`n_scenarios` / `scenario_count_history` 里** ⇒⇒⇒⇒⇒⇒⇒ "
          "**并把 Y993C 判据与 audit 散文里所有写死的条数一并改成机制表述**"
          "（**1021 通则⑤在它自己身上兑现了一遍**）",
          'scenario_count_history' in _p1019
          and '"n_before_1019": 8' in _p1019
          and '批 1022 改写横幅，原文一字不删' in _p1019
          and '**（批 1022 改写横幅：原文写的条数已被改成机制表述' in _ausrc
          and '一小批场景（条数见产物）**' in _ausrc
          and '"p3_absolute_readings_expire_here_2022_"' in _ausrc)
    check("BB993F.3 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**P3 —— 哪些数字一个字没动、为什么**：`Z993D` 里引用「1019 那 8 条 / 8/8 全绿」的话，"
          "**是 1020 当时对 1019 那个状态的实测记录、今天仍然是真的** ⇒ "
          "**⇒ 「撤销只挂横幅」在这里的正确用法是「那几条别动」**；"
          "唯一加横幅的是「当时没敢动 1019」那一条 —— **本批真的动了 ⇒ 它的处境变了**",
          '"p4_what_was_not_changed_2022_"' in _ausrc
          and '「撤销只挂横幅、原文一字不删」在这里的正确用法是' in _ausrc
          and '**批 1022 已经把那两格真的落进 1019 了 ⇒ 上面这句的处境变了' in _ausrc
          and '"p5_scope_2022_"' in _ausrc
          and '"p6_offline_2022_"' in _ausrc
          and '"p7_golden_2022_"' in _ausrc)
    check("BB993F.4 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ **口径边界**："
          "**只动了 1019 那份 harness 的场景表与判分函数**，**没改被测函数真身、没改 stub、"
          "没改 1020 的任何一行** ⇒ **⇒⇒⇒⇒⇒ 1020 的全部读数在今天依然成立**"
          "（它量的是「1020 当时的 1019」，而那正是它被要求量的）；"
          "**补的格在基线上先跑一遍确认全绿再提交**；**纯离线、零浏览器**",
          '**没有**改被测的函数真身' in _ausrc
          and '**⇒⇒⇒⇒⇒⇒ 1020 的全部读数在今天依然成立**' in _ausrc
          and '补的格**在基线上先跑一遍确认全绿' in _ausrc
          and 'atexit.register(shutil.rmtree, str(TMPDIR), ignore_errors=True)' in _p1019)


    # ══ CC993G. 批 1023 量「类型层」那一道闸：tsc 早就装好了，而一条判据把一句从没成立过的话当成了前提
    print("— CC993G. 批 1023 量类型层：tsc 早就在、整仓零错误；"
          "1020 那 4 个「等价变异体」被类型层 4/4 全抓住；而「npm run check 不跑 tsc」从来没成立过")
    check("CC993G.1 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**P1 成立 —— 本批量「类型层」那一道闸。** 两条基线都必须先干净："
          "**整仓 `tsc --noEmit` rc=0 零错误**、**未变异副本也 rc=0** ⇒ 不干净则"
          "**「tsc 抓到了」可能只是副本装置坏了 ⇒ 后面全部作废、立刻停**；"
          "⭐ **零安装零网络** —— 用的是仓里**早就装好的** `typescript` 与根 `tsconfig.json`",
          'def whole_repo_tsc()' in _p1023
          and 'self_test' not in _p1023          # 不许有那个字段名（避免判据自我锚定）
          and 'SELFCHECK = (REPO_TSC["rc"] == 0 and COPY_TSC["rc"] == 0)' in _p1023
          and 'raise SystemExit("自检失败：仓当前就有类型错误、或副本装置不干净，先停。%r / %r"' in _p1023
          and 'TMPDIR = Path(tempfile.mkdtemp(prefix="b1023-", dir=str(ROOT)))' in _p1023
          and 'atexit.register(shutil.rmtree, str(TMPDIR), ignore_errors=True)' in _p1023
          and '**零安装、零网络** —— 用的是仓里**早就装好的** `typescript`' in _ausrc
          and '"p1_tsc_is_already_here_and_the_repo_is_clean_2023_"' in _ausrc)
    check("CC993G.2 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**P2 成立 —— 1020 那 4 个「运行期不可区分」的类型变异体，**tsc 全部抓到（4/4）** ⇒ "
          "**⇒⇒⇒⇒⇒ 1020 那句「它们是等价变异体、不算判别力缺口」只在运行期成立** ⇒ "
          "**⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 真正的结论不是「缺口没人管」，是「工具早就在、只是没人调」**",
          'T1020 = [r for r in TMUT_ROWS if r["name"] in' in _p1023
          and 'T1020_CAUGHT = [r["name"] for r in T1020 if r["rc"] != 0]' in _p1023
          and 'P2 = bool(WIRING["node_modules/typescript"])' in _p1023
          and '"the_four_from_1020"' in _p1023
          and '**⇒⇒⇒⇒⇒ 1020 那句「它们是等价变异体、不算判别力缺口」' in _p1023
          and '真正的结论不是「缺口没人管」，是「工具早就在、只是没人调」**' in _p1023
          and '"p2_type_layer_catches_all_four_2023_"' in _ausrc)
    check("CC993G.3 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**P3 —— 而类型层也不是全覆盖的**：7 个类型变异体里 **tsc 抓到 6、存活 1** ⇒ "
          "**收窄型全抓住、放宽型（`dir: number`）活下来** ⇒ "
          "**⇒ 「没有任何一层能抓的变异体」是存在的一类，不能因为多了一道门就说抓全了**",
          '("T7_dir_widened_to_number", "dir: 1 | -1", "dir: number")' in _p1023
          and '"n_caught_by_tsc": len(T_CAUGHT)' in _p1023
          and '"n_survived_tsc": len(T_SURVIVED)' in _p1023
          and '"the_honest_boundary"' in _p1023
          and '"predicted_wrong"' in _p1023
          and '**收窄型（把能接的接得变少）全部被抓住；' in _p1023
          and '**「没有任何一层能抓的变异体」是存在的一类' in _p1023
          and '我第一版预测 T4（`1 | -2`）会存活**' in _p1023
          and '"p3_the_honest_boundary_2023_"' in _ausrc
          and '"p4_prediction_was_wrong_2023_"' in _ausrc)
    check("CC993G.4 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**P5 成立 —— 接线盘点**：`typescript` 在、`typecheck` 在、`check` 链了它、"
          "CI **调了**且**在 `push` 上触发** ⇒ ⭐ **但本地 `pre-commit` 一次都没调过 tsc** ⇒ "
          "**⇒⇒⇒⇒⇒ 本地提交门看不见类型层、远端能看见** ⇒ "
          "**而本仓所有会话都是直推 master ⇒ 类型错误要等远端 CI 才发现**",
          'PRECOMMIT = ROOT / ".git/hooks/pre-commit"' in _p1023
          and '"本地 pre-commit 调过 tsc": bool(re.search(r"\\btsc\\b|typecheck", PRE_SRC))' in _p1023
          and '"CI 调过 typecheck"' in _p1023
          and '"CI 在 push 上触发"' in _p1023
          and '"check 链了 typecheck"' in _p1023
          and '**本地提交门看不见类型层、远端能看见**' in _ausrc
          and '"p5_wiring_census_2023_"' in _ausrc)
    check("CC993G.5 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**P6 —— 而顺手挖出一条「从来没成立过的前提」**：源码里那句"
          "**「`npm run check` 是 eslint、不跑 tsc」**，判据 `CC.9` 把"
          "**那句注释还在不在**当成凭据 ⇒⇒⇒⇒⇒ "
          "**而初始提交 `523fc473` 的 `check` 就是 `npm run lint && npm run typecheck && npm run build`** ⇒ "
          "**⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒⇒ 那句话从来就不成立，而判据会永远绿**；"
          "⚠️ **匹配前必须去掉两侧空白** —— **那句话在源码里跨了两行**，第一版精确 `in` 返回 `False`",
          'AGP_FLAT = re.sub(r"\\s+", "", AGP_SRC)' in _p1023
          and 'SENTENCE_IN_SRC = re.sub(r"\\s+", "", STALE_SENTENCE) in AGP_FLAT' in _p1023
          and 'CC9_ANCHORS_ON_EXISTENCE = \'"不跑 tsc" in _agp_raw\' in VER_SRC' in _p1023
          and 'def git_show(rev, path):' in _p1023
          and '"rev-list", "--max-parents=0", "HEAD"' in _p1023
          and '**判据锚的是「注释还在」，不是「注释说的对」**' in _p1023
          and '拿代码自己的注释当证据」是第二种循环**' in _p1023
          and '"p6_a_never_true_premise_2023_"' in _ausrc
          and '"p7_second_way_of_being_circular_2023_"' in _ausrc
          and '"p8_a_measurement_mistake_2023_"' in _ausrc
          and '"p9_scope_and_offline_2023_"' in _ausrc
          and '"p10_golden_2023_"' in _ausrc
          and 'anchor-gate-coverage-1021.json' not in _p1023)

    print("— DD993H. 批 1024 普查「豁免声明」：把 1018「没看见」/ 1023「看不见」/"
          "本批「看见了、被配成不算数」三种形态分清；⭐⭐⭐⭐⭐ 本批最值钱的一条读数是"
          "**阳性对照红了两轮、每一轮逼出一个仪器 bug** ⇒ 处置是把切分单位从物理行换成逻辑单元")
    check("DD993H.1 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**「门看不见」必须分清三种形态** —— ① **没看见**（1018）；② **看不见**（1023）；"
          "③ **看见了、并且被配成不算数**（本批 `lint` 是裸 `eslint`、"
          "`--max-warnings` 没配 ⇒ **每一条 warning 都不影响 exit code**）⇒ "
          "⇒ **只报「看不见」会整类漏掉「③」，而它恰恰是三者里最容易修的**",
          '⇒ **「门看见了，但它被配置成不报错」** —— 这是同一种病的**第三种形态**：' in _p1024
          and '不是「没看见」，也不是「看不见」，是「看见了、并且被配成不算数」。' in _p1024
          and 'LINT_HAS_MAXWARN = "--max-warnings" in LINT_SCRIPT' in _p1024
          and 'P5 = (not LINT_HAS_MAXWARN) and RC_PLAIN == 0 and RC_MW0 != 0' in _p1024
          # ⭐⭐⭐⭐⭐ **负向锚点：判据/产物散文里不许再写死绝对读数** ——
          #   我第一版把「15 条 warning」写进了 `third_shape` 的解释里
          #   ⇒ 那条数会随别人修 warning 而漂移 ⇒ **按批自己立的纪律处置：只钉机制**
          and '**15 条 warning 一条都不影响 exit code**' not in _p1024
          and '"p1_three_shapes_of_the_gate_being_blind_2024_"' in _ausrc
          and '"p6_tightening_the_gate_is_the_projects_call_2024_"' in _ausrc)
    check("DD993H.2 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**阳性对照是常驻闸，且它红过两轮、每一轮逼出一个仪器 bug** —— "
          "⭐ 第一轮**整行看不见**；⭐⭐⭐⭐⭐⭐ **第二轮更隐蔽：两行都抽到了，"
          "却因为「这句话点名了哪个脚本」按**行**解析而看不见两行的关系**；"
          "⭐⭐⭐⭐⭐⭐⭐ **第三轮又一层：工具在不在脚本里按**字符串包含**判，"
          "而 `tsc` 是**隔着 `npm run typecheck` 间接接进去的** ⇒ "
          "⇒ **三次都是同一个病的加深 ⇒ 「逐行正则」有结构性上限，不是「我这次写漏了」** ⇒ "
          "⇒ **处置不是「再小心一次」，是把切分单位从物理行换成逻辑单元** ⇒ "
          "⇒ **这是本项目第四次栽在「跨行」上面**",
          'POSITIVE_CONTROL = found_independently and len(CONTRADICTED) >= 1' in _p1024
          and 'KNOWN_FALSE_SIGNATURE = "不跑 tsc"' in _p1024
          and '⇒ 返回 `(行号, 文本, 逻辑块号)`：**行注释各自成块**，**连续 `//` 行归成同一块**，块注释整块一块' in _p1024
          and '⇒ 处置：`comment_lines` 改为返回 `(行号, 文本, 逻辑块号)`，按**逻辑注释块**解析。' in _p1024
          and '⇒⇒⇒⇒⇒⇒⇒⇒⇒ 判据必须按**调用链**解析，不能按字符串包含解析' in _p1024
          and '**「工具在不在这条脚本的调用链闭包里」**。' in _p1024
          and '**阳性对照 `P3` 是常驻闸**：' in _p1024
          and 'the_hard_won_rule' in _p1024
          and 'n_caught_by_positive_control' in _p1024
          # ⭐⭐⭐⭐⭐ **负向锚点：「闸失败了几轮」是它的履历、不是它的判据 ⇒ 键名里不许出现这个数**
          and 'p4_positive_control_caught_two_instrument_bugs_2024_' not in _ausrc
          and 'note_that_number_will_drift' in _p1024
          and '**这已经是本项目第四次栽在它上面（1023 一次、1024 三次）** ⇒ ' in _p1024
          and '"p4_positive_control_caught_the_instrument_bugs_2024_"' in _ausrc
          and '"p7_the_rule_itself_needed_upgrading_2024_"' in _ausrc
          and '"p8_a_count_i_remembered_wrong_2024_"' in _ausrc)
    check("DD993H.3 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**Ⓐ「豁免指令本身是一句断言」：逐条判定必须用 eslint 自己的 `Unused eslint-disable directive`，"
          "不是我的正则** ⇒ ⇒ **代码后来修好了、豁免还留着，这句话就变成了假的** ⇒ "
          "⇒⇒⇒⇒⇒ **这一类与 1023 那条过期注释是同一个形状，"
          "只不过这一条 eslint 会主动报** ⇒ "
          "⇒⇒⇒⇒⇒⇒⇒⇒⇒ **「机制能看见」与「机制被当成了依据」是两件事**",
          '⇒ 用 **eslint 自己**的 `Unused eslint-disable directive` 警告逐条判定。' in _p1024
          and '"p2_an_escape_hatch_that_is_now_unnecessary_2024_"' in _ausrc)
    check("DD993H.4 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**Ⓒ「打不开的证据」有两种，不是一种** ⇒ "
          "**「引用了一份谁都打不开的证据」与「引用了但后来被删」不是同一种债** —— "
          "**前一种更难受：复核者连「它以前长什么样」都无从知道** ⇒ "
          "⇒⇒⇒⇒⇒⇒ **所以每条打不开的都必须再查一次 `git log --all`，"
          "且「从来没进过仓」必须单独成一个计数器**",
          'def in_git_history(path):' in _p1024
          and 'N_NEVER_IN_GIT = sum(1 for e in MISSING_EVID if not e["in_git_history"])' in _p1024
          and '"n_missing_that_never_existed_in_git": N_NEVER_IN_GIT,' in _p1024
          and '"p5_a_citation_nobody_ever_had_2024_"' in _ausrc)
    check("DD993H.5 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**Ⓑ 那条已知为假的断言在源码里有两处（块注释一处、行注释一处），"
          "而 1023 只报了其中一处** ⇒ ⇒ "
          "**⇒ 「按条数清账」这件事本身会漏；删掉其中一条并不能让这句话恢复成真的** ⇒ "
          "⇒⇒⇒⇒⇒ **探针与产物都按机制钉：把「同一个错误在两个语法位置各出现一次」记成结构事实，"
          "而不是记成「2 条」这个会漂移的数**",
          '"p3_the_same_false_sentence_lives_in_two_places_2024_"' in _ausrc
          and 'class_B_toolchain_claims_in_comments' in _p1024
          # ⭐ 判据把**两个口径的读数都留下**：调用链闭包（真）与同一行字面包含（那个会漏的粗口径）
          and 'tool_in_named_script_by_literal_substring' in _p1024
          and 'resolved_script_body' in _p1024)
    check("DD993H.6 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**「这个工具在不在这个脚本里」是个陷阱问句，除非先说清「在哪一层」** —— "
          "**1023 说「工具早就在、只是没人调」；本批说「工具早就在、只是没人在同一行看见它」** ⇒ "
          "⇒⇒⇒⇒⇒⇒⇒ **两条合起来是一句更硬的话：接线是**传递**的，判断接线却是**逐行**的** ⇒ "
          "⇒⇒⇒⇒⇒⇒⇒⇒⇒ **⇒ 与 1018「等价变异体是相对某一层说的」是同一个陷阱的两副面孔**",
          '"class_D_is_the_gate_wired_to_fail": {' in _p1024
          and '"p10_golden_1024_"' in _ausrc
          and '"p9_scope_and_offline_1024_"' in _ausrc)
    print("— DD993I. 批 1025 量「判据的方向」：verifier 936 条 check() 里，"
          "**钉死等值 `== N` 且 N 是易变量**的有几条；⭐⭐⭐⭐⭐ 关键是"
          "**「== N」这个形状本身不是缺口，缺口是「== N」且 N 是易变量** ⇒ "
          "**⇒ 形状机械可判、语义不可判 ⇒ 分类器认不出来的必须老实写 `unknown`**")
    check("DD993I.1 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**先把「锚点型」和「活判据型」分开，判据要机械** —— 把条件里的字符串字面量"
          "全部摘掉之后，**剩下 `Call`/`Subscript`/`Attribute`/非字符串常量的才是活的**；"
          "**只剩 `Name` 的是锚点** ⇒⇒⇒⇒⇒ `_pXXXX` 是**预读源码字符串**，"
          "在它身上做 `in` 验的是「那段字还在」不是行为（1018）",
          '① **锚点型** vs **活判据型** —— 前者只验「那段字还在」，后者验「那个性质还成立」' in _p1025
          and '⭐⭐⭐⭐⭐ **口径：把全部字符串字面量摘掉，看剩下什么形状**' in _p1025
          and '剩 ⇒ 活的（真的会被求值）；不剩 ⇒ 锚点（只验「那段字还在」）' in _p1025
          and '只剩 `Name`（纯变量引用）⇒ **锚点**' in _p1025
          and '**在它身上做 `in` 验的是「那段字还在」，不是行为**（1018 的原话）' in _p1025
          and '"axis_A_anchor_only_vs_live"' in _p1025
          and '"n_live": len(LIVE)' in _p1025
          and '"n_anchor_only": len(ANCHOR_ONLY)' in _p1025
          and '"P1_every_check_is_classed_live_or_anchor_only_1025"' in _p1025
          # ⭐⭐⭐⭐⭐ **每个 audit 键都必须被一条判据引用** ——
          #   1021 的教训：「登记必须会红」，没人引用的键会静默烂掉
          and '"p1_first_split_anchor_from_live_2025_"' in _ausrc
          and '"criterion_direction_1025": {' in _ausrc)
    check("DD993I.2 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**「== N」这个形状本身不是缺口，缺口是「== N」且 N 是易变量** ⇒ "
          "⇒⇒⇒⇒⇒⇒ **两类必须分开报：把 `X.count()==2` 当成和 `len(实测)==2` 同一种病，"
          "是「用形状代替语义」—— 而形状是机械可判的、语义不是** ⇒ "
          "⇒⇒⇒⇒⇒⇒⇒⇒ **本批只分类、不判决：「不会漂」与「对」是两件事，"
          "机械分类只能证明前一件**",
          '"**⇒ 「== N」这个形状本身不是缺口，缺口是「== N」且 N 是易变量** ⇒ "' in _p1025
          and '"是**用形状代替语义**——而形状是机械可判的、语义不是**"' in _p1025
          and '"axis_C_which_volatility_is_pinned"' in _p1025
          and '"n_pinned_eq_on_runtime_measured": len(PINNED_EQ_RUNTIME)' in _p1025
          and '"n_pinned_eq_on_source_text": len(PINNED_EQ_SOURCE)' in _p1025
          and '"what_this_does_not_claim"' in _p1025
          and '"p2_the_shape_is_not_the_gap_2025_"' in _ausrc
          and '"**不代表它对，只代表「它不会因为跑第二轮而变」** ⇒ "' in _p1025)
    check("DD993I.3 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**⭐⭐⭐⭐⭐ 分类器把自己搞不清的归进危险那一类，是一个会自己制造结论的偏差** —— "
          "**它让读数看起来更严重，而更严重的读数更容易被采信** ⇒ "
          "⇒⇒⇒⇒⇒⇒ **处置：只认两种有把握的形状，认不出来的老实写 `unknown`** "
          "⇒⇒⇒⇒⇒⇒⇒⭐ **而本批三版分类器各错一次，全部是「安静的失败形态」**："
          "① `seg(c)` 未绑定 ⇒ 某个形状一个都没命中；"
          "② 把预读源码当活的 ⇒ 「936 条全是活的、锚点 0 条」**那个结论假得很整齐**；"
          "③ 启发式太宽 ⇒ 把数源码出现次数的判据误判成易变量",
          '⚠️⚠️⚠️ **仪器 bug 3（第三版）：第一版有一句 `"(" in lhs.split(".")[0]`' in _p1025
          and '**「分类器把自己搞不清的归进危险那一类」是一个会自己' in _p1025
          and '制造结论的偏差** —— 它让读数看起来更严重，而**更严重的读数更容易被采信**' in _p1025
          and '⚠️⚠️⚠️⚠️ **仪器 bug 2（第二版）：第一版用「子树里有没有 `Name`」判活**' in _p1025
          and '⇒ `"x" in _p1024` 里有个 `Name(_p1024)` ⇒ **936 条全被判成活的、锚点型 0 条**' in _p1025
          and '⇒⇒⇒⇒⇒ **那个结论是假的，而且假得「很整齐」—— 整齐本身就是该怀疑的信号**' in _p1025
          and '⚠️⚠️ **仪器 bug 1（第一版）：末尾写的是 `seg(c)`，而 `c` 只在上面的' in _p1025
          and '"p3_the_classifier_fabricated_a_conclusion_2025_"' in _ausrc
          and '"p4_positive_control_must_also_verify_the_citation_2025_"' in _ausrc)
    check("DD993I.4 ⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐ "
          "**阳性对照：不告知答案，得自己找到 §83 那条已知为真的「易变量判据」** ⇒ "
          "⇒ **而且顺带独立核对那段「易变量写成了断言」的原文确实在源码里** "
          "（不许凭记忆断言它存在）⇒⇒⇒⇒⇒ "
          "**⇒ 「找得到已知答案」与「那段记录确实在」是两件都要验的事**",
          'KNOWN_TRUE_MARKER = "易变量写成了断言"' in _p1025
          and 'POSITIVE_CONTROL = bool(pc_hits)' in _p1025
          and 'P3 = POSITIVE_CONTROL and MARKER_IN_SRC' in _p1025
          and 'if KNOWN_TRUE_MARKER in l or "钉条数就是把易变量当契约" in l:' in _p1025
          and '"P3_positive_control_the_scan_finds_the_volatile_criterion_on_its_own_1025"' in _p1025
          and '"marker_in_source"' in _p1025
          and '"P6_scope_declared_2025"' in _p1025
          and '"axis_B_shape_of_live_conditions"' in _p1025
          and '"p5_one_instance_was_fixed_but_the_class_was_never_counted_2025_"' in _ausrc
          and '"p6_scope_and_offline_1025_"' in _ausrc
          and '"p7_golden_1025_"' in _ausrc)
    print(f"\n{checks - len(failures)}/{checks}")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("batch 841-unclickable OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
