import { launch, open, closePromos, 往返拖, 读画布坐标 } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

const 结构 = (标) => {
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const 节点=[...document.querySelectorAll('.react-flow__node')];
  const 带句柄=节点.filter(n=>n.querySelectorAll('.react-flow__handle').length>0);
  return {标, 节点数:节点.length,
    有句柄的节点数:带句柄.length,
    句柄总数:document.querySelectorAll('.react-flow__handle').length,
    可见句柄:(()=>{let n=0; document.querySelectorAll('.react-flow__handle').forEach(h=>{
      const r=h.getBoundingClientRect(); const s=getComputedStyle(h);
      if(r.width>0&&s.opacity!=='0'&&s.visibility!=='hidden') n++;}); return n;})(),
    连线数:document.querySelectorAll('.react-flow__edge').length,
    边句柄样例:[...document.querySelectorAll('.react-flow__handle')].slice(0,4).map(h=>{
      const r=h.getBoundingClientRect();
      return {cls:(h.className||'').toString().slice(0,44), 框:R(h),
        不透明度:getComputedStyle(h).opacity, 可见性:getComputedStyle(h).visibility,
        指针:getComputedStyle(h).pointerEvents};}),
    第一个节点:(()=>{const n=节点[0]; if(!n) return null;
      const r=n.getBoundingClientRect();
      const m=/translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform||'');
      return {id:n.getAttribute('data-id'), 框:R(n), 画布坐标:m?[Number(m[1]),Number(m[2])]:null};})()};
  // ⭐ 缺陷 513：正则必须写在 evaluate 回调体内，不能引用 Node 侧函数
};


try {
  await open(page,B); await closePromos(page); await 稳();
  // 工作流态基准
  const 基准=await page.evaluate(结构,'工作流态');
  T('【工作流态基准】', JSON.stringify(基准,null,1).slice(0,2200));
  const id0=基准.第一个节点 && 基准.第一个节点.id;
  const 坐标0=基准.第一个节点 && 基准.第一个节点.画布坐标;

  // 切故事板
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  const 故=await page.evaluate(结构,'故事板态');
  T('【故事板态】', JSON.stringify(故,null,1).slice(0,2200));

  // 拖一个节点：往返拖，净位移应为 0
  if(id0){
    const r=await 往返拖(page, id0, 60);
    T('【故事板态 往返拖 60px】', JSON.stringify(r));
    const 终=await 读画布坐标(page, id0);
    T('  拖完画布坐标:', 终, '基准:', 坐标0, '复原了吗:', JSON.stringify(终)===JSON.stringify(坐标0));
  }
  await page.screenshot({path:E('gl4-a-故事板态全貌.png')});
  T('【拖完再读结构】', JSON.stringify(await page.evaluate(结构,'拖完'),null,1).slice(0,900));
} finally { await browser.close(); }
