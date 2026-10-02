// 批次 92 · A：审计 `10-tasks/duplicate-delete-history.md`（普查 **77**，全册最陈旧）。
//
// 这一页把「删了能 ⌘Z 回来」写得很细，但**从头到尾没回答一个机械问题**：
//
// 🔑 **⌘Z 恢复出来的节点，还是不是同一个 id？**
//     - 若是**同一个 id** ⇒ 原来挂在它身上的连线可以原样回来（页面对「恢复整条连线」的
//       说法就成立，而且我们知道了它为什么成立）。
//     - 若是**新 id** ⇒ 节点回来了但**连不回来**，而页面第 136 行「被删节点上的连线一并移除」
//       ＋ 第 168 行「⌘Z 能恢复整条连线」这两条**合起来是错的**。
//
// ⇒ 这是一个**可机械验证**的问题，而且本页没有任何一条判据能回答它。
//
// 另外顺带答两个也没写过的：
//   **P2 ⌘D 复制副本**：副本的 id 是新生成的吗？位置相对原件偏移多少？
//   **P3 撤销栈的判据**：删之前先看右键菜单里「重做 ⌘⇧Z」有没有「无需重做操作」副文案 ——
//       概念页第 492 节教过「先看一眼撤销在不在」，但本页没把它写成步骤。
//
// ⛔ 安全边界：
//   - 只操作**自己新建的节点**（文本节点），绝不碰他人的 21+ 个节点。
//   - 改数据前**先确认撤销栈可用**（概念页纪律）。
//   - 收尾把自建节点**按 id 精确删净**，并把画布恢复到起点计数。
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
const edgeN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) edges?/) || [])[1]);
const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const zoomPct = async () => p.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]'); return e ? Number((e.getAttribute('aria-label').match(/(\d+)%/) || [])[1]) : null; });
const pos = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const m = (n.getAttribute('style') || '').match(/translate\(\s*([-\d.]+)px,\s*([-\d.]+)px/);
  return m ? { x: Number(m[1]), y: Number(m[2]) } : null; }, id);
const aria = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); return n ? n.getAttribute('aria-label') : null; }, id);
// 落点：先证明最上层就是它（批次 89 的修法）
const landing = (id) => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const r = n.getBoundingClientRect();
  if (!(r.left >= 0 && r.top >= 0 && r.right <= 1280 && r.bottom <= 720)) return null;
  const hits = [];
  for (let fx = 0.2; fx <= 0.8; fx += 0.2) for (let fy = 0.2; fy <= 0.8; fy += 0.2) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    const el = document.elementFromPoint(x, y);
    if (el && el.closest('.react-flow__node') === n) hits.push({ x, y }); }
  return hits.length ? hits[Math.floor(hits.length / 2)] : null; }, id);
const selectNode = async (id) => { const pt = await landing(id); if (!pt) return false;
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1000);
  return (await selN()) === '1' && (await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id'))))[0] === id; };
const ctxDelete = async () => { const pt = await landing(await p.evaluate(() => { const s = document.querySelector('.react-flow__node.selected'); return s ? s.getAttribute('data-id') : null; }));
  if (!pt) return 'no-landing';
  await p.mouse.click(pt.x, pt.y, { button: 'right' }); await p.waitForTimeout(1000);
  const r = await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-context-menu"]'); if (!m) return { ok: false };
    const items = Array.from(m.querySelectorAll('[role="menuitem"]')).map((x) => ({ t: x.innerText.replace(/\s+/g, ' ').trim(), dis: x.getAttribute('aria-disabled') }));
    const undo = items.find((i) => /^撤销/.test(i.t)); const redo = items.find((i) => /^重做/.test(i.t));
    const del = items.find((i) => /^删除/.test(i.t));
    return { ok: true, items, undo, redo, del }; });
  if (r.ok && r.del) { await p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-context-menu"]');
    const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /^删除/.test(x.innerText.replace(/\s+/g, ' ').trim())); if (it) it.click(); });
    await p.waitForTimeout(1500); }
  return r; };

try {
  // 起点归位：先确保 0 选中，缩放 60%
  if (await selN() !== '0') { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
  out.start = { nodes: (await ids()).length, edges: await edgeN(), sel: await selN(), credits: await credits(), zoom: await zoomPct() };
  log('起点：', JSON.stringify(out.start));

  // ═══ P3：改数据之前先确认撤销栈状态 ═══
  const pre = await (async () => { await p.mouse.click(20, 400); await p.waitForTimeout(700);
    return await p.mouse.click(20, 400, { button: 'right' }).then(async () => { await p.waitForTimeout(1000);
      return p.evaluate(() => { const m = document.querySelector('[data-testid="canvas-context-menu"]'); if (!m) return null;
        return Array.from(m.querySelectorAll('[role="menuitem"]')).map((x) => ({ t: x.innerText.replace(/\s+/g, ' ').trim(), dis: x.getAttribute('aria-disabled') })); }); }); })();
  out.preMenu = pre;
  log('空白右键菜单（撤销栈状态）：', JSON.stringify(pre?.filter((i) => /撤销|重做/.test(i.t))));
  await p.keyboard.press('Escape'); await p.waitForTimeout(600);

  // ═══ 建一个文本节点 ═══
  const pre0 = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (!rail) throw new Error('左栏找不到「文本」');
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3600);
  const made = (await ids()).filter((x) => !pre0.includes(x));
  log('新建：', made.length, '个', made.join(' '), '｜缩放', await zoomPct());
  if (made.length !== 1) throw new Error('新建异常 ' + made.length);
  mine.push(made[0]);
  const A = made[0];
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  out.A = { id: A, aria: await aria(A), pos: await pos(A) };
  log('A：', JSON.stringify(out.A));

  // ═══ P2：⌘D 复制副本 ═══
  const pre1 = await ids();
  if (!await selectNode(A)) { log('⚠️ A 选不中 ⇒ P2 记 VOID'); out.p2 = 'VOID-select'; }
  else {
    await p.keyboard.press('Meta+d'); await p.waitForTimeout(1800);
    const after = await ids();
    const B = after.filter((x) => !pre1.includes(x) && x !== A)[0];
    out.p2 = { copied: after.length - pre1.length, newId: B || null,
      aPos: await pos(A), bPos: B ? await pos(B) : null,
      bAria: B ? await aria(B) : null,
      offset: B ? { dx: (await pos(B))?.x - (await pos(A))?.x, dy: (await pos(B))?.y - (await pos(A))?.y } : null };
    if (B) mine.push(B);
    log('P2 ⌘D：', JSON.stringify(out.p2));
  }

  // ═══ P1：删掉副本 → ⌘Z，看 id 是不是同一个 ═══
  const B = out.p2?.newId;
  if (!B) { out.p1 = 'VOID-no-copy'; log('P1 记 VOID（没有可删的副本）'); }
  else {
    const before = { nodes: (await ids()).length, edges: await edgeN() };
    if (!await selectNode(B)) { out.p1 = 'VOID-select-B'; log('⚠️ B 选不中 ⇒ P1 记 VOID'); }
    else {
      const del = await ctxDelete();
      out.p1_delete = { menu: del, after: { nodes: (await ids()).length, edges: await edgeN(), bStillThere: (await ids()).includes(B) } };
      log('删除后：', JSON.stringify(out.p1_delete.after));
      // ⌘Z
      await p.keyboard.press('Meta+z'); await p.waitForTimeout(1800);
      const back = await ids();
      out.p1_undo = { nodes: back.length, edges: await edgeN(), bBack: back.includes(B), bPos: back.includes(B) ? await pos(B) : null,
        bAria: back.includes(B) ? await aria(B) : null, bSel: back.includes(B) };
      log('⌘Z 后：', JSON.stringify(out.p1_undo));
      out.p1 = { sameId: back.includes(B), verdict: back.includes(B) ? 'SAME_ID' : 'NEW_ID_OR_LOST',
        posRestored: JSON.stringify(out.p1_undo.bPos) === JSON.stringify(out.p2.bPos) };
      log('P1 判定：', JSON.stringify(out.p1));
    }
  }
} catch (e) { out.error = String(e); log('🔴', String(e)); }
finally {
  // 收尾：把自建节点按 id 删净
  log('── 收尾删除');
  for (const id of mine) {
    if (!(await ids()).includes(id)) { log('  ', id, '已不在'); continue; }
    if (!await selectNode(id)) { log('  ⚠️ 选不中', id); continue; }
    const r = await ctxDelete();
    log('  删', id, JSON.stringify(r === 'no-landing' ? r : (r.del ? 'clicked' : 'no-item')));
  }
  const left = (await ids()).filter((x) => mine.includes(x));
  out.cleanup = { mine, leftover: left, nodes: (await ids()).length, edges: await edgeN(), sel: await selN() };
  log('清理', mine.length, '→ 剩', left.length, left.length ? '🔴 ' + left.join(' ') : '✅', '｜画布', out.cleanup.nodes, '节点');
  out.end = { credits: await credits(), zoom: await zoomPct() };
  if (!left.length && mine.length) { try { const led = JSON.parse(readFileSync(LEDGER, 'utf8'));
    const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort();
      led.per_batch = { ...(led.per_batch || {}), 92: [...new Set([...(led.per_batch?.['92'] || []), ...mine])] };
      led.updated_at = new Date().toISOString().slice(0, 10);
      writeFileSync(LEDGER, JSON.stringify(led, null, 1)); log('已登记台账'); } } catch (e) { log('台账失败', String(e)); } }
  writeFileSync(new URL('./_tmp-b92a.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
