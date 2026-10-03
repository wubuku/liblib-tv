// Batch DL-2：把分类真实数量数出来 —— 用**翻页累积**，不用无限滚动。
//
// ⛌ DL-0 的 `total = 40` **作废**：请求体里明写 `"pageSize":40`（前端写死），
//    所以响应里的 `total` 必然等于 pageSize ⇒ 它是**单页条数**，不是分类总量。
//    我上一轮差点把「九个分类都是 40」写成结论 —— 幸好看到了 `pageSize`。
//
// ⭐ 正确做法：广场是**无限滚动** ⇒ 它内部一定在**反复翻页**。
//    所以：⭐ **不去构造请求**（只读、不自己发），而是**触发页面自己翻页**（滚到底），
//    然后把**每一条 feed/stream 响应**里的 `data.data[]` 按 `uuid` 去重累积。
//    每次翻页 +40 条，滚到「不再有新页」为止 ⇒ 累积数 = 真实总量。
//
// ⚠️ 分类在 **POST body 的 `tagIds`** 里（不在 query）—— 已由 DL-1 坐实。
//    读数要**按 tagIds 分组**，否则会把不同分类的页混在一起。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
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

// ---------- 收集：每次响应记下 tagIds + 该页的全部 uuid ----------
const 页 = [];
page.on('response', async (resp) => {
  try {
    if (!/model\/feed\/stream/.test(resp.url())) return;
    const req = resp.request();
    let body = ''; try { body = req.postData() || ''; } catch { body = ''; }
    const m = body.match(/"tagIds":\[([^\]]*)\]/);
    const tagIds = m ? m[1] : '(无)';
    const text = await resp.text();
    if (!text) return;
    let j; try { j = JSON.parse(text); } catch { return; }
    const arr = (j && j.data && j.data.data) || [];
    页.push({
      tagIds, 时间: Date.now(),
      page: j?.data?.page, total: j?.data?.total, pageSize: j?.data?.pageSize, hasMore: j?.data?.hasMore,
      uuid: arr.map((r) => r.uuid),
    });
  } catch { /* 忽略 */ }
});

await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(5000);

// ---------- 逐分类：切过去 → 反复滚到底，累积它的页 ----------
const 分类 = ['风格插画', '摄影写真', '动漫游戏', '电商营销'];
out.结果 = [];
const MAX页 = 12;

for (const 名 of 分类) {
  const 起点 = 页.length;
  await page.evaluate((n) => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === n); if (b) b.click(); }, 名);
  await page.waitForTimeout(3500);
  const 我的 = 页.filter((p) => p.uuid.length && p.时间 >= 0).slice(起点);
  // 记下这个分类的 tagIds 特征（取第一页的）
  const 特征 = 我的.length ? 我的[0].tagIds : '(没抓到)';
  const 集 = new Set();
  let 无新 = 0; let 轮 = 0; let 抓到页数 = 我的.length;
  for (let i = 0; i < MAX页; i += 1) {
    for (const u of 我的.flatMap((p) => p.uuid)) 集.add(u);
    轮 = i + 1;
    // ⭐ 判收敛：连续 2 轮滚动都没带来新页
    const 前 = 抓到页数;
    await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = v.scrollHeight; });
    await page.waitForTimeout(3200);
    抓到页数 = 页.length;
    if (抓到页数 === 前) { 无新 += 1; if (无新 >= 2) break; } else 无新 = 0;
  }
  // 滚动后再累积一次
  for (const u of 页.slice(起点).flatMap((p) => p.uuid)) 集.add(u);
  const 我的页 = 页.slice(起点).filter((p) => p.tagIds === 特征);
  const rec = {
    分类: 名, tagIds: 特征, 滚了轮数: 轮, 抓到页数: 我的页.length,
    去重后张数: 集.size,
    每页条数: [...new Set(我的页.map((p) => p.uuid.length))],
    hasMore序列: 我的页.map((p) => p.hasMore),
    page序列: 我的页.map((p) => p.page),
  };
  out.结果.push(rec);
  LOG(`\n【${名}】tagIds=${特征.slice(0, 40)}…`);
  LOG(`   滚 ${轮} 轮，捕获 ${rec.抓到页数} 页，每页条数 ${JSON.stringify(rec.每页条数)}`);
  LOG(`   page 序列: ${JSON.stringify(rec.page序列)}`);
  LOG(`   hasMore 序列: ${JSON.stringify(rec.hasMore序列)}`);
  LOG(`   ⭐ 按 uuid 去重后共 ${rec.去重后张数} 张`);
  await writeFile(new URL('./batchDL2.json', import.meta.url), JSON.stringify(out, null, 2));
}

await writeFile(new URL('./batchDL2.json', import.meta.url), JSON.stringify(out, null, 2));
LOG('\n=== 已写 tools/batchDL2.json ===');
await browser.close();
