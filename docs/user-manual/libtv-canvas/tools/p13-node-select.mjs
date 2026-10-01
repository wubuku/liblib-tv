// 探针 13 —— 弄清「选中一个节点之后能对它做什么」，特别是删除到底走哪条路。
//
// 为什么专门查：clearCanvas 用 force click + Delete 连着几轮都删不掉节点，
// 截图里一直挂着上一轮的残留节点。与其猜快捷键，不如把选中态的真实工具条读出来。
import { launch, open } from './lib.mjs';
import { CANVAS_URL } from './test-project.mjs';
import { clearToasts, closePromos, shot } from './scenario.mjs';
import { nodeCount, listNodes, clearCanvas } from './canvas-ops.mjs';

const { browser, page } = await launch();

try {
  await open(page, CANVAS_URL, { settle: 4000 });
  await closePromos(page);
  await clearToasts(page);
  await page.waitForTimeout(1000);
  console.log('起始节点:', await nodeCount(page));

  // 先建一个文本节点 —— 上一次跑这脚本时画布是空的，压根点不到节点。
  await page.getByRole('button', { name: '添加节点', exact: true }).first().click();
  await page.waitForTimeout(900);
  await page.locator('[data-guide-lockable-portal="true"], [data-canvas-menu-portal="true"]').first().getByText('文本').first().click();
  await page.waitForTimeout(2500);
  console.log('建完节点:', await nodeCount(page));

  // 选中第一个节点，看浮出什么东西
  const n0 = page.locator('.react-flow__node').first();
  await n0.click({ force: true });
  await page.waitForTimeout(1200);

  const sel = await page.evaluate(() => {
    const node = document.querySelector('.react-flow__node.selected') || document.querySelector('.react-flow__node');
    const btns = [...document.querySelectorAll('button')].filter((b) => {
      const r = b.getBoundingClientRect();
      return r.width > 8 && r.height > 8;
    }).map((b) => {
      const r = b.getBoundingClientRect();
      return { aria: b.getAttribute('aria-label'), title: b.getAttribute('title'), text: (b.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 20), xy: [Math.round(r.x), Math.round(r.y)] };
    });
    // 只报节点附近（上/下/左/右 200px 内）的按钮，那才是节点工具条
    const nr = node.getBoundingClientRect();
    const near = btns.filter((b) => b.xy[0] > nr.x - 240 && b.xy[0] < nr.right + 240 && b.xy[1] > nr.y - 120 && b.xy[1] < nr.bottom + 120);
    return {
      nodeClasses: node.className,
      nearButtons: near,
      allAria: [...new Set(btns.map((b) => b.aria).filter(Boolean))],
    };
  });
  console.log('节点类名:', sel.nodeClasses);
  console.log('节点附近按钮:', JSON.stringify(sel.nearButtons, null, 1));
  console.log('页面上出现过的 aria-label:', JSON.stringify(sel.allAria));
  await shot(page, 'p13-node-selected.png');

  // 逐种删除方式试一遍
  for (const how of ['Delete', 'Backspace']) {
    const before = await nodeCount(page);
    if (!before) break;
    await page.locator('.react-flow__node').first().click({ force: true });
    await page.waitForTimeout(400);
    await page.keyboard.press(how);
    await page.waitForTimeout(1400);
    console.log(`按 ${how}: ${before} -> ${await nodeCount(page)}`);
  }

  const cleared = await clearCanvas(page);
  console.log('clearCanvas 结果:', JSON.stringify(cleared));
  console.log('剩余:', JSON.stringify(await listNodes(page)));
  await shot(page, 'p13-after-clear.png');
} finally {
  await browser.close();
}
