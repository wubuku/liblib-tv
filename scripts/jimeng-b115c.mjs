// 批次 115 · c 轮：把「需要额外一步才进编辑态」这些**替代解释**逐个排掉。
//
// b 轮已确认（单击 `BUTTON[Rename 主体 1]`）：
//   · 焦点落在**那个 BUTTON 本身**（`inNode: true`），**不是输入面**
//   · **点后没有新增任何输入面**（清单与点前逐字相同，`点后新增输入面: []`）
//   · **按钮没有消失**（没有切换成 input）
//   · +0 / +1500 / +4500ms 三次读数**完全一致**
// ⇒ 单击**不进**编辑态。
//
// 🔴 但下「不进」这个结论前，必须把替代解释逐个排掉（本项目老规矩）：
//   ① 要**双击**才进？
//   ② 焦点在按钮上按 **Enter** 才进？
//   ③ 按 **Space** 才进？
//   ④ 旁边那个 `Edit 主体 1`（`53×22`）才是真正的编辑入口？
//   ⑤ 输入面会不会在**更晚**才渲染（b 轮只等到 +4.5s）？
//
// ⚠️ 与 keyGuard 的关系（这条值得单独说清）：
//   `jimeng-safe-keys.mjs` 的注释说「单击选中『主体』节点 ⇒ 标题 `input[aria-label="名称"]`
//   **自动获焦**」，守卫**照这条拦人**。b 轮证伪了它：**点之前节点里就没有这个 input，
//   点之后也没有出现**。⇒ 守卫注释里的那个元素**从来不存在**。
//   但守卫**本身仍然安全** —— 因为焦点落在一个 `BUTTON` 上，不是输入面，
//   字母键不会被吞成打字（`Rename` 只响应 Enter/Space，不响应字母）。
//   ⇒ 这是「**理由是假的，但结论仍然对**」的一格，必须写清区别。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const SELF = process.env.SELF_ID;
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c', self: SELF };
const save = () => writeFileSync(new URL('./_tmp-b115c.json', import.meta.url), JSON.stringify(out, null, 1));

const readFocus = (lbl) => p.evaluate((l) => {
  const a = document.activeElement; if (!a) return { at: Date.now(), lbl: l, tag: null };
  return { at: Date.now(), lbl: l, tag: a.tagName, tid: a.getAttribute('data-testid'),
    aria: a.getAttribute('aria-label'), type: a.getAttribute('type'),
    isInputLike: a.tagName === 'INPUT' || a.tagName === 'TEXTAREA' || a.isContentEditable === true,
    value: a.value !== undefined ? String(a.value) : null, inNode: !!(a.closest && a.closest('.react-flow__node')) };
}, lbl);
const readInputs = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  return { inputs: Array.from(n.querySelectorAll('input,textarea,[contenteditable]')).map((e) => { const r = e.getBoundingClientRect();
      return { tag: e.tagName, aria: e.getAttribute('aria-label'), type: e.getAttribute('type'),
        rect: [r.x, r.y, r.width, r.height].map(Math.round), value: e.value !== undefined ? String(e.value) : null }; }),
    hasRename: !!Array.from(n.querySelectorAll('button')).find((e) => /^Rename\b/.test(e.getAttribute('aria-label') || '')) };
}, SELF);
// 现算落点，限定在 aria 匹配的按钮内部
const ptOf = (ariaRe) => p.evaluate((src) => {
  const re = new RegExp(src);
  const n = document.querySelector('.react-flow__node.selected') || document.querySelector('.react-flow__node');
  if (!n) return { __err: 'no-node' };
  const btn = Array.from(n.querySelectorAll('button,[role=button]')).find((e) => re.test(e.getAttribute('aria-label') || ''));
  if (!btn) return { __err: 'no-btn' };
  const r = btn.getBoundingClientRect();
  for (let y = Math.ceil(r.y); y < r.y + r.height; y += 2)
    for (let x = Math.ceil(r.x); x < r.x + r.width; x += 2) {
      if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
      const el = document.elementFromPoint(x, y); if (el && (el === btn || btn.contains(el))) return { x, y, aria: btn.getAttribute('aria-label') }; }
  return { __err: 'no-clickable', rect: [r.x, r.y, r.width, r.height].map(Math.round) };
}, ariaRe);

out.nodeExists = await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), SELF);
log('节点存在？', out.nodeExists);
if (!out.nodeExists) { log('⛔ 中止'); await b.close(); process.exit(3); }

out.trials = [];
async function trial(tag, fn) {
  log(`\n──────── ${tag} ────────`);
  const before = { focus: await readFocus(tag + '-before'), inputs: await readInputs() };
  const r = await fn();
  const t0 = await readFocus(tag + '-t0');
  await p.waitForTimeout(1200);
  const t1 = await readFocus(tag + '-t+1.2s');
  await p.waitForTimeout(2500);
  const t2 = await readFocus(tag + '-t+3.7s');
  const after = await readInputs();
  const rec = { tag, act: r || null, before, t0, t1, t2, after,
    进编辑态: t2.isInputLike, 三次一致: t0.isInputLike === t1.isInputLike && t1.isInputLike === t2.isInputLike,
    新增输入面: after.inputs.filter((a) => !before.inputs.inputs.some((b2) => b2.tag === a.tag && b2.rect.join() === a.rect.join())),
    Rename按钮还在: after.hasRename };
  out.trials.push(rec);
  log('  焦点 t0/t1.2s/t3.7s：', rec.t0.tag, rec.t0.aria || '', '｜输入面？', rec.t0.isInputLike, '/', rec.t1.isInputLike, '/', rec.t2.isInputLike);
  log('  输入面：', JSON.stringify(after.inputs));
  log('  Rename 按钮还在？', rec.Rename按钮还在, '｜新增输入面：', JSON.stringify(rec.新增输入面));
  save();
  return rec;
}

// ① 双击 Rename
await trial('①双击Rename', async () => {
  const pt = await ptOf('^Rename\\b'); log('  落点：', JSON.stringify(pt));
  if (pt.__err) return pt;
  await p.mouse.dblclick(pt.x, pt.y); return { clicked: pt };
});
// ② 单击后按 Enter
await trial('②单击后按Enter', async () => {
  const pt = await ptOf('^Rename\\b'); if (pt.__err) return pt;
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(700);
  const g = await keyGuard(p); log('  按 Enter 前守卫：', g.safe ? '✅' : 'ⓘ', g.where || '');
  await p.keyboard.press('Enter'); return { clicked: pt, guard: { safe: g.safe, where: g.where } };
});
// ③ 单击后按 Space
await trial('③单击后按Space', async () => {
  const pt = await ptOf('^Rename\\b'); if (pt.__err) return pt;
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(700);
  await p.keyboard.press(' '); return { clicked: pt };
});
// ④ 点 `Edit 主体 1`
await trial('④点Edit主体', async () => {
  const pt = await ptOf('^Edit\\s'); log('  落点：', JSON.stringify(pt));
  if (pt.__err) return pt;
  await p.mouse.click(pt.x, pt.y); return { clicked: pt };
});
// ⑤ 点 `Edit subject description`
await trial('⑤点Edit描述', async () => {
  const pt = await ptOf('^Edit subject description$'); log('  落点：', JSON.stringify(pt));
  if (pt.__err) return pt;
  await p.mouse.click(pt.x, pt.y); return { clicked: pt };
});

out.verdict = out.trials.map((t) => ({ 试: t.tag, 进编辑态: t.进编辑态, 焦点元素: t.t2.aria || t.t2.tag,
  新增输入面数: t.新增输入面.length, 三次一致: t.三次一致, Rename还在: t.Rename按钮还在 }));
log('\n=== 判定汇总 ==='); log(JSON.stringify(out.verdict, null, 1));
out.anyEntered = out.trials.some((t) => t.进编辑态);
log('\n  ⇒ 有没有任何一种操作进入编辑态：', out.anyEntered);
out.end = { nodes: await p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]),
  credits: await p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label')) };
log('终点：', JSON.stringify(out.end));
save();
log('\nDONE c');
process.exit(0);
