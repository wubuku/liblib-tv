// GM-5a：底栏「移动」按钮的只读取证。
// ⛔ 本脚本**不拖动画布、不移动节点**（拖拽的落点自证在 gm3 批已被证伪，见缺陷 526）。
//    只读按钮态、提示条、快捷键切换，stdout 必须落盘以免「可复算数字靠手抄」。
import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
async function 稳(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

// 底栏 7 枚按钮的「是什么」与「现在什么状态」
const 底栏 = () => page.evaluate(()=>{
  const 名=['添加节点','移动','素材库','角色造型室','生成历史','快捷键','教程'];
  const o=[];
  for(const n of 名){
    const b=document.querySelector(`button[aria-label="${n}"]`);
    if(!b){o.push({名:n,存在:false}); continue;}
    const r=b.getBoundingClientRect();
    o.push({名:n, 存在:true,
      框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
      背景:getComputedStyle(b).backgroundColor,
      描边:getComputedStyle(b).borderColor,
      ariaPressed:b.getAttribute('aria-pressed'),
      ariaExpanded:b.getAttribute('aria-expanded'),
      dataPressed:b.getAttribute('data-pressed'),
      class:b.className,
      innerHTML:b.innerHTML.slice(0,120),
      title:b.getAttribute('title'),
      // ⭐ title 是不是 aria 名 —— 之前有人以为 tooltip 另有信息
      tooltip:b.getAttribute('title')===n ? '等于 aria 名' : ('≠ 「'+b.getAttribute('title')+'」')});
  }
  return o;});

// 提示条：只认「叶子节点 + 文字在白名单内 + 有框」
// ⭐ 判据纪律（缺陷 517/521 的反面）：白名单来自**读过的字面量**，不是尺寸/位置阈值。
// ⭐ 容器查找必须在同一次 evaluate 里保留 DOM 引用 —— 存成 plain object 再 contains() 会炸。
const 提示条 = () => page.evaluate(()=>{
  const 白=['移动','V','抓手工具','H','Esc','取消ESC','正在跟随'];
  const 节点=[...document.querySelectorAll('*')].filter(e=>{
    if(e.children.length!==0) return false;
    if(!白.includes((e.innerText||'').trim())) return false;
    const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;});
  const 命中=节点.map(e=>{const r=e.getBoundingClientRect();
    return {文字:(e.innerText||'').trim(),
      框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
      透明度:getComputedStyle(e).opacity, 指针:getComputedStyle(e).pointerEvents};});
  // 最近的「position:absolute 且把这些叶子都包住」的容器 —— 提示条本体
  let 容器=null;
  const 首=节点[0];
  if(首){
    const cand=[...document.querySelectorAll('*')].filter(x=>{
      if(!节点.every(n=>x.contains(n))) return false;
      const cs=getComputedStyle(x); if(cs.position!=='absolute'&&cs.position!=='fixed') return false;
      const r=x.getBoundingClientRect(); return r.width>0&&r.height>0;});
    const 选=cand.sort((a,b)=>{
      const ra=a.getBoundingClientRect(), rb=b.getBoundingClientRect();
      return (ra.width*ra.height)-(rb.width*rb.height);})[0];
    if(选){const r=选.getBoundingClientRect();
      容器={tag:选.tagName, class:String(选.className).slice(0,160),
        框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)],
        opacity:getComputedStyle(选).opacity, pointerEvents:getComputedStyle(选).pointerEvents,
        innerText:选.innerText.replace(/\s+/g,' ').slice(0,140)};}
  }
  return {命中, 容器};
});

// ⭐⭐ tooltip 到底是��么：底栏按钮 title 属性是 null，说明 tooltip 来自 hover 浮层。
const 探tooltip = async (名) => {
  const b=page.locator(`button[aria-label="${名}"]`).first();
  await b.hover(); await page.waitForTimeout(1100);
  const r = await page.evaluate((名)=>{
    const 全=[...document.querySelectorAll('*')].filter(e=>{
      const t=(e.innerText||'').trim(); if(t!==名) return false;
      if(e.children.length!==0) return false;
      const r=e.getBoundingClientRect(); return r.width>0&&r.height>0;});
    return 全.map(e=>{const r=e.getBoundingClientRect();
      return {tag:e.tagName, role:e.getAttribute('role'),
        class:String(e.className).slice(0,140),
        框:[Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)]};});
  }, 名);
  await page.mouse.move(10,400); await page.waitForTimeout(500);
  return r;
};

try {
  await open(page,B); await closePromos(page); T('节点数', await 稳());
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);

  T('A 初始底栏:', await 底栏());
  T('A 初始提示条:', await 提示条());

  // ⭐⭐⭐ 逐枚 hover，读真正的 tooltip 浮层（title 属性全是 null ⇒ 不能拿 title 当 tooltip）
  const tt={};
  for(const n of ['添加节点','移动','素材库','角色造型室','生成历史','快捷键','教程']) tt[n]=await 探tooltip(n);
  T('A 逐枚 hover 出来的 tooltip 浮层:', tt);

  await page.locator('button[aria-label="移动"]').first().click(); await page.waitForTimeout(1500);
  T('B 点「移动」后底栏:', await 底栏());
  T('B 点「移动」后提示条:', await 提示条());
  await page.screenshot({path: resolve('tools','.evidence','gm5-a-点移动后.png')});

  // ⭐⭐⭐ V 是不是「关掉」？按 V 之后底栏还亮不亮、提示条还在不在
  await page.keyboard.press('v'); await page.waitForTimeout(1300);
  T('C 按 v 之后底栏:', await 底栏());
  T('C 按 v 之后提示条:', await 提示条());

  // ⭐⭐⭐ 换到抓手
  await page.keyboard.press('h'); await page.waitForTimeout(1300);
  T('D 按 h 之后底栏:', await 底栏());
  T('D 按 h 之后提示条:', await 提示条());
  await page.screenshot({path: resolve('tools','.evidence','gm5-b-按h后.png')});

  // ⭐⭐⭐ Esc 关不关得掉？
  await page.keyboard.press('Escape'); await page.waitForTimeout(1300);
  T('E 按 Esc 之后底栏:', await 底栏());
  T('E 按 Esc 之后提示条:', await 提示条());
  await page.screenshot({path: resolve('tools','.evidence','gm5-c-按Esc后.png')});

  T('F 收尾 节点数（必须还是 12）:', await page.locator('.react-flow__node').count());
} finally { await browser.close(); }
