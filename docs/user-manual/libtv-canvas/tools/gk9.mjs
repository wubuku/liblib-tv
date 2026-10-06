import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

const 编辑态 = () => {
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  // ⭐ 缺陷 522：只用「宽 ≥500 + 含『高级设置』或『参考』」，不设高度门槛
  const p=[...document.querySelectorAll('.node-floating-ui')].find(e=>{
    const r=e.getBoundingClientRect();
    return r.width>=500 && r.height>=150 && /参考/.test(e.innerText||'');});
  if(!p) return {无:true};
  return {框:R(p), 文字:(p.innerText||'').trim().replace(/\n{2,}/g,' | ').slice(0,190)};
};

// ⭐ 裁到 y=810：编辑态的提示框/模型下拉/积分/↑键 都在 y 549~797
const CLIP={x:490,y:40,width:950,height:770};
try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  T('【前】', await page.evaluate(编辑态));
  await page.screenshot({path:E('gk9-1-前.png'), clip:CLIP});

  await page.locator('.assetboard-panel button', {hasText:'音频节点 1'}).first().click();
  await page.waitForTimeout(2500);
  T('【音频】', await page.evaluate(编辑态));
  await page.screenshot({path:E('gk9-2-音频.png'), clip:CLIP});
  await page.keyboard.press('Escape'); await page.waitForTimeout(1700);

  // ⭐ 每步之间必须确认「面板真的关了」—— 不然下一步的点击会被上一块面板盖住
  for(let i=0;i<4 && !(await page.evaluate(编辑态)).无;i++){
    await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  }
  T('【关干净了吗】', await page.evaluate(编辑态));

  await page.mouse.click(1150, 220); await page.waitForTimeout(2500);
  T('【视频】', await page.evaluate(编辑态));
  await page.screenshot({path:E('gk9-4-视频.png'), clip:CLIP});
  await page.keyboard.press('Escape'); await page.waitForTimeout(1700);
  T('【复原】', await page.evaluate(编辑态));
} finally { await browser.close(); }
