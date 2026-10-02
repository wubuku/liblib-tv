// Batch AV3 —— 坐实「高级设置」的入口是 `⚙`，并把它**展开后的画面**拍下来。
//
// AV2 的决定性读数：点参数条上那枚 32×32 的 `⚙`（SVG `M14 17H5M19 7h-9`）之后，
// `diffPanels` 冒出四个新容器，其中一个是
//   `DIV|flex flex-col gap-1 pb-2 pt-1 px-2` → `联网搜索 自动校验素材 智能引用 AutoLink`
// 而**面板高度从 246 变成 411**（`[391,479,658,246]` → `[391,479,658,411]`）。
//
// 也就是：**入口是 `⚙`，不是那四个字「高级设置」。**
// 那四个字是标题（`div.pt-3.text-xs.font-bold`），点它命中的是画布背景 ——
// Batch AU 盯着那四个字试了十三轮，然后我把「我没找到入口」写成了「产品没有这个功能」。
// **那是同一个错误的第二次**：第一次是 AU5 的「默认展开」，这次是 AU 末尾的「没有展开态」。
//
// 这轮要钉死的三件事：
//   ① `⚙` 是不是 **toggle**（再点一下会不会收回去）—— §15 记过 toggle 坑，先读状态再点
//   ② 展开后**三个开关各自是什么状态**（`aria-checked` / `checked`）
//   ③ 展开后的**完整画面**（Batch AU 那节最大的遗憾就是没有画面）
//
// ⚠️ 仍然不点 `文A`（八成是翻译提示词，可能扣积分），不点提交箭头。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView, fingerprint, diffPanels } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAV3';
const { browser, page } = await launch();

const panelRect = () => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return { err: '没有选中节点' };
  const c = [...n.querySelectorAll('div')]
    .map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((o) => o.r.width > 400 && o.r.height > 100)
    .filter((o) => (o.e.innerText || '').includes('参考'))
    .sort((a, b) => (a.r.width * a.r.height) - (b.r.width * b.r.height))[0];
  if (!c) return { err: '没找到面板' };
  return { rect: [Math.round(c.r.x), Math.round(c.r.y), Math.round(c.r.width), Math.round(c.r.height)],
    bottom: Math.round(c.r.bottom), fullyVisible: c.r.x >= 0 && c.r.y >= 0 && c.r.right <= 1440 && c.r.bottom <= 810 };
});

/** 找 `⚙` 并读它周围那三个开关的当前状态（**先读状态再决定点不点**，§15.6）。 */
const readAdvanced = () => page.evaluate(() => {
  const n = document.querySelector('.react-flow__node.selected');
  if (!n) return { err: '没选中节点' };
  const p = [...n.querySelectorAll('div')]
    .map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((o) => o.r.width > 400 && o.r.height > 100)
    .filter((o) => (o.e.innerText || '').includes('参考'))
    .sort((a, b) => (a.r.width * a.r.height) - (b.r.width * b.r.height))[0]?.e;
  if (!p) return { err: '没找到面板' };
  const isGear = (e) => { const s = e.querySelector('svg');
    if (!s) return false;
    const ds = [...s.querySelectorAll('path')].map((x) => x.getAttribute('d') || '').filter(Boolean);
    return ds.some((d) => d.startsWith('M14 17H5')); };
  const gear = [...p.querySelectorAll('button')].find(isGear);
  // 三个开关的当前状态
  const sw = [...p.querySelectorAll('.mantine-Switch-root,[class*="Switch-trackLabel"],[role="switch"],input[type="checkbox"]')]
    .map((e) => {
      const lab = (e.closest('label,[class*="flex"]') || e.parentElement)?.textContent || '';
      const inp = e.querySelector?.('input') || (e.tagName === 'INPUT' ? e : null);
      const track = e.classList.contains('mantine-Switch-root') ? e.querySelector('[class*="track"]') : e;
      return { label: lab.replace(/\s+/g, ' ').trim().slice(0, 16),
        checked: inp ? (inp.checked === true ? true : inp.checked === false ? false : null)
          : (e.getAttribute('aria-checked') || track?.getAttribute('data-checked') || null),
        rect: (() => { const q = e.getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; })(),
        y: Math.round(e.getBoundingClientRect().y) };
    });
  // grid-rows-[0fr] 那个容器的当前计算值
  const grid = p.querySelector('[class*="grid-rows-"]');
  const cs = grid ? getComputedStyle(grid) : null;
  const gr = grid ? grid.getBoundingClientRect() : null;
  return {
    gearFound: !!gear,
    gearRect: gear ? (() => { const q = gear.getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; })() : null,
    switches: sw,
    gridRowsClass: grid ? (grid.getAttribute('class') || '').match(/grid-rows-\[\d?fr?\]?/)?.[0] || (grid.getAttribute('class') || '').slice(-30) : null,
    gridRowsComputed: cs ? cs.gridTemplateRows : null,
    gridH: gr ? Math.round(gr.height) : null,
    gridInnerH: grid?.firstElementChild ? grid.firstElementChild.clientHeight : null,
    any1frOnPage: document.querySelectorAll('[class*="grid-rows-\\[1fr\\]"]').length,
    sliders: [...p.querySelectorAll('.mantine-Slider-root')].map((e) => {
      const q = e.getBoundingClientRect();
      return { rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
        y: Math.round(q.y), value: e.querySelector('[aria-valuenow]')?.getAttribute('aria-valuenow') || null };
    }),
  };
});

async function selectByText(t) {
  const plan = await page.evaluate((t) => {
    for (const n of document.querySelectorAll('.react-flow__node')) {
      if (!(n.innerText || '').includes(t) || n.classList.contains('selected')) continue;
      const r = n.getBoundingClientRect();
      if (r.x < 5 || r.x + r.width > 1435 || r.y < 60 || r.y + r.height > 800) continue;
      for (const [fx, fy] of [[0.5, 0.4], [0.5, 0.5], [0.35, 0.5], [0.65, 0.5], [0.5, 0.25], [0.5, 0.3], [0.5, 0.7]]) {
        const cx = r.x + r.width * fx, cy = r.y + r.height * fy;
        const on = document.elementFromPoint(cx, cy);
        if (on && n.contains(on) && !on.closest('[class*="Popover"],[class*="Menu"],[class*="Dropdown"]')) {
          return { cx: Math.round(cx), cy: Math.round(cy) };
        }
      }
    }
    return { err: '找不到可点的「' + t + '」' };
  }, t);
  if (plan.err) return plan;
  await page.mouse.click(plan.cx, plan.cy);
  await page.waitForTimeout(4000);
  return plan;
}

/** 空格 + 拖 = 平移画布（不受网格吸附影响，比拖节点精确）。 */
async function panCanvas(dx, dy) {
  await page.keyboard.down('Space');
  await page.mouse.move(700, 400);
  await page.mouse.down();
  for (let i = 1; i <= 10; i += 1) { await page.mouse.move(700 + (dx * i) / 10, 400 + (dy * i) / 10); await page.waitForTimeout(60); }
  await page.mouse.up();
  await page.keyboard.up('Space');
  await page.waitForTimeout(1500);
  return { moved: [dx, dy] };
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await fitView(page); await page.waitForTimeout(1200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(2200);
  await beginBatch(B, { note: '坐实 ⚙ 是「高级设置」入口：验证 toggle + 读开关状态 + 拍展开后的画面' });

  const out = {};
  out.sel = await selectByText('视频节点');
  console.log('AV3 选中视频:', JSON.stringify(out.sel));
  if (out.sel.err) throw new Error('视频节点没选中');

  out.before = { panel: await panelRect(), adv: await readAdvanced() };
  console.log('AV3 点之前 —— 面板:', JSON.stringify(out.before.panel.rect));
  console.log('AV3 点之前 —— gear:', out.before.adv.gearFound, JSON.stringify(out.before.adv.gearRect));
  console.log('AV3 点之前 —— grid:', out.before.adv.gridRowsClass, '计算值', out.before.adv.gridRowsComputed,
    '高', out.before.adv.gridH, '内部', out.before.adv.gridInnerH);
  console.log('AV3 点之前 —— 开关:', JSON.stringify(out.before.adv.switches));

  // ① 点第一下
  const g0 = out.before.adv.gearRect;
  const cx = g0[0] + g0[2] / 2, cy = g0[1] + g0[3] / 2;
  await page.mouse.click(cx, cy);
  await page.waitForTimeout(2800);
  out.afterClick1 = { panel: await panelRect(), adv: await readAdvanced() };
  console.log('\nAV3 点第 1 下 —— 面板:', JSON.stringify(out.afterClick1.panel.rect),
    '完全可见?', out.afterClick1.panel.fullyVisible);
  console.log('AV3 点第 1 下 —— grid:', out.afterClick1.adv.gridRowsClass, '计算值', out.afterClick1.adv.gridRowsComputed,
    '高', out.afterClick1.adv.gridH, '内部', out.afterClick1.adv.gridInnerH);
  console.log('AV3 点第 1 下 —— 开关:', JSON.stringify(out.afterClick1.adv.switches));
  console.log('AV3 点第 1 下 —— 全页 grid-rows-[1fr]:', out.afterClick1.adv.any1frOnPage);

  // ② 面板出屏就平移画布，把它拉回来
  if (!out.afterClick1.panel.fullyVisible) {
    const b = out.afterClick1.panel;
    const dy = Math.min(-20, b.bottom - 790);
    out.pan = await panCanvas(0, dy);
    out.afterPan = { panel: await panelRect() };
    console.log('AV3 平移', JSON.stringify(out.pan), '→ 面板:', JSON.stringify(out.afterPan.panel.rect),
      '完全可见?', out.afterPan.panel.fullyVisible);
  }
  await shot(page, 'M-142-视频节点-高级设置展开.png');
  out.shotExpanded = 'M-142-视频节点-高级设置展开.png';

  // ③ toggle 验证：再点一下会不会收回去
  const g1 = (await readAdvanced()).gearRect;
  await page.mouse.click(g1[0] + g1[2] / 2, g1[1] + g1[3] / 2);
  await page.waitForTimeout(2600);
  out.afterClick2 = { panel: await panelRect(), adv: await readAdvanced() };
  console.log('\nAV3 点第 2 下（toggle 验证）—— 面板:', JSON.stringify(out.afterClick2.panel.rect));
  console.log('AV3 点第 2 下 —— grid:', out.afterClick2.adv.gridRowsClass, '计算值', out.afterClick2.adv.gridRowsComputed,
    '高', out.afterClick2.adv.gridH);
  console.log('AV3 toggle 结论: 高度回到', out.afterClick2.panel.rect[3],
    '（第1下是', out.afterClick1.panel.rect[3], '）',
    out.afterClick2.panel.rect[3] < out.afterClick1.panel.rect[3] ? '→ 是 toggle，收起了' : '→ **不是 toggle**，没收起');

  await logStep(B, {
    id: 'AV3-advanced-gear-entry', title: '「高级设置」的真实入口是参数条上那枚 ⚙，并拍下展开后的画面',
    target: '**「我点不到」≠「它不存在」**。Batch AU 盯着「高级设置」那四个字试了十三轮，'
      + '把「我没找到入口」升级成了「产品没有这个功能」——**同一个错误的第二次**。'
      + '真正的入口是参数条右侧那枚 32×32 的 `⚙`，点它面板从 246 高涨到 411 高',
    evidence: out,
    visible_text: JSON.stringify({
      before: out.before.adv, after1: out.afterClick1.adv, after2: out.afterClick2.adv,
      panels: [out.before.panel.rect, out.afterClick1.panel.rect, out.afterClick2.panel.rect],
    }).slice(0, 3000),
    shot: 'M-142-视频节点-高级设置展开.png',
  });
  console.log('\nAV3 完成');
} finally {
  await browser.close();
}
