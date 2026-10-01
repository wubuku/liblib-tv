// Batch AK —— 补救 batchAJ。
//
// AJ 扑空的原因：**列检测器是我自己写的最脆的一环**。
// 它按「宽度 380~620 + 高度 >300 + 文本以 文本/图片/视频 开头 + 没有同类子元素」去筛，
// 结果 `colCount: 0` —— 三列明明在（底部状态条文本把「文本 图片 视频 全部 对话」全读出来了）。
//
// 而且这轮暴露了一件更要紧的事：**切到故事板时 TV Director 面板自动弹出，
// 正好压住视频列的右半边**（batchT 已经发现过这个连带效应，这回它直接挡住了要点的按钮）。
//
// 所以这一轮：
//   1. 先把 TV Director 面板收掉（点它自己的「—」，不按 Esc —— Esc 会连带改别的东西）
//   2. 不再猜 class，直接**按文字全页搜按钮**，记下每一枚的坐标和所在列
//   3. 「对话」按钮在 M-87 截图里**看不见**但 innerText 里有 → 怀疑要 hover 才现形，
//      所以逐个节点行悬停后再搜一遍
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchAK';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodeList = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 10),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}));
/** 全页找按钮，按文字或 aria 匹配；顺带报它落在哪一列（按 x 归属）。 */
const findBtns = (label) => page.evaluate((lb) => [...document.querySelectorAll('button,[role="button"],[role="tab"],[role="menuitem"]')]
  .map((b) => { const r = b.getBoundingClientRect();
    const t = (b.innerText || '').replace(/\s+/g, ' ').trim();
    const aria = b.getAttribute('aria-label');
    return { t, aria, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
      visible: r.width > 0 && r.height > 0 && getComputedStyle(b).opacity > 0.05,
      inTv: !!b.closest('.mantine-Drawer-content'),
      covered: (() => { const top = document.elementFromPoint(Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2));
        return top ? !b.contains(top) && top !== b : false; })() }; })
  .filter((b) => b.t === lb || b.aria === lb), label);
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
/** 收掉 TV Director 面板：点它标题栏右侧那枚「—」，不按 Esc。 */
async function collapseTv() {
  const btn = await page.evaluate(() => {
    const p = document.querySelector('.mantine-Drawer-inner,[class*="mantine-Drawer-content"]');
    if (!p || p.getBoundingClientRect().x < 500) return null;
    const e = [...p.querySelectorAll('button')].find((b) => {
      const t = (b.innerText || '').replace(/\s+/g, ' ').trim();
      return t === '—' || t === '−' || /最小化|收起/.test(b.getAttribute('aria-label') || '');
    });
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2), t: (e.innerText || '').trim() };
  });
  if (!btn) return null;
  await page.mouse.click(btn.cx, btn.cy); await page.waitForTimeout(1600);
  const still = await page.evaluate(() => {
    const p = document.querySelector('.mantine-Drawer-inner,[class*="mantine-Drawer-content"]');
    return !p || p.getBoundingClientRect().x < 500;
  });
  return { btn, collapsed: still };
}
async function freeSpot() {
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(450);
  const ns = await nodeList();
  if (!ns.length) return [760, 320];
  const right = Math.max(...ns.map((n) => n.rect[0] + n.rect[2]));
  const bottom = Math.max(...ns.map((n) => n.rect[1] + n.rect[3]));
  for (const [x, y] of [[Math.min(right + 360, 1370), 260], [Math.min(right + 360, 1370), 540],
    [700, Math.min(bottom + 280, 720)], [1150, Math.min(bottom + 280, 720)], [430, Math.min(bottom + 280, 720)]]) {
    if (!ns.some((n) => x > n.rect[0] - 40 && x < n.rect[0] + n.rect[2] + 40 && y > n.rect[1] - 40 && y < n.rect[1] + n.rect[3] + 40)
        && x > 400 && y > 140 && y < 740) return [x, y];
  }
  return null;
}
async function addNode(item) {
  for (let r = 0; r < 3; r += 1) {
    const spot = await freeSpot();
    if (!spot) return false;
    await page.mouse.dblclick(spot[0], spot[1]); await page.waitForTimeout(1100);
    const it = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
      .getByText(item, { exact: false }).first();
    if (await it.count().catch(() => 0)) {
      const b = await N();
      await it.click({ timeout: 4000 }).catch(() => {}); await page.waitForTimeout(2300);
      if (await N() > b) return true;
    }
    await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(700);
  }
  return false;
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '先收 TV 面板，再按文字全页搜「全部」「对话」' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  for (const item of ['文本', '图片', '视频']) console.log(`建 ${item}:`, await addNode(item), await N());
  await page.getByRole('button', { name: '故事板', exact: true }).first().click({ timeout: 6000 });
  await page.waitForTimeout(3200);

  const tvBefore = await page.evaluate(() => {
    const p = document.querySelector('.mantine-Drawer-inner,[class*="mantine-Drawer-content"]');
    return p ? { x: Math.round(p.getBoundingClientRect().x), w: Math.round(p.getBoundingClientRect().width) } : null; });
  const collapse = await collapseTv();
  await shot(page, 'M-91-故事板-收掉TV面板之后.png');
  const all = await findBtns('全部');
  const talkBefore = await findBtns('对话');
  console.log('AK0:', JSON.stringify({ tvBefore, collapse, all, talkBefore }).slice(0, 1500));

  // 悬停到节点行上再看一次「对话」出不出现
  let hovered = null;
  if (!talkBefore.length) {
    const rows = await page.evaluate(() => [...document.querySelectorAll('*')]
      .filter((e) => { const r = e.getBoundingClientRect(); const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
        return /^节点 \d+$|^(文本|图片|视频)节点 \d+$/.test(t) && r.y > 90 && r.y < 300 && r.width > 40 && r.height > 14
          && ![...e.children].some((c) => /节点 \d+$/.test((c.innerText || '').trim())); })
      .map((e) => { const r = e.getBoundingClientRect();
        return { t: (e.innerText || '').trim(), cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }));
    for (const row of rows) {
      await page.mouse.move(row.cx, row.cy); await page.waitForTimeout(900);
      const found = await findBtns('对话');
      if (found.length) { hovered = { row: row.t, found }; break; }
    }
    await shot(page, 'M-92-故事板-悬停节点行.png');
  }
  console.log('AK-hover:', JSON.stringify(hovered).slice(0, 900));

  // ── AK1 「全部」筛选
  try {
    const btn = all[0];
    if (!btn) throw new Error('全页没有「全部」按钮');
    await page.mouse.click(btn.cx, btn.cy); await page.waitForTimeout(1900);
    const pop = await floating();
    await shot(page, 'M-93-故事板-全部筛选下拉.png');
    let picked = null;
    const opt = pop?.[0]?.items?.find((i) => i.t && i.t !== '全部');
    if (opt) {
      await page.mouse.click(opt.cx, opt.cy); await page.waitForTimeout(1900);
      const after = await findBtns('全部');
      const colText = await page.evaluate(() => {
        const e = [...document.querySelectorAll('*')].find((x) => /视频节点 \d+/.test((x.innerText || '').replace(/\s+/g, ' ')));
        return e ? (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160) : null; });
      picked = { opt: opt.t, btnAfter: after.map((b) => b.t || b.aria), colText };
      await shot(page, 'M-94-故事板-筛选选中之后.png');
    }
    await logStep(B, { id: 'AK1-board-filter', title: '故事板「全部」筛选里有什么、选了之后怎么变',
      target: `切到故事板并收掉 TV Director 面板后，点 (${btn.cx},${btn.cy}) 的「全部」按钮`,
      evidence: { tvBefore, collapse, btn, pop, picked },
      visible_text: `切到故事板时 TV Director 面板在 ${JSON.stringify(tvBefore)}；点它自己的「${collapse?.btn?.t}」把它收掉：${JSON.stringify(collapse)}。` +
        `「全部」按钮位置 ${JSON.stringify(btn.rect)}（被遮挡：${btn.covered}）。点开后浮层 ${JSON.stringify(pop)}。` +
        (picked ? `选「${picked.opt}」之后：按钮文案变成 ${JSON.stringify(picked.btnAfter)}，视频列附近文案「${picked.colText}」。`
          : '**没有可点的选项。**'),
      shot: 'M-93-故事板-全部筛选下拉.png' });
    console.log('AK1:', JSON.stringify({ pop, picked }).slice(0, 1800));
  } catch (e) { await logStep(B, { id: 'AK1-board-filter', title: '故事板「全部」筛选', failed: true, visible_text: String(e).slice(0, 300) }); console.log('AK1 失败', String(e).slice(0, 250)); }

  // ── AK2 「对话」按钮
  try {
    const talk = talkBefore[0] || hovered?.found?.[0];
    if (!talk) throw new Error('找不到「对话」按钮（悬停也没试出来）');
    const nBefore = await N();
    await page.mouse.click(talk.cx, talk.cy); await page.waitForTimeout(2800);
    const detail = await page.evaluate(() => {
      const panel = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')].find((x) => x.getBoundingClientRect().x > 500);
      const buttons = panel ? [...panel.querySelectorAll('button')].map((x) => ({
        t: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), aria: x.getAttribute('aria-label'),
        disabled: x.disabled === true || getComputedStyle(x).opacity < 0.45 })) : [];
      const ed = panel?.querySelector('.ChatRichInput-editor,[contenteditable="true"]');
      return {
        panelFound: !!panel,
        panelText: panel ? (panel.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300) : null,
        buttons: buttons.slice(0, 22),
        danger: buttons.filter((x) => /发送|提交|派发|运行|开始生成|消耗|Send/.test(`${x.t}${x.aria || ''}`)),
        stillWelcome: !!document.querySelector('.chat-welcome-root'),
        editor: ed ? { text: (ed.innerText || '').replace(/\s+/g, ' ').trim(),
          rect: [Math.round(ed.getBoundingClientRect().x), Math.round(ed.getBoundingClientRect().y),
            Math.round(ed.getBoundingClientRect().width), Math.round(ed.getBoundingClientRect().height)] } : null,
      };
    });
    await shot(page, 'M-95-故事板-点对话之后.png');
    await logStep(B, { id: 'AK2-board-dialog', title: '故事板节点上的「对话」点开是什么',
      target: `点 (${talk.cx},${talk.cy}) 的「对话」按钮，之后**只读 DOM，一个发送控件都没点**`,
      evidence: { talk, talkBefore, hovered, nodeCountBefore: nBefore, nodeCountAfter: await N(), detail },
      visible_text: `全页按文字搜到「对话」按钮 ${talkBefore.length} 枚 ${JSON.stringify(talkBefore)}；` +
        `悬停节点行后 ${hovered ? `出现了：${JSON.stringify(hovered)}` : '**仍然没出现**'}。` +
        `点之前画布 ${nBefore} 个节点，点之后 ${await N()} 个。` +
        `右侧面板 ${detail.panelFound ? '出现' : '没出现'}，文案「${(detail.panelText || '').slice(0, 200)}」；` +
        `按钮 ${JSON.stringify(detail.buttons.map((x) => x.t || x.aria))}；` +
        `**发送类 ${JSON.stringify(detail.danger)}${detail.danger.length ? '（已停手）' : ''}**；` +
        `输入区 ${JSON.stringify(detail.editor)}；仍停在欢迎页：${detail.stillWelcome}`,
      shot: 'M-95-故事板-点对话之后.png' });
    console.log('AK2:', JSON.stringify(detail).slice(0, 2000));
  } catch (e) { await logStep(B, { id: 'AK2-board-dialog', title: '故事板「对话」按钮', failed: true, visible_text: String(e).slice(0, 300) }); console.log('AK2 失败', String(e).slice(0, 250)); }

  console.log('收尾节点:', await N());
} finally {
  await browser.close();
}
