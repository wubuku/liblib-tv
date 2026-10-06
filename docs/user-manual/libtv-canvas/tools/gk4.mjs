import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

// ⭐ 判据修正：面板**不能**在 .assetboard-panel 里面（缺陷 521）
const 面板读数 = () => {
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const 候选=[...document.querySelectorAll('div')].filter(e=>{
    if(e.closest('.assetboard-panel')) return false;               // ⭐ 排除分栏卡
    const s=getComputedStyle(e), r=e.getBoundingClientRect(), t=(e.innerText||'');
    return r.width>=200 && r.width<=720 && r.height>=200 && r.height<=720
      && (s.position==='fixed'||s.position==='absolute') && +s.opacity>0.5
      && /待确认后生成/.test(t) && /(高级设置|语速|声调|音量|添加到对话|风格|特效|角色库|运镜)/.test(t);})
    .sort((a,b)=>{const q=b.getBoundingClientRect(),p2=a.getBoundingClientRect();
      return q.width*q.height-p2.width*p2.height;});
  if(!候选.length) return {无面板:true};
  const p=候选[0];
  return {框:R(p), cls:(p.className||'').toString().slice(0,90),
    文字:(p.innerText||'').trim().replace(/\n{2,}/g,' | ').slice(0,300),
    按钮:[...p.querySelectorAll('button')].map(b=>({t:(b.innerText||'').trim().slice(0,8),
      aria:b.getAttribute('aria-label'), title:b.getAttribute('title'), 框:R(b),
      禁用:b.disabled===true})).slice(0,18),
    输入:[...p.querySelectorAll('input,textarea')].map(i=>({ph:i.placeholder||'',
      值:(i.value||'').slice(0,20), aria:i.getAttribute('aria-label'), 框:R(i)}))};
};

try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  T('【基准·无面板】', await page.evaluate(面板读数));

  await page.mouse.click(1150, 220); await page.waitForTimeout(2400);   // 点视频卡
  const p1=await page.evaluate(面板读数);
  T('【点视频卡·面板】', p1);
  await page.screenshot({path:E('gk4-a-视频卡参数面板.png')});

  await page.keyboard.press('Escape'); await page.waitForTimeout(1600);
  T('【Esc 一次】', await page.evaluate(面板读数));
  await page.keyboard.press('Escape'); await page.waitForTimeout(1600);
  T('【Esc 两次】', await page.evaluate(面板读数));

  // 找关闭方式：面板里有没有 ✕ / aria=关闭
  T('页面里所有关闭类按钮:', await page.evaluate(()=>[...document.querySelectorAll('button')]
    .filter(b=>/关闭|close|取消|✕|×/i.test(b.getAttribute('aria-label')||b.getAttribute('title')||b.innerText||''))
    .map(b=>{const r=b.getBoundingClientRect();
      return {aria:b.getAttribute('aria-label'), title:b.getAttribute('title'),
        t:(b.innerText||'').trim().slice(0,6),
        框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
        可见:getComputedStyle(b).opacity};})));

  // 点故事板左半空白（音频列下方空白）
  await page.mouse.click(300, 700); await page.waitForTimeout(1800);
  T('【点故事板空白之后】', await page.evaluate(面板读数));
  await page.screenshot({path:E('gk4-b-点空白后.png')});
} finally { await browser.close(); }
