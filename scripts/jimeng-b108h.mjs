// 批次 108 · h 轮：截图 + 事件派发双路，看「背景色」点开之后屏上到底有什么。
//
// g 轮的差分结果是 **新增 0 / 减少 0**（两次快照都是 697 条）⇒
//   要么面板根本没开，要么它开在**我的签名条件之外**（视口外 / 尺寸 <4 / visibility hidden）。
// 本轮不再猜：**先截图**，人眼看一眼；再用 `dispatchEvent` 兜一次。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString() };
out.groupId = 'node_0ctj8mcr3m';
const G = out.groupId;
const save = () => writeFileSync(new URL('./_tmp-b108h.json', import.meta.url), JSON.stringify(out, null, 1));

const status = () => p.evaluate(() => { const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1] }; });
const groupInfo = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  return { sel: n.classList.contains('selected'), members: (n.innerText.match(/(\d+) members/) || [])[1] || null,
    text: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 100) };
}, G);
const bgBtn = () => p.evaluate(() => {
  const bar = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
    .find((e) => { const r = e.getBoundingClientRect(); return r.width > 100 && r.y > 0 && r.y < 400 && getComputedStyle(e).visibility !== 'hidden'; });
  if (!bar) return null;
  const btn = Array.from(bar.querySelectorAll('button,[role=button]')).find((e) => /背景色/.test(e.innerText || ''));
  if (!btn) return null;
  const r = btn.getBoundingClientRect();
  return { w: Math.round(r.width), h: Math.round(r.height), cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
});

let g = await groupInfo();
log('组：', JSON.stringify(g));
if (!g.sel) { log('🔴 没选中'); save(); await b.close(); process.exit(1); }

const btn = await bgBtn();
log('背景色钮：', JSON.stringify(btn));
out.btn = btn;
if (!btn) { save(); await b.close(); process.exit(1); }

// ① 鼠标点击 + 截图
await p.screenshot({ path: '/tmp/b108-h-before.png', clip: { x: 460, y: 150, width: 520, height: 380 } });
await p.mouse.move(btn.cx, btn.cy); await p.waitForTimeout(600);
await p.mouse.click(btn.cx, btn.cy); await p.waitForTimeout(2000);
await p.screenshot({ path: '/tmp/b108-h-after-mouse.png', clip: { x: 460, y: 150, width: 520, height: 380 } });
out.afterMouse = await status();
log('鼠标点击后状态行：', JSON.stringify(out.afterMouse));
log('截图已存 /tmp/b108-h-before.png 与 /tmp/b108-h-after-mouse.png');
save();

// ② 视口外也扫一遍：全页所有「小圆点」（宽=高、圆角 ≥50%、有实心背景色）
out.roundDots = await p.evaluate(() => {
  const out = [];
  for (const e of document.querySelectorAll('body *')) {
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.width > 60) continue;
    if (Math.abs(r.width - r.height) > 1.5) continue;
    const cs = getComputedStyle(e);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    const br = parseFloat(cs.borderRadius) || 0;
    if (br < r.width / 2 - 1) continue;
    if (cs.backgroundColor === 'rgba(0, 0, 0, 0)') continue;
    out.push({ tag: e.tagName, tid: e.getAttribute('data-testid'), a: e.getAttribute('aria-label'),
      t: (e.innerText || '').trim().slice(0, 8), w: Math.round(r.width),
      x: Math.round(r.x), y: Math.round(r.y), bg: cs.backgroundColor, br: cs.borderRadius,
      bdr: cs.borderColor, inViewport: r.x >= 0 && r.y >= 0 && r.x + r.width <= innerWidth && r.y + r.height <= innerHeight });
  }
  return { count: out.length, items: out.slice(0, 30) };
});
log('\n圆点扫描（含视口外）：', JSON.stringify(out.roundDots, null, 1));
save();

// ③ 事件派发兜底
if (!out.roundDots.count) {
  log('\n>>> 换事件派发：在按钮上直接派发 pointer/mouse 序列');
  out.dispatched = await p.evaluate(() => {
    const bar = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
      .find((e) => { const r = e.getBoundingClientRect(); return r.width > 100 && r.y > 0 && r.y < 400; });
    if (!bar) return { ok: false, why: 'no-bar' };
    const btn = Array.from(bar.querySelectorAll('button,[role=button]')).find((e) => /背景色/.test(e.innerText || ''));
    if (!btn) return { ok: false, why: 'no-btn' };
    for (const type of ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click']) {
      btn.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
    }
    return { ok: true };
  });
  await p.waitForTimeout(1800);
  await p.screenshot({ path: '/tmp/b108-h-after-dispatch.png', clip: { x: 460, y: 150, width: 520, height: 380 } });
  out.afterDispatch = await status();
  log('派发后状态行：', JSON.stringify(out.afterDispatch), '派发结果：', JSON.stringify(out.dispatched));
  out.roundDots2 = await p.evaluate(() => {
    const o = [];
    for (const e of document.querySelectorAll('body *')) {
      const r = e.getBoundingClientRect();
      if (r.width < 8 || r.width > 60 || Math.abs(r.width - r.height) > 1.5) continue;
      const cs = getComputedStyle(e);
      if (cs.visibility === 'hidden' || cs.backgroundColor === 'rgba(0, 0, 0, 0)') continue;
      if ((parseFloat(cs.borderRadius) || 0) < r.width / 2 - 1) continue;
      o.push({ tag: e.tagName, tid: e.getAttribute('data-testid'), a: e.getAttribute('aria-label'), t: (e.innerText || '').trim().slice(0, 8),
        w: Math.round(r.width), x: Math.round(r.x), y: Math.round(r.y), bg: cs.backgroundColor, bdr: cs.borderColor });
    }
    return { count: o.length, items: o.slice(0, 30) };
  });
  log('派发后圆点扫描：', JSON.stringify(out.roundDots2, null, 1));
}
save();
log('\n已落盘');
await b.close();
