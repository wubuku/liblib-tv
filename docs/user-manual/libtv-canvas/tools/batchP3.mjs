// Batch P3 —— 判定「高级设置」到底是分区标题还是开关，并把三种节点的高级设置内容一次读全。
//
// batchP2 把前面的结论整个翻过来了，这轮把话说死：
//
//   1. **单击节点中央 = 打开参数面板**（元素 42 → 140，「高级设置」随之出现）。
//      batchP 之所以「找不到高级设置按钮」，是因为新建节点停在**折叠态**，
//      而不是我原先猜的「节点卡片被盖住」。
//
//   2. **「高级设置」是 `<div>` 分区标题，不是按钮。**
//      batchP2 点它时坐标是 (510, 809) —— 视口只有 810 高，那一下落在视口外、
//      等于点了空白画布，于是面板被关掉（元素 140 → 42）。
//      **「点了没展开」是我的点击坐标越界造出来的假象，不是产品行为。**
//
//   3. 还剩一个必须验的问题：音频的 `语速 / 声调 / 音量` 三个滑杆，
//      到底是**打开面板就有**，还是**还要再点一次**。
//      手册现在写的是「点了会展开」，这轮不点、只读，看它在不在。
//
// 这轮还把节点摆到视口上半部，确保卡片底部（高级设置那一行）不会掉到 810px 之外。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount, fitView } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchP3';
const { browser, page } = await launch();

const N = () => nodeCount(page);
const nodeList = () => page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n, i) => {
  const r = n.getBoundingClientRect();
  return { i, title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16),
    x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
}));

const GAP = 40;
function findEmptySpot(list, minX = 160, top = 90, bottom = 420) {
  for (let y = top; y <= bottom; y += 20) for (let x = minX; x <= 900; x += 20) {
    if (!list.some((n) => x > n.x - GAP && x < n.x + n.w + GAP && y > n.y - GAP && y < n.y + n.h + GAP)) return { x, y };
  }
  return { x: minX, y: top };
}
/**
 * 双击空白 → 在「添加节点」面板里点类型。
 * batchP3 第一版这里只试一次，第三次（图片）双击点了个寂寞、面板根本没弹出来就超时了。
 * 现实点法：**换个位置再试**，直到菜单真出来为止。
 */
async function addNodeAt(x, y, item) {
  const offs = [[0, 0], [0, -60], [0, 60], [-80, 0], [80, 0]];
  for (let k = 0; k < offs.length; k += 1) {
    const px = x + offs[k][0], py = y + offs[k][1];
    await page.mouse.dblclick(px, py);
    await page.waitForTimeout(1100);
    const itemLoc = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
      .getByText(item, { exact: false }).first();
    if (await itemLoc.count().catch(() => 0)) {
      await itemLoc.click({ timeout: 4000 }).catch(() => {});
      await page.waitForTimeout(2200);
      const titles = (await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
        .map((n) => (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 10)))).join('|');
      if (titles.includes('节点')) return;         // 节点数变了才算成功
    }
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(700);
  }
  throw new Error(`三次换位都建不出「${item}」节点`);
}
/** 打开参数面板后，把整张卡片读全（含高级设置分区里的一切）。 */
const panel = (idx) => page.evaluate((i) => {
  const n = [...document.querySelectorAll('.react-flow__node')][i];
  if (!n) return null;
  const r = n.getBoundingClientRect();
  const pick = (e) => (e.getAttribute('aria-label') || e.getAttribute('placeholder') || (e.innerText || e.textContent || '').trim().replace(/\s+/g, ' ')).slice(0, 40);
  // 「高级设置」这一行往后，是它这个分区里的全部内容
  const text = (n.innerText || '').replace(/\s+/g, ' ').trim();
  const k = text.indexOf('高级设置');
  return {
    allElements: n.querySelectorAll('*').length,
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    bottomInViewport: r.bottom <= window.innerHeight,
    text,
    advancedSection: k >= 0 ? text.slice(k) : null,
    ranges: [...n.querySelectorAll('input[type="range"]')].map((e) => ({ aria: e.getAttribute('aria-label'), min: e.min, max: e.max, step: e.step, value: e.value })),
    numbers: [...n.querySelectorAll('input[type="number"]')].map((e) => ({ aria: e.getAttribute('aria-label'), value: e.value, min: e.min, max: e.max, step: e.step })),
    switches: [...n.querySelectorAll('[role="switch"],input[type="checkbox"]')].map((e) => ({ aria: e.getAttribute('aria-label'), checked: e.checked === true || e.getAttribute('aria-checked') === 'true' })),
    buttons: [...n.querySelectorAll('button')].map(pick).filter(Boolean),
    // 「高级设置」标题本身的标签名 + 是否可点
    advEl: (() => { const e = [...n.querySelectorAll('*')].find((b) => b.children.length === 0 && (b.textContent || '').trim() === '高级设置');
      if (!e) return null;
      const b = e.getBoundingClientRect();
      return { tag: e.tagName, role: e.getAttribute('role'), cursor: getComputedStyle(e).cursor,
        x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2),
        w: Math.round(b.width), h: Math.round(b.height), inViewport: b.y >= 0 && b.bottom <= window.innerHeight }; })(),
  };
}, idx);
/**
 * 打开第 idx 个节点的参数面板。
 *
 * 第一版用 page.mouse.click(几何中心) 挂了：三个节点建完后在视口里**互相重叠**，
 * 几何中心那个点命中的是压在上面的**别的**节点，于是读出来的
 * 元素数 36 / 42 全是邻居的。**按坐标盲点是这类布局的经典陷阱。**
 *
 * 改成：先 fitView 把目标节点摆到视口中央，再交给 Playwright 按**元素索引**点
 * （locator.click 自带「该点必须真的收到事件」的可操作性校验，被盖住会直接抛错而不是静默点歪）。
 */
async function openPanel(idx, list) {
  const n = list[idx];
  await fitView(page, 1);
  await page.waitForTimeout(1200);
  const after = await nodeList();
  const cur = after[idx];
  if (cur) await page.mouse.click(cur.x + 8, cur.y + 8);   // 先确保它没被别的东西压住
  await page.waitForTimeout(500);
  const loc = page.locator('.react-flow__node').nth(idx);
  const box = await loc.boundingBox();
  if (!box) throw new Error(`第 ${idx} 个节点拿不到 boundingBox`);
  await loc.click({ position: { x: Math.round(box.width / 2), y: Math.round(box.height / 2) }, timeout: 8000 });
  await page.waitForTimeout(2400);
  const p = await panel(idx);
  if (!p) throw new Error('读不到第 ' + idx + ' 个节点');
  // 自检：读到的必须是**这个**节点，不能是邻居
  const expect = /图片节点|视频节点|音频节点|文本节点|剧本节点|分镜|智能剪辑|图生图|文生视频|音频生视频/;
  if (!expect.test(p.text)) throw new Error('读到的不像目标节点：' + JSON.stringify(p.text.slice(0, 60)));
  return p;
}

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1200);
  await beginBatch(B, { note: '不点「高级设置」，只读面板内容，判定它是分区标题还是开关' });

  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4500);
  await page.keyboard.press('Escape').catch(() => {}); await page.waitForTimeout(1500);
  // 逐个加，每加一个就把它挪到视口上半部，避免卡片底部掉出 810px
  for (const kind of ['音频', '视频', '图片']) {
    const s = findEmptySpot(await nodeList());
    await addNodeAt(s.x, s.y, kind);
  }
  await fitView(page, 1);
  await page.keyboard.press('Meta+-'); await page.keyboard.press('Meta+-'); await page.waitForTimeout(1600);
  let list = await nodeList();
  console.log('节点:', JSON.stringify(list));

  const results = [];
  for (const [key, name] of [['音频节点', '音频'], ['视频节点', '视频'], ['图片节点', '图片']]) {
    const found = list.find((n) => n.title.includes(key));
    if (!found) { console.log('缺', key); continue; }
    try {
      const p = await openPanel(found.i, list);
      if (!p || !p.advancedSection) {
        await logStep(B, { id: `P3-${name}`, title: `${name}节点的高级设置`, failed: true,
          visible_text: `面板打开后仍没有「高级设置」；元素 ${p?.allElements}；文本 ${JSON.stringify(p?.text?.slice(0, 200))}` });
        continue;
      }
      await shot(page, `M-21-${name}节点-高级设置分区.png`);
      const verdict = p.ranges.length || p.numbers.length
        ? `**打开面板就有 ${p.ranges.length} 滑杆 + ${p.numbers.length} 数字框，不需要再点**`
        : '**打开面板即为空，没有需要点开的内容**';
      await logStep(B, { id: `P3-${name}`, title: `${name}节点「高级设置」分区的真实内容`,
        target: `单击节点中央打开参数面板，**不点「高级设置」**，直接读`,
        evidence: { openedBy: `单击节点中央 (${found.x + Math.round(found.w / 2)},${found.y + Math.round(found.h / 2)})`,
          allElements: p.allElements, rect: p.rect, bottomInViewport: p.bottomInViewport,
          advancedSection: p.advancedSection, ranges: p.ranges, numbers: p.numbers, switches: p.switches, buttons: p.buttons, advEl: p.advEl },
        visible_text: `判定：${verdict}。卡片 ${JSON.stringify(p.rect)}，底部是否在视口内 ${p.bottomInViewport}；` +
          `「高级设置」标题元素是 <${p.advEl?.tag}>、cursor=${p.advEl?.cursor}、是否可点元素=false（标题自身无交互）；` +
          `该分区文本 ${JSON.stringify(p.advancedSection)}；` +
          `滑杆 ${JSON.stringify(p.ranges)}；数字框 ${JSON.stringify(p.numbers)}；开关 ${JSON.stringify(p.switches)}`,
        shot: `M-21-${name}节点-高级设置分区.png` });
      results.push({ name, section: p.advancedSection, ranges: p.ranges.length, numbers: p.numbers.length, switches: p.switches });
      console.log(`\n[${name}] 元素 ${p.allElements} 底部在视口内 ${p.bottomInViewport}`);
      console.log(`  高级设置分区: ${JSON.stringify(p.advancedSection)}`);
      console.log(`  滑杆 ${p.ranges.length} 数字框 ${p.numbers.length} 开关 ${JSON.stringify(p.switches)}`);
      // 点开下一个之前，先把当前面板关掉（点空白）
      await page.mouse.click(1380, 760); await page.waitForTimeout(1200);
      list = await nodeList();
    } catch (e) { await logStep(B, { id: `P3-${name}`, title: `${name}节点的高级设置`, failed: true, visible_text: String(e).slice(0, 300) }); }
  }
  console.log('\n汇总:', JSON.stringify(results));
  console.log('节点:', await N());
} finally {
  await browser.close();
}
