// 批次 131 · c 轮：补上**单选态**读数，把 b 轮那张无效的对比表做成有效的。
//
// 🔴 b 轮的「单选 vs 多选」对比**无效**：单选那一步报了 `no-node`，于是「单选」一列全是「不存在」——
//   **那不是事实，是我没点成。** 根因：我的落点条件里同时写了
//   `for y in [r.y+0.4h, r.y+0.6h]` 和 `y > 70`。该节点 `r.y = -74`、`h = 192`
//   ⇒ 搜索区间是 `[2.8, 41.2]`，**与 `y > 70` 不可满足** ⇒ 必然 `no-node`。
//   ⇒ 立规：**写完落点条件要当场验一次「它可满足吗」**（本批第四次栽在落点条件上）。
//
// 🔑 真正该问的不是「落点安不安全」，而是「**落点是否命中目标元素、且不是交互控件**」。
//   侦察结论：目标音频节点的可见部分（y 60–150）扫了 **682** 个采样点，
//   **全部命中 `audio-node-empty`（`role="img"`），一个按钮都没有** —— 所以直接点它即可。
//   节点**部分出屏本来就是常态**（60% 缩放下 8 个可见节点标题全在视口外，y −154…−63）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c' };
const save = () => writeFileSync(new URL('./_tmp-b131c.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);
const idsNow = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const posNow = () => p.evaluate(() => { const m = {}; for (const n of document.querySelectorAll('.react-flow__node')) { const r = n.getBoundingClientRect(); m[n.getAttribute('data-id')] = [Math.round(r.x), Math.round(r.y)]; } return m; });
const B = JSON.parse((await import('node:fs')).readFileSync(new URL('./_tmp-b131b.json', import.meta.url), 'utf8'));

out.start = { 状态行: await status(), 选中: await sel(), zoom: await zoom() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
for (let i = 0; i < 2; i++) { if (await overlays()) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); } }
out.起始id = await idsNow();
const 基线位置 = await posNow();
save();

const TIDS = ['selection-context-toolbar', 'selection-context-toolbar-surface', 'selection-context-toolbar-count',
  'selection-context-toolbar-popup-host', 'node-toolbar', 'node-feature-chrome-host', 'node-toolbar-feature-host',
  'flow-node-multi-selection-source-toolbar', 'flow-node-multi-selection-source-handle',
  'flow-node-multi-selection-source-connection-menu-button',
  'flow-node-source-connection-menu-button', 'flow-node-target-connection-menu-button',
  'flow-node-media-stroke', 'node-external'];

const 读 = (label) => p.evaluate(({ lb, tids }) => {
  const r = {};
  for (const t of tids) {
    const els = Array.from(document.querySelectorAll('[data-testid="' + t + '"]'));
    if (!els.length) { r[t] = { 存在: false }; continue; }
    const e = els[0]; const q = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    const 链 = []; for (let n = e; n && n.nodeType === 1 && 链.length < 4; n = n.parentElement)
      链.push(n.getAttribute('data-testid') || n.tagName.toLowerCase());
    r[t] = { 存在: true, 状态: lb, 元素数: els.length, tag: e.tagName, role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
      矩形: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
      有面积: q.width >= 1 && q.height >= 1, opacity: cs.opacity,
      逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 70), 子元素数: e.children.length, 祖先链: 链,
      按钮: Array.from(e.querySelectorAll('button,[role=button]')).map((x) => { const bx = x.getBoundingClientRect();
        return { 文字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12), aria: x.getAttribute('aria-label'),
          testid: x.getAttribute('data-testid'), ariaDisabled: x.getAttribute('aria-disabled'),
          尺寸: [Math.round(bx.width), Math.round(bx.height)], 矩形: [Math.round(bx.x), Math.round(bx.y)] }; }) };
  }
  return r;
}, { lb: label, tids: TIDS });

// ---------------------------------------------------------------- ① 单选
log('\n=== ① 单选一个音频节点（落点只要求「命中目标且不是交互控件」）===');
{
  const pt = await p.evaluate(() => {
    for (const n of document.querySelectorAll('.react-flow__node-audio')) {
      const r = n.getBoundingClientRect();
      // 落点必须在视口内、在节点矩形内、且命中元素不是按钮
      for (let y = 60; y <= Math.min(150, r.bottom - 4); y += 5) {
        for (let x = Math.ceil(r.x) + 6; x <= r.right - 6; x += 8) {
          const h = document.elementFromPoint(x, y);
          if (!h || !(h === n || n.contains(h))) continue;
          if (h.closest('button,[role=button]')) continue;
          return { x, y, id: n.getAttribute('data-id'), 命中: h.getAttribute('data-testid') || h.tagName,
            节点矩形: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
        }
      }
    }
    return { __err: 'no-safe-point' };
  });
  out.单选落点 = pt;
  if (pt.__err) { log('  ⛔', pt.__err); }
  else {
    log('  落点', JSON.stringify(pt));
    // 当场验证落点条件可满足（立规：写完条件先验它）
    log('  落点合法性：x,y 在视口内 =', pt.x >= 0 && pt.x < 1280 && pt.y >= 0 && pt.y < 720,
      '｜在节点矩形内 =', pt.命中 !== null);
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1500);
    out.单选后 = { 选中数: await sel(), 状态行: await status() };
    log('  点后：选中数 =', out.单选后.选中数, '｜状态行', JSON.stringify(out.单选后.状态行));
    if (out.单选后.选中数 === 1) {
      out.单选 = await 读('单选1个');
      log('  单选态各层：');
      for (const t of TIDS) { const e = out.单选[t];
        if (!e.存在) { log(`      · ${t} —— 不存在`); continue; }
        log(`      · ${t} <${e.tag}>${e.role ? ' role=' + e.role : ''} ${e.矩形.join(',')} 有面积=${e.有面积} 元素数=${e.元素数} 按钮数=${e.按钮.length} «${e.逐字}»`);
        log(`          祖先链 ${e.祖先链.join(' < ')}`);
        e.按钮.forEach((x) => log(`          · 按钮 «${x.文字}» aria=${x.aria} testid=${x.testid} aria-disabled=${x.ariaDisabled} ${x.尺寸.join('×')}@${x.矩形.join(',')}`)); }
      save();
    } else log('  ⛔ 选中数不是 1');
  }
  const panePt = await p.evaluate(() => { for (let y = 300; y < 640; y += 7) for (let x = 300; x < 760; x += 7) { const h = document.elementFromPoint(x, y); if (h && h.classList && h.classList.contains('react-flow__pane')) return { x, y }; } return null; });
  if (panePt) { await p.mouse.click(panePt.x, panePt.y); await p.waitForTimeout(1100); }
  log('  取消后选中数', await sel());
}

// ---------------------------------------------------------------- ② 框选多选（同一批 testid）
log('\n=== ② 框选多选 ===');
{
  const plan = await p.evaluate(() => {
    const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => { const r = n.getBoundingClientRect();
      return { x: r.x, y: r.y, right: r.right, bottom: r.bottom }; });
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
    await p.mouse.move(L, T);
    const h0 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y); return h ? h.className.toString().split(' ')[0] : null; }, [L, T]);
    log('  框', JSON.stringify(plan.矩形), '罩住', plan.罩住节点数, '个｜按下点', h0);
    await p.mouse.down();
    for (let i = 1; i <= 12; i++) { await p.mouse.move(Math.round(L + ((R - L) * i) / 12), Math.round(T + ((B - T) * i) / 12)); await p.waitForTimeout(55); }
    await p.mouse.up(); await p.waitForTimeout(1400);
    out.框选后 = { 选中数: await sel() };
    const 位置 = await posNow();
    out.位置变化 = Object.keys(位置).filter((k) => 位置[k][0] !== 基线位置[k][0] || 位置[k][1] !== 基线位置[k][1]);
    log('  松开后选中数 =', out.框选后.选中数, '｜位置变化（必须空）', JSON.stringify(out.位置变化));
    if (out.框选后.选中数 >= 2) out.多选 = await 读(`多选${out.框选后.选中数}个`);
  }
}

// ---------------------------------------------------------------- ③ 有效对比
log('\n=== ③ 单选 vs 多选（这次两张表都有实测数据）===');
out.对比 = [];
for (const t of TIDS) {
  const s = out.单选?.[t], m = out.多选?.[t];
  const sv = s && s.存在 ? s.矩形.join(',') : '不存在';
  const mv = m && m.存在 ? m.矩形.join(',') : '不存在';
  out.对比.push({ testid: t, 单选: sv, 多选: mv, 同矩形: sv === mv && sv !== '不存在',
    单选按钮: s && s.存在 ? (s.按钮.map((x) => x.aria || x.文字 || '(无)')) : null,
    多选按钮: m && m.存在 ? (m.按钮.map((x) => x.aria || x.文字 || '(无)')) : null });
}
out.对比.forEach((x) => log(`  ${x.testid.padEnd(48)} 单选 ${String(x.单选).padEnd(20)} 多选 ${String(x.多选).padEnd(20)} ${x.同矩形 ? '= 同矩形' : '≠'}`));
log('\n  🔑 只在多选态出现：', JSON.stringify(out.对比.filter((x) => x.单选 === '不存在' && x.多选 !== '不存在').map((x) => x.testid)));
log('  🔑 只在单选态出现：', JSON.stringify(out.对比.filter((x) => x.多选 === '不存在' && x.单选 !== '不存在').map((x) => x.testid)));
log('  🔑 两种状态都出现且同矩形：', JSON.stringify(out.对比.filter((x) => x.同矩形).map((x) => x.testid)));
out.按钮对比 = out.对比.filter((x) => x.单选按钮 || x.多选按钮).map((x) => ({ testid: x.testid, 单选按钮: x.单选按钮, 多选按钮: x.多选按钮 }));
out.按钮对比.forEach((x) => log(`  ${x.testid}：单选按钮 ${JSON.stringify(x.单选按钮)}｜多选按钮 ${JSON.stringify(x.多选按钮)}`));
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
log('\nDONE c');
process.exit(0);
