// GM-6：把「底栏②不是整理画布，是平移工具切换器」这件事钉死。
//
// ① 移动工具态下**拖节点**会怎样？（这解释 FV-6「点了它画布被重排」的成因）
//    ⛔ 微拖 +6,+6 再 −6,−6，终点等于原点；每步都比对节点坐标，守卫复原。
// ② 那两行常驻提示条本身能不能点？（`V`/`H` 的透明度是 0.4，指针是 auto）
import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

const 快照 = () => page.evaluate(()=>{
  const v=document.querySelector('.react-flow__viewport');
  const m=/matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform||'');
  const 节点=[...document.querySelectorAll('.react-flow__node')].map(n=>{
    const t=/translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform||'');
    return (n.getAttribute('data-id')||'')+':'+(t?Math.round(Number(t[1]))+','+Math.round(Number(t[2])):'?');}).sort();
  return {矩阵:m?m[1]:null, 节点,
    选中:[...document.querySelectorAll('.react-flow__node.selected')].map(n=>n.getAttribute('data-id')),
    框选矩形:document.querySelectorAll('.react-flow__selection').length};
});
const 工具按钮 = () => page.evaluate(()=>{
  const b=document.querySelector('button[aria-label="移动"],button[aria-label="抓手工具"]');
  if(!b) return null; const r=b.getBoundingClientRect();
  return {aria:b.getAttribute('aria-label'), 背景:getComputedStyle(b).backgroundColor,
    框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)]};});
const 提示条 = () => page.evaluate(()=>{
  const 白=['移动','V','抓手工具','H'];
  return [...document.querySelectorAll('*')].filter(e=>{
    if(e.children.length!==0) return false; if(!白.includes((e.innerText||'').trim())) return false;
    const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;})
    .map(e=>{const r=e.getBoundingClientRect();
      return {文字:(e.innerText||'').trim(), 框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
        透明度:getComputedStyle(e).opacity, 指针:getComputedStyle(e).pointerEvents};});});

const 拖 = async (p,dx,dy,步=10) => {
  await page.mouse.move(p[0],p[1]); await page.waitForTimeout(280);
  await page.mouse.down(); await page.waitForTimeout(180);
  for(let i=1;i<=步;i++){ await page.mouse.move(p[0]+dx*i/步, p[1]+dy*i/步); await page.waitForTimeout(150); }
  await page.mouse.up(); await page.waitForTimeout(750);
};

try {
  await open(page,B); await closePromos(page); T('节点数', await 稳());
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  const 基线=await 快照(); T('【基线矩阵】', 基线.矩阵);
  T('【A 初始 工具按钮】', await 工具按钮());

  // ② 提示条可点吗？先进入移动工具态让提示条出现
  await page.locator('button[aria-label="移动"]').first().click(); await page.waitForTimeout(1500);
  T('【B 点按钮后 工具按钮】', await 工具按钮());
  const bar=await 提示条(); T('【B 提示条四行】', bar);

  // ⭐ 点提示条里「抓手工具」那一行（y≈703 的行）
  const 抓手行=bar.find(h=>h['文字']==='抓手工具');
  if(抓手行){
    const cx=抓手行.框[0]+Math.round(抓手行.框[2]/2), cy=抓手行.框[1]+Math.round(抓手行.框[3]/2);
    T('【点「抓手工具」行之前 elementFromPoint】', await page.evaluate(([x,y])=>{
      const h=document.elementFromPoint(x,y);
      return {命中:h?h.tagName:null, 文字:h?(h.innerText||'').trim().slice(0,20):null,
        指针:h?getComputedStyle(h).pointerEvents:null};}, [cx,cy]));
    await page.mouse.click(cx,cy); await page.waitForTimeout(1300);
    T('【C 点提示条「抓手工具」行之后】', await 工具按钮());
    await page.keyboard.press('v'); await page.waitForTimeout(1100);
    T('【D 随后按 v】', await 工具按钮());
  }

  // ① 移动工具态下拖节点。先找一个节点的屏幕框并落点自证（中心落在卡片上）
  await page.keyboard.press('v'); await page.waitForTimeout(1200);
  T('【E 回到移动工具态】', await 工具按钮());
  const 目标=await page.evaluate(()=>{
    const n=[...document.querySelectorAll('.react-flow__node')][0];
    const r=n.getBoundingClientRect(); const id=n.getAttribute('data-id');
    const cx=Math.round(r.x+r.width/2), cy=Math.round(r.y+24);
    const h=document.elementFromPoint(cx,cy);
    return {id, 框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
      落点:[cx,cy], 落点命中:h?h.tagName:null, 命中属主:h?(h.closest('.react-flow__node')?.getAttribute('data-id')??null):null};});
  T('【E 目标节点】', 目标);
  if(目标.命中属主===目标.id){
    await 拖(目标.落点, 6,6, 4);
    const 中=await 快照();
    T('【F 移动工具态 微拖节点 +6,+6 之后】', {选中:中.选中, 框选矩形:中.框选矩形,
      该节点坐标:(中.节点.find(s=>s.startsWith(目标.id+':'))||'?'),
      基线坐标:(基线.节点.find(s=>s.startsWith(目标.id+':'))||'?')});
    await 拖([目标.落点[0]+6, 目标.落点[1]+6], -6,-6, 4);
    const 后=await 快照();
    T('【G 拖回之后 节点坐标是否复原】', 后.节点.find(s=>s.startsWith(目标.id+':'))===基线.节点.find(s=>s.startsWith(目标.id+':')));
    T('【G 全画布节点坐标是否复原】', JSON.stringify(基线.节点)===JSON.stringify(后.节点));
    T('【G 选中态】', 后.选中);
  }
  await page.keyboard.press('Escape'); await page.waitForTimeout(800);
  await page.keyboard.press('Meta+0'); await page.waitForTimeout(1800);
  const 末=await 快照();
  T('【末态 节点坐标复原】', JSON.stringify(基线.节点)===JSON.stringify(末.节点));
  T('【末态 矩阵】', 末.矩阵);
} finally { await browser.close(); }
