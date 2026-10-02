// Batch CB-2：把抽屉头部（y 84–134 那条 50px 高的条）整棵子树 dump 到文件。
// ⭐ CB-1 的教训：按 innerText 找「资产」再往上冒泡，拿到的第一个祖先是**同时含两个页签**的容器
//   （`flex min-w-0 items-center gap-1`，w=104），点它等于点了整条，点不中任何一个页签。
//   这次直接看结构，不再猜祖先。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
// ⚠️ 顶部那个 const URL = ... 把全局 URL 构造器遮蔽了，new URL() 会炸。改用 path 拼。

const URL = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

const { browser, page } = await launch();
await open(page, URL);
await closePromos(page);

await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  [...document.querySelectorAll('[aria-label="资产管理"]')].filter(vis)
    .map((el) => ({ el, r: el.getBoundingClientRect() }))
    .filter((c) => c.r.x < 100)
    .sort((a, b) => a.r.x - b.r.x)[0]?.el.click();
});
await page.waitForTimeout(1500);

const tree = await page.evaluate(() => {
  const d = document.querySelector('.mantine-Drawer-content');
  if (!d) return { err: 'no drawer' };
  // 找 y 在 80..140 之间、宽接近抽屉全宽的那条
  const strip = [...d.querySelectorAll('div')].find((el) => {
    const r = el.getBoundingClientRect();
    return r.y >= 80 && r.y < 140 && r.width > 280 && r.height <= 60;
  });
  const root = strip || d;
  const walk = (el, depth) => {
    const r = el.getBoundingClientRect();
    const own = [...el.childNodes]
      .filter((n) => n.nodeType === 3)
      .map((n) => n.textContent.trim()).filter(Boolean).join(' ');
    return {
      d: depth,
      tag: el.tagName,
      txt: own.slice(0, 20),
      aria: el.getAttribute('aria-label'),
      role: el.getAttribute('role'),
      data: Object.entries(el.attributes).filter(([k]) => k.startsWith('data-')).map(([k, v]) => `${k}=${v}`).join(','),
      cls: (el.className?.toString?.() || '').slice(0, 70),
      box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      kids: depth < 5 ? [...el.children].map((c) => walk(c, depth + 1)) : [],
    };
  };
  return { stripBox: (() => { const r = root.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })(), tree: walk(root, 0) };
});

await writeFile(resolve(HERE, '.evidence/cb2-tabs.json'), JSON.stringify(tree, null, 2));
console.log('stripBox=', JSON.stringify(tree.stripBox));
await browser.close();
