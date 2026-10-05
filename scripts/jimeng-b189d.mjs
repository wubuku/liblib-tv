// 批次 189 d 轮：k 到底是「每个节点记住各自的缩放」，还是**过渡动画的中间值**？
//
// 189 c 轮在 80% 档读到 `flow-node-title` / `flow-node-selected-tag` 的 k 有 **6 个值**：
//   `[2, 1.785, 1.25, 1.512, 1.367, 1.285]`，跨 5 个状态共见过 **14 个** k 值。
// 而公式 `k = min(2, 1/缩放)` 在 80% 只该给 **1.25**（1/0.8），在 50% 给 2。
// 中间值 1.785 / 1.512 / 1.367 / 1.285 对应的「等效缩放」分别是 0.560 / 0.661 / 0.731 / 0.778 ——
// 都不是任何一档手动设过的值。
//
// 两个候选解释：
//   ① **过渡动画**：k 是 CSS 过渡属性，缩放变化时每个元素从旧值补间到新值，
//      我在补间途中读 ⇒ 读到中间值（1.785 是从 2 往 1.25 走的路上）。
//      支持证据：这些中间值全都**夹在「旧值 2」与「新值 1.25」之间**。
//   ② **每个节点记住各自的缩放**（手册 20-reference:1754 观察到「老节点 k 恒为 2、新节点是 1.6667」，
//      当时判「成因未查明」）。若成立，中间值应当**一直停在那儿**，等多久都不收敛。
//
// 判别方法只有一个：**等**。同一个缩放档上，隔 0.85s / 2s / 4s / 7s 各读一次 k 分布。
//   若是动画 ⇒ k 会向单值收敛；
//   若是「各记各的」 ⇒ k 分布不随时间变化。
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '189d', 判别: 'k 是过渡动画的中间值，还是每节点各记各的' };
await settle(p, R);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
rec.起点 = { 节点数: 基线.ids.length, 积分: await R.credits(), 缩放: await R.zoom() };

const k分布 = () => p.evaluate(() => {
  const 视口 = document.querySelector('.react-flow__viewport');
  const ms = 视口 ? /scale\(([-\d.]+)\)/.exec(视口.style.transform || '') : null;
  const s = ms ? parseFloat(ms[1]) : null;
  const 数 = (v) => { if (v == null) return null; const t = String(v).trim();
    if (t === '' || t === 'none') return null; const n = parseFloat(t); return Number.isFinite(n) ? n : null; };
  const 出 = {};
  for (const e of Array.from(document.querySelectorAll('[data-testid="flow-node-title"],[data-testid="flow-node-selected-tag"]'))) {
    const cs = getComputedStyle(e); const k = 数(cs.scale); if (k === null) continue;
    const tid = e.getAttribute('data-testid');
    const key = Math.round(k * 1000) / 1000;
    (出[tid] = 出[tid] || {}); 出[tid][key] = (出[tid][key] || 0) + 1;
  }
  const 转成 = (o) => Object.keys(o).map(Number).sort((a, b) => b - a).map((k) => ({ k, 实例数: o[k] }));
  return { scale: s, 标题: 转成(出['flow-node-title'] || {}), 标签: 转成(出['flow-node-selected-tag'] || {}) };
});

// ① 静息态在 26%（起点）读一次，作为「老状态」基线
await p.mouse.move(1250, 706); await p.waitForTimeout(800);
rec.序列 = [];
let r = await k分布();
rec.序列.push({ 场景: '起点 26%', 等了ms: 800, ...r });

// ② 切到 80%，然后在 0.85 / 2 / 4 / 7 秒各读一次
await setZoom(p, 80);
const t0 = Date.now();
for (const 目标ms of [850, 2000, 4000, 7000]) {
  const 已等 = Date.now() - t0;
  if (已等 < 目标ms) await p.waitForTimeout(目标ms - 已等);
  r = await k分布();
  rec.序列.push({ 场景: '切到 80% 后', 等了ms: Date.now() - t0, ...r });
}

// ③ 再切回 26%，同样定时序读（看反向补间是否对称）
await setZoom(p, 26);
const t1 = Date.now();
for (const 目标ms of [850, 2000, 4000]) {
  const 已等 = Date.now() - t1;
  if (已等 < 目标ms) await p.waitForTimeout(目标ms - 已等);
  r = await k分布();
  rec.序列.push({ 场景: '切回 26% 后', 等了ms: Date.now() - t1, ...r });
}

rec.判定 = {
  序列: rec.序列.map((x) => ({ 场景: x.场景, 等了ms: x.等了ms, scale: x.scale,
    标题k: x.标题.map((y) => `${y.k}×${y.实例数}`), 标签k: x.标签.map((y) => `${y.k}×${y.实例数}`) })),
  // 若动画：同一场景下「等了 7 秒」那次的 k 种数应少于「等了 850ms」那次
  收敛: (() => {
    const 正 = rec.序列.filter((x) => x.场景 === '切到 80% 后');
    if (正.length < 2) return null;
    const 早 = 正[0], 晚 = 正[正.length - 1];
    const 种数 = (x, f) => x[f].length;
    return { 早标题种数: 种数(早, '标题'), 晚标题种数: 种数(晚, '标题'),
      早标签种数: 种数(早, '标签'), 晚标签种数: 种数(晚, '标签'),
      标题收敛: 种数(晚, '标题') < 种数(早, '标题'), 标签收敛: 种数(晚, '标签') < 种数(早, '标签'),
      晚标题k: 晚.标题, 晚标签k: 晚.标签 };
  })(),
  预期值: { '80%': Math.min(2, 1 / 0.8), '26%': 2 },
  非空守卫: { 读数次数: rec.序列.length, 每次都有标题读数: rec.序列.every((x) => x.标题.length > 0),
    每次都有标签读数: rec.序列.every((x) => x.标签.length > 0) },
};

await p.keyboard.press('Escape'); await p.waitForTimeout(700);
rec.收尾 = await endState(p, R, 基线);
console.log(JSON.stringify(rec, null, 1));
await b.close();
