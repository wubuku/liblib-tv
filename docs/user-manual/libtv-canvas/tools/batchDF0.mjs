// Batch DF-0：两个连着的遗留。
//
// 遗留 1：特效广场为什么**每张卡都是 `✧` 入口**（12/12），那边是否存在「单模型」卡？
//   已知（DC）：风格广场里「能用几个模型」决定左上角显徽标还是 `✧`。
//   ⭐ 推测：特效广场的卡**每张都能用 ≥2 个模型** ⇒ 于是每张都走入口。
//   验证：把特效广场**每张可见卡**都悬停读一遍，**看有没有列 1 个的**。
//   ⚠️ 阴性要配对照：同一套手法在**风格广场**跑，已知那里**有**只列 1 个模型的卡
//     （徽标卡 10 枚全部「无面板」）⇒ 「特效这边一个都没有」若成立，
//     对照组必须能读出「有」。
//
// 遗留 2：风格广场跨分类的「单模型 / 多模型」分布。
//   只在「推荐」一个分类里采过（12 张里 2 张是 ✧）。
//   本步：换 3~4 个分类各采一轮，看比例是否稳定 ⇒ 「`✧` 少见」是普遍现象还是
//   只在推荐分类成立。
//   ⚠️ 每换分类要重新等卡片加载（分类切换是异步的）—— 采样前先等
//     **连续两次 scrollHeight 不变**，否则会采到上一屏的残留。
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

// 等卡片铺完：连续两次 scrollHeight 不变
async function waitStable() {
  let prev = -1;
  for (let i = 0; i < 8; i += 1) {
    const h = await page.evaluate(() => [...document.querySelectorAll('.mantine-ScrollArea-viewport')].map((e) => e.scrollHeight).join(','));
    if (h === prev) return h;
    prev = h; await page.waitForTimeout(1800);
  }
  return prev;
}

// 视口内每张卡的左上格
const topLeftCells = () => page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
  const modals = [...document.querySelectorAll('.mantine-Modal-inner')].filter(vis);
  if (!modals.length) return [];
  const root = modals.sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; })[0];
  const seen = new Set(); const cells = [];
  for (const b of root.querySelectorAll('button')) {
    if (!vis(b)) continue;
    const r = b.getBoundingClientRect();
    if (r.width > 150 || r.height > 150) continue;      // 排除卡片本身
    if (r.width !== 24 || r.height !== 24) continue;     // 只认 24×24 那一格
    // 往上找一个 150~260 宽的容器当卡
    let card = null;
    for (let p = b.parentElement, j = 0; p && j < 8; p = p.parentElement, j += 1) { const q = p.getBoundingClientRect(); if (q.width > 150 && q.width < 260 && q.height > 150) { card = p; break; } }
    if (!card) continue;
    const cr = card.getBoundingClientRect();
    if (Math.abs(r.x - (cr.x + 9)) > 3 || Math.abs(r.y - (cr.y + 9)) > 3) continue;
    if (cr.y < 0 || cr.y > 700) continue;
    const key = `${Math.round(cr.x)},${Math.round(cr.y)}`;
    if (seen.has(key)) continue; seen.add(key);
    cells.push({ 徽标: (b.innerText || '').replace(/\s+/g, ' ').trim() || null, 中心: [Math.round(r.x + 12), Math.round(r.y + 12)] });
  }
  return cells;
});

const readPanel = async (pt) => {
  await page.mouse.move(5, 400); await page.waitForTimeout(350);
  await page.mouse.move(pt[0], pt[1]); await page.waitForTimeout(900);
  return page.evaluate(() => {
    const vis = (e) => { if (!e) return false; const q = e.getBoundingClientRect(); const c = getComputedStyle(e); return q.width > 0 && q.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
    const hit = [...document.querySelectorAll('body *')].filter((e) => e.tagName !== 'SCRIPT' && e.tagName !== 'STYLE' && vis(e) && /全部适配模型/.test(e.textContent || '') && e.children.length === 0)[0];
    if (!hit) return { 有面板: false };
    let panel = hit.parentElement;
    for (let k = 0; k < 5; k += 1) { const b = panel.getBoundingClientRect(); if (b.width > 150 && b.height > 60) break; panel = panel.parentElement; }
    const 条 = [...panel.querySelectorAll('*')].filter((e) => e.children.length === 0 && (e.innerText || '').trim() && (e.innerText || '').trim() !== '全部适配模型')
      .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim());
    return { 有面板: true, 模型数: [...new Set(条)].length, 模型: [...new Set(条)] };
  });
};

// =============== A 特效广场：每张卡的面板模型数 ===============
LOG('══════════ A 特效广场：逐张读模型数 ══════════');
await openTab('特效库');
out.特效scrollH = await waitStable();
LOG(`scrollH=${out.特效scrollH}`);
const 特格 = await topLeftCells();
LOG(`视口内带左上格的卡 ${特格.length} 张（全部应无文字 = 入口）`);
out.特效 = [];
for (const [i, c] of 特格.entries()) {
  const r = await readPanel(c.中心);
  out.特效.push({ 序: i, 徽标: c.徽标, ...r });
  LOG(`  卡${i} ${c.徽标 ? `徽标「${c.徽标}」` : '入口'} → ${r.有面板 ? `${r.模型数} 个: ${JSON.stringify(r.模型)}` : '⛔ 无面板'}`);
}
const 特有面板 = out.特效.filter((x) => x.有面板);
LOG(`\n⭐ 特效广场：有面板 ${特有面板.length}/${out.特效.length}，模型数分布 ${JSON.stringify(特有面板.map((x) => x.模型数))}`);
LOG(`⭐ 有没有列 1 个模型的卡: ${特有面板.some((x) => x.模型数 === 1) ? '有' : '⛔ 一张都没有'}`);

// =============== B 风格广场跨分类采样 ===============
LOG('\n══════════ B 风格广场：跨分类采样 ══════════');
await page.keyboard.press('Escape'); await page.waitForTimeout(1200);
await openTab('风格库');
const 分类 = ['摄影写真', '电商营销', '动漫游戏', '风格插画'];
out.分类 = [];
for (const 名 of 分类) {
  const ok = await page.evaluate((n) => {
    const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === n);
    if (!b) return false; b.click(); return true;
  }, 名);
  if (!ok) { LOG(`  ⛔ 找不到分类「${名}」`); continue; }
  const sh = await waitStable();
  await page.waitForTimeout(1200);
  const cells = await topLeftCells();
  const 有徽标 = cells.filter((c) => c.徽标).length;
  const 入口 = cells.filter((c) => !c.徽标).length;
  LOG(`\n  【${名}】scrollH=${sh} 视口内 ${cells.length} 张：徽标 ${有徽标} / 入口 ${入口}`);
  const 采样 = [];
  for (const c of cells.slice(0, 6)) {
    const r = await readPanel(c.中心);
    采样.push({ 徽标: c.徽标, ...r });
  }
  const 入口样本 = 采样.filter((s) => !s.徽标);
  const 模型数 = 入口样本.filter((s) => s.有面板).map((s) => s.模型数);
  LOG(`     悬停采样 ${采样.length} 张：徽标卡面板数 ${JSON.stringify(采样.filter((s) => s.徽标).map((s) => s.模型数))}，入口卡模型数 ${JSON.stringify(模型数)}`);
  out.分类.push({ 分类: 名, scrollH: sh, 视口卡数: cells.length, 徽标: 有徽标, 入口, 采样 });
}
await shot(page, 'DF-a-风格广场某分类.png', { clip: { x: 0, y: 0, width: 1440, height: 560 } });
LOG('\n📸 DF-a');

// 汇总
const 总徽标 = out.分类.reduce((a, c) => a + c.徽标, 0);
const 总入口 = out.分类.reduce((a, c) => a + c.入口, 0);
LOG(`\n⭐ 跨 ${分类.length} 个分类合计：徽标 ${总徽标} / 入口 ${总入口} ⇒ 入口占 ${总入口 && Math.round((总入口 / (总徽标 + 总入口)) * 100)}%`);

await writeFile(new URL('./batchDF0.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDF0.json ===');
await browser.close();
