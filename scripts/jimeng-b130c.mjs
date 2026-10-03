// 批次 130 · c 轮：① **全量差集按 testid 归类**；② **复核「数浮层要用有面积过滤」那条规**的适用场景；
// ③ 顺带把 `flow-node-*` 三家族的完整契约建档（全册从未系统记录过）。
//
// 🔑 a 轮的读数必须**诚实解释**，不能硬凑一个「规被推翻」的结论：
//   差集 646 个里 **`role=dialog/menu/listbox` 恰好 0 个**。
//   而 `30-concepts.md:2182` 那条例的**具体场景**是「关掉但没卸载的弹层节点仍留在 DOM 里」——
//   那些节点要么零尺寸（被 `width>1` 滤掉），要么不可见但**不带浮层 role**（不参与浮层计数）。
//   ⇒ **那条例在本批的场景下没有被推翻**；被证伪的是一个**更宽泛的说法**（「有面积 = 可见」），
//   而那个更宽泛的说法手册里**并没有立成规**。本轮把这条边界用实验钉死。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c' };
const save = () => writeFileSync(new URL('./_tmp-b130c.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const idsNow = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const escAll = async () => { for (let i = 0; i < 4; i++) { const n = await p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length); if (!n) break; await p.keyboard.press('Escape'); await p.waitForTimeout(900); } };
const toggle = async (s, label) => {
  const pt = await p.evaluate((q) => { const e = document.querySelector(q); if (!e) return { __err: 'nf' };
    const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) { const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; }
    return { __err: 'np' }; }, s);
  if (pt.__err) { log(`  【${label}】⛔ ${pt.__err}`); return pt; }
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1700); return pt;
};

out.start = { 状态行: await status(), 选中: await sel(), zoom: await zoom() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
await escAll();
out.起始id = await idsNow();

// ---------------------------------------------------------------- ① 全量差集按 testid 归类
log('\n=== ① 全量差集按 testid 归类（旧判据会多算的那些）===');
const classify = () => p.evaluate(() => {
  const all = Array.from(document.querySelectorAll('*'));
  const 链可见 = (e) => {
    let node = e, op = 1, vis = true;
    while (node && node.nodeType === 1) {
      const cs = getComputedStyle(node);
      if (cs.display === 'none') return false;
      if (cs.visibility === 'hidden' || cs.visibility === 'collapse') vis = false;
      op *= parseFloat(cs.opacity);
      node = node.parentElement;
    }
    if (op < 0.01 || !vis) return false;
    const r = e.getBoundingClientRect();
    return r.width >= 1 && r.height >= 1;
  };
  const 旧 = all.filter((e) => e.getBoundingClientRect().width > 1);
  const 新 = all.filter(链可见);
  const 差 = 旧.filter((e) => !新.includes(e));
  const byTestid = {}, byRoot = {}, byCause = { 自身opacity0: 0, 自身visibilityHidden: 0, 祖先链: 0 };
  for (const e of 差) {
    const t = e.getAttribute('data-testid') || '(无 tid)';
    byTestid[t] = (byTestid[t] || 0) + 1;
    let root = '其它';
    for (let n = e; n && n.nodeType === 1; n = n.parentElement) {
      const c = (n.className && typeof n.className === 'string') ? n.className.split(/\s+/)[0] : '';
      if (n.classList && (n.classList.contains('react-flow__node'))) { root = '节点子树（' + c + '）'; break; }
      if (n.getAttribute && n.getAttribute('data-testid') === 'canvas-feature-sidecar') { root = 'Agent 侧栏空壳'; break; }
      if (n.tagName === 'HEADER') { root = '顶栏'; break; }
      if (n.getAttribute && /canvas-navigation/.test(n.getAttribute('data-testid') || '')) { root = '左栏导航'; break; }
    }
    byRoot[root] = (byRoot[root] || 0) + 1;
    const cs = getComputedStyle(e);
    if (parseFloat(cs.opacity) < 0.01) byCause.自身opacity0++;
    else if (cs.visibility === 'hidden') byCause.自身visibilityHidden++;
    else byCause.祖先链++;
  }
  return { 元素总数: all.length, 旧: 旧.length, 新: 新.length, 差集: 差.length,
    差集里带浮层role: 差.filter((e) => ['dialog', 'menu', 'listbox', 'alertdialog'].includes(e.getAttribute('role'))).length,
    byTestid, byRoot, byCause };
});
out.分类 = await classify();
log(`  元素总数 ${out.分类.元素总数}｜旧判据 ${out.分类.旧}｜祖先链判据 ${out.分类.新}｜差集 ${out.分类.差集}`);
log(`  🔑 差集里带浮层 role 的: **${out.分类.差集里带浮层role}**`);
log('\n  按 testid 归类：');
Object.entries(out.分类.byTestid).sort((a, b) => b[1] - a[1]).forEach(([k, v]) => log(`      ${String(v).padStart(4)}  ${k}`));
log('\n  按宿主归类：');
Object.entries(out.分类.byRoot).sort((a, b) => b[1] - a[1]).forEach(([k, v]) => log(`      ${String(v).padStart(4)}  ${k}`));
log('\n  按不可见的成因：', JSON.stringify(out.分类.byCause));
save();

// ---------------------------------------------------------------- ② flow-node 三家族契约
log('\n=== ② flow-node 三家族：全册从未系统记录过 ===');
out.flowNode = await p.evaluate(() => {
  const pick = (t) => Array.from(document.querySelectorAll('[data-testid="' + t + '"]'));
  const desc = (e) => { const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    const n = e.closest('.react-flow__node'); const nr = n ? n.getBoundingClientRect() : null;
    return { 矩形: [Math.round(r.width), Math.round(r.height)],
      opacity: cs.opacity, visibility: cs.visibility, pe: cs.pointerEvents, display: cs.display,
      相对本节点的左偏移: nr ? Math.round(r.x - nr.x) : null, 相对本节点的右偏移: nr ? Math.round(nr.right - r.right) : null }; };
  const fam = {};
  for (const t of ['flow-node-target-handle', 'flow-node-source-handle', 'flow-node-selected-tag', 'flow-node-title']) {
    const els = pick(t);
    const 样本 = els.slice(0, 3).map(desc);
    const 尺寸集 = new Set(els.map((e) => { const r = e.getBoundingClientRect(); return Math.round(r.width) + '×' + Math.round(r.height); }));
    fam[t] = { 元素数: els.length, 所在节点数: new Set(els.map((e) => (e.closest('.react-flow__node') || {}).getAttribute?.('data-id'))).size, 尺寸集: Array.from(尺寸集), 样本 };
  }
  return fam;
});
for (const [k, v] of Object.entries(out.flowNode)) {
  log(`  ${k}: ${v.元素数} 个 / 分布在 ${v.所在节点数} 个节点上｜尺寸 ${JSON.stringify(v.尺寸集)}`);
  log(`      样本 ${JSON.stringify(v.样本[0] || null)}`);
}
save();

// ---------------------------------------------------------------- ③ 复核那条例的适用场景
log('\n=== ③ 复核：「关掉但没卸载的弹层」在两种判据下各读到几 ===');
out.浮层复核 = {};
const 读浮层 = () => p.evaluate(() => {
  const roles = ['dialog', 'menu', 'listbox', 'alertdialog'];
  const all = Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox],[role=alertdialog]'));
  const 旧 = all.filter((e) => e.getBoundingClientRect().width > 1);
  const 链可见 = (e) => {
    let node = e, op = 1, vis = true;
    while (node && node.nodeType === 1) { const cs = getComputedStyle(node);
      if (cs.display === 'none') return false;
      if (cs.visibility === 'hidden' || cs.visibility === 'collapse') vis = false;
      op *= parseFloat(cs.opacity); node = node.parentElement; }
    if (op < 0.01 || !vis) return false;
    const r = e.getBoundingClientRect(); return r.width >= 1 && r.height >= 1;
  };
  const 新 = all.filter(链可见);
  return { DOM里浮层总数: all.length, 旧判据: 旧.length, 新判据: 新.length,
    两者差: 旧.length - 新.length,
    旧判据认但新判据不认的: 旧.filter((e) => !新.includes(e)).map((e) => ({ tid: e.getAttribute('data-testid'), tag: e.tagName,
      rect: (() => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })(),
      文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20) })) };
});
for (const [n, s] of [['搜索', '[data-testid="canvas-panel-launcher"][aria-label="搜索"]'],
  ['生成历史', '[data-testid="canvas-panel-launcher"][aria-label="生成历史"]'],
  ['用户菜单', '[data-testid="canvas-user-menu-trigger"]'],
  ['分享', '[data-testid="canvas-share-trigger"]'],
  ['项目', '[data-testid="canvas-project-trigger"]'],
  ['节点N', '[data-testid="canvas-node-summary-trigger"]']]) {
  const 关态 = await 读浮层();
  const pt = await toggle(s, n);
  if (pt.__err) { out.浮层复核[n] = { 打开失败: pt.__err }; continue; }
  const 开态 = await 读浮层();
  await escAll();
  const 再关 = await 读浮层();
  out.浮层复核[n] = { 关态, 开态, 再关 };
  log(`  【${n}】关态 ${关态.旧判据}/${关态.新判据}（DOM 共 ${关态.DOM里浮层总数}）→ 开态 **${开态.旧判据}/${开态.新判据}** → 再关 ${再关.旧判据}/${再关.新判据}`);
  if (开态.两者差 > 0) log(`      🔑 开态两判据差 ${开态.两者差}：${JSON.stringify(开态.旧判据认但新判据不认的)}`);
  save();
}
await escAll();

// ---------------------------------------------------------------- 收尾
await p.mouse.move(1276, 716); await p.waitForTimeout(600);
const endIds = await idsNow();
out.收尾 = { 选中: await sel(), 状态行: await status(), zoom: await zoom(), 节点数: endIds.length, 起始节点数: out.起始id.length };
out.新增id = endIds.filter((x) => !out.起始id.includes(x));
log('\n收尾：', JSON.stringify(out.收尾), '｜新增 id', JSON.stringify(out.新增id));
save();
log('\nDONE c');
process.exit(0);
