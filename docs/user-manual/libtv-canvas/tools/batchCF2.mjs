// Batch CF-2：给视频节点上那枚**只此一处**的匿名图标 `M10.26…` 认个名字。
//
// CF-0 的读数：四类节点都有的图标里，`M10.26 1.67c.32 0 .57.25.57.57v.35c0 .32-.25.5`
// **只在视频节点出现**。视频节点比另外三类多出来的那一枚无名按钮，嫌疑人是「提示词优化」。
//
// ⭐ 这一步的设计关键是 **阳性对照**：
//   同一套悬停手法，先去 hover 一枚**名字早就坐实**的按钮（`M15.52` = 翻译提示词）。
//   对照能读出 tooltip ⇒ 这套手法有效，`M10.26` 读不出/读出什么才算数；
//   对照也读不出 ⇒ 说明这套 tooltip 对它们不生效，**不能**据此说 `M10.26` 没有名字。
//
// ⛔ 只读不点。余额只有 20 积分，**不确定它是否收费就不点**。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const VID = 'v-eMpqKtiLlx';
const SUSPECT = 'M10.26 1.67c.32 0 .57.25.57.57v.35c0 .32-.25.5';
const CONTROL = 'M15.52 7.2c.16 0 .31.1.37.26l3.8 10';

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

const findBy = (nid, pre) => page.evaluate(({ n, p }) => {
  const node = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!node) return null;
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  for (const b of [...node.querySelectorAll('button,[role="button"]')].filter(vis)) {
    const svg = b.querySelector('svg');
    const d = svg ? [...svg.querySelectorAll('path')].map((x) => x.getAttribute('d')).join(' ') : '';
    if (d.includes(p)) {
      const r = b.getBoundingClientRect();
      return {
        found: true, aria: b.getAttribute('aria-label'), title: b.getAttribute('title'),
        own: b.getAttribute('data-tooltip') || b.getAttribute('data-position'),
        disabled: b.disabled === true,
        box: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        // 按钮所在那一小片区域的文字：看它旁边有没有标积分
        邻域文字: (b.parentElement ? b.parentElement.innerText : '').trim().slice(0, 120),
      };
    }
  }
  return { found: false };
}, { n: nid, p: pre });

// ⭐ 教训（本轮自己踩的）：`.react-flow__node` **只渲染视口内的节点**。
// 不先 `⌘0` 收全画布 + 点选，就去读节点里的按钮，读数必然是「没找到」——
// 而「没找到」会被误当成「不存在」。这里把「收全 → 选中 → 断言选中」写成硬前置。
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2200);
await page.evaluate((n) => document.querySelector(`.react-flow__node[data-id="${n}"]`)?.click(), VID);
await page.waitForTimeout(2000);
out.sel = await page.evaluate((n) => {
  const el = document.querySelector(`.react-flow__node[data-id="${n}"]`);
  if (!el) return { inDom: false };
  return { inDom: true, selected: el.className.includes('selected'), cls: el.className.slice(0, 80) };
}, VID);
if (!out.sel.inDom || !out.sel.selected) {
  console.log('!! 没选中，后续读数一律作废：' + JSON.stringify(out.sel));
  await browser.close();
  process.exit(1);
}

// 读页面上所有 tooltip 类浮层
const readTips = () => page.evaluate(() => {
  const grab = (sel) => [...document.querySelectorAll(sel)]
    .map((e) => (e.innerText || e.textContent || '').trim())
    .filter((t) => t && t.length < 60);
  return {
    role: grab('[role="tooltip"]'),
    mantine: grab('[class*="Tooltip"]'),
    title: grab('[title]').slice(0, 12),
  };
});

const probe = async (label, pre) => {
  const rec = { label, path: pre.slice(0, 40) };
  rec.before = await findBy(VID, pre);
  if (!rec.before?.found) { rec.note = '节点不在 DOM 或没找到该路径'; return rec; }
  // 先把鼠标挪开，避免继承上一次的 hover
  await page.mouse.move(5, 5);
  await page.waitForTimeout(400);
  rec.tipsBefore = await readTips();
  await page.mouse.move(rec.before.box[0], rec.before.box[1]);
  await page.waitForTimeout(1400);
  // 悬停后再挪 1px，逼出 mouseenter
  await page.mouse.move(rec.before.box[0] + 1, rec.before.box[1]);
  await page.waitForTimeout(1200);
  rec.tipsAfter = await readTips();
  rec.newTips = rec.tipsAfter.role.filter((t) => !rec.tipsBefore.role.includes(t))
    .concat(rec.tipsAfter.mantine.filter((t) => !rec.tipsBefore.mantine.includes(t)));
  return rec;
};

// ① 阳性对照：名字早已坐实的「翻译提示词」
out.control = await probe('对照:翻译提示词(名字已知)', CONTROL);
await page.mouse.move(5, 5);
await page.waitForTimeout(600);
// ② 嫌疑人
out.suspect = await probe('嫌疑人:视频节点独有的那枚', SUSPECT);

// ③ 空提示词时它是不是灰的（前置条件的直接读数，不点它）
await page.mouse.move(5, 5);
await page.waitForTimeout(500);
out.suspectIdle = await findBy(VID, SUSPECT);
out.controlIdle = await findBy(VID, CONTROL);
out.balance = await page.evaluate(() => {
  const vis = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const t = [...document.querySelectorAll('header *,nav *')].filter(vis).map((e) => (e.innerText || '').trim()).filter((x) => /^\d{1,4}$/.test(x));
  return t.length ? Number(t[t.length - 1]) : null;
});

await writeFile(resolve(HERE, '.evidence/cf2-hover-name.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 2).slice(0, 4000));
await browser.close();
