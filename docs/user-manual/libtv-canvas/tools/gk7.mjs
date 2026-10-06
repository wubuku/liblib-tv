import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

const 编辑态 = () => {
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const p=[...document.querySelectorAll('.node-floating-ui')].find(e=>{
    const r=e.getBoundingClientRect();
    return r.height>=180 && /高级设置/.test(e.innerText||'');});
  if(!p) return {无:true};
  return {框:R(p), 文字:(p.innerText||'').trim().replace(/\n{2,}/g,' | ').slice(0,200)};
};
const 落点=(x,y)=>page.evaluate(([x,y])=>{const h=document.elementFromPoint(x,y);
  if(!h) return null; let p=h; const 链=[];
  for(let k=0;k<4&&p;k++){链.push(p.tagName+'.'+((p.className||'').toString().slice(0,34)));
    p=p.parentElement;} return 链;},[x,y]);

try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);

  // ① 裸坐标点
  T('落点(58,140) 归属链:', await 落点(58,140));
  await page.mouse.click(58, 140); await page.waitForTimeout(2400);
  T('【① 裸坐标 mouse.click(58,140)】', await page.evaluate(编辑态));
  await page.screenshot({path:E('gk7-a-裸坐标点音频卡.png'),
    clip:{x:0,y:40,width:760,height:420}});

  await page.keyboard.press('Escape'); await page.waitForTimeout(1600);
  // ② locator 点（同一枚）
  const 卡=page.locator('.assetboard-panel button', {hasText:'音频节点 1'});
  T('locator 命中数:', await 卡.count());
  await 卡.first().click(); await page.waitForTimeout(2400);
  T('【② locator.click 第一枚】', await page.evaluate(编辑态));
  await page.screenshot({path:E('gk7-b-locator点音频卡.png'),
    clip:{x:0,y:40,width:760,height:420}});

  await page.keyboard.press('Escape'); await page.waitForTimeout(1600);
  // ③ 第二枚
  await 卡.nth(1).click(); await page.waitForTimeout(2400);
  T('【③ locator.click 第二枚】', await page.evaluate(编辑态));
  await page.screenshot({path:E('gk7-c-locator点第二枚.png'),
    clip:{x:0,y:40,width:760,height:420}});
} finally { await browser.close(); }
