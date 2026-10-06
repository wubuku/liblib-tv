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
  // 基线：先看工作流态下点节点行有没有「对话」
  const 基线=await page.evaluate(()=>[...document.querySelectorAll('button')]
    .filter(b=>(b.innerText||'').trim()==='对话' && b.getBoundingClientRect().width>0)
    .map(b=>{const r=b.getBoundingClientRect();return {box:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)], op:getComputedStyle(b).opacity};}));
  T('⭐ 工作流态下可见的「对话」按钮:', 基线, '（空＝工作流态没有这枚按钮）');
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3000);
  const d=await page.evaluate(()=>{
    const 行=[...document.querySelectorAll('div.group')].find(e=>e.querySelector('button')&&
      (e.innerText||'').includes('图片节点 2') &&
      [...e.querySelectorAll('button')].some(b=>(b.innerText||'').trim()==='对话'));
    if(!行) return null; const b=[...行.querySelectorAll('button')].find(x=>(x.innerText||'').trim()==='对话');
    const r=b.getBoundingClientRect(); return {box:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)]};});
  T('故事板态 对话按钮:', d);
  if(d){
    await page.mouse.move(d.box[0]+d.box[2]/2, d.box[1]+d.box[3]/2); await page.waitForTimeout(700);
    await page.mouse.click(d.box[0]+d.box[2]/2, d.box[1]+d.box[3]/2);
    await page.waitForTimeout(3200);
    const 附件=await page.evaluate(()=>{
      // 输入框区域内的所有小 pill
      const inp=document.querySelector('textarea')||document.querySelector('[contenteditable="true"]');
      const base=inp?inp.getBoundingClientRect():null;
      const pills=[...document.querySelectorAll('*')].filter(e=>{
        const r=e.getBoundingClientRect();
        return r.width>20&&r.width<200&&r.height>=16&&r.height<30&&e.children.length<=2 &&
          /^(图片节点|视频节点|文本节点|音频节点)/.test((e.innerText||'').trim());})
        .map(e=>{const r=e.getBoundingClientRect();return {t:(e.innerText||'').trim().slice(0,14),
          box:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)]};});
      return {输入框框: base?[Math.round(base.x),Math.round(base.y),Math.round(base.width),Math.round(base.height)]:null, pills};});
    T('附件 chip:', 附件);
    // 提交按钮状态（⛔ 只读不点）
    T('⛔ 提交按钮状态（只读）:', await page.evaluate(()=>{
      const bs=[...document.querySelectorAll('button')].map(b=>{const r=b.getBoundingClientRect();
        return {aria:b.getAttribute('aria-label'), t:(b.innerText||'').trim().slice(0,6),
          disabled:b.disabled, op:getComputedStyle(b).opacity,
          box:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)]};})
        .filter(o=>o.box[0]>1080&&o.box[1]>700&&o.box[2]>0);
      return bs;}));
    await page.screenshot({path:E('gh1-故事板-点对话之后.png'), clip:{x:1000,y:140,width:440,height:680}});
    console.log('  拍 gh1');
  }
} finally { await browser.close(); }
