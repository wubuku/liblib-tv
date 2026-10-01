// 探针 20 —— 连线图的收尾：把已连好的画布缩到 50%，让两张卡和整条线都进画面。
// 画布 projectId=98415b4a…（p19 现场新建的那张），连线已成立（edgeCount=1）。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';

const URL = 'https://www.liblib.tv/canvas?spaceId=10354929&projectId=98415b4a360243c2ae215fc356e080e3';
const { browser, page } = await launch();

try {
  await open(page, URL, { settle: 4000 });
  await closePromos(page);
  await clearToasts(page);
  await page.waitForTimeout(1500);
  await beginBatch('batchC6', { note: '连线图缩放收尾' });

  for (const z of ['50%']) {
    await page.getByRole('button', { name: '缩放选项', exact: true }).first().click();
    await page.waitForTimeout(800);
    const item = page.getByText(`缩放至${z}`, { exact: false }).first();
    if (await item.count()) { await item.click(); await page.waitForTimeout(1500); }
    else await page.keyboard.press('Escape');
  }
  await page.waitForTimeout(1200);

  const edges = await page.evaluate(() => document.querySelectorAll('.react-flow__edge').length);
  const boxes = await page.evaluate(() =>
    [...document.querySelectorAll('.react-flow__node')].map((n) => {
      const r = n.getBoundingClientRect();
      return { title: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14), x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
    }));
  console.log('缩放后连线数:', edges, '节点:', JSON.stringify(boxes));

  await shot(page, 'I-01-节点连线-总览.png');
  await logStep('batchC6', {
    id: 'I-overview',
    title: '图片节点 → 视频节点（50% 全景）',
    evidence: { edgeCount: edges, boxes },
    shot: 'I-01-节点连线-总览.png',
  });
} finally {
  await browser.close();
}
