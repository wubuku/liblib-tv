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
  // 顶栏两枚按钮的完整状态
  const 顶=await page.evaluate(()=>['工作流','故事板'].map(a=>{
    const b=document.querySelector(`button[aria-label="${a}"]`);
    if(!b) return {a, 存在:false};
    const r=b.getBoundingClientRect(); const cs=getComputedStyle(b);
    return {a, 框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
      ariaPressed:b.getAttribute('aria-pressed'), ariaSelected:b.getAttribute('aria-selected'),
      dataState:b.getAttribute('data-state'), bg:cs.backgroundColor, 文字:(b.innerText||'').trim()};}));
  T('顶栏两枚（工作流态）:', 顶);
  // URL 有没有模式参数
  T('URL:', await page.evaluate(()=>location.href));
  // 切到故事板，看按钮状态变化 + 栏目
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3000);
  T('顶栏两枚（故事板态）:', await page.evaluate(()=>['工作流','故事板'].map(a=>{
    const b=document.querySelector(`button[aria-label="${a}"]`);
    const r=b.getBoundingClientRect(); const cs=getComputedStyle(b);
    return {a, ariaPressed:b.getAttribute('aria-pressed'), dataState:b.getAttribute('data-state'),
      bg:cs.backgroundColor, cls:(b.className||'').toString().slice(0,150)};})));
  T('故事板栏目:', await page.evaluate(()=>{
    // 找出分栏标题
    const t=[...document.querySelectorAll('*')].filter(e=>e.children.length===0 &&
      /^(音频|文本|图片|视频|剪辑|全部|对话)$/.test((e.innerText||'').trim()));
    return t.map(e=>{const r=e.getBoundingClientRect();return {t:e.innerText.trim(),
      框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)]};}).slice(0,12);}));
  await page.screenshot({path:E('gg1-故事板态.png'), clip:{x:0,y:0,width:1440,height:620}});
  console.log('  拍 gg1');
  T('URL（故事板）:', await page.evaluate(()=>location.href));
  // ⭐ 故事板态下节点还能不能点
  const n1=await page.evaluate(()=>{const n=document.querySelector('.react-flow__node-text');
    const r=n.getBoundingClientRect(); const hit=document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2));
    return {节点框:[Math.round(r.x),Math.round(r.y)], 落点:(hit.innerText||hit.tagName).trim().slice(0,20),
      属主是节点:n.contains(hit)||hit===n};});
  T('故事板态下点节点:', n1);
} finally { await browser.close(); }
