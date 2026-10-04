// Batch EW-9：⭐⭐⭐ 直接问「角色库」本人。
//
// EW-8 的截图把气泡放大了 4 倍，看得清清楚楚：
//   气泡底部有一个**小三角指针（▼）**，落点正好在参数面板顶排
//   `特效` / `角色库` / `运镜` 那一行的 **`角色库` 正上方**。
//
// 但这和 EW-5 的读数有矛盾：EW-5 扫全视口时，指针在**顶栏 y=30 一整排**它都在，
//   根本没碰到 `角色库`。⇒ 要么它被「卡在打开态」，要么它压根不是 `角色库` 的悬停气泡。
//
// 本轮一次问清：
//   ① 选中视频节点 → 它在不在
//   ② 指针移到 `角色库` 上 → 文案是什么
//   ③ 指针**移开**（放到空画布）→ 它还在不在  ⭐ 这条决定它是不是悬停气泡
//   ④ 依次悬停 `特效` / `运镜` / `参考` / `标记` → 各自的文案
import { launch, open, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchEW9.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

/** 读此刻所有真显示着的 Mantine 气泡 */
const 读气泡 = (page) => page.evaluate(() => {
  const 出 = [];
  for (const e of document.querySelectorAll('[class*="mantine-Tooltip-tooltip"]')) {
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    if (r.width < 4 || r.height < 4) continue;
    if (parseFloat(cs.opacity) < 0.5) continue;
    出.push({ 文字: (e.innerText || '').trim().slice(0, 30), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] });
  }
  return 出;
});

/** 按可见文字找一枚控件的中心（找**控件**本身，不是它的子 span） */
const 找按钮 = (page, 文) => page.evaluate((t) => {
  for (const e of document.querySelectorAll('button,[role="button"]')) {
    if ((e.innerText || '').trim() !== t) continue;
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) continue;
    return { box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
  }
  return null;
}, 文);

try {
  await open(page, CANVAS_URL);
  await closePromos(page);
  await page.waitForTimeout(4000);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(2500);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  // ① 选中视频节点 3
  const p = await page.evaluate(() => {
    const el = document.querySelector('.react-flow__node[data-id="v-v2hlWY4Br3"]');
    const r = el.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + 14)];
  });
  const 验 = await page.evaluate(([x, y]) => {
    const n = document.elementFromPoint(x, y)?.closest('.react-flow__node');
    return n ? n.getAttribute('data-id') : null;
  }, p);
  记('落点自证=' + 验);
  await page.mouse.click(p[0], p[1]);
  await page.waitForTimeout(2500);

  // 指针先放到空画布（远离一切控件）
  await page.mouse.move(120, 400);
  await page.waitForTimeout(1200);
  const S1 = await 读气泡(page);
  记('[1] 指针在空画布(120,400)｜气泡=' + S1);
  结果.读数['1_空画布'] = S1;

  // ② 悬停「角色库」
  const RB = await 找按钮(page, '角色库');
  记('角色库按钮：' + JSON.stringify(RB));
  if (RB) {
    await page.mouse.move(RB.中心[0], RB.中心[1]);
    await page.waitForTimeout(1400);
    const S2 = await 读气泡(page);
    记('[2] 悬停角色库｜气泡=' + S2);
    结果.读数['2_悬停角色库'] = S2;
    await page.screenshot({ path: EVID + 'ew9-悬停角色库.png', clip: { x: 380, y: 190, width: 460, height: 110 } });
    记('已拍 ew9-悬停角色库.png');

    // ③ ⭐ 指针移开 —— 它还在不在
    await page.mouse.move(120, 400);
    await page.waitForTimeout(1500);
    const S3 = await 读气泡(page);
    记('[3] 指针移回空画布｜气泡=' + S3);
    结果.读数['3_移开后'] = S3;
  }

  // ④ 依次悬停那一排的其它按钮
  for (const 文 of ['特效', '运镜', '参考', '标记']) {
    const b = await 找按钮(page, 文);
    if (!b) { 记(`   ${文}：按钮没找到`); continue; }
    await page.mouse.move(b.中心[0], b.中心[1]);
    await page.waitForTimeout(1200);
    const g = await 读气泡(page);
    记(`   悬停 ${文}｜气泡=${JSON.stringify(g)}`);
    (结果.读数['④_逐个'] ||= {})[文] = { 按钮: b.box, 气泡: g };
  }

  // ⑤ 悬停完最后一个，指针停在空画布 —— 再看一次
  await page.mouse.move(120, 400);
  await page.waitForTimeout(1500);
  const S5 = await 读气泡(page);
  记('[5] 全部悬停完、指针回空画布｜气泡=' + S5);
  结果.读数['5_收尾'] = S5;

  await page.mouse.click(40, 700);
  await page.waitForTimeout(1200);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后坐标复核：' + JSON.stringify(偏差));
  结果.收尾 = { 偏差, 已渲染: Object.keys(await 读全部坐标(page)).length };
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  落盘(结果);
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchEW9.json ===');
}
