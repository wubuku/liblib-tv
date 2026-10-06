import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

const 探针 = () => {
  const btn=document.querySelector('button[aria-label="放大视频"]');
  if(!btn) return {错:'没有放大视频按钮'};
  const r=btn.getBoundingClientRect();
  const cx=Math.round(r.x+r.width/2), cy=Math.round(r.y+r.height/2);
  const h=document.elementFromPoint(cx,cy);
  // 页面里所有 position:fixed / absolute 的高层容器
  const 浮层=[...document.querySelectorAll('body *')].filter(e=>{
    const s=getComputedStyle(e); const q=e.getBoundingClientRect();
    return (s.position==='fixed') && q.width>200 && q.height>120 && q.width<2000 && s.zIndex!=='auto';
  }).map(e=>{const q=e.getBoundingClientRect();
    return {tag:e.tagName, cls:(e.className||'').toString().slice(0,80), z:getComputedStyle(e).zIndex,
      box:[Math.round(q.x),Math.round(q.y),Math.round(q.width),Math.round(q.height)]};});
  return {框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
    aria:btn.getAttribute('aria-label'), 可见:getComputedStyle(btn).opacity,
    落点: h?{tag:h.tagName, cls:(h.className||'').toString().slice(0,60), t:(h.innerText||'').trim().slice(0,20)}:null,
    浮层};
};

try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);

  T('【点之前·抽屉开着】', await page.evaluate(探针));
  await page.screenshot({path:E('gj1-a-放大视频-抽屉开着.png'), clip:{x:960,y:40,width:480,height:120}});

  // 关抽屉
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  T('【Esc 之后】', await page.evaluate(探针));
  const 抽屉框 = await page.evaluate(()=>{const d=document.querySelector('.copilotKitChat');
    if(!d) return 'DOM 里没有 .copilotKitChat'; const r=d.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];});
  T('抽屉框:', 抽屉框);
  await page.screenshot({path:E('gj1-b-放大视频-抽屉关掉.png'), clip:{x:960,y:40,width:480,height:120}});

  // 点「放大视频」
  const btn = page.locator('button[aria-label="放大视频"]');
  const n = await btn.count();
  T('放大视频按钮数:', n);
  if(n===1){
    await btn.click(); await page.waitForTimeout(2600);
    T('【点开之后】', await page.evaluate(探针));
    await page.screenshot({path:E('gj1-c-点开之后-全屏.png')});
    const 文 = await page.evaluate(()=>document.body.innerText.replace(/\n{2,}/g,'\n').slice(0,2600));
    T('【点开之后可见文字】', 文);
  }
} finally { await browser.close(); }
