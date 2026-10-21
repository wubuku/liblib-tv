#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838 源站探针 v2：查清「**S83·镜2**」这个名字的**来源与构成**。

★ v1 的决定性发现（已确证）：
  「S83·镜2」是 `react-flow__node-video` 节点的**标题**（盒 232×133，
  文字「S83·镜2」＋「864 × 496」尺寸）⟹ ★★ **它不是「镜头名」**，
  而是一个**视频节点的标题**。
  ⟹ ★ **batch 837 README 里「源站用 S83·镜2 体系」那句是错的，必须更正**。

★ v2 要查清的三件事：
  ① 「S83」的 **S** 是什么、**83** 是什么（节点 id？序号？时间码？）
  ② 「镜2」的 **2** 是什么（第几个镜头？）
  ③ ★★ 视频节点标题的**生成规则**是什么（源站 bundle 里有没有这个模板）

★ 方法：
  - 读该节点的**全部 DOM 属性**（`data-*`、title、aria、样式）；
  - 读它在 React 上的 **props**（`__reactFiber$` / `__reactProps$`）⟹ 拿到节点数据；
  - 读页面上**其它**视频/图片节点的标题 ⟹ 看「S<数字>·镜<数字>」是不是**通例**；
  - 读「逐帧拉片」（shot-breakdown）节点里的**分镜条目** ⟹ 那才是源站的镜头，
    看它们**叫什么**。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_shotname838b.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(800)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(9_000)


def clean(page):
    page.evaluate("() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")


# ★ 所有画布节点的标题行（第一行文字）与节点类型
DUMP_TITLES = """() => {
  const out=[];
  for (const n of Array.from(document.querySelectorAll('.react-flow__node'))) {
    const r=n.getBoundingClientRect();
    const cls=(n.className||'').toString();
    const kind=(cls.match(/react-flow__node-([a-z0-9-]+)/)||[])[1]||'?';
    const data={};
    for (const [k,v] of Object.entries(n.dataset||{})) data[k]=String(v).slice(0,60);
    // 标题：第一个叶子 span 的文本
    let title=null;
    const spans=Array.from(n.querySelectorAll('span,div'));
    for (const s of spans) {
      if (s.childElementCount>0) continue;
      const r2=s.getBoundingClientRect();
      if (r2.width<=0||r2.height<=0) continue;
      const t=(s.textContent||'').trim();
      if (t && t.length<40) { title=t; break; }
    }
    out.push({kind, title, data, box:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
              fullText:(n.textContent||'').trim().slice(0,160)});
  }
  return out;
}"""

# ★ React props 里的节点数据
# ★ v1 整体 JSON.stringify 撞上循环引用（React context 的 Provider）⟹
#   ★ 修法：**定点提取**标量字段，不整体序列化 ⟹ 不可能撞环。
DUMP_PROPS = """() => {
  const scalar = (v, depth) => {
    if (v === null || v === undefined) return v;
    const t = typeof v;
    if (t === 'string') return v.length > 200 ? v.slice(0,200)+'…' : v;
    if (t === 'number' || t === 'boolean') return v;
    if (t === 'function') return '[fn]';
    if (Array.isArray(v)) return v.slice(0,12).map(x=>scalar(x, depth+1));
    if (t === 'object') {
      if (depth > 2) return '[obj]';
      const o={};
      for (const [k,x] of Object.entries(v).slice(0,60)) {
        if (k === 'Provider' || k === 'Consumer' || k === '_context' || k === '_currentValue') continue;
        try { o[k]=scalar(x, depth+1); } catch(e) { o[k]='[err]'; }
      }
      return o;
    }
    return String(v);
  };
  const res=[];
  for (const n of Array.from(document.querySelectorAll('.react-flow__node'))) {
    const cls=(n.className||'').toString();
    const kind=(cls.match(/react-flow__node-([a-z0-9-]+)/)||[])[1]||'?';
    if (kind!=='video' && kind!=='shot-breakdown' && kind!=='script-v2') continue;
    let payload=null;
    const key=Object.keys(n).find(k=>k.startsWith('__reactProps$'));
    if (key) {
      const p=n[key]||{};
      // 常见挂点：props.data / props.node / props 本身
      payload = {__propKeys:Object.keys(p).slice(0,40)};
      for (const src of ['data','node','nodeData','item','value','content']) {
        if (p[src] !== undefined) {
          try { payload[src]=scalar(p[src],0); } catch(e) { payload[src]='[err]'; }
        }
      }
      // 顶层标量也抓一遍
      for (const [k,v] of Object.entries(p).slice(0,40)) {
        if (typeof v==='string'||typeof v==='number'||typeof v==='boolean') payload[k]=v;
      }
    }
    res.push({kind, payload});
  }
  return res;
}"""

# ★ 「逐帧拉片」节点（shot-breakdown）里的所有可见文本 ⟹ 那是源站的镜头
DUMP_BREAKDOWN = """() => {
  const n=document.querySelector('.react-flow__node-shot-breakdown');
  if (!n) return null;
  const r=n.getBoundingClientRect();
  const vis=(e)=>{const b=e.getBoundingClientRect(); return b.width>0&&b.height>0;};
  const texts=[];
  for (const el of Array.from(n.querySelectorAll('span,div,button,a,p,li'))) {
    if (!vis(el) || el.childElementCount>0) continue;
    const t=(el.textContent||'').trim();
    if (!t || t.length>60) continue;
    const b=el.getBoundingClientRect();
    texts.push({text:t, x:Math.round(b.x-n.getBoundingClientRect().x),
                y:Math.round(b.y-n.getBoundingClientRect().y)});
  }
  return {box:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)], texts};
}"""


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

        out["①所有节点标题"] = page.evaluate(DUMP_TITLES)
        out["②节点React数据"] = page.evaluate(DUMP_PROPS)
        out["③逐帧拉片节点"] = page.evaluate(DUMP_BREAKDOWN)

        try:
            page.screenshot(path="/tmp/liblib_source_shotname838b.png")
            out["截图"] = "/tmp/liblib_source_shotname838b.png"
        except Exception:
            pass
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
        print("\n=== 各画布节点的标题 ===")
        for n in out.get("①所有节点标题") or []:
            print("  %-22s title=%-22r data=%s" % (n["kind"], n["title"], n["data"]))
        print("\n=== 逐帧拉片节点内的文本 ===")
        bd = out.get("③逐帧拉片节点") or {}
        for t in (bd.get("texts") or [])[:40]:
            print("  @(+%s,+%s) %r" % (t["x"], t["y"], t["text"]))
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
