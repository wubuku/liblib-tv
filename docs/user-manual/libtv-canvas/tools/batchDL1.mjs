// Batch DL-1：核实 `total = 40` 到底是不是分类总量。
//
// DL-0 的读数：九个分类的 `feed/stream` 响应**全部**是
//   page=1, total=40, pageSize=40, hasMore=true, data 长度 40
// ⛔ 三条红旗：
//   ① `total` 九个分类**完全一样**（40）—— 分类内容量不可能都相等；
//   ② `40` 恰好等于 `pageSize` ⇒ 更像**单页上限**；
//   ③ 接口路径是 `/api/www/model/feed/stream`（「模型 feed」），
//      而风格广场是**风格**库 ⇒ ⭐ **可能盯错了接口** ——
//      这是主 feed，广场可能另有一个接口，或者广场就是复用它。
//
// 本步：⭐ **先把「这一屏 12 张卡」在响应里对上号** ——
//   若它们全在 `data.data`（40 条）里，说明广场用的就是这个接口；
//   顺便记下**它们在这 40 条里的下标**。
// 然后：⭐ 切分类时**请求 URL 变没变**（DL-0 里 URL 打印被截到 200 字符且没带 query），
//   把**完整 query** 打出来 —— 分类参数就在那儿。没有 query 变化 ⇒ 分类是**前端过滤**。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 请求: [], 对上号: null };

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

// ⭐ 抓**所有**请求的 URL（含 query），不只 feed/stream
const 全部请求 = [];
page.on('request', (r) => {
  const u = r.url();
  if (!/api2?\.liblib\.(art|tv)/.test(u)) return;
  全部请求.push({ 方法: r.method(), url: u, 时间: Date.now(), postData: (r.postData() || '').slice(0, 200) });
});

await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(5000);

const 快照1 = 全部请求.length;
// 读一屏卡的 runCount（界面上显示的数字）
out.界面数字 = await page.evaluate(() => {
  const vis = (e) => { if (!e) return false; const r = e.getBoundingClientRect(); const c = getComputedStyle(e); return r.width > 0 && r.height > 0 && c.visibility !== 'hidden' && +c.opacity > 0; };
  const modals = [...document.querySelectorAll('.mantine-Modal-inner')].filter(vis);
  if (!modals.length) return [];
  const root = modals.sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; })[0];
  const o = []; const seen = new Set();
  for (const D of root.querySelectorAll('button[aria-label="详情"]')) {
    let L3 = null;
    for (let p = D.parentElement, j = 0; p && j < 6; p = p.parentElement, j += 1) { const r = p.getBoundingClientRect(); if (r.width > 150 && r.width < 260 && r.height > 260) { L3 = p; break; } }
    if (!L3) continue;
    const cr = L3.getBoundingClientRect();
    if (cr.y < 0 || cr.y > 620) continue;
    const k = `${Math.round(cr.x)},${Math.round(cr.y)}`;
    if (seen.has(k)) continue; seen.add(k);
    const 数字 = [...L3.querySelectorAll('*')].filter((e) => e.children.length === 0 && vis(e) && /^\d+(\.\d+)?w?$/.test((e.innerText || '').trim())).map((e) => (e.innerText || '').trim());
    o.push({ 数字: 数字[0] || null });
  }
  return o;
});
LOG(`界面这一屏读到 ${out.界面数字.length} 个数字: ${JSON.stringify(out.界面数字.map((x) => x.数字))}`);

// 切三个分类，看请求参数变不变
out.切分类 = [];
for (const 名 of ['摄影写真', '动漫游戏', '风格插画']) {
  const 起点 = 全部请求.length;
  await page.evaluate((n) => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === n); if (b) b.click(); }, 名);
  await page.waitForTimeout(4000);
  const 新 = 全部请求.slice(起点);
  out.切分类.push({ 分类: 名, 新请求: 新.map((r) => r.url) });
  LOG(`\n【${名}】切了之后新发 ${新.length} 个请求：`);
  for (const r of 新) LOG(`   ${r.方法} ${r.url.slice(0, 220)}${r.postData ? `  POST=${r.postData}` : ''}`);
}

LOG(`\n══════════ 广场打开后全部 API 请求（${全部请求.length} 个）══════════`);
out.请求 = 全部请求.map((r) => ({ 方法: r.方法, url: r.url }));
for (const r of 全部请求) LOG(`  ${r.方法} ${r.url.slice(0, 200)}`);

// ⭐⭐ 正面回答：这一屏的卡在不在 feed/stream 的 40 条里？
LOG(`\n══════════ 正面核实：广场用的到底是不是这个接口 ══════════`);
const feed = 全部请求.filter((r) => /model\/feed\/stream/.test(r.url));
out.feed请求数 = feed.length;
LOG(`feed/stream 请求数: ${feed.length}`);

await writeFile(new URL('./batchDL1.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDL1.json ===');
await browser.close();
