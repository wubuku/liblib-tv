// Batch DN-4：正面坐实「仅看可商用」到底按**哪个字段**筛。
//
// ⛔ DN-3 也不能用：关态 uuid 去重 1044 vs 算式 1045（自检不符，页数 27 而末页 page=28 ⇒ 漏页），
//    而且「打开后新出现 61 张」—— **`推荐` 是动态推荐池，两次抓取内容本就不一样**。
//    ⇒ 拿 `推荐` 做「筛前 vs 筛后」的集合对照，**在原理上就不成立**。
//
// ⭐ 本步换思路：**不比数量，比字段。**
//   DJ 那轮的成功经验是「同值匹配」—— 先看界面上确切是什么，再去数据里找对应。
//   这里反过来：把「被筛掉的卡」和「保留下来的卡」的记录**逐字段比**，
//   找出**哪一个字段不同**，那就是「仅看可商用」对应的开关。
//
// ⭐ 顺带解决「保留率只有 96.5%」的疑问：如果找到的字段能**完全解释**差异，
//    那 3.5% 的差就是**真实的非商用卡**，不是噪声。
//
// ⚠️ 换用 `风格插画`：DM 测它总量 738 且**两次独立复现**过 ⇒ 比 `推荐` 稳定。
//    首屏 28/30 带「商用」徽标 ⇒ 混得开，能筛出东西来。
//
// ⚠️ 存储：每页 400KB，只保留**标量字段**（剔除 images / attachment / extraInfo 等大对象），
//    否则 JSON 会到几十 MB。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 关态: [], 开态: [], 字段差异: null };
const SAVE = () => writeFile(new URL('./batchDN4.json', import.meta.url), JSON.stringify(out, null, 2));

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

const 大字段 = new Set(['images', 'attachment', 'extraInfo', 'tagsV2', 'originalUrl', 'webpUrl', 'posterUrl', 'videoUrl', 'imageUrl', 'avatar']);
let 页 = [];
page.on('response', async (resp) => {
  try {
    if (!/model\/feed\/stream/.test(resp.url())) return;
    let bj = {}; try { bj = JSON.parse(resp.request().postData() || '{}'); } catch { /* 忽略 */ }
    const t = await resp.text(); if (!t) return;
    let j; try { j = JSON.parse(t); } catch { return; }
    const arr = (j?.data?.data) || [];
    const 精简 = arr.map((r) => {
      const o = { __uuid: r.uuid, __name: r.name };
      for (const k of Object.keys(r)) {
        if (大字段.has(k)) continue;
        const v = r[k];
        if (v === null || ['string', 'number', 'boolean'].includes(typeof v)) o[k] = v;
        else if (Array.isArray(v) && v.length <= 6) o[k] = JSON.stringify(v).slice(0, 120);
      }
      return o;
    });
    页.push({ page: j?.data?.page, hasMore: j?.data?.hasMore, modelLicense: bj.modelLicense ?? null, recs: 精简 });
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

const 收全 = async (标签) => {
  const 起 = 页.length;
  const uu = new Set();
  let 轮 = 0; let 无新 = 0;
  for (let i = 1; i <= 60; i += 1) {
    const 前 = 页.length;
    await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = v.scrollHeight; });
    await page.waitForTimeout(2100);
    轮 = i;
    for (const r of 页.slice(起).flatMap((p) => p.recs)) uu.add(r.__uuid);
    const 末 = 页.slice(起).filter((p) => p.recs.length).slice(-1)[0];
    const 到底 = await page.evaluate(() => {
      const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600);
      return v ? Math.round(v.scrollTop) >= Math.round(v.scrollHeight) - Math.round(v.clientHeight) - 8 : null;
    });
    if (页.length - 前 === 0) 无新 += 1; else 无新 = 0;
    if (到底 && 末?.hasMore === false && 无新 >= 2) break;
    if (无新 >= 5) { LOG(`   ⚠️ ${标签} 强制收手`); break; }
  }
  const 我的 = 页.slice(起).filter((p) => p.recs.length);
  const 去重页 = [...new Set(我的.map((p) => p.page))].sort((a, b) => a - b);
  const 末页 = 我的.find((p) => p.page === Math.max(...去重页));
  const 算式 = 去重页.length > 1 ? (去重页.length - 1) * 40 + (末页?.recs.length || 0) : (末页?.recs.length || 0);
  const rec = {
    滚了轮数: 轮, 页数: 去重页.length, 页序列: 去重页, 末页page: 末页?.page, 末页条数: 末页?.recs.length,
    末页hasMore: 末页?.hasMore, uuid去重数: uu.size, 算式, 自检一致: 算式 === uu.size,
    modelLicense取值: [...new Set(我的.map((p) => (p.modelLicense === null ? '无' : JSON.stringify(p.modelLicense))))],
  };
  LOG(`  ${标签}: 页数 ${rec.页数}(序列${JSON.stringify(去重页.slice(0, 4))}…) 末页 ${rec.末页page}(${rec.末页条数}条,hasMore=${rec.末页hasMore}) uuid去重 ${rec.去重数 || rec.uuid去重数} 算式 ${算式} ${rec.自检一致 ? '✅' : '⛔不符'} modelLicense=${JSON.stringify(rec.modelLicense取值)}`);
  return { 概览: rec, 记录: 我的.flatMap((p) => p.recs) };
};

await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '风格插画'); if (b) b.click(); });
await page.waitForTimeout(4000);
LOG(`风格插画 · 勾选状态 ${await 读勾选()}（应 false）`);
LOG('\n=== ① 关闭态 ===');
const 关 = await 收全('关闭态');
out.关态 = 关.记录; SAVE();

LOG('\n=== ② 打开态 ===');
LOG(`点勾选后重读: ${await 翻勾选()}（应 true）`);
const 开 = await 收全('打开态');
out.开态 = 开.记录; SAVE();

// ---------- 字段差异分析 ----------
const 关表 = new Map(关.记录.map((r) => [r.__uuid, r]));
const 开表 = new Map(开.记录.map((r) => [r.__uuid, r]));
const 只在关 = 关.记录.filter((r) => !开表.has(r.__uuid));
const 只在开 = 开.记录.filter((r) => !关表.has(r.__uuid));
LOG(`\n══════ 集合关系 ══════`);
LOG(`关闭 ${关表.size} / 打开 ${开表.size} | 只在关闭态 ${只在关.length} | 只在打开态 ${只在开.length}`);
LOG(`开 ⊆ 关 ？ ${只在开.length === 0 ? '✅ 是（开态是关态的子集）' : '⛔ 否'}`);

if (只在关.length) {
  const 键 = [...new Set(只在关.flatMap((r) => Object.keys(r)))].filter((k) => !k.startsWith('__'));
  LOG(`\n=== 只在关闭态出现的 ${只在关.length} 张卡，逐字段看它们和「保留卡」的差别 ===`);
  const 保留样本 = [...开表.values()].slice(0, 40);
  const 差异表 = [];
  for (const k of 键) {
    const 被滤值 = [...new Set(只在关.map((r) => JSON.stringify(r[k])))];
    const 保留值 = [...new Set(保留样本.map((r) => JSON.stringify(r[k])))];
    // 只在「被滤掉的卡」里出现、在「保留的卡」里完全不出现的取值 ⇒ 判别字段
    const 判别 = 被滤值.filter((v) => !保留值.includes(v));
    if (判别.length && 判别.length === 被滤值.length) {
      差异表.push({ 字段: k, 被筛取值: 判别, 保留取值: 保留值.slice(0, 4) });
    }
  }
  if (差异表.length) {
    LOG('⭐⭐ 找到能完全区分「被筛掉」与「保留」的字段：');
    for (const r of 差异表) LOG(`   \`${r.字段}\`: 被筛掉的一律是 ${JSON.stringify(r.被筛取值)}，保留的是 ${JSON.stringify(r.保留取值)}`);
  } else {
    LOG('⛔ 没有任何单一字段能完全区分 ⇒ 需逐个字段打印');
    for (const k of 键) {
      const a = [...new Set(只在关.slice(0, 5).map((r) => JSON.stringify(r[k])))];
      const b = [...new Set(保留样本.slice(0, 5).map((r) => JSON.stringify(r[k])))];
      if (JSON.stringify(a) !== JSON.stringify(b)) LOG(`   候选 \`${k}\`: 被筛 ${JSON.stringify(a)} / 保留 ${JSON.stringify(b)}`);
    }
  }
  out.字段差异 = 差异表;
  LOG(`\n被筛掉的卡（前 6）:`);
  for (const r of 只在关.slice(0, 6)) LOG(`   ${r.__name} | uuid=${r.__uuid}`);
}

// 保留卡的 openAccess 分布
if (开表.size) {
  const 分布 = {};
  for (const r of 开表.values()) {
    for (const k of ['openAccess', 'openMix', 'isRunnable', 'privilege', 'modelType', 'checkpointType']) {
      if (k in r) { 分布[k] = 分布[k] || {}; 分布[k][JSON.stringify(r[k])] = (分布[k][JSON.stringify(r[k])] || 0) + 1; }
    }
  }
  LOG(`\n=== 打开态 ${开表.size} 张卡的关键字段分布 ===`);
  for (const k of Object.keys(分布)) LOG(`   ${k}: ${JSON.stringify(分布[k])}`);
  out.打开态字段分布 = 分布;
}
if (只在关.length) {
  const 分布 = {};
  for (const r of 只在关) {
    for (const k of ['openAccess', 'openMix', 'isRunnable', 'privilege', 'modelType', 'checkpointType']) {
      if (k in r) { 分布[k] = 分布[k] || {}; 分布[k][JSON.stringify(r[k])] = (分布[k][JSON.stringify(r[k])] || 0) + 1; }
    }
  }
  LOG(`\n=== 被筛掉的 ${只在关.length} 张卡的同一批字段分布 ===`);
  for (const k of Object.keys(分布)) LOG(`   ${k}: ${JSON.stringify(分布[k])}`);
}

SAVE();
const 收尾 = await 翻勾选();
LOG(`\n收工勾选状态: ${收尾}（应 false）`);
out.收尾勾选 = 收尾;
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDN4.json ===');
