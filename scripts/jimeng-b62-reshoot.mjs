// 补拍：`@` 菜单向**左溢出到抽屉之外**（240×296@770,252，抽屉左沿是 868），
// 上一张的 clip 从 860 起 ⇒ 菜单左侧 90px 被切掉了，选项文字只剩一排 `›`。
// 这一张把 clip 左移到 740，把整条菜单收进来。
import { chromium } from 'playwright';
import { pinViewport } from './jimeng-safe-keys.mjs';
const SHOTS = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const sidecar = () => p.evaluate(() => { const e=document.querySelector('[data-testid="canvas-feature-sidecar"]');
  if(!e||e.getBoundingClientRect().width<1) return null; return !!e.querySelector('[data-testid="canvas-agent-panel"]') ? 'EXPANDED':'COLLAPSED'; });
const pops = () => p.evaluate(() => Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"],[role="menu"],[data-testid="agent-skill-menu"]'))
  .filter(e=>{const r=e.getBoundingClientRect();return r.width>1&&r.height>1;})
  .map(e=>{const r=e.getBoundingClientRect();return{tid:e.getAttribute('data-testid'),role:e.getAttribute('role'),
    box:`${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,text:(e.innerText||'').replace(/\s+/g,' ').trim()};}));
const openDrawer = async () => { if (await sidecar()==='EXPANDED') return 'already';
  const rb = await p.evaluate(()=>{const e=Array.from(document.querySelectorAll('button')).find(x=>/与\s*AI\s*对话/.test(x.getAttribute('aria-label')||''));if(!e)return null;const r=e.getBoundingClientRect();return{cx:Math.round(r.x+r.width/2),cy:Math.round(r.y+r.height/2)};});
  if(!rb)return 'nobtn'; await p.mouse.click(rb.cx,rb.cy); await p.waitForTimeout(1600); return 'ok'; };
const focusEditor = async () => { const c=await p.evaluate(()=>{const e=document.querySelector('.tiptap.ProseMirror[contenteditable="true"]');if(!e)return null;const r=e.getBoundingClientRect();return{cx:Math.round(r.x+24),cy:Math.round(r.y+24)};});
  if(!c)return false; await p.mouse.click(c.cx,c.cy); await p.waitForTimeout(450);
  return p.evaluate(()=>!!(document.activeElement&&document.activeElement.closest('.tiptap.ProseMirror'))); };
console.log('侧栏 =', await sidecar(), '| 打开:', await openDrawer(), '| 侧栏 =', await sidecar());
const items = await p.evaluate(() => { const e=document.querySelector('[role="listbox"]'); if(!e) return null;
  const r=e.getBoundingClientRect();
  return { box:`${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    items:Array.from(e.querySelectorAll('[role="option"],[role="menuitem"],li,div')).filter(x=>{const b=x.getBoundingClientRect();return b.width>1&&b.height>1&&b.height<60;})
      .map(x=>{const b=x.getBoundingClientRect();return{role:x.getAttribute('role'),aria:x.getAttribute('aria-label'),cls:String(x.className||'').slice(0,36),box:`${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}`,text:(x.innerText||'').replace(/\s+/g,' ').trim().slice(0,24)};}).slice(0,12)}; });
console.log('`@` listbox:', JSON.stringify(items,null,1));
console.log('聚焦 =', await focusEditor());
await p.keyboard.press('@');
await p.waitForTimeout(1400);
console.log('`@` 后浮层:', JSON.stringify(await pops()));
await p.screenshot({ path: new URL('62-agent-at-menu.png', SHOTS).pathname, clip: { x: 700, y: 180, width: 580, height: 460 } });
console.log('📷 62-agent-at-menu.png（clip 700,180 580×460，含左溢出部分）');
await p.keyboard.press('Escape'); await p.waitForTimeout(900);
console.log('关浮层:', JSON.stringify(await pops()));
await p.evaluate(()=>{const c=document.querySelector('.tiptap.ProseMirror[contenteditable="true"]');if(c)c.blur();});
await b.close();
