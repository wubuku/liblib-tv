#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 803 探针 a：导演台撤销/重做入口 —— **先量几何，再决定放不放得下**

## 为什么要先量

750 留了一条待拍板 ③：「撤销/重做要不要给按钮（功能已完整，151 个可交互节点
**0 个**入口，鼠标用户无路）」。同时我自己在待办里写了一句「header 右列 280px
**已塞满**，需先量几何」。

★ 这句「已塞满」是**未经测量的假设**，必须实测才能决定这按钮到底放不放得下。
本探针只做测量与现状普查，**不改任何代码**。

## 三格读数

  格 1 `headerRightColumn` —— 右列 280px 容器与**每一个直接子元素**的矩形、
        文本、标记，再算余量。注意容器是 `justify-between` + `gap-2`，
        所以「塞满」不是简单相加，得按 flex 的实际排布算。
  格 2 `interactiveCensus` —— 导演台内全部可交互元素逐个列出（含
        `data-*` / `aria-label` / `title` / 文本），并按撤销/重做语义筛一遍。
        独立复核 750 那句「151 个里 0 个入口」，而不是引用它。
  格 3 `undoKeyboard` —— **阳性对照**：先用时间线的预设一键建一条运动轨迹
        （`data-director-motion-path-count` 是 DOM 可观测读数），再按 `Cmd+Z`，
        看这个读数会不会回退。★ 这一格不证明「按钮该做」，它证明的是
        **撤销真的有 DOM 后果、而且后果可测** ⟹ 否则按钮点了也验不了。

## 判据纪律

- 探针**不取整**：`getBoundingClientRect()` 的浮点值原样记录（799 的教训：
  `Math.round` 会把亚像素藏起来）。
- 每格之前都回到「画布起点 + 重新打开导演台」，绝不把上一格状态带进下一格。
- 4317 是多人共用 ⟹ **不并发**跑多个浏览器脚本。
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path(
    "/Users/yangjiefeng/Documents/wubuku/liblib-tv"
    "/docs/research/liblib-canvas-batch803-2026-10-01/raw/vb803a-pre.json")

CANVAS_UP = "()=>!!document.querySelector('[data-open-director]')"

# ── 格 1：header 右列几何 ────────────────────────────────────────────────
# 右列容器没有独立 data-*，按 class 里的 `min-[899px]:w-[280px]` 认：
# 只取 header 内、className 同时含 `w-[280px]` 与 `justify-end` 的那个 div。
RIGHT_COL = r"""()=>{
  const header = document.querySelector('[data-director-header]');
  if (!header) return {found:false, why:'no header'};
  const col = Array.from(header.querySelectorAll('div'))
      .find(d => /w-\[280px\]/.test(d.className||'')
                && /justify-end/.test(d.className||''));
  if (!col) return {found:false, why:'no 280px column'};
  const cr = col.getBoundingClientRect();
  const kids = Array.from(col.children).map((el,i)=>{
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    const data = {};
    for (const a of el.attributes) if (a.name.startsWith('data-')) data[a.name]=a.value;
    return {i, tag:el.tagName,
            data, ariaLabel:el.getAttribute('aria-label'),
            title:el.getAttribute('title'),
            disabled: el.disabled === true,
            text:(el.textContent||'').trim().slice(0,28),
            rect:{x:r.x,y:r.y,w:r.width,h:r.height},
            // ★ 内层身份：右列有一枚**匿名包裹层**（`div.relative` 装导出按钮），
            //   它自己既无 aria-label 也无文本（按钮里只有图标）⟹ 只看直接子元素
            //   自身的属性，这一项就是「认不出来」。S3 因此要求每个子元素
            //   **自身或内层**至少能命名一次。
            nested: Array.from(el.querySelectorAll('button,[aria-label],[title]'))
                .slice(0,4).map(n=>({tag:n.tagName,
                                     ariaLabel:n.getAttribute('aria-label'),
                                     title:n.getAttribute('title'),
                                     text:(n.textContent||'').trim().slice(0,20)})),
            computed:{width:cs.width,minWidth:cs.minWidth,maxWidth:cs.maxWidth,
                      flex:cs.flex, gap:cs.gap, padding:cs.padding,
                      justifyContent:cs.justifyContent, overflow:cs.overflow}};
  });
  const cs = getComputedStyle(col);
  const gap = parseFloat(cs.gap) || 0;
  const padL = parseFloat(cs.paddingLeft)||0, padR = parseFloat(cs.paddingRight)||0;
  const used = kids.reduce((s,k)=>s+k.rect.w,0) + gap*Math.max(0,kids.length-1);
  return {found:true,
          col:{rect:{x:cr.x,y:cr.y,w:cr.width,h:cr.height},
               className:col.className,
               computed:{width:cs.width,padding:cs.padding,gap:cs.gap,
                         justifyContent:cs.justifyContent, overflow:cs.overflow,
                         boxSizing:cs.boxSizing}},
          budget:{inner: cr.width - padL - padR, kidsWidth: used,
                  gaps: gap*Math.max(0,kids.length-1),
                  slack: (cr.width - padL - padR) - used},
          kids};
}"""

# ── 格 2：全部可交互元素普查 ─────────────────────────────────────────────
# 750 查过四条路（文本/title/aria-label/属性名）。本探针把**四条路一起**记下来，
# 并且把每个元素的 data-* 全量带上，避免「换个命名就查不到」。
INTERACTIVE = r"""()=>{
  const d = document.querySelector('[role="dialog"][aria-modal="true"]');
  if (!d) return {open:false};
  const sel = 'button,[role="button"],a[href],input,select,textarea,[tabindex]';
  const all = Array.from(d.querySelectorAll(sel));
  const rows = all.map((el,i)=>{
    const data = {};
    for (const a of el.attributes) if (a.name.startsWith('data-')) data[a.name]=a.value;
    return {i, tag:el.tagName, role:el.getAttribute('role'),
            tabindex:el.getAttribute('tabindex'),
            ariaLabel:el.getAttribute('aria-label'),
            title:el.getAttribute('title'),
            type:el.getAttribute('type'),
            disabled: el.disabled === true,
            data, text:(el.textContent||'').trim().slice(0,24)};
  });
  const re = /撤销|重做|undo|redo|回退|恢复|复原/i;
  const hits = rows.filter(r => re.test([r.text,r.ariaLabel,r.title,
              Object.keys(r.data).join(' '),Object.values(r.data).join(' ')].join(' ')));
  // 命中判定逐条给出「命中了哪个字段」，不只给布尔
  const which = hits.map(h=>({i:h.i, tag:h.tag,
      inText:re.test(h.text), inAria:re.test(h.ariaLabel||''),
      inTitle:re.test(h.title||''),
      inDataName:re.test(Object.keys(h.data).join(' ')),
      inDataValue:re.test(Object.values(h.data).join(' ')),
      text:h.text, ariaLabel:h.ariaLabel, title:h.title}));
  return {open:true, total: rows.length, hits: hits.length, which, sample: rows.slice(0,6)};
}"""

# ── 格 3：阳性对照 —— Cmd+Z 有没有 DOM 后果 ───────────────────────────────
PATH_COUNT = r"""()=>{
  const e = document.querySelector('[data-director-motion-path-count]');
  return {present: !!e, count: e ? Number(e.getAttribute('data-director-motion-path-count')) : null};
}"""

# 建一条运动轨迹：点轨道行（role=button）→ 开菜单 → 点预设
CREATE_PATH = r"""()=>{
  const rows = Array.from(document.querySelectorAll('[role="button"]'))
      .filter(e => /机位/.test(e.getAttribute('title')||e.textContent||''));
  if (!rows.length) return {ok:false, why:'no track row'};
  const r = rows[0];
  r.dispatchEvent(new MouseEvent('click',{bubbles:true}));
  return {ok:true, title:r.getAttribute('title'), text:(r.textContent||'').trim().slice(0,20)};
}"""
OPEN_MENU = r"""()=>{
  const b = document.querySelector('[data-director-create-motion-path]');
  if (!b) return {ok:false, why:'no trigger'};
  if (b.disabled) return {ok:false, why:'trigger disabled'};
  b.click();
  return {ok:true};
}"""
CLICK_PRESET = r"""()=>{
  const all = Array.from(document.querySelectorAll('[data-director-motion-path-preset]'));
  if (!all.length) return {ok:false, why:'no preset', allLabels: []};
  const b = all[0];
  const v = b.getAttribute('data-director-motion-path-preset');
  b.click();
  // ★ 把整组预设的标记与文案都记下来：起点被污染时菜单内容会变，
  //   只记点中的那一个会看不出「其实点的不是同一个按钮」。
  return {ok:true, preset:v, label:(b.textContent||'').trim(),
          indexInGroup: 0, groupSize: all.length,
          allLabels: all.map(x=>(x.getAttribute('data-director-motion-path-preset')
                        + '|' + (x.textContent||'').trim()))};
}"""


def open_desk(pg):
    """每次都从画布起点重新打开导演台。"""
    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_selector(".react-flow__node", timeout=25000)
    pg.wait_for_timeout(1200)
    pg.evaluate("()=>{const b=document.querySelector('[data-open-director]');"
                "if(b)b.click();}")
    pg.wait_for_selector('[role="dialog"][aria-modal="true"]', timeout=25000)
    pg.wait_for_timeout(2500)          # 等面板与懒加载子组件落定


def ensure_path_zero(pg, tries=6):
    """★ 把 `path-count` 真的撤回 0，并**核验**它回到 0。

    ## 第一版没有这一步，读数直接作废了

    第一版假设「`pg.goto` 重新加载 = 回到起点」。**不成立**：导演台工作区**跨页面
    重载被持久化**，所以第二轮的起点 `path-count` 是 **1** 而不是 0，于是
    「建一条 → 1」「撤销 → 1」读出一组毫无意义的数。

    ★ 更隐蔽的信号：第二轮点到的预设按钮**文案都变了**（「直线路径」变成
    「机位自动帧轨迹」）—— 起点被污染时，菜单里的内容也跟着变了。
    ★ 这正是 750 定的规矩：**一条链路只问一个问题，问之前必须能从
      `path-count` 读到 0**。第一版我自己违反了它。

    这里不去 `localStorage.clear()`：4317 是多人共用，且清空会把种子画布也带走。
    只用**同一个浏览器上下文里**反复撤销把它撤干净，撤不干净就**如实作废**。
    """
    seen = []
    for t in range(tries):
        cur = pg.evaluate(PATH_COUNT)
        seen.append(cur.get("count"))
        if cur.get("count") == 0:
            return {"ok": True, "tries": t, "seen": seen}
        pg.keyboard.press("Meta+z")
        pg.wait_for_timeout(700)
    cur = pg.evaluate(PATH_COUNT)
    seen.append(cur.get("count"))
    return {"ok": cur.get("count") == 0, "tries": tries, "seen": seen}


def run_round(pg, R, br_ctx):
    rec = {"round": R}

    # ── 格 1 + 格 2 同一次打开（纯读，不改状态）
    open_desk(pg)
    rec["headerRightColumn"] = pg.evaluate(RIGHT_COL)
    rec["interactiveCensus"] = pg.evaluate(INTERACTIVE)

    # ── 格 3：建路径 → 读 → Cmd+Z → 再读（阳性对照）
    rec["undoKeyboard"] = {"FAILED": None}
    try:
        open_desk(pg)
        # ★ 前提闸：起点必须真的是 0，撤不干净就把这一臂**显式作废**
        zero = ensure_path_zero(pg)
        before = pg.evaluate(PATH_COUNT)
        if not zero.get("ok") or before.get("count") != 0:
            rec["undoKeyboard"] = {
                "FAILED": None, "INVALID": True,
                "why": "★ 起点 path-count 不是 0 ⟹ 这一臂不成立，"
                       "读数没有意义（第一版就是栽在这里）",
                "ensureZero": zero, "before": before}
            return rec
        picked = pg.evaluate(CREATE_PATH)
        pg.wait_for_timeout(500)
        opened = pg.evaluate(OPEN_MENU)
        pg.wait_for_timeout(400)
        preset = pg.evaluate(CLICK_PRESET)
        pg.wait_for_timeout(900)
        afterCreate = pg.evaluate(PATH_COUNT)
        pg.keyboard.press("Meta+z")
        pg.wait_for_timeout(900)
        afterUndo = pg.evaluate(PATH_COUNT)
        pg.keyboard.press("Meta+Shift+z")
        pg.wait_for_timeout(900)
        afterRedo = pg.evaluate(PATH_COUNT)
        rec["undoKeyboard"] = {"FAILED": None, "ensureZero": zero,
                               "before": before,
                               "pickedTrack": picked, "openedMenu": opened,
                               "clickedPreset": preset,
                               "afterCreate": afterCreate,
                               "afterUndo": afterUndo,
                               "afterRedo": afterRedo}
    except Exception as exc:            # 一格坏掉不许把整轮带走
        rec["undoKeyboard"] = {"FAILED": type(exc).__name__ + ": " + str(exc)[:220]}

    # ── 格 4：重载之后，文档还在吗？撤销还活着吗？
    # ★ 这条是**撞出来的**：第二版探针第二轮起点 `path-count` 是 1，
    #   「反复 Cmd+Z 撤回 0」连按 6 次**一次都没降**。撞出来的观察不能当结论，
    #   所以单开一格**专门去测**，问三个问题：
    #     ① 重载后 `path-count` 还在 1 吗 ⟹ 文档有没有被持久化
    #     ② 重载后连按 Cmd+Z，它降吗 ⟹ 历史栈还在不在
    #     ③ 这两件事同时成立意味着什么（读数说话，结论不预写）
    rec["reloadPersistence"] = {"FAILED": None}
    try:
        ctx2 = br_ctx.new_context(viewport={"width": 1440, "height": 1000})
        p2 = ctx2.new_page()
        try:
            open_desk(p2)
            start = p2.evaluate(PATH_COUNT)
            p2.evaluate(CREATE_PATH);      p2.wait_for_timeout(500)
            p2.evaluate(OPEN_MENU);        p2.wait_for_timeout(400)
            p2.evaluate(CLICK_PRESET);     p2.wait_for_timeout(900)
            afterCreate = p2.evaluate(PATH_COUNT)

            # ★★ **格内阳性对照**。没有这一步，「重载后撤销失效」这条结论
            #   撑不住 —— 它同样可以由「这一格导演台整体就不对」造成。
            #   所以**在重载之前**先把撤销/重做各走一次，证明这一格里的
            #   撤销**确实是活的**，这样后面「按了没反应」才是变化而非恒态。
            p2.keyboard.press("Meta+z");      p2.wait_for_timeout(700)
            inCellUndo = p2.evaluate(PATH_COUNT)
            p2.keyboard.press("Meta+Shift+z"); p2.wait_for_timeout(700)
            inCellRedo = p2.evaluate(PATH_COUNT)

            open_desk(p2)                  # ★ 重新加载并重新打开导演台
            afterReload = p2.evaluate(PATH_COUNT)

            seq = []
            for _ in range(3):
                p2.keyboard.press("Meta+z")
                p2.wait_for_timeout(700)
                seq.append(p2.evaluate(PATH_COUNT).get("count"))

            rec["reloadPersistence"] = {
                "FAILED": None, "start": start, "afterCreate": afterCreate,
                "inCellUndo": inCellUndo, "inCellRedo": inCellRedo,
                "afterReload": afterReload,
                "undoAfterReload": seq,
                "inCellUndoWorked": inCellUndo.get("count") == 0,
                "documentSurvivedReload": afterReload.get("count") == afterCreate.get("count"),
                "undoAliveAfterReload": any(c == 0 for c in seq)}
        finally:
            ctx2.close()
    except Exception as exc:
        rec["reloadPersistence"] = {"FAILED": type(exc).__name__ + ": " + str(exc)[:220]}
    return rec


def strip(o):
    """去掉坐标类噪声里不可复现的部分之外的一切：不 strip 任何读数。"""
    return o


def main():
    rounds = []
    br_state = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)      # ★ 一律 headless
        try:
            # ★★ **每一轮一个全新 context**。这不是洁癖，是被读数逼出来的：
            #   第一版两轮共用一个 context，第二轮起点 `path-count` 是 1。
            #   第二版加「反复 Cmd+Z 撤回 0」，结果**连按 6 次一直是 1** ——
            #   ★ 因为导演台**持久化的是文档、不是历史栈** ⟹ 重载后
            #   `history.past` 是空的，无从撤销，只撤得掉本会话内的命令。
            #   ⟹ 撤销根本不是清场的正确工具，得换**隔离**。
            #   全新 context 天然是空的种子状态，且只影响自己那一轮
            #   （4317 多人共用，绝不去动共享存储）。
            for R in range(2):
                ctx = br.new_context(viewport={"width": 1440, "height": 1000})
                pg = ctx.new_page()
                try:
                    rounds.append(run_round(pg, R, br))
                finally:
                    ctx.close()
        finally:
            br.close()
    out = {"batch": 803, "phase": "pre", "base": BASE, "rounds": rounds,
           "browserState": br_state}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in rounds:
        c = r.get("headerRightColumn") or {}
        u = r.get("undoKeyboard") or {}
        print("round %s ｜ 右列 %s ｜ 余量 %s ｜ 可交互 %s ｜ 撤销命中 %s ｜ path %s→%s→%s%s"
              % (r["round"], c.get("col", {}).get("rect", {}).get("w"),
                 (c.get("budget") or {}).get("slack"),
                 (r.get("interactiveCensus") or {}).get("total"),
                 (r.get("interactiveCensus") or {}).get("hits"),
                 (u.get("before") or {}).get("count"),
                 (u.get("afterCreate") or {}).get("count"),
                 (u.get("afterUndo") or {}).get("count"),
                 "  ★作废" if u.get("INVALID") else ""))
    print("wrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())