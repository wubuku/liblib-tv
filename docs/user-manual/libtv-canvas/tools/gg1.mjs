import { launch, open, closePromos } from './lib.mjs';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
async function 稳定(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}
const 快照=()=>page.evaluate(()=>{
  const ns=[...document.querySelectorAll('.react-flow__node')];
  return {节点数:ns.length,
    节点:ns.map(n=>{const r=n.getBoundingClientRect();return {
      类型:(n.className||'').match(/react-flow__node-([a-z0-9-]+)/)?.[1],
      标题:(n.innerText||'').trim().split('\n')[0],
      框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)]};}),
    连线:document.querySelectorAll('.react-flow__edge').length,
    小地图:!!document.querySelector('.react-flow__minimap'),
    URL:location.search};
});
try {
  await open(page,B); await closePromos(page);
  T('工作流态 节点数:', await 稳定());
  const A=await 快照(); T('工作流:', A);
  // 切到故事板
  const sb=page.locator('button[aria-label="故事板"]');
  T('故事板按钮数:', await sb.count());
  await sb.click(); await page.waitForTimeout(3000);
  const B1=await 快照(); T('故事板:', B1);
  T('故事板页面文字（前 400）:', await page.evaluate(()=>(document.body.innerText||'').slice(0,400)));
  // 切回工作流
  const wf=page.locator('button[aria-label="工作流"]');
  T('切回后 工作流按钮数:', await wf.count());
  await wf.click(); await page.waitForTimeout(3000);
  const C=await 快照(); T('切回工作流:', C);
  // ⭐ 对比：节点位置/连线是否原样
  const 同样 = JSON.stringify(A.节点)===JSON.stringify(C.节点);
  T('⭐ 往返后节点列表逐字一致:', 同样, ' 连线', A.连线, '→', C.连线, ' URL同:', A.URL===C.URL);
  if(!同样){ T('A节点:', JSON.stringify(A.节点)); T('C节点:', JSON.stringify(C.节点)); }
} finally { await browser.close(); }
