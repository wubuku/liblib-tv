// 批次 90 · D：用**强判据**重测「⌘/ 是不是开关」。
//
// 🔴 **c 轮自伤**：我用 `!!document.querySelector('[data-testid="canvas-feature-sidecar"]')`
//     当「抽屉开着」的判据。**批次 84 早就钉过它折叠后元素仍在 DOM 里**
//     （`200×348@1068,360` + `pointer-events: none` + **0 个可见元素**）。
//     ⇒ 我的判据把「折叠」也读成「开着」，于是「⌘/ 关不掉」这个结论**不成立**。
//     这与概念页 988「『收起』不等于『关闭』—— 读数没变，可能是尺子量错了量程」同型。
//
// ⇒ 强判据（三项一起读，缺一不可）：
//     ① 屏上尺寸     展开 `400×696@868,12` ／ 折叠 `200×348@1068,360`
//     ② `pointer-events`  展开 `auto` ／ 折叠 `none`
//     ③ **有面积的可见子元素数**  展开 > 0 ／ 折叠 **0**
//
// 可证伪预测 **P1**：⌘/ 是**开关** ⇒ 同一焦点条件下连按两次回到「折叠」。
//   若第二次之后仍是「展开」⇒ 不是开关。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const selCount = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);

// ⚠️ **强判据**：存在性 + 尺寸 + pe + 有面积的可见子元素数，一起读
const state = () => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-feature-sidecar"]');
  if (!e) return { exists: false, verdict: 'ABSENT' };
  const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
  const vis = Array.from(e.querySelectorAll('*')).filter((n) => { const q = n.getBoundingClientRect(); return q.width > 0 && q.height > 0; }).length;
  const box = `${Math.round(r.width)}×${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`;
  const verdict = (box === '400×696@868,12' && cs.pointerEvents === 'auto' && vis > 0) ? 'EXPANDED'
    : (box === '200×348@1068,360' && cs.pointerEvents === 'none' && vis === 0) ? 'COLLAPSED' : `OTHER(${box},pe=${cs.pointerEvents},vis=${vis})`;
  return { exists: true, box, pe: cs.pointerEvents, visChildren: vis, verdict };
});
const active = () => p.evaluate(() => { const a = document.activeElement; return a ? { tag: a.tagName, tid: a.getAttribute('data-testid'), aria: a.getAttribute('aria-label') } : null; });

out.start = { credits: await credits(), sel: await selCount(), state: await state(), active: await active() };
log('起点：', JSON.stringify(out.start));

// 焦点交还画布（点空白），排除「焦点在抽屉里」这一个变量
const blank = await p.evaluate(() => { const r = document.querySelector('.react-flow__pane') || document.querySelector('.rf__wrapper');
  if (!r) return null; const q = r.getBoundingClientRect(); return { x: Math.round(q.x + 24), y: Math.round(q.y + q.height - 24) }; });
if (blank) { await p.mouse.click(blank.x, blank.y); await p.waitForTimeout(800); }
out.onCanvas = { state: await state(), active: await active() };
log('点空白后（焦点回画布）：', JSON.stringify(out.onCanvas));

const press = async (label) => { await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1400);
  const s = await state(); log(`  ${label} ⌘/ ⇒`, JSON.stringify(s)); return s; };
out.s1 = await press('第 1 次');
out.s2 = await press('第 2 次');
out.s3 = await press('第 3 次');

// 收尾：回到「不占画布」的初始态
for (let k = 0; k < 3; k++) { const s = await state(); if (s.verdict !== 'EXPANDED') break; await press('收尾 ⌘/'); }
out.end = { state: await state(), sel: await selCount(), credits: await credits() };
log('终态：', JSON.stringify(out.end), '｜积分未变 =', out.start.credits === out.end.credits);
out.verdict = { s1: out.s1.verdict, s2: out.s2.verdict, s3: out.s3.verdict, end: out.end.state.verdict,
  isToggle: out.s1.verdict !== out.s2.verdict };
log('判定：', JSON.stringify(out.verdict), '｜**⌘/ 是', out.verdict.isToggle ? '开关 ✅' : '不是开关 ❌', '**');
writeFileSync(new URL('./_tmp-b90d.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
