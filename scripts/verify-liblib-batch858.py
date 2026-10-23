#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 858 门禁：「添加角色」**左侧面板模式**（源站逐字 ＋ 源站实测）。

## ★ 本批整改的是 batch 857 登记的 D1

clone 此前把「添加角色」做成 rail 上的 **portal 浮层** ⟹ ⟹ 它与场景树
**完全重叠**（浮层 x=48..280 ＝ 场景树 x=48..280）⟹ ⟹ 浮层里的选项
**截走**落在组行上的点击 ⟹ ⟹ 场景树**看着能点、其实点不动**。

源站逐字（源站 chunk）：
    `e?null:(0,i.jsxs)("div",{className:"flex w-[232px] min-w-0 flex-col
       bg-[#171717]",children:["scene"===z?n:null,"character"===z?(…)]})`
⟹ ⟹ 左侧面板是**模式互斥**的 ⟹ ⟹ 切到 character 时**场景树不渲染**。

## ★ 期望值的出处（**不是** clone 自己算的）

| 期望 | 出处 |
| --- | --- |
| 面板 @(48,52) 宽 232、标题条 h-12/12px | 源站 chunk 逐字（`aO`）＋ batch 858 源站实测 |
| 11 行、行 h-8/13px、逐行 y=100…420 | 同上 ＋ 源站实测 |
| crowd 按钮 **(56,388) 216×32** | **源站实测**（raw/source-858-panel.json） |
| 几何就地展开 **(68,452) 204×256**、项 199×32 | **源站实测**（raw/source-858-panel.json） |
| 对话框 **(280,388) 220×204**、z 1800、bg rgba(31,31,31,0.98) | **源站实测** |
| 对话框内部：标题行 20 / 网格 106 / 页脚 28、label 行高 17.05px | **源站实测** |
| 量程 rows/cols 1..10 step1、spacing .1..10 step.1 | 源站 chunk 逐字 |

## ★ 输出
  docs/research/liblib-canvas-batch858-2026-10-01/runtime-audit.json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs/research/liblib-canvas-batch858-2026-10-01"
BASE = "http://localhost:4317"

# ── 源站实测的期望值（出处见上表） ────────────────────────────────
SOURCE = {
    "panel": {"x": 48, "y": 52, "w": 232},
    "title": {"h": 48, "font": "12px"},
    "row": {"h": 32, "font": "13px", "x": 56, "w": 216},
    "row_ys": [100, 132, 164, 196, 228, 260, 292, 324, 356, 388, 420],
    "crowd_btn": {"x": 56, "y": 388, "w": 216, "h": 32},
    "geometry": {"x": 68, "y": 452, "w": 204, "h": 256},
    "geometry_item": {"w": 199, "h": 32},
    "dialog": {"x": 280, "y": 388, "w": 220, "h": 204},
    "dialog_z": "1800",
    "dialog_bg": "rgba(31, 31, 31, 0.98)",
    # ⚠ 用 **list** 而不是 tuple：探针读回来的是 JSON ⟹ ⟹ 列表 ⟹ ⟹
    #   写成 tuple 会因为「类型不同」而假红（实测值本身是对的）。
    "dialog_kids": [[401, 20], [433, 106], [551, 28]],
    "label_line_height": "17.05px",
    "range_rows": ("1", "10", "1"),
    "range_cols": ("1", "10", "1"),
    "range_spacing": ("0.1", "10", "0.1"),
}

# 源站逐字的 11 行顺序（源站 chunk 的 ei.map + 本地上传 + crowd + geometry）
EXPECTED_ROWS = [
    ("local-upload", "本地上传"),
    ("standard-male", "标准男性"),
    ("standard-female", "标准女性"),
    ("muscular", "健硕"),
    ("slim", "纤细"),
    ("teen", "少年"),
    ("child", "儿童"),
    ("broad", "宽厚"),
    ("chibi", "二头身"),
    ("crowd-3x3", "群众 (3x3)"),
    ("geometry", "几何模型"),
]

# ★ 本批引入的 Tailwind 类名 ⟹ ⟹ 必须**真的**在构建产物 CSS 里
#   （4317 的 Tailwind 扫描是冻结的 ⟹ ⟹ 新类名可能**静默无样式**）。
NEW_CLASSES = [
    "text-white/88", "text-white/90", "bg-white/8", "border-white/8",
    "leading-[1.55]", "z-[1800]", "bg-white/[0.06]", "text-white/45",
    "text-white/55", "shadow-[0_8px_24px_rgba(0,0,0,0.35)]",
    "backdrop-blur-xl", "size-3.5", "min-w-0", "col-span-2",
]

READ = r"""()=>{
  const rect=(e)=>{ if(!e) return null; const r=e.getBoundingClientRect();
    return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width),
            h:Math.round(r.height), right:Math.round(r.right),
            bottom:Math.round(r.bottom)}; };
  const q=(s)=>document.querySelector(s);
  const panel=q('[data-director-character-panel]');
  const title=q('[data-director-panel-title="add-character"]');
  const dlg=q('[data-director-crowd-dialog]');
  const geo=q('[data-director-geometry-submenu]');
  const crowdBtn=q("[data-director-character-option='crowd-3x3']");
  const rows=[...document.querySelectorAll('[data-director-character-option]')].map(el=>{
    const labelSpan=[...el.querySelectorAll('span')].find(s=>s.getAttribute('aria-hidden')!=='true');
    const r=el.getBoundingClientRect();
    return {id:el.getAttribute('data-director-character-option'),
            label:(labelSpan?.innerText||'').trim(),
            x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height),
            font:getComputedStyle(el).fontSize,
            ariaExpanded:el.getAttribute('aria-expanded'),
            ariaHasPopup:el.getAttribute('aria-haspopup'),
            chevron:Boolean(el.querySelector('span[aria-hidden="true"]'))};
  });
  const geoItems=[...document.querySelectorAll('[data-director-geometry-option]')].map(el=>{
    const r=el.getBoundingClientRect();
    return {id:el.getAttribute('data-director-geometry-option'),
            x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)};
  });
  const dlgKids = dlg ? [...dlg.children].map(c=>{
    const r=c.getBoundingClientRect();
    return [Math.round(r.y), Math.round(r.height)];
  }) : null;
  const dlgLabels = dlg ? [...dlg.querySelectorAll('label')].map(l=>{
    const sp=l.querySelector('span');
    const ss=sp?getComputedStyle(sp):null;
    return {lineHeight: ss?ss.lineHeight:null,
            inputH: l.querySelector('input')?getComputedStyle(l.querySelector('input')).height:null};
  }) : null;
  const inp=(k)=>{ const e=q("[data-director-crowd-input='"+k+"']"); if(!e) return null;
    return {value:e.value, min:e.getAttribute('min'), max:e.getAttribute('max'),
            step:e.getAttribute('step'), aria:e.getAttribute('aria-label')}; };
  const railBtn=(id)=>{ const e=q("[data-director-rail-entry='"+id+"']"); if(!e) return null;
    return {pressed:e.getAttribute('aria-pressed')}; };
  return {
    面板: rect(panel),
    面板存在: panel!==null,
    标题条: rect(title),
    标题字号: title?getComputedStyle(title).fontSize:null,
    标题文本: title?title.innerText.trim():null,
    标题有截断span: title?Boolean(title.querySelector('span.truncate')):null,
    左侧面板模式: (q('[data-director-left-panel-view]')||{}).getAttribute
        ? q('[data-director-left-panel-view]').getAttribute('data-director-left-panel-view') : null,
    场景树存在: Boolean(q('[data-director-tree]')),
    场景树按钮数: document.querySelectorAll('[data-director-tree] button').length,
    行: rows,
    几何展开: rect(geo),
    几何展开在面板内: geo?geo.closest('[data-director-character-panel]')!==null:null,
    几何展开父是body: geo?geo.parentElement===document.body:null,
    几何项: geoItems,
    crowd按钮: rect(crowdBtn),
    crowd按钮背景: crowdBtn?getComputedStyle(crowdBtn).backgroundColor:null,
    对话框: rect(dlg),
    对话框z: dlg?getComputedStyle(dlg).zIndex:null,
    对话框背景: dlg?getComputedStyle(dlg).backgroundColor:null,
    对话框段: dlgKids,
    对话框label: dlgLabels,
    计数文案: (q('[data-director-crowd-count]')||{}).textContent||'',
    行数: inp('rows'), 列数: inp('columns'), 间距: inp('spacing'),
    rail场景: railBtn('scene'), rail添加角色: railBtn('add-character'),
    rail添加机位: railBtn('add-camera'),
    rail全景图: railBtn('panorama'), rail画幅比例: railBtn('aspect-ratio'),
  };
}"""


class Verifier:
    def __init__(self) -> None:
        self.result: dict[str, Any] = {}
        self.failures: list[str] = []
        self.count = 0

    def check(self, name: str, ok: bool, detail: Any = "") -> None:
        self.count += 1
        self.result[name] = {"ok": bool(ok), "detail": detail}
        if not ok:
            self.failures.append(name)
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}"
              + (f"  ⟵ {detail}" if detail else ""))


def open_desk(page: Any) -> None:
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    page.wait_for_function("() => Boolean(window.__director_store)", timeout=90_000)
    page.wait_for_timeout(1500)
    node = page.locator(".react-flow__node-script-execution").first
    try:
        node.scroll_into_view_if_needed(timeout=8000)
        node.hover(timeout=8000)
    except Exception:  # noqa: BLE001
        pass
    page.wait_for_timeout(400)
    page.locator("[data-open-director]").first.click(timeout=15_000)
    page.wait_for_timeout(6500)
    page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")


def css_class_check(v: Verifier) -> None:
    """★ 本批引入的类名必须**真的**在构建产物 CSS 里（冻结扫描会静默丢样式）。"""
    import importlib.util
    import io
    import contextlib
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8",
                                     delete=False) as fh:
        fh.write("\n".join(NEW_CLASSES))
        list_file = fh.name
    spec = importlib.util.spec_from_file_location(
        "clscheck", ROOT / "scripts/check-tailwind-classes-in-css.py")
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = mod.main(["check-tailwind-classes-in-css.py", "--list-from", list_file])
    missing = [ln for ln in buf.getvalue().splitlines() if ln.startswith("MISS")]
    v.check("new-tailwind-classes-exist-in-the-built-css",
            code == 0 and not missing, detail=missing or "all present")


def main() -> int:
    v = Verifier()
    audit: dict[str, Any] = {
        "batch": 858,
        "title": "「添加角色」面板化（源站左侧面板模式 ＋ crowd 对话框逐字）",
        "sourceExpectations": SOURCE,
        "checks": {},
    }

    # ── 静态契约：源站逐字的类名必须真的写在源码里 ────────────────
    panel_src = (ROOT / "src/components/director/DirectorCharacterPanel.tsx").read_text(
        encoding="utf-8")
    desk_src = (ROOT / "src/components/director/DirectorDesk.tsx").read_text(
        encoding="utf-8")
    rail_src = (ROOT / "src/components/director/DirectorIconRail.tsx").read_text(
        encoding="utf-8")
    v.check("source:panel-is-232-wide-with-source-title-class",
            "w-[232px] min-w-0 flex-col" in desk_src or "min-w-0 flex-col" in panel_src,
            "面板容器类名")
    v.check("source:title-bar-is-the-source-aO-class",
            "flex h-12 shrink-0 items-center px-3 text-[12px] leading-5 text-white/90"
            in panel_src)
    v.check("source:row-class-is-the-source-eu-class",
            "flex h-8 w-full items-center gap-2 rounded-lg px-2 text-left "
            "text-[13px] leading-5 text-white/88 transition-colors hover:bg-white/8"
            in panel_src)
    v.check("source:geometry-expands-in-place",
            "border-white/8 ml-3 border-l pl-1" in panel_src)
    v.check("source:dialog-uses-the-source-z-1800",
            "z-[1800]" in panel_src and "w-[220px]" in panel_src)
    v.check("source:rail-no-longer-owns-a-character-flyout",
            "characterFlyout" not in rail_src
            and "crowdDialogOpen" not in rail_src)
    v.check("source:desk-switches-left-panel-by-mode",
            'leftPanelView === "character"' in desk_src
            and 'data-director-left-panel-view' in desk_src)

    css_class_check(v)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900},
                                    device_scale_factor=1)
            open_desk(page)

            base = page.evaluate(READ)
            v.check("initial:left-panel-is-scene-and-tree-is-there",
                    base.get("左侧面板模式") == "scene" and base.get("场景树存在") is True
                    and base.get("面板存在") is False,
                    f"mode={base.get('左侧面板模式')} tree={base.get('场景树存在')}")
            v.check("initial:scene-rail-entry-is-pressed",
                    (base.get("rail场景") or {}).get("pressed") == "true")

            # 点「添加角色」
            page.locator("[data-director-rail-entry='add-character']").click(timeout=15_000)
            page.wait_for_timeout(600)
            st = page.evaluate(READ)
            audit["afterAddCharacter"] = st

            v.check("panel:opens", st.get("面板存在") is True, st.get("面板"))
            v.check("panel:width-232-at-x-48",
                    (st.get("面板") or {}).get("w") == SOURCE["panel"]["w"]
                    and (st.get("面板") or {}).get("x") == SOURCE["panel"]["x"],
                    st.get("面板"))
            v.check("panel:title-bar-h-48-12px-and-text",
                    (st.get("标题条") or {}).get("h") == SOURCE["title"]["h"]
                    and st.get("标题字号") == SOURCE["title"]["font"]
                    and st.get("标题文本") == "添加角色"
                    and st.get("标题有截断span") is True,
                    f"{st.get('标题条')} font={st.get('标题字号')} text={st.get('标题文本')}")
            v.check("panel:scene-tree-is-gone-mutually-exclusive",
                    st.get("场景树存在") is False and st.get("场景树按钮数") == 0,
                    f"tree={st.get('场景树存在')} buttons={st.get('场景树按钮数')}")
            v.check("panel:rail-add-character-is-pressed",
                    (st.get("rail添加角色") or {}).get("pressed") == "true"
                    and (st.get("rail场景") or {}).get("pressed") == "false")

            rows = st.get("行") or []
            v.check("panel:eleven-rows-in-source-order",
                    [(r["id"], r["label"]) for r in rows] == EXPECTED_ROWS,
                    [r["label"] for r in rows])
            v.check("panel:row-geometry-32px-13px-at-x-56-w-216",
                    all(r["h"] == SOURCE["row"]["h"] and r["font"] == SOURCE["row"]["font"]
                        and r["x"] == SOURCE["row"]["x"] and r["w"] == SOURCE["row"]["w"]
                        for r in rows),
                    [(r["label"], r["x"], r["y"], r["w"], r["h"], r["font"]) for r in rows][:3])
            v.check("panel:row-ys-match-the-source-measurement",
                    [r["y"] for r in rows] == SOURCE["row_ys"],
                    [r["y"] for r in rows])
            v.check("panel:crowd-row-has-aria-haspopup-dialog",
                    (next((r for r in rows if r["id"] == "crowd-3x3"), {}) or {})
                    .get("ariaHasPopup") == "dialog")
            v.check("panel:submenu-rows-have-chevrons",
                    [r["chevron"] for r in rows]
                    == [False] * 9 + [True, True],
                    [(r["label"], r["chevron"]) for r in rows])

            cb = st.get("crowd按钮") or {}
            v.check("crowd:button-is-at-the-source-measured-rect",
                    all(cb.get(k) == val for k, val in SOURCE["crowd_btn"].items()), cb)

            # ── 几何就地展开 ────────────────────────────────────────
            page.locator("[data-director-character-option='geometry']").click(timeout=15_000)
            page.wait_for_timeout(600)
            geo = page.evaluate(READ)
            audit["afterGeometry"] = geo
            gb = geo.get("几何展开") or {}
            v.check("geometry:expands-in-place-at-the-source-measured-rect",
                    all(gb.get(k) == val for k, val in SOURCE["geometry"].items()), gb)
            v.check("geometry:is-inside-the-panel-not-a-portal",
                    geo.get("几何展开在面板内") is True
                    and geo.get("几何展开父是body") is False)
            gi = geo.get("几何项") or []
            v.check("geometry:eight-items-199x32",
                    len(gi) == 8
                    and all(i["w"] == SOURCE["geometry_item"]["w"]
                            and i["h"] == SOURCE["geometry_item"]["h"] for i in gi),
                    [(i["id"], i["w"], i["h"]) for i in gi])

            # ── 开 crowd 对话框 ─────────────────────────────────────
            page.locator("[data-director-character-option='crowd-3x3']").click(timeout=15_000)
            page.wait_for_timeout(700)
            dlg = page.evaluate(READ)
            audit["afterCrowd"] = dlg
            db = dlg.get("对话框") or {}
            v.check("crowd:dialog-is-at-the-source-measured-rect",
                    all(db.get(k) == val for k, val in SOURCE["dialog"].items()), db)
            v.check("crowd:dialog-z-1800-and-bg-source",
                    dlg.get("对话框z") == SOURCE["dialog_z"]
                    and dlg.get("对话框背景") == SOURCE["dialog_bg"],
                    f"z={dlg.get('对话框z')} bg={dlg.get('对话框背景')}")
            v.check("crowd:dialog-internal-segments-match-the-source",
                    dlg.get("对话框段") == SOURCE["dialog_kids"], dlg.get("对话框段"))
            v.check("crowd:dialog-label-line-height-matches-the-source",
                    all(l["lineHeight"] == SOURCE["label_line_height"]
                        for l in (dlg.get("对话框label") or []))
                    and all(l["inputH"] == "28px" for l in (dlg.get("对话框label") or [])),
                    dlg.get("对话框label"))
            v.check("crowd:geometry-closed-because-source-shares-one-state",
                    dlg.get("几何展开") is None)
            v.check("crowd:count-reads-9-by-default",
                    (dlg.get("计数文案") or "").strip() == "共9人", dlg.get("计数文案"))
            v.check("crowd:input-ranges-match-the-source",
                    (dlg.get("行数") or {}).get("min") == SOURCE["range_rows"][0]
                    and (dlg.get("行数") or {}).get("max") == SOURCE["range_rows"][1]
                    and (dlg.get("行数") or {}).get("step") == SOURCE["range_rows"][2]
                    and (dlg.get("列数") or {}).get("min") == SOURCE["range_cols"][0]
                    and (dlg.get("列数") or {}).get("max") == SOURCE["range_cols"][1]
                    and (dlg.get("列数") or {}).get("step") == SOURCE["range_cols"][2]
                    and (dlg.get("间距") or {}).get("min") == SOURCE["range_spacing"][0]
                    and (dlg.get("间距") or {}).get("max") == SOURCE["range_spacing"][1]
                    and (dlg.get("间距") or {}).get("step") == SOURCE["range_spacing"][2],
                    [dlg.get("行数"), dlg.get("列数"), dlg.get("间距")])

            # ★ 间距行为：填 1.55 ⟹ 读回 1.6（源站实测行为）
            page.locator("[data-director-crowd-input='spacing']").fill("1.55")
            page.wait_for_timeout(400)
            sp = page.evaluate(READ)["间距"]
            v.check("crowd:spacing-keeps-one-decimal-1.55-becomes-1.6",
                    sp.get("value") == "1.6", sp)

            # ★ 再点一次 ⟹ 关闭（源站 `if("crowd"===L)return void O(null)`）
            page.locator("[data-director-character-option='crowd-3x3']").click(timeout=15_000)
            page.wait_for_timeout(500)
            v.check("crowd:clicking-the-row-again-closes-the-dialog",
                    page.evaluate(READ)["对话框"] is None)

            # ★ 点外面 ⟹ 关闭（源站 outside-mousedown）
            page.locator("[data-director-character-option='crowd-3x3']").click(timeout=15_000)
            page.wait_for_timeout(500)
            page.locator("[data-director-character-option='standard-male']").click(timeout=15_000)
            page.wait_for_timeout(500)
            v.check("crowd:clicking-outside-closes-the-dialog",
                    page.evaluate(READ)["对话框"] is None)

            # ── 切回「场景」 ────────────────────────────────────────
            page.locator("[data-director-rail-entry='scene']").click(timeout=15_000)
            page.wait_for_timeout(700)
            back = page.evaluate(READ)
            v.check("scene:panel-closes-and-the-tree-comes-back",
                    back.get("面板存在") is False and back.get("场景树存在") is True
                    and back.get("左侧面板模式") == "scene",
                    f"panel={back.get('面板存在')} tree={back.get('场景树存在')}")
            v.check("scene:rail-scene-entry-is-pressed-again",
                    (back.get("rail场景") or {}).get("pressed") == "true"
                    and (back.get("rail添加角色") or {}).get("pressed") == "false")

            # ★ 点「全景图」⟹ ⟹ 左侧面板必须让位（源站 z 互斥）
            page.locator("[data-director-rail-entry='add-character']").click(timeout=15_000)
            page.wait_for_timeout(500)
            page.locator("[data-director-rail-entry='panorama']").click(timeout=15_000)
            page.wait_for_timeout(600)
            sw = page.evaluate(READ)
            v.check("rail:another-entry-makes-the-character-panel-yield",
                    sw.get("面板存在") is False
                    and (sw.get("rail全景图") or {}).get("pressed") == "true",
                    f"panel={sw.get('面板存在')} pano={sw.get('rail全景图')}")
            page.close()

            # ── 移动端（clone 自己的扩展：源站没有移动端布局） ──────
            mpage = browser.new_page(viewport={"width": 390, "height": 844},
                                     device_scale_factor=1)
            open_desk(mpage)
            mpage.locator("[data-director-crowd-mobile-trigger]").click(timeout=15_000)
            mpage.wait_for_timeout(700)
            mst = mpage.evaluate(READ)
            v.check("mobile:the-mobile-entry-still-opens-the-dialog",
                    mst.get("对话框") is not None
                    and (mst.get("对话框") or {}).get("w") == SOURCE["dialog"]["w"],
                    mst.get("对话框"))
            mpage.close()
        except Exception:  # noqa: BLE001
            import traceback
            v.check("probe:no-exception", False, traceback.format_exc()[-1200:])
        finally:
            browser.close()

    audit["checks"] = v.result
    audit["failures"] = v.failures
    audit["count"] = v.count
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "runtime-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"\n{v.count} 判据，{len(v.failures)} 失败")
    for f in v.failures:
        print("  FAILED: " + f)
    return 1 if v.failures else 0


if __name__ == "__main__":
    sys.exit(main())
