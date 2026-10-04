#!/usr/bin/env python3
"""batch 772 探针 b：补 preset、补 pathmenu 的归因，外加一个相机可删性对照

## 为什么要 b

772a 已经把 4 个浮层（export / phonevcam / crowd / modellib）与 undo 臂量清楚了，
**这些读数不作废**。但有两格不成立，各有各的原因：

1. **preset 三格全 FAILED（触发器点不动 = `disabled`）** —— 这是 772a 的
   **排序 bug**：`cell()` 先 `ensure_camera()` 再 `click_tree_row()` 去点
   第一个对象（`director-character-lead`），**那一���把刚选中的相机顶掉了**，
   于是 preset 触发器重新变 `disabled`。修法：对 `needs=="cameraTrack"`
   的浮层，**被删目标就用相机本身**，点一次同时满足「触发器可用」与
   「有选中」两个前提。
2. **pathmenu 两格没删对象** —— 但**不能**写成「被挡住了」。772a 的读数是：
   按键时 `selectedIds = ['director-camera-main']`（**打开菜单把选中换成了
   相机**），按完**选中没变、对象没少**。于是至少有三种解释：
   (a) 快捷键真的没进去；(b) 进去了但相机不可删；(c) 进去了但相机那一档
   `deleteDirectorEntity` 是 no-op。**772a 无法区分这三者。**

   所以本探针加一个**对照格**：选中相机、焦点放在**任何浮层之外**的对话框
   控件上、按 `Delete` —— 相机被删 ⟹ (a)；不被删 ⟹ (b)/(c)。
   没有这个对照，「pathmenu 没删」会被误读成「这条路是好的」。

## 两个信号，都要读

| 信号 | 含义 |
| --- | --- |
| `objectsDropped` | 对象总数真的少了 ⟹ 破坏真的发生 |
| `selectionCleared` | `selectedIds` 从非空变成空 ⟹ 桌内那个 Delete 分支**真的跑到了删除** |

772a 的 4 个泄漏格里两个信号同时为真。**相机若不可删，只有第二个信号可用** ——
所以两个都得读，不能只报一个。

## 格子

| mode | 做什么 |
| --- | --- |
| `cam-deletable-control` | 选中相机 → 焦点放到**浮层之外**的对话框控件 → `Delete` |
| `preset/del-noneditable` | 选中相机（= 目标）→ 开预设面板 → 落非编辑框 → `Delete` |
| `preset/bs-noneditable` | 同上，`Backspace` |
| `preset/undo-noneditable` | 设置：树上删掉角色（5→4，自证）→ 选中相机 → 开面板 → `Meta+Z` |
| `pathmenu/del-noneditable` | 选中相机 → 开路径菜单 → 落非编辑框 → `Delete` |
| `pathmenu/bs-noneditable` | 同上，`Backspace` |
| `pathmenu/undo-noneditable` | 同 preset 的 undo 臂 |

## 边界

与 772a 相同：只点对象树的行、6 个 disclosure 触发器、选中相机；
不点提交/连接/添加，更不做付费或真实生图生视频。破坏只存在于本页内。
"""
import json
import pathlib
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
LS_KEY = "liblib-tv-director-project-v1"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch772-2026-10-01/raw/vb772b.json")
CAM = "director-camera-main"
CHAR = "director-character-lead"

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
 const p=a?d.querySelector(a[0]):null; const act=document.activeElement;
 return {deskOpen:true, panelPresent:!!p,
   activeInPanel:!!(act&&p&&p.contains(act))};}"""

# 浮层内第 idx 个可聚焦控件；want='editable'|'noneditable'
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

# ★ 对照格用：对话框里**不在任何浮层内**的第一个可聚焦控件
FOCUS_OUTSIDE = """(panelSel)=>{const d=document.querySelector(
 '[role="dialog"][aria-modal="true"]'); if(!d) return {err:'no dialog'};
 const p=d.querySelector(panelSel);
 const foc=(root)=>[...root.querySelectorAll(
  'a[href],button,input,select,textarea,[tabindex],'
  +'[contenteditable="true"]')].filter(e=>{
  if(e.disabled) return false; const ti=e.getAttribute('tabindex');
  if(ti!==null&&Number(ti)<0) return false;
  const s=getComputedStyle(e);
  if(s.display==='none'||s.visibility==='hidden') return false;
  const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;});
 const f=foc(d).filter(e=>!(p&&p.contains(e)));
 if(!f.length) return {err:'no control outside the panel'};
 f[0].focus({preventScroll:true});
 return {ok:true, count:f.length, tag:f[0].tagName,
   type:f[0].getAttribute('type'),
   text:(f[0].textContent||'').trim().slice(0,12),
   aria:f[0].getAttribute('aria-label')};}"""

FOCUS_TREE_ROW = """(id)=>{const t=document.querySelector(
 '[data-director-tree]'); if(!t) return {err:'no tree'};
 const r=t.querySelector('[data-director-object-id="'+id+'"]');
 if(!r) return {err:'no row'};
 r.focus({preventScroll:true}); return {ok:true};}"""

LAYERS = {
    "preset": {"trigger": "[data-director-camera-preset-trigger]",
               "panel": "[data-director-camera-preset-panel]"},
    "pathmenu": {"trigger": '[data-director-track-draw-trail='
                             '"director-track-camera-main"]',
                 "panel": "[data-director-motion-path-menu]"},
}
PLANS = [
    ("cam-deletable-control", None, "Delete"),
    ("preset/del-noneditable", "preset", "Delete"),
    ("preset/bs-noneditable", "preset", "Backspace"),
    ("preset/undo-noneditable", "preset", "Meta+z"),
    ("pathmenu/del-noneditable", "pathmenu", "Delete"),
    ("pathmenu/bs-noneditable", "pathmenu", "Backspace"),
    ("pathmenu/undo-noneditable", "pathmenu", "Meta+z"),
]


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
    pg.wait_for_timeout(500)
    return {"ok": True, "id": oid}


def open_layer(pg, lay):
    d = LAYERS[lay]
    if pg.evaluate(STATE, [d["panel"]]).get("panelPresent"):
        return {"alreadyOpen": True}
    s = pg.evaluate(SCAN_CLICK, d["trigger"])
    if not s.get("pt"):
        return {"FAILED": "触发器点不动", "scan": s}
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(700)
    if not pg.evaluate(STATE, [d["panel"]]).get("panelPresent"):
        return {"FAILED": "点了但浮层没出现"}
    return {"opened": True}


def run_cell(pg, plan, key):
    R = {"plan": plan, "key": key}
    r = fresh(pg)
    if r.get("FAILED"):
        R["FAILED"] = "导演台没开"
        return R
    isUndo = plan.endswith("undo-noneditable")
    isControl = plan == "cam-deletable-control"

    if isUndo:
        # 设置：先删掉角色并**自证**真的删了（R86）
        pg.evaluate(FOCUS_TREE_ROW, CHAR)
        n0 = pg.evaluate(TREE).get("objectCount")
        pg.keyboard.press("Delete")
        pg.wait_for_timeout(700)
        t = pg.evaluate(TREE)
        R["setup"] = {"objectsBefore": n0, "objectsAfter": t.get("objectCount")}
        if not (t.get("objectCount") or 0) < (n0 or 0):
            R["FAILED"] = "设置失败：树上按 Delete 没删掉对象"
            return R
    # ★ 对 `cameraTrack` 两层：**被删目标就用相机本身** ——
    #   点一次同时满足「触发器可用」与「有选中」两个前提（772a 的排序 bug）
    sel = click_tree_row(pg, CAM)
    R["select"] = sel
    t1 = pg.evaluate(TREE)
    R["selectedAfterSelect"] = t1.get("selectedIds")
    if CAM not in (t1.get("selectedIds") or []):
        R["FAILED"] = "相机没选中"
        return R

    if isControl:
        f = pg.evaluate(FOCUS_OUTSIDE, "[data-director-model-library-panel]")
    else:
        lay = plan.split("/")[0]
        op = open_layer(pg, lay)
        R["open"] = op
        if op.get("FAILED"):
            R["FAILED"] = op["FAILED"]
            return R
        f = pg.evaluate(FOCUS_IN, [LAYERS[lay]["panel"], "noneditable"])
    R["focus"] = f
    if f.get("err"):
        R["FAILED"] = "放不进焦点：%s" % f["err"]
        return R

    R["before"] = pg.evaluate(TREE)
    R["focusBefore"] = pg.evaluate(DESK)
    selBefore = R["before"].get("selectedIds")
    pg.keyboard.press(key)
    pg.wait_for_timeout(700)
    R["after"] = pg.evaluate(TREE)
    R["focusAfter"] = pg.evaluate(DESK)
    b, a = R["before"], R["after"]
    R["delta"] = {
        "objects": (a.get("objectCount") or 0) - (b.get("objectCount") or 0),
        "nodes": (a.get("nodeCount") or 0) - (b.get("nodeCount") or 0),
    }
    R["selectedBeforeKey"] = selBefore
    R["selectedAfterKey"] = a.get("selectedIds")
    R["objectsDropped"] = R["delta"]["objects"] < 0
    R["selectionCleared"] = bool(selBefore) and not a.get("selectedIds")
    R["restored"] = bool(isUndo and R["delta"]["objects"] > 0)
    R["deskStillOpen"] = pg.evaluate(DESK).get("open")
    return R


def run_round(pg, R):
    R["rows"] = []
    for plan, lay, key in PLANS:
        try:
            r = run_cell(pg, plan, key)
        except Exception as e:
            r = {"plan": plan, "key": key,
                 "FAILED": "%s: %s" % (type(e).__name__, str(e)[:150])}
        r["layer"] = lay
        R["rows"].append(r)


def summarize(R):
    for r in R.get("rows") or []:
        if r.get("FAILED"):
            print("   %-28s FAILED: %s" % (r["plan"], str(r["FAILED"])[:46]))
            continue
        if r["plan"].endswith("undo-noneditable"):
            v = "★ 撤销穿透" if r["restored"] else "撤销没穿透"
        elif r["plan"] == "cam-deletable-control":
            v = ("★ 对照：相机可删（对象 %+d）" % r["delta"]["objects"]
                 if r["objectsDropped"] else
                 "★ 对照：相机**删不掉**（对象 %+d、选中 %s）"
                 % (r["delta"]["objects"], r["selectedAfterKey"]))
        else:
            v = "穿透：对象%+d 选中清空=%s" % (r["delta"]["objects"],
                                              r["selectionCleared"])
        print("   %-28s 落点=%-6s 按前选中=%-26s → %s"
              % (r["plan"], (r.get("focus") or {}).get("tag"),
                 str(r.get("selectedBeforeKey")), v))


def main():
    res = {"batch": 772, "probe": "b",
           "question": "补 preset（772a 的排序 bug）与 pathmenu 的归因，"
                       "外加一个「相机到底可不可删」的对照格",
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
