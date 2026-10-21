#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 834 clone 侧探针：读 clone 的 **5 步引导**，并**按源站算法重算位置**自证。

★ 读什么（每一步）：
  - 气泡的正文 / 步数 / 盒 / 两枚按钮的文案与盒；
  - 光环（ring）的盒；
  - ★★ **按源站 chunk 原文的算法重算**一次位置（从 DOM 找 target ＋ 图标锚点），
    再与**实际渲染出来的**气泡盒比对 ⟹ 这样判的是「算法被照抄了」，
    而不是「某个绝对坐标碰巧对」。

★ 为什么**不**直接比绝对坐标：源站那次活体采集时场景里**有**相机轨道
  （所以第 2/3 步分别指向「绘制轨迹」与浮层里的「圆环」），
  而 clone 的默认场景**没有**轨道 ⟹ 源站的算法会**退回**到 add-track
  ⟹ 绝对坐标当然不同 ⟹ 那不是「clone 错了」，是**场景状态不同**。

★ 期望值来自 raw/source-834-timeline-guide.json（源站活体 ＋ chunk 原文两路交叉核对）。
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

BATCH = pathlib.Path(__file__).resolve().parent.parent
RAW = BATCH / "raw" / "source-834-timeline-guide.json"
OUT = BATCH / "raw" / "clone-834-timeline-guide.json"
SHOTS = pathlib.Path("/tmp/liblib_clone_guide834")

BASE = "http://localhost:4317"

# ★ 读气泡 ＋ 光环 ＋ **按源站算法重算**位置
DUMP = """()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const bubble=document.querySelector('[data-director-timeline-guide-bubble]');
  const ring=document.querySelector('[data-director-timeline-guide-ring]');
  const overlay=document.querySelector('[data-director-timeline-guide-overlay]');
  const out={overlay:Boolean(overlay), bubble:null, ring:null};
  if(bubble){
    const count=document.querySelector('[data-director-timeline-guide-count]');
    const body=bubble.querySelector('div');
    const buttons=Array.from(bubble.querySelectorAll('button')).filter(vis)
      .map(b=>({t:(b.textContent||'').trim(), box:box(b)}));
    out.bubble={
      text:(body?(body.textContent||''):'').trim(),
      count:(count?(count.textContent||'').trim():''),
      box:box(bubble),
      buttons,
      class:String(bubble.className||'').slice(0,200),
      styleLeft:bubble.style.left, styleTop:bubble.style.top,
      styleWidth:bubble.style.width,
    };
  }
  if(ring) out.ring={box:box(ring)};
  // ★ 源站算法（chunk 原文照抄）——用来重算位置
  const byTarget=(n)=>document.querySelector('[data-director-timeline-guide-target="'+n+'"]');
  const visibleTargets=Array.from(document.querySelectorAll(
      '[data-director-timeline-guide-target]'))
    .filter(vis).map(e=>e.getAttribute('data-director-timeline-guide-target'));
  out.visibleTargets=visibleTargets;
  return out;
}"""

# ★ 源站的 5 步参数（与组件里的一致，从 raw 的「代码定义」读出来传给 JS）
STEP_SPECS = [
    {"target": "add-track", "width": 260, "bubbleOffsetX": -80, "bubbleHeight": 112},
    {"target": "draw-trajectory", "width": 300, "bubbleOffsetX": -64, "bubbleHeight": 112},
    {"target": "motion-preset-ring", "width": 360, "bubbleOffsetX": -48, "bubbleHeight": 136},
    {"target": "play", "width": 300, "bubbleOffsetX": 12, "bubbleHeight": 112},
    {"target": "export-to-canvas", "width": 360, "bubbleOffsetX": -268, "bubbleHeight": 112},
]

# ★ 用**源站的算法**重算（step 由调用方传进来）
RECOMPUTE = """(spec)=>{
  const byTarget=(n)=>document.querySelector('[data-director-timeline-guide-target="'+n+'"]');
  const target=byTarget(spec.target)
    ?? (spec.target==='motion-preset-ring'?byTarget('draw-trajectory'):null)
    ?? byTarget('add-track');
  if(!target) return {found:false};
  const t=target.getBoundingClientRect();
  const iconEl=target.querySelector('[data-director-timeline-guide-icon="true"]')||target;
  const n=iconEl.getBoundingClientRect();
  const clamp=(v,lo,hi)=>Math.min(Math.max(v,lo),hi);
  const width=Math.min(spec.width, window.innerWidth-24);
  const centerX=n.left+n.width/2;
  const left=clamp(centerX+spec.bubbleOffsetX, 12, window.innerWidth-width-12);
  const above=t.top-spec.bubbleHeight-2;
  const top=above>=12?above:clamp(t.bottom+14, 12, window.innerHeight-120);
  return {found:true, usedTarget:target.getAttribute('data-director-timeline-guide-target'),
          left:Math.round(left), top:Math.round(top), width:Math.round(width),
          ringLeft:Math.round(centerX-30), ringTop:Math.round(n.top+n.height/2-30),
          iconCenterX:Math.round(centerX)};
}"""


def main():
    src_raw = json.loads(RAW.read_text(encoding="utf-8"))
    out = {"说明": "clone 侧 5 步引导的活体读数 ＋ 按源站算法的重算位置"}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        page = br.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(f"{BASE}/?batch834=1", wait_until="networkidle", timeout=90_000)
        page.wait_for_function(
            "() => Boolean(window.__libtv_store && window.__libtv_ui_store "
            "&& window.__director_store)", timeout=60_000)
        page.wait_for_timeout(800)
        nid = page.evaluate("""() => {
          const nodes = window.__libtv_store.getState().getActiveCanvas().nodes
            .filter((n) => n.type === 'script-execution');
          return nodes.length === 1 ? nodes[0].id : null;
        }""")
        page.locator('.react-flow__node[data-id="%s"] [data-open-director]' % nid).first.click()
        page.locator("[data-director-workspace]").wait_for(state="visible", timeout=30_000)
        page.wait_for_timeout(2_500)
        page.evaluate(
            "() => { for (const el of document.querySelectorAll('nextjs-portal')) el.remove(); }")
        SHOTS.mkdir(exist_ok=True)

        steps = []
        for i, spec in enumerate(STEP_SPECS):
            reading = page.evaluate(DUMP)
            recomputed = page.evaluate(RECOMPUTE, spec)
            record = {"步序": i, "读数": reading, "重算": recomputed}
            steps.append(record)
            page.screenshot(path=str(SHOTS / ("834_clone_step_%d.png" % i)))
            btn = page.get_by_role("button", name="下一步", exact=True)
            label = "下一步"
            if not btn.count():
                btn = page.get_by_role("button", name="完成", exact=True)
                label = "完成"
            if not btn.count():
                record["点击"] = "没有推进按钮"
                break
            try:
                btn.first.click(timeout=4_000)
                page.wait_for_timeout(1_200)
                record["点击"] = "点了「%s」" % label
            except Exception as exc:  # noqa: BLE001
                record["点击"] = "★ 点不动：%s" % str(exc).splitlines()[0][:160]
                # ★ 用 JS 直接点，绕开命中测试（并把这件事如实记下来）
                page.evaluate(
                    "() => { const b=document.querySelector"
                    "('[data-director-timeline-guide-next]'); if(b) b.click(); }")
                page.wait_for_timeout(1_200)
                record["★JS 直点后"] = page.evaluate(DUMP)
        out["逐步"] = steps
        out["走完后"] = page.evaluate(DUMP)
        # ★ 收起标记是否写进去了
        out["localStorage"] = page.evaluate(
            "() => window.localStorage.getItem('director-timeline-coach-dismissed')")
        br.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落盘：", OUT)
    for s in steps:
        b = (s["读数"] or {}).get("bubble")
        rc = s["重算"]
        if not b:
            print("  步%s：没有气泡" % s["步序"])
            continue
        print("  步%s %s 正文=%r 宽=%s 左=%s(重算%s) 上=%s(重算%s) 按钮=%s"
              % (s["步序"], b["count"], b["text"][:22], b["box"]["w"],
                 b["box"]["x"], rc.get("left"), b["box"]["y"], rc.get("top"),
                 [x["t"] for x in b["buttons"]]))


if __name__ == "__main__":
    main()
