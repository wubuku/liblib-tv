// 画布通用操作：清空、选中、拖拽、连线。
//
// 「清空」是 Batch B 能反复重跑的前提。第一版 batchB 就是因为上一轮残留的节点
// 留在画布上，导致「空画布双击」之类的取证全都不在预期状态上。
import { fingerprint, diffPanels } from './scenario.mjs';

export const NODE_SEL = '.react-flow__node';

export async function nodeCount(page) {
  return page.locator(NODE_SEL).count();
}

/** 列出画布上所有节点的第一行文字，用来判断「画布是不是干净的」。 */
export async function listNodes(page) {
  return page.evaluate(() =>
    [...document.querySelectorAll('.react-flow__node')].map((n) => {
      const r = n.getBoundingClientRect();
      return {
        id: n.getAttribute('data-id'),
        title: (n.innerText || '').replace(/\s+/g, ' ').slice(0, 40),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        selected: n.classList.contains('selected') || n.getAttribute('aria-selected') === 'true',
      };
    }),
  );
}

/**
 * 建完节点后按 ⌘0「适应画布」，让整个节点进入视口。
 *
 * 为什么必须做：节点是按点击落点放置的，而且图片/视频节点本身就很大，
 * 默认 100% 缩放下大半张卡片在视口外 —— 那样截出来的图没法当正文插图用
 * （第一版 B-n2-图片 就只拍到节点上半截）。
 */
export async function fitView(page, times = 1) {
  for (let i = 0; i < times; i += 1) {
    await page.keyboard.press('Meta+0');
    await page.waitForTimeout(700);
  }
  return page.evaluate(() => {
    const vp = document.querySelector('.react-flow__viewport');
    return vp ? vp.style.transform : null;
  });
}

/**
 * 把画布恢复到空。
 *
 * 实测（探针 13）：**选中节点后单按 Delete / Backspace 都不删**（1 → 1）。
 * 真正有效的是「焦点在画布空白处 → ⌘A → Backspace」。
 * 而直接从节点里点完就 ⌘A 是不行的——焦点还在节点的 textarea/contenteditable 里，
 * ⌘A 选中的是节点内文字。所以顺序必须是：Esc → 点空白画布 → ⌘A → ⌫。
 */
export async function clearCanvas(page, maxRounds = 4) {
  const before = await nodeCount(page);
  for (let round = 0; round < maxRounds; round += 1) {
    if (!(await nodeCount(page))) break;
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(250);
    // 点一块绝对空白把焦点交回画布。
    // 注意别用 .react-flow__pane 的相对坐标点法：节点会落在面板锚点附近，
    // 相对 (60,60) 有时正好点在节点上，于是「点空白」其实点了节点，⌘A 又变成选中节点内文字。
    // 探针 13 证实有效的做法是绝对坐标点左上角空白。
    await page.mouse.click(180, 150);
    await page.waitForTimeout(300);
    await page.keyboard.press('Meta+A');
    await page.waitForTimeout(350);
    await page.keyboard.press('Backspace');
    await page.waitForTimeout(1300);
  }
  return { before, after: await nodeCount(page), removed: before - (await nodeCount(page)) };
}

/**
 * 打开「添加节点」面板并点中某一项，返回点中后的节点数变化。
 * panelItem 用面板内的精确文本定位，避免和空画布的快捷芯片（图片生成/音频生成…）混淆
 * ——上一版就是 /^音频/ 撞上了画布上的「音频生成」芯片，节点类型整个对不上。
 */
export async function addNode(page, itemText, { settle = 2200 } = {}) {
  const openBtn = page.getByRole('button', { name: '添加节点', exact: true }).first();
  await openBtn.click({ timeout: 6000 });
  await page.waitForTimeout(900);
  const panel = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first();
  const item = panel.getByText(itemText, { exact: false }).first();
  const n = await item.count();
  if (!n) {
    const all = await panel.locator('button').allInnerTexts();
    throw new Error(`面板里找不到「${itemText}」，面板现有项：${JSON.stringify(all)}`);
  }
  const before = await nodeCount(page);
  await item.click({ timeout: 6000 });
  await page.waitForTimeout(settle);
  return { before, after: await nodeCount(page) };
}

/** 读一个节点面板的全部可交互控件（建 20-reference 字段表用）。 */
export async function readNodeControls(page, index = 0) {
  return page.evaluate((i) => {
    const n = [...document.querySelectorAll('.react-flow__node')][i];
    if (!n) return { none: true };
    const pick = (el) => (el.getAttribute('aria-label') || el.getAttribute('placeholder') || (el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ')).slice(0, 40);
    return {
      text: (n.innerText || '').replace(/\s+/g, ' ').slice(0, 1500),
      buttons: [...n.querySelectorAll('button')].map(pick).filter(Boolean),
      inputs: [...n.querySelectorAll('input,textarea')].map((e) => ({ type: e.type, aria: e.getAttribute('aria-label'), ph: e.getAttribute('placeholder'), value: e.value, checked: e.checked })),
      roles: [...n.querySelectorAll('[role="combobox"],[role="listbox"],[role="radio"],[role="switch"],[role="slider"]')].map((e) => `${e.getAttribute('role')}:${pick(e)}`),
      ports: [...n.querySelectorAll('.react-flow__handle,[class*="handle"]')].map((h) => ({
        cls: (h.className || '').toString().replace(/[\w-]*css-\w+/g, '').slice(0, 70),
        type: h.getAttribute('data-handlepos') || h.getAttribute('data-nodeid') || null,
        pos: h.getAttribute('data-handlepos'),
      })),
      rect: (() => { const r = n.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })(),
    };
  }, index);
}

export { fingerprint, diffPanels };
