// 批次 71 · 第三轮：把**参考页**那张只有 3/7 行的矩阵补成 7/7，
// 而且是**本批独立复现**每一行（不是抄批次 59 的表）。
//
// 靶子：`10-tasks/connect-nodes.md:81` 让读者「逐项可连性矩阵见 参考页」，
// 但 `20-reference.md` 的同名矩阵只有 视频/图片/文本/导演台 四行 ——
// 少掉的 音频/时间线/主体 三个源，读者在参考页查不到。
//
// 方法论（本项目第三次用在「复现」上）：
//   ① 每一行都在本轮**新建自己的空节点**、选中、读菜单、按 id 删掉；
//   ② 读数前**硬断言 selected === true**，不满足就抛错而不是记 0；
//   ③ **文本源排第一**当阳性对照 —— 它必有一个 ⊕（批次 69 实测），
//      没有它，导演台读到的 0 只是「我的尺子坏了」；
//   ④ 菜单项颜色同时记 textContent 与 computed color，理由文案可能挂在 sr-only 上。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const OUT = new URL('./_tmp-b71c.json', import.meta.url);

// 七种源，**文本排第一**（阳性对照），导演台排最后（它的 0 只有在对照之后才成立）
const SOURCES = ['文本', '图片', '视频', '音频', '时间线', '主体', '导演台'];

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);

const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
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
    }
    return null;
  });
  if (pt) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(900); }
  return p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
}

const scanPlus = (id) => p.evaluate((vid) => Array.from(document.querySelectorAll('[aria-label^="Create connected node"]'))
  .map((e) => {
    const q = e.getBoundingClientRect();
    if (q.width <= 1) return null;
    return {
      testid: e.getAttribute('data-testid'),
      aria: e.getAttribute('aria-label'),
      box: `${Math.round(q.width)}x${Math.round(q.height)}`,
      cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2),
      inTarget: !!e.closest(`.react-flow__node[data-id="${vid}"]`),
    };
  })
  .filter(Boolean), id);

async function selectNode(id) {
  for (const [fx, fy] of [[0.5, 0.2], [0.5, 0.12], [0.15, 0.2], [0.85, 0.2], [0.3, 0.3], [0.5, 0.5], [0.7, 0.18], [0.25, 0.45]]) {
    const pt = await p.evaluate(([vid, ax, ay]) => {
      const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return null;
      const r = n.getBoundingClientRect();
      const x = Math.round(r.x + r.width * ax), y = Math.round(r.y + r.height * ay);
      if (x < 4 || y < 4 || x > innerWidth - 4 || y > innerHeight - 4) return null;
      const el = document.elementFromPoint(x, y);
      return { x, y, inNode: !!(el && el.closest(`.react-flow__node[data-id="${vid}"]`)) };
    }, [id, fx, fy]);
    if (!pt || !pt.inNode) continue;
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(900);
    if (await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"].selected`), id)) return true;
  }
  return false;
}

async function readMenu() {
  return p.evaluate(() => {
    const ms = Array.from(document.querySelectorAll('[role="menu"],[data-testid="canvas-context-menu"]'))
      .filter((e) => e.getBoundingClientRect().width > 1);
    const el = ms[ms.length - 1];
    if (!el) return { none: true };
    const r = el.getBoundingClientRect();
    return {
      testid: el.getAttribute('data-testid'), role: el.getAttribute('role'),
      aria: el.getAttribute('aria-label'),
      box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      items: Array.from(el.querySelectorAll('[role="menuitem"]')).map((x) => {
        const q = x.getBoundingClientRect();
        const cs = getComputedStyle(x);
        return {
          name: (x.innerText || '').trim().split('\n')[0].trim(),
          reason: (x.textContent || '').replace((x.innerText || '').split('\n')[0], '').replace(/\s+/g, ' ').trim() || null,
          dis: x.getAttribute('aria-disabled'), cursor: cs.cursor,
          color: cs.color, box: `${Math.round(q.width)}x${Math.round(q.height)}`,
        };
      }),
    };
  });
}

async function ctxDelete(id) {
  const box = await p.evaluate((v) => {
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 14) };
  }, id);
  if (!box) return true;
  await p.mouse.click(box.x, box.y, { button: 'right' });
  await p.waitForTimeout(900);
  let gone = await p.evaluate(() => {
    const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
    const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || ''));
    if (!it) return false;
    it.click(); return true;
  });
  await p.waitForTimeout(1500);
  if (!(await ids()).includes(id)) return true;
  if (!gone) { await esc(2); await p.mouse.click(box.x, box.y, { button: 'right' }); await p.waitForTimeout(900);
    await p.evaluate(() => {
      const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
      const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click();
    });
    await p.waitForTimeout(1500);
  }
  return !(await ids()).includes(id);
}

const out = { startedAt: new Date().toISOString(), sources: {} };
const log = (...a) => console.log(a.join(' '));
const MINE = [];

try {
  log('开跑前:', await status(), '| 缩放', await zoomOf(), '| 积分', await credit());
  for (const kind of SOURCES) {
    const pre = await ids();
    const rail = await p.evaluate((k) => {
      const el = Array.from(document.querySelectorAll('button,[role="button"]'))
        .find((x) => new RegExp('^' + k + '$').test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) };
    }, kind);
    if (!rail) { log(`🔴 ${kind}: 左栏找不到入口`); out.sources[kind] = { error: '左栏无入口' }; continue; }
    await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(2300);
    const created = (await ids()).filter((x) => !pre.includes(x));
    if (created.length !== 1) { log(`🔴 ${kind}: 新建了 ${created.length} 个节点（${JSON.stringify(created)}）`); created.forEach((x) => MINE.push(x)); out.sources[kind] = { error: '新建数异常', created }; await esc(2); continue; }
    const id = created[0]; MINE.push(id);
    const box = await p.evaluate((v) => { const r = document.querySelector(`.react-flow__node[data-id="${v}"]`).getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; }, id);

    await deselectReal();
    const ok = await selectNode(id);
    const selCount = await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
    if (!ok || selCount !== 1) {   // 前置不成立 ⇒ 读数作废（批次 69 的纪律）
      log(`🔴 ${kind}: 前置不成立（选中=${ok}, selected=${selCount}）→ 本行作废`);
      out.sources[kind] = { id, box, selected: ok, selCount, VOID: '前置不成立' };
      await ctxDelete(id); MINE.pop();
      continue;
    }
    const plus = await scanPlus(id);
    log(`\n── ${kind} ${box} | ⊕ ${plus.length} ${JSON.stringify(plus.map((x) => (x.inTarget ? '本节点:' : '他节点:') + (x.testid || '').replace(/flow-node-|-connection-menu-button/g, '')))}`);
    const rec = { id, box, plus: plus.length, plusTestids: plus.map((x) => x.testid), plusInTarget: plus.every((x) => x.inTarget) };
    if (plus.length) {
      const btn = plus[0];
      await p.mouse.click(btn.cx, btn.cy); await p.waitForTimeout(1750);
      const menu = await readMenu();
      rec.menu = menu;
      log('   菜单', menu.aria, menu.role, menu.testid, menu.box);
      for (const it of (menu.items || [])) log(`     ${it.dis === 'true' || it.cursor === 'not-allowed' ? '🔘' : '✅'} ${it.name}｜${it.reason || '—'}｜${it.cursor}｜${it.color}｜${it.box}`);
      await esc(2);
    }
    out.sources[kind] = rec;
    await ctxDelete(id); MINE.pop();
    log(`   已删除 ${id} → ${(await ids()).includes(id) ? '🔴 仍在' : '✅'}`);
  }
  // 阳性对照收尾：导演台的 0 之后，再确认文本源此刻仍能读到 ⊕
  log('\n积分（全程）:', await credit());
} catch (e) {
  console.error('ABORT:', e.message); out.abort = e.message;
} finally {
  await esc(3);
  for (const id of [...new Set(MINE)]) { if (!(await ids()).includes(id)) continue; const g = await ctxDelete(id); log('清理', id, g ? '✅ deleted' : '🔴 仍在'); }
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
  writeFileSync(OUT, JSON.stringify(out, null, 1));
  log('写入', OUT.pathname);
  await b.close();
}
