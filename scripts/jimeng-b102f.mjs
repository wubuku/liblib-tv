// 批次 102 · f 轮：退到 40% 档拍「文本文件 → 文本节点」，然后**删节点 + 归位**。
//
// e 轮两处没成，都照实记：
//   ① `.txt` 有没有 `Upload complete` 状态串 ⇒ **判不出来（VOID）**。
//      e 轮的叶子过滤写得太严（排除「子节点里也含 upload」的祖先），
//      结果连**早就在页面上的** `b22-upload.png: Upload complete` 都没抓到
//      ⇒ 读数 `[]` **不能**支持「文本上传不产生状态串」这个结论。宁可记未定。
//   ② 60% 档下 `224×240` 的空位 **`best=null`**（视口内已有 **55 个他人节点**）
//      ⇒ 与批次 101 同一个原因，本页截图只能退到 40% 档。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString(), selfId: 'node_0gg1c9b3tq' };
const SELF = out.selfId;
const SHOT = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const selN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]');
  return e ? e.getAttribute('aria-label') : null; });
const scaleNow = () => p.evaluate(() => { const e = document.querySelector('.react-flow__viewport');
  const m = e && /scale\(([\d.]+)\)/.exec(e.style.transform || ''); return m ? Number(m[1]) : null; });
const zoomLabel = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return e ? e.getAttribute('aria-label') : null; });
const toolAria = () => p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return t ? t.getAttribute('aria-label') : null; });
const setZoom = async (t) => { for (let k = 1; k <= 4; k++) {
  const zl = await zoomLabel(); if (zl && new RegExp(`, ${t}%`).test(zl)) return true;
  await p.click('[data-testid="canvas-zoom-percent"]'); await p.waitForTimeout(1000);
  if (await p.evaluate(() => !!document.querySelector('input[data-testid="canvas-zoom-percent-input"]'))) {
    await p.evaluate((v) => { const i = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set.call(i, String(v));
      i.dispatchEvent(new Event('input', { bubbles: true }));
      i.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      i.dispatchEvent(new Event('change', { bubbles: true })); i.blur(); }, t);
    await p.waitForTimeout(1700);
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
  return false; };
const safeEval = async (fn, arg, tries = 6) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

out.start = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), scale: await scaleNow() };
log('起点：', JSON.stringify(out.start));
out.idsBefore = await allIds();

await setZoom(40);
out.z40 = await (async () => { const a = await scaleNow(); await p.waitForTimeout(900); const b2 = await scaleNow(); return [a, b2, a === b2]; })();
log('40% 档：', JSON.stringify(out.z40), '｜', await zoomLabel());
if (!out.z40[2] || out.z40[0] !== 0.4) { log('🔴 缩放不稳 ⇒ 中止'); await b.close(); process.exit(1); }

out.plan = await safeEval((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'node-null' };
  const se = n.querySelector('[data-testid="text-flow-node-full"]') || n;
  const surf = se.getBoundingClientRect();
  const te = n.querySelector('[data-testid="flow-node-title"]');
  const TITLE = te ? Math.round(surf.y - te.getBoundingClientRect().y) : 0;
  const W = Math.round(surf.width), H = Math.round(surf.height);
  const L = 12, T = 0, R = 12, Bt = 12;
  const others = Array.from(document.querySelectorAll('.react-flow__node')).filter((e) => e !== n && !e.contains(n) && !n.contains(e))
    .map((e) => { const r = e.getBoundingClientRect(); return { aria: e.getAttribute('aria-label'), x0: r.x, y0: r.y, x1: r.x + r.width, y1: r.y + r.height }; });
  const clearAt = (x, y) => { const bx0 = x - L, by0 = y - TITLE - T, bx1 = x + W + R, by1 = y + H + Bt;
    if (bx0 < 195 || by0 < 62 || bx1 > 1276 || by1 > 636) return false;
    return !others.some((o) => o.x0 < bx1 && o.x1 > bx0 && o.y0 < by1 && o.y1 > by0); };
  const cur = { x: Math.round(surf.x), y: Math.round(surf.y) };
  let best = null;
  for (let dy = -220; dy <= 220; dy += 3) for (let dx = -300; dx <= 300; dx += 3) {
    if (!clearAt(cur.x + dx, cur.y + dy)) continue;
    const d = Math.abs(dx) + Math.abs(dy); if (!best || d < best.d) best = { dx, dy, d }; }
  return { W, H, TITLE, cur, best, othersCount: others.length, hereClear: clearAt(cur.x, cur.y) };
}, SELF);
log('尺寸/空位：', JSON.stringify(out.plan));

if (out.plan && !out.plan.__err && out.plan.best) {
  const grab = await safeEval((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const t = n.querySelector('[data-testid="flow-node-title"]'); if (!t) return { __err: 'no-title' };
    const r = t.getBoundingClientRect();
    for (let f = 0.03; f <= 0.97; f += 0.02) { const x = Math.round(r.x + r.width * f), y = Math.round(r.y + r.height / 2);
      const el = document.elementFromPoint(x, y);
      if (!el || el.closest('button') || !el.closest('[data-testid="flow-node-title"]')) continue;
      return { point: [x, y] }; }
    return { __err: 'no-free-point' }; }, SELF);
  if (!grab.__err) {
    await p.mouse.move(grab.point[0], grab.point[1]); await p.waitForTimeout(400);
    await p.mouse.down(); await p.waitForTimeout(280);
    await p.mouse.move(grab.point[0] + Math.round(out.plan.best.dx / 2), grab.point[1] + Math.round(out.plan.best.dy / 2), { steps: 10 });
    await p.waitForTimeout(300);
    await p.mouse.move(grab.point[0] + out.plan.best.dx, grab.point[1] + out.plan.best.dy, { steps: 10 });
    await p.waitForTimeout(450); await p.mouse.up(); await p.waitForTimeout(1300);
    log('已拖动：', JSON.stringify(out.plan.best));
  }
  const pt = await safeEval((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const s = (n.querySelector('[data-testid="text-flow-node-full"]') || n).getBoundingClientRect();
    const x = Math.round(s.x + s.width / 2), y = Math.round(s.y + 24);
    const el = document.elementFromPoint(x, y);
    return { point: [x, y], insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)) }; }, SELF);
  if (pt.insideSelf) { await p.mouse.move(pt.point[0], pt.point[1]); await p.waitForTimeout(300); await p.mouse.click(pt.point[0], pt.point[1]); await p.waitForTimeout(1200); }
}

out.crop = await safeEval((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'node-null' };
  const pick = ['flow-node-title', 'text-flow-node-full', 'text-node-selection-outline', 'text-node-resize-controls'];
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const t of pick) { const e = n.querySelector(`[data-testid="${t}"]`); if (!e) continue;
    const r = e.getBoundingClientRect(); if (r.width === 0 || r.height === 0) continue;
    x0 = Math.min(x0, r.x); y0 = Math.min(y0, r.y); x1 = Math.max(x1, r.x + r.width); y1 = Math.max(y1, r.y + r.height); }
  if (!isFinite(x0)) { const r = n.getBoundingClientRect(); x0 = r.x; y0 = r.y; x1 = r.x + r.width; y1 = r.y + r.height; }
  const L = 12, T = 0, R = 12, Bt = 12;
  const clip = { x: Math.max(0, Math.floor(x0 - L)), y: Math.max(0, Math.floor(y0 - T)), width: 0, height: 0 };
  clip.width = Math.ceil(Math.min(x1 - x0 + L + R, 1280 - clip.x));
  clip.height = Math.ceil(Math.min(y1 - y0 + T + Bt, 720 - clip.y));
  const hits = Array.from(document.querySelectorAll('.react-flow__node')).filter((e) => {
      if (e === n || e.contains(n) || n.contains(e)) return false;
      const r = e.getBoundingClientRect();
      return r.x < clip.x + clip.width && r.x + r.width > clip.x && r.y < clip.y + clip.height && r.y + r.height > clip.y; })
    .map((e) => ({ id: e.getAttribute('data-id'), aria: e.getAttribute('aria-label') }));
  const chrome = Array.from(document.querySelectorAll('.react-flow__node-toolbar,[role=menu],[role=dialog]'))
    .map((e) => { const r = e.getBoundingClientRect(); if (r.width === 0 || r.height === 0) return null;
      if (!(r.x < clip.x + clip.width && r.x + r.width > clip.x && r.y < clip.y + clip.height && r.y + r.height > clip.y)) return null;
      return { cls: (e.className || '').toString().slice(0, 40) }; }).filter(Boolean);
  return { clip, hits, chrome, innerText: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 120) };
}, SELF);
log('裁切：', JSON.stringify(out.crop, null, 1));
out.guardPass = !out.crop.__err && out.crop.hits.length === 0 && out.crop.chrome.length === 0;
log('守卫：', out.guardPass ? '✅' : '🔴');
if (out.guardPass) {
  const buf = await p.screenshot({ type: 'png', clip: out.crop.clip });
  const f = new URL('103-upload-txt-becomes-text-node.png', SHOT);
  writeFileSync(f, buf);
  out.shot = { file: f.pathname, bytes: buf.length, sha256: createHash('sha256').update(buf).digest('hex'), clip: out.crop.clip };
  log('📸 ', JSON.stringify(out.shot));
}

// ---- 归位缩放 ----
for (let k = 0; k < 3; k++) { await setZoom(60);
  const a = await scaleNow(); await p.waitForTimeout(900); const b2 = await scaleNow();
  log(`  归位第 ${k + 1} 次：`, JSON.stringify([a, b2, a === b2]), '｜', await zoomLabel());
  if (a !== null && a === b2 && a === 0.6) break; }

// ---- 删自建节点（护栏） ----
log('\n=== 删除自建节点 ===');
for (let k = 0; k < 2; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(500); }
const cur = await safeEval((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { gone: true };
  const s = (n.querySelector('[data-testid="text-flow-node-full"]') || n).getBoundingClientRect();
  const x = Math.round(s.x + s.width / 2), y = Math.round(s.y + 24);
  const el = document.elementFromPoint(x, y);
  return { selected: n.classList.contains('selected'), point: [x, y], insideSelf: !!(el && el.closest(`.react-flow__node[data-id="${i}"]`)) }; }, SELF);
log('当前：', JSON.stringify(cur));
if (!cur.gone) {
  if (!cur.selected && cur.insideSelf) { await p.mouse.move(cur.point[0], cur.point[1]); await p.waitForTimeout(350);
    await p.mouse.click(cur.point[0], cur.point[1]); await p.waitForTimeout(1100); }
  const rc = await safeEval((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const s = (n.querySelector('[data-testid="text-flow-node-full"]') || n).getBoundingClientRect();
    return [Math.round(s.x + s.width / 2), Math.round(s.y + 24)]; }, SELF);
  await p.mouse.move(rc[0], rc[1]); await p.waitForTimeout(300); await p.mouse.move(rc[0], rc[1]); await p.waitForTimeout(200);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(260); await p.mouse.up({ button: 'right' });
  await p.waitForTimeout(1000);
  const del = await p.evaluate(() => {
    for (const m of document.querySelectorAll('[role=menu]')) { let target = null;
      for (const it of m.querySelectorAll('[role=menuitem]')) if ((it.innerText || '').trim().startsWith('删除')) target = it;
      if (!target) continue;
      const r = target.getBoundingClientRect();
      const x = Math.round(r.x + r.width / 2), y = Math.round(r.y + r.height / 2);
      const el = document.elementFromPoint(x, y);
      return { point: [x, y], txt: (target.innerText || '').trim(),
        disabled: target.getAttribute('aria-disabled') === 'true',
        inside: !!(el && (el === target || target.contains(el))), hitText: el ? (el.textContent || '').trim() : null }; }
    return null; });
  log('删除项：', JSON.stringify(del));
  if (del && !del.disabled && del.inside) {
    await p.mouse.move(del.point[0], del.point[1]); await p.waitForTimeout(400);
    await p.mouse.click(del.point[0], del.point[1]); await p.waitForTimeout(1900);
    out.clicked = true;
  } else { log('  🔴 落点/状态不对 ⇒ 不点'); out.clicked = false; }
}
await p.waitForTimeout(1200);
out.idsAfter = await allIds();
const after = new Set(out.idsAfter);
out.vanished = out.idsBefore.filter((id) => !after.has(id));
out.appeared = out.idsAfter.filter((id) => !out.idsBefore.includes(id));
out.guardOk = out.vanished.length === 1 && out.vanished[0] === SELF;
log('护栏：删前', out.idsBefore.length, '→ 删后', out.idsAfter.length, '｜消失', JSON.stringify(out.vanished), '｜新增', JSON.stringify(out.appeared));
log('  ⇒ 消失的**恰好只有 SELF**？', out.guardOk ? '✅' : '🔴');

if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }
for (let k = 0; k < 2; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
out.end = { nodes: await nodeN(), sel: await selN(), credits: await credits(), zoom: await zoomLabel(), scale: await scaleNow(), tool: await toolAria(), hasSelf: after.has(SELF) };
log('终态：', JSON.stringify(out.end));
out.clean = out.end.sel === '0' && out.end.scale === 0.6 && out.end.tool === '选择工具' && !out.end.hasSelf;
log('收尾干净？', out.clean ? '✅' : '🔴');
writeFileSync(new URL('./_tmp-b102f.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
