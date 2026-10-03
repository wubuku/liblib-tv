// 批次 140 a 轮探针：组卡片**八向缩放把手**的完整建档 + 钉死尺寸机制。
//
// 🔑 为什么值得做（两处「未决/冲突」叠在一起）：
//   ① §3.22 只记组卡片「**四角**把手 aria 逐字，各 24×24」（top left/right/bottom right/bottom left），
//      但批次 139 实测**组也是 8 个**（还有 Resize group from top/right/bottom/left 四个边中点）——
//      节点侧的把手手册早就在 `create-first-node.md` 记成「八个方向」，**组侧漏了四个**。
//   ② §4.15.6「缩放把手这一族的尺寸机制」是一则**明确挂着的未决项**：
//      同一张 320×320 卡片，角把手 23% 读 11×11、40% 读 19×19、60% 读 24×24，
//      「屏上恒定」与「canvas 恒定」两个假设都被证伪，**当时没定案**。
//      既然批次 139 已经把「组工具条宽度」这类「看似随缩放变、其实有公式」的东西挖穿了，
//      这族把手很可能也是同一个坑：**也许不是"两个假设都不对"，而是第三个公式**。
//
// 本轮只读：不拖、不点把手，只把 8 个把手在**多档缩放**下的几何全 dump 出来。
// 建组走救援脚本同款护栏（建 3 文本 → 点选 → 编组），组留在画布上给 b/c 轮，救援收尾。
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 建N个, 点选一组, 点编组, 组数, idsOf, selCount, 可点落点 } from './jimeng-b139-lib.mjs';
import fs from 'node:fs';

const 档位 = [40, 60, 100];
const rec = { 轮: '140a', 档位 };
let 全过 = true;
const 断言 = (名, ok, 详情) => { (rec.断言 = rec.断言 || []).push({ 名, 通过: !!ok, 详情 }); if (!ok) 全过 = false; };

const { b, p } = await openCanvas();
const R = readers(p);

/** 读组卡片八向把手的全层几何。**只读**，不触碰。 */
const 读把手 = (p) => p.evaluate(() => {
  const shadow = document.querySelector('[data-id^="__group-resize-chrome__"].react-flow__node-group');
  if (!shadow) return { __err: 'no-shadow' };
  const handles = Array.from(shadow.querySelectorAll('[aria-label^="Resize group from"]'));
  const box = (e) => { const r = e.getBoundingClientRect();
    return { x: Math.round(r.x * 10) / 10, y: Math.round(r.y * 10) / 10,
      w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10,
      cx: Math.round((r.x + r.width / 2) * 10) / 10, cy: Math.round((r.y + r.height / 2) * 10) / 10 }; };
  const 真身 = document.querySelector('.react-flow__node-group:not([data-id^="__group-resize-chrome__"])');
  return {
    scale: (() => { const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null; return m ? Math.round(parseFloat(m[1]) * 1000) / 1000 : null; })(),
    组卡片: 真身 ? { canvas: { w: 真身.offsetWidth, h: 真身.offsetHeight }, 屏上: box(真身) } : null,
    把手数: handles.length,
    把手: handles.map((e) => {
      const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      return { aria: e.getAttribute('aria-label'), tag: e.tagName,
        屏上: box(e), offset: { w: e.offsetWidth, h: e.offsetHeight },
        pe: cs.pointerEvents, cursor: cs.cursor, borderRadius: cs.borderRadius,
        bg: cs.backgroundColor, zIndex: cs.zIndex,
        中心命中: (() => { const h = document.elementFromPoint(Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2));
          return h ? { tag: h.tagName, aria: h.getAttribute('aria-label'), 是把手: h === e || e.contains(h) } : null; })() };
    }).sort((a, b) => a.aria.localeCompare(b.aria)),
  };
});

try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p), zoom: await R.zoom() };
  断言('①起始无组卡片', (await 组数(p)) === 0, { 组数: await 组数(p) });
  断言('②起始 0 选中', (await selCount(p)) === 0, { 选中: await selCount(p) });

  // 建 3 文本 → 点选 → 编组
  const 建 = await 建N个(p, '文本', 3, 断言, 76);
  rec.建 = { ids: 建.ids, ok: 建.ok };
  if (建.ids && 建.ids.length === 3) {
    const 点 = await 点选一组(p, 建.ids);
    rec.点选ok = 点.ok;
    断言('③点选后恰好选中这 3 个', 点.ok, { 选中: 点.最终选中 });
    if (点.ok) {
      const g = await 点编组(p);
      rec.编组ok = g.ok;
      断言('④编组后恰好 1 个真身组', g.ok, g);
      if (g.ok) {
        // ---- 多档读把手
        rec.各档 = [];
        for (const pct of 档位) {
          const z = await setZoom(p, pct);
          const h = await 读把手(p);
          rec.各档.push({ 标称: pct, 追平: z.scale已追平, ...h });
          断言(`⑤${pct}% 实测 scale 已追平`, z.scale已追平, { z });
        }
        // 判定
        const 角 = ['Resize group from top left', 'Resize group from bottom right'];
        rec.判定 = rec.各档.map((d) => {
          const 角档 = d.把手 ? d.把手.filter((x) => 角.includes(x.aria)) : [];
          return { 标称: d.标称, scale: d.scale, 把手数: d.把手数,
            角把手屏上: 角档.map((x) => `${x.屏上.w}×${x.屏上.h}`),
            角把手offset: 角档.map((x) => `${x.offset.w}×${x.offset.h}`),
            '屏上是否恒定': new Set(角档.map((x) => `${x.屏上.w}×${x.屏上.h}`)).size === 1,
            'canvas(屏上/scale)': 角档.map((x) => (d.scale ? Math.round((x.屏上.w / d.scale) * 10) / 10 : null)) };
        });
        rec.把手总数各档 = rec.各档.map((d) => d.把手数);
        断言('⑥各档把手数一致（应为 8）', new Set(rec.把手总数各档).size === 1 && rec.把手总数各档[0] === 8, rec.把手总数各档);
      }
    }
  }
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 600); }

// 归位：先回 60%，组留给救援
try {
  const z = await setZoom(p, 60);
  rec.归位 = { zoom: await R.zoom(), 追平: z.scale已追平 };
  if ((await R.minimap()) && (await R.minimap()).ariaPressed !== 'true') {
    const mm = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3);
    if (!mm.__err) { await p.mouse.click(mm.x, mm.y); await p.waitForTimeout(1200); }
    rec.重开小地图 = mm;
  }
  rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 组数: await 组数(p),
    选中: await selCount(p), zoom: await R.zoom(), minimap: await R.minimap() };
} catch (e) { rec.收尾异常 = String(e && e.message).slice(0, 200); }

rec.断言全过 = 全过;
fs.writeFileSync(new URL('./_tmp-b140a.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 判定: rec.判定, 把手总数各档: rec.把手总数各档, 收尾: rec.收尾 }, null, 1));
console.log('断言全过', 全过);
await b.close();
