import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

const 条判据 = `(()=>{const c=(e)=>e.className||'';return [...document.querySelectorAll('div')]
  .filter(e=>{const r=e.getBoundingClientRect();
    return r.y>=528&&r.y<=534&&r.width>800&&r.height>=40&&r.height<=50
      &&(e.innerText||'').includes('00:00');})
  .sort((a,b)=>b.getBoundingClientRect().width-a.getBoundingClientRect().width)[0];})()`;

try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  await page.locator('button[aria-label="剪辑"]').click(); await page.waitForTimeout(3500);

  const j=await page.evaluate(`(()=>{
    const R=(e)=>{const r=e.getBoundingClientRect();
      return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
    const 条=${条判据}; if(!条) return {错:'仍找不到'};
    const 点=[...条.querySelectorAll('button,[role="button"]')].map((b,i)=>{const s=getComputedStyle(b);
      const r=b.getBoundingClientRect();
      return {i, 框:R(b), 文本:(b.innerText||'').trim().replace(/\\s+/g,' ').slice(0,10),
        aria:b.getAttribute('aria-label'), title:b.getAttribute('title'),
        禁用:b.disabled===true||b.getAttribute('aria-disabled')==='true',
        鼠标:s.cursor, 不透明度:s.opacity,
        落点:(()=>{const h=document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2));
          return h?(h.tagName+(h.closest('button')===b?'':'(不在内)')):'null';})()};});
    const 画布=[...document.querySelectorAll('canvas')].map(c=>R(c));
    const 滑=[...条.querySelectorAll('input[type=range],[role=slider]')]
      .map(e=>({框:R(e), 值:e.value??e.getAttribute('aria-valuenow'),
        min:e.min,max:e.max,aria:e.getAttribute('aria-label')}));
    return {条框:R(条), 按钮数:点.length, 按钮:点, 画布, 滑块:滑,
      条文字:(条.innerText||'').trim().replace(/\\s+/g,' ')};})()`);
  T('工具条完整读数:', JSON.stringify(j,null,1).slice(0,6000));
  await page.screenshot({path:E('gj8-a-工具条读数.png')});
} finally { await browser.close(); }
