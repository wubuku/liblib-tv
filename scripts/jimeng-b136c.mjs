// 批次 136 · c 轮：**已建成的连线怎么选中、怎么删** —— 手册完全没有这一节。
//
// 🔑 b 轮首次建线成功（源 `b22-upload` → 目标 `音频 30`），并用 `⌘Z` 撤销归位。
//   新建档：边 class `react-flow__edge react-flow__edge-reference nopan selectable`、
//   `data-testid="rf__edge-edge_<uuid>"`、内层 `<g data-testid="reference-edge-interaction" data-state="default">`。
//   🔴 **手册只讲了「怎么建线」，没讲「建完之后怎么选中它、怎么删掉它」** —— 而这正是用户会立刻需要的下一步。
//
// 🛡 共享画布纪律：本轮**以「删掉这条边」为终点**，不是以「留着它」为终点。
//   删边走**右键菜单里的「删除」**（与节点删除同一条路径，前缀匹配 `删除`）；
//   菜单里没有就退回 `⌘Z`（b 轮已验证有效）。收尾硬断言**边数回到 0**。
//
// 📌 本轮顺带订正 `connect-nodes.md:104`：那里记「拖完源节点变成选中态（`1 selected`）」，
//   而 b 轮**建线成功后选中数是 0**。本轮用一组对照把「起手方式」这个变量单独拿出来：
//   **从已选中节点的手柄起手**（此时中心被 ⊕ 接管）到底会发生什么。
import { writeFileSync } from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { readConnect, canvasPos } from './jimeng-b136-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c' };
const save = () => writeFileSync(new URL('./_tmp-b136c.json', import.meta.url), JSON.stringify(out, null, 1));
const 断言 = (名, 条件, 详情) => { const ok = !!!!条件; (out.护栏 = out.护栏 || []).push({ 名, 通过: ok, 详情 });
  log(`  ${ok ? '✅' : '⛔'} 断言·${名}：${JSON.stringify(详情)}`); save(); return ok; };

const 边数 = async () => (await readConnect(p)).边数;
const 边详情 = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__edge')).map((e) => {
  const r = e.getBoundingClientRect();
  const g = e.querySelector('[data-testid="reference-edge-interaction"]');
  return { class: e.getAttribute('class'), testid: e.getAttribute('data-testid'), id: e.getAttribute('data-id'),
    rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    屏上中点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
    g层: g ? { dataState: g.getAttribute('data-state'), style: g.getAttribute('style'),
      子元素: Array.from(g.children).map((c) => c.tagName + '.' + String(c.getAttribute('class') || '').split(' ').slice(0, 2).join('.')),
      g矩形: (() => { const q = g.getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; })(),
      g祖先: (() => { const a = []; for (let n = g; n && n !== document.body; n = n.parentElement) a.push(String(n.className || '').split(' ')[0] || n.tagName); return a.slice(0, 6); })() } : null,
    path: (() => { const q = e.querySelector('path'); return q ? { d: q.getAttribute('d'), strokeWidth: q.getAttribute('stroke-width'), cls: q.getAttribute('class') } : null; })(),
    全层html: e.innerHTML.slice(0, 700) };
}));

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
断言('起点边数为 0', (await 边数()) === 0, {});

// ---------------------------------------------------------------- ② 建一条边
log('\n=== ② 建一条边（复现 b 轮的起手方式：未选中态 + source 热区） ===');
const plan = await p.evaluate(() => {
  const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const r = n.getBoundingClientRect();
    const h = n.querySelector('[data-testid="flow-node-source-handle"]');
    const hr = h ? h.getBoundingClientRect() : null;
    return { id: n.getAttribute('data-id'), 标题: (n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || null,
      x: r.x, y: r.y, right: r.right, bottom: r.bottom, w: r.width, h: r.height,
      手柄中心: hr ? [Math.round(hr.x + hr.width / 2), Math.round(hr.y + hr.height / 2)] : null };
  });
  const 源 = nodes.find((n) => n.手柄中心 && n.手柄中心[0] > 4 && n.手柄中心[0] < innerWidth - 4 && n.手柄中心[1] > 4 && n.手柄中心[1] < innerHeight - 4);
  if (!源) return { ok: false, 原因: '没有手柄中心在视口内的源' };
  // 🔴 整节点在视口**外**时，L>R2 且 T>B2 ⇒ 宽高**都是负数**，相乘得**大正数**，
  //   「可见面积」会算出 788957 这种假值，落点跑到 (-505,-322) 去（批次 136 c 轮第一版踩中）。
  //   ⇒ 必须**先判正性**再算面积，不能只判「面积够大」。
  const 落 = nodes.filter((n) => n.id !== 源.id).map((n) => {
    const L = Math.max(n.x, 4), R2 = Math.min(n.right, innerWidth - 4), T = Math.max(n.y, 66), B2 = Math.min(n.bottom, innerHeight - 66);
    const 宽 = R2 - L, 高 = B2 - T;
    if (!(宽 > 20 && 高 > 20)) return null;
    return { id: n.id, 标题: n.标题, 可见面积: 宽 * 高, 可见部分: [Math.round(L), Math.round(T), Math.round(R2), Math.round(B2)], 落点: [Math.round((L + R2) / 2), Math.round((T + B2) / 2)] };
  }).filter(Boolean).sort((a, b) => b.可见面积 - a.可见面积);
  return { ok: true, 源: { id: 源.id, 标题: 源.标题, 手柄中心: 源.手柄中心 }, 落: 落[0] || null, 落候选数: 落.length };
});
out.建边计划 = plan;
log('  ', JSON.stringify(plan));
save();
if (!plan.ok || !plan.落) { log('  ⛔ 无法建边，本轮到此为止'); await b.close(); process.exit(0); }
await p.mouse.move(plan.源.手柄中心[0], plan.源.手柄中心[1]); await p.waitForTimeout(300);
await p.mouse.down(); await p.waitForTimeout(250);
for (let i = 1; i <= 12; i++) {
  await p.mouse.move(Math.round(plan.源.手柄中心[0] + ((plan.落.落点[0] - plan.源.手柄中心[0]) * i) / 12),
                     Math.round(plan.源.手柄中心[1] + ((plan.落.落点[1] - plan.源.手柄中心[1]) * i) / 12));
  await p.waitForTimeout(55);
}
await p.waitForTimeout(500);
await p.mouse.up();
await p.waitForTimeout(2500);
await settle(p, R);
out.建边后 = { 边数: await 边数(), 选中: await R.selCount(), 状态行: await R.status() };
log('  ', JSON.stringify(out.建边后));
save();
断言('落点逐字在视口内（防止再踩「负宽×负高」那个坑）', plan.落.落点[0] > 0 && plan.落.落点[0] < 1280 && plan.落.落点[1] > 0 && plan.落.落点[1] < 720, { 落点: plan.落.落点, 可见部分: plan.落.可见部分 });
断言('边已建成', (await 边数()) === 1, { 边数: await 边数() });
if ((await 边数()) !== 1) { log('  ⛔ 没建出线，跳过后续'); await b.close(); process.exit(0); }

// ---------------------------------------------------------------- ③ 边的全层建档
log('\n=== ③ 边的全层建档 ===');
const e0 = (await 边详情())[0];
out.边 = e0;
log('  class  ', e0.class);
log('  testid ', e0.testid, '｜id', e0.id);
log('  屏上矩形', JSON.stringify(e0.rect), '｜中点', JSON.stringify(e0.屏上中点));
log('  g 层   ', JSON.stringify(e0.g层));
log('  path d ', e0.path && e0.path.d);
save();

// ---------------------------------------------------------------- ④ 悬停 / 点击边
log('\n=== ④ 悬停与点击边（读 data-state 与是否出浮层） ===');
out.交互 = [];
const 探 = async (tag) => {
  const s = await readConnect(p);
  const d = (await 边详情())[0];
  const rec = { tag, dataState: d && d.g层 && d.g层.dataState, gstyle: d && d.g层 && d.g层.style,
    选中节点: s.选中, 浮层: await R.overlays(),
    浮层testid: await p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).map((m) => m.getAttribute('data-testid') || m.getAttribute('aria-label'))),
    testid增量: s.testid.filter((x) => !out.基线testids.includes(x)) };
  out.交互.push(rec);
  log(`  ── ${tag} ── data-state «${rec.dataState}»｜g style «${rec.gstyle}»｜选中节点 ${JSON.stringify(rec.选中节点)}｜浮层 ${JSON.stringify(rec.浮层testid)}`);
  save();
  return rec;
};
await p.mouse.move(e0.屏上中点[0], e0.屏上中点[1]); await p.waitForTimeout(1200);
await 探('悬停在边上');
await p.mouse.click(e0.屏上中点[0], e0.屏上中点[1]); await p.waitForTimeout(1500);
const clicked = await 探('单击边');
out.单击边后选中数 = await R.selCount();
log('  单击边后选中数（节点）：', out.单击边后选中数);
save();

// ---------------------------------------------------------------- ⑤ 右键边 → 菜单 → 删除
log('\n=== ⑤ 右键边 → 读菜单 → 用「删除」项删掉它 ===');
await p.mouse.move(e0.屏上中点[0], e0.屏上中点[1]);
await p.mouse.click(e0.屏上中点[0], e0.屏上中点[1], { button: 'right' });
await p.waitForTimeout(1800);
const 菜单 = await p.evaluate(() => {
  const items = Array.from(document.querySelectorAll('[role=menuitem]')).map((e) => {
    const r = e.getBoundingClientRect();
    return { 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(), 禁用: e.getAttribute('aria-disabled'),
      rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      testid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label') };
  });
  const panel = document.querySelector('[role=menu]');
  const pr = panel ? panel.getBoundingClientRect() : null;
  return { 菜单testid: panel ? panel.getAttribute('data-testid') : null,
    菜单aria: panel ? panel.getAttribute('aria-label') : null,
    菜单矩形: pr ? [Math.round(pr.x), Math.round(pr.y), Math.round(pr.width), Math.round(pr.height)] : null,
    项数: items.length, 项: items };
});
out.边的右键菜单 = 菜单;
log('  菜单：', JSON.stringify({ testid: 菜单.菜单testid, aria: 菜单.菜单aria, 矩形: 菜单.菜单矩形, 项数: 菜单.项数 }));
for (const it of 菜单.项) log(`    · «${it.逐字}» 禁用=${it.禁用} testid=${it.testid}`);
save();

let 删掉了 = false;
const del = 菜单.项.find((it) => /^删除/.test(it.逐字.replace(/\s+/g, '')));
if (del && del.禁用 !== 'true') {
  out.删除项 = del;
  await p.mouse.click(Math.round(del.rect[0] + del.rect[2] / 2), Math.round(del.rect[1] + del.rect[3] / 2));
  await p.waitForTimeout(2500);
  await settle(p, R);
  out.删除后边数 = await 边数();
  log('  点「删除」后边数 =', out.删除后边数);
  删掉了 = out.删除后边数 === 0;
  save();
} else {
  out.删除项 = del || null;
  log('  ⛔ 菜单里没有可用的「删除」项 —— 退回 ⌘Z');
  await settle(p, R);
}
if (!删掉了 && (await 边数()) > 0) {
  const g = await keyGuard(p);
  out.兜底焦点守卫 = g;
  if (g.safe) { await p.keyboard.press('Meta+z'); await p.waitForTimeout(2500); await settle(p, R); log('  ⌘Z 后边数 =', await 边数()); }
  else log('  ⛔ 焦点不安全，不按 ⌘Z —— 如实报告');
}
await settle(p, R);
out.最终边数 = await 边数();
log('  最终边数 =', out.最终边数);
save();
断言('边已删除，边数回到 0', (await 边数()) === 0, { 边数: await 边数() });

// ---------------------------------------------------------------- ⑥ 收尾
log('\n=== ⑥ 零副作用收尾 ===');
const endCanvas = await canvasPos(p);
const 移动 = Object.keys(out.基线canvas).filter((id) => JSON.stringify(out.基线canvas[id]) !== JSON.stringify(endCanvas[id]));
const ids = await R.ids(), t = await R.testids();
out.收尾 = { 状态行: await R.status(), 选中: await R.selCount(), 浮层: await R.overlays(), zoom: await R.zoom(),
  credits: await R.credits(), minimap: await R.minimap(), 节点数: ids.length, testid种类: t.length,
  节点被移动: 移动,
  节点差集: { 多: ids.filter((x) => !out.基线ids.includes(x)), 少: out.基线ids.filter((x) => !ids.includes(x)) },
  testid差集: { 多: t.filter((x) => !out.基线testids.includes(x)), 少: out.基线testids.filter((x) => !t.includes(x)) } };
log('  ', JSON.stringify(out.收尾));
save();
断言('节点 canvas 坐标零位移', 移动.length === 0, { 移动 });
断言('节点 id 与基线逐个一致', out.收尾.节点差集.多.length === 0 && out.收尾.节点差集.少.length === 0, out.收尾.节点差集);
断言('静态 testid 与基线逐个一致', out.收尾.testid差集.多.length === 0 && out.收尾.testid差集.少.length === 0, out.收尾.testid差集);
save(); save();
log('\n✅ c 轮完成 → ./_tmp-b136c.json');
await b.close();
