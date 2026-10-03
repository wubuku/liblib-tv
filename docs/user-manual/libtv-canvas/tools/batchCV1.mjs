// Batch CV-1：定 `aria-label="minimize"` 到底属于哪个浮层。
//
// CV-0 的读数（**部分有效、部分作废**，如实分开）：
//
// ✅ 有效的硬读数：
//   某个浮层的标题栏上并排两枚 40×40 按钮 ——
//     `[1227,92,40,40]` `aria-label="minimize"`  svg `M9.76 10.59c.28 0 .5.22.5.5v8a.4.4…`
//     `[1283,92,40,40]` `aria-label="close"`      svg `M15.8.12a.4.4 0 0 1 .56 0l.7.7a.4.4…`
//   ⭐⭐ **`minimize` 那枚的 svg path 和节点大编辑器右上角「收拢箭头」逐字相同** ⇒
//     同一个图标在两处复用，而 CM 批次只说「大编辑器右上角有个收拢箭头」。
//   ⭐⭐ **全站 `aria-label` 都是中文**（「教程」「素材库」「画布小地图」…），
//     **只有这一处是英文** ⇒ 「哪个浮层」可以靠 aria 的语言认出来。
//
// ⛔ 作废的读数（原因写在这里，免得下批又踩）：
//   - `layerState` 用 `body.innerText` 判「广场开没开」，明明开了却报 false
//     ⇒ **「层开没开」不能靠 innerText 判**，这一条作废
//   - 「风格库」的落点 `[565,563,222,164]` 高度 164，可疑；点完进去的浮层里
//     第一个 tab 文字是「**特效广场**」⇒ **我可能点进了特效广场**。
//     但没有图，不敢定性 ⇒ 广场本体这一面标「没测到」。
//
// 本步：**每一步都拍图**，用图判归属。只读，不点任何功能按钮
//   （`素材库` / `风格库` / `详情` 属于导航，必须点）。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const shots = [];

const { browser, page } = await launch();
await open(page, URL_);
await closePromos(page);
await page.waitForTimeout(1500);
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2800);
for (let i = 0; i < 3; i += 1) {
  const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
  if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(600);
}
const pk = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '下次再说');
  if (!b) return null; const r = b.getBoundingClientRect();
  return r.width > 0 ? [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] : null;
});
if (pk) { await page.mouse.click(pk[0], pk[1]); await page.waitForTimeout(1200); }

// ⭐ 读「当前最上层浮层」的两枚标题栏按钮 + 该浮层的身份文字
const topLayer = (page) => page.evaluate(() => {
  // 逐层按 zIndex 找最高的、可见的、有面积的浮层容器
  const cands = [];
  const walk = (e, depth) => {
    const s = getComputedStyle(e);
    const r = e.getBoundingClientRect();
    const z = parseInt(s.zIndex, 10);
    if (!Number.isNaN(z) && z >= 200 && r.width > 200 && r.height > 200) {
      cands.push({ z, depth, el: e, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], cls: (e.className || '').toString().slice(0, 46) });
    }
    for (const c of e.children) walk(c, depth + 1);
  };
  walk(document.body, 0);
  if (!cands.length) return null;
  cands.sort((a, b2) => b2.z - a.z);
  const top = cands[0];
  const btns = [...top.el.querySelectorAll('button,[role="button"]')].map((b) => {
    const r = b.getBoundingClientRect();
    if (!r.width || r.y > top.rect[1] + 80) return null;      // 只要标题栏那一行
    return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], aria: b.getAttribute('aria-label'), text: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 16), svg: [...b.querySelectorAll('svg path')].map((p) => (p.getAttribute('d') || '').slice(0, 40)) };
  }).filter(Boolean).sort((a, b2) => a.rect[0] - b2.rect[0]);
  return {
    z: top.z, rect: top.rect, cls: top.cls,
    标题栏按钮: btns,
    全文前120: (top.el.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120),
  };
});

const out = { steps: [] };
const mark = async (label, file) => {
  const s = await topLayer(page);
  out.steps.push({ label, ...s });
  LOG(`\n▸ ${label}`);
  LOG(`   最上层浮层 z=${s?.z} rect=${JSON.stringify(s?.rect)} cls=${s?.cls}`);
  LOG(`   标题栏按钮: ${JSON.stringify(s?.标题栏按钮)}`);
  LOG(`   全文前120: ${JSON.stringify(s?.全文前120)}`);
  if (file) { await shot(page, file, {}); shots.push(file); LOG(`   📸 ${file}（全屏）`); }
  return s;
};

await mark('0 初始画布', 'CV-a-初始画布.png');

// ---- 1 点底栏「素材库」 ---------------------------------------------------------
let c = await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); const r = b.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
await page.mouse.click(c[0], c[1]);
await page.waitForTimeout(1800);
await mark('1 点底栏「素材库」', 'CV-b-素材库面板.png');

// ---- 2 点「风格库」（这次先确认命中的是哪一项）---------------------------------
const items = await page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  return [...document.querySelectorAll('div,button,[role="button"]')].filter(vis)
    .filter((e) => e.children.length <= 3 && /^(风格库|特效库|打开工具箱)/.test((e.innerText || '').replace(/\s+/g, ' ').trim()))
    .map((e) => { const r = e.getBoundingClientRect(); return { text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], tag: e.tagName.toLowerCase(), cls: (e.className || '').toString().slice(0, 44) }; })
    .sort((a, b) => (a.rect[1] - b.rect[1]) || (a.rect[0] - b.rect[0]));
});
LOG(`\n素材库面板里那三项的完整身份:\n${JSON.stringify(items, null, 1)}`);
const styleItem = items.find((i) => i.text.startsWith('风格库'));
if (styleItem) {
  await page.mouse.click(styleItem.rect[0] + styleItem.rect[2] / 2, styleItem.rect[1] + Math.min(20, styleItem.rect[3] / 2));
  await page.waitForTimeout(2600);
  await mark(`2 点「风格库」@${JSON.stringify(styleItem.rect)}`, 'CV-c-点风格库之后.png');
} else {
  LOG('⛔ 没找到「风格库」那一项');
}

// ---- 3 找卡上的「详情」并点开 ---------------------------------------------------
const dets = await page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  const byAria = [...document.querySelectorAll('button[aria-label="详情"]')].filter(vis);
  return { 按aria: byAria.length, 位置: byAria.slice(0, 3).map((b) => { const r = b.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y)]; }) };
});
LOG(`\nbutton[aria-label="详情"] 可见 ${dets.按aria} 个 ${JSON.stringify(dets.位置)}`);
let d = dets.按aria ? await page.evaluate(() => { const b = [...document.querySelectorAll('button[aria-label="详情"]')].find((x) => { const r = x.getBoundingClientRect(); return r.width > 0; }); const r = b.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; }) : null;
if (!d) {
  // 退回：扫卡上所有 24×24 按钮，报身份
  const alt = await page.evaluate(() => {
    const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
    return [...document.querySelectorAll('button,[role="button"]')].filter(vis)
      .map((b) => { const r = b.getBoundingClientRect(); return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], aria: b.getAttribute('aria-label'), svg: [...b.querySelectorAll('svg path')].map((p) => (p.getAttribute('d') || '').slice(0, 36)), text: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12) }; })
      .filter((b) => b.rect[2] <= 30 && b.rect[3] <= 30 && b.rect[0] > 100)
      .slice(0, 14);
  });
  LOG(`24×24 附近的按钮:\n${JSON.stringify(alt, null, 1)}`);
}
if (d) { await page.mouse.click(d[0], d[1]); await page.waitForTimeout(2400); await mark('3 点卡上「详情」', 'CV-d-详情浮层.png'); }

await writeFile(new URL('./batchCV1.json', import.meta.url), JSON.stringify(out, null, 2));
LOG(`\n已写 tools/batchCV1.json；截图 ${shots.length} 张：${shots.join(', ')}`);
await browser.close();
