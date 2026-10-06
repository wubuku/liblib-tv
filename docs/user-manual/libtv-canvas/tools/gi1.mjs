import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
const 栏目=['音频','文本','图片','视频','剪辑'];
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}
try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  const 列=await page.evaluate((名单)=>{
    return 名单.map(t=>{
      const el=[...document.querySelectorAll('*')].find(e=>e.children.length===0 &&
        (e.innerText||'').trim()===t && e.getBoundingClientRect().width>0);
      if(!el) return {列:t, 存在:false};
      const tr=el.getBoundingClientRect();
      // ⭐ 边走边用元素引用，不要把 DOMRect 当元素
      let 容器=el;
      for(let k=0;k<6;k++){ 容器=容器.parentElement; if(!容器) break;
        const r=容器.getBoundingClientRect();
        if(r.width>150 && r.height>80) break; }
      if(!容器){ return {列:t, 标题框:[Math.round(tr.x),Math.round(tr.y),Math.round(tr.width),Math.round(tr.height)], 容器:null}; }
      const r=容器.getBoundingClientRect();
      return {列:t, 存在:true,
        标题框:[Math.round(tr.x),Math.round(tr.y),Math.round(tr.width),Math.round(tr.height)],
        容器框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
        容器class:(容器.className||'').toString().slice(0,70),
        按钮数:容器.querySelectorAll('button').length,
        文本:(容器.innerText||'').trim().slice(0,160)};});
  }, 栏目);
  T('⭐ 故事板各列:');
  列.forEach(c=>{ console.log('  ', c.列, JSON.stringify(c.标题框), c.容器框?JSON.stringify(c.容器框):'(无容器)',
    '按钮', c.按钮数); if(c.文本) console.log('     文本:', JSON.stringify(c.文本)); });
  T('视口:', await page.evaluate(()=>[innerWidth,innerHeight]));
  // 页面总宽（判断剪辑列是否需要横向滚动）
  T('滚动信息:', await page.evaluate(()=>{
    const cands=[...document.querySelectorAll('*')].filter(e=>e.scrollWidth>e.clientWidth+20 && e.getBoundingClientRect().width>200);
    return cands.slice(0,4).map(e=>({cls:(e.className||'').toString().slice(0,60),
      scrollW:e.scrollWidth, clientW:e.clientWidth, scrollL:e.scrollLeft,
      box:(()=>{const r=e.getBoundingClientRect();return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];})(),
      ovX:getComputedStyle(e).overflowX}));}));
  await page.screenshot({path:E('gi1-故事板全列.png'), clip:{x:0,y:0,width:1440,height:810}});
  console.log('  拍 gi1');
} finally { await browser.close(); }
