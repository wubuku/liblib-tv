#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838 源站探针 v5：从 **网络响应**里拿画布节点的权威数据。

★ 为什么换这条路：v3 的 Fiber 只爬到 up=1 的 id；v4 从 Fiber 找 react-flow 的
  store **没找到**（props 里没有 store）⟹ ★ **读运行时内部结构这条路走不通** ⟹
  ★ 改走**权威数据源**：画布节点的 JSON 是从 API 拉的 ⟹ 抓响应。

★ 本探针：
  ① 记录所有 XHR/fetch 响应（URL + 状态 + 体积）；
  ② 把**含「镜」「S83」「shot」「镜头」**等关键词的响应体**落盘**；
  ③ 在响应体里搜「S83」与「·镜」⟹ 看标题的**生成端**（是服务端给的，还是前端拼的）。

★ 只读，不改源站项目。
"""
import json
import pathlib
import re
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_shotname838e.json")
RAW_DIR = pathlib.Path("/tmp/liblib_838e_raw")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

KEYWORDS = ("S83", "·镜", "镜2", "镜头", "shot", "Shot", "storyboard", "分镜")


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(800)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(9_000)


def run(out, cookies):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1920, "height": 1080}, locale="zh-CN")
        ctx.add_cookies([{"name": c["name"], "value": c["value"],
                          "domain": c["domain"], "path": c.get("path", "/"),
                          "expires": c.get("expires", -1),
                          "httpOnly": c.get("httpOnly", False),
                          "secure": c.get("secure", False),
                          "sameSite": c.get("sameSite", "Lax")} for c in cookies])
        page = ctx.new_page()
        seen = []
        hits = []

        def on_response(resp):
            try:
                ct = resp.headers.get("content-type", "") or ""
                if "json" not in ct and "text" not in ct:
                    return
                body = resp.text()
            except Exception:
                return
            if not body or len(body) > 4_000_000:
                return
            url = resp.url
            seen.append({"url": url[:200], "status": resp.status, "len": len(body)})
            found = [k for k in KEYWORDS if k in body]
            if found:
                name = re.sub(r"[^A-Za-z0-9_.-]", "_", url.split("?")[0].split("/")[-1] or "resp")
                p = RAW_DIR / (name + ".txt")
                try:
                    p.write_text(body, encoding="utf-8")
                except Exception:
                    pass
                hits.append({"url": url[:200], "status": resp.status, "len": len(body),
                             "keywords": found, "saved": str(p)})

        page.on("response", on_response)
        page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(12_000)
        open_desk(page)
        page.wait_for_timeout(4_000)
        out["①全部响应"] = seen
        out["②命中关键词的响应"] = hits
        out["★S83出现在哪些响应"] = [h["url"] for h in hits if "S83" in h["keywords"]]
        br.close()


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    try:
        run(out, cookies)
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        print("\n=== 命中关键词的响应 ===")
        for h in out.get("②命中关键词的响应") or []:
            print("  [%s] len=%s kw=%s" % (h["status"], h["len"], h["keywords"]))
            print("     ", h["url"][:160])
        print("\n=== S83 出现在 ===")
        for u in out.get("★S83出现在哪些响应") or []:
            print("  ", u[:160])
        print("\n=== 响应总数 ===", len(out.get("①全部响应") or []))
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
