// 批次 107 · e 轮：把「怎么进文本编辑态」逐个入口试一遍，并记录哪一个真能进。
//
// 已知：
//   · `edit-text-node.md:18/25/173` 写了两条正路：**双击节点主体** /
//     **在已选中的节点上再单击一次**；
//   · `help-and-shortcuts.md` 的 F 键表写「文本 + F → `text-editor-fullscreen-dialog` ✅」。
// 实测：**两条都不work**（b 轮按 F 无 dialog；d 轮 `p.mouse.dblclick` 无 contenteditable）。
//
// ⇒ 本轮**不假设是哪一个坏了**，而是把候选入口逐个跑，每跑一个都记三件事：
//   ① 有没有出现可编辑面（`[contenteditable]` / `textarea`，且在**我那个节点里**）；
//   ② 节点自身是否还 selected；
//   ③ 焦点落在哪。
// 顺带记一条**可复用的正向读数**（与编辑态无关，独立成立）：
//   `.md` 上传出来的正文**直接是真语义标签**，不是纯文本：
//     `H1`「一级标题行」`163×24` → `H2`「二级标题行」`163×17`
//     → `H3`「三级标题行」`163×14` → `P`「普通正文行。」`163×13`
//   ⇒ **字号随层级递减 24 → 17 → 14 → 13**，这给了「层级」一个肉眼可判的读数。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), selfId: 'node_gmvz7secas' };
const SELF = out.selfId;
const save = () => writeFileSync(new URL('./_tmp-b107e.json', import.meta.url), JSON.stringify(out, null, 1));

const safeEval = async (fn, arg, tries = 8) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

const probe = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const ce = Array.from(n.querySelectorAll('[contenteditable="true"],textarea')).map((e) => {
    const q = e.getBoundingClientRect();
    return { tag: e.tagName, tid: e.getAttribute('data-testid'), w: Math.round(q.width), h: Math.round(q.height) };
  });
  const a = document.activeElement;
  return { ce, n: ce.length, sel: n.classList.contains('selected'),
    active: a ? `${a.tagName}${a.getAttribute('data-testid') ? '[' + a.getAttribute('data-testid') + ']' : ''}${a.isContentEditable ? '(ce)' : ''}` : null,
    // 编辑态工具条：只在节点上方浮出，8 个按钮
    toolbar: Array.from(document.querySelectorAll('[data-testid]'))
      .filter((e) => /toolbar/i.test(e.getAttribute('data-testid') || ''))
      .map((e) => ({ tid: e.getAttribute('data-testid'), inside: n.contains(e), n: e.querySelectorAll('button,[role=button]').length,
        aria: Array.from(e.querySelectorAll('button,[role=button]')).map((x) => x.getAttribute('aria-label') || (x.innerText || '').trim()).filter(Boolean) }))
      .filter((x) => x.n > 0) };
}, SELF);

const spot = async () => safeEval((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  const others = Array.from(document.querySelectorAll('.react-flow__node')).filter((e) => e.getAttribute('data-id') !== i)
    .map((e) => { const q = e.getBoundingClientRect(); return { x: q.x, y: q.y, w: q.width, h: q.height }; });
  for (let fy = 0.35; fy <= 0.8; fy += 0.05) for (let fx = 0.2; fx <= 0.8; fx += 0.05) {
    const x = r.x + r.width * fx, y = r.y + r.height * fy;
    if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
    const el = document.elementFromPoint(x, y);
    if (!el || !(el === n || n.contains(el))) continue;
    if (others.some((o) => x >= o.x && x <= o.x + o.w && y >= o.y && y <= o.y + o.h)) continue;
    return { x: Math.round(x), y: Math.round(y) };
  }
  return { __err: 'no-safe-spot' };
}, SELF);

out.start = await probe();
log('起点：', JSON.stringify({ n: out.start.n, sel: out.start.sel, active: out.start.active }));
const S = await spot();
out.spot = S;
log('落点：', JSON.stringify(S));
if (S.__err) { log('🔴 无安全落点'); save(); await b.close(); process.exit(1); }

out.tries = [];
async function attempt(name, fn) {
  log(`\n>>> 尝试：${name}`);
  const before = await probe();
  await fn();
  await p.waitForTimeout(1600);
  const after = await probe();
  const rec = { name, before: { n: before.n, sel: before.sel, active: before.active },
    after: { n: after.n, sel: after.sel, active: after.active, toolbar: after.toolbar },
    entered: after.n > 0 };
  out.tries.push(rec);
  log('   前：', JSON.stringify(rec.before));
  log('   后：', JSON.stringify({ n: rec.after.n, sel: rec.after.sel, active: rec.after.active }));
  if (after.toolbar.length) log('   工具条：', JSON.stringify(after.toolbar));
  log('   进入编辑态 =', rec.entered ? '✅' : '🔴');
  save();
  return rec.entered;
}

// ① 在已选中的节点上再单击一次
if (await attempt('已选中 → 再单击一次', async () => {
  await p.mouse.move(S.x, S.y); await p.waitForTimeout(400);
  await p.mouse.click(S.x, S.y);
})) { log('✅ 正路一可用，停止试其余入口'); }
else if (await attempt('双击（down/up 两次，间隔 90ms）', async () => {
  await p.mouse.move(S.x, S.y); await p.waitForTimeout(400);
  await p.mouse.down(); await p.waitForTimeout(40); await p.mouse.up();
  await p.waitForTimeout(90);
  await p.mouse.down(); await p.waitForTimeout(40); await p.mouse.up();
})) { log('✅ 正路二可用'); }
else {
  // ③ 先确保选中再试双击
  const sel = await p.evaluate((i) => { const e = document.querySelector(`.react-flow__node[data-id="${i}"]`); return e ? e.classList.contains('selected') : null; }, SELF);
  log('\n（当前 selected =', sel, '；若为 false 先点空白取消再单击选中）');
  if (!sel) {
    await p.keyboard.press('Escape'); await p.waitForTimeout(700);
    await p.mouse.move(S.x, S.y); await p.waitForTimeout(400); await p.mouse.click(S.x, S.y); await p.waitForTimeout(1000);
  }
  await attempt('Esc 后重新选中 → 双击', async () => {
    await p.mouse.move(S.x, S.y); await p.waitForTimeout(400);
    await p.mouse.dblclick(S.x, S.y, { delay: 60 });
  });
  const g = await keyGuard(p);
  out.guardEnter = g;
  log('\nkeyGuard（按 Enter 前）：', JSON.stringify(g));
  if (g.safe) {
    await attempt('按 Enter', async () => { await p.keyboard.press('Enter'); });
  }
  // 悬停看有没有编辑提示
  log('\n>>> 悬停读数');
  await p.mouse.move(S.x, S.y); await p.waitForTimeout(1200);
  out.hover = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    return { cursor: getComputedStyle(n).cursor,
      bodyCursor: (() => { const b = n.querySelector('[data-testid="text-flow-node-full"]'); return b ? getComputedStyle(b).cursor : null; })(),
      anyEditable: Array.from(n.querySelectorAll('*')).filter((e) => e.isContentEditable).length,
      title: getComputedStyle(n).getPropertyValue('cursor') };
  }, SELF);
  log('悬停：', JSON.stringify(out.hover));
}

out.end = await probe();
log('\n终点：', JSON.stringify({ n: out.end.n, sel: out.end.sel, active: out.end.active }));
out.anyWorked = out.tries.some((t) => t.entered);
log('本轮是否有任何入口成功 =', out.anyWorked);
save();
await b.close();
