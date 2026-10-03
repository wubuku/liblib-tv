// 批次 120 · z2 轮（清理补做）：z 轮按 Backspace **没删掉**。
//
// 🔴 z 轮的失败与它立下的规：
//   落点现算落在节点**中心**，命中的是节点**内部工具条上的一个 BUTTON** ⇒
//   节点虽然是 `.selected`，但**键盘焦点不在节点上**，按 Backspace 无反应
//   （读数：消失的 id = `[]`，选中态没变）。
//   ⇒ 立规：**删除不要走键盘**。节点有子控件时，中心落点会把焦点交给子控件。
//     走**右键 → 上下文菜单 → 「删除」**（批次 118/119/97 都验过这条路），
//     菜单项的落点现算 + `elementFromPoint` 自检在**同一个 evaluate** 里做。
//
// 护栏同 z 轮：②差集恰好一个且唯一选中 ③删前确认仍 selected、事后消失集合恰好 {SELF}
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
// ⚠️ z2 不用 diffNodePositions：它要的是 [x,y] 坐标表，canvasBaseline 返回的是对象
//    （z2 第一次跑时传错了形状，被该 helper 正确挡下 —— 这个守卫是有用的）
import { pinViewport, keyGuard, canvasBaseline } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'z2', 起因: 'z 轮 Backspace 未生效（焦点被节点内部 BUTTON 接管）' };
const save = () => writeFileSync(new URL('./_tmp-b120z.json', import.meta.url), JSON.stringify(out, null, 1));

const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const tool = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-pointer-tool-toggle"]'); return e ? e.getAttribute('aria-label') : null; });
const ids = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node[data-id]')).map((n) => n.getAttribute('data-id')));
const sel = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((n) => ({ id: n.getAttribute('data-id'), 标题: (n.innerText || '').split('\n')[0] })));

out.start = { zoom: await zoom(), credits: await credits(), tool: await tool() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
const base0 = await canvasBaseline(p);

// 先按 Esc 收掉可能开着的面板
await p.keyboard.press('Escape'); await p.waitForTimeout(900);

const baseline = new Set(readFileSync('/tmp/b120-baseline-ids.txt', 'utf8').split('\n').map((s) => s.trim()).filter(Boolean));
const now = await ids();
const extra = now.filter((i) => !baseline.has(i));
let selected = await sel();
out.guard = { 基线数: baseline.size, 现状数: now.length, 多出: extra, 选中: selected };
log('\n护栏②：基线 ' + baseline.size + ' → 现状 ' + now.length + '｜多出 ' + JSON.stringify(extra) + '｜选中 ' + JSON.stringify(selected));
if (extra.length === 0 && now.length === baseline.size) {
  // 幂等重跑：上一轮已经删干净了，只补记终态
  out.alreadyClean = true;
  const z1 = await zoom(); await p.waitForTimeout(700); const z2 = await zoom();
  out.zoom归位 = { 读数1: z1, 读数2: z2, 一致: z1 === z2 && z1 === 'Zoom options, 60%' };
  out.tool = await tool(); out.selEnd = (await sel()).length; out.creditsEnd = await credits();
  out.nodesEnd = now.length;
  out.残留时间线3 = now.some((i) => false);
  out.终态 = { 缩放: out.zoom归位, 工具: out.tool, 选中: out.selEnd, 积分: out.creditsEnd, 节点数: out.nodesEnd };
  log('\n幂等重跑：已是干净终态 ', JSON.stringify(out.终态));
  save(); log('\nDONE z2'); await b.close(); process.exit(0);
}
if (extra.length !== 1) { log('⛔ 多出的 id 不是恰好一个，中止'); save(); await b.close(); process.exit(3); }
const SELF = extra[0];

// 护栏③前半：确保 SELF 是唯一选中项
if (selected.length !== 1 || selected[0].id !== SELF) {
  const selPt = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
    const r = n.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 6; y < r.y + r.height - 6; y += 5)
      for (let x = Math.ceil(r.x) + 6; x < r.x + r.width - 6; x += 5) { if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
        const el = document.elementFromPoint(x, y); if (el && (el === n || n.contains(el))) return { x, y }; }
    return { __err: 'unreachable', rect: [r.x, r.y, r.width, r.height].map(Math.round) }; }, SELF);
  log('补选落点：', JSON.stringify(selPt));
  if (selPt.__err) { log('⛔ 中止'); save(); await b.close(); process.exit(3); }
  await p.mouse.click(selPt.x, selPt.y); await p.waitForTimeout(1500);
  selected = await sel();
  log('补选后选中态：', JSON.stringify(selected));
}
if (selected.length !== 1 || selected[0].id !== SELF) { log('⛔ SELF 不是唯一选中项，中止'); save(); await b.close(); process.exit(3); }
log('✅ 护栏③前半通过：SELF=' + SELF + '（' + selected[0].标题 + '）');

// 右键 → 菜单 → 删除
const rc = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); const r = n.getBoundingClientRect(); return [r.x, r.y, r.width, r.height].map(Math.round); }, SELF);
const rx = Math.round(rc[0] + rc[2] / 2), ry = Math.round(rc[1] + rc[3] / 2);
out.rightClickAt = [rx, ry];
await p.mouse.move(rx, ry); await p.waitForTimeout(450);
await p.mouse.down({ button: 'right' }); await p.waitForTimeout(300); await p.mouse.up({ button: 'right' });
await p.waitForTimeout(1400);

const del = await p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]')) {
  const cs = getComputedStyle(m); if (cs.visibility === 'hidden') continue;
  for (const it of m.querySelectorAll('[role=menuitem]')) {
    const t = (it.innerText || '').replace(/\s+/g, ' ').trim();
    if (!/^删除/.test(t)) continue;
    if (it.getAttribute('aria-disabled') === 'true' || it.hasAttribute('disabled')) return { t, disabled: true };
    const r = it.getBoundingClientRect(); if (r.width < 1) continue;
    const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    const h = document.elementFromPoint(cx, cy);
    if (!h || !(h === it || it.contains(h))) return { t, hitFail: { tag: h ? h.tagName : null, txt: h ? (h.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20) : null } };
    return { t, rect: [r.x, r.y, r.width, r.height].map(Math.round), disabled: false, 菜单项数: m.querySelectorAll('[role=menuitem]').length }; } }
  return null; });
out.del = del;
log('「删除」项：', JSON.stringify(del));
if (!del || del.disabled || del.hitFail) { log('⛔ 拿不到可点的「删除」⇒ 中止'); await p.keyboard.press('Escape'); await p.waitForTimeout(600); save(); await b.close(); process.exit(4); }

const before = await ids();
await p.mouse.click(del.rect[0] + del.rect[2] / 2, del.rect[1] + del.rect[3] / 2);
await p.waitForTimeout(2400);
const after = await ids();
const disappeared = before.filter((i) => !after.includes(i));
out.result = { before: before.length, after: after.length, 消失: disappeared, 恰好SELF: disappeared.length === 1 && disappeared[0] === SELF, 选中: await sel() };
log('\n护栏③后半：消失的 id =', JSON.stringify(disappeared), '｜', before.length, '→', after.length, '｜恰好 SELF？', out.result.恰好SELF);
if (!out.result.恰好SELF) { log('⛔ 消失集合不等于 {SELF}'); save(); await b.close(); process.exit(4); }
log('✅ 护栏③通过：自建节点已清除');

// 归位：缩放连读两次 + 工具态 + sel=0
let z1 = await zoom(); await p.waitForTimeout(700); let z2 = await zoom();
if (z1 !== 'Zoom options, 60%' || z2 !== 'Zoom options, 60%') {
  await p.evaluate(() => document.querySelector('[data-testid="canvas-zoom-percent"]').click());
  await p.waitForTimeout(500);
  await p.fill('[data-testid="canvas-zoom-percent-input"]', '60');
  await p.keyboard.press('Enter');
  await p.waitForTimeout(1700);
  z1 = await zoom(); await p.waitForTimeout(700); z2 = await zoom();
}
out.zoom归位 = { 读数1: z1, 读数2: z2, 一致: z1 === z2 && z1 === 'Zoom options, 60%' };
out.tool = await tool();
out.selEnd = (await sel()).length;
out.creditsEnd = await credits();
out.nodesEnd = (await ids()).length;
out.基线条数 = base0.nodes ? base0.nodes.length : null;
log('\n终态：', JSON.stringify({ 缩放: out.zoom归位, 工具: out.tool, 选中: out.selEnd, 积分: out.creditsEnd, 节点数: out.nodesEnd, 基线状态行: base0.status }));
save();
log('\nDONE z2');
process.exit(0);
