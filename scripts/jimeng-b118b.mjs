// 批次 118 · b 轮：确认「主体节点**没有**浮动工具条」—— 换 class 复扫 + 阳性对照。
//
// a 轮读数：主体节点选中时，`[data-testid="node-toolbar"]` 只有**两个零高度**元素
//   （宽度 `0` 和 `211`），**可见工具条 0 个** ⇒ 疑似「没有工具条」。
//   零高度元素的宽度随缩放变：`40% → 141`、`60% → 211`、`100% → 352`
//   ⇒ 宽度 = 节点的 canvas 宽 `352`（352×0.4=140.8≈141、×0.6=211.2≈211、×1=352），
//      与批次 85 在视频节点上记的「宽度等于节点屏上宽、高度恒 0」**同构**。
//
// 🔴 但 a 轮有个**结构性漏洞**（本项目老坑的镜像）：
//   它**只按 testid 找**。而 `use-node-toolbar.md:46` 明写
//   「两者都用 **`.react-flow__node-toolbar`** 作为外层类名」
//   ⇒ **testid 与 class 是两个不同的宿主**，只取一个可能整个漏掉。
//   📌 立规：**判「某个 UI 元素在不在」，所有可能的宿主（testid / class / role /
//   祖先结构）都要扫一遍**；只取一个来源得出的「没有」，在补扫之前不算结论。
//
// 本轮做两件事：
//   ① 按 **class** `.react-flow__node-toolbar` + 常见 role/结构**复扫**主体节点
//   ② 造一个**文本节点**当**阳性对照**（手册已记它有 `背景色`／`全屏`／`下载` 三项）
//      —— 判据若在文本节点上打不中，说明判据本身坏了，不是「主体节点没有」
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const SUBJECT = process.env.SELF_ID;
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b', subject: SUBJECT };
const save = () => writeFileSync(new URL('./_tmp-b118b.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });

// 🔑 **多宿主复扫**：同一类 UI 可能挂在 testid / class / role / 结构位置上，
//    一次全读，并**逐个宿主分别报数**（不合并成「工具条数」）。
const sweepAll = (lbl) => p.evaluate((l) => {
  const r = (e) => { const q = e.getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; };
  const desc = (e) => ({ rect: r(e), text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 90),
    svgs: e.querySelectorAll('svg').length,
    btns: Array.from(e.querySelectorAll('button,[role=button]')).map((x) => x.getAttribute('aria-label')).filter(Boolean) });
  const hosts = {
    'testid=node-toolbar': Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')),
    'class=react-flow__node-toolbar': Array.from(document.querySelectorAll('.react-flow__node-toolbar')),
    'class*=node-toolbar': Array.from(document.querySelectorAll('[class*="node-toolbar"]')),
    'testid*=toolbar': Array.from(document.querySelectorAll('[data-testid*="toolbar" i]')),
    'testid=text-editor-toolbar': Array.from(document.querySelectorAll('[data-testid="text-editor-toolbar"]')),
    'role=toolbar': Array.from(document.querySelectorAll('[role="toolbar"]')),
    'class*=floating': Array.from(document.querySelectorAll('[class*="floating" i]')),
  };
  const o = { at: Date.now(), lbl: l, hosts: {} };
  for (const [k, els] of Object.entries(hosts)) {
    o.hosts[k] = { n: els.length, visible: els.filter((e) => { const q = e.getBoundingClientRect(); return q.width > 1 && q.height > 1; }).map(desc) };
  }
  // 独立于上面几类：**浮在节点上方、与节点同宽或更窄、且不含节点自身内容**的元素
  o.candidates = [];
  for (const sel of ['body > div', '.react-flow__renderer > div']) for (const e of document.querySelectorAll(sel)) {
    const q = e.getBoundingClientRect(); if (q.width < 40 || q.height < 20) continue;
    const cs = getComputedStyle(e);
    if (!/absolute|fixed/.test(cs.position)) continue;
    const btns = Array.from(e.querySelectorAll('button,[role=button]')).map((x) => x.getAttribute('aria-label')).filter(Boolean);
    if (!btns.length) continue;
    o.candidates.push({ sel, rect: r(e), z: cs.zIndex, pos: cs.position, cls: (e.getAttribute('class') || '').toString().slice(0, 40),
      tid: e.getAttribute('data-testid'), btns, nSvgs: e.querySelectorAll('svg').length });
  }
  return o;
}, lbl);

const selNode = async (id) => { const pt = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  if (n.classList.contains('selected')) return { already: true };
  const q = n.getBoundingClientRect();
  for (let y = Math.ceil(q.y) + 6; y < q.y + q.height - 6; y += 5)
    for (let x = Math.ceil(q.x) + 6; x < q.x + q.width - 6; x += 5) { if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
    const el = document.elementFromPoint(x, y); if (el && (el === n || n.contains(el))) return { x, y }; }
  return { __err: 'unreachable' }; }, id);
  if (pt.x) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1800); } return pt; };

out.zoom0 = await zoom();
log('起点 zoom：', out.zoom0, '｜积分：', await credits());

// ---- ① 主体节点（已知：testid 口径下没有可见工具条） ----
log('\n########## 主体节点（多宿主复扫）##########');
out.selSubject = await selNode(SUBJECT);
log('选中：', JSON.stringify(out.selSubject));
out.subject = await sweepAll('subject-selected');
log('\n逐个宿主：');
for (const [k, v] of Object.entries(out.subject.hosts)) {
  log(`  ${k.padEnd(34)} 元素 ${String(v.n).padStart(2)} 个｜可见 ${v.visible.length} 个`);
  v.visible.forEach((d) => log(`      ${JSON.stringify(d.rect)}｜${JSON.stringify(d.text)}｜按钮 ${JSON.stringify(d.btns)}`));
}
log('\n浮层候选（absolute/fixed 且含按钮）：');
out.subject.candidates.forEach((c) => log('   ' + JSON.stringify(c)));
save();

// ---- ② 文本节点作**阳性对照** ----
log('\n########## 文本节点（阳性对照）##########');
const reloc = await p.evaluate(() => {
  const bad = (x, y) => { const el = document.elementFromPoint(x, y);
    if (!el || el.closest('.react-flow__node')) return true;
    if (x < 200 || y < 60 || y > 630 || x > 1120) return true;
    if (el.closest('button,[role=button],input,a,[contenteditable]')) return true;
    if (el.closest('[role="menu"],[data-testid="node-toolbar"],[class*="node-toolbar"]')) return true; return false; };
  for (let y = 280; y < 630; y += 12) for (let x = 260; x < 1100; x += 12) if (!bad(x, y)) return { x, y }; return null; });
if (reloc) { await p.mouse.click(reloc.x, reloc.y); await p.waitForTimeout(1400); }
const idsBefore = await allIds();
const blank = await p.evaluate(() => {
  const bad = (x, y) => { const el = document.elementFromPoint(x, y);
    if (!el || el.closest('.react-flow__node')) return true;
    if (x < 200 || y < 60 || y > 630 || x > 1120) return true;
    if (el.closest('button,[role=button],input,a')) return true; return false; };
  for (let y = 280; y < 630; y += 12) for (let x = 260; x < 1100; x += 12) if (!bad(x, y)) return [x, y]; return null; });
log('空白落点：', JSON.stringify(blank));
if (!blank) { log('🔴 中止'); await b.close(); process.exit(3); }
await p.mouse.move(blank[0], blank[1]); await p.waitForTimeout(400);
await p.mouse.down({ button: 'right' }); await p.waitForTimeout(300); await p.mouse.up({ button: 'right' });
await p.waitForTimeout(1300);
const nj = await p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]'))
  for (const it of m.querySelectorAll('[role=menuitem]')) {
    if ((it.innerText || '').trim().startsWith('新建节点')) { const r = it.getBoundingClientRect();
      return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; } } return null; });
await p.mouse.move(nj.x, nj.y); await p.waitForTimeout(500);
await p.mouse.move(nj.x + 3, nj.y); await p.waitForTimeout(1500);
const target = await p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]')) {
    if (getComputedStyle(m).visibility === 'hidden') continue;
    for (const it of m.querySelectorAll('[role=menuitem]')) { if ((it.innerText || '').trim() !== '文本') continue;
      const r = it.getBoundingClientRect(); if (r.width < 1) continue;
      const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
      const h = document.elementFromPoint(cx, cy); if (!h || !(h === it || it.contains(h))) continue;
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; } }
  return { __err: 'no-clickable' }; });
if (target.__err) { log('⛔ 中止'); await b.close(); process.exit(3); }
await p.mouse.click(target.rect[0] + target.rect[2] / 2, target.rect[1] + target.rect[3] / 2);
let TXT = null, guard = null;
for (let k = 1; k <= 16; k++) { await p.waitForTimeout(1200);
  const ids = await allIds(); const diff = ids.filter((id) => !idsBefore.includes(id));
  if (diff.length === 1) { const sel = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
    guard = { diff, sel, ok: sel.includes(diff[0]) }; if (guard.ok) { TXT = diff[0]; break; } }
  else if (diff.length > 1) { log(`  ⛔ 差集超过一个：${JSON.stringify(diff)}`); break; } }
out.guardText = guard; out.text = TXT;
log(`护栏②：${JSON.stringify(guard)} ⇒ ${TXT ? '✅ ' + TXT : '🔴'}`);
save();
if (!TXT) { log('🔴 中止'); await b.close(); process.exit(3); }
await p.waitForTimeout(1600);
out.textSweep = await sweepAll('text-selected');
log('\n逐个宿主：');
for (const [k, v] of Object.entries(out.textSweep.hosts)) {
  log(`  ${k.padEnd(34)} 元素 ${String(v.n).padStart(2)} 个｜可见 ${v.visible.length} 个`);
  v.visible.forEach((d) => log(`      ${JSON.stringify(d.rect)}｜${JSON.stringify(d.text)}｜按钮 ${JSON.stringify(d.btns)}`));
}
log('\n浮层候选：');
out.textSweep.candidates.forEach((c) => log('   ' + JSON.stringify(c)));

// ---- 对照判定 ----
const vis = (sw, k) => sw.hosts[k] ? sw.hosts[k].visible.length : 0;
out.compare = {};
for (const k of Object.keys(out.subject.hosts)) out.compare[k] = { 主体节点可见: vis(out.subject, k), 文本节点可见: vis(out.textSweep, k) };
log('\n=== 对照（同一判据，只差节点类型）===');
log(JSON.stringify(out.compare, null, 1));
out.judgement = {
  判据在文本节点上打中: Object.entries(out.compare).filter(([, v]) => v.文本节点可见 > 0).map(([k]) => k),
  判据在主体节点上打中: Object.entries(out.compare).filter(([, v]) => v.主体节点可见 > 0).map(([k]) => k),
  主体节点候选数: out.subject.candidates.length, 文本节点候选数: out.textSweep.candidates.length,
};
log('\n=== 判定 ==='); log(JSON.stringify(out.judgement, null, 1));
out.end = { nodes: await nodeN(), credits: await credits() };
log('终点：', JSON.stringify(out.end));
save();
log('\nDONE b');
process.exit(0);
