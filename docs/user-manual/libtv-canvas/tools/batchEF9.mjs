// Batch EF-9：EF-8 定位到大编辑器的真实 box（647,490,658,246），
//   里面写着「参考 | 标记 | 风格 | 替换」—— 「风格/替换」**不是 <button>**，
//   所以前几轮用 querySelectorAll('button') 一直找不到它们。
//
// 本步：在那个大编辑器容器内，**按可见文字**点「替换」（或「风格」），再找白底徽标。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEF9.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));

const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };
const 目标ID = 'i-sODTbgLUm1';

/** ⭐ 找近白底的叶子元素（徽标候选）。 */
const 找白底 = (page) => page.evaluate(() => {
  const out = [];
  for (const e of document.querySelectorAll('div,span')) {
    if (e.children.length > 0) continue;
    const cs = getComputedStyle(e);
    const m = cs.backgroundColor.match(/rgba?\((\d+), (\d+), (\d+)/);
    if (!m) continue;
    if (!(+m[1] > 240 && +m[2] > 240 && +m[3] > 240)) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 25 || r.width > 240 || r.height > 46) continue;
    const 卡 = e.closest('[class*="group"]');
    out.push({
      文本: (e.innerText || '').trim(),
      bg: cs.backgroundColor, 色: cs.color, 字号: cs.fontSize, 圆角: cs.borderRadius,
      box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      svg数: e.querySelectorAll('svg').length,
      卡首行: (卡?.innerText || '').split('\n').filter(Boolean).slice(0, 3).join(' / '),
      className: e.className.toString().slice(0, 130),
      html: e.outerHTML.slice(0, 300),
    });
  }
  return out;
});

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
  await closePromos(page);
  await page.waitForTimeout(1200);
  await page.evaluate(() => { for (const b of document.querySelectorAll('button')) if ((b.innerText || '').trim() === '知道了') { b.click(); return; } });
  await page.waitForTimeout(600);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1500);

  // 选中节点（点标题）
  const 标题 = await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    const t = [...n.querySelectorAll('*')].find(e => /图片节点/.test(e.innerText || '') && e.children.length === 0);
    const r = (t || n).getBoundingClientRect();
    return [r.left + r.width / 2, r.top + r.height / 2];
  }, 目标ID);
  await page.mouse.click(标题[0], 标题[1]);
  await page.waitForTimeout(1600);

  // ⭐ 在大编辑器里按文字点「替换」或「风格」（不限标签）
  const 点了 = await page.evaluate(() => {
    const 编辑器 = [...document.querySelectorAll('div')].find(e => {
      const r = e.getBoundingClientRect();
      if (r.width < 250 || r.height < 150) return false;
      const t = e.innerText || '';
      if (!/参考/.test(t) || !/Lib Image/.test(t)) return false;
      for (const c of e.children) {
        const cr = c.getBoundingClientRect();
        if (cr.width >= 250 && cr.height >= 150 && /参考/.test(c.innerText || '') && /Lib Image/.test(c.innerText || '')) return false;
      }
      return true;
    });
    if (!编辑器) return { 错: '没找到大编辑器' };
    for (const 文 of ['替换', '风格']) {
      const el = [...编辑器.querySelectorAll('*')].find(e => {
        if (e.children.length > 0) return false;
        return (e.innerText || '').trim() === 文;
      });
      if (el) { el.click(); return { 点了: 文, tag: el.tagName, cls: el.className.toString().slice(0, 70) }; }
    }
    return { 错: '编辑器里没找到「替换」或「风格」文字节点', 全部: [...编辑器.querySelectorAll('*')].filter(e => e.children.length === 0).map(e => (e.innerText || '').trim()).filter(Boolean).slice(0, 20) };
  });
  记(`点按钮结果：${JSON.stringify(点了)}`);
  结果.读数.点按钮 = 点了;
  落盘(结果);

  await page.waitForTimeout(2800);

  // ⭐ 找徽标
  const 白底 = await 找白底(page);
  结果.读数.白底 = 白底;
  记(`近白底元素：${白底.length} 个`);
  for (const m of 白底) {
    console.log(`  「${m.文本}」 bg=${m.bg} 字号=${m.字号} 圆角=${m.圆角} box=${JSON.stringify(m.box)} svg=${m.svg数}`);
    console.log(`     卡=${m.卡首行.slice(0, 50)}`);
  }
  await page.screenshot({ path: '.evidence/batchEF9-找当前使用徽标.png' });
  落盘(结果);

  // ⭐ 阳性对照：把「非白底的小徽标」也列出来（模型徽标长什么样）
  const 徽标们 = await page.evaluate(() => {
    const out = [];
    for (const e of document.querySelectorAll('div,span')) {
      if (e.children.length > 0) continue;
      const r = e.getBoundingClientRect();
      if (r.width < 25 || r.width > 240 || r.height > 46) continue;
      const cs = getComputedStyle(e);
      const t = (e.innerText || '').trim();
      if (!t) continue;
      out.push({ 文本: t.slice(0, 18), bg: cs.backgroundColor, 色: cs.color, box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
    }
    return out.slice(0, 20);
  });
  结果.读数.阳性对照 = 徽标们;
  console.log('\n═══ 阳性对照：页面上所有小徽标 ═══');
  for (const c of 徽标们) console.log(`  「${c.文本}」 bg=${c.bg} 色=${c.色} box=${JSON.stringify(c.box)}`);
  落盘(结果);
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEF9.json ===');
}
