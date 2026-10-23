#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 857 门禁：导演台「群众阵列（crowd）」对话框（对齐源站逐字）。

## ★ 这批要守住的东西

★ 靶子：源站「添加群众阵列」对话框的**参数、落点、开关行为**，
  以及 clone 里**多出来的那个入口**。

| | 源站 | clone（整改前） | clone（整改后） |
| --- | --- | --- | --- |
| crowd 入口数（**桌面可见**） | **1** | **2**（rail ＋ 视口工具栏） | **1**（rail） |
| 对话框落点 | **按钮 right+8 / 按钮 top** | 写死「rail+294」 | **按钮 right+8 / 按钮 top** |
| 间距 onChange | **保留 1 位小数** | 原样透传 | **保留 1 位小数** |
| 行/列/间距量程 | **1–10 / 1–10 / 0.1–10** | 对话框对、store 又夹一层 | **1–10 / 1–10 / 0.1–10**（store 不夹） |
| 再点一次「群众 (3x3)」 | **关闭** | 无脑重开 | **关闭** |
| 点对话框/按钮**外面** | **关闭** | 只能按「取消」 | **关闭** |

★ 源站逐字（机器提取见 `raw/source-857-contract.json`，13/13 唯一命中）：
  `[K,Q]=useState(1.2)` ｜ `Math.min(10,Math.max(.1,Math.round(10*t)/10))`
  ｜ `W({left:t.right+8,top:t.top})` ｜ `if("crowd"===L)return void O(null)`
  ｜ `en.current?.contains(t)||ea.current?.contains(t)||O(null)`
★ 源站实测（`raw/source-857-crowd.json`）：
  对话框 **220×204 @(280,388)** ｜ 间距填 1.55 ⟹ **读回 1.6** ｜
  ★ **自指判据**：全页 `aria-label == 添加群众阵列` 的元素**只有 1 个**
  ⟹ ⟹ 源站**只有一个入口**。

## ★ ★ 判据分工（★ 各条读的字段互不重叠 ⟹ ⟹ 阴性每条只翻它自己那一条）

| 判据 | 读什么 | 阴性 |
| --- | --- | --- |
| S1 | 契约：13 个片段**唯一命中** ＋ 关键逐字 ＋ 两项自检 | N1 |
| S2 | 源站实测：对话框 **220×204 @(280,388)** ＋ 三个输入的量程/初值 | N2 |
| S3 | 源站**行为**：间距填 1.55 ⟹ **读回 1.6** | N3 |
| S4 | 源站**唯一入口**（自指判据 count == 1） | N4 |
| S5 | 源站逐字：开关 ＋ 点外面关闭 ＋ aria-expanded | N5 |
| S6 | clone 实测：落点 **＝ 按钮 right+8 / 按钮 top** | N6 |
| S7 | clone **行为**：间距填 1.55 ⟹ **读回 1.6** | N7 |
| S8 | clone 实测：再点一次 ⟹ 关；点外面 ⟹ 关 | N8 |
| S9 | clone 实测：**桌面可见入口 == 1** | N9 |
| S10 | clone 实测：**移动端可见入口 == 1**，开的是**同一个**对话框 | N10 |
| S11 | clone 源码：legacy 面板/选择器**清零** ＋ 1 位小数 ＋ store 不夹取 | N11／N12 |
| S12 | 老门禁迁移：`45.py`（crowd 段迁到 rail）＋ `625.py`（落点改推导） | N13／N14 |

## ★ ★★ **本门禁是「归档型」⟹ ⟹ 它没有运行时牙**（batch 858 受控对照实测）

★ S2–S10 读的**全是 batch 857 当时录下的 JSON 产物**
（`raw/source-857-contract.json`／`raw/source-857-crowd.json`／
`raw/source-857-mobile.json`／`raw/clone-857-crowd.json`）
⟹ ⟹ **不是实时 DOM** ⟹ ⟹ 把源码换回去它**照样绿**。

★ batch 858 的**受控对照**（`docs/research/liblib-canvas-batch858-2026-10-01/`
的 `probes/attrib858_mix.py`）实测：
- **MIX 半回退态**（只把 `DirectorIconRail.tsx` ＋ `DirectorDesk.tsx` 换回 HEAD）
  ⟹ ⟹ 本门禁 **12/12 全绿**；
- 而同态下 `verify-liblib-batch858.py` **红 21 条**、`45`／`536`／`589`／
  `613`／`625`／`738` **全红**。
⟹ ⟹ **结论：这是「职责边界」、不是漏洞** —— 本门禁守的是 **crowd 对话框契约**
（量程／落点／开关行为），**不守「面板 vs 浮层」这个结构**；
后者由 **live DOM 门禁**（858 等）守。

★ ★ 顺带一条方法学：**「红了」≠「判据红了」**。
本门禁在 **HEAD 全回退态**下是红的，但那红来自
`FileNotFoundError: DirectorCharacterPanel.tsx`（读不到文件）⟹ ⟹ **假牙**；
只有 MIX 半回退态里「**具名判据**翻红」才叫真牙。

## ★ ★★ **S3/S7 是「源站 ↔ clone」的行为交叉**

★ 只断言 clone 是 1.6 ⟹ ⟹ 那可能只是「探针瞎了」⟹ ⟹ 所以必须**同时**
断言「**同一个动作**在源站上读回 1.6」（S3）与「在 clone 上读回 1.6」（S7）
⟹ ⟹ **两边的读数证明这条行为规则不是 clone 自己发明的**。
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch857-2026-10-01"
RAW = BATCH / "raw"

SRC_RAIL = ROOT / "src/components/director/DirectorIconRail.tsx"
# ★ Batch 858：「添加角色」改成**左侧面板模式**（源站逐字）⟹ ⟹ 间距的
#   1 位小数舍入代码从 rail 搬到了 DirectorCharacterPanel.tsx ⟹ ⟹
#   静态契约要跟着搬（**判据内容一字未改**）。
SRC_CHAR_PANEL = ROOT / "src/components/director/DirectorCharacterPanel.tsx"
SRC_VIEWPORT = ROOT / "src/components/director/DirectorViewport.tsx"
SRC_STORE = ROOT / "src/store/directorStore.ts"

results = []


def record(name, ok, detail):
    results.append({"判据": name, "通过": bool(ok), "详情": detail})
    print(("  PASS  " if ok else "  FAIL  ") + name + " ｜ " + detail)


def main() -> int:
    for p in (RAW / "source-857-contract.json",
              RAW / "source-857-crowd.json",
              RAW / "source-857-mobile.json",
              RAW / "clone-857-crowd.json"):
        if not p.exists():
            print("★★ 缺产物：%s" % p)
            return 2

    contract = json.loads((RAW / "source-857-contract.json").read_text(encoding="utf-8"))
    src = json.loads((RAW / "source-857-crowd.json").read_text(encoding="utf-8"))
    src_m = json.loads((RAW / "source-857-mobile.json").read_text(encoding="utf-8"))
    clone = json.loads((RAW / "clone-857-crowd.json").read_text(encoding="utf-8"))
    rail_src = SRC_RAIL.read_text(encoding="utf-8")
    char_panel_src = SRC_CHAR_PANEL.read_text(encoding="utf-8")
    view_src = SRC_VIEWPORT.read_text(encoding="utf-8")
    store_src = SRC_STORE.read_text(encoding="utf-8")

    # ══════════════════════════════════════════════════════════════════
    # S1 契约：13 个片段唯一命中 ＋ 关键逐字 ＋ 两项自检
    # ══════════════════════════════════════════════════════════════════
    frags = contract.get("片段", {})
    uniq = [k for k, v in frags.items() if v.get("锚点命中数") == 1 and v.get("原文")]
    key_verbatim = [
        ("对话框 state 初值（行3／列3／间距1.2 ＝ 真正生效的默认值）",
         "[U,H]=(0,o.useState)(3),[V,G]=(0,o.useState)(3),[K,Q]=(0,o.useState)(1.2)"),
        ("间距 onChange（夹 [0.1,10] ＋ 保留 1 位小数）",
         "Math.min(10,Math.max(.1,Math.round(10*t)/10))"),
        ("「添加」按钮的载荷（count ＝ 行×列）",
         "h({count:U*V,crowdRows:U,crowdCols:V,crowdSpacing:K}),O(null)"),
        ("add 回调的兜底（不夹取；1.6 只是兜底、不是默认值）",
         "let{count:t,crowdRows:r,crowdCols:n,crowdSpacing:a,...i}=e,o=t??1,s=r??1,l=n??o,c=a??1.6"),
        ("rail 入口的结构特征（aria-haspopup=dialog ＋ crowd 状态）",
         '"aria-haspopup":"dialog","aria-expanded":"crowd"===L'),
    ]
    verbatim_ok = all(
        needle in frags.get(name, {}).get("原文", "")
        for name, needle in key_verbatim
    )
    arb_ok = contract.get("★任意值类名自检", {}).get("通过") is True
    # ★ 跨片段防呆：初值 1.2 ≠ 兜底 1.6 ⟹ ⟹ 「把 1.6 当默认值」是错的
    cross_ok = contract.get("★跨片段防呆自检（初值 ≠ 兜底）", {}).get("通过") is True
    record("S1 契约：17 个片段唯一命中 ＋ 5 条关键逐字 ＋ 两项自检",
           len(uniq) == 17 and verbatim_ok and arb_ok and cross_ok,
           "唯一命中 %d/17 ｜ 关键逐字 %s ｜ 任意值自检 %s ｜ 跨片段防呆 %s"
           % (len(uniq), verbatim_ok, arb_ok, cross_ok))

    # ══════════════════════════════════════════════════════════════════
    # S2 源站实测：对话框 220×204 @(280,388) ＋ 三个输入的量程/初值
    # ══════════════════════════════════════════════════════════════════
    crowd = src.get("④对话框", {}).get("crowd", {})
    vals = {v.get("aria"): v for v in (crowd.get("vals") or [])}
    s2_ok = (
        crowd.get("w") == 220 and crowd.get("h") == 204
        and crowd.get("x") == 280 and crowd.get("y") == 388
        and vals.get("行数", {}).get("min") == "1"
        and vals.get("行数", {}).get("max") == "10"
        and vals.get("行数", {}).get("v") == "3"
        and vals.get("列数", {}).get("v") == "3"
        and vals.get("间距", {}).get("min") == "0.1"
        and vals.get("间距", {}).get("max") == "10"
        and vals.get("间距", {}).get("step") == "0.1"
        and vals.get("间距", {}).get("v") == "1.2"
    )
    record("S2 源站实测：对话框 220×204 @(280,388) ＋ 量程/初值",
           s2_ok,
           "盒 %sx%s @(%s,%s) ｜ 间距 %s ｜ 行 %s ｜ 列 %s"
           % (crowd.get("w"), crowd.get("h"), crowd.get("x"), crowd.get("y"),
              vals.get("间距"), vals.get("行数"), vals.get("列数")))

    # ══════════════════════════════════════════════════════════════════
    # S3 源站**行为**：间距填 1.55 ⟹ 读回 1.6（行为证据，不是读代码）
    # ══════════════════════════════════════════════════════════════════
    s3_ok = src.get("⑥间距填1.55后") == "1.6"
    record("S3 源站行为：间距填 1.55 ⟹ 读回 1.6（保留 1 位小数）",
           s3_ok, "源站读回 %r" % (src.get("⑥间距填1.55后"),))

    # ══════════════════════════════════════════════════════════════════
    # S4 源站**唯一入口**（自指判据：全页同 aria-label 的元素只有 1 个）
    # ══════════════════════════════════════════════════════════════════
    same = src.get("⑤同aria元素", {}) or {}
    s4_ok = same.get("aria") == "添加群众阵列" and same.get("count") == 1
    record("S4 源站唯一入口：全页同 aria-label 的元素只有 1 个",
           s4_ok, "aria %r ｜ count %r ｜ 命中 %s"
           % (same.get("aria"), same.get("count"),
              [h.get("tag") for h in (same.get("hits") or [])]))

    # ══════════════════════════════════════════════════════════════════
    # S5 源站逐字：开关 ＋ 点外面关闭 ＋ aria-expanded
    #   （判据读的是**契约里的逐字**，不是 clone）
    # ══════════════════════════════════════════════════════════════════
    s5_need = [
        ('★开关：再点一次「群众 (3x3)」＝ 关闭对话框',
         'if("crowd"===L)return void O(null)'),
        ('★点外面关闭：点在按钮/对话框之外 ⟹ 关闭',
         'en.current?.contains(t)||ea.current?.contains(t)||O(null)'),
        ('rail 入口的结构特征（aria-haspopup=dialog ＋ crowd 状态）',
         '"aria-haspopup":"dialog","aria-expanded":"crowd"===L'),
    ]
    s5_missing = [
        name for name, needle in s5_need
        if needle not in frags.get(name, {}).get("原文", "")
    ]
    s5_ok = not s5_missing
    record("S5 源站逐字：开关 ＋ 点外面关闭 ＋ aria-expanded",
           s5_ok, "三条逐字均已机器提取入库 %s%s"
           % (s5_ok, ("｜ 缺 %s" % s5_missing) if s5_missing else ""))

    # ══════════════════════════════════════════════════════════════════
    # S6 clone 实测：落点 ＝ 按钮 right+8 / 按钮 top（源站公式）
    # ══════════════════════════════════════════════════════════════════
    place = clone.get("③落点是否符合源站公式", {}) or {}
    s6_ok = place.get("left相等") is True and place.get("top相等") is True
    record("S6 clone 实测：对话框落点 ＝ 按钮 right+8 / 按钮 top",
           s6_ok,
           "left 期望 %s 实测 %s（相等 %s）｜ top 期望 %s 实测 %s（相等 %s）"
           % (place.get("期望_left"), place.get("实测_left"),
              place.get("left相等"), place.get("期望_top"),
              place.get("实测_top"), place.get("top相等")))

    # ══════════════════════════════════════════════════════════════════
    # S7 clone 行为：间距填 1.55 ⟹ 读回 1.6（与 S3 同一动作、同口径）
    # ══════════════════════════════════════════════════════════════════
    clone_spacing = (clone.get("④间距填1.55后", {}) or {}).get("间距", {})
    s7_ok = clone_spacing.get("value") == "1.6"
    record("S7 clone 行为：间距填 1.55 ⟹ 读回 1.6（与源站同口径）",
           s7_ok, "clone 读回 %r" % (clone_spacing.get("value"),))

    # ══════════════════════════════════════════════════════════════════
    # S8 clone 实测：再点一次 ⟹ 关；点外面 ⟹ 关
    # ══════════════════════════════════════════════════════════════════
    toggle = clone.get("⑤再点一次后", {}) or {}
    outside = clone.get("⑦点外面之后", {}) or {}
    s8_ok = (toggle.get("对话框可见") is False
             and toggle.get("rail入口ariaExpanded") == "false"
             and outside.get("对话框可见") is False)
    record("S8 clone 实测：再点一次关 ＋ 点外面关（源站两条行为）",
           s8_ok,
           "再点一次后 对话框可见 %r / aria-expanded %r ｜ 点外面后 对话框可见 %r"
           % (toggle.get("对话框可见"), toggle.get("rail入口ariaExpanded"),
              outside.get("对话框可见")))

    # ══════════════════════════════════════════════════════════════════
    # S9 clone 实测：桌面**可见**入口 == 1（与源站的「唯一入口」同口径）
    # ══════════════════════════════════════════════════════════════════
    desk_n = clone.get("⑧桌面可见入口数")
    s9_ok = desk_n == 1
    record("S9 clone 实测：桌面可见的 crowd 入口 == 1",
           s9_ok, "桌面可见入口数 %r" % (desk_n,))

    # ══════════════════════════════════════════════════════════════════
    # S10 clone 实测：移动端可见入口 == 1，且开的是**同一个**对话框
    #   （★ 源站**没有移动端布局** ⟹ ⟹ 移动端那枚是 clone 自己的扩展）
    # ══════════════════════════════════════════════════════════════════
    mob = clone.get("⑩移动端点开对话框", {}) or {}
    mob_toggle = clone.get("⑪移动端再点一次", {}) or {}
    src_has_mobile = (src_m.get("①导演台开着了") is False
                       and src_m.get("②aside") == [])
    s10_ok = (
        mob.get("可见入口数") == 1
        and mob.get("移动端入口可见") is True
        and mob.get("rail入口可见") is False
        and (mob.get("对话框") or {}).get("w") == 220
        and (mob.get("间距") or {}).get("value") == "1.2"
        and src_has_mobile
        # ★ 移动端那枚也得是**开关**（源站的「群众 (3x3)」是开关 ⟹ ⟹
        #   clone 自己的扩展要同语义 ⟹ ⟹ 不然就是「点了没反应」）
        and mob_toggle.get("对话框可见") is False
    )
    record("S10 clone 实测：移动端可见入口 == 1 ＋ 开的是同一个对话框 ＋ 那枚也是开关",
           s10_ok,
           "移动端可见入口数 %r ｜ 移动端入口可见 %r ｜ rail 入口可见 %r ｜ "
           "对话框宽 %r ｜ 间距初值 %r ｜ 再点一次后对话框可见 %r ｜ 源站无移动端布局 %s"
           % (mob.get("可见入口数"), mob.get("移动端入口可见"),
              mob.get("rail入口可见"), (mob.get("对话框") or {}).get("w"),
              (mob.get("间距") or {}).get("value"),
              mob_toggle.get("对话框可见"), src_has_mobile))

    # ══════════════════════════════════════════════════════════════════
    # S11 clone 源码：legacy 清零 ＋ 1 位小数 ＋ store 不夹取
    # ══════════════════════════════════════════════════════════════════
    legacy = ["data-director-crowd-trigger", "data-director-crowd-panel",
              "data-director-crowd-rows", "data-director-crowd-columns",
              "data-director-crowd-spacing", "data-director-crowd-action"]
    legacy_left = [s for s in legacy if s in view_src]
    s11_legacy_ok = not legacy_left
    s11_round_ok = "Math.round(next * 10) / 10" in char_panel_src
    # ★ store 的判据要**限定在 addCrowdArray 那段函数体里** ——
    #   否则整份 store 里的 `Math.min(` 会被误算成「还在夹取」。
    m = re.search(r"addCrowdArray:\s*\(\{[^)]*\)\s*=>\s*\{", store_src)
    body = ""
    if m:
        depth = 0
        i = m.end() - 1
        for j in range(i, len(store_src)):
            if store_src[j] == "{":
                depth += 1
            elif store_src[j] == "}":
                depth -= 1
                if depth == 0:
                    body = store_src[m.start():j + 1]
                    break
    s11_store_ok = (
        bool(body)
        and "Math.min(" not in body
        and "spacing ?? 1.6" in body
        and "Math.max(1," in body
    )
    record("S11 clone 源码：legacy 选择器清零 ＋ 间距保留 1 位小数 ＋ store 不夹取",
           s11_legacy_ok and s11_round_ok and s11_store_ok,
           "legacy 残留 %s ｜ 1 位小数 %s ｜ store 不夹取 %s（函数体 %d 字，"
           "含 Math.min %s、含 1.6 兜底 %s）"
           % (legacy_left, s11_round_ok, s11_store_ok, len(body),
              "Math.min(" in body, "spacing ?? 1.6" in body))

    # ══════════════════════════════════════════════════════════════════
    # S12 老门禁迁移：45.py（crowd 段迁到 rail ＋ 负向断言）＋ 625.py（落点改推导）
    # ══════════════════════════════════════════════════════════════════
    g45 = ROOT / "scripts/verify-liblib-batch45.py"
    g625 = ROOT / "scripts/verify-liblib-batch625.py"
    s12_ok = False
    s12_detail = ""
    if g45.exists() and g625.exists():
        t45 = g45.read_text(encoding="utf-8")
        t625 = g625.read_text(encoding="utf-8")
        # 45：crowd 段必须走 rail 的对话框（不再是 legacy 视口面板）
        #   ★ 判据要**区分「用 locator 取」与「出现在负向断言清单里」** ——
        #   ⟹ ⟹ 否则「负向断言里写了 legacy 名字」会被误判成「还在用」。
        legacy_in_locator = [
            s for s in legacy
            if re.search(r"locator\([^)]*" + re.escape(s), t45)
        ]
        s12_45 = ("[data-director-character-option='crowd-3x3']" in t45
                  and "[data-director-crowd-dialog]" in t45
                  and not legacy_in_locator)
        # 45：必须有「关掉浮层」这一步（否则点组行 toggle 会被浮层截走）
        s12_45b = ("[data-director-rail-entry='scene']" in t45
                   and "data-director-character-panel" in t45)
        # 45：必须对 legacy 选择器有**负向断言**（只写正向的话旧写法还在也能过）
        s12_45c = all(s in t45 for s in legacy)
        # 625：crowd-dialog 的期望必须**按源站公式推导**，旧的写死坐标要清零
        s12_625 = ('"crowd-dialog": [294, 52, 220, 208]' not in t625
                   and "anchor[\"right\"] + 8" in t625
                   and "anchor[\"top\"]" in t625
                   and "crowd-dialog-width-is-220" in t625)
        s12_ok = s12_45 and s12_45b and s12_45c and s12_625
        s12_detail = ("45: 迁到 rail %s ｜ 45: 关浮层 %s ｜ 45: 负向断言 %s ｜ "
                      "625: 落点改推导 %s"
                      % (s12_45, s12_45b, s12_45c, s12_625))
    else:
        s12_detail = "★ 缺 45.py / 625.py"
    record("S12 老门禁迁移：45.py（crowd 段迁到 rail）＋ 625.py（落点改推导）",
           s12_ok, s12_detail)

    # ── 汇总 ──────────────────────────────────────────────────────────
    out_path = BATCH / "runtime-audit.json"
    out_path.write_text(
        json.dumps({"批次": 857, "判据": results}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    passed = sum(1 for r in results if r["通过"])
    print("\n%d/%d 条通过" % (passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
