#!/usr/bin/env python3
"""batch 763 探针 h：导演台里的增删，扛不扛得过一次完整页面重载？

起因：763b 两轮的对象列表不一样（round 1 六个 / round 2 五个，round 1 被我删掉的
character 与 prop-table 在 round 2 里不见了），而 round 2 里那台相机的 id
`director-camera-1791136225444-1` 与 round 1 **逐字符相同**。
如果两次之间真的重新加载过页面（`load()` 里是 `set_viewport_size` + `goto`），
⟹ 导演台的改动落在了**页面之外**的存储里。

这决定两件事，必须实测而不是推演：
  1. 我还能不能宣称「两轮一致」（探针自伤会让两轮不可比）
  2. 导演台工作区对画布种子数据是**破坏性**的，且刷新救不回来

本探针：加载 → 开台 → 记对象数 → 加一台机位 → 记对象数 →
读 localStorage / sessionStorage 的键名与体积 → **重新加载** → 再开台 → 记对象数。
"""
import json
import pathlib
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch763-2026-10-01/raw/vb763h.json")

OBJECTS = """()=>{const d=document.querySelector(
  '[role="dialog"][aria-modal="true"]');
 if(!d) return {err:'no dialog'};
 const t=d.querySelector('aside[aria-label="场景对象"]');
 if(!t) return {err:'no tree'};
 const rows=[];
 for(const e of t.querySelectorAll('[data-director-object-id]')){
   const r=e.getBoundingClientRect(); if(r.width<=0||r.height<=0) continue;
   rows.push({id:e.getAttribute('data-director-object-id'),
     kind:e.getAttribute('data-director-object-kind'),
     text:(e.textContent||'').trim().slice(0,18)});}
 return {count:rows.length, ids:rows.map(r=>r.id)};}"""

STORAGE = """()=>{const dump=(s)=>{const out=[];
  try{ for(let i=0;i<s.length;i++){ const k=s.key(i);
    const v=s.getItem(k)||'';
    out.push({key:k, bytes:v.length,
      looksDirector:/director|camera|prop|character/i.test(v)});}}
  catch(e){ return {err:String(e)}; }
  return out;};
 return {local:dump(localStorage), session:dump(sessionStorage),
   localCount:localStorage.length, sessionCount:sessionStorage.length};}"""

SCAN_CLICK = """(sel)=>{const el=document.querySelector(sel);
 if(!el) return {missing:true};
 const r=el.getBoundingClientRect();
 for(let f=0.1; f<=0.95; f+=0.07) for(let g=0.1; g<=0.95; g+=0.07){
   const x=Math.round(r.x+r.width*f), y=Math.round(r.y+r.height*g);
   if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
   const e=document.elementFromPoint(x,y);
   if(e&&e.closest&&e.closest(sel)) return {pt:[x,y]};}
 return {noHit:true};}"""


def settle(pg, tries=8, gap=220):
    prev, same = None, 0
    for _ in range(36):
        cur = pg.evaluate("""()=>{const v=window.__libtv_store.getState()
          .getActiveCanvas().viewport; return [v.x,v.y,v.zoom].join('|');}""")
        same = same + 1 if cur == prev else 0
        prev = cur
        if same >= tries:
            return cur
        pg.wait_for_timeout(gap)
    return prev


def load(pg):
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1200)
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(600)
    settle(pg)
    return pg.evaluate(SCAN_CLICK, "[data-open-director]")


def open_desk(pg):
    s = pg.evaluate(SCAN_CLICK, "[data-open-director]")
    if not s.get("pt"):
        return {"FAILED": s}
    pg.mouse.click(s["pt"][0], s["pt"][1])
    try:
        pg.wait_for_selector('[role="dialog"][aria-modal="true"]', timeout=25000)
    except Exception:
        return {"FAILED": "点了但没 dialog"}
    pg.wait_for_timeout(1800)
    return {"ok": True}


def run_round(pg, R):
    s = load(pg)
    R["loadClick"] = s
    if not s.get("pt"):
        R["FAILED"] = s
        return
    R["open1"] = open_desk(pg)
    if "FAILED" in R["open1"]:
        return
    R["objectsAtOpen1"] = pg.evaluate(OBJECTS)
    ac = pg.evaluate(SCAN_CLICK, '[data-director-rail-entry="add-camera"]')
    R["addCameraClick"] = ac
    if ac.get("pt"):
        pg.mouse.click(ac["pt"][0], ac["pt"][1])
        pg.wait_for_timeout(1200)
    R["objectsAfterAdd"] = pg.evaluate(OBJECTS)
    R["storageBeforeReload"] = pg.evaluate(STORAGE)

    # ★ 完整重新加载
    s2 = load(pg)
    R["reloadClick"] = s2
    if not s2.get("pt"):
        R["FAILED_reload"] = s2
        return
    R["open2"] = open_desk(pg)
    if "FAILED" in R["open2"]:
        return
    R["objectsAfterReload"] = pg.evaluate(OBJECTS)
    R["storageAfterReload"] = pg.evaluate(STORAGE)

    a = R["objectsAtOpen1"]
    b = R["objectsAfterAdd"]
    c = R["objectsAfterReload"]
    R["verdict"] = {
        "baseCount": a.get("count") if isinstance(a, dict) else None,
        "afterAddCount": b.get("count") if isinstance(b, dict) else None,
        "afterReloadCount": c.get("count") if isinstance(c, dict) else None,
        "addSurvivedReload": (isinstance(b, dict) and isinstance(c, dict)
                             and b.get("count") == c.get("count")
                             and set(b.get("ids") or []) == set(c.get("ids") or [])),
        "reloadLostAdd": (isinstance(b, dict) and isinstance(c, dict)
                          and c.get("count") == a.get("count")),
        "newIdsAfterAdd": sorted(set(b.get("ids") or [])
                                 - set(a.get("ids") or [])) if
        isinstance(a, dict) and isinstance(b, dict) else None}


def main():
    res = {"batch": 763, "probe": "h",
           "question": "导演台里的增删扛不扛得过一次完整页面重载？",
           "rounds": []}
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 1440, "height": 1000})
        try:
            for i in range(2):
                R = {}
                res["rounds"].append(R)
                print("round %d" % (i + 1))
                run_round(pg, R)
                print("   verdict:", json.dumps(R.get("verdict"),
                                                ensure_ascii=False))
        finally:
            OUT.parent.mkdir(parents=True, exist_ok=True)
            try:
                br.close()
            except Exception:
                pass
            OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1),
                           encoding="utf-8")
    a, b = res["rounds"]
    print("\n两轮 verdict 一致 =", a.get("verdict") == b.get("verdict"))
    sa = (a.get("storageBeforeReload") or {})
    sb = (a.get("storageAfterReload") or {})
    print("重载前 localStorage 键 =", json.dumps(
        [x["key"] for x in sa.get("local", [])], ensure_ascii=False)[:300])
    print("重载后 localStorage 键 =", json.dumps(
        [x["key"] for x in sb.get("local", [])], ensure_ascii=False)[:300])
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
