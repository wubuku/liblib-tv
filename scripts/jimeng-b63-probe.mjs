// 批次 63 探测二：建好节点后，**从价格那句文字反查**面板容器的 testid，
// 而不是照抄手册里的 form[data-testid=generation-form]。
// 上一轮照抄读到 null，但价格读得到（Current price 56.）—— 说明面板在，只是不是那个选择器。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g,''),10) : null; });
const statusLine = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/)||['?'])[0]);
const nodeIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map(e=>e.getAttribute('data-id')));
const reset = async () => { for (let i=0;i<3;i++){ await p.keyboard.press('Escape'); await p.waitForTimeout(320);} };
const isEmpty = (x,y) => p.evaluate(([x,y]) => { const el=document.elementFromPoint(x,y); if(!el) return true;
  if (el.closest('.react-flow__node')) return false;
  if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"],[data-testid="canvas-feature-sidecar"]')) return false;
  return true; },[x,y]);
const findEmpty = async () => { for (let y=110;y<=620;y+=20) for (let x=90;x<=1240;x+=20){ if(x>1140&&y>590)continue; if(await isEmpty(x,y)) return {x,y};} return null; };
const deselect = async () => { await reset(); const e=await findEmpty(); if(e){await p.mouse.click(e.x,e.y);await p.waitForTimeout(600);} return true; };
const makeNode = async (kind) => { await deselect();
  const rb = await p.evaluate((nm)=>{const e=Array.from(document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button')).find(x=>(x.getAttribute('aria-label')||'').startsWith(nm));if(!e)return null;const r=e.getBoundingClientRect();return{cx:Math.round(r.x+r.width/2),cy:Math.round(r.y+r.height/2)};},kind);
  if(!rb) return null; const pre=await nodeIds(); await p.mouse.click(rb.cx,rb.cy); await p.waitForTimeout(3400);
  const made=(await nodeIds()).filter(x=>!pre.includes(x)); return made.length===1?made[0]:null; };
const deleteById = async (id) => { await reset();
  const ok = await p.evaluate((vid)=>{const e=document.querySelector(`.react-flow__node[data-id="${vid}"]`);if(!e)return false;const r=e.getBoundingClientRect();
    for(let fy=0.12;fy<=0.9;fy+=0.08)for(let fx=0.12;fx<=0.9;fx+=0.08){const x=Math.round(r.x+r.width*fx),y=Math.round(r.y+r.height*fy);
      const t=document.elementFromPoint(x,y);if(!t||!t.closest(`.react-flow__node[data-id="${vid}"]`))continue;if(t.closest('button,a,[role="button"],input,textarea,select'))continue;
      e.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,clientX:x,clientY:y}));e.dispatchEvent(new MouseEvent('mouseup',{bubbles:true,clientX:x,clientY:y}));
      e.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:x,clientY:y}));return true;}return false;},id);
  await p.waitForTimeout(900);
  if (await p.evaluate((v)=>!!document.querySelector(`.react-flow__node[data-id="${v}"].selected`),id)) {
    await p.evaluate(()=>{const e=document.querySelector('.react-flow__node.selected');if(!e)return;const r=e.getBoundingClientRect();
      e.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,cancelable:true,clientX:Math.round(r.x+r.width/2),clientY:Math.round(r.y+14)}));});
    await p.waitForTimeout(800);
    await p.evaluate(()=>{const m=Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter(e=>e.getBoundingClientRect().width>1).pop();
      const it=m&&Array.from(m.querySelectorAll('[role="menuitem"]')).find(x=>/删除/.test(x.innerText||''));if(it)it.click();});
    await p.waitForTimeout(1300); }
  await reset();
  return (await p.evaluate((v)=>!document.querySelector(`.react-flow__node[data-id="${v}"]`),id))?'deleted':'STILL-THERE'; };
const desc = (e) => { const r=e.getBoundingClientRect();
  return { tag:e.tagName, tid:e.getAttribute('data-testid'), role:e.getAttribute('role'), aria:e.getAttribute('aria-label'),
    cls:String(e.className||'').slice(0,44), box:`${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    text:(e.innerText||'').replace(/\s+/g,' ').trim().slice(0,60) }; };
const out = { startedAt:new Date().toISOString() };
let MINE = null;
try {
  const id = await makeNode('视频');
  console.log('建临时视频节点:', id);
  if (!id) throw new Error('建节点失败');
  MINE = id; out.nodeId = id;
  await p.waitForTimeout(1500);
  const info = await p.evaluate(() => {
    const vis = (e) => { const r=e.getBoundingClientRect(); return r.width>1&&r.height>1; };
    // 找到含 "Current price" 的最小可见元素
    let hit = null;
    for (const e of document.querySelectorAll('*')) { if (!vis(e)) continue;
      if ((e.textContent||'').includes('Current price') && e.children.length === 0) { hit = e; break; } }
    const chain = []; let n = hit;
    while (n && n !== document.body) { chain.push(desc0(n)); if (chain.length > 14) break; n = n.parentElement; }
    function desc0(e){ const r=e.getBoundingClientRect();
      return { tag:e.tagName, tid:e.getAttribute('data-testid'), role:e.getAttribute('role'), aria:e.getAttribute('aria-label'),
        box:`${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
        text:(e.innerText||'').replace(/\s+/g,' ').trim().slice(0,70) }; }
    const forms = Array.from(document.querySelectorAll('form,[data-testid*="form"],[data-testid*="panel"],[data-testid*="generation"]'))
      .filter(vis).map(desc0);
    return { hit: hit ? desc0(hit) : null, chain, forms,
      allTids: Array.from(new Set(Array.from(document.querySelectorAll('[data-testid]')).map(e=>e.getAttribute('data-testid')))).filter(t=>/gen|panel|form|prompt|compos|toolbar/i.test(t)) };
  });
  console.log('\n价格元素:', JSON.stringify(info.hit));
  console.log('\n祖先链:');
  for (const c of info.chain) console.log('  ', JSON.stringify(c));
  console.log('\n可见 form/panel 类元素:');
  for (const f of info.forms) console.log('  ', JSON.stringify(f));
  console.log('\n相关 testid:', JSON.stringify(info.allTids));
  out.info = info;
} catch (e) { console.error('ABORT:', e.message); out.error = e.message; }
finally {
  if (MINE) console.log('\n删', MINE, '->', await deleteById(MINE));
  await reset();
  const fin = await p.evaluate(()=>Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map(e=>{const m=/translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform||'');return[e.getAttribute('data-id'),m?[Math.round(parseFloat(m[1])*100)/100,Math.round(parseFloat(m[2])*100)/100]:null];})));
  let dev=0; for (const [id,base] of Object.entries(BASE.nodes)) { const c=fin[id]; const d=c&&base.canvas?[Math.round((c[0]-base.canvas[0])*100)/100,Math.round((c[1]-base.canvas[1])*100)/100]:'MISSING';
    if(d==='MISSING'||(Array.isArray(d)&&(Math.abs(d[0])>0.01||Math.abs(d[1])>0.01))) dev++; }
  console.log('终态:', await statusLine(), '| 积分', await credit(), '| 节点', Object.keys(fin).length, '| 偏离', dev, '| 缩放', await p.evaluate(()=>(document.querySelector('button[aria-label^="Zoom options"]')||{}).getAttribute?.('aria-label')));
  out.end = { status: await statusLine(), credit: await credit(), dev, nodes: Object.keys(fin).length };
  writeFileSync(new URL('./_tmp-b63-probe.json', import.meta.url), JSON.stringify(out,null,1));
  await b.close();
}
