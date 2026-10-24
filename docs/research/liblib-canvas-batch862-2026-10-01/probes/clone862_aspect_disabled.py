#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 862 clone 探针：**删光机位** ⟹ ⟹ 七档画幅比例应当**全部禁用**。

## ★ 靶子

★ 源站逐字（`aU` 的 props ＋ 父组件传参 ＋ aspect 段）：
- `hasCameras:a` ⟹ 父组件传 `hasCameras: rL.cameras.length > 0`
- aspect 段每一格：`disabled:!a`
- 类名含 `disabled:cursor-not-allowed disabled:opacity-35`

⇒ ⇒ **没有机位 ⟹ 七档比例全部禁用**（源站逐字）。

★ ★★ 诚实标注：源站的「无机位」态**未能实测**（源站机位行只有「隐藏」「锁定」，
`Delete`／`Backspace` 都删不掉）⟹ ⟹ 本探针在 **clone 侧**实测这条契约。

## ★ 本探针要读到的

① 有机位时：七格 `disabled=false`；
② ★ 删光机位（点对象树里的删除按钮）⟹ ⟹ 七格 `disabled=true`
   ＋ `cursor: not-allowed` ＋ `opacity: 0.35`；
③ ★ 禁用态下点「16:9」⟹ ⟹ **取景比例不变**（禁用按钮点不动）；
④ 删机位前后的机位计数 ＋ 无诊断错误。

## 输出
  raw/clone-862-aspect-disabled.json
"""
from __future__ import annotations

import json
import pathlib

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch862-2026-10-01"
RAW = BATCH / "raw"
BASE = "http://localhost:4317"

READ_OPTIONS = r"""()=>{
  const q=(s)=>document.querySelector(s);
  return [...document.querySelectorAll('[data-director-aspect-option]')].map(e=>{
    const cs=getComputedStyle(e);
    return {text:(e.textContent||'').replace(/\s+/g,' ').trim(),
            disabled:e.disabled===true, opacity:cs.opacity, cursor:cs.cursor};
  });
}"""

# ★ 场景树里机位行（kind==="camera"）与它们的删除按钮
READ_TREE = r"""()=>{
  const store=window.__director_store;
  const objects=store?store.getState().objects:[];
  const cams=objects.filter(o=>o.kind==='camera');
  const dels=[...document.querySelectorAll('[data-director-delete-object]')].map(e=>{
    const r=e.getBoundingClientRect();
    return {id:e.getAttribute('data-director-delete-object'),
            x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};
  });
  return {机位数:cams.length, 机位:cams.map(c=>({id:c.id,name:c.name})),
          删除按钮:dels};
}"""

READ_FRAME = r"""()=>{
  const s=window.__director_store?window.__director_store.getState():null;
  return {取景比例:s?s.frameAspectRatio:null,
          取景框:!!document.querySelector('[data-director-aspect-frame]')};
}"""


def open_desk(page) -> None:
    page.goto(BASE + "/", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
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
    page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")


def main() -> int:
    out: dict = {"batch": 862, "probe": "clone862_aspect_disabled"}
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

            # ① 有机位 ⟹ aspect 模式读七格
            page.locator("[data-director-rail-entry='aspect-ratio']").first.click(
                timeout=15000)
            page.wait_for_timeout(900)
            out["有机位_七格"] = page.evaluate(READ_OPTIONS)
            out["有机位_机位数"] = page.evaluate(READ_TREE)["机位数"]

            # ② 回到 scene 模式 ⟹ ⟹ 删光机位
            page.locator("[data-director-rail-entry='scene']").first.click(
                timeout=15000)
            page.wait_for_timeout(900)
            deleted: list[str] = []
            for _ in range(8):
                tree = page.evaluate(READ_TREE)
                out.setdefault("删除过程", []).append(
                    {"机位数": tree["机位数"], "删除按钮数": len(tree["删除按钮"])})
                if tree["机位数"] == 0:
                    break
                cam_ids = {c["id"] for c in tree["机位"]}
                target = next((d for d in tree["删除按钮"] if d["id"] in cam_ids), None)
                if target is None:
                    out.setdefault("删除过程", []).append({"找不到机位的删除按钮": True})
                    break
                page.mouse.click(target["x"] + target["w"] / 2,
                                 target["y"] + target["h"] / 2)
                deleted.append(target["id"])
                page.wait_for_timeout(900)
            out["删掉的机位"] = deleted
            out["删完后_机位数"] = page.evaluate(READ_TREE)["机位数"]

            # ③ 无机位 ⟹ aspect 模式读七格
            page.locator("[data-director-rail-entry='aspect-ratio']").first.click(
                timeout=15000)
            page.wait_for_timeout(900)
            out["无机位_七格"] = page.evaluate(READ_OPTIONS)

            # ④ 禁用态下点「16:9」⟹ ⟹ 取景比例应当不变
            before = page.evaluate(READ_FRAME)
            try:
                page.locator("[data-director-aspect-option='16:9']").first.click(
                    timeout=8000, force=True)
                page.wait_for_timeout(900)
            except Exception as exc:  # noqa: BLE001
                out["点16比9_异常"] = type(exc).__name__
            after = page.evaluate(READ_FRAME)
            out["点16比9_前"] = before
            out["点16比9_后"] = after
            out["点16比9_比例未变"] = before["取景比例"] == after["取景比例"]

            out["错误"] = [e for e in errors if "TransformControls" not in e][:8]
        finally:
            browser.close()
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "clone-862-aspect-disabled.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("有机位_七格:", json.dumps(out.get("有机位_七格"), ensure_ascii=False)[:220])
    print("有机位_机位数:", out.get("有机位_机位数"))
    print("删除过程:", json.dumps(out.get("删除过程"), ensure_ascii=False))
    print("删完后_机位数:", out.get("删完后_机位数"))
    print("无机位_七格:", json.dumps(out.get("无机位_七格"), ensure_ascii=False)[:400])
    print("点16比9_比例未变:", out.get("点16比9_比例未变"),
          "| 前:", out.get("点16比9_前"), "| 后:", out.get("点16比9_后"))
    print("错误:", out.get("错误"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
