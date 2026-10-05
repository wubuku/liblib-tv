// ⭐⭐⭐⭐⭐ Batch FD-3：诊断「框选成功后为什么找不到可拖落点」，然后验证整组移动
//
// FD-2 已经拿到两条硬结果：
//   ⭐⭐⭐ **框选 11/11 成功**（起点 (12,64)、终点 (1430,735)，两点都在 pane 空白区）。
//     FD-1 失败的根因就是**起点 (20,30) 落在顶栏里**（`未命名工作区`/`画布 2` 都在 y 8~40），
//     不在 React Flow 的 pane 上，`mouse.down` 根本没打在画布上。
//   ⭐⭐⭐ 那个漏网浮层的真实读数：`<div class="fixed w-[280px] max-w-[calc(100vw-24px)]">`
//     **z-index = 101**（⛔ 不是 PROGRESS 里 📖 记的 `z-[180]` / `z-[305]`），
//     框 `[732,447,280,311]`，文案「Agent 已升级为 TV Director … 知道了」。
//     ⭐ `lib.mjs` 的 `closePromos` 只认 `.mantine-Modal-overlay`，这个不是 Mantine 模态框 ⇒ 关不掉。
//
// FD-2 卡在最后一步：11 个节点都选中了，但**每个节点的 9 个候选落点全部不合格**。
// 本轮把 `elementFromPoint` 的**完整祖先链**倒出来，看它到底命中了什么。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFD3.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;
const 读 = (id) => page.evaluate((nid) => {
  const n = document.querySelector(`.react-flow__node[data-id="${nid}"]`);
  if (!n) return null;
  const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  return { 画布: t ? [Number(t[1]), Number(t[2])] : null, 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 选中: n.classList.contains('selected') };
}, id);
/** ⭐ 完整祖先链：命中了什么、属不属于目标节点、有没有 nodrag、祖先里有没有 selection/pane 类 */
const 命中链 = (p) => page.evaluate(([x, y]) => {
  const e = document.elementFromPoint(x, y);
  if (!e) return null;
  const 链 = [];
  let n = e;
  for (let i = 0; i < 9 && n; i++, n = n.parentElement) {
    链.push({
      标签: n.tagName,
      class: (n.getAttribute('class') || '').slice(0, 95),
      dataId: n.getAttribute('data-id'),
      aria: n.getAttribute('aria-label'),
      选中: n.classList ? n.classList.contains('selected') : null,
    });
  }
  const node = e.closest('.react-flow__node');
  return {
    链,
    属主: node ? node.getAttribute('data-id') : null,
    有nodrag: !!e.closest('.nodrag'),
    nodrag类: e.closest('.nodrag') ? (e.closest('.nodrag').getAttribute('class') || '').slice(0, 80) : null,
    在selection里: !!e.closest('.react-flow__selection'),
    在pane里: !!e.closest('.react-flow__pane'),
  };
}, p);

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(12000);
  await closePromos(page);
  // ⭐ 手动关掉那个非 Mantine 的 TV Director 浮层
  const 关 = await page.evaluate(() => {
    const el = [...document.querySelectorAll('div.fixed')].find((d) => /Agent 已升级为 TV Director/.test(d.innerText || ''));
    if (!el) return null;
    const btn = [...el.querySelectorAll('button')].find((b) => /知道了/.test(b.innerText || ''));
    if (!btn) return { 找到浮层: true, 有按钮: false };
    const r = btn.getBoundingClientRect();
    return { 找到浮层: true, 有按钮: true, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
  });
  记('TV Director 浮层 = ' + JSON.stringify(关));
  if (关 && 关.中心) {
    await page.mouse.move(关.中心[0], 关.中心[1]); await page.waitForTimeout(350);
    await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(1200);
    await page.mouse.move(720, 300); await page.waitForTimeout(600);
    const 还在 = await page.evaluate(() => [...document.querySelectorAll('div.fixed')].some((d) => /Agent 已升级为 TV Director/.test(d.innerText || '')));
    记(`   ⭐ 点「知道了」之后浮层还在？ ${还在}`);
    R.读数.浮层已关 = !还在;
  }
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(4000);

  // 框选（FD-2 验证过的落点）
  const 起 = [12, 64], 落 = [1430, 735];
  await page.mouse.move(起[0], 起[1]); await page.waitForTimeout(320);
  await page.mouse.down(); await page.waitForTimeout(140);
  for (let i = 1; i <= 10; i++) { await page.mouse.move(Math.round(起[0] + ((落[0] - 起[0]) * i) / 10), Math.round(起[1] + ((落[1] - 起[1]) * i) / 10)); await page.waitForTimeout(130); }
  await page.mouse.up(); await page.waitForTimeout(900);
  const n1 = await page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
  记(`⭐⭐ 框选后 .selected = ${n1}`);
  R.读数.选中数 = n1;
  await page.mouse.move(720, 300); await page.waitForTimeout(400);
  await page.screenshot({ path: EVID + 'fd3-01-框选后.png' });

  // ⭐ 诊断：对一个已选节点，dump 中心点的完整祖先链
  记('—— 诊断落点为什么不合格 ——');
  const 各选 = [];
  for (const id of Object.keys(坐标)) { const s = await 读(id); if (s && s.选中) 各选.push([id, s.框]); }
  记('已选：' + JSON.stringify(各选.map((x) => x[0])));
  for (const [id, b] of 各选.slice(0, 3)) {
    const cx = b[0] + Math.round(b[2] / 2), cy = b[1] + Math.round(b[3] / 2);
    const c = await 命中链([cx, cy]);
    记(`   ${id} 中心 (${cx},${cy})：`);
    记(`      属主 = ${c.属主}｜有 nodrag = ${c.有nodrag}${c.nodrag类 ? '（' + c.nodrag类 + '）' : ''}｜在 selection 里 = ${c.在selection里}｜在 pane 里 = ${c.在pane里}`);
    for (const [i, l] of c.链.entries()) 记(`      ${i} <${l.标签} data-id=${l.dataId} selected=${l.选中} class="${l.class}">`);
    R.读数['链_' + id] = c;
  }

  // ⭐ 找可拖落点：这次额外允许「命中 `.nodrag` 但 nodrag 只挂在 handle 上」的情况不算，
  //    并把每个候选点的诊断一起打出来
  let 目标 = null;
  const 候选表 = [];
  for (const [id, b] of 各选) {
    for (const [fc, fr] of [[0.5, 0.5], [0.2, 0.2], [0.5, 0.2], [0.2, 0.5], [0.8, 0.2], [0.8, 0.5], [0.5, 0.8], [0.2, 0.8], [0.8, 0.8], [0.35, 0.35], [0.65, 0.35]]) {
      const x = b[0] + Math.round(b[2] * fc), y = b[1] + Math.round(b[3] * fr);
      if (x < 4 || x > 1436 || y < 4 || y > 730) continue;
      const c = await 命中链([x, y]);
      const 合格 = c && c.属主 === id && !c.有nodrag;
      候选表.push({ id, x, y, 属主: c && c.属主, nodrag: c && c.有nodrag, 合格 });
      if (合格 && !目标) 目标 = [id, { x, y }];
    }
  }
  const 不合格 = 候选表.filter((o) => !o.合格);
  记(`   ⭐ 候选落点共 ${候选表.length} 个，合格 ${候选表.filter((o) => o.合格).length} 个`);
  const 原因 = {};
  for (const o of 不合格) { const k = `${o.属主 || 'null'}|nodrag=${o.nodrag}`; 原因[k] = (原因[k] || 0) + 1; }
  记('   不合格原因分布：' + JSON.stringify(原因));
  R.读数.候选表 = 候选表;
  if (!目标) {
    记('   ⛔ 仍然没有合格落点');
  } else {
    记(`—— 拖 ${目标[0]}，落点 ${JSON.stringify(目标[1])}，位移 +1100 屏 px ——`);
    const 前 = await 读全部坐标(page);
    await page.mouse.move(目标[1].x, 目标[1].y); await page.waitForTimeout(320);
    await page.mouse.down(); await page.waitForTimeout(160);
    for (let i = 1; i <= 10; i++) { await page.mouse.move(Math.round(目标[1].x + (1100 * i) / 10), 目标[1].y); await page.waitForTimeout(150); }
    await page.mouse.up(); await page.waitForTimeout(800);
    await page.mouse.move(720, 300); await page.waitForTimeout(400);
    const 后 = await 读全部坐标(page);
    const 位移 = {};
    for (const id of Object.keys(坐标)) if (前[id] && 后[id]) 位移[id] = Number((后[id][0] - 前[id][0]).toFixed(3));
    const 动了 = Object.entries(位移).filter(([, d]) => Math.abs(d) > 0.5);
    记(`   ⭐⭐⭐ 动了 ${动了.length} 个 / ${Object.keys(位移).length} 个`);
    记('      ' + JSON.stringify(位移));
    const xs = 动了.map(([, d]) => d);
    if (xs.length) {
      记(`   ⭐⭐⭐⭐ 位移区间 ${Math.min(...xs).toFixed(3)} ~ ${Math.max(...xs).toFixed(3)}｜**完全一致？ ${(Math.max(...xs) - Math.min(...xs)) < 0.5}**`);
      R.读数.整组位移 = 位移;
      R.搬移量 = xs[0];
    }
    await page.screenshot({ path: EVID + 'fd3-02-整组拖后.png' });
  }
} catch (e) {
  R.错误 = String((e && e.stack) || e);
  记('❌ ' + e.message);
} finally {
  if (R.搬移量) {
    记('—— finally：把整组原样拖回 ——');
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
      if (宽 >= 0.5) { 记('   ⛔ 各节点位移不一致，停止自动拖'); break; }
      const s = await 读(偏[0].id); if (!s) break;
      const [L, T, W, H] = s.框;
      let p = null;
      for (const [fc, fr] of [[0.5, 0.5], [0.2, 0.2], [0.5, 0.2], [0.2, 0.5], [0.8, 0.2], [0.8, 0.5], [0.5, 0.8], [0.2, 0.8], [0.8, 0.8]]) {
        const x = L + Math.round(W * fc), y = T + Math.round(H * fr);
        if (x < 4 || x > 1436 || y < 4 || y > 730) continue;
        const c = await 命中链([x, y]);
        if (c && c.属主 === 偏[0].id && !c.有nodrag) { p = { x, y }; break; }
      }
      if (!p) { 记('   ⛔ 找不到落点'); break; }
      let px = Math.round(-R.搬移量 / z);
      if (Math.abs(px) < 4) px = -R.搬移量 > 0 ? 5 : -5;
      await page.mouse.move(p.x, p.y); await page.waitForTimeout(300);
      await page.mouse.down(); await page.waitForTimeout(150);
      for (let i = 1; i <= 10; i++) { await page.mouse.move(Math.round(p.x + (px * i) / 10), p.y); await page.waitForTimeout(150); }
      await page.mouse.up(); await page.waitForTimeout(700);
      await page.mouse.move(720, 300); await page.waitForTimeout(300);
      记(`   拖 ${px}px`);
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
  console.log('\n=== 已写 tools/batchFD3.json ===');
}
