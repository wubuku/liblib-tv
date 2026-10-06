import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

const 探=()=>{
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const D=(e)=>({tag:e.tagName, aria:e.getAttribute('aria-label'),
    dataStoryboardExpand:e.getAttribute('data-storyboard-expand'),
    ariaExpanded:e.getAttribute('aria-expanded'),
    dataColumn:e.getAttribute('data-storyboard-column'),
    dataExpanded:e.getAttribute('data-storyboard-expanded'),
    框:R(e), 类:(e.className||'').toString().slice(0,80)});
  return {
    // ⭐ 本仓库源码专有的 data-* 判据
    dataExpand元素:[...document.querySelectorAll('[data-storyboard-expand]')].map(D),
    dataColumn元素:[...document.querySelectorAll('[data-storyboard-column]')].map(D),
    // 全部 aria-label 里带「放大」「还原」的
    含放大还原:[...document.querySelectorAll('button,[role="button"]')].filter(b=>/放大|还原|展开|收起/.test(
      b.getAttribute('aria-label')||b.getAttribute('title')||'')).map(D),
    // 每列头所有按钮
    列头按钮:[...document.querySelectorAll('.assetboard-panel')].map(p=>({
      列:(p.innerText||'').trim().split('\n')[0], 框:R(p),
      按钮:[...p.querySelectorAll('header button,header [role="button"]')].map(b=>({
        aria:b.getAttribute('aria-label'), 文本:(b.innerText||'').trim().slice(0,8),
        dataExpand:b.getAttribute('data-storyboard-expand'), 框:R(b)}))})),
  };
};

try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  T('【A 故事板态】', JSON.stringify(await page.evaluate(探),null,1).slice(0,4000));

  await page.locator('button[aria-label="放大视频"]').click(); await page.waitForTimeout(2200);
  T('【B 放大态】', JSON.stringify(await page.evaluate(探),null,1).slice(0,4000));
  await page.screenshot({path:E('gj9-a-放大态.png')});
  await page.screenshot({path:E('gj9-b-放大态-两列头.png'),
    clip:{x:0,y:40,width:1440,height:60}});
  await page.keyboard.press('Escape'); await page.waitForTimeout(1600);
  T('【C Esc 还原后】', JSON.stringify(await page.evaluate(探),null,1).slice(0,2500));
} finally { await browser.close(); }
