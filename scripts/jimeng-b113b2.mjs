// 批次 113 · b2 轮：**不新建节点**，直接复用本批次已造好的两个。
//
// 为什么有 b2：b 轮两臂都被**判据自己**挡下来了，不是产品行为：
//   臂 1：落点校验写成「用 testid 反查目标元素」，而媒体节点的播放按钮 `tid: null`
//         ⇒ `querySelector('[data-testid="null"]')` 恒为 null ⇒ ok 恒 false。
//         批次 108 的原话：「落点判据只问『命中元素是否落在目标内部』」——
//         反查这一步把「目标元素」换成了「另一个按 testid 猜的元素」，假设就跑偏了。
//   臂 2：`音色库` 按钮在**媒体节点**的工具条上根本不存在 —— 音色库是
//         **空音频节点**的生成面板才有的东西。b 轮一直在 T1（上传出来的媒体节点）上找。
//
// 🔴 本轮的修法（写进长期规矩）：
//   **「找元素 → 算中心 → elementFromPoint → 校验」必须放在同一次 page.evaluate 里。**
//   元素引用一旦跨 evaluate 传出去就只能靠属性反查，而属性反查是**换了一个目标**。
//   下面 `clickByPredicate()` 就是这条规矩的实现。
//
// 弹药（都是本批次自建，z 轮统一清）：
//   T1  = node_zvmkems3fe  ← b 轮左栏上传 wav 造的**媒体**音频节点（有播放按钮）
//   SELF= node_cp2dh7fn7d  ← a 轮右键新建的**空**音频节点（有音色库面板）
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b2' };
const save = () => writeFileSync(new URL('./_tmp-b113b2.json', import.meta.url), JSON.stringify(out, null, 1));

const T1 = 'node_zvmkems3fe';
const SELF = 'node_cp2dh7fn7d';
const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);

// 🔑 规矩实现：同一 evaluate 内完成「找 → 算中心 → elementFromPoint → 判定是否在目标内部」
//
// ⚠️ `page.evaluate` **不能传 RegExp**（结构化克隆会把它序列化成 `{}`），
//    所以判据一律传**字符串**，在页面侧 `new RegExp()` 构造。
const clickByPredicate = (arg) => p.evaluate(async (a) => {
  const re = a.aria ? new RegExp(a.aria) : null;
  const cands = [];
  for (const e of document.querySelectorAll('button,[role=button],[aria-label]')) {
    if (re) { const l = e.getAttribute('aria-label') || ''; if (!re.test(l)) continue; }
    if (a.inNode) { const n = document.querySelector(`.react-flow__node[data-id="${a.inNode}"]`); if (!n || !n.contains(e)) continue; }
    const r = e.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    cands.push(e);
  }
  if (!cands.length) return { __err: 'not-found' };
  // 逐个候选找**真实可点**的那个：中心点命中自己或自己的后代
  for (const t of cands) {
    const r = t.getBoundingClientRect();
    const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    if (cx < 4 || cy < 4 || cy > innerHeight - 4 || cx > innerWidth - 4) continue;
    const el = document.elementFromPoint(cx, cy);
    if (!el || !(el === t || t.contains(el))) continue;
    return {
      ok: true, aria: t.getAttribute('aria-label'), tid: t.getAttribute('data-testid'),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      hitTag: el.tagName, hitDesc: `${el.tagName}#${el.getAttribute('data-testid') || '-'}`,
      nCandidates: cands.length,
    };
  }
  return { __err: 'no-clickable', nCandidates: cands.length,
    all: cands.map((t) => { const r = t.getBoundingClientRect();
      return { aria: t.getAttribute('aria-label'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; }) };
}, arg);

const doClick = (c) => p.mouse.click(c.rect[0] + c.rect[2] / 2, c.rect[1] + c.rect[3] / 2);

// 四通道快照：testid 家族 / 带 Play|Pause 的 aria / 文本标志 / 所有 <audio>
const snap = (lbl) => p.evaluate((l) => {
  const r = {};
  r.tids = Array.from(new Set(Array.from(document.querySelectorAll('[data-testid^="audio-simple-player"]')).map((e) => e.getAttribute('data-testid'))));
  r.pp = Array.from(new Set(Array.from(document.querySelectorAll('[aria-label]'))
    .map((e) => ({ a: e.getAttribute('aria-label'), t: e.getAttribute('data-testid'), inNode: !!e.closest('.react-flow__node') }))
    .filter((x) => /^(Play|Pause)\b/.test(x.a || ''))
    .map((x) => `${x.a}#${x.t || '-'}${x.inNode ? '@node' : ''}`)));
  r.audios = Array.from(document.querySelectorAll('audio')).map((a) => ({ paused: a.paused, t: a.getAttribute('data-testid'), ct: +(a.currentTime || 0).toFixed(2), dur: +(a.duration || 0).toFixed(2), srcTail: (a.currentSrc || a.src || '').slice(-28) }));
  r.at = Date.now(); r.lbl = l; return r;
}, lbl);

const installMo = (tag) => p.evaluate((tg) => {
  window.__b = { tag: tg, t0: Date.now(), ev: [] };
  const hit = (s) => /play|pause|audio|生动|解说|试听/i.test(String(s));
  const desc = (n) => { if (!n) return null; if (n.nodeType === 3) return (n.nodeValue || '').replace(/\s+/g, ' ').trim().slice(0, 40);
    if (n.nodeType !== 1) return `#${n.nodeName}`;
    const t = n.getAttribute && n.getAttribute('data-testid'), a = n.getAttribute && n.getAttribute('aria-label');
    return `${n.tagName}${t ? '#' + t : ''}${a ? '[' + a.replace(/\s+/g, ' ').trim().slice(0, 30) + ']' : ''}`; };
  const mo = new MutationObserver((list) => { for (const rec of list) {
    const e = { t: Date.now() - window.__b.t0, type: rec.type };
    if (rec.type === 'childList') { const ad = Array.from(rec.addedNodes).map(desc).filter((x) => x && hit(x));
      const rm = Array.from(rec.addedNodes).map(desc).filter((x) => x && hit(x));
      const r2 = Array.from(rec.removedNodes).map(desc).filter((x) => x && hit(x));
      if (ad.length || r2.length) e.ch = { added: ad.slice(0, 4), removed: r2.slice(0, 4) }; }
    else if (rec.type === 'attributes') { e.attr = rec.attributeName; e.on = desc(rec.target);
      if (rec.attributeName === 'aria-label' || rec.attributeName === 'data-testid') e.new = String(rec.target.getAttribute(rec.attributeName) || '').replace(/\s+/g, ' ').trim().slice(0, 50); }
    else if (rec.type === 'characterData') e.txt = desc(rec.target);
    if (e.ch || e.attr || e.txt) window.__b.ev.push(e); } });
  mo.observe(document.body, { childList: true, subtree: true, attributes: true, characterData: true, attributeOldValue: true });
  window.__b.mo = mo;
  return { tag: tg, channels: ['childList', 'attributes', 'characterData'] };
}, tag);
const readMo = (tag) => p.evaluate((tg) => (window.__b && window.__b.tag === tg ? { n: window.__b.ev.length, ev: window.__b.ev } : { n: -1, ev: [] }), tag);

const watch = async (ms, step = 250) => { const s = []; const t0 = Date.now();
  while (Date.now() - t0 < ms) { s.push(await snap('w')); await p.waitForTimeout(step); } return s; };
const fold = (arr) => { const r = []; for (const s of arr) {
  const k = s.tids.join('|') + '::' + s.pp.join('|') + '::' + JSON.stringify(s.audios.map((a) => [a.paused, a.ct]));
  if (!r.length || r[r.length - 1].k !== k) r.push({ k, t: s.at, n: arr.indexOf(s) }); } return r; };

out.start = { nodes: await nodeN(), credits: await credits() };
const ids = await allIds();
out.selfCheck = { t1: ids.includes(T1), self: ids.includes(SELF), n: ids.length };
log('起点：', JSON.stringify(out.start), '｜T1 在?', out.selfCheck.t1, '｜SELF 在?', out.selfCheck.self);
save();

const g = await keyGuard(p);
log('焦点守卫：', g.safe ? '✅' : '⛔', g.where || '');
if (!g.safe) { log('⛔ 中止'); await b.close(); process.exit(2); }

// ================= 臂 1：媒体节点的播放（阳性对照） =================
log('\n=== 臂 1（阳性对照）：node_zvmkems3fe 的 Play ===');
// 先把 T1 选中（面板/工具条会挡住别的，但播放按钮在卡片上）
const selT1 = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  if (n.classList.contains('selected')) return { already: true };
  const r = n.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 6; y < r.y + r.height - 6; y += 6)
    for (let x = Math.ceil(r.x) + 6; x < r.x + r.width - 6; x += 6) { if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
      const el = document.elementFromPoint(x, y); if (el && (el === n || n.contains(el))) return { x, y }; }
  return { __err: 'unreachable' }; }, T1);
log('  T1 选中落点：', JSON.stringify(selT1));
if (selT1 && selT1.x) { await p.mouse.click(selT1.x, selT1.y); await p.waitForTimeout(1600); }
out.t1State = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  return { selected: n.classList.contains('selected'),
    inner: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160),
    tids: Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')))),
    // 时长读数：新发现——两个形态都出现了
    durs: Array.from(n.querySelectorAll('[data-testid^="audio-duration"]')).map((e) => ({ tid: e.getAttribute('data-testid'), txt: (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim(), r: (() => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() })) }; }, T1);
log('  T1 状态：', JSON.stringify(out.t1State, null, 1));

const arm1Btn = await clickByPredicate({ aria: '^Play\\b', inNode: T1 });
log('  臂 1 落点：', JSON.stringify(arm1Btn));
out.arm1 = { btn: arm1Btn };
if (arm1Btn.__err) { log('🔴 臂 1 拿不到可点落点 ⇒ 放弃'); out.arm1 = { fail: arm1Btn }; }
else {
  out.arm1.before = await snap('arm1');
  out.arm1.moInstall = await installMo('arm1');
  const t0 = Date.now();
  await doClick(arm1Btn); log('  已点 Play，连采 14s…');
  out.arm1.samples = await watch(14000, 250);
  out.arm1.elapsed = Date.now() - t0;
  out.arm1.mo = await readMo('arm1');
  out.arm1.seq = fold(out.arm1.samples).map((x) => ({ t: x.t, tids: x.k.split('::')[0], pp: x.k.split('::')[1], au: x.k.split('::')[2] }));
  log('  ⇒ 臂 1 取值序列（折叠后）：');
  out.arm1.seq.forEach((x) => log(`     t=${x.t} tids=${x.tids} pp=${x.pp} au=${x.au}`));
  log('  ⇒ observer 记到', out.arm1.mo.n, '条');
  out.arm1.mo.ev.slice(0, 30).forEach((e) => log('     ' + JSON.stringify(e)));
  // 停掉
  const pz = await clickByPredicate({ aria: '^Pause\\b', inNode: T1 });
  if (pz.ok) { await doClick(pz); await p.waitForTimeout(900); log('  已点 Pause'); out.arm1.paused = true; } else log('  ⚠️ 找不到 Pause（可能已播完自动停）');
}
save();

// ================= 臂 2：音色库样音（靶子） =================
log('\n=== 臂 2（靶子）：空音频节点的音色库样音 ===');
// 选 SELF（空音频节点）—— 它的工具条里才有「音色库」
const selSelf = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  if (n.classList.contains('selected')) return { already: true };
  const r = n.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 6; y < r.y + r.height - 6; y += 6)
    for (let x = Math.ceil(r.x) + 6; x < r.x + r.width - 6; x += 6) { if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
      const el = document.elementFromPoint(x, y); if (el && (el === n || n.contains(el))) return { x, y }; }
  return { __err: 'unreachable' }; }, SELF);
log('  SELF 选中落点：', JSON.stringify(selSelf));
if (selSelf && selSelf.x) { await p.mouse.click(selSelf.x, selSelf.y); await p.waitForTimeout(1800); }
out.selfState = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  const tb = n.querySelector('[data-testid="node-toolbar"]') || document.querySelector('[data-testid="node-toolbar"]');
  return { selected: n.classList.contains('selected'), inner: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160),
    toolbar: tb ? { present: true, txt: (tb.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200),
      btns: Array.from(tb.querySelectorAll('button,[role=button]')).map((e) => e.getAttribute('aria-label')).filter(Boolean) } : { present: false } }; }, SELF);
log('  SELF 状态：', JSON.stringify(out.selfState, null, 1));

let libBtn = await clickByPredicate({ aria: '^音色库$' });
out.libBtn = libBtn;
log('  「音色库」：', JSON.stringify(libBtn));
out.libExpanded = await p.evaluate(() => { for (const e of document.querySelectorAll('[aria-label="音色库"]')) { if (e.getAttribute('aria-expanded')) return e.getAttribute('aria-expanded'); } return null; });
if (libBtn.__err) { log('🔴 臂 2 找不到「音色库」⇒ 放弃'); out.arm2 = { fail: libBtn }; }
else {
  if (out.libExpanded === 'false') { await doClick(libBtn); await p.waitForTimeout(2000); log('  已点开音色库'); }
  out.libExpanded2 = await p.evaluate(() => { for (const e of document.querySelectorAll('[aria-label="音色库"]')) { if (e.getAttribute('aria-expanded')) return e.getAttribute('aria-expanded'); } return null; });
  out.libOpen = await p.evaluate(() => { const e = document.querySelector('[aria-label="全音色"]'); if (!e) return { present: false };
    const r = e.getBoundingClientRect(); return { present: true, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; });
  log('  音色库：', out.libExpanded2, JSON.stringify(out.libOpen));
  // 🔴 靶子按钮：音色库里的 `Play <音色名>`。**必须限定不在任何 .react-flow__node 里** ——
  //    否则会抓到 T1 的播放按钮（那是臂 1 的靶子，作用域不同）。
  const sample = await p.evaluate(() => { const c = [];
    for (const e of document.querySelectorAll('[aria-label]')) { const a = e.getAttribute('aria-label') || '';
      if (!/^Play\s+\S/.test(a)) continue; const r = e.getBoundingClientRect(); if (r.width < 1) continue;
      c.push({ aria: a, tid: e.getAttribute('data-testid'), inNode: !!e.closest('.react-flow__node'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }); }
    return c; });
  out.allPlayBtns = sample;
  log('  页面上所有 `Play <名>` 按钮：', JSON.stringify(sample, null, 1));
  const libOnly = await p.evaluate((cands) => { for (const t of cands) { if (t.inNode) continue;
      const el = document.querySelector(`[aria-label="${t.aria.replace(/"/g, '\\"')}"]`); if (!el) continue;
      const r = el.getBoundingClientRect(); const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
      if (cx < 4 || cy < 4 || cy > innerHeight - 4 || cx > innerWidth - 4) continue;
      const h = document.elementFromPoint(cx, cy); if (!h || !(h === el || el.contains(h))) continue;
      return { ok: true, aria: t.aria, tid: t.tid, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], hit: h.tagName }; }
    return { __err: 'no-clickable' }; }, sample);
  out.sampleBtn = libOnly;
  log('  靶子落点：', JSON.stringify(libOnly));
  if (libOnly.__err) { log('🔴 靶子拿不到可点落点 ⇒ 放弃'); out.arm2 = { fail: libOnly }; }
  else {
    out.arm2 = { btn: libOnly };
    out.arm2.before = await snap('arm2');
    out.arm2.moInstall = await installMo('arm2');
    const t0 = Date.now();
    await doClick(libOnly); log('  已点样音 Play，连采 30s（批次 97 记的就是 30s）…');
    out.arm2.samples = await watch(30000, 250);
    out.arm2.elapsed = Date.now() - t0;
    out.arm2.mo = await readMo('arm2');
    out.arm2.seq = fold(out.arm2.samples).map((x) => ({ t: x.t, tids: x.k.split('::')[0], pp: x.k.split('::')[1], au: x.k.split('::')[2] }));
    log('  ⇒ 臂 2 取值序列（折叠后）：');
    out.arm2.seq.forEach((x) => log(`     t=${x.t} tids=${x.tids} pp=${x.pp} au=${x.au}`));
    log('  ⇒ observer 记到', out.arm2.mo.n, '条');
    out.arm2.mo.ev.slice(0, 30).forEach((e) => log('     ' + JSON.stringify(e)));
  }
}
save();

log('\n=== 两臂对照 ===');
out.compare = {
  arm1: out.arm1 && out.arm1.seq ? { flips: out.arm1.seq.length - 1, mo: out.arm1.mo.n, secs: Math.round(out.arm1.elapsed / 1000) } : null,
  arm2: out.arm2 && out.arm2.seq ? { flips: out.arm2.seq.length - 1, mo: out.arm2.mo.n, secs: Math.round(out.arm2.elapsed / 1000) } : null,
};
log(JSON.stringify(out.compare, null, 1));
out.end = { nodes: await nodeN(), credits: await credits() };
log('终点：', JSON.stringify(out.end));
save();
log('\nDONE b2');
process.exit(0);
