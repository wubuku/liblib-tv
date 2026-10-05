// 探针：① 「网格吸附」按钮的 DOM 前后逐字对照（找开/关到底怎么表达）
//      ② 点开之后背景 pattern 会不会从「圆点」变成「网格线」
//      ③ 顺带把 dot 点阵的真实相位算出来（不手算，页内算）
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(HERE + 'dbg-fb3.json', JSON.stringify(o, null, 2));
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); 落盘(R); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;

/** 底栏里那个按钮的完整 DOM（连祖先一起，便于看清状态挂在哪一层） */
const 按钮DOM = () => page.evaluate(() => {
  let b = null;
  for (const x of document.querySelectorAll('button')) {
    const r = x.getBoundingClientRect();
    if (r.top < 740 || r.bottom > 810 || r.left > 340) continue;
    if ((x.getAttribute('aria-label') || '').includes('网格吸附')) { b = x; break; }
  }
  if (!b) return null;
  const 层 = [];
  let n = b;
  for (let i = 0; i < 4 && n; i++, n = n.parentElement) {
    层.push({
      标签: n.tagName,
      class: n.getAttribute('class'),
      aria: n.getAttribute('aria-label'),
      pressed: n.getAttribute('aria-pressed'),
      data: Object.fromEntries([...n.attributes].filter((a) => a.name.startsWith('data-')).map((a) => [a.name, a.value])),
      样式: (() => { const c = getComputedStyle(n); return { bg: c.backgroundColor, color: c.color, opacity: c.opacity, cursor: c.cursor }; })(),
      外链: n.outerHTML.slice(0, 700),
    });
  }
  const r = b.getBoundingClientRect();
  return { 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 层 };
});

/** 背景 pattern 的全部属性 + 内容类型 + 算好的点阵相位 */
const 背景 = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
  const p = m ? m[1].split(',').map(Number) : [1, 0, 0, 1, 0, 0];
  const zoom = p[0];
  const svg = document.querySelector('svg.react-flow__background') || document.querySelector('.react-flow__background');
  const pat = svg ? svg.querySelector('pattern') : null;
  if (!pat) return { zoom, 有pattern: false };
  const A = Object.fromEntries([...pat.attributes].map((a) => [a.name, a.value]));
  const 内容 = [...pat.children].map((c) => {
    const o = Object.fromEntries([...c.attributes].map((a) => [a.name, a.value]));
    return { 标签: c.tagName, class: c.getAttribute('class'), 属性: o };
  });
  const w = Number(A.width), x = Number(A.x), y = Number(A.y);
  const t = /translate\(\s*(-?[\d.]+)px?\s*,\s*(-?[\d.]+)px?\s*\)/.exec(A.patternTransform || '');
  const tx = t ? Number(t[1]) : 0, ty = t ? Number(t[2]) : 0;
  const 内容标签 = 内容.map((c) => c.标签);
  const 圆 = 内容.find((c) => c.标签 === 'circle');
  return {
    zoom, 有pattern: true, 属性: A, 内容,
    内容类型: 内容标签.join('+'),
    算: {
      步长px: w,
      步长画布: w / zoom,
      平移px: [tx, ty],
      tile原点px: [x + tx, y + ty],
      tile原点画布: [(x + tx) / zoom, (y + ty) / zoom],
      圆心在tile内px: 圆 ? [Number(圆.属性.cx), Number(圆.属性.cy)] : null,
      圆心画布: 圆 ? [(x + tx + Number(圆.属性.cx)) / zoom, (y + ty + Number(圆.属性.cy)) / zoom] : null,
      圆半径px: 圆 ? Number(圆.属性.r) : null,
      圆半径画布: 圆 ? Number(圆.属性.r) / zoom : null,
    },
  };
});

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  const b0 = await 背景();
  记('⭐ 开态前：内容类型 = ' + b0.内容类型 + '｜步长 ' + b0.算.步长画布?.toFixed(4) + ' 画布单位');
  记('   圆阵相位（画布单位）= ' + JSON.stringify(b0.算.圆心画布?.map((n) => Number(n.toFixed(4)))) + '｜半径 ' + b0.算.圆半径画布?.toFixed(4));
  记('   tile 原点（画布单位）= ' + JSON.stringify(b0.算.tile原点画布.map((n) => Number(n.toFixed(4)))));
  R.读数.开态前 = b0;
  await page.screenshot({ path: EVID + 'fb3-01-网格吸附关.png' });

  const d0 = await 按钮DOM();
  记('⭐⭐ 按钮中心 = ' + JSON.stringify(d0.中心) + '｜框 ' + JSON.stringify(d0.框));
  for (const [i, 层] of d0.层.entries()) {
    记(`  层${i} <${层.标签} class="${层.class}" aria="${层.aria}" pressed="${层.pressed}"> 样式 ${JSON.stringify(层.样式)}`);
  }
  R.读数.按钮关 = d0;

  // 先自证落点
  const v = await page.evaluate((p) => {
    const e = document.elementFromPoint(p[0], p[1]);
    return e ? e.tagName + '|' + (e.getAttribute('aria-label') || '') + '|closest按钮=' + (e.closest('button') ? (e.closest('button').getAttribute('aria-label') || '无aria') : 'null') : 'null';
  }, d0.中心);
  await page.mouse.move(d0.中心[0], d0.中心[1]); await page.waitForTimeout(420);
  const v2 = await page.evaluate((p) => {
    const e = document.elementFromPoint(p[0], p[1]);
    return e ? e.tagName + '|' + (e.getAttribute('aria-label') || '') + '|closest按钮=' + (e.closest('button') ? (e.closest('button').getAttribute('aria-label') || '无aria') : 'null') : 'null';
  }, d0.中心);
  记('  ⭐ 自证落点：move 之前「' + v + '」→ move 之后「' + v2 + '」');
  if (!/网格吸附/.test(v2)) throw new Error('落点不属于网格吸附按钮，中止');

  await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(1100);
  await page.mouse.move(720, 240); await page.waitForTimeout(600);

  const d1 = await 按钮DOM();
  const b1 = await 背景();
  R.读数.按钮开 = d1; R.读数.开态后 = b1;
  记('⭐⭐⭐ 点击后：内容类型 = ' + b1.内容类型 + (b1.内容类型 !== b0.内容类型 ? '　⛔⭐⭐⭐ 背景**变了**！' : '（背景没变）'));
  记('   步长 ' + b1.算.步长画布?.toFixed(4) + ' 画布单位｜圆阵相位 ' + JSON.stringify(b1.算.圆心画布?.map((n) => Number(n.toFixed(4)))));
  记('   逐层对照：');
  for (let i = 0; i < Math.max(d0.层.length, d1.层.length); i++) {
    const a = d0.层[i], c = d1.层[i];
    if (!a || !c) { 记(`    层${i}：只在一侧存在`); continue; }
    const 差 = [];
    if (a.class !== c.class) 差.push(`class ${a.class} → ${c.class}`);
    if (a.aria !== c.aria) 差.push(`aria ${a.aria} → ${c.aria}`);
    if (a.pressed !== c.pressed) 差.push(`aria-pressed ${a.pressed} → ${c.pressed}`);
    if (JSON.stringify(a.样式) !== JSON.stringify(c.样式)) 差.push(`样式 ${JSON.stringify(a.样式)} → ${JSON.stringify(c.样式)}`);
    记(`    层${i}：${差.length ? 差.join('；') : '无变化'}`);
  }
  await page.screenshot({ path: EVID + 'fb3-02-网格吸附开.png' });
  记('已拍 fb3-01-网格吸附关.png / fb3-02-网格吸附开.png');
} catch (e) {
  R.错误 = String((e && e.stack) || e);
  记('❌ ' + e.message);
} finally {
  记('收尾核对：' + JSON.stringify(await 核对坐标(page)));
  await 浏览器.browser.close();
  落盘(R);
}
