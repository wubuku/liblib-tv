// 批次 78 · I：钉死「新建节点 ⇒ 缩放变小」这条的边界。
// b78h 已确认：新建（自动选中）后 scale 0.6 → 0.568085，**标签同步变成 57%**。
// 还剩四个问题，一次答完：
//   a) 是固定**相对**降幅吗？（100% 建节点后是否落到 ~94.7%）
//   b) 再建第二个节点还会再降吗，还是降一次就停？
//   c) 换类型（文本）也一样吗？
//   d) 取消选中会还原吗？（b78h 看到「不还原」，但那次我同时手动设了 100%，有混淆）
// 只读观察 + 只动视图缩放与新建临时节点，量完删干净、缩放归位 60%。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const mine = [];
const read = (lb) => p.evaluate((l) => {
  const vw = document.querySelector('.react-flow__viewport');
  const m = /matrix\(([-\d.]+)/.exec(getComputedStyle(vw).transform);
  const n0 = document.querySelector('.react-flow__node.selected');
  return { lb: l, label: (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'),
    scale: m ? +(+m[1]).toFixed(6) : null,
    counterVar: n0 ? getComputedStyle(n0).getPropertyValue('--octo-canvas-node-chrome-counter-scale').trim() : null,
    selectedId: n0 ? n0.getAttribute('data-id') : null,
    status: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected/) || ['?'])[0] };
}, lb);
const setZoom = async (pct) => { await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
  const sl = 'input[data-testid=canvas-zoom-percent-input]';
  if (!(await p.$(sl))) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); return; }
  await p.fill(sl, String(pct)); await p.keyboard.press('Enter'); await p.waitForTimeout(1500); };
const mk = async (label) => {
  const pre = await ids();
  const rail = await p.evaluate((L) => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => new RegExp('^' + L + '$').test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }, label);
  if (!rail) { log('找不到 rail 按钮', label); return null; }
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3000);
  const c = (await ids()).filter((x) => !pre.includes(x));
  if (c.length !== 1) { log('新建异常', label, JSON.stringify(c)); return null; }
  mine.push(c[0]); return c[0];
};
try {
  out.s0 = await read('开场'); log('开场', JSON.stringify(out.s0));
  await setZoom(100); out.s100 = await read('设为 100%'); log('100%', JSON.stringify(out.s100));
  const v1 = await mk('视频'); out.a_videoAt100 = await read('100% 下建视频节点'); log('a', JSON.stringify(out.a_videoAt100));
  if (v1 && out.s100.scale) out.relA = +((out.a_videoAt100.scale / out.s100.scale)).toFixed(6);
  const v2 = await mk('视频'); out.b_second = await read('再建一个视频节点'); log('b', JSON.stringify(out.b_second));
  await p.keyboard.press('Escape'); await p.waitForTimeout(1500); out.d_deselect = await read('Escape 取消选中'); log('d', JSON.stringify(out.d_deselect));
  const t1 = await mk('文本'); out.c_text = await read('再建文本节点'); log('c', JSON.stringify(out.c_text));
  if (t1 && out.d_deselect.scale) out.relC = +((out.c_text.scale / out.d_deselect.scale)).toFixed(6);
  out.summary = { relA: out.relA, relC: out.relC, afterDeselectEqualsBefore: out.d_deselect.scale === out.a_videoAt100.scale };
  log('小结', JSON.stringify(out.summary));
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  for (let i = 0; i < 2; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  for (const id of mine) {
    const box = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null; const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }, id);
    if (!box) continue;
    await p.mouse.click(box.x, box.y, { button: 'right' }); await p.waitForTimeout(1000);
    await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
      const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
    await p.waitForTimeout(1500);
    log('清理', id, (await ids()).includes(id) ? '🔴 仍在' : '✅');
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  for (let t = 0; t < 3; t++) { const z = await p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
    if (z && z.includes('60%')) break; await setZoom(60); }
  const f = await read('终态'); out.final = f; log('终态', JSON.stringify(f));
  const cp = await p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
    const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
    return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null]; })));
  const dev = []; for (const [id, b2] of Object.entries(BASE.nodes)) { const c = cp[id]; const d = c && b2.canvas ? [Math.round((c[0] - b2.canvas[0]) * 100) / 100, Math.round((c[1] - b2.canvas[1]) * 100) / 100] : 'MISSING';
    if (d === 'MISSING' || (Array.isArray(d) && (Math.abs(d[0]) > 0.01 || Math.abs(d[1]) > 0.01))) dev.push([id, d]); }
  out.deviation = dev; log('基线偏离', JSON.stringify(dev));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8')); const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort(); writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b78i.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
