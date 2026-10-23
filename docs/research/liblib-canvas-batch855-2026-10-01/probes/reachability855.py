#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 855 附带：clone 的**「用户可达」普查**（为用户新要求服务）。

★ 用户新要求（2026-10-01）：
★ 「所有完成的克隆成果（"页面"）都必须通过克隆网站根目录"用户可达"，
★  并且文档中说明如何"可达"、用户可以如何进行交互测试」。

## ★ 本探针做什么

★ **只从根地址 `http://localhost:4317/`（不带任何参数）出发** ⟹ ⟹
★ 走**真实点击**（不调 store、不改 URL）⟹ ⟹ 验「从根能不能到达」，
★ 并把每条路径的**可交互元素**列出来 ⟹ ⟹ 供那份说明文档引用。

## ★ 普查的三条主干路径

| 路径 | 怎么点 | 落点 |
| --- | --- | --- |
| A | hover 画布上的「导演台」节点 ⟹ 点「打开导演台 →」 | 导演台（场景树／rail／时间轴） |
| B | 左栏「角色造型室」⟹ 「官方角色库」⟹ 点角色卡 ⟹ 「编辑角色」 | 角色大编辑器（脸部&身体／服装造型／音色音调 三段） |
| C | 底部工具条「资产管理」 | 资产管理面板 |

★ ★ **「这个入口没有 X」这类断言必须真的点一下才算数** ⟹ ⟹ 每条路径
★   都是**点完再读**，不靠「源码里有这个按钮」推断。

## 输出

  raw/reachability-855.json
  images/855reach_{01-root,02-director,03-studio,04-editor,05-assets}.png
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

# ★ 普查用的选择器（全部是 clone 自己带的数据属性 ⟹ ⟹ 不靠文案定位）
SEL_SIDEBAR = "[data-sidebar-btn]"
SEL_BOTTOM = "[data-bottom-tool]"          # 不存在就退回 aria-label
SEL_DIRECTOR_BTN = "[data-open-director]"
SEL_EDITOR = "[data-character-editor]"
SEL_ASSETS = "[data-asset-manager]"


def clean_portal(pg):
    pg.evaluate("() => { const p=document.querySelector('nextjs-portal'); if(p) p.remove(); }")


def open_root(pg):
    """★ **根地址、无参数**。"""
    pg.goto(BASE + "/", wait_until="domcontentloaded")
    pg.wait_for_timeout(3000)
    clean_portal(pg)
    pg.wait_for_function("() => Boolean(window.__libtv_store)", timeout=60_000)
    pg.wait_for_timeout(1200)


def box(pg, selector):
    return pg.evaluate("""(sel)=>{
      const e=document.querySelector(sel);
      if(!e)return null; const r=e.getBoundingClientRect();
      return {x:Math.round(r.x),y:Math.round(r.y),
              w:Math.round(r.width),h:Math.round(r.height)};}""", selector)


def click_sel(pg, selector, index=0):
    """★ 点第 index 个匹配元素（先 scrollIntoView ⟹ ⟹ 不点可视区外的）。"""
    loc = pg.locator(selector)
    if loc.count() <= index:
        return False
    el = loc.nth(index)
    try:
        el.scroll_into_view_if_needed(timeout=8000)
    except Exception:
        pass
    pg.wait_for_timeout(250)
    el.click(timeout=15000)
    pg.wait_for_timeout(900)
    return True


def click_attr(pg, selector, attr, value):
    """★ 按**属性值**精确匹配后点击（⟹ 不手打索引 ⟹ ⟹ 也不靠文案）。

    ★ ★ 左栏那枚「角色造型室」是**纯图标**按钮 ⟹ ⟹ `textContent` 是空的
    ★ ⟹ ⟹ 必须按 `aria-label`／`data-sidebar-btn` 这类**属性**定位。
    """
    n = pg.locator(selector).count()
    for i in range(n):
        el = pg.locator(selector).nth(i)
        if el.get_attribute(attr) == value:
            try:
                el.scroll_into_view_if_needed(timeout=8000)
            except Exception:
                pass
            pg.wait_for_timeout(250)
            el.click(timeout=15000)
            pg.wait_for_timeout(900)
            return True
    return False


def click_text(pg, selector, text):
    """★ 点第一个**文字正好等于** text 的元素（不手打索引 ⟹ ⟹ 不「定位元素别用 first」）。"""
    n = pg.locator(selector).count()
    for i in range(n):
        el = pg.locator(selector).nth(i)
        if (el.text_content() or "").strip() == text:
            try:
                el.scroll_into_view_if_needed(timeout=8000)
            except Exception:
                pass
            pg.wait_for_timeout(250)
            el.click(timeout=15000)
            pg.wait_for_timeout(900)
            return True
    return False


def shot(pg, name):
    p = SHOTS / ("855reach_%s.png" % name)
    p.parent.mkdir(parents=True, exist_ok=True)
    pg.screenshot(path=str(p))
    return p.name


def enumerate_root(pg):
    """★ 根页上的**可交互入口**清单（供文档写「有哪些地方可以点」）。"""
    return pg.evaluate(r"""()=>{
      const vis=(e)=>{const r=e.getBoundingClientRect();
        return r.width>0&&r.height>0;};
      const side=[...document.querySelectorAll('[data-sidebar-btn]')]
        .filter(vis).map(e=>({key:e.getAttribute('data-sidebar-btn'),
                              aria:e.getAttribute('aria-label')||'',
                              text:(e.textContent||'').trim().slice(0,20)}));
      const bottom=[...document.querySelectorAll('button[aria-label]')]
        .filter(e=>{const r=e.getBoundingClientRect();
          return vis(e)&&r.y>window.innerHeight-140;})
        .map(e=>({aria:e.getAttribute('aria-label')||'',
                  text:(e.textContent||'').trim().slice(0,20)}));
      const nodes=[...document.querySelectorAll('.react-flow__node')].filter(vis)
        .map(e=>({cls:e.className.split(' ').filter(c=>c.startsWith('react-flow__node-'))
                    .map(c=>c.replace('react-flow__node-',''))[0]||'',
                  text:(e.textContent||'').trim().replace(/\s+/g,' ').slice(0,40)}));
      return {左栏:side, 底部工具条:bottom, 画布节点数:nodes.length,
              画布节点:nodes,
              根URL:location.href};
    }""")


def director_path(pg):
    """★ 路径 A：根 ⟹ 导演台。"""
    out = {"步骤": []}
    node = pg.locator(".react-flow__node-script-execution").first
    try:
        node.scroll_into_view_if_needed(timeout=8000)
    except Exception:
        pass
    pg.wait_for_timeout(300)
    try:
        node.hover(timeout=8000)
        pg.wait_for_timeout(600)
    except Exception:
        pass
    out["步骤"].append("① 在根画布上 hover「导演台」节点")
    ok = click_sel(pg, SEL_DIRECTOR_BTN)
    out["步骤"].append("② 点节点里的「打开导演台 →」")
    pg.wait_for_timeout(5000)
    clean_portal(pg)
    out["点到了"] = ok
    out["导演台URL"] = pg.evaluate("()=>location.href")
    out["有场景树"] = pg.locator("[data-director-tree]").count() > 0
    out["对象树行数"] = pg.locator("[data-director-object-id]").count()
    out["组行数"] = pg.locator("[data-director-group-id]").count()
    out["rail项数"] = pg.locator("[data-director-rail-entry]").count()
    out["可交互元素数"] = pg.locator(
        "[data-director-tree] button, [data-director-rail-entry], "
        "[data-director-object-id] button").count()
    out["可交互元素"] = pg.evaluate(r"""()=>{
      const q=s=>[...document.querySelectorAll(s)];
      const items=[];
      q('[data-director-rail-entry]').forEach(e=>items.push(
        {类:'rail', 键:e.getAttribute('data-director-rail-entry'),
         文本:(e.textContent||'').trim().slice(0,16)}));
      q('[data-director-group-action]').forEach(e=>items.push(
        {类:'组动作', 键:e.getAttribute('data-director-group-action'),
         文本:(e.textContent||'').trim().slice(0,16)}));
      q('[data-director-object-id]').forEach(e=>items.push(
        {类:'对象行', 键:e.getAttribute('data-director-object-kind'),
         文本:(e.textContent||'').trim().slice(0,16)}));
      return items;}""")
    return out


def studio_path(pg):
    """★ 路径 B：根 ⟹ 角色造型室 ⟹ 角色大编辑器。"""
    out = {"步骤": []}
    ok_side = click_attr(pg, "button[aria-label]", "aria-label", "角色造型室")
    if not ok_side:
        ok_side = click_attr(pg, SEL_SIDEBAR, "data-sidebar-btn",
                             "character-library")
    out["步骤"].append("① 点左栏的「角色造型室」")
    out["面板开了"] = pg.locator("[data-character-studio]").count() > 0
    ok_tab = click_sel(pg, "[data-character-studio-tab='official']")
    out["步骤"].append("② 切到「官方角色库」")
    out["角色卡数"] = pg.locator("[data-character-strip-card]").count()
    ok_card = click_sel(pg, "[data-character-strip-card]")
    out["步骤"].append("③ 点第一张角色卡")
    out["编辑CTA数"] = pg.locator("[data-character-studio-cta='edit']").count()
    ok_edit = click_sel(pg, "[data-character-studio-cta='edit']")
    out["步骤"].append("④ 点「编辑角色」")
    pg.wait_for_timeout(1500)
    clean_portal(pg)
    out["点到了"] = {"左栏": ok_side, "页签": ok_tab, "角色卡": ok_card,
                     "编辑CTA": ok_edit}
    out["编辑器开了"] = pg.locator(SEL_EDITOR).count() > 0
    out["左列分段"] = pg.evaluate(r"""()=>{
      return [...document.querySelectorAll('[data-character-editor-segment]')]
        .map(e=>({键:e.getAttribute('data-character-editor-segment'),
                  文本:(e.textContent||'').trim().slice(0,12)}));}""")
    # ★ 逐段点一下（★ 「这个入口没有 X」必须真的点一下才算数）
    seg_reads = {}
    for seg in ("traits", "outfit", "voice"):
        ok = click_sel(pg, "[data-character-editor-segment='%s']" % seg)
        pg.wait_for_timeout(500)
        seg_reads[seg] = {
            "点到了": ok,
            "激活": pg.evaluate(
                "(s)=>{const e=document.querySelector"
                "(\"[data-character-editor-segment='\"+s+\"']\");"
                "return e?e.className:null;}", seg),
            "音色卡数": pg.locator("[data-character-editor-voice-card]").count(),
            "服装卡数": pg.locator("[data-character-editor-outfit-card]").count(),
            "服装子段数": pg.locator(
                "[data-character-editor-outfit-clothes-card]").count(),
        }
    out["分段读数"] = seg_reads
    return out


def assets_path(pg):
    """★ 路径 C：根 ⟹ 资产管理面板。"""
    out = {"步骤": []}
    ok = click_text(pg, "button[aria-label]", "资产管理")
    out["步骤"].append("① 点底部工具条的「资产管理」")
    pg.wait_for_timeout(1200)
    clean_portal(pg)
    out["点到了"] = ok
    out["面板元素数"] = pg.locator(
        "[data-asset-manager], [aria-label='关闭资产管理']").count()
    out["关闭按钮数"] = pg.locator("[aria-label='关闭资产管理']").count()
    return out


def main() -> int:
    out = {}
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            pg = ctx.new_page()
            pg.set_default_timeout(30_000)
            open_root(pg)
            out["根页"] = enumerate_root(pg)
            out["根页URL"] = pg.evaluate("()=>location.href")
            shot(pg, "01-root")

            for label, fn, shotname in (
                ("路径A_导演台", director_path, "02-director"),
                ("路径B_角色大编辑器", studio_path, "04-editor"),
                ("路径C_资产管理", assets_path, "05-assets"),
            ):
                try:
                    out[label] = fn(pg)
                    shot(pg, shotname)
                except Exception:
                    out["★%s 段异常" % label] = traceback.format_exc()[-800:]
                # ★ 每条路径都**从根重新出发**（★ 路径之间互不依赖）
                open_root(pg)
            br.close()
    except Exception:
        out["异常"] = traceback.format_exc()
    finally:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / "reachability-855.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", RAW / "reachability-855.json")
        for k in ("路径A_导演台", "路径B_角色大编辑器", "路径C_资产管理"):
            v = out.get(k)
            if isinstance(v, dict):
                print("---", k)
                for kk, vv in v.items():
                    if kk in ("可交互元素", "分段读数"):
                        continue
                    print("    %-16s %s" % (kk, vv))
        if out.get("异常"):
            print("异常：", out["异常"][-600:])
    return 0


if __name__ == "__main__":
    sys.exit(main())
