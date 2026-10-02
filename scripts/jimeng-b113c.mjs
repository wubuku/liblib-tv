// 批次 113 · c 轮：结清「`@<音色名>` 手写后能否被正确识别」这条老账。
//
// 手册现在的说法（`audio-node-voice.md:195-207`）：
//   「**音色名不会被写进提示词**」「`Add` 按钮的作用是**给你一段照抄的示例**」
//   「所以『引用音色』的正确用法是照着示例手写 `@<音色名>`」
//   —— 但**手写之后到底被不被识别，这一页从来没验过**。
//
// 🔴 c 轮的核心判据陷阱：
//   「手打 `@父亲` 之后 innerText 仍是 `@父亲`」—— 这**证明不了任何事**。
//   未识别的纯文本和已识别的 chip，innerText **逐字相同**。
//   ⇒ 判据必须落在**只有「被识别」才会变的地方**：
//     ① 补全层：打字 `@` 之后有没有弹出候选（`role=listbox` / `role=option` / 各种 popover）
//     ② 编辑器 **DOM 结构**：ProseMirror 里有没有多出非文本节点（chip / mention 元素）
//     ③ 面板上的引用 chip 有没有跟着变
//   ��� **不**用「面板能不能发请求」判（那要付费）。
//
// 🔴 keyGuard 放行（批次 107 已有同类先例）：本轮**测试的前提就是焦点在编辑器里** ——
//   守卫会报 `safe:false`（焦点在 contenteditable），**这正是我们要的状态**。
//   放行理由：① 焦点是我们自己刚点进去的；② 只往**自建空节点**的提示词里打字，
//   不碰任何他人节点；③ 打字内容不触发任何扣费/生成动作。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c' };
const save = () => writeFileSync(new URL('./_tmp-b113c.json', import.meta.url), JSON.stringify(out, null, 1));

const SELF = 'node_cp2dh7fn7d';
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));

// 🔑 编辑器读数：**同时**读 innerText / innerHTML / 结构摘要 / 全页补全层 ——
//    前两者对「识别与否」无区分力，区分力在后面两个。
//
// ⚠️ 编辑器**必须按宿主限定**：共享画布上别人的文本节点也开着 `.tiptap.ProseMirror`，
//    全局取第一个会抓到别人的编辑器（本项目老坑：读数对象取到了但取的不是目标）。
const HOST = '[data-testid="node-toolbar"]';
const readEditor = (lbl) => p.evaluate((a) => {
  const { l, host } = a;
  const scope = document.querySelector(host);
  const ed = (scope ? scope.querySelector('.tiptap.ProseMirror') : null)
    || document.querySelector('.tiptap.ProseMirror');   // 兜底，但要**记下走了兜底**
  const r = { at: Date.now(), lbl: l, scoped: !!(scope && scope.querySelector('.tiptap.ProseMirror')),
    nProseMirror: document.querySelectorAll('.tiptap.ProseMirror').length };
  if (!ed) { r.__err = 'no-editor'; return r; }
  r.html = ed.innerHTML;
  r.text = (ed.innerText || '').replace(/\s+/g, ' ').trim();
  r.childTags = Array.from(ed.querySelectorAll('*')).map((e) => e.tagName + (e.getAttribute('data-testid') ? '#' + e.getAttribute('data-testid') : '') + (e.getAttribute('data-mention') ? '@mention' : '')).slice(0, 40);
  r.mentions = Array.from(ed.querySelectorAll('[data-mention],[data-id*="mention"],[class*="mention"],[data-testid*="mention"],[data-type="mention"]'))
    .map((e) => ({ tag: e.tagName, tid: e.getAttribute('data-testid'), dm: e.getAttribute('data-mention'), dt: e.getAttribute('data-type'), txt: (e.innerText || '').trim().slice(0, 30) }));
  r.atomCount = ed.querySelectorAll('.ProseMirror-node').length;
  // 补全层：各种可能的宿主全读
  r.completions = [];
  for (const sel of ['[role=listbox]', '[role=option]', '[role=menu]', '[data-radix-popper-content-wrapper]', '[role=dialog]', '[data-testid*="mention" i]', '[data-testid*="suggest" i]', '[data-testid*="popup" i]', '[class*="popover"]', '[class*="Popover"]']) {
    for (const e of document.querySelectorAll(sel)) { const b = e.getBoundingClientRect();
      if (b.width < 1 || b.height < 1) continue;
      const t = (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120);
      if (!t) continue;
      r.completions.push({ sel, txt: t, rect: [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)] }); }
  }
  r.completions = r.completions.slice(0, 20);
  // 面板上「音色库/引用/时长 chip」的变化
  r.panelChips = Array.from(new Set(Array.from(document.querySelectorAll('[aria-label]'))
    .map((e) => e.getAttribute('aria-label')).filter((a) => /^(引用参考|Add |全音色|音色库|生成分镜视频|生成)/.test(a)))).slice(0, 20);
  const tip = document.querySelector('[data-testid="node-toolbar"]');
  r.panelTop = tip ? (tip.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 180) : null;
  return r;
}, { l: lbl, host: HOST });

out.start = { nodes: await nodeN(), credits: await credits() };
log('起点：', JSON.stringify(out.start));
save();

// ---- 选 SELF，打开面板 ----
log('\n=== 选空音频节点 ===');
const sel = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  if (n.classList.contains('selected')) return { already: true };
  const r = n.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 6; y < r.y + r.height - 6; y += 6)
    for (let x = Math.ceil(r.x) + 6; x < r.x + r.width - 6; x += 6) { if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
      const el = document.elementFromPoint(x, y); if (el && (el === n || n.contains(el))) return { x, y }; }
  return { __err: 'unreachable' }; }, SELF);
log('落点：', JSON.stringify(sel));
if (sel.x) { await p.mouse.click(sel.x, sel.y); await p.waitForTimeout(1800); }

// ---- 先展开音色库、读音色名，再收起 ----
// ⚠️ 时机很重要：音色库**收起时 `Add <音色>` 按钮不在 DOM 里**（本轮 c 第一次跑就读到空数组），
//    所以必须**展开状态下**读，读完再收起。
log('\n=== 展开音色库读音色名 ===');
const vb = await p.evaluate(() => { for (const e of document.querySelectorAll('[aria-label*="音色"]')) {
  const r = e.getBoundingClientRect(); if (r.width < 1) continue;
  const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
  const h = document.elementFromPoint(cx, cy); if (h && (h === e || e.contains(h)))
    return { aria: e.getAttribute('aria-label'), exp: e.getAttribute('aria-expanded'), x: cx, y: cy }; } return null; });
log('音色按钮现态：', JSON.stringify(vb));
out.voiceBtn0 = vb;
if (vb && vb.exp === 'false') { await p.mouse.click(vb.x, vb.y); await p.waitForTimeout(2000);
  log('  已展开，expanded=', await p.evaluate(() => { const e = document.querySelector('[aria-label*="音色"]'); return e ? e.getAttribute('aria-expanded') : null; })); }

// 🔴 `[aria-label^="Add "]` 会把节点的 **`Add tags` 角标**一起匹配进来（`slice(4)` 变成 `tags`）——
//    那是节点的标签功能，不是音色。必须显式排除，否则会拿 `tags` 当音色名去手写。
out.voiceNamesRaw = await p.evaluate(() => Array.from(new Set(Array.from(document.querySelectorAll('[aria-label^="Add "]')).map((e) => (e.getAttribute('aria-label') || '').slice(4)))));
out.voiceNames = out.voiceNamesRaw.filter((n) => n !== 'tags');
out.voiceNameFalsePositives = out.voiceNamesRaw.filter((n) => !out.voiceNames.includes(n));
log('`Add ` 前缀匹配到的原始值：', JSON.stringify(out.voiceNamesRaw));
log('排除 `Add tags` 后的真音色：', JSON.stringify(out.voiceNames));
save();

// 挑一个名字（优先「父亲」，它就是手册示例里用的）
// 🔑 手册的用法示例写的是 `@父亲` / `@女儿` —— 本轮**逐一核对这个名字在不在音色库里**。
out.exampleNamesInLib = { '父亲': out.voiceNames.includes('父亲'), '女儿': out.voiceNames.includes('女儿'),
  '生动解说': out.voiceNames.includes('生动解说') };
log('手册示例里的名字是否真实存在：', JSON.stringify(out.exampleNamesInLib));
const PICK = '生动解说';   // 音色库里确实有的第一个（列表逐字第 1 个真音色）
out.pick = PICK;
out.pickIsReal = out.voiceNames.includes(PICK);
log('本轮手写目标：', JSON.stringify(PICK), '｜真实存在?', out.pickIsReal);

// ---- 收起音色库（**必须**，否则它会盖住提示词输入区） ----
// ⚠️ 音色库面板 `648×216@128,367` 与提示词输入区 `646×28@117,529` **纵向重叠 48px**，
//    展开状态下 `elementFromPoint` 命中的是音色库而不是输入区 ⇒ 落点一个都找不到。
log('\n=== 收起音色库 ===');
{
  const v = await p.evaluate(() => { for (const e of document.querySelectorAll('[aria-label*="音色"]')) {
    const r = e.getBoundingClientRect(); if (r.width < 1) continue;
    const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    const h = document.elementFromPoint(cx, cy); if (h && (h === e || e.contains(h)))
      return { aria: e.getAttribute('aria-label'), exp: e.getAttribute('aria-expanded'), x: cx, y: cy }; } return null; });
  out.voiceBtnCollapse = v; log('  现态：', JSON.stringify(v));
  if (v && v.exp === 'true') { await p.mouse.click(v.x, v.y); await p.waitForTimeout(1600);
    out.voiceBtnAfter = await p.evaluate(() => { const e = document.querySelector('[aria-label*="音色"]'); return e ? e.getAttribute('aria-expanded') : null; });
    log('  已收起，expanded=', out.voiceBtnAfter); }
  else log('  本来就收着');
  out.libOpenNow = await p.evaluate(() => !!document.querySelector('[aria-label="全音色"]'));
  log('  音色库面板还在 DOM 里吗 =', out.libOpenNow);
  save();
}

// ---- 点进提示词编辑器 ----
log('\n=== 点进提示词编辑器 ===');
// 🔑 不取「第一个」——面板里可能有多个编辑器（音色库里的每个音色都有描述编辑器）。
//    列出全部，**逐个**找自己内部的命中点（只问 `el === t || t.contains(el)`）。
out.editors = await p.evaluate(() => { const c = [];
  for (const e of document.querySelectorAll('.tiptap.ProseMirror')) { const r = e.getBoundingClientRect();
    const inTb = !!e.closest('[data-testid="node-toolbar"]'); const inLib = !!e.closest('[aria-label="全音色"]');
    c.push({ inTb, inLib, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      vis: r.width > 1 && r.height > 1 && r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth,
      ed: e }); }
  return c.map(({ ed, ...r }) => r); });
log('页面上 .tiptap.ProseMirror 全部：', JSON.stringify(out.editors));
// 🔑 落点判据：命中元素落在 **`[data-testid="generation-prompt-editor"]` 容器**内部，
//    **不是**落在 `.tiptap.ProseMirror` 内部。
//    原因（批次 113 c 轮诊断实证）：提示词输入区有**两棵几何完全重合的子树** ——
//      · contenteditable 的 `.tiptap.ProseMirror`（`646×28@117,529`，内部只有 `P` + `BR`）
//      · 占位符层（同尺寸，装着 `SPAN 322×20@429,532`）
//    `querySelector('.tiptap.ProseMirror')` 取到的**不是**覆盖层，
//    在它内部按 1×3 网格打 6048 个点，**自命中 0 个** —— 不是不可点，是压根不在最上层。
//    ⇒ 「找元素 → elementFromPoint → 判定在它内部」这条链里，
//      **`querySelector` 找的元素和实际命中层不是同一个时，判据必然失败**（批次 108 的老教训）。
const ed = await p.evaluate(() => {
  const host = document.querySelector('[data-testid="generation-prompt-editor"]');
  if (!host) return { __err: 'no-host' };
  const r = host.getBoundingClientRect();
  const scan = [];
  for (let y = Math.ceil(r.y) + 2; y < r.y + r.height - 2; y += 2)
    for (let x = Math.ceil(r.x) + 2; x < r.x + r.width - 2; x += 2) {
      if (x < 4 || y < 4 || y > innerHeight - 4 || x > innerWidth - 4) continue;
      const el = document.elementFromPoint(x, y);
      if (!el || !(el === host || host.contains(el))) continue;
      // 排除落在按钮/输入上的点（点它不会聚焦编辑器）
      if (el.closest('button,[role=button],a,input,textarea')) continue;
      scan.push({ x, y, hit: el.tagName }); }
  if (!scan.length) return { __err: 'no-clickable', hostRect: [r.x, r.y, r.width, r.height].map(Math.round) };
  return { x: scan[0].x, y: scan[0].y, n: scan.length, hostRect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    hostAria: host.getAttribute('aria-label'), sample: scan.slice(0, 3) };
});
log('编辑器落点：', JSON.stringify(ed));
if (!ed || ed.__err) { log('🔴 点不到编辑器 ⇒ 中止'); await b.close(); process.exit(3); }
await p.mouse.click(ed.x, ed.y); await p.waitForTimeout(900);

const g = await keyGuard(p);
out.keyGuard = { safe: g.safe, where: g.where, reason: g.reason };
log('\n=== keyGuard ===', JSON.stringify(out.keyGuard));
out.keyGuardWaiver = { granted: true,
  why: '本轮测试的前提就是焦点在编辑器里；守卫报 unsafe 恰是期望状态。焦点由本脚本自己点进去；只往本批次自建的空节点提示词里打字；不触发任何扣费/生成动作。（批次 107 已有同类放行先例）' };
if (!g.safe) log('  ⓘ 守卫报 unsafe —— 按上面的理由**显式放行**（焦点 = 编辑器，正是本轮要的）');
else log('  ✅ 守卫直接放行');
save();

// ---- observer：盯编辑器子树 + 浮层 ----
await p.evaluate(() => {
  window.__c = { t0: Date.now(), ev: [] };
  const desc = (n) => { if (!n) return null; if (n.nodeType === 3) return `#text("${(n.nodeValue || '').replace(/\s+/g, ' ').trim().slice(0, 20)}")`;
    if (n.nodeType !== 1) return `#${n.nodeName}`;
    const t = n.getAttribute && n.getAttribute('data-testid'), c = (n.getAttribute && n.getAttribute('class')) || '';
    return `${n.tagName}${t ? '#' + t : ''}${/mention/i.test(c) ? '~mention' : ''}${c ? '.' + c.replace(/\s+/g, ' ').split(' ').slice(0, 2).join('.') : ''}`; };
  const mo = new MutationObserver((l) => { for (const rec of l) { const e = { t: Date.now() - window.__c.t0, type: rec.type };
    if (rec.type === 'childList') { e.added = Array.from(rec.addedNodes).map(desc).slice(0, 5); e.removed = Array.from(rec.removedNodes).map(desc).slice(0, 5); }
    else if (rec.type === 'attributes') { e.attr = rec.attributeName; e.on = desc(rec.target); }
    else if (rec.type === 'characterData') e.on = desc(rec.target);
    window.__c.ev.push(e); } });
  mo.observe(document.body, { childList: true, subtree: true, attributes: true, characterData: true, attributeFilter: ['data-type', 'data-mention', 'class', 'data-testid', 'contenteditable'] });
  window.__c.mo = mo;
});
log('observer 已挂');

// ---- 打字序列：逐段打、逐段读 ----
out.steps = [];
const step = async (label, text, wait) => {
  const before = await readEditor(label + '-before');
  await p.keyboard.type(text, { delay: 90 });
  await p.waitForTimeout(wait);
  const after = await readEditor(label + '-after');
  out.steps.push({ label, typed: text, before, after });
  log(`\n--- ${label}：打「${text}」 ---`);
  log('  text   =', JSON.stringify(after.text));
  log('  html   =', JSON.stringify((after.html || '').slice(0, 220)));
  log('  子节点 =', JSON.stringify(after.childTags));
  log('  mention元素 =', JSON.stringify(after.mentions), '｜ProseMirror-node 数 =', after.atomCount);
  log('  补全层 =', JSON.stringify(after.completions));
  log('  panelChips =', JSON.stringify(after.panelChips));
  log('  面板顶部 =', JSON.stringify((after.panelTop || '').slice(0, 120)));
  save();
  return after;
};

const s0 = await readEditor('empty');
log('空编辑器：text=', JSON.stringify(s0.text), '｜html=', JSON.stringify(s0.html));
out.empty = s0;

const s1 = await step('S1-普通字', '灯塔熄灭了', 1200);
const s2 = await step('S2-只打at', '@', 1400);
const s3 = await step('S3-补名字', PICK, 1600);
const s4 = await step('S4-继续打字', '，你好', 1400);

out.moEvents = await p.evaluate(() => window.__c.ev);
log(`\n=== observer 记到 ${out.moEvents.length} 条 ===`);
out.moInteresting = out.moEvents.filter((e) => /mention|ProseMirror|editor|listbox|option|popover|complet/i.test(JSON.stringify(e)));
log('  其中与「识别」有关的：', out.moInteresting.length, '条');
out.moInteresting.slice(0, 40).forEach((e) => log('   ' + JSON.stringify(e)));
save();

// ---- 判定表 ----
out.verdict = out.steps.map((s) => ({ label: s.label, typed: s.typed, text: s.after.text,
  htmlChanged: s.before.html !== s.after.html, mentions: s.after.mentions.length, atom: s.after.atomCount,
  completions: s.after.completions.length, compText: s.after.completions.map((c) => c.txt.slice(0, 60)) }));
log('\n=== 判定表 ===');
out.verdict.forEach((v) => log('  ' + JSON.stringify(v)));

out.end = { nodes: await nodeN(), credits: await credits() };
log('终点：', JSON.stringify(out.end));
save();
log('\nDONE c');
process.exit(0);
