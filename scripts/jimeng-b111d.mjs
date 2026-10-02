// 批次 111 · d 轮：把 c 轮没做完的对照做完，**不依赖落在节点上**。
//
// c 轮中止的原因（不是产品问题，是我选的落点）：60% 下自建节点缩到 `458,36 266×46`，
// **y=36 落在顶栏底下** ⇒ `elementFromPoint` 命中的永远是顶栏 ⇒ 落点校验不过 ⇒ **中止**。
// 这正是第四道护栏该有的行为（批次 108：读不到就停，不猜不硬来）。
//
// d 轮改用**不需要落在节点上**的对照，判据反而更硬：
//   画布上共 **3 个**时间线节点（时间线 1 / 2 是别人的、3 是本轮自建），
//   60% 下三者的标尺刻度间距**逐字相同**（都 `96.3`）
//   ⇒ ��「如果时间线有自己的缩放」，它们的间距应该可以各不相同
//   ⇒ 若一次 `⌘ scroll` 让**三者**按**同一比值**变 ⇒ 间距只是画布缩放的副产物
//
// 再补一格：在 60% 下**重做 b 轮那个动作**（`⌘ scroll` 打在自建时间线上），
// 这次落点扫描放宽到「y 必须 > 60（避开顶栏）」。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'd' };
const save = () => writeFileSync(new URL('./_tmp-b111d.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-zoom-percent"]') || { getAttribute: () => null }).getAttribute('aria-label'));
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
const readRuler = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const ruler = n.querySelector('[data-testid="timeline-ruler"]');
  if (!ruler) return { __err: 'no-ruler' };
  const r = ruler.getBoundingClientRect();
  const ticks = Array.from(ruler.querySelectorAll('*'))
    .filter((e) => e.children.length === 0 && /^\d{2}:\d{2}$/.test((e.textContent || '').trim()))
    .map((e) => { const bb = e.getBoundingClientRect(); return { text: (e.textContent || '').trim(), x: Math.round(bb.x * 10) / 10 }; })
    .sort((a2, b2) => a2.x - b2.x);
  const gaps = [];
  for (let k = 1; k < ticks.length; k++) gaps.push(Math.round((ticks[k].x - ticks[k - 1].x) * 10) / 10);
  return { title: (n.getAttribute('aria-label') || '').slice(0, 40), nTicks: ticks.length, gaps,
    nodeBox: (() => { const nb = n.getBoundingClientRect(); return `${Math.round(nb.x)},${Math.round(nb.y)} ${Math.round(nb.width)}×${Math.round(nb.height)}`; })(),
    rulerBox: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    mean: gaps.length ? Math.round((gaps.reduce((s, x) => s + x, 0) / gaps.length) * 100) / 100 : null,
    inner: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 110) };
}, id);
const trackPointSafe = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const s = n.querySelector('[data-testid="timeline-track-scroll"]') || n.querySelector('[data-testid="timeline-clip-track"]');
  if (!s) return { __err: 'no-track' };
  const r = s.getBoundingClientRect();
  const tried = [];
  for (let y = Math.ceil(r.y) + 2; y < r.y + r.height - 2; y += 2)
    for (let x = Math.ceil(r.x) + 4; x < r.x + r.width - 4; x += 2) {
      if (y <= 60 || y >= innerHeight - 40) continue;          // 避开顶栏与底栏
      if (x <= 200 || x >= innerWidth - 8) continue;           // 避开左栏
      const el = document.elementFromPoint(x, y);
      if (el && (el === s || s.contains(el))) return { x, y, box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` };
      if (tried.length < 4) tried.push({ x, y, tag: el ? el.tagName : null, inNode: el ? !!el.closest('.react-flow__node') : false });
    }
  return { none: true, box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`, tried };
}, id);

out.timelines = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-timeline'))
  .map((n) => ({ id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label') })));
out.ids = out.timelines.map((t) => t.id);
log('时间线节点：', JSON.stringify(out.timelines));
save();

out.z0 = await zoom();
log('\n起点画布缩放：', out.z0);
if (out.z0 !== 'Zoom options, 60%') { await setZoom(60); await p.waitForTimeout(900); }
out.z0 = await zoom();
log('归位后：', out.z0);

// ---- 三个时间线的标尺：同一缩放下是否本来就相同 ----
out.base = { zoom: out.z0, rulers: {} };
for (const id of out.ids) out.base.rulers[id] = await readRuler(id);
log('\n=== 同一画布缩放下，三个时间线的标尺 ===');
for (const id of out.ids) { const r = out.base.rulers[id];
  log(`  ${id}（${r.title}）节点 ${r.nodeBox} 标尺 ${r.rulerBox} 平均间距 ${r.mean}｜${JSON.stringify(r.gaps)}`); }
save();

// ---- 对照 A：`⌘ scroll` 打在画布空白处，看**三个**标尺是否同步 ----
const cpt = await p.evaluate(() => {
  for (let y = 320; y < 620; y += 8) for (let x = 300; x < 1120; x += 8) {
    const e = document.elementFromPoint(x, y);
    if (e && !e.closest('.react-flow__node') && !e.closest('button,[role=button]')) return { x, y }; }
  return null; });
out.cpt = cpt;
log('\n=== 对照 A：`⌘ scroll` 打在画布空白处', JSON.stringify(cpt), '===');
if (cpt) {
  await p.mouse.move(cpt.x, cpt.y); await p.waitForTimeout(450);
  await p.keyboard.down('Meta'); await p.waitForTimeout(200);
  for (let k = 0; k < 4; k++) { await p.mouse.wheel(0, 120); await p.waitForTimeout(400); }
  await p.keyboard.up('Meta'); await p.waitForTimeout(1500);
  out.afterA = { zoom: await zoom(), rulers: {} };
  for (const id of out.ids) out.afterA.rulers[id] = await readRuler(id);
  log('  画布缩放：', out.base.zoom, '→', out.afterA.zoom);
  for (const id of out.ids) { const a = out.base.rulers[id].mean, c = out.afterA.rulers[id].mean;
    log(`  ${id}：平均间距 ${a} → ${c}｜比值 ${(a / c).toFixed(3)}`); }
  save();
}

// ---- 归位 ----
await setZoom(60); await p.waitForTimeout(1100);
out.zBack = await zoom();
log('\n归位到 60%：', out.zBack);
save();

// ---- 对照 B：`⌘ scroll` 打在自建时间线上（落点避开顶栏） ----
const SELF = out.ids.find((id) => id === 'node_egh7n0acaw') || out.ids[out.ids.length - 1];
out.self = SELF;
out.baseB = { zoom: out.zBack, ruler: await readRuler(SELF) };
log('\n=== 对照 B：`⌘ scroll` 打在自建时间线', SELF, '===');
log('  节点盒：', out.baseB.ruler.nodeBox, '｜标尺：', out.baseB.ruler.rulerBox, '｜平均间距：', out.baseB.ruler.mean);
const tp = await trackPointSafe(SELF);
out.tp = tp;
log('  落点扫描：', JSON.stringify(tp));
const chk = tp && tp.x ? await p.evaluate((t) => { const e = document.elementFromPoint(t.x, t.y);
  return { ok: !!e, inTrack: e ? !!e.closest('[data-testid="timeline-clip-track"],[data-testid="timeline-track-scroll"]') : false, tag: e ? e.tagName : null }; }, tp) : null;
log('  落点校验：', JSON.stringify(chk));
if (tp && tp.x && chk && chk.ok && chk.inTrack) {
  await p.mouse.move(tp.x, tp.y); await p.waitForTimeout(500);
  await p.keyboard.down('Meta'); await p.waitForTimeout(200);
  for (let k = 0; k < 4; k++) { await p.mouse.wheel(0, 120); await p.waitForTimeout(400); }
  await p.keyboard.up('Meta'); await p.waitForTimeout(1500);
  out.afterB = { zoom: await zoom(), ruler: await readRuler(SELF) };
  log('  画布缩放：', out.baseB.zoom, '→', out.afterB.zoom);
  log('  平均间距：', out.baseB.ruler.mean, '→', out.afterB.ruler.mean, '｜比值', (out.baseB.ruler.mean / out.afterB.ruler.mean).toFixed(3));
  log('  刻度：', JSON.stringify(out.afterB.ruler.gaps));
  save();
} else {
  out.stepB = 'skipped: landing point not available';
  log('  ⛔ 落点不可用 ⇒ 跳过本格（护栏中止，不猜）');
  save();
}

// ---- 最终归位 + 连读两次 ----
await setZoom(60); await p.waitForTimeout(1000);
out.zEnd = await zoom();
await p.waitForTimeout(900);
out.zEnd2 = await zoom();
out.zStable = out.zEnd === out.zEnd2;
log('\n最终缩放：', out.zEnd, '｜连读：', out.zEnd2, '｜一致 =', out.zStable);
save();

const ratio = (a, c) => (a && c ? Math.round((a / c) * 1000) / 1000 : null);
out.verdict = {
  same_zoom_all_rulers_equal: new Set(Object.values(out.base.rulers).map((r) => r.mean)).size === 1,
  base_mean: out.base.rulers[out.ids[0]].mean,
  afterA: out.afterA ? { zoom: out.afterA.zoom, ratios: out.ids.map((id) => ({ id, base: out.base.rulers[id].mean, after: out.afterA.rulers[id].mean, ratio: ratio(out.base.rulers[id].mean, out.afterA.rulers[id].mean) })) } : null,
  afterB: out.afterB ? { zoom: out.afterB.zoom, ratio: ratio(out.baseB.ruler.mean, out.afterB.ruler.mean) } : null,
  zoomFinal: out.zEnd,
};
log('\n=== 判定 ===');
log(JSON.stringify(out.verdict, null, 1));
save();
log('\nDONE d');
process.exit(0);
