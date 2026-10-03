// 批次 127 · e 轮：解决 d 轮暴露的**读数矛盾**，并把翻页补上。
//
// 🔴 d 轮的矛盾（不能靠平均、必须靠能区分预测的条件来判）：
//   同样是「0 条结果」，面板高度读出两个值 ——
//     「主体」页签、输入框为空、0 条  →  `320×604`，且 `canvas-search-results-viewport` **不存在**
//     「主体」页签、输入框有词、0 条  →  `320×211`
//   假设 A：**高度只跟结果条数有关**（0 条 ⇒ 211）
//     ⇒ 预测：「主体 + 无关键词 + 0 条」也该是 211。🔴 d 轮读到 604 ⇒ **被否**。
//   假设 B：**高度跟「输入框有没有词」有关**（有词 ⇒ 走另一条空态分支 ⇒ 211）
//     ⇒ 预测：「全部」页签 + 有词但**有命中**（如「视频」2 条）时，高度随条数走还是也变 211？
//        若仍是 604 ⇒ 与条数无关，B 成立；若也变 211 ⇒ 真正相关量是别的。
//   假设 C：**高度是内容自适应 + 过渡动画未落定**
//     ⇒ 预测：拉长等待后读数会变。d 轮只等了 1300ms。
//   ⇒ 设计：把三种条件交叉各测一遍，且**每次都等足 2000ms**，并同时记
//     「视口在不在」「逐字」「页签带不带计数」「tablist 的 scrollWidth」。
//
// 📌 另两件 d 轮没测成的：
//   · **面板记住了上次选的页签**（d 轮打开时直接停在「其他 1」）—— 这本身是个结论，
//     但它导致分页器不存在 ⇒ 翻页必须**先显式切回「全部」**再测。
//   · 结果行 testid 后缀与 `data-id` 的关系（d 轮那一步恰好 0 条结果 ⇒ 读到空数组）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'e' };
const save = () => writeFileSync(new URL('./_tmp-b127e.json', import.meta.url), JSON.stringify(out, null, 1));
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
  const tp = panel.querySelector('[role=tabpanel]');
  return { 情形: lb, 面板: R(panel),
    tabpanel: tp ? R(tp) : null, 视口: vp ? { rect: R(vp), scrollHeight: vp.scrollHeight } : null,
    分页NAV: nav ? { rect: R(nav), 逐字: (nav.innerText || '').replace(/\s+/g, ' ').trim() } : null,
    渐隐遮罩: (() => { const m = panel.querySelector('[data-testid="canvas-search-tab-mask-next"]'); return m ? R(m) : null; })(),
    tablist: list ? { rect: R(list), scrollWidth: list.scrollWidth, clientWidth: list.clientWidth, scrollLeft: list.scrollLeft } : null,
    页签: Array.from(panel.querySelectorAll('[role=tab]')).map((e) => ({ 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), sel: e.getAttribute('aria-selected') })),
    结果行数: panel.querySelectorAll('[data-testid^="canvas-search-result-node_"]').length,
    结果testid: Array.from(panel.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).slice(0, 3).map((x) => x.getAttribute('data-testid')),
    输入值: (() => { const i = panel.querySelector('input'); return i ? i.value : null; })(),
    逐字: (panel.innerText || '').replace(/\s+/g, ' ').trim() };
}, label);

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

// 关掉任何残留面板，开一个新的
for (let i = 0; i < 2; i++) { if (await overlays()) { await p.keyboard.press('Escape'); await p.waitForTimeout(1100); } }
const openPt = await p.evaluate(() => { const t = Array.from(document.querySelectorAll('[data-testid="canvas-panel-launcher"]')).find((e) => (e.getAttribute('aria-label') || '') === '搜索');
  if (!t) return null; const r = t.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
    const h = document.elementFromPoint(x, y); if (h && (h === t || t.contains(h))) return { x, y }; } return null; });
if (openPt) { await p.mouse.click(openPt.x, openPt.y); await p.waitForTimeout(2000); }

// ---- 交叉实验：{页签: 全部/主体} × {输入框: 空/有词} ----
out.交叉 = [];
const setKeyword = async (kw) => {
  const inp = await p.evaluate(() => { const i = document.querySelector('[data-testid="canvas-feature-panel"] input'); if (!i) return null;
    const r = i.getBoundingClientRect(); for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
      const h = document.elementFromPoint(x, y); if (h && (h === i || i.contains(h))) return { x, y }; } return null; });
  if (!inp) return { __err: 'no-input' };
  await p.mouse.click(inp.x, inp.y); await p.waitForTimeout(400);
  await p.keyboard.press('Meta+a'); await p.waitForTimeout(180);
  await p.keyboard.press('Delete'); await p.waitForTimeout(300);
  if (kw) { await p.keyboard.type(kw, { delay: 70 }); }
  await p.waitForTimeout(2000);
  return { ok: true, kw };
};

const goTab = async (label, kw) => {
  await setKeyword(kw || '');
  const t = await clickTab(label);
  if (t.__err) { out.交叉.push({ 目标: label + ' / ' + (kw || '(空)'), 落点: t }); log(`  [${label} / ${kw || '空'}] ⛔ ${t.__err}`); return; }
  await p.mouse.click(t.x, t.y);
  await p.waitForTimeout(2000);
  const r = await probe(`${label} / 输入框${kw ? '「' + kw + '」' : '空'}`);
  out.交叉.push({ 目标: label + ' / ' + (kw || '(空)'), 落点: t, 读数: r });
  log(`  [${label} / ${kw || '空'}] 面板=${JSON.stringify(r.面板)} 行数=${r.结果行数} 视口=${r.视口 ? JSON.stringify(r.视口.rect) : '无'} 分页=${r.分页NAV ? JSON.stringify(r.分页NAV.逐字) : '无'} 遮罩=${JSON.stringify(r.渐隐遮罩)} scrollW=${r.tablist ? r.tablist.scrollWidth : '?'}`);
  log(`      页签：${JSON.stringify(r.页签)}`);
};

log('\n=== 交叉实验：高度到底跟什么有关 ===');
await goTab('全部', '');
await goTab('全部', '视频');   // 有词、有命中
await goTab('全部', 'zzz不存在'); // 有词、0 命中
await goTab('全部', '');
await goTab('主体', '');      // 无词、0 命中
await goTab('主体', 'zzz不存在'); // 有词、0 命中（与上一格对照：只多了「有没有词」）
out.高度取值 = [...new Set(out.交叉.filter((x) => x.读数).map((x) => JSON.stringify(x.读数.面板)))];
log('  面板矩形出现过的取值：', out.高度取值.length, JSON.stringify(out.高度取值));
save();
await p.screenshot({ path: new URL('10-subject-empty-604.png', shotDir).pathname, clip: { x: 750, y: 40, width: 350, height: 640 } });

// ---- 翻页（先显式回到「全部」且清空关键词） ----
await setKeyword('');
const tAll = await clickTab('全部');
log('\n=== 翻页 ===\n  切回「全部」落点：', JSON.stringify(tAll));
if (!tAll.__err) { await p.mouse.click(tAll.x, tAll.y); await p.waitForTimeout(2000); }
out.翻页前 = await probe('翻页前');
log('  翻页前：面板=', JSON.stringify(out.翻页前.面板), '行数=', out.翻页前.结果行数, '分页=', JSON.stringify(out.翻页前.分页NAV));
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
  log('  第 2 页：分页=', JSON.stringify(out.第2页.分页NAV?.逐字), '行数=', out.第2页.结果行数, 'testid=', JSON.stringify(out.第2页.结果testid));
  log('  换了一批：', JSON.stringify(out.第2页.结果testid) !== JSON.stringify(out.翻页前.结果testid));
  await p.screenshot({ path: new URL('11-page2.png', shotDir).pathname, clip: { x: 750, y: 40, width: 350, height: 640 } });
  const pv = await navBtn('上一页');
  log('  「前往上一页」：', JSON.stringify(pv));
  out.上一页按钮 = pv;
  if (!pv.__err) { await p.mouse.click(pv.x, pv.y); await p.waitForTimeout(1800);
    const back = await probe('回到第1页');
    out.回第1页 = { 分页: back.分页NAV?.逐字, testid: back.结果testid, 与翻页前相同: JSON.stringify(back.结果testid) === JSON.stringify(out.翻页前.结果testid) };
    log('  回到第 1 页：', JSON.stringify(out.回第1页)); }
}
out.testid对照2 = await p.evaluate(() => {
  const rows = Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).map((x) => x.getAttribute('data-testid'));
  const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id'));
  return { 行数: rows.length, 前三: rows.slice(0, 3),
    '全部行都能对上(去node_前缀)': rows.every((t) => nodes.some((n) => 'canvas-search-result-node_' + n.replace(/^node_/, '') === t)),
    对上的条数: rows.filter((t) => nodes.some((n) => 'canvas-search-result-node_' + n.replace(/^node_/, '') === t)).length };
});
log('  结果行 testid ↔ 节点 data-id：', JSON.stringify(out.testid对照2));
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
log('\nDONE e');
process.exit(0);
