#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 823 探针 —— **纯 UI 可达性审查**：后门造出来的现象，用户真的看得到吗？

## ★ 这批要反省什么

过去 800+ 批的探针，**起点状态几乎全靠 `window.__libtv_store` /
`window.__director_store` 这两个后门造**（`canvasStore.ts:4344`、
`directorStore.ts:8721` —— 那是**我给测试挂的**，源站产品里根本不存在）。
⟹ 那些读数证明的是「**store 这么做**」，**不是**「**用户能走到这里**」。

★ 第一版探针当场自曝三条：
  ① 导演台打开后**默认选中的是角色轨道**，不是相机轨道
     ⟹ ★★ 821/822 全部读数的起点「相机轨道已选中」**是后门给的**；
  ② 因此**预设开关是 disabled** ⟹ 纯 UI 下「追加运镜」**根本打不开**；
  ③ 探针自己两个 bug：`RO()` 读 `S.nodes`（**画布 store 没有这个顶层键**）、
     拿**轨道 id** 去比**对象 id**（匹配失败、根本没点）。

## ★ 本批的硬约束

1. ★ **零 store 写调用**：所有 store 访问**只允许**经 `RO()` / `RO_D()`
   两个只读入口（验收器用正则扫源码自证）。
2. ★ **每个动作都记「入口候选数」**：走不通时必须能区分
   「产品没有这个入口」与「探针没找到」⟹ 所以每一步都报
   **符合语义的控件个数**，并把它作为证据。
3. ★ **每步两读数**：store 读数**变没变** ＋ UI 上有没有可见反馈。
4. ★ **绝对读数**：节点数、关键帧数、坐标、选中 id —— 不靠「提示出现了」。

## ★ 枢纽问题

**用户能不能纯 UI 选中相机轨道？** 答不上来，821/822 的读数就都悬着。
"""
import json
import os
import pathlib
import re
import sys
import time
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

OUT = pathlib.Path(os.environ.get("VB823_OUT") or
                   (HERE.parent / "raw" / "vb823a.json"))

# ★★ 画布 store 的节点在 `canvases[activeCanvasId].nodes` —— **没有** `S.nodes`
RO = """()=>{const S=window.__libtv_store.getState();
  const c=(S.canvases||[]).find(x=>x.id===S.activeCanvasId)||null;
  const nodes=(c&&c.nodes)||[];
  return {画布id:S.activeCanvasId,
          画布数:(S.canvases||[]).length,
          '★ 节点数':nodes.length,
          '★ 节点类型':nodes.map(n=>n.type||n.kind||null),
          '★ 节点位置':nodes.slice(0,8).map(n=>({
            id:n.id,type:n.type||n.kind||null,
            x:n.position?Math.round(n.position.x):null,
            y:n.position?Math.round(n.position.y):null})),
          '★ 选中节点':(S.selectedNodeIds||[]).slice(),
          '★ 边数':((c&&c.edges)||[]).length,
          '★ 历史长度':((c&&c.history&&c.history.past)||[]).length};}"""

RO_D = """()=>{const S=window.__director_store.getState();
  const tl=S.timeline;
  const t=tl.tracks.find(x=>x.kind==='camera')||null;
  const kfs=t?t.keyframes:[];
  const cam=t?S.objects.find(o=>o.id===t.objectId):null;
  const sel=S.selectedObjectId;
  const selObj=S.objects.find(o=>o.id===sel);
  return {选中轨道:tl.selectedTrackId,
          轨道数:tl.tracks.length,
          '★ 轨道清单':tl.tracks.map(x=>({id:x.id,kind:x.kind,
            对象:x.objectId,n:x.keyframes.length})),
          相机轨道id:t?t.id:null,
          '★ 关键帧数':kfs.length,
          '★ 末关键帧毫秒':kfs.length?Math.round(kfs[kfs.length-1].time*1000):null,
          总时长毫秒:Math.round(tl.duration*1000),
          '★ 选中对象':sel||null,
          '★ 选中对象类型':selObj?(selObj.camera?'camera':(selObj.type||'?')):null,
          '★ 相机锁定':cam?!!cam.locked:null,
          '★ 跟随目标':cam&&cam.camera?cam.camera.followTargetId||null:null,
          presetError:(tl.cameraMotionPreset.error||{}).message||null};}"""

# ★ 入口候选普查：把「这个入口存不存在」变成一个**可数**的读数
PROBE = """(sel)=>{
  const visible=(e)=>{const r=e.getBoundingClientRect();
    if(r.width===0&&r.height===0)return false;
    const cs=getComputedStyle(e);
    return cs.visibility!=='hidden'&&cs.visibility!=='collapse'
      && cs.display!=='none'&&Number(cs.opacity||'1')>0;};
  const all=Array.from(document.querySelectorAll(sel));
  const vis=all.filter(visible);
  return {选择器:sel, 全部个数:all.length, 可见个数:vis.length,
          可见文字:vis.slice(0,8).map(e=>(e.textContent||'').trim()
            .replace(/\\s+/g,' ').slice(0,28)),
          可见标签:vis.slice(0,8).map(e=>(e.getAttribute('aria-label')
            ||e.getAttribute('title')||''))};}"""

# ★ 把 DOM 上**所有**带 data- 的可见元素列出来（先看事实，不猜标记名）
DUMP = """()=>{const out=[];
  for(const e of Array.from(document.querySelectorAll('*'))){
    const attrs=Array.from(e.attributes).filter(a=>a.name.startsWith('data-'));
    if(!attrs.length)continue;
    const r=e.getBoundingClientRect();
    if(r.width===0&&r.height===0)continue;
    out.push({tag:e.tagName,
      data:attrs.map(a=>a.name+'='+a.value).join(' ').slice(0,90),
      text:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,26),
      aria:e.getAttribute('aria-label')||'',
      title:e.getAttribute('title')||'',
      rect:{x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)}});}
  return out;}"""


def cand(pg, sel):
    return pg.evaluate(PROBE, sel)


def safe_click(pg, sel):
    """★ 全程容错：找不到就记 'not-found'，**绝不抛异常** ——
    否则一步失败就丢掉整轮读数（第一版就因为 B6a 的 orbit 按钮不存在
    而整轮报废、raw 都没写出来）。"""
    try:
        el = pg.query_selector(sel)
    except Exception as exc:                                    # noqa: BLE001
        return {"结果": "error", "详情": str(exc)[:120]}
    if not el:
        return {"结果": "not-found", "选择器": sel}
    try:
        if el.is_disabled():
            return {"结果": "disabled", "选择器": sel,
                    "aria": el.get_attribute("aria-label"),
                    "title": el.get_attribute("title")}
        el.click()
        return {"结果": "clicked", "选择器": sel}
    except Exception as exc:                                    # noqa: BLE001
        return {"结果": "click-error", "详情": str(exc)[:120]}


def run(b):
    out = {"画布": [], "导演台": [], "操作": {}}
    pg = b.new_page()
    pg.set_default_timeout(25000)
    try:
        pg.goto(A.BASE, wait_until="domcontentloaded")
        pg.wait_for_timeout(3200)

        # ═════════════ 画布 ═════════════
        c0 = pg.evaluate(RO)
        out["画布"].append({
            "步骤": "A0·刚打开画布（**纯 UI 起点**）",
            "读数": c0,
            "★ 添加入口候选": cand(pg, "[data-add-node-entry]"),
            "★ 面板类 data- 元素": [d for d in pg.evaluate(DUMP)
                                    if "add-node" in d["data"]
                                    or "panel" in d["data"]][:12]})

        # A1：找「添加节点」的真实入口 —— 先看事实
        dump0 = pg.evaluate(DUMP)
        out["画布"][-1]["★ 画布上所有可见 data- 元素（前 40）"] = dump0[:40]

        # A2：纯 UI 选中一个节点（点节点中心）
        target = pg.evaluate("""()=>{
          const els=Array.from(document.querySelectorAll(
            '.react-flow__node'));
          if(!els.length)return null;
          const e=els[els.length-1];
          const r=e.getBoundingClientRect();
          return {x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2),
                  id:e.getAttribute('data-id'),
                  w:Math.round(r.width),h:Math.round(r.height)};}""")
        out["操作"]["A2 节点矩形"] = target
        if target:
            pg.mouse.click(target["x"], target["y"])
            pg.wait_for_timeout(700)
        c2 = pg.evaluate(RO)
        out["画布"].append({
            "步骤": "A2·点节点中心（纯 UI 选中）", "读数": c2,
            "★ 选中节点": c2["★ 选中节点"]})

        # A3：纯 UI 拖拽
        before = pg.evaluate(RO)["★ 节点位置"]
        if target:
            pg.mouse.move(target["x"], target["y"])
            pg.mouse.down()
            pg.wait_for_timeout(200)
            for i in range(1, 7):
                pg.mouse.move(target["x"] + 18 * i, target["y"] + 12 * i)
                pg.wait_for_timeout(60)
            pg.mouse.up()
            pg.wait_for_timeout(800)
        after = pg.evaluate(RO)["★ 节点位置"]
        out["画布"].append({
            "步骤": "A3·真实鼠标拖拽 +108px/+72px",
            "★ 拖之前": before, "★ 拖之后": after,
            "★ 位置变了": before != after})

        # A4：Delete 键
        n_before = pg.evaluate(RO)["★ 节点数"]
        pg.keyboard.press("Delete")
        pg.wait_for_timeout(800)
        n_after = pg.evaluate(RO)["★ 节点数"]
        out["画布"].append({
            "步骤": "A4·按 Delete 键",
            "★ 删除前节点数": n_before, "★ 删除后节点数": n_after,
            "★ 少了": n_before - n_after,
            "读数": pg.evaluate(RO)})

        # A5：Cmd+Z 撤销
        pg.keyboard.press("Meta+z")
        pg.wait_for_timeout(900)
        n_undo = pg.evaluate(RO)["★ 节点数"]
        out["画布"].append({
            "步骤": "A5·按 Cmd+Z 撤销", "★ 撤销后节点数": n_undo,
            "★ 回到删除前": n_undo == n_before, "读数": pg.evaluate(RO)})

        # A6：Cmd+Shift+Z 重做
        pg.keyboard.press("Meta+Shift+z")
        pg.wait_for_timeout(900)
        n_redo = pg.evaluate(RO)["★ 节点数"]
        out["画布"].append({
            "步骤": "A6·按 Cmd+Shift+Z 重做", "★ 重做后节点数": n_redo,
            "★ 等于删除后": n_redo == n_after, "读数": pg.evaluate(RO)})

        # A7：纯 UI 连线（从 source handle 拖到另一个节点的 target handle）
        handles = pg.evaluate("""()=>Array.from(document.querySelectorAll(
          '[data-handleid=source]')).map(e=>{
          const r=e.getBoundingClientRect();
          return {节点:e.getAttribute('data-nodeid'),
                  x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};})""")
        targets = pg.evaluate("""()=>Array.from(document.querySelectorAll(
          '[data-handleid=target]')).map(e=>{
          const r=e.getBoundingClientRect();
          return {节点:e.getAttribute('data-nodeid'),
                  x:Math.round(r.x+r.width/2),y:Math.round(r.y+r.height/2)};})""")
        out["操作"]["A7 source handle"] = handles
        out["操作"]["A7 target handle"] = targets
        e_before = pg.evaluate(RO)["★ 边数"]
        made = False
        if handles and targets:
            src, dst = handles[0], None
            for t in targets:
                if t["节点"] != src["节点"]:
                    dst = t
                    break
            if dst:
                pg.mouse.move(src["x"], src["y"])
                pg.mouse.down()
                pg.wait_for_timeout(200)
                pg.mouse.move((src["x"] + dst["x"]) // 2,
                              (src["y"] + dst["y"]) // 2, steps=6)
                pg.wait_for_timeout(150)
                pg.mouse.move(dst["x"], dst["y"], steps=6)
                pg.wait_for_timeout(250)
                pg.mouse.up()
                pg.wait_for_timeout(900)
                made = True
        e_after = pg.evaluate(RO)["★ 边数"]
        out["画布"].append({
            "步骤": "A7·纯 UI 从 source handle 拖到 target handle",
            "★ 真的拖了": made,
            "★ 连线前边数": e_before, "★ 连线后边数": e_after,
            "★ 多了": e_after - e_before})

        # ═════════════ 导演台 ═════════════
        out["操作"]["B1 打开导演台"] = safe_click(pg, "[data-open-director]")
        pg.wait_for_timeout(4200)
        opened = pg.evaluate(
            "()=>!!document.querySelector('[data-director-workspace]')")
        d0 = pg.evaluate(RO_D)
        out["导演台"].append({
            "步骤": "B1·点「打开导演台」",
            "★ 导演台开了": opened, "读数": d0,
            "★ 时间轴对象行候选": cand(
                pg, "[data-director-timeline-object-row]")})

        # B2：★ 枢纽 —— 纯 UI 能不能选中**相机轨道**？
        rows = pg.evaluate("""()=>Array.from(document.querySelectorAll(
          '[data-director-timeline-object-row]')).map(e=>{
          const r=e.getBoundingClientRect();
          return {对象id:e.getAttribute('data-director-timeline-object-row'),
                  选中:e.getAttribute('data-director-timeline-object-selected'),
                  文本:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,30),
                  rect:{x:Math.round(r.x),y:Math.round(r.y),
                        w:Math.round(r.width),h:Math.round(r.height)}};})""")
        out["操作"]["B2 时间轴对象行"] = rows
        cam_obj = None
        for tr in d0["★ 轨道清单"]:
            if tr["kind"] == "camera":
                cam_obj = tr["对象"]
                break
        out["操作"]["B2 相机轨道对应的对象 id"] = cam_obj
        row = None
        for r in rows:
            if cam_obj and r["对象id"] == cam_obj:
                row = r
                break
        out["操作"]["B2 匹配到的那一行"] = row
        # ★★ 探针返工（第三版）：点**对象名**，不是行首。
        #   `DirectorTimeline.tsx:1664` 的对象名是
        #   `data-director-timeline-object-name={group.objectId}`、
        #   onClick → `selectTimelineTrack(group.tracks[0].id)`；
        #   而行首（x+12）那个位置是 **展开/收起箭头**
        #   （aria「展开属性」），点它**只 toggle 展开、不选轨道**
        #   ⟹ ★ 第一、二版探针点的是行首 ⟹ 读数「没变」⟹
        #   ★ 差点把「纯 UI 选不中相机轨道」写成结论（**读数对不上先怀疑自己**）。
        name_el = pg.query_selector(
            '[data-director-timeline-object-name="%s"]' % cam_obj) if cam_obj else None
        out["操作"]["B2 对象名元素"] = {
            "存在": bool(name_el),
            "aria": (name_el.get_attribute("title") if name_el else None),
        }
        if name_el:
            nb = name_el.bounding_box()
            out["操作"]["B2 对象名矩形"] = nb
            pg.mouse.click(nb["x"] + nb["width"] / 2, nb["y"] + nb["height"] / 2)
        elif row:
            pg.mouse.click(row["rect"]["x"] + 12,
                           row["rect"]["y"] + row["rect"]["h"] / 2)
        pg.wait_for_timeout(1200)
        d1 = pg.evaluate(RO_D)
        out["导演台"].append({
            "步骤": "B2·★ 点时间轴上的相机对象行（纯 UI 选相机）",
            "★ 点了哪一行": row, "读数": d1,
            "★ 选中轨道变了": d1["选中轨道"] != d0["选中轨道"],
            "★ 选中对象变了": d1["★ 选中对象"] != d0["★ 选中对象"]})

        # B3：检查器里有没有「跟随目标」下拉（要先选中相机对象）
        fsel = pg.query_selector("[data-director-camera-follow-target]")
        out["操作"]["B3 跟随目标 select"] = {
            "存在": bool(fsel),
            "disabled": (fsel.is_disabled() if fsel else None),
            "选项": ([o.get_attribute("value") for o in
                      fsel.query_selector_all("option")] if fsel else []),
        }
        d2 = d1
        if fsel and not fsel.is_disabled():
            vals = [o.get_attribute("value") for o in
                    fsel.query_selector_all("option") if o.get_attribute("value")]
            if vals:
                fsel.select_option(vals[0])
                pg.wait_for_timeout(1000)
            d2 = pg.evaluate(RO_D)
        out["导演台"].append({
            "步骤": "B3·在检查器里选跟随目标（纯 UI）", "读数": d2,
            "★ 跟随目标变了": d2["★ 跟随目标"] != d1["★ 跟随目标"]})

        # B4：纯 UI 锁定（**要读被选中的那个对象的 locked**）
        lock = pg.query_selector("[data-director-inspector-lock]")
        out["操作"]["B4 锁定按钮"] = {
            "存在": bool(lock),
            "aria": (lock.get_attribute("aria-label") if lock else None),
            "disabled": (lock.is_disabled() if lock else None),
        }
        d3 = d2
        if lock and not lock.is_disabled():
            out["操作"]["B4 点击"] = safe_click(
                pg, "[data-director-inspector-lock]")
            pg.wait_for_timeout(900)
            d3 = pg.evaluate(RO_D)
        out["导演台"].append({
            "步骤": "B4·点检查器里的锁定按钮（纯 UI）", "读数": d3,
            "★ 相机锁定变了": d3["★ 相机锁定"] != d2["★ 相机锁定"]})

        # B5：解锁后开预设面板
        if lock and not lock.is_disabled():
            out["操作"]["B5b 解锁"] = safe_click(
                pg, "[data-director-inspector-lock]")
            pg.wait_for_timeout(800)
        trig = pg.query_selector("[data-director-camera-preset-trigger]")
        out["操作"]["B5 预设开关"] = {
            "存在": bool(trig),
            "disabled": (trig.is_disabled() if trig else None),
        }
        if trig and not trig.is_disabled():
            out["操作"]["B5 点击"] = safe_click(
                pg, "[data-director-camera-preset-trigger]")
        pg.wait_for_timeout(900)
        panel = pg.evaluate(
            "()=>!!document.querySelector('[data-director-camera-preset-panel]')")
        d4 = pg.evaluate(RO_D)
        out["导演台"].append({
            "步骤": "B5·点预设运镜开关", "★ 面板开了": panel, "读数": d4,
            "★ 面板内提示": pg.evaluate(
                "()=>Array.from(document.querySelectorAll("
                "'[data-director-camera-preset-error]')).map(e=>"
                "(e.textContent||'').trim())")})

        # B6：★★ 纯 UI 下能不能造出 822 的「两句同屏」？
        out["操作"]["B6a 切append"] = safe_click(
            pg, '[data-director-camera-preset-mode-option="append"]')
        pg.wait_for_timeout(500)
        out["操作"]["B6a 按orbit"] = safe_click(
            pg, '[data-director-camera-preset-option="orbit"]')
        pg.wait_for_timeout(1000)
        d5 = pg.evaluate(RO_D)
        out["导演台"].append({
            "步骤": "B6a·append 被拒（★ 面板内应有提示）",
            "★ 面板还开着": pg.evaluate(
                "()=>!!document.querySelector("
                "'[data-director-camera-preset-panel]')"),
            "读数": d5,
            "★ 屏幕上的提示": pg.evaluate(
                "()=>Array.from(document.querySelectorAll("
                "'[data-director-camera-preset-error]')).map(e=>({"
                "文本:(e.textContent||'').trim(),"
                "在面板内:!!e.closest('[data-director-camera-preset-panel]')}))")})

        # ★★ 关键：纯 UI 点跟随 select（面板开着时会被外部点击关闭）
        fsel2 = pg.query_selector("[data-director-camera-follow-target]")
        out["操作"]["B6 跟随 select 现在"] = {
            "存在": bool(fsel2),
            "disabled": (fsel2.is_disabled() if fsel2 else None),
        }
        d6 = d5
        if fsel2 and not fsel2.is_disabled():
            vals2 = [o.get_attribute("value") for o in
                     fsel2.query_selector_all("option")
                     if o.get_attribute("value")]
            if vals2:
                fsel2.select_option(vals2[0])
                pg.wait_for_timeout(1000)
            d6 = pg.evaluate(RO_D)
        both = pg.evaluate(
            "()=>Array.from(document.querySelectorAll("
            "'[data-director-camera-preset-error]')).map(e=>({"
            "文本:(e.textContent||'').trim(),"
            "在面板内:!!e.closest('[data-director-camera-preset-panel]')}))")
        out["导演台"].append({
            "步骤": "B6b·★★ 纯 UI 点跟随 select 之后",
            "★ 面板还开着": pg.evaluate(
                "()=>!!document.querySelector("
                "'[data-director-camera-preset-panel]')"),
            "★ 屏幕上的提示": both, "读数": d6,
            "★ 两句同屏了吗": len(both) >= 2})

        # ═════════ B7：★★ 清掉跟随 ⟹ 面板就能开 ⟹ append 才可能被拒
        #   ★ 清跟随有**两个**纯 UI 入口，各测一次：
        #     ① 跟随横幅上的取消（`data-director-follow-cancel`）
        #        —— ★★ 那个横幅整块是 `pointer-events-none`（`DirectorDesk.tsx:1393`
        #           注释说这是**有意偏离源站**）⟹ 按钮点不点得动**要实测**；
        #     ② 检查器里那个 select 选「不跟随」。
        cancel = pg.query_selector("[data-director-follow-cancel]")
        out["操作"]["B7 跟随横幅取消按钮"] = {
            "存在": bool(cancel),
            "aria": (cancel.get_attribute("aria-label") if cancel else None),
        }
        if cancel:
            bb = cancel.bounding_box()
            out["操作"]["B7 取消按钮矩形"] = bb
            out["操作"]["B7 点击取消"] = safe_click(
                pg, "[data-director-follow-cancel]")
            pg.wait_for_timeout(1000)
        d7 = pg.evaluate(RO_D)
        out["导演台"].append({
            "步骤": "B7·★ 点跟随横幅上的取消（纯 UI 清跟随）",
            "读数": d7,
            "★ 跟随目标清了吗": d7["★ 跟随目标"] is None})

        # 若横幅取消没生效，改用检查器的 select 选「不跟随」
        d7b = d7
        if d7b["★ 跟随目标"] is not None:
            fsel3 = pg.query_selector("[data-director-camera-follow-target]")
            if fsel3 and not fsel3.is_disabled():
                fsel3.select_option("")
                pg.wait_for_timeout(1000)
                d7b = pg.evaluate(RO_D)
            out["导演台"].append({
                "步骤": "B7b·改用检查器 select 选「不跟随」",
                "读数": d7b,
                "★ 跟随目标清了吗": d7b["★ 跟随目标"] is None})

        # B8：★★ 现在面板能开 ⟹ 让 append 被拒 ⟹ 面板内出现那句
        trig2 = pg.query_selector("[data-director-camera-preset-trigger]")
        out["操作"]["B8 预设开关"] = {
            "存在": bool(trig2),
            "disabled": (trig2.is_disabled() if trig2 else None),
        }
        if trig2 and not trig2.is_disabled():
            out["操作"]["B8 点击"] = safe_click(
                pg, "[data-director-camera-preset-trigger]")
        pg.wait_for_timeout(900)
        out["操作"]["B8a 切append"] = safe_click(
            pg, '[data-director-camera-preset-mode-option="append"]')
        pg.wait_for_timeout(500)
        out["操作"]["B8a 按orbit"] = safe_click(
            pg, '[data-director-camera-preset-option="orbit"]')
        pg.wait_for_timeout(1000)
        d8 = pg.evaluate(RO_D)
        panel_on = pg.evaluate(
            "()=>!!document.querySelector("
            "'[data-director-camera-preset-panel]')")
        tips8 = pg.evaluate(
            "()=>Array.from(document.querySelectorAll("
            "'[data-director-camera-preset-error]')).map(e=>({"
            "文本:(e.textContent||'').trim(),"
            "在面板内:!!e.closest('[data-director-camera-preset-panel]')}))")
        out["导演台"].append({
            "步骤": "B8·★★ 无跟随时开面板 + append ⟹ 面板内应有「没有可追加的时长」",
            "★ 面板开着": panel_on, "读数": d8, "★ 屏幕上的提示": tips8})

        # B9：★★★ 决定性的一条 —— 此刻**纯 UI** 点跟随 select
        #   ⟹ 预期：`:576` 的 pointerdown 外部点击**当场关掉面板**
        #   ⟹ ⟹ 面板内那句「没有可追加的时长」**随之消失**
        #   ⟹ ⟹ ★★ 于是「两句同屏」在纯 UI 下**造不出来**
        fsel4 = pg.query_selector("[data-director-camera-follow-target]")
        out["操作"]["B9 跟随 select"] = {
            "存在": bool(fsel4),
            "disabled": (fsel4.is_disabled() if fsel4 else None),
        }
        d9 = d8
        if fsel4 and not fsel4.is_disabled():
            vals4 = [o.get_attribute("value") for o in
                     fsel4.query_selector_all("option")
                     if o.get_attribute("value")]
            if vals4:
                fsel4.select_option(vals4[0])
                pg.wait_for_timeout(1100)
            d9 = pg.evaluate(RO_D)
        tips9 = pg.evaluate(
            "()=>Array.from(document.querySelectorAll("
            "'[data-director-camera-preset-error]')).map(e=>({"
            "文本:(e.textContent||'').trim(),"
            "在面板内:!!e.closest('[data-director-camera-preset-panel]')}))")
        out["导演台"].append({
            "步骤": "B9·★★★ 纯 UI 点跟随 select 之后（★ 面板还开着吗）",
            "★ 面板还开着": pg.evaluate(
                "()=>!!document.querySelector("
                "'[data-director-camera-preset-panel]')"),
            "★ 屏幕上的提示": tips9, "读数": d9,
            "★ 两句同屏了吗": len(tips9) >= 2,
            "★ 面板内那句还在吗": any(
                t["在面板内"] for t in tips9)})

        # ═════════ B10：★★★ 决定性的一条 —— 用**真实鼠标**点那个 select
        #   ★★ B9 用的是 `select_option()`，它是**程序化设值**：
        #   直接改 value 再派发 change ⟹ ★★ **不产生 pointerdown**
        #   ⟹ 于是绕过了 `:576` 的「面板外部点击关闭」
        #   ⟹ ⟹ B9 的「两句同屏」**仍然不是用户能造出来的**。
        #   ★ 真实用户是**用鼠标点开这个下拉框**的 ⟹ 那一下 pointerdown
        #   落在面板外（检查器不在预设面板里）⟹ ⟹ **面板应当场关掉**。
        #   ⟹ 本臂就量这一下。
        fsel5 = pg.query_selector("[data-director-camera-follow-target]")
        out["操作"]["B10 跟随 select"] = {
            "存在": bool(fsel5),
            "disabled": (fsel5.is_disabled() if fsel5 else None),
        }
        panel_before = pg.evaluate(
            "()=>!!document.querySelector("
            "'[data-director-camera-preset-panel]')")
        if fsel5:
            bb = fsel5.bounding_box()
            out["操作"]["B10 select 矩形"] = bb
            # ★ 真实鼠标点击（⟹ 产生 pointerdown）
            pg.mouse.click(bb["x"] + bb["width"] / 2,
                           bb["y"] + bb["height"] / 2)
            pg.wait_for_timeout(700)
        panel_after = pg.evaluate(
            "()=>!!document.querySelector("
            "'[data-director-camera-preset-panel]')")
        tips10 = pg.evaluate(
            "()=>Array.from(document.querySelectorAll("
            "'[data-director-camera-preset-error]')).map(e=>({"
            "文本:(e.textContent||'').trim(),"
            "在面板内:!!e.closest('[data-director-camera-preset-panel]')}))")
        out["导演台"].append({
            "步骤": "B10·★★★ **真实鼠标**点跟随 select（★ 面板被点关了吗）",
            "★ 点击前面板开着": panel_before,
            "★ 点击后面板开着": panel_after,
            "★ 面板被真实点击关掉了": (panel_before and not panel_after),
            "★ 屏幕上的提示": tips10,
            "★ 两句同屏了吗": len(tips10) >= 2,
            "★ 面板内那句还在吗": any(
                t["在面板内"] for t in tips10)})

        return out
    except Exception as exc:                                    # noqa: BLE001
        out["★ 异常"] = {"类型": type(exc).__name__, "详情": str(exc)[:300]}
        return out
    finally:
        pg.close()


def main():
    out = {"★ 探针自身失败": None}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        try:
            out = run(br)
        except Exception as exc:                                # noqa: BLE001
            out = {"★ 探针自身失败": {"类型": type(exc).__name__,
                                       "详情": str(exc)[:400]}}
        finally:
            br.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print("画布步数", len(out.get("画布", [])), "导演台步数",
          len(out.get("导演台", [])))


if __name__ == "__main__":
    main()
