// 批次 78 · C：空视频节点「播放占位图标 vs 真的可点控件」+ 「暂无视频」为何不显示。
// 上一版（b78b）拍到的画面：卡片里只有一个居中的播放形图标，没有任何文字。
// 但 DOM 读数里明明有 `video-node-empty 322x181 文字「暂无视频」` ——
// 这就是批次 76 那个坑的同构题：**「读得到」≠「看得见」**（sr-only 假阴性/假阳性）。
// 这里只读不点：不 click 那个图标，只读它的 cursor / elementFromPoint / Range 文本矩形。
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
const out = { startedAt: new Date().toISOString() };
let mine = null;
try {
  log('开场', await status(), '| 缩放', await zoomOf());
  const pre = await ids();
  const rail = await p.evaluate(() => { const el = Array.from(document.querySelectorAll('button,[role="button"]'))
    .find((x) => /^视频$/.test(((x.getAttribute('aria-label') || '') + (x.innerText || '')).trim()));
    const r = el.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  await p.mouse.click(rail.x, rail.y); await p.waitForTimeout(2600);
  // ⚠️ 自伤修正①：上一行写成 `const created = (ids = await ids())...`，
  //    `ids` 是 const ⇒ Assignment to constant variable ⇒ 抛在 `mine = created[0]` **之前**
  //    ⇒ finally 里 `if (mine)` 为假 ⇒ 刚建的节点**没被清掉**，留了个孤儿在共享画布上。
  //    现在：先算 created、先断言、再落定 mine，之后任何一步炸了都能收干净。
  const nowIds = await ids();
  const created = nowIds.filter((x) => !pre.includes(x));
  if (created.length !== 1) throw new Error('新建异常：' + JSON.stringify(created));
  mine = created[0];
  log('新建', mine);
  // —— 拖到空白处，拖完**立刻**复核（他人会在这中间移动节点）
  const target = await p.evaluate((v) => {
    const others = Array.from(document.querySelectorAll('.react-flow__node'))
      .filter((n) => n.getAttribute('data-id') !== v).map((n) => n.getBoundingClientRect());
    const r = document.querySelector(`.react-flow__node[data-id="${v}"]`).getBoundingClientRect();
    for (let y = 120; y < 560; y += 20) for (let x = 260; x < 1180; x += 20) {
      const box = { x: x - r.width / 2, y: y - r.height / 2, right: x + r.width / 2, bottom: y + r.height / 2 };
      if (box.x < 8 || box.y < 8 || box.right > innerWidth - 8 || box.bottom > innerHeight - 8) continue;
      if (others.some((o) => box.x < o.right + 12 && box.right + 12 > o.x && box.y < o.bottom + 12 && box.bottom + 12 > o.y)) continue;
      return { x, y };
    } return null;
  }, mine);
  if (!target) throw new Error('找不到空位');
  // 落点必须属于本节点（中心是图标，改用左 1/4 处并用 elementFromPoint 确认）
  const grip = await p.evaluate((v) => {
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect();
    const cx = Math.round(r.x + r.width * 0.22), cy = Math.round(r.y + r.height * 0.5);
    const hit = document.elementFromPoint(cx, cy);
    return { cx, cy, ok: !!hit && n.contains(hit), hit: hit ? `${hit.tagName}.${(hit.getAttribute('class') || '').slice(0, 40)}` : 'null' };
  }, mine);
  log('抓手', JSON.stringify(grip));
  if (!grip.ok) throw new Error('抓手落点不属于本节点');
  await p.mouse.move(grip.cx, grip.cy); await p.mouse.down();
  for (let i = 1; i <= 10; i++) { await p.mouse.move(Math.round(grip.cx + (target.x - grip.cx) * i / 10), Math.round(grip.cy + (target.y - grip.cy) * i / 10)); await p.waitForTimeout(70); }
  await p.mouse.up(); await p.waitForTimeout(1100);

  // —— 前置条件断言：selected 必须是 true，否则下面所有「选中态读数」作废
  const pre1 = await p.evaluate((v) => {
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
    return { selected: n.classList.contains('selected') || !!n.closest('.selected'), cls: n.className, group: !!document.querySelector('.react-flow__node-group') };
  }, mine);
  log('前置', JSON.stringify(pre1));
  if (!pre1.selected) throw new Error('拖完未保持选中 ⇒ 读数作废(VOID)');
  if (pre1.group) throw new Error('画布存在组节点 ⇒ 分组污染读数(VOID)');

  // —— 只读探针：video-node-empty 的文字到底画没画
  const probe = await p.evaluate((v) => {
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
    const e = n.querySelector('.video-node-empty');
    if (!e) return { found: false };
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    const walk = document.createTreeWalker(e, NodeFilter.SHOW_TEXT);
    const texts = []; let t;
    while ((t = walk.nextNode())) {
      const s = (t.textContent || '').trim(); if (!s) continue;
      const rg = document.createRange(); rg.selectNodeContents(t);
      const rects = Array.from(rg.getClientRects()).map((x) => ({ w: +x.width.toFixed(2), h: +x.height.toFixed(2) }));
      const ts = getComputedStyle(t.parentElement);
      texts.push({ s, rects, color: ts.color, fontSize: ts.fontSize, visibility: ts.visibility, opacity: ts.opacity, clip: ts.clip, clipPath: ts.clipPath, w: ts.whiteSpace, overflow: ts.overflowWrap, parentCls: (t.parentElement.getAttribute('class') || '').slice(0, 60) });
    }
    const srOnly = []; for (let x = e; x && x !== document.body; x = x.parentElement) if (/sr-only/.test(x.getAttribute('class') || '')) srOnly.push((x.getAttribute('class') || '').slice(0, 60));
    // 播放图标：落点是谁？cursor 是不是 pointer？（不点，只读）
    const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    const hit = document.elementFromPoint(cx, cy);
    const chain = []; for (let x = hit; x && x !== document.body; x = x.parentElement) { const c = getComputedStyle(x); chain.push(`${x.tagName}.${(x.getAttribute('class') || '').slice(0, 34)}|cursor=${c.cursor}|pe=${c.pointerEvents}`); if (chain.length > 5) break; }
    return {
      found: true, box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      selfOpacity: cs.opacity, selfVisibility: cs.visibility, selfColor: cs.color, selfOverflow: cs.overflow, selfBg: cs.backgroundColor,
      srOnlyAncestors: srOnly, texts,
      iconHit: hit ? `${hit.tagName}.${(hit.getAttribute('class') || '').slice(0, 50)}` : 'null', iconChain: chain,
      html: e.outerHTML.slice(0, 500),
    };
  }, mine);
  out.probe = probe;
  log('探针', JSON.stringify(probe, null, 1));

  // —— 重拍：padding 自适应，断言「我要写进 alt 的元素」都落在 clip 内
  const clipInfo = await p.evaluate((v) => {
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect();
    const want = ['.flow-node-title', '.flow-node-target-connection-menu-button', '.flow-node-source-connection-menu-button', '.video-node-empty']
      .map((s) => ({ s, el: n.querySelector(s) })).filter((o) => o.el).map((o) => ({ s: o.s, r: o.el.getBoundingClientRect() }));
    let pad = 16;
    for (const { r: w } of want) {
      pad = Math.max(pad, Math.round(r.x - w.x), Math.round(w.right - r.right), Math.round(r.y - w.y), Math.round(w.bottom - r.bottom));
    }
    pad = Math.min(pad, 40);
    const L = Math.max(0, Math.round(r.x - pad)), T = Math.max(0, Math.round(r.y - pad));
    const R = Math.min(innerWidth, Math.round(r.right + pad)), B = Math.min(innerHeight, Math.round(r.bottom + pad));
    const intr = Array.from(document.querySelectorAll('.react-flow__node')).filter((o) => o.getAttribute('data-id') !== v)
      .map((o) => ({ id: o.getAttribute('data-id'), r: o.getBoundingClientRect() }))
      .filter(({ r: o }) => o.x < R && o.right > L && o.y < B && o.bottom > T).map(({ id }) => id);
    const outside = want.filter(({ r: w }) => w.x < L || w.right > R || w.y < T || w.bottom > B).map(({ s }) => s);
    return { pad, clip: { x: L, y: T, width: R - L, height: B - T }, intruding: intr, outside, wantCount: want.length };
  }, mine);
  out.clip = clipInfo;
  log('clip', JSON.stringify(clipInfo));
  if (clipInfo.intruding.length) throw new Error('clip 内有他人节点：' + clipInfo.intruding.join(','));
  if (clipInfo.outside.length) throw new Error('以下元素没被裁进来：' + clipInfo.outside.join(','));
  await p.screenshot({ path: new URL('78-empty-video-node-card.png', SHOTS).pathname, clip: clipInfo.clip });
  log('📷 78-empty-video-node-card.png（选中态，pad=' + clipInfo.pad + '，目标元素 ' + clipInfo.wantCount + ' 个全在 clip 内，clip 内他人节点 0 个）');
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
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
  out.end = { status: await status(), zoom: await zoomOf(), deviation: dev, credits: await p.evaluate(() => (document.body.innerText.match(/积分[^0-9]{0,6}(\d+)/) || [])[1]) };
  log('终态', out.end.status, '| 缩放', out.end.zoom, '| 偏离', JSON.stringify(dev), '| 积分', out.end.credits);
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8')); if (mine && !led.ids.includes(mine)) { led.ids = [...new Set([...led.ids, mine])].sort(); writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b78c.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
