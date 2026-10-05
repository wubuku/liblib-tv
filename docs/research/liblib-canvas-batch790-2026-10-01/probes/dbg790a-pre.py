#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 790 前置探针 —— 画布行内菜单到底**现在**还可达吗

## 为什么先测再改

Batch 755 记了一条**高严重度**读数：行内菜单（重命名/复制/删除）被祖先
容器的 `overflow` 裁掉 ⟹ 三项功能对多数用户**不可达**，且可达性取决于
**画布数量**与**行在列表里的位置**。

但那是 755 的读数。★ 改 `src/` 之前必须先确认缺陷**还在当前代码里** ——
CSS 上下文、类名、DOM 结构都可能已经变了。旧读数不能当现状。

## 测什么

对每个格子（画布数 × 行的位置）取四类**互相独立**的证据：

| 证据 | 怎么取 | 为什么单独一条 |
| --- | --- | --- |
| 几何 | 菜单 rect 与**每一个** `overflow != visible` 祖先的 rect | 说清「被谁裁」而不是猜 |
| 命中 | 每项中心 `elementFromPoint` 落回它自己吗 | 几何只说「可能」 |
| 功能 | 真点一次「重命名画布」，出行内 input 吗 | 命中说「点得到」，功能说「点了有用」 |
| ★ 阳性对照 | 有一个格子**本来就该全可点**，且实测全可点 | 755 的 R18：没有阳性对照，「不可点」和「我没点到」无法区分 |

## 顺带记录

菜单的**祖先裁剪链**完整写进 raw ⟹ 「被谁裁」是读出来的，不是推断的。

## 格数

画布数 {2, 6} × 行 {首, 末} × 2 轮 = 8 格
"""
import json
import pathlib
import sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

#: ★ 前置与后置**共用同一份测量代码**（`dbg790a.py pre` / `dbg790a.py post`）
#: ⟹ before/after 的差异只能来自 `src/`，不能来自探针本身换了写法
PHASE = sys.argv[1] if len(sys.argv) > 1 else "pre"
assert PHASE in ("pre", "post"), "★ 阶段只能是 pre / post，收到 %r" % PHASE

OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
    "liblib-canvas-batch790-2026-10-01/raw/vb790a-%s.json" % PHASE)

TRIGGER = "[data-canvas-trigger]"
NEW = "[data-canvas-new]"
ROW = "[data-canvas-row]"
MORE = '[aria-label="更多操作"]'
OVERLAY = '[data-liblib-overlay="canvas-dropdown"]'

ITEMS = ["在新窗口打开", "重命名画布", "复制画布", "删除画布"]

#: ★ 只**读**：菜单的裁剪链 + 每项命中。★ 不在这里 click（见 R20）
MEASURE = """(idx)=>{
  const rows=[...document.querySelectorAll('[data-canvas-row]')];
  if(!rows.length) return {FAILED:'没有画布行', rowCount:0};
  const i = idx < 0 ? rows.length + idx : idx;
  const row = rows[i];
  if(!row) return {FAILED:'行不存在', rowCount:rows.length, idx};
  const more = row.querySelector('[aria-label="更多操作"]');
  if(!more) return {FAILED:'行里没有「更多操作」', rowCount:rows.length};
  const R=(r)=>({t:Math.round(r.top),b:Math.round(r.bottom),
                  l:Math.round(r.left),r:Math.round(r.right),
                  w:Math.round(r.width),h:Math.round(r.height)});
  // ★ 菜单是否真的开着
  const rename=[...document.querySelectorAll('button')]
    .find(b=>(b.textContent||'').trim()==='重命名画布');
  if(!rename) return {FAILED:'菜单没打开', rowCount:rows.length, idx};
  const menu=rename.parentElement;
  const mr=menu.getBoundingClientRect();
  // ★ 裁剪链：★ 从 `menu.parentElement` 起（**不是** menu 自己 ——
  //   menu 自己也有 `overflow-hidden rounded-lg`，从它起会把**自己**
  //   报成第一个裁剪者，读数就没有信息量了。R21）
  //
  // ★★ R23：光看「祖先 rect 装不下菜单」是**不够**的 —— 还要看那个祖先
  //   **在不在菜单的包含块链上**。`position: absolute` 的包含块是最靠近的
  //   定位祖先，`position: fixed` 的包含块是**视口** ⟹ 后者一个祖先都裁不到它。
  //   ⟹ 所以必须记下每个祖先的 `position`，再按规则挑出**真**裁剪者。
  //   （第一批 post 读数里「裁下边的=2」就是这么来的假阳性：菜单改成 fixed
  //     之后那两个祖先根本不在它的包含块链上。）
  const menuPos = getComputedStyle(menu).position;
  const chain=[]; let n=menu.parentElement;
  while(n && n!==document.body){
    const cs=getComputedStyle(n);
    const ox=cs.overflowX, oy=cs.overflowY;
    if(ox!=='visible'||oy!=='visible'){
      const r=n.getBoundingClientRect();
      chain.push({tag:n.tagName, position:cs.position, overflowX:ox, overflowY:oy,
        hasRounded:/\brounded/.test(n.className||''),
        rect:R(r),
        // 纯几何：这个祖先的盒子有没有装不下菜单
        rectTooSmall: mr.bottom > r.bottom});
    }
    n=n.parentElement;
  }
  // ★ 真裁剪者 = 「在包含块链上」且「裁到」的那些
  const realClippers = menuPos === 'fixed' ? [] : chain.filter(
      c => c.position !== 'static' && c.rectTooSmall);
  // ★ 每项：几何 + 命中（点中心，看落回谁）
  const items=[...menu.querySelectorAll('button')].map(b=>{
    const r=b.getBoundingClientRect();
    const cx=Math.round(r.left+r.width/2), cy=Math.round(r.top+r.height/2);
    const hit=document.elementFromPoint(cx,cy);
    return {text:(b.textContent||'').trim(), rect:R(r),
      point:[cx,cy],
      pointInViewport: cx>=0&&cy>=0&&cx<=innerWidth&&cy<=innerHeight,
      hitIsSelf: !!(hit&&hit.closest&&hit.closest('button')===b),
      hitTag: hit?hit.tagName:null,
      hitText: hit?(hit.textContent||'').trim().slice(0,10):null};
  });
  return {rowCount:rows.length, idx:i, rowRect:R(row.getBoundingClientRect()),
          menuRect:R(mr), menuPosition:menuPos, chain, realClippers,
          items, menuTexts: items.map(x=>x.text)};
}"""

#: ★ 只**读**：点完「重命名画布」之后看有没有出行内 input
FUNC = """()=>{
  const input=[...document.querySelectorAll('[data-canvas-row] input')][0]||null;
  return {inputAppeared:!!input,
          inputFocused: !!(input && document.activeElement===input),
          overlayStillOpen: !!document.querySelector('[data-liblib-overlay="canvas-dropdown"]')};
}"""


def boot(pg):
    """★ 画布级轻量启动：**不开**导演台（`A.fresh` 会开）。"""
    pg.goto(A.BASE, wait_until="domcontentloaded")
    pg.evaluate(A.CLEAR_LS, A.LS_KEY)
    pg.set_viewport_size({"width": 1440, "height": 1000})
    pg.goto(A.BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1100)


def click(pg, sel, nth=0):
    """★ 用扫描法点第 `nth` 个匹配（同一个选择器可能有多处）。"""
    s = pg.evaluate("""(a)=>{const sel=a.sel, n=a.nth;
      const el=document.querySelectorAll(sel)[n];
      if(!el) return {missing:true};
      if(el.disabled) return {disabled:true};
      const r=el.getBoundingClientRect();
      for(let f=0.08; f<=0.95; f+=0.07)
        for(let g=0.08; g<=0.95; g+=0.07){
          const x=Math.round(r.x+r.width*f), y=Math.round(r.y+r.height*g);
          if(x<2||y<2||x>innerWidth-2||y>innerHeight-2) continue;
          const e=document.elementFromPoint(x,y);
          if(e&&e.closest&&e.closest(sel)===el) return {pt:[x,y]};}
      return {noHit:true};}""", {"sel": sel, "nth": nth})
    if not s.get("pt"):
        return False
    pg.mouse.click(s["pt"][0], s["pt"][1])
    pg.wait_for_timeout(260)
    return True


def click_text(pg, text):
    """★ 点**文案完全相等**的那个按钮（真实鼠标 + 等一拍）。

    ★ R20：第一版在**同一次 evaluate 里** `.click()` 然后立刻读 DOM，
    React 的 state 还没 flush ⟹ 8 格全读成「菜单没打开」。
    ⟹ 规矩：**click 与读必须分开成两步**，中间真的要等一拍。
    """
    pt = pg.evaluate("""(t)=>{
      const b=[...document.querySelectorAll('button')]
        .find(x=>(x.textContent||'').trim()===t);
      if(!b) return null;
      const r=b.getBoundingClientRect();
      if(!r.width||!r.height) return {zero:true};
      return {pt:[Math.round(r.left+r.width/2),
                  Math.round(r.top+r.height/2)]};}""", text)
    if not pt or not pt.get("pt"):
        return False
    pg.mouse.click(pt["pt"][0], pt["pt"][1])
    pg.wait_for_timeout(300)          # ★ 等 React flush
    return True


def run_cell(pg, want_canvases, which):
    """which: 'first' | 'last'"""
    boot(pg)
    if not click(pg, TRIGGER):
        return {"FAILED": "点不到画布触发器"}
    if not pg.evaluate("()=>!!document.querySelector('%s')" % OVERLAY):
        return {"FAILED": "下拉没开"}
    # ★ 加到目标画布数（点「新建画布」会 closeDropdown ⟹ 每加一次都要重开）
    cur = pg.evaluate("()=>document.querySelectorAll('%s').length" % ROW)
    for _ in range(max(0, want_canvases - cur)):
        if not click(pg, NEW):
            return {"FAILED": "点不到新建画布", "cur": cur}
        if not click(pg, TRIGGER):
            return {"FAILED": "重开下拉失败", "cur": cur}
        cur = pg.evaluate("()=>document.querySelectorAll('%s').length" % ROW)
    idx = 0 if which == "first" else -1
    # ★ R22：`document.querySelectorAll(sel)[-1]` 在 JS 里是 `undefined`
    #   （数组**没有**负索引）⟹ 「末行」第一版全部 FAILED「点不到更多操作」。
    #   ⟹ 负索引必须在 Python 侧先问出行数再翻译成正索引。
    n_rows = pg.evaluate("()=>document.querySelectorAll('%s').length" % ROW)
    pos = idx if idx >= 0 else n_rows + idx
    # ★ 第一步：真点该行的「更多操作」（hover 才显形，但 `opacity-0` 不挡命中）
    if not click(pg, MORE, nth=pos):
        return {"FAILED": "点不到「更多操作」", "cur": cur, "nRows": n_rows}
    # ★ 第二步：只读几何与命中
    m = pg.evaluate(MEASURE, idx)
    if m.get("FAILED"):
        m["FAILED"] = "%s @cur=%s" % (m["FAILED"], cur)
        return m
    # ★ 第三步：真点「重命名画布」⟹ 第四步：只读有没有出行内 input
    hit_rename = click_text(pg, "重命名画布")
    f = pg.evaluate(FUNC)
    f["renameClickDispatched"] = hit_rename
    m["func"] = f
    m["wantCanvases"] = want_canvases
    m["which"] = which
    return m


def main():
    cells = [(2, "first"), (2, "last"), (6, "first"), (6, "last")]
    rounds = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        for rd in range(2):
            rows = []
            for want, which in cells:
                cell, tries = None, 0
                for t in range(3):
                    pg = b.new_page()
                    pg.set_default_timeout(15000)
                    tries = t + 1
                    try:
                        cell = run_cell(pg, want, which)
                    except Exception as e:      # noqa: BLE001
                        cell = {"FAILED": "%s: %s" % (type(e).__name__, e)}
                    finally:
                        try:
                            pg.close()
                        except Exception:       # noqa: BLE001
                            pass
                    if not cell.get("FAILED"):
                        break
                cell["tries"] = tries
                rows.append(cell)
                # ★ 一行摘要：几何 + 每项命中 + 功能
                if cell.get("FAILED"):
                    msg = "FAILED:%s" % cell["FAILED"]
                else:
                    parts = []
                    for it in cell["items"]:
                        parts.append("%s%s" % (it["text"][:4],
                                               "✓" if it["hitIsSelf"] else "✗"))
                    msg = ("menu %s %d-%d | 真裁剪=%d | %s | input=%s"
                           % (cell["menuPosition"], cell["menuRect"]["t"],
                              cell["menuRect"]["b"],
                              len(cell["realClippers"]), " ".join(parts),
                              cell["func"].get("inputAppeared")))
                print("  r%d %d张·%-5s %s" % (rd + 1, want, which, msg),
                      flush=True)
            rounds.append({"round": rd + 1, "rows": rows})
        b.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"batch": 790, "phase": PHASE,
                               "rounds": rounds},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
