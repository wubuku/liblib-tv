// 批次 122 · b 轮：打开顶栏「更多」菜单，看 `canvas-editor-menu` 这个 testid
// **在菜单打开后会不会变成 2 个**（这正是「testid 相同不等于同一个东西」那类坑的温床）。
//
// 🔴 a 轮已经把手册内部矛盾解开了一半：
//   · `canvas-editor-menu` = `<DIV>` `36×36@1061,12`、**`display:flex`、只有一个孩子**
//   · 那个孩子 = `<BUTTON aria="更多" data-testid="null">` `28×28@1065,16`
//   ⇒ **「更多」按钮本身确实没有 testid**（`canvas-context.md:49,53` 是对的）
//   ⇒ 但它**有一个 36×36 的壳叫 `canvas-editor-menu`**
//     （`use-node-toolbar.md:515`「`canvas-editor-menu` … ⇒ **顶栏按钮**」把这层壳当成了按钮）
//
// 📌 另一个 a 轮顺带读到的结构事实：壳的父级是一个 `DIV.contents`（`display:contents`、
//   矩形 `0×0`）—— 这就是为什么 `canvas-top-bar-actions` 的 `children.length` 只有 **4**，
//   而它视觉上装着 6 个东西。
//
// ⛔ 本轮只「打开菜单并读它」，**不点任何菜单项**（项目信息/复制项目都未授权执行）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b' };
const save = () => writeFileSync(new URL('./_tmp-b122b.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);

const census = () => p.evaluate(() => {
  const r = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const em = Array.from(document.querySelectorAll('[data-testid="canvas-editor-menu"]'));
  const menus = Array.from(document.querySelectorAll('[role=menu],[role=dialog],[data-radix-menu-content],[data-radix-popper-content-wrapper]'))
    .filter((m) => { const q = m.getBoundingClientRect(); return q.width > 1 && getComputedStyle(m).visibility !== 'hidden'; });
  const btn = Array.from(document.querySelectorAll('button')).find((e) => (e.getAttribute('aria-label') || '') === '更多');
  return {
    canvasEditorMenu数: em.length,
    canvasEditorMenu: em.map((e) => ({ 矩形: r(e), 子元素数: e.children.length, 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
      后代testid: Array.from(e.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')),
      后代aria: Array.from(e.querySelectorAll('[aria-label]')).map((x) => x.getAttribute('aria-label')).filter(Boolean),
      内含menuitem: e.querySelectorAll('[role=menuitem]').length,
      祖先: (() => { let c = e.parentElement; const a = []; for (let k = 0; k < 4 && c; k++) { a.push(c.tagName + ' tid=' + c.getAttribute('data-testid') + ' disp=' + getComputedStyle(c).display); c = c.parentElement; } return a; })() })),
    浮层: menus.map((m) => ({ tag: m.tagName, tid: m.getAttribute('data-testid'), role: m.getAttribute('role'), 矩形: r(m),
      cls: (m.getAttribute('class') || '').toString().slice(0, 70),
      文字: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60),
      menuitem: Array.from(m.querySelectorAll('[role=menuitem]')).map((it) => ({ 逐字: (it.innerText || '').replace(/\s+/g, ' ').trim(), 矩形: r(it),
        禁用: it.getAttribute('aria-disabled') === 'true' || it.hasAttribute('disabled') })) })),
    更多按钮: btn ? { 矩形: r(btn), tid: btn.getAttribute('data-testid'), ariaExpanded: btn.getAttribute('aria-expanded'),
      ariaHaspopup: btn.getAttribute('aria-haspopup'), dataState: btn.getAttribute('data-state'),
      祖先链: (() => { const a = []; let c = btn; for (let k = 0; k < 5 && c; k++) { a.push({ tag: c.tagName, tid: c.getAttribute('data-testid'), disp: getComputedStyle(c).display, 矩形: r(c) }); c = c.parentElement; } return a; })() } : null,
  };
});

out.before = await census();
log('=== 菜单打开前 ===');
log('  canvas-editor-menu 数：', out.before.canvasEditorMenu数, '｜浮层数：', out.before.浮层.length);
log('  更多按钮：', JSON.stringify({ 矩形: out.before.更多按钮?.矩形, ariaExpanded: out.before.更多按钮?.ariaExpanded, ariaHaspopup: out.before.更多按钮?.ariaHaspopup, dataState: out.before.更多按钮?.dataState }));
log('  按钮祖先链：', JSON.stringify(out.before.更多按钮?.祖先链));
save();

// ---- 真实鼠标点击打开（落点现算 + elementFromPoint 自检必须命中那个 BUTTON 自己） ----
const pt = await p.evaluate(() => {
  const btn = Array.from(document.querySelectorAll('button')).find((e) => (e.getAttribute('aria-label') || '') === '更多');
  if (!btn) return { __err: 'no-btn' };
  const r = btn.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2)
    for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
      const e = document.elementFromPoint(x, y); if (e && (e === btn || btn.contains(e))) return { x, y, 矩形: [r.x, r.y, r.width, r.height].map(Math.round) }; }
  return { __err: 'no-point' };
});
log('\n「更多」落点自检：', JSON.stringify(pt));
out.point = pt;
if (pt.__err) { log('⛔ 中止'); save(); await b.close(); process.exit(3); }
await p.mouse.click(pt.x, pt.y);
await p.waitForTimeout(1500);

out.after = await census();
log('\n=== 菜单打开后 ===');
log('  canvas-editor-menu 数：', out.after.canvasEditorMenu数, '｜浮层数：', out.after.浮层.length);
out.after.canvasEditorMenu.forEach((e, i) => log(`   canvas-editor-menu[${i}] ${JSON.stringify(e.矩形)} 子=${e.子元素数} menuitem=${e.内含menuitem} 文字=${JSON.stringify(e.文字)}\n      后代testid=${JSON.stringify(e.后代testid)} 后代aria=${JSON.stringify(e.后代aria)}\n      祖先=${JSON.stringify(e.祖先)}`));
out.after.浮层.forEach((m, i) => log(`   浮层[${i}] <${m.tag}> tid=${JSON.stringify(m.tid)} role=${m.role} ${JSON.stringify(m.矩形)}\n      cls=${JSON.stringify(m.cls)}\n      文字=${JSON.stringify(m.文字)}\n      menuitem=${JSON.stringify(m.menuitem)}`));
log('  更多按钮 aria-expanded：', out.after.更多按钮?.ariaExpanded, '｜data-state：', out.after.更多按钮?.dataState);
save();

// ---- 关掉（Esc），并确认回到关闭态 ----
await p.keyboard.press('Escape');
await p.waitForTimeout(1200);
out.closed = await census();
log('\n=== Esc 关闭后 ===');
log('  canvas-editor-menu 数：', out.closed.canvasEditorMenu数, '｜浮层数：', out.closed.浮层.length, '｜aria-expanded：', out.closed.更多按钮?.ariaExpanded);
out.恢复校验 = { 浮层清空: out.closed.浮层.length === 0, testid回到1个: out.closed.canvasEditorMenu数 === 1, zoom: await zoom(), status: await status() };
log('  恢复校验：', JSON.stringify(out.恢复校验));
save();
log('\nDONE b');
process.exit(0);
