// 批次 63 主实验 v2：用 **aria 前缀**定位参数 chip（而不是显示文字），
// 并且把「关弹层」与「关面板」拆开。
//
// 🔑 v1 的失败点：为了关弹层我按了 3 次 Escape，
// 而 **Escape 会连带取消选中节点 ⇒ 生成面板整个消失** ⇒
// 后面 11 次 `clickChip` 全部 `notfound`。
// 这是同一条纪律的**第五次**应验：**读数前先问前置条件还在不在。**
//
// v2 的两个修正：
//   ① chip 定位改用 **aria 前缀** —— 显示文字会随选择变化
//      （aria 分别是 `选择模型: …` / `视频尺寸选项: …` / `生成模式: …` / `选择视频生成时长: …`），
//      拿文字当锚点，第二轮就找不到第一个 chip 了。
//   ② `closePopup()` 只按**一次** Escape，然后断言「弹层没了 **且** 面板还在」；
//      面板不在就 `ensurePanel()` 重新选中节点。
//
// 全程**不点生成**（`generation-submit-icon` 永不点击）。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const SHOTS = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const OUT = new URL('./_tmp-b63-price2.json', import.meta.url);
const FORM = 'form[data-testid="video-generation-form"]';
const MINE = [];

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);

const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const statusLine = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const nodeIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const canvasPos = () => p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
  return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null]; })));
const hasForm = () => p.evaluate((F) => { const f = document.querySelector(F); return !!(f && f.getBoundingClientRect().width > 1); }, FORM);
const isEmpty = (x, y) => p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y); if (!el) return true;
  if (el.closest('.react-flow__node')) return false;
  if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"],[data-testid="canvas-feature-sidecar"]')) return false;
  return true; }, [x, y]);
const findEmpty = async () => { for (let y = 110; y <= 600; y += 20) for (let x = 90; x <= 1240; x += 20) {
  if (x > 1140 && y > 570) continue; if (await isEmpty(x, y)) return { x, y }; } return null; };
const deselect = async () => { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); }
  const e = await findEmpty(); if (e) { await p.mouse.click(e.x, e.y); await p.waitForTimeout(600); } };
const makeNode = async (kind) => { await deselect();
  const rb = await p.evaluate((nm) => { const e = Array.from(document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button'))
      .find((x) => (x.getAttribute('aria-label') || '').startsWith(nm)); if (!e) return null;
    const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }, kind);
  if (!rb) return { err: '左栏没找到按钮' };
  const pre = await nodeIds();
  await p.mouse.click(rb.cx, rb.cy); await p.waitForTimeout(3400);
  const made = (await nodeIds()).filter((x) => !pre.includes(x));
  if (made.length !== 1) return { err: `新增 ${made.length} 个` };
  MINE.push(made[0]); return { id: made[0] }; };
// 选中我自己的节点（细网格扫落点，逐点校验归属）
const selectMine = async (id) => { await deselect();
  const pts = await p.evaluate((vid) => { const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return [];
    const r = n.getBoundingClientRect(); const out = [];
    for (let fy = 0.14; fy <= 0.88; fy += 0.07) for (let fx = 0.14; fx <= 0.88; fx += 0.07) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
      const el = document.elementFromPoint(x, y); if (!el || !el.closest(`.react-flow__node[data-id="${vid}"]`)) continue;
      if (el.closest('button,a,[role="button"],input,textarea,select,[role="menu"]')) continue;
      out.push({ x, y }); } return out; }, id);
  for (const pt of pts) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(600);
    if (await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"].selected`), id)) return true; }
  return false; };
const ensurePanel = async (id) => { if (await hasForm()) return true;
  if (!(await selectMine(id))) return false; await p.waitForTimeout(1500); return await hasForm(); };
const deleteById = async (id) => { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); }
  await selectMine(id); await p.waitForTimeout(400);
  const ok = await p.evaluate((vid) => { const e = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!e) return false;
    const r = e.getBoundingClientRect();
    for (let fy = 0.12; fy <= 0.9; fy += 0.08) for (let fx = 0.12; fx <= 0.9; fx += 0.08) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const t = document.elementFromPoint(x, y); if (!t || !t.closest(`.react-flow__node[data-id="${vid}"]`)) continue;
      if (t.closest('button,a,[role="button"],input,textarea,select')) continue;
      e.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, clientX: x, clientY: y }));
      e.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, clientX: x, clientY: y }));
      e.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y })); return true; } return false; }, id);
  await p.waitForTimeout(900);
  if (await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"].selected`), id)) {
    await p.evaluate(() => { const e = document.querySelector('.react-flow__node.selected'); if (!e) return; const r = e.getBoundingClientRect();
      e.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 14) })); });
    await p.waitForTimeout(800);
    await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
      const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
    await p.waitForTimeout(1400); }
  for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); }
  return (await p.evaluate((v) => !document.querySelector(`.react-flow__node[data-id="${v}"]`), id)) ? 'deleted' : 'STILL-THERE'; };
const restoreZoom = async (want = '60%') => { for (let t = 0; t < 3; t++) { const z = await zoomOf();
    if (z && z.includes(want)) { console.log('  缩放归位 ok:', z); return true; }
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
    const s = 'input[data-testid=canvas-zoom-percent-input]';
    if (await p.$(s)) { await p.fill(s, want.replace('%', '')); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); }
    else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } }
  console.log('  缩放归位 FAILED:', await zoomOf(), '| 目标', want); return false; };
const pops = () => p.evaluate(() => Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"],[role="menu"]'))
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { role: e.getAttribute('role'), box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      items: Array.from(e.querySelectorAll('[role="option"],[role="menuitem"],[role="radio"],li')).map((x) => { const q = x.getBoundingClientRect();
        return { sel: x.getAttribute('aria-selected'), check: x.getAttribute('aria-checked'), dis: x.getAttribute('aria-disabled'),
          box: `${Math.round(q.width)}x${Math.round(q.height)}@${Math.round(q.x)},${Math.round(q.y)}`,
          text: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 70) }; }) }; }));
const readParams = () => p.evaluate((F) => { const f = document.querySelector(F); if (!f) return null;
  const bar = f.querySelector('[data-testid="video-generation-fixed-parameters"]');
  const t = (f.innerText || '').replace(/\n{2,}/g, '\n');
  return { barText: bar ? (bar.innerText || '').replace(/\s+/g, ' ').trim() : null,
    chips: bar ? Array.from(bar.querySelectorAll('[aria-label]')).map((e) => { const r = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
        text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) }; }) : [],
    price: (t.match(/Current price[^\n]*/) || [null])[0],
    original: (t.match(/Original price[^\n]*/) || [null])[0],
    discount: (t.match(/Discount[^\n]*/) || [null])[0] }; }, FORM);
// 按 **aria 前缀** 点 chip
const clickChip = async (ariaPrefix) => { const r = await p.evaluate(([F, pre]) => { const f = document.querySelector(F); if (!f) return { why: 'noform' };
    const e = Array.from(f.querySelectorAll('[aria-label]')).find((x) => (x.getAttribute('aria-label') || '').startsWith(pre));
    if (!e) return { why: 'nochip', avail: Array.from(f.querySelectorAll('[aria-label]')).map((x) => x.getAttribute('aria-label')) };
    const q = e.getBoundingClientRect(); const cx = Math.round(q.x + q.width / 2), cy = Math.round(q.y + q.height / 2);
    const t = document.elementFromPoint(cx, cy); const o = t && t.closest('[aria-label]');
    return { cx, cy, aria: e.getAttribute('aria-label'), landed: !!o && o === e }; }, [FORM, ariaPrefix]);
  if (r.why) return { ok: false, ...r };
  if (!r.landed) return { ok: false, why: 'occluded', r };
  await p.mouse.click(r.cx, r.cy); await p.waitForTimeout(1400);
  return { ok: true, aria: r.aria }; };
// 在弹层里点「文字以 prefix 开头」的项
const pickInPop = async (prefix) => { const r = await p.evaluate((pre) => {
  const list = Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1);
  const pop = list.pop(); if (!pop) return { why: 'nopop' };
  const items = Array.from(pop.querySelectorAll('[role="option"],[role="menuitem"],[role="radio"],li'));
  const e = items.find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().startsWith(pre));
  if (!e) return { why: 'noitem', avail: items.map((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40)) };
  const q = e.getBoundingClientRect(); const cx = Math.round(q.x + q.width / 2), cy = Math.round(q.y + q.height / 2);
  const t = document.elementFromPoint(cx, cy); const o = t && t.closest('[role="option"],[role="menuitem"],[role="radio"],li');
  return { cx, cy, landed: !!o && o === e, dis: e.getAttribute('aria-disabled') }; }, prefix);
  if (r.why) return { ok: false, ...r };
  if (r.dis === 'true') return { ok: false, why: 'disabled' };
  if (!r.landed) return { ok: false, why: 'occluded' };
  await p.mouse.click(r.cx, r.cy); await p.waitForTimeout(1700);
  return { ok: true }; };
// 只关弹层：按**一次** Escape，断言弹层没了；面板若也没了就补选回来
const closePopup = async (id) => { await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  const left = (await pops()).length; const form = await hasForm();
  if (left) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
  if (!form) { await ensurePanel(id); }
  return { popsLeft: left, formKept: form }; };

const out = { startedAt: new Date().toISOString() };
const c0 = await credit();
console.log('=== 批次 63 v2：切换模型/比例/时长后的价格 ===\n起点:', await statusLine(), '| 积分', c0, '| 缩放', await zoomOf());
await restoreZoom();
out.start = { status: await statusLine(), credit: c0, zoom: await zoomOf() };

try {
  const v = await makeNode('视频');
  console.log('\n建临时视频节点:', JSON.stringify(v));
  if (!v.id) throw new Error('建节点失败 ' + JSON.stringify(v));
  out.nodeId = v.id;
  await p.waitForTimeout(1600);
  const base = await readParams();
  console.log('\n=== 面板基线 ===');
  console.log('bar:', base.barText, '| 价格:', base.price);
  for (const c of base.chips) console.log('  chip aria:', JSON.stringify(c.aria), c.box);
  out.baseline = base;
  console.log('积分:', await credit());

  const DIMS = [
    { key: 'model', pre: '选择模型' },
    { key: 'size', pre: '视频尺寸选项' },
    { key: 'duration', pre: '选择视频生成时长' },
  ];
  out.dims = {};
  for (const dim of DIMS) {
    console.log(`\n======== 维度：${dim.key}（aria 前缀「${dim.pre}」）========`);
    if (!(await ensurePanel(v.id))) { console.log('  面板没起来'); out.dims[dim.key] = { rows: [], err: 'nopanel' }; continue; }
    const op = await clickChip(dim.pre);
    console.log('  开弹层:', JSON.stringify(op));
    if (!op.ok) { out.dims[dim.key] = { open: op, rows: [] }; continue; }
    const pop = (await pops()).pop();
    if (!pop) { console.log('  没有弹层'); out.dims[dim.key] = { open: op, rows: [] }; continue; }
    console.log('  弹层:', pop.role, pop.box, '| 项数', pop.items.length);
    for (const it of pop.items) console.log(`    ${it.box} sel=${it.sel} dis=${it.dis} «${it.text}»`);
    out.dims[dim.key] = { pop: { role: pop.role, box: pop.box, items: pop.items }, rows: [] };
    const names = pop.items.map((i) => (i.text.split(/(?=\s)/)[0] || i.text).trim());
    await closePopup(v.id);

    for (const nm of names) {
      if (!(await ensurePanel(v.id))) { console.log('  面板掉了，中断'); break; }
      const before = await readParams();
      const o2 = await clickChip(dim.pre);
      if (!o2.ok) { console.log(`  [${nm}] 开弹层失败`, JSON.stringify(o2)); await closePopup(v.id); continue; }
      const pick = await pickInPop(nm);
      if (!pick.ok) { console.log(`  [${nm}] 未选中`, JSON.stringify(pick)); await closePopup(v.id); continue; }
      await p.waitForTimeout(1000);
      if (!(await ensurePanel(v.id))) { console.log(`  [${nm}] 选完面板没了`); continue; }
      const after = await readParams();
      const cr = await credit();
      console.log(`  «${nm}»  bar: ${before.barText}  ⇒  ${after.barText}`);
      console.log(`      价格: ${before.price}  ⇒  ${after.price}  ${after.price !== before.price ? '★变了' : '(没变)'}`);
      console.log(`      积分 ${cr} | chip aria: ${(after.chips || []).map((c) => c.aria).join(' ｜ ')}`);
      out.dims[dim.key].rows.push({ name: nm, barBefore: before.barText, barAfter: after.barText,
        priceBefore: before.price, priceAfter: after.price, priceChanged: after.price !== before.price,
        barChanged: after.barText !== before.barText, credit: cr, chips: after.chips });
      await closePopup(v.id);
    }
  }
  // 配图：当前参数条（已被改过）
  if (await ensurePanel(v.id)) { await p.screenshot({ path: new URL('63-price-params.png', SHOTS).pathname, clip: { x: 260, y: 445, width: 700, height: 225 } }); console.log('\n📷 63-price-params.png'); }
  const cEnd = await credit();
  console.log('\n=== 积分全程 ===', c0, '->', cEnd, 'Δ=', cEnd - c0);
  out.creditEnd = cEnd;
} catch (e) { console.error('ABORT:', e.message); out.error = e.message; }
finally {
  console.log('\n=== 收尾 ===');
  for (const id of MINE) console.log('删', id, '->', await deleteById(id));
  for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(300); }
  await restoreZoom();
  for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(300); }
  const fin = await canvasPos();
  let dev = 0;
  for (const [id, b2] of Object.entries(BASE.nodes)) { const cur = fin[id];
    const d = cur && b2.canvas ? [Math.round((cur[0] - b2.canvas[0]) * 100) / 100, Math.round((cur[1] - b2.canvas[1]) * 100) / 100] : 'MISSING';
    if (d === 'MISSING' || (Array.isArray(d) && (Math.abs(d[0]) > 0.01 || Math.abs(d[1]) > 0.01))) dev++; }
  console.log('终态:', await statusLine(), '| 缩放', await zoomOf(), '| 积分', await credit(), '| 节点', Object.keys(fin).length, '| 偏离', dev);
  console.log('剩余待删:', JSON.stringify(MINE.filter((id) => fin[id])));
  out.end = { status: await statusLine(), zoom: await zoomOf(), credit: await credit(), dev, mineLeft: MINE.filter((id) => fin[id]) };
  writeFileSync(OUT, JSON.stringify(out, null, 1));
  console.log('写入', OUT.pathname);
  await b.close();
}
