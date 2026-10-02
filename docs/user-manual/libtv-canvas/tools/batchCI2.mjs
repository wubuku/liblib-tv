// Batch CI-2：「正在跟随」横幅的时间线 —— 它到底**画没画出来过**。
//
// CI-1 挖出来的矛盾（这才是关键）：
//   · DOM 里确实有：`span.text-sm`「正在跟随」+ `button[aria-label="退出跟随"]`「取消ESC」
//     + `span.absolute.top-full`「按 ESC 退出」，容器 `div.flex.gap-2.rounded-b-xl.border`
//     174×34，位置 [633, 0]，字体颜色/尺寸都是正常的。
//   · 静置 55 秒纹丝不动（4 次采样都在）。
//   · **可是全屏截图里那个位置什么都没有。**
//
// ⭐ 所以问题不是「有没有这个元素」，而是「**它画出来过吗**」。
//    最像的解释：它是**加载时的一次性 toast** —— 播完淡出，但节点没被卸载。
//    若成立，那么 ①「打开画布就会弹一次，宣布 TV Director 挂上了」；
//    ② §12.2「点故事板 → TV Director 跟着一起来」的**因果是错的**（抽屉开屏就有）。
//
// 本步用 `addInitScript` 在**任何页面脚本之前**埋一个采样器，每 100ms 记一次
// 存在性 + opacity + visibility + transform，**先跑一遍拿时间线**，
// 知道「可见窗口」在第几毫秒之后，**再跑一遍专门去拍那一段**。
// ⛔ 全程只读：不点「取消」、不切模式、不碰节点。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

const INSTRUMENT = () => {
  window.__followLog = [];
  const t0 = performance.now();
  let last = null;
  const sample = () => {
    const el = document.querySelector('[aria-label="退出跟随"]');
    const rec = el
      ? (() => {
          let box = el;
          while (box.parentElement && !/border/.test(box.parentElement.className || '')) box = box.parentElement;
          const cs = getComputedStyle(box);
          const r = box.getBoundingClientRect();
          return {
            t: Math.round(performance.now() - t0),
            在: true,
            opacity: cs.opacity,
            visibility: cs.visibility,
            transform: cs.transform.slice(0, 34),
            宽: Math.round(r.width),
            rect: [Math.round(r.x), Math.round(r.y)],
          };
        })()
      : { t: Math.round(performance.now() - t0), 在: false };
    const key = JSON.stringify({ ...rec, t: 0 });
    if (key !== last) { last = key; window.__followLog.push(rec); }
  };
  sample();
  const id = setInterval(sample, 100);
  setTimeout(() => clearInterval(id), 30000);
};

// ── 第 1 遍：只要时间线，不拍图 ──────────────────────────────────
{
  const { browser, ctx, page } = await launch();
  await ctx.addInitScript(INSTRUMENT);
  await page.goto(URL_, { waitUntil: 'commit', timeout: 60000 });
  await page.waitForTimeout(12000);
  const log = await page.evaluate(() => window.__followLog);
  console.log('════ 第 1 遍：时间线 ════');
  for (const r of log) console.log(`  ${String(r.t).padStart(6)}ms  ${r.在 ? `在 opacity=${r.opacity} vis=${r.visibility} tf=${r.transform} 宽=${r.宽} @${r.rect}` : '不在'}`);
  await writeFile(resolve(HERE, '.evidence/ci2-toast-timeline.json'), JSON.stringify(log, null, 2));
  await browser.close();
}

// 从时间线里推出「可见窗口」：opacity 最大的那一段
const log = JSON.parse(await (await import('node:fs/promises')).readFile(resolve(HERE, '.evidence/ci2-toast-timeline.json'), 'utf8'));
const alive = log.filter((r) => r.在);
const visible = alive.filter((r) => Number(r.opacity) > 0.05 && r.visibility === 'visible');
console.log('\n存在区间 =', alive.length ? `${alive[0].t}ms → ${alive[alive.length - 1].t}ms` : '（不存在）');
console.log('可见区间 =', visible.length ? `${visible[0].t}ms → ${visible[visible.length - 1].t}ms` : '（全程不可见）');

// ── 第 2 遍：冲进那个窗口去拍 ────────────────────────────────────
{
  const { browser, ctx, page } = await launch();
  await ctx.addInitScript(INSTRUMENT);
  await page.goto(URL_, { waitUntil: 'commit', timeout: 60000 });
  const start = visible.length ? Math.max(0, visible[0].t - 300) : 1200;
  const end = visible.length ? visible[visible.length - 1].t + 200 : 6000;
  console.log(`\n════ 第 2 遍：${start}ms → ${end}ms 连拍 ════`);
  const frames = [];
  while (true) {
    const t = await page.evaluate(() => Math.round(performance.now()));
    if (t > end) break;
    if (t >= start) {
      const st = await page.evaluate(() => {
        const el = document.querySelector('[aria-label="退出跟随"]');
        if (!el) return { 在: false };
        let box = el;
        while (box.parentElement && !/border/.test(box.parentElement.className || '')) box = box.parentElement;
        const cs = getComputedStyle(box);
        const r = box.getBoundingClientRect();
        return { 在: true, opacity: cs.opacity, visibility: cs.visibility, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
      });
      if (st.在) {
        const name = `M-325-t${String(t).padStart(5, '0')}-op${st.opacity}.png`;
        await shot(page, name, { clip: { x: Math.max(0, st.rect[0] - 200), y: 0, width: 580, height: 96 } });
        // 画没画出来，用元素栈说话：那个点上谁在最上面
        const stack = await page.evaluate(([cx, cy]) => document.elementsFromPoint(cx, cy).slice(0, 6)
          .map((e) => `${e.tagName.toLowerCase()}.${(e.className || '').toString().slice(0, 26)}`), [st.rect[0] + 60, st.rect[1] + 17]);
        frames.push({ t, opacity: st.opacity, name, 元素栈: stack });
        console.log(`  t=${t}ms opacity=${st.opacity} → ${name}  栈: ${JSON.stringify(stack)}`);
      }
    }
    await page.waitForTimeout(120);
  }
  await writeFile(resolve(HERE, '.evidence/ci2-frames.json'), JSON.stringify(frames, null, 2));
  await browser.close();
}
console.log('\n（本步只读，未点「取消」）');
