// 批次 115 · b 轮：把落点修正到 **`BUTTON[Rename 主体 1]`** 本身。
//
// a 轮的两条读数（先看，它们各自都有用）：
//   ① 落点 `261,249` 命中标题元素的**空白处**（图标左侧），**不是**里面的
//      `BUTTON aria="Rename 主体 1"`（`36×32@280,248`）⇒ 这次点击**根本没触发改名**，
//      所以「没获焦」是**我点错了地方**，不是「不自动获焦」。
//      （这正是批次 97 栽的地方：它落点落在节点中心的空态导入区。）
//   ② 🆕 主体节点内部**根本没有 `input[aria-label="名称"]`** —— `querySelectorAll('input')`
//      只读出**一个** `type="file"` 的 `0×0` 隐藏 input（导入区那个）。
//      而 `jimeng-safe-keys.mjs` 的注释写着「标题 `input[aria-label="名称"]` **自动获焦**」，
//      守卫**照这条拦人**。⇒ 守卫引用的这个元素在**点之前就不存在**，它只可能是
//      **点击之后才渲染出来**的 —— 这正是 b 轮要验的。
//
// 🔴 b 轮判据：
//   · 落点**必须在 `BUTTON[Rename …]` 内部**（同一次 evaluate 内完成找+校验）
//   · 点后连读 3 次焦点（+0ms / +1500ms / +4500ms），**三次都读**才能下结论
//   · 同时读「节点里有没有出现新的 input」—— 只读焦点不够，
//     **可能获焦到了别的东西**（批次 108：「读数对象里没取的字段，判据里不许出现」的镜像）
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const SELF = process.env.SELF_ID || 'node_8j2xkq4vw9';   // a 轮建的；跑完 a 轮后按实际改
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b', self: SELF };
const save = () => writeFileSync(new URL('./_tmp-b115b.json', import.meta.url), JSON.stringify(out, null, 1));

const readFocus = (lbl) => p.evaluate((l) => {
  const a = document.activeElement;
  if (!a) return { at: Date.now(), lbl: l, tag: null, where: '(body)' };
  const r = a.getBoundingClientRect();
  return { at: Date.now(), lbl: l, tag: a.tagName, tid: a.getAttribute('data-testid'),
    aria: a.getAttribute('aria-label'), type: a.getAttribute('type'),
    isInputLike: a.tagName === 'INPUT' || a.tagName === 'TEXTAREA' || a.isContentEditable === true,
    value: a.value !== undefined ? String(a.value) : null,
    rect: [r.x, r.y, r.width, r.height].map(Math.round),
    inNode: !!(a.closest && a.closest('.react-flow__node')) };
}, lbl);

// 节点里的输入面清单（点前/点后各读一次）
const readInputs = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  return { inputs: Array.from(n.querySelectorAll('input,textarea,[contenteditable]')).map((e) => { const r = e.getBoundingClientRect();
      return { tag: e.tagName, tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
        type: e.getAttribute('type'), pe: getComputedStyle(e).pointerEvents, ce: e.isContentEditable === true,
        rect: [r.x, r.y, r.width, r.height].map(Math.round), value: e.value !== undefined ? String(e.value) : null }; }),
    buttons: Array.from(n.querySelectorAll('button,[role=button]')).map((e) => { const r = e.getBoundingClientRect();
      return { aria: e.getAttribute('aria-label'), rect: [r.x, r.y, r.width, r.height].map(Math.round) }; }).filter((x) => x.aria) };
}, SELF);

out.nodeExists = await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), SELF);
log('节点存在？', out.nodeExists);
if (!out.nodeExists) { log('⛔ 节点不在 ⇒ 换 id 后重跑'); await b.close(); process.exit(3); }

out.before = { focus: await readFocus('before'), inputs: await readInputs() };
log('\n=== 点之前 ===');
log('焦点：', JSON.stringify(out.before.focus));
log('输入面：', JSON.stringify(out.before.inputs.inputs));
log('按钮：', JSON.stringify(out.before.inputs.buttons));

// 落点：**Rename 按钮内部**，同一次 evaluate 内完成找 + 校验
const pt = await p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  const btn = Array.from(n.querySelectorAll('button,[role=button]')).find((e) => /^Rename\b/.test(e.getAttribute('aria-label') || ''));
  if (!btn) return { __err: 'no-rename-btn' };
  const r = btn.getBoundingClientRect();
  const cands = [];
  for (let y = Math.ceil(r.y); y < r.y + r.height; y += 2)
    for (let x = Math.ceil(r.x); x < r.x + r.width; x += 2) {
      if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
      const el = document.elementFromPoint(x, y);
      if (!el || !(el === btn || btn.contains(el))) continue;
      cands.push({ x, y, hit: el.tagName }); }
  return { n: cands.length, first: cands[0] || null, btnRect: [r.x, r.y, r.width, r.height].map(Math.round),
    btnAria: btn.getAttribute('aria-label') };
}, SELF);
out.pt = pt;
log('\nRename 按钮内可用落点：', JSON.stringify(pt));
if (!pt.first) { log('⛔ 拿不到落点 ⇒ 中止'); await b.close(); process.exit(4); }

await p.mouse.click(pt.first.x, pt.first.y);
out.t0 = await readFocus('t+0');
await p.waitForTimeout(1500);
out.t1500 = await readFocus('t+1500');
await p.waitForTimeout(3000);
out.t4500 = await readFocus('t+4500');
out.after = { focus: out.t1500, inputs: await readInputs() };

log('\n=== 点之后 ===');
for (const k of ['t0', 't1500', 't4500']) {
  const f = out[k];
  log(`  ${k}: tag=${f.tag} tid=${f.tid} aria=${JSON.stringify(f.aria)} type=${f.type} 输入面=${f.isInputLike} value=${JSON.stringify(f.value)} inNode=${f.inNode}`);
}
log('输入面：', JSON.stringify(out.after.inputs.inputs));
log('按钮：', JSON.stringify(out.after.inputs.buttons));

out.verdict = {
  点前有Rename: !!out.before.inputs.buttons.find((x) => /^Rename/.test(x.aria || '')),
  点后有Rename: !!out.after.inputs.buttons.find((x) => /^Rename/.test(x.aria || '')),
  获焦: out.t1500.isInputLike,
  获焦元素: out.t1500.aria || out.t1500.tid || out.t1500.tag,
  获焦在节点内: out.t1500.inNode,
  三次一致: out.t0.isInputLike === out.t1500.isInputLike && out.t1500.isInputLike === out.t4500.isInputLike,
  点后新增输入面: out.after.inputs.inputs.filter((a) => !out.before.inputs.inputs.some((b2) => b2.tag === a.tag && b2.rect.join() === a.rect.join())),
};
log('\n=== 判定 ==='); log(JSON.stringify(out.verdict, null, 1));
save();
log('\nDONE b');
process.exit(0);
