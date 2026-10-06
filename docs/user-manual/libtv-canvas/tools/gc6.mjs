import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const EMPTY='https://www.liblib.tv/canvas?spaceId=10354929&projectId=13249957f18e42ce90d3b913e985cef0';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<12;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}
try {
  // 现在 GC 画布上已有 1 个 video-clip 节点。先看它长什么样
  await open(page,EMPTY); await closePromos(page);
  T('节点数:', await 稳定());
  const n1=await page.evaluate(()=>{
    const n=document.querySelector('.react-flow__node-video-clip');
    if(!n) return null;
    const r=n.getBoundingClientRect();
    return {box:[r.x,r.y,r.width,r.height].map(Math.round), 标题:(n.innerText||'').trim().slice(0,80),
      class:(n.className||'').toString().slice(0,120)};
  });
  T('video-clip 节点:', n1);
  await page.screenshot({path:E('gc4-点芯片建出的智能剪辑节点.png'), clip:{x:Math.max(0,n1.box[0]-40),y:Math.max(0,n1.box[1]-40),width:Math.min(600,n1.box[2]+80),height:Math.min(260,n1.box[3]+80)}});
  console.log('  拍 gc4');
  // 图：无遮挡时的芯片整排（干净版，节点还在）
  await page.screenshot({path:E('gc3-芯片排-无遮挡.png'), clip:{x:180,y:330,width:1080,height:230}});
  console.log('  拍 gc3 覆盖');
} finally { await browser.close(); }
