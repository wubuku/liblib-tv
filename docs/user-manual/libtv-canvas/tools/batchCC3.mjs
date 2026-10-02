// Batch CC-3：卡面上有三个 12–14px 的无文字图标，**没有 aria、没有 title**：
//   ① 左上「•••」  ② 右上「收藏」星（这个有 aria-label="收藏"）
//   ③ 数字前面那枚 —— 它守着「3500 / 1500 / 549」这个数，**单位至今没人知道**
// 这一步把那三个图标的 `d` 路径原样取出来，靠路径形状认图标，而不是靠猜。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
const out = {};

await page.evaluate(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  for (let i = 0; i < 6; i += 1) {
    const hit = [...document.querySelectorAll('button, [role="button"]')].find((b) => (b.innerText || '').trim() === '知道了');
    if (hit) { hit.click(); await sleep(500); }
    if (!(document.body.innerText || '').includes('已升级为 TV Director')) return;
  }
});
await page.waitForTimeout(700);
const enterPlaza = async (name) => {
  await page.evaluate(() => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    [...document.querySelectorAll('[aria-label="素材库"]')].filter(vis)[0]?.click();
  });
  await page.waitForTimeout(1700);
  await page.evaluate((n) => {
    const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
    const hit = [...document.querySelectorAll('*')].filter((e) => vis(e) && (e.innerText || '').trim() === n);
    let el = hit[hit.length - 1];
    let btn = null;
    for (let i = 0; i < 5 && el && !btn; i += 1) {
      if (el.tagName === 'BUTTON' || el.getAttribute('role') === 'button') btn = el;
      el = el.parentElement;
    }
    (btn || hit[hit.length - 1]?.parentElement)?.click();
  }, name);
  await page.waitForTimeout(2800);
};

const dumpCardIcons = () => page.evaluate(() => {
  const m = [...document.querySelectorAll('.mantine-Modal-content')]
    .find((el) => (el.innerText || '').includes('广场'));
  if (!m) return { err: '没有广场' };
  const cards = [...m.querySelectorAll('div')].filter((el) => {
    const c = el.className?.toString?.() || '';
    return /rounded-xl/.test(c) && /flex-col/.test(c) && /p-2/.test(c);
  });
  const one = (card) => [...card.querySelectorAll('svg')].map((s) => {
    const paths = [...s.querySelectorAll('path,circle,rect,line,polyline,polygon')]
      .map((p) => [p.tagName, p.getAttribute('d') || p.getAttribute('cx') || p.getAttribute('x1') || ''].join('|')).join(' ; ');
    const r = s.getBoundingClientRect();
    return { size: [Math.round(r.width), Math.round(r.height)], viewBox: s.getAttribute('viewBox'),
      parentAria: s.closest('button,[role="button"]')?.getAttribute('aria-label') || null,
      parentText: (s.closest('button,[role="button"]')?.innerText || '').trim().slice(0, 12) || null,
      geom: paths.slice(0, 260) };
  });
  return { n: cards.length, first: one(cards[0]), second: one(cards[1] || cards[0]) };
});

await enterPlaza('特效库');
out.special = await dumpCardIcons();

// 顺便把「适配模型」面板里的图标也取出来（那是悬停/点击后才出现的）
out.hoverPanel = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const m = [...document.querySelectorAll('.mantine-Modal-content')].find((el) => (el.innerText || '').includes('特效广场'));
  const cards = [...m.querySelectorAll('div')].filter((el) => {
    const c = el.className?.toString?.() || '';
    return /rounded-xl/.test(c) && /flex-col/.test(c) && /p-2/.test(c);
  });
  const r = cards[0].getBoundingClientRect();
  return { box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
});
await page.mouse.move(out.hoverPanel.box[0] + out.hoverPanel.box[2] / 2, out.hoverPanel.box[1] + 60, { steps: 10 });
await page.waitForTimeout(1200);
out.modelPanel = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const m = [...document.querySelectorAll('.mantine-Modal-content')].find((el) => (el.innerText || '').includes('特效广场'));
  const p = [...m.querySelectorAll('div')].filter((el) => (el.innerText || '').includes('全部适配模型') && vis(el));
  if (!p.length) return { found: false };
  const last = p[p.length - 1];
  return {
    found: true,
    text: (last.innerText || '').replace(/\s+/g, ' ').slice(0, 120),
    box: (() => { const r = last.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })(),
    items: [...last.querySelectorAll('div')].filter((d) => { const r = d.getBoundingClientRect(); return vis(d) && r.height >= 20 && r.height <= 40; })
      .map((d) => ({ t: (d.innerText || '').trim(), svg: d.querySelector('svg') ? [...d.querySelectorAll('path,circle')].map((x) => x.getAttribute('d') || x.getAttribute('cx')).join(';').slice(0, 120) : null })).filter((o) => o.t).slice(0, 8),
  };
});

// 风格广场也取一遍，**两边的数字图标是不是同一枚**？
await page.keyboard.press('Escape');
await page.waitForTimeout(800);
await enterPlaza('风格库');
out.style = await dumpCardIcons();

await writeFile(resolve(HERE, '.evidence/cc3-icons.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 2).slice(0, 4500));
await browser.close();
