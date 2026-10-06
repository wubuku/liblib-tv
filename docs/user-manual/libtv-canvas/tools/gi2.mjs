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
  // 「剪辑」元素的完整信息
  const j=await page.evaluate(()=>{
    const el=[...document.querySelectorAll('*')].find(e=>e.children.length===0 &&
      (e.innerText||'').trim()==='剪辑' && e.getBoundingClientRect().width>0);
    if(!el) return null;
    const r=el.getBoundingClientRect();
    let p=el, 链=[];
    for(let k=0;k<6&&p;k++){const q=p.getBoundingClientRect();
      链.push({k,tag:p.tagName,cls:(p.className||'').toString().slice(0,90),
        box:[Math.round(q.x),Math.round(q.y),Math.round(q.width),Math.round(q.height)],
        可点:getComputedStyle(p).cursor, 文本:(p.innerText||'').trim().slice(0,50)});
      p=p.parentElement;}
    return {框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)], 链,
      兄弟:(()=>{const par=el.parentElement; return par?[...par.children].map(c=>{
        const q=c.getBoundingClientRect(); return {tag:c.tagName, t:(c.innerText||'').trim().slice(0,12),
          box:[Math.round(q.x),Math.round(q.y),Math.round(q.width),Math.round(q.height)]};}):null;})()};});
  T('「剪辑」元素:', JSON.stringify(j,null,1).slice(0,2000));
  // 视频列里「全部」筛选的完整兄弟
  const 视频列=await page.evaluate(()=>{
    const el=[...document.querySelectorAll('*')].find(e=>e.children.length===0 &&
      (e.innerText||'').trim()==='视频' && e.getBoundingClientRect().width>0);
    if(!el) return null;
    let 容器=el; for(let k=0;k<6;k++){容器=容器.parentElement; if(!容器) break;
      const r=容器.getBoundingClientRect(); if(r.width>150&&r.height>80) break;}
    if(!容器) return null;
    return [...容器.querySelectorAll('button,[role="button"]')].map(b=>{const r=b.getBoundingClientRect();
      return {t:(b.innerText||'').trim().slice(0,8), aria:b.getAttribute('aria-label'),
        box:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
        落点:(()=>{const h=document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2));
          return h?(h.innerText||h.tagName).trim().slice(0,12):null;})()};});});
  T('视频列所有按钮:', JSON.stringify(视频列,null,1).slice(0,1600));
  await page.screenshot({path:E('gi2-视频列与剪辑行.png'), clip:{x:960,y:40,width:480,height:770}});
  console.log('  拍 gi2');
} finally { await browser.close(); }
