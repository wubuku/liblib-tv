// 批次 107 · f 轮：把 **⌘⌥1 / ⌘⌥2 / ⌘⌥3 / ⌘⌥0** 逐个测全。
//
// 🔴 上一轮（d）为什么读成「没进编辑态」：
//   `p.mouse.dblclick()` 之后我只等了 **1600ms**，而 React 的双击处理是**异步**的 ——
//   `document.activeElement` 在 d 轮读完时还是 `DIV[]`（没有 `(ce)`），
//   到 e 轮一开始再看，同一个元素已经变成 **`DIV(ce)`**（contenteditable 已生效）。
//   ⇒ **「双击没生效」是我读早了，不是双击没生效。**
//   📌 这与批次 104 的「播放途中暂停」是同一类错：**读数必须等状态真的落定。**
//
// 判据（沿用批次 105/106 的教训）：
//   「⌘⌥3 生效了」只能看**目标那一行自己的渲染结果**（标签名 / class / 字号 / 字重）。
//   **不能**看 innerText（文字本来就在那儿）、**不能**看「页面上有没有 h3」。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), selfId: 'node_gmvz7secas' };
const SELF = out.selfId;
const save = () => writeFileSync(new URL('./_tmp-b107f.json', import.meta.url), JSON.stringify(out, null, 1));

const safeEval = async (fn, arg, tries = 8) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

const probe = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const ce = Array.from(n.querySelectorAll('[contenteditable="true"],textarea')).map((e) => {
    const q = e.getBoundingClientRect();
    return { tag: e.tagName, tid: e.getAttribute('data-testid'), cls: (e.className || '').toString().slice(0, 40),
      w: Math.round(q.width), h: Math.round(q.height), x: Math.round(q.x), y: Math.round(q.y) };
  });
  const a = document.activeElement;
  const inNodeCE = a ? !!(n.contains(a) && (a.isContentEditable || a.closest('[contenteditable]'))) : false;
  return { ce, n: ce.length, sel: n.classList.contains('selected'), activeInNodeCE: inNodeCE,
    active: a ? `${a.tagName}${a.getAttribute('data-testid') ? '[' + a.getAttribute('data-testid') + ']' : ''}${a.isContentEditable ? '(ce)' : ''}` : null,
    toolbar: Array.from(document.querySelectorAll('[data-testid]'))
      .filter((e) => /toolbar/i.test(e.getAttribute('data-testid') || ''))
      .map((e) => ({ tid: e.getAttribute('data-testid'), inside: n.contains(e), n: e.querySelectorAll('button,[role=button]').length,
        aria: Array.from(e.querySelectorAll('button,[role=button]')).map((x) => x.getAttribute('aria-label') || (x.innerText || '').trim()).filter(Boolean) }))
      .filter((x) => x.n > 0) };
}, SELF);

// 目标行「普通正文行。」的**渲染读数**（判据本体）+ 它的屏幕位置
const lineInfo = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  const host = n && Array.from(n.querySelectorAll('[contenteditable="true"],textarea'))
    .find((e) => e.getBoundingClientRect().width > 30);
  if (!host) return { __err: 'no-editor' };
  const all = [host, ...Array.from(host.querySelectorAll('*'))];
  let hit = null;
  for (const e of all) { const t = (e.innerText || e.value || ''); if (t.includes('普通正文行')) { if (!hit || e.contains(hit)) hit = e; } }
  if (!hit) return { __err: 'target-not-found', sample: (host.innerText || '').replace(/\s+/g, ' ').slice(0, 120) };
  const cs = getComputedStyle(hit); const q = hit.getBoundingClientRect();
  return { tag: hit.tagName, cls: (hit.className || '').toString().slice(0, 60), fs: cs.fontSize, fw: cs.fontWeight,
    box: `${Math.round(q.x)},${Math.round(q.y)} ${Math.round(q.width)}×${Math.round(q.height)}`,
    x: Math.round(q.x + q.width / 2), y: Math.round(q.y + q.height / 2),
    parentTag: hit.parentElement ? hit.parentElement.tagName : null,
    parentCls: hit.parentElement ? (hit.parentElement.className || '').toString().slice(0, 50) : null,
    html: hit.outerHTML.replace(/\s+/g, ' ').slice(0, 200),
    // 编辑面里现存的标签清单（看有没有多出 h1/h2/h3）
    allTags: Array.from(new Set(Array.from(host.querySelectorAll('*')).map((e) => e.tagName))).slice(0, 20) };
}, SELF);

out.s0 = await probe();
log('起点：', JSON.stringify({ n: out.s0.n, sel: out.s0.sel, active: out.s0.active, inNodeCE: out.s0.activeInNodeCE }));
if (out.s0.toolbar.length) log('  工具条：', JSON.stringify(out.s0.toolbar));

// 不在编辑态就双击，**并等够 3.5 秒**
if (out.s0.n === 0) {
  const S = await safeEval((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    const r = n.getBoundingClientRect();
    return { x: Math.round(r.x + r.width * 0.7), y: Math.round(r.y + r.height * 0.45) };
  }, SELF);
  log('\n>>> 双击（这次等 3.5s）', JSON.stringify(S));
  await p.mouse.move(S.x, S.y); await p.waitForTimeout(400);
  await p.mouse.dblclick(S.x, S.y, { delay: 60 });
  await p.waitForTimeout(3500);
  out.s1 = await probe();
  log('双击后：', JSON.stringify({ n: out.s1.n, active: out.s1.active, inNodeCE: out.s1.activeInNodeCE }));
  if (out.s1.toolbar.length) log('  工具条：', JSON.stringify(out.s1.toolbar));
  save();
  if (out.s1.n === 0) { log('🔴 仍未进编辑态，停止'); save(); await b.close(); process.exit(1); }
}

out.base = await lineInfo();
log('\n基线（未按任何快捷键）：', JSON.stringify(out.base, null, 1));
save();

out.steps = [];
for (const [key, label, combo] of [['h1', '一级标题', 'Meta+Alt+1'], ['h2', '二级标题', 'Meta+Alt+2'],
                                   ['h3', '三级标题', 'Meta+Alt+3'], ['p', '普通文本', 'Meta+Alt+0']]) {
  const cur = await lineInfo();
  if (cur.__err) { log(`\n>>> ${label}：🔴 找不到目标行（${cur.__err}）`); out.steps.push({ key, label, err: cur.__err }); save(); continue; }
  if (cur.x) { await p.mouse.click(cur.x, cur.y); await p.waitForTimeout(800); }   // 每次重新落光标
  const g = await keyGuard(p);
  log(`\n>>> ${label}：按 ${combo} ｜ keyGuard ${g.safe ? '放行' : '拒绝'}（${g.where}）`);
  if (!g.safe) { out.steps.push({ key, label, refused: g.reason }); save(); continue; }
  const before = await lineInfo();
  await p.keyboard.press(combo);
  await p.waitForTimeout(1300);
  const after = await lineInfo();
  const sig = (x) => x && !x.__err ? `${x.tag}|${x.cls}|${x.fs}|${x.fw}|${x.box}` : 'ERR';
  const rec = { key, label, combo, guard: g.where, beforeSig: sig(before), afterSig: sig(after),
    before: { tag: before.tag, cls: before.cls, fs: before.fs, fw: before.fw, box: before.box },
    after: { tag: after.tag, cls: after.cls, fs: after.fs, fw: after.fw, box: after.box, tags: after.allTags },
    changed: sig(before) !== sig(after) };
  out.steps.push(rec);
  log('   前：', rec.beforeSig);
  log('   后：', rec.afterSig);
  log('   变了 =', rec.changed ? '✅' : '🔴 无变化');
  save();
}

out.end = await probe();
log('\n终点：', JSON.stringify({ n: out.end.n, active: out.end.active }));
out.anyChanged = (out.steps || []).some((s) => s.changed);
out.h3Changed = (out.steps || []).find((s) => s.key === 'h3');
log('⌘⌥3 是否生效 =', out.h3Changed ? (out.h3Changed.changed ? '✅' : '🔴 无变化') : '未测到');
save();
await b.close();
