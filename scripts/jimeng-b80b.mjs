// 批次 80 · B：补两件事。
// ① **行内重命名的提交动作** —— 页面第 104 行明写「改名提交动作**未执行**，保持画布原状」。
//    上一轮失败原因已定位：按 Esc 关菜单/编辑器时**多按了一次**，把选中态一起取消
//    （`selectedBefore: false`），于是 Rename 钮根本没出现。
//    本轮纪律：**先断言 `selected===true`，再去找 Rename 钮**；找不到就 VOID，不硬点。
// ② **工具条尺寸是否随画布缩放变化** —— 承接批次 78/79 的口径表：
//    浮层（工具条/菜单/面板）在缩放视口之外，预期**不随缩放变**；本轮实测确认或推翻。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const labelOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const scaleOf = () => p.evaluate(() => { const m = /matrix\(([-\d.]+)/.exec(getComputedStyle(document.querySelector('.react-flow__viewport')).transform); return m ? +(+m[1]).toFixed(6) : null; });
const settle = async () => { for (let i = 0; i < 15; i++) { const a = await scaleOf(); await p.waitForTimeout(200); const c = await scaleOf();
  if (a === c) return { scale: c, stable: true }; } return { scale: await scaleOf(), stable: false }; };
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
let mine = null;
const setZoom = async (pct) => { await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
  const sl = 'input[data-testid=canvas-zoom-percent-input]';
  if (!(await p.$(sl))) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); return; }
  await p.fill(sl, String(pct)); await p.keyboard.press('Enter'); await p.waitForTimeout(1400); };
const isSel = (v) => p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  return n ? /(^|\s)selected(\s|$)/.test(n.className) : null; }, v);
/** 保证节点处于选中态。
 *  ⚠️ 自伤修正：上一版无脑点「标题行 y = r.y − 15」，结果 `selected:false` ⇒ 整轮 VOID。
 *  两个原因：① 新节点**本来就自动选中**，根本不需要点；
 *            ② 那个坐标可能落在别的元素上（`elementFromPoint` 没验归属）。
 *  现在：先看自动选中；不行再按候选点试，**每个点先验 elementFromPoint 属于本节点**，
 *        点完**再断言** selected 起来了，没起来就如实报 false（由调用方判 VOID）。 */
const ensureSelected = async (v) => {
  if (await isSel(v)) return { selected: true, via: '自动选中' };
  const tried = [];
  const pts = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); const r = n.getBoundingClientRect();
    const out = [];
    for (const f of [[0.5, -15], [0.25, -15], [0.75, -15], [0.5, 0.5], [0.5, 0.3], [0.5, 0.7], [0.2, 0.5], [0.8, 0.5]]) {
      const x = Math.round(r.x + r.width * f[0]), y = Math.round(r.y + r.height * (f[1] < 0 ? f[1] / r.height : f[1]));
      const h = document.elementFromPoint(x, y);
      if (h && n.contains(h) && !h.closest('[role="menu"]') && h.tagName !== 'INPUT' && h.tagName !== 'TEXTAREA')
        out.push({ x, y, tag: h.tagName, tid: h.getAttribute('data-testid') || '' });
    } return out; }, v);
  for (const q of pts) { await p.mouse.click(q.x, q.y); await p.waitForTimeout(900);
    if (await isSel(v)) { tried.push(`${q.x},${q.y}(${q.tag}${q.tid ? '#' + q.tid : ''})`); return { selected: true, via: '点 ' + tried.join('→') }; }
    tried.push(`${q.x},${q.y}✗`); }
  return { selected: false, via: '试过 ' + tried.join(' ') + '｜候选点 ' + pts.length + ' 个' };
};
try {
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^文本$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3000);
  const made = (await ids()).filter((x) => !pre.includes(x));
  if (made.length !== 1) throw new Error('新建异常');
  mine = made[0]; log('新建', mine);

  // —————————————— ② 工具条 × 缩放（先做，趁节点还新）——————————————
  out.toolbarByZoom = [];
  const sel0 = await ensureSelected(mine); log('选中断言', JSON.stringify(sel0));
  if (!sel0.selected) throw new Error('选中不起来 ⇒ VOID');
  for (const pct of [60, 100, 60]) {
    await setZoom(pct);
    const zz = await settle();
    const r = await p.evaluate(() => {
      const tb = document.querySelector('[data-testid="node-toolbar"]');
      const box = (el) => { if (!el) return null; const b = el.getBoundingClientRect(); return `${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}`; };
      return { nodeToolbar: box(tb),
        items: tb ? Array.from(tb.querySelectorAll('button,[role="button"]')).map((e) => (e.getAttribute('aria-label') || e.innerText || '').trim().split('\n')[0]).filter(Boolean) : null };
    });
    out.toolbarByZoom.push({ pct, scale: zz.scale, ...r });
    log(`node-toolbar @${pct}%`, 'scale', zz.scale, '→', JSON.stringify(r));
  }
  // 编辑态工具条：进编辑态再量
  const selE = await ensureSelected(mine); log('进编辑前选中断言', JSON.stringify(selE));
  if (!selE.selected) throw new Error('进编辑前未选中 ⇒ VOID');
  const bd = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height * 0.62) }; }, mine);
  await p.mouse.dblclick(bd.x, bd.y); await p.waitForTimeout(1300);
  const inEdit = await p.evaluate(() => { const e = document.querySelector('.ProseMirror[contenteditable="true"]'); return { open: !!e, focused: document.activeElement === e }; });
  out.editState = inEdit; log('编辑态', JSON.stringify(inEdit));
  if (!inEdit.open) throw new Error('没进编辑态 ⇒ VOID');
  out.editToolbar = [];
  for (const pct of [100, 60]) {
    await setZoom(pct);
    const zz = await settle();
    const r = await p.evaluate(() => {
      // 编辑态工具条：节点上方那条 8 按钮的
      const cands = Array.from(document.querySelectorAll('div')).filter((e) => {
        const b = e.getBoundingClientRect(); const cs = getComputedStyle(e);
        return cs.position === 'absolute' && b.height > 20 && b.height < 60 && b.width > 200 && b.width < 500 && e.querySelectorAll('button').length >= 8; });
      const el = cands[0] || null;
      if (!el) return { found: false };
      const b = el.getBoundingClientRect();
      return { found: true, screen: `${Math.round(b.width)}x${Math.round(b.height)}@${Math.round(b.x)},${Math.round(b.y)}`,
        n: el.querySelectorAll('button').length,
        labels: Array.from(el.querySelectorAll('button')).map((x) => (x.getAttribute('aria-label') || '').trim()) };
    });
    out.editToolbar.push({ pct, scale: zz.scale, ...r });
    log(`编辑态工具条 @${pct}%`, 'scale', zz.scale, '→', JSON.stringify(r));
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(1000);   // Esc = 提交（批次 80 A 轮已实测）
  log('Esc 后仍选中 =', await p.evaluate((v) => /(^|\s)selected(\s|$)/.test(document.querySelector(`.react-flow__node[data-id="${v}"]`).className), mine));

  // —————————————— ① 行内重命名的提交动作 ——————————————
  const sel1 = await ensureSelected(mine);
  out.rename = { selectedBefore: sel1.selected, via: sel1.via };
  if (!sel1.selected) throw new Error('选中不起来 ⇒ 重命名读数作废(VOID)');
  const rb = await p.evaluate(() => { const el = document.querySelector('button[aria-label^="Rename"]'); if (!el) return null;
    const r = el.getBoundingClientRect(); return { aria: el.getAttribute('aria-label'), x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  out.rename.button = rb; log('Rename 钮', JSON.stringify(rb));
  if (!rb) throw new Error('Rename 钮不出现 ⇒ VOID');
  await p.mouse.click(rb.x, rb.y); await p.waitForTimeout(1000);
  out.rename.afterClick = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
    const i = n.querySelector('input'); const t = n.querySelector('[data-testid=flow-node-title]');
    return { inputFound: !!i, value: i ? i.value : null, focused: i ? document.activeElement === i : false,
      titleText: t ? (t.innerText || '').trim() : null, aria: n.getAttribute('aria-label') }; }, mine);
  log('点 Rename 后', JSON.stringify(out.rename.afterClick));
  if (!out.rename.afterClick.inputFound || !out.rename.afterClick.focused) throw new Error('输入框没出现/没聚焦 ⇒ VOID');
  await p.keyboard.press('Meta+A'); await p.waitForTimeout(250);
  await p.keyboard.type('改名测试80'); await p.waitForTimeout(500);
  out.rename.beforeEnter = await p.evaluate((v) => { const i = document.querySelector(`.react-flow__node[data-id="${v}"] input`); return { value: i ? i.value : null }; }, mine);
  log('输入后', JSON.stringify(out.rename.beforeEnter));
  await p.keyboard.press('Enter'); await p.waitForTimeout(1500);
  out.rename.afterEnter = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
    const t = n.querySelector('[data-testid=flow-node-title]'); const i = n.querySelector('input');
    return { inputStillThere: !!i, titleText: t ? (t.innerText || '').trim() : null, aria: n.getAttribute('aria-label'),
      status: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected/) || ['?'])[0] }; }, mine);
  log('Enter 之后', JSON.stringify(out.rename.afterEnter));
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  for (let i = 0; i < 2; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(450); }
  if (mine) {
    for (let a = 1; a <= 3 && (await ids()).includes(mine); a++) {
      const q = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
        const r = n.getBoundingClientRect();
        for (const f of [[0.5, 0.5], [0.5, 0.2], [0.25, 0.5], [0.75, 0.5], [0.5, 0.8]]) { const x = Math.round(r.x + r.width * f[0]), y = Math.round(r.y + r.height * f[1]);
          const h = document.elementFromPoint(x, y); if (h && n.contains(h) && !h.closest('[role="menu"]')) return { x, y }; } return null; }, mine);
      if (!q) break;
      await p.mouse.click(q.x, q.y, { button: 'right' }); await p.waitForTimeout(1000);
      await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
        const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
      await p.waitForTimeout(1500);
    }
    log('清理', mine, (await ids()).includes(mine) ? '🔴 仍在' : '✅');
  }
  for (let t = 0; t < 3; t++) { const z = await labelOf(); if (z && z.includes('60%')) break; await setZoom(60); }
  const zf = await settle();
  const cp = await p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
    const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
    return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null]; })));
  const dev = []; for (const [id, b2] of Object.entries(BASE.nodes)) { const c = cp[id]; const d = c && b2.canvas ? [Math.round((c[0] - b2.canvas[0]) * 100) / 100, Math.round((c[1] - b2.canvas[1]) * 100) / 100] : 'MISSING';
    if (d === 'MISSING' || (Array.isArray(d) && (Math.abs(d[0]) > 0.01 || Math.abs(d[1]) > 0.01))) dev.push([id, d]); }
  out.end = { status: await status(), zoomLabel: await labelOf(), scale: zf.scale, deviation: dev };
  log('终态', JSON.stringify(out.end));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8')); if (mine && !led.ids.includes(mine)) {
    led.ids = [...new Set([...led.ids, mine])].sort();
    led.per_batch = { ...(led.per_batch || {}), 80: [...new Set([...(led.per_batch?.['80'] || []), mine])] };
    writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b80b.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
