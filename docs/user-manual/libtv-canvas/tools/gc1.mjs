import { launch, open, closePromos } from './lib.mjs';
const MAIN='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
try {
  await open(page,MAIN); await closePromos(page);
  // 建一张空画布（留空名? 不行——留空不建。给它起名）
  await page.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(x=>{const r=x.getBoundingClientRect();
    return r.x>160&&r.x<180&&r.y<20&&r.width>40;}); b.click();});
  await page.waitForTimeout(900);
  await page.locator('button[aria-label="新建画布"]').click(); await page.waitForTimeout(900);
  await page.locator('input[aria-label="画布名称"]').fill('GC-空画布取证');
  await page.keyboard.press('Enter'); await page.waitForTimeout(3000);
  T('新画布 pid:', await page.evaluate(()=>(location.search.match(/projectId=(\w+)/)||[])[1]));
  T('顶栏:', await page.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(x=>{const r=x.getBoundingClientRect();
    return r.x>160&&r.x<180&&r.y<20&&r.width>40;}); return b?b.innerText.trim():null;}));
  // 等节点数连续3次不变（缺陷 491）
  let prev=-1, ok=false;
  for(let i=0;i<10;i++){ const n=await page.locator('.react-flow__node').count();
    if(n===prev){ ok=true; break; } prev=n; await page.waitForTimeout(900); }
  T('节点数稳定:', ok, '值', prev);
  // 空画布中央那排「生成芯片」
  const 芯片 = await page.evaluate(()=>{
    const 词=['图片生成','视频生成','音频生成','剧本生成','智能剪辑'];
    return 词.map(w=>{
      const els=[...document.querySelectorAll('button,[role="button"],div,span,a')].filter(e=>(e.innerText||'').trim()===w);
      if(!els.length) return {词:w, 找到:0};
      // 取最内层
      const e=els.sort((a,b)=>{const x=a.getBoundingClientRect(),y=b.getBoundingClientRect();return x.width*y.height-y.width*x.height;})[0];
      const r=e.getBoundingClientRect();
      return {词:w, 找到:els.length, tag:e.tagName, aria:e.getAttribute('aria-label'),
        title:e.getAttribute('title'), box:[r.x,r.y,r.width,r.height].map(Math.round),
        中心属主:(()=>{const t=document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2));
          return t?(t.innerText||t.tagName).trim().slice(0,20):null;})()};
    });
  });
  T('五枚芯片:', 芯片);
} finally { await browser.close(); }
