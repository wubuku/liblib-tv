// Batch EV-5：⭐⭐ 重做「吸附开」的阳性对照 —— EV-4 的阶段 B 作废。
//
// ⛔ **EV-4 错在哪**：`切吸附()` 用 `栏.find(b => b.svg数 === 1 || b.svg数 === 2)`
//   取**第一枚**符合条件的按钮。底栏第一枚是 `资产管理`（svg 数也是 1），
//   于是「点开吸附」实际点到了 `整理画布，Option+Shift+F` —— **一枚完全不同的按钮**。
//   日志里能直接看到：阶段 B 记的枚是 `整理画布`、box `[334,764,28,28]`。
//   ⇒ 阶段 B 的三组落点**全部作废**，不能当成「吸附开」的读数。
//   ⭐ **判据缺陷**：「用某个属性筛出候选」之后必须**再按位置/身份交叉验一次**，
//      哪怕那个属性「在这枚按钮上恰好成立」。
//
// ⭐⭐ 本轮的正确定位方式：**按底栏从左到右的第 5 枚（索引 4）**，
//   再用 `aria === 网格吸附` 交叉验 —— 两条独立依据对上才认。
//
// 阶段 A（吸附关）的三组读数直接沿用 EV-4，它没点任何按钮：
//   落点对 35 的余数 = `[-11,24]` / `[-30,20.98]` / `[-24,20]`，**零规律**。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEV5.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 目标 = 'a-THmbuJXQj4';
const 基线 = 坐标[目标];
const 阶段A = [
  { 请求屏幕: [60, 40], 落点: [-1236, 689], 对35的余数: [-11, 24] },
  { 请求屏幕: [-83, 57], 落点: [-1500, 720.975], 对35的余数: [-30, 20.98] },
  { 请求屏幕: [44, -66], 落点: [-1284, 475], 对35的余数: [-24, 20] },
];

const browser = await launch();
const page = browser.page;

const 读变换 = () => page.evaluate(() => {
  const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(document.querySelector('.react-flow__viewport')).transform);
  const n = m[1].split(',').map(Number);
  return { zoom: n[0], panX: n[4], panY: n[5] };
});

const 读节点 = (id) => page.evaluate((nid) => {
  const el = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!el) return null;
  const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(el.style.transform || '');
  const r = el.getBoundingClientRect();
  return { 画布: m ? [parseFloat(m[1]), parseFloat(m[2])] : null, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
}, id);

/** ⭐ 枚举底栏并按 left 排序，返回带索引的清单 */
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
      cls: String(e.className).slice(0, 90),
    });
  }
  out.sort((a, b) => a.box[0] - b.box[0]);
  out.forEach((x, i) => { x.索引 = i; });
  return out;
});

/** ⭐ 定位「网格吸附」：按索引 4 + aria 交叉验，两条依据都符合才算 */
const 定位吸附 = async () => {
  const 栏 = await 枚举底栏();
  const 枚 = 栏[4];
  const 认 = !!枚 && 枚.aria === '网格吸附';
  return { 栏, 枚, 认, 开: 认 && 枚.svg数 === 2 };
};

const 切吸附 = async (想要开) => {
  const 定位 = await 定位吸附();
  if (!定位.认) throw new Error('定位不到网格吸附：' + JSON.stringify(定位.栏));
  if (定位.开 === 想要开) return { 动作: '无需切换', ...定位 };
  const [x, y] = 定位.枚.中心;
  // ⭐ 点击前自证：指针精确落在 aria=网格吸附 的按钮上
  const 验 = await page.evaluate(([px, py]) => {
    const e = document.elementFromPoint(px, py);
    const b = e ? e.closest('button') : null;
    return { 落点aria: b ? b.getAttribute('aria-label') : null, 落点box: b ? [Math.round(b.getBoundingClientRect().left), Math.round(b.getBoundingClientRect().width)] : null };
  }, [x, y]);
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.mouse.up();
  await page.waitForTimeout(1000);
  await page.mouse.move(700, 300);
  await page.waitForTimeout(400);
  const 后 = await 定位吸附();
  return { 动作: 想要开 ? '点开' : '点关', 点击自证: 验, ...后 };
};

const 拖到 = async (id, tx, ty) => {
  const 变 = await 读变换();
  const 前 = await 读节点(id);
  const [cx, cy] = 前.中心;
  const 验 = await page.evaluate(([px, py, nid]) => {
    const e = document.elementFromPoint(px, py);
    const n = e ? e.closest('.react-flow__node') : null;
    return { 落点id: n ? n.getAttribute('data-id') : null, 正确: !!(n && n.getAttribute('data-id') === nid) };
  }, [cx, cy, id]);
  if (!验.正确) throw new Error('落点不是目标节点：' + JSON.stringify(验));
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
  return { 前画布: 前.画布, 后画布: 后.画布, 请求屏幕位移: [dx, dy], 落点自证: 验 };
};

try {
  await open(page, CANVAS_URL);
  await closePromos(page);
  await page.waitForTimeout(4000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));
  结果.读数.阶段A_沿用EV4 = 阶段A;

  // 先确认当前是关的
  const 初始 = await 定位吸附();
  记('初始底栏：' + JSON.stringify(初始.栏.map((b) => ({ i: b.索引, aria: b.aria, svg: b.svg数, left: b.box[0] }))));
  记('初始定位：认=' + 初始.认 + ' 开=' + 初始.开);
  if (!初始.认) throw new Error('底栏结构与预期不符，中止');
  if (初始.开) { await 切吸附(false); }

  // ════════ 开吸附，做三组 ════════
  const 开 = await 切吸附(true);
  记('切到开：' + JSON.stringify(开));
  if (!开.开) throw new Error('点完还是关着，AB 失败');
  await page.screenshot({ path: EVID + 'ev5-吸附已开.png', clip: { x: 0, y: 740, width: 340, height: 70 } });
  记('已拍 ev5-吸附已开.png（底栏特写，看图标叠没叠斜杠）');

  const 样本 = [[60, 40], [-83, 57], [44, -66]];
  const B = [];
  for (const [dx, dy] of 样本) {
    const 起 = await 读节点(目标);
    const 变 = await 读变换();
    const 目标画布 = [起.画布[0] + Math.round(dx / 变.zoom), 起.画布[1] + Math.round(dy / 变.zoom)];
    const r = await 拖到(目标, 目标画布[0], 目标画布[1]);
    const 行 = {
      请求屏幕: [dx, dy],
      请求画布: [目标画布[0] - r.前画布[0], 目标画布[1] - r.前画布[1]],
      实际画布位移: [+(r.后画布[0] - r.前画布[0]).toFixed(2), +(r.后画布[1] - r.前画布[1]).toFixed(2)],
      落点: r.后画布,
      对35的余数: [+(r.后画布[0] % 35).toFixed(2), +(r.后画布[1] % 35).toFixed(2)],
    };
    B.push(行);
    记('  B ' + JSON.stringify(行));
    // ⭐ 开着吸附时能不能精确停回基线？—— 这本身是结论
    await 拖到(目标, 基线[0], 基线[1]);
    const 试回 = await 读节点(目标);
    const 差 = [+(试回.画布[0] - 基线[0]).toFixed(2), +(试回.画布[1] - 基线[1]).toFixed(2)];
    记('    ⭐ 开着吸附拖回基线 → ' + JSON.stringify(试回.画布) + ' 差 ' + JSON.stringify(差) +
        ' 对35余数 ' + JSON.stringify([+(试回.画布[0] % 35).toFixed(2), +(试回.画布[1] % 35).toFixed(2)]));
    (结果.读数.开着吸附拖回基线 ||= []).push({ 目标: 基线, 实际: 试回.画布, 差 });
  }
  结果.读数.阶段B_吸附开 = B;
  结果.读数.切开读数 = 开.枚;

  // ════════ 复原：⭐ 先关吸附，再回基线 ════════
  const 关 = await 切吸附(false);
  记('复原：切关 ' + JSON.stringify(关.动作) + ' 现在开=' + 关.开);
  await 拖到(目标, 基线[0], 基线[1]);
  const 回 = await 读节点(目标);
  记('拖回基线 → ' + JSON.stringify(回.画布));
  结果.读数.复原 = { 吸附开: 关.开, 节点: 回.画布 };

  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后坐标复核：' + JSON.stringify(偏差));
  结果.收尾 = { 偏差, 已渲染: Object.keys(await 读全部坐标(page)).length, 吸附最后: (await 定位吸附()).开 };
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  落盘(结果);
  await browser.browser.close();
  console.log('\n=== 已写 tools/batchEV5.json ===');
}
