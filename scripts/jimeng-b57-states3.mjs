// 批次 57 实验三：补齐选中态的 4 个缺口 + 查实一个新发现
//
// 缺口 ① 文本 1 / 文本 2 **没选中**（selAfterClick=[]）——
//   「它们没有 Rename」是**无效读数**，前置条件就没成立（批次 56 的老教训：
//   阴性结果先问「我测的是不是同一个东西、前置条件成立了吗」）。
//   原因：三个文本节点在画布上**互相重叠**，安全落点扫描出来的点没选中目标。
//   → 本轮在节点矩形内做**细网格**逐点试点，报告「哪种落点能选中」。
//
// 缺口 ② 图片 / 音频 / 主体 三个类型**只有静息态**读数（主脚本只量到 S1）。
//   主体静息时就已经是 `Edit 主体 1`（不是 `Rename`）—— 契约又不一样。
//   → 本轮新建这三个，量 S1/S2/S3，量完按 id 精确删除。
//
// 新发现 ③ 导演台节点**选中后「进入导演台」按钮从 DOM 消失**：
//   静息 aria = [Add tags, 进入导演台]；选中 aria = [Rename 导演台, Add tags]。
//   「进入导演台」是该节点类型**唯一的操作**，它消失是大事 —— 但必须先排除
//   「只是挪到节点子树之外的 portal」。→ 选中时**扫全文档**逐字找「进入导演台」。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const OUT = new URL('./_tmp-b57-out3.json', import.meta.url);
const MINE = [];

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);
const reset = async () => { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); } };
const selIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const scaleOf = () => p.evaluate(() => { const v = document.querySelector('.react-flow__viewport');
  const m = v && /scale\(([-\d.]+)\)/.exec(v.style.transform); return m ? +(+m[1]).toFixed(4) : null; });
const coords = () => p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
  return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null];
})));
const isEmpty = (x, y) => p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y); if (!el) return true;
  if (el.closest('.react-flow__node')) return false;
  if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"]')) return false;
  return true; }, [x, y]);
const findEmpty = async () => { for (let y = 110; y <= 630; y += 20) for (let x = 80; x <= 1250; x += 20) { if (x > 1150 && y > 600) continue; if (await isEmpty(x, y)) return { x, y }; } return null; };
const deselect = async () => { await reset(); const e = await findEmpty();
  if (e) { await p.mouse.click(e.x, e.y); await p.waitForTimeout(600); }
  for (let i = 0; i < 3 && (await selIds()).length; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  return (await selIds()).length === 0; };

// 读数：卡片矩形 + 子树内全部带 aria-label 的元素 + 全文档关键字命中
const dump = (id, state, kw) => p.evaluate(([vid, st, k]) => {
  const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`);
  if (!n) return null;
  const RR = (e) => { const r = e.getBoundingClientRect(); return { x: +r.x.toFixed(1), y: +r.y.toFixed(1), w: +r.width.toFixed(1), h: +r.height.toFixed(1) }; };
  const node = RR(n), nt = n.getBoundingClientRect().top;
  const ariaEls = Array.from(n.querySelectorAll('[aria-label]')).filter((e) => (e.getAttribute('aria-label') || '').length > 0);
  return {
    state: st, id: vid, cls: Array.from(n.classList).filter((c) => c.startsWith('react-flow__node-')).join(','),
    nodeAria: n.getAttribute('aria-label'), node, selected: n.classList.contains('selected'),
    countDescendants: n.querySelectorAll('*').length, countAria: ariaEls.length,
    countTid: n.querySelectorAll('[data-testid]').length,
    aria: ariaEls.map((e) => { const r = e.getBoundingClientRect();
      return { a: e.getAttribute('aria-label'), t: e.getAttribute('data-testid'), box: RR(e), vis: r.width > 1 && r.height > 1,
        dTop: +(r.top - nt).toFixed(1), dBottom: +(r.bottom - nt).toFixed(1) }; }),
    // 全文档逐字找关键字（判 portal / 判「按钮是不是消失了」）
    docHits: Array.from(document.querySelectorAll('button,[role="button"],[aria-label]'))
      .filter((e) => ((e.innerText || '') + ' ' + (e.getAttribute('aria-label') || '')).includes(k))
      .map((e) => { const r = e.getBoundingClientRect();
        return { txt: ((e.innerText || '').trim().split('\n')[0] || e.getAttribute('aria-label') || '').slice(0, 30),
          aria: e.getAttribute('aria-label'), tid: e.getAttribute('data-testid'),
          inThisNode: !!e.closest(`.react-flow__node[data-id="${vid}"]`), inSomeNode: (e.closest('.react-flow__node') || {}).getAttribute?.('data-id') || null,
          box: RR(e), vis: r.width > 1 && r.height > 1 }; }),
  };
}, [id, state, kw || '']);

// 细网格试点：找出**真能选中**该节点的落点（重叠节点的必需手段）
const selectByScan = async (id) => {
  const pts = await p.evaluate((vid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`);
    if (!n) return [];
    const r = n.getBoundingClientRect(); const out = [];
    for (let fy = 0.10; fy <= 0.92; fy += 0.06) for (let fx = 0.10; fx <= 0.92; fx += 0.06) {
      const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
      const el = document.elementFromPoint(x, y);
      if (!el || !el.closest(`.react-flow__node[data-id="${vid}"]`)) continue;
      if (el.closest('button,a,[role="button"],input,textarea,select,[role="menu"],[contenteditable="true"]')) continue;
      out.push({ x, y, fx: +fx.toFixed(2), fy: +fy.toFixed(2) });
    }
    return out;
  }, id);
  if (!pts.length) return { ok: false, reason: '节点矩形内找不到安全落点' };
  for (const pt of pts) {
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(550);
    const s = await selIds();
    if (s.length === 1 && s[0] === id) return { ok: true, pt, tried: pts.length, first: pts[0] };
  }
  return { ok: false, reason: `试了 ${pts.length} 个落点都没选中`, sample: pts.slice(0, 3) };
};

const makeNode = async (kind) => {
  await deselect();
  const rb = await p.evaluate((nm) => { const e = Array.from(document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button'))
      .find((x) => (x.getAttribute('aria-label') || '').startsWith(nm)); if (!e) return null;
    const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }, kind);
  if (!rb) return { err: `左栏找不到「${kind}」` };
  const pre = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
  await p.mouse.click(rb.cx, rb.cy); await p.waitForTimeout(2800);
  const post = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
  const made = post.filter((x) => !pre.includes(x));
  if (made.length !== 1) return { err: `新建「${kind}」新增 ${made.length} 个` };
  MINE.push(made[0]); return { id: made[0] };
};

const result = { startedAt: new Date().toISOString(), zoom: await zoomOf(), scale: await scaleOf(), cases: [] };
console.log('起始', result.zoom, 'scale', result.scale, '\n');

// ── 缺口③：导演台「进入导演台」按钮在选中态是否真的消失 ──
console.log('=== 缺口③ 导演台「进入导演台」在选中态是否消失 ===');
{
  await deselect();
  const d1 = await dump('node_pxvkay973v', '静息', '进入导演台');
  const sel = await selectByScan('node_pxvkay973v');
  const d3 = await dump('node_pxvkay973v', '选中', '进入导演台');
  console.log('选中结果:', JSON.stringify(sel).slice(0, 200));
  console.log('静息 全文档命中「进入导演台」:', d1.docHits.length, '| 节点内 aria:', JSON.stringify(d1.aria.map((e) => e.a)));
  console.log('选中 全文档命中「进入导演台」:', d3.docHits.length, '| 节点内 aria:', JSON.stringify(d3.aria.map((e) => e.a)));
  for (const h of d3.docHits) console.log('   选中态命中:', JSON.stringify(h.txt), 'inThisNode=', h.inThisNode, 'inSomeNode=', h.inSomeNode, JSON.stringify(h.box), 'vis=', h.vis);
  result.cases.push({ kind: 'director', sel, rest: d1, selected: d3 });
  await reset();
}

// ── 缺口①：文本 1 / 文本 2 细网格试点 ──
console.log('\n=== 缺口① 文本节点的细网格试点 ===');
for (const [id, label] of [['node_3bfb9r79qe', '文本 1'], ['node_aw29cp094x', '文本 2']]) {
  await deselect();
  const sel = await selectByScan(id);
  const d = await dump(id, '选中', 'Rename');
  console.log(`${label} ${id} → ${sel.ok ? '✅ 选中，落点 ' + JSON.stringify(sel.pt) + `（试到第 ${ptsIndex(sel, pts => pts)} 个）` : '❌ ' + sel.reason}`);
  if (d) {
    const ren = d.aria.filter((e) => /^(Rename|Edit)\s/.test(e.a));
    console.log(`   选中态 aria ${d.countAria} 个: ${JSON.stringify(d.aria.map((e) => e.a).slice(0, 6))}`);
    for (const e of ren) console.log(`   🏷 ${JSON.stringify(e.a)} ${e.box.w}x${e.box.h}  顶-卡片顶=${e.dTop} 底-卡片顶=${e.dBottom}`);
    console.log(`   全文档 Rename/Edit 命中: ${d.docHits.length}`);
  }
  result.cases.push({ kind: 'text', id, label, sel, selected: d });
  await reset();
}

// ── 缺口②：新建 图片 / 音频 / 主体，量三态 ──
console.log('\n=== 缺口② 图片 / 音频 / 主体 三态 ===');
for (const kind of ['图片', '音频', '主体']) {
  const r = await makeNode(kind);
  if (r.err) { console.log(`  ❌ ${kind}: ${r.err}`); result.cases.push({ kind, err: r.err }); continue; }
  const rec = { kind, id: r.id, states: [] };
  await deselect();
  rec.states.push(await dump(r.id, 'S1静息', 'Rename'));
  const hp = await p.evaluate((vid) => { const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`); if (!n) return null;
    const b = n.getBoundingClientRect();
    for (const [fx, fy] of [[0.5, 0.5], [0.3, 0.7], [0.7, 0.7], [0.5, 0.8], [0.25, 0.5]]) {
      const x = Math.round(b.x + b.width * fx), y = Math.round(b.y + b.height * fy);
      if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
      const el = document.elementFromPoint(x, y);
      if (el && el.closest(`.react-flow__node[data-id="${vid}"]`) && !el.closest('button,a,[role="button"],input,textarea,[role="menu"],[contenteditable="true"]')) return { x, y };
    } return null; }, r.id);
  if (hp) { await p.mouse.move(hp.x, hp.y); await p.mouse.move(hp.x + 1, hp.y + 1); await p.waitForTimeout(1000); }
  rec.states.push(await dump(r.id, 'S2悬停', 'Rename'));
  const sel = await selectByScan(r.id);
  rec.sel = sel;
  rec.states.push(await dump(r.id, 'S3选中', 'Rename'));
  console.log(`  ${kind} ${r.id} 选中=${sel.ok ? '✅' : '❌ ' + sel.reason}`);
  for (const s of rec.states) {
    if (!s) continue;
    const ren = s.aria.filter((e) => /^(Rename|Edit)\s/.test(e.a));
    console.log(`   ${s.state} 后代 ${s.countDescendants} aria ${s.countAria} tid ${s.countTid} | Rename/Edit ${ren.length} | aria: ${JSON.stringify(s.aria.map((e) => e.a).slice(0, 5))}`);
    for (const e of ren) console.log(`      🏷 ${JSON.stringify(e.a)} ${e.box.w}x${e.box.h} 顶-卡片顶=${e.dTop} 底-卡片顶=${e.dBottom}`);
  }
  result.cases.push(rec);
  await reset();
}

// ── 收尾：先删自建节点，再归位缩放 ──
console.log('\n--- 收尾 ---');
await reset();
if (MINE.length) {
  const { execFileSync } = await import('node:child_process');
  try { console.log(execFileSync('node', ['scripts/jimeng-node-cleanup.mjs', ...MINE], { cwd: process.cwd(), encoding: 'utf8' })); }
  catch (e) { console.log('清理退出码', e.status, (e.stdout || '') + (e.stderr || '')); }
}
for (let r = 0; r < 3; r++) {
  const z = await zoomOf();
  if (z && z.includes('60%')) { console.log('缩放归位 ok:', z); break; }
  await p.click('button[aria-label^="Zoom options"]'); await p.waitForTimeout(700);
  const sel = 'input[data-testid="canvas-zoom-percent-input"]';
  if (await p.$(sel)) { await p.fill(sel, '60'); await p.keyboard.press('Enter'); await p.waitForTimeout(1100); }
  else { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  if (r === 2) console.log('缩放归位 FAILED:', await zoomOf());
}
await reset();
const fin = await coords();
console.log('终态缩放:', await zoomOf(), '| scale:', await scaleOf());
console.log('节点 canvas 坐标:');
for (const [id, c] of Object.entries(fin)) {
  const bs = BASELINE.nodes[id];
  const d = bs ? [+(c[0] - bs.canvas[0]).toFixed(2), +(c[1] - bs.canvas[1]).toFixed(2)] : null;
  console.log(`  ${id} ${JSON.stringify(c)} 基线 ${JSON.stringify(bs ? bs.canvas : null)} Δ=${JSON.stringify(d)}`);
}
console.log('选中数:', (await selIds()).length, '| 节点数:', Object.keys(fin).length);
result.end = { zoom: await zoomOf(), scale: await scaleOf(), coords: fin, selected: await selIds() };
writeFileSync(OUT, JSON.stringify(result, null, 1));
console.log('写入', OUT.pathname);
await b.close();

function ptsIndex(sel, _f) { return sel.tried ? '?' : '?'; }
