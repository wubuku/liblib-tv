// 批次 85 · A：审计 `prepare-generation.md`（普查下一名，停在批次 63）。
//
// 🔴 **本页与批次 80 的结论正面相撞**，这正是选它的理由：
//
//   本页（批次 63/64 测的）：「选中一个**空节点**，节点下方弹出生成面板」
//                        「面板 DOM **一律是** `[data-testid="node-toolbar"]`」
//                        「视频面板与图片面板实测同为 **680×208**」
//
//   批次 80（刚测的）  ：「节点浮动工具条 `node-toolbar` **随缩放**
//                        （60% → `192×40`、100% → `320×40`，**canvas 恒 `192×40`**）」
//
//   ⇒ **同一个 testid、两个差 5 倍以上的尺寸。** 三种可能，必须分开：
//     (a) 它们**是同一个元素**，某一页量错了；
//     (b) 它们**是两个不同的元素**，只是**共用了同一个 testid**；
//     (c) 批次 80 撞上了那个 **`0×0` 常驻占位**（它自己记的第三个坑），量到的不是真身。
//
// 🔑 **本轮用批次 78 的核心手法做可证伪实验**：
//   **同一个元素在两个缩放档下各量一次。**
//   · 若 `680×208` 是**屏上**读数 ⇒ 屏上量随缩放变、canvas 量恒定；
//   · 若 `680×208` 是 **canvas** 读数 ⇒ 屏上量随缩放变、canvas 恒定。
//   两种情况的**屏上量都会变**，但**canvas 量哪个恒定**能一句话说清那个数字是什么量纲。
//   顺带把批次 80 的「canvas 恒 192×40」在**同一元素同一时刻**再验一次。
//
// ⛔ 绝不点：生成、下拉（模型/比例/时长/模式）、`添加参考`、`引用参考`。
//    只建节点、只量、只读逐字。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';
const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const mine = [];
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const credits = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const zoomLabel = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const zoomPct = async () => { const l = await zoomLabel(); return l ? Number((l.match(/(\d+)%/) || [])[1]) : null; };
const readScale = async () => { const rd = () => p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
    const m = (vp ? (vp.style.transform || '') : '').match(/scale\(([-\d.]+)\)/); return m ? Number(m[1]) : null; });
  const a = await rd(); await p.waitForTimeout(500); const c = await rd(); return { scale: a, stable: a !== null && a === c }; };
const setZoom = async (t0) => { for (let t = 1; t <= 3; t++) { if (await zoomPct() === t0) return { ok: true, how: 'already' };
    await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(800);
    if (!await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); continue; }
    await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
      i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t0);
    await p.waitForTimeout(1300); await p.keyboard.press('Escape'); await p.waitForTimeout(600);
    const a = await zoomPct(); await p.waitForTimeout(900); const c = await zoomPct();
    if (a === c && a === t0) return { ok: true, how: 'input', pct: a }; }
  return { ok: false, pct: await zoomPct() }; };

/** 🔑 把所有 `[data-testid="node-toolbar"]` 全列出来（按面积降序），屏上 + canvas 两种口径都给。 */
const toolbars = () => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const m = (vp ? (vp.style.transform || '') : '').match(/scale\(([-\d.]+)\)/);
  const scale = m ? Number(m[1]) : null;
  return Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).map((e) => {
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    const parent = e.closest('.react-flow__node');
    return {
      screen: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      area: Math.round(r.width) * Math.round(r.height),
      canvas: scale ? `${Math.round(r.width / scale)}x${Math.round(r.height / scale)}` : null,
      w: Math.round(r.width), h: Math.round(r.height), scale,
      parentIs: parent ? (parent.getAttribute('data-id') || '?') : 'renderer',
      parentChain: (() => { const c = []; let q = e.parentElement;
        for (let i = 0; q && i < 4; i++) { c.push(q.tagName + (q.getAttribute('data-testid') ? '[' + q.getAttribute('data-testid') + ']' : '') + (q.className ? '.' + String(q.className).split(' ')[0] : '')); q = q.parentElement; } return c; })(),
      pos: cs.position, display: cs.display, vis: cs.visibility, op: cs.opacity, pe: cs.pointerEvents,
      z: cs.zIndex, overflow: cs.overflow,
      text: (e.innerText || '').replace(/\n/g, ' ｜ ').slice(0, 130),
      controls: Array.from(e.querySelectorAll('button,[role="button"],[role="combobox"],[contenteditable="true"],input'))
        .map((x) => { const xr = x.getBoundingClientRect();
          return `${(x.getAttribute('aria-label') || x.innerText || x.getAttribute('placeholder') || '').trim().replace(/\n/g, ' ').slice(0, 40)} ${Math.round(xr.width)}x${Math.round(xr.height)}`; }),
      svgCount: e.querySelectorAll('svg').length };
  }).sort((a, b) => b.area - a.area);
});

try {
  out.credits0 = await credits();
  out.zoom0 = await setZoom(60); log('缩放', JSON.stringify(out.zoom0), '积分', out.credits0);

  // ══════ 建一个空视频节点 ══════
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^视频$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (!rail) throw new Error('左栏找不到「视频」按钮');
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3400);
  const made = (await ids()).filter((x) => !pre.includes(x));
  log('新建', made.length, made.join(' '), '缩放=', await zoomPct());
  if (made.length !== 1) throw new Error('新建异常 ' + made.length);
  mine.push(made[0]);
  out.nodeBox = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect();
    return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; }, made[0]);
  log('节点屏上', out.nodeBox);

  // ══════ 选中它（点标题行，scale-aware 落点） ══════
  const sc = await readScale();
  const title = await p.evaluate((arg) => { const n = document.querySelector(`.react-flow__node[data-id="${arg.v}"]`); if (!n) return null;
    const r = n.getBoundingClientRect();
    for (let k = -70; k <= 4; k += 3) for (const f of [0.25, 0.5, 0.75]) { const x = Math.round(r.x + r.width * f), y = Math.round(r.y + Math.round(k * arg.scale));
      if (x < 0 || y < 0 || y > 716) continue; const h = document.elementFromPoint(x, y);
      if (h && n.contains(h) && (h.innerText || h.getAttribute('aria-label'))) return { x, y, txt: (h.innerText || '').trim().slice(0, 12) }; }
    return null; }, { v: made[0], scale: sc.scale });
  out.title = title; log('标题落点', JSON.stringify(title), 'scale=', sc.scale);
  if (title) { await p.mouse.click(title.x, title.y); await p.waitForTimeout(2000); }
  out.sel = { count: await p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]), focus: (await keyGuard(p)).where };
  log('选中', JSON.stringify(out.sel));

  // ══════ 档 1：60% —— 量 node-toolbar 全列 ══════
  out.at60 = { zoom: await zoomPct(), scale: await readScale(), bars: await toolbars() };
  log(`── 60% 档：node-toolbar 命中 ${out.at60.bars.length} 个 ──`);
  out.at60.bars.forEach((t, i) => log(`  [${i}] 屏上 ${t.screen}  canvas ${t.canvas}  父 ${t.parentIs}/${t.parentChain[0]}  pos=${t.pos} vis=${t.vis} op=${t.op} z=${t.z} svg=${t.svgCount}\n       文本: ${t.text}\n       控件: ${t.controls.join(' / ')}`));

  // ══════ 档 2：100% —— 同一元素再量一次（可证伪实验的核心） ══════
  out.zoom1 = await setZoom(100); log('切到', JSON.stringify(out.zoom1));
  // 缩放变了，节点可能移出视野/被遮挡，重新选一次
  await p.waitForTimeout(1200);
  const sel2 = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y - 20), box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; }, made[0]);
  out.at100Before = sel2; log('100% 下节点', JSON.stringify(sel2));
  if (sel2 && sel2.y > 4) { await p.mouse.click(sel2.x, sel2.y); await p.waitForTimeout(1800); }
  out.at100 = { zoom: await zoomPct(), scale: await readScale(), bars: await toolbars(),
    sel: await p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]) };
  log(`── 100% 档：node-toolbar 命中 ${out.at100.bars.length} 个（选中 ${out.at100.sel}）──`);
  out.at100.bars.forEach((t, i) => log(`  [${i}] 屏上 ${t.screen}  canvas ${t.canvas}  父 ${t.parentIs}/${t.parentChain[0]}  pos=${t.pos} vis=${t.vis} op=${t.op} z=${t.z} svg=${t.svgCount}\n       文本: ${t.text}\n       控件: ${t.controls.join(' / ')}`));

  // ══════ 档 3：40% —— 第三个数据点 ══════
  out.zoom2 = await setZoom(40);
  await p.waitForTimeout(1000);
  const sel3 = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y - 20) }; }, made[0]);
  if (sel3 && sel3.y > 4) { await p.mouse.click(sel3.x, sel3.y); await p.waitForTimeout(1800); }
  out.at40 = { zoom: await zoomPct(), scale: await readScale(), bars: await toolbars(),
    sel: await p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]) };
  log(`── 40% 档：node-toolbar 命中 ${out.at40.bars.length} 个（选中 ${out.at40.sel}）──`);
  out.at40.bars.forEach((t, i) => log(`  [${i}] 屏上 ${t.screen}  canvas ${t.canvas}  svg=${t.svgCount}\n       文本: ${t.text}`));

  out.credits1 = await credits();
  log('积分', out.credits0, '→', out.credits1);
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  for (let i = 0; i < 2; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  for (const v of mine) {
    for (let a = 1; a <= 3 && (await ids()).includes(v); a++) {
      const q = await p.evaluate((x) => { const n = document.querySelector(`.react-flow__node[data-id="${x}"]`); if (!n) return null;
        const r = n.getBoundingClientRect();
        for (const f of [[0.5, 0.5], [0.5, 0.2], [0.25, 0.5], [0.75, 0.5], [0.5, 0.8]]) { const X = Math.round(r.x + r.width * f[0]), Y = Math.round(r.y + r.height * f[1]);
          const h = document.elementFromPoint(X, Y); if (h && n.contains(h) && !h.closest('[role="menu"]')) return { x: X, y: Y }; } return null; }, v);
      if (!q) break;
      await p.mouse.click(q.x, q.y, { button: 'right' }); await p.waitForTimeout(950);
      await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
        const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
      await p.waitForTimeout(1400);
    }
  }
  const left = (await ids()).filter((x) => mine.includes(x));
  log('清理', mine.length, '→ 剩', left.length, left.length ? '🔴 ' + left.join(' ') : '✅');
  out.zoomFinal = await setZoom(60);
  out.end = { status: await status(), zoom: await zoomLabel(), credits: await credits(), leftover: left };
  log('终态', JSON.stringify(out.end));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8'));
    const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort();
      led.per_batch = { ...(led.per_batch || {}), 85: [...new Set([...(led.per_batch?.['85'] || []), ...mine])] };
      writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b85a.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
