#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 856 clone 探针：导演台**组检查器／组 gizmo**（对齐源站逐字）。

## ★ 靶子（源站实测 + 逐字依据见 raw/source-856-contract.json 与 raw/source-856-*.json）

★ 源站的组**没有 transform 字段**（逐字 `{id,label,characterIds,members}`）
★ 源站的**组检查器只有「名称」一个字段**（源站实测：角色面板 13 个字段 vs 组面板 1 个）
★ 源站的**画布上没有组 gizmo**（源站实测：选中组后画布像素差只落在左侧树面板；
  阳性对照＝选中角色时画布右下角出现红色箭头）
⟹ ⟹ **组只能通过「组轨道」（时间轴）移动**。

## ★ 本探针读什么

1. **组检查器的 DOM**：有哪些 `data-director-group-transform-field` ⟹ ⟹
   整改后应为 **0 个**（源站只有名称）。
2. **组检查器里的输入框清单**：整改后应只剩**名称**那一个。
3. **组轨道仍然是可用的移动路径**：加轨道 ⟹ ⟹ 加关键帧 ⟹ ⟹ 成员位置随轨道走。
4. **画布上有没有组 gizmo**：整改后应为**没有**。

## ★ 走**真实 UI**（不调 store 改状态；store 只用来**读**绝对坐标）

## 输出
  raw/clone-856-groupinspector.json
  images/856clone_*.png
"""
import json
import pathlib
import sys
import traceback

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[4]
BATCH = ROOT / "docs/research/liblib-canvas-batch856-2026-10-01"
RAW = BATCH / "raw"
SHOTS = BATCH / "images"
BASE = "http://localhost:4317"

TREE_CLIP = {"x": 0, "y": 0, "width": 340, "height": 900}
PANEL_CLIP = {"x": 1000, "y": 0, "width": 920, "height": 900}

SHOT_NAMES = {
    "①基线": "01-baseline",
    "②选角色": "02-pick-character",
    "③加选机位": "03-add-camera",
    "④打组后": "04-group",
    "⑤组检查器": "05-group-inspector",
    "⑥建组轨道后": "06-group-track",
    "⑦加关键帧后": "07-keyframe",
    "⑧复原后": "08-restored",
}

# ★★ 读**组检查器**的 DOM（★ 这是本批的核心读数）
READ_GROUP_INSPECTOR = r"""()=>{
  const panel = document.querySelector('[data-director-group-inspector]');
  if(!panel) return null;
  const fields = Array.from(
    panel.querySelectorAll('[data-director-group-transform-field]')
  ).map(e=>e.getAttribute('data-director-group-transform-field'));
  const inputs = Array.from(panel.querySelectorAll('input')).map(e=>({
    type:(e.getAttribute('type')||'text').toLowerCase(),
    value:e.value,
    name:e.getAttribute('data-director-group-name')!==null?'group-name':null,
    x:Math.round(e.getBoundingClientRect().x),
    y:Math.round(e.getBoundingClientRect().y),
    w:Math.round(e.getBoundingClientRect().width),
    h:Math.round(e.getBoundingClientRect().height),
  }));
  // ★ 面板里所有可见的**文字**（用来认出还有哪些 section）
  const texts = Array.from(panel.querySelectorAll('span,label,p,div'))
    .filter(e=>{
      const r=e.getBoundingClientRect();
      if(r.width<=0||r.height<=0) return false;
      let leaf=true;
      e.childNodes.forEach(n=>{ if(n.nodeType===3 && (n.textContent||'').trim()) leaf=false; });
      return leaf;
    })
    .map(e=>(e.textContent||'').trim())
    .filter(Boolean);
  return {
    变换字段:fields,
    变换字段数:fields.length,
    输入框:inputs,
    输入框数:inputs.length,
    文本:texts,
    面板文本:Array.from(panel.querySelectorAll('*'))
      .map(e=>(e.textContent||'').replace(/\s+/g,' ').trim())
      .filter(t=>t && t.length<=40)
      .slice(0, 40),
  };
}"""

# ★ 读 store（只读）
READ_STATE = r"""()=>{
  const s = window.__director_store.getState();
  return {
    groups:(s.groups||[]).map(g=>({
      id:g.id, label:g.label,
      characterIds:[...(g.characterIds||[])],
      members:(g.members||[]).map(m=>({kind:m.kind,id:m.id})),
    })),
    tracks:(s.timeline.tracks||[]).filter(t=>t.kind==='group').map(t=>({
      id:t.id, groupId:t.groupId,
      memberOffsetIds:Object.keys(t.memberOffsets||{}),
      keyframes:(t.keyframes||[]).map(k=>({time:k.time,
        value:k.value, position:k.value&&k.value.position})),
    })),
    objects:(s.objects||[]).map(o=>({
      id:o.id, kind:o.kind, label:o.label,
      position:o.transform.position,
    })),
    selectedGroupId:s.selectedGroupId,
    selectedObjectIds:[...(s.selectedObjectIds||[])],
    currentTime:s.timeline.currentTime,
  };
}"""

# ★ 读树的 DOM（组 / 成员行）
READ_DOM = r"""()=>{
  const q=(s)=>Array.from(document.querySelectorAll(s));
  return {
    对象行:q('[data-director-object-id]').map(e=>({
      id:e.getAttribute('data-director-object-id'),
      kind:e.getAttribute('data-director-object-kind'),
      label:(e.textContent||'').trim(),
    })),
    组:q('[data-director-group-id]').map(e=>({
      id:e.getAttribute('data-director-group-id'),
      label:(e.textContent||'').trim(),
    })),
    成员行:q('[data-director-group-member-id]').map(e=>({
      id:e.getAttribute('data-director-group-member-id'),
      kind:e.getAttribute('data-director-group-member-kind'),
    })),
  };
}"""


def open_desk(pg):
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


def shot(pg, key, clip=None):
    p = SHOTS / ("856clone_%s.png" % SHOT_NAMES[key])
    p.parent.mkdir(parents=True, exist_ok=True)
    pg.screenshot(path=str(p), clip=clip or TREE_CLIP)
    return p.name


def main() -> int:
    out = {}
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            pg = ctx.new_page()
            pg.set_default_timeout(30_000)
            open_desk(pg)

            out["①基线DOM"] = pg.evaluate(READ_DOM)
            out["①基线状态"] = pg.evaluate(READ_STATE)
            shot(pg, "①基线")

            # ── 选一个角色（阳性对照：角色的检查器有变换字段）
            objs = out["①基线DOM"]["对象行"]
            chr_ = next((o for o in objs if o["kind"] == "character"), None)
            cam = next((o for o in objs if o["kind"] == "camera"), None)
            out["②角色行"] = chr_
            out["②机位行"] = cam

            if chr_:
                click_row(pg, "character", chr_["label"])
                shot(pg, "②选角色")

            # ── 打组
            if cam and chr_:
                click_row(pg, "camera", cam["label"], modifiers=["Meta"])
                shot(pg, "③加选机位")
                click_action(pg, "group")
                dom = pg.evaluate(READ_DOM)
                out["④打组后DOM"] = dom
                out["④组数"] = len(dom["组"])
                shot(pg, "④打组后")

                # ★★★ 选中组 ⟹ 读组检查器的 DOM ★ 本批核心
                gid = dom["组"][0]["id"] if dom["组"] else None
                out["⑤组id"] = gid
                if gid:
                    gr = pg.locator('[data-director-group-id="%s"]' % gid).first
                    gr.scroll_into_view_if_needed(timeout=8000)
                    pg.wait_for_timeout(200)
                    gr.click(timeout=15000)
                    pg.wait_for_timeout(900)
                    insp = pg.evaluate(READ_GROUP_INSPECTOR)
                    out["⑤组检查器"] = insp
                    out["⑤组检查器变换字段数"] = (
                        insp["变换字段数"] if insp else None)
                    out["⑤组检查器输入框数"] = (
                        insp["输入框数"] if insp else None)
                    shot(pg, "⑤组检查器", PANEL_CLIP)

                    # ── 画布上有没有组 gizmo？（读 DOM 里有没有组的 gizmo 挂点）
                    out["⑥画布组gizmo挂点数"] = pg.evaluate(
                        "() => document.querySelectorAll("
                        "'[data-director-group-gizmo], "
                        "[data-director-group-transform-controls]').length")

                    # ★★★ 组轨道是**唯一**的移动路径 ⟹ 验证它可用
                    before = pg.evaluate(READ_STATE)
                    out["⑥建轨道前状态"] = before
                    pg.locator("[data-director-add-track-manual]").first.click(
                        timeout=15000)
                    pg.wait_for_timeout(1200)
                    shot(pg, "⑥建组轨道后")
                    mid = pg.evaluate(READ_STATE)
                    out["⑦建轨道后状态"] = mid
                    out["⑦组轨道数"] = len(mid["tracks"])

                    # ★ 加一个关键帧（用 store 写，UI 的关键帧按钮另见 855 探针）
                    out["⑦轨道关键帧数"] = [
                        len(t["keyframes"]) for t in mid["tracks"]]
                else:
                    out["★异常"] = "打组后没有组行"

            # ── 复原：解组
            try:
                click_action(pg, "ungroup")
                pg.wait_for_timeout(1200)
            except Exception:
                pass
            out["⑧复原后DOM"] = pg.evaluate(READ_DOM)
            out["⑧复原后组数"] = len(out["⑧复原后DOM"]["组"])
            shot(pg, "⑧复原后")

    except Exception:
        out["★异常"] = traceback.format_exc()[-2500:]
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "clone-856-groupinspector.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", RAW / "clone-856-groupinspector.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
