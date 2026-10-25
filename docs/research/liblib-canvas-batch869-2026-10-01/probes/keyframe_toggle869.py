#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""★★★ ★★ SUPERSEDED（★ 已被作废 ⟹ ⟹ ⟹ ⟹ ⇒ ★ **不要**照它写新探针）★★★ ★★
#
# ★ 本脚本编码的是 batch 869 **一度走错的方向**：★ 把工具条那枚「添加关键帧」
# ★ 改成「有则移除、无则添加」的**切换**语义。
#
# ★ ★★ 它**已被撤回** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 理由（★ 源站 batch 36 逐字规格 ⟹ ⟹ ⟹ ⟹ ⇒ ★
# ★ `docs/research/liblib-canvas-batch36-2026-08-26/DIRECTOR_TIMELINE.spec.md`）：
# ★   `◆ 添加关键帧` captures the selected track object's complete current value;
# ★   same-time add replaces the existing keyframe value;
# ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 那是「**取当前值、同时刻覆盖**」⟹ ⟹ ⟹ ⟹ ⇒ ★ **不是**切换。
#
# ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 真正生效的探针是**同目录**的 `keyframe_window869.py`
# ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ （13 条判据全绿）⟹ ⟹ ⟹ ⟹ ⇒ ★ 它验的是**命中窗口 ±0.05s**。
# ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ 完整更正记录见 `raw/source-869-correction.md`（★ 更正 ②）。
#
# ★ ★★ 本文件**原样保留**作为痕迹 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 追加式记录不可重写。
# ─────────────────────────────────────────────────────────────────────────────
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

SEL = "[data-director-add-keyframe]"

READ = """()=>{
  const st = window.__director_store && window.__director_store.getState();
  if(!st) return {错:'store 没暴露'};
  const tl = st.timeline;
  const track = tl.tracks.find(t=>t.id===tl.selectedTrackId) || null;
  const kfs = track ? track.keyframes : [];
  const btn = document.querySelector('[data-director-add-keyframe]');
  return {
    选中轨道id: tl.selectedTrackId,
    当前时间: tl.currentTime,
    该轨道关键帧时间: kfs.map(k=>k.time),
    该轨道关键帧数: kfs.length,
    按钮ariaLabel: btn ? btn.getAttribute('aria-label') : null,
    按钮title: btn ? btn.getAttribute('title') : null,
    按钮ariaPressed: btn ? btn.getAttribute('aria-pressed') : null,
    按钮文字: btn ? (btn.textContent||'').trim() : null,
    按钮toggleState: btn ? btn.getAttribute('data-director-keyframe-toggle-state') : null,
    按钮disabled: btn ? btn.disabled : null,
  };
}"""

# ★ ★★ 把播头**精确**设到某个时间（★ 走 store 的 `setTimelineTime`）
SET_TIME = """(t)=>{
  const st = window.__director_store.getState();
  st.setTimelineTime(t);
  return st.timeline.currentTime;
}"""

# ★ ★★ 选中一个轨道
SELECT_TRACK = """(id)=>{
  const el = document.querySelector('[data-director-track-id="'+id+'"]');
  if(!el) return false;
  el.click();
  return true;
}"""


def read(pg) -> dict:
    return pg.evaluate(READ)


def click(pg) -> dict:
    before = read(pg)
    pg.locator(SEL).first.click(force=True, timeout=5000)
    pg.wait_for_timeout(700)
    after = read(pg)
    return {"前": before, "后": after}


def main() -> int:
    out: dict = {"说明": "★ 全部判据只从实测读数来"}
    checks: list[dict] = []

    def chk(name: str, ok: bool, detail=None) -> None:
        checks.append({"判据": name, "通过": bool(ok), "证据": detail})

    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                             locale="zh-CN")
        pg = ctx.new_page()
        pg.set_default_timeout(30_000)
        C.open_director(pg, dismiss=True)
        pg.wait_for_timeout(800)

        # 选中第一个轨道
        track_ids = pg.evaluate(
            "()=>[...document.querySelectorAll('[data-director-track-id]')]"
            ".map(e=>e.getAttribute('data-director-track-id'))")
        out["轨道列表"] = track_ids
        if track_ids:
            pg.evaluate(SELECT_TRACK, track_ids[0])
            pg.wait_for_timeout(600)

        st0 = read(pg)
        out["初始"] = st0
        times = st0.get("该轨道关键帧时间") or []
        first_time = times[0] if times else 0.0

        # ── C1：当前帧**有**关键帧时 ⟹ aria-label 逐字「当前帧有关键帧」──
        pg.evaluate(SET_TIME, first_time)
        pg.wait_for_timeout(500)
        s_has = read(pg)
        out["当前帧有"] = s_has
        chk("C1: 当前帧有关键帧时 aria-label 逐字＝「当前帧有关键帧」",
            s_has.get("按钮ariaLabel") == "当前帧有关键帧",
            {"got": s_has.get("按钮ariaLabel")})

        # ── C3：aria-pressed 随状态翻转 ──
        chk("C3: 当前帧有关键帧时 aria-pressed＝true",
            s_has.get("按钮ariaPressed") == "true",
            {"got": s_has.get("按钮ariaPressed")})

        # ── C4：点击「有」⟹ 那枚关键帧真的消失 ──
        r = click(pg)
        out["点击_有"] = r
        gone = first_time not in (r["后"].get("该轨道关键帧时间") or [])
        chk("C4: 当前帧有关键帧时点击 ⟹ 该时间点的关键帧**消失**（不是被覆盖）",
            gone,
            {"前": r["前"].get("该轨道关键帧时间"),
             "后": r["后"].get("该轨道关键帧时间")})

        # ── C2：无 ⟹ aria-label 逐字「当前帧无关键帧」──
        s_none = read(pg)
        out["当前帧无"] = s_none
        chk("C2: 当前帧无关键帧时 aria-label 逐字＝「当前帧无关键帧」",
            s_none.get("按钮ariaLabel") == "当前帧无关键帧",
            {"got": s_none.get("按钮ariaLabel")})
        chk("C3b: 当前帧无关键帧时 aria-pressed＝false",
            s_none.get("按钮ariaPressed") == "false",
            {"got": s_none.get("按钮ariaPressed")})

        # ── C5：点击「无」⟹ 真的多出一枚 ──
        r2 = click(pg)
        out["点击_无"] = r2
        before_n = len(r2["前"].get("该轨道关键帧时间") or [])
        after_n = len(r2["后"].get("该轨道关键帧时间") or [])
        chk("C5: 当前帧无关键帧时点击 ⟹ 该时间点**真的多出一枚**关键帧",
            after_n == before_n + 1,
            {"前": before_n, "后": after_n,
             "前时间": r2["前"].get("该轨道关键帧时间"),
             "后时间": r2["后"].get("该轨道关键帧时间")})

        # ── C6：±0.05s 命中窗口（★ 源站逐字）──
        # ★ 把播头放在「有／无」的分界上：★ 距最近关键帧 **0.04s** ⟹ ⟹ ⟹ ⟹ ⇒
        # ★ 源站（0.05）判「**有**」⟹ ⟹ ⟹ ⟹ ⇒ ★ clone 原先（1e-3）会判「无」
        base = (r2["后"].get("该轨道关键帧时间") or [0.0])[0]
        probe_time = base + 0.04
        pg.evaluate(SET_TIME, probe_time)
        pg.wait_for_timeout(500)
        s_win = read(pg)
        out["窗口探针_播头=base+0.04"] = s_win
        chk("C6: 播头距最近关键帧 0.04s（源站窗口 ±0.05s）⟹ ⟹ ⟹ ⟹ ⇒ ★ "
            "按钮必须判为「当前帧**有**关键帧」",
            s_win.get("按钮ariaLabel") == "当前帧有关键帧",
            {"播头": probe_time, "最近关键帧": base,
             "距离": round(probe_time - base, 4),
             "got": s_win.get("按钮ariaLabel")})
        br.close()

    out["核对"] = checks
    out["失败数"] = sum(1 for c in checks if not c["通过"])
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / "keyframe-toggle-869.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for c in checks:
        print("%s %-70s %s" % ("✔" if c["通过"] else "✘", c["判据"][:70],
                               "" if c["通过"] else c["证据"]))
    print("★ %d 条核对，%d 失败" % (len(checks), out["失败数"]))
    print("★ 读数已落盘：%s" % (RAW / "keyframe-toggle-869.json"))
    return 0 if out["失败数"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
