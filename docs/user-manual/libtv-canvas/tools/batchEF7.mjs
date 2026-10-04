// Batch EF-7：⭐ 风格已应用（大编辑器里出现了「替换」按钮），这轮去**风格选择器**里找徽标。
//
// EF-6 的两处修正：
//   ① 「风格」按钮点不动了 —— 节点已有风格时它改名成「**替换**」，这本身就是个新读数；
//   ② 关 TV Director 时用「点第 N 个图标按钮」太宽泛（点到 13 个），改成精确定位它的关闭图标。
//
// ⭐ 本步目标：打开风格选择器 → 找到那枚「白底 ✓ 当前使用」胶囊 → 读它的全部读数。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEF7.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };
const 目标ID = 'i-sODTbgLUm1';

/** 广场/选择器里所有近白底的叶子元素。 */
const 找白底 = (page) => page.evaluate(() => {
  const 面板 = [...document.querySelectorAll('.mantine-Modal-content, .mantine-Drawer-content, .mantine-Popover-dropdown')]
    .filter(e => { const r = e.getBoundingClientRect(); return r.width > 300 && r.height > 200; })
    .sort((a, b) => b.getBoundingClientRect().width - a.getBoundingClientRect().width)[0];
  if (!面板) return { 开着: false };
  const out = [];
  for (const e of 面板.querySelectorAll('div,span')) {
    if (e.children.length > 0) continue;
    const cs = getComputedStyle(e);
    const m = cs.backgroundColor.match(/rgba?\((\d+), (\d+), (\d+)/);
    if (!m) continue;
    if (!(+m[1] > 240 && +m[2] > 240 && +m[3] > 240)) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 25 || r.width > 220 || r.height > 44) continue;
    const 卡 = e.closest('[class*="group"]');
    out.push({
      文本: (e.innerText || '').trim(),
      bg: cs.backgroundColor, 色: cs.color, 字号: cs.fontSize, 圆角: cs.borderRadius,
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      svg数: e.querySelectorAll('svg').length,
      卡首行: (卡?.innerText || '').split('\n').filter(Boolean).slice(0, 3).join(' / '),
      className: e.className.toString().slice(0, 120),
      html: e.outerHTML.slice(0, 280),
    });
  }
  const pr = 面板.getBoundingClientRect();
  return { 开着: true, 面板box: [Math.round(pr.left), Math.round(pr.top), Math.round(pr.width), Math.round(pr.height)], 白底: out };
});

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
  await closePromos(page);
  await page.waitForTimeout(1000);
  await page.evaluate(() => { for (const b of document.querySelectorAll('button')) if ((b.innerText || '').trim() === '知道了') { b.click(); return; } });
  await page.waitForTimeout(600);

  // 选节点
  const 框 = await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!n) return null; const r = n.getBoundingClientRect(); return [r.left, r.top, r.width, r.height];
  }, 目标ID);
  await page.mouse.click(框[0] + 框[2] / 2, 框[1] + 框[3] / 2);
  await page.waitForTimeout(1400);

  // ⭐ 读大编辑器顶部那排按钮，确认「替换」还在
  const 顶排 = await page.evaluate(() => {
    const bs = [...document.querySelectorAll('button')].map(b => {
      const t = (b.innerText || '').trim();
      if (!['参考', '标记', '风格', '替换', '特效', '角色库', '运镜', '风格设置'].includes(t)) return null;
      const r = b.getBoundingClientRect();
      return { 文案: t, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
    }).filter(Boolean);
    return bs;
  });
  结果.读数.顶排按钮 = 顶排;
  记(`顶排按钮：${JSON.stringify(顶排.map(b => b.文案))}`);

  // ⭐ 点「替换」（不是「风格」）
  const 点了 = await page.evaluate(() => {
    for (const 文 of ['替换', '风格']) {
      const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === 文);
      if (b) { b.click(); return 文; }
    }
    return false;
  });
  记(`点了按钮：${点了}`);
  await page.waitForTimeout(2600);

  const 读 = await 找白底(page);
  结果.读数.面板 = 读;
  记(`面板开着=${读.开着}，近白底元素 ${(读.白底 || []).length} 个`);
  for (const m of (读.白底 || [])) {
    console.log(`  「${m.文本}」 bg=${m.bg} 字号=${m.字号} 圆角=${m.圆角} box=${JSON.stringify(m.box)} svg=${m.svg数}`);
    console.log(`     卡=${m.卡首行.slice(0, 46)}`);
  }
  落盘(结果);
  await page.screenshot({ path: '.evidence/batchEF7-风格选择器里的白底徽标.png' });

  // ⭐ 阳性对照：面板开着的时候，随便找几个近黑底的徽标（模型徽标），证明白底筛选有区分力
  const 对照 = await page.evaluate(() => {
    const 面板 = [...document.querySelectorAll('.mantine-Modal-content, .mantine-Drawer-content')]
      .filter(e => { const r = e.getBoundingClientRect(); return r.width > 300 && r.height > 200; })[0];
    if (!面板) return null;
    const out = [];
    for (const e of 面板.querySelectorAll('div,span')) {
      if (e.children.length > 0) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 25 || r.width > 220 || r.height > 44) continue;
      const cs = getComputedStyle(e);
      const t = (e.innerText || '').trim();
      if (!t) continue;
      out.push({ 文本: t.slice(0, 16), bg: cs.backgroundColor, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
    }
    return out.slice(0, 14);
  });
  结果.读数.阳性对照 = 对照;
  console.log('\n═══ 阳性对照：面板里所有小徽标 ═══');
  for (const c of (对照 || [])) console.log(`  「${c.文本}」 bg=${c.bg} box=${JSON.stringify(c.box)}`);
  落盘(结果);
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEF7.json ===');
}
