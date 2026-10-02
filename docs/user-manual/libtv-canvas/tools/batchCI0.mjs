// Batch CI-0：顶栏那枚 `aria="退出跟随"` 是什么 —— **只读，一个字都不点**。
//
// CH-4 扫顶栏时读到一枚从没见过的元素：
//     [762,17]  文字="取消ESC"  aria=退出跟随
// 「取消ESC」三个字 + 一个「退出跟随」的无障碍名 ⇒ 页面上有一个**跟随态**，
// 而它的**退出入口就摆在顶栏**。
//
// ⭐ 为什么这件事优先级高：本手册的取证画布从头到尾是**我一个人在上面建了删、删了建**，
//    而画布上**出现了我没建过的节点**（`v-v2hlWY4Br3` / `i-sODTbgLUm1` /
//    `a-THmbuJXQj4` …）。如果那是「跟随」带来的**别人的编辑**，
//    那我此前所有「节点数 11 → 11」的读数都需要重新审视。
//
// ⛔ **只读，绝不点它** —— 「退出跟随」是个**状态切换**：
//    我不知道当前跟随的是谁、也不知道退出之后画布会不会被对方的内容覆盖回去。
//    在搞清楚之前，点它就是拿用户画布冒险。
//
// 本步只回答四件事：它长什么样、悬停说什么、旁边还有没有别的跟随相关元素、
// 以及**画布上那些节点到底是不是「跟着来的」**（用创建线索去查，不靠猜）。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;

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
await page.reload({ waitUntil: 'domcontentloaded' });
await page.waitForTimeout(5000);
await closePromos(page);
await page.waitForTimeout(1200);

const readTips = () => page.evaluate(() => {
  const grab = (sel) => [...document.querySelectorAll(sel)].map((e) => (e.innerText || e.textContent || '').trim()).filter((t) => t && t.length < 60);
  return { role: grab('[role="tooltip"]'), mantine: grab('[class*="Tooltip"]') };
});

// ① 那枚元素的完整信息
out.退出跟随 = await page.evaluate(() => {
  const el = document.querySelector('[aria-label="退出跟随"]');
  if (!el) return { found: false };
  const r = el.getBoundingClientRect();
  const chain = [];
  for (let a = el; a && a !== document.body && chain.length < 4; a = a.parentElement) {
    const rr = a.getBoundingClientRect();
    chain.push({ tag: a.tagName.toLowerCase(), cls: (a.className || '').toString().slice(0, 60), 尺寸: `${Math.round(rr.width)}x${Math.round(rr.height)}`, 位置: [Math.round(rr.x), Math.round(rr.y)] });
  }
  return {
    found: true,
    tag: el.tagName.toLowerCase(),
    cls: (el.className || '').toString().slice(0, 90),
    文字: (el.innerText || '').replace(/\s+/g, ' ').trim(),
    aria: el.getAttribute('aria-label'),
    title: el.getAttribute('title'),
    位置: [Math.round(r.x), Math.round(r.y)], 尺寸: `${Math.round(r.width)}x${Math.round(r.height)}`,
    可见: r.width > 0 && r.height > 0,
    cursor: getComputedStyle(el).cursor,
    祖先链: chain,
  };
});
console.log('退出跟随 =', JSON.stringify(out.退出跟随, null, 2));

// ② 悬停读名字（不点）
if (out.退出跟随?.found) {
  const [x, y] = out.退出跟随.位置;
  await page.mouse.move(5, 400);
  await page.waitForTimeout(400);
  const b0 = await readTips();
  await page.mouse.move(x + 10, y + 10);
  await page.waitForTimeout(1400);
  await page.mouse.move(x + 11, y + 10);
  await page.waitForTimeout(1100);
  const b1 = await readTips();
  out.悬停气泡 = b1.role.filter((t) => !b0.role.includes(t)).concat(b1.mantine.filter((t) => !b0.mantine.includes(t)));
  console.log('悬停气泡 =', JSON.stringify(out.悬停气泡));
  await shot(page, 'M-323-顶栏那枚退出跟随.png', { clip: { x: Math.max(0, x - 170), y: 0, width: 360, height: 150 } });
  await page.mouse.move(5, 400);
  await page.waitForTimeout(500);
}

// ③ 页面上还有没有别的「跟随」痕迹
out.跟随痕迹 = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden'; };
  const byAria = [], byText = [];
  for (const el of document.querySelectorAll('[aria-label],[title]')) {
    if (!vis(el)) continue;
    const v = (el.getAttribute('aria-label') || '') + '|' + (el.getAttribute('title') || '');
    if (/跟随|follow/i.test(v)) byAria.push({ tag: el.tagName.toLowerCase(), aria: el.getAttribute('aria-label'), title: el.getAttribute('title'), 文字: (el.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24) });
  }
  for (const el of document.querySelectorAll('*')) {
    if (!vis(el)) continue;
    const t = (el.innerText || '').trim();
    if (t && t.length <= 12 && /跟随/.test(t)) byText.push({ tag: el.tagName.toLowerCase(), 文字: t, cls: (el.className || '').toString().slice(0, 40) });
  }
  return { 带跟随的aria或title: byAria, 文字里含跟随: byText.slice(0, 10), 页面含跟随二字: (document.body.innerText || '').includes('跟随') };
});
console.log('\n跟随痕迹 =', JSON.stringify(out.跟随痕迹, null, 2));

// ④ ⭐ 画布上那些节点到底是什么来路 —— 查**创建线索**，不靠猜
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2600);
out.节点来路 = await page.evaluate(() => {
  const rows = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const id = n.getAttribute('data-id');
    // 节点上挂的 data-* 属性是 React Flow 内部状态，有时能看出是不是本地新建
    const attrs = {};
    for (const a of n.attributes) if (a.name.startsWith('data-') && a.name !== 'data-id') attrs[a.name] = (a.value || '').slice(0, 40);
    // 命名规律：本批脚本建的节点 id 前缀与类型对应
    const prefix = (id || '').split('-')[0];
    rows.push({ id, 前缀: prefix, cls: (n.className || '').toString().slice(0, 46), 其他data属性: attrs });
  }
  return { 视口内节点数: rows.length, 节点: rows };
});
console.log('\n节点来路（视口内）=');
for (const r of out.节点来路.节点) console.log(`   ${r.id}  前缀=${r.前缀}  ${JSON.stringify(r.其他data属性)}`);

await writeFile(resolve(HERE, '.evidence/ci0-follow-mode.json'), JSON.stringify(out, null, 2));
console.log('\n（本步只读，未点击「退出跟随」）');
await browser.close();
