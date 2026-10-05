#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 799 探针 —— **嵌套分组**：793 的「先外后内 + 每轮重算」从未被实测过

## 起点：793–798 **五批都没验**嵌套分组

793 加 `fitStoryboardGroupsToChildren` 时写下边界 2：「组的顺序按「先外后内」，
每轮都**重新**从当前列表算绝对位置，这样嵌套时内层拿到的绝对位置已经是对的」。
★ 这句话**从未被任何一批实测过**——793–798 造的全是**单层**组。

## ★★ 前提：UI **造不出**嵌套（792 已记，本批复核）

`groupSelectedNodes` 的 children 过滤里有 `node.type !== "storyboard-group"`
⟹ **组本身不能成为新组的子节点** ⟹ 键盘 `G` / 右键菜单都造不出嵌套。
（792 当时把这条记成「嵌套组合没实现」，本批要**复核**它今天仍然成立。）

⟹ 所以要测纯函数层，只能**直接往 store 注入嵌套数据**，再触发一条会走
`fitStoryboardGroupsToChildren` 的路径。

## ★★ 799 找的到底是什么（读源码 `:765-768` + `:791` 得出，不是猜）

`nextPosition = minX - GROUP_PADDING`，其中 `minX` 是 kids 的**绝对**坐标；
然后 `:791` 把它直接写进组的 `position` —— 但 `position` 的语义
（`getAbsoluteNodePosition` `:569`）是**相对直接父节点**。

⟹ **单层**（组没有父节点）时 `parentAbs == 0`，绝对值恰好等于相对值 ⟹ 无差别；
⟹ **嵌套**时绝对值被当成相对值 ⟹ 外层位移被**重复计入**。

★ 这就是 793–798 五批全都测不到它的原因：五批造的组**全都没有父节点**。

## ★ 四条臂：外层组在原点 vs 外层组有偏移

★ 只用**键盘方向键**（795 加的、已验过的能力）触发 fit，**不用鼠标拖**。
  理由：一旦发散，节点会飞出视口 ⟹ `SCAN_MEMBER` 取到屏幕外坐标、
  拖动根本没发生 ⟹ 整条臂变成空读数（793 第一版踩过）。
  键盘 nudge 不依赖节点在视口内 ⟹ 读数永远拿得到。

| 臂 | 数据 | 步数 | 角色 |
| --- | --- | --- | --- |
| ★ 单层 nudge | 组无父节点 | 2 | 阳性对照：单层必须全对 |
| ★ 嵌套·外层在原点 | `outer@(0,0)` | 2 | 阴性对照：`parentAbs==0` ⟹ 必须全对 |
| ★ 嵌套·外层有偏移（一次） | `outer@(200,150)` | 1 | 首次分歧定位 |
| ★ 嵌套·外层有偏移（两次） | `outer@(200,150)` | 2 | 分歧累积 |

★ **阴性对照的作用**：证明「臂没失败」不是因为探针/判据坏了，而是因为数据真的
  落在「外层在原点」这个特例上。断言直接查 raw 里的 `g-outer.position`。

## ★ 判据：两条**与坐标系语义无关**的客观不变量

不变量 A（793 的核心承诺，对每个非组节点）：节点的**绝对**位置必须落在
它所属组的**绝对**框内。

不变量 B（贴合）：每个有子节点的组，其**绝对**框 = 直接子节点绝对包围盒 ⊕ padding。

★ 两条都用**绝对**坐标表述 ⟹ 不预设 `position` 该写绝对还是相对 ⟹
  判的是**用户看得见的几何**，不是实现细节。
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
    "liblib-canvas-batch799-2026-10-01/raw/vb799a-%s.json" % PHASE)

#: ★ 注入用的图。`kind==='single'` 是单层阳性对照；否则注入 `outer ⊃ {inner, loose}`、
#: `inner ⊃ {m1, m2}`，外层组的坐标由 `spec.ox/oy` 给。
#: ★★ 全部**层序自洽**：每个 `position` 都从 0 起、语义严格「相对直接父节点」，
#:   且组与成员的**绝对**位置与父链逐层相加后自洽。
#:   （第一版注入 `-9999/-8888` 之类「故意放歪」的值，触发的是坏数据路径；
#:    799 要测的是机制 ⟹ 数据必须合法。）
MAKE_GRAPH = """(spec)=>{
  const st=window.__libtv_store;
  const mk=(id,type,pos,extra)=>Object.assign({
    id:id,type:type,position:{x:pos[0],y:pos[1]},width:0,height:0,
    data:{},style:{},measured:{},selected:false,dragging:false},extra||{});
  const g=(id,pos,parentId,title)=>mk(id,'storyboard-group',pos,{
    parentId:parentId||undefined,width:10,height:10,
    style:{width:10,height:10,zIndex:-1001},zIndex:-1001,
    data:{title:title,variant:'image'}});
  const t=(id,pos,parentId)=>mk(id,'text',pos,{
    parentId:parentId||undefined,width:200,height:100});
  let nodes;
  if(spec.kind==='single'){
    nodes=[g('g-single',[0,0],null,'单层'),
           t('s-m1',[0,0],'g-single'),
           t('s-m2',[400,0],'g-single')];
  }else{
    nodes=[g('g-outer',[spec.ox,spec.oy],null,'外层'),
           g('g-inner',[40,40],'g-outer','内层'),
           t('n-m1',[40,40],'g-inner'),
           t('n-m2',[440,40],'g-inner'),
           t('n-loose',[40,440],'g-outer')];
  }
  st.getState().setNodes(nodes);
  return {ok:true,count:nodes.length,kind:spec.kind};}"""

#: ★ 读**绝对**几何（沿 `parentId` 链求和）。组与节点都给出 `pos`（相对）与 `abs`（绝对）。
MEASURE = """()=>{
  const S=window.__libtv_store.getState();
  const cv=S.canvases.find(c=>c.id===S.activeCanvasId)||S.canvases[0];
  const byId=new Map(cv.nodes.map(n=>[n.id,n]));
  const abs=(n)=>{let x=n.position.x,y=n.position.y,p=n.parentId;
    const seen=new Set([n.id]); let depth=0;
    while(p&&!seen.has(p)&&depth<32){seen.add(p);depth+=1;
      const q=byId.get(p); if(!q)break; x+=q.position.x;y+=q.position.y;p=q.parentId;}
    return {x:x,y:y,depth:depth};};
  const one=(n)=>{const a=abs(n);
    return {id:n.id, type:n.type, parentId:n.parentId||null,
      pos:{x:n.position.x,y:n.position.y}, abs:{x:a.x,y:a.y}, depth:a.depth,
      w:n.width, h:n.height};};
  return {nodes:cv.nodes.map(one).sort((x,y)=>String(x.id)<String(y.id)?-1:1),
    total:cv.nodes.length,
    groupCount:cv.nodes.filter(n=>n.type==='storyboard-group').length};}"""


def boot(pg):
    pg.goto(A.BASE, wait_until="domcontentloaded")
    pg.evaluate(A.CLEAR_LS, A.LS_KEY)
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.goto(A.BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1300)
    pg.keyboard.press("Meta+0")
    pg.wait_for_timeout(700)


def inject(pg, spec):
    r = pg.evaluate(MAKE_GRAPH, spec)
    if r.get("FAILED"):
        return r.get("FAILED")
    pg.wait_for_timeout(700)
    return None


def nudge(pg, node_id, key):
    """★ 触发一次 fit：选中最小的那个成员，按一次方向键（`nudgeSelectedNodes` → `:3437`）。"""
    pg.evaluate("(id)=>window.__libtv_store.getState().selectNodes([id]);", node_id)
    pg.keyboard.press(key)
    pg.wait_for_timeout(700)


def run_arm(pg, spec, target, steps):
    err = inject(pg, spec)
    if err:
        return {"FAILED": err}
    seq = [{"step": 0, "state": pg.evaluate(MEASURE)}]
    for i, key in enumerate(["ArrowRight", "ArrowLeft"][:steps]):
        nudge(pg, target, key)
        seq.append({"step": i + 1, "key": key,
                    "state": pg.evaluate(MEASURE)})
    return {"spec": spec, "target": target, "steps": steps, "seq": seq}


ARMS = [
    ("singleNudge", {"kind": "single"}, "s-m1", 2),
    ("nestedOrigin", {"kind": "nest", "ox": 0, "oy": 0}, "n-m1", 2),
    ("nestedOffsetOnce", {"kind": "nest", "ox": 200, "oy": 150}, "n-m1", 1),
    ("nestedOffsetTwice", {"kind": "nest", "ox": 200, "oy": 150}, "n-m1", 2),
]


def fmt(cell):
    if cell.get("FAILED"):
        return "FAILED:%s" % cell["FAILED"]
    sp = cell["spec"]
    parts = ["组%d" % cell["seq"][0]["state"]["groupCount"]]
    for step in cell["seq"]:
        gs = ", ".join(
            "%s rel(%s,%s) abs(%s,%s) %sx%s" % (
                n["id"], n["pos"]["x"], n["pos"]["y"],
                n["abs"]["x"], n["abs"]["y"], n["w"], n["h"])
            for n in step["state"]["nodes"] if n["type"] == "storyboard-group")
        ns = ", ".join("%s abs(%s,%s)" % (n["id"], n["abs"]["x"], n["abs"]["y"])
                       for n in step["state"]["nodes"] if n["type"] != "storyboard-group")
        tag = "注入" if step["step"] == 0 else "步%s" % step["step"]
        parts.append("  %s 组[%s] 节点[%s]" % (tag, gs, ns))
    head = "kind=%s" % sp.get("kind")
    if sp.get("kind") != "single":
        head += " outer@(%s,%s)" % (sp["ox"], sp["oy"])
    return head + " ｜ " + " ｜ ".join(parts)


def main():
    rounds = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        for rd in range(2):
            rows = []
            for name, spec, target, steps in ARMS:
                cell, tries = None, 0
                for t in range(3):
                    pg = b.new_page()
                    pg.set_default_timeout(15000)
                    tries = t + 1
                    try:
                        boot(pg)
                        cell = run_arm(pg, spec, target, steps)
                        cell["arm"] = name
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
    OUT.write_text(json.dumps({"batch": 799, "phase": PHASE, "rounds": rounds},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
