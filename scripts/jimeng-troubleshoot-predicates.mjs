// 批次 90 · B：把排障页的判据变成**能跑的**。
//
// 批次 90 a 轮的结构性发现：70 条真实排障条目里，
//   A 档（有 testid/aria 定位器，机器能直接复跑）**只有 12**，
//   C 档（只剩自然语言，读者无法自查）**19**。
//
// 🔑 排障页的特殊性：每一条都建立在「**这样就能确认你处在这个问题里**」之上。
//    判据不可核对 ⇒ 读者只能凭感觉对号入座，机器也无法复跑。
//
// ⇒ 本脚本把这些判据**固化成可执行的断言**，并给出**三态**：
//     ✔ 证实 ／ ✘ 证伪 ／ **— 本轮无法验证**
// 🔴 **第三态必须和前两态一样显眼**（批次 87 的纪律：「我测不出来」曾被打成「它不存在」）。
//
// ⛔ 安全边界：只做**只读读数** ＋ 开关**只读浮层**（项目面板 / 节点汇总 / 缩放菜单 /
//    资产库模态 / Agent 抽屉）＋ 选中与取消选中 ＋ ⌘0 适配与缩放归位。
//    **不点任何扣费按钮、不建/删他人节点、不上传、不进导演台、不按 F。**
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import fs from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const out = { at: new Date().toISOString(), rows: [] };
const R = (n) => Math.round(n * 100) / 100;

/**
 * 记一条判据。`expect` 传 null 表示「本轮不判」——它会显示成 —，**不是 ✔**。
 * ⚠️ 自伤：判据可以是 **RegExp 或函数**，而 `JSON.stringify(/x/)` 是 `{}` ——
 *    拿它做相等比较会让**所有正则判据永远判红**（批次 90 自伤①）。
 *    所以这里显式分派：RegExp 走 test，函数走调用，其余走逐字相等。
 */
const same = (expect, actual) => {
  if (expect instanceof RegExp) return expect.test(String(actual));
  if (typeof expect === 'function') return !!expect(actual);
  return JSON.stringify(expect) === JSON.stringify(actual);
};
const rec = (id, sec, expect, actual, note) => {
  const verdict = expect === null || expect === undefined ? '—' : (same(expect, actual) ? '✔' : '✘');
  out.rows.push({ id, sec, expect, actual, verdict, note });
  console.log(`  ${verdict} ${id}  ${sec}`);
  if (verdict !== '✔') console.log(`      期望 ${JSON.stringify(expect)}｜实测 ${JSON.stringify(actual)}${note ? '｜' + note : ''}`);
};

const selCount = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const zoomPct = async () => p.evaluate(() => { const b = document.querySelector('button[aria-label^="Zoom options"]'); return b ? Number((b.getAttribute('aria-label').match(/(\d+)%/) || [])[1]) : null; });
const statusLine = async () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [null])[0]);

out.start = { status: await statusLine(), sel: await selCount(), credits: await credits(), zoom: await zoomPct() };
console.log('起点：', JSON.stringify(out.start));
console.log('\n══ 排障判据自查（三态：✔ 证实 / ✘ 证伪 / — 本轮无法验证）');

// ── P01 状态行逐字 ──
rec('P01', '多条排障共用：状态行是自查入口', /^\d+ nodes?, \d+ edges?, \d+ selected\. Editable\. Room connected\. 已保存\.$/,
  await statusLine());

// ── P02 缩放按钮 aria ──
const zoomAria = await p.evaluate(() => { const b = document.querySelector('button[aria-label^="Zoom options"]'); return b ? b.getAttribute('aria-label') : null; });
// ⚠️ 实测逐字是 **`Zoom options, 60%`（逗号，不是冒号）** —— 判据按实测值写，
//    否则一条永远判红的正则会被当成「页面变了」。
rec('P02', '「点了适配画布，缩放百分比却没变」等', /^Zoom options, \d+%$/, zoomAria);

// ── P03 工具按钮互斥 ──
// 🔴 **自伤：把「当前是选择工具」当成了契约。**
//     实测那个钮的 `aria` 逐轮在 `选择工具` / `抓手工具` 之间变 —— 而且**并不是脚本弄脏的**：
//     批次 90 f 轮证实**只有一个** toggle 钮（`[data-testid="canvas-pointer-tool-toggle"]`，
//     `28×28@16,672`），aria 在两个词之间翻；**抓手态下点节点根本不选中**（`sel` 恒 0，
//     双击也不行），而 **V 键不切工具**（批次 82）⇒ 抓手态的**唯一**退出路径就是点它。
//     真契约是手册那句「aria 即当前模式」，所以判据是「这个钮存在，且 aria 是这两个词之一」；
//     至于此刻是哪个词，**如实记下来**，并由收尾把它归位（否则它会污染下一轮的前置）。
const tools = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  if (!e) return []; const r = e.getBoundingClientRect();
  return [{ aria: e.getAttribute('aria-label'), box: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }]; });
rec('P03', '空白处一拖就选出一片 / 想拖画布却拖不动', (a) => a.length === 1 && ['选择工具', '抓手工具'].includes(a[0].aria), tools,
  `当前模式=${tools[0]?.aria || '（无）'}｜抓手态下点节点不选中，退出只能点这个钮（V 键无效）`);

// ── P04 节点 aria 前缀分组（批次 89 机制）──
const groups = await p.evaluate(() => { const m = {};
  for (const n of document.querySelectorAll('.react-flow__node')) { const a = n.getAttribute('aria-label') || '(无)';
    const k = a.split('：')[0].split(':')[0].trim(); m[k] = (m[k] || 0) + 1; } return m; });
rec('P04', '「@」面板里找不到某类型 / 按类型统计对不上', 'HAS_外部', groups['外部 node'] === 1 ? 'HAS_外部' : 'MISS', JSON.stringify(groups));

// ── P05 Add tags 尺寸公式（批次 89）──
const tagSizes = await p.evaluate(() => { const m = new Map();
  for (const n of document.querySelectorAll('.react-flow__node')) { const t = n.querySelector('[data-testid="flow-node-selected-tag"]'); if (!t) continue;
    const r = t.getBoundingClientRect(); const k = `${Math.round(r.width)}×${Math.round(r.height)}`; m.set(k, (m.get(k) || 0) + 1); }
  return [...m.entries()].sort((a, c) => c[1] - a[1]); });
rec('P05', '节点标题点不动 / 找不到改名入口（标记色那一颗）', 'MULTI_SIZE_NOT_ONE', tagSizes.length >= 2 ? 'MULTI_SIZE_NOT_ONE' : 'SINGLE', JSON.stringify(tagSizes));

// ── P06 / P07 需要选中一个节点 ──
// ⚠️ **不能直接点 DOM 顺序的第一个节点** —— 批次 89 实测 24% 下有 **91/100** 的采样点
//    被别的节点盖住，点中心会选中**别人**。这里用同一招：先扫出
//    「`elementFromPoint` 最上层就是它」的点，再点；找不到就记 VOID。
const sel = await p.evaluate(() => {
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const r = n.getBoundingClientRect();
    // 必须在视口内，否则 elementFromPoint 命中的不是它
    if (!(r.left >= 0 && r.top >= 0 && r.right <= 1280 && r.bottom <= 720)) continue;
    const pts = [];
    for (let fx = 0.2; fx <= 0.8; fx += 0.2) for (let fy = 0.2; fy <= 0.8; fy += 0.2) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const el = document.elementFromPoint(x, y); const top = el && el.closest('.react-flow__node');
      if (top === n) pts.push({ x, y });
    }
    if (pts.length) return { id: n.getAttribute('data-id'), ...pts[Math.floor(pts.length / 2)], candidates: pts.length, method: 'elementFromPoint+viewport' };
  }
  return null;
});
if (sel) {
  await p.mouse.click(sel.x, sel.y); await p.waitForTimeout(1000);
  const s1 = await selCount();
  if (s1 !== '1') { console.log(`  ⚠️ 点选未生效（sel=${s1}）⇒ P06/P07 记 —，不记 ✘`); rec('P06', '选中节点后找不到连线手柄', null, 'VOID', 'sel=' + s1 + ' id=' + sel.id); rec('P07', '⊕ 菜单 / 「视频 / 主体可连」类问题', null, 'VOID', 'sel=' + s1); }
  else {
    const hd = await p.evaluate(() => { const R = (n) => Math.round(n * 100) / 100;   // ⚠️ 自足：Node 侧 R 不可见
      return Array.from(document.querySelectorAll('[data-testid$="-handle"]')).map((e) => { const r = e.getBoundingClientRect();
      return `${e.getAttribute('data-testid')}=${R(r.width)}×${R(r.height)}`; }); });
    rec('P06', '选中节点后找不到连线手柄', 'HAS_HANDLE', hd.length ? 'HAS_HANDLE' : 'NONE', JSON.stringify(hd));
    const plus = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid$="connection-menu-button"]')).map((e) => { const r = e.getBoundingClientRect();
      return `${Math.round(r.width)}×${Math.round(r.height)}`; }));
    rec('P07', '⊕ 菜单里好多项是灰的 / 类型不可连', '36x36', plus.length && plus.every((x) => x === '36×36') ? '36x36' : JSON.stringify(plus), JSON.stringify(plus));
  }
  await p.keyboard.press('Escape'); await p.waitForTimeout(700);
} else { rec('P06', '选中节点后找不到连线手柄', null, 'VOID', '首个节点不在视口内'); rec('P07', '⊕ 菜单里好多项是灰的', null, 'VOID', '首个节点不在视口内'); }

// ── P08 顶栏可点元素与「标记色」 ──
const topbar = await p.evaluate(() => { const bar = document.querySelector('[data-testid="canvas-top-bar"]'); if (!bar) return null;
  return { clickable: Array.from(bar.querySelectorAll('button,a,[role="button"]')).length,
    hasMarkerColor: /标记色/.test(bar.innerText) }; });
rec('P08', '顶栏找不到某入口', 10, topbar?.clickable, JSON.stringify(topbar));

// ── P09 项目面板（开→量→Esc）──
await p.click('button[aria-label="项目"], [data-testid="canvas-project-trigger"]').catch(() => {});
await p.waitForTimeout(1200);
const proj = await p.evaluate(() => { const R = (n) => Math.round(n * 100) / 100;   // ⚠️ 自足：Node 侧 R 在 evaluate 里不可见
  const e = document.querySelector('[data-testid="canvas-project-panel-popover"]'); if (!e) return null;
  const r = e.getBoundingClientRect(); const rows = Array.from(e.querySelectorAll('button')).map((x) => { const q = x.getBoundingClientRect(); return Math.round(q.width); });
  return { box: `${R(r.width)}×${R(r.height)}@${R(r.x)},${R(r.y)}`, nameBtnWidths: [...new Set(rows)] }; });
rec('P09', '「项目」里看不到自己的画布 / 项目列表对不上', '240×280@12,52', proj?.box, JSON.stringify(proj));
await p.keyboard.press('Escape'); await p.waitForTimeout(600);

// ── P10 节点汇总面板高度公式 ──
await p.click('button[aria-label^="Canvas node summary"]'); await p.waitForTimeout(1800);
const sum = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-node-summary-popover"]'); if (!e) return null;
  const r = e.getBoundingClientRect(); const txt = (e.innerText || '').replace(/\s+/g, ' ').trim();
  // ⚠️ 判据要数**类型行**；本页的行没有 aria 属性（批次 90 主发现五），
  //    所以只能按逐字文案数，别用 `[aria-label="Canvas node summary"]` 的个数（永远是 1）。
  const n = (txt.match(/图片 \d+|视频 \d+|文本 \d+|音频 \d+|主体 \d+|时间线 \d+|外部 \d+/g) || []).length;
  return { w: Math.round(r.width), h: Math.round(r.height), n, pred: 4 + 40 * n + 12 + 36, txt: txt.slice(0, 110) }; });
rec('P10', '顶栏「节点 N」与实际对不上', (a) => !!a && a.w === 200 && a.h === a.pred, sum, sum?.txt);
await p.keyboard.press('Escape'); await p.waitForTimeout(600);

// ── P11 Agent 抽屉 ⌘/ —— 必须用**强判据** ──
// 🔴 本批自伤：用 `!!document.querySelector('[data-testid="canvas-feature-sidecar"]')`
//     当「开着」是**错的** —— 折叠态该元素仍在 DOM 里（pe none、0 个可见子元素）。
//     由此一度得出「⌘/ 关不掉」的假结论（批次 84 早已钉过折叠态的三个读数）。
// ⇒ 判据三项一起读：屏上尺寸 / `pointer-events` / **有面积的可见子元素数**。
const sidecar = () => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-feature-sidecar"]');
  if (!e) return { verdict: 'ABSENT' };
  const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
  const vis = Array.from(e.querySelectorAll('*')).filter((n) => { const q = n.getBoundingClientRect(); return q.width > 0 && q.height > 0; }).length;
  const box = `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`;
  const verdict = (box === '400×696@868,12' && cs.pointerEvents === 'auto' && vis > 0) ? 'EXPANDED'
    : (box === '200×348@1068,360' && cs.pointerEvents === 'none' && vis === 0) ? 'COLLAPSED' : `OTHER(${box},pe=${cs.pointerEvents},vis=${vis})`;
  return { box, pe: cs.pointerEvents, visChildren: vis, verdict };
});
const blank = await p.evaluate(() => { const r = document.querySelector('.react-flow__pane') || document.querySelector('.rf__wrapper');
  if (!r) return null; const q = r.getBoundingClientRect(); return { x: Math.round(q.x + 24), y: Math.round(q.y + q.height - 24) }; });
if (blank) { await p.mouse.click(blank.x, blank.y); await p.waitForTimeout(800); }   // 焦点交还画布，排除「焦点在抽屉里」
const s0 = await sidecar();
await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1400); const s1 = await sidecar();
await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1400); const s2 = await sidecar();
rec('P11', '按了快捷键没反应 / Agent 抽屉关不掉', (a) => a.s0 !== a.s1 && a.s1 !== a.s2, { s0: s0.verdict, s1: s1.verdict, s2: s2.verdict },
  '⌘/ 连按两次的状态序列');
// 收尾：回到折叠（不占画布）
for (let k = 0; k < 3; k++) { if ((await sidecar()).verdict !== 'EXPANDED') break; await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1200); }

// ── P12 .sr-only 计数（批次 86）──
const sr = await p.evaluate(() => { const all = document.querySelectorAll('.sr-only');
  const inVp = Array.from(all).filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.left >= 0 && r.top >= 0 && r.right <= 1280 && r.bottom <= 720; }).length;
  return { total: all.length, inViewport: inVp }; });
rec('P12', '（工具向）别用「数 .sr-only 个数」当判据', 'TOTAL_GT_INVP', sr.total > sr.inViewport ? 'TOTAL_GT_INVP' : 'EQUAL', JSON.stringify(sr));

// 收尾：① Agent 抽屉回到折叠；② **把工具恢复成「选择工具」** ——
// ⚠️ 上一版就是漏了这一步，导致下一轮 P03 读到「抓手工具」而判红。
//    **脚本的收尾必须把状态还原到它断言的前置上**，否则它污染的不是画布，是自己。
const restoreTool = async () => {
  // ⚠️ **不能找 `aria-label="选择工具"` 的按钮去点** —— 批次 90 e/f 轮实测：
  //    底部 dock 只有**一个**工具钮 `[data-testid="canvas-pointer-tool-toggle"]`，
  //    它的 aria 在两个词之间**翻**；抓手态下 aria 就是「抓手工具」，
  //    所以「找『选择工具』」必然找不到（上一版恒为 `no-button`）。
  // ⇒ 正确做法：**点那个 toggle 本身**，再回读 aria 确认翻过来了。
  for (let k = 0; k < 3; k++) {
    const t = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
      if (!e) return null; const r = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
    if (!t) return 'no-button';
    if (t.aria === '选择工具') return 'already-选择工具';
    await p.mouse.click(t.x, t.y); await p.waitForTimeout(700);
  }
  const now = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]'); return e ? e.getAttribute('aria-label') : null; });
  return now === '选择工具' ? 'restored' : `failed(${now})`;
};
out.restoreTool = await restoreTool();
console.log('工具归位：', out.restoreTool);
await p.keyboard.press('Escape'); await p.waitForTimeout(500);

out.end = { status: await statusLine(), sel: await selCount(), credits: await credits(), zoom: await zoomPct() };
console.log('\n终态：', JSON.stringify(out.end), '｜积分未变 =', out.start.credits === out.end.credits);
const c = { '✔': 0, '✘': 0, '—': 0 }; for (const r of out.rows) c[r.verdict]++;
out.summary = c;
console.log(`已覆盖的判据：✔ ${c['✔']} ／ ✘ ${c['✘']} ／ — ${c['—']}`);

// ── 覆盖率自报 ──
// 🔴 **「— 0」是假干净**：本脚本只给 12 条排障条目写了判据，
//     另外那几十条**根本没有判据**，于是它们连「无法验证」都没被计数 ——
//     「没写」比「测了但测不出来」更糟，却更不显眼。
//     ⇒ 这里把**全页条目**拉出来逐条对照，明确列出「无判据」的。
//     （条目清单由 jimeng-b90a.mjs 同一套标题解析得出，判据按**标题关键词**匹配，
//       匹配不到的就是「无判据」，宁可多报也不漏报。）
console.log('\n══ 覆盖率自报（全页条目 vs 本脚本判据）');
const md = fs.readFileSync(new URL('../docs/user-manual/jimeng-canvas/90-troubleshooting.md', import.meta.url), 'utf8').split('\n');
const entries = []; let cur = null;
md.forEach((L, i) => { if (/^##\s/.test(L)) cur = null; else if (/^###\s/.test(L)) { cur = { line: i + 1, title: L.replace(/^#+\s*/, '').trim() }; entries.push(cur); } });
// ⚠️ **显式声明，不用模糊匹配** —— 模糊匹配会「看起来覆盖了」却对不上号，
//     而这正是本页最不能出的错：把「没验证过」说成「验证过」。
//     宁可多报无判据。每一项是小节标题里的一段逐字子串。
const COVERS = [
  ['空白处一拖就选出一片', 'P03 工具按钮互斥'],
  ['找不到某个节点', 'P08 顶栏可点元素 ＋ P01 状态行'],
  ['时间线节点很宽', 'P04 按 aria 前缀分组（类型计数对不对）'],
  ['选中时间线节点没有工具条', 'P06 选中后才有手柄/⊕'],
  ['节点标题点不动', 'P05 Add tags 尺寸不是契约（批次 89）'],
  ['画布右侧的节点点不中', 'P06 手柄热区'],
  ['⊕ 菜单里好多项都是灰的', 'P07 ⊕ 屏上恒 36×36 ＋ 选中才有'],
  ['点了提示词反推，右侧弹出了 AI 对话抽屉', 'P11 ⌘/ 是开关（强判据）'],
  ['点了「适配画布」，缩放百分比却没变', 'P02 缩放按钮 aria 逐字'],
  ['画布上明明有两条线，状态行却写', 'P01 状态行逐字 ＋ P10 节点汇总面板公式'],
];
const hit = new Set();
for (const [sub] of COVERS) for (const e of entries) if (e.title.includes(sub)) hit.add(e.line);
out.coverage = { totalEntries: entries.length, covered: hit.size, without: entries.length - hit.size };
console.log(`  全页排障条目 ${entries.length} 条｜本脚本覆盖 ${hit.size} 条｜**无判据 ${out.coverage.without} 条**`);
console.log('  ── 已覆盖（判据可复跑）：');
for (const [sub, why] of COVERS) { const m = entries.filter((e) => e.title.includes(sub));
  for (const e of m) console.log(`     ✔ ${e.line}  ${e.title.slice(0, 46)}  ← ${why}`); }
console.log('  ── 无判据（读者只能凭感觉对号入座，机器也无法复跑）—— 节选前 12 条，完整清单见 pages 文档：');
for (const e of entries.filter((x) => !hit.has(x.line)).slice(0, 12)) console.log(`     — ${e.line}  ${e.title.slice(0, 52)}`);
console.log(`     ……另有 ${out.coverage.without - Math.min(12, out.coverage.without)} 条`);
console.log(`\n  ⚠️ 结论要按三态读：**已覆盖且证实 ${c['✔']}** ／ 已覆盖但证伪 ${c['✘']} ／`);
console.log(`     **无判据 ${out.coverage.without}** —— 无判据**不等于没问题**，它是「还没被验证过」。`);
writeFileSync(new URL('./_tmp-b90b.json', import.meta.url), JSON.stringify(out, null, 1));
console.log('\n已写 scripts/_tmp-b90b.json');
await b.close();
