// 批次 85 · B：把 a 轮的核心实验做完，并回答那个真正的问题。
//
// a 轮 53% 缩放档的读数（空视频节点、已选中）：
//
//   [0] 屏上 680×208@241,456   canvas 1273×390   ← 生成面板（真身，10 个控件与页面逐字一致）
//   [1] 屏上  304×0  @429,229  canvas   569×0     ← 高度为 0 的占位，**宽度正好等于节点宽 304**
//
// 🔴 由此撞出本页与批次 80 的正面矛盾，必须分清是「量纲错了」还是「有两个不同的东西」：
//
//   本页（批次 63/64）：生成面板 `[data-testid="node-toolbar"]` = **680×208**
//   批次 80          ：节点浮动工具条 `node-toolbar` = 60% 时 **192×40**（canvas 恒 192×40）
//
//   差 5 倍以上，**不可能是同一个东西的不同缩放**。
//   ⇒ 可证伪预测（三条同时成立才算立住）：
//      P1  面板真身的**屏上**尺寸随缩放变 ⇒ `680×208` 是**屏上**读数，页面把它当固定值是错的。
//      P2  面板真身的 **canvas** 尺寸不随缩放变 ⇒ 那条「canvas 恒 X」的话术可以用在它身上。
//      P3  **换一个节点类型**（文本）弹出的 `node-toolbar` 尺寸**完全不同**（≈192×40），
//          ⇒ 同一个 testid 覆盖了**至少两类**面板，「`node-toolbar` = 节点浮动工具条」是错的等式。
//
// ⚠️ a 轮 100%/40% 两档空跑的原因：**改缩放后节点位置变了**，我还在用旧坐标
//    `y = 节点顶 - 20` 去点，落空 ⇒ 没选中 ⇒ 面板没出现。
//    修法：**每次改完缩放都重算落点**（按当场读的 scale 扫标题行），
//    并且**断言选中数 > 0** 才继续，否则该档记 VOID 而不是记「没有面板」。
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
// 🔑 摘要里记过的坑：不能回 DOMRect 上的 getAttribute，也不能在 Node 侧对 evaluate 的返回值再取属性。
//   字符串在 evaluate 内部一次取完。
const zoomPct = async () => { const l = await p.evaluate(() => {
    const e = document.querySelector('button[aria-label^="Zoom options"]');
    return e ? e.getAttribute('aria-label') : null; });
  return l ? Number((l.match(/(\d+)%/) || [])[1]) : null; };
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
/** 🔑 每次都重算落点：按当场 scale 扫标题行，取第一个「在节点内且带文字/aria」的点。 */
const titlePointXY = async (id) => { const sc = await readScale();
  return await p.evaluate((arg) => { const n = document.querySelector(`.react-flow__node[data-id="${arg.v}"]`); if (!n) return null;
    const r = n.getBoundingClientRect(); const tries = [];
    for (let k = -70; k <= 4; k += 3) for (const f of [0.25, 0.5, 0.75]) {
      const x = Math.round(r.x + r.width * f), y = Math.round(r.y + Math.round(k * arg.scale));
      if (x < 0 || y < 0 || y > 716) continue;
      const h = document.elementFromPoint(x, y); if (!h || !n.contains(h)) continue;
      tries.push({ k, f, x, y, txt: (h.innerText || h.getAttribute('aria-label') || '').trim().slice(0, 14) }); }
    const withTxt = tries.filter((t) => t.txt); const pick = withTxt[0] || tries[0] || null;
    return { scale: arg.scale, nodeBox: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      pick, nTries: tries.length }; }, { v: id, scale: sc.scale }); };
const toolbars = () => p.evaluate(() => { const vp = document.querySelector('.react-flow__viewport');
  const m = (vp ? (vp.style.transform || '') : '').match(/scale\(([-\d.]+)\)/); const scale = m ? Number(m[1]) : null;
  return Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).map((e) => { const r = e.getBoundingClientRect();
    const node = e.closest('.react-flow__node');
    return { screen: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      canvas: scale ? `${Math.round(r.width / scale)}x${Math.round(r.height / scale)}` : null,
      area: Math.round(r.width) * Math.round(r.height), scale, svg: e.querySelectorAll('svg').length,
      nInNode: node ? (node.getAttribute('data-id') || '?') : 'renderer',
      text: (e.innerText || '').replace(/\n/g, '｜').slice(0, 110),
      controls: Array.from(e.querySelectorAll('button,[role="button"],[role="combobox"],[contenteditable="true"],input'))
        .map((x) => `${(x.getAttribute('aria-label') || x.innerText || '').trim().replace(/\n/g, ' ').slice(0, 34)} ${Math.round(x.getBoundingClientRect().width)}x${Math.round(x.getBoundingClientRect().height)}`) };
  }).sort((a, b) => b.area - a.area); });
const selCount = () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);

/** 建一个左栏节点（不点它自带的任何东西）。 */
const makeNode = async (label) => { const pre = await ids();
  const rail = await p.evaluate((n) => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
      .find((x) => (x.getAttribute('aria-label') || '').trim() === n || (x.innerText || '').trim() === n);
    if (!el) return null; const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }, label);
  if (!rail) return { err: `左栏找不到「${label}」` };
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(3400);
  const made = (await ids()).filter((x) => !pre.includes(x));
  return { made, n: made.length }; };
/** 选中并断言；断言不过就返回 VOID，不记「没有面板」。 */
const selectAndMeasure = async (id, tag) => { const t = await titlePointXY(id);
  if (!t || !t.pick) return { tag, void: '找不到落点', t };
  await p.mouse.click(t.pick.x, t.pick.y); await p.waitForTimeout(2000);
  const s = await selCount();
  if (s === '0') return { tag, void: `落点没选中（点 ${t.pick.x},${t.pick.y}）`, t, bars: await toolbars() };
  const bars = await toolbars();
  return { tag, sel: s, scale: t.scale, nodeBox: t.nodeBox, pick: t.pick, zoom: await zoomPct(), bars }; };

try {
  out.credits0 = await credits();
  out.zoom0 = await setZoom(60); log('起始缩放', JSON.stringify(out.zoom0));

  // ══════ P1/P2：空视频节点，三个缩放档 ══════
  const v = await makeNode('视频'); log('建视频节点', JSON.stringify(v));
  if (v.n !== 1) throw new Error('建视频失败');
  mine.push(v.made[0]);
  out.video = [];
  for (const z of [60, 100, 40]) {
    out.zoomZ = await setZoom(z);
    const m = await selectAndMeasure(v.made[0], `空视频@${z}%`);
    out.video.push(m);
    log(`── 空视频 @${z}% ──`, m.void ? `VOID：${m.void}` : `选中 ${m.sel} scale ${m.scale}`);
    if (!m.void) m.bars.forEach((t, i) => log(`   [${i}] 屏上 ${t.screen}  canvas ${t.canvas}  svg=${t.svg}  父节点=${t.nInNode}\n       ${t.text}\n       控件: ${t.controls.join(' / ')}`));
  }
  out.predictions = { P1: null, P2: null, P3: null };
  if (out.video.length >= 2 && out.video.every((m) => !m.void)) {
    const big = (m) => m.bars[0];
    const a1 = big(out.video[0]), a2 = big(out.video[1]);
    out.predictions.P1_screenChanges = a1.screen !== a2.screen;
    out.predictions.P1 = `${a1.screen} vs ${a2.screen} ⇒ 屏上${a1.screen !== a2.screen ? '**变**' : '不变'}`;
    out.predictions.P2 = `${a1.canvas} vs ${a2.canvas} ⇒ canvas${a1.canvas !== a2.canvas ? '**变**' : '不变'}`;
    log('P1 屏上是否随缩放变：', out.predictions.P1);
    log('P2 canvas 是否恒定：', out.predictions.P2);
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);

  // ══════ P3：换节点类型，看 node-toolbar 是不是另一个尺寸 ══════
  await setZoom(60);
  out.otherTypes = [];
  for (const label of ['文本', '图片', '音频']) {
    const r = await makeNode(label);
    if (r.n !== 1) { log(`${label} 建节点失败`, JSON.stringify(r)); continue; }
    mine.push(r.made[0]);
    const m = await selectAndMeasure(r.made[0], `${label}@60%`);
    out.otherTypes.push(m);
    log(`── ${label} @60% ──`, m.void ? `VOID：${m.void}` : `选中 ${m.sel}`);
    if (!m.void) m.bars.forEach((t, i) => log(`   [${i}] 屏上 ${t.screen}  canvas ${t.canvas}  svg=${t.svg}\n       ${t.text}\n       控件: ${t.controls.join(' / ')}`));
    await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  }
  out.credits1 = await credits();
  log('积分', out.credits0, '→', out.credits1);
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
finally {
  for (let i = 0; i < 2; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  for (const v2 of mine) {
    for (let a = 1; a <= 3 && (await ids()).includes(v2); a++) {
      const q = await p.evaluate((x) => { const n = document.querySelector(`.react-flow__node[data-id="${x}"]`); if (!n) return null;
        const r = n.getBoundingClientRect();
        for (const f of [[0.5, 0.5], [0.5, 0.2], [0.25, 0.5], [0.75, 0.5], [0.5, 0.8]]) { const X = Math.round(r.x + r.width * f[0]), Y = Math.round(r.y + r.height * f[1]);
          const h = document.elementFromPoint(X, Y); if (h && n.contains(h) && !h.closest('[role="menu"]')) return { x: X, y: Y }; } return null; }, v2);
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
  out.end = { status: await status(), credits: await credits(), leftover: left };
  log('终态', JSON.stringify(out.end));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8'));
    const add = mine.filter((x) => !led.ids.includes(x));
    if (add.length) { led.ids = [...new Set([...led.ids, ...add])].sort();
      led.per_batch = { ...(led.per_batch || {}), 85: [...new Set([...(led.per_batch?.['85'] || []), ...mine])] };
      writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b85b.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
