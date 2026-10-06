import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

const CLIP={x:490,y:40,width:950,height:420};
// ⚠️ 缺陷 513：这里是**浏览器侧**函数，函数体里绝不能出现 `page`
const 编辑态 = () => {
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  // ⭐ `.node-floating-ui` 是通用容器，页面上有多个（含常驻空浮层），
  //    要用「含『高级设置』且框高 ≥ 200」才能定位到参数面板那一个
  const p=[...document.querySelectorAll('.node-floating-ui')].find(e=>{
    const r=e.getBoundingClientRect();
    return r.height>=200 && /高级设置/.test(e.innerText||'');});
  if(!p) return {无:true};
  return {框:R(p), 文字:(p.innerText||'').trim().replace(/\n{2,}/g,' | ').slice(0,220),
    顶部按钮:[...p.querySelectorAll('button')].map(b=>{const r=b.getBoundingClientRect();
      return {t:(b.innerText||'').trim().slice(0,6), aria:b.getAttribute('aria-label'),
        title:b.getAttribute('title'), 框:R(b)};}).slice(0,12),
    高级设置折叠:(()=>{const h=[...p.querySelectorAll('*')]
      .find(e=>(e.innerText||'').trim()==='高级设置'&&e.children.length===0);
      if(!h) return null; let q=h; for(let k=0;k<3&&q;k++){q=q.parentElement;
        if(q&&/grid-rows/.test(getComputedStyle(q).gridTemplateRows))
          return {行高:getComputedStyle(q).gridTemplateRows, 框:R(q)};}
      return {框:R(h)};})()};
};

try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  T('【未点】', await page.evaluate(编辑态));
  await page.screenshot({path:E('gk6-a-点之前.png'), clip:CLIP});
  await page.screenshot({path:E('gk6-a2-点之前-左半.png'), clip:{x:0,y:40,width:500,height:420}});

  await page.mouse.click(1150, 220); await page.waitForTimeout(2500);
  T('【点视频卡之后】', await page.evaluate(编辑态));
  await page.screenshot({path:E('gk6-b-点之后.png'), clip:CLIP});
  await page.screenshot({path:E('gk6-b2-点之后-左半.png'), clip:{x:0,y:40,width:500,height:420}});

  await page.keyboard.press('Escape'); await page.waitForTimeout(1800);
  T('【Esc 之后】', await page.evaluate(编辑态));
  await page.screenshot({path:E('gk6-c-Esc之后.png'), clip:CLIP});

  // 左半：点音频卡（对照，看左半列会怎样）
  await page.mouse.click(58, 140); await page.waitForTimeout(2500);
  T('【点音频卡之后】', await page.evaluate(编辑态));
  await page.screenshot({path:E('gk6-d-点音频卡-全宽.png'), clip:{x:0,y:40,width:1440,height:420}});
} finally { await browser.close(); }
