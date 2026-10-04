// Batch EW-8：⭐⭐ 揪出「新功能：支持真人」的**触发元素本体**。
//
// EW-7 已经定死归属：平移画布 (+260,+150) 时
//   气泡位移 [260,150]、节点卡位移 [260,150]、卡内「文生视频」位移 [260,150]，
//   而顶栏「全能创作」和通知 toast「开启」都是 [0,0]。
//   ⇒ **它逐像素跟着「视频节点 3」这张卡片走，归属就是这张卡。**
//
// 还差最后一环：它挂在**卡片里哪一个元素**上？
// Mantine 用 floating-ui 定位，位置由触发元素的矩形决定。
// 气泡在卡的**左边 24px、下边 147px**（卡高 161）⇒ 触发元素应该在卡的左下角附近。
//
// ⭐ 本轮枚举卡片内的**每一个**后代元素，**包含 0×0 的**（很多 tooltip 触发器
// 就是包在图标外面的零尺寸 span），按「离气泡中心的距离」排序。
// ⛔ 前几轮都漏了 0 尺寸元素 —— 这正是「按 `cursor-help` 找、找不到」的原因之一。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEW8.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;
try {
  await open(page, CANVAS_URL);
  await closePromos(page);
  await page.waitForTimeout(4000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  const p = await page.evaluate(() => {
    const el = document.querySelector('.react-flow__node[data-id="v-v2hlWY4Br3"]');
    const r = el.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + 14)];
  });
  const 验 = await page.evaluate(([x, y]) => {
    const n = document.elementFromPoint(x, y)?.closest('.react-flow__node');
    return n ? n.getAttribute('data-id') : null;
  }, p);
  if (验 !== 'v-v2hlWY4Br3') throw new Error('落点不对：' + 验);
  await page.mouse.click(p[0], p[1]);
  await page.waitForTimeout(2500);

  const 读 = await page.evaluate(() => {
    const 框 = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; };
    let 泡 = null;
    for (const e of document.querySelectorAll('[class*="mantine-Tooltip-tooltip"]')) {
      if ((e.innerText || '').trim() === '新功能：支持真人' && parseFloat(getComputedStyle(e).opacity) >= 0.5) { 泡 = e; break; }
    }
    if (!泡) return { 找到: false };
    const 卡 = document.querySelector('.react-flow__node[data-id="v-v2hlWY4Br3"]');
    const 泡框 = 框(泡);
    const 卡框 = 框(卡);
    // ⭐ 枚举卡内**所有**后代，含 0 尺寸
    const 列 = [];
    const 走 = (根, 深度) => {
      for (const c of 根.children) {
        const b = 框(c);
        const cs = getComputedStyle(c);
        列.push({
          深度, 标签: c.tagName,
          文字: (c.innerText || '').trim().slice(0, 22),
          cls: String(c.className).slice(0, 80),
          box: b, 宽: b[2], 高: b[3],
          display: cs.display, visibility: cs.visibility, opacity: cs.opacity,
          光标: cs.cursor, position: cs.position,
          子数: c.children.length,
          html: c.outerHTML.slice(0, 220),
        });
        if (深度 < 12) 走(c, 深度 + 1);
      }
    };
    走(卡, 1);
    // 按「离气泡左下角 / 离气泡中心」的距离排
    const 泡心 = [泡框[0] + 泡框[2] / 2, 泡框[1] + 泡框[3] / 2];
    const 距 = (b) => Math.hypot(b[0] + b[2] / 2 - 泡心[0], b[1] + b[3] / 2 - 泡心[1]);
    列.sort((a, b) => 距(a.box) - 距(b.box));
    return { 找到: true, 泡框, 卡框, 泡心, 相对卡: [泡框[0] - 卡框[0], 泡框[1] - 卡框[1]], 总数: 列.length, 最近: 列.slice(0, 14) };
  });
  记('⭐ 气泡框 ' + JSON.stringify(读.泡框) + '　卡框 ' + JSON.stringify(读.卡框) + '　相对卡 ' + JSON.stringify(读.相对卡));
  记('卡内后代共 ' + 读.总数 + ' 个（含 0 尺寸）。离气泡最近的 14 个：');
  for (const x of 读.最近) {
    记(`  深度${x.深度} ${x.标签} ${JSON.stringify(x.box)} ${x.宽}×${x.高} 文字${JSON.stringify(x.文字)} 光标${x.光标} display${x.display}`);
    记(`      cls=${x.cls}`);
  }
  结果.读数.读 = 读;

  await page.screenshot({ path: EVID + 'ew8-卡片与气泡.png' });
  记('已拍 ew8-卡片与气泡.png');

  await page.mouse.click(40, 700);
  await page.waitForTimeout(1200);
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
  console.log('\n=== 已写 tools/batchEW8.json ===');
}
