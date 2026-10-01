// 健壮版视口平移：小步拖拽，每步不超过 140px，避开 dock / 左栏 / 右上角
import { chromium } from 'playwright';

export async function makePanner(page) {
  // ⚠️ 必须先切到**抓手工具**：选择工具下在空白处拖拽是**框选**，不是平移 ——
  //    那样拖完 translate 纹丝不动，函数却返回「成功」（批次 50 实测踩过）。
  const tool = await page.evaluate(() => {
    const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
    if (!t) return { ok: false, why: '找不到抓手工具开关' };
    if (t.getAttribute('aria-label') !== '抓手工具') { t.click(); }
    return { ok: true, now: t.getAttribute('aria-label') };
  });
  if (!tool.ok) return { ok: false, why: tool.why };
  await page.waitForTimeout(600);

  // 起点：**按真实边界矩形**网格扫描，而不是固定候选点。
  // ⚠️ 批次 50 实测：旧版固定候选表会选中 (640,660) —— 落在底栏 dock 上，
  //    拖拽静默无效；只靠 closest() 判断也漏得掉（元素不在那些容器里，
  //    但落点其实在 dock 的可视区域）。所以这里直接取各面板的 getBoundingClientRect。
  const start = await page.evaluate(() => {
    const rect = (sel) => { const e = document.querySelector(sel); return e ? e.getBoundingClientRect() : null; };
    const rail = rect('[data-testid="canvas-fixed-toolbar-left-rail"]');
    const top = rect('[data-testid="canvas-top-bar-actions"]') || rect('header');
    const dock = rect('[data-testid="workspace-bottom-dock-frame"]');
    const x0 = Math.max(90, (rail ? rail.right : 70) + 26);
    const y0 = Math.max(100, (top ? top.bottom : 58) + 26);
    const y1 = Math.min(700, (dock ? dock.top : 640) - 18);
    const bad = (n) => !n || n.closest('.react-flow__node') || n.closest('button') || n.closest('input') ||
      n.closest('[data-testid="workspace-bottom-dock-frame"]') || n.closest('[data-testid="canvas-fixed-toolbar-left-rail"]') ||
      n.closest('[data-testid="canvas-top-bar-actions"]') || n.closest('[data-testid="canvas-panel-launcher"]') ||
      n.closest('[role="menu"]') || n.closest('[role="listbox"]') || n.closest('[data-testid="node-toolbar"]');
    for (let y = y0; y <= y1; y += 20) {
      for (let x = x0; x <= 1250; x += 20) {
        if (x > 1150 && y > 580) continue;          // 右下角是「与 AI 对话」
        if (!bad(document.elementFromPoint(x, y))) return { x, y, bounds: { x0, y0, y1 } };
      }
    }
    return null;
  });
  if (!start) return { ok: false, why: '找不到安全空白起点' };
  const readTx = () => page.evaluate(() => {
    const v = document.querySelector('.react-flow__viewport');
    const m = v && /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(v.style.transform);
    return m ? { tx: +m[1], ty: +m[2] } : null;
  });
  return {
    start,
    /**
     * @param {number} dx 希望**画布内容在屏幕上**横向移动多少（正 = 向右）
     * @param {number} dy 纵向
     * 🔑 批次 50 实测（2026-10-01，缩放 60%，抓手工具）：
     *    鼠标拖 (dx,dy) → 视口 translate **同向** +(dx,dy)，画布数据不动、缩放不变。
     *    旧版注释写的「方向与直觉相反」与实测相反，已订正 —— 旧版还多取了一次负号，
     *    等于把内容往反方向推。
     */
    async move(dx, dy) {
      const tdx = dx, tdy = dy;
      const before = await readTx();
      // 拆成 ≤140px 的小步
      const steps = Math.max(1, Math.ceil(Math.max(Math.abs(tdx), Math.abs(tdy)) / 140));
      const sx = tdx / steps, sy = tdy / steps;
      await page.mouse.move(start.x, start.y);
      await page.mouse.down();
      await page.waitForTimeout(120);
      for (let i = 0; i < steps; i++) {
        await page.mouse.move(start.x + sx * (i + 1), start.y + sy * (i + 1));
        await page.waitForTimeout(45);
      }
      await page.mouse.up();
      await page.waitForTimeout(800);
      const after = await readTx();
      if (!before || !after) return { ok: false, why: '读不到视口 transform' };
      const gotX = after.tx - before.tx, gotY = after.ty - before.ty;
      // 断言真的按期望方向、按期望量移动了（不静默吞掉无效拖拽）
      if (Math.abs(gotX - tdx) > 12 || Math.abs(gotY - tdy) > 12) {
        return { ok: false, why: `拖拽未按预期生效：期望 translate +(${tdx},${tdy})，实际 +(${gotX.toFixed(1)},${gotY.toFixed(1)})`, got: { gotX, gotY } };
      }
      return { ok: true, got: { gotX, gotY } };
    },
  };
}

// 直接当脚本跑：把**视频 1** 节点挪到目标位置。
// ⚠️⚠️ 共享画布 64b58cd5 上「视频 1」是**别人的节点** —— 这个 CLI 模式会
//    **真实移动它的位置**。共享画布上禁止使用；它只保留给「自己独占的画布」调试。
//    共享画布上要挪动别人的节点，必须走 jimeng-node-cleanup.mjs 那套按 id 精确操作，
//    并且先确认该节点属于自己。
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
    const r = await panner.move(dx, dy);
    if (!r.ok) { console.error(`ABORT: ${r.why}`); break; }     // 静默无效 → 立刻停
    const v2 = await page.evaluate(() => { const n = document.querySelector('.react-flow__node-video'); const r = n.getBoundingClientRect(); return { x: Math.round(r.x), y: Math.round(r.y) }; });
    console.log(`round ${round}: 拖 (${dx},${dy}) → @${v2.x},${v2.y}  | ${await T()}`);
    if (Math.abs(v2.x - v.x) < 2 && Math.abs(v2.y - v.y) < 2) { console.log('位移无变化，停止'); break; }
  }
  console.log('最终 =', await T());
  console.log('节点 =', JSON.stringify(await page.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => { const r = n.getBoundingClientRect(); return { t: (n.innerText || '').split('\n').pop().trim().slice(0, 12), x: Math.round(r.x), y: Math.round(r.y) }; }))));
  await browser.close();
}
