// ⭐⭐⭐⭐⭐ Batch FT-5：⭐ **先把右侧那个 TV Director 抽屉关掉**再重拍
//
// FT-4 的三条断言全过、几何也量准了（浮层 `[656,507,658,190]`），
// ⛔ **但截图里浮层右半边被 TV Director 抽屉盖住了** ——
// 那个抽屉是 `mantine-Drawer-inner [1024,154,400,640]`，**本批之前一直开着**。
// 断言只管「框在视口内」，⛔ **不管「有没有被别的浮层遮住」**（缺陷 449 的老问题，
// 这里换了个马甲又出现一次）。
//
// ⭐ 本轮补一条硬判据：拍之前断言
//   `elementFromPoint(浮层几何中心).closest('div').isConnected` 且
//   该点**不在**任何 `.mantine-Drawer-inner` 里 ⇒ 浮层没被遮。
//
// ⛔ 安全边界：抽屉的关闭钮 aria 是「关闭」；⛔ **不点「开启浏览器通知」**、
//   不点「感知画布开始创作」/「从爆款预设开始剧本原创」/「上传故事来改编」/
//   「批量优化提示词」/「全能创作」/「Send」—— 那些会进创作流程或发通知。
import { launch, closePromos, ORIGIN, 断言器, 中心属主 } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const 主画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 证据图: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFT5.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = 断言器(记);

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(主画布, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);

  // ── ① 关掉 TV Director 抽屉
  记('=== ① 关 TV Director 抽屉 ===');
  R.读数.抽屉前 = await page.evaluate(() => {
    const d = document.querySelector('.mantine-Drawer-inner');
    if (!d) return null;
    const r = d.getBoundingClientRect();
    return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] };
  });
  记('   抽屉 ' + JSON.stringify(R.读数.抽屉前));
  const 关 = await page.evaluate(() => {
    const d = document.querySelector('.mantine-Drawer-inner');
    if (!d) return null;
    for (const b of d.querySelectorAll('button,[aria-label]')) {
      const t = (b.getAttribute('aria-label') || '').trim();
      if (t !== '关闭') continue;                 // ⛔ 白名单：只认 aria 恰为「关闭」
      const r = b.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)];
    }
    return null;
  });
  记('   关闭钮落点 ' + JSON.stringify(关));
  断言(!!关, '抽屉上找得到 aria=关闭 的那枚按钮', null);
  if (关) {
    await page.mouse.click(关[0], 关[1]);
    await page.waitForTimeout(2200);
  }
  R.读数.抽屉后 = await page.evaluate(() => !!document.querySelector('.mantine-Drawer-inner'));
  记('   关掉之后抽屉还在吗：' + R.读数.抽屉后);
  断言(!R.读数.抽屉后, '⭐ TV Director 抽屉真的关掉了', R.读数.抽屉后);

  // ── ② 选最靠右的图片节点
  记('=== ② 选最靠右的图片节点 ===');
  const 图节点 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
    .map((n) => { const r = n.getBoundingClientRect(); return { id: n.getAttribute('data-id'), 类: (String(n.className).match(/node-([a-z0-9-]+)/) || [, '?'])[1], 框: [r.x, r.y, r.width, r.height] }; })
    .filter((n) => n.类 === 'image' && n.框[2] > 0)
    .sort((a, b) => b.框[0] - a.框[0]));
  const 目标 = 图节点[0];
  记('   图片节点 ' + JSON.stringify(图节点) + '｜选 ' + 目标.id);
  const t = [Math.round(目标.框[0] + 目标.框[2] / 2), Math.round(目标.框[1] + 14)];
  await page.mouse.click(t[0], t[1]);
  await page.waitForTimeout(3200);
  const a = await 中心属主(page, 目标.id);
  断言(!!a && a.属主 === 目标.id, `${目标.id} 中心落点属主就是它自己`, a);

  // ── ③ 量浮层（最小命中）并**验没被遮**
  记('=== ③ 量浮层 + 验没被遮 ===');
  R.读数.浮层 = await page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ').trim();
    const 命中 = [...document.querySelectorAll('div')].filter((el) => {
      const r = el.getBoundingClientRect();
      if (!(r.width > 200 && r.height > 80)) return false;
      return /^参考\s*标记\s*风格/.test(归(el.innerText));
    });
    if (!命中.length) return null;
    命中.sort((a, b) => { const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect(); return (ra.width * ra.height) - (rb.width * rb.height); });
    const el = 命中[0];
    const r = el.getBoundingClientRect();
    const 壳 = el.closest('.node-floating-ui') || el.parentElement?.parentElement;
    const sr = 壳 ? 壳.getBoundingClientRect() : r;
    return {
      框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      壳框: [Math.round(sr.x), Math.round(sr.y), Math.round(sr.width), Math.round(sr.height)],
      壳class: String(壳?.className || '').slice(0, 200),
      全文: 归(el.innerText).slice(0, 300),
    };
  });
  记('   ⭐ 浮层 ' + JSON.stringify(R.读数.浮层, null, 1));
  断言(!!R.读数.浮层, '找得到编辑区浮层（最小命中）', null);

  // ⭐⭐ 硬判据：沿浮层宽度取 5 个采样点，逐个验落点不在任何抽屉里
  const 遮 = await page.evaluate(({ f }) => {
    const 点 = [];
    for (let i = 1; i <= 5; i++) 点.push([Math.round(f[0] + (f[2] * i) / 6), Math.round(f[1] + f[3] / 2)]);
    return 点.map(([x, y]) => {
      const el = document.elementFromPoint(x, y);
      if (!el) return { x, y, 命中: null, 在抽屉内: false };
      const d = el.closest('.mantine-Drawer-inner');
      return { x, y, 命中类: String(el.className || '').slice(0, 40), 在抽屉内: !!d };
    });
  }, { f: R.读数.浮层.框 });
  R.读数.遮 = 遮;
  记('   ⭐ 沿浮层取 5 个采样点：' + JSON.stringify(遮));
  断言(遮.every((p) => p.命中 && !p.在抽屉内), '⭐ 浮层上 5 个采样点全部没被抽屉遮住', 遮);

  const 壳 = R.读数.浮层.壳框;
  const clip = { x: Math.max(0, 壳[0] - 18), y: Math.max(0, 壳[1] - 18), width: Math.min(1440 - Math.max(0, 壳[0] - 18), 壳[2] + 36), height: Math.min(810 - Math.max(0, 壳[1] - 18), 壳[3] + 36) };
  await page.screenshot({ path: resolve(EVID, 'ft5-0-图片编辑区浮层-无抽屉.png'), clip });
  R.证据图.push({ 文件: 'ft5-0-图片编辑区浮层-无抽屉.png', clip });
  记(`   📷 ft5-0-图片编辑区浮层-无抽屉.png｜壳 ${JSON.stringify(壳)}｜裁剪 ${JSON.stringify(clip)}`);

  记(`断言统计 ${JSON.stringify(断言.统计)}`);
  R.读数.断言 = 断言.统计;
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFT5.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
