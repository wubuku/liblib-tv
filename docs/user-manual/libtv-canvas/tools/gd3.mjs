import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const MAIN='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
const 建过的=[];
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}
async function 新空画布(名){ await open(page,MAIN); await closePromos(page);
  await page.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(x=>{const r=x.getBoundingClientRect();
    return r.x>160&&r.x<180&&r.y<20&&r.width>40;}); b.click();});
  await page.waitForTimeout(900);
  await page.locator('button[aria-label="新建画布"]').click(); await page.waitForTimeout(900);
  await page.locator('input[aria-label="画布名称"]').fill(名);
  await page.keyboard.press('Enter'); await page.waitForTimeout(3200);
  const pid=await page.evaluate(()=>(location.search.match(/projectId=(\w+)/)||[])[1]); 建过的.push({名,pid});
  await page.evaluate(()=>{const bs=[...document.querySelectorAll('button[aria-label="关闭"]')]
    .filter(b=>{const r=b.getBoundingClientRect(); return r.width>0&&r.height>0;}); if(bs.length) bs[bs.length-1].click();});
  await page.waitForTimeout(1600); await 稳定(); return pid;}
try {
  for (const w of ['剧本生成','智能剪辑']) {
    await 新空画布(`GD2-${w}`);
    const b=page.locator('button').filter({hasText:new RegExp(`^${w}$`)}).first();
    const 证=await b.evaluate(el=>{const r=el.getBoundingClientRect();
      const hit=document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2));
      return {是芯片: el.contains(hit)||hit===el};});
    T(`${w} 落点可点:`, 证);
    const net=[]; const h=r=>{const u=r.url(); if(/generate|submit|task/.test(u)) net.push(r.method()+' '+u.replace('https://api.liblib.tv',''));};
    page.on('request',h);
    await b.click(); await page.waitForTimeout(3500);
    const 稳=await 稳定();
    const 全=await page.evaluate(()=>{
      const ns=[...document.querySelectorAll('.react-flow__node')];
      return {节点数:ns.length,
        类型:ns.map(n=>(n.className||'').match(/react-flow__node-([a-z0-9-]+)/)?.[1]),
        标题:ns.map(n=>(n.innerText||'').trim().split('\n')[0]),
        框:ns.map(n=>{const r=n.getBoundingClientRect();return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];}),
        页面有这些字:(document.body.innerText||'').match(/脚本[^\n]{0,20}|智能剪辑[^\n]{0,20}/g)?.slice(0,8),
        新浮层:[...document.querySelectorAll('[class*="Modal"],[class*="Popover"],[role="dialog"]')]
          .filter(e=>e.getBoundingClientRect().height>0)
          .map(e=>({cls:(e.className||'').toString().slice(0,60), t:(e.innerText||'').trim().slice(0,60)})).slice(0,3)};
    });
    T(`${w} 结果:`, 全);
    T(`${w} 请求:`, net);
    if(全.节点数>0){ const r=全.框[0];
      await page.screenshot({path:E(`gd2-${w}.png`), clip:{x:Math.max(0,r[0]-60),y:Math.max(0,r[1]-60),
        width:Math.min(700,r[2]+120),height:Math.min(470,r[3]+120)}});
      console.log(`  拍 gd2-${w}`); }
  }
  T('建过:', 建过的.map(x=>x.名));
} finally { await browser.close(); }
