import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  await page.locator('button[aria-label="剪辑"]').click(); await page.waitForTimeout(3500);

  // ⭐ 缺陷 517 治法：别用尺寸门槛筛，用点采样从已知点反查
  const 摸=await page.evaluate(()=>{
    const R=(e)=>{const r=e.getBoundingClientRect();
      return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
    const 存=[];
    for(let y=490;y<=620;y+=10){
      const e=document.elementFromPoint(760,y);
      存.push({y, tag:e?e.tagName:'null', cls:e?(e.className||'').toString().slice(0,60):'',
        框:e?R(e):null, 文字:e?(e.innerText||'').trim().slice(0,10):''});
    }
    return 存;});
  T('纵向扫描 x=760:', JSON.stringify(摸,null,0).slice(0,3000));
} finally { await browser.close(); }
