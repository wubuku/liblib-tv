// 批次 100 · d 轮：把 c 轮那个**判据不合格**的对账重做一遍。
//
// 🔴 c 轮的判据有**三个缺陷**，每一个都造出了假的结论 —— 这正是批次 90 那条
//    「判据失败信息必须和结果同等显眼」的升级版：
//
//   ① **裸字符串 `includes` 在单字符键上大面积误命中**：
//      `keysInOk = okSec.includes('G')` ⇒ 「创建编组 ⌘ G」里的那个 `G` 让
//      **「宫格视图 G」被判成 `both`**；`okSec.includes('+')` 让
//      「⌘ + 滚轮」里的 `+` 让 **「放大视图 ⌘ +」被判成 `both`**。
//      ⇒ 判据必须**按 Markdown 表格的单元格切分**，逐单元格**全等**比较，
//        不能在整段文字里做子串搜索。
//
//   ② **字符差异**：面板写 `⌘ -`（ASCII 连字符），手册写 `⌘ −`（U+2212 减号）
//      ⇒ 「缩小视图」被误判成「两边都没有」。⇒ 键名必须**归一化**后再比。
//
//   ③ **只扫两张表 ⇒ 漏掉正文专节里的结论**：
//      「预览视图 F」在正文有整整一节、「缩放时间线 ⌘scroll」在正文有专门讨论，
//      它们只是**没排进那两张表**。⇒ 判据必须扫**「逐项实测结果」之后的全部正文**，
//      并把「表里有」与「正文别处有」**分开报** —— 否则会把「排版没归类」误报成「没验证过」。
//
// ⇒ 本轮输出**两栏缺口**：真缺口（全文都没有结论） vs 待归类（有结论但没排进表）。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const MD = new URL('../docs/user-manual/jimeng-canvas/10-tasks/help-and-shortcuts.md', import.meta.url);

const selN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const nodeN = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const zoomLabel = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]');
  return e ? e.getAttribute('aria-label') : null; });
const toolAria = () => p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]');
  return t ? t.getAttribute('aria-label') : null; });

out.start = { nodes: await nodeN(), sel: await selN(), zoom: await zoomLabel(), tool: await toolAria() };
log('起点：', JSON.stringify(out.start));
for (let k = 0; k < 3; k++) { await p.keyboard.press('Escape'); await p.waitForTimeout(600); }
if (await toolAria() !== '选择工具') { await p.click('[data-testid="canvas-pointer-tool-toggle"]'); await p.waitForTimeout(1100); }

// ---- 取面板（真实鼠标点击两段）----
const trig = await p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-user-menu-trigger"]');
  const r = t.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
await p.mouse.move(trig.x, trig.y); await p.waitForTimeout(300);
await p.mouse.click(trig.x, trig.y); await p.waitForTimeout(1500);
const sk = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[role="menuitem"]'))
    .find((x) => x.innerText.replace(/\s+/g, ' ').trim() === '快捷键');
  const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
await p.mouse.move(sk.x, sk.y); await p.waitForTimeout(300);
await p.mouse.click(sk.x, sk.y); await p.waitForTimeout(2000);

out.panel = await p.evaluate(() => {
  const scroll = document.querySelector('[data-testid="shortcut-help-scroll-region"]');
  if (!scroll) return { present: false };
  const r = scroll.getBoundingClientRect();
  const leaves = Array.from(scroll.querySelectorAll('*'))
    .filter((e) => e.children.length === 0 && (e.innerText || '').trim())
    .map((e) => ({ tag: e.tagName, text: e.innerText.replace(/\s+/g, ' ').trim() }));
  const groups = []; let cur = null; let lastSpan = null;
  for (const l of leaves) {
    if (l.tag === 'H3') { cur = { group: l.text, items: [] }; groups.push(cur); lastSpan = null; continue; }
    if (!cur) continue;
    if (l.tag === 'SPAN') { lastSpan = { name: l.text, keys: [] }; cur.items.push(lastSpan); }
    else if (l.tag === 'KBD' && lastSpan) lastSpan.keys.push(l.text);
    else lastSpan = null;
  }
  return { present: true, screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    scrollHeight: scroll.scrollHeight, clientHeight: scroll.clientHeight, leafCount: leaves.length, groups,
    itemCount: groups.reduce((n, g) => n + g.items.length, 0) };
});
log('面板：', out.panel.screen, '| 叶子行', out.panel.leafCount, '| 功能项', out.panel.itemCount);
await p.keyboard.press('Escape');
await p.waitForTimeout(1000);

// ---- 🔑 归一化 ----
const norm = (s) => String(s)
  .replace(/−/g, '-')          // U+2212 → ASCII
  .replace(/–/g, '-').replace(/—/g, '-')
  .replace(/[ 　]/g, ' ')      // NBSP / 全角空格
  .replace(/\s+/g, '')
  .replace(/scroll/g, '滚动')  // ⌘scroll 与「⌘ + 滚轮」是同一个键的两种写法
  .toUpperCase();

out.normExamples = [
  { raw: '⌘ -', norm: norm('⌘ -') },
  { raw: '⌘ −', norm: norm('⌘ −') },
  { raw: '⌘ scroll', norm: norm('⌘ scroll') },
  { raw: '⌘ + 滚轮', norm: norm('⌘ + 滚轮') },
];
log('归一化样例：', JSON.stringify(out.normExamples));

// ---- 切 Markdown 的表格单元格（**不在整段文字里做子串搜索**）----
const md = readFileSync(MD, 'utf8');
const bodyFrom = (h) => { const i = md.indexOf(h); return i < 0 ? '' : md.slice(i); };
const okSec = bodyFrom('### 确认可用');
const noSec = bodyFrom('### 声明了但当前不可用');
const proseSec = bodyFrom('## 逐项实测结果');

const cells = (sec) => {
  const set = new Set();
  // 表格单元格
  for (const line of sec.split('\n')) {
    const t = line.trim();
    if (!t.startsWith('|')) continue;
    for (const c of t.slice(1, t.endsWith('|') ? -1 : undefined).split('|')) {
      const v = c.replace(/[*`]/g, '').replace(/<br\s*\/?>/gi, ' ').trim();
      if (v && !/^:?-{2,}:?$/.test(v)) set.add(v);
    }
  }
  // 行内代码
  for (const m of sec.matchAll(/`([^`]+)`/g)) set.add(m[1].trim());
  return set;
};
const cellsOk = cells(okSec), cellsNo = cells(noSec), cellsProse = cells(proseSec);
out.cellCounts = { ok: cellsOk.size, no: cellsNo.size, prose: cellsProse.size };
log('切出的单元格集合：', JSON.stringify(out.cellCounts));

const inSet = (set, s) => { const n = norm(s); for (const v of set) if (norm(v) === n) return v; return null; };
const inSetLoose = (set, s) => { const n = norm(s); for (const v of set) { const nv = norm(v); if (nv === n || (n.length > 1 && (nv.includes(n) || n.includes(nv)))) return v; } return null; };

out.classify = [];
for (const g of out.panel.groups) {
  for (const it of g.items) {
    const keyCells = it.keys.map((k) => ({
      panel: k,
      okExact: inSet(cellsOk, k), noExact: inSet(cellsNo, k),
      prose: inSetLoose(cellsProse, k) }));
    const nameOk = inSet(cellsOk, it.name) || inSetLoose(cellsProse, it.name);
    const nameNo = inSet(cellsNo, it.name);
    const anyOk = nameOk || keyCells.some((k) => k.okExact);
    const anyNo = nameNo || keyCells.some((k) => k.noExact);
    const anyProse = keyCells.some((k) => k.prose);
    let cls;
    if (anyOk && anyNo) cls = 'both-tables';
    else if (anyOk) cls = 'ok-table';
    else if (anyNo) cls = 'no-table';
    else if (anyProse) cls = 'prose-only';     // 有结论但没排进表
    else cls = 'REAL-GAP';                     // 🔴 真缺口：全文都没有结论
    out.classify.push({ group: g.group, name: it.name, keys: it.keys, cls, keyCells });
  }
}
const cnt = {};
out.classify.forEach((c) => { cnt[c.cls] = (cnt[c.cls] || 0) + 1; });
log('\n对账（改进判据）：', JSON.stringify(cnt));
out.classify.forEach((c) => log(`   [${c.cls.padEnd(11)}] ${c.group} ｜ ${c.name} ｜ ${c.keys.join(' + ')}` +
  (c.cls === 'REAL-GAP' ? '   🔴' : c.cls === 'prose-only' ? '   ⚠️ 正文有结论但没排进表' : '')));
out.realGap = out.classify.filter((c) => c.cls === 'REAL-GAP');
out.proseOnly = out.classify.filter((c) => c.cls === 'prose-only');
log(`\n🔴 真缺口（全文无结论）：${out.realGap.length} 项`);
out.realGap.forEach((c) => log(`   ❓ ${c.group} ｜ ${c.name} ｜ ${c.keys.join(' + ')}`));
log(`⚠️ 正文有结论但没排进两张表：${out.proseOnly.length} 项`);
out.proseOnly.forEach((c) => log(`   ⚠️ ${c.group} ｜ ${c.name} ｜ ${c.keys.join(' + ')}`));

out.end = { nodes: await nodeN(), sel: await selN(), zoom: await zoomLabel(), tool: await toolAria() };
log('终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b100d.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
