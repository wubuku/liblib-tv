// ⭐⭐⭐⭐⭐ Batch FG-1：**关态下**成组拖动会不会换一套吸附规则？
//
// 手册里关于吸附只剩最后一个 📖：「成组拖动、或按住 ⌥/⌘ 时会不会临时换一套规则」。
// 其中 ⛔ **修饰键（⌥/⌘）本轮明确不试** —— 手册 `20-reference.md` 记着
//    「创建副本 = `⌘`+`Option`+拖动」，⛔ 单独试 ⌥ 或 ⌘ 有可能**新建节点**，
//    而新建节点要再删（画布无回收站），风险不对等。**不拿不可逆操作换一个 📖。**
//
// ✅ 本轮只做零风险的那一半：**框选之后（关态 / 吸附态）整组拖动**。
//    FD-4 当时测的是**开态**，得到「整组拖动不吸附」；**关态下整组拖是空白**。
//
// ⭐⭐⭐⭐⭐ 本轮全程用新写进 lib.mjs 的 `往返拖`（拖 +d 再拖 −d，净位移 0），
//    这是 FB/FD/FE/FF 四次事故之后唯一被验证零风险的拖法。
//
// 三个互斥的预测（关态 + 框选 + 整组拖）：
//   ① **整组也吸附**   ⇒ 每个节点各自落到 12 栅格上，位移一致，节点间距不变
//   ② **整组不吸附**   ⇒ 位移一致，但落点是带小数的（整块自由平移）
//   ③ **整组不刚性**   ⇒ 11 个节点位移不一致（这会直接推翻 FD-4 的「刚体」结论）
import { launch, closePromos, ORIGIN, 读画布坐标, 读当前zoom, 往返拖, 一步复原 } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, BASE } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFG1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

let 开关初始 = null;
let 已框选 = false;

const 浏览器 = await launch();
const page = 浏览器.page;

/** ⭐ 一次读全部节点的画布 x（⛔ 框选状态下 querySelectorAll 会漏读，逐个 data-id 读） */
const 读全部x = (ids) => page.evaluate((list) => {
  const o = {};
  for (const id of list) {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!n) { o[id] = null; continue; }
    const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
    o[id] = t ? Number(t[1]) : null;
  }
  return o;
}, ids);

/** 框选：FD-1 验证过 (12,64)→(1430,735) 能选中 11/11，起点必须在 pane 空白 */
const 框选全部 = async () => {
  await page.mouse.move(12, 64); await page.waitForTimeout(300);
  await page.mouse.down(); await page.waitForTimeout(160);
  for (let i = 1; i <= 20; i++) { await page.mouse.move(12 + (1430 - 12) * i / 20, 64 + (735 - 64) * i / 20); await page.waitForTimeout(60); }
  await page.mouse.up(); await page.waitForTimeout(800);
  await page.mouse.move(720, 170); await page.waitForTimeout(300);
  已框选 = true;
  return page.evaluate((list) => list.filter((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    return n && n.classList.contains('selected');
  }).length, BASE);
};

const 开关 = () => page.evaluate(() => {
  let b = null;
  for (const x of document.querySelectorAll('button')) {
    const r = x.getBoundingClientRect();
    if (r.top < 740 || r.bottom > 810 || r.left > 340) continue;
    if ((x.getAttribute('aria-label') || '').includes('网格吸附')) { b = x; break; }
  }
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return { svg数: b.querySelectorAll('svg').length, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
});

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 150));
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(4000);
  const g = await 开关(); 开关初始 = g?.svg数 ?? 1;
  const z = await 读当前zoom(page);
  记(`zoom=${z}｜开关 svg=${开关初始}（1=关/吸附态）｜${BASE.length} 个节点的 x 基线 ${JSON.stringify(Object.values(坐标).map((v) => v[0]))}`);

  // ① 框选
  const 选中 = await 框选全部();
  记(`—— ① 框选：选中 ${选中}/${BASE.length} 个 ——`);
  if (选中 < 3) throw new Error(`框选只选中 ${选中} 个，无法做整组拖动`);
  const 前 = await 读全部x(BASE);
  R.读数.拖前 = 前;

  // ② 关态下整组拖：选一个「框内没有 nodrag 祖先」的落点（框选态下 elementFromPoint 被选区层挡住，
  //    所以直接用节点框中心 —— FD-4 证实框选后从节点框中心发起就能整组移动）
  const 抓手 = await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    return { x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2), 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }, 'v-oZNpH99MtM');
  记(`   抓手 ${JSON.stringify(抓手)}`);

  const 总屏px = 80, 帧数 = 40;
  const 采样 = async (dx) => {
    const 轨迹 = [];
    await page.mouse.move(抓手.x, 抓手.y); await page.waitForTimeout(300);
    await page.mouse.down(); await page.waitForTimeout(160);
    for (let i = 1; i <= 帧数; i++) {
      await page.mouse.move(抓手.x + (dx * i) / 帧数, 抓手.y);
      await page.waitForTimeout(170);
      轨迹.push(await 读全部x(BASE));
    }
    await page.mouse.up(); await page.waitForTimeout(620);
    await page.mouse.move(720, 170); await page.waitForTimeout(240);
    return 轨迹;
  };

  记('—— ② 关态整组拖 +80 屏px（40 帧 × 2px）——');
  const 去 = await 采样(总屏px);
  const 后 = await 读全部x(BASE);
  const 位移 = {};
  let 有效 = 0;
  for (const id of BASE) if (前[id] != null && 后[id] != null) { 位移[id] = Number((后[id] - 前[id]).toFixed(4)); if (Math.abs(位移[id]) > 0.01) 有效++; }
  const 值 = Object.values(位移).filter((v) => Math.abs(v) > 0.01);
  const 区间 = 值.length ? [Math.min(...值), Math.max(...值)] : null;
  const 末帧落点 = 去[去.length - 1];
  const 是12 = (v) => Math.abs(v - Math.round(v / 12) * 12) < 0.02;
  记(`   动了 ${有效}/${BASE.length} 个｜位移集合 ${JSON.stringify([...new Set(值)].slice(0, 8))}｜区间 ${JSON.stringify(区间)}｜宽度 ${区间 ? Number((区间[1] - 区间[0]).toFixed(4)) : null}`);
  记(`   末帧落点是 12 的倍数？ ${BASE.filter((id) => 末帧落点[id] != null).filter((id) => 是12(末帧落点[id])).length}/${BASE.length}`);
  R.读数.去程 = { 位移, 末帧落点, 有效节点数: 有效 };

  // ③ 往返回程（⛔ 拖回时抓手位置会变，重读）
  记('—— ③ 往返回程 −80 屏px ——');
  const 抓手2 = await page.evaluate((id) => {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!n) return null;
    const r = n.getBoundingClientRect();
    return { x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2) };
  }, 'v-oZNpH99MtM');
  await page.mouse.move(抓手2.x, 抓手2.y); await page.waitForTimeout(300);
  await page.mouse.down(); await page.waitForTimeout(160);
  for (let i = 1; i <= 帧数; i++) { await page.mouse.move(抓手2.x - (总屏px * i) / 帧数, 抓手2.y); await page.waitForTimeout(170); }
  await page.mouse.up(); await page.waitForTimeout(620);
  await page.mouse.move(720, 170); await page.waitForTimeout(400);

  // ④ 解除框选 + 读最终坐标
  记('—— ④ 点空白解除框选，再读坐标 ——');
  await page.keyboard.press('Escape'); await page.waitForTimeout(300);
  await page.mouse.click(1432, 745); await page.waitForTimeout(900);
  已框选 = false;
  const 终 = {};
  for (const id of BASE) { const c = await 读画布坐标(page, id); 终[id] = c; }
  const 残差 = {};
  let 最大残差 = 0, 偏个数 = 0;
  for (const id of BASE) {
    if (!终[id]) { 残差[id] = '读不到'; 偏个数++; continue; }
    const d = Number(Math.hypot(终[id][0] - 坐标[id][0], 终[id][1] - 坐标[id][1]).toFixed(3));
    残差[id] = d;
    if (d > 1.5) 偏个数++;
    最大残差 = Math.max(最大残差, d);
  }
  记(`   往返后残差：最大 ${最大残差}｜偏离基线(>1.5) ${偏个数}/${BASE.length} 个`);
  R.读数.往返后残差 = { 残差, 最大残差, 偏个数 };
  await page.screenshot({ path: EVID + 'fg1-01-收尾.png' });
} catch (e) {
  记('❌ 出错：' + (e && e.message ? e.message : String(e)));
} finally {
  try {
    const s = await 开关();
    记(`finally：开关 svg=${s?.svg数}`);
  } catch (e) { /* 读不到就算了 */ }
  try { await page.waitForTimeout(15000); } catch (e) { /* 静置 */ }
  try {
    const 核 = await page.evaluate((基线) => Object.entries(基线).map(([id, [bx, by]]) => {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!n) return { id, 现: null, 偏: '不在 DOM' };
      const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
      if (!t) return { id, 现: null, 偏: '无 transform' };
      const x = parseFloat(t[1]), y = parseFloat(t[2]);
      return Math.hypot(x - bx, y - by) > 1.5 ? { id, 基线: [bx, by], 现: [x, y], 偏: Number(Math.hypot(x - bx, y - by).toFixed(2)) } : null;
    }).filter(Boolean), 坐标);
    记('⭐ 静置 15s 后核对坐标：' + JSON.stringify(核));
    R.读数.核对 = 核;
  } catch (e) { 记('核对失败：' + e); }
  try { await 浏览器.browser.close(); } catch (e) { /* 关 */ }
  记('done');
}
