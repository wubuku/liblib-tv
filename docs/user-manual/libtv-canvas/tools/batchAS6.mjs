// Batch AS6 —— 全程按 `aria-label` 定位，不再猜几何。
//
// 上一轮（AS5）把底栏整排 dump 了出来，直接把三个错处坐实了：
//
//   1. 底栏**每一枚按钮都有 aria**，而我的筛选条件是「无文字、无 aria、无 title」
//      —— 条件写反了，所以一个都没匹配上。**筛选条件里带 `!aria` 是个危险写法。**
//   2. 「+」的 aria 是 **`添加节点`**（`[580,757,32×32]`），不是「无名的图标按钮」。
//   3. AS 拿到的 `[789,757,32×32]` 是 **`快捷键`**（cx=805）——**它不是「+」**。
//      于是 AS2 读到的 `成组 G / 解组 / 连线 L / 复制节点和连线 / 缩放 / 移动画布 /
//      整理画布` 不是「常驻 DOM」，而是**被点开的快捷键面板**。§19 差点把这个
//      错误结论写进 PROGRESS，先在这里纠正。
//   4. 底栏还有一枚**独立的 `素材库` 按钮**（`[660,757,32×32]`，cx=676），
//      根本不用走「+」→「素材库」子菜单。工具箱大概率就在它里面。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';

const SPACE = '10354929';
const B = 'batchAS6';
const { browser, page } = await launch();

const floats = () => page.evaluate(() => [...document.querySelectorAll(
  '[class*="Menu-dropdown"],[class*="Popover-dropdown"],[class*="Dropdown-dropdown"],[class*="Modal-inner"],[role="dialog"],[class*="Drawer-content"]')]
  .map((e) => { const r = e.getBoundingClientRect();
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cls: (e.className || '').toString().slice(0, 70),
      isModal: /Modal-inner/.test((e.className || '').toString()) || e.getAttribute('role') === 'dialog',
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 600),
      items: [...e.querySelectorAll('button,[role="button"],[role="menuitem"],li')].map((b) => {
        const q = b.getBoundingClientRect();
        return { t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 50),
          aria: b.getAttribute('aria-label'),
          rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
          area: Math.round(q.width * q.height), disabled: b.disabled === true,
          cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2) };
      }).filter((x) => x.area > 0 && (x.t || x.aria)) }; })
  .filter((m) => m.rect[2] > 60 && m.rect[3] > 20));
const diff = (a, b) => b.filter((n) => !a.some((o) => o.rect.join() === n.rect.join() && o.text === n.text));
const clickAria = async (aria) => {
  const h = await page.evaluate((a) => {
    const e = [...document.querySelectorAll('button,[role="button"],[aria-label]')]
      .filter((x) => (x.getAttribute('aria-label') || '').trim() === a)
      .map((x) => { const r = x.getBoundingClientRect();
        return { area: Math.round(r.width * r.height), visible: r.width > 2 && r.height > 2,
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
      .find((x) => x.visible);
    return e || { err: '找不到可见的 aria-label="' + a + '"' };
  }, aria);
  if (h.err) return h;
  await page.mouse.click(h.cx, h.cy); await page.waitForTimeout(2500);
  return h;
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await beginBatch(B, { note: '全程按 aria 定位：添加节点 / 素材库 / 工具箱' });

  const out = {};

  // ① 「添加节点」面板 —— 顺便纠正 AS 读错的那次
  const f0 = await floats();
  out.addBtn = await clickAria('添加节点');
  const f1 = await floats();
  out.addPanel = diff(f0, f1).find((n) => !n.isModal) || null;
  await shot(page, 'M-127-添加节点面板.png');
  console.log('AS6 添加节点面板:', JSON.stringify(out.addPanel).slice(0, 1200));

  // ② 「素材库」按钮（**不是**通过「+」的子菜单）
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(900);
  const g0 = await floats();
  out.libBtn = await clickAria('素材库');
  const g1 = await floats();
  out.libPanel = diff(g0, g1).find((n) => !n.isModal) || null;
  await shot(page, 'M-128-素材库面板.png');
  console.log('AS6 素材库面板:', JSON.stringify(out.libPanel).slice(0, 1600));

  // ③ 「打开工具箱」
  const tb = (out.libPanel?.items || []).find((i) => /工具箱/.test((i.t || '') + (i.aria || '')));
  out.toolboxBtn = tb || null;
  if (tb) {
    await page.mouse.click(tb.cx, tb.cy);
    await page.waitForTimeout(3400);
    await shot(page, 'M-129-工具箱弹窗.png');
    const g2 = await floats();
    out.dialog = g2.find((n) => n.isModal) || diff(g1, g2)[0] || null;
    out.dialogButtons = (out.dialog?.items || []).map((i) => ({ t: i.t, aria: i.aria, rect: i.rect, disabled: i.disabled }));
    // **只读**：把「使用」类按钮的坐标记下来，不点
    out.useBtn = (out.dialog?.items || []).filter((i) => /使用|应用|套用|添加/.test((i.t || '') + (i.aria || '')));
    console.log('AS6 工具箱弹窗:', JSON.stringify(out.dialog).slice(0, 2200));
    console.log('AS6 使用类按钮:', JSON.stringify(out.useBtn).slice(0, 900));
  } else {
    out.toolboxErr = '素材库面板里没有工具箱项；items = '
      + JSON.stringify((out.libPanel?.items || []).map((i) => i.t || i.aria));
    console.log('AS6:', out.toolboxErr);
  }

  await logStep(B, {
    id: 'AS6-aria-toolbox', title: '底栏全部有 aria（纠正 AS 读错的那次）+ 素材库 → 工具箱',
    target: '**全程按 aria-label 定位**；工具箱弹窗里只读按钮文案与坐标，「使用」类按钮**不点**',
    evidence: out,
    visible_text: `「添加节点」面板：${JSON.stringify(out.addPanel).slice(0, 700)}。`
      + `\n\n「素材库」面板：${JSON.stringify(out.libPanel).slice(0, 800)}。`
      + `\n\n工具箱弹窗：${JSON.stringify(out.dialog).slice(0, 900)}。`
      + `\n\n使用类按钮：${JSON.stringify(out.useBtn)}`,
    shot: 'M-128-素材库面板.png',
  });
  console.log('AS6 完成');
} finally {
  await browser.close();
}
