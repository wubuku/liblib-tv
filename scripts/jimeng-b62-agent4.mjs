// 批次 62 第四轮（收口）：用**修正后的落点判据**补完 `/` 与 `@`，并出齐配图。
//
// 探测脚本查清了上一轮 `landed.isInside === false` 的真因 —— **是我的断言写错了，不是产品有问题**：
//
//   DIV[data-testid=canvas-agent-session-composer] 390×164@873,539
//   └ DIV[data-testid=prompt-composer] 357×84@890,554   aria="说说你的想法或任务，上传参考、输入文字或"
//     └ DIV (relative w-full max-w-full flex-1 …) 357×84@890,554
//       └ DIV.contents 0×0@0,0
//         ├ DIV.tiptap.ProseMirror  357×84@890,554   ← contenteditable=true，真正能打字的那层
//         └ DIV.relative.col-start-1.row-start-1 … 357×84@890,554  ← **占位符层，叠在它上面**
//
// 输入框内**任意**点，`elementFromPoint` 命中的都是占位符层（DOM 里排在 tiptap **之后** ⇒ z 更上）。
// 我原来断言「落点必须 `contenteditable.contains(落点)`」—— 那是**兄弟关系**，
// 永远 false。正确判据：**落点在 `canvas-agent-session-composer` 之内**。
//
// 🔑 附带收获：抽屉的稳定选择器是
//   `ASIDE[data-testid="canvas-feature-sidecar"]`（aria 逐字 `Agent`，400×696@868,12）
//   —— 前三轮我一直在用「宽 340–460 且贴右边」的几何启发式找它，能用但脆。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const SHOTS = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const OUT = new URL('./_tmp-b62-round4.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);

const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
const statusLine = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
// 抽屉：改用稳定选择器，不再靠几何
const drawer = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-feature-sidecar"]');
  if (!e) return null; const r = e.getBoundingClientRect();
  if (r.width < 1) return null; return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, aria: e.getAttribute('aria-label') }; });
const skillPicker = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-agent-skill-picker"]');
  if (!e || e.getBoundingClientRect().width < 1) return null; const r = e.getBoundingClientRect();
  return { box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, rows: e.querySelectorAll('[data-testid^="canvas-agent-skill-row-"]').length }; });
// 「非技能」的浮层：所有可见 dialog / listbox / popover，逐个报名字
const pops = () => p.evaluate(() => Array.from(document.querySelectorAll('[role="dialog"],[role="listbox"],[role="menu"]'))
  .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1; })
  .map((e) => { const r = e.getBoundingClientRect();
    return { tid: e.getAttribute('data-testid'), role: e.getAttribute('role'),
      box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200) }; }));
const editorState = () => p.evaluate(() => {
  const ce = document.querySelector('.tiptap.ProseMirror[contenteditable="true"]');
  if (!ce) return { found: false };
  const r = ce.getBoundingClientRect();
  const sk = Array.from(ce.querySelectorAll('[data-testid="agent-skill-chip"]')).map((x) => (x.innerText || '').trim());
  return { found: true, box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
    aria: ce.getAttribute('aria-label'), text: (ce.innerText || '').replace(/\n+$/, ''), html: (ce.innerHTML || '').slice(0, 200), skillChips: sk,
    activeIsCE: !!(document.activeElement && document.activeElement.closest('[contenteditable]')) };
});
const clearComposer = async () => { await p.evaluate(() => { const c = document.querySelector('.tiptap.ProseMirror[contenteditable="true"]');
  if (!c) return; c.focus();
  // tiptap 用 document.execCommand 才是「真删除」；直接改 innerHTML 也行，但要发 input
  document.execCommand('selectAll', false, null); document.execCommand('delete', false, null);
  if ((c.innerText || '').trim()) { c.innerHTML = ''; c.dispatchEvent(new InputEvent('input', { bubbles: true, data: '', inputType: 'deleteContentBackward' })); } });
  await p.waitForTimeout(450); return editorState(); };
const clickRe = async (re) => { const h = await p.evaluate((src) => { const rx = new RegExp(src);
    const e = Array.from(document.querySelectorAll('button,[role="button"]')).filter((x) => { const r = x.getBoundingClientRect(); return r.width > 1 && r.height > 1; })
      .find((x) => rx.test(x.getAttribute('aria-label') || '') || rx.test((x.innerText || '').trim()));
    if (!e) return null; const r = e.getBoundingClientRect();
    const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    const o = (document.elementFromPoint(cx, cy) || {}).closest?.('button,[role="button"]');
    return { cx, cy, aria: e.getAttribute('aria-label'), ok: !!o && (o === e || e.contains(o)) }; }, re.source);
  if (!h) return { ok: false, why: 'notfound' }; if (!h.ok) return { ok: false, why: 'occluded', h };
  await p.mouse.click(h.cx, h.cy); await p.waitForTimeout(900); return h; };
// 聚焦输入框：判据改成「落点在 composer 容器内」
const focusEditor = async () => {
  const c = await p.evaluate(() => { const e = document.querySelector('.tiptap.ProseMirror[contenteditable="true"]'); if (!e) return null;
    const box = e.closest('[data-testid="canvas-agent-session-composer"]'); if (box) box.scrollIntoView({ block: 'center' });
    const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + 24), cy: Math.round(r.y + 24) }; });
  if (!c) return { ok: false, why: 'noeditor' };
  const land = await p.evaluate(([x, y]) => { const t = document.elementFromPoint(x, y); if (!t) return { tag: null };
    const box = document.querySelector('[data-testid="canvas-agent-session-composer"]');
    return { tag: t.tagName, cls: String(t.className || '').slice(0, 50),
      inComposer: !!(box && (box === t || box.contains(t))), isPlaceholderLayer: /col-start-1/.test(String(t.className || '')),
      pointerEvents: getComputedStyle(t).pointerEvents }; }, [c.cx, c.cy]);
  if (!land.inComposer) return { ok: false, why: 'occluded', c, land };
  await p.mouse.click(c.cx, c.cy); await p.waitForTimeout(500);
  const g = await keyGuard(p);
  const foc = await p.evaluate(() => { const a = document.activeElement;
    return { tag: a && a.tagName, inCE: !!(a && a.closest && a.closest('[contenteditable]')), isEditor: !!(a && a.closest && a.closest('.tiptap.ProseMirror')) }; });
  return { ok: foc.isEditor, c, land, focus: foc, keyGuard: g.reason };
};
const closePops = async (max = 5) => { const log = [];
  for (let i = 0; i < max; i++) { const pk = await skillPicker(); const ps = await pops();
    if (!pk && !ps.length) { log.push('(无浮层)'); return log; }
    await p.keyboard.press('Escape'); await p.waitForTimeout(850);
    log.push(`Esc#${i + 1} 收到 ${[pk && 'skill-picker', ps.length + ' pop'].filter(Boolean).join('+')}`); }
  return log; };
const shot = async (n) => { await p.screenshot({ path: new URL(n, SHOTS).pathname, clip: { x: 860, y: 8, width: 412, height: 700 } }); console.log('  📷', n); return n; };
const dense = async (label, TT) => { const ser = []; const t0 = Date.now();
  for (const t of TT) { const w = t0 + t - Date.now(); if (w > 0) await p.waitForTimeout(w);
    const s = { t, picker: (await skillPicker()) ? 'YES' : 'no', pops: await pops(), ed: await editorState() };
    ser.push({ t, picker: s.picker, pops: s.pops.map((x) => `${x.tid || x.role}${x.text ? ' «' + x.text.slice(0, 60) + '»' : ' «空»'}`), text: s.ed.text, html: s.ed.html, skillChips: s.ed.skillChips, activeIsCE: s.ed.activeIsCE });
    console.log(`    t=${String(t).padStart(4)}ms picker=${s.picker} pops=${JSON.stringify(ser[ser.length - 1].pops)}`);
    console.log(`            editor.text=${JSON.stringify(s.ed.text)} chips=${JSON.stringify(s.ed.skillChips)} 焦点在编辑区=${s.ed.activeIsCE}`); }
  return ser; };

const out = { startedAt: new Date().toISOString() };
const c0 = await credit();
console.log('=== 批次 62 第四轮：`/` 与 `@` 收口 ===\n起点:', await statusLine(), '| 积分', c0);
out.creditStart = c0;
if (!(await drawer())) { const rb = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button'))
    .find((x) => /与\s*AI\s*对话/.test(x.getAttribute('aria-label') || '')); if (!e) return null;
    const r = e.getBoundingClientRect(); return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; });
  if (!rb) { console.error('ABORT: 找不到按钮'); await b.close(); process.exit(1); }
  await p.mouse.click(rb.cx, rb.cy); await p.waitForTimeout(1600); }
console.log('抽屉（稳定选择器）:', JSON.stringify(await drawer()));
console.log('清浮层:', JSON.stringify(await closePops()));
await shot('62-agent-empty.png');

const TT = [0, 300, 700, 1200, 1800, 2600, 3600];

// ── B：空输入框按 `/`
console.log('\n【B】空输入框按「/」');
const cb = await clearComposer();
console.log('  清空后:', JSON.stringify({ text: cb.text, chips: cb.skillChips }));
const fb = await focusEditor();
console.log('  聚焦:', JSON.stringify(fb));
if (!fb.ok) { console.error('ABORT: 聚焦失败'); await b.close(); process.exit(12); }
console.log('  keyGuard 判定:', fb.keyGuard, '—— 本轮**故意**往输入框打字，落点已断言在 composer 内');
await p.keyboard.press('/');
out.slash = await dense('slash', TT);
const slashPicker = out.slash.some((x) => x.picker === 'YES');
const slashPop = out.slash.flatMap((x) => x.pops);
console.log('  => `/` 后技能选择器:', slashPicker ? 'YES' : 'no', '| 出现过浮层:', JSON.stringify([...new Set(slashPop)]));

// ── C：空输入框按 `@`
console.log('\n【C】空输入框按「@」');
console.log('  关浮层:', JSON.stringify(await closePops()));
console.log('  清空后:', JSON.stringify((await clearComposer()).text));
const fc = await focusEditor();
console.log('  聚焦:', JSON.stringify(fc));
if (!fc.ok) { console.error('ABORT: 聚焦失败'); await b.close(); process.exit(13); }
await p.keyboard.press('@');
out.at = await dense('at', TT);
const atPop = [...new Set(out.at.flatMap((x) => x.pops))];
console.log('  => `@` 后出现过的浮层:', JSON.stringify(atPop));
await shot('62-agent-at.png');

// ── D：点 skill chip → 带 chip 的输入卡
console.log('\n【D】点 skill chip 后的输入卡');
console.log('  关浮层:', JSON.stringify(await closePops()));
console.log('  清空后:', JSON.stringify((await clearComposer()).text));
const hd = await clickRe(/^视频反解$|^\/\s*视频反解$/);
await p.waitForTimeout(1300);
const ed = await editorState();
console.log('  点击:', JSON.stringify(hd));
console.log('  editor:', ed.box, '| text =', JSON.stringify(ed.text), '| skillChips =', JSON.stringify(ed.skillChips));
console.log('  editor.innerHTML =', ed.html);
out.chip = { click: hd, editor: ed };
await shot('62-agent-skill-chip.png');

const c1 = await credit();
console.log('\n=== 积分全程 ===', c0, '->', c1, 'Δ=', c1 - c0);
out.creditEnd = c1;

// ── 收尾
const finEd = await clearComposer();
console.log('收尾 editor:', JSON.stringify({ text: finEd.text, chips: finEd.skillChips, html: finEd.html }));
const left = (finEd.text || '').trim() || (finEd.skillChips || []).length;
console.log('  残留检查:', left ? '<< 仍有内容 ✗' : '<< 已清空 ✓');
await p.evaluate(() => { const c = document.querySelector('.tiptap.ProseMirror[contenteditable="true"]'); if (c) c.blur(); });
await p.waitForTimeout(300);
console.log('点收起:', JSON.stringify(await clickRe(/^收起$/)));
await p.waitForTimeout(1100);
console.log('关浮层:', JSON.stringify(await closePops()));
for (let i = 0; i < 3; i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(280); }
console.log('终态:', await statusLine(), '| 积分', await credit(), '| 抽屉 =', (await drawer()) === null ? 'null ✓' : '还开着 ✗', '| 浮层 =', JSON.stringify(await pops()));
out.end = { status: await statusLine(), credit: await credit(), drawer: (await drawer()) === null, pops: await pops(), residue: left };
writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log('写入', OUT.pathname);
await b.close();
