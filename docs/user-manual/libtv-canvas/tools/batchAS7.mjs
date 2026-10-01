// Batch AS7 —— 只把「打开工具箱 → 工具箱弹窗」这一件事做完。
//
// 前面 AS6 又栽在同一类坑上，这次把根因写清楚：
//
//   我用 `[class*="Menu-dropdown"],[class*="Popover-dropdown"],…` 去筛浮层，
//   结果**素材库面板明明开了**（M-128 截图里三行清清楚楚：风格库 NEW / 特效库 NEW /
//   打开工具箱），`diff` 却返回空。
//
//   原因：**这个面板的 class 不是 Mantine 的那几种**（它带一个指向下方的三角，
//   是自定义 popover）。所以「按 class 白名单筛浮层」会**静默漏掉一整类面板**。
//
//   这跟 §17.4 是同一条：**DOM 说没有、截图说明明有 —— 以截图为准，回头修判据。**
//   这次改用 `fingerprint()` / `diffPanels()`：它不认 class，只认「可见 + 面积 + 位置」，
//   所以认不认得 class 都能捞出来。差集按面积升序，**最小的新容器**才是面板本身。
import { launch, open } from './lib.mjs';
import { clearToasts, closePromos, shot, beginBatch, logStep, fingerprint, diffPanels } from './scenario.mjs';

const SPACE = '10354929';
const B = 'batchAS7';
const { browser, page } = await launch();

const clickAria = async (aria) => {
  const h = await page.evaluate((a) => {
    const e = [...document.querySelectorAll('button,[role="button"],[aria-label]')]
      .filter((x) => (x.getAttribute('aria-label') || '').trim() === a)
      .map((x) => { const r = x.getBoundingClientRect();
        return { area: Math.round(r.width * r.height), visible: r.width > 2 && r.height > 2,
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
      .find((x) => x.visible);
    return e || { err: '找不到可见的 aria-label="' + a + '"' };
  }, aria);
  if (h.err) return h;
  await page.mouse.click(h.cx, h.cy); await page.waitForTimeout(2500);
  return h;
};
/** 按文案找可点元素 —— 取**面积最小**的那个（外层容器也会命中同一句文案）。 */
const clickText = async (t) => {
  const h = await page.evaluate((s) => {
    const el = [...document.querySelectorAll('div,li,button,span,a')]
      .filter((e) => (e.innerText || '').trim() === s)
      .map((e) => { const r = e.getBoundingClientRect();
        return { tag: e.tagName, area: Math.round(r.width * r.height), visible: r.width > 2 && r.height > 2,
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })
      .filter((x) => x.visible)
      .sort((a, b) => a.area - b.area)[0];
    return el || { err: '找不到可见的「' + s + '」' };
  }, t);
  if (h.err) return h;
  await page.mouse.click(h.cx, h.cy); await page.waitForTimeout(3200);
  return h;
};
/** 指纹差集里**面积最小**的那个新容器 = 面板本身；再往里挖按钮。 */
const readPanelFromDiff = (d) => (d[0] ? {
  ...d[0],
  deeper: d.slice(0, 3).map((x) => ({ sig: x.sig, area: x.area, text: (x.all || '').slice(0, 200), buttons: x.buttons })),
} : null);

try {
  await open(page, `https://www.liblib.tv/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`, { settle: 4500 });
  await closePromos(page); await clearToasts(page); await page.waitForTimeout(1500);
  await beginBatch(B, { note: '用指纹差集而不是 class 白名单来认面板' });

  const out = {};
  // ① 素材库
  const f0 = await fingerprint(page);
  out.libBtn = await clickAria('素材库');
  const f1 = await fingerprint(page);
  out.libDiff = diffPanels(f0, f1);
  out.libPanel = readPanelFromDiff(out.libDiff);
  await shot(page, 'M-128-素材库面板.png');
  console.log('AS7 素材库面板:', JSON.stringify(out.libPanel).slice(0, 1400));

  // ② 打开工具箱
  out.tbBtn = await clickText('打开工具箱');
  const f2 = await fingerprint(page);
  out.toolboxDiff = diffPanels(f1, f2);
  out.dialog = readPanelFromDiff(out.toolboxDiff);
  await shot(page, 'M-129-工具箱弹窗.png');
  console.log('AS7 工具箱弹窗:', JSON.stringify(out.dialog).slice(0, 2500));

  // ③ 弹窗里「使用」类按钮 —— **只读坐标，不点**
  if (out.dialog) {
    out.useBtns = await page.evaluate(() => {
      const raw = (document.body.innerText || '');
      if (!/工具箱/.test(raw)) return { err: '页面上已经没有「工具箱」字样' };
      // 以**最小的、含「工具箱」且够大的**容器为界
      const cands = [...document.querySelectorAll('div,section')].filter((e) => {
        const r = e.getBoundingClientRect();
        const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
        return r.width > 300 && r.height > 200 && /工具箱/.test(t) && t.length < 1500;
      });
      if (!cands.length) return { err: '没有匹配的容器' };
      let best = cands[0], bd = 1e9;
      for (const e of cands) { let d = 0, n = e; while ((n = n.parentElement)) d += 1; if (d < bd) { bd = d; best = e; } }
      const r = best.getBoundingClientRect();
      const inR = (el) => { const q = el.getBoundingClientRect();
        return q.width > 0 && q.height > 0 && q.x >= r.x - 2 && q.y >= r.y - 2
          && q.x + q.width <= r.x + r.width + 2 && q.y + q.height <= r.y + r.height + 2; };
      return {
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        cls: (best.className || '').toString().slice(0, 80),
        text: (best.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 800),
        buttons: [...best.querySelectorAll('button,[role="button"]')].filter(inR).map((b) => {
          const q = b.getBoundingClientRect();
          return { t: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40),
            aria: b.getAttribute('aria-label'), title: b.getAttribute('title'),
            disabled: b.disabled === true, opacity: getComputedStyle(b).opacity,
            rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)],
            cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2) }; }),
        inputs: [...best.querySelectorAll('input')].filter(inR).map((i) => {
          const q = i.getBoundingClientRect();
          return { type: i.type, aria: i.getAttribute('aria-label'), ph: i.placeholder, v: i.value,
            rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] }; }),
      };
    });
    console.log('AS7 弹窗读数:', JSON.stringify(out.useBtns).slice(0, 2500));
  }

  await logStep(B, {
    id: 'AS7-toolbox-dialog', title: '素材库 → 打开工具箱（用指纹差集认面板，不认 class）',
    target: '面板识别改用 `fingerprint`/`diffPanels`（只看可见+面积+位置，不认 class）；弹窗内按钮**只读坐标不点**',
    evidence: out,
    visible_text: `素材库面板：${JSON.stringify(out.libPanel).slice(0, 600)}。`
      + `\n\n工具箱弹窗：${JSON.stringify(out.dialog).slice(0, 900)}。`
      + `\n\n弹窗读数：${JSON.stringify(out.useBtns).slice(0, 1200)}`,
    shot: 'M-129-工具箱弹窗.png',
  });
  console.log('AS7 完成');
} finally {
  await browser.close();
}
