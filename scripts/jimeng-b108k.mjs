// 批次 108 · k 轮：删掉**最后一个**成员，取真正的 **0 成员**态。
//
// j 轮的 `if (!stillThere) break;` 让它只走到 **1 成员**就停了，
// 而我把那一档的标签写成了「B 态：0 个成员」—— **标签与事实不符，差一步**。
// ⇒ 补这一轮，把 0 成员真的取到，并且**不继承 j 轮那个错标签**。
//
// 🔴 本轮顺手修掉一个判据：j 轮用 `/(\d+) members/` 取成员数，
//   删掉一个成员后组文本变成 **`编组 1 Group 编组 1, 1 member. Not selected.`**
//   —— **单数是 `member` 不带 s**，正则返回 `null`。
//   ⇒ 📌 成员数要按 `(\d+) members?` 取；**而且这本身是一条可写进手册的读数**：
//   **组会区分单复数**（`1 member.` / `2 members.`），可以当「组里还剩几个」的判据。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';
import { readFileSync } from 'node:fs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString() };
out.groupId = 'node_0ctj8mcr3m';
out.last = 'node_8vwsfmqc24';
const G = out.groupId;
const save = () => writeFileSync(new URL('./_tmp-b108k.json', import.meta.url), JSON.stringify(out, null, 1));

const status = () => p.evaluate(() => { const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1] }; });
// 🔴 修好的成员数判据：单复数都吃
const groupInfo = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  const t = n.querySelector('[data-testid="group-title-chrome"]');
  const tr = t ? t.getBoundingClientRect() : null;
  const txt = n.innerText.replace(/\s+/g, ' ').trim();
  return { sel: n.classList.contains('selected'), text: txt.slice(0, 110),
    members: (txt.match(/(\d+) members?/) || [])[1] ?? null,
    memberPhrase: (txt.match(/(\d+) members?\.?/) || [])[0] ?? null,
    title: tr ? { cx: Math.round(tr.x + tr.width / 2), cy: Math.round(tr.y + tr.height / 2) } : null };
}, G);
const readBar = () => p.evaluate(() => {
  const bar = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
    .find((e) => { const r = e.getBoundingClientRect(); return r.width > 60 && r.y > 0 && r.y < 400 && getComputedStyle(e).visibility !== 'hidden'; });
  if (!bar) return null;
  const r = bar.getBoundingClientRect();
  return { w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y),
    items: Array.from(bar.querySelectorAll('button,[role=button]')).map((e) => { const q = e.getBoundingClientRect();
      return { t: (e.innerText || '').trim(), a: e.getAttribute('aria-label'), w: Math.round(q.width), h: Math.round(q.height),
        cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2) }; }) };
});
const readPalette = () => p.evaluate(() => {
  const host = document.querySelector('[data-testid="selection-context-toolbar-popup-host"]');
  if (!host) return { found: false };
  const hr = host.getBoundingClientRect();
  const sw = Array.from(host.querySelectorAll('.size-canvas-color-choice-swatch, [class*=color-choice-swatch]'))
    .map((e) => { const q = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      let label = null; let nn = e.parentElement;
      for (let k = 0; k < 3 && nn && !label; k++, nn = nn.parentElement) { const s = nn.querySelector('.sr-only'); if (s && s !== e) label = (s.innerText || '').trim(); }
      return { label, w: Math.round(q.width), h: Math.round(q.height), x: Math.round(q.x), y: Math.round(q.y),
        bg: cs.backgroundColor, br: cs.borderRadius, bdr: cs.borderColor,
        cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2) }; });
  return { found: true, hostBox: `${Math.round(hr.x)},${Math.round(hr.y)} ${Math.round(hr.width)}×${Math.round(hr.height)}`,
    hostText: (host.innerText || '').replace(/\s+/g, ' ').trim(), n: sw.length, swatches: sw };
});

log('起点：', JSON.stringify(await status()));
out.g0 = await groupInfo();
log('组（起点）：', JSON.stringify(out.g0));

// 删最后一个成员
log(`\n>>> 删最后一个成员 ${out.last}`);
await p.mouse.click(8, 300); await p.waitForTimeout(1200);
const spot = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect(); const c = [];
  for (let y = Math.ceil(r.y) + 2; y < r.y + r.height - 2; y += 4)
    for (let x = Math.ceil(r.x) + 2; x < r.x + r.width - 2; x += 4) {
      if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
      const el = document.elementFromPoint(x, y);
      if (el && (el === n || n.contains(el))) c.push({ x, y });
    }
  return { total: c.length, sample: c.slice(0, 4) };
}, out.last);
log('  落点：', JSON.stringify({ total: spot.total }));
if (!spot.total) { log('  🔴 无落点，停止'); save(); await b.close(); process.exit(1); }
const pt = spot.sample[Math.floor(spot.sample.length / 2)];
await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(500);
await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1500);
const selNow = await p.evaluate((i) => { const e = document.querySelector(`.react-flow__node[data-id="${i}"]`); return e ? e.classList.contains('selected') : null; }, out.last);
log('  点击后 selected =', selNow);
if (!selNow) { log('  🔴 没选中，停止'); save(); await b.close(); process.exit(1); }
await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(450);
await p.mouse.down({ button: 'right' }); await p.waitForTimeout(300); await p.mouse.up({ button: 'right' });
await p.waitForTimeout(1400);
const del = await p.evaluate(() => {
  const m = Array.from(document.querySelectorAll('div,ul,section')).find((x) => { const q = x.getBoundingClientRect();
    return q.width > 60 && q.width < 600 && q.height > 60 && getComputedStyle(x).visibility !== 'hidden'
      && (x.innerText || '').replace(/\s+/g, ' ').trim().startsWith('复制 ⌘ C'); });
  if (!m) return null;
  const btn = Array.from(m.querySelectorAll('button,[role=menuitem]')).find((e) => /^删除/.test(e.innerText.trim()));
  if (!btn) return null;
  const q = btn.getBoundingClientRect();
  return { x: Math.round(q.x + q.width / 2), y: Math.round(q.y + q.height / 2) };
});
log('  删除项：', JSON.stringify(del));
if (!del) { log('  🔴 没有删除项，停止'); save(); await b.close(); process.exit(1); }
await p.mouse.move(del.x, del.y); await p.waitForTimeout(400);
await p.mouse.click(del.x, del.y); await p.waitForTimeout(2200);
out.afterDel = await status();
out.memberGone = !(await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), out.last));
log('  成员还在吗 =', out.memberGone ? '否 ✅' : '是 🔴', '｜状态行', JSON.stringify(out.afterDel));
out.g1 = await groupInfo();
log('  组现在：', JSON.stringify(out.g1));
save();

// 0 成员态：选中组 → 读工具条 → 点背景色 → 读色板
log('\n########## 0 成员态 ##########');
let g = out.g1;
if (!g.sel && g.title) {
  await p.mouse.move(g.title.cx, g.title.cy); await p.waitForTimeout(550);
  await p.mouse.click(g.title.cx, g.title.cy); await p.waitForTimeout(1700);
  g = await groupInfo();
}
out.gZero = g;
out.statusZero = await status();
log('组：', JSON.stringify(g), '｜状态行', JSON.stringify(out.statusZero));
out.barZero = await readBar();
log('工具条（0 成员）：', JSON.stringify(out.barZero));
await p.screenshot({ path: '/tmp/b108-k-0-选中零成员组.png', clip: { x: 430, y: 150, width: 560, height: 400 } });
const bg = out.barZero && out.barZero.items.find((i) => /背景色/.test(i.t));
out.bgBtnZero = bg || null;
log('工具条里有没有「背景色」=', bg ? '✅ 有' : '🔴 没有');
if (bg) {
  await p.mouse.move(bg.cx, bg.cy); await p.waitForTimeout(650);
  await p.mouse.click(bg.cx, bg.cy); await p.waitForTimeout(2000);
  out.paletteZero = await readPalette();
  log('色板（0 成员）：', JSON.stringify(out.paletteZero, null, 1));
  await p.screenshot({ path: '/tmp/b108-k-1-零成员色板.png', clip: { x: 430, y: 150, width: 560, height: 400 } });
} else {
  out.paletteZero = { found: false, why: '工具条里没有「背景色」项' };
  log('色板：无法取（工具条里没有「背景色」这一项）');
}
await p.keyboard.press('Escape'); await p.waitForTimeout(1000);
save();

// 与 j 轮的两成员态对账
const prev = readFileSync(new URL('./_tmp-b108j.json', import.meta.url), 'utf8');
const j = JSON.parse(prev);
out.compare = {
  twoMembers: { bar: (j.barA.items || []).map((i) => i.t || i.a), palette: (j.paletteA.swatches || []).map((s) => `${s.label}|${s.bg}|${s.w}x${s.h}`) },
  oneMember: { bar: (j.barB.items || []).map((i) => i.t || i.a), palette: (j.paletteB.swatches || []).map((s) => `${s.label}|${s.bg}|${s.w}x${s.h}`) },
  zeroMember: { bar: (out.barZero && out.barZero.items || []).map((i) => i.t || i.a),
    palette: (out.paletteZero.swatches || []).map((s) => `${s.label}|${s.bg}|${s.w}x${s.h}`) },
};
log('\n════ 三态对账 ════');
log('2 成员 工具条：', JSON.stringify(out.compare.twoMembers.bar));
log('1 成员 工具条：', JSON.stringify(out.compare.oneMember.bar));
log('0 成员 工具条：', JSON.stringify(out.compare.zeroMember.bar));
log('2 成员 色板：', JSON.stringify(out.compare.twoMembers.palette));
log('1 成员 色板：', JSON.stringify(out.compare.oneMember.palette));
log('0 成员 色板：', JSON.stringify(out.compare.zeroMember.palette));
const sig = (a) => JSON.stringify(a);
out.samePalette = sig(out.compare.twoMembers.palette) === sig(out.compare.oneMember.palette)
  && sig(out.compare.oneMember.palette) === sig(out.compare.zeroMember.palette);
log('三态色板逐字相同 =', out.samePalette ? '✅' : '❌ 不同');
out.sameBar = sig(out.compare.twoMembers.bar) === sig(out.compare.oneMember.bar)
  && sig(out.compare.oneMember.bar) === sig(out.compare.zeroMember.bar);
log('三态工具条逐字相同 =', out.sameBar ? '✅' : '❌ 不同');
save();
log('\n已落盘');
await b.close();
