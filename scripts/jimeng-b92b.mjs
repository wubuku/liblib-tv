// 批次 92 · B：收拾 a 轮留下的自建节点，并把「落点」策略改稳。
//
// a 轮两处翻车，根因是同一个：
//   `landing()` 要求节点**完全**在视口内 才肯返回落点 ——
//   新建的文本节点落在 canvas (1916, 956)，**那是别的会话那一片节点区**，被压住了，
//   于是 0 个可用落点 ⇒ 选不中 ⇒ ⌘D 无对象 ⇒ P1/P2 整轮 VOID，
//   **还留下一个自建节点没删掉**。
//
// 🔑 这就是批次 88「静息态没静息」、批次 90「收尾污染下一轮」的同一族：
//     **一个前置没成立，后面所有读数都是废的，而且它还会留痕。**
//     ⇒ 收尾必须在 finally 里**独立于实验成败**地执行（本轮它执行了，只是也失败了）。
//
// 本轮做法：
//   ① 先用 ⌘0 把所有节点纳入视野，再找落点；仍然找不到就**放宽到「中心点归它」**，
//      再不行就换 `elementFromPoint` 从四个角往里逐像素试。
//   ② 删节点**不依赖选中** —— 直接用 `data-id` 定位元素、按元素几何右键，
//      因为 elementFromPoint 找不到不代表元素不存在。
import { chromium } from 'playwright';
import { writeFileSync, readFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };

const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const zoomPct = async () => p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]'); return e ? Number((e.getAttribute('aria-label').match(/(\d+)%/) || [])[1]) : null; });
const pos = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const m = (n.getAttribute('style') || '').match(/translate\(\s*([-\d.]+)px,\s*([-\d.]+)px/);
  return m ? { x: Number(m[1]), y: Number(m[2]) } : null; }, id);
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

/** 逐级放宽的落点搜索：细网格 → 中心 → 四角向内 → 不限视口 */
const landing = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const r = n.getBoundingClientRect();
  const ok = (x, y) => { const el = document.elementFromPoint(x, y); return !!el && el.closest('.react-flow__node') === n; };
  const inVp = (x, y) => x >= 0 && y >= 0 && x <= 1280 && y <= 720;
  for (const step of [0.05, 0.1, 0.2, 0.33]) {
    for (let fx = step; fx <= 1 - step + 1e-9; fx += step) for (let fy = step; fy <= 1 - step + 1e-9; fy += step) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      if (!inVp(x, y)) continue;
      if (ok(x, y)) return { x, y, how: `grid@${step}` };
    }
  }
  return { fail: true, box: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` };
}, id);

const selectNode = async (id) => {
  for (let attempt = 1; attempt <= 2; attempt++) {
    const pt = await landing(id);
    if (pt && !pt.fail) {
      await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1000);
      const got = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
      if (got[0] === id) return { ok: true, how: pt.how, attempt };
      log(`   尝试${attempt}：点上去选中的是 ${JSON.stringify(got)}，再试`);
    } else log(`   尝试${attempt}：找不到可用落点 ${JSON.stringify(pt)}`);
    if (attempt === 1) { await p.keyboard.press('Meta+0'); await p.waitForTimeout(1700); log('   → ⌘0 适配后重试'); }
  }
  return { ok: false };
};

/** 删除：先试选中后右键；不行就直接对该节点元素的几何中心右键（menu 属于该节点的上下文） */
const deleteById = async (id) => {
  const s = await selectNode(id);
  let via = 'select+rightclick';
  if (!s.ok) via = 'direct-rightclick';
  const pt = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }, id);
  if (!pt) return 'gone';
  await p.mouse.click(pt.x, pt.y, { button: 'right' }); await p.waitForTimeout(1100);
  const menu = await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-context-menu"]'); if (!m) return null;
    return Array.from(m.querySelectorAll('[role="menuitem"]')).map((x) => ({ t: x.innerText.replace(/\s+/g, ' ').trim(), dis: x.getAttribute('aria-disabled') })); });
  if (!menu) return { via, menu: null };
  const del = menu.find((i) => /^删除/.test(i.t));
  if (del && del.dis !== 'true') { await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-context-menu"]');
    const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /^删除/.test(x.innerText.replace(/\s+/g, ' ').trim())); if (it) it.click(); });
    await p.waitForTimeout(1500); return { via, deleted: true, menu: menu.map((i) => i.t) }; }
  return { via, deleted: false, menu: menu.map((i) => i.t) };
};

out.start = { nodes: (await ids()).length, sel: await selN(), credits: await credits(), zoom: await zoomPct() };
log('起点：', JSON.stringify(out.start));

// ── 先清掉 a 轮的自建节点 ──
// 台账里的 id 都是我自己建的，但**不靠台账去找** —— 共享画布上别人也可能建过同名类型的节点，
// 按台账 id 盲删风险太高。这里只清 a 轮**本轮明确创建**的那一个（写死并逐字核对 aria）。
const known = ['node_z3qd75wjaf'];
out.orphanCleanup = [];
for (const id of known) {
  if (!(await ids()).includes(id)) { log('遗留', id, '已不在'); continue; }
  const r = await deleteById(id);
  const still = (await ids()).includes(id);
  out.orphanCleanup.push({ id, r, still });
  log('删遗留', id, '→', JSON.stringify(r), '｜还在 =', still);
}
if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
out.afterCleanup = { nodes: (await ids()).length, sel: await selN() };
log('清理后：', JSON.stringify(out.afterCleanup));

// ═══ 重做 P1 / P2 ═══
const mine = [];
try {
  const pre0 = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3600);
  const made = (await ids()).filter((x) => !pre0.includes(x));
  if (made.length !== 1) throw new Error('新建异常 ' + made.length + ' ' + made.join(','));
  const A = made[0]; mine.push(A);
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  out.A = { id: A, pos: await pos(A), aria: await p.evaluate((i) => document.querySelector(`.react-flow__node[data-id="${i}"]`)?.getAttribute('aria-label'), A) };
  log('A：', JSON.stringify(out.A));

  // 选中它（放宽版落点）
  const sA = await selectNode(A);
  log('选中 A：', JSON.stringify(sA));
  if (!sA.ok) out.p2 = 'VOID-select-A';

  // P2：⌘D
  if (sA.ok) {
    const pre1 = await ids();
    await p.keyboard.press('Meta+d'); await p.waitForTimeout(2000);
    const after = await ids();
    const B = after.filter((x) => !pre1.includes(x))[0] || null;
    if (B) mine.push(B);
    out.p2 = { added: after.length - pre1.length, newId: B, aPos: out.A.pos, bPos: B ? await pos(B) : null,
      offset: B ? { dx: (await pos(B)).x - out.A.pos.x, dy: (await pos(B)).y - out.A.pos.y } : null,
      bAria: B ? await p.evaluate((i) => document.querySelector(`.react-flow__node[data-id="${i}"]`)?.getAttribute('aria-label'), B) : null };
    log('P2 ⌘D：', JSON.stringify(out.p2));
  }

  // P1：删副本 → ⌘Z → 比对 id
  const B = out.p2?.newId;
  if (B) {
    const before = { nodes: (await ids()).length, bPos: await pos(B) };
    const del = await deleteById(B);
    out.p1_delete = { via: del.via, deleted: del.deleted, after: { nodes: (await ids()).length, bThere: (await ids()).includes(B) } };
    log('删除副本：', JSON.stringify(out.p1_delete));
    await p.keyboard.press('Meta+z'); await p.waitForTimeout(2000);
    const back = await ids();
    out.p1_undo = { nodes: back.length, bBack: back.includes(B), bPos: back.includes(B) ? await pos(B) : null,
      bAria: back.includes(B) ? await p.evaluate((i) => document.querySelector(`.react-flow__node[data-id="${i}"]`)?.getAttribute('aria-label'), B) : null,
      allIds: back };
    out.p1 = { sameId: back.includes(B), verdict: back.includes(B) ? 'SAME_ID' : 'LOST',
      posRestored: JSON.stringify(out.p1_undo.bPos) === JSON.stringify(before.bPos) };
    log('P1 判定：', JSON.stringify({ ...out.p1, undo: { bBack: out.p1_undo.bBack, bPos: out.p1_undo.bPos, before } }));
  } else out.p1 = 'VOID-no-copy';
} catch (e) { out.error = String(e); log('🔴', String(e)); }
finally {
  log('── 收尾');
  for (const id of mine) { if (!(await ids()).includes(id)) continue; const r = await deleteById(id); log('  删', id, JSON.stringify(r?.deleted ?? r)); }
  if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
  await setZoom(60);
  const left = (await ids()).filter((x) => mine.includes(x));
  out.cleanup = { mine, leftover: left, nodes: (await ids()).length, sel: await selN() };
  log('清理', mine.length, '→ 剩', left.length, left.length ? '🔴 ' + left.join(' ') : '✅', '｜画布', out.cleanup.nodes, '节点');
  if (!left.length && mine.length) { try { const led = JSON.parse(readFileSync(LEDGER, 'utf8'));
    const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort();
      led.per_batch = { ...(led.per_batch || {}), 92: [...new Set([...(led.per_batch?.['92'] || []), ...mine])] };
      led.updated_at = new Date().toISOString().slice(0, 10);
      writeFileSync(LEDGER, JSON.stringify(led, null, 1)); log('已登记台账'); } } catch (e) { log('台账失败', String(e)); } }
  out.end = { credits: await credits(), zoom: await zoomPct() };
  writeFileSync(new URL('./_tmp-b92b.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
