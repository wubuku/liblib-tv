// 批次 151 · b 轮 —— 把 a 轮读出来的**上限**钉死。
//
// a 轮（`_tmp-b151.json` 的 `缩放档`）实测：
//   实测 scale 0.6  ⇒ 补偿系数 k = 1.6667 = 1/0.6
//   实测 scale 0.8  ⇒ k = 1.2500 = 1/0.8
//   实测 scale 0.4  ⇒ k = **2.0000**，而 1/0.4 = 2.5  ⇒ **不是 1/s**
//
// ⇒ 三档读数**恰好**符合 `k = min(1/scale, 2)`。
//    但「恰好符合」还只是拟合 —— 🔑 **下界没验过**：如果 30%（1/s = 3.33）读出来
//    还是 2.0，才算坐实上限；如果读出别的值，说明那条公式也不对。
//
// 本轮只做一件事：文本族建 3 个，在 **6 档**缩放上读
//   `--octo-canvas-node-chrome-counter-scale`（变量本身是否被截断）
//   + `flow-node-title` / `flow-node-selected-tag` 的 css 与屏上。
// 判据（不预设具体数值，只判自洽）：
//   ① k(元素) 在 6 档上是否**两两相同** ⇒ 若同，说明两个元素共用同一个 k
//   ② k 与 1/s 的关系：取 `1/s > 2` 的档位，看 k 是否恒等于 2
//   ③ 变量本身是否等于 k（变量被截断）还是等于 1/s（k 是别处算出来的）
//
// ⚠️ 建-删护栏全程生效；不点任何生成/扣费按钮、不输入一个字、不按任何字母键。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, idsOf, canvasPos, 可点落点, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 151, 轮次: 'b', 目的: '把 a 轮读出的补偿系数上限钉死：6 档缩放读变量本身 + css + 屏上' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b151b.json', import.meta.url), JSON.stringify(rec, null, 1));

const 实测scale = () => p.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const t = v && getComputedStyle(v).transform;
  const m = t && t.match(/matrix\(([^)]+)\)/);
  return m ? Number(m[1].split(',')[0].trim()) : null;
});

const 量3 = () => p.evaluate(() => {
  const 读 = (sel) => Array.from(document.querySelectorAll(sel)).slice(0, 3).map((e) => {
    const q = e.getBoundingClientRect(); const s = getComputedStyle(e);
    return { 屏上: [Math.round(q.width * 1000) / 1000, Math.round(q.height * 1000) / 1000],
      css: [s.width, s.height], 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20) };
  });
  const 变量 = (() => {
    const n = document.querySelector('.react-flow__node-text');
    if (!n) return null;
    const cs = getComputedStyle(n); const v = {};
    for (let k = 0; k < cs.length; k++) { const 名 = cs[k];
      if (名.startsWith('--octo-canvas')) v[名] = cs.getPropertyValue(名).trim(); }
    return v; })();
  return { 标题: 读('.react-flow__node-text .flow-node-title'),
    标签: 读('.react-flow__node-text [data-testid="flow-node-selected-tag"]'),
    节点数: document.querySelectorAll('.react-flow__node-text').length, 变量 };
});

const 清零 = async () => {
  for (let k = 0; k < 4 && (await selCount(p)) > 0; k++) {
    const 空 = await p.evaluate(() => {
      const 坏 = (x, y) => { const h = document.elementFromPoint(x, y);
        if (!h) return 1;
        if (h.tagName === 'BUTTON' || h.getAttribute('role') === 'button' || h.closest('button,[role=button]')) return 1;
        if (h.closest('.react-flow__node') || h.closest('[data-testid="node-toolbar"]') || h.closest('[role=dialog],[role=menu],[role=listbox]')) return 1;
        return !(h.classList && h.classList.contains('react-flow__pane')); };
      for (let y = 90; y < innerHeight - 90; y += 8) for (let x = 360; x < innerWidth - 350; x += 8) if (!坏(x, y)) return { x, y };
      return { __err: 'no-free-pane' };
    });
    if (空.__err) break;
    await p.mouse.click(空.x, 空.y); await p.waitForTimeout(1000);
  }
  return selCount(p);
};

const 删一个 = async (id) => {
  await 清零();
  const 前 = await idsOf(p);
  const 落 = await 可点落点(p, `.react-flow__node[data-id="${id}"]`, 4, 4);
  if (落.__err) return { id, __err: 'no-point' };
  const 归属 = await p.evaluate(([x, y, i]) => { const h = document.elementFromPoint(x, y);
    const n = h && h.closest('.react-flow__node'); return { 对: !!(n && n.getAttribute('data-id') === i) }; }, [落.x, 落.y, id]);
  if (!归属.对) return { id, __err: 'wrong-target（被压住）' };
  await p.mouse.click(落.x, 落.y, { button: 'right' }); await p.waitForTimeout(1800);
  const del = await p.evaluate(() => {
    const els = Array.from(document.querySelectorAll('[role=menuitem],[role=menu] button,li,button'))
      .filter((e) => /^删除/.test((e.innerText || '').replace(/\s+/g, '').trim()));
    if (!els.length) return { __err: 'no-delete-item' };
    const e = els[0]; const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2)
      for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) {
        const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim() }; }
    return { __err: 'no-point' };
  });
  if (del.__err) return { id, __err: del.__err };
  await p.mouse.click(del.x, del.y); await p.waitForTimeout(2500); await settle(p, R);
  const 后 = await idsOf(p);
  return { id, 消失: 前.filter((x) => !后.includes(x)), 删除项逐字: del.逐字 };
};

const 档位 = [60, 50, 45, 40, 30, 25];

const { b, p } = await openCanvas();
const R = readers(p);
let 基线canvas = null;
try {
  await keyGuard(p); await settle(p, R);
  await setZoom(p, 60); await p.waitForTimeout(900);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(),
    实测scale: await 实测scale(), 积分: await R.credits(), 组数: await 组数(p), 选中: await selCount(p) };
  基线canvas = await canvasPos(p);

  const 建 = await 建N个(p, '文本', 3, null, (await idsOf(p)).length);
  rec.ids = 建.ids;
  rec.护栏 = 建.护栏.map((h) => [h.名, h.通过]);
  rec.护栏全过 = 建.护栏.every((h) => h.通过);
  rec.档 = [];
  if (建.ids && 建.ids.length) {
    await p.waitForTimeout(1500); await settle(p, R);
    for (const pct of 档位) {
      await setZoom(p, pct); await p.waitForTimeout(1400); await settle(p, R);
      const s = await 实测scale();
      const q = await 量3();
      const k = (屏, cssv) => (屏 && cssv ? Number((parseFloat(屏) / (parseFloat(cssv) * s)).toFixed(4)) : null);
      rec.档.push({ 设: pct, aria: await R.zoom(), 实测scale: s, 一比缩放: s ? Number((1 / s).toFixed(4)) : null,
        读: q,
        k_标题: (q.标题[0] ? k(q.标题[0].屏上[0], q.标题[0].css[0]) : null),
        k_标题高: (q.标题[0] ? k(q.标题[0].屏上[1], q.标题[0].css[1]) : null),
        k_标签: (q.标签[0] ? k(q.标签[0].屏上[0], q.标签[0].css[0]) : null),
        k_标签高: (q.标签[0] ? k(q.标签[0].屏上[1], q.标签[0].css[1]) : null),
        变量_chrome: q.变量 && q.变量['--octo-canvas-node-chrome-counter-scale'],
        变量_tagHit: q.变量 && q.变量['--octo-canvas-node-tag-hit-area-counter-scale'],
      });
      落盘();
    }
    await setZoom(p, 60); await p.waitForTimeout(900); await 清零();
    rec.删除 = [];
    for (const id of 建.ids) rec.删除.push(await 删一个(id));
  }
  const 末 = await idsOf(p); const 末c = await canvasPos(p);
  rec.收尾检查 = { 节点数: 末.length,
    位移节点: 基线canvas ? Object.keys(基线canvas).filter((k) => 末c[k] && (末c[k][0] !== 基线canvas[k][0] || 末c[k][1] !== 基线canvas[k][1])) : null };
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); 落盘(); }

await setZoom(p, 60); await p.waitForTimeout(900);
for (let k = 0; k < 3 && (await R.overlays()) > 0; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(800); }
await 清零();
const 小地图前 = await R.minimap();
if (!小地图前 || 小地图前.ariaPressed !== 'true') {
  const t = await 可点落点(p, '[data-testid="canvas-display-toggle-minimap"]', 3, 3);
  if (!t.__err) { await p.mouse.click(t.x, t.y); await p.waitForTimeout(1400); }
}
rec.小地图后 = await R.minimap();
await settle(p, R);
rec.收尾 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, 选中: await selCount(p),
  浮层: await R.overlays(), zoom: await R.zoom(), 实测scale: await 实测scale(), 积分: await R.credits(), 组数: await 组数(p),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length),
  残留自建: (await idsOf(p)).filter((x) => (rec.ids || []).includes(x)) };

console.log('=== 6 档缩放：变量本身 vs 补偿系数 k ===');
console.log('设    aria              实测scale   1/s      变量_chrome   k_标题    k_标签');
for (const d of (rec.档 || []))
  console.log(String(d.设).padEnd(5) + String(d.aria).padEnd(18) + String(d.实测scale).padEnd(12) + String(d.一比缩放).padEnd(9) + String(d.变量_chrome).padEnd(13) + String(d.k_标题).padEnd(9) + String(d.k_标签));
console.log('\n删除', JSON.stringify((rec.删除 || []).map((d) => d.消失 || d.__err)));
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');

断言('① 建 3 个并全部删除', (rec.删除 || []).length === 3, (rec.删除 || []).length);
断言('② 建-删护栏全过', rec.护栏全过 === true, rec.护栏);
断言('③ 每个删除的消失集合恰好 {SELF}', (rec.删除 || []).every((d) => d.消失 && d.消失.length === 1), (rec.删除 || []).map((d) => d.消失 || d.__err));
断言('④ 6 档缩放全部读到读数', (rec.档 || []).length === 档位.length && rec.档.every((d) => d.k_标题 != null && d.k_标签 != null), (rec.档 || []).map((d) => [d.设, d.k_标题, d.k_标签]));
// 判据（只判自洽，不预设具体数值）
const 超过2 = (rec.档 || []).filter((d) => d.一比缩放 != null && d.一比缩放 > 2);
const 恒2 = 超过2.length > 0 && 超过2.every((d) => d.k_标签 === 2 && d.k_标题 <= 2.001);
rec.超过2的档 = 超过2.map((d) => ({ 设: d.设, 一比缩放: d.一比缩放, k_标题: d.k_标题, k_标签: d.k_标签, 变量: d.变量_chrome }));
断言('⑤ 🔑 `1/s > 2` 的档位上 **k 恒等于 2**（坐实上限，不只是拟合 3 点）', 恒2, 超过2.map((d) => [d.设, d.一比缩放, d.k_标题, d.k_标签]));
const 未超 = (rec.档 || []).filter((d) => d.一比缩放 != null && d.一比缩放 <= 2);
const 合公式 = 未超.length > 0 && 未超.every((d) => Math.abs(d.k_标签 - d.一比缩放) < 0.002);
rec.未超2的档 = 未超.map((d) => ({ 设: d.设, 一比缩放: d.一比缩放, k_标题: d.k_标题, k_标签: d.k_标签 }));
断言('⑥ `1/s ≤ 2` 的档位上 **k = 1/s**（两段拼起来才是一条公式）', 合公式, 未超.map((d) => [d.设, d.一比缩放, d.k_标题, d.k_标签]));
if (rec.收尾检查 && rec.收尾检查.位移节点) 断言('⑦ 其余节点零位移', rec.收尾检查.位移节点.length === 0, rec.收尾检查);

rec.断言全过 = 断言过; 落盘();
await b.close();
