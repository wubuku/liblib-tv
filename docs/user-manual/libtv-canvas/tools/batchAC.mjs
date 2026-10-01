// Batch AC —— batchAB 的截图里出现了一个必须查清楚的现象：
//
// TV Director 对话抽屉底部的输入区里，**并排出现了两个一模一样、写着「图片节点 1」的附件 chip**。
// 脚本只点了一次「添加到Agent」，画布上只有 1 个节点。
//
// 两种可能，手册的写法完全不同：
//   (a) 产品把同一个节点重复挂载了两次（真 bug，值得写进排障）
//   (b) 两个 chip 语义不同 —— 比如一个是节点、一个是节点的某个引用对象，
//       只是渲染出来长得一样（那就得说清楚各自是什么）
//
// 判据：把 chip 逐个 dump 出来 —— class、位置、title、里面有没有删除按钮、
// 以及有没有 data-* / aria 能区分。**不点任何删除按钮，不点 Send。**
//
// 顺带补两件 batchAB 没答完的：
//   · 输入框是空的（编辑器 innerText 为空）还是被填了字？
//     —— AB 查的 `.ChatRichInput-editor` 命中了一个 x=726 的**别的**编辑器（在面板外），
//        所以 editorText="" 是查错了对象。这次改成**只在右抽屉里面找**。
//   · Send 按钮在只有附件、没有正文时是不是可点。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchAC';
const { browser, page } = await launch();

const N = () => nodeCount(page);
/** 右侧那张抽屉（x > 500），不是左边资产管理那张。 */
const rightPanel = () => page.evaluate(() => {
  const p = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
    .find((x) => x.getBoundingClientRect().x > 500);
  if (!p) return null;
  const r = p.getBoundingClientRect();
  return { x: r.x, el: p, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
});
const opener = page.locator('[data-academy-guide-anchor="workspace-asset-management"]');
const openDrawer = async () => {
  if (await page.evaluate(() => !!document.querySelector('div.group\\/node'))) return true;
  await opener.first().click({ timeout: 6000 }); await page.waitForTimeout(2600);
  return await page.evaluate(() => !!document.querySelector('div.group\\/node'));
};
const openRowMenu = () => page.evaluate(() => {
  const row = document.querySelector('div.group\\/node');
  if (!row) return { err: '没有行' };
  const btn = [...row.querySelectorAll('button')].find((b) => b.getAttribute('aria-label') === '更多操作');
  if (!btn) return { err: '没有「更多操作」按钮' };
  const b = btn.getBoundingClientRect();
  return { cx: Math.round(b.x + b.width / 2), cy: Math.round(b.y + b.height / 2) };
});
const readMenu = () => page.evaluate(() => {
  const m = document.querySelector('[class*="mantine-Menu-dropdown"]');
  if (!m) return null;
  return [...m.querySelectorAll('button,[role="menuitem"],li,div')].filter((e) => {
    const r = e.getBoundingClientRect();
    return r.width > 40 && r.height > 16 && r.height < 46 && (e.innerText || '').trim().length <= 12 && !e.querySelector('div[style]');
  }).map((e) => { const r = e.getBoundingClientRect();
    return { t: (e.innerText || '').trim(), cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
    .filter((x, i, a) => a.findIndex((y) => y.t === x.t && y.cy === x.cy) === i);
});
const clickMenu = async (label) => {
  const m0 = await openRowMenu();
  if (m0.err) throw new Error(m0.err);
  await page.mouse.click(m0.cx, m0.cy); await page.waitForTimeout(1800);
  const menu = await readMenu();
  const it = menu?.find((i) => i.t === label);
  if (!it) throw new Error(`菜单里没有「${label}」；读到 ${JSON.stringify(menu?.map((i) => i.t))}`);
  await page.mouse.click(it.cx, it.cy);
  return it;
};

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '坐实「添加到Agent」是不是真的挂了重复附件；补正文框与 Send 状态' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  let placed = false;
  for (const [x, y] of [[560, 340], [560, 430], [560, 250]]) {
    await page.mouse.dblclick(x, y); await page.waitForTimeout(1100);
    const it = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
      .getByText('图片', { exact: false }).first();
    if (await it.count().catch(() => 0)) { await it.click({ timeout: 4000 }).catch(() => {}); await page.waitForTimeout(2400); }
    if (await N() > 0) { placed = true; break; }
    await page.keyboard.press('Escape').catch(() => {});
  }
  if (!placed) throw new Error('节点没建起来');
  await fitView(page, 1); await page.waitForTimeout(1200);

  // 点一次「添加到Agent」，记下点击次数这个变量本身
  const clickCount = 1;
  if (!(await openDrawer())) throw new Error('抽屉打不开');
  const n0 = await N();
  await clickMenu('添加到Agent');
  await page.waitForTimeout(3200);

  const chipProbe = await page.evaluate(() => {
    const p = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
      .find((x) => x.getBoundingClientRect().x > 500);
    if (!p) return { err: '右抽屉不在' };
    // 找所有「叶子节点里带图片图标 + 节点名」的小胶囊：
    // 判据是元素内文本恰好等于节点名，且没有再包含同名的子元素
    const leaves = [...p.querySelectorAll('*')].filter((e) => {
      const t = (e.innerText || '').trim();
      if (t !== '图片节点 1') return false;
      return ![...e.children].some((c) => (c.innerText || '').trim() === '图片节点 1');
    });
    // 编辑器：这次**只在右抽屉里**找
    const ed = p.querySelector('.ChatRichInput-editor,[contenteditable="true"]');
    const edB = ed ? ed.getBoundingClientRect() : null;
    const send = [...p.querySelectorAll('button')].find((b) => b.getAttribute('aria-label') === 'Send');
    return {
      chipCount: leaves.length,
      chips: leaves.map((e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
        return { tag: e.tagName, cls: (e.className || '').toString().slice(0, 70),
          title: e.getAttribute('title'), aria: e.getAttribute('aria-label'),
          dataAttrs: [...e.attributes].filter((a) => a.name.startsWith('data-')).map((a) => `${a.name}=${a.value}`).slice(0, 6),
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          html: (e.innerHTML || '').slice(0, 260),
          hasRemoveBtn: !!e.querySelector('button,[aria-label*="移除"],[aria-label*="删除"],[aria-label*="Remove"],[aria-label*="close"]'),
          textColor: cs.color, bg: cs.backgroundColor }; }),
      editorFound: !!ed,
      editorRect: edB ? [Math.round(edB.x), Math.round(edB.y), Math.round(edB.width), Math.round(edB.height)] : null,
      editorText: ed ? (ed.innerText || '').replace(/\s+/g, ' ').trim() : null,
      editorPlaceholder: ed ? ed.getAttribute('data-placeholder') || ed.getAttribute('placeholder') : null,
      sendFound: !!send,
      sendDisabled: send ? (send.disabled === true || getComputedStyle(send).opacity < 0.45) : null,
      sendAria: send ? send.getAttribute('aria-label') : null,
      bottomBar: [...p.querySelectorAll('button')].slice(-6).map((b) => ({
        t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16), aria: b.getAttribute('aria-label'), title: b.getAttribute('title') })),
    };
  });
  await shot(page, 'M-54-添加到Agent-附件逐个看.png');
  console.log('AC:', JSON.stringify(chipProbe, null, 1).slice(0, 2600));
  await logStep(B, { id: 'AC1-chip-duplicate', title: '「添加到Agent」挂了几个附件：重复 chip 的成因',
    target: `点一次「⋯ → 添加到Agent」，然后把右抽屉里所有文本恰为节点名、且不含同名子元素的元素全 dump 出来`,
    evidence: { clickCount, nodeCountBefore: n0, nodeCountAfter: await N(), chipProbe },
    visible_text: `画布上 **${n0} 个**节点，只点了 **${clickCount} 次**「添加到Agent」。` +
      `右抽屉输入区里文本恰为「图片节点 1」的最内层元素共 **${chipProbe.chipCount} 个**：${JSON.stringify(chipProbe.chips)}。` +
      (chipProbe.chipCount > 1
        ? `→ 两个 chip 的 class ${chipProbe.chips.map((c) => c.cls)}、位置 ${chipProbe.chips.map((c) => c.rect)}。` +
          `**两者 innerHTML 完全一致：${chipProbe.chips[0].html === chipProbe.chips[1]?.html ? '是' : '否'}**，` +
          `data-* 属性 ${JSON.stringify(chipProbe.chips.map((c) => c.dataAttrs))} —— ` +
          `**同一个节点被重复挂载了两次（重复附件）**。`
        : `→ 只挂了一个，正常。`) +
      `正文编辑区：${chipProbe.editorFound ? `找到，内容 ${JSON.stringify(chipProbe.editorText)}（**是空的，节点是以附件形式进来的，不是正文**）` : '没找到'}；` +
      `Send 按钮：${chipProbe.sendFound ? `存在，禁用=${chipProbe.sendDisabled}` : '没找到'}；` +
      `底栏按钮 ${JSON.stringify(chipProbe.bottomBar)}`,
    shot: 'M-54-添加到Agent-附件逐个看.png' });

  console.log('收尾节点:', await N());
} finally {
  await browser.close();
}
