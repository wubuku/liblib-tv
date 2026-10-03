// 批次 129 · a 轮：**全册 testid 存活率普查**（纯只读 + 一次安全的节点选中）。
//
// 🔑 靶子：手册里到处写着 testid，但它们是**一次次实测记下来的、分布在不同时间点**的。
//   批次 83 记的 `240×200`、批次 120 记的 `N nodes…` 都已过时；
//   **testid 本身也会改名或消失，而没有任何一道门在管这件事**（9 道门里没有一道查 testid 存活）。
//   本批把「手册里出现过的 testid」全量拉出来，逐个对当前构建核验。
//
// 📌 候选的取法（写清楚免得下一个人取歪）：
//   只取**反引号里**、形如 `[a-z][a-z0-9]*(-[a-z0-9]+)+` 的 token（像 testid），
//   排除含空格或斜杠的。全册共 **551** 个候选（出现 ≥2 次的 274 个）。
//   ⚠️ 候选里**混着属性名与 class 名**（`aria-label` / `pointer-events` / `sr-only` …），
//   所以必须**分类**而不是直接当 testid。
//
// 📌 分类判据（三类，用三条**互不共享假设**的探针）：
//   ① 现在是 testid 吗？  → `[data-testid="T"]` 命中
//   ② 那它是不是「属性名 / class 名」？ → 扫全文档的属性名集合 ＋ 用 `CSS.escape` 查
//      `.T` 是否命中（说明它至少还是活的 class）—— **这条与 ① 完全独立**
//   ③ 需要「选中态」才出现？ → 选中一个节点后重查
//   三条都不命中 ⇒ **疑似过时**（才是真正要人看的那一类）
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b129a.json', import.meta.url), JSON.stringify(out, null, 1));

const cands = JSON.parse(readFileSync('/tmp/b129-candidates.json', 'utf8'));
out.候选数 = cands.length;
log('候选 token：', cands.length);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);

out.start = { 状态行: await status(), 选中: await sel(), zoom: await zoom(), credits: await credits(), 浮层: await overlays() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
for (let i = 0; i < 2; i++) { if (await overlays()) { await p.keyboard.press('Escape'); await p.waitForTimeout(1000); } }

// ---- 在页面里核验一批候选 ----
const verify = (label, list) => p.evaluate(({ lb, toks }) => {
  const attrNames = new Set();
  const classNames = new Set();
  for (const e of Array.from(document.querySelectorAll('*'))) {
    for (const a of Array.from(e.attributes)) attrNames.add(a.name);
    if (e.classList) for (const c of e.classList) classNames.add(c);
  }
  const testids = new Set(Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')));
  const res = toks.map((t) => {
    const asTestid = testids.has(t);
    let asClass = false;
    try { asClass = !!document.querySelector('.' + CSS.escape(t)); } catch { asClass = false; }
    const asAttr = attrNames.has(t);
    let detail = null;
    if (asTestid) { const e = document.querySelector('[data-testid="' + t.replace(/"/g, '\\"') + '"]');
      const r = e.getBoundingClientRect();
      detail = { tag: e.tagName, rect: [r.x, r.y, r.width, r.height].map(Math.round), 有面积: r.width >= 1 && r.height >= 1,
        文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30), aria: e.getAttribute('aria-label') }; }
    return { 扫描点: lb, token: t, 是testid: asTestid, 是class: asClass, 是属性名: asAttr, 详情: detail };
  });
  return { 扫描点: lb, 全文档testid种类: testids.size, 结果: res,
    命中testid: res.filter((r) => r.是testid).length, 未命中: res.filter((r) => !r.是testid).length };
}, { lb: label, toks: list });

out.基线 = await verify('画布静态（无选中、无面板）', cands);
log('\n=== ① 画布静态 ===');
log('  全文档 data-testid 种类：', out.基线.全文档testid种类, '｜候选命中：', out.基线.命中testid, '｜未命中：', out.基线.未命中);
const miss0 = out.基线.结果.filter((r) => !r.是testid).map((r) => r.token);
out.未命中0 = miss0;
log('  未命中（' + miss0.length + ' 个）：', JSON.stringify(miss0));
save();

// ---- 分类：其中哪些是「属性名 / class 名」（不是过时 testid） ----
out.分类0 = out.基线.结果.filter((r) => !r.是testid).map((r) => ({ token: r.token, 是class: r.是class, 是属性名: r.是属性名 }));
const 纯可疑 = out.分类0.filter((r) => !r.是class && !r.是属性名).map((r) => r.token);
out.纯可疑0 = 纯可疑;
log('\n=== ② 分类 ===');
log('  是 class 名或属性名（**不是过时的 testid**）：', out.分类0.length - 纯可疑.length, '个');
log('  两条探针都不命中（**疑似过时**）：', 纯可疑.length, '个：', JSON.stringify(纯可疑));
save();

// ---- ③ 打开几个面板，把「面板里的 testid」捞回来 ----
async function openBySel(s) {
  const pt = await p.evaluate((sel) => { const e = document.querySelector(sel); if (!e) return { __err: 'not-found' };
    const r = e.getBoundingClientRect(); if (r.width < 1) return { __err: 'zero-size' };
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
      const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; }
    return { __err: 'no-point' }; }, s);
  if (pt.__err) return pt;
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1600);
  return pt;
}
out.面板态 = {};
const panelSeq = [
  ['搜索', '[data-testid="canvas-panel-launcher"][aria-label="搜索"]'],
  ['生成历史', '[data-testid="canvas-panel-launcher"][aria-label="生成历史"]'],
  ['更多', 'button[aria-label="更多"]'],
  ['用户菜单', '[data-testid="canvas-user-menu-trigger"]'],
  ['分享', '[data-testid="canvas-share-trigger"]'],
  ['项目', '[data-testid="canvas-project-trigger"]'],
  ['节点N', '[data-testid="canvas-node-summary-trigger"]'],
];
log('\n=== ③ 逐个打开面板，复查未命中的候选 ===');
for (const [name, s] of panelSeq) {
  const pt = await openBySel(s);
  if (pt.__err) { log(`  【${name}】⛔ ${pt.__err}`); out.面板态[name] = { 打开: pt }; continue; }
  const v = await verify(name, 纯可疑);
  const got = v.结果.filter((r) => r.是testid).map((r) => r.token);
  out.面板态[name] = { 打开: pt, 全文档testid种类: v.全文档testid种类, 补回: got };
  log(`  【${name}】全文档 testid ${v.全文档testid种类} 种｜补回 ${got.length} 个：${JSON.stringify(got)}`);
  save();
  for (let i = 0; i < 2; i++) { if (!(await overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(1000); }
}
const 补回集合 = new Set(Object.values(out.面板态).flatMap((v) => v.补回 || []));
out.仍可疑 = 纯可疑.filter((t) => !补回集合.has(t));
log('\n  面板态补回后**仍一条都没命中**的（真正疑似过时）：', out.仍可疑.length, '个');
log('  ', JSON.stringify(out.仍可疑));
save();

// ---- ④ 选中一个节点（安全：只选中，不做任何别的），看「需要选中态」的 testid ----
out.选中态 = {};
const nodePt = await p.evaluate(() => {
  // 找一个**文本节点**（它的工具条最全），落点现算 + 自检
  const nodes = Array.from(document.querySelectorAll('.react-flow__node-text'));
  for (const n of nodes) { const r = n.getBoundingClientRect();
    if (r.x < 60 || r.y < 60 || r.x + r.width > window.innerWidth - 320 || r.y + r.height > window.innerHeight - 60) continue;
    for (let y = Math.ceil(r.y) + 4; y <= r.y + r.height - 4; y += 3) for (let x = Math.ceil(r.x) + 4; x <= r.x + r.width - 4; x += 3) {
      const h = document.elementFromPoint(x, y); if (h && (h === n || n.contains(h))) return { x, y, id: n.getAttribute('data-id'), 文字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20) }; }
  }
  return { __err: 'no-visible-text-node' };
});
log('\n=== ④ 选中态复查 ===\n  文本节点落点：', JSON.stringify(nodePt));
if (!nodePt.__err) {
  await p.mouse.click(nodePt.x, nodePt.y);
  await p.waitForTimeout(1300);
  out.选中态.落点 = nodePt;
  out.选中态.选中数 = await sel();
  out.选中态.状态行 = await status();
  log('  点后：选中数=', out.选中态.选中数, '状态行=', JSON.stringify(out.选中态.状态行));
  const v = await verify('选中一个文本节点后', out.仍可疑);
  const got = v.结果.filter((r) => r.是testid).map((r) => r.token);
  out.选中态.补回 = got;
  out.选中后仍可疑 = out.仍可疑.filter((t) => !got.includes(t));
  log('  选中态补回', got.length, '个：', JSON.stringify(got));
  log('  选中态之后**仍然一条都没命中**：', out.选中后仍可疑.length, '个');
  log('  ', JSON.stringify(out.选中后仍可疑));
  save();
}
save();

// ---- 收尾：点空白取消选中（落点必须命中 .react-flow__pane —— 点空白要反着判） ----
const panePt = await p.evaluate(() => { const pr = document.querySelector('[data-testid="canvas-feature-panel"]');
  const box = pr ? pr.getBoundingClientRect() : null;
  for (let y = 300; y < 620; y += 7) for (let x = 300; x < 740; x += 7) {
    if (box && x > box.x - 10 && x < box.x + box.width + 10 && y > box.y - 10 && y < box.y + box.height + 10) continue;
    const h = document.elementFromPoint(x, y);
    if (h && h.classList && h.classList.contains('react-flow__pane')) return { x, y }; }
  return null; });
out.收尾落点 = panePt;
if (panePt) { await p.mouse.click(panePt.x, panePt.y); await p.waitForTimeout(1200); }
out.收尾 = { 选中: await sel(), 状态行: await status(), 浮层: await overlays(), zoom: await zoom(), credits: await credits() };
log('\n收尾：', JSON.stringify(out.收尾));
save();
log('\nDONE a');
process.exit(0);
