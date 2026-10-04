// Batch EI-1：验「转分镜组」到底可不可用 —— ⭐ 旧结论说它「灰的、点了什么也不会发生」。
//
// 源码查清（3-mou5v69wxmq.js）：
//   lM = lR.length >= 2 && lR.length <= 25 && lR.every(e => e.type === IMAGE)
//   canStoryboardGroup: lM，storyboardGroupDisabledReason: "分镜组仅支持图片节点，且组内节点数量不可超过 25 个"
// ⇒ 判据是「选中 **2～25 个**、**全部是图片节点**」
//
// ⭐ 基线画布正好有 2 个图片节点（i-9nlG6HdjK2 / i-sODTbgLUm1）⇒ **满足条件**
//    所以旧结论「它永远是灰的」很可能是**在没满足条件时测的**。
//
// ⭐ 判据用 §289 的方法：量**内部结构**（disabled 属性 / class / opacity），
//    不只看颜色；并且**分三组对照**：
//      ① 选中 2 个图片节点   （应可用）
//      ② 选中 2 个非图片节点 （应灰）
//      ③ 选中 1 个节点       （数量不足，应灰）
//
// ⛔ 不点「转分镜组」本身（它会真的转换组，改画布结构）—— 只读它的可用状态。
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { BASE } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const OUT = new URL('./batchEI1.json', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

/** ⭐ 读组操作条上「转分镜组」按钮的完整可用状态。 */
const 读转分镜组 = (page) => page.evaluate(() => {
  const 全部 = [...document.querySelectorAll('button')];
  const btn = 全部.find(b => /转分镜组|合并分镜组/.test((b.innerText || '').trim()));
  if (!btn) return { 找到: false };
  const cs = getComputedStyle(btn);
  return {
    找到: true,
    文字: btn.innerText.trim(),
    disabled: btn.disabled,
    ariaDisabled: btn.getAttribute('aria-disabled'),
    opacity: cs.opacity,
    cursor: cs.cursor,
    pointerEvents: cs.pointerEvents,
    背景: cs.backgroundColor,
    box: (() => { const r = btn.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; })(),
    title: btn.getAttribute('title') || '',
    className: btn.className.toString().slice(0, 120),
  };
});

const 选节点 = async (page, ids) => {
  // ⭐ 先点空白清空选择，再逐个点选（避免框选）
  await page.mouse.click(60, 700);
  await page.waitForTimeout(700);
  for (const [k, id] of ids.entries()) {
    const p = await page.evaluate((i) => {
      const el = document.querySelector(`.react-flow__node[data-id="${i}"]`);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return [r.left + r.width / 2, r.top + 20];
    }, id);
    if (!p) { 记(`节点 ${id} 不在视口内`); continue; }
    if (k > 0) await page.keyboard.down('Shift');   // ⭐ 累加多选
    await page.mouse.click(p[0], p[1]);
    if (k > 0) await page.keyboard.up('Shift');
    await page.waitForTimeout(700);
  }
  await page.waitForTimeout(1000);
  const 选中 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node.selected')].map(n => n.getAttribute('data-id')));
  return 选中;
};

const { browser, page } = await launch();
try {
  await open(page, CANVAS_URL, { settle: 6500 });
  await closePromos(page);
  await page.waitForTimeout(1200);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(1500);

  const 节点 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map(n => ({
    id: n.getAttribute('data-id'),
    cls: n.className.toString().split(' ').filter(c => c.startsWith('react-flow__node-')).join(','),
  })));
  结果.读数.节点 = 节点;
  const 图片 = 节点.filter(n => n.cls === 'react-flow__node-image').map(n => n.id);
  const 非图片 = 节点.filter(n => n.cls !== 'react-flow__node-image').map(n => n.id);
  记(`图片节点 ${图片.length} 个：${JSON.stringify(图片)}`);
  记(`非图片节点 ${非图片.length} 个：${JSON.stringify(非图片)}`);

  // ① 选中 2 个图片节点 —— 源码判据说应该「可用」
  let s = await 选节点(page, 图片.slice(0, 2));
  记(`① 选中 2 个图片节点 → 实际选中 ${JSON.stringify(s)}`);
  let r = await 读转分镜组(page);
  结果.读数.两个图片 = r;
  记(`   「转分镜组」：${JSON.stringify(r)}`);

  // ② 选中 2 个非图片节点 —— 应当灰
  await page.mouse.click(60, 700);
  await page.waitForTimeout(700);
  s = await 选节点(page, 非图片.slice(0, 2));
  记(`② 选中 2 个非图片节点 → 实际选中 ${JSON.stringify(s)}`);
  r = await 读转分镜组(page);
  结果.读数.两个非图片 = r;
  记(`   「转分镜组」：${JSON.stringify(r)}`);

  // ③ 只选 1 个图片节点 —— 数量不足，应当灰
  s = await 选节点(page, 图片.slice(0, 1));
  记(`③ 选中 1 个图片节点 → 实际选中 ${JSON.stringify(s)}`);
  r = await 读转分镜组(page);
  结果.读数.一个图片 = r;
  记(`   「转分镜组」：${JSON.stringify(r)}`);

  // ⭐⭐ 对照：把「转分镜组」和另一个**已知可用**的按钮（解组/颜色圆点）比，
  //    确认这套读数有区分力
  if (图片.length >= 2) {
    s = await 选节点(page, 图片.slice(0, 2));
    const 对照 = await page.evaluate(() => {
      const out = [];
      for (const b of document.querySelectorAll('button')) {
        const t = (b.innerText || '').trim();
        if (!t || t.length > 8) continue;
        const cs = getComputedStyle(b);
        if (cs.opacity === '0') continue;
        out.push({ 文字: t, disabled: b.disabled, opacity: cs.opacity, cursor: cs.cursor });
      }
      return out.slice(0, 14);
    });
    结果.读数.同排按钮 = 对照;
    记(`⭐ 阳性对照：选中 2 个图片节点时，操作条上所有按钮的可用状态：`);
    for (const c of 对照) console.log(`     「${c.文字}」disabled=${c.disabled} opacity=${c.opacity} cursor=${c.cursor}`);
  }
  await page.mouse.click(60, 700);
  await page.waitForTimeout(800);
  落盘(结果);
} catch (e) {
  结果.错误 = String(e && e.stack || e);
  console.error('❌', e);
} finally {
  落盘(结果);
  await browser.close();
  console.log('\n=== 已写 tools/batchEI1.json ===');
}
