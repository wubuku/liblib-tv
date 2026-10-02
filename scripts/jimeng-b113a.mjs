// 批次 113 · a 轮：造一个**空音频节点**，用 `MutationObserver` 结清
// 「未选中空节点的空态元素是否始终在 DOM 里」这条**两轮读数矛盾**的老账。
//
// 矛盾的原文（`audio-node-voice.md:238`）：
//   「a 轮 31/31 读到 `Not selected.`，b 轮在锁定节点未选中时却读到该元素**不在 DOM 里**（`null`）。
//     只有『末句随选中态在 `Selected.` / `Not selected.` 之间变』这一条两轮都站得住。」
//   ⇒ 批次 97 已把它记 **VOID**（`VOlD` = 没法验证，**不等于「不存在」**）
//
// 🔴 方法上采纳批次 97 自己立的规矩：
//   「『Play→Pause 有没有翻转』用 `MutationObserver` 判，不要用轮询判 ——
//     轮询间隔大于翻转耗时时会**整个漏掉**翻转。」
//   本轮把这条用在**节点增删/选中态切换**上：在页面里挂一个 `MutationObserver`，
//   逐条记时间戳与**具体变了什么**（addedNodes / removedNodes / attributeFilter）。
//   同时跑一条轮询通道作**旁证**（不共享同一套假设）。
//
// 🔴 护栏三道：建前存全画布 id 集合；建后差集**恰好一个**且**同时 `.selected`**；
//    z 轮删除时落点**按动作时刻现算**、`elementFromPoint` 命中目标内部、不叠矩形条件。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b113a.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);

// 读「空态描述元素」：**不预设它在哪个属性里** —— 根 aria / 内部 aria / innerText 三处都读
const readState = (id) => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  const inner = (n.innerText || '').replace(/\s+/g, ' ').trim();
  const allAria = [n.getAttribute('aria-label'), ...Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label'))]
    .filter(Boolean).map((s) => s.replace(/\s+/g, ' ').trim());
  // 「资源账 / 状态描述」这类句子可能落在任意一个 aria 上，**全列出来**再判
  const descLike = allAria.filter((a) => /No resources|resources?:|Selected|Not selected|正在上传|处理上传/.test(a));
  return {
    rootAria: n.getAttribute('aria-label'),
    selected: n.classList.contains('selected'),
    innerText: inner.slice(0, 200),
    descLike: Array.from(new Set(descLike)),
    allAria: Array.from(new Set(allAria)),
    testids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    screen: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    nButtons: n.querySelectorAll('button').length,
  };
}, id);

out.start = { nodes: await nodeN(), credits: await credits() };
const idsBefore = await allIds();
log('起点：', JSON.stringify(out.start), '｜id 数', idsBefore.length);
save();

const g = await keyGuard(p);
log('焦点守卫：', g.safe ? '✅' : '⛔', g.where || '');
if (!g.safe) { log('⛔ 中止'); await b.close(); process.exit(2); }

// ---- 空白右键 → 新建节点 → 音频 ----
out.blank = await p.evaluate(() => {
  const bad = (x, y) => { const el = document.elementFromPoint(x, y);
    if (!el || el.closest('.react-flow__node')) return true;
    if (x < 200 || y < 60 || y > 630 || x > 1120) return true;
    if (el.closest('button,[role=button],input,a')) return true; return false; };
  const all = [];
  for (let y = 280; y < 630; y += 12) for (let x = 260; x < 1100; x += 12) if (!bad(x, y)) all.push([x, y]);
  return { n: all.length, first: all[0] || null }; });
log('可用空白点数：', out.blank.n, '｜第一块：', JSON.stringify(out.blank.first));
if (!out.blank.first) { log('🔴 找不到空白 ⇒ 中止'); await b.close(); process.exit(3); }
const [bx, by] = out.blank.first;
await p.mouse.move(bx, by); await p.waitForTimeout(400);
await p.mouse.down({ button: 'right' }); await p.waitForTimeout(300); await p.mouse.up({ button: 'right' });
await p.waitForTimeout(1200);

out.nj = await p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]'))
  for (const it of m.querySelectorAll('[role=menuitem]')) {
    if ((it.innerText || '').trim().startsWith('新建节点')) { const r = it.getBoundingClientRect();
      return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), expanded: it.getAttribute('aria-expanded') }; } } return null; });
log('「新建节点」：', JSON.stringify(out.nj));
await p.mouse.move(out.nj.x, out.nj.y); await p.waitForTimeout(500);
await p.mouse.move(out.nj.x + 3, out.nj.y); await p.waitForTimeout(1400);

out.items = await p.evaluate(() => { const c = [];
  for (const m of document.querySelectorAll('[role=menu]')) { const cs = getComputedStyle(m);
    for (const it of m.querySelectorAll('[role=menuitem]')) { const ir = it.getBoundingClientRect(); if (!ir.width) continue;
      const t = (it.innerText || '').replace(/\s+/g, ' ').trim();
      c.push({ t, vis: cs.visibility, x: Math.round(ir.x + ir.width / 2), y: Math.round(ir.y + ir.height / 2) }); } }
  return c; });
log('可见菜单项：', JSON.stringify(out.items.map((c) => c.t)));
const target = out.items.find((c) => c.t === '音频' && c.vis !== 'hidden');
log('目标「音频」：', JSON.stringify(target));
if (!target) { log('🔴 找不到「音频」项 ⇒ 中止'); await p.keyboard.press('Escape'); await b.close(); process.exit(3); }
const chk = await p.evaluate((t) => { const e = document.elementFromPoint(t.x, t.y);
  return { ok: !!e, text: e ? (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 20) : null, inMenu: e ? !!e.closest('[role=menu]') : false }; }, target);
log('落点校验：', JSON.stringify(chk));
if (!chk.ok || !chk.inMenu) { log('🔴 校验不过 ⇒ 中止'); await p.keyboard.press('Escape'); await b.close(); process.exit(3); }
await p.mouse.click(target.x, target.y);
log('已点「音频」');
save();

let SELF = null;
for (let k = 1; k <= 16; k++) {
  await p.waitForTimeout(1200);
  const ids = await allIds();
  const diff = ids.filter((id) => !idsBefore.includes(id));
  if (diff.length) { SELF = diff[0]; log(`  #${k} 差集 = ${JSON.stringify(diff)}`); }
  if (SELF) { const selIds = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
    out.guardrail2 = { diffN: (out.diff || diff).length, ok: diff.length === 1 && selIds.includes(SELF) };
    if (out.guardrail2.ok) { log('  ⇒ 护栏② 通过', JSON.stringify(selIds)); break; } }
  save();
}
out.self = SELF; out.diff = SELF ? [SELF] : [];
log('SELF =', SELF, SELF ? '✅' : '🔴');
save();
if (!SELF) { log('🔴 没建出节点 ⇒ 中止'); await b.close(); process.exit(3); }

// ================= 挂 MutationObserver（这一轮的主角） =================
log('\n=== 挂 MutationObserver：盯整棵 document 的增删与属性变化 ===');
out.mo = await p.evaluate(() => {
  window.__b113a = { events: [], t0: Date.now() };
  const mo = new MutationObserver((list) => {
    for (const rec of list) {
      const e = { t: Date.now() - window.__b113a.t0, type: rec.type };
      if (rec.type === 'childList') {
        e.added = rec.addedNodes.length; e.removed = rec.removedNodes.length;
        const grab = (n) => { if (n.nodeType !== 1) return (n.nodeValue || '').replace(/\s+/g, ' ').trim().slice(0, 40);
          return `${n.tagName}${(n.getAttribute && n.getAttribute('data-testid')) ? '#' + n.getAttribute('data-testid') : ''}[${(n.className || '').toString().slice(0, 24)}]`; };
        if (rec.addedNodes.length) e.addedSample = Array.from(rec.addedNodes).slice(0, 3).map(grab);
        if (rec.removedNodes.length) e.removedSample = Array.from(rec.removedNodes).slice(0, 3).map(grab);
      } else {
        e.attr = rec.attributeName;
        const tg = rec.target;
        e.target = tg.nodeType === 1 ? `${tg.tagName}${(tg.getAttribute && tg.getAttribute('data-testid')) ? '#' + tg.getAttribute('data-testid') : ''}` : null;
        e.newValue = rec.type === 'attributes' ? String(tg.getAttribute(rec.attributeName) || '').replace(/\s+/g, ' ').trim().slice(0, 60) : null;
      }
      window.__b113a.events.push(e);
    }
  });
  mo.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['aria-label', 'class', 'data-state'] });
  window.__b113a.mo = mo;
  return { installed: true };
});
log('observer 已挂：', JSON.stringify(out.mo));
save();

// ---- 通道 A：选中态 → 取消选中 ----
// 落点用**已经校验过的那块空白**（`out.blank.first`）：`bad()` 已排除
// 「落在任何节点里」「落在 button/input/a 上」「贴边」。批次 108 教训：
// 落点要**按动作时刻现算**，不写死坐标。
log('\n=== A：点空白取消选中 @', JSON.stringify(out.blank.first), '===');
const [ux, uy] = out.blank.first;
const uCheck = await p.evaluate((t) => { const e = document.elementFromPoint(t[0], t[1]);
  return { tag: e ? e.tagName : null, inNode: e ? !!e.closest('.react-flow__node') : null,
    inBtn: e ? !!e.closest('button,[role=button],input,a') : null }; }, [ux, uy]);
log('  取消落点校验：', JSON.stringify(uCheck));
await p.mouse.click(ux, uy); await p.waitForTimeout(1800);
out.unselected = await readState(SELF);
log('  selected =', out.unselected.selected);
log('  rootAria =', out.unselected.rootAria);
log('  innerText =', JSON.stringify(out.unselected.innerText));
log('  状态描述类 aria =', JSON.stringify(out.unselected.descLike));
log('  testids =', JSON.stringify(out.unselected.testids));
log('  按钮数 =', out.unselected.nButtons);
save();

// ---- 通道 B：再点回来选中 ----
log('\n=== B：再点回来选中 ===');
const sp = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
  if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect(); const c = [];
  for (let y = Math.ceil(r.y) + 3; y < r.y + r.height - 3; y += 4)
    for (let x = Math.ceil(r.x) + 3; x < r.x + r.width - 3; x += 4) {
      if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
      const el = document.elementFromPoint(x, y);
      if (el && (el === n || n.contains(el))) c.push({ x, y }); }
  return { total: c.length, sample: c.slice(0, 2) };
}, SELF);
log('  落点：', JSON.stringify(sp));
if (sp.total) {
  await p.mouse.click(sp.sample[0].x, sp.sample[0].y); await p.waitForTimeout(1800);
  out.reselected = await readState(SELF);
  log('  selected =', out.reselected.selected);
  log('  状态描述类 aria =', JSON.stringify(out.reselected.descLike));
  log('  testids =', JSON.stringify(out.reselected.testids));
  save();
}

// ---- 通道 C：再取消（回到未选中），用来确认「不是一次性的」 ----
log('\n=== C：再取消一次（确认可复现，不是偶发）===');
const [vx, vy] = out.blank.first;
const vCheck = await p.evaluate((t) => { const e = document.elementFromPoint(t[0], t[1]);
  return { tag: e ? e.tagName : null, inNode: e ? !!e.closest('.react-flow__node') : null }; }, [vx, vy]);
log('  取消落点校验：', JSON.stringify(vCheck));
await p.mouse.click(vx, vy); await p.waitForTimeout(1800);
out.unselected2 = await readState(SELF);
log('  selected =', out.unselected2.selected);
log('  状态描述类 aria =', JSON.stringify(out.unselected2.descLike));
log('  testids =', JSON.stringify(out.unselected2.testids));
save();

// ---- 读 observer 的记录 ----
out.moEvents = await p.evaluate(() => (window.__b113a ? window.__b113a.events : []));
log(`\n=== MutationObserver 记到 ${out.moEvents.length} 条 ===`);
// 只打印与本节点/aria 有关的，省得刷屏
const interesting = out.moEvents.filter((e) => (e.added || e.removed) && (String(e.addedSample) + String(e.removedSample)).match(/audio|resource|Selected|node/i))
  .concat(out.moEvents.filter((e) => e.attr === 'aria-label'));
out.moInteresting = interesting;
interesting.slice(0, 40).forEach((e) => log('  ' + JSON.stringify(e)));
save();

// ---- 三态并排 ----
out.threeStates = { unselected: out.unselected, reselected: out.reselected, unselected2: out.unselected2 };
log('\n=== 三态并排（判据：状态描述元素在不在、末句是什么） ===');
for (const [k, v] of Object.entries(out.threeStates)) {
  if (!v) { log(`  ${k}: ——`); continue; }
  log(`  ${k}: selected=${v.selected}｜描述类 aria=${JSON.stringify(v.descLike)}｜按钮数=${v.nButtons}`);
  log(`      testids=${JSON.stringify(v.testids)}`);
}
log('\n  ⇒ 三态里「描述元素是否存在」是否一致 =',
  [out.unselected, out.reselected, out.unselected2].filter(Boolean)
    .map((v) => v.descLike.length > 0).join(' / '));
log('  ⇒ 三态里末句是否都存在 =',
  [out.unselected, out.reselected, out.unselected2].filter(Boolean)
    .map((v) => (v.descLike.find((d) => /Selected\.$|Not selected\.$/.test(d)) || '（没有末句）')).join(' || '));
save();

out.end = { nodes: await nodeN(), credits: await credits() };
log('\n终点：', JSON.stringify(out.end));
save();
log('\nDONE a');
process.exit(0);
