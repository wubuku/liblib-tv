import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

// 抓手工具态读数：viewport 矩阵 + 7 枚按钮的激活状态 + 常驻提示条
const 状 = (标) => {
  const v=document.querySelector('.react-flow__viewport');
  const m=v?/matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform||''):null;
  const 按钮={};
  ['添加节点','移动','素材库','角色造型室','生成历史','快捷键','教程'].forEach(n=>{
    const b=document.querySelector(`button[aria-label="${n}"]`); if(!b) return;
    const s=getComputedStyle(b);
    按钮[n]={ariaPressed:b.getAttribute('aria-pressed'),
      背景:s.backgroundColor, 边框:s.borderColor, 类:(b.className||'').toString().slice(0,60)};
  });
  const 提示条=[...document.querySelectorAll('*')].filter(e=>e.children.length===0
    && ['移动','V','抓手工具','H'].includes((e.innerText||'').trim())
    && e.getBoundingClientRect().width>0)
    .map(e=>{const r=e.getBoundingClientRect();
      return {文字:(e.innerText||'').trim(), 框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)]};});
  return {标, 矩阵:m?m[1]:null, 按钮, 提示条};
};

// 在画布空白处拖 200px，看 viewport 平移了多少
const 拖画布 = async (x0,y0,dx,dy) => {
  const 前=await page.evaluate(()=>{const v=document.querySelector('.react-flow__viewport');
    const m=/matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform||'');
    return m?m[1].split(',').map(Number):null;});
  await page.mouse.move(x0,y0); await page.waitForTimeout(250);
  await page.mouse.down(); await page.waitForTimeout(150);
  const 帧=8;
  for(let i=1;i<=帧;i++){ await page.mouse.move(x0+dx*i/帧, y0+dy*i/帧); await page.waitForTimeout(170); }
  await page.mouse.up(); await page.waitForTimeout(700);
  const 后=await page.evaluate(()=>{const v=document.querySelector('.react-flow__viewport');
    const m=/matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform||'');
    return m?m[1].split(',').map(Number):null;});
  return {前, 后, 平移: 前&&后? [+(后[4]-前[4]).toFixed(2), +(后[5]-前[5]).toFixed(2)] : null};
};

try {
  await open(page,B); await closePromos(page); await 稳();
  await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  T('【A 初始】', JSON.stringify(await page.evaluate(状,'A')).slice(0,1200));

  // 默认态拖画布
  const d1=await 拖画布(300,200,200,0);
  T('【B 默认态 拖画布 +200px】', JSON.stringify(d1));
  await page.screenshot({path:E('gm2-a-默认拖画布后.png')});
  await 拖画布(500,200,-200,0);   // 复原
  T('【C 复原后】', JSON.stringify(await page.evaluate(状,'C')).slice(0,600));

  // 开「移动」工具
  await page.locator('button[aria-label="移动"]').first().click(); await page.waitForTimeout(1600);
  T('【D 点「移动」之后】', JSON.stringify(await page.evaluate(状,'D')).slice(0,1600));
  await page.screenshot({path:E('gm2-b-开抓手工具.png')});
  await page.screenshot({path:E('gm2-c-抓手工具提示条.png'),
    clip:{x:560,y:700,width:500,height:80}});

  const d2=await 拖画布(300,200,200,0);
  T('【E 抓手态 拖画布 +200px】', JSON.stringify(d2));
  await page.screenshot({path:E('gm2-d-抓手拖画布后.png')});
  await 拖画布(500,200,-200,0);

  // ⭐ 复原：按 V / 按 H 分别试
  await page.keyboard.press('v'); await page.waitForTimeout(1200);
  T('【F 按 v 之后】', JSON.stringify(await page.evaluate(状,'F')).slice(0,1200));
  await page.screenshot({path:E('gm2-e-按v之后.png'), clip:{x:560,y:700,width:500,height:80}});
} finally { await browser.close(); }
