// 批次 95 · 受控复测第 2 轮：**锁定同一个节点 id** 重做两件事。
//
// 🔴 上一轮（b95g）两个实验都废掉，但废法各有意思：
//
//   ① **双击实验 VOID**：`findTextNode()` 返回 null —— 32 个节点里没有一个是
//      「未选中 + 视口内 + 点得到」的文本节点。VOID 照记，不当成「不存在」。
//
//   ② **缩放三档读数被污染**：40% 档读到 node 128×128，60%/100% 档都读到 75×75。
//      除以各自 scale 得 canvas 320 / 125 / 75 —— **同一个节点不该在换缩放后改尺寸**。
//      真因是：`findTextNode()` 每档都**扫出不同的节点**（视口内容随缩放变），
//      于是「屏上恒定 vs 随缩放」这个判据根本没在比同一个对象。
//      ⇒ **换缩放做对照，唯一变量必须是节点**：锁定 `data-id`，并在每档把 `aria` 打出来自证同一个。
//      （这与批次 89 「Add tags」那批是同族坑：那次是**逐节点**读各自的 counter-scale，
//        这次连「逐节点」都没做，直接读了「扫到的第一个」。）
//
// 实验 A 的纪律：**双击就只发双击**（`mouse.dblclick`），任何前置单击都不许有；
// 另外加 A6 格专门**复现批次 93 当初那个错误序列**（单击→立即双击＝三击），
// 看它到底读到什么——把「批次 93 的结论对不对」和「批次 93 的测法对不对」分开。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), cells: [], zooms: [] };

const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const nodeN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const scaleNow = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport');
  const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; });
const zoomPct = () => p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]');
  return e ? Number((e.getAttribute('aria-label').match(/(\d+)%/) || [])[1]) : null; });
const scaleStable = async () => { const a = await scaleNow(); await p.waitForTimeout(400); const c = await scaleNow();
  return { a, c, stable: a !== null && a === c, usable: a }; };

const read = (label, id) => p.evaluate((l) => {
  const n = l.id ? document.querySelector(`.react-flow__node[data-id="${l.id}"]`) : null;
  const g = (t) => { const e = document.querySelector(`[data-testid="${t}"]`); if (!e) return null;
    const r = e.getBoundingClientRect();
    return { w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y) }; };
  const cnt = (t) => document.querySelectorAll(`[data-testid="${t}"]`).length;
  const nb = n ? n.getBoundingClientRect() : null;
  const inView = nb ? (nb.right > 0 && nb.bottom > 0 && nb.left < 1280 && nb.top < 720) : null;
  // 归属校验：这个锁定节点此刻**自己**点上会选到谁
  const owner = (inView && nb) ? (() => { const x = Math.round(nb.x + nb.width / 2), y = Math.round(nb.y + nb.height / 2);
    if (x < 0 || y < 0 || x > 1280 || y > 720) return 'offscreen';
    const e = document.elementFromPoint(x, y); const o = e && e.closest('.react-flow__node');
    return o ? o.getAttribute('data-id') : 'null'; })() : null;
  return { label: l.label, present: !!n, aria: n ? n.getAttribute('aria-label') : null,
    selected: n ? n.classList.contains('selected') : null, inView, centerOwner: owner,
    editable: document.querySelectorAll('[contenteditable="true"]').length,
    proseMirror: document.querySelectorAll('.ProseMirror').length,
    node: nb ? { w: Math.round(nb.width), h: Math.round(nb.height) } : null,
    menuOpen: !!document.querySelector('[data-testid="canvas-context-menu"]'),
    tids: { resize: cnt('text-node-resize-controls'), outline: cnt('text-node-selection-outline'),
      nodeToolbar: cnt('node-toolbar'), selToolbar: cnt('selection-context-toolbar'),
      selSurface: cnt('selection-context-toolbar-surface'), featureHost: cnt('node-toolbar-feature-host'),
      chromeHost: cnt('node-feature-chrome-host'), editorMenu: cnt('canvas-editor-menu') },
    geo: { resize: g('text-node-resize-controls'), outline: g('text-node-selection-outline'),
      corner: g('text-node-resize-top-left'), edgeTop: g('text-node-resize-top'), edgeLeft: g('text-node-resize-left'),
      affordance: g('textarea-resize-affordance'), selSurface: g('selection-context-toolbar-surface'),
      selToolbar: g('selection-context-toolbar'), nodeToolbar: g('node-toolbar'),
      editorMenu: g('canvas-editor-menu') } };
}, { label, id });

const cell = async (label, id) => { const c = await read(label, id); out.cells.push(c);
  log(`${label}: aria=${c.aria} sel=${c.selected} inView=${c.inView} owner=${c.centerOwner} ` +
      `ed=${c.editable}/${c.proseMirror} resize=${c.tids.resize} nt=${c.tids.nodeToolbar} node=${c.node?.w}×${c.node?.h}`); return c; };

// 落点：锁定 id，逐级放宽，并**回报归属**
const pointAt = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  for (const f of [0.5, 0.3, 0.7, 0.2, 0.8, 0.1, 0.9, 0.05, 0.95]) {
    const x = Math.round(r.x + r.width * f), y = Math.round(r.y + r.height * f);
    if (x < 2 || y < 2 || x > 1278 || y > 718) continue;
    const e = document.elementFromPoint(x, y);
    if (e && e.closest('.react-flow__node') === n) return { x, y };
  }
  return null;
}, id);

out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomPct() };
log('起点：', JSON.stringify(out.start));

// ============ 阶段 1：退到 40% + 适配全画布，让所有节点都点得到 ============
const setZoom = async (t0) => {
  for (let k = 1; k <= 3; k++) {
    if (await zoomPct() === t0) return true;
    await p.click('button[aria-label^="Zoom options"]');
    await p.waitForTimeout(800);
    if (!await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) {
      await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue;
    }
    await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
      i.dispatchEvent(new Event('input', { bubbles: true }));
      i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t0);
    await p.waitForTimeout(1600); await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  }
  return await zoomPct() === t0;
};
await setZoom(40);
await p.keyboard.press('Meta+0');   // 适配全画布：把基线 6 节点收进视口
await p.waitForTimeout(1800);
out.afterFit = { zoom: await zoomPct(), scale: (await scaleStable()).usable, nodes: await nodeN() };
log('适配后：', JSON.stringify(out.afterFit));

// ============ 阶段 2：锁定一个未选中的文本节点 ============
const cand = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-text'))
  .map((n) => ({ id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
    sel: n.classList.contains('selected'), w: Math.round(n.getBoundingClientRect().width) })));
out.allTextNodes = cand;
log('全部文本节点：', JSON.stringify(cand));

const TID = (cand.find((c) => !c.sel) || cand[0] || {}).id;
out.locked = TID;
log('锁定 id：', TID);
if (!TID) { log('🔴 一个文本节点都没有'); writeFileSync(new URL('./_tmp-b95h.json', import.meta.url), JSON.stringify(out, null, 1)); await b.close(); process.exit(1); }

// ============ 阶段 3：实验 A —— 单击 / 双击 / 批次93 的三击序列 ============
out.expA = {};
// A0 起点必须是「未选中 + 非编辑态 + 点得到」
let pt = await pointAt(TID);
let a0 = await cell('A0-起点', TID);
out.expA.A0_pt = pt;
if (a0.editable !== 0 || a0.selected !== false || !pt) { out.expA.A0_precond = '不满足 ⇒ A 组 VOID'; log('⚠️ A0 前置不满足，A 组记 VOID'); }
else {
  // A1：单击
  await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(250);
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1300);
  const a1 = await cell('A1-单击', TID); out.expA.singleClickEntersEdit = a1.editable > 0;

  // A2/A3：Esc 到底回未选中
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  const a2 = await cell('A2-Esc到底', TID);

  // A3：纯双击（无前置单击）
  if (a2.selected === false && a2.editable === 0 && pt) {
    await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(250);
    await p.mouse.dblclick(pt.x, pt.y); await p.waitForTimeout(1600);
    const a3 = await cell('A3-纯双击', TID); out.expA.dblclickEntersEdit = a3.editable > 0;
  } else out.expA.A3_precond = '不满足 ⇒ VOID';

  // A4/A5：Esc 逐步回退
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  await cell('A4-Esc一次', TID);
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  const a5 = await cell('A5-Esc两次', TID);

  // A6：复现批次 93 的错误序列 —— 单击后「立即」双击（三击）
  if (a5.selected === false && a5.editable === 0) {
    await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(120);
    await p.mouse.click(pt.x, pt.y);
    await p.waitForTimeout(120);                      // 🔴 只有 120ms，接着就双击
    await p.mouse.dblclick(pt.x, pt.y);
    await p.waitForTimeout(1600);
    const a6 = await cell('A6-单击后120ms双击(批次93序列)', TID);
    out.expA.batch93SequenceEntersEdit = a6.editable > 0;
  } else out.expA.A6_precond = '不满足 ⇒ VOID';
}
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }

// ============ 阶段 4：锁 id 三档缩放 —— 同一节点，读「屏上恒定 vs 随缩放」============
for (const z of [40, 60, 100]) {
  const ok = await setZoom(z);
  const sc = await scaleStable();
  const st = await read(`Z${z}%-读数`, TID);
  // 前置：不满足就 VOID
  let measured = null; let why = '';
  if (!st.present) { why = '节点不在 DOM'; }
  else if (!st.inView) { why = '节点不在视口内'; }
  else {
    pt = await pointAt(TID);
    if (!pt) why = '点不到（被完全盖住）';
    else {
      await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1300);
      const sel = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
        return n ? n.classList.contains('selected') : null; }, TID);
      const s2 = await read(`Z${z}%-选中后`, TID);
      if (sel !== true) why = `单击后 selected=${sel}`;
      else if (s2.editable > 0) why = '单击后进了编辑态（前置被破坏）';
      else if (!s2.tids.resize) why = 'resize 控件没出现';
      else measured = s2;
    }
  }
  out.zooms.push({ z, ok, scale: sc, lockedId: TID, aria: st.aria, why: why || null, measured });
  if (measured) {
    const m = measured;
    log(`z=${z}% scale=${sc.usable}(stable=${sc.stable}) node=${m.node.w}×${m.node.h} corner=${m.geo.corner?.w}×${m.geo.corner?.h} ` +
        `edgeTop=${m.geo.edgeTop?.w}×${m.geo.edgeTop?.h} outline=${m.geo.outline?.w}×${m.geo.outline?.h} ` +
        `surface=${m.geo.selSurface?.w}×${m.geo.selSurface?.h} content=${m.geo.selToolbar?.w}×${m.geo.selToolbar?.h} ` +
        `affordance=${m.geo.affordance?.w}×${m.geo.affordance?.h}`);
  } else log(`z=${z}% scale=${sc.usable} ⇒ VOID：${why}`);
  for (let k = 0; k < 2; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
}

await setZoom(60);
await p.keyboard.press('Meta+0'); await p.waitForTimeout(1500);
if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
out.end = { nodes: await nodeN(), sel: await selN(), zoom: await zoomPct(), credits: await credits(), scale: (await scaleStable()).usable };
log('终态：', JSON.stringify(out.end), '｜缩放归位', (await zoomPct()) === 60 ? '✅' : '🔴');
writeFileSync(new URL('./_tmp-b95h.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
