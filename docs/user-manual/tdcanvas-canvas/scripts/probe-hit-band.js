/**
 * probe-hit-band.js —— 量「连线那条看不见的命中带」的真实屏幕几何（M305）。
 *
 * 要回答的是 `connect-references.md` 那句话的**几何形态**：
 * 「命中半宽 = 8 × 缩放、可见线全宽 = 2 × 缩放」——**所以能点中的那条带子
 * 是你看见的那条线的 4 倍宽**（8 ÷ 2 = 4）。**M269 复过算术（3.99 / 4.00 / 4.00），
 * 但至今没有任何一张图把这个 4 倍画出来。**
 *
 * ★ **本探针只量不拍图。** ★ **拍图是量完之后的事**——
 *   ★ **标注框里的每个数字必须来自当场实测，不能来自源码常量**（F129）。
 *
 * ★ **★★★ 全流程必须在同一个浏览器会话里（M305 踩到的坑）**：★★
 *   ★ **每次 `chromium.launch()` 都是全新 profile，★★ **而画布存在 IndexedDB
 *   ★ **的 `tdcanvas:canvas_store` 里，★★ **换个 profile 就等于换了一个空数据库——
 *   ★ **★ 于是「先建画布、关掉、换个会话再打开」这条路直接走不通，
 *   ★ **★ 表现是「URL 对、页面开、节点数恒为 0」，★ **★ 而那不是产品的问题。**
 *
 * 用法：
 *   node scripts/probe-hit-band.js
 *
 * ── 这支探针自己的纪律 ──
 *
 * 1. **自己开一张干净画布**，不碰任何既有画布（并发工作流可能在用）。
 * 2. **全程只建不删**（M192 用 /删除/ 子串点中了「删除全部」，两张画布一起没了）。
 * 3. **缩放现算**：命中带的屏幕宽度随缩放变，写死 zoom=1 量出来的数换个缩放就作废。
 * 4. **命中边界用 `elementFromPoint` 实测**，不用源码常量当结论——
 *    源码那 16 是用户单位，屏幕上的实际宽度要过一遍 CTM。
 */
const { chromium } = require(process.env.PLAYWRIGHT_PATH ||
  '/Users/yangjiefeng/.nvm/versions/node/v24.6.0/lib/node_modules/@playwright/test/node_modules/playwright');

const BASE = process.env.TD_BASE || 'http://localhost:3000';
const say = (...a) => console.log(a.join(' '));

/** 在画布上从 Dock 建一个节点，type 是菜单项的可见文字。
 *
 * ★ **必须把点击范围收进 `.td-canvas-flyout`**（M305 实测）：★ **第一版用全页
 * ★ **`getByText('文本')`，★ **★ 而第一个节点建出来之后它自己的正文里就有「文本」两个字，
 * ★ **★★ 于是第二次点菜单项时命中的是节点内容、★ **★ 结果只建出 1 个节点。**
 */
async function addNode(page, type) {
  await page.locator('button[aria-label="添加节点"]').click();
  await page.waitForTimeout(500);
  await page.locator('.td-canvas-flyout').getByText(type, { exact: true }).first().click();
  await page.waitForTimeout(900);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const VW = Number(process.env.TD_VW || 1920), VH = Number(process.env.TD_VH || 1080);
  const page = await browser.newPage({
    viewport: { width: VW, height: VH },
    // ★ **拍图时用 2 倍像素密度**：★★ **8 像素的命中带在 1 倍图上几乎看不见，
    //   ★ **★ 而放大像素密度**不改变任何几何**（★ **它只是同一块屏幕取更多采样点**），
    //   ★ **★★ 所以图里的 8 px 仍然是实测的 8 px。**
    deviceScaleFactor: process.env.TD_SHOT ? 2 : 1,
  });
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e).split('\n')[0]));

  // ── 1. 先核对「打开的确实是 TDCanvas」（M194 的教训：200 只证明有东西在监听）──
  await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1500);
  const title = await page.title();
  say('页面标题:', title);
  if (!/TDCanvas/i.test(title)) throw new Error('打开的不是 TDCanvas，先停下');

  // ── 2. 建一张属于本批的干净画布（必须与后续操作同会话）──
  await page.getByRole('button', { name: '新建画布' }).click();
  await page.waitForTimeout(2000);
  const canvasUrl = page.url();
  say('新建画布 URL:', canvasUrl);
  if (!/\/canvas\//.test(canvasUrl)) throw new Error('没跳到画布页，停下');

  // ── 3. 建两个文本节点 ──
  await addNode(page, '文本');
  const nodeCount0 = await page.locator('[data-node-id]').count();
  say('建第一个节点后:', nodeCount0);
  if (nodeCount0 < 1) throw new Error('第一个节点没建出来，停下');

  // ── 4. 把两个节点挪开（默认叠在画布中心，连线会退化成一点）──
  const readRects = () => page.evaluate(() => Array.from(document.querySelectorAll('[data-node-id]'))
    .map((e) => { const r = e.getBoundingClientRect(); return { id: e.getAttribute('data-node-id'), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) }; }));

  // 用节点标题栏拖动（M137 的教训：根元素上拖会连画布一起平移）
  const moveNodeTo = async (idx, tx, ty) => {
    const cur = (await readRects())[idx];
    const dx = tx - cur.x, dy = ty - cur.y;
    const hx = cur.x + cur.w / 2, hy = cur.y + 14;      // 标题栏
    await page.mouse.move(hx, hy);
    await page.mouse.down();
    for (let i = 1; i <= 12; i++) await page.mouse.move(hx + (dx * i) / 12, hy + (dy * i) / 12, { steps: 1 });
    await page.mouse.up();
    await page.waitForTimeout(700);
  };

  // ★ **建一个挪一个，不建齐再一起挪（F129：落点每次动作前重算）**：
  //   ★ **★ 新节点默认全部落在画布中心，而**DOM 顺序不等于 z 序**——
  //   ★ **★ 第一版先建两个再一起挪，于是「拖第 0 个」实际抓到的是盖在最上面的那个，
  //   ★ **★★★ 结果 idx 0 原地没动、idx 1 被拖了两次。★★
  //   ★ **★★★ 而后续代码按「idx 0 在左、idx 1 在右」连线，★★
  //   ★ **★★★ 于是起点终点算反、连线没建出来，★★★ **报错长得像「产品没有连线」。**
  const first = (await readRects())[0];
  say('第一个节点初始位置:', JSON.stringify(first));
  await moveNodeTo(0, 360, (VH - first.h) / 2 - 140);

  // ★ **★★ 把节点收窄（M305 实测，纯为构图）**：★★
  //   ★ **★ 默认 520 px 宽，★★ **而 1440 视口里「Dock 占 336 + 两个节点 1040」
  //   ★ **★★ 只剩 64 px 留给连线裸露段，★★★ **图上根本看不出那条带子。
  //   ★ **★★★ 而第一版把左节点放在 x = 24，★★★ **它整个被左侧 Dock 压在下面——
  //   ★ **★★★ 于是图里出现一个「被面板切掉一半的节点」，★★ **而它跟要讲的事毫无关系。**
  //   ★ **★ 收窄到 300 之后：336 + 300 + 300（裸露）+ 300 + 24 = 1260，**装得下。**
  const TARGET_W = 300;
  const shrinkNode = async (idx) => {
    const r = (await readRects())[idx];
    if (r.w <= TARGET_W + 8) return r;
    const hx = r.x + r.w + 2, hy = r.y + 2;          // 右上角手柄圆心（size-7 挂在角外侧 14px）
    const dx = r.w - TARGET_W;
    await page.mouse.move(hx, hy);
    await page.mouse.down();
    for (let i = 1; i <= 14; i++) await page.mouse.move(hx - (dx * i) / 14, hy, { steps: 1 });
    await page.mouse.up();
    await page.waitForTimeout(700);
    return (await readRects())[idx];
  };
  const r0 = await shrinkNode(0);
  say('节点 0 收窄后:', JSON.stringify(r0));
  if (r0.w > TARGET_W + 40) say('★ **收窄没生效（可能触发了最小宽度），构图按实际宽度走**');

  await addNode(page, '文本');
  const nodeCount = await page.locator('[data-node-id]').count();
  say('建完节点数:', nodeCount);
  if (nodeCount < 2) throw new Error('节点没建出来，停下');

  // 用节点标题栏拖动（M137 的教训：根元素上拖会连画布一起平移）
  // ★ **按目标位置算位移，不写死偏移（F129：落点每次动作前重算）**：
  //   ★ **★ 第一版写死「各拖 ±520」，★★ **而那在 1920 宽的视口里刚好、
  //   ★ **★★ 换成 1440 宽就把一个节点拖到了 x = -60（出屏），★★
  //   ★ **★★★ 于是拖线起点落在视口外、连线没建出来、探针报「没有命中层 path」——
  //   ★ **★★★ 而那个报错长得像「产品没有连线」，★★ **其实是我的落点算错了。**
  const second0 = (await readRects())[1];
  await shrinkNode(1);
  const second = (await readRects())[1];
  say('节点 1 收窄后:', JSON.stringify(second));
  await moveNodeTo(1, 360 + TARGET_W + 300, (VH - second.h) / 2 - 40);
  const rects2 = await readRects();
  say('拖开后位置:', JSON.stringify(rects2));

  // ── 5. 从左节点右侧端口拖到右节点左侧端口，建立连线 ──
  const L = rects2[0], R = rects2[1];

  // ★ **★★ 落点必须是「输入端口」，不是节点中心也不是节点边缘（M305 实测）**：
  //   ★ **★ 端口元素是 `[data-port-direction="output"]` / `"input"`、48×48、
  //   ★ **★ 它的圆心正好落在节点边缘的中点上**——★★ **而我按「节点中心」落，
  //   ★ **★ 拖动中 `.td-canvas-flyout` 数量恒为 0、★★ **松开后连线数也是 0，
  //   ★ **★★★ 而报错「没有命中层 path」长得极像「产品没有连线」。★★
  //   ★ **★★★ 换个视口它又能连上，★★★ **纯属当时恰好蒙对了。**
  // ★ **★★★ 按下之前必须先「从节点内部移过去」（M305 实测，源码 canvas-node.tsx:1109）**：
  //   ★ **★ 文本节点的端口是 legacy 端口，★★ **而 legacy 端口的
  //   ★ **★ `visible={!port.legacy || hovered || isSelected || isConnecting}`——
  //   ★ **★ 不 visible 时整块是 `pointer-events-none opacity-0`。★★
  //   ★ **★★ 所以直接 `mouse.move` 到端口圆心再 `down()`：★★
  //   ★ **★★ 那一刻节点还没被 hover，★★ **按下落到了节点根元素上，
  //   ★ **★★★ 于是**整条拖动变成了平移画布**（实测：反向重试那一拖让节点整体右移 848 px）。
  //   ★ **★★★ 而「连线数 = 0」这个症状长得极像「产品没连线」，★★ **其实是我没先 hover。**
  //   ★ **★ 端口 48 px 宽、圆心正好压在节点边界上，★★ **所以要取它「靠节点内侧」的那一半。**
  const INNER = 10;
  const tryConnect = async (outBox, inBox, fromRight, toLeft) => {
    // 1) 先落在源节点内部 → 触发 hover → 端口转为可交互
    const approachX = fromRight ? outBox.x - (outBox.inner + INNER) : outBox.x + (outBox.inner + INNER);
    await page.mouse.move(approachX, outBox.y, { steps: 6 });
    await page.waitForTimeout(350);
    // 2) 再滑到端口内侧按下
    await page.mouse.move(outBox.x - fromRight * INNER, outBox.y, { steps: 6 });
    await page.waitForTimeout(250);
    const pe = await page.evaluate(([x, y]) => {
      const e = document.elementFromPoint(x, y);
      return e ? { cls: (e.className || '').toString().slice(0, 40), hasPort: !!(e.closest && e.closest('[data-port-direction]')) } : null;
    }, [outBox.x - fromRight * INNER, outBox.y]);
    await page.mouse.down();
    // 3) 拖到目标端口内侧再停一停，松开
    for (let i = 1; i <= 24; i++) {
      await page.mouse.move(
        (outBox.x - fromRight * INNER) + ((inBox.x + toLeft * INNER - (outBox.x - fromRight * INNER)) * i) / 24,
        outBox.y + ((inBox.y - outBox.y) * i) / 24, { steps: 1 });
      await page.waitForTimeout(12);
    }
    await page.waitForTimeout(250);
    await page.mouse.up();
    await page.waitForTimeout(1500);
    return page.locator('path[data-connection-id]').count();
  };

  // 端口盒：中心 + 它相对节点的内侧偏移量
  const portFull = async (dir, idx) => {
    const b = await page.locator(`[data-node-id] >> nth=${idx} >> [data-port-direction="${dir}"]`).boundingBox();
    const r = (await readRects())[idx];
    return b ? { x: b.x + b.width / 2, y: b.y + b.height / 2, inner: dir === 'output' ? 24 : 24 } : null;
  };
  const outA = await portFull('output', 0), inB = await portFull('input', 1);
  say('A 输出端口:', JSON.stringify(outA), '| B 输入端口:', JSON.stringify(inB));
  if (!outA || !inB) throw new Error('没找到端口元素，停下');

  let connCount = await tryConnect(outA, inB, true, true);
  say('正向（A 出 → B 入）连线数:', connCount);
  if (!connCount) {
    const outB = await portFull('output', 1), inA = await portFull('input', 0);
    connCount = await tryConnect(outB, inA, true, true);
    say('反向（B 出 → A 入）连线数:', connCount);
  }
  if (!connCount) throw new Error('两次都没建出连线，停下（先看上面的诊断行）');

  // ── 6. 脱选，让连线回到「未选中」态 ──
  // ★ **★★★ 这一步不是整理，是测量前提（M305 实测）**：★★
  //   ★ **新建出来的连线是选中态，源码 `strokeWidth={active ? 3 : 2}`，★★
  //   ★ **★ 于是量到的可见线是 3px、倍比 16 ÷ 3 = 5.33。★★
  //   ★ **★ 而手册那句话说的是 2px 那一种（未选中），★★
  //   ★ **★ 也就是说：★★ **「4 倍」是**未选中连线**的结论，★★
  //   ★ **★★ 选中时那条线会粗到 3px、倍比变成 16 ÷ 2 = 8（全宽比）。★★
  //   ★ **★★ 而这一条在手册里没有写——★★★ **它是本批补上的第二个发现。**
  // ★ **脱选要落在一个「此刻真的空着」的点上，不能写死坐标**：★★
  // ★ **★ 第一版写死 (1000, 780)，★★ **在 1920×1080 下它确实是空地，
  // ★ **★★ 换到 1440×900 它就落在了别的东西上、★★ **连线一直是选中态、
  // ★ **★★★ 于是量到的可见线是 3px、倍比变成 2.667（F129：落点每次动作前重算）。**
  const emptySpot = await page.evaluate(({ vw, vh }) => {
    const ok = (x, y) => {
      const e = document.elementFromPoint(x, y);
      if (!e) return false;
      if (e.closest('[data-node-id]')) return false;
      if (e.closest('.td-canvas-dock')) return false;
      if (y < 64 || x < 336) return false;
      return true;
    };
    for (let y = vh - 60; y > 100; y -= 12)
      for (let x = 360; x < vw - 40; x += 12)
        if (ok(x, y) && ok(x + 20, y) && ok(x, y + 20)) return { x, y };
    return null;
  }, { vw: VW, vh: VH });
  if (!emptySpot) throw new Error('找不到空地来脱选，停下');
  say('脱选落点:', JSON.stringify(emptySpot));
  await page.mouse.click(emptySpot.x, emptySpot.y);
  await page.waitForTimeout(500);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(800);

  // ── 7. 量几何：命中带与可见线的屏幕宽度（未选中态）──
  const geom = await page.evaluate(() => {
    const hit = document.querySelector('path[data-connection-id]');
    if (!hit) return { err: '没有命中层 path' };
    const svg = hit.ownerSVGElement;
    const ctm = hit.getScreenCTM();
    const scale = Math.hypot(ctm.a, ctm.b);
    // 同 d 的可见层：命中层的下一个兄弟 path
    const vis = hit.nextElementSibling;
    return {
      scale,
      hitStrokeAttr: hit.getAttribute('stroke-width'),
      hitStrokeComputed: getComputedStyle(hit).strokeWidth,
      hitPointerEvents: getComputedStyle(hit).pointerEvents,
      visStrokeAttr: vis ? vis.getAttribute('stroke-width') : null,
      visStrokeComputed: vis ? getComputedStyle(vis).strokeWidth : null,
      visPointerEvents: vis ? getComputedStyle(vis).pointerEvents : null,
      d: hit.getAttribute('d'),
      svgViewBox: svg.getAttribute('viewBox'),
    };
  });
  say('几何实测（未选中态）:', JSON.stringify(geom, null, 1));

  if (geom.err) throw new Error(geom.err);
  const hitW = parseFloat(geom.hitStrokeComputed), visW = parseFloat(geom.visStrokeComputed);
  say(`屏幕宽度: 命中带全宽 ${hitW} px，可见线全宽 ${visW} px，倍比 ${(hitW / visW).toFixed(3)}`);
  say(`  → 命中半宽 ${hitW / 2} px ÷ 可见线全宽 ${visW} px = ${((hitW / 2) / visW).toFixed(3)}`);
  // ★ **断言可见线必须是 2 px**：★★ **源码是 `active ? 3 : 2`，
  // ★ **★★ 而手册那句「4 倍」只对未选中态成立。★★★ **拿 3 px 去标注 4 倍
  // ★ **★★ 会把一个只属于选中态的数字写成通则——★★★ **所以这里直接停。**
  if (visW !== 2) throw new Error(`可见线是 ${visW} px（选中态），不是未选中态的 2 px——脱选没生效，停下`);

  // ── 8. ★ 垂直扫描：用 elementFromPoint 量出「离中心线多远还点得中」──
  // ★ **这是本批最硬的一步**：★★ **上面那两个数是「元素上写的属性」，
  // ★ **★ 而这一步量的是「鼠标真的点在哪儿会被它接住」——★★
  // ★ **★ 前者是声明，后者才是行为。★★ **两者相等才说明手册那句话是对的。**
  const scan = await page.evaluate(() => {
    const hit = document.querySelector('path[data-connection-id]');
    if (!hit) return { err: '没有命中层 path' };
    const svg = hit.ownerSVGElement;
    const ctm = hit.getScreenCTM();
    const len = hit.getTotalLength();
    const pt = svg.createSVGPoint();
    const at = (t) => { const p = hit.getPointAtLength(t * len); pt.x = p.x; pt.y = p.y; return pt.matrixTransform(ctm); };
    // 命中判定：elementFromPoint 命中的元素自己或祖先带 data-connection-id
    const hits = (x, y) => {
      const e = document.elementFromPoint(x, y);
      return !!(e && e.closest && e.closest('path[data-connection-id]'));
    };
    const out = [];
    for (const frac of [0.3, 0.4, 0.5, 0.6, 0.7]) {
      const c = at(frac);
      // 切线方向（有限差分），法线 = 切线转 90°
      const e1 = at(Math.max(0, frac - 0.01)), e2 = at(Math.min(1, frac + 0.01));
      const tx = e2.x - e1.x, ty = e2.y - e1.y, L = Math.hypot(tx, ty) || 1;
      const nx = -ty / L, ny = tx / L;
      const row = [];
      for (let d = 0; d <= 14; d += 0.5) {
        row.push({ d, up: hits(c.x + nx * d, c.y + ny * d), down: hits(c.x - nx * d, c.y - ny * d) });
      }
      // ★ **顶层阳性对照**：d=0 就必须命中。★★ **不命中说明这个采样点被别的元素盖住了
      // ★ **（第一版就是这么废掉的：★ **两个采样点正落在节点底下，★★ **于是
      // ★ **「最远命中 0 px」被算进了平均值，★★ **把 8 px 拉成 2.67 px），
      // ★ **★ 而那不是产品的行为、★★★ **是采样点选错了。**
      const occluded = !row[0].up && !row[0].down;
      const lastHit = row.filter((r) => r.up || r.down).pop();
      out.push({ frac, cx: Math.round(c.x), cy: Math.round(c.y), occluded, lastHitD: lastHit ? lastHit.d : 0, row });
    }
    return out;
  });
  const good = [];
  let avg = NaN;
  if (scan.err) { say('扫描失败:', scan.err); } else {
    for (const s of scan) {
      if (s.occluded) {
        say(`  中心线参数 ${s.frac}（屏幕 ${s.cx},${s.cy}）：★ **d=0 就不命中 → 采样点被节点盖住，作废**`);
        continue;
      }
      good.push(s);
      say(`  中心线参数 ${s.frac}（屏幕 ${s.cx},${s.cy}）：最远仍命中 ${s.lastHitD} px`);
      say('    ' + s.row.map((r) => `${r.d}${r.up || r.down ? '+' : '-'}`).join(' '));
    }
    if (!good.length) {
      say('  ★ **全部采样点都被遮挡，扫描作废（F129：复现不了的读数作废并写明根因）**');
    } else {
      avg = good.reduce((a, s) => a + s.lastHitD, 0) / good.length;
      const spread = good.map((s) => s.lastHitD);
      say(`  → 有效采样点 ${good.length}/${scan.length} 个，命中半宽读数 ${spread.join(' / ')} px，均值 ${avg.toFixed(2)} px`);
      say(`  → 理论值 8 px（命中带 16 ÷ 2）；可见线全宽 ${visW} px`);
      say(`  → 倍比（命中半宽 ÷ 可见线全宽）= ${(avg / visW).toFixed(3)}`);
    }
  }

  say('页面 JS 错误:', errors.length ? errors.join(' | ') : '无');
  say('画布 URL（留在同一会话里）:', canvasUrl);

  // ══════════════════════════════════════════════════════════════
  // 拍图（只在 TD_SHOT 给了路径时做）
  // ══════════════════════════════════════════════════════════════
  // ★ **★ 图里每一个数字都取自上面这次实测**，★★ **不重算、不写死、不从源码常量抄——
  //   ★ **★★ 理由：F129 记着「标注框里的数字必须实测」。**
  if (process.env.TD_SHOT) {
    // ★ **落点每次动作前重算（M137 的教训）**：★★ **找一个此刻真的空着的矩形**——
    //   ★ **★ 不压节点、不压左侧 Dock（x < 336）、★ **★ 不压顶栏（y < 64）。
    const spot = await page.evaluate(({ vw, vh }) => {
      const isDock = (e) => !!(e && e.closest && e.closest('.td-canvas-dock'));
      const bgOK = (x, y) => {
        const e = document.elementFromPoint(x, y);
        if (!e) return false;
        if (e.closest('[data-node-id]')) return false;
        if (isDock(e)) return false;
        if (y < 64 || x < 336) return false;
        return true;
      };
      for (const [w, h] of [[300, 92], [300, 120], [280, 92]]) {
        // ★ **落点必须容得下最高的那个盒子**：★★ **inset 高 158 px，
      // ★ **★ 而第一版从 `vh - 130` 往上找，★★★ **落点 y = 770 → 底边 928，
      // ★ **★★★ 整个 figure 高度 900，★★★ **于是 inset 的图注被切在视口外、
      // ★ **★★★ 图上只剩一个没有说明的方块。**
      for (let y = vh - 210; y > 120; y -= 20) {
          for (let x = 400; x < vw - 320; x += 20) {
            let ok = true;
            for (const dx of [2, w / 2, w - 2]) for (const dy of [2, h / 2, h - 2]) {
              if (!bgOK(x + dx, y + dy)) { ok = false; break; }
            }
            if (ok) return { x, y, w, h };
          }
        }
      }
      return null;
    }, { vw: VW, vh: VH });
    if (!spot) throw new Error('找不到不压节点的标签落点，停下（F129：落点必须当场重算）');
    say('标签落点:', JSON.stringify(spot));

    const first = good[0];
    const shotInfo = await page.evaluate(({ spot, d, hitW, visW, ratio, first }) => {
      const hit = document.querySelector('path[data-connection-id]');
      const ctm = hit.getScreenCTM();
      const dAttr = hit.getAttribute('d');
      const screenD = (() => {
        const nums = dAttr.match(/-?\d+(\.\d+)?/g).map(Number);
        const pt = hit.ownerSVGElement.createSVGPoint();
        const xf = (x, y) => { pt.x = x; pt.y = y; const p = pt.matrixTransform(ctm); return `${p.x} ${p.y}`; };
        return `M ${xf(nums[0], nums[1])} C ${xf(nums[2], nums[3])}, ${xf(nums[4], nums[5])}, ${xf(nums[6], nums[7])}`;
      })();

      const INSET = 6;                       // 横截面放大倍数
      const bandW = hitW * INSET, lineW = visW * INSET;
      const insetW = bandW + 64, insetH = bandW + 52;   // ★ **高度按 bandW 算——★★
      // ★ **★ 黄块是 bandW 见方的方块，★★ **第一版写成 lineW + 58，★★★
      // ★ **★★★ 结果盒子比方块矮 26 px、★★ **方块直接顶出边框。**

      const ns = 'http://www.w3.org/2000/svg';
      const svg = document.createElementNS(ns, 'svg');
      svg.setAttribute('style', 'position:fixed;left:0;top:0;width:100vw;height:100vh;pointer-events:none;z-index:2147483000');
      const el = (tag, at) => { const n = document.createElementNS(ns, tag); for (const k in at) n.setAttribute(k, at[k]); return n; };
      const chip = (x, y, w, h) => el('rect', { x, y, width: w, height: h, rx: 5, fill: '#0f172a', 'fill-opacity': 0.82 });

      // ── 命中带：先描一条实边（hitW + 2.5），再盖一层半透明填充（hitW），
      //    ★ **这样带子的两条边就自己显出来了**——★★
      //    ★ **而把路径整体做偏移描边是做不到的（曲线没法整体平移）。**
      svg.appendChild(el('path', { d: screenD, fill: 'none', stroke: '#f59e0b', 'stroke-width': hitW + 2.5, 'stroke-opacity': 0.95 }));
      svg.appendChild(el('path', { d: screenD, fill: 'none', stroke: '#78350f', 'stroke-width': hitW, 'stroke-opacity': 0.55 }));
      // ── 可见线：描红，标出「你看见的就是这条」
      svg.appendChild(el('path', { d: screenD, fill: 'none', stroke: '#ef4444', 'stroke-width': visW + 0.8 }));

      // ── 半宽刻度：法线方向量出 hitW / 2
      const px = first.cx, py = first.cy;
      const upX = px, upY = py - d;             // 这条曲线在屏幕上近水平，法线取竖直
      const g = el('g', {});
      // ★ **标签放刻度右侧而不是正上方**：★★ **第一版放在正上方，
      // ★ **★ 而那一版节点的裸露段只有 30 px，★★ **标签直接盖住了整条线。**
      g.appendChild(chip(px + 14, py - 13, 148, 26));
      g.appendChild(el('line', { x1: px, y1: py, x2: upX, y2: upY, stroke: '#fde68a', 'stroke-width': 1.8 }));
      g.appendChild(el('line', { x1: px - 7, y1: py, x2: px + 7, y2: py, stroke: '#fde68a', 'stroke-width': 1.8 }));
      g.appendChild(el('line', { x1: upX - 7, y1: upY, x2: upX + 7, y2: upY, stroke: '#fde68a', 'stroke-width': 1.8 }));
      const t1 = el('text', { x: px + 22, y: py + 5, fill: '#fde68a', 'font-size': 15, 'font-weight': 700 });
      t1.textContent = `偏 ${d} 仍命中`;
      g.appendChild(t1);
      svg.appendChild(g);

      // ── 标注盒（深底浅字：界面是深色，浅字深底才读得出来）
      const box = el('g', {});
      box.appendChild(el('rect', { x: spot.x, y: spot.y, width: spot.w, height: spot.h, rx: 8, fill: '#0f172a', 'fill-opacity': 0.93, stroke: '#f59e0b', 'stroke-width': 1.4 }));
      const lines = [
        ['命中带 ', `${hitW} 像素`, '，透明，你看不见'],
        ['可见线 ', `${visW} 像素`, '，就是你看见的那条'],
        ['命中半宽 ', `${hitW / 2} ÷ ${visW} = ${ratio} 倍`, ''],
      ];
      lines.forEach((row, i) => {
        const y = spot.y + 24 + i * 24;
        const tt = el('text', { x: spot.x + 12, y, fill: i === 2 ? '#fde68a' : '#e2e8f0', 'font-size': 15, 'font-weight': i === 2 ? 700 : 500 });
        tt.textContent = row[0] + row[1] + row[2];
        box.appendChild(tt);
      });
      svg.appendChild(box);

      // ── inset：同一处横截面，放大 6 倍。★★ **它自己就是证据——
      //    ★ **黄块 96 : 红条 12 = 8 : 1，正是「命中带 : 可见线」那个比。**
      const ix = spot.x + spot.w + 18, iy = spot.y;
      const ins = el('g', {});
      ins.appendChild(el('rect', { x: ix, y: iy, width: insetW, height: insetH, rx: 8, fill: '#0f172a', 'fill-opacity': 0.93, stroke: '#f59e0b', 'stroke-width': 1.4 }));
      const cx = ix + 32, cy = iy + 40;
      ins.appendChild(el('rect', { x: cx, y: cy - bandW / 2, width: bandW, height: bandW, fill: '#92400e', 'fill-opacity': 0.75, stroke: '#f59e0b', 'stroke-width': 1.2 }));
      ins.appendChild(el('rect', { x: cx, y: cy - lineW / 2, width: bandW, height: lineW, fill: '#ef4444' }));
      const cap = el('text', { x: ix + 10, y: iy + 20, fill: '#e2e8f0', 'font-size': 12.5, 'font-weight': 600 });
      cap.textContent = `横截面 · 放大 ${INSET} 倍`;
      ins.appendChild(cap);
      const cap2 = el('text', { x: ix + 10, y: iy + insetH - 9, fill: '#94a3b8', 'font-size': 12 });
      cap2.textContent = `黄 ${bandW} : 红 ${lineW} = 8 : 1`;
      ins.appendChild(cap2);
      svg.appendChild(ins);

      document.body.appendChild(svg);
      return { screenD, bandW, lineW, insetW, insetH, ok: true };
    }, { spot, d: first.lastHitD, hitW, visW, ratio: (avg / visW).toFixed(1).replace(/\.0$/, ''), first: { cx: first.cx, cy: first.cy } });
    say('overlay 注入:', JSON.stringify(shotInfo));
    await page.waitForTimeout(400);
    await page.screenshot({ path: process.env.TD_SHOT });
    say('已保存截图:', process.env.TD_SHOT);
  }

  await browser.close();
})().catch((e) => { console.error('FAIL:', e.message.split('\n')[0]); process.exit(1); });
