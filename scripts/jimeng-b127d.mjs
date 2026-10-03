// 批次 127 · d 轮：补 c 轮被「切不回全部页签」坑掉的翻页，并测三件还没读数的事：
//   ① 分页器在 76 条结果下点「下一页 / 上一页」是否换一批（c 轮因为 scrollLeft 停在 199.5
//      导致「全部」页签滚出视野、切不回去而没测成 —— **这个坑本身就是结论的一部分**）。
//   ② 面板高度到底跟不跟结果数走？a 轮读 604（全部 76 / 10 行）、c 轮读 604（主体 0 条、其他 1 条）
//      ⇒ 初看与结果数无关；但「输入关键词后 0 条」那一步没记高度，补上。
//   ③ 结果行 testid 的后缀与节点 `data-id` 的确切关系
//      （c 轮 `id对得上=false`，因为 `data-id` 自带 `node_` 前缀，而 testid 后缀没有）。
//   ④ 切页签时页签条的 `scrollLeft` 会不会自动把选中项滚进视野。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'd' };
const save = () => writeFileSync(new URL('./_tmp-b127d.json', import.meta.url), JSON.stringify(out, null, 1));
const shotDir = new URL('./_tmp-b127a-shots/', import.meta.url);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);
const state = () => p.evaluate(() => {
  const panel = document.querySelector('[data-testid="canvas-feature-panel"]');
  if (!panel) return { __err: 'no-panel' };
  const R = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const list = panel.querySelector('[role=tablist]');
  const vp = panel.querySelector('[data-testid="canvas-search-results-viewport"]');
  const nav = panel.querySelector('[aria-label="Search result pages"]');
  return { 面板: R(panel), scrollLeft: list ? list.scrollLeft : null,
    选中页签: Array.from(panel.querySelectorAll('[role=tab]')).filter((x) => x.getAttribute('aria-selected') === 'true').map((x) => (x.innerText || '').replace(/\s+/g, ' ').trim()),
    结果行: Array.from(panel.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).map((x) => x.getAttribute('data-testid')),
    分页: nav ? (nav.innerText || '').replace(/\s+/g, ' ').trim() : null,
    视口: vp ? { rect: R(vp), scrollHeight: vp.scrollHeight, clientHeight: vp.clientHeight, scrollTop: vp.scrollTop } : null,
    输入值: (() => { const i = panel.querySelector('input'); return i ? i.value : null; })(),
    逐字: (panel.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160) };
});
// 点某个 role=tab（按逐字匹配），落点现算 + elementFromPoint 自检；找不到可命中点就报出来
const clickTab = (name) => p.evaluate((nm) => {
  const t = Array.from(document.querySelectorAll('[data-testid="canvas-feature-panel"] [role=tab]'))
    .find((e) => (e.innerText || '').replace(/\s+/g, '').trim() === nm);
  if (!t) return { __err: 'no-tab:' + nm };
  const r = t.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2)
    for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) { const h = document.elementFromPoint(x, y);
      if (h && h.closest('[role=tab]') === t) return { x, y, 矩形: [r.x, r.y, r.width, r.height].map(Math.round) }; }
  return { __err: 'not-clickable:' + nm, 矩形: [r.x, r.y, r.width, r.height].map(Math.round) };
}, name);

out.start = { 浮层: await overlays(), 选中: await sel(), zoom: await zoom(), credits: await credits(), status: await status() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);

// ---- 打开搜索面板 ----
const openPt = await p.evaluate(() => { const t = Array.from(document.querySelectorAll('[data-testid="canvas-panel-launcher"]')).find((e) => (e.getAttribute('aria-label') || '') === '搜索');
  if (!t) return null; const r = t.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
    const h = document.elementFromPoint(x, y); if (h && (h === t || t.contains(h))) return { x, y }; } return null; });
if (openPt) { await p.mouse.click(openPt.x, openPt.y); await p.waitForTimeout(1600); }
out.开面板 = await state();
log('\n=== 打开后 ===\n  ', JSON.stringify({ 面板: out.开面板.面板, scrollLeft: out.开面板.scrollLeft, 选中页签: out.开面板.选中页签, 结果行数: out.开面板.结果行.length, 分页: out.开面板.分页, 视口: out.开面板.视口 }));

// ---- ① 翻页 ----
out.翻页 = {};
const navPt = (label) => p.evaluate((lb) => { const n = document.querySelector('[data-testid="canvas-feature-panel"] [aria-label="Search result pages"]');
  if (!n) return { __err: 'no-nav' };
  const btn = Array.from(n.querySelectorAll('button')).find((e) => new RegExp(lb).test(e.getAttribute('aria-label') || ''));
  if (!btn) return { __err: 'no-btn:' + lb, 全部: Array.from(n.querySelectorAll('button')).map((e) => e.getAttribute('aria-label')) };
  const r = btn.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
    const h = document.elementFromPoint(x, y); if (h && (h === btn || btn.contains(h))) return { x, y, aria: btn.getAttribute('aria-label'), 禁用: btn.hasAttribute('disabled') || btn.getAttribute('aria-disabled') === 'true' }; }
  return { __err: 'no-point' }; }, label);

const n0 = await navPt('下一页');
log('\n=== ① 翻页 ===\n  第 1 页 →', JSON.stringify(out.开面板.分页), '结果行数', out.开面板.结果行.length);
log('  「前往下一页」按钮：', JSON.stringify(n0));
out.翻页.下一页按钮 = n0;
if (!n0.__err) {
  await p.mouse.click(n0.x, n0.y); await p.waitForTimeout(1400);
  const s1 = await state();
  out.翻页.第2页 = { 分页: s1.分页, 结果行: s1.结果行, 视口: s1.视口, 换了一批: JSON.stringify(s1.结果行) !== JSON.stringify(out.开面板.结果行) };
  log('  第 2 页：', JSON.stringify({ 分页: s1.分页, 结果行数: s1.结果行.length, 换了一批: out.翻页.第2页.换了一批 }));
  log('  第 2 页结果 testid：', JSON.stringify(s1.结果行));
  await p.screenshot({ path: new URL('09-page2.png', shotDir).pathname, clip: { x: 750, y: 40, width: 350, height: 640 } });
  const pv = await navPt('上一页');
  log('  「前往上一页」按钮：', JSON.stringify(pv));
  out.翻页.上一页按钮 = pv;
  if (!pv.__err) { await p.mouse.click(pv.x, pv.y); await p.waitForTimeout(1400);
    const s0 = await state();
    out.翻页.回到第1页 = { 分页: s0.分页, 与初始相同: JSON.stringify(s0.结果行) === JSON.stringify(out.开面板.结果行) };
    log('  回到第 1 页：', JSON.stringify(out.翻页.回到第1页)); }
}
save();

// ---- ② 面板高度与结果数的关系 ----
out.高度 = { 记录: [] };
const rec = async (label) => { const s = await state(); out.高度.记录.push({ 情形: label, 面板: s.面板, 选中页签: s.选中页签, 结果行数: s.结果行.length, 分页: s.分页, 视口: s.视口 });
  log(`  高度[${label}]：面板=${JSON.stringify(s.面板)} 结果行数=${s.结果行.length} 分页=${JSON.stringify(s.分页)} 视口=${s.视口 ? JSON.stringify(s.视口.rect) + ' scrollH=' + s.视口.scrollHeight : null}`); return s; };
log('\n=== ② 面板高度 vs 结果数 ===');
await rec('全部 76 条 / 每页 10');
const t主体 = await clickTab('主体');
log('  点「主体」落点：', JSON.stringify(t主体));
if (!t主体.__err) { await p.mouse.click(t主体.x, t主体.y); await p.waitForTimeout(1200); await rec('主体 0 条'); }
const t其他 = await clickTab('其他1');
log('  点「其他 1」落点：', JSON.stringify(t其他));
if (!t其他.__err) { await p.mouse.click(t其他.x, t其他.y); await p.waitForTimeout(1200); const s = await rec('其他 1 条');
  out.高度.其他页签scrollLeft = s.scrollLeft; }
// 关键词 0 命中
const inp = await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-feature-panel"] input'); if (!i) return null;
  const r = i.getBoundingClientRect(); for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
    const h = document.elementFromPoint(x, y); if (h && (h === i || i.contains(h))) return { x, y }; } return null; });
if (inp) {
  await p.mouse.click(inp.x, inp.y); await p.waitForTimeout(400);
  out.高度.keyGuard = await keyGuard(p);
  await p.keyboard.type('zzz不存在zzz', { delay: 60 });
  await p.waitForTimeout(1300);
  await rec('关键词 0 命中（在「其他」页签下）');
  await p.keyboard.press('Meta+a'); await p.waitForTimeout(200); await p.keyboard.press('Delete'); await p.waitForTimeout(1000);
  await rec('清空关键词后');
}
out.高度.唯一值 = [...new Set(out.高度.记录.map((r) => JSON.stringify(r.面板)))];
log('  面板矩形出现过几种：', out.高度.唯一值.length, JSON.stringify(out.高度.唯一值));
save();

// ---- ③ 结果行 testid 后缀 vs 节点 data-id ----
out.testid对照 = await p.evaluate(() => {
  const rows = Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).slice(0, 3)
    .map((x) => x.getAttribute('data-testid'));
  const nodes = Array.from(document.querySelectorAll('.react-flow__node')).slice(0, 3).map((e) => e.getAttribute('data-id'));
  const all = Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id'));
  return { 行: rows, 节点dataId样本: nodes, 节点id样本: all.slice(0, 4),
    带node_前缀的比例: (all.filter((x) => /^node_/.test(x)).length + '/' + all.length),
    去前缀后与行后缀相同: rows.length ? rows.every((t) => all.some((n) => 'canvas-search-result-node_' + n.replace(/^node_/, '') === t)) : null };
});
log('\n=== ③ 结果行 testid 与节点 data-id 的关系 ===\n  ', JSON.stringify(out.testid对照, null, 1));

// ---- ④ 切页签时 scrollLeft 是否自动跟随 ----
out.滚动跟随 = [];
for (const nm of ['图片1', '视频1', '音频68', '文本3']) {
  const t = await clickTab(nm);
  if (t.__err) { out.滚动跟随.push({ 页签: nm, 落点: t }); log(`  点「${nm}」：${t.__err}`); continue; }
  await p.mouse.click(t.x, t.y); await p.waitForTimeout(1000);
  const s = await state();
  const selTab = await p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-feature-panel"] [role=tab][aria-selected=true]'); if (!t) return null;
    const r = t.getBoundingClientRect(); const l = document.querySelector('[data-testid="canvas-feature-panel"] [role=tablist]');
    return { 文字: (t.innerText || '').replace(/\s+/g, ' ').trim(), rect: [r.x, r.y, r.width, r.height].map(Math.round),
      完整可见: r.x >= l.getBoundingClientRect().x && r.x + r.width <= l.getBoundingClientRect().x + l.getBoundingClientRect().width,
      scrollLeft: l.scrollLeft }; });
  out.滚动跟随.push({ 页签: nm, scrollLeft: s.scrollLeft, 选中项: selTab });
  log(`  点「${nm}」后：scrollLeft=${s.scrollLeft} 选中项=${JSON.stringify(selTab)}`);
}
save();

// ---- 收尾 ----
await p.keyboard.press('Escape'); await p.waitForTimeout(1300);
await p.keyboard.press('Escape'); await p.waitForTimeout(1300);
out.收尾 = { 浮层: await overlays(), 面板在: await p.evaluate(() => !!document.querySelector('[data-testid="canvas-feature-panel"]')),
  选中: await sel(), zoom1: await zoom(), credits: await credits(), status: await status() };
await p.waitForTimeout(1200);
out.收尾.zoom2 = await zoom();
log('\n收尾：', JSON.stringify(out.收尾));
save();
log('\nDONE d');
process.exit(0);
