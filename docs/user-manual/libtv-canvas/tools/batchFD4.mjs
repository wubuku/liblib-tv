// ⭐⭐⭐⭐⭐ Batch FD-4：这层「虚线遮罩」到底是什么 + 框选后拖动是不是整组移动
//
// FD-3 找到了 FD-2「找不到可拖落点」的根因，118 个候选落点全部命中同一层：
//   <DIV class="absolute inset-0 rounded-lg border-dashed">
//     ↑ <DIV class="pointer-events-none absolute z-30">
//       ↑ <DIV class="react-flow light">
// ⭐⭐⭐ `absolute inset-0` = 铺满整个画布，`z-30` = 盖在所有节点之上
//     ⇒ **框选之后整块画布被一层虚线遮罩盖住**，任何 `elementFromPoint` 都命中它。
//     这也解释了 EZ 那条「框选才弹多选工具条」—— 框选确实多了一层东西。
//
// 三个问题一次问完：
//   ① 这层遮罩在什么条件下出现？（点选 1 个 / 框选 2 个 / 框选 11 个 / 全不选）
//   ② 它的完整读数：class、z-index、框、里面有没有文字、兄弟元素有哪些
//   ③ ⭐ 在它上面拖动会发生什么 —— 整组移动？投放？还是吞掉？
//      ⚠️ 安全：松手位置**选在空白区**，绝不落在任何节点上，
//         免得触发「把节点投放进另一个节点」这类会新建对象/连线的操作。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFD4.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;
const 读 = (id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return { 画布: t ? [Number(t[1]), Number(t[2])] : null, 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 选中: n.classList.contains('selected') };
}, id);
const 选中数 = () => page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
/** ⭐ 那层虚线遮罩的完整读数 */
const 遮罩读数 = () => page.evaluate(() => {
  const 找 = [...document.querySelectorAll('div')].filter((d) => /border-dashed/.test(d.getAttribute('class') || ''));
  if (!找.length) return { 有: false };
  const e = 找[找.length - 1];
  const r = e.getBoundingClientRect();
  const 父 = e.parentElement;
  const pr = 父 ? 父.getBoundingClientRect() : null;
  return {
    有: true,
    个数: 找.length,
    框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)],
    尺寸: [Math.round(r.width), Math.round(r.height)],
    class: e.getAttribute('class'),
    计算: (() => { const c = getComputedStyle(e); return { zIndex: c.zIndex, pointerEvents: c.pointerEvents, border: c.border, display: c.display, opacity: c.opacity }; })(),
    父class: 父 ? (父.getAttribute('class') || '') : null,
    父框: pr ? [Math.round(pr.left), Math.round(pr.top), Math.round(pr.width), Math.round(pr.height)] : null,
    父z: 父 ? getComputedStyle(父).zIndex : null,
    文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120) || '（空）',
    兄弟: 父 ? [...父.children].map((c) => (c.getAttribute('class') || c.tagName).slice(0, 60)) : [],
  };
});
const 画布层 = () => page.evaluate(() => {
  // 那个 z-30 的层里，除了遮罩还有什么（多选工具条大概在这层）
  const 层 = [...document.querySelectorAll('div')].find((d) => /pointer-events-none absolute z-30/.test(d.getAttribute('class') || ''));
  if (!层) return null;
  return {
    框: (() => { const r = 层.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; })(),
    子元素: [...层.children].map((c) => {
      const r = c.getBoundingClientRect();
      return { class: (c.getAttribute('class') || '').slice(0, 60), 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 文字: (c.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) };
    }),
  };
});

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(12000);
  await closePromos(page);
  const 关 = await page.evaluate(() => {
    const el = [...document.querySelectorAll('div.fixed')].find((d) => /Agent 已升级为 TV Director/.test(d.innerText || ''));
    const btn = el && [...el.querySelectorAll('button')].find((b) => /知道了/.test(b.innerText || ''));
    if (!btn) return null;
    const r = btn.getBoundingClientRect();
    return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)];
  });
  if (关) { await page.mouse.move(关[0], 关[1]); await page.waitForTimeout(320); await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(1000); }
  await page.mouse.move(720, 300); await page.waitForTimeout(500);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(4000);

  // ① 四种状态各读一次
  记('—— ① 那层虚线遮罩在什么条件下出现 ——');
  记(`   【全不选】.selected=${await 选中数()}｜遮罩 ${JSON.stringify(await 遮罩读数())}`);
  R.读数.全不选 = await 遮罩读数();

  // 点选 1 个
  const s0 = await 读('v-oZNpH99MtM');
  await page.mouse.move(s0.框[0] + 20, s0.框[1] + 20); await page.waitForTimeout(300);
  await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(700);
  await page.mouse.move(720, 300); await page.waitForTimeout(400);
  const 单选 = await 遮罩读数();
  记(`   【点选 1 个】.selected=${await 选中数()}｜遮罩有？ ${单选.有} ${单选.有 ? JSON.stringify(单选.框) + ' 文字「' + 单选.文字 + '」' : ''}`);
  R.读数.单选 = 单选;

  // 框选 2 个（只框住左边两个）
  await page.mouse.move(12, 500); await page.waitForTimeout(300);
  await page.mouse.down(); await page.waitForTimeout(140);
  for (let i = 1; i <= 8; i++) { await page.mouse.move(Math.round(12 + (700 * i) / 8), Math.round(500 + (240 * i) / 8)); await page.waitForTimeout(130); }
  await page.mouse.up(); await page.waitForTimeout(900);
  await page.mouse.move(720, 300); await page.waitForTimeout(400);
  const 两选 = await 遮罩读数();
  const 层2 = await 画布层();
  记(`   【框选 2 个】.selected=${await 选中数()}｜遮罩有？ ${两选.有}`);
  if (两选.有) {
    记(`      class = ${两选.class}`);
    记(`      框 ${JSON.stringify(两选.框)}｜尺寸 ${JSON.stringify(两选.尺寸)}`);
    记(`      计算样式 ${JSON.stringify(两选.计算)}`);
    记(`      父 class = ${两选.父class}｜父框 ${JSON.stringify(两选.父框)}｜父 z-index = ${两选.父z}`);
    记(`      遮罩内文字「${两选.文字}」`);
    记(`      ⭐ 遮罩个数 ${两选.个数}`);
  }
  if (层2) 记(`      ⭐ z-30 层里的子元素：${JSON.stringify(层2.子元素)}`);
  R.读数.两选 = 两选; R.读数.z30层 = 层2;
  await page.screenshot({ path: EVID + 'fd4-01-框选两个.png' });

  // ② 框选 11 个
  记('—— ② 框选全部 11 个 ——');
  await page.mouse.move(12, 64); await page.waitForTimeout(320);
  await page.mouse.down(); await page.waitForTimeout(140);
  for (let i = 1; i <= 10; i++) { await page.mouse.move(Math.round(12 + (1418 * i) / 10), Math.round(64 + (671 * i) / 10)); await page.waitForTimeout(130); }
  await page.mouse.up(); await page.waitForTimeout(900);
  await page.mouse.move(720, 300); await page.waitForTimeout(400);
  const 全选 = await 遮罩读数();
  const 层3 = await 画布层();
  记(`   .selected = ${await 选中数()}｜遮罩 ${JSON.stringify(全选.框)}｜z-30 框 ${JSON.stringify(层3 && 层3.框)}`);
  记(`   ⭐ z-30 层里的子元素：${JSON.stringify(层3 && 层3.子元素)}`);
  R.读数.全选 = 全选; R.读数.z30层全选 = 层3;
  await page.screenshot({ path: EVID + 'fd4-02-框选全部.png' });

  // ③ 在遮罩上拖，松手落在空白区
  记('—— ③ 在遮罩上拖 +1100 屏px（松手落在空白区）——');
  const 靶 = await 读('a-GgqvrVz0pw');
  const 起点 = [靶.框[0] + Math.round(靶.框[2] / 2), 靶.框[1] + Math.round(靶.框[3] / 2)];
  const 终点 = [起点[0] + 1100, 起点[1]];
  记(`   起点 ${JSON.stringify(起点)}｜终点 ${JSON.stringify(终点)}`);
  const 终点框集 = [];
  for (const id of Object.keys(坐标)) { const s = await 读(id); if (s) 终点框集.push([id, s.框]); }
  const 终点在节点上 = 终点框集.filter(([, b]) => 终点[0] > b[0] && 终点[0] < b[0] + b[2] && 终点[1] > b[1] && 终点[1] < b[1] + b[3]).map(([id]) => id);
  记(`   ⭐ 终点落在哪些节点上：${JSON.stringify(终点在节点上)} ${终点在节点上.length ? '⛔ 改用空白落点' : '✅ 空白，安全'}`);
  const 落 = 终点在节点上.length ? [起点[0] + 600, 起点[1]] : 终点;
  const 落b = 终点在节点上.length ? [落[0] + 600, 落[1]] : 落;
  const 落集 = 终点在节点上.length ? 落b : 落;
  const 仍在节点 = 终点框集.filter(([, b]) => 落集[0] > b[0] && 落集[0] < b[0] + b[2] && 落集[1] > b[1] && 落集[1] < b[1] + b[3]).map(([id]) => id);
  记(`   实际落点 ${JSON.stringify(落集)}｜其上有节点：${JSON.stringify(仍在节点)} ${仍在节点.length ? '⛔ 放弃拖拽' : '✅ 空白'}`);

  if (!仍在节点.length) {
    const 前 = await 读全部坐标(page);
    await page.mouse.move(起点[0], 起点[1]); await page.waitForTimeout(320);
    await page.mouse.down(); await page.waitForTimeout(160);
    for (let i = 1; i <= 10; i++) { await page.mouse.move(Math.round(起点[0] + ((落集[0] - 起点[0]) * i) / 10), 起点[1]); await page.waitForTimeout(150); }
    await page.mouse.up(); await page.waitForTimeout(900);
    await page.mouse.move(720, 300); await page.waitForTimeout(500);
    const 后 = await 读全部坐标(page);
    const 位移 = {};
    for (const id of Object.keys(坐标)) if (前[id] && 后[id]) 位移[id] = Number((后[id][0] - 前[id][0]).toFixed(3));
    const 动了 = Object.entries(位移).filter(([, d]) => Math.abs(d) > 0.5);
    记(`   ⭐⭐⭐ 动了 ${动了.length} 个 / ${Object.keys(位移).length} 个`);
    记('      ' + JSON.stringify(位移));
    const xs = 动了.map(([, d]) => d);
    if (xs.length) {
      记(`   ⭐⭐⭐⭐ 位移区间 ${Math.min(...xs).toFixed(3)} ~ ${Math.max(...xs).toFixed(3)}｜**完全一致？ ${(Math.max(...xs) - Math.min(...xs)) < 0.5}**`);
      R.读数.整组位移 = 位移; R.搬移量 = xs[0];
    } else 记('   ⛔ 一个都没动 ⇒ 遮罩把拖拽吞掉了');
    const 新遮罩 = await 遮罩读数();
    记(`   拖完之后遮罩还有？ ${新遮罩.有}`);
    await page.screenshot({ path: EVID + 'fd4-03-遮罩上拖后.png' });
  }
} catch (e) {
  R.错误 = String((e && e.stack) || e);
  记('❌ ' + e.message);
} finally {
  if (R.搬移量) {
    记('—— finally：原样拖回 ——');
    const z = await page.evaluate(() => {
      const v = document.querySelector('.react-flow__viewport');
      const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
      return m ? Number(m[1].split(',')[0]) : 1;
    });
    for (let 轮 = 1; 轮 <= 5; 轮++) {
      const 前 = await 读全部坐标(page);
      const 偏 = Object.entries(坐标).map(([id, xy]) => ({ id, d: 前[id] ? Number((前[id][0] - xy[0]).toFixed(3)) : 99999 })).filter((o) => Math.abs(o.d) > 0.5);
      if (!偏.length) { 记(`   ✅ 复原到位（轮 ${轮}）`); break; }
      const 宽 = Math.max(...偏.map((o) => o.d)) - Math.min(...偏.map((o) => o.d));
      记(`   轮${轮}：偏 ${偏.length} 个，位移宽度 ${宽.toFixed(3)}`);
      if (宽 >= 0.5) { 记('   ⛔ 位移不一致，停止'); break; }
      const s = await 读(偏[0].id); if (!s) break;
      const 起点 = [s.框[0] + Math.round(s.框[2] / 2), s.框[1] + Math.round(s.框[3] / 2)];
      let px = Math.round(-R.搬移量 / z);
      if (Math.abs(px) < 4) px = -R.搬移量 > 0 ? 5 : -5;
      await page.mouse.move(起点[0], 起点[1]); await page.waitForTimeout(300);
      await page.mouse.down(); await page.waitForTimeout(150);
      for (let i = 1; i <= 10; i++) { await page.mouse.move(Math.round(起点[0] + (px * i) / 10), 起点[1]); await page.waitForTimeout(150); }
      await page.mouse.up(); await page.waitForTimeout(700);
      await page.mouse.move(720, 300); await page.waitForTimeout(300);
      记(`   拖 ${px}px → ${JSON.stringify((await 读全部坐标(page))[偏[0].id])}`);
    }
  }
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 全 = await 读全部坐标(page);
  const 残 = Object.entries(坐标).filter(([id, xy]) => {
    const n = 全[id]; return !n || Math.hypot(n[0] - xy[0], n[1] - xy[1]) > 0.5;
  }).map(([id, xy]) => `${id} 基线${JSON.stringify(xy)} 现${JSON.stringify(全[id] || '未渲染')}`);
  记('⭐⭐ 静置 15s 后坐标复核：' + (残.length ? JSON.stringify(残) : '[]（全部一致）'));
  R.收尾 = 残;
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchFD4.json ===');
}
