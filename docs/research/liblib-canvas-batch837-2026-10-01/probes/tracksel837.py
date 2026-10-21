#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 837 探针（替代 750 丢失的 `/tmp/dbg750e.py`）：单点复验 750 的 C5 读数。

★ 为什么需要它：`scripts/verify-liblib-batch750.py` 的运行时探针在 `/tmp/dbg750e.py`
  （**从未入库** ⟹ 已随 /tmp 清空丢失）⟹ 整门禁跑不起来。
  本探针**只复验 750 的 C5 那一条**（轨道行内 role=button 的标题），
  用**与 750 当时同一口径**的读法 ⟹ 用来证明本批把 750 的期望值
  从「机位01 · 对峙中景 · 机位」改成「机位1 · 机位」是**对的**，
  而不是把一个没跑过的门禁改成橡皮章。

★ 口径（照抄 750 的 runtime-audit.json 里 `trackSelection` 的字段含义）：
  - 外壳：轨道行容器（无 data-* 标记，点它无效果）
  - 内壳：行内**没有 data-*** 的 `role="button"`（tabIndex=0）⟹ 它才是可点目标
  - `innerTitle` ⟹ 内壳的 textContent
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

BASE = "http://localhost:4317"
OUT = pathlib.Path("/tmp/b837-tracksel.json")


def main():
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto(BASE + "/?batch837b=1", wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
        page.wait_for_function("() => Boolean(window.__libtv_store && window.__director_store)",
                               timeout=60_000)
        page.evaluate("""() => {
            const cands = [...document.querySelectorAll('button,[role="button"]')];
            const b = cands.find(e => e.getAttribute('data-open-director') ||
                (e.textContent||'').includes('打开导演台') || (e.textContent||'').includes('导演台'));
            if (b) { b.click(); return true; } return false; }""")
        page.wait_for_timeout(1800)
        page.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")

        opened = page.evaluate("() => Boolean(document.querySelector('[data-director-workspace]'))")
        out["导演台已打开"] = opened
        if not opened:
            print("★ 导演台没打开")
            br.close()
            return 2

        # ★ 找轨道行：其内壳（role=button 且无 data-*）的 textContent
        # ★★ 口径修正（第一版踩坑）：第一版用「所有 role=button 里含『机位』的」来找内壳，
        #    读到的却是**对象行**的机位名（`机位1`）——对象行与轨道行**长得像但不是同一个元素**，
        #    且对象行是 `data-director-timeline-object-name`（**有** data-*）⟹ 正好被
        #    「内壳必须无 data-*」这条筛掉，剩下的「机位」是**图标按钮的 aria/文字**。
        #    ⟹ 修法：**先按轨道行外壳定位**（`[data-director-track-row-kind="camera"]`），
        #    再在**它内部**找 `role=button` 的内壳 ⟹ 元素类型与界面真实结构相交。
        info = page.evaluate("""() => {
          const rows = [...document.querySelectorAll('[data-director-track-row-kind="camera"]')];
          return rows.map(row => {
            const inner = [...row.querySelectorAll('[role="button"]')].filter(
              e => Object.keys(e.dataset||{}).length === 0);
            return {
              rowId: row.getAttribute('data-director-track-row'),
              outerDataKeys: Object.keys(row.dataset||{}),
              innerCount: inner.length,
              innerTitle: inner.map(e => (e.textContent||'').trim()),
              innerTitleAttr: inner.map(e => e.getAttribute('title')),
              innerHasData: inner.map(e => Object.keys(e.dataset||{}).length > 0),
            };
          });
        }""")
        out["相机轨道行"] = info

        # 找最像「机位 · 机位」的那个内壳
        # ★★ 口径修正（第二版）：轨道行的**显示文本**是 `directorTrackShortName(track)`
        #   （短名，只剩「机位」两字），**完整 label 在 `title` 属性里**
        #   （`DirectorTimeline.tsx:1817 title={track.label}`）⟹
        #   750 当时读到的「机位01 · 对峙中景 · 机位」**只能是 title 属性**（textContent 给不出后缀）
        #   ⟹ 本探针读 `title` ⟹ 与 750 的 `innerTitle` **同口径**。
        inner = []
        for row in info:
            for i, t in enumerate(row["innerTitleAttr"]):
                if not row["innerHasData"][i] and t and "机位" in t:
                    inner.append({"text": t, "rowId": row["rowId"],
                                  "titleAttr": t,
                                  "visibleText": row["innerTitle"][i]})
        out["内壳候选"] = inner
        out["innerTitle"] = inner[0]["text"] if inner else None
        out["innerTitle是否机位1 · 机位"] = out["innerTitle"] == "机位1 · 机位"
        out["★口径说明"] = (
            "innerTitle 读的是轨道行内壳（role=button，无 data-*）的 **title 属性** "
            "（= track.label 的完整串）⟹ 与 750 的 innerTitle 同口径；"
            "可见文本是 directorTrackShortName 的短名（不含「· 机位」后缀）"
        )

        # ★ 外壳：找含 data-* 的祖先（轨道行外壳）
        outer_info = page.evaluate("""() => {
          const row = document.querySelector('[data-director-track-row-kind="camera"]');
          if (!row) return null;
          return {
            rowDataKeys: Object.keys(row.dataset||{}),
            rowText: (row.textContent||'').trim(),
            hasDataMarkerOnInner: [...row.querySelectorAll('[role="button"]')]
              .map(e => Object.keys(e.dataset||{}).length > 0),
          };
        }""")
        out["轨道行外壳"] = outer_info

        page.close()
        ctx.close()
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("写入", OUT)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
