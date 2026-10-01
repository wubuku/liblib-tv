// 批次 63 探测六：找到尺寸弹层的**真正外层容器**。
//
// 🔴 链路回顾（本批第三次「读数与图冲突」）：
//   1. 我用 `role ∈ {dialog,listbox,menu}` 读弹层 ⇒ `302×40` / 四项 `1 2 3 4`
//   2. 手册旧截图 `83` 是 `334×292` 三段 ⇒ 我以为旧截图是旧版本
//   3. **我自己截的图 `63-size-dialog-2vip.png` 清清楚楚是三段**
//      （选择比例 6 项 / 选择分辨率 3 项 / 选择生成数量 4 项）
// ⇒ 真相是：**我的选择器只抓到了「选择生成数量」那一段**（它自带 role="listbox"），
//   外层容器 role 不在 {dialog,listbox,menu} 里。
//   这是假阴性的**第三种成因**：前两种是「找的不是同一个东西」「恒真元素」，
//   这一种是「**选择器只匹配到内层**」。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const FORM = 'form[data-testid="video-generation-form"]';
const OUT = new URL('./_tmp-b63-probe5.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const credit=()=>p.evaluate(()=>{const m=document.body.innerText.match(/(\d[\d,]*)\s*基础会员/);return m?parseInt(m[1].replace(/,/g,''),10):null;});
const statusLine=()=>p.evaluate(()=>(document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/)||['?'])[0]);
const zoomOf=()=>p.evaluate(()=>(document.querySelector('button[aria-label^="Zoom options"]')||{}).getAttribute?.('aria-label'));
const isEmpty=(x,y)=>p.evaluate(([x,y])=>{const el=document.elementFromPoint(x,y);if(!el)return true;if(el.closest('.react-flow__node'))return false;
  if(el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"],[data-testid="canvas-feature-sidecar"]'))return false;return true;},[x,y]);
const findEmpty=async()=>{for(let y=110;y<=600;y+=20)for(let x=90;x<=1240;x+=20){if(x>1140&&y>570)continue;if(await isEmpty(x,y))return{x,y};}return null;};
const deselect=async()=>{for(let i=0;i<3;i++){await p.keyboard.press('Escape');await p.waitForTimeout(320);}const e=await findEmpty();if(e){await p.mouse.click(e.x,e.y);await p.waitForTimeout(600);}};
const makeNode=async(k)=>{await deselect();const rb=await p.evaluate((nm)=>{const e=Array.from(document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button')).find(x=>(x.getAttribute('aria-label')||'').startsWith(nm));if(!e)return null;const r=e.getBoundingClientRect();return{cx:Math.round(r.x+r.width/2),cy:Math.round(r.y+r.height/2)};},k);
  if(!rb)return null;const pre=await p.evaluate(()=>Array.from(document.querySelectorAll('.react-flow__node')).map(e=>e.getAttribute('data-id')));
  await p.mouse.click(rb.cx,rb.cy);await p.waitForTimeout(3400);
  const m=(await p.evaluate(()=>Array.from(document.querySelectorAll('.react-flow__node')).map(e=>e.getAttribute('data-id')))).filter(x=>!pre.includes(x));return m.length===1?m[0]:null;};
const selectMine=async(id)=>{await deselect();const pts=await p.evaluate((vid)=>{const n=document.querySelector(`.react-flow__node[data-id="${vid}"]`);if(!n)return[];const r=n.getBoundingClientRect();const o=[];
  for(let fy=0.14;fy<=0.88;fy+=0.07)for(let fx=0.14;fx<=0.88;fx+=0.07){const x=Math.round(r.x+r.width*fx),y=Math.round(r.y+r.height*fy);
    if(x<2||y<2||x>innerWidth-2||y>innerHeight-2)continue;const el=document.elementFromPoint(x,y);if(!el||!el.closest(`.react-flow__node[data-id="${vid}"]`))continue;
    if(el.closest('button,a,[role="button"],input,textarea,select,[role="menu"]'))continue;o.push({x,y});}return o;},id);
  for(const pt of pts){await p.mouse.click(pt.x,pt.y);await p.waitForTimeout(600);
    if(await p.evaluate((v)=>!!document.querySelector(`.react-flow__node[data-id="${v}"].selected`),id))return true;}return false;};
const deleteById=async(id)=>{for(let i=0;i<3;i++){await p.keyboard.press('Escape');await p.waitForTimeout(320);}await selectMine(id);await p.waitForTimeout(400);
  await p.evaluate((vid)=>{const e=document.querySelector(`.react-flow__node[data-id="${vid}"]`);if(!e)return;const r=e.getBoundingClientRect();
    for(let fy=0.12;fy<=0.9;fy+=0.08)for(let fx=0.12;fx<=0.9;fx+=0.08){const x=Math.round(r.x+r.width*fx),y=Math.round(r.y+r.height*fy);
      const t=document.elementFromPoint(x,y);if(!t||!t.closest(`.react-flow__node[data-id="${vid}"]`))continue;if(t.closest('button,a,[role="button"],input,textarea,select'))continue;
      e.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,clientX:x,clientY:y}));e.dispatchEvent(new MouseEvent('mouseup',{bubbles:true,clientX:x,clientY:y}));
      e.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:x,clientY:y}));return;}},id);
  await p.waitForTimeout(900);
  if(await p.evaluate((v)=>!!document.querySelector(`.react-flow__node[data-id="${v}"].selected`),id)){
    await p.evaluate(()=>{const e=document.querySelector('.react-flow__node.selected');if(!e)return;const r=e.getBoundingClientRect();
      e.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,clientX:Math.round(r.x+r.width/2),clientY:Math.round(r.y+14)}));});
    await p.waitForTimeout(800);
    await p.evaluate(()=>{const m=Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter(e=>e.getBoundingClientRect().width>1).pop();
      const it=m&&Array.from(m.querySelectorAll('[role="menuitem"]')).find(x=>/删除/.test(x.innerText||''));if(it)it.click();});
    await p.waitForTimeout(1400);}
  for(let i=0;i<3;i++){await p.keyboard.press('Escape');await p.waitForTimeout(320);}
  return (await p.evaluate((v)=>!document.querySelector(`.react-flow__node[data-id="${v}"]`),id))?'deleted':'STILL-THERE';};
const restoreZoom=async()=>{for(let t=0;t<3;t++){const z=await zoomOf();if(z&&z.includes('60%')){console.log('  缩放 ok',z);return true;}
  await p.click('button[aria-label^="Zoom options"]');await p.waitForTimeout(700);const s='input[data-testid=canvas-zoom-percent-input]';
  if(await p.$(s)){await p.fill(s,'60');await p.keyboard.press('Enter');await p.waitForTimeout(1100);}else{await p.keyboard.press('Escape');await p.waitForTimeout(400);}}
  console.log('  缩放 FAILED',await zoomOf());return false;};
const clickChip=async(pre)=>{const r=await p.evaluate(([F,pr])=>{const f=document.querySelector(F);if(!f)return{why:'noform'};
  const e=Array.from(f.querySelectorAll('[aria-label]')).find(x=>(x.getAttribute('aria-label')||'').startsWith(pr));if(!e)return{why:'nochip'};
  const q=e.getBoundingClientRect();const cx=Math.round(q.x+q.width/2),cy=Math.round(q.y+q.height/2);const t=document.elementFromPoint(cx,cy);const o=t&&t.closest('[aria-label]');
  return{cx,cy,aria:e.getAttribute('aria-label'),landed:!!o&&o===e};},[FORM,pre]);
  if(r.why)return{ok:false,...r};if(!r.landed)return{ok:false,why:'occluded'};await p.mouse.click(r.cx,r.cy);await p.waitForTimeout(1500);return{ok:true,aria:r.aria};};
const out={startedAt:new Date().toISOString()};
let MINE=null;
try{
  MINE=await makeNode('视频');console.log('建节点:',MINE);if(!MINE)throw new Error('建节点失败');out.nodeId=MINE;
  await p.waitForTimeout(1700);
  console.log('开弹层:',JSON.stringify(await clickChip('视频尺寸选项')));
  await p.waitForTimeout(1200);
  const full=await p.evaluate(()=>{
    // 从「21:9」这个叶子往上爬，看外层到底是谁
    const seed=Array.from(document.querySelectorAll('*')).find(x=>x.children.length===0&&(x.innerText||'').trim()==='21:9');
    if(!seed)return{err:'no-seed'};
    const chain=[];let n=seed;
    for(let i=0;i<9&&n;i++){const r=n.getBoundingClientRect();
      chain.push({tag:n.tagName,role:n.getAttribute('role'),tid:n.getAttribute('data-testid'),aria:n.getAttribute('aria-label'),
        cls:String(n.className||'').slice(0,44),box:`${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
        text:(n.innerText||'').replace(/\s+/g,' ').trim().slice(0,70)});
      n=n.parentElement;}
    // 「选择生成数量」那一段自己的 role
    const cnt=Array.from(document.querySelectorAll('*')).find(x=>x.children.length===0&&(x.innerText||'').trim()==='选择生成数量');
    const cntChain=[];let m=cnt;
    for(let i=0;i<5&&m;i++){const r=m.getBoundingClientRect();
      cntChain.push({tag:m.tagName,role:m.getAttribute('role'),cls:String(m.className||'').slice(0,40),
        box:`${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`});m=m.parentElement;}
    return{seedChain:chain,cntChain};
  });
  console.log('\n=== 从叶子「21:9」往上的祖先链 ===');
  for(const c of full.seedChain)console.log('  ',JSON.stringify(c));
  console.log('\n=== 「选择生成数量」标题往上的链（解释 302×40 是谁）===');
  for(const c of full.cntChain)console.log('  ',JSON.stringify(c));
  out.full=full;
  // 顺带：外层弹层的三段逐项
  const sections=await p.evaluate(()=>{
    const seed=Array.from(document.querySelectorAll('*')).find(x=>x.children.length===0&&(x.innerText||'').trim()==='21:9');
    let outer=seed;for(let i=0;i<9&&outer;i++){const r=outer.getBoundingClientRect();if(r.width>=250&&r.height>=200){break;}outer=outer.parentElement;}
    if(!outer)return null;const r=outer.getBoundingClientRect();
    return{box:`${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,role:outer.getAttribute('role'),
      text:(outer.innerText||'').replace(/\s+/g,' ').trim().slice(0,300),
      clicks:Array.from(outer.querySelectorAll('*')).filter(x=>{const q=x.getBoundingClientRect();return q.width>20&&q.height>20&&x.children.length===0;})
        .map(x=>{const q=x.getBoundingClientRect();return{box:`${Math.round(q.width)}x${Math.round(q.height)}@${Math.round(q.x)},${Math.round(q.y)}`,text:(x.innerText||'').replace(/\s+/g,' ').trim().slice(0,16)};})};});
  console.log('\n=== 外层容器 ===');
  console.log(JSON.stringify(sections,null,1).slice(0,2500));
  out.sections=sections;
}catch(e){console.error('ABORT:',e.message);out.error=e.message;}
finally{
  if(MINE)console.log('\n删',MINE,'->',await deleteById(MINE));
  for(let i=0;i<3;i++){await p.keyboard.press('Escape');await p.waitForTimeout(300);}
  await restoreZoom();
  for(let i=0;i<3;i++){await p.keyboard.press('Escape');await p.waitForTimeout(300);}
  const cp=await p.evaluate(()=>Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map(e=>{const m=/translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform||'');return[e.getAttribute('data-id'),m?[Math.round(parseFloat(m[1])*100)/100,Math.round(parseFloat(m[2])*100)/100]:null];})));
  let dev=0;for(const[id,b2]of Object.entries(BASE.nodes)){const c2=cp[id];const d2=c2&&b2.canvas?[Math.round((c2[0]-b2.canvas[0])*100)/100,Math.round((c2[1]-b2.canvas[1])*100)/100]:'MISSING';
    if(d2==='MISSING'||(Array.isArray(d2)&&(Math.abs(d2[0])>0.01||Math.abs(d2[1])>0.01)))dev++;}
  console.log('终态:',await statusLine(),'| 缩放',await zoomOf(),'| 积分',await credit(),'| 节点',Object.keys(cp).length,'| 偏离',dev);
  out.end={status:await statusLine(),credit:await credit(),dev};
  writeFileSync(OUT,JSON.stringify(out,null,1));console.log('写入',OUT.pathname);
  await b.close();
}
