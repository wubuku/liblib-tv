// ⭐⭐⭐⭐⭐ Batch FZ-1：真的建一张画布 —— 关掉抽屉再点「新建画布」
//
// FY-6 为什么没建成（缺陷 499）：
//   点击落点自证**是对的**（`elementFromPoint` 命中 BUTTON 本身，第 0 层），
//   框 `[346,57,24,24]` 也与截图完全对上（加号在下拉**右上角**、
//   分区标题「画布」那一行，⛔ **不在「画布 63」那一行旁边**）。
//   ⛔ 但点了之后 URL 没变、没弹任何东西。
//   ⇒ 最可能的原因：**右侧 TV Director 抽屉当时开着**，
//      它盖住了屏幕右侧；或者下拉在点击前就被别的东西关掉了。
//
// 本轮顺序：
//   ① 关掉右侧抽屉与通知横幅
//   ② 打开下拉
//   ③ 先读一遍画布总数（建前基线）
//   ④ 点加号，**盯 3 种可能的响应**：URL 变 / 弹命名框 / 下拉里多一行
//   ⑤ 每次都记「点了之后立刻读到什么」
//
// ⛔ 新建画布是 CRUD，允许。⛔ 建完只读，不建节点、不点生成。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const 主画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFZ1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = (名, 过, 明) => { R.断言.push({ 名, 过, 明 }); 记(`${过 ? '✅' : '❌'} ${名} —— ${明}`); };

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
      找到.push({ 词: w, x: Math.round(r.x), y: Math.round(r.y),
        w: Math.round(r.width), h: Math.round(r.height) });
      break;
    }
  }
  return 找到;
});

// 数下拉里的画布项
const 数画布 = () => page.evaluate(() => {
  const 名 = new Set();
  for (const e of document.querySelectorAll('*')) {
    if (e.children.length) continue;
    const t = (e.innerText || '').trim();
    if (!/^画布 \d+$|^手册|^示范|^示例/.test(t) || t.length > 20) continue;
    const r = e.getBoundingClientRect();
    if (r.x < 100 || r.x > 500) continue;
    名.add(t);
  }
  return [...名];
});

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(主画布, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(6000);
  await closePromos(page);
  await page.waitForTimeout(4000);

  // ── ① 关抽屉（FY-6 漏了这步）
  记('--- ① 关掉右侧抽屉与通知横幅 ---');
  const 抽屉前 = await page.evaluate(() => document.querySelectorAll('.mantine-Drawer-inner').length);
  const 横幅前 = await page.evaluate(() =>
    [...document.querySelectorAll('*')].filter((e) => !e.children.length && /开启浏览器通知/.test(e.innerText || '')).length);
  记(`  关之前：抽屉 ${抽屉前} 个、通知横幅 ${横幅前} 个`);
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('.mantine-Drawer-inner [aria-label="关闭"], .mantine-Drawer-close')) b.click();
  });
  await page.waitForTimeout(900);
  await page.evaluate(() => {
    for (const e of document.querySelectorAll('[aria-label="关闭"], button')) {
      const p = e.parentElement;
      if (p && /开启浏览器通知/.test(p.innerText || '')) { e.click(); return; }
    }
  });
  await page.waitForTimeout(900);
  const 抽屉后 = await page.evaluate(() => document.querySelectorAll('.mantine-Drawer-inner').length);
  const 横幅后 = await page.evaluate(() =>
    [...document.querySelectorAll('*')].filter((e) => !e.children.length && /开启浏览器通知/.test(e.innerText || '')).length);
  记(`  关之后：抽屉 ${抽屉后} 个、通知横幅 ${横幅后} 个`);
  await page.screenshot({ path: resolve(EVID, 'fz1-1-关掉抽屉之后.png') });

  // ── ② 打开下拉，建前基线
  记('\n--- ② 打开下拉，记建前基线 ---');
  await page.mouse.click(200, 24);
  await page.waitForTimeout(1700);
  const 前 = await 数画布();
  R.读数.建前 = 前;
  记(`  建前下拉里有 ${前.length} 项`);
  await page.screenshot({ path: resolve(EVID, 'fz1-2-下拉开着.png') });

  // ── ③ 找加号，确认它此刻仍然可见且未被挡
  记('\n--- ③ 定位并验「新建画布」按钮 ---');
  const 按钮 = await page.evaluate(() => {
    const bs = [...document.querySelectorAll('[aria-label="新建画布"]')];
    const o = bs.map((b) => {
      const r = b.getBoundingClientRect();
      return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        可见: r.width > 4 && r.y > 0 && r.y < 810,
        disabled: b.disabled || b.getAttribute('aria-disabled') === 'true' };
    });
    return { 全部: o, 共: bs.length };
  });
  R.读数.按钮 = 按钮;
  记(`  全页共 ${按钮.共} 枚「新建画布」按钮：${JSON.stringify(按钮.全部)}`);
  const 可用 = 按钮.全部.find((b) => b.可见);
  if (!可用) { 记('  ⛔ 没有可见的'); }
  else {
    记(`  用第一枚可见的 @${可用.中心.join(',')}`);
    // 遮挡采样：沿按钮中心横向取 3 点
    const 遮 = await page.evaluate(({ x, y }) => {
      const o = [];
      for (const dx of [-6, 0, 6]) {
        const e = document.elementFromPoint(x + dx, y);
        let 属 = null;
        for (let i = 0, p = e; i < 6 && p; i++, p = p.parentElement) {
          if (p.getAttribute && p.getAttribute('aria-label') === '新建画布') { 属 = i; break; }
        }
        o.push({ dx, tag: e?.tagName, 属新建按钮: 属 });
      }
      return o;
    }, { x: 可用.中心[0], y: 可用.中心[1] });
    R.读数.遮挡 = 遮;
    断言('按钮中心 3 个采样点都归它', 遮.every((s) => s.属新建按钮 === 0), JSON.stringify(遮));

    // ── ④ 点
    记('\n--- ④ 点它，并盯三种响应 ---');
    const URL0 = page.url();
    await page.mouse.click(可用.中心[0], 可用.中心[1]);
    await page.waitForTimeout(1200);
    const 即时 = await page.evaluate(() => ({
      弹窗: [...document.querySelectorAll('[role="dialog"]')].map((e) => (e.innerText || '').trim().slice(0, 80)),
      input: [...document.querySelectorAll('input')].map((i) => ({ ph: i.placeholder, v: i.value })).filter((x) => x.ph || x.v),
      下拉还在: document.querySelectorAll('.mantine-ScrollArea-content').length,
    }));
    记(`  点后 1.2 秒：URL 变了吗 ${page.url() !== URL0}；弹窗 ${即时.弹窗.length} 个；输入框 ${JSON.stringify(即时.input)}`);
    await page.screenshot({ path: resolve(EVID, 'fz1-3-点后1秒.png') });

    await page.waitForTimeout(4000);
    const URL1 = page.url();
    记(`  点后 5 秒：${URL1}`);
    const 节点 = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
    记(`  节点数 ${节点}`);
    await page.screenshot({ path: resolve(EVID, 'fz1-4-点后5秒.png') });

    断言('URL 变了（真的建了/切了画布）', URL1 !== URL0, `${URL0.slice(-30)} → ${URL1.slice(-30)}`);

    if (URL1 !== URL0) {
      // 重新开下拉，数画布
      await page.mouse.click(200, 24);
      await page.waitForTimeout(1700);
      const 后 = await 数画布();
      R.读数.建后 = 后;
      记(`  建后下拉里有 ${后.length} 项（建前 ${前.length}）`);
      const 新项 = 后.filter((x) => !前.includes(x));
      记(`  ⭐ 新出现的项：${新项.join(' / ') || '（无）'}`);
      断言('下拉里多了一项', 后.length > 前.length, `${前.length} → ${后.length}`);
      await page.screenshot({ path: resolve(EVID, 'fz1-5-建后下拉.png') });
      await page.keyboard.press('Escape');
      await page.waitForTimeout(800);
    }

    // ── ⑤ 探引导
    记('\n--- ⑤ 探新手引导 ---');
    await closePromos(page);
    await page.waitForTimeout(2500);
    const G = await 探引导();
    R.读数.引导 = G;
    断言('出现引导', G.length > 0, G.length ? G.map((g) => `「${g.词}」@${g.x},${g.y}`).join(' / ') : '0 条');
    if (G.length) await page.screenshot({ path: resolve(EVID, 'fz1-6-引导出现.png') });
  }
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFZ1.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
