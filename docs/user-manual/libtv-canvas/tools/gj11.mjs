import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

// ⭐ 三态统一 clip 起点，圈号坐标才能直接复用
const CLIP={x:452,y:40,width:988,height:770};
const 落=()=>page.evaluate((C)=>{
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const g=(s)=>{const b=document.querySelector(`button[aria-label="${s}"]`);
    return b?{框:R(b), 中心是它:(()=>{const r=b.getBoundingClientRect();
      const h=document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2));
      return !!(h&&(h===b||b.contains(h)));})()}:null;};
  const 列=[...document.querySelectorAll('.assetboard-panel')].map(p=>
    ({标题:(p.innerText||'').trim().split('\n')[0], 框:R(p)}));
  const 取=(x,y)=>{const h=document.elementFromPoint(x,y); if(!h) return null;
    let p=h,n=null; for(let k=0;k<8&&p;k++){ if(p.classList?.contains('assetboard-panel')){
      n=(p.innerText||'').trim().split('\n')[0]; break;} p=p.parentElement;}
    return n;};
  return {列, 收起图片:g('收起图片'), 收起视频:g('收起视频'),
    放大图片:g('放大图片'), 放大视频:g('放大视频'),
    左半属列:取(700,400), 右半属列:取(1200,400), 最右属列:取(1400,300)};
}, CLIP);

try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);

  T('【态1 基准】', JSON.stringify(await 落()));
  await page.screenshot({path:E('gj11-1-基准.png'), clip:CLIP});

  await page.locator('button[aria-label="放大视频"]').click(); await page.waitForTimeout(2200);
  T('【态2 点放大视频】', JSON.stringify(await 落()));
  await page.screenshot({path:E('gj11-2-放大视频后.png'), clip:CLIP});

  await page.keyboard.press('Escape'); await page.waitForTimeout(1700);
  await page.locator('button[aria-label="放大图片"]').click(); await page.waitForTimeout(2200);
  T('【态3 点放大图片】', JSON.stringify(await 落()));
  await page.screenshot({path:E('gj11-3-放大图片后.png'), clip:CLIP});

  await page.keyboard.press('Escape'); await page.waitForTimeout(1700);
  // 剪辑器素材
  await page.locator('button[aria-label="剪辑"]').click(); await page.waitForTimeout(3600);
  await page.screenshot({path:E('gj11-4-剪辑器.png'), clip:{x:452,y:40,width:988,height:770}});
  await page.screenshot({path:E('gj11-5-工具条.png'), clip:{x:500,y:520,width:930,height:64}});
  T('【剪辑器读数】', JSON.stringify(await page.evaluate(()=>{
    const R=(e)=>{const r=e.getBoundingClientRect();
      return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
    const 条=[...document.querySelectorAll('div')].filter(e=>{const r=e.getBoundingClientRect();
      return r.y>=528&&r.y<=534&&r.width>800&&r.height>=40&&r.height<=50
        &&(e.innerText||'').includes('00:00');})
      .sort((a,b)=>b.getBoundingClientRect().width-a.getBoundingClientRect().width)[0];
    const 出=document.querySelector('button[title*="暂无片段"],button[title*="合成"]');
    const 退=[...document.querySelectorAll('button')].find(b=>b.getAttribute('title')==='退出剪辑');
    const 全=[...document.querySelectorAll('button')].find(b=>b.getAttribute('title')==='全屏预览');
    const 收=[...document.querySelectorAll('button')].find(b=>b.getAttribute('title')==='收起预览');
    return {工具条:R(条), 导出:出?{框:R(出),title:出.getAttribute('title'),禁用:出.disabled}:null,
      退出剪辑:退?R(退):null, 全屏预览:全?R(全):null, 收起预览:收?R(收):null,
      画布:[...document.querySelectorAll('canvas')].map(R)};})).slice(0,1500));
} finally { await browser.close(); }
