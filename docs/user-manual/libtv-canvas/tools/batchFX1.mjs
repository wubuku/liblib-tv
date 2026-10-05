// ⭐⭐⭐⭐⭐ Batch FX-1：实拍小地图面板 + 两枚开关的两态对照
//
// 手册 `organize-canvas.md:348` 写的是：
//     「切换小地图 | 显示/隐藏**右下角**缩略图，节点多时用它定位 | ✅ 能来回切」
// ⭐ 但触发它的按钮在**左下角** —— 一个左下角的开关控制右下角的面板？
// ⇒ 要拍出来才知道面板到底在哪、什么样、有多大。
//
// 顺带把两枚开关的**两态**拍成对照（手册 M-356 / M-368 只记了「有两态」，
// 但没有并排对照图）：
//   `隐藏节点连线`  开 ⇄ 关
//   `网格吸附`      开 ⇄ 关
//
// ⛔ 这两枚是纯视图开关，改了能原样改回（规程允许「整理画布+保留」这类可复原操作）。
// ⛔ 每一步都读回状态自证，不靠截图猜。
// ⛔ 复原只允许「开关按回去」。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = resolve(HERE, '.evidence');
const R = { 步骤: [], 读数: {}, 断言: [] };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFX1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };
const 断言 = (名, 过, 明) => { R.断言.push({ 名, 过, 明 }); 记(`${过 ? '✅' : '❌'} ${名} —— ${明}`); };

const 浏览器 = await launch();
const page = 浏览器.page;

// 读小地图面板：react-flow 的小地图有固定 class（.react-flow__minimap）
const 读小地图 = () => page.evaluate(() => {
  const m = document.querySelector('.react-flow__minimap');
  if (!m) return { 有: false };
  const r = m.getBoundingClientRect();
  const img = m.querySelector('svg, img, canvas');
  return { 有: true, 框: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    可见: r.width > 4 && r.height > 4,
    内部: [...m.querySelectorAll('*')].map((e) => ({ t: e.tagName, c: (e.getAttribute('class') || '').slice(0, 60),
      w: Math.round(e.getBoundingClientRect().width), h: Math.round(e.getBoundingClientRect().height) })).slice(0, 12) };
});

// 读两枚开关的视觉状态：data-checked / aria-pressed / 内部 svg 的 fill
const 读开关 = (aria) => page.evaluate((n) => {
  const b = document.querySelector(`[aria-label="${n}"]`);
  if (!b) return { 有: false };
  const r = b.getBoundingClientRect();
  const cs = getComputedStyle(b);
  const svgs = [...b.querySelectorAll('svg')].map((s) => ({
    w: s.getAttribute('width'), h: s.getAttribute('height'),
    fill: getComputedStyle(s).fill, color: getComputedStyle(s).color,
    路径数: s.querySelectorAll('path').length }));
  return { 有: true, 中心: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
    背景: cs.backgroundColor, 颜色: cs.color, 不透明度: cs.opacity,
    dataChecked: b.getAttribute('data-checked'), ariaPressed: b.getAttribute('aria-pressed'),
    圆点: [...b.querySelectorAll('[class*="rounded-full"], [class*="bg-"]')].map((e) => {
      const c = getComputedStyle(e); const rr = e.getBoundingClientRect();
      return { 背景: c.backgroundColor, 边: rr.width, 左: Math.round(rr.x - r.x) }; }),
    svgs };
}, aria);

// 读连线数（判「隐藏节点连线」有没有真的生效）
const 读连线 = () => page.evaluate(() => ({
  边: document.querySelectorAll('.react-flow__edge').length,
  可见边: [...document.querySelectorAll('.react-flow__edge')]
    .filter((e) => { const r = e.getBoundingClientRect(); return r.width > 0; }).length,
  路径可见: [...document.querySelectorAll('.react-flow__edge path')]
    .filter((p) => { const s = getComputedStyle(p); return s.stroke !== 'rgba(0, 0, 0, 0)' && s.opacity !== '0'; }).length,
}));

try {
  mkdirSync(EVID, { recursive: true });
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(6000);
  await closePromos(page);
  await page.waitForTimeout(3500);

  // ⭐ 等节点数稳定（缺陷 491）
  let 上次 = -1, 稳 = 0;
  for (let i = 0; i < 25; i++) {
    const n = await page.evaluate(() => document.querySelectorAll('.react-flow__node').length);
    if (n === 上次) { 稳++; if (稳 >= 3) { 记(`画布稳定在 ${n} 个节点`); break; } } else 稳 = 0;
    上次 = n; await page.waitForTimeout(1200);
  }

  // 关抽屉 + 通知横幅
  await page.evaluate(() => {
    for (const b of document.querySelectorAll('.mantine-Drawer-inner [aria-label="关闭"], .mantine-Drawer-close')) b.click();
  });
  await page.waitForTimeout(900);

  // ── ① 小地图
  记('\n--- ① 小地图面板 ---');
  const 前 = await 读小地图();
  R.读数.小地图前 = 前;
  记(`点开前：${前.有 ? `已存在（可见=${前.可见}）` : '⛔ 面板不在 DOM 里'}`);

  const 开关 = await 读开关('切换小地图');
  R.读数.小地图开关前 = 开关;
  记(`按钮「切换小地图」：背景 ${开关.背景}，圆点 ${JSON.stringify(开关.圆点)}`);

  await page.mouse.click(开关.中心[0], 开关.中心[1]);
  await page.waitForTimeout(1400);
  const 后 = await 读小地图();
  R.读数.小地图后 = 后;
  断言('小地图面板出现了', 后.有 && 后.可见, 后.有 ? `框 ${后.框.join(',')}` : '面板不在 DOM');
  if (后.有) {
    记(`⭐ 小地图框 = [${后.框.join(',')}]（x=${后.框[0]}, y=${后.框[1]}）`);
    记(`   ⇒ x=${后.框[0]} ${后.框[0] < 200 ? '在**左下**' : '在**右下**'}；手册写的是「右下角」`);
    记(`   内部元素 ${后.内部.length} 个：${后.内部.slice(0, 6).map((e) => `${e.t}.${e.c}(${e.w}×${e.h})`).join(' | ')}`);
  }
  await page.screenshot({ path: resolve(EVID, 'fx1-1-小地图打开.png') });
  await page.screenshot({ path: resolve(EVID, 'fx1-2-小地图特写.png'),
    clip: 后.有 ? { x: Math.max(0, 后.框[0] - 30), y: Math.max(0, 后.框[1] - 30),
                  width: 后.框[2] + 60, height: 后.框[3] + 60 } : undefined });

  // 复原
  const 开关2 = await 读开关('切换小地图');
  await page.mouse.click(开关2.中心[0], 开关2.中心[1]);
  await page.waitForTimeout(1300);
  const 关后 = await 读小地图();
  断言('小地图已复原为关闭', !关后.可见, `可见=${关后.可见}`);

  // ── ② 隐藏节点连线 两态
  记('\n--- ② 隐藏节点连线 两态 ---');
  const 连0 = await 读连线();
  const 隐0 = await 读开关('隐藏节点连线');
  R.读数.连线前 = { 连0, 隐0 };
  记(`点之前：边 ${连0.边}、可见 ${连0.可见边}、路径有 stroke ${连0.路径可见}；按钮背景 ${隐0.背景}`);

  await page.mouse.click(隐0.中心[0], 隐0.中心[1]);
  await page.waitForTimeout(1300);
  const 连1 = await 读连线();
  const 隐1 = await 读开关('隐藏节点连线');
  R.读数.连线后 = { 连1, 隐1 };
  记(`点之后：边 ${连1.边}、可见 ${连1.可见边}、路径有 stroke ${连1.路径可见}；按钮背景 ${隐1.背景}`);
  断言('连线的可见性真的变了', 连0.可见边 !== 连1.可见边 || 连0.路径可见 !== 连1.路径可见,
    `${连0.可见边}→${连1.可见边} / ${连0.路径可见}→${连1.路径可见}`);
  await page.screenshot({ path: resolve(EVID, 'fx1-3-连线隐藏后.png') });
  // 复原（⛔ 必须**重新读**按钮坐标：点一次之后 DOM 会重排，缓存的坐标会失效 —— FX-1 第一版就栽在这）
  const 隐1b = await 读开关('隐藏节点连线');
  记(`复原前重读按钮：${隐1b.有 ? `中心 ${隐1b.中心}` : '⛔ 按钮不在'}`);
  if (隐1b.有) {
    await page.mouse.click(隐1b.中心[0], 隐1b.中心[1]);
    await page.waitForTimeout(1500);
  }
  const 连2 = await 读连线();
  断言('连线已复原', 连2.可见边 === 连0.可见边, `${连0.可见边} → ${连2.可见边}`);

  // ── ③ 网格吸附 两态
  记('\n--- ③ 网格吸附 两态 ---');
  const 吸0 = await 读开关('网格吸附');
  R.读数.吸附前 = 吸0;
  记(`点之前：背景 ${吸0.背景}，圆点 ${JSON.stringify(吸0.圆点)}`);
  await page.mouse.click(吸0.中心[0], 吸0.中心[1]);
  await page.waitForTimeout(1300);
  const 吸1 = await 读开关('网格吸附');
  R.读数.吸附后 = 吸1;
  记(`点之后：背景 ${吸1.背景}，圆点 ${JSON.stringify(吸1.圆点)}`);
  断言('网格吸附的视觉真的变了', JSON.stringify(吸0.背景) !== JSON.stringify(吸1.背景)
    || JSON.stringify(吸0.圆点) !== JSON.stringify(吸1.圆点), `${吸0.背景} → ${吸1.背景}`);
  await page.screenshot({ path: resolve(EVID, 'fx1-4-网格吸附开.png') });
  const 吸1b = await 读开关('网格吸附');
  记(`复原前重读按钮：${吸1b.有 ? `中心 ${吸1b.中心}` : '⛔ 按钮不在'}`);
  if (吸1b.有) { await page.mouse.click(吸1b.中心[0], 吸1b.中心[1]); await page.waitForTimeout(1500); }
  const 吸2 = await 读开关('网格吸附');
  断言('网格吸附已复原', 吸2.背景 === 吸0.背景, `${吸1.背景} → ${吸2.背景}`);

  await page.screenshot({ path: resolve(EVID, 'fx1-5-末态.png') });
} catch (e) {
  记('❌ 异常：' + e.message);
  R.读数.错误 = e.message;
} finally {
  writeFileSync(HERE + 'batchFX1.json', JSON.stringify(R, null, 2));
  await 浏览器.browser.close().catch(() => {});
  console.log('\n完成。');
}
