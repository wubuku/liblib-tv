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
    r = subprocess.run([sys.executable, str(AUDIT)], capture_output=True,
                       text=True, env=env, cwd=str(ROOT), timeout=600)
    out = (r.stdout or "") + (r.stderr or "")
    data = {}
    if OUT.exists():
        try:
            data = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            data = {"_parse_error": str(e)}
    states = data.get("states", [])
    real = data.get("confirmed", [])
    by_modal = data.get("by_modal", [])
    st = data.get("self_test", {})
    kb = data.get("keyboard", [])
    kb_bad = data.get("keyboard_bad", [])
    kb_deep = data.get("keyboard_deep", [])
    kb_cov = data.get("keyboard_covered", [])
    kbst = data.get("kb_self_test", {})

    # ── A. 普查本身 ───────────────────────────────────────────────
    print("— A. 普查跑通 —")
    # A.0 退出码：不能只看"是不是 0"。本批工具**真报出 3 条焦点被遮的缺陷**，
    #     退出码 1 是判据在干活，不是工具坏了。所以断言改成**与桶一致**：
    #     任一缺陷桶非空就必须非 0，三个桶全空才 0。这条能两个方向失败 ——
    #     把 kb_covered 从退出码里漏掉（缺陷被当通过放行），或者干脆写死 0，
    #     都会被抓住；全空时想靠"反正不空"蒙混也过不去。
    any_bad = bool(real or kb_bad or kb_cov)
    check(f"A.0 退出码与缺陷桶一致（任一桶非空 ⇒ 非 0；实测 rc={r.returncode}，"
          f"real={len(real)} / kb_bad={len(kb_bad)} / kb_covered={len(kb_cov)}）",
          r.returncode == (1 if any_bad else 0),
          f"rc={r.returncode}")
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
    check("E.7 最终退出码由**三个**缺陷桶推出"
          "（`real` / `kb_bad` / `kb_covered`，不许写死 0）",
          "return 1 if (real or kb_bad or kb_covered) else 0" in asrc)
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
    # 自检：盖一层遮挡物，被遮住的焦点位必须**变多**。比的是计数不是"有没有" ——
    # 基线里本来就真有几处（那正是本批查出来的缺陷），"撤掉后不再报"是错前提，
    # 第一版就栽在这儿、自检把自己判红了。
    check("G.4 自检：盖上遮挡物后被遮住的焦点位**变多**（判据对遮挡敏感）",
          (kbst.get("covered_n_when_shut") or 0)
          > (kbst.get("covered_n_when_clear") or 0),
          f"{kbst.get('covered_n_when_clear')} → {kbst.get('covered_n_when_shut')}")
    check("G.5 自检用的层必须是**深**的（Tab 1 就进去的层照不到被遮住的控件）",
          kbst.get("covered_probe_layer") == "jimeng-search-overlay",
          f"实际={kbst.get('covered_probe_layer')!r}")
    check("G.6 键盘探针在每一步都判「焦点是否被遮住」（源码里真有这一步）",
          "state: occluded ? 'covered' : 'other'" in asrc)
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

    print(f"\n{checks - len(failures)}/{checks}")
    if failures:
        print("FAILED: " + ", ".join(failures))
        return 1
    print("batch 841-unclickable OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
