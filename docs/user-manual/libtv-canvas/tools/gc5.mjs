import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const EMPTY='https://www.liblib.tv/canvas?spaceId=10354929&projectId=13249957f18e42ce90d3b913e985cef0';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
const 自证=()=>page.evaluate(()=>{
  const 词=['图片生成','视频生成','音频生成','剧本生成','智能剪辑'];
  return 词.map(w=>{
    const b=[...document.querySelectorAll('button')].find(e=>e.innerText.trim()===w);
    if(!b) return {词:w,存在:false};
    const r=b.getBoundingClientRect(); const cx=Math.round(r.x+r.width/2), cy=Math.round(r.y+r.height/2);
    const hit=document.elementFromPoint(cx,cy);
    return {词:w, 落点属主: hit?(hit.innerText||hit.tagName).trim().slice(0,20):null, 属主是芯片本身: b.contains(hit)||hit===b};
  });
});
try {
  await open(page,EMPTY); await closePromos(page);
  let p=-1; for(let i=0;i<12;i++){const n=await page.locator('.react-flow__node').count(); if(n===p) break; p=n; await page.waitForTimeout(900);}
  T('关抽屉前:', await 自证());
  // 点抽屉的关闭
  const cb=page.locator('button[aria-label="关闭"]').last();
  T('关闭按钮数:', await page.locator('button[aria-label="关闭"]').count());
  await cb.click(); await page.waitForTimeout(2000);
  T('抽屉还在吗:', await page.evaluate(()=>!!document.querySelector('.chat-welcome-root')));
  T('关抽屉后:', await 自证());
  // 图：关掉抽屉后的芯片整排（干净的）
  await page.screenshot({path:E('gc3-芯片排-无遮挡.png'), clip:{x:180,y:330,width:1080,height:230}});
  console.log('  拍 gc3');
  // 现在点第5枚
  const net=[]; page.on('request',r=>{const u=r.url(); if(/generate|submit|task|media/.test(u)) net.push(r.method()+' '+u.replace('https://api.liblib.tv',''));});
  const b5=page.locator('button').filter({hasText:/^智能剪辑$/}).first();
  const bx=await b5.boundingBox(); T('第5枚框:', bx);
  await b5.click(); await page.waitForTimeout(3000);
  T('点后 节点数:', await page.locator('.react-flow__node').count());
  T('节点类型:', await page.evaluate(()=>[...document.querySelectorAll('.react-flow__node')].map(n=>(n.className||'').match(/react-flow__node-([a-z0-9-]+)/)?.[1])));
  T('请求:', net);
} finally { await browser.close(); }
