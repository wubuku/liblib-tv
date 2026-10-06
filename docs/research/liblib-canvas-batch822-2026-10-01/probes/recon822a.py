#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 822 侦察 —— 分支序3 的前提到底存不存在

要回答的四件事（全部只读，不造状态）：
  R1 种子数据下，相机轨道最后一个关键帧的 time 是多少、总时长是多少
     ⟹ `lastKeyframe.time >= duration - 0.001` 这个前提**天然成立吗**
  R2 「总时长」输入框在 ms / s 两种单位下的**显示值**与 `data-...-duration`
     ⟹ ★ UI 能表达的最小刻度是多少（这是容差能不能被用户碰到的关键）
  R3 切到 ms 后往里敲数字，**每敲一位会不会就提交一次**（onChange 里 commit）
     ⟹ 会不会出现「敲到一半的中间值也被写进 store」
  R4 预设面板里「追加运镜」这个模式选项的 DOM 读数（aria-pressed / 文案）
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

OUT = pathlib.Path(os.environ.get("VB822_RECON_OUT") or
                   (HERE.parent / "raw" / "recon822a.json"))

# ★ 相机轨道 + 全局时长的精确读数（不取整：全部原样吐出来）
GEOM = """()=>{const S=window.__director_store.getState();
  const tl=S.timeline;
  const t=tl.tracks.find(x=>x.kind==='camera')||null;
  const kfs=t?t.keyframes:[];
  const last=kfs.length?kfs[kfs.length-1]:null;
  const dur=tl.duration;
  return {
    总时长: dur,
    '★ 总时长×1000': dur*1000,
    播放头: tl.currentTime,
    选中轨道: tl.selectedTrackId,
    相机轨道id: t?t.id:null,
    轨道关键帧数: kfs.length,
    '★ 关键帧时间': kfs.map(k=>k.time),
    '★ 末关键帧时间': last?last.time:null,
    '★ 差（末关键帧 - 总时长）': last?(last.time-dur):null,
    '★ 拒绝条件 last >= dur-0.001': last?String(last.time>=dur-0.001):null,
    '★ 若把总时长设为末关键帧+0.001 仍拒': last?String(last.time>=(last.time+0.001)-0.001):null,
    '★ 若把总时长设为末关键帧+0.002 可过': last?String(!(last.time>=(last.time+0.002)-0.001)):'null',
    所有轨道: tl.tracks.map(x=>({id:x.id,kind:x.kind,
      n:x.keyframes.length,
      last:x.keyframes.length?x.keyframes[x.keyframes.length-1].time:null})),
  };}"""

# ★ 时长框的**绝对读数**：显示文本 + data 属性 + 单位 + 计算尺寸
FIELDS = """()=>{const out=[];
  for(const e of Array.from(document.querySelectorAll('[data-director-time-field]'))){
    const r=e.getBoundingClientRect();
    out.push({字段:e.getAttribute('data-director-time-field'),
              aria:e.getAttribute('aria-label'),
              显示值:e.value,
              单位:e.getAttribute('data-director-time-field-unit'),
              data时间:e.getAttribute('data-director-timeline-time'),
              data时长:e.getAttribute('data-director-timeline-duration'),
              宽:r.width, 高:r.height,
              readOnly:e.readOnly,
              type:e.type});}
  const u=document.querySelector('[data-director-time-unit]');
  return {时间框:out,
          单位按钮:u?{文本:u.textContent.trim(),
                    aria:u.getAttribute('aria-label')}:null};}"""

# ★ 预设面板内的模式选项与预设按钮
PANEL = """()=>{const p=document.querySelector('[data-director-camera-preset-panel]');
  if(!p)return {面板开着:false};
  const modes=Array.from(p.querySelectorAll('[data-director-camera-preset-mode-option]'))
    .map(b=>({mode:b.getAttribute('data-director-camera-preset-mode-option'),
              文本:(b.textContent||'').trim(),
              ariaPressed:b.getAttribute('aria-pressed')}));
  const opts=Array.from(p.querySelectorAll('[data-director-camera-preset-option]'))
    .map(b=>({preset:b.getAttribute('data-director-camera-preset-option'),
              文本:(b.textContent||'').trim().replace(/\\s+/g,' '),
              ariaPressed:b.getAttribute('aria-pressed'),
              disabled:b.disabled===true}));
  const modeBox=p.querySelector('[data-director-camera-preset-mode]');
  return {面板开着:true,
          面板mode:modeBox?modeBox.getAttribute('data-director-camera-preset-mode'):null,
          面板mode属性:p.getAttribute('data-director-camera-preset-panel-mode'),
          模式选项:modes, 预设按钮:opts};}"""


def boot(b):
    pg = b.new_page()
    pg.set_default_timeout(25000)
    pg.goto(A.BASE, wait_until="domcontentloaded")
    pg.wait_for_timeout(2500)
    pg.evaluate("""()=>{const S=window.__libtv_store.getState();
      S.addNodeAtPosition('script-execution',{x:160,y:160});}""")
    pg.wait_for_timeout(1400)
    btn = pg.query_selector("[data-open-director]")
    if not btn:
        raise SystemExit("找不到「打开导演台」按钮")
    btn.click()
    pg.wait_for_timeout(4000)
    if not pg.query_selector("[data-director-workspace]"):
        raise SystemExit("导演台没打开")
    pg.evaluate("""()=>{const S=window.__director_store.getState();
      const t=S.timeline.tracks.find(x=>x.kind==='camera');
      if(t)S.selectTimelineTrack(t.id);}""")
    pg.wait_for_timeout(700)
    return pg


def run():
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        out = {}
        pg = boot(br)
        out["R1 起点（只读）"] = pg.evaluate(GEOM)
        out["R2 时间框·默认单位"] = pg.evaluate(FIELDS)

        # ── 切到 ms
        u = pg.query_selector("[data-director-time-unit]")
        out["R2b 切单位前文本"] = (u.text_content() or "").strip() if u else None
        if u:
            u.click()
        pg.wait_for_timeout(700)
        out["R2c 时间框·ms 单位"] = pg.evaluate(FIELDS)

        # ── R3：往时长框敲 "9000"，记录每一步 store 的时长
        fld = pg.query_selector('[data-director-time-field="duration"]')
        seq = []
        if fld:
            fld.click()
            pg.wait_for_timeout(200)
            for ch in "9000":
                pg.keyboard.type(ch)
                pg.wait_for_timeout(260)
                seq.append({"敲入": ch,
                            "★ 输入框显示": pg.eval_on_selector(
                                '[data-director-time-field="duration"]',
                                "e=>e.value"),
                            "★ store 总时长": pg.evaluate(
                                "()=>window.__director_store.getState().timeline.duration"),
                            "★ DOM data 时长": pg.eval_on_selector(
                                '[data-director-time-field="duration"]',
                                "e=>e.getAttribute('data-director-timeline-duration')")})
        out["R3 逐字符提交"] = seq
        out["R3b 敲完之后"] = {"store": pg.evaluate(GEOM),
                               "时间框": pg.evaluate(FIELDS)}

        # ★ R3c：**能不能敲出小数毫秒**（"9000.5"）
        fld = pg.query_selector('[data-director-time-field="duration"]')
        sub = []
        if fld:
            fld.click()
            pg.wait_for_timeout(200)
            pg.keyboard.press("Meta+A")
            pg.wait_for_timeout(150)
            pg.keyboard.type("9000.5")
            pg.wait_for_timeout(500)
            sub.append({"★ 敲入": "9000.5",
                        "★ 输入框显示": pg.eval_on_selector(
                            '[data-director-time-field="duration"]', "e=>e.value"),
                        "★ store 总时长": pg.evaluate(
                            "()=>window.__director_store.getState().timeline.duration"),
                        "★ DOM data 时长": pg.eval_on_selector(
                            '[data-director-time-field="duration"]',
                            "e=>e.getAttribute('data-director-timeline-duration')")})
        out["R3c ms 模式能不能敲小数"] = sub

        # ── R4：打开预设面板
        trig = pg.query_selector("[data-director-camera-preset-trigger]")
        out["R4a 触发按钮"] = {"disabled": (trig.is_disabled() if trig else None),
                               "title": (trig.get_attribute("title") if trig else None)}
        if trig:
            trig.click()
        pg.wait_for_timeout(800)
        out["R4b 面板"] = pg.evaluate(PANEL)

        out["R5 面板开着时的几何"] = pg.evaluate(GEOM)
        br.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2)[:9000])


if __name__ == "__main__":
    run()