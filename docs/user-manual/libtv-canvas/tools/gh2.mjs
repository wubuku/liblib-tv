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
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3000);
  // 「图片节点 2」有 2 处（[512,108] 和 [512,365]）。找含「对话」按钮的那个分栏
  const 结构=await page.evaluate(()=>{
    const c=[...document.querySelectorAll('*')].filter(e=>e.children.length===0 &&
      (e.innerText||'').trim()==='图片节点 2');
    return c.map(e=>{
      // 从标题往上找到「行」容器：父的父，量它内部所有 opacity 变化的 button
      let p=e; for(let k=0;k<3&&p;k++) p=p.parentElement;
      const r=p.getBoundingClientRect();
      const btns=[...p.querySelectorAll('button')].map(b=>{const q=b.getBoundingClientRect();
        return {t:(b.innerText||'').trim().slice(0,6), aria:b.getAttribute('aria-label'),
          op:getComputedStyle(b).opacity, box:[Math.round(q.x),Math.round(q.y),Math.round(q.width),Math.round(q.height)]};});
      return {行框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
        行class:(p.className||'').toString().slice(0,80), btns};
    });});
  T('两处「图片节点 2」所在行:', JSON.stringify(结构,null,1).slice(0,1800));
  // 选有「对话」button 的那行
  const 目标=结构.find(s=>s.btns.some(b=>/对话/.test(b.t+b.aria)));
  T('目标行:', JSON.stringify(目标));
  if(目标){
    const cx=目标.行框[0]+目标.行框[2]*0.5, cy=目标.行框[1]+14;
    await page.mouse.move(cx,cy); await page.waitForTimeout(900);
    const after=await page.evaluate(([x0,y0,w])=>{
      return [...document.querySelectorAll('button')].map(b=>{const q=b.getBoundingClientRect();
        return {t:(b.innerText||'').trim().slice(0,6), aria:b.getAttribute('aria-label'), op:getComputedStyle(b).opacity,
          box:[Math.round(q.x),Math.round(q.y),Math.round(q.width),Math.round(q.height)]};})
        .filter(o=>o.box[0]>=x0-10&&o.box[0]<=x0+w&&Math.abs(o.box[1]-y0)<26);}, [目标.行框[0],目标.行框[1]+14,目标.行框[2]]);
    T('hover 该行标题高度后可见按钮:', after);
    const d=after.find(b=>/对话/.test(b.t+b.aria||''));
    if(d){
      T('点「对话」', d.box);
      await page.mouse.click(d.box[0]+d.box[2]/2, d.box[1]+d.box[3]/2);
      await page.waitForTimeout(3200);
      T('抽屉:', await page.evaluate(()=>{const c=document.querySelector('.chat-welcome-root');
        return c?(c.innerText||'').trim().slice(0,150):'无';}));
      T('消息区:', await page.evaluate(()=>[...document.querySelectorAll('.copilotKitMessagesContainer')]
        .filter(e=>e.getBoundingClientRect().height>0).map(e=>(e.innerText||'').trim().slice(0,100))));
      await page.screenshot({path:E('gh1-故事板-点对话之后.png'), clip:{x:1000,y:140,width:440,height:680}});
      console.log('  拍 gh1');
    }
  }
} finally { await browser.close(); }
