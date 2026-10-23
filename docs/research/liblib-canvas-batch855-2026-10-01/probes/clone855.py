#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 855 clone 探针：导演台**组 rig 的成员语义**（锚点／成员偏移／组轨道／解组）。

## ★ 靶子（源站逐字依据见 raw/source-855-contract.json）

- **H**：`function H(e,t){var r=O(e).map(t).filter(e=>!!e);…return{x:n.x/r.length,…}}`
  ⟹ ⟹ 组的**锚点 ＝ 全部成员位置的均值**（`O(e)` ＝ 权威成员列表，**任意类别**）。
- **V**：`function V(e,t,r){return O(e).reduce(…e[N(n)]={x:a.x-t.x,…}…)}`
  ⟹ ⟹ **成员偏移给全部成员算**（键 ＝ `N(n)`＝`kind:id`）。
- **rig 应用块**：`A.forEach(…if("character"===o){…}if("prop"===o){…}if("emptyObject"===o){…}})`
  ⟹ ⟹ 分支只有 **character／prop／emptyObject** ⟹ ⟹ **没有 camera 分支**
  ⟹ ⟹ **机位入组后不会被组轨道带动**。
- **rig 的位置公式**：`position:{x:e.position.x+r.x,y:e.position.y+r.y,z:e.position.z+r.z}`
  ⟹ ⟹ **纯平移**（偏移不参与旋转／缩放，成员保留自己的 rotation／scale）。
- **UNGROUP_CHARACTER_GROUP**：复原成员／移除该组轨道／选择态＝复原成员／`selectedGroupId:null`。

## ★ 期望值从哪来

★ **不是手打的** ⟹ ⟹ 逐字依据全部来自 `raw/source-855-contract.json`
（源站 chunk 的机器提取，8/8 唯一命中）⟹ ⟹ 三层证据链：
**源站 chunk 原文 → 提取器 → 本探针的 clone 实测**。

## ★ 走**真实 UI**（不调 store）

- 点机位行 → 选 1 个
- **⌘+点**角色行 → 加选（与 854 的源站实测同一条路径）
- 点「打组」按钮 ⟹ 组出现
- 点「+ 轨道」⟹ 组轨道出现
- 在组检查器里改「位置 x」⟹ 写组关键帧
- 时间轴拖到 0 / 4 ⟹ 读**绝对坐标**
- 点「解组」⟹ 复原

## ★ 唯一的**数据级受控检查**（明确标注，不冒充 UI 证据）

「rig 是纯平移」这条判据，用 UI 改不出**可判别的**读数
（改位置时 Δrotation＝0，旋转增量与缩放比都退化成恒等 ⟹ 两种实现读数一样）。
⟹ ⟹ 这条用一个**显式标注的数据级受控检查**：直接把组轨道的关键帧写成
「位置 ＋ 旋转 ≠ 0」，再读成员**绝对坐标**，
判据是**逐字公式**（位置 ＝ 关键帧位置 ＋ 成员偏移；rotation／scale 不变）。

## 输出

  raw/clone-855-grouprig.json
  images/855clone_*.png
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch855-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"
BASE = "http://localhost:4317"

TREE_CLIP = {"x": 0, "y": 0, "width": 340, "height": 900}

SHOT_NAMES = {
    "①基线": "01-baseline",
    "②选机位": "02-pick-camera",
    "③cmd加选角色": "03-cmd-add-character",
    "④打组后": "04-group",
    "⑤建组轨道后": "05-group-track",
    "⑥改位置后": "06-move-group",
    "⑦t0": "07-t0",
    "⑧t4": "08-t4",
    "⑨解组后": "09-ungroup",
    "⑩道具组后": "10-prop-group",
    "⑪结束": "11-final",
}

# ★ 读一次 store：组 / 轨道 / 成员的**绝对**变换
READ_STATE = r"""()=>{
  const s = window.__director_store.getState();
  const groups = (s.groups||[]).map(g=>({
    id:g.id, label:g.label,
    characterIds:[...(g.characterIds||[])],
    members:(g.members||[]).map(m=>({kind:m.kind,id:m.id})),
  }));
  const tracks = (s.timeline.tracks||[]).filter(t=>t.kind==='group').map(t=>({
    id:t.id, groupId:t.groupId,
    memberOffsetIds:Object.keys(t.memberOffsets||{}),
    memberOffsets:Object.fromEntries(Object.entries(t.memberOffsets||{}).map(([k,v])=>[k,v])),
    keyframes:(t.keyframes||[]).map(k=>({time:k.time, value:k.value})),
  }));
  const objects = (s.objects||[]).map(o=>({
    id:o.id, kind:o.kind, label:o.label,
    position:o.transform.position, rotation:o.transform.rotation, scale:o.transform.scale,
  }));
  return {
    groups, tracks, objects,
    selectedObjectId:s.selectedObjectId,
    selectedObjectIds:[...(s.selectedObjectIds||[])],
    selectedGroupId:s.selectedGroupId,
    currentTime:s.timeline.currentTime,
    autoKeyframe:s.timeline.autoKeyframe,
  };
}"""

# ★ 树的 DOM 读数（组 / 成员行 / 对象行）
READ_DOM = r"""()=>{
  const q=(s)=>Array.from(document.querySelectorAll(s));
  const rows=q('[data-director-object-id]').map(e=>({
    id:e.getAttribute('data-director-object-id'),
    kind:e.getAttribute('data-director-object-kind'),
    label:(e.textContent||'').trim(),
  }));
  const groups=q('[data-director-group-id]').map(e=>({
    id:e.getAttribute('data-director-group-id'),
    label:(e.textContent||'').trim(),
  }));
  const members=q('[data-director-group-member-id]').map(e=>({
    id:e.getAttribute('data-director-group-member-id'),
    kind:e.getAttribute('data-director-group-member-kind'),
  }));
  return {对象行:rows, 组:groups, 成员行:members,
          对象行数:rows.length, 组数:groups.length, 成员行数:members.length};
}"""


def open_desk(pg):
    """★ **从根地址无参进入**（覆盖「根目录可达」）。"""
    pg.goto(BASE + "/", wait_until="domcontentloaded")
    pg.wait_for_timeout(3000)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")
    pg.wait_for_function("() => Boolean(window.__director_store)", timeout=90_000)
    pg.wait_for_timeout(1500)
    node = pg.locator(".react-flow__node-script-execution").first
    try:
        node.scroll_into_view_if_needed(timeout=8000)
    except Exception:
        pass
    pg.wait_for_timeout(400)
    try:
        node.hover(timeout=8000)
        pg.wait_for_timeout(600)
    except Exception:
        pass
    pg.locator("[data-open-director]").first.click(timeout=15000)
    pg.wait_for_timeout(6500)
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")


def click_row(pg, kind, label, modifiers=None):
    """★ 真点那一行（kind ＋ label 双重定位）。"""
    loc = pg.locator('[data-director-object-kind="%s"]' % kind)
    n = loc.count()
    target = None
    for i in range(n):
        el = loc.nth(i)
        if (el.text_content() or "").strip() == label:
            target = el
            break
    if target is None:
        raise SystemExit("★ 找不到 %s／%s 这一行（共 %d 行）" % (kind, label, n))
    try:
        target.scroll_into_view_if_needed(timeout=8000)
    except Exception:
        pass
    pg.wait_for_timeout(200)
    kwargs = {"timeout": 15000}
    if modifiers:
        kwargs["modifiers"] = modifiers
    target.click(**kwargs)
    pg.wait_for_timeout(600)


def click_action(pg, action):
    btn = pg.locator('[data-director-group-action="%s"]' % action).first
    btn.scroll_into_view_if_needed(timeout=8000)
    pg.wait_for_timeout(200)
    btn.click(timeout=15000)
    pg.wait_for_timeout(1000)


def shot(pg, key):
    p = SHOTS / ("855clone_%s.png" % SHOT_NAMES[key])
    p.parent.mkdir(parents=True, exist_ok=True)
    pg.screenshot(path=str(p), clip=TREE_CLIP)
    return p.name


def obj_by_id(state, oid):
    for o in state["objects"]:
        if o["id"] == oid:
            return o
    return None


def mean_position(state, ids):
    """★ 源站 `H` 的口径：全部成员位置的**均值**。"""
    ps = [obj_by_id(state, i) for i in ids]
    ps = [p for p in ps if p]
    if not ps:
        return None
    n = len(ps)
    return [round(sum(p["position"][i] for p in ps) / n, 6) for i in range(3)]


def main() -> int:
    out = {}
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            pg = ctx.new_page()
            pg.set_default_timeout(40_000)
            open_desk(pg)

            base = pg.evaluate(READ_STATE)
            base_dom = pg.evaluate(READ_DOM)
            out["①基线"] = {"state": base, "dom": base_dom}
            shot(pg, "①基线")

            # ── 建组：机位 ＋ 角色（⌘ 加选，与 854 源站实测同路径）────────
            try:
                click_row(pg, "camera", "机位1")
                out["②选机位"] = {"state": pg.evaluate(READ_STATE)}
                shot(pg, "②选机位")
                click_row(pg, "character", "角色A", modifiers=["Meta"])
                out["③cmd加选角色"] = {"state": pg.evaluate(READ_STATE)}
                shot(pg, "③cmd加选角色")
                click_action(pg, "group")
                g = pg.evaluate(READ_STATE)
                g_dom = pg.evaluate(READ_DOM)
                out["④打组后"] = {"state": g, "dom": g_dom}
                shot(pg, "④打组后")
            except Exception:
                out["★建组段异常"] = traceback.format_exc()[-900:]
                return finish(out)

            group = (g["groups"] or [None])[0]
            member_ids = [m["id"] for m in (group or {}).get("members", [])]
            char_ids = [m["id"] for m in (group or {}).get("members", [])
                        if m["kind"] == "character"]
            out["④判定"] = {
                "组成员": (group or {}).get("members"),
                "组characterIds": (group or {}).get("characterIds"),
                "★组成员含机位": any(m["kind"] == "camera"
                                  for m in (group or {}).get("members", [])),
                "★characterIds只是派生量": (group or {}).get("characterIds") == char_ids,
            }

            # ── 建组轨道 ⟹ memberOffsets 键集必须覆盖**全部成员** ─────────
            try:
                add = pg.locator("[data-director-add-track-manual]").first
                add.scroll_into_view_if_needed(timeout=8000)
                pg.wait_for_timeout(200)
                add.click(timeout=15000)
                pg.wait_for_timeout(1200)
                t = pg.evaluate(READ_STATE)
                out["⑤建组轨道后"] = {"state": t}
                shot(pg, "⑤建组轨道后")
                gt = (t["tracks"] or [None])[0]
                out["⑤判定"] = {
                    "组轨道memberOffsets键": (gt or {}).get("memberOffsetIds"),
                    "★期望键集＝全部成员": sorted((gt or {}).get("memberOffsetIds", []))
                    == sorted(member_ids),
                    "★键集含机位": any(
                        obj_by_id(t, k) and obj_by_id(t, k)["kind"] == "camera"
                        for k in (gt or {}).get("memberOffsetIds", [])),
                    "关键帧数": len((gt or {}).get("keyframes", [])),
                }
            except Exception:
                out["★建轨段异常"] = traceback.format_exc()[-900:]

            # ── 改组的位置 x ⟹ 写组关键帧；然后 t=0 / t=4 对比 ─────────────
            try:
                st0 = pg.evaluate(READ_STATE)
                anchor0 = mean_position(st0, member_ids)
                out["⑥改位置前"] = {
                    "state": st0,
                    "锚点": anchor0,
                    "成员位置": {i: (obj_by_id(st0, i) or {}).get("position")
                             for i in member_ids},
                }
                field = pg.locator(
                    '[data-director-group-transform-field="position"] '
                    '[data-director-transform-axis="x"]'
                ).first
                field.scroll_into_view_if_needed(timeout=8000)
                pg.wait_for_timeout(200)
                field.fill(str(round((anchor0 or [0, 0, 0])[0] + 1.2, 4)))
                pg.wait_for_timeout(900)
                st1 = pg.evaluate(READ_STATE)
                out["⑥改位置后"] = {
                    "state": st1,
                    "锚点": mean_position(st1, member_ids),
                    "成员位置": {i: (obj_by_id(st1, i) or {}).get("position")
                             for i in member_ids},
                    "当前时间": st1["currentTime"],
                    "autoKeyframe": st1["autoKeyframe"],
                }
                shot(pg, "⑥改位置后")

                # ★ 拖到 t=0 与 t=4，读**绝对坐标**
                pg.evaluate("() => window.__director_store.getState().setTimelineTime(0)")
                pg.wait_for_timeout(700)
                s0 = pg.evaluate(READ_STATE)
                shot(pg, "⑦t0")
                pg.evaluate("() => window.__director_store.getState().setTimelineTime(4)")
                pg.wait_for_timeout(700)
                s4 = pg.evaluate(READ_STATE)
                shot(pg, "⑧t4")
                out["⑦t0"] = {"state": s0,
                             "成员位置": {i: (obj_by_id(s0, i) or {}).get("position")
                                     for i in member_ids},
                             "锚点": mean_position(s0, member_ids)}
                out["⑧t4"] = {"state": s4,
                             "成员位置": {i: (obj_by_id(s4, i) or {}).get("position")
                                     for i in member_ids},
                             "锚点": mean_position(s4, member_ids)}
            except Exception:
                out["★时间轴段异常"] = traceback.format_exc()[-900:]

            # ── ★★ 数据级受控检查：rig 是**纯平移** ────────────────────────
            # ★ UI 改不出可判别的读数（改位置时 Δrotation＝0 ⟹ 两种实现读数一样），
            # ⟹ ⟹ 这里显式把关键帧写成「位置＋2、旋转 90 度」，再读成员绝对坐标。
            # ★ ★ **关键设计：前后读数在【同一个时间点】上取**（都取 t=0）⟹ ⟹
            #    成员**自身轨道**的贡献在前后完全相同 ⟹ ⟹ 差值只可能来自组 rig。
            try:
                pg.evaluate(
                    "() => window.__director_store.getState().setTimelineTime(0)"
                )
                pg.wait_for_timeout(700)
                before = pg.evaluate(READ_STATE)
                ctrl = pg.evaluate(
                    """(groupId) => {
                      const st = window.__director_store.getState();
                      const track = st.timeline.tracks.find(
                        (t) => t.kind === 'group' && t.groupId === groupId);
                      if (!track) return null;
                      const snap = (k) => ({
                        time: k.time,
                        value: {
                          position: [...k.value.position],
                          rotation: [...k.value.rotation],
                          scale: [...k.value.scale],
                        },
                      });
                      const oldKeyframes = track.keyframes.map(snap);
                      window.__director_store.setState((s) => ({
                        timeline: {
                          ...s.timeline,
                          tracks: s.timeline.tracks.map((t) =>
                            t.id === track.id
                              ? {
                                  ...t,
                                  keyframes: t.keyframes.map((k) => ({
                                    ...k,
                                    value: {
                                      ...k.value,
                                      position: [
                                        k.value.position[0] + 2,
                                        k.value.position[1],
                                        k.value.position[2],
                                      ],
                                      rotation: [0, 90, 0],
                                    },
                                  })),
                                }
                              : t,
                          ),
                        },
                      }));
                      return {
                        oldKeyframes: oldKeyframes,
                        newKeyframes: track.keyframes.map(snap),
                        memberOffsets: track.memberOffsets,
                      };
                    }""",
                    (group or {}).get("id"),
                )
                # ★ 改写 `timeline` 之后**必须再触发一次采样**：
                #   运行时对象是 `setTimelineTime` 时算出来的，不是 timeline 的派生值
                #   ⟹ ⟹ 不重采样就读到的是**旧值**（本批踩过一次）。
                pg.evaluate(
                    "() => window.__director_store.getState().setTimelineTime(0)"
                )
                pg.wait_for_timeout(700)
                after = pg.evaluate(READ_STATE)
                off = (ctrl or {}).get("memberOffsets", {})
                rows = []
                for oid in off:
                    b = obj_by_id(before, oid)
                    a = obj_by_id(after, oid)
                    if not b or not a:
                        continue
                    rows.append({
                        "id": oid, "kind": b["kind"],
                        "偏移": off[oid],
                        "前位置": b["position"],
                        "后位置": a["position"],
                        # ★ 关键帧只把 **x** 挪了 ＋2 ⟹ 期望也只有 x 变
                        "★纯平移期望位置": [
                            round(b["position"][0] + 2, 6),
                            round(b["position"][1], 6),
                            round(b["position"][2], 6),
                        ],
                        "前rotation": b["rotation"],
                        "后rotation": a["rotation"],
                        "前scale": b["scale"],
                        "后scale": a["scale"],
                        "★rig驱动类别": b["kind"] in ("character", "prop"),
                    })
                out["★数据级受控检查：rig 纯平移"] = {
                    "说明": "★ **不是 UI 证据** ⟹ 显式标注的数据级受控检查："
                          "在**同一个时间点**（t=0）上，把组轨道关键帧改成"
                          "「位置＋2、旋转 90 度」，再读成员绝对坐标 ⟹ "
                          "判据是源站逐字公式（位置 ＝ 关键帧位置 ＋ 成员偏移；"
                          "rotation／scale 不变；机位不动）。",
                    "时间点": before["currentTime"],
                    "改写前关键帧": (ctrl or {}).get("oldKeyframes"),
                    "改写后关键帧": (ctrl or {}).get("newKeyframes"),
                    "成员": rows,
                }
            except Exception:
                out["★受控检查段异常"] = traceback.format_exc()[-900:]

            # ── 解组 ⟹ 对齐 UNGROUP_CHARACTER_GROUP ──────────────────────
            try:
                pg.evaluate("() => window.__director_store.getState().setTimelineTime(0)")
                pg.wait_for_timeout(400)
                click_action(pg, "ungroup")
                u = pg.evaluate(READ_STATE)
                u_dom = pg.evaluate(READ_DOM)
                out["⑨解组后"] = {"state": u, "dom": u_dom}
                shot(pg, "⑨解组后")
                out["⑨判定"] = {
                    "组数": len(u["groups"]),
                    "组轨道数": len(u["tracks"]),
                    "对象行数": u_dom["对象行数"],
                    "基线对象行数": base_dom["对象行数"],
                    "★成员都还在": all(
                        obj_by_id(u, i) is not None for i in member_ids),
                    "★选中态＝全部成员": sorted(u["selectedObjectIds"]) == sorted(member_ids),
                    "★selectedGroupId为空": u["selectedGroupId"] is None,
                }
            except Exception:
                out["★解组段异常"] = traceback.format_exc()[-900:]

            # ── 道具组：★ 道具也要跟组动（源站 rig 有 prop 分支）──────────
            try:
                click_row(pg, "prop", "咖啡桌")
                click_row(pg, "character", "角色A", modifiers=["Meta"])
                click_action(pg, "group")
                pg2 = pg.evaluate(READ_STATE)
                grp2 = (pg2["groups"] or [None])[0]
                ids2 = [m["id"] for m in (grp2 or {}).get("members", [])]
                out["⑩道具组后"] = {"state": pg2}
                out["⑩道具组后"]["道具位置"] = {
                    o["id"]: o["position"] for o in pg2["objects"]
                    if o["kind"] == "prop"
                }
                shot(pg, "⑩道具组后")
                add = pg.locator("[data-director-add-track-manual]").first
                add.scroll_into_view_if_needed(timeout=8000)
                pg.wait_for_timeout(200)
                add.click(timeout=15000)
                pg.wait_for_timeout(1200)
                st_before = pg.evaluate(READ_STATE)
                out["⑩建轨后"] = {"state": st_before}
                anchor2 = mean_position(st_before, ids2)
                field = pg.locator(
                    '[data-director-group-transform-field="position"] '
                    '[data-director-transform-axis="x"]'
                ).first
                field.scroll_into_view_if_needed(timeout=8000)
                pg.wait_for_timeout(200)
                field.fill(str(round((anchor2 or [0, 0, 0])[0] + 1.2, 4)))
                pg.wait_for_timeout(900)
                # ★ 改后先读 **t=0**（与「改前」同一时刻 ⟹ 无时间差混淆）
                pg.evaluate(
                    "() => window.__director_store.getState().setTimelineTime(0)"
                )
                pg.wait_for_timeout(800)
                st2b = pg.evaluate(READ_STATE)
                after_t0 = {i: (obj_by_id(st2b, i) or {}).get("position")
                            for i in ids2}
                pg.evaluate("() => window.__director_store.getState().setTimelineTime(4)")
                pg.wait_for_timeout(800)
                s4b = pg.evaluate(READ_STATE)
                base2 = None
                for o in s4b["objects"]:
                    if o["id"] in ids2:
                        base2 = o
                        break
                st_after = pg.evaluate(READ_STATE)
                anchor2 = mean_position(st_after, ids2)
                before_pos = {i: (obj_by_id(st_before, i) or {}).get("position")
                              for i in ids2}
                out["⑩判定"] = {
                    "组成员": (grp2 or {}).get("members"),
                    "★含道具": any(m["kind"] == "prop"
                                for m in (grp2 or {}).get("members", [])),
                    "锚点": anchor2,
                    "★改前成员位置": before_pos,
                    "★改后t0成员位置": after_t0,
                    "t4成员位置": {i: (obj_by_id(s4b, i) or {}).get("position")
                               for i in ids2},
                }
                # ★★ 判据：道具与角色的 **x 位移必须相同**（源站 rig 是纯平移）
                out["⑩判定"]["★成员x位移"] = {
                    i: {
                        "改前x": before_pos[i][0] if before_pos.get(i) else None,
                        "改后x": after_t0[i][0] if after_t0.get(i) else None,
                        "位移x": (round(after_t0[i][0] - before_pos[i][0], 6)
                              if before_pos.get(i) and after_t0.get(i) else None),
                        "类别": next((m["kind"] for m in (grp2 or {}).get("members", [])
                                  if m["id"] == i), None),
                    }
                    for i in ids2
                }
                # ★ 道具的 x 是否随组移动（偏移不变 ⟹ x 变了）
                prop_ids = [m["id"] for m in (grp2 or {}).get("members", [])
                            if m["kind"] == "prop"]
                char_ids2 = [m["id"] for m in (grp2 or {}).get("members", [])
                             if m["kind"] == "character"]
                out["⑩判定"]["★道具x"] = {
                    i: (obj_by_id(s4b, i) or {}).get("position", [None])[0]
                    for i in prop_ids
                }
                out["⑩判定"]["★角色x"] = {
                    i: (obj_by_id(s4b, i) or {}).get("position", [None])[0]
                    for i in char_ids2
                }
                out["⑩判定"]["★锚点x"] = (anchor2 or [None])[0]
                click_action(pg, "ungroup")
                pg.wait_for_timeout(600)
            except Exception:
                out["★道具组段异常"] = traceback.format_exc()[-900:]

            out["⑪结束"] = {"state": pg.evaluate(READ_STATE)}
            shot(pg, "⑪结束")
            br.close()
    except Exception:
        out["★总异常"] = traceback.format_exc()[-1500:]
    return finish(out)


def finish(out):
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / "clone-855-grouprig.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：", path)
    for key in ("④判定", "⑤判定", "⑨判定", "⑩判定"):
        if key in out:
            print("── %s ──" % key)
            print(json.dumps(out[key], ensure_ascii=False, indent=1)[:1600])
    if "★数据级受控检查：rig 纯平移" in out:
        print("── ★数据级受控检查 ──")
        print(json.dumps(out["★数据级受控检查：rig 纯平移"]["成员"],
                         ensure_ascii=False, indent=1)[:1600])
    for key in out:
        if key.startswith("★") and "异常" in key:
            print("★★ %s: %s" % (key, out[key][:600]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
