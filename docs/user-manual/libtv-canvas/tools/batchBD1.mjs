// Batch BD —— 手册里「提到但没实按」的那几枚，全部只读或可复原。
//
// 上一批结束时做了一次静态盘点：手册正文里共 71 行「📖 / 没验 / 没点过」声明。
// 按「只读就能验 / 会写数据需授权 / 环境不可能」分诊之后，这一批挑四个
// **不需要授权、且能复原**的目标：
//
// A. `网格吸附` 开关 —— 手册只写「拖动节点时是否自动对齐网格」，**没实按过**。
//    这轮：读当前态 → 点开 → **实测拖一个节点看它吸不吸附** → **点回去复原**。
//    ⭐ 吸附的判据不能只看开关变色，要看**节点落点是不是落在网格整数倍上**。
// B. `移动 / 抓手` 工具（`data-sidebar-btn="tool-mode"`，按 `H` 切换）——
//    两态的 `cursor` 分别是什么、抓手态下拖画布会怎样。
// C. `⌘` `Option` + 拖动 —— 20-reference 里 `Option` + 拖动标 ✅（验过），
//    而 **`⌘` `Option` + 拖动标 📖**（没验）。这轮对比两者有没有区别。
// D. 预设工作流图标上的**蓝点** —— 手册写「推测是推荐或新功能标记，含义未验证」。
//    这轮 hover 蓝点读 tooltip，看能不能读出官方说法。
//
// ⚠️ 全程可复原：不生成、不上传、不创建、不删除。C 会改画布内容（多一张副本），
//    验完用 `⌘Z` 或资产管理删除**复原并逐字确认**。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBD1';
const { browser, page } = await launch();

const snapScale = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const m = v ? /scale\(([\d.]+)\)/.exec(v.style.transform || '') : null;
  return m ? +m[1] : null; });

const listNodes = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id') || '?', prefix: (n.getAttribute('data-id') || '?').split('-')[0],
    cls: ((/react-flow__node-([a-zA-Z]+)/.exec(n.className || '') || [])[1] || '?'),
    name: ((n.innerText || '').replace(/\s+/g, ' ').trim().split(' ')[0] || '').slice(0, 10),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }));

async function exclusivePoint(pg, id) {
  return pg.evaluate((nid) => {
    const t = [...document.querySelectorAll('.react-flow__node')].find((n) => n.getAttribute('data-id') === nid);
    if (!t) return { err: 'no node' };
    const r = t.getBoundingClientRect();
    for (let fy = 0.2; fy <= 0.8; fy += 0.15) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const o = document.elementFromPoint(x, y);
      if (o && o.closest('.react-flow__node') === t) return { x, y };
    }
    return { err: 'no exclusive point' };
  }, id);
}

/** 按 aria-label 找底栏左侧按钮。 */
async function clickByAria(pg, re) {
  const pt = await pg.evaluate((r) => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => new RegExp(r).test(x.getAttribute('aria-label') || x.getAttribute('title') || ''));
    if (!e) return { err: '没找到 ' + r };
    const q = e.getBoundingClientRect();
    return { x: Math.round(q.x + q.width / 2), y: Math.round(q.y + q.height / 2),
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
      aria: e.getAttribute('aria-label'), cls: (e.className || '').toString().slice(0, 60) }; }, re);
  if (pt.err) return pt;
  await pg.mouse.click(pt.x, pt.y);
  await pg.waitForTimeout(2200);
  return pt;
}

/** 底栏开关的当前态：**aria 必须全等**，不能用 alternation ——
 *  `切换小地图` 在 DOM 里排在 `网格吸附` 前面，/网格吸附|切换小地图/ 会抓到前者。 */
const bottomSwitchState = (aria) => page.evaluate((name) => {
  const e = [...document.querySelectorAll('button,[role="button"]')]
    .find((x) => x.getAttribute('aria-label') === name);
  if (!e) return { err: '没找到 ' + name };
  const cs = getComputedStyle(e);
  return { aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
    ariaPressed: e.getAttribute('aria-pressed'), ariaChecked: e.getAttribute('aria-checked'),
    dataActive: e.getAttribute('data-active'), dataState: e.getAttribute('data-state'),
    cls: (e.className || '').toString(),
    color: cs.color, bg: cs.backgroundColor, opacity: cs.opacity }; }, aria);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1500);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1800);
  await beginBatch(B, { note: '网格吸附实按+拖动吸附验证 / 抓手工具 / ⌘Option 拖动 / 预设蓝点 tooltip' });

  const out = {};
  // 整轮开始前的节点位置，用于最后把被拖动的节点拖回去
  const originNodes = await listNodes();
  out.origin = originNodes.map((n) => ({ id: n.id, rect: n.rect }));

  // ═══ A：网格吸附
  console.log('--- BD1 A 网格吸附 ---');
  await page.keyboard.press('Meta+-'); await page.waitForTimeout(600); // 放大一点，网格才看得见
  await fitView(page); await page.waitForTimeout(1600);
  const s0 = await bottomSwitchState('网格吸附');
  console.log('初始:', JSON.stringify(s0));

  /** 从所有节点里挑**第一个找得到独占网格点**的 —— 挑死一个前缀会挑到被遮挡的节点。 */
  const pickDraggable = async (preferPrefix) => {
    const ns = await listNodes();
    const order = [...ns.filter((n) => n.prefix === preferPrefix), ...ns.filter((n) => n.prefix !== preferPrefix)];
    const tried = [];
    for (const n of order) {
      const pt = await exclusivePoint(page, n.id);
      if (!pt.err) return { n, pt, tried };
      tried.push(`${n.id}(${n.name})`);
    }
    return { err: '所有节点都没有独占点', tried };
  };

  /** 拖一个节点，返回它落点的屏幕坐标 + 画布 scale，看落点是不是网格整数倍。 */
  const dragOnce = async (label) => {
    const { n: cand, pt, tried } = await pickDraggable('t');
    if (pt?.err) return { err: `没有可拖的点`, tried };
    const before = (await listNodes()).find((n) => n.id === cand.id);
    // 故意拖一个**不是网格整数倍**的偏移
    const dx = 37, dy = 23;
    await page.mouse.move(pt.x, pt.y); await page.mouse.down();
    for (let i = 1; i <= 12; i += 1) { await page.mouse.move(pt.x + (dx * i) / 12, pt.y + (dy * i) / 12); await page.waitForTimeout(60); }
    await page.mouse.up(); await page.waitForTimeout(1800);
    const after = (await listNodes()).find((n) => n.id === cand.id);
    const scale = await snapScale();
    if (!after) return { err: '拖完节点不见了' };
    const movedX = after.rect[0] - before.rect[0];
    const movedY = after.rect[1] - before.rect[1];
    // 网格步长：常见是 8/10/16/20/32。这里判据是「落点相对起点的偏移是不是被取整到某个固定步长」
    const steps = [4, 8, 10, 12, 16, 20, 24, 32, 40].filter((s) =>
      movedX % s === 0 && movedY % s === 0);
    return { label, id: cand.id, before: before.rect, after: after.rect,
      movedX, movedY, scale, divisibleBy: steps,
      requested: [dx, dy] };
  };

  const dragOff = await dragOnce('吸附关闭时');
  console.log('拖动（吸附关）:', JSON.stringify(dragOff));
  await shot(page, 'M-179-网格吸附-关闭.png');
  out.grid = { before: s0, dragOff };

  const sw = await clickByAria(page, '网格吸附');
  console.log('点开关:', JSON.stringify(sw));
  const s1 = await bottomSwitchState('网格吸附');
  console.log('打开后:', JSON.stringify(s1));
  const dragOn = await dragOnce('吸附打开时');
  console.log('拖动（吸附开）:', JSON.stringify(dragOn));
  await shot(page, 'M-180-网格吸附-打开.png');
  out.shot = 'M-180-网格吸附-打开.png';
  out.grid.after = s1; out.grid.dragOn = dragOn;
  out.grid.switchChanged = JSON.stringify(s0) !== JSON.stringify(s1);

  // ✅ 点回去复原
  await clickByAria(page, '网格吸附');
  const s2 = await bottomSwitchState('网格吸附');
  console.log('复原后:', JSON.stringify(s2));
  out.grid.restored = s2;
  out.grid.restoredSame = JSON.stringify(s0) === JSON.stringify(s2);

  // ═══ B：抓手 / 移动 工具
  console.log('\n--- BD1 B 抓手 / 移动 工具 ---');
  const toolState = () => page.evaluate(() => {
    const b = document.querySelector('[data-sidebar-btn="tool-mode"]');
    if (!b) return { err: '没有 tool-mode 按钮' };
    const cs = getComputedStyle(b);
    // 画布上任意空白点的 cursor，就是当前工具的真实表现
    const probe = [[400, 200], [900, 300], [1200, 600]];
    const cursors = probe.map(([x, y]) => {
      const e = document.elementFromPoint(x, y);
      if (!e) return { at: [x, y], on: 'nothing', cursor: null };
      const hitEl = e.closest('.react-flow__pane,.react-flow__node,button');
      return { at: [x, y], on: hitEl ? (hitEl.closest('.react-flow__node') ? 'node' : 'ui') : 'canvas',
        cursor: getComputedStyle(e).cursor };
    });
    return { aria: b.getAttribute('aria-label'), title: b.getAttribute('title'),
      cls: (b.className || '').toString().slice(0, 70),
      dataActive: b.getAttribute('data-active'), cursor: cs.cursor, probes: cursors }; });

  const t0 = await toolState();
  console.log('初始:', JSON.stringify(t0).slice(0, 600));
  await page.keyboard.press('Escape'); await page.waitForTimeout(600);
  await page.mouse.click(400, 400); await page.waitForTimeout(900);
  await page.keyboard.press('h'); await page.waitForTimeout(1800); await clearToasts(page);
  const t1 = await toolState();
  console.log('按 H 后:', JSON.stringify(t1).slice(0, 600));
  await shot(page, 'M-181-抓手模式.png');
  out.shot2 = 'M-181-抓手模式.png';

  // 抓手态下拖画布，看节点整体是否跟着动
  const before2 = await listNodes();
  await page.mouse.move(400, 400); await page.mouse.down();
  for (let i = 1; i <= 10; i += 1) { await page.mouse.move(400 + 10 * i, 400); await page.waitForTimeout(60); }
  await page.mouse.up(); await page.waitForTimeout(1600);
  const after2 = await listNodes();
  const panDx = after2.length && before2.length
    ? after2[0].rect[0] - before2[0].rect[0] : null;
  console.log('抓手态拖画布：第一个节点 x 位移', panDx);
  out.tool = { before: t0, afterH: t1, panDx,
    panWorked: panDx !== null && Math.abs(panDx) > 10 };

  // ✅ 按 H 切回
  await page.keyboard.press('h'); await page.waitForTimeout(1600);
  const t2 = await toolState();
  console.log('再按 H 复原:', JSON.stringify(t2).slice(0, 400));
  out.tool.restored = t2;
  out.tool.restoredSame = JSON.stringify(t0.cls) === JSON.stringify(t2.cls);

  await fitView(page); await page.waitForTimeout(1400);

  // ═══ C：⌘Option + 拖动
  console.log('\n--- BD1 C ⌘Option 拖动 vs Option 拖动 ---');
  const pickNode = async () => {
    const { n, pt, err, tried } = await pickDraggable('t');
    if (err || !n) return { err: err || '找不到可拖节点', tried };
    return { n, pt };
  };

  const dragWith = async (withMeta, label) => {
    const before = await listNodes();
    const { n, pt } = await pickNode();
    if (!n) return { err: '没有可拖节点' };
    if (withMeta) await page.keyboard.down(withMeta);
    await page.mouse.move(pt.x, pt.y); await page.mouse.down();
    for (let i = 1; i <= 12; i += 1) { await page.mouse.move(pt.x + 8 * i, pt.y + 5 * i); await page.waitForTimeout(60); }
    await page.mouse.up();
    if (withMeta) await page.keyboard.up(withMeta);
    await page.waitForTimeout(2000); await clearToasts(page);
    const after = await listNodes();
    const created = after.filter((a) => !before.some((b) => b.id === a.id));
    return { label, id: n.id, nBefore: before.length, nAfter: after.length,
      created: created.map((c) => ({ id: c.id, name: c.name, rect: c.rect })),
      names: after.map((a) => a.name) };
  };

  await page.mouse.click(80, 120); await page.waitForTimeout(1200);
  const cOpt = await dragWith('Alt', 'Option + 拖动');
  console.log('Option+拖动:', JSON.stringify(cOpt));
  await fitView(page); await page.waitForTimeout(1400);
  await page.mouse.click(80, 120); await page.waitForTimeout(1200);
  const cOptCmd = await dragWith(null, '无修饰键 + 拖动（对照）');
  console.log('无修饰键+拖动:', JSON.stringify(cOptCmd));
  await shot(page, 'M-182-拖动新建副本.png');
  out.shot3 = 'M-182-拖动新建副本.png';
  out.drag = { option: cOpt, plain: cOptCmd };
  console.log('对比：Option 拖动新建了', cOpt.created.length, '个；不按修饰键新建了', cOptCmd.created.length, '个');
  // ⌘Option 组合键在 Playwright 里要 Meta+Alt 两个一起，按键名一次只能一个 —— 记成未验
  out.drag.metaAltNote = '⌘Option 同时按需要两个修饰键一起 down，Playwright 的 keyboard.down 一次只能下一个 —— 本轮未验';

  // ═══ 复原：⌘Z 撤掉本轮新建的副本，逐个撤到节点数回到 11
  console.log('\n--- 复原 ---');
  const undo = async () => {
    await page.keyboard.press('Escape'); await page.waitForTimeout(500);
    await page.keyboard.press('Meta+z'); await page.waitForTimeout(2000);
  };
  let guard = 0;
  while ((await listNodes()).length > 11 && guard < 6) { await undo(); guard += 1; }
  const finalNodes = await listNodes();
  console.log('撤销后节点数：', finalNodes.length, '（按了', guard, '次 ⌘Z）');
  out.restore = { undos: guard, finalCount: finalNodes.length,
    finalIds: finalNodes.map((n) => n.id),
    countRestored: finalNodes.length === 11 };
  if (finalNodes.length !== 11) {
    console.log('⚠️ 节点数没回到 11，当前：', finalNodes.map((n) => `${n.id}:${n.name}`).join(', '));
  }

  // ═══ 复原：把 A 段拖动过的节点按位移拖回去
  const nowNodes = await listNodes();
  const moved = [];
  for (const o of originNodes) {
    const cur = nowNodes.find((n) => n.id === o.id);
    if (!cur) continue;
    const dx = o.rect[0] - cur.rect[0], dy = o.rect[1] - cur.rect[1];
    if (Math.abs(dx) < 3 && Math.abs(dy) < 3) continue;
    const pt = await exclusivePoint(page, o.id);
    if (pt.err) { moved.push({ id: o.id, err: pt.err }); continue; }
    await page.mouse.move(pt.x, pt.y); await page.mouse.down();
    for (let i = 1; i <= 10; i += 1) {
      await page.mouse.move(pt.x + (dx * i) / 10, pt.y + (dy * i) / 10); await page.waitForTimeout(55);
    }
    await page.mouse.up(); await page.waitForTimeout(1300);
    moved.push({ id: o.id, dx, dy });
  }
  await fitView(page); await page.waitForTimeout(1400);
  const endNodes = await listNodes();
  const drift = originNodes.map((o) => {
    const cur = endNodes.find((n) => n.id === o.id);
    return cur ? { id: o.id, d: [cur.rect[0] - o.rect[0], cur.rect[1] - o.rect[1]] } : { id: o.id, gone: true };
  }).filter((x) => x.gone || Math.abs(x.d[0]) > 3 || Math.abs(x.d[1]) > 3);
  console.log('位置复原：拖回', moved.length, '个节点；仍有偏差的：', JSON.stringify(drift));
  out.restore.moved = moved;
  out.restore.drift = drift;
  out.restore.allBack = drift.length === 0;

  // ═══ D：预设工作流图标上的蓝点 —— hover 读 tooltip
  console.log('\n--- BD1 D 预设工作流蓝点 ---');
  await page.keyboard.press('Escape'); await page.waitForTimeout(800);
  // 打开「预设工作流」：Tab 弹「添加节点」面板 → 点预设工作流入口
  await page.keyboard.press('Tab'); await page.waitForTimeout(2200); await clearToasts(page);
  const openPreset = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"],div')]
      .find((x) => (x.innerText || '').trim() === '预设工作流');
    if (!e) return { err: '没找到「预设工作流」入口' };
    const r = e.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
  if (openPreset.err) {
    console.log('D 跳过：', openPreset.err);
    out.blueDot = { err: openPreset.err };
  } else {
    await page.mouse.click(openPreset.x, openPreset.y); await page.waitForTimeout(2600); await clearToasts(page);
    // 找蓝点：preset 面板里**没有文字的极小圆形元素**，按尺寸+颜色筛
    const dots = await page.evaluate(() => {
      const all = [...document.querySelectorAll('body *')].filter((e) => {
        const r = e.getBoundingClientRect();
        if (r.width < 4 || r.width > 14 || r.height < 4 || r.height > 14) return false;
        if (e.children.length) return false;
        const cs = getComputedStyle(e);
        const m = /rgba?\((\d+),\s*(\d+),\s*(\d+)/.exec(cs.backgroundColor);
        if (!m) return false;
        const [r0, g0, b0] = [+m[1], +m[2], +m[3]];
        return b0 > 150 && b0 - r0 > 50 && g0 > 80;   // 偏蓝
      });
      return all.map((e) => {
        const r = e.getBoundingClientRect();
        return { tag: e.tagName, cls: (e.className || '').toString().slice(0, 70),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          bg: getComputedStyle(e).backgroundColor,
          parentText: (e.parentElement?.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) };
      }); });
    console.log('蓝点候选', dots.length, '个：', JSON.stringify(dots.slice(0, 8)));
    const tooltips = [];
    for (const d of dots.slice(0, 6)) {
      const [x, y, w, h] = d.rect;
      await page.mouse.move(x + w / 2, y + h / 2); await page.waitForTimeout(1400);
      const tip = await page.evaluate(() => {
        const t = [...document.querySelectorAll('[class*="Tooltip-tooltip"]')]
          .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
          .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim());
        return t; });
      tooltips.push({ dot: d, tip });
      console.log('  hover', JSON.stringify(d.parentText), '→', JSON.stringify(tip));
    }
    out.blueDot = { dots, tooltips, anyTooltip: tooltips.some((t) => t.tip && t.tip.length) };
    if (out.blueDot.anyTooltip) await shot(page, 'M-183-预设蓝点提示.png'), (out.shot4 = 'M-183-预设蓝点提示.png');
    await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
  }

  await logStep(B, {
    id: 'BD1-grid-grip-drag', title: '网格吸附实按 / 抓手工具 / 拖动新建副本 / 预设蓝点',
    target: '手册 71 行「📖 未验」声明里，挑出**不需要授权且能复原**的四个目标。'
      + '网格吸附不只看开关变色，还要看**节点落点是不是落在网格步长上**。'
      + '全程可复原：网格吸附与抓手都点了回去，拖动产生的副本用 ⌘Z 撤销，节点位置按位移拖回。',
    evidence: out,
    visible_text: JSON.stringify({ grid: out.grid, tool: out.tool, drag: out.drag }).slice(0, 3500),
    shot: out.shot,
  });
  console.log('\nBD1 完成');
} finally {
  await browser.close();
}
