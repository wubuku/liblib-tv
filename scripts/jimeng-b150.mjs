// 批次 150 —— 查清「**逐节点 counter-scale 变尺寸**」到底影响**哪些**元素。
//
// 🔑 靶子来自批次 149 的一个订正：`Add tags` 的屏上边长在同一画布 60% 下
//    实测到过 `24×24` / `28×28` / `29×29` 三种，批次 89 已给出机制
//    —— `24px × 视口 scale × 该节点各自的 --octo-canvas-node-chrome-counter-scale`。
//    但**全册还有多少尺寸是这么来的？手册里那些写死的数字有几条其实会变？**
//    这一批就是回答这个问题。
//
// 🔑 方法上的关键简化：**量尺寸不需要点击**。
//    `getBoundingClientRect()` 与遮挡无关 ⇒ 被别的节点压住的元素照样量得到。
//    所以本轮**不建「可点」的节点**，而是**建几个同类型节点、直接在 DOM 里逐个量**，
//    再逐元素**横向比对**。这样既避开了共享画布拥挤的落点问题，也完全不点任何东西。
//
// 本轮三问：
//   Q1 同类型的 N 个节点之间，**哪些元素的屏上尺寸不一致**（⇒ 手册的定值是错的）
//   Q2 跨类型之间同一元素（`flow-node-title` / `flow-node-selected-tag` / 标题行…）差多少
//   Q3 不一致的元素，其 **canvas 尺寸是否一致**（⇒ 若一致，说明是「同一 canvas 值 × 不同逐节点变量」）
//
// ⚠️ 建-删护栏全程生效：**建前基线 / 建后差集恰好 1 且 .selected / 右键「删除 ⌫」/
//    消失集合恰好 {SELF}**。不点任何生成/扣费按钮、不输入一个字。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, idsOf, canvasPos, 可点落点, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 150, 目的: '普查「逐节点 counter-scale 变尺寸」影响哪些元素' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b150.json', import.meta.url), JSON.stringify(rec, null, 1));

/** 量一个节点里每个「可命名元素」的屏上尺寸 + canvas 尺寸 + 逐节点 CSS 变量。 */
const 量节点 = (id) => p.evaluate((i) => {
  const n = document.querySelector('.react-flow__node[data-id="' + i + '"]');
  if (!n) return { __err: 'not-found' };
  const r = n.getBoundingClientRect();
  const cs = getComputedStyle(n);
  // 逐节点 CSS 变量：把节点上出现过的 --octo-canvas-* 全部读出来
  const 变量 = {};
  for (let k = 0; k < cs.length; k++) { const 名 = cs[k];
    if (名.startsWith('--octo-canvas')) 变量[名] = cs.getPropertyValue(名).trim(); }
  const 元素 = {};
  for (const e of n.querySelectorAll('[data-testid], .flow-node-title, [aria-label^="Add tags"], [aria-label^="Edit tags"], [aria-label^="Create connected node"]')) {
    const q = e.getBoundingClientRect(); const s = getComputedStyle(e);
    const key = e.getAttribute('data-testid') || ('aria:' + (e.getAttribute('aria-label') || '').slice(0, 18)) || e.tagName;
    if (元素[key]) continue;
    元素[key] = { 屏上: [Math.round(q.width * 10) / 10, Math.round(q.height * 10) / 10],
      字体: s.fontSize, 行高: s.lineHeight, padding: s.padding, 变量: (() => {
        const v = {}; for (let k = 0; k < s.length; k++) { const 名 = s[k];
          if (名.startsWith('--octo-canvas')) v[名] = s.getPropertyValue(名).trim(); } return v; })() };
  }
  return { 节点屏上: [Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10],
    class: n.className, aria: n.getAttribute('aria-label'), 变量, 元素 };
}, id);

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
  if (!归属.对) return { id, __err: 'wrong-target（被压住，量尺寸不需要删——本轮改为整组不删）' };
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

const { b, p } = await openCanvas();
const R = readers(p);
const 族表 = ['音频', '图片', '视频', '文本'];
try {
  await keyGuard(p); await settle(p, R);
  await setZoom(p, 60); await p.waitForTimeout(900);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(), 积分: await R.credits(), 组数: await 组数(p) };
  const 基线canvas = await canvasPos(p);

  rec.族 = [];
  for (const 族 of 族表) {
    const 条 = { 族, 缩放建前: await R.zoom() };
    // 🔴 建 3 个（同一批建，彼此叠放也不要紧——量尺寸与遮挡无关）
    const 建 = await 建N个(p, 族, 3, null, (await idsOf(p)).length);
    条.护栏 = 建.护栏.map((h) => [h.名, h.通过]);
    条.护栏全过 = 建.护栏.every((h) => h.通过);
    条.ids = 建.ids;
    if (!建.ids || !建.ids.length) { 条.__err = '建节点未成'; rec.族.push(条); 落盘(); continue; }
    await p.waitForTimeout(1500); await settle(p, R);
    条.缩放建后 = await R.zoom();
    条.量 = [];
    for (const id of 建.ids) 条.量.push(await 量节点(id));
    // 逐元素横向比对
    const 键集 = [...new Set(条.量.flatMap((m) => Object.keys(m.元素 || {})))];
    条.比对 = 键集.map((k) => ({
      元素: k,
      各节点屏上: 条.量.map((m) => (m.元素 && m.元素[k] ? m.元素[k].屏上 : null)),
      是否全同: new Set(条.量.map((m) => JSON.stringify(m.元素 && m.元素[k] ? m.元素[k].屏上 : null))).size === 1,
      各节点变量: 条.量.map((m) => (m.元素 && m.元素[k] ? m.元素[k].变量 : null)),
    }));
    条.节点变量 = 条.量.map((m) => m.变量);
    条.节点屏上 = 条.量.map((m) => m.节点屏上);
    // 逐个删
    条.删除 = [];
    for (const id of 建.ids) 条.删除.push(await 删一个(id));
    rec.族.push(条);
    await setZoom(p, 60); await p.waitForTimeout(800); await 清零();
    落盘();
  }
  const 末 = await idsOf(p); const 末c = await canvasPos(p);
  const 位移 = Object.keys(基线canvas).filter((k) => 末c[k] && (末c[k][0] !== 基线canvas[k][0] || 末c[k][1] !== 基线canvas[k][1]));
  rec.收尾检查 = { 节点数: 末.length, 位移节点: 位移 };
} catch (e) { rec.异常 = String((e && e.stack) || e).slice(0, 900); }

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
  浮层: await R.overlays(), zoom: await R.zoom(), 积分: await R.credits(), 组数: await 组数(p),
  边数: await p.evaluate(() => document.querySelectorAll('.react-flow__edge').length),
  残留自建: (await idsOf(p)).filter((x) => rec.族.some((q) => (q.ids || []).includes(x))) };

// ---- 出表 ----
console.log('=== 逐族：哪些元素在同族三个节点之间屏上尺寸不一致 ===');
for (const q of rec.族) {
  console.log('\n【' + q.族 + '】护栏', q.护栏全过, '| 缩放', q.缩放建后, '| 节点屏上', JSON.stringify(q.节点屏上));
  for (const b of (q.比对 || [])) console.log('  ', b.是否全同 ? '✅全同' : '🔴不一致', b.元素, JSON.stringify(b.各节点屏上));
  console.log('   删除:', JSON.stringify((q.删除 || []).map((d) => d.消失 || d.__err)));
}
console.log('\n收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');

断言('① 四族都建了 3 个并全部删除', rec.族.length === 4 && rec.族.every((q) => (q.删除 || []).length === 3), rec.族.map((q) => [q.族, (q.删除 || []).length]));
断言('② 每族的建-删护栏全过', rec.族.every((q) => q.护栏全过 === true), rec.族.map((q) => [q.族, q.护栏全过]));
断言('③ 每个删除的消失集合**恰好是 {SELF}**', rec.族.every((q) => (q.删除 || []).every((d) => d.消失 && d.消失.length === 1)), rec.族.map((q) => (q.删除 || []).map((d) => d.消失 || d.__err)));
const 有不一致 = rec.族.flatMap((q) => (q.比对 || []).filter((b) => !b.是否全同).map((b) => ({ 族: q.族, 元素: b.元素, 各: b.各节点屏上 })));
rec.有不一致 = 有不一致;
断言('④ 🔑 **确实存在**「同族内屏上尺寸不一致」的元素（⇒ 手册的定值有一批是错的）', 有不一致.length > 0, { 不一致条数: 有不一致.length });
if (rec.收尾检查) 断言('⑤ 终态节点数回到基线、其余节点零位移', rec.收尾检查.位移节点.length === 0, rec.收尾检查);

rec.断言全过 = 断言过; 落盘();
await b.close();
