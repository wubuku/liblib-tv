// 批次 115 · a 轮：验 **「选中主体节点标题输入框自动获焦」**（批次 97 记 VOID）。
//
// 老账（`subject-node.md:283`）：
//   「⚠️ 本轮有一格记 VOID：『选中主体节点标题输入框自动获焦』没测到 ——
//     第一次的落点落在节点中心（空态导入区，不在标题上），
//     第二次该节点在密集区被别的节点完全盖住、一个可用落点都拿不到。」
//
// 🔑 这条为什么重要：它不是普通功能读数，而是 **keyGuard 守卫自己的前提假设**。
//    `scripts/jimeng-safe-keys.mjs` 的注释写着「单击选中『主体』节点 ——
//    标题 `input[aria-label="名称"]` **自动获焦**」，而守卫**照这条拦人**。
//    ⇒ 如果它不成立，守卫的一个前提是错的（守卫本身不会坏，但理由是假的）。
//
// 🔴 批次 97 失败的两个原因，本轮都有对应的现成办法：
//   ①「落点落在节点中心（不在标题上）」⇒ **直接读标题元素的矩形**，在它内部找点，
//      不用节点中心；且按**动作时刻现算**（批次 113 立规）。
//   ②「被别的节点完全盖住」⇒ 现算落点时**只问「命中元素是否落在标题内部」**，
//      命中不了就先用缩放输入框填小值把节点带回视口（批次 111 的办法），**不跳过**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b115a.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return e ? { aria: e.getAttribute('aria-label'), rect: (() => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() } : null; });

// 读焦点：把 keyGuard 用到的那几个字段全读出来，并记 activeElement 的祖先链
const readFocus = (lbl) => p.evaluate((l) => {
  const a = document.activeElement;
  if (!a) return { at: Date.now(), lbl: l, tag: null, where: '(body)' };
  const chain = []; let n = a, d = 0;
  while (n && d++ < 6) { const r = n.getBoundingClientRect();
    chain.push({ d, tag: n.tagName, tid: n.getAttribute('data-testid'), aria: n.getAttribute('aria-label'),
      type: n.getAttribute('type'), cls: (n.getAttribute('class') || '').toString().slice(0, 34),
      ce: n.isContentEditable === true, rect: [r.x, r.y, r.width, r.height].map(Math.round) });
    n = n.parentElement; }
  return { at: Date.now(), lbl: l, tag: a.tagName, tid: a.getAttribute('data-testid'),
    aria: a.getAttribute('aria-label'), type: a.getAttribute('type'),
    isInputLike: a.tagName === 'INPUT' || a.tagName === 'TEXTAREA' || a.isContentEditable === true,
    value: a.value !== undefined ? String(a.value) : null, chain };
}, lbl);

out.start = { nodes: await nodeN(), credits: await credits(), zoom: await zoom() };
log('起点：', JSON.stringify(out.start));
save();

// 先把焦点归位到画布（上一批可能留在别处）
const reloc = await p.evaluate(() => {
  const bad = (x, y) => { const el = document.elementFromPoint(x, y);
    if (!el || el.closest('.react-flow__node')) return true;
    if (x < 200 || y < 60 || y > 630 || x > 1120) return true;
    if (el.closest('button,[role=button],input,a,[contenteditable]')) return true;
    if (el.closest('[role="menu"],[data-testid="node-toolbar"]')) return true;
    return false; };
  for (let y = 280; y < 630; y += 12) for (let x = 260; x < 1100; x += 12) if (!bad(x, y)) return { x, y };
  return null; });
if (reloc) { await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  await p.mouse.click(reloc.x, reloc.y); await p.waitForTimeout(1200); }
const g0 = await keyGuard(p);
log('焦点守卫（起点）：', g0.safe ? '✅' : '⛔', g0.where || '');
if (!g0.safe) { log('⛔ 中止'); await b.close(); process.exit(2); }

// ---- 造一个自建主体节点 ----
log('\n=== 造主体节点 ===');
const idsBefore = await allIds();
const blank = await p.evaluate(() => {
  const bad = (x, y) => { const el = document.elementFromPoint(x, y);
    if (!el || el.closest('.react-flow__node')) return true;
    if (x < 200 || y < 60 || y > 630 || x > 1120) return true;
    if (el.closest('button,[role=button],input,a')) return true; return false; };
  for (let y = 280; y < 630; y += 12) for (let x = 260; x < 1100; x += 12) if (!bad(x, y)) return [x, y];
  return null; });
log('空白落点：', JSON.stringify(blank));
if (!blank) { log('🔴 找不到可用空白 ⇒ 中止'); await b.close(); process.exit(3); }
await p.mouse.move(blank[0], blank[1]); await p.waitForTimeout(400);
await p.mouse.down({ button: 'right' }); await p.waitForTimeout(300); await p.mouse.up({ button: 'right' });
await p.waitForTimeout(1300);
const nj = await p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]'))
  for (const it of m.querySelectorAll('[role=menuitem]')) {
    if ((it.innerText || '').trim().startsWith('新建节点')) { const r = it.getBoundingClientRect();
      return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; } } return null; });
if (!nj) { log('🔴 找不到「新建节点」'); await b.close(); process.exit(3); }
await p.mouse.move(nj.x, nj.y); await p.waitForTimeout(500);
await p.mouse.move(nj.x + 3, nj.y); await p.waitForTimeout(1500);
const target = await p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]')) {
    if (getComputedStyle(m).visibility === 'hidden') continue;
    for (const it of m.querySelectorAll('[role=menuitem]')) { if ((it.innerText || '').trim() !== '主体') continue;
      const r = it.getBoundingClientRect(); if (r.width < 1) continue;
      const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
      const h = document.elementFromPoint(cx, cy); if (!h || !(h === it || it.contains(h))) continue;
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; } }
  return { __err: 'no-clickable' }; });
log('「主体」落点：', JSON.stringify(target));
if (target.__err) { log('⛔ 中止'); await b.close(); process.exit(3); }
await p.mouse.click(target.rect[0] + target.rect[2] / 2, target.rect[1] + target.rect[3] / 2);
log('已点「主体」');

let SELF = null, guard = null;
for (let k = 1; k <= 16; k++) {
  await p.waitForTimeout(1200);
  const ids = await allIds();
  const diff = ids.filter((id) => !idsBefore.includes(id));
  if (diff.length === 1) { const sel = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
    guard = { diff, sel, ok: sel.includes(diff[0]) };
    if (guard.ok) { SELF = diff[0]; break; } }
  else if (diff.length > 1) { log(`  ⛔ 差集超过一个：${JSON.stringify(diff)}`); break; }
}
out.guard = guard; out.self = SELF;
log(`护栏②：${JSON.stringify(guard)} ⇒ ${SELF ? '✅ ' + SELF : '🔴'}`);
save();
if (!SELF) { log('🔴 没建出主体节点 ⇒ 中止'); await b.close(); process.exit(3); }

// ---- 读主体节点的结构，特别是**标题**那一行 ----
out.node = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  const rect = (e) => { const r = e.getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map(Math.round); };
  return { selected: n.classList.contains('selected'),
    inner: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160),
    rect: rect(n),
    tids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    inputs: Array.from(n.querySelectorAll('input,textarea,[contenteditable]')).map((e) => ({ tag: e.tagName,
      tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), type: e.getAttribute('type'),
      pe: getComputedStyle(e).pointerEvents, rect: rect(e) })),
    // 所有可能是「标题」的元素：testid=flow-node-title 及其后代
    titleEl: (() => { const t = n.querySelector('[data-testid="flow-node-title"]'); if (!t) return null;
      return { rect: rect(t), text: (t.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30),
        kids: Array.from(t.querySelectorAll('*')).map((k) => { const kr = k.getBoundingClientRect();
          return { tag: k.tagName, tid: k.getAttribute('data-testid'), aria: k.getAttribute('aria-label'),
            cls: (k.getAttribute('class') || '').toString().slice(0, 30), pe: getComputedStyle(k).pointerEvents,
            rect: [kr.x, kr.y, kr.width, kr.height].map(Math.round) }; }) }; })() };
}, SELF);
log('\n主体节点结构：'); log(JSON.stringify(out.node, null, 1));
save();

// ---- 焦点基线：点之前先读一次 ----
out.focusBefore = await readFocus('before-click');
log('\n点之前的焦点：', JSON.stringify({ tag: out.focusBefore.tag, tid: out.focusBefore.tid, aria: out.focusBefore.aria }));

// ---- 落点：在**标题元素内部**现算一个能命中的点 ----
const pt = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  // 标题 = flow-node-title（含它的子元素）
  const t = n.querySelector('[data-testid="flow-node-title"]');
  if (!t) return { __err: 'no-title' };
  const r = t.getBoundingClientRect();
  const cands = [];
  for (let y = Math.ceil(r.y); y < r.y + r.height; y += 2)
    for (let x = Math.ceil(r.x); x < r.x + r.width; x += 2) {
      if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
      const el = document.elementFromPoint(x, y);
      if (!el || !(el === t || t.contains(el))) continue;
      cands.push({ x, y, hit: el.tagName }); }
  return { n: cands.length, first: cands[0] || null, titleRect: [r.x, r.y, r.width, r.height].map(Math.round),
    titleText: (t.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) };
}, SELF);
out.titlePoint = pt;
log('\n标题内可用落点：', JSON.stringify(pt));
if (!pt.first) { log('  🔴 标题一个可点位置都没有 ⇒ 记录并中止'); save(); await b.close(); process.exit(4); }

// ---- 点它，然后立刻 + 稍后各读一次焦点（防止只抓到瞬时状态） ----
await p.mouse.click(pt.first.x, pt.first.y);
out.focusT0 = await readFocus('t+0ms');
await p.waitForTimeout(1500);
out.focusT1500 = await readFocus('t+1500ms');
await p.waitForTimeout(3000);
out.focusT4500 = await readFocus('t+4500ms');
log('\n=== 焦点读数 ===');
for (const k of ['focusBefore', 'focusT0', 'focusT1500', 'focusT4500']) {
  const f = out[k];
  log(`  ${k}: tag=${f.tag} tid=${f.tid} aria=${JSON.stringify(f.aria)} type=${f.type} 输入面=${f.isInputLike} value=${JSON.stringify(f.value)}`);
}
out.verdict = {
  标题文本: pt.titleText,
  落点: pt.first,
  自动获焦: !!out.focusT1500.isInputLike,
  获焦元素: out.focusT1500.aria || out.focusT1500.tid || out.focusT1500.tag,
  瞬时与稳定是否一致: (out.focusT0.isInputLike === out.focusT1500.isInputLike) && (out.focusT1500.isInputLike === out.focusT4500.isInputLike),
};
log('\n=== 判定 ==='); log(JSON.stringify(out.verdict, null, 1));
out.end = { nodes: await nodeN(), credits: await credits() };
log('终点：', JSON.stringify(out.end));
save();
log('\nDONE a');
process.exit(0);
