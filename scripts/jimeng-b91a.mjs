// 批次 91 · A：审计 `10-tasks/connect-nodes.md`（普查停在 **78**，528 行，全册最陈旧的大页）。
//
// 🔑 **手上现成的弹药**（批次 89 顺带撞到、当时没追）：
//     `flow-node-target-handle` 命中 **20** 个（= 全部节点），
//     `flow-node-source-handle` 只命中 **19** 个
//     ⇒ **有一个节点没有出边手柄**，而本页通篇按「每个节点左右各一个手柄」写。
//     ⇒ **P1a**：是哪一个节点？它的类型有什么特别？
//
// 🔑 本页第 512 行自认「手柄 43×87 是在 72% 缩放量得的，**不是稳定契约**」，
//     而批次 78/85/88 三次独立确认 **canvas 恒 `60×120`**。
//     交叉验算：`60×0.72 = 43.2`、`120×0.72 = 86.4 ≈ 87` ✅ —— 两边自洽。
//     ⇒ **P1b**：在 40/60/100% 三档实测屏上热区，反推 canvas 是不是恒 `60×120`。
//
// ⛔ 本轮**只读**：不建连线（那会新增 edge）、不删任何东西、不碰他人节点。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const selCount = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const zoomPct = async () => p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]'); return e ? Number((e.getAttribute('aria-label').match(/(\d+)%/) || [])[1]) : null; });
const readScale = async () => { const rd = () => p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
    const m = (vp ? (vp.style.transform || '') : '').match(/scale\(([-\d.]+)\)/); return m ? Number(m[1]) : null; });
  const a = await rd(); await p.waitForTimeout(500); const c = await rd(); return { scale: a, stable: a !== null && a === c }; };
const status = async () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);

out.start = { status: await status(), sel: await selCount(), credits: await credits(), zoom: await zoomPct() };
log('起点：', JSON.stringify(out.start));

// ── P1a：逐节点查 source / target 手柄 ──
log('\n══ P1a：逐节点的手柄清点');
out.handles = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id'), aria: (n.getAttribute('aria-label') || '').slice(0, 26),
    typeCls: (String(n.className || '').match(/react-flow__node-([a-z]+)/) || [])[1] || '?',
    nodeScreen: `${Math.round(r.width)}×${Math.round(r.height)}`,
    source: n.querySelectorAll('[data-testid="flow-node-source-handle"]').length,
    target: n.querySelectorAll('[data-testid="flow-node-target-handle"]').length,
    plus: n.querySelectorAll('[data-testid$="connection-menu-button"]').length };
}));
const noSrc = out.handles.filter((h) => h.source === 0);
const noTgt = out.handles.filter((h) => h.target === 0);
log(`  节点 ${out.handles.length} 个｜source=${out.handles.reduce((a, h) => a + h.source, 0)} ｜target=${out.handles.reduce((a, h) => a + h.target, 0)}`);
log(`  🔴 没有 source 手柄的：${noSrc.length ? noSrc.map((h) => `${h.aria}[${h.typeCls}]`).join('、') : '（无）'}`);
log(`  🔴 没有 target 手柄的：${noTgt.length ? noTgt.map((h) => `${h.aria}[${h.typeCls}]`).join('、') : '（无）'}`);
const byType = {};
for (const h of out.handles) { const k = h.typeCls; byType[k] = byType[k] || { n: 0, src: 0, tgt: 0 };
  byType[k].n++; byType[k].src += h.source; byType[k].tgt += h.target; }
out.byType = byType;
log('  按类型：' + JSON.stringify(byType));

// ── 现存连线 ──
out.edges = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__edge')).map((e) => {
  const pth = e.querySelector('path'); const r = (pth || e).getBoundingClientRect();
  return { id: e.getAttribute('data-id'), aria: e.getAttribute('aria-label'), cls: String(e.className || '').slice(0, 40),
    d: pth ? (pth.getAttribute('d') || '').slice(0, 40) : null, box: `${Math.round(r.width)}×${Math.round(r.height)}` };
}));
log(`\n══ 现存连线 ${out.edges.length} 条` + (out.edges.length ? '' : '（画布当前 0 edge）'));
for (const e of out.edges.slice(0, 6)) log('   ', JSON.stringify(e));

// ── P1b：三档缩放实测手柄热区 ──
const setZoom = async (t0) => { for (let t = 1; t <= 3; t++) { if (await zoomPct() === t0) return true;
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
    const has = await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'));
    if (!has) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
    await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
      i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t0);
    await p.waitForTimeout(1300); await p.keyboard.press('Escape'); await p.waitForTimeout(700);
    if (await zoomPct() === t0) return true; }
  return false; };

log('\n══ P1b：三档缩放 × 手柄热区（反推 canvas 值）');
out.grids = [];
for (const z of [100, 40, 60]) {
  const ok = await setZoom(z);
  const sc = await readScale();
  // 手柄在未选中时是存在的（批次 78/88 已证），只读尺寸
  const hs = await p.evaluate(() => { const seen = new Map();
    for (const e of document.querySelectorAll('[data-testid$="-handle"]')) { const r = e.getBoundingClientRect();
      const k = e.getAttribute('data-testid').includes('source') ? 'source' : 'target';
      const box = `${Math.round(r.width)}×${Math.round(r.height)}`;
      if (!seen.has(k + '|' + box)) seen.set(k + '|' + box, { kind: k, box, n: 0, cls: String(e.className || '').slice(0, 60) });
      seen.get(k + '|' + box).n++; }
    return [...seen.values()]; });
  const row = { zoom: z, ok, scale: sc.scale, stable: sc.stable, handles: hs };
  row.derived = hs.map((h) => { const [w, hh] = h.box.split('×').map(Number);
    return sc.scale ? { kind: h.kind, screen: h.box, canvas: `${Math.round(w / sc.scale)}×${Math.round(hh / sc.scale)}`, n: h.n } : null; });
  out.grids.push(row);
  log(`  ${z}%  scale=${sc.scale} 稳定=${sc.stable}｜屏上 ${JSON.stringify(hs.map((h) => h.box))}｜反推 canvas ${JSON.stringify(row.derived.map((d) => d && d.canvas))}`);
}
out.p1b = { verdict: out.grids.every((g) => g.derived && g.derived.every((d) => d && d.canvas === '60×120')) ? 'CANVAS_60x120_ALL_LEVELS' : 'MIXED', grids: out.grids.map((g) => ({ zoom: g.zoom, canvas: g.derived.map((d) => d && d.canvas) })) };
log('  P1b 判定：', JSON.stringify(out.p1b));

out.end = { status: await status(), sel: await selCount(), zoom: await zoomPct(), credits: await credits() };
log('\n终态：', JSON.stringify(out.end), '｜积分未变 =', out.start.credits === out.end.credits);
writeFileSync(new URL('./_tmp-b91a.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
