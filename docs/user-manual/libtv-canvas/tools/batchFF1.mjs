// ⭐⭐⭐⭐⭐ Batch FF-1：「12 格」是**画布单位**还是**屏幕像素**？
//
// 手册里长期挂着一个 📖：FB 记的吸附格距 12 一直没在别的缩放级别上复验过。
// ⭐ 这个问题的两种答案给出**互斥的预测**，一次实验就能分开：
//
//   假设 A：格距是 **12 个画布单位**（画布坐标系的固定刻度，与缩放无关）
//     ⇒ 任何缩放下，相邻两个落点的**间距都恒等于 12 个画布单位**
//   假设 B：格距是 **12 个屏幕像素**（跟着缩放换算）
//     ⇒ zoom 越小，12 像素代表的画布单位越多：20% 时 1 屏px = 5 单位 ⇒ 间距会是 **60**
//
// ⭐ 所以判据就是一句话：**量「相邻落点的间距」，看它是不是恒等于 12。**
// 20% 档区分度最高（12 vs 60，差 5 倍），50% 次之（12 vs 24）。
//
// ⛔⭐⭐⭐ 本轮最重要的工程约束（Batch FE 血的教训）：
//   **全程先确保「网格吸附」是关的（吸附态）做实验，收尾前切到开态再复原。**
//   ⛔ 吸附态下的多轮迭代复原会发散 —— FE-2 就是这么把 11 个节点推出画布的。
//   ⇒ 这里的复原分两步：① 往返法把位移抵消掉；② 仍有余差就先**切成开态**再闭环复原；
//     ③ 最后无条件点回关态（目标 svg 数 = 1）。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFF1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const ID = 'v-oZNpH99MtM';
let Z = 0.48;
let 开关初始 = null;
let 已拖动 = false;

const 浏览器 = await launch();
const page = 浏览器.page;

const 读zoom = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
  return m ? Number(m[1].split(',')[0]) : 1;
});
const 读 = (id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return { 画布: t ? [Number(t[1]), Number(t[2])] : null, 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 屏宽: Math.round(r.width) };
}, id);
const 扫落点 = async (id) => {
  const s = await 读(id);
  if (!s || !s.框) return [];
  const [L, T, W, H] = s.框;
  const 好 = [];
  for (let r = 0; r < 6; r++) for (let c = 0; c < 6; c++) {
    const x = L + Math.round(W * (c + 0.5) / 6), y = T + Math.round(H * (r + 0.5) / 6);
    if (x < 4 || x > 1436 || y < 4 || y > 806) continue;
    const ok = await page.evaluate((p) => {
      const e = document.elementFromPoint(p[0], p[1]);
      const n = e ? e.closest('.react-flow__node') : null;
      return !!(n && !e.closest('.nodrag') && n.getAttribute('data-id') === p[2]);
    }, [x, y, id]);
    if (ok) 好.push({ x, y });
  }
  return 好;
};
const 逐帧拖 = async (id, p, 总dx, 帧数) => {
  const 起 = (await 读(id)).画布;
  const 轨迹 = [];
  await page.mouse.move(p.x, p.y); await page.waitForTimeout(300);
  await page.mouse.down(); await page.waitForTimeout(160);
  for (let i = 1; i <= 帧数; i++) {
    await page.mouse.move(Math.round(p.x + (总dx * i) / 帧数), p.y);
    await page.waitForTimeout(170);
    轨迹.push((await 读(id)).画布[0]);
  }
  await page.mouse.up(); await page.waitForTimeout(620);
  await page.mouse.move(720, 170); await page.waitForTimeout(240);
  已拖动 = true;
  return { 轨迹, 起, 后: (await 读(id)).画布[0] };
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
const 点开关 = async () => {
  const g = await 开关();
  if (!g) return null;
  await page.mouse.move(g.中心[0], g.中心[1]); await page.waitForTimeout(300);
  await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(900);
  await page.mouse.move(720, 170); await page.waitForTimeout(400);
  return 开关();
};
/** ⭐ 用缩放菜单顶部的「缩放比例」输入框设档。传 null = 不动缩放，用当前档。 */
const 设缩放 = async (百分数) => {
  if (百分数 === null || 百分数 === undefined) return { ok: true, zoom: await 读zoom(), 原样: true };
  const 标签 = await page.evaluate(() => {
    for (const x of document.querySelectorAll('button,[role="button"]')) {
      const r = x.getBoundingClientRect();
      if (r.bottom < 740 || r.top > 810 || r.left > 340) continue;
      if (/^\d+%$/.test((x.innerText || '').trim())) return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
    }
    return null;
  });
  if (!标签) return { ok: false, 原因: '找不到左下角百分比标签' };
  await page.mouse.click(标签[0], 标签[1]); await page.waitForTimeout(900);
  const 框 = await page.evaluate(() => {
    const el = document.querySelector('input[aria-label="缩放比例"]')
      || [...document.querySelectorAll('input')].find((i) => (i.getAttribute('aria-label') || '').includes('缩放比例'));
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return r.width > 0 ? [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] : null;
  });
  if (!框) { await page.keyboard.press('Escape'); await page.waitForTimeout(300); return { ok: false, 原因: '菜单里没有「缩放比例」输入框' }; }
  await page.mouse.click(框[0], 框[1]); await page.waitForTimeout(200);
  await page.keyboard.press('Meta+a'); await page.waitForTimeout(120);
  await page.keyboard.type(String(百分数)); await page.waitForTimeout(200);
  await page.keyboard.press('Enter'); await page.waitForTimeout(1600);
  await page.keyboard.press('Escape'); await page.waitForTimeout(500);
  return { ok: true, zoom: await 读zoom() };
};
/** ⭐⭐ 关态下走 40 帧，量「相邻落点的间距」 */
const 量一档 = async (名, 目标百分数) => {
  const 设 = await 设缩放(目标百分数);
  if (!设.ok) { 记(`   ⛔ ${名} 设缩放失败：${设.原因}`); return { 名, 失败: 设.原因 }; }
  const z = await 读zoom();
  const 落 = await 扫落点(ID);
  if (!落.length) { 记(`   ⛔ ${名} zoom=${z} 框内找不到干净落点（节点在屏幕上太小：屏宽 ${(await 读(ID)).屏宽}px）`); return { 名, zoom: z, 失败: '无落点' }; }
  const p = 落[Math.floor(落.length / 2)];
  const r = await 逐帧拖(ID, p, 80, 40);   // 80 屏 px，40 帧 × 2px
  const 不同 = [...new Set(r.轨迹)].sort((a, b) => a - b);
  const 间距 = 不同.slice(1).map((v, i) => Number((v - 不同[i]).toFixed(4)));
  const 间距集合 = [...new Set(间距)].sort((a, b) => a - b);
  const 屏宽 = (await 读(ID)).屏宽;
  return {
    名, 目标百分数, zoom: z, 屏宽,
    落点: p, 不同坐标个数: 不同.length, 不同坐标: 不同,
    间距集合, 理论_若画布单位: 12, 理论_若屏幕像素: Number((12 / z).toFixed(3)),
    全是12的倍数: 间距.every((d) => Math.abs(d - Math.round(d / 12) * 12) < 0.02),
    起: r.起, 净位移: Number((r.后 - r.起[0]).toFixed(4)),
  };
};

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(13000);
  记('closePromos：' + JSON.stringify(await closePromos(page)).slice(0, 160));
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(4000);
  const s0 = await 开关(); 开关初始 = s0?.svg数 ?? 1;
  Z = await 读zoom();
  记(`起点 zoom=${Z}（⌘0）｜开关 svg=${开关初始}｜${ID} 基线 ${JSON.stringify(坐标[ID])}`);

  const 档 = [];
  // ① ⌘0 那一档（当对照）
  记('—— ① ⌘0 档（对照）——');
  const a0 = await 量一档('⌘0', null);
  记(`   zoom=${a0.zoom}｜不同坐标 ${a0.不同坐标个数} 个｜间距集合 ${JSON.stringify(a0.间距集合)}`);
  档.push(a0);
  // 往返回程
  let l = await 扫落点(ID); await 逐帧拖(ID, l[Math.floor(l.length / 2)], -80, 40);

  // ② 20%
  记('—— ② 20% 档（区分度最高：画布单位说 12，屏幕像素说 60）——');
  const a1 = await 量一档('20%', 20);
  记(`   zoom=${a1.zoom}｜屏宽=${a1.屏宽}｜不同坐标 ${a1.不同坐标个数} 个｜间距集合 ${JSON.stringify(a1.间距集合)}`);
  档.push(a1);
  if (a1.不同坐标个数) { l = await 扫落点(ID); await 逐帧拖(ID, l[Math.floor(l.length / 2)], -80, 40); }

  // ③ 50%
  记('—— ③ 50% 档（画布单位说 12，屏幕像素说 24）——');
  const a2 = await 量一档('50%', 50);
  记(`   zoom=${a2.zoom}｜屏宽=${a2.屏宽}｜不同坐标 ${a2.不同坐标个数} 个｜间距集合 ${JSON.stringify(a2.间距集合)}`);
  档.push(a2);
  if (a2.不同坐标个数) { l = await 扫落点(ID); await 逐帧拖(ID, l[Math.floor(l.length / 2)], -80, 40); }

  // ④ 回 ⌘0
  await page.keyboard.press('Meta+0'); await page.waitForTimeout(3500);
  Z = await 读zoom();
  记(`—— ④ 回 ⌘0，zoom=${Z} ——`);

  R.读数 = { zoom起点: Z, 开关初始, 档 };
  const 表 = 档.filter((d) => d.间距集合);
  if (表.length >= 2) {
    记('—— 判据汇总 ——');
    for (const d of 表) 记(`   ${d.名}：zoom=${d.zoom}｜间距 ${JSON.stringify(d.间距集合)}｜若是画布单位应为 12，若是屏幕像素应为 ${d.理论_若屏幕像素}`);
  }
  await page.screenshot({ path: EVID + 'ff1-01-收尾.png' });
} catch (e) {
  记('❌ 出错：' + (e && e.message ? e.message : String(e)));
} finally {
  // ⭐⭐⭐ FE 教训：复原前先切成开态（不吸附），否则多轮迭代必然发散
  try {
    if (已拖动) {
      const s = await 开关();
      if (s && s.svg数 === 1) { const b = await 点开关(); 记(`finally：先切成开态 svg ${s.svg数} → ${b?.svg数}`); }
      for (let 轮 = 1; 轮 <= 16; 轮++) {
        const st = await 读(ID);
        if (!st || !st.画布) { 记('finally：节点读不到，停止'); break; }
        const dx = 坐标[ID][0] - st.画布[0], dy = 坐标[ID][1] - st.画布[1];
        if (Math.hypot(dx, dy) < 0.5) { 记(`finally 复原完成：${轮 - 1} 轮，终点 ${JSON.stringify(st.画布)}`); break; }
        const z = await 读zoom();
        let px = Math.round((dx - Math.sign(dx) * Math.min(6, Math.abs(dx) / 6)) / z);
        if (dx !== 0 && Math.abs(px) < 6) px = dx > 0 ? 7 : -7;
        let py = Math.round((dy - Math.sign(dy) * Math.min(6, Math.abs(dy) / 6)) / z);
        if (dy !== 0 && Math.abs(py) < 6) py = dy > 0 ? 7 : -7;
        if (px === 0 && py === 0) py = 7;
        const 落 = await 扫落点(ID);
        if (!落.length) { 记('finally：找不到落点，停止'); break; }
        await 逐帧拖(ID, 落[Math.floor(落.length / 2)], px, Math.max(3, Math.round(Math.abs(px) / 3)));
        记(`   复原轮${轮}：${JSON.stringify(st.画布)} → ${JSON.stringify((await 读(ID)).画布)}（拖 ${px},${py}px @zoom ${z}）`);
        if (轮 === 16) 记('⛔ 复原轮数用完');
      }
    } else 记('finally：没拖过');
    const s = await 开关();
    if (s && s.svg数 !== 开关初始) { const b = await 点开关(); 记(`finally 点回开关 svg ${s.svg数} → ${b?.svg数}（目标 ${开关初始}）`); }
    else 记(`finally：开关已是 svg=${s?.svg数}`);
  } catch (e) { 记('finally 出错：' + (e && e.message ? e.message : String(e))); }
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
  } catch (e) { 记('核对失败：' + e); }
  try { await 浏览器.browser.close(); } catch (e) { /* 关 */ }
  记('done');
}
