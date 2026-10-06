import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

const 全扫 = () => {
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const 列=[...document.querySelectorAll('.assetboard-panel')].map(p=>{
    // 每列：列头按钮 + 内容区的可点元素
    const 头=p.querySelector('header')||p;
    const 头按钮=[...头.querySelectorAll('button,[role="button"]')].map(b=>({
      aria:b.getAttribute('aria-label'), 文本:(b.innerText||'').trim().replace(/\s+/g,' ').slice(0,8), 框:R(b)}));
    // 卡片：取「可点但不缩到 0 宽」的元素，排除列头和容器
    const 卡=[...p.querySelectorAll('*')].filter(e=>{
      const r=e.getBoundingClientRect(); const s=getComputedStyle(e);
      return r.width>=40 && r.height>=20 && s.cursor==='pointer' && +s.opacity>0
        && !e.closest('header');
    });
    // 按 y 排序 + 去重（只留最内层的）
    const 见过=new Set(); const 卡集=[];
    for(const e of 卡.sort((a,b)=>a.getBoundingClientRect().y-b.getBoundingClientRect().y)){
      if(见过.has(e)) continue; 见过.add(e);
      卡集.push({tag:e.tagName, 框:R(e),
        文字:(e.innerText||'').trim().replace(/\s+/g,' ').slice(0,40),
        子:e.children.length, 无名:e.children.length>0 && !(e.innerText||'').trim()});
    }
    return {列名:(p.innerText||'').trim().split('\n')[0], 列框:R(p), 头按钮, 卡数:卡集.length, 卡:卡集.slice(0,14)};
  });
  return {列};
};

try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  T('【四列全扫】', JSON.stringify(await page.evaluate(全扫),null,1).slice(0,6000));
  await page.screenshot({path:E('gk1-a-故事板全貌.png')});
  await page.screenshot({path:E('gk1-b-左半两列.png'),
    clip:{x:0,y:40,width:495,height:300}});
  await page.screenshot({path:E('gk1-c-右半两列.png'),
    clip:{x:495,y:40,width:945,height:300}});
} finally { await browser.close(); }
