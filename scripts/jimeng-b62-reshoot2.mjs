// 上一张 `@` 截图里 composer 是 `@@`（脚本没清空就按了 @）⇒ 重拍一张干净的。
// 顺带把「添加参考」菜单的**结构**读准：它是 **1 个标题 + 5 个选项**，
// 上一轮我按 innerText 行数数成了 6 项 —— 把标题当成了选项。
import { chromium } from 'playwright';
import { pinViewport } from './jimeng-safe-keys.mjs';
const SHOTS = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const ed = () => p.evaluate(() => { const c=document.querySelector('.tiptap.ProseMirror[contenteditable="true"]');
  return c ? { text:(c.innerText||''), html:(c.innerHTML||'').slice(0,160) } : null; });
const clear = async () => { await p.evaluate(()=>{const c=document.querySelector('.tiptap.ProseMirror[contenteditable="true"]');if(!c)return;
  c.focus(); document.execCommand('selectAll',false,null); document.execCommand('delete',false,null);
  if((c.innerText||'').trim()){c.innerHTML='';c.dispatchEvent(new InputEvent('input',{bubbles:true,data:'',inputType:'deleteContentBackward'}));}});
  await p.waitForTimeout(450); return ed(); };
const st = () => p.evaluate(()=>{const e=document.querySelector('[data-testid="canvas-feature-sidecar"]');
  if(!e||e.getBoundingClientRect().width<1)return null; return e.querySelector('[data-testid="canvas-agent-panel"]')?'EXPANDED':'COLLAPSED';});
const focus = async () => { const c=await p.evaluate(()=>{const e=document.querySelector('.tiptap.ProseMirror[contenteditable="true"]');if(!e)return null;const r=e.getBoundingClientRect();return{cx:Math.round(r.x+24),cy:Math.round(r.y+24)};});
  if(!c)return false; await p.mouse.click(c.cx,c.cy); await p.waitForTimeout(450);
  return p.evaluate(()=>!!(document.activeElement&&document.activeElement.closest('.tiptap.ProseMirror'))); };
console.log('开场 editor:', JSON.stringify(await ed()));
console.log('清空后:', JSON.stringify(await clear()));
if (await st() !== 'EXPANDED') { const rb=await p.evaluate(()=>{const e=Array.from(document.querySelectorAll('button')).find(x=>/与\s*AI\s*对话/.test(x.getAttribute('aria-label')||''));if(!e)return null;const r=e.getBoundingClientRect();return{cx:Math.round(r.x+r.width/2),cy:Math.round(r.y+r.height/2)};});
  if(rb){await p.mouse.click(rb.cx,rb.cy);await p.waitForTimeout(1600);} }
console.log('侧栏 =', await st(), '| 聚焦 =', await focus());
await p.keyboard.press('@');
await p.waitForTimeout(1400);
const menu = await p.evaluate(() => { const e=document.querySelector('[role="listbox"]'); if(!e)return null; const r=e.getBoundingClientRect();
  const opts = Array.from(e.querySelectorAll('[role="option"]'));
  return { box:`${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    heading: (()=>{const h=Array.from(e.querySelectorAll('*')).find(x=>x.children.length===0&&/^添加参考$/.test((x.innerText||'').trim()));if(!h)return null;const b=h.getBoundingClientRect();return{text:'添加参考',box:`${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}`,cls:String(h.className||'').slice(0,40)};})(),
    optionCount: opts.length,
    options: opts.map(x=>{const b=x.getBoundingClientRect();return{aria:x.getAttribute('aria-label'),sel:x.getAttribute('aria-selected'),box:`${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}`,text:(x.innerText||'').replace(/\s+/g,' ').trim().slice(0,20)};}),
    leafRows: Array.from(e.querySelectorAll('*')).filter(x=>{const b=x.getBoundingClientRect();return b.width>1&&b.height>=30&&b.height<60&&x.children.length<=2;}).map(x=>{const b=x.getBoundingClientRect();return`${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)} «${(x.innerText||'').replace(/\s+/g,' ').trim().slice(0,16)}»`;}).slice(0,10),
    editorText: (document.querySelector('.tiptap.ProseMirror[contenteditable="true"]')||{}).innerText }; });
console.log('菜单结构:', JSON.stringify(menu,null,1));
await p.screenshot({ path: new URL('62-agent-at-menu.png', SHOTS).pathname, clip: { x: 700, y: 180, width: 580, height: 460 } });
console.log('📷 62-agent-at-menu.png');
await p.keyboard.press('Escape'); await p.waitForTimeout(900);
const fin = await clear();
console.log('收尾 editor:', JSON.stringify(fin), (fin&&fin.text&&fin.text.trim())?'<< 残留 ✗':'<< 已清空 ✓');
await p.evaluate(()=>{const c=document.querySelector('.tiptap.ProseMirror[contenteditable="true"]');if(c)c.blur();});
await p.waitForTimeout(300);
console.log('终态:', (await p.evaluate(()=>(document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/)||['?'])[0])),
  '| 积分', await p.evaluate(()=>{const m=document.body.innerText.match(/(\d[\d,]*)\s*基础会员/);return m?m[1]:null;}),
  '| 侧栏', await st(), '| 缩放', await p.evaluate(()=>(document.querySelector('button[aria-label^="Zoom options"]')||{}).getAttribute?.('aria-label')));
await b.close();
