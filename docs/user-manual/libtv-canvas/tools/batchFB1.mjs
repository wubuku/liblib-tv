// Batch FB-1：⭐⭐⭐「开了网格吸附以后，到底在什么条件下才真的对齐」
//
// EV 批已经坐实两件事：
//   · 点网格的真实步长 = **35 画布单位**（DOM pattern 16.05 ÷ zoom 0.4586 = 35.00）
//   · 开着吸附逐帧采 40 帧，x 相邻步长**全部 10.9/10.91 一帧不差**（严格 1:1 跟手），
//     落点对 35 的最大偏差 `17.02` ≈ 关态的 `17.00`
//   ⇒ 425 个画布单位跨过约 12 条网格线，**一次都没吸**
//
// 📖 剩下的问题是「那它在什么条件下才生效」。
//
// ⭐⭐⭐ 本轮先做一件**完全不动**的事：**拿 11 个节点的现有坐标去问「离 35 的整数倍有多近」**。
//    如果吸附真的在生效，被吸附过的节点应当**恰好**落在整数倍上（偏差 = 0）；
//    而没被吸附过的，偏差应当是「到最近整数倍的距离」，在 [0, 17.5] 上近似均匀。
//    ⇒ 一个距离分布就能回答「历史上有没有节点被吸过」。
//
// 然后再做一个**慢速拖拽实验**（逐帧小步 + 每步停顿），
// 因为 EV 那次是快速长距离拖 —— 若吸附带阈值/滞回，慢速才可能吸上。
//
// ⭐⭐⭐ **复原写在 `finally` 里**（EZ-1e 丢过节点的教训）。
// ⛔ 只拖 `a-THmbuJXQj4`（音频节点，画面左上、旁边无遮挡），拖完按画布坐标精确复原。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标, 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const OUT = HERE + 'batchFB1.json';
const EVID = HERE + '.evidence/';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const 结果 = { 读数: {}, 步骤: [] };
const 记 = (s) => { 结果.步骤.push(s); 落盘(结果); console.log('· ' + s); };

const 步长 = 35;          // EV 实测的网格步长（画布单位）
const 目标 = 'a-THmbuJXQj4';  // 要拖的节点（音频节点，旁边无遮挡）
let 原位 = null;
let 拖过 = false;

const 浏览器 = await launch();
const page = 浏览器.page;

/** 每个节点的画布坐标 + 到最近 35 整数倍的距离 */
const 距离统计 = () => page.evaluate((步) => {
  const 距 = (v) => { const r = v / 步; return Math.abs(r - Math.round(r)) * 步; };
  return [...document.querySelectorAll('.react-flow__node')].map((n) => {
    const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
    if (!m) return null;
    const x = Number(m[1]), y = Number(m[2]);
    const r = n.getBoundingClientRect();
    return {
      id: n.getAttribute('data-id'),
      画布: [x, y],
      x离整数倍: Number(距(x).toFixed(4)),
      y离整数倍: Number(距(y).toFixed(4)),
      屏: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
      中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
    };
  }).filter(Boolean).map((o) => Object.assign(o, { 最小距离: Math.min(o.x离整数倍, o.y离整数倍) }))
    .sort((a, b) => a.最小距离 - b.最小距离);
}, 步长);

const 网格开关 = async () => {
  const b = await page.evaluate(() => {
    const x = [...document.querySelectorAll('button')].find((e) => e.getAttribute('aria-label') === '网格吸附');
    if (!x) return null;
    const r = x.getBoundingClientRect();
    return { pt: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], 开: (x.getAttribute('aria-label') || '').includes('显示') };
  });
  if (!b) throw new Error('找不到网格吸附');
  await page.mouse.move(b.pt[0], b.pt[1]); await page.waitForTimeout(420);
  await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(900);
  await page.mouse.move(720, 250); await page.waitForTimeout(500);
  const 后 = await page.evaluate(() => {
    const x = [...document.querySelectorAll('button')].find((e) => ['网格吸附', '显示网格吸附'].includes(e.getAttribute('aria-label')));
    return x ? x.getAttribute('aria-label') : null;
  });
  记('  网格吸附 aria：点击后 = ' + JSON.stringify(后));
  return 后;
};

/** ⭐ 画布坐标驱动的拖拽 + 逐帧采样 + 循环复原到误差 < 0.5 */
const 慢拖 = async (起点画布, 终点画布, 标签) => {
  const 起 = await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    const v = document.querySelector('.react-flow__viewport');
    const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
    const p = m ? m[1].split(',').map(Number) : [1, 0, 0, 1, 0, 0];
    const r = n.getBoundingClientRect();
    return { 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], zoom: p[0] };
  }, 目标);
  const 落点验证 = await page.evaluate((p) => {
    const e = document.elementFromPoint(p[0], p[1]);
    const n = e ? e.closest('.react-flow__node') : null;
    return n && n.getAttribute('data-id');
  }, 起.中心);
  if (落点验证 !== 目标) { 记(`  ⛔ ${标签}：落点被 ${落点验证} 挡住，跳过`); return []; }

  const 读 = () => page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
    return m ? [Number(m[1]), Number(m[2])] : null;
  }, 目标);

  await page.mouse.move(起.中心[0], 起.中心[1]); await page.waitForTimeout(400);
  await page.mouse.down(); await page.waitForTimeout(160);
  const 轨迹 = [];
  // ⭐ 慢速：小步长（每步约 4 画布单位）+ 每步停 90ms —— 若吸附有滞回/阈值，这一路最有机会吸上
  const 总步 = 60;
  for (let i = 1; i <= 总步; i++) {
    const t = i / 总步;
    const cx = 起点画布[0] + (终点画布[0] - 起点画布[0]) * t;
    const cy = 起点画布[1] + (终点画布[1] - 起点画布[1]) * t;
    await page.mouse.move(起.中心[0] + (cx - 起点画布[0]) * 起.zoom, 起.中心[1] + (cy - 起点画布[1]) * 起.zoom);
    await page.waitForTimeout(90);
    if (i % 6 === 0) {
      const 现 = await 读();
      轨迹.push({ 步: i, 画布: 现, x离整数倍: 现 ? Number((Math.abs(现[0] / 步长 - Math.round(现[0] / 步长)) * 步长).toFixed(3)) : null });
    }
  }
  await page.mouse.up(); await page.waitForTimeout(900);
  await page.mouse.move(720, 250); await page.waitForTimeout(500);
  const 末 = await 读();
  记(`  ${标签}：落点画布 ${JSON.stringify(末)}；x 离 35 整数倍 ${末 ? (Math.abs(末[0] / 步长 - Math.round(末[0] / 步长)) * 步长).toFixed(3) : '?'}`);
  记(`    采样 ${轨迹.length} 点，x 离整数倍：${JSON.stringify(轨迹.map((t) => t.x离整数倍))}`);
  return 轨迹;
};

const 拖回原位 = async () => {
  if (!原位) return true;
  for (let 轮 = 1; 轮 <= 8; 轮++) {
    const s = await page.evaluate((id) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      const v = document.querySelector('.react-flow__viewport');
      const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
      const p = m ? m[1].split(',').map(Number) : [1, 0, 0, 1, 0, 0];
      const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
      const r = n.getBoundingClientRect();
      return { 画布: t ? [Number(t[1]), Number(t[2])] : null, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], zoom: p[0] };
    }, 目标);
    if (!s.画布) return false;
    const dx = 原位[0] - s.画布[0], dy = 原位[1] - s.画布[1];
    const 误 = Math.hypot(dx, dy);
    记(`  复原第 ${轮} 轮：现 [${s.画布}] → 目标 [${原位}]，误差 ${误.toFixed(3)}`);
    if (误 < 0.5) return true;
    const sx = s.中心[0] + dx * s.zoom, sy = s.中心[1] + dy * s.zoom;
    if (sx < 2 || sy < 2 || sx > 1438 || sy > 808) { 记('  ⛔ 出视口'); return false; }
    const ok = await page.evaluate((p) => {
      const e = document.elementFromPoint(p[0], p[1]);
      const n = e ? e.closest('.react-flow__node') : null;
      return n && n.getAttribute('data-id');
    }, s.中心);
    if (ok !== 目标) { 记('  ⛔ 落点被 ' + ok + ' 挡住'); return false; }
    await page.mouse.move(s.中心[0], s.中心[1]); await page.waitForTimeout(380);
    await page.mouse.down(); await page.waitForTimeout(130);
    for (let i = 1; i <= 12; i++) { await page.mouse.move(s.中心[0] + (sx - s.中心[0]) * i / 12, s.中心[1] + (sy - s.中心[1]) * i / 12); await page.waitForTimeout(38); }
    await page.mouse.up(); await page.waitForTimeout(700);
    await page.mouse.move(720, 250); await page.waitForTimeout(350);
  }
  return false;
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  // ---------- 阶段 1：只读统计 ----------
  记('—— 阶段 1：11 个节点离 35 整数倍有多远（完全不动）——');
  const 统 = await 距离统计();
  记('  按最小距离排序：');
  for (const o of 统) 记(`    ${o.id} 画布 [${o.画布[0]}, ${o.画布[1]}]｜x 离 ${o.x离整数倍}｜y 离 ${o.y离整数倍}`);
  const 最小 = Math.min(...统.map((o) => o.最小距离));
  记(`  ⭐⭐ 全场最小距离 = ${最小}`);
  记(`  ⭐⭐ 小于 0.5 的有几个：${统.filter((o) => o.最小距离 < 0.5).length} 个`);
  结果.读数.距离统计 = 统;
  结果.读数.最小距离 = 最小;

  // ---------- 阶段 2：开吸附 + 慢速拖拽 ----------
  记('—— 阶段 2：开网格吸附，慢速小步拖拽 ——');
  const 开关前 = await page.evaluate(() => {
    const x = [...document.querySelectorAll('button')].find((e) => ['网格吸附', '显示网格吸附'].includes(e.getAttribute('aria-label')));
    return x ? x.getAttribute('aria-label') : null;
  });
  记('  开关初始 aria = ' + JSON.stringify(开关前));
  const 后 = await 网格开关();
  const 开着 = (后 || '').includes('显示');
  记('  吸附现在是「' + (开着 ? '开' : '关') + '」');

  const 起 = (统.find((o) => o.id === 目标) || {}).画布;
  原位 = 起 ? [起[0], 起[1]] : null;
  记(`  ${目标} 的画布坐标 = ${JSON.stringify(原位)}`);
  if (原位) {
    const 轨迹1 = await 慢拖(原位, [原位[0] + 240, 原位[1] + 60], '慢拖 240×60（开吸附）');
    拖过 = true;
    结果.读数.轨迹1 = 轨迹1;
    await 拖回原位();
    const 轨迹2 = await 慢拖(原位, [原位[0] - 175, 原位[1] - 140], '慢拖 -175×-140（开吸附，目标是 -175 = 35×5）');
    结果.读数.轨迹2 = 轨迹2;
    await 拖回原位();
    await page.screenshot({ path: EVID + 'fb1-吸附实验后.png' });
    记('  已拍 fb1-吸附实验后.png');
  }

  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 偏差 = await 核对坐标(page);
  记('⭐⭐ 静置 15s 后坐标复核：' + JSON.stringify(偏差));
  const 现 = await 读全部坐标(page);
  记(`  ${目标} 画布坐标现值 ${JSON.stringify(现[目标])}，基线 ${JSON.stringify(坐标[目标])}`);
  结果.收尾 = { 偏差, 现值: 现[目标], 基线: 坐标[目标] };
} catch (e) {
  记('❌ ' + e.message);
  结果.错误 = String((e && e.stack) || e);
} finally {
  // ⭐⭐⭐ 复原无条件执行，且先于关浏览器
  if (拖过) {
    记('—— finally：复原 ' + 目标 + ' ——');
    try {
      const 成 = await 拖回原位();
      记('  复原：' + (成 ? '✅ 到位' : '⛔ 没到位'));
      结果.收尾 = Object.assign(结果.收尾 || {}, { 复原: 成 ? '到位' : '没到位' });
    } catch (e2) {
      记('  ⛔ 复原抛错：' + e2.message);
      结果.收尾 = Object.assign(结果.收尾 || {}, { 复原: '抛错：' + e2.message });
    }
  }
  落盘(结果);
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchFB1.json ===');
}
