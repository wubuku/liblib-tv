// ⭐⭐⭐⭐⭐ 紧急复原：把 FV-6 误触的「整理画布」撤回去
//
// 事故经过（写下来当反面教材）：
//   FV-6 想点底栏第一枚 `+`（添加节点），但筛选条件是
//   「y ≥ 760 且尺寸 34×34 且 innerText 为空且含 svg」——
//   **底栏七枚按钮全都满足**，`querySelectorAll` 取第一个
//   ⇒ 点到了第二枚（✈ 整理画布），画布被重排，
//   左下弹出「是否保留此次整理结果？还原 / 保留」。
//
// ⛔ 本脚本只点「还原」这一个按钮（= 规程允许的「一步复原」），
//    绝不点「保留」，绝不碰 Delete / Backspace。
//
// 复原判据（自证）：
//   ① 「是否保留此次整理结果」这段文案消失
//   ② 缩放回到事故前的 48%
//   ③ 12 个节点的 id 集合与事故前完全一致
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFV7.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = (名, 过, 明) => { R.断言.push({ 名, 过, 明 }); 记(`${过 ? '✅' : '❌'} ${名} —— ${明}`); };

const 状态 = () => page.evaluate(() => ({
  确认框: [...document.querySelectorAll('*')].some((e) => /是否保留此次整理结果/.test(e.innerText || '') && e.children.length === 0),
  还原按钮: (() => {
    for (const e of document.querySelectorAll('button, [role="button"], div')) {
      if (e.children.length) continue;
      if ((e.innerText || '').trim() !== '还原') continue;
      const r = e.getBoundingClientRect();
      if (r.width < 10) continue;
      return { x: Math.round(r.x), y: Math.round(r.y), 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)] };
    }
    return null;
  })(),
  缩放: (() => {
    const m = [...document.querySelectorAll('*')].find((e) => /^\d+%$/.test((e.innerText || '').trim()) && e.children.length === 0);
    return m ? m.innerText.trim() : '';
  })(),
  节点: [...document.querySelectorAll('.react-flow__node')].map((e) => (e.getAttribute('data-id') || '').trim()).sort(),
  画布按钮: (() => {
    // 底栏七枚按钮逐枚实名（位置 + 中心），供下次避开
    const out = [];
    for (const b of document.querySelectorAll('button, [role="button"]')) {
      const r = b.getBoundingClientRect();
      if (r.y < 730 || r.y > 800 || r.width < 20 || r.width > 60) continue;
      out.push({ x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
        中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        文: (b.innerText || '').trim().slice(0, 10), aria: b.getAttribute('aria-label'),
        title: b.getAttribute('title') });
    }
    return out;
  })(),
}));

const 浏览器 = await launch();
const page = 浏览器.page;

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  await closePromos(page);
  await page.screenshot({ path: resolve(EVID, 'fv7-0-复原前.png') });

  const 前 = await 状态();
  R.读数.前 = 前;
  记(`复原前：确认框 ${前.确认框 ? '在' : '不在'}，缩放 ${前.缩放}%，节点 ${前.节点.length} 个`);
  记(`\n⭐ 底栏七枚按钮逐枚实名（下次照这个点，别再靠尺寸猜）：`);
  前.画布按钮.forEach((b, i) => 记(`   ${i + 1}. 中心(${b.中心.join(',')}) ${b.w}×${b.h} 文「${b.文}」 aria=${b.aria} title=${b.title}`));

  if (!前.确认框) { 记('⛔ 页面上没有「是否保留此次整理结果」，可能已刷新过'); }
  else if (!前.还原按钮) { 记('❌ 确认框在，但找不到「还原」按钮 —— ⛔ 不猜，需要人工看一眼'); }
  else {
    记(`\n点「还原」@${前.还原按钮.中心.join(',')}`);
    await page.mouse.click(前.还原按钮.中心[0], 前.还原按钮.中心[1]);
    await page.waitForTimeout(1500);
    await page.screenshot({ path: resolve(EVID, 'fv7-1-点还原之后.png') });
    const 后 = await 状态();
    R.读数.后 = 后;
    断言('确认框消失', !后.确认框, `确认框 ${后.确认框 ? '还在' : '已消失'}`);
    断言('缩放回到 48%', 后.缩放 === '48%', `当前 ${后.缩放}%`);
    断言('节点数回到 12', 后.节点.length === 12, `当前 ${后.节点.length} 个`);
    断言('节点 id 集合不变', JSON.stringify(后.节点) === JSON.stringify(前.节点), '逐条比对 id 集合');
  }
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFV7.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
