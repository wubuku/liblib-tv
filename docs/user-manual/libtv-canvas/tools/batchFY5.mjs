// ⭐⭐⭐⭐⭐ Batch FY-5：核实「新建画布」按钮到底在不在下拉里
//
// 矛盾出现了（缺陷 497 的典型）：
//   `20-reference.md` 的「画布下拉」表写着：
//       新建 | 右上角加号按钮，`aria-label="新建画布"`
//       行   | `aria-label="切换到画布 {名称}"`
//   而 FY-4 在下拉里找 `[role] [tabindex] [data-*]`：
//       **0 个** —— 整列 63 行，一个都没有这些标记。
//
// ⇒ 两种可能：
//   H1 手册记错了（那是**别的**下拉，比如画布列表页的）
//   H2 FY-4 的查询范围太窄（只查了 x∈[100,700]、y∈[30,700]）
//
// 本轮把整个下拉**连同右上角**完整扫一遍，
// 逐条记录所有元素的 tag / role / aria / tabindex / data-* / cursor。
// ⛔ 纯读，不点。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const 主画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFY5.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = (名, 过, 明) => { R.断言.push({ 名, 过, 明 }); 记(`${过 ? '✅' : '❌'} ${名} —— ${明}`); };

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(主画布, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(6000);
  await closePromos(page);
  await page.waitForTimeout(4000);

  await page.mouse.click(200, 24);
  await page.waitForTimeout(1600);
  await page.screenshot({ path: resolve(EVID, 'fy5-1-下拉开着.png') });

  // ── ① 找到下拉容器（有 2260 高内容的那层）
  记('--- ① 定位下拉容器 ---');
  const 容器 = await page.evaluate(() => {
    let 最佳 = null;
    for (const e of document.querySelectorAll('div')) {
      const r = e.getBoundingClientRect();
      if (r.height < 300) continue;                 // 内容高度 2260
      if (r.x < 120 || r.x > 400) continue;
      const t = e.innerText || '';
      if (!/画布 63/.test(t) || !/画布 2\b/.test(t)) continue;
      if (!最佳 || r.height < 最佳.h) 最佳 = { h: r.height, cls: (e.className || '').toString().slice(0, 60),
        框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
    }
    return 最佳;
  });
  R.读数.容器 = 容器;
  记(`  最内层匹配容器：${JSON.stringify(容器)}`);
  if (!容器) { 记('  ⛔ 没找到下拉容器'); }
  else {
    // ── ② 容器内所有「可点特征」元素，一个不漏
    记('\n--- ② 容器内带可点特征的元素（role/tabindex/data-*/aria/cursor:pointer）---');
    const 特征 = await page.evaluate((框) => {
      const o = [];
      for (const e of document.querySelectorAll('[role],[tabindex],[data-project-id],[data-id],[data-canvas-id],[aria-label],[class*="cursor-pointer"]')) {
        const r = e.getBoundingClientRect();
        if (r.x + r.width < 框[0] - 10 || r.x > 框[0] + 框[2] + 10) continue;
        if (r.y + r.height < 框[1] - 10 || r.y > 框[1] + 框[3] + 10) continue;
        const cs = getComputedStyle(e);
        o.push({ tag: e.tagName, 文: (e.innerText || '').trim().slice(0, 18),
          role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
          tabindex: e.getAttribute('tabindex'),
          dataId: e.getAttribute('data-id'), projectId: e.getAttribute('data-project-id'),
          cursor: cs.cursor,
          框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
      }
      return o;
    }, 容器.框);
    R.读数.特征元素 = 特征;
    记(`  ${特征.length} 个：`);
    特征.slice(0, 25).forEach((e) => 记(`   <${e.tag}> 「${e.文}」 role=${e.role} aria=${e.aria} tabindex=${e.tabindex} data-id=${e.dataId} cursor=${e.cursor} ${e.框.join(',')}`));
    if (!特征.length) 记('  ⛔ 容器内一个可点特征都没有');

    // ── ③ 单独找「新建」：按 aria、按文字、按 + 号，三路都试
    记('\n--- ③ 三路找「新建画布」 ---');
    const 三路 = await page.evaluate((框) => {
      const 出 = { aria: [], 文字: [], 加号: [] };
      for (const e of document.querySelectorAll('*')) {
        const r = e.getBoundingClientRect();
        if (r.width < 8 || r.height < 8) continue;
        if (r.x + r.width < 框[0] - 20 || r.x > 框[0] + 框[2] + 20) continue;
        if (r.y + r.height < 框[1] - 20 || r.y > 框[1] + 框[3] + 20) continue;
        const a = e.getAttribute('aria-label') || '';
        if (/新建|创建/.test(a)) 出.aria.push({ tag: e.tagName, aria: a, 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
        const t = (e.innerText || '').trim();
        if (/^(新建|创建)/.test(t) && t.length < 10) 出.文字.push({ tag: e.tagName, 文: t, 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
        if (/^\+?$/.test(t) && r.width < 30 && r.height < 30) 出.加号.push({ tag: e.tagName, 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
      }
      return 出;
    }, 容器.框);
    R.读数.三路 = 三路;
    记(`  按 aria 找：${三路.aria.length} 个 ${JSON.stringify(三路.aria)}`);
    记(`  按文字找：${三路.文字.length} 个 ${JSON.stringify(三路.文字)}`);
    记(`  按加号找：${三路.加号.length} 个 ${JSON.stringify(三路.加号.slice(0, 5))}`);

    // ── ④ 容器右上角那一块（手册说「右上角加号」）
    记('\n--- ④ 容器右上角 60×60 范围内有什么 ---');
    const 角 = await page.evaluate((框) => {
      const o = [];
      for (const e of document.querySelectorAll('*')) {
        const r = e.getBoundingClientRect();
        if (r.width < 4 || r.height < 4) continue;
        if (r.x < 框[0] + 框[2] - 70 || r.x > 框[0] + 框[2] + 20) continue;
        if (r.y < 框[1] - 20 || r.y > 框[1] + 60) continue;
        o.push({ tag: e.tagName, 文: (e.innerText || '').trim().slice(0, 10),
          aria: e.getAttribute('aria-label'), cls: (e.className || '').toString().slice(0, 50),
          框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] });
      }
      return o;
    }, 容器.框);
    R.读数.右上角 = 角;
    记(`  ${角.length} 个：`);
    角.forEach((e) => 记(`   <${e.tag}> 文「${e.文}」 aria=${e.aria} ${e.框.join(',')} cls=${e.cls}`));
  }
  await page.screenshot({ path: resolve(EVID, 'fy5-2-末态.png') });
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFY5.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
