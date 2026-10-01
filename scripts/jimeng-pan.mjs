// 健壮版视口平移：小步拖拽，每步不超过 140px，避开 dock / 左栏 / 右上角
import { chromium } from 'playwright';

export async function makePanner(page) {
  // 找一个确定空白的起点：反复探测，直到 elementFromPoint 不在任何交互元素里
  const start = await page.evaluate(() => {
    const bad = (n) => !n || n.closest('.react-flow__node') || n.closest('button') || n.closest('input') ||
      n.closest('[data-testid="workspace-bottom-dock-frame"]') || n.closest('[data-testid="canvas-fixed-toolbar-left-rail"]') ||
      n.closest('[data-testid="canvas-top-bar-actions"]') || n.closest('[data-testid="canvas-panel-launcher"]') ||
      n.closest('[role="menu"]') || n.closest('[role="listbox"]') || n.closest('[data-testid="node-toolbar"]');
    for (const [x, y] of [[640, 660], [700, 640], [900, 660], [500, 650], [300, 620], [640, 300], [1100, 300]]) {
      if (!bad(document.elementFromPoint(x, y))) return { x, y };
    }
    return null;
  });
  if (!start) return { ok: false, why: '找不到安全空白起点' };
  return {
    start,
    async move(dx, dy) {
      // ⚠️ 符号：鼠标拖拽方向与画布内容移动方向相反。
      //    本函数收「希望节点在屏幕上移动多少」，内部取反后再拖。
      const tdx = -dx, tdy = -dy;
      // 拆成 ≤140px 的小步
      const steps = Math.max(1, Math.ceil(Math.max(Math.abs(tdx), Math.abs(tdy)) / 140));
      const sx = tdx / steps, sy = tdy / steps;
      await page.mouse.move(start.x, start.y);
      await page.mouse.down();
      for (let i = 0; i < steps; i++) {
        await page.mouse.move(start.x + sx * (i + 1), start.y + sy * (i + 1));
        await page.waitForTimeout(35);
      }
      await page.mouse.up();
      await page.waitForTimeout(800);
    },
  };
}

// 直接当脚本跑：把视频节点挪到目标位置
if (import.meta.url === `file://${process.argv[1]}`) {
  const TX = Number(process.argv[2] || 434), TY = Number(process.argv[3] || 220);
  const browser = await chromium.connectOverCDP('http://127.0.0.1:9444');
  const ctx = browser.contexts()[0];
  const page = ctx.pages().find((p) => p.url().includes('jimeng.jianying.com'));
  const cdp = await ctx.newCDPSession(page);
  await cdp.send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 720, deviceScaleFactor: 2, mobile: false });
  await page.waitForTimeout(700);
  for (let i = 0; i < 3; i++) { await page.keyboard.press('Escape'); await page.waitForTimeout(380); }
  const T = () => page.evaluate(() => { const v = document.querySelector('.react-flow__viewport'); return v ? v.style.transform : '?'; });
  const panner = await makePanner(page);
  console.log('pan 起点 =', JSON.stringify(panner.start));
  if (panner.why) { console.error(panner.why); process.exit(2); }
  for (let round = 0; round < 40; round++) {
    const v = await page.evaluate(() => { const n = document.querySelector('.react-flow__node-video'); if (!n) return null; const r = n.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y) }; });
    if (!v) { console.log('无视频节点'); break; }
    const dx = TX - v.x, dy = TY - v.y;
    if (Math.abs(dx) <= 3 && Math.abs(dy) <= 3) { console.log(`round ${round}: 到位 @${v.x},${v.y}`); break; }
    await panner.move(dx, dy);
    const v2 = await page.evaluate(() => { const n = document.querySelector('.react-flow__node-video'); const r = n.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y) }; });
    console.log(`round ${round}: 拖 (${dx},${dy}) → @${v2.x},${v2.y}  | ${await T()}`);
    if (Math.abs(v2.x - v.x) < 2 && Math.abs(v2.y - v.y) < 2) { console.log('位移无变化，停止'); break; }
  }
  console.log('最终 =', await T());
  console.log('节点 =', JSON.stringify(await page.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => { const r = n.getBoundingClientRect(); return { t: (n.innerText || '').split('\n').pop().trim().slice(0, 12), x: Math.round(r.x), y: Math.round(r.y) }; }))));
  await browser.close();
}
