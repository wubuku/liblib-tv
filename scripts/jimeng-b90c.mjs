// 批次 90 · C：`⌘/` 到底是不是**开关**。
//
// b 轮 P11 证实了「⌘/ 能打开 Agent 抽屉」，但 P11b **证伪了「再按一次能关闭」** ——
// 连按两次后抽屉仍在。若手册写的是「⌘/ 开关面板」，这条排障建议就是错的。
//
// 🔑 但先别急着下结论 —— 批次 84 已经钉过一件事：
//     **抽屉开着时焦点被接管**，此后的按键去向会变。
//     所以「第二次 ⌘/ 无效」有三种可能，必须分开：
//       (a) ⌘/ 本来就**不是**开关（只开不关）；
//       (b) 焦点在抽屉里，第二次 ⌘/ 被输入框吃掉了；
//       (c) 两次按得太快，第二次落在打开动画里。
//
// ⇒ 可证伪预测 **P1**：先把焦点交还画布（点空白画布，不点任何节点），
//   再按 ⌘/ ⇒ 应当能关闭。若仍不能 ⇒ (a) 成立。
//   同时对照 **P2**：抽屉开着时按普通字母键，看它去了哪（批次 84 已记「字母进输入框」）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const selCount = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
const credits = async () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-commerce-entry"]'); return e ? e.getAttribute('aria-label') : null; });
const open = () => p.evaluate(() => !!document.querySelector('[data-testid="canvas-feature-sidecar"]'));
const active = () => p.evaluate(() => { const a = document.activeElement; if (!a) return null;
  return { tag: a.tagName, tid: a.getAttribute('data-testid'), aria: a.getAttribute('aria-label'), cls: String(a.className || '').slice(0, 40) }; });
const composerVal = () => p.evaluate(() => { const c = document.querySelector('[data-testid="prompt-composer"]');
  const i = c && (c.querySelector('textarea') || c.querySelector('input') || (c.querySelector('[contenteditable]'))); return i ? (i.value ?? i.innerText) : null; });

log('起点：抽屉开着 =', await open(), '｜sel =', await selCount());

// P2：抽屉开着时按普通字母，看它去了哪（批次 84 已记「字母进输入框」）
await p.keyboard.press('KeyQ'); await p.waitForTimeout(700);
out.p2 = { active: await active(), composer: await composerVal() };
log('P2 按 Q 后：焦点', JSON.stringify(out.p2.active), '｜composer 内容 =', JSON.stringify(out.p2.composer));
await p.keyboard.press('Backspace'); await p.waitForTimeout(400);

// P1：把焦点交还画布（点空白），再按 ⌘/
const blank = await p.evaluate(() => { const r = document.querySelector('.react-flow__pane') || document.querySelector('[data-testid="canvas-main-region"]');
  if (!r) return null; const q = r.getBoundingClientRect(); return { x: Math.round(q.x + 24), y: Math.round(q.y + q.height - 24) }; });
log('空白落点：', JSON.stringify(blank));
if (blank) { await p.mouse.click(blank.x, blank.y); await p.waitForTimeout(800); }
out.afterBlank = { active: await active(), open: await open() };
log('点空白后：焦点', JSON.stringify(out.afterBlank.active), '｜抽屉', out.afterBlank.open);

await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1400);
out.p1 = { openAfterSecond: await open(), active: await active() };
log('P1 焦点回画布后再按 ⌘/ ⇒ 抽屉', out.p1.openAfterSecond, '｜焦点', JSON.stringify(out.p1.active));

// 对照组：Esc 能不能关
if (await open()) {
  await p.keyboard.press('Escape'); await p.waitForTimeout(1000);
  out.esc = { open: await open(), active: await active() };
  log('对照 Esc ⇒ 抽屉', out.esc.open, '｜焦点', JSON.stringify(out.esc.active));
}
// 终态：确保抽屉关着
if (await open()) { await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1200); }
out.end = { open: await open(), sel: await selCount(), credits: await credits() };
log('终态：', JSON.stringify(out.end), '｜积分未变 =', out.start?.credits);
out.verdict = { toggleWorks: out.p1.openAfterSecond === false, escCloses: out.esc ? out.esc.open === false : null };
log('判定：', JSON.stringify(out.verdict));
writeFileSync(new URL('./_tmp-b90c.json', import.meta.url), JSON.stringify(out, null, 1));
await b.close();
