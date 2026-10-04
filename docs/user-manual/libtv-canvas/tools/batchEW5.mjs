// Batch EW-5：⭐⭐⭐ **全视口悬停扫描** —— 一次把所有「会出气泡的点」连同气泡文案全找出来。
//
// 前面几轮都在「猜触发者」：ET 逐枚试了 3 枚 `.cursor-help`，EW-4 又试了导演台节点标题栏，
// 全都没命中。**逐枚试是低效的，而且容易漏。**
//
// 本轮换穷举：把指针按网格扫过**整个视口**，每到一个点就问一句
// 「此刻页面上有没有 Mantine 气泡、是什么字、在哪」。
// 把**所有出现过的 (触发点, 文案, 气泡位置)** 收成一张表。
// ⭐ 触发者就是「指针一移过去气泡就冒出来」的那个点 —— **不用猜，扫出来就是。**
//
// 这是差分法：靠「移动指针 ⇒ 出现/消失」来认触发，不靠 class、不靠 aria、不靠逐枚试。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEW5.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

/** 读此刻页面上所有 Mantine 气泡 */
const 读气泡 = (page) => page.evaluate(() => {
  const 出 = [];
  for (const e of document.querySelectorAll('[class*="mantine-Tooltip-tooltip"]')) {
    const r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    const cs = getComputedStyle(e);
    if (parseFloat(cs.opacity) < 0.5) continue;     // 只算真显示着的
    出.push({ 文字: (e.innerText || '').trim().slice(0, 40), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
  }
  return 出;
});

/** 指针下面是什么 */
const 读落点 = (page, x, y) => page.evaluate(([px, py]) => {
  const e = document.elementFromPoint(px, py);
  if (!e) return null;
  const b = e.closest('button,[role="button"],a') || e;
  const r = e.getBoundingClientRect();
  const rb = b.getBoundingClientRect();
  return {
    标签: e.tagName,
    元素aria: b.getAttribute('aria-label'),
    元素文字: (b.innerText || '').trim().slice(0, 26),
    元素cls: String(b.className).slice(0, 70),
    元素box: [Math.round(rb.left), Math.round(rb.top), Math.round(rb.width), Math.round(rb.height)],
    指针box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
  };
}, [x, y]);

const 浏览器 = await launch();
const page = 浏览器.page;
try {
  await open(page, CANVAS_URL);
  await closePromos(page);
  await page.waitForTimeout(4000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  // 收起首访弹窗（它们会挡住扫描）
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('button')) {
      const t = (b.innerText || '').trim();
      if (t === '知道了' || t === '开启' || t === '取消') { try { b.click(); } catch (e) {} }
    }
  });
  await page.waitForTimeout(1500);

  // ① 不选中任何东西，先扫一遍（拿到画布自身的触发点）
  const 扫 = async (标签, 步长 = 56) => {
    const 命中 = new Map();
    for (let y = 30; y < 800; y += 步长) {
      for (let x = 24; x < 1420; x += 步长) {
        await page.mouse.move(x, y);
        await page.waitForTimeout(70);
        const 泡 = await 读气泡(page);
        if (!泡.length) continue;
        const 落 = await 读落点(page, x, y);
        for (const b of 泡) {
          const k = b.文字;
          if (!命中.has(k)) 命中.set(k, { 文字: k, 气泡: b.box, 触发点: [], 触发元素: null });
          const h = 命中.get(k);
          if (h.触发点.length < 6) {
            h.触发点.push([x, y]);
            if (!h.触发元素) h.触发元素 = 落;
          }
        }
      }
    }
    const 表 = [...命中.values()];
    记(`—— ${标签}：扫出 ${表.length} 种气泡 ——`);
    for (const h of 表) {
      记(`   「${h.文字}」 气泡@${JSON.stringify(h.气泡)} 触发点${JSON.stringify(h.触发点)} 元素=${h.触发元素 ? h.触发元素.标签 + '/' + (h.触发元素.元素aria || h.触发元素.元素文字 || '—') : '—'}`);
    }
    return 表;
  };

  const 未选中 = await 扫('A 未选中任何节点');
  结果.读数.未选中 = 未选中;

  // ② 选中视频节点，再扫一遍
  const p = await page.evaluate(() => {
    const el = document.querySelector('.react-flow__node[data-id="v-v2hlWY4Br3"]');
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + 18)];
  });
  const 验 = await page.evaluate(([x, y]) => {
    const n = document.elementFromPoint(x, y)?.closest('.react-flow__node');
    return n ? n.getAttribute('data-id') : null;
  }, p);
  记('点视频节点 ' + JSON.stringify(p) + ' 落点自证=' + 验);
  if (验 === 'v-v2hlWY4Br3') {
    await page.mouse.click(p[0], p[1]);
    await page.waitForTimeout(2500);
    const 选中 = await 扫('B 选中视频节点');
    结果.读数.选中视频 = 选中;
    // 差分：哪些气泡是选中后才出现的
    const 旧 = new Set(未选中.map((h) => h.文字));
    结果.读数.新增气泡 = 选中.filter((h) => !旧.has(h.文字));
    记('⭐ 选中后新增的气泡：' + JSON.stringify(结果.读数.新增气泡, null, 1));
  }

  // 收尾
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
  console.log('\n=== 已写 tools/batchEW5.json ===');
}
