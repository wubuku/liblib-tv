// 批次 82 · I：收拾残局 + 诊断「缩放卡在 13%」。
//
// 两件事没做完：
//   ① h 轮 `setZoom(60)` 三次全失败、且**又漏删 2 个节点**（22 nodes）。
//      漏删的机理和 g 轮一样：13% 缩放下 `dy=-30` 的落点算不准，
//      右键菜单打不开。⇒ **删除失败不是偶发，是缩放漂移的必然下游**。
//   ② 缩放为什么是 13%？h 轮新建 3 个节点后仍是 13%（不是 58%），
//      说明 13% 在建节点**之前**就已经在了。
//      疑点：**别的 session 同时在动这块共享画布**。
//      先把「缩放是谁改的」和「现在归谁」分开查：读 viewport transform、
//      全部节点的 canvas 坐标范围、以及自适应是不是被某个节点拉爆的。
//
// 恢复手段按可靠度排序（页面记载 ⌘0/⇧1 可用）：
//   1. 缩放输入框直接写值（h 轮失败）
//   2. **按 ⌘0（适配画布）** —— 产品自己的「把所有节点收进视野」
//   3. 按 ⌘1（缩放至 100%）
//   4. 底部缩放菜单点「适配画布 ⇧1」
import { chromium } from 'playwright';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';
import { writeFileSync } from 'node:fs';
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const LEFTOVER = ['node_32x2zvaysb', 'node_snn0297esd'];

const zoomLabel = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const zoomPct = async () => { const l = await zoomLabel(); return l ? Number((l.match(/(\d+)%/) || [])[1]) : null; };
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));

const dump = () => p.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  const tf = vp ? (vp.style.transform || getComputedStyle(vp).transform) : 'none';
  const m = (tf || '').match(/translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([-\d.]+)\)/);
  const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const s = n.style.transform || '';
    const mm = s.match(/translate\(([-\d.]+)px,\s*([-\d.]+)px\)/);
    return { id: n.getAttribute('data-id'),
      canvas: mm ? [Number(mm[1]), Number(mm[2])] : null,
      label: (n.getAttribute('aria-label') || n.innerText || '').split('\n')[0].slice(0, 18) };
  });
  const withC = nodes.filter((n) => n.canvas);
  const xs = withC.map((n) => n.canvas[0]), ys = withC.map((n) => n.canvas[1]);
  const inp = document.querySelector('input[data-testid="canvas-zoom-percent-input"]');
  return { transform: tf, scale: m ? Number(m[3]) : null, count: nodes.length,
    canvasRange: withC.length ? { x: [Math.min(...xs), Math.max(...xs)], y: [Math.min(...ys), Math.max(...ys)] } : null,
    zoomInput: inp ? { value: inp.value, readOnly: !!inp.readOnly, disabled: !!inp.disabled } : null,
    status: (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0] };
});

try {
  out.before = await dump();
  log('诊断', JSON.stringify(out.before, null, 1));
  out.leftover = (await ids()).filter((x) => LEFTOVER.includes(x));
  log('待删', JSON.stringify(out.leftover));

  // ——— 恢复缩放：⌘0 适配画布 ———
  await p.mouse.click(200, 120); await p.waitForTimeout(700);
  const g0 = await keyGuard(p); log('焦点', g0.where, 'safe=', g0.safe);
  if (g0.safe) {
    await p.keyboard.press('Meta+Digit0'); await p.waitForTimeout(1800);
    out.afterCmd0 = { pct: await zoomPct(), tf: (await dump()).transform };
    log('⌘0 后', JSON.stringify(out.afterCmd0));
    const a = await zoomPct(); await p.waitForTimeout(800); const c = await zoomPct();
    log('连读两次', a, c, a === c ? '静止' : '还在动');
  }
  // ——— 再试 ⌘1 ———
  {
    const g = await keyGuard(p);
    if (g.safe) { await p.keyboard.press('Meta+Digit1'); await p.waitForTimeout(1600);
      const a = await zoomPct(); await p.waitForTimeout(800); const c = await zoomPct();
      out.afterCmd1 = { pct: a, again: c, settled: a === c }; log('⌘1 后', JSON.stringify(out.afterCmd1)); }
  }
  out.after = await dump();
  log('恢复后', JSON.stringify({ pct: await zoomPct(), tf: out.after.transform, status: out.after.status }, null, 1));
} catch (e) { out.error = e.message; console.error('ABORT:', e.message); }
writeFileSync(new URL('./_tmp-b82i.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
