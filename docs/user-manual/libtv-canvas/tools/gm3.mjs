import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

// ⭐ 缺陷 526：先找一个**确实是画布空白**的落点（elementFromPoint 落在 pane 自己身上）
const 找空白 = () => {
  const pane=document.querySelector('.react-flow__pane');
  if(!pane) return null;
  const r=pane.getBoundingClientRect();
  for(let y=Math.round(r.y)+8; y<Math.round(r.bottom)-8; y+=14){
    for(let x=Math.round(r.x)+8; x<Math.round(r.right)-8; x+=14){
      const h=document.elementFromPoint(x,y);
      if(h && (h===pane || h.classList?.contains('react-flow__pane'))) return [x,y];
    }
  }
  return null;
};
const 矩阵 = () => page.evaluate(()=>{const v=document.querySelector('.react-flow__viewport');
  const m=/matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform||'');
  return m?m[1].split(',').map(Number):null;});
const 工具条 = () => page.evaluate(()=>[...document.querySelectorAll('*')]
  .filter(e=>e.children.length===0 && ['移动','V','抓手工具','H'].includes((e.innerText||'').trim())
    && e.getBoundingClientRect().width>0)
  .map(e=>{const r=e.getBoundingClientRect();
    return {文字:(e.innerText||'').trim(), 框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)]};}));
const 激活 = () => page.evaluate(()=>{const o={};
  ['添加节点','移动','素材库','角色造型室','生成历史','快捷键','教程'].forEach(n=>{
    const b=document.querySelector(`button[aria-label="${n}"]`); if(!b) return;
    o[n]=getComputedStyle(b).backgroundColor;}); return o;});

const 拖 = async (p,dx) => {
  const 前=await 矩阵();
  await page.mouse.move(p[0],p[1]); await page.waitForTimeout(260);
  await page.mouse.down(); await page.waitForTimeout(160);
  for(let i=1;i<=8;i++){ await page.mouse.move(p[0]+dx*i/8, p[1]); await page.waitForTimeout(170); }
  await page.mouse.up(); await page.waitForTimeout(700);
  const 后=await 矩阵();
  return {平移: 前&&后? [+(后[4]-前[4]).toFixed(2), +(后[5]-前[5]).toFixed(2)] : null};
};

try {
  await open(page,B); await closePromos(page); await 稳();
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  const 空=await page.evaluate(找空白);
  T('找到的画布空白落点:', 空);
  T('A 默认态 激活按钮:', await 激活());

  const d1=await 拖(空,200); T('B 默认态 在空白处拖 +200px:', JSON.stringify(d1));
  await 拖([空[0]+200,空[1]],-200);

  await page.locator('button[aria-label="移动"]').first().click(); await page.waitForTimeout(1500);
  T('C 点「移动」后 激活按钮:', await 激活());
  T('C 常驻提示条:', await 工具条());
  await page.screenshot({path:E('gm3-a-抓手工具提示条.png'), clip:{x:560,y:640,width:520,height:90}});
  await page.screenshot({path:E('gm3-b-开抓手后底栏.png'), clip:{x:560,y:745,width:310,height:56}});

  const d2=await 拖(空,200); T('D 抓手态 在同一空白处拖 +200px:', JSON.stringify(d2));
  await page.screenshot({path:E('gm3-c-抓手拖后.png')});
  await 拖([空[0]+200,空[1]],-200);

  // ⭐ 按 H 换到「抓手工具」
  await page.keyboard.press('h'); await page.waitForTimeout(1400);
  T('E 按 h 之后 激活按钮:', await 激活());
  const d3=await 拖(空,200); T('F H 态 拖 +200px:', JSON.stringify(d3));
  await 拖([空[0]+200,空[1]],-200);
  T('G 复原后 激活按钮:', await 激活());
  T('G 矩阵:', (await 矩阵()).map(x=>+x.toFixed(4)));
} finally { await browser.close(); }
