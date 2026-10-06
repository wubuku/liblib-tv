import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const EMPTY='https://www.liblib.tv/canvas?spaceId=10354929&projectId=13249957f18e42ce90d3b913e985cef0';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
try {
  await open(page,EMPTY); await closePromos(page);
  let p=-1; for(let i=0;i<12;i++){const n=await page.locator('.react-flow__node').count();
    if(n===p) break; p=n; await page.waitForTimeout(900);}
  // 图1：整排芯片 + 抽屉叠压全景
  const CLIP={x:180,y:330,width:1080,height:290};
  await page.screenshot({path:E('gc1-芯片排与抽屉叠压.png'), clip:CLIP});
  console.log('  拍 gc1');
  // 图2：第5枚落点自证的特写（放大到芯片4~5 + 抽屉左缘）
  await page.screenshot({path:E('gc2-第五枚被遮特写.png'), clip:{x:800,y:390,width:460,height:100}});
  console.log('  拍 gc2');
  // 试着把抽屉关掉，再看第5枚能否点到
  const 关=await page.evaluate(()=>{
    const btns=[...document.querySelectorAll('button')].map(b=>({b,t:b.innerText.trim().slice(0,12),
      aria:b.getAttribute('aria-label'),box:(()=>{const r=b.getBoundingClientRect();return [r.x,r.y,r.width,r.height].map(Math.round);})()}))
      .filter(x=>x.box[2]>0&&x.box[0]>1000&&x.box[0]<1440&&x.box[1]<260);
    return btns;
  });
  T('抽屉顶部附近按钮:', 关);
} finally { await browser.close(); }
