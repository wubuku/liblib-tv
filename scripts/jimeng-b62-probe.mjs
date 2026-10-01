// 批次 62 探测：输入卡的真实 DOM 结构，以及 (914,578) 那个点上到底是谁。
//
// 背景：第三轮【B】段两次都栽在 `landed.isInside === false`。
// `focusComposer()` 用的选择器是
//   `[data-testid="prompt-composer"] [contenteditable="true"], [contenteditable="true"]`
// 读回的 `data-testid` 是 **null** ⇒ 走的是**逗号后的兜底分支**，
// 命中了文档里**第一个** `[contenteditable=true]` —— 那多半是画布上别的节点（主体描述 / 文本编辑器）。
//
// 🔑 这是同一个坑的第三次现身：
//   批次 50–55「阴性结果先问：我找的是不是同一个东西」
//   批次 61「点候选节点前必须确认落点属于目标节点」
//   本次「点输入框前必须确认落点属于目标输入框」
// **共用同一条纪律：落点归属要断言，不要推断。**
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const OUT = new URL('./_tmp-b62-probe.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);

const drawerOpen = async () => !!(await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-agent-panel"]');
  return e && e.getBoundingClientRect().width > 1; }));
if (!(await drawerOpen())) {
  const rb = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button'))
    .find((x) => /与\s*AI\s*对话/.test(x.getAttribute('aria-label') || '')); if (!e) return null;
    const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
  if (!rb) { console.error('ABORT: 找不到「与 AI 对话」'); await b.close(); process.exit(1); }
  await p.mouse.click(rb.cx, rb.cy); await p.waitForTimeout(1600);
}
console.log('drawer =', await drawerOpen());

const probe = await p.evaluate(() => {
  const desc = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
    return { tag: e.tagName, tid: e.getAttribute('data-testid'), cls: String(e.className || '').slice(0, 60),
      ce: e.getAttribute('contenteditable'), aria: (e.getAttribute('aria-label') || '').slice(0, 50),
      box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      kids: e.children.length, text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) }; };
  const all = Array.from(document.querySelectorAll('[contenteditable="true"]')).map(desc);
  const pc = document.querySelector('[data-testid="prompt-composer"]');
  // prompt-composer 的后代树（只到 3 层）
  const tree = [];
  const walk = (e, d) => { if (d > 3) return; for (const c of e.children) { tree.push({ depth: d, ...desc(c) }); walk(c, d + 1); } };
  if (pc) walk(pc, 1);
  // 沿 prompt-composer 自己往祖先找，看 contenteditable 挂在哪一层
  let chain = []; let n = pc;
  while (n && n !== document.body) { chain.push(desc(n)); n = n.parentElement; }
  // 在几个候选点上 elementFromPoint 是谁
  const pts = [];
  for (const [x, y] of [[914, 578], [1000, 590], [1100, 600], [960, 570], [1068, 574]]) {
    const t = document.elementFromPoint(x, y);
    pts.push({ x, y, hit: desc(t), inPC: !!(t && pc && pc.contains(t)), isPC: !!(t && pc === t) });
  }
  return { allEditable: all, promptComposer: desc(pc), tree, chain, pts };
});
console.log('\n=== 全文档 [contenteditable=true] ===');
for (const e of probe.allEditable) console.log(' ', JSON.stringify(e));
console.log('\n=== prompt-composer ===', JSON.stringify(probe.promptComposer));
console.log('\n=== prompt-composer 后代（≤3 层）===');
for (const e of probe.tree) console.log(' ', '  '.repeat(e.depth - 1) + JSON.stringify(e));
console.log('\n=== 从 prompt-composer 往上的祖先链 ===');
for (const e of probe.chain) console.log(' ', JSON.stringify(e));
console.log('\n=== 落点探测 ===');
for (const q of probe.pts) console.log(`  (${q.x},${q.y}) 命中=${q.hit ? q.hit.tag + ' tid=' + q.hit.tid + ' cls=' + q.hit.cls : 'null'}  在PC内=${q.inPC} 就是PC=${q.isPC}`);

writeFileSync(OUT, JSON.stringify(probe, null, 1));
console.log('\n写入', OUT.pathname);
await b.close();
