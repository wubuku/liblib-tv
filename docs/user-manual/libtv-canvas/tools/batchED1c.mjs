// Batch ED-1c：复位视图后重测「删节点确认框」。
//
// ⭐⭐ ED-1/ED-1b 失败的真因（ED-1b 才抓到）：**EB 批把测试画布留在了 800% 缩放**
//    （`viewport transform: matrix(8,0,0,8,…)`），于是：
//      · 那个 4976×2800 的「巨型节点」其实是放大后的内容；
//      · 其余 10 个节点全在视口外，点都点不到。
//    ⇒ **不是页面没加载，是我没复位视图。** 这是「测完要复位」的一次现场复发。
//
// 本步：先 `⌘0` 适合屏幕（纯视图，不写数据），确认 11 个节点都在视口里，
//      再选**一个普通节点**按 Delete，**只读框、只点取消**。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchED1c.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = { 读数: {} };

const 读全部 = (page) => page.evaluate(() => {
  const W = window.innerWidth, H = window.innerHeight;
  const vp = document.querySelector('.react-flow__viewport');
  const nodes = [...document.querySelectorAll('.react-flow__node')].map(n => {
    const r = n.getBoundingClientRect();
    return {
      id: n.getAttribute('data-id'),
      cls: n.className.toString().split(' ').filter(c => c.startsWith('react-flow__node-')).join(','),
      rect: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      在视口内: r.right > 0 && r.bottom > 0 && r.left < W && r.top < H,
    };
  });
  return { 缩放: vp ? getComputedStyle(vp).transform : null, 节点总数: nodes.length, 节点: nodes };
});

const 读确认框 = (page) => page.evaluate(() =>
  [...document.querySelectorAll('.mantine-Modal-content')].map(r => ({
    全文: r.innerText,
    按钮: [...r.querySelectorAll('button')].map(b => b.innerText.trim()).filter(Boolean),
  })));

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6000 });
  await closePromos(page);
  await page.waitForTimeout(1200);

  const 前 = await 读全部(page);
  console.log('复位前: 缩放=', 前.缩放, '节点数=', 前.节点总数);
  落盘(结果);

  // ⭐ 复位：⌘0 适合屏幕
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1600);

  const 后 = await 读全部(page);
  结果.读数.复位后 = 后;
  console.log('\n复位后: 缩放=', 后.缩放, '节点数=', 后.节点总数,
    '在视口内=', 后.节点.filter(n => n.在视口内).length);
  console.log('\n节点明细:');
  for (const n of 后.节点) console.log(`  ${n.id}  ${n.cls}  在视口内=${n.在视口内}`);
  落盘(结果);

  // 选一个普通（非组、非 video 巨物）节点
  const 目标 = 后.节点.find(n => n.在视口内 && n.rect[2] < 600 && n.rect[3] < 600
    && !/group/i.test(n.cls));
  console.log('\n>>> 目标节点:', 目标?.id, 目标?.cls, 目标?.rect);

  if (目标) {
    const cx = 目标.rect[0] + 目标.rect[2] / 2;
    const cy = 目标.rect[1] + 目标.rect[3] / 2;
    await page.mouse.click(cx, cy);
    await page.waitForTimeout(1000);
    const 选中 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
    console.log('  选中态:', JSON.stringify(选中));
    结果.读数.选中后 = 选中;
    落盘(结果);

    // ⛔ 只点取消
    await page.keyboard.press('Delete');
    await page.waitForTimeout(1200);
    const 框 = await 读确认框(page);
    结果.读数.确认框 = 框;
    console.log('\n═══ ⭐ 删节点确认框 ═══');
    if (!框.length) console.log('  （没弹出确认框）');
    for (const f of 框) {
      console.log('  按钮:', JSON.stringify(f.按钮));
      console.log('  全文:\n   ', f.全文.replace(/\n/g, '\n    '));
    }
    await page.screenshot({ path: '.evidence/batchED1c-删节点确认框.png' });
    落盘(结果);

    const 取消 = page.locator('.mantine-Modal-content button:has-text("取消")').first();
    if (await 取消.count()) { await 取消.click(); await page.waitForTimeout(800); console.log('  >>> 已点取消'); }
    const 末 = await 读全部(page);
    console.log(`  节点数: 复位后 ${后.节点总数} → 取消后 ${末.节点总数}`);
    结果.读数.末节点数 = 末.节点总数;
    落盘(结果);
  }
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchED1c.json ===');
}
