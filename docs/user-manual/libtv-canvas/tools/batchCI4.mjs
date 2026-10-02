// Batch CI-4：把 `reducedMotion: 'reduce'` 这个盲区坐实，并拍到真正给用户看的那张图。
//
// CI-3 的决定性读数（祖先链逐层量出来的，不是猜的）：
//   [0] button.peer.rounded-full.bg-white…「取消ESC」      opacity=1 累计=1
//   [1] span.relative.ml-1.inline-flex                    opacity=1 累计=1
//   [2] div.flex.gap-2.rounded-b-xl.border.text-white      opacity=1 累计=1   ← 白底容器，174×34
//   [3] div.pointer-events-none.fixed.z-[305].motion-safe: opacity=0 累计=0  ⭐ 就是这一层
//   [4] body / [5] html                                    累计=0
//
// ⭐⭐⭐ 也就是说：**不是没画出来给用户看，是我们自己的浏览器把它藏了。**
//    Tailwind 的 `motion-safe:` 变体 = 「用户没要求减少动效时才启用」，
//    而 `lib.mjs` 为了让截图可比，一直把 `reducedMotion` 设成 `'reduce'`。
//    ⇒ **本手册此前所有截图里，凡是 `motion-safe:` 门控的元素，一个都没出现过。**
//    这是一条影响全批的判据缺陷，不是一枚按钮的小事。
//
// 本步：
//   ① 用 `reducedMotion:'no-preference'` 重开，验证横幅累计 opacity 变 1；
//   ② 读全那层的完整 class，坐实变体名；
//   ③ 找同页**所有** `motion-safe:` 门控的元素（CI-3 只撞见两个：z-[305] 横幅、z-[180] 全屏层），
//      全屏那个必须查清 —— 万一它在默认用户那里是**盖住整屏的蒙层**，性质完全不同；
//   ④ 拍一张**名副其实**的图放进手册。
// ⛔ 仍然不点「取消」。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

// ⭐ 本步**故意**用 'no-preference'（真实用户的默认值），和前面几遍相反。
const { browser, page } = await launch({ reducedMotion: 'no-preference' });
const out = {};
const MOTION = await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches);
console.log('本上下文 prefers-reduced-motion:reduce =', MOTION, '（应为 false）');

await open(page, URL_);
await closePromos(page);
await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.reload({ waitUntil: 'domcontentloaded' });
await page.waitForTimeout(6500);
await closePromos(page);
await page.waitForTimeout(1800);

// ① ② 累计 opacity + 完整 class
out.横幅 = await page.evaluate(() => {
  const el = document.querySelector('[aria-label="退出跟随"]');
  if (!el) return { 有: false };
  let box = el;
  while (box.parentElement && !/border/.test(box.parentElement.className || '')) box = box.parentElement;
  const wrapper = box.parentElement;
  let acc = 1;
  const chain = [];
  for (let a = box; a; a = a.parentElement) {
    acc *= Number(getComputedStyle(a).opacity);
    chain.push({ cls: (a.className || '').toString(), opacity: getComputedStyle(a).opacity });
    if (a.tagName === 'HTML') break;
  }
  const r = box.getBoundingClientRect();
  return {
    有: true,
    累计opacity: Math.round(acc * 1000) / 1000,
    容器完整class: (box.className || '').toString(),
    外层完整class: (wrapper.className || '').toString(),
    外层opacity: getComputedStyle(wrapper).opacity,
    全文: (box.innerText || '').replace(/\s+/g, ' ').trim(),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    链: chain,
  };
});
console.log('\n════ 横幅（motion 允许后）════');
console.log('累计opacity =', out.横幅.累计opacity);
console.log('外层完整class =', out.横幅.外层完整class);
console.log('外层opacity =', out.横幅.外层opacity);
console.log('容器全文 =', out.横幅.全文, ' rect =', out.横幅.rect);

// ③ 全页 `motion-safe:` 门控元素总览 —— 有没有第二个「盖住整屏的」
out.motionSafe元素 = await page.evaluate(() => {
  const rows = [];
  for (const a of document.querySelectorAll('*')) {
    const cls = (a.className || '').toString();
    if (!/motion-safe:/.test(cls)) continue;
    const r = a.getBoundingClientRect();
    const cs = getComputedStyle(a);
    let acc = 1;
    for (let p = a; p; p = p.parentElement) { acc *= Number(getComputedStyle(p).opacity); if (p.tagName === 'HTML') break; }
    rows.push({
      cls: cls.slice(0, 150),
      尺寸: [Math.round(r.width), Math.round(r.height)],
      rect: [Math.round(r.x), Math.round(r.y)],
      position: cs.position,
      zIndex: cs.zIndex,
      pointerEvents: cs.pointerEvents,
      自身opacity: cs.opacity,
      累计opacity: Math.round(acc * 1000) / 1000,
      内含可交互元素数: a.querySelectorAll('button,a,input,[role="button"]').length,
      文字: (a.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40),
    });
  }
  return rows;
});
console.log('\n════ 全页 motion-safe: 门控元素 ════');
for (const r of out.motionSafe元素) {
  console.log(`  尺寸=${JSON.stringify(r.尺寸)} @${r.rect} ${r.position}/z=${r.zIndex} 自身op=${r.自身opacity} 累计op=${r.累计opacity} 可交互=${r.内含可交互元素数}`);
  console.log(`    class=${r.cls}`);
  console.log(`    文字=${JSON.stringify(r.文字)}`);
}

// ④ 拍图：横幅 + 一点上下文（顶栏），只截真正该出现的那块
if (out.横幅.有 && out.横幅.累计opacity > 0.5) {
  const [x, y] = out.横幅.rect;
  await shot(page, 'M-327-顶栏正在跟随横幅.png', { clip: { x: Math.max(0, x - 300), y: 0, width: 780, height: 84 } });
  console.log('\n已拍 M-327-顶栏正在跟随横幅.png');
  await shot(page, 'M-328-顶栏整条含跟随横幅.png');
  console.log('已拍 M-328-顶栏整条含跟随横幅.png');
} else {
  console.log('\n⚠️ 累计opacity 仍 ≤0.5，**不拍图**（宁可没有图，也不要名不副实的图）');
}

await writeFile(resolve(HERE, '.evidence/ci4-motion-safe.json'), JSON.stringify(out, null, 2));
console.log('\n（本步只读，未点「取消」）');
await browser.close();
