#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838 源站探针 v3：读出视频节点「**S83·镜2**」的**数据来源**。

★ v1 已确证：「S83·镜2」是 `react-flow__node-video` 节点的**标题**（不是镜头名）。
★ v2 已确证：节点 id = `v-3CmzlptLJl`；兄弟节点 script-v2 id=`b-007xQ4Z8ZW` 标题「脚本 V2 1」。
★ v3 要做的：从 React Fiber 往上爬，拿到**节点的真实数据对象**，
  读出标题字段（name/title/label）与相关编号字段 ⟹ 才能回答
  「S83」= 什么、「镜2」= 什么。

★ 方法（**定点提取**，不整体序列化 ⟹ 不会撞循环引用）：
  - 从 DOM 节点找 `__reactFiber$<key>`；
  - 沿 `fiber.return` 往上爬若干层，每层取 `memoizedProps` 里的**标量**字段
    与**浅层对象**（限深度、限字段数、跳过 React 内部键）；
  - 特别关注：`name` / `title` / `label` / `index` / `shotId` / `scriptId` /
    `seq` / `number` / `camera` 等。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_shotname838c.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

DUMP_FIBER = """() => {
  const scalar = (v, depth) => {
    if (v === null || v === undefined) return v;
    const t = typeof v;
    if (t === 'string') return v.length > 160 ? v.slice(0,160)+'…' : v;
    if (t === 'number' || t === 'boolean') return v;
    if (t === 'function') return '[fn]';
    if (Array.isArray(v)) return v.slice(0,10).map(x=>scalar(x, depth+1));
    if (t === 'object') {
      if (v.nodeType) return '[dom]';
      if (depth > 2) return '[obj]';
      const o={};
      let n=0;
      for (const [k,x] of Object.entries(v)) {
        if (n>=40) break;
        if (k.startsWith('__react')||k==='Provider'||k==='Consumer'||k==='_context'
            ||k==='_currentValue'||k==='_currentValue2'||k==='_threadCount') continue;
        if (typeof x === 'function') continue;
        try { o[k]=scalar(x, depth+1); n++; } catch(e) {}
      }
      return o;
    }
    return String(v);
  };
  const INTEREST = ['name','title','label','text','index','idx','seq','number','no',
                    'shotId','shotIndex','scriptId','cameraId','camera','nodeId','id',
                    'type','kind','prompt','description','duration','frame','start','end'];

  const res=[];
  for (const n of Array.from(document.querySelectorAll('.react-flow__node'))) {
    const cls=(n.className||'').toString();
    const kind=(cls.match(/react-flow__node-([a-z0-9-]+)/)||[])[1]||'?';
    if (kind!=='video') continue;
    const fk=Object.keys(n).find(k=>k.startsWith('__reactFiber$'));
    if (!fk) { res.push({kind, err:'no fiber'}); continue; }
    let fiber=n[fk];
    const layers=[];
    for (let up=0; up<10 && fiber; up++, fiber=fiber.return) {
      const mp=fiber.memoizedProps;
      const layer={up, tag:fiber.tag, type:(typeof fiber.type==='string'?fiber.type:(fiber.type&&(fiber.type.displayName||fiber.type.name))||'?')};
      if (mp && typeof mp==='object') {
        const picked={};
        for (const k of INTEREST) {
          if (mp[k]!==undefined && mp[k]!==null && typeof mp[k]!=='function') {
            try { picked[k]=scalar(mp[k],0); } catch(e){ picked[k]='[err]'; }
          }
        }
        // 也抓 props 里浅层的 data/node
        for (const src of ['data','node','nodeData','item']) {
          if (mp[src] && typeof mp[src]==='object') {
            const sub={};
            for (const k of INTEREST) {
              if (mp[src][k]!==undefined && typeof mp[src][k]!=='function') {
                try { sub[k]=scalar(mp[src][k],1); } catch(e){}
              }
            }
            if (Object.keys(sub).length) picked[src]=sub;
          }
        }
        layer.picked=picked;
        layer.propKeys=Object.keys(mp).slice(0,30);
      }
      layers.push(layer);
    }
    res.push({kind, layers});
  }
  return res;
}"""

# ★ 节点内的 title 元素 / aria-label / data 属性
DUMP_VIDEO_HTML = """() => {
  const n=document.querySelector('.react-flow__node-video');
  if (!n) return null;
  const r=n.getBoundingClientRect();
  const attrs={};
  for (const a of Array.from(n.attributes)) attrs[a.name]=String(a.value).slice(0,120);
  const inner=[];
  for (const el of Array.from(n.querySelectorAll('*'))) {
    const b=el.getBoundingClientRect();
    const t=(el.textContent||'').trim();
    if (!t || t.length>50) continue;
    inner.push({tag:el.tagName, text:t, title:el.getAttribute('title'),
                aria:el.getAttribute('aria-label'),
                cls:(el.className||'').toString().slice(0,80),
                box:[Math.round(b.x),Math.round(b.y),Math.round(b.width),Math.round(b.height)]});
  }
  return {attrs, box:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)], inner:inner.slice(0,40)};
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
        out["①video节点HTML"] = page.evaluate(DUMP_VIDEO_HTML)
        out["②video节点Fiber"] = page.evaluate(DUMP_FIBER)
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
        v = out.get("①video节点HTML") or {}
        print("\n=== video 节点属性 ===")
        for k, val in (v.get("attrs") or {}).items():
            print("  %s = %s" % (k, val))
        print("\n=== 内部元素（前 25）===")
        for e in (v.get("inner") or [])[:25]:
            print("  <%s> title=%r aria=%r %r" % (e["tag"], e["title"], e["aria"], e["text"][:40]))
        print("\n=== Fiber 各层 pick ===")
        for item in out.get("②video节点Fiber") or []:
            for layer in item.get("layers") or []:
                picked = layer.get("picked") or {}
                if picked:
                    print("  up=%s type=%s %s" % (layer["up"], layer["type"], json.dumps(picked, ensure_ascii=False)[:300]))
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
