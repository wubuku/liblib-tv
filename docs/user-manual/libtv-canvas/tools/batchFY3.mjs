// ⭐⭐⭐⭐⭐ Batch FY-3：翻遍 62 张画布，找那张会弹新手引导的
//
// FY-2 的收获（写进手册的素材）：项目下拉里是 **62 张数字画布（画布 2~63）
// 加 1 张「手册取证画布」**，**下拉里没有「新建画布」这一项**。
//
// ⇒ 关键推论：新手引导（`onboardingStep1-4`）几乎肯定是
// **「打开某张特定画布时」** 触发的，而这张画布不是我们建过的任何一张
// —— 它很可能是**产品预置的第一张示范画布**，名字和「画布 N」不一样。
//
// 本轮做法：
//   ① 先列出下拉里的**全部**项（FY-2 漏了非数字的那些）
//   ② 逐张打开，探引导文案；⛔ **只 GET，不改任何东西**
//   ③ 一旦找到引导，立刻停下并把它读全
//
// ⛔ 只读。不点「生成」。不改任何节点。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const 主画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [], 扫过: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFY3.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = (名, 过, 明) => { R.断言.push({ 名, 过, 明 }); 记(`${过 ? '✅' : '❌'} ${名} —— ${明}`); };

const 探引导 = () => page.evaluate(() => {
  const 词 = ['第1/4步', '第2/4步', '第3/4步', '第4/4步', '跟着做，快速上手',
    '双击或右键创建新节点', '图片上方工具栏有高清', '拖拽一个或多个节点', '把多个作品打组',
    '先跟着引导完成这一步', '知道了', '跳过'];
  const 找到 = [];
  for (const w of 词) {
    for (const e of document.querySelectorAll('*')) {
      if (e.children.length) continue;
      const t = (e.innerText || '').trim();
      if (!t.includes(w)) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) continue;
      if (r.x < -200 || r.y < -200 || r.x > 2000 || r.y > 1200) continue;
      找到.push({ 词: w, x: Math.round(r.x), y: Math.round(r.y),
        w: Math.round(r.width), h: Math.round(r.height) });
      break;
    }
  }
  return 找到;
});

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(主画布, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(6000);
  await closePromos(page);
  await page.waitForTimeout(4000);

  // ── ① 打开项目下拉，逐项读出「名字 + 它真正的链接/标识」
  记('--- ① 项目下拉逐项实名 ---');
  await page.mouse.click(200, 24);
  await page.waitForTimeout(1500);
  await page.screenshot({ path: resolve(EVID, 'fy3-1-项目下拉全貌.png') });

  const 项 = await page.evaluate(() => {
    const o = [];
    const seen = new Set();
    for (const e of document.querySelectorAll('*')) {
      if (e.children.length) continue;
      const t = (e.innerText || '').trim();
      if (!t || t.length > 24) continue;
      if (!/^画布|手册|示范|示例|新手|教程|我的/.test(t)) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 30 || r.height < 12) continue;
      if (r.x < 100) continue;                 // ⛔ 只认下拉区（顶栏那一列）
      const k = t + '@' + Math.round(r.x);
      if (seen.has(k)) continue;
      seen.add(k);
      o.push({ 名: t, x: Math.round(r.x), y: Math.round(r.y),
        中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        行文: (e.parentElement?.innerText || '').trim().slice(0, 40) });
    }
    return o;
  });
  R.读数.下拉项 = 项;
  const 唯一 = [...new Map(项.map((x) => [x.名, x])).values()];
  记(`  下拉里逐项读到 ${项.length} 个 DOM 行，去重后 ${唯一.length} 个名字：`);
  记(`  ${唯一.map((x) => x.名).join(' / ')}`);

  // ⭐ 非「画布 N」的那些最可疑
  const 可疑 = 唯一.filter((x) => !/^画布 \d+$/.test(x.名));
  记(`\n  ⭐ 非「画布 N」命名的 ${可疑.length} 个：${可疑.map((x) => `「${x.名}」`).join(' / ')}`);

  await page.keyboard.press('Escape');
  await page.waitForTimeout(600);

  // ── ② 逐张打开：先看非「画布 N」的，再看数字最小的几张
  const 候选 = [...可疑, ...唯一.filter((x) => /^画布 (2|3|4|5|6)$/.test(x.名))];
  记(`\n--- ② 逐张打开 ${候选.length} 张，探引导 ---`);

  for (const c of 候选) {
    记(`\n打开「${c.名}」`);
    // 重新开下拉（每张都要重开）
    await page.mouse.click(200, 24);
    await page.waitForTimeout(1200);
    const t = await page.evaluate((名) => {
      for (const e of document.querySelectorAll('*')) {
        if (e.children.length) continue;
        if ((e.innerText || '').trim() !== 名) continue;
        const r = e.getBoundingClientRect();
        if (r.width < 30 || r.height < 10) continue;
        if (r.x < 100) continue;
        return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
      }
      return null;
    }, c.名);
    if (!t) { 记('  ⛔ 下拉里没找到这一项'); await page.keyboard.press('Escape'); continue; }
    await page.mouse.click(t[0], t[1]);
    await page.waitForTimeout(4500);
    await closePromos(page);
    const url = page.url();
    const 节点数 = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
    const 引导 = await 探引导();
    记(`  URL ${url.replace(ORIGIN, '').slice(0, 70)}；节点 ${节点数} 个；引导 ${引导.length} 条`);
    R.扫过.push({ 名: c.名, url, 节点数, 引导: 引导.map((g) => g.词) });

    if (引导.length) {
      断言(`「${c.名}」上有引导`, true, 引导.map((g) => `「${g.词}」@${g.x},${g.y} ${g.w}×${g.h}`).join(' / '));
      await page.screenshot({ path: resolve(EVID, `fy3-找到引导-${c.名}.png`) });
      await page.screenshot({ path: resolve(EVID, 'fy3-2-整屏.png') });
      记(`  ⭐⭐⭐ 找到了！`);
      break;
    } else {
      断言(`「${c.名}」上有引导`, false, `节点 ${节点数} 个，无引导文案`);
      if (节点数 === 0) await page.screenshot({ path: resolve(EVID, `fy3-空画布-${c.名}.png`) });
    }
  }
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFY3.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
