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
  // 参数面板 = 出现「待确认后生成」以外一整套编辑控件的那个容器
  const 候选=[...document.querySelectorAll('div')].filter(e=>{
    const s=getComputedStyle(e), r=e.getBoundingClientRect();
    const t=(e.innerText||'');
    return r.width>=200 && r.width<=700 && r.height>=180 && r.height<=700
      && (s.position==='fixed'||s.position==='absolute')
      && /待确认后生成/.test(t) && /(高级设置|语速|描述|添加到对话|GVLM|Lib Image|Seed Audio)/.test(t)
      && +s.opacity>0.5;})
    .sort((a,b)=>b.getBoundingClientRect().width*b.getBoundingClientRect().height
                -a.getBoundingClientRect().width*a.getBoundingClientRect().height);
  const p=候选[0];
  const 面板=p?{框:R(p), cls:(p.className||'').toString().slice(0,80),
    全部文字:(p.innerText||'').trim().replace(/\n{2,}/g,' | ').slice(0,400),
    按钮:[...p.querySelectorAll('button')].map(b=>({t:(b.innerText||'').trim().slice(0,8),
      aria:b.getAttribute('aria-label'), title:b.getAttribute('title'), 框:R(b),
      禁用:b.disabled===true})).slice(0,20)}:null;
  // 卡片是否「已打开」—— 看有没有 active/selected 类
  const 激活=[...document.querySelectorAll('.assetboard-panel *')].filter(e=>{
    const s=getComputedStyle(e);
    return (s.outline!=='none'&&s.outlineWidth!=='0px')||s.boxShadow!=='none';})
    .map(e=>({cls:(e.className||'').toString().slice(0,60), 框:R(e)}));
  return {标, 面板, 激活样式数:激活.length, 激活:激活.slice(0,5),
    选中节点:document.querySelectorAll('.react-flow__node.selected').length};
};

const 读尾部=()=>page.evaluate(()=>document.body.innerText.replace(/\n{2,}/g,'\n').slice(-500));

try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);

  // ① 图片卡
  const 图卡=page.locator('.assetboard-panel').filter({hasText:'图片'}).first()
    .locator('div').filter({hasText:/^图片节点 2/}).first();
  await page.mouse.click(700, 220); await page.waitForTimeout(2400);
  T('【点图片卡区之后】', await page.evaluate(状,'点图片卡'));
  T('  文字尾:', await 读尾部());
  await page.screenshot({path:E('gk3-a-点图片卡.png')});

  // ② Esc 关掉，再点视频卡
  await page.keyboard.press('Escape'); await page.waitForTimeout(1600);
  T('【Esc 后面板还在吗】', await page.evaluate(状,'Esc后'));
  await page.mouse.click(1150, 220); await page.waitForTimeout(2400);
  T('【点视频卡区之后】', await page.evaluate(状,'点视频卡'));
  T('  文字尾:', await 读尾部());
  await page.screenshot({path:E('gk3-b-点视频卡.png')});
  await page.keyboard.press('Escape'); await page.waitForTimeout(1600);
  T('【再 Esc 之后】', await page.evaluate(状,'再Esc后'));
} finally { await browser.close(); }
