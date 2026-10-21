#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 838 源站探针 v1：查清「**S83·镜2**」到底是什么。

★ 背景：batch 837 的整页扫描读到了「S83·镜2」（x 127, y 104，class 含
  `cursor-text pointer-events-auto`）⟹ 当时把它记成「源站的镜头名形态」。
  ★★ 但那个 class 更像**画布上可编辑的文本元素**，不像面板里的系统命名 ⟹
  ★★ **必须先排除替代解释**：「S83·镜2」是**用户自己放在画布上的内容**，
     而不是系统的镜头命名规则。

★ 本探针要回答的四个问题（缺一不可）：
  ① 「S83·镜2」的 **DOM 祖先链**是什么 ⟹ 它在画布节点里还是在面板里？
  ② 它**是不是可编辑的画布文本**（contentEditable / 画布节点容器）？
  ③ ★★ **区分实验**：在源站**新建一台机位** ⟹ 画布上是否**新出现**一个
     「S<数字>·镜<数字>」文本？
     ⟹ **出现了** ⟹ 它**是**系统命名规则（且能推出编号含义）；
     ⟹ **没出现** ⟹ 它**是静态的用户内容** ⟹ batch 837 那条「源站用
        S83·镜2 体系」的说法**不成立** ⟹ 必须更正。
  ④ 源站的**镜头**（系统意义上的分镜）到底叫什么、叫什么形态 ⟹
     扫**所有** `S<数字>·镜<数字>` 形态的文本 ＋ 镜头相关的 UI 位置。

★ 纪律：
  - **以进站基线为准** ⟹ 不删不属于本批的对象；新建的机位**收尾要复原**；
  - 记录**每一步的前后对比**，不靠单点观察下结论；
  - 只读源站，不做付费/生图操作。
"""
import json
import pathlib
import re
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_shotname838.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 匹配「S<数字>·镜<数字>」形态（也放宽成「S<数字>·<任意>」）
SHOT_RE = re.compile(r"^S\d+[·.・]")

# ★ 扫所有叶子文本里形如「S..」的
DUMP_SHOTLIKE = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0;};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('span,div,button,a,p,li,h1,h2,h3,input'))) {
    if (!vis(el)) continue;
    if (el.childElementCount > 0) continue;
    const t=(el.textContent||el.value||'').trim();
    if (!t || t.length > 40) continue;
    if (!/^S\\d+/.test(t)) continue;
    const r=el.getBoundingClientRect();
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y),
              w:Math.round(r.width), h:Math.round(r.height),
              cls:(el.className||'').toString().slice(0,120), tag:el.tagName});
  }
  return out.sort((a,b)=> (a.y-b.y) || (a.x-b.x));
}"""

# ★ 目标文本的祖先链 + 可编辑性
DUMP_ANCESTORS = """(target) => {
  const vis=(e)=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;};
  const all = Array.from(document.querySelectorAll('span,div,p'));
  const el = all.find(e => vis(e) && (e.textContent||'').trim() === target);
  if (!el) return null;
  const chain=[];
  let p = el;
  for (let i=0;i<8 && p;i++) {
    const r=p.getBoundingClientRect();
    chain.push({
      tag:p.tagName,
      cls:(p.className||'').toString().slice(0,110),
      dataKeys:Object.keys(p.dataset||{}),
      contentEditable: p.getAttribute('contenteditable'),
      text:(p.textContent||'').trim().slice(0,40),
      box:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
    });
    p = p.parentElement;
  }
  return chain;
}"""

# ★ 场景树（左侧）里的可见叶子文本 ⟹ 用来取机位名
DUMP_TREE = """() => {
  const vis=(e)=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;};
  const out=[];
  for (const el of Array.from(document.querySelectorAll('span,div,button,a'))) {
    if (!vis(el) || el.childElementCount > 0) continue;
    const r=el.getBoundingClientRect();
    if (r.x > 340) continue;             // ★ 只要左栏
    const t=(el.textContent||'').trim();
    if (!t || t.length > 30) continue;
    out.push({text:t, x:Math.round(r.x), y:Math.round(r.y)});
  }
  return out;
}"""

# ★ 视口内的 react-flow 节点（画布上的对象）⟹ 判断「S83·镜2」是不是画布节点
DUMP_NODES = """() => {
  const out=[];
  for (const n of Array.from(document.querySelectorAll('.react-flow__node'))) {
    const r=n.getBoundingClientRect();
    const cls=(n.className||'').toString();
    out.push({cls:cls.slice(0,140), box:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
              text:(n.textContent||'').trim().slice(0,60)});
  }
  return out;
}"""

# ★ 点画布上那个「S83·镜2」看它会变成什么（可编辑？弹面板？）
CLICK_TARGET = """(target) => {
  const vis=(e)=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;};
  const all = Array.from(document.querySelectorAll('span,div,p'));
  const el = all.find(e => vis(e) && (e.textContent||'').trim() === target);
  if (!el) return {ok:false, why:'没找到目标'};
  const r=el.getBoundingClientRect();
  return {ok:true, x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2),
          tag:el.tagName, cls:(el.className||'').toString().slice(0,120)};
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

        # ① 基线：所有「S..」形态文本
        out["①基线_ShotLike文本"] = page.evaluate(DUMP_SHOTLIKE)
        out["①基线_ShotLike数量"] = len(out["①基线_ShotLike文本"])
        out["①基线_画布节点"] = page.evaluate(DUMP_NODES)
        out["①基线_左栏文本"] = page.evaluate(DUMP_TREE)

        target = None
        for d in out["①基线_ShotLike文本"]:
            if "镜" in d["text"]:
                target = d["text"]
                break
        out["①目标文本"] = target

        # ② 祖先链 + 可编辑性
        if target:
            out["②目标祖先链"] = page.evaluate(DUMP_ANCESTORS, target)

        # ③ ★★ 区分实验：新建一台机位，看是否新出现「S..」形态文本
        out["③新建前_ShotLike集合"] = sorted(
            d["text"] for d in out["①基线_ShotLike文本"])
        # 点 rail 的「机位」入口 ⟹ 找「新增机位」
        try:
            page.locator("[aria-label='机位']").first.click()
            page.wait_for_timeout(1_200)
            clean(page)
            out["③机位面板_可见文本"] = page.evaluate("""() => {
              const vis=(e)=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;};
              const out=[];
              for (const el of Array.from(document.querySelectorAll('span,div,button,a'))) {
                if (!vis(el) || el.childElementCount > 0) continue;
                const r=el.getBoundingClientRect();
                if (r.x < 100) continue;
                const t=(el.textContent||'').trim();
                if (!t || t.length > 30) continue;
                out.push({text:t, x:Math.round(r.x), y:Math.round(r.y)});
              }
              return out;
            }""")
        except Exception as exc:
            out["③机位面板_异常"] = str(exc)

        try:
            add = page.get_by_text("新增机位", exact=False).first
            add.click()
            page.wait_for_timeout(2_000)
            clean(page)
            out["③新建后_ShotLike文本"] = page.evaluate(DUMP_SHOTLIKE)
            after = sorted(d["text"] for d in out["③新建后_ShotLike文本"])
            before = set(out["③新建前_ShotLike集合"])
            out["③新建后_ShotLike集合"] = after
            out["③★新出现的S形态文本"] = [t for t in after if t not in before]
            out["③★是否新出现S形态文本"] = bool(out["③★新出现的S形态文本"])
        except Exception as exc:
            out["③新建_异常"] = str(exc)

        out["③新建后_左栏文本"] = page.evaluate(DUMP_TREE)
        out["③新建后_画布节点"] = page.evaluate(DUMP_NODES)

        try:
            page.screenshot(path="/tmp/liblib_source_shotname838.png")
            out["截图"] = "/tmp/liblib_source_shotname838.png"
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
        print("\n=== 基线「S..」形态文本 ===")
        for d in out.get("①基线_ShotLike文本") or []:
            print("  @(%s,%s) %r  <%s> %s" % (d["x"], d["y"], d["text"], d["tag"], d["cls"][:70]))
        print("\n=== 目标祖先链 ===")
        for c in out.get("②目标祖先链") or []:
            print("  <%s> data=%s ce=%s box=%s %r" %
                  (c["tag"], c["dataKeys"], c["contentEditable"], c["box"], c["text"][:40]))
        print("\n=== 区分实验 ===")
        print("  新出现的 S 形态文本：", out.get("③★新出现的S形态文本"))
        print("  是否新出现：", out.get("③★是否新出现S形态文本"))
        if out.get("异常"):
            print("异常：", out["异常"])


if __name__ == "__main__":
    main()
