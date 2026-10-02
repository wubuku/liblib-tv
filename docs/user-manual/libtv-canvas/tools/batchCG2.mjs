// Batch CG-2：节点浮层右上角**叠在一起的那两枚** 28×28 按钮。
//
// CG-1 查到了两件要紧的事：
//   ① `M1.4 8.9c…` 的 class 是 `absolute right-2 top-2 z-10 flex size-7`
//      —— 它**绝对定位在 660 宽的浮层卡片右上角**，不在参数条上。
//      ⛔ CF-0 的身份证表用它自己的 `node.querySelectorAll('button')` 扫**整个节点**，
//         却把结果当「参数条」列出来 —— **判据错误，本步坐实并更正**。
//   ② ⭐⭐ 它的**兄弟里还有一枚一模一样的 28×28**（`absolute right-2 top-2 z-1`）——
//      **两枚完全重叠**，z-10 那枚盖在上面。
//      ⇒ 这就解释了 CG-0 的「悬停读不出气泡」：**鼠标只能命中上面那枚**，
//         底下那枚**收不到 mouseenter**，tooltip 自然永远不弹。
//
// 本步只读 + 只拍：
//   ① 两枚各自的路径 / z / class；
//   ② **真鼠标移到那个点上，`elementFromPoint` 到底命中哪一枚**（不点，只读命中对象）；
//   ③ 重拍特写 —— 上一版 clip 用 `node-shell` 的 x 算，而这枚按钮在 660 宽的浮层里，
//      屏幕 x 根本不在 clip 范围内，拍了个空。**这次按按钮自己的 rect 算。**
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const MYSTERY = 'M1.4 8.9c.22 0 .4.18.4.4v5.54l5.26-5.26a.4.4 0';
const VID = 'v-eMpqKtiLlx';

const { browser, page } = await launch();
const out = {};

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
await page.waitForTimeout(800);

await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2200);
await page.evaluate((n) => document.querySelector(`.react-flow__node[data-id="${n}"]`)?.click(), VID);
await page.waitForTimeout(2000);
out.sel = await page.evaluate((n) => {
  const el = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  return { inDom: !!el, selected: !!el && el.className.includes('selected') };
}, VID);
if (!out.sel.inDom || !out.sel.selected) { console.log('!! 没选中，读数作废'); await browser.close(); process.exit(1); }

// ① 浮层卡片右上角 absolute right-2 top-2 的所有按钮
out.右上角那几枚 = await page.evaluate(({ n, pre }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  const hit = [];
  for (const b of node.querySelectorAll('button,[role="button"]')) {
    const cls = (b.className || '').toString();
    if (!/absolute/.test(cls) || !/right-2/.test(cls)) continue;
    const r = b.getBoundingClientRect();
    if (!(r.width > 0 && r.height > 0)) continue;
    const svg = b.querySelector('svg');
    const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '(无 svg)';
    hit.push({
      cls: cls.slice(0, 90), 尺寸: `${Math.round(r.width)}x${Math.round(r.height)}`,
      x: Math.round(r.x), y: Math.round(r.y),
      文字: (b.innerText || '').trim().slice(0, 12), aria: b.getAttribute('aria-label'),
      disabled: b.disabled === true,
      zIndex: getComputedStyle(b).zIndex, position: getComputedStyle(b).position,
      是不是那枚M1_4: d.includes(pre),
      路径全: d,
    });
  }
  return hit;
}, { n: VID, pre: MYSTERY });

// ② 真鼠标移到那个坐标上，看命中的是哪一枚（只读，不点）
const top = out.右上角那几枚.filter((h) => h.zIndex === '10')[0] || out.右上角那几枚[0];
if (top) {
  await page.mouse.move(5, 5);
  await page.waitForTimeout(400);
  await page.mouse.move(top.x + 14, top.y + 14);
  await page.waitForTimeout(900);
  out.鼠标命中 = await page.evaluate(({ x, y, pre }) => {
    const el = document.elementFromPoint(x, y);
    const btn = el ? el.closest('button,[role="button"]') : null;
    if (!btn) return { 命中: el ? el.tagName.toLowerCase() + '.' + (el.className || '').toString().slice(0, 50) : 'null' };
    const svg = btn.querySelector('svg');
    const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    return {
      命中按钮的cls: (btn.className || '').toString().slice(0, 90),
      是不是那枚M1_4: d.includes(pre),
      路径全: d,
      悬停时cursor: getComputedStyle(btn).cursor,
    };
  }, { x: top.x + 14, y: top.y + 14, pre: MYSTERY });
}

// ③ 重拍特写：**按按钮自己的 rect** 算 clip（上一版按 node-shell 算，拍空了）
await page.mouse.move(5, 5);
await page.waitForTimeout(600);
const clip = await page.evaluate(({ n, pre }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  for (const b of node.querySelectorAll('button,[role="button"]')) {
    const svg = b.querySelector('svg');
    const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    if (d.includes(pre)) {
      const r = b.getBoundingClientRect();
      const x = Math.max(0, Math.round(r.x - 150));
      const y = Math.max(0, Math.round(r.y - 46));
      return { x, y, width: Math.min(1440 - x, 300), height: Math.min(810 - y, 130) };
    }
  }
  return null;
}, { n: VID, pre: MYSTERY });
if (clip) {
  out.特写clip = clip;
  await shot(page, 'M-308-节点浮层右上角两枚按钮.png', { clip });
}

await writeFile(resolve(HERE, '.evidence/cg2-corner-buttons.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 2).slice(0, 5000));
await browser.close();
