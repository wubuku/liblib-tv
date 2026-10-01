// 批次 63 主实验 v3：把九个模型逐个测完 + 时长 + 比例/分辨率入口。
//
// v2 的三个坑，这一版逐个堵上：
//   ① **模型名提取**：`text.split(/(?=\s)/)[0]` 对中文名无效
//      （「即梦 Seedance 2.5」→ 只剩「即梦」⇒ 五个即梦模型全测了第一个）。
//      v2 实测 DOM：**名称是独立的 `SPAN.block.overflow-hidden.truncate`（22 高）**，
//      说明是另一个 `SPAN.block.truncate.text-xs`（20 高）⇒ 按**类名**取，不用文本猜。
//   ② **列表会滚动**：弹层 `overflow-y: hidden`、`scrollH === clientH === 384`，
//      但内部有个 `DIV.pointer-events-auto.touch-none.absolute` **2×183** 的滚动条
//      ⇒ 内容约是视口的 2 倍。第九个模型 Wan 3.0 的名称在 **y=822**，落在 720 视口之外。
//      修法：先 `scrollIntoView` 再点，并**断言落点属于该名称所在的那一项**。
//   ③ **Escape 会连带关掉面板**：v2 探针里 A 段按完 Escape 就 `noform` 了。
//      修法：`ensurePanel()` 在每一步之前兜底。
//
// 🔑 全程**不点生成**。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const SHOTS = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const OUT = new URL('./_tmp-b63-price3.json', import.meta.url);
const FORM = 'form[data-testid="video-generation-form"]';
const MINE = [];

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);
const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const statusLine = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
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
const makeNode = async (k) => { await deselect();
  const rb = await p.evaluate((nm) => { const e = Array.from(document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button'))
      .find((x) => (x.getAttribute('aria-label') || '').startsWith(nm)); if (!e) return null;
    const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }, k);
  if (!rb) return null; const pre = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
  await p.mouse.click(rb.cx, rb.cy); await p.waitForTimeout(3400);
  const m = (await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')))).filter((x) => !pre.includes(x));
  return m.length === 1 ? m[0] : null; };
const selectMine = async (id) => { await deselect();
  const pts = await p.evaluate((vid) => { const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return []; const r = n.getBoundingClientRect(); const o = [];
    for (let fy = 0.14; fy <= 0.88; fy += 0.07) for (let fx = 0.14; fx <= 0.88; fx += 0.07) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
      const el = document.elementFromPoint(x, y); if (!el || !el.closest(`.react-flow__node[data-id="${vid}"]`)) continue;
      if (el.closest('button,a,[role="button"],input,textarea,select,[role="menu"]')) continue; o.push({ x, y }); } return o; }, id);
  for (const pt of pts) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(600);
    if (await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"].selected`), id)) return true; } return false; };
const ensurePanel = async (id) => { if (await hasForm()) return true; if (!(await selectMine(id))) return false;
  await p.waitForTimeout(1600); return await hasForm(); };
const deleteById = async (id) => { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); }
  await selectMine(id); await p.waitForTimeout(400);
  await p.evaluate((vid) => { const e = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!e) return; const r = e.getBoundingClientRect();
    for (let fy = 0.12; fy <= 0.9; fy += 0.08) for (let fx = 0.12; fx <= 0.9; fx += 0.08) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const t = document.elementFromPoint(x, y); if (!t || !t.closest(`.react-flow__node[data-id="${vid}"]`)) continue;
      if (t.closest('button,a,[role="button"],input,textarea,select')) continue;
      e.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, clientX: x, clientY: y }));
      e.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, clientX: x, clientY: y }));
      e.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y })); return; } }, id);
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
const restoreZoom = async () => { for (let t = 0; t < 3; t++) { const z = await zoomOf();
    if (z && z.includes('60%')) { console.log('  缩放归位 ok:', z); return true; }
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
    const s = 'input[data-testid=canvas-zoom-percent-input]';
    if (await p.$(s)) { await p.fill(s, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); }
    else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } }
  console.log('  缩放归位 FAILED:', await zoomOf()); return false; };
const clickChip = async (pre) => { const r = await p.evaluate(([F, pr]) => { const f = document.querySelector(F); if (!f) return { why: 'noform' };
    const e = Array.from(f.querySelectorAll('[aria-label]')).find((x) => (x.getAttribute('aria-label') || '').startsWith(pr));
    if (!e) return { why: 'nochip', avail: Array.from(f.querySelectorAll('[aria-label]')).map((x) => x.getAttribute('aria-label')) };
    const q = e.getBoundingClientRect(); const cx = Math.round(q.x + q.width / 2), cy = Math.round(q.y + q.height / 2);
    const t = document.elementFromPoint(cx, cy); const o = t && t.closest('[aria-label]');
    return { cx, cy, aria: e.getAttribute('aria-label'), landed: !!o && o === e }; }, [FORM, pre]);
  if (r.why) return { ok: false, ...r }; if (!r.landed) return { ok: false, why: 'occluded' };
  await p.mouse.click(r.cx, r.cy); await p.waitForTimeout(1500); return { ok: true, aria: r.aria }; };
// 模型弹层：按**名称 span 的类名**定位 + 滚动 + 断言落点属于该项
const NAME_SEL = 'span.block.overflow-hidden.truncate';
const listModelNames = () => p.evaluate((S) => { const pop = Array.from(document.querySelectorAll('[role="listbox"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
  if (!pop) return null; return Array.from(pop.querySelectorAll(S)).map((e) => { const r = e.getBoundingClientRect();
    return { name: (e.innerText || '').trim(), y: Math.round(r.y), inView: r.top >= 0 && r.bottom <= innerHeight,
      row: (() => { let n = e; while (n && n !== pop && !(n.className || '').toString().match(/cursor-pointer|flex|w-full/)) n = n.parentElement; return n ? String(n.className).slice(0, 40) : ''; })() }; }); }, NAME_SEL);
const pickModel = async (name) => { const r = await p.evaluate(([S, nm]) => {
  const pop = Array.from(document.querySelectorAll('[role="listbox"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
  if (!pop) return { why: 'nopop' };
  const el = Array.from(pop.querySelectorAll(S)).find((x) => (x.innerText || '').trim() === nm);
  if (!el) return { why: 'gone' };
  el.scrollIntoView({ block: 'center' });
  const row = el.closest('*') && el.parentElement ? el.parentElement : el;
  // 往上找到可点的那一层（含禁用标记的）
  let clickable = el, dis = null;
  for (let n = el; n && n !== pop; n = n.parentElement) { if (n.getAttribute && n.getAttribute('aria-disabled') !== null) { dis = n.getAttribute('aria-disabled'); clickable = n; break; } }
  const q = clickable.getBoundingClientRect();
  const cx = Math.round(q.x + q.width / 2), cy = Math.round(q.y + Math.min(q.height / 2, 30));
  const t = document.elementFromPoint(cx, cy);
  const hit = t && (t === el || el.contains(t) || (t.closest && t.closest('*') && el.closest('*') && el.closest('*').contains(t.closest('*'))));
  return { cx, cy, dis, landed: !!hit, y: Math.round(q.y), h: Math.round(q.height) }; }, [NAME_SEL, name]);
  if (r.why) return { ok: false, ...r };
  if (r.dis === 'true') return { ok: false, why: 'disabled' };
  if (!r.landed) return { ok: false, why: 'occluded', r };
  await p.mouse.click(r.cx, r.cy); await p.waitForTimeout(1900); return { ok: true, r }; };
const readParams = () => p.evaluate((F) => { const f = document.querySelector(F); if (!f) return null;
  const bar = f.querySelector('[data-testid="video-generation-fixed-parameters"]'); const t = (f.innerText || '').replace(/\n{2,}/g, '\n');
  return { barText: bar ? (bar.innerText || '').replace(/\s+/g, ' ').trim() : null,
    chips: bar ? Array.from(bar.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')) : [],
    price: (t.match(/Current price[^\n]*/) || [null])[0], original: (t.match(/Original price[^\n]*/) || [null])[0],
    discount: (t.match(/Discount[^\n]*/) || [null])[0] }; }, FORM);
const closePopup = async (id) => { await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  if ((await p.evaluate(() => Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).length)) > 0) {
    await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
  if (!(await hasForm())) await ensurePanel(id); };

const out = { startedAt: new Date().toISOString() };
const c0 = await credit();
console.log('=== 批次 63 v3：九个模型逐个测 + 时长 + 比例入口 ===\n起点:', await statusLine(), '| 积分', c0, '| 缩放', await zoomOf());
await restoreZoom();
out.start = { status: await statusLine(), credit: c0 };
try {
  const id = await makeNode('视频');
  console.log('建临时视频节点:', id);
  if (!id) throw new Error('建节点失败');
  MINE.push(id); out.nodeId = id;
  await p.waitForTimeout(1700);
  const base = await readParams();
  console.log('\n基线 bar:', base.barText, '| 价格:', base.price);
  out.baseline = base;

  // ── A. 九个模型逐个
  console.log('\n======== A. 逐个模型（每次都从基线状态出发会串味，故记录实际前值）========');
  const names = [];
  console.log('  开模型弹层:', JSON.stringify(await clickChip('选择模型')));
  const l0 = await listModelNames();
  if (l0) { for (const n of l0) { names.push(n.name); console.log(`   · ${n.name}  y=${n.y} 视口内=${n.inView}`); } }
  out.modelNames = names;
  await closePopup(id);
  out.models = [];
  for (const nm of names) {
    if (!(await ensurePanel(id))) { console.log('  面板掉了'); break; }
    const before = await readParams();
    const o = await clickChip('选择模型');
    if (!o.ok) { console.log(`  [${nm}] 开弹层失败`, JSON.stringify(o)); await closePopup(id); continue; }
    const pick = await pickModel(nm);
    if (!pick.ok) { console.log(`  [${nm}] 未选中`, JSON.stringify(pick)); await closePopup(id); continue; }
    await p.waitForTimeout(1000);
    const panelKept = await ensurePanel(id);
    const after = panelKept ? await readParams() : null;
    const cr = await credit();
    if (!after) { console.log(`  [${nm}] 选完面板没了`); continue; }
    console.log(`  «${nm}»${before.barText.includes(nm) ? '(本来就是它)' : ''}`);
    console.log(`     ${before.barText}  ⇒  ${after.barText}`);
    console.log(`     ${before.price}  ⇒  ${after.price}${after.price !== before.price ? '  ★变了' : ''}`);
    console.log(`     积分 ${cr} | chips: ${after.chips.join(' ｜ ')}`);
    out.models.push({ name: nm, before: before, after, credit: cr, changed: after.price !== before.price });
    if (after.barText.includes('样片')) { await p.screenshot({ path: new URL('63-price-model-sample.png', SHOTS).pathname, clip: { x: 260, y: 445, width: 700, height: 225 } }); console.log('     📷 63-price-model-sample.png'); }
    await closePopup(id);
  }

  // ── B. 时长
  console.log('\n======== B. 时长弹层 ========');
  if (await ensurePanel(id)) {
    const ob = await clickChip('选择视频生成时长');
    console.log('  开弹层:', JSON.stringify(ob));
    if (ob.ok) {
      const dur = await p.evaluate(() => Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"]')).filter((e) => e.getBoundingClientRect().width > 1)
        .map((e) => { const r = e.getBoundingClientRect();
          return { role: e.getAttribute('role'), box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
            text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200),
            clickable: Array.from(e.querySelectorAll('*')).filter((x) => { const q = x.getBoundingClientRect(); return q.width > 1 && q.height > 1 && x.children.length === 0; })
              .map((x) => { const q = x.getBoundingClientRect(); return `${x.tagName}«${(x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20)}»${Math.round(q.width)}x${Math.round(q.height)}@${Math.round(q.x)},${Math.round(q.y)}`; }) }; }));
      console.log('  弹层:', JSON.stringify(dur, null, 1).slice(0, 2000));
      out.durationPop = dur;
    }
    await closePopup(id);
  }

  // ── C. 比例 / 分辨率入口
  console.log('\n======== C. 比例 / 分辨率入口 ========');
  if (await ensurePanel(id)) {
    const all = await p.evaluate((F) => { const f = document.querySelector(F); if (!f) return null;
      return Array.from(f.querySelectorAll('button,[role="button"],[aria-label],[data-testid]')).map((e) => { const r = e.getBoundingClientRect();
        return { tag: e.tagName, tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
          box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
          text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) }; })
        .filter((x) => x.box && !x.box.startsWith('0x0')); }, FORM);
    if (all) { console.log('  表单内可点元素', all.length, '个:');
      for (const c of all) console.log('   ', JSON.stringify(c)); out.allControls = all; }
    else console.log('  表单读不到（面板掉了）');
  }
  const cEnd = await credit();
  console.log('\n=== 积分全程 ===', c0, '->', cEnd, 'Δ=', cEnd - c0);
  out.creditEnd = cEnd;
} catch (e) { console.error('ABORT:', e.message); out.error = e.message; }
finally {
  console.log('\n=== 收尾 ===');
  for (const i of MINE) console.log('删', i, '->', await deleteById(i));
  for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(300); }
  await restoreZoom();
  for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(300); }
  const fin = await canvasPos();
  let dev = 0;
  for (const [id2, b2] of Object.entries(BASE.nodes)) { const cur = fin[id2];
    const d = cur && b2.canvas ? [Math.round((cur[0] - b2.canvas[0]) * 100) / 100, Math.round((cur[1] - b2.canvas[1]) * 100) / 100] : 'MISSING';
    if (d === 'MISSING' || (Array.isArray(d) && (Math.abs(d[0]) > 0.01 || Math.abs(d[1]) > 0.01))) dev++; }
  console.log('终态:', await statusLine(), '| 缩放', await zoomOf(), '| 积分', await credit(), '| 节点', Object.keys(fin).length, '| 偏离', dev);
  console.log('剩余待删:', JSON.stringify(MINE.filter((i) => fin[i])));
  out.end = { status: await statusLine(), zoom: await zoomOf(), credit: await credit(), dev, mineLeft: MINE.filter((i) => fin[i]) };
  writeFileSync(OUT, JSON.stringify(out, null, 1));
  console.log('写入', OUT.pathname);
  await b.close();
}
