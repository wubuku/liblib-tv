#!/usr/bin/env python3
"""batch 772 探针 a：**浮层开着时，导演台的全局快捷键会不会「穿透」进来**

## 这一批问的

767–771 连续五批都在 disclosure 浮层的**焦点围栏**上（D11 归还 / D13 围栏 /
可达性）。D8（按 Esc 丢整个工作区）是「窗口级处理器抢在浮层前面动手」的一个
**实例**。本批问它的**同族**：

  **浮层开着、焦点落在浮层里某个控件上时，导演台的全局快捷键会不会照样生效？**

机制（静态可查，本批已逐字读过）：

`DirectorDesk.tsx:473-571` 在 **window、冒泡**阶段注册了**一个** keydown 处理器，
它管的不止 Escape：

| 键 | 行为 | 行号 |
| --- | --- | --- |
| `Escape` + `activeMobilePanel` | 关移动抽屉 | `:482-486` |
| — | `if (isEditable) return;` ← **唯一的挡板** | `:487` |
| `Meta/Ctrl+C` | `copyDirectorSelection()` | `:490-494` |
| `Meta/Ctrl+V` | `pasteDirectorClipboard()` | `:495-505` |
| `Meta/Ctrl+Z` / `Shift+Z` | `undoDirector()` | `:506-511` |
| `Meta/Ctrl+Y` | `redoDirector()` | `:512-516` |
| **`Delete` / `Backspace`** | **`deleteDirectorEntity()`（真删东西）** | `:517-548` |
| `Escape` | 手势取消 → 关导出面板 → 退出跟随 → **`closeWorkspace()`** | `:549-568` |

`isEditable` 只认 `isContentEditable` 与 `INPUT/TEXTAREA/SELECT`（`:475-480`）。
而 6 个浮层的可编辑控件数（769/770/771 三批独立读数一致）：

| 浮层 | 可编辑 / 不可编辑 |
| --- | --- |
| export | 1 / 4 |
| preset | **0 / 10** |
| pathmenu | **0 / 5** |
| phonevcam | **0 / 2** |
| crowd | 3 / 2 |
| modellib | 2 / 13 |

⟹ **preset / pathmenu / phonevcam 三个浮层里没有任何一个控件能让那道早退生效。**

### 冒烟阶段量到的判别式（先验，全部成立才上全网格）

1. 能在对象树上**选中**一个对象 —— Delete 分支只在有选中时才动手
2. 焦点在**树上**按 Delete，对象数**真的会掉** ← 阳性对照
3. 焦点落在浮层内的**输入框**上按 Delete，对象数**不掉** ← 守卫对照
   （就是 769 量的那道 `isEditable` 早退；没有它就量不到「漏没漏」）
4. 6 个浮层都开得了、焦点都放得进去，落点下标与控件计数**逐个吻合**

### 四条臂

| 臂 | mode | 落点 | 键 | 格数 |
| --- | --- | --- | --- | --- |
| 1 | `del-noneditable` | 浮层内第一个**不可编辑**控件 | `Delete` | 6 |
| 2 | `bs-noneditable` | 同上 | `Backspace` | 6 |
| 3 | `del-editable` | 浮层内第一个**可编辑**控件 | `Delete` | 3（只有 export/crowd/modellib 有） |
| 4 | `undo-noneditable` | 浮层内第一个**不可编辑**控件 | `Meta+Z` | 6 |

臂 4 的**设置**（每次都新开一页）：先在树上选中一个对象、按 `Delete` 删掉它，
**确认对象数真的掉了**（没掉就判该格失败 —— 否则「撤销没生效」可能只是
「本来就没东西可撤」，R86），再开浮层、把焦点放进浮层、按 `Meta+Z`。

### 读数

每次按键前后各读一次：对象总数、选中 id、React Flow 节点数、浮层还在不在、
导演台还在不在、按键后焦点在哪。

### 边界

只点对象树的行、6 个 disclosure 触发器、以及为开 preset/pathmenu 而选中相机；
**不点提交/连接/添加，更不做付费或真实生图生视频**。`Delete` 是被测行为，
放它跑 —— 破坏只存在于本探针这一页内（每格都重载 + 清 localStorage）。
"""
import json
import pathlib
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
LS_KEY = "liblib-tv-director-project-v1"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch772-2026-10-01/raw/vb772a.json")

CLEAR_LS = """(k)=>{const ks=[]; for(let i=0;i<localStorage.length;i++){
    const key=localStorage.key(i); if(key&&key.indexOf(k)===0){ks.push(key);}}
  ks.forEach(x=>localStorage.removeItem(x)); return {removed:ks};}"""

SCAN_CLICK = """(sel)=>{const el=document.querySelector(sel);
 if(!el) return {missing:true};
 if(el.disabled) return {disabled:true};
 const r=el.getBoundingClientRect();
 for(let f=0.08; f<=0.95; f+=0.07)
   for(let g=0.08; g<=0.95; g+=0.07){
     const x=Math.round(r.x+r.width*f), y=Math.round(r.y+r.height*g);
     if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
     const e=document.elementFromPoint(x,y);
     if(e&&e.closest&&e.closest(sel)===el) return {pt:[x,y]};}
 return {noHit:true};}"""

DESK = """()=>{const d=document.querySelector(
 '[role="dialog"][aria-modal="true"]'); const a=document.activeElement;
 return {open:!!d, tag:a?a.tagName:null, type:a?a.getAttribute('type'):null,
   aria:a?a.getAttribute('aria-label'):null,
   text:a?(a.textContent||'').trim().slice(0,12):null,
   isBody:a===document.body,
   inDialog:!!(d&&a&&(d===a||d.contains(a)))};}"""

TREE = """()=>{const t=document.querySelector('[data-director-tree]');
 if(!t) return {tree:false};
 const objs=[...t.querySelectorAll('[data-director-object-id]')];
 const groups=[...t.querySelectorAll('[data-director-group-id]')];
 return {tree:true, objectCount:objs.length,
   objectIds:objs.map(e=>e.getAttribute('data-director-object-id')),
   selectedIds:objs.filter(e=>e.getAttribute('data-director-object-selected')
     ==='true').map(e=>e.getAttribute('data-director-object-id')),
   groupCount:groups.length,
   selectedGroups:groups.filter(e=>e.getAttribute(
     'data-director-group-selected')==='true').length,
   nodeCount:document.querySelectorAll('.react-flow__node').length};}"""

STATE = """(a)=>{const d=document.querySelector(
 '[role="dialog"][aria-modal="true"]'); if(!d) return {deskOpen:false};
 const p=d.querySelector(a[0]); const act=document.activeElement;
 return {deskOpen:true, panelPresent:!!p,
   activeInPanel:!!(act&&p&&p.contains(act))};}"""

FOCUS_IN = """(a)=>{const d=document.querySelector(
 '[role="dialog"][aria-modal="true"]'); if(!d) return {err:'no dialog'};
 const p=d.querySelector(a[0]); if(!p) return {err:'no panel'};
 const foc=(root)=>[...root.querySelectorAll(
  'a[href],button,input,select,textarea,[tabindex],'
  +'[contenteditable="true"]')].filter(e=>{
  if(e.disabled) return false; const ti=e.getAttribute('tabindex');
  if(ti!==null&&Number(ti)<0) return false;
  const s=getComputedStyle(e);
  if(s.display==='none'||s.visibility==='hidden') return false;
  const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;});
 const f=foc(p);
 const isEd=(e)=>e.isContentEditable||e.tagName==='INPUT'
   ||e.tagName==='TEXTAREA'||e.tagName==='SELECT';
 const counts={editable:0,noneditable:0};
 f.forEach(e=>{counts[isEd(e)?'editable':'noneditable']++;});
 const want=a[1];
 const i = want==='editable' ? f.findIndex(isEd)
                             : f.findIndex(e=>!isEd(e));
 if(i<0) return {err:'no '+want+' control', panelCount:f.length, counts};
 f[i].focus({preventScroll:true});
 return {ok:true, panelCount:f.length, localIdx:i, counts,
   tag:f[i].tagName, type:f[i].getAttribute('type'),
   text:(f[i].textContent||'').trim().slice(0,12), editable:isEd(f[i])};}"""

FOCUS_TREE_ROW = """(id)=>{const t=document.querySelector(
 '[data-director-tree]'); if(!t) return {err:'no tree'};
 const r=t.querySelector('[data-director-object-id="'+id+'"]');
 if(!r) return {err:'no row'};
 r.focus({preventScroll:true}); return {ok:true, tag:r.tagName};}"""

DISCLOSURES = [
    {"id": "export", "trigger": "[data-director-export-trigger]",
     "panel": "[data-director-export-panel]", "needs": "none"},
    {"id": "preset", "trigger": "[data-director-camera-preset-trigger]",
     "panel": "[data-director-camera-preset-panel]", "needs": "cameraTrack"},
    {"id": "pathmenu",
     "trigger": '[data-director-track-draw-trail="director-track-camera-main"]',
     "panel": "[data-director-motion-path-menu]", "needs": "cameraTrack"},
    {"id": "phonevcam", "trigger": "[data-director-phone-vcam-trigger]",
     "panel": "[data-director-phone-vcam-panel]", "needs": "none"},
    {"id": "crowd", "trigger": "[data-director-crowd-trigger]",
     "panel": "[data-director-crowd-panel]", "needs": "none"},
    {"id": "modellib", "trigger": "[data-director-model-library-trigger]",
     "panel": "[data-director-model-library-panel]", "needs": "none"},
]

# mode -> (want, key)
MODES = [
    ("del-noneditable", "noneditable", "Delete"),
    ("bs-noneditable", "noneditable", "Backspace"),
    ("del-editable", "editable", "Delete"),
    ("undo-noneditable", "noneditable", "Meta+z"),
]
HAS_EDITABLE = {"export", "crowd", "modellib"}


def settle(pg, tries=8, gap=220):
    prev, same = None, 0
    for _ in range(30):
        cur = pg.evaluate("()=>{const d=document.querySelector("
                          "'[role=\"dialog\"][aria-modal=\"true\"]');"
                          "return d?1:0;}")
        same = same + 1 if cur == prev else 0
        prev = cur
        if cur == 1 and same >= tries:
            return cur
        pg.wait_for_timeout(gap)
    return prev


def open_desk(pg):
    if pg.evaluate(DESK).get("open"):
        return {"ok": True, "already": True}
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


def fresh(pg):
    pg.goto(BASE, wait_until="domcontentloaded")
    pg.evaluate(CLEAR_LS, LS_KEY)
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1200)
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(600)
    settle(pg)
    return open_desk(pg)


def click_tree_row(pg, oid):
    s = pg.evaluate("""(id)=>{const t=document.querySelector(
      '[data-director-tree]');
      const r=t&&t.querySelector('[data-director-object-id="'+id+'"]');
      if(!r) return {missing:true};
      const b=r.getBoundingClientRect();
      for(let f=0.12; f<=0.88; f+=0.08)
        for(let g=0.12; g<=0.88; g+=0.08){
          const x=Math.round(b.x+b.width*f), y=Math.round(b.y+b.height*g);
          if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
          const e=document.elementFromPoint(x,y);
          if(e&&e.closest&&e.closest('[data-director-object-id="'+id+'"]')===r)
            return {pt:[x,y]};}
      return {noHit:true};}""", oid)
    if not s.get("pt"):
        return {"FAILED": "点不到对象行", "scan": s, "id": oid}
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(450)
    return {"ok": True, "id": oid}


def ensure_camera(pg):
    """选中主机位。★ 必须**点击** —— 焦点落在一行上不等于选中它
    （第一版写成 focus，preset 的触发器一直 disabled）。"""
    s = pg.evaluate(SCAN_CLICK, '[data-director-object-id='
                               '"director-camera-main"]')
    if not s.get("pt"):
        return {"FAILED": "点不到主机位行", "scan": s}
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(700)
    return {"ok": True, "selectedIds": (pg.evaluate(TREE) or {}).get(
        "selectedIds")}


def open_disclosure(pg, d):
    st = pg.evaluate(STATE, [d["panel"]])
    if st.get("panelPresent"):
        return {"alreadyOpen": True}
    s = pg.evaluate(SCAN_CLICK, d["trigger"])
    if not s.get("pt"):
        return {"FAILED": "触发器点不动", "scan": s}
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(700)
    if not pg.evaluate(STATE, [d["panel"]]).get("panelPresent"):
        return {"FAILED": "点了但浮层没出现"}
    return {"opened": True}


def cell(pg, d, mode, want, key):
    R = {"id": d["id"], "name": d.get("name"), "mode": mode, "key": key}
    r = fresh(pg)
    if r.get("FAILED"):
        R["FAILED"] = "导演台没开"
        return R
    if d["needs"] == "cameraTrack":
        c = ensure_camera(pg)
        if c.get("FAILED"):
            R["FAILED"] = "相机没选中"
            return R
    # ── 选中一个对象（Delete/Undo 分支的前提）
    t0 = pg.evaluate(TREE)
    ids = (t0 or {}).get("objectIds") or []
    if not ids:
        R["FAILED"] = "对象树里没有对象"
        return R
    target = ids[0]
    R["target"] = target
    R["select"] = click_tree_row(pg, target)
    t1 = pg.evaluate(TREE)
    R["selectedBefore"] = t1.get("selectedIds")
    if not t1.get("selectedIds"):
        R["FAILED"] = "点了对象行但没选中"
        return R
    R["countsBeforeSelect"] = {"objects": t1.get("objectCount"),
                               "nodes": t1.get("nodeCount")}

    if mode == "undo-noneditable":
        # 设置：先在**树上**删掉一个，确认真的删了（R86：没删就判失败）
        pg.evaluate(FOCUS_TREE_ROW, target)
        n0 = pg.evaluate(TREE).get("objectCount")
        pg.keyboard.press("Delete")
        pg.wait_for_timeout(700)
        t2 = pg.evaluate(TREE)
        R["setup"] = {"objectsBefore": n0, "objectsAfter": t2.get("objectCount"),
                      "nodesAfter": t2.get("nodeCount")}
        if not (t2.get("objectCount") or 0) < (n0 or 0):
            R["FAILED"] = "设置失败：树上按 Delete 没删掉对象"
            return R
        # 重新选中另一个还存在的对象，让撤销有「可撤的删除」以外的背景
        t2ids = t2.get("objectIds") or []
        if t2ids:
            click_tree_row(pg, t2ids[0])
            pg.wait_for_timeout(300)
        R["objectsBeforeKey"] = pg.evaluate(TREE).get("objectCount")

    op = open_disclosure(pg, d)
    if op.get("FAILED"):
        R["FAILED"] = op["FAILED"]
        return R
    R["open"] = op
    f = pg.evaluate(FOCUS_IN, [d["panel"], want])
    R["focus"] = f
    if f.get("err"):
        R["FAILED"] = "放不进焦点：%s" % f["err"]
        return R
    R["before"] = pg.evaluate(TREE)
    R["stateBefore"] = pg.evaluate(STATE, [d["panel"]])
    R["focusBefore"] = pg.evaluate(DESK)

    pg.keyboard.press(key)
    pg.wait_for_timeout(700)

    R["after"] = pg.evaluate(TREE)
    R["stateAfter"] = pg.evaluate(STATE, [d["panel"]])
    R["focusAfter"] = pg.evaluate(DESK)
    b, a = R["before"], R["after"]
    R["delta"] = {
        "objects": (a.get("objectCount") or 0) - (b.get("objectCount") or 0),
        "nodes": (a.get("nodeCount") or 0) - (b.get("nodeCount") or 0),
        "groups": (a.get("groupCount") or 0) - (b.get("groupCount") or 0),
    }
    R["layerStillOpen"] = R["stateAfter"].get("panelPresent")
    R["deskStillOpen"] = R["stateAfter"].get("deskOpen")
    R["leaked"] = bool(R["delta"]["objects"] < 0 or R["delta"]["nodes"] < 0)
    R["restored"] = bool(mode == "undo-noneditable"
                         and (a.get("objectCount") or 0)
                         > (b.get("objectCount") or 0))
    return R


def run_round(pg, R):
    R["rows"] = []
    for d in DISCLOSURES:
        for mode, want, key in MODES:
            if mode == "del-editable" and d["id"] not in HAS_EDITABLE:
                R["rows"].append({"id": d["id"], "mode": mode,
                                  "SKIPPED": "该浮层没有可编辑控件（"
                                            "0 个，isEditable 不可能成立）"})
                continue
            try:
                r = cell(pg, d, mode, key and want, key)
            except Exception as e:
                r = {"id": d["id"], "mode": mode,
                     "FAILED": "%s: %s" % (type(e).__name__, str(e)[:150])}
            r.setdefault("name", d.get("name") or d["id"])
            R["rows"].append(r)
            if pg.evaluate(DESK).get("open") is not True:
                R.setdefault("deskGoneAfter", []).append(
                    d["id"] + "/" + mode)


def summarize(R):
    for r in R.get("rows") or []:
        if r.get("SKIPPED"):
            print("   %-10s %-18s SKIP: %s" % (r["id"], r["mode"],
                                              r["SKIPPED"]))
            continue
        if r.get("FAILED"):
            print("   %-10s %-18s FAILED: %s" % (r["id"], r["mode"],
                                                  str(r["FAILED"])[:50]))
            continue
        dl = r["delta"]
        if r["mode"] == "undo-noneditable":
            v = "★ 撤销穿透进浮层了" if r["restored"] else "撤销没进浮层"
        elif r["leaked"]:
            v = "★ 穿透：对象 %+d / 节点 %+d" % (dl["objects"], dl["nodes"])
        else:
            v = "被挡住了（对象 %+d）" % dl["objects"]
        print("   %-10s %-18s 落点=%-6s idx=%-3s 可编辑=%-5s 浮层还在=%-5s"
              " 导演台还在=%-5s → %s"
              % (r["id"], r["mode"], (r.get("focus") or {}).get("tag"),
                 (r.get("focus") or {}).get("localIdx"),
                 (r.get("focus") or {}).get("editable"),
                 r["layerStillOpen"], r["deskStillOpen"], v))


def main():
    res = {"batch": 772, "probe": "a",
           "question": "浮层开着、焦点在浮层内某个控件上时，导演台的全局"
                       "快捷键（Delete / Backspace / Meta+Z）会不会照样生效",
           "rounds": []}
    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context(viewport={"width": 1440, "height": 1000})
        pg = ctx.new_page()
        try:
            for i in range(2):
                R = {}
                res["rounds"].append(R)
                print("round %d" % (i + 1))
                run_round(pg, R)
                summarize(R)
        finally:
            OUT.parent.mkdir(parents=True, exist_ok=True)
            try:
                br.close()
            except Exception:
                pass
            OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1),
                           encoding="utf-8")
            print("（已落盘）")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
