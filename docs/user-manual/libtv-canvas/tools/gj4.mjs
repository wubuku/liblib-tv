import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

const 探=(tag)=>{
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const 层=[...document.querySelectorAll('body *')].filter(e=>{
    const s=getComputedStyle(e), r=e.getBoundingClientRect();
    return (s.position==='fixed') && r.width>=120 && r.height>=40
      && +s.zIndex>=40 && r.x<1440 && r.y<900 && r.width<=1600 && r.height<=900;
  }).map(e=>{const s=getComputedStyle(e);
    return {tag:e.tagName, cls:(e.className||'').toString().slice(0,72), z:s.zIndex, op:s.opacity,
      PE:s.pointerEvents, 框:R(e), 文字:(e.innerText||'').trim().replace(/\s+/g,' ').slice(0,70)};});
  const 抽屉=document.querySelector('.copilotKitChat');
  return {层, 抽屉框:抽屉?R(抽屉):'无',
    节点数:document.querySelectorAll('.react-flow__node').length, URL:location.href,
    可见文字:document.body.innerText.replace(/\n{2,}/g,'\n').slice(0,1500)};
};

try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  T('【A 点剪辑前】', await page.evaluate(探,'A'));

  const 剪=page.locator('button[aria-label="剪辑"]');
  T('剪辑按钮数:', await 剪.count());
  const b=await 剪.boundingBox();
  T('剪辑按钮框:', b && [Math.round(b.x),Math.round(b.y),Math.round(b.width),Math.round(b.height)]);
  // 落点自证：opacity:1 的唯一一枚 + 中心与目标一致
  const 属=await page.evaluate(()=>{const btn=document.querySelector('button[aria-label="剪辑"]');
    const r=btn.getBoundingClientRect();
    const h=document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2));
    return {命中:h?(h.innerText||h.getAttribute('aria-label')||h.tagName).trim().slice(0,14):null};});
  T('中心落点属主:', 属);
  await page.screenshot({path:E('gj4-a-点剪辑前-右下角.png'),
    clip:{x:1240,y:640,width:200,height:170}});

  await 剪.click(); await page.waitForTimeout(3000);
  T('【B 点开 3s】', await page.evaluate(探,'B'));
  await page.screenshot({path:E('gj4-b-点开剪辑.png')});

  await page.waitForTimeout(3000);
  T('【C 再等 3s】', await page.evaluate(探,'C'));
  await page.screenshot({path:E('gj4-c-剪辑-6秒.png')});
} finally { await browser.close(); }
