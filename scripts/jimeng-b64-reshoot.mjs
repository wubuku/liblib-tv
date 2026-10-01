// 上一张裁切写死在 {x:250,y:400}，节点其实落在 clip 的**上沿**，拍到的是节点下边缘 + 大片空画布。
// 改成**按节点实际 rect 计算 clip**；顺带把「选中后 node-toolbar 读数 0×0」这件事重测一次
// （0×0 可能是时序问题，也可能是判据选错 —— 先测再说）。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const SHOTS = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const FILE = '/tmp/b22-upload.png';
const OUT = new URL('./_tmp-b64-reshoot.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const credit=()=>p.evaluate(()=>{const m=document.body.innerText.match(/(\d[\d,]*)\s*基础会员/);return m?parseInt(m[1].replace(/,/g,''),10):null;});
const statusLine=()=>p.evaluate(()=>(document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/)||['?'])[0]);
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
const clipAround = (id, pad = 90) => p.evaluate(([vid,pd])=>{const n=document.querySelector(`.react-flow__node[data-id="${vid}"]`);if(!n)return null;
  const r=n.getBoundingClientRect();const x=Math.max(0,Math.round(r.x-pd)),y=Math.max(0,Math.round(r.y-pd));
  return{x,y,width:Math.min(1280-x,Math.round(r.width+pd*2)),height:Math.min(720-y,Math.round(r.height+pd*2)),node:`${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)}`};},[id,pad]);
const out={startedAt:new Date().toISOString()};
const MINE=[];
try{
  const pre=await nodeIds();
  const h=await p.$$('input[type=file]');
  await h[0].setInputFiles(FILE);
  console.log('已 setInputFiles，等待 6s 让缩略图换成远程图…');
  await p.waitForTimeout(6000);
  const ids=(await nodeIds()).filter(x=>!pre.includes(x));
  console.log('新增节点:',JSON.stringify(ids),'|',await statusLine());
  if(ids.length!==1) throw new Error('新增节点数不为 1');
  MINE.push(ids[0]);
  const rd=await p.evaluate((vid)=>{const e=document.querySelector(`.react-flow__node[data-id="${vid}"]`);const r=e.getBoundingClientRect();
    const vis=(x)=>{const q=x.getBoundingClientRect();return q.width>1&&q.height>1;};
    const t=Array.from(e.querySelectorAll('*')).find(x=>vis(x)&&/Rename /.test(x.getAttribute('aria-label')||''));
    return{cls:Array.from(e.classList).filter(c=>c.startsWith('react-flow__node-')).join(' '),aria:e.getAttribute('aria-label'),
      title:t?(t.getAttribute('aria-label')||'').replace(/^Rename /,''):null,box:`${Math.round(r.width)}x${Math.round(r.height)}`,
      imgs:Array.from(e.querySelectorAll('img')).filter(vis).map(x=>`${x.naturalWidth}x${x.naturalHeight} ${(x.getAttribute('src')||'').slice(0,44)}`)};},ids[0]);
  console.log('节点读数:',JSON.stringify(rd,null,1));

  // 1) 未选中态配图
  await deselect(); await p.waitForTimeout(700);
  let clip=await clipAround(ids[0]);
  await p.screenshot({path:new URL('64-upload-node-idle.png',SHOTS).pathname,clip:{x:clip.x,y:clip.y,width:clip.width,height:clip.height}});
  console.log('📷 64-upload-node-idle.png', JSON.stringify(clip));

  // 2) 选中态：工具条读数**密集采样**（上一轮 0×0 疑为时序）
  console.log('\n=== 选中后 node-toolbar 密集采样 ===');
  const ok=await selectMine(ids[0]);
  console.log('选中成功 =', ok, '|', await statusLine());
  const ser=[];
  for(const t of [500,1200,2000,3000,4500]){
    if(t===500)await p.waitForTimeout(500);else await p.waitForTimeout(t-[500,1200,2000,3000,4500][ser.length]);
    const tb=await p.evaluate(()=>{const els=Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'));
      return els.map(e=>{const r=e.getBoundingClientRect();return{box:`${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
        btns:Array.from(e.querySelectorAll('button,[role="button"]')).filter(x=>x.getBoundingClientRect().width>1)
          .map(x=>(x.getAttribute('aria-label')||(x.innerText||'').trim().slice(0,10)))};});});
    ser.push({t,tb});
    console.log(`  t=${t}ms toolbars=${JSON.stringify(tb)}`);
  }
  out.toolbarSeries=ser;
  const anyTb=ser.map(s=>s.tb).flat().find(x=>!x.box.startsWith('0x0'));
  clip=await clipAround(ids[0],140);
  await p.screenshot({path:new URL('64-upload-node-selected.png',SHOTS).pathname,clip:{x:clip.x,y:clip.y,width:clip.width,height:clip.height}});
  console.log('📷 64-upload-node-selected.png', JSON.stringify(clip));
  console.log('工具条是否出现过非 0×0:', anyTb? JSON.stringify(anyTb).slice(0,300) : '全程 0×0');
  out.toolbarFound=!!anyTb;
  console.log('积分:',await credit());
}catch(e){console.error('ABORT:',e.message);}
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
  out.end={status:await statusLine(),credit:await credit(),dev};
  writeFileSync(OUT,JSON.stringify(out,null,1));console.log('写入',OUT.pathname);
  await b.close();
}
