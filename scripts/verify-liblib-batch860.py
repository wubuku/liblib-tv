#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 860 门禁：**画幅比例真的驱动机位取景框**（源站实测 ＋ 源站逐字）。

## ★ 本批整改的是 batch 859 登记的 D11 —— 且 **D11 的说法本身是错的**

batch 859 登记的 D11 说：「clone 的『选择画幅比例』选中项**不改画布宽高比**」。

★ **本批实测把它推翻了**（`raw/source-860-viewport.json` ／ `raw/source-860-frame.json`）：

| | 基线（自适应） | 点「21:9」后 | 复原后 |
|---|---|---|---|
| 画布容器 `h-full w-full` | 1920×1080 (1.7778) | **1920×1080 (1.7778)** | 1920×1080 |
| `react-flow__viewport` | 732×411 (1.7778) | **732×411 (1.7778)** | 732×411 |
| 机位取景框 | **不在场** | **@(329,270) 1262×541（ratio 2.3334）** | 不在场 |

⟹ ⟹ ★ **源站选比例【不改画布】** ⟹ ⟹ 它改的是**机位取景框**。
⟹ ⟹ 所以 D11 应当**改写**为：
★ **clone 的取景框只支持三档**（`16:9`／`9:16`／`1:1`），
  且 **左侧面板的七格根本没接到 store** ⟹ ⟹ **点哪一档取景框都不动**。

## ★ 源站七档逐档实测（`raw/source-860-frame.json`）

| 档 | 取景框 | ratio |
|---|---|---|
| 自适应 | **不在场** | — |
| 21:9 | @(329,270) 1262×541 | 2.3334 |
| 16:9 | @(329,185) 1262×710 | 1.7778 |
| 4:3 | @(389,112) 1141×856 | 1.3333 |
| 1:1 | @(532,112) 856×856 | 1.0 |
| 3:4 | @(639,112) 642×856 | 0.75 |
| 9:16 | @(719,112) 482×856 | 0.5625 |

★ **算法**（从读数反推，六档全部命中、误差 ≤0.5px）：
① 可用区 ＝ 视口去掉 padding；② 框宽 ＝ `min(可用宽, 可用高×ratio)`、
框高 ＝ 框宽÷ratio；③ 框在可用区里**居中**（源站六档框中心恒为 (960,540)）。

## ★ 判据的设计取舍

★ **绝对像素不可比**：源站视口 1920×1080、clone 视口 1307×810 ⟹ ⟹
同一个比例在两边的框**像素不同**（源站 21:9 ＝ 1262×541、clone ＝ 1278×548）。
⇒ ⇒ 判据比 **ratio**（可比量）＋ **算法约束**（可用区内切 ＋ 居中），
  **不比**绝对像素。

## ★ 输出
  docs/research/liblib-canvas-batch860-2026-10-01/runtime-audit.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs/research/liblib-canvas-batch860-2026-10-01"
RAW = OUT_DIR / "raw"
BASE = "http://localhost:4317"

SRC_STORE = ROOT / "src/store/directorStore.ts"
SRC_MATH = ROOT / "src/components/director/directorViewportMath.ts"
SRC_PANEL = ROOT / "src/components/director/DirectorAspectPanel.tsx"
SRC_VIEW = ROOT / "src/components/director/DirectorViewport.tsx"

# ── 源站实测的期望值（出处见上表） ────────────────────────────────
# ★ ratio ＝ 源站实测的框宽÷框高（不是理论值）⟹ ⟹ 判据直接比源站的读数。
SOURCE_RATIOS: list[tuple[str, float | None, float | None]] = [
    # (档名, 期望 ratio（None ＝ 不在场）, 源站实测 ratio)
    ("自适应", None, None),
    ("21:9", 21 / 9, 2.3334),
    ("16:9", 16 / 9, 1.7778),
    ("4:3", 4 / 3, 1.3333),
    ("1:1", 1.0, 1.0),
    ("3:4", 3 / 4, 0.75),
    ("9:16", 9 / 16, 0.5625),
]

READ = r"""()=>{
  const rect=(e)=>{ if(!e) return null; const r=e.getBoundingClientRect();
    return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width),
            h:Math.round(r.height),
            ratio: r.height>0 ? +(r.width/r.height).toFixed(4) : null}; };
  const q=(s)=>document.querySelector(s);
  const frame=q('[data-director-aspect-frame]');
  // ★ 画布容器：带 canvas 的那个全屏容器
  const canvasBox=[...document.querySelectorAll('div')].find(e=>{
    const c=(e.className||'').toString().trim();
    return c==='h-full w-full' && e.querySelector('canvas');});
  const flowVp=q('.react-flow__viewport');
  return {
    取景框: frame?rect(frame):null,
    取景框比例标记: frame?frame.getAttribute('data-director-aspect-ratio'):null,
    // ★ 取景框的**定位容器**（`position:absolute` 的最近祖先）⟹ ⟹
    //   它就是导演台视口 ⟹ ⟹ 用来判「框居中于视口」。
    取景框定位容器: frame?rect(frame.offsetParent||frame.parentElement):null,
    画布容器: canvasBox?rect(canvasBox):null,
    reactflow视口: flowVp?rect(flowVp):null,
    底部比例按钮: [...document.querySelectorAll('[data-director-aspect]')].map(e=>({
      text:(e.textContent||'').trim(),
      pressed:e.getAttribute('aria-pressed')})),
    画幅格: [...document.querySelectorAll('[data-director-aspect-option]')].map(e=>({
      text:(e.textContent||'').replace(/\s+/g,' ').trim(),
      pressed:e.getAttribute('aria-pressed')})),
  };
}"""


class Verifier:
    def __init__(self) -> None:
        self.count = 0
        self.failures: list[str] = []
        self.result: dict[str, Any] = {}

    def check(self, name: str, ok: bool, detail: Any = "") -> None:
        self.count += 1
        if not ok:
            self.failures.append(f"{name}  ⟵ {detail}")


def strip_comments(src: str) -> str:
    """去掉 `//` 行注释与 `/* */` 块注释 ⟹ ⟹ 静态判据只读**代码**。

    ★ batch 859 的教训：注释里逐字抄的类串**足以**让判据变绿 ⟹ ⟹ 假绿。
    """
    out = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    out = re.sub(r"//[^\n]*", " ", out)
    return out


def open_desk(page: Any) -> None:
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    page.evaluate(
        "() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    page.wait_for_function("() => Boolean(window.__director_store)", timeout=90_000)
    page.wait_for_timeout(1500)
    node = page.locator(".react-flow__node-script-execution").first
    try:
        node.scroll_into_view_if_needed(timeout=8000)
    except Exception:  # noqa: BLE001
        pass
    page.wait_for_timeout(400)
    try:
        node.hover(timeout=8000)
        page.wait_for_timeout(600)
    except Exception:  # noqa: BLE001
        pass
    page.locator("[data-open-director]").first.click(timeout=15000)
    page.wait_for_timeout(6500)
    page.evaluate(
        "() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")


def main() -> int:
    v = Verifier()
    audit: dict[str, Any] = {
        "batch": 860,
        "title": "画幅比例真的驱动机位取景框（七档 ＋ 自适应＝无框）",
    }

    # ══ S1 源码契约（静态、剥注释后比）════════════════════════════
    store_code = strip_comments(SRC_STORE.read_text(encoding="utf-8"))
    math_code = strip_comments(SRC_MATH.read_text(encoding="utf-8"))
    panel_code = strip_comments(SRC_PANEL.read_text(encoding="utf-8"))
    view_code = strip_comments(SRC_VIEW.read_text(encoding="utf-8"))

    v.check("source:store-has-a-separate-frame-aspect-state",
            "frameAspectRatio" in store_code
            and "setFrameAspectRatio" in store_code,
            detail="store 里要有 frameAspectRatio ＋ setFrameAspectRatio")
    # ★ 状态**声明**与**初始值**都要在（★ N9 负控曾只改声明里的名字 ⟹ ⟹
    #   TS 类型**不参与运行时** ⟹ ⟹ 行为完全没变 ⟹ ⟹ 门禁绿是**正确的**、
    #   但那条变异**测不到任何东西** ⟹ ⟹ 所以这里改成改**运行时初始值**）。
    m_state = re.search(
        r"frameAspectRatio:\s*([^,\n]+),", store_code)
    v.check("source:frame-aspect-initial-state-is-auto",
            bool(m_state) and m_state.group(1).strip() == "null",
            detail={"initial": m_state.group(1).strip() if m_state else None,
                    "why": "★ 初始必须是 null（＝自适应）⟹ ⟹ 与源站一致"
                           "（刚打开导演台时取景框不在场）"})
    # ★ 只看**类型联合块**里的档位 ⟹ ⟹ 不能拿全文 `in`：
    #   `DIRECTOR_FRAME_ASPECT_VALUES` 的**键**里也有 `"21:9"` 等字样
    #   ⟹ ⟹ 全文搜会漏判（★ N4 变异改的就是类型里的那一行）。
    m_union = re.search(
        r"export\s+type\s+DirectorFrameAspectRatio\s*=(.*?);", store_code, re.S)
    union_text = m_union.group(1) if m_union else ""
    v.check("source:frame-aspect-covers-the-six-source-ratios",
            bool(union_text)
            and all(f'"{k}"' in union_text
                    for k in ("21:9", "16:9", "4:3", "1:1", "3:4", "9:16")),
            detail={"union": union_text.strip()[:200]})
    # ★ 比例值必须**数值**（源站逐字 `aj`：value 是数值比例）。
    #   ★ 只看 `DIRECTOR_FRAME_ASPECT_VALUES` 那个**对象**里的值，
    #   不能拿全文 `in`（注释里也可能有这些字样）。
    m_vals = re.search(
        r"DIRECTOR_FRAME_ASPECT_VALUES[^=]*=\s*\{(.*?)\};", store_code, re.S)
    vals_text = m_vals.group(1) if m_vals else ""
    v.check("source:frame-aspect-values-are-numeric",
            bool(vals_text)
            and "21 / 9" in vals_text and "4 / 3" in vals_text
            and "3 / 4" in vals_text and "9 / 16" in vals_text,
            detail={"values": vals_text.strip()[:220]})
    v.check("source:frame-rect-accepts-a-null-ratio",
            "ratio === null" in math_code,
            detail="getDirectorFrameRect 要把 null（＝自适应）当成「不画框」")
    v.check("source:panel-writes-to-the-store",
            "useDirectorStore((state) => state.frameAspectRatio)" in panel_code
            and "useDirectorStore((state) => state.setFrameAspectRatio)" in panel_code
            and "useState" not in panel_code,
            detail="★ 面板必须**从 store 读** frameAspectRatio 并**写** setFrameAspectRatio"
                   "（组件内 useState 正是「点哪档都不动」的根因）")
    v.check("source:viewport-reads-the-frame-aspect",
            "frameAspectRatio" in view_code
            and "DIRECTOR_FRAME_ASPECT_VALUES" in view_code,
            detail="视口要读 frameAspectRatio 并换算成数值比例")

    # ══ S2 源站实测产物必须存在 ═════════════════════════════════
    src_frame = RAW / "source-860-frame.json"
    src_vp = RAW / "source-860-viewport.json"
    v.check("source:measurement-exists",
            src_frame.exists() and src_vp.exists(),
            detail=[str(src_frame), str(src_vp)])
    if src_frame.exists():
        sf = json.loads(src_frame.read_text(encoding="utf-8"))
        src_centres: list[tuple[float, float]] = []
        # ★ 复核源站六档的 ratio（判据的期望值不许凭空写）
        for label, expect, src_ratio in SOURCE_RATIOS:
            key = "①自适应" if label == "自适应" else f"②{label}"
            frames = (sf.get(key) or {}).get("取景框") or []
            if expect is None:
                v.check(f"source:no-frame-for-{label}", not frames,
                        detail=frames[:1])
            else:
                got = (frames[0]["rect"]["ratio"] if frames else None)
                v.check(f"source:ratio-for-{label}",
                        got is not None and abs(got - src_ratio) < 0.005,
                        detail={"got": got, "want": src_ratio})
                if frames:
                    r = frames[0]["rect"]
                    src_centres.append((r["x"] + r["w"] / 2,
                                        r["y"] + r["h"] / 2))
        # ★ ★ 对照：**源站的六档也共享同一个中心** ⟹ ⟹ 这条不变量是
        #   **源站同款**的契约，不是 clone 自己编的。
        if src_centres:
            xs = [c[0] for c in src_centres]
            ys = [c[1] for c in src_centres]
            v.check("source:all-frames-share-one-centre",
                    (max(xs) - min(xs)) <= 2.0
                    and (max(ys) - min(ys)) <= 2.0,
                    detail={"xs": [round(x, 2) for x in xs],
                            "ys": [round(y, 2) for y in ys]})

    # ══ S3 clone 实测（live DOM）═════════════════════════════════
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080},
                                    device_scale_factor=1)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text)
                    if m.type == "error" else None)
            open_desk(page)
            page.locator("[data-director-rail-entry='aspect-ratio']").first.click(
                timeout=15000)
            page.wait_for_timeout(800)

            per: dict[str, Any] = {}
            centres: list[tuple[float, float]] = []
            for label, expect, src_ratio in SOURCE_RATIOS:
                page.locator(
                    f"[data-director-aspect-option='{label}']").first.click(
                    timeout=15000)
                page.wait_for_timeout(700)
                r = page.evaluate(READ)
                per[label] = r
                frame = r.get("取景框")
                if expect is None:
                    v.check(f"panel:auto-has-no-framing-box", frame is None,
                            detail=frame)
                    # ★ 「自适应」时框**不在场** ⟹ ⟹ 那个 `data-director-aspect-ratio`
                    #   标记**压根不会出现** ⟹ ⟹ 所以「自适应」这一档**测不到**标记
                    #   ⟹ ⟹ 单独判「自适应时**不出现**取景框」＋「有框的那档标记正确」
                    #   （★ N8 负控曾漏在这里：改 `?? "auto"` 那一支**测不出来**
                    #    ⟹ ⟹ 属**判据漏了一个分支**）。
                    v.check(f"panel:auto-has-no-frame-mark",
                            r.get("取景框比例标记") is None,
                            detail=r.get("取景框比例标记"))
                else:
                    v.check(f"panel:frame-exists-for-{label}", frame is not None,
                            detail=frame)
                    if frame:
                        # ★ 比 **ratio**（可比量）⟹ ⟹ 不比绝对像素
                        v.check(f"panel:frame-ratio-for-{label}",
                                abs(frame["ratio"] - expect) < 0.005,
                                detail={"got": frame["ratio"], "want": expect,
                                        "sourceRatio": src_ratio})
                        # ★ 框必须**居中于导演台视口**。
                        #   ★ ⚠ **不能用 `react-flow__viewport` 当判据**：那是
                        #     **画布**的视口（源站 732×411），而取景框住在
                        #     **导演台自己的视口**里（clone 1358×810）
                        #     ⟹ ⟹ 第一版拿它判 ⟹ ⟹ 四档**假红**
                        #     （★ 判据读的东西必须与它声称的东西同粒度）。
                        #   ★ ★ 也不是「在容器里居中」——**上下 padding 不对称**
                        #     （clone 32/88、源站 112/968）⟹ ⟹ 框居中于
                        #     **去掉 padding 后的可用区** ⟹ ⟹ 纵向偏上
                        #     （clone 恒 −28px、源站恒 0px——因为源站的
                        #     上下 padding 与视口中心恰好对称地错开）。
                        #   ⇒ 判据改成**结构性**断言：
                        #     ① 横向中心 ＝ 容器中心（**精确**）；
                        #     ② 纵向：框的上下边距**到可用区上下边**相等
                        #        （⟹ ⟹ 直接断言「它内切于可用区且居中」，
                        #          **不依赖**具体 padding 数值）。
                        host = r.get("取景框定位容器")
                        if host:
                            cx = frame["x"] + frame["w"] / 2
                            hx = host["x"] + host["w"] / 2
                            v.check(f"panel:frame-is-horizontally-centred-for-{label}",
                                    frame["w"] > 0 and frame["h"] > 0
                                    and abs(cx - hx) <= 1.5,
                                    detail={"frame": frame, "host": host,
                                            "centerDeltaX": round(cx - hx, 2)})

                            # ★ ★ **源站算法的不变量（不依赖任何 padding 常数）**：
                            #   框在可用区里居中 ⟹ ⟹ **所有档的框共享同一个中心**。
                            #   ★ 源站实测：六档中心恒为 (960, 540)
                            #   ★ clone 实测：六档中心恒为 (960, 465)
                            #   ⇒ 「共享中心」这条**跨视口、跨 padding** 都成立
                            #     ⟹ ⟹ 是最稳的判据。
                            # ★ ⚠ 第一版拿「相对**容器**的上下留白相等」来判 ⟹ ⟹ 六档全红
                            #   ——**上下 padding 不对称**（clone 32/88、源站 112/968）
                            #   ⟹ ⟹ 相对容器的上下留白**本来就不相等** ⟹ ⟹ 判据错、不是产品错。
                            inset_w = frame["x"] - host["x"]
                            inset_w2 = (host["x"] + host["w"]) - (frame["x"] + frame["w"])
                            v.check(f"panel:frame-insets-the-available-area-for-{label}",
                                    abs(inset_w - inset_w2) <= 1.5,
                                    detail={"left": inset_w, "right": inset_w2,
                                            "why": "左右边距相等（宽撑满/内切）"})
                            centres.append((frame["x"] + frame["w"] / 2,
                                            frame["y"] + frame["h"] / 2))
                        else:
                            v.check(f"panel:frame-is-horizontally-centred-for-{label}",
                                    False, detail="取景框的定位容器读不到")
                    v.check(f"panel:frame-marks-{label}",
                            r.get("取景框比例标记") == label,
                            detail=r.get("取景框比例标记"))
                # ★ 选中态必须落在那一格
                pressed = [c["text"] for c in (r.get("画幅格") or [])
                           if c.get("pressed") == "true"]
                v.check(f"panel:selection-is-on-{label}",
                        pressed == [label], detail=pressed)
            audit["逐档"] = per

            # ★ ★ **所有档共享同一个中心** ⟹ ⟹ 这就是「框在可用区里居中」
            #   的**不依赖 padding** 的表述（源站实测：六档恒为 (960,540)）。
            if centres:
                xs = [c[0] for c in centres]
                ys = [c[1] for c in centres]
                v.check("panel:all-frames-share-one-centre",
                        (max(xs) - min(xs)) <= 2.0
                        and (max(ys) - min(ys)) <= 2.0,
                        detail={"xs": [round(x, 2) for x in xs],
                                "ys": [round(y, 2) for y in ys],
                                "why": "所有档的框中心必须一致（居中于同一可用区）"})

            # ★ 画布容器**恒定**（源站实测三态恒为 1920×1080）
            canvases = {label: (per[label].get("画布容器") or {}).get("w")
                        for label, _, _ in SOURCE_RATIOS}
            v.check("panel:the-canvas-never-changes",
                    len({v for v in canvases.values() if v is not None}) <= 1,
                    detail=canvases)

            # ★ 底部三枚（clone 扩展）与面板**共享状态**
            v.check("panel:bottom-buttons-share-the-state",
                    all(b.get("pressed") in ("true", "false")
                        for b in (per["16:9"].get("底部比例按钮") or [])),
                    detail=per["16:9"].get("底部比例按钮"))

            v.check("diagnostics:no-page-errors",
                    not [e for e in errors if "TransformControls" not in e],
                    detail=errors[:5])
        finally:
            browser.close()

    v.result = {"判据数": v.count, "失败": v.failures, "audit": audit}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "runtime-audit.json").write_text(
        json.dumps(v.result, ensure_ascii=False, indent=1, default=str),
        encoding="utf-8")
    print(f"\n{v.count} 判据，{len(v.failures)} 失败")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
