#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 797 诊断 —— 为什么「拖组本身」那条臂**完全没动**

`dragGroupSnapOn` 读数：组 `(76,-157) 706x812` → `(76,-157) 706x812`，
成员两轮都纹丝不动，且**没有 FAILED**。

★ 这正是 789 记的「阳性对照必须有」：没有它，区分不了
  ①「组根本不能被拖」与 ②「我的扫描没点着」。
⟹ 本诊断只回答一个问题：**沿四边扫出来的那个点，`elementFromPoint` 到底命中谁？**
"""
import json
import pathlib
import sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402
import dbg797a as P  # noqa: E402

OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch797-2026-10-01/raw/diag797-dragpoint.json")

#: ★ 沿四边扫，并把每个采样点的 `elementFromPoint` 命中物**全部**记下来
PROBE_POINTS = """(gid)=>{
  const el=document.querySelector(
    '.react-flow__node-storyboard-group[data-id="'+gid+'"]');
  if(!el) return {FAILED:'组 DOM 不在'};
  const r=el.getBoundingClientRect();
  const cx=r.left+r.width/2, cy=r.top+r.height/2;
  // ★ 先把四个采样点算成**数值**（第一版把 'l'/'r' 传给 Math.round
  //   ⟹ elementFromPoint 报 "non-finite"，白跑一轮）
  const pts=[];
  for(const inset of [3,6,10,16,24,34,44]){
    pts.push(['l', inset, r.left+inset, cy]);
    pts.push(['r', inset, r.right-inset, cy]);
    pts.push(['t', inset, cx, r.top+inset]);
    pts.push(['b', inset, cx, r.bottom-inset]);
  }
  const hits=[];
  for(const [edge,inset,x,y] of pts){
    const px=Math.round(x), py=Math.round(y);
    const h=document.elementFromPoint(px,py);
    const node=h&&h.closest?h.closest('.react-flow__node'):null;
    hits.push({inset:inset, edge:edge, x:px, y:py,
      tag:h?h.tagName:null,
      cls:h?String(h.className).slice(0,70):null,
      nodeId:node?node.getAttribute('data-id'):null,
      nodeCls:node?String(node.className).slice(0,50):null,
      isGroup: !!(node&&node.getAttribute('data-id')===gid)});
  }
  const cs=getComputedStyle(el);
  return {rect:{l:r.left,t:r.top,r:r.right,b:r.bottom,
      w:r.width,h:r.height},
    groupStyle:{zIndex:cs.zIndex, pointerEvents:cs.pointerEvents,
      position:cs.position},
    groupClass:String(el.className).slice(0,120),
    hits:hits,
    属于组的点数: hits.filter(h=>h.isGroup).length};}"""


def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        pg = b.new_page()
        pg.set_default_timeout(15000)
        P.boot(pg)
        r = pg.evaluate(P.MAKE_PAIR_GROUP)
        if r.get("FAILED"):
            print("★ 造组失败：%s" % r["FAILED"])
            return
        pg.wait_for_timeout(600)
        res = pg.evaluate(PROBE_POINTS, r["gid"])
        pg.close()
        b.close()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"gid": r["gid"], "probe": res},
                              ensure_ascii=False, indent=1), encoding="utf-8")

    print("组 rect:", json.dumps(res.get("rect"), ensure_ascii=False))
    print("组 class:", res.get("groupClass"))
    print("组 style:", json.dumps(res.get("groupStyle"), ensure_ascii=False))
    print("★ 属于组的采样点数：%s / %d"
          % (res.get("属于组的点数"), len(res.get("hits", []))))
    for h in res.get("hits", []):
        mark = "★组" if h["isGroup"] else "  "
        print("  %s inset=%-3s %s (%s,%s) → %s cls=%s nodeId=%s"
              % (mark, h["inset"], h["edge"], h["x"], h["y"],
                 h["tag"], (h["cls"] or "")[:40], h["nodeId"]))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
