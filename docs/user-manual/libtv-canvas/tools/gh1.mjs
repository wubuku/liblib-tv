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
  // 切故事板
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3000);
  T('故事板态');
  // 找图片列里的节点行（标题「图片节点 2」）
  const 行=await page.evaluate(()=>{
    const c=[...document.querySelectorAll('*')].filter(e=>e.children.length===0 &&
      (e.innerText||'').trim()==='图片节点 2');
    if(!c.length) return null;
    return c.map(e=>{const r=e.getBoundingClientRect();
      // 往上找可 hover 的行容器
      let p=e, 行框=null;
      for(let k=0;k<6&&p;k++){const q=p.getBoundingClientRect();
        if(q.width>120&&q.height>24){行框=[Math.round(q.x),Math.round(q.y),Math.round(q.width),Math.round(q.height)];break;}
        p=p.parentElement;}
      return {框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)], 行框};});
  });
  T('「图片节点 2」出现处:', JSON.stringify(行));
  if(!行) { console.log('  没找到，退出'); }
  else {
    // ⭐ hover 那一行，找「对话」按钮
    const y = 行[0].行框 ? 行[0].行框[1] + 行[0].行框[3]/2 : 行[0].框[1]+10;
    const x = 行[0].行框 ? 行[0].行框[0] + 行[0].行框[2]/2 : 行[0].框[0]+50;
    await page.mouse.move(x, y); await page.waitForTimeout(900);
    const 对话=await page.evaluate(([px,py])=>{
      const near=[...document.querySelectorAll('button')].map(b=>{const r=b.getBoundingClientRect();
        return {t:(b.innerText||'').trim().slice(0,8), aria:b.getAttribute('aria-label'),
          op:getComputedStyle(b).opacity, pe:getComputedStyle(b).pointerEvents,
          box:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)]};})
        .filter(o=>o.box[0]>px-250 && o.box[0]<px+250 && Math.abs(o.box[1]+o.box[3]/2-py)<30 && o.box[2]>0);
      return near;}, [x,y]);
    T('该行附近的按钮（hover 后）:', 对话);
    const d=对话.find(b=>b.t==='对话'||/对话/.test(b.aria||''));
    if(d){
      T('找到「对话」:', d);
      await page.mouse.click(d.box[0]+d.box[2]/2, d.box[1]+d.box[3]/2);
      await page.waitForTimeout(3000);
      T('点后 抽屉:', await page.evaluate(()=>{const c=document.querySelector('.chat-welcome-root');
        return c?{框:(()=>{const q=c.getBoundingClientRect();return [Math.round(q.x),Math.round(q.y),Math.round(q.width),Math.round(q.height)];})(),
          文字:(c.innerText||'').trim().slice(0,200)}:'无';}));
      T('点后 输入框附件 chip:', await page.evaluate(()=>{
        const inp=document.querySelector('textarea,input[placeholder]');
        const chips=[...document.querySelectorAll('[class*="chip"],[class*="Chip"],[class*="attachment"],[class*="Attachment"]')]
          .filter(e=>e.getBoundingClientRect().width>0).map(e=>(e.innerText||'').trim().slice(0,20)).filter(Boolean);
        return {placeholder: inp?inp.getAttribute('placeholder'):null, chips:chips.slice(0,6)};}));
      T('⛔ 检查有没有自动发消息:', await page.evaluate(()=>{
        const m=[...document.querySelectorAll('.copilotKitMessagesContainer, [class*="message"]')]
          .filter(e=>e.getBoundingClientRect().height>0).map(e=>(e.innerText||'').trim().slice(0,120));
        return m.slice(0,3);}));
      await page.screenshot({path:E('gh1-故事板-点对话之后.png'), clip:{x:1000,y:140,width:440,height:680}});
      console.log('  拍 gh1');
    }
  }
} finally { await browser.close(); }
