// ⭐⭐⭐ 复原 v4：画布已损坏，用产品自带的「整理画布」救回来
//
// 损坏成因（全部是本轮自己造成的，如实记录）：
//   restore-v2 第 3 轮要拖 −1465 屏 px（≈ −3194 画布单位），那是**发散**不是复原；
//   节点被拖到离原点 3 万个单位以外 ⇒ `⌘0` 的 fit view 把范围撑到极大
//   ⇒ **zoom 被压到 0.1，11 个节点一个都不渲染**，`⌘0` / `⌘1` / `⌘2` 全部无效。
//
// 恢复手段只用产品自己的功能：**左下角「整理画布」**。
// 它会把所有节点重新排布，正好把跑飞的节点拉回可读范围；
// 弹窗里的「保留」才会落盘，「还原」会退回现在这个坏状态 —— 所以点「保留」。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'restore-v4.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;
const 快照 = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const o = { viewport: v ? getComputedStyle(v).transform : null, 节点: {} };
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
    o.节点[n.getAttribute('data-id')] = t ? [Number(t[1]), Number(t[2])] : n.style.transform;
  }
  o.数 = Object.keys(o.节点).length;
  return o;
});
/** 找一枚按钮：优先按 aria，其次按 left 坐标 */
const 找按钮 = (关键字, 兜底left) => page.evaluate(([kw, lf]) => {
  let b = null;
  for (const x of document.querySelectorAll('button')) {
    const r = x.getBoundingClientRect();
    if (r.top < 740 || r.bottom > 810) continue;
    if ((x.getAttribute('aria-label') || '').includes(kw)) { b = x; break; }
  }
  if (!b && lf != null) {
    for (const x of document.querySelectorAll('button')) {
      const r = x.getBoundingClientRect();
      if (r.top < 740 || r.bottom > 810) continue;
      if (Math.abs(r.left - lf) < 20) { b = x; break; }
    }
  }
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return { aria: b.getAttribute('aria-label'), 文字: (b.innerText || '').trim().slice(0, 30), 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
}, [关键字, 兜底left ?? null]);

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(12000);
  await closePromos(page);
  await page.waitForTimeout(2000);
  const a = await 快照();
  记(`损坏态：viewport = ${a.viewport}｜渲染 ${a.数} 个节点`);
  for (const [id, xy] of Object.entries(坐标)) 记(`   ${id} 基线${JSON.stringify(xy)} 渲染${JSON.stringify(a.节点[id] || '未渲染')}`);
  await page.screenshot({ path: EVID + 'fb13-01-损坏态.png' });
  R.读数.损坏态 = a;

  // 点「整理画布」
  const btn = await 找按钮('整理画布', 112);
  记('整理画布按钮 = ' + JSON.stringify(btn));
  if (!btn) throw new Error('底栏找不到整理画布');
  await page.mouse.move(btn.中心[0], btn.中心[1]); await page.waitForTimeout(420);
  const v = await page.evaluate((p) => {
    const e = document.elementFromPoint(p[0], p[1]);
    const n = e ? e.closest('button') : null;
    return n ? (n.getAttribute('aria-label') || n.innerText || '').trim().slice(0, 30) : 'null';
  }, btn.中心);
  记('  自证落点 = ' + JSON.stringify(v));
  if (!/整理画布/.test(v)) throw new Error('落点不是整理画布，中止');
  await page.mouse.down(); await page.mouse.up();
  await page.waitForTimeout(4000);
  await page.mouse.move(720, 200); await page.waitForTimeout(800);

  const b = await 快照();
  记(`整理后（未点保留）：viewport = ${b.viewport}｜渲染 ${b.数} 个节点`);
  for (const [id, xy] of Object.entries(b.节点)) 记(`   ${id} 整理到 ${JSON.stringify(xy)}`);
  await page.screenshot({ path: EVID + 'fb13-02-整理后.png' });
  R.读数.整理后 = b;

  // 找弹窗里的「保留」
  const dlg = await page.evaluate(() => {
    const out = [];
    for (const x of document.querySelectorAll('button')) {
      const t = (x.innerText || '').trim();
      if (!t) continue;
      const r = x.getBoundingClientRect();
      if (r.top > 810 || r.bottom < 0) continue;
      out.push({ 文字: t.slice(0, 20), 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
    }
    return out;
  });
  记('当前可见按钮：' + JSON.stringify(dlg));
  R.读数.按钮 = dlg;
  const 保留 = dlg.find((d) => /保留/.test(d.文字));
  if (保留) {
    记('点「保留」' + JSON.stringify(保留));
    await page.mouse.move(保留.中心[0], 保留.中心[1]); await page.waitForTimeout(380);
    await page.mouse.down(); await page.mouse.up();
    await page.waitForTimeout(4000);
    await page.mouse.move(720, 200); await page.waitForTimeout(800);
  } else {
    记('⛔ 没找到「保留」按钮');
  }
  const c = await 快照();
  记(`点保留后：viewport = ${c.viewport}｜渲染 ${c.数} 个节点`);
  for (const [id, xy] of Object.entries(c.节点)) 记(`   ${id} = ${JSON.stringify(xy)}`);
  await page.screenshot({ path: EVID + 'fb13-03-点保留后.png' });
  R.读数.保留后 = c;
  R.新基线 = c.节点;
} catch (e) {
  R.错误 = String((e && e.stack) || e);
  记('❌ ' + e.message);
} finally {
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const d = await 快照();
  记(`⭐⭐ 静置 15s 后：viewport = ${d.viewport}｜渲染 ${d.数} 个节点`);
  for (const [id, xy] of Object.entries(d.节点)) 记(`   ${id} = ${JSON.stringify(xy)}`);
  R.收尾 = d;
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/restore-v4.json ===');
}
