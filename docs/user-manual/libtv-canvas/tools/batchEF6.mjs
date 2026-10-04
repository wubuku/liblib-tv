// Batch EF-6：⭐ 「当前使用」徽标 —— 上一轮已把风格应用到节点上（截图可见大编辑器里
// 出现了风格缩略图），但广场被 TV Director 抽屉挡住、没真正打开，所以读数是 0。
//
// 本步修正三件事：
//   ① 先关掉 TV Director 抽屉（再点一次它那枚触发图标 —— 手册 AUDIT.md:84 记着 Esc 不管用）；
//   ② 关掉「Agent 已升级」促销弹窗（点「知道了」）；
//   ③ 再开风格广场，然后按**白底胶囊**找徽标。
//
// ⭐ 判据不用文字搜（SSR 注水数据里也有「当前使用」，EF-1b 已证明是假阳性），
//    改找**白底 + 黑字**的胶囊元素，并要求它在广场卡面里。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEF6.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 目标ID = 'i-sODTbgLUm1';

/** ⭐ 按「白底胶囊」找徽标 —— 不搜文字，避免 SSR 注水的假阳性。 */
const 找白底徽标 = (page) => page.evaluate(() => {
  const 广场 = [...document.querySelectorAll('.mantine-Modal-content, .mantine-Drawer-content')]
    .find(e => /风格广场|我的收藏|最近使用/.test(e.innerText || ''));
  if (!广场) return { 广场开着: false };

  const out = [];
  // 广场里所有「白底（接近纯白）且带文字」的小元素
  for (const e of 广场.querySelectorAll('div,span')) {
    if (e.children.length > 0 && e.tagName === 'DIV') continue;   // 只要叶子容器
    const cs = getComputedStyle(e);
    const bg = cs.backgroundColor;
    const m = bg.match(/rgba?\((\d+), (\d+), (\d+)/);
    if (!m) continue;
    const [r, g, b] = [+m[1], +m[2], +m[3]];
    if (!(r > 240 && g > 240 && b > 240)) continue;   // ⭐ 只要近白底
    const rect = e.getBoundingClientRect();
    if (rect.width < 30 || rect.width > 200 || rect.height > 40) continue;
    const txt = (e.innerText || '').trim();
    const 卡 = e.closest('[class*="group"]');
    out.push({
      文本: txt,
      bg, 色: cs.color, 字号: cs.fontSize,
      box: [Math.round(rect.left), Math.round(rect.top), Math.round(rect.width), Math.round(rect.height)],
      圆角: cs.borderRadius,
      svg数: e.querySelectorAll('svg').length,
      所在卡首行: (卡?.innerText || '').split('\n').filter(Boolean).slice(0, 3).join(' / '),
      className: e.className.toString().slice(0, 110),
      html: e.outerHTML.slice(0, 260),
    });
  }
  return { 广场开着: true, 广场box: (() => { const r = 广场.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; })(), 白底元素: out };
});

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
  await closePromos(page);
  await page.waitForTimeout(1200);

  // ── ① 关掉促销弹窗（点「知道了」）──
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('button')) {
      if ((b.innerText || '').trim() === '知道了') { b.click(); return; }
    }
  });
  await page.waitForTimeout(700);

  // ── ② 关掉 TV Director 抽屉：再点一次它的触发图标（Esc 不管用）──
  const 关抽屉 = await page.evaluate(() => {
    // 抽屉容器
    const 抽屉 = document.querySelector('.mantine-Drawer-content');
    if (!抽屉) return { 原来: '没有抽屉' };
    const r = 抽屉.getBoundingClientRect();
    // 抽屉标题栏里那几枚图标按钮
    const btns = [...抽屉.querySelectorAll('button')].filter(b => {
      const br = b.getBoundingClientRect();
      return br.width >= 20 && br.width <= 40 && br.height >= 20 && br.height <= 40 && !b.innerText.trim();
    });
    if (btns.length) { btns[btns.length - 1].click(); return { 点了几: btns.length }; }
    return { 点了几: 0 };
  });
  记(`关 TV Director 抽屉：${JSON.stringify(关抽屉)}`);
  await page.waitForTimeout(1200);

  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1500);

  // ── ③ 确认节点上还挂着那个风格（读大编辑器）──
  const 框 = await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    return [r.left, r.top, r.width, r.height];
  }, 目标ID);
  await page.mouse.click(框[0] + 框[2] / 2, 框[1] + 框[3] / 2);
  await page.waitForTimeout(1300);

  const 编辑器 = await page.evaluate(() => {
    const 面板 = [...document.querySelectorAll('div')].find(e => {
      const r = e.getBoundingClientRect();
      return r.width > 400 && r.height > 300 && /Lib Image|风格|参考/.test(e.innerText || '') && e.children.length < 40;
    });
    return 面板 ? (面板.innerText || '').slice(0, 200) : null;
  });
  结果.读数.大编辑器 = 编辑器;
  记(`大编辑器片段：${JSON.stringify(编辑器)}`);

  // ── ④ 开风格广场 ──
  const 开了 = await page.evaluate(() => {
    const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === '风格');
    if (!b) return false; b.click(); return true;
  });
  await page.waitForTimeout(2500);
  记(`点「风格」：${开了}`);

  // ── ⑤ ⭐ 读白底徽标 ──
  const 读数 = await 找白底徽标(page);
  结果.读数.广场 = 读数;
  记(`广场开着=${读数.广场开着}，白底元素 ${(读数.白底元素 || []).length} 个`);
  for (const m of (读数.白底元素 || [])) {
    console.log(`  「${m.文本}」 bg=${m.bg} 字号=${m.字号} box=${JSON.stringify(m.box)} svg=${m.svg数} 卡=${m.所在卡首行.slice(0, 30)}`);
  }
  await page.screenshot({ path: '.evidence/batchEF6-广场里的白底徽标.png' });
  落盘(结果);

  // ── ⑥ ⭐ 对照：把鼠标移到卡上悬停，看徽标是否只在悬停时出现 ──
  const 卡 = 读数.白底元素?.[0];
  if (卡) {
    const 卡中心 = [卡.box[0] + 20, 卡.box[1] + 60];
    await page.mouse.move(卡中心[0], 卡中心[1]);
    await page.waitForTimeout(900);
    const 悬停后 = await 找白底徽标(page);
    结果.读数.悬停后 = 悬停后;
    记(`悬停后白底元素 ${(悬停后.白底元素 || []).length} 个`);
    落盘(结果);
  }
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEF6.json ===');
}
