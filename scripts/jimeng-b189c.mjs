// 批次 189 c 轮：把「k 从哪来」和「同一个 testid 里有几套 k」两件事钉死。
//
// 手册 20-reference.md:1751 早就写了公式 `k = min(1/实测缩放, 2)`，但 **1754 明写「成因未查明，不下机制断言」**。
// 188 g 轮 + 189 a 轮已经给出答案：**k 就是元素身上的独立 CSS `scale` 属性**（`computedStyle.scale`），
// 它不出现在 `computedStyle.transform` 里 —— 这正是 1751 那张表的 k 一直找不到出处的原因。
//
// 本轮要钉的两件事：
//   ① **全量分布**：把每个 testid 家族下**每一个实例**的 `scale` 值列出来，
//      看「放大型（k=2）」与「钉住型（k=1/s）」各占多少 —— 手册 1727 行在 60% 下记过
//      `28.8×68 / 28.6×6 / 25.23×1 / 24.05×1`，但没归因到 k 的两个取值。
//   ② **手册声称的 k=1.25**：那是 `1/0.8`，只有 **80% 档**才会出现 —— 189 b 轮的 9 档里没有 80%，
//      所以本轮把 **80%** 加进档位，专程看它。
//   ③ **那个没有 testid 的家族**（`absolute -inset-1 visible`）到底是什么：`-inset-1` = 向外 4px，
//      几何上像「选中描边」，但 `flow-node-media-stroke` 是有 testid 的那个 ⇒ 两者不是同一个东西。
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const rec = { 批次: '189c', 目标: 'k 的出处（全量分布）+ 80% 档的 k=1.25 + 无名家族身份' };
await settle(p, R);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
rec.起点 = { 节点数: 基线.ids.length, 积分: await R.credits(), 缩放: await R.zoom() };

/** 每个带独立 scale≠1 的实例都列出来，并按 scale 值归桶；同时单独特写那个无名家族。 */
const 全量 = () => p.evaluate(() => {
  const 视口 = document.querySelector('.react-flow__viewport');
  const ms = 视口 ? /scale\(([-\d.]+)\)/.exec(视口.style.transform || '') : null;
  const s = ms ? parseFloat(ms[1]) : null;
  const 数 = (v) => { if (v == null) return null; const t = String(v).trim();
    if (t === '' || t === 'none') return null; const n = parseFloat(t); return Number.isFinite(n) ? n : null; };
  const 桶 = {}; const 无名 = [];
  for (const e of Array.from(document.querySelectorAll('*'))) {
    let cs; try { cs = getComputedStyle(e); } catch { continue; }
    const sc = 数(cs.scale); if (sc === null || Math.abs(sc - 1) <= 0.001) continue;
    const r = e.getBoundingClientRect();
    const tid = e.getAttribute('data-testid');
    const key = tid || '(无testid)' + String(e.className || '').split(' ').slice(0, 3).join(' ');
    // scale 值四舍五入到 3 位再归桶，避免浮点噪声把同一个值拆成两桶
    const sk = Math.round(sc * 1000) / 1000;
    (桶[key] = 桶[key] || {});
    (桶[key][sk] = 桶[key][sk] || []).push({ 屏上w: Math.round(r.width * 100) / 100, offsetW: e.offsetWidth });
    if (!tid) {
      const 父 = e.parentElement;
      无名.push({ cls: String(e.className || ''), 父cls: 父 ? String(父.className || '').split(' ').slice(0, 3).join(' ') : null,
        父testid: 父 && 父.getAttribute ? 父.getAttribute('data-testid') : null,
        position: cs.position, inset: [cs.top, cs.right, cs.bottom, cs.left].join(' '),
        border: cs.border, borderRadius: cs.borderRadius, background: cs.backgroundColor,
        屏上: { w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100 },
        相对节点: (() => { const nd = e.closest('.react-flow__node'); if (!nd) return null;
          const a = e.getBoundingClientRect(), b = nd.getBoundingClientRect();
          return { 节点屏上: { w: Math.round(b.width * 100) / 100, h: Math.round(b.height * 100) / 100 },
            每边外扩: { 上: Math.round((b.top - a.top) * 100) / 100, 左: Math.round((b.left - a.left) * 100) / 100 } }; })() });
    }
  }
  const 分布 = {};
  for (const k of Object.keys(桶)) {
    分布[k] = Object.keys(桶[k]).map((sk) => ({ scale值: Number(sk), 实例数: 桶[k][sk].length,
      屏上样本: 桶[k][sk][0].屏上w, offsetW样本: 桶[k][sk][0].offsetW,
      预测min2式: (() => { const ow = 桶[k][sk][0].offsetW; return Math.round(Math.min(2 * ow * s, ow) * 100) / 100; })(),
      预测钉住式: (() => { const ow = 桶[k][sk][0].offsetW; return ow; })() }))
      .sort((a, b2) => b2.实例数 - a.实例数);
  }
  return { scale: s, 缩放aria: (document.querySelector('[data-testid="canvas-zoom-percent"]') || {}).ariaLabel || null,
    选中数: document.querySelectorAll('.react-flow__node.selected').length, 分布,
    无名家族样本: 无名.slice(0, 4), 无名家族实例数: 无名.length };
});

const 档位 = [80, 60, 50, 100, 26];
rec.各档 = [];
for (const pct of 档位) {
  const z = await setZoom(p, pct);
  await p.mouse.move(1250, 706); await p.waitForTimeout(850);
  rec.各档.push({ 档: pct, 回读: z.回读, ...(await 全量()) });
}

rec.判定 = {
  各档家族: rec.各档.map((x) => ({ 档: x.档, scale: x.scale, 家族: Object.keys(x.分布), 无名实例数: x.无名家族实例数 })),
  八十档的k值: (() => { const x = rec.各档.find((y) => y.档 === 80);
    const 出 = {}; for (const k of Object.keys(x.分布)) 出[k] = x.分布[k].map((d) => d.scale值);
    return 出; })(),
  无名家族身份: (() => { const x = rec.各档.find((y) => y.无名家族实例数 > 0);
    return x ? { 样例: x.无名家族样本[0], 实例数: x.无名家族实例数 } : null; })(),
  同一testid多套k: (() => { const 出 = {}; for (const x of rec.各档) for (const k of Object.keys(x.分布)) {
    (出[k] = 出[k] || new Set()); for (const d of x.分布[k]) 出[k].add(d.scale值); }
    const r = {}; for (const k of Object.keys(出)) r[k] = Array.from(出[k]).sort((a, b2) => a - b2);
    return r; })(),
  非空守卫: { 档数: rec.各档.length, 每档都有家族: rec.各档.every((x) => Object.keys(x.分布).length > 0),
    八十档确实在档位里: !!rec.各档.find((x) => x.档 === 80), scale与aria一致: rec.各档.every((x) => Math.abs(x.scale - x.档 / 100) <= 0.005) },
};

await p.keyboard.press('Escape'); await p.waitForTimeout(700);
rec.收尾 = await endState(p, R, 基线);
console.log(JSON.stringify(rec, null, 1));
await b.close();
