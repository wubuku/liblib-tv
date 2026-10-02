// 批次 95 · A：审计 `create-first-node.md`（普查 **79**）。
//
// 建节点是本手册每批都在做的事，所以这一页的判据**应该最容易被复跑**——
// 正好用它检验「已验证说明」里的数字今天还成不成立。
//
// 🔑 **P1（数字复跑）**：本页第 52 行写「空白右键菜单 `Canvas context menu`，
//     实测 **240×172**，四项各 **232×36**」。
//     ⚠️ 批次 83/89 测过一批**别的**右键菜单（⊕ 菜单 200×316 / 右键项 192×36）——
//     两套菜单宽度和条目宽度都不同，所以这一页的数**必须单独验**，不能拿别的菜单推。
//
// 🔑 **P2（位置契约）**：本页第 55 行写「点击子菜单项即**在右键位置**创建」；
//     而方式 A（左栏插入）写的是「画布**中央**立即出现」。
//     ⇒ 两条路径的落点**是不是真的不同**？这是可机械比的（读节点的 canvas translate）。
//
// 🔑 **P3（承接批次 93）**：本页第 143 行称「文本节点**有**编辑态」。
//     批次 93 实测**空**文本节点双击后 `contenteditable`/`.ProseMirror` 恒 0。
//     ⇒ 要把适用范围写清：是「文本节点」还是「**带内容的**文本节点」。
import { chromium } from 'playwright';
import { writeFileSync, readFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const mine = [];

const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const nodeN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const zoomPct = async () => p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]'); return e ? Number((e.getAttribute('aria-label').match(/(\d+)%/) || [])[1]) : null; });
const setZoom = async (t0) => { for (let t = 1; t <= 3; t++) { if (await zoomPct() === t0) return true;
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
  const has = await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'));
  if (!has) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
  await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
    Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
    i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t0);
  await p.waitForTimeout(1500); await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  const a = await zoomPct(); await p.waitForTimeout(900); const c = await zoomPct();
  if (a === t0 && a === c) return true; } return false; };
const pos = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const m = (n.getAttribute('style') || '').match(/translate\(\s*([-\d.]+)px,\s*([-\d.]+)px/);
  return m ? { x: Number(m[1]), y: Number(m[2]) } : null; }, id);
const rightClick = async (x, y) => { await p.mouse.move(x, y); await p.waitForTimeout(150);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(220); await p.mouse.up({ button: 'right' }); await p.waitForTimeout(1100); };
const menuRead = (sel) => p.evaluate((s) => { const m = document.querySelector(s); if (!m) return { found: false };
  const r = m.getBoundingClientRect();
  const items = Array.from(m.querySelectorAll('[role="menuitem"]')).map((x) => { const q = x.getBoundingClientRect();
    return { t: x.innerText.replace(/\s+/g, ' ').trim(), dis: x.getAttribute('aria-disabled'), box: `${Math.round(q.width)}×${Math.round(q.height)}` }; });
  const subs = Array.from(m.querySelectorAll('[role="menu"],[role="listbox"]')).map((x) => { const q = x.getBoundingClientRect();
    return { role: x.getAttribute('role'), box: `${Math.round(q.width)}×${Math.round(q.height)}@${Math.round(q.x)},${Math.round(q.y)}`, n: x.querySelectorAll('[role="menuitem"]').length }; });
  return { found: true, aria: m.getAttribute('aria-label'), role: m.getAttribute('role'),
    box: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, items, subs }; }, sel);

try {
  if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
  await setZoom(60);
  out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomPct() };
  log('起点：', JSON.stringify(out.start));

  // ── P1：空白右键菜单 ──
  const bp = await p.evaluate(() => { const r = document.querySelector('.react-flow__pane'); if (!r) return null;
    const q = r.getBoundingClientRect();
    for (let fx = 0.15; fx <= 0.85; fx += 0.05) for (let fy = 0.15; fy <= 0.85; fy += 0.05) {
      const x = Math.round(q.x + q.width * fx), y = Math.round(q.y + q.height * fy);
      const el = document.elementFromPoint(x, y);
      if (el && !el.closest('.react-flow__node') && !el.closest('button') && !el.closest('input')) return { x, y }; }
    return null; });
  out.blankPoint = bp;
  if (!bp) { out.p1 = 'VOID-no-blank'; log('🔴 找不到空白点'); }
  else {
    await rightClick(bp.x, bp.y);
    out.p1 = await menuRead('[data-testid="canvas-context-menu"]');
    log('P1 空白右键菜单：', JSON.stringify({ aria: out.p1.aria, role: out.p1.role, box: out.p1.box, items: out.p1.items }));
    // 悬停「新建节点」看子菜单
    const item = await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-context-menu"]'); if (!m) return null;
      const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /新建节点/.test(x.innerText)); if (!it) return null;
      const r = it.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
    if (item) { await p.mouse.move(item.x, item.y); await p.waitForTimeout(1200);
      out.p1_subs = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"]')).map((m) => {
        const r = m.getBoundingClientRect();
        return { box: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
          items: Array.from(m.querySelectorAll('[role="menuitem"]')).map((x) => x.innerText.replace(/\s+/g, ' ').trim()) }; }));
      log('P1 子菜单：', JSON.stringify(out.p1_subs)); }
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);

  // ── P2：两条创建路径的落点是否真的不同 ──
  // 方式 A：左栏插入
  const preA = await ids(); const zBefore = await zoomPct();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3800);
  const A = (await ids()).filter((x) => !preA.includes(x))[0];
  if (A) { mine.push(A); out.p2_rail = { id: A, aria: await p.evaluate((i) => document.querySelector(`.react-flow__node[data-id="${i}"]`)?.getAttribute('aria-label'), A),
    pos: await pos(A), sel: await selN(), nodes: await nodeN(), zoomBefore: zBefore, zoomAfter: await zoomPct() };
    log('方式A 左栏插入：', JSON.stringify(out.p2_rail)); }
  else { out.p2_rail = { fail: true }; log('方式A 建节点失败'); }
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);

  // 方式 C：空白右键 → 新建节点 → 文本
  if (bp) {
    const preC = await ids();
    await rightClick(bp.x, bp.y);
    const it = await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-context-menu"]'); if (!m) return null;
      const x = Array.from(m.querySelectorAll('[role="menuitem"]')).find((e) => /新建节点/.test(e.innerText)); if (!x) return null;
      const r = x.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
    if (it) { await p.mouse.move(it.x, it.y); await p.waitForTimeout(1200);
      const sub = await p.evaluate(() => { const ms = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"]'));
        const last = ms[ms.length - 1]; if (!last) return null;
        const t = Array.from(last.querySelectorAll('[role="menuitem"]')).find((x) => /^文本/.test(x.innerText.replace(/\s+/g, ' ').trim()));
        if (!t) return null; const r = t.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
      if (sub) { await p.mouse.click(sub.x, sub.y); await p.waitForTimeout(3000);
        const C = (await ids()).filter((x) => !preC.includes(x))[0];
        if (C) { mine.push(C); out.p2_ctx = { id: C, pos: await pos(C), sel: await selN(), nodes: await nodeN(),
          aria: await p.evaluate((i) => document.querySelector(`.react-flow__node[data-id="${i}"]`)?.getAttribute('aria-label'), C) };
          log('方式C 右键菜单创建：', JSON.stringify(out.p2_ctx)); }
        else { out.p2_ctx = { fail: true }; log('方式C 没建出节点'); } } }
    await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  }
  out.p2_verdict = out.p2_rail?.pos && out.p2_ctx?.pos
    ? { samePos: out.p2_rail.pos.x === out.p2_ctx.pos.x && out.p2_rail.pos.y === out.p2_ctx.pos.y, a: out.p2_rail.pos, c: out.p2_ctx.pos } : 'VOID';
  log('P2 判定（两路径落点是否相同）：', JSON.stringify(out.p2_verdict));

  // ── P3：空文本节点双击是否进编辑态（承接批次 93）──
  if (A && (await ids()).includes(A)) {
    const pt = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
      const r = n.getBoundingClientRect();
      for (let fx = 0.1; fx <= 0.9; fx += 0.1) for (let fy = 0.1; fy <= 0.9; fy += 0.1) {
        const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
        if (x < 0 || y < 0 || x > 1280 || y > 720) continue;
        const el = document.elementFromPoint(x, y);
        if (el && el.closest('.react-flow__node') === n) return { x, y }; }
      return null; }, A);
    if (pt) {
      await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1000);
      const before = await p.evaluate(() => ({ ce: document.querySelectorAll('[contenteditable="true"]').length, pm: document.querySelectorAll('.ProseMirror').length }));
      await p.mouse.dblclick(pt.x, pt.y); await p.waitForTimeout(1500);
      const after = await p.evaluate(() => ({ ce: document.querySelectorAll('[contenteditable="true"]').length, pm: document.querySelectorAll('.ProseMirror').length,
        tid: Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).map((e) => { const r = e.getBoundingClientRect();
          return `${Math.round(r.width)}×${Math.round(r.height)}|${e.querySelectorAll('button').length}`; }) }));
      out.p3 = { before, after };
      log('P3 双击前：', JSON.stringify(before), '｜双击后：', JSON.stringify(after));
      await p.keyboard.press('Escape'); await p.waitForTimeout(800);
    } else out.p3 = { VOID: '找不到落点' };
  }
} catch (e) { out.error = String(e); log('🔴', String(e)); }
finally {
  log('── 收尾');
  await setZoom(60);
  for (const id of mine) { if (!(await ids()).includes(id)) continue;
    const pr = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
      const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }, id);
    if (!pr) continue;
    // 先选中再右键（这样菜单属于它）
    await p.mouse.click(pr.x, pr.y); await p.waitForTimeout(900);
    const who = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
    if (who[0] !== id) { log('  ⚠️ 选不中', id); continue; }
    await rightClick(pr.x, pr.y);
    await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-context-menu"]');
      const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /^删除/.test(x.innerText.replace(/\s+/g, ' ').trim())); if (it) it.click(); });
    await p.waitForTimeout(1600);
    log('  删', id, '→', (await ids()).includes(id) ? '🔴 还在' : '✅'); }
  if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
  await setZoom(60);
  const left = (await ids()).filter((x) => mine.includes(x));
  out.cleanup = { mine, leftover: left, nodes: await nodeN() };
  log('清理', mine.length, '→ 剩', left.length, left.length ? '🔴 ' + left.join(' ') : '✅', '｜画布', out.cleanup.nodes);
  if (!left.length && mine.length) { try { const led = JSON.parse(readFileSync(LEDGER, 'utf8'));
    const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort();
      led.per_batch = { ...(led.per_batch || {}), 95: [...new Set([...(led.per_batch?.['95'] || []), ...mine])] };
      led.updated_at = new Date().toISOString().slice(0, 10); writeFileSync(LEDGER, JSON.stringify(led, null, 1)); log('已登记台账'); } } catch (e) { log('台账失败', String(e)); } }
  out.end = { credits: await credits(), zoom: await zoomPct() };
  writeFileSync(new URL('./_tmp-b95a.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
