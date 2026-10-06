import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const EMPTY='https://www.liblib.tv/canvas?spaceId=10354929&projectId=13249957f18e42ce90d3b913e985cef0';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
try {
  await open(page,EMPTY); await closePromos(page);
  let p=-1; for(let i=0;i<12;i++){const n=await page.locator('.react-flow__node').count(); if(n===p) break; p=n; await page.waitForTimeout(900);}
  // 抽屉当前状态 + 芯片5 落点
  const st=await page.evaluate(()=>{
    const d=document.querySelector('.chat-welcome-root');
    const b5=[...document.querySelectorAll('button')].find(e=>e.innerText.trim()==='智能剪辑');
    const r=b5&&b5.getBoundingClientRect();
    const hit=r?document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2)):null;
    return {抽屉: d? (()=>{const q=d.getBoundingClientRect();return [q.x,q.y,q.width,q.height].map(Math.round);})():null,
      芯片5框: r?[r.x,r.y,r.width,r.height].map(Math.round):null,
      落点: hit?(hit.innerText||hit.tagName).trim().slice(0,25):null,
      属主是芯片5: hit?(b5.contains(hit)||hit===b5):null};
  });
  T('当前状态:', st);
  // 如果抽屉在，点「关闭」把它收掉，然后再想办法打开
  if (st.抽屉) {
    await page.locator('button[aria-label="关闭"]').last().click(); await page.waitForTimeout(1500);
    T('点关闭后抽屉:', await page.evaluate(()=>{const d=document.querySelector('.chat-welcome-root');
      return d?(()=>{const q=d.getBoundingClientRect();return [q.x,q.y,q.width,q.height].map(Math.round);})():null;}));
    // 找「停靠到右侧」或再点关闭看是否收起
    const 停靠=page.locator('button[aria-label="停靠到右侧"]');
    T('停靠到右侧 按钮数:', await 停靠.count());
  }
  // 现在抽屉收起了 → 拍干净的芯片排（已有）
  // 再用底栏的 TV Director 入口重新打开抽屉，验证它又会压住
  T('找 TV Director 入口…');
} finally { await browser.close(); }
