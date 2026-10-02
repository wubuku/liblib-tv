// 批次 107 · d 轮：进文本编辑态，把 **⌘⌥1 / ⌘⌥2 / ⌘⌥3 / ⌘⌥0** 逐个测全。
//
// 前两轮的翻车记录（判据，不是产品）：
//   b 轮：`keyGuard` 放行（焦点 BODY、0 个可见输入面），按 `f` 之后
//         `text-editor-fullscreen-dialog` **没出现** ⇒ **F 在本节点上没开出编辑器**，
//         单独记为一条观测，**不与「标题有没有生效」混在一起**。
//   c 轮：我按 testid 找 `canvas-editor-menu`，找到的那个 **`owner=elsewhere`
//         （1079,30，在顶栏）**，是**顶栏那个**编辑钮，不是节点自己的 —— 点错了地方。
//         ⇒ **testid 相同不等于同一个东西**（又一条老教训）。
//         本轮改走 `edit-text-node.md:18/25/173` 写明的两条正路：
//         **双击节点主体** / **在已选中的节点上再单击一次**。
//
// 🔴 判据（沿用批次 105/106 的教训）：
//   「⌘⌥3 生效了」只能看**目标那一行自己的渲染结果**（标签名/class/字号/字重）。
//   **不能**看 innerText（文字本来就在那儿）、**不能**看「页面上有没有 h3」。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), selfId: 'node_gmvz7secas' };
const SELF = out.selfId;
const save = () => writeFileSync(new URL('./_tmp-b107d.json', import.meta.url), JSON.stringify(out, null, 1));

const safeEval = async (fn, arg, tries = 8) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

// 只认**我那个节点里**的编辑面
const editState = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const ce = Array.from(n.querySelectorAll('[contenteditable="true"],textarea')).map((e) => {
    const q = e.getBoundingClientRect();
    return { tag: e.tagName, tid: e.getAttribute('data-testid'), cls: (e.className || '').toString().slice(0, 40),
      w: Math.round(q.width), h: Math.round(q.height), x: Math.round(q.x), y: Math.round(q.y),
      focused: e === document.activeElement || e.contains(document.activeElement) };
  });
  // 编辑态才有的 8 钮工具条
  const bar = n.querySelector('[data-testid="node-toolbar"]') || (() => {
    const cand = Array.from(document.querySelectorAll('[data-testid]'))
      .filter((e) => /toolbar/i.test(e.getAttribute('data-testid') || ''));
    let best = null;
    for (const c of cand) if (n.contains(c) || cand.length === 1) { best = c; break; }
    return best;
  })();
  return { ce, n: ce.length,
    toolbarAria: bar ? Array.from(bar.querySelectorAll('button,[role=button]')).map((e) => e.getAttribute('aria-label') || (e.innerText || '').trim()).filter(Boolean) : null,
    active: (() => { const a = document.activeElement; return a ? `${a.tagName}[${a.getAttribute('data-testid') || ''}]` : null; })(),
    sel: n.classList.contains('selected') };
}, SELF);

// 目标行「普通正文行。」在编辑面里的**渲染读数**（判据本体）
const lineInfo = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const host = n && Array.from(n.querySelectorAll('[contenteditable="true"],textarea'))
    .find((e) => e.getBoundingClientRect().width > 30);
  if (!host) return { __err: 'no-editor' };
  // 找到含目标文字的那个最内层元素
  const TARGET = '普通正文行';
  let hit = null;
  const all = [host, ...Array.from(host.querySelectorAll('*'))];
  for (const e of all) {
    const t = (e.innerText || e.value || '');
    if (t.includes(TARGET)) { if (!hit || e.contains(hit)) hit = e; }
  }
  if (!hit) return { __err: 'target-not-found', sample: (host.innerText || '').replace(/\s+/g, ' ').slice(0, 120) };
  const cs = getComputedStyle(hit);
  const q = hit.getBoundingClientRect();
  return { tag: hit.tagName, cls: (hit.className || '').toString().slice(0, 60),
    fs: cs.fontSize, fw: cs.fontWeight, lh: cs.lineHeight,
    box: `${Math.round(q.x)},${Math.round(q.y)} ${Math.round(q.width)}×${Math.round(q.height)}`,
    parentTag: hit.parentElement ? hit.parentElement.tagName : null,
    parentCls: hit.parentElement ? (hit.parentElement.className || '').toString().slice(0, 50) : null,
    outerHTML: hit.outerHTML.replace(/\s+/g, ' ').slice(0, 220) };
}, SELF);

out.s0 = await editState();
log('起点：', JSON.stringify(out.s0));

// ---- 进编辑态：双击节点主体（避开标题行） ----
const spot = await safeEval((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  const others = Array.from(document.querySelectorAll('.react-flow__node')).filter((e) => e.getAttribute('data-id') !== i)
    .map((e) => { const q = e.getBoundingClientRect(); return { x: q.x, y: q.y, w: q.width, h: q.height }; });
  for (let fy = 0.35; fy <= 0.8; fy += 0.1) for (let fx = 0.2; fx <= 0.8; fx += 0.1) {
    const x = r.x + r.width * fx, y = r.y + r.height * fy;
    if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
    const el = document.elementFromPoint(x, y);
    if (!el || !(el === n || n.contains(el))) continue;
    if (others.some((o) => x >= o.x && x <= o.x + o.w && y >= o.y && y <= o.y + o.h)) continue;
    return { x: Math.round(x), y: Math.round(y), fx, fy, top: el.tagName };
  }
  return { __err: 'no-safe-spot' };
}, SELF);
out.spot = spot;
log('\n落点：', JSON.stringify(spot));
if (spot.__err) { log('🔴 没有安全落点，停止'); save(); await b.close(); process.exit(1); }
await p.mouse.move(spot.x, spot.y); await p.waitForTimeout(400);
await p.mouse.dblclick(spot.x, spot.y);
await p.waitForTimeout(1800);
out.s1 = await editState();
log('双击后：', JSON.stringify(out.s1, null, 1));
out.inEdit = out.s1.n > 0;
log('进入编辑态 =', out.inEdit ? '✅' : '🔴');
save();
if (!out.inEdit) { log('🔴 没进编辑态，停止'); await b.close(); process.exit(1); }

// ---- 点进目标行，再逐个按快捷键 ----
const target = await safeEval((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const host = n && Array.from(n.querySelectorAll('[contenteditable="true"],textarea'))
    .find((e) => e.getBoundingClientRect().width > 30);
  if (!host) return { __err: 'no-editor' };
  const all = [host, ...Array.from(host.querySelectorAll('*'))];
  let hit = null;
  for (const e of all) { const t = (e.innerText || e.value || ''); if (t.includes('普通正文行')) { if (!hit || e.contains(hit)) hit = e; } }
  if (!hit) return { __err: 'target-not-found' };
  const q = hit.getBoundingClientRect();
  return { x: Math.round(q.x + q.width / 2), y: Math.round(q.y + q.height / 2), w: Math.round(q.width), h: Math.round(q.height) };
}, SELF);
out.target = target;
log('\n目标行位置：', JSON.stringify(target));
if (!target.__err) { await p.mouse.click(target.x, target.y); await p.waitForTimeout(900); }

out.base = await lineInfo();
log('\n基线（未按）：', JSON.stringify(out.base, null, 1));

out.steps = [];
for (const [key, label, combo] of [['h1', '一级标题', 'Meta+Alt+1'], ['h2', '二级标题', 'Meta+Alt+2'], ['h3', '三级标题', 'Meta+Alt+3'], ['p', '普通文本', 'Meta+Alt+0']]) {
  if (target && !target.__err) { await p.mouse.click(target.x, target.y); await p.waitForTimeout(700); } // 每次重新落光标
  const g = await keyGuard(p);
  if (!g.safe) { log(`\n>>> ${label}：🔴 keyGuard 拒绝（${g.reason}）`); out.steps.push({ key, label, refused: g.reason }); save(); continue; }
  log(`\n>>> 按 ${combo}（${label}）｜ keyGuard: ${g.where}`);
  const before = await lineInfo();
  await p.keyboard.press(combo);
  await p.waitForTimeout(1100);
  const after = await lineInfo();
  const rec = { key, label, combo, guard: g.where, before, after,
    changed: JSON.stringify({ t: before.tag, c: before.cls, f: before.fs, w: before.fw })
      !== JSON.stringify({ t: after.tag, c: after.cls, f: after.fs, w: after.fw }) };
  out.steps.push(rec);
  log('   前：', JSON.stringify({ tag: before.tag, cls: before.cls, fs: before.fs, fw: before.fw }));
  log('   后：', JSON.stringify({ tag: after.tag, cls: after.cls, fs: after.fs, fw: after.fw }));
  log('   变了 =', rec.changed ? '✅' : '🔴 无变化');
  save();
}

out.endState = await editState();
log('\n终点：', JSON.stringify(out.endState));
save();
log('已落盘');
await b.close();
