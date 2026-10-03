// 批次 131 · d 轮：钉死「多选工具条里到底有没有 Add tags」—— 它与本册一条明确断言冲突。
//
// 🔴 冲突点：`organize-group-layout.md:54` 写着
//   「⚠️ **多选工具条里没有「Add tags」** —— 逐字核对工具条内容只有上表四项。
//     `Add tags` 是**每个节点自己的**标记按钮（DOM `flow-node-selected-tag`），
//     出现在节点标题行右侧，**不属于顶部工具条**。」
// 而 c 轮实测：多选态下
//   `selection-context-toolbar`（基座）= 3 个按钮（编组/布局/下载）**确实没有** Add tags；
//   但 `selection-context-toolbar-surface` 与 `node-toolbar`（它们的外层，**同矩形 624×40**）
//   都各有 **4** 个按钮，第 4 个就是 **`Add tags`，testid `flow-node-selected-tag`**，
//   位置 `24×24@670,-174`（紧贴工具条右端）。
//
// 📌 关键问题：`flow-node-selected-tag` 在批次 130 刚被记成「**每节点一个**的选中标记」，
//   画布上有 76 个节点 ⇒ 常态应有 76 个实例。多选时**总数变成多少**？工具条里那个
//   是**第 77 个新实例**，还是**某个已有实例被搬到了工具条里**？本轮数清楚。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'd' };
const save = () => writeFileSync(new URL('./_tmp-b131d.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);
const idsNow = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const posNow = () => p.evaluate(() => { const m = {}; for (const n of document.querySelectorAll('.react-flow__node')) { const r = n.getBoundingClientRect(); m[n.getAttribute('data-id')] = [Math.round(r.x), Math.round(r.y)]; } return m; });

out.start = { 状态行: await status(), 选中: await sel(), zoom: await zoom() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
for (let i = 0; i < 2; i++) { if (await overlays()) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); } }
out.起始id = await idsNow();
const 基线位置 = await posNow();

const 数AddTags = (label) => p.evaluate((lb) => {
  const els = Array.from(document.querySelectorAll('[data-testid="flow-node-selected-tag"]'));
  const 归类 = els.map((e) => {
    const r = e.getBoundingClientRect();
    const 宿主 = e.closest('[data-testid]');
    const 宿主tid = 宿主 ? 宿主.getAttribute('data-testid') : null;
    const 在节点里 = !!e.closest('.react-flow__node');
    return { 宿主tid, 在节点里, aria: e.getAttribute('aria-label'), 矩形: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      尺寸: [Math.round(r.width), Math.round(r.height)] };
  });
  return { 状态: lb, 总数: els.length, 在节点里的: 归类.filter((x) => x.在节点里).length,
    在工具条里的: 归类.filter((x) => !x.在节点里),
    宿主分布: 归类.reduce((m, x) => { const k = (x.在节点里 ? '节点内' : '工具条内') + (x.宿主tid ? ':' + x.宿主tid : ''); m[k] = (m[k] || 0) + 1; return m; }, {}) };
}, label);

// ---------------------------------------------------------------- ① 静态态基线
log('\n=== ① 静态态：flow-node-selected-tag 有多少个 ===');
out.静态 = await 数AddTags('静态 0 选中');
log('  总数', out.静态.总数, '｜在节点里的', out.静态.在节点里的, '｜在工具条里的', JSON.stringify(out.静态.在工具条里的));
log('  宿主分布', JSON.stringify(out.静态.宿主分布));
save();

// ---------------------------------------------------------------- ② 单选
log('\n=== ② 单选一个音频节点 ===');
{
  const pt = await p.evaluate(() => {
    for (const n of document.querySelectorAll('.react-flow__node-audio')) {
      const r = n.getBoundingClientRect();
      for (let y = 60; y <= Math.min(150, r.bottom - 4); y += 5)
        for (let x = Math.ceil(r.x) + 6; x <= r.right - 6; x += 8) {
          const h = document.elementFromPoint(x, y);
          if (!h || !(h === n || n.contains(h))) continue;
          if (h.closest('button,[role=button]')) continue;
          return { x, y, id: n.getAttribute('data-id') };
        }
    }
    return { __err: 'no-point' };
  });
  out.单选落点 = pt;
  if (pt.__err) log('  ⛔', pt.__err);
  else {
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1400);
    out.单选数 = await sel();
    log('  落点', JSON.stringify(pt), '→ 选中数', out.单选数);
    if (out.单选数 === 1) { out.单选 = await 数AddTags('单选 1 个'); log('  总数', out.单选.总数, '｜在节点里的', out.单选.在节点里的, '｜在工具条里的', JSON.stringify(out.单选.在工具条里的));
      log('  宿主分布', JSON.stringify(out.单选.宿主分布)); save(); }
  }
  const panePt = await p.evaluate(() => { for (let y = 300; y < 640; y += 7) for (let x = 300; x < 760; x += 7) { const h = document.elementFromPoint(x, y); if (h && h.classList && h.classList.contains('react-flow__pane')) return { x, y }; } return null; });
  if (panePt) { await p.mouse.click(panePt.x, panePt.y); await p.waitForTimeout(1100); }
}

// ---------------------------------------------------------------- ③ 多选
log('\n=== ③ 框选多选（8 个）===');
{
  const plan = await p.evaluate(() => {
    const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => { const r = n.getBoundingClientRect(); return { x: r.x, y: r.y, right: r.right, bottom: r.bottom }; });
    const isPane = (x, y) => { const h = document.elementFromPoint(x, y); return !!(h && h.classList && h.classList.contains('react-flow__pane')); };
    const isFree = (x, y) => !nodes.some((n) => x >= n.x && x <= n.right && y >= n.y && y <= n.bottom);
    for (let pad = 20; pad <= 200; pad += 10) {
      const vis = nodes.filter((n) => n.right > 0 && n.x < innerWidth && n.bottom > 60 && n.y < innerHeight - 60);
      const xs = vis.flatMap((n) => [n.x, n.right]), ys = vis.flatMap((n) => [n.y, n.bottom]);
      const L = Math.min(...xs) - pad, R = Math.max(...xs) + pad, T = Math.max(Math.min(...ys), 62), B = Math.min(Math.max(...ys), innerHeight - 70);
      if (!(L > 4 && R < innerWidth - 300 && T > 60 && B < innerHeight - 60)) continue;
      if (![[L, T], [R, T], [L, B], [R, B]].every(([x, y]) => isPane(x, y) && isFree(x, y))) continue;
      if (nodes.filter((n) => n.right > L && n.x < R && n.bottom > T && n.y < B).length >= 2)
        return { 矩形: [L, T, R, B].map(Math.round), 罩住节点数: nodes.filter((n) => n.right > L && n.x < R && n.bottom > T && n.y < B).length };
    }
    return null;
  });
  out.框选计划 = plan;
  if (!plan) log('  ⛔ 无安全矩形');
  else {
    const [L, T, R, B] = plan.矩形;
    await p.mouse.move(L, T);
    await p.mouse.down();
    for (let i = 1; i <= 12; i++) { await p.mouse.move(Math.round(L + ((R - L) * i) / 12), Math.round(T + ((B - T) * i) / 12)); await p.waitForTimeout(55); }
    await p.mouse.up(); await p.waitForTimeout(1400);
    out.多选数 = await sel();
    const 位置 = await posNow();
    out.位置变化 = Object.keys(位置).filter((k) => 位置[k][0] !== 基线位置[k][0] || 位置[k][1] !== 基线位置[k][1]);
    log('  框', JSON.stringify(plan.矩形), '→ 选中数', out.多选数, '｜位置变化', JSON.stringify(out.位置变化));
    if (out.多选数 >= 2) {
      out.多选 = await 数AddTags(`多选 ${out.多选数} 个`);
      log('  🔑 总数', out.多选.总数, '｜在节点里的', out.多选.在节点里的);
      log('  **在工具条（节点外）里的**：', JSON.stringify(out.多选.在工具条里的));
      log('  宿主分布', JSON.stringify(out.多选.宿主分布));
      save();
    }
  }
}

// ---------------------------------------------------------------- ④ 三个工具条层各自的按钮数
log('\n=== ④ 三个「工具条」层各自的按钮，逐个点名 ===');
out.四层按钮 = await p.evaluate(() => {
  const rd = (t) => { const e = document.querySelector('[data-testid="' + t + '"]'); if (!e) return { t, 存在: false };
    const r = e.getBoundingClientRect();
    return { t, 存在: true, 矩形: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      直接子按钮: Array.from(e.children).filter((c) => c.tagName === 'BUTTON' || c.getAttribute('role') === 'button').length,
      全部后代按钮: Array.from(e.querySelectorAll('button,[role=button]')).length,
      逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) }; };
  return ['selection-context-toolbar', 'selection-context-toolbar-surface', 'node-toolbar', 'node-toolbar-feature-host'].map(rd);
});
out.四层按钮.forEach((e) => { if (!e.存在) { log(`  · ${e.t} —— 不存在`); return; }
  log(`  · ${e.t} ${e.矩形.join(',')} 直接子按钮=${e.直接子按钮} 后代按钮=${e.全部后代按钮} «${e.逐字}»`); });
save();

// ---------------------------------------------------------------- 收尾
{
  const panePt = await p.evaluate(() => { for (let y = 300; y < 640; y += 7) for (let x = 300; x < 760; x += 7) { const h = document.elementFromPoint(x, y); if (h && h.classList && h.classList.contains('react-flow__pane')) return { x, y }; } return null; });
  if (panePt) { await p.mouse.click(panePt.x, panePt.y); await p.waitForTimeout(1200); }
}
await p.mouse.move(1276, 716); await p.waitForTimeout(700);
const endIds = await idsNow();
out.收尾 = { 选中: await sel(), 状态行: await status(), 浮层: await overlays(), zoom: await zoom(), 节点数: endIds.length, 起始节点数: out.起始id.length };
out.新增id = endIds.filter((x) => !out.起始id.includes(x));
out.收尾后AddTags = await 数AddTags('收尾 0 选中');
log('\n收尾：', JSON.stringify(out.收尾));
log('  新增 id（必须空）：', JSON.stringify(out.新增id));
log('  收尾后 Add tags 总数：', out.收尾后AddTags.总数, '｜工具条内', JSON.stringify(out.收尾后AddTags.在工具条里的));
save();
log('\nDONE d');
process.exit(0);
