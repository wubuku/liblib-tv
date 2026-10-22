#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 841 源站探针①：把角色大编辑器**右栏五枚页签**（眉眼/鼻子/嘴唇/脸部/妆造）的控件实测出来。

## 为什么测这个

batch 840 只实测了**「皮肤」页签**的六条滑杆 ⟹ ⟹ clone 里那五枚页签只能显示
**空态说明**（本批不编造控件）。⟹ 本批把它们的**控件内容**实测出来 ⟹ ⟹ clone 才能填上。

★ 同时也要看清楚：**点右栏页签会不会连带改左列**（源站的左列五段与右栏六页签可能不是
两层独立导航）⟹ ⟹ 每点一次都读**整棵模态子树** ⟹ 一次读数就把两侧的变化都记下来。

## 安全

★★ **只读**：绝不点「确认生成／保存／保存并添加到画布／智能调整／撤销／恢复／按住对比」。
   ★★ 而且**每次点击前后都读一次 ⚡ 积分**（源站那趟 ⚡44）⟹ 若积分变了 ⟹ **立刻停**
   ⟹ （那是「点一下就花了真钱」的信号 ⟹ 必须停下来报告，不能继续）。
   ★ 左右两列的段／页签只是**导航**（切换面板内容），不产生生成 ⟹ 但仍然每步核对积分。

## 输出

`/tmp/liblib_source_841_tabs.json`
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_841_tabs.json")
SHOT = pathlib.Path("/tmp/liblib_source_841_tabs.png")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 读整棵模态子树的**元素清单**（与 batch 840 的第②趟同款，但更精简）
MEASURE = r"""()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\s+/g,' ');
  const vis=(e)=>{const r=e.getBoundingClientRect();
    if(r.width<=0||r.height<=0)return false;
    const cs=getComputedStyle(e);
    return cs.display!=='none'&&cs.visibility!=='hidden'&&Number(cs.opacity||'1')>0.001;};
  const leafByText=(t)=>{for(const e of document.querySelectorAll('span,div,button,a,p,label')){
    if(e.children.length===0&&txt(e)===t)return e;}return null;};
  const save=leafByText('保存'), seg=leafByText('脸部精修');
  if(!save||!seg)return {err:'锚点没找到'};
  const chain=(e)=>{const s=new Set();for(let n=e;n;n=n.parentElement)s.add(n);return s;};
  const cs_=chain(seg);let modal=null;
  for(let n=save;n;n=n.parentElement){if(cs_.has(n)){modal=n;break;}}
  if(!modal)return {err:'模态容器没找到'};

  const all=[];
  for(const e of modal.querySelectorAll('*')){
    if(!vis(e))continue;
    const t=txt(e);
    all.push({tag:e.tagName,role:e.getAttribute('role')||'',
      text:(e.children.length===0?t:''),
      type:e.getAttribute('type')||'',
      value:(e.tagName==='INPUT'||e.tagName==='TEXTAREA')?(e.value||''):'',
      aria:e.getAttribute('aria-label')||'',
      checked:(e.tagName==='INPUT')?(e.checked===true):null,
      box:box(e),cls:(e.getAttribute('class')||'').slice(0,110)});
  }
  const leaves=all.filter(e=>e.text&&e.text.length<=44);
  const inputs=all.filter(e=>e.tag==='INPUT'||e.tag==='TEXTAREA');
  const ctrls=all.filter(e=>e.tag==='BUTTON'||e.role==='button'||e.role==='slider'
    ||e.role==='switch'||e.type==='checkbox'||e.type==='range');
  const svgs=all.filter(e=>e.tag==='svg');
  // ★ 右栏的滚动区（y 在 231..833 之外的那一段）—— 用来切出「右栏这一页」的内容
  const right=all.filter(e=>e.box.x>=1273&&e.box.y>=231&&e.box.y<=833);
  // ★ 积分（⚡ 旁边的数字）
  const credit=leaves.filter(e=>/^\d+$/.test(e.text||'')).map(e=>({
    text:e.text,box:e.box}));
  const segBtn=[...modal.querySelectorAll('button')].filter(b=>{
    const t=txt(b);
    return ['脸部精修','脸部 & 身体特征','身材塑形','服装造型','音色音调']
      .some(x=>t.startsWith(x));});
  const tabBtn=[...modal.querySelectorAll('button')].filter(b=>{
    const a=b.getAttribute('aria-label')||'';
    return ['皮肤','眉眼','鼻子','嘴唇','脸部','妆造'].includes(a);});
  return {
    modal:box(modal),
    segBtns:segBtn.map(b=>({text:txt(b).slice(0,20),box:box(b),
      selected:!!b.getAttribute('aria-selected')||b.className.includes('bg-[')})),
    tabBtns:tabBtn.map(b=>({aria:b.getAttribute('aria-label'),box:box(b),
      cls:(b.getAttribute('class')||'').slice(0,60),
      borderBottom:getComputedStyle(b).borderBottomColor})),
    leaves,inputs,ctrls,svgs,right,credit,
    count:all.length,url:location.href};
}"""


def click_text(page, label):
    for e in page.query_selector_all("span,div,button,a,p"):
        if (e.text_content() or "").strip() != label:
            continue
        bb = e.bounding_box()
        if not bb:
            continue
        page.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
        return True
    return False


def read_credit(page):
    """读**底栏那颗**积分（源站那趟是 44）。

    ★★ **第一版这里踩了坑**：读数器把**整页所有**纯数字叶子都读了（画布节点的编号、
       右栏滑杆的数值…）⟹ ⟹ 切一次页签，右栏滑杆的「0」就换了个 y ⟹ ⟹ 列表变了
       ⟹ ⟹ 报成「积分变了 ⟹ 立刻停」⟹ ⟹ **误报**，而且**只测到 1/5 页签就停了**。

    ★ **通用形态**：安全闸必须读**那一颗**积分（位置确定：底栏 ⚡ 右边、x≈547 y≈868），
      不能读「页面上所有数字」⟹ ⟹ **判据要读对的字段**。
    """
    return page.evaluate("""()=>{
      const hits=[];
      for(const e of document.querySelectorAll('span,div,b')){
        const t=(e.textContent||'').trim();
        if(!/^\\d+$/.test(t)||e.children.length!==0)continue;
        const r=e.getBoundingClientRect();
        if(r.width<=0||r.height<=0)continue;
        const x=Math.round(r.x), y=Math.round(r.y);
        // ★ 底栏那一颗：⚡ 右边、y 落在底栏那一行（源站实测 ⚡ @534,872 ／ 44 @547,868）
        if(x>=540&&x<=575&&y>=855&&y<=885)hits.push({t,x,y});
      }
      return hits;}""")


def main():
    log = {}
    try:
        cookies = json.loads(COOKIE.read_text(encoding="utf-8"))
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            ctx = br.new_context(viewport={"width": 1920, "height": 1080},
                                 locale="zh-CN")
            ctx.add_cookies([{"name": c["name"], "value": c["value"],
                              "domain": c["domain"], "path": c.get("path", "/")}
                             for c in cookies])
            pg = ctx.new_page()
            pg.set_default_timeout(25_000)
            pg.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            pg.wait_for_timeout(12_000)
            el = pg.query_selector("text=下次再说")
            if el:
                el.click()
                pg.wait_for_timeout(900)
            el = pg.query_selector('[data-sidebar-btn="character-library"]')
            if el:
                bb = el.bounding_box()
                if bb:
                    pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
            pg.wait_for_timeout(5000)
            tab = pg.query_selector("button:text-is('官方角色库')")
            if tab:
                bb = tab.bounding_box()
                pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
                pg.wait_for_timeout(4000)
            log["★是否点到编辑角色"] = click_text(pg, "编辑角色")
            pg.wait_for_timeout(5000)

            states = {}
            # ★ 基线：默认态（脸部精修 ＋ 皮肤）
            base_credit = read_credit(pg)
            states["A_默认态_脸部精修_皮肤"] = pg.evaluate(MEASURE)
            log["★基线积分"] = base_credit

            def credit_now():
                return read_credit(pg)

            # ★ 点**右栏**的六枚页签（皮肤是基线 ⟹ 只点另外五枚）
            for label in ["眉眼", "鼻子", "嘴唇", "脸部", "妆造"]:
                before = credit_now()
                ok = pg.evaluate(
                    """(label)=>{
                      const b=[...document.querySelectorAll('button')]
                        .find(e=>(e.getAttribute('aria-label')||'')===label);
                      if(!b)return false; b.click(); return true;}""", label)
                pg.wait_for_timeout(2500)
                after = credit_now()
                states["B_页签_%s" % label] = pg.evaluate(MEASURE)
                log["★页签_%s_积分前" % label] = before
                log["★页签_%s_积分后" % label] = after
                log["★页签_%s_积分是否变化" % label] = (before != after)
                log["★页签_%s_是否点到" % label] = ok
                if before != after:
                    log["★★ 积分变了 ⟹ 立刻停"] = True
                    break
                # ★ 点完切回「皮肤」，保证下一枚页签是从同一基线出发
                pg.evaluate("""()=>{const b=[...document.querySelectorAll('button')]
                    .find(e=>(e.getAttribute('aria-label')||'')==='皮肤'); if(b)b.click();}""")
                pg.wait_for_timeout(1500)

            # ★ 再点**左列**的四段（默认是「脸部精修」⟹ 点另外四段）
            for label in ["脸部 & 身体特征", "身材塑形", "服装造型", "音色音调"]:
                before = credit_now()
                ok = pg.evaluate(
                    """(label)=>{
                      const b=[...document.querySelectorAll('button')]
                        .find(e=>(e.textContent||'').trim().startsWith(label));
                      if(!b)return false; b.click(); return true;}""", label)
                pg.wait_for_timeout(2500)
                after = credit_now()
                states["C_分段_%s" % label] = pg.evaluate(MEASURE)
                log["★分段_%s_积分前" % label] = before
                log["★分段_%s_积分后" % label] = after
                log["★分段_%s_积分是否变化" % label] = (before != after)
                log["★分段_%s_是否点到" % label] = ok
                if before != after:
                    log["★★ 积分变了 ⟹ 立刻停"] = True
                    break

            log["★各状态读数"] = states
            pg.screenshot(path=str(SHOT))
            br.close()
    except Exception:
        log["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        for k, v in log.items():
            if k.startswith("★") and "读数" not in k:
                print("  %-28s %s" % (k, json.dumps(v, ensure_ascii=False)[:120]))
        for name, st in (log.get("★各状态读数") or {}).items():
            if not st or st.get("err"):
                print("  ★ %s ⟹ %s" % (name, st))
                continue
            right_leaves = [l for l in st.get("right", [])
                            if l["text"] and l["text"] != "皮肤"]
            print("── %s （元素 %d ／ 右栏文本 %d）"
                  % (name, st.get("count", 0), len(right_leaves)))
            for l in right_leaves[:26]:
                print("     %-7s %-22s box=(%d,%d,%d,%d)" % (
                    l["tag"], (l["text"] or "")[:22], l["box"]["x"], l["box"]["y"],
                    l["box"]["w"], l["box"]["h"]))
        if log.get("异常"):
            print("异常：", log["异常"])


if __name__ == "__main__":
    main()
