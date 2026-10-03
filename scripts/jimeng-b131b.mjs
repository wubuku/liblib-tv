// 批次 131 · b 轮：单选 vs 多选下工具条三层的**语义差异**，加 `flow-node-multi-selection-*` 新层解剖。
//
// 🔑 a 轮已确认：框选（mousedown 落在 `.react-flow__pane`）一次罩住 8 个节点，
//   `selection-context-toolbar` 及其三层全部出现，**位置零变化、id 零变化** ⇒ 方法有效。
//
// 🔑 本轮要回答三件事：
//   ① `selection-context-toolbar-surface` 在**单选态也存在**（批次 129 的 18 态里查过），
//      而基座 `selection-context-toolbar` **只在多选态** —— 同一个 testid 在两种语义下复用？
//      这与批次 127「两个入口 testid 相同 ⇒ 共用一个面板」互为**镜像**。
//   ② `flow-node-multi-selection-source-toolbar` / `-source-handle` / `-source-connection-menu-button`
//      三个 testid 在批次 129 的 **18 个状态里一次都没出现过** ⇒ 多选态专属的新层，全册未记。
//   ③ 多选工具条上那个「下载」按钮为什么逐字带着「没有可用的就绪资源」。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b' };
const save = () => writeFileSync(new URL('./_tmp-b131b.json', import.meta.url), JSON.stringify(out, null, 1));

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
save();

const TIDS = ['selection-context-toolbar', 'selection-context-toolbar-surface', 'selection-context-toolbar-count',
  'selection-context-toolbar-popup-host', 'node-toolbar',
  'flow-node-multi-selection-source-toolbar', 'flow-node-multi-selection-source-handle',
  'flow-node-multi-selection-source-connection-menu-button',
  'flow-node-source-connection-menu-button', 'flow-node-target-connection-menu-button', 'flow-node-media-stroke'];

const 读 = (label) => p.evaluate(({ lb, tids }) => {
  const r = {};
  for (const t of tids) {
    const e = document.querySelector('[data-testid="' + t + '"]');
    if (!e) { r[t] = { 存在: false }; continue; }
    const q = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    const 父 = e.parentElement;
    const 链 = []; for (let n = e; n && n.nodeType === 1 && 链.length < 4; n = n.parentElement)
      链.push(n.getAttribute('data-testid') || n.tagName.toLowerCase());
    r[t] = { 存在: true, 状态: lb, tag: e.tagName, role: e.getAttribute('role'),
      矩形: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
      有面积: q.width >= 1 && q.height >= 1, opacity: cs.opacity, pe: cs.pointerEvents,
      逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 70), 子元素数: e.children.length,
      祖先链: 链, 父testid: 父 ? 父.getAttribute('data-testid') : null,
      按钮: Array.from(e.querySelectorAll('button,[role=button]')).map((x) => { const bx = x.getBoundingClientRect();
        return { 文字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12), aria: x.getAttribute('aria-label'),
          testid: x.getAttribute('data-testid'), disabled: x.disabled === true, ariaDisabled: x.getAttribute('aria-disabled'),
          尺寸: [Math.round(bx.width), Math.round(bx.height)], 矩形: [Math.round(bx.x), Math.round(bx.y)] }; }) };
  }
  return r;
}, { lb: label, tids: TIDS });

const show = (r) => { for (const t of TIDS) { const e = r[t];
  if (!e.存在) { log(`      · ${t} —— 不存在`); continue; }
  log(`      · ${t} <${e.tag}>${e.role ? ' role=' + e.role : ''} ${e.矩形.join(',')} 有面积=${e.有面积} op=${e.opacity} 按钮数=${e.按钮.length} «${e.逐字}»`);
  log(`          祖先链 ${e.祖先链.join(' < ')}`);
  e.按钮.forEach((x) => log(`          · 按钮 «${x.文字}» aria=${x.aria} testid=${x.testid} disabled=${x.disabled} aria-disabled=${x.ariaDisabled} ${x.尺寸.join('×')}@${x.矩形.join(',')}`)); } };

// ---------------------------------------------------------------- ① 单选一个节点
log('\n=== ① 单选一个音频节点：工具条是什么语义 ===');
{
  const pt = await p.evaluate(() => {
    for (const n of document.querySelectorAll('.react-flow__node-audio')) {
      const r = n.getBoundingClientRect();
      if (r.x < 90 || r.x + r.width > innerWidth - 90 || r.y + r.height < 110 || r.y > innerHeight - 110) continue;
      const yT = r.y + r.height * 0.4, yB = r.y + r.height * 0.6, xL = r.x + r.width * 0.3, xR = r.x + r.width * 0.7;
      for (let y = Math.ceil(yT); y <= yB; y += 3) for (let x = Math.ceil(xL); x <= xR; x += 3) {
        const h = document.elementFromPoint(x, y);
        if (h && (h === n || n.contains(h)) && x > 90 && y > 70 && y < innerHeight - 80) return { x, y, id: n.getAttribute('data-id') };
      }
    }
    return { __err: 'no-node' };
  });
  out.单选落点 = pt;
  if (pt.__err) log('  ⛔', pt.__err);
  else {
    log('  落点', JSON.stringify(pt));
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1400);
    out.单选后 = { 选中数: await sel(), 状态行: await status() };
    log('  点后选中数 =', out.单选后.选中数);
    if (out.单选后.选中数 === 1) { out.单选 = await 读('单选1个'); log('  单选态各层：'); show(out.单选); save(); }
  }
  const panePt = await p.evaluate(() => { for (let y = 300; y < 640; y += 7) for (let x = 300; x < 760; x += 7) { const h = document.elementFromPoint(x, y); if (h && h.classList && h.classList.contains('react-flow__pane')) return { x, y }; } return null; });
  if (panePt) { await p.mouse.click(panePt.x, panePt.y); await p.waitForTimeout(1100); }
  log('  取消后选中数', await sel());
}

// ---------------------------------------------------------------- ② 框选 8 个
log('\n=== ② 框选多选：同一批 testid 换了一种语义 ===');
{
  const plan = await p.evaluate(() => {
    const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => { const r = n.getBoundingClientRect();
      return { id: n.getAttribute('data-id'), x: r.x, y: r.y, right: r.right, bottom: r.bottom }; });
    const isPane = (x, y) => { const h = document.elementFromPoint(x, y); return !!(h && h.classList && h.classList.contains('react-flow__pane')); };
    const isFree = (x, y) => !nodes.some((n) => x >= n.x && x <= n.right && y >= n.y && y <= n.bottom);
    for (let pad = 20; pad <= 200; pad += 10) {
      const vis = nodes.filter((n) => n.right > 0 && n.x < innerWidth && n.bottom > 60 && n.y < innerHeight - 60);
      const xs = vis.flatMap((n) => [n.x, n.right]), ys = vis.flatMap((n) => [n.y, n.bottom]);
      const L = Math.min(...xs) - pad, R = Math.max(...xs) + pad, T = Math.max(Math.min(...ys), 62), B = Math.min(Math.max(...ys), innerHeight - 70);
      if (!(L > 4 && R < innerWidth - 300 && T > 60 && B < innerHeight - 60)) continue;
      if (![[L, T], [R, T], [L, B], [R, B]].every(([x, y]) => isPane(x, y) && isFree(x, y))) continue;
      const 罩住 = nodes.filter((n) => n.right > L && n.x < R && n.bottom > T && n.y < B);
      if (罩住.length >= 2) return { 矩形: [L, T, R, B].map(Math.round), 罩住节点数: 罩住.length };
    }
    return null;
  });
  out.框选计划 = plan;
  if (!plan) log('  ⛔ 找不到安全矩形');
  else {
    const [L, T, R, B] = plan.矩形;
    log('  框', JSON.stringify(plan.矩形), '罩住', plan.罩住节点数, '个');
    await p.mouse.move(L, T);
    const h0 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y); return h ? h.className.toString().split(' ')[0] : null; }, [L, T]);
    log('  按下点命中：', h0);
    await p.mouse.down();
    for (let i = 1; i <= 12; i++) { await p.mouse.move(Math.round(L + ((R - L) * i) / 12), Math.round(T + ((B - T) * i) / 12)); await p.waitForTimeout(55); }
    await p.mouse.up(); await p.waitForTimeout(1400);
    out.框选后 = { 选中数: await sel(), 状态行: await status() };
    log('  松开后选中数 =', out.框选后.选中数);
    const 位置 = await posNow();
    out.位置变化 = Object.keys(位置).filter((k) => 位置[k][0] !== 基线位置[k][0] || 位置[k][1] !== 基线位置[k][1]);
    log('  位置变化（必须空）：', JSON.stringify(out.位置变化));
    if (out.框选后.选中数 >= 2) { out.多选 = await 读(`多选${out.框选后.选中数}个`); log('  多选态各层：'); show(out.多选); save(); }
  }
}

// ---------------------------------------------------------------- ③ 单选 vs 多选 逐层对比
log('\n=== ③ 单选 vs 多选：同一个 testid 的语义差异 ===');
out.对比 = [];
for (const t of TIDS) {
  const s = out.单选?.[t], m = out.多选?.[t];
  if (!s && !m) continue;
  const line = { testid: t, 单选: s && s.存在 ? s.矩形.join(',') : '不存在', 多选: m && m.存在 ? m.矩形.join(',') : '不存在',
    相同: s && m && s.存在 && m.存在 && s.矩形.join(',') === m.矩形.join(',') };
  out.对比.push(line);
  log(`  ${t.padEnd(48)} 单选 ${String(line.单选).padEnd(22)} 多选 ${String(line.多选).padEnd(22)} ${line.相同 ? '= 同矩形' : '≠'}`);
}
log('\n  🔑 只在多选态出现的：', JSON.stringify(out.对比.filter((x) => x.单选 === '不存在' && x.多选 !== '不存在').map((x) => x.testid)));
log('  🔑 只在单选态出现的：', JSON.stringify(out.对比.filter((x) => x.多选 === '不存在' && x.单选 !== '不存在').map((x) => x.testid)));
save();

// ---------------------------------------------------------------- ④ 「下载」按钮的禁用原因
log('\n=== ④ 「下载」按钮逐字带「没有可用的就绪资源」是怎么来的 ===');
out.下载按钮 = await p.evaluate(() => {
  const tb = document.querySelector('[data-testid="selection-context-toolbar"]') || document.querySelector('[data-testid="node-toolbar"]');
  if (!tb) return { __err: 'no-toolbar' };
  const bs = Array.from(tb.querySelectorAll('button'));
  return bs.map((x) => ({ 逐字: (x.innerText || '').replace(/\s+/g, ' ').trim(), aria: x.getAttribute('aria-label'),
    disabled: x.disabled, ariaDisabled: x.getAttribute('aria-disabled'), className: x.className.toString().slice(0, 70),
    子元素: Array.from(x.children).map((c) => ({ tag: c.tagName, cls: c.className.toString().slice(0, 40), 文字: (c.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) })),
    innerHTML: x.innerHTML.slice(0, 260) }));
});
if (out.下载按钮.__err) log('  ⛔', out.下载按钮.__err);
else out.下载按钮.forEach((x, i) => { log(`  按钮${i}：逐字«${x.逐字}» aria=${x.aria} disabled=${x.disabled} aria-disabled=${x.ariaDisabled}`);
  log(`        子元素 ${JSON.stringify(x.子元素)}`); log(`        HTML ${x.innerHTML.replace(/</g, '‹').slice(0, 200)}`); });
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
log('\n收尾：', JSON.stringify(out.收尾));
log('  新增 id（必须空）：', JSON.stringify(out.新增id));
save();
log('\nDONE b');
process.exit(0);
