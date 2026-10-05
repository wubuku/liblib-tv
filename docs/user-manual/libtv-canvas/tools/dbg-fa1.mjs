import { launch, closePromos, ORIGIN } from './lib.mjs';
const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const 浏览器 = await launch();
const page = 浏览器.page;

const dump = (标签) => page.evaluate((t) => ({
  标签: t,
  url: location.href,
  视口: getComputedStyle(document.querySelector('.react-flow__viewport')).transform,
  节点: [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')),
  选中: [...document.querySelectorAll('.react-flow__node.selected')].map((n) => n.getAttribute('data-id')),
  节点总数: document.querySelectorAll('.react-flow').length,
}), 标签);

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  console.log('A0', JSON.stringify(await dump('打开后')));

  const p = await page.evaluate(() => {
    const n = document.querySelector('.react-flow__node[data-id="v-v2hlWY4Br3"]');
    const r = n.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + 14), Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)];
  });
  console.log('落点', p);
  await page.mouse.move(p[0], p[1]); await page.waitForTimeout(400);
  console.log('落点自证', await page.evaluate(([x, y]) => { const e = document.elementFromPoint(x, y); const n = e && e.closest('.react-flow__node'); return { tag: e && e.tagName, cls: e && (e.className || '').toString().slice(0, 40), id: n && n.getAttribute('data-id') }; }, p));
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(950);
  console.log('B 点后', JSON.stringify(await dump('点后未移动')));
  await page.mouse.move(720, 250); await page.waitForTimeout(700);
  console.log('C 移后', JSON.stringify(await dump('移动到720,250之后')));
  await page.waitForTimeout(3000);
  console.log('D 再等3s', JSON.stringify(await dump('再等3秒')));
  await page.screenshot({ path: new URL('.evidence/fa1-debug.png', import.meta.url).pathname });
  console.log('已拍 fa1-debug.png');
} catch (e) { console.log('ERR', e.message); } finally { await 浏览器.browser.close(); }
