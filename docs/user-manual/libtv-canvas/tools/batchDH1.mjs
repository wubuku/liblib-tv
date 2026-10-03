// Batch DH-1：验证 `z-[180]` 的 `duration-200` 为什么算出来是 `0s`。
//
// DH-0 的硬读数：
//   class: pointer-events-none fixed inset-0 z-[180] motion-safe:transition-opacity motion-safe:duration-200
//   计算样式: transitionProperty = all，**transitionDuration = 0s**，getAnimations() = []
// ⭐⭐ class 写了 `duration-200`（=200ms），算出来却是 `0s` ⇒ **规则没生效**。
//   最可能：⭕ **`motion-safe:` = `@media (prefers-reduced-motion: no-preference)`**，
//   而**无头浏览器默认报 `prefers-reduced-motion: reduce`** ⇒ 整条规则不匹配。
//
// ⚠️⚠️ 这一条如果成立，影响面很大（不只 z-180）：
//   **`motion-safe:` 前缀的动画在这个测试环境里全部不生效** ——
//   那么此前所有「某元素没有动画 / 淡入淡出读不出来」的结论都要打问号。
//   ⇒ 本步必须先量 `matchMedia('(prefers-reduced-motion: reduce)').matches`。
//
// 顺带：这也可能是「z-[180] 一直不亮」的**真正原因之一** ——
//   如果它靠 `motion-safe:transition-opacity` 淡入，而规则被这条 media query 关掉了…（待验）
import { launch, open, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = {};

const { browser, page } = await launch();
await open(page, URL_);
await page.waitForTimeout(3000);

out.环境 = await page.evaluate(() => ({
  'prefers-reduced-motion: reduce': window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  'prefers-reduced-motion: no-preference': window.matchMedia('(prefers-reduced-motion: no-preference)').matches,
  'prefers-color-scheme: dark': window.matchMedia('(prefers-color-scheme: dark)').matches,
  'pointer: fine': window.matchMedia('(pointer: fine)').matches,
  UA: navigator.userAgent.slice(0, 110),
  webdriver: navigator.webdriver,
}));
LOG('══════════ 媒体特性 ══════════');
for (const [k, v] of Object.entries(out.环境)) LOG(`  ${k} = ${v}`);

// ⭐ 直接验证：把 reduced-motion 模拟成 no-preference，再看 duration 变不变
out.改前 = await page.evaluate(() => {
  const t = [...document.querySelectorAll('body *')].find((e) => {
    const s = getComputedStyle(e);
    return s.position === 'fixed' && s.zIndex === '180' && e.getBoundingClientRect().width > 1000;
  });
  if (!t) return { 找到: false };
  const s = getComputedStyle(t);
  return { transitionDuration: s.transitionDuration, transitionProperty: s.transitionProperty, class: (t.className || '').toString() };
});
LOG(`\n改之前: ${JSON.stringify(out.改前)}`);

// ⭐⭐ 用 CDP 覆盖 prefers-reduced-motion = no-preference
try {
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'no-preference' }] });
  await page.waitForTimeout(1500);
  out.改后 = await page.evaluate(() => {
    const t = [...document.querySelectorAll('body *')].find((e) => {
      const s = getComputedStyle(e);
      return s.position === 'fixed' && s.zIndex === '180' && e.getBoundingClientRect().width > 1000;
    });
    if (!t) return { 找到: false };
    const s = getComputedStyle(t);
    return {
      reduce: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
      transitionDuration: s.transitionDuration, transitionProperty: s.transitionProperty,
    };
  });
  LOG(`⭐ 覆盖成 no-preference 之后: ${JSON.stringify(out.改后)}`);
  out.覆盖有效 = out.改后?.transitionDuration !== out.改前?.transitionDuration;
  LOG(`⭐ duration 有没有变: ${out.覆盖有效 ? '✅ 变了 ⇒ 确认是 reduced-motion 关掉了 motion-safe 规则' : '⛔ 没变 ⇒ 另有原因'}`);
} catch (e) {
  LOG(`⛔ CDP 覆盖失败: ${String(e).slice(0, 120)}`);
  out.覆盖有效 = null;
}

await writeFile(new URL('./batchDH1.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDH1.json ===');
await browser.close();
