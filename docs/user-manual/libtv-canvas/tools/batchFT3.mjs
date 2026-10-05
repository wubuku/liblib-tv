// ⭐⭐⭐⭐⭐ Batch FT-3：⭐⭐⭐ 抓到一张**本手册从未描述过**的大界面
//
// FT-2 的截图撞出新东西：**参数条其实出现了，只是整个浮层跑到视口左侧、被裁掉一半**。
// 我按「节点框下方 200px 内」去找，一个都没读到 —— ⛔ 因为它挂在**节点左边**。
//
// ⭐⭐⭐⭐⭐ **这层浮层就是「图片编辑区」**，逐字读到的内容：
//   · 顶部一枚 `⤢` 展开箭头（右上角）
//   · 一枚 `风格` 徽标（带图层图标）
//   · 占位提示「**或上传图片输入文字指令对图片进行编辑，如：将背景改为雪夜**」
//     ⭐⭐⭐ **这是「用文字指令编辑图片」的入口 —— 手册一个字都没写过**
//   · 底部参数条：`Lib Image 2.5 Pro` `▾` │ `16:9 · 标准画质 · 2K · 1张` ▾ │ `1张` ▾
//     │ 三枚纯图标按钮（其中一枚带蓝点）│ `文A`（翻译提示词）│ `⛭`（预设）│ `⚡15` │ 圆形提交箭头
//
// ⭐⭐⭐ 底部参数条和 [参数条实测](10-tasks/image-presets.md) 那页对得上，
//    ⛔ 但**「风格」徽标 + 那句占位提示**两页都没有。
//    ⇒ 顺带更正 FT-2 的一处知识错误：「图片节点折叠态只有 169 高、参数条在框外 150px」
//    —— ⛔ **参数条不是固定偏移**，它属于**这个编辑区浮层**，浮层位置随节点变。
//
// 本轮做三件事：
//   ① 用 `⌘0` 之后重选一个**位置靠右**的图片节点，让浮层完整落在视口内
//   ② 逐字读完整浮层（含那枚带蓝点的图标，悬停读它的 tooltip）
//   ③ 量出这个浮层的真实几何并拍成成品图
//
// ⛔ 安全边界：不点任何会消耗积分或改内容的按钮；只选节点、只悬停、只截图。
import { launch, closePromos, ORIGIN, 全页文字, 归一, 断言器, 中心属主 } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const 主画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 证据图: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFT3.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
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

  // ⭐ 选**最靠右**的图片节点（浮层挂在它左边，才不会跑到视口外）
  const 图节点 = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')]
    .map((n) => { const r = n.getBoundingClientRect(); return { id: n.getAttribute('data-id'), 类: (String(n.className).match(/node-([a-z0-9-]+)/) || [, '?'])[1], 框: [r.x, r.y, r.width, r.height], 图片数: n.querySelectorAll('img').length }; })
    .filter((n) => n.类 === 'image' && n.框[2] > 0)
    .sort((a, b) => b.框[0] - a.框[0]));
  记('   图片节点（按 x 降序）' + JSON.stringify(图节点));
  const 目标 = 图节点[0];
  断言(!!目标, '至少有一个图片节点', 图节点.length);
  记(`   ⭐ 选最靠右的：${目标.id} 框 ${JSON.stringify(目标.框.map(Math.round))}`);

  const t = [Math.round(目标.框[0] + 目标.框[2] / 2), Math.round(目标.框[1] + 14)];
  const 前 = await page.evaluate(() => document.querySelectorAll('button,[role="button"]').length);
  await page.mouse.click(t[0], t[1]);
  await page.waitForTimeout(3200);
  const 后 = await page.evaluate(() => document.querySelectorAll('button,[role="button"]').length);
  记(`   点标题栏：全页可点元素 ${前} → ${后}（${后 > 前 ? '⭐ 变多了 = 编辑区展开了' : '没变'}）`);
  const a = await 中心属主(page, 目标.id);
  断言(!!a && a.属主 === 目标.id, `图片节点(${目标.id}) 中心落点属主就是它自己`, a);
  断言(后 > 前, '⭐ 选中后出现了新的可点元素（编辑区/参数条展开了）', { 前, 后 });

  // ⭐ 找这个编辑区浮层：含 `⤢` 展开箭头 + 占位提示那个框
  R.读数.编辑区 = await page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ').trim();
    return [...document.querySelectorAll('div')].filter((el) => {
      const r = el.getBoundingClientRect();
      if (!(r.width > 380 && r.height > 100)) return false;
      const t = el.innerText || '';
      return /上传图片输入文字指令|请输入提示词/.test(t);
    }).map((el) => {
      const r = el.getBoundingClientRect();
      return {
        框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        z: getComputedStyle(el).zIndex,
        class: String(el.className).slice(0, 140),
        全文: 归(el.innerText).slice(0, 400),
        按钮: [...el.querySelectorAll('button,[role="button"]')].map((b) => {
          const br = b.getBoundingClientRect();
          if (!(br.width > 0 && br.height > 0)) return null;
          return {
            文字: 归(b.innerText), aria: b.getAttribute('aria-label') || '', title: b.getAttribute('title') || '',
            框: [Math.round(br.x), Math.round(br.y), Math.round(br.width), Math.round(br.height)],
            点: [Math.round(br.x + br.width / 2), Math.round(br.y + br.height / 2)],
            禁用: b.disabled === true, cursor: getComputedStyle(b).cursor,
            class: String(b.className || '').slice(0, 80),
          };
        }).filter(Boolean),
      };
    });
  });
  记('   ⭐ 编辑区浮层：' + JSON.stringify(R.读数.编辑区, null, 1).slice(0, 2500));
  const 区 = (R.读数.编辑区 || []).sort((a, b) => (b.框[2] * b.框[3]) - (a.框[2] * a.框[3]))[0];
  断言(!!区, '⭐ 找到图片编辑区浮层（含占位提示那个框）', (R.读数.编辑区 || []).map((x) => x.框));
  断言(区 && 区.框[0] >= 0 && 区.框[0] + 区.框[2] <= 1440,
    '⭐ 编辑区完整落在视口内（FT-2 那一轮它被裁掉了一半）', 区 && 区.框);

  // ── 逐个悬停读 tooltip（只取离鼠标最近的那一条，FP-3 定的规矩）
  R.读数.气泡 = {};
  for (const b of (区?.按钮 || [])) {
    const 名 = b.文字 || b.aria || b.title;
    if (名) { R.读数.气泡[名] = '（本身有名字）'; continue; }
    await page.mouse.move(b.点[0] - 50, b.点[1]);
    await page.waitForTimeout(220);
    await page.mouse.move(b.点[0], b.点[1]);
    await page.waitForTimeout(1400);
    const g = await page.evaluate(({ x, y }) => {
      const 全部 = [...document.querySelectorAll('[class*="Tooltip"],[role="tooltip"],[data-portal]')]
        .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 30 && r.height > 10 && (e.innerText || '').trim(); })
        .map((e) => { const r = e.getBoundingClientRect(); return { x: r.x + r.width / 2, y: r.y, 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 100) }; });
      return 全部.sort((a, b) => (Math.abs(a.x - x) + Math.abs(a.y - y)) - (Math.abs(b.x - x) + Math.abs(b.y - y)))[0] || null;
    }, { x: b.点[0], y: b.点[1] });
    R.读数.气泡[`[${b.框}]`] = g ? g.文字 : '（读不到气泡）';
    记(`   悬停 ${JSON.stringify(b.框)}（class ${b.class.slice(0, 40)}）→ ${JSON.stringify(g && g.文字)}`);
  }
  记('   ⭐ 气泡汇总 ' + JSON.stringify(R.读数.气泡, null, 1));

  if (区) {
    const clip = { x: Math.max(0, 区.框[0] - 16), y: Math.max(0, 区.框[1] - 16), width: Math.min(1440, 区.框[2] + 32), height: Math.min(810, 区.框[3] + 32) };
    await page.screenshot({ path: resolve(EVID, 'ft3-0-图片编辑区浮层.png'), clip });
    R.证据图.push({ 文件: 'ft3-0-图片编辑区浮层.png', clip });
    记(`   📷 ft3-0-图片编辑区浮层.png｜裁剪 ${JSON.stringify(clip)}`);
  }

  记(`断言统计 ${JSON.stringify(断言.统计)}`);
  R.读数.断言 = 断言.统计;
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFT3.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
