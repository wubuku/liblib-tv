// 批次 63 探测三：三个结构问题 —— ① 模型项的「名称」到底在哪个子元素里
// （v2 用 `split(/(?=\s)/)[0]` 提取，全部变成「即梦」⇒ 五个即梦模型只测了第一个）；
// ② 模型列表 400×384 但项到 y=811，**下半截在视口外**，得滚动；
// ③ 时长弹层是 role=dialog 400×100，**用 option/menuitem/li 一个都选不到**。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const FORM = 'form[data-testid="video-generation-form"]';
const OUT = new URL('./_tmp-b63-probe2.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const credit = () => p.evaluate(() => { const m=document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m?parseInt(m[1].replace(/,/g,''),10):null; });
const statusLine = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/)||['?'])[0]);
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]')||{}).getAttribute?.('aria-label'));
const nodeIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map(e=>e.getAttribute('data-id')));
const isEmpty=(x,y)=>p.evaluate(([x,y])=>{const el=document.elementFromPoint(x,y);if(!el)return true;if(el.closest('.react-flow__node'))return false;
  if(el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"],[data-testid="canvas-feature-sidecar"]'))return false;return true;},[x,y]);
const findEmpty=async()=>{for(let y=110;y<=600;y+=20)for(let x=90;x<=1240;x+=20){if(x>1140&&y>570)continue;if(await isEmpty(x,y))return{x,y};}return null;};
const deselect=async()=>{for(let i=0;i<3;i++){await p.keyboard.press('Escape');await p.waitForTimeout(320);}const e=await findEmpty();if(e){await p.mouse.click(e.x,e.y);await p.waitForTimeout(600);}};
const makeNode=async(k)=>{await deselect();const rb=await p.evaluate((nm)=>{const e=Array.from(document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button')).find(x=>(x.getAttribute('aria-label')||'').startsWith(nm));if(!e)return null;const r=e.getBoundingClientRect();return{cx:Math.round(r.x+r.width/2),cy:Math.round(r.y+r.height/2)};},k);
  if(!rb)return null;const pre=await nodeIds();await p.mouse.click(rb.cx,rb.cy);await p.waitForTimeout(3400);const m=(await nodeIds()).filter(x=>!pre.includes(x));return m.length===1?m[0]:null;};
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
  if(r.why)return{ok:false,...r};if(!r.landed)return{ok:false,why:'occluded'};await p.mouse.click(r.cx,r.cy);await p.waitForTimeout(1400);return{ok:true,aria:r.aria};};
const pops=()=>p.evaluate(()=>Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"],[role="menu"]')).filter(e=>{const r=e.getBoundingClientRect();return r.width>1&&r.height>1;})
  .map(e=>{const r=e.getBoundingClientRect();return{role:e.getAttribute('role'),box:`${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    scrollH:e.scrollHeight,clientH:e.clientHeight,scrollable:e.scrollHeight>e.clientHeight+1,html:(e.innerHTML||'').slice(0,300),
    text:(e.innerText||'').replace(/\s+/g,' ').trim().slice(0,300)};}));
const out={startedAt:new Date().toISOString()};
let MINE=null;
try{
  MINE=await makeNode('视频'); console.log('建节点:',MINE);
  if(!MINE) throw new Error('建节点失败'); out.nodeId=MINE;
  await p.waitForTimeout(1600);

  console.log('\n=== A. 模型列表项的 DOM 结构（找「名称」元素）===');
  console.log('开弹层:',JSON.stringify(await clickChip('选择模型')));
  const detail = await p.evaluate(() => {
    const pop = Array.from(document.querySelectorAll('[role="listbox"]')).filter(e=>e.getBoundingClientRect().width>1).pop();
    if(!pop) return null; const r=pop.getBoundingClientRect();
    const rows = Array.from(pop.children).map((row,i)=>{const q=row.getBoundingClientRect();
      return { i, tag:row.tagName, role:row.getAttribute('role'), dis:row.getAttribute('aria-disabled'), sel:row.getAttribute('aria-selected'),
        cls:String(row.className||'').slice(0,40), box:`${Math.round(q.width)}x${Math.round(q.height)}@${Math.round(q.x)},${Math.round(q.y)}`,
        inViewport: q.top>=0 && q.bottom<=innerHeight,
        leaves: Array.from(row.querySelectorAll('*')).filter(x=>x.getBoundingClientRect().width>1 && x.children.length===0)
          .map(x=>({tag:x.tagName, tid:x.getAttribute('data-testid'), cls:String(x.className||'').slice(0,34),
            box:(()=>{const z=x.getBoundingClientRect();return`${Math.round(z.width)}x${Math.round(z.height)}@${Math.round(z.x)},${Math.round(z.y)}`;})(),
            text:(x.innerText||'').replace(/\s+/g,' ').trim().slice(0,50)})) };});
    return { pop:{box:`${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, scrollH:pop.scrollHeight, clientH:pop.clientHeight, overflowY:getComputedStyle(pop).overflowY}, rows };
  });
  console.log('弹层:',JSON.stringify(detail && detail.pop));
  for (const row of (detail?detail.rows:[])) { console.log(`  #${row.i} ${row.box} 视口内=${row.inViewport} dis=${row.dis} sel=${row.sel}`);
    for (const l of row.leaves) console.log(`      leaf ${l.tag} ${l.cls} ${l.box} «${l.text}»`); }
  out.modelDetail = detail;
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);

  console.log('\n=== B. 时长弹层的完整结构 ===');
  console.log('开弹层:',JSON.stringify(await clickChip('选择视频生成时长')));
  const dur = await p.evaluate(() => {
    const pop = Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"]')).filter(e=>e.getBoundingClientRect().width>1).pop();
    if(!pop) return null; const r=pop.getBoundingClientRect();
    return { role:pop.getAttribute('role'), box:`${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      html:(pop.innerHTML||'').slice(0,1400),
      leaves: Array.from(pop.querySelectorAll('*')).filter(x=>x.getBoundingClientRect().width>1 && x.children.length===0)
        .map(x=>{const q=x.getBoundingClientRect();return{tag:x.tagName,cls:String(x.className||'').slice(0,40),tid:x.getAttribute('data-testid'),
          box:`${Math.round(q.width)}x${Math.round(q.height)}@${Math.round(q.x)},${Math.round(q.y)}`,text:(x.innerText||'').replace(/\s+/g,' ').trim().slice(0,30)};}) };
  });
  console.log('时长弹层:',JSON.stringify(dur,null,1).slice(0,2600));
  out.durationDetail = dur;
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);

  console.log('\n=== C. 比例 / 分辨率的入口在哪（找全表单内所有可点元素）===');
  const allCtl = await p.evaluate((F)=>{const f=document.querySelector(F);if(!f)return null;
    return Array.from(f.querySelectorAll('button,[role="button"],[aria-label],[data-testid]')).map(e=>{const r=e.getBoundingClientRect();
      return{tag:e.tagName,tid:e.getAttribute('data-testid'),role:e.getAttribute('role'),aria:e.getAttribute('aria-label'),
        box:`${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
        text:(e.innerText||'').replace(/\s+/g,' ').trim().slice(0,36)};}).filter(x=>x.box&&!x.box.startsWith('0x0'));},FORM);
  for (const c of allCtl) console.log('  ',JSON.stringify(c));
  out.allControls = allCtl;
} catch(e){ console.error('ABORT:',e.message); out.error=e.message; }
finally{
  if(MINE) console.log('\n删',MINE,'->',await deleteById(MINE));
  for(let i=0;i<3;i++){await p.keyboard.press('Escape');await p.waitForTimeout(300);}
  await restoreZoom();
  for(let i=0;i<3;i++){await p.keyboard.press('Escape');await p.waitForTimeout(300);}
  const fin=await p.evaluate(()=>Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map(e=>{const m=/translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform||'');return[e.getAttribute('data-id'),m?[Math.round(parseFloat(m[1])*100)/100,Math.round(parseFloat(m[2])*100)/100]:null];})));
  let dev=0;for(const[id,b2]of Object.entries(BASE.nodes)){const c=fin[id];const d=c&&b2.canvas?[Math.round((c[0]-b2.canvas[0])*100)/100,Math.round((c[1]-b2.canvas[1])*100)/100]:'MISSING';
    if(d==='MISSING'||(Array.isArray(d)&&(Math.abs(d[0])>0.01||Math.abs(d[1])>0.01)))dev++;}
  console.log('终态:',await statusLine(),'| 缩放',await zoomOf(),'| 积分',await credit(),'| 节点',Object.keys(fin).length,'| 偏离',dev);
  out.end={status:await statusLine(),credit:await credit(),dev};
  writeFileSync(OUT,JSON.stringify(out,null,1)); console.log('写入',OUT.pathname);
  await b.close();
}
