import { launch, open, closePromos } from './lib.mjs';
const MAIN='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}
try {
  await open(page,MAIN); await closePromos(page);
  await page.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(x=>{const r=x.getBoundingClientRect();
    return r.x>160&&r.x<180&&r.y<20&&r.width>40;}); if(b) b.click();});
  await page.waitForTimeout(900);
  T('下拉开:', await page.evaluate(()=>!!document.querySelector('button[aria-label="新建画布"]')));
  await page.locator('button[aria-label="新建画布"]').click(); await page.waitForTimeout(900);
  await page.locator('input[aria-label="画布名称"]').fill('GE-诊断');
  await page.keyboard.press('Enter'); await page.waitForTimeout(3500);
  T('节点数:', await 稳定());
  T('URL:', await page.evaluate(()=>location.search));
  const 诊断=await page.evaluate(()=>{
    const w='图片生成';
    const all=[...document.querySelectorAll('*')].filter(e=>e.innerText && e.innerText.trim()===w);
    return {命中总数: all.length,
      明细: all.map(e=>{const r=e.getBoundingClientRect();
        return {tag:e.tagName, cls:(e.className||'').toString().slice(0,60),
          box:[r.x,r.y,r.width,r.height].map(Math.round),
          area:Math.round(r.width*r.height)};}).slice(0,6)};
  });
  T('「图片生成」元素:', 诊断);
  T('页面有没有 智能剪辑:', await page.evaluate(()=>({body:(document.body.innerText||'').includes('智能剪辑')})));
} finally { await browser.close(); }
