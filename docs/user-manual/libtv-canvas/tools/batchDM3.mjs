// Batch DM-3：把 `推荐` 补上，并抓两张此前没拿到的东西。
//
// DM-2 的诊断结论（假设已坐实）：`推荐` 的 feed/stream 请求体里
//   **没有 `tagIds`，取而代之的是 `types:[27,42,43,79,40,70,37,39,53,55,68]`**
//   外加 `models:[21,5]` / `isTemplate:"true"` / `sort:0`
// ⇒ DM-1 的判据 ③「只取 tagIds 匹配该分类的页」把 `推荐` 整类滤没了。
//    **是我的过滤器滤掉的，不是它没有内容。**
//
// 本轮做三件事：
//   ① `推荐` 用**自己的判据**（types 匹配）滚到底，把真实数量数出来
//   ② 抓 `public/tag/v3` 的**完整**响应 —— 那是**分类 ↔ 标签 id 的权威对照表**
//      （DM-2 只截了前 200 字符，956 字节里应该有全部 10 个分类）
//   ③ 记录 `sort` 字段在切分类时会不会变（DE 批次结论是「界面上没有排序入口」，
//      这里补一个接口层的读数。⚠️ 字段存在 ≠ 有排序 UI，别混为一谈）
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 页: [], 分类对照表: null, sort观测: [] };
const SAVE = () => writeFile(new URL('./batchDM3.json', import.meta.url), JSON.stringify(out, null, 2));

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

// ---------- 监听：feed/stream（记 types + sort）与 tag/v3（存全文） ----------
page.on('response', async (resp) => {
  try {
    const url = resp.url();
    if (/public\/tag\/v3/.test(url)) {
      const t = await resp.text();
      if (t) { try { out.分类对照表 = JSON.parse(t); } catch { out.分类对照表 = { 原文: t }; } SAVE(); }
      return;
    }
    if (!/model\/feed\/stream/.test(url)) return;
    let body = ''; try { body = resp.request().postData() || ''; } catch { body = ''; }
    let bj = {}; try { bj = JSON.parse(body); } catch { /* 保留原文 */ }
    const t = await resp.text(); if (!t) return;
    let j; try { j = JSON.parse(t); } catch { return; }
    const arr = (j && j.data && j.data.data) || [];
    const tm = body.match(/"tagIds":\[([^\]]*)\]/);
    out.页.push({
      page: j?.data?.page, hasMore: j?.data?.hasMore, pageSize: j?.data?.pageSize, total: j?.data?.total,
      条数: arr.length, uuid: arr.map((r) => r.uuid),
      tagIds: tm ? tm[1] : null,
      types: bj.types || null, models: bj.models || null, sort: bj.sort, isTemplate: bj.isTemplate ?? null,
    });
    SAVE();
  } catch { /* 忽略 */ }
});

await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(6000);

// ⭐ `推荐` 的页 = tagIds 为 null 且 types 非 null
const 推荐页 = () => out.页.filter((p) => !p.tagIds && Array.isArray(p.types) && p.types.length);

const 度量 = () => page.evaluate(() => {
  const modals = [...document.querySelectorAll('.mantine-Modal-inner')].filter((e) => {
    const r = e.getBoundingClientRect(); const c = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && +c.opacity > 0;
  });
  if (!modals.length) return { 有弹层: false };
  const root = modals.sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; })[0];
  const 卡 = new Set();
  for (const D of root.querySelectorAll('button[aria-label="详情"]')) {
    for (let p = D.parentElement, j = 0; p && j < 6; p = p.parentElement, j += 1) {
      const r = p.getBoundingClientRect();
      if (r.width > 150 && r.width < 260 && r.height > 260) { 卡.add(p); break; }
    }
  }
  const 尾 = [...document.querySelectorAll('.mantine-Modal-inner *')]
    .filter((e) => e.children.length === 0 && /没有更多|已全部|到底了|暂无更多/.test((e.textContent || '').trim()))
    .map((e) => (e.textContent || '').trim()).slice(0, 3);
  let vp = [...卡][0] ? [...卡][0].closest('.mantine-ScrollArea-viewport') : null;
  return {
    DOM卡数: 卡.size, 收尾文案: 尾,
    容器: vp ? { scrollTop: Math.round(vp.scrollTop), scrollHeight: Math.round(vp.scrollHeight), clientHeight: Math.round(vp.clientHeight) } : null,
    到底: vp ? Math.round(vp.scrollTop) >= Math.round(vp.scrollHeight) - Math.round(vp.clientHeight) - 8 : null,
  };
});

// ---------- ① 先在 `推荐`（未点任何分类）滚到底 ----------
LOG('=== ① 推荐（进广场的默认分类）===');
LOG(`基线: ${JSON.stringify(await 度量())}`);
let 轮 = 0; let 无新 = 0; const 轨迹 = [];
for (let i = 1; i <= 60; i += 1) {
  const 前 = out.页.length;
  await page.evaluate(() => { const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600); if (v) v.scrollTop = v.scrollHeight; });
  await page.waitForTimeout(2200);
  轮 = i;
  const m = await 度量();
  const 新页 = out.页.slice(-1)[0];
  轨迹.push({ 轮: i, 新页, DOM: m.DOM卡数, 到底: m.到底, 收尾: m.收尾文案 });
  if (out.页.length - 前 === 0) 无新 += 1; else 无新 = 0;
  if (m.到底 && 新页?.hasMore === false && 无新 >= 2) break;
  if (无新 >= 5) { LOG('   ⚠️ 连续 5 轮无新页但未满足判据，强制收手'); break; }
}
const rec = 推荐页();
const uu = new Set(rec.flatMap((p) => p.uuid));
const 去重页 = [...new Set(rec.map((p) => p.page))].sort((a, b) => a - b);
const 末 = rec.find((p) => p.page === Math.max(...去重页)) || rec[rec.length - 1];
const 算式 = 去重页.length > 1 ? (去重页.length - 1) * (末?.pageSize || 40) + (末?.uuid.length || 0) : (末?.uuid.length || 0);
out.推荐 = {
  页数: 去重页.length, 末页page: 末?.page, 末页条数: 末?.uuid.length, 末页hasMore: 末?.hasMore,
  uuid去重数: uu.size, 算式, 自检一致: 算式 === uu.size,
  types: 末?.types, models: 末?.models, isTemplate: 末?.isTemplate, sort: 末?.sort,
  滚了轮数: 轮, 收尾文案: (轨迹[轨迹.length - 1] || {}).收尾 || [],
  DOM取值集合: [...new Set(轨迹.map((t) => t.DOM))].sort((a, b) => a - b),
};
LOG(`页数 ${out.推荐.页数} | 末页 ${out.推荐.末页page}(${out.推荐.末页条数}条, hasMore=${out.推荐.末页hasMore}) | uuid去重 ${uu.size} | 算式 ${算式} | ${out.推荐.自检一致 ? '✅一致' : '⛔不一致'}`);
LOG(`types=${JSON.stringify(out.推荐.types)} models=${JSON.stringify(out.推荐.models)} isTemplate=${out.推荐.isTemplate} sort=${out.推荐.sort}`);
LOG(`收尾文案: ${JSON.stringify(out.推荐.收尾文案)} | DOM ${JSON.stringify(out.推荐.DOM取值集合)}`);
await shot(page, 'DM-a-推荐分类滚到底.png');
LOG('📸 DM-a');
SAVE();

// ---------- ② 分类 ↔ 标签 权威对照表 ----------
if (out.分类对照表?.data) {
  LOG('\n=== ② 分类 ↔ 标签 id 对照表（public/tag/v3，categoryCode=model）===');
  for (const g of out.分类对照表.data) LOG(`  ${g.name}: [${(g.ids || []).join(',')}]`);
} else {
  LOG('\n⚠️ 没抓到 public/tag/v3 响应');
}

// ---------- ③ sort 字段观测：逐个分类点一遍，只看 sort / types 有没有变 ----------
LOG('\n=== ③ sort 字段逐分类观测 ===');
for (const 名 of ['摄影写真', '电商营销', '动漫游戏', '风格插画', '平面设计', '建筑及室内设计', '创意玩法', '文创周边', '小说推文']) {
  const 前 = out.页.length;
  await page.evaluate((n) => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === n); if (b) b.click(); }, 名);
  await page.waitForTimeout(2800);
  const p = out.页.slice(前).find((x) => x.page === 1) || out.页[out.页.length - 1];
  const 观测 = { 分类: 名, sort: p?.sort, types: p?.types || null, models: p?.models, isTemplate: p?.isTemplate, tagIds有值: !!p?.tagIds };
  out.sort观测.push(观测);
  LOG(`  ${名}: sort=${观测.sort} types=${JSON.stringify(观测.types)} models=${JSON.stringify(观测.models)} isTemplate=${观测.isTemplate} 带tagIds=${观测.tagIds有值}`);
  SAVE();
}

SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDM3.json ===');
