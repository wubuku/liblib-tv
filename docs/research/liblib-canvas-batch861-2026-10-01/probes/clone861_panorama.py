#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 861 clone 探针：读「全景图」面板三行**是不是真的有反应**。

## ★ 靶子

★ clone 此前这三行**完全没有 `onClick`** ⟹ ⟹ 点了什么也不会发生（死按钮）。
★ 源站实测（`raw/source-861-panorama-diff.json`）：
  · 「本地上传」⟹ ⟹ **弹出文件选择器**（`filechooser` 事件 ＝ True）
  · 「历史记录」⟹ ⟹ 打开**资产库选择器**（按钮 86 → 95）
  · 「AI生成」  ⟹ ⟹ 打开**同一个**选择器 ＋ 多「上传图片」「生成」「关闭」（86 → 98）

## ★ 本探针要读到的

A. 点「本地上传」⟹ ⟹ **Playwright 收到 `filechooser` 事件**（不选文件）；
B. 隐藏 file input 在 DOM 且 `accept="image/*"`；
C. 点「历史记录」⟹ ⟹ picker 在 DOM、`mode=history`、**没有**「生成」按钮；
D. 点「AI生成」⟹ ⟹ picker 在 DOM、`mode=ai`、**有**「生成」按钮；
E. ★ 用 `set_input_files` 喂一张**真图** ⟹ ⟹ store 里出现
   `localPanoramaAsset` ⟹ ⟹ 选择器里多出一个选项 ⟹ ⟹ 确认后全景图来源变成它；
F. 无诊断错误。

## 输出
  raw/clone-861-panorama.json
"""
from __future__ import annotations

import json
import pathlib
import struct
import zlib

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch861-2026-10-01"
RAW = BATCH / "raw"
BASE = "http://localhost:4317"
FIXTURE = pathlib.Path("/tmp/b861-local-panorama.png")

READ = r"""()=>{
  const q=(s)=>document.querySelector(s);
  const picker=q('[data-director-panorama-picker]');
  const fileInput=q('[data-director-panorama-file-input]');
  const store=window.__director_store;
  const asset=store?store.getState().localPanoramaAsset:null;
  return {
    三行: [...document.querySelectorAll('[data-director-panorama-option]')].map(e=>({
      id:e.getAttribute('data-director-panorama-option'),
      text:(e.textContent||'').replace(/\s+/g,' ').trim(),
      rect:(()=>{const r=e.getBoundingClientRect();
        return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};})(),
    })),
    隐藏文件输入: fileInput?{accept:fileInput.getAttribute('accept'),
                            type:fileInput.getAttribute('type'),
                            在场:!!fileInput}:null,
    选择器: picker?{
      mode:picker.getAttribute('data-director-panorama-picker-mode'),
      rect:(()=>{const r=picker.getBoundingClientRect();
        return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};})(),
      有生成按钮:!!q('[data-director-panorama-generate]'),
      有上传图片按钮:!!q('[data-director-panorama-picker-upload]'),
      有取消按钮:!!q('[data-director-panorama-picker-cancel]'),
      有确认按钮:!!q('[data-director-panorama-picker-confirm]'),
      空态:!!q('[data-director-panorama-picker-empty]'),
      选项: [...document.querySelectorAll('[data-director-panorama-picker-option]')]
        .map(e=>e.getAttribute('data-director-panorama-picker-option')),
    }:null,
    本地资产: asset?{id:asset.id, filename:asset.filename,
                     imageUrl前缀:asset.imageUrl.slice(0,12),
                     w:asset.width, h:asset.height}:null,
    // ★ ★ 分开读「元素在不在场」与「属性是多少」⟹ ⟹ 别用 fallback 把
    //   「元素不存在」和「属性为空」混成同一个 null。
    全景图选择元素在场: !!q('[data-director-panorama-selection]'),
    全景图来源: q('[data-director-panorama-selection]')
      ? q('[data-director-panorama-selection]').getAttribute('data-director-panorama-source-id')
      : '(元素不在场)',
    全景图状态元素在场: !!q('[data-director-panorama-status]'),
    全景图状态: q('[data-director-panorama-status]')
      ? (q('[data-director-panorama-status]').textContent||'').replace(/\s+/g,' ').trim()
      : '(元素不在场)',
    当前全景图元素在场: !!q('[data-director-panorama-current]'),
    当前全景图来源: q('[data-director-panorama-current]')
      ? q('[data-director-panorama-current]').getAttribute('data-director-panorama-current-source')
      : '(元素不在场)',
    当前全景图文本: q('[data-director-panorama-current]')
      ? (q('[data-director-panorama-current]').textContent||'').replace(/\s+/g,' ').trim()
      : '(元素不在场)',
    检查器在场: !!q('[data-director-panorama-source]'),
  };
}"""


def write_fixture() -> None:
    """★ 生成一张 8×8 的真 PNG（不依赖仓库里的大图）。"""
    w = h = 8
    raw = b"".join(b"\x00" + bytes([(x * 30) % 256, (y * 30) % 256, 180] * 1)
                   * w for y in range(h) for x in [0])
    # ★ 逐像素构造（RGB）
    rows = []
    for y in range(h):
        row = b"\x00"
        for x in range(w):
            row += bytes([(x * 30) % 256, (y * 30) % 256, 180])
        rows.append(row)
    raw = b"".join(rows)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw))
           + chunk(b"IEND", b""))
    FIXTURE.write_bytes(png)


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
    write_fixture()
    out: dict = {}
    chooser_fired: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080},
                                    device_scale_factor=1)
            errors: list[str] = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: errors.append(m.text)
                    if m.type == "error" else None)
            page.on("filechooser", lambda fc: chooser_fired.append("filechooser"))
            open_desk(page)
            page.locator("[data-director-rail-entry='panorama']").first.click(
                timeout=15000)
            page.wait_for_timeout(900)

            out["打开面板后"] = page.evaluate(READ)

            # ★ A：点「本地上传」⟹ ⟹ 应当弹出文件选择器
            page.locator("[data-director-panorama-option='local-upload']").first.click(
                timeout=15000)
            page.wait_for_timeout(1200)
            out["本地上传_弹了文件选择器"] = bool(chooser_fired)
            out["本地上传_弹了文件选择器_次数"] = len(chooser_fired)

            # ★ C：点「历史记录」
            page.locator("[data-director-panorama-option='history']").first.click(
                timeout=15000)
            page.wait_for_timeout(900)
            out["历史记录_后"] = page.evaluate(READ)
            # ★ ★ 选择器是**全屏遮罩**（源站同款：实测 rect 1920×1080）
            #   ⟹ ⟹ 它会**挡住**面板 ⟹ ⟹ 必须先关掉才能点下一行。
            page.locator("[data-director-panorama-picker-cancel]").first.click(
                timeout=15000)
            page.wait_for_timeout(700)
            out["取消后_选择器在场"] = page.evaluate(READ)["选择器"] is not None

            # ★ D：点「AI生成」
            page.locator("[data-director-panorama-option='ai-generate']").first.click(
                timeout=15000)
            page.wait_for_timeout(900)
            out["AI生成_后"] = page.evaluate(READ)
            page.locator("[data-director-panorama-picker-cancel]").first.click(
                timeout=15000)
            page.wait_for_timeout(700)

            # ★ E：喂一张真文件给隐藏 input ⟹ ⟹ 触发 onChange
            page.locator("[data-director-panorama-file-input]").first.set_input_files(
                str(FIXTURE), timeout=15000)
            page.wait_for_timeout(1500)
            out["选完文件后"] = page.evaluate(READ)

            # ★ 打开选择器 ⟹ ⟹ 断言本地那张在选项里 ⟹ ⟹ 选中并确认
            page.locator("[data-director-panorama-option='history']").first.click(
                timeout=15000)
            page.wait_for_timeout(900)
            out["含本地的选择器"] = page.evaluate(READ)
            options = out["含本地的选择器"]["选择器"]["选项"] or []
            local_opt = next((o for o in options if o.startswith("local-panorama:")), None)
            out["本地选项"] = local_opt
            if local_opt:
                page.locator(
                    f"[data-director-panorama-picker-option='{local_opt}']").first.click(
                    timeout=15000)
                page.wait_for_timeout(500)
                page.locator("[data-director-panorama-picker-confirm]").first.click(
                    timeout=15000)
                page.wait_for_timeout(1200)
            out["确认后"] = page.evaluate(READ)

            out["错误"] = [e for e in errors if "TransformControls" not in e][:8]
        finally:
            browser.close()
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "clone-861-panorama.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1)[:5000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
