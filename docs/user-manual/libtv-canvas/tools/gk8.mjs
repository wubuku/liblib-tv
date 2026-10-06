import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

const 编辑态 = () => {
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  // ⭐ 缺陷 522：不要用固定高度阈值 —— 音频面板只有 188 高，视频 248 高
  const p=[...document.querySelectorAll('.node-floating-ui')].find(e=>{
    const r=e.getBoundingClientRect();
    return r.width>=500 && r.height>=150 && /高级设置/.test(e.innerText||'');});
  if(!p) return {无:true};
  return {框:R(p), 文字:(p.innerText||'').trim().replace(/\n{2,}/g,' | ').slice(0,200),
    顶栏:[...p.querySelectorAll('button')].slice(0,6).map(b=>{const r=b.getBoundingClientRect();
      return {t:(b.innerText||'').trim().slice(0,6), aria:b.getAttribute('aria-label'),
        title:b.getAttribute('title'), 框:R(b)};})};
};

const CLIP={x:490,y:40,width:950,height:430};
try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);

  // 音频编辑态（clip 覆盖 x 512~1415）
  await page.locator('.assetboard-panel button', {hasText:'音频节点 1'}).first().click();
  await page.waitForTimeout(2500);
  T('【音频编辑态】', await page.evaluate(编辑态));
  await page.screenshot({path:E('gk8-a-音频编辑态.png'), clip:CLIP});
  await page.screenshot({path:E('gk8-b-音频编辑态-全宽.png'), clip:{x:0,y:40,width:1440,height:430}});
  await page.keyboard.press('Escape'); await page.waitForTimeout(1700);

  // 文本编辑态
  await page.locator('.assetboard-panel span', {hasText:'文本节点 2'}).first().click();
  await page.waitForTimeout(2500);
  T('【文本编辑态】', await page.evaluate(编辑态));
  await page.screenshot({path:E('gk8-c-文本编辑态.png'), clip:CLIP});
  await page.keyboard.press('Escape'); await page.waitForTimeout(1700);

  // 图片编辑态
  await page.mouse.click(700, 220); await page.waitForTimeout(2500);
  T('【图片编辑态】', await page.evaluate(编辑态));
  await page.screenshot({path:E('gk8-d-图片编辑态.png'), clip:CLIP});
  await page.keyboard.press('Escape'); await page.waitForTimeout(1700);
  T('【复原后】', await page.evaluate(编辑态));
} finally { await browser.close(); }
