// Batch AN —— 第三轮。同一个目标，换一种写法。
//
// AL、AM 两次失败，**根因完全一样**：我在 `page.evaluate` 里手搓「找容器 → 在容器里找控件」。
// AL 猜 `position: fixed`（面板不是 fixed，是居中大面板）；
// AM 改成从文案往上爬，爬过头了 —— 取到的是 `relative h-screen w-screen`（整个应用根节点），
// `controls()` 又取了**最小**那个锚点（只有「暂无历史记录」六个字的 div），它的父容器里当然没有按钮。
//
// 两轮的失败方式都一样：**静默返回空数组**，不报错，于是后面八项全报「面板里没有这个控件」。
//
// 这一轮**不再手搓遍历**。Playwright 的 locator 自带可见性判定、作用域和
// 「这个点必须真的收到事件」的校验 —— 这些正是我手写时反复漏掉的东西。
//
// 具体做法：
//   打开  page.getByRole('button', { name: '生成历史' })
//   读数  page.getByText(label, { exact: true }) → count / boundingBox / 外层标签 / aria
//   点击  直接对它 click（locator 会自动解析到真正可点的那层）
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';

const SPACE = '10354929';
const B = 'batchAN';
const { browser, page } = await launch();

const N = () => nodeCount(page);
/** 用 locator 读一个文案对应的元素：标签、外层可点祖先、aria、坐标。 */
async function probe(label) {
  const loc = page.getByText(label, { exact: true });
  const n = await loc.count().catch(() => 0);
  if (!n) return { err: '页面上找不到这个文案' };
  const el = loc.first();
  const info = await el.evaluate((e) => {
    const r = e.getBoundingClientRect();
    const clickable = e.closest('button,[role="button"],[role="tab"],[role="menuitem"],a') || e;
    const cr = clickable.getBoundingClientRect();
    return {
      tag: e.tagName, cls: (e.className || '').toString().slice(0, 44),
      aria: e.getAttribute('aria-label'), title: e.getAttribute('title'), role: e.getAttribute('role'),
      ownText: (e.innerText || '').trim(),
      clickableTag: clickable.tagName, clickableAria: clickable.getAttribute('aria-label'),
      disabled: clickable.disabled === true || getComputedStyle(clickable).opacity < 0.45,
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      clickAt: [Math.round(cr.x + cr.width / 2), Math.round(cr.y + cr.height / 2)],
      visible: r.width > 0 && r.height > 0,
      count: document.querySelectorAll(`*`).length,
    };
  });
  return info;
}
/** 浮层：Playwright 看得见的、盖在面板上的浮层容器。 */
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
  await beginBatch(B, { note: '生成历史面板 —— 全程用 locator，不再手搓 DOM 遍历' });

  await page.getByRole('button', { name: '生成历史', exact: true }).first().click({ timeout: 8000 });
  await page.waitForTimeout(2400);
  const openMark = { close: await probe('生成历史'), empty: await probe('暂无历史记录') };
  await shot(page, 'M-103-生成历史-打开.png');

  const LABELS = ['全部画布', '本画布', '图片', '视频', '音频', '所有评级', '时间倒序', '批量操作'];
  const probes = {};
  for (const label of LABELS) probes[label] = await probe(label);
  console.log('AN0:', JSON.stringify(probes).slice(0, 2600));
  await logStep(B, { id: 'AN0-labels', title: '生成历史面板里每个控件是什么元素',
    target: '对八个文案各用 `page.getByText(label, { exact: true })` 读标签、外层可点祖先、aria、坐标',
    evidence: { openMark, probes },
    visible_text: `面板已打开（标题 ${JSON.stringify(openMark.close?.rect)}、空状态 ${JSON.stringify(openMark.empty?.ownText)}）。` +
      Object.entries(probes).map(([k, v]) => `**${k}** → ${v.err ? v.err :
        `\`${v.tag}\`（${v.cls}），外层可点祖先 \`${v.clickableTag}\`（aria=${JSON.stringify(v.clickableAria)}），` +
        `尺寸 ${JSON.stringify(v.rect)}，禁用 ${v.disabled}`}`).join('\n'),
    shot: 'M-103-生成历史-打开.png' });

  // ── 逐个点开
  const opened = {};
  for (const label of ['所有评级', '时间倒序', '批量操作', '全部画布', '本画布', '图片', '视频', '音频']) {
    const p = probes[label];
    if (p?.err) { opened[label] = { err: p.err }; continue; }
    try {
      await page.mouse.click(p.clickAt[0], p.clickAt[1]); await page.waitForTimeout(1700);
      const pop = await floating();
      const after = await probe(label);
      opened[label] = { clickAt: p.clickAt, pop, labelAfter: after?.ownText ?? after?.err };
      if (pop?.length) await shot(page, `M-104-生成历史-${label}.png`);
      // toggle 关掉：点同一个位置
      await page.mouse.click(p.clickAt[0], p.clickAt[1]).catch(() => {});
      await page.waitForTimeout(1100);
      console.log(`AN1 ${label}:`, JSON.stringify(opened[label]).slice(0, 400));
    } catch (e) { opened[label] = { err: String(e).slice(0, 200) }; }
  }
  await shot(page, 'M-105-生成历史-八项试完.png');
  await logStep(B, { id: 'AN1-dropdowns', title: '生成历史里八个控件逐个点开是什么',
    target: '逐个点击后读浮层；浮层里的选项一个都没点',
    evidence: { opened },
    visible_text: Object.entries(opened).map(([k, v]) => `**${k}** → ` +
      (v.err ? `没测成：${v.err}` :
        `点击 (${v.clickAt}) → 浮层 ${JSON.stringify(v.pop)}；点完该控件文案变成 ${JSON.stringify(v.labelAfter)}`)).join('\n') +
      `\n\n⚠️ **浮层里的选项一个都没点** —— 「批量操作」里可能有删除类操作，删的是账户里的生成产物。`,
    shot: 'M-104-生成历史-批量操作.png' });

  // ── 顶部那两枚无文字图标 + 滑杆：这次用「坐标落在面板顶部带」来找
  try {
    const band = await page.evaluate(() => {
      const t = [...document.querySelectorAll('*')].find((e) => (e.innerText || '').replace(/\s+/g, ' ').trim() === '生成历史'
        && e.getBoundingClientRect().width < 200);
      if (!t) return null;
      const y = t.getBoundingClientRect().y;
      return [...document.querySelectorAll('button,[role="button"],[class*="Slider"]')].map((b) => { const r = b.getBoundingClientRect();
        return { tag: b.tagName, aria: b.getAttribute('aria-label'), t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 10),
          cls: (b.className || '').toString().slice(0, 40),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          sameBand: Math.abs(r.y - y) < 26 && r.width > 4 }; })
        .filter((b) => b.sameBand);
    });
    const icons = (band || []).filter((b) => !b.t && !b.aria);
    const results = [];
    for (let i = 0; i < icons.length; i += 1) {
      const cx = Math.round(icons[i].rect[0] + icons[i].rect[2] / 2);
      const cy = Math.round(icons[i].rect[1] + icons[i].rect[3] / 2);
      const before = await page.evaluate(() => document.body.innerText.slice(0, 200));
      await page.mouse.click(cx, cy); await page.waitForTimeout(1600);
      const after = await page.evaluate(() => document.body.innerText.slice(0, 200));
      const panelGone = !(await page.getByText('暂无历史记录', { exact: true }).count().catch(() => 0));
      results.push({ i: i + 1, at: [cx, cy], size: [icons[i].rect[2], icons[i].rect[3]],
        changed: before !== after, panelClosed: panelGone });
      await shot(page, `M-106-生成历史-顶部图标${i + 1}.png`);
      if (!panelGone) { await page.mouse.click(cx, cy).catch(() => {}); await page.waitForTimeout(1100); }
      else { await page.getByRole('button', { name: '生成历史', exact: true }).first().click({ timeout: 8000 }).catch(() => {}); await page.waitForTimeout(1800); }
    }
    const sliders = (band || []).filter((b) => /Slider/.test(b.cls || ''));
    let sliderMove = null;
    if (sliders.length) {
      const r = sliders[0].rect;
      const read = () => page.evaluate(() => {
        const s = document.querySelector('[class*="Slider"]');
        return s ? { cls: (s.className || '').toString().slice(0, 60), style: (s.getAttribute('style') || '').slice(0, 80),
          thumbs: [...s.querySelectorAll('[class*="thumb"],[class*="Thumb"]')].map((t) => (t.getAttribute('style') || '').slice(0, 60)) } : null; });
      const b4 = await read();
      await page.mouse.click(Math.round(r[0] + r[2] * 0.12), Math.round(r[1] + r[3] / 2));
      await page.waitForTimeout(1300);
      const af = await read();
      sliderMove = { rect: r, before: b4, after: af };
      await shot(page, 'M-106-生成历史-滑杆点左侧.png');
    }
    await logStep(B, { id: 'AN2-top-bar', title: '生成历史顶部条：两枚无文字图标 + 中间那根滑杆',
      target: '按「与标题同一水平带」这个几何条件挑出顶部控件，逐个点一次；滑杆点到最左',
      evidence: { band, icons, results, sliders, sliderMove },
      visible_text: `标题同一水平带上的控件 ${JSON.stringify(band)}。` +
        `其中无文字图标 ${icons.length} 枚，逐个点开：${JSON.stringify(results)}。` +
        `滑杆 ${JSON.stringify(sliders)}；点最左前后读数 ${JSON.stringify(sliderMove)}。` +
        `⚠️ **面板是空的**（从没生成过东西），视图切换可能看不出差别`,
      shot: 'M-106-生成历史-顶部图标1.png' });
    console.log('AN2:', JSON.stringify({ band, results, sliderMove }).slice(0, 2200));
  } catch (e) { await logStep(B, { id: 'AN2-top-bar', title: '顶部条控件', failed: true, visible_text: String(e).slice(0, 300) }); console.log('AN2 失败', String(e).slice(0, 250)); }

  console.log('收尾节点:', await N());
} finally {
  await browser.close();
}
