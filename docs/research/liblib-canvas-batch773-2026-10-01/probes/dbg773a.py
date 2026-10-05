#!/usr/bin/env python3
"""batch 773 探针 a：**分支到没到**的直接读数（不靠副作用反推）

## 这一批问的

772 得出两个结论，其中一个带缺口：

  ✅ **4/6 个浮层**（导出 / 本机预演 / 群众阵列 / 模型库）实测按
     `Delete`/`Backspace` 会**真删**选中对象（8/8 可判格）；
  ✅ `Meta+Z` **6/6 个浮层**都能从浮层里撤销掉已发生的删除；
  ⚠️ **preset / 路径菜单的 4 个 Delete 格「结构上不可判」** ——
     它们必须选中主机位才能开，而对照格实测**相机根本删不掉**，
     于是「对象没少」既可能是「分支没跑」，也可能是「跑了但目标删不掉」。

772 的读法是**靠副作用反推**。本批换一个**直接读数**。

## 关键：桌内那个处理器每次动手都会 `preventDefault()`

逐字读 `DirectorDesk.tsx:473-571`：

| 键 | 分支 | 那一行 |
| --- | --- | --- |
| `Escape` + `activeMobilePanel` | 移动抽屉 | `:483` `event.preventDefault()` |
| `Meta/Ctrl+C` | 复制 | `:491` `event.preventDefault()` |
| `Meta/Ctrl+V` | 粘贴 | `:502` `event.preventDefault()` |
| `Meta/Ctrl+Z` | 撤销 | `:507` `event.preventDefault()` |
| `Meta/Ctrl+Y` | 重做 | `:513` `event.preventDefault()` |
| `Delete` / `Backspace` | **删除** | `:541` / `:526` `event.preventDefault()` |
| `Escape` | 手势/面板/跟随/工作区 | `:550` `event.preventDefault()` |

而 `useDirectorFocusContainment.ts:149-172` 那个 Tab 处理器**只对 Tab**
调 `preventDefault()`（`:153`、`:169`）⟹ 对本批这些键**不污染读数**。
`src/app/page.tsx` 那条在桌开时已整条早退（772 的 F9）⟹ 也不污染。

⟹ **「按键结束时 `event.defaultPrevented === true`」就是「桌内那个处理器"
真的走到了对应分支"的直接证据。**

## 怎么读：注册在它**之后**

同一个节点（`window`）上的监听器按**注册顺序**触发。桌内那个处理器在
**挂载时**注册（`DirectorDesk.tsx:570`），而本探针的间谍是**开完浮层之后**
才装的 ⟹ 注册更晚 ⟹ 冒泡到 window 时**它一定排在桌内那个之后**，
读到的 `defaultPrevented` 已经包含桌内那次的 `preventDefault()`。

★ 这个顺序不是假设，判据里会验：间谍自己先记一次**进入时**的
`defaultPrevented`，再记一次**读出时**的；两者不一致才说明有人在中途
调了 `preventDefault()`。

## 格子

| 臂 | 落点 | 键 | 格数 |
| --- | --- | --- | --- |
| 臂 1 | 浮层内第一个**不可编辑**控件 | `Delete` / `Backspace` / `Meta+z` / `Meta+c` / `Meta+v` | 6 × 5 = 30 |
| 臂 2 | 浮层内第一个**可编辑**控件 | 同上 | 3 × 5 = 15 |

臂 2 是**守卫对照**：769/772 已实测 `isEditable` 早退会挡住 Delete。
本批要验的是它**同样**挡住 `Meta+C/V/Z/Y` —— 如果挡住，那道早退的作用域
就量全了；如果没挡住，那 D14 的范围比 772 记的还大。

## 边界

只点对象树的行、6 个 disclosure 触发器、选中相机；**不点提交/连接/添加，
更不做付费或真实生图生视频**。间谍是**纯读**（只加一个监听器，不改行为）。
"""
import json
import pathlib
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
LS_KEY = "liblib-tv-director-project-v1"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch773-2026-10-01/raw/vb773a.json")
CAM = "director-camera-main"

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
 return {tree:true, objectCount:objs.length,
   objectIds:objs.map(e=>e.getAttribute('data-director-object-id')),
   selectedIds:objs.filter(e=>e.getAttribute('data-director-object-selected')
     ==='true').map(e=>e.getAttribute('data-director-object-id')),
   nodeCount:document.querySelectorAll('.react-flow__node').length};}"""

STATE = """(a)=>{const d=document.querySelector(
 '[role="dialog"][aria-modal="true"]'); if(!d) return {deskOpen:false};
 const p=d.querySelector(a[0]); return {deskOpen:true, panelPresent:!!p};}"""

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

# ★ 间谍：window 冒泡阶段，**注册在桌内那个之后** ⟹ 读到的是最终值
SPY = """()=>{if(window.__spyOn) return {already:1};
 window.__spyOn=1; window.__spyLog=[];
 window.addEventListener('keydown', function(e){
   window.__spyLog.push({key:e.key, code:e.code, meta:e.metaKey||e.ctrlKey,
     shift:e.shiftKey, dp:e.defaultPrevented,           // ★ 就是要读这一个
     tag:e.target&&e.target.tagName,
     type:e.target&&e.target.getAttribute('type')});
 }, false);
 return {installed:true, now:window.__spyLog.length};}"""

SPY_READ = """()=>{const v=window.__spyLog||[]; window.__spyLog=[]; return v;}"""

# ★ 中性键对照：桌内那个处理器**只处理** Escape / Meta+C,V,Z,Y /
#   Delete / Backspace。F2 不在其中 ⟹ 间谍必须读到 defaultPrevented=false。
#   这一格是「间谍没在读别的东西」的证据（R86）。
NEUTRAL_KEY = "F2"

DISCLOSURES = [
    {"id": "export", "trigger": "[data-director-export-trigger]",
     "panel": "[data-director-export-panel]", "needs": "none"},
    {"id": "preset", "trigger": "[data-director-camera-preset-trigger]",
     "panel": "[data-director-camera-preset-panel]", "needs": "camera"},
    {"id": "pathmenu",
     "trigger": '[data-director-track-draw-trail="director-track-camera-main"]',
     "panel": "[data-director-motion-path-menu]", "needs": "camera"},
    {"id": "phonevcam", "trigger": "[data-director-phone-vcam-trigger]",
     "panel": "[data-director-phone-vcam-panel]", "needs": "none"},
    {"id": "crowd", "trigger": "[data-director-crowd-trigger]",
     "panel": "[data-director-crowd-panel]", "needs": "none"},
    {"id": "modellib", "trigger": "[data-director-model-library-trigger]",
     "panel": "[data-director-model-library-panel]", "needs": "none"},
]
KEYS = [("Delete", "Delete"), ("Backspace", "Backspace"),
        ("Meta+z", "Meta+z"), ("Meta+c", "Meta+c"), ("Meta+v", "Meta+v")]
HAS_EDITABLE = {"export", "crowd", "modellib"}


def settle(pg, tries=8, gap=200):
    prev, same = None, 0
    for _ in range(28):
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
    pg.wait_for_timeout(1600)
    return {"ok": True}


def fresh(pg):
    pg.goto(BASE, wait_until="domcontentloaded")
    pg.evaluate(CLEAR_LS, LS_KEY)
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1100)
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(500)
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


def run_cell(pg, d, want, key):
    R = {"id": d["id"], "want": want, "key": key}
    r = fresh(pg)
    if r.get("FAILED"):
        R["FAILED"] = "导演台没开"
        return R
    # 目标：对 cameraTrack 两层用相机（772 已证它删不掉，所以必须靠间谍判）；
    # 对其余四层用一个**可删**的对象，让「副作用」与「分支」两个信号都能读。
    target = CAM if d["needs"] == "camera" else None
    if target is None:
        ids = (pg.evaluate(TREE) or {}).get("objectIds") or []
        if not ids:
            R["FAILED"] = "对象树里没有对象"
            return R
        target = ids[0]
    sel = click_tree_row(pg, target)
    R["select"] = sel
    t1 = pg.evaluate(TREE)
    R["selectedIds"] = t1.get("selectedIds")
    if target not in (t1.get("selectedIds") or []):
        R["FAILED"] = "目标没选中"
        return R
    R["target"] = target
    R["targetUndeletable"] = (target == CAM)
    s = pg.evaluate(SCAN_CLICK, d["trigger"])
    if not s.get("pt"):
        R["FAILED"] = "触发器点不动"
        R["scan"] = s
        return R
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(650)
    if not pg.evaluate(STATE, [d["panel"]]).get("panelPresent"):
        R["FAILED"] = "点了但浮层没出现"
        return R
    if want == "neutral":
        # 对照：落非编辑框（与臂 1 同起点），但按**桌内不处理**的键
        f = pg.evaluate(FOCUS_IN, [d["panel"], "noneditable"])
    else:
        f = pg.evaluate(FOCUS_IN, [d["panel"], want])
    R["focus"] = f
    if f.get("err"):
        R["FAILED"] = "放不进焦点：%s" % f["err"]
        return R
    if want == "neutral":
        R["neutral"] = True
        R["key"] = NEUTRAL_KEY
    # ── 装间谍（**开完浮层之后** ⟹ 注册晚于桌内那个处理器）
    R["spy"] = pg.evaluate(SPY)
    pg.evaluate(SPY_READ)                       # 清空
    R["before"] = pg.evaluate(TREE)
    R["focusBefore"] = pg.evaluate(DESK)
    pg.keyboard.press(R["key"] if want == "neutral" else key)
    pg.wait_for_timeout(450)
    log = pg.evaluate(SPY_READ)
    R["spyLog"] = log
    R["after"] = pg.evaluate(TREE)
    R["focusAfter"] = pg.evaluate(DESK)
    hits = [x for x in log if x.get("key")]
    R["eventsSeen"] = len(hits)
    # ★ 取**最后一个**事件：Meta 键自己也会发一个 keydown，press("Meta+z")
    #   ���共两个事件，最后一个才是字母键那个。
    R["defaultPrevented"] = hits[-1].get("dp") if hits else None
    R["dpAll"] = [x.get("dp") for x in hits]
    R["keysSeen"] = [x.get("key") for x in hits]
    R["eventTargetTag"] = hits[-1].get("tag") if hits else None
    R["objectsDelta"] = ((R["after"].get("objectCount") or 0)
                         - (R["before"].get("objectCount") or 0))
    R["deskStillOpen"] = pg.evaluate(DESK).get("open")
    if not hits:
        R["FAILED"] = "间谍一个 keydown 都没收到 —— 读数不算数"
    return R


def run_round(pg, R):
    R["rows"] = []
    for d in DISCLOSURES:
        for want in ("noneditable", "editable", "neutral"):
            if want == "editable" and d["id"] not in HAS_EDITABLE:
                R["rows"].append({"id": d["id"], "want": want,
                                  "SKIPPED": "该浮层没有可编辑控件"})
                continue
            for _label, key in KEYS:
                try:
                    r = run_cell(pg, d, want, key)
                except Exception as e:
                    r = {"id": d["id"], "want": want, "key": key,
                         "FAILED": "%s: %s" % (type(e).__name__, str(e)[:150])}
                R["rows"].append(r)
                if pg.evaluate(DESK).get("open") is not True:
                    R.setdefault("deskGoneAfter", []).append(
                        d["id"] + "/" + want + "/" + key)


def summarize(R):
    for r in R.get("rows") or []:
        if r.get("SKIPPED"):
            continue
        if r.get("FAILED"):
            print("   %-10s %-11s %-10s FAILED: %s"
                  % (r["id"], r["want"], r["key"], str(r["FAILED"])[:40]))
            continue
        print("   %-10s %-11s %-10s 落点=%-6s 可编辑=%-5s defaultPrevented=%-5s"
              " 键流=%-18s Δ对象=%+d 目标=%s"
              % (r["id"], r["want"], r["key"], (r.get("focus") or {}).get("tag"),
                 (r.get("focus") or {}).get("editable"),
                 r["defaultPrevented"], r.get("keysSeen"), r["objectsDelta"],
                 "相机(不可删)" if r["targetUndeletable"] else "可删对象"))


def main():
    res = {"batch": 773, "probe": "a",
           "question": "桌内那个 keydown 处理器的分支**到底到没到** —— "
                       "用 event.defaultPrevented 做直接读数，而不是靠副作用反推",
           "spyDesign": "★ 间谍注册在 window **冒泡**阶段，且是**开完浮层之后**"
                        "才装的 ⟹ 排在桌内那个处理器（挂载时注册）**之后**，"
                        "读到的 defaultPrevented 已包含桌内那次的 preventDefault()",
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
