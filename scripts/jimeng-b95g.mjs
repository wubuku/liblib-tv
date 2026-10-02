// 批次 95 · 受控复测：**「双击文本节点是否进编辑态」**，以及文本节点 resize 控件是否随缩放变。
//
// 🔴 要推翻的是批次 93 自己写下的结论：「空文本节点双击后 `contenteditable`/`.ProseMirror` 恒 0」。
//     批次 93 当时的动作序列是「**先单击选中** → **立即双击**」= **三击**。
//     而 b95e 四格对照已经证明：**单击一个已选中的文本节点就会进编辑态**（`editable` 0→1）。
//     ⇒ 批次 93 那次很可能**测的就是编辑态**，只是把「双击」当成了变量，实际变量是「第三次点击」。
//     ⇒ 这一轮的关键纪律：**双击就只发双击，任何前置单击都不许有**（用 `mouse.dblclick`，不用 click+click）。
//
// 第二件事：b95e 量到文本节点选中态有 **8 向 resize 控件**（角 24×24 / 边 178×10、10×178）与
// `text-node-selection-outline` 200×200。批次 93 已钉过工具条按钮是「**屏上恒定**」，
//     这批控件是恒定还是随缩放，**换个缩放档一量就知道** —— 顺便验证批次 93 的除法纪律。
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
// 缩放**连读两次**相同才算静止 —— 绝不写死 0.6（批次 93 教训）
const scaleStable = async () => { const a = await scaleNow(); await p.waitForTimeout(400); const c = await scaleNow();
  return { a, c, stable: a !== null && a === c, usable: a }; };

// 找一个**未选中、且在视口内点得到**的文本节点
const findTextNode = () => p.evaluate(() => {
  for (const n of document.querySelectorAll('.react-flow__node-text')) {
    if (n.classList.contains('selected')) continue;
    const r = n.getBoundingClientRect();
    for (let fx = 0.1; fx <= 0.9; fx += 0.1) for (let fy = 0.1; fy <= 0.9; fy += 0.1) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      if (x < 4 || y < 4 || x > 1276 || y > 716) continue;
      if (document.elementFromPoint(x, y)?.closest('.react-flow__node') === n)
        return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'), pt: { x, y },
          rect: { w: Math.round(r.width), h: Math.round(r.height) } };
    }
  }
  return null;
});

const read = (label, id) => p.evaluate((l) => {
  const n = l.id ? document.querySelector(`.react-flow__node[data-id="${l.id}"]`) : null;
  const cnt = (t) => document.querySelectorAll(`[data-testid="${t}"]`).length;
  const geo = (t) => { const e = document.querySelector(`[data-testid="${t}"]`); if (!e) return null;
    const r = e.getBoundingClientRect();
    return { w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y) }; };
  return { label: l.label, present: !!n, selected: n ? n.classList.contains('selected') : null,
    editable: document.querySelectorAll('[contenteditable="true"]').length,
    proseMirror: document.querySelectorAll('.ProseMirror').length,
    menuOpen: !!document.querySelector('[data-testid="canvas-context-menu"]'),
    tids: { resize: cnt('text-node-resize-controls'), outline: cnt('text-node-selection-outline'),
      nodeToolbar: cnt('node-toolbar'), selToolbar: cnt('selection-context-toolbar'),
      selSurface: cnt('selection-context-toolbar-surface'), featureHost: cnt('node-toolbar-feature-host'),
      chromeHost: cnt('node-feature-chrome-host'), editorMenu: cnt('canvas-editor-menu') },
    geo: { resize: geo('text-node-resize-controls'), outline: geo('text-node-selection-outline'),
      corner: geo('text-node-resize-top-left'), edgeTop: geo('text-node-resize-top'), edgeLeft: geo('text-node-resize-left'),
      affordance: geo('textarea-resize-affordance'), selSurface: geo('selection-context-toolbar-surface'),
      selToolbar: geo('selection-context-toolbar'), nodeToolbar: geo('node-toolbar'),
      editorMenu: geo('canvas-editor-menu') } };
}, { label, id });

const cell = async (label, id) => { const c = await read(label, id); out.cells.push(c);
  log(`${label}: sel=${c.selected} editable=${c.editable}/${c.proseMirror} resize=${c.tids.resize} nt=${c.tids.nodeToolbar} em=${c.tids.editorMenu}`); return c; };

out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomPct() };
log('起点：', JSON.stringify(out.start));

// ---- 主实验：双击（不带任何前置单击）----
const t = await findTextNode();
out.target = t;
log('文本节点：', JSON.stringify(t));
if (t) {
  // 确认起点确实是「未选中、非编辑态」
  await cell('g0-双击前(未选中)', t.id);

  await p.mouse.move(t.pt.x, t.pt.y);
  await p.waitForTimeout(300);
  await p.mouse.dblclick(t.pt.x, t.pt.y);   // 🔴 只有双击，没有前置单击
  await p.waitForTimeout(1500);
  const c1 = await cell('g1-双击后', t.id);
  out.dblclickEnteredEdit = c1.editable > 0;

  // 再测一格：编辑态下 Esc 一次 ⇒ 回哪一态？
  await p.keyboard.press('Escape');
  await p.waitForTimeout(900);
  const c2 = await cell('g2-编辑态Esc一次', t.id);

  // 回到未选中，再测「单击已选中」是否也进编辑态（复核 b95e 的发现）
  if (c2.editable === 0) {
    await p.keyboard.press('Escape');
    await p.waitForTimeout(800);
    await cell('g3-再Esc一次(应未选中)', t.id);
    await p.mouse.click(t.pt.x, t.pt.y);
    await p.waitForTimeout(1200);
    const c4 = await cell('g4-未选中单击(应选中态)', t.id);
    await p.mouse.click(t.pt.x, t.pt.y);
    await p.waitForTimeout(1200);
    const c5 = await cell('g5-已选中单击(应编辑态)', t.id);
    out.clickSelectedEnteredEdit = c5.editable > 0;
    out.c4 = c4; out.c5 = c5;
  }
  await p.keyboard.press('Escape');
  await p.waitForTimeout(800);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(800);
}

// ---- 缩放三档：量 resize 角/边控件是「屏上恒定」还是「随缩放」----
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

for (const z of [40, 60, 100]) {
  const ok = await setZoom(z);
  const sc = await scaleStable();
  // 每档都要有一个**处于选中态**的文本节点才量得到 resize 控件
  let probe = null;
  for (let tries = 0; tries < 3 && !probe; tries++) {
    const cand = await findTextNode();
    if (cand) {
      await p.mouse.click(cand.pt.x, cand.pt.y);
      await p.waitForTimeout(1200);
      const s = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
        return n ? n.classList.contains('selected') : null; }, cand.id);
      if (s === true) probe = cand;
      else { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
    } else { await p.keyboard.press('Meta+0'); await p.waitForTimeout(1700); }
  }
  if (!probe) { out.zooms.push({ z, ok, sc, probe: null }); log(`z=${z}% 找不到可点中的未选中文本节点 ⇒ VOID`); continue; }
  const r = await p.evaluate((id) => {
    const g = (t) => { const e = document.querySelector(`[data-testid="${t}"]`); if (!e) return null;
      const b = e.getBoundingClientRect(); return { w: Math.round(b.width), h: Math.round(b.height) }; };
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    const nb = n.getBoundingClientRect();
    return { selected: n.classList.contains('selected'), editable: document.querySelectorAll('[contenteditable="true"]').length,
      node: { w: Math.round(nb.width), h: Math.round(nb.height) },
      corner: g('text-node-resize-top-left'), edgeTop: g('text-node-resize-top'), edgeLeft: g('text-node-resize-left'),
      controls: g('text-node-resize-controls'), outline: g('text-node-selection-outline'),
      affordance: g('textarea-resize-affordance'),
      selSurface: g('selection-context-toolbar-surface'), selToolbar: g('selection-context-toolbar'),
      nodeToolbar: g('node-toolbar'), editorMenu: g('canvas-editor-menu') };
  }, probe.id);
  // **前置条件断言**：不满足就记 VOID，不硬写读数
  const valid = r.selected === true && r.editable === 0 && r.corner !== null;
  out.zooms.push({ z, ok, sc, valid, r });
  log(`z=${z}% scale=${sc.usable}(stable=${sc.stable}) sel=${r.selected} ed=${r.editable} valid=${valid} ` +
      `node=${r.node.w}×${r.node.h} corner=${r.corner?.w}×${r.corner?.h} edgeTop=${r.edgeTop?.w}×${r.edgeTop?.h} ` +
      `outline=${r.outline?.w}×${r.outline?.h} surface=${r.selSurface?.w}×${r.selSurface?.h} content=${r.selToolbar?.w}×${r.selToolbar?.h}`);
  await p.keyboard.press('Escape');
  await p.waitForTimeout(800);
}

await setZoom(60);
if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
out.end = { nodes: await nodeN(), sel: await selN(), zoom: await zoomPct(), credits: await credits(), scale: (await scaleStable()).usable };
log('终态：', JSON.stringify(out.end), '｜缩放归位', (await zoomPct()) === 60 ? '✅' : '🔴');
writeFileSync(new URL('./_tmp-b95g.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
