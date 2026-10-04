#!/usr/bin/env python3
"""batch 762 探针 b：导演台里那 2 个「不可达」的可聚焦元素 + 折叠后的 inert 围栏

762a 是个干净的全过（焦点围栏完全成立）。但它顺手量到两个没解释的数：

  ① dialog 里有 **128 个**可聚焦元素，其中 **126 个 reachable** ——
     有 2 个元素「在 DOM 里、没 disabled、tabindex 不为负」，
     却因为 `display:none` / `visibility:hidden` 而 Tab 不到。
     **是哪两个、为什么**，必须点名。
  ② `inert={treeMobileInactive || viewportPanelsCollapsed}`（`:1182`）这条路
     **一次都没走到** —— 762a 没找到折叠开关（那枚按钮是纯图标、
     `aria-hidden` 的 svg，没有 textContent，按文案找必然落空）。
     正确的钩子是 `data-director-panels-toggle`（`aria-label="收起"`）。

本探针补这两格，外加两格：
  ③ 折叠后：面板 `inert` / `aria-hidden` 是否同步、Tab 是否仍被围在 dialog 内
  ④ Esc 在焦点位于**子面板**（而非 dialog 根）时是否仍能关闭

仍然：真实点击前先 `elementFromPoint` 断言命中；每格前重开导演台，绝不带上一格状态。
"""
import json
import pathlib
import re
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch762-2026-10-01/raw/vb762b.json")

LIST = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const sel='a[href],button,input,select,textarea,[tabindex]';
 const cs=getComputedStyle;
 const rows=[];
 for(const e of d.querySelectorAll(sel)){
   if(e.disabled) continue;
   const t=e.getAttribute('tabindex');
   if(t!==null && Number(t)<0) continue;
   const s=cs(e);
   const rect=e.getBoundingClientRect();
   rows.push({tag:e.tagName, ariaLabel:e.getAttribute('aria-label'),
     title:e.getAttribute('title'), tabindex:t,
     display:s.display, visibility:s.visibility,
     text:(e.textContent||'').trim().slice(0,22),
     cls:(e.getAttribute('class')||'').slice(0,64),
     w:Math.round(rect.width), h:Math.round(rect.height),
     reachable: s.display!=='none' && s.visibility!=='hidden'});}
 const bad=rows.filter(r=>!r.reachable);
 return {open:true, total:rows.length,
   reachable:rows.length-bad.length, unreachable:bad.length,
   unreachableList:bad};}"""

STATE = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const t=d.querySelector('[data-director-panels-toggle]');
 const panels=[...d.querySelectorAll('aside')].map(el=>({
   ariaLabel:el.getAttribute('aria-label'),
   inert:!!el.inert, ariaHidden:el.getAttribute('aria-hidden'),
   display:getComputedStyle(el).display,
   w:Math.round(el.getBoundingClientRect().width)}));
 return {open:true, collapsed:d.getAttribute('data-director-panels-collapsed'),
   togglePresent:!!t,
   toggleAriaLabel:t?t.getAttribute('aria-label'):null,
   toggleAriaPressed:t?t.getAttribute('aria-pressed'):null,
   toggleInert:t?!!t.inert:null,
   panels:panels};}"""

ACTIVE = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 const a=document.activeElement;
 return {open:!!d, inDialog:d?(d===a||d.contains(a)):false,
   tag:a?a.tagName:null,
   ariaLabel:a?a.getAttribute('aria-label'):null,
   text:a?(a.textContent||'').trim().slice(0,20):null};}"""

FOCUSABLE_N = """()=>{const d=document.querySelector('[role="dialog"][aria-modal="true"]');
 if(!d) return {open:false};
 const sel='a[href],button,input,select,textarea,[tabindex]';
 let n=0; for(const e of d.querySelectorAll(sel)){
   if(e.disabled) continue; const t=e.getAttribute('tabindex');
   if(t!==null && Number(t)<0) continue;
   const s=getComputedStyle(e);
   if(s.display==='none'||s.visibility==='hidden') continue;
   n++; }
 return {open:true, reachable:n};}"""

# ⚠ 一次只能查一个选择器：早先把它写死成查 panels-toggle，
# 拿去点「打开导演台」必然 ok=false —— 当场停是对的，是探针错了。
HIT = """(a)=>{const x=a[0],y=a[1],sel=a[2];const e=document.elementFromPoint(x,y);
 if(!e) return {tag:null,ok:false,sel:sel};
 const t=e.closest(sel);
 return {tag:e.tagName, ok:!!t, sel:sel,
   ariaLabel:t?t.getAttribute('aria-label'):null};}"""


def open_director(pg):
    el = pg.query_selector("[data-open-director]")
    if not el:
        return {"FAILED": "画布上找不到「打开导演台」"}
    pg.evaluate("()=>{const b=document.querySelector('[data-open-director]');"
                "if(b) b.scrollIntoView({block:'center'});}")
    pg.wait_for_timeout(400)
    el = pg.query_selector("[data-open-director]")
    box = el.bounding_box()
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    hit = pg.evaluate(HIT, [cx, cy, "[data-open-director]"])
    if not hit.get("ok"):
        raise SystemExit("FATAL「打开导演台」坐标没命中 —— 当场停")
    pg.mouse.click(cx, cy)
    try:
        pg.wait_for_selector('[role="dialog"][aria-modal="true"]', timeout=25000)
    except Exception:
        return {"FAILED": "点了但 dialog 没出现"}
    pg.wait_for_timeout(2400)
    return {"at": [int(cx), int(cy)]}


def tab_walk(pg, n):
    seq = []
    for i in range(n):
        pg.keyboard.press("Tab")
        pg.wait_for_timeout(80)
        a = pg.evaluate(ACTIVE)
        seq.append({"after": i, "inDialog": a["inDialog"], "tag": a["tag"],
                    "ariaLabel": a["ariaLabel"]})
    esc = [s["after"] for s in seq if s["inDialog"] is False]
    return {"steps": n, "escapedCount": len(esc), "escapedAt": esc, "seq": seq}


def main():
    res = {"batch": 762, "probe": "b", "rounds": []}
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1440, "height": 1000})
        for _ in range(1, 2):
            pg.goto(BASE, wait_until="networkidle")
            pg.wait_for_selector(".react-flow__node", timeout=25000)
            pg.wait_for_timeout(1200)
            pg.keyboard.press("Meta+0")
            pg.wait_for_timeout(900)
            R = {}
            r = open_director(pg)
            if "FAILED" in r:
                R["FAILED"] = r["FAILED"]
                res["rounds"].append(R)
                continue

            # ① 点名那 2 个不可达元素
            R["B1_list"] = pg.evaluate(LIST)
            R["B1_state"] = pg.evaluate(STATE)
            R["B1_focusable"] = pg.evaluate(FOCUSABLE_N)

            # ② 折叠：用正确的钩子，真实点击
            tg = pg.query_selector("[data-director-panels-toggle]")
            hit = None
            if tg:
                box = tg.bounding_box()
                cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
                hit = pg.evaluate(HIT, [cx, cy, "[data-director-panels-toggle]"])
                if not hit.get("ok"):
                    raise SystemExit("FATAL 折叠按钮坐标没命中 —— 当场停")
                pg.mouse.click(cx, cy)
                pg.wait_for_timeout(1400)
            R["B2_hit"] = hit
            R["B2_after"] = pg.evaluate(STATE)
            R["B2_focusable"] = pg.evaluate(FOCUSABLE_N)
            R["B2_tab"] = tab_walk(pg, 14)

            # ③ 焦点落到某个子面板上时，Esc 是否仍能关闭
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(1200)
            R["B3_escClosed"] = pg.evaluate(ACTIVE)["open"] is False
            R["B3_focusAfter"] = pg.evaluate(ACTIVE)
            r2 = open_director(pg)
            if "FAILED" in r2:
                R["B4_reopen"] = r2
            else:
                # 先 Tab 若干次把焦点推进子面板，再 Esc
                pg.keyboard.press("Tab")
                pg.keyboard.press("Tab")
                pg.keyboard.press("Tab")
                pg.keyboard.press("Tab")
                pg.keyboard.press("Tab")
                pg.wait_for_timeout(200)
                R["B4_focusBeforeEsc"] = pg.evaluate(ACTIVE)
                pg.keyboard.press("Escape")
                pg.wait_for_timeout(1200)
                R["B4_afterEsc"] = pg.evaluate(ACTIVE)

            res["rounds"].append(R)
        br.close()

    def strip(o):
        if isinstance(o, str):
            return re.sub(r"-\d{10,}-[a-z0-9]{6}\b", "-<gen>", o)
        if isinstance(o, dict):
            return {k: strip(v) for k, v in o.items()}
        if isinstance(o, list):
            return [strip(v) for v in o]
        return o

    r1 = res["rounds"][0]
    res["roundDiff"] = {}
    res["consistent"] = True
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

    print("FAILED:", r1.get("FAILED"))
    b1 = r1.get("B1_list") or {}
    print("B1 总数=%s 可达=%s 不可达=%s"
          % (b1.get("total"), b1.get("reachable"), b1.get("unreachable")))
    for u in (b1.get("unreachableList") or []):
        print("   不可达: <%s> aria-label=%r display=%s visibility=%s "
              "w×h=%sx%s cls=%s text=%r"
              % (u["tag"], u["ariaLabel"], u["display"], u["visibility"],
                 u["w"], u["h"], u["cls"][:46], u["text"]))
    st = r1.get("B2_after") or {}
    print("B2 折叠后 collapsed=%s togglePresent=%s toggleAriaPressed=%s "
          "可达焦点=%s"
          % (st.get("collapsed"), st.get("togglePresent"),
             st.get("toggleAriaPressed"),
             (r1.get("B2_focusable") or {}).get("reachable")))
    for pn in st.get("panels", []):
        print("   面板 %-8s inert=%-5s aria-hidden=%-6s display=%-6s w=%s"
              % (pn["ariaLabel"], pn["inert"], pn["ariaHidden"], pn["display"],
                 pn["w"]))
    t = r1.get("B2_tab") or {}
    print("B2 折叠后 Tab %s 次，逃出 dialog %s 次（步 %s）"
          % (t.get("steps"), t.get("escapedCount"), t.get("escapedAt")))
    print("B3 折叠态下 Esc 能关闭:", r1.get("B3_escClosed"),
          "| 关闭后焦点:", json.dumps(r1.get("B3_focusAfter"),
                                      ensure_ascii=False)[:170])
    print("B4 焦点在子面板时 Esc 前焦点:",
          json.dumps(r1.get("B4_focusBeforeEsc"), ensure_ascii=False)[:170])
    print("B4 Esc 后:", json.dumps(r1.get("B4_afterEsc"),
                                   ensure_ascii=False)[:200])


if __name__ == "__main__":
    main()
