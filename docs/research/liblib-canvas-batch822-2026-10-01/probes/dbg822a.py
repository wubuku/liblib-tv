#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 822 探针 —— 「追加运镜」被拒的那条边界，比时长框能表达的最细刻度**晚 1 毫秒**

## 起点（读源码 + 侦察得到的）

`directorStore.ts:7600` 分支序3 的拒绝条件：

```js
if (mode === "append" &&
    (!lastKeyframe || lastKeyframe.time >= state.timeline.duration - 0.001))
```

★ **它跟播放头一点关系都没有** —— 只看「最后一个关键帧是否已经贴着总时长」。
（821 的「不声称」里写的是「要把播放头拖到时间轴末尾」，**那是错的**，
本批顺手更正。）

侦察实测：种子里相机轨道 3 个关键帧、时间 `[0, 4, 8]`、总时长 `8`
⟹ ★ **前提天然成立**，不需要造状态。

## ★★ 本批的命题：容差 1ms 与「时长框能表达的刻度」**重合**

`DirectorTimeline.tsx:191` 的 `format`／`:193` 的 `parse`：

- `ms` 模式：`format = String(Math.round(seconds * 1000))`、`parse = Number(raw) / 1000`
- 而容差是 `0.001` 秒 = **正好 1ms**

⟹ `duration = 末关键帧 + 1ms` 时
`末关键帧 >= duration - 0.001 = 末关键帧` **成立** ⟹ **仍然被拒**
⟹ ★ **实际临界点在 +2ms**，比 UI 能表达的最细刻度晚一格。

★ ★ 但 `parse` **不校验整数** ⟹ 敲 `8000.5` 会算出 `8.0005`（落在容差**内部**）
⟹ 而 `format` 立刻把它 `Math.round` 回 **`8001`** ⟹ ★★ **框里显示的数与 store 真值不是同一个数**。

## ★ 第二条线：★ 点时长框会把预设面板**点关**

`DirectorTimeline.tsx:576` 的 `pointerdown` 外部点击关闭 ⟹ ★ 面板开着时点「总时长」框，
面板**当场关掉** ⟹ 而时长框恰恰是解开「追加被拒」的那把钥匙
⟹ 用户要多绕「关面板 → 改时长 → 重开面板 → 重选追加模式 → 再按预设」。
★ 好消息：`presetMode` 的 `useState` 在 `DirectorTimeline` 里（面板是条件渲染）
⟹ 面板**不会**把模式重置回「替换运镜」。

## ★ 第三条线：两条拒绝分支**共用一个 error 槽位**

序2（跟随目标）与序3（无可追加时长）都写 `cameraMotionPreset.error`、只有 `message` 不同
⟹ ★ **后写的会盖掉先写的** ⟹ 可能造出**面板外说「跟随…」、面板内说「时长…」**，
而**当下真正的原因是跟随** ⟹ 屏幕上两句**互相矛盾**。

## ★ 扫描器自检

否定性读数（「面板外没有提示」）最容易是**扫描器坏了** ⟹
每次扫描先往**两个通道**各注入一个探针、必须都扫得到，再删掉扫真实 DOM。
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

OUT = pathlib.Path(os.environ.get("VB822_OUT") or
                   (HERE.parent / "raw" / "vb822a.json"))

# ★ 几何读数：末关键帧 vs 总时长，带足精度（毫秒，不取整）
GEOM = """()=>{const S=window.__director_store.getState();
  const tl=S.timeline;
  const t=tl.tracks.find(x=>x.kind==='camera')||null;
  const kfs=t?t.keyframes:[];
  const last=kfs.length?kfs[kfs.length-1]:null;
  const dur=tl.duration;
  const cam=t?S.objects.find(o=>o.id===t.objectId):null;
  return {总时长秒:dur,
          '★ 总时长毫秒':Math.round(dur*1000),
          '★ 总时长精确毫秒':dur*1000,
          '★ 总时长是整数毫秒吗':String(dur*1000===Math.round(dur*1000)),
          '★ 末关键帧毫秒':last?Math.round(last.time*1000):null,
          '★ 末关键帧秒':last?last.time:null,
          '★ 差毫秒':last?Math.round((last.time-dur)*1000):null,
          '★ 拒绝条件成立':last?String(last.time>=dur-0.001):null,
          播放头:tl.currentTime,
          选中轨道:tl.selectedTrackId,
          '★ 关键帧数':kfs.length,
          '★ 关键帧时间毫秒':kfs.map(k=>Math.round(k.time*1000)),
          '★ 全局最大关键帧毫秒':Math.round(tl.tracks.reduce((a,x)=>
            x.keyframes.reduce((b,k)=>Math.max(b,k.time),a),0)*1000),
          相机锁定:cam?!!cam.locked:null,
          跟随目标:cam&&cam.camera?cam.camera.followTargetId||null:null,
          presetError:(tl.cameraMotionPreset.error||{}).message||null};}"""

# ★ 扫描两处提示 ＋ **区分面板内/外** ＋ 绿色成功状态 ＋ 扫描器自检
SCAN = """()=>{
  // ★ 判「用户看得见」必须读**计算样式**（821 教训：
  //   `visibility:hidden` 的元素**在 DOM 里、有尺寸、但用户看不见**，
  //   「跳过零尺寸元素」的过滤抓不到它）
  const visible=(e)=>{const r=e.getBoundingClientRect();
    if(r.width===0&&r.height===0)return false;
    const cs=getComputedStyle(e);
    return cs.visibility!=='hidden'&&cs.visibility!=='collapse'
      && cs.display!=='none' && Number(cs.opacity||'1')>0;};
  const inPanel=(e)=>!!e.closest('[data-director-camera-preset-panel]');
  const scan=()=>{const out=[];
    for(const e of Array.from(
        document.querySelectorAll('[data-director-camera-preset-error]'))){
      if(!visible(e))continue;
      out.push({通道:'预设错误提示',
                文本:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,60),
                在预设面板内部:inPanel(e)});}
    for(const e of Array.from(
        document.querySelectorAll('[data-director-camera-preset-status]'))){
      if(!visible(e))continue;
      out.push({通道:'预设成功状态',
                文本:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,60),
                模式:e.getAttribute('data-mode'),
                预设:e.getAttribute('data-preset'),
                本次生成关键帧数:Number(e.getAttribute('data-keyframe-count')),
                开始毫秒:Math.round(Number(e.getAttribute('data-start-time'))*1000),
                结束毫秒:Math.round(Number(e.getAttribute('data-end-time'))*1000),
                在预设面板内部:inPanel(e)});}
    return out;};
  // ★ 扫描器自检：**两个通道各注入一个探针**，都必须扫得到
  const PROBES=[['data-director-camera-preset-error','扫描器探针822a'],
                ['data-director-camera-preset-status','扫描器探针822b']];
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
  const fld=document.querySelector('[data-director-time-field="duration"]');
  const panel=document.querySelector('[data-director-camera-preset-panel]');
  return {'★ 所有可见读数':scan(),
          面板开着:!!panel,
          面板mode:panel?panel.getAttribute('data-director-camera-preset-panel-mode'):null,
          开关按钮disabled:trig?trig.disabled===true:null,
          '★ 时长框显示':fld?fld.value:null,
          '★ 时长框单位':fld?fld.getAttribute('data-director-time-field-unit'):null,
          '★ DOM 时长毫秒':fld?
            Math.round(Number(fld.getAttribute('data-director-timeline-duration'))*1000):null,
          '★ 扫描器自检':selfTest>0,
          '★ 探针被扫到几个':selfTest};}"""

TRIG = "[data-director-camera-preset-trigger]"
MODE_APPEND = '[data-director-camera-preset-mode-option="append"]'


def rd(pg, tag):
    s, c = pg.evaluate(GEOM), pg.evaluate(SCAN)
    vis = c["★ 所有可见读数"]
    return {"时刻": tag, "store": s, "dom": c, "所有可见读数": vis,
            "★ 面板外的读数": [x for x in vis if not x["在预设面板内部"]],
            "★ 面板内的读数": [x for x in vis if x["在预设面板内部"]],
            "★ 错误提示": [x for x in vis if x["通道"] == "预设错误提示"],
            "★ 成功状态": [x for x in vis if x["通道"] == "预设成功状态"]}


def click(pg, sel):
    el = pg.query_selector(sel)
    if not el:
        return "not-found"
    if el.is_disabled():
        return "disabled"
    el.click()
    return "clicked"


def set_ms(pg, raw):
    """往时长框写一个字符串并提交。

    ★ ★ 探针返工（第一版）：**不能**用 `keyboard.type` 逐字符敲 ——
    时长框 `onChange` 里**立刻 commit**，而 `useEffect([value])` 又把 draft
    重置成 `format(value)` ⟹ ★ 连续键入时**互相打架**，第一版读到的
    `900.005` 是**光标落点 + 交错提交**的产物、**不是产品行为**
    （809/810/821 的老坑：**读数对不上时先怀疑自己**）。
    改成：`Meta+A` 全选 → **`fill()` 一次性**提交，只提交一次、不留中间态。
    ★ `raw` 故意传字符串：只有传字符串才测得到「非整数毫秒」那条路。"""
    fld = pg.query_selector('[data-director-time-field="duration"]')
    if not fld:
        return "not-found"
    fld.click()
    pg.wait_for_timeout(140)
    pg.keyboard.press("Meta+A")
    pg.wait_for_timeout(140)
    fld.fill(str(raw))
    pg.wait_for_timeout(650)
    s = pg.evaluate(GEOM)
    # ★ ★ 必须记**失焦之前**的显示值：`onBlur` 里 `setDraft(format(value))`
    #   会把框重置成真实值 ⟹ ★ 只要之后碰了别处（重开面板就算碰了），
    #   「用户敲的数其实被 clamp 拒绝了」这件事就被**抹掉了**。
    #   第二版漏了这一行 ⟹ 臂「显示 vs 真值」被 blur 掩盖、判据差点失真。
    return {"写入": str(raw), "★ store 总时长秒": s["总时长秒"],
            "★ store 总时长毫秒": s["★ 总时长毫秒"],
            "★ store 总时长精确毫秒": s["★ 总时长精确毫秒"],
            "★ 框里显示(失焦前)": pg.eval_on_selector(
                '[data-director-time-field="duration"]', "e=>e.value"),
            "★ 框里显示(此刻已失焦)": pg.eval_on_selector(
                '[data-director-time-field="duration"]',
                "e=>document.activeElement===e?null:e.value"),
            "★ 面板还开着吗": pg.evaluate(
                "()=>!!document.querySelector"
                "('[data-director-camera-preset-panel]')")}


def reopen_append(pg):
    """★ 真实用户路径：面板被时长框点关之后，得**重新打开 + 重选模式**。"""
    opened = pg.evaluate("()=>!document.querySelector("
                         "'[data-director-camera-preset-panel]')")
    if opened:
        click(pg, TRIG)
        pg.wait_for_timeout(650)
    sel = click(pg, MODE_APPEND)
    pg.wait_for_timeout(450)
    return {"★ 面板是自己关的所以重开": bool(opened), "重选append": sel,
            "★ 现在面板mode": pg.evaluate(
                "()=>{const p=document.querySelector("
                "'[data-director-camera-preset-panel]');"
                "return p?p.getAttribute('data-director-camera-preset-panel-mode'):null;}")}


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
        pg.evaluate("""()=>{const S=window.__director_store.getState();
          const t=S.timeline.tracks.find(x=>x.kind==='camera');
          if(t)S.selectTimelineTrack(t.id);}""")
        pg.wait_for_timeout(700)

        out = {"读取": [], "操作": {}}
        out["读取"].append(rd(pg, "序0·选中相机轨道、面板还没开"))
        out["操作"]["起点时长框"] = pg.evaluate(
            """()=>{const e=document.querySelector(
                 '[data-director-time-field="duration"]');
               return e?{显示:e.value,单位:e.getAttribute(
                 'data-director-time-field-unit')}:null;}""")

        out["操作"]["开面板"] = click(pg, TRIG)
        pg.wait_for_timeout(700)
        out["读取"].append(rd(pg, "序0b·面板开了、默认是「替换运镜」"))
        out["操作"]["切到追加运镜"] = click(pg, MODE_APPEND)
        pg.wait_for_timeout(500)
        out["读取"].append(rd(pg, "序0c·已切到「追加运镜」、还没按预设"))

        # ── 臂 1：分支序3 拒绝（总时长 8000ms == 末关键帧 8000ms）
        out["操作"]["臂1 按预设(append/orbit)"] = click(
            pg, '[data-director-camera-preset-option="orbit"]')
        pg.wait_for_timeout(850)
        out["读取"].append(rd(pg, "臂1·append 被拒「没有可追加的时长」"))

        # ── 臂 2：★ 点时长框 ⟹ **面板被点关**
        out["操作"]["臂2 点时长框"] = set_ms(pg, 8000)
        out["读取"].append(rd(pg, "臂2·★ 点时长框之后 ⟹ 面板没了"))

        # ── 臂 3：★ +1ms ⟹ **仍拒**
        out["操作"]["臂3 时长设为8001"] = set_ms(pg, 8001)
        out["操作"]["臂3 重开面板+选append"] = reopen_append(pg)
        out["读取"].append(rd(pg, "臂3·+1ms、重开面板之后"))
        out["操作"]["臂3 按预设(append/half-arc)"] = click(
            pg, '[data-director-camera-preset-option="half-arc"]')
        pg.wait_for_timeout(850)
        out["读取"].append(rd(pg, "臂3b·+1ms 之后再按 ⟹ ★ 仍被拒"))

        # ── 臂 4：★ ms 框敲**非整数毫秒**「8000.5」
        #   ★ 我原本的假设是「非整数毫秒能落进容差内部、从而绕过 1ms」
        #   ⟹ **实测是错的**：8.0005 - 0.001 = 7.9995，而末关键帧是 8.0
        #   ⟹ `8.0 >= 7.9995` 成立 ⟹ **仍然被拒**。
        #   ⟹ ★ 但另有一条读数浮出来：框里显示「8001」而 store 真值是 8.0005
        out["操作"]["臂4 时长写入8000.5"] = set_ms(pg, "8000.5")
        out["操作"]["臂4 重开面板+选append"] = reopen_append(pg)
        out["读取"].append(rd(pg, "臂4·★ 敲了 8000.5 之后 ⟹ 显示与真值"))
        out["操作"]["臂4 按预设(append/orbit)"] = click(
            pg, '[data-director-camera-preset-option="orbit"]')
        pg.wait_for_timeout(850)
        out["读取"].append(rd(pg, "臂4b·8000.5 之后按 ⟹ ★ 仍被拒"))

        # ── 臂 5：★★ **矛盾句** —— 此刻 append 仍被拒，立刻设跟随目标
        #   ★★ 必须在**仍拒**的状态下做：一旦有一次成功，error 就被清成 null
        cam_obj = pg.evaluate("""()=>{const S=window.__director_store.getState();
          const t=S.timeline.tracks.find(x=>x.kind==='camera');
          return t?t.objectId:null;}""")
        out["操作"]["相机对象"] = cam_obj
        out["操作"]["臂5 此刻面板开着"] = pg.evaluate(
            "()=>!!document.querySelector('[data-director-camera-preset-panel]')")
        if cam_obj:
            out["操作"]["臂5 设跟随目标"] = pg.evaluate(
                """(o)=>{const S=window.__director_store.getState();
                  const other=S.objects.find(x=>x.id!==o&&!x.camera);
                  if(!other)return null;
                  S.updateCamera(o,{followTargetId:other.id});
                  return other.id;}""", cam_obj)
        pg.wait_for_timeout(850)
        out["读取"].append(rd(pg, "臂5·★ 设了跟随目标 ⟹ 两句错误提示同时挂着"))

        # ── 臂 6：★ 拉长时长 ⟹ 条件已解除，**旧提示是否还在**
        out["操作"]["臂6 清跟随"] = pg.evaluate(
            """(o)=>{const S=window.__director_store.getState();
              S.updateCamera(o,{followTargetId:null});return true;}""", cam_obj)
        pg.wait_for_timeout(600)
        out["操作"]["臂6 时长设为9000"] = set_ms(pg, 9000)
        out["操作"]["臂6 重开面板+选append"] = reopen_append(pg)
        out["读取"].append(rd(pg, "臂6·★ 拉长时长之后 ⟹ 旧提示应仍在"))

        # ── 臂 7：★ 此刻 append **已经可行**，但那句「没有可追加的时长」还挂着
        out["操作"]["臂7 按预设(append/orbit)"] = click(
            pg, '[data-director-camera-preset-option="orbit"]')
        pg.wait_for_timeout(900)
        out["读取"].append(rd(pg, "臂7·按一次预设 ⟹ ★ 提示才清、且这次成功"))

        # ── 臂 8：★★ **成功状态 + 禁止提示并存**
        #   ★ `:1468` 的渲染是 **error 优先于 application** ⟹ 所以必须
        #   **一次失败都不插**、成功之后**直接**设跟随，
        #   才能让「绿色成功状态」和「面板外禁止提示」同屏。
        if cam_obj:
            out["操作"]["臂8 设跟随目标"] = pg.evaluate(
                """(o)=>{const S=window.__director_store.getState();
                  const other=S.objects.find(x=>x.id!==o&&!x.camera);
                  if(!other)return null;
                  S.updateCamera(o,{followTargetId:other.id});
                  return other.id;}""", cam_obj)
        pg.wait_for_timeout(850)
        out["读取"].append(rd(pg, "臂8·★★ 成功之后设跟随 ⟹ 绿字 + 禁止提示同屏"))
        out["操作"]["臂8 这时还能不能打开面板"] = pg.evaluate(
            """()=>{const t=document.querySelector(
                 '[data-director-camera-preset-trigger]');
               return {按钮disabled:t?t.disabled===true:null,
                       面板开着:!!document.querySelector(
                         '[data-director-camera-preset-panel]')};}""")
        if cam_obj:
            out["操作"]["臂8 清跟随"] = pg.evaluate(
                """(o)=>{const S=window.__director_store.getState();
                  S.updateCamera(o,{followTargetId:null});return true;}""",
                cam_obj)
        pg.wait_for_timeout(700)

        # ── 臂 9：★★ **没有终点** —— 成功之后末关键帧被顶到新时长，
        #   ⟹ 第二次 append **又变拒**
        out["操作"]["臂9 再按一次预设(append/orbit)"] = click(
            pg, '[data-director-camera-preset-option="orbit"]')
        pg.wait_for_timeout(900)
        out["读取"].append(rd(pg, "臂9·★★ 紧接着第二次 append ⟹ 又被拒"))

        # ── 臂 10：★★ 追加成功之后**总时长调不回去**（被关键帧顶住）
        #   ★ 判据看「失焦前显示 8000 / store 真值 9000」
        out["操作"]["臂10 时长试图设回8000"] = set_ms(pg, 8000)
        out["读取"].append(rd(pg, "臂10·★ 追加后把总时长设回 8000 ⟹ 显示 vs 真值"))
        out["操作"]["臂10 重开面板+选append"] = reopen_append(pg)
        out["读取"].append(rd(pg, "臂10b·★ 失焦之后框里变成了什么"))

        # ── 臂 11：★ 被顶住的时长 ⟹ append 依然被拒
        out["操作"]["臂11 按预设(append/orbit)"] = click(
            pg, '[data-director-camera-preset-option="orbit"]')
        pg.wait_for_timeout(900)
        out["读取"].append(rd(pg, "臂11·★ 时长被关键帧顶住之后 append 仍被拒"))

        # ── 臂 12：★ 关面板重开 ⟹ 模式还在不在、提示还在不在
        pg.evaluate("""()=>{const p=document.querySelector(
          '[data-director-camera-preset-panel]');
          if(p){const b=p.querySelector('button[aria-label]');if(b)b.click();}}""")
        pg.wait_for_timeout(550)
        out["操作"]["臂12 关面板后还在吗"] = pg.evaluate(
            "()=>!!document.querySelector('[data-director-camera-preset-panel]')")
        out["操作"]["臂12 重开面板"] = click(pg, TRIG)
        pg.wait_for_timeout(650)
        out["读取"].append(rd(pg, "臂12·关掉再打开面板之后"))

        return out
    finally:
        pg.close()


def main():
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        out = run(br)
        br.close()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print("读数时刻数:", len(out.get("读取", [])))


if __name__ == "__main__":
    main()