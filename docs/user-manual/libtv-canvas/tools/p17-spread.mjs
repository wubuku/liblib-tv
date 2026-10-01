// 探针 17 —— 把两张叠在一起的节点拖开，得到一张能进手册的连线图。
//
// 为什么需要单独一趟：新增节点一律落在同一个锚点（实测两台都落在 x=720,y=408），
// 所以 batchC/p16 虽然连线成功（edgeCount=1），画面上两张卡是叠着的，看不出「谁连谁」。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { nodeCount } from './canvas-ops.mjs';

const URL = 'https://www.liblib.tv/canvas?spaceId=10354929&projectId=7491cfb22a10423fbcb3b0875799415e';
const B = 'batchC3';
const { browser, page } = await launch();

const boxOf = (page, prefix) =>
  page.evaluate((p) => {
    const n = [...document.querySelectorAll('.react-flow__node')]
      .find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().startsWith(p));
    if (!n) return null;
    const r = n.getBoundingClientRect();
    return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + 24), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
  }, prefix);

try {
  await open(page, URL, { settle: 4000 });
  await closePromos(page);
  await clearToasts(page);
  await page.waitForTimeout(1500);
  await beginBatch(B, { note: '拖开节点后的连线图' });
  console.log('节点数:', await nodeCount(page));

  // 把上面那张（后建的视频节点）拖到右边
  const v = await boxOf(page, '视频节点');
  console.log('视频节点位置:', JSON.stringify(v));
  if (v) {
    // 用节点标题栏拖动，避免误触提示词输入区
    await page.mouse.move(v.cx, v.y + 10);
    await page.mouse.down();
    await page.mouse.move(v.cx + 60, v.y + 10, { steps: 8 });
    await page.mouse.move(v.cx + 420, v.y - 40, { steps: 24 });
    await page.mouse.up();
    await page.waitForTimeout(2200);
  }

  const after = { img: await boxOf(page, '图片节点'), vid: await boxOf(page, '视频节点') };
  console.log('拖开后:', JSON.stringify(after));

  // 连线是否还在
  const edges = await page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
  console.log('连线数:', edges);
  await shot(page, 'G-05-连线-拖开.png');
  await logStep(B, {
    id: 'G-spread',
    title: '拖开两张节点后的连线全貌',
    target: '拖动节点标题栏',
    evidence: { boxes: after, edgeCount: edges },
    shot: 'G-05-连线-拖开.png',
  });

  // 选中连线看有没有操作条
  const edge = page.locator('.react-flow__edge').first();
  if (await edge.count()) {
    await edge.click({ force: true }).catch(() => {});
    await page.waitForTimeout(1200);
    await shot(page, 'G-06-选中连线.png');
    await logStep(B, { id: 'G-edge', title: '选中连线', evidence: { edgeCount: edges }, shot: 'G-06-选中连线.png' });
  }
} finally {
  await browser.close();
}
