// Batch AS8 —— 只补一张图：工具箱卡片 hover 之后「使用」按钮显形。
//
// 为什么要专门跑一轮：AS7 读到了 29 个 `使用` 按钮（`50×24`），但 M-129 截图里
// **一个都看不见**。这跟故事板那个「对话」按钮是同一类 —— **平时 opacity 为 0，
// 悬停卡片才显形**（§16.2 已经为故事板那枚记过一遍）。
//
// 判据：**先量未 hover 时的 opacity，再 hover 再量一次**。
// 两次读数相同 → 说明它不是 hover 才显形，那 M-129 里看不见就是别的原因
//（比如被预览图盖住）—— 这两种情况必须分开，不能只拍一张 hover 图就下结论。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep } from './scenario.mjs';

const SPACE = '10354929';
const B = 'batchAS8';
const { browser, page } = await launch();

const clickAria = async (aria) => {
  const h = await page.evaluate((a) => {
    const e = [...document.querySelectorAll('button,[role="button"],[aria-label]')]
      .filter((x) => (x.getAttribute('aria-label') || '').trim() === a)
      .map((x) => { const r = x.getBoundingClientRect();
        return { visible: r.width > 2 && r.height > 2, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
      .find((x) => x.visible);
    return e || { err: '找不到可见的 aria-label="' + a + '"' };
  }, aria);
  if (h.err) return h;
  await page.mouse.click(h.cx, h.cy); await page.waitForTimeout(2600);
  return h;
};
const clickText = async (t) => {
  const h = await page.evaluate((s) => {
    const el = [...document.querySelectorAll('div,li,button,span,a')]
      .filter((e) => (e.innerText || '').trim() === s)
      .map((e) => { const r = e.getBoundingClientRect();
        return { area: Math.round(r.width * r.height), visible: r.width > 2 && r.height > 2,
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
      .filter((x) => x.visible).sort((a, b) => a.area - b.area)[0];
    return el || { err: '找不到可见的「' + s + '」' };
  }, t);
  if (h.err) return h;
  await page.mouse.click(h.cx, h.cy); await page.waitForTimeout(3200);
  return h;
};
/** 卡片容器的几何（找得到就用，不依赖 class）。 */
const cardGeom = () => page.evaluate(() => {
  const cards = [...document.querySelectorAll('div')].filter((e) => {
    const r = e.getBoundingClientRect();
    const s = getComputedStyle(e);
    return /aspect-square/.test((e.className || '').toString()) && r.width > 140 && r.height > 140
      && s.visibility !== 'hidden' && +s.opacity > 0.05;
  }).map((e) => { const r = e.getBoundingClientRect();
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
      name: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) }; })
    .sort((a, b) => (a.rect[1] - b.rect[1]) || (a.rect[0] - b.rect[0]));
  return { count: cards.length, first: cards[0], second: cards[1], all: cards.slice(0, 6) };
});
/** 该卡片里那枚「使用」按钮的 opacity —— 读**它自己**的，不用容器推。 */
const useBtnState = (card) => page.evaluate((c) => {
  const hit = [...document.querySelectorAll('button')].filter((b) => (b.innerText || '').trim() === '使用')
    .map((b) => { const r = b.getBoundingClientRect(); const s = getComputedStyle(b);
      return { inside: r.x >= c[0] - 4 && r.y >= c[1] - 4 && r.x + r.width <= c[0] + c[2] + 4 && r.y + r.height <= c[1] + c[3] + 4,
        opacity: s.opacity, visibility: s.visibility, display: s.display,
        area: Math.round(r.width * r.height),
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
    .filter((x) => x.inside)[0];
  return hit || { err: '这张卡片里找不到「使用」按钮' };
}, card);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await beginBatch(B, { note: '补拍工具箱卡片 hover 后「使用」按钮显形；先量未 hover 的 opacity' });

  const out = {};
  out.libBtn = await clickAria('素材库');
  out.tbBtn = await clickText('打开工具箱');
  await page.waitForTimeout(1200);
  out.cards = await cardGeom();
  console.log('AS8 卡片:', JSON.stringify(out.cards).slice(0, 900));
  if (!out.cards.first) throw new Error('找不到卡片容器');

  // ① **未 hover** 时量一次
  out.beforeHover = await useBtnState(out.cards.first.rect);
  await shot(page, 'M-130-工具箱-未悬停.png');
  console.log('AS8 未悬停:', JSON.stringify(out.beforeHover));

  // ② hover 到第一张卡片，再量
  await page.mouse.move(out.cards.first.cx, out.cards.first.cy);
  await page.waitForTimeout(1600);
  out.afterHover = await useBtnState(out.cards.first.rect);
  console.log('AS8 悬停后:', JSON.stringify(out.afterHover));
  await shot(page, 'M-131-工具箱-悬停显示使用.png');

  // ③ 换第二张，确认不是「只有第一张特殊」
  if (out.cards.second) {
    await page.mouse.move(out.cards.second.cx, out.cards.second.cy);
    await page.waitForTimeout(1600);
    out.secondHover = await useBtnState(out.cards.second.rect);
    console.log('AS8 第二张悬停:', JSON.stringify(out.secondHover));
  }

  const b = out.beforeHover || {}, a = out.afterHover || {};
  out.verdict = b.err || a.err ? '有一侧没读到按钮'
    : (parseFloat(b.opacity) === 0 && parseFloat(a.opacity) > 0)
      ? `「使用」按钮**未悬停时 opacity ${b.opacity}、悬停后 ${a.opacity}** —— 确认是 hover 才显形`
      : `未悬停 opacity ${b.opacity}、悬停后 ${a.opacity} —— 不是 hover 才显形，另有原因`;
  console.log('AS8:', out.verdict);

  await logStep(B, {
    id: 'AS8-toolbox-hover', title: '工具箱卡片「使用」按钮：未悬停 vs 悬停后各量一次',
    target: '**先量未 hover 的 opacity 再 hover 重量**，两次读数不同才下「hover 才显形」的结论',
    evidence: out,
    visible_text: `未悬停：${JSON.stringify(out.beforeHover)}；悬停后：${JSON.stringify(out.afterHover)}。结论：${out.verdict}`,
    shot: 'M-131-工具箱-悬停显示使用.png',
  });
  console.log('AS8 完成');
} finally {
  await browser.close();
}
