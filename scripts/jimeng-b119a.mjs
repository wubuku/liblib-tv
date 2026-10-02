// 批次 119 · a 轮：造**自建时间线节点**，读全它的浮动工具条。
//
// 靶子：时间线节点的浮动工具条**全册没有系统记录** ——
//   `use-node-toolbar.md` 覆盖六种（文本/图片/视频/空/多选/编组），**没有时间线**；
//   `timeline-node.md` 记的是节点内部（20 个 testid、9 aria、7 个专有按钮），
//   **没有读工具条**。零散只见于 90-troubleshooting.md:105 的「控制栏」一句。
//
// 🔑 触发它的是批次 118 的复扫：按 `[class*="node-toolbar"]` 宽泛扫时，
//   画布上**两个时间线节点**各带出一套工具条，形状是
//   `00:00 / 00:00 全屏编辑` ＋ 按钮 `导出时间线` / `全屏编辑` ＋ 一排刻度
//   `00:00 / 00:05 / … / 00:30` ⇒ 那是**别人的节点**、且在视口外（坐标为负），
//   本轮必须**自建一个**来读全。
//
// ⚠️ 已知坑（批次 111）：时间线节点建出来的位置常常**在顶栏底下 / 视口外**，
//    落点一个都拿不到。处置：**先造，再读位置；若在视口外，用缩放输入框填小值
//    把它带回视口**（批次 111 的办法），**不跳过**。
//
// ⛔ 只读不点：`导出时间线` 属**未获授权**的对外产出动作；`全屏编辑` 亦未单独授权。
//    本轮只读它们的 aria / 尺寸 / 位置，**一个都不点**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b119a.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return e ? { aria: e.getAttribute('aria-label'), rect: (() => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() } : null; });

// 工具条读数：只认**归属于该节点**的那一条（批次 118 立规：宽泛扫会命中别人的东西）
const readTlToolbar = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  const r = (e) => { const q = e.getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; };
  const nr = n.getBoundingClientRect();
  // 时间线工具条在节点**上方**，用「水平重叠 + 在节点上方」归属，避开别人的
  const cands = Array.from(document.querySelectorAll('.react-flow__node-toolbar,[data-testid="node-toolbar"]'))
    .map((e) => ({ e, q: e.getBoundingClientRect() }))
    .filter((x) => x.q.width > 1 && x.q.height > 1)
    .filter((x) => x.q.right > nr.left - 40 && x.q.left < nr.right + 40 && x.q.bottom <= nr.top + 60);
  return {
    at: Date.now(), nodeRect: [nr.x, nr.y, nr.width, nr.height].map(Math.round),
    nAllTb: document.querySelectorAll('.react-flow__node-toolbar,[data-testid="node-toolbar"]').length,
    mine: cands.map((x) => ({ rect: r(x.e), tid: x.e.getAttribute('data-testid'), cls: (x.e.getAttribute('class') || '').toString().slice(0, 40),
      text: (x.e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200), svgs: x.e.querySelectorAll('svg').length,
      btns: Array.from(x.e.querySelectorAll('button,[role=button]')).map((e) => ({ aria: e.getAttribute('aria-label'), rect: r(e) })).filter((y) => y.aria) })),
    // 刻度逐字：工具条里所有含 00: 的元素
    ticks: Array.from(document.querySelectorAll('.react-flow__node-toolbar *'))
      .map((e) => ({ t: (e.textContent || '').replace(/\s+/g, ' ').trim(), rect: r(e), tag: e.tagName, tid: e.getAttribute('data-testid') }))
      .filter((x) => /^\d{2}:\d{2}$/.test(x.t) && x.rect[2] > 1).slice(0, 20),
  };
}, id);

// 把节点带回视口：缩放输入框填小值（批次 111 的办法）
async function zoomTo(pct) {
  const r = await zoom();
  if (r.aria.includes(`${pct}%`)) return r.aria;
  await p.mouse.click(r.rect[0] + r.rect[2] / 2, r.rect[1] + r.rect[3] / 2); await p.waitForTimeout(800);
  const inp = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent-input"]'); if (!e) return null;
    const q = e.getBoundingClientRect(); return [Math.round(q.x + q.width / 2), Math.round(q.y + q.height / 2)]; });
  if (!inp) return null;
  await p.mouse.click(inp[0], inp[1]); await p.waitForTimeout(350);
  await p.keyboard.press('Meta+a'); await p.waitForTimeout(150);
  await p.keyboard.type(String(pct), { delay: 100 }); await p.waitForTimeout(400);
  await p.keyboard.press('Enter'); await p.waitForTimeout(1800);
  return (await zoom()).aria;
}

out.start = { nodes: await nodeN(), credits: await credits(), zoom: await zoom() };
log('起点：', JSON.stringify(out.start));
const reloc = await p.evaluate(() => {
  const bad = (x, y) => { const el = document.elementFromPoint(x, y);
    if (!el || el.closest('.react-flow__node')) return true;
    if (x < 200 || y < 60 || y > 630 || x > 1120) return true;
    if (el.closest('button,[role=button],input,a,[contenteditable]')) return true;
    if (el.closest('[role="menu"],[class*="node-toolbar"],[data-testid="node-toolbar"]')) return true; return false; };
  for (let y = 280; y < 630; y += 12) for (let x = 260; x < 1100; x += 12) if (!bad(x, y)) return { x, y }; return null; });
if (reloc) { await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  await p.mouse.click(reloc.x, reloc.y); await p.waitForTimeout(1200); }
const g0 = await keyGuard(p);
log('焦点守卫：', g0.safe ? '✅' : '⛔', g0.where || '');
if (!g0.safe) { log('⛔ 中止'); await b.close(); process.exit(2); }

// ---- 造自建时间线节点 ----
log('\n=== 造时间线节点 ===');
const idsBefore = await allIds();
const blank = await p.evaluate(() => {
  const bad = (x, y) => { const el = document.elementFromPoint(x, y);
    if (!el || el.closest('.react-flow__node')) return true;
    if (x < 200 || y < 60 || y > 630 || x > 1120) return true;
    if (el.closest('button,[role=button],input,a')) return true; return false; };
  for (let y = 280; y < 630; y += 12) for (let x = 260; x < 1100; x += 12) if (!bad(x, y)) return [x, y]; return null; });
log('空白落点：', JSON.stringify(blank));
if (!blank) { log('🔴 中止'); await b.close(); process.exit(3); }
await p.mouse.move(blank[0], blank[1]); await p.waitForTimeout(400);
await p.mouse.down({ button: 'right' }); await p.waitForTimeout(300); await p.mouse.up({ button: 'right' });
await p.waitForTimeout(1300);
const nj = await p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]'))
  for (const it of m.querySelectorAll('[role=menuitem]')) {
    if ((it.innerText || '').trim().startsWith('新建节点')) { const r = it.getBoundingClientRect();
      return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; } } return null; });
await p.mouse.move(nj.x, nj.y); await p.waitForTimeout(500);
await p.mouse.move(nj.x + 3, nj.y); await p.waitForTimeout(1500);
const target = await p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]')) {
    if (getComputedStyle(m).visibility === 'hidden') continue;
    for (const it of m.querySelectorAll('[role=menuitem]')) { if ((it.innerText || '').trim() !== '时间线') continue;
      const r = it.getBoundingClientRect(); if (r.width < 1) continue;
      const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
      const h = document.elementFromPoint(cx, cy); if (!h || !(h === it || it.contains(h))) continue;
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; } }
  return { __err: 'no-clickable' }; });
log('「时间线」落点：', JSON.stringify(target));
if (target.__err) { log('⛔ 中止'); await b.close(); process.exit(3); }
await p.mouse.click(target.rect[0] + target.rect[2] / 2, target.rect[1] + target.rect[3] / 2);

let SELF = null, guard = null;
for (let k = 1; k <= 18; k++) {
  await p.waitForTimeout(1200);
  const ids = await allIds();
  const diff = ids.filter((id) => !idsBefore.includes(id));
  if (diff.length === 1) { const sel = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
    guard = { diff, sel, ok: sel.includes(diff[0]) };
    if (guard.ok) { SELF = diff[0]; log(`  #${k} 护栏② 通过：${SELF}`); break; } }
  else if (diff.length > 1) { log(`  ⛔ 差集超过一个：${JSON.stringify(diff)}`); break; }
}
out.guard = guard; out.self = SELF;
log(`护栏②：${JSON.stringify(guard)} ⇒ ${SELF ? '✅' : '🔴'}`);
save();
if (!SELF) { log('🔴 中止'); await b.close(); process.exit(3); }

// ---- 节点位置 + 是否在视口内 ----
out.tlNode = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  return { selected: n.classList.contains('selected'),
    clsType: (n.getAttribute('class') || '').toString().match(/react-flow__node-(\w+)/)?.[1] || null,
    screenRect: [r.x, r.y, r.width, r.height].map(Math.round),
    在视口内: r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth && r.width > 1,
    inner: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120),
    tids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))) }; }, SELF);
log('\n时间线节点：', JSON.stringify(out.tlNode, null, 1));
save();

// ---- 若在视口外：缩小把它带回（批次 111 的办法），**不跳过** ----
if (!out.tlNode.在视口内) {
  log('\n⚠️ 节点不在视口内 ⇒ 缩小把它带回');
  for (const pct of [40, 30, 20]) {
    const z = await zoomTo(pct);
    const vis = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
      const r = n.getBoundingClientRect();
      return { rect: [r.x, r.y, r.width, r.height].map(Math.round), 在视口内: r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth && r.width > 1 }; }, SELF);
    log(`  ${pct}% → ${z}｜${JSON.stringify(vis)}`);
    out[`visAt${pct}`] = vis;
    if (vis && vis.在视口内) { out.broughtBack = { pct, z }; log(`  ✅ ${pct}% 带回视口`); break; }
  }
} else log('节点本来就在视口内');
save();

// ---- 读工具条 ----
out.tb = await readTlToolbar(SELF);
log('\n=== 归属本节点的工具条 ===');
log('节点屏上矩形：', JSON.stringify(out.tb.nodeRect), '｜全页工具条元素数：', out.tb.nAllTb, '｜归属本节点的：', out.tb.mine.length);
out.tb.mine.forEach((t, i) => {
  log(`  #${i} ${JSON.stringify(t.rect)}｜tid=${t.tid}｜class ${JSON.stringify(t.cls)}｜svg ${t.svgs}`);
  log(`     text  ${JSON.stringify(t.text)}`);
  log(`     按钮 ${t.btns.length} 个：${JSON.stringify(t.btns.map((x) => x.aria))}`);
  t.btns.forEach((x) => log(`        ${JSON.stringify(x.aria)} ${JSON.stringify(x.rect)}`));
});
log('\n刻度逐字（全部工具条里含 00: 的元素）：');
out.tb.ticks.forEach((t) => log(`   ${JSON.stringify(t)}`));
out.end = { nodes: await nodeN(), credits: await credits(), zoom: await zoom() };
log('\n终点：', JSON.stringify(out.end));
save();
log('\nDONE a');
process.exit(0);
