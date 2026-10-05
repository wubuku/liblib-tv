// ⭐⭐⭐⭐⭐ Batch FY-2：从主画布 UI 上找「新建画布」入口，不再猜 URL 路径
//
// FY-1 失败原因（缺陷 495）：`/workspace?spaceId=…` 返回 **404**，
// 而我在下手前**没有查账本里记过哪些 URL** —— 账本只记了 `/canvas?…`。
// ⇒ **路径要靠 UI 上的入口去发现，不能凭「听起来对」拼。**
//
// 本轮做法：从主画布的顶栏 / 左下 / 项目下拉里，逐个找写着
// 「新建」「画布」「项目」的可点元素，读它们的 href 或点击后的跳转。
//
// ⛔ 新建画布是 CRUD，允许。⛔ 只读引导层，不点「生成」。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const 主画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFY2.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = (名, 过, 明) => { R.断言.push({ 名, 过, 明 }); 记(`${过 ? '✅' : '❌'} ${名} —— ${明}`); };

const 探引导 = () => page.evaluate(() => {
  const 词 = ['第1/4步', '第2/4步', '第3/4步', '第4/4步', '跟着做，快速上手',
    '双击或右键创建新节点', '图片上方工具栏有高清', '拖拽一个或多个节点', '把多个作品打组',
    '先跟着引导完成这一步'];
  const 找到 = [];
  for (const w of 词) {
    for (const e of document.querySelectorAll('*')) {
      if (e.children.length) continue;
      const t = (e.innerText || '').trim();
      if (!t.includes(w)) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 4 || r.height < 4) continue;
      if (r.x < -200 || r.y < -200 || r.x > 2000 || r.y > 1200) continue;
      找到.push({ 词: w, x: Math.round(r.x), y: Math.round(r.y) });
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
  let 上 = -1, 稳 = 0;
  for (let i = 0; i < 20; i++) {
    const n = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
    if (n === 上) { 稳++; if (稳 >= 3) { 记(`主画布稳定在 ${n} 个节点`); break; } } else 稳 = 0;
    上 = n; await page.waitForTimeout(1200);
  }

  // ── ① 全页所有 href（这是「发现路径」最可靠的办法）
  记('--- ① 页面上所有 href ---');
  const hrefs = await page.evaluate(() => [...new Set(
    [...document.querySelectorAll('a[href]')].map((a) => a.getAttribute('href'))
      .filter((h) => h && !h.startsWith('#'))
  )]);
  R.读数.href = hrefs;
  记(`  ${hrefs.length} 个：`);
  hrefs.slice(0, 30).forEach((h) => 记(`   ${h}`));

  // ── ② 顶栏与左下的可点元素，逐个实名
  记('\n--- ② 顶部/左下可点元素实名 ---');
  const 可点 = await page.evaluate(() => {
    const o = [];
    for (const e of document.querySelectorAll('a, button, [role="button"], [class*="cursor-pointer"]')) {
      const r = e.getBoundingClientRect();
      if (r.width < 10 || r.height < 10) continue;
      if (r.y > 120) continue;                       // ⛔ 只看顶部区域
      o.push({ tag: e.tagName, 文: (e.innerText || '').trim().slice(0, 16),
        aria: e.getAttribute('aria-label'), href: e.getAttribute('href'),
        x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
        中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] });
    }
    return o;
  });
  R.读数.顶栏 = 可点;
  可点.forEach((e) => 记(`   ${e.tag} 文「${e.文}」aria=${e.aria} href=${e.href} @${e.x},${e.y} ${e.w}×${e.h}`));

  // ── ③ 打开「画布 2 ⌄」那个下拉，看里面有没有「新建画布」
  记('\n--- ③ 打开项目下拉 ---');
  const 下拉 = 可点.find((e) => /画布\s*\d/.test(e.文) || /未命名工作区/.test(e.文));
  if (!下拉) {
    记('  ⛔ 顶栏没找到项目下拉');
  } else {
    记(`  点「${下拉.文}」@${下拉.中心.join(',')}`);
    await page.mouse.click(下拉.中心[0], 下拉.中心[1]);
    await page.waitForTimeout(1400);
    await page.screenshot({ path: resolve(EVID, 'fy2-1-项目下拉.png') });
    const 菜单 = await page.evaluate(() => {
      const o = [];
      for (const e of document.querySelectorAll('[role="menu"] *, [class*="Dropdown"] *, [class*="Popover"] *')) {
        const t = (e.innerText || '').trim();
        if (!t || t.length > 24) continue;
        const r = e.getBoundingClientRect();
        if (r.width < 30 || r.height < 12) continue;
        o.push({ 文: t, y: Math.round(r.y), x: Math.round(r.x),
          中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] });
      }
      const seen = new Map();
      for (const o2 of o) if (!seen.has(o2.y) || seen.get(o2.y).文.length < o2.文.length) seen.set(o2.y, o2);
      return [...seen.values()].sort((a, b) => a.y - b.y);
    });
    R.读数.下拉菜单 = 菜单;
    记(`  菜单读到 ${菜单.length} 行：${菜单.map((m) => `「${m.文}」`).join(' / ') || '（无）'}`);
    const 新 = 菜单.find((m) => /新建|创建/.test(m.文));
    if (!新) { 记('  ⛔ 菜单里没有新建项'); await page.keyboard.press('Escape'); }
    else {
      记(`  ⭐ 点「${新.文}」`);
      await page.mouse.click(新.中心[0], 新.中心[1]);
      await page.waitForTimeout(3000);
      记(`  跳到：${page.url()}`);
      await page.screenshot({ path: resolve(EVID, 'fy2-2-点新建之后.png') });
      const D = await 探引导();
      R.读数.新建后 = D;
      断言('新建画布后引导出现', D.length > 0, D.length ? D.map((x) => `「${x.词}」@${x.x},${x.y}`).join(' / ') : '没找到引导文案');
    }
  }
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFY2.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
