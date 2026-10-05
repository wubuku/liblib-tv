// ⭐⭐⭐⭐⭐ Batch FJ-1：在**真实生产 bundle** 里查那几个一直没查清的 📖
//
// FH 已经证实：本仓库的 `src/` 是克隆（`package.json` 的 name 就叫 liblib-tv-canvas-clones），
// ⛔ 回答不了界面问题；而手册引的 `10v03g6udfcrl.js` 是**从站点抓下来的真实 bundle**，
// 但它**不在本地** —— 是当时在浏览器里抓的。
// ⭐ 所以这一轮**在页面上下文里重新抓一遍**，而且一次查多个目标。
//
// 要查的 📖（全部只读，零风险，只是 GET 几个已加载的 JS 文件）：
//   ① `loadingMore` / `allLoaded`  —— 一直没人说得清是什么
//   ② `heat` / `score` / `likeCount` —— 三个数字分别是什么
//   ③ `canSearch` —— 搜索框的可用条件
//   ④ `materialMissingVersionCannotFavorite` —— 收藏按钮为什么有时点不了
//   ⑤ ⭐⭐ 顺带查**「单画布编辑锁」**：`lib.mjs` 的 `isEditorLocked` 在检测
//      「会话已过期」「请刷新页面以继续编辑」两段文案，
//      而**手册里一个字都没写这个功能**。查它在源码里是什么条件、什么组件。
//
// ⭐ 判据：只报**逐字命中**，并把命中处的上下文原样打出来 —— 不做转述。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFJ1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 120));

  // 页面上下文里列出所有已加载的 script
  const 脚本 = await page.evaluate(() => [...document.querySelectorAll('script[src]')].map((s) => s.src));
  记(`已加载 script ${脚本.length} 个`);

  // 逐个抓文本，搜目标串
  const 目标 = ['loadingMore', 'allLoaded', 'materialMissingVersionCannotFavorite', 'canSearch', 'likeCount', '会话已过期', '请刷新页面以继续编辑', '正在编辑'];
  // ⛔⚠️ page.evaluate 只能传 **一个** 参数（缺陷 404，踩过一次）
  const 命中 = await page.evaluate(async ({ list, keys }) => {
    const 找到 = [];
    for (const src of list) {
      let txt = '';
      try {
        const r = await fetch(src, { credentials: 'omit' });
        if (!r.ok) continue;
        txt = await r.text();
      } catch (e) { continue; }
      if (txt.length < 500) continue;
      for (const k of keys) {
        let i = txt.indexOf(k);
        let n = 0;
        while (i >= 0 && n < 3) {
          找到.push({ 文件: src.split('/').pop().slice(0, 40), 字节: txt.length, 词: k, 上下文: txt.slice(Math.max(0, i - 180), i + 220) });
          i = txt.indexOf(k, i + 1); n++;
        }
      }
    }
    return 找到;
  }, { list: 脚本, keys: 目标 });

  记(`—— 命中 ${命中.length} 处 ——`);
  const 按词 = {};
  for (const h of 命中) (按词[h.词] = 按词[h.词] || []).push(h);
  for (const [词, 组] of Object.entries(按词)) {
    记(`▪ 「${词}」命中 ${组.length} 处，文件 ${[...new Set(组.map((g) => g.文件))].join(', ')}`);
    for (const g of 组.slice(0, 2)) {
      记('   —— ' + g.上下文.replace(/\s+/g, ' ').slice(0, 330));
    }
  }
  const 没命中 = 目标.filter((k) => !按词[k]);
  记(`⛔ 没命中：${JSON.stringify(没命中)}`);
  R.读数.命中 = 命中;
  R.读数.脚本数 = 脚本.length;
  R.读数.没命中 = 没命中;
} catch (e) {
  记('❌ 出错：' + (e && e.message ? e.message : String(e)));
} finally {
  try { await 浏览器.browser.close(); } catch (e) { /* 关 */ }
  记('done');
}
