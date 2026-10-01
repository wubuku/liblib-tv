// Batch AM —— 补救 batchAL。
//
// AL 的错在**面板定位**，不在打开动作：`[data-sidebar-btn="history"]` 是点开了的
// （M-96 截图里生成历史面板清清楚楚占着屏幕中央）。但我的容器检测要求
// `position: fixed`，而这个面板是**居中的大面板**（约 [72,80,1296×640]），
// 于是 `panel()` 返回 null、`panelControls()` 返回空、后面八个控件全报「面板里没有」。
//
// 修法：**不再猜容器的 CSS 属性**。
// 从一句面板里独有的文案（「暂无历史记录」/「生成历史」）出发，往上找到「够大但不超过视口」的祖先。
// 这跟 §16.1 是同一个教训的另一半 —— 猜布局容器要靠内容锚点，不能靠样式。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchAM';
const { browser, page } = await launch();

const N = () => nodeCount(page);
/** 从面板独有的文案出发往上找容器。 */
const panelBox = () => page.evaluate(() => {
  const anchors = [...document.querySelectorAll('*')].filter((e) => {
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    const r = e.getBoundingClientRect();
    return (t === '暂无历史记录' || /^生成历史\s*(全部画布|本画布)/.test(t))
      && r.width > 600 && r.height > 300;
  });
  if (!anchors.length) return null;
  // 取最靠内、但仍然够大的那个 —— 太大的是外层壳，太小的是文案自己
  const ranked = anchors.map((e) => { const r = e.getBoundingClientRect();
    return { e, area: r.width * r.height, r }; }).sort((a, b) => b.area - a.area);
  // 往上走两到三层，直到接近视口宽度的 90%
  let best = ranked[0];
  for (const { e, area } of ranked) { if (area < best.area * 0.92) best = { e, area, r: e.getBoundingClientRect() }; else break; }
  const r = best.r;
  return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    cls: (best.e.className || '').toString().slice(0, 70) };
});
const controls = () => page.evaluate(() => {
  const anchors = [...document.querySelectorAll('*')].filter((e) => {
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim(); const r = e.getBoundingClientRect();
    return (t === '暂无历史记录' || /^生成历史\s*(全部画布|本画布)/.test(t)) && r.width > 600 && r.height > 300;
  }).sort((a, b) => (a.getBoundingClientRect().width * a.getBoundingClientRect().height)
    - (b.getBoundingClientRect().width * b.getBoundingClientRect().height));
  const p = anchors[0];
  if (!p) return null;
  // 往上一层：控件都在锚点的父容器里
  const host = p.parentElement || p;
  const pick = (e) => { const r = e.getBoundingClientRect();
    return { tag: e.tagName, t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18),
      aria: e.getAttribute('aria-label'), title: e.getAttribute('title'), role: e.getAttribute('role'),
      cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
      w: Math.round(r.width), h: Math.round(r.height), type: e.getAttribute('type'),
      disabled: e.disabled === true, cls: (e.className || '').toString().slice(0, 44) }; };
  return {
    text: (host.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 400),
    buttons: [...host.querySelectorAll('button,[role="button"],[role="tab"]')].filter((e) => e.getBoundingClientRect().width > 4).map(pick),
    sliders: [...host.querySelectorAll('[class*="Slider"]')].map((e) => { const r = e.getBoundingClientRect();
      return { cls: (e.className || '').toString().slice(0, 46), aria: e.getAttribute('aria-label'),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        value: e.getAttribute('data-value') || e.querySelector('input')?.value || null }; }),
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
  await beginBatch(B, { note: '补救 AL：面板定位改成「文案锚点往上找」' });

  await page.getByRole('button', { name: '生成历史', exact: true }).first().click({ timeout: 8000 });
  await page.waitForTimeout(2400);
  const box = await panelBox();
  const base = await controls();
  await shot(page, 'M-100-生成历史-控件全读.png');
  console.log('AM0:', JSON.stringify({ box, base }).slice(0, 3000));
  await logStep(B, { id: 'AM0-controls', title: '生成历史面板的完整控件清单',
    target: '打开生成历史，从「暂无历史记录」文案往上找容器，再 dump 里面所有控件',
    evidence: { box, base },
    visible_text: `面板容器 class ${JSON.stringify(box?.cls)}，位置 ${JSON.stringify(box?.rect)}。` +
      `面板文案「${(base?.text || '').slice(0, 220)}」。` +
      `按钮 ${JSON.stringify((base?.buttons || []).map((b) => ({ 文案: b.t, aria: b.aria, 角色: b.role, 尺寸: [b.w, b.h], 中心: [b.cx, b.cy], 禁用: b.disabled })))}；` +
      `滑杆 ${JSON.stringify(base?.sliders)}`,
    shot: 'M-100-生成历史-控件全读.png' });

  // ── AM1 逐个点开有下拉的控件
  const targets = ['所有评级', '时间倒序', '批量操作', '全部画布', '本画布', '图片', '视频', '音频'];
  const probes = {};
  for (const label of targets) {
    try {
      const cur = await controls();
      const hit = (cur?.buttons || []).find((b) => b.t === label || b.aria === label);
      if (!hit) { probes[label] = { err: '面板里没有这个控件；现有哪些=' + JSON.stringify((cur?.buttons || []).map((b) => b.t || b.aria)) }; continue; }
      await page.mouse.click(hit.cx, hit.cy); await page.waitForTimeout(1700);
      const pop = await floating();
      probes[label] = { btn: { t: hit.t, aria: hit.aria, disabled: hit.disabled, c: [hit.cx, hit.cy] },
        pop, after: (await controls())?.text?.slice(0, 150) };
      if (pop?.length) {
        await shot(page, `M-101-生成历史-${label}.png`);
        const cur2 = await controls();
        const again = (cur2?.buttons || []).find((b) => b.t === label || b.aria === label);
        if (again) { await page.mouse.click(again.cx, again.cy); await page.waitForTimeout(1100); }
      }
      console.log(`AM1 ${label}:`, JSON.stringify(probes[label]).slice(0, 450));
    } catch (e) { probes[label] = { err: String(e).slice(0, 200) }; }
  }
  await logStep(B, { id: 'AM1-dropdowns', title: '生成历史里八个带下拉的控件，逐个点开是什么',
    target: '对 `所有评级` / `时间倒序` / `批量操作` / `全部画布` / `本画布` / `图片` / `视频` / `音频` 逐个点击并读浮层',
    evidence: { probes },
    visible_text: Object.entries(probes).map(([k, v]) => `**${k}** → ` +
      (v.err ? `没测成：${v.err}` :
        `控件 ${JSON.stringify(v.btn)}；浮层 ${JSON.stringify(v.pop)}；点后面板文案「${v.after}」`)).join('\n') +
      `\n\n⚠️ **浮层里的选项一个都没点** —— 「批量操作」里可能有删除类操作，删的是账户里的生成产物。`,
    shot: 'M-101-生成历史-批量操作.png' });

  // ── AM2 顶部两枚视图切换图标 + 中间那根滑杆
  try {
    const cur = await controls();
    const icons = (cur?.buttons || []).filter((b) => !b.t && !b.aria && b.w <= 40 && b.cy < 200);
    const beforeText = cur?.text;
    const results = [];
    for (let i = 0; i < icons.length; i += 1) {
      const b = icons[i];
      await page.mouse.click(b.cx, b.cy); await page.waitForTimeout(1600);
      const after = await controls();
      results.push({ i, size: [b.w, b.h], c: [b.cx, b.cy], changed: beforeText !== after?.text, after: (after?.text || '').slice(0, 110) });
      await shot(page, `M-102-生成历史-顶部图标${i + 1}.png`);
      const again = (await controls())?.buttons.filter((x) => !x.t && !x.aria && x.w <= 40 && x.cy < 200)[i];
      if (again) { await page.mouse.click(again.cx, again.cy).catch(() => {}); await page.waitForTimeout(1000); }
    }
    let slider = null;
    const sl = (await controls())?.sliders || [];
    if (sl.length) {
      const r = sl[0].rect;
      const readBefore = (await controls())?.sliders?.[0]?.value;
      await page.mouse.click(Math.round(r[0] + r[2] * 0.15), Math.round(r[1] + r[3] / 2));
      await page.waitForTimeout(1200);
      const readAfter = (await controls())?.sliders?.[0]?.value;
      await shot(page, 'M-102-生成历史-滑杆拖到左侧.png');
      slider = { sl, readBefore, readAfter };
    }
    await logStep(B, { id: 'AM2-view-slider', title: '生成历史顶部那两枚图标和中间那根滑杆',
      target: '把顶部没有文字也没有 aria 的小图标逐个点一次；再把滑杆点到最左',
      evidence: { icons, beforeText, results, slider },
      visible_text: `顶部无文字图标 ${icons.length} 枚 ${JSON.stringify(icons.map((b) => ({ 尺寸: [b.w, b.h], 中心: [b.cx, b.cy] })))}；` +
        `逐个点开后面板文案是否变化 ${JSON.stringify(results.map((r) => ({ 第: r.i + 1, 变了: r.changed, 之后: r.after })))}。` +
        `滑杆 ${JSON.stringify(slider)}。⚠️ **面板是空的**（从没生成过东西），视图差异可能看不出来`,
      shot: 'M-102-生成历史-顶部图标1.png' });
    console.log('AM2:', JSON.stringify({ results, slider }).slice(0, 1800));
  } catch (e) { await logStep(B, { id: 'AM2-view-slider', title: '顶部图标与滑杆', failed: true, visible_text: String(e).slice(0, 300) }); console.log('AM2 失败', String(e).slice(0, 250)); }

  console.log('收尾节点:', await N());
} finally {
  await browser.close();
}
