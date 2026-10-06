#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 806 探针 a：回收站的**完整动作面**普查 —— 「彻底删除」是入口为 0，还是没做

## 要回答的两个问题

① 755 ④ 记的是：`purgeRemovedCanvas` **零调用点** ⟹ 回收站没有「彻底删除」。
   今天仍然成立（静态：`src/store/canvasStore.ts:300` 只有类型声明、`:1221`
   只有实现，`src/` 里再无第三个出现处）。但这只回答了「渲染层没接」。
   ★ **没回答的是**：这个能力**本身是好的还是坏的** —— 两者处置完全不同
   （前者是「差一个入口」，后者是「先修能力再谈入口」）。本批把两者分开。
② 755 ④ 同时记了一条文案矛盾：删除确认框写「**此操作不可恢复**」，而实现是
   **软删除**（完整快照进回收站、30 天保留）。805 刚把那句「30 天」变成真的，
   于是这个矛盾**更尖锐**了：现在用户被告知「不可恢复」，而它其实可恢复 30 天，
   且**恢复入口在另一个路由**（`/project` 的回收站），画布里既不提示也不链接。

## 判据纪律

- 面板里**每一个可交互元素**都要被独立点名（文本/title/aria/data-*），
  不只报个数（803 的 S3 教训）。
- 「入口为 0」这个结论必须由**普查**给出，同时用**阳性对照**排除
  「我的普查器根本没看进去」——所以要逐个验证现存动作**真的有效果**。
- 能力与入口分开验：`purgeRemovedCanvas` **绕过 UI 直接调**，若它有效，
  那么结论才是「能力在、入口无」，而不是「功能没做」。
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"


def ev(pg, js, arg=None):
    try:
        return pg.evaluate(js) if arg is None else pg.evaluate(js, arg)
    except Exception as exc:
        return {"FAILED": type(exc).__name__ + ": " + str(exc)[:220]}


# ── 面板内可交互元素普查 ─────────────────────────────────────────────────
CENSUS = r"""()=>{
  const panel = document.querySelector('[data-recycle-panel]');
  if(!panel) return {open:false};
  const sel='button,input,[role="button"],a[href],[tabindex]';
  const rows=Array.from(panel.querySelectorAll(sel)).map((el,i)=>{
    const data={};
    for(const a of el.attributes) if(a.name.startsWith('data-')) data[a.name]=a.value;
    const r=el.getBoundingClientRect();
    return {i, tag:el.tagName, type:el.getAttribute('type'),
            ariaLabel:el.getAttribute('aria-label'), title:el.getAttribute('title'),
            disabled: el.disabled===true, data,
            text:(el.textContent||'').trim().slice(0,20),
            rect:{w:Math.round(r.width), h:Math.round(r.height)}};
  });
  const re=/删除|移除|清理|purge|delete|remove|永久|彻底/i;
  return {open:true, total:rows.length, rows,
          purgeLike: rows.filter(r=>re.test(
            [r.text,r.ariaLabel,r.title,Object.keys(r.data).join(' '),
             Object.values(r.data).join(' ')].join(' ')))};
}"""

# 面板里到底有几项、每项还剩几天
ITEMS = r"""()=>{
  const panel=document.querySelector('[data-recycle-panel]');
  if(!panel) return {open:false};
  return {open:true, empty: !!panel.querySelector('[data-recycle-empty]'),
          ids: Array.from(panel.querySelectorAll('[data-recycle-item]'))
                 .map(li=>li.getAttribute('data-recycle-item'))};
}"""

CLICK_RESTORE = r"""(id)=>{
  const b=document.querySelector('[data-recycle-restore="'+id+'"]');
  if(!b) return {ok:false, why:'no restore button'};
  if(b.disabled) return {ok:false, why:'restore disabled'};
  b.click(); return {ok:true};
}"""
CLICK_CHECK = r"""(id)=>{
  const c=document.querySelector('[data-recycle-check="'+id+'"]');
  if(!c) return {ok:false, why:'no checkbox'};
  c.click(); return {ok:true};
}"""
BATCH_RESTORE = """()=>{
  const b=document.querySelector('[data-recycle-restore-selected]');
  if(!b) return {ok:false, why:'no batch restore button'};
  if(b.disabled) return {ok:false, why:'batch restore disabled'};
  b.click(); return {ok:true};
}"""
SELECTION_TEXT = """()=>{const e=document.querySelector('[data-recycle-selection]');
  return e?(e.textContent||'').trim():null;}"""

# ★ 能力验算：绕过 UI 直接调 store 的彻底删除
PURGE_VIA_STORE = r"""(id)=>{
  const s=window.__libtv_store;
  if(!s) return {ok:false, why:'no store'};
  const before = s.getState();
  const wasRemoved = before.removedCanvases.some(c=>c.id===id);
  const wasLive   = before.canvases.some(c=>c.id===id);
  const snapshot  = (before.removedCanvases.find(c=>c.id===id)||{}).nodes;
  try { s.getState().purgeRemovedCanvas(id); }
  catch(e){ return {ok:false, why:'threw: '+String(e).slice(0,160)}; }
  const after = s.getState();
  return {ok:true, id, wasRemoved, wasLive,
          snapshotNodes: snapshot ? snapshot.length : null,
          stillInRemoved: after.removedCanvases.some(c=>c.id===id),
          appearedInLive: after.canvases.some(c=>c.id===id),
          removedCountBefore: before.removedCanvases.length,
          removedCountAfter: after.removedCanvases.length};
}"""

STATE_COUNTS = """()=>{const s=window.__libtv_store;
  if(!s) return null;
  const st=s.getState();
  return {canvases: st.canvases.length, removed: st.removedCanvases.length,
          activeCanvasId: st.activeCanvasId};}"""

DELETE_CONFIRM_COPY = r"""()=>{
  const box=document.querySelector('[data-canvas-delete-confirm]');
  if(!box) return {open:false};
  return {open:true, text:(box.textContent||'').trim().slice(0,120),
          saysUnrecoverable:/不可恢复/.test(box.textContent||'')};
}"""


def make_one_removed(ctx):
    """造出一个**回收站里有一项**的状态：走真实 UI 删一张画布 + 客户端路由。"""
    pg = ctx.new_page()
    try:
        pg.goto(BASE, wait_until="networkidle")
        pg.wait_for_selector("[data-canvas-trigger]", timeout=25000)
        pg.wait_for_timeout(1200)
        pg.evaluate("()=>document.querySelector('[data-canvas-trigger]').click()")
        pg.wait_for_selector("[data-canvas-row]", timeout=10000)
        pg.evaluate("()=>{const r=document.querySelector('[data-canvas-row]');"
                    "r.querySelector('[data-canvas-row-more]').click();}")
        pg.wait_for_selector('[data-canvas-row-menu-item="delete"]', timeout=10000)
        pg.evaluate("()=>document.querySelector('[data-canvas-row-menu-item=\"delete\"]').click()")
        pg.wait_for_selector("[data-canvas-delete-confirm]", timeout=10000)
        confirm_copy = ev(pg, DELETE_CONFIRM_COPY)
        pg.wait_for_timeout(400)
        ev(pg, """()=>{const box=document.querySelector('[data-canvas-delete-confirm]');
             const b=Array.from(box.querySelectorAll('button'))
               .find(x=>/^确认$/.test((x.textContent||'').trim()));
             if(b) b.click(); return {ok:!!b};}""")
        pg.wait_for_timeout(900)
        pg.evaluate("()=>document.querySelector('[data-project-menu-trigger]').click()")
        pg.wait_for_selector("[data-project-menu-item]", timeout=10000)
        pg.evaluate("()=>document.querySelector('[data-project-menu-item=\"全部项目\"]').click()")
        pg.wait_for_selector("[data-project-list-page]", timeout=25000)
        pg.wait_for_timeout(900)
        ev(pg, """()=>{if(document.querySelector('[data-recycle-panel]')) return;
             const b=Array.from(document.querySelectorAll('button'))
               .find(x=>/回收站/.test(x.textContent||''));
             if(b) b.click();}""")
        pg.wait_for_selector("[data-recycle-panel]", timeout=10000)
        pg.wait_for_timeout(500)
        return pg, confirm_copy
    except Exception as exc:
        pg.close()
        raise RuntimeError("造状态失败: %s: %s" % (type(exc).__name__, str(exc)[:200]))


def run_round(ctx, R):
    rec = {"round": R}
    pg, confirm_copy = make_one_removed(ctx)
    try:
        rec["deleteConfirmCopy"] = confirm_copy
        rec["state0"] = ev(pg, STATE_COUNTS)

        # ── 格 1：面板动作面普查（先测「恢复」有效，排除「普查器没看进去」）
        rec["census"] = ev(pg, CENSUS)
        items0 = ev(pg, ITEMS)
        rec["items0"] = items0
        rid = (items0.get("ids") or [None])[0]

        if rid:
            ev(pg, CLICK_RESTORE, rid)
            pg.wait_for_timeout(800)
            rec["restoreSingle"] = {"clicked": rid,
                                   "itemsAfter": ev(pg, ITEMS),
                                   "stateAfter": ev(pg, STATE_COUNTS)}

            # 重新删一张，测批量恢复
            pg.close()
            pg, _ = make_one_removed(ctx)
            items1 = ev(pg, ITEMS)
            ids1 = items1.get("ids") or []
            rec["items1"] = items1
            if ids1:
                ev(pg, CLICK_CHECK, ids1[0])
                pg.wait_for_timeout(400)
                # ★★ 普查必须记**两个状态**：批量恢复按钮是**条件渲染**的
                #   （`selectedRemoved.length > 0` 才出现），只在「未勾选」状态下
                #   普查会**少算一个**入口 ⟹ 那正是我在模块 docstring 里自己警告的
                #   「普查器没看进去」。所以勾选后**再普查一遍**。
                rec["censusAfterSelect"] = ev(pg, CENSUS)
                rec["batchRestore"] = {
                    "selectionText": ev(pg, SELECTION_TEXT),
                    "click": ev(pg, BATCH_RESTORE),
                    "itemsAfter": None, "stateAfter": None}
                pg.wait_for_timeout(800)
                rec["batchRestore"]["itemsAfter"] = ev(pg, ITEMS)
                rec["batchRestore"]["stateAfter"] = ev(pg, STATE_COUNTS)

            # ── 格 2：能力验算 —— 绕过 UI 直接调 purgeRemovedCanvas
            pg.close()
            pg, _ = make_one_removed(ctx)
            items2 = ev(pg, ITEMS)
            pid = (items2.get("ids") or [None])[0]
            rec["purgeViaStore"] = ev(pg, PURGE_VIA_STORE, pid) if pid else \
                {"FAILED": "no id to purge"}
            pg.wait_for_timeout(700)
            rec["afterPurge"] = {"items": ev(pg, ITEMS),
                                 "state": ev(pg, STATE_COUNTS)}
    finally:
        pg.close()
    return rec


def main():
    out_path = pathlib.Path(sys.argv[1])
    rounds = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        try:
            for R in range(2):
                ctx = br.new_context(viewport={"width": 1440, "height": 1000})
                try:
                    rounds.append(run_round(ctx, R))
                finally:
                    ctx.close()
        finally:
            br.close()
    out = {"batch": 806, "base": BASE, "rounds": rounds}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                        encoding="utf-8")
    for r in rounds:
        c = r.get("census") or {}
        p = r.get("purgeViaStore") or {}
        print("round %s ｜ 面板可交互 %s ｜ 删除类命中 %s ｜ purgeViaStore=%s ｜ after=%s"
              % (r["round"], c.get("total"),
                 [x["text"] or x["data"] for x in (c.get("purgeLike") or [])],
                 {k: p.get(k) for k in ("ok", "wasRemoved", "stillInRemoved",
                                        "appearedInLive")},
                 (r.get("afterPurge") or {}).get("state")))
    print("wrote %s" % out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())