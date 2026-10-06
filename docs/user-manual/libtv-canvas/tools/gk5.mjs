import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

// ⭐ 用「高级设置」这个文本当锚点往上爬，直到不是分栏卡的兄弟
const 读 = (标) => {
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const 锚=[...document.querySelectorAll('*')].filter(e=>e.children.length===0
    && (e.innerText||'').trim()==='高级设置')[0];
  if(!锚) return {标, 有面板:false};
  const 链=[]; let p=锚;
  for(let k=0;k<9&&p;k++){
    const r=p.getBoundingClientRect();
    链.push({k, tag:p.tagName, cls:(p.className||'').toString().slice(0,64),
      框:R(p), 文字:(p.innerText||'').trim().replace(/\n{2,}/g,' | ').slice(0,110),
      在分栏卡内:!!p.closest('.assetboard-panel')});
    p=p.parentElement;
  }
  // 找到既不是分栏卡、又不是分栏卡子节点的那一层
  const 面板=链.find(x=>!x.在分栏卡内 && x.框[2]>=200 && x.框[2]<=720 && x.框[3]>=200);
  return {标, 有面板:true, 链, 面板层:面板||null,
    尾文:document.body.innerText.replace(/\n{2,}/g,'\n').slice(-420)};
};

try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  T('【A 未点卡】', await page.evaluate(读,'A'));

  await page.mouse.click(1150, 220); await page.waitForTimeout(2400);
  T('【B 点视频卡】', await page.evaluate(读,'B'));
  await page.screenshot({path:E('gk5-a-视频卡参数面板.png')});
  await page.screenshot({path:E('gk5-b-视频卡参数面板-右半.png'),
    clip:{x:940,y:40,width:500,height:770}});

  await page.keyboard.press('Escape'); await page.waitForTimeout(1700);
  T('【C Esc 之后】', await page.evaluate(读,'C'));
} finally { await browser.close(); }
