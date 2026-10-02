// 批次 111 · b 轮：在**自建时间线节点**上测 `⌘ scroll`（面板把它写作「缩放时间线」）。
//
// 要关的那一格：`help-and-shortcuts.md:329`
//   | 时间线 | 缩放时间线 | `⌘ scroll` | ❓ **未单独实测** | 只验证过**画布侧**的同一按键 |
//
// 🔴 判据设计（本批最重要的一步）：**缩放时间线这一格该读什么？**
//   节点里**没有**任何「缩放 %」控件（20 个 testid 里没有 zoom 类的）
//   ⇒ 不能去读「百分比」这种不存在的读数（批次 108：「读数对象里没取的字段，判据里不许出现」）
//   ⇒ 改取**控件自己声明的状态**：**标尺刻度标签的 x 间距**。
//      空时间线的标尺逐字是 `00:00 00:05 00:10 00:15 00:20 00:25 00:30`（每 5 秒一格），
//      缩放变了 ⇒ **相邻标签的像素间距必变**。这是最直接的自证信号。
//   ⇒ 同时**连读画布侧的缩放 aria**，证明它**没有**跟着变（这正是两条命令分家的依据）。
//
// 📌 控制变量：同一格里再测一次**不带 Meta 的普通滚轮**，用来分辨
//    「间距变了」是「缩放」造成的，还是「滚动」造成的。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b', self: 'node_egh7n0acaw' };
const SELF = out.self;
const save = () => writeFileSync(new URL('./_tmp-b111b.json', import.meta.url), JSON.stringify(out, null, 1));

// 读数：**标尺刻度标签的 x 间距** ＋ 画布缩放 aria ＋ 轨道滚动位置
const readAll = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const ruler = n.querySelector('[data-testid="timeline-ruler"]');
  const scroll = n.querySelector('[data-testid="timeline-track-scroll"]');
  const clock = n.querySelector('[data-testid="timeline-playback-clock"]');
  // 标尺刻度：取 ruler 里所有叶子 span，按文字形如 mm:ss 取
  const ticks = ruler ? Array.from(ruler.querySelectorAll('*'))
    .filter((e) => e.children.length === 0 && /^\d{2}:\d{2}$/.test((e.textContent || '').trim()))
    .map((e) => { const b = e.getBoundingClientRect();
      return { text: (e.textContent || '').trim(), x: Math.round(b.x * 10) / 10, w: Math.round(b.width) }; })
    .sort((a2, b2) => a2.x - b2.x) : [];
  const gaps = [];
  for (let k = 1; k < ticks.length; k++) gaps.push(Math.round((ticks[k].x - ticks[k - 1].x) * 10) / 10);
  const sr = scroll ? scroll.getBoundingClientRect() : null;
  return {
    innerText: (n.innerText || '').replace(/\s+/g, ' ').trim(),
    rulerBox: ruler ? (() => { const r = ruler.getBoundingClientRect(); return `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`; })() : null,
    ticks, gaps,
    clock: clock ? (clock.innerText || clock.textContent || '').replace(/\s+/g, ' ').trim() : null,
    scrollBox: sr ? `${Math.round(sr.x)},${Math.round(sr.y)} ${Math.round(sr.width)}×${Math.round(sr.height)}` : null,
    scrollLeft: scroll ? scroll.scrollLeft : null,
    scrollTop: scroll ? scroll.scrollTop : null,
    scrollW: scroll ? scroll.scrollWidth : null,
    scrollH: scroll ? scroll.scrollHeight : null,
    canvasZoom: (document.querySelector('[data-testid="canvas-zoom-percent"]') || { getAttribute: () => null }).getAttribute('aria-label'),
  };
}, SELF);

const trackPoint = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return null;
  const s = n.querySelector('[data-testid="timeline-track-scroll"]') || n.querySelector('[data-testid="timeline-clip-track"]');
  if (!s) return null;
  const r = s.getBoundingClientRect();
  // 落点现算（批次 108 纪律：动作时刻才算，且只问「命中元素是否落在目标内部」）
  for (let y = Math.ceil(r.y) + 4; y < r.y + r.height - 4; y += 3)
    for (let x = Math.ceil(r.x) + 6; x < r.x + r.width - 6; x += 3) {
      const el = document.elementFromPoint(x, y);
      if (el && (el === s || s.contains(el))) return { x, y, box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` };
    }
  return { none: true, box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` };
}, SELF);

const status = () => p.evaluate(() => {
  const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    zoom: (document.querySelector('[data-testid="canvas-zoom-percent"]') || { getAttribute: () => null }).getAttribute('aria-label') };
});

out.start = await status();
out.r0 = await readAll();
log('起点：', JSON.stringify(out.start));
log('标尺刻度：', JSON.stringify(out.r0.ticks));
log('相邻间距：', JSON.stringify(out.r0.gaps));
log('画布缩放：', out.r0.canvasZoom, '｜时钟：', out.r0.clock);
save();

const g = await keyGuard(p);
log('\n焦点守卫：', g.safe ? '✅' : '⛔', g.where || '');

// ---- 落点现算 ----
const tp = await trackPoint();
out.tp = tp;
log('轨道落点：', JSON.stringify(tp));
if (!tp || tp.none) { log('🔴 找不到轨道落点 ⇒ 中止'); save(); await b.close(); process.exit(3); }
const el = await p.evaluate((t) => { const e = document.elementFromPoint(t.x, t.y);
  return { ok: !!e, inTrack: e ? !!e.closest('[data-testid="timeline-clip-track"],[data-testid="timeline-track-scroll"]') : false,
    tag: e ? e.tagName : null }; }, tp);
log('落点校验：', JSON.stringify(el));
if (!el.ok || !el.inTrack) { log('🔴 落点校验不过 ⇒ 中止'); save(); await b.close(); process.exit(3); }

// ---- ① Meta + 滚轮（往下） ----
log('\n=== ① Meta + 滚轮 ↓ （面板写作「缩放时间线」）===');
await p.mouse.move(tp.x, tp.y); await p.waitForTimeout(500);
out.act1 = { before: out.r0 };
await p.keyboard.down('Meta'); await p.waitForTimeout(200);
for (let k = 0; k < 4; k++) { await p.mouse.wheel(0, 120); await p.waitForTimeout(400); }
await p.keyboard.up('Meta'); await p.waitForTimeout(1200);
out.r1 = await readAll();
log('  刻度：', JSON.stringify(out.r1.ticks));
log('  间距：', JSON.stringify(out.r1.gaps));
log('  画布缩放：', out.r1.canvasZoom, '｜scrollLeft：', out.r1.scrollLeft);
save();

// ---- ② Meta + 滚轮（往上，反向） ----
log('\n=== ② Meta + 滚轮 ↑ ===');
await p.mouse.move(tp.x, tp.y); await p.waitForTimeout(400);
await p.keyboard.down('Meta'); await p.waitForTimeout(200);
for (let k = 0; k < 4; k++) { await p.mouse.wheel(0, -120); await p.waitForTimeout(400); }
await p.keyboard.up('Meta'); await p.waitForTimeout(1200);
out.r2 = await readAll();
log('  刻度：', JSON.stringify(out.r2.ticks));
log('  间距：', JSON.stringify(out.r2.gaps));
log('  画布缩放：', out.r2.canvasZoom, '｜scrollLeft：', out.r2.scrollLeft);
save();

// ---- ③ 控制变量：普通滚轮（不带 Meta） ----
log('\n=== ③ 控制变量：普通滚轮（不带 Meta） ===');
await p.mouse.move(tp.x, tp.y); await p.waitForTimeout(400);
for (let k = 0; k < 4; k++) { await p.mouse.wheel(0, 120); await p.waitForTimeout(400); }
await p.waitForTimeout(1000);
out.r3 = await readAll();
log('  刻度：', JSON.stringify(out.r3.ticks));
log('  间距：', JSON.stringify(out.r3.gaps));
log('  画布缩放：', out.r3.canvasZoom, '｜scrollLeft：', out.r3.scrollLeft, '｜scrollW/H：', out.r3.scrollW, out.r3.scrollH);
save();

// ---- ④ 对照：Meta + 滚轮打在**画布**上（不是时间线） ----
log('\n=== ④ 对照：Meta + 滚轮打在画布空白处 ===');
const canvasPt = await p.evaluate(() => {
  for (let y = 300; y < 600; y += 10) for (let x = 300; x < 1100; x += 10) {
    const e = document.elementFromPoint(x, y);
    if (e && !e.closest('.react-flow__node') && !e.closest('button,[role=button]')) return { x, y }; }
  return null; });
log('  画布落点：', JSON.stringify(canvasPt));
if (canvasPt) {
  await p.mouse.move(canvasPt.x, canvasPt.y); await p.waitForTimeout(400);
  await p.keyboard.down('Meta'); await p.waitForTimeout(200);
  for (let k = 0; k < 4; k++) { await p.mouse.wheel(0, 120); await p.waitForTimeout(400); }
  await p.keyboard.up('Meta'); await p.waitForTimeout(1200);
  out.r4 = await readAll();
  log('  画布缩放：', out.r4.canvasZoom, '｜时间线间距：', JSON.stringify(out.r4.gaps));
  save();
}

out.summary = {
  base_gaps: out.r0.gaps,
  meta_down_gaps: out.r1.gaps,
  meta_up_gaps: out.r2.gaps,
  plain_wheel_gaps: out.r3.gaps,
  canvas_zoom_throughout: [out.r0.canvasZoom, out.r1.canvasZoom, out.r2.canvasZoom, out.r3.canvasZoom, out.r4 ? out.r4.canvasZoom : null],
};
log('\n=== 汇总 ===');
log(JSON.stringify(out.summary, null, 1));
save();
log('\nDONE b');
process.exit(0);
