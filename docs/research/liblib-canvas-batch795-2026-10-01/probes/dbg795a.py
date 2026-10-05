#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 795 探针 —— 键盘方向键**能不能移动节点**

## 起点：793 遗留里写的第三条

793 的遗留原文：「未测键盘方向键移动成员是否同样触发跟随」。

★ **但动手之前先查源码，结论是这条遗留的前提不成立**：

- `src/app/page.tsx` 里 `handleKeyDown` 的分支只有 `Escape` / `Delete` /
  `Backspace` / `Tab` / `Cmd+0` / `Cmd+=` / `Cmd+-` / `Cmd+z` / `Cmd+d` / `g` …，
  **没有任何 `Arrow*` 分支**（全仓 `grep Arrow(Up|Down|Left|Right)` 只命中 lucide
  图标与导演台滑杆，没有一处是画布节点移动）。
- `@xyflow/react` v12 **没有内建方向键移动节点**（它内建的只有
  `deleteKeyCode` / `multiSelectionKeyCode` 这些，而且 `deleteKeyCode={[]}`
  在 `page.tsx:1583` 被显式清空了）。
- store 里也**没有** `nudge` / `moveNodeBy` 之类的 API。

⟹ 不是「方向键移动了但框没跟随」，而是**键盘用户根本没法移动节点**。
793 遗留写错了前提；本批把它当成一个**独立的可交互性缺陷**来测。

## ★ 为什么必须带阳性对照

「按了方向键、节点没动」有两种解释：

1. 键盘移动这个能力**本来就没有**（本批的结论）
2. 探针**没把事件送到位**（探针坏了）

⟹ 每条臂都配一条**同页、同焦点、同 `keyboard.press` 通道**的阳性对照：
`Delete` 键删掉一个节点。它走 `page.tsx:1344` 的自定义分支，
和方向键走**完全相同**的 `window` keydown 监听器 ⟹ 阳性对照通过即证明
「事件确实到达了画布的键盘处理器」。

## 三条臂（每臂自带阳性对照）

| 臂 | 动作 | 判什么 |
| --- | --- | --- |
| ★ 方向键移动成员 | 选中组成员 → 按 `ArrowRight` ×3 | 节点有没有动一点 |
| ★ 方向键移动组本身 | 选中组 → 按 `ArrowRight` ×3 | 组有没有动 |
| ★ 阳性对照 | 选中一个散节点 → 按 `Delete` | 键盘事件**确实到达**画布 |

★ 另记 `past`：若将来真加了方向键移动，它**必须**纳入撤销栈，
否则会出现 756 那种「用户唯一出路是撤销、但撤销里没有这次移动」的情况。
所以本批顺手把 `past` 记下来，作为**将来的验收钩子**。
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
    "liblib-canvas-batch795-2026-10-01/raw/vb795a-%s.json" % PHASE)

#: ★ 造一个**两成员**的组（与 794 同一套，保证框是贴合值）
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

#: ★ 只量「一个节点的绝对位置 + 撤销栈深度 + 节点总数」
#:   绝对位置沿 parentId 链求和（与 helper 同算法）
MEASURE = """(ids)=>{
  const s=window.__libtv_store.getState();
  const cv=s.canvases.find(c=>c.id===s.activeCanvasId)||s.canvases[0];
  const byId=new Map(cv.nodes.map(n=>[n.id,n]));
  const abs=(n)=>{let x=n.position.x,y=n.position.y,p=n.parentId;
    const seen=new Set([n.id]);
    while(p&&!seen.has(p)){seen.add(p);const q=byId.get(p);
      if(!q)break;x+=q.position.x;y+=q.position.y;p=q.parentId;}
    return {x:Math.round(x),y:Math.round(y)};};
  return {past:(s.historyByCanvas&&s.historyByCanvas[s.activeCanvasId]
      ? (s.historyByCanvas[s.activeCanvasId].past||[]).length : -1),
    nodeCount:cv.nodes.length,
    targets:(ids||[]).map(id=>{const n=byId.get(id);
      return {id:String(id), exists:!!n, abs:n?abs(n):null,
        w:n&&n.width, h:n&&n.height};})};}"""


def boot(pg):
    pg.goto(A.BASE, wait_until="domcontentloaded")
    pg.evaluate(A.CLEAR_LS, A.LS_KEY)
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.goto(A.BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1300)
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(700)


def make_pair(pg):
    r = pg.evaluate(MAKE_PAIR_GROUP)
    if r.get("FAILED"):
        return None, r.get("FAILED")
    pg.wait_for_timeout(500)
    return r, None


def arm_arrow_moves_member(pg):
    """★ 选中组里一个成员 → 连按 3 次 `ArrowRight`。"""
    r, err = make_pair(pg)
    if err:
        return {"arm": "arrowMovesMember", "FAILED": err}
    gid, kid = r["gid"], r["memberIds"][0]
    pg.evaluate("(id)=>window.__libtv_store.getState().selectNodes([id]);", kid)
    before = pg.evaluate(MEASURE, [kid, gid])
    for _ in range(3):
        pg.keyboard.press("ArrowRight")
        pg.wait_for_timeout(180)
    pg.wait_for_timeout(500)
    after = pg.evaluate(MEASURE, [kid, gid])
    return {"arm": "arrowMovesMember", "gid": gid, "kid": kid,
            "before": before, "after": after}


def arm_arrow_moves_group(pg):
    """★ 选中组**本身** → 连按 3 次 `ArrowRight`。"""
    r, err = make_pair(pg)
    if err:
        return {"arm": "arrowMovesGroup", "FAILED": err}
    gid = r["gid"]
    pg.evaluate("(id)=>window.__libtv_store.getState().selectNodes([id]);", gid)
    before = pg.evaluate(MEASURE, [gid, r["memberIds"][0]])
    for _ in range(3):
        pg.keyboard.press("ArrowRight")
        pg.wait_for_timeout(180)
    pg.wait_for_timeout(500)
    after = pg.evaluate(MEASURE, [gid, r["memberIds"][0]])
    return {"arm": "arrowMovesGroup", "gid": gid, "kid": r["memberIds"][0],
            "before": before, "after": after}


def arm_positive_delete(pg):
    """★ 阳性对照：同页同焦点按 `Delete` ⟹ 节点数必须真的减 1。

    ★ 它和方向键走**同一个** `window` keydown 监听器（`page.tsx:1423`），
    所以它通过即证明「键盘事件确实到达了画布」。
    """
    r, err = make_pair(pg)
    if err:
        return {"arm": "positiveDelete", "FAILED": err}
    victim = r["memberIds"][0]
    pg.evaluate("(id)=>window.__libtv_store.getState().selectNodes([id]);",
                victim)
    before = pg.evaluate(MEASURE, [victim, r["gid"]])
    pg.keyboard.press("Delete")
    pg.wait_for_timeout(600)
    after = pg.evaluate(MEASURE, [victim, r["gid"]])
    return {"arm": "positiveDelete", "gid": r["gid"], "kid": victim,
            "before": before, "after": after}


ARMS = [("arrowMovesMember", arm_arrow_moves_member),
        ("arrowMovesGroup", arm_arrow_moves_group),
        ("positiveDelete", arm_positive_delete)]


def fmt(cell):
    if cell.get("FAILED"):
        return "FAILED:%s" % cell["FAILED"]
    b, a = cell["before"], cell["after"]
    tb = [(t["id"][:8], t["abs"]) for t in b["targets"]]
    ta = [(t["id"][:8], t["abs"]) for t in a["targets"]]
    return ("节点数 %d→%d ｜ past %d→%d ｜ %s → %s"
            % (b["nodeCount"], a["nodeCount"], b["past"], a["past"], tb, ta))


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
                print("  r%d %-20s %s" % (rd + 1, name, fmt(cell)), flush=True)
            rounds.append({"round": rd + 1, "rows": rows})
        b.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"batch": 795, "phase": PHASE, "rounds": rounds},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
