#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 834：源站探针 —— 把「使用教程」引导气泡的 **5 步**逐步读出来。

★ 为什么做这一批：clone 的引导气泡只有**第 1 步**（batch 556：文案 ＋ 「1/5」
  ＋ 跳过／下一步，点「下一步」直接收起）⟹ 而源站是 **5 步** ⟹ 步 2–5 的
  文案／指向／几何**从未被采样过**（batch 571 只拍了第 1 步的截图 58）。

★ 怎么找气泡本体（不靠猜选择器）：
  先在整页里找**自身文本形如 `n/5`** 的元素 ⟹ 再向上找**同时含「跳过」「下一步」
  两个按钮**的祖先 ⟹ 那就是气泡容器。
  ⟹ ★ 这样即使源站的 class 名与 clone 不同也能定位。

★ 副作用控制：
  - 引导气泡是**纯前端浮层** ⟹ 不改项目数据；
  - 唯一的状态是 localStorage 里那个「已跳过」标记 ⟹ 本探针**先清掉它**
    （只清匹配 coach/tutorial/guide/onboard/skip 的键）⟹ 结束时**不再复原**
    （它是「用户已看过教程」的用户态，留在「未看过」更接近默认）。
"""
import json
import pathlib
import re

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_coach834.json")
SHOTS = pathlib.Path("/tmp/liblib_source_coach834")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 找引导气泡：自身文本像「n/5」的元素 ⟹ 向上找到含「跳过」「下一步」的祖先
DUMP_COACH = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const all=Array.from(document.querySelectorAll('body *'));
  const stepEls=all.filter(e=>{
    if(e.childElementCount!==0) return false;
    const t=(e.textContent||'').trim();
    return /^\\d\\s*\\/\\s*\\d+$/.test(t);
  }).filter(vis);
  if(!stepEls.length) return {found:false, reason:'没找到「n/5」样式的步数元素'};
  const stepEl=stepEls[stepEls.length-1];
  // 向上找同时含「跳过」「下一步」的祖先
  let node=stepEl, host=null;
  for(let i=0;i<8 && node;i++){
    const btns=Array.from(node.querySelectorAll('button')).filter(vis)
      .map(b=>(b.textContent||'').trim());
    if(btns.some(t=>t.includes('跳过')) && btns.some(t=>t.includes('下一步'))){host=node;break;}
    node=node.parentElement;
  }
  if(!host) return {found:false, reason:'没找到含跳过/下一步的祖先', step:stepEl.textContent};
  const texts=Array.from(host.querySelectorAll('div,span,p')).filter(vis)
    .filter(e=>e.childElementCount===0)
    .map(e=>({t:(e.textContent||'').trim(), y:Math.round(e.getBoundingClientRect().y)}))
    .filter(x=>x.t);
  const btns=Array.from(host.querySelectorAll('button')).filter(vis)
    .map(b=>({t:(b.textContent||'').trim(), box:box(b), cls:String(b.className||'').slice(0,120)}));
  const cs=getComputedStyle(host);
  return {found:true, step:(stepEl.textContent||'').trim(),
          hostBox:box(host), texts, buttons:btns,
          hostClass:String(host.className||'').slice(0,200),
          position:cs.position, zIndex:cs.zIndex,
          parentText:(host.parentElement?(host.parentElement.textContent||'').trim().slice(0,200):'')};
}"""

# ★ 页面上有没有「被高亮的元素」（引导气泡通常会高亮一个目标）
DUMP_HIGHLIGHT = """()=>{
  const out=[];
  for(const e of document.querySelectorAll('body *')){
    const r=e.getBoundingClientRect();
    if(r.width<=0||r.height<=0) continue;
    const cs=getComputedStyle(e);
    const ring=cs.boxShadow||'';
    const outline=cs.outline||'';
    if(ring.includes('rgb') && ring.length>20 && !ring.includes('rgba(0, 0, 0, 0)')){
      out.push({tag:e.tagName, cls:String(e.className||'').slice(0,90),
                box:{x:Math.round(r.x),y:Math.round(r.y),
                     w:Math.round(r.width),h:Math.round(r.height)},
                boxShadow:ring.slice(0,90), outline:outline.slice(0,60)});
    }
  }
  return out.slice(0,14);
}"""


def open_desk(page):
    card = page.locator(".react-flow__node-director-console-3d").first
    card.hover()
    page.wait_for_timeout(800)
    page.locator(
        ".react-flow__node-director-console-3d button:has-text('打开导演台')").first.click()
    page.wait_for_timeout(9_000)


def main():
    cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
    out = {}
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
        page.wait_for_timeout(8_000)

        # ★ 先清掉「已看过教程」的用户态标记（只清匹配这些词的键）
        cleared = page.evaluate("""()=>{
          const out=[];
          for(const k of Object.keys(localStorage)){
            if(/coach|tutorial|guide|onboard|skip/i.test(k)){
              out.push(k); localStorage.removeItem(k);
            }
          }
          return out;
        }""")
        out["清掉的 localStorage 键"] = cleared
        page.reload(wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(10_000)
        open_desk(page)
        SHOTS.mkdir(exist_ok=True)

        # ★★ 关键：**先打开时间轴**，引导气泡才会出现（它锚在时间轴上）
        #   ⟹ 第一版探针没开时间轴 ⟹ 全页找不到「n/5」⟹ 误以为「源站没有引导」。
        #   （diag834b.py 的元素签名差分证明了：开时间轴那一刻，页面多出两枚
        #     `h-7 rounded-lg bg-transparent px-3` / `bg-white/10` 的按钮。）
        try:
            page.locator("button[aria-label='动画时间轴']").first.click()
            page.wait_for_timeout(3_000)
        except Exception as exc:  # noqa: BLE001
            out["★开时间轴异常"] = repr(exc)[:200]

        out["①开时间轴后"] = page.evaluate(DUMP_COACH)
        page.screenshot(path=str(SHOTS / "834_step_open.png"))

        # ★ 走「帮助 → 使用教程」
        try:
            help_btn = page.locator("button[aria-label='帮助']").first
            help_btn.click()
            page.wait_for_timeout(1_200)
            tutorial = page.locator("[role='menuitem']").filter(
                has_text="使用教程").first
            tutorial.click()
            page.wait_for_timeout(2_500)
        except Exception as exc:  # noqa: BLE001
            out["★点使用教程异常"] = repr(exc)[:300]
        out["②点使用教程后"] = page.evaluate(DUMP_COACH)
        page.screenshot(path=str(SHOTS / "834_step_tutorial.png"))

        # ★ 逐点「下一步」，把 5 步全读出来
        # ★★ 注意：这趟**只能跑一次** —— batch 572 实测「气泡收起状态跨重载持久」
        #   （很可能是**服务端**的用户偏好）⟹ 走完 5 步之后这个帐号可能再也看不到它
        #   ⟹ 所以**一趟必须采全**（含最后一枚按钮的文案）。
        steps = []
        for i in range(6):
            coach = page.evaluate(DUMP_COACH)
            hl = page.evaluate(DUMP_HIGHLIGHT)
            steps.append({"轮次": i, "coach": coach, "高亮": hl})
            page.screenshot(path=str(SHOTS / ("834_step_%d.png" % i)))
            if not coach.get("found"):
                break
            nxt = page.get_by_role("button", name="下一步", exact=True)
            if not nxt.count():
                # ★ 最后一枚按钮的文案不是「下一步」⟹ 记下它是什么
                out["★末枚按钮文案"] = [b.get("t") for b in coach.get("buttons") or []]
                break
            nxt.first.click()
            page.wait_for_timeout(1_500)
        out["③逐步"] = steps
        out["④走完后·还在吗"] = page.evaluate(DUMP_COACH)
        out["④走完后·存储"] = page.evaluate("""()=>{
          const ls={}, ss={};
          for(const k of Object.keys(localStorage)) ls[k]=String(localStorage.getItem(k)).slice(0,80);
          for(const k of Object.keys(sessionStorage)) ss[k]=String(sessionStorage.getItem(k)).slice(0,80);
          return {localStorage:ls, sessionStorage:ss};
        }""")
        ctx.close()
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：", OUT)
    for s in out.get("③逐步") or []:
        c = s["coach"]
        if c.get("found"):
            txt = [x["t"] for x in c["texts"] if x["t"] not in ("跳过", "下一步")]
            print("  轮%s 步数=%s 盒=%s 文本=%s"
                  % (s["轮次"], c["step"], c["hostBox"], txt[:3]))
        else:
            print("  轮%s 没找到气泡：%s" % (s["轮次"], c.get("reason")))


if __name__ == "__main__":
    main()
