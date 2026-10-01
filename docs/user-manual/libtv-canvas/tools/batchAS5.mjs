// Batch AS5 —— 只做「+」→ 素材库 → 工具箱 这一条路径，外加给 Plugin 一个更准的结论。
//
// 先把坐标的来历说清楚（这是这轮真正的教训）：
//   AS 的 addBtn 报 `[789,757,32×32]`、AS4 的几何筛选报 `null` —— 都**不是**「+」。
//   把 M-126 的截图量一遍：「+」在显示坐标 (824,1074)，
//   ×1.44 回原图 2880 宽、再 ÷2（DPR=2）→ **CSS 坐标 (593,773)**。
//   `789` 那枚是同一排里的别的按钮（键盘/帮助）。
//
//   **「按几何条件找按钮」必须先确认筛出来的是哪一个** —— 我筛了三次，
//   三次都拿到一个「确实存在但不是我要的」元素，而且**每次都不报错**。
//   AS5 先把底栏整排按钮 dump 出来带坐标，再由坐标反推哪枚是「+」。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';

const SPACE = '10354929';
const B = 'batchAS5';
const { browser, page } = await launch();

const floats = () => page.evaluate(() => [...document.querySelectorAll(
  '[class*="Menu-dropdown"],[class*="Popover-dropdown"],[class*="Dropdown-dropdown"],[class*="Modal-inner"],[role="dialog"]')]
  .map((e) => { const r = e.getBoundingClientRect();
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cls: (e.className || '').toString().slice(0, 70),
      isModal: /Modal-inner/.test((e.className || '').toString()) || e.getAttribute('role') === 'dialog',
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 500),
      items: [...e.querySelectorAll('button,[role="button"],[role="menuitem"],li')].map((b) => {
        const q = b.getBoundingClientRect();
        return { t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 50),
          aria: b.getAttribute('aria-label'),
          rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
          area: Math.round(q.width * q.height),
          cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2) };
      }).filter((x) => x.area > 0 && (x.t || x.aria)) }; })
  .filter((m) => m.rect[2] > 60 && m.rect[3] > 20));
const diff = (a, b) => b.filter((n) => !a.some((o) => o.rect.join() === n.rect.join() && o.text === n.text));

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await beginBatch(B, { note: '先 dump 底栏整排按钮再定位「+」，工具箱卡片只读' });

  // ① 底栏整排按钮，带坐标 —— 先看清楚再点
  const bar = await page.evaluate(() => {
    const out = [];
    for (const b of document.querySelectorAll('button,[role="button"]')) {
      const r = b.getBoundingClientRect();
      if (r.width < 8 || r.height < 8) continue;
      if (r.y < 700 || r.y > 810) continue;
      out.push({ t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24),
        aria: b.getAttribute('aria-label'), title: b.getAttribute('title'),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
        childSvg: !!b.querySelector('svg') });
    }
    return out.sort((a, b) => a.cx - b.cx);
  });
  console.log('AS5 底栏按钮:', JSON.stringify(bar));

  // ② 「+」= 底栏**最靠左**、有 svg 图标、没有任何文字/aria/title 的那枚
  const plus = bar.find((b) => !b.t && !b.aria && !b.title && b.childSvg) || null;
  const out = { bar, plus };
  if (!plus) throw new Error('底栏里找不到无文字的图标按钮');

  const f0 = await floats();
  await page.mouse.click(plus.cx, plus.cy);
  await page.waitForTimeout(2400);
  const f1 = await floats();
  out.panel = diff(f0, f1).find((n) => !n.isModal) || diff(f0, f1)[0] || null;
  await shot(page, 'M-127-添加节点面板.png');
  console.log('AS5 面板:', JSON.stringify(out.panel).slice(0, 1100));

  // ③ 悬停「素材库」出子菜单
  const lib = (out.panel?.items || []).find((i) => i.t === '素材库');
  out.libItem = lib || null;
  if (lib) {
    const f2 = await floats();
    for (const [dx, dy] of [[0, 0], [2, 0], [0, 2], [1, 1]]) {
      await page.mouse.move(lib.cx + dx, lib.cy + dy); await page.waitForTimeout(1300);
    }
    const f3 = await floats();
    out.submenu = diff(f2, f3).find((n) => !n.isModal) || null;
    out.submenuAll = diff(f2, f3);
    await shot(page, 'M-128-素材库子菜单.png');
    console.log('AS5 子菜单:', JSON.stringify(out.submenu).slice(0, 1100));
  } else {
    out.libErr = '面板里没有「素材库」；items = ' + JSON.stringify((out.panel?.items || []).map((i) => i.t || i.aria));
  }

  // ④ 「打开工具箱」
  const tb = (out.submenu?.items || []).find((i) => /工具箱/.test((i.t || '') + (i.aria || '')));
  out.toolboxBtn = tb || null;
  if (tb) {
    await page.mouse.click(tb.cx, tb.cy);
    await page.waitForTimeout(3200);
    await shot(page, 'M-129-工具箱弹窗.png');
    const f4 = await floats();
    out.dialog = f4.find((n) => n.isModal) || null;
    out.dialogButtons = out.dialog ? out.dialog.items.map((i) => ({ t: i.t, aria: i.aria, rect: i.rect })) : null;
    console.log('AS5 工具箱弹窗:', JSON.stringify(out.dialog).slice(0, 2000));
    console.log('AS5 弹窗按钮:', JSON.stringify(out.dialogButtons).slice(0, 1200));
  } else {
    out.toolboxErr = '子菜单里没有工具箱项；items = ' + JSON.stringify((out.submenu?.items || []).map((i) => i.t || i.aria));
  }

  await logStep(B, {
    id: 'AS5-plus-and-toolbox', title: '底栏整排按钮 dump + 「+」→ 素材库 → 工具箱（卡片只读）',
    target: '先把底栏每一枚按钮的坐标打出来再定位「+」，不靠猜；工具箱弹窗里**只读按钮文案与坐标，不点**',
    evidence: out,
    visible_text: `底栏按钮（按 x 排序）：${JSON.stringify(bar)}。`
      + `\n\n添加节点面板：${JSON.stringify(out.panel).slice(0, 700)}。`
      + `\n\n素材库子菜单：${JSON.stringify(out.submenu).slice(0, 600)}。`
      + `\n\n工具箱弹窗：${JSON.stringify(out.dialog).slice(0, 900)}`,
    shot: 'M-127-添加节点面板.png',
  });
  console.log('AS5 完成');
} finally {
  await browser.close();
}
