// 批次 121 · z 轮（清理）：删掉本轮自建的 **1 条边 ＋ 3 个节点**，并归位。
//
// 自建清单（全部由本轮自己创建，**没有碰任何他人的节点**）：
//   `node_5k3gf1n51s` 视频 2（b 轮建，d2 轮拖到画布左下）
//   `node_bm52y0m7hn` 视频 3（b 轮建，与 视频 2 重叠、未连线）
//   `node_fs3jetarej` 视频 4（e 轮由 ⊕ 菜单「添加节点」创建，f 轮拖到右下）
//   边：`edge_kz8dze9vxz`（`视频 2 → 视频 4`，`rf__edge-edge_kz8dze9vxz`）
//
// 护栏：②删前确认目标仍 selected；③事后核对「本轮消失的 id」**恰好只有 SELF**（逐个动作核）。
// ④落点在动作即将发生的那一刻现算；`elementFromPoint` 必须落在**目标自身**内。
// 📌 批次 120 立规：删节点**走右键菜单**、不走键盘（中心落点会把焦点交给子控件）。
// 📌 批次 121 补充：删**边**要先点中 `path.react-flow__edge-interaction`（20px 命中区），
//   它是 SVG path，没有 testid，判据用**类名 + 命中自身**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'z', 自建节点: ['node_5k3gf1n51s', 'node_bm52y0m7hn', 'node_fs3jetarej'], 自建边: 'edge_kz8dze9vxz' };
const save = () => writeFileSync(new URL('./_tmp-b121z.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const tool = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]'); return e ? e.getAttribute('aria-label') : null; });
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node[data-id]')).map((n) => n.getAttribute('data-id')));
const edgeIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__edge')).map((e) => e.getAttribute('data-id')));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);

out.start = { zoom: await zoom(), credits: await credits(), tool: await tool(), status: await status(), 节点: (await ids()).length, 边: await edgeIds() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
out.base = { 节点: await ids(), 边: await edgeIds() };

// ============================================================
// 1) 删边：点中 20px 命中区 → 选中 → ⌫（必要时退回右键菜单）
// ============================================================
if (out.start.边.length === 1) {
  const ep = await p.evaluate(() => {
    const h = document.querySelector('.react-flow__edge-interaction'); if (!h) return { __err: 'no-hit-area' };
    const r = h.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 3)
      for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 3) {
        if (x < 2 || y < 2 || y > innerHeight - 2 || x > innerWidth - 2) continue;
        const e = document.elementFromPoint(x, y);
        if (e === h) return { x, y, 命中区矩形: [r.x, r.y, r.width, r.height].map(Math.round) }; }
    return { __err: 'no-point-on-hit-area', 命中区矩形: [r.x, r.y, r.width, r.height].map(Math.round) };
  });
  log('\n边的命中区落点：', JSON.stringify(ep));
  out.edgePoint = ep;
  if (!ep.__err) {
    const before = await edgeIds();
    await p.mouse.click(ep.x, ep.y); await p.waitForTimeout(1500);
    out.edgeSelected = await status();
    log('  点后状态：', out.edgeSelected);
    if (/, 1 selected/.test(out.edgeSelected)) {
      await p.keyboard.press('Backspace'); await p.waitForTimeout(1800);
    }
    const after = await edgeIds();
    const gone = before.filter((x) => !after.includes(x));
    out.edgeGone = { before, after, 消失: gone, 恰好SELF: gone.length === 1 && gone[0] === 'edge_kz8dze9vxz' };
    log('  删边结果：', JSON.stringify(out.edgeGone));
    if (!out.edgeGone.恰好SELF) {
      log('  ⚠️ ⌫ 没删掉边 ⇒ 退回右键菜单');
      await p.mouse.move(ep.x, ep.y); await p.waitForTimeout(400);
      await p.mouse.down({ button: 'right' }); await p.waitForTimeout(300); await p.mouse.up({ button: 'right' });
      await p.waitForTimeout(1400);
      const del = await p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]')) {
        if (getComputedStyle(m).visibility === 'hidden') continue;
        for (const it of m.querySelectorAll('[role=menuitem]')) {
          const t = (it.innerText || '').replace(/\s+/g, ' ').trim(); if (!/^删除/.test(t)) continue;
          const r = it.getBoundingClientRect(); if (r.width < 1) continue;
          for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 3) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 3) {
            const e = document.elementFromPoint(x, y); if (e && (e === it || it.contains(e))) return { t, x, y, 矩形: [r.x, r.y, r.width, r.height].map(Math.round) }; }
          return { t, __err: 'no-point' }; } } return null; });
      log('  菜单删除项：', JSON.stringify(del));
      if (del && !del.__err) { await p.mouse.click(del.x, del.y); await p.waitForTimeout(2000); }
      const a2 = await edgeIds(); const g2 = before.filter((x) => !a2.includes(x));
      out.edgeGone = { after: a2, 消失: g2, 恰好SELF: g2.length === 1 && g2[0] === 'edge_kz8dze9vxz', 走法: '右键菜单' };
      log('  删边结果（菜单）：', JSON.stringify(out.edgeGone));
    }
  }
}
save();

// ============================================================
// 2) 删三个自建节点：逐个走右键菜单 →「删除」
// ============================================================
out.deletions = [];
for (const T of out.自建节点) {
  const before = await ids();
  if (!before.includes(T)) { log(`\n${T} 已不在 ⇒ 跳过`); out.deletions.push({ id: T, skipped: true }); save(); continue; }
  // 确保选中
  let selNow = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id')));
  if (selNow.length !== 1 || selNow[0] !== T) {
    const sp = await p.evaluate((id) => { const n = document.querySelector(`.react-flow__node[data-id="${id}"]`); if (!n) return { __err: 'gone' };
      const r = n.getBoundingClientRect();
      for (let y = Math.ceil(r.y) + 8; y < r.y + r.height - 8; y += 4)
        for (let x = Math.ceil(r.x) + 8; x < r.x + r.width - 8; x += 4) { if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
          const e = document.elementFromPoint(x, y); if (e && (e === n || n.contains(e))) return { x, y }; }
      return { __err: 'unreachable', rect: [r.x, r.y, r.width, r.height].map(Math.round) }; }, T);
    if (!sp.__err) { await p.mouse.click(sp.x, sp.y); await p.waitForTimeout(1500);
      selNow = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => n.getAttribute('data-id'))); }
  }
  log(`\n=== 删 ${T}｜选中态 ${JSON.stringify(selNow)} ===`);
  if (selNow.length !== 1 || selNow[0] !== T) { log('  ⛔ 没能选中 ⇒ 中止（不硬删）'); out.deletions.push({ id: T, aborted: 'not-selected' }); save(); continue; }
  const rc = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); const r = n.getBoundingClientRect();
    return [r.x, r.y, r.width, r.height].map(Math.round); }, T);
  const rx = Math.round(rc[0] + rc[2] / 2), ry = Math.round(rc[1] + rc[3] / 2);
  const beforeDel = await ids();
  await p.mouse.move(rx, ry); await p.waitForTimeout(450);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(300); await p.mouse.up({ button: 'right' });
  await p.waitForTimeout(1400);
  const del = await p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]')) {
    if (getComputedStyle(m).visibility === 'hidden') continue;
    for (const it of m.querySelectorAll('[role=menuitem]')) {
      const t = (it.innerText || '').replace(/\s+/g, ' ').trim(); if (!/^删除/.test(t)) continue;
      if (it.getAttribute('aria-disabled') === 'true' || it.hasAttribute('disabled')) return { t, disabled: true };
      const r = it.getBoundingClientRect(); if (r.width < 1) continue;
      for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 3) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 3) {
        const e = document.elementFromPoint(x, y); if (e && (e === it || it.contains(e))) return { t, x, y, 矩形: [r.x, r.y, r.width, r.height].map(Math.round) }; }
      return { t, __err: 'no-point' }; } } return null; });
  log('  「删除」项：', JSON.stringify(del));
  if (!del || del.disabled || del.__err) { log('  ⛔ 拿不到可点的「删除」⇒ 中止');
    await p.keyboard.press('Escape'); await p.waitForTimeout(600);
    out.deletions.push({ id: T, aborted: 'no-del', del }); save(); continue; }
  await p.mouse.click(del.x, del.y);
  await p.waitForTimeout(2200);
  const after = await ids();
  const gone = beforeDel.filter((x) => !after.includes(x));
  const ok = gone.length === 1 && gone[0] === T;
  log(`  消失的 id = ${JSON.stringify(gone)}｜恰好 SELF？ ${ok}｜${beforeDel.length} → ${after.length}`);
  out.deletions.push({ id: T, 消失: gone, 恰好SELF: ok, 前: beforeDel.length, 后: after.length });
  save();
}

// ============================================================
// 3) 归位
// ============================================================
let z1 = await zoom(); await p.waitForTimeout(700); let z2 = await zoom();
if (z1 !== 'Zoom options, 60%' || z2 !== 'Zoom options, 60%') {
  const zp = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); const r = e.getBoundingClientRect();
    const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2); const el = document.elementFromPoint(cx, cy);
    return { x: cx, y: cy, ok: el ? (el === e || e.contains(el)) : false }; });
  log('\n缩放归位落点自检：', JSON.stringify(zp));
  if (zp.ok) { await p.mouse.click(zp.x, zp.y); await p.waitForTimeout(700);
    if (await p.evaluate(() => !!document.querySelector('[data-testid="canvas-zoom-percent-input"]'))) {
      await p.fill('[data-testid="canvas-zoom-percent-input"]', '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1900); } }
  z1 = await zoom(); await p.waitForTimeout(700); z2 = await zoom();
}
out.zoom归位 = { 读数1: z1, 读数2: z2, 一致: z1 === z2 && z1 === 'Zoom options, 60%' };
out.tool = await tool();
out.终态 = { 节点: await ids(), 边: await edgeIds(), 选中: await status(), 积分: await credits() };
log('\n终态：', JSON.stringify({ 缩放: out.zoom归位, 工具: out.tool, 节点数: out.终态.节点.length, 边: out.终态.边, 状态行: out.终态.选中, 积分: out.终态.积分 }));
log('自建节点是否全部清除：', out.自建节点.map((i) => `${i}=${!out.终态.节点.includes(i)}`).join(' '));
save();
log('\nDONE z');
process.exit(0);
