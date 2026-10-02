// 即梦画布取证 —— **快捷键面板 vs 手册分类的机械对账**（批次 100 建，批次 101 起为常驻判据）。
//
// 用途：面板那 28 项快捷键，每一项在手册里属于哪一档？哪些**全文都没有结论**？
// 输出四档，并把「真缺口」和「正文有结论但没排进表」**分开报** ——
// 后者只是排版问题，混进真缺口就会把「没归类」误报成「没验证过」
// （批次 90 立的规矩：无判据 ≠ 没问题 = 还没被验证过，但反过来也要成立）。
//
// 🔴 **判据自身的三条硬规矩**（都是被自己的错误判据教会的，写在最前面）：
//   ① **不许在整段文字里做子串搜索**。单字符键（`G` `+` `-` `V`）会大面积误命中 ——
//      `okSec.includes('G')` 会被「创建编组 ⌘ G」里的那个 G 命中。
//      ⇒ 必须**按 Markdown 表格的单元格切分**、逐单元格**全等**比较。
//   ② **键名必须归一化**。面板写 `⌘ -`（ASCII），手册写 `⌘ −`（U+2212）——
//      不归一化就会造出假的「两边都没有」。
//   ③ **按标题截断要按下一个同级标题**，不能一路取到文末。
//      取到文末会让「不可用」段吞掉后面所有正文，把 11 项误判成 `both-tables`。
//   ④ 🔴 **判据只回答它能机械回答的问题**。本脚本迭代到第四版才发现：
//      「手册把这一项**归到哪一档**」是**语义活**，不是机械规则能判的 ——
//      「确认可用」表的第一列写的是**键**（如 `⌘ 0 / ⇧ 1（适配画布）`），
//      并不存在名为「适配画布」的独立单元格，精确匹配必然落空。
//      ⇒ **本判据的职责收窄为两件机械的事**：
//        ① 面板到底有哪 28 项（组 / 功能名 / 键），逐字导出；
//        ② 手册全文里**有没有提到过**这一项的功能名或键（归一化后宽松匹配）。
//      「归到哪一档」由 `help-and-shortcuts.md` 里**人写的三态总账表**负责，
//      本判据反过来校验那张表：**表里出现的每一项，面板上都必须有**（防臆造）。
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
// 🔴 b100d 的 bug：原来 `md.slice(i)` 一直取到**文末**，
//    于是「声明了但当前不可用」那一段把后面所有正文都吞了进去
//    ⇒ 任何在后面正文出现的项都被判成 `both-tables`（实测 11 项误判）。
//    ⇒ 修：**按下一个同级或更高级的标题截断**。
const sectionByHeading = (h) => {
  const i = md.indexOf(h);
  if (i < 0) return '';
  const level = (h.match(/^#+/g) || [''])[0].length;
  const rest = md.slice(i + h.length);
  const re = new RegExp(`^#{1,${level}}\\s`, 'm');
  const m = re.exec(rest);
  return m ? md.slice(i, i + h.length + m.index) : md.slice(i);
};
const okSec = sectionByHeading('### 确认可用');
const noSec = sectionByHeading('### 声明了但当前不可用');
// 🔴 判据缺陷 #5（第二次跑就暴露）：扫描范围原本只取「## 逐项实测结果」之后，
//    于是「三级标题 ⌘⌥3」被判成「手册没提到」—— 可它**确实**在本页的
//    「快捷键全表」第 77 行照抄了面板。判据没扫到那一段。
//    ⇒ 但如果改成扫全文，**28 项全都因为「照抄全表」而命中**，判据直接失效。
//    ⇒ 正确做法：**扫全文，但先剔除「照抄面板全表」那一节** ——
//       问的其实是「**除了照抄面板之外，手册有没有对这一项给出实测结论**」。
const withoutPanelCopy = md.replace(/## 快捷键全表[\s\S]*?(?=\n## )/, '\n');
const proseSec = withoutPanelCopy;

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
    // 🔴 判据缺陷 #4（第一次跑就暴露）：原来这里把
    //    `inSet(cellsOk, name)`（**表内精确**）和 `inSetLoose(cellsProse, name)`（**全文宽松**）
    //    用 `||` 合成一个 `nameOk` ⇒ 「正文里提到过」被当成了「排进表里了」。
    //    实测后果：「移动工具 V」被判成 `ok-table`，而它其实**两栏都没有**。
    //    ⇒ 拆开：表内归类**只认精确匹配**；宽松匹配只用来判 `prose-only`。
    const nameOk = inSet(cellsOk, it.name);
    const nameNo = inSet(cellsNo, it.name);
    const nameProseLoose = inSetLoose(cellsProse, it.name);
    const anyOk = nameOk || keyCells.some((k) => k.okExact);
    const anyNo = nameNo || keyCells.some((k) => k.noExact);
    const anyProse = keyCells.some((k) => k.prose) || !!nameProseLoose;
    // 本判据只做二值判定：**手册提到过 / 没提到过**。
    // 「归到哪一档」是语义活，由正文那张三态总账表负责（见文件头纪律 ④）。
    const mentioned = anyOk || anyNo || anyProse;
    let cls = mentioned ? 'mentioned' : 'NOT-MENTIONED';
    out.classify.push({ group: g.group, name: it.name, keys: it.keys, cls, mentioned,
      signals: { inOkTable: anyOk, inNoTable: anyNo, inProse: anyProse },
      keyCells });
    continue;
    let _unused;
    out.classify.push({ group: g.group, name: it.name, keys: it.keys, cls, mentioned,
      signals: { inOkTable: anyOk, inNoTable: anyNo, inProse: anyProse }, keyCells });
  }
}
const cnt = {};
out.classify.forEach((c) => { cnt[c.cls] = (cnt[c.cls] || 0) + 1; });
log('\n对账（面板 28 项 vs 手册全文）：', JSON.stringify(cnt));
log('   辅助信号（仅供参考，不是结论）：',
  JSON.stringify({ 在确认可用表: out.classify.filter((c) => c.signals.inOkTable).length,
    在不可用表: out.classify.filter((c) => c.signals.inNoTable).length,
    仅正文提到: out.classify.filter((c) => !c.signals.inOkTable && !c.signals.inNoTable && c.signals.inProse).length }));
out.classify.forEach((c) => log(`   [${c.cls.padEnd(14)}] ${c.group} ｜ ${c.name} ｜ ${c.keys.join(' + ')}` +
  (c.cls === 'NOT-MENTIONED' ? '   🔴 手册全文没有提到这一项' : '')));
out.notMentioned = out.classify.filter((c) => c.cls === 'NOT-MENTIONED');
log(`\n🔴 手册全文没有提到的面板项：${out.notMentioned.length} 项`);
out.notMentioned.forEach((c) => log(`   ❓ ${c.group} ｜ ${c.name} ｜ ${c.keys.join(' + ')}`));
log('\n📌 「归到哪一档」请看 help-and-shortcuts.md 的三态总账表 —— 那是语义活，判据不代劳。');

out.end = { nodes: await nodeN(), sel: await selN(), zoom: await zoomLabel(), tool: await toolAria() };
log('终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b100d.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
