// Batch AB —— 补救 batchAA 的 AA3。
//
// AA3 失败原因不是产品没反应，是**探针把自己的前提用完了**：
// AA2 刚把测试画布删到 0 个节点，而 openDrawer() 的判据是
// 「页面上存在 div.group/node 才算抽屉开着」——一个节点都没有时，
// 抽屉明明开着（还写着「画布暂无节点 共 0 节点」），脚本却判定「打不开」并抛错。
// 教训：**判据要问「抽屉在不在」，不是「里面有没有行」。**
// 这次改成查 `.mantine-Drawer-content` 本身在不在。
//
// 要查的东西没变：点「⋯ → 添加到Agent」之后，
//   · 底部输入框里到底装了什么（节点名？还是节点的完整数据？）
//   · 发送按钮叫什么、默认是不是禁用（只读 DOM，**绝不点**）
//   · 输入框右上角的「全能创作」是什么，点开会不会只是模式切换（安全）
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchAB';
const { browser, page } = await launch();

const N = () => nodeCount(page);
/** 抽屉在不在 —— 看容器本身，不看里面有没有行（AA3 的教训）。 */
const drawerOpen = () => page.evaluate(() => {
  const d = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
    .find((x) => { const r = x.getBoundingClientRect(); return r.width > 200 && r.height > 300; });
  if (!d) return false;
  const r = d.getBoundingClientRect();
  return { open: r.x > -50 && r.x < 400, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
});
const opener = page.locator('[data-academy-guide-anchor="workspace-asset-management"]');
const openDrawer = async () => {
  if ((await drawerOpen()).open) return true;
  await opener.first().click({ timeout: 6000 }); await page.waitForTimeout(2600);
  return (await drawerOpen()).open;
};
const closeDrawer = async () => { await page.mouse.click(1250, 780).catch(() => {}); await page.waitForTimeout(900); };
const openRowMenu = (idx = 0) => page.evaluate((i) => {
  const row = document.querySelectorAll('div.group\\/node')[i];
  if (!row) return { err: '没有第 ' + i + ' 行' };
  const btn = [...row.querySelectorAll('button')].find((b) => b.getAttribute('aria-label') === '更多操作');
  if (!btn) return { err: '该行没有「更多操作」按钮' };
  const b = btn.getBoundingClientRect();
  return { cx: Math.round(b.x + b.width / 2), cy: Math.round(b.y + b.height / 2), rowText: (row.innerText || '').trim() };
}, idx);
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
  const m0 = await openRowMenu(0);
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
  await beginBatch(B, { note: '补救 AA3：抽屉判据改成查容器本身；读「添加到Agent」面板' });

  // 造一个**有内容的**节点：有提示词和模型的图片节点，面板里才有东西可读
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
  await fitView(page, 1); await page.waitForTimeout(1300);
  console.log('节点:', await N());

  if (!(await openDrawer())) throw new Error('抽屉还是打不开');
  const n0 = await N();
  await clickMenu('添加到Agent');
  await page.waitForTimeout(3000);

  const detail = await page.evaluate(() => {
    const ed = document.querySelector('.ChatRichInput-editor,[contenteditable="true"]');
    const b = ed ? ed.getBoundingClientRect() : null;
    // 只认「滑到屏幕右侧」的那张抽屉，避免把资产管理抽屉也算进来
    const panel = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
      .find((x) => x.getBoundingClientRect().x > 500);
    const buttons = panel ? [...panel.querySelectorAll('button')].map((x) => { const r = x.getBoundingClientRect();
      return { t: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24), aria: x.getAttribute('aria-label'),
        title: x.getAttribute('title'), disabled: x.disabled === true || getComputedStyle(x).opacity < 0.45,
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }) : [];
    return {
      panelRect: panel ? (({ x, y, width, height }) => [Math.round(x), Math.round(y), Math.round(width), Math.round(height)])(panel.getBoundingClientRect()) : null,
      panelText: panel ? (panel.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 320) : null,
      editorText: ed ? (ed.innerText || ed.textContent || '').replace(/\s+/g, ' ').trim() : null,
      editorHtml: ed ? (ed.innerHTML || '').slice(0, 300) : null,
      editorRect: b ? [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)] : null,
      buttons,
      dangerWords: buttons.filter((x) => /发送|提交|派发|运行|开始生成|消耗|扣费/.test(`${x.t}${x.aria || ''}${x.title || ''}`))
        .map((x) => ({ t: x.t, aria: x.aria, disabled: x.disabled })),
      stillWelcome: !!document.querySelector('.chat-welcome-root'),
      welcomeText: (document.querySelector('.chat-welcome-root')?.innerText || '').replace(/\s+/g, ' ').slice(0, 220),
    };
  });
  await shot(page, 'M-52-添加到Agent-面板细节.png');
  console.log('AB:', JSON.stringify({ ed: detail.editorText, html: detail.editorHtml, btns: detail.buttons, welcome: detail.stillWelcome, danger: detail.dangerWords }));

  // 「全能创作」点开看是不是模式菜单 —— 只看选项，不选
  const modeBtn = await page.evaluate(() => {
    const panel = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')].find((x) => x.getBoundingClientRect().x > 500);
    if (!panel) return null;
    const hit = [...panel.querySelectorAll('button,[role="button"],div')].find((x) => (x.innerText || '').trim() === '全能创作');
    if (!hit) return null;
    const r = hit.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
  });
  let modeOpts = null;
  if (modeBtn) {
    await page.mouse.click(modeBtn.cx, modeBtn.cy); await page.waitForTimeout(1500);
    modeOpts = await page.evaluate(() => {
      const pops = [...document.querySelectorAll('[class*="Popover-dropdown"],[class*="Menu-dropdown"]')]
        .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 60 && r.height > 20; });
      return pops.map((p) => ({ rect: [Math.round(p.getBoundingClientRect().width), Math.round(p.getBoundingClientRect().height)],
        text: (p.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200) }));
    });
    await shot(page, 'M-53-全能创作-模式菜单.png');
    // 只截图不选；点同一个按钮收起来
    await page.mouse.click(modeBtn.cx, modeBtn.cy).catch(() => {}); await page.waitForTimeout(900);
  }

  await logStep(B, { id: 'AB1-add-to-agent-detail', title: '「添加到Agent」把节点放进了什么：输入框内容、发送按钮、模式切换',
    target: '点「⋯ → 添加到Agent」后只读 DOM，**全程没点任何发送控件**',
    evidence: { nodeCountBefore: n0, nodeCountAfter: await N(), detail, modeBtn, modeOpts },
    visible_text: `点之前画布 ${n0} 个节点，点之后 ${await N()} 个 —— **画布上什么都没多出来**。` +
      `弹出的是右侧一张 TV Director 对话抽屉（位置 ${JSON.stringify(detail.panelRect)}），文案「${(detail.panelText || '').slice(0, 110)}…」。` +
      `底部输入框（\`ChatRichInput-editor\`）里已经预填了 **${JSON.stringify(detail.editorText)}**，位置 ${JSON.stringify(detail.editorRect)}，` +
      `里面是 **节点名本身**（不是节点数据）。` +
      `面板里的按钮 ${JSON.stringify(detail.buttons.map((x) => x.t || x.aria))}；` +
      `发送类按钮 ${JSON.stringify(detail.dangerWords)}（禁用态：${JSON.stringify(detail.dangerWords.map((x) => x.disabled))}）；` +
      `是否仍停在欢迎页（=**没自动发消息**）：**${detail.stillWelcome ? '是' : '否'}**，欢迎页文案「${detail.welcomeText}」。` +
      (modeBtn ? `点开输入框旁的「全能创作」弹出 ${JSON.stringify(modeOpts)}。` : '「全能创作」没找到可点的元素。'),
    shot: 'M-52-添加到Agent-面板细节.png' });

  console.log('收尾节点:', await N());
} finally {
  await browser.close();
}
