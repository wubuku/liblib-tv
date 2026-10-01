// 批次 63 探测五：**换到 2.0 VIP 下**重测尺寸弹层。
//
// 探测四证明弹层**不是动画**（3 秒恒定 302×40 / 四项 1·2·3·4），
// 而手册旧截图 `83-video-size-dialog.png` 是 `334×292` **三段**
// （选择比例 6 项 / 选择分辨率 3 项 / 选择生成数量 4 项）。
// 两次读的**模型不同**：探测四的基线是 `Wan 3.0`。
//
// 🔑 所以真正的结论不是「我读错了」，而是
//    **尺寸弹层的内容随模型而变** —— 又是一次「只测了一支就外推」。
//    手册的「三段分别选择」在 `2.0 VIP` 下是对的；我拿 `Wan 3.0` 去否定它是错的。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const SHOTS = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const FORM = 'form[data-testid="video-generation-form"]';
const OUT = new URL('./_tmp-b63-probe4.json', import.meta.url);
const NAME_SEL = 'span.block.overflow-hidden.truncate';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const credit=()=>p.evaluate(()=>{const m=document.body.innerText.match(/(\d[\d,]*)\s*基础会员/);return m?parseInt(m[1].replace(/,/g,''),10):null;});
const statusLine=()=>p.evaluate(()=>(document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/)||['?'])[0]);
const zoomOf=()=>p.evaluate(()=>(document.querySelector('button[aria-label^="Zoom options"]')||{}).getAttribute?.('aria-label'));
const hasForm=()=>p.evaluate((F)=>{const f=document.querySelector(F);return !!(f&&f.getBoundingClientRect().width>1);},FORM);
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
const ensurePanel=async(id)=>{if(await hasForm())return true;if(!(await selectMine(id)))return false;await p.waitForTimeout(1600);return await hasForm();};
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
  const e=Array.from(f.querySelectorAll('[aria-label]')).find(x=>(x.getAttribute('aria-label')||'').startsWith(pr));
  if(!e)return{why:'nochip',avail:Array.from(f.querySelectorAll('[aria-label]')).map(x=>x.getAttribute('aria-label'))};
  const q=e.getBoundingClientRect();const cx=Math.round(q.x+q.width/2),cy=Math.round(q.y+q.height/2);const t=document.elementFromPoint(cx,cy);const o=t&&t.closest('[aria-label]');
  return{cx,cy,aria:e.getAttribute('aria-label'),landed:!!o&&o===e};},[FORM,pre]);
  if(r.why)return{ok:false,...r};if(!r.landed)return{ok:false,why:'occluded'};await p.mouse.click(r.cx,r.cy);await p.waitForTimeout(1500);return{ok:true,aria:r.aria};};
const pickModel=async(nm)=>{const r=await p.evaluate(([S,n])=>{const pop=Array.from(document.querySelectorAll('[role="listbox"]')).filter(e=>e.getBoundingClientRect().width>1).pop();
  if(!pop)return{why:'nopop'};const el=Array.from(pop.querySelectorAll(S)).find(x=>(x.innerText||'').trim()===n);
  if(!el)return{why:'gone'};el.scrollIntoView({block:'center'});
  let dis=null,cl=el;for(let n2=el;n2&&n2!==pop;n2=n2.parentElement){if(n2.getAttribute&&n2.getAttribute('aria-disabled')!==null){dis=n2.getAttribute('aria-disabled');cl=n2;break;}}
  const q=cl.getBoundingClientRect();const cx=Math.round(q.x+q.width/2),cy=Math.round(q.y+Math.min(q.height/2,30));
  const t=document.elementFromPoint(cx,cy);return{cx,cy,dis,landed:!!t&&(t===el||el.contains(t)||el.parentElement.contains(t))};},[NAME_SEL,nm]);
  if(r.why)return{ok:false,...r};if(r.dis==='true')return{ok:false,why:'disabled'};if(!r.landed)return{ok:false,why:'occluded'};
  await p.mouse.click(r.cx,r.cy);await p.waitForTimeout(1800);return{ok:true};};
const read=()=>p.evaluate((F)=>{const f=document.querySelector(F);if(!f)return null;const bar=f.querySelector('[data-testid="video-generation-fixed-parameters"]');const t=f.innerText||'';
  return{bar:bar?(bar.innerText||'').replace(/\s+/g,' ').trim():null,price:(t.match(/Current price[^\n]*/)||[null])[0],original:(t.match(/Original price[^\n]*/)||[null])[0]};},FORM);
const dlg=()=>p.evaluate(()=>{const l=Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"],[role="menu"]')).filter(e=>e.getBoundingClientRect().width>1);
  if(!l.length)return null;const e=l[l.length-1];const r=e.getBoundingClientRect();
  return{role:e.getAttribute('role'),box:`${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    text:(e.innerText||'').replace(/\s+/g,' ').trim().slice(0,300),
    sections:Array.from(e.querySelectorAll('*')).filter(x=>{const q=x.getBoundingClientRect();return q.width>200&&q.height>14&&q.height<26&&x.children.length===0;})
      .map(x=>(x.innerText||'').trim()).filter(Boolean).slice(0,8),
    leaves:Array.from(e.querySelectorAll('*')).filter(x=>{const q=x.getBoundingClientRect();return q.width>1&&q.height>1&&x.children.length===0;})
      .map(x=>{const q=x.getBoundingClientRect();return{box:`${Math.round(q.width)}x${Math.round(q.height)}@${Math.round(q.x)},${Math.round(q.y)}`,text:(x.innerText||'').replace(/\s+/g,' ').trim().slice(0,20)};})};});
const out={startedAt:new Date().toISOString()};
let MINE=null;
try{
  MINE=await makeNode('视频');console.log('建节点:',MINE);if(!MINE)throw new Error('建节点失败');out.nodeId=MINE;
  await p.waitForTimeout(1700);
  console.log('基线:',JSON.stringify(await read()));
  console.log('\n切到 2.0 VIP：',JSON.stringify(await clickChip('选择模型')),JSON.stringify(await pickModel('即梦 Seedance 2.0 VIP')));
  await p.keyboard.press('Escape');await p.waitForTimeout(900);
  if(!(await ensurePanel(MINE))){console.log('面板掉了');throw new Error('nopanel');}
  console.log('切后:',JSON.stringify(await read()));

  console.log('\n=== 2.0 VIP 下的尺寸弹层 ===');
  const oc=await clickChip('视频尺寸选项');
  console.log('开弹层:',JSON.stringify(oc));
  await p.waitForTimeout(1000);
  const d=await dlg();
  console.log('box:',d.box,'| role:',d.role);
  console.log('分段标题:',JSON.stringify(d.sections));
  console.log('全文:',d.text);
  console.log('叶子元素',d.leaves.length,'个:');
  for(const l of d.leaves)console.log(`   ${l.box} «${l.text}»`);
  out.dialog2vip=d;
  await p.screenshot({path:new URL('63-size-dialog-2vip.png',SHOTS).pathname,clip:{x:330,y:190,width:480,height:420}});
  console.log('📷 63-size-dialog-2vip.png');
  await p.keyboard.press('Escape');await p.waitForTimeout(900);

  // ── 隔离变量：手册旧截图的 bar 是「16:9 · 720P ⭐ · **1**」（张数=1 且 720P 带 ⭐）
  //    先把张数设回 1，再开弹层，看是否变成三段。
  console.log('\n=== 隔离：把张数设回 1，再开弹层 ===');
  out.isolate = {};
  for (const step of ['to1']) {
    if (!(await ensurePanel(MINE))) break;
    const before = await read();
    const o = await clickChip('视频尺寸选项');
    console.log('  开弹层:', JSON.stringify(o));
    await p.waitForTimeout(900);
    const hit = await p.evaluate(()=>{const dd=Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"],[role="menu"]')).filter(e=>e.getBoundingClientRect().width>1).pop();
      if(!dd)return{why:'nodlg'};const e=Array.from(dd.querySelectorAll('*')).find(x=>x.children.length===0&&(x.innerText||'').trim()==='1');
      if(!e)return{why:'nopt'};const q=e.getBoundingClientRect();
      return{cx:Math.round(q.x+q.width/2),cy:Math.round(q.y+q.height/2),landed:!!document.elementFromPoint(Math.round(q.x+q.width/2),Math.round(q.y+q.height/2))};});
    if (hit.landed) { await p.mouse.click(hit.cx, hit.cy); await p.waitForTimeout(1600); }
    await p.keyboard.press('Escape'); await p.waitForTimeout(900);
    if (!(await ensurePanel(MINE))) break;
    const after = await read();
    console.log('  张数 4 ⇒ 1:', before.bar, '⇒', after.bar, '|', before.price, '⇒', after.price);
    out.isolate.afterSet1 = after;
    const o2 = await clickChip('视频尺寸选项');
    await p.waitForTimeout(1000);
    const d2 = await dlg();
    console.log('  张数=1 时的弹层:', d2 ? d2.box : 'null', '| 全文:', d2 ? JSON.stringify(d2.text.slice(0,150)) : '-');
    console.log('  叶子元素:', d2 ? d2.leaves.length : 0);
    if (d2) for (const l of d2.leaves) console.log(`     ${l.box} «${l.text}»`);
    out.isolate.dialogAt1 = d2;
    if (d2 && d2.box !== '302x40@390,551') {
      await p.screenshot({ path: new URL('63-size-dialog-at1.png', SHOTS).pathname, clip: { x: 330, y: 180, width: 480, height: 440 } });
      console.log('  📷 63-size-dialog-at1.png（张数=1 时的三段弹层）');
    }
    await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  }
  // chip 内部结构：是不是一个 button 里有多个可点子段
  console.log('\n=== chip 内部结构 ===');
  const chipIn = await p.evaluate((F)=>{const f=document.querySelector(F);if(!f)return null;
    const e=Array.from(f.querySelectorAll('[aria-label]')).find(x=>(x.getAttribute('aria-label')||'').startsWith('视频尺寸选项'));if(!e)return null;
    const r=e.getBoundingClientRect();
    return { tag:e.tagName, aria:e.getAttribute('aria-label'), box:`${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      innerText:(e.innerText||'').replace(/\s+/g,' ').trim(),
      children:Array.from(e.querySelectorAll('*')).map(x=>{const q=x.getBoundingClientRect();
        return {tag:x.tagName,cls:String(x.className||'').slice(0,32),box:`${Math.round(q.width)}x${Math.round(q.height)}@${Math.round(q.x)},${Math.round(q.y)}`,text:(x.innerText||'').replace(/\s+/g,' ').trim().slice(0,16)};}).slice(0,14),
      html:(e.innerHTML||'').slice(0,600) };},FORM);
  console.log(JSON.stringify(chipIn,null,1).slice(0,2200));
  out.chipInner = chipIn;

  out.ratio=[];out.res=[];
  for(const grp of [{key:'ratio',items:['21:9','16:9','4:3','1:1','3:4','9:16']},{key:'res',items:['720P','1080P','4K']}]){
    for(const lb of grp.items){
      if(!(await ensurePanel(MINE))){console.log('面板掉了');break;}
      const before=await read();
      const o=await clickChip('视频尺寸选项');
      if(!o.ok){console.log(`  [${lb}] 开弹层失败`,JSON.stringify(o));await p.keyboard.press('Escape');await p.waitForTimeout(800);continue;}
      await p.waitForTimeout(800);
      const hit=await p.evaluate((t2)=>{const dd=Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"],[role="menu"]')).filter(e=>e.getBoundingClientRect().width>1).pop();
        if(!dd)return{why:'nodlg'};const e=Array.from(dd.querySelectorAll('*')).find(x=>x.children.length===0&&(x.innerText||'').replace(/\s+/g,' ').trim()===t2);
        if(!e)return{why:'nopt'};e.scrollIntoView({block:'center'});const q=e.getBoundingClientRect();
        const cx=Math.round(q.x+q.width/2),cy=Math.round(q.y+q.height/2);const el=document.elementFromPoint(cx,cy);
        return{cx,cy,landed:!!el&&(el===e||e.contains(el))};},lb);
      if(!hit.landed){console.log(`  [${lb}] 未命中`,JSON.stringify(hit));await p.keyboard.press('Escape');await p.waitForTimeout(800);continue;}
      await p.mouse.click(hit.cx,hit.cy);await p.waitForTimeout(1600);
      if(!(await ensurePanel(MINE))){console.log(`  [${lb}] 选完面板没了`);continue;}
      const after=await read();
      console.log(`  «${lb}»  ${before.bar} ⇒ ${after.bar}   |   ${before.price} ⇒ ${after.price}${after.price!==before.price?'  ★':''}`);
      (grp.key==='ratio'?out.ratio:out.res).push({v:lb,before,after,changed:after.price!==before.price});
      await p.keyboard.press('Escape');await p.waitForTimeout(800);
    }
  }
  const cE=await credit();console.log('\n积分全程:',cE);out.creditEnd=cE;
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
