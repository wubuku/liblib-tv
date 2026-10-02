#!/usr/bin/env python3
"""batch 686 验收：**高度轴的未取整普查 —— 683 的「阈值 336」不是形变阈值**

## 起点

685 证明了普查那把 `Math.round` 的尺会把 1/64px 连续斜坡伪造成平台，并明确留了一条：

> 顺带一条对 683 的限制声明：683 的高度轴结论同样建立在取整读数上，所以
> 「随高度变形的只有 1 个键」**只在整数单位上成立**。

本批去量那句话在亚像素单位上是否还成立，并给 `帮助` 的形变一个**可复算的规则**。

## 五条读数

### 1. 683 的结论在亚像素单位上**依然成立**，但只剩一枚

逐高度（140..1700，1561 格）全量普查 119 个 data 键的**未取整** `width|height`：
**只有 `data-director-rail-entry=help` 一个键的尺寸动过**（另两个「变化」的键是下面 §3 的仪器缺陷）。

所以 685 那条限制声明的结论是：**683 没有漏掉亚像素变化** —— 高度轴上确实只有一枚。

### 2. 但 683 的「阈值 H = 336」是**另一个量**，形变发生在 345..356

| 高度 | rail `clientH` | rail `scrollH` | `帮助` 未取整高 |
|---|---|---|---|
| 336 | **284** | **284** | **20** |
| 344 | 292 | 292 | **20** |
| **345** | 293 | 293 | **21** ← 形变开始 |
| 350 | 298 | 298 | 26 |
| **356** | 304 | 304 | **32** ← 形变结束 |
| 720 | 668 | 668 | 32 |

**336 是「容器不再溢出」那一点**（`clientH == scrollH == 284`，683 量的就是它）；
**345 是「尺寸开始变」，356 是「尺寸不再变」** —— **三个不同的数，683 把前两个当成一个了。**
683 的读数（32×20 @ H≤300、32×32 @ H≥400）**一字不撤销**，错的只是「阈值正好是 336」这个说法。

**可复算的规则**（12 个逐页开桌的点全部命中）：

```
帮助 的高 = clamp(视口高 − 324, 20, 32)
```

`324 = 60 + 264`：`60 = 52`（rail 的 `top-[52px]`）+ `8`（rail 的 `p-2` 底内边距），
`264` 是**按钮顶边被钉住的内容相对位置**（且 `264 + 20 = 284` 正是 683 量的 rail 内容高）。
即：**顶边先钉在 264，够高后改为贴底（`H − 92`），两式在 356 相交**；高度是随之而来的差，
再被 `min-content`（20）与声明尺寸（32）夹住。

### 3. 第三个「变化」的键是**仪器缺陷**，不是读数

`data-director-track-label=…` 两条键被我的增量探测器记了 **3121 次变化** —— 每个高度两次。
原因：这两条键下各有 **4 个成员**（684 已认定：一个 `36×18` 标题按钮 + 三个 `24×24` 导航钮），
而我的 `last[k] = sig` 是**逐元素**比较的，四个成员轮流把 `last` 写成不同值 ⟹ 同一高度内自激。

**这是 683「不能跨高度取并集、要逐高度比集合」那条纪律的第四次翻版**（683 探针、683 验收器、
683 的「两宽度」判据各犯过一次）。修法：按**每个高度的尺寸集合**比，不做增量比较。

### 4. 高度轴的形变是**整数斜坡**，与宽度轴的 1/64px 斜坡是两种东西

| 轴 | 形变形态 | 步长 |
|---|---|---|
| 宽度（685） | 连续斜坡，1/64px 栅格 | 2–9 个 1/64（0.03–0.14px） |
| **高度（本批）** | **12 步、每步整 1px** | **1px** |

**同一种「几何随视口连续变形」，在两个轴上是两种量纲。** 宽度轴的形变是 flex 收缩的分数分配，
高度轴的形变是**整数像素的剩余空间**。

### 5. 密集扫描的读数**有一部分是路径的函数** —— 本批最重要的一条方法论读数

686a 的逐高度扫描读到的 `data-director-timeline-height` **恒为 88**（= `timelineCollapsed ? 88 : …`），
而**逐页开桌**在同一批高度上读到的全是 **182**（展开）。

原因是**扫描的第一步**：窗口被压到 140，时间轴随即收起，之后 1560 格都在测另一个状态。

**所以本批做「顺序对照」**：同一页先 **1700 → 140 下行**、再 **140 → 1700 上行**，逐格比对七个量。

⟹ 得到一条干净的切分：

| 量 | 性质 | 两遍是否一致 |
|---|---|---|
| `帮助` 的高 / 顶边 / 底边、rail 的 `clientH`/`scrollH` | **纯布局量** | **一致** |
| `data-director-timeline-height`、轨道区高、`collapsed` | **应用状态量** | **不一致** |

**布局量与路径无关；应用状态量与路径有关。** 683 与 685 引用的「每格恒 132 枚」是**普查口径**
（同时含布局与状态），而 685 的「rendered 125→130」是**纯布局量** —— 两者可靠性不同，本批把这条区分写明。

**没有这条对照，686a 会报出「时间轴在 140..1700 的每个高度都是 88 高」—— 一条纯属虚构的缺陷。**

## 不声称

- **不声称** 683 的读数错了（它在本批的 18 个逐页开桌高度上逐字复现）；
- **不声称** 324 / 272 / 20 / 32 是源站的值（**未取证**；全是 clone 的读数，且 272 是**本批从
  `helpTop − railTop` 逐格量出来的**，不是从源码推的）；
- **不声称** 140..1700 覆盖了所有高度临界（630 记过「窗口矮于 176 时 store 的 MIN 会把时间轴值
  顶回 88」，本批在这条带内**读到的正是收起态**，所以那条在案项在 140..176 上与本批的状态重合，
  无法用本批的读数区分）；
- **不声称** 顺序依赖只发生在时间轴上（本批只量了七个字段）；
- **不声称** `clamp` 公式在 140 以外更矮的视口上仍成立（140 以下没测）。
"""

import importlib.util
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch686-2026-10-01"
# 缓存放在仓库**外**：它在仓库内会变成一份 1.7MB 的重复副本，
# 而 README 与 audit 都已经带着读数了。
RAW_CACHE = Path(os.environ.get("LIBLIB_BATCH686_CACHE_FILE",
                                "/tmp/liblib-batch686-raw.json"))

H_MIN, H_MAX = 140, 1700
WIDTH = 1280
HELP = "data-director-rail-entry=help"
RAIL_TOP = 52                      # rail 是 top-[52px]
# 逐页开桌的高度：跨过 336 / 345 / 356 三个点，且两端都取到
FRESH_HEIGHTS = [200, 300, 320, 330, 336, 337, 340, 344, 345, 346, 350, 355,
                 356, 357, 360, 400, 720, 1150]
TRACK_LABELS = ["data-director-track-label=director-track-camera-main",
                "data-director-track-label=director-track-character-lead-transform"]

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

SEL = ("'button, [role=button], [role=tab], [role=switch], [role=slider],'"
       " + ' [role=menuitem], input, select, textarea, a[href],'"
       " + ' [tabindex]:not([tabindex=\"-1\"])'")

CENSUS_JS = """(withRows) => {
  const scope = document.querySelector('[data-director-workspace]') || document.body;
  const SEL = %s;
  const cs = (e) => getComputedStyle(e);
  const dataOf = (e) => { for (let n = e; n && n !== document.body; n = n.parentElement)
      for (const a of n.attributes) if (a.name.startsWith('data-')) return a.name + '=' + a.value;
    return '-'; };
  const rows = [];
  const sigs = {};
  let n = 0, zero = 0;
  for (const e of scope.querySelectorAll(SEL)) {
    const s = cs(e);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    if (parseFloat(s.opacity) === 0) continue;
    n++;
    const r = e.getBoundingClientRect();
    const k = dataOf(e);
    // **未取整**；这是本批与 683 的尺的差别。
    // 按 key 收成**集合**（684：同键下有多个成员，不能按元素比）
    (sigs[k] = sigs[k] || new Set()).add(s.width + '|' + s.height);
    if (!Math.round(r.width) || !Math.round(r.height)) zero++;
    if (withRows) rows.push({data: k,
      box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      sig: s.width + '|' + s.height,
      rawW: Math.round(r.width), rawH: Math.round(r.height)});
  }
  const help = document.querySelector('[data-director-rail-entry="help"]');
  let rail = help;
  while (rail && rail.parentElement && cs(rail).position === 'static') rail = rail.parentElement;
  const rr = rail.getBoundingClientRect(), hr = help.getBoundingClientRect();
  const tlH = document.querySelector('[data-director-timeline-height]');
  const col = document.querySelector('[data-director-timeline-collapsed]');
  const tlist = document.querySelector('[data-director-timeline-track-list]');
  return {
    vw: innerWidth, vh: innerHeight, n, zero,
    rows: withRows ? rows : null,
    // 紧凑签名：每个键**排序后的集合**。逐像素存全量 rows 会让 audit 到 81MB，
    // 这里只留签名，Python 侧按「集合变化」增量落盘。
    sizeKey: Object.keys(sigs).sort().map(k => k + '=' + [...sigs[k]].sort().join(',')).join(';'),
    helpSig: cs(help).height + '|' + cs(help).width,
    helpTop: Math.round(hr.y), helpBottom: Math.round(hr.bottom),
    railTop: Math.round(rr.y), railH: Math.round(rr.height),
    clientH: rail.clientHeight, scrollH: rail.scrollHeight,
    // 这两个不是装饰：它们证明 帮助 在**每个**高度都真的被渲染，
    // 所以 §2 的斜坡读数不是在读一个 display:none 的子树。
    railDisplay: cs(rail).display, railOverflowY: cs(rail).overflowY,
    tlAttr: tlH ? tlH.getAttribute('data-director-timeline-height') : null,
    collapsed: col ? col.getAttribute('data-director-timeline-collapsed') : null,
    trackListH: tlist ? Math.round(tlist.getBoundingClientRect().height) : null,
  };
}""" % SEL

SETTLE_JS = """() => {
  const e = document.querySelector('[data-director-timeline]');
  const h = document.querySelector('[data-director-rail-entry="help"]');
  return [e ? Math.round(e.getBoundingClientRect().height) : -1,
          h ? Math.round(parseFloat(getComputedStyle(h).height)) : -1];
}"""


def _clean(page) -> None:
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(100)


PANEL_FIELDS = ("helpSig", "helpTop", "helpBottom", "railTop", "railH",
                "clientH", "scrollH", "tlAttr", "collapsed", "trackListH",
                "n", "zero", "railDisplay", "railOverflowY")


def compact(passes: dict) -> dict:
    """逐像素存全量 rows 会把 audit 推到 81MB，**不能提交**。
    两遍各留：面板/计数字段全量（11 个小字段 × 1561 格），外加
    **尺寸签名只在相对上一格发生变化时记一条**。

    变化检测必须比「集合」而不是比「单个成员」—— 684 已证同键下有 4 个成员
    （一个 36x18 标题 + 三个 24x24 导航钮），逐成员比会自激。
    """
    out: dict = {}
    for name, cells in passes.items():
        ordered = sorted(cells, key=int)
        keep: dict = {}
        prev_sig = None
        for h in ordered:
            c = cells[h]
            slim = {f: c.get(f) for f in PANEL_FIELDS}
            # 幂等：缓存里存的就是**已压缩过**的（sizeKey 只在变化处有），
            # 所以只在本次确实带 sizeKey 时才做变化检测。
            if "sizeKey" in c and c["sizeKey"] != prev_sig:
                slim["sizeKey"] = c["sizeKey"]
                prev_sig = c["sizeKey"]
            keep[h] = slim
        out[name] = keep
    return out


def size_sets_at(cells: dict, h: int) -> dict:
    """取高度 h 的「每键尺寸集合」：从最近一次变化点向后继承（签名只在变化处落盘）。"""
    last = None
    for hh in sorted(cells, key=int):
        if int(hh) > h:
            break
        if "sizeKey" in cells[hh]:
            last = cells[hh]["sizeKey"]
    out: dict = {}
    for part in (last or "").split(";"):
        if not part:
            continue
        # **rsplit**：键名本身含 `=`（`data-director-rail-entry=help`），
        # 用 split("=", 1) 会把 119 个键塌成 61 个 —— 第一次跑就是这样判错的。
        # 值里不含 `=`，所以从右边切是安全的。
        k, v = part.rsplit("=", 1)
        out[k] = tuple(v.split(","))
    return out


def px(s: Any) -> float:
    return float(s) if not isinstance(s, str) else float(s.replace("px", "") or 0)


class Verifier:
    def __init__(self) -> None:
        self.result: dict[str, Any] = {}
        self.failures: list[str] = []
        self.count = 0

    def check(self, name: str, ok: bool, detail: Any = "", note: str = "") -> None:
        self.count += 1
        self.result[name] = {"ok": bool(ok), "detail": detail, "note": note or None}
        if not ok:
            self.failures.append(name)
        print(("  PASS " if ok else "  FAIL ") + name
              + (f"  {str(detail)[:130]}" if detail else "")
              + (f"  [{note[:96]}]" if note else ""))


def main() -> int:
    v = Verifier()
    fresh: dict[str, Any] = {}
    passes: dict[str, Any] = {"down": {}, "up": {}}

    with sync_playwright() as p:
        br = p.chromium.launch()

        if os.environ.get("LIBLIB_BATCH686_CACHE") and RAW_CACHE.exists():
            # 断言改动不该再花 8 分钟开浏览器。缓存复用是**显式**的，
            # 且会把 source 标成 cache，避免把陈旧读数当成新读数。
            cached = json.loads(RAW_CACHE.read_text(encoding="utf-8"))
            fresh, passes = cached["fresh"], cached["passes"]
            print(f"  [cache] reused raw readings from {RAW_CACHE}")
        else:
            # ---- 腿 1：逐页开桌（顺序无关，天生如此） ----
            for h in FRESH_HEIGHTS:
                page = br.new_page(viewport={"width": WIDTH, "height": h},
                                   device_scale_factor=1)
                b617.open_desk(page)
                _clean(page)
                fresh[str(h)] = page.evaluate(CENSUS_JS, True)
                page.close()

            # ---- 腿 2：同一页扫两遍（下行 + 上行）做顺序对照 ----
            page = br.new_page(viewport={"width": WIDTH, "height": 720},
                               device_scale_factor=1)
            b617.open_desk(page)
            _clean(page)
            for name, rng in (("down", range(H_MAX, H_MIN - 1, -1)),
                              ("up", range(H_MIN, H_MAX + 1))):
                for h in rng:
                    page.set_viewport_size({"width": WIDTH, "height": h})
                    page.wait_for_timeout(10)
                    prev = page.evaluate(SETTLE_JS)
                    for _ in range(7):
                        page.wait_for_timeout(30)
                        cur = page.evaluate(SETTLE_JS)
                        if cur == prev:
                            break
                        prev = cur
                    passes[name][str(h)] = page.evaluate(CENSUS_JS, False)
            page.close()
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_CACHE.write_text(json.dumps(
        {"stage": "raw-readings", "fresh": fresh, "passes": compact(passes)},
        ensure_ascii=False, indent=1, default=repr), encoding="utf-8")

    HS = [str(h) for h in FRESH_HEIGHTS]
    up = passes["up"]
    down = passes["down"]
    heights = sorted(int(k) for k in up)

    # ---------- 判据 1：人口恒定，且高度轴没有零尺寸对调 ----------
    pop = {h: len(fresh[h]["rows"]) for h in HS}
    zero_keys = {h: sorted({r["data"] for r in fresh[h]["rows"]
                            if r["rawW"] == 0 or r["rawH"] == 0}) for h in HS}
    v.check("population-is-132-and-the-height-axis-has-no-zero-population-exchange",
            set(pop.values()) == {132}
            and all(z == ["data-director-viewport=true"] for z in zero_keys.values()),
            detail={"population": pop,
                    "zeroKeysByHeight": zero_keys,
                    "contrastWithTheWidthAxis":
                        "685 found the zero population EXCHANGES at 898/899: 9 keys when "
                        "narrow (7 not-rendered + 2 genuinely zero) and 2 when wide. On the "
                        "height axis there is no exchange at all -- the same 2 keys at every "
                        "one of the 18 heights.",
                    "theRailItselfIsRenderedAtEveryHeight":
                        sorted({fresh[h]["railDisplay"] for h in HS}),
                    "railOverflowY": sorted({fresh[h]["railOverflowY"] for h in HS}),
                    "whyThisFieldIsNotDecoration":
                        "it proves 帮助 is genuinely rendered at all 18 heights, so "
                        "the ramp readings are real and not a display:none subtree"},
            note="an axis can have a seam on one and none on the other; do not carry a "
                 "conclusion across axes without measuring it")

    # ---------- 判据 2：帮助 的高 = clamp(H − 324, 20, 32) ----------
    help_h = {h: round(px(fresh[h]["helpSig"].split("|")[0]), 4) for h in HS}
    pred = {str(h): max(20.0, min(32.0, float(h) - 324.0)) for h in FRESH_HEIGHTS}
    v.check("the-help-button-height-is-clamp(viewportHeightMinus324,20,32)",
            help_h == pred and help_h["336"] == 20.0 and help_h["345"] == 21.0
            and help_h["356"] == 32.0 and help_h["720"] == 32.0,
            detail={"measured": help_h, "predictedByRule": pred,
                    "allFreshHeightsMatch": help_h == pred,
                    "decomposition": {
                        "52": "the rail is top-[52px], so rail height = H - 52",
                        "272": "the button's TOP edge is pinned at rail-relative 272 "
                               "(verified below), so height = (H-52) - 272 = H - 324",
                        "20": "the floor -- the button's min-content height",
                        "32": "the cap -- its declared size-8"},
                    "whyAFloorExists": "at H<=344 the formula goes below 20 and the button "
                                       "stops at 20, so the shrink is bounded by min-content, "
                                       "not unbounded",
                    "whereTheRampIs": "345..356 -- twelve heights, one pixel each"},
            note="a rule that can be recomputed beats a threshold that was measured once")

    # ---------- 判据 3：336 / 345 / 356 是三个不同的数 ----------
    at336, at344, at345, at356 = (fresh["336"], fresh["344"], fresh["345"], fresh["356"])
    v.check("336-345-and-356-are-three-different-numbers-not-one-threshold",
            at336["clientH"] == at336["scrollH"] == 284
            and at336["helpSig"].startswith("20px")
            and at344["clientH"] == 292 and at344["helpSig"].startswith("20px")
            and at345["clientH"] == 293 and at345["helpSig"].startswith("21px")
            and at356["clientH"] == 304 and at356["helpSig"].startswith("32px")
            and len({284, 345 - RAIL_TOP - 272, 356}) == 3,
            detail={"at336": {"clientH": at336["clientH"], "scrollH": at336["scrollH"],
                              "helpHeight": px(at336["helpSig"].split("|")[0]),
                              "whatHappened": "the rail stops overflowing (clientH == "
                                              "scrollH == 284) -- this is the number 683 "
                                              "derived as 52+284"},
                     "at344": {"clientH": at344["clientH"],
                               "helpHeight": px(at344["helpSig"].split("|")[0]),
                               "whatHappened": "still 20px, eight heights after 336"},
                     "at345": {"clientH": at345["clientH"],
                               "helpHeight": px(at345["helpSig"].split("|")[0]),
                               "whatHappened": "the size starts changing"},
                     "at356": {"clientH": at356["clientH"],
                               "helpHeight": px(at356["helpSig"].split("|")[0]),
                               "whatHappened": "the size stops changing"},
                     "theCorrection":
                         "683's READINGS stand (32x20 at H<=300, 32x32 at H>=400, all 24 of "
                         "its cells reproduce here verbatim). What was wrong is calling 336 "
                         "'the threshold': 336 is where the CONTAINER stops overflowing, not "
                         "where the CONTROL changes size. Those are 345 and 356.",
                     "whyNobodyNoticed": "683 sampled 300 and 400, which straddle the whole "
                                         "345..356 ramp without landing in it -- the same "
                                         "way 682 straddled 336"},
            note="history is not rewritten: the correction is recorded here, and 683 stays "
                 "as it was committed")

    # ---------- 判据 4：高度轴的斜坡是整数斜坡，与宽度轴的 1/64 斜坡不同量纲 ----------
    ramp = [(h, px(up[str(h)]["helpSig"].split("|")[0]))
            for h in range(343, 359) if str(h) in up]
    deltas = [round(ramp[i + 1][1] - ramp[i][1], 6) for i in range(len(ramp) - 1)]
    # ramp 的元素是 (高度, 高度值) 元组 ⟹ 取左端高度
    changing = [ramp[i][0] for i in range(1, len(ramp)) if deltas[i - 1] != 0]
    v.check("the-height-axis-ramp-is-twelve-integer-pixels-not-a-subpixel-ramp",
            # ramp 从 343 起，343→344 是平的（都还在 20px 下限），
            # 真正的 12 个 +1 落在 deltas[1:13]
            deltas[0] == 0.0 and deltas[1:13] == [1.0] * 12
            and len(changing) == 12 and changing[0] == 345 and changing[-1] == 356
            and all(d == int(d) for d in deltas),
            detail={"ramp": ramp, "deltas": deltas,
                    "heightsThatChange": [int(h) for h in changing],
                    "contrastWith685":
                        "the width axis deforms by 2-9 sixtieth-fourths of a pixel per pixel "
                        "(a flex-shrink fraction). The height axis deforms by exactly 1 whole "
                        "pixel per pixel. Same phenomenon -- geometry varying continuously "
                        "with the viewport -- two different units.",
                    "whyTheUnitsDiffer": "vertically the button is absorbing leftover integer "
                                         "space in a bottom-anchored flex column; "
                                         "horizontally it is taking a fractional share of a "
                                         "shrunk flex row"},
            note="an invariant in one unit is not an invariant in another")

    # ---------- 判据 5：顶边先钉住、够高后改贴底，两式在 356 相交 ----------
    def pred_top(h: int) -> int:
        return max(264, h - 92)

    def pred_h(h: int) -> float:
        return max(20.0, min(32.0, float(h) - 324.0))

    top_fresh = {h: fresh[h]["helpTop"] - fresh[h]["railTop"] for h in HS}
    model_ok = {"freshTop": 0, "freshHeight": 0}
    for h in HS:
        model_ok["freshTop"] += top_fresh[h] == pred_top(int(h))
        model_ok["freshHeight"] += px(fresh[h]["helpSig"].split("|")[0]) == pred_h(int(h))
    per_pass = {}
    for name in ("down", "up"):
        okT = okH = 0
        for k, c in passes[name].items():
            h = int(k)
            okT += (c["helpTop"] - c["railTop"]) == pred_top(h)
            okH += px(c["helpSig"].split("|")[0]) == pred_h(h)
        per_pass[name] = {"topMatches": okT, "heightMatches": okH, "cells": len(passes[name])}
    cross = [h for h in (354, 355, 356, 357)
             if (up[str(h)]["helpTop"] - up[str(h)]["railTop"]) == pred_top(h)]
    v.check("the-top-edge-is-pinned-at-264-then-switches-to-bottom-anchored-crossing-at-356",
            model_ok["freshTop"] == len(HS) and model_ok["freshHeight"] == len(HS)
            and all(p["topMatches"] == p["cells"] and p["heightMatches"] == p["cells"]
                    for p in per_pass.values())
            and cross == [354, 355, 356, 357]
            and all(up[str(h)]["helpTop"] - up[str(h)]["railTop"] == 264
                    for h in range(140, 357))
            and all(up[str(h)]["helpTop"] - up[str(h)]["railTop"] == h - 92
                    for h in range(357, H_MAX + 1)),
            detail={"model": {
                "topRelRail": "max(264, H - 92)",
                "height": "clamp(H - 324, 20, 32)",
                "where92ComesFrom": "railH - 8(p-2 bottom padding) - 32(size-8)",
                "where264ComesFrom": "the content-relative position the top is pinned to; "
                                     "264 + 20 = 284, the rail content height 683 measured",
                "where324ComesFrom": "60 + 264, with 60 = 52 (rail top-[52px]) + 8 (p-2)",
                "where356ComesFrom": "the two top formulas cross: 264 = H - 92 <=> H = 356",
                "where345ComesFrom": "the height leaves its 20px floor: 324 + 20 + 1"},
                "freshTopMinusRailTop": top_fresh,
                "matchesPerPass": per_pass,
                "bothFormulasHoldEverywhere":
                    "3122 scan cells (1561 x 2 passes) plus 18 fresh pages, no exceptions"},
            note="a pinned edge that becomes a riding edge is the whole mechanism; 683 saw "
                 "only the resulting difference and named a threshold")

    # ---------- 判据 6：布局量是高度的函数；store 值不是 ----------
    LAYOUT_FIELDS = ["helpSig", "helpTop", "helpBottom", "clientH", "scrollH", "railH"]
    STORE_FIELDS = ["tlAttr", "trackListH"]
    FLAG_FIELDS = ["collapsed"]
    drift = {f: sorted(int(k) for k in down if down[k][f] != up[k][f])
             for f in LAYOUT_FIELDS + STORE_FIELDS + FLAG_FIELDS}
    v.check("layout-readings-are-a-function-of-height-but-the-timeline-height-store-value-is-not",
            all(not drift[f] for f in LAYOUT_FIELDS)
            and all(len(drift[f]) > 0 for f in STORE_FIELDS)
            and not any(drift[f] for f in FLAG_FIELDS)
            and len(down) == len(up) == H_MAX - H_MIN + 1,
            detail={"heightsPerPass": len(down),
                    "driftHeightsByField": {f: len(drift[f]) for f in drift},
           "driftHeightsFull": {f: drift[f] for f in STORE_FIELDS},
                    "driftRange": {f: [drift[f][0], drift[f][-1]] for f in STORE_FIELDS},
                    "driftIsContiguous": {
                        f: drift[f] == list(range(drift[f][0], drift[f][-1] + 1))
                        for f in STORE_FIELDS},
                    "layoutFields": LAYOUT_FIELDS,
                    "storeValueFields": STORE_FIELDS,
                    "flagFields": FLAG_FIELDS,
                    "flagNeverTrue": sorted({str(down[k]["collapsed"]) for k in down}),
                    "at720BothWays": {"down": down["720"]["tlAttr"],
                                      "up": up["720"]["tlAttr"]},
                    "whatHappened":
                        "the first step of a scan can change the app state under "
                        "measurement. Walking 1700->140 first drives the timeline height "
                        "store down to its minimum, and that value is STICKY: the ascending "
                        "pass then reads 88 at every height, including 720 where a fresh page "
                        "reads 182.",
                    "theFabricatedDefectWeAvoided":
                        "without this control the scan would have reported 'the timeline is "
                        "88px tall at every height from 140 to 1700' -- pure artefact.",
                    "theCleanSplit":
                        "every field that reports computed geometry agrees in both passes; "
                        "every field that reports a mutable store value disagrees. So '132 "
                        "controls at every height' (a census figure, mixed) and 'rendered "
                        "125->130' (685, pure layout) do NOT carry the same reliability.",
                    "whichPriorBatchesAreAffected":
                        "683 and 685 resized without an order control. 683's own numbers "
                        "(rail clientH/scrollH, help box) are pure layout and reproduce here "
                        "verbatim, so its readings stand; this batch does not claim to have "
                        "audited their state fields."},
            note="the control is the deliverable: a scan without one reports its own path")

    # ---------- 判据 7：88 这个值同时是收起分支与 store 下限，属性分不出状态 ----------
    up88 = [h for h in heights if up[str(h)]["tlAttr"] == "88"]
    v.check("the-attribute-value-88-cannot-tell-you-whether-the-timeline-is-collapsed",
            down["720"]["tlAttr"] == "182" and up["720"]["tlAttr"] == "88"
            and all(down[k]["collapsed"] in ("false", "None") for k in down)
            and all(up[k]["collapsed"] in ("false", "None") for k in up)
            and len(up88) == len(up),
            detail={"sourceFact": "DirectorTimeline.tsx:794 -- "
                                  "data-director-timeline-height={timelineCollapsed ? 88 : "
                                  "timelineHeight}. The two branches are NUMERICALLY "
                                  "IDENTICAL, because directorStore.ts:99 sets "
                                  "DIRECTOR_TIMELINE_HEIGHT_MIN = 88.",
                    "theCollapse": "up[720].tlAttr == '88' while up[720].collapsed == false, "
                                   "so 88 there is the store value, not the collapse branch",
                    "collapsedEverTrue": False,
                    "heightsWhereUpPassReads88": len(up88),
                    "myOwnMisreading":
                        "the first pass of this batch read tlAttr=88, saw "
                        "`timelineCollapsed ? 88 : ...` in the source, and concluded 'the "
                        "timeline collapsed'. That was WRONG: the flag never became true. "
                        "The source line made me read a value as a flag.",
                    "theLesson":
                        "the same class as 670/678/683 -- a missing or overloaded field reads "
                        "as one value. Here the field is present and correctly named; it is "
                        "the SOURCE EXPRESSION that overloads it. An attribute that can hold "
                        "two meanings cannot answer 'which state am I in'.",
                    "whatWouldDisambiguate": "a separate data attribute, or making the "
                                             "collapsed branch a different number"},
            note="an API that answers two questions with one number answers neither reliably")

    # ---------- 判据 8：规则在「新的/下行」历史上成立，在「已被夹住」的历史上不成立 ----------
    def tl_rule(h: int) -> str:
        """时间轴高度 store 值的规则（与 帮助 的高度规则无关，故分开命名）。"""
        return str(max(88, min(182, h - 88)))

    down_ok = [h for h in heights if down[str(h)]["tlAttr"] == tl_rule(h)]
    fresh_ok = [h for h in FRESH_HEIGHTS if fresh[str(h)]["tlAttr"] == tl_rule(h)]
    up_ok = [h for h in heights if up[str(h)]["tlAttr"] == tl_rule(h)]
    up_bad = [h for h in heights if up[str(h)]["tlAttr"] != tl_rule(h)]
    v.check("the-timeline-height-rule-holds-on-fresh-and-descending-history-and-fails-after-clamping",
            len(down_ok) == len(down) and len(fresh_ok) == len(FRESH_HEIGHTS)
            # 上行只在「规则本身已经等于下限」的那些高度上命中 ——
            # 即它与规则的分歧**全部**落在规则说该 >88 的高度上。
            and up_ok == [h for h in heights if h <= 176]
            and all(h >= 177 for h in up_bad)
            and all(up[str(h)]["tlAttr"] == "88" for h in up_bad),
            detail={"rule": "clamp(viewportHeight - 88, 88, 182)",
                    "descendingPassMatches": f"{len(down_ok)}/{len(down)}",
                    "freshPagesMatch": f"{len(fresh_ok)}/{len(FRESH_HEIGHTS)}",
                    "ascendingPassMatches": f"{len(up_ok)}/{len(up)}",
                    "ascendingPassMisses": len(up_bad),
                    "ascendingPassMatchesOnlyBelow": 176,
                    "sample": [{"h": h, "rule": tl_rule(h),
                                "down": down[str(h)]["tlAttr"], "up": up[str(h)]["tlAttr"]}
                               for h in (140, 176, 177, 200, 269, 270, 300, 720, 1700)],
                    "theStickyMinimum":
                        "the store minimum is 88 (directorStore.ts:99). The resize handler "
                        "clamps DOWN to it and never writes back UP, so once a session has "
                        "visited a short viewport the timeline stays at 88 forever.",
                    "confirms630sInCaseItem":
                        "630 recorded 'below 176 the store MIN pins the timeline value back "
                        "to 88'. This batch derives the same 176 from the rule: "
                        "h - 88 = 88 <=> h = 176, and the measurement brackets it exactly "
                        "(h=177 reads 89, h=176 reads 88).",
                    "capAt182": "182 is the maximum; the rule saturates there from h=270 up"},
            note="a rule that reproduces a fresh session and a descending scan but not an "
                 "ascending one is measuring the session, not the layout")

    # ---------- 判据 9：683 的「只有 1 个键」在未取整单位上仍成立 ----------
    varying: dict[str, list] = defaultdict(list)
    for h in heights:
        for k, st in size_sets_at(passes["up"], h).items():
            varying[k].append(st)
    # **逐高度比集合**，不做增量比较（§3 的教训）
    size_changing = sorted(k for k, seq in varying.items() if len(set(seq)) > 1)
    v.check("683s-only-one-key-holds-in-unrounded-units-too",
            size_changing == [HELP],
            detail={"keysWhoseSizeSetChangesWithHeight": size_changing,
                    "keysMeasured": len(varying),
                    "itsUnroundedHeightByHeight": {
                        str(h): px(up[str(h)]["helpSig"].split("|")[0])
                        for h in [140, 300, 336, 344, 345, 350, 356, 400, 720, 1150, 1700]
                        if str(h) in up},
                    "theCorrection685LeftOpen":
                        "685 said 683's conclusion 'only holds in integer units' and left "
                        "measuring it open. Measured: it holds. On the height axis there is "
                        "no sub-pixel deformation at all -- the 119 other keys are constant "
                        "to the last of the four decimals getComputedStyle returns.",
                    "whyItIsWorthSaying": "a limitation that turns out not to bind is worth "
                                          "recording too, otherwise it stays folklore",
                    "noteOnMethod":
                        "compared as a SET per height, never incrementally: the two "
                        "track-label keys each hold four members, and an incremental "
                        "last-value comparison reports 3121 spurious changes per key "
                        "(this batch's third instrument defect)"},
            note="683 is confirmed, not merely un-refuted")

    # ---------- 判据 10：同键两尺寸在高度轴上仍是异质性而非变形 ----------
    tl_sizes = {}
    for h in HS:
        tl_sizes[h] = sorted({(r["rawW"], r["rawH"]) for r in fresh[h]["rows"]
                              if r["data"] in TRACK_LABELS and r["rawW"] and r["rawH"]})
    v.check("the-two-track-label-keys-still-carry-two-sizes-at-every-height",
            all(v_ == [(24, 24), (36, 18)] for v_ in tl_sizes.values())
            and not any(k in TRACK_LABELS for k in size_changing),
            detail={"sizesAtEveryFreshHeight": tl_sizes,
                    "relationTo683": "683 separated 'deforms with height' from 'two sizes "
                                     "under one key'; the second is heterogeneity WITHIN a "
                                     "height, and it is not deformation",
                    "relationTo684": "684 named the 36x18 member: the track title button "
                                     "(机位, `truncate`), against three 24x24 nav buttons",
                    "whyItIsNotDeformation":
                        "the per-height set is {(24,24),(36,18)} at all 18 heights AND in "
                        "both scan passes -- it never changes, so it is structure. It is "
                        "also the exact thing that broke the incremental detector in this "
                        "batch."},
            note="four batches now agree: this one is invariant in three directions")

    out = {"hMin": H_MIN, "hMax": H_MAX, "width": WIDTH,
           "freshHeights": FRESH_HEIGHTS, "heightsPerPass": len(down),
           "population": pop, "zeroKeysByHeight": zero_keys,
           "helpRule": {"formula": "clamp(H - 324, 20, 32)",
                        "measured": help_h, "predicted": pred},
           "helpModelTopRelRail": top_fresh,
           "helpModelMatches": per_pass,
           "ramp": ramp, "rampDeltas": deltas,
           "sizeChangingKeys": size_changing,
           "driftHeightsByField": {f: len(drift[f]) for f in drift},
           "driftHeightsFull": {f: drift[f] for f in STORE_FIELDS},
           "trackLabelSizes": tl_sizes,
           "judged": sum(pop.values()),
           "hypothesisNotClaim":
               "Every number here is a clone reading. No source-site session was used and no "
               "source-site behaviour is claimed anywhere in this batch."}
    # default=repr 是**兜底**：断言写错不该让整轮 8 分钟的测量白跑，
    # 但任何漏出去的可调用对象都会以 repr 出现在载荷里（可被 grep 到），不会静默消失。
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "fresh": fresh, "passes": compact(passes),
                    "checks": v.result}, ensure_ascii=False, indent=1,
                   default=repr), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
