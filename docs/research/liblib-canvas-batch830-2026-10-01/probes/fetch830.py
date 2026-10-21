#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 830：把**源站导演台组件代码**抓下来。

★ 为什么必须抓：缓存的 161 个 chunk 里，连「导演视角」按钮的 i18n 键
  （`directorViewModeDirector`）都**只出现在 i18n 字典 chunk 里** ⟹
  导演台的组件代码**根本不在缓存里** ⟹ 盲按快捷键测不出东西，
  得直接读代码：快捷键到底绑在哪、什么条件下生效、撤销栈覆盖什么。

★ 抓法：开着导演台录下所有 .js 请求 ⟹ 把**缓存里没有的**存到 /tmp/liblib_srcjs2/
  同时把 XHR/fetch 的 JSON 响应存下来（快捷键说明表可能是服务端下发的）。
"""
import json
import pathlib
import urllib.request

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
CACHE = pathlib.Path("/tmp/liblib_srcjs")
OUTDIR = pathlib.Path("/tmp/liblib_srcjs2")
API_DIR = pathlib.Path("/tmp/liblib_srcapi")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")
OUT = pathlib.Path("/tmp/liblib_source_desk830_fetch.json")


def main():
    OUTDIR.mkdir(exist_ok=True)
    API_DIR.mkdir(exist_ok=True)
    known = {p.name for p in CACHE.glob("*.js.js")}
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    seen_js = []
    seen_api = []
    body_store = {}

    def on_request(req):
        u = req.url
        if ".js" in u and "static" in u or u.endswith(".js"):
            seen_js.append(u)
        if req.resource_type in ("xhr", "fetch"):
            seen_api.append(u)

    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                             locale="zh-CN")
        ctx.add_cookies([{"name": c["name"], "value": c["value"],
                          "domain": c["domain"], "path": c.get("path", "/"),
                          "expires": c.get("expires", -1),
                          "httpOnly": c.get("httpOnly", False),
                          "secure": c.get("secure", False),
                          "sameSite": c.get("sameSite", "Lax")} for c in cookies])
        page = ctx.new_page()
        page.on("request", on_request)

        def on_response(resp):
            u = resp.url
            if resp.request.resource_type in ("xhr", "fetch"):
                try:
                    body_store[u] = resp.text()[:200000]
                except Exception:
                    pass

        page.on("response", on_response)
        page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(12_000)
        before = set(seen_js)
        card = page.locator(".react-flow__node-director-console-3d").first
        card.hover()
        page.wait_for_timeout(600)
        page.locator(
            ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
        page.wait_for_timeout(10_000)
        new_js = [u for u in dict.fromkeys(seen_js) if u not in before]
        # 也把「本来就加载过但缓存里没有」的算上
        missing = [u for u in dict.fromkeys(seen_js) if u.split("/")[-1] not in known]
        todo = list(dict.fromkeys(new_js + missing))
        got = []
        for u in todo:
            name = u.split("/")[-1].split("?")[0]
            try:
                data = urllib.request.urlopen(u, timeout=60).read()
                (OUTDIR / (name + ".js")).write_bytes(data)
                got.append({"url": u, "name": name, "bytes": len(data),
                            "in_old_cache": name in known})
            except Exception as e:
                got.append({"url": u, "error": str(e)[:120]})
        for i, u in enumerate(dict.fromkeys(seen_api)):
            b = body_store.get(u)
            if b:
                (API_DIR / ("api%03d.json" % i)).write_text(b, encoding="utf-8")
        (OUT / "js.json").parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(
            {"new_js_on_open": new_js, "downloaded": got,
             "api_urls": list(dict.fromkeys(seen_api))[:80],
             "api_files": sorted(p.name for p in API_DIR.glob("*.json"))},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print("下载 %d 个新 chunk；API %d 个" % (len(got), len(list(API_DIR.glob('*.json')))))
        for g in got:
            print("  ", g.get("name"), g.get("bytes"), "旧缓存有" if g.get("in_old_cache") else "")
        ctx.close()
        br.close()


if __name__ == "__main__":
    main()
