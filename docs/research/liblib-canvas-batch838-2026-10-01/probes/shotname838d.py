#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838 源站探针 v4：从 **react-flow 的 store** 读画布节点的**完整数据**。

★ v3 已确证：视频节点的 DOM id `v-3CmzlptLJl` 是**随机串** ⟹ 「S83」**不是**从 id 来的。
★ v3 的 Fiber 爬取只到 up=1 就有 id ⟹ 真实数据在 react-flow 的 store 里。

★ 方法：找 react-flow 的实例（DOM 上带 `__reactFiber` → props 里带 `store`，
  或 `__reactProps$` 里有 `store`）⟹ 调 `store.getState().nodes` 拿到**每个节点的 data**。

★ 拿到 data 后直接读：
  - video 节点的 `name` / `title` / `label`；
  - 与它相关的编号字段（shotId / scriptId / index / seq）；
  - ★ script-v2 节点的 id 与编号（用于对照「S83」的 83 是不是脚本序号）。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_shotname838d.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

DUMP_FLOW = """() => {
  const res={found:[], errors:[]};
  // ① 从任一 react-flow 节点往上爬，找带 store 的 props
  const node=document.querySelector('.react-flow__node');
  if (!node) return {err:'没有节点'};
  const fk=Object.keys(node).find(k=>k.startsWith('__reactFiber$'));
  if (!fk) return {err:'没有 fiber'};
  let fiber=node[fk];
  const scalar = (v, depth) => {
    if (v===null||v===undefined) return v;
    const t=typeof v;
    if (t==='string') return v.length>400 ? v.slice(0,400)+'…' : v;
    if (t==='number'||t==='boolean') return v;
    if (t==='function') return '[fn]';
    if (Array.isArray(v)) return v.slice(0,30).map(x=>scalar(x,depth+1));
    if (t==='object') {
      if (v.nodeType) return '[dom]';
      if (depth>3) return '[obj]';
      const o={}; let n=0;
      for (const [k,x] of Object.entries(v)) {
        if (n>=80) break;
        if (k.startsWith('__react')||k==='Provider'||k==='Consumer'||k==='_context') continue;
        if (typeof x==='function') continue;
        try { o[k]=scalar(x,depth+1); n++; } catch(e){}
      }
      return o;
    }
    return String(v);
  };
  for (let up=0; up<25 && fiber; up++, fiber=fiber.return) {
    const mp=fiber.memoizedProps;
    if (!mp || typeof mp!=='object') continue;
    const st = mp.store || (mp.state && mp.state.store) || null;
    if (st && typeof st.getState==='function') {
      try {
        const s=st.getState();
        const nodes=s.nodes||[];
        res.found.push({
          up,
          type:(typeof fiber.type==='string'?fiber.type:(fiber.type&&(fiber.type.displayName||fiber.type.name))||'?'),
          nodeCount:nodes.length,
          nodes:nodes.map(nd=>({
            id:nd.id,
            type:nd.type,
            data: scalar(nd.data,0),
          })),
        });
        if (res.found.length>=2) break;
      } catch(e) { res.errors.push('up'+up+': '+String(e)); }
    }
  }
  return res;
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(800)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(9_000)


def clean(page):
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")


def run(out, cookies):
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
        page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(12_000)
        open_desk(page)
        clean(page)
        out["①reactFlow"] = page.evaluate(DUMP_FLOW)
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
        rf = out.get("①reactFlow") or {}
        print("err:", rf.get("err"))
        for f in rf.get("found") or []:
            print("=== up=%s type=%s nodeCount=%s ===" % (f["up"], f["type"], f["nodeCount"]))
            for nd in f["nodes"]:
                print("  id=%s type=%s" % (nd["id"], nd["type"]))
                print("     data=", json.dumps(nd["data"], ensure_ascii=False)[:600])
        if rf.get("errors"):
            print("errors:", rf["errors"][:5])
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
