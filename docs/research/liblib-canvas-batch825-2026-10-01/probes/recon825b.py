#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 825 源站取证②：打开**源站的导演台**，看它**懒加载**了哪些 chunk，
并在那些 chunk 里搜「跟随横幅」。

★ 为什么要这一轮：
  我在画布页抓的 160 个 JS 里，跟随横幅组件**只有一个调用点**（协作跟随），
  ★★ 而橙色 #E46525 在整个 bundle 里**一个字节都没有** ⟹
  ★★ batch 605 记录的「导演台里机位跟随时有橙色横幅」⟹
  ★★ **要么** 那条横幅属于协作功能（605 归因错了），
  ★★ **要么** 导演台的代码是**懒加载**的 chunk，我还没抓到 ⟹ ★ 这一轮堵这个漏。

★ 这一轮做三件事：
  ① 点开画布上的「导演台」节点 ⟹ **记录新加载的 JS chunk**（对比点击前后）
  ② 在新 chunk 里搜横幅特征串（`rounded-b-xl` / `z-[305]` / `正在跟随` / `E46525`）
  ③ 记录导演台打开后的 DOM：有没有跟随横幅、有没有机位跟随相关的控件
"""
import hashlib
import json
import pathlib
import re
import time

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
DEST = pathlib.Path("/tmp/liblib_srcjs")
DESK = pathlib.Path("/tmp/liblib_srcjs_desk")
DESK.mkdir(parents=True, exist_ok=True)
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 导演台打开后的 DOM 读数（只读，不动任何状态）
DESK_DOM = """()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    if(r.width===0&&r.height===0)return false;
    const cs=getComputedStyle(e);
    return cs.visibility!=='hidden'&&cs.display!=='none'
      && Number(cs.opacity||'1')>0;};
  const out={};
  out['url']=location.href;
  out['title']=document.title;
  out['节点数']=document.querySelectorAll('.react-flow__node').length;
  out['可见节点标题']=Array.from(document.querySelectorAll('.react-flow__node'))
    .map(e=>(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,24))
    .filter(Boolean).slice(0,30);
  out['含导演台的节点']=Array.from(document.querySelectorAll('.react-flow__node'))
    .map(e=>({text:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,30),
              data:Array.from(e.attributes).filter(a=>a.name.startsWith('data-'))
                .map(a=>a.name+'='+a.value).join(' ').slice(0,120)}))
    .filter(x=>/导演台|director/i.test(x.text+' '+x.data));
  // ★ 跟随横幅（不管它叫什么 testid，按**结构**找：顶部固定 + 圆角下沿 + 白胶囊）
  const cands=[];
  for(const e of document.querySelectorAll('div,span,button')){
    if(!vis(e))continue;
    const cs=getComputedStyle(e);
    if(cs.position!=='fixed')continue;
    const r=e.getBoundingClientRect();
    if(r.y>60||r.height>60||r.width<80)continue;
    const t=(e.textContent||'').trim().replace(/\\s+/g,' ');
    if(!/跟随|ESC/.test(t))continue;
    cands.push({tag:e.tagName,text:t.slice(0,40),
      testid:e.getAttribute('data-testid')||'',
      cls:(e.getAttribute('class')||'').slice(0,120),
      rect:{x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)},
      bg:cs.backgroundColor, pe:cs.pointerEvents, z:cs.zIndex});
  }
  out['顶部跟随横幅候选']=cands;
  // ★ 按钮/控件普查：找「跟随目标」「不跟随」这类
  const ctrls=[];
  for(const e of document.querySelectorAll('button,select,input,[role=button],[role=combobox]')){
    if(!vis(e))continue;
    const t=((e.getAttribute('aria-label')||'')+' '+(e.textContent||'')).trim()
      .replace(/\\s+/g,' ').slice(0,30);
    if(!t)continue;
    if(/跟随|机位|取消ESC|ESC/.test(t))
      ctrls.push({tag:e.tagName,text:t,
        testid:e.getAttribute('data-testid')||'',
        aria:e.getAttribute('aria-label')||''});
  }
  out['跟随相关控件']=ctrls.slice(0,40);
  return out;}"""

cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
seen = {}
new_chunks = []

with sync_playwright() as pw:
    br = pw.chromium.launch(headless=True)
    ctx = br.new_context(viewport={"width": 1600, "height": 950},
                          user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X "
                                      "10_15_7) AppleWebKit/537.36 (KHTML, like "
                                      "Gecko) Chrome/134.0.0.0 Safari/537.36"),
                          locale="zh-CN")
    ctx.add_cookies([{"name": c["name"], "value": c["value"],
                      "domain": c["domain"], "path": c.get("path", "/")}
                     for c in cookies])
    pg = ctx.new_page()

    def on_response(resp):
        try:
            ct = resp.headers.get("content-type", "")
            if "javascript" not in ct and "text/javascript" not in ct:
                return
            body = resp.body()
        except Exception:                                         # noqa: BLE001
            return
        h = hashlib.sha1(resp.url.encode("utf-8")).hexdigest()[:10]
        name = "%s_%s.js" % (h, re.sub(r"[^A-Za-z0-9._-]", "_",
                                       resp.url.rsplit("/", 1)[-1])[:60])
        if name in seen:
            return
        seen[name] = resp.url
        (DESK / name).write_bytes(body)
        new_chunks.append({"file": name, "url": resp.url, "bytes": len(body)})

    pg.on("response", on_response)
    pg.goto(URL, wait_until="domcontentloaded", timeout=90_000)
    pg.wait_for_timeout(10_000)
    for label in ("下次再说",):
        el = pg.query_selector("text=%s" % label)
        if el:
            el.click()
            pg.wait_for_timeout(900)
            break

    before = len(seen)
    nodes = pg.evaluate("""()=>Array.from(document.querySelectorAll('.react-flow__node'))
      .map((e,i)=>{const r=e.getBoundingClientRect();
        return {i, text:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,30),
                x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2)};})""")
    print("画布节点:", json.dumps(nodes, ensure_ascii=False)[:600])

    # ★ 点那个「导演台」节点（中心点，真实鼠标）
    target = None
    for n in nodes:
        if "导演台" in n["text"]:
            target = n
            break
    print("目标节点:", json.dumps(target, ensure_ascii=False))
    if target:
        pg.mouse.click(target["x"], target["y"])
        pg.wait_for_timeout(6000)

    dom = pg.evaluate(DESK_DOM)
    (DESK / "_desk-dom.json").write_text(
        json.dumps(dom, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n=== 导演台 DOM ===")
    print(json.dumps(dom, ensure_ascii=False, indent=1)[:3000])
    print("\n=== 新加载的 chunk：%d 个（点击前 %d）===" % (len(seen), before))
    br.close()

(DESK / "_index.json").write_text(
    json.dumps(new_chunks, ensure_ascii=False, indent=1), encoding="utf-8")
print("chunk 落盘 →", DESK)

print("\n=== 在**全部** chunk（含导演台新加载的）里搜横幅特征 ===")
alldir = sorted(set(list(DEST.glob("*.js")) + list(DESK.glob("*.js"))))
for needle in ["rounded-b-xl", "z-[305]", "正在跟随", "E46525", "228, 101, 37",
               "collab-follow-banner", "取消ESC"]:
    hits = []
    for f in alldir:
        t = f.read_text(encoding="utf-8", errors="replace")
        if needle in t:
            hits.append((f.name, t.count(needle)))
    print("  %-20s %s" % (needle, hits if hits else "★无★"))
