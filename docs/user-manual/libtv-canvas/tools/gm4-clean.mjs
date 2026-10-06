import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

const 全量 = () => {
  const v=document.querySelector('.react-flow__viewport');
  const m=/matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform||'');
  const 节点=[...document.querySelectorAll('.react-flow__node')].map(n=>{
    const t=/translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform||'');
    return {id:n.getAttribute('data-id'),
      画布坐标:t?[Math.round(Number(t[1])),Math.round(Number(t[2]))]:null};});
  return {矩阵:m?m[1]:null, 节点数:节点.length,
    节点:节点.sort((a,b)=>String(a.id).localeCompare(String(b.id))),
    选中:document.querySelectorAll('.react-flow__node.selected').length,
    框选矩形:document.querySelectorAll('.react-flow__selection').length};
};

try {
  await open(page,B); await closePromos(page); await 稳();
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  const 基线=await page.evaluate(全量);
  T('【基线（干净载入）】', JSON.stringify(基线,null,1).slice(0,2200));

  // ⭐ 用「适合屏幕 ⌘0」把 viewport 拉回适配位
  await page.keyboard.press('Meta+0'); await page.waitForTimeout(1800);
  const 适配=await page.evaluate(全量);
  T('【⌘0 之后】', JSON.stringify(适配,null,1).slice(0,2200));
  await page.screenshot({path:E('gm4-a-复原后.png')});
} finally { await browser.close(); }
