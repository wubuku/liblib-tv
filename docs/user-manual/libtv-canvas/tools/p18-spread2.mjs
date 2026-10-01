// 探针 18 —— 最后一次攻「把节点拖开 + 干净连线图」。
//
// p17 失败的原因：React Flow 的拖拽有一个**启动阈值**——按下后必须先有一次小幅移动
// 才会进入 drag 状态，直接从起点一步挪到终点会被当成普通点击，节点纹丝不动。
// 这里按下后先走 8px 触发拖拽，停 250ms，再分多段移动到目标位置。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';

const URL = 'https://www.liblib.tv/canvas?spaceId=10354929&projectId=7491cfb22a10423fbcb3b0875799415e';
const B = 'batchC4';
const { browser, page } = await launch();

const boxOf = (page, prefix) =>
  page.evaluate((p) => {
    const n = [...document.querySelectorAll('.react-flow__node')]
      .find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().startsWith(p));
    if (!n) return null;
    const r = n.getBoundingClientRect();
    return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height), titleX: Math.round(r.x + r.width / 2), titleY: Math.round(r.y + 12) };
  }, prefix);

/** 带拖拽启动阈值的节点拖动。 */
async function dragNode(page, from, dx, dy) {
  await page.mouse.move(from.titleX, from.titleY);
  await page.mouse.down();
  await page.waitForTimeout(120);
  await page.mouse.move(from.titleX + 8, from.titleY + 8, { steps: 3 });   // 触发 drag 阈值
  await page.waitForTimeout(250);
  await page.mouse.move(from.titleX + dx / 2, from.titleY + dy / 2, { steps: 14 });
  await page.waitForTimeout(180);
  await page.mouse.move(from.titleX + dx, from.titleY + dy, { steps: 14 });
  await page.waitForTimeout(300);
  await page.mouse.up();
  await page.waitForTimeout(1600);
}

try {
  await open(page, URL, { settle: 4000 });
  await closePromos(page);
  await clearToasts(page);
  await page.waitForTimeout(1500);
  await beginBatch(B, { note: '拖开节点 + 重连，产出干净连线图' });

  const before = { img: await boxOf(page, '图片节点'), vid: await boxOf(page, '视频节点') };
  console.log('拖前:', JSON.stringify(before));

  // 视频节点往下拖一屏（后建的在上面，先把它挪开）
  if (before.vid) await dragNode(page, before.vid, 0, 420);
  const mid = { img: await boxOf(page, '图片节点'), vid: await boxOf(page, '视频节点') };
  console.log('拖后:', JSON.stringify(mid));

  // 缩到能一眼看全
  await page.getByRole('button', { name: '缩放选项', exact: true }).first().click();
  await page.waitForTimeout(700);
  const z = page.getByText('缩放至50%', { exact: false }).first();
  if (await z.count()) { await z.click(); await page.waitForTimeout(1400); }

  const boxes = { img: await boxOf(page, '图片节点'), vid: await boxOf(page, '视频节点') };
  console.log('缩放后:', JSON.stringify(boxes));

  const handles = async (p) => page.evaluate((pfx) => {
    const n = [...document.querySelectorAll('.react-flow__node')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().startsWith(pfx));
    if (!n) return null;
    return [...n.querySelectorAll('.react-flow__handle')].map((h) => {
      const r = h.getBoundingClientRect();
      return { pos: h.getAttribute('data-handlepos'), xy: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
    });
  }, p);

  const ih = await handles('图片节点');
  const vh = await handles('视频节点');
  console.log('图片端口', JSON.stringify(ih), '视频端口', JSON.stringify(vh));

  if (ih && vh) {
    const out = ih.find((h) => h.pos === 'right') || ih[ih.length - 1];
    const inp = vh.find((h) => h.pos === 'left') || vh[0];
    await page.mouse.move(out.xy[0], out.xy[1]);
    await page.mouse.down();
    await page.waitForTimeout(150);
    await page.mouse.move(inp.xy[0], inp.xy[1], { steps: 30 });
    await page.waitForTimeout(700);
    await page.mouse.up();
    await page.waitForTimeout(2500);
    const edges = await page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
    await shot(page, 'H-01-节点连线-完整.png');
    await logStep(B, {
      id: 'H-connect',
      title: '图片节点 → 视频节点 连线全貌',
      target: 'source/right → target/left',
      evidence: { edgeCount: edges, boxes, out, inp },
      visible_text: `连线数: ${edges}`,
      shot: 'H-01-节点连线-完整.png',
    });
  }
} finally {
  await browser.close();
}
