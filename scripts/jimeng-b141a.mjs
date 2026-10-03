// 批次 141 a 轮：把**节点角把手 40% 档的 `19.2`** 钉死 —— 定位它到底在哪个缩放跳变。
//
// 🔑 批次 140 留下的尾巴：角把手在 40% 读 `19.2×19.2`，而 60/100/200% 都是 `24×24`。
//   已排除 CSS 裁剪（overflow 全 visible、clip-path 全 none）与热区遮挡
//   （getBoundingClientRect 是布局盒，40% 档 4 角里 3 角中心仍命中把手自身）。
//   剩下两种可能，**必须分档才能分开**：
//     E1「**阈值机制**」：缩放低于某个值，组件才把角把手换成小一号的盒子
//        ⇒ 存在一个**跳变点**，`19.2` 与 `24` 各自在自己的区间里**恒定**。
//     E2「**连续变化**」：角把手尺寸随缩放连续变化，`19.2` 只是恰好落在 40%。
//        ⇒ 相邻档（如 38% / 39% / 41% / 42%）会读出 `19.2` 与 `24` **之间**的值。
//
// 本轮取档：36 / 38 / 40 / 42 / 45 / 50 / 55 / 60 —— **在 40% 两侧密布**，
//   两种预测会给出**明显不同**的表：E1 是一列 `19.2` 加一列 `24`（中间直接跳），
//   E2 是一串中间值。判据自带分辨率，不靠"看起来像"。
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 建N个, 可点落点, selCount, idsOf } from './jimeng-b139-lib.mjs';
import { findEmptyPane } from './jimeng-b136-lib.mjs';
import fs from 'node:fs';

const 档位 = [36, 38, 40, 42, 45, 50, 55, 60];
const rec = { 轮: '141a', 档位 };
let 全过 = true;
const 断言 = (名, ok, 详情) => { (rec.断言 = rec.断言 || []).push({ 名, 通过: !!ok, 详情 }); if (!ok) 全过 = false; };

const { b, p } = await openCanvas();
const R = readers(p);

/** 读锁定节点的角把手 + 边把手 + 包裹层几何。**只读**。 */
const 读 = (p, id) => p.evaluate((ID) => {
  const n = document.querySelector(`.react-flow__node[data-id="${ID}"]`);
  if (!n) return { __err: 'node-gone' };
  const scale = (() => { const vp = document.querySelector('.react-flow__viewport');
    const m = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null;
    return m ? Math.round(parseFloat(m[1]) * 1000) / 1000 : null; })();
  const box = (e) => { const r = e.getBoundingClientRect();
    return { w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100,
      x: Math.round(r.x * 100) / 100, y: Math.round(r.y * 100) / 100 }; };
  const all = Array.from(n.querySelectorAll('[data-testid^="text-node-resize-"]'));
  const 角 = all.filter((e) => /nwse|nesw/.test(getComputedStyle(e).cursor || ''));
  const 边 = all.filter((e) => /ns-resize|ew-resize/.test(getComputedStyle(e).cursor || ''));
  const 容器 = n.querySelector('[data-testid="text-node-resize-controls"]');
  return {
    scale, 节点屏上: box(n), 节点canvas: { w: n.offsetWidth, h: n.offsetHeight },
    容器: 容器 ? box(容器) : null,
    角: 角.map((e) => ({ testid: e.getAttribute('data-testid'), 盒: box(e), offset: { w: e.offsetWidth, h: e.offsetHeight } }))
      .sort((a, b) => String(a.testid).localeCompare(String(b.testid))),
    边: 边.map((e) => ({ testid: e.getAttribute('data-testid'), 盒: box(e) }))
      .sort((a, b) => String(a.testid).localeCompare(String(b.testid))),
  };
}, id);

try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), zoom: await R.zoom() };
  断言('①起始 0 选中', (await selCount(p)) === 0, { 选中: await selCount(p) });

  const 建 = await 建N个(p, '文本', 1, 断言, 76);
  rec.建 = { ids: 建.ids, ok: 建.ok };
  if (!(建.ids && 建.ids.length === 1)) { rec.中止 = '建文本节点未成'; }
  else {
    const tid = 建.ids[0];
    const 落 = await 可点落点(p, `.react-flow__node[data-id="${tid}"]`, 4, 4);
    if (!落.__err) { await p.mouse.click(落.x, 落.y); await p.waitForTimeout(1200); }
    const 选中态 = await p.evaluate((id) => document.querySelectorAll('.react-flow__node.selected').length === 1
      && document.querySelector('.react-flow__node.selected').getAttribute('data-id') === id, tid);
    断言('②目标恰好选中', 选中态, { 选中态 });

    rec.各档 = [];
    for (const pct of 档位) {
      const z = await setZoom(p, pct);
      const h = await 读(p, tid);
      rec.各档.push({ 标称: pct, 追平: z.scale已追平, ...h });
      断言(`③${pct}% 实测 scale 已追平`, z.scale已追平, { z, 实测: h.scale });
    }

    // ---- E1 vs E2 判定：角把手边长在 40% 两侧是否连续
    const 表 = rec.各档.map((d) => ({
      标称: d.标称, scale: d.scale, 节点屏上: d.节点屏上.w,
      角边长: d.角[0] ? d.角[0].盒.w : null,
      角去重: d.角.map((a) => a.盒.w).filter((v, i, arr) => arr.indexOf(v) === i),
      边长: d.边[0] ? d.边[0].盒.w : null, 边厚: d.边[0] ? d.边[0].盒.h : null,
      容器: d.容器 && d.容器.w,
    }));
    rec.表 = 表;
    const 角值 = 表.map((t) => t.角边长);
    rec.角把手各档边长 = 角值;
    // 节点 canvas 四档恒定（证明锁死同一节点）
    rec.节点canvas = rec.各档.map((d) => `${d.节点canvas.w}×${d.节点canvas.h}`);
    断言('④节点 canvas 八档恒定（证明没换节点）', new Set(rec.节点canvas).size === 1, rec.节点canvas);
    // 边把手：长度 canvas 恒、厚度屏上恒（批次 140 已验，这里做回归确认）
    const 边长canvas = rec.各档.map((d) => d.边[0] ? Math.round((d.边[0].盒.w / d.scale) * 100) / 100 : null);
    rec.边长反推canvas = 边长canvas;
    rec.边厚去重 = [...new Set(rec.各档.map((d) => d.边[0] && d.边[0].盒.h))];
    断言('⑤边把手长度反推 canvas 恒定（批次 140 结论回归）', new Set(边长canvas).size === 1, 边长canvas);
    断言('⑥边把手厚度屏上恒定 10（批次 140 结论回归）', rec.边厚去重.length === 1 && rec.边厚去重[0] === 10, rec.边厚去重);
    // 角把手：是否只有 {19.2, 24} 两个值（E1）或出现中间值（E2）
    rec.角把手去重全表 = [...new Set(角值)];
    断言('⑦角把手边长只出现有限个离散值（不是连续变化）', rec.角把手去重全表.length <= 3, { 各档: 角值, 去重: rec.角把手去重全表 });
  }
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 600); }

// 收尾：清选中 + 删靶子 + 回 60% + 重开小地图
try {
  if (await selCount(p) > 0) { const 空 = await findEmptyPane(p); if (空) { await p.mouse.click(空.x, 空.y); await p.waitForTimeout(900); } }
  if (rec.建 && rec.建.ids && rec.建.ids[0]) {
    const tid = rec.建.ids[0];
    const 落 = await 可点落点(p, `.react-flow__node[data-id="${tid}"]`, 4, 4);
    if (!落.__err) {
      await p.mouse.click(落.x, 落.y); await p.waitForTimeout(900);
      const 确 = await p.evaluate((id) => document.querySelectorAll('.react-flow__node.selected').length === 1
        && document.querySelector('.react-flow__node.selected').getAttribute('data-id') === id, tid);
      if (确) {
        await p.mouse.click(落.x, 落.y, { button: 'right' }); await p.waitForTimeout(1600);
        const del = await p.evaluate(() => {
          const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
            .filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
          if (!els.length) return { __err: 'no-delete-item' };
          const e = els[0]; const r = e.getBoundingClientRect();
          for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2)
            for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
              const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y };
            }
          return { __err: 'no-point' };
        });
        rec.靶子删除 = del;
        if (!del.__err) { await p.mouse.click(del.x, del.y); await p.waitForTimeout(2200); }
      }
    }
  }
  const z = await setZoom(p, 60);
  rec.归位 = { zoom: await R.zoom(), 追平: z.scale已追平 };
  if ((await R.minimap()) && (await R.minimap()).ariaPressed !== 'true') {
    const mm = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3);
    if (!mm.__err) { await p.mouse.click(mm.x, mm.y); await p.waitForTimeout(1200); }
  }
  rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p),
    浮层: await R.overlays(), zoom: await R.zoom(), minimap: await R.minimap() };
} catch (e) { rec.收尾异常 = String(e && e.message).slice(0, 200); }

rec.断言全过 = 全过;
fs.writeFileSync(new URL('./_tmp-b141a.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log('| 缩放 | scale | 节点屏上 | 角边长 | 边长×厚 | 边长反推canvas | 容器 |');
console.log('|---|---|---|---|---|---|---|');
for (const t of rec.表 || []) console.log(`| ${t.标称}% | ${t.scale} | ${t.节点屏上} | **${t.角边长}** | ${t.边长}×${t.边厚} | ${(rec.边长反推canvas||[])[(rec.表||[]).indexOf(t)]} | ${t.容器} |`);
console.log('角把手去重全表', JSON.stringify(rec.角把手去重全表));
console.log('断言全过', 全过, '| 收尾', JSON.stringify(rec.收尾));
await b.close();
