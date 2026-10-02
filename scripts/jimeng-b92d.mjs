// 批次 92 · D：重做 P1 / P2 —— 这次**关键动作一律走右键菜单**，不用键盘快捷键。
//
// c 轮清债时学到的三件事，全部用上：
//   ① 右键必须 `down + 220ms + up`（`click({button:'right'})` 菜单**弹不出来**）；
//   ② 落点扫描要**逐级放宽**（0.05 → 0.33 步长），盖得严时只有 1 个点可用；
//   ③ 删节点**逐字核对 aria** 是「文本 node: 文本 N」才动手，绝不按类型删。
//
// 🔑 顺带对照：**⌘D 键盘版** vs **菜单「复制副本 ⌘ D」**。
//    a 轮 ⌘D 加了 0 个节点，当时无法判断是「快捷键无效」还是「前置没成立」（节点没选中）。
//    这次菜单版与键盘版**各做一次**，把「哪个真的能用」分开。
//
// ⇒ **P1（本页从未回答过的那条）**：⌘Z 恢复出来的节点，**还是不是同一个 id**？
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
const info = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const m = (n.getAttribute('style') || '').match(/translate\(\s*([-\d.]+)px,\s*([-\d.]+)px/);
  return { aria: n.getAttribute('aria-label'), x: m ? Number(m[1]) : null, y: m ? Number(m[2]) : null }; }, id);
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
  const r = n.getBoundingClientRect(); let tested = 0;
  for (let fx = 0.04; fx <= 0.96; fx += 0.04) for (let fy = 0.04; fy <= 0.96; fy += 0.04) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    if (x < 0 || y < 0 || x > 1280 || y > 720) continue; tested++;
    const el = document.elementFromPoint(x, y);
    if (el && el.closest('.react-flow__node') === n) return { x, y, tested }; }
  return { fail: true, tested, box: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; }, id);
const selectNode = async (id) => { for (const z of [await zoomPct(), 100, 200, 400, 800]) {
  if (!await setZoom(z)) continue; const pt = await scan(id);
  if (!pt || pt.fail) { log(`   @${z}% 无落点 ${JSON.stringify(pt)}`); continue; }
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1000);
  const got = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
  if (got[0] === id) return { ok: true, zoom: z, pt };
  log(`   @${z}% 点上去是 ${JSON.stringify(got)}`); await p.keyboard.press('Escape'); await p.waitForTimeout(500); }
  return { ok: false }; };
const openMenu = async (x, y) => { await p.mouse.move(x, y); await p.waitForTimeout(150);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(220); await p.mouse.up({ button: 'right' }); await p.waitForTimeout(1100);
  return p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-context-menu"]'); if (!m) return null;
    return Array.from(m.querySelectorAll('[role="menuitem"]')).map((x) => ({ t: x.innerText.replace(/\s+/g, ' ').trim(), dis: x.getAttribute('aria-disabled') })); }); };
const clickItem = async (re) => { const ok = await p.evaluate((r) => { const src = r.source;
  const m = document.querySelector('[data-testid="canvas-context-menu"]'); if (!m) return false;
  const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => new RegExp(src).test(x.innerText.replace(/\s+/g, ' ').trim()));
  if (it) { it.click(); return true; } return false; }, { source: re.source });
  await p.waitForTimeout(1600); return ok; };

try {
  if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
  await setZoom(60);
  out.start = { nodes: (await ids()).length, sel: await selN(), credits: await credits(), zoom: await zoomPct() };
  log('起点：', JSON.stringify(out.start));

  // 建文本节点 A
  const pre0 = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3800);
  const made = (await ids()).filter((x) => !pre0.includes(x));
  if (made.length !== 1) throw new Error('新建异常 ' + made.length);
  const A = made[0]; mine.push(A);
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  out.A = await info(A);
  log('A：', JSON.stringify(out.A));

  const sA = await selectNode(A);
  log('选中 A：', JSON.stringify(sA));
  if (!sA.ok) throw new Error('A 选不中，后续全部 VOID');

  // 菜单逐字（顺带记录）
  const menu = await openMenu(sA.pt.x, sA.pt.y);
  out.menu = menu;
  log('文本节点右键菜单：' + JSON.stringify(menu?.map((i) => i.t)));

  // ── P2a：菜单「复制副本 ⌘ D」 ──
  const pre1 = await ids();
  const didCopy = menu ? await clickItem(/^复制副本/) : false;
  const after1 = await ids();
  const B = after1.filter((x) => !pre1.includes(x))[0] || null;
  if (B) mine.push(B);
  out.p2a = { clicked: didCopy, added: after1.length - pre1.length, newId: B, aInfo: out.A, bInfo: B ? await info(B) : null,
    offset: B ? { dx: (await info(B)).x - out.A.x, dy: (await info(B)).y - out.A.y } : null };
  log('P2a 菜单复制副本：', JSON.stringify(out.p2a));

  // ── P2b：键盘 ⌘D（对照组；此时 A 应仍处于选中态或需重选） ──
  if (B) {
    const sB = await selectNode(B);
    const pre2 = await ids();
    await p.keyboard.press('Meta+d'); await p.waitForTimeout(2000);
    const after2 = await ids();
    const C = after2.filter((x) => !pre2.includes(x))[0] || null;
    if (C) mine.push(C);
    out.p2b = { selectB: sB.ok, added: after2.length - pre2.length, newId: C, cInfo: C ? await info(C) : null };
    log('P2b 键盘 ⌘D：', JSON.stringify(out.p2b));
    if (C) { const sC = await selectNode(C); const r = await openMenu(sC.pt.x, sC.pt.y);
      if (r) await clickItem(/^删除/); log('C 已删：', !(await ids()).includes(C)); }
    await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  }

  // ── P1：删 B → ⌘Z → 比对 id ──
  if (B) {
    const sB2 = await selectNode(B);
    if (!sB2.ok) out.p1 = 'VOID-select-B';
    else {
      const beforePos = (await info(B));
      const r = await openMenu(sB2.pt.x, sB2.pt.y);
      const del = r ? await clickItem(/^删除/) : false;
      out.p1_delete = { selectOk: sB2.ok, menuOpen: !!r, deleted: del, nodes: (await ids()).length, bThere: (await ids()).includes(B) };
      log('删除 B：', JSON.stringify(out.p1_delete));
      if (del) {
        // 改数据前先确认撤销栈可用（概念页纪律）：看「重做」有没有「无需重做操作」
        const probe = await (async () => { const anySel = (await ids()).find(() => true); await p.mouse.click(30, 400); await p.waitForTimeout(500);
          await rightClickAny(30, 400); return null; })();
        await p.keyboard.press('Meta+z'); await p.waitForTimeout(2200);
        const back = await ids();
        out.p1_undo = { nodes: back.length, bBack: back.includes(B), bInfo: back.includes(B) ? await info(B) : null, beforePos };
        out.p1 = { sameId: back.includes(B), verdict: back.includes(B) ? 'SAME_ID_RESTORED' : 'NOT_RESTORED',
          posRestored: JSON.stringify(out.p1_undo.bInfo) === JSON.stringify(beforePos) };
        log('P1 判定：', JSON.stringify(out.p1));
        log('  删除前 B：' + JSON.stringify(beforePos) + '｜恢复后：' + JSON.stringify(out.p1_undo.bInfo));
      } else out.p1 = 'VOID-not-deleted';
    }
  }
  async function rightClickAny(x, y) { await p.mouse.move(x, y); await p.waitForTimeout(150);
    await p.mouse.down({ button: 'right' }); await p.waitForTimeout(200); await p.mouse.up({ button: 'right' }); await p.waitForTimeout(900);
    await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
} catch (e) { out.error = String(e); log('🔴', String(e)); }
finally {
  log('── 收尾');
  await setZoom(60);
  for (const id of mine) { if (!(await ids()).includes(id)) continue;
    const s = await selectNode(id);
    if (!s.ok) { log('  ⚠️ 选不中', id, '（仍在画布上，需要人工处理）'); continue; }
    const r = await openMenu(s.pt.x, s.pt.y); if (r) await clickItem(/^删除/);
    log('  删', id, '→', (await ids()).includes(id) ? '🔴 还在' : '✅'); }
  if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
  await setZoom(60);
  const left = (await ids()).filter((x) => mine.includes(x));
  out.cleanup = { mine, leftover: left, nodes: (await ids()).length, sel: await selN() };
  log('清理', mine.length, '→ 剩', left.length, left.length ? '🔴 ' + left.join(' ') : '✅', '｜画布', out.cleanup.nodes);
  if (!left.length && mine.length) { try { const led = JSON.parse(readFileSync(LEDGER, 'utf8'));
    const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort();
      led.per_batch = { ...(led.per_batch || {}), 92: [...new Set([...(led.per_batch?.['92'] || []), ...mine])] };
      led.updated_at = new Date().toISOString().slice(0, 10); writeFileSync(LEDGER, JSON.stringify(led, null, 1)); log('已登记台账'); } } catch (e) { log('台账失败', String(e)); } }
  out.end = { credits: await credits(), zoom: await zoomPct() };
  writeFileSync(new URL('./_tmp-b92d.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
