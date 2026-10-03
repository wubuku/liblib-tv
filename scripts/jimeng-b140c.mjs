// 批次 140 c 轮：把「角把手 40% 档读 19.2 而不是 24」这件事**钉死** —— 它到底是裁剪还是第四种机制。
//
// 🔑 b 轮已把整族读全：角把手在 40% 档读 `19.2×19.2`、其余三档 `24×24`。
//   `19.2 = 24 × 0.8` 看着像"另一套尺寸"，但**反推 canvas 值 48 / 40 / 24 / 12 单调递减**
//   —— 递减正是「被外层容器裁掉一圈」的签名（裁掉多少取决于把手相对容器的位置）。
//
// 本轮要分清两种解释（它们都能解释 19.2，但只有一种是对的）：
//   E1 **裁剪**：`text-node-resize-controls` 容器比把手小，40% 下把手有一截落在容器外，
//      `getBoundingClientRect()` 仍返回**完整**盒子（不受 overflow 裁剪影响），
//      **但 CSS 里若有 `clip-path` / `mask` / 父级 `overflow:hidden` + 视觉裁剪**，
//      真正的可点区会变小。判据：读把手**中心点**的 `elementFromPoint` ——
//      若中心仍命中把手 ⇒ 只是"视觉被裁"，**热区没变**；若中心落空 ⇒ **热区真的变小了**。
//   E2 第四种机制：40% 下组件真的按比例算了一个不同的尺寸。
//      判据：把手**中心点是否仍在把手内**，以及手盒子相对容器的偏移量随缩放怎么变。
//
// 📌 这正是批次 136 记的「返回值 ≠ 遮挡者」与批次 133 的「返回值 ≠ 命中者」的第三个面：
//   **`getBoundingClientRect()` 返回的是布局盒，命中测试才是热区**。
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 建N个, 可点落点, selCount, idsOf } from './jimeng-b139-lib.mjs';
import fs from 'node:fs';

const 档位 = [40, 60, 100];
const rec = { 轮: '140c', 档位 };
let 全过 = true;
const 断言 = (名, ok, 详情) => { (rec.断言 = rec.断言 || []).push({ 名, 通过: !!ok, 详情 }); if (!ok) 全过 = false; };

const { b, p } = await openCanvas();
const R = readers(p);

/** 读角把手与容器之间的几何关系 + 命中测试。**只读**。 */
const 读关系 = (p, id) => p.evaluate((ID) => {
  const n = document.querySelector(`.react-flow__node[data-id="${ID}"]`);
  if (!n) return { __err: 'node-gone' };
  const scale = (() => { const vp = document.querySelector('.react-flow__viewport');
    const m = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null;
    return m ? Math.round(parseFloat(m[1]) * 1000) / 1000 : null; })();
  const box = (e) => { const r = e.getBoundingClientRect();
    return { x: Math.round(r.x * 100) / 100, y: Math.round(r.y * 100) / 100,
      w: Math.round(r.width * 100) / 100, h: Math.round(r.height * 100) / 100 }; };
  const 容器 = n.querySelector('[data-testid="text-node-resize-controls"]');
  // 🔴 第一版把 `pcs` 写在 `探` 里面，却在**返回对象**里用它 ⇒ `ReferenceError: pcs is not defined`，
  //   整个 evaluate 挂掉、三个档一个都没读到。作用域要放在它真正被用的那一层。
  const pcs = 容器 ? getComputedStyle(容器) : null;
  const 角 = Array.from(n.querySelectorAll('[data-testid^="text-node-resize-"]'))
    .filter((e) => /nwse|nesw/.test(getComputedStyle(e).cursor || ''));
  const 探 = (e) => {
    const r = e.getBoundingClientRect();
    const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    const h = document.elementFromPoint(cx, cy);
    const cs = getComputedStyle(e);
    return {
      testid: e.getAttribute('data-testid'),
      盒: box(e),
      中心: [cx, cy],
      中心命中: h ? { 是把手: h === e || e.contains(h), tag: h.tagName,
        testid: h.getAttribute('data-testid'), aria: h.getAttribute('aria-label') } : null,
      裁剪样式: { overflow: cs.overflow, clipPath: cs.clipPath, mask: cs.maskImage ? '(有)' : cs.mask },
      父级链: (() => { const c = []; for (let x = e.parentElement; x && x !== document.body; x = x.parentElement) {
        const s = getComputedStyle(x);
        c.push({ tag: x.tagName, testid: x.getAttribute('data-testid'), overflow: s.overflow, clipPath: s.clipPath }); } return c.slice(0, 5); })(),
    };
  };
  return { scale, 容器: 容器 ? { ...box(容器), overflow: pcs.overflow, clipPath: pcs.clipPath } : null,
    节点屏上: box(n), 角: 角.map(探) };
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
      const h = await 读关系(p, tid);
      rec.各档.push({ 标称: pct, 追平: z.scale已追平, ...h });
      断言(`③${pct}% 实测 scale 已追平`, z.scale已追平, { z, 实测: h.scale });
    }

    // ---- E1 vs E2 判定
    rec.判定 = rec.各档.map((d) => ({
      标称: d.标称, scale: d.scale,
      容器屏上: d.容器 && `${d.容器.w}×${d.容器.h}`,
      角盒: d.角.map((a) => `${a.盒.w}×${a.盒.h}`),
      角中心仍命中自身: d.角.map((a) => a.中心命中 ? (a.中心命中.是把手 ? '是' : '否→' + (a.中心命中.testid || a.中心命中.tag)) : 'null'),
      角盒边长四档: d.角[0] ? d.角[0].盒.w : null,
    }));
    // 关键：**中心仍命中把手自身** ⇒ 盒是完整布局盒，19.2 只是布局盒本身的尺寸变化，
    //   而不是"可点区被裁"；这时要问的是"为什么盒会变"。
    const 中心全中 = rec.各档.every((d) => d.角.every((a) => a.中心命中 && a.中心命中.是把手));
    rec.角中心四档全命中自身 = 中心全中;
    断言('④角把手中心四档都命中自身（说明 19.2 不是「命中被裁」）', 中心全中, rec.判定);

    // 容器 overflow / clip-path 有没有在裁
    rec.裁剪样式汇总 = rec.各档.map((d) => ({
      标称: d.标称, 容器overflow: d.容器 && d.容器.overflow, 容器clipPath: d.容器 && d.容器.clipPath,
      角自overflow: d.角[0] && d.角[0].裁剪样式.overflow, 角自clipPath: d.角[0] && d.角[0].裁剪样式.clipPath,
      父级有overflowhidden: d.角[0] && d.角[0].父级链.some((x) => x.overflow === 'hidden'),
    }));
    rec.有任一裁剪样式 = rec.裁剪样式汇总.some((r) => r.父级有overflowhidden || (r.角自clipPath && r.角自clipPath !== 'none'));
    console.log('角中心四档全命中自身 =', 中心全中, '| 有任一裁剪样式 =', rec.有任一裁剪样式);
  }
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 600); }

// 收尾：清选中 + 删靶子 + 回 60% + 重开小地图
try {
  if (await selCount(p) > 0) { const 空 = await p.evaluate(() => {
      const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getBoundingClientRect());
      for (let y = 660; y >= 90; y -= 6) for (let x = 8; x <= innerWidth - 8; x += 6) {
        const h = document.elementFromPoint(x, y);
        if (h && h.classList && h.classList.contains('react-flow__node-pane') === false
          && h.classList && h.classList.contains('react-flow__pane')
          && !nodes.some((r) => x >= r.x && x <= r.right && y >= r.y && y <= r.bottom)) return { x, y };
      } return null; });
    if (空) { await p.mouse.click(空.x, 空.y); await p.waitForTimeout(900); } }
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
fs.writeFileSync(new URL('./_tmp-b140c.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 判定: rec.判定, 裁剪样式汇总: rec.裁剪样式汇总 }, null, 1));
console.log('断言全过', 全过);
await b.close();
