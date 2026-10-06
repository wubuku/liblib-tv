import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

const 状 = (标) => {
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const 节点=[...document.querySelectorAll('.react-flow__node')];
  const 选中=节点.filter(n=>n.className.includes('selected')).map(n=>{
    const t=(n.innerText||'').trim().split('\n')[0];
    const r=n.getBoundingClientRect();
    return {标题:t, 框:R(n), z:getComputedStyle(n).zIndex};});
  const 新增=[...document.querySelectorAll('body *')].filter(e=>{
    const s=getComputedStyle(e), r=e.getBoundingClientRect();
    return (s.position==='fixed') && r.width>=200 && r.height>=120
      && +s.zIndex>=40 && r.width<=1600 && r.height<=900
      && +s.opacity>0.5;})
    .map(e=>({cls:(e.className||'').toString().slice(0,60), z:getComputedStyle(e).zIndex,
      框:R(e), 文字:(e.innerText||'').trim().replace(/\s+/g,' ').slice(0,50)}));
  const 音频=[...document.querySelectorAll('audio')].map(a=>({框:R(a), 播放:!a.paused,
    时长:+(a.duration||0).toFixed(1), 源:(a.currentSrc||'').slice(-40)}));
  return {标, 节点数:节点.length, 选中, 新增浮层:新增, 音频元素:音频,
    文字尾:document.body.innerText.replace(/\n{2,}/g,'\n').slice(-420)};
};

try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  T('【基准·故事板态】', await page.evaluate(状,'基准'));
  await page.screenshot({path:E('gk2-a-基准.png')});

  // ① 点第一枚「音频节点 1」（它是 BUTTON）
  const 卡=page.locator('.assetboard-panel button', {hasText:'音频节点 1'});
  T('音频卡数:', await 卡.count());
  if(await 卡.count()>=1){
    await 卡.first().click(); await page.waitForTimeout(2500);
    T('【点第一枚音频卡之后】', await page.evaluate(状,'点音频卡'));
    await page.screenshot({path:E('gk2-b-点音频卡之后.png')});
  }
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);

  // ② 点「文本节点 2」那一行
  const 行=page.locator('.assetboard-panel').filter({hasText:'文本节点 2'}).locator('span', {hasText:'文本节点 2'});
  T('文本标题数:', await 行.count());
  if(await 行.count()>=1){
    await 行.first().click(); await page.waitForTimeout(2500);
    T('【点文本行之后】', await page.evaluate(状,'点文本行'));
    await page.screenshot({path:E('gk2-c-点文本行之后.png')});
  }
} finally { await browser.close(); }
