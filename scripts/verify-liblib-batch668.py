#!/usr/bin/env python3
"""batch 668 验收：那条 1px 缝到底存不存在

## 起点

667 收尾时把两条阶梯并成一句话：视口 pe:none 层右沿 = `W − 281`，检视器透明列
左沿 = `W − 280`，两者重叠 1px、合起来把 `x > 281` 铺满，而提示条正活在那条
带子里 —— **所以「一旦被视口层的右沿够到，就再也逃不掉」，中间没有缝。**

**那句话里有一个可以被问死的量。** 决定性的问法不是「两条边在纸上差几 px」，
而是：

> 有没有**任何一个宽度**，提示条的某个控件**点得到**（`own=True`）**且不落在
> 检视器那根透明列里**？

缝存在 ⟺ 这个宽度集合非空。**本批开跑前的预测是：空集，缝不存在**
（理由是控件中心随 W 的移动慢于 1px/px，于是「落在视口层内」与「落在检视器
列内」会在同一宽度同时成立）。

**读数把这个预测推翻了：缝存在，而且以 1331 / 1418 / 1510 三个宽度分别开窗，
在 1280–1760 的量程内不再关闭。** 本批的全部内容就是：把「缝存在」这句话
换成它的闭式，并把**真正的绑定约束**从那 1px 差上摘下来。

## 一：四级阶梯（从读数里长出来，不是先验写死）

每格记四个布尔读数：`(点得到, 中心还在自己滚动容器内, 命中列, 命中 section)`。
**不压成带优先级的单一分类** —— 「被裁掉」那一格栈顶根本不是滚动容器本身
（点在它盒外时它不会被命中），而 1318 那一格**同时**既被 section 盖住又落在
裁剪区外，谁先谁后是判据编的、不是读数说的。

对 `上传图片`（`cx = 1037`），W 从大往小（键 = 上面的四元组）：

| W | 键 | 栈顶 |
|---|---|---|
| **≥ 1331** | `(T,T,F,F)` | `svg.lucide-image-plus`（自己）—— **点得到** |
| 1319–1330 | `(F,F,F,F)` | `div.absolute.inset-0`（视口面）：点落在**自己的**滚动容器盒外 |
| **= 1318** | `(F,F,F,T)` | `section…border-l…` —— **只有这一个宽度** |
| ≤ 1317 | `(F,F,T,F)` | `div.min-h-0.flex-1.overflow-y-auto` |

三枚控件的键序**逐位相同**（370 宽度 × 3 控件 = 1110 格）：

| 控件 | `cx` | 命中列到 | 命中 `section` | 出裁剪 | 可点 |
|---|---|---|---|---|---|
| `上传图片` | 1037 | 1317 | **1318** | 1331 | **≥1331** |
| `描述想搭建的场景` | **1124.5** | 1405 | **1406** | 1418 | **≥1418** |
| `发送` | 1216 | 1496 | **1497** | 1510 | **≥1510** |

「命中 section」每枚**恰好 1 个宽度宽** —— 因为 `section` 比 `column` 宽的那 1px
就是它自己的 `border-l`（`DirectorInspector.tsx:2197`，且 `:2194-2196` 的注释
记着这条边框是**源站实测**的），两层在同一个宽度同时越界。

## 二：那 1px 缝没有说错，只是问错了对象

* 视口那层是 `pointer-events:none`，**原理上不可能成为命中栈顶**。
  667 的两条阶梯几何没错，但左半条与点击无关。
* 真正绑住控件的是提示条**自己的** `overflow-x-auto`（右沿 `W − 293`）：
  944 宽的 `mx-auto shrink-0` 行溢出它（`654 scroll_gate` 那个形状，
  **盖住者是受害者自己的祖先**）。**这机制 659/660 已有，本批不当作新发现。**
* 那 1px 只在恰好一个宽度上起作用，之后挡住控件的是**另一个机制**。

## 三：`getBoundingClientRect()` 的边 ≠ 命中测试用的边（本批最要紧的一条）

阶梯第一版差在 `描述想搭建的场景` 的 1405/1406 两格。0.02px 步长扫点实测
（1280 / 1330 / 1405 三个宽度）：

| 元素 | rect 左沿 | 命中区左沿 | 差 |
|---|---|---|---|
| 检视器 `section` | `W − 281` | `W − 281.98` | **≈1.0**（该点**不含**） |
| 检视器 `column` | `W − 280` | `W − 280.98` | **≈1.0**（该点**不含**） |
| 提示条 `overflow-x-auto` | 右沿 `W − 293` | 同 | **0**（半开区间） |

`0.98` 是 0.02px 分辨率下的**下界**（该点不含，真值在 `(0.98, 1.00]`）。
**右沿不服从同一条规律**：列的命中区在 rect 右沿前 **0.52px** 就结束，再往右
`elementFromPoint` 返回 `null` —— **不解释**，记为残差。

**后果**：任何「rect 边 ⟹ 可点性」的闭式，对**中心落在半像素上的控件**差一格；
`描述想搭建的场景`（`cx = 1124.5`）正是那一枚。**659/660 不受影响**
（它们用的是滚动容器右沿，那一侧差 0）；**受影响的正是 667 那两条 rect 边** ——
667 没写错，它只是记了 rect，而 rect 回答不了点击的问题。

## 四：同盒 6 枚元素 —— 第 10 个盲区形状

1330 那一格上，视口格 `[281, 88, W−562, 880]` 上同时躺着 **6 枚盒完全相同的
元素**：3 枚 `pe:auto`（`main…` / `section…bg-[#20252b]` /
**`div.absolute.inset-0` ← 吃掉点击的就是它**）+ 2 枚无 class 的 `pe:none` `div`
（其一即 666 命名的视口层）+ 1 枚 `pe:none` `canvas`。

所以 664 的 `pe:none` 普查**结构上看不见**吃点击的那一枚，666 的仪器
（在 `pe:none` 里取面积最大者）**恰好点出了不能吃点击的那一枚**；
而 666 的 `CH3` 闭式仍然成立 —— 它判的是「被 pe:none 层罩住」，
与「谁吃掉点击」本来就是两个问题。

**不声称**：命中区整体偏左 ≈1px 的机制；列右沿那 0.52px 残差；
`cx` 为何在 W=1530 之后以 0.5px/px 移动；以及源站是否有同样的行为。
"""

import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "docs/research/liblib-canvas-batch668-2026-10-01"

spec = importlib.util.spec_from_file_location(
    "b617", ROOT / "scripts/verify-liblib-batch617.py")
b617 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b617)

W_FROM, W_TO, W_STEP, HEIGHT = 1280, 1760, 2, 1150
TARGETS = ["上传图片", "描述想搭建的场景", "发送"]

JS = r"""(targets) => {
  const scope = document.querySelector('[data-director-workspace]') || document.body;
  const cx_ = (e) => (e.getAttribute('class') || '').trim().split(/\s+/).join('.')
                 || '<' + e.tagName.toLowerCase() + '>';
  // 一律记到 1/100 px，不四舍五入到整像素：检视器的两条边落在**半像素**上，
  // 而 描述想搭建的场景 的 cx 也是半像素 —— 任何整像素化都会造出假不一致
  const raw = (v) => Math.round(v * 100) / 100;
  const bx = (e) => { const r = e.getBoundingClientRect();
    // [x, y, w, h, right] —— 右沿单独留着，几何断言全靠它
    return [raw(r.x), raw(r.y), raw(r.width), raw(r.height), raw(r.right)]; };
  // 检视器那根透明滚动列：结构定位，不写死宽高
  let col = null, area = -1;
  for (const e of scope.querySelectorAll('div')) {
    const c = e.getAttribute('class') || '';
    if (!(c.includes('min-h-0') && c.includes('flex-1') && c.includes('overflow-y-auto'))) continue;
    const r = e.getBoundingClientRect(); const a = r.width * r.height;
    if (a > area) { area = a; col = e; }
  }
  const sec = col ? col.parentElement : null;
  const rows = [];
  let chain = null, scroller = null, kids = null;
  for (const el of scope.querySelectorAll('button,input')) {
    const name = el.getAttribute('aria-label') || el.getAttribute('placeholder') || '';
    if (targets.indexOf(name) < 0) continue;
    const r = el.getBoundingClientRect();
    const px = r.x + r.width / 2, py = r.y + r.height / 2;
    const hit = document.elementFromPoint(px, py);
    if (!chain) {
      const els = []; for (let n = el; n && n !== document.body; n = n.parentElement) els.push(n);
      chain = els.map((n) => ({ident: cx_(n), box: bx(n),
                              pe: getComputedStyle(n).pointerEvents}));
      scroller = null;
      for (const n of els) { const c = n.getAttribute('class') || '';
        if (c.includes('overflow-x-auto') && c.includes('pointer-events-auto')) { scroller = n; break; } }
      if (scroller) kids = Array.from(scroller.children).map((k) => ({ident: cx_(k), box: bx(k)}));
    }
    rows.push({
      control: name,
      cx: raw(px), cy: raw(py),
      hitIdent: hit ? cx_(hit) : null,
      // 分类只认对象身份，不拿读数去比一个先验写死的式子
      hitIsSelf: !!(hit && (hit === el || el.contains(hit))),
      hitIsColumn: hit === col, hitIsSection: hit === sec, hitIsScroller: hit === scroller,
      // clip 闸门：中心点是否还在自己的滚动容器盒内（654 的形状）
      inScrollerClip: scroller ? (px >= scroller.getBoundingClientRect().left
                             && px < scroller.getBoundingClientRect().right) : null,
      inColumn: col ? (px >= col.getBoundingClientRect().left
                    && px <= col.getBoundingClientRect().right) : null,
    });
  }
  return {
    W: innerWidth,
    colLeft: col ? raw(col.getBoundingClientRect().left) : null,
    secLeft: sec ? raw(sec.getBoundingClientRect().left) : null,
    colIdent: col ? cx_(col) : null, secIdent: sec ? cx_(sec) : null,
    scrollerBox: scroller ? bx(scroller) : null,
    chain: chain, scrollerKids: kids,
    rows: rows,
  };
}"""

TWIN_JS = r"""() => {
  // 锚在**真正吃掉点击的那一枚**上，而不是 main —— 问的是「谁和它同盒」
  const scope = document.querySelector('[data-director-workspace]') || document.body;
  const ident = (e) => (e.getAttribute('class') || '').trim().split(/\s+/).join('.')
                   || '<' + e.tagName.toLowerCase() + '>';
  const key = (e) => { const r = e.getBoundingClientRect();
    return [r.x, r.y, r.width, r.height].map((v) => Math.round(v)).join(','); };
  let el = null;
  for (const c of scope.querySelectorAll('button,input')) {
    if (c.getAttribute('aria-label') === '上传图片') { el = c; break; }
  }
  if (!el) return {W: innerWidth, blockerBox: null, twins: []};
  const r = el.getBoundingClientRect();
  const hit = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
  if (!hit) return {W: innerWidth, blockerBox: null, twins: []};
  const want = key(hit);
  const twins = [];
  for (const e of scope.querySelectorAll('*')) {
    if (key(e) !== want) continue;
    const s = getComputedStyle(e);
    twins.push({ident: ident(e), pe: s.pointerEvents, z: s.zIndex, pos: s.position});
  }
  return {W: innerWidth, blockerBox: want, blockerIdent: ident(hit), twins: twins};
}"""


EDGE_JS = r"""() => {
  // rect 的边 与 elementFromPoint 用的边，到底差多少 —— 0.02px 步长扫出来
  const scope = document.querySelector('[data-director-workspace]') || document.body;
  let el = null;
  for (const c of scope.querySelectorAll('button,input')) {
    if (c.getAttribute('aria-label') === '上传图片'
        || c.getAttribute('placeholder') === '描述想搭建的场景') { el = c; break; }
  }
  if (!el) return {W: innerWidth, found: false};
  let col = null, area = -1;
  for (const e of scope.querySelectorAll('div')) {
    const c = e.getAttribute('class') || '';
    if (!(c.includes('min-h-0') && c.includes('flex-1') && c.includes('overflow-y-auto'))) continue;
    const b = e.getBoundingClientRect(); const a = b.width * b.height;
    if (a > area) { area = a; col = e; }
  }
  const sec = col.parentElement;
  const r = el.getBoundingClientRect();
  const cy = r.y + r.height / 2;
  const cb = col.getBoundingClientRect(), sb = sec.getBoundingClientRect();
  const firstX = (from, to, want) => {
    for (let x = from; x <= to + 1e-9; x += 0.02) {
      const h = document.elementFromPoint(x, cy);
      const t = h === col ? 'COL' : h === sec ? 'SEC' : (h && (h === el || el.contains(h))) ? 'SELF' : '..';
      if (t === want) return Math.round(x * 1000) / 1000;
    }
    return null;
  };
  const lastX = (from, to, want) => {
    let last = null;
    for (let x = from; x <= to + 1e-9; x += 0.02) {
      const h = document.elementFromPoint(x, cy);
      const t = h === col ? 'COL' : h === sec ? 'SEC' : (h && (h === el || el.contains(h))) ? 'SELF' : '..';
      if (t === want) last = Math.round(x * 1000) / 1000;
    }
    return last;
  };
  return {
    W: innerWidth, found: true, step: 0.02,
    colRectLeft: cb.left, colRectRight: cb.right, secRectLeft: sb.left,
    colHitLeft: firstX(cb.left - 2, cb.left + 1, 'COL'),
    secHitLeft: firstX(sb.left - 2, sb.left + 1, 'SEC'),
    colHitLeftStrictlyInside: (() => { const a = firstX(cb.left - 2, cb.left + 1, 'COL');
                                       return a === null ? null : a + 0.02; })(),
    colHitRight: lastX(cb.right - 2, cb.right + 1, 'COL'),
    colRightNeighbour: (() => { const h = document.elementFromPoint(cb.right - 0.3, cy);
      return h ? (h.getAttribute('class')||'').trim().split(/\s+/).slice(0,2).join('.')
                  || '<'+h.tagName.toLowerCase()+'>' : 'null'; })(),
  };
}"""


def _clean(page) -> None:
    page.evaluate("() => { for (const el of document.querySelectorAll("
                  "'nextjs-portal')) el.remove(); }")
    page.mouse.move(5, 5)
    page.wait_for_timeout(60)


def snap(page, w: int) -> dict[str, Any]:
    page.set_viewport_size({"width": w, "height": HEIGHT})
    page.wait_for_timeout(80)
    _clean(page)
    return page.evaluate(JS, TARGETS)


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
              + (f"  {str(detail)[:150]}" if detail else "")
              + (f"  [{note[:96]}]" if note else ""))


def key4(r: dict[str, Any]) -> tuple:
    """一格的四个布尔读数：(点得到, 还在自己滚动容器内, 命中列, 命中 section)

    不用「优先级」把它们压成单一分类 —— 1318 那一格**同时**既被 section 盖住、
    又落在自己滚动容器的裁剪区外，谁先谁后是判据编的，不是读数说的。
    """
    return (bool(r["hitIsSelf"]), bool(r["inScrollerClip"]),
            bool(r["hitIsColumn"]), bool(r["hitIsSection"]))


def main() -> int:
    v = Verifier()
    cells: dict[int, Any] = {}
    twins: dict[int, Any] = {}
    edges: dict[int, Any] = {}

    with sync_playwright() as p:
        br = p.chromium.launch()
        page = br.new_page(viewport={"width": W_FROM, "height": HEIGHT},
                           device_scale_factor=1)
        b617.open_desk(page)
        for w in range(W_FROM, W_TO + 1, W_STEP):
            cells[w] = snap(page, w)
        # 边界处 1px 精修：凡是盖住者身份变过的粗扫档，各取 ±1
        rough = sorted(cells)
        edge_widths: set[int] = set()
        for a, b in zip(rough, rough[1:]):
            for ra, rb in zip(cells[a]["rows"], cells[b]["rows"]):
                if (ra["hitIsSelf"], ra["hitIsColumn"], ra["hitIsSection"],
                        ra["cx"]) != (rb["hitIsSelf"], rb["hitIsColumn"],
                                      rb["hitIsSection"], rb["cx"]):
                    edge_widths.add(b)
        for w in sorted(edge_widths):
            for x in (w - 1, w, w + 1):
                if W_FROM <= x <= W_TO and x not in cells:
                    cells[x] = snap(page, x)
        for w in (1330, 1600):
            page.set_viewport_size({"width": w, "height": HEIGHT})
            page.wait_for_timeout(80)
            _clean(page)
            twins[w] = page.evaluate(TWIN_JS)
        for w in (1280, 1330, 1405):
            page.set_viewport_size({"width": w, "height": HEIGHT})
            page.wait_for_timeout(80)
            _clean(page)
            edges[w] = page.evaluate(EDGE_JS)
        page.close()
        br.close()

    widths = sorted(cells)
    per = {t: {w: [r for r in cells[w]["rows"] if r["control"] == t][0] for w in widths}
           for t in TARGETS}

    # 原始读数先落盘：下面的分析若崩掉，证据仍然在案（这一条是被 668 自己
    # 的第一次运行教会的 —— 崩在写 audit 之前，等于什么都没留下）
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"stage": "raw-readings", "widths": widths,
                    "cells": {str(w): cells[w] for w in widths}, "twins": twins},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    def chain_of(t: str) -> list[dict[str, Any]]:
        """W 从大到小，四元组键的每一段 —— 阶梯是读出来的，不是我写死的"""
        runs: list[dict[str, Any]] = []
        for w in sorted(widths, reverse=True):
            k = key4(per[t][w])
            if runs and tuple(runs[-1]["key"]) == k:
                runs[-1]["upTo"] = w
                runs[-1]["widths"] += 1
            else:
                runs.append({"key": list(k), "from": w, "upTo": w, "widths": 1})
        return runs

    # ---- 从读数里导出阶梯的四个常数（三枚控件都必须给出同一个答案） -------
    # ---- 三堵墙的常数全部从**几何读数**导出，一格一格比，不用钉死的数字 ----
    col_off = sorted({w - cells[w]["colLeft"] for w in widths})
    sec_off = sorted({w - cells[w]["secLeft"] for w in widths})
    scr_off = sorted({w - cells[w]["scrollerBox"][4] for w in widths})
    scr_left = sorted({cells[w]["scrollerBox"][0] for w in widths})
    K_COL = col_off[0] if len(col_off) == 1 else None
    K_SEC = sec_off[0] if len(sec_off) == 1 else None
    K_SCR = scr_off[0] if len(scr_off) == 1 else None

    # ---- 命中测试用的边与 rect 报的边差多少：由 0.02px 扫描导出，不预设 ----
    infl_col = sorted({round(edges[w]["colRectLeft"] - edges[w]["colHitLeft"], 3)
                       for w in edges if edges[w].get("colHitLeft")})
    infl_sec = sorted({round(edges[w]["secRectLeft"] - edges[w]["secHitLeft"], 3)
                       for w in edges if edges[w].get("secHitLeft")})
    infl_col_r = sorted({round(edges[w]["colRectRight"] - edges[w]["colHitRight"], 3)
                         for w in edges if edges[w].get("colHitRight")})
    # 命中区左沿：rect 左沿再往左 infl（且该点本身**不含**在内）
    HIT_COL = (K_COL + infl_col[0]) if K_COL is not None and len(infl_col) == 1 else None
    HIT_SEC = (K_SEC + infl_sec[0]) if K_SEC is not None and len(infl_sec) == 1 else None

    ladder: dict[str, Any] = {}
    for t in TARGETS:
        seq = [(w, per[t][w]) for w in widths]
        free = [w for w, r in seq if r["hitIsSelf"]]
        first_free = min(free) if free else None
        col_ends = max((w for w, r in seq if r["hitIsColumn"]), default=None)
        sec_is = sorted(w for w, r in seq if r["hitIsSection"])
        # 「被自己的滚动容器裁掉」不是身份判据（点在它盒外时它根本不会被命中），
        # 而是闸门判据 inScrollerClip=False —— 那一格栈顶是视口面，记下来但不命名机制
        clipped = sorted(w for w, r in seq if not r["inScrollerClip"])
        cx_ref = per[t][first_free]["cx"] if first_free else seq[-1][1]["cx"]
        ladder[t] = {
            "cx": cx_ref,
            "firstFree": first_free,
            "columnBlockedUpTo": col_ends,
            "sectionAt": sec_is,
            "sectionBandWidth": len(sec_is),
            "clippedBand": [clipped[0], clipped[-1]] if clipped else None,
            "whatIsHitWhenClipped": sorted({r["hitIdent"] for w, r in seq
                                            if not r["inScrollerClip"]}),
            # 命中区是 (左沿, 右沿] 这一侧排他、那一侧含端点 —— 所以是 ceil(x)-1 不是 floor(x)
            "predColumnEnds": (math.ceil(cx_ref + HIT_COL) - 1) if HIT_COL else None,
            "predSectionEnds": (math.floor(cx_ref + HIT_COL) + 1) if HIT_COL else None,
            "predClipEnds": math.floor(cx_ref + K_SCR) if K_SCR else None,
            "predFirstFree": (math.floor(cx_ref + K_SCR) + 1) if K_SCR else None,
            "hitEdgeColumn": cx_ref - (K_COL + infl_col[0]) if infl_col else None,
            "hitEdgeSection": cx_ref - (K_SEC + infl_sec[0]) if infl_sec else None,
            "keyChain": chain_of(t),
        }

    # 四条逐格恒等式；每一条都在**每个控件 × 每个宽度**上与读数比对
    id_free, id_clip, id_col, id_sec = [], [], [], []
    n_judged = 0
    for t in TARGETS:
        for w in widths:
            r = per[t][w]
            cx = r["cx"]
            n_judged += 1
            # 「点得到」⟺「中心点还在自己滚动容器的盒内」—— 两条独立读数互相证
            if r["hitIsSelf"] != r["inScrollerClip"]:
                id_clip.append(f"{t}@{w}")
            # 滚动容器的右沿：与 rect 逐位相同，区间是**半开**的
            if r["hitIsSelf"] != (cx < w - K_SCR):
                id_free.append(f"{t}@{w}")
            # 检视器两枚：命中区左沿比 rect 左沿靠左 infl，且边界排他
            if r["hitIsColumn"] != (cx > w - HIT_COL):
                id_col.append(f"{t}@{w}")
            if r["hitIsSection"] != (cx > w - HIT_SEC and cx <= w - HIT_COL):
                id_sec.append(f"{t}@{w}")
    out = {"widths": [widths[0], widths[-1], len(widths)], "ladder": ladder,
           "wallConstants": {"columnRectLeft": K_COL, "sectionRectLeft": K_SEC,
                             "scrollerRight": K_SCR, "scrollerLeft": scr_left,
                             "columnHitLeft": HIT_COL, "sectionHitLeft": HIT_SEC,
                             "seenOnce": {"col": col_off, "sec": sec_off, "scr": scr_off}},
           "rectVsHitScan": edges,
           "inflation": {"columnLeft": infl_col, "sectionLeft": infl_sec,
                         "columnRight": infl_col_r},
           "judgements": n_judged,
           "identityMismatches": {"own==inClip": id_clip, "own==cx>wall": id_free,
                                  "hitColumn==cx>hitEdge": id_col,
                                  "hitSection==inBand": id_sec}}

    v.check("the-seam-exists-the-decisive-boolean-is-true-at-some-width",
            all(ladder[t]["firstFree"] is not None for t in TARGETS)
            and all(ladder[t]["firstFree"] - 1 in
                    range(ladder[t]["clippedBand"][0], ladder[t]["clippedBand"][1] + 1)
                    for t in TARGETS),
            detail={t: [ladder[t]["cx"], ladder[t]["firstFree"]] for t in TARGETS},
            note="prediction before the run was the EMPTY set; the reading refutes it")

    v.check("each-wall-is-a-single-constant-on-every-swept-width",
            K_COL is not None and K_SEC is not None and K_SCR is not None
            and len(scr_left) == 1 and K_SEC > K_COL and K_SCR > K_SEC,
            detail=out["wallConstants"],
            note="constants are the modal W-minus-edge of the measured boxes; the "
                 "rect edges are integers; the two inspector edges need a "
                 "measured 1.0px correction before they can predict clicks")

    v.check("the-ladder-is-four-rungs-and-the-section-rung-is-one-pixel-wide",
            all(len(ladder[t]["keyChain"]) == 4 for t in TARGETS)
            and all(ladder[t]["sectionBandWidth"] == 1 for t in TARGETS)
            and all([tuple(run["key"]) for run in ladder[t]["keyChain"]]
                    == [tuple(run["key"]) for run in ladder[TARGETS[0]]["keyChain"]]
                    for t in TARGETS),
            detail={t: {"rungs": ladder[t]["keyChain"],
                        "columnBlockedUpTo": ladder[t]["columnBlockedUpTo"],
                        "clippedBand": ladder[t]["clippedBand"],
                        "firstFree": ladder[t]["firstFree"]}
                    for t in TARGETS},
            note="four rungs, identical key order for all three controls; "
                 "the section rung is exactly one width wide")

    v.check("four-identities-hold-on-every-control-times-every-width",
            not (id_free or id_clip or id_col or id_sec) and n_judged > 0,
            detail={"judgements": n_judged, "mismatches":
                    {k: vv[:4] for k, vv in out["identityMismatches"].items() if vv}},
            note="own == inClip; own == (cx > W-293); hitColumn == (cx > hitEdge); "
                 "hitSection == (hitSecEdge < cx <= hitColEdge)")

    v.check("rect-left-and-the-edge-elementfrompoint-uses-differ-by-about-one-pixel",
            len(infl_col) == 1 and len(infl_sec) == 1 and len(infl_col_r) == 1
            and 0.9 < infl_col[0] < 1.02 and infl_sec[0] == infl_col[0],
            detail={"inflationLeft": infl_col, "inflationSectionLeft": infl_sec,
                    "inflationRight": infl_col_r,
                    "note": "0.98 是 0.02px 扫描分辨率下的**下界**：该点本身不含，"
                            "真值在 (0.98, 1.00]",
                    "rightEdgeNeighbour": {w: edges[w]["colRightNeighbour"]
                                           for w in sorted(edges)},
                    "scanStep": 0.02, "widthsScanned": sorted(edges),
                    "hitColumnEdge": {w: [edges[w]["colRectLeft"], edges[w]["colHitLeft"]]
                                      for w in sorted(edges)},
                    "hitSectionEdge": {w: [edges[w]["secRectLeft"], edges[w]["secHitLeft"]]
                                       for w in sorted(edges)}},
            note="left edges need a measured ~1.0px correction; the RIGHT edge does "
                 "NOT follow the same rule (0.52) and is recorded unexplained — "
                 "mechanism NOT pinned for either")

    v.check("the-boundary-widths-are-floor-of-cx-plus-the-wall-constant",
            all(ladder[t]["predFirstFree"] == ladder[t]["firstFree"]
                and ladder[t]["predClipEnds"] == (ladder[t]["firstFree"] - 1)
                and ladder[t]["predColumnEnds"] == ladder[t]["columnBlockedUpTo"]
                and ladder[t]["predSectionEnds"] == ladder[t]["sectionAt"][0]
                for t in TARGETS),
            detail={t: {"cx": ladder[t]["cx"],
                        "pred": [ladder[t]["predColumnEnds"], ladder[t]["predSectionEnds"],
                                 ladder[t]["predClipEnds"], ladder[t]["predFirstFree"]],
                        "read": [ladder[t]["columnBlockedUpTo"], ladder[t]["sectionAt"][0],
                                 ladder[t]["firstFree"] - 1, ladder[t]["firstFree"]]}
                    for t in TARGETS},
            note="ceil(x)-1 for the inspector walls (their hit edge is left-exclusive), "
                 "floor(x) for the scroll container (half-open); 描述想搭建的场景's cx "
                 "is a half pixel (1124.5), which is what exposed the difference")

    row_w = {w: (cells[w]["scrollerKids"][0]["box"][2] if cells[w]["scrollerKids"] else None)
             for w in widths}
    sc_w = {w: cells[w]["scrollerBox"][2] for w in widths}
    overflows = {w: (row_w[w] - sc_w[w]) for w in widths if row_w[w] and sc_w[w]}
    fit = min((w for w in widths if overflows.get(w, 1) <= 0), default=None)
    pill = {w: (next((m["box"] for m in (cells[w]["chain"] or [])
                      if "z-10" in m["ident"]), None)) for w in widths}
    pill_ok = sorted(w for w in widths
                     if pill[w] and pill[w][4] <= cells[w]["scrollerBox"][4])
    v.check("the-row-stops-overflowing-at-exactly-one-width",
            fit is not None and all(overflows[w] > 0 for w in widths if w < fit)
            and all(overflows[w] <= 0 for w in widths if w >= fit)
            and pill_ok[:1] == [fit],
            detail={"rowWidth@1280": row_w[widths[0]], "rowWidthIsConstant":
                    len(set(v for v in row_w.values() if v)) == 1,
                    "scrollerWidth@1280": sc_w[widths[0]],
                    "overflow@1280": overflows[widths[0]],
                    "overflow@1530": overflows.get(1530), "overflow@1600": overflows.get(1600),
                    "firstWidthThatFits": fit, "pillFullyVisibleFrom": pill_ok[:1]},
            note="the earlier 'always overflows' guess is refuted at 1600; the clip "
                 "is self-inflicted only while the row is wider than its scroller")

    tw = twins.get(1330, {})
    t1330 = tw.get("twins", [])
    pes = [t["pe"] for t in t1330]
    v.check("same-box-twins-the-blocker-is-pe-auto-a-pe-none-sibling-shares-its-box",
            len(t1330) >= 2 and "none" in pes and "auto" in pes
            and any(t["pe"] == "auto" and t["ident"] == tw.get("blockerIdent")
                    for t in t1330)
            and any(t["pe"] == "none" for t in t1330),
            detail={"blockerBox": tw.get("blockerBox"), "blockerIdent": tw.get("blockerIdent"),
                    "sameBoxCount": len(t1330), "twins": t1330},
            note="a pe:none-only census (664) is structurally blind to the pe:auto "
                 "one; 666 named the pe:none sibling because it only looked at pe:none")

    v.check("the-escape-window-never-closes-within-the-swept-range",
            all(per[t][w]["hitIsSelf"] for t in TARGETS for w in widths
                if w > per[t][w]["cx"] + K_SCR),
            detail={"lastSweptWidth": widths[-1],
                    "cx@1280": per[TARGETS[0]][1280]["cx"],
                    "cx@last": per[TARGETS[0]][widths[-1]]["cx"],
                    "K_scrollerRight": K_SCR},
            note="walls move 1px/px; cx moves at most 0.5px/px (measured, cause not pinned)")

    cx_series = [(w, per[TARGETS[0]][w]["cx"]) for w in widths]
    first_move = next((w for i, (w, c) in enumerate(cx_series)
                       if i and c != cx_series[i - 1][1]), None)
    rate = None
    if first_move is not None:
        i0 = next(i for i, (w, _) in enumerate(cx_series) if w == first_move)
        if i0 > 0 and cx_series[-1][0] > cx_series[i0 - 1][0]:
            rate = round((cx_series[-1][1] - cx_series[i0 - 1][1])
                         / (cx_series[-1][0] - cx_series[i0 - 1][0]), 3)
    v.check("cx-starts-moving-at-exactly-the-width-the-row-stops-overflowing",
            first_move is not None and fit is not None and first_move == fit + 1
            and rate is not None and 0 < rate <= 0.5,
            detail={"cxConstantUpTo": (first_move - 1) if first_move else None,
                    "firstWidthCxMoves": first_move, "rateAfterBreak": rate,
                    "firstWidthRowFits": fit},
            note="coincidence to the pixel; mx-auto is the suspect but NOT claimed as cause")

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    (AUDIT_DIR / "runtime-audit.json").write_text(
        json.dumps({"verifier": out, "cells": {str(w): cells[w] for w in widths},
                    "twins": twins, "checks": v.result},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n{v.count - len(v.failures)}/{v.count} checks passed")
    for f in v.failures:
        print("  FAILED:", f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
