import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const EMPTY='https://www.liblib.tv/canvas?spaceId=10354929&projectId=13249957f18e42ce90d3b913e985cef0';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){ let p=-1; for(let i=0;i<12;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p; }
const 芯片=(w)=>page.locator('button').filter({hasText:new RegExp(`^${w}$`)}).first();
try {
  await open(page,EMPTY); await closePromos(page);
  T('节点数:', await 稳定());
  // 逐枚 hover，读 tooltip
  for (const w of ['图片生成','视频生成','音频生成','剧本生成','智能剪辑']) {
    const b=芯片(w);
    if(await b.count()===0){ T(`${w}: 找不到`); continue; }
    await b.hover(); await page.waitForTimeout(900);
    const tip=await page.evaluate(()=>{
      // 站点 tooltip 通常是浮层容器里的文字
      const cands=[...document.querySelectorAll('[role="tooltip"],.mantine-Tooltip-tooltip,[data-portal] div')]
        .filter(e=>{const r=e.getBoundingClientRect(); return r.width>0&&r.height>0&&r.y<700;})
        .map(e=>(e.innerText||'').trim()).filter(Boolean);
      return cands.slice(0,3);
    });
    T(`${w} hover →`, tip);
  }
  // 整排的完整 HTML 结构（第一枚）
  const html=await page.evaluate(()=>{
    const b=[...document.querySelectorAll('button')].find(e=>e.innerText.trim()==='图片生成');
    if(!b) return null;
    let p=b, out=[];
    for(let i=0;i<4&&p;i++){ out.push({i,tag:p.tagName,cls:(p.className||'').toString().slice(0,150),
      box:(()=>{const r=p.getBoundingClientRect();return [r.x,r.y,r.width,r.height].map(Math.round);})()}); p=p.parentElement; }
    return out;
  });
  T('图片生成 祖先链:', html);
  // 点第一枚 —— 安全的：它只是打开节点创建面板，不触发生成
  const net=[]; page.on('request',r=>{const u=r.url(); if(/generate|submit|task/.test(u)) net.push(r.method()+' '+u.replace('https://api.liblib.tv',''));});
  const b=芯片('图片生成'); const bx=await b.boundingBox();
  T('点前 节点数:', await page.locator('.react-flow__node').count());
  await b.click(); await page.waitForTimeout(2500);
  T('点后 节点数:', await page.locator('.react-flow__node').count());
  T('有无面板:', await page.evaluate(()=>{
    const ps=[...document.querySelectorAll('[class*="Popover"],[class*="Modal"],[role="dialog"],[class*="Dropdown"]')]
      .filter(e=>e.getBoundingClientRect().height>0).map(e=>({cls:(e.className||'').toString().slice(0,80),
        box:(()=>{const r=e.getBoundingClientRect();return [r.x,r.y,r.width,r.height].map(Math.round);})(),
        t:(e.innerText||'').trim().slice(0,60)}));
    return ps.slice(0,5);
  }));
  T('生图类请求:', net);
} finally { await browser.close(); }
