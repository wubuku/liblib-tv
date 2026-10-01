// Batch AO —— Batch AN 之后剩下三个没问完的点。
//
// AN 用 locator 之后终于拿到了真读数，也暴露三处空白：
//
//   ① 「图片 / 视频 / 音频」用 `getByText(exact: true)` **找不到** ——
//      它们在界面上是「图片 0」「视频 0」「音频 0」，计数徽标把文字撑开了。
//      AN 的 AN0 直接判了「页面上找不到这个文案」，那是**我的匹配写错**，不是控件不存在。
//   ② 「时间倒序」点开**没有浮层**，而点完之后 `getByText('时间倒序')` 找不到了 ——
//      说明它不是下拉，是**点了就换**。要读出它换成了什么。
//   ③ AN2 只在 `button` 里挑顶部控件，结果挑出来的「分镜/动态/音乐/图片高清/口播视频」
//      全是**画布上「添加节点」面板的按钮**（它们在面板后面，靠得太近被几何条件误收）。
//      真正要找的两枚 ⊞ 和那根滑杆**不是 <button>**，得扫全部元素。
//
// 判据（这轮定死）：**扫元素，不扫标签**。
// 用「与标题同一水平带 + x 在面板右半区 + 尺寸像控件」三个几何条件，不预设标签名。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';

const SPACE = '10354929';
const B = 'batchAO';
const { browser, page } = await launch();

/** 「与标题同高、位于面板右半区」的所有元素 —— 不预设标签名。 */
const topBand = () => page.evaluate(() => {
  const title = [...document.querySelectorAll('*')].find((e) => (e.innerText || '').trim() === '生成历史'
    && e.getBoundingClientRect().width < 200 && e.getBoundingClientRect().y > 80);
  if (!title) return null;
  const ty = title.getBoundingClientRect().y;
  return [...document.querySelectorAll('*')].map((e) => { const r = e.getBoundingClientRect();
    return { tag: e.tagName, cls: (e.className || '').toString().slice(0, 52),
      aria: e.getAttribute('aria-label'), title: e.getAttribute('title'),
      t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      hasSvg: !!e.querySelector(':scope > svg'), kids: e.children.length }; })
    .filter((e) => e.rect[0] > 950 && e.rect[0] < 1420 && Math.abs(e.rect[1] - ty) < 30
      && e.rect[2] > 6 && e.rect[2] <= 200 && e.rect[3] > 6 && e.rect[3] <= 50);
});
const sortRow = () => page.evaluate(() => [...document.querySelectorAll('button')].map((b) => ({
  t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14), title: b.getAttribute('title'),
  rect: [Math.round(b.getBoundingClientRect().x), Math.round(b.getBoundingClientRect().y),
    Math.round(b.getBoundingClientRect().width), Math.round(b.getBoundingClientRect().height)],
  y: Math.round(b.getBoundingClientRect().y) })).filter((b) => b.y > 150 && b.y < 220 && b.rect[0] > 950));
const typeTabs = () => page.evaluate(() => [...document.querySelectorAll('button')].map((b) => ({
  t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16), title: b.getAttribute('title'),
  rect: [Math.round(b.getBoundingClientRect().x), Math.round(b.getBoundingClientRect().y),
    Math.round(b.getBoundingClientRect().width), Math.round(b.getBoundingClientRect().height)] }))
  .filter((b) => b.rect[0] > 200 && b.rect[0] < 600 && b.rect[1] > 160 && b.rect[1] < 210));

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '分类计数标签 / 排序切换 / 顶部两枚图标与滑杆' });

  await page.getByRole('button', { name: '生成历史', exact: true }).first().click({ timeout: 8000 });
  await page.waitForTimeout(2400);

  // ── AO1 分类计数标签（图片 0 / 视频 0 / 音频 0）
  const tabs0 = await typeTabs();
  const all0 = await sortRow();
  const band0 = await topBand();
  await shot(page, 'M-107-生成历史-三个区域读数.png');

  // ── AO2 「时间倒序」点了换什么 —— 连点三轮，把三个态都读出来
  const sorts = [];
  for (let i = 0; i < 3; i += 1) {
    const row = await sortRow();
    const cur = row.find((b) => /时间|最新|最早|倒序|正序/.test(b.t));
    if (!cur) { sorts.push({ err: '这一轮没找到排序按钮', row }); break; }
    const cx = Math.round(cur.rect[0] + cur.rect[2] / 2);
    const cy = Math.round(cur.rect[1] + cur.rect[3] / 2);
    const popBefore = await page.evaluate(() => [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"]')]
      .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; }).length);
    await page.mouse.click(cx, cy); await page.waitForTimeout(1700);
    const popAfter = await page.evaluate(() => [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"]')]
      .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120))
      .filter((e) => { const r = e.querySelector('.mantine-Menu-dropdown, .mantine-Popover-dropdown')?.getBoundingClientRect();
        return !!r && r.width > 40 && r.height > 12; }));
    const next = await sortRow();
    sorts.push({ before: { t: cur.t, title: cur.title }, popupBefore: popBefore,
      popupAfter: popAfter, after: next.filter((b) => /时间|最新|最早|倒序|正序/.test(b.t)) });
    await shot(page, `M-108-生成历史-排序第${i + 1}轮.png`);
  }

  // ── AO3 顶部右半区那两枚 ⊞ 和滑杆（不是 button，按几何条件扫全部元素）
  const bandIcons = (band0 || []).filter((e) => e.rect[2] <= 40 && e.rect[3] <= 40 && e.rect[2] > 10);
  const sliderLike = (band0 || []).filter((e) => e.rect[2] > 60 && e.rect[2] <= 220 && e.rect[3] <= 20);
  const iconResults = [];
  for (let i = 0; i < bandIcons.length; i += 1) {
    const b = bandIcons[i];
    const cx = Math.round(b.rect[0] + b.rect[2] / 2);
    const cy = Math.round(b.rect[1] + b.rect[3] / 2);
    const beforeText = await page.evaluate(() => document.body.innerText.slice(0, 160));
    await page.mouse.click(cx, cy); await page.waitForTimeout(1600);
    const afterText = await page.evaluate(() => document.body.innerText.slice(0, 160));
    const closed = !(await page.getByText('暂无历史记录', { exact: true }).count().catch(() => 0));
    iconResults.push({ i: i + 1, at: [cx, cy], size: [b.rect[2], b.rect[3]], cls: b.cls, kids: b.kids,
      changed: beforeText !== afterText, panelClosed: closed });
    await shot(page, `M-109-生成历史-顶部图标${i + 1}.png`);
    if (closed) { await page.getByRole('button', { name: '生成历史', exact: true }).first().click({ timeout: 8000 }).catch(() => {}); await page.waitForTimeout(1800); }
    else { await page.mouse.click(cx, cy).catch(() => {}); await page.waitForTimeout(1100); }
  }
  let slider = null;
  if (sliderLike.length) {
    const r = sliderLike[0].rect;
    const read = () => page.evaluate(() => [...document.querySelectorAll('*')]
      .filter((e) => (e.className || '').toString().includes('Slider') && e.getBoundingClientRect().width > 40)
      .map((e) => ({ cls: (e.className || '').toString().slice(0, 50),
        rect: [Math.round(e.getBoundingClientRect().x), Math.round(e.getBoundingClientRect().y),
          Math.round(e.getBoundingClientRect().width), Math.round(e.getBoundingClientRect().height)],
        html: (e.innerHTML || '').slice(0, 200) })).slice(0, 3));
    const before = await read();
    await page.mouse.click(Math.round(r[0] + r[2] * 0.1), Math.round(r[1] + r[3] / 2));
    await page.waitForTimeout(1300);
    const after = await read();
    slider = { rect: r, before, after };
    await shot(page, 'M-109-生成历史-滑杆点最左.png');
  }
  await shot(page, 'M-110-生成历史-收尾.png');

  await logStep(B, { id: 'AO1-rest', title: '生成历史剩下的三处：分类计数标签、排序切换、顶部图标与滑杆',
    target: '分类标签按坐标带扫按钮；排序连点三轮读三个态；顶部右半区按几何条件扫**全部元素**（不是只扫 button）',
    evidence: { tabs0, all0, band0, sorts, bandIcons, iconResults, sliderLike, slider },
    visible_text: `分类/范围一排按钮 ${JSON.stringify(tabs0)}；右侧一排 ${JSON.stringify(all0)}。` +
      `\n\n**排序按钮连点三轮**：${JSON.stringify(sorts)}。` +
      `\n\n**顶部右半区扫到的元素** ${JSON.stringify(band0)}；其中小图标 ${bandIcons.length} 枚，逐个点开 ${JSON.stringify(iconResults)}；` +
      `滑杆状元素 ${JSON.stringify(sliderLike)}，点最左前后 ${JSON.stringify(slider)}。` +
      `\n\n⚠️ 面板是空的，视图/滑杆效果可能看不出差别`,
    shot: 'M-110-生成历史-收尾.png' });
  console.log('AO:', JSON.stringify({ tabs0, all0, sorts, bandIcons, iconResults, sliderLike }).slice(0, 3000));

} finally {
  await browser.close();
}
