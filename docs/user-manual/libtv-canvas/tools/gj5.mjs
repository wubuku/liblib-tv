import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

// 进剪辑器后，把「智能剪辑」标题的祖先当剪辑器根
const 读剪辑器 = () => {
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const 标=[...document.querySelectorAll('*')].find(e=>e.children.length===0 &&
    (e.innerText||'').trim()==='智能剪辑' && e.getBoundingClientRect().width>0);
  if(!标) return {错:'找不到智能剪辑标题'};
  let 根=标; for(let k=0;k<6;k++){ 根=根.parentElement; if(!根) break;
    const r=根.getBoundingClientRect(); if(r.width>500 && r.height>400) break; }
  if(!根) return {错:'找不到剪辑器根'};
  const 描述=(b)=>{const s=getComputedStyle(b);
    return {tag:b.tagName, 文本:(b.innerText||'').trim().slice(0,10),
      aria:b.getAttribute('aria-label'), title:b.getAttribute('title'),
      dataTip:b.getAttribute('data-tip')||b.getAttribute('data-tooltip'),
      框:R(b), 禁用:b.disabled===true, 透明度:s.opacity, 鼠标:s.cursor,
      落点:(()=>{const r=b.getBoundingClientRect();
        const h=document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2));
        return h?(h.tagName+(h.closest('button')?'(内)':'')).slice(0,14):null;})()};};
  return {根框:R(根), 根类:(根.className||'').toString().slice(0,90),
    按钮:[...根.querySelectorAll('button')].map(描述),
    视频元素:根.querySelectorAll('video').length,
    轨道:[...根.querySelectorAll('[class*="track"],[class*="Track"]')]
      .map(e=>({cls:(e.className||'').toString().slice(0,50), 框:R(e)})).slice(0,8),
    故事板列:[...document.querySelectorAll('.assetboard-panel')]
      .map(p=>({标题:(p.innerText||'').trim().split('\n')[0], 框:R(p)}))};
};

try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  await page.locator('button[aria-label="剪辑"]').click(); await page.waitForTimeout(3500);
  const j=await page.evaluate(读剪辑器);
  T('剪辑器:', JSON.stringify(j,null,1).slice(0,4200));
  await page.screenshot({path:E('gj5-a-剪辑器全貌.png')});
  await page.screenshot({path:E('gj5-b-工具条.png'),
    clip:{x:495,y:505,width:940,height:70}});
} finally { await browser.close(); }
