// 批次 124 · b 轮：**A/B/A 三段**，验「节点 N」面板只列非零类型。
//
// 🔴 a 轮拿到了一对**不共享同一假设**的关键读数（同一画布、同一时刻、同一份节点数据）：
//   · 顶栏「节点 N」`canvas-node-summary-popover` `200×292@73,47` 逐字
//     `图片 1 ｜ 视频 1 ｜ 文本 3 ｜ 音频 68 ｜ 时间线 2 ｜ 外部 1 ｜ 查看项目信息` —— **没有「主体」**
//   · 「查看项目信息」`workspace-project-info-dialog` `800×546@240,87` 的「节点分布」逐字
//     `全部节点 全部 76 ｜ 图片 1 ｜ 视频 1 ｜ 音频 68 ｜ 文本 3 ｜ 时间线 2 ｜ **主体 0** ｜ 其他 1`
//     —— **「主体 0」明明列出来了**
//   ⇒ 假设：**「节点 N」只列非零类型；「项目信息」列全部类型（含 0）**。
//
// 本轮把这条做成 **A/B/A**（造一个主体节点 → 读两个面板 → 删掉 → 再读两个面板）：
//   A  = 6 行无主体 ｜ 项目信息「主体 0」
//   B  = 7 行有主体 ｜ 项目信息「主体 1」
//   A' = 6 行无主体 ｜ 项目信息「主体 0」
// ⇒ 两个面板在**同一个变量**上同步变化，才算证据。
//
// 🆕 a 轮顺带记到一处**命名不一致**：导演台在「节点 N」里叫「**外部**」，
//   在「项目信息 · 节点分布」里叫「**其他**」—— 同一份数据、两套叫法。
//
// 护栏：造节点前存 id 集合；建后差集**恰好一个**且**同时是 `.selected`**；
//      事后「本轮消失的 id」**恰好只有 SELF**（z 轮核对）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b', 自建: [] };
const save = () => writeFileSync(new URL('./_tmp-b124b.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node[data-id]')).map((n) => n.getAttribute('data-id')));

const railClick = async (label) => {
  const pt = await p.evaluate((lb) => { const rail = document.querySelector('[data-testid="canvas-fixed-toolbar-left-rail"]');
    const btn = Array.from(rail.querySelectorAll('button,[role=button]')).find((e) => (e.getAttribute('aria-label') || '').trim() === lb);
    if (!btn) return { __err: 'no-btn' }; const r = btn.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
      const e = document.elementFromPoint(x, y); if (e && (e === btn || btn.contains(e))) return { x, y, 矩形: [r.x, r.y, r.width, r.height].map(Math.round) }; }
    return { __err: 'no-point' }; }, label);
  if (pt.__err) return pt;
  await p.mouse.click(pt.x, pt.y);
  return pt;
};

// 读「节点 N」面板
const readNodeSummary = async () => {
  const pt = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-node-summary-trigger"]');
    const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
      const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; }
    return null; });
  if (!pt) return { __err: 'no-trigger-point' };
  await p.mouse.click(pt.x, pt.y);
  await p.waitForTimeout(1500);
  const r = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-node-summary-popover"]');
    if (!e) return { __err: 'no-panel' }; const q = e.getBoundingClientRect();
    return { 矩形: [q.x, q.y, q.width, q.height].map(Math.round), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(),
      有主体: /主体/.test(e.innerText || '') }; });
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  return r;
};

// 读「项目信息」面板的节点分布
const readProjectInfo = async () => {
  const s = await readNodeSummary();            // 先开一次节点 N，才有面板可点末行
  if (s.__err) return { __err: 'no-node-summary' };
  await p.waitForTimeout(400);
  // 重新打开并点末行
  const pt = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-node-summary-trigger"]');
    const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
      const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; }
    return null; });
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1400);
  const hit = await p.evaluate(() => { for (const e of document.querySelectorAll('button,[role=button]')) {
    if (!/查看项目信息/.test(e.innerText || '')) continue; const r = e.getBoundingClientRect(); if (r.width < 1) continue;
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 3) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 3) {
      const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; } }
    return null; });
  if (!hit) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { __err: 'no-lastrow-point' }; }
  await p.mouse.click(hit.x, hit.y); await p.waitForTimeout(1600);
  const d = await p.evaluate(() => { const m = document.querySelector('[data-testid="workspace-project-info-dialog"]');
    if (!m) return { __err: 'no-dialog' }; const q = m.getBoundingClientRect();
    return { 矩形: [q.x, q.y, q.width, q.height].map(Math.round), 逐字: (m.innerText || '').replace(/\s+/g, ' ').trim(),
      主体段: ((m.innerText || '').match(/主体\s*\d+/) || [])[0] || null }; });
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
  return d;
};

out.start = { zoom: await zoom(), credits: await credits(), status: await status() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
const baseline = new Set(await ids());
out.baseline = baseline.size;

// ================= A =================
out.A = { 节点N: await readNodeSummary(), 项目信息: await readProjectInfo() };
log('\n=== A（造之前）===');
log('  节点N：', JSON.stringify(out.A.节点N));
log('  项目信息：', JSON.stringify(out.A.项目信息));
save();

// ================= B：造一个主体节点 =================
const beforeB = await ids();
const clickPt = await railClick('主体');
log('\n建主体节点，落点：', JSON.stringify(clickPt));
if (clickPt.__err) { log('⛔ 左栏「主体」点不到，中止'); save(); await b.close(); process.exit(3); }
await p.waitForTimeout(1700);
const afterB = await ids();
const diffB = afterB.filter((i) => !beforeB.includes(i));
const selB = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => ({ id: n.getAttribute('data-id'), 标题: (n.innerText || '').split('\n')[0] })));
out.建节点 = { 差集: diffB, 选中: selB };
log('  差集 =', JSON.stringify(diffB), '｜选中 =', JSON.stringify(selB));
if (diffB.length !== 1 || selB.length !== 1 || selB[0].id !== diffB[0]) { log('⛔ 护栏②不通过，中止（z 轮仍会清理）'); save(); await b.close(); process.exit(3); }
const SELF = diffB[0];
out.SELF = SELF;
out.自建.push({ id: SELF, 标题: selB[0].标题 });
log('✅ 护栏②通过：SELF =', SELF, selB[0].标题);

out.B = { 节点N: await readNodeSummary(), 项目信息: await readProjectInfo() };
log('\n=== B（造了 1 个主体节点之后）===');
log('  节点N：', JSON.stringify(out.B.节点N));
log('  项目信息：', JSON.stringify(out.B.项目信息));
save();

// ================= A'：删掉，回到基线 =================
{
  const beforeDel = await ids();
  const rc = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); const r = n.getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map(Math.round); }, SELF);
  await p.mouse.move(Math.round(rc[0] + rc[2] / 2), Math.round(rc[1] + rc[3] / 2)); await p.waitForTimeout(420);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(300); await p.mouse.up({ button: 'right' });
  await p.waitForTimeout(1400);
  const del = await p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]')) {
    if (getComputedStyle(m).visibility === 'hidden') continue;
    for (const it of m.querySelectorAll('[role=menuitem]')) { const t = (it.innerText || '').replace(/\s+/g, ' ').trim();
      if (!/^删除/.test(t)) continue; if (it.getAttribute('aria-disabled') === 'true') return { t, disabled: true };
      const r = it.getBoundingClientRect(); if (r.width < 1) continue;
      for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 3) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 3) {
        const e = document.elementFromPoint(x, y); if (e && (e === it || it.contains(e))) return { t, x, y }; }
      return { t, __err: 'no-point' }; } } return null; });
  log('\n删除项：', JSON.stringify(del));
  if (del && !del.disabled && !del.__err) {
    await p.mouse.click(del.x, del.y); await p.waitForTimeout(2200);
    const afterDel = await ids();
    const gone = beforeDel.filter((x) => !afterDel.includes(x));
    out.删除 = { 消失: gone, 恰好SELF: gone.length === 1 && gone[0] === SELF, 前: beforeDel.length, 后: afterDel.length };
    log('  消失 =', JSON.stringify(gone), '｜恰好 SELF？', out.删除.恰好SELF);
  } else { await p.keyboard.press('Escape'); await p.waitForTimeout(700); out.删除 = { aborted: true, del }; log('  ⛔ 删不掉，留给 z 轮'); }
  save();
}

out.A2 = { 节点N: await readNodeSummary(), 项目信息: await readProjectInfo() };
log('\n=== A′（删掉之后）===');
log('  节点N：', JSON.stringify(out.A2.节点N));
log('  项目信息：', JSON.stringify(out.A2.项目信息));
save();

// ---- 收尾 ----
if ((await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length)) !== 0) {
  const bk = await p.evaluate(() => { for (let y = 200; y < 620; y += 7) for (let x = 200; x < 1100; x += 7) {
    const e = document.elementFromPoint(x, y); if (e && e.classList && e.classList.contains('react-flow__pane')) return { x, y }; } return null; });
  if (bk) { await p.mouse.click(bk.x, bk.y); await p.waitForTimeout(1200); }
}
out.终态 = { zoom: await zoom(), credits: await credits(), status: await status(),
  浮层: await p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu]')).filter((m) => m.getBoundingClientRect().width > 1).length) };
log('\n终态：', JSON.stringify(out.终态));
save();
log('\nDONE b');
process.exit(0);
