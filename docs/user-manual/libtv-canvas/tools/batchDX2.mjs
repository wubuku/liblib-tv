// Batch DX-2：特效广场的数据到底从哪个接口来？
//
// ⛔ DX-1 已经把**页签**问题彻底坐实（切进特效广场后：
//    `特效广场` 高亮、`风格广场` 页签「⛔ 不存在」⇒ 两者是各自独立的一组页签），
//    但**卡记录 0 条** —— 我只认 `/api/www/model/feed/stream` + `j.data.data` 这个形状。
//
// ⭐ 三种可能，本轮一次分开：
//   ① 同一个接口，但**响应结构不同**（`j.data.data` 不是数组）
//   ② **另一个接口**（`model/feed/stream` 压根没被调用）
//   ③ 数据在切入口**之前**就到了（监听器在，理应抓到 ⇒ 可排除）
//
// ⭐ 做法：把所有 XHR/fetch 响应全记下来（URL + 状态 + 体积 + 结构摘要），
//   切入口前后各存一份，**diff 出来的就是特效广场特有的请求**。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 前: [], 后: [], 新增请求: null, feed响应结构: null };
const SAVE = () => writeFileSync(new URL('./batchDX2.json', import.meta.url), JSON.stringify(out, null, 2));

const { browser, page } = await launch();
const 全部 = [];
page.on('response', async (resp) => {
  try {
    const rt = resp.request().resourceType();
    if (!/xhr|fetch/.test(rt)) return;
    const u = resp.url();
    if (/analytics|log|sentry|track|beacon|report/i.test(u)) return;
    const t = await resp.text().catch(() => '');
    let j = null; try { j = JSON.parse(t); } catch { /* 非 JSON */ }
    const 摘要 = (o) => {
      if (!o || typeof o !== 'object') return typeof o;
      const k = Object.keys(o);
      const d = o.data;
      return { 顶层键: k.slice(0, 12), data类型: Array.isArray(d) ? `数组(${d.length})` : typeof d, data键: d && typeof d === 'object' && !Array.isArray(d) ? Object.keys(d).slice(0, 12) : null };
    };
    全部.push({ rt, url: u.slice(0, 160), 状态: resp.status(), 字节: t.length, 是JSON: !!j, 摘要: j ? 摘要(j) : null });
  } catch { /* 忽略 */ }
});

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

// 只开侧栏，不进任何广场
await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2500);
LOG(`侧栏已开，收到 ${全部.length} 个 XHR/fetch`);

// 标记分界
const 分界 = 全部.length;
const 点 = await page.evaluate(() => {
  const b = [...document.querySelectorAll('button')].find((x) => { const t = (x.innerText || '').replace(/\s+/g, ' ').trim(); const r = x.getBoundingClientRect(); return /^特效库/.test(t) && r.width > 0; });
  if (!b) return null; b.click(); return (b.innerText || '').replace(/\s+/g, ' ').trim();
});
LOG(`点了入口: ${JSON.stringify(点)}`);
await page.waitForTimeout(7000);
LOG(`点完之后累计 ${全部.length} 个 XHR/fetch`);

out.前 = 全部.slice(0, 分界);
out.后 = 全部.slice(分界);
out.新增请求 = 全部.slice(分界).map((x) => x.url);
LOG(`\n══════ ⭐ 点「特效库」之后**新增**的请求 ${out.新增请求.length} 个 ══════`);
for (const u of out.新增请求) LOG(`   ${u}`);

const feed = 全部.filter((x) => /model\/feed\/stream/.test(x.url));
LOG(`\n══════ 全程 model/feed/stream 响应 ${feed.length} 个 ══════`);
for (const f of feed) LOG(`   ${f.字节} 字节 ${f.是JSON ? JSON.stringify(f.摘要) : '非 JSON'}`);
out.feed响应结构 = feed;
LOG(`\n⭐ 判定：feed/stream 共 ${feed.length} 次，其中 ${feed.filter((f) => f.摘要?.data类型 === '数组' || /^\w+\(\d+\)$/.test(String(f.摘要?.data类型))).length} 个的 data 是数组`);
const 别名 = 全部.filter((x) => /lens|effect|material/i.test(x.url) && !/model\/feed\/stream/.test(x.url));
LOG(`⭐ 含 lens/effect/material 字样的其他请求 ${别名.length} 个:`);
for (const a of 别名.slice(0, 8)) LOG(`   ${a.字节} 字节 ${a.url}`);
out.其他候选接口 = 别名.map((x) => x.url);
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDX2.json ===');
