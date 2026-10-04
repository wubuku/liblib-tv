// Batch EV-4：⭐⭐⭐ 拖拽 A/B —— 「网格吸附」到底会不会真的对齐。
//
// 到这一步为止已经拿到两路互证的步长：
//   · DOM 路：`<pattern width="16.0517" patternUnits="userSpaceOnUse">`，zoom 0.458621
//     ⇒ 16.0517 / 0.458621 = **35.00 画布单位**（精确到小数第 6 位）
//   · 像素路：把画布平移到空白区拍图，自相关基频 **32 图像像素 = 16.0 CSS px**
//     ⇒ 16.0 / 0.458621 = 34.89（量化到半像素，落在 35 上）
//
// ⭐⭐⭐ 而 Batch EH 当时试的步长是 **4 / 8 / 10 / 20** —— **一个都不是 35**。
//   它必然测不到吸附，然后据此写下「点了没用」。**这是判据缺陷，不是产品缺陷。**
//
// 本轮做受控 A/B：**同一个节点、同样的屏幕位移**，吸附关 / 吸附开各做 3 组。
//   看的是「落点相对 35 的余数」：关着应该五花八门，开着应该一律贴 0。
//
// ⭐⭐ 安全要点（本轮踩到的真坑）：
//   **开着吸附时根本停不到任意坐标上** —— 这本身就是结论的一部分。
//   所以复原顺序必须是：**先关掉吸附，再把节点拖回基线**，反过来会卡在网格线上回不去。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEV4.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 目标 = 'a-THmbuJXQj4';           // 基线 [-1356, 600]，卡片 161×161，整体在视口内
const 基线 = 坐标[目标];

const browser = await launch();
const page = browser.page;

/** 读视口变换 */
const 读变换 = () => page.evaluate(() => {
  const vp = document.querySelector('.react-flow__viewport');
  if (!vp) return null;
  const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(vp).transform);
  if (!m) return null;
  const n = m[1].split(',').map(Number);
  return { zoom: n[0], panX: n[4], panY: n[5] };
});

/** 读节点当前画布坐标 + 屏幕中心 */
const 读节点 = (id) => page.evaluate((nid) => {
  const el = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!el) return null;
  const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(el.style.transform || '');
  const r = el.getBoundingClientRect();
  return {
    画布: m ? [parseFloat(m[1]), parseFloat(m[2])] : null,
    中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
    宽: Math.round(r.width), 高: Math.round(r.height),
  };
}, id);

/** 枚举底栏（不按名字查） */
const 枚举底栏 = () => page.evaluate(() => {
  const out = [];
  for (const e of document.querySelectorAll('button')) {
    const r = e.getBoundingClientRect();
    if (r.top < 740 || r.bottom > 810 || r.left > 340) continue;
    if (e.querySelector('button')) continue;
    out.push({
      aria: e.getAttribute('aria-label'),
      中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      svg数: e.querySelectorAll('svg').length,
    });
  }
  return out;
});

/** 切「网格吸附」，用枚举 + svg 数判断，不依赖名字一定查得到 */
const 切吸附 = async (想要开) => {
  const 栏 = await 枚举底栏();
  const 枚 = 栏.find((b) => b.svg数 === 1 || b.svg数 === 2);
  // ⭐ 靠 svg 数锁定：1 = 关，2 = 开。不用名字，避免改名型开关把自己找丢。
  const 现在开 = !!枚 && 枚.svg数 === 2;
  if (现在开 === 想要开) return { 已开: 现在开, 枚, 动作: '无需切换' };
  const [x, y] = 枚.中心;
  const 验 = await page.evaluate(([px, py]) => {
    const e = document.elementFromPoint(px, py);
    return { 标签: e ? e.tagName : null, aria: e ? e.getAttribute('aria-label') : null, 最近按钮: !!(e && e.closest('button')) };
  }, [x, y]);
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.mouse.up();
  await page.waitForTimeout(900);
  await page.mouse.move(700, 300);           // ⭐ 把鼠标移开，否则背景色被悬停污染
  await page.waitForTimeout(400);
  const 栏2 = await 枚举底栏();
  const 枚2 = 栏2.find((b) => b.svg数 === 1 || b.svg数 === 2);
  return { 已开: !!枚2 && 枚2.svg数 === 2, 枚: 枚2, 落点自证: 验, 动作: 想要开 ? '点开' : '点关' };
};

/** ⭐ 按画布坐标把节点拖到目标画布坐标（三铁律：坐标驱动 + 落点自证） */
const 拖到 = async (id, tx, ty) => {
  const 变 = await 读变换();
  const 前 = await 读节点(id);
  if (!前 || !前.画布) throw new Error('读不到节点 ' + id);
  const [cx, cy] = 前.中心;
  // 三铁律②：按下去之前先验落点属于目标节点
  const 验 = await page.evaluate(([px, py, nid]) => {
    const e = document.elementFromPoint(px, py);
    const n = e ? e.closest('.react-flow__node') : null;
    return { 落点id: n ? n.getAttribute('data-id') : null, 正确: !!(n && n.getAttribute('data-id') === nid) };
  }, [cx, cy, id]);
  if (!验.正确) throw new Error('落点不是目标节点：' + JSON.stringify(验));
  // 三铁律①：Δscreen = Δcanvas × zoom
  const dx = Math.round((tx - 前.画布[0]) * 变.zoom);
  const dy = Math.round((ty - 前.画布[1]) * 变.zoom);
  await page.mouse.move(cx, cy);
  await page.mouse.down();
  for (let i = 1; i <= 10; i++) {
    await page.mouse.move(cx + Math.round((dx * i) / 10), cy + Math.round((dy * i) / 10));
    await page.waitForTimeout(25);
  }
  await page.mouse.up();
  await page.waitForTimeout(700);
  const 后 = await 读节点(id);
  return { 前画布: 前.画布, 后画布: 后 ? 后.画布 : null, 请求屏幕位移: [dx, dy], 落点自证: 验, zoom: 变.zoom };
};

try {
  await open(page, CANVAS_URL);
  await closePromos(page);
  await page.waitForTimeout(4000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));
  结果.读数.基线坐标 = 基线;

  const 样本 = [[60, 40], [-83, 57], [44, -66]];   // 屏幕像素位移，三组互不成倍数

  // ════════ 阶段 A：吸附**关**（阴性对照）════════
  const 切A = await 切吸附(false);
  记('阶段A 吸附状态：' + JSON.stringify(切A));
  const A = [];
  for (const [dx, dy] of 样本) {
    const 起 = await 读节点(目标);
    const 变 = await 读变换();
    const 目标画布 = [起.画布[0] + Math.round(dx / 变.zoom), 起.画布[1] + Math.round(dy / 变.zoom)];
    const r = await 拖到(目标, 目标画布[0], 目标画布[1]);
    const 实际位移 = [r.后画布[0] - r.前画布[0], r.后画布[1] - r.前画布[1]];
    const 行 = {
      请求屏幕: [dx, dy], 请求画布: [目标画布[0] - r.前画布[0], 目标画布[1] - r.前画布[1]],
      实际画布位移: 实际位移, 落点: r.后画布,
      对35的余数: [+(r.后画布[0] % 35).toFixed(2), +(r.后画布[1] % 35).toFixed(2)],
    };
    A.push(行);
    记('  A ' + JSON.stringify(行));
    await 拖到(目标, 基线[0], 基线[1]);          // 回基线
  }
  结果.读数.阶段A_吸附关 = A;

  // ════════ 阶段 B：吸附**开**（阳性对照）════════
  const 切B = await 切吸附(true);
  记('阶段B 吸附状态：' + JSON.stringify(切B));
  const B = [];
  for (const [dx, dy] of 样本) {
    const 起 = await 读节点(目标);
    const 变 = await 读变换();
    const 目标画布 = [起.画布[0] + Math.round(dx / 变.zoom), 起.画布[1] + Math.round(dy / 变.zoom)];
    const r = await 拖到(目标, 目标画布[0], 目标画布[1]);
    const 实际位移 = [r.后画布[0] - r.前画布[0], r.后画布[1] - r.前画布[1]];
    const 行 = {
      请求屏幕: [dx, dy], 请求画布: [目标画布[0] - r.前画布[0], 目标画布[1] - r.前画布[1]],
      实际画布位移: 实际位移, 落点: r.后画布,
      对35的余数: [+(r.后画布[0] % 35).toFixed(2), +(r.后画布[1] % 35).toFixed(2)],
    };
    B.push(行);
    记('  B ' + JSON.stringify(行));
    // ⭐ 这里**不**急着回基线：先记录开着吸附时能不能停在基线上（这本身是结论）
    await 拖到(目标, 基线[0], 基线[1]);
    const 试回 = await 读节点(目标);
    记('    ⭐ 开着吸附拖回基线 → 实际 ' + JSON.stringify(试回.画布) + ' 差 ' +
      JSON.stringify([+(试回.画布[0] - 基线[0]).toFixed(2), +(试回.画布[1] - 基线[1]).toFixed(2)]));
    结果.读数.开着吸附拖回基线 = { 目标: 基线, 实际: 试回.画布, 差: [试回.画布[0] - 基线[0], 试回.画布[1] - 基线[1]] };
  }
  结果.读数.阶段B_吸附开 = B;

  await page.screenshot({ path: EVID + 'ev4-吸附开启中.png' });
  记('已拍 ev4-吸附开启中.png');

  // ════════ 复原：⭐ 先关吸附，再回基线 ════════
  const 切回 = await 切吸附(false);
  记('复原：吸附状态 ' + JSON.stringify(切回.已开));
  const 回 = await 拖到(目标, 基线[0], 基线[1]);
  记('拖回基线：' + JSON.stringify(回.后画布));
  结果.读数.复原拖回 = 回;

  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后坐标复核：' + JSON.stringify(偏差));
  结果.收尾 = { 偏差, 已渲染: Object.keys(await 读全部坐标(page)).length, 吸附最后状态: (await 切吸附(false)).已开 };
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  落盘(结果);
  await browser.browser.close();
  console.log('\n=== 已写 tools/batchEV4.json ===');
}
