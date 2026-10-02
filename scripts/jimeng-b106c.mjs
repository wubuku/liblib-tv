// 批次 106 · c 轮：缩放菜单的 A/B 对照 + 缩放输入框这条「没闭环的路径」。
//
// b 轮读到一条：**抓手态下点缩放钮，菜单没出现**（`menuOpened: false`）。
// 但那条判据是「扫一个含『缩放至200%』且 x<300 y>500 的浮层」——
// 🔴 **判据本身不够硬**：`canvas-zoom-percent-input` 这个输入框**只在菜单打开时出现**
//   （navigate-canvas.md 362-365 行已写明），它才是这页**专属的开关信号**。
//   本轮用**两个信号同时**判：A 浮层扫描、B 输入框存在。
//
// 顺带结掉一条**从没闭环的老账**：截图 74 的 alt 逐字写着
//   「缩放读数变成被橙色高亮标出的输入框、**已键入 65 未按回车，所以画面大小仍是 100%**」
// —— 也就是说**「键入 + 回车」这半步从来没被验证过**，只证了「键入会进输入框」。
// 批次 105 又撞出「缩放菜单里没有 40% 档」，而此前多批都用过 40% ——
// 本轮正好可以一次性问清楚：**40% 到底怎么来的？**
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString() };
const DOCK = '[data-testid="canvas-navigation-dock"]';
const save = () => writeFileSync(new URL('./_tmp-b106c.json', import.meta.url), JSON.stringify(out, null, 1));

const safeEval = async (fn, arg, tries = 8) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

// 菜单开没开：两个独立信号
const menuState = () => p.evaluate(() => {
  const inp = document.querySelector('[data-testid="canvas-zoom-percent-input"]');
  const layer = Array.from(document.querySelectorAll('div,ul,section')).find((x) => {
    const q = x.getBoundingClientRect(); const t = x.innerText || '';
    return q.x < 320 && q.y > 480 && q.width > 140 && q.height > 100 &&
      getComputedStyle(x).visibility !== 'hidden' && /缩放至200%/.test(t); });
  const btn = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return { inputPresent: !!inp, inputBox: inp ? (() => { const q = inp.getBoundingClientRect();
      return { v: inp.value, type: inp.type, tag: inp.tagName, w: Math.round(q.width), h: Math.round(q.height), x: Math.round(q.x), y: Math.round(q.y) }; })() : null,
    layerFound: !!layer, layerText: layer ? layer.innerText.replace(/\s+/g, ' ').trim().slice(0, 160) : null,
    btnText: btn ? btn.innerText.trim() : null, btnAria: btn ? btn.getAttribute('aria-label') : null,
    btnBox: btn ? (() => { const q = btn.getBoundingClientRect(); return { w: Math.round(q.width), h: Math.round(q.height) }; })() : null };
});
const state = () => safeEval((sel) => {
  const d = document.querySelector(sel);
  const g = (t) => { const e = d.querySelector(`[data-testid="${t}"]`); if (!e) return null;
    const q = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), pressed: e.getAttribute('aria-pressed'), x: Math.round(q.x), y: Math.round(q.y), w: Math.round(q.width), h: Math.round(q.height) }; };
  return { tool: g('canvas-pointer-tool-toggle'), mini: g('canvas-display-toggle-minimap'), conn: g('canvas-display-toggle-connections'), zoom: g('canvas-zoom-percent') };
}, DOCK);
const clickBtn = async (btn, label) => { log(`  >>> 点「${label}」(${btn.x},${btn.y})`);
  await p.mouse.move(btn.x + btn.w / 2, btn.y + btn.h / 2); await p.waitForTimeout(450);
  await p.mouse.click(btn.x + btn.w / 2, btn.y + btn.h / 2); await p.waitForTimeout(1400); };

out.start = { state: await state(), menu: await menuState() };
log('起点工具态 =', out.start.state.tool.aria, '｜缩放 aria =', out.start.state.zoom.aria);
log('起点菜单信号 =', JSON.stringify({ inputPresent: out.start.menu.inputPresent, layerFound: out.start.menu.layerFound }));

// ================= A/B：两种工具态下点缩放钮 =================
out.ab = {};
for (const want of ['选择工具', '抓手工具']) {
  let s = await state();
  if (s.tool.aria !== want) {
    log(`\n===== 切到「${want}」=====`);
    await clickBtn(s.tool, '工具切换');
    s = await state();
  }
  log(`\n===== A/B 格：${s.tool.aria} =====`);
  // 保险：先确保菜单是关的
  if ((await menuState()).inputPresent) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
  const before = await menuState();
  await clickBtn(s.zoom, '缩放值按钮');
  const after = await menuState();
  out.ab[s.tool.aria] = { toolAria: s.tool.aria, toolPressed: s.tool.pressed,
    before: { inputPresent: before.inputPresent, layerFound: before.layerFound },
    after: { inputPresent: after.inputPresent, layerFound: after.layerFound, btnText: after.btnText, layerText: after.layerText, inputBox: after.inputBox },
    opened: after.inputPresent || after.layerFound };
  log('  点前信号：', JSON.stringify(out.ab[s.tool.aria].before));
  log('  点后信号：', JSON.stringify(out.ab[s.tool.aria].after));
  log('  菜单打开 =', out.ab[s.tool.aria].opened ? '✅' : '🔴');
  if (out.ab[s.tool.aria].opened) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); }
  save();
}

// ================= 输入框路径：键入 + 回车 =================
log('\n\n===== 缩放输入框路径（选择工具态）=====');
let s = await state();
if (s.tool.aria !== '选择工具') { await clickBtn(s.tool, '工具切换'); s = await state(); }
log('工具态 =', s.tool.aria, '｜缩放 aria =', s.zoom.aria);
await clickBtn(s.zoom, '缩放值按钮');
const m1 = await menuState();
log('菜单打开：', m1.inputPresent, '｜输入框 =', JSON.stringify(m1.inputBox), '｜按钮文字 =', JSON.stringify(m1.btnText));
out.beforeInput = { zoomAria: s.zoom.aria, menu: m1 };
save();

if (m1.inputPresent) {
  // 直接往那个 input 打字（它是真 input，Playwright 可以 fill/type）
  const sel = '[data-testid="canvas-zoom-percent-input"]';
  await p.click(sel).catch(() => {});
  await p.waitForTimeout(400);
  await p.fill(sel, '').catch((e) => log('  fill 失败：', e.message));
  await p.type(sel, '40', { delay: 220 });
  await p.waitForTimeout(500);
  const typed = await menuState();
  log('\n  键入 40（未回车）后：', JSON.stringify({ inputBox: typed.inputBox, btnText: typed.btnText, zoomBtnAria: (await state()).zoom.aria }));
  out.typedNoEnter = { inputBox: typed.inputBox, zoomAria: (await state()).zoom.aria };
  save();
  await p.keyboard.press('Enter');
  await p.waitForTimeout(1800);
  const ent = await menuState();
  const st2 = await state();
  log('  按回车后：', JSON.stringify({ inputPresent: ent.inputPresent, layerFound: ent.layerFound, zoomAria: st2.zoom.aria }));
  out.afterEnter = { menu: { inputPresent: ent.inputPresent, layerFound: ent.layerFound }, zoomAria: st2.zoom.aria };
  // 连读两次确认静止
  await p.waitForTimeout(1300);
  out.afterEnter.zoomAria2 = (await state()).zoom.aria;
  log('  再读一次缩放 aria：', out.afterEnter.zoomAria2, out.afterEnter.zoomAria === out.afterEnter.zoomAria2 ? '（两次相同）' : '（⚠️ 还在动）');
  save();
}

out.endState = await state();
log('\n终点：', JSON.stringify({ tool: out.endState.tool.aria, mini: out.endState.mini.pressed, conn: out.endState.conn.pressed, zoom: out.endState.zoom.aria }));
save();
log('已落盘');
await b.close();
