// Batch EZ-1c：⭐⭐ 键盘能不能选中那个「被完全盖住」的图片节点？
//
// EZ-1b 的读数把当年的疑问钉死了：
//   图 A `i-9nlG6HdjK2` 框 `[76,319,285,161]`，按 6px 网格扫 **1296 格**，
//   **1250 格归视频节点 `v-eMpqKtiLlx`**，只剩 **46 格**（x ∈ [352,358] 一条缝），
//   而那条缝的质心 `(355,398)` 自证回来的仍然是视频节点的一个 `<circle>`。
//   ⇒ **图 A 一个像素都点不到。**
//   ⇒ ⛔ 手册当年写的原因（「框选会把它一起圈进来」）**不够狠**：
//      真正的原因是**它根本点不到，也不框得到**。
//
// 本轮试最后一条**不动任何东西**的路：**键盘 Tab 遍历**（React Flow 的
// `selectNodesOnFocus`）。⛔ 只按 Tab，不点任何节点、不拖任何东西。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEZ1c.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

const 选中 = () => page.evaluate(() => ({
  选中: [...document.querySelectorAll('.react-flow__node.selected')].map((n) => n.getAttribute('data-id')),
  焦点: (document.activeElement && (document.activeElement.getAttribute('data-id') || document.activeElement.className || document.activeElement.tagName) || '').toString().slice(0, 40),
}));

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  // 先点空白，把焦点交给画布
  await page.mouse.move(720, 640); await page.waitForTimeout(400);
  await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(800);
  await page.mouse.move(720, 780); await page.waitForTimeout(500);
  记('点空白后：' + JSON.stringify(await 选中()));

  const 轨迹 = [];
  for (let i = 1; i <= 16; i++) {
    await page.keyboard.press('Tab');
    await page.waitForTimeout(420);
    const s = await 选中();
    轨迹.push({ 次: i, ...s });
    记(`  Tab#${i} → 选中 ${JSON.stringify(s.选中)}｜焦点 ${s.焦点}`);
    if (s.选中.length && s.选中.includes('i-9nlG6HdjK2')) {
      记('  ⭐⭐⭐ Tab 走得到图 A！');
      break;
    }
  }
  结果.读数.Tab轨迹 = 轨迹;
  const 到过 = [...new Set(轨迹.flatMap((t) => t.选中))];
  记('Tab 一共能到达的节点：' + JSON.stringify(到过));
  结果.读数.能到达 = 到过;

  // ⭐ 阳性对照：图 B（没被遮挡）能不能用普通点击选中
  记('—— 对照：普通点击图 B ——');
  const B = await page.evaluate(() => {
    const n = document.querySelector('.react-flow__node[data-id="i-sODTbgLUm1"]');
    if (!n) return null;
    const r = n.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
  });
  if (B) {
    await page.mouse.move(B[0], B[1]); await page.waitForTimeout(450);
    const v = await page.evaluate((p) => {
      const e = document.elementFromPoint(p[0], p[1]);
      const n = e ? e.closest('.react-flow__node') : null;
      return { id: n && n.getAttribute('data-id'), tag: e && e.tagName };
    }, B);
    记('  图 B 落点自证：' + JSON.stringify(v));
    if (v.id === 'i-sODTbgLUm1') {
      await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(900);
      await page.mouse.move(720, 780); await page.waitForTimeout(500);
      const s = await 选中();
      记('  ⭐ 选中结果：' + JSON.stringify(s.选中));
      结果.读数.图B可点 = s.选中;
      await page.screenshot({ path: EVID + 'ez1c-图B-普通点击选中.png' });
      记('  已拍 ez1c-图B-普通点击选中.png');
    }
  }

  await page.mouse.move(720, 640); await page.waitForTimeout(300);
  await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(600);
  记('清选区后：' + JSON.stringify(await 选中()));

  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后坐标复核：' + JSON.stringify(偏差));
  结果.收尾 = { 偏差, 已渲染: Object.keys(await 读全部坐标(page)).length };
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  落盘(结果);
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchEZ1c.json ===');
}
