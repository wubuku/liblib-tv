// Batch EH-1：网格吸附「点了没反应」—— ⭐ 先确认它**到底翻没翻**。
//
// 源码结论（10v03g6udfcrl.js）：
//   Y = useCanvasStore(e => e.snapToGrid)          ← 全局 store 字段
//   Y ? <Check/> : <svg class="absolute inset-0">  ← 开了打勾、没开叠斜杠
//   aria-label = f("canvas:snapToGrid")
//   ⚠️ 与「隐藏节点连线」完全同构（同一个 canvas store 的两个 boolean）
//   ⚠️ 且 !ea（只读/非 owner）时按钮**根本不渲染**
//
// 本步只读状态：点一次 → 读按钮内 svg 结构的变化 → 再点回来 → 读复原。
// ⛔ 不拖任何节点。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEH1.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

/** ⭐ 读网格吸附按钮的**内部结构指纹**（svg 数量、各自 class）。 */
const 读按钮 = (page) => page.evaluate(() => {
  const out = {};
  for (const aria of ['网格吸附', '隐藏节点连线', '画布小地图', '整理画布，Option+Shift+F']) {
    const b = document.querySelector(`button[aria-label="${aria}"]`);
    if (!b) { out[aria] = '按钮不存在'; continue; }
    const span = b.querySelector('span');
    out[aria] = {
      存在: true,
      box: (() => { const r = b.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; })(),
      svg数: b.querySelectorAll('svg').length,
      // ⭐ 每个 svg 的 class —— 判「打勾」还是「斜杠」的关键
      svg: [...b.querySelectorAll('svg')].map(s => s.getAttribute('class') || '').slice(0, 3),
      背景: getComputedStyle(b).backgroundColor,
    };
  }
  return out;
});

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
  await closePromos(page);
  await page.waitForTimeout(1200);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1500);

  const 开前 = await 读按钮(page);
  结果.读数.开前 = 开前;
  记(`开前 网格吸附：${JSON.stringify(开前['网格吸附'])}`);
  记(`  对照 隐藏节点连线：${JSON.stringify(开前['隐藏节点连线'])}`);

  // 点一次
  const 点了 = await page.evaluate(() => {
    const b = document.querySelector('button[aria-label="网格吸附"]');
    if (!b) return false; b.click(); return true;
  });
  await page.waitForTimeout(1300);
  const 开后 = await 读按钮(page);
  结果.读数.开后 = 开后;
  记(`点了：${点了} → 网格吸附：${JSON.stringify(开后['网格吸附'])}`);

  // ⭐ 变了没有？
  const 变了吗 = JSON.stringify(开前['网格吸附']?.svg) !== JSON.stringify(开后['网格吸附']?.svg)
    || JSON.stringify(开前['网格吸附']?.背景) !== JSON.stringify(开后['网格吸附']?.背景);
  记(`⭐ 按钮视觉是否变化：${变了吗 ? '✅ 变了' : '⛔ 没变'}`);

  // ⭐⭐ 阳性对照：点「隐藏节点连线」，看它的按钮会不会变（证明这套判据本身有效）
  await page.evaluate(() => {
    const b = document.querySelector('button[aria-label="隐藏节点连线"]');
    if (b) b.click();
  });
  await page.waitForTimeout(1300);
  const 对照 = await 读按钮(page);
  记(`⭐ 阳性对照（隐藏节点连线）点后：${JSON.stringify(对照['隐藏节点连线'])}`);
  记(`  它的 aria 是否变成了 showNodeEdges：见 aria 读数`);
  结果.读数.阳性对照 = 对照;
  // 点回来
  await page.evaluate(() => {
    for (const a of ['显示节点连线', '隐藏节点连线']) {
      const b = document.querySelector(`button[aria-label="${a}"]`);
      if (b) { b.click(); return; }
    }
  });
  await page.waitForTimeout(1200);
  const 复原 = await 读按钮(page);
  记(`复原后 隐藏节点连线：${JSON.stringify(复原['隐藏节点连线'])}`);
  结果.读数.复原 = 复原;

  // ⭐ 网格吸附也点回来
  await page.evaluate(() => {
    const b = document.querySelector('button[aria-label="网格吸附"]');
    if (b) b.click();
  });
  await page.waitForTimeout(1200);
  const 网复 = await 读按钮(page);
  记(`点回后 网格吸附：${JSON.stringify(网复['网格吸附'])}`);
  结果.读数.网格复原 = 网复;
  落盘(结果);
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEH1.json ===');
}
