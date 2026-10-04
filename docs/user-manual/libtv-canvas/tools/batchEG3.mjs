// Batch EG-3：EG-2 点到了「管理」（切库成功），但读内容全是 undefined
//   ⇒ 那个「资产管理」弹窗**不是** .mantine-Modal-content。
//
// 本步只做一件事：把「可灵主体库」这两个字所在的**全部祖先容器**列出来，
// 逐层报告 class / 尺寸 / 按钮数，找到真正承载它的那一层。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEG3.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {} };

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
  await closePromos(page);
  await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1500);

  await page.evaluate(() => {
    for (const b of document.querySelectorAll('button')) if ((b.innerText || '').trim() === '资产管理') { b.click(); return; }
  });
  await page.waitForTimeout(1600);
  await page.evaluate(() => {
    const d = document.querySelector('.mantine-Drawer-content');
    const t = d && [...d.querySelectorAll('button')].find(b => (b.innerText || '').trim() === '资产');
    if (t) t.click();
  });
  await page.waitForTimeout(1600);
  await page.evaluate(() => {
    const d = document.querySelector('.mantine-Drawer-content');
    const m = d && [...d.querySelectorAll('button')].find(b => (b.innerText || '').trim() === '管理');
    if (m) m.click();
  });
  await page.waitForTimeout(2200);

  // ⭐ 找「可灵主体库」文本节点，打印整条祖先链
  const 链 = await page.evaluate(() => {
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let n, 命中 = null;
    while ((n = w.nextNode())) {
      if ((n.nodeValue || '').trim() === '可灵主体库') { 命中 = n.parentElement; break; }
    }
    if (!命中) return { 错: '页面上没有「可灵主体库」这四个字' };
    const 链 = [];
    for (let e = 命中; e && e !== document.documentElement; e = e.parentElement) {
      const r = e.getBoundingClientRect();
      const cs = getComputedStyle(e);
      链.push({
        tag: e.tagName,
        cls: e.className.toString().slice(0, 90),
        box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
        按钮数: e.querySelectorAll('button').length,
        更多操作: e.querySelectorAll('button[aria-label="更多操作"]').length,
        文本长: (e.innerText || '').length,
        position: cs.position, zIndex: cs.zIndex,
      });
    }
    return { 链 };
  });
  结果.读数.祖先链 = 链;
  if (链.错) { console.log('  ', 链.错); }
  else {
    console.log('═══「可灵主体库」的祖先链（自内向外）═══');
    链.链.forEach((c, i) => {
      console.log(`  [${i}] <${c.tag}> box=${JSON.stringify(c.box)} 按钮=${c.按钮数} 更多操作=${c.更多操作} 文本长=${c.文本长} pos=${c.position} z=${c.zIndex}`);
      console.log(`      cls=${c.cls}`);
    });
  }
  await page.screenshot({ path: '.evidence/batchEG3-可灵主体库祖先链.png' });
  落盘(结果);
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEG3.json ===');
}
