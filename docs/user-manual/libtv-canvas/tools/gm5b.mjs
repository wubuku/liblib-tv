// GM-5b：底栏按钮的「全集」取证 —— ⭐ 上一批的教训：**按名字白名单扫会漏掉"消失"**。
// 「移动」按钮按 H 后从 DOM 消失，所以这里扫**所有** button，不按 aria-label 过滤。
import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
async function 稳(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

// ⭐ 底栏 = 「y 落在同一条带上的 button 们」。用位置聚类，不用 aria 名白名单。
const 底栏全集 = () => page.evaluate(()=>{
  const 全部=[...document.querySelectorAll('button')].map(b=>{
    const r=b.getBoundingClientRect(); if(r.width<=0||r.height<=0) return null;
    return {b, x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)};})
    .filter(Boolean);
  // 底栏带：y 相同且 button 数最多的一组
  const 按y={}; 全部.forEach(e=>{ (按y[e.y]=按y[e.y]||[]).push(e); });
  const 组=Object.entries(按y).sort((a,b)=>b[1].length-a[1].length);
  const 最大=组[0];
  if(!最大 || 最大[1].length<4) return {错误:'没找到底栏带', 各组:组.slice(0,6).map(g=>[g[0],g[1].length])};
  const 带=最大[1].sort((a,b)=>a.x-b.x);
  // 这个带的容器（判它挂在谁身上）
  let 容器=null;
  const 首=带[0].b;
  const cand=[...document.querySelectorAll('*')].filter(x=>x!==首 && 带.every(e=>x.contains(e.b)));
  const 选=cand.sort((a,b)=>{const ra=a.getBoundingClientRect(), rb=b.getBoundingClientRect();
    return (ra.width*ra.height)-(rb.width*rb.height);})[0];
  if(选){const r=选.getBoundingClientRect();
    容器={tag:选.tagName, class:String(选.className).slice(0,170),
      框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
      innerText:选.innerText.replace(/\s+/g,' ').slice(0,80)};}
  return {
    带y:最大[0], 按钮数:带.length, 容器,
    按钮:带.map(e=>({aria:e.b.getAttribute('aria-label'), title:e.b.getAttribute('title'),
      框:[e.x,e.y,e.w,e.h], 背景:getComputedStyle(e.b).backgroundColor,
      描边:getComputedStyle(e.b).borderColor, disabled:e.b.disabled,
      svg:e.b.querySelectorAll('svg').length,
      // 激活的高亮在 span 上还是 button 上？
      span背景:e.b.querySelector('span')?getComputedStyle(e.b.querySelector('span')).backgroundColor:null})),
    // ⭐ 逐个位置问 elementFromPoint 那里现在是什么（判"消失"是没了还是被换）
    落点:带.map(e=>{const h=document.elementFromPoint(e.x+Math.round(e.w/2), e.y+Math.round(e.h/2));
      let 属=h, n=0; while(属 && n<6){ if(带.some(k=>k.b===属)) break; 属=属.parentElement; n++; }
      return {在:e.x, 命中:h?h.tagName:null,
        命中aria:h?(h.closest('button')?.getAttribute('aria-label')??null):null,
        是底栏某枚:属?带.some(k=>k.b===属):false,
        命中class:h?String(h.className).slice(0,90):null};}),
  };
});

try {
  await open(page,B); await closePromos(page); T('节点数', await 稳());
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);

  T('A 初始底栏全集:', await 底栏全集());
  await page.locator('button[aria-label="移动"]').first().click(); await page.waitForTimeout(1500);
  T('B 点「移动」后:', await 底栏全集());
  await page.keyboard.press('h'); await page.waitForTimeout(1400);
  T('C 按 h 后:', await 底栏全集());
  await page.screenshot({path: resolve('tools','.evidence','gm5b-c-按h后底栏全图.png')});
  // ⭐ 按 H 后还能不能换回去？点「抓手工具」提示条里的字行不行 / 空格行不行
  await page.keyboard.press('v'); await page.waitForTimeout(1300);
  T('D 按 v 回移动:', await 底栏全集());
  // ⭐ 抓手段下有没有「抓手」按钮？扫全页 aria-label 含 抓/手 的
  T('E 全页 aria-label 含「抓」或「手」的按钮:', await page.evaluate(()=>
    [...document.querySelectorAll('[aria-label]')].map(e=>e.getAttribute('aria-label'))
      .filter(s=>s&&/抓|手/.test(s))));
  T('F 收尾 节点数（必须还是 12）:', await page.locator('.react-flow__node').count());
} finally { await browser.close(); }
