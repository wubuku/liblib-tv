// ⭐⭐⭐⭐⭐ Batch FT-2：诊断「FT-1 点标题栏后参数条根本没出现」
//
// FT-1 的读数（**两条断言都过了，但结论是反的**）：
//   · 中心落点自证 ✅ —— 节点确实被选中了
//   · ⛔ 「参数条（y>500，节点外）」**读到 23 枚，全是顶栏/底栏/TV Director 抽屉**，
//     **一枚节点参数条按钮都没有**
//   · ⛔ `AnnotateToolbar` 的容器特征（`shadow-md + rounded-xl + w-fit`）**读到 0 个**
//
// ⚠️⚠️ 第一条断言是**假绿灯**！它只证明「点在标题栏上命中了那个节点」，
//    ⛔ **不证明节点进入了「参数条已展开」的状态** —— 这是本轮要拆的坑。
//
// ⭐ 知识修正（很重要，别再错）：
//   之前 PROGRESS 记的是「参数条 y 600~800」「y=657」「y=668」。
//   ⛔⭐ 那些读数来自**图片节点当时占据的那一格**。
//   FT-1 选中的图片节点框是 **y 329~498**，参数条若紧贴它 ⇒ 大约在 **y 500~530**。
//   ⇒ **`y>500` 这个阈值把它漏了**；`y>500` 抓到的 y=521 那两枚其实是
//     TV Director 抽屉里的「上传故事来改编 / 批量优化提示词」。
//
// 本轮改用**相对锚点**：量出节点框，再在「节点框下方 200px 内」找参数条。
// ⛔ 但同时用**绝对锚点 y>700** 排除底栏，两条一起用。
//
// ⛔ 安全边界：不点任何会消耗积分或改内容的按钮；只选节点、只量、只截图。
import { launch, closePromos, ORIGIN, 全页文字, 归一, 断言器, 中心属主 } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const 主画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 证据图: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFT2.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
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

  const 图节点 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
    .map((n) => { const r = n.getBoundingClientRect(); return { id: n.getAttribute('data-id'), 类: (String(n.className).match(/node-([a-z0-9-]+)/) || [, '?'])[1], 框: [r.x, r.y, r.width, r.height], 图片数: n.querySelectorAll('img').length, 文本: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) }; })
    .filter((n) => n.类 === 'image' && n.框[2] > 0));
  记('   图片节点 ' + JSON.stringify(图节点));
  const 目标 = 图节点.find((n) => n.图片数 > 0) || 图节点[0];
  记(`   ⭐ 目标 ${目标.id} 框 ${JSON.stringify(目标.框.map(Math.round))}`);

  // 点**卡片标题栏**（顶部 14px）
  const t = [Math.round(目标.框[0] + 目标.框[2] / 2), Math.round(目标.框[1] + 14)];
  const 基线 = await page.evaluate(() => document.querySelectorAll('button,[role="button"]').length);
  await page.mouse.click(t[0], t[1]);
  await page.waitForTimeout(3000);
  const 选中后 = await page.evaluate(() => document.querySelectorAll('button,[role="button"]').length);
  记(`   点标题栏：全页可点元素 ${基线} → ${选中后}`);
  const a = await 中心属主(page, 目标.id);
  记('   中心落点自证 ' + JSON.stringify(a));
  断言(!!a && a.属主 === 目标.id, `图片节点(${目标.id}) 中心落点属主就是它自己`, a);

  R.读数.选中态class = await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    return { class: String(n.className), 框: (() => { const r = n.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })() };
  }, 目标.id);
  记('   ⭐ 选中后节点的 class = ' + R.读数.选中态class.class);
  断言(/selected/.test(R.读数.选中态class.class), '节点 class 里真的带 selected', R.读数.选中态class.class);

  // ── ⭐ 用**相对锚点**：节点框下方 200px 内，且 y<700 排除底栏
  const 框 = R.读数.选中态class.框;
  R.读数.相对锚点参数条 = await page.evaluate(({ f }) => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ').trim();
    const 顶 = f[1] + f[3], 底 = Math.min(810, 顶 + 200);
    return [...document.querySelectorAll('button,[role="button"]')].map((b) => {
      const r = b.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) return null;
      if (b.closest('.react-flow__node')) return null;          // 节点内的不算
      if (!(r.top >= 顶 - 8 && r.bottom <= 底)) return null;     // ⭐ 相对锚点
      if (r.top > 700) return null;                             // ⛔ 排除底栏
      const cs = getComputedStyle(b);
      return {
        文字: 归(b.innerText), aria: b.getAttribute('aria-label') || '', title: b.getAttribute('title') || '',
        框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        禁用: b.disabled === true, cursor: cs.cursor, opacity: Number(cs.opacity).toFixed(2),
        class: String(b.className || '').slice(0, 110),
      };
    }).filter(Boolean);
  }, { f: 框 });
  记(`   ⭐ 相对锚点（节点框 ${JSON.stringify(框)} 下方 200px 内、y<700）读到 ${R.读数.相对锚点参数条.length} 枚`);
  R.读数.相对锚点参数条.forEach((b, i) => 记(`   [${i}] ${JSON.stringify(b)}`));
  断言(R.读数.相对锚点参数条.length > 0,
    '⭐ 用相对锚点能读到参数条（FT-1 用 y>500 一个都没读到，是阈值漏了）',
    R.读数.相对锚点参数条.length);

  // ── 逐个悬停读 tooltip
  R.读数.气泡 = {};
  for (const b of R.读数.相对锚点参数条) {
    const k = b.文字 || b.aria || b.title || `[${b.框}]`;
    if (b.文字 || b.aria || b.title) { R.读数.气泡[k] = '（本身有名字）'; continue; }
    await page.mouse.move(b.点[0] - 60, b.点[1]);
    await page.waitForTimeout(220);
    await page.mouse.move(b.点[0], b.点[1]);
    await page.waitForTimeout(1400);
    const g = await page.evaluate(({ x, y }) => {
      const 全部 = [...document.querySelectorAll('[class*="Tooltip"],[role="tooltip"],[data-portal]')]
        .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 30 && r.height > 10 && (e.innerText || '').trim(); })
        .map((e) => { const r = e.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y, 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 90) }; });
      return 全部.sort((a, b) => (Math.abs(a.x - x) + Math.abs(a.y - y)) - (Math.abs(b.x - x) + Math.abs(b.y - y)))[0] || null;
    }, { x: b.点[0], y: b.点[1] });
    R.读数.气泡[`[${b.框}]`] = g ? g.文字 : '（读不到气泡）';
    记(`   悬停 ${JSON.stringify(b.框)} → ${JSON.stringify(g && g.文字)}`);
  }
  记('   ⭐ 气泡汇总 ' + JSON.stringify(R.读数.气泡, null, 1));

  // ── AnnotateToolbar 容器
  R.读数.工具条容器 = await page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ');
    return [...document.querySelectorAll('div')].filter((el) => {
      const c = String(el.className || '');
      if (!/shadow-md/.test(c)) return false;
      const r = el.getBoundingClientRect();
      return r.width > 60 && r.height > 24 && r.top < 800;
    }).map((el) => {
      const r = el.getBoundingClientRect();
      return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], class: String(el.className).slice(0, 140), 文字: 归(el.innerText).slice(0, 120), 按钮数: el.querySelectorAll('button,[role="button"]').length };
    });
  });
  记('   ⭐ 带 `shadow-md` 的容器：' + JSON.stringify(R.读数.工具条容器));

  await page.screenshot({ path: resolve(EVID, 'ft2-0-图片节点选中参数条.png') });
  R.证据图.push({ 文件: 'ft2-0-图片节点选中参数条.png' });
  记('   📷 ft2-0-图片节点选中参数条.png');

  记(`断言统计 ${JSON.stringify(断言.统计)}`);
  R.读数.断言 = 断言.统计;
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFT2.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
