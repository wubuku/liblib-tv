// 批次 64 探测二：把「入口能不能开文件选择器」与「上传本身通不通」**拆成两个问题**。
//
// 上一轮：点「上传」8 秒内没有 filechooser 事件。
// 但 DOM 里有一个**常驻的隐藏 `input[type=file]`**（0×0、`multiple=true`、
// accept 覆盖 50+ 种类型）。所以要分清：
//   A. 入口的**触发**是否有效（点它会不会真的开选择器）
//   B. 给那个 input 塞文件，**上传本身**通不通
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const FILE = '/tmp/b22-upload.png';
const OUT = new URL('./_tmp-b64-probe2.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
let fcEvents = [];
p.on('filechooser', (c) => { fcEvents.push({ multiple: c.isMultiple() }); });
const statusLine=()=>p.evaluate(()=>(document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/)||['?'])[0]);
const credit=()=>p.evaluate(()=>{const m=document.body.innerText.match(/(\d[\d,]*)\s*基础会员/);return m?parseInt(m[1].replace(/,/g,''),10):null;});
const zoomOf=()=>p.evaluate(()=>(document.querySelector('button[aria-label^="Zoom options"]')||{}).getAttribute?.('aria-label'));
const nodeIds=()=>p.evaluate(()=>Array.from(document.querySelectorAll('.react-flow__node')).map(e=>e.getAttribute('data-id')));
const isEmpty=(x,y)=>p.evaluate(([x,y])=>{const el=document.elementFromPoint(x,y);if(!el)return true;if(el.closest('.react-flow__node'))return false;
  if(el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"],[data-testid="canvas-feature-sidecar"]'))return false;return true;},[x,y]);
const findEmpty=async()=>{for(let y=110;y<=600;y+=20)for(let x=90;x<=1240;x+=20){if(x>1140&&y>570)continue;if(await isEmpty(x,y))return{x,y};}return null;};
const deselect=async()=>{for(let i=0;i<3;i++){await p.keyboard.press('Escape');await p.waitForTimeout(320);}const e=await findEmpty();if(e){await p.mouse.click(e.x,e.y);await p.waitForTimeout(600);}};
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
const restoreZoom=async()=>{for(let t=0;t<3;t++){const z=await zoomOf();if(z&&z.includes('60%')){return true;}
  await p.click('button[aria-label^="Zoom options"]');await p.waitForTimeout(700);const s='input[data-testid=canvas-zoom-percent-input]';
  if(await p.$(s)){await p.fill(s,'60');await p.keyboard.press('Enter');await p.waitForTimeout(1100);}else{await p.keyboard.press('Escape');await p.waitForTimeout(400);}}
  return false;};
const out={startedAt:new Date().toISOString()};
const MINE=[];
try{
  console.log('=== A. 入口触发：点「上传」到底会不会开 filechooser ===');
  const up=await p.evaluate(()=>{const e=Array.from(document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button, [data-testid="canvas-fixed-toolbar-left-rail"] button'))
    .find(x=>(x.getAttribute('aria-label')||'')==='上传');if(!e)return null;const r=e.getBoundingClientRect();
    return{cx:Math.round(r.x+r.width/2),cy:Math.round(r.y+r.height/2),tag:e.tagName,html:(e.innerHTML||'').slice(0,200)};});
  console.log('  上传按钮:',JSON.stringify(up));
  await deselect(); fcEvents=[];
  await p.mouse.click(up.cx,up.cy);
  await p.waitForTimeout(3500);
  console.log('  鼠标点击后 filechooser 事件数 =', fcEvents.length, JSON.stringify(fcEvents));
  if (!fcEvents.length) {
    console.log('  → 换成 DOM 级 .click() 再试');
    await p.evaluate(()=>{const e=Array.from(document.querySelectorAll('[data-testid="canvas-fixed-toolbar-left-rail"] button, aside[data-testid="canvas-fixed-toolbar-left-rail"] button')).find(x=>(x.getAttribute('aria-label')||'')==='上传');if(e)e.click();});
    await p.waitForTimeout(3500);
    console.log('  DOM click 后 filechooser 事件数 =', fcEvents.length, JSON.stringify(fcEvents));
  }
  out.entry = { button: up, fcAfterMouse: fcEvents.length };
  for(let i=0;i<3;i++){await p.keyboard.press('Escape');await p.waitForTimeout(300);}

  console.log('\n=== B. 上传本身：给隐藏 input 塞文件 ===');
  const infos=await p.evaluate(()=>Array.from(document.querySelectorAll('input[type=file]')).map((e,i)=>({i,multiple:e.multiple,acceptLen:(e.accept||'').length,vis:e.getBoundingClientRect().width>1})));
  console.log('  input[type=file] 数量 =', infos.length, JSON.stringify(infos));
  out.fileInputs=infos;
  const pre=await nodeIds();
  console.log('  上传前节点数 =', pre.length, '| 积分', await credit());
  const t0=Date.now();
  // 用 DOM 触发 change：Playwright 的 setInputFiles 需要 ElementHandle
  const handles = await p.$$('input[type=file]');
  console.log('  拿到 handle 数 =', handles.length);
  if (!handles.length) throw new Error('没有 input[type=file]');
  await handles[0].setInputFiles(FILE);
  console.log('  已 setInputFiles');
  const ser=[];
  for (const t of [0,400,900,1500,2200,3200,4500,6000,8000]) {
    const w=t0+t-Date.now(); if(w>0)await p.waitForTimeout(w);
    const ids=(await nodeIds()).filter(x=>!pre.includes(x));
    let rd=null;
    if(ids.length===1) rd=await p.evaluate((vid)=>{const e=document.querySelector(`.react-flow__node[data-id="${vid}"]`);if(!e)return null;
      const r=e.getBoundingClientRect();const vis=(x)=>{const q=x.getBoundingClientRect();return q.width>1&&q.height>1;};
      const t=Array.from(e.querySelectorAll('*')).find(x=>vis(x)&&/Rename /.test(x.getAttribute('aria-label')||''));
      return{cls:Array.from(e.classList).filter(c=>c.startsWith('react-flow__node-')).join(' '),aria:e.getAttribute('aria-label'),
        title:t?(t.getAttribute('aria-label')||'').replace(/^Rename /,''):null,
        box:`${Math.round(r.width)}x${Math.round(r.height)}`,
        imgs:Array.from(e.querySelectorAll('img')).filter(vis).map(x=>`${x.naturalWidth}x${x.naturalHeight} src=${(x.getAttribute('src')||'').slice(0,30)}`),
        text:(e.innerText||'').replace(/\s+/g,' ').trim().slice(0,80)};},ids[0]);
    ser.push({t,n:ids.length,id:ids[0]||null,status:await statusLine(),credit:await credit(),rd});
    console.log(`  t=${String(t).padStart(4)}ms 新增=${ids.length} ${await statusLine()} 积分${await credit()}` + (rd?` | ${rd.cls} | 标题=${JSON.stringify(rd.title)} | img=${JSON.stringify(rd.imgs)}`:''));
    if(ids.length===1&&!MINE.includes(ids[0]))MINE.push(ids[0]);
  }
  out.series=ser;
  const ids=(await nodeIds()).filter(x=>!pre.includes(x));
  console.log('\n  最终新增 =', JSON.stringify(ids), '| 积分', await credit());
  if(ids.length===1){
    await p.waitForTimeout(1200);
    if(await selectMine(ids[0])){await p.waitForTimeout(1500);
      const tb=await p.evaluate(()=>{const t=document.querySelector('[data-testid="node-toolbar"]');if(!t)return null;const r=t.getBoundingClientRect();
        return{box:`${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
          btns:Array.from(t.querySelectorAll('button,[role="button"]')).filter(x=>x.getBoundingClientRect().width>1).map(x=>(x.getAttribute('aria-label')||(x.innerText||'').trim().slice(0,10)))};});
      console.log('  选中后工具条:',JSON.stringify(tb));
      out.toolbar=tb;
      await p.screenshot({path:new URL('64-upload-node-selected.png',new URL('../docs/user-manual/jimeng-canvas/screenshots/',import.meta.url)).pathname,clip:{x:250,y:400,width:740,height:270}});
      console.log('  📷 64-upload-node-selected.png');
    }
  }
  const cE=await credit();console.log('\n=== 积分全程 ===',cE, '| Δ=',cE-805);
  out.creditEnd=cE;
}catch(e){console.error('ABORT:',e.message);out.error=e.message;}
finally{
  const now=await nodeIds();
  for(const id of MINE)if(now.includes(id))console.log('删',id,'->',await deleteById(id));
  for(let i=0;i<3;i++){await p.keyboard.press('Escape');await p.waitForTimeout(300);}
  await restoreZoom();
  for(let i=0;i<3;i++){await p.keyboard.press('Escape');await p.waitForTimeout(300);}
  const cp=await p.evaluate(()=>Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map(e=>{const m=/translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform||'');return[e.getAttribute('data-id'),m?[Math.round(parseFloat(m[1])*100)/100,Math.round(parseFloat(m[2])*100)/100]:null];})));
  let dev=0;for(const[id,b2]of Object.entries(BASE.nodes)){const c2=cp[id];const d2=c2&&b2.canvas?[Math.round((c2[0]-b2.canvas[0])*100)/100,Math.round((c2[1]-b2.canvas[1])*100)/100]:'MISSING';
    if(d2==='MISSING'||(Array.isArray(d2)&&(Math.abs(d2[0])>0.01||Math.abs(d2[1])>0.01)))dev++;}
  console.log('终态:',await statusLine(),'| 缩放',await zoomOf(),'| 积分',await credit(),'| 节点',Object.keys(cp).length,'| 偏离',dev);
  out.end={status:await statusLine(),credit:await credit(),dev,mineLeft:MINE.filter(i=>cp[i])};
  writeFileSync(OUT,JSON.stringify(out,null,1));console.log('写入',OUT.pathname);
  await b.close();
}
