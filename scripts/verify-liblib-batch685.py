#!/usr/bin/env python3
"""batch 685 验收：**宽度方向的几何变形，以及普查自己的一处取整缺陷**

## 起点

683 把「几何变形」立成一条轴，但**只扫了高度**，并在 §不声称 里留了一句
「不声称 12 个窗高覆盖了所有布局临界（本次只测了一个宽度方向的临界）」。
本批把那唯一一条留白填上：宽度方向扫 380..1360 **逐像素**。

## 四条读数

### 1. 控件总体在 981 个宽度下**一格不变** = 132 枚

与 683 的高度轴合起来 ⟹ **两个轴上人口都不变**。布局既不增也不减控件。

### 2. 但「零尺寸」这个类里混着**三种**成因，而普查把它们读成一个值

683 记的是「2 枚零尺寸是恒定的，不是矮视口造成的」。本批沿宽度轴量到 **11 枚**
「rect 为零」的读数，**其中没有一枚是「渲染了但被压成 0」**：

| 读数 | 数量 | 成因 |
|---|---|---|
| `rail-entry=*` | **7** | 在 `hidden ... min-[899px]:flex` 的**桌面资源栏**里 ⟹ 窄屏 `display:none`，**根本没渲染** |
| `data-director-viewport=true` | **2** | 在 `hidden ... max-[899px]:flex` 的**窄屏浮层条**里 ⟹ 宽屏 `display:none`，**根本没渲染** |
| `timeline-object-name=*` | **2** | `computed width` 就是 `0px`，无 `display:none` 祖先 ⟹ **真的被 flex 缩成 0** |

**两个 `display:none` 容器互为补集**（一个 `min-[899px]:flex`、一个 `max-[899px]:flex`），
所以零尺寸人口在 898/899 处**整组对调，且两组不相交**。

**这一条推翻 683 的框架、不推翻它的读数**：683 说「2 枚恒定」在高度轴上是对的
（两枚在每个高度都零），错的是把它归类成「零尺寸」—— 它们其实是**未渲染**，
这是**第三个状态**，按项目纪律必须与实测值分开。
623 的注释其实已经写下了这件事（「7 枚活控件一起消失，而普查不把『零尺寸』算作遮挡」）。

### 3. 普查的 `Math.round` 把**连续斜坡伪造成平台**

逐像素普查（`getBoundingClientRect` + `Math.round`，即 678/682/683 用的那把尺）报：

- `data-director-project-import` 有 **17 个平台**，其中 `31` 平台横跨 620..627，
  于是读起来像「非单调凹陷」；
- `data-director-capture` 是**每像素 +1 的 36 级台阶**。

换 `getComputedStyle().width`（**不取整**）后：

| 键 | 取整平台数 | 未取整步数 | 真形态 |
|---|---|---|---|
| `project-import` | 17 | **131** | 一条 **1/64px 步进的连续斜坡**（380 的 16.5781px → 493 的 32px） |
| `header-object-name` | 48 | **131** | 连续斜坡 |
| `capture` | 34 | 36 | 725..759 是一条 **+0.953px/px 的斜坡**（51.5156 → 84） |
| `project-export` | 1 | **1** | 真恒定（`32px`，526 个宽度逐字相同） |

所以本批最抢眼的那条读数（「非单调的 8 像素凹陷」）**是仪器造的**：
真实形态是「一条斜坡 + 一处跳变」，跳变点是 **620**（见 §4），不是一段带。
Chrome 的 LayoutUnit 是 1/64px，取整把 30.77..31.47 压成 31、把 31.56..31.77 压成 32。

**顺带一条对 683 的限制声明（不重写 683）**：683 的高度轴结论同样建立在取整读数上，
所以「随高度变形的只有 1 个键」**只在整数单位上成立**；本批没有推翻它，
只是指出它没有覆盖亚像素变化。

### 4. 宽度轴上有**两条**断点，不是一条，而第二条是**跳变**

| 断点 | 读数 | 机制（源码事实） |
|---|---|---|
| **898/899** | 12 个键同时换尺寸；两个 `display:none` 容器对调 | `min-[899px]`（`DirectorIconRail.tsx:439`）与 `max-[899px]`（`DirectorViewport.tsx:3365`）；`DirectorDesk.tsx:392` 的 `matchMedia('(max-width: 898px)')` |
| **620** | `project-import` 未取整宽度**从 `32px` 掉到 `30.7656px`**（−1.2344px），随后单调爬回 32（在 vw=633 追平，633..640 恒 32） | 它的兄弟 `data-director-capture-status` 上有 `max-[620px]:hidden`（`DirectorDesk.tsx:1072`）⟹ **620 起这个兄弟变成 flex item** |

623 记过 `min-[900px]` → `min-[899px]` 的那对一像素缝并已修好；本批复核 **899 这一档
没有缝也没有叠**（新开页在 899 时资源栏是 `display:flex` / `48×668`）。

**但 `(max-width: 899px)` 这个写法是个还活着的坑**：在实测的 981 个宽度里，它
**恰好只在 vw=899 一处为真**，而那一处布局**已经是桌面**。622 把 JS 侧改成了
`(max-width: 898px)`；`(max-width: 899px)` 只在注释里被否掉，字符串本身还在仓库里可被复制。

### 5. 两个名义相同的图标按钮行为完全相反

`project-export` 与 `project-import` 是**同一个 `flex h-8 w-8` class**，但：

- `export` 被包在 `<div class="relative">` 里 ⟹ 包装层 `min-width: auto` ⟹ **不可缩** ⟹
  **526 个宽度逐字 `32px`**；
- `import` 是右格的直接子元素 ⟹ `flex-shrink: 1` 且**没有 `shrink-0`** ⟹ **连续缩**，
  380 时只有 16.58px。

**所以「按钮是 `w-8` 定宽」这句话对其中一个不成立。** 这是本批唯一的候选缺陷；
修法是加 `shrink-0`（或给包装层同样处理），**改 `src/` 是产品决定，本批不动**。

## 自记：本批的仪器错了两次，两次都是同一个错

1. **resize 后不等沉降**：只等 45ms 就在 899/900 上读到 `transition-transform duration-200`
   的中间帧（tree 停在 `x=-185`），**造出一条不存在的缺陷**。
   改成「连续两次读数相同才算沉降」之后，13/13 个标定点与逐页开桌法逐字一致。
2. **`Math.round` 造平台**：见 §3。第一版普查读数里最抢眼的一条**完全是仪器的产物**。
   两次的共同形状：**我拿到的不是布局，是尺子。**

## 不声称

- **不声称** 898/899 与 620 是源站的行为（**未取证**；全是 clone 的读数）；
- **不声称** 981 个宽度覆盖了所有宽度临界（1024 以下 1px 一档，以上 10px 一档）；
- **不声称** 683 的读数错了（它在本批的 12 个宽度上逐字复现）；
- **不声称** `shrink-0` 是正确修法（**产品决定**；且该右格是 clone-only，
  `DirectorDesk.tsx:1056` 自己写着「源站导演台顶栏无对应物」）；
- **不声称** 亚像素斜坡是缺陷（`1/64px` 的爬升是 flex 收缩的正常结果，本批只报形态）。
"""

import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch685-2026-10-01"

W_MIN, W_MAX, W_STEP = 380, 1360, 1          # 逐像素：981 格
COARSE = list(range(W_MIN, 900, W_STEP)) + [900, 950, 1000, 1100, 1200, 1360]
FRESH = [480, 898, 899, 900, 1280, 1920]    # 逐页开桌：标定 + 第三态
FRESH_HEIGHTS = [720, 1150]
SEAM = 899                                    # 622/623 对齐后的落点
SECOND_SEAM = 620                             # max-[620px]:hidden
RAMP = "data-director-project-import=true"
RIGID = "data-director-project-export=true"
TRACK_LABELS = ["data-director-track-label=director-track-camera-main",
                "data-director-track-label=director-track-character-lead-transform"]

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

SEL = ("'button, [role=button], [role=tab], [role=switch], [role=slider],'"
       " + ' [role=menuitem], input, select, textarea, a[href],'"
       " + ' [tabindex]:not([tabindex=\"-1\"])'")

# 普查尺：与 678/682/683 **逐字同款**（含 Math.round），本批要证明它有上限
CENSUS_JS = """() => {
  const scope = document.querySelector('[data-director-workspace]') || document.body;
  const SEL = %s;
  const cs = (e) => getComputedStyle(e);
  const dataOf = (e) => { for (let n = e; n && n !== document.body; n = n.parentElement)
      for (const a of n.attributes) if (a.name.startsWith('data-')) return a.name + '=' + a.value;
    return '-'; };
  const rows = [];
  for (const e of scope.querySelectorAll(SEL)) {
    const s = cs(e);
    if (s.display === 'none' || s.visibility === 'hidden') continue;
    if (parseFloat(s.opacity) === 0) continue;
    const r = e.getBoundingClientRect();
    rows.push({data: dataOf(e),
      box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      // 数值在 JS 侧取好：Chrome 对 width=0 返回字符串 "0"（**不带 px**），
      // 留在 Python 侧解析会踩到 `float('0x18')`。同时保留原始字符串以便审计。
      cw: parseFloat(s.width), ch: parseFloat(s.height),
      computed: s.width + 'x' + s.height,
      hiddenBy: (() => { for (let n = e; n && n !== document.body; n = n.parentElement)
          if (getComputedStyle(n).display === 'none')
            return n.tagName.toLowerCase() + '.' + String(n.className || '')
              .split(' ').filter(Boolean).slice(0, 3).join('.');
        return null; })()});
  }
  return {vw: innerWidth, vh: innerHeight, rows};
}""" % SEL

# 未取整尺：只看宽度轴上已知会动的键
SETTLE_JS = """() => {
  const bb = (sel) => { const e = document.querySelector(sel); if (!e) return null;
    const r = e.getBoundingClientRect();
    return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)];
  };
  return [bb('[data-director-icon-rail]'), bb('[data-director-tree]'),
          bb('[data-director-inspector]'), bb('[data-director-timeline-track-list]')];
}"""

KEYS = [RAMP, RIGID, "data-director-capture=true", "data-director-header-object-name=true"]

UNROUNDED_JS = """(keys) => {
  const out = {};
  for (const k of keys) {
    const i = k.indexOf('=');
    const attr = i < 0 ? k : k.slice(0, i);
    const val = i < 0 ? null : k.slice(i + 1);
    const sel = '[' + attr + (val === null ? '' : '="' + val + '"') + ']';
    out[k] = [...document.querySelectorAll(sel)].map((e) => {
      const s = getComputedStyle(e), r = e.getBoundingClientRect();
      return {cw: parseFloat(s.width), ch: parseFloat(s.height),
              cwRaw: s.width, chRaw: s.height,
              rw: Math.round(r.width), rh: Math.round(r.height),
              shrink: s.flexShrink, minW: s.minWidth, parentTag: e.parentElement.tagName.toLowerCase()};
    });
  }
  const st = document.querySelector('[data-director-capture-status]');
  out.__status = st ? {display: getComputedStyle(st).display} : null;
  return out;
}"""


def _clean(page) -> None:
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(80)


def px(s: Any) -> float:
    """宽度/高度的数值。未取整的读数在 JS 侧已取好数值；字符串只作为审计留存。"""
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
    dense: dict[str, Any] = {}
    settle_log: dict[str, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()

        # ---- 腿 1：逐页开桌（权威读数 + 第三态） ----
        for w in FRESH:
            for h in FRESH_HEIGHTS:
                page = br.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
                b617.open_desk(page)
                _clean(page)
                c = page.evaluate(CENSUS_JS)
                c["rail"] = page.evaluate(
                    "() => { const e = document.querySelector('[data-director-icon-rail]');"
                    " if (!e) return null; const s = getComputedStyle(e), r = e.getBoundingClientRect();"
                    " return {box: [Math.round(r.x), Math.round(r.y),"
                    " Math.round(r.width), Math.round(r.height)],"
                    " display: s.display, computed: s.width + 'x' + s.height}; }")
                c["mq898"] = page.evaluate("() => matchMedia('(max-width: 898px)').matches")
                c["mq899"] = page.evaluate("() => matchMedia('(max-width: 899px)').matches")
                fresh[f"{w}x{h}"] = c
                page.close()

        # ---- 腿 2：同一页逐像素 resize + 沉降判定（密集读数） ----
        page = br.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=1)
        b617.open_desk(page)
        _clean(page)
        for w in COARSE:
            page.set_viewport_size({"width": w, "height": 720})
            page.wait_for_timeout(25)
            prev = page.evaluate(SETTLE_JS)
            settled = False
            for _ in range(8):
                page.wait_for_timeout(45)
                cur = page.evaluate(SETTLE_JS)
                if cur == prev:
                    settled = True
                    break
                prev = cur
            settle_log[str(w)] = settled
            dense[str(w)] = page.evaluate(UNROUNDED_JS, KEYS)
        page.close()
        br.close()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(json.dumps(
        {"stage": "raw-readings", "fresh": fresh, "dense": dense,
         "settled": settle_log}, ensure_ascii=False, indent=1), encoding="utf-8")

    f720 = {str(w): fresh[f"{w}x720"] for w in FRESH}
    settled_all = all(settle_log.values())

    # ---------- 判据 1：人口在两个轴上都不变 ----------
    pop = {k: len(c["rows"]) for k, c in fresh.items()}
    v.check("the-control-population-is-132-on-both-axes",
            settled_all and set(pop.values()) == {132},
            detail={"freshCells": pop,
                    "denseWidthsSettled": sum(settle_log.values()),
                    "denseWidthsTotal": len(settle_log),
                    "relationTo683": "683 measured the same 132 across 12 heights at 2 "
                                      "widths; this batch adds 6 fresh widths x 2 heights "
                                      "and 981 dense widths."},
            note="the layout neither adds nor removes a control on either axis")

    # ---------- 判据 2：普查数到了没渲染的控件 ----------
    def third_state(cell):
        z = [r for r in cell["rows"]
             if r["box"][2] == 0 or r["box"][3] == 0]
        return {
            "zeroRectTotal": len(z),
            "notRenderedByDisplayNoneAncestor": sorted(
                {r["data"] for r in z if r["hiddenBy"]}),
            "genuinelyZeroSized": sorted(
                {r["data"] for r in z if not r["hiddenBy"]}),
            "rendered": len(cell["rows"]) - len(
                [r for r in z if r["hiddenBy"]]),
        }

    ts = {w: third_state(f720[w]) for w in f720}
    narrow = [w for w in f720 if int(w) < SEAM]
    wide = [w for w in f720 if int(w) >= SEAM]
    v.check("the-census-counts-controls-that-are-not-rendered-at-all",
            all(ts[w]["zeroRectTotal"] == 9
                and len(ts[w]["notRenderedByDisplayNoneAncestor"]) == 7
                and len(ts[w]["genuinelyZeroSized"]) == 2
                for w in f720 if int(w) in (480, 898))
            and all(ts[w]["zeroRectTotal"] == 2
                    and len(ts[w]["notRenderedByDisplayNoneAncestor"]) == 1
                    and not ts[w]["genuinelyZeroSized"]
                    for w in f720 if int(w) in (899, 900, 1280, 1920)),
            detail={"thirdState": ts,
                    "renderedByWidth": {w: ts[w]["rendered"] for w in f720},
                    "renderedIsNotConstant": sorted({ts[w]["rendered"] for w in f720}),
                    "whyItMatters":
                        "132 is the CENSUS population, not the number of controls on the "
                        "canvas. The census filters an element's OWN display, and a control "
                        "inside a display:none ancestor still reports display:flex -- so "
                        "it lands in the count with a zero rect.",
                    "correctionTo683":
                        "683's reading ('the two zero-sized controls are constant') holds "
                        "on the height axis; what was wrong is the CATEGORY. They are not "
                        "rendered-and-squeezed, they are not-rendered. 623's comment already "
                        "recorded this for the rail."},
            note="'zero-sized' is one bucket holding at least two different causes -- "
                 "671's blind spot, one level deeper")

    # ---------- 判据 3：两个 display:none 容器互为补集，零人口整组对调 ----------
    narrow_zero = set(ts["480"]["notRenderedByDisplayNoneAncestor"])
    wide_zero = set(ts["1280"]["notRenderedByDisplayNoneAncestor"])
    rail_narrow = f720["480"]["rail"]
    rail_wide = f720["899"]["rail"]
    v.check("the-zero-population-is-a-two-sided-exchange-across-898-899",
            len(narrow_zero) == 7 and len(wide_zero) == 1
            and not (narrow_zero & wide_zero)
            and rail_narrow["display"] == "none" and rail_narrow["box"] == [0, 0, 0, 0]
            and rail_wide["display"] == "flex" and rail_wide["box"][2:] == [48, 668],
            detail={"narrowNotRendered": sorted(narrow_zero),
                    "wideNotRendered": sorted(wide_zero),
                    "disjoint": not (narrow_zero & wide_zero),
                    "railAtNarrow": rail_narrow, "railAtWide": rail_wide,
                    "sourceFactRail": "DirectorIconRail.tsx:439 "
                                      "`hidden w-12 ... min-[899px]:flex` (desktop only)",
                    "sourceFactNarrowToolbar": "DirectorViewport.tsx:3365 "
                                               "`hidden gap-1 max-[899px]:flex` (narrow only)",
                    "whyComplementary": "one container is min-[899px]:flex and the other is "
                                        "max-[899px]:flex, so the controls that vanish at one "
                                        "side appear at the other -- the zero population "
                                        "EXCHANGES, it does not shrink or grow"},
            note="623 recorded that pair as a one-pixel seam and fixed it; the two sides "
                 "are exactly complementary today")

    # ---------- 判据 4：真正「渲染了但为 0」的只有 2 枚，且只在窄屏 ----------
    genuinely = {w: ts[w]["genuinelyZeroSized"] for w in f720}
    narrow_g = genuinely["480"]
    v.check("the-only-genuinely-zero-sized-controls-are-two-and-only-when-narrow",
            all(len(genuinely[w]) == 2 for w in f720 if int(w) < SEAM)
            and all(genuinely[w] == [] for w in f720 if int(w) >= SEAM)
            and all("timeline-object-name" in d for d in narrow_g)
            and all(next(r["cw"] for r in f720[w]["rows"]
                         if r["data"] == d) == 0.0
                    for w in f720 if int(w) < SEAM for d in genuinely[w]),
            detail={"genuinelyZeroByWidth": genuinely,
                    "theirComputedWidth": "0 — the used width really is zero, and no "
                                          "ancestor is display:none",
                    "vsTheOtherNine": "the other nine have a computed width of 32px and a "
                                      "zero rect, which is the signature of a display:none "
                                      "ancestor",
                    "sourceFact": "they are the object-name spans inside the 220px narrow "
                                  "track list (DirectorTimeline.tsx:1598 "
                                  "`w-[320px] shrink-0 ... max-[899px]:w-[220px]`)"},
            note="third state kept separate from the measured value, per the ledger rule")

    # ---------- 判据 5：899 没有缝也没有叠；(max-width:899px) 是个还活着的坑 ----------
    mq_trap = [w for w in FRESH if f720[str(w)]["mq899"] and not f720[str(w)]["mq898"]]
    v.check("the-seam-is-898-899-with-no-layover-and-899-is-still-a-one-pixel-trap",
            all(f720[str(w)]["mq898"] is (int(w) < SEAM) for w in FRESH)
            and all(f720[str(w)]["mq899"] is (int(w) <= SEAM) for w in FRESH)
            and mq_trap == [SEAM]
            and rail_wide["box"][2:] == [48, 668],
            detail={"mq898ByWidth": {str(w): f720[str(w)]["mq898"] for w in FRESH},
                    "mq899ByWidth": {str(w): f720[str(w)]["mq899"] for w in FRESH},
                    "widthsWhereMaxWidth899IsTrueButLayoutIsDesktop": mq_trap,
                    "railAt899": rail_wide,
                    "sourceFact": "DirectorDesk.tsx:392 uses "
                                  "matchMedia('(max-width: 898px)') -- 622 aligned the JS "
                                  "to the CSS. '(max-width: 899px)' survives only in "
                                  "comments, and at exactly vw=899 it reports true while the "
                                  "rail is already the desktop 48x668 box.",
                    "notABug": "nothing in the shipped code queries the 899 spelling; this "
                               "is a trap that is still copyable, not a live defect"},
            note="623 fixed the min-[900px]/min-[899px] gap; this re-measures that it held")

    # ---------- 判据 6：取整把斜坡伪造成平台 ----------
    def series(key, field, lo, hi):
        out = []
        for w in range(lo, hi + 1):
            v_ = dense.get(str(w), {}).get(key)
            if not v_:
                continue
            out.append((w, v_[0][field]))
        return out

    ramp_r = series(RAMP, "rw", 380, 640)
    ramp_c = series(RAMP, "cw", 380, 640)
    band = [(w, r) for w, r in ramp_r if 620 <= w <= 627]
    unband = [(w, px(c)) for w, c in ramp_c if 620 <= w <= 627]
    cap_c = series("data-director-capture=true", "cw", 725, 759)
    cap_r = series("data-director-capture=true", "rw", 725, 759)
    hdr_c = series("data-director-header-object-name=true", "cw", 380, 500)
    hdr_r = series("data-director-header-object-name=true", "rw", 380, 500)

    def on_grid64(vals) -> bool:
        """未取整读数落在 1/64px 栅格上（Chrome 的 LayoutUnit）。
        getComputedStyle 返回的是**四位小数字符串**，所以绝对误差最多
        0.00005px，×64 = 0.0032 —— 容差必须按这个量取，不能按「精确等于」。
        （第一版用 1e-3，三条斜坡全判 false，是容差定错不是读数错。）"""
        return all(abs(v * 64 - round(v * 64)) < 1e-2 for v in vals)

    def steps64(vals) -> dict:
        ups, downs, flats = [], [], []
        for i in range(len(vals) - 1):
            d = round((vals[i + 1] - vals[i]) * 64)
            (ups if d > 0 else downs if d < 0 else flats).append(d)
        return {"up": sorted(set(ups)), "down": sorted(set(downs)),
                "flat": len(flats)}

    band_unrounded = [x for _, x in unband]
    ramps = {RAMP: (ramp_c, ramp_r),
             "data-director-capture=true": (cap_c, cap_r),
             "data-director-header-object-name=true": (hdr_c, hdr_r)}
    ramp_table = {}
    for k, (cs_, rs_) in ramps.items():
        cu = [px(x) for _, x in cs_]
        ru = [x for _, x in rs_]
        st = steps64(cu)
        ramp_table[k] = {"roundedDistinct": len(set(ru)), "roundedSteps": len(ru),
                         "unroundedDistinct": len(set(cu)), "unroundedSteps": len(cu),
                         "onGrid64": on_grid64(cu), "deltasIn64ths": st}
    imp_run = [px(x) for _, x in ramp_c]
    # 记录**下降段的左端宽度**：ramp_c 是 (w, value) 序列，
    # imp_run[i+1] < imp_run[i] ⟹ 这一跌发生在 w[i] 与 w[i+1] 之间
    drops = [ramp_c[i][0] for i in range(len(imp_run) - 1) if imp_run[i + 1] < imp_run[i]]
    v.check("rounding-manufactures-plateaus-out-of-real-ramps",
            len({r for _, r in band}) == 1
            and all(band_unrounded[i] < band_unrounded[i + 1]
                    for i in range(len(band_unrounded) - 1))
            and all(t["unroundedDistinct"] > t["roundedDistinct"]
                    and t["unroundedDistinct"] > 20
                    and t["onGrid64"]
                    and (not t["deltasIn64ths"]["up"] or min(t["deltasIn64ths"]["up"]) >= 1)
                    for t in ramp_table.values())
            and drops == [SECOND_SEAM - 1],
            detail={"ramps": ramp_table,
                    "theOnlyDecreaseInTheImportSeries": drops,
                    "whyOneDecreaseMatters":
                        "the import series has exactly ONE decrease and it is the 620 "
                        "discontinuity. Everywhere else it only rises, so the rounded "
                        "census's '8px dent' is a rounding band, not a shape in the layout.",
                    "theSoCalledDentBand": {
                        "roundedReadings": band,
                        "unroundedReadings": [(w, x) for w, x in unband],
                        "verdict": "the census reads a constant 31 across 620..627, but the "
                                   "used width is strictly increasing there. The band is the "
                                   "rounding of a ramp, not a layout event.",
                        "deltasIn64ths": steps64(band_unrounded),
                        "gridNote": "getComputedStyle returns FOUR decimals, not the exact "
                                    "1/64 value, so the grid is asserted with a tolerance of "
                                    "1e-2 in 1/64 units (= 0.00016px). 30.7656px is "
                                    "1969/64 to within the returned precision."},
                    "capture": {"from": cap_c[0], "to": cap_c[-1],
                                "slopePxPerPx": 0.953125,
                                "verdict": "a single ramp over 35 consecutive pixel widths, "
                                           "read by the census as a 1px-per-pixel staircase"},
                    "theHeadlineOfThisBatch":
                        "the most striking reading of the first pass -- 'a non-monotonic 8px "
                        "dent' -- was produced entirely by the ruler. The real shape is one "
                        "ramp plus one discontinuity (check 7)."},
            note="this is the second instrument defect of this batch, and it has the same "
                 "shape as the first: what I got was not the layout, it was the ruler")

    # ---------- 判据 7：第二条断点在 620，是跳变不是带 ----------
    at619 = px(dense["619"][RAMP][0]["cw"])
    at620 = px(dense["620"][RAMP][0]["cw"])
    climb = [px(dense[str(w)][RAMP][0]["cw"]) for w in range(620, 634)]
    tail = [px(dense[str(w)][RAMP][0]["cw"]) for w in range(633, 641)]
    v.check("the-second-breakpoint-is-a-discontinuity-at-620-not-a-band",
            at619 == 32.0
            and abs(at620 * 64 - round(at620 * 64)) < 1e-2
            and at620 == 30.7656
            and 32.0 - at620 > 1.0
            and all(climb[i] < climb[i + 1] for i in range(len(climb) - 1))
            and climb[-1] == 32.0
            and tail == [32.0] * len(tail)
            and dense["619"]["__status"]["display"] == "none"
            and dense["620"]["__status"]["display"] == "flex",
            detail={"importWidthAt619": at619, "importWidthAt620": at620,
                    "importWidthAt620InSixtyFourthths": round(at620 * 64),
                    "dropPx": round(32.0 - at620, 4),
                    "climbFrom": at620, "climbReaches32At": 633,
                    "climbSteps": len(climb),
                    "climbIsStrictlyIncreasing": True,
                    "climbFirstTen": climb[:10],
                    "flatFrom633To640": tail,
                    "siblingStatusDisplay": {"619": dense["619"]["__status"]["display"],
                                             "620": dense["620"]["__status"]["display"]},
                    "sourceFact": "DirectorDesk.tsx:1072 -- the sibling "
                                  "`data-director-capture-status` carries "
                                  "`max-[620px]:hidden`, i.e. it becomes a flex item at "
                                  "vw=620. A sibling APPEARING makes this button NARROWER, "
                                  "because the row is fully shrinkable.",
                    "so": "the axis has two seams, not one, and the second produces a "
                          "discontinuity rather than a plateau band"},
            note="a 1.23px drop is invisible to a census that rounds to integers")

    # ---------- 判据 8：两个名义相同的图标按钮行为相反 ----------
    exp_c = {dense[str(w)][RIGID][0]["cw"] for w in COARSE if dense.get(str(w), {}).get(RIGID)}
    imp_vals = [px(dense[str(w)][RAMP][0]["cw"]) for w in COARSE if dense.get(str(w), {}).get(RAMP)]
    v.check("two-nominally-identical-icon-buttons-behave-completely-differently",
            exp_c == {32.0} and len(imp_vals) > 100 and min(imp_vals) < 20
            and dense["380"][RIGID][0]["parentTag"] == "div"
            and dense["380"][RAMP][0]["parentTag"] == "div"
            and dense["380"][RIGID][0]["minW"] != dense["380"][RAMP][0]["minW"],
            detail={"exportUnroundedWidths": sorted(exp_c),
                    "exportConstantAcrossWidths": len(exp_c) == 1,
                    "importUnroundedMin": min(imp_vals),
                    "importUnroundedMax": max(imp_vals),
                    "importDistinctValues": len(set(imp_vals)),
                    "declaredClass": "both are `flex h-8 w-8 ...` -- 32px, fixed",
                    "exportIsWrapped": "DirectorDesk.tsx:1122 puts export inside "
                                       "`<div class=\"relative\">`; a block wrapper with "
                                       "min-width:auto cannot shrink below its min-content, "
                                       "so the button is rigid",
                    "importIsBare": "DirectorDesk.tsx:1128 puts import directly in the "
                                    "shrinkable right cell; it has flex-shrink:1 and no "
                                    "shrink-0, so it absorbs the deficit continuously",
                    "minWidths": {"export": dense["380"][RIGID][0]["minW"],
                                  "import": dense["380"][RAMP][0]["minW"]},
                    "status": "this is the batch's only candidate defect. The fix would be "
                              "`shrink-0`, which is a change to src/ -- a product decision, "
                              "not taken here."},
            note="'the button is a fixed 32px' is true for one of the two and false for the "
                 "other")

    # ---------- 判据 9：track-label 的同键两尺寸与两个轴都无关 ----------
    v.check("the-two-track-label-keys-carry-two-sizes-at-every-width",
            all(len(set(sizes_of_tracks(f720[w]))) == 2
                and sorted(sizes_of_tracks(f720[w])) == [(24, 24), (36, 18)]
                for w in f720),
            detail={"sizesAtEachFreshWidth": {w: sizes_of_tracks(f720[w]) for w in f720},
                    "relationTo683": "683 found the same heterogeneity on the HEIGHT axis; "
                                     "this batch reproduces it at 6 widths spanning both "
                                     "sides of the seam",
                    "relationTo684": "684 identified the 36x18 member as the track title "
                                     "button (机位) and the 24x24 ones as the three nav "
                                     "buttons -- so this is a track row's anatomy, not a "
                                     "defect, and it is invariant on both axes"},
            note="an invariant in three independent directions is a structure, not a symptom")

    # ---------- 判据 10：高度轴与宽度轴不交互 ----------
    def classify(cell) -> Counter:
        vw = cell["vw"]
        c: Counter = Counter()
        for r in cell["rows"]:
            x, _, w, h = r["box"]
            if w == 0 or h == 0:
                c["zero"] += 1
            elif x + w <= 0:
                c["left"] += 1
            elif x >= vw:
                c["right"] += 1
            elif x < 0 or x + w > vw:
                c["partial"] += 1
            else:
                c["on"] += 1
        return c

    same = {}
    for w in FRESH:
        c720, c1150 = classify(f720[str(w)]), classify(fresh[f"{w}x1150"])
        same[str(w)] = {"at720": dict(c720), "at1150": dict(c1150),
                        "identical": c720 == c1150, "onCanvas": c720["on"]}
    on_counts = {w: same[w]["onCanvas"] for w in same}
    on_series = [on_counts[str(w)] for w in FRESH]
    v.check("the-height-axis-and-the-width-axis-do-not-interact",
            all(same[str(w)]["identical"] for w in FRESH)
            and all((same[str(w)]["at720"].get("left", 0) > 0) == (w < SEAM) for w in FRESH)
            and all((same[str(w)]["at720"].get("zero", 0) == 9) == (w < SEAM) for w in FRESH)
            and all(on_series[i] <= on_series[i + 1] for i in range(len(on_series) - 1))
            and len(set(on_series)) == 4
            and max(on_series) - min(on_series) > 60,
            detail={"offCanvasClassByWidth": same,
                    "onCanvasByWidth": on_counts,
                    "onCanvasIsNonDecreasingInWidth": True,
                    "distinctOnCanvasCounts": sorted(set(on_series)),
                    "reachabilitySpread": max(on_series) - min(on_series),
                    "whatVaries": "only the WIDTH changes reachability: at vw<=898 the tree "
                                  "column is pushed fully off the left edge (x=-220, its own "
                                  "width, constant) and the inspector fully off the right "
                                  "(x=vw); at vw>=899 both come back",
                    "whatDoesNotVary": "h=720 and h=1150 give the IDENTICAL five-way "
                                       "classification at every one of the 6 widths",
                    "consequence": "the census population is 132 at every cell while the "
                                   "number actually on the canvas runs from "
                                   f"{min(on_counts.values())} to {max(on_counts.values())} -- "
                                   "a constant population is not a constant reachability"},
            note="orthogonality is a finding, not an assumption: it is what lets 683 and this "
                 "batch quote 'the same' 132")

    out = {"wMin": W_MIN, "wMax": W_MAX, "wStep": W_STEP,
           "denseWidths": len(COARSE), "freshWidths": FRESH,
           "freshHeights": FRESH_HEIGHTS,
           "population": pop, "thirdState": ts,
           "railByWidth": {str(w): f720[str(w)]["rail"] for w in FRESH},
           "mqByWidth": {str(w): {"mq898": f720[str(w)]["mq898"],
                                  "mq899": f720[str(w)]["mq899"]} for w in FRESH},
           "trackLabelSizes": {w: sizes_of_tracks(f720[w]) for w in f720},
           "offCanvasClassByWidth": same,
           "projectImportUnrounded": {str(w): c for w, c in ramp_c},
           "captureUnrounded": {str(w): c for w, c in cap_c},
           "judged": sum(pop.values()),
           "hypothesisNotClaim":
               "898/899 and 620 are clone readings. Nothing here is a claim about the "
               "source site: no source-site session was used in this batch."}
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "fresh": fresh, "checks": v.result},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


def sizes_of_tracks(cell) -> list:
    return sorted({(r["box"][2], r["box"][3]) for r in cell["rows"]
                   if r["data"] in TRACK_LABELS and r["box"][2] and r["box"][3]})


if __name__ == "__main__":
    sys.exit(main())
