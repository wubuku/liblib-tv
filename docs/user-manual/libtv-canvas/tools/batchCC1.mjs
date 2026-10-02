// Batch CC-1：CC-0 点「特效库」用的是「文字恰好等于它、且没有子元素」的那个节点 ——
// 点在文字叶子上，事件冒泡到祖先才生效，直接 click 叶节点**不冒泡到同级的处理器**。
// ⭐ 这与 CB 的教训同族：**判据没错，选错了对象**。
// 这一步 dump 面板里「风格库 / 特效库 / 工具箱」那块的真实结构，按结构点。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
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
await page.waitForTimeout(800);

await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  [...document.querySelectorAll('[aria-label="素材库"]')].filter(vis)[0]?.click();
});
await page.waitForTimeout(1800);

// dump 含「特效库」的那块
out.struct = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const hit = [...document.querySelectorAll('*')].filter((e) => vis(e) && (e.innerText || '').trim() === '特效库');
  if (!hit.length) return { err: '面板里没有特效库' };
  let el = hit[hit.length - 1];
  const chain = [];
  for (let i = 0; i < 5 && el; i += 1) {
    const r = el.getBoundingClientRect();
    chain.push({
      tag: el.tagName, role: el.getAttribute('role'), aria: el.getAttribute('aria-label'),
      cls: (el.className?.toString?.() || '').slice(0, 70),
      box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      kids: el.children.length,
    });
    el = el.parentElement;
  }
  return { n: hit.length, chain };
});

// 按最外层带 handler 的容器点：向上找到第一个 button/[role=button]，否则点那个大容器
out.clicked = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const hit = [...document.querySelectorAll('*')].filter((e) => vis(e) && (e.innerText || '').trim() === '特效库');
  if (!hit.length) return { ok: false };
  let el = hit[hit.length - 1];
  let btn = null;
  for (let i = 0; i < 5 && el && !btn; i += 1) {
    if (el.tagName === 'BUTTON' || el.getAttribute('role') === 'button' || el.getAttribute('tabindex') != null) btn = el;
    el = el.parentElement;
  }
  const target = btn || hit[hit.length - 1].parentElement;
  if (!target) return { ok: false, why: '找不到可点祖先' };
  const r = target.getBoundingClientRect();
  target.click();
  return { ok: true, tag: target.tagName, box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
});
await page.waitForTimeout(3000);
out.page = await page.evaluate(() => (document.body.innerText || '').replace(/\s+/g, ' ').slice(0, 500));
await shot(page, 'M-296-特效广场-全景.png', { clip: { x: 0, y: 0, width: 1440, height: 810 } });

// dump 卡片：这一回按「浮层容器里重复出现的同尺寸块」来找
out.floats = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  return [...document.querySelectorAll('.mantine-Modal-content, [role="dialog"], .mantine-Drawer-content, .mantine-Popover-dropdown')]
    .filter(vis)
    .map((el) => {
      const r = el.getBoundingClientRect();
      return { cls: (el.className?.toString?.() || '').slice(0, 60),
        box: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        text: (el.innerText || '').replace(/\s+/g, ' ').slice(0, 200) };
    });
});

await writeFile(resolve(HERE, '.evidence/cc1-plaza.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify({ struct: out.struct, clicked: out.clicked, page: out.page, floats: out.floats }, null, 2));
await browser.close();
