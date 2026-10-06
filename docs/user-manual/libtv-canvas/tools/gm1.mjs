import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

const 浮层 = (标) => {
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  return {标,
    面板:[...document.querySelectorAll('div')].filter(e=>{
      const s=getComputedStyle(e), r=e.getBoundingClientRect();
      return r.width>=200&&r.width<=1400&&r.height>=120&&r.height<=900
        &&(s.position==='fixed'||s.position==='absolute')&&+s.opacity>0.5
        &&+s.zIndex>=40&&r.x<1440&&r.y<900;})
    .sort((a,b)=>{const q=b.getBoundingClientRect(),p2=a.getBoundingClientRect();
      return q.width*q.height-p2.width*p2.height;})
    .slice(0,3).map(e=>({cls:(e.className||'').toString().slice(0,60), z:getComputedStyle(e).zIndex,
      框:R(e), 文字:(e.innerText||'').trim().replace(/\n{2,}/g,' | ').slice(0,220)})),
    尾文:document.body.innerText.replace(/\n{2,}/g,'\n').slice(-300)};
};
const 提示 = () => [...document.querySelectorAll('[role="tooltip"]')]
  .filter(e=>{const r=e.getBoundingClientRect(); return r.width>0 && +getComputedStyle(e).opacity>0.5;})
  .map(e=>(e.innerText||'').trim().slice(0,40));

const 按钮=['添加节点','移动','素材库','角色造型室','生成历史','快捷键','教程'];

try {
  await open(page,B); await closePromos(page); await 稳();
  T('【基准】', await page.evaluate(浮层,'基准'));

  // 逐枚 hover 读 tooltip（⛔ 只悬停）
  const 表=[];
  for (const 名 of 按钮) {
    const b=page.locator(`button[aria-label="${名}"]`).first();
    const bb=await b.boundingBox();
    if(!bb){ 表.push({名, 错:'没有框'}); continue; }
    await page.mouse.move(bb.x+bb.width/2, bb.y+bb.height/2);
    await page.waitForTimeout(800);
    表.push({名, 框:[Math.round(bb.x),Math.round(bb.y),Math.round(bb.width),Math.round(bb.height)],
      提示:(await page.evaluate(提示)).join(' / ')});
    await page.mouse.move(700, 400); await page.waitForTimeout(400);
  }
  T('【7 枚按钮逐枚 hover】', JSON.stringify(表,null,1));
  await page.screenshot({path:E('gm1-a-底栏7枚.png'), clip:{x:560,y:745,width:310,height:56}});

  // 点「移动」—— 本手册从未验过的一枚
  await page.locator('button[aria-label="移动"]').first().click(); await page.waitForTimeout(2200);
  T('【点「移动」之后】', await page.evaluate(浮层,'点移动'));
  await page.screenshot({path:E('gm1-b-点移动.png')});
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  T('【Esc 之后】', await page.evaluate(浮层,'移动后Esc'));
  // 关掉键在哪
  T('关掉类按钮:', await page.evaluate(()=>[...document.querySelectorAll('button')]
    .filter(b=>/关闭|close|取消|✕|×/i.test(b.getAttribute('aria-label')||b.getAttribute('title')||b.innerText||''))
    .map(b=>{const r=b.getBoundingClientRect();
      return {aria:b.getAttribute('aria-label'), title:b.getAttribute('title'),
        框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
        可见:getComputedStyle(b).opacity};})));
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);

  // 点「素材库」
  await page.locator('button[aria-label="素材库"]').first().click(); await page.waitForTimeout(2400);
  T('【点「素材库」之后】', await page.evaluate(浮层,'点素材库'));
  await page.screenshot({path:E('gm1-c-点素材库.png')});
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  T('【复原】', await page.evaluate(浮层,'复原'));
} finally { await browser.close(); }
