// 批次 118 · a 轮：读**主体节点**的浮动工具条（全册此前没有这一档）。
//
// 缺口：`use-node-toolbar.md` 覆盖了**六种**工具条 ——
//   文本（选中态/编辑态）、图片（有资源）、视频（有资源）、空节点（=生成面板）、
//   多选、编组。
//   **唯独没有「主体节点」这一档**。而批次 115 已经证明主体节点是自建得出的、
//   护栏跑通的一档 ⇒ 弹药现成。
//
// 🔑 读数要点（沿用批次 93/108 立下的契约）：
//   ① 面板 testid `node-toolbar` **覆盖两类东西**（生成面板 / 浮动工具条），
//      而且生成面板旁边还有一个**高度恒 0** 的同 testid 元素
//      ⇒ 必须按「面积最大且高度 > 1」筛，**不能用单数 querySelector**。
//   ② 尺寸契约：**屏上高度恒定、宽度随缩放变**（文本节点 40/40/40，宽 160/192/320）。
//      本轮读**屏上**读数并**换算成 canvas**（屏上 × 1/scale）。
//   ③ 按钮屏上**恒定** ⇒ 按钮才是真契约。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b118a.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return e ? e.getAttribute('aria-label') : null; });

// 浮动工具条读数：**按面积筛**，并把屏上尺寸换算成 canvas
const readToolbars = (lbl) => p.evaluate((l) => {
  const r = (e) => { const q = e.getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; };
  const all = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'));
  const tbs = all.map((e) => ({ e, q: e.getBoundingClientRect() }));
  const visible = tbs.filter((x) => x.q.width > 1 && x.q.height > 1);
  visible.sort((a, b) => b.q.width * b.q.height - a.q.width * a.q.height);
  return { at: Date.now(), lbl: l, nAll: all.length,
    nZeroHeight: tbs.filter((x) => x.q.height === 0).map((x) => ({ width: Math.round(x.q.width) })),
    toolbars: visible.map((x) => ({ rect: r(x.e), text: (x.e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120),
      cls: (x.e.getAttribute('class') || '').toString().slice(0, 40),
      svgs: x.e.querySelectorAll('svg').length,
      btns: Array.from(x.e.querySelectorAll('button,[role=button]')).map((e2) => ({ aria: e2.getAttribute('aria-label'),
        tid: e2.getAttribute('data-testid'), rect: r(e2) })).filter((y) => y.aria) })) };
}, lbl);

// 宿主节点自身：类型、testid、内部按钮
const readNode = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  const r = (e) => { const q = e.getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; };
  return { selected: n.classList.contains('selected'), clsType: (n.getAttribute('class') || '').toString().match(/react-flow__node-(\w+)/)?.[1] || null,
    rect: r(n), inner: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 100),
    tids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    ownBtns: Array.from(n.querySelectorAll('button,[role=button]')).map((e) => ({ aria: e.getAttribute('aria-label'), rect: r(e) })).filter((x) => x.aria) };
}, id);

out.start = { nodes: await nodeN(), credits: await credits(), zoom: await zoom() };
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

// ---- 造自建主体节点 ----
log('\n=== 造主体节点 ===');
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
    for (const it of m.querySelectorAll('[role=menuitem]')) { if ((it.innerText || '').trim() !== '主体') continue;
      const r = it.getBoundingClientRect(); if (r.width < 1) continue;
      const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
      const h = document.elementFromPoint(cx, cy); if (!h || !(h === it || it.contains(h))) continue;
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; } }
  return { __err: 'no-clickable' }; });
log('「主体」落点：', JSON.stringify(target));
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

// ---- 读工具条 ----
await p.waitForTimeout(1800);
out.zoomNow = await zoom();
out.node = await readNode(SELF);
out.tbSelected = await readToolbars('selected');
log('\n=== 节点 ==='); log(JSON.stringify({ clsType: out.node.clsType, rect: out.node.rect, inner: out.node.inner }, null, 1));
log('节点内部 testid（' + out.node.tids.length + '）：', JSON.stringify(out.node.tids));
log('\n=== 选中态工具条（zoom ' + out.zoomNow + '）===');
log('同 testid 元素总数：', out.tbSelected.nAll, '｜零高度元素：', JSON.stringify(out.tbSelected.nZeroHeight));
log('可见工具条数：', out.tbSelected.toolbars.length);
out.tbSelected.toolbars.forEach((t, i) => {
  log(`  #${i} ${JSON.stringify(t.rect)}｜class ${JSON.stringify(t.cls)}｜svg ${t.svgs}`);
  log(`     text  ${JSON.stringify(t.text)}`);
  log(`     按钮 ${t.btns.length} 个：${JSON.stringify(t.btns.map((x) => x.aria))}`);
  t.btns.forEach((x) => log(`        ${JSON.stringify(x.aria)} ${JSON.stringify(x.rect)} tid=${x.tid}`));
});
save();

// ---- 取消选中：工具条应消失 ----
log('\n=== 取消选中（对照：工具条应消失）===');
const reloc2 = await p.evaluate(() => {
  const bad = (x, y) => { const el = document.elementFromPoint(x, y);
    if (!el || el.closest('.react-flow__node')) return true;
    if (x < 200 || y < 60 || y > 630 || x > 1120) return true;
    if (el.closest('button,[role=button],input,a,[contenteditable]')) return true;
    if (el.closest('[role="menu"],[data-testid="node-toolbar"]')) return true; return false; };
  for (let y = 280; y < 630; y += 12) for (let x = 260; x < 1100; x += 12) if (!bad(x, y)) return { x, y }; return null; });
if (reloc2) { await p.mouse.click(reloc2.x, reloc2.y); await p.waitForTimeout(1600); }
out.tbUnselected = await readToolbars('unselected');
log('同 testid 元素总数：', out.tbUnselected.nAll, '｜可见工具条数：', out.tbUnselected.toolbars.length);
out.tbUnselected.toolbars.forEach((t, i) => log(`  #${i} ${JSON.stringify(t.rect)} 按钮 ${JSON.stringify(t.btns.map((x) => x.aria))}`));
save();

// ---- 三档缩放读数（验证「高度恒定、按钮恒定」） ----
log('\n=== 三档缩放读数 ===');
out.zoomTiers = [];
for (const pct of ['40', '60', '100']) {
  const z = await zoom();
  if (z && z.includes(`${pct}%`)) { log(`  ${pct}%：已是，跳过`); continue; }
  const r = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
    const q = e.getBoundingClientRect(); return [Math.round(q.x + q.width / 2), Math.round(q.y + q.height / 2)]; });
  await p.mouse.click(r[0], r[1]); await p.waitForTimeout(800);
  const inp = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent-input"]'); if (!e) return null;
    const q = e.getBoundingClientRect(); return [Math.round(q.x + q.width / 2), Math.round(q.y + q.height / 2)]; });
  if (!inp) { log(`  ${pct}%：输入框没出现`); continue; }
  await p.mouse.click(inp[0], inp[1]); await p.waitForTimeout(350);
  await p.keyboard.press('Meta+a'); await p.waitForTimeout(150);
  await p.keyboard.type(pct, { delay: 100 }); await p.waitForTimeout(400);
  await p.keyboard.press('Enter'); await p.waitForTimeout(1800);
  // 缩放会取消选中 ⇒ 重新选中宿主
  let sel = await p.evaluate((i) => document.querySelector(`.react-flow__node[data-id="${i}"]`)?.classList.contains('selected'), SELF);
  if (!sel) {
    const pt = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
      const q = n.getBoundingClientRect();
      for (let y = Math.ceil(q.y) + 6; y < q.y + q.height - 6; y += 5)
        for (let x = Math.ceil(q.x) + 6; x < q.x + q.width - 6; x += 5) { if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
          const el = document.elementFromPoint(x, y); if (el && (el === n || n.contains(el))) return { x, y }; }
      return null; }, SELF);
    if (pt) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1600); }
  }
  const z2 = await zoom();
  const tb = await readToolbars('zoom-' + pct);
  const main = tb.toolbars[0];
  out.zoomTiers.push({ pct, zoom: z2, nAll: tb.nAll, rect: main && main.rect, text: main && main.text,
    btns: main ? main.btns.map((x) => ({ aria: x.aria, rect: x.rect })) : null,
    zeroH: tb.nZeroHeight });
  log(`  ${pct}% → 实际 ${z2}｜工具条 ${JSON.stringify(main && main.rect)}`);
  log(`     按钮：${JSON.stringify(main && main.btns.map((x) => `${x.aria} ${x.rect[2]}×${x.rect[3]}`))}`);
  log(`     零高度同 testid 元素：${JSON.stringify(tb.nZeroHeight)}`);
}
out.end = { nodes: await nodeN(), credits: await credits() };
log('\n终点：', JSON.stringify(out.end));
save();
log('\nDONE a');
process.exit(0);
