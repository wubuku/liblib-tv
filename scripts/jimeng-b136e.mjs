// 批次 136 · e 轮：**把删除按钮本身验掉** + 建档「显示连线」开关。
//
// 🔑 d 轮已经分出胜负但**留了一个洞**：
//   `Delete` **无效**（1→1）／`Backspace` **有效**（1→0）—— 边数一归零，脚本的
//   `if (边数 > 0 && 删类.length)` 就跳过了，**`reference-edge-delete-control` 那个按钮压根没被点过**。
//   ⇒ 一个「看起来能用」的路径**没有实测**，就不能写进手册当操作步骤。本轮专门补上。
//
// 🆕 同时建档 d 轮顺带撞见、从没被记录过的开关：
//   `canvas-display-toggle-connections`（在可见按钮快照里，与 `canvas-display-toggle-minimap` 并列）。
//   小地图开关本册已建过档（`28×28@48,672`、`aria-pressed` 可靠、`data-state` 不可靠），
//   **连线开关此前全册 0 次出现**。
//
// 📌 顺带钉一条新契约：边**自带 aria 标签**，逐字形如
//   `Reference connection from <源类型> node: <源标题> to <目标类型> node: <目标标题>`
//   —— 悬停/聚焦时它就是 `document.activeElement`。
import { writeFileSync } from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { readConnect, canvasPos } from './jimeng-b136-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'e', 路径: [] };
const save = () => writeFileSync(new URL('./_tmp-b136e.json', import.meta.url), JSON.stringify(out, null, 1));
const 断言 = (名, 条件, 详情) => { const ok = !!!!条件; (out.护栏 = out.护栏 || []).push({ 名, 通过: ok, 详情 });
  log(`  ${ok ? '✅' : '⛔'} 断言·${名}：${JSON.stringify(详情)}`); save(); return ok; };
const 边数 = async () => (await readConnect(p)).边数;

async function 建一条边(base) {
  const plan = await p.evaluate(() => {
    const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
      const r = n.getBoundingClientRect();
      const h = n.querySelector('[data-testid="flow-node-source-handle"]');
      const hr = h ? h.getBoundingClientRect() : null;
      return { id: n.getAttribute('data-id'), 标题: (n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || null,
        x: r.x, y: r.y, right: r.right, bottom: r.bottom,
        手柄中心: hr ? [Math.round(hr.x + hr.width / 2), Math.round(hr.y + hr.height / 2)] : null };
    });
    const 源 = nodes.find((n) => n.手柄中心 && n.手柄中心[0] > 4 && n.手柄中心[0] < innerWidth - 4 && n.手柄中心[1] > 4 && n.手柄中心[1] < innerHeight - 4);
    if (!源) return null;
    const 落 = nodes.filter((n) => n.id !== 源.id).map((n) => {
      const L = Math.max(n.x, 4), R2 = Math.min(n.right, innerWidth - 4), T = Math.max(n.y, 66), B2 = Math.min(n.bottom, innerHeight - 66);
      const 宽 = R2 - L, 高 = B2 - T;
      if (!(宽 > 20 && 高 > 20)) return null;
      return { id: n.id, 标题: n.标题, 面积: 宽 * 高, 落点: [Math.round((L + R2) / 2), Math.round((T + B2) / 2)] };
    }).filter(Boolean).sort((a, b) => b.面积 - a.面积);
    return { 源: { id: 源.id, 标题: 源.标题, 手柄中心: 源.手柄中心 }, 落: 落[0] || null };
  });
  if (!plan || !plan.落) return null;
  await p.mouse.move(plan.源.手柄中心[0], plan.源.手柄中心[1]); await p.waitForTimeout(300);
  await p.mouse.down(); await p.waitForTimeout(250);
  for (let i = 1; i <= 12; i++) {
    await p.mouse.move(Math.round(plan.源.手柄中心[0] + ((plan.落.落点[0] - plan.源.手柄中心[0]) * i) / 12),
                       Math.round(plan.源.手柄中心[1] + ((plan.落.落点[1] - plan.源.手柄中心[1]) * i) / 12));
    await p.waitForTimeout(55);
  }
  await p.waitForTimeout(500);
  await p.mouse.up(); await p.waitForTimeout(2500);
  await settle(p, R);
  return plan;
}

// ---------------------------------------------------------------- ① 基线
out.start = { 状态行: await R.status(), zoom: await R.zoom() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
await settle(p, R);
out.基线 = { 状态行: await R.status(), 节点数: (await R.ids()).length, testid种类: (await R.testids()).length };
out.基线ids = await R.ids();
out.基线testids = await R.testids();
out.基线canvas = await canvasPos(p);
log('基线：', JSON.stringify(out.基线));
save();
断言('起点边数 0', (await 边数()) === 0, {});

// ---------------------------------------------------------------- ② 建档「显示连线」开关
log('\n=== ② 建档 canvas-display-toggle-connections（小地图开关的同族，此前全册 0 次出现） ===');
out.连线开关 = await p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-display-toggle-connections"]');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  const s = getComputedStyle(e);
  const 点命中 = (() => { const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
    const h = document.elementFromPoint(cx, cy); return h ? h.tagName + '.' + String(h.className || '').split(' ')[0] : null; })();
  return { testid: 'canvas-display-toggle-connections', tag: e.tagName, role: e.getAttribute('role'),
    ariaLabel: e.getAttribute('aria-label'), ariaPressed: e.getAttribute('aria-pressed'), dataState: e.getAttribute('data-state'),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(), pe: s.pointerEvents, 中心命中: 点命中,
    父级: (() => { const a = []; for (let n = e; n && n !== document.body && a.length < 5; n = n.parentElement) a.push(String(n.className || '').split(' ')[0] || n.tagName); return a; })() };
});
log('  ', JSON.stringify(out.连线开关));
const 小地图开关 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]');
  const r = e.getBoundingClientRect(); return { ariaPressed: e.getAttribute('aria-pressed'), dataState: e.getAttribute('data-state'),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; });
out.小地图开关 = 小地图开关;
log('  对照·小地图开关：', JSON.stringify(小地图开关));
save();
断言('连线开关存在且有 aria-pressed', !!out.连线开关 && out.连线开关.ariaPressed !== null, { 连线开关: out.连线开关 });

// ---------------------------------------------------------------- ③ 建边 → 选中 → 读删除按钮三层
log('\n=== ③ 建边 → 单击选中 → 读删除按钮三层结构 ===');
const plan = await 建一条边();
out.建边计划 = plan;
log('  ', JSON.stringify(plan));
save();
断言('边已建成', (await 边数()) === 1, { 边数: await 边数() });
if ((await 边数()) !== 1) { log('  ⛔ 没建出线'); await b.close(); process.exit(0); }

const 边信息 = await p.evaluate(() => { const e = document.querySelector('.react-flow__edge'); const r = e.getBoundingClientRect();
  return { 中点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
    aria: e.getAttribute('aria-label'), rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; });
out.边 = 边信息;
log('  边 aria 逐字 «' + 边信息.aria + '»');
await p.mouse.click(边信息.中点[0], 边信息.中点[1]);
await p.waitForTimeout(1800);
out.选中态删除三层 = await p.evaluate(() => {
  const q = (t) => document.querySelector(`[data-testid="${t}"]`);
  const box = (e) => { if (!e) return null; const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
    return { tag: e.tagName, rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      pe: s.pointerEvents, opacity: s.opacity, visibility: s.visibility, zIndex: s.zIndex, position: s.position,
      逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(), aria: e.getAttribute('aria-label') }; };
  const c = q('reference-edge-delete-control');
  return { positioner: box(q('reference-edge-delete-positioner')),
    screenSpace: box(q('reference-edge-delete-screen-space')),
    control: box(c),
    control子元素: c ? Array.from(c.children).map((x) => x.tagName + '.' + String(x.getAttribute('class') || '').split(' ')[0]) : null,
    control中心命中: (() => { if (!c) return null; const r = c.getBoundingClientRect();
      const h = document.elementFromPoint(Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2));
      return h ? h.tagName + '.' + String(h.className || '').split(' ')[0] + ' tid=' + h.getAttribute('data-testid') : null; })(),
    dataState: (() => { const g = q('reference-edge-interaction'); return g ? g.getAttribute('data-state') : null; })() };
});
log('  positioner ', JSON.stringify(out.选中态删除三层.positioner));
log('  screenSpace', JSON.stringify(out.选中态删除三层.screenSpace));
log('  control    ', JSON.stringify(out.选中态删除三层.control));
log('  中心命中   ', out.选中态删除三层.control中心命中, '｜data-state', out.选中态删除三层.dataState);
save();
const c = out.选中态删除三层.control;
断言('删除按钮中心命中它自己（没有被遮挡）', /reference-edge-delete-control/.test(String(out.选中态删除三层.control中心命中)), { 中心命中: out.选中态删除三层.control中心命中 });
断言('删除按钮 aria 逐字是 Delete connection', c && c.aria === 'Delete connection', { aria: c && c.aria });

// ---------------------------------------------------------------- ④ 点删除按钮
log('\n=== ④ 点 reference-edge-delete-control ===');
const 前 = await 边数();
await p.mouse.click(c.rect[0] + c.rect[2] / 2, c.rect[1] + c.rect[3] / 2);
await p.waitForTimeout(2500);
await settle(p, R);
const 后 = await 边数();
out.路径.push({ 路径: '点 reference-edge-delete-control 按钮', 前边数: 前, 后边数: 后, 成功: 后 < 前 });
log(`  ${后 < 前 ? '🎉' : '⛔'} 边数 ${前} → ${后}`);
save();
断言('删除按钮真的能删掉连线', 后 === 0, { 边数: 后 });

// ---------------------------------------------------------------- ⑤ 复现 Delete 无效 / Backspace 有效
log('\n=== ⑤ 再建一条，复现「Delete 无效 / Backspace 有效」 ===');
if ((await 边数()) === 0) {
  await 建一条边();
  const e2 = await p.evaluate(() => { const e = document.querySelector('.react-flow__edge'); if (!e) return null;
    const r = e.getBoundingClientRect(); return { 中点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)], aria: e.getAttribute('aria-label') }; });
  out.第二条边 = e2;
  log('  第二条边 aria «' + (e2 && e2.aria) + '»｜边数', await 边数());
  save();
  if (e2 && (await 边数()) === 1) {
    await p.mouse.click(e2.中点[0], e2.中点[1]); await p.waitForTimeout(1800);
    const g = await keyGuard(p);
    out.第二条焦点守卫 = g;
    log('  焦点：', g.where, '｜safe', g.safe);
    await p.keyboard.press('Delete'); await p.waitForTimeout(2000); await settle(p, R);
    const a = await 边数();
    await p.keyboard.press('Backspace'); await p.waitForTimeout(2000); await settle(p, R);
    const bb = await 边数();
    out.按键复现 = { Delete后: a, Backspace后: bb };
    log(`  Delete 后边数 ${a}｜Backspace 后边数 ${bb}`);
    save();
  }
}
if ((await 边数()) > 0) { const g = await keyGuard(p); if (g.safe) { await p.keyboard.press('Meta+z'); await p.waitForTimeout(2200); await settle(p, R); } }
out.最终边数 = await 边数();
log('\n  最终边数 =', out.最终边数);
save();
断言('边数回到 0', (await 边数()) === 0, { 边数: await 边数() });

// ---------------------------------------------------------------- ⑥ 收尾
log('\n=== ⑥ 收尾 ===');
const endCanvas = await canvasPos(p);
const 移动 = Object.keys(out.基线canvas).filter((id) => JSON.stringify(out.基线canvas[id]) !== JSON.stringify(endCanvas[id]));
const ids = await R.ids(), t = await R.testids();
out.收尾 = { 状态行: await R.status(), 选中: await R.selCount(), 浮层: await R.overlays(), zoom: await R.zoom(),
  credits: await R.credits(), minimap: await R.minimap(), 节点数: ids.length, testid种类: t.length, 节点被移动: 移动,
  节点差集: { 多: ids.filter((x) => !out.基线ids.includes(x)), 少: out.基线ids.filter((x) => !ids.includes(x)) },
  testid差集: { 多: t.filter((x) => !out.基线testids.includes(x)), 少: out.基线testids.filter((x) => !t.includes(x)) } };
log('  ', JSON.stringify(out.收尾));
save();
断言('节点 canvas 坐标零位移', 移动.length === 0, { 移动 });
断言('节点 id 与基线逐个一致', out.收尾.节点差集.多.length === 0 && out.收尾.节点差集.少.length === 0, out.收尾.节点差集);
断言('静态 testid 与基线逐个一致', out.收尾.testid差集.多.length === 0 && out.收尾.testid差集.少.length === 0, out.收尾.testid差集);
save(); save();
log('\n✅ e 轮完成 → ./_tmp-b136e.json');
await b.close();
