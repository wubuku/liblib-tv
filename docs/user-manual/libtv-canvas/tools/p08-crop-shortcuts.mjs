// 探针 08 —— 把快捷键面板按四列裁成四张图，供正文分节配图（而不是一张大图糊过去）。
// 裁剪基于面板自身的列容器位置，不是写死像素。
import { launch, open, closePromos, shot, SHOTS } from './lib.mjs';
import { CANVAS_URL } from './test-project.mjs';
import { mkdir } from 'node:fs/promises';

await mkdir(SHOTS, { recursive: true });
const { browser, page } = await launch();

try {
  await open(page, CANVAS_URL, { settle: 3500 });
  await closePromos(page);
  for (const n of ['关闭浏览器通知提示', '知道了', '关闭']) {
    const b = page.getByRole('button', { name: n, exact: true });
    if (await b.count()) await b.first().click({ timeout: 2000 }).catch(() => {});
    await page.waitForTimeout(300);
  }
  await page.getByRole('button', { name: '快捷键', exact: true }).click();
  await page.waitForTimeout(1500);

  const cols = await page.evaluate(() => {
    const hosts = [...document.querySelectorAll('div')].filter((el) => {
      const r = el.getBoundingClientRect();
      return r.width > 500 && r.height > 250 && /成组/.test(el.innerText || '');
    });
    const host = hosts[hosts.length - 1];
    const hr = host.getBoundingClientRect();
    // 四个分区标题（创作/缩放/移动画布/其他）的 x 位置即列起点
    const titles = ['创作', '缩放', '移动画布', '其他'].map((t) => {
      const el = [...host.querySelectorAll('*')].find((e) => !e.children.length && (e.textContent || '').trim() === t);
      const r = el.getBoundingClientRect();
      return { t, x: r.x, y: r.y };
    });
    return {
      panel: { x: hr.x, y: hr.y, w: hr.width, h: hr.height },
      titles,
      vp: { w: window.innerWidth, h: window.innerHeight },
    };
  });

  console.log('panel:', JSON.stringify(cols.panel));
  console.log('titles:', JSON.stringify(cols.titles));

  const bounds = cols.titles;
  for (let i = 0; i < bounds.length; i += 1) {
    const x0 = bounds[i].x - 28;
    const x1 = i + 1 < bounds.length ? bounds[i + 1].x - 24 : cols.panel.x + cols.panel.w - 8;
    await shot(page, `p08-shortcuts-${i + 1}-${['chuangzuo', 'suofang', 'yidong', 'qita'][i]}.png`, {
      clip: { x: Math.max(0, x0), y: Math.max(0, cols.panel.y), width: Math.max(80, x1 - x0), height: Math.min(cols.panel.h, cols.vp.h - cols.panel.y) },
    });
    console.log('cropped:', i + 1, bounds[i].t);
  }
} finally {
  await browser.close();
}
