#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 827 clone 侧实测：量「角色造型室」面板的几何，输出与源站 raw 同形的 JSON。

用法：python3 /tmp/measure827.py [输出路径]
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/liblib_clone_studio827.json")
URL = "http://localhost:4317/"

JS = r"""()=>{
  const box=(e)=>{const r=e.getBoundingClientRect();
    return {x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const txt=(e)=>(e.textContent||'').trim().replace(/\s+/g,' ');
  const hit=(e)=>{const r=e.getBoundingClientRect();
    if(r.width<=0||r.height<=0)return false;
    const h=document.elementFromPoint(r.x+r.width/2, r.y+r.height/2);
    return !!(h&&(h===e||e.contains(h)));};
  const modal=document.querySelector('[data-character-studio]');
  if(!modal) return {error:'no panel'};

  const tabs=[...modal.querySelectorAll('[data-character-studio-tab]')].map(e=>({
    text:txt(e), box:box(e),
    font:getComputedStyle(e).fontSize+'/'+getComputedStyle(e).fontWeight,
    color:getComputedStyle(e).color}));

  const pills=[...modal.querySelectorAll('details[data-character-filter]')].map(d=>{
    const s=d.querySelector('summary');
    const panel=d.querySelector('.cs-panel');
    return {key:d.getAttribute('data-character-filter'),
      open:d.hasAttribute('open'),
      summary:box(s), summaryText:txt(s),
      panel:panel?box(panel):null,
      选项:[...d.querySelectorAll('[data-character-filter-chip]')].map(c=>txt(c))};
  });

  const byLabel={};
  for(const b of modal.querySelectorAll('button')){
    const a=b.getAttribute('aria-label')||txt(b);
    if(!a) continue;
    if(/^(搜索|多选|退出多选|列表模式|宫格模式|关闭|生成其他年龄版本|上一组|下一组)/.test(a)) byLabel[a]=box(b);
  }

  const cards=[...modal.querySelectorAll('[data-character-strip-card]')].map(c=>{
    const img=c.querySelector('img');
    return {name:c.getAttribute('data-character-strip-card'),
      box:box(c), img:img?box(img):null};
  });

  const cta=[...modal.querySelectorAll('[data-character-studio-cta]')].map(e=>({
    kind:e.getAttribute('data-character-studio-cta'), text:txt(e), box:box(e),
    bg:getComputedStyle(e).backgroundColor, color:getComputedStyle(e).color}));

  const range=modal.querySelector('input[type=range]');
  const nameEl=modal.querySelector('[data-character-studio-name]');
  const quick=modal.querySelector('[data-character-studio-quick]');
  const assets=modal.querySelector('[data-character-studio-view-assets]');

  const opts=[];
  for(const lab of modal.querySelectorAll('[data-character-filter-chip]')){
    opts.push({text:txt(lab), box:box(lab), 命中:hit(lab),
      cbSize:(()=>{const cb=lab.querySelector('input[type=checkbox]');
        return cb?box(cb):null;})(),
      有checkmark:!!lab.querySelector('.cs-check')});
  }

  return {面板:box(modal), aria:modal.getAttribute('aria-label'),
    面板样式:{bg:getComputedStyle(modal).backgroundColor,
      radius:getComputedStyle(modal).borderRadius,
      overflow:getComputedStyle(modal).overflow},
    页签:tabs, 筛选胶囊:pills, 工具按钮:byLabel,
    卡片:cards, CTA:cta,
    名字: nameEl?{text:txt(nameEl), box:box(nameEl)}:null,
    快捷: quick?box(quick):null,
    查看资产: assets?{box:box(assets), opacity:getComputedStyle(assets).opacity}:null,
    滚动条: range?{aria:range.getAttribute('aria-label'), box:box(range)}:null,
    选项:opts};
}"""


def main() -> None:
    result = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        page.get_by_role("button", name="角色造型室").first.click()
        page.wait_for_timeout(900)

        result["我的角色库"] = page.evaluate(JS)

        # 展开「性别」下拉（真实点击 summary）
        page.locator('[data-character-filter-summary="性别"]').click()
        page.wait_for_timeout(500)
        result["展开性别"] = page.evaluate(JS)
        result["展开性别"]["下拉详情"] = page.evaluate(
            """()=>[...document.querySelectorAll('details[data-character-filter]')].map(d=>{
                 const s=d.querySelector('summary'), p=d.querySelector('.cs-panel');
                 const b=(e)=>{const r=e.getBoundingClientRect();
                   return {x:Math.round(r.x),y:Math.round(r.y),
                           w:Math.round(r.width),h:Math.round(r.height)};};
                 return {key:d.getAttribute('data-character-filter'),
                         open:d.hasAttribute('open'),
                         summary:b(s), panel:p?b(p):null};})"""
        )
        page.locator('[data-character-filter-summary="性别"]').click()
        page.wait_for_timeout(300)

        page.locator('[data-character-studio-tab="official"]').click()
        page.wait_for_timeout(900)
        result["官方角色库"] = page.evaluate(JS)

        browser.close()

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written", OUT)


if __name__ == "__main__":
    main()
