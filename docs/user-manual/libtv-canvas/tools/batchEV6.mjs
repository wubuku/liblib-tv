// Batch EV-6：⭐⭐⭐ 换判据 —— **在拖拽过程中逐帧采样**节点位置。
//
// 前面 EV-4/EV-5 只看「松手后的落点」，灵敏度不够：
//   吸附开：B 组落点对 35 的余数 `[-13.26,13.5] / [-3.63,19.92] / [-24.05,27.26]`
//   吸附关：A 组落点对 35 的余数 `[-11,24] / [-30,20.98] / [-24,20]`
//   ⛔ 两组**没有区别**。但这也可能是「两者都没吸附」，看不出所以然。
//   离线把 4~80 的步长全扫了一遍，最优步长 56 的相对偏差也只有 0.125 ——
//   **这个量级完全可能只是 3 组样本的巧合**（77 个候选里挑最优，必然能挑出一个小值）。
//
// ⭐⭐ 本轮换一条**结构性**判据：拖拽**还没松手**的时候，
//   连着采 40 帧节点的画布坐标。
//   · 吸附生效 ⇒ React 每帧把位置量化到网格 ⇒ 采样到的 x/y 落在**少数几个离散值**上；
//   · 吸附不生效 ⇒ 采样值随指针连续变化，几乎每个都不同。
//   判据：**采样值的「去重后个数 / 总数」**。
//   离散 ⇒ 去重比低；连续 ⇒ 去重比接近 1。**这个量与步长无关，不受「猜步长」拖累。**
//
// ⭐⭐ 关键设计：同一次实验里**先关后开各做一遍**（同一节点、同一路径），
//   两个「去重比」直接对比。阳性对照就在同一个脚本里。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEV6.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 目标 = 'a-THmbuJXQj4';
const 基线 = 坐标[目标];

const browser = await launch();
const page = browser.page;

const 读变换 = () => page.evaluate(() => {
  const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(document.querySelector('.react-flow__viewport')).transform);
  const n = m[1].split(',').map(Number);
  return { zoom: n[0] };
});

const 读位置 = (id) => page.evaluate((nid) => {
  const el = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!el) return null;
  const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(el.style.transform || '');
  return m ? [parseFloat(m[1]), parseFloat(m[2])] : null;
}, id);

const 枚举底栏 = () => page.evaluate(() => {
  const out = [];
  for (const e of document.querySelectorAll('button')) {
    const r = e.getBoundingClientRect();
    if (r.top < 740 || r.bottom > 810 || r.left > 340) continue;
    if (e.querySelector('button')) continue;
    out.push({ aria: e.getAttribute('aria-label'), 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], box: [Math.round(r.left)], svg数: e.querySelectorAll('svg').length });
  }
  out.sort((a, b) => a.box[0] - b.box[0]);
  return out;
});

const 定位吸附 = async () => {
  const 栏 = await 枚举底栏();
  const 枚 = 栏[4];
  return { 栏: 栏.map((b) => ({ i: b.box[0], aria: b.aria, svg: b.svg数 })), 枚, 认: !!枚 && 枚.aria === '网格吸附', 开: !!枚 && 枚.aria === '网格吸附' && 枚.svg数 === 2 };
};

const 切吸附 = async (想要开) => {
  const 前 = await 定位吸附();
  if (!前.认) throw new Error('定位不到网格吸附');
  if (前.开 === 想要开) return 前;
  const [x, y] = 前.枚.中心;
  const 验 = await page.evaluate(([px, py]) => {
    const e = document.elementFromPoint(px, py);
    const b = e ? e.closest('button') : null;
    return b ? b.getAttribute('aria-label') : null;
  }, [x, y]);
  await page.mouse.move(x, y); await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(1000);
  await page.mouse.move(700, 300); await page.waitForTimeout(400);
  const 后 = await 定位吸附();
  return { ...后, 点击自证: 验 };
};

/** ⭐ 拖一段并**逐帧采样**，返回全部采样值 */
const 边拖边采 = async (id, 起点屏幕, 总dx, 总dy, 帧数 = 40) => {
  const [cx, cy] = 起点屏幕;
  const 验 = await page.evaluate(([px, py, nid]) => {
    const e = document.elementFromPoint(px, py);
    const n = e ? e.closest('.react-flow__node') : null;
    return n ? n.getAttribute('data-id') : null;
  }, [cx, cy, id]);
  if (验 !== id) throw new Error('落点不是目标节点：' + 验);
  const 采样 = [];
  await page.mouse.move(cx, cy);
  await page.mouse.down();
  for (let i = 1; i <= 帧数; i++) {
    await page.mouse.move(cx + Math.round((总dx * i) / 帧数), cy + Math.round((总dy * i) / 帧数));
    await page.waitForTimeout(35);
    const p = await 读位置(id);
    if (p) 采样.push([+p[0].toFixed(2), +p[1].toFixed(2)]);
  }
  await page.mouse.up();
  await page.waitForTimeout(700);
  const 末 = await 读位置(id);
  return { 采样, 末 };
};

try {
  await open(page, CANVAS_URL);
  await closePromos(page);
  await page.waitForTimeout(4000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  const 变 = await 读变换();
  记('zoom=' + 变.zoom);

  const 跑一轮 = async (想要开) => {
    const 切 = await 切吸附(想要开);
    记(`—— 轮次 ${想要开 ? '吸附开' : '吸附关'}：切=${切.动作 || '无需切'} 认=${切.认} 开=${切.开} 点击自证=${切.点击自证 || '—'}`);
    if (!切.认) throw new Error('定位失败');
    if (切.开 !== 想要开) throw new Error('切换没生效');
    const 起 = await 读位置(目标);
    const el = await page.evaluate((nid) => {
      const e = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const r = e.getBoundingClientRect();
      return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
    }, 目标);
    const r = await 边拖边采(目标, el, 200, 130);
    记(`   采到 ${r.采样.length} 帧，首=${JSON.stringify(r.采样[0])} 末=${JSON.stringify(r.末)}`);
    // 复原（此时吸附状态是想要开那个）
    if (想要开) await 切吸附(false);
    const 变2 = await 读变换();
    const cur = await 读位置(目标);
    const [cx, cy] = await page.evaluate((nid) => {
      const e = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
      const rr = e.getBoundingClientRect();
      return [Math.round(rr.left + rr.width / 2), Math.round(rr.top + rr.height / 2)];
    }, 目标);
    await page.mouse.move(cx, cy); await page.mouse.down();
    for (let i = 1; i <= 10; i++) { await page.mouse.move(cx + Math.round(((基线[0] - cur[0]) * 变2.zoom * i) / 10), cy + Math.round(((基线[1] - cur[1]) * 变2.zoom * i) / 10)); await page.waitForTimeout(30); }
    await page.mouse.up(); await page.waitForTimeout(800);
    const 回 = await 读位置(目标);
    记(`   复原后=${JSON.stringify(回)} 差=${JSON.stringify([+(回[0] - 基线[0]).toFixed(2), +(回[1] - 基线[1]).toFixed(2)])}`);
    return { 轮: 想要开 ? '开' : '关', 采样: r.采样, 末: r.末, 复原后: 回 };
  };

  const 关轮 = await 跑一轮(false);
  结果.读数.吸附关 = 关轮;
  const 开轮 = await 跑一轮(true);
  结果.读数.吸附开 = 开轮;

  // ════════ 离线统计：去重比 ════════
  const 统计 = (采样) => {
    const xs = 采样.map((p) => p[0]);
    const uniq = new Set(xs.map((v) => v.toFixed(2)));
    // 相邻帧的位移量
    const 步 = [];
    for (let i = 1; i < xs.length; i++) 步.push(+(xs[i] - xs[i - 1]).toFixed(2));
    return { 帧数: 采样.length, x去重个数: uniq.size, 去重比: +(uniq.size / xs.length).toFixed(3), 相邻步长样本: 步.slice(0, 12) };
  };
  结果.读数.统计 = { 关: 统计(关轮.采样), 开: 统计(开轮.采样) };
  记('⭐ 统计：关 ' + JSON.stringify(结果.读数.统计.关));
  记('⭐ 统计：开 ' + JSON.stringify(结果.读数.统计.开));

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
  console.log('\n=== 已写 tools/batchEV6.json ===');
}
