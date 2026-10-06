import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}
const 落点=async(sel)=>page.evaluate((s)=>{
  const b=document.querySelector(s); if(!b) return null;
  const r=b.getBoundingClientRect(); const h=document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2));
  return {框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
    落点:(h?(h.getAttribute('aria-label')||h.innerText||h.tagName).trim().slice(0,16):null),
    属主是按钮: h?(b===h||b.contains(h)):false};}, sel);
try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  T('抽屉开 剪辑按钮落点:', await 落点('button[aria-label="剪辑"]'));
  T('抽屉开 放大视频落点:', await 落点('button[aria-label="放大视频"]'));
  await page.screenshot({path:E('gi2-视频列-剪辑按钮被挡.png'), clip:{x:960,y:40,width:480,height:770}});
  console.log('  拍 gi2（遮挡态）');
  // ⭐ 关抽屉
  const 关=await page.evaluate(()=>{const bs=[...document.querySelectorAll('button[aria-label="关闭"]')]
    .filter(b=>{const r=b.getBoundingClientRect();return r.width>0&&r.height>0;});
    if(!bs.length) return false; bs[bs.length-1].click(); return true;});
  T('点了关闭 =', 关); await page.waitForTimeout(1800);
  T('抽屉现在:', await page.evaluate(()=>{const d=document.querySelector('.copilotKitChat');
    return d?(()=>{const r=d.getBoundingClientRect();return [Math.round(r.x),Math.round(r.width)];})():null;}));
  T('⭐ 关抽屉后 剪辑按钮落点:', await 落点('button[aria-label="剪辑"]'));
  T('⭐ 关抽屉后 放大视频落点:', await 落点('button[aria-label="放大视频"]'));
  // hover 拿 tooltip
  for (const [名, sel] of [['剪辑','button[aria-label="剪辑"]'],['放大视频','button[aria-label="放大视频"]']]) {
    const b=page.locator(sel).first();
    const bx=await b.boundingBox();
    if(!bx){ T(`${名}: 无框`); continue; }
    await page.mouse.move(bx.x+bx.width/2, bx.y+bx.height/2); await page.waitForTimeout(1100);
    T(`⭐ ${名} hover →:`, await page.evaluate(()=>[...document.querySelectorAll('[role="tooltip"],.mantine-Tooltip-tooltip')]
      .filter(e=>e.getBoundingClientRect().width>0).map(e=>(e.innerText||'').trim())));
  }
  await page.screenshot({path:E('gi3-视频列-剪辑按钮可点.png'), clip:{x:960,y:40,width:480,height:770}});
  console.log('  拍 gi3（关抽屉后）');
  await page.screenshot({path:E('gi4-故事板四列全景.png'), clip:{x:0,y:0,width:1440,height:810}});
  console.log('  拍 gi4');
} finally { await browser.close(); }
