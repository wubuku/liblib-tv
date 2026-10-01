// 批次 63 探测四：尺寸弹层的**真身** —— v3 只读到 `302×40` / 四项 1·2·3·4，
// 而手册既有截图 `83-video-size-dialog.png` 明明是 `334×292` **三段**
// （选择比例 6 项 / 选择分辨率 3 项 / 选择生成数量 4 项）。
//
// 🔴 我差点据此把手册的「三段分别选择」订正成「只改张数」——
// **那份旧截图就是这件事的阳性对照**：
// 读数与证据冲突时**先看图**，批次 58 记过这条，批次 63 又差点重演。
//
// 假设：`302×40` 是**弹层展开动画的中间帧**（只量到最后一行的宽度）。
// 验证：开弹层后密集采样 10 点，看高度是不是从 40 长到 292。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const SHOTS = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const FORM = 'form[data-testid="video-generation-form"]';
const OUT = new URL('./_tmp-b63-probe3.json', import.meta.url);
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
  if(r.why)return{ok:false,...r};if(!r.landed)return{ok:false,why:'occluded'};await p.mouse.click(r.cx,r.cy);return{ok:true,aria:r.aria};};
const sizeDialog=()=>p.evaluate(()=>{const cands=Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"],[role="menu"]')).filter(e=>e.getBoundingClientRect().width>1);
  if(!cands.length)return null;const e=cands[cands.length-1];const r=e.getBoundingClientRect();
  return{role:e.getAttribute('role'),box:`${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    text:(e.innerText||'').replace(/\s+/g,' ').trim().slice(0,200),
    groups:Array.from(e.querySelectorAll('*')).filter(x=>{const q=x.getBoundingClientRect();return q.width>150&&q.height>1&&x.children.length>0&&q.height>40;}).length,
    leaves:Array.from(e.querySelectorAll('*')).filter(x=>{const q=x.getBoundingClientRect();return q.width>1&&q.height>1&&x.children.length===0;})
      .map(x=>{const q=x.getBoundingClientRect();return{tag:x.tagName,box:`${Math.round(q.width)}x${Math.round(q.height)}@${Math.round(q.x)},${Math.round(q.y)}`,text:(x.innerText||'').replace(/\s+/g,' ').trim().slice(0,24)};})};});
const priceOf=()=>p.evaluate((F)=>{const f=document.querySelector(F);if(!f)return null;const t=f.innerText||'';
  return{price:(t.match(/Current price[^\n]*/)||[null])[0],bar:((f.querySelector('[data-testid="video-generation-fixed-parameters"]')||{}).innerText||'').replace(/\s+/g,' ').trim()};},FORM);
const out={startedAt:new Date().toISOString()};
let MINE=null;
try{
  MINE=await makeNode('视频'); console.log('建节点:',MINE);
  if(!MINE)throw new Error('建节点失败'); out.nodeId=MINE;
  await p.waitForTimeout(1700);
  console.log('基线:',JSON.stringify(await priceOf()));
  console.log('\n=== 密集采样：开尺寸弹层后的尺寸演化 ===');
  const c=await clickChip('视频尺寸选项');
  console.log('点 chip:',JSON.stringify(c));
  const ser=[]; const t0=Date.now();
  for(const t of [0,100,200,300,450,600,800,1000,1400,2000,3000]){
    const w=t0+t-Date.now(); if(w>0)await p.waitForTimeout(w);
    const d=await sizeDialog();
    ser.push({t,box:d?d.box:null,leaves:d?d.leaves.length:0,text:d?d.text.slice(0,80):null});
    console.log(`  t=${String(t).padStart(4)}ms  box=${d?d.box:'null'}  叶子元素=${d?d.leaves.length:0}  text=${d?JSON.stringify(d.text.slice(0,60)):'-'}`);
  }
  out.series=ser;
  const fin=await sizeDialog();
  console.log('\n=== 稳定后的完整结构 ===');
  console.log('box:',fin.box,'| role:',fin.role);
  console.log('text:',fin.text);
  console.log('叶子元素',fin.leaves.length,'个:');
  for(const l of fin.leaves)console.log(`   ${l.box} «${l.text}»`);
  out.final=fin;
  await p.screenshot({path:new URL('63-size-dialog.png',SHOTS).pathname,clip:{x:340,y:200,width:460,height:400}});
  console.log('📷 63-size-dialog.png');
  await p.keyboard.press('Escape');await p.waitForTimeout(900);

  console.log('\n=== 逐段改比例，看价格 ===');
  out.ratio=[];
  for(const rb of ['21:9','16:9','4:3','1:1','3:4','9:16']){
    const before=await priceOf();
    const oc=await clickChip('视频尺寸选项');
    if(!oc.ok){console.log(`  [${rb}] 开弹层失败`);await p.keyboard.press('Escape');await p.waitForTimeout(700);continue;}
    await p.waitForTimeout(900);
    const hit=await p.evaluate((lb)=>{const d=Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"],[role="menu"]')).filter(e=>e.getBoundingClientRect().width>1).pop();
      if(!d)return{why:'nodlg'};const e=Array.from(d.querySelectorAll('*')).find(x=>x.children.length===0&&(x.innerText||'').trim()===lb);
      if(!e)return{why:'nopt'};e.scrollIntoView({block:'center'});const q=e.getBoundingClientRect();
      const cx=Math.round(q.x+q.width/2),cy=Math.round(q.y+q.height/2);const t=document.elementFromPoint(cx,cy);
      const o=t&&t.closest('*');return{cx,cy,landed:!!t&&(t===e||e.contains(t))};},rb);
    if(!hit.landed){console.log(`  [${rb}] 未命中`,JSON.stringify(hit));await p.keyboard.press('Escape');await p.waitForTimeout(700);continue;}
    await p.mouse.click(hit.cx,hit.cy);await p.waitForTimeout(1500);
    const after=await priceOf();
    console.log(`  «${rb}»  ${before.bar} ⇒ ${after.bar}   |   ${before.price} ⇒ ${after.price}${after.price!==before.price?'  ★':''}`);
    out.ratio.push({ratio:rb,before,after,changed:after.price!==before.price});
    await p.keyboard.press('Escape');await p.waitForTimeout(800);
  }
  const cE=await credit();console.log('\n积分全程:',cE);
  out.creditEnd=cE;
}catch(e){console.error('ABORT:',e.message);out.error=e.message;}
finally{
  if(MINE)console.log('\n删',MINE,'->',await deleteById(MINE));
  for(let i=0;i<3;i++){await p.keyboard.press('Escape');await p.waitForTimeout(300);}
  await restoreZoom();
  for(let i=0;i<3;i++){await p.keyboard.press('Escape');await p.waitForTimeout(300);}
  const cp=await p.evaluate(()=>Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map(e=>{const m=/translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform||'');return[e.getAttribute('data-id'),m?[Math.round(parseFloat(m[1])*100)/100,Math.round(parseFloat(m[2])*100)/100]:null];})));
  let dev=0;for(const[id,b2]of Object.entries(BASE.nodes)){const c2=cp[id];const d=c2&&b2.canvas?[Math.round((c2[0]-b2.canvas[0])*100)/100,Math.round((c2[1]-b2.canvas[1])*100)/100]:'MISSING';
    if(d==='MISSING'||(Array.isArray(d)&&(Math.abs(d[0])>0.01||Math.abs(d[1])>0.01)))dev++;}
  console.log('终态:',await statusLine(),'| 缩放',await zoomOf(),'| 积分',await credit(),'| 节点',Object.keys(cp).length,'| 偏离',dev);
  out.end={status:await statusLine(),credit:await credit(),dev};
  writeFileSync(OUT,JSON.stringify(out,null,1));console.log('写入',OUT.pathname);
  await b.close();
}
