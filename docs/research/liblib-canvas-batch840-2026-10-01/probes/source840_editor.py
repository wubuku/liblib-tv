#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 840 源站探针：把「编辑角色」打开的**角色大编辑器**测清楚。

★★ **只读**：绝不点「确认生成／保存／保存并添加到画布」—— 底部那个「保存时生成角色资产 ⚡44」
是**真实积分** ⟹ 本趟只**打开**编辑器并**读**，不产生任何付费副作用。

★ 上一趟（batch 839 的 `assets839c`）只记到了**新增文本**（`[text,x,y]` 三元组）⟹ 缺三样：
  ① 编辑器**容器**的盒（不知道它到底盖住哪儿、是不是模态）；
  ② **输入框的值**（底栏标题是 `<input>` ⟹ 文本读数器**读不到**）；
  ③ **滑杆轨道**与右栏页签**图标**（没有文本 ⟹ 文本读数器也读不到）。

⟹ 本趟改成**子树读数**：
  1. 找到叶子文本「脸部精修」与「确认生成」；
  2. 往上找**同时**包含这两者的**最小公共祖先** ⟹ 那个就是**编辑器容器**；
  3. 把这棵**子树**整棵读出来（含 `input` 的 value、`button` 的 aria-label、
     `role=slider`／`input[type=range]` 的轨道与当前值、每个 `svg` 图标的盒）。

★ 为什么不用「点前/点后差分」当主口径：差分分不清**画布上被盖住的节点**与**编辑器自己的元素**
⟹ ⟹ 子树读数**天然**只含编辑器自己的 DOM。

★ 输出：`/tmp/liblib_source_840_editor.json` ＋ 截图 `/tmp/liblib_source_840_editor.png`
"""
import json
import pathlib
import traceback

from playwright.sync_api import sync_playwright

COOKIE = pathlib.Path("/tmp/liblib-cookie.json")
OUT = pathlib.Path("/tmp/liblib_source_840_editor.json")
SHOT = pathlib.Path("/tmp/liblib_source_840_editor.png")
URL = ("https://www.liblib.tv/canvas?spaceId=7709759"
       "&projectId=a860e1da8e9e4504bececda022386429")

# ★ 编辑器容器：取「脸部精修」与「确认生成」的**最小公共祖先**
TREE = r"""()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\s+/g,' ');
  const vis=(e)=>{const r=e.getBoundingClientRect();
    if(r.width<=0||r.height<=0)return false;
    const cs=getComputedStyle(e);
    return cs.display!=='none'&&cs.visibility!=='hidden'&&Number(cs.opacity||'1')>0.001;};
  const leafByText=(t)=>{for(const e of document.querySelectorAll('span,div,button,a,p,label')){
    if(e.children.length===0&&txt(e)===t)return e;}return null;};
  const a=leafByText('脸部精修'), b=leafByText('确认生成');
  if(!a||!b)return {err:'锚点没找到',hasA:!!a,hasB:!!b};
  const chain=(e)=>{const s=new Set();for(let n=e;n;n=n.parentElement)s.add(n);return s;};
  const ca=chain(a);let root=null;
  for(let n=b;n;n=n.parentElement){if(ca.has(n)){root=n;break;}}
  if(!root)return {err:'找不到公共祖先'};

  const desc=root.querySelectorAll('*');
  const leaves=[],inputs=[],ctrls=[],icons=[],svgs=[];
  for(const e of desc){
    if(!vis(e))continue;
    const r=e.getBoundingClientRect();
    const t=txt(e);
    const tag=e.tagName;
    const cls=(e.getAttribute('class')||'').slice(0,120);
    if(e.children.length===0&&t&&t.length<=40)
      leaves.push({tag,text:t,box:box(e),cls});
    if(tag==='INPUT'||tag==='TEXTAREA')
      inputs.push({tag,type:e.getAttribute('type')||'',value:e.value||'',
        placeholder:e.getAttribute('placeholder')||'',box:box(e),cls});
    const role=e.getAttribute('role')||'';
    if(role==='slider'||e.getAttribute('type')==='range')
      ctrls.push({kind:'slider',role,ariaNow:e.getAttribute('aria-valuenow'),
        ariaMin:e.getAttribute('aria-valuemin'),ariaMax:e.getAttribute('aria-valuemax'),
        value:e.value||'',box:box(e),cls});
    if(role==='switch'||e.getAttribute('type')==='checkbox')
      ctrls.push({kind:'switch',role,checked:!!e.checked,
        ariaChecked:e.getAttribute('aria-checked'),box:box(e),cls});
    if(tag==='BUTTON'||role==='button')
      ctrls.push({kind:'button',text:t.slice(0,30),
        aria:e.getAttribute('aria-label')||'',box:box(e),cls});
    if(tag==='SVG')
      svgs.push({box:box(e),cls,parentTag:e.parentElement?e.parentElement.tagName:'',
        parentAria:e.parentElement?(e.parentElement.getAttribute('aria-label')||''):''});
  }
  const rcs=getComputedStyle(root);
  return {
    root:{tag:root.tagName,box:box(root),cls:(root.getAttribute('class')||'').slice(0,200),
      position:rcs.position,zIndex:rcs.zIndex,bg:rcs.backgroundColor,
      radius:rcs.borderRadius,overflow:rcs.overflow},
    leaves,inputs,ctrls,icons,svgs,
    url:location.href,
  };
}"""

FIND_ASSETS_BTN = """()=>{
  const out=[];
  for(const e of document.querySelectorAll('button')){
    if((e.textContent||'').trim()!=='查看角色资产')continue;
    const r=e.getBoundingClientRect();
    out.push({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),
      h:Math.round(r.height)});
  }
  return out;}"""


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
            log["★是否登录成功_有画布"] = bool(
                pg.query_selector('[data-sidebar-btn="character-library"]'))
            el = pg.query_selector('[data-sidebar-btn="character-library"]')
            if el:
                bb = el.bounding_box()
                if bb:
                    pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
            pg.wait_for_timeout(5000)

            tab = pg.query_selector("button:text-is('官方角色库')")
            log["★是否有官方角色库页签"] = bool(tab)
            if tab:
                bb = tab.bounding_box()
                pg.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)
                pg.wait_for_timeout(4000)

            # ★ 进资产视图：先悬停（浮层 pointer-events-none）⟹ 等 ⟹ 再点
            bs = pg.evaluate(FIND_ASSETS_BTN)
            log["★找到查看角色资产"] = bool(bs)
            if bs:
                b = bs[0]
                pg.mouse.move(b["x"] + b["w"] / 2, b["y"] + b["h"] / 2)
                pg.wait_for_timeout(1500)
                bs2 = pg.evaluate(FIND_ASSETS_BTN)
                b2 = bs2[0] if bs2 else b
                pg.mouse.click(b2["x"] + b2["w"] / 2, b2["y"] + b2["h"] / 2)
                pg.wait_for_timeout(3500)

            log["★是否点到编辑角色"] = click_text(pg, "编辑角色")
            pg.wait_for_timeout(5000)

            tree = pg.evaluate(TREE)
            log["★子树读数"] = tree
            pg.screenshot(path=str(SHOT))
            br.close()
    except Exception:
        log["异常"] = traceback.format_exc()
    finally:
        OUT.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        print("已落盘：", OUT)
        t = log.get("★子树读数") or {}
        print("登录：", log.get("★是否登录成功_有画布"),
              "｜页签：", log.get("★是否有官方角色库页签"),
              "｜资产视图按钮：", log.get("★找到查看角色资产"),
              "｜编辑角色：", log.get("★是否点到编辑角色"))
        if t.get("err"):
            print("★ 读数失败：", t)
        if t.get("root"):
            print("容器：", json.dumps(t["root"], ensure_ascii=False))
            print("文本 %d 条｜输入 %d 条｜控件 %d 条｜svg %d 条" % (
                len(t.get("leaves") or []), len(t.get("inputs") or []),
                len(t.get("ctrls") or []), len(t.get("svgs") or [])))
        if log.get("异常"):
            print("异常：", log["异常"])


if __name__ == "__main__":
    main()
