// Batch AL —— 生成历史面板：Batch A 时代拍过一张 M-01，之后再没打开过。
//
// 那张截图里的东西**一个都没点过**：
//   · 顶部那两枚视图切换图标（网格/瀑布流？）+ 缩放滑杆
//   · 「全部画布 / 本画布」切换
//   · 「图片 / 视频 / 音频」三个计数分类
//   · 「所有评级」筛选、「时间倒序」排序、「批量操作」
//
// 问题在于**面板是空的**（从没生成过东西），空面板上很多控件压根不出现。
// 所以这一轮先确认：空态下哪些控件**在 DOM 里**、哪些点了才有反应。
//
// ⚠️ 安全边界（不变）：不触发任何生成、不按 ⌘Enter、不点「整组执行」。
// 「批量操作」可能有删除类操作 —— 只打开菜单读选项，**不点任何会删的项**。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchAL';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodeList = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 10),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}));
/** 面板容器：生成历史是从哪一侧出来的？先不猜位置，直接按「盖住视口 + 有实质尺寸」找。 */
const panel = () => page.evaluate(() => [...document.querySelectorAll('*')]
  .filter((e) => {
    const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 500 && r.height > 400 && r.width < 1400 && cs.position === 'fixed'
      && r.x > -10 && r.x < 500 && r.height > 400;
  })
  .map((e) => { const r = e.getBoundingClientRect();
    return { tag: e.tagName, cls: (e.className || '').toString().slice(0, 70),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], el: e }; })
  .sort((a, b) => (b.rect[2] * b.rect[3]) - (a.rect[2] * a.rect[3]))[0] || null);
const panelControls = () => page.evaluate(() => {
  const p = [...document.querySelectorAll('*')].filter((e) => {
    const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return r.width > 500 && r.height > 400 && cs.position === 'fixed' && r.x > -10 && r.x < 500;
  }).sort((a, b) => (b.getBoundingClientRect().width * b.getBoundingClientRect().height)
    - (a.getBoundingClientRect().width * a.getBoundingClientRect().height))[0];
  if (!p) return null;
  const pick = (e) => { const r = e.getBoundingClientRect();
    return { tag: e.tagName, t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18),
      aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
      role: e.getAttribute('role'), cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
      w: Math.round(r.width), h: Math.round(r.height), type: e.getAttribute('type'),
      disabled: e.disabled === true, cls: (e.className || '').toString().slice(0, 40) }; };
  return {
    panelText: (p.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
    buttons: [...p.querySelectorAll('button,[role="button"],[role="tab"],[role="switch"]')].filter((e) => e.getBoundingClientRect().width > 4).map(pick),
    inputs: [...p.querySelectorAll('input')].filter((e) => e.getBoundingClientRect().width > 4).map(pick),
    ranges: [...p.querySelectorAll('input[type="range"],[class*="Slider"]')].map(pick),
    tabs: [...p.querySelectorAll('[role="tab"],[role="radiogroup"] *')].filter((e) => e.getBoundingClientRect().width > 4).map(pick),
  };
});
const floating = () => page.evaluate(() => [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"],[class*="Dropdown-dropdown"]')]
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { cls: (e.className || '').toString().slice(0, 36), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 240),
      items: [...e.querySelectorAll('[role="menuitem"],[role="option"],button,li,label,div')].filter((c) => {
        const cr = c.getBoundingClientRect();
        return cr.width > 24 && cr.height > 8 && cr.height < 46 && (c.innerText || '').trim().length <= 24 && !c.querySelector('div[style]');
      }).map((c) => { const cr = c.getBoundingClientRect();
        return { t: (c.innerText || '').trim(), cx: Math.round(cr.x + cr.width / 2), cy: Math.round(cr.y + cr.height / 2) }; })
        .filter((x, i, a) => a.findIndex((y) => y.t === x.t && y.cy === x.cy) === i) }; }));

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '生成历史面板：视图切换 / 画布范围 / 分类 / 评级 / 排序 / 批量操作' });

  // 建两个节点，让「本画布」和「全部画布」有可能读出差别
  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  for (const item of ['图片', '文本']) {
    let done = false;
    for (const [x, y] of [[600, 300], [600, 500], [900, 300], [900, 500]]) {
      await page.mouse.dblclick(x, y); await page.waitForTimeout(1100);
      const it = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
        .getByText(item, { exact: false }).first();
      if (await it.count().catch(() => 0)) {
        const b = await N();
        await it.click({ timeout: 4000 }).catch(() => {}); await page.waitForTimeout(2300);
        if (await N() > b) { done = true; break; }
      }
      await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(700);
    }
    console.log(`建 ${item}:`, done, await N());
  }

  const openHistory = async () => {
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(600);
    const btn = page.locator('[data-sidebar-btn="history"]').first();
    if (await btn.count().catch(() => 0)) { await btn.click({ timeout: 6000 }).catch(() => {}); }
    else await page.locator('[aria-label*="生成历史"], [title*="生成历史"]').first().click({ timeout: 6000 }).catch(() => {});
    await page.waitForTimeout(2200);
  };
  await openHistory();
  const base = await panelControls();
  const box = await panel();
  await shot(page, 'M-96-生成历史-控件全读.png');
  console.log('AL0:', JSON.stringify({ box, base }).slice(0, 3000));
  await logStep(B, { id: 'AL0-controls', title: '生成历史面板里到底有哪些控件（连 aria 一起 dump）',
    target: '打开生成历史，把面板内所有 button / input / [role=tab] / 滑杆连坐标读出来',
    evidence: { box, base },
    visible_text: `面板容器 ${JSON.stringify(box?.cls)}，位置 ${JSON.stringify(box?.rect)}；面板文案「${(base?.panelText || '').slice(0, 220)}」。` +
      `按钮 ${JSON.stringify((base?.buttons || []).map((b) => ({ 文案: b.t, aria: b.aria, 角色: b.role, 尺寸: [b.w, b.h], 禁用: b.disabled })))}；` +
      `输入框 ${JSON.stringify((base?.inputs || []).map((i) => ({ 类型: i.type, aria: i.aria, 尺寸: [i.w, i.h] })))}；` +
      `滑杆 ${JSON.stringify((base?.ranges || []).map((r) => ({ cls: r.cls, 尺寸: [r.w, r.h] })))}`,
    shot: 'M-96-生成历史-控件全读.png' });

  // ── AL1 逐个点开有下拉的控件
  const targets = ['所有评级', '时间倒序', '批量操作', '全部画布', '本画布', '图片', '视频', '音频'];
  const probes = {};
  for (const label of targets) {
    try {
      // 每次都从「面板已开」的状态重新读实时坐标，不复用旧坐标
      const cur = await panelControls();
      const hit = (cur?.buttons || []).find((b) => b.t === label || b.aria === label);
      if (!hit) { probes[label] = { err: '面板里没有这个控件' }; continue; }
      await page.mouse.click(hit.cx, hit.cy); await page.waitForTimeout(1700);
      const pop = await floating();
      probes[label] = { btn: { t: hit.t, aria: hit.aria, disabled: hit.disabled, c: [hit.cx, hit.cy] },
        pop, after: (await panelControls())?.panelText?.slice(0, 160) };
      if (pop?.length) {
        await shot(page, `M-97-生成历史-${label}.png`);
        // 关闭：点同一个按钮（toggle），不按 Esc
        const cur2 = await panelControls();
        const again = (cur2?.buttons || []).find((b) => b.t === label || b.aria === label);
        if (again) { await page.mouse.click(again.cx, again.cy); await page.waitForTimeout(1100); }
      }
      console.log(`AL1 ${label}:`, JSON.stringify(probes[label]).slice(0, 400));
    } catch (e) { probes[label] = { err: String(e).slice(0, 200) }; }
  }
  await shot(page, 'M-98-生成历史-全部控件试完.png');
  await logStep(B, { id: 'AL1-dropdowns', title: '生成历史里八个带下拉的控件，逐个点开是什么',
    target: '对 `所有评级` / `时间倒序` / `批量操作` / `全部画布` / `本画布` / `图片` / `视频` / `音频` 逐个点击并读浮层',
    evidence: { probes },
    visible_text: Object.entries(probes).map(([k, v]) => `**${k}** → ` +
      (v.err ? `没测成：${v.err}` :
        `控件 ${JSON.stringify(v.btn)}；浮层 ${JSON.stringify(v.pop)}；点后面板文案「${v.after}」`)).join('\n') +
      `\n\n⚠️ **「批量操作」的浮层只读不点** —— 里面可能有删除类操作，删的是账户里的生成产物。`,
    shot: 'M-98-生成历史-全部控件试完.png' });

  // ── AL2 顶部视图切换 + 缩放滑杆
  try {
    const cur = await panelControls();
    const iconBtns = (cur?.buttons || []).filter((b) => !b.t && !b.aria && b.w <= 40);
    const before = (await panelControls())?.panelText;
    const results = [];
    for (const b of iconBtns.slice(0, 4)) {
      await page.mouse.click(b.cx, b.cy); await page.waitForTimeout(1500);
      const after = (await panelControls())?.panelText;
      results.push({ pos: [b.cx, b.cy], size: [b.w, b.h], changed: before !== after, after: (after || '').slice(0, 120) });
      await shot(page, `M-99-生成历史-视图${results.length}.png`);
      await page.mouse.click(b.cx, b.cy).catch(() => {}); await page.waitForTimeout(1000);
    }
    const ranges = (await panelControls())?.ranges || [];
    let rangeMoved = null;
    if (ranges.length) {
      const r = ranges[0];
      const before = await page.evaluate(() => document.querySelector('[class*="Slider-root"],input[type="range"]')?.getAttribute('aria-valuenow')
        || document.querySelector('[class*="Slider-root"]')?.style?.cssText || null);
      await page.mouse.click(Math.round(r.cx + r.w * 0.25), r.cy);
      await page.waitForTimeout(1200);
      const now = await page.evaluate(() => document.querySelector('[class*="Slider-root"],input[type="range"]')?.getAttribute('aria-valuenow')
        || document.querySelector('[class*="Slider-root"]')?.style?.cssText || null);
      rangeMoved = { before, now };
      await shot(page, 'M-99-生成历史-缩放滑杆.png');
    }
    await logStep(B, { id: 'AL2-view-slider', title: '生成历史顶部的视图切换图标和缩放滑杆',
      target: '把面板里所有「没有文字也没有 aria」的小图标按钮各点一次，并拖动滑杆',
      evidence: { iconBtns, before, results, ranges, rangeMoved },
      visible_text: `面板内无文字图标按钮 ${iconBtns.length} 枚 ${JSON.stringify(iconBtns.map((b) => ({ 位置: [b.cx, b.cy], 尺寸: [b.w, b.h] })))}；` +
        `逐个点开后面板文案是否变化 ${JSON.stringify(results.map((r) => ({ 位置: r.pos, 变了: r.changed })))}。` +
        `滑杆 ${JSON.stringify(ranges.map((r) => ({ cls: r.cls, 尺寸: [r.w, r.h] })))}；点左侧后读数 ${JSON.stringify(rangeMoved)}。` +
        `⚠️ **面板是空的**（从没生成过东西），视图切换可能看不出差别`,
      shot: 'M-99-生成历史-视图1.png' });
    console.log('AL2:', JSON.stringify({ results, ranges, rangeMoved }).slice(0, 1500));
  } catch (e) { await logStep(B, { id: 'AL2-view-slider', title: '视图切换/滑杆', failed: true, visible_text: String(e).slice(0, 300) }); console.log('AL2 失败', String(e).slice(0, 250)); }

  console.log('收尾节点:', await N());
} finally {
  await browser.close();
}
