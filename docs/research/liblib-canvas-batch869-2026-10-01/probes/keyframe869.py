#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 869 探针：★ 「添加关键帧」在**无选中轨道**时的**真实行为**。

## ★ ★★ 要回答的问题（★ 用实测 ⟹ ⟹ 不猜）

★ 868 的普查把「添加关键帧」「删除关键帧」记成「点了没反应」
⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 但那次的普查用的是 `force=True`
⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ `force=True` 会**绕过** Playwright 对 `disabled` 的保护
⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 浏览器**仍然**忽略 disabled 按钮的点击
⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 所以「点了没反应」**可能**只是
⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 一个 disabled 按钮的**正常行为**。

★ 本探针做**三档**测量（★ 每档都读**实时**状态 ⟹ ⟹ 不靠记忆）：

| 档 | 状态 | 要读的 |
| --- | --- | --- |
| A | 默认（**有**默认选中轨道） | 两枚按钮的 `disabled`；点「添加」后关键帧数 |
| B | **清空选中轨道** | 两枚按钮的 `disabled`；点「添加」后关键帧数 |
| C | 选中一个轨道后再**清空选中关键帧** | 「删除」按钮的 `disabled` |

★ ★★ 判据的**关键**：★ 「按钮可点」**不等于**「点了会做事」
⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 所以每一档都要同时读 **disabled** 与 **点了之后的结果**
⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 两者的**组合**才说明问题在哪。

## 输出
  raw/keyframe-869.json
"""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, "/Users/yangjiefeng/.pyenv/shims")
from playwright.sync_api import sync_playwright  # noqa: E402

_C868 = pathlib.Path(__file__).resolve().parents[2] / (
    "liblib-canvas-batch868-2026-10-01/probes")
sys.path.insert(0, str(_C868))
import census868 as C  # noqa: E402

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
BATCH = ROOT / "docs/research/liblib-canvas-batch869-2026-10-01"
RAW = BATCH / "raw"

SEL_ADD = "[data-director-add-keyframe]"
SEL_DEL = "[data-director-delete-keyframe]"

READ = """()=>{
  // ★ ★★ 读**真 store**（★ `window.__director_store`）⟹ ⟹ ⟹ ⟹ ⇒ ★
  //   ★ 而**不是**数 DOM 上的关键帧个数 ⟹ ⟹ ⟹ ⟹ ⇒ ★
  //   ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ★★ 原因：★ `upsertTrackKeyframe` 是 **upsert**
  //   ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 当前时间点**已有**关键帧时
  //   ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 点「添加关键帧」是**覆盖**它
  //   ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⇒ **个数不变** ⟹ ⟹ ⟹ ⟹ ⇒
  //   ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⇒ ★★ 只数个数 ⟹ ⟹ ⟹ ⟹ ⇒ ★ **掩盖**了
  //   ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 「值被更新、选中态变了」这件事
  const st = window.__director_store && window.__director_store.getState();
  if(!st) return {错: 'store 没暴露'};
  const tl = st.timeline;
  const track = tl.tracks.find(t=>t.id===tl.selectedTrackId) || null;
  const kfs = track ? track.keyframes : [];
  const selKf = kfs.find(k=>k.id===tl.selectedKeyframeId) || null;
  const dom = (sel)=>{
    const e = document.querySelector(sel);
    if(!e) return null;
    return {hasDisabledAttr: e.hasAttribute('disabled'),
            ariaDisabled: e.getAttribute('aria-disabled'),
            title: e.getAttribute('title'),
            cursor: getComputedStyle(e).cursor,
            browserDisabled: e.disabled === true};
  };
  return {
    选中轨道id: tl.selectedTrackId,
    选中轨道label: track ? track.label : null,
    选中轨道kind: track ? track.kind : null,
    该轨道关键帧数: kfs.length,
    该轨道关键帧时间: kfs.map(k=>k.time),
    选中关键帧id: tl.selectedKeyframeId,
    选中关键帧值: selKf ? JSON.stringify(selKf.value).slice(0,200) : null,
    当前时间: tl.currentTime,
    add: dom('[data-director-add-keyframe]'),
    del: dom('[data-director-delete-keyframe]'),
  };
}"""

# ★ ★★ 清空「选中轨道」：★ 点轨道行的**空白处**（★ 不是选中态）
CLEAR_TRACK = """()=>{
  // ★ 点所有轨道行 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 让最后一次点击落在**没有选中态**的位置
  const rows=[...document.querySelectorAll('[data-director-track-id]')];
  rows.forEach(r=>r.setAttribute('aria-selected','false'));
  return rows.length;
}"""

CLEAR_KEYFRAME = """()=>{
  const kfs=[...document.querySelectorAll('[data-director-keyframe-id]')];
  kfs.forEach(k=>k.setAttribute('aria-pressed','false'));
  return kfs.length;
}"""


def read(pg) -> dict:
    return pg.evaluate(READ)


def snap(pg) -> dict:
    """★ 一个**可比**的快照（★ 只留会变的量）⟹ ⟹ ⟹ ⟹ ⇒ ★ 便于逐项对比。"""
    r = read(pg)
    if "错" in r:
        return r
    return {k: r.get(k) for k in ("选中轨道id", "该轨道关键帧数", "该轨道关键帧时间",
                                  "选中关键帧id", "选中关键帧值", "当前时间")}


def click_and_count(pg, sel) -> dict:
    """★ 点一下 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 记录**前后的可比快照**（★ 不是只数个数）。"""
    before = snap(pg)
    try:
        pg.locator(sel).first.click(force=True, timeout=5000)
        err = None
    except Exception as e:  # noqa: BLE001
        err = str(e)[:200]
    pg.wait_for_timeout(700)
    after = snap(pg)
    diff = {k: [before.get(k), after.get(k)] for k in before
            if before.get(k) != after.get(k)}
    return {"前": before, "后": after, "变了的量": diff,
            "有变化": bool(diff), "错误": err}


def main() -> int:
    out: dict = {"说明": "★ 三档测量 ⟹ ⟹ 每档都读实时状态 ＋ 点了之后的结果"}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                             locale="zh-CN")
        pg = ctx.new_page()
        pg.set_default_timeout(30_000)
        C.open_director(pg, dismiss=True)
        pg.wait_for_timeout(800)

        # ── 档 A：默认（有默认选中轨道）──
        out["档A_默认"] = read(pg)
        out["档A_点添加"] = click_and_count(pg, SEL_ADD)

        # ── 档 B：清空选中轨道 ──
        n = pg.evaluate(CLEAR_TRACK)
        pg.wait_for_timeout(400)
        out["档B_清空选中轨道_轨道行数"] = n
        out["档B_清空选中轨道"] = read(pg)
        out["档B_点添加"] = click_and_count(pg, SEL_ADD)
        out["档B_点删除"] = click_and_count(pg, SEL_DEL)

        # ── 档 C：重新选中一个轨道 ⟹ ⟹ 再清空选中关键帧 ──
        track_ids = pg.evaluate(
            "()=>[...document.querySelectorAll('[data-director-track-id]')]"
            ".map(e=>e.getAttribute('data-director-track-id'))")
        if track_ids:
            pg.evaluate(
                "(id)=>{const e=document.querySelector("
                "'[data-director-track-id=\"'+id+'\"]'); if(e) e.click();}",
                track_ids[0])
            pg.wait_for_timeout(600)
        m = pg.evaluate(CLEAR_KEYFRAME)
        pg.wait_for_timeout(400)
        out["档C_清空选中关键帧_数量"] = m
        out["档C_清空选中关键帧"] = read(pg)
        out["档C_点添加"] = click_and_count(pg, SEL_ADD)
        out["档C_点删除"] = click_and_count(pg, SEL_DEL)
        br.close()

    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "keyframe-869.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    # ★ 打印**结论表**
    for k in sorted(out):
        if not k.startswith("档"):
            continue
        v = out[k]
        if not isinstance(v, dict) or "add" not in v:
            print("%-26s %s" % (k, v))
            continue
        print("%-26s add.disabled=%s del.disabled=%s 选中轨道=%s 该轨道关键帧=%s 时间=%s"
              % (k, v["add"] and v["add"]["hasDisabledAttr"],
                 v["del"] and v["del"]["hasDisabledAttr"],
                 v.get("选中轨道id"), v.get("该轨道关键帧数"),
                 v.get("该轨道关键帧时间")))
    for k in sorted(out):
        if k.endswith(("点添加", "点删除")):
            v = out[k]
            print("  %-24s 有变化=%-5s 变了的量=%s"
                  % (k, v.get("有变化"),
                     list((v.get("变了的量") or {}).keys())))
    print("读数已落盘：%s" % (RAW / "keyframe-869.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
