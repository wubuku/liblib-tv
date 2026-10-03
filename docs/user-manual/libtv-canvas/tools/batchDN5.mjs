// Batch DN-5：修掉 DN-4 的漏抓，重测「仅看可商用」。
//
// ⛔ DN-4 的 bug：`收全()` 里的起点 `起 = 页.length` 取在**切分类之后**，
//    而**点分类标签那一刻就已经发出了 `page=1`** —— 它被排除在统计之外。
//    症状很典型：**页序列从 2 开始**（`[2,3,4,5]…`），算式却"自检通过"。
//    对照 DM-1 已知 `风格插画` = 738：DN-4 读到 698，**698 + 40 = 738** —— 漏的正是 page 1。
//    ⇒ **「算式自检通过」不能证明没漏页** —— 算式只验内部一致性，不验起点对不对。
//
// ⭐ 修法：把起点标记**提到切分类之前**，让切分类那一页也算进来。
//
// ⭐ 顺带回答一个更要紧的问题：开态那个 641 补上 page 1 之后，
//    和关态 738 的差**到底是不是「被筛掉的张数」**。
//    DN-4 报「只在打开态 39 张」⇒ 集合不是包含关系 ⇒ 要查清为什么。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 关态: null, 开态: null, 对照: null, 收尾勾选: null };
const SAVE = () => writeFile(new URL('./batchDN5.json', import.meta.url), JSON.stringify(out, null, 2));

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
    页.push({ page: j?.data?.page, hasMore: j?.data?.hasMore, 条数: arr.length, modelLicense: bj.modelLicense ?? null, uuid: arr.map((r) => r.uuid), 名字: arr.map((r) => r.name) });
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

// ⭐ 起点由外部传入 —— 必须在「点分类标签」**之前**取，才能把 page=1 算进来
const 收全 = async (标签, 起) => {
  const uu = new Set(); const 名字 = new Set();
  let 轮 = 0; let 无新 = 0;
  for (let i = 0; i <= 60; i += 1) {
    const 前 = 页.length;
    if (i > 0) {
      await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = v.scrollHeight; });
      await page.waitForTimeout(2100);
    } else {
      await page.waitForTimeout(500);
    }
    轮 = i;
    for (const p of 页.slice(起)) { p.uuid.forEach((u) => uu.add(u)); }
    for (const p of 页.slice(起)) { (p.名字 || []).forEach((n) => 名字.add(n)); }
    const 末 = 页.slice(起).filter((p) => p.uuid.length).slice(-1)[0];
    const 到底 = await page.evaluate(() => {
      const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600);
      return v ? Math.round(v.scrollTop) >= Math.round(v.scrollHeight) - Math.round(v.clientHeight) - 8 : null;
    });
    if (页.length - 前 === 0) 无新 += 1; else 无新 = 0;
    if (i > 0 && 到底 && 末?.hasMore === false && 无新 >= 2) break;
    if (无新 >= 5 && i > 0) break;
  }
  const 我的 = 页.slice(起).filter((p) => p.uuid.length);
  const 去重页 = [...new Set(我的.map((p) => p.page))].sort((a, b) => a - b);
  const 末页 = 我的.find((p) => p.page === Math.max(...去重页));
  const 首页 = 我的.find((p) => p.page === Math.min(...去重页));
  const 算式 = 去重页.length > 1 ? (去重页.length - 1) * 40 + (末页?.uuid.length || 0) : (末页?.uuid.length || 0);
  const rec = {
    滚了轮数: 轮, 页数: 去重页.length, 页序列头尾: [去重页[0], 去重页[去重页.length - 1]],
    首页页号: 首页?.page, 首页条数: 首页?.uuid.length,
    末页page: 末页?.page, 末页条数: 末页?.uuid.length, 末页hasMore: 末页?.hasMore,
    uuid去重数: uu.size, 算式, 算式吻合: 算式 === uu.size,
    名字去重数: 名字.size,
    modelLicense取值: [...new Set(我的.map((p) => (p.modelLicense === null ? '无' : JSON.stringify(p.modelLicense))))],
    uuid: [...uu],
  };
  LOG(`  ${标签}: 页数 ${rec.页数}（${rec.页序列头尾[0]}…${rec.页序列头尾[1]}）首页条数 ${rec.首页条数} | 末页 ${rec.末页page}(${rec.末页条数}条,hasMore=${rec.末页hasMore})`);
  LOG(`     uuid去重 ${rec.uuid去重数} | 算式 ${算式} ${rec.算式吻合 ? '✅' : '⛔'} | 名字去重 ${rec.名字去重数} | modelLicense=${JSON.stringify(rec.modelLicense取值)}`);
  return rec;
};

// ---------- ① 关闭态（起点在切分类之前） ----------
LOG('=== ① 风格插画 · 关闭态 ===');
await page.waitForTimeout(1000);
const 起关 = 页.length;                      // ⭐ 先记起点
await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '风格插画'); if (b) b.click(); });
await page.waitForTimeout(4000);              // ⭐ 让 page=1 到达
const 关 = await 收全('关闭态', 起关);
out.关态 = 关; SAVE();

// ---------- ② 打开态 ----------
LOG('\n=== ② 风格插画 · 打开态 ===');
LOG(`点勾选后重读: ${await 翻勾选()}（应 true）`);
const 起开 = 页.length;
await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = 0; });
await page.waitForTimeout(3500);
const 开 = await 收全('打开态', 起开);
out.开态 = 开; SAVE();

// ---------- ③ 对照 ----------
const A = new Set(关.uuid); const B = new Set(开.uuid);
const 被筛掉 = [...A].filter((x) => !B.has(x));
const 新出现 = [...B].filter((x) => !A.has(x));
LOG(`\n══════ 对照 ══════`);
LOG(`关闭 ${A.size}（DM-1 已知 738：${A.size === 738 ? '✅ 完全吻合，漏抓已修好' : `⚠️ 与 738 差 ${A.size - 738}`}）`);
LOG(`打开 ${B.size}`);
LOG(`⭐ 被「仅看可商用」筛掉: ${被筛掉.length} 张`);
LOG(`⭐ 打开后新出现: ${新出现.length} 张`);
LOG(`保留率: ${((B.size / A.size) * 100).toFixed(1)}%`);
out.对照 = { 关闭态: A.size, 打开态: B.size, 被筛掉数: 被筛掉.length, 新出现数: 新出现.length, 保留率: (B.size / A.size * 100).toFixed(1) + '%' };
if (被筛掉.length) {
  LOG(`\n被筛掉的卡（前 12 个名字）:`);
  const 名集 = new Map();
  for (const p of 页) (p.名字 || []).forEach((n, i) => { if (p.uuid[i] && 被筛掉.includes(p.uuid[i]) && !名集.has(n)) 名集.set(n, p.uuid[i]); });
  [...名集.keys()].slice(0, 12).forEach((n) => LOG(`   ${n}`));
  out.被筛掉的卡名 = [...名集.keys()].slice(0, 30);
}
SAVE();

const 收尾 = await 翻勾选();
LOG(`\n收工勾选状态: ${收尾}（应 false）`);
out.收尾勾选 = 收尾;
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDN5.json ===');
