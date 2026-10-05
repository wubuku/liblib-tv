// ⭐⭐⭐⭐⭐ Batch FT-1：上界面找 AnnotateToolbar —— 先解决 FR-4 的三个坑
//
// FS 已经从源码里确知：
//   · `AnnotateToolbar` 的 props 是
//     { tool, color, strokeWidth, canUndo, canRedo, onClose, onToolChange,
//       onColorChange, onStrokeWidthChange, onUndo, onRedo, onSave }
//   · 它的容器 class 是
//     `border-hair bg-panel-background border-canvas-controls-border
//      flex w-fit items-center gap-2 rounded-xl p-2 shadow-md`
//     ⭐⭐ **`shadow-md` + `rounded-xl` + `w-fit`** —— 这三个特征组合在画布上很好认
//   · 里面有三种笔：`pencil` / `rect` / `text`（高亮时 `bg-canvas-controls-active`）
//     ⭐⭐ **高亮 class = `bg-canvas-controls-active`** —— 又一个可用的判据
//
// ⛔ FR-4 踩的三个坑，这一批逐个拆掉：
//   ① `⤢` 的 class 正则 `size-[15px]|right-0.5` **没匹配上**（缺陷 471）
//      ⇒ 这次改用**穷举 + 逐个悬停读 tooltip**，不靠 class。
//   ② 视频节点全是空态 ⇒ 工具条不出现（缺陷 471 的教训）
//      ⇒ 这次**换成有内容的图片节点**（主画布 `i-9nlG6HdjK2` 300×169 明确有图）。
//   ③ 选节点要点**标题栏**而不是中心（缺陷 463）
//
// ⛔ 安全边界：
//   ⛔ 不点任何会消耗积分的按钮（抠图/扩图/高清放大/宫格高清/多角度/打光…）
//   ⛔ 不点「保存标注」「确认裁剪」—— 它们会改内容
//   ⛔ 不上传任何文件
//   ✅ 只选节点、只悬停读 tooltip、只截图、只量结构
//   ⛔ 菜单/面板**可以点开看结构**（点开是瞬态的，关掉即恢复）
import { launch, closePromos, ORIGIN, 全页文字, 归一, 断言器, 找节点, 中心属主, 查重叠 } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const 主画布 = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 证据图: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFT1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = 断言器(记);

const 浏览器 = await launch();
const page = 浏览器.page;

const 危险 = ['保存标注', '确认裁剪', '抠图', '扩图', '高清放大', '多角度', '打光', '补光', '保存', '确认', '生成', '删除'];
async function 扫危险(标签) {
  const 命中 = await page.evaluate((黑) => {
    const 归 = (s) => (s || '').replace(/\s+/g, '');
    return [...document.querySelectorAll('button,[role="button"]')].map((b) => {
      const r = b.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) return null;
      const t = 归(b.innerText) || 归(b.getAttribute('aria-label')) || 归(b.title);
      if (!t || !黑.some((k) => t.includes(归(k)))) return null;
      const cs = getComputedStyle(b);
      return { 文字: t.slice(0, 16), 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 禁用: b.disabled === true, cursor: cs.cursor };
    }).filter(Boolean);
  }, 危险);
  记(`   ⛔ ${标签}：危险按钮 ${命中.length} 枚 ${JSON.stringify(命中).slice(0, 360)}`);
  return 命中;
}

/** 只取离鼠标最近的那一条气泡（FP-3 定的规矩）。 */
async function 悬停读(点) {
  await page.mouse.move(点[0] - 60, 点[1]);
  await page.waitForTimeout(250);
  await page.mouse.move(点[0], 点[1]);
  await page.waitForTimeout(1500);
  return page.evaluate(({ x, y }) => {
    const 全部 = [...document.querySelectorAll('[class*="Tooltip"],[role="tooltip"],[data-portal]')]
      .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 30 && r.height > 10 && (e.innerText || '').trim(); })
      .map((e) => { const r = e.getBoundingClientRect(); return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 90) }; });
    return 全部.sort((a, b) => (Math.abs(a.框[0] + a.框[2] / 2 - x) + Math.abs(a.框[1] - y)) - (Math.abs(b.框[0] + b.框[2] / 2 - x) + Math.abs(b.框[1] - y)))[0] || null;
  }, { x: 点[0], y: 点[1] });
}

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(主画布, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(14000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);

  // ── ① 找一个有内容的图片节点（不靠 class 猜「有内容」，靠卡片里有 <img>/<video>）
  记('=== ① 找一个有内容的图片节点 ===');
  const 图节点 = await page.evaluate(() => {
    const ns = [...document.querySelectorAll('.react-flow__node')]
      .map((n) => {
        const r = n.getBoundingClientRect();
        return {
          id: n.getAttribute('data-id'),
          类: (String(n.className).match(/node-([a-z0-9-]+)/) || [, '?'])[1],
          框: [r.x, r.y, r.width, r.height],
          有媒体: n.querySelectorAll('img,video,canvas').length,
          图片数: n.querySelectorAll('img').length,
          文本: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40),
        };
      })
      .filter((n) => n.框[2] > 0 && n.框[3] > 0);
    return ns.filter((n) => n.类 === 'image');
  });
  记('   图片节点 ' + JSON.stringify(图节点, null, 1));
  const 有内容的 = 图节点.find((n) => n.图片数 > 0) || 图节点[0];
  断言(!!有内容的, '至少有一个图片节点', 图节点.length);
  记(`   ⭐ 选：${有内容的.id} 有 ${有内容的.图片数} 张图｜${有内容的.文本}`);

  // 点标题栏选中
  const t = await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    const r = n.getBoundingClientRect();
    return [Math.round(r.x + r.width / 2), Math.round(r.y + 14)];
  }, 有内容的.id);
  await page.mouse.click(t[0], t[1]);
  await page.waitForTimeout(2500);
  const a = await 中心属主(page, 有内容的.id);
  记('   选中后中心落点自证 ' + JSON.stringify(a));
  断言(!!a && a.属主 === 有内容的.id, `图片节点(${有内容的.id}) 中心落点属主就是它自己`, a);
  await 扫危险('选中后');

  // ── ② 穷举参数条上的按钮，逐个悬停读 tooltip（不靠 class 猜 ⤢）
  记('=== ② 穷举参数条按钮 + 逐个悬停读 tooltip ===');
  R.读数.参数条 = await page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ').trim();
    return [...document.querySelectorAll('button,[role="button"]')].map((b) => {
      const r = b.getBoundingClientRect();
      if (!(r.width > 0 && r.height > 0)) return null;
      const n = b.closest('.react-flow__node');
      if (n) return null;                              // 只要节点**外面**的
      if (!(r.top > 500)) return null;                 // ⭐ 用**绝对锚点**：参数条在 y>500
      const cs = getComputedStyle(b);
      return {
        文字: 归(b.innerText), aria: b.getAttribute('aria-label') || '', title: b.getAttribute('title') || '',
        框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
        点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
        禁用: b.disabled === true, cursor: cs.cursor, opacity: Number(cs.opacity).toFixed(2),
        class: String(b.className || '').slice(0, 100),
      };
    }).filter(Boolean);
  });
  记(`   ⭐ 参数条（y>500，节点外）共 ${R.读数.参数条.length} 枚`);
  R.读数.参数条.forEach((b, i) => 记(`   [${i}] ${JSON.stringify(b)}`));

  R.读数.气泡 = {};
  for (const b of R.读数.参数条) {
    if (b.文字 || b.aria) { R.读数.气泡[`${b.文字}|${b.aria}`] = '（本身有名字）'; continue; }
    const g = await 悬停读(b.点);
    R.读数.气泡[`[${b.框}]`] = g ? g.文字 : '（读不到气泡）';
    记(`   悬停 ${JSON.stringify(b.框)} → ${JSON.stringify(g)}`);
  }
  记('   气泡汇总 ' + JSON.stringify(R.读数.气泡, null, 1));

  // ── ③ ⭐ 找 `AnnotateToolbar` 的容器（shadow-md + rounded-xl + w-fit）
  R.读数.工具条容器 = await page.evaluate(() => {
    const 归 = (s) => (s || '').replace(/\s+/g, ' ');
    return [...document.querySelectorAll('div')].filter((el) => {
      const c = String(el.className || '');
      if (!/shadow-md/.test(c) || !/rounded-xl/.test(c) || !/w-fit/.test(c)) return false;
      const r = el.getBoundingClientRect();
      return r.width > 60 && r.height > 24;
    }).map((el) => {
      const r = el.getBoundingClientRect();
      return { 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], class: String(el.className).slice(0, 130), 文字: 归(el.innerText).slice(0, 120), 按钮数: el.querySelectorAll('button,[role="button"]').length };
    });
  });
  记('   ⭐ 找 `shadow-md + rounded-xl + w-fit` 的容器：' + JSON.stringify(R.读数.工具条容器));

  await 扫危险('参数条读完');
  await page.screenshot({ path: resolve(EVID, 'ft1-0-图片节点选中全景.png') });
  R.证据图.push({ 文件: 'ft1-0-图片节点选中全景.png' });
  记('   📷 ft1-0-图片节点选中全景.png');

  记(`断言统计 ${JSON.stringify(断言.统计)}`);
  R.读数.断言 = 断言.统计;
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFT1.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
