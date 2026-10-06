#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 821 探针 —— 导演台·相机预设的**错误提示**是「状态算出来的」还是「操作产生的」

## 为什么换到导演台

815–820 六批全在画布那一条链上（派生节点 → 撤销栈 → 封顶）。
用户指定的两个重点是**画布与导演台**，导演台**六批完全没碰** ⟹ 本批换面。

## 起点（读源码发现的）

`directorStore.ts:7565` 的 `applyCameraMotionPreset` 有**三条拒绝分支**，
反馈机制**不一样**：

| 分支 | 条件 | 反馈写到哪 |
| --- | --- | --- |
| 序1 | `camera.locked`（`:7575`） | **只**写 `lastCommandResult`（REJECTED／`DIRECTOR_TARGET_LOCKED`） |
| 序2 | `camera.camera.followTargetId`（`:7587`） | 写 `cameraMotionPreset.error`，文案「跟随目标时不可使用预设运镜」 |
| 序3 | `append` 且没有可追加时长（`:7606`） | 写 `cameraMotionPreset.error`，文案「当前时间轴没有可追加的时长」 |

★ 而 **UI 上有两处 `data-director-camera-preset-error`**，
**驱动源完全不同**：

- `DirectorTimeline.tsx:1097` ← 条件 `cameraFollowActive`
  ⟹ ★ **状态驱动**：用户**一个按钮都还没点**，提示就已经在屏幕上了；
- `DirectorTimeline.tsx:1468` ← `selectedPresetError`（来自 store 的 `error`）
  ⟹ **操作驱动**：只有真的按了预设才会出现。

★ 而 `:1084` 的开关按钮是
`disabled={selectedTrack?.kind !== "camera" || cameraFollowActive}`
⟹ ★ **跟随目标时按钮直接 disabled** ⟹ store 的**分支 序2 用户根本走不到**
（`:602`／`:696` 也各有一次同样的守卫）。

⟹ 本批量三件事：
① 跟随目标激活时，按钮是不是 disabled、`data-...-error` 是不是**已经**在屏幕上；
② 程序化调用 `applyCameraMotionPreset` 能不能走到 store 的分支 序2
（⟹ 分支 序2 是不是**只能程序化到达**）；
③ 锁住相机后按预设，用户**看到什么**（走 `lastCommandResult` 那条通道）。

## ★ 同一个 data 属性有**两处渲染** ⟹ 必须靠 DOM 祖先关系区分

`:1097` 那处在**预设面板外面**，`:1468` 那处在**面板里面**
（面板容器是 `[data-director-camera-preset-panel]`）⟹
所以「提示在不在面板内部」就是一个**可判的**读数。

## ★ 扫描器自检

否定性读数（「面板外没有提示」）最容易是**扫描器坏了** ⟹
每次扫描都先注入一个带 `data-director-camera-preset-error` 的探针节点、
必须扫得到它，再删掉探针扫真实 DOM。
"""
import json
import os
import pathlib
import sys
import time
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

OUT = pathlib.Path(os.environ.get("VB821_OUT") or
                   (HERE.parent / "raw" / "vb821a.json"))

STATE = """()=>{const S=window.__director_store.getState();
  const t=S.timeline.tracks.find(x=>x.kind==='camera')||null;
  const cam=t?S.objects.find(o=>o.id===t.objectId):null;
  const e=S.timeline.cameraMotionPreset&&S.timeline.cameraMotionPreset.error;
  const l=S.lastCommandResult||null;
  return {选中轨道:t?t.id:null, 轨道关键帧数:t?t.keyframes.length:null,
          相机对象:t?t.objectId:null,
          相机锁定:cam?!!cam.locked:null,
          跟随目标:cam&&cam.camera?cam.camera.followTargetId||null:null,
          presetError:e?{trackId:e.trackId,preset:e.preset,mode:e.mode,
                        message:e.message}:null,
          lastCommand:l?{kind:l.commandKind,disposition:l.disposition,
                         reason:l.reason}:null};}"""

#: ★ 扫描两处提示 ＋ **区分它们在不在面板内部** ＋ 扫描器自检
SCAN = """()=>{
  // ★★ 探针返工（两处，**都是「否定性读数其实是探针坏了」**）：
  //   ① 第一版**只扫** `data-director-camera-preset-error` ⟹ 于是
  //      「锁定拒绝之后没有任何提示变化」被读成了**静默**——
  //      ★ 其实锁定的反馈走的是**另一条通道**
  //      `DirectorDesk.tsx:983` 的 `data-director-command-feedback`
  //      （`role="status"`），第一版**压根没扫它**。
  //   ② ★ 更阴的一处：`DirectorDesk.tsx:999` 的
  //      `!commandFeedback && "invisible"` 是 Tailwind 的 `invisible`
  //      ＝ **`visibility: hidden`** ⟹ **元素在 DOM 里、有尺寸、但用户看不见**
  //      ⟹ 第一版「跳过零尺寸元素」的过滤**抓不到它**。
  //      ⟹ 所以判「用户看得见」必须读**计算样式**：
  //      尺寸非零 **且** `visibility !== hidden` **且** `opacity > 0`。
  const visible=(e)=>{const r=e.getBoundingClientRect();
    if(r.width===0&&r.height===0)return false;
    const cs=getComputedStyle(e);
    return cs.visibility!=='hidden'&&cs.visibility!=='collapse'
      && cs.display!=='none' && Number(cs.opacity||'1')>0;};
  const scan=()=>{const out=[];
    for(const e of Array.from(
        document.querySelectorAll('[data-director-camera-preset-error]'))){
      if(!visible(e))continue;
      out.push({通道:'预设错误提示',
                文本:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,60),
                在预设面板内部:!!e.closest('[data-director-camera-preset-panel]')});}
    for(const e of Array.from(
        document.querySelectorAll('[data-director-command-feedback]'))){
      if(!visible(e))continue;
      out.push({通道:'命令反馈',
                文本:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,60),
                处置:e.getAttribute('data-director-command-feedback-disposition'),
                理由:e.getAttribute('data-director-command-feedback-reason'),
                在预设面板内部:!!e.closest('[data-director-camera-preset-panel]')});}
    return out;};
  // ★ 扫描器自检：**两个通道各注入一个探针**，都必须扫得到
  const PROBES=[['data-director-camera-preset-error','扫描器探针821a'],
                ['data-director-command-feedback','扫描器探针821b']];
  for(const [attr,txt] of PROBES){
    const d=document.createElement('div');
    d.setAttribute(attr,'');
    d.style.cssText='position:fixed;left:0;top:0;width:12px;height:12px';
    d.textContent=txt;
    document.body.appendChild(d);}
  const selfTest=scan().filter(
    x=>PROBES.some(([,t])=>x.文本===t)).length;
  for(const d of Array.from(document.body.children))
    if(PROBES.some(([,t])=>d.textContent===t)) d.remove();
  const trig=document.querySelector('[data-director-camera-preset-trigger]');
  return {提示:scan(),
          面板开着:!!document.querySelector('[data-director-camera-preset-panel]'),
          开关按钮存在:!!trig,
          开关按钮disabled:trig?trig.disabled===true:null,
          开关按钮title:trig?trig.getAttribute('title'):null,
          '★ 扫描器自检':selfTest>0,
          '★ 探针被扫到几个':selfTest};}"""


def rd(pg, tag):
    s, c = pg.evaluate(STATE), pg.evaluate(SCAN)
    vis = c["提示"]
    return {"时刻": tag, "store": s, "dom": c, "所有可见提示": vis,
            "★ 预设错误提示": [x for x in vis if x["通道"] == "预设错误提示"],
            "★ 命令反馈": [x for x in vis if x["通道"] == "命令反馈"],
            "★ 面板外的提示": [x for x in vis if not x["在预设面板内部"]],
            "★ 面板内的提示": [x for x in vis if x["在预设面板内部"]]}


def click(pg, sel):
    el = pg.query_selector(sel)
    if not el:
        return "not-found"
    if el.is_disabled():
        return "disabled"
    el.click()
    return "clicked"


def run(b):
    pg = b.new_page()
    pg.set_default_timeout(25000)
    try:
        pg.goto(A.BASE, wait_until="domcontentloaded")
        pg.wait_for_timeout(2500)
        pg.evaluate("""()=>{const S=window.__libtv_store.getState();
          S.addNodeAtPosition('script-execution',{x:160,y:160});}""")
        pg.wait_for_timeout(1400)
        btn = pg.query_selector("[data-open-director]")
        if not btn:
            return {"FAILED": "找不到「打开导演台」按钮"}
        btn.click()
        pg.wait_for_timeout(4000)
        if not pg.query_selector("[data-director-workspace]"):
            return {"FAILED": "导演台没打开"}

        out = {"读取": [], "操作": {}}
        out["读取"].append(rd(pg, "序0·刚打开导演台、什么都还没点"))

        # ★ 让相机轨道成为选中轨道（否则按钮本来就 disabled）
        sel = pg.evaluate("""()=>{const S=window.__director_store.getState();
          const t=S.timeline.tracks.find(x=>x.kind==='camera');
          if(!t)return null;
          S.selectTimelineTrack(t.id);
          return t.id;}""")
        out["操作"]["选中相机轨道"] = sel
        pg.wait_for_timeout(700)
        out["读取"].append(rd(pg, "序0b·选中了相机轨道、还没点任何按钮"))

        cam_obj = pg.evaluate("""()=>{const S=window.__director_store.getState();
          const t=S.timeline.tracks.find(x=>x.kind==='camera');
          return t?t.objectId:null;}""")
        out["操作"]["相机对象"] = cam_obj

        # ── 臂 1：跟随目标
        if cam_obj:
            tgt = pg.evaluate("""(o)=>{const S=window.__director_store.getState();
              const other=S.objects.find(x=>x.id!==o&&!x.camera);
              if(!other)return null;
              S.updateCamera(o,{followTargetId:other.id});
              return other.id;}""", cam_obj)
            out["操作"]["跟随目标"] = tgt
            pg.wait_for_timeout(800)
            out["读取"].append(rd(pg, "臂1·设了跟随目标、**一个按钮都还没点**"))
            # ★ 程序化调用：看 store 的分支 序2 到底能不能走到
            out["操作"]["程序化 applyCameraMotionPreset"] = pg.evaluate(
                """(o)=>{const S=window.__director_store.getState();
                  const t=S.timeline.tracks.find(x=>x.kind==='camera');
                  if(!t)return {ok:false,why:'no camera track'};
                  try{
                    const r=S.applyCameraMotionPreset('orbit','replace',t.id);
                    // ★★ 探针返工：zustand 的 `getState()` 返回**调用前的快照**，
                    //   `set()` 之后 `S.timeline` **不会**更新 ⟹ 第一版在同一个
                    //   evaluate 里读 `S.timeline...error` 读到的是 **null**，
                    //   ★ 差点把「分支序2 走不到」写成结论（809／810 的老坑：
                    //   **读数对不上时先怀疑自己**）。修法：**调用后重新 getState**。
                    const S2=window.__director_store.getState();
                    return {返回:r,
                            presetError:(
                              S2.timeline.cameraMotionPreset.error||{}).message||null,
                            lastCommand:(S2.lastCommandResult||{}).reason||null};}
                  catch(e){return {threw:String(e)}};}""", cam_obj)
            pg.wait_for_timeout(600)
            out["读取"].append(rd(pg, "臂1b·程序化调过预设之后"))
            # 清掉跟随
            pg.evaluate("""(o)=>{window.__director_store.getState()
              .updateCamera(o,{followTargetId:null});}""", cam_obj)
            pg.wait_for_timeout(700)
            out["读取"].append(rd(pg, "臂1c·清掉跟随目标之后"))

        # ── 臂 2：锁住相机 → 开面板 → 按一个预设
        if cam_obj:
            pg.evaluate("""(o)=>{window.__director_store.getState()
              .updateObject(o,{locked:true});}""", cam_obj)
            pg.wait_for_timeout(700)
            out["读取"].append(rd(pg, "臂2·锁住相机、还没按预设"))
            out["操作"]["开面板"] = click(
                pg, "[data-director-camera-preset-trigger]")
            pg.wait_for_timeout(800)
            out["读取"].append(rd(pg, "臂2b·打开预设面板之后"))
            out["操作"]["按预设"] = click(
                pg, '[data-director-camera-preset-option="orbit"]')
            pg.wait_for_timeout(1000)
            out["读取"].append(rd(pg, "臂2c·锁定状态下按了预设之后"))
            # 解锁再按一次，看成功时提示会不会被清掉
            pg.evaluate("""(o)=>{window.__director_store.getState()
              .updateObject(o,{locked:false});}""", cam_obj)
            pg.wait_for_timeout(600)
            out["操作"]["解锁后再按预设"] = click(
                pg, '[data-director-camera-preset-option="orbit"]')
            pg.wait_for_timeout(1000)
            out["读取"].append(rd(pg, "臂2d·解锁后按预设（成功路径）"))
        return out
    except Exception as e:  # noqa: BLE001
        return {"FAILED": "%s: %s" % (type(e).__name__, e)}
    finally:
        try:
            pg.close()
        except Exception:  # noqa: BLE001
            pass


def main():
    out = {"base": A.BASE, "cells": []}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        t0 = time.time()
        c = run(br)
        c["round"] = 0
        c["secs"] = round(time.time() - t0, 1)
        out["cells"].append(c)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        if c.get("FAILED"):
            print("FAILED:", c["FAILED"], flush=True)
        for r in (c.get("读取") or []):
            d = r.get("dom") or {}
            print("%-30s | 开关disabled=%s | 预设错误提示=%s | 命令反馈=%s" % (
                r.get("时刻"), d.get("开关按钮disabled"),
                json.dumps([(x["文本"], x["在预设面板内部"]) for x in
                            (r.get("★ 预设错误提示") or [])], ensure_ascii=False),
                json.dumps([(x["文本"], x.get("理由")) for x in
                            (r.get("★ 命令反馈") or [])], ensure_ascii=False)),
                flush=True)
        print("操作:", json.dumps(c.get("操作"), ensure_ascii=False), flush=True)
        br.close()
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written", OUT)


if __name__ == "__main__":
    main()