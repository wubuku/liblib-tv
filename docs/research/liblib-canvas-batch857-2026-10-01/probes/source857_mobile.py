#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 857 源站探针（**移动端 390×844**）：「群众阵列（crowd）」的入口
**在移动端还能不能到达**。

## ★ 为什么必须单独取证

batch 857 的 clone 整改把**视口工具栏那枚「添加群众阵列」按钮删了**
（源站没有那个入口 —— 自指判据：全页 `aria-label == 添加群众阵列` 只有 1 个）。

★ 但 clone 的 **rail 在 <899px 是 `hidden`** ⟹ ⟹ 移动端「添加角色」这一路
**在 clone 里根本不存在** ⟹ ⟹ 如果源站移动端**有**可达的 crowd 入口，
那么 clone 删掉视口那枚按钮就**同时删掉了移动端的唯一入口**
⟹ ⟹ 那不是「对齐源站」，那是**制造了移动端的功能缺口**。

⟹ ⟹ 所以这里要单独量源站在 390×844 下：
① 左侧 aside / rail 在不在、可见不可见
② `button[aria-haspopup="dialog"]`（crowd 入口的**结构特征**）有没有
③ 它可不可点（点它之后对话框出不出现）
④ 场景树在移动端是什么样（是否也换成面板）

## ★ 判据纪律
- 用**结构**（`button[aria-haspopup="dialog"]`）找 crowd 入口 ⟹ 不手打中文。
- 「元素在不在」与「点得动吗」**分别取证** ⟹ 「读不到某东西」当证据时，
  必须有一条「读得到同类东西」的阳性对照（这里就是 ①的 rail 按钮列表）。

## 输出
  raw/source-857-mobile.json
  images/857src_mobile-*.png
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch857-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"
COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 所有可见的 button（带 aria/文案），用来回答「移动端有没有任何入口」
READ_BUTTONS = r"""()=>{
  const out=[];
  document.querySelectorAll('button').forEach(b=>{
    const r=b.getBoundingClientRect();
    const vis = !!(r.width>0 && r.height>0);
    out.push({vis, x:Math.round(r.x), y:Math.round(r.y),
      w:Math.round(r.width), h:Math.round(r.height),
      aria:b.getAttribute('aria-label')||'',
      haspopup:b.getAttribute('aria-haspopup')||'',
      text:(b.textContent||'').trim().slice(0,24)});
  });
  return out;
}"""

READ_ASIDE = r"""()=>{
  const out=[];
  document.querySelectorAll('aside').forEach(a=>{
    const r=a.getBoundingClientRect();
    const cs=getComputedStyle(a);
    out.push({x:Math.round(r.x), y:Math.round(r.y),
      w:Math.round(r.width), h:Math.round(r.height),
      display:cs.display, visibility:cs.visibility,
      aria:a.getAttribute('aria-label')||''});
  });
  return out;
}"""

READ_DIALOGS = r"""()=>{
  const out=[];
  document.querySelectorAll('[role="dialog"]').forEach(d=>{
    const r=d.getBoundingClientRect();
    out.push({aria:d.getAttribute('aria-label')||'',
      vis:!!(r.width>0&&r.height>0),
      x:Math.round(r.x), y:Math.round(r.y),
      w:Math.round(r.width), h:Math.round(r.height),
      n:d.querySelectorAll('input[type="number"]').length});
  });
  return out;
}"""


def main() -> int:
    out = {"批次": "batch 857", "探针": "source857_mobile",
           "视口": {"width": 390, "height": 844},
           "问题": "源站在移动端还有没有可达的 crowd 入口"}
    RAW.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)
    try:
        cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 390, "height": 844},
                                 locale="zh-CN", is_mobile=False)
            ctx.add_cookies([{"name": c["name"], "value": c["value"],
                              "domain": c["domain"], "path": c.get("path", "/")}
                             for c in cookies])
            pg = ctx.new_page()
            pg.set_default_timeout(20_000)
            pg.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            pg.wait_for_timeout(12_000)
            el = pg.query_selector("text=下次再说")
            if el:
                # ★ 390px 下这个提示可能在视口外 ⟹ ⟹ 用 force 点（点不到就跳过，
                #   后面有「导演台开着了吗」的自读数）
                try:
                    el.click(timeout=4000, force=True)
                    pg.wait_for_timeout(900)
                except Exception:
                    pass

            # 打开导演台（源站：hover 脚本节点 ⟹ 出现「进入导演台」）
            node = pg.query_selector(".react-flow__node-script-execution")
            if node:
                node.scroll_into_view_if_needed()
                pg.wait_for_timeout(400)
                node.hover()
                pg.wait_for_timeout(600)
            opener = pg.query_selector("[data-open-director]")
            if opener:
                opener.click()
                pg.wait_for_timeout(9000)
            out["①导演台开着了"] = bool(pg.query_selector("[data-director-practice-escape]")
                                       or pg.query_selector("[data-open-director]"))

            aside = pg.evaluate(READ_ASIDE)
            out["②aside"] = aside
            buttons = pg.evaluate(READ_BUTTONS)
            out["③可见button数"] = len([b for b in buttons if b["vis"]])
            out["③可见button（前30）"] = [b for b in buttons if b["vis"]][:30]
            out["③aria-haspopup=dialog的button"] = [
                b for b in buttons if b["haspopup"] == "dialog"
            ]
            out["③左侧窄栏里的button（x<70）"] = [
                b for b in buttons if b["vis"] and b["x"] < 70
            ]

            # ★ 尝试点那个 crowd 入口（结构特征），看对话框出不出来
            entry = None
            for b in out["③aria-haspopup=dialog的button"]:
                if b["vis"]:
                    entry = b
                    break
            out["④准备点的入口"] = entry
            if entry:
                try:
                    pg.mouse.click(entry["x"] + entry["w"] / 2,
                                   entry["y"] + entry["h"] / 2)
                    pg.wait_for_timeout(1200)
                    out["⑤点后dialogs"] = pg.evaluate(READ_DIALOGS)
                    pg.screenshot(path=str(SHOTS / "857src_mobile-after-click.png"))
                except Exception as exc:  # noqa: BLE001
                    out["⑤点入口异常"] = str(exc)[:300]
            pg.screenshot(path=str(SHOTS / "857src_mobile-director.png"))
    except Exception:
        out["★异常"] = traceback.format_exc()[-2500:]
    p = RAW / "source-857-mobile.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if "★异常" not in out else 1


if __name__ == "__main__":
    sys.exit(main())
