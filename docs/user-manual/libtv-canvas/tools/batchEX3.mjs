// Batch EX-3：⭐⭐ 「开关翻开时，悬停气泡的文案跟不跟着改？」
//
// EU 批已经坐实：`隐藏节点连线` 的 **`aria-label` 会改名** ⇄ `显示节点连线`。
// 但**悬停气泡的文案**从来没读过 —— 两者是**两个不同的来源**，
// 改名这件事不一定波及气泡。EX-1 的细扫读到的气泡文案是 `隐藏节点连线`（关态），
// 开态的还没读。
//
// 本轮只做这一件事：关态读一次 → 点开 → 开态读一次 → 点回 → 复原读一次。
// ⭐ 三次读数放一起，才能区分「文案跟着改」「文案不变」「气泡整个消失」。
//
// ⚠️ 定位方式沿用 EU/EV 定的规矩：**底栏按 left 排序 + svg 数筛 + aria 交叉验**，
//    不用下标、不用名字单条件。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEX3.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

const 读气泡 = (page) => page.evaluate(() => {
  const 出 = [];
  for (const e of document.querySelectorAll('[class*="mantine-Tooltip-tooltip"]')) {
    const r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    if (parseFloat(getComputedStyle(e).opacity) < 0.5) continue;
    出.push({ 文字: (e.innerText || '').trim().slice(0, 40), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
  }
  return 出;
});

/** 底栏按 left 排序；用「svg 数会变 + aria 会改名」这组特征锁定那一枚 */
const 底栏 = () => page.evaluate(() => {
  const out = [];
  for (const e of document.querySelectorAll('button')) {
    const r = e.getBoundingClientRect();
    if (r.top < 740 || r.bottom > 810 || r.left > 340) continue;
    if (e.querySelector('button')) continue;
    out.push({ aria: e.getAttribute('aria-label'), 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], left: Math.round(r.left), svg数: e.querySelectorAll('svg').length });
  }
  out.sort((a, b) => a.left - b.left);
  return out;
});

/** 锁定目标：底栏里「aria 里带『节点连线』」的那枚（改名后仍含「节点连线」）*/
const 锁定 = (栏) => 栏.find((b) => (b.aria || '').includes('节点连线')) || 栏.find((b) => b.svg数 === 1 || b.svg数 === 2);

const 读这一枚 = async (标签) => {
  const 栏 = await 底栏();
  const 枚 = 锁定(栏);
  if (!枚) { 记(`${标签}：锁定不到`); return null; }
  await page.mouse.move(枚.中心[0], 枚.中心[1]);
  await page.waitForTimeout(1200);
  const 泡 = await 读气泡(page);
  const 出 = { 标签, aria: 枚.aria, svg数: 枚.svg数, 中心: 枚.中心, 气泡: 泡 };
  记(`${标签}：aria=${枚.aria} svg=${枚.svg数} → 气泡=${JSON.stringify(泡)}`);
  return 出;
};

try {
  await open(page, CANVAS_URL);
  await closePromos(page);
  await page.waitForTimeout(4000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('button')) {
      const t = (b.innerText || '').trim();
      if (t === '知道了' || t === '开启') { try { b.click(); } catch (e) {} }
    }
  });
  await page.waitForTimeout(1200);

  const 栏0 = await 底栏();
  记('底栏：' + JSON.stringify(栏0.map((b) => ({ a: b.aria, svg: b.svg数, left: b.left }))));

  // 关态
  const 关 = await 读这一枚('关态');
  await page.mouse.move(700, 300);
  await page.waitForTimeout(700);

  // 点开
  // ⛔⛔ 修一个刚犯的错：第一版在 `读这一枚` 之后把鼠标移到了 (700,300)「清场」，
  //    然后**直接 down/up** —— 点击根本没落在按钮上，三态读数当然一模一样。
  //    ⇒ **清场之后必须把指针移回目标再点**，并且点前重新自证落点。
  const 枚 = 锁定(栏0);
  await page.mouse.move(枚.中心[0], 枚.中心[1]);
  await page.waitForTimeout(400);
  const 验 = await page.evaluate(([x, y]) => {
    const b = document.elementFromPoint(x, y)?.closest('button');
    return b ? b.getAttribute('aria-label') : null;
  }, 枚.中心);
  记('点击前自证落点 aria=' + 验 + '（必须等于「隐藏节点连线」，否则中止）');
  if (验 !== '隐藏节点连线') throw new Error('落点不对，中止：' + 验);
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(1200);
  await page.mouse.move(700, 300); await page.waitForTimeout(800);

  // 开态
  const 开 = await 读这一枚('开态');
  await page.screenshot({ path: EVID + 'ex3-开态底栏.png', clip: { x: 0, y: 720, width: 340, height: 90 } });
  记('已拍 ex3-开态底栏.png');
  await page.mouse.move(700, 300); await page.waitForTimeout(700);

  // 点回（同样先移回按钮再点）
  const 枚2 = 锁定(await 底栏());
  await page.mouse.move(枚2.中心[0], 枚2.中心[1]);
  await page.waitForTimeout(400);
  const 验2 = await page.evaluate(([x, y]) => {
    const b = document.elementFromPoint(x, y)?.closest('button');
    return b ? b.getAttribute('aria-label') : null;
  }, 枚2.中心);
  记('点回前自证落点 aria=' + 验2);
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(1200);
  await page.mouse.move(700, 300); await page.waitForTimeout(800);

  // 复原态
  const 回 = await 读这一枚('复原态');

  结果.读数.三态 = { 关, 开, 回 };
  记('⭐⭐ 三态对比：');
  记(`   aria  : 关=${关 && 关.aria} | 开=${开 && 开.aria} | 回=${回 && 回.aria}`);
  记(`   气泡  : 关=${JSON.stringify(关 && 关.气泡)}`);
  记(`          开=${JSON.stringify(开 && 开.气泡)}`);
  记(`          回=${JSON.stringify(回 && 回.气泡)}`);

  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后坐标复核：' + JSON.stringify(偏差));
  结果.收尾 = { 偏差, 已渲染: Object.keys(await 读全部坐标(page)).length, 复原aria: 回 && 回.aria };
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  落盘(结果);
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchEX3.json ===');
}
