// 批次 140 b 轮：钉死**节点**侧那族把手（`text-node-resize-*`）的尺寸机制 ——
//   结清 SOURCE_OBSERVATIONS.md §4.15.6 挂着的那个未决项。
//
// 🔴 §4.15.6 记的未决：同一张 canvas `320×320` 的文本卡片，角把手屏上
//   23% 档 `11×11`、40% 档 `19×19`、60% 档 `24×24`
//   ⇒ 反推 canvas 47 / 47.5 / 40。「屏上恒定」与「canvas 恒定」**两个假设都被证伪**。
//
// 🔴 但同一节的 §4.15.7.2 自曝了取证实况：「换缩放做对照时，**节点换了**」——
//   `findTextNode()` 每次扫「第一个点得到的未选中文本节点」，视口内容随缩放变，
//   40% 档读到节点屏上 `128×128`，而 60%/100% 档都读到 `75×75`。
//   🔑 `320 × 0.234 = 75` ⇒ **那两个「60%/100%」档其实量的是 23% 的视口**。
//   ⇒ 那三条读数**不是三种尺寸，是同一个尺寸被贴了三个档位标签**。
//
// 本轮方法（与批次 139 同款，且是 §4.15.6 缺的那一条）：**锁死同一个 `data-id`**，
//   每档**等实测 `scale()` 追平**再读 ⇒ 自变量真的只有缩放。
//   并且判据覆盖**两个假设之外的第三个**：不是「屏上恒定 or canvas 恒定」二选一，
//   而是量出 `屏上 / scale` 的**反推 canvas 值**看它到底跟不跟。
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 建N个, 可点落点, selCount, idsOf } from './jimeng-b139-lib.mjs';
import { findEmptyPane } from './jimeng-b136-lib.mjs';
import fs from 'node:fs';

const 档位 = [40, 60, 100, 200];
const rec = { 轮: '140b', 档位 };
let 全过 = true;
const 断言 = (名, ok, 详情) => { (rec.断言 = rec.断言 || []).push({ 名, 通过: !!ok, 详情 }); if (!ok) 全过 = false; };

const { b, p } = await openCanvas();
const R = readers(p);

/** 读「锁定的那一个节点」的把手几何。**只读**。 */
const 读节点把手 = (p, id) => p.evaluate((ID) => {
  const n = document.querySelector(`.react-flow__node[data-id="${ID}"]`);
  if (!n) return { __err: 'node-gone' };
  const box = (e) => { const r = e.getBoundingClientRect();
    return { x: Math.round(r.x * 10) / 10, y: Math.round(r.y * 10) / 10,
      w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10 }; };
  // 该节点内所有 `text-node-resize-*`（角 + 边），逐个带出 testid / 尺寸 / cursor
  const hs = Array.from(n.querySelectorAll('[data-testid^="text-node-resize-"]'));
  return {
    scale: (() => { const vp = document.querySelector('.react-flow__viewport');
      const m = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null;
      return m ? Math.round(parseFloat(m[1]) * 1000) / 1000 : null; })(),
    节点aria: n.getAttribute('aria-label'),
    节点屏上: box(n), 节点canvas: { w: n.offsetWidth, h: n.offsetHeight },
    选中: n.classList.contains('selected'),
    把手数: hs.length,
    把手: hs.map((e) => { const cs = getComputedStyle(e);
      return { testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
        屏上: box(e), offset: { w: e.offsetWidth, h: e.offsetHeight },
        cursor: cs.cursor, pe: cs.pointerEvents, borderRadius: cs.borderRadius }; })
      .sort((a, b2) => String(a.testid).localeCompare(String(b2.testid))),
  };
}, id);

try {
  await keyGuard(p);
  await settle(p, R);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p), zoom: await R.zoom() };
  断言('①起始 0 选中（不得有上轮残留选中态）', (await selCount(p)) === 0, { 选中: await selCount(p) });

  // ---- 靶子：**自己建一个**文本节点（比借用别人的更可控，且必然在视口中央）
  // 🔴 b 轮第一版用 `/文本|文字|text/i` 匹配 `aria-label` 找现成文本节点，候选数 **0** ——
  //   诊断显示画布上 3 个文本节点（`文本 node: 文本 1/2/3`）**全在视口可用区之外**
  //   （`视口可用区且有文本aria: 0`），而 45 个可用节点里**没有一个是文本节点**。
  //   ⇒ 借别人的节点不可靠，改为建一个自己的。
  const 建 = await 建N个(p, '文本', 1, 断言, 76);
  rec.建 = { ids: 建.ids, ok: 建.ok };
  if (!(建.ids && 建.ids.length === 1)) { rec.中止 = '建文本节点未成'; }
  else {
  const T = await p.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!n) return { __err: 'node-gone' };
    const r = n.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 6; y <= r.y + r.height - 6; y += 4)
      for (let x = Math.ceil(r.x) + 6; x <= r.x + r.width - 6; x += 4) {
        const h = document.elementFromPoint(x, y);
        if (h && h.closest && h.closest('.react-flow__node') === n && !h.closest('button,[role=button],[contenteditable],input,textarea'))
          return { id, aria: n.getAttribute('aria-label'), 落点: { x, y },
            屏上: { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) },
            canvas: { w: n.offsetWidth, h: n.offsetHeight } };
      }
    return { __err: 'no-point' };
  }, 建.ids[0]);
    rec.靶子 = T;
    await p.mouse.click(T.落点.x, T.落点.y);
    await p.waitForTimeout(1200);
    const 选中态 = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      return { 选中: !!(n && n.classList.contains('selected')), 选中数: document.querySelectorAll('.react-flow__node.selected').length }; }, T.id);
    rec.选中态 = 选中态;
    断言('③点后目标节点恰好选中', 选中态.选中 && 选中态.选中数 === 1, 选中态);

    // ---- 四档读数（锁死 data-id，等实测 scale 追平）
    rec.各档 = [];
    for (const pct of 档位) {
      const z = await setZoom(p, pct);
      const h = await 读节点把手(p, T.id);
      rec.各档.push({ 标称: pct, 追平: z.scale已追平, ...h });
      断言(`④${pct}% 实测 scale 已追平`, z.scale已追平, { z, 实测: h.scale });
    }
    // ---- 判定：角把手（square cursor） vs 边把手
    const 判一个 = (d) => {
      const 角 = (d.把手 || []).filter((h) => /nwse|nesw/.test(h.cursor || ''));
      const 边 = (d.把手 || []).filter((h) => /ns-resize|ew-resize/.test(h.cursor || ''));
      const 角值 = 角.map((h) => ({ testid: h.testid, 屏上: `${h.屏上.w}×${h.屏上.h}`,
        反推canvas: d.scale ? `${Math.round(h.屏上.w / d.scale * 10) / 10}×${Math.round(h.屏上.h / d.scale * 10) / 10}` : null }));
      const 边值 = 边.map((h) => ({ testid: h.testid, 屏上: `${h.屏上.w}×${h.屏上.h}`,
        反推canvas: d.scale ? `${Math.round(h.屏上.w / d.scale * 10) / 10}×${Math.round(h.屏上.h / d.scale * 10) / 10}` : null }));
      return { 标称: d.标称, scale: d.scale, 节点屏上: `${d.节点屏上.w}×${d.节点屏上.h}`, 节点canvas: `${d.节点canvas.w}×${d.节点canvas.h}`,
        把手数: d.把手数, 角, 边 };
    };
    rec.判定 = rec.各档.map(判一个);
    // 角把手屏上是否恒定
    const 角屏上 = new Set();
    for (const d of rec.各档) for (const h of d.把手 || []) if (/nwse|nesw/.test(h.cursor || '')) 角屏上.add(`${h.屏上.w}×${h.屏上.h}`);
    rec.角把手屏上去重 = [...角屏上];
    rec.角把手屏上恒定 = 角屏上.size === 1;
    断言('⑤角把手屏上恒定（这是 §4.15.6 缺的那条实测）', rec.角把手屏上恒定, { 各档去重: rec.角把手屏上恒定 ? rec.角把手屏上去重 : [...角屏上] });
    // 节点 canvas 四档恒定（证明锁死的是同一个节点）
    rec.节点canvas四档 = rec.各档.map((d) => `${d.节点canvas.w}×${d.节点canvas.h}`);
    断言('⑥节点 canvas 尺寸四档恒定（证明没换节点）', new Set(rec.节点canvas四档).size === 1, rec.节点canvas四档);
  }
} catch (e) { rec.异常 = String(e && e.stack || e).slice(0, 600); }

// 收尾：取消选中 + 删掉自建靶子 + 回 60% + 重开小地图
try {
  if (await selCount(p) > 0) { const 空 = await findEmptyPane(p); if (空) { await p.mouse.click(空.x, 空.y); await p.waitForTimeout(900); } }
  // 🔴 自建靶子必须删掉（共享画布）。走救援脚本同款配方：**先清 0 选中 → 单选 → 右键 → 删除**。
  if (rec.建 && rec.建.ids && rec.建.ids[0]) {
    const tid = rec.建.ids[0];
    const 落 = await 可点落点(p, `.react-flow__node[data-id="${tid}"]`, 4, 4);
    if (!落.__err) {
      await p.mouse.click(落.x, 落.y); await p.waitForTimeout(900);
      const 确 = await p.evaluate((id) => document.querySelectorAll('.react-flow__node.selected').length === 1
        && document.querySelector('.react-flow__node.selected').getAttribute('data-id') === id, tid);
      rec.靶子单选 = 确;
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
fs.writeFileSync(new URL('./_tmp-b140b.json', import.meta.url), JSON.stringify(rec, null, 1));
console.log(JSON.stringify({ 靶子: rec.靶子, 判定: rec.判定, 角把手屏上去重: rec.角把手屏上去重, 节点canvas四档: rec.节点canvas四档, 收尾: rec.收尾 }, null, 1));
console.log('断言全过', 全过);
await b.close();
