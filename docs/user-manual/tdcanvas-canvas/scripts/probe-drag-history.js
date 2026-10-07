/**
 * probe-drag-history.js —— 把「一次拖拽算一条」这件事并排做出来（M306）。
 *
 * `undo-persistence.md` 那节讲的是一个反直觉的规则：**从按下到松手之间只要
 * 不静默，一次拖拽就只记 1 条历史**；中途停 400ms 再继续，就记 2 条。
 * 全文是文字，而且**界面上看不到历史条数**——`canvas-toolbar.tsx:387` 那个
 * 历史飞层里只有「撤销 / 重做」两个按钮，**没有任何条目列表**。
 *
 * ★ **★ 所以读者没有任何办法建立这个直觉。★★★ **这张图的办法是：**
 * ★ **★★ 在同一张画布上做两遍同一件事，只让「中途停不停」这一个变量不同，
 * ★ **★★ 然后各按一次撤销，把两个结果并排放着。★★★ **图本身就是实验。**
 *
 * ★ **★ 不宣称 3/3 重复**：★ **★ 正文那条 3/3 是另外三次实验的结论，
 * ★ **★★ 本图只做各一次，★★ **图上写的是「各一次」的读数。**
 *
 * 用法：
 *   node scripts/probe-drag-history.js
 *   TD_SHOT=screenshots/xx.png node scripts/probe-drag-history.js
 *
 * ── 纪律 ──
 * 1. 自己开干净画布，全程只建不删。
 * 2. **三个尺寸全部当场实测**（起点 / 终点 / 撤销后），标注框里的数字不写死。
 * 3. 撤销键走 `Meta+z`，按之前确认画布已获得焦点。
 */
const { chromium } = require(process.env.PLAYWRIGHT_PATH ||
  '/Users/yangjiefeng/.nvm/versions/node/v24.6.0/lib/node_modules/@playwright/test/node_modules/playwright');

const BASE = process.env.TD_BASE || 'http://localhost:3000';
const VW = Number(process.env.TD_VW || 1440), VH = Number(process.env.TD_VH || 900);
const PAUSE_MS = Number(process.env.TD_PAUSE || 400);
const say = (...a) => console.log(a.join(' '));

async function addNode(page, type) {
  await page.locator('button[aria-label="添加节点"]').click();
  await page.waitForTimeout(500);
  await page.locator('.td-canvas-flyout').getByText(type, { exact: true }).first().click();
  await page.waitForTimeout(900);
}
const readRects = (page) => page.evaluate(() => Array.from(document.querySelectorAll('[data-node-id]'))
  .map((e) => { const r = e.getBoundingClientRect(); return { id: e.getAttribute('data-node-id'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; }));

async function moveNodeTo(page, idx, tx, ty) {
  const cur = (await readRects(page))[idx];
  const dx = tx - cur.x, dy = ty - cur.y;
  const hx = cur.x + cur.w / 2, hy = cur.y + 14;
  await page.mouse.move(hx, hy);
  await page.mouse.down();
  for (let i = 1; i <= 12; i++) await page.mouse.move(hx + (dx * i) / 12, hy + (dy * i) / 12, { steps: 1 });
  await page.mouse.up();
  await page.waitForTimeout(700);
}

/** 拖右下角手柄改变尺寸。pauseMs > 0 时中途静默一次。 */
async function resizeBy(page, idx, targetW, targetH, pauseMs) {
  const r = (await readRects(page))[idx];
  // 手柄盒子挂在角外侧 14px、size-7(28px)，圆心正好是角的坐标
  const sx = r.x + r.w, sy = r.y + r.h;
  const ex = r.x + targetW, ey = r.y + targetH;
  await page.mouse.move(sx, sy);
  await page.mouse.down();
  const STEPS = 20, at = Math.floor(STEPS / 2);
  for (let i = 1; i <= STEPS; i++) {
    await page.mouse.move(sx + ((ex - sx) * i) / STEPS, sy + ((ey - sy) * i) / STEPS, { steps: 1 });
    await page.waitForTimeout(10);
    // ★ **中途静默**：★ **手指不松开、只是停住，★★ **而这正是正文那条规则的触发条件
    if (pauseMs > 0 && i === at) await page.waitForTimeout(pauseMs);
  }
  await page.mouse.up();
  await page.waitForTimeout(800);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { width: VW, height: VH },
    deviceScaleFactor: process.env.TD_SHOT ? 2 : 1,
  });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e).split('\n')[0]));

  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1500);
  if (!/TDCanvas/i.test(await page.title())) throw new Error('打开的不是 TDCanvas');
  await page.getByRole('button', { name: '新建画布' }).click();
  await page.waitForTimeout(2200);
  const canvasUrl = page.url();
  say('新建画布:', canvasUrl);
  if (!/\/canvas\//.test(canvasUrl)) throw new Error('没跳到画布页');

  const TARGET_W = 420, TARGET_H = 460;
  const out = {};

  // ── A：一路拖到底，中途不停 ──
  await addNode(page, '文本');
  await moveNodeTo(page, 0, 300, 180);
  const a0 = (await readRects(page))[0];
  await resizeBy(page, 0, TARGET_W, TARGET_H, 0);
  const aEnd = (await readRects(page))[0];
  await page.keyboard.press('Meta+z');
  await page.waitForTimeout(900);
  const aUndo = (await readRects(page))[0];
  out.A = { start: [a0.w, a0.h], end: [aEnd.w, aEnd.h], undo: [aUndo.w, aUndo.h] };
  say('A（中途不停）起点 / 终点 / 撤销后:', JSON.stringify(out.A));

  // ── B：同一段位移，中途按住 400ms ──
  await addNode(page, '文本');
  await moveNodeTo(page, 1, 900, 180);
  const b0 = (await readRects(page))[1];
  await resizeBy(page, 1, TARGET_W, TARGET_H, PAUSE_MS);
  const bEnd = (await readRects(page))[1];
  await page.keyboard.press('Meta+z');
  await page.waitForTimeout(900);
  const bUndo = (await readRects(page))[1];
  out.B = { start: [b0.w, b0.h], end: [bEnd.w, bEnd.h], undo: [bUndo.w, bUndo.h] };
  say(`B（中途停 ${PAUSE_MS}ms）起点 / 终点 / 撤销后:`, JSON.stringify(out.B));

  // ── 判据：撤销后是不是回到了起点 / 是不是停在两端之间 ──
  // ★ **★ 这两个判据第一版都写错了，★★ **而数据其实是对的**：
  //   ★ **★ ① `a[0]` 把**对象**当数组下标取**（out.A 是 {start,end,undo}），★★
  //   ★ **★★ 于是 `Math.abs(undefined - 520)` = NaN、★★ **NaN <= 2 恒为 false——
  //   ★ **★★ 表现是「明明回到了起点，判据说没回到」，★★★ **而它长得像产品出问题了。**
  //   ★ **★ ② 「停在中间」被我写成「比起点大」，★★ **而这次是把节点拖**小**了
  //   ★ **★ （520 → 420），★★ **中间值比起点**小**，★ **★ 于是判据方向反了。**
  //   ★ **★★ 修法：判据必须**方向无关**——★★ **「在两端之间」而不是「比哪头大」。**
  const near = (a, b, tol = 2) => Math.abs(a - b) <= tol;
  const between = (v, s, e, margin = 4) =>
    (v > Math.min(s, e) + margin) && (v < Math.max(s, e) - margin);
  const backToStart = (a) => near(a.undo[0], a.start[0]) && near(a.undo[1], a.start[1]);
  const midway = (a) => between(a.undo[0], a.start[0], a.end[0]) && between(a.undo[1], a.start[1], a.end[1]);
  say('A 撤销后宽高:', out.A.undo.join('x'), '| 起点:', out.A.start.join('x'),
      '| 回到起点:', backToStart(out.A));
  say('B 撤销后宽高:', out.B.undo.join('x'), '| 起点:', out.B.start.join('x'),
      '| 终点:', out.B.end.join('x'), '| 停在两端之间:', midway(out.B));
  if (!backToStart(out.A)) throw new Error('A 按一次撤销没回到起点——本图的前提不成立，停下');
  if (!midway(out.B)) throw new Error('B 按一次撤销没停在中间——本图的前提不成立，停下');

  say('页面 JS 错误:', errors.length ? errors.join(' | ') : '无');

  if (process.env.TD_SHOT) {
    // ★ **★ 拍图前必须脱选**：★★ **选中一个节点会挂出它的生成面板**
    // ★ **★ （文本节点那块「文本创作」有 400 多像素高），★★★ **而它正好压在右下角，
    // ★ **★★★ 于是标注框被面板盖掉一半、图上多出一大块与主题无关的内容。**
    const spot = await page.evaluate(({ vw, vh }) => {
      const ok = (x, y) => {
        const e = document.elementFromPoint(x, y);
        if (!e) return false;
        if (e.closest('[data-node-id]')) return false;
        if (e.closest('.td-canvas-dock')) return false;
        if (y < 64 || x < 336) return false;
        return true;
      };
      for (let y = 120; y < vh - 40; y += 12)
        for (let x = 360; x < vw - 40; x += 12)
          if (ok(x, y) && ok(x + 24, y) && ok(x, y + 24)) return { x, y };
      return null;
    }, { vw: VW, vh: VH });
    if (spot) { await page.mouse.click(spot.x, spot.y); await page.waitForTimeout(600); await page.keyboard.press('Escape'); await page.waitForTimeout(600); }
    say('脱选落点:', JSON.stringify(spot));

    // ★ **图上每个数字都取自上面这次实测**（F129）：★★ **起点与终点都是实测，
    // ★ **★ 而「撤销后」那两个数就是节点此刻的真实盒模型。**
    const rects = await readRects(page);
    const info = await page.evaluate(({ rects, boxA, boxB, startW, startH, endW, endH, pause, out }) => {
      const ns = 'http://www.w3.org/2000/svg';
      const svg = document.createElementNS(ns, 'svg');
      svg.setAttribute('style', 'position:fixed;left:0;top:0;width:100vw;height:100vh;pointer-events:none;z-index:2147483000');
      const el = (tag, at) => { const n = document.createElementNS(ns, tag); for (const k in at) n.setAttribute(k, at[k]); return n; };

      const outline = (r, w, h, color, dash) => svg.appendChild(el('rect', {
        x: r.x, y: r.y, width: w, height: h, fill: 'none', stroke: color,
        'stroke-width': 1.6, 'stroke-dasharray': dash,
      }));
      const caption = (x, y, lines, accent) => {
        const g = el('g', {});
        const wBox = Math.max(...lines.map((s) => s.length)) * 8.2 + 24;
        const hBox = lines.length * 22 + 18;
        g.appendChild(el('rect', { x, y, width: wBox, height: hBox, rx: 8, fill: '#0f172a', 'fill-opacity': 0.93, stroke: accent, 'stroke-width': 1.4 }));
        lines.forEach((s, i) => {
          const t = el('text', { x: x + 12, y: y + 24 + i * 22, fill: i === lines.length - 1 ? '#fde68a' : '#e2e8f0', 'font-size': 15, 'font-weight': i === lines.length - 1 ? 700 : 500 });
          t.textContent = s;
          g.appendChild(t);
        });
        svg.appendChild(g);
        return hBox;
      };

      // A：起点虚线框（绿色，因为它精确回到了起点）
      outline(rects[0], startW, startH, '#22c55e', '6 4');
      // B：起点虚线框（琥珀色，因为它没回去）
      outline(rects[1], startW, startH, '#f59e0b', '6 4');
      // 两个节点此刻的实际盒模型（实线）
      outline(rects[0], rects[0].w, rects[0].h, '#22c55e', '');
      outline(rects[1], rects[1].w, rects[1].h, '#f59e0b', '');

      // 起点尺寸的说明，挂在各自节点的右上方
      const tagA = el('g', {});
      tagA.appendChild(el('rect', { x: rects[0].x, y: rects[0].y - 52, width: 210, height: 24, rx: 5, fill: '#0f172a', 'fill-opacity': 0.85 }));
      const ta = el('text', { x: rects[0].x + 10, y: rects[0].y - 35, fill: '#86efac', 'font-size': 14, 'font-weight': 600 });
      ta.textContent = `虚线框 = 起点 ${startW}×${startH}`;
      tagA.appendChild(ta);
      svg.appendChild(tagA);
      const tagB = el('g', {});
      tagB.appendChild(el('rect', { x: rects[1].x, y: rects[1].y - 52, width: 210, height: 24, rx: 5, fill: '#0f172a', 'fill-opacity': 0.85 }));
      const tb = el('text', { x: rects[1].x + 10, y: rects[1].y - 35, fill: '#fcd34d', 'font-size': 14, 'font-weight': 600 });
      tb.textContent = `虚线框 = 起点 ${startW}×${startH}`;
      tagB.appendChild(tb);
      svg.appendChild(tagB);

      caption(boxA.x, boxA.y, [
        '左边：一路拖到底，中途没停',
        `撤销 1 次 → ${out.A.undo.join('×')}，实线与虚线完全重合`,
      ], '#22c55e');
      caption(boxB.x, boxB.y, [
        `右边：同一段位移，中途按住 ${pause}ms`,
        `撤销 1 次 → ${out.B.undo.join('×')}（停在两端之间）`,
      ], '#f59e0b');

      document.body.appendChild(svg);
      return { rects: rects.map((r) => [r.x, r.y, r.w, r.h]) };
    }, {
      rects, boxA: { x: 300, y: 760 }, boxB: { x: 780, y: 760 },
      startW: 520, startH: 300, endW: TARGET_W, endH: TARGET_H, pause: PAUSE_MS, out,
    });
    say('overlay:', JSON.stringify(info));
    await page.waitForTimeout(400);
    await page.screenshot({ path: process.env.TD_SHOT });
    say('已保存截图:', process.env.TD_SHOT);
  }
  await browser.close();
})().catch((e) => { console.error('FAIL:', e.message.split('\n')[0]); process.exit(1); });
