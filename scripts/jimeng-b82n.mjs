// 批次 82 · N：回答最后一问 —— m 轮按 F 之后 `vis 844→881`（+37 个可见元素），
// 但 `[text-editor-fullscreen-dialog]` 仍然是 null。**那 37 个元素是什么？**
//
// 页面第 179 行写「容器 `div[text-editor-fullscreen-dialog]` **1280×720@0,0**」。
// 我的选择器是 `document.querySelector('[text-editor-fullscreen-dialog]')`，
// 语法上等价。⇒ 两种可能：
//   (a) F 打开的**不是**页面记的那个容器（页面记录有误，或 F 的结果变了）；
//   (b) F 打开的容器**属性名不是** `text-editor-fullscreen-dialog`。
//
// 🔑 这一轮**不猜**：按 F 前后各取一份「有面积元素」的完整快照
//    （testid / 各种 attr / tag / class / 尺寸 / 文本摘要），
//    再算**差集**，把新增的东西逐条打出来。差集自带答案。
//
// 顺带钉一个新契约：m 轮日志里出现了
//   `DIV[rf__node-node_a0zads9g8h] aria="文本 node: 文本 4"`
//   ⇒ 节点 wrapper 的 **aria-label 格式是 `<类型> node: <标题>`**。
//   这是按节点定位的又一把钥匙，本轮顺带全量取一遍。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard, pressLetter } from './jimeng-safe-keys.mjs';
const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const mine = [];
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const selCount = () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const zoomLabel = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const zoomPct = async () => { const l = await zoomLabel(); return l ? Number((l.match(/(\d+)%/) || [])[1]) : null; };
const toast = () => p.evaluate(() => { const c = Array.from(document.querySelectorAll('div,span'))
    .filter((x) => /此快捷键当前不可用/.test((x.innerText || '').trim()) && x.children.length <= 2);
  const e = c.sort((a, b2) => b2.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
  if (!e) return null; const r = e.getBoundingClientRect();
  return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, text: (e.innerText || '').trim() }; });
const agentState = () => p.evaluate(() => { const els = Array.from(document.querySelectorAll('[data-testid^="canvas-agent-"]'));
  return { withArea: els.filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; }).length,
    pmAnywhere: document.querySelectorAll('.ProseMirror[contenteditable="true"]').length }; });
const setZoom = async (t0) => { for (let t = 1; t <= 3; t++) { if (await zoomPct() === t0) return { ok: true, how: 'already' };
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
    if (!await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
    await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
      i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t0);
    await p.waitForTimeout(1300); await p.keyboard.press('Escape'); await p.waitForTimeout(600);
    const a = await zoomPct(); await p.waitForTimeout(900); const c = await zoomPct();
    if (a === c && a === t0) return { ok: true, how: 'input', pct: a }; }
  return { ok: false, pct: await zoomPct() }; };
const clickPane = async () => { const e = await p.evaluate(() => { const pane = document.querySelector('.react-flow__pane'); if (!pane) return null;
    for (let y = 110; y < 660; y += 20) for (let x = 210; x < 1240; x += 28) { const h = document.elementFromPoint(x, y); if (h && pane.contains(h)) return { x, y }; }
    return null; });
  if (!e) return null; await p.mouse.click(e.x, e.y); await p.waitForTimeout(650); return e; };

/** 🔑 可见元素快照：给差集用。每项带足够多的定位线索。 */
const snap = () => p.evaluate(() => {
  const AT = ['data-testid','data-state','data-slot','role','aria-label','aria-modal','data-radix-popper-content-wrapper','data-side','data-align'];
  const out = [];
  for (const e of document.querySelectorAll('*')) {
    const r = e.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    const rec = { tag: e.tagName, cls: String(e.className || '').split(' ').filter(Boolean).slice(0, 2).join('.'),
      w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y) };
    for (const a of AT) { const v = e.getAttribute(a); if (v) { rec[a] = v.slice(0, 46); break; } }
    const t = (e.innerText || '').trim().split('\n')[0];
    if (t && t.length <= 22) rec.t = t;
    // 键：结构性签名，用来判「是不是同一个东西」
    rec.k = `${rec.tag}|${rec.cls}|${rec.w}x${rec.h}|${rec['data-testid'] || rec['aria-label'] || rec.role || ''}|${rec.t || ''}`;
    out.push(rec);
  } return out;
});
const diff = (A, B) => { const m = new Map(); for (const r of A) m.set(r.k, r);
  const add = B.filter((r) => !m.has(r.k)); const m2 = new Map(B.map((r) => [r.k, r]));
  return { added: add, removed: A.filter((r) => !m2.has(r.k)) }; };

try {
  out.zoom = await setZoom(60); log('缩放', JSON.stringify(out.zoom));
  const ab = await agentState();
  if (ab.withArea > 5) { await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1400); }

  // 节点 wrapper 的 aria-label 格式（m 轮顺带发现，全量取一遍）
  out.nodeAria = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const w = n.parentElement; const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), aria: w ? w.getAttribute('aria-label') : null,
      box: `${Math.round(r.width)}x${Math.round(r.height)}`, kind: n.className.split(' ').find((c) => /-node-/.test(c)) || null };
  }));
  log('节点 wrapper aria（前 6 条）');
  out.nodeAria.slice(0, 6).forEach((n) => log('   ', n.id, '|', n.aria, '|', n.box, '|', n.kind));

  const pre0 = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3400);
  const made = (await ids()).filter((x) => !pre0.includes(x));
  log('新建', made.length, made.join(' '));
  if (made.length < 1) throw new Error('新建失败');
  mine.push(...made);
  const one = made[0];

  // 单选：框选罩一片 → Shift toggle 掉其中一个
  await clickPane();
  const geo = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height }; }, one);
  const pad = 40, x0 = Math.round(geo.x - pad), y0 = Math.round(geo.y - pad), x1 = Math.round(geo.x + geo.w + pad), y1 = Math.round(geo.y + geo.h + pad);
  if (await p.evaluate(([x, y]) => { const pane = document.querySelector('.react-flow__pane'); const h = document.elementFromPoint(x, y); return !!(pane && h && pane.contains(h)); }, [x0, y0])) {
    await p.mouse.move(x0, y0); await p.mouse.down();
    for (let k = 1; k <= 6; k++) { await p.mouse.move(Math.round(x0 + (x1 - x0) * k / 6), Math.round(y0 + (y1 - y0) * k / 6)); await p.waitForTimeout(70); }
    await p.mouse.up(); await p.waitForTimeout(900);
  }
  const title = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect();
    for (let k = -70; k <= 4; k += 3) for (const f of [0.25, 0.5, 0.75]) { const x = Math.round(r.x + r.width * f), y = Math.round(r.y + Math.round(k * 0.6));
      if (x < 0 || y < 0 || y > 716) continue; const h = document.elementFromPoint(x, y);
      if (h && n.contains(h) && (h.innerText || h.getAttribute('aria-label'))) return { x, y }; }
    return null; }, one);
  if (title) { await p.keyboard.down('Shift'); await p.mouse.click(title.x, title.y); await p.keyboard.up('Shift'); await p.waitForTimeout(1000); }
  out.pre = { sel: await selCount(), focusWhere: (await keyGuard(p)).where, title };
  log('单选前置', JSON.stringify(out.pre));

  // 前后快照 + 差集
  await p.waitForTimeout(600);
  const A = await snap();
  const g = await keyGuard(p); out.guardSafe = g.safe;
  if (g.safe) await pressLetter(p, 'f'); else out.void = 'keyGuard 拒绝';
  for (const d of [500, 1000, 1800]) await p.waitForTimeout(d);
  out.toast = await toast();
  const B = await snap();
  const D = diff(A, B);
  out.added = D.added; out.removedCount = D.removed.length;
  log(`按 F：新增 ${D.added.length} 个有面积元素，消失 ${D.removed.length} 个`);
  log('新增逐条：');
  D.added.forEach((r, i) => log(`  +${i}`, JSON.stringify(r)));
  log('全屏编辑器命中：', await p.evaluate(() => {
    const sels = ['[text-editor-fullscreen-dialog]','[data-testid="text-editor-fullscreen-dialog"]',
      '.text-editor-fullscreen-dialog','[class*="fullscreen"]','[class*="full-screen"]','[role="dialog"]'];
    return sels.map((s) => { try { const e = document.querySelector(s); if (!e) return `${s} → 无`;
      const r = e.getBoundingClientRect(); return `${s} → ${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; }
      catch (e) { return `${s} → 语法错`; } }); }));
  out.bigOverlays = B.filter((r) => r.w >= 600 && r.h >= 400).slice(0, 14);
  log('≥600×400 的元素：');
  out.bigOverlays.forEach((r) => log('   ', JSON.stringify(r)));
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  for (let i = 0; i < 2; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  out.zoomFinal = await setZoom(60);
  out.end = { status: await status(), zoom: await zoomLabel(), agent: await agentState(), leftover: (await ids()).filter((x) => mine.includes(x)) };
  log('终态', JSON.stringify(out.end));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8'));
    const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort();
      led.per_batch = { ...(led.per_batch || {}), 82: [...new Set([...(led.per_batch?.['82'] || []), ...mine])] };
      writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b82n.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
