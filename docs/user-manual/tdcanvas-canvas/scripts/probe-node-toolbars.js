/**
 * probe-node-toolbars.js —— 量「同一条悬浮工具条，按节点类型与内容变几种长度」。
 *
 * 复核的是 `10-tasks/edit-nodes.md` 那张对照表。2026-10-04（M194）实测：
 * 图片空节点 4 个、图片有图 13 个、文本空节点 8 个、组 2 个，**与手册逐项逐序一致**。
 *
 * 用法：
 *   TD_PROBE_PROFILE=/tmp/m124-profile \
 *   node scripts/probe-node-toolbars.js http://localhost:3000/canvas/<画布id>
 *
 * ── 这支探针自己的教训（M194 记，都是判据的错，不是产品的错）──
 *
 * 1. **一条读数只证明一件事。** 开工时我用 `curl localhost:5173` 拿到 200 就当成了
 *    TDCanvas，探针跑完才发现那台是**另一个人的应用**（星幕 AI），登录墙 + 401。
 *    200 只证明**有东西在监听**。所以本探针第一步是核对页面标题与版本号，
 *    不是「打得开就算」。
 *
 * 2. **`elementFromPoint` 阳性对照会在「节点叠在一起」时失败。** 三个新节点默认
 *    全部落在画布中心，中心位置上盖着最上面那个节点，于是 `elementFromPoint`
 *    命中的不是我打算点的那个（`hitsSelf` 全为 false）。
 *    本探针因此**不靠坐标点节点**，改为把事件直接派发到目标节点元素上；
 *    替代证据是**不同节点必须读出不同的工具条**——若事件都落到同一个顶层节点，
 *    三条读数会一模一样。
 *
 * 3. **「上传图片」打开的是系统原生文件选择框，不是资产库弹窗。** 用 JS 的
 *    `el.click()` 点它，什么都不会弹——必须挂 `filechooser` 事件把文件喂进去。
 *    （源码侧的旁证：`AssetPickerModal` 挂在 `assetPickerOpen` 上，
 *      而那个 state 全仓库只有初始 false 与置 false 两处，**没有一处置 true**。）
 *
 * 4. **不碰任何删除类按钮。** M192 用 `/删除/` 这类子串匹配，点中了「删除全部」
 *    而不是卡片上的「删除」，两张画布一起没了。本探针全程只建不删。
 */
const { chromium } = require(process.env.PLAYWRIGHT_PATH ||
  '/Users/yangjiefeng/.nvm/versions/node/v24.6.0/lib/node_modules/@playwright/test/node_modules/playwright');

const URL = process.argv[2];
if (!URL) {
  console.error('用法：node scripts/probe-node-toolbars.js <画布URL>');
  process.exit(2);
}
const PNG = process.env.TD_PROBE_PNG || '/tmp/probe-node-toolbars.png';

const say = (...a) => console.log(a.join(' '));

/** 辅助函数在模块顶层，所以 page 必须提升到模块作用域（第一版定义在 IIFE 里，报 page is not defined）。 */
let page;

const IDS = () => Array.from(
  document.querySelectorAll('[data-canvas-node-hover-toolbar] [data-canvas-node-toolbar-action]')
).map((b) => b.getAttribute('data-canvas-node-toolbar-action'));

/** 把事件直接派发到第 idx 个节点上，绕开节点互相遮挡。 */
async function selectNodeByIndex(idx) {
  return page.evaluate(async (i) => {
    const node = document.querySelectorAll('[data-node-id]')[i];
    if (!node) return { err: '节点不存在' };
    const b = node.getBoundingClientRect();
    const cx = b.left + b.width / 2, cy = b.top + b.height / 2;
    const hit = document.elementFromPoint(cx, cy);
    // 记录但不作为通过条件：节点默认叠在中心，这里大概率是 false
    const hitsSelf = !!(hit && hit.closest('[data-node-id]') === node);
    for (const t of ['pointerdown', 'mousedown', 'mouseup', 'click']) {
      node.dispatchEvent(t.startsWith('pointer')
        ? new PointerEvent(t, { bubbles: true, clientX: cx, clientY: cy, button: 0, pointerId: 1 })
        : new MouseEvent(t, { bubbles: true, clientX: cx, clientY: cy, button: 0 }));
    }
    await new Promise((z) => setTimeout(z, 900));
    const ids = Array.from(
      document.querySelectorAll('[data-canvas-node-hover-toolbar] [data-canvas-node-toolbar-action]')
    ).map((x) => x.getAttribute('data-canvas-node-toolbar-action'));
    return { nodeId: node.getAttribute('data-node-id'), hitsSelf, ids };
  }, idx);
}

async function addNodeByMenu(item) {
  return page.evaluate(async (menu) => {
    const before = document.querySelectorAll('[data-node-id]').length;
    // 先点空白处取消选中：节点处于选中态时，创建菜单这一步不响应，
    // 节点数不涨——第一版没做这步，两次都读到「建不出来」。
    document.body.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, clientX: 5, clientY: 5, button: 0 }));
    await new Promise((r) => setTimeout(r, 350));
    const opener = Array.from(document.querySelectorAll('button'))
      .find((b) => /添加节点|新建节点/.test(b.getAttribute('aria-label') || b.textContent || ''));
    if (!opener) return { ok: false, why: '没有添加节点入口' };
    opener.click();
    await new Promise((r) => setTimeout(r, 700));
    const target = Array.from(document.querySelectorAll('button, [role="menuitem"], li'))
      .find((e) => (e.textContent || '').trim() === menu);
    if (!target) return { ok: false, why: `菜单里没有「${menu}」` };
    target.click();
    await new Promise((r) => setTimeout(r, 1500));
    return { ok: true, before, after: document.querySelectorAll('[data-node-id]').length };
  }, item);
}

(async () => {
  const profile = process.env.TD_PROBE_PROFILE || '/tmp/m124-profile';
  const ctx = await chromium.launchPersistentContext(profile, {
    headless: true, viewport: { width: 1600, height: 1000 },
  });
  page = await ctx.newPage();
  const errs = [], choosers = [];
  page.on('pageerror', (e) => errs.push(String((e && e.message) || e)));
  page.on('filechooser', async (fc) => {
    choosers.push({ multiple: fc.isMultiple() });
    await fc.setFiles(PNG).catch((e) => choosers.push({ setErr: String(e).slice(0, 120) }));
  });

  // ── 0. 身份核对：标题与版本，不是「打得开就算」（教训 1）──
  await page.goto(URL, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2500);
  const brand = await page.evaluate(() => ({
    title: document.title,
    version: (document.body.innerText.match(/v\d+\.\d+\.\d+/) || [null])[0],
    nodes: document.querySelectorAll('[data-node-id]').length,
  }));
  say(`[0] 身份核对 = ${JSON.stringify(brand)}`);
  if (!/TDCanvas/.test(brand.title || '')) {
    say('!! 这不是 TDCanvas，中止——别把别的应用的读数写进手册');
    await ctx.close();
    return;
  }

  const readings = [];

  // ── 1. 画布上已有的每个节点，各读一条 ──
  for (let i = 0; i < brand.nodes; i++) {
    const r = await selectNodeByIndex(i);
    if (r.err) { say(`  节点#${i + 1} ${r.err}`); continue; }
    readings.push({ ...r, state: '画布上原有' });
    say(`  节点#${i + 1} (${String(r.nodeId).slice(0, 14)}) 点中自己=${r.hitsSelf} → ${r.ids.length} 个 → ${JSON.stringify(r.ids)}`);
  }

  // ── 2. 补建文本与组，各读一条 ──
  for (const item of ['文本', '组']) {
    const made = await addNodeByMenu(item);
    say(`[2] 建「${item}」节点 = ${JSON.stringify(made)}`);
    if (!made.ok || made.after !== made.before + 1) {
      say(`   阳性对照不成立（节点数没 +1），跳过「${item}」的读数`);
      continue;
    }
    const r = await selectNodeByIndex(made.after - 1);
    readings.push({ ...r, state: `新建 ${item}` });
    say(`   → ${r.ids ? r.ids.length : '?'} 个 → ${JSON.stringify(r.ids)}`);
  }

  // ── 3. 图片节点：空态 4 个 → 放上图后 13 个 ──
  const imgIdx = readings.findIndex((r) => r.ids && r.ids.includes('uploadImage'));
  if (imgIdx >= 0) {
    const up = page.locator('[data-canvas-node-toolbar-action="uploadImage"]').first();
    await up.click().catch((e) => say(`   点「上传图片」失败: ${String(e).slice(0, 100)}`));
    await page.waitForTimeout(3000);
    say(`[3] 「上传图片」触发的原生文件框 = ${JSON.stringify(choosers)}`
      + `  ${choosers.length ? '' : '（没弹，对照不成立——多半不是原生文件框路径）'}`);
    await page.waitForTimeout(2500);
    const filled = await page.evaluate((i) => {
      const n = document.querySelectorAll('[data-node-id]')[i];
      return n ? n.querySelectorAll('img').length : -1;
    }, imgIdx);
    say(`    阳性对照：节点内 img 数 = ${filled}（证明文件真进去了，而不只是点了按钮）`);
    const r = await selectNodeByIndex(imgIdx);
    readings.push({ ...r, state: '图片节点（有图）' });
    say(`    有图后 → ${r.ids.length} 个 → ${JSON.stringify(r.ids)}`);
  } else {
    say('[3] 画布上没有「uploadImage」按钮（没有空的图片节点），本项跳过');
  }

  // ── 4. 收尾 ──
  say('---');
  for (const r of readings.filter(Boolean)) {
    say(`  ${r.state}｜${String(r.nodeId).slice(0, 14)}｜${r.ids.length} 个｜${r.ids.join(',')}`);
  }
  say(`[4] 不同节点读出 ${new Set(readings.map((r) => (r.ids || []).join(','))).size} 种不同工具条`
    + '（若都落到同一个顶层节点，这里会是 1 种——替代 elementFromPoint 的证据）');
  say(`[5] 页面错误 = ${JSON.stringify(errs.slice(0, 3))}`);
  await ctx.close();
})().catch((e) => { console.error('探针崩了:', e); process.exit(1); });
