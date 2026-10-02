// 批次 106 · z2 轮：补上「抓手态下缩放菜单项能不能点」这一层。
//
// z 轮失败原因（判据，不是产品）：菜单项的 `innerText` 逐字是
//   **`放大视图` + 快捷键**（批次 105 读到的整段是「放大视图 | ⌘ + | 缩小视图 | ⌘ - |
//   适配画布 | ⇧ 1 | 缩放至选中项 | ⇧ 2 | 缩放至50% | 缩放至100% | ⌘ 1 | 缩放至200%」），
//   而我用**全等**去比 `'放大视图'` ⇒ **匹配不到**。
//   ⇒ **菜单项要按「归一化后逐字以标签开头」来定位，不是全等。**
//
// z 轮的归位是干净的：选择工具 / 小地图 off / 连线 on / 缩放 60% / 0 selected ✅
// 本轮起点即那个干净状态。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString() };
const DOCK = '[data-testid="canvas-navigation-dock"]';
const save = () => writeFileSync(new URL('./_tmp-b106z2.json', import.meta.url), JSON.stringify(out, null, 1));

const safeEval = async (fn, arg, tries = 8) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };
const state = () => safeEval((sel) => {
  const d = document.querySelector(sel);
  const g = (t) => { const e = d.querySelector(`[data-testid="${t}"]`); if (!e) return null;
    const q = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), pressed: e.getAttribute('aria-pressed'),
      x: Math.round(q.x), y: Math.round(q.y), w: Math.round(q.width), h: Math.round(q.height) }; };
  const inp = document.querySelector('[data-testid="canvas-zoom-percent-input"]');
  return { tool: g('canvas-pointer-tool-toggle'), mini: g('canvas-display-toggle-minimap'),
    conn: g('canvas-display-toggle-connections'), zoom: g('canvas-zoom-percent'),
    inputPresent: !!inp, inputValue: inp ? inp.value : null };
}, DOCK);
const clickBtn = async (btn, label) => { log(`  >>> 点「${label}」(${btn.x},${btn.y})`);
  await p.mouse.move(btn.x + btn.w / 2, btn.y + btn.h / 2); await p.waitForTimeout(450);
  await p.mouse.click(btn.x + btn.w / 2, btn.y + btn.h / 2); await p.waitForTimeout(1400); };

// 菜单项：归一化后**逐字以标签开头**，再取最小的那个盒子
const findItem = (label) => p.evaluate((lb) => {
  const cands = Array.from(document.querySelectorAll('button,[role=menuitem],[role=option],li,div,span'))
    .map((x) => ({ x, t: (x.innerText || '').replace(/\s+/g, ' ').trim(), q: x.getBoundingClientRect(), v: getComputedStyle(x).visibility }))
    .filter((y) => y.t.startsWith(lb) && y.q.width > 12 && y.q.height > 10 && y.v !== 'hidden')
    .sort((a, c) => a.q.width * a.q.height - c.q.width * c.q.height);
  if (!cands.length) return { found: false, sample: Array.from(document.querySelectorAll('body *')).slice(0, 0) };
  const e = cands[0];
  return { found: true, text: e.t, x: e.q.x + e.q.width / 2, y: e.q.y + e.q.height / 2,
    w: Math.round(e.q.width), h: Math.round(e.q.height), n: cands.length };
}, label);
const clickItem = async (label) => {
  const h = await findItem(label);
  if (!h.found) { log(`  🔴 找不到「${label}」`); return null; }
  log(`  >>> 点菜单项「${label}」（逐字「${h.text}」 ${h.w}×${h.h}）`);
  await p.mouse.move(h.x, h.y); await p.waitForTimeout(350);
  await p.mouse.click(h.x, h.y); await p.waitForTimeout(1600);
  return h;
};

out.start = await state();
log('起点：', JSON.stringify({ tool: out.start.tool.aria, zoom: out.start.zoom.aria }));

// ================= 选择工具态：先把菜单项逐字抄一遍（当基线） =================
log('\n===== 基线：选择工具态下列出缩放菜单全部项 =====');
let s = out.start;
if (s.tool.aria !== '选择工具') { await clickBtn(s.tool, '工具切换'); s = await state(); }
await clickBtn(s.zoom, '缩放值按钮');
out.menuItems = await p.evaluate(() => {
  const inp = document.querySelector('[data-testid="canvas-zoom-percent-input"]');
  if (!inp) return { open: false };
  // 菜单是输入框的兄弟浮层：往上找共同祖先
  let n = inp, host = inp.parentElement;
  for (let k = 0; k < 6 && host; k++, host = host.parentElement) {
    const items = Array.from(host.querySelectorAll('button,[role=menuitem],[role=option],li'))
      .map((e) => ({ t: (e.innerText || '').replace(/\s+/g, ' ').trim(), v: getComputedStyle(e).visibility,
        w: Math.round(e.getBoundingClientRect().width), h: Math.round(e.getBoundingClientRect().height) }))
      .filter((x) => x.t && x.w > 12 && x.h > 8 && x.v !== 'hidden');
    if (items.length >= 4) return { open: true, depth: k, n: items.length,
      items: items.map((x) => x.t), boxes: items.map((x) => `${x.w}×${x.h}`) };
    n = host;
  }
  return { open: true, items: [] };
});
log('菜单打开 =', out.menuItems.open, '｜项数 =', out.menuItems.n);
log('逐项：', JSON.stringify(out.menuItems.items));
log('尺寸：', JSON.stringify(out.menuItems.boxes));
save();
await p.keyboard.press('Escape'); await p.waitForTimeout(900);

// ================= 抓手态：放大视图 / 缩小视图 逐个点 =================
out.trials = [];
for (const [key, label] of [['zoomIn', '放大视图'], ['zoomOut', '缩小视图']]) {
  s = await state();
  if (s.tool.aria !== '抓手工具') { await clickBtn(s.tool, '工具切换'); s = await state(); }
  log(`\n===== 抓手态下点「${label}」（工具态 ${s.tool.aria}）=====`);
  if (!s.inputPresent) { await clickBtn(s.zoom, '缩放值按钮'); }
  const opened = (await state()).inputPresent;
  log('  菜单已打开 =', opened);
  const before = (await state()).zoom.aria;
  const h = await clickItem(label);
  const after = await state();
  out.trials.push({ key, label, menuOpened: opened, hit: h, toolAria: after.tool.aria,
    zoomBefore: before, zoomAfter: after.zoom.aria, inputPresentAfter: after.inputPresent,
    resp: before !== after.zoom.aria });
  log('   ', before, '→', after.zoom.aria, '｜工具态', after.tool.aria,
      '｜响应', before !== after.zoom.aria ? '✅' : '🔴');
  if (after.inputPresent) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
  save();
}

// ================= 归位 =================
log('\n===== 归位 =====');
s = await state();
log('归位前：', JSON.stringify({ tool: s.tool.aria, zoom: s.zoom.aria, mini: s.mini.pressed, conn: s.conn.pressed }));
if (s.tool.aria !== '选择工具') { await clickBtn(s.tool, '工具切换'); }
s = await state();
if (s.mini.pressed === 'true') { await clickBtn(s.mini, '小地图'); }
s = await state();
if (s.conn.pressed === 'false') { await clickBtn(s.conn, '显示连线'); }
s = await state();
if (!/60%/.test(s.zoom.aria)) {
  if (!s.inputPresent) { await clickBtn(s.zoom, '缩放值按钮'); }
  const sel = '[data-testid="canvas-zoom-percent-input"]';
  await p.click(sel).catch(() => {}); await p.waitForTimeout(350);
  await p.fill(sel, '').catch(() => {}); await p.type(sel, '60', { delay: 200 });
  await p.waitForTimeout(350); await p.keyboard.press('Enter'); await p.waitForTimeout(1800);
}
const e1 = await state(); await p.waitForTimeout(1200); const e2 = await state();
out.end = { first: e1.zoom.aria, second: e2.zoom.aria };
out.clean = e1.tool.aria === '选择工具' && e1.mini.pressed === 'false' && e1.conn.pressed === 'true'
  && /60%/.test(e1.zoom.aria) && e1.zoom.aria === e2.zoom.aria;
log('终态：', JSON.stringify({ tool: e1.tool.aria, mini: e1.mini.pressed, conn: e1.conn.pressed, zoom: e1.zoom.aria, zoomAgain: e2.zoom.aria }));
log('clean =', out.clean);
save();
await b.close();
