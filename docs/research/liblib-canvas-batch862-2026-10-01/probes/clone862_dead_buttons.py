#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 862 clone 普查：**导演台里哪些按钮点了没反应**。

## ★ 为什么做这个普查

★ 用户硬要求：「检查既有复刻成果，发现『糊弄』之处必须整改」。
★ 逐个面板人工点一遍太慢 ⟹ ⟹ 这个探针**自动**遍历导演台左栏五个模式面板
里的**每一枚按钮** ⟹ ⟹ 逐个点 ⟹ ⟹ 看**是否产生可观测变化**
（DOM 变化／出现对话框／出现提示条）⟹ ⟹ 报出「点了没反应」的清单。

## ★ 安全

★ **排除**掉一切可能有副作用的入口（删除／生成／AI／截图／导出／购买／上传／发布）：
`删除|移除|trash|delete|生成|AI |智能|截图|导出|发布|购买|上传|充值|解冻|恢复`
★ 其余按钮一律点 ⟹ ⟹ 点完**刷新页面**再继续下一个 ⟹ ⟹ 避免互相污染。

## ★ 输出
  raw/clone-862-dead-buttons.json
"""
from __future__ import annotations

import json
import pathlib
import re

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch862-2026-10-01"
RAW = BATCH / "raw"
BASE = "http://localhost:4317"

DANGEROUS = re.compile(
    r"删除|移除|回收|trash|delete|生成|智能|AI|截图|导出|发布|购买|上传|充值|"
    r"解冻|恢复|确认|提交|保存|新建|添加|创建|开始|拉片|合成",
    re.I,
)

# ★ 读「当前页面上有什么」的指纹
SNAP = r"""()=>{
  const btn=[...document.querySelectorAll('button')].map(b=>
    ((b.getAttribute('aria-label')||'')+'|'+(b.title||'')+'|'
     +(b.textContent||'')).replace(/\s+/g,' ').trim().slice(0,60));
  const dialogs=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"]')]
    .map(e=>{const r=e.getBoundingClientRect();
      return {w:Math.round(r.width),h:Math.round(r.height),
              text:(e.textContent||'').replace(/\s+/g,' ').trim().slice(0,120)};})
    .filter(d=>d["w"]>0);
  const body=(document.body.innerText||'').replace(/\s+/g,' ').trim();
  return {nButtons:btn.length, dialogs:dialogs, textLen:body.length,
          bodyTail:body.slice(-300),
          toast:[...document.querySelectorAll('[class*="toast"],[class*="Toast"],'
            +'[class*="notice"],[class*="ack"],[class*="flash"]')]
            .map(e=>(e.textContent||'').replace(/\s+/g,' ').trim().slice(0,90))
            .filter(Boolean).slice(0,5)};
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


# ★ 读左栏面板内的按钮（48 ≤ x < 300 ⟹ 排除 rail 那一列）
READ_PANEL_BUTTONS = r"""()=>{
  const out=[];
  for(const b of document.querySelectorAll('aside button')){
    const r=b.getBoundingClientRect();
    if(r.width===0||r.height===0) continue;
    if(r.x<48||r.x>=300) continue;
    const label=((b.getAttribute('aria-label')||'')+'|'+(b.title||'')+'|'
                 +(b.textContent||'')).replace(/\s+/g,' ').trim().slice(0,60);
    out.push({label, disabled:b.disabled===true,
              x:Math.round(r.x),y:Math.round(r.y),
              w:Math.round(r.width),h:Math.round(r.height)});
  }
  return out;
}"""


def main() -> int:
    out: dict = {"batch": 862, "probe": "clone862_dead_buttons", "modes": {}}
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

            modes = ["scene", "add-character", "add-camera", "panorama", "aspect-ratio"]
            for mode in modes:
                entry = page.locator(f"[data-director-rail-entry='{mode}']").first
                entry.click(timeout=15000)
                page.wait_for_timeout(900)
                buttons = page.evaluate(READ_PANEL_BUTTONS)
                results = []
                for b in buttons:
                    label = b["label"]
                    if not label or DANGEROUS.search(label):
                        results.append({**b, "结果": "跳过（可能有副作用）"})
                        continue
                    before = page.evaluate(SNAP)
                    try:
                        page.mouse.click(b["x"] + b["w"] / 2, b["y"] + b["h"] / 2)
                        page.wait_for_timeout(1100)
                        after = page.evaluate(SNAP)
                        changed = (
                            after["nButtons"] != before["nButtons"]
                            or after["textLen"] != before["textLen"]
                            or len(after["dialogs"]) != len(before["dialogs"])
                            or after["toast"] != before["toast"]
                        )
                        results.append({
                            **b, "结果": "有反应" if changed else "★ 没反应",
                            "前": {"按钮数": before["nButtons"],
                                   "文本长": before["textLen"],
                                   "对话框数": len(before["dialogs"]),
                                   "提示": before["toast"]},
                            "后": {"按钮数": after["nButtons"],
                                   "文本长": after["textLen"],
                                   "对话框数": len(after["dialogs"]),
                                   "提示": after["toast"]},
                        })
                    except Exception as exc:  # noqa: BLE001
                        results.append({**b, "结果": f"★ 崩了: {type(exc).__name__}"})
                    # ★ 点完回到该模式 ⟹ ⟹ 避免面板被点没了
                    try:
                        page.locator(f"[data-director-rail-entry='{mode}']").first.click(
                            timeout=8000)
                        page.wait_for_timeout(500)
                    except Exception:  # noqa: BLE001
                        pass
                out["modes"][mode] = results
                dead = [r for r in results if str(r.get("结果", "")).startswith("★")]
                print(f"[{mode}] 按钮 {len(buttons)} 枚，可疑 {len(dead)} 枚："
                      f"{[r['label'] for r in dead]}", flush=True)
            out["错误"] = [e for e in errors if "TransformControls" not in e][:8]
        finally:
            browser.close()
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "clone-862-dead-buttons.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
