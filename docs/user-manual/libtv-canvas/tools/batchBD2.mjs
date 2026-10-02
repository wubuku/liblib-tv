// Batch BD2 —— 接着 BD1 的三个「没跑通/没复现」往下钉。
//
// BD1 的结果里有三件事必须处理：
//
// 1. ⚠️ **网格吸附点了两下没回到原状**（第二次点完 bg 仍是 rgba(255,255,255,0.1)）。
//    手册不能写「点一下就复原」就完事，得知道是**偶发**还是**点第二下无效**。
//    这轮：带**回读重试**地关它，并且每次点击都换一种触发方式对比。
// 2. ⭐ **按第二次 `H` 没切回「移动」**（aria 仍是 `抓手工具`）。
//    手册 10-tasks/shortcuts.md 写的是「`V`/`H` 在两态间切换」—— 要坐实到底是
//    「H 单向」还是「第二次掉了」。这轮依次试：再按 H / 按 V / 点底栏那枚按钮。
// 3. **C 段（Option 拖动复制）没跑到** —— 因为上一段结束时卡在抓手态，
//    节点间互相遮挡，找不到「独占网格点」。这轮先确认真回到移动模式再跑。
// 4. **D 段（预设蓝点 tooltip）**上一轮没执行到，单独补。
//
// ⚠️ 安全边界不变：不生成、不上传、不创建、不删除、不付费。
//    C 段若新建了副本，用 ⌘Z 撤销并回读节点数。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchBD2';
const { browser, page } = await launch();

const listNodes = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { id: n.getAttribute('data-id') || '?',
    prefix: (n.getAttribute('data-id') || '?').split('-')[0],
    name: ((n.innerText || '').replace(/\s+/g, ' ').trim().split(' ')[0] || '').slice(0, 12),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }));

async function exclusivePoint(pg, id) {
  return pg.evaluate((nid) => {
    const t = [...document.querySelectorAll('.react-flow__node')].find((n) => n.getAttribute('data-id') === nid);
    if (!t) return { err: 'no node' };
    const r = t.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return { err: 'zero size' };
    for (let fy = 0.2; fy <= 0.8; fy += 0.15) for (let fx = 0.06; fx <= 0.95; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const o = document.elementFromPoint(x, y);
      if (o && o.closest('.react-flow__node') === t) return { x, y };
    }
    return { err: 'no exclusive point' };
  }, id);
}

/** 底栏按钮：aria 必须**全等**。用 alternation 会抓到 DOM 里更靠前的邻居
 *  （BD1 就因此把 `切换小地图` 当成了 `网格吸附`）。 */
async function btn(pg, aria) {
  return pg.evaluate((name) => {
    const e = [...document.querySelectorAll('button,[role="button"]')]
      .find((x) => x.getAttribute('aria-label') === name);
    if (!e) return { err: '没找到 ' + name };
    const q = e.getBoundingClientRect();
    return { x: Math.round(q.x + q.width / 2), y: Math.round(q.y + q.height / 2) };
  }, aria);
}

/** 开关/切换钮的可见态：只看 **背景色**（BD1 已坐实 class 与 aria 全都不变）。 */
const bgOf = (pg, aria) => pg.evaluate((name) => {
  const e = [...document.querySelectorAll('button,[role="button"]')]
    .find((x) => x.getAttribute('aria-label') === name);
  if (!e) return { err: '没找到 ' + name };
  return { aria: e.getAttribute('aria-label'), bg: getComputedStyle(e).backgroundColor,
    color: getComputedStyle(e).color, cls: (e.className || '').toString() };
}, aria);

const isOn = (st) => /255, 255, 255, 0\.1/.test(st.bg || '');

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1500);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  await beginBatch(B, { note: '网格吸附点第二下是否生效 / H 能否切回 / Option 拖动复制 / 预设蓝点 tooltip' });

  const out = {};

  // ═══ 1：把网格吸附关回去 —— 这次**带回读重试**，并对比两种触发方式
  console.log('--- BD2-1 网格吸附：点第二下到底生不生效 ---');
  const g0 = await bgOf(page, '网格吸附');
  console.log('进场时:', JSON.stringify(g0), '→', isOn(g0) ? '开' : '关');
  out.grid = { enter: g0, enterOn: isOn(g0) };

  /** 点一次（可选先挪开鼠标再点），回读，返回点后状态。 */
  const clickOnce = async (moveAwayFirst) => {
    if (moveAwayFirst) { await page.mouse.move(720, 300); await page.waitForTimeout(400); }
    const p = await btn(page, '网格吸附');
    if (p.err) return { err: p.err };
    await page.mouse.move(p.x, p.y); await page.waitForTimeout(250);
    await page.mouse.click(p.x, p.y); await page.waitForTimeout(2000);
    return await bgOf(page, '网格吸附');
  };

  const g1 = await clickOnce(true);
  console.log('点 1 下 →', isOn(g1) ? '开' : '关', JSON.stringify(g1.bg));
  const g2 = await clickOnce(true);
  console.log('点 2 下 →', isOn(g2) ? '开' : '关', JSON.stringify(g2.bg));
  const g3 = await clickOnce(false);
  console.log('点 3 下（不挪鼠标）→', isOn(g3) ? '开' : '关', JSON.stringify(g3.bg));

  // 结论性判断：连点三次能不能收敛到「关」
  let guard = 0;
  while (isOn(await bgOf(page, '网格吸附')) && guard < 5) { await clickOnce(true); guard += 1; }
  const gEnd = await bgOf(page, '网格吸附');
  console.log(`重试 ${guard} 次后：`, isOn(gEnd) ? '仍是开 ⚠️' : '已关 ✅');
  out.grid.toggles = [{ n: 1, on: isOn(g1) }, { n: 2, on: isOn(g2) }, { n: 3, on: isOn(g3) }];
  out.grid.retryCount = guard;
  out.grid.finalOn = isOn(gEnd);
  out.grid.restored = !isOn(gEnd);
  await shot(page, 'M-184-网格吸附-关闭态.png');
  out.shot = 'M-184-网格吸附-关闭态.png';

  // ═══ 2：`H` 到底能不能切回「移动」
  console.log('\n--- BD2-2 H 能否切回移动模式 ---');
  const toolMode = () => page.evaluate(() => {
    const b = document.querySelector('[data-sidebar-btn="tool-mode"]');
    if (!b) return { err: '没有 tool-mode 按钮' };
    const e = document.elementFromPoint(900, 300) || document.body;
    return { aria: b.getAttribute('aria-label'), cls: (b.className || '').toString(),
      bg: getComputedStyle(b).backgroundColor, cursorAt900x300: getComputedStyle(e).cursor };
  });

  await page.mouse.click(720, 300); await page.waitForTimeout(900);
  const m0 = await toolMode();
  console.log('初始:', JSON.stringify(m0));
  await page.keyboard.press('h'); await page.waitForTimeout(1800); await clearToasts(page);
  const m1 = await toolMode();
  console.log('按 H 一次:', JSON.stringify(m1));
  await shot(page, 'M-181-抓手模式.png');
  out.shot2 = 'M-181-抓手模式.png';

  const attempts = [];
  // ① 再按一次 H
  await page.keyboard.press('h'); await page.waitForTimeout(1800); await clearToasts(page);
  const m2 = await toolMode();
  attempts.push({ how: '再按一次 H', aria: m2.aria, cursor: m2.cursorAt900x300 });
  console.log('① 再按 H:', JSON.stringify(m2));
  // ② 按 V
  await page.keyboard.press('v'); await page.waitForTimeout(1800); await clearToasts(page);
  const m3 = await toolMode();
  attempts.push({ how: '按 V', aria: m3.aria, cursor: m3.cursorAt900x300 });
  console.log('② 按 V:', JSON.stringify(m3));
  // ③ 点底栏那枚按钮本身
  if (m3.aria !== '移动') {
    const p = await btn(page, m3.aria);
    if (!p.err) { await page.mouse.click(p.x, p.y); await page.waitForTimeout(1800); }
    const m4 = await toolMode();
    attempts.push({ how: '点底栏按钮本身', aria: m4.aria, cursor: m4.cursorAt900x300 });
    console.log('③ 点按钮:', JSON.stringify(m4));
  }
  out.tool = { start: m0, afterH: m1, attempts };
  out.tool.hSwitchesBothWays = attempts.some((a) => a.aria === '移动');
  out.tool.backToMove = (await toolMode()).aria === '移动';

  // 确认真的回到移动模式，否则 C 段无从下手
  if ((await toolMode()).aria !== '移动') {
    const p = await btn(page, '抓手工具');
    if (!p.err) { await page.mouse.click(p.x, p.y); await page.waitForTimeout(1800); }
    console.log('兜底点击后:', (await toolMode()).aria);
  }
  await fitView(page); await page.waitForTimeout(1500);

  // ═══ 3：Option 拖动 vs 裸拖动
  console.log('\n--- BD2-3 Option 拖动复制 ---');
  const pickDraggable = async () => {
    const ns = await listNodes();
    const order = [...ns.filter((n) => n.prefix === 't'), ...ns.filter((n) => n.prefix !== 't')];
    const tried = [];
    for (const n of order) {
      const pt = await exclusivePoint(page, n.id);
      if (!pt.err) return { n, pt, tried };
      tried.push(n.id);
    }
    return { err: '所有节点都没有独占点', tried };
  };

  const dragWith = async (mod, label) => {
    const before = await listNodes();
    const { n, pt, err } = await pickDraggable();
    if (err) return { label, err, tried: err };
    if (mod) await page.keyboard.down(mod);
    await page.mouse.move(pt.x, pt.y); await page.mouse.down();
    for (let i = 1; i <= 12; i += 1) { await page.mouse.move(pt.x + 8 * i, pt.y + 5 * i); await page.waitForTimeout(60); }
    await page.mouse.up();
    if (mod) await page.keyboard.up(mod);
    await page.waitForTimeout(2200); await clearToasts(page);
    const after = await listNodes();
    const created = after.filter((a) => !before.some((b) => b.id === a.id));
    return { label, draggedId: n.id, nBefore: before.length, nAfter: after.length,
      created: created.map((c) => ({ id: c.id, name: c.name, rect: c.rect })) };
  };

  const dOpt = await dragWith('Alt', 'Option + 拖动');
  console.log('Option+拖动:', JSON.stringify(dOpt));
  await fitView(page); await page.waitForTimeout(1500);
  const dPlain = await dragWith(null, '无修饰键 + 拖动（对照）');
  console.log('裸拖动:', JSON.stringify(dPlain));
  await shot(page, 'M-182-拖动新建副本.png');
  out.shot3 = 'M-182-拖动新建副本.png';
  out.drag = { option: dOpt, plain: dPlain };
  out.drag.optionCreates = (dOpt.created || []).length;
  out.drag.plainCreates = (dPlain.created || []).length;
  out.drag.metaAltNote = '⌘Option 要两个修饰键同时按住，Playwright 的 keyboard.down 一次只下一个 —— 本轮仍未验';

  // ═══ 复原：⌘Z 撤销副本
  let u = 0;
  while ((await listNodes()).length > 11 && u < 8) {
    await page.keyboard.press('Escape'); await page.waitForTimeout(400);
    await page.keyboard.press('Meta+z'); await page.waitForTimeout(2000);
    u += 1;
  }
  const fin = await listNodes();
  console.log(`⌘Z ×${u} 后节点数：`, fin.length, fin.map((n) => n.id).join(','));
  out.undo = { presses: u, count: fin.length, ids: fin.map((n) => n.id), ok: fin.length === 11 };

  // ═══ 4：预设工作流蓝点 tooltip
  console.log('\n--- BD2-4 预设工作流蓝点 ---');
  await page.keyboard.press('Escape'); await page.waitForTimeout(700);
  await page.keyboard.press('Tab'); await page.waitForTimeout(2500); await clearToasts(page);
  const entry = await page.evaluate(() => {
    const e = [...document.querySelectorAll('button,[role="button"],li,div')]
      .find((x) => (x.innerText || '').trim() === '预设工作流');
    if (!e) return { err: '没找到「预设工作流」入口' };
    const r = e.getBoundingClientRect();
    return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), tag: e.tagName };
  });
  if (entry.err) {
    console.log('D 跳过:', entry.err);
    out.blueDot = { err: entry.err };
  } else {
    await page.mouse.click(entry.x, entry.y); await page.waitForTimeout(2800); await clearToasts(page);
    const dots = await page.evaluate(() => {
      const all = [...document.querySelectorAll('body *')].filter((e) => {
        const r = e.getBoundingClientRect();
        if (r.width < 4 || r.width > 14 || r.height < 4 || r.height > 14) return false;
        if (e.children.length) return false;
        const m = /rgba?\((\d+),\s*(\d+),\s*(\d+)/.exec(getComputedStyle(e).backgroundColor);
        if (!m) return false;
        const [r0, g0, b0] = [+m[1], +m[2], +m[3]];
        return b0 > 150 && b0 - r0 > 50;
      });
      return all.map((e) => {
        const r = e.getBoundingClientRect();
        return { tag: e.tagName, cls: (e.className || '').toString().slice(0, 60),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          bg: getComputedStyle(e).backgroundColor,
          parentText: (e.parentElement?.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24) };
      }); });
    console.log('蓝点候选', dots.length, '个');
    for (const d of dots.slice(0, 6)) console.log('  ', JSON.stringify(d));
    const tips = [];
    for (const d of dots.slice(0, 6)) {
      const [x, y, w, h] = d.rect;
      await page.mouse.move(x + w / 2, y + h / 2); await page.waitForTimeout(1500);
      const tip = await page.evaluate(() => [...document.querySelectorAll('[class*="Tooltip-tooltip"]')]
        .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
        .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()));
      tips.push({ parentText: d.parentText, bg: d.bg, tip });
      console.log('  hover', JSON.stringify(d.parentText), '→', JSON.stringify(tip));
    }
    out.blueDot = { dots, tips, anyTooltip: tips.some((t) => t.tip && t.tip.length) };
    if (out.blueDot.anyTooltip) {
      await shot(page, 'M-183-预设蓝点提示.png');
      out.shot4 = 'M-183-预设蓝点提示.png';
    }
  }

  await logStep(B, {
    id: 'BD2-toggle-h-option-blue', title: '网格吸附第二次点击 / H 能否切回 / Option 拖动复制 / 预设蓝点',
    target: 'BD1 留下三件没跑通的事：网格吸附点第二下没复原、按第二次 H 没切回移动、'
      + 'C 段因卡在抓手态而没执行。这轮逐条钉死，网格吸附带回读重试确保复原。',
    evidence: out,
    visible_text: JSON.stringify({ grid: out.grid, tool: out.tool, drag: out.drag, undo: out.undo }).slice(0, 3500),
    shot: out.shot2,
  });
  console.log('\nBD2 完成');
} finally {
  await browser.close();
}
