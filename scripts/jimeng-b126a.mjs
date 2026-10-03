// 批次 126 · a 轮（只读 + 一次打开）：把顶栏「生成历史」面板 `canvas-feature-panel` **内部解剖**。
//
// 🔑 靶子：全册只在批次 31（2026-09-23）记过「一级页签两个 + 二级页签五个 + 暂无生成历史」，
//   那是**一句转述**，从来没有人把这棵 DOM 拆开看过：页签是不是 `role="tab"`、
//   有没有 `data-state`、面板内有哪些 testid、五个二级页签各自的空态逐字是不是同一句、
//   打开后启动器的 `aria-expanded` 变没变 —— **全都没有读数**。
//
// 📌 沿用已立的规：
//   · 「搜索」「生成历史」共用 `canvas-panel-launcher` ⇒ 必须按 `aria-label` 挑，不能按 testid 挑第一个。
//   · 批次 122：拿到 testid 先数孩子与 `tagName` ⇒ 判「是不是按钮」要看 `tagName`，别信 testid 命名。
//   · 批次 122/125：Radix 弹层的开关态**只认 `aria-expanded` / `aria-selected`**；
//     `data-state` 用 `getAttribute` 回读，**null 就是属性不存在**，不能拿 `undefined` 蒙混。
//   · 批次 120 规一：落点必须在**动作即将发生的那一刻**现算 + `elementFromPoint` 自检，
//     判据是 `el === target || target.contains(el)`。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b126a.json', import.meta.url), JSON.stringify(out, null, 1));
const shotDir = new URL('./_tmp-b126b-shots/', import.meta.url);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);

out.start = { zoom: await zoom(), credits: await credits(), status: await status(), 浮层: await overlays() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);

// ---- ① 点开之前：先把「生成历史」启动器的身份读全（含 aria-expanded 的初值） ----
out.launcher_before = await p.evaluate(() => {
  const cands = Array.from(document.querySelectorAll('[data-testid="canvas-panel-launcher"]'));
  const rows = cands.map((e) => { const r = e.getBoundingClientRect(); return {
    tag: e.tagName, tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
    ariaExpanded: e.getAttribute('aria-expanded'), dataState: e.getAttribute('data-state'),
    矩形: [r.x, r.y, r.width, r.height].map(Math.round) }; });
  const target = cands.find((e) => (e.getAttribute('aria-label') || '') === '生成历史');
  if (!target) return { __err: 'no-launcher', 候选: rows };
  const r = target.getBoundingClientRect();
  return { 候选: rows, 目标tag: target.tagName, 目标ariaExpanded: target.getAttribute('aria-expanded'),
    目标dataState: target.getAttribute('data-state'), 目标矩形: [r.x, r.y, r.width, r.height].map(Math.round),
    目标子元素数: target.children.length,
    目标内可点: Array.from(target.querySelectorAll('button,[role=button],a')).map((e) => ({ tag: e.tagName, 文字: (e.innerText || '').replace(/\s+/g, ' ').trim() })) };
});
log('\n=== ① 打开前：canvas-panel-launcher 家族 ===');
if (out.launcher_before.__err) { log('  ', JSON.stringify(out.launcher_before)); save(); await b.close(); process.exit(3); }
log('  同 testid 元素共 ', out.launcher_before.候选.length, ' 个：');
out.launcher_before.候选.forEach((c) => log(`    <${c.tag}> ${JSON.stringify(c.矩形)} aria=${JSON.stringify(c.aria)} aria-expanded=${c.ariaExpanded} data-state=${c.dataState}`));
log('  目标（aria=生成历史）：', JSON.stringify({ tag: out.launcher_before.目标tag, rect: out.launcher_before.目标矩形, ariaExpanded: out.launcher_before.目标ariaExpanded, 子元素数: out.launcher_before.目标子元素数, 内可点: out.launcher_before.目标内可点 }));
save();

// ---- ② 落点现算 + elementFromPoint 自检，然后点开 ----
const pt = await p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('[data-testid="canvas-panel-launcher"]')).find((x) => (x.getAttribute('aria-label') || '') === '生成历史');
  if (!e) return { __err: 'no-launcher' };
  const r = e.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2)
    for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
      const h = document.elementFromPoint(x, y);
      if (h && (h === e || e.contains(h))) return { x, y, 命中tag: h.tagName, 命中aria: h.getAttribute('aria-label') };
    }
  return { __err: 'no-point' };
});
log('\n=== ② 落点自检 ===\n  ', JSON.stringify(pt));
if (pt.__err) { save(); await b.close(); process.exit(3); }
await p.mouse.click(pt.x, pt.y);
await p.waitForTimeout(1500);

out.opened = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-feature-panel"]');
  if (!e) return { __err: 'no-panel' };
  const l = Array.from(document.querySelectorAll('[data-testid="canvas-panel-launcher"]')).find((x) => (x.getAttribute('aria-label') || '') === '生成历史');
  return { 面板存在: true, 启动器ariaExpanded: l ? l.getAttribute('aria-expanded') : null,
    启动器dataState: l ? l.getAttribute('data-state') : null }; });
log('  打开后：', JSON.stringify(out.opened));
if (out.opened.__err) { save(); await b.close(); process.exit(3); }

// ---- ③ 面板内部解剖：整棵树（只列有面积的元素，标出屏外/裁剪的） ----
out.tree = await p.evaluate(() => {
  const panel = document.querySelector('[data-testid="canvas-feature-panel"]');
  if (!panel) return { __err: 'no-panel' };
  const R = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const cs = getComputedStyle(panel);
  const nodes = [];
  const walk = (e, d) => {
    if (d > 6) return;
    const r = e.getBoundingClientRect();
    const visible = r.width >= 1 && r.height >= 1;
    const st = getComputedStyle(e);
    const clipped = st.clip !== 'none' || st.clipPath !== 'none' || st.overflow === 'hidden';
    nodes.push({ d, tag: e.tagName, cls: (e.getAttribute('class') || '').slice(0, 40),
      role: e.getAttribute('role'), tid: e.getAttribute('data-testid'),
      aria: e.getAttribute('aria-label'), ariaSelected: e.getAttribute('aria-selected'),
      ariaControls: e.getAttribute('aria-controls'), dataState: e.getAttribute('data-state'),
      ariaExpanded: e.getAttribute('aria-expanded'),
      rect: R(e), 有面积: visible, pe: st.pointerEvents,
      srOnly: st.position === 'absolute' && (st.clip || '').includes('rect'),
      文字: (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40) });
    Array.from(e.children).forEach((c) => walk(c, d + 1));
  };
  walk(panel, 0);
  return { 面板: { tag: panel.tagName, cls: (panel.getAttribute('class') || '').slice(0, 60), role: panel.getAttribute('role'),
      aria: panel.getAttribute('aria-label'), 矩形: R(panel), 孩子数: panel.children.length,
      position: cs.position, zIndex: cs.zIndex, pointerEvents: cs.pointerEvents, overflow: cs.overflow },
    逐字: (panel.innerText || '').replace(/\s+/g, ' ').trim(),
    有面积元素数: nodes.filter((n) => n.有面积).length, 无面积元素: nodes.filter((n) => !n.有面积).map((n) => ({ d: n.d, tag: n.tag, cls: n.cls, 文字: n.文字 })),
    树: nodes };
});
log('\n=== ③ 面板本体 ===');
if (out.tree.__err) { log('  ', out.tree.__err); save(); await b.close(); process.exit(3); }
log('  ', JSON.stringify(out.tree.面板));
log('  逐字：', JSON.stringify(out.tree.逐字));
log(`  子树元素 ${out.tree.树.length} 个，其中有面积 ${out.tree.有面积元素数} 个；无面积的：`, JSON.stringify(out.tree.无面积元素));
log('\n  === 有面积的节点（按深度）===');
out.tree.树.filter((n) => n.有面积).forEach((n) => log(`  ${'  '.repeat(n.d)}<${n.tag}> ${JSON.stringify(n.rect)} role=${n.role ?? '-'} tid=${n.tid ?? '-'} aria=${JSON.stringify(n.aria)} sel=${n.ariaSelected ?? '-'} ctl=${JSON.stringify(n.ariaControls)} dstate=${n.dataState ?? '-'} exp=${n.ariaExpanded ?? '-'} pe=${n.pe} «${n.文字}»`));
save();

// ---- ④ 页签 / tabpanel / 可点元素 / 内部 testid 分组 ----
out.tabs = await p.evaluate(() => {
  const panel = document.querySelector('[data-testid="canvas-feature-panel"]');
  const R = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const D = (e) => ({ tag: e.tagName, role: e.getAttribute('role'), tid: e.getAttribute('data-testid'),
    ariaSelected: e.getAttribute('aria-selected'), ariaControls: e.getAttribute('aria-controls'),
    dataState: e.getAttribute('data-state'), rect: R(e),
    文字: (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim() });
  return { roleTab: Array.from(panel.querySelectorAll('[role=tab]')).map(D),
    tablist: Array.from(panel.querySelectorAll('[role=tablist]')).map(D),
    tabpanel: Array.from(panel.querySelectorAll('[role=tabpanel]')).map((e) => ({ ...D(e), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim() })),
    全部button: Array.from(panel.querySelectorAll('button')).map(D),
    全部可点: Array.from(panel.querySelectorAll('[role=button],a,[onclick]')).map(D),
    内部testid: Array.from(panel.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')),
    内部aria: Array.from(panel.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')),
    内部表格: Array.from(panel.querySelectorAll('table,[role=table],[role=grid],[role=row]')).map(D),
    内部input: Array.from(panel.querySelectorAll('input,textarea')).map(D) };
});
log('\n=== ④ 分组读数 ===');
log('  [role=tab]（', out.tabs.roleTab.length, '个）');
out.tabs.roleTab.forEach((t, i) => log(`    [${i}] <${t.tag}> ${JSON.stringify(t.rect)} «${t.文字}» aria-selected=${t.ariaSelected} data-state=${t.dataState} aria-controls=${JSON.stringify(t.ariaControls)}`));
log('  [role=tablist]（', out.tabs.tablist.length, '个）：');
out.tabs.tablist.forEach((t) => log(`    <${t.tag}> ${JSON.stringify(t.rect)} «${t.文字}»`));
log('  [role=tabpanel]（', out.tabs.tabpanel.length, '个）：');
out.tabs.tabpanel.forEach((t) => log(`    <${t.tag}> ${JSON.stringify(t.rect)} «${t.逐字}»`));
log('  <button>（', out.tabs.全部button.length, '个）：');
out.tabs.全部button.forEach((t, i) => log(`    [${i}] <${t.tag}> ${JSON.stringify(t.rect)} role=${t.role ?? '-'} «${t.文字}» sel=${t.ariaSelected ?? '-'} dstate=${t.dataState ?? '-'}`));
log('  其他可点（', out.tabs.全部可点.length, '个）：', JSON.stringify(out.tabs.全部可点));
log('  内部 testid：', JSON.stringify(out.tabs.内部testid));
log('  内部 aria-label：', JSON.stringify(out.tabs.内部aria));
log('  内部表格元素：', out.tabs.内部表格.length, JSON.stringify(out.tabs.内部表格));
log('  内部输入框：', out.tabs.内部input.length, JSON.stringify(out.tabs.内部input));
save();

// ---- ⑤ 面板外：确认它挂在哪个 portal 宿主下、有没有兄弟、同矩形元素 ----
out.host = await p.evaluate(() => {
  const panel = document.querySelector('[data-testid="canvas-feature-panel"]');
  if (!panel) return { __err: 'no-panel' };
  const R = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const same = Array.from(document.querySelectorAll('body *')).filter((e) => { const r = e.getBoundingClientRect();
    const p2 = panel.getBoundingClientRect(); return r.width > 1 && Math.abs(r.x - p2.x) < 1 && Math.abs(r.y - p2.y) < 1 && Math.abs(r.width - p2.width) < 1 && Math.abs(r.height - p2.height) < 1; })
    .map((e) => ({ tag: e.tagName, cls: (e.getAttribute('class') || '').slice(0, 40), tid: e.getAttribute('data-testid'), role: e.getAttribute('role') }));
  const chain = []; let e = panel;
  for (let i = 0; i < 5 && e && e !== document.body; i++) { e = e.parentElement; if (e) chain.push({ tag: e.tagName, cls: (e.getAttribute('class') || '').slice(0, 40), rect: R(e) }); }
  return { 同矩形元素: same, 祖先链: chain, 面板父: (() => { const q = panel.parentElement; return { tag: q.tagName, cls: (q.getAttribute('class') || '').slice(0, 40), tid: q.getAttribute('data-testid'), rect: R(q) }; })() };
});
log('\n=== ⑤ 宿主与祖先 ===');
log('  同矩形元素（', out.host.同矩形元素.length, '个）：', JSON.stringify(out.host.同矩形元素));
log('  面板直接父级：', JSON.stringify(out.host.面板父));
log('  祖先链：', JSON.stringify(out.host.祖先链));
save();
await p.screenshot({ path: new URL('00-panel-open.png', shotDir).pathname, clip: { x: 780, y: 40, width: 360, height: 250 } });
await p.screenshot({ path: new URL('01-panel-open-full.png', shotDir).pathname });

out.收尾 = { 浮层: await overlays(), 选中: await sel(), zoom: await zoom(), credits: await credits(), status: await status() };
log('\n收尾（面板仍开着）：', JSON.stringify(out.收尾));
save();
log('\nDONE a —— 面板保持打开，交 b 轮');
process.exit(0);
