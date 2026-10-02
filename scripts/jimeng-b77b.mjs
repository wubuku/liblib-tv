// 批次 77 · B：补齐 ⌘D 副本命名在**文本 / 主体**上的读数。
// 主轮两处没测到：① 文本 —— 单击卡片进了编辑态，`selected` 不成立；
//               ② 主体 —— keyGuard 拦下（焦点在 `TEXTAREA aria="描述"`），
//               这不是失败而是**守卫按设计生效**，必须换个落点再按。
// 页面已经写明正解是「点标题行选中」；主体再多一步：先点标题行再复查守卫。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const OUT = new URL('./_tmp-b77b.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const esc = async (n = 1) => { for (let i = 0; i < n; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } };
const selCount = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
/** 点**标题行**：页面上写明的正解（点卡片主体会进编辑态） */
async function selectByTitle(id) {
  const t = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
    const title = n.querySelector('.flow-node-title,[data-testid="node-title"],.react-flow__node-title') || n;
    const r = title.getBoundingClientRect();
    return { x: Math.round(r.x + Math.min(r.width / 2, 30)), y: Math.round(r.y + r.height / 2), box: `${Math.round(r.width)}x${Math.round(r.height)}` }; }, id);
  if (!t) return { ok: false, why: 'no node' };
  await p.mouse.click(t.x, t.y); await p.waitForTimeout(900);
  const ok = await p.evaluate((v) => !!document.querySelector(`.react-flow__node[data-id="${v}"].selected`), id);
  return { ok, at: t, focus: await keyGuard(p) };
}
async function ctxDelete(id) {
  const box = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 14) }; }, id);
  if (!box) return true;
  await p.mouse.click(box.x, box.y, { button: 'right' }); await p.waitForTimeout(1000);
  await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
    const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
  await p.waitForTimeout(1500); return !(await ids()).includes(id);
}
const out = { startedAt: new Date().toISOString(), created: [], dup: [] };
const log = (...a) => console.log(a.join(' '));
let mine = null;
try {
  log('开跑前:', await status(), '| 缩放', await zoomOf(), '| 积分', await credit());
  for (const kind of ['文本', '主体']) {
    const pre = await ids();
    const rail = await p.evaluate((k) => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
      .find((x) => new RegExp('^' + k + '$').test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
      const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }, kind);
    await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(2400);
    const created = (await ids()).filter((x) => !pre.includes(x));
    if (created.length !== 1) { log(`🔴 ${kind} 新建异常`); await esc(2); continue; }
    const id = created[0]; mine = id; out.created.push(id);
    await esc(1);
    const sel = await selectByTitle(id);
    log(`\n── ${kind} 点标题行 ${JSON.stringify(sel.at && sel.at.box)} → selected=${sel.ok}｜焦点 ${sel.focus.where} 安全=${sel.focus.safe}`);
    if (!sel.ok) { log(`   ⛔ 标题行也没选中 ⇒ 本轮 ⌘D 作废（记录前置不成立）`); }
    else if (!sel.focus.safe) {
      // 主体：焦点还在描述框里 ⇒ 先点画布空白再重新点标题行
      log('   ↺ 焦点不安全（' + sel.focus.where + '）→ 点空白后重试一次');
      await esc(1);
      const blank = await p.evaluate(() => { for (let y = 140; y < 640; y += 20) for (let x = 140; x < 1180; x += 20) {
        const el = document.elementFromPoint(x, y); if (!el || el.closest('.react-flow__node')) continue;
        if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="dialog"],[data-testid="node-toolbar"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"]')) continue;
        return { x, y }; } return null; });
      if (blank) { await p.mouse.click(blank.x, blank.y); await p.waitForTimeout(700); }
      const sel2 = await selectByTitle(id);
      log(`   重试 → selected=${sel2.ok}｜焦点 ${sel2.focus.where} 安全=${sel2.focus.safe}`);
      if (!sel2.ok || !sel2.focus.safe) { log('   ⛔ 仍不安全 ⇒ ⌘D 作废（不硬按）'); }
      else await runDup(kind, id);
    } else await runDup(kind, id);
    async function runDup(k, nodeId) {
      const before = await ids();
      await p.keyboard.press('Meta+d'); await p.waitForTimeout(1500);
      const after = await ids();
      const made = after.filter((x) => !before.includes(x));
      const rec = { kind: k, createdCount: made.length, n0: before.length, n1: after.length };
      if (made.length === 1) {
        const g = await p.evaluate(([a, c]) => { const f = (e) => { const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || ''); return m ? [parseFloat(m[1]), parseFloat(m[2])] : null; };
          const box = (e) => e ? [Math.round(e.getBoundingClientRect().width), Math.round(e.getBoundingClientRect().height)] : null;
          const A = document.querySelector(`.react-flow__node[data-id="${a}"]`), C = document.querySelector(`.react-flow__node[data-id="${c}"]`);
          return { a: f(A), c: f(C), ab: box(A), cb: box(C),
            }; }, [nodeId, made[0]]);
        // ⚠️ 自伤修正：上一版把 `document.querySelector` 写在了 **Node 侧**
        //    （page.evaluate 之外）⇒ `document is not defined`。取标题必须在页面里取。
        const titles = await p.evaluate(([a, c]) => [a, c].map((v) => {
          const e = document.querySelector(`.react-flow__node[data-id="${v}"]`);
          return e ? e.innerText.trim().split('\n').slice(0, 2) : null;
        }), [nodeId, made[0]]);
        rec.origTitle = titles[0]; rec.dupTitle = titles[1];
        rec.dx = g.a && g.c ? Math.round((g.c[0] - g.a[0]) * 100) / 100 : null;
        rec.dy = g.a && g.c ? Math.round((g.c[1] - g.a[1]) * 100) / 100 : null;
        rec.sameBox = JSON.stringify(g.ab) === JSON.stringify(g.cb);
        log(`   ⌘D → 新增 1｜原 ${JSON.stringify(rec.origTitle)} → 副本 ${JSON.stringify(rec.dupTitle)}｜dx=${rec.dx} dy=${rec.dy}｜同尺寸 ${rec.sameBox}`);
        await p.keyboard.press('Meta+z'); await p.waitForTimeout(1300);
        rec.afterUndo = { gone: !(await ids()).includes(made[0]), nodes: (await ids()).length };
        log(`   ⌘Z → ${rec.afterUndo.gone ? '✅ 已撤销' : '🔴 仍在'}｜节点数 ${rec.afterUndo.nodes}`);
      } else log(`   ⌘D → 新增 ${made.length} 个（≠1，不作断言）`);
      out.dup.push(rec);
      await esc(2);
    }
    log(`   清理 ${id} ${(await ctxDelete(id)) ? '✅' : '🔴 仍在'}`); mine = null;
  }
  log('\n积分（全程）:', await credit());
} catch (e) { console.error('ABORT:', e.message); out.abort = e.message; }
finally {
  await esc(3);
  if (mine && (await ids()).includes(mine)) log('清理', mine, (await ctxDelete(mine)) ? '✅ deleted' : '🔴 仍在');
  await esc(3);
  for (let t = 0; t < 3; t++) { const z = await zoomOf(); if (z && z.includes('60%')) break;
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
    const sl = 'input[data-testid=canvas-zoom-percent-input]';
    if (await p.$(sl)) { await p.fill(sl, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); } else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } }
  const cp = await p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
    const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
    return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null]; })));
  const dev = []; for (const [id, b2] of Object.entries(BASE.nodes)) { const c = cp[id]; const d = c && b2.canvas ? [Math.round((c[0] - b2.canvas[0]) * 100) / 100, Math.round((c[1] - b2.canvas[1]) * 100) / 100] : 'MISSING';
    if (d === 'MISSING' || (Array.isArray(d) && (Math.abs(d[0]) > 0.01 || Math.abs(d[1]) > 0.01))) dev.push([id, d]); }
  const extra = Object.keys(cp).filter((x) => !BASE.nodes[x]);
  out.end = { status: await status(), zoom: await zoomOf(), credit: await credit(), nodes: Object.keys(cp).length, dev, extra };
  log('终态', JSON.stringify(out.end));
  writeFileSync(OUT, JSON.stringify(out, null, 1));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8')); led.ids = [...new Set([...(led.ids || []), ...out.created])].sort();
    led.per_batch = { ...(led.per_batch || {}), '77b': out.created }; writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } catch {}
  await b.close();
}
