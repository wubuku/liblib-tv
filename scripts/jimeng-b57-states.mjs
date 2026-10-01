// 批次 57 实验二：两件事一次做完
//
// ① 【判责】视频 1 疑似被移了 Δ=(385,385)。我的脚本里**没有任何 down→move→up
//    的拖拽路径**（只有 mouse.move / mouse.click，click 不会产生位移）。
//    385,385 是完全相等的整数对 —— 程序化 setNodes 才会这样，人手拖拽几乎不可能。
//    但「几乎不可能」不是证据。本实验用**完全相同的点击序列**跑一遍，
//    前后各读一次 canvas 坐标：坐标不变 ⇒ 这条代码路径洗清移动嫌疑。
//
// ② 【补测】批次 57 主脚本的逐行读数被输出流截掉了，而结论段已经暴露
//    「静息态全篇文档 0 个 ^(Rename|Edit) 元素」。必须拿到 S1/S2/S3
//    三态下**完整的 aria 清单**，才能判清是「标题真的不存在」还是「读数方法错了」。
//    → 这次全部写进 JSON 文件，不再依赖终端输出流。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const OUT = new URL('./_tmp-b57-out.json', import.meta.url);

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);
const reset = async () => { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); } };

const scaleOf = () => p.evaluate(() => { const v = document.querySelector('.react-flow__viewport');
  const m = v && /scale\(([-\d.]+)\)/.exec(v.style.transform); return m ? +(+m[1]).toFixed(4) : null; });
const zoomOf = () => p.evaluate(() => (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label'));
const coords = () => p.evaluate(() => Object.fromEntries(Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
  return [e.getAttribute('data-id'), m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null];
})));
const selIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));

// 节点内一个绝不会点到按钮/输入面的落点
const safePoint = (id) => p.evaluate((vid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  const c = [];
  for (let fy = 0.5; fy >= 0.12; fy -= 0.06) for (let fx = 0.5; fx >= 0.12; fx -= 0.06) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
    const el = document.elementFromPoint(x, y);
    if (!el || !el.closest(`.react-flow__node[data-id="${vid}"]`)) continue;
    if (el.closest('button,a,[role="button"],input,textarea,select,[role="menu"],[contenteditable="true"]')) continue;
    c.push({ x, y, d: Math.abs(fx - 0.5) + Math.abs(fy - 0.5) });
  }
  c.sort((u, v) => u.d - v.d); return c[0] || null;
}, id);
const isEmpty = (x, y) => p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y); if (!el) return true;
  if (el.closest('.react-flow__node')) return false;
  if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"]')) return false;
  return true; }, [x, y]);
const findEmpty = async () => { for (let y = 110; y <= 630; y += 20) for (let x = 80; x <= 1250; x += 20) { if (x > 1150 && y > 600) continue; if (await isEmpty(x, y)) return { x, y }; } return null; };
const deselect = async () => { await reset(); const e = await findEmpty();
  if (e) { await p.mouse.click(e.x, e.y); await p.waitForTimeout(600); }
  if ((await selIds()).length) { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); } }
  return (await selIds()).length === 0; };

// 一次完整读数：卡片矩形 + 子树内全部带 aria-label 的元素 + 全文档 Rename/Edit 元素
const dump = (id, state) => p.evaluate(([vid, st]) => {
  const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`);
  if (!n) return null;
  const RR = (e) => { const r = e.getBoundingClientRect(); return { x: +r.x.toFixed(1), y: +r.y.toFixed(1), w: +r.width.toFixed(1), h: +r.height.toFixed(1), b: +r.bottom.toFixed(1) }; };
  const ariaEls = Array.from(n.querySelectorAll('[aria-label]')).filter((e) => (e.getAttribute('aria-label') || '').length > 0);
  const descAll = Array.from(n.querySelectorAll('*'));
  const node = RR(n);
  return {
    state: st, id: vid,
    cls: Array.from(n.classList).filter((c) => c.startsWith('react-flow__node-')).join(','),
    nodeAria: n.getAttribute('aria-label'), node, selected: n.classList.contains('selected'),
    countDescendants: descAll.length, countAria: ariaEls.length,
    countTid: n.querySelectorAll('[data-testid]').length,
    aria: ariaEls.map((e) => { const r = e.getBoundingClientRect();
      return { a: e.getAttribute('aria-label'), t: e.getAttribute('data-testid'),
        box: RR(e), vis: r.width > 1 && r.height > 1,
        dTop: +((r.top - node.y) / 1).toFixed(1), dBottom: +((r.bottom - node.y) / 1).toFixed(1) }; }),
    // 全文档里所有 ^(Rename|Edit) —— 用来判「是不是 portal 挂出去了」
    docRename: Array.from(document.querySelectorAll('[aria-label]'))
      .filter((e) => /^(Rename|Edit)\s/.test(e.getAttribute('aria-label') || ''))
      .map((e) => ({ a: e.getAttribute('aria-label'), inThisNode: !!e.closest(`.react-flow__node[data-id="${vid}"]`),
        inSomeNode: (e.closest('.react-flow__node') || {}).getAttribute?.('data-id') || null,
        box: RR(e), vis: e.getBoundingClientRect().width > 1,
        parent: e.parentElement ? e.parentElement.tagName + '.' + String(e.parentElement.className || '').split(' ')[0] : null })),
  };
}, [id, state]);

const result = { startedAt: new Date().toISOString(), zoom: await zoomOf(), scale: await scaleOf(), nodes: [], blame: [] };
console.log('起始缩放', result.zoom, 'scale', result.scale);

const all = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
  const t = e.querySelector('[data-testid="flow-node-title"]');
  return { id: e.getAttribute('data-id'), canvas: m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null,
    title: t ? (t.innerText || '').trim() : null, cls: Array.from(e.classList).filter((c) => c.startsWith('react-flow__node-')).join(',') };
}));

for (const n of all) {
  console.log(`\n>>> ${n.id} [${n.cls}] ${JSON.stringify(n.title)} canvas=${JSON.stringify(n.canvas)}`);
  const rec = { ...n, states: [] };
  // S1 静息
  const ok1 = await deselect();
  rec.states.push(await dump(n.id, 'S1静息'));
  // S2 悬停
  const hp = await safePoint(n.id);
  if (hp) { await p.mouse.move(hp.x, hp.y); await p.mouse.move(hp.x + 1, hp.y + 1); await p.waitForTimeout(1000); }
  rec.states.push(await dump(n.id, 'S2悬停'));
  // S3 选中（单点，且落点已排除按钮）
  if (hp) { await p.mouse.click(hp.x, hp.y); await p.waitForTimeout(900); }
  rec.selAfterClick = await selIds();
  rec.states.push(await dump(n.id, 'S3选中'));
  await reset();
  result.nodes.push(rec);
  for (const s of rec.states) {
    const ren = s && s.aria.filter((e) => /^(Rename|Edit)\s/.test(e.a));
    console.log(`   ${s && s.state} 后代 ${s && s.countDescendants} | aria ${s && s.countAria} | tid ${s && s.countTid} | 本节点内 Rename/Edit: ${ren ? ren.length : '?'} | 全文档 Rename/Edit: ${s ? s.docRename.length : '?'}`);
    if (ren) for (const e of ren) console.log(`        ${JSON.stringify(e.a)}  ${e.box.w}x${e.box.h} @y${e.box.y}  顶-卡片顶=${e.dTop} 底-卡片顶=${e.dBottom}`);
  }
}

// 判责：整轮点选跑完后，canvas 坐标有没有动过
const after = await coords();
const before = Object.fromEntries(all.map((n) => [n.id, n.canvas]));
const moved = [];
for (const id of Object.keys(before)) {
  const a = after[id], e = before[id];
  if (!a || !e) { moved.push({ id, note: '节点消失' }); continue; }
  const d = [+(a[0] - e[0]).toFixed(2), +(a[1] - e[1]).toFixed(2)];
  if (Math.abs(d[0]) > 0.01 || Math.abs(d[1]) > 0.01) moved.push({ id, before: e, after: a, delta: d });
}
result.blame = { baselineRecorded: Object.fromEntries(Object.entries(BASELINE.nodes).map(([k, v]) => [k, v.canvas])),
  beforeThisRun: before, afterThisRun: after, movedByThisRun: moved };
console.log('\n================ 判责 ================');
console.log('本轮 move/click 造成的位移:', JSON.stringify(moved));
for (const n of all) {
  const bse = BASELINE.nodes[n.id];
  if (!bse) continue;
  const a = after[n.id];
  const d = [+(a[0] - bse.canvas[0]).toFixed(2), +(a[1] - bse.canvas[1]).toFixed(2)];
  console.log(`  ${n.id} ${JSON.stringify(n.title)} 基线 ${JSON.stringify(bse.canvas)} → 现在 ${JSON.stringify(a)}  Δ=${JSON.stringify(d)}`);
}
result.endZoom = await zoomOf();
writeFileSync(OUT, JSON.stringify(result, null, 1));
console.log('\n写入', OUT.pathname, '| 终态缩放', result.endZoom);
await b.close();
