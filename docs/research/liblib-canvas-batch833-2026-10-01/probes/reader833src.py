#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 833：源站**只读**探针 —— 验证**规则 R**（probes/reader833.py）在源站活体上成立。

★ 本探针**只读**：不点任何机位预设 ⟹ 不会新建机位 ⟹ 不产生副作用。

★ 干什么：
  1. 打开导演台 ⟹ 点场景树里的「机位1」（**已存在**的机位 ⟹ 选中不产生副作用）
  2. 用**与 clone 侧完全相同**的 JS 读数器（reader833.READ_PROPS_JS）读右栏
  3. 与**另一次独立采集**（/tmp/liblib_source_diag833.json，diag833.py 的产物）
     的读数**逐字比对**
  ⟹ ★ 这一步是为了证明「规则 R 在源站上真的能读出东西」——
     否则后面 clone 侧读到一组数，也可能是**读数器在源站侧就已经瞎了**，
     两边一起瞎 ⟹ 「逐字相等」就成了**两个空集相等**。

★ 落盘：raw/source-833-reader-selftest.json
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from reader833 import READ_PROPS_JS, semantics_from_js  # noqa: E402

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
DIAG = pathlib.Path("/tmp/liblib_source_diag833.json")
OUT = (pathlib.Path(__file__).resolve().parent.parent
       / "raw" / "source-833-reader-selftest.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(800)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(9_000)


def diag_expectation():
    """从 diag833.py 的独立采集里，取出「选中机位1后右栏」的所有 number 值 + range 值。"""
    doc = json.loads(DIAG.read_text(encoding="utf-8"))
    rows = doc["②选中机位1后右栏"]["rows"]
    nums = [r["value"] for r in rows
            if r["tag"] == "INPUT" and r["type"] == "number"]
    ranges = [r["value"] for r in rows
              if r["tag"] == "INPUT" and r["type"] == "range"]
    titles = [r["text"] for r in rows
              if r["tag"] in ("DIV", "SPAN", "LEGEND") and r["text"]]
    return {"nums": nums, "ranges": ranges, "titles": titles}


def main():
    if not COOKIE.exists():
        raise SystemExit("缺少 cookie：%s" % COOKIE)
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            ctx.add_cookies([{
                "name": c["name"], "value": c["value"], "domain": c["domain"],
                "path": c.get("path", "/"), "expires": c.get("expires", -1),
                "httpOnly": c.get("httpOnly", False),
                "secure": c.get("secure", False),
                "sameSite": c.get("sameSite", "Lax"),
            } for c in cookies])
            page = ctx.new_page()
            page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            page.wait_for_timeout(12_000)
            open_desk(page)
            try:
                page.get_by_text("机位1", exact=True).first.click()
                page.wait_for_timeout(2_500)
                js = page.evaluate(READ_PROPS_JS)
                out["规则R读数"] = js
                out["规则R语义"] = semantics_from_js(js)
                out["候选标题(FOV相关)"] = [c for c in js["candidates"]
                                       if "FOV" in c["t"]]
            except Exception as exc:  # noqa: BLE001
                out["异常"] = repr(exc)[:400]
            try:
                page.locator("[aria-label='关闭']:visible").first.click()
                page.wait_for_timeout(2_500)
            except Exception:
                pass
            ctx.close()
            br.close()
    finally:
        out["独立采集(对照)"] = diag_expectation()
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        print("已落盘：", OUT)
        print("规则R语义：", json.dumps(out.get("规则R语义"), ensure_ascii=False))


if __name__ == "__main__":
    main()
