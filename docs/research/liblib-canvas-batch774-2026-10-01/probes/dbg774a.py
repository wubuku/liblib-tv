#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 774 探针 A —— **问①：D14「修法方向①」够不够？**（注入对照，不改 `src/`）

## 为什么用注入，而不是改源码

方向① 说的是「把 `isEditable` 那道早退的判据，从**按标签名**换成**按浮层**」。
那是 `src/` 改动，需要授权。**但方向① 的真正论断不是「谓词该怎么写」，
而是「那道守卫一旦在浮层后代上触发，D14 的全部可见后果就没了」**——
后者可以在运行时注入验证，一行 `src/` 都不用动。

**所以本探针验的是充分性，不是识别性**（识别性必须改 `src/`，攒为拍板项）。
这个区分是本批最要紧的一句，不能含糊过去。

## 注入怎么做，才算忠实

桌内那个处理器的判据（`DirectorDesk.tsx:474-479` 现读）：

    isEditable = target instanceof HTMLElement && (
      target.isContentEditable || tagName ∈ {INPUT, TEXTAREA, SELECT})

要让它在**非可编辑**落点上触发，只有 `isContentEditable` 这一条路。两个变体：

| 变体 | 注入 | 代表什么 |
| --- | --- | --- |
| **α** | 只给**落点元素本身** `contentEditable="true"` | 最小手术：同一个 `event.target`、同一道守卫，只改判据的**输入** |
| **β** | 给**浮层根** `contentEditable="true"`，靠 `isContentEditable` 沿 DOM 继承 | **方向① 的真实形状**（整层一个谓词） |

α 验充分性；β 额外验两件事：**继承到底成不成立**（浏览器行为，不靠猜），
以及 β **会不会过宽**（可编辑落点上 β 应当与现状一致）。

★ **`isContentEditable` 的继承是本探针唯一的浏览器行为假设**，
所以间谍把 `event.target.isContentEditable` 一起记下来——它是**守卫的输入值**，
连同 `defaultPrevented` 一起读，就能把「守卫有没有真的触发」变成直接读数，
而不是从「东西有没有被删」反推（R97）。

## 读数为什么不被污染

1. 间谍注册在 window **冒泡**阶段、且是**开完浮层之后**才装的 ⟹ 排在
   桌内那个处理器（挂载时注册）**之后** ⟹ 读到的 `dp` 已包含桌内那次。
2. `contentEditable` **不改任何监听器** ⟹ 不影响键投递。
3. **中性键 `F2`**：桌内只处理 Escape / Meta+C,V,Z,Y / Delete / Backspace，
   F2 不在其中 ⟹ 注入臂下必须仍读到 `dp=false`。这一格是
   「注入没把键投递本身弄坏」的证据（R86）。
4. **每格都先验注入真的生效**（`isContentEditable === true`），没生效就记
   `injectionSilent` ⟹ **不算结果**（R99：45 格全读成 `None` 那一版）。

## 格子

| 臂 | 注入 | 落点 | 键 | 格数 |
| --- | --- | --- | --- | --- |
| 臂 A 基线 | 无 | 浮层内第一个**不可编辑**控件 | `Delete` | 6 |
| 臂 B | α（落点元素） | 同上 | `Delete` / `Backspace` / `Meta+z` / `Meta+c` / `Meta+v` | 6 × 5 = 30 |
| 臂 C | β（浮层根） | 同上 | `Delete` | 6 |
| 臂 D 中性 | α | 同上 | `F2`（桌内不处理） | 6 |
| 臂 E | β | 浮层内第一个**可编辑**控件 | `Delete` | 3 |

臂 A 是**同会话基线**：不是引用 773 的历史读数，而是当场再测一遍——
否则 774 就是在用一个可能已经坏掉的读数方法去验 773 的结论（R99 的同族）。

## 边界

**只点**对象树的行、6 个 disclosure 触发器、**选中**相机；
**不点**提交/连接/添加，更不做付费或真实生图生视频。间谍是**纯读**
（只加监听器 + 只写 `contentEditable` 属性，不改任何业务逻辑）。
"""
import json
import pathlib
from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
LS_KEY = "liblib-tv-director-project-v1"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch774-2026-10-01/raw/vb774a.json")
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

# ★ 变体 α：只给**落点元素本身**打 contentEditable —— 同一个 event.target、
#   同一道守卫，只改判据的输入。返回注入**是否真的生效**。
INJECT_ALPHA = """()=>{const a=document.activeElement;
  if(!a||a===document.body) return {err:'no active element'};
  const tagBefore=a.tagName, ceBefore=!!a.isContentEditable;
  a.setAttribute('contenteditable','true');
  const ceAfter=!!a.isContentEditable;
  return {variant:'alpha', tagBefore:tagBefore, ceBefore:ceBefore,
    ceAfter:ceAfter, took:ceAfter&&!ceBefore,
    stillFocused:document.activeElement===a};}"""

# ★ 变体 β：给**浮层根**打 contentEditable —— 方向① 的真实形状
#   （整层一个谓词）。`isContentEditable` 沿 DOM 继承，所以落点也该变成 true；
#   **这条继承是本探针唯一的浏览器行为假设**，返回值里必须能看出来。
INJECT_BETA = """(panelSel)=>{const d=document.querySelector(
    '[role="dialog"][aria-modal="true"]'); if(!d) return {err:'no dialog'};
  const p=d.querySelector(panelSel); if(!p) return {err:'no panel'};
  const a=document.activeElement;
  const ceBefore=!!(a&&a.isContentEditable);
  p.setAttribute('contenteditable','true');
  return {variant:'beta', rootCE:!!p.isContentEditable,
    activeCE:!!(a&&a.isContentEditable), ceBefore:ceBefore,
    took:!!(a&&a.isContentEditable)&&!ceBefore,
    inPanel:!!(a&&p.contains(a)),
    stillFocused:!!a&&document.activeElement===a};}"""

# ★ 中性键：桌内那个处理器**只处理** Escape / Meta+C,V,Z,Y / Delete / Backspace。
#   F2 不在其中 ⟹ 注入臂下必须仍读到 defaultPrevented=false。
NEUTRAL_KEY = "F2"

# ★ 间谍：window 冒泡阶段，**开完浮层之后**才注册 ⟹ 排在桌内那个之后。
#   `targetCE` 是**守卫的输入值**——它与 `dp` 一起把「守卫有没有真的触发」
#   变成直接读数，而不是从副作用反推。
SPY = """()=>{if(window.__spyOn) return {already:1};
 window.__spyOn=1; window.__spyLog=[];
 window.addEventListener('keydown', function(e){
   const t=e.target;
   window.__spyLog.push({key:e.key, code:e.code, meta:e.metaKey||e.ctrlKey,
     shift:e.shiftKey, dp:e.defaultPrevented,           // ★ 桌内分支有没有跑
     targetCE:!!(t&&t.isContentEditable),               // ★ 守卫的输入值
     targetTag:t&&t.tagName,
     targetType:t&&t.getAttribute&&t.getAttribute('type')});
 }, false);
 return {installed:true, now:window.__spyLog.length};}"""

SPY_READ = """()=>{const v=window.__spyLog||[]; window.__spyLog=[]; return v;}"""

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


def run_cell(pg, d, arm, want, key):
    R = {"id": d["id"], "arm": arm, "want": want, "key": key}
    r = fresh(pg)
    if r.get("FAILED"):
        R["FAILED"] = "导演台没开"
        return R
    # preset/pathmenu 必须用相机（773 已证相机删不掉 ⟹ 只能靠间谍判分支）；
    # 其余四层用一个**可删**对象，让「副作用」与「分支」两个信号都能读。
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
    f = pg.evaluate(FOCUS_IN, [d["panel"], want])
    R["focus"] = f
    if f.get("err"):
        R["FAILED"] = "放不进焦点：%s" % f["err"]
        return R
    if arm == "neutral":
        R["key"] = NEUTRAL_KEY
    # ── 注入：**先验生效**，没生效就记 injectionSilent，不算结果（R99）
    R["inject"] = None
    if arm in ("alpha", "neutral"):
        R["inject"] = pg.evaluate(INJECT_ALPHA)
    elif arm == "beta":
        R["inject"] = pg.evaluate(INJECT_BETA, d["panel"])
    if R["inject"] is not None:
        inj = R["inject"]
        if inj.get("err"):
            R["FAILED"] = "注入没做上：%s" % inj["err"]
            return R
        # ★ 注入必须真的把守卫的输入翻成 true，否则这一格**不能算结果**
        if not inj.get("took"):
            R["injectionSilent"] = True
        if not inj.get("stillFocused"):
            R["focusMovedByInject"] = True
    # ── 装间谍（开完浮层之后 ⟹ 注册晚于桌内那个处理器）
    R["spy"] = pg.evaluate(SPY)
    pg.evaluate(SPY_READ)                       # 清空
    R["before"] = pg.evaluate(TREE)
    R["focusBefore"] = pg.evaluate(DESK)
    pg.keyboard.press(R["key"])
    pg.wait_for_timeout(450)
    log = pg.evaluate(SPY_READ)
    R["spyLog"] = log
    R["after"] = pg.evaluate(TREE)
    R["focusAfter"] = pg.evaluate(DESK)
    hits = [x for x in log if x.get("key")]
    R["eventsSeen"] = len(hits)
    # ★ 取最后一个事件：press("Meta+z") 会发两个 keydown（Meta 自己 + 字母），
    #   最后一个才是字母键那个。
    last = hits[-1] if hits else None
    R["defaultPrevented"] = last.get("dp") if last else None
    R["targetCE"] = last.get("targetCE") if last else None
    R["targetTag"] = last.get("targetTag") if last else None
    R["dpAll"] = [x.get("dp") for x in hits]
    R["ceAll"] = [x.get("targetCE") for x in hits]
    R["keysSeen"] = [x.get("key") for x in hits]
    R["objectsDelta"] = ((R["after"].get("objectCount") or 0)
                         - (R["before"].get("objectCount") or 0))
    R["selectedDelta"] = len(R["after"].get("selectedIds") or []) - len(
        R["before"].get("selectedIds") or [])
    R["deskStillOpen"] = pg.evaluate(DESK).get("open")
    R["panelStillOpen"] = pg.evaluate(STATE, [d["panel"]]).get("panelPresent")
    if not hits:
        R["FAILED"] = "间谍一个 keydown 都没收到 —— 读数不算数"
    return R


def run_round(pg, R):
    R["rows"] = []

    def add(arm, want, keys, layers=None):
        for d in DISCLOSURES:
            if layers is not None and d["id"] not in layers:
                continue
            if want == "editable" and d["id"] not in HAS_EDITABLE:
                R["rows"].append({"id": d["id"], "arm": arm, "want": want,
                                  "SKIPPED": "该浮层没有可编辑控件"})
                continue
            for key in keys:
                try:
                    r = run_cell(pg, d, arm, want, key)
                except Exception as e:
                    r = {"id": d["id"], "arm": arm, "want": want, "key": key,
                         "FAILED": "%s: %s" % (type(e).__name__, str(e)[:150])}
                R["rows"].append(r)
                if pg.evaluate(DESK).get("open") is not True:
                    R.setdefault("deskGoneAfter", []).append(
                        "%s/%s/%s" % (d["id"], arm, key))

    # 臂 A 基线：不注入，按 Delete —— 当场复现 773 的 dp=true
    add("base", "noneditable", ["Delete"])
    # 臂 B：α 注入，五个破坏性/编辑类键全跑
    add("alpha", "noneditable", [k for _l, k in KEYS])
    # 臂 C：β 注入（方向① 的真实形状），验继承 + 验不过宽
    add("beta", "noneditable", ["Delete"])
    # 臂 D 中性对照：α 注入 + 桌内不处理的 F2
    add("neutral", "noneditable", ["Delete"])
    # 臂 E：β 注入落在**可编辑**控件上 ⟹ 守卫本来就该触发，β 不应改变结果
    add("beta", "editable", ["Delete"], layers=HAS_EDITABLE)


def summarize(R):
    for r in R.get("rows") or []:
        if r.get("SKIPPED"):
            continue
        if r.get("FAILED"):
            print("   %-10s %-8s %-11s %-10s FAILED: %s"
                  % (r["id"], r["arm"], r["want"], r["key"],
                     str(r["FAILED"])[:40]))
            continue
        print("   %-10s %-8s %-11s %-10s 落点=%-6s targetCE=%-5s dp=%-5s"
              " 键流=%-16s Δ对象=%+d 桌=%s 层=%s%s"
              % (r["id"], r["arm"], r["want"], r["key"],
                 (r.get("focus") or {}).get("tag"), r.get("targetCE"),
                 r.get("defaultPrevented"), r.get("keysSeen"),
                 r.get("objectsDelta"),
                 "开" if r.get("deskStillOpen") else "关",
                 "开" if r.get("panelStillOpen") else "关",
                 "  ★注入没生效" if r.get("injectionSilent") else ""))


def main():
    res = {"batch": 774, "probe": "a",
           "question": "问①：D14「修法方向①」够不够？—— 注入 contentEditable 让"
                       "既有守卫在浮层后代上真的触发，**不改 src/**",
           "whatThisProves": "验的是**充分性**（「守卫一旦触发，D14 的可见后果"
                             "就没了」），**不是识别性**（「谓词该不该这么写」"
                             "——那要改 src/，攒为拍板项）",
           "spyDesign": "★ 间谍注册在 window **冒泡**阶段、且是**开完浮层之后**"
                        "才装的 ⟹ 排在桌内那个处理器之后；同时记 "
                        "`target.isContentEditable`（**守卫的输入值**）与 "
                        "`defaultPrevented` ⟹ 「守卫有没有真的触发」是直接读数，"
                        "不是从副作用反推（R97）",
           "injectionHonesty": "★ α = 只给落点元素打 contentEditable（同一 target、"
                               "同一守卫、只改输入）；β = 给浮层根打、靠 "
                               "isContentEditable 沿 DOM 继承（方向① 的真实形状）。"
                               "**继承是本探针唯一的浏览器行为假设**，所以每格都先验 "
                               "took=true，没生效记 injectionSilent 且**不算结果**（R99）",
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
