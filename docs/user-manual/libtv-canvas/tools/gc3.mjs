import { launch, open, closePromos } from './lib.mjs';
const EMPTY='https://www.liblib.tv/canvas?spaceId=10354929&projectId=13249957f18e42ce90d3b913e985cef0';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
try {
  await open(page,EMPTY); await closePromos(page);
  let p=-1; for(let i=0;i<12;i++){const n=await page.locator('.react-flow__node').count();
    if(n===p) break; p=n; await page.waitForTimeout(900);}
  // 画布上有没有 TV Director 抽屉盖着？
  const 抽屉=await page.evaluate(()=>{
    const r=document.querySelector('.chat-welcome-root');
    if(!r) return {有无:false};
    const b=r.getBoundingClientRect(); const cs=getComputedStyle(r);
    // 往上找遮罩
    let p=r.parentElement, ov=[];
    for(let i=0;i<5&&p;i++){const q=p.getBoundingClientRect(); ov.push({i,tag:p.tagName,
      cls:(p.className||'').toString().slice(0,90), box:[q.x,q.y,q.width,q.height].map(Math.round),
      z:getComputedStyle(p).zIndex, pos:getComputedStyle(p).position}); p=p.parentElement;}
    return {有无:true, box:[b.x,b.y,b.width,b.height].map(Math.round), 文字:(r.innerText||'').trim().slice(0,120), 祖先:ov};
  });
  T('TV Director 抽屉:', 抽屉);
  // 芯片在不在？被谁挡？
  const 挡=await page.evaluate(()=>{
    const 词=['图片生成','视频生成','音频生成','剧本生成','智能剪辑'];
    return 词.map(w=>{
      const b=[...document.querySelectorAll('button')].find(e=>e.innerText.trim()===w);
      if(!b) return {词:w,存在:false};
      const r=b.getBoundingClientRect();
      const cx=Math.round(r.x+r.width/2), cy=Math.round(r.y+r.height/2);
      const hit=document.elementFromPoint(cx,cy);
      const 属主=hit?(hit.innerText||hit.tagName).trim().slice(0,30):null;
      const inChip = b.contains(hit)||hit===b;
      // 芯片 z-index 链
      let z=[]; let p=b;
      for(let i=0;i<6&&p;i++){z.push(getComputedStyle(p).zIndex); p=p.parentElement;}
      return {词:w, 存在:true, box:[r.x,r.y,r.width,r.height].map(Math.round),
        落点属主:属主, 属主是芯片本身:inChip, 芯片z链:z};
    });
  });
  T('五枚芯片落点自证:', 挡);
} finally { await browser.close(); }
