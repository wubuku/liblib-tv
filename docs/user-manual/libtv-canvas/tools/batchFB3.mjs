// Batch FB-3：⭐⭐⭐ 用**行为**判据回答「网格吸附到底有没有在吸附」
//
// 前两轮翻的车：
//   FB-1 拿「节点坐标离 35 整数倍多近」当吸附判据 ⇒ 报出导演台只差 0.03
//   FB-2 拿 `<pattern patternTransform>` 当网格线原点 ⇒ 换算成 -17.5
//   fb3 探针查清了：那个 pattern 画的是 **`<circle class="…dots">` 圆点阵**，
//   步长 35 画布单位、圆半径 0.5、**相位随视口平移跳变**
//   ⇒ 「35 的整数倍」根本不是画布里存在的格线，「离它多近」与吸不吸附无关。
//
// ⛔ 而且「网格吸附」按钮点完**四层 DOM 逐项零变化**（class/aria/aria-pressed/计算样式），
//   背景也不变 ⇒ 按钮外观**不承载**开关状态，FB-1「没翻面」的说法本身也是错的判据。
//
// 本轮只信行为：
//   ① 连续整数像素微拖 +1px ×10 / +3px ×10，**把每一个落点都记下来**再离线判量化
//   ② 三重判据同时上：无量化 ⇒ 没吸附；有固定格距 ⇒ 吸附；按住 Alt 拖分布不同 ⇒ 确证
//   ③ 再点一次按钮，用**完整 outerHTML 归一化 diff**（不是只比 4 个字段）确认外观是否真的一点不变
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 读全部坐标, 坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const OUT = HERE + 'batchFB3.json';
const 落盘 = (o) => writeFileSync(OUT, JSON.stringify(o, null, 2));
const R = { 读数: {}, 步骤: [] };
const 记 = (s) => { R.步骤.push(s); 落盘(R); console.log('· ' + s); };
const 目标 = ['n-56F19pXVB4', 't-UtVx3lZmrV'];

const 浏览器 = await launch();
const page = 浏览器.page;

/** 读一个节点的画布坐标 + 屏幕中心 */
const 读点 = (id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return {
    画布: t ? [Number(t[1]), Number(t[2])] : null,
    中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
  };
}, id);

const zoom = () => page.evaluate(() => {
  const v = document.querySelector('.react-flow__viewport');
  const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
  return m ? Number(m[1].split(',')[0]) : 1;
});

/** 拖整数像素；返回是否成功。落点必须自证。alt=true 时按住 Alt。 */
const 拖 = async (id, dx, dy, alt) => {
  const s = await 读点(id);
  if (!s || !s.中心) return { 错: '读不到节点' };
  await page.mouse.move(s.中心[0], s.中心[1]);
  await page.waitForTimeout(320);
  const v = await page.evaluate(([p, nid]) => {
    const e = document.elementFromPoint(p[0], p[1]);
    const n = e ? e.closest('.react-flow__node') : null;
    return n ? n.getAttribute('data-id') : 'null';
  }, [s.中心, id]);
  if (v !== id) return { 错: `落点是 ${v}，不是 ${id}` };
  if (alt) await page.keyboard.down('Alt');
  await page.mouse.down(); await page.waitForTimeout(150);
  await page.mouse.move(s.中心[0] + dx, s.中心[1] + dy, { steps: 5 });
  await page.waitForTimeout(260);
  await page.mouse.up();
  if (alt) await page.keyboard.up('Alt');
  await page.waitForTimeout(520);
  await page.mouse.move(720, 200); await page.waitForTimeout(260);
  return { 成功: true };
};

/** 按钮完整 outerHTML（去空白归一化） */
const 按钮全 = () => page.evaluate(() => {
  let b = null;
  for (const x of document.querySelectorAll('button')) {
    const r = x.getBoundingClientRect();
    if (r.top < 740 || r.bottom > 810 || r.left > 340) continue;
    if ((x.getAttribute('aria-label') || '').includes('网格吸附')) { b = x; break; }
  }
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return {
    外链: b.outerHTML.replace(/\s+/g, ' ').trim(),
    框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
    中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)],
  };
});

/** 离最近「p 的整数倍」有多远 */
const 距格 = (v, p, 相位) => Math.abs(((v - 相位) / p) - Math.round((v - 相位) / p)) * p;

/** 一串 +1px 或 +3px 的微拖，把每个落点记下来 */
const 探针 = async (id, 步长, 次数, alt) => {
  const 落点 = [];
  let 前 = (await 读点(id)).画布;
  for (let i = 0; i < 次数; i++) {
    const r = await 拖(id, 步长, 0, alt);
    if (!r || !r.成功) { 落点.push({ i, 失败: r }); break; }
    const 后 = (await 读点(id)).画布;
    落点.push({ i, 画布: 后, 增量: Number((后[0] - 前[0]).toFixed(4)) });
    前 = 后;
  }
  return 落点;
};

let 动过 = [];
try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  const z = await zoom();
  记(`⭐ zoom = ${z}｜1 屏幕像素 = ${(1 / z).toFixed(4)} 画布单位`);
  R.读数.zoom = z;

  for (const id of 目标) 动过.push([id, (await 读点(id)).画布.slice()]);

  // ---------- ③ 完整 outerHTML 对照 ----------
  记('—— 开关外观：完整 outerHTML 归一化 diff ——');
  const g0 = await 按钮全();
  await page.screenshot({ path: EVID + 'fb3-01-吸附开前-整屏.png' });
  const 截0 = await page.screenshot({ clip: { x: g0.框[0] - 130, y: g0.框[1] - 8, width: 260, height: 44 } });
  writeFileSync(EVID + 'fb3-02-吸附按钮-点击前.png', 截0);
  await page.mouse.move(g0.中心[0], g0.中心[1]); await page.waitForTimeout(400);
  await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(1000);
  await page.mouse.move(720, 200); await page.waitForTimeout(600);
  const g1 = await 按钮全();
  const 截1 = await page.screenshot({ clip: { x: g1.框[0] - 130, y: g1.框[1] - 8, width: 260, height: 44 } });
  writeFileSync(EVID + 'fb3-03-吸附按钮-点击后.png', 截1);
  记('  外链完全相同？ ' + (g0.外链 === g1.外链));
  记('  前：' + g0.外链);
  记('  后：' + g1.外链);
  R.读数.按钮前 = g0.外链; R.读数.按钮后 = g1.外链;

  // ---------- ① 微拖落点序列（导演台：不被遮挡的角落区）----------
  const id = 'n-56F19pXVB4';
  记(`—— ① 微拖落点序列：${id} ——`);
  const 细 = await 探针(id, 1, 10, false);
  记('  细探（+1px ×10）每次画布增量：' + JSON.stringify(细.map((d) => d.增量)));
  const 粗 = await 探针(id, 3, 10, false);
  记('  粗探（+3px ×10）每次画布增量：' + JSON.stringify(粗.map((d) => d.增量)));
  R.读数.细 = 细; R.读数.粗 = 粗;

  const 全部落点 = [...细, ...粗].filter((d) => d.画布).map((d) => d.画布[0]);
  const 增量集 = [...细, ...粗].filter((d) => typeof d.增量 === 'number').map((d) => d.增量);
  记('  ⭐ 增量取值集合 = ' + JSON.stringify([...new Set(增量集)].sort((a, b) => a - b)));
  记(`  ⭐ 期望的**无吸附**增量：+1px → ${(1 / z).toFixed(4)}，+3px → ${(3 / z).toFixed(4)}`);
  for (const p of [5, 10, 15, 20, 25, 35, 50]) {
    const 残 = 全部落点.map((v) => Number(距格(v, p, 0).toFixed(3)));
    记(`  判据 p=${String(p).padStart(2)}（相位 0）：离格距离 min=${Math.min(...残).toFixed(3)} max=${Math.max(...残).toFixed(3)}｜<0.5 的有 ${残.filter((r) => r < 0.5).length}/${残.length}`);
  }
  R.读数.增量集 = [...new Set(增量集)].sort((a, b) => a - b);

  // ---------- ② 按住 Alt ----------
  记('—— ② 按住 Alt 再拖 6 次 ——');
  const alt落 = await 探针(id, 3, 6, true);
  记('  Alt 增量：' + JSON.stringify(alt落.map((d) => d.增量)));
  R.读数.Alt = alt落;

  await page.screenshot({ path: EVID + 'fb3-04-微拖之后-整屏.png' });
  记('已拍 fb3-01/02/03/04');
} catch (e) {
  R.错误 = String((e && e.stack) || e);
  记('❌ ' + e.message);
} finally {
  if (动过.length) {
    记('—— finally：复原 ——');
    for (const [id, 原位] of 动过) {
      try {
        for (let 轮 = 1; 轮 <= 30; 轮++) {
          const s = await 读点(id);
          if (!s || !s.画布) break;
          const dx = 原位[0] - s.画布[0], dy = 原位[1] - s.画布[1];
          if (Math.hypot(dx, dy) < 0.5) { 记(`  ✅ ${id} 复原到位（轮 ${轮}）→ ${JSON.stringify(s.画布)}`); break; }
          const px_ = Math.max(-8, Math.min(8, Math.round(dx * z)));
          const py = Math.max(-8, Math.min(8, Math.round(dy * z)));
          if (px_ === 0 && py === 0) { 记(`  ⛔ ${id} 整数像素已为 0（剩余 ${Math.hypot(dx, dy).toFixed(3)}）`); break; }
          const r = await 拖(id, px_, py, false);
          if (!r || !r.成功) { 记(`  ⛔ ${id} 复原失败：${JSON.stringify(r)}`); break; }
        }
        const 终 = await 读点(id);
        记(`  ${id} 基线 ${JSON.stringify(坐标[id])} → 现在 ${JSON.stringify(终.画布)}`);
      } catch (e2) { 记('  ⛔ 复原抛错：' + e2.message); }
    }
  }
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 全 = await 读全部坐标(page);
  const 差 = Object.entries(坐标).filter(([id, xy]) => {
    const n = 全[id]; if (!n) return true;
    return Math.hypot(n[0] - xy[0], n[1] - xy[1]) > 0.5;
  }).map(([id, xy]) => `${id} 基线${JSON.stringify(xy)} 现${JSON.stringify(全[id] || '未渲染')}`);
  记('⭐⭐ 静置 15s 后坐标复核：' + (差.length ? JSON.stringify(差) : '[]（全部一致）'));
  R.收尾复核 = 差;
  落盘(R);
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchFB3.json ===');
}
