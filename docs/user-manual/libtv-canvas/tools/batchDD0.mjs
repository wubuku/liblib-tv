// Batch DD-0：特效广场那 12 枚「•••」和风格广场那 5 枚「✧」是不是同一枚？
//
// 旧账里两处都提到同一段 path 的**开头**：
//   特效广场 `•••`：path 以 `M2 0a2 2 0 1 1 0 4 2 2 0 0 1 0-4` 开头
//   风格广场 `✧`  ：path 以 `M2 0a2 2 0 1 1 0 4 2 2 0 0 1 0` 开头
// ⚠️⚠️ 但**两边都只读了前 30 个字符** —— 前缀相同**不能**推出是同一个图标，
//   更不能推出**行为相同**。本轮要比的是：
//   ① **完整 `d` 属性**逐字比（不截断、不取前 N 字）；
//   ② **行为**：在特效广场悬停它，会不会也出「全部适配模型」面板？
//      —— DC 已经坐实风格广场那侧「悬停出面板、点它什么也不发生」。
//   ⭐ 这一问才是关键：**同一个图标在两个地方做同一件事**才叫同一枚，
//     长得一样但行为不同是**最坑**的一种撞车（CT 的 `⤡` / `⤢` 就是这样）。
//
// ⚠️ 方法纪律（DB/DC 血买来的）：
//   · 数东西用 **DOM 总数**，不用可见性过滤；
//   · 找东西用**几何**（精确坐标）或完整属性，**不信文字**；
//   · 搜文字**排除 SCRIPT/STYLE**（Next.js 数据流会命中）。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = {};

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

async function openTab(名字) {
  await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
  await page.waitForTimeout(2000);
  await page.evaluate((n) => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith(n))?.click(), 名字);
  await page.waitForTimeout(3500);
}

// ⭐ 抽出「卡面左上角那一格」的完整读数
const probe = () => page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
  const res = { 卡数: 0, 有左上格的卡: [], 详情按钮: [...document.querySelectorAll('button[aria-label="详情"]')].length };
  // 特效广场没有「详情」按钮 ⇒ 改用「有较大面积的卡片容器」当卡
  const cards = [...document.querySelectorAll('body *')].filter((e) => {
    const r = e.getBoundingClientRect();
    return vis(e) && r.width > 150 && r.width < 260 && r.height > 180 && r.height < 320;
  });
  // 去重（父子都可能命中，按 rect 唯一）
  const seen = new Set(); const uniq = [];
  for (const c of cards) { const r = c.getBoundingClientRect(); const k = `${Math.round(r.x)},${Math.round(r.y)}`; if (seen.has(k)) continue; seen.add(k); uniq.push(c); }
  for (const card of uniq) {
    const cr = card.getBoundingClientRect();
    if (cr.y < 0 || cr.y > 700) continue;
    res.卡数 += 1;
    const gx = cr.x + 9; const gy = cr.y + 9;
    for (const b of card.querySelectorAll('button')) {
      const r = b.getBoundingClientRect();
      if (Math.abs(r.x - gx) <= 3 && Math.abs(r.y - gy) <= 3) {
        const pth = b.querySelector('path');
        res.有左上格的卡.push({
          文字: (b.innerText || '').replace(/\s+/g, ' ').trim() || null,
          rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
          aria: b.getAttribute('aria-label'), title: b.getAttribute('title'),
          完整path: pth ? (pth.getAttribute('d') || '') : null,
          path长度: pth ? (pth.getAttribute('d') || '').length : 0,
          svg数: b.querySelectorAll('svg').length,
          class: (b.className || '').toString().slice(0, 70),
        });
        break;
      }
    }
  }
  return res;
});

const readPanel = async (pt) => {
  await page.mouse.move(5, 400); await page.waitForTimeout(600);
  await page.mouse.move(pt[0], pt[1]); await page.waitForTimeout(1400);
  return page.evaluate(() => {
    const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
    const hit = [...document.querySelectorAll('body *')].filter((e) => e.tagName !== 'SCRIPT' && e.tagName !== 'STYLE' && vis(e) && /全部适配模型/.test(e.textContent || '') && e.children.length === 0)[0];
    if (!hit) return { 有面板: false };
    let panel = hit.parentElement;
    for (let i = 0; i < 5; i += 1) { const b = panel.getBoundingClientRect(); if (b.width > 150 && b.height > 60) break; panel = panel.parentElement; }
    const 条目 = [...panel.querySelectorAll('*')].filter((e) => e.children.length === 0 && (e.innerText || '').trim() && (e.innerText || '').trim() !== '全部适配模型')
      .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim());
    const r = panel.getBoundingClientRect();
    return { 有面板: true, 面板rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 模型数: 条目.length, 模型: [...new Set(条目)] };
  });
};

// =============== A 风格广场的 ✧ ===============
LOG('══════════ A 风格广场的 ✧ ══════════');
await openTab('风格库');
out.风格 = await probe();
LOG(`可见卡数=${out.风格.卡数} 详情按钮(DOM)=${out.风格.详情按钮} 有左上格的卡=${out.风格.有左上格的卡.length}`);
const 风格X = out.风格.有左上格的卡.filter((c) => !c.文字);
LOG(`其中无文字（✧）的: ${风格X.length} 枚`);
if (风格X.length) {
  LOG(`⭐ 完整 path（${风格X[0].path长度} 字符，未截断）:`);
  LOG(`   ${风格X[0]['完整path']}`);
  const pt = [风格X[0].rect[0] + 12, 风格X[0].rect[1] + 12];
  out.风格面板 = await readPanel(pt);
  LOG(`   悬停后面板: ${out.风格面板.有面板 ? `${out.风格面板.模型数} 个模型 ${JSON.stringify(out.风格面板.模型)}` : '⛔ 没有'}`);
  await shot(page, 'DD-a-风格广场悬停✧之后.png', { clip: { x: Math.max(0, 风格X[0].rect[0] - 200), y: Math.max(0, 风格X[0].rect[1] - 60), width: 460, height: 320 } });
  LOG('   📸 DD-a');
}

// =============== B 特效广场的 ••• ===============
LOG('\n══════════ B 特效广场的 ••• ══════════');
await page.keyboard.press('Escape');
await page.waitForTimeout(1200);
await openTab('特效库');
out.特效 = await probe();
LOG(`可见卡数=${out.特效.卡数} 详情按钮(DOM)=${out.特效.详情按钮} 有左上格的卡=${out.特效.有左上格的卡.length}`);
const 特效X = out.特效.有左上格的卡.filter((c) => !c.文字);
LOG(`其中无文字（•••）的: ${特效X.length} 枚`);
if (特效X.length) {
  LOG(`⭐ 完整 path（${特效X[0].path长度} 字符，未截断）:`);
  LOG(`   ${特效X[0]['完整path']}`);
  const pt = [特效X[0].rect[0] + 12, 特效X[0].rect[1] + 12];
  out.特效面板 = await readPanel(pt);
  LOG(`   悬停后面板: ${out.特效面板.有面板 ? `${out.特效面板.模型数} 个模型 ${JSON.stringify(out.特效面板.模型)}` : '⛔ 没有面板'}`);
  await shot(page, 'DD-b-特效广场悬停三点之后.png', { clip: { x: Math.max(0, 特效X[0].rect[0] - 200), y: Math.max(0, 特效X[0].rect[1] - 60), width: 460, height: 320 } });
  LOG('   📸 DD-b');
}

// =============== C 逐字比对 ===============
LOG('\n══════════ C 逐字比对 ══════════');
if (风格X.length && 特效X.length) {
  const a = 风格X[0]['完整path']; const b = 特效X[0]['完整path'];
  out.比对 = { 风格长度: a.length, 特效长度: b.length, 逐字相同: a === b };
  LOG(`风格 path 长 ${a.length}，特效 path 长 ${b.length}，⭐ 逐字相同 = ${a === b}`);
  if (a !== b) {
    let i = 0; while (i < Math.min(a.length, b.length) && a[i] === b[i]) i += 1;
    LOG(`   第一个不同的位置: 第 ${i} 字符`);
    LOG(`   风格: …${a.slice(Math.max(0, i - 20), i + 20)}…`);
    LOG(`   特效: …${b.slice(Math.max(0, i - 20), i + 20)}…`);
  }
  out.比对.行为相同 = (out.风格面板?.有面板 ?? false) === (out.特效面板?.有面板 ?? false);
  LOG(`⭐ 行为是否相同（都出/都不出面板）= ${out.比对.行为相同}`);
}

await writeFile(new URL('./batchDD0.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDD0.json ===');
await browser.close();
