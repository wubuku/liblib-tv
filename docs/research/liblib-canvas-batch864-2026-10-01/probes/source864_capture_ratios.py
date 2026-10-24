#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 864 源站探针：**截图／导出的比例档位**（batch 860 登记为「未取证」）。

## ★ 靶子

★ chunk 里 capture／record 命令的比例**取值集合**逐字是：

```js
t4 = new Set(["1:1","3:4","4:3","9:16","16:9","21:9"])      // ← 六个
"capture" === i ? (o.views = ro(e.views,"views",t5,t) ?? "current",
                   o.aspect_ratio = ro(e.aspect_ratio,"aspect_ratio",t4,t) ?? "16:9") : …
```

⟹ ⟹ **协议层**允许六档 ⟹ ⟹ 但**界面**上给几档？⟹ ⟹ 未知 ⟹ ⟹ **必须实测**。

★ clone 的截图/导出比例是**三档**（`DirectorAspectRatio = "16:9" | "9:16" | "1:1"`）
  ⟹ ⟹ 若源站界面是六档 ⟹ ⟹ clone **缺三档** ⟹ ⟹ 那才是真实缺口。

## ★ 本探针的难点（★ 已实测踩到）

① 源站会**间歇性**弹「Agent 已升级为 TV Director」模态（**A/B 实验**，
   body 里有 `xingliu_index_exp`）⟹ ⟹ 它会**挡住点击** ⟹ ⟹ 必须能关掉它；
② 那个模态的按钮**不一定是 `<button>`** ⟹ ⟹ 只按标签找会漏
   ⟹ ⟹ 改用「按叶子节点精确文本找 ＋ DOM `.click()`」；
③ ★ 模态**有时根本不出现** ⟹ ⟹ 「找不到」是**正常状态** ⟹ ⟹ 不能当成失败；
④ ⟹ ⟹ 故本探针带**重试循环**：失败就重载再试（最多 3 次）。

## ★ 副作用声明

★ 只**打开**截图面板并读取 DOM ⟹ ⟹ **绝不点**「确认截图」「生成」「导出」
  ⟹ ⟹ 不产生付费、不落盘、不触发生图。

## 输出
  raw/source-864-capture-ratios.json
"""
from __future__ import annotations

import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch864-2026-10-01"
RAW = BATCH / "raw"
COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 枚举导演台里所有**可交互元素**（找「截图」入口）
READ_BUTTONS = r"""()=>{
  const out=[];
  for(const el of document.querySelectorAll('button, [role="button"], a')){
    const t=(el.textContent||'').trim().slice(0,40);
    const al=el.getAttribute('aria-label')||'';
    const tt=el.getAttribute('title')||'';
    const r=el.getBoundingClientRect();
    if(r.width<2||r.height<2) continue;
    const cs=getComputedStyle(el);
    if(cs.visibility==='hidden'||cs.display==='none') continue;
    out.push({text:t, aria:al, title:tt,
              x:Math.round(r.x),y:Math.round(r.y),
              w:Math.round(r.width),h:Math.round(r.height)});
  }
  return out;
}"""

# ★ 读所有「像比例」的格子（只读 DOM，不点）
READ_RATIOS = r"""()=>{
  const re=/^\s*(\d{1,2})\s*[:：/]\s*(\d{1,2})\s*$/;
  const cells=[];
  for(const el of document.querySelectorAll('button, [role="button"], [role="radio"], label, div, span')){
    const t=(el.textContent||'').trim();
    if(!re.test(t) || t.length>12) continue;
    if(el.children.length) continue;          // ★ 只要叶子节点
    const r=el.getBoundingClientRect();
    if(r.width<2||r.height<2) continue;
    const cs=getComputedStyle(el);
    if(cs.visibility==='hidden'||cs.display==='none'||Number(cs.opacity)===0) continue;
    cells.push({text:t, x:Math.round(r.x), y:Math.round(r.y),
                w:Math.round(r.width), h:Math.round(r.height),
                tag:el.tagName, aria:el.getAttribute('aria-label'),
                pressed:el.getAttribute('aria-pressed'),
                checked:el.getAttribute('aria-checked'),
                cls:(el.getAttribute('class')||'').slice(0,90)});
  }
  const seen=new Set(); const out=[];
  for(const c of cells){
    const k=[c.text,c.x,c.y,c.w,c.h].join('|');
    if(seen.has(k)) continue; seen.add(k); out.push(c);
  }
  return {比例候选:out, 数量:out.length};
}"""

# ★ 读所有可见的浮层/对话框（看清面板标题与选项名）
READ_PANELS = r"""()=>{
  const out=[];
  for(const el of document.querySelectorAll('[role="dialog"], [aria-modal="true"]')){
    const r=el.getBoundingClientRect();
    if(r.width<4||r.height<4) continue;
    out.push({x:Math.round(r.x),y:Math.round(r.y),
              w:Math.round(r.width),h:Math.round(r.height),
              文本:(el.innerText||'').slice(0,1500)});
  }
  return out;
}"""


def dismiss_modals(page) -> list[str]:
    """★ 关掉源站**间歇性**弹出的模态。

    ★ 「找不到」是**正常状态**（A/B 实验，有时不弹）⟹ ⟹ 安静跳过。
    """
    hits = page.evaluate(
        """()=>{
          const want=['下次再说','知道了'];
          const out=[];
          for(const el of document.querySelectorAll('body *')){
            const t=(el.textContent||'').trim();
            if(!want.includes(t)) continue;
            if(el.children.length) continue;
            const r=el.getBoundingClientRect();
            if(r.width<4||r.height<4) continue;
            const cs=getComputedStyle(el);
            if(cs.visibility==='hidden'||cs.display==='none') continue;
            out.push(t);
          }
          return out;
        }"""
    )
    closed: list[str] = []
    for label in hits:
        try:
            ok = page.evaluate(
                """(label)=>{
                  const el=[...document.querySelectorAll('body *')]
                    .find(e=>(e.textContent||'').trim()===label
                             && e.children.length===0);
                  if(!el) return false;
                  el.click();
                  return true;
                }""",
                label,
            )
            if ok:
                page.wait_for_timeout(1200)
                closed.append(label)
        except Exception:  # noqa: BLE001
            pass
    return closed


def load_cookies(page) -> None:
    data = json.loads(COOKIE.read_text(encoding="utf-8"))
    cookies = data if isinstance(data, list) else data.get("cookies", [])
    page.context.add_cookies([
        {"name": c["name"], "value": c["value"], "domain": c["domain"],
         "path": c.get("path", "/")}
        for c in cookies if c.get("name")
    ])


def open_director(page, audit: dict) -> bool:
    """★ 打开导演台 ⟹ ⟹ 返回是否成功。

    ★ ★ 定位要**退级**：★ 有一次源站的画布上**根本没有**
      `.react-flow__node-director-console-3d` 这个节点（节点数 ＝ 0），
      可「打开导演台」按钮**就在页面的别处** ⟹ ⟹ 只用节点内定位会整轮失败
      ⟹ ⟹ 故：先试节点内，**退化**到全页文本匹配。
    """
    try:
        node = page.locator(".react-flow__node-director-console-3d").first
        if node.count() >= 1:
            try:
                node.hover(timeout=8_000)
                page.wait_for_timeout(600)
            except Exception:  # noqa: BLE001
                pass
        btn = page.locator("button:has-text('打开导演台')").first
        btn.click(timeout=15_000)
        page.wait_for_timeout(8_000)
    except Exception as e:  # noqa: BLE001
        audit.setdefault("打开失败", []).append(str(e)[:200])
        return False
    # ★ 判据：**真的打开了吗**？
    #   ⟹ ⟹ ★ 不能用「框上那枚开关」当标志 —— ★ 那枚开关**只在选了比例时**存在
    #   ⟹ ⟹ （第一版就是这么写的 ⟹ ⟹ 三次尝试全判成「未打开」⟹ ⟹ 白跑）
    #   ⟹ ⟹ 改用 rail 入口「选择画幅比例」在场来判（导演台一开就有）。
    ok = page.evaluate(
        """()=>{
          const hit=[...document.querySelectorAll('button, [role="button"]')]
            .some(b=>/选择画幅比例|全景图|添加角色/.test(
              (b.getAttribute('aria-label')||'')+' '+(b.textContent||'')));
          return hit;
        }"""
    )
    return bool(ok)


def main() -> int:
    audit: dict = {"batch": 864, "probe": "source864_capture_ratios",
                   "尝试": []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1920, "height": 1080})
            load_cookies(page)
            for attempt in range(1, 4):
                rec: dict = {"第几次": attempt}
                try:
                    page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
                    page.wait_for_timeout(6_000)
                    closed = dismiss_modals(page)
                    if closed:
                        rec["关掉的弹窗"] = closed
                    if not open_director(page, audit):
                        rec["导演台"] = "未打开"
                        audit["尝试"].append(rec)
                        continue
                    rec["导演台"] = "已打开"
                    buttons = page.evaluate(READ_BUTTONS)
                    rec["可交互元素数"] = len(buttons)
                    rec["截图入口候选"] = [
                        b for b in buttons
                        if any(k in (b["text"] + b["aria"] + b["title"])
                               for k in ("截图", "导出", "拍板", "合成", "成片"))
                    ]
                    rec["全部按钮"] = [
                        {"text": b["text"], "aria": b["aria"], "title": b["title"]}
                        for b in buttons
                    ][:200]
                    rec["打开截图面板前的比例"] = page.evaluate(READ_RATIOS)
                    rec["打开截图面板前的浮层"] = page.evaluate(READ_PANELS)

                    # ★ 点「截图」入口 ⟹ ⟹ **只打开面板** ⟹ ⟹ 不点确认
                    shot = page.locator(
                        "button:has-text('截图'), [aria-label*='截图']").first
                    if shot.count() >= 1:
                        shot.click(timeout=15_000)
                        page.wait_for_timeout(2_500)
                        rec["点截图后的比例"] = page.evaluate(READ_RATIOS)
                        rec["点截图后的浮层"] = page.evaluate(READ_PANELS)
                    else:
                        rec["说明"] = "★ 没找到「截图」按钮"
                    audit["尝试"].append(rec)
                    audit["成功轮次"] = attempt
                    break
                except Exception:
                    rec["异常"] = traceback.format_exc()[-800:]
                    audit["尝试"].append(rec)
        finally:
            browser.close()

    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "source-864-capture-ratios.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=1)[:6000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
