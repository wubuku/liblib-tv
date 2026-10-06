import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const MAIN='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<12;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}
const 芯片排=()=>page.evaluate(()=>['图片生成','视频生成','音频生成','剧本生成','智能剪辑'].map(w=>{
  const b=[...document.querySelectorAll('button')].find(e=>e.innerText.trim()===w);
  return b? w : null;}).filter(Boolean).length);
try {
  // 建一张全新的空画布
  await open(page,MAIN); await closePromos(page);
  await page.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(x=>{const r=x.getBoundingClientRect();
    return r.x>160&&r.x<180&&r.y<20&&r.width>40;}); b.click();});
  await page.waitForTimeout(900);
  await page.locator('button[aria-label="新建画布"]').click(); await page.waitForTimeout(900);
  await page.locator('input[aria-label="画布名称"]').fill('GC-取证二');
  await page.keyboard.press('Enter'); await page.waitForTimeout(3200);
  const pid=await page.evaluate(()=>(location.search.match(/projectId=(\w+)/)||[])[1]);
  T('新空画布 pid:', pid, '节点数:', await 稳定(), '芯片数:', await 芯片排());
  // 此刻抽屉是开着的吗
  const 抽=await page.evaluate(()=>{const d=document.querySelector('.chat-welcome-root');
    return d?(()=>{const q=d.getBoundingClientRect();return [q.x,q.y,q.width,q.height].map(Math.round);})():null;});
  T('抽屉:', 抽);
  const 落=await page.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(e=>e.innerText.trim()==='智能剪辑');
    if(!b) return null; const r=b.getBoundingClientRect();
    const hit=document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2));
    return {框:[r.x,r.y,r.width,r.height].map(Math.round), 属主:(hit.innerText||hit.tagName).trim().slice(0,20),
      属主是芯片:b.contains(hit)||hit===b};});
  T('芯片5 落点:', 落);
  // ⭐ 拍：叠压全景
  await page.screenshot({path:E('gc1-芯片排与抽屉叠压.png'), clip:{x:180,y:330,width:1080,height:290}});
  console.log('  拍 gc1');
  // ⭐ 拍：叠压特写（这次确保有内容）
  await page.screenshot({path:E('gc2-第五枚被遮特写.png'), clip:{x:960,y:380,width:320,height:120}});
  console.log('  拍 gc2');
  // 关抽屉 → 拍干净的
  await page.locator('button[aria-label="关闭"]').last().click(); await page.waitForTimeout(1800);
  const 落2=await page.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(e=>e.innerText.trim()==='智能剪辑');
    if(!b) return null; const r=b.getBoundingClientRect();
    const hit=document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2));
    return {属主:(hit.innerText||hit.tagName).trim().slice(0,20), 属主是芯片:b.contains(hit)||hit===b};});
  T('关抽屉后 芯片5 落点:', 落2);
  await page.screenshot({path:E('gc3-芯片排-无遮挡.png'), clip:{x:180,y:330,width:1080,height:230}});
  console.log('  拍 gc3');
  T('✅ 可清理的画布名: GC-取证二', pid);
} finally { await browser.close(); }
