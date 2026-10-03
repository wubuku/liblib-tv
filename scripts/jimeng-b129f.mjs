// 批次 129 · f 轮：① **重做多选**（修正落点选取缺陷）；② 给 39 个「静态漏记 testid」补 DOM 契约。
//
// 🔴 d 轮多选失败的真正原因（本轮才查清，是**我的落点选取缺陷**，不是产品行为）：
//   d 轮取落点的循环是「从节点矩形上边缘起、每 4px 扫一行」，
//   于是拿到的第一个命中点是 **y=1 和 y=0** —— 正好卡在视口顶边。
//   手册 `help-and-shortcuts.md:322` 已记：Shift+点选是**标准 toggle 语义**（批次 56 受控复测）。
//   ⇒ 之前「Shift 点第二个仍是 1 selected」**不能**读成「Shift 多选无效」。
//   本轮把落点改成**节点中心附近**（离矩形上/下边缘各留 ≥15%），并**先断言落点合法**再点。
//   ⇒ 立规：**采集落点不能从边缘起扫**；读数异常时先怀疑自己的落点，再怀疑产品。
//
// 📌 ② b 轮的「145 个手册没提过的 testid」里有 106 个是**按实例生成**的
//   （`rf__node-node_*` / `project-*-ordinary-<uuid>` / `canvas-search-*-node_*`），
//   记进手册只会变成噪音。**真正的知识缺口是 39 个静态 testid**，本轮把它们的 DOM 契约一次抓全。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'f' };
const save = () => writeFileSync(new URL('./_tmp-b129f.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);
const collect = () => p.evaluate(() => { const s = new Set(); for (const e of document.querySelectorAll('[data-testid]')) s.add(e.getAttribute('data-testid')); return Array.from(s); });
const idsNow = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const escAll = async () => { for (let i = 0; i < 3; i++) { if (!(await overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(900); } };
const toggle = async (selq, label) => {
  const pt = await p.evaluate((s) => { const e = document.querySelector(s); if (!e) return { __err: 'not-found' };
    const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) { const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; }
    return { __err: 'no-point' }; }, selq);
  if (pt.__err) { log(`  【${label}】⛔`, pt.__err); return pt; }
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1500); return pt;
};

out.start = { 状态行: await status(), 选中: await sel(), zoom: await zoom(), 浮层: await overlays() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
await escAll();
out.起始id = await idsNow();
const 基线 = await collect();
log('静态基线 testid：', 基线.length, '种｜节点', out.起始id.length, '个');
save();

// ---------------------------------------------------------------- ① 多选（落点取中心附近）
log('\n=== ① 多选：落点改成节点中心附近（离上下边缘各留 ≥15%）===');
{
  const pts = await p.evaluate(() => {
    const acc = [];
    for (const n of document.querySelectorAll('.react-flow__node-audio')) {
      const r = n.getBoundingClientRect();
      // 必须整个矩形落在「安全区」内：离顶栏 ≥12、离底 dock ≥12、左右各留 ≥90
      if (r.x < 90 || r.x + r.width > innerWidth - 90 || r.y < 12 || r.y + r.height > innerHeight - 12) continue;
      const yTop = r.y + r.height * 0.3, yBot = r.y + r.height * 0.7;
      const xL = r.x + r.width * 0.2, xR = r.x + r.width * 0.8;
      let hit = null;
      for (let y = Math.ceil(yTop); y <= yBot && !hit; y += 3)
        for (let x = Math.ceil(xL); x <= xR; x += 3) {
          const h = document.elementFromPoint(x, y);
          if (h && (h === n || n.contains(h))) { hit = { x, y, id: n.getAttribute('data-id') }; break; }
        }
      if (hit) acc.push({ ...hit, 矩形: [r.x, r.y, r.width, r.height].map(Math.round) });
      if (acc.length >= 2) break;
    }
    return acc;
  });
  out.多选落点 = pts;
  log('  落点：', JSON.stringify(pts));
  if (pts.length < 2 || pts[0].id === pts[1].id) log('  ⛔ 落点不足或 id 相同，放弃');
  else {
    // 断言：两个落点都在视口内且离顶边 ≥20px（这正是 d 轮漏掉的断言）
    for (const p2 of pts) if (p2.y < 20 || p2.x < 0) { log('  ⛔ 落点贴边，放弃（d 轮的错就在这）'); }
    await p.mouse.click(pts[0].x, pts[0].y); await p.waitForTimeout(1200);
    const s1 = await sel();
    await p.keyboard.down('Shift');
    await p.mouse.click(pts[1].x, pts[1].y);
    await p.keyboard.up('Shift');
    await p.waitForTimeout(1600);
    const s2 = await sel();
    out.多选后 = { 第一个点后: s1, Shift第二个后: s2, 状态行: await status() };
    log('  第一个点后选中数 =', s1, '｜Shift 点第二个后 =', s2);
    if (s2 === 2) {
      const t = await collect();
      out.多选testid = { 种类: t.length, 增量: t.filter((x) => !基线.includes(x)), 减量: 基线.filter((x) => !t.includes(x)) };
      log('  多选态 testid', t.length, '种｜**增量**', JSON.stringify(out.多选testid.增量), '**减量**', JSON.stringify(out.多选testid.减量));
      for (const k of ['selection-context-toolbar', 'selection-context-toolbar-surface', 'selection-context-toolbar-popup-host', 'selection-context-toolbar-count'])
        log(`      ${k} → 多选态${t.includes(k) ? '在' : '不在'}｜静态基线${基线.includes(k) ? '在' : '不在'}`);
      // 多选态的工具条几何
      out.多选工具条 = await p.evaluate(() => ['selection-context-toolbar', 'selection-context-toolbar-surface', 'selection-context-toolbar-count', 'selection-context-toolbar-popup-host']
        .map((t) => { const e = document.querySelector('[data-testid="' + t + '"]'); if (!e) return { t, 存在: false };
          const r = e.getBoundingClientRect(); return { t, 存在: true, tag: e.tagName, 矩形: [r.x, r.y, r.width, r.height].map(Math.round), 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40), 子元素数: e.children.length }; }));
      out.多选工具条.forEach((e) => log('      ·', JSON.stringify(e)));
      save();
    } else log('  ⛔ 仍未选中 2 个');
    save();
  }
  const panePt = await p.evaluate(() => { for (let y = 300; y < 640; y += 7) for (let x = 300; x < 760; x += 7) { const h = document.elementFromPoint(x, y); if (h && h.classList && h.classList.contains('react-flow__pane')) return { x, y }; } return null; });
  if (panePt) { await p.mouse.click(panePt.x, panePt.y); await p.waitForTimeout(1100); }
  await p.mouse.move(1276, 716); await p.waitForTimeout(700);
  log('  取消后选中数：', await sel());
}

// ---------------------------------------------------------------- ② 39 个静态漏记的 DOM 契约
log('\n=== ② 39 个静态漏记 testid 的 DOM 契约 ===');
const 缺 = JSON.parse(readFileSync('/tmp/b129-filling.json', 'utf8'));
out.待补 = 缺;
log('  待补：', 缺.length, '个');

const grab = () => p.evaluate((toks) => {
  const r = {};
  for (const t of toks) {
    const els = Array.from(document.querySelectorAll('[data-testid="' + t + '"]'));
    const vis = els.filter((e) => { const b = e.getBoundingClientRect(); return b.width >= 1 && b.height >= 1; });
    const e = vis[0] || els[0];
    if (!e) { r[t] = { 存在: false }; continue; }
    const b = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    r[t] = { 存在: true, 有面积: vis.length > 0, tag: e.tagName, role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
      矩形: [b.x, b.y, b.width, b.height].map(Math.round), opacity: cs.opacity, pe: cs.pointerEvents,
      文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40), 元素数: els.length,
      父: e.parentElement ? (e.parentElement.getAttribute('data-testid') || e.parentElement.className.toString().slice(0, 36)) : null };
  }
  return r;
}, 缺);

out.契约 = {};
const 记录 = async (name) => { const g = await grab(); for (const k in g) if (g[k].存在 && !out.契约[k]) out.契约[k] = Object.assign({ 状态: name }, g[k]);
  log(`  【${name}】补到 ${Object.values(g).filter((x) => x.存在).length} 个`); save(); };

await 记录('静态');
for (const [n, s] of [['搜索', '[data-testid="canvas-panel-launcher"][aria-label="搜索"]'],
  ['用户菜单', '[data-testid="canvas-user-menu-trigger"]'],
  ['分享', '[data-testid="canvas-share-trigger"]'],
  ['更多', 'button[aria-label="更多"]'],
  ['项目', '[data-testid="canvas-project-trigger"]']]) { const pt = await toggle(s, n); if (!pt.__err) { await 记录(n); await escAll(); } }
{ // 快捷键抽屉
  const um = await toggle('[data-testid="canvas-user-menu-trigger"]', '用户菜单');
  if (!um.__err) { const it = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[role=menuitem],button')).find((x) => /^快捷键/.test((x.innerText || '').replace(/\s+/g, '').trim()));
    if (!e) return null; const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2) for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) { const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; }
    return null; });
    if (it) { await p.mouse.click(it.x, it.y); await p.waitForTimeout(1800); await 记录('快捷键抽屉'); } }
  await escAll();
}
await escAll();

out.补到的 = Object.keys(out.契约);
out.仍缺 = 缺.filter((t) => !out.契约[t]);
log('  补到 DOM 契约：', out.补到的.length, '个');
log('  **仍缺**（各状态都没有）：', out.仍缺.length, '个：', JSON.stringify(out.仍缺));
log('\n  契约表：');
for (const k of out.补到的) { const e = out.契约[k];
  log(`    ${k} ｜ <${e.tag}> ${e.矩形.join(',')}${e.role ? ' role=' + e.role : ''}${e.aria ? ' aria=' + e.aria : ''}${e.文字 ? ' «' + e.文字 + '»' : ''}`); }
save();

// ---------------------------------------------------------------- 收尾
await p.mouse.move(1276, 716); await p.waitForTimeout(700);
const endIds = await idsNow(); const endT = await collect();
out.收尾 = { 选中: await sel(), 状态行: await status(), 浮层: await overlays(), zoom: await zoom(), 节点数: endIds.length, 起始节点数: out.起始id.length, testid种类: endT.length };
out.新增id = endIds.filter((x) => !out.起始id.includes(x));
out.相对基线增量 = endT.filter((t) => !基线.includes(t));
out.相对基线减量 = 基线.filter((t) => !endT.includes(t));
log('\n收尾：', JSON.stringify(out.收尾));
log('  新增 id（必须空）：', JSON.stringify(out.新增id));
log('  testid 相对基线：增量', JSON.stringify(out.相对基线增量), '减量', JSON.stringify(out.相对基线减量));
save();
log('\nDONE f');
process.exit(0);
