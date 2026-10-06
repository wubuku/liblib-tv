import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

// 精确定位「资产管理」：它的文字是个 span，不是 button
const 定位 = (词) => {
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const 叶=[...document.querySelectorAll('*')].filter(e=>e.children.length===0
    && (e.innerText||'').trim()===词 && e.getBoundingClientRect().width>0);
  return 叶.map(e=>{const r=e.getBoundingClientRect();
    let p=e, 链=[]; for(let k=0;k<4&&p;k++){
      链.push({k, tag:p.tagName, cls:(p.className||'').toString().slice(0,50), 框:R(p),
        鼠标:getComputedStyle(p).cursor, PE:getComputedStyle(p).pointerEvents,
        落点:(()=>{const h=document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2));
          return h?(h.tagName+'.'+((h.className||'').toString().slice(0,26))):null;})()});
      p=p.parentElement;}
    return {词, 链};});
};

const 深读 = (a)=>{
  const b=document.querySelector(`button[aria-label="${a}"]`);
  if(!b) return {无:true};
  const 全部=(e)=>[...e.querySelectorAll('*')].slice(0,14).map(x=>({
    tag:x.tagName, cls:(x.className||'').toString().slice(0,40),
    文字:(x.innerText||'').trim().slice(0,14)}));
  const r=b.getBoundingClientRect();
  return {框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
    内部:全部(b), 外层类:b.parentElement?(b.parentElement.className||'').toString().slice(0,60):null};
};

const 提示 = () => [...document.querySelectorAll('[role="tooltip"]')]
  .filter(e=>{const r=e.getBoundingClientRect(); return r.width>0 && +getComputedStyle(e).opacity>0.5;})
  .map(e=>(e.innerText||'').trim().slice(0,40));

try {
  await open(page,B); await closePromos(page); await 稳();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);

  T('【「资产管理」定位】', JSON.stringify(await page.evaluate(定位,'资产管理'),null,1).slice(0,1800));
  T('【「积分超市」深读】', JSON.stringify(await page.evaluate(深读,'积分超市'),null,1).slice(0,1200));

  // hover 三枚，读 tooltip（⛔ 只悬停不点）
  for (const 名 of ['积分超市', '发布与分享']) {
    const b = page.locator(`button[aria-label="${名}"]`);
    const bb = await b.boundingBox();
    T(`${名} 框:`, bb && [Math.round(bb.x),Math.round(bb.y),Math.round(bb.width),Math.round(bb.height)]);
    await page.mouse.move(bb.x+bb.width/2, bb.y+bb.height/2); await page.waitForTimeout(900);
    T(`  ${名} 悬停提示:`, await page.evaluate(提示));
    await page.mouse.move(700, 500); await page.waitForTimeout(500);
  }
  await page.screenshot({path:E('gl3-a-积分超市hover.png'), clip:{x:900,y:0,width:540,height:120}});

  // 点「资产管理」—— 手册已授权的读取路径
  const 点位 = await page.evaluate(()=>{
    const e=[...document.querySelectorAll('*')].find(x=>x.children.length===0
      && (x.innerText||'').trim()==='资产管理' && x.getBoundingClientRect().width>0);
    if(!e) return null; const r=e.getBoundingClientRect();
    return [Math.round(r.x+r.width/2), Math.round(r.y+r.height/2)];});
  T('「资产管理」中心点:', 点位);
  if(点位){
    await page.mouse.click(点位[0], 点位[1]); await page.waitForTimeout(2200);
    const 读=await page.evaluate(()=>{const R=(e)=>{const r=e.getBoundingClientRect();
        return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
      return [...document.querySelectorAll('.mantine-Drawer-inner,.mantine-Drawer-content,[class*="drawer" i]')]
        .map(e=>({cls:(e.className||'').toString().slice(0,30), 框:R(e),
          宽:e.getBoundingClientRect().width, 文字:(e.innerText||'').trim().replace(/\s+/g,' ').slice(0,60)}))
        .filter(x=>x.宽>50);});
    T('【点「资产管理」之后】', JSON.stringify(读,null,1).slice(0,1500));
    await page.screenshot({path:E('gl3-b-故事板态开资产管理.png')});
  }
} finally { await browser.close(); }
