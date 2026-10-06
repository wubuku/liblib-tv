import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

const 探=(标)=>{
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const 键=(s)=>[...document.querySelectorAll(`button[aria-label="${s}"]`)].map(b=>({
    aria:b.getAttribute('aria-label'), 框:R(b), 不透明度:getComputedStyle(b).opacity,
    // ⭐ 落点自证：中心命中的是不是这枚自己（或其后代）
    中心是它:(b=>{const r=b.getBoundingClientRect();
      const h=document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2));
      return !!(h && (h===b || b.contains(h)));})(b),
    z:(()=>{let p=b,n=0; while(p&&n<40){const s=getComputedStyle(p);
      if(s.zIndex!=='auto'&&+s.zIndex>0) n=+s.zIndex; p=p.parentElement;} return n;})()}));
  const 列=[...document.querySelectorAll('.assetboard-panel')].map(p=>({
    标题:(p.innerText||'').trim().split('\n')[0], 框:R(p)}));
  const 取=(x,y)=>{const h=document.elementFromPoint(x,y); if(!h) return null;
    let p=h,名=null; for(let k=0;k<8&&p;k++){ if(p.classList?.contains('assetboard-panel')){
      名=(p.innerText||'').trim().split('\n')[0]; break;} p=p.parentElement;}
    return {t:(h.innerText||'').trim().replace(/\s+/g,' ').slice(0,18), 属列:名};};
  return {标, 列, 放大图片:键('放大图片'), 收起图片:键('收起图片'),
    放大视频:键('放大视频'), 收起视频:键('收起视频'),
    左半取样:取(700,400), 右半取样:取(1200,400), 最右取样:取(1400,120)};
};

try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  T('【A 基准】', JSON.stringify(await page.evaluate(探,'A'),null,1).slice(0,2600));
  await page.screenshot({path:E('gj10-a-基准四列.png')});

  await page.locator('button[aria-label="放大图片"]').click(); await page.waitForTimeout(2200);
  T('【B 点「放大图片」后】', JSON.stringify(await page.evaluate(探,'B'),null,1).slice(0,2600));
  await page.screenshot({path:E('gj10-b-放大图片态.png')});
  await page.screenshot({path:E('gj10-c-放大图片态-列头.png'),
    clip:{x:0,y:40,width:1440,height:56}});

  await page.keyboard.press('Escape'); await page.waitForTimeout(1600);
  T('【C Esc 还原】', JSON.stringify(await page.evaluate(探,'C'),null,1).slice(0,1400));
} finally { await browser.close(); }
