// ⭐⭐⭐⭐⭐ Batch FY-6：用**实测到的**「新建画布」按钮建一张画布，探新手引导
//
// FY-5 的结论：按钮在，aria 逐字是 `新建画布`，框 `[346,57,24,24]`（第一行）。
// ⛔ **FY-4 说「没有」是因为查询范围写窄了**（只看 role/tabindex/data-*，
//    漏掉了只有 aria 的）⇒ 缺陷 497。
//
// ⭐ 本轮真正要回答的问题：
//   `onboardingStep1-4`（第1/4步…第4/4步）在**新建画布**上会不会自动弹？
//
// 造一个新 projectId 是有状态的操作，但属 CRUD 范围内。
// ⛔ 建完只读引导，不点「生成」、不点引导里的「跳过」或「下一步」。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const 主画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFY6.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = (名, 过, 明) => { R.断言.push({ 名, 过, 明 }); 记(`${过 ? '✅' : '❌'} ${名} —— ${明}`); };

// ⭐ 引导判据：文案表里那几句**逐字**，外加「跟着做，快速上手」这个跳过条
const 探引导 = () => page.evaluate(() => {
  const 词 = ['第1/4步', '第2/4步', '第3/4步', '第4/4步', '跟着做，快速上手',
    '双击或右键创建新节点', '图片上方工具栏有高清', '拖拽一个或多个节点',
    '把多个作品打组', '先跟着引导完成这一步', '知道了', '跳过', '下一步', '上一步'];
  const 找到 = [];
  for (const w of 词) {
    for (const e of document.querySelectorAll('*')) {
      if (e.children.length) continue;
      const t = (e.innerText || '').trim();
      if (!t.includes(w)) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) continue;
      if (r.x < -200 || r.y < -200 || r.x > 2000 || r.y > 1200) continue;
      找到.push({ 词: w, tag: e.tagName, x: Math.round(r.x), y: Math.round(r.y),
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

  // 建跑前基线
  const 前 = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
  记(`建跑前主画布 ${前} 个节点`);

  // ── ① 打开下拉，按 aria 找到新建按钮
  记('\n--- ① 打开下拉并按 aria 找「新建画布」---');
  await page.mouse.click(200, 24);
  await page.waitForTimeout(1600);

  const 按钮 = await page.evaluate(() => {
    const b = document.querySelector('[aria-label="新建画布"]');
    if (!b) return null;
    const r = b.getBoundingClientRect();
    if (r.width < 8) return null;
    return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
  });
  R.读数.新建按钮 = 按钮;
  断言('找到「新建画布」按钮', !!按钮, 按钮 ? `框 ${按钮.框.join(',')}` : 'querySelector 返回 null');
  if (!按钮) { 记('  ⛔ 找不到，放弃'); }
  else {
    记(`  框 ${按钮.框.join(',')}；先拍下拉全貌`);
    await page.screenshot({ path: resolve(EVID, 'fy6-1-下拉里的新建按钮.png') });
    const clip = { x: Math.max(0, 按钮.框[0] - 120), y: Math.max(0, 按钮.框[1] - 30),
      width: 150, height: 80 };
    await page.screenshot({ path: resolve(EVID, 'fy6-2-新建按钮特写.png'), clip });

    // 落点自证
    const 落 = await page.evaluate(({ x, y }) => {
      const e = document.elementFromPoint(x, y);
      if (!e) return null;
      let p = e, 命中 = null;
      for (let i = 0; i < 6 && p; i++) { if (p.getAttribute('aria-label') === '新建画布') { 命中 = i; break; } p = p.parentElement; }
      return { tag: e.tagName, aria: e.getAttribute('aria-label'), 往上第几层命中: 命中 };
    }, { x: 按钮.中心[0], y: 按钮.中心[1] });
    R.读数.落点 = 落;
    断言('落点属主就是它', 落?.命中 != null, JSON.stringify(落));

    // ── ② 点它
    记('\n--- ② 点「新建画布」---');
    await page.mouse.click(按钮.中心[0], 按钮.中心[1]);
    await page.waitForTimeout(5000);
    const 新URL = page.url();
    R.读数.新URL = 新URL;
    记(`  跳到：${新URL}`);
    await page.screenshot({ path: resolve(EVID, 'fy6-3-新建之后.png') });

    // 可能弹了命名弹窗
    const 弹窗 = await page.evaluate(() => {
      const o = [];
      for (const e of document.querySelectorAll('[role="dialog"], [class*="Modal"]')) {
        const t = (e.innerText || '').trim();
        if (t && t.length < 200) o.push(t);
      }
      return o;
    });
    R.读数.弹窗 = 弹窗;
    if (弹窗.length) 记(`  ⭐ 弹窗：${弹窗.join(' || ')}`);

    // ── ③ 探引导
    记('\n--- ③ 探新手引导 ---');
    await closePromos(page);
    await page.waitForTimeout(2000);
    const G = await 探引导();
    R.读数.引导 = G;
    断言('新画布上出现引导', G.length > 0, G.length ? G.map((g) => `「${g.词}」@${g.x},${g.y} ${g.w}×${g.h}`).join(' / ') : '没找到引导文案');

    if (G.length) {
      await page.screenshot({ path: resolve(EVID, 'fy6-4-引导出现.png') });
      // 读全引导层
      const 详情 = await page.evaluate(() => {
        const o = [];
        for (const e of document.querySelectorAll('*')) {
          const t = (e.innerText || '').trim();
          if (!/第\d\/4步|跟着做/.test(t)) continue;
          const r = e.getBoundingClientRect();
          if (r.width < 40) continue;
          o.push({ tag: e.tagName, cls: (e.className || '').toString().slice(0, 80),
            框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
            文: t.slice(0, 120) });
        }
        return o;
      });
      R.读数.引导层 = 详情;
      记(`  引导层 ${详情.length} 个：`);
      详情.forEach((d) => 记(`   <${d.tag}> ${d.框.join(',')} cls=${d.cls}\n     文「${d.文}」`));
    }
  }
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFY6.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
