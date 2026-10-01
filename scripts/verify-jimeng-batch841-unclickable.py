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
    any_bad = bool(real or kb_bad or kb_cov or kb_ni or kb_esc or kb_arr)
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
    check("G.3b 每条 finding 指名**被哪个浮层盖住**（浮层锚的对照，不是光说看不见）",
          bool(kb_cov) and all(
              (k.get("covered") or {}).get("top")
              and (k.get("covered") or {}).get("top_anchor")
                  != (k.get("covered") or {}).get("focus_anchor")
              and (k.get("covered") or {}).get("edges")
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
    check("G.5 自检用的层必须是**深**的（Tab 1 就进去的层照不到被遮住的控件）",
          kbst.get("covered_probe_layer") == "jimeng-search-overlay",
          f"实际={kbst.get('covered_probe_layer')!r}")
    check("G.6 键盘探针在每一步都判「焦点是否被遮住」（源码里真有这一步）",
          "state: occluded ? 'covered' : 'other'" in asrc)
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
    # ⚠️ 方向键这一项**没测到**（探针 850 在它上面栽了六次，见 README §68）。
    #    `None` 是 falsy ⇒ 不产生 finding、也不当通过。这一条钉住「不许
    #    偷偷把它填成 True/False」—— 填哪个都是编。
    check("J.3 方向键一项是 `None`（**没测到**），不许被填成 True/False",
          all(base.get(t, {}).get("arrows_move", "MISSING") is None
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
    AUD_OK = ["audio-voice-model-listbox", "audio-gen-mode-listbox"]
    AUD_MISS = ["audio-music-model-listbox", "audio-music-duration-listbox",
                "audio-all-voices-listbox"]
    check("K.1 取到样的 2 层**在基线表里**（851b 实测：接管焦点 / 不困 Tab /"
          " Esc 不归位）",
          all(t in base for t in AUD_OK),
          f"{[t for t in AUD_OK if t in base]}")
    check("K.2 那 2 层的方向键仍是 `None`（**没测到**），不许填成 True/False",
          all(base.get(t, {}).get("arrows_move", "MISSING") is None
              for t in AUD_OK),
          f"{ {t: base.get(t, {}).get('arrows_move', 'MISSING') for t in AUD_OK} }")
    whys = [n.get("why", "") for n in kb_ns
            if n.get("layer") in AUD_MISS]
    check("K.3 没取到的 3 层**仍留在** `kb_not_sampled`"
          "（实测不到 ≠ 可以按「同类层」推测）",
          all(t not in base and t in {n.get("layer") for n in kb_ns}
              for t in AUD_MISS),
          f"进了基线表的：{[t for t in AUD_MISS if t in base]}")
    check("K.4 这 3 层的 why **互不相同**（笼统一句「没取过样」会把"
          "「前置态没成立」和「判据量错对象」混成一种）",
          len(whys) == len(AUD_MISS) and len(set(whys)) == len(whys)
          and any("前置态没成立" in w for w in whys)
          and any("量错对象" in w for w in whys),
          f"{len(whys)} 条 why，去重后 {len(set(whys))} 条")
    # 音色库那条必须点明「伪像」——它读出来的「源站不接管焦点」是认错层造成的
    av = next((n.get("why", "") for n in kb_ns
               if n.get("layer") == "audio-all-voices-listbox"), "")
    check("K.5 音色库那一层的 why 写明读出来的结论是**伪像**"
          "（判据把整页容器当成了层；放宽判据只会把伪像洗成结论）",
          "伪像" in av and "648" in av, f"why={av[:60]!r}")
    # 产品侧：**只接取到样的 2 层**
    audp = ROOT / "src/components/jimeng/JimengAudioGenPanel.tsx"
    asrc2 = audp.read_text(encoding="utf-8") if audp.exists() else ""
    check("K.6 复刻接了**取到样的 2 层**（voiceBoxRef / dubBoxRef）",
          all(f"useTakeFocusAtOpen({v}" in asrc2
              for v in ("voiceBoxRef", "dubBoxRef"))
          and all(f"ref={{{v}}}" in asrc2 for v in ("voiceBoxRef", "dubBoxRef")),
          f"接上 {sum(1 for v in ('voiceBoxRef', 'dubBoxRef') if f'useTakeFocusAtOpen({v}' in asrc2)}/2")
    # ⚠️ 核心：**没取到样的 3 层不许接** —— 接了就是「源站测不到的行为也实现」
    not_connected = [v for v in ("musicBoxRef", "durBoxRef", "voicesBoxRef")
                     if f"useTakeFocusAtOpen({v}" in asrc2]
    check("K.7 **没取到样**的 3 层**不许**接那个 hook"
          "（接了就是「伪称可用」，比不做更坏）",
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

    print(f"\n{checks - len(failures)}/{checks}")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("batch 841-unclickable OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
