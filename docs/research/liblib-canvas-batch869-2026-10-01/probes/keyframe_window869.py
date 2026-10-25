#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 869 探针：★ 「当前帧关键帧」命中窗口必须等于**源站逐字**的 ±0.05s。

## ★ 源站依据（★ 逐字 ⟹ ⟹ 不用记忆 ⟹ ⟹ 判据不许手打）

★ 源站 chunk `0fmehki05gkzw.js.js` 的 `cZ` 函数（★ 逐字全文见
★ `raw/source-869-cz-toggle.txt`）：

```js
f = markers.find(e => .05 >= Math.abs(e.time - h)) ?? null   // ← 当前帧命中 ±0.05s
m = … if (n && n.time < t - .05) return n …                    // ← 上一关键帧取点
x = markers.find(e => e.time > h + .05) ?? null                // ← 下一关键帧取点
b = p(f ? "canvas:directorTimelineCurrentKeyframeVisible"
        : "canvas:directorTimelineCurrentKeyframeHidden")
aria-pressed: !!f
onClick: o({ …, action: f ? "remove" : "add" })
```

★ 源站 i18n 字典（★ 逐字见 `raw/source-869-i18n-dictionary.txt`）：

```
"directorTimelineCurrentKeyframeVisible":"当前帧有关键帧"
"directorTimelineCurrentKeyframeHidden":"当前帧无关键帧"
```

★ ⇒ **判据**（★ 全部**只从实测读数**来）：

| # | 判据 |
| --- | --- |
| W1 | ★ 播头落在关键帧 **+0.04s**（★ 源站 ±0.05s 窗口**内**）⟹ ⟹ ⟹ ⟹ ⇒ ★ 轨道行中键的 `aria-label` 逐字＝「当前帧有关键帧」 |
| W2 | ★ 同处 `aria-pressed`＝`true` |
| W3 | ★ 同处「上一关键帧」**disabled**（★ 源站 `T < T+0.04-0.05` 不成立） |
| W4 | ★ 点中键 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 那枚关键帧**真的消失**（★ 数量 −1 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 不是覆盖、不是新增） |
| W5 | ★ 播头落在关键帧 **+0.2s**（★ 窗口**外**）⟹ ⟹ ⟹ ⟹ ⇒ ★ `aria-label` 逐字＝「当前帧无关键帧」、`aria-pressed`＝`false` |
| W6 | ★ 点中键 ⟹ ⟹ ⟹ ⟹ ⇒ ★ **真的多出一枚**（★ 数量 +1） |
| W7 | ★ 检查器那枚开关（★ 源站每个数值框右端一枚）⟹ ⟹ ⟹ ⟹ ⇒ ★ 在 +0.04s 处逐字＝「当前帧有关键帧」、state＝`on` |
| W8 | ★ 检查器开关在 +0.04s 处点击 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 那枚关键帧**真的消失**（★ 数量 −1） |
| W9 | ★ 工具条「添加关键帧」是**取当前值覆盖**（★ 源站逐字规格）⟹ ⟹ ⟹ ⟹ ⇒ ★ 数量**不变**、时间列表**不变**、但那枚的 **value 变成对象当前变换** |

★ ★★ **为什么 W9 是「覆盖」而不是「切换」**：★ 源站 batch 36 的逐字规格
★ （★ `docs/research/liblib-canvas-batch36-2026-08-26/DIRECTOR_TIMELINE.spec.md`）：
★   `◆ 添加关键帧` captures the selected track object's complete current value;
★   same-time add replaces the existing keyframe value;
★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ 详见 `raw/source-869-correction.md`（★ 本批一度改错方向的记录）。

## ★ 手法说明

- ★ 播头**精确**放置：★ 走 store 的 `setTimelineTime` ⟹ ⟹ ⟹ ⟹ ⇒ ★ 原因：★
  源站那个窗口是 **±0.05s** ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ 点标尺根本没法命中 40ms 这种
  精度 ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ 而**被测动作本身仍然是真实按钮点击**。
- ★ 对象变换的挪动走 `setState`（★ 绕开 `updateObjectTransform`）⟹ ⟹ ⟹ ⟹ ⇒ ★
  原因：★ 后者在「自动关键帧」开着时会**顺手记一枚关键帧** ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹
  那样 W9 的「数量不变」就会被**污染**成假失败。

## 输出
  raw/keyframe-window-869.json
"""
from __future__ import annotations

import json
import os
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

TOOLBAR_ADD = "[data-director-add-keyframe]"

# ★ ★★ 读数：★ 一把把「轨道行三键 ＋ 检查器开关 ＋ 关键帧列表 ＋ 对象变换」读全
READ = """()=>{
  const st = window.__director_store && window.__director_store.getState();
  if(!st) return {错:'store 没暴露'};
  const tl = st.timeline;
  const track = tl.tracks.find(t=>t.id===tl.selectedTrackId) || null;
  const kfs = track ? track.keyframes : [];
  const row = track
    ? document.querySelector('[data-director-track-row="'+track.id+'"]')
    : null;
  const q = (label) => row ? row.querySelector('button[aria-label="'+label+'"]') : null;
  const mid = row
    ? (row.querySelector('button[aria-label="当前帧有关键帧"]')
       || row.querySelector('button[aria-label="当前帧无关键帧"]'))
    : null;
  const prev = q('上一关键帧');
  const next = q('下一关键帧');
  const insp = document.querySelector('[data-director-keyframe-toggle]');
  const obj = st.objects.find(o=>o.id===st.selectedObjectId) || null;
  return {
    选中轨道id: tl.selectedTrackId,
    轨道对象id: track ? track.objectId : null,
    选中对象id: st.selectedObjectId,
    轨道种类: track ? track.kind : null,
    当前时间: tl.currentTime,
    关键帧时间: kfs.map(k=>k.time),
    关键帧数: kfs.length,
    关键帧值: kfs.map(k=>k.value===undefined ? null : k.value),
    中键aria: mid ? mid.getAttribute('aria-label') : null,
    中键pressed: mid ? mid.getAttribute('aria-pressed') : null,
    上一键disabled: prev ? prev.disabled : null,
    下一键disabled: next ? next.disabled : null,
    检查器开关aria: insp ? insp.getAttribute('aria-label') : null,
    检查器开关state: insp ? insp.getAttribute('data-director-keyframe-toggle-state') : null,
    检查器开关testId: insp ? insp.getAttribute('data-director-keyframe-toggle') : null,
    对象变换: obj ? obj.transform : null,
  };
}"""

SET_TIME = """(t)=>{
  const st = window.__director_store.getState();
  st.setTimelineTime(t);
  return st.timeline.currentTime;
}"""

SELECT_TRACK = """(id)=>{
  const el = document.querySelector('[data-director-track-id="'+id+'"]');
  if(!el) return false;
  el.click();
  return true;
}"""

SELECT_OBJECT = """(id)=>{
  const st = window.__director_store.getState();
  st.selectObject(id);
  return st.selectedObjectId;
}"""

# ★ 挪对象变换（★ 绕开命令层 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 免得自动关键帧顺手记一枚）
NUDGE_OBJECT = """(id)=>{
  const store = window.__director_store;
  const st = store.getState();
  const bump = (o)=>{
    if(o.id!==id) return o;
    const t = o.transform || {position:[0,0,0],rotation:[0,0,0],scale:[1,1,1]};
    const pos = (t.position || [0,0,0]).slice();
    pos[0] = Number((pos[0] + 1.25).toFixed(6));
    return {...o, transform: {...t, position: pos}};
  };
  store.setState({
    objects: st.objects.map(bump),
    authoredObjects: st.authoredObjects.map(bump),
  });
  const after = store.getState().objects.find(o=>o.id===id);
  return after ? after.transform : null;
}"""

# ★ ★★ 固定夹具：★ 把选中轨道的关键帧**重置成一份已知集合**（★ 默认只留一枚）。
# ★ ★★ 为什么必须有它：★ Batch 869 第一版的探针**没有**它 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 于是
# ★   「点中键」那一步会**在当前帧新增一枚** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 而后面的「检查器开关」
# ★   ⟹ ⟹ ⟹ ⟹ ⇒ ★ 读到的是**那枚新增的** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 于是检查器那两条判据
# ★   ⟹ ⟹ ⟹ ⟹ ⇒ ★ **与窗口无关**（★ 变异成 1e-3 之后它们照样绿）⟹ ⟹ ⟹ ⟹ ⇒ ★
# ★   ⟹ ⟹ ⟹ ⟹ **证不出**检查器那枚开关到底用哪个窗口。
# ★ ⇒ 纪律：★ **判据之间不许互相污染** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 每一步都从**已知状态**出发。
SET_KEYFRAMES = """(times)=>{
  const store = window.__director_store;
  const st = store.getState();
  const trackId = st.timeline.selectedTrackId;
  const track = st.timeline.tracks.find(t=>t.id===trackId);
  if(!track) return null;
  // ★ 原型值（★ ★ 随轨道种类而变）⟹ ⟹ ⟹ ⇒ ★ 必须在**关键帧还在的时候**
  //   ⟹ ⟹ ⟹ ⇒ ★ 捕获一次、之后一直复用（★ 否则清空后就没有原型了 ⟹ ⟹ ⟹ ⇒ ★
  //   ⟹ ⟹ ⟹ ⇒ ★ 而 value 变成 null ⟹ ⟹ ⟹ ⇒ ★ 采样时 cloneTransform(null) 抛错）。
  if(window.__probe_kf_proto === undefined){
    const proto = track.keyframes[0];
    if(proto){
      window.__probe_kf_proto = JSON.parse(JSON.stringify(proto.value));
    } else {
      const obj = st.objects.find(o=>o.id===track.objectId);
      const tr = (obj && obj.transform) || {position:[0,0,0],rotation:[0,0,0],scale:[1,1,1]};
      window.__probe_kf_proto = track.kind === 'camera'
        ? {transform:{position:[...tr.position],rotation:[...tr.rotation],scale:[...tr.scale]},
           target: (obj && obj.camera && obj.camera.target) ? [...obj.camera.target] : [0,0,0],
           fov: (obj && obj.camera && obj.camera.fov) || 50}
        : {position:[...(tr.position||[0,0,0])],
           rotation:[...(tr.rotation||[0,0,0])],
           scale:[...(tr.scale||[1,1,1])]};
    }
  }
  const protoValue = window.__probe_kf_proto;
  const keyframes = times.map((tm,i)=>({
    id: trackId + '-probe-kf-' + i,
    time: tm,
    value: JSON.parse(JSON.stringify(protoValue)),
  }));
  store.setState({
    timeline: {...st.timeline, tracks: st.timeline.tracks.map(t=>
      t.id===trackId ? {...t, keyframes} : t), selectedKeyframeId: null},
  });
  const after = store.getState().timeline.tracks.find(t=>t.id===trackId);
  return after ? after.keyframes.map(k=>k.time) : null;
}"""


def _tr_eq(a, b) -> bool:
    """★ 三个三元组逐分量数值比较（★ 免得 JSON 字符串键序骗人）。"""
    if not isinstance(a, dict) or not isinstance(b, dict):
        return False
    for k in ("position", "rotation", "scale"):
        va, vb = a.get(k), b.get(k)
        if not isinstance(va, list) or not isinstance(vb, list):
            return False
        if len(va) != len(vb):
            return False
        for x, y in zip(va, vb):
            try:
                if abs(float(x) - float(y)) > 1e-6:
                    return False
            except (TypeError, ValueError):
                return False
    return True


def _value_transform(value):
    """★ 取关键帧 value 里携带的**变换**（★ camera 轨有外层包装）。"""
    if not isinstance(value, dict):
        return None
    if isinstance(value.get("transform"), dict):
        return value["transform"]
    return value


def read(pg) -> dict:
    return pg.evaluate(READ)


def click_mid(pg) -> dict:
    """★ 点**轨道行中键**（★ 源站 `cZ` 的中间那枚）⟹ ⟹ ⟹ ⟹ ⇒ ★ 真点击。"""
    before = read(pg)
    row = before.get("选中轨道id")
    sel = ('[data-director-track-row="%s"] button[aria-label="当前帧有关键帧"],'
           '[data-director-track-row="%s"] button[aria-label="当前帧无关键帧"]'
           % (row, row))
    pg.locator(sel).first.click(force=True, timeout=8000)
    pg.wait_for_timeout(700)
    return {"前": before, "后": read(pg)}


def main() -> int:
    out: dict = {
        "说明": "★ 全部判据只从实测读数来",
        "源站依据": {
            "命中窗口": "±0.05s（★ 源站 chunk `cZ` 逐字）",
            "aria 文案": "当前帧有关键帧 ／ 当前帧无关键帧（★ 源站 i18n 字典逐字）",
            "添加关键帧语义": "取当前值覆盖（★ 源站 batch 36 逐字规格）",
        },
    }
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
        pg.wait_for_timeout(900)

        track_ids = pg.evaluate(
            "()=>[...document.querySelectorAll('[data-director-track-id]')]"
            ".map(e=>e.getAttribute('data-director-track-id'))")
        out["轨道列表"] = track_ids
        if not track_ids:
            raise RuntimeError("导演台没有轨道行")
        pg.evaluate(SELECT_TRACK, track_ids[0])
        pg.wait_for_timeout(700)

        s0 = read(pg)
        out["初始"] = s0
        times = s0.get("关键帧时间") or []
        if not times:
            raise RuntimeError("选中的轨道没有关键帧 ⟹ 没法做 ±0.05s 的判定")
        t0 = float(times[0])
        obj_id = s0.get("轨道对象id")
        # ★ 选中对象 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 检查器才会渲染它的数值框与那枚开关
        if obj_id:
            pg.evaluate(SELECT_OBJECT, obj_id)
            pg.wait_for_timeout(600)

        # ── W0a：★ 探针自身的可读性自检 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 后面几项不是空判 ────
        chk("W0a: 轨道行中键读得到 aria-label（★ 探针可读性自检）",
            isinstance(s0.get("中键aria"), str) and s0.get("中键aria") != "",
            {"got": s0.get("中键aria"), "轨道种类": s0.get("轨道种类")})

        def fixture() -> list:
            """★ ★★ 每一步都从**同一份已知状态**出发（★ 判据之间不许互相污染）。"""
            got = pg.evaluate(SET_KEYFRAMES, [t0])
            pg.wait_for_timeout(500)
            return got

        # ── 阶段 A（★ **只读**）：★ 窗口内 +0.04s ─────────────────────────
        out["夹具_关键帧时间"] = fixture()
        pg.evaluate(SET_TIME, t0 + 0.04)
        pg.wait_for_timeout(600)
        s_in = read(pg)
        out["窗口内_+0.04s"] = s_in
        chk("W1: 播头落在关键帧 +0.04s（源站 ±0.05s 窗口内）⟹ 轨道行中键 aria-label 逐字＝「当前帧有关键帧」",
            s_in.get("中键aria") == "当前帧有关键帧",
            {"got": s_in.get("中键aria"), "当前时间": s_in.get("当前时间"),
             "关键帧时间": s_in.get("关键帧时间")})
        chk("W2: 同处 aria-pressed＝true",
            s_in.get("中键pressed") == "true",
            {"got": s_in.get("中键pressed")})
        chk("W3: 同处「上一关键帧」disabled（源站逐字：T < 播头-0.05 不成立）",
            s_in.get("上一键disabled") is True,
            {"got": s_in.get("上一键disabled"),
             "源站算式": "T(%s) < %s-0.05 ⟹ %s" % (t0, t0 + 0.04, t0 < t0 + 0.04 - 0.05),
             "全部关键帧时间": s_in.get("关键帧时间")})

        # ── W7：★ 检查器那枚开关（★ **同一次只读** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 与 W1/W2/W3
        #   ⟹ ⟹ ⟹ ⟹ 读的是**同一个瞬间** ⟹ ⟹ ⟹ ⟹ ⇒ ★ 不受任何点击影响）
        out["检查器_窗口内"] = s_in
        chk("W7: 检查器开关在 +0.04s 处逐字＝「当前帧有关键帧」且 state＝on",
            s_in.get("检查器开关aria") == "当前帧有关键帧"
            and s_in.get("检查器开关state") == "on",
            {"got": s_in.get("检查器开关aria"),
             "state": s_in.get("检查器开关state"),
             "testId": s_in.get("检查器开关testId"),
             "关键帧时间": s_in.get("关键帧时间")})

        # ── 阶段 B（★ **只读**）：★ 窗口外 +0.2s ─────────────────────────
        pg.evaluate(SET_TIME, t0 + 0.2)
        pg.wait_for_timeout(600)
        s_out = read(pg)
        out["窗口外_+0.2s"] = s_out
        chk("W5: 播头落在关键帧 +0.2s（源站窗口外）⟹ aria-label 逐字＝「当前帧无关键帧」",
            s_out.get("中键aria") == "当前帧无关键帧",
            {"got": s_out.get("中键aria"), "当前时间": s_out.get("当前时间"),
             "关键帧时间": s_out.get("关键帧时间")})
        chk("W5b: 同处 aria-pressed＝false",
            s_out.get("中键pressed") == "false",
            {"got": s_out.get("中键pressed")})

        # ── 阶段 C（★ **点击**）：★ W4 ─────────────────────────────────────
        out["夹具_关键帧时间_W4前"] = fixture()
        pg.evaluate(SET_TIME, t0 + 0.04)
        pg.wait_for_timeout(400)
        r = click_mid(pg)
        out["点击_窗口内"] = r
        after_times = r["后"].get("关键帧时间") or []
        chk("W4: 窗口内点中键 ⟹ 那枚关键帧真的消失（数量 −1，不是覆盖、不是新增）",
            (r["后"].get("关键帧数") == (r["前"].get("关键帧数") or 0) - 1)
            and all(abs(x - t0) > 1e-9 for x in after_times),
            {"前": r["前"].get("关键帧时间"), "后": after_times,
             "前数": r["前"].get("关键帧数"), "后数": r["后"].get("关键帧数")})

        # ── W4b：★ 播头**正好**落在关键帧时刻 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 中键是「有」
        #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ 点它 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 源站逐字 `action: f?"remove":"add"`
        #   ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⟹ ⟹ ⟹ ⇒ ★ ⟹ ⇒ **移除**那一枚（★ 不是「再加一枚」）
        out["夹具_关键帧时间_W4b前"] = fixture()
        pg.evaluate(SET_TIME, t0)
        pg.wait_for_timeout(400)
        r_back = click_mid(pg)
        out["点击_关键帧时刻"] = r_back
        back_times = r_back["后"].get("关键帧时间") or []
        chk("W4b: 播头正好落在关键帧时刻 ⟹ 中键＝「当前帧有关键帧」⟹ 点它 ⟹ "
            "那一枚**消失**（源站逐字 action＝remove，★ 不是「再加一枚」）",
            r_back["前"].get("中键aria") == "当前帧有关键帧"
            and (r_back["后"].get("关键帧数") or 0) == (r_back["前"].get("关键帧数") or 0) - 1
            and all(abs(x - t0) > 1e-9 for x in back_times),
            {"前": r_back["前"].get("关键帧时间"), "后": back_times,
             "前中键aria": r_back["前"].get("中键aria"),
             "前数": r_back["前"].get("关键帧数"),
             "后数": r_back["后"].get("关键帧数")})

        # ── W6：★ 窗口外点中键 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 真的多出一枚 ──────────────────
        out["夹具_关键帧时间_W6前"] = fixture()
        pg.evaluate(SET_TIME, t0 + 0.2)
        pg.wait_for_timeout(400)
        r_out = click_mid(pg)
        out["点击_窗口外"] = r_out
        chk("W6: 窗口外点中键 ⟹ 真的多出一枚（数量 +1）",
            (r_out["后"].get("关键帧数") or 0) == (r_out["前"].get("关键帧数") or 0) + 1,
            {"前": r_out["前"].get("关键帧时间"), "后": r_out["后"].get("关键帧时间")})

        # ── W8：★ 点检查器开关 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 那枚真的消失 ──────────────────
        out["夹具_关键帧时间_W8前"] = fixture()
        pg.evaluate(SET_TIME, t0 + 0.04)
        pg.wait_for_timeout(400)
        before8 = read(pg)
        pg.locator("[data-director-keyframe-toggle]").first.click(
            force=True, timeout=8000)
        pg.wait_for_timeout(700)
        after8 = read(pg)
        out["点击_检查器开关"] = {"前": before8, "后": after8}
        chk("W8: 检查器开关在 +0.04s 处点击 ⟹ 那枚关键帧真的消失（数量 −1）",
            (after8.get("关键帧数") or 0) == (before8.get("关键帧数") or 0) - 1,
            {"前": before8.get("关键帧时间"), "后": after8.get("关键帧时间")})

        # ── 阶段 D：★ W9（★ 工具条「添加关键帧」＝取当前值覆盖）───────────
        out["夹具_关键帧时间_W9前"] = fixture()
        pg.evaluate(SET_TIME, t0)
        pg.wait_for_timeout(400)

        # ── W9：★ 工具条「添加关键帧」＝**取当前值覆盖** ──────────────────
        before9 = read(pg)
        obj_id = before9.get("轨道对象id")
        new_transform = pg.evaluate(NUDGE_OBJECT, obj_id)
        pg.wait_for_timeout(500)
        mid9 = read(pg)
        # ★ W0b：★ 挪动**读回**确认 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 否则 W9 是空判
        tr_before = before9.get("对象变换")
        tr_after = mid9.get("对象变换")
        chk("W0b: 挪动对象后读回的 transform 确实变了（★ 否则 W9 是空判）",
            (not _tr_eq(tr_before, tr_after)) and _tr_eq(tr_after, new_transform),
            {"挪动前": tr_before, "挪动后": tr_after, "期望": new_transform})

        pg.locator(TOOLBAR_ADD).first.click(force=True, timeout=8000)
        pg.wait_for_timeout(800)
        after9 = read(pg)
        out["工具条_添加关键帧"] = {
            "前": before9, "挪动后": mid9, "后": after9,
            "对象新变换": new_transform,
        }

        def value_at(state, t):
            for kf_t, kf_v in zip(state.get("关键帧时间") or [],
                                  state.get("关键帧值") or []):
                if abs(kf_t - t) < 1e-9:
                    return kf_v
            return None

        val_before = value_at(before9, t0)
        val_after = value_at(after9, t0)
        obj_now = after9.get("对象变换")
        tr_val_before = _value_transform(val_before)
        tr_val_after = _value_transform(val_after)
        chk("W9: 工具条「添加关键帧」＝取当前值覆盖（源站逐字）：数量不变、时间列表不变，"
            "但那枚的 value 变成对象当前变换",
            (after9.get("关键帧数") == before9.get("关键帧数"))
            and (after9.get("关键帧时间") == before9.get("关键帧时间"))
            and tr_val_after is not None
            and _tr_eq(tr_val_after, obj_now)
            and (not _tr_eq(tr_val_after, tr_val_before)),
            {"数量前": before9.get("关键帧数"), "数量后": after9.get("关键帧数"),
             "时间前": before9.get("关键帧时间"), "时间后": after9.get("关键帧时间"),
             "value前": val_before, "value后": val_after,
             "对象当前变换": obj_now, "对象新变换": new_transform,
             "轨道种类": before9.get("轨道种类")})

        pg.close()
        br.close()

    out["判据"] = checks
    out["失败数"] = sum(1 for c in checks if not c["通过"])
    RAW.mkdir(parents=True, exist_ok=True)
    # ★ ★★ 输出路径可重定向（★ 环境变量 `KEYFRAME_WINDOW_OUT`）⟹ ⟹ ⟹ ⟹ ⇒ ★
    #   ★ 原因：★ 负控要跑**变异后**的探针 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 而**入库证据**不能被
    #   ★ ⟹ ⟹ ⟹ ⟹ 负控覆盖 ⟹ ⟹ ⟹ ⟹ ⇒ ★ 所以负控把输出指到临时文件 ⟹ ⟹ ⟹ ⟹ ⇒ ★
    #   ★ 默认路径才是入库那份。
    out_path = pathlib.Path(
        os.environ.get("KEYFRAME_WINDOW_OUT")
        or (RAW / "keyframe-window-869.json"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("★ %d 条判据，%d 失败" % (len(checks), out["失败数"]))
    for c in checks:
        print("  %s %s" % ("PASS" if c["通过"] else "FAIL", c["判据"]))
        if not c["通过"]:
            print("      证据：%s" % json.dumps(c["证据"], ensure_ascii=False))
    return 1 if out["失败数"] else 0


if __name__ == "__main__":
    sys.exit(main())
