// 批次 120 · z 轮（清理）：c 轮的「取消选中」落点 (24,400) 打在了**左栏按钮**上
// （实测命中 `inline-flex size-9 shrink-0 items-center justify-c…`），
// 于是**建出了一个时间线节点**（76 → 77，标题「时间线 3」，且是 `.selected`）。
//
// 🔴 本脚本记录的事故与立规：
//   「点空白处取消选中」这个动作，**空白点必须先自检**：
//   落点现算 + `elementFromPoint` 命中**不是**画布空白（`.react-flow__pane`）就**不许点**。
//   我在 b 轮立规时只写了「命中元素落在目标内部」，那是**「点某个控件」的正路**；
//   「点空白」是**反向**用法 —— 判据是「命中元素属于可点的 chrome 就算错」。
//
// 护栏（批次 97/105）：
//   ① 基线 = 批次 119 收尾门输出的 76 个 id（本文件从 /tmp/b120-baseline-ids.txt 读）
//   ② 现状取差集，**必须恰好一个**，且**必须同时是 `.selected`**
//   ③ 删除前再确认目标仍 selected；事后核对「本轮消失的 id」**恰好只有 SELF**
//   ④ 落点在动作即将发生的那一刻现算；点完读到「少了一个」才继续
//
// 收尾顺序：删自建节点 → 归位缩放（回读 + 连读两次）→ 归位工具态 → 确认 sel=0
import { chromium } from 'playwright';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { pinViewport, keyGuard, canvasBaseline, diffNodePositions } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'z', incident: 'c 轮空白落点打在左栏按钮上，建出「时间线 3」' };
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
out.base0 = { 节点数: base0.length };

// ---- 护栏① ②：差集必须恰好一个，且必须 selected ----
const baseline = new Set(readFileSync('/tmp/b120-baseline-ids.txt', 'utf8').split('\n').map((s) => s.trim()).filter(Boolean));
const now = await ids();
const extra = now.filter((i) => !baseline.has(i));
const missing = [...baseline].filter((i) => !now.includes(i));
const selected = await sel();
out.guard = { 基线数: baseline.size, 现状数: now.length, 多出: extra, 缺失: missing, 选中: selected };
log('\n护栏②：基线 ' + baseline.size + ' → 现状 ' + now.length + '｜多出 ' + extra.length + ' 个 ' + JSON.stringify(extra) + '｜缺失 ' + missing.length);
log('         选中态：', JSON.stringify(selected));
if (extra.length !== 1) { log('⛔ 多出的 id 不是恰好一个，中止（不猜不硬删）'); save(); await b.close(); process.exit(3); }
if (selected.length !== 1 || selected[0].id !== extra[0]) { log('⛔ 多出的 id 不是唯一选中项，中止'); save(); await b.close(); process.exit(3); }
const SELF = extra[0];
out.self = { id: SELF, 标题: selected[0].标题 };
log('✅ 护栏②通过：SELF = ' + SELF + '（' + selected[0].标题 + '）');

// ---- 护栏③：删除前再确认目标仍 selected ----
const selBefore = await sel();
log('\n护栏③（删除前再确认）：', JSON.stringify(selBefore));
if (selBefore.length !== 1 || selBefore[0].id !== SELF) { log('⛔ 目标不再是唯一选中项，中止'); save(); await b.close(); process.exit(3); }

// ---- 护栏④：落点现算（不点任何 chrome，命中必须落回节点自身） ----
const pt = await p.evaluate((id) => {
  const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
  if (!n) return { __err: 'gone' };
  const q = n.getBoundingClientRect();
  const cx = q.x + q.width / 2, cy = q.y + q.height / 2;
  const el = document.elementFromPoint(cx, cy);
  return { 矩形: [q.x, q.y, q.width, q.height].map(Math.round), 落点: [Math.round(cx), Math.round(cy)],
    命中: el ? el.tagName + '.' + (el.className || '').toString().slice(0, 40) : null,
    命中落回本节点: el ? (el === n || n.contains(el)) : false };
}, SELF);
out.point = pt;
log('落点（现算）：', JSON.stringify(pt));
if (pt.__err || !pt.命中落回本节点) { log('⛔ 落点自检不通过，中止'); save(); await b.close(); process.exit(3); }

await p.keyboard.press('Backspace');
await p.waitForTimeout(1500);

// ---- 护栏③后半：核对「本轮消失的 id」恰好只有 SELF ----
const after = await ids();
const disappeared = now.filter((i) => !after.includes(i));
out.after = { 现状数: after.length, 消失: disappeared, 选中: await sel() };
log('\n护栏③（事后）：消失的 id =', JSON.stringify(disappeared), '｜现状', after.length, '｜选中', JSON.stringify(out.after.选中));
if (disappeared.length !== 1 || disappeared[0] !== SELF) { log('⛔ 消失集合不等于 {SELF}，需要人工核查'); save(); await b.close(); process.exit(4); }
log('✅ 护栏③通过：本轮消失的 id 恰好只有 SELF');

// ---- 归位缩放：回读 + 连读两次 ----
let z = await zoom();
if (z !== 'Zoom options, 60%') {
  log('\n缩放需要归位：当前', z);
  await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); e.click(); });
  await p.waitForTimeout(500);
  await p.fill('[data-testid="canvas-zoom-percent-input"]', '60');
  await p.keyboard.press('Enter');
  await p.waitForTimeout(1600);
  z = await zoom();
}
const z1 = await zoom(); await p.waitForTimeout(700); const z2 = await zoom();
out.zoom归位 = { 读数1: z1, 读数2: z2, 一致: z1 === z2 };
log('\n缩放归位：', JSON.stringify(out.zoom归位));

// ---- 归位工具态 + 确认 sel=0 ----
const t = await tool();
out.tool = t;
out.selEnd = (await sel()).length;
out.creditsEnd = await credits();
out.positions = await diffNodePositions(p, base0, 1.5);
log('工具态：', t, '｜终态选中数：', out.selEnd, '｜积分：', out.creditsEnd);
log('节点位置偏离：', out.positions ? out.positions.length + ' 个' : JSON.stringify(out.positions));
save();
log('\nDONE z');
process.exit(0);
