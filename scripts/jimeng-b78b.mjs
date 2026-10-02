// 批次 78 · B：重拍空视频节点配图。
// 第一版 clip 把**别人节点**的缩略图串进了左上角（批次 64 的裁切纪律）。
// 修法：先把自己的节点**拖到一块空白处**（只拖自建节点，不碰他人），
// 裁切前**逐个断言 clip 内没有别的节点的矩形**。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const LEDGER = new URL('./jimeng-ephemeral-ledger.json', import.meta.url);
const SHOTS = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const esc = async (n = 1) => { for (let i = 0; i < n; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } };
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const log = (...a) => console.log(a.join(' '));
let mine = null;
try {
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^视频$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(2600);
  const created = (await ids()).filter((x) => !pre.includes(x));
  if (created.length !== 1) throw new Error('新建异常');
  mine = created[0];
  await esc(1);
  // —— 找一个**屏幕上**远离所有他人节点的落点，再把自己的节点拖过去
  const target = await p.evaluate(([v]) => {
    const others = Array.from(document.querySelectorAll('.react-flow__node'))
      .filter((n) => n.getAttribute('data-id') !== v).map((n) => n.getBoundingClientRect());
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect();
    let best = null;
    for (let y = 120; y < 560; y += 20) for (let x = 260; x < 1180; x += 20) {
      const w = r.width, h = r.height;
      const box = { x: x - w / 2, y: y - h / 2, right: x + w / 2, bottom: y + h / 2 };
      if (box.x < 8 || box.y < 8 || box.right > innerWidth - 8 || box.bottom > innerHeight - 8) continue;
      if (others.some((o) => box.x < o.right + 12 && box.right + 12 > o.x && box.y < o.bottom + 12 && box.bottom + 12 > o.y)) continue;
      const d = Math.hypot(x - (r.x + r.width / 2), y - (r.y + r.height / 2));
      if (!best || d < best.d) best = { x, y, d: Math.round(d) };
    }
    return { best, from: { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }, box: `${Math.round(r.width)}x${Math.round(r.height)}` };
  }, [mine]);
  log('节点', mine, target.box);
  // 拖拽 + 复核的**原子循环**：同画布上别人正在动节点，
  // 「先找空位、再拖过去、再截图」中间对方一动位置就作废（第二版就是这么翻车的），
  // 所以**拖完立刻复核**，被占就换位置重来，最多 3 次。
  let clip = null, tries = [];
  for (let attempt = 1; attempt <= 3 && !clip; attempt++) {
    const from = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; }, mine);
    const others = await p.evaluate(([v]) => Array.from(document.querySelectorAll('.react-flow__node'))
      .filter((o) => o.getAttribute('data-id') !== v)
      .map((o) => { const r = o.getBoundingClientRect(); return { x: r.x, y: r.y, right: r.right, bottom: r.bottom }; }), [mine]);
    const w = target.box.split('x')[0] | 0, h = target.box.split('x')[1].split('@')[0] | 0;
    let best = null;
    for (let y = 140; y < 600; y += 20) for (let x = 300; x < 1180; x += 20) {
      const box = { x: x - w / 2, y: y - h / 2, right: x + w / 2, bottom: y + h / 2 };
      if (box.x < 8 || box.y < 8 || box.right > 1272 || box.bottom > 712) continue;
      if (others.some((o) => box.x < o.right + 16 && box.right + 16 > o.x && box.y < o.bottom + 16 && box.bottom + 16 > o.y)) continue;
      const d = Math.hypot(x - from.x, y - from.y);
      if (!best || d < best.d) best = { x, y, d: Math.round(d) };
    }
    if (!best) { tries.push(`第 ${attempt} 次：找不到空位`); continue; }
    const grab = await p.evaluate(([x, y, v]) => { const el = document.elementFromPoint(x, y); return !!(el && el.closest(`.react-flow__node[data-id="${v}"]`)); }, [from.x, from.y, mine]);
    if (!grab) { tries.push(`第 ${attempt} 次：起点不在自己的节点上 ⇒ 拒绝拖`); continue; }
    await p.mouse.move(from.x, from.y); await p.waitForTimeout(220);
    await p.mouse.down(); await p.waitForTimeout(180);
    for (let i = 1; i <= 10; i++) { await p.mouse.move(Math.round(from.x + (best.x - from.x) * i / 10), Math.round(from.y + (best.y - from.y) * i / 10)); await p.waitForTimeout(70); }
    await p.mouse.up(); await p.waitForTimeout(1100);
    const c = await p.evaluate((v) => {
      const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect();
      const L = Math.max(0, Math.round(r.x - 16)), T = Math.max(0, Math.round(r.y - 16));
      const R = Math.min(innerWidth, Math.round(r.right + 16)), B = Math.min(innerHeight, Math.round(r.bottom + 16));
      const intr = Array.from(document.querySelectorAll('.react-flow__node')).filter((o) => o.getAttribute('data-id') !== v)
        .map((o) => ({ id: o.getAttribute('data-id'), r: o.getBoundingClientRect() }))
        .filter(({ r }) => r.x < R && r.right > L && r.y < B && r.bottom > T).map(({ id }) => id);
      return { x: L, y: T, width: R - L, height: B - T, intruding: intr, at: best = { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) } };
    }, mine);
    tries.push(`第 ${attempt} 次 → 中心 ${JSON.stringify(c.at)}｜clip 内他人节点 ${c.intruding.length} 个 ${JSON.stringify(c.intruding)}`);
    if (!c.intruding.length) clip = c;
  }
  log(tries.join('\n'));
  if (!clip) throw new Error('3 次都没抢到干净位置');
  if (false) { const _unused = await p.evaluate((v) => {
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect();
    const L = Math.max(0, Math.round(r.x - 16)), T = Math.max(0, Math.round(r.y - 16));
    const R = Math.min(innerWidth, Math.round(r.right + 16)), B = Math.min(innerHeight, Math.round(r.bottom + 16));
    // ⚠️ 自伤修正：上一版先 `.map(o => o.getBoundingClientRect())` 之后又去调
    //    `o.getAttribute('data-id')` —— 此时 o 已是 DOMRect ⇒ TypeError。
    //    正确做法：先取出 {id, rect} **对**，再过滤。
    const intr = Array.from(document.querySelectorAll('.react-flow__node'))
      .filter((o) => o.getAttribute('data-id') !== v)
      .map((o) => ({ id: o.getAttribute('data-id'), r: o.getBoundingClientRect() }))
      .filter(({ r }) => r.x < R && r.right > L && r.y < B && r.bottom > T)
      .map(({ id }) => id);
    return { x: L, y: T, width: R - L, height: B - T, intruding: intr };
  }, mine); }
  log('clip', JSON.stringify(clip));
  if (clip.intruding.length) throw new Error('clip 内仍有他人节点：' + clip.intruding.join(','));
  await p.screenshot({ path: new URL('78-empty-video-node-card.png', SHOTS).pathname, clip: { x: clip.x, y: clip.y, width: clip.width, height: clip.height } });
  log('📷 78-empty-video-node-card.png（重拍，clip 内他人节点 0 个）');
  await esc(2);
} catch (e) { console.error('ABORT:', e.message); }
finally {
  await esc(3);
  if (mine) {
    const box = await p.evaluate((v) => { const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); if (!n) return null; const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 14) }; }, mine);
    if (box) { await p.mouse.click(box.x, box.y, { button: 'right' }); await p.waitForTimeout(1000);
      await p.evaluate(() => { const m = Array.from(document.querySelectorAll('[data-testid="canvas-context-menu"],[role="menu"]')).filter((e) => e.getBoundingClientRect().width > 1).pop();
        const it = m && Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /删除/.test(x.innerText || '')); if (it) it.click(); });
      await p.waitForTimeout(1500); }
    log('清理', mine, (await ids()).includes(mine) ? '🔴 仍在' : '✅');
  }
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
  log('终态', status(), '| 缩放', await zoomOf(), '| 偏离', JSON.stringify(dev));
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8')); if (mine && !led.ids.includes(mine)) { led.ids = [...new Set([...led.ids, mine])].sort(); writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  await b.close();
}
