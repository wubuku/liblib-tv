// 批次 138 · a 轮：在**「有边」的状态下**观测「显示连线」开关。
//
// 🔑 靶子：`SOURCE_OBSERVATIONS.md:9651` 记着一行自我标注的读数缺陷 ——
//   「`canvas-display-toggle-connections` `28×28@80,672`，`aria-pressed` **`true → false`**，
//    **但 `edges` 恒 `0` ⇒ 判「无变化」🔴**」。
//   ⇒ 早前确实点过这个开关，**但画布上一条边都没有**，所以**它到底管不管用从未被观测过**。
//   本轮补上：**先建一条边**，再开→关→开三态读数。
//
// 🔑 顺带做一组**交叉对照**（批次 134 的「任何缩放操作都会关掉小地图」正好是同类现象）：
//   ① 点缩放按钮（**根本不改缩放**）→ 小地图被关、**连线开关会不会也被关？**
//   ② 反过来：先关掉小地图，再点连线开关 → **小地图会不会被顺手打开？**
//   —— 这两个开关是不是「共用一个『重置显示设置』的动作」？
//
// 🛡 共享画布纪律：本轮建 1 条边，终点是**边数回到 0**（`⌘Z`，焦点守卫通过后按）。
//   开关本身是纯视图开关，三态读完后必须**回到「开」**（小地图也必须回到「开」）。
import { writeFileSync } from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { readConnect, canvasPos } from './jimeng-b136-lib.mjs';
import { 建一条边 } from './jimeng-b136-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b138a.json', import.meta.url), JSON.stringify(out, null, 1));
const 断言 = (名, 条件, 详情) => { const ok = !!!!条件; (out.护栏 = out.护栏 || []).push({ 名, 通过: ok, 详情 });
  log(`  ${ok ? '✅' : '⛔'} 断言·${名}：${JSON.stringify(详情).slice(0, 300)}`); save(); return ok; };
const 边数 = async () => (await readConnect(p)).边数;

process.on('uncaughtException', async (e) => {
  console.error('💥 未捕获异常：', e && e.message);
  try { if ((await 边数()) > 0) { const g = await keyGuard(p); if (g.safe) { await p.keyboard.press('Meta+z'); await p.waitForTimeout(2000); } } } catch (_) {}
  await b.close(); process.exit(4);
});

/** 读两个显示开关 + 边的全部可观测状态。 */
const 快照 = () => p.evaluate(() => {
  const box = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
    return { w: Math.round(r.width * 10) / 10, h: Math.round(r.height * 10) / 10, x: Math.round(r.x), y: Math.round(r.y) }; };
  const sw = (t) => { const e = document.querySelector(`[data-testid="${t}"]`); if (!e) return null;
    const s = getComputedStyle(e);
    return { testid: t, tag: e.tagName, rect: box(e), ariaLabel: e.getAttribute('aria-label'),
      ariaPressed: e.getAttribute('aria-pressed'), dataState: e.getAttribute('data-state'),
      pe: s.pointerEvents, opacity: s.opacity, visibility: s.visibility, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(),
      子元素数: e.children.length,
      祖先链: (() => { const a = []; for (let n = e; n && n !== document.body && a.length < 6; n = n.parentElement) a.push(String(n.className || '').split(' ')[0] || n.tagName); return a; })() }; };
  const edges = Array.from(document.querySelectorAll('.react-flow__edge'));
  const vp = document.querySelector('.react-flow__viewport');
  const ms = vp ? /scale\(([-\d.]+)\)/.exec(vp.style.transform || '') : null;
  return {
    连线开关: sw('canvas-display-toggle-connections'),
    小地图开关: sw('canvas-display-toggle-minimap'),
    实测scale: ms ? Math.round(parseFloat(ms[1]) * 1000) / 1000 : null,
    边DOM数: edges.length,
    边: edges.map((e) => { const r = e.getBoundingClientRect();
      return { testid: e.getAttribute('data-testid'), id: e.getAttribute('data-id'), class: e.getAttribute('class'),
        aria: e.getAttribute('aria-label'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        dataState: (() => { const g = e.querySelector('[data-testid="reference-edge-interaction"]'); return g ? g.getAttribute('data-state') : null; })(),
        pathStroke: (() => { const q = e.querySelector('path.react-flow__edge-path'); return q ? getComputedStyle(q).stroke : null; })(),
        pathOpacity: (() => { const q = e.querySelector('path.react-flow__edge-path'); return q ? getComputedStyle(q).strokeOpacity : null; })(),
        祖先链: (() => { const a = []; for (let n = e; n && n !== document.body && a.length < 5; n = n.parentElement) a.push(String(n.className || '').split(' ')[0] || n.tagName); return a; })() }; }),
    edges层矩形: (() => { const e = document.querySelector('.react-flow__edges'); return e ? box(e) : null; })(),
    小地图面: (() => { const e = document.querySelector('[data-testid="canvas-minimap-surface"]'); return e ? box(e) : null; })(),
    testid总数: new Set(Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid'))).size,
    全部testid: Array.from(new Set(Array.from(document.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))).sort(),
  };
});

/** 点一个开关（先在它内部找一个真能点到的点，**不靠坐标猜**）。 */
const 点开关 = async (testid) => {
  const pt = await p.evaluate((t) => { const e = document.querySelector(`[data-testid="${t}"]`); if (!e) return { __err: 'nf' };
    const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2)
      for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
        const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y };
      }
    return { __err: 'no-point' }; }, testid);
  if (pt.__err) { log(`  ⛔ ${testid} ${pt.__err}`); return pt; }
  await p.mouse.click(pt.x, pt.y);
  await p.waitForTimeout(1800);
  return pt;
};

// ---------------------------------------------------------------- ① 基线
await keyGuard(p);
await settle(p, R);
out.基线 = { 状态行: await R.status(), 节点数: (await R.ids()).length, testid种类: (await R.testids()).length, zoom: await R.zoom() };
out.基线ids = await R.ids();
out.基线testids = await R.testids();
out.基线canvas = await canvasPos(p);
out.无边基线快照 = await 快照();
log('基线（**没有边**）：', JSON.stringify(out.基线));
log('  连线开关：', JSON.stringify(out.无边基线快照.连线开关));
log('  小地图开关：', JSON.stringify(out.无边基线快照.小地图开关));
save();
断言('起点 0 边', (await 边数()) === 0, {});
断言('两个开关都在 DOM 里', !!out.无边基线快照.连线开关 && !!out.无边基线快照.小地图开关, {});

// ---------------------------------------------------------------- ② 建一条边
log('\n=== ② 建一条边（建边代码与批次 136 逐字相同） ===');
const 建 = await 建一条边(p);
out.建边 = 建;
log('  ', JSON.stringify({ ok: 建.ok, 边数: 建.边数, 源: 建.计划 && 建.计划.源 }));
save();
断言('边已建成', 建.ok, { 边数: 建.边数 });
if (!建.ok) { log('⛔ 没建出线'); await b.close(); process.exit(0); }

// ---------------------------------------------------------------- ③ 开 → 关 → 开 三态
log('\n=== ③ 三态：开（默认）→ 关 → 开 ===');
out.三态 = [];
const 记 = async (tag) => { const s = await 快照();
  const rec = { tag, 连线开关: s.连线开关, 小地图开关: s.小地图开关, 边DOM数: s.边DOM数,
    边: s.边, edges层矩形: s.edges层矩形, 小地图面: s.小地图面, testid总数: s.testid总数, 实测scale: s.实测scale };
  out.三态.push(rec);
  log(`\n  ── ${tag} ──`);
  log(`     连线开关 aria-pressed=${rec.连线开关 && rec.连线开关.ariaPressed} data-state=${rec.连线开关 && rec.连线开关.dataState} aria=«${rec.连线开关 && rec.连线开关.ariaLabel}»`);
  log(`     小地图开关 aria-pressed=${rec.小地图开关 && rec.小地图开关.ariaPressed}｜小地图面 ${JSON.stringify(rec.小地图面)}`);
  log(`     **边 DOM 数 ${rec.边DOM数}**｜${JSON.stringify(rec.边 && rec.边.map((e) => ({ id: e.id, rect: e.rect, dataState: e.dataState, stroke: e.pathStroke, strokeOpacity: e.pathOpacity })))}`);
  log(`     edges 层矩形 ${JSON.stringify(rec.edges层矩形)}｜testid 种类 ${rec.testid总数}`);
  save();
  return rec;
};
const S0 = await 记('① 默认（开关应为开）');
await 点开关('canvas-display-toggle-connections');
const S1 = await 记('② 点「显示连线」之后');
await 点开关('canvas-display-toggle-connections');
const S2 = await 记('③ 再点一次（回到开）');
save();

// ---------------------------------------------------------------- ④ 交叉对照：两个开关会不会互相影响
log('\n=== ④ 交叉对照：开关之间、以及与缩放按钮之间 ===');
out.交叉 = [];
const 记2 = async (tag) => { const s = await 快照();
  const rec = { tag, 连线: s.连线开关 && s.连线开关.ariaPressed, 小地图: s.小地图开关 && s.小地图开关.ariaPressed,
    边DOM数: s.边DOM数, 小地图面: s.小地图面, 实测scale: s.实测scale, zoom: await R.zoom() };
  out.交叉.push(rec);
  log(`  ── ${tag} ── 连线开关 ${rec.连线}｜小地图开关 ${rec.小地图}｜边 DOM ${rec.边DOM数}｜小地图面 ${JSON.stringify(rec.小地图面)}｜zoom «${rec.zoom}»／实测 scale ${rec.实测scale}`);
  save(); return rec;
};
log('\n  · 对照 A：两个开关都开着时，只点「缩放按钮」（**不改缩放**）');
await 记2('A0 起点');
{
  const pt = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) { const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; } return null; });
  if (pt) { await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1800); } else log('    ⛔ 找不到缩放按钮落点');
  for (let i = 0; i < 3; i++) { if (!(await R.overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(700); }
  await 记2('A1 只点缩放按钮之后');
}
log('\n  · 对照 B：先把小地图关掉，再点「显示连线」，看小地图会不会被顺手打开');
await 记2('B0 起点');
await 点开关('canvas-display-toggle-minimap');
await 记2('B1 关掉小地图之后');
await 点开关('canvas-display-toggle-connections');
await 记2('B2 再点「显示连线」之后');
await 点开关('canvas-display-toggle-connections');
await 记2('B3 再点回「开」');
save();

// ---------------------------------------------------------------- ⑤ 归位
log('\n=== ⑤ 归位：删边、两个开关都回「开」、小地图开 ===');
if ((await 边数()) > 0) { const g = await keyGuard(p); if (g.safe) { await p.keyboard.press('Meta+z'); await p.waitForTimeout(2500); } }
await settle(p, R);
const fin = await 快照();
if (fin.连线开关.ariaPressed !== 'true') { await 点开关('canvas-display-toggle-connections'); }
const fin2 = await 快照();
if (fin2.小地图开关.ariaPressed !== 'true') { await 点开关('canvas-display-toggle-minimap'); }
await settle(p, R);
const end = await canvasPos(p);
const ids = await R.ids(), t = await R.testids();
const 末 = await 快照();
out.收尾 = { 状态行: await R.status(), 边数: await 边数(), 选中: await R.selCount(), 浮层: await R.overlays(),
  zoom: await R.zoom(), credits: await R.credits(), minimap: 末.小地图开关.ariaPressed, 连线开关: 末.连线开关.ariaPressed,
  节点数: ids.length, testid种类: t.length,
  节点被移动: Object.keys(out.基线canvas).filter((id) => JSON.stringify(out.基线canvas[id]) !== JSON.stringify(end[id])),
  节点差集: { 多: ids.filter((x) => !out.基线ids.includes(x)), 少: out.基线ids.filter((x) => !ids.includes(x)) },
  testid差集: { 多: t.filter((x) => !out.基线testids.includes(x)), 少: out.基线testids.filter((x) => !t.includes(x)) } };
log('  ', JSON.stringify(out.收尾));
save();
断言('边数回到 0', (await 边数()) === 0, { 边数: await 边数() });
断言('两个开关都回「开」', 末.连线开关.ariaPressed === 'true' && 末.小地图开关.ariaPressed === 'true',
  { 连线: 末.连线开关.ariaPressed, 小地图: 末.小地图开关.ariaPressed });
断言('节点 id 与 testid 均与基线逐个一致', out.收尾.节点差集.多.length === 0 && out.收尾.节点差集.少.length === 0
  && out.收尾.testid差集.多.length === 0 && out.收尾.testid差集.少.length === 0, { 节点: out.收尾.节点差集, testid: out.收尾.testid差集 });
save(); save();
log('\n✅ a 轮完成 → ./_tmp-b138a.json');
await b.close();
