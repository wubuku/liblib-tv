// 探针 19 —— 用「双击落点定位」把两张节点分别建在不同位置，再连线。
//
// 前面三次都栽在同一件事上：不管从「添加节点」按钮建还是别的入口，节点**一律落在
// 同一个锚点**（实测两台都在 x=720 y=408），于是端口坐标几乎重合
// （left=720,494 与 left=721,494），拖拽起点终点在同一个像素点上，React Flow 判定为
// 空操作，edgeCount=0；而拖动节点也拖不动（标题栏正好被另一张卡盖住）。
//
// 解法：空画布提示就写着「双击画布 自由生成节点」——双击面板是**锚在双击点**弹出的，
// 于是换两个不同的双击位置就能把两张卡分开建出来。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';
import { openDropdown } from './canvas-dropdown.mjs';

const SPACE = '10354929';
const B = 'batchC5';
const { browser, page } = await launch();

/** 在指定坐标双击 → 在弹出的面板里点某个节点类型。 */
async function addNodeAt(page, x, y, item) {
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(400);
  await page.mouse.dblclick(x, y);
  await page.waitForTimeout(1100);
  const panel = page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first();
  await panel.getByText(item, { exact: false }).first().click({ timeout: 6000 });
  await page.waitForTimeout(2400);
}

const boxOf = (page, prefix) =>
  page.evaluate((p) => {
    const n = [...document.querySelectorAll('.react-flow__node')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().startsWith(p));
    if (!n) return null;
    const r = n.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
  }, prefix);

const handlesOf = (page, prefix) =>
  page.evaluate((p) => {
    const n = [...document.querySelectorAll('.react-flow__node')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().startsWith(p));
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
  await page.waitForTimeout(1200);
  await beginBatch(B, { note: '双击落点建节点 → 连线 → 干净图' });

  // 现场新建一张空画布
  await openDropdown(page, 1000);
  await page.getByRole('button', { name: '新建画布', exact: true }).first().click();
  await page.waitForTimeout(4000);
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(1200);
  console.log('新画布:', page.url());

  // 两个**不同的**双击位置
  await addNodeAt(page, 260, 220, '图片');
  console.log('图片位置:', JSON.stringify(await boxOf(page, '图片节点')));
  await addNodeAt(page, 900, 520, '视频');
  console.log('视频位置:', JSON.stringify(await boxOf(page, '视频节点')));

  const ih = await handlesOf(page, '图片节点');
  const vh = await handlesOf(page, '视频节点');
  console.log('图片端口:', JSON.stringify(ih), '\n视频端口:', JSON.stringify(vh));

  if (ih && vh) {
    const out = ih.find((h) => h.pos === 'right') || ih[ih.length - 1];
    const inp = vh.find((h) => h.pos === 'left') || vh[0];
    console.log('拖拽:', JSON.stringify(out.xy), '->', JSON.stringify(inp.xy));

    await page.mouse.move(out.xy[0], out.xy[1]);
    await page.waitForTimeout(400);
    await page.mouse.down();
    await page.waitForTimeout(180);
    await page.mouse.move(out.xy[0] + 60, out.xy[1] + 40, { steps: 8 });
    await page.waitForTimeout(250);
    await page.mouse.move(inp.xy[0], inp.xy[1], { steps: 30 });
    await page.waitForTimeout(800);
    await shot(page, 'H-10-连线-拖拽中.png');
    await page.mouse.up();
    await page.waitForTimeout(2600);

    const edges = await page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
    await shot(page, 'H-11-节点连线-完整.png');
    await logStep(B, {
      id: 'H-connect',
      title: '图片节点输出端口 → 视频节点输入端口',
      target: 'source/right → target/left',
      evidence: {
        edgeCount: edges,
        img: await boxOf(page, '图片节点'),
        vid: await boxOf(page, '视频节点'),
        out, inp,
      },
      visible_text: `连线数: ${edges}`,
      shot: 'H-11-节点连线-完整.png',
    });

    // 选中两张节点一起看
    await shot(page, 'H-12-连线-节点特写.png');
  }
} finally {
  await browser.close();
}
