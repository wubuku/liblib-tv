// Batch AI —— 补最后一块：画布标签下 `筛选：全部` 这枚按钮。
//
// 前五轮把它漏掉的原因很典型：AE2 想找「那枚没有 aria-label 的匿名图标」，
// 用的是 `tb.buttons.find(b => !b.t && !known.test(b.aria))` ——
// 「known」里只列了 `搜索节点`/`展示设置`/`评级`，没列 `筛选：全部`，
// 于是 `.find()` 取到的第一个纯图标按钮是 `收起节点侧栏`（底部那枚收起箭头），
// 差之毫厘。
//
// AD0 其实早就把它的名字读出来了：**`筛选：全部`** —— aria-label 里带着当前档位。
// 这说明它和 `所有评级` 是**两个不同的筛选器**，点开就知道差在哪。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchAI';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodeList = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 10),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
}));
const drawerBox = () => page.evaluate(() => {
  const d = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
    .find((x) => { const r = x.getBoundingClientRect(); return r.width > 200 && r.height > 300 && r.x < 400; });
  return d ? { x: d.getBoundingClientRect().x } : null;
});
const opener = page.locator('[data-academy-guide-anchor="workspace-asset-management"]');
const openDrawer = async () => {
  const b = await drawerBox();
  if (b && b.x > -50) return true;
  await opener.first().click({ timeout: 6000 }); await page.waitForTimeout(2600);
  return (await drawerBox())?.x > -50;
};
const closeDrawer = async () => { await page.mouse.click(880, 110).catch(() => {}); await page.waitForTimeout(900); };
const rows = () => page.evaluate(() => [...document.querySelectorAll('div.group\\/node')]
  .map((r) => (r.innerText || '').replace(/\s+/g, ' ').trim()));
const drawerText = () => page.evaluate(() => {
  const d = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
    .find((x) => { const r = x.getBoundingClientRect(); return r.width > 200 && r.height > 300 && r.x < 400; });
  return d ? (d.innerText || '').replace(/\s+/g, ' ').trim() : null;
});
const btnBy = (aria) => page.evaluate((a) => {
  const d = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
    .find((x) => { const r = x.getBoundingClientRect(); return r.width > 200 && r.height > 300 && r.x < 400; });
  const e = d && [...d.querySelectorAll('button')].find((b) => b.getAttribute('aria-label') === a);
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return { t: (e.innerText || '').replace(/\s+/g, ' ').trim(), cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
    w: Math.round(r.width), h: Math.round(r.height), html: (e.innerHTML || '').slice(0, 80) };
}, aria);
const floating = () => page.evaluate(() => [...document.querySelectorAll('[class*="Menu-dropdown"],[class*="Popover-dropdown"],[class*="Dropdown-dropdown"]')]
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 40 && r.height > 12; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { cls: (e.className || '').toString().slice(0, 36), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 260),
      items: [...e.querySelectorAll('[role="menuitem"],[role="option"],button,li,label,div')].filter((c) => {
        const cr = c.getBoundingClientRect();
        return cr.width > 24 && cr.height > 8 && cr.height < 46 && (c.innerText || '').trim().length <= 24 && !c.querySelector('div[style]');
      }).map((c) => { const cr = c.getBoundingClientRect();
        return { t: (c.innerText || '').trim(), cx: Math.round(cr.x + cr.width / 2), cy: Math.round(cr.y + cr.height / 2) }; })
        .filter((x, i, a) => a.findIndex((y) => y.t === x.t && y.cy === x.cy) === i) }; }));
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
  await beginBatch(B, { note: '画布标签「筛选：全部」点开是什么' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  for (const item of ['图片', '音频', '文本']) console.log(`建 ${item}:`, await addNode(item), await N());
  closeDrawer();

  if (!(await openDrawer())) throw new Error('抽屉打不开');
  const before = { rows: await rows(), text: await drawerText() };
  const btn = await btnBy('筛选：全部');
  if (!btn) {
    // aria 里的档位可能不是「全部」，先按前缀找
    const alt = await page.evaluate(() => {
      const d = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
        .find((x) => { const r = x.getBoundingClientRect(); return r.width > 200 && r.height > 300 && r.x < 400; });
      const e = d && [...d.querySelectorAll('button')].find((b) => /^筛选/.test(b.getAttribute('aria-label') || ''));
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
    });
    if (!alt) throw new Error('画布标签下找不到「筛选：…」按钮');
    var pick = alt;
  } else { var pick = { aria: '筛选：全部', cx: btn.cx, cy: btn.cy, w: btn.w, h: btn.h }; }

  await page.mouse.click(pick.cx, pick.cy); await page.waitForTimeout(1800);
  const pop = await floating();
  await shot(page, 'M-85-筛选-全部-点开.png');
  const items = pop?.[0]?.items || [];
  let picked = null;
  const opt = items.find((i) => i.t && i.t !== (pick.aria || '').replace('筛选：', ''));
  if (opt) {
    const r0 = await rows();
    await page.mouse.click(opt.cx, opt.cy); await page.waitForTimeout(1800);
    const r1 = await rows();
    const afterBtn = await page.evaluate(() => {
      const d = [...document.querySelectorAll('[class*="mantine-Drawer-content"]')]
        .find((x) => { const r = x.getBoundingClientRect(); return r.width > 200 && r.height > 300 && r.x < 400; });
      const e = d && [...d.querySelectorAll('button')].find((b) => /^筛选/.test(b.getAttribute('aria-label') || ''));
      return e ? e.getAttribute('aria-label') : null;
    });
    picked = { opt: opt.t, before: r0, after: r1, ariaAfter: afterBtn };
    await shot(page, 'M-86-筛选-选中之后.png');
  }
  await logStep(B, { id: 'AI1-canvas-filter', title: '画布标签的「筛选：…」和「所有评级」是两个不同的筛选器',
    target: `点 aria-label=${JSON.stringify(pick.aria)} 的按钮 (${pick.cx},${pick.cy})，读浮层并选一项`,
    evidence: { before, btn, pick, pop, picked },
    visible_text: `画布上 ${await N()} 个节点，列表 ${JSON.stringify(before.rows)}。` +
      `这枚按钮的 aria-label 是 **${JSON.stringify(pick.aria)}** —— **档位直接写进 aria-label 里**，所以它和右边那枚文案可见的「所有评级」是两个独立控件。` +
      `点开后浮层 ${JSON.stringify(pop)}。` +
      (picked ? `选「${picked.opt}」：列表 ${picked.before.length} 行 → ${picked.after.length} 行 ${JSON.stringify(picked.after)}，按钮 aria 变成 **${JSON.stringify(picked.ariaAfter)}**。`
        : '没有可点的选项。'),
    shot: 'M-85-筛选-全部-点开.png' });
  console.log('AI1:', JSON.stringify({ pick, pop, picked }).slice(0, 2200));

  console.log('收尾节点:', await N());
} finally {
  await browser.close();
}
