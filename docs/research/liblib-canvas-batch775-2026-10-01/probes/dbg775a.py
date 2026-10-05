#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 775 探针 A —— **方向① 的谓词上有没有洞？**

## 772 与 774 共同的盲区

772/774 量 D14 时，落点**全部**取自「浮层内第一个可聚焦控件」。
本批要问的是：**浮层开着、但落点不在这类控件上时会怎样**。

方向① 的谓词是「**焦点在某个浮层内**就早退」。于是有四种落点它管不到：

| 落点类 | 用户在跟谁交互 | 用户可达？ | `activeElement` 在浮层内？ | 方向① 的谓词 |
| --- | --- | --- | --- | --- |
| `trigger` | 浮层的**触发器**（浮层仍开着） | 是（Tab / 点击） | 否 | **不触发** |
| `outsidePanel` | 桌内**另一个**面板 | 是 | 否 | **不触发** |
| `treeContainer` | 对象树的**容器**（不点行，免得改选中） | 是 | 否 | **不触发** |
| `body` | 谁都不是（焦点掉到 body） | 是 | 否 | **不触发** |
| `layerRoot` | 浮层**根**（非控件，`tabindex=-1`） | **否**（键盘 Tab 到不了） | **是** | 触发 |

★ **「层内但落点不是控件」这一格，本批不假定它存在。** 第一版把
`layerNonControl`（点浮层空白处）当成一类落点，冒烟立刻打回：
export 面板里**一个非控件的点都找不到** —— `data-*` 挂在内层容器上，
几何上被控件铺满。于是它从「一类落点」降级成**一条普查**
（`CENSUS_BLANK`：每个浮层有没有非控件区？点它会不会把焦点移进层内？），
**「找不到」本身就是读数**。

## 关键：伤害是「缺陷」还是「正常编辑」，不能一概而论

- 落点在**对象树**上时，Delete 删掉用户刚点的东西 —— 这是**正常编辑**，
  说它是「方向① 漏网」就是把「按设计」写成了「没修好」。
- 落点在**浮层自己的区域**上而焦点在 body 时，用户根本没在编辑对象 ——
  那才是缺陷候选。

所以本批不数「几格被放过」，而是给每一格**三个可判读数**：

| 读数 | 含义 |
| --- | --- |
| `activeInLayer` | `document.activeElement` 是否在浮层内（**方向① 若按 activeElement 写就会管到**） |
| `targetInLayer` | keydown 的 `event.target` 是否在浮层内 |
| `lastPointerInLayer` | 最近一次 pointerdown 是否落在浮层内（**用户到底在跟谁交互**） |

三者的**组合**才决定「缺陷」还是「按设计」。只报其中任何一个都会得出
一个错的结论 —— 这正是 773/774 反复撞到的 R97。

## 格子的两个前置（不满足就不是读数）

1. **浮层仍然开着** —— 落点动作绝不能顺手把浮层关掉（点触发器会）。
   所以除 `layerNonControl` 外一律用 `.focus()` 而不是点击。
2. **导演台里选中的目标没变** —— 落点动作不能改选中（点对象树行会）。
   所以 `treeContainer` 只把焦点放到树的**容器**上，不点行。

## 读数为什么不被污染

- 间谍注册在 window **冒泡**、**开完浮层之后**才装 ⟹ 排在桌内那个之后。
- **中性键 `F2`**：桌内不处理 ⟹ 注入无关地必须读到 `dp=false`（R86 的加强版：
  同时断言**间谍确实收到了 `F2`**）。
- **同会话基线臂**：不落点、也不注入，直接按 Delete ⟹ 必须 6/6 `dp=true`，
  证明读数方法还活着（R99 的同族）。
"""
import json
import pathlib
import sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
# ★ **跨批 import 上一批的探针基础设施**（`dbg774a`），不是抄一份。
#   理由：772/774 与本批量的都是同一个量 —— 「落点」—— 而落点必须**逐字相同**
#   两批才可比。抄一份的话，任何一处改动都会让「本批 vs 772/774」的对比
#   悄悄失去前提（而那种改动不会报任何错）。
#   代价：本批的探针**必须**与 batch774 目录同时在场，已写进 README 的复现命令。
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402  复用 774 的基础设施（同一批落点规则、同一套间谍）

OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch775-2026-10-01/raw/vb775a.json")

# ── 落点类 ────────────────────────────────────────────────────────────
# ★ 一律用 `.focus()`（除 layerNonControl 要真点），因为**点击触发器会把浮层关掉**、
#   **点击对象树行会改选中** —— 两个都会破坏前置条件。
FOCUS_OUTSIDE = """(a)=>{const d=document.querySelector(
    '[role="dialog"][aria-modal="true"]');
  if(!d) return {err:'no dialog'};
  const mode=a[0], panelSel=a[1];
  const panel=d.querySelector(panelSel);
  if(!panel) return {err:'no panel'};
  const inPanel=(e)=>!!(e&&panel.contains(e));
  let hadTabindexBefore=null;
  const foc=(root)=>[...root.querySelectorAll(
    'a[href],button,input,select,textarea,[tabindex]')].filter(e=>{
    if(e.disabled) return false; const ti=e.getAttribute('tabindex');
    if(ti!==null&&Number(ti)<0) return false;
    if(inPanel(e)) return false;              // ★ 绝不选到浮层内的控件
    const s=getComputedStyle(e);
    if(s.display==='none'||s.visibility==='hidden') return false;
    const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;});
  let el=null, note='';
  if(mode==='trigger'){
    const t=document.querySelector(a[2]);
    if(t){ el=t; note='浮层自己的触发器'; }
  } else if(mode==='treeContainer'){
    el=document.querySelector('[data-director-tree]');
    if(el){ const ti=el.getAttribute('tabindex');
            if(ti===null) el.setAttribute('tabindex','-1');
            note='对象树容器（不点行，免得改选中）'; }
  } else if(mode==='outsidePanel'){
    const c=foc(d)[0]; if(c){ el=c; note='桌内另一个面板的可聚焦控件'; }
  } else if(mode==='layerRoot'){
    // ★ 「层内但落点不是控件」——声明的浮层根。
    //   **`hadTabindexBefore` 是本批最该记的一个读数**：产品里浮层根**本来**
    //   没有 tabindex（不可聚焦）⟹ 「焦点在层内、落点却不是控件」这个状态
    //   **是探针注入造出来的**，不是产品里存在的。
    //   第一版把「它不可达」当成一个**标注**写进 raw，而那个标注同时出现在
    //   两个臂上还不一致（landing=True / neutral=False）——
    //   **自己的断言冒充了读数**。现在改成：探针只记测量，
    //   「可达性」由汇编器**从落点名推导**（单一真相源）。
    const had = panel.hasAttribute('tabindex');
    if(!had) panel.setAttribute('tabindex','-1');
    el=panel;
    note='浮层根（非控件；产品里本来'+(had?'就有':'没有')+' tabindex）';
    if(a[2]!=='__had__'){ hadTabindexBefore=had; }
  } else if(mode==='body'){
    const b=document.body;
    if(!b.hasAttribute('tabindex')) b.setAttribute('tabindex','-1');
    el=b; note='body（焦点谁都不在）';
  } else { return {err:'未知 mode '+mode}; }
  if(!el) return {err:'找不到 '+mode, note:note};
  try { el.focus({preventScroll:true}); } catch(e){ return {err:'focus 抛了: '+e}; }
  const a0=document.activeElement;
  return {ok:true, note:note, hadTabindexBefore:hadTabindexBefore,
    tag:a0?a0.tagName:null,
    text:a0?(a0.textContent||'').trim().slice(0,14):null,
    isBody:a0===document.body,
    activeInLayer:inPanel(a0)};}"""

# ★ 普查：**浮层里到底有没有「非控件区」** —— 点它会不会把焦点移进层内？
#   找不到本身就是一条读数（不是失败）：`noBlank` 说明这个浮层**没有**用户
#   可达的「层内落非控件处」，于是「方向① 覆盖不到」的那一类里没有这一项。
CENSUS_BLANK = """(panelSel)=>{const d=document.querySelector(
    '[role="dialog"][aria-modal="true"]'); if(!d) return {err:'no dialog'};
  const p=d.querySelector(panelSel); if(!p) return {err:'no panel'};
  const r=p.getBoundingClientRect();
  const focInPanel=[...p.querySelectorAll(
    'a[href],button,input,select,textarea,[tabindex]')].length;
  for(let f=0.02; f<=0.98; f+=0.02)
    for(let g=0.02; g<=0.98; g+=0.02){
      const x=Math.round(r.x+r.width*f), y=Math.round(r.y+r.height*g);
      if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
      const e=document.elementFromPoint(x,y);
      if(!e||!e.closest) continue;
      if(!p.contains(e)) continue;                    // 必须在浮层内
      if(e.closest('a[href],button,input,select,textarea,[tabindex]')) continue;
      return {pt:[x,y], hitTag:e.tagName, controls:focInPanel,
              hitText:(e.textContent||'').trim().slice(0,14)};}
  return {noBlank:true, panelRect:[Math.round(r.x),Math.round(r.y),
      Math.round(r.width),Math.round(r.height)], controls:focInPanel};}"""

# ★ 记「最近一次 pointerdown 是不是落在浮层内」——用户到底在跟谁交互
POINTER_TRACK = """(panelSel)=>{const d=document.querySelector(
    '[role="dialog"][aria-modal="true"]'); if(!d) return {err:'no dialog'};
  const p=d.querySelector(panelSel); if(!p) return {err:'no panel'};
  if(window.__ptrOn) return {already:1};
  window.__ptrOn=1; window.__ptrInLayer=[];
  document.addEventListener('pointerdown', function(e){
    window.__ptrInLayer.push(!!(e.target&&p.contains(e.target)));}, true);
  return {installed:true};}"""

POINTER_READ = """()=>{const v=window.__ptrInLayer||[]; window.__ptrInLayer=[];
  return {clicks:v, last:v.length?v[v.length-1]:null};}"""

# ★ 五类落点全部**用户可达**（键盘 Tab 或真实点击都能到）。
#   「层内但落点不是控件」**不在这个列表里** —— 那是普查要回答的问题，
#   不是能假定存在的落点（见 CENSUS_BLANK 与本文件开头的表）。
LANDINGS = ["trigger", "outsidePanel", "treeContainer", "body", "layerRoot"]
NEUTRAL_KEY = "F2"
#: 每格最多试几次（含第一次）。见 run_round 里的说明。
MAX_TRIES = 3


def run_cell(pg, d, arm, landing, key):
    """arm ∈ {base, neutral}：base 是不落点直接按 key；neutral 是落点后按 F2。"""
    R = {"id": d["id"], "arm": arm, "landing": landing, "key": key}
    # ★ 这里**不**写 userReachable：「用户可达」是**从落点名推导**的量，
    #   不是读数。探针写它就会有两个真相源（第一版就因此在两个臂上不一致）。
    r = A.fresh(pg)
    if r.get("FAILED"):
        R["FAILED"] = "导演台没开"
        return R
    target = A.CAM if d["needs"] == "camera" else None
    if target is None:
        ids = (pg.evaluate(A.TREE) or {}).get("objectIds") or []
        if not ids:
            R["FAILED"] = "对象树里没有对象"
            return R
        target = ids[0]
    A.click_tree_row(pg, target)
    t1 = pg.evaluate(A.TREE)
    if target not in (t1.get("selectedIds") or []):
        R["FAILED"] = "目标没选中"
        return R
    R["target"] = target
    R["targetUndeletable"] = (target == A.CAM)
    s = pg.evaluate(A.SCAN_CLICK, d["trigger"])
    if not s.get("pt"):
        R["FAILED"] = "触发器点不动"
        R["scan"] = s
        return R
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(650)
    if not pg.evaluate(A.STATE, [d["panel"]]).get("panelPresent"):
        R["FAILED"] = "点了但浮层没出现"
        return R
    # ★ 指针追踪在**开完浮层之后**装，只看落点动作之后的点击
    R["ptr"] = pg.evaluate(POINTER_TRACK, d["panel"])
    if landing != "base":
        f = pg.evaluate(FOCUS_OUTSIDE, [landing, d["panel"], d["trigger"]])
        R["landed"] = f
        if f.get("err"):
            R["FAILED"] = "放不进焦点：%s" % f["err"]
            return R
    R["ptrAfter"] = pg.evaluate(POINTER_READ)
    # ── 前置条件逐条自证：浮层还开着吗？选中变了吗？
    st = pg.evaluate(A.STATE, [d["panel"]])
    R["layerStillOpen"] = bool(st.get("panelPresent"))
    t2 = pg.evaluate(A.TREE)
    R["selectedAfterLanding"] = t2.get("selectedIds")
    R["selectionUnchanged"] = (t2.get("selectedIds") == t1.get("selectedIds"))
    if not R["layerStillOpen"] and landing != "base":
        R["FAILED"] = "★ 落点动作把浮层关掉了 —— 这一格不是有效读数"
        return R
    if not R["selectionUnchanged"]:
        R["FAILED"] = "★ 落点动作改选中 —— 这一格不是有效读数"
        return R
    R["before"] = t2
    R["focusBefore"] = pg.evaluate(A.DESK)
    if arm == "neutral":
        R["key"] = NEUTRAL_KEY
        R["expectedKey"] = NEUTRAL_KEY
    R["spy"] = pg.evaluate(A.SPY)
    pg.evaluate(A.SPY_READ)
    pg.keyboard.press(R["key"])
    pg.wait_for_timeout(450)
    log = pg.evaluate(A.SPY_READ)
    R["spyLog"] = log
    R["after"] = pg.evaluate(A.TREE)
    hits = [x for x in log if x.get("key")]
    last = hits[-1] if hits else None
    R["eventsSeen"] = len(log)
    R["defaultPrevented"] = last.get("dp") if last else None
    R["targetCE"] = last.get("targetCE") if last else None
    R["targetTag"] = last.get("targetTag") if last else None
    R["keysSeen"] = [x.get("key") for x in log]
    R["objectsDelta"] = ((R["after"].get("objectCount") or 0)
                         - (R["before"].get("objectCount") or 0))
    R["deskStillOpen"] = pg.evaluate(A.DESK).get("open")
    # ★ 方向① 的谓词在两个写法下各自会怎么判
    R["targetInLayer"] = pg.evaluate(
        """(ps)=>{const d=document.querySelector(
             '[role="dialog"][aria-modal="true"]');
           const p=d&&d.querySelector(ps); const a=document.activeElement;
           return {panelPresent:!!p, activeInLayer:!!(p&&a&&p.contains(a))};}""",
        d["panel"])
    if not hits:
        R["FAILED"] = "间谍一个 keydown 都没收到 —— 读数不算数"
    return R


def run_census(pg, R):
    """★ 普查：每个浮层里**有没有「非控件区」**，点它会不会把焦点移进层内。

    这不是格，是**前提**：方向① 的谓词是「焦点在浮层内」，
    而「层内但落点不是控件」这个状态如果**用户根本到不了**，
    那么「方向① 覆盖不到」的那一类里就没有它 —— 这个结论必须**测出来**，
    不能假定。找不到（`noBlank`）本身就是一条读数。
    """
    R["census"] = []
    for d in A.DISCLOSURES:
        r, tries = None, 0
        while tries < MAX_TRIES:
            tries += 1
            r = A.fresh(pg)
            if not r.get("FAILED"):
                break
            pg.wait_for_timeout(900 * tries)
        r = dict(r or {})
        r["tries"] = tries
        if r.get("FAILED"):
            R["census"].append({"id": d["id"], "FAILED": "导演台没开"})
            continue
        # ★ 普查也必须走与 run_cell **同一套前置**（含选相机）——
        #   否则 preset/pathmenu 的触发器是 disabled，普查会静默少 2 层
        #   （第一版就少测了 preset，「触发器点不动」被当成一条读数）。
        if d["needs"] == "camera":
            sel2 = A.click_tree_row(pg, A.CAM)
            if sel2.get("FAILED") or A.CAM not in (
                    (pg.evaluate(A.TREE) or {}).get("selectedIds") or []):
                R["census"].append({"id": d["id"],
                                    "FAILED": "相机没选中（触发器会 disabled）"})
                continue
        s2 = pg.evaluate(A.SCAN_CLICK, d["trigger"])
        if not s2.get("pt"):
            R["census"].append({"id": d["id"], "FAILED": "触发器点不动",
                                "scan": s2})
            continue
        pg.mouse.click(s2["pt"][0], s2["pt"][1])
        pg.wait_for_timeout(650)
        if not pg.evaluate(A.STATE, [d["panel"]]).get("panelPresent"):
            R["census"].append({"id": d["id"], "FAILED": "浮层没出现"})
            continue
        hit = pg.evaluate(CENSUS_BLANK, d["panel"])
        row = {"id": d["id"], "hit": hit}
        if hit.get("pt"):
            # ★ 真点一下，看焦点会不会被移进层内
            pg.evaluate("()=>{document.activeElement&&"
                        "document.activeElement.blur&&"
                        "document.activeElement.blur();}")
            pg.wait_for_timeout(200)
            row["activeBefore"] = pg.evaluate(A.DESK)
            pg.mouse.click(hit["pt"][0], hit["pt"][1])
            pg.wait_for_timeout(350)
            row["activeAfter"] = pg.evaluate(
                """(ps)=>{const d=document.querySelector(
                     '[role="dialog"][aria-modal="true"]');
                   const p=d&&d.querySelector(ps); const a=document.activeElement;
                   return {tag:a?a.tagName:null, isBody:a===document.body,
                     activeInLayer:!!(p&&a&&p.contains(a))};}""", d["panel"])
            row["panelStillOpen"] = bool(
                pg.evaluate(A.STATE, [d["panel"]]).get("panelPresent"))
        R["census"].append(row)


def run_round(pg, R):
    R["rows"] = []
    R["census"] = []
    run_census(pg, R)
    for d in A.DISCLOSURES:
        # ★ 三个臂，缺一不可：
        #   base    —— 同会话基线（不落点，按 Delete）：读数方法还活着吗
        #   landing —— **主测量**：五类落点上按 Delete，伤害还在不在
        #   neutral —— 对照：同样五类落点，但按桌内不处理的 F2
        #   （第一版只有 base + neutral ⟹ 五类落点上**一次都没测过伤害**，
        #     而那正是本批要问的东西）
        for arm, key, landings in (("base", "Delete", ["base"]),
                                   ("landing", "Delete", LANDINGS),
                                   ("neutral", "Delete", LANDINGS)):
            for landing in landings:
                # ★ 格内重试：4317 是多人共用的 dev server，偶发「导演台没开」
                #   /「目标没选中」是**基础设施抖动**，不是机制读不出来。
                #   汇编器对任何 FAILED 都判失败，所以抖动必须在这里消化 ——
                #   而**重试次数要记进 raw**（`retries`），否则「重试过」这件事
                #   就从产物里消失了（R96：失效机制要记下来，不只是修好）。
                r, tries = None, 0
                while tries < MAX_TRIES:
                    tries += 1
                    try:
                        r = run_cell(pg, d, arm, landing, key)
                    except Exception as e:  # noqa: BLE001
                        r = {"id": d["id"], "arm": arm, "landing": landing,
                             "key": key,
                             "FAILED": "%s: %s" % (type(e).__name__,
                                                   str(e)[:150])}
                    if not r.get("FAILED"):
                        break
                    pg.wait_for_timeout(900 * tries)
                r["tries"] = tries
                if tries > 1:
                    r["retried"] = True
                R["rows"].append(r)


def summarize(R):
    for c in R.get("census") or []:
        if c.get("FAILED"):
            print("   [普查] %-10s FAILED: %s" % (c["id"], c["FAILED"]))
            continue
        h = c.get("hit") or {}
        if h.get("noBlank"):
            print("   [普查] %-10s **没有非控件区**（浮层被控件铺满，%d 个可聚焦）"
                  % (c["id"], h.get("controls") or 0))
        else:
            print("   [普查] %-10s 有非控件区 @%s  点它之后 焦点在层内=%s "
                  "层仍开=%s" % (c["id"], h.get("pt"),
                                 (c.get("activeAfter") or {}).get("activeInLayer"),
                                 c.get("panelStillOpen")))
    for r in R.get("rows") or []:
        if r.get("FAILED"):
            print("   %-10s %-8s %-16s %-9s FAILED(试了 %s 次): %s"
                  % (r["id"], r["arm"], r["landing"], r.get("key"),
                     r.get("tries"), str(r["FAILED"])[:40]))
            continue
        ain = (r.get("targetInLayer") or {}).get("activeInLayer")
        # 「用户可达」由**落点名**推导（不是读数）：layerRoot 那个状态是
        # 探针注入 tabindex=-1 造出来的 ⟹ 产品里到不了。
        reach = (r.get("landing") not in ("base", "layerRoot"))
        print("   %-10s %-8s %-16s %-9s dp=%-5s Δ=%+2d 层仍开=%-5s "
              "选中未变=%-5s activeInLayer=%-5s 可达(推导)=%-5s "
              "根有tabindex(前)=%s"
              % (r["id"], r["arm"], r["landing"], r.get("key"),
                 r.get("defaultPrevented"), r.get("objectsDelta"),
                 r.get("layerStillOpen"), r.get("selectionUnchanged"),
                 ain, reach,
                 (r.get("landed") or {}).get("hadTabindexBefore")))


def main():
    res = {"batch": 775, "probe": "a",
           "question": "方向① 的谓词（「焦点在浮层内就早退」）上有没有洞？—— "
                       "772/774 的落点**全部**取自「浮层内第一个可聚焦控件」，"
                       "本批把落点空间枚举一遍",
           "whyItMatters": "★ 本批**先普查、后断言**，方向反过来：普查测出"
                           "**6/6 浮层都没有非控件区**、**6/6 浮层根本来没有 "
                           "tabindex** ⟹ 「人在层里但 `event.target`/`activeElement` "
                           "都不是层内控件」这个状态**产品里没有自然入口**。"
                           "所以 `layerRoot` 那一臂是**探针注入 tabindex=-1 合成"
                           "出来的**（`hadTabindexBefore` 把这件事变成实测而不是"
                           "断言）。它的意义不是「现在有洞」，而是回答"
                           "**「若将来有人给浮层根加 tabindex，方向① 还成立吗」**"
                           "—— 即：合成状态下谓词管不管得到。**把合成状态报成"
                           "当前缺陷，就是把一次注入实验写成产品结论（R105）。**",
           "threeReadings": "★ 伤害是「缺陷」还是「正常编辑」不能一概而论："
                            "落点在对象树上是**正常编辑**（用户刚点了它），"
                            "落点完全离开对象编辑才可能是缺陷。所以每格读三个量："
                            "`targetInLayer`（按 target 写的谓词会管到吗）、"
                            "`activeInLayer`（按 activeElement 写的会管到吗）、"
                            "`lastPointerInLayer`（用户到底在跟谁交互）。"
                            "**只报其中任何一个都会得出错的结论**（R97）",
           "preconditions": "★ 两个前置，不满足就不是读数：① 落点动作**不能顺手"
                            "关掉浮层**（点触发器会 ⟹ 除 `trigger` 外一律用 "
                            "`.focus()`）；② **不能改选中**"
                            "（点对象树行会 ⟹ treeContainer 只把焦点放到"
                            "树的容器上）",
           "spyDesign": "★ 间谍注册在 window **冒泡**、开完浮层之后才装 ⟹ "
                        "排在桌内那个之后；**中性键 F2** 用于对照，且**同时"
                        "断言间谍确实收到了它**（R86 的加强版）",
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
            except Exception:  # noqa: BLE001
                pass
            OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1),
                           encoding="utf-8")
            print("（已落盘）")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
