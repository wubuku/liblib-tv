// ⭐⭐⭐⭐⭐ Batch FD-5：把一个节点拖到**另一个节点上**松手，会发生什么？
//
// 这是用户最高频的操作之一，**手册里一条都没有**。
// FD-4 已经拿到「拖到空白松手」的对照（整组移动 2278.9，11 个节点一致），
// 本轮只做「拖到节点上」这一半，两边对比。
//
// ⭐ 目标选择：`v-v2hlWY4Br3`（视频节点，屏幕中心 [215,153]）
//   → 拖 +797 屏 px 落在 `n-56F19pXVB4`（导演台，屏幕中心 [1012,153]）**正中心**。
//
// ⛔ 安全边界：
//   · 目标节点是**基线里的既有节点**，不删任何东西。
//   · 若真的新建了对象，只删**本轮新建 + `m-` 前缀 + 不在基线**的（canvas-baseline 的 `允许删除`）。
//   · ⛔ **不点任何生成/提交类按钮**；出现弹窗只点「取消/关闭」。
//   · ⛔ **不删除连线** —— 连线删除不可逆，风险高于收益；出现了就如实记录并报告。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 坐标, 允许删除 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const EVID = HERE + '.evidence/';
const R = { 步骤: [], 读数: {} };
const 记 = (s) => { R.步骤.push(s); writeFileSync(HERE + 'batchFD5.json', JSON.stringify(R, null, 2)); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;
const 逐个读 = () => page.evaluate((ids) => {
  const o = {};
  for (const id of ids) {
    const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
    if (!n) { o[id] = null; continue; }
    const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
    const r = n.getBoundingClientRect();
    o[id] = { 画布: t ? [Number(t[1]), Number(t[2])] : null, 中心: [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)], 框: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] };
  }
  return o;
}, Object.keys(坐标));
/** ⭐ 画布全量快照：所有 react-flow 节点 id（含基线外的）+ 连线 + 面板 */
const 快照 = () => page.evaluate(() => {
  const 节点 = [...document.querySelectorAll('.react-flow__node')].map((n) => n.getAttribute('data-id'));
  const 连线 = [...document.querySelectorAll('.react-flow__edge')].map((e) => (e.getAttribute('data-id') || e.id || e.className).slice(0, 60));
  const 句柄 = document.querySelectorAll('.react-flow__handle').length;
  const 面板 = [...document.querySelectorAll('[role="dialog"], .mantine-Modal-content, .mantine-Drawer-content')]
    .map((d) => (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 80)).filter(Boolean);
  const 工具条 = [...document.querySelectorAll('button[aria-label]')]
    .map((b) => b.getAttribute('aria-label'))
    .filter((a) => /组|复制|排列|对齐|移动到|投放|合并|连接|吸附|吸附到|生成/.test(a));
  return { 节点数: 节点.length, 节点, 连线数: 连线.length, 连线, 句柄, 面板, 工具条 };
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
  if (关) { await page.mouse.move(关[0], 关[1]); await page.waitForTimeout(300); await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(1000); }
  await page.mouse.move(720, 300); await page.waitForTimeout(500);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(4000);

  const 前 = await 快照();
  记('—— 拖之前 ——');
  记(`   节点 ${前.节点数} 个：${JSON.stringify(前.节点)}`);
  记(`   连线 ${前.连线数} 条｜句柄 ${前.句柄} 个｜面板 ${JSON.stringify(前.面板)}`);
  R.读数.前 = 前;
  await page.screenshot({ path: EVID + 'fd5-01-拖之前.png' });

  // 点选 v-v2hlWY4Br3（单个视频节点）
  const 全 = await 逐个读();
  const 源 = 'v-v2hlWY4Br3', 靶 = 'n-56F19pXVB4';
  const 起 = 全[源].中心, 落 = 全[靶].中心;
  记(`—— 点选 ${源}，从 ${JSON.stringify(起)} 拖到 ${JSON.stringify(落)}（落在 ${靶} 正中心）——`);
  await page.mouse.move(起[0], 起[1]); await page.waitForTimeout(350);
  const 落点属主 = await page.evaluate((p) => {
    const e = document.elementFromPoint(p[0], p[1]);
    const n = e ? e.closest('.react-flow__node') : null;
    return { 属主: n ? n.getAttribute('data-id') : null, 有nodrag: !!(e && e.closest('.nodrag')), 标签: e ? e.tagName : null };
  }, 起);
  记(`   ⭐ 起点落点自证：${JSON.stringify(落点属主)}`);
  if (落点属主.属主 !== 源 || 落点属主.有nodrag) { 记('   ⛔ 起点不合格，不拖'); throw new Error('起点不合格'); }
  await page.mouse.down(); await page.mouse.up(); await page.waitForTimeout(700);
  记(`   点选后 selected = ${await page.evaluate((id) => document.querySelector(`.react-flow__node[data-id="${id}"]`).classList.contains('selected'), 源)}`);

  // ⭐ 拖到靶节点正中心，中途**逐帧**并在最后 1/3 观察有没有出现投放提示
  const 轨迹 = [];
  await page.mouse.move(起[0], 起[1]); await page.waitForTimeout(300);
  await page.mouse.down(); await page.waitForTimeout(160);
  const 帧 = 12;
  for (let i = 1; i <= 帧; i++) {
    const x = Math.round(起[0] + ((落[0] - 起[0]) * i) / 帧);
    await page.mouse.move(x, 起[1]);
    await page.waitForTimeout(150);
    轨迹.push(x);
  }
  // ⭐ 在靶节点上方**悬停**一下，读投放提示
  const 悬停读数 = await page.evaluate((p) => {
    const e = document.elementFromPoint(p[0], p[1]);
    const 靶 = e ? e.closest('.react-flow__node[data-id="n-56F19pXVB4"]') : null;
    return {
      命中属主: e ? (e.closest('.react-flow__node') ? e.closest('.react-flow__node').getAttribute('data-id') : null) : null,
      靶class: 靶 ? 靶.getAttribute('class') : null,
      靶高亮: 靶 ? getComputedStyle(靶).outline : null,
      页面浮层: [...document.querySelectorAll('div')].filter((d) => {
        const r = d.getBoundingClientRect();
        const t = (d.innerText || '').trim();
        return r.width > 60 && r.height > 20 && r.width < 600 && r.height < 200 && /投放|放入|放到|松手|合并|连接|替换|填入/.test(t) && t.length < 60;
      }).map((d) => (d.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 50)),
    };
  }, [落[0], 起[1]]);
  记(`   ⭐⭐ 悬停在 ${靶} 上时：命中属主 ${悬停读数.命中属主}｜靶 outline ${悬停读数.靶高亮}`);
  记(`      投放类提示浮层：${JSON.stringify(悬停读数.页面浮层)}`);
  R.读数.悬停 = 悬停读数;
  await page.screenshot({ path: EVID + 'fd5-02-拖到靶上方.png' });

  await page.mouse.up();
  await page.waitForTimeout(1200);
  await page.mouse.move(720, 300); await page.waitForTimeout(600);
  const 后 = await 快照();
  记('—— 松手之后 ——');
  记(`   节点 ${后.节点数} 个：${JSON.stringify(后.节点)}`);
  记(`   连线 ${后.连线数} 条｜句柄 ${后.句柄} 个`);
  记(`   面板 ${JSON.stringify(后.面板)}`);
  记(`   相关工具条 ${JSON.stringify(后.工具条)}`);
  R.读数.后 = 后;
  const 新增 = 后.节点.filter((id) => !前.节点.includes(id));
  const 消失 = 前.节点.filter((id) => !后.节点.includes(id));
  记(`   ⭐⭐⭐ 节点数 ${前.节点数} → ${后.节点数}｜**新增 ${JSON.stringify(新增)}｜消失 ${JSON.stringify(消失)}**`);
  记(`   ⭐⭐⭐ 连线数 ${前.连线数} → ${后.连线数}｜差 ${后.连线数 - 前.连线数}`);
  const 全后 = await 逐个读();
  const 位移 = {};
  for (const id of Object.keys(坐标)) if (全[id] && 全后[id] && 全[id].画布 && 全后[id].画布) 位移[id] = [Number((全后[id].画布[0] - 全[id].画布[0]).toFixed(2)), Number((全后[id].画布[1] - 全[id].画布[1]).toFixed(2))];
  const 动 = Object.entries(位移).filter(([, d]) => Math.hypot(d[0], d[1]) > 0.5);
  记(`   ⭐ 移动了 ${动.length} 个基线节点：${JSON.stringify(动)}`);
  R.读数.位移 = 位移;
  await page.screenshot({ path: EVID + 'fd5-03-松手之后.png' });

  // ⛔ 若新建了对象，只删「本轮新建 + m- 前缀 + 不在基线」的
  const 本轮新建 = 新增.filter((id) => 允许删除(id, 新增));
  if (本轮新建.length) 记(`   ⛔ 新建对象 ${JSON.stringify(本轮新建)}（符合删除条件），但本轮**不删** —— 先记录，避免误伤`);
} catch (e) {
  R.错误 = String((e && e.stack) || e);
  记('❌ ' + e.message);
} finally {
  // 复原：把动过的节点拖回去（单个拖就行，动得少）
  const 全3 = await 逐个读();
  const 偏 = Object.keys(坐标).map((id) => ({ id, d: 全3[id] && 全3[id].画布 ? [全3[id].画布[0] - 坐标[id][0], 全3[id].画布[1] - 坐标[id][1]] : null }))
    .filter((o) => o.d && Math.hypot(o.d[0], o.d[1]) > 0.5);
  if (偏.length) {
    记(`—— finally：有 ${偏.length} 个节点偏离基线 ${JSON.stringify(偏.slice(0, 3))} ——`);
    const Z = await page.evaluate(() => {
      const v = document.querySelector('.react-flow__viewport');
      const m = /matrix\(([^)]+)\)/.exec(getComputedStyle(v).transform || '');
      return m ? Number(m[1].split(',')[0]) : 1;
    });
    for (const o of 偏) {
      const s = 全3[o.id];
      let px = Math.round(-o.d[0] * Z), py = Math.round(-o.d[1] * Z);
      if (Math.abs(px) < 3 && px !== 0) px = 3;
      if (Math.abs(py) < 3 && py !== 0) py = 3;
      const ok = await page.evaluate((p) => {
        const e = document.elementFromPoint(p[0], p[1]);
        const n = e ? e.closest('.react-flow__node') : null;
        return !!(n && !e.closest('.nodrag') && n.getAttribute('data-id') === p[2]);
      }, s.中心, o.id);
      if (!ok) { 记(`   ⛔ ${o.id} 中心落点不合格`); continue; }
      记(`   ${o.id} 拖 ${px},${py}px（请求量，吸附后未必到位）`);
      await page.mouse.move(s.中心[0], s.中心[1]); await page.waitForTimeout(300);
      await page.mouse.down(); await page.waitForTimeout(150);
      const f = 10;
      for (let i = 1; i <= f; i++) { await page.mouse.move(Math.round(s.中心[0] + (px * i) / f), Math.round(s.中心[1] + (py * i) / f)); await page.waitForTimeout(150); }
      await page.mouse.up(); await page.waitForTimeout(700);
      await page.mouse.move(720, 300); await page.waitForTimeout(300);
    }
  }
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(15000);
  const 全 = await page.evaluate((ids) => {
    const o = {};
    for (const id of ids) {
      const n = document.querySelector(`.react-flow__node[data-id="${id}"]`);
      if (!n) { o[id] = '未渲染'; continue; }
      const t = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
      o[id] = t ? [Number(t[1]), Number(t[2])] : n.style.transform;
    }
    return o;
  }, Object.keys(坐标));
  const 残 = Object.entries(坐标).filter(([id, xy]) => {
    const n = 全[id]; return !Array.isArray(n) || Math.hypot(n[0] - xy[0], n[1] - xy[1]) > 0.5;
  }).map(([id, xy]) => `${id} 基线${JSON.stringify(xy)} 现${JSON.stringify(全[id])}`);
  记('⭐⭐ 静置 15s 后坐标复核：' + (残.length ? JSON.stringify(残) : '[]（全部一致）'));
  R.收尾 = 残;
  await 浏览器.browser.close();
  console.log('\n=== 已写 tools/batchFD5.json ===');
}
