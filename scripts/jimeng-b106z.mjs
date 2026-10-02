// 批次 106 · z 轮：把「抓手态下 dock 的其它按钮还能不能点」**测到菜单项这一层**，
// 然后归位。
//
// c 轮已经关掉两件事：
//   🔑 **40% 之谜**：缩放菜单里**没有 40% 档**，但
//     `canvas-zoom-percent-input` 是 `INPUT type=text`、值就是当前百分比、
//     **`48×28@124,672`（与按钮同一矩形）**；
//     键入 `40` **不回车** ⇒ input 值变 40 而 `canvas-zoom-percent` 的 aria
//     **仍是 `Zoom options, 60%`**（画面不变，与截图 74 的 alt 逐字吻合）；
//     按 **Enter** ⇒ 输入框消失（菜单关闭）、aria 变成 **`Zoom options, 40%`**，
//     连读两次 40/40。
//     ⇒ **此前多批用到的 40% 档，走的就是这条输入框路径。**
//   🔴 b 轮的「抓手态下菜单打不开」是**判据错**：`layerFound` 恒为 `false`（那条浮层扫描
//     从来就没扫到过东西），真信号是 `inputPresent`。A/B 两格实测**完全一致**：
//     选择工具 ✅ / 抓手工具 ✅。
//
// 本轮补上最后一层：**抓手态下，缩放菜单里的「放大视图 / 缩小视图」项能不能点？**
//   —— 原问题问的是「dock 的其它按钮」，而按钮点开后还有一层菜单，一层不测不算关。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString() };
const DOCK = '[data-testid="canvas-navigation-dock"]';
const save = () => writeFileSync(new URL('./_tmp-b106z.json', import.meta.url), JSON.stringify(out, null, 1));

const safeEval = async (fn, arg, tries = 8) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };
const state = () => safeEval((sel) => {
  const d = document.querySelector(sel);
  const g = (t) => { const e = d.querySelector(`[data-testid="${t}"]`); if (!e) return null;
    const q = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), pressed: e.getAttribute('aria-pressed'),
      x: Math.round(q.x), y: Math.round(q.y), w: Math.round(q.width), h: Math.round(q.height) }; };
  const inp = document.querySelector('[data-testid="canvas-zoom-percent-input"]');
  const t = document.body.innerText;
  return { tool: g('canvas-pointer-tool-toggle'), mini: g('canvas-display-toggle-minimap'),
    conn: g('canvas-display-toggle-connections'), zoom: g('canvas-zoom-percent'),
    inputPresent: !!inp, inputValue: inp ? inp.value : null,
    status: (t.match(/(\d+) nodes?/) || [])[1] + ' nodes, ' + (t.match(/(\d+) selected/) || [])[1] + ' selected' };
}, DOCK);
const clickBtn = async (btn, label) => { log(`  >>> 点「${label}」(${btn.x},${btn.y})`);
  await p.mouse.move(btn.x + btn.w / 2, btn.y + btn.h / 2); await p.waitForTimeout(450);
  await p.mouse.click(btn.x + btn.w / 2, btn.y + btn.h / 2); await p.waitForTimeout(1400); };
// 在菜单里按**逐字**找一项并点它
const clickMenuItem = async (label) => {
  const hit = await p.evaluate((lb) => {
    const e = Array.from(document.querySelectorAll('button,[role=menuitem],[role=option],li,div'))
      .filter((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === lb)
      .map((x) => ({ x, q: x.getBoundingClientRect(), v: getComputedStyle(x).visibility }))
      .filter((y) => y.q.width > 10 && y.q.height > 8 && y.v !== 'hidden')
      .sort((a, b2) => a.q.width * a.q.height - b2.q.width * b2.q.height)[0];
    if (!e) return null;
    return { x: e.q.x + e.q.width / 2, y: e.q.y + e.q.height / 2, w: Math.round(e.q.width), h: Math.round(e.q.height) };
  }, label);
  if (!hit) { log(`  🔴 菜单里找不到「${label}」`); return null; }
  log(`  >>> 点菜单项「${label}」(${Math.round(hit.x)},${Math.round(hit.y)} ${hit.w}×${hit.h})`);
  await p.mouse.move(hit.x, hit.y); await p.waitForTimeout(350);
  await p.mouse.click(hit.x, hit.y); await p.waitForTimeout(1500);
  return hit;
};

out.start = await state();
log('起点：', JSON.stringify({ tool: out.start.tool.aria, zoom: out.start.zoom.aria, inputPresent: out.start.inputPresent }));

// ================= 抓手态下测菜单项 =================
let s = out.start;
if (s.tool.aria !== '抓手工具') { await clickBtn(s.tool, '工具切换'); s = await state(); }
log('\n工具态 =', s.tool.aria, '｜缩放 =', s.zoom.aria);
if (s.inputPresent) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }

out.menu = {};
for (const [key, label] of [['zoomIn', '放大视图'], ['zoomOut', '缩小视图']]) {
  const cur = await state();
  if (cur.tool.aria !== '抓手工具') { log('🔴 工具态串扰，中止'); break; }
  if (!cur.inputPresent) { await clickBtn(cur.zoom, '缩放值按钮'); }
  const beforeAria = (await state()).zoom.aria;
  const hit = await clickMenuItem(label);
  const after = await state();
  out.menu[key] = { label, hit, toolAria: after.tool.aria, zoomBefore: beforeAria, zoomAfter: after.zoom.aria,
    inputPresentAfter: after.inputPresent, resp: beforeAria !== after.zoom.aria };
  log('   ', beforeAria, '→', after.zoom.aria, '｜工具态', after.tool.aria, '｜响应', out.menu[key].resp ? '✅' : '🔴');
  // 菜单多半会自己关掉；没关就 Esc
  if (after.inputPresent) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
  save();
}

// ================= 归位 =================
log('\n===== 归位 =====');
s = await state();
if (s.tool.aria !== '选择工具') { await clickBtn(s.tool, '工具切换'); }
s = await state();
log('工具态 =', s.tool.aria);
if (s.mini.pressed === 'true') { await clickBtn(s.mini, '小地图'); }
s = await state();
if (s.conn.pressed === 'false') { await clickBtn(s.conn, '显示连线'); }
s = await state();

// 缩放：走刚验过的输入框路径回 60%
if (!/60%/.test(s.zoom.aria)) {
  log('\n用输入框路径把缩放设回 60%（当前', s.zoom.aria, '）');
  if (!s.inputPresent) { await clickBtn(s.zoom, '缩放值按钮'); }
  const sel = '[data-testid="canvas-zoom-percent-input"]';
  await p.click(sel).catch(() => {});
  await p.waitForTimeout(350);
  await p.fill(sel, '').catch(() => {});
  await p.type(sel, '60', { delay: 200 });
  await p.waitForTimeout(400);
  await p.keyboard.press('Enter');
  await p.waitForTimeout(1800);
  out.restoreZoom = (await state()).zoom.aria;
  log('  回读缩放 aria =', out.restoreZoom);
}

out.end = await state();
log('\n终态：', JSON.stringify({ tool: out.end.tool.aria, toolPressed: out.end.tool.pressed,
  mini: out.end.mini.pressed, conn: out.end.conn.pressed, zoom: out.end.zoom.aria,
  inputPresent: out.end.inputPresent, status: out.end.status }));
out.clean = out.end.tool.aria === '选择工具' && out.end.mini.pressed === 'false'
  && out.end.conn.pressed === 'true' && /60%/.test(out.end.zoom.aria)
  && out.end.status.indexOf('0 selected') >= 0;
log('clean =', out.clean);
save();
await b.close();
