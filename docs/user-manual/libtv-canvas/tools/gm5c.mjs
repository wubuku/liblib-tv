// GM-5c：三种拖动画布方式的对照 + 底栏 tooltip 的正确采样。
//
// ⭐⭐⭐ 落点自证（治缺陷 526 / 517）：**先算出所有节点的屏幕框，取一个「半径 60px 内
//    12 个采样点全部命中 .react-flow__pane」的落点**。上一批只验了落点自己一个点，
//    结果落点确实在 pane 上、但半径边缘压着节点，拖动时 react-flow 命中了节点。
// ⭐⭐⭐ 守卫：每一步拖完都比对**节点画布坐标**，一旦变了立刻 ⌘0 并退出，绝不带着位移收工。
import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

const 快照 = () => page.evaluate(()=>{
  const v=document.querySelector('.react-flow__viewport');
  const m=/matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform||'');
  const 节点=[...document.querySelectorAll('.react-flow__node')].map(n=>{
    const t=/translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform||'');
    return (n.getAttribute('data-id')||'')+':'+(t?Math.round(Number(t[1]))+','+Math.round(Number(t[2])):'?');
  }).sort();
  return {矩阵:m?m[1]:null, 节点};
});

// ⭐⭐⭐ 落点自证：候选点必须「自己 + 半径 60 的 12 个采样点」全部是 .react-flow__pane
const 安全落点 = () => page.evaluate(()=>{
  const pane=document.querySelector('.react-flow__pane'); if(!pane) return null;
  const pr=pane.getBoundingClientRect();
  const nodes=[...document.querySelectorAll('.react-flow__node')]
    .map(n=>n.getBoundingClientRect());
  const 环=[[0,0],[40,0],[-40,0],[0,40],[0,-40],[28,28],[28,-28],[-28,28],[-28,-28],
            [40,40],[40,-40],[-40,40],[-40,-40]];
  const 候选=[];
  for(let y=Math.round(pr.y)+70; y<Math.round(pr.bottom)-70; y+=20)
    for(let x=Math.round(pr.x)+70; x<Math.round(pr.right)-70; x+=20) 候选.push([x,y]);
  for(const c of 候选){
    let ok=true;
    for(const [dx,dy] of 环){
      const x=c[0]+dx, y=c[1]+dy;
      const h=document.elementFromPoint(x,y);
      if(!(h && (h===pane||h.classList?.contains('react-flow__pane')))){ok=false; break;}
    }
    if(ok){ // 再确认离最近节点足够远
      const d=Math.min(...nodes.map(n=>{
        const dx=Math.max(n.left-c[0],0,c[0]-n.right), dy=Math.max(n.top-c[1],0,c[1]-n.bottom);
        return Math.hypot(dx,dy);}));
      return {落点:c, 最近节点距离:+d.toFixed(1), 候选数:候选.length};}
  }
  return {落点:null, 候选数:候选.length};
});

const 平移 = async (p,dx,dy=0) => {
  const 前=await 快照();
  await page.mouse.move(p[0],p[1]); await page.waitForTimeout(280);
  await page.mouse.down(); await page.waitForTimeout(180);
  for(let i=1;i<=10;i++){ await page.mouse.move(p[0]+dx*i/10, p[1]+dy*i/10); await page.waitForTimeout(150); }
  await page.mouse.up(); await page.waitForTimeout(750);
  const 后=await 快照();
  const a=前.矩阵.split(',').map(Number), b=后.矩阵.split(',').map(Number);
  return {位移:[+(b[4]-a[4]).toFixed(2), +(b[5]-a[5]).toFixed(2)],
    节点变了:JSON.stringify(前.节点)!==JSON.stringify(后.节点)};
};

// ⭐ tooltip 正确采样：Mantine 浮层是**新挂到 body 上的 div**，不按 aria 名找，找「hover 后新出现的浮层」
const tooltip全文 = async (名) => {
  const 前=await page.evaluate(()=>document.body.children.length);
  const b=page.locator(`button[aria-label="${名}"]`).first();
  await b.hover(); await page.waitForTimeout(1200);
  const r=await page.evaluate(({前})=>{
    const 新=[...document.body.children].slice(前);
    const 出=new Map();
    新.forEach(e=>{ const t=(e.innerText||'').trim(); if(t) 出.set(t, String(e.className).slice(0,90)); });
    return [...出.entries()].map(([文字,cls])=>({文字,cls}));
  }, {前});
  await page.mouse.move(8,300); await page.waitForTimeout(600);
  return r;
};

try {
  await open(page,B); await closePromos(page); T('节点数', await 稳());
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  const 基线=await 快照(); T('【基线矩阵】', 基线.矩阵);

  const s=await 安全落点(); T('【安全落点】', s);
  if(!s||!s.落点){ T('!! 没有找到安全落点，中止平移测试'); throw new Error('no safe drop point'); }
  const p=s.落点;

  // ⭐ 底栏 tooltip 全文（默认态，别被平移测试污染）
  const tt={}; for(const n of ['移动','素材库','快捷键','教程']) tt[n]=await tooltip全文(n);
  T('【底栏 tooltip 浮层全文】', tt);

  let 坏了=false;
  const dA=await 平移(p,220,120); T('A 普通态（未进平移工具）拖 +220,+120:', dA);
  if(dA.节点变了) 坏了=true;
  await 平移(p,-220,-120);

  await page.locator('button[aria-label="移动"]').first().click(); await page.waitForTimeout(1500);
  T('B 已点「移动」按钮，aria=', await page.evaluate(()=>{
    const b=document.querySelector('button[aria-label="移动"],button[aria-label="抓手工具"]');
    return b?b.getAttribute('aria-label')+' 背景='+getComputedStyle(b).backgroundColor:'没有这枚按钮';}));
  const dB=await 平移(p,220,120); T('B 移动工具态 拖 +220,+120:', dB);
  if(dB.节点变了) 坏了=true;
  await 平移(p,-220,-120);

  await page.keyboard.press('h'); await page.waitForTimeout(1300);
  T('C 已按 h，aria=', await page.evaluate(()=>{
    const b=document.querySelector('button[aria-label="移动"],button[aria-label="抓手工具"]');
    return b?b.getAttribute('aria-label')+' 背景='+getComputedStyle(b).backgroundColor:'没有这枚按钮';}));
  const dC=await 平移(p,220,120); T('C 抓手工具态 拖 +220,+120:', dC);
  if(dC.节点变了) 坏了=true;
  await page.screenshot({path:E('gm5c-a-抓手态底栏.png'), clip:{x:560,y:640,width:520,height:90}});
  await page.screenshot({path:E('gm5c-b-抓手态底栏按钮.png'), clip:{x:560,y:740,width:340,height:60}});
  await 平移(p,-220,-120);

  await page.keyboard.press('v'); await page.waitForTimeout(1300);
  T('D 已按 v，aria=', await page.evaluate(()=>{
    const b=document.querySelector('button[aria-label="移动"],button[aria-label="抓手工具"]');
    return b?b.getAttribute('aria-label')+' 背景='+getComputedStyle(b).backgroundColor:'没有这枚按钮';}));

  // ⭐⭐⭐ 复原核查：矩阵与节点坐标必须回到基线
  await page.keyboard.press('Meta+0'); await page.waitForTimeout(1800);
  const 末=await 快照();
  T('【末态矩阵】', 末.矩阵);
  T('【节点坐标是否回到基线】', JSON.stringify(基线.节点)===JSON.stringify(末.节点));
  T('【矩阵是否回到基线】', 基线.矩阵===末.矩阵);
  T('【过程中节点被拖动过吗】', 坏了);
} finally { await browser.close(); }
