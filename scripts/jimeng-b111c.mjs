// 批次 111 · c 轮：钉死「`⌘ scroll` 到底缩放的是画布还是时间线」—— 用**别人的另一个时间线节点**做对照。
//
// b 轮的读数已经很强，但还差一格：
//   `⌘ scroll`（打在自建时间线上）⇒ 标尺间距 `73.9 → 35.6`，画布缩放 `46% → 22%`
//   比值：`73.9/35.6 = 2.076`　vs　`46/22 = 2.090`　⇒ **几乎同一个比**
//   ⇒ 提示：**时间线跟着变，只是因为它是画布上的一个节点、被整体缩放了**
//   反向 `⌘ scroll` 回去 ⇒ 间距逐字回到 `73.9 / 73.9 / 73.8 / …`
//   **普通滚轮（不带 Meta）** ⇒ 间距、画布缩放、`scrollLeft` **全部不动**
//
// 仍存的一个反驳空间：**「两个东西一起变」也可能是「两个缩放恰好同步」**。
// 决定性对照：**同时读另一个时间线节点的标尺**（画布上有「时间线 2」，1 visual track）。
//   · 若**两个时间线**的间距按**同一比值**变 ⇒ 画布级缩放，时间线**没有自己的缩放**
//   · 若只有**我这个**变 ⇒ 那是时间线级缩放
//
// 🔴 只读别人的节点：只量它的标尺刻度位置，**不点它、不拖它、不改它**。
// 🔴 收尾：b 轮把画布缩放留在 22%，本轮**先归位到 60%** 再测，测完再归位一次。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c', self: 'node_egh7n0acaw' };
const SELF = out.self;
const save = () => writeFileSync(new URL('./_tmp-b111c.json', import.meta.url), JSON.stringify(out, null, 1));

// 读**任意**时间线节点的标尺刻度（只读，不碰）
const readRuler = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const ruler = n.querySelector('[data-testid="timeline-ruler"]');
  if (!ruler) return { __err: 'no-ruler' };
  const ticks = Array.from(ruler.querySelectorAll('*'))
    .filter((e) => e.children.length === 0 && /^\d{2}:\d{2}$/.test((e.textContent || '').trim()))
    .map((e) => { const b = e.getBoundingClientRect(); return { text: (e.textContent || '').trim(), x: Math.round(b.x * 10) / 10 }; })
    .sort((a2, b2) => a2.x - b2.x);
  const gaps = [];
  for (let k = 1; k < ticks.length; k++) gaps.push(Math.round((ticks[k].x - ticks[k - 1].x) * 10) / 10);
  return { title: (n.getAttribute('aria-label') || '').slice(0, 40), nTicks: ticks.length, first: ticks[0] ? ticks[0].text : null, gaps,
    mean: gaps.length ? Math.round((gaps.reduce((s, x) => s + x, 0) / gaps.length) * 100) / 100 : null };
}, id);

const canvasZoom = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-zoom-percent"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const setZoom = async (v) => {
  const bt = await p.evaluate(() => { const z = document.querySelector('[data-testid="canvas-zoom-percent"]');
    if (!z) return null; const r = z.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (!bt) return false;
  await p.mouse.click(bt.x, bt.y); await p.waitForTimeout(900);
  const inp = await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-zoom-percent-input"]');
    if (!i) return null; i.focus(); const r = i.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (!inp) { await p.keyboard.press('Escape'); return false; }
  await p.mouse.click(inp.x, inp.y); await p.waitForTimeout(350);
  await p.keyboard.press('ControlOrMeta+a'); await p.waitForTimeout(180);
  await p.keyboard.type(String(v), { delay: 110 }); await p.waitForTimeout(400);
  await p.keyboard.press('Enter'); await p.waitForTimeout(1500);
  return true;
};
const trackPoint = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null;
  const s = n.querySelector('[data-testid="timeline-track-scroll"]') || n.querySelector('[data-testid="timeline-clip-track"]');
  if (!s) return null;
  const r = s.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 4; y < r.y + r.height - 4; y += 3)
    for (let x = Math.ceil(r.x) + 6; x < r.x + r.width - 6; x += 3) {
      const el = document.elementFromPoint(x, y);
      if (el && (el === s || s.contains(el))) return { x, y }; }
  return null;
}, id);

// ---- 找画布上**所有**时间线节点（只列，不碰） ----
out.timelines = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-timeline')).map((n) => {
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
    inner: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80),
    screen: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }; }));
log('=== 画布上的时间线节点（只列） ===');
out.timelines.forEach((t) => log(`  ${t.id}  ${t.aria}  ${t.screen}\n      ${t.inner}`));
save();
const others = out.timelines.filter((t) => t.id !== SELF);
log('\n别人的时间线节点：', JSON.stringify(others.map((t) => ({ id: t.id, aria: t.aria }))));
out.otherIds = others.map((t) => t.id);

// ---- 归位到 60% 再测 ----
out.zoomBefore = await canvasZoom();
log('\n归位前画布缩放：', out.zoomBefore);
if (out.zoomBefore !== 'Zoom options, 60%') {
  const ok = await setZoom(60);
  await p.waitForTimeout(900);
  out.zoomSet = await canvasZoom();
  log('归位到 60%：', ok, '⇒', out.zoomSet);
} else { out.zoomSet = out.zoomBefore; }
save();

// ---- 基线 ----
out.base = { zoom: await canvasZoom(), mine: await readRuler(SELF) };
for (const id of out.otherIds) out.base[id] = await readRuler(id);
log('\n=== 基线（60%） ===');
log('  画布缩放：', out.base.zoom);
for (const k of ['mine', ...out.otherIds]) log(`  ${k === 'mine' ? '自建' : k}（${out.base[k].title}）：刻度数 ${out.base[k].nTicks} 首个 ${out.base[k].first} 平均间距 ${out.base[k].mean}｜${JSON.stringify(out.base[k].gaps)}`);
save();

// ---- `⌘ scroll` 打在**自建时间线**上 ----
const tp = await trackPoint(SELF);
out.tp = tp;
log('\n自建时间线轨道落点：', JSON.stringify(tp));
const chk = tp ? await p.evaluate((t) => { const e = document.elementFromPoint(t.x, t.y);
  return { ok: !!e, inTrack: e ? !!e.closest('[data-testid="timeline-clip-track"],[data-testid="timeline-track-scroll"]') : false }; }, tp) : null;
log('落点校验：', JSON.stringify(chk));
if (!tp || !chk || !chk.ok || !chk.inTrack) { log('🔴 落点校验不过 ⇒ 中止'); save(); await b.close(); process.exit(3); }

log('\n=== `⌘ scroll` ↓ 打在自建时间线上 ===');
await p.mouse.move(tp.x, tp.y); await p.waitForTimeout(500);
await p.keyboard.down('Meta'); await p.waitForTimeout(200);
for (let k = 0; k < 4; k++) { await p.mouse.wheel(0, 120); await p.waitForTimeout(400); }
await p.keyboard.up('Meta'); await p.waitForTimeout(1400);
out.after = { zoom: await canvasZoom(), mine: await readRuler(SELF) };
for (const id of out.otherIds) out.after[id] = await readRuler(id);
log('  画布缩放：', out.after.zoom);
for (const k of ['mine', ...out.otherIds]) log(`  ${k === 'mine' ? '自建' : k}：平均间距 ${out.base[k].mean} → ${out.after[k].mean}｜${JSON.stringify(out.after[k].gaps)}`);
save();

const ratio = (a, c) => (a && c ? Math.round((a / c) * 1000) / 1000 : null);
out.verdict = {
  zoom_before: out.base.zoom, zoom_after: out.after.zoom,
  mine_gap_ratio: ratio(out.base.mine.mean, out.after.mine.mean),
  zoom_ratio: ratio(Number((out.base.zoom || '').replace(/\D/g, '')), Number((out.after.zoom || '').replace(/\D/g, ''))),
  others: out.otherIds.map((id) => ({ id, base: out.base[id].mean, after: out.after[id].mean, ratio: ratio(out.base[id].mean, out.after[id].mean) })),
};
log('\n=== 判定 ===');
log(JSON.stringify(out.verdict, null, 1));
save();

// ---- 归位 ----
log('\n=== 归位画布到 60% ===');
await setZoom(60); await p.waitForTimeout(1000);
out.zoomEnd = await canvasZoom();
await p.waitForTimeout(800);
out.zoomEnd2 = await canvasZoom();
log('归位后：', out.zoomEnd, '｜连读：', out.zoomEnd2, '｜一致 =', out.zoomEnd === out.zoomEnd2);
save();
log('\nDONE c');
process.exit(0);
