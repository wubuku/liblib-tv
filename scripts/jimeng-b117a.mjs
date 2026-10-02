// 批次 117 · a 轮：验**文本节点的行内改名**到底有没有可行路径。
//
// 老账（`edit-text-node.md:104`，批次 80 记，2026-10-02）：
//   「🔴 **订正（批次 80）**：本页此前写「点击后标题变为输入框，改名后回车提交」—— **未复现**。
//    2026-10-02 试了三种点法，**没有任何一种让标题变成输入框**：
//    ① 单击 Rename 钮；② 再单击一次；③ **双击标题行**。
//    三次之后全文档都**没有**出现 input / textarea / contenteditable
//    （只有两个 type=file 的隐藏上传框），焦点仍停在 Rename 钮上。
//    ⇒ 本页**不给出行内改名的可行路径**，因为没找到。」
//
// 🔑 批次 115 撞出的差别让这条老账**值得重测**：
//   批次 115 在**主体节点**上测到 —— **单击** `Rename` 按钮**不**进编辑态，
//   而**双击那个按钮**、或单击后按 **Enter/Space**，**都**进编辑态
//   （`INPUT aria="Node title"`）。
//   ⇒ 批次 80 试的「**双击标题行**」和批次 115 试的「**双击 Rename 按钮**」
//   **不是同一个落点**。手册写「没找到」时，试的落点可能就少了这一种。
//
// 本轮把**五种点法**各做一遍（批次 80 试过的三种**照做一遍当对照**）：
//   ① 单击 `Rename` 钮            （批次 80 的 ①）
//   ② 再单击一次                  （批次 80 的 ②）
//   ③ 双击**标题行**（非按钮）      （批次 80 的 ③）—— 对照组
//   ④ **双击 `Rename` 钮**         ← **批次 80 没试过的那一种**
//   ⑤ 单击 `Rename` 钮 → **Enter**
//   ⑥ 单击 `Rename` 钮 → **Space**
// 每种都连读三次焦点（+0 / +1.2s / +3.7s，三次全一致才算数），
// 并同时读「全文档有没有新增 input / textarea / contenteditable」。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b117a.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);

// 读焦点 + 读**全文档**的输入面（不限于节点内 —— 批次 80 就是「全文档都没有」）
const readFocus = (lbl) => p.evaluate((l) => {
  const a = document.activeElement; if (!a) return { at: Date.now(), lbl: l, tag: null };
  return { at: Date.now(), lbl: l, tag: a.tagName, tid: a.getAttribute('data-testid'),
    aria: a.getAttribute('aria-label'), type: a.getAttribute('type'),
    isInputLike: a.tagName === 'INPUT' || a.tagName === 'TEXTAREA' || a.isContentEditable === true,
    value: a.value !== undefined ? String(a.value) : null,
    inNode: !!(a.closest && a.closest('.react-flow__node')) };
}, lbl);
const readDocInputs = () => p.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 || r.height > 0 || e.offsetParent !== null; };
  return Array.from(document.querySelectorAll('input,textarea,[contenteditable]')).map((e) => { const r = e.getBoundingClientRect();
    return { tag: e.tagName, tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
      type: e.getAttribute('type'), pe: getComputedStyle(e).pointerEvents, ce: e.isContentEditable === true,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      inNode: !!e.closest('.react-flow__node'), inToolbar: !!e.closest('[data-testid="node-toolbar"]'),
      value: e.value !== undefined ? String(e.value) : null }; });
});

out.start = { nodes: await nodeN(), credits: await credits() };
log('起点：', JSON.stringify(out.start));
const reloc = await p.evaluate(() => {
  const bad = (x, y) => { const el = document.elementFromPoint(x, y);
    if (!el || el.closest('.react-flow__node')) return true;
    if (x < 200 || y < 60 || y > 630 || x > 1120) return true;
    if (el.closest('button,[role=button],input,a,[contenteditable]')) return true;
    if (el.closest('[role="menu"],[data-testid="node-toolbar"]')) return true; return false; };
  for (let y = 280; y < 630; y += 12) for (let x = 260; x < 1100; x += 12) if (!bad(x, y)) return { x, y }; return null; });
if (reloc) { await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  await p.mouse.click(reloc.x, reloc.y); await p.waitForTimeout(1200); }
const g0 = await keyGuard(p);
log('焦点守卫：', g0.safe ? '✅' : '⛔', g0.where || '');
if (!g0.safe) { log('⛔ 中止'); await b.close(); process.exit(2); }

// ---- 造一个自建文本节点 ----
log('\n=== 造文本节点 ===');
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
    for (const it of m.querySelectorAll('[role=menuitem]')) { if ((it.innerText || '').trim() !== '文本') continue;
      const r = it.getBoundingClientRect(); if (r.width < 1) continue;
      const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
      const h = document.elementFromPoint(cx, cy); if (!h || !(h === it || it.contains(h))) continue;
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; } }
  return { __err: 'no-clickable' }; });
log('「文本」落点：', JSON.stringify(target));
if (target.__err) { log('⛔ 中止'); await b.close(); process.exit(3); }
await p.mouse.click(target.rect[0] + target.rect[2] / 2, target.rect[1] + target.rect[3] / 2);

let SELF = null, guard = null;
for (let k = 1; k <= 16; k++) {
  await p.waitForTimeout(1200);
  const ids = await allIds();
  const diff = ids.filter((id) => !idsBefore.includes(id));
  if (diff.length === 1) { const sel = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
    guard = { diff, sel, ok: sel.includes(diff[0]) }; if (guard.ok) { SELF = diff[0]; break; } }
  else if (diff.length > 1) { log(`  ⛔ 差集超过一个：${JSON.stringify(diff)}`); break; }
}
out.guard = guard; out.self = SELF;
log(`护栏②：${JSON.stringify(guard)} ⇒ ${SELF ? '✅ ' + SELF : '🔴'}`);
save();
if (!SELF) { log('🔴 中止'); await b.close(); process.exit(3); }

// ---- 读节点结构：标题行 + Rename 按钮 ----
out.node = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  const rect = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; };
  const t = n.querySelector('[data-testid="flow-node-title"]');
  return { selected: n.classList.contains('selected'), inner: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120),
    rect: rect(n), tids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    title: t ? { rect: rect(t), text: (t.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
      kids: Array.from(t.querySelectorAll('*')).map((k) => ({ tag: k.tagName, aria: k.getAttribute('aria-label'),
        cls: (k.getAttribute('class') || '').toString().slice(0, 26), rect: rect(k) })) } : null,
    btns: Array.from(n.querySelectorAll('button,[role=button]')).map((e) => ({ aria: e.getAttribute('aria-label'), rect: rect(e) })).filter((x) => x.aria) };
}, SELF);
log('\n节点结构：'); log(JSON.stringify(out.node, null, 1));
out.docInputsBefore = await readDocInputs();
log('\n操作前全文档输入面：', JSON.stringify(out.docInputsBefore));
save();

// ---- 落点现算：Rename 按钮 / 标题行（不含按钮的区域） ----
const ptRename = () => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  const btn = Array.from(n.querySelectorAll('button,[role=button]')).find((e) => /^Rename\b/.test(e.getAttribute('aria-label') || ''));
  if (!btn) return { __err: 'no-rename' };
  const r = btn.getBoundingClientRect();
  for (let y = Math.ceil(r.y); y < r.y + r.height; y += 2)
    for (let x = Math.ceil(r.x); x < r.x + r.width; x += 2) { if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
      const el = document.elementFromPoint(x, y); if (el && (el === btn || btn.contains(el)))
        return { x, y, aria: btn.getAttribute('aria-label'), rect: [r.x, r.y, r.width, r.height].map(Math.round) }; }
  return { __err: 'no-clickable', rect: [r.x, r.y, r.width, r.height].map(Math.round) }; }, SELF);
const ptTitleNotBtn = () => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  const t = n.querySelector('[data-testid="flow-node-title"]'); if (!t) return { __err: 'no-title' };
  const btn = Array.from(n.querySelectorAll('button')).find((e) => /^Rename\b/.test(e.getAttribute('aria-label') || ''));
  const r = t.getBoundingClientRect(), br = btn ? btn.getBoundingClientRect() : null;
  // 标题行里、**避开 Rename 按钮** 的点
  for (let y = Math.ceil(r.y); y < r.y + r.height; y += 2)
    for (let x = Math.ceil(r.x); x < r.x + r.width; x += 2) { if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
      if (br && x >= br.left - 2 && x <= br.right + 2 && y >= br.top - 2 && y <= br.bottom + 2) continue;
      const el = document.elementFromPoint(x, y); if (el && (el === t || t.contains(el))) return { x, y, titleRect: [r.x, r.y, r.width, r.height].map(Math.round) }; }
  return { __err: 'no-point-outside-btn' }; }, SELF);

out.trials = [];
async function trial(tag, act) {
  log(`\n──────── ${tag} ────────`);
  const before = await readDocInputs();
  const fBefore = await readFocus(tag + '-before');
  const r = await act();
  const t0 = await readFocus(tag + '-t0');
  await p.waitForTimeout(1200);
  const t1 = await readFocus(tag + '-t1.2s');
  await p.waitForTimeout(2500);
  const t2 = await readFocus(tag + '-t+3.7s');
  const after = await readDocInputs();
  const added = after.filter((a) => !before.some((b2) => b2.tag === a.tag && b2.rect.join() === a.rect.join() && b2.aria === a.aria));
  const rec = { tag, act: r || null, fBefore, t0, t1, t2, nInputsBefore: before.length, nInputsAfter: after.length,
    added, 进编辑态: t2.isInputLike, 三次一致: t0.isInputLike === t1.isInputLike && t1.isInputLike === t2.isInputLike,
    焦点: t2.aria || t2.tag, 全部输入面: after };
  out.trials.push(rec);
  log('  焦点 t0/t1.2s/t3.7s：', t0.tag, JSON.stringify(t0.aria || ''), '｜输入面', t0.isInputLike, '/', t1.isInputLike, '/', t2.isInputLike);
  log('  全文档输入面：', before.length, '→', after.length, after.length > before.length ? `｜新增 ${JSON.stringify(added)}` : '（无新增）');
  if (after.length) log('  现有：', JSON.stringify(after));
  save();
  return rec;
}

// ① 单击 Rename 钮（批次 80 的 ①）
await trial('①单击Rename钮', async () => { const pt = await ptRename(); log('  落点：', JSON.stringify(pt));
  if (pt.__err) return pt; await p.mouse.click(pt.x, pt.y); return pt; });
// ② 再单击一次（批次 80 的 ②）
await trial('②再单击一次', async () => { const pt = await ptRename(); if (pt.__err) return pt;
  await p.mouse.click(pt.x, pt.y); return pt; });
// ③ 双击**标题行**（避开 Rename 按钮）—— 批次 80 的 ③，对照组
await trial('③双击标题行(避开按钮)', async () => { const pt = await ptTitleNotBtn(); log('  落点：', JSON.stringify(pt));
  if (pt.__err) return pt; await p.mouse.dblclick(pt.x, pt.y); return pt; });
// ④ 双击 **Rename 钮** —— 批次 80 没试过的那一种
await trial('④双击Rename钮', async () => { const pt = await ptRename(); log('  落点：', JSON.stringify(pt));
  if (pt.__err) return pt; await p.mouse.dblclick(pt.x, pt.y); return pt; });
// ⑤ 单击 Rename 钮 → Enter
await trial('⑤单击后Enter', async () => { const pt = await ptRename(); if (pt.__err) return pt;
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(800);
  const g = await keyGuard(p); log('  按 Enter 前守卫：', g.safe ? '✅' : 'ⓘ', g.where || '');
  await p.keyboard.press('Enter'); return { pt, guard: { safe: g.safe, where: g.where } }; });
// ⑥ 单击 Rename 钮 → Space
await trial('⑥单击后Space', async () => { const pt = await ptRename(); if (pt.__err) return pt;
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(800);
  await p.keyboard.press(' '); return pt; });

out.verdict = out.trials.map((t) => ({ 试: t.tag, 进编辑态: t.进编辑态, 焦点: t.焦点,
  新增输入面: t.added.length, 输入面总数: t.nInputsAfter, 三次一致: t.三次一致 }));
log('\n=== 判定汇总 ==='); log(JSON.stringify(out.verdict, null, 1));
out.anyEntered = out.trials.filter((t) => t.进编辑态).map((t) => t.tag);
log('\n  ⇒ 进入编辑态的操作：', JSON.stringify(out.anyEntered));
out.end = { nodes: await nodeN(), credits: await credits() };
log('终点：', JSON.stringify(out.end));
save();
log('\nDONE a');
process.exit(0);
