import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const MAIN='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}
async function 新空画布(名){ await open(page,MAIN); await closePromos(page);
  await page.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(x=>{const r=x.getBoundingClientRect();
    return r.x>160&&r.x<180&&r.y<20&&r.width>40;}); b.click();});
  await page.waitForTimeout(900);
  await page.locator('button[aria-label="新建画布"]').click(); await page.waitForTimeout(900);
  await page.locator('input[aria-label="画布名称"]').fill(名);
  await page.keyboard.press('Enter'); await page.waitForTimeout(3200);
  await page.evaluate(()=>{const bs=[...document.querySelectorAll('button[aria-label="关闭"]')]
    .filter(b=>{const r=b.getBoundingClientRect(); return r.width>0&&r.height>0;}); if(bs.length) bs[bs.length-1].click();});
  await page.waitForTimeout(1600); await 稳定(); }
try {
  // 拍「剧本生成」点开后的题材抽屉
  await 新空画布('GD3-剧本抽屉');
  const b=page.locator('button').filter({hasText:/^剧本生成$/}).first();
  await b.click(); await page.waitForTimeout(3500); await 稳定();
  const d=await page.evaluate(()=>{
    const e=document.querySelector('.mantine-Drawer-content');
    if(!e) return null; const r=e.getBoundingClientRect();
    return {框:[r.x,r.y,r.width,r.height].map(Math.round), 全文:(e.innerText||'').trim().slice(0,300)};});
  T('题材抽屉:', d);
  if(d) await page.screenshot({path:E('gd3-剧本生成-题材抽屉.png'),
    clip:{x:Math.max(0,d.框[0]-20),y:Math.max(0,d.框[1]-20),width:d.框[2]+40,height:Math.min(700,d.框[3]+40)}});
  console.log('  拍 gd3');
  T('节点数（应仍为 0）:', await page.locator('.react-flow__node').count());
} finally { await browser.close(); }
