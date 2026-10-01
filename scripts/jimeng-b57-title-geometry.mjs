// 批次 57：把「标题行在卡片上沿之外，**所有节点都这样**」做全类型对照
//
// 手册原文（connect-nodes.md:124-127 / 90-troubleshooting.md:647 /
//           SOURCE_OBSERVATIONS.md §3.40 批次 28）：
//   「📍 **标题行在卡片上沿之外**：实测 `Rename` 按钮 y=169、高 32（169–201），
//     而卡片本体从 **y=200** 才开始 —— 标题行是**浮在卡片上方**的一条，
//     不是卡片内部的一行。（此前批次 18 在编组上观察到同样现象，
//     **本批确认这不是编组特有，所有节点都这样**。）」
//   以及那张 5 元素表的「何时可见」列：标题 / 标记色 / 内容区 = **始终**。
//
// 🔴 为什么这是靶子：
//   「所有节点都这样」这句话的证据只有**两支** —— 批次 18 在**编组**上观察到、
//   批次 28 在**一个空视频节点**上量到。7 种节点类型里只碰了 2 种，
//   而这 2 种都是**卡片较大、内容区完整**的类型。
//   台账里其实已经埋着反例线索，却没被拿来判这条结论：
//     · 主体节点：`Rename 主体 1` **仅在未填描述时存在**，填过描述后变成
//       `Edit 主体 1`（51×21）—— 同一个位置换了另一个元素、换了尺寸；
//       且**选中主体时标题 input 会自动获焦点**（批次 43）。
//     · 导演台节点：台账把 `Rename 导演台` / `Add tags` 记成 **hover 控件**，
//       而批次 28 那张表说它们「**始终**」可见。
//   ⇒ 「几何位置」和「何时可见」两条轴都可能只在被测的那一支上成立。
//
// 方法（全类型 × 三状态，不外推）：
//   S1 静息（无悬停、无选中）／S2 悬停／S3 选中
//   对**每一支**量同一组量：节点容器矩形、标题元素逐字 aria 与矩形、
//   标题底边相对卡片顶边的偏移、卡片内带 aria 元素的可见清单与总数。
//   偏移量同时给屏幕 px 与 canvas px（除以当前 scale）—— 绝对值会随缩放漂移，
//   真正的不变量是**符号与相对量**。
//
// 取材策略（少动共享画布）：
//   画布上现成就有 视频 / 文本×3 / 时间线 / 导演台 四种类型 —— **只读，不新建**；
//   文本出现 3 次，正好当**重复性对照**（同一类型不同实例，几何应当一致）。
//   只新建缺的 图片 / 音频 / 主体 三种，量完按 id 精确删除。
//
// ⚠️ 导演台节点的卡片正中就是「进入导演台」按钮，**点了会离开画布**。
//    所以 `safePoint()` 在节点内做网格扫描，逐点用 elementFromPoint 排除
//    button / a / input / [role=button] / [role=menu] 的落点。
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
import { canvasBaseline, diffNodePositions, pinViewport } from './jimeng-safe-keys.mjs';

const BASELINE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const OTHERS = Object.keys(BASELINE.nodes);
const MINE = [];
const ROWS = [];

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);

const real = (l) => l.filter((x) => !String(x).startsWith('__group-resize-chrome__'));
const ids = async () => real(await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id'))));
const selIds = async () => real(await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id'))));
const statusLine = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['(none)'])[0]);
const scale = () => p.evaluate(() => { const v = document.querySelector('.react-flow__viewport');
  const m = v && /scale\(([-\d.]+)\)/.exec(v.style.transform); return m ? parseFloat(m[1]) : 1; });
const reset = async () => { for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(320); } };

const isEmpty = (x, y) => p.evaluate(([x, y]) => { const el = document.elementFromPoint(x, y); if (!el) return true;
  if (el.closest('.react-flow__node')) return false;
  if (el.closest('button,[role="button"],input,textarea,[role="menu"],[role="listbox"],[data-testid="node-toolbar"],[data-testid="workspace-bottom-dock-frame"],[data-testid="canvas-fixed-toolbar-left-rail"],[data-testid="canvas-top-bar-actions"],[data-testid="canvas-panel-launcher"]')) return false;
  return true; }, [x, y]);
const findEmpty = async () => { for (let y = 110; y <= 630; y += 20) for (let x = 80; x <= 1250; x += 20) { if (x > 1150 && y > 600) continue; if (await isEmpty(x, y)) return { x, y }; } return null; };

// 节点内一个**绝不会点到按钮/输入面**的落点（导演台节点的卡片正中就是「进入导演台」）
const safePoint = async (id) => p.evaluate((vid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`);
  if (!n) return null;
  const r = n.getBoundingClientRect();
  const cands = [];
  for (let fy = 0.5; fy >= 0.12; fy -= 0.06) for (let fx = 0.5; fx >= 0.12; fx -= 0.06) {
    const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
    if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
    const el = document.elementFromPoint(x, y);
    if (!el) continue;
    if (!el.closest(`.react-flow__node[data-id="${vid}"]`)) continue;   // 落到别的节点/浮层
    if (el.closest('button,a,[role="button"],input,textarea,select,[role="menu"],[role="listbox"],[contenteditable="true"]')) continue;
    cands.push({ x, y, d: Math.abs(fx - 0.5) + Math.abs(fy - 0.5) });
  }
  cands.sort((u, v) => u.d - v.d);
  return cands[0] || null;
}, id);

const selectMine = async (id) => {
  const pt = await safePoint(id);
  if (!pt) return 'nopoint';
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(800);
  const s = await selIds();
  if (s.length === 1 && s[0] === id) return 'selected';
  return `selected=${JSON.stringify(s)}`;
};
const deselect = async () => {
  await reset();
  const e = await findEmpty();
  if (e) { await p.mouse.click(e.x, e.y); await p.waitForTimeout(600); }
  const s = await selIds();
  if (s.length === 0) return 'cleared';
  // 兜底：空白点没清掉就逐个 Esc
  for (let i = 0; i < 4 && (await selIds()).length; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(400); }
  return (await selIds()).length === 0 ? 'cleared-esc' : `left=${JSON.stringify(await selIds())}`;
};

// ---- 核心测量 ----
const probe = async (id, state) => {
  const s = await scale();
  const r = await p.evaluate((vid) => {
    const n = document.querySelector(`.react-flow__node[data-id="${vid}"]`);
    if (!n) return null;
    const RR = (e) => { const b = e.getBoundingClientRect();
      return { x: +b.x.toFixed(1), y: +b.y.toFixed(1), w: +b.width.toFixed(1), h: +b.height.toFixed(1), t: +b.top.toFixed(1), b: +b.bottom.toFixed(1) }; };
    const visible = (e) => { const b = e.getBoundingClientRect(); return b.width > 1 && b.height > 1; };
    // 「带 aria 的元素」= 有非空 aria-label 的元素；另单列 data-testid
    const ariaEls = Array.from(n.querySelectorAll('[aria-label]')).filter((e) => (e.getAttribute('aria-label') || '').length > 0);
    const tidEls = Array.from(n.querySelectorAll('[data-testid]'));
    const pick = (re) => ariaEls.find((e) => re.test(e.getAttribute('aria-label'))) || null;
    const titleEl = pick(/^(Rename|Edit)\s/) || null;
    const tagsEl = n.querySelector('[data-testid="flow-node-selected-tag"]') || pick(/^Edit tags:/) || null;
    const plus = { before: !!n.querySelector('[data-testid="flow-node-target-connection-menu-button"]'),
                   after: !!n.querySelector('[data-testid="flow-node-source-connection-menu-button"]') };
    return {
      nodeAria: n.getAttribute('aria-label'),
      nodeCls: Array.from(n.classList).filter((c) => c.startsWith('react-flow__node-')).join(','),
      node: RR(n),
      // 总数口径与批次 28 对齐：带 aria-label 的 + 带 data-testid 的
      countAria: ariaEls.length, countTid: tidEls.length,
      title: titleEl ? { aria: titleEl.getAttribute('aria-label'), vis: visible(titleEl), ...RR(titleEl) } : null,
      tags: tagsEl ? { aria: tagsEl.getAttribute('aria-label') || tagsEl.getAttribute('data-testid'), vis: visible(tagsEl), ...RR(tagsEl) } : null,
      plus,
      ariaList: ariaEls.map((e) => { const bb = e.getBoundingClientRect();
        return { a: e.getAttribute('aria-label'), vis: bb.width > 1 && bb.height > 1, y: +bb.y.toFixed(1), h: +bb.height.toFixed(1) }; }),
      selected: n.classList.contains('selected'),
    };
  }, id);
  if (!r) return null;
  // 归一到 canvas px：新建节点会触发自动适配，绝对 px 会随 scale 漂移，不变量是相对量
  const norm = (v) => (v === null || v === undefined ? null : +(v / s).toFixed(1));
  const titleB = r.title && r.title.vis ? r.title.b - r.node.t : null;
  const titleT = r.title && r.title.vis ? r.title.t - r.node.t : null;
  const row = {
    id, state, scale: s, type: r.nodeCls, nodeAria: r.nodeAria,
    node: `${r.node.w}x${r.node.h}`,
    countAria: r.countAria, countTid: r.countTid,
    title: r.title ? { aria: r.title.aria, vis: r.title.vis, size: `${r.title.w}x${r.title.h}` } : null,
    titleVis: r.title ? r.title.vis : false,
    tagsVis: r.tags ? r.tags.vis : false,
    // 判据：标题底边相对卡片顶边的偏移。>0 表示底部压在卡片内，<0 表示完全在卡片上方
    dBottom: titleB === null ? null : norm(titleB),
    dTop: titleT === null ? null : norm(titleT),
    titleH: r.title && r.title.vis ? norm(r.title.h) : null,
    plus: r.plus, selected: r.selected,
    ariaList: r.ariaList,
  };
  ROWS.push(row);
  return row;
};

// ---- 左栏新建 ----
const railBtns = async () => p.evaluate(() => Array.from(document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button')).map((e) => e.getAttribute('aria-label')));
const makeNode = async (kind) => {
  await reset(); await deselect();
  const rb = await p.evaluate((nm) => { const e = Array.from(document.querySelectorAll('aside[data-testid="canvas-fixed-toolbar-left-rail"] button'))
      .find((x) => (x.getAttribute('aria-label') || '').startsWith(nm)); if (!e) return null;
    const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }, kind);
  if (!rb) return { err: `左栏找不到「${kind}」` };
  const pre = await ids();
  await p.mouse.click(rb.cx, rb.cy); await p.waitForTimeout(2600);
  const post = await ids();
  const made = post.filter((x) => !pre.includes(x));
  if (made.length !== 1) return { err: `新建「${kind}」后新增 ${made.length} 个节点：${JSON.stringify(made)}` };
  MINE.push(made[0]);
  return { id: made[0] };
};

// ---- 三状态测量 ----
const threeStates = async (id, label) => {
  await deselect();
  await probe(id, 'S1静息');
  const hp = await safePoint(id);
  if (hp) { await p.mouse.move(hp.x, hp.y); await p.mouse.move(hp.x + 1, hp.y + 1); await p.waitForTimeout(900); }
  await probe(id, 'S2悬停');
  const st = await selectMine(id);
  if (st !== 'selected') console.log(`  ⚠️ ${label} 选中失败：${st}`);
  await probe(id, 'S3选中');
  return st;
};

// ================= 主流程 =================
console.log('=== 批次 57：标题几何全类型对照 ===\n');
const base0 = await canvasBaseline(p);
console.log('基线状态行:', base0.status, '| 缩放:', base0.zoom, '| 他人节点:', base0.nodes.length);
if (base0.nodes.length !== 6) { console.error('ABORT: 他人节点数不是 6，先人工确认'); process.exit(2); }
console.log('左栏按钮:', JSON.stringify(await railBtns()), '\n');

// ── Phase 0：现成节点的**只读**静息态（一个都不点）──
console.log('--- Phase 0：现成 6 节点 · 只读静息态（不点击）---');
for (const n of base0.nodes) await probe(n.id, 'S0只读静息');

// ── Phase 1：现成节点的三状态（点选但不改内容，逐个 Esc 复位）──
console.log('\n--- Phase 1：现成节点 · 悬停/选中态（单点，绝不点按钮）---');
for (const n of base0.nodes) { console.log(`  ${n.id} ${JSON.stringify(n.title)}`); await threeStates(n.id, n.title); }

// ── Phase 2：补齐缺的 3 种类型 ──
console.log('\n--- Phase 2：新建 图片 / 音频 / 主体 ---');
for (const kind of ['图片', '音频', '主体']) {
  const r = await makeNode(kind);
  if (r.err) { console.log(`  ❌ ${kind}: ${r.err}`); continue; }
  console.log(`  ✅ ${kind} → ${r.id}  缩放=${await scale()}  ${await statusLine()}`);
  await threeStates(r.id, kind);
}

// ── 输出 ──
console.log('\n================ 逐行读数 ================');
for (const r of ROWS) {
  const cls = r.type.replace('react-flow__node-', '') || '(无)';
  const T = r.title ? `${r.title.vis ? '可见' : '不可见'} ${r.title.aria} ${r.title.size}` : '**无标题元素**';
  console.log(`${r.state.padEnd(10)} ${String(cls).padEnd(9)} ${r.id}  卡片 ${String(r.node).padEnd(9)} aria元素 ${String(r.countAria).padStart(2)} tid ${String(r.countTid).padStart(2)} ⊕ ${r.plus.before ? '1' : '0'}${r.plus.after ? '1' : '0'} | 标题: ${T}`);
  if (r.titleVis) console.log(`${''.padEnd(10)} ${''.padEnd(9)} └ 标题底-卡片顶 = ${r.dBottom} canvas px｜标题高 ${r.titleH}｜顶-顶 = ${r.dTop}｜scale ${r.scale}`);
}
console.log('\n================ 逐类型结论 ================');
const byType = {};
for (const r of ROWS) { const k = (r.type || '(无)').replace('react-flow__node-', ''); (byType[k] ||= []).push(r); }
for (const [k, list] of Object.entries(byType)) {
  const s1 = list.filter((r) => r.state === 'S0只读静息' || r.state === 'S1静息');
  const geo = s1.map((r) => ({ id: r.id, title: r.title ? r.title.aria : null, vis: r.titleVis, d: r.dBottom }));
  const verdict = s1.every((r) => r.dBottom !== null && r.dBottom <= 0) ? '标题完全在卡片上方'
    : s1.every((r) => r.dBottom !== null) ? '标题压在卡片顶边上（跨线）' : '**静息态无可见标题元素**';
  console.log(`${k.padEnd(10)} ${verdict}  ${JSON.stringify(geo)}`);
}

// ── 收尾：先删自建节点，再归位缩放 ──
console.log('\n--- 收尾 ---');
await reset();
if (MINE.length) {
  console.log('待删自建节点:', JSON.stringify(MINE));
  const { execFileSync } = await import('node:child_process');
  try {
    console.log(execFileSync('node', ['scripts/jimeng-node-cleanup.mjs', ...MINE], { cwd: process.cwd(), encoding: 'utf8' }));
  } catch (e) { console.log('清理输出(退出码', e.status, '):\n' + (e.stdout || '') + (e.stderr || '')); }
}
await p.waitForTimeout(800);
const after = await canvasBaseline(p);
console.log('清理后状态行:', after.status, '| 剩余节点:', after.nodes.length, '| 缩放:', after.zoom);
const drifted = await diffNodePositions(p, Object.fromEntries(BASELINE.nodes.map((k, v) => [k, v.canvas])));
console.log('他人节点位置偏离:', JSON.stringify(drifted));
await b.close();
process.exit(0);
