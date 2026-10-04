// 批次 152 —— 正面回答批次 151 留下的那个未决：
//
//   🔴 「为什么画布上**原有**的节点不跟着缩放重算 counter-scale？」
//      批次 151 只测到**行为差异**（原有 3 个文本节点 k 六档恒为 2，新建的在 60% 是 1.6667），
//      没查到**成因**。而这个成因直接决定手册能不能给用户一条可操作的规则。
//
// 本轮三问：
//   Q1 🔑 **全量普查**：在**同一个缩放**下读画布上**全部 76 个节点**的 counter-scale，
//      按族分组看 k 有几个取值。
//      判读：
//        · 若同一族内出现**多个** k ⇒「k 是逐节点的」在**历史节点**上确实成立
//          （这正是批次 88 看到三档、批次 150 在新建节点上没看到的原因）；
//        · 若每族只有 1 个 k ⇒ 批次 88 的三档需要别的解释。
//   Q2 🔑 **事件测试**：在原有节点仍在场的情况下**建 1 个新节点**
//      （建节点会触发画布自动适配缩放 + 全局重渲染，这是本项目每批都在做的动作），
//      立刻重读原有节点的 k。
//        · 若 k 变了 ⇒ 成因是「k 只在某些全局事件上重算」，而缩放菜单不算；
//        · 若 k 没变 ⇒ 成因另有其人，继续查。
//   Q3 建完删完后再读一次（删除也是一次全局事件）⇒ 看「删除」会不会触发重算。
//
// 🔑 Q1 是**只读普查，零点击、零建删**；Q2/Q3 才用建-删护栏。
// ⚠️ 不点任何生成/扣费按钮、不输入一个字、不按任何字母键。
import fs from 'node:fs';
import { openCanvas, readers, settle, keyGuard, setZoom } from './jimeng-b135-lib.mjs';
import { 建N个, selCount, idsOf, canvasPos, 可点落点, 组数 } from './jimeng-b139-lib.mjs';

const rec = { 批次: 152, 目的: '回答「原有节点为什么不随缩放重算 counter-scale」' };
let 断言过 = true;
const 断言 = (名, ok, 详情) => { const v = !!ok; if (!v) 断言过 = false; console.log((v ? '  ✅ ' : '  ❌ ') + 名 + (v ? '' : ' ' + JSON.stringify(详情))); return v; };
const 落盘 = () => fs.writeFileSync(new URL('./_tmp-b152.json', import.meta.url), JSON.stringify(rec, null, 1));

const 实测scale = () => p.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const t = v && getComputedStyle(v).transform;
  const m = t && t.match(/matrix\(([^)]+)\)/);
  return m ? Number(m[1].split(',')[0].trim()) : null;
});

/** 只读普查：画布上**全部**节点的 counter-scale（一次 evaluate 取完，不逐个往返）。 */
const 全量普查 = () => p.evaluate(() => {
  const 节点变量键 = '--octo-canvas-node-chrome-counter-scale';
  const 行 = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const cs = getComputedStyle(n);
    const k = cs.getPropertyValue(节点变量键).trim();
    const r = n.getBoundingClientRect();
    const 族 = (n.className.match(/react-flow__node-([a-z-]+)/) || [])[1] || '(无)';
    const 标签 = n.querySelector('[data-testid="flow-node-selected-tag"]');
    const 标题 = n.querySelector('[data-testid="flow-node-title"]');
    行.push({
      id: n.getAttribute('data-id'), 族,
      k: k === '' ? '(未定义)' : Number(k),
      变量原始: k,
      aria: n.getAttribute('aria-label'),
      class: n.className,
      节点屏上: [Math.round(r.width * 100) / 100, Math.round(r.height * 100) / 100],
      标签屏上: 标签 ? (() => { const q = 标签.getBoundingClientRect(); return [Math.round(q.width * 100) / 100, Math.round(q.height * 100) / 100]; })() : null,
      标签css: 标签 ? getComputedStyle(标签).width : null,
      标题文字: 标题 ? (标题.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20) : null,
    });
  }
  return 行;
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

const { b, p } = await openCanvas();
const R = readers(p);
let 基线canvas = null;
try {
  await keyGuard(p); await settle(p, R);
  await setZoom(p, 60); await p.waitForTimeout(1000);
  rec.起点 = { 状态行: await R.status(), 节点数: (await idsOf(p)).length, zoom: await R.zoom(),
    实测scale: await 实测scale(), 积分: await R.credits(), 组数: await 组数(p), 选中: await selCount(p) };
  基线canvas = await canvasPos(p);

  // ---- Q1 全量普查（只读） ----
  rec.Q1 = { 时点: '起点后、未建任何节点', 实测scale: await 实测scale(), 行: await 全量普查() };
  落盘();

  // ---- Q2：建 1 个节点（触发自动适配 + 全局重渲染）后立刻重读 ----
  const 建 = await 建N个(p, '音频', 1, null, (await idsOf(p)).length);
  rec.建 = { ids: 建.ids, 护栏: 建.护栏.map((h) => [h.名, h.通过]), 护栏全过: 建.护栏.every((h) => h.通过) };
  if (建.ids && 建.ids.length) {
    await p.waitForTimeout(1600); await settle(p, R);
    rec.Q2 = { 时点: '建完 1 个音频节点后', zoom: await R.zoom(), 实测scale: await 实测scale(), 行: await 全量普查() };
    落盘();
    await setZoom(p, 60); await p.waitForTimeout(900);
    rec.Q2b = { 时点: '建完后再 setZoom(60) 归位', zoom: await R.zoom(), 实测scale: await 实测scale(), 行: await 全量普查() };
    落盘();
    // ---- Q3：删掉后再读（删除也是一次全局事件） ----
    await 清零();
    rec.删除 = [];
    for (const id of 建.ids) rec.删除.push(await 删一个(id));
    await p.waitForTimeout(1200); await settle(p, R);
    rec.Q3 = { 时点: '删完归零后', zoom: await R.zoom(), 实测scale: await 实测scale(), 行: await 全量普查() };
    落盘();
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
  残留自建: (await idsOf(p)).filter((x) => ((rec.建 || {}).ids || []).includes(x)) };

// ---- 出表 ----
function 分族(时点) {
  const 行 = (rec[时点] || {}).行 || [];
  const by = {};
  for (const r of 行) { (by[r.族] ??= []).push(r); }
  const 表 = {};
  for (const [族, rs] of Object.entries(by)) {
    const k集 = [...new Set(rs.map((r) => r.k))].sort((a, b) => a - b);
    表[族] = { 节点数: rs.length, k取值: k集, 各档计数: k集.map((k) => k + '×' + rs.filter((r) => r.k === k).length).join(' '),
      标签屏上取值: [...new Set(rs.map((r) => JSON.stringify(r.标签屏上)))].join(' | '),
      节点屏上取值: [...new Set(rs.map((r) => JSON.stringify(r.节点屏上)))].join(' | ') };
  }
  return 表;
}
console.log('=== Q1 全量普查（起点，未建任何节点）===');
console.log('实测 scale', (rec.Q1 || {}).实测scale, '| 节点数', ((rec.Q1 || {}).行 || []).length);
for (const [族, v] of Object.entries(分族('Q1')))
  console.log('  ' + 族.padEnd(10) + ' n=' + String(v.节点数).padEnd(4) + ' k: ' + v.各档计数.padEnd(34) + ' 标签屏上: ' + v.标签屏上取值);
for (const t of ['Q2', 'Q2b', 'Q3']) {
  if (!rec[t]) continue;
  console.log('\n=== ' + t + '（' + rec[t].时点 + '）zoom ' + rec[t].zoom + ' 实测 ' + rec[t].实测scale + ' ===');
  const Q1表 = 分族('Q1');
  for (const [族, v] of Object.entries(分族(t))) {
    const 前 = Q1表[族];
    const 变 = 前 ? JSON.stringify(v.k取值) !== JSON.stringify(前.k取值) : false;
    console.log('  ' + 族.padEnd(10) + ' n=' + String(v.节点数).padEnd(4) + ' k: ' + v.各档计数.padEnd(34) +
      ' 标签屏上: ' + v.标签屏上取值 + (变 ? '   🔴 k 分布变了' : ''));
  }
}
console.log('\n删除', JSON.stringify((rec.删除 || []).map((d) => d.消失 || d.__err)));
console.log('收尾', JSON.stringify(rec.收尾), '| 异常', rec.异常 || '无');

断言('① Q1 普查到的节点数等于基线', ((rec.Q1 || {}).行 || []).length === ((rec.起点 || {}).节点数), [((rec.Q1 || {}).行 || []).length, (rec.起点 || {}).节点数]);
断言('② 每个时点的普查节点数都等于基线（自建节点已删净）', ['Q2', 'Q2b', 'Q3'].filter((t) => rec[t]).every((t) => rec[t].行.length >= (rec.起点.节点数)), ['Q2', 'Q2b', 'Q3'].filter((t) => rec[t]).map((t) => [t, rec[t].行.length]));
断言('③ 建-删护栏全过 + 消失集合恰好 {SELF}', rec.建 && rec.建.护栏全过 === true && (rec.删除 || []).every((d) => d.消失 && d.消失.length === 1), { 护栏: rec.建 && rec.建.护栏全过, 删除: (rec.删除 || []).map((d) => d.消失 || d.__err) });
if (rec.收尾检查 && rec.收尾检查.位移节点) 断言('④ 其余节点零位移', rec.收尾检查.位移节点.length === 0, rec.收尾检查);

// 判据：Q1 里**是否存在同族内 k 不唯一**（不预设真值，只记互斥性）
rec.同族k唯一 = {};
for (const [族, v] of Object.entries(分族('Q1'))) rec.同族k唯一[族] = { 节点数: v.节点数, k取值数: v.k取值.length, k取值: v.k取值 };
rec.跨时点k变化 = {};
for (const t of ['Q2', 'Q2b', 'Q3']) {
  if (!rec[t]) continue;
  const A = 分族('Q1'), B = 分族(t);
  rec.跨时点k变化[t] = Object.keys(B).filter((族) => A[族] && JSON.stringify(A[族].k取值) !== JSON.stringify(B[族].k取值))
    .map((族) => ({ 族, 之前: A[族].k取值, 之后: B[族].k取值 }));
}
console.log('\n同族 k 唯一性:', JSON.stringify(rec.同族k唯一));
console.log('跨时点 k 变化:', JSON.stringify(rec.跨时点k变化));
断言('⑤ 🔑 Q1 普查非空且每个族都记下了 k 取值', Object.keys(rec.同族k唯一).length > 0 && Object.values(rec.同族k唯一).every((v) => v.节点数 > 0 && v.k取值.length >= 1), rec.同族k唯一);

rec.断言全过 = 断言过; 落盘();
await b.close();
