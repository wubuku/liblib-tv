// Batch E6 —— 补 batchE5 那个变量名笔误没跑成的两步：组操作条上的「转分镜组」与「批量下载」。
//
// H2 已经读出操作条的真实结构：五个动作全是 div/span，**不是 <button>**，
// 所以按 button 找永远找不到（batchE4b 的 G4/G5 就栽在这儿）。
// 这一轮直接按 innerText 精确定位 div/span。
//
// 安全边界：不点「整组执行」（会触发生成、扣积分）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchE6';
const { browser, page } = await launch();

const N = () => page.locator('.react-flow__node').count();
const nodesOf = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
  const r = n.getBoundingClientRect();
  return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16),
    isGroup: /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''),
    x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
}));
const vp = () => page.evaluate(() => {
  const s = document.querySelector('.react-flow__viewport')?.style.transform || '';
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*scale\(([-\d.]+)\)/.exec(s);
  return m ? { x: +m[1], y: +m[2], z: +m[3] } : { raw: s || null };
});
/** 组操作条上某一枚动作的实时状态（点之前先读 disabled）。 */
const barAction = (label) => page.evaluate((lb) => {
  const g = [...document.querySelectorAll('.react-flow__node')].find((n) => /group/i.test(n.className || '') || /group/i.test(n.getAttribute('data-id') || ''));
  if (!g) return { found: false, why: '没有组节点' };
  const r = g.getBoundingClientRect();
  const el = [...g.querySelectorAll('div,span')].find((e) => (e.innerText || '').trim() === lb && e.getBoundingClientRect().width > 0 && e.getBoundingClientRect().y < r.y + 60);
  if (!el) return { found: false, why: `顶部 60px 内没有文案为「${lb}」的元素` };
  const b = el.getBoundingClientRect();
  const cs = getComputedStyle(el);
  return { found: true, tag: el.tagName.toLowerCase(), x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2),
    disabled: el.getAttribute('aria-disabled') === 'true' || el.className.toString().includes('disabled') || cs.pointerEvents === 'none',
    opacity: cs.opacity };
}, label);
/** 点组操作条上的某枚动作。 */
async function clickBarAction(label) {
  const a = await barAction(label);
  if (!a.found) throw new Error(a.why);
  if (a.disabled) return { clicked: false, reason: 'disabled', at: a };
  await page.mouse.click(a.x, a.y);
  await page.waitForTimeout(2600);
  return { clicked: true, at: a };
}

const GAP = 30, VPW = 1440, SAFE_TOP = 80, SAFE_BOTTOM = 740;
function findEmptySpot(list) {
  for (let y = SAFE_TOP; y <= SAFE_BOTTOM; y += 20) for (let x = 40; x <= VPW - 40; x += 20) {
    if (!list.some((n) => x > n.x - GAP && x < n.x + n.w + GAP && y > n.y - GAP && y < n.y + n.h + GAP)) return { x, y };
  }
  return null;
}
async function addNodeAt(x, y, item) {
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(300);
  await page.mouse.dblclick(x, y); await page.waitForTimeout(1000);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
    .getByText(item, { exact: false }).first().click({ timeout: 6000 });
  await page.waitForTimeout(2000);
}
async function safe(id, title, target, fn) {
  try { await fn(); } catch (e) {
    console.log(`  ✗ ${id}: ${String(e).split('\n')[0].slice(0, 160)}`);
    await logStep(B, { id, title, target, failed: true, visible_text: `执行抛错：${String(e).split('\n')[0].slice(0, 300)}` });
  }
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '补 batchE5 笔误没跑成的「转分镜组」与「批量下载」；操作条是 div/span 不是 button' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  await addNodeAt(360, 280, '文本');
  await addNodeAt(1000, 280, '音频');
  await fitView(page, 1); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1200);

  // 框选 + 成组
  const list = await nodesOf();
  const x0 = Math.min(...list.map((n) => n.x)) - 14, y0 = Math.min(...list.map((n) => n.y)) - 14;
  const x1 = Math.max(...list.map((n) => n.x + n.w)) + 14, y1 = Math.max(...list.map((n) => n.y + n.h)) + 14;
  const spot = findEmptySpot(list);
  await page.keyboard.down('Shift');
  await page.mouse.move(spot.x, spot.y); await page.mouse.down(); await page.waitForTimeout(150);
  await page.mouse.move(x0, y0, { steps: 10 }); await page.mouse.move(x1, y1, { steps: 12 });
  await page.mouse.up(); await page.keyboard.up('Shift'); await page.waitForTimeout(1300);
  await page.keyboard.press('Meta+g'); await page.waitForTimeout(2500);
  await page.keyboard.press('Meta+-'); await page.waitForTimeout(1000);
  console.log('成组后:', JSON.stringify(await nodesOf()));

  // ── I1 「批量下载」在组里没有产物时是什么状态
  await safe('I1-group-batch-download', '组操作条「批量下载」', '读「批量下载」这一枚的 disabled 状态，不点', async () => {
    const a = await barAction('批量下载');
    await logStep(B, { id: 'I1-group-batch-download', title: '组操作条「批量下载」', target: '读「批量下载」这一枚的可用状态（不点）',
      evidence: a, visible_text: `找到: ${a.found}；状态 ${JSON.stringify(a)}` });
  });

  // ── I2 「转分镜组」：`⌘⌥G 合并分镜组` 到底在说什么
  await safe('I2-to-storyboard-group', '组操作条「转分镜组」', '按 innerText 精确定位 div/span 后点「转分镜组」', async () => {
    const before = { nodes: await N(), groups: (await nodesOf()).filter((n) => n.isGroup).length,
      titles: (await nodesOf()).map((n) => n.title) };
    const r = await clickBarAction('转分镜组');
    const after = { nodes: await N(), groups: (await nodesOf()).filter((n) => n.isGroup).length,
      titles: (await nodesOf()).map((n) => n.title),
      barStillThere: (await barAction('转分镜组')).found,
      toast: await page.evaluate(() => [...document.querySelectorAll('[role="alert"],[class*="toast"],[class*="Toast"]')]
        .filter((t) => t.getBoundingClientRect().width > 0).map((t) => (t.innerText || '').replace(/\s+/g, ' ').slice(0, 100))) };
    await shot(page, 'K-10-转分镜组后.png');
    await logStep(B, { id: 'I2-to-storyboard-group', title: '组操作条「转分镜组」', target: '点组操作条上的「转分镜组」',
      evidence: { click: r, before, after },
      visible_text: `点击 ${JSON.stringify(r)}；节点 ${before.nodes} → ${after.nodes}；分组 ${before.groups} → ${after.groups}；提示 ${JSON.stringify(after.toast)}；组名 ${JSON.stringify(after.titles.filter((t) => /Group|分镜/.test(t)))}`,
      shot: 'K-10-转分镜组后.png' });
  });

  // ── I3 整组能否像单个节点那样被拖动
  await safe('I3-drag-group', '拖动整个组', '按住组的标题栏往右拖 200px', async () => {
    const g = (await nodesOf()).find((n) => n.isGroup);
    if (!g) throw new Error('没有组节点');
    const before = { x: g.x, y: g.y };
    const from = { x: Math.max(30, g.x + 40), y: Math.max(90, g.y - 14) };
    await page.mouse.move(from.x, from.y);
    await page.mouse.down(); await page.waitForTimeout(180);
    await page.mouse.move(from.x + 100, from.y + 20, { steps: 12 });
    await page.mouse.move(from.x + 200, from.y + 40, { steps: 12 });
    await page.waitForTimeout(300);
    await page.mouse.up(); await page.waitForTimeout(1500);
    const g2 = (await nodesOf()).find((n) => n.isGroup);
    const members = (await nodesOf()).filter((n) => !n.isGroup).map((n) => [n.x, n.y]);
    await shot(page, 'K-11-拖动整组后.png');
    await logStep(B, { id: 'I3-drag-group', title: '拖动整个组', target: `按住组标题栏从 (${from.x},${from.y}) 拖到 (+200,+40)`,
      evidence: { groupBefore: [before.x, before.y], groupAfter: g2 ? [g2.x, g2.y] : null,
        membersAfter: members, moved: g2 ? (g2.x !== before.x || g2.y !== before.y) : false },
      visible_text: `组外框 (${before.x},${before.y}) → ${g2 ? `(${g2.x},${g2.y})` : 'n/a'}；成员位置 ${JSON.stringify(members)}；是否移动 ${g2 ? (g2.x !== before.x || g2.y !== before.y) : false}`,
      shot: 'K-11-拖动整组后.png' });
  });

  console.log('\n最终节点:', JSON.stringify(await nodesOf()));
} finally {
  await browser.close();
}
