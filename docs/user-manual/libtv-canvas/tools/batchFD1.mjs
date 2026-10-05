// ⭐⭐⭐⭐⭐ Batch FD-1：验证「框选之后拖动，会不会被整组搬走」
//
// 起因：FB 事故后画布被「整理画布」搬到了 x ≈ −48000。
// 想搬回原点附近，就得**整块平移**，而手册里**没有**「多选之后拖动是整组移动」这条行为。
// EZ 只证到「点 A + Shift 点 B，`.selected` 实打实有两个」，**没证过拖动会带着整组走**。
//
// FD-1 只做两件事（低风险、可回报）：
//   ① 探「缩放选项」菜单有哪些预设（缩小 zoom 就能一次搬更远）
//   ② 框选全部 11 个节点 → 拖其中一个 → 看**其余 10 个是否跟着动、且位移是否完全相同**
//      （这一步既是验证，也是搬移的第一段）
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 读全部坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFD1.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

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
  return { 画布: t ? [Number(t[1]), Number(t[2])] : null, 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], 选中: n.classList.contains('selected') };
}, id);
const 选中数 = () => page.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);

try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(12000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(4000);
  let Z = await 读zoom();
  记(`zoom = ${Z}｜1 屏px = ${(1 / Z).toFixed(4)} 画布单位`);

  // ① 探缩放选项菜单（纯只读：点开看一眼就 Esc 关掉）
  记('—— ① 「缩放选项」菜单里有什么 ——');
  const zb = await page.evaluate(() => {
    let b = null;
    for (const x of document.querySelectorAll('button')) {
      const r = x.getBoundingClientRect();
      if (r.top < 740 || r.bottom > 810 || r.left < 200 || r.left > 340) continue;
      b = x; break;
    }
    if (!b) return null;
    const r = b.getBoundingClientRect();
    return { aria: b.getAttribute('aria-label'), 文字: (b.innerText || '').trim(), 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] };
  });
  记('   按钮 = ' + JSON.stringify(zb));
  if (zb) {
    await page.mouse.move(zb.中心[0], zb.中心[1]); await page.waitForTimeout(350);
    await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(1000);
    const 菜单 = await page.evaluate(() => {
      const out = [];
      for (const x of document.querySelectorAll('button, [role="menuitem"], li')) {
        const t = (x.innerText || '').trim();
        if (!t || t.length > 12) continue;
        const r = x.getBoundingClientRect();
        if (r.top > 810 || r.bottom < 0 || r.width === 0) continue;
        out.push({ 文字: t, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)] });
      }
      return out;
    });
    记('   菜单项：' + JSON.stringify(菜单.map((m) => m.文字)));
    R.读数.缩放菜单 = 菜单;
    await page.screenshot({ path: EVID + 'fd1-01-缩放菜单.png' });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(600);
    await page.mouse.move(720, 300); await page.waitForTimeout(500);
    记(`   Esc 后 zoom = ${await 读zoom()}`);
  }

  // ② 框选全部 → 拖一个 → 看整组是否跟着动
  记('—— ② 框选全部 11 个，拖其中一个 ——');
  const 前 = await 读全部坐标(page);
  记('   拖前 x 范围：' + JSON.stringify([Math.min(...Object.values(前).map((v) => v[0])), Math.max(...Object.values(前).map((v) => v[0]))]));
  const 起框 = [20, 30], 落框 = [1420, 700];
  const 在框内 = await page.evaluate(([a, b, c, d]) => {
    let n = 0;
    for (const x of document.querySelectorAll('.react-flow__node')) {
      const r = x.getBoundingClientRect();
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      if (cx > a && cx < c && cy > b && cy < d) n++;
    }
    return n;
  }, [起框[0], 起框[1], 落框[0], 落框[1]]);
  记(`   框 (${起框}) → (${落框}) 内含 ${在框内} 个节点中心`);
  await page.mouse.move(起框[0], 起框[1]); await page.waitForTimeout(300);
  await page.mouse.down();
  const 帧 = 8;
  for (let i = 1; i <= 帧; i++) {
    await page.mouse.move(Math.round(起框[0] + ((落框[0] - 起框[0]) * i) / 帧), Math.round(起框[1] + ((落框[1] - 起框[1]) * i) / 帧));
    await page.waitForTimeout(120);
  }
  await page.mouse.up(); await page.waitForTimeout(800);
  const n1 = await 选中数();
  记(`   ⭐ 框完后 .selected = ${n1} 个`);
  R.读数.选中数 = n1;
  const 各选 = [];
  for (const id of Object.keys(坐标)) { const s = await 读(id); if (s && s.选中) 各选.push(id); }
  记('   被选中的：' + JSON.stringify(各选));
  await page.screenshot({ path: EVID + 'fd1-02-框选后.png' });

  // 找一个可拖的已选节点
  let 目标 = null;
  for (const id of 各选) {
    const s = await 读(id);
    const [L, T, W, H] = s.框;
    let 好 = null;
    for (const [fc, fr] of [[0.5, 0.5], [0.2, 0.2], [0.5, 0.2], [0.2, 0.5], [0.8, 0.2], [0.8, 0.5], [0.5, 0.8], [0.2, 0.8], [0.8, 0.8]]) {
      const x = L + Math.round(W * fc), y = T + Math.round(H * fr);
      if (x < 4 || x > 1436 || y < 4 || y > 700) continue;
      const ok = await page.evaluate((p) => {
        const e = document.elementFromPoint(p[0], p[1]);
        const n = e ? e.closest('.react-flow__node') : null;
        return !!(n && !e.closest('.nodrag') && n.getAttribute('data-id') === p[2]);
      }, [x, y, id]);
      if (ok) { 好 = { x, y }; break; }
    }
    if (好) { 目标 = [id, 好]; break; }
  }
  if (!目标) throw new Error('已选节点里找不到可拖落点');
  记(`   拖 ${目标[0]}，落点 ${JSON.stringify(目标[1])}`);

  const 位移px = 1100;
  await page.mouse.move(目标[1].x, 目标[1].y); await page.waitForTimeout(320);
  await page.mouse.down(); await page.waitForTimeout(160);
  const f2 = 10;
  for (let i = 1; i <= f2; i++) {
    await page.mouse.move(Math.round(目标[1].x + (位移px * i) / f2), 目标[1].y);
    await page.waitForTimeout(150);
  }
  await page.mouse.up(); await page.waitForTimeout(700);
  await page.mouse.move(720, 300); await page.waitForTimeout(400);

  const 后 = await 读全部坐标(page);
  const 位移 = {};
  for (const id of Object.keys(坐标)) {
    if (前[id] && 后[id]) 位移[id] = [Number((后[id][0] - 前[id][0]).toFixed(3)), Number((后[id][1] - 前[id][1]).toFixed(3))];
  }
  const 动了 = Object.entries(位移).filter(([, d]) => Math.hypot(d[0], d[1]) > 0.5);
  const 没动 = Object.entries(位移).filter(([, d]) => Math.hypot(d[0], d[1]) <= 0.5);
  记(`   ⭐⭐ 动了 ${动了.length} 个，没动 ${没动.length} 个`);
  for (const [id, d] of 动了) 记(`      ${id} 位移 ${JSON.stringify(d)}｜新坐标 ${JSON.stringify(后[id])}`);
  for (const [id, d] of 没动) 记(`      ${id} 位移 ${JSON.stringify(d)}（没动）`);
  const xs = 动了.map(([, d]) => d[0]);
  const 一致 = xs.length > 1 ? (Math.max(...xs) - Math.min(...xs) < 0.5) : null;
  记(`   ⭐⭐⭐ 所有动过的节点 x 位移：min ${Math.min(...xs).toFixed(3)} max ${Math.max(...xs).toFixed(3)}｜**完全一致？ ${一致}**`);
  记(`   请求位移 ${位移px} 屏px = ${(位移px / Z).toFixed(2)} 画布单位｜实际 ${xs[0]} 画布单位`);
  R.读数.位移 = 位移;
  await page.screenshot({ path: EVID + 'fd1-03-整组拖后.png' });
} catch (e) {
  R.错误 = String((e && e.stack) || e);
  记('❌ ' + e.message);
} finally {
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 全 = await 读全部坐标(page);
  const 残 = Object.entries(坐标).filter(([id, xy]) => {
    const n = 全[id]; return !n || Math.hypot(n[0] - xy[0], n[1] - xy[1]) > 0.5;
  }).map(([id, xy]) => `${id} 基线${JSON.stringify(xy)} 现${JSON.stringify(全[id] || '未渲染')}`);
  记('⭐⭐ 静置 15s 后坐标复核：' + (残.length ? JSON.stringify(残) : '[]（全部一致）'));
  R.收尾 = 残;
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchFD1.json ===');
}
