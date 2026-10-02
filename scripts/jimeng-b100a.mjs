// 批次 100 · a 轮：`help-and-shortcuts.md`（普查 82，353 行）—— 快捷键总账的**第三次机械对账**。
//
// 🔑 **主靶点是一个分类缺口**：本页把快捷键分成三块 ——「面板逐字全表」/「确认可用」/
//    「声明了但当前不可用」。但 `V`（移动工具）**两栏都没有** ——
//    它既不在「确认可用」，也不在「声明了但当前不可用」⇒ **读者会默认它能用**。
//    而批次 96 已**第三次独立确认**「V 键不切工具」（连按三次，toggle 的 aria 恒为
//    `选择工具`），批次 82 首测也记过同样结论。
//    ⇒ 缺的是**第三类：「面板声明了，但按了没有任何反应」** —— 与「给了提示」不同
//      （本页第 139/144 行已强调过 G 在未选中时**连提示都不给**，那个坑和这个是同一族）。
//
// 第二件事：**面板全表第三次对账**。批次 82 抓过一次（62 行 / 28 项，与四张表逐字一致），
//    本轮重抓，验证是否漂移，并把对账**固化成可重跑的断言**（批次 90 的做法）。
//
// 🔴 纪律：只打开「用户菜单 → 快捷键」这个**只读面板**；按 `V` 前后都过 `keyGuard`
//    （画布上若有主体节点被选中，V 会直接改它的标题，见 subject-node.md）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };

const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const nodeN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]');
  return e ? e.getAttribute('aria-label') : null; });
const zoomLabel = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return e ? e.getAttribute('aria-label') : null; });
const toolAria = () => p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return t ? { aria: t.getAttribute('aria-label'), pressed: t.getAttribute('aria-pressed') } : null; });
const setZoom = async (t) => { for (let k = 1; k <= 4; k++) {
  const zl = await zoomLabel(); if (zl && new RegExp(`, ${t}%`).test(zl)) return true;
  await p.click('[data-testid="canvas-zoom-percent"]'); await p.waitForTimeout(1000);
  if (await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) {
    await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
      i.dispatchEvent(new Event('input', { bubbles: true }));
      i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t);
    await p.waitForTimeout(1700);
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
  return false; };

out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), tool: await toolAria() };
log('起点：', JSON.stringify(out.start));
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
if ((await toolAria())?.aria !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }

// ---- P1：打开用户菜单 → 快捷键面板（只读）----
const menuOpened = await p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-user-menu-trigger"]');
  if (!t) return false; t.click(); return true; });
await p.waitForTimeout(1400);
out.userMenu = await p.evaluate(() => {
  const items = Array.from(document.querySelectorAll('[role="menuitem"],[role="menu"] *'))
    .map((e) => ({ tag: e.tagName, role: e.getAttribute('role'), text: e.innerText.replace(/\s+/g, ' ').trim().slice(0, 24),
      aria: e.getAttribute('aria-label') })).filter((x) => x.text);
  return { items: items.slice(0, 12) }; });
log('P1 用户菜单项：', JSON.stringify(out.userMenu.items.map((x) => x.text)));

const clicked = await p.evaluate(() => {
  const el = Array.from(document.querySelectorAll('[role="menuitem"],button,div,li'))
    .find((e) => e.innerText && e.innerText.replace(/\s+/g, ' ').trim() === '快捷键'
      && e.getBoundingClientRect().width > 0);
  if (!el) return false; el.click(); return true; });
out.clickedShortcut = clicked;
log('点「快捷键」：', clicked);
await p.waitForTimeout(1800);

out.panel = await p.evaluate(() => {
  const scroll = document.querySelector('[data-testid="shortcut-help-scroll-region"]');
  const drawer = scroll ? scroll.closest('[role="dialog"],aside,div[class*="drawer"],[class*="shortcut"]') : null;
  const r = (e) => { if (!e) return null; const b = e.getBoundingClientRect();
    return `${Math.round(b.width)}×${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}`; };
  if (!scroll) return { present: false };
  return { present: true, scrollScreen: r(scroll), drawerScreen: r(drawer),
    scrollHeight: scroll.scrollHeight, clientHeight: scroll.clientHeight,
    // 逐行导出：面板里的每一行文本
    rows: Array.from(scroll.querySelectorAll('*'))
      .filter((e) => e.children.length === 0 && (e.innerText || '').trim())
      .map((e) => ({ tag: e.tagName, text: e.innerText.replace(/\s+/g, ' ').trim() })) };
});
log('P2 面板：', out.panel.present ? `${out.panel.scrollScreen} 可滚动 ${out.panel.scrollHeight}/可见 ${out.panel.clientHeight}` : '未出现');
out.rows = out.panel.rows ?? [];
log(`   导出 ${out.rows.length} 行：`);
out.rows.forEach((r, i) => log(`     ${String(i + 1).padStart(2)}. [${r.tag}] ${r.text}`));

await p.keyboard.press('Escape');
await p.waitForTimeout(1000);
out.panelClosed = await p.evaluate(() => document.querySelectorAll('[data-testid="shortcut-help-scroll-region"]').length);
log('Esc 后面板数：', out.panelClosed);

// ---- P3：V 键实测（三次，前后过 keyGuard；判据不只是 toggle 的 aria）----
out.vTest = { steps: [] };
for (let k = 1; k <= 3; k++) {
  const g = await keyGuard(p);
  const before = await p.evaluate(() => ({
    tool: (() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
      return { aria: t ? t.getAttribute('aria-label') : null, pressed: t ? t.getAttribute('aria-pressed') : null }; })(),
    sel: document.body.innerText.match(/(\d+) selected/)?.[1] ?? '0',
    nodes: document.body.innerText.match(/(\d+) nodes?/)?.[1] ?? '0',
    // 「有没有出现任何浮层/提示」——这是本轮新增的判据，用来区分「无效」与「有反馈但无效」
    overlays: document.querySelectorAll('[role="alert"],[role="status"],[role="tooltip"],[class*="toast"],[class*="shortcut"],[class*="unavailable"]').length,
    menuItems: document.querySelectorAll('[role="menuitem"]').length,
    activeTag: (() => { const a = document.activeElement; return a ? a.tagName : null; })() }));
  if (!g.safe) { out.vTest.steps.push({ k, refused: true, g }); log(`V 第 ${k} 次：keyGuard 拒绝`); break; }
  await p.keyboard.press('v');
  await p.waitForTimeout(1200);
  const after = await p.evaluate(() => ({
    tool: (() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
      return { aria: t ? t.getAttribute('aria-label') : null, pressed: t ? t.getAttribute('aria-pressed') : null }; })(),
    sel: document.body.innerText.match(/(\d+) selected/)?.[1] ?? '0',
    nodes: document.body.innerText.match(/(\d+) nodes?/)?.[1] ?? '0',
    overlays: document.querySelectorAll('[role="alert"],[role="status"],[role="tooltip"],[class*="toast"],[class*="shortcut"],[class*="unavailable"]').length,
    menuItems: document.querySelectorAll('[role="menuitem"]').length,
    activeTag: (() => { const a = document.activeElement; return a ? a.tagName : null; })() }));
  const changed = JSON.stringify(before) !== JSON.stringify(after);
  out.vTest.steps.push({ k, before, after, changed });
  log(`V 第 ${k} 次：${changed ? '🔴 有变化' : '无变化'}｜工具 ${before.tool.aria} → ${after.tool.aria}｜` +
      `sel ${before.sel}→${after.sel}｜nodes ${before.nodes}→${after.nodes}｜` +
      `浮层 ${before.overlays}→${after.overlays}｜菜单项 ${before.menuItems}→${after.menuItems}`);
}
out.vAnyChange = out.vTest.steps.some((s) => s.changed);

// ---- P4：对账（本页四张表 vs 面板导出）----
out.manual = {
  通用操作: [['打开/关闭 Agent', '⌘ /'], ['撤销', '⌘ Z'], ['还原', '⌘ ⇧ Z / ⌘ Y'],
    ['移动工具', 'V'], ['预览视图', 'F'], ['宫格视图', 'G'], ['创建编组', '⌘ G'], ['取消编组', '⌘ ⇧ G']],
  视图: [['放大视图', '⌘ +'], ['缩小视图', '⌘ −'], ['适配画布', '⇧ 1 / ⌘ 0'],
    ['缩放至 100%', '⌘ 1'], ['缩放至选中项', '⇧ 2'], ['缩放画布', '⌘ scroll']],
};
const panelText = out.rows.map((r) => r.text).join(' ｜ ');
out.reconcile = {};
for (const [grp, items] of Object.entries(out.manual)) {
  out.reconcile[grp] = items.map(([name, key]) => {
    const nameHit = panelText.includes(name);
    const keyHit = key.split(/[/或]/).map((s) => s.trim()).some((s) => s && panelText.includes(s));
    return { name, key, nameHit, keyHit };
  });
}
log('P4 对账：');
for (const [g2, items] of Object.entries(out.reconcile)) {
  log(`   ${g2}：`);
  items.forEach((i) => log(`     ${i.nameHit ? '✔' : '✘'} 名称「${i.name}」 ｜${i.keyHit ? '✔' : '✘'} 键「${i.key}」`));
}

out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), tool: await toolAria() };
log('终态：', JSON.stringify(out.end), '（本轮只读，未改任何状态）');
writeFileSync(new URL('./_tmp-b100a.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
