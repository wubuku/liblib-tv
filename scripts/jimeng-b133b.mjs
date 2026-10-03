// 批次 133 · b 轮：验证「Agent 侧栏头部被顶栏盖住、按钮点不到」这个发现。
//
// 🔑 起因：a 轮点 `canvas-agent-session-menu-trigger`（`885,25,58,32`）报 `no-point`，
//   逐点探测发现 `elementFromPoint` 在该矩形内**全部命中 `HEADER`** ——
//   而顶栏 `canvas-top-bar` 是 `12,10,1256,40`（**y 10..50**），
//   那两个按钮都在 **y 13..32**，**完全落在顶栏的 y 范围内**。
//   手册 `20-reference.md:19` 早就记着「整条 `HEADER[canvas-top-bar]` 是 `pointer-events:none`
//   （`z-index:30`，高于节点层 `z-index:4`），只有 10 个按…可点」——
//   **但侧栏展开时它似乎不是 none**，否则 `elementFromPoint` 不会返回它。
//
// 📌 本轮要量的：对每个 Agent 按钮，**扫描它整个矩形的采样点，统计有多少比例能命中自身**，
//   并列出**实际挡住它的是什么**。这是把「点不到」从一句观察变成可复现的比例。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b' };
const save = () => writeFileSync(new URL('./_tmp-b133b.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const idsNow = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const sidecar = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-feature-sidecar"]');
  return e ? { op: getComputedStyle(e).opacity, state: e.getAttribute('data-state'), 子元素: e.children.length } : null; });

out.start = { 状态行: await status(), 选中: await sel(), zoom: await zoom(), 侧栏: await sidecar() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
await p.mouse.move(1276, 716); await p.waitForTimeout(700);
out.起始id = await idsNow();

// 保证侧栏是展开态
if ((await sidecar())?.op !== '1') { await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1600); }
log('侧栏：', JSON.stringify(await sidecar()));
save();

const 扫 = () => p.evaluate(() => {
  const tids = ['canvas-agent-session-menu-trigger', 'canvas-agent-session-create', 'canvas-agent-session-collapse',
    'canvas-agent-skill-trigger', 'canvas-agent-send', 'canvas-agent-composer-add', 'canvas-agent-composer-mention',
    'canvas-agent-composer-placeholder-mention', 'canvas-agent-mode-action', 'canvas-agent-session-title'];
  const 按钮 = [];
  for (const t of tids) {
    const e = document.querySelector('[data-testid="' + t + '"]');
    if (!e) { 按钮.push({ t, 存在: false }); continue; }
    const q = e.getBoundingClientRect();
    let hit = 0, tot = 0; const stack = {};
    for (let y = Math.ceil(q.y) + 1; y <= q.y + q.height - 1; y += 2)
      for (let x = Math.ceil(q.x) + 1; x <= q.x + q.width - 1; x += 3) {
        tot++;
        const h = document.elementFromPoint(x, y);
        const k = h ? (h.getAttribute('data-testid') || h.tagName) : 'null';
        stack[k] = (stack[k] || 0) + 1;
        if (h && (h === e || e.contains(h))) hit++;
      }
    const cs = getComputedStyle(e);
    按钮.push({ t, 存在: true, 矩形: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
      命中自身: hit + '/' + tot, 自身pe: cs.pointerEvents, 自身zIndex: cs.zIndex,
      挡住它的: Object.entries(stack).filter(([k]) => k !== t).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([k, v]) => k + '×' + v) });
  }
  const hd = document.querySelector('header') || document.querySelector('[data-testid="canvas-top-bar"]');
  const hcs = hd ? getComputedStyle(hd) : null;
  const hr = hd ? hd.getBoundingClientRect() : null;
  const hdTid = hd ? hd.getAttribute('data-testid') : null;
  // 顶栏在「有侧栏」与「无侧栏」两种状态下的 pointer-events 对照
  const headerProbe = [];
  for (const [x, y] of [[885, 27], [1195, 25], [926, 654], [400, 300]]) {
    const h = document.elementFromPoint(x, y);
    headerProbe.push({ 点: [x, y], 命中: h ? (h.getAttribute('data-testid') || h.tagName) : null });
  }
  const side = document.querySelector('[data-testid="canvas-feature-sidecar"]');
  return { 按钮, 顶栏: { testid: hdTid, 矩形: hr ? [Math.round(hr.x), Math.round(hr.y), Math.round(hr.width), Math.round(hr.height)] : null,
      pointerEvents: hcs ? hcs.pointerEvents : null, zIndex: hcs ? hcs.zIndex : null, 逐字: hd ? (hd.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 50) : null },
    侧栏: side ? { zIndex: getComputedStyle(side).zIndex, 矩形: (r => [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)])(side.getBoundingClientRect()) } : null,
    四个点的命中: headerProbe };
});

log('\n=== ① 侧栏展开态：每个按钮的「可点比例」与遮挡者 ===');
out.展开态 = await 扫();
out.展开态.按钮.forEach((e) => {
  if (!e.存在) { log(`  · ${e.t} —— 不存在`); return; }
  log(`  · ${e.t.padEnd(44)} ${JSON.stringify(e.矩形).padEnd(24)} 命中自身 ${e.命中自身.padEnd(8)} pe=${e.自身pe} z=${e.自身zIndex}  遮挡: ${e.挡住它的.join(', ') || '无'}`);
});
log('\n  顶栏：', JSON.stringify(out.展开态.顶栏));
log('  侧栏 z-index：', JSON.stringify(out.展开态.侧栏));
log('  四个采样点的命中：', JSON.stringify(out.展开态.四个点的命中));
save();

// ---------------------------------------------------------------- ② 关掉侧栏再扫一次（对照）
log('\n=== ② 关掉侧栏再扫一次（对照：顶栏的 pointer-events 变不变）===');
{
  await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1600);
  out.折叠态 = await 扫();
  log('  侧栏：', JSON.stringify(await sidecar()));
  log('  顶栏：', JSON.stringify(out.折叠态.顶栏));
  log('  四个采样点的命中：', JSON.stringify(out.折叠态.四个点的命中));
  const 有 = out.展开态.顶栏.pointerEvents, 无 = out.折叠态.顶栏.pointerEvents;
  out.顶栏对照 = { 展开时: 有, 折叠时: 无, 相同: 有 === 无 };
  log(`  🔑 顶栏 pointer-events：展开 ${有} ／ 折叠 ${无} ⇒ ${有 === 无 ? '**相同**' : '**不同**'}`);
  save();
}

// ---------------------------------------------------------------- ③ 收尾：确保侧栏关、鼠标移开
log('\n=== ③ 收尾归位 ===');
{
  let s = await sidecar(), n = 0;
  while (s && s.op === '1' && n < 3) { await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1500); s = await sidecar(); n++; }
  await p.mouse.move(1276, 716); await p.waitForTimeout(800);
  const t = await collect();
  function collect() { return p.evaluate(() => { const s = new Set(); for (const e of document.querySelectorAll('[data-testid]')) s.add(e.getAttribute('data-testid')); return Array.from(s); }); }
  out.收尾 = { 侧栏: s, 选中: await sel(), 状态行: await status(), zoom: await zoom(),
    浮层含tooltip: await p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox],[role=tooltip]')).filter((m) => m.getBoundingClientRect().width > 1).length),
    浮层不含tooltip: await p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length),
    节点数: (await idsNow()).length, 起始节点数: out.起始id.length, testid种类: t.length };
  out.新增id = (await idsNow()).filter((x) => !out.起始id.includes(x));
  log('收尾：', JSON.stringify(out.收尾));
  log('  新增 id（必须空）：', JSON.stringify(out.新增id));
  save();
}
log('\nDONE b');
process.exit(0);
