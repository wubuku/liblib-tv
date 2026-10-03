// Batch DM-1：把**十个分类**的真实数量一次数完。
//
// DL-3 已经把方法验证过了（风格插画 = 738，算式与 uuid 去重完全吻合）。
// 本轮把那套方法套到剩下 9 个分类上，并**重跑风格插画当阳性对照** ——
// 如果复现 738，说明方法稳定；如果不复现，说明方法有问题，后面 9 个数都不能信。
//
// ⭐ 判据照 DL-3 定的三条治法来（见 PROGRESS §89.5）：
//   ① 收敛 = 容器到底 **且** 末页 hasMore===false **且** 连续 2 轮无新页（三者齐）
//   ② 滚动容器 = 从卡容器 closest('.mantine-ScrollArea-viewport') 反查，不猜
//   ③ 只累积 **tagIds 匹配该分类** 的页，避免把切分类窗口里的杂页算进去
//
// ⭐⭐ 自检：每类都算一遍 `(页数-1)×pageSize + 末页条数`，与 uuid 去重数比对。
//    对不上就是异常，必须报出来而不是照样写进结论。
//
// ⚠️ 10 类 × 最多 60 轮 ⇒ 远超 290s 看门狗 ⇒ nohup 后台跑，且**每类处理完立刻落盘**。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 结果: [] };
const SAVE = () => writeFile(new URL('./batchDM1.json', import.meta.url), JSON.stringify(out, null, 2));

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

// ---------- 网络层：只读。记下每页的 tagIds，判据 ③ 要用 ----------
const 页 = [];
page.on('response', async (resp) => {
  try {
    if (!/model\/feed\/stream/.test(resp.url())) return;
    let body = ''; try { body = resp.request().postData() || ''; } catch { body = ''; }
    const m = body.match(/"tagIds":\[([^\]]*)\]/);
    const tagIds = m ? m[1] : '(无)';
    const t = await resp.text(); if (!t) return;
    let j; try { j = JSON.parse(t); } catch { return; }
    const arr = (j && j.data && j.data.data) || [];
    页.push({ tagIds, page: j?.data?.page, total: j?.data?.total, pageSize: j?.data?.pageSize, hasMore: j?.data?.hasMore, uuid: arr.map((r) => r.uuid) });
  } catch { /* 忽略 */ }
});

await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(5000);

// 判据 ②：从卡容器反查滚动容器
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
  const 全部 = [...卡];
  let vp = 全部[0] ? 全部[0].closest('.mantine-ScrollArea-viewport') : null;
  if (!vp) vp = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600) || null;
  const 尾 = [...document.querySelectorAll('.mantine-Modal-inner *')]
    .filter((e) => e.children.length === 0 && /没有更多|已全部|到底了|暂无更多/.test((e.textContent || '').trim()))
    .map((e) => (e.textContent || '').trim()).slice(0, 3);
  return {
    DOM卡数: 全部.length,
    容器: vp ? { scrollTop: Math.round(vp.scrollTop), scrollHeight: Math.round(vp.scrollHeight), clientHeight: Math.round(vp.clientHeight) } : null,
    到底: vp ? Math.round(vp.scrollTop) >= Math.round(vp.scrollHeight) - Math.round(vp.clientHeight) - 8 : null,
    收尾文案: 尾,
  };
});

const 分类表 = ['推荐', '摄影写真', '电商营销', '动漫游戏', '风格插画', '平面设计', '建筑及室内设计', '创意玩法', '文创周边', '小说推文'];
const MAX = 60;

for (const 名 of 分类表) {
  const ok = await page.evaluate((n) => {
    const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === n);
    if (!b) return false; b.click(); return true;
  }, 名);
  if (!ok) { LOG(`⛔ 找不到分类「${名}」`); out.结果.push({ 分类: 名, 错误: '找不到分类按钮' }); SAVE(); continue; }

  await page.waitForTimeout(3500);
  // 判据 ③：只取「切完之后、且 tagIds 非 (无)」的页当本类第一页的特征
  const 本类页 = () => 页.filter((p) => p.tagIds !== '(无)');
  const 特征 = 本类页().length ? 本类页()[本类页().length - 1].tagIds : '(没抓到)';

  let 轮 = 0; let 无新 = 0; const 轨迹 = [];
  for (let i = 1; i <= MAX; i += 1) {
    const 前 = 页.length;
    await page.evaluate(() => {
      const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600);
      if (v) v.scrollTop = v.scrollHeight;
    });
    await page.waitForTimeout(2200);
    轮 = i;
    const m = await 度量();
    const 我的 = 页.slice(-1)[0];
    轨迹.push({ 轮: i, 新页: 页.length - 前, 到底: m.到底, page: 我的?.page, hasMore: 我的?.hasMore, DOM: m.DOM卡数 });
    if (页.length - 前 === 0) 无新 += 1; else 无新 = 0;
    // 判据 ①：三条齐了才收工
    if (m.到底 && 我的?.hasMore === false && 无新 >= 2) break;
    if (无新 >= 5) { LOG(`   ⚠️ ${名} 连续 5 轮无新页但未满足到底判据，强制收手`); break; }
  }

  // 只累积 tagIds 匹配本类的页
  const 归属 = 页.filter((p) => p.tagIds === 特征);
  const uuid集 = new Set(归属.flatMap((p) => p.uuid));
  const 去重后 = [...new Set(归属.map((p) => p.page))].sort((a, b) => a - b);
  const 末页 = 归属.find((p) => p.page === Math.max(...去重后)) || 归属[归属.length - 1];
  const pageSize = 末页?.pageSize || 40;
  // ⭐⭐ 自检：算式 vs uuid 去重
  const 算式 = 去重后.length > 1 ? (去重后.length - 1) * pageSize + (末页?.uuid.length || 0) : (末页?.uuid.length || 0);
  const rec = {
    分类: 名, tagIds: 特征, 滚了轮数: 轮, 页数: 去重后.length,
    末页page: 末页?.page, 末页条数: 末页?.uuid.length, 末页hasMore: 末页?.hasMore,
    pageSize, uuid去重数: uuid集.size, 算式, 自检一致: 算式 === uuid集.size,
    收尾文案: (轨迹[轨迹.length - 1] || {}).收尾文案 || [],
    DOM取值集合: [...new Set(轨迹.map((t) => t.DOM))].sort((a, b) => a - b),
  };
  out.结果.push(rec);
  LOG(`【${名}】页数 ${rec.页数} | 末页 ${rec.末页page}(${rec.末页条数}条, hasMore=${rec.末页hasMore}) | uuid去重 ${rec.uuid去重数} | 算式 ${算式} | ${rec.自检一致 ? '✅一致' : '⛔不一致'} | 收尾 ${JSON.stringify(rec.收尾文案)} | DOM ${JSON.stringify(rec.DOM取值集合)}`);
  SAVE();
}

SAVE();
LOG('\n══════════ 汇总 ══════════');
for (const r of out.结果) {
  if (r.错误) { LOG(`${r.分类}: ⛔ ${r.错误}`); continue; }
  LOG(`${r.分类}: ${r.uuid去重数} 张（${r.页数} 页，末页 hasMore=${r.末页hasMore}，${r.自检一致 ? '算式吻合' : '⛔算式不符'}）`);
}
await browser.close();
LOG('\n=== 已写 tools/batchDM1.json ===');
