// Batch DN-3：用**干净判据**重测「仅看可商用」。
//
// ⛔ 先作废 DN-2 的「被筛掉 20 张 / 新出现 54 张」：那张 `J_漫剧素材三视图…`（1.1w，JM32）
//    在 DN-2 报告里被列为「被筛掉」，**可它明明白白出现在 DN-d 那张「已勾选」的截图里**。
//    根因：判据用了**卡名**，而卡名**大量重复**（`推荐` 首屏 30 张只有 6 个不同卡名），
//    且两边滚动覆盖的页数不同 ⇒ 集合差集全是噪声。
// ⇒ **卡名不能当唯一标识。** 本轮改用接口返回的 `uuid`。
//
// ⭐ 本轮的设计（每一步都有对照）：
//   ① 两边**都滚到 `hasMore=false`** ⇒ 比的是两个**完整集合**，不是「滚了几轮碰到什么」
//   ② 唯一标识 = `uuid`（卡名、作者名都会重复，uuid 不会）
//   ③ 去掉 DN-2 的竞态：点完勾选框**等 3.5s 再读状态**，不信 `inp.checked` 的即时值
//   ④ 关态那个分类已知总量（`推荐` = 1086，DM 测的）⇒ **顺带做阳性对照**
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 关态: null, 开态: null, 对照: null, 收尾勾选: null };
const SAVE = () => writeFile(new URL('./batchDN3.json', import.meta.url), JSON.stringify(out, null, 2));

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

// ---------- 网络层：uuid 是唯一判据 ----------
let 页 = [];
page.on('response', async (resp) => {
  try {
    if (!/model\/feed\/stream/.test(resp.url())) return;
    let bj = {}; try { bj = JSON.parse(resp.request().postData() || '{}'); } catch { /* 忽略 */ }
    const t = await resp.text(); if (!t) return;
    let j; try { j = JSON.parse(t); } catch { return; }
    const arr = (j?.data?.data) || [];
    页.push({ page: j?.data?.page, hasMore: j?.data?.hasMore, 条数: arr.length, modelLicense: bj.modelLicense ?? null, uuid: arr.map((r) => r.uuid) });
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
// ⭐ 点完等 3.5s 再读，别信即时值（DN-2 就是在这栽的）
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

// ---------- 滚到 hasMore=false，累积完整 uuid 集合 ----------
const 收全 = async (标签) => {
  const 起 = 页.length;
  const uu = new Set();
  let 轮 = 0; let 无新 = 0;
  for (let i = 1; i <= 60; i += 1) {
    const 前 = 页.length;
    await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = v.scrollHeight; });
    await page.waitForTimeout(2100);
    轮 = i;
    for (const u of 页.slice(起).flatMap((p) => p.uuid)) uu.add(u);
    const 末 = 页.slice(起).filter((p) => p.uuid.length).slice(-1)[0];
    const 到底 = await page.evaluate(() => {
      const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600);
      return v ? Math.round(v.scrollTop) >= Math.round(v.scrollHeight) - Math.round(v.clientHeight) - 8 : null;
    });
    if (页.length - 前 === 0) 无新 += 1; else 无新 = 0;
    if (到底 && 末?.hasMore === false && 无新 >= 2) break;
    if (无新 >= 5) { LOG(`   ⚠️ ${标签} 连续 5 轮无新页但未满足判据，强制收手`); break; }
  }
  const 我的 = 页.slice(起).filter((p) => p.uuid.length);
  const 去重页 = [...new Set(我的.map((p) => p.page))].sort((a, b) => a - b);
  const 末页 = 我的.find((p) => p.page === Math.max(...去重页));
  const 算式 = 去重页.length > 1 ? (去重页.length - 1) * 40 + (末页?.uuid.length || 0) : (末页?.uuid.length || 0);
  return {
    滚了轮数: 轮, 页数: 去重页.length, 末页page: 末页?.page, 末页条数: 末页?.uuid.length,
    末页hasMore: 末页?.hasMore, uuid去重数: uu.size, 算式, 自检一致: 算式 === uu.size,
    modelLicense取值: [...new Set(我的.map((p) => (p.modelLicense === null ? '无' : JSON.stringify(p.modelLicense))))],
    uuid: [...uu],
  };
};

// ---------- ① 关态 ----------
LOG('=== ① 关闭态（推荐 分类）===');
await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '推荐'); if (b) b.click(); });
await page.waitForTimeout(4000);
LOG(`确认勾选状态: ${await 读勾选()}（应为 false）`);
const 关 = await 收全('关闭态');
LOG(`页数 ${关.页数} | 末页 ${关.末页page}(${关.末页条数}条, hasMore=${关.末页hasMore}) | uuid去重 ${关.uuid去重数} | 算式 ${关.算式} | ${关.自检一致 ? '✅自检吻合' : '⛔自检不符'}`);
LOG(`modelLicense 取值: ${JSON.stringify(关.modelLicense取值)}`);
out.关态 = 关; SAVE();

// ---------- ② 开态 ----------
LOG('\n=== ② 打开态（同一分类）===');
const 翻后 = await 翻勾选();
LOG(`点击后重新读勾选状态: ${翻后}（应为 true）`);
const 开 = await 收全('打开态');
LOG(`页数 ${开.页数} | 末页 ${开.末页page}(${开.末页条数}条, hasMore=${开.末页hasMore}) | uuid去重 ${开.uuid去重数} | 算式 ${开.算式} | ${开.自检一致 ? '✅自检吻合' : '⛔自检不符'}`);
LOG(`modelLicense 取值: ${JSON.stringify(开.modelLicense取值)}`);
out.开态 = 开; SAVE();

// ---------- ③ 对照 ----------
const A = new Set(关.uuid); const B = new Set(开.uuid);
const 被筛掉 = [...A].filter((x) => !B.has(x));
const 新出现 = [...B].filter((x) => !A.has(x));
LOG(`\n══════ 对照 ══════`);
LOG(`关闭态 uuid ${A.size} | 打开态 uuid ${B.size}`);
LOG(`⭐ 被「仅看可商用」筛掉: ${被筛掉.length} 张`);
LOG(`⭐ 打开后新出现: ${新出现.length} 张 ${新出现.length ? '⛔不该有——集合不该只增不减' : ''}`);
LOG(`保留率: ${((B.size / A.size) * 100).toFixed(1)}%`);
out.对照 = { 关闭态: A.size, 打开态: B.size, 被筛掉数: 被筛掉.length, 新出现数: 新出现.length, 被筛掉样本: 被筛掉.slice(0, 20) };
SAVE();

// 截图：打开态回到顶部
await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = 0; });
await page.waitForTimeout(1500);
await shot(page, 'DN-e-仅看可商用-筛选后全貌.png');
LOG('📸 DN-e');

// ---------- ④ 收工：改回关闭并确认 ----------
const 收尾 = await 翻勾选();
LOG(`\n收工时勾选状态: ${收尾}（应为 false）`);
out.收尾勾选 = 收尾;
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDN3.json ===');
