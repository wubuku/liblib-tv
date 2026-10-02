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
]

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
    """真正剥掉 JS/TS/Python 注释，供「代码里到底有没有 X」用。

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
    check("A.3 skipped（前置态没成立）= 0 —— 不许静默少跑",
          not data.get("skipped"), "; ".join(data.get("skipped", [])[:2]))

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

    print(f"\n{checks - len(failures)}/{checks}")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("batch 841-unclickable OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
