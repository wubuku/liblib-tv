import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

const 场景 = (标签) => {
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const 层=[...document.querySelectorAll('body *')].filter(e=>{
    const s=getComputedStyle(e), r=e.getBoundingClientRect();
    return (s.position==='fixed'||s.position==='absolute') && r.width>=200 && r.height>=100
      && r.width<=2000 && r.height<=1200 && r.x<1440 && r.y<900 && +s.zIndex!==0;
  }).map(e=>({tag:e.tagName, cls:(e.className||'').toString().slice(0,70), z:getComputedStyle(e).zIndex,
    box:R(e), 文字:(e.innerText||'').trim().replace(/\s+/g,' ').slice(0,40)}));
  const vids=[...document.querySelectorAll('video')].map(v=>({box:R(v), 时长:+(v.duration||0).toFixed(1),
    当前:+(v.currentTime||0).toFixed(2), 播放:!v.paused, 静音:v.muted, 源:(v.currentSrc||'').slice(-46)}));
  const 找=(s)=>{const e=[...document.querySelectorAll('*')].filter(x=>x.children.length===0&&
    (x.innerText||'').trim()===s && x.getBoundingClientRect().width>0)[0];
    if(!e) return null; let p=e,链=[]; for(let k=0;k<4&&p;k++){链.push({k,tag:p.tagName,
      cls:(p.className||'').toString().slice(0,55), box:R(p), 角色:p.getAttribute('role'),
      aria:p.getAttribute('aria-label')}); p=p.parentElement;}
    return {box:R(e), 链};};
  return {层, 视频:vids, 正在跟随:找('正在跟随'), 取消ESC:找('取消ESC'), 按ESC退出:找('按 ESC 退出')};
};

try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  T('【A 基准·故事板态】', await page.evaluate(场景,'A'));

  await page.locator('button[aria-label="放大视频"]').click();
  await page.waitForTimeout(1800);
  T('【B 点开 1.8s】', await page.evaluate(场景,'B'));
  await page.screenshot({path:E('gj2-a-放大视频-刚点开.png')});
  await page.waitForTimeout(3000);
  T('【C 再等 3s】', await page.evaluate(场景,'C'));
  await page.screenshot({path:E('gj2-b-放大视频-3秒后.png')});
  const 文 = await page.evaluate(()=>document.body.innerText.replace(/\n{2,}/g,'\n'));
  T('【全部可见文字】', 文.slice(0,1800));

  // 按 ESC 退出
  await page.keyboard.press('Escape'); await page.waitForTimeout(1800);
  T('【D Esc 之后】', await page.evaluate(场景,'D'));
  await page.screenshot({path:E('gj2-c-Esc退出后.png')});
} finally { await browser.close(); }
