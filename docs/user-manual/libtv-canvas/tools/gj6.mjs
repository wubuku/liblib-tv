import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

// 判据：时间码文本所在的横向条带（y 在 505~580）
const 读工具条 = () => {
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const 条=[...document.querySelectorAll('div')].filter(e=>{const r=e.getBoundingClientRect();
    const s=getComputedStyle(e);
    return r.y>495 && r.y<530 && r.width>800 && r.height>40 && r.height<90
      && s.display==='flex' && (e.innerText||'').includes('00:00');})
    .sort((a,b)=>b.getBoundingClientRect().width-a.getBoundingClientRect().width)[0];
  if(!条) return {错:'找不到工具条'};
  // 往根爬一层，看时间轴
  const 描述=(e)=>{const s=getComputedStyle(e); const r=e.getBoundingClientRect();
    return {tag:e.tagName, 文本:(e.innerText||'').trim().replace(/\s+/g,' ').slice(0,12),
      aria:e.getAttribute('aria-label'), title:e.getAttribute('title'),
      框:R(e), 禁用:e.disabled===true||e.getAttribute('aria-disabled')==='true',
      鼠标:s.cursor, 不透明度:s.opacity,
      落点:(()=>{const h=document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2));
        return h?h.tagName:'null';})()};};
  return {条框:R(条), 条类:(条.className||'').toString().slice(0,110),
    可点:[...条.querySelectorAll('button,[role="button"],[tabindex]')].map(描述),
    全部子:条.children.length,
    条文字:(条.innerText||'').trim().replace(/\s+/g,' '),
    // 时间轴：条的正下方
    时间轴:(()=>{const r=条.getBoundingClientRect();
      const 下=[...document.querySelectorAll('div')].filter(e=>{const q=e.getBoundingClientRect();
        return q.y>Math.round(r.bottom)-6 && q.y<Math.round(r.bottom)+14 && q.width>800 && q.height>80;})
        .sort((a,b)=>b.getBoundingClientRect().height-a.getBoundingClientRect().height);
      return 下.slice(0,3).map(e=>({框:R(e), cls:(e.className||'').toString().slice(0,80)}));})()};
};

try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  await page.locator('button[aria-label="剪辑"]').click(); await page.waitForTimeout(3500);
  const j=await page.evaluate(读工具条);
  T('工具条:', JSON.stringify(j,null,1).slice(0,5000));

  // 逐枚 hover 读 tooltip
  const 点位=await page.evaluate(()=>{const 条=[...document.querySelectorAll('div')]
    .filter(e=>{const r=e.getBoundingClientRect(); const s=getComputedStyle(e);
      return r.y>495&&r.y<530&&r.width>800&&r.height>40&&r.height<90&&s.display==='flex'
        &&(e.innerText||'').includes('00:00');})
    .sort((a,b)=>b.getBoundingClientRect().width-a.getBoundingClientRect().width)[0];
    if(!条) return [];
    const R=(e)=>{const r=e.getBoundingClientRect();return [r.x+r.width/2, r.y+r.height/2];};
    return [...条.querySelectorAll('button,[role="button"]')].map((e,i)=>({i, 框:R(e),
      文本:(e.innerText||'').trim().slice(0,8), title:e.getAttribute('title')}));});
  T('点位:', JSON.stringify(点位));
  const 读提示=()=>[...document.querySelectorAll('[role="tooltip"],[class*="Tooltip"],[class*="tooltip"]')]
    .filter(e=>{const r=e.getBoundingClientRect(); const s=getComputedStyle(e);
      return r.width>0 && +s.opacity>0.5 && (e.innerText||'').trim();})
    .map(e=>(e.innerText||'').trim().slice(0,20));
  const 结果=[];
  for(const p of 点位){
    await page.mouse.move(p.框[0], p.框[1]); await page.waitForTimeout(750);
    结果.push({i:p.i, 文本:p.文本, title:p.title, 提示:await page.evaluate(读提示)});
  }
  T('逐枚 hover 结果:', JSON.stringify(结果,null,1).slice(0,3500));
  await page.screenshot({path:E('gj6-a-工具条读数.png')});
} finally { await browser.close(); }
