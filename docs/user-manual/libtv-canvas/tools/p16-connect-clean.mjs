// 探针 16 —— 干净的连线取证：现场新建一张画布，只放 图片 + 视频 两张，拖一条线，拍一张干净的图。
//
// 前面 batchC 的连线本身是成功的（edgeCount=1，source/right → target/left 都对），
// 但那张图上堆着历轮残留的十个节点，根本不能进手册。所以重来一次，起点完全确定。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, shotHighlighted, beginBatch, logStep } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchC2';
const { browser, page } = await launch();

async function createNode(page, item) {
  await page.keyboard.press('Escape').catch(() => {});
  await page.getByRole('button', { name: '添加节点', exact: true }).first().click({ timeout: 10000 });
  await page.waitForTimeout(1000);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first()
    .getByText(item, { exact: false }).first().click({ timeout: 6000 });
  await page.waitForTimeout(2400);
}

const handlesOf = (page, prefix) =>
  page.evaluate((p) => {
    const n = [...document.querySelectorAll('.react-flow__node')]
      .find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().startsWith(p));
    if (!n) return null;
    return [...n.querySelectorAll('.react-flow__handle')].map((h) => {
      const r = h.getBoundingClientRect();
      return { pos: h.getAttribute('data-handlepos'), id: h.getAttribute('data-handleid'), xy: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
    });
  }, prefix);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4000 });
  await closePromos(page);
  await clearToasts(page);
  await page.waitForTimeout(1000);
  await beginBatch(B, { note: '干净画布上的连线取证' });

  // 新建一张空画布
  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4000);
  await clearPromosSafe(page);
  await page.waitForTimeout(1500);
  console.log('新画布:', page.url(), '节点数:', await nodeCount(page));

  await createNode(page, '图片');
  await createNode(page, '视频');

  // 把两张拉开一点，线才好看
  const boxes = await page.evaluate(() =>
    [...document.querySelectorAll('.react-flow__node')].map((n) => {
      const r = n.getBoundingClientRect();
      return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
    }));
  console.log('节点位置:', JSON.stringify(boxes));

  const imgH = await handlesOf(page, '图片节点');
  const vidH = await handlesOf(page, '视频节点');
  console.log('图片端口:', JSON.stringify(imgH), '视频端口:', JSON.stringify(vidH));

  if (imgH && vidH) {
    const out = imgH.find((h) => h.pos === 'right') || imgH[imgH.length - 1];
    const inp = vidH.find((h) => h.pos === 'left') || vidH[0];

    // 拖拽前先高亮起点端口，拍一张「从哪个口拖出」
    await page.mouse.move(out.xy[0], out.xy[1]);
    await page.waitForTimeout(400);
    await shot(page, 'G-01-连线-起点端口.png');

    await page.mouse.down();
    await page.mouse.move(inp.xy[0], inp.xy[1], { steps: 30 });
    await page.waitForTimeout(700);
    await shot(page, 'G-02-连线-拖拽中.png');
    await page.mouse.up();
    await page.waitForTimeout(2500);

    const edges = await page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
    await shot(page, 'G-03-连线-完成.png');
    await logStep(B, {
      id: 'G-connect',
      title: '连线：从图片节点输出端口拖到视频节点输入端口',
      target: 'source/right → target/left',
      evidence: { edgeCount: edges, out, inp },
      visible_text: `连线数: ${edges}`,
      shot: 'G-03-连线-完成.png',
    });

    // 选中连线看看有什么操作
    const edge = page.locator('.react-flow__edge').first();
    if (await edge.count()) {
      await edge.click({ force: true }).catch(() => {});
      await page.waitForTimeout(1200);
      await shot(page, 'G-04-选中连线.png');
      const btns = await page.evaluate(() => [...document.querySelectorAll('button')]
        .filter((b) => b.getBoundingClientRect().width > 8)
        .map((b) => b.getAttribute('aria-label') || (b.innerText || '').trim())
        .filter((t) => /删除|断开|移除|连线|edit|delete/i.test(String(t))));
      await logStep(B, { id: 'G-edge-select', title: '选中连线后的可用操作', evidence: { buttons: btns }, shot: 'G-04-选中连线.png' });
    }
  }
} finally {
  await browser.close();
}

async function clearPromosSafe(page) {
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(400);
}
