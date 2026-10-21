#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838 源站探针 v6：读源站导演台**时间轴**里显示的轨道名。

★ 前五趟已确证的三件事实：
  ① 「S83·镜2」是**用户上传的 mp4 文件名**（服务端 `alt: "S83·镜2.mp4"`）⟹
     ★★ **不是**任何系统命名规则 ⟹ batch 837 README 那句「源站用 S83·镜2 体系」**是错的**。
  ② 源站导演台的权威数据（`compositionData`）：
     `cameras[]`  label = 「机位1」/「机位2」；
     `animation.cameraTracks[]` = **一条**，name = 「**主机位**」，targetId = `director-main-camera`；
     `characters[]` label = 「角色A」；
     `animation.characterTracks[]` = **空**。
  ③ 源站**没有「镜头」实体** ⟹ clone 的 `shots[]` 是**借自 StoryAI 上游**的分层设计
     （见 batch 96 PLAN.md），**不是**源站事实。

★ 本趟要读的唯一问题：**源站时间轴上，相机轨道那一行到底显示什么文字？**
  ⟹ 由 DOM 读数决定，不由 compositionData 的 `name` 字段**推测**
     （★ 存储的名字 ≠ 显示的名字 ⟹ 两者要分开读）。

★ 纪律：只读；不点任何会产生副作用的按钮；记录**每个读数的来源区域**。
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_trackname838.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 下半屏所有可见叶子文本（时间轴在视口下方）
DUMP_LOWER = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0 && getComputedStyle(e).visibility!=='hidden';};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('span,div,button,a,p,li'))) {
    if (!vis(el) || el.childElementCount>0) continue;
    const r=el.getBoundingClientRect();
    if (r.y < 620) continue;
    const t=(el.textContent||'').trim();
    if (!t || t.length>50) continue;
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height),
              cls:(el.className||'').toString().slice(0,90), tag:el.tagName});
  }
  return out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
}"""

# ★ 找含「主机位」的元素的祖先链 ⟹ 它属于哪块 UI
DUMP_HOSTCHAIN = """(target) => {
  const vis=(e)=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;};
  const all=Array.from(document.querySelectorAll('span,div,button,a,p'));
  const el=all.find(e => vis(e) && (e.textContent||'').trim().indexOf(target)>=0
                          && (e.textContent||'').trim().length < target.length+4);
  if (!el) return null;
  const chain=[];
  let p=el;
  for (let i=0;i<8&&p;i++){
    const r=p.getBoundingClientRect();
    chain.push({tag:p.tagName, cls:(p.className||'').toString().slice(0,110),
                dataKeys:Object.keys(p.dataset||{}),
                text:(p.textContent||'').trim().slice(0,50),
                box:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)]});
    p=p.parentElement;
  }
  return chain;
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
        out["①下半屏所有可见叶子文本"] = page.evaluate(DUMP_LOWER)
        out["②含主机位的祖先链"] = page.evaluate(DUMP_HOSTCHAIN, "主机位")
        out["③含机位1的祖先链"] = page.evaluate(DUMP_HOSTCHAIN, "机位1")
        try:
            page.screenshot(path="/tmp/liblib_source_trackname838.png")
            out["截图"] = "/tmp/liblib_source_trackname838.png"
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
        print("\n=== 下半屏可见叶子文本（前 60）===")
        for d in (out.get("①下半屏所有可见叶子文本") or [])[:60]:
            print("  @(%s,%s) %r <%s> %s" % (d["x"], d["y"], d["text"], d["tag"], d["cls"][:60]))
        for key in ("②含主机位的祖先链", "③含机位1的祖先链"):
            print("\n=== %s ===" % key)
            for c in out.get(key) or []:
                print("  <%s> data=%s box=%s %r" % (c["tag"], c["dataKeys"], c["box"], c["text"][:44]))
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
