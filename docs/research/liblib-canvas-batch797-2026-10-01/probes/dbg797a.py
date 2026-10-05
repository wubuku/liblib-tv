#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 797 探针 —— 分组框的**网格吸附**：功能已存在，但框**用不上**

## 起点：796 顺带发现的那条

796 记下：拖后框的 `width` 是 `1173.3422818791946`，它会进 `node.style.width`
⟹ 用户可见的 DOM 尺寸带浮点尾数。796 判它**非缺陷**（无害），但同时指出：
「若将来要做尺寸吸附/对齐，这里需要先归一化」。

★ 本批去查「将来」这件事**是不是已经发生了** —— 结果是**已经**：

- 画布**已经有**网格吸附：`page.tsx` 传 `snapToGrid={snapToGrid}` +
  `snapGrid={[20, 20]}`，状态在 `uiStore`（`:222` 初值 `false`），
  UI 入口是 `BottomToolbar.tsx` 里那个「网格吸附」按钮
- ★ 但**分组框是 store 派生的**：793 的 `fitStoryboardGroupsToChildren` 直接写
  `node.position` / `node.width` / `node.style`，**根本不经过 react-flow 的拖拽管线**
  ⟹ react-flow 的 `snapToGrid` 对它**不可能生效**

★ 这是一个**真实可测**的缺陷：用户打开「网格吸附」、拖动一个成员，
成员会吸到 20 的倍数上，而**框不会** ⟹ 框与成员不再对齐网格。

## ★ 四条臂

| 臂 | 吸附开/关 | 动作 | 判什么 |
| --- | --- | --- | --- |
| ★ 吸附+成员臂 | **开** | 拖一个成员 137 像素 | 成员落点是不是 20 的倍数 |
| ★ 吸附+框臂 | **开** | 同上 | **框**落点是不是 20 的倍数（预期：否） |
| ★ 吸附+成员对照 | **关** | 同上 | 关掉时**不**吸附（证明吸附真的在工作） |
| ★ 前置对照 | **开** | **什么都不做** | 打开吸附**本身**不改任何几何 |

★ 第 3 条是**必需的**：若「成员也不吸附」，那缺陷就不是「框不吸附」而是
「吸附整体坏了」，两者的修法完全不同。

## ★ 读数不取整（796 的教训）

`Math.round` 会把亚像素掩盖成整数 ⟹ 本批直接读**原值**，
这样「137 是不是 20 的倍数」才有意义。
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
    "liblib-canvas-batch797-2026-10-01/raw/vb797a-%s.json" % PHASE)

#: ★ 造一个**两成员**的组（与 793-796 同一套）
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

#: ★ 读组几何 + 成员绝对位置 + **吸附开关的真实状态**
MEASURE = """(gid)=>{
  const s=window.__libtv_store.getState();
  const cv=s.canvases.find(c=>c.id===s.activeCanvasId)||s.canvases[0];
  const byId=new Map(cv.nodes.map(n=>[n.id,n]));
  const abs=(n)=>{let x=n.position.x,y=n.position.y,p=n.parentId;
    const seen=new Set([n.id]);
    while(p&&!seen.has(p)){seen.add(p);const q=byId.get(p);
      if(!q)break;x+=q.position.x;y+=q.position.y;p=q.parentId;}
    // ★ 不取整（796 的教训：取整会隐藏亚像素，吸附判定必须看原值）
    return {x:x,y:y};};
  const ui=window.__libtv_ui_store?window.__libtv_ui_store.getState():null;
  const g=byId.get(gid);
  const kids=cv.nodes.filter(n=>n.parentId===gid);
  const R=(r)=>({t:r.top,l:r.left,w:r.width,h:r.height,
    b:r.bottom,r:r.right});
  const ge=document.querySelector(
    '.react-flow__node-storyboard-group[data-id=\"'+gid+'\"]');
  return {snapToGrid: ui?ui.snapToGrid:null,
    groupStore:g?{pos:{x:g.position.x,y:g.position.y},
      w:g.width,h:g.height, styleW:g.style&&g.style.width}:null,
    groupDom: ge?R(ge.getBoundingClientRect()):null,
    members:kids.map(m=>({id:m.id, abs:abs(m), w:m.width, h:m.height,
      pos:{x:m.position.x,y:m.position.y}}))
      .sort((a,b)=>String(a.id)<String(b.id)?-1:1)};}"""

SCAN_MEMBER = """(mid)=>{
  const el=document.querySelector('.react-flow__node[data-id=\"'+mid+'\"]');
  if(!el) return {FAILED:'成员 DOM 不在'};
  const r=el.getBoundingClientRect();
  return {x:Math.round(r.left+r.width/2), y:Math.round(r.top+r.height/2)};}"""

#: ★ 读真实的吸附开关状态（不能只信 store，要读 DOM 上 react-flow 的实际行为）
READ_SNAP = """()=>{
  const host=document.querySelector('[data-libtv-react-flow-host]');
  const ui=window.__libtv_ui_store?window.__libtv_ui_store.getState():null;
  return {storeValue: ui?ui.snapToGrid:null,
    hasUIStore: !!window.__libtv_ui_store,
    host: !!host};}"""


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


def set_snap(pg, on):
    """★ 用**真实 UI 按钮**切吸附（不是直接改 store）⟹ 才能证明用户路径。"""
    btn = pg.query_selector('button[aria-label="网格吸附"]')
    if not btn:
        # ★ 兜底：把事实回报，不静默改 store（否则会读出一个假的「吸附开着」）
        return {"FAILED": "找不到「网格吸附」按钮"}
    # ★ `IconButton` 用 `aria-pressed` 表示激活态（不是 `data-state`）
    cur = pg.evaluate("()=>{const u=window.__libtv_ui_store;"
                      "return u?u.getState().snapToGrid:null;}")
    if cur != on:
        btn.click()
        pg.wait_for_timeout(500)
    now = pg.evaluate("()=>{const u=window.__libtv_ui_store;"
                      "return u?u.getState().snapToGrid:null;}")
    aria = pg.get_attribute('button[aria-label="网格吸附"]', "aria-pressed")
    if now != on:
        return {"FAILED": "切吸附失败：想要 %r 实际 %r" % (on, now)}
    # ★ store 值与按钮的 aria-pressed 必须一致 ⟹ 否则「开了」只是我以为开了
    if (aria == "true") != bool(on):
        return {"FAILED": "aria-pressed(%r) 与 store(%r) 不一致"
                % (aria, now)}
    return {"ok": True, "ariaPressed": aria}


SCAN_GROUP = """(gid)=>{
  const el=document.querySelector(
    '.react-flow__node-storyboard-group[data-id="'+gid+'"]');
  if(!el) return {FAILED:'组 DOM 不在'};
  const r=el.getBoundingClientRect();
  const cx=r.left+r.width/2, cy=r.top+r.height/2;
  // ★★ 关键：`inset` 必须**跳过 20 像素**。`StoryboardGroupNode` 在左右两侧
  //   各有一个 20x20 的 `<Handle>`（连线用），而 handle 的 pointerdown 被
  //   react-flow 当成「开始连线」⟹ 按在 handle 上拖**不会移动组**。
  //   诊断（diag797）实测 `inset=3` 的左右两点命中的正是
  //   `react-flow__handle`，那正是「组纹丝不动」的原因。
  for(const inset of [26,30,34,40,48,56,64]){
    for(const [x,y] of [[r.left+inset,cy],[r.right-inset,cy],
      [cx,r.top+inset],[cx,r.bottom-inset]]){
      const hit=document.elementFromPoint(Math.round(x),Math.round(y));
      if(!hit) continue;
      // ★ 必须**排除 handle**：否则又按回连线起点
      if(hit.closest('.react-flow__handle')) continue;
      const node=hit.closest('.react-flow__node');
      if(node&&node.getAttribute('data-id')===gid)
        return {x:Math.round(x), y:Math.round(y), inset:inset,
                hit:String(hit.className).slice(0,60),
                isHandle:false};
    }
  }
  return {FAILED:'找不到「非 handle 且属于组」的点'};}"""


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


def arm_drag_snap_on(pg):
    """★ 吸附**开**，拖成员 137 像素（137 不是 20 的倍数 ⟹ 吸不吸能分辨）。"""
    s = set_snap(pg, True)
    if s.get("FAILED"):
        return {"arm": "dragSnapOn", "FAILED": s["FAILED"]}
    r, err = make_pair(pg)
    if err:
        return {"arm": "dragSnapOn", "FAILED": err}
    gid, kid = r["gid"], r["memberIds"][0]
    p = pg.evaluate(SCAN_MEMBER, kid)
    if p.get("FAILED"):
        return {"arm": "dragSnapOn", "FAILED": p["FAILED"]}
    before = pg.evaluate(MEASURE, gid)
    drag(pg, p, 137, 0)
    after = pg.evaluate(MEASURE, gid)
    return {"arm": "dragSnapOn", "gid": gid, "kid": kid, "snapUI": s,
            "before": before, "after": after}


def arm_drag_snap_off(pg):
    """★ 吸附**关**，同样拖 137 像素 ⟹ 对照组（证明吸附真的在工作）。"""
    s = set_snap(pg, False)
    if s.get("FAILED"):
        return {"arm": "dragSnapOff", "FAILED": s["FAILED"]}
    r, err = make_pair(pg)
    if err:
        return {"arm": "dragSnapOff", "FAILED": err}
    gid, kid = r["gid"], r["memberIds"][0]
    p = pg.evaluate(SCAN_MEMBER, kid)
    if p.get("FAILED"):
        return {"arm": "dragSnapOff", "FAILED": p["FAILED"]}
    before = pg.evaluate(MEASURE, gid)
    drag(pg, p, 137, 0)
    after = pg.evaluate(MEASURE, gid)
    return {"arm": "dragSnapOff", "gid": gid, "kid": kid, "snapUI": s,
            "before": before, "after": after}


def arm_snap_toggle_only(pg):
    """★ 前置对照：只切吸附开关，**什么都不拖** ⟹ 几何必须完全不变。"""
    s = set_snap(pg, True)
    if s.get("FAILED"):
        return {"arm": "snapToggleOnly", "FAILED": s["FAILED"]}
    r, err = make_pair(pg)
    if err:
        return {"arm": "snapToggleOnly", "FAILED": err}
    before = pg.evaluate(MEASURE, r["gid"])
    pg.wait_for_timeout(600)
    after = pg.evaluate(MEASURE, r["gid"])
    return {"arm": "snapToggleOnly", "gid": r["gid"], "snapUI": s,
            "before": before, "after": after}


def arm_drag_group_snap_on(pg):
    """★★ 吸附**开**，拖**组本身** 137 像素。

    ★ 这是本批**最可能暴露实质问题**的一条：组的 `position` 会被 react-flow
      吸附到网格，但它的成员是**相对**组的偏移 ⟹ 成员会不会被带离网格？
      若会，用户开了吸附、拖组，成员反而落到网格外。
    """
    s = set_snap(pg, True)
    if s.get("FAILED"):
        return {"arm": "dragGroupSnapOn", "FAILED": s["FAILED"]}
    r, err = make_pair(pg)
    if err:
        return {"arm": "dragGroupSnapOn", "FAILED": err}
    gid = r["gid"]
    p = pg.evaluate(SCAN_GROUP, gid)
    if p.get("FAILED"):
        return {"arm": "dragGroupSnapOn", "FAILED": p["FAILED"]}
    before = pg.evaluate(MEASURE, gid)
    drag(pg, p, 137, 0)
    after = pg.evaluate(MEASURE, gid)
    return {"arm": "dragGroupSnapOn", "gid": gid,
            "memberIds": r["memberIds"], "snapUI": s,
            "before": before, "after": after}


def arm_group_drag_after_members_snapped(pg):
    """★★★ **本批的核心臂**：先把两个成员都拖到**吸附后的整数网格**上，
    再拖组本身。

    ★ 为什么必须先摆平成员：`dragGroupSnapOn` 那一臂里成员**本来就离网格**
      （132、273 都不是 20 的倍数），所以「拖完组成员离网格」不能证明什么
      —— 它们拖之前就离网格。★ 摆平之后，「成员从网格上被拖下来」才是
      由**这一步**造成的 ⟹ 缺陷归属才清楚。
    """
    s = set_snap(pg, True)
    if s.get("FAILED"):
        return {"arm": "groupDragAfterMembersSnapped", "FAILED": s["FAILED"]}
    r, err = make_pair(pg)
    if err:
        return {"arm": "groupDragAfterMembersSnapped", "FAILED": err}
    gid = r["gid"]
    # ★ 先把**每个**成员各拖一次 ⟹ 吸附会把它落到 20 的倍数上
    for mid in r["memberIds"]:
        p = pg.evaluate(SCAN_MEMBER, mid)
        if p.get("FAILED"):
            return {"arm": "groupDragAfterMembersSnapped",
                    "FAILED": "成员 %s 找不到中心点" % mid[:8]}
        drag(pg, p, 61, 0)          # 61 不是 20 的倍数 ⟹ 吸不吸能分辨
    settled = pg.evaluate(MEASURE, gid)
    # ★ 确认两个成员**此刻都在网格上**，否则这条臂的前提就不成立 ⟹ 如实报 FAILED
    offgrid = [m["id"][:8] for m in settled["members"]
               if m["abs"]["x"] % 20 or m["abs"]["y"] % 20]
    if offgrid:
        return {"arm": "groupDragAfterMembersSnapped",
                "FAILED": "摆平后成员仍不在网格上：%r（吸附可能没生效）" % offgrid,
                "settled": settled}
    g = pg.evaluate(SCAN_GROUP, gid)
    if g.get("FAILED"):
        return {"arm": "groupDragAfterMembersSnapped", "FAILED": g["FAILED"]}
    drag(pg, g, 137, 0)
    after = pg.evaluate(MEASURE, gid)
    return {"arm": "groupDragAfterMembersSnapped", "gid": gid,
            "memberIds": r["memberIds"], "snapUI": s,
            "before": settled, "after": after,
            "dragPoint": g}


ARMS = [("dragSnapOn", arm_drag_snap_on),
        ("dragSnapOff", arm_drag_snap_off),
        ("snapToggleOnly", arm_snap_toggle_only),
        ("dragGroupSnapOn", arm_drag_group_snap_on),
        ("groupDragAfterMembersSnapped",
         arm_group_drag_after_members_snapped)]


def fmt(cell):
    if cell.get("FAILED"):
        return "FAILED:%s" % cell["FAILED"]
    b, a = cell["before"], cell["after"]
    m0, m1 = b["members"][0], a["members"][0]
    g = lambda m: (("(%s,%s)%sx%s" % (m["groupStore"]["pos"]["x"],
                                      m["groupStore"]["pos"]["y"],
                                      m["groupStore"]["w"], m["groupStore"]["h"]))
                   if m and m.get("groupStore") else "无组")
    return ("snap=%s ｜ 成员 %s→%s ｜ 组 %s→%s ｜ 组 styleW=%s"
            % (a.get("snapToGrid"),
               (m0["abs"]["x"], m0["abs"]["y"]),
               (m1["abs"]["x"], m1["abs"]["y"]),
               g(b), g(a),
               (a.get("groupStore") or {}).get("styleW")))


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
                print("  r%d %-16s %s" % (rd + 1, name, fmt(cell)), flush=True)
            rounds.append({"round": rd + 1, "rows": rows})
        b.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"batch": 797, "phase": PHASE, "rounds": rounds},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
