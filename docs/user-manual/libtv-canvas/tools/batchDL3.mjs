// Batch DL-3：把「分类到底有多少张卡」彻底定案 —— ⛔ 收掉 DL-2 和 DI-2 的两个错误结论。
//
// ⛔ 错误 1（DI-2 的措辞）：`风格插画 = 8` 被写成「分类真数」。
//    翻 DI-2 源码，它有 `if (cr3.y < 0 || cr3.y > 620) continue;`
//    ⇒ **8 只是一屏视口内的入口卡数**，从来不是分类总量。
//    （DI-2 当时要回答的是「入口卡占多少」，视口过滤是对的；错的是**账本里的措辞**。）
//
// ⛔ 错误 2（DL-2 的数字）：`去重后 520 张` 也不是真值 ——
//    `hasMore` 13 次全是 `true` ⇒ 12 轮根本没滚到底 ⇒ 520 只是**下界**。
//    而且 4 个分类数字一模一样（都恰好 13 页 × 40），这也是红旗。
//
// ⭐ 本步只问三个问题，且**每轮都同时记 DOM 和网络两个口径**：
//   1. 无限滚动有没有尽头？（到底后还有新页吗 / 有「没有更多了」提示吗）
//   2. 用户**真正看到**的卡片数（DOM 渲染口径）vs 接口给的数据量（uuid 去重口径）差多少？
//   3. 滚动容器到底是哪个？（DL-2 用「第一个 scrollHeight>600 的 viewport」——可能选错）
//
// ⚠️ 阳性对照：如果 scrollTop 到底后 `page` 不再递增，那说明我根本没在驱动这个列表 ⇒ 读数作废。
import { launch, open, closePromos, ORIGIN, shot } from './lib.mjs';
import { writeFile } from 'node:fs/promises';

const URL_ = `${ORIGIN}/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b`;
const LOG = console.log;
const out = { 轮次: [], 页: [], 终局: null };
const SAVE = () => writeFile(new URL('./batchDL3.json', import.meta.url), JSON.stringify(out, null, 2));

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

// ---------- 网络侧：只读，不自己发请求 ----------
page.on('response', async (resp) => {
  try {
    if (!/model\/feed\/stream/.test(resp.url())) return;
    const t = await resp.text(); if (!t) return;
    let j; try { j = JSON.parse(t); } catch { return; }
    const arr = (j && j.data && j.data.data) || [];
    out.页.push({ page: j?.data?.page, total: j?.data?.total, hasMore: j?.data?.hasMore, 条数: arr.length, uuid: arr.map((r) => r.uuid) });
  } catch { /* 忽略 */ }
});

await page.evaluate(() => { const b = document.querySelector('[data-sidebar-btn="open-asset"]'); if (b) b.click(); });
await page.waitForTimeout(2000);
await page.evaluate(() => [...document.querySelectorAll('button')].find((b) => (b.innerText || '').replace(/\s+/g, ' ').trim().startsWith('风格库'))?.click());
await page.waitForTimeout(5000);
await page.evaluate(() => { const b = [...document.querySelectorAll('button')].find((x) => (x.innerText || '').replace(/\s+/g, ' ').trim() === '风格插画'); if (b) b.click(); });
await page.waitForTimeout(4000);

// ---------- DOM 侧：⭐ 用「卡容器往上找最近的 ScrollArea」定位滚动容器，不再猜「第一个大的」 ----------
const 度量 = () => page.evaluate(() => {
  const modals = [...document.querySelectorAll('.mantine-Modal-inner')].filter((e) => {
    const r = e.getBoundingClientRect(); const c = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && +c.opacity > 0;
  });
  if (!modals.length) return { 有弹层: false };
  const root = modals.sort((a, b) => { const ra = a.getBoundingClientRect(); const rb = b.getBoundingClientRect(); return rb.width * rb.height - ra.width * ra.height; })[0];
  // 卡容器 = 详情按钮往上第 3 层（DI-1 实测 191×302）
  const 卡 = new Set();
  for (const D of root.querySelectorAll('button[aria-label="详情"]')) {
    for (let p = D.parentElement, j = 0; p && j < 6; p = p.parentElement, j += 1) {
      const r = p.getBoundingClientRect();
      if (r.width > 150 && r.width < 260 && r.height > 260) { 卡.add(p); break; }
    }
  }
  const 全部 = [...卡];
  const 视口内 = 全部.filter((e) => { const r = e.getBoundingClientRect(); return r.y >= -20 && r.y <= 700; });
  // ⭐ 从任意一张卡往上找最近的滚动容器
  let vp = 全部[0] ? 全部[0].closest('.mantine-ScrollArea-viewport') : null;
  if (!vp) vp = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600) || null;
  // 找找「没有更多了 / 到底了」之类的收尾文案
  const 尾 = [...document.querySelectorAll('.mantine-Modal-inner *')]
    .filter((e) => e.children.length === 0 && /没有更多|已全部|到底了|没有更多了|暂无更多|更多内容/.test((e.textContent || '').trim()))
    .map((e) => (e.textContent || '').trim()).slice(0, 4);
  const 载入中 = [...document.querySelectorAll('.mantine-Modal-inner *')]
    .filter((e) => e.children.length === 0 && /加载中|载入中|正在加载/.test((e.textContent || '').trim()))
    .map((e) => (e.textContent || '').trim()).slice(0, 3);
  return {
    有弹层: true,
    DOM卡数: 全部.length,
    视口内卡数: 视口内.length,
    容器: vp ? { scrollTop: Math.round(vp.scrollTop), scrollHeight: Math.round(vp.scrollHeight), clientHeight: Math.round(vp.clientHeight) } : null,
    到底: vp ? Math.round(vp.scrollTop) >= Math.round(vp.scrollHeight) - Math.round(vp.clientHeight) - 8 : null,
    收尾文案: 尾,
    载入中文案: 载入中,
    首行卡名: 全部.length ? (全部[0].innerText || '').split('\n')[0].slice(0, 18) : null,
    末行卡名: 全部.length ? (全部[全部.length - 1].innerText || '').split('\n')[0].slice(0, 18) : null,
  };
});

const 基线 = await 度量();
LOG(`【风格插画 · 基线】DOM ${基线.DOM卡数} 张 / 视口内 ${基线.视口内卡数} / 容器 ${JSON.stringify(基线.容器)}`);
out.基线 = 基线; SAVE();

// ---------- 逐轮滚到底 ----------
const MAX = 30;
for (let i = 1; i <= MAX; i += 1) {
  const 前页 = out.页.length;
  await page.evaluate(() => {
    const v = [...document.querySelectorAll('.mantine-ScrollArea-viewport')].find((e) => e.scrollHeight > 600);
    if (v) v.scrollTop = v.scrollHeight;
  });
  await page.waitForTimeout(2600);
  const m = await 度量();
  const rec = { 轮: i, 新增页: out.页.length - 前页, ...m };
  out.轮次.push(rec); SAVE();
  LOG(`  轮 ${String(i).padStart(2)}: DOM ${String(m.DOM卡数).padStart(4)} | 视口内 ${String(m.视口内卡数).padStart(2)} | 新增页 ${rec.新增页} | top ${m.容器?.scrollTop}/${m.容器?.scrollHeight} | 到底 ${m.到底}`);
  // 到底了且连续 3 轮没新页 ⇒ 收敛
  if (m.到底 && out.轮次.slice(-3).every((r) => r.新增页 === 0)) { LOG(`  ⛔ 判定：滚动已到尽头且连续 3 轮无新页，第 ${i} 轮停止`); break; }
  if (out.轮次.length >= 6 && out.轮次.slice(-6).every((r) => r.新增页 === 0)) { LOG(`  ⛔ 判定：连续 6 轮无新页，第 ${i} 轮停止`); break; }
}

const 终 = await 度量();
const uuid集 = new Set(out.页.flatMap((p) => p.uuid));
out.终局 = {
  ...终,
  抓到页数: out.页.length,
  uuid去重数: uuid集.size,
  page序列: out.页.map((p) => p.page),
  hasMore序列: out.页.map((p) => p.hasMore),
  每页条数: [...new Set(out.页.map((p) => p.条数))],
  total序列: [...new Set(out.页.map((p) => p.total))],
};
LOG(`\n══════ 终局 ══════`);
LOG(`DOM 卡片总数: ${终.DOM卡数}`);
LOG(`接口 uuid 去重: ${uuid集.size}（共 ${out.页.length} 页）`);
LOG(`page 序列: ${JSON.stringify(out.终局.page序列)}`);
LOG(`hasMore 末值: ${终.到底 ? '' : ''}${JSON.stringify(out.页.slice(-3).map((p) => p.hasMore))}`);
LOG(`total 取值集合: ${JSON.stringify(out.终局.total序列)}`);
LOG(`每页条数: ${JSON.stringify(out.终局.每页条数)}`);
LOG(`收尾文案: ${JSON.stringify(终.收尾文案)}`);
LOG(`容器: ${JSON.stringify(终.容器)}`);
await shot(page, 'DL-c-滚到底时的一屏.png');
LOG('📸 DL-c');
SAVE();
await browser.close();
LOG('\n=== 已写 tools/batchDL3.json ===');
