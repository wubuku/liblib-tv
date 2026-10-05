/**
 * 批次 226 收尾清理：关掉仍开着的画布浮层（搜索面板），并复核焦点守卫 + 选中态。
 *
 * 为什么单独一个脚本：焦点修复脚本（`jimeng-focus-fix.mjs`）的职责是「把焦点交回画布」，
 * 而收尾门要求画布回到**没有浮层、没有选中**的干净状态 —— 两者是两条不同的判据，
 * 混在一个脚本里就会出现「顺手点一下把 selected 变成 1」的副作用（批次 226 第一版的坑）。
 * 这里只按 Escape（纯键盘、绝无副作用），按完立刻重读状态行与焦点。
 *
 * 用法：node scripts/jimeng-b226-clean.mjs
 */
import { chromium } from 'playwright';
import { keyGuard } from './jimeng-safe-keys.mjs';
import { writeFileSync } from 'node:fs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const page = b.contexts()[0].pages().find((p) => p.url().includes('ai-canvas'));
if (!page) { console.error('找不到画布页面'); process.exit(2); }

const dialogs = () => page.evaluate(() => Array.from(document.querySelectorAll('[role="dialog"]'))
  .filter((e) => e.getBoundingClientRect().width > 1)
  .map((e) => e.getAttribute('data-testid') || e.getAttribute('aria-label') || '(无名对话框)'));
const status = () => page.evaluate(() => {
  const t = document.body.innerText;
  return {
    状态行: (t.match(/[\d]+ nodes?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0] || null,
    缩放: (document.querySelector('button[aria-label^="Zoom options"]') || {}).getAttribute?.('aria-label') || null,
    transform: (() => { const e = document.querySelector('.react-flow__viewport'); return e ? e.style.transform : null; })(),
    积分: (t.match(/(\d[\d,]*)\s*基础会员/) || [])[1] || null,
  };
});

const out = { 步骤: [] };
out.浮层_前 = await dialogs();
console.log('【浮层·前】', JSON.stringify(out.浮层_前));

let n = 0;
while ((await dialogs()).length && n < 4) {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);
  n += 1;
  out.步骤.push({ 第几次: n, 剩余浮层: await dialogs() });
}
out.浮层_后 = await dialogs();
out.状态 = await status();
const g = await keyGuard(page);
out.焦点守卫 = { safe: g.safe, where: g.where, reason: g.reason };

console.log(`【Escape 次数】${n}`);
console.log('【浮层·后】', JSON.stringify(out.浮层_后));
console.log('【状态】', JSON.stringify(out.状态));
console.log(`【焦点守卫】${g.safe ? '✅ 可按字母键' : '⛔ 不可'}（${g.where}）`);

writeFileSync('/tmp/b226-clean.json', JSON.stringify(out, null, 1));
await b.close();