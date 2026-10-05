// 批次 170 u 轮：决定性实验 —— 子菜单改内联的**触发条件到底是什么**。
//
// 冲突（必须解释，不能挑一个顺眼的记）：
//   r 轮（宽度从 1280 一路递减到 400）：**700 → 飞出**，**640 → 流内**
//   t 轮（宽度从 648 一路递减到 640）：**640 → 飞出**（8 档全是飞出）
//   ⇒ 同一个视口宽度（640）两轮读出两种态 ⇒ **它不是视口宽度的纯函数**。
//
// 假设 H_pos：条件是「菜单右侧还放不放得下 212 px 的飞出块」，即
//              `锚点x + 菜单宽 + 子菜单宽 + 余量 ≤ 视口宽`。
// 实验：把视口宽**钉死在 700**，只扫锚点 x，看切换点落在哪。
// 预测（若 H_pos 成立）：切换应发生在 x ≈ 700 − 240 − 212 = 248 附近，与 r 轮的 700/640 一致。
import { openCanvas, readers } from './jimeng-b135-lib.mjs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const { b, p: shared } = await openCanvas();
const p = shared;
const R = readers(p);

const tab = await b.contexts()[0].newPage();
await tab.goto(shared.url(), { waitUntil: 'domcontentloaded' });
await tab.waitForSelector('.react-flow__node', { timeout: 60000 });
await tab.waitForTimeout(3500);

const pin = async (w, h = 720) => {
  await tab.context().newCDPSession(tab).then(async (s) => {
    await s.send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 2, mobile: false });
  });
  await tab.waitForTimeout(1200);
};

const probeAt = async (x) => {
  await tab.keyboard.press('Escape');
  await tab.waitForTimeout(220);
  const y = Math.round(720 * 0.25);
  const ok = await tab.evaluate(([px, py]) => {
    const e = document.elementFromPoint(px, py);
    return !!(e && e.closest('.react-flow__pane'));
  }, [x, y]);
  await tab.mouse.click(x, y, { button: 'right' });
  await tab.waitForTimeout(750);
  return tab.evaluate((pointOk) => {
    const e = document.querySelector('[data-testid="canvas-context-menu"]');
    if (!e) return { 菜单没开: true, 点位合法: pointOk };
    const mr = e.getBoundingClientRect();
    const trig = e.firstElementChild && e.firstElementChild.firstElementChild;
    let pos = null;
    if (trig) for (const c of trig.querySelectorAll('div')) {
      if (c.querySelectorAll('[role=menuitem]').length >= 5) { pos = getComputedStyle(c).position; break; }
    }
    return {
      菜单: [Math.round(mr.x), Math.round(mr.y), Math.round(mr.width), Math.round(mr.height)],
      视口宽: innerWidth,
      子菜单pos: pos,
      // 飞出块若放右边要占到的最右位置
      飞出右边界: Math.round(mr.x + mr.width) + 212 + 12,
    };
  }, ok);
};

const rows = [];
for (const W of [700, 640]) {
  console.log(`\n════ 视口宽钉死 ${W} ════`);
  await pin(W);
  for (const x of [20, 120, 200, 240, 260, 300, 360, 420, 480, 560, 620]) {
    if (x >= W - 6) continue;
    const r = await probeAt(x);
    rows.push({ 视口宽: W, 锚点x: x, ...r });
    console.log(`  锚点 x=${String(x).padStart(3)} → ${r.菜单没开 ? '❌ 菜单没开' :
      `${(r.子菜单pos || '?').padEnd(9)} 菜单 ${r.菜单[0]}..${r.菜单[0] + r.菜单[2]} 宽${r.菜单[2]}×${r.菜单[3]}  飞出右边界 ${r.飞出右边界}`}`);
  }
}

await tab.keyboard.press('Escape'); await tab.waitForTimeout(300);
await tab.close();
console.log('\n共享页签复位:', JSON.stringify(await pinViewport(shared)), JSON.stringify({ sel: await R.selCount(), credits: await R.credits() }));
const fs = await import('node:fs');
fs.writeFileSync(new URL('./_tmp-b170u.json', import.meta.url), JSON.stringify(rows, null, 1));
await b.close();
