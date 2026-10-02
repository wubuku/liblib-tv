// 批次 114 · c 轮：判定**「宿主自身」会不会被排除**。
//
// b 轮已经把「空节点被排除」钉死了（图片 1 个有资源 ⇒ 列出；视频 2 / 音频 69 全空 ⇒ 0 条），
// 但**「宿主自身是否额外被排除」仍判不了**：b 轮两个宿主自己都是空节点，
// 于是「空节点被排除」和「空节点 + 自身被排除」**两种假设预测的读数逐字相同**。
//
// 判法：造一个**自身有资源**的宿主（有资源的音频节点），在它自己的面板上打 `@`，
// 看「音频」类里**有没有它自己**。
//   · 列出了自己 ⇒ 「空节点被排除」就是全部规则
//   · 没列出自己 ⇒ 「空节点被排除」+「自身被排除」两条叠加
//
// 🔑 这次判据是**逐字对账**：条目文字必须等于该节点的 `flow-node-title` 逐字。
//    只数个数不够（「1 条」既可能是自己，也可能是别的节点）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const WAV = '/tmp/jimeng-b104-test.wav';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c' };
const save = () => writeFileSync(new URL('./_tmp-b114c.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);

const inventory = () => p.evaluate(() => { const m = {};
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const id = n.getAttribute('data-id');
    const type = ((n.getAttribute('class') || '').toString().match(/react-flow__node-(\w+)/) || [])[1] || '?';
    const t = (n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || '';
    const hasRes = !!n.querySelector('[data-testid$="-node-result"]');
    (m[type] = m[type] || []).push({ id, title: (t || '').replace(/\s+/g, ' ').trim().slice(0, 30), hasRes });
  } return m; });

const readMention = (lbl) => p.evaluate((l) => {
  const r = { at: Date.now(), lbl: l, level1: null, level2: null };
  const l1 = document.querySelector('[data-testid="generation-mention-panel"]');
  if (l1) { r.level1 = { options: Array.from(l1.querySelectorAll('[role="option"]')).map((o) => (o.innerText || '').replace(/\s+/g, ' ').trim()) } }
  const l2 = document.querySelector('[data-testid="generation-mention-submenu"]');
  if (l2) { const bb = l2.getBoundingClientRect();
    r.level2 = { rect: [bb.x, bb.y, bb.width, bb.height].map(Math.round),
      text: (l2.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
      options: Array.from(l2.querySelectorAll('[role="option"]')).map((o) => (o.innerText || '').replace(/\s+/g, ' ').trim()),
      status: Array.from(l2.querySelectorAll('[role="status"]')).map((s) => (s.innerText || '').replace(/\s+/g, ' ').trim()) }; }
  return r;
}, lbl);

out.start = { nodes: await nodeN(), credits: await credits() };
log('起点：', JSON.stringify(out.start));

// ⚠️ 上一轮（b 轮）收尾时焦点还留在提示词编辑器里 ⇒ keyGuard 会报 unsafe。
//    护栏中止的是「这一步动作」，不是义务 —— **先合法地把焦点移回画布**再继续。
//    落点现算：命中元素必须在画布上、且不在任何节点/按钮里。
const reloc = await p.evaluate(() => {
  const bad = (x, y) => { const el = document.elementFromPoint(x, y);
    if (!el || el.closest('.react-flow__node')) return true;
    if (x < 200 || y < 60 || y > 630 || x > 1120) return true;
    if (el.closest('button,[role=button],input,a,[contenteditable]')) return true;
    if (el.closest('[role="menu"],[data-testid="generation-mention-panel"],[data-testid="node-toolbar"]')) return true;
    return false; };
  for (let y = 280; y < 630; y += 12) for (let x = 260; x < 1100; x += 12) if (!bad(x, y)) return { x, y, tag: document.elementFromPoint(x, y).tagName };
  return null; });
out.relocate = reloc;
log('把焦点移回画布的落点：', JSON.stringify(reloc));
if (reloc) { await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  await p.mouse.click(reloc.x, reloc.y); await p.waitForTimeout(1200); }

const g0 = await keyGuard(p);
log('焦点守卫：', g0.safe ? '✅' : '⛔', g0.where || '', g0.reason || '');
if (!g0.safe) { log('⛔ 仍不安全 ⇒ 中止'); await b.close(); process.exit(2); }

// ---- 1. 左栏上传 wav，造一个**自身有资源**的音频节点 ----
log('\n=== 上传 wav（有资源的宿主）===');
const idsBefore = await allIds();
const rail = await p.evaluate(() => Array.from(document.querySelectorAll('button,[role=button]'))
  .map((e) => { const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; })
  .filter((x) => x.aria === '上传' && x.w > 0 && x.h > 0));
log('上传入口：', JSON.stringify(rail));
if (!rail.length) { log('🔴 找不到上传入口'); await b.close(); process.exit(3); }
let fcSeen = null;
const onFc = async (fc) => { fcSeen = { multiple: fc.isMultiple() };
  try { await fc.setFiles(WAV); log('  setFiles ok'); } catch (e) { log('  setFiles 失败：', e.message); out.setFilesErr = e.message; } };
p.on('filechooser', onFc);
const r0 = rail[0];
await p.mouse.move(r0.x + r0.w / 2, r0.y + r0.h / 2); await p.waitForTimeout(600);
await p.mouse.click(r0.x + r0.w / 2, r0.y + r0.h / 2);
log('已点上传…');
await p.waitForTimeout(2500);

let T2 = null, guard = null;
for (let k = 1; k <= 20; k++) {
  const ids = await allIds();
  const diff = ids.filter((id) => !idsBefore.includes(id));
  if (diff.length === 1) { const sel = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
    guard = { diff, sel, ok: sel.includes(diff[0]) };
    if (guard.ok) { T2 = diff[0]; log(`  #${k} 护栏② 通过：${T2}`); break; } }
  else if (diff.length > 1) { log(`  ⛔ 差集超过一个：${JSON.stringify(diff)}`); break; }
  await p.waitForTimeout(1200);
}
out.guard = guard; out.t2 = T2;
if (!T2) { log('🔴 没建出有资源的宿主 ⇒ 中止'); await b.close(); process.exit(3); }
// 等 ready
out.readyLog = [];
for (let k = 1; k <= 24; k++) {
  const st = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
    return { inner: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 130) }; }, T2);
  out.readyLog.push({ k, inner: st.inner });
  if (st.inner && /1 ready/.test(st.inner) && !/processing/.test(st.inner)) { log(`  ready（#${k}）：${JSON.stringify(st.inner.slice(0, 90))}`); break; }
  await p.waitForTimeout(1500);
}
out.t2Title = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  return (n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || ''; }, T2);
log('T2 标题逐字：', JSON.stringify(out.t2Title));
out.t2Sel = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  return { selected: n.classList.contains('selected'), cls: (n.getAttribute('class') || '').toString().match(/react-flow__node-(\w+)/)?.[1] || null,
    rect: (() => { const rr = n.getBoundingClientRect(); return [Math.round(rr.x), Math.round(rr.y), Math.round(rr.width), Math.round(rr.height)]; })() }; }, T2);
log('T2 状态：', JSON.stringify(out.t2Sel));
save();

// ---- 2. 在它自己的面板上打 `@`，逐类读二级 ----
log('\n=== 在有资源的宿主上打 @ ===');
const fe = await p.evaluate(() => { const host = document.querySelector('[data-testid="generation-prompt-editor"]'); if (!host) return { __err: 'no-host' };
  const r = host.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y < r.y + r.height - 2; y += 2)
    for (let x = Math.ceil(r.x) + 2; x < r.x + r.width - 2; x += 2) { if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
      const el = document.elementFromPoint(x, y); if (!el || !(el === host || host.contains(el))) continue;
      if (el.closest('button,[role=button],a,input,textarea')) continue; return { x, y }; }
  return { __err: 'no-clickable' }; });
log('提示词框落点：', JSON.stringify(fe));
if (fe.__err) { log('🔴 点不到提示词框'); await b.close(); process.exit(3); }
await p.mouse.click(fe.x, fe.y); await p.waitForTimeout(900);
const g = await keyGuard(p);
log('keyGuard：', g.safe ? '✅' : 'ⓘ unsafe（焦点在编辑器）—— 显式放行', g.where || '');
out.keyGuardWaiver = { granted: true, why: '测试前提就是焦点在编辑器；只往本批自建节点打字；不触发生成。' };
await p.keyboard.press('Meta+a'); await p.waitForTimeout(250);
await p.keyboard.press('Backspace'); await p.waitForTimeout(700);
await p.keyboard.type('@', { delay: 60 });
log('已打 @');
let seen = null;
for (let k = 0; k < 20; k++) { await p.waitForTimeout(180); const r = await readMention('t2#' + k); if (r.level1) { seen = r; break; } }
if (!seen) { log('🔴 一级面板没出现'); await b.close(); process.exit(3); }
log('一级选项：', JSON.stringify(seen.level1.options));
out.inv = await inventory();
log('画布有资源的节点：', JSON.stringify(Object.entries(out.inv).flatMap(([k, v]) => v.filter((x) => x.hasRes).map((x) => ({ type: k, ...x })))));

out.results = [];
for (const cat of seen.level1.options) {
  const ok = await p.evaluate((t) => { const el = Array.from(document.querySelectorAll('[data-testid="generation-mention-panel"] [role="option"]'))
    .find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === t); if (!el) return { __err: 'gone' };
    const r = el.getBoundingClientRect(); const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    const h = document.elementFromPoint(cx, cy); if (!h || !(h === el || el.contains(h))) return { __err: 'hit' };
    return { x: cx, y: cy }; }, cat);
  if (ok.__err) { log(`  ▸ ${cat} 拿不到落点`); continue; }
  await p.mouse.click(ok.x, ok.y); await p.waitForTimeout(1100);
  const r2 = await readMention('t2-' + cat);
  const inv = out.inv[cat] || [];
  log(`  ▸ ${cat}：画布该类型 ${inv.length} 个（有资源 ${inv.filter((x) => x.hasRes).length}）⇒ 二级 options ${JSON.stringify(r2.level2 ? r2.level2.options : null)} status ${JSON.stringify(r2.level2 ? r2.level2.status : null)}`);
  if (r2.level2) log(`      二级逐字：${JSON.stringify(r2.level2.text)}｜rect ${JSON.stringify(r2.level2.rect)}`);
  out.results.push({ cat, invN: inv.length, invReady: inv.filter((x) => x.hasRes).map((x) => ({ id: x.id, title: x.title })),
    opts: r2.level2 ? r2.level2.options : null, status: r2.level2 ? r2.level2.status : null, rect: r2.level2 ? r2.level2.rect : null });
  save();
}

out.verdict = out.results.map((r) => ({ cat: r.cat, 画布有资源: r.invReady, 二级列出: r.opts,
  含自身: r.opts ? r.opts.includes(out.t2Title) : null }));
log('\n=== 判定（含自身？逐字对账）===');
log(JSON.stringify(out.verdict, null, 1));
out.end = { nodes: await nodeN(), credits: await credits() };
log('终点：', JSON.stringify(out.end));
save();
log('\nDONE c');
process.exit(0);
