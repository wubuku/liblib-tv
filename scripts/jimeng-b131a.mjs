// 批次 131 · a 轮：**用框选**做多选，补上批次 129 三次都没验成的 `selection-context-toolbar`。
//
// 🔑 为什么换方法：批次 129 的 c/d/f 三轮都在「给节点找一个安全的落点」上栽了
//   （落点全是同一个节点 / 落点贴视口顶边 / 过滤条件把可见节点全排掉）。
//   ⇒ 立规：**读数异常先换方法，别在同一个假设上磨三次。**
//
// 🔑 关键认识（本轮的做法依据）：**框选与拖动节点的分野只在 `mousedown` 落在哪** ——
//   落在 `.react-flow__pane`（空白）= 进入框选模式，**后续鼠标路径穿过节点完全安全**；
//   落在节点上 = 拖动节点。所以只要把**按下点**校验成 pane，就不必约束整条路径。
//   这直接绕开了「找一个既在节点内又在安全区的点」这个死结。
//
// 📌 护栏：只框选、只读数，**不做任何拖动节点、不连线**；框完立即点 `.react-flow__pane` 取消。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b131a.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);
const collect = () => p.evaluate(() => { const s = new Set(); for (const e of document.querySelectorAll('[data-testid]')) s.add(e.getAttribute('data-testid')); return Array.from(s); });
const idsNow = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
// 位置指纹：用来证明「框选没有顺手拖动任何节点」
const posNow = () => p.evaluate(() => { const m = {}; for (const n of document.querySelectorAll('.react-flow__node')) { const r = n.getBoundingClientRect(); m[n.getAttribute('data-id')] = [Math.round(r.x), Math.round(r.y)]; } return m; });

out.start = { 状态行: await status(), 选中: await sel(), zoom: await zoom(), 浮层: await overlays() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
for (let i = 0; i < 2; i++) { if (await overlays()) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); } }
out.起始id = await idsNow();
const 基线testid = await collect();
const 基线位置 = await posNow();
log('静态基线 testid', 基线testid.length, '种｜节点', out.起始id.length, '个');
save();

// ---------------------------------------------------------------- ① 找一块能安全框选的空白
log('\n=== ① 规划框选矩形（按下点必须命中 .react-flow__pane）===');
const plan = await p.evaluate(() => {
  const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const r = n.getBoundingClientRect();
    return { id: n.getAttribute('data-id'), x: r.x, y: r.y, w: r.width, h: r.height, right: r.right, bottom: r.bottom };
  });
  const 在视口内 = nodes.filter((n) => n.right > 0 && n.x < innerWidth && n.bottom > 60 && n.y < innerHeight - 60);
  const isPane = (x, y) => { const h = document.elementFromPoint(x, y); return !!(h && h.classList && h.classList.contains('react-flow__pane')); };
  const isFree = (x, y) => !nodes.some((n) => x >= n.x && x <= n.right && y >= n.y && y <= n.bottom);
  // 目标：罩住 ≥2 个可见节点，同时四角都必须是「不在任何节点内」的
  for (let pad = 20; pad <= 200; pad += 10) {
    const xs = 在视口内.flatMap((n) => [n.x, n.right]), ys = 在视口内.flatMap((n) => [n.y, n.bottom]);
    const L = Math.min(...xs) - pad, R = Math.max(...xs) + pad, T = Math.max(Math.min(...ys), 62), B = Math.min(Math.max(...ys), innerHeight - 70);
    if (!(L > 4 && R < innerWidth - 300 && T > 60 && B < innerHeight - 60)) continue;
    const 角 = [[L, T], [R, T], [L, B], [R, B]];
    if (!角.every(([x, y]) => isPane(x, y) && isFree(x, y))) continue;
    const 罩住 = nodes.filter((n) => n.right > L && n.x < R && n.bottom > T && n.y < B).map((n) => n.id);
    if (罩住.length >= 2) return { ok: true, 矩形: [L, T, R, B].map(Math.round), 罩住节点数: 罩住.length, 罩住, 角全是pane且不在节点内: true, 可见节点数: 在视口内.length };
  }
  return { ok: false, 可见节点: 在视口内.map((n) => ({ id: n.id, x: Math.round(n.x), y: Math.round(n.y), right: Math.round(n.right), bottom: Math.round(n.bottom) })) };
});
out.框选计划 = plan;
log('  ', JSON.stringify(plan));
save();
if (!plan.ok) { log('  ⛔ 找不到安全的框选矩形'); process.exit(0); }

// ---------------------------------------------------------------- ② 执行框选
log('\n=== ② 执行框选（mousedown 落在 pane ⇒ 框选模式，后续路径可穿节点）===');
{
  const [L, T, R, B] = plan.矩形;
  await p.mouse.move(L, T);
  const h0 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y); return h ? h.tagName + '.' + (h.className || '').toString().split(' ')[0] : null; }, [L, T]);
  log('  按下点', L, T, '命中：', h0);
  await p.mouse.down();
  for (let i = 1; i <= 12; i++) {
    const x = Math.round(L + ((R - L) * i) / 12), y = Math.round(T + ((B - T) * i) / 12);
    await p.mouse.move(x, y);
    await p.waitForTimeout(60);
  }
  out.框选中途 = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__selection')).map((e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; }));
  log('  松开前的选择框 DOM：', JSON.stringify(out.框选中途));
  await p.mouse.up();
  await p.waitForTimeout(1400);
  out.框选后 = { 选中数: await sel(), 状态行: await status() };
  log('  松开后：选中数 =', out.框选后.选中数, '｜状态行', JSON.stringify(out.框选后.状态行));
  const 位置 = await posNow();
  out.位置变化 = Object.keys(位置).filter((k) => 位置[k][0] !== 基线位置[k][0] || 位置[k][1] !== 基线位置[k][1]);
  log('  🔑 位置发生变化的节点（必须为空 —— 证明没顺手拖动节点）：', JSON.stringify(out.位置变化));
  const ids2 = await idsNow();
  out.id变化 = { 多: ids2.filter((x) => !out.起始id.includes(x)), 少: out.起始id.filter((x) => !ids2.includes(x)) };
  log('  id 变化：多', JSON.stringify(out.id变化.多), '少', JSON.stringify(out.id变化.少));
  save();

  if (out.框选后.选中数 >= 2) {
    const 多选 = await collect();
    out.多选testid = { 种类: 多选.length, 增量: 多选.filter((t) => !基线testid.includes(t)), 减量: 基线testid.filter((t) => !多选.includes(t)) };
    log('\n  多选态 testid', 多选.length, '种');
    log('  **相对静态基线的增量**：', JSON.stringify(out.多选testid.增量));
    log('  相对静态基线的减量：', JSON.stringify(out.多选testid.减量));
    for (const t of ['selection-context-toolbar', 'selection-context-toolbar-surface', 'selection-context-toolbar-popup-host', 'selection-context-toolbar-count', 'node-toolbar'])
      log(`      ${t} → 多选态${多选.includes(t) ? '✅ 在' : '❌ 不在'}｜静态基线${基线testid.includes(t) ? '在' : '不在'}`);
    // 多选工具条完整 DOM 契约
    out.工具条 = await p.evaluate(() => {
      const r = (t) => { const e = document.querySelector('[data-testid="' + t + '"]'); if (!e) return { t, 存在: false };
        const q = e.getBoundingClientRect(); const cs = getComputedStyle(e);
        const 按钮 = Array.from(e.querySelectorAll('button,[role=button]')).map((x) => { const b = x.getBoundingClientRect();
          return { 文字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 14), aria: x.getAttribute('aria-label'), testid: x.getAttribute('data-testid'), 尺寸: [Math.round(b.width), Math.round(b.height)], 矩形: [Math.round(b.x), Math.round(b.y)] }; });
        return { t, 存在: true, tag: e.tagName, role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
          矩形: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)], display: cs.display, pe: cs.pointerEvents,
          逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60), 按钮数: 按钮.length, 按钮, 子元素数: e.children.length }; };
      return ['selection-context-toolbar', 'selection-context-toolbar-surface', 'selection-context-toolbar-count', 'selection-context-toolbar-popup-host', 'node-toolbar'].map(r);
    });
    log('\n  多选工具条 DOM 契约：');
    out.工具条.forEach((e) => {
      if (!e.存在) { log('      ·', e.t, '不存在'); return; }
      log(`      · ${e.t} <${e.tag}> ${e.矩形.join(',')} role=${e.role || '-'} pe=${e.pe} 按钮数=${e.按钮数} «${e.逐字}»`);
      e.按钮.forEach((btn) => log(`           · 按钮 «${btn.文字}» aria=${btn.aria} testid=${btn.testid} ${btn.尺寸.join('×')}@${btn.矩形.join(',')}`));
    });
    save();
  } else log('\n  ⛔ 选中数不足 2，未能验多选工具条');
  save();
}

// ---------------------------------------------------------------- ③ 点空白取消
log('\n=== ③ 取消多选 ===');
{
  const panePt = await p.evaluate(() => { for (let y = 300; y < 640; y += 7) for (let x = 300; x < 760; x += 7) { const h = document.elementFromPoint(x, y); if (h && h.classList && h.classList.contains('react-flow__pane')) return { x, y }; } return null; });
  out.取消落点 = panePt;
  if (panePt) { await p.mouse.click(panePt.x, panePt.y); await p.waitForTimeout(1200); }
  log('  点 pane', JSON.stringify(panePt), '→ 选中数', await sel());
}
await p.mouse.move(1276, 716); await p.waitForTimeout(700);

const endIds = await idsNow(); const endT = await collect();
out.收尾 = { 选中: await sel(), 状态行: await status(), 浮层: await overlays(), zoom: await zoom(), 节点数: endIds.length, 起始节点数: out.起始id.length, testid种类: endT.length };
out.新增id = endIds.filter((x) => !out.起始id.includes(x));
out.相对基线增量 = endT.filter((t) => !基线testid.includes(t));
out.相对基线减量 = 基线testid.filter((t) => !endT.includes(t));
log('\n收尾：', JSON.stringify(out.收尾));
log('  新增 id（必须空）：', JSON.stringify(out.新增id));
log('  testid 相对基线：增量', JSON.stringify(out.相对基线增量), '减量', JSON.stringify(out.相对基线减量));
save();
log('\nDONE a');
process.exit(0);
