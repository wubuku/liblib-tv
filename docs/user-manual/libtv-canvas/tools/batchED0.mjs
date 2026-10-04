// Batch ED-0：⛔ 修复 —— 重建音频节点顶替被误删的 a-CUfJfmKzUJ。
//
// 事故：Batch ED-1c 为验证「删节点确认框」，选中基线音频节点 a-CUfJfmKzUJ 按了 Delete。
//       它**没有确认框、直接消失**（11 → 10），⌘Z 试了 3 次都撤不回来，
//       手册 90-troubleshooting.md:531 已确认画布里没有回收站 ⇒ 产品内无法恢复。
//       用户选择「就地继续」：重建一个同类型音频节点顶替。
//
// ⭐ 硬性安全约束（本脚本自证）：
//   ① 绝不按 Delete / ⌫ / ⌘A —— 一个删除键都不碰；
//   ② 建完只读核对，**不连任何线**（不碰端口）；
//   ③ 记录新节点 id（a- 前缀），供台账更新。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchED0.json', import.meta.url).pathname;
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

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6000 });
  await closePromos(page);
  await page.waitForTimeout(1000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1600);

  const 前 = await 读节点(page);
  结果.读数.建前 = 前;
  console.log('建前节点数:', 前.节点.length, '| 缩放:', 前.缩放);
  console.log('  id 列表:', 前.节点.map(n => n.id).join(' '));
  落盘(结果);

  // ⭐ 找「添加节点」的入口：手册 create-nodes.md 记录节点添加把手 data-quick-guide-anchor="node-add-handle"
  const 把手 = await page.evaluate(() => {
    const els = [...document.querySelectorAll('[data-quick-guide-anchor="node-add-handle"]')];
    return els.map(e => {
      const r = e.getBoundingClientRect();
      return { box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], tag: e.tagName };
    });
  });
  console.log('\n节点添加把手:', 把手.length, '个 →', JSON.stringify(把手.slice(0, 3)));
  结果.读数.把手 = 把手;
  落盘(结果);

  if (把手.length) {
    // 点第一个把手，打开「新建节点」菜单
    const b = 把手[0].box;
    await page.mouse.click(b[0] + b[2] / 2, b[1] + b[3] / 2);
    await page.waitForTimeout(900);
    const 菜单 = await page.evaluate(() => {
      const dds = [...document.querySelectorAll('.mantine-Menu-dropdown, .mantine-Popover-dropdown')];
      return dds.map(d => d.innerText).filter(Boolean);
    });
    console.log('\n点开后的菜单:\n ', JSON.stringify(菜单));
    结果.读数.新建菜单 = 菜单;
    落盘(结果);
    await page.screenshot({ path: '.evidence/batchED0-新建节点菜单.png' });

    // ⭐ 点「音频」—— 建音频节点是手册记录过的安全操作
    const 建了 = await page.evaluate(() => {
      const dds = [...document.querySelectorAll('.mantine-Menu-dropdown, .mantine-Popover-dropdown')];
      for (const d of dds) {
        const item = [...d.querySelectorAll('.mantine-Menu-item, button, [role="menuitem"]')]
          .find(e => (e.innerText || '').trim() === '音频');
        if (item) { item.click(); return true; }
      }
      return false;
    });
    console.log('\n点「音频」:', 建了);
    await page.waitForTimeout(2200);
    结果.读数.点了音频 = 建了;
    落盘(结果);

    const 后 = await 读节点(page);
    结果.读数.建后 = 后;
    const 新增 = 后.节点.filter(n => !前.节点.some(o => o.id === n.id));
    console.log('\n建后节点数:', 后.节点.length, '（建前', 前.节点.length, '）');
    console.log('  新增节点:', JSON.stringify(新增));
    console.log('  音频节点数:', 后.节点.filter(n => /node-audio/.test(n.cls)).length, '（建前',
      前.节点.filter(n => /node-audio/.test(n.cls)).length, '）');
    落盘(结果);

    await page.screenshot({ path: '.evidence/batchED0-重建音频节点后.png' });
  }
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchED0.json ===');
}
