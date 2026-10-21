#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 824 验收探针 —— 「TV Director」入口：源站在**画布底部**，clone 在**顶部**

## ★ 这批做了什么

**测量**（源站侧，无头 + 登录态）：
- 源站画布**底部中间**有一条工具条，8 枚按钮，可及名逐字：
  添加节点／移动／素材库／**角色造型室**／生成历史／快捷键／教程／**TV Director**
- 「TV Director」是 **48×48 的青色渐变球 + 右侧文字**，点位 (955,889,48,48)
- ★ 点它打开的是**右侧「新对话」AI 抽屉**，**不是导演台**
  （URL 不变、画布节点数不变、抽屉标题逐字「新对话」）

**实施**（clone 侧）：
- clone 的 `AgentDrawer` **标题逐字就是「新对话」** ⟹ 面板本来就有
- ★ 但 clone 的入口在**顶部导航**（文案「Agent」）⟹ 用户在画布上找不到
- ⟹ ★★ **补一枚与源站同位同形的底部胶囊**（顶部那枚不能删：它被
  batch723/737/649/280 的 runtime-audit 钉住）
- ★ 抽屉开着时胶囊**消失**（与源站截图一致）

## ★ 硬约束

1. ★ **零 store 写调用**（验收器正则扫源码自证）
2. ★ **真实鼠标点击**（823 的教训：`select_option` 那种程序化路径不算纯 UI）
3. ★ 判据只认**绝对几何**与 **DOM 可见读数**
"""
import json
import os
import pathlib
import sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent /
                       "liblib-canvas-batch774-2026-10-01" / "probes"))
import dbg774a as A  # noqa: E402

OUT = pathlib.Path(os.environ.get("VB824_OUT") or
                   (HERE.parent / "raw" / "vb824b.json"))

# ★★ 唯一的 store 只读入口
RO = """()=>{const S=window.__libtv_store.getState();
  const c=(S.canvases||[]).find(x=>x.id===S.activeCanvasId)||null;
  return {'★ 节点数':((c&&c.nodes)||[]).length,
          '★ 边数':((c&&c.edges)||[]).length,
          '★ 选中节点':(S.selectedNodeIds||[]).slice()};}"""

# ★ 底部工具条：取**视口底部**那一簇（★ 823 的教训：视口高度不同，
#   坐标过滤要跟着视口走，不能写死 y<700）
TOOLBAR = """()=>{
  const visible=(e)=>{const r=e.getBoundingClientRect();
    if(r.width===0&&r.height===0)return false;
    const cs=getComputedStyle(e);
    return cs.visibility!=='hidden'&&cs.display!=='none'
      && Number(cs.opacity||'1')>0;};
  const H=window.innerHeight;
  const out=[];
  for(const e of Array.from(document.querySelectorAll(
      'button[aria-label],button[title]'))){
    if(!visible(e))continue;
    const r=e.getBoundingClientRect();
    if(r.y < H-140)continue;                 // ★ 跟着视口高度走
    if(r.width>200)continue;
    out.push({aria:e.getAttribute('aria-label')||'',
              title:e.getAttribute('title')||'',
              文本:(e.textContent||'').trim().replace(/\\s+/g,' ').slice(0,20),
              w:Math.round(r.width),h:Math.round(r.height),
              x:Math.round(r.x),y:Math.round(r.y)});}
  return {视口高:window.innerHeight, 视口宽:window.innerWidth, 底部按钮:out};}"""

# ★ AgentDrawer 的可见读数
DRAWER = """()=>{
  const visible=(e)=>{const r=e.getBoundingClientRect();
    if(r.width===0&&r.height===0)return false;
    const cs=getComputedStyle(e);
    return cs.visibility!=='hidden'&&cs.display!=='none'
      && Number(cs.opacity||'1')>0;};
  const txt=[];
  for(const e of Array.from(document.querySelectorAll('h1,h2,h3,p,span,button'))){
    if(!visible(e))continue;
    const t=(e.textContent||'').trim().replace(/\\s+/g,' ');
    if(!t||t.length>44)continue;
    const r=e.getBoundingClientRect();
    if(r.width<8||r.height<8)continue;
    txt.push(t);}
  const uniq=[]; for(const t of txt) if(uniq.indexOf(t)<0) uniq.push(t);
  return {文本:uniq.slice(0,50)};}"""

# ★★ Batch 824 补测：源站那枚球**不在药丸里**（药丸结束后隔 14px 单独挂一枚），
#   而且文字是 `width:0 + opacity:0` ⟹ 视觉上没有字。
#   ⟹ 这里量三件事：① 球与药丸的**相对几何** ② 球与药丸按钮行的**同轴**
#   ③ 文字的**藏法**（宽 0 + 透明）
ORB = """()=>{
  const rect=(e)=>{if(!e)return null;const r=e.getBoundingClientRect();
    return {x:+r.x.toFixed(2),y:+r.y.toFixed(2),
            w:+r.width.toFixed(2),h:+r.height.toFixed(2),
            cx:+(r.x+r.width/2).toFixed(2),cy:+(r.y+r.height/2).toFixed(2)};};
  const sty=(e)=>{if(!e)return null;const cs=getComputedStyle(e);
    return {bg:cs.backgroundColor, border:cs.border, radius:cs.borderRadius,
            padding:cs.padding, opacity:cs.opacity, width:cs.width,
            position:cs.position, overflow:cs.overflow,
            text:(e.textContent||'').trim().replace(/\\s+/g,' ')};};
  const orb=document.querySelector('button[aria-label="TV Director"]');
  if(!orb)return {存在:false};
  // ★ 绝对定位元素的 offsetParent 就是那个药丸容器
  const pill=orb.offsetParent;
  // ★ 药丸里最右一枚按钮（「教程」）⟹ 用它校同轴
  const help=document.querySelector('button[aria-label="教程"]');
  // ★ 球体（28×28）
  const ball=orb.querySelector('[data-testid="canvas-agent-orb-entry"]');
  // ★★ 球**本体**（真正画渐变的那一层）⟹ ★ 没有它就只是一只空圆钮
  const core=ball?(ball.firstElementChild||null):null;
  // ★ 承载「TV Director」文字的元素（最外层那个 span）
  let txtEl=null;
  for(const e of orb.querySelectorAll('span')){
    if((e.textContent||'').trim()==='TV Director'){txtEl=e;break;}}
  const o=rect(orb), p=rect(pill), hl=rect(help);
  return {存在:true,
    球:o, 球样式:sty(orb),
    药丸:p, 药丸样式:sty(pill),
    教程按钮:hl,
    球体:rect(ball), 球体样式:sty(ball),
    球芯:rect(core), 球芯样式:core?{bgImage:getComputedStyle(core).backgroundImage,
      boxShadow:getComputedStyle(core).boxShadow,
      radius:getComputedStyle(core).borderRadius,
      w:getComputedStyle(core).width,h:getComputedStyle(core).height}:null,
    文字元素:rect(txtEl), 文字样式:sty(txtEl),
    间隙: (o&&p)? +(o.x-(p.x+p.w)).toFixed(2):null,
    按钮到球间隙: (o&&hl)? +(o.x-(hl.x+hl.w)).toFixed(2):null,
    同轴偏差: (o&&hl)? +(o.cy-hl.cy).toFixed(2):null,
    药丸是否包住球: (o&&p)? (o.x>=p.x-0.5 && o.x+o.w<=p.x+p.w+0.5):null,
    球在药丸右侧: (o&&p)? (o.x>=p.x+p.w-0.5):null,
    offsetParent是药丸: !!(pill&&pill!==document.body),
  };}"""


def real_click(pg, sel):
    el = pg.query_selector(sel)
    if not el:
        return {"结果": "not-found", "选择器": sel}
    try:
        if el.is_disabled():
            return {"结果": "disabled", "选择器": sel}
        bb = el.bounding_box()
        pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
        return {"结果": "clicked", "选择器": sel, "矩形": bb}
    except Exception as exc:                                    # noqa: BLE001
        return {"结果": "click-error", "详情": str(exc)[:120]}


def run(b):
    out = {"步骤": [], "操作": {}}
    pg = b.new_page()
    pg.set_default_timeout(25000)
    try:
        pg.goto(A.BASE, wait_until="domcontentloaded")
        pg.wait_for_timeout(3200)

        # ── B0 起点：底部工具条上有没有「TV Director」
        tb0 = pg.evaluate(TOOLBAR)
        out["步骤"].append({
            "步骤": "B0·★ 起点：画布底部工具条上有几枚按钮、有没有「TV Director」",
            "读数": tb0,
            "★ 球几何": pg.evaluate(ORB),
            "★ 有 TV Director 吗": any(
                d["aria"] == "TV Director" for d in tb0["底部按钮"])})

        # ── B1 ★★ 真实鼠标点那枚胶囊
        cap = pg.query_selector('button[aria-label="TV Director"]')
        out["操作"]["B1 胶囊存在"] = bool(cap)
        r1 = real_click(pg, 'button[aria-label="TV Director"]')
        out["操作"]["B1 点击"] = r1
        pg.wait_for_timeout(1500)
        dr = pg.evaluate(DRAWER)
        tb1 = pg.evaluate(TOOLBAR)
        out["步骤"].append({
            "步骤": "B1·★★ 点胶囊 ⟹ 抽屉打开了吗",
            "★ 点击": r1,
            "★ 抽屉可见文本": dr["文本"],
            "★ 抽屉开着": any(t in dr["文本"] for t in ("新对话", "TV Director")),
            "★ 底部工具条还有 TV Director 吗": any(
                d["aria"] == "TV Director" for d in tb1["底部按钮"]),
            "★ 节点数（不该变）": pg.evaluate(RO)["★ 节点数"]})

        # ── B2 ★ 抽屉开着时，胶囊应当**消失**（与源站截图一致）
        out["步骤"].append({
            "步骤": "B2·★ 抽屉开着时底部胶囊**应当消失**",
            "★ 底部按钮": tb1["底部按钮"],
            "★ 还有 TV Director 吗": any(
                d["aria"] == "TV Director" for d in tb1["底部按钮"])})

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
    print("步数", len(out.get("步骤", [])))


if __name__ == "__main__":
    main()
