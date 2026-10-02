// 批次 78 · E：修三处后重拍。
// ① 选择器：`.video-node-empty` 这个 **class 不存在**，真正能用的是 `data-testid=video-node-empty`
//    （b78c 因此 found:false；b78 那轮的采样器用的是 testid 却把值记进了「class」列 ⇒ 假 class）。
// ② 断言不许空转：b78c 的 `wantCount:0` 让「目标元素都在 clip 内」**空过**，必须 wantCount>=1 才算通过。
// ③ 裁切还要挡**非节点 UI**：b78b/b78c 的守卫只查 `.react-flow__node` 矩形，
//    于是顶部工具条的边角被裁进了图里（画面最上沿那条圆角残影 + 倒三角）。
//    这里加一条更一般的守卫：clip 内、且在节点矩形之外的采样点，
//    命中的元素必须属于 `.react-flow` / `.react-flow__pane` / body 这种**纯背景**，否则换位置重试。
// 只读观察：不点那个占位图标，只读它的 cursor / elementFromPoint 链。
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
  const nowIds = await ids();
  const created = nowIds.filter((x) => !pre.includes(x));
  if (created.length !== 1) throw new Error('新建异常：' + JSON.stringify(created));
  mine = created[0];                       // ← 先落定 mine，后面炸了也收得掉
  log('新建', mine);

  // —— 选落点：clip 顶边必须 ≥ 80（避开顶部工具条），且离他人节点 ≥ 12
  const plan = await p.evaluate((v) => {
    const others = Array.from(document.querySelectorAll('.react-flow__node'))
      .filter((n) => n.getAttribute('data-id') !== v).map((n) => n.getBoundingClientRect());
    const r = document.querySelector(`.react-flow__node[data-id="${v}"]`).getBoundingClientRect();
    for (let y = 260; y < 620; y += 20) for (let x = 300; x < 1200; x += 20) {
      const box = { x: x - r.width / 2, y: y - r.height / 2, right: x + r.width / 2, bottom: y + r.height / 2 };
      if (box.x - 16 < 8 || box.y - 16 < 80 || box.right + 16 > innerWidth - 8 || box.bottom + 16 > innerHeight - 8) continue;
      if (others.some((o) => box.x < o.right + 12 && box.right + 12 > o.x && box.y < o.bottom + 12 && box.bottom + 12 > o.y)) continue;
      return { x, y, top: Math.round(box.y - 16) };
    } return null;
  }, mine);
  if (!plan) throw new Error('找不到满足「clip 顶边≥80 且远离他人」的落点');
  const grip = await p.evaluate((v) => {
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect();
    const cx = Math.round(r.x + r.width * 0.22), cy = Math.round(r.y + r.height * 0.5);
    const hit = document.elementFromPoint(cx, cy);
    return { cx, cy, ok: !!hit && n.contains(hit), hit: hit ? `${hit.tagName}.${(hit.getAttribute('class') || '').slice(0, 40)}` : 'null' };
  }, mine);
  if (!grip.ok) throw new Error('抓手落点不属于本节点：' + JSON.stringify(grip));
  await p.mouse.move(grip.cx, grip.cy); await p.mouse.down();
  for (let i = 1; i <= 10; i++) { await p.mouse.move(Math.round(grip.cx + (plan.x - grip.cx) * i / 10), Math.round(grip.cy + (plan.y - grip.cy) * i / 10)); await p.waitForTimeout(70); }
  await p.mouse.up(); await p.waitForTimeout(1200);
  out.plan = plan; log('落点', JSON.stringify(plan));

  // —— 前置条件断言：不成立则下面所有读数作废(VOID)
  const pre1 = await p.evaluate((v) => {
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
    return { selected: /(^|\s)selected(\s|$)/.test(n.className), cls: n.className, group: !!document.querySelector('.react-flow__node-group') };
  }, mine);
  log('前置', JSON.stringify(pre1));
  if (!pre1.selected) throw new Error('拖完未保持选中 ⇒ 读数作废(VOID)');
  if (pre1.group) throw new Error('画布存在组节点 ⇒ 读数污染(VOID)');

  // —— 探针：testid 版；并区分「画出来的文字」与「只有 aria-label 的文字」
  const probe = await p.evaluate((v) => {
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`);
    const zoom = (() => { const t = getComputedStyle(document.querySelector('.react-flow__viewport')).transform;
      const m = /matrix\(([-\d.]+)/.exec(t); return m ? +m[1] : null; })();
    const e = n.querySelector('[data-testid=video-node-empty]');
    const surface = n.querySelector('[data-testid=video-flow-node-surface]');
    const r = (e || n).getBoundingClientRect();
    const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    const hit = document.elementFromPoint(cx, cy);
    const chain = []; for (let x = hit; x && x !== document.body; x = x.parentElement) {
      const c = getComputedStyle(x);
      chain.push(`${x.tagName}${x.getAttribute('data-testid') ? '#' + x.getAttribute('data-testid') : ''}.${(x.getAttribute('class') || '').slice(0, 30)}|cursor=${c.cursor}|pe=${c.pointerEvents}`);
      if (chain.length > 6) break;
    }
    // 画出来的文字 vs 只有 aria-label 的文字：全节点扫一遍
    const painted = [], ariaOnly = [];
    for (const el of n.querySelectorAll('*')) {
      const own = Array.from(el.childNodes).filter((c) => c.nodeType === 3 && (c.textContent || '').trim()).map((c) => c.textContent.trim());
      if (!own.length) continue;
      const rg = document.createRange(); rg.selectNodeContents(el);
      const w = Array.from(rg.getClientRects()).reduce((s, x) => s + x.width, 0);
      const rec = { txt: own.join(' ').slice(0, 40), paintedW: +w.toFixed(2), color: getComputedStyle(el).color };
      (w > 0.5 ? painted : ariaOnly).push(rec);
    }
    const srOnlyText = Array.from(n.querySelectorAll('.sr-only')).map((x) => (x.textContent || '').trim().slice(0, 70));
    const svgIcon = e ? e.querySelector('svg') : null;
    return {
      zoom,
      surfaceBox: surface ? `${(surface.getBoundingClientRect().width / zoom).toFixed(1)}x${(surface.getBoundingClientRect().height / zoom).toFixed(1)} canvas` : null,
      emptyFound: !!e,
      emptyTag: e ? e.tagName : null,
      emptyClass: e ? (e.getAttribute('class') || '') : null,
      emptyAria: e ? (e.getAttribute('aria-label') || '') : null,
      emptyInnerText: e ? JSON.stringify(e.innerText) : null,
      emptyInnerHTML: e ? e.innerHTML.slice(0, 220) : null,
      emptyBox: e ? `${(r.width / zoom).toFixed(1)}x${(r.height / zoom).toFixed(1)} canvas` : null,
      svgIconBox: svgIcon ? `${(svgIcon.getBoundingClientRect().width / zoom).toFixed(1)}x${(svgIcon.getBoundingClientRect().height / zoom).toFixed(1)} canvas` : null,
      iconChain: chain,
      paintedText: painted, ariaOnlyText: ariaOnly, srOnlyText,
    };
  }, mine);
  out.probe = probe;
  log('探针', JSON.stringify(probe, null, 1));

  // —— 裁切守卫 v2：既挡他人节点矩形，也挡非节点 UI
  const clipInfo = await p.evaluate((v) => {
    const n = document.querySelector(`.react-flow__node[data-id="${v}"]`); const r = n.getBoundingClientRect();
    const want = ['[data-testid=flow-node-title]', '[data-testid=flow-node-target-connection-menu-button]',
      '[data-testid=flow-node-source-connection-menu-button]', '[data-testid=video-node-empty]']
      .map((s) => ({ s, el: n.querySelector(s) })).filter((o) => o.el);
    let pad = 16;
    for (const o of want) { const w = o.el.getBoundingClientRect();
      pad = Math.max(pad, Math.round(r.x - w.x), Math.round(w.right - r.right), Math.round(r.y - w.y), Math.round(w.bottom - r.bottom)); }
    pad = Math.min(pad, 40);
    const L = Math.max(0, Math.round(r.x - pad)), T = Math.max(0, Math.round(r.y - pad));
    const R = Math.min(innerWidth, Math.round(r.right + pad)), B = Math.min(innerHeight, Math.round(r.bottom + pad));
    const intr = Array.from(document.querySelectorAll('.react-flow__node')).filter((o) => o.getAttribute('data-id') !== v)
      .map((o) => ({ id: o.getAttribute('data-id'), r: o.getBoundingClientRect() }))
      .filter(({ r: o }) => o.x < R && o.right > L && o.y < B && o.bottom > T).map(({ id }) => id);
    // clip 内、节点矩形之外的采样点：命中的必须是纯背景层
    const chrome = [];
    for (let y = T + 3; y < B; y += 7) for (let x = L + 3; x < R; x += 7) {
      if (x > r.x - 1 && x < r.right + 1 && y > r.y - 1 && y < r.bottom + 1) continue;
      const h = document.elementFromPoint(x, y); if (!h) continue;
      const okBg = h === document.body || h.classList.contains('react-flow') || h.classList.contains('react-flow__pane')
        || h.classList.contains('react-flow__renderer') || h.classList.contains('react-flow__viewport');
      if (!okBg) { const t = `${h.tagName}${(h.getAttribute('aria-label') || h.innerText || '').trim().split('\n')[0].slice(0, 22)}`.trim();
        if (!chrome.some((c) => c.t === t)) chrome.push({ t, at: `${x},${y}` }); }
    }
    const outside = want.filter((o) => { const w = o.el.getBoundingClientRect(); return w.x < L || w.right > R || w.y < T || w.bottom > B; }).map((o) => o.s);
    return { pad, clip: { x: L, y: T, width: R - L, height: B - T }, intruding: intr, chrome, outside, wantCount: want.length };
  }, mine);
  out.clip = clipInfo; log('clip', JSON.stringify(clipInfo));
  if (clipInfo.intruding.length) throw new Error('clip 内有他人节点：' + clipInfo.intruding.join(','));
  if (clipInfo.chrome.length) throw new Error('clip 内有非节点 UI：' + clipInfo.chrome.map((c) => `${c.t}@${c.at}`).join(' / '));
  if (clipInfo.wantCount < 1) throw new Error('wantCount=0 ⇒ 目标元素断言空转，不算通过');
  if (clipInfo.outside.length) throw new Error('以下元素没被裁进来：' + clipInfo.outside.join(','));
  await p.screenshot({ path: new URL('78-empty-video-node-card.png', SHOTS).pathname, clip: clipInfo.clip });
  log('📷 78-empty-video-node-card.png（pad=' + clipInfo.pad + '，目标元素 ' + clipInfo.wantCount + ' 个全在 clip 内，他人节点 0，非节点 UI 0）');
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
  out.end = { status: await status(), zoom: await zoomOf(), deviation: dev, credits: await p.evaluate(() => (document.body.innerText.match(/积分[^0-9]{0,6}(\d+)/) || [])[1] || null) };
  log('终态', out.end.status, '| 缩放', out.end.zoom, '| 偏离', JSON.stringify(dev), '| 积分', out.end.credits);
  try { const led = JSON.parse(readFileSync(LEDGER, 'utf8')); if (mine && !led.ids.includes(mine)) { led.ids = [...new Set([...led.ids, mine])].sort(); writeFileSync(LEDGER, JSON.stringify(led, null, 1)); } } catch {}
  writeFileSync(new URL('./_tmp-b78e.json', import.meta.url), JSON.stringify(out, null, 1));
  await b.close();
}
