// 批次 127 · c 轮：补 b 轮被超时掐断的 ④，并回答 b 轮逼出来的新问题：
//   ① b 轮发现**九个页签一行放不下**（tablist `overflow-x:auto`、`scrollWidth 519` vs
//      `clientWidth 320`），最后三个（时间线 / 组 / 其他）`elementFromPoint` 扫不到命中点
//      ⇒ **用户到底怎么点到它们？** 本轮逐个试：横向滚轮 / Shift+滚轮 / 拖拽 / 键盘。
//   ② 滚到「其他 1」（导演台）后点它，验证结果行 testid 里的节点 id **就是画布节点的 data-id**。
//   ③ 分页器（`NAV[aria="Search result pages"]`，`1 / 6`）点「前往下一页」换不换一批。
//   ④ 输入框筛选：输入「视频」→ 看结果；再 ⌘A + Delete 清空 → 是否回到 76。
//   ⑤ 每行那个 `role="status"` 的 `sr-only` span 本轮实测**逐字为空**；试一下悬停会不会灌字。
//
// ⛔ 边界：**不点任何结果行**（点了会选中节点并移动视口）；不点生成/扣费控件；
//   打字前一律过 keyGuard。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c' };
const save = () => writeFileSync(new URL('./_tmp-b127c.json', import.meta.url), JSON.stringify(out, null, 1));
const shotDir = new URL('./_tmp-b127a-shots/', import.meta.url);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);

const step = async (name, fn) => { try { const r = await fn(); out[name] = r; log(`  [${name}] ✅`); return r; } catch (e) { out[name] = { __err: String(e).slice(0, 200) }; log(`  [${name}] ⛔ ${String(e).slice(0, 160)}`); return null; } };
const state = () => p.evaluate(() => {
  const panel = document.querySelector('[data-testid="canvas-feature-panel"]');
  if (!panel) return { __err: 'no-panel' };
  const R = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const list = panel.querySelector('[role=tablist]');
  return { 面板: R(panel), aria: panel.getAttribute('aria-label'),
    scrollLeft: list ? list.scrollLeft : null, scrollWidth: list ? list.scrollWidth : null, clientWidth: list ? list.clientWidth : null,
    当前页签: Array.from(panel.querySelectorAll('[role=tab]')).filter((x) => x.getAttribute('aria-selected') === 'true').map((x) => (x.innerText || '').replace(/\s+/g, ' ').trim()),
    页签矩形: Array.from(panel.querySelectorAll('[role=tab]')).map((x) => ({ 文字: (x.innerText || '').replace(/\s+/g, ' ').trim(), rect: R(x) })),
    结果行: Array.from(panel.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).map((x) => x.getAttribute('data-testid')),
    结果逐字: Array.from(panel.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).map((x) => (x.innerText || '').replace(/\s+/g, ' ').trim()).slice(0, 4),
    分页逐字: (() => { const n = panel.querySelector('[aria-label="Search result pages"]'); return n ? (n.innerText || '').replace(/\s+/g, ' ').trim() : null; })(),
    输入值: (() => { const i = panel.querySelector('input'); return i ? i.value : null; })(),
    逐字: (panel.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 150) };
});

out.start = { 浮层: await overlays(), 选中: await sel(), zoom: await zoom(), credits: await credits(), status: await status() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);

out.基线 = await state();
log('\n=== 基线 ===\n  ', JSON.stringify({ 面板: out.基线.面板, scrollLeft: out.基线.scrollLeft, scrollWidth: out.基线.scrollWidth, clientWidth: out.基线.clientWidth, 当前页签: out.基线.当前页签, 结果行数: out.基线.结果行.length, 分页: out.基线.分页逐字 }));

// ---- ① 页签条怎么横向滚：四种手法逐个试，每种都读 scrollLeft ----
const mid = out.基线.页签矩形[2] ? [out.基线.页签矩形[2].rect[0] + 10, out.基线.页签矩形[2].rect[1] + 18] : [800, 130];
out.滚法 = { 落点: mid };
const tryScroll = async (name, fn) => {
  const before = await p.evaluate(() => (document.querySelector('[data-testid="canvas-feature-panel"] [role=tablist]') || {}).scrollLeft ?? null);
  try { await fn(); } catch (e) { out.滚法[name] = { __err: String(e).slice(0, 120) }; return; }
  await p.waitForTimeout(700);
  const after = await p.evaluate(() => { const l = document.querySelector('[data-testid="canvas-feature-panel"] [role=tablist]');
    return l ? { scrollLeft: l.scrollLeft, scrollWidth: l.scrollWidth, clientWidth: l.clientWidth } : null; });
  out.滚法[name] = { 前: before, 后: after, 变了: after && before !== null && after.scrollLeft !== before };
  log(`  手法「${name}」：scrollLeft ${before} → ${after && after.scrollLeft}  ${out.滚法[name].变了 ? '✅ 有效' : '❌ 无变化'}`);
};
log('\n=== ① 页签条横向滚动：四种手法 ===');
await tryScroll('横向滚轮', async () => { await p.mouse.move(mid[0], mid[1]); await p.mouse.wheel(200, 0); });
await tryScroll('纵向滚轮', async () => { await p.mouse.move(mid[0], mid[1]); await p.mouse.wheel(0, 200); });
await tryScroll('Shift+纵向滚轮', async () => { await p.keyboard.down('Shift'); await p.mouse.move(mid[0], mid[1]); await p.mouse.wheel(0, 200); await p.keyboard.up('Shift'); });
await tryScroll('拖拽', async () => {
  await p.mouse.move(out.基线.页签矩形[1].rect[0] + 20, mid[1]);
  await p.mouse.down();
  for (let i = 1; i <= 8; i++) { await p.mouse.move(out.基线.页签矩形[1].rect[0] + 20 - i * 25, mid[1]); await p.waitForTimeout(40); }
  await p.mouse.up();
});
out.滚后 = await state();
log('  滚动后页签矩形：', JSON.stringify(out.滚后.页签矩形));
log('  滚动后 scrollLeft：', out.滚后.scrollLeft, '｜可命中扫描：');
out.滚动后可命中 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="canvas-feature-panel"] [role=tab]')).map((e) => {
  const r = e.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2)
    for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) { const h = document.elementFromPoint(x, y);
      if (h && h.closest('[role=tab]') === e) return { 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), 点: [x, y] }; }
  return { 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), 点: null };
}));
out.滚动后可命中.forEach((t) => log(`    «${t.文字}» → ${JSON.stringify(t.点)}`));
save();
await p.screenshot({ path: new URL('05-tabs-scrolled.png', shotDir).pathname, clip: { x: 750, y: 40, width: 350, height: 200 } });

// ---- ② 点「其他 1」（导演台），验证结果行 testid 里的 id 就是画布节点 data-id ----
const otherTab = out.滚动后可命中.find((t) => /其他/.test(t.文字));
if (otherTab && otherTab.点) {
  await step('点其他页签', async () => { await p.mouse.click(otherTab.点[0], otherTab.点[1]); await p.waitForTimeout(1200);
    const s2 = await state();
    // 拿画布上「导演台」节点的 data-id 做对照
    const canvas = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node-external')).map((e) => ({ id: e.getAttribute('data-id'), aria: e.getAttribute('aria-label') })));
    return { 面板: s2.面板, 当前页签: s2.当前页签, 结果行: s2.结果行, 结果逐字: s2.结果逐字, 画布外部节点: canvas,
      id对得上: s2.结果行.length === 1 && canvas.some((c) => s2.结果行[0] === 'canvas-search-result-node_' + c.id) };
  });
  log('  点「其他 1」：', JSON.stringify(out.点其他页签));
  await p.screenshot({ path: new URL('06-tab-other-result.png', shotDir).pathname, clip: { x: 750, y: 40, width: 350, height: 300 } });
} else { log('\n=== ② ⛔ 滚完之后仍点不到「其他」页签 ==='); out.点其他页签 = { __err: 'no-tab-point' }; }
save();

// ---- ③ 分页 ----
const backAll = await p.evaluate(() => { const t = Array.from(document.querySelectorAll('[data-testid="canvas-feature-panel"] [role=tab]')).find((e) => (e.innerText || '').replace(/\s+/g, '').startsWith('全部'));
  if (!t) return null; const r = t.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) { const h = document.elementFromPoint(x, y);
    if (h && h.closest('[role=tab]') === t) return { x, y }; } return null; });
if (backAll) { await p.mouse.click(backAll.x, backAll.y); await p.waitForTimeout(1100); }
out.分页前 = await state();
log('\n=== ③ 分页 ===\n  翻页前：当前页签=', JSON.stringify(out.分页前.当前页签), '分页逐字=', JSON.stringify(out.分页前.分页逐字), '结果行数=', out.分页前.结果行.length);
const nextPt = await p.evaluate(() => { const n = document.querySelector('[data-testid="canvas-feature-panel"] [aria-label="Search result pages"]');
  if (!n) return { __err: 'no-nav' };
  const btn = Array.from(n.querySelectorAll('button')).find((e) => /下一页/.test(e.getAttribute('aria-label') || ''));
  if (!btn) return { __err: 'no-next-btn', 全部按钮: Array.from(n.querySelectorAll('button')).map((e) => e.getAttribute('aria-label')) };
  const r = btn.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
    const h = document.elementFromPoint(x, y); if (h && (h === btn || btn.contains(h))) return { x, y, aria: btn.getAttribute('aria-label'), 禁用: btn.hasAttribute('disabled') }; }
  return { __err: 'no-point' }; });
log('  「下一页」：', JSON.stringify(nextPt));
await step('翻页', async () => { await p.mouse.click(nextPt.x, nextPt.y); await p.waitForTimeout(1300);
  const s3 = await state();
  return { 分页逐字: s3.分页逐字, 结果行: s3.结果行, 结果逐字: s3.结果逐字,
    换了一批: JSON.stringify(s3.结果行) !== JSON.stringify(out.分页前.结果行) }; });
log('  翻页后：', JSON.stringify(out.翻页));
await p.screenshot({ path: new URL('07-page2.png', shotDir).pathname, clip: { x: 750, y: 40, width: 350, height: 640 } });
save();

// ---- ④ 悬停结果行：每行那个 role=status 的 sr-only span 会不会灌字 ----
await step('悬停看status', async () => {
  const r0 = await p.evaluate(() => { const row = document.querySelector('[data-testid^="canvas-search-result-node_"]'); if (!row) return null;
    const q = row.getBoundingClientRect(); return { x: q.x + 40, y: q.y + q.height / 2, tid: row.getAttribute('data-testid') }; });
  if (!r0) return { __err: 'no-row' };
  const before = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="canvas-feature-panel"] [role=status]')).map((x) => (x.textContent || '').trim()).filter(Boolean));
  await p.mouse.move(r0.x, r0.y); await p.waitForTimeout(900);
  const after = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="canvas-feature-panel"] [role=status]')).map((x) => (x.textContent || '').trim()).filter(Boolean));
  return { 行: r0.tid, 悬停前有字的status: before, 悬停后有字的status: after, 变了: JSON.stringify(before) !== JSON.stringify(after) };
});
log('  悬停：', JSON.stringify(out.悬停看status));

// ---- ⑤ 输入框筛选：输入「视频」→ 读结果；再 ⌘A + Delete 清空 ----
const inputPt = await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-feature-panel"] input'); if (!i) return null;
  const r = i.getBoundingClientRect(); for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
    const h = document.elementFromPoint(x, y); if (h && (h === i || i.contains(h))) return { x, y }; } return null; });
log('\n=== ⑤ 输入框筛选 ===\n  输入框落点：', JSON.stringify(inputPt));
if (inputPt) {
  await p.mouse.click(inputPt.x, inputPt.y); await p.waitForTimeout(500);
  // 📌 这里 keyGuard 必然报「unsafe：焦点在输入面」——**那正是我们要的**：
  // 本步的**意图就是往搜索框里打字**。所以只记录它的判定，不据此中止；
  // 但绝不能用 pressLetter（那个 helper 会在这种判定下直接抛错）。
  out.打字前焦点判定 = await keyGuard(p);
  log('  打字前 keyGuard 判定：', JSON.stringify(out.打字前焦点判定));
  await step('输入视频', async () => { await p.keyboard.type('视频', { delay: 120 });
    await p.waitForTimeout(1200); const s = await state();
    return { 输入值: s.输入值, 当前页签: s.当前页签, 结果行数: s.结果行.length, 结果逐字: s.结果逐字, 逐字: s.逐字 }; });
  log('  输入「视频」：', JSON.stringify(out.输入视频));
  await p.screenshot({ path: new URL('08-input-filter.png', shotDir).pathname, clip: { x: 750, y: 40, width: 350, height: 300 } });
  await step('清空输入', async () => { await p.keyboard.press('Meta+a'); await p.waitForTimeout(250); await p.keyboard.press('Delete');
    await p.waitForTimeout(1200); const s = await state();
    return { 输入值: s.输入值, 当前页签: s.当前页签, 结果行数: s.结果行.length, 分页逐字: s.分页逐字 }; });
  log('  ⌘A + Delete 清空：', JSON.stringify(out.清空输入));
}
save();

// ---- 收尾：Esc 关面板，回到干净终态 ----
await p.keyboard.press('Escape'); await p.waitForTimeout(1300);
out.收尾1 = { 浮层: await overlays(), 面板在: await p.evaluate(() => !!document.querySelector('[data-testid="canvas-feature-panel"]')), 选中: await sel() };
await p.keyboard.press('Escape'); await p.waitForTimeout(1300);
out.收尾2 = { 浮层: await overlays(), 面板在: await p.evaluate(() => !!document.querySelector('[data-testid="canvas-feature-panel"]')),
  选中: await sel(), zoom1: await zoom(), credits: await credits(), status: await status() };
await p.waitForTimeout(1200);
out.收尾2.zoom2 = await zoom();
log('\n收尾：', JSON.stringify(out.收尾2));
save();
log('\nDONE c');
process.exit(0);
