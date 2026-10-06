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
  // ⭐ 先在工作流态看「剪辑」按钮在不在
  const wf=await page.evaluate(()=>[...document.querySelectorAll('button[aria-label="剪辑"], button')]
    .filter(b=>(b.getAttribute('aria-label')||'')==='剪辑' && b.getBoundingClientRect().width>0)
    .map(b=>{const r=b.getBoundingClientRect();return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];}));
  T('工作流态 剪辑按钮:', wf, '（空=只有故事板态有）');
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  // ⭐ 各列容器框（确认到底有几列）
  const 面板=await page.evaluate(()=>[...document.querySelectorAll('.assetboard-panel')].map(p=>{
    const r=p.getBoundingClientRect();
    const 标题=(p.innerText||'').trim().split('\n')[0];
    return {标题, 框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)]};}));
  T('⭐ .assetboard-panel 全部:', JSON.stringify(面板));
  T('⭐ 列数 =', 面板.length);
  // 剪辑按钮的图标与兄弟
  T('剪辑按钮内部:', await page.evaluate(()=>{
    const b=document.querySelector('button[aria-label="剪辑"]');
    if(!b) return null;
    return {HTML: b.innerHTML.slice(0,300), 子元素:[...b.children].map(c=>({tag:c.tagName,
      t:(c.innerText||'').trim().slice(0,6), box:(()=>{const r=c.getBoundingClientRect();return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];})()}))};}));
  // 放大视频按钮
  T('放大视频按钮:', await page.evaluate(()=>{
    const b=document.querySelector('button[aria-label="放大视频"]');
    if(!b) return null; const r=b.getBoundingClientRect();
    return {框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
      title:b.getAttribute('title'), HTML:b.innerHTML.slice(0,200),
      兄弟文本:(()=>{const p=b.parentElement; return p?(p.innerText||'').trim().slice(0,40):null;})()};}));
  // ⛔ 只 hover 不点：看 tooltip 逐字
  for (const [名字, sel] of [['剪辑','button[aria-label="剪辑"]'], ['放大视频','button[aria-label="放大视频"]']]) {
    const b=page.locator(sel).first();
    if(await b.count()===0){ T(`${名字}: 不存在`); continue; }
    await b.hover(); await page.waitForTimeout(1000);
    const tip=await page.evaluate(([sx,sy])=>{
      const cand=[...document.querySelectorAll('[role="tooltip"],.mantine-Tooltip-tooltip,[class*="Tooltip"]')]
        .filter(e=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;})
        .map(e=>({t:(e.innerText||'').trim(), box:(()=>{const r=e.getBoundingClientRect();return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];})()}));
      return cand;}, [0,0]);
    T(`⭐ ${名字} hover → tooltip:`, tip);
  }
  await page.screenshot({path:E('gi2-视频列与剪辑按钮.png'), clip:{x:960,y:40,width:480,height:770}});
  console.log('  拍 gi2');
  await page.screenshot({path:E('gi3-故事板全景.png'), clip:{x:0,y:0,width:1440,height:810}});
  console.log('  拍 gi3');
} finally { await browser.close(); }
