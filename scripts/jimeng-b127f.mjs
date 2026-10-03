// 批次 127 · f 轮：把 e 轮缺的那一格补上，并完成翻页与 testid 规则。
//
// 🔑 e 轮已定的 2×2 里的 3 格：
//   全部 + 关键词「zzz不存在」+ 0 命中 → 211
//   主体 + 输入框空            + 0 命中 → 604
//   主体 + 关键词「zzz不存在」 + 0 命中 → 211
//   ⇒ 相关量是**「输入框有没有词」**，不是结果条数（主体两格都是 0 条，高度却不同）。
//
// ⚠️ e 轮失败的教训（**判据不成立导致读数取不到**，不是产品行为）：
//   我的 `clickTab` 用**逐字相等**匹配页签，而带计数时页签文字是「全部 76」不是「全部」
//   ⇒ 「全部 + 空」「全部 + 视频」两格直接 `no-tab:全部`。
//   📌 立规：**匹配页签文字要按「去掉计数后的名字」**，不能逐字相等 ——
//   计数是**随筛选变的东西**（批次 124 已证明「只列非零」这类过滤规则），
//   拿它当身份的一部分必然在另一种筛选下失配。
//
// 本轮目标：① 补「有词 + 有命中」那一格（全部 + 「音频」⇒ 68 命中、7 页）
//          ② 翻页（第 1 页 → 第 2 页 → 回第 1 页）
//          ③ 有结果时再验一次「结果行 testid 后缀 = data-id 去掉 node_ 前缀」
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'f' };
const save = () => writeFileSync(new URL('./_tmp-b127f.json', import.meta.url), JSON.stringify(out, null, 1));
const shotDir = new URL('./_tmp-b127a-shots/', import.meta.url);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);

const probe = (label) => p.evaluate((lb) => {
  const panel = document.querySelector('[data-testid="canvas-feature-panel"]');
  if (!panel) return { __err: 'no-panel' };
  const R = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const list = panel.querySelector('[role=tablist]');
  const vp = panel.querySelector('[data-testid="canvas-search-results-viewport"]');
  const nav = panel.querySelector('[aria-label="Search result pages"]');
  return { 情形: lb, 面板: R(panel),
    视口: vp ? { rect: R(vp), scrollHeight: vp.scrollHeight, clientHeight: vp.clientHeight } : null,
    分页: nav ? { rect: R(nav), 逐字: (nav.innerText || '').replace(/\s+/g, ' ').trim() } : null,
    tablist: list ? { scrollWidth: list.scrollWidth, clientWidth: list.clientWidth, scrollLeft: list.scrollLeft } : null,
    页签: Array.from(panel.querySelectorAll('[role=tab]')).map((e) => ({ 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), sel: e.getAttribute('aria-selected') })),
    结果行数: panel.querySelectorAll('[data-testid^="canvas-search-result-node_"]').length,
    结果testid: Array.from(panel.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).map((x) => x.getAttribute('data-testid')),
    输入值: (() => { const i = panel.querySelector('input'); return i ? i.value : null; })(),
    逐字: (panel.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 180) };
}, label);

// 📌 修好的判据：按**去掉计数后的名字**前缀匹配，而不是逐字相等
const clickTabByName = (name) => p.evaluate((nm) => {
  const strip = (s) => (s || '').replace(/\s+/g, '').replace(/\d+$/, '');
  const tabs = Array.from(document.querySelectorAll('[data-testid="canvas-feature-panel"] [role=tab]'));
  const t = tabs.find((e) => strip(e.innerText) === nm) || tabs.find((e) => strip(e.innerText).startsWith(nm));
  if (!t) return { __err: 'no-tab:' + nm, 现有: tabs.map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()) };
  const r = t.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2)
    for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) { const h = document.elementFromPoint(x, y);
      if (h && h.closest('[role=tab]') === t) return { x, y, 文字: (t.innerText || '').replace(/\s+/g, ' ').trim(), 矩形: [r.x, r.y, r.width, r.height].map(Math.round) }; }
  return { __err: 'not-clickable:' + nm, 文字: (t.innerText || '').replace(/\s+/g, ' ').trim(), 矩形: [r.x, r.y, r.width, r.height].map(Math.round) };
}, name);

const setKw = async (kw) => {
  const inp = await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-feature-panel"] input'); if (!i) return null;
    const r = i.getBoundingClientRect(); for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
      const h = document.elementFromPoint(x, y); if (h && (h === i || i.contains(h))) return { x, y }; } return null; });
  if (!inp) return { __err: 'no-input' };
  await p.mouse.click(inp.x, inp.y); await p.waitForTimeout(400);
  await p.keyboard.press('Meta+a'); await p.waitForTimeout(200);
  await p.keyboard.press('Delete'); await p.waitForTimeout(300);
  if (kw) await p.keyboard.type(kw, { delay: 70 });
  await p.waitForTimeout(2000);
  return { ok: true };
};

out.start = { 浮层: await overlays(), 选中: await sel(), zoom: await zoom(), credits: await credits(), status: await status() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);

for (let i = 0; i < 2; i++) { if (await overlays()) { await p.keyboard.press('Escape'); await p.waitForTimeout(1100); } }
const openPt = await p.evaluate(() => { const t = Array.from(document.querySelectorAll('[data-testid="canvas-panel-launcher"]')).find((e) => (e.getAttribute('aria-label') || '') === '搜索');
  if (!t) return null; const r = t.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
    const h = document.elementFromPoint(x, y); if (h && (h === t || t.contains(h))) return { x, y }; } return null; });
if (openPt) { await p.mouse.click(openPt.x, openPt.y); await p.waitForTimeout(2000); }

// ---- ① 补「有词 + 有命中」：全部 + 「音频」 ----
log('\n=== ① 交叉实验收口 ===');
await setKw('');
const tAll = await clickTabByName('全部');
log('  切回「全部」落点：', JSON.stringify(tAll));
if (!tAll.__err) { await p.mouse.click(tAll.x, tAll.y); await p.waitForTimeout(2000); }
out.格1 = await probe('全部 / 输入框空');
log(`  [全部 / 空] 面板=${JSON.stringify(out.格1.面板)} 行数=${out.格1.结果行数} 分页=${JSON.stringify(out.格1.分页?.逐字)} 视口=${out.格1.视口 ? JSON.stringify(out.格1.视口.rect) + ' scrollH=' + out.格1.视口.scrollHeight : '无'}`);
await setKw('音频');
out.格2 = await probe('全部 / 「音频」');
log(`  [全部 / 音频] 面板=${JSON.stringify(out.格2.面板)} 行数=${out.格2.结果行数} 分页=${JSON.stringify(out.格2.分页?.逐字)} 视口=${out.格2.视口 ? JSON.stringify(out.格2.视口.rect) + ' scrollH=' + out.格2.视口.scrollHeight : '无'}`);
log(`      页签：${JSON.stringify(out.格2.页签)}`);
log(`      逐字：${JSON.stringify(out.格2.逐字)}`);
await p.screenshot({ path: new URL('12-keyword-hit.png', shotDir).pathname, clip: { x: 750, y: 40, width: 350, height: 640 } });
save();

// ---- ② 翻页（在「全部」+ 空关键词 = 76 条 ⇒ 7 页） ----
await setKw('');
const tAll2 = await clickTabByName('全部');
if (!tAll2.__err) { await p.mouse.click(tAll2.x, tAll2.y); await p.waitForTimeout(2000); }
out.翻页前 = await probe('翻页前');
log('\n=== ② 翻页 ===\n  翻页前：面板=', JSON.stringify(out.翻页前.面板), '行数=', out.翻页前.结果行数, '分页=', JSON.stringify(out.翻页前.分页?.逐字), 'scrollW=', out.翻页前.tablist?.scrollWidth);
const navBtn = (re) => p.evaluate((r0) => { const n = document.querySelector('[data-testid="canvas-feature-panel"] [aria-label="Search result pages"]');
  if (!n) return { __err: 'no-nav' };
  const btn = Array.from(n.querySelectorAll('button')).find((e) => new RegExp(r0).test(e.getAttribute('aria-label') || ''));
  if (!btn) return { __err: 'no-btn', 全部: Array.from(n.querySelectorAll('button')).map((e) => e.getAttribute('aria-label')) };
  const q = btn.getBoundingClientRect();
  for (let y = Math.ceil(q.y) + 2; y <= q.y + q.height - 2; y += 2) for (let x = Math.ceil(q.x) + 2; x <= q.x + q.width - 2; x += 2) {
    const h = document.elementFromPoint(x, y); if (h && (h === btn || btn.contains(h))) return { x, y, aria: btn.getAttribute('aria-label'), 禁用: btn.hasAttribute('disabled') || btn.getAttribute('aria-disabled') === 'true' }; }
  return { __err: 'no-point' }; }, re);
const nx = await navBtn('下一页');
log('  「前往下一页」：', JSON.stringify(nx));
out.下一页按钮 = nx;
if (!nx.__err) {
  await p.mouse.click(nx.x, nx.y); await p.waitForTimeout(1800);
  out.第2页 = await probe('第2页');
  log('  第 2 页：分页=', JSON.stringify(out.第2页.分页?.逐字), '行数=', out.第2页.结果行数);
  log('  换了一批：', JSON.stringify(out.第2页.结果testid) !== JSON.stringify(out.翻页前.结果testid));
  log('  两页 testid 前三：', JSON.stringify(out.翻页前.结果testid.slice(0, 3)), '→', JSON.stringify(out.第2页.结果testid.slice(0, 3)));
  await p.screenshot({ path: new URL('13-page2.png', shotDir).pathname, clip: { x: 750, y: 40, width: 350, height: 640 } });
  const pv = await navBtn('上一页');
  log('  「前往上一页」：', JSON.stringify(pv));
  if (!pv.__err) { await p.mouse.click(pv.x, pv.y); await p.waitForTimeout(1800);
    const back = await probe('回第1页');
    out.回第1页 = { 分页: back.分页?.逐字, 与翻页前相同: JSON.stringify(back.结果testid) === JSON.stringify(out.翻页前.结果testid) };
    log('  回第 1 页：', JSON.stringify(out.回第1页)); }
}
out.testid规则 = await p.evaluate(() => {
  const rows = Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).map((x) => x.getAttribute('data-testid'));
  const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id'));
  const 命中 = rows.filter((t) => nodes.some((n) => 'canvas-search-result-node_' + n.replace(/^node_/, '') === t));
  return { 行数: rows.length, 命中条数: 命中.length, 前三: rows.slice(0, 3),
    '全部行都能对上(去node_前缀)': rows.length > 0 && 命中.length === rows.length };
});
log('\n=== ③ 结果行 testid ↔ data-id ===\n  ', JSON.stringify(out.testid规则));
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
log('\nDONE f');
process.exit(0);
