// Batch CL：清素材库剩下的三个 📖。
//
//   ① 卡面左上角那枚**模型徽标**（`24×24`，柱状图图标 + 模型名）点下去会怎样
//   ② 详情浮层里那枚 **`使用`** 按钮点下去会怎样
//   ③ 广场**真正的排序**入口在哪（`全部 ▾` 那个已查明是**按模型筛**，不是排序）
//
// ⛔ **本步盯住积分**：每一步前后都读顶栏余额，**一旦掉分立刻停手并如实记录**。
//    ② 之所以敢试：CK 刚坐实「点卡片本体 = 建一个节点」，而 `使用` 就在同一条链路上；
//    但「会不会消耗」本手册从没验过，所以**先读余额再点、点后再读**，不预设结论。
//
// ⭐ 认人纪律沿用：只按**本轮 diff 出来的新 `data-id`** 认节点；
//    点完一律做**时间序列采样**（每 400ms × 8），单点采样不足以定性。
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
await page.waitForTimeout(6000);
await closePromos(page);
await page.waitForTimeout(1500);
for (let i = 0; i < 3; i += 1) {
  const d = page.locator('.mantine-Drawer-inner button[aria-label="关闭"]').first();
  if (await d.count()) await d.click({ timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(700);
}
await page.evaluate(() => document.body.focus());
await page.keyboard.press('Meta+0');
await page.waitForTimeout(2600);

const snap = () => page.evaluate(() => ({
  节点id: [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id')),
  积分: (() => {
    const b = [...document.querySelectorAll('button,[role="button"]')].find((x) => (x.innerText || '').trim() === '20' || (x.innerText || '').trim() === '19' || /^\d{1,4}$/.test((x.innerText || '').trim()));
    const t = (document.body.innerText || '').match(/\n(\d{1,4})\n/);
    return t ? Number(t[1]) : (b ? Number((b.innerText || '').trim()) : null);
  })(),
  广场: (document.body.innerText || '').includes('风格广场'),
  详情: (document.body.innerText || '').includes('风格详情'),
  浮层: [...document.querySelectorAll('[class*="Drawer"],[class*="Modal"],[class*="Popover"],[class*="Tooltip"]')].filter((e) => e.getBoundingClientRect().width > 0).map((e) => (e.className || '').toString().slice(0, 26)).slice(0, 6),
}));
out.基线 = await snap();
console.log('基线 =', JSON.stringify(out.基线));

// 打开素材库 → 风格库
await page.locator('button[aria-label="素材库"]').first().click({ timeout: 8000 }).catch(() => {});
await page.waitForTimeout(2000);
const lb = page.locator('text=风格库').first();
if (await lb.count()) { await lb.click({ timeout: 8000 }).catch(() => {}); await page.waitForTimeout(2200); }

// ── ① 模型徽标 ────────────────────────────────────────────────
console.log('\n════ ① 卡面左上角模型徽标 ════');
out.徽标 = await page.evaluate(() => {
  const rows = [];
  for (const b of document.querySelectorAll('button[aria-label="详情"]')) {
    let card = b;
    for (let i = 0; i < 6 && card.parentElement; i += 1) { card = card.parentElement; const r = card.getBoundingClientRect(); if (r.width > 150 && r.width < 400 && r.height > 150) break; }
    const cr = card.getBoundingClientRect();
    // 卡内 24×24 的按钮（无 aria 的那枚 = 模型徽标或 ••）
    const small = [...card.querySelectorAll('button')].map((x) => { const q = x.getBoundingClientRect(); return { aria: x.getAttribute('aria-label'), 文字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 12), rect: [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)] }; }).filter((x) => x.rect[2] > 0 && x.rect[2] <= 30);
    rows.push({ 卡文字: (card.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40), 卡rect: [Math.round(cr.x), Math.round(cr.y), Math.round(cr.width), Math.round(cr.height)], 小按钮: small });
  }
  return rows.slice(0, 6);
});
for (const c of out.徽标.slice(0, 3)) console.log(`  卡「${c.卡文字}」 小按钮=${JSON.stringify(c.小按钮)}`);

const c0 = out.徽标[0];
const badge = c0 && c0.小按钮.find((b) => !b.aria);
if (badge) {
  const before = await snap();
  await page.mouse.move(badge.rect[0] + 12, badge.rect[1] + 12);
  await page.waitForTimeout(900);
  await page.mouse.click(badge.rect[0] + 12, badge.rect[1] + 12);
  out.徽标采样 = [];
  for (let i = 0; i < 8; i += 1) {
    await page.waitForTimeout(400);
    const s = await snap();
    out.徽标采样.push({ i: i + 1, 节点数: s.节点id.length, 新增: s.节点id.filter((x) => !before.节点id.includes(x)), 积分: s.积分, 广场: s.广场, 详情: s.详情, 浮层: s.浮层 });
  }
  for (const r of out.徽标采样) console.log(`  #${r.i} 节点=${r.节点数} 新增=${JSON.stringify(r.新增)} 积分=${r.积分} 广场=${r.广场} 详情=${r.详情} 浮层=${JSON.stringify(r.浮层)}`);
  out.徽标结论 = { 按钮: badge, 前: before.节点id.length, 后: out.徽标采样.at(-1).节点数, 新增: [...new Set(out.徽标采样.flatMap((r) => r.新增))], 积分前: before.积分, 积分后: out.徽标采样.at(-1).积分 };
  console.log('  结论 =', JSON.stringify(out.徽标结论));
} else console.log('  ⛔ 没找到无 aria 的 24×24 徽标 ⇒ 没测到');

// ── ③ 排序入口：把面板上所有**看起来像下拉**的控件全列出来 ──────
console.log('\n════ ③ 找真正的排序入口 ════');
out.疑似下拉 = await page.evaluate(() => {
  const rows = [];
  for (const b of document.querySelectorAll('button,[role="button"],[role="combobox"]')) {
    const r = b.getBoundingClientRect();
    if (r.width <= 0 || r.height <= 0) continue;
    const t = (b.innerText || '').replace(/\s+/g, ' ').trim();
    const hasArrow = !!b.querySelector('svg path,[class*="Chevron"],[class*="caret"]') || /▾|▼|⌄/.test(t);
    if (hasArrow && t.length <= 20) rows.push({ 文字: t, aria: b.getAttribute('aria-label'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
  }
  return rows;
});
for (const r of out.疑似下拉) console.log(`  ${JSON.stringify(r.文字).padEnd(14)} aria=${r.aria} @${JSON.stringify(r.rect)}`);

// 试着把每个疑似下拉都点开，读新增的文字块
out.下拉内容 = [];
for (const cand of out.疑似下拉.slice(0, 5)) {
  const b0 = await page.evaluate(() => [...document.querySelectorAll('[class*="Menu"],[role="menu"],[class*="Dropdown"],[class*="Popover"]')].filter((e) => e.getBoundingClientRect().width > 0).map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80)));
  await page.mouse.click(cand.rect[0] + cand.rect[2] / 2, cand.rect[1] + cand.rect[3] / 2);
  await page.waitForTimeout(1100);
  const b1 = await page.evaluate(() => [...document.querySelectorAll('[class*="Menu"],[role="menu"],[class*="Dropdown"],[class*="Popover"]')].filter((e) => e.getBoundingClientRect().width > 0).map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80)));
  const 新增 = b1.filter((x) => !b0.includes(x));
  console.log(`  点「${cand.文字}」→ 新增浮层文字 = ${JSON.stringify(新增)}`);
  out.下拉内容.push({ 候选: cand, 新增 });
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(700);
}

await writeFile(resolve(HERE, '.evidence/cl0-asset-badge-sort.json'), JSON.stringify(out, null, 2));
console.log('\n积分 起始 =', out.基线.积分, '（若与结束不同，本步如实记录）');
await browser.close();
