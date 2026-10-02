// 批次 93 · A：审计 `use-node-toolbar.md`（普查 **79**，348 行，普查 79 簇里最大的一页）。
//
// 🔑 **现成的矛盾可打**（不需要新弹药）：
//     本页第 38 行写「文本节点**选中态**工具条 **185×40**」，
//     而批次 85 在 60% 下量到的是 **`192×40`**（**随缩放**，canvas 恒 `320×67`）。
//     `185` 与 `192` 差 7 px —— 两者必有一个不是同一口径，或者其中一个不是当前行为。
//     ⇒ **P1**：自己建一个文本节点，逐档缩放实测选中态工具条的屏上尺寸，
//       看 `185` 能不能在任何一档复现，`192` 又对应哪一档。
//
// 🔑 **P2（ID 双轨）**：本页第 44 行称「两者都用 `.react-flow__node-toolbar` 作为**外层类名**」，
//     而批次 85/88 全部是按 `[data-testid="node-toolbar"]` 找的。
//     ⇒ class 与 data-testid **是不是同一个元素**？两个都在时，谁才是稳定定位器？
//     这是批次 85「一个 testid 覆盖两类面板」之后必须钉清的一件事。
//
// 🔑 **P3（两套工具条）**：选中态三项 / 编辑态八项，本页的数来自 2026-09-23，
//     要用今天的 DOM 复核一遍。
//
// ⛔ 只建**自己的**文本节点、只测**不产生费用**的工具条；
//    绝不点 截取帧 / 视频修剪 / 局部重拍 / 视频编辑 / 工具∨ / 预设∨ / AI 助手∨
//    （这些在批次 85 之后一律未获授权）。
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
  await p.waitForTimeout(1400); await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  const a = await zoomPct(); await p.waitForTimeout(800); const c = await zoomPct();
  if (a === t0 && a === c) return true; } return false; };
const scan = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const r = n.getBoundingClientRect();
  for (let fx = 0.04; fx <= 0.96; fx += 0.04) for (let fy = 0.04; fy <= 0.96; fy += 0.04) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    if (x < 0 || y < 0 || x > 1280 || y > 720) continue;
    const el = document.elementFromPoint(x, y);
    if (el && el.closest('.react-flow__node') === n) return { x, y }; }
  return { fail: true }; }, id);
const selectNode = async (id) => { for (const z of [await zoomPct(), 100, 200, 400, 800]) { if (!await setZoom(z)) continue;
  const pt = await scan(id); if (!pt || pt.fail) continue;
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1100);
  const got = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
  if (got[0] === id) return { ok: true, zoom: z, pt };
  await p.keyboard.press('Escape'); await p.waitForTimeout(500); } return { ok: false }; };
const rightClick = async (x, y) => { await p.mouse.move(x, y); await p.waitForTimeout(150);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(220); await p.mouse.up({ button: 'right' }); await p.waitForTimeout(1100); };
const clickMenuItem = async (src) => { const ok = await p.evaluate((s) => { const m = document.querySelector('[data-testid="canvas-context-menu"]'); if (!m) return false;
  const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => new RegExp(s).test(x.innerText.replace(/\s+/g, ' ').trim())); if (it) { it.click(); return true; } return false; }, src);
  await p.waitForTimeout(1600); return ok; };

/** 一次读全：class 选择器 / data-testid 各命中几个、几何、按钮 aria */
const readToolbars = () => p.evaluate(() => {
  const byClass = Array.from(document.querySelectorAll('.react-flow__node-toolbar'));
  const byTid = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'));
  const sameElements = byClass.length === byTid.length && byClass.every((e, i) => e === byTid[i]);
  const desc = (e) => { const r = e.getBoundingClientRect();
    return { tag: e.tagName, box: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      cls: String(e.className || '').slice(0, 70),
      buttons: Array.from(e.querySelectorAll('button,[role="button"]')).map((x) => { const q = x.getBoundingClientRect();
        return `${x.getAttribute('aria-label') || (x.innerText || '').trim() || '(无 aria)'}|${Math.round(q.width)}×${Math.round(q.height)}`; }) }; };
  return { classCount: byClass.length, tidCount: byTid.length, sameElements,
    class: byClass.map(desc), tid: byTid.map(desc) };
});

try {
  if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
  await setZoom(60);
  out.start = { nodes: (await ids()).length, sel: await selN(), credits: await credits(), zoom: await zoomPct() };
  log('起点：', JSON.stringify(out.start));

  // 未选中态：先读一次（证明工具条确实「选中才有」）
  out.unselected = await readToolbars();
  log('未选中：class 命中', out.unselected.classCount, '｜testid 命中', out.unselected.tidCount);

  // 建文本节点
  const pre0 = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3800);
  const A = (await ids()).filter((x) => !pre0.includes(x))[0];
  if (!A) throw new Error('新建失败');
  mine.push(A);
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  log('自建文本节点：', A);

  // ── P2：ID 双轨 ──
  const s = await selectNode(A);
  if (!s.ok) { out.p2 = 'VOID-select'; log('⚠️ 选不中，后续 VOID'); }
  else {
    out.p2 = await readToolbars();
    log('P2 选中态：class 命中', out.p2.classCount, '｜testid 命中', out.p2.tidCount, '｜同一批元素 =', out.p2.sameElements);
    log('   class 版：', JSON.stringify(out.p2.class.map((c) => ({ box: c.box, n: c.buttons.length }))));
    log('   tid  版：', JSON.stringify(out.p2.tid.map((c) => ({ box: c.box, n: c.buttons.length }))));
    log('   按钮：', JSON.stringify(out.p2.tid[0]?.buttons));
    log('   class 串：', out.p2.class[0]?.cls);

    // ── P1：逐档缩放，看 185 还是 192 ──
    out.p1 = [];
    for (const z of [60, 100, 40]) {
      if (!await setZoom(z)) { out.p1.push({ zoom: z, fail: 'zoom' }); continue; }
      const stillSel = (await selN()) === '1';
      if (!stillSel) { const s2 = await selectNode(A); if (!s2.ok) { out.p1.push({ zoom: z, fail: 'select' }); continue; } }
      const r = await readToolbars();
      const sc = await p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
        const m = (vp ? (vp.style.transform || '') : '').match(/scale\(([-\d.]+)\)/); return m ? Number(m[1]) : null; });
      const el = r.tid[0];
      const row = { zoom: z, scale: sc, count: r.tidCount,
        box: el ? el.box : null, buttons: el ? el.buttons.length : null,
        canvas: (el && sc) ? (() => { const m2 = el.box.match(/([\d.]+)×([\d.]+)@/); return m2 ? `${Math.round(Number(m2[1]) / sc)}×${Math.round(Number(m2[2]) / sc)}` : null; })() : null };
      out.p1.push(row);
      log(`  @${z}% scale=${sc}｜工具条 ${row.box}｜按钮 ${row.buttons} 个｜反推 canvas ${row.canvas}`);
    }
    out.p1verdict = { page185: out.p1.map((r) => r.box), matches185: out.p1.some((r) => r.box && r.box.startsWith('185')),
      matches192: out.p1.some((r) => r.box && r.box.startsWith('192')),
      canvasValues: out.p1.map((r) => r.canvas) };
    log('P1 判定：', JSON.stringify(out.p1verdict));

    // ── P3：编辑态八项（双击进编辑，不产生费用） ──
    if (await setZoom(60)) { const s3 = await selectNode(A); if (s3.ok) {
      await p.mouse.dblclick(s3.pt.x, s3.pt.y); await p.waitForTimeout(1400);
      out.p3 = await readToolbars();
      log('P3 双击后：class', out.p3.classCount, '｜tid', out.p3.tidCount);
      log('   工具条几何：', JSON.stringify(out.p3.tid.map((c) => ({ box: c.box, n: c.buttons.length }))));
      log('   按钮：', JSON.stringify(out.p3.tid[0]?.buttons));
      await p.keyboard.press('Escape'); await p.waitForTimeout(800); } }
  }
} catch (e) { out.error = String(e); log('🔴', String(e)); }
finally {
  log('── 收尾');
  await setZoom(60);
  for (const id of mine) { if (!(await ids()).includes(id)) continue;
    const s = await selectNode(id); if (!s.ok) { log('  ⚠️ 选不中', id); continue; }
    await rightClick(s.pt.x, s.pt.y); await clickMenuItem('^删除');
    log('  删', id, '→', (await ids()).includes(id) ? '🔴 还在' : '✅'); }
  if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
  await setZoom(60);
  const left = (await ids()).filter((x) => mine.includes(x));
  out.cleanup = { mine, leftover: left, nodes: (await ids()).length };
  log('清理', mine.length, '→ 剩', left.length, left.length ? '🔴 ' + left.join(' ') : '✅', '｜画布', out.cleanup.nodes);
  if (!left.length && mine.length) { try { const led = JSON.parse(readFileSync(LEDGER, 'utf8'));
    const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort();
      led.per_batch = { ...(led.per_batch || {}), 93: [...new Set([...(led.per_batch?.['93'] || []), ...mine])] };
      led.updated_at = new Date().toISOString().slice(0, 10); writeFileSync(LEDGER, JSON.stringify(led, null, 1)); log('已登记台账'); } } catch (e) { log('台账失败', String(e)); } }
  out.end = { credits: await credits(), zoom: await zoomPct() };
  writeFileSync(new URL('./_tmp-b93a.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
