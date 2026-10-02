// 批次 100 · c 轮：把快捷键面板的 **28 项**与本手册的分类表做**机械对账**。
//
// 🔑 **本批要解决的正是本页最大的结构问题**：本页把面板全表（28 项）与两栏实测结果
//    （「确认可用」/「声明了但当前不可用」）**并排放着，但两者没有逐项对齐**。
//    后果是：**既不在「确认可用」、也不在「不可用」里的项，读者会默认它能用。**
//    `V`（移动工具）就是典型 —— 面板声明了、批次 82/96/100 三次实测**按了没有任何反应**，
//    而它在两栏里都找不到。
//
// 这一轮先把**缺口量化**：脚本从面板拿 28 项，再从手册两个表里抓行，
// 然后**把「两边都没有」的项单独列出来** —— 就像批次 90 那套
// 「无判据 ≠ 没问题 = 还没被验证过」。
//
// ⚠️ 归类本身是语义活，脚本只负责**把没归类的项显性化**；最终的三态表由人工补。
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

// ---- 打开面板：用户菜单 → 快捷键（**必须真实鼠标点击**，a 轮的 DOM click 打不开）----
const trig = await p.evaluate(() => { const t = document.querySelector('[data-testid="canvas-user-menu-trigger"]');
  if (!t) return null; const r = t.getBoundingClientRect();
  return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
await p.mouse.move(trig.x, trig.y); await p.waitForTimeout(300);
await p.mouse.click(trig.x, trig.y);
await p.waitForTimeout(1500);

out.userMenu = await p.evaluate(() => {
  const m = document.querySelector('[data-testid="canvas-user-menu"]');
  if (!m) return null;
  const r = m.getBoundingClientRect();
  return { screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    role: m.getAttribute('role'),
    items: Array.from(m.querySelectorAll('[role="menuitem"]')).map((e) => { const b = e.getBoundingClientRect();
      return { text: e.innerText.replace(/\s+/g, ' ').trim(), w: Math.round(b.width), h: Math.round(b.height) }; }) }; });
log('用户菜单：', JSON.stringify(out.userMenu));

const sk = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[role="menuitem"]'))
    .find((x) => x.innerText.replace(/\s+/g, ' ').trim() === '快捷键');
  if (!e) return null; const r = e.getBoundingClientRect();
  return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
await p.mouse.move(sk.x, sk.y); await p.waitForTimeout(300);
await p.mouse.click(sk.x, sk.y);
await p.waitForTimeout(2000);

// ---- 把 62 行压成「组 + 功能 + 键」的结构 ----
out.panel = await p.evaluate(() => {
  const scroll = document.querySelector('[data-testid="shortcut-help-scroll-region"]');
  if (!scroll) return { present: false };
  const r = scroll.getBoundingClientRect();
  const leaves = Array.from(scroll.querySelectorAll('*'))
    .filter((e) => e.children.length === 0 && (e.innerText || '').trim())
    .map((e) => ({ tag: e.tagName, text: e.innerText.replace(/\s+/g, ' ').trim() }));
  // H3 = 组标题；SPAN = 功能名；KBD = 键。**SPAN 后面连续的 KBD 全归它**（还原有 ⌘⇧Z 与 ⌘Y 两个）
  const groups = []; let cur = null; let lastSpan = null;
  for (const l of leaves) {
    if (l.tag === 'H3') { cur = { group: l.text, items: [] }; groups.push(cur); lastSpan = null; continue; }
    if (!cur) continue;
    if (l.tag === 'SPAN') { lastSpan = { name: l.text, keys: [] }; cur.items.push(lastSpan); }
    else if (l.tag === 'KBD' && lastSpan) lastSpan.keys.push(l.text);
    else lastSpan = null;
  }
  return { present: true, screen: `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    scrollHeight: scroll.scrollHeight, clientHeight: scroll.clientHeight,
    leafCount: leaves.length, groups,
    itemCount: groups.reduce((n, g) => n + g.items.length, 0),
    keysPerItem: groups.flatMap((g) => g.items.map((i) => `${g.group}|${i.name}|${i.keys.join('+')}`)) };
});
log('面板：', out.panel.present ? `${out.panel.screen} 滚动 ${out.panel.scrollHeight}/可见 ${out.panel.clientHeight}` : '未出现');
log(`   叶子行 ${out.panel.leafCount}、组 ${out.panel.groups.length}、**功能项 ${out.panel.itemCount}**`);
out.panel.keysPerItem?.forEach((k) => log('   ' + k));
await p.keyboard.press('Escape');
await p.waitForTimeout(1000);
out.closed = await p.evaluate(() => document.querySelectorAll('[data-testid="shortcut-help-scroll-region"]').length);

// ---- 机械对账：手册两个表里出现过哪些 ----
const md = readFileSync(MD, 'utf8');
const section = (from, to) => { const i = md.indexOf(from); if (i < 0) return ''; const j = to ? md.indexOf(to, i) : -1;
  return j < 0 ? md.slice(i) : md.slice(i, j); };
const okSec = section('### 确认可用', '### 声明了但当前不可用');
const noSec = section('### 声明了但当前不可用', '#### 🔑');
out.mdSections = { okLen: okSec.length, noLen: noSec.length };
log(`手册：确认可用段 ${okSec.length} 字、不可用段 ${noSec.length} 字`);

out.classify = (out.panel.keysPerItem ?? []).map((line) => {
  const [group, name, keys] = line.split('|');
  // 在两段里找「功能名」或「键」是否出现
  const nameInOk = okSec.includes(name);
  const keysInOk = keys.split('+').some((k) => okSec.includes(k));
  const nameInNo = noSec.includes(name);
  const keysInNo = keys.split('+').some((k) => noSec.includes(k));
  let cls = 'unclassified';
  if ((nameInOk || keysInOk) && (nameInNo || keysInNo)) cls = 'both';
  else if (nameInOk || keysInOk) cls = 'ok';
  else if (nameInNo || keysInNo) cls = 'disabled-with-hint';
  return { group, name, keys, cls };
});
const cnt = {};
out.classify.forEach((c) => { cnt[c.cls] = (cnt[c.cls] || 0) + 1; });
log('对账结果：', JSON.stringify(cnt));
log('逐项：');
out.classify.forEach((c) => log(`   [${c.cls.padEnd(19)}] ${c.group} ｜ ${c.name} ｜ ${c.keys}`));
out.unclassified = out.classify.filter((c) => c.cls === 'unclassified');
log(`\n⚠️ 既不在「确认可用」也不在「声明了但当前不可用」里的项：${out.unclassified.length} 项`);
out.unclassified.forEach((c) => log(`   ❓ ${c.group} ｜ ${c.name} ｜ ${c.keys}`));

out.end = { nodes: await nodeN(), sel: await selN(), zoom: await zoomLabel(), tool: await toolAria() };
log('终态：', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b100c.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
