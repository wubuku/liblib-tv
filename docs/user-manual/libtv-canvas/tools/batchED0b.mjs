// Batch ED-0b：重建音频节点（ED-0 找到入口了，但选择器没认出来那个面板）。
//
// ED-0 的教训：那个「引用该节点生成」面板**不是** mantine-Menu-dropdown / Popover，
// 所以按 class 找 = 读到空数组 ⇒ 误判成「菜单没打开」。
// ⭐ 这就是 §256 的又一次翻版：**「我按什么在找的」**。
// 本步改成**按可见文字 `音频` 找**，并优先用底部工具条那枚 `+` 主入口。
//
// ⛔ 安全约束不变：一个删除键都不碰；不连任何线。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchED0b.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = { 读数: {} };

const 读节点 = (page) => page.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  return {
    缩放: vp ? getComputedStyle(vp).transform : null,
    节点: [...document.querySelectorAll('.react-flow__node')].map(n => {
      const r = n.getBoundingClientRect();
      return {
        id: n.getAttribute('data-id'),
        cls: n.className.toString().split(' ').filter(c => c.startsWith('react-flow__node-')).join(','),
        rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      };
    }),
  };
});

/** ⭐ 不按 class，按「可见文字」找可点元素并点它。 */
const 按文字点 = async (page, 文案) => page.evaluate((t) => {
  const els = [...document.querySelectorAll('button,[role="menuitem"],[role="button"],li,div')];
  const hit = els.find(e => {
    if (e.querySelector('button,[role="menuitem"],[role="button"]')) return false;
    const s = getComputedStyle(e);
    if (s.visibility === 'hidden' || s.opacity === '0') return false;
    const r = e.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return false;
    return (e.innerText || '').trim() === t;
  });
  if (!hit) return false;
  hit.click();
  return true;
}, 文案);

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6000 });
  await closePromos(page);
  await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1600);

  const 前 = await 读节点(page);
  结果.读数.建前 = 前;
  console.log('建前节点数:', 前.节点.length, '| 音频节点:',
    前.节点.filter(n => /node-audio/.test(n.cls)).length);
  落盘(结果);

  // ⭐ 优先用底部工具条的 `+` 主入口
  const 加号 = await page.evaluate(() => {
    const els = [...document.querySelectorAll('button')];
    const hit = els.find(b => {
      const r = b.getBoundingClientRect();
      // 底部工具条中央那枚白底大加号：约 36×36，位于视口下半部中线附近
      return r.width >= 28 && r.width <= 48 && r.height >= 28 && r.height <= 48
        && r.top > window.innerHeight * 0.85
        && Math.abs((r.left + r.width / 2) - window.innerWidth / 2) < 260
        && !b.innerText.trim();
    });
    if (!hit) return null;
    const r = hit.getBoundingClientRect();
    return { box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], cls: hit.className.toString().slice(0, 60) };
  });
  console.log('底部 `+` 按钮:', JSON.stringify(加号));
  结果.读数.加号 = 加号;
  落盘(结果);

  if (加号) {
    const b = 加号.box;
    await page.mouse.click(b[0] + b[2] / 2, b[1] + b[3] / 2);
    await page.waitForTimeout(1000);
  }

  // ⭐ 按可见文字找「音频」
  const 建了 = await 按文字点(page, '音频');
  console.log('\n按文字点「音频」:', 建了);
  await page.waitForTimeout(2500);
  结果.读数.建了 = 建了;
  落盘(结果);

  const 后 = await 读节点(page);
  const 新增 = 后.节点.filter(n => !前.节点.some(o => o.id === n.id));
  结果.读数.建后 = 后;
  结果.读数.新增 = 新增;
  console.log('建后节点数:', 后.节点.length, '（建前', 前.节点.length, '）');
  console.log('  新增:', JSON.stringify(新增));
  console.log('  音频节点数:', 后.节点.filter(n => /node-audio/.test(n.cls)).length, '（建前',
    前.节点.filter(n => /node-audio/.test(n.cls)).length, '）');
  落盘(结果);

  await page.screenshot({ path: '.evidence/batchED0b-重建后.png' });

  // ⭐ 刷新复核（确认真的落盘，不只是内存里多了个节点）
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(5500);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1600);
  const 刷 = await 读节点(page);
  结果.读数.刷新后 = 刷;
  console.log('\n⭐ 刷新后: 节点数=', 刷.节点.length, '| 音频节点=',
    刷.节点.filter(n => /node-audio/.test(n.cls)).length);
  console.log('  刷新后仍在的新增 id:', JSON.stringify(刷.节点.map(n => n.id).filter(id => !前.节点.some(o => o.id === id))));
  落盘(结果);
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchED0b.json ===');
}
