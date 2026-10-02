// 批次 78 · H：查清 0.568085 是什么。
// 现象（b78e / b78g 两次独立复现，6 位全同）：新建节点并**保持选中**时，
//   `.react-flow__viewport` 的 computed matrix scale = 0.568085，而缩放标签仍写「60%」。
//   删掉节点 / 取消选中后回到 matrix(0.6)。
// 关键：0.568085 / 0.6 = 0.946808。若成立，则手册里所有**在选中态量到的尺寸**
//   （节点面、⊕ 手柄热区等）都系统性偏小 5.3% ⇒ 必须重算。
// 三个候选解释，一次分开：
//   A 选中即生效        → 新建后不拖，直接读
//   B 拖拽才触发        → 对照 A，若 A 已是 0.568 则 A 成立
//   C 缩放档位整体错位  → 选中态下再设 50% / 100%，看比例是否恒为 ×0.946808
// 另测：悬停（未选中）是否也变 —— 若悬停也变，那是 hover chrome 留位，不是「选中」。
// 只读观察 + 只动视图缩放，量完归位 60%、删掉自建节点。
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
const out = { at: new Date().toISOString(), ratio: {} };
let mine = null;
const snap = (label, id) => p.evaluate(([v, lb]) => {
  const vw = document.querySelector('.react-flow__viewport');
  const m = /matrix\(([-\d.]+)/.exec(getComputedStyle(vw).transform);
  const s = m ? +(+m[1]).toFixed(6) : null;
  const btn = document.querySelector('button[aria-label^="Zoom options"]');
  const n = v ? document.querySelector(`.react-flow__node[data-id="${v}"]`) : null;
  const r = n ? n.getBoundingClientRect() : null;
  const t = n ? /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '') : null;
  return { lb, label: btn ? btn.getAttribute('aria-label') : null, scale: s,
    selected: n ? /(^|\s)selected(\s|$)/.test(n.className) : null,
    inline: vw.style.transform,
    nodeCanvas: t ? [+t[1], +t[2]] : null,
    nodeScreen: r ? [Math.round(r.width * 100) / 100, Math.round(r.height * 100) / 100] : null,
    cssVar: (() => { const cs = getComputedStyle(document.documentElement);
      return { counter: cs.getPropertyValue('--octo-canvas-node-chrome-counter-scale').trim() || null,
        nodeCounter: n ? getComputedStyle(n).getPropertyValue('--octo-canvas-node-chrome-counter-scale').trim() || null : null }; })() };
}, [id, label]);
const setZoom = async (pct) => {
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
  const sl = 'input[data-testid=canvas-zoom-percent-input]';
  if (!(await p.$(sl))) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); return null; }
  await p.fill(sl, String(pct)); await p.keyboard.press('Enter'); await p.waitForTimeout(1400); return null;
};
try {
  out.idle0 = await snap('开场(未选中)');
  log('开场', JSON.stringify(out.idle0));
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^视频$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3000);
  const created = (await ids()).filter((x) => !pre.includes(x));
  if (created.length !== 1) throw new Error('新建异常');
  mine = created[0];
  // A：新建完**不拖**，直接读（新建即自动选中）
  out.A_selectedNoDrag = await snap('A 选中未拖', mine);
  log('A 选中未拖', JSON.stringify(out.A_selectedNoDrag));
  // 悬停另一个节点（不选中它）—— 鼠标移过去，shift 不按
  const other = await p.evaluate((v) => { const n = Array.from(document.querySelectorAll('.react-flow__node'))
    .filter((x) => x.getAttribute('data-id') !== v)
    .map((x) => { const r = x.getBoundingClientRect(); return { id: x.getAttribute('data-id'), x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), on: r.x > 0 && r.right < innerWidth && r.y > 0 && r.bottom < innerHeight }; })
    .filter((o) => o.on)[0]; return n || null; }, mine);
  if (other) { await p.mouse.move(other.x, other.y); await p.waitForTimeout(1500);
    out.hover = await snap('悬停他人节点(本节点仍选中)', mine); log('悬停', JSON.stringify(out.hover)); }
  // C：选中态下换档位，看比例
  out.C50 = (await setZoom(50), await snap('C 选中 50%', mine)); log('C50', JSON.stringify(out.C50));
  out.C100 = (await setZoom(100), await snap('C 选中 100%', mine)); log('C100', JSON.stringify(out.C100));
  // 取消选中后再读：比例是否回到 1（若是 ⇒ 与选中强相关）
  await p.mouse.click(640, 40); await p.waitForTimeout(1600);   // 点顶部空白 toolbar 区
  const sel0 = await p.evaluate((v) => /(^|\s)selected(\s|$)/.test(document.querySelector(`.react-flow__node[data-id="${v}"]`).className), mine);
  out.deselect = { stillSelected: sel0, ...(await snap('取消选中后', mine)) };
  log('取消选中', JSON.stringify(out.deselect));
  for (const k of ['A_selectedNoDrag', 'C50', 'C100']) if (out[k] && out[k].scale) out.ratio[k] = +(out[k].scale / (+String(out[k].label).match(/(\d+)%/)[1]) / 100).toFixed(6);
  log('比例 scale/(pct/100)', JSON.stringify(out.ratio));
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  for (let i = 0; i < 2; i++) await p.keyboard.press('Escape'); await p.waitForTimeout(600);
  for (let t = 0; t < 3; t++) { const z = await p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
    if (z && z.includes('60%')) break; await setZoom(60); }
  if (mine) {
    const box = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null; const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height * 0.5) }; }, mine);
    if (box) { await p.mouse.click(box.x, box.y, { button: 'right' }); await p.waitForTimeout(1000);
      await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
        const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
      await p.waitForTimeout(1500); }
    log('清理', mine, (await ids()).includes(mine) ? '🔴 仍在' : '✅');
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(500);
  out.finalScale = await p.evaluate(() => { const m = /matrix\(([-\d.]+)/.exec(getComputedStyle(document.querySelector('.react-flow__viewport')).transform); return m ? +(+m[1]).toFixed(6) : null; });
  out.finalZoomLabel = await p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
  log('终态 scale', out.finalScale, '| 标签', out.finalZoomLabel);
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8')); if (mine && !led.ids.includes(mine)) { led.ids = [...new Set([...led.ids, mine])].sort(); writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b78h.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
