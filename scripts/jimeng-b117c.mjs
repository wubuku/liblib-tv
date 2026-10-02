// 批次 117 · c 轮：在**干净状态**下专门测「标题行有没有变成输入框」。
//
// a 轮把三件事混在一起了，这轮拆开：
//
//   · ③ 双击**标题行** ⇒ 确实进入了编辑态，但进的是 **正文**编辑器：
//       新增 `DIV contenteditable aria="Text"` @ `260,280,192×37`
//       —— 注意它在**卡片位置**（y=280），而标题行在 `y=248`。
//     ⇒ 批次 80 问的是「**标题**变成输入框没有」，它找到的应该是**标题行位置**的输入面。
//     ⇒ **A、B 两个判据必须分开**（下面就是）。
//
//   · ④⑤⑥ 全部**无效**：③ 进了正文编辑态之后，标题的 `Rename` 按钮**直接消失**
//     （④ 报 `no-rename`）⇒ 那三轮的动作**根本没发生**，焦点停在正文编辑器里。
//     ⇒ 「护栏中止的是这一步动作」；但这里更该记的是：
//       **动作前置条件（按钮在不在）必须在每轮开始时现算并断言**，不能沿用上一轮的状态。
//
// 本轮每一步都先断言前置条件，并读**标题行矩形内**有没有输入面。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const SELF = process.env.SELF_ID;
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c', self: SELF };
const save = () => writeFileSync(new URL('./_tmp-b117c.json', import.meta.url), JSON.stringify(out, null, 1));

const nodeState = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  const rect = (e) => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; };
  const t = n.querySelector('[data-testid="flow-node-title"]');
  const ce = Array.from(document.querySelectorAll('[contenteditable]')).map((e) => { const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), rect: [r.x, r.y, r.width, r.height].map(Math.round), inNode: !!e.closest('.react-flow__node') }; });
  const inputs = Array.from(document.querySelectorAll('input,textarea')).map((e) => { const r = e.getBoundingClientRect();
    return { tag: e.tagName, aria: e.getAttribute('aria-label'), type: e.getAttribute('type'),
      rect: [r.x, r.y, r.width, r.height].map(Math.round) }; });
  const a = document.activeElement;
  return {
    selected: n.classList.contains('selected'),
    inner: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 100),
    titleRect: t ? rect(t) : null,
    titleText: t ? (t.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20) : null,
    renameBtn: (() => { const e = Array.from(n.querySelectorAll('button')).find((x) => /^Rename\b/.test(x.getAttribute('aria-label') || ''));
      return e ? { aria: e.getAttribute('aria-label'), rect: rect(e) } : null; })(),
    tids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    contenteditables: ce, inputs,
    focus: a ? { tag: a.tagName, aria: a.getAttribute('aria-label'), tid: a.getAttribute('data-testid'),
      isCE: a.isContentEditable === true, isInputLike: a.tagName === 'INPUT' || a.tagName === 'TEXTAREA' || a.isContentEditable === true } : null,
  };
}, SELF);

out.nodeExists = await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), SELF);
log('节点存在？', out.nodeExists);
if (!out.nodeExists) { log('⛔ 中止'); await b.close(); process.exit(3); }

// ---- 0. 复位到「选中但未编辑」状态 ----
log('\n=== 复位到干净状态 ===');
for (let k = 0; k < 3; k++) {
  const st = await nodeState();
  if (!st.focus || !st.focus.isInputLike) { log(`  第 ${k + 1} 轮：焦点不在输入面（${JSON.stringify(st.focus)}）⇒ 干净`); break; }
  log(`  第 ${k + 1} 轮：焦点在 ${st.focus.tag}/${st.focus.aria} ⇒ Esc 退出`);
  await p.keyboard.press('Escape'); await p.waitForTimeout(900);
}
await p.waitForTimeout(1200);
out.clean = await nodeState();
log('\n干净状态：'); log(JSON.stringify({ selected: out.clean.selected, titleRect: out.clean.titleRect,
  renameBtn: out.clean.renameBtn, focus: out.clean.focus, ce: out.clean.contenteditables, inputs: out.clean.inputs }, null, 1));
save();

// ---- 判据 A / B 分开 ----
const judge = (st, tag) => {
  // B：标题行矩形内有没有输入面（标题编辑态）
  const tr = st.titleRect;
  const inTitle = (list) => tr ? list.filter((x) => { const r = x.rect;
    return r[0] >= tr[0] - 4 && r[0] + r[2] <= tr[0] + tr[2] + 8 && r[1] >= tr[1] - 6 && r[1] + r[3] <= tr[1] + tr[3] + 8; }) : [];
  const bInputs = [...inTitle(st.inputs).map((x) => ({ kind: 'input', ...x })), ...inTitle(st.contenteditables).map((x) => ({ kind: 'ce', ...x }))];
  // A：正文编辑态（contenteditable 出现在卡片位置，y 明显大于标题行）
  const aEditors = st.contenteditables.filter((x) => tr && x.rect[1] > tr[1] + tr[3]);
  return { tag, B标题编辑面: bInputs, A正文编辑器: aEditors.map((x) => ({ aria: x.aria, rect: x.rect })),
    focus: st.focus, 进标题编辑态: bInputs.length > 0, 进正文编辑态: aEditors.length > 0 };
};

out.trials = [];
async function trial(tag, act) {
  // 🔴 每轮**先断言前置条件**并把状态复位，不沿用上一轮
  for (let k = 0; k < 3; k++) {
    const st = await nodeState();
    if (st.focus && st.focus.isInputLike) { await p.keyboard.press('Escape'); await p.waitForTimeout(900); } else break;
  }
  await p.waitForTimeout(1000);
  const pre = await nodeState();
  log(`\n──────── ${tag} ────────`);
  log('  前置：selected=', pre.selected, '｜Rename 钮=', pre.renameBtn ? pre.renameBtn.aria : '（无）', '｜焦点=', JSON.stringify(pre.focus));
  if (!pre.renameBtn) { log('  ⛔ Rename 按钮不在 ⇒ 本轮动作无法发生，跳过'); out.trials.push({ tag, skipped: 'no-rename-btn' }); save(); return null; }
  const r = await act(pre);
  const t0 = await nodeState(); await p.waitForTimeout(1200);
  const t1 = await nodeState(); await p.waitForTimeout(2500);
  const t2 = await nodeState();
  const j0 = judge(t0, tag + ' t0'), j1 = judge(t1, tag + ' t+1.2s'), j2 = judge(t2, tag + ' t+3.7s');
  const rec = { tag, act: r || null, pre: { selected: pre.selected, renameBtn: pre.renameBtn },
    j0, j1, j2, 三次一致: j2.进标题编辑态 === j1.进标题编辑态 && j1.进标题编辑态 === j0.进标题编辑态,
    进标题编辑态: j2.进标题编辑态, 进正文编辑态: j2.进正文编辑态, 焦点: t2.focus,
    末态tids: t2.tids, 末态inner: t2.inner };
  out.trials.push(rec);
  log('  三次（t0/t1.2s/t3.7s）标题编辑面数：', j0.B标题编辑面.length, '/', j1.B标题编辑面.length, '/', j2.B标题编辑面.length);
  log('  三次 正文编辑器数：', j0.A正文编辑器.length, '/', j1.A正文编辑器.length, '/', j2.A正文编辑器.length);
  log('  判定：进标题编辑态=', rec.进标题编辑态, '｜进正文编辑态=', rec.进正文编辑态, '｜三次一致=', rec.三次一致);
  if (j2.B标题编辑面.length) log('  标题编辑面逐字：', JSON.stringify(j2.B标题编辑面));
  save();
  return rec;
}

const ptOfRename = async () => p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  const btn = Array.from(n.querySelectorAll('button')).find((e) => /^Rename\b/.test(e.getAttribute('aria-label') || ''));
  if (!btn) return { __err: 'no-rename' };
  const r = btn.getBoundingClientRect();
  for (let y = Math.ceil(r.y); y < r.y + r.height; y += 2)
    for (let x = Math.ceil(r.x); x < r.x + r.width; x += 2) { if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
      const el = document.elementFromPoint(x, y); if (el && (el === btn || btn.contains(el))) return { x, y, aria: btn.getAttribute('aria-label') }; }
  return { __err: 'no-clickable' }; }, SELF);

// ① 单击 Rename 钮
await trial('①单击Rename钮', async () => { const pt = await ptOfRename(); if (pt.__err) return pt; await p.mouse.click(pt.x, pt.y); return pt; });
// ② 双击 Rename 钮  ← 批次 80 没试过
await trial('②双击Rename钮', async () => { const pt = await ptOfRename(); log('  落点：', JSON.stringify(pt)); if (pt.__err) return pt; await p.mouse.dblclick(pt.x, pt.y); return pt; });
// ③ 单击 Rename 钮 → Enter
await trial('③单击后Enter', async () => { const pt = await ptOfRename(); if (pt.__err) return pt;
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(800);
  const g = await keyGuard(p); log('  按 Enter 前守卫：', g.safe ? '✅' : 'ⓘ', g.where || '');
  await p.keyboard.press('Enter'); return { pt, guard: { safe: g.safe, where: g.where } }; });
// ④ 单击 Rename 钮 → Space
await trial('④单击后Space', async () => { const pt = await ptOfRename(); if (pt.__err) return pt;
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(800); await p.keyboard.press(' '); return pt; });
// ⑤ 单击 Rename 钮 → 双击 Rename 钮（连着试：单击已把焦点放上去）
await trial('⑤单击后立刻双击', async () => { const pt = await ptOfRename(); if (pt.__err) return pt;
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(500); await p.mouse.dblclick(pt.x, pt.y); return pt; });

out.verdict = out.trials.map((t) => t.skipped ? { 试: t.tag, 跳过: t.skipped }
  : { 试: t.tag, 进标题编辑态: t.进标题编辑态, 进正文编辑态: t.进正文编辑态, 三次一致: t.三次一致, 焦点: t.焦点 && (t.焦点.aria || t.焦点.tag) });
log('\n=== 判定汇总 ==='); log(JSON.stringify(out.verdict, null, 1));
out.anyTitle = out.trials.filter((t) => t.进标题编辑态).map((t) => t.tag);
out.anyBody = out.trials.filter((t) => t.进正文编辑态).map((t) => t.tag);
log('\n  ⇒ 进「标题编辑态」的操作：', JSON.stringify(out.anyTitle));
log('  ⇒ 进「正文编辑态」的操作：', JSON.stringify(out.anyBody));
out.end = { nodes: await p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]),
  credits: await p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label')) };
log('终点：', JSON.stringify(out.end));
save();
log('\nDONE c');
process.exit(0);
