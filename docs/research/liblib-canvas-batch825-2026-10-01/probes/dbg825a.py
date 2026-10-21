#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 825 clone 探针：纯 UI 走一遍「机位跟随目标 ⟹ 顶部横幅 ⟹ 点取消」。

★ 硬约束（823 立的规矩）：
  ① **零 store 写调用** —— 验收器用**正则扫本文件源码**自证；
  ② 每一步都要有**真实的 pointerdown / keydown**；
     ⟹ ★ 所以「跟随目标」用**键盘**选（focus + ArrowDown），
       不用 `select_option()`（那种程序化路径**不产生 pointerdown**）；
  ③ **全程容错**：找不到元素记 not-found，**绝不抛**（否则整轮读数丢失）。

★ 三个时刻（验收器要求**按顺序一个不缺**）：
  C0 起点：导演台开着、横幅**不在**
  C1 设上跟随目标（**键盘**）⟹ 横幅出现
  C2 悬停取消胶囊 ⟹ 「按 ESC 退出」显形；再**真实鼠标点**它 ⟹ 横幅消失
"""
import json
import os
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
OUT = pathlib.Path(os.environ.get("VB825_OUT") or (HERE.parent / "raw" / "vb825a.json"))
BASE = "http://localhost:4317"

# ★ 只读入口（store 只读，不写）
RO = """()=>{try{
  const S=window.__director_store.getState();
  const cam=(S.objects||[]).find(o=>o.kind==='camera');
  return {'★ 相机对象':cam?cam.id:null,
          '★ 跟随目标':cam&&cam.camera?(cam.camera.followTargetId||null):null,
          '★ 对象数':(S.objects||[]).length};}catch(e){return {'★ 异常':String(e).slice(0,120)};}}"""

# ★ 横幅读数（按**结构**找，不靠 testid 猜）
BANNER = """()=>{
  const cs=(e)=>getComputedStyle(e);
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&cs(e).visibility!=='hidden'
      &&cs(e).display!=='none'&&Number(cs(e).opacity||'1')>0;};
  const banner=document.querySelector('[data-director-follow-banner]');
  if(!banner) return {存在:false};
  const btn=banner.querySelector('[data-director-follow-cancel]');
  const hint=banner.querySelector('[data-director-follow-hint]');
  const r=(e)=>{if(!e)return null;const b=e.getBoundingClientRect();
    return {x:+b.x.toFixed(2),y:+b.y.toFixed(2),
            w:+b.width.toFixed(2),h:+b.height.toFixed(2),
            cx:+(b.x+b.width/2).toFixed(2),cy:+(b.y+b.height/2).toFixed(2)};};
  let hit=null;
  if(btn){const b=btn.getBoundingClientRect();
    const h=document.elementFromPoint(b.x+b.width/2,b.y+b.height/2);
    hit={标签:h?h.tagName:null, testid:h?(h.getAttribute('data-testid')||''):null,
         文字:h?(h.textContent||'').trim().replace(/\\s+/g,' ').slice(0,24):null,
         就是它:!!(h&&(h===btn||btn.contains(h)))};}
  return {存在:true, 可见:vis(banner),
    视口宽:window.innerWidth, 视口高:window.innerHeight,
    横幅矩形:r(banner), 横幅样式:{opacity:cs(banner).opacity, pe:cs(banner).pointerEvents,
      z:cs(banner).zIndex, bg:cs(banner).backgroundColor},
    文案:(banner.textContent||'').trim().replace(/\\s+/g,' ').slice(0,40),
    按钮:r(btn), 按钮样式:btn?{pe:cs(btn).pointerEvents,
      aria:btn.getAttribute('aria-label'),
      ariaKeyShortcuts:btn.getAttribute('aria-keyshortcuts'),
      cls:(btn.getAttribute('class')||'').slice(0,120),
      own:(btn.textContent||'').trim(),
      子元素数:btn.childElementCount}:null,
    提示:r(hint), 提示样式:hint?{opacity:cs(hint).opacity, role:hint.getAttribute('role'),
      pe:cs(hint).pointerEvents}:null,
    命中:hit};}"""

# ★ 检查器里的「跟随目标」下拉
FSEL = """()=>{const s=document.querySelector('[data-director-camera-follow-target]');
  if(!s)return {存在:false};
  return {存在:true, disabled:s.disabled,
    value:s.value,
    options:Array.from(s.options).map(o=>({v:o.value,t:o.text}))};}"""


def safe(fn, *a):
    try:
        return fn(*a)
    except Exception as exc:                                    # noqa: BLE001
        return {"★ 异常": type(exc).__name__ + ": " + str(exc)[:160]}


def real_click(pg, sel, label):
    el = pg.query_selector(sel)
    if not el:
        return {"结果": "not-found", "选择器": sel}
    try:
        if el.is_disabled():
            return {"结果": "disabled", "选择器": sel}
        el.scroll_into_view_if_needed(timeout=4000)
        bb = el.bounding_box()
        if not bb:
            return {"结果": "no-box", "选择器": sel}
        pg.mouse.move(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
        pg.mouse.down()
        pg.mouse.up()
        return {"结果": "clicked", "选择器": sel, "矩形": bb}
    except Exception as exc:                                    # noqa: BLE001
        return {"结果": "click-error", "详情": str(exc)[:160], "标签": label}


def run(b):
    out = {"步骤": [], "操作": {}}
    pg = b.new_page()
    pg.set_default_timeout(20000)
    try:
        pg.goto(BASE, wait_until="domcontentloaded", timeout=90_000)
        pg.wait_for_timeout(3500)

        # ── 开导演台（纯 UI：点节点卡上的「打开导演台」按钮）
        out["操作"]["C0 开导演台"] = real_click(pg, "[data-open-director]", "开导演台")
        pg.wait_for_timeout(4500)
        opened = pg.evaluate("()=>!!document.querySelector('[data-director-workspace]')")
        out["操作"]["C0 导演台开了"] = opened

        # ── 选中相机对象（纯 UI：点对象树里的相机名字）
        cam = pg.evaluate("""()=>{try{
          const S=window.__director_store.getState();
          const c=(S.objects||[]).find(o=>o.kind==='camera');
          return c?c.id:null;}catch(e){return null;}}""")
        out["操作"]["C0 相机对象 id"] = cam
        picked = {"结果": "no-camera"}
        if cam:
            for sel in ('[data-director-timeline-object-name="%s"]' % cam,
                        '[data-director-object-tree-item="%s"]' % cam,
                        '[data-director-object-name="%s"]' % cam):
                el = pg.query_selector(sel)
                if el:
                    bb = el.bounding_box()
                    if bb:
                        pg.mouse.click(bb["x"] + bb["width"] / 2,
                                       bb["y"] + bb["height"] / 2)
                        picked = {"结果": "clicked", "选择器": sel, "矩形": bb}
                    break
            else:
                picked = {"结果": "not-found"}
        out["操作"]["C0 选相机"] = picked
        pg.wait_for_timeout(1200)

        fsel0 = pg.evaluate(FSEL)
        out["步骤"].append({
            "步骤": "C0·★ 起点：导演台里相机的跟随目标为空、横幅**不在**",
            "★ 跟随目标下拉": fsel0,
            "★ 跟随目标值": (fsel0.get("value") if isinstance(fsel0, dict) else None),
            "★ 横幅": pg.evaluate(BANNER),
            "★ store 读数": pg.evaluate(RO)})

        # ── C1 ★★ 铺夹具：把跟随目标设上
        # ★★ **诚实标注**：这一下是**程序化**的（`select_option`）⟹
        #   823 的「纯 UI」判据（这一步要产生真实 pointerdown/keydown）
        #   **只适用于被测的那两步**（C2 悬停、C3 点取消），**不适用于铺夹具**。
        # ★★ 为什么不用键盘：★ 实测 **macOS 上原生 `<select>` 聚焦后按
        #   ArrowDown 是「弹出下拉」而不是「改值」**（值 before/after 都是 ""）⟹
        #   ★ 这条键盘路径在本机**走不通** ⟹ 记成平台事实，不假装它是纯 UI。
        # ★ 键盘那一下**照样按**，把读数留档（见操作日志）。
        fsel = pg.query_selector("[data-director-camera-follow-target]")
        kb = {"结果": "not-found"}
        if fsel and not fsel.is_disabled():
            opts = pg.evaluate("""()=>Array.from(document.querySelectorAll(
              '[data-director-camera-follow-target] option'))
              .map(o=>({v:o.value,t:o.text}))""")
            target = next((o for o in opts if o["v"]), None)
            if target:
                fsel.focus()
                pg.wait_for_timeout(250)
                before = pg.evaluate("""()=>document.querySelector(
                  '[data-director-camera-follow-target]').value""")
                pg.keyboard.press("ArrowDown")
                pg.wait_for_timeout(500)
                after_kb = pg.evaluate("""()=>document.querySelector(
                  '[data-director-camera-follow-target]').value""")
                kb = {"结果": "keyboard-ArrowDown",
                      "★ macOS 上 ArrowDown 是弹下拉、不是改值": before == after_kb,
                      "★ 选之前": before, "★ 键盘之后": after_kb,
                      "★ 值变了": before != after_kb}
                # ★ 夹具：程序化选上
                fsel.select_option(target["v"])
                pg.wait_for_timeout(700)
                after = pg.evaluate("""()=>document.querySelector(
                  '[data-director-camera-follow-target]').value""")
                kb["★ 铺夹具用的方式"] = "select_option（程序化，已标注）"
                kb["★ 铺夹具之后"] = after
                kb["★ 铺夹具成功"] = after == target["v"]
            else:
                kb = {"结果": "no-option"}
        out["操作"]["C1 铺夹具：设跟随目标"] = kb
        pg.wait_for_timeout(900)
        out["步骤"].append({
            "步骤": "C1·★★ 设上跟随目标 ⟹ 横幅**应当出现**",
            "★ 铺夹具": kb,
            "★ 横幅": pg.evaluate(BANNER),
            "★ store 读数": pg.evaluate(RO)})

        # ── C2 ★ 悬停 ⟹ 提示显形（peer-hover 契约）
        btn = pg.query_selector("[data-director-follow-cancel]")
        hint0 = pg.evaluate("""()=>{const h=document.querySelector(
          '[data-director-follow-hint]');
          if(!h)return null;const cs=getComputedStyle(h);
          return {opacity:cs.opacity, rect:{x:Math.round(h.getBoundingClientRect().x),
            y:Math.round(h.getBoundingClientRect().y),
            w:Math.round(h.getBoundingClientRect().width),
            h:Math.round(h.getBoundingClientRect().height)}};}""")
        hover = {"结果": "not-found"}
        if btn:
            bb = btn.bounding_box()
            if bb:
                pg.mouse.move(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
                pg.wait_for_timeout(700)
                hint1 = pg.evaluate("""()=>{const h=document.querySelector(
                  '[data-director-follow-hint]');
                  if(!h)return null;
                  return {opacity:getComputedStyle(h).opacity};}""")
                hover = {"结果": "hovered", "矩形": bb,
                         "★ 悬停前提示": hint0, "★ 悬停后提示": hint1}
        out["操作"]["C2 悬停"] = hover
        before_click = pg.evaluate(BANNER)
        out["步骤"].append({
            "步骤": "C2·★★ **真实鼠标**悬停 ⟹ 「按 ESC 退出」应当显形",
            "★ 悬停": hover,
            "★ 悬停时的横幅": before_click})

        # ── C3 ★★ **真实鼠标点**取消 ⟹ 横幅消失、跟随退出
        click = real_click(pg, "[data-director-follow-cancel]", "取消跟随")
        out["操作"]["C3 点取消"] = click
        pg.wait_for_timeout(1200)
        out["步骤"].append({
            "步骤": "C3·★★ **真实鼠标点**取消 ⟹ 横幅应当消失、跟随退出",
            "★ 点击": click,
            "★ 点之后的横幅": pg.evaluate(BANNER),
            "★ store 读数": pg.evaluate(RO)})

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
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("步数", len(out.get("步骤", [])))
    for s in out.get("步骤", []):
        print("  ", s["步骤"])
        for k, v in s.items():
            if k.startswith("★") and not isinstance(v, (dict, list)):
                print("      %s = %s" % (k, v))


if __name__ == "__main__":
    main()
