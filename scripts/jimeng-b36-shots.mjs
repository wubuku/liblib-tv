// 批次 36 截图：「从画布选择」全屏拾取模式（只开不选）
import { chromium } from 'playwright';
import { writeFileSync, readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { makePanner } from './jimeng-pan.mjs';
const DIR = '/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/user-manual/jimeng-canvas/screenshots';
const results = []; const MINE = [];
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const ctx = b.contexts()[0];
const page = ctx.pages().find((p) => p.url().includes('jimeng.jianying.com'));
const cdp = await ctx.newCDPSession(page);
await cdp.send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 720, deviceScaleFactor: 2, mobile: false });
await cdp.send('Emulation.setTimezoneOverride', { timezoneId: 'Asia/Shanghai' });
await page.waitForTimeout(700);
const vp = await page.evaluate(() => ({ w: innerWidth, h: innerHeight }));
if (vp.w !== 1280 || vp.h !== 720) { console.error('VIEWPORT POLLUTED', JSON.stringify(vp)); process.exit(2); }
for (let i = 0; i < 3; i++) { await page.keyboard.press('Escape'); await page.waitForTimeout(400); }
const esc = async (n) => { for (let i = 0; i < n; i++) { await page.keyboard.press('Escape'); await page.waitForTimeout(420); } };
const T = () => page.evaluate(() => { const v = document.querySelector('.react-flow__viewport'); return v ? v.style.transform : '?'; });
const T0 = await T(); console.log('起点 =', T0);
const allNodes = () => page.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => ({ id: n.getAttribute('data-id') || '', type: Array.from(n.classList).filter((c) => c.startsWith('react-flow__node-')).join(','), title: (n.innerText || '').split('\n').pop().trim().slice(0, 20) })));
const OTHERS = new Set((await allNodes()).map((n) => n.id));
const railBtn = (n) => page.evaluate((nm) => { const e = Array.from(document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button')).find((x) => (x.getAttribute('aria-label') || '') === nm); if (!e) return null; const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }, n);

// 缩放钉死 60%
{ const sc = (String(T0).match(/scale\(([\d.]+)\)/) || [])[1];
  if (sc && Math.abs(parseFloat(sc) - 0.6) > 0.005) {
    const btn = await page.evaluate(() => { const e = document.querySelector('button[aria-label^="Zoom options"]'); const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
    await page.mouse.click(btn.cx, btn.cy); await page.waitForTimeout(1200);
    const box = await page.evaluate(() => { const e = document.querySelector('input[data-testid="canvas-zoom-percent-input"]'); if (!e) return null; const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
    if (box) { await page.mouse.click(box.cx, box.cy); await page.waitForTimeout(450); await page.keyboard.press('Meta+A'); await page.waitForTimeout(220); await page.keyboard.type('60'); await page.waitForTimeout(320); await page.keyboard.press('Enter'); await page.waitForTimeout(1500);
      for (let i = 0; i < 2; i++) { await page.keyboard.press('Escape'); await page.waitForTimeout(380); } console.log('缩放归位 →', await T()); }
    else { console.error('ABORT: 无 zoom 输入框'); process.exit(3); }
  } else console.log('缩放已 60%'); }

// pan 走他人节点
const panner = await makePanner(page);
if (panner.why) { console.error(panner.why); process.exit(2); }
for (let i = 0; i < 6; i++) {
  await panner.move(0, -200);
  const vis = await page.evaluate((ids) => Array.from(document.querySelectorAll('.react-flow__node')).filter((n) => { const r = n.getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight && ids.includes(n.getAttribute('data-id')); }).map((n) => n.getAttribute('data-id')), Array.from(OTHERS));
  if (!vis.length) { console.log(`pan ${i + 1} 轮后他人节点已全部移出视口`); break; }
}
console.log('视口内他人节点 =', await page.evaluate((ids) => Array.from(document.querySelectorAll('.react-flow__node')).filter((n) => { const r = n.getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight && ids.includes(n.getAttribute('data-id')); }).map((n) => n.getAttribute('data-id')), Array.from(OTHERS)));

// 新建宿主（空图片节点）
async function makeNode(kind, cls) {
  await esc(3); const rb = await railBtn(kind); if (!rb) return null;
  const pre = await allNodes();
  await page.mouse.click(rb.cx, rb.cy); await page.waitForTimeout(2400);
  const post = await allNodes();
  const c = post.filter((x) => !pre.some((y) => y.id === x.id) && x.type === cls);
  if (!c.length) return null; MINE.push(c[0].id); return c[0].id;
}
async function selectById(id) {
  const box = await page.evaluate((vid) => { const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return null; n.scrollIntoView({ block: 'center' }); const r = n.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + 26) }; }, id);
  if (!box) return false; await page.mouse.click(box.x, box.y); await page.waitForTimeout(1800);
  let ok = await page.evaluate((vid) => { const s = document.querySelector('.react-flow__node.selected'); return !!s && s.getAttribute('data-id') === vid; }, id);
  if (!ok) { await page.evaluate((vid) => { const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return; const r = n.getBoundingClientRect(); for (const t of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) n.dispatchEvent(new MouseEvent(t, { bubbles: true, cancelable: true, clientX: Math.round(r.x + r.width / 2), clientY: Math.round(r.y + 26) })); }, id);
    await page.waitForTimeout(1800); ok = await page.evaluate((vid) => { const s = document.querySelector('.react-flow__node.selected'); return !!s && s.getAttribute('data-id') === vid; }, id); }
  return ok;
}
async function highlight(sel, pad = 4) { return page.evaluate(({ s, p }) => { document.querySelectorAll('.__b36hl').forEach((e) => e.remove()); const out = [];
  Array.from(document.querySelectorAll(s)).forEach((n) => { const r = n.getBoundingClientRect(); const d = document.createElement('div'); d.className = '__b36hl';
    d.style.cssText = `position:fixed;left:${r.x - p}px;top:${r.y - p}px;width:${r.width + p * 2}px;height:${r.height + p * 2}px;border:2px solid #ff7a00;pointer-events:none;z-index:2147483647;border-radius:6px;`;
    document.body.appendChild(d); out.push({ x: r.x, y: r.y, w: r.width, h: r.height, inView: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight }); });
  return out; }, { s: sel, p: pad }); }
const unhl = () => page.evaluate(() => document.querySelectorAll('.__b36hl').forEach((e) => e.remove()));
async function shoot(name, clip, note) { await page.screenshot({ path: `${DIR}/${name}`, clip }); await unhl();
  const sha = createHash('sha256').update(readFileSync(`${DIR}/${name}`)).digest('hex'); results.push({ name, sha, note }); console.log('📸', name, sha.slice(0, 12), note); }

const host = await makeNode('图片', 'react-flow__node-image');
console.log('宿主 =', host);
if (!host) { console.error('ABORT'); process.exit(4); }
console.log('宿主选中 =', await selectById(host));
const addBtn = await page.evaluate(() => { const tb = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).filter((e) => e.getBoundingClientRect().width > 1 && e.getBoundingClientRect().height > 1)[0]; const e = tb && Array.from(tb.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '添加参考'); if (!e) return null; const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
await page.mouse.click(addBtn.cx, addBtn.cy); await page.waitForTimeout(1500);
const pick = await page.evaluate(() => { const m = document.querySelector('[role="menu"][aria-label="添加参考"]'); if (!m) return null; const it = Array.from(m.querySelectorAll('[role="menuitem"]')).find((x) => /从画布选择/.test(x.innerText || '')); if (!it) return null; const r = it.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
await page.mouse.click(pick.cx, pick.cy); await page.waitForTimeout(2200);
const st = await page.evaluate(() => {
  const R = (e) => { const r = e.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height), inView: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight }; };
  const chip = document.querySelector('[data-testid="generation-source-picker-chip"]');
  const close = document.querySelector('[data-testid="generation-source-picker-close"]');
  const mask = document.querySelector('[data-testid="canvas-source-picker-canvas-mask"]');
  const frame = document.querySelector('[data-testid="canvas-source-picker-canvas-frame"]');
  const f = document.querySelector('form[data-testid="generation-form"]');
  const hint = (() => { if (!f) return null; const el = Array.from(f.querySelectorAll('*')).filter((e) => /Select a supported/.test(e.innerText || '')).pop(); if (!el) return null; const r = el.getBoundingClientRect(); return { x: r.x, y: r.y, w: r.width, h: r.height, inView: r.x >= 0 && r.y >= 0 && r.right <= innerWidth && r.bottom <= innerHeight, text: (el.innerText || '').replace(/\s+/g, ' ').trim() }; })();
  return { chip: chip ? { ...R(chip), text: (chip.innerText || '').trim() } : null, close: close ? { ...R(close), aria: close.getAttribute('aria-label') } : null,
    mask: mask ? R(mask) : null, frame: frame ? R(frame) : null, hint,
    formAria: f ? f.getAttribute('aria-label') : null, formBox: f ? R(f) : null,
    railBtns: document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button').length,
    status: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0] };
});
console.log('选择模式状态 =', JSON.stringify(st, null, 1));
if (st.chip && st.hint && st.chip.inView && st.hint.inView) {
  const rects = await highlight('[data-testid="generation-source-picker-chip"], [data-testid="generation-source-picker-close"]');
  const h = st.hint; rects.push({ x: h.x, y: h.y, w: h.w, h: h.h, inView: h.inView });
  console.log('高亮 =', JSON.stringify(rects));
  if (rects.every((r) => r.inView)) {
    // ⚠️ 英文提示元素是 1×1 的隐藏辅助文案，**不在画面上**，不能拿它撑 clip
    const x = Math.max(0, Math.min(...rects.slice(0, 2).map((r) => r.x)) - 18);
    const y = Math.max(0, Math.min(...rects.slice(0, 2).map((r) => r.y)) - 18);
    const clip = { x: Math.round(x), y: Math.round(y), width: Math.round(Math.max(...rects.slice(0, 2).map((r) => r.x + r.w)) - x + 18), height: Math.round(Math.max(...rects.slice(0, 2).map((r) => r.y + r.h)) - y + 18) };
    console.log('clip =', JSON.stringify(clip));
    await shoot('97-from-canvas-picker.png', clip, '「从画布选择」拾取模式的状态 chip');
  }
}
// 收尾：取消选择
await page.evaluate(() => { const b2 = document.querySelector('[data-testid="generation-source-picker-close"]'); if (b2) b2.click(); });
await page.waitForTimeout(1600);
for (let i = 0; i < 3; i++) { await page.keyboard.press('Escape'); await page.waitForTimeout(450); }
writeFileSync('/tmp/b36-mine.txt', MINE.join('\n'));
writeFileSync('/tmp/b36-shots.json', JSON.stringify(results, null, 1));
console.log('MINE =', JSON.stringify(MINE));
console.log('收尾 =', JSON.stringify(await page.evaluate(() => ({ nodes: document.querySelectorAll('.react-flow__node').length, groups: document.querySelectorAll('.react-flow__node-group').length, mask: document.querySelectorAll('[data-testid="canvas-source-picker-canvas-mask"]').length, selected: document.querySelectorAll('.react-flow__node.selected').length, hl: document.querySelectorAll('.__b36hl').length, status: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0], credits: (document.body.innerText.match(/(\d[\d,]*)\s*基础会员/) || [])[1] || null }))));
await b.close();
