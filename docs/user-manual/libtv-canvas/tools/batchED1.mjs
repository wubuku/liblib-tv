// Batch ED-1：删**节点**的确认框 —— 只打开、只读、只点「取消」。
//
// EC 批在源码里挖到删节点确认框的完整分支（`3-mou5v69wxmq.js`）：
//   有 SCRIPT/SCRIPT_V2 节点        → 「确认删除」/「…{undoShortcut}…」
//   VIDEO 且 data.openingUsed        → 「确认删除该节点？」/「创意片头」那段
//   分镜组（含非 video）             → 「删除分镜图组」/…
//   分镜组（video）                  → 「删除分镜视频组」/…
//   都没有（普通节点）               → 走 deleteNodeConfirmTitle/Message
// 但**手册一个字都没记**（只记了文件夹/画布的确认框）。
//
// ⚠️⛔ 安全边界：本脚本**只点「取消」**，绝不点「确定删除/继续删除」。
//    ⛔ 不用 ⌘A（全选）、不按 ⌫。只选中**一个**普通节点、按 Delete 打开框、读完就取消。
//    （`connect-nodes.md` 记录：Delete 打开的是确认框，⌘Z 也能兜底。）
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchED1.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = { 读数: {} };

/** 画布上的节点清单（data-id + 类型 class）。 */
const 读节点 = (page) => page.evaluate(() => {
  return [...document.querySelectorAll('.react-flow__node')].map(n => ({
    id: n.getAttribute('data-id'),
    cls: n.className.toString().split(' ').filter(c => c.startsWith('react-flow__node-')).join(','),
    type: n.getAttribute('data-node-type') || n.getAttribute('data-type') || '',
    rect: (() => { const r = n.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; })(),
  }));
});

/** 读所有确认框的 title / 正文 / 按钮。 */
const 读确认框 = (page) => page.evaluate(() => {
  const roots = [...document.querySelectorAll('.mantine-Modal-content')];
  return roots.map(r => ({
    全文: r.innerText,
    标题: r.querySelector('h2,h3,.mantine-Modal-title')?.innerText || '',
    按钮: [...r.querySelectorAll('button')].map(b => b.innerText.trim()).filter(Boolean),
  }));
});

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 4500 });
  await closePromos(page);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(800);

  const 节点 = await 读节点(page);
  结果.读数.节点清单 = 节点;
  console.log('═══ 画布节点清单 ═══');
  for (const n of 节点) console.log(`  ${n.id}  type="${n.type}"  cls="${n.cls}"`);
  落盘(结果);

  // 选一个**普通节点**（排除 group / 分镜），点它的中心
  const 普通 = 节点.find(n => !/group/i.test(n.cls) && !/shot|script/i.test(n.cls));
  console.log('\n>>> 选中:', 普通?.id, 普通?.cls);

  if (普通) {
    const cx = 普通.rect[0] + 普通.rect[2] / 2;
    const cy = 普通.rect[1] + 普通.rect[3] / 2;
    await page.mouse.click(cx, cy);
    await page.waitForTimeout(900);
    const 选中态 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
    结果.读数.选中后 = 选中态;
    console.log('  选中态:', JSON.stringify(选中态));
    落盘(结果);

    // ⚠️ 按 Delete —— 目的是弹确认框，**只点取消**
    await page.keyboard.press('Delete');
    await page.waitForTimeout(1000);

    const 框 = await 读确认框(page);
    结果.读数.确认框 = 框;
    console.log('\n═══ ⭐ 删节点确认框 ═══');
    if (!框.length) console.log('  （没有弹出确认框）');
    for (const f of 框) {
      console.log('  标题:', f.标题);
      console.log('  按钮:', JSON.stringify(f.按钮));
      console.log('  全文:', f.全文);
    }
    await page.screenshot({ path: '.evidence/batchED1-删节点确认框.png' });
    落盘(结果);

    // ⛔ 只点「取消」
    const 取消 = page.locator('.mantine-Modal-content button:has-text("取消")').first();
    if (await 取消.count()) {
      await 取消.click();
      await page.waitForTimeout(700);
      console.log('\n  >>> 已点「取消」');
    }
    const 后 = await 读节点(page);
    结果.读数.取消后节点数 = 后.length;
    结果.读数.基线节点数 = 节点.length;
    console.log(`  节点数 基线 ${节点.length} → 取消后 ${后.length}（应相等）`);
    落盘(结果);
  }
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchED1.json ===');
}
