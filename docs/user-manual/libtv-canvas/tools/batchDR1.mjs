// Batch DR-1：修好「仅看可商用筛掉多少张」。
//
// ⛔ 前三轮（DN-2/3/4/5）为什么全废，一句话：**每一页的归属是靠「时序」判的。**
//   · 起点记在切分类之后 ⇒ 漏掉切分类那一刻已经发出的 page=1（DN-4：698，真实 738）
//   · 起点记在切分类之前 ⇒ 把**还在飞行中**的上一个分类的请求也算了进去（DN-5：冒出 1086）
//   ⇒ 两种错法都是「时序不可靠」。**「这页属于谁」该由数据自证，不该由时序自证。**
//
// ⭐⭐ 本轮核心改动：**每一页按 `tagIds` 归属**（DM 批验证过的干净判据）。
//    `风格插画` = `520047,…,510017`；`推荐` 不带 tagIds
//    ⇒ 「推荐」的页**无论何时到达都会被过滤掉**，起点放在哪都不影响结果。
//    起点只负责「不漏 page=1」：等「看到 tagIds 匹配且 page=1 的响应」为止，不靠固定 sleep。
//
// ⭐ 算式也改了：**逐页用实际条数求和**，不再用 `页数×40` 反推
//    （DM-5 已经被这个假设坑过一次：首屏 41 条、末页 5 条）。
//
// ⭐ 阳性对照（判据必须自证）：关闭态结果必须 **等于 DM 批独立测过的 738**。
//    对不上就说明本轮数据有问题，结论作废。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const 本类 = '520047,520048,520049,520050,520051,520052,520053,510011,510012,510013,510014,510015,510016,510017';
const out = { 归属键: 本类, 关态: null, 开态: null, 对照: null, 收尾勾选: null };
const SAVE = () => writeFile(new URL('./batchDR1.json', import.meta.url), JSON.stringify(out, null, 2));

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

const 页 = [];
page.on('response', async (resp) => {
  try {
    if (!/model\/feed\/stream/.test(resp.url())) return;
    let bj = {}; try { bj = JSON.parse(resp.request().postData() || '{}'); } catch { /* 忽略 */ }
    const t = await resp.text(); if (!t) return;
    let j; try { j = JSON.parse(t); } catch { return; }
    const arr = (j?.data?.data) || [];
    页.push({
      page: j?.data?.page, hasMore: j?.data?.hasMore, 条数: arr.length,
      tagIds: Array.isArray(bj.tagIds) ? bj.tagIds.join(',') : '(无)',
      modelLicense: bj.modelLicense ?? null,
      uuid: arr.map((r) => r.uuid), 名字: arr.map((r) => r.name),
    });
    SAVE();
  } catch { /* 忽略 */ }
});

await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(5000);

const 读勾选 = () => page.evaluate(() => {
  for (const lb of document.querySelectorAll('label,div,span')) {
    if (/仅看可商用/.test(lb.textContent || '') && lb.children.length <= 2) {
      const inp = lb.querySelector('input[type="checkbox"]');
      if (inp) return inp.checked;
    }
  }
  return null;
});
const 翻勾选 = async () => {
  await page.evaluate(() => {
    for (const lb of document.querySelectorAll('label,div,span')) {
      if (/仅看可商用/.test(lb.textContent || '') && lb.children.length <= 2) {
        const inp = lb.querySelector('input[type="checkbox"]');
        if (inp) { inp.click(); return; }
      }
    }
  });
  await page.waitForTimeout(3500);
  return 读勾选();
};

// ⭐⭐ 核心：按 tagIds 归属，不按时序
const 属本类 = () => 页.filter((p) => p.tagIds === 本类 && p.uuid.length);

const 等首页 = async (标签) => {
  const t0 = Date.now();
  for (let i = 0; i < 30; i += 1) {
    const 首页 = 属本类().find((p) => p.page === 1);
    if (首页) { LOG(`  ${标签}：page=1 已到达（${首页.条数} 条，用了 ${Date.now() - t0}ms）`); return true; }
    await page.waitForTimeout(500);
  }
  LOG(`  ⚠️ ${标签}：等了 15 秒没看到 tagIds 匹配且 page=1 的响应`);
  return false;
};

const 收全 = async (标签) => {
  const 看到 = new Set(属本类().map((p) => p.page));
  let 轮 = 0; let 无新 = 0;
  for (let i = 1; i <= 60; i += 1) {
    const 前 = 属本类().length;
    await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = v.scrollHeight; });
    await page.waitForTimeout(2100);
    轮 = i;
    for (const p of 属本类()) 看到.add(p.page);
    const 我的 = 属本类();
    const 末 = 我的[我的.length - 1];
    const 到底 = await page.evaluate(() => {
      const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600);
      return v ? Math.round(v.scrollTop) >= Math.round(v.scrollHeight) - Math.round(v.clientHeight) - 8 : null;
    });
    if (我的.length === 前) 无新 += 1; else 无新 = 0;
    if (到底 && 末?.hasMore === false && 无新 >= 2) break;
    if (无新 >= 5) { LOG(`   ⚠️ ${标签} 连续 5 轮无新页，强制收手`); break; }
  }
  const 我的 = 属本类();
  const uu = new Set(我的.flatMap((p) => p.uuid));
  const 页序 = [...看到].sort((a, b) => a - b);
  const 末页 = 我的.find((p) => p.page === Math.max(...页序));
  // ⭐ 逐页用**实际条数**求和，不用 页数×40 反推
  const 求和 = 页序.reduce((acc, p) => acc + (我的.find((x) => x.page === p)?.条数 || 0), 0);
  const rec = {
    滚了轮数: 轮, 页数: 页序.length, 页序头尾: [页序[0], 页序[页序.length - 1]],
    末页: 末页?.page, 末页条数: 末页?.条数, 末页hasMore: 末页?.hasMore,
    uuid去重: uu.size, 逐页实际条数求和: 求和, 自检一致: 求和 === uu.size,
    modelLicense取值: [...new Set(我的.map((p) => (p.modelLicense === null ? '无' : JSON.stringify(p.modelLicense))))],
    名字去重: new Set(我的.flatMap((p) => p.名字 || [])).size,
    uuid: [...uu],
  };
  LOG(`  ${标签}: ${rec.页数} 页（${JSON.stringify(rec.页序头尾)}）末页 ${rec.末页}(${rec.末页条数}条,hasMore=${rec.末页hasMore})`);
  LOG(`     uuid去重 ${rec.uuid去重} | 逐页实际求和 ${rec.逐页实际条数求和} | ${rec.自检一致 ? '✅自检通过' : '⛔自检不符'} | 名字去重 ${rec.名字去重} | modelLicense=${JSON.stringify(rec.modelLicense取值)}`);
  return rec;
};

// ---------- ① 关闭态 ----------
LOG('=== ① 风格插画 · 关闭态（勾选应为 false）===');
await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '风格插画'); if (b) b.click(); });
await page.waitForTimeout(2500);
LOG(`  勾选状态: ${await 读勾选()}`);
await 等首页('关闭态');
const 关 = await 收全('关闭态');
out.关态 = 关; SAVE();

// ⭐ 阳性对照
const 对照OK = 关.uuid去重 === 738;
LOG(`\n⭐ 阳性对照：关闭态 ${关.uuid去重} vs DM 批独立测得的 738 → ${对照OK ? '✅ 完全吻合，判据可信' : `⛔ 差 ${关.uuid去重 - 738}，本轮数据作废`}`);

// ---------- ② 打开态 ----------
LOG('\n=== ② 风格插画 · 打开态 ===');
LOG(`  点勾选后重读: ${await 翻勾选()}（应 true）`);
await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = 0; });
await page.waitForTimeout(2000);
await 等首页('打开态');
const 开 = await 收全('打开态');
out.开态 = 开; SAVE();

// ---------- ③ 对照 ----------
const A = new Set(关.uuid); const B = new Set(开.uuid);
const 被筛掉 = [...A].filter((x) => !B.has(x));
const 新出现 = [...B].filter((x) => !A.has(x));
LOG(`\n══════ 对照 ══════`);
LOG(`关闭 ${A.size} | 打开 ${B.size}`);
LOG(`⭐ 被「仅看可商用」筛掉: ${被筛掉.length} 张`);
LOG(`⭐ 打开后新出现: ${新出现.length} 张 ${新出现.length ? '（集合不是子集关系，需在正文说明）' : '✅ 子集关系成立'}`);
LOG(`保留率: ${(B.size / A.size * 100).toFixed(1)}%`);
out.对照 = { 关闭: A.size, 打开: B.size, 被筛掉数: 被筛掉.length, 新出现数: 新出现.length, 保留率: (B.size / A.size * 100).toFixed(1) + '%' };

if (被筛掉.length) {
  const 名 = new Set();
  for (const p of 页) {
    if (p.tagIds !== 本类) continue;
    (p.名字 || []).forEach((n, i) => { if (p.uuid[i] && 被筛掉.includes(p.uuid[i])) 名.add(n); });
  }
  LOG(`\n被筛掉的卡（前 12 个名字）:`);
  [...名].slice(0, 12).forEach((n) => LOG(`   ${n}`));
  out.被筛掉的卡名 = [...名].slice(0, 40);
  out.被筛掉的卡名总数 = 名.size;
}
SAVE();

const 收尾 = await 翻勾选();
LOG(`\n收工勾选状态: ${收尾}（应 false）`);
out.收尾勾选 = 收尾;
out.阳性对照通过 = 对照OK;
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDR1.json ===');
