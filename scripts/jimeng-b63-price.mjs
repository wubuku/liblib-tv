// 批次 63 主实验：切换**模型 / 比例 / 时长**后价格如何变化。
//
// 手册 `prepare-generation.md:415` 写「未验证 …（避免误触发扣费前置动作）」——
// 这个理由是批次 61、62 连续两次推翻过的**同一个滥用标签**。
// 批次 61 的实测读数：改宿主节点的参考列表，八轮积分 805→805。
// **改模型/比例/时长同样是「改设置 + 读价格」，不点生成就不扣费。**
//
// 🔑 本批全程**不点生成**（`generation-submit-icon` 永不点击）。
// 🔑 全部在**自建临时节点**上做 —— 共享画布上那 6 个是别人的。
//
// 附带更正：上一轮照抄手册的 `form[data-testid=generation-form]` 读到 null，
// 真实 testid 是 **`video-generation-form`**。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const SHOTS = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const OUT = new URL('./_tmp-b63-price.json', import.meta.url);
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
const reset = async () => { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); } };
const isEmpty = (x, y) => p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y); if (!el) return true;
  if (el.closest('.react-flow__node')) return false;
  if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"],[data-testid="canvas-feature-sidecar"]')) return false;
  return true; }, [x, y]);
const findEmpty = async () => { for (let y = 110; y <= 600; y += 20) for (let x = 90; x <= 1240; x += 20) {
  if (x > 1140 && y > 570) continue; if (await isEmpty(x, y)) return { x, y }; } return null; };
const deselect = async () => { await reset(); const e = await findEmpty(); if (e) { await p.mouse.click(e.x, e.y); await p.waitForTimeout(600); } return true; };
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
const deleteById = async (id) => { await reset();
  const ok = await p.evaluate((vid) => { const e = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!e) return false; const r = e.getBoundingClientRect();
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
    await p.waitForTimeout(1300); }
  await reset();
  return (await p.evaluate((v) => !document.querySelector(`.react-flow__node[data-id="${v}"]`), id)) ? 'deleted' : 'STILL-THERE'; };
// 缩放归位：填 60 + Enter 偶发不生效 ⇒ **回读验证 + 最多 3 次**
const restoreZoom = async (want = '60%') => { for (let t = 0; t < 3; t++) { const z = await zoomOf();
    if (z && z.includes(want)) { console.log('  缩放归位 ok:', z); return true; }
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
    const s = 'input[data-testid=canvas-zoom-percent-input]';
    if (await p.$(s)) { await p.fill(s, want.replace('%', '')); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); }
    else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } }
  const z = await zoomOf(); console.log('  缩放归位 FAILED:', z, '| 目标', want); return z && z.includes(want); };
const closeSidecar = async () => { const st = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-feature-sidecar"]');
  if (!e || e.getBoundingClientRect().width < 1) return 'absent'; return e.querySelector('[data-testid="canvas-agent-panel"]') ? 'EXPANDED' : 'COLLAPSED'; });
  if (st !== 'EXPANDED') return st;
  const r = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-agent-session-collapse"]'); if (!e) return null;
    const b = e.getBoundingClientRect(); return { cx: Math.round(b.x + b.width / 2), cy: Math.round(b.y + b.height / 2) }; });
  if (r) { await p.mouse.click(r.cx, r.cy); await p.waitForTimeout(1400); }
  return await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-feature-sidecar"]');
    if (!e || e.getBoundingClientRect().width < 1) return 'absent'; return e.querySelector('[data-testid="canvas-agent-panel"]') ? 'EXPANDED' : 'COLLAPSED'; }); };

// ── 面板读数
const FORM = 'form[data-testid="video-generation-form"]';
const params = () => p.evaluate((F) => { const f = document.querySelector(F); if (!f) return null;
  const bar = f.querySelector('[data-testid="video-generation-fixed-parameters"]');
  const t = (f.innerText || '').replace(/\n{2,}/g, '\n');
  return { aria: f.getAttribute('aria-label'),
    barText: bar ? (bar.innerText || '').replace(/\s+/g, ' ').trim() : null,
    barChips: bar ? Array.from(bar.querySelectorAll('button,[role="button"],[data-testid]')).map((e) => { const r = e.getBoundingClientRect();
      return { tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
        box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
        text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) }; }) : null,
    price: (t.match(/Current price[^\n]*/) || [null])[0],
    original: (t.match(/Original price[^\n]*/) || [null])[0],
    discount: (t.match(/Discount[^\n]*/) || [null])[0],
    full: t.trim().slice(0, 400) }; }, FORM);
const pops = () => p.evaluate(() => Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"],[role="menu"]'))
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { role: e.getAttribute('role'), tid: e.getAttribute('data-testid'),
      box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      items: Array.from(e.querySelectorAll('[role="option"],[role="menuitem"],[role="radio"],li,[data-value]')).map((x) => { const q = x.getBoundingClientRect();
        return { role: x.getAttribute('role'), sel: x.getAttribute('aria-selected'), check: x.getAttribute('aria-checked'),
          disabled: x.getAttribute('aria-disabled'),
          box: `${Math.round(q.width)}x${Math.round(q.height)}@${Math.round(q.x)},${Math.round(q.y)}`,
          text: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) }; }),
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400) }; }));
// 点参数条上某个 chip（按**当前显示文字**定位，并断言落点属于它）
const clickChip = async (label) => { const r = await p.evaluate(([F, lb]) => { const f = document.querySelector(F); if (!f) return null;
    const bar = f.querySelector('[data-testid="video-generation-fixed-parameters"]'); if (!bar) return null;
    const e = Array.from(bar.querySelectorAll('*')).find((x) => (x.innerText || '').trim() === lb);
    if (!e) return null; const q = e.getBoundingClientRect();
    const cx = Math.round(q.x + q.width / 2), cy = Math.round(q.y + q.height / 2);
    const t = document.elementFromPoint(cx, cy); const own = t && (t === e || e.contains(t) || (t.closest && t.closest('*') && e.contains(t.closest('*'))));
    return { cx, cy, landed: !!t && !!(t.closest && t.closest('*') && (e.contains(t.closest('*')) || e === t.closest('*'))) }; }, [FORM, label]);
  if (!r) return { ok: false, why: 'notfound' };
  if (!r.landed) return { ok: false, why: 'occluded' };
  await p.mouse.click(r.cx, r.cy); await p.waitForTimeout(1300);
  return { ok: true, ...r }; };
// 在弹层里点逐字等于 label 的项（并断言落点属于该项）
const pickInPop = async (label) => { const r = await p.evaluate((lb) => {
  const pops = Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1);
  const pop = pops.pop(); if (!pop) return { why: 'nopop' };
  const items = Array.from(pop.querySelectorAll('[role="option"],[role="menuitem"],[role="radio"],li,[data-value]'));
  const e = items.find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === lb);
  if (!e) return { why: 'noitem', avail: items.map((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30)) };
  const q = e.getBoundingClientRect(); const cx = Math.round(q.x + q.width / 2), cy = Math.round(q.y + q.height / 2);
  const t = document.elementFromPoint(cx, cy);
  const owner = t && t.closest('[role="option"],[role="menuitem"],[role="radio"],li,[data-value]');
  return { cx, cy, landed: !!owner && owner === e, disabled: e.getAttribute('aria-disabled') }; }, label);
  if (!r || r.why) return { ok: false, ...r };
  if (r.disabled === 'true') return { ok: false, why: 'disabled' };
  if (!r.landed) return { ok: false, why: 'occluded' };
  await p.mouse.click(r.cx, r.cy); await p.waitForTimeout(1600);
  return { ok: true }; };

const out = { startedAt: new Date().toISOString() };
const c0 = await credit();
console.log('=== 批次 63：切换模型/比例/时长后的价格 ===\n起点:', await statusLine(), '| 积分', c0, '| 缩放', await zoomOf(), '| 侧栏', await closeSidecar());
out.start = { status: await statusLine(), credit: c0, zoom: await zoomOf() };
console.log('缩放归位:', await restoreZoom());

try {
  const v = await makeNode('视频');
  console.log('\n建临时视频节点:', JSON.stringify(v));
  if (!v.id) throw new Error('建节点失败 ' + JSON.stringify(v));
  out.nodeId = v.id;
  await p.waitForTimeout(1500);

  const base = await params();
  console.log('\n=== 面板基线 ===');
  console.log('form aria:', base.aria, '| bar:', base.barText);
  console.log('价格:', base.price, '| 原文:', base.original, '| 折扣:', base.discount);
  console.log('参数条 chip:', JSON.stringify(base.barChips, null, 1));
  out.baseline = base;
  const cBase = await credit();
  console.log('积分（建节点后）:', cBase);

  const dims = [
    { key: 'model', label: (base.barText.match(/即梦.*?VIP|即梦.*?(?=\s{2}|$)/) || ['即梦 Seedance 2.0 VIP'])[0].trim() },
    { key: 'ratio', label: (base.barText.match(/\d+:\d+/) || ['16:9'])[0] },
    { key: 'duration', label: (base.barText.match(/\d+s/) || ['4s'])[0] },
  ];
  console.log('\n三个维度锚定文字:', JSON.stringify(dims));

  out.dims = {};
  for (const dim of dims) {
    console.log(`\n======== 维度：${dim.key}（锚定「${dim.label}」）========`);
    const op = await clickChip(dim.label);
    console.log('  开弹层:', JSON.stringify(op));
    if (!op.ok) { out.dims[dim.key] = { open: op, rows: [] }; continue; }
    let pop = (await pops()).pop();
    if (!pop) { console.log('  没有弹层'); out.dims[dim.key] = { open: op, rows: [] }; continue; }
    console.log('  弹层:', pop.role, pop.box, '| 项数', pop.items.length);
    for (const it of pop.items) console.log(`    ${it.box} sel=${it.sel} check=${it.check} dis=${it.disabled} «${it.text}»`);
    const labels = pop.items.map((i) => i.text);
    out.dims[dim.key] = { open: op, pop: { role: pop.role, box: pop.box, items: pop.items }, rows: [] };
    await reset(); await p.waitForTimeout(600);

    for (const lb of labels) {
      const before = await params();
      const o2 = await clickChip(dim.label);
      if (!o2.ok) { console.log(`  [${lb}] 重开弹层失败`, JSON.stringify(o2)); await reset(); continue; }
      const pick = await pickInPop(lb);
      if (!pick.ok) { console.log(`  [${lb}] 未选中`, JSON.stringify(pick)); await reset(); continue; }
      await p.waitForTimeout(900);
      const after = await params();
      const cr = await credit();
      const changed = after.barText !== before.barText;
      const priceChanged = after.price !== before.price;
      console.log(`  «${lb}» → bar: ${before.barText}  ⇒  ${after.barText}`);
      console.log(`     价格: ${before.price}  ⇒  ${after.price}  ${priceChanged ? '★变了' : '(没变)'} | 积分 ${cr} | bar${changed ? '变了' : '没变'}`);
      out.dims[dim.key].rows.push({ label: lb, barBefore: before.barText, barAfter: after.barText, priceBefore: before.price, priceAfter: after.price, credit: cr, priceChanged, barChanged: changed });
      await reset(); await p.waitForTimeout(500);
    }
  }
  const cEnd = await credit();
  console.log('\n=== 积分全程 ===', c0, '->', cEnd, 'Δ=', cEnd - c0);
  out.creditEnd = cEnd;
  // 最后一张配图：展示被改过的参数条
  await p.screenshot({ path: new URL('63-price-params.png', SHOTS).pathname, clip: { x: 260, y: 445, width: 700, height: 225 } });
  console.log('📷 63-price-params.png');
} catch (e) { console.error('ABORT:', e.message); out.error = e.message; }
finally {
  console.log('\n=== 收尾 ===');
  for (const id of MINE) console.log('删', id, '->', await deleteById(id));
  await reset();
  console.log('缩放归位:', await restoreZoom());
  await reset();
  const fin = await canvasPos();
  let dev = 0;
  for (const [id, base2] of Object.entries(BASE.nodes)) { const cur = fin[id];
    const d = cur && base2.canvas ? [Math.round((cur[0] - base2.canvas[0]) * 100) / 100, Math.round((cur[1] - base2.canvas[1]) * 100) / 100] : 'MISSING';
    if (d === 'MISSING' || (Array.isArray(d) && (Math.abs(d[0]) > 0.01 || Math.abs(d[1]) > 0.01))) dev++; }
  console.log('终态:', await statusLine(), '| 缩放', await zoomOf(), '| 积分', await credit(), '| 节点', Object.keys(fin).length, '| 偏离', dev);
  console.log('剩余待删:', JSON.stringify(MINE.filter((id) => fin[id])));
  out.end = { status: await statusLine(), zoom: await zoomOf(), credit: await credit(), dev, mineLeft: MINE.filter((id) => fin[id]) };
  writeFileSync(OUT, JSON.stringify(out, null, 1));
  console.log('写入', OUT.pathname);
  await b.close();
}
