import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

const 探 = () => {
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  // ⭐ 用结构判据取列（class assetboard-panel），不用文字清单（缺陷 516）
  const 列=[...document.querySelectorAll('.assetboard-panel')].map(p=>{
    const r=p.getBoundingClientRect();
    return {框:R(p), 头:(p.querySelector('button[aria-label="全部"],button[aria-label^="筛选"]')?.innerText||'').trim(),
      标题:(p.innerText||'').trim().split('\n')[0], 卡片数:p.querySelectorAll('[class*="cursor-pointer"],a,img').length};});
  const 取=(x,y)=>{const e=document.elementFromPoint(x,y); if(!e) return null;
    let p=e,列名=null; for(let k=0;k<8&&p;k++){ if(p.classList?.contains('assetboard-panel'))
        {列名=(p.innerText||'').trim().split('\n')[0]; break;} p=p.parentElement;}
    return {tag:e.tagName, t:(e.innerText||'').trim().slice(0,16), 属列:列名};};
  // 「正在跟随」条的真实可见性
  const 跟随=[...document.querySelectorAll('*')].find(e=>(e.innerText||'').trim()==='正在跟随'
    && e.children.length===0);
  let 跟条=null;
  if(跟随){ let p=跟随; for(let k=0;k<3&&p;k++){p=p.parentElement;
    if(p&&getComputedStyle(p).position==='fixed'){const s=getComputedStyle(p);
      跟条={框:R(p), 容器不透明度:s.opacity, 容器PE:s.pointerEvents,
        退出键不透明度:getComputedStyle(p.querySelector('button[aria-label="退出跟随"]')||p).opacity,
        退出键PE:getComputedStyle(p.querySelector('button[aria-label="退出跟随"]')||p).pointerEvents,
        退出现在:!!p.offsetParent}; break;}}}
  const 剪=document.querySelector('button[aria-label="剪辑"]');
  const 放=document.querySelector('button[aria-label="放大视频"]');
  return {列, 右列中心取样:取(900,400), 右列上部取样:取(1200,120),
    跟随条:跟条, 剪辑:剪?{框:R(剪),可见:getComputedStyle(剪).opacity}:null,
    放大:放?{框:R(放),可见:getComputedStyle(放).opacity}:null,
    URL:location.href, 节点数:document.querySelectorAll('.react-flow__node').length};
};

try {
  await open(page,B); await closePromos(page); await 稳定();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  T('【A 放大前】', await page.evaluate(探));

  await page.locator('button[aria-label="放大视频"]').click(); await page.waitForTimeout(2200);
  T('【B 放大后】', await page.evaluate(探));
  await page.screenshot({path:E('gj3-a-放大态.png')});

  // 放大态下点「全部 ▾」
  const 筛=page.locator('.assetboard-panel button').filter({hasText:'全部'});
  T('放大态「全部」按钮数:', await 筛.count());
  if(await 筛.count()===1){
    await 筛.click(); await page.waitForTimeout(900);
    const 菜单=await page.evaluate(()=>[...document.querySelectorAll('.mantine-Menu-dropdown,[role="menu"]')]
      .map(m=>{const r=m.getBoundingClientRect();
        return {框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
          项:[...m.querySelectorAll('[role="menuitem"],button')].map(x=>(x.innerText||'').trim().slice(0,10))};}));
    T('放大态筛选菜单:', 菜单);
    await page.screenshot({path:E('gj3-b-放大态-筛选菜单.png')});
    await page.keyboard.press('Escape'); await page.waitForTimeout(700);
  }
  T('【C 菜单关掉后仍在放大态?】', await page.evaluate(探));
  await page.screenshot({path:E('gj3-c-放大态-菜单关后.png')});
} finally { await browser.close(); }
