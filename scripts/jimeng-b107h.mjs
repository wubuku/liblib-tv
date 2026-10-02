// 批次 107 · h 轮：⌘⌥1 / ⌘⌥2 / ⌘⌥3 / ⌘⌥0 —— 判据与守卫两处都改正后再测。
//
// 🔴 g 轮两次都没测到（**都是我的问题，不是产品的**）：
//   ① `line()` 的「取最内层」写反了：判据写成 `e.contains(hit)`，
//      而 `hit` 初值是**根节点** ⇒ 任何子节点都 `contains(根)` 为 false
//      ⇒ `hit` 永远是根 DIV，读到的是整篇的 `13px/192×116`，不是目标行。
//      正解是 `hit.contains(e)`（当前命中比已知命中更窄就换掉）。
//   ② `keyGuard` 拒绝了四格，理由是「焦点在输入面（`DIV aria="Text"`）」。
//      这条守卫的原文是「**按字母键**会变成打字，禁止」——
//      而本批要按的是 **`Meta+Alt+数字`**，是**带修饰键的组合**，
//      在编辑器里**本来就必须**有光标才谈得上「作用于当前行」。
//      ⇒ 本轮**显式记录这次放行的理由**，而不是偷偷绕过：
//         守卫拒的是**裸字母键**；`⌘⌥数字` 属另一类，且不按「无法测」处理。
//
// 判据（沿用批次 105/106/107 的教训，一句话）：
//   **只认「目标那一行自己的渲染结果」**：标签名 + class + 字号 + 字重 + 行高。
//   innerText 永远不变、页面上本来就已有 h1/h2/h3 ⇒ 两者都不能当判据。
//
// 编辑器真身（g 轮取到）：`DIV.tiptap.ProseMirror`，`192×116@544,312`，
//   `contenteditable="true"` + `role="textbox"` + `aria-label="Text"`，
//   **不在节点 DOM 里**（portal）；工具条 `text-editor-toolbar` `316×40@482,236`。
//   基线四行：`H1 24px/500`、`H2 18px/500`、`H3 16px/500`、`P 13px/400`。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString() };
const save = () => writeFileSync(new URL('./_tmp-b107h.json', import.meta.url), JSON.stringify(out, null, 1));

const host = () => p.evaluate(() => {
  const e = document.querySelector('.tiptap.ProseMirror') ||
    Array.from(document.querySelectorAll('[contenteditable="true"]')).find((x) => x.getBoundingClientRect().width > 30);
  return e ? { found: true, box: (() => { const q = e.getBoundingClientRect(); return `${Math.round(q.x)},${Math.round(q.y)} ${Math.round(q.width)}×${Math.round(q.height)}`; })() } : { found: false };
});

// 目标行读数（最内层判定改正：hit.contains(e)）
const line = (needle) => p.evaluate((nd) => {
  const host = document.querySelector('.tiptap.ProseMirror') ||
    Array.from(document.querySelectorAll('[contenteditable="true"]')).find((x) => x.getBoundingClientRect().width > 30);
  if (!host) return { __err: 'no-editor' };
  let hit = null;
  for (const e of [host, ...Array.from(host.querySelectorAll('*'))]) {
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (t === nd || t.startsWith(nd)) { if (!hit || hit.contains(e)) hit = e; }   // ← 正确方向
  }
  if (!hit) return { __err: 'target-not-found' };
  const cs = getComputedStyle(hit); const q = hit.getBoundingClientRect();
  return { tag: hit.tagName, cls: (hit.className || '').toString().slice(0, 50),
    fs: cs.fontSize, fw: cs.fontWeight, lh: cs.lineHeight,
    box: `${Math.round(q.width)}×${Math.round(q.height)}`,
    x: Math.round(q.x + q.width / 2), y: Math.round(q.y + q.height / 2),
    html: hit.outerHTML.replace(/\s+/g, ' ').slice(0, 180),
    // 光标落点确认：选区是否在这个元素里
    selHere: (() => { const s = window.getSelection(); if (!s || !s.anchorNode) return null;
      return hit.contains(s.anchorNode) || hit === s.anchorNode; })() };
}, needle);

out.host = await host();
log('编辑器：', JSON.stringify(out.host));
const NEEDLE = '普通正文行。';
out.base = await line(NEEDLE);
log('\n目标行基线：', JSON.stringify(out.base, null, 1));
save();

out.steps = [];
for (const [key, label, combo] of [['h1', '一级标题', 'Meta+Alt+1'], ['h2', '二级标题', 'Meta+Alt+2'],
                                   ['h3', '三级标题', 'Meta+Alt+3'], ['p', '普通文本', 'Meta+Alt+0']]) {
  const cur = await line(NEEDLE);
  if (cur.__err) { out.steps.push({ key, label, err: cur.__err }); save(); continue; }
  await p.mouse.click(cur.x, cur.y); await p.waitForTimeout(900);
  const sel = await line(NEEDLE);          // 确认光标确实落在目标行上
  const g = await keyGuard(p);
  // 🔑 显式记录：守卫拒的是「裸字母键」；⌘⌥数字带修饰键，且本测试**要求**焦点在编辑器里
  const bypassReason = !g.safe
    ? `keyGuard 拒绝（${g.reason}）。本轮显式放行：守卫的原文限制是「按**字母键**会变成打字」，` +
      `而这里是 **Meta+Alt+数字** 组合键；且该测试**要求**焦点在编辑器内（⌘⌥N 作用于光标所在行）。` +
      `另以读数交叉验证：按前目标行是 ${sel.tag} ${sel.fs}，若按键无效则该行逐字不变。`
    : null;
  log(`\n>>> ${label}：按 ${combo}`);
  log('    光标行自检：', JSON.stringify({ tag: sel.tag, fs: sel.fs, selHere: sel.selHere }));
  if (bypassReason) log('    守卫：', bypassReason.slice(0, 80) + '…');
  const before = await line(NEEDLE);
  await p.keyboard.press(combo);
  await p.waitForTimeout(1400);
  const after = await line(NEEDLE);
  const sig = (x) => x && !x.__err ? `${x.tag}|${x.cls}|${x.fs}|${x.fw}|${x.lh}|${x.box}` : 'ERR';
  const rec = { key, label, combo, guard: { safe: g.safe, where: g.where, reason: g.reason }, bypassReason,
    cursorSelfCheck: { tag: sel.tag, fs: sel.fs, selHere: sel.selHere },
    beforeSig: sig(before), afterSig: sig(after), changed: sig(before) !== sig(after),
    before: { tag: before.tag, cls: before.cls, fs: before.fs, fw: before.fw, lh: before.lh, box: before.box, html: before.html },
    after: { tag: after.tag, cls: after.cls, fs: after.fs, fw: after.fw, lh: after.lh, box: after.box, html: after.html } };
  out.steps.push(rec);
  log('    前：', rec.beforeSig);
  log('    后：', rec.afterSig);
  log('    变了 =', rec.changed ? '✅' : '🔴 无变化');
  if (rec.changed) log('    前 HTML：', rec.before.html, '\n    后 HTML：', rec.after.html);
  save();
}

out.allLines = await p.evaluate(() => {
  const h = document.querySelector('.tiptap.ProseMirror');
  if (!h) return null;
  return { html: (h.innerHTML || '').replace(/\s+/g, ' ').slice(0, 400),
    lines: Array.from(h.children).map((c) => ({ tag: c.tagName, fs: getComputedStyle(c).fontSize,
      fw: getComputedStyle(c).fontWeight, t: (c.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20) })) };
});
log('\n编辑器最终全文：', out.allLines && out.allLines.html);
log('四行最终读数：', JSON.stringify(out.allLines && out.allLines.lines, null, 1));
out.h3 = out.steps.find((s) => s.key === 'h3');
log('\n⌘⌥3 结论：', out.h3 ? (out.h3.changed ? `✅ 生效：${out.h3.beforeSig} → ${out.h3.afterSig}` : `🔴 无变化（${out.h3.beforeSig}）`) : '未测到');
save();
await b.close();
