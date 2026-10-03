// Batch CV-0：把广场那条链路走完（CU-1 少点了一步）。
//
// CU-1 的面②③ **没测到**：它点开底栏 `素材库` 之后就以为进广场了，
// 但那一步只打开了「添加节点」面板（`风格库 / 特效库 / 打开工具箱` 三项），
// ⭐ **还要再点「风格库」才进风格广场**。asset-library.md 的路径本来是对的：
//   底栏「素材库」→ 面板三项 → 点「风格库」→ 风格广场
//
// 本步按手册记的路径逐级走完，**每一步都记状态**（哪些文字在、哪些层开着），
// 这样能验「手册写的路径到底走不走得通」，而不只是拍到终点。
//
// 终点任务：
//   ① 广场第一屏所有**无文字**控件的逐枚普查（悬停气泡）
//   ② 进风格详情浮层，扫它内部 —— 重点是右上角那枚 `⤡`
//      （asset-library.md 记「读到图标，按钮无文字」）
//
// ⛔ **一个都不点**（除了必要的导航）。`⤡` 只 hover 读身份，不点 ——
//    手册说它是「缩到最小化」，但那是从图标猜的，本轮要的是它的身份读数。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;

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

const out = { steps: [] };
const layerState = (page) => page.evaluate(() => {
  const t = (document.body.innerText || '').replace(/\s+/g, ' ');
  const nodes = [...document.body.children].map((e) => {
    const s = getComputedStyle(e); const r = e.getBoundingClientRect();
    return { z: s.zIndex, pos: s.position, w: Math.round(r.width), h: Math.round(r.height), cls: (e.className || '').toString().slice(0, 40) };
  }).filter((x) => x.w > 200 && x.h > 200);
  return {
    有素材库面板: /风格库[\s\S]{0,40}特效库/.test(t),
    有风格广场: /风格广场/.test(t),
    有详情浮层: /风格详情/.test(t),
    分类数: (t.match(/推荐 摄影写真|摄影写真 电商营销|小说推文/) ? 1 : 0),
    大层: nodes,
  };
});
const step = async (label, page) => {
  const s = await layerState(page);
  out.steps.push({ label, ...s });
  LOG(`▸ ${label}: 素材库面板=${s.有素材库面板} 风格广场=${s.有风格广场} 详情浮层=${s.有详情浮层}`);
  return s;
};
await step('初始', page);

// ---- 第 1 步：底栏「素材库」 ---------------------------------------------------
let c = await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); const r = b.getBoundingClientRect(); return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
await page.mouse.click(c[0], c[1]);
await page.waitForTimeout(1800);
await step('点底栏「素材库」', page);

// ---- 第 2 步：点面板里的「风格库」 ---------------------------------------------
const styleLib = await page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  const hit = [...document.querySelectorAll('button,[role="button"],div')].filter(vis)
    .find((e) => (e.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'));
  if (!hit) return null;
  const r = hit.getBoundingClientRect();
  return { 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], tag: hit.tagName.toLowerCase(), cls: (hit.className || '').toString().slice(0, 50) };
});
LOG(`「风格库」落点: ${JSON.stringify(styleLib)}`);
if (styleLib) { await page.mouse.click(styleLib.中心[0], styleLib.中心[1]); await page.waitForTimeout(2600); }
await step('点「风格库」', page);

// ---- ① 广场第一屏无文字控件普查 -------------------------------------------------
const readTips = (page) => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  return [...new Set([...document.querySelectorAll('[role="tooltip"]')].filter(vis).map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter(Boolean))];
});
const cards = await page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  // 卡 = 视口内、带 aria-label="详情" 的那枚的最近祖先容器
  const dets = [...document.querySelectorAll('button[aria-label="详情"]')].filter(vis);
  return dets.map((d) => {
    let card = d.parentElement;
    for (let i = 0; i < 6 && card; i += 1, card = card.parentElement) {
      const r = card.getBoundingClientRect();
      if (r.width > 120 && r.height > 120) return { 详情钮: (() => { const b = d.getBoundingClientRect(); return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)]; })(), 卡rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    }
    return null;
  }).filter(Boolean);
});
LOG(`\n广场第一屏带「详情」钮的卡片 ${cards.length} 张`);
out.卡片 = cards;

const ctl = await page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0 && r.y > 90 && r.y < 800; };
  return [...document.querySelectorAll('button,[role="button"]')].filter(vis)
    .filter((b) => { const r = b.getBoundingClientRect(); return r.x > 700; })   // 广场在画布右侧
    .map((b) => {
      const r = b.getBoundingClientRect();
      return {
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        text: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18),
        aria: b.getAttribute('aria-label'),
        data: Object.fromEntries([...b.attributes].filter((a) => a.name.startsWith('data-')).map((a) => [a.name, a.value])),
        svgPaths: [...b.querySelectorAll('svg path')].map((p) => (p.getAttribute('d') || '').slice(0, 44)),
        cls: (b.className || '').toString().slice(0, 50),
      };
    }).sort((a, z) => (a.rect[1] - z.rect[1]) || (a.rect[0] - z.rect[0]));
});
LOG(`\n===== 广场第一屏（x>700）可交互元素 ${ctl.length} 枚 =====`);
out.广场控件 = ctl;
const rows = [];
for (const it of ctl) {
  if (it.text && it.text.length > 2 && !/^\d/.test(it.text)) { rows.push({ ...it, 气泡: [], 跳过: '有文字' }); continue; }
  await page.mouse.move(300, 400); await page.waitForTimeout(210);
  const base = await readTips(page);
  await page.mouse.move(it.rect[0] + it.rect[2] / 2, it.rect[1] + it.rect[3] / 2);
  await page.waitForTimeout(760);
  const novel = (await readTips(page)).filter((t) => !base.includes(t));
  rows.push({ ...it, 气泡: novel });
  LOG(`  @${JSON.stringify(it.rect).padEnd(20)} text=${JSON.stringify(it.text)} aria=${JSON.stringify(it.aria)} 气泡=${novel.length ? `「${novel.join('/')}」` : '⛔无'} svg=${JSON.stringify(it.svgPaths).slice(0, 70)}`);
}
out.广场扫描 = rows;

// ---- ② 进详情浮层 ---------------------------------------------------------------
const det = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button[aria-label="详情"]')].find((x) => { const r = x.getBoundingClientRect(); return r.width > 0; });
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
});
LOG(`\n第一张卡的「详情」落点: ${JSON.stringify(det)}`);
if (det) { await page.mouse.click(det[0], det[1]); await page.waitForTimeout(2200); }
await step('点卡上「详情」', page);

const detCtl = await page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && +s.opacity > 0; };
  const inDetail = (e) => { for (let p = e; p; p = p.parentElement) if (p.classList?.contains('mantine-Modal-content')) return true; return false; };
  return [...document.querySelectorAll('button,[role="button"]')].filter(vis).filter(inDetail)
    .map((b) => {
      const r = b.getBoundingClientRect();
      return {
        rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        text: (b.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20),
        aria: b.getAttribute('aria-label'), title: b.getAttribute('title'),
        data: Object.fromEntries([...b.attributes].filter((a) => a.name.startsWith('data-')).map((a) => [a.name, a.value])),
        svgPaths: [...b.querySelectorAll('svg path')].map((p) => (p.getAttribute('d') || '').slice(0, 52)),
        cls: (b.className || '').toString().slice(0, 60),
      };
    }).sort((a, z) => a.rect[0] - z.rect[0]);
});
LOG(`\n===== 详情浮层内可交互元素 ${detCtl.length} 枚 =====`);
out.详情控件 = detCtl;
for (const it of detCtl) {
  await page.mouse.move(300, 400); await page.waitForTimeout(200);
  const base = await readTips(page);
  await page.mouse.move(it.rect[0] + it.rect[2] / 2, it.rect[1] + it.rect[3] / 2);
  await page.waitForTimeout(760);
  const novel = (await readTips(page)).filter((t) => !base.includes(t));
  it.气泡 = novel;
  LOG(`  @${JSON.stringify(it.rect).padEnd(20)} text=${JSON.stringify(it.text)} aria=${JSON.stringify(it.aria)} title=${JSON.stringify(it.title)} 气泡=${novel.length ? `「${novel.join('/')}」` : '⛔无'}`);
  LOG(`      svg=${JSON.stringify(it.svgPaths)}`);
  LOG(`      data=${JSON.stringify(it.data)} class=${it.cls}`);
}
out.详情扫描 = detCtl;

await writeFile(new URL('./batchCV0.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n已写 tools/batchCV0.json');
await browser.close();
