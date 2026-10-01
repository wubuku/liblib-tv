// 批次 71 · 第四轮：**before ⊕ 与 after ⊕ 是不是两套不同的菜单？**
//
// 触发：第三轮 7 源全表复现与批次 59 的表**大面积不一致**，但不一致有规律 ——
//   ① 只有 1 个 ⊕ 的两种源（文本=after、时间线=before）我与批次 59 **逐项一致**；
//   ② 有 2 个 ⊕ 的四种源（图片/视频/音频/主体）**每一项都对不上**。
// ⇒ 嫌疑自变量只有一个：我点的是 `plus[0]`（DOM 顺序第一个），
//    而 DOM 顺序是 target/before 还是 source/after **因源节点而异**。
//
// 决定性实验（同一个节点实例内前后对照，排除「换了个节点」这个混杂）：
//   同一个节点 → 点 before ⊕ 读一遍 → Esc → 点 after ⊕ 读一遍 → 对拍。
// 只在有**两个** ⊕ 的四种源上做；文本/时间线只有一个 ⊕，只读一次（当对照）。
//
// 顺带解掉一个被写进手册的「契约」：批次 59 说「时间线源的菜单标题是
// 『添加上下文』，其余六种源都是『添加节点』」—— 本轮看标题到底跟**源类型**走
// 还是跟**点了哪个 ⊕** 走。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const OUT = new URL('./_tmp-b71d.json', import.meta.url);
const SOURCES = ['视频', '主体', '音频', '图片', '时间线', '文本'];

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);

const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const selCount = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const esc = async (n = 3) => { for (let i = 0; i < n; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(340); } };

async function deselectReal() {
  await esc(2);
  const pt = await p.evaluate(() => {
    for (let y = 120; y < 640; y += 20) for (let x = 100; x < 1200; x += 20) {
      if (x > 1120 && y > 540) continue;
      const el = document.elementFromPoint(x, y);
      if (!el || el.closest('.react-flow__node')) continue;
      if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[role="dialog"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"],[data-testid="canvas-feature-sidecar"]')) continue;
      return { x, y };
    } return null; });
  if (pt) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(900); }
  return selCount();
}

const scanPlus = (id) => p.evaluate((vid) => Array.from(document.querySelectorAll('[aria-label^="Create connected node"]'))
  .map((e) => { const q = e.getBoundingClientRect(); if (q.width <= 1) return null;
    return { testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
      box: `${Math.round(q.width)}x${Math.round(q.height)}`,
      cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2),
      inTarget: !!e.closest(`.react-flow__node[data-id="${vid}"]`) }; })
  .filter(Boolean), id);

async function selectNode(id) {
  for (const [fx, fy] of [[0.5, 0.2], [0.5, 0.12], [0.15, 0.2], [0.85, 0.2], [0.3, 0.3], [0.5, 0.5], [0.7, 0.18], [0.25, 0.45]]) {
    const pt = await p.evaluate(([vid, ax, ay]) => {
      const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return null;
      const r = n.getBoundingClientRect();
      const x = Math.round(r.x + r.width * ax), y = Math.round(r.y + r.height * ay);
      if (x < 4 || y < 4 || x > innerWidth - 4 || y > innerHeight - 4) return null;
      return { x, y, inNode: !!(document.elementFromPoint(x, y) || {}).closest?.(`.react-flow__node[data-id="${vid}"]`) };
    }, [id, fx, fy]);
    if (!pt || !pt.inNode) continue;
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(900);
    if (await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"].selected`), id)) return true;
  }
  return false;
}

async function readMenu() {
  return p.evaluate(() => {
    const ms = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]')).filter((e) => e.getBoundingClientRect().width > 1);
    const el = ms[ms.length - 1]; if (!el) return { none: true };
    const r = el.getBoundingClientRect();
    return { testid: el.getAttribute('data-testid'), role: el.getAttribute('role'), aria: el.getAttribute('aria-label'),
      box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      items: Array.from(el.querySelectorAll('[role="menuitem"]')).map((x) => {
        const cs = getComputedStyle(x);
        return { name: (x.innerText || '').trim().split('\n')[0].trim(),
          reason: (x.textContent || '').replace((x.innerText || '').split('\n')[0], '').replace(/\s+/g, ' ').trim() || null,
          dis: x.getAttribute('aria-disabled'), cursor: cs.cursor, color: cs.color }; }) };
  });
}

async function ctxDelete(id) {
  const box = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 14) }; }, id);
  if (!box) return true;
  await p.mouse.click(box.x, box.y, { button: 'right' }); await p.waitForTimeout(900);
  await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
    const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
  await p.waitForTimeout(1500);
  return !(await ids()).includes(id);
}

const out = { startedAt: new Date().toISOString(), sources: {} };
const log = (...a) => console.log(a.join(' '));
const MINE = [];
try {
  log('开跑前:', await status(), '| 缩放', await zoomOf(), '| 积分', await credit());
  for (const kind of SOURCES) {
    const pre = await ids();
    const rail = await p.evaluate((k) => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
      .find((x) => new RegExp('^' + k + '$').test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
      if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }, kind);
    if (!rail) { log(`🔴 ${kind} 左栏无入口`); continue; }
    await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(2300);
    const created = (await ids()).filter((x) => !pre.includes(x));
    if (created.length !== 1) { log(`🔴 ${kind} 新建 ${created.length} 个`); created.forEach((x) => MINE.push(x)); await esc(2); continue; }
    const id = created[0]; MINE.push(id);
    await deselectReal();
    if (!(await selectNode(id)) || (await selCount()) !== 1) { log(`🔴 ${kind} 前置不成立 → 作废`); await ctxDelete(id); MINE.pop(); continue; }
    const plus = await scanPlus(id);
    log(`\n══ ${kind} 源 ⊕ ${plus.length} 个`);
    for (const x of plus) log(`   ⊕ ${x.testid}｜aria 逐字「${x.aria}」｜${x.box}`);
    const rec = { id, plus: plus.map((x) => ({ testid: x.testid, aria: x.aria, box: x.box })), reads: [] };
    // 逐个 ⊕ 各读一遍；**每次读前都硬断言仍处于选中态**
    for (const x of plus) {
      if ((await selCount()) !== 1) {   // 前置不成立 ⇒ 该次读数作废
        log(`   ⛔ 读「${x.testid}」前 selected=${await selCount()}，本行作废`);
        rec.reads.push({ testid: x.testid, VOID: '前置不成立' }); continue;
      }
      await p.mouse.click(x.cx, x.cy); await p.waitForTimeout(1750);
      const m = await readMenu();
      const avail = (m.items || []).filter((i) => i.dis !== 'true' && i.cursor !== 'not-allowed').map((i) => i.name);
      const dis = (m.items || []).filter((i) => i.dis === 'true' || i.cursor === 'not-allowed').map((i) => `${i.name}:${i.reason}`);
      log(`   ⊕ ${x.testid.replace(/flow-node-|-connection-menu-button/g, '')} → 标题「${m.aria}」 ${m.box}`);
      log(`      可用: ${avail.length ? avail.join(' / ') : '（无）'}`);
      log(`      禁用: ${dis.join(' | ')}`);
      rec.reads.push({ testid: x.testid, aria: x.aria, menuAria: m.aria, box: m.box, avail, dis });
      await esc(2);
    }
    out.sources[kind] = rec;
    await ctxDelete(id); MINE.pop();
    log(`   已删除 ${id} → ${(await ids()).includes(id) ? '🔴 仍在' : '✅'}`);
  }
  log('\n积分（全程）:', await credit());
} catch (e) { console.error('ABORT:', e.message); out.abort = e.message; }
finally {
  await esc(3);
  for (const id of [...new Set(MINE)]) { if (!(await ids()).includes(id)) continue; log('清理', id, (await ctxDelete(id)) ? '✅ deleted' : '🔴 仍在'); }
  await esc(3);
  for (let t = 0; t < 3; t++) { const z = await zoomOf(); if (z && z.includes('60%')) break;
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
    const sl = 'input[data-testid=canvas-zoom-percent-input]';
    if (await p.$(sl)) { await p.fill(sl, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); } else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } }
  const cp = await p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
    const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
    return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null]; })));
  const dev = [];
  for (const [id, b2] of Object.entries(BASE.nodes)) { const c = cp[id]; const d = c && b2.canvas ? [Math.round((c[0] - b2.canvas[0]) * 100) / 100, Math.round((c[1] - b2.canvas[1]) * 100) / 100] : 'MISSING';
    if (d === 'MISSING' || (Array.isArray(d) && (Math.abs(d[0]) > 0.01 || Math.abs(d[1]) > 0.01))) dev.push([id, d]); }
  const extra = Object.keys(cp).filter((x) => !BASE.nodes[x]);
  out.end = { status: await status(), zoom: await zoomOf(), credit: await credit(), nodes: Object.keys(cp).length, dev, extra };
  log('终态', JSON.stringify(out.end));
  writeFileSync(OUT, JSON.stringify(out, null, 1)); log('写入', OUT.pathname);
  await b.close();
}
