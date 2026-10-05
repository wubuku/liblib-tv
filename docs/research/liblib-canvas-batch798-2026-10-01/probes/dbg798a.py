#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 798 探针 —— 分组框的**尺寸**要不要吸附？

## 起点：797 留下的

797 修了「拖组把成员拖下网格」⟹ 改的是 `GROUP_PADDING`（它决定组**位置**与
成员的**相对偏移**）。但框的**尺寸**仍带浮点尾数（796 记的 `1173.34`
会进 `node.style.width`）。797 明确留下一句：「未测框的**尺寸**是否也该吸附」。

## ★ 先做数学判定（这决定本批能不能是「修」）

组框尺寸 = `(max(成员右) − min(成员左)) + 2 × PADDING`。
若成员**位置**都在网格上，则尺寸的余数 = **成员尺寸余数之和**，
**与 PADDING 无关**（PADDING=40 是 20 的倍数，加它不改变余数）。

★ 种子成员的尺寸实测：`618 % 20 = 18`、`350 % 20 = 10` ⟹ **成员尺寸本身
就不是网格倍数** ⟹ 组尺寸在数学上**不可能**落在网格上。

⟹ 只有三条路，每条都有代价：

| 路 | 代价 |
| --- | --- |
| ① 改成员尺寸 | 那是改**用户对象**的大小，超出「组框」范围 |
| ② 放弃「恰好包住成员」 | **破坏 793 的不变量**（框不再贴合） |
| ③ 接受组尺寸不在网格 | 容器不吸附 |

## ★ 所以本批真正要回答的是：**③ 是不是对的**？

桌面画布（Figma / FigJam）的惯例是「**容器不吸附、只对象吸附**」——
容器是派生几何，它的位置/尺寸由内容决定。★ 但「惯例」不是证据，
必须能从**本仓现状**测出来 ⟹ 下面两条臂：

| 臂 | 动作 | 判什么 |
| --- | --- | --- |
| ★ 位置臂 | 摆平成员后测组**位置** | 位置**在**网格上（797 的成果，本批不许回退） |
| ★ 尺寸臂 | 同一状态下测组**尺寸** | 尺寸**不在**网格上，且余数 = 成员尺寸余数 |

★ 尺寸臂的判据不是「尺寸不在网格」本身（那只是观察），而是
「**余数恰好等于独立算出的成员尺寸余数**」⟹ 这样才能说「不是漏吸附，
而是数学上做不到」。

## ★ 前置对照：组的尺寸**是不是用户可调的**

★ 全仓 `grep NodeResizer` = **0** ⟹ 组没有 resize 控件，尺寸纯属派生值。
本批在运行时复核这一点（不靠记忆），因为它决定了「尺寸吸附对用户有什么用」。
"""
import json
import pathlib
import sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

PHASE = sys.argv[1] if len(sys.argv) > 1 else "pre"
assert PHASE in ("pre", "post"), "★ 阶段只能是 pre / post，收到 %r" % PHASE

OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch798-2026-10-01/raw/vb798a-%s.json" % PHASE)

MAKE_PAIR_GROUP = """()=>{
  const st=window.__libtv_store.getState();
  const cv=st.canvases.find(c=>c.id===st.activeCanvasId)||st.canvases[0];
  const loose=cv.nodes.filter(n=>n.type!=='storyboard-group'&&!n.parentId)
    .slice(0,2).map(n=>n.id);
  if(loose.length<2) return {FAILED:'散节点不足两个'};
  window.__libtv_store.getState().selectNodes(loose);
  window.__libtv_store.getState().groupSelectedNodes(loose);
  const s2=window.__libtv_store.getState();
  const cv2=s2.canvases.find(c=>c.id===s2.activeCanvasId)||s2.canvases[0];
  const g=cv2.nodes.find(n=>n.type==='storyboard-group'
    && cv2.nodes.filter(m=>m.parentId===n.id).length>=2);
  if(!g) return {FAILED:'没造出两成员的组'};
  return {gid:g.id, memberIds:cv2.nodes.filter(m=>m.parentId===g.id)
    .map(m=>m.id)};}"""

#: ★ 读组几何、成员绝对位置与尺寸、**DOM 上实测的框尺寸**、以及
#:   「组有没有 resize 控件」的真实证据
MEASURE = """(gid)=>{
  const s=window.__libtv_store.getState();
  const cv=s.canvases.find(c=>c.id===s.activeCanvasId)||s.canvases[0];
  const byId=new Map(cv.nodes.map(n=>[n.id,n]));
  const abs=(n)=>{let x=n.position.x,y=n.position.y,p=n.parentId;
    const seen=new Set([n.id]);
    while(p&&!seen.has(p)){seen.add(p);const q=byId.get(p);
      if(!q)break;x+=q.position.x;y+=q.position.y;p=q.parentId;}
    return {x:x,y:y};};
  const g=byId.get(gid);
  const el=document.querySelector(
    '.react-flow__node-storyboard-group[data-id="'+gid+'"]');
  // ★ 「能不能手动调尺寸」的运行时证据：找 react-flow 的 resize 把手
  const handles=el?el.querySelectorAll('.react-flow__resize-control').length:0;
  const resizers=el?el.querySelectorAll('[class*=\"resize\"]').length:0;
  const R=(r)=>({w:r.width,h:r.height});
  return {snapToGrid:(window.__libtv_ui_store?
      window.__libtv_ui_store.getState().snapToGrid:null),
    groupStore:g?{pos:{x:g.position.x,y:g.position.y},
      w:g.width,h:g.height, styleW:g.style&&g.style.width,
      styleH:g.style&&g.style.height}:null,
    groupDom: el?R(el.getBoundingClientRect()):null,
    resizeHandles:handles, resizeAny:resizers,
    members:cv.nodes.filter(n=>n.parentId===gid)
      .map(m=>({id:m.id, abs:abs(m), w:m.width, h:m.height,
        pos:{x:m.position.x,y:m.position.y}}))
      .sort((a,b)=>String(a.id)<String(b.id)?-1:1)};}"""

SCAN_MEMBER = """(mid)=>{
  const el=document.querySelector('.react-flow__node[data-id="'+mid+'"]');
  if(!el) return {FAILED:'成员 DOM 不在'};
  const r=el.getBoundingClientRect();
  return {x:Math.round(r.left+r.width/2), y:Math.round(r.top+r.height/2)};}"""


def boot(pg):
    pg.goto(A.BASE, wait_until="domcontentloaded")
    pg.evaluate(A.CLEAR_LS, A.LS_KEY)
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.goto(A.BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1300)
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(700)


def set_snap(pg, on):
    """★ 用真实 UI 按钮切吸附（797 已验证 `aria-pressed` 与 store 必须一致）。"""
    btn = pg.query_selector('button[aria-label="网格吸附"]')
    if not btn:
        return {"FAILED": "找不到「网格吸附」按钮"}
    cur = pg.evaluate("()=>{const u=window.__libtv_ui_store;"
                      "return u?u.getState().snapToGrid:null;}")
    if cur != on:
        btn.click()
        pg.wait_for_timeout(500)
    now = pg.evaluate("()=>{const u=window.__libtv_ui_store;"
                      "return u?u.getState().snapToGrid:null;}")
    aria = pg.get_attribute('button[aria-label="网格吸附"]', "aria-pressed")
    if now != on or (aria == "true") != bool(on):
        return {"FAILED": "切吸附失败：store=%r aria=%r 想要 %r"
                % (now, aria, on)}
    return {"ok": True, "ariaPressed": aria}


def drag(pg, start, dx, dy, steps=12):
    pg.mouse.move(start["x"], start["y"])
    pg.mouse.down()
    for i in range(1, steps + 1):
        pg.mouse.move(start["x"] + dx * i // steps,
                      start["y"] + dy * i // steps)
        pg.wait_for_timeout(18)
    pg.wait_for_timeout(160)
    pg.mouse.up()
    pg.wait_for_timeout(550)


def settle_on_grid(pg, gid, memberIds):
    """★ 把每个成员各拖一次 ⟹ 吸附会把它落到 20 的倍数上。"""
    for mid in memberIds:
        p = pg.evaluate(SCAN_MEMBER, mid)
        if p.get("FAILED"):
            return {"FAILED": "成员 %s 找不到中心点" % mid[:8]}
        drag(pg, p, 61, 0)
    st = pg.evaluate(MEASURE, gid)
    off = [m["id"][:8] for m in st["members"]
           if m["abs"]["x"] % 20 or m["abs"]["y"] % 20]
    if off:
        return {"FAILED": "摆平后成员仍不在网格：%r" % off, "state": st}
    return st


def arm_size_vs_grid(pg):
    """★★ 尺寸臂：成员都在网格上时，组**位置**在网格、**尺寸**不在，
    且尺寸余数**恰好等于**独立算出的成员尺寸余数。"""
    s = set_snap(pg, True)
    if s.get("FAILED"):
        return {"arm": "sizeVsGrid", "FAILED": s["FAILED"]}
    r = pg.evaluate(MAKE_PAIR_GROUP)
    if r.get("FAILED"):
        return {"arm": "sizeVsGrid", "FAILED": r["FAILED"]}
    pg.wait_for_timeout(500)
    st = settle_on_grid(pg, r["gid"], r["memberIds"])
    if isinstance(st, dict) and st.get("FAILED"):
        return {"arm": "sizeVsGrid", "FAILED": st["FAILED"], "state": st}
    return {"arm": "sizeVsGrid", "gid": r["gid"],
            "memberIds": r["memberIds"], "snapUI": s, "settled": st}


def arm_resize_affordance(pg):
    """★ 尺寸可调性臂：运行时复核组**没有** resize 控件（尺寸是派生值）。"""
    s = set_snap(pg, True)
    if s.get("FAILED"):
        return {"arm": "resizeAffordance", "FAILED": s["FAILED"]}
    r = pg.evaluate(MAKE_PAIR_GROUP)
    if r.get("FAILED"):
        return {"arm": "resizeAffordance", "FAILED": r["FAILED"]}
    pg.wait_for_timeout(700)
    st = pg.evaluate(MEASURE, r["gid"])
    # ★ 再补一条：把组**选中**后看有没有 resize 把手出现
    pg.evaluate("(id)=>window.__libtv_store.getState().selectNodes([id]);",
                r["gid"])
    pg.wait_for_timeout(500)
    st2 = pg.evaluate(MEASURE, r["gid"])
    return {"arm": "resizeAffordance", "gid": r["gid"], "snapUI": s,
            "before": st, "after": st2}


def arm_snap_off_size(pg):
    """★ 对照臂：吸附**关**时尺寸**同样**不是倍数 ⟹ 说明这不是「吸附开着才坏」。"""
    s = set_snap(pg, False)
    if s.get("FAILED"):
        return {"arm": "snapOffSize", "FAILED": s["FAILED"]}
    r = pg.evaluate(MAKE_PAIR_GROUP)
    if r.get("FAILED"):
        return {"arm": "snapOffSize", "FAILED": r["FAILED"]}
    pg.wait_for_timeout(600)
    st = pg.evaluate(MEASURE, r["gid"])
    return {"arm": "snapOffSize", "gid": r["gid"], "snapUI": s, "settled": st}


ARMS = [("sizeVsGrid", arm_size_vs_grid),
        ("resizeAffordance", arm_resize_affordance),
        ("snapOffSize", arm_snap_off_size)]


def fmt(cell):
    if cell.get("FAILED"):
        return "FAILED:%s" % cell["FAILED"]
    m = cell.get("settled") or cell.get("after")
    if not m:
        return "（无读数）"
    g = m.get("groupStore")
    return ("组 pos=(%s,%s) %sx%s ｜ 成员 %s ｜ resizeHandles=%s"
            % (g["pos"]["x"], g["pos"]["y"], g["w"], g["h"],
               [(x["w"], x["h"], x["w"] % 20, x["h"] % 20)
                for x in m["members"]],
               m.get("resizeHandles")))


def main():
    rounds = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        for rd in range(2):
            rows = []
            for name, fn in ARMS:
                cell, tries = None, 0
                for t in range(3):
                    pg = b.new_page()
                    pg.set_default_timeout(15000)
                    tries = t + 1
                    try:
                        boot(pg)
                        cell = fn(pg)
                    except Exception as e:      # noqa: BLE001
                        cell = {"arm": name,
                                "FAILED": "%s: %s" % (type(e).__name__, e)}
                    finally:
                        try:
                            pg.close()
                        except Exception:       # noqa: BLE001
                            pass
                    if not cell.get("FAILED"):
                        break
                cell["tries"] = tries
                rows.append(cell)
                print("  r%d %-18s %s" % (rd + 1, name, fmt(cell)), flush=True)
            rounds.append({"round": rd + 1, "rows": rows})
        b.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"batch": 798, "phase": PHASE, "rounds": rounds},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
