// 批次 96 · b 轮：缩放菜单的**真实 testid 与几何**（只读）。
//
// a 轮拿到三件事，其中一件直接推翻了本页第 82 行：
//   ① 缩放按钮是 **纯 `<button type="button" data-testid="canvas-zoom-percent">`**，
//      `48×28@124,672`，`innerText = "60%"`，**内部 0 个 input、0 个子元素、不是 contenteditable**
//      ⇒ 「缩放按钮**本身**是一个输入框」不成立。
//   ② 弹层打开后，`aria="Set zoom percentage"` 的 `input[data-testid="canvas-zoom-percent-input"]`
//      出现，**`48×28@124,672` —— 与按钮逐字同位置同尺寸**（所以肉眼看是「按钮变成了输入框」），
//      但它是**另一个元素**，且 `min`/`max`/`step` **全是 null**（没有 HTML 约束，
//      页面说的 8%–800% 钳制是 JS 做的，不是输入框属性）。
//      弹层关闭时全页只有 2 个 `type=file` 的 input，这个 input **0 个**。
//   ③ 🔴 a 轮读 `[data-testid="canvas-context-menu"]` 得 **null**，而
//      `[data-testid="canvas-zoom-menu"]` **存在** ⇒ **缩放菜单不是右键菜单那个容器**。
//      本页第 59 行只说「`role="menu"`，实测 200×292」，没说 testid —— 于是后人会用错 selector。
//
// 本轮把缩放菜单的容器几何、条目逐字、以及「弹层打开后按钮本身还在不在」一次读全。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };

const zoomLabel = () => p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]');
  return e ? e.getAttribute('aria-label') : null; });
const scaleNow = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport');
  const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; });

out.start = { zoom: await zoomLabel(), scale: await scaleNow() };
log('起点：', JSON.stringify(out.start));

// 打开前的按钮快照
out.before = await p.evaluate(() => {
  const btn = document.querySelector('[data-testid="canvas-zoom-percent"]');
  const r = btn.getBoundingClientRect();
  return { present: !!btn, aria: btn.getAttribute('aria-label'), innerText: btn.innerText.trim(),
    screen: { w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y) },
    stackAtCenter: (() => { const e = document.elementFromPoint(Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2));
      return e ? { tag: e.tagName, tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label') } : null; })() };
});
log('打开前：', JSON.stringify(out.before));

await p.click('[data-testid="canvas-zoom-percent"]');
await p.waitForTimeout(1300);

out.after = await p.evaluate(() => {
  const btn = document.querySelector('[data-testid="canvas-zoom-percent"]');
  const inp = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
  const menu = document.querySelector('[data-testid="canvas-zoom-menu"]');
  const ctx = document.querySelector('[data-testid="canvas-context-menu"]');
  const g = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
    return { w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y) }; };
  const menuItems = menu ? Array.from(menu.querySelectorAll('[role="menuitem"]')) : [];
  // 逐条列出**所有** role 组合，确认到底有没有 menuitem
  const roles = menu ? Array.from(new Set(Array.from(menu.querySelectorAll('[role]')).map((e) => e.getAttribute('role')))) : [];
  return {
    btnStillPresent: !!btn, btnAria: btn ? btn.getAttribute('aria-label') : null,
    btnGeo: g(btn), btnInnerText: btn ? btn.innerText.trim() : null,
    inpPresent: !!inp, inpGeo: g(inp), inpValue: inp ? inp.value : null,
    inpAria: inp ? inp.getAttribute('aria-label') : null,
    inpAttrs: inp ? { min: inp.min, max: inp.max, step: inp.step, type: inp.type, readOnly: inp.readOnly } : null,
    menuPresent: !!menu, menuRole: menu ? menu.getAttribute('role') : null, menuGeo: g(menu),
    ctxMenuPresent: !!ctx, roles,
    items: menuItems.map((x) => { const b2 = x.getBoundingClientRect();
      return { text: x.innerText.replace(/\s+/g, ' ').trim(), w: Math.round(b2.width), h: Math.round(b2.height),
        x: Math.round(b2.x), y: Math.round(b2.y), disabled: x.getAttribute('aria-disabled'),
        aria: x.getAttribute('aria-label') }; }),
    // 菜单容器里还有没有非 menuitem 的可见子元素
    menuInner: menu ? Array.from(menu.children).map((c) => { const r = c.getBoundingClientRect();
      return { tag: c.tagName, role: c.getAttribute('role'), testid: c.getAttribute('data-testid'),
        w: Math.round(r.width), h: Math.round(r.height), text: c.innerText.replace(/\s+/g, ' ').trim().slice(0, 30) }; }) : null,
    // 打开态下最上层是谁
    topAtMenu: (() => { if (!menu) return null; const r = menu.getBoundingClientRect();
      const e = document.elementFromPoint(Math.round(r.x + r.width / 2), Math.round(r.y + 10));
      return e ? { tag: e.tagName, tid: e.getAttribute('data-testid'), role: e.getAttribute('role') } : null; })(),
  };
});
log('打开后：');
log('   按钮仍在？', out.after.btnStillPresent, '| aria =', out.after.btnAria, '| innerText =', JSON.stringify(out.after.btnInnerText));
log('   按钮几何', JSON.stringify(out.after.btnGeo), '| input 几何', JSON.stringify(out.after.inpGeo), '| input value =', out.after.inpValue);
log('   input 属性', JSON.stringify(out.after.inpAttrs));
log('   canvas-zoom-menu：present=%s role=%s geo=%s', out.after.menuPresent, out.after.menuRole, JSON.stringify(out.after.menuGeo));
log('   canvas-context-menu 是否同时存在：', out.after.ctxMenuPresent);
log('   菜单内 role 集合：', JSON.stringify(out.after.roles));
log('   条目：');
(out.after.items || []).forEach((i, n) => log(`     ${n + 1}. ${i.text}  ${i.w}×${i.h}@${i.x},${i.y} disabled=${i.disabled}`));
log('   菜单直接子元素：', JSON.stringify(out.after.menuInner));

// 焦点归属：打开后焦点落在哪？
out.focus = await p.evaluate(() => {
  const a = document.activeElement;
  return { tag: a ? a.tagName : null, tid: a ? a.getAttribute('data-testid') : null,
    aria: a ? a.getAttribute('aria-label') : null, tag2: a ? a.getAttribute('tagName') : null };
});
log('打开后焦点：', JSON.stringify(out.focus));

// 关闭（Esc），确认状态复原
await p.keyboard.press('Escape');
await p.waitForTimeout(900);
out.closed = await p.evaluate(() => ({
  menu: document.querySelectorAll('[data-testid="canvas-zoom-menu"]').length,
  inp: document.querySelectorAll('input[data-testid="canvas-zoom-percent-input"]').length,
  ctx: document.querySelectorAll('[data-testid="canvas-context-menu"]').length }));
log('Esc 后：', JSON.stringify(out.closed), '| zoom =', await zoomLabel(), '| scale =', await scaleNow());

writeFileSync(new URL('./_tmp-b96b.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
