import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const MAIN='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const E=(n)=>resolve('tools','.evidence',n);
const 词=['图片生成','视频生成','音频生成','剧本生成','智能剪辑'];
async function 建空画布(page, 名){
  await page.evaluate(()=>{const b=[...document.querySelectorAll('button')].find(x=>{const r=x.getBoundingClientRect();
    return r.x>160&&r.x<180&&r.y<20&&r.width>40;}); if(b) b.click();});
  await page.waitForTimeout(1000);
  if(!await page.evaluate(()=>!!document.querySelector('button[aria-label="新建画布"]'))) return false;
  await page.locator('button[aria-label="新建画布"]').click(); await page.waitForTimeout(1000);
  await page.locator('input[aria-label="画布名称"]').fill(名);
  await page.keyboard.press('Enter'); await page.waitForTimeout(3500);
  return true;
}
async function 稳定(page){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}
for (const 宽 of [1440, 1280, 1100]) {
  const { browser, page } = await launch({ viewport: { width: 宽, height: 810 } });
  console.log(`\n===== 视口宽 ${宽} =====`);
  try {
    await open(page,MAIN); await closePromos(page);
    console.log('  建画布:', await 建空画布(page, `GE2-${宽}`), '节点数', await 稳定(page));
    const 读=async(tag)=>{
      const r=await page.evaluate((W)=>{
        const out=W.map(w=>{
          const b=[...document.querySelectorAll('button')].filter(e=>e.innerText.trim()===w)
            .sort((x,y)=>{const a=x.getBoundingClientRect(),c=y.getBoundingClientRect();
              return a.width*a.height-c.width*c.height;})[0];
          if(!b) return {词:w,存在:false};
          const q=b.getBoundingClientRect(); const cx=Math.round(q.x+q.width/2), cy=Math.round(q.y+q.height/2);
          const hit=document.elementFromPoint(cx,cy);
          return {词:w, 框:[q.x,q.y,q.width,q.height].map(Math.round),
            可点: hit?(b.contains(hit)||hit===b):false,
            属主: hit?(hit.innerText||hit.tagName).trim().slice(0,12):null};});
        const d=document.querySelector('.copilotKitChat');
        const dq=d?d.getBoundingClientRect():null;
        return {芯片:out, 抽屉:dq?[dq.x,dq.width].map(Math.round):null, 视口:innerWidth};}, 词);
      console.log(`  [${tag}] 视口${r.视口} 抽屉x=${r.抽屉?r.抽屉[0]+' 宽'+r.抽屉[1]:'无'}`);
      r.芯片.forEach(c=>console.log(`    ${c.存在? (c.可点?'✅':'⛔被挡') : '不存在'} ${c.词} ${c.框?JSON.stringify(c.框):''} ${(!c.可点&&c.属主)?'属主='+c.属主:''}`));
      return r;
    };
    const a=await 读('抽屉开');
    if(宽===1440) await page.screenshot({path:E('ge1-1440-抽屉开.png'), clip:{x:0,y:300,width:1440,height:200}});
    // 关抽屉
    await page.evaluate(()=>{const bs=[...document.querySelectorAll('button[aria-label="关闭"]')]
      .filter(b=>{const r=b.getBoundingClientRect();return r.width>0&&r.height>0;}); if(bs.length) bs[bs.length-1].click();});
    await page.waitForTimeout(1800);
    await 读('关抽屉后');
  } finally { await browser.close(); }
}
console.log('\n待清理: GE2-1440 GE2-1280 GE2-1100 GE-1440 GE-1280 GE-1100 GE-诊断');
