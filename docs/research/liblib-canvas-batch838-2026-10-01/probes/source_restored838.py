#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838：★ **当下独立复核**源站是否已复原（跨刷新读权威 API）。

★ 为什么要有这一趟（★ 已入库那条「内存里消失 ≠ 存盘了」的直系应用）：
  - v19（`charname838j`）那趟自己**新建**的「角色B」没删掉 ⟹ 它的 `F_★★是否已复原 = False`；
  - 随后 `cleanup838.py` 把它删了 ⟹ **API 读数**确认只剩「角色A」；
  - ★★ 但那两趟**都在同一个浏览器进程里** ⟹ 「内存里的 DOM 没了」与「服务端真存了」
    仍然只由**同一份 API 读数**支撑 ⟹ ⟹ 补这一趟：**全新进程、全新浏览器会话**
    再读一次 API ⟹ 证明复原是**服务端状态**，不是内存残留。

★ 只读：全程**不点任何东西**（不建、不删、不改）⟹ 不会二次污染源站。

★ 铁律（沿用 v17）：
  - 鉴权头（`token` ＋ `webid`）**只能从页面自己发的请求里抄** ⟹ 手打必然失效；
  - 响应里**必须**有 `data.projectDetail.nodeList` ⟹ 读不到就**显式失败**，不下结论；
  - 找不到 `type=36` 的导演台节点 ⟹ **显式失败**，不下结论。
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_restored838.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")
DETAIL_API = ("https://api.liblib.tv/api/canvas/project/detail-by-space"
              "?spaceId=7709759"
              "&projectUuid=a860e1da8e9e4504bececda022386429")


def api_read(page, auth) -> dict:
    """★ 权威读数：导演台节点的 `compositionData`。读不到就抛 ⟹ 不下结论。"""
    resp = page.request.get(DETAIL_API, headers=auth)
    raw = resp.text()
    d = json.loads(raw)
    node_list = ((d.get("data") or {}).get("projectDetail") or {}).get("nodeList")
    if not node_list:
        raise RuntimeError(
            "API 没返回 nodeList（len=%d, code=%s, msg=%s）⟹ 读数方法坏了 ⟹ 不下结论"
            % (len(raw), d.get("code"), d.get("msg")))
    for node in node_list:
        if node.get("type") != 36:
            continue
        dd = json.loads(node["data"])
        comp = dd.get("compositionData")
        if isinstance(comp, str):
            comp = json.loads(comp)
        if isinstance(comp, dict):
            return {
                "角色": [{"id": c.get("id"), "label": c.get("label")}
                        for c in (comp.get("characters") or [])],
                "相机": [c.get("label") for c in (comp.get("cameras") or [])],
            }
    raise RuntimeError("API 里没有 type=36 的导演台节点 ⟹ 不下结论")


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
    try:
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
            auth = {}

            def on_req(req):
                try:
                    if 'detail-by-space' not in req.url:
                        return
                    h = req.headers
                    if h.get('token'):
                        auth['token'] = h['token']
                    if h.get('webid'):
                        auth['webid'] = h['webid']
                except Exception:
                    pass

            page.on('request', on_req)
            page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            page.wait_for_timeout(14_000)
            out["★捕获到的鉴权头键"] = sorted(auth.keys())
            if 'token' not in auth or 'webid' not in auth:
                raise RuntimeError("没抓到 token/webid ⟹ 读数方法坏了 ⟹ 不下结论")
            read = api_read(page, auth)
            out["★独立复核_角色"] = read["角色"]
            out["★独立复核_角色标签"] = [c["label"] for c in read["角色"]]
            out["★独立复核_相机标签"] = read["相机"]
            out["★角色数"] = len(read["角色"])
            out["★★是否只剩角色A"] = (
                len(read["角色"]) == 1 and read["角色"][0]["label"] == "角色A")
            out["★★角色A的id是否仍是xqns9rxe"] = (
                len(read["角色"]) == 1 and read["角色"][0]["id"] == "xqns9rxe")
            out["★★是否还有实验遗留的角色B"] = any(
                c["label"] == "角色B" for c in read["角色"])
            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        for k in ("★独立复核_角色标签", "★独立复核_相机标签", "★角色数",
                  "★★是否只剩角色A", "★★角色A的id是否仍是xqns9rxe",
                  "★★是否还有实验遗留的角色B"):
            print("%-30s %r" % (k, out.get(k)))
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
