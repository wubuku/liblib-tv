// 批次 71：补齐「添加节点」可连性矩阵缺的两行 —— **时间线源** 与 **主体源**
//
// 现状（20-reference.md）：矩阵只有 视频源 / 图片源 / 文本源 / 导演台（无 ⊕）四行。
// 缺 时间线源 与 主体源。PROGRESS 里散落着「时间线源只有音频可点」的旧记录，
// 但**没有进矩阵**，读者查表时看不到。
//
// 受控条件：与批次 69 完全相同的动作序列（**选中 → 找 ⊕ → 点 → 读菜单**），
// 只换**源节点类型**。时间线与主体节点都**自己新建**（不用他人那 6 个节点里的）。
// ⚠️ 主体库是空态且是**共享**数据 ⇒ 本批**只读菜单、不导入任何素材**。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const SHOTS = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const OUT = new URL('./_tmp-b71.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const esc = async (n = 3) => { for (let i = 0; i < n; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(340); } };
const deselectReal = async () => { await esc(2);
  const pt = await p.evaluate(() => { for (let y = 120; y < 640; y += 20) for (let x = 100; x < 1200; x += 20) { if (x > 1120 && y > 540) continue;
    const el = document.elementFromPoint(x, y); if (!el || el.closest('.react-flow__node')) continue;
    if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[role="dialog"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"],[data-testid="canvas-feature-sidecar"]')) continue;
    return { x, y }; } return null; });
  if (pt) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(900); } return p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length); };
/** ★ 只按 aria 前缀扫，不限 tag（批次 69 的教训） */
const scanPlus = (id) => p.evaluate((vid) => Array.from(document.querySelectorAll('[aria-label^="Create connected node"]'))
  .map((e) => { const q = e.getBoundingClientRect(); if (q.width <= 1) return null;
    return { testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), box: `${Math.round(q.width)}x${Math.round(q.height)}`,
      cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2), inTarget: !!e.closest(`.react-flow__node[data-id="${vid}"]`) }; })
  .filter(Boolean), id);
async function ctxDelete(id) {
  await p.evaluate((vid) => { const s = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!s) return;
    const r = s.getBoundingClientRect(); s.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 14) })); }, id);
  await p.waitForTimeout(800);
  const hit = await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
    if (!m) return false; const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (!it) return false; it.click(); return true; });
  await p.waitForTimeout(1400);
  return { hit, gone: !(await ids()).includes(id) };
}
const out = { startedAt: new Date().toISOString(), steps: [], cases: [] };
const log = (...a) => { const s = a.join(' '); console.log(s); out.steps.push(s); };
const MINE = [];
async function makeByRail(kw) {
  const pre = await ids();
  const r = await p.evaluate((k) => { const b = Array.from(document.querySelectorAll('button,[role="button"]')).find((x) => k.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    if (!b) return null; const q = b.getBoundingClientRect(); return { x: Math.round(q.x + q.width / 2), y: Math.round(q.y + q.height / 2) }; }, kw);
  if (!r) { log('  🔴 找不到左栏入口', String(kw)); return null; }
  await p.mouse.click(r.x, r.y); await p.waitForTimeout(2000);
  const c = (await ids()).filter((x) => !pre.includes(x)); if (c[0]) MINE.push(c[0]);
  return c[0] || null;
}
async function probe(label, id, shotName) {
  await deselectReal();
  const c = await p.evaluate((v) => { const r = document.querySelector(`.react-flow__node[data-id="${v}"]`).getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height * 0.75) }; }, id);
  await p.mouse.click(c.x, c.y); await p.waitForTimeout(1200);
  const seld = await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"].selected`), id);
  const plus = await scanPlus(id);
  log(`\n=== ${label} === 选中? ${seld} | ⊕ 数量 ${plus.length}`);
  if (!plus.length) { out.cases.push({ label, id, plus: 0, seld }); return { label, plus: 0 }; }
  log('⊕:', JSON.stringify(plus, null, 1));
  const btn = plus.find((x) => /after/.test(x.aria)) || plus[0];
  await p.mouse.click(btn.cx, btn.cy); await p.waitForTimeout(1600);
  const menu = await p.evaluate(() => { const ms = Array.from(document.querySelectorAll('[role="menu"],[data-testid*="connection-menu"]')).filter((e) => e.getBoundingClientRect().width > 1);
    const el = ms[ms.length - 1]; if (!el) return { none: true };
    const r = el.getBoundingClientRect();
    return { testid: el.getAttribute('data-testid'), aria: el.getAttribute('aria-label'),
      box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      items: Array.from(el.querySelectorAll('[role="menuitem"]')).map((x) => { const q = x.getBoundingClientRect();
        const lines = (x.innerText || '').trim().split('\n').map((s) => s.trim()).filter(Boolean);
        return { name: lines[0], reason: lines.slice(1).join(' / ') || null, dis: x.getAttribute('aria-disabled'),
          cursor: getComputedStyle(x).cursor, box: `${Math.round(q.width)}x${Math.round(q.height)}` }; }) }; });
  log('菜单:', JSON.stringify(menu, null, 1));
  // 配图：菜单 + 节点并集，逐项断言不被裁
  if (shotName && menu && menu.items) {
    const clip = await p.evaluate(() => { const n = document.querySelector('.react-flow__node.selected'); if (!n) return null;
      const ms = Array.from(document.querySelectorAll('[role="menu"],[data-testid*="connection-menu"]')).filter((e) => e.getBoundingClientRect().width > 1);
      const rects = [n.getBoundingClientRect(), ...ms.map((e) => e.getBoundingClientRect())];
      const L = Math.max(0, Math.round(Math.min(...rects.map((r) => r.x)) - 30));
      const T = Math.max(0, Math.round(Math.min(...rects.map((r) => r.y)) - 30));
      const R = Math.min(1280, Math.round(Math.max(...rects.map((r) => r.right)) + 30));
      const B = Math.min(720, Math.round(Math.max(...rects.map((r) => r.bottom)) + 30));
      const keys = [];
      for (const m of ms) for (const it of m.querySelectorAll('[role="menuitem"]')) { const q = it.getBoundingClientRect(); if (q.width <= 1) continue;
        keys.push({ what: (it.innerText || '').trim().split('\n')[0], cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2) }); }
      return { x: L, y: T, width: R - L, height: B - T, keys: keys.map((k) => ({ ...k, ok: k.cx >= L && k.cx <= R && k.cy >= T && k.cy <= B })) }; });
    if (clip) { const bad = clip.keys.filter((k) => !k.ok);
      log('配图 clip', JSON.stringify({ x: clip.x, y: clip.y, width: clip.width, height: clip.height }), '| 项', clip.keys.length, '被裁', bad.length);
      if (!bad.length) {
        await p.screenshot({ path: new URL(shotName, SHOTS).pathname, clip: { x: clip.x, y: clip.y, width: clip.width, height: clip.height } });
        log('📷', shotName);
        out.cases.push({ label, id, plus: plus.length, menu, clip });
        await esc(2);
        return { label, plus: plus.length, menu };
      }
    }
  }
  await esc(2);
  out.cases.push({ label, id, plus: plus.length, menu });
  return { label, plus: plus.length, menu };
}
try {
  log('开跑前:', await status(), '| 缩放', await zoomOf(), '| 积分', await credit());
  // 对照：文本节点（已知有 ⊕，用于证明本轮动作序列有效）
  const txt = await makeByRail(/^文本$/);
  const ctl = await probe('对照组 文本节点', txt, null);
  // 实验：时间线源
  const tl = await makeByRail(/^时间线$/);
  const t1 = await probe('时间线源', tl, '71-timeline-source-menu.png');
  // 实验：主体源
  const sj = await makeByRail(/^主体$/);
  const t2 = await probe('主体源', sj, '71-subject-source-menu.png');
  log('\n=== 汇总 ===');
  log('  文本节点 ⊕', ctl.plus, '| 时间线源 ⊕', t1.plus, '| 主体源 ⊕', t2.plus);
  for (const [lbl, r] of [['文本', ctl], ['时间线', t1], ['主体', t2]]) {
    if (!r.menu || !r.menu.items) { log(`  ${lbl}: 菜单未读到`); continue; }
    const ok = r.menu.items.filter((i) => !i.dis).map((i) => i.name);
    const no = r.menu.items.filter((i) => i.dis).map((i) => `${i.name}(${i.reason || '无原因文案'})`);
    log(`  ${lbl} 源 → 可用: [${ok.join(', ')}]  禁用: [${no.join(', ')}]`);
  }
  log('\n积分:', await credit()); out.creditAfter = await credit();
} catch (e) { console.error('ABORT:', e.message); out.abort = e.message; }
finally {
  await esc(3);
  for (const id of [...new Set(MINE)]) { if (!(await ids()).includes(id)) { log('清理', id, '不存在'); continue; }
    const r = await ctxDelete(id); log('清理', id, '→', r.gone ? '✅ deleted' : '🔴 仍在'); }
  await esc(3);
  for (let t = 0; t < 3; t++) { const z = await zoomOf(); if (z && z.includes('60%')) { log('缩放 60%'); break; }
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
    const sl = 'input[data-testid=canvas-zoom-percent-input]';
    if (await p.$(sl)) { await p.fill(sl, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); } else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } }
  await esc(3);
  const cp = await p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => { const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || ''); return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null]; })));
  let dev = []; for (const [id, b2] of Object.entries(BASE.nodes)) { const c = cp[id]; const d2 = c && b2.canvas ? [Math.round((c[0] - b2.canvas[0]) * 100) / 100, Math.round((c[1] - b2.canvas[1]) * 100) / 100] : 'MISSING';
    if (d2 === 'MISSING' || (Array.isArray(d2) && (Math.abs(d2[0]) > 0.01 || Math.abs(d2[1]) > 0.01))) dev.push([id, d2]); }
  const extra = Object.keys(cp).filter((x) => !BASE.nodes[x]);
  log('终态', await status(), '| 缩放', await zoomOf(), '| 积分', await credit(), '| 节点', Object.keys(cp).length, '| 偏离', JSON.stringify(dev), '| 剩余自建', JSON.stringify(extra));
  out.end = { status: await status(), zoom: await zoomOf(), credit: await credit(), nodes: Object.keys(cp).length, dev, extra };
  writeFileSync(OUT, JSON.stringify(out, null, 1)); log('写入', OUT.pathname);
  await b.close();
}
