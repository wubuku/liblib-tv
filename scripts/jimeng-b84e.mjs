// 批次 84 · E：收尾 + 把 d 轮两处要如实标注的地方查实。
//
// d 轮留下的两件事：
//
// ① 🔴 **终态 `sel: "1"`** —— 我用框选做前置，选中状态被留在了共享画布上。
//    收尾门会报「选中数不为 0」。点画布空白即可归零，**不需要改任何节点**。
//
// ② 🔴 **格 B 的输入框在我按 G 之前就有内容「音频 6」** ——
//    `before.pm = "音频 6||"`，`after.pm = "g"`。
//    也就是说**我的那一下 G 把一个已存在的引用替换掉了**。
//    这不是「我的测试数据」，是**别人（或上一个会话）留在 Agent 草稿框里的东西**。
//    必须查清楚：① 它是在我点输入框之前就在，还是**我点击那一下**才把它变成「音频 6」的？
//    ② 现在还剩什么？
//    —— 查法：**不点任何东西**，直接读展开态的输入框内容；
//       再用 `elementFromPoint` 看我点的那个坐标 (910,574) 上**本来**是什么元素。
//       两次读数一比就知道是「它本来就在」还是「我点出来的」。
//
// ⚠️ Agent 输入框是**本地草稿态**，不是画布数据（画布节点数/积分全程 20 nodes / 805）。
//    但如实记录仍然必要：这正是共享画布纪律的一部分。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const selCount = () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const zoomLabel = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const zoomPct = async () => { const l = await zoomLabel(); return l ? Number((l.match(/(\d+)%/) || [])[1]) : null; };
const credits = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const pmInfo = () => p.evaluate(() => { const e = document.querySelector('[data-testid="prompt-composer"] .ProseMirror');
  if (!e) return null; const r = e.getBoundingClientRect();
  return { text: (e.innerText || '').replace(/\n/g, '|').slice(0, 40), html: (e.innerHTML || '').slice(0, 200),
    box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; });
const drawerOpen = () => p.evaluate(() => { const s = document.querySelector('[data-testid="canvas-feature-sidecar"]'); if (!s) return null;
  const r = s.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; });
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

try {
  out.enter = { status: await status(), sel: await selCount(), zoom: await zoomLabel(), credits: await credits(), drawer: await drawerOpen() };
  log('进场', JSON.stringify(out.enter));

  // ══════ ② 查实「音频 6」的来历：不点任何东西，只读 ══════
  log('当前输入框（未做任何点击）', JSON.stringify(await pmInfo()));
  const st = await drawerOpen();
  if (st && st.startsWith('200x')) { await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1900); }
  out.afterExpand = { drawer: await drawerOpen(), pm: await pmInfo() };
  log('展开后（没点任何东西）', JSON.stringify(out.afterExpand));
  // 我 d 轮点的那个坐标上本来是什么
  out.probeAt910_574 = await p.evaluate(() => { const h = document.elementFromPoint(910, 574); if (!h) return null;
    const r = h.getBoundingClientRect();
    return { tag: h.tagName, cls: String(h.className || '').split(' ').slice(0, 3).join('.'),
      box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      t: (h.innerText || h.getAttribute('aria-label') || '').trim().slice(0, 24),
      ce: h.getAttribute('contenteditable'), testid: h.getAttribute('data-testid') }; });
  log('(910,574) 上是什么', JSON.stringify(out.probeAt910_574));

  // 收起抽屉，回到默认终态
  const cb = await p.evaluate(() => { const s = document.querySelector('[data-testid="canvas-feature-sidecar"]'); if (!s) return null;
    const x = Array.from(s.querySelectorAll('button,[role="button"]')).find((e) => /收起|折叠|collapse/i.test((e.getAttribute('aria-label') || '') + (e.innerText || '')));
    if (!x) return null; const r = x.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (cb) { await p.mouse.click(cb.x, cb.y); await p.waitForTimeout(1700); }
  out.afterCollapse = { drawer: await drawerOpen() };
  log('收起后', JSON.stringify(out.afterCollapse));

  // ══════ ① 取消 d 轮留下的那 1 个选中 ══════
  const before = await selCount();
  const e = await p.evaluate(() => { const pane = document.querySelector('.react-flow__pane'); if (!pane) return null;
    for (let y = 110; y < 660; y += 20) for (let x = 210; x < 1240; x += 28) { const h = document.elementFromPoint(x, y); if (h && h === pane) return { x, y, hit: h.className }; }
    return null; });
  if (e) { await p.mouse.click(e.x, e.y); await p.waitForTimeout(1000); }
  out.deselect = { before, at: e, after: await selCount(), focus: (await keyGuard(p)).where };
  log('取消选中', JSON.stringify(out.deselect));

  out.zoom = await setZoom(60);
  out.end = { status: await status(), sel: await selCount(), zoom: await zoomLabel(), credits: await credits(), drawer: await drawerOpen() };
  log('终态', JSON.stringify(out.end));
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
writeFileSync(new URL('./_tmp-b84e.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
