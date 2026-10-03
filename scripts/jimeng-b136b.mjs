// 批次 136 · b 轮：**把松手点放在目标节点上** —— 真正试一次建线，成则**立刻撤销**。
//
// 🔑 a 轮已经查清「拖拽起不了拖」是误读：拖动时**确实出现了预览连线**
//   （`<g>` 矩形随鼠标从 `194.7×140.3@459,26` 变到 `347.9×520@307,-54` 再到 `687.7×189.9@(-4,470)`），
//   在空白处松手即取消、边数仍 0、节点 canvas 坐标**零位移**。
//   ⇒ `connect-nodes.md:104` 记的「拖完也没建出连线」**不是「起不了拖」，是「松手位置不对」**。
//   本轮把松手点从空白 pane 换成**目标节点本体**，看边到底能不能出来。
//
// 🛡 共享画布纪律：建边会留下产物，所以本轮把**撤销**写死成硬护栏 ——
//   ① 建边后**当场**断言边数 == 1 并抓下这条边的 DOM 指纹；
//   ② 撤销走 **`⌘Z`**（先过 `keyGuard`）；
//   ③ 撤销后**当场**断言边数回到 0；④ 兜底：若 ⌘Z 没生效，
//      改走**选中边 → 右键菜单 → 删除**，再不行就**如实报告并停手**（不硬来）。
//
// 📌 落点选取的坑（批次 135 c 轮教训）：a 轮的目标节点中心 `cy = -35` **在视口外** ——
//   节点互相重叠，60% 下大半节点只露出一条。所以本轮取「**节点可见部分**的中心」，
//   并**当场断言落点在视口内**，不再拿「在视口内」这个含糊判据糊弄。
import { writeFileSync } from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { readConnect, findEmptyPane, canvasPos } from './jimeng-b136-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b', 检查点: [] };
const save = () => writeFileSync(new URL('./_tmp-b136b.json', import.meta.url), JSON.stringify(out, null, 1));
const 断言 = (名, 条件, 详情) => { const ok = !!!!条件; (out.护栏 = out.护栏 || []).push({ 名, 通过: ok, 详情 });
  log(`  ${ok ? '✅' : '⛔'} 断言·${名}：${JSON.stringify(详情)}`); save(); return ok; };

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
断言('起点边数为 0', (await readConnect(p)).边数 === 0, { 边数: (await readConnect(p)).边数 });

// ---------------------------------------------------------------- ② 选源 + 选「可见部分中心」落点
log('\n=== ② 选源节点与落点（落点必须**当场**在视口内） ===');
const plan = await p.evaluate(() => {
  const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const r = n.getBoundingClientRect();
    const h = n.querySelector('[data-testid="flow-node-source-handle"]');
    return { id: n.getAttribute('data-id'), 标题: (n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || null,
      x: r.x, y: r.y, right: r.right, bottom: r.bottom, w: r.width, h: r.height,
      handle: h ? (() => { const b = h.getBoundingClientRect(); return { cx: Math.round(b.x + b.width / 2), cy: Math.round(b.y + b.height / 2) }; })() : null };
  });
  const 在视口 = (a, b, c, d) => a >= 4 && c <= innerWidth - 4 && b >= 66 && d <= innerHeight - 66;
  // 源：手柄中心**逐字**在视口内
  const 源 = nodes.find((n) => n.handle && n.handle.cy > 4 && n.handle.cy < innerHeight - 4 && n.handle.cx > 4 && n.handle.cx < innerWidth - 4);
  if (!源) return { ok: false, 原因: '没有手柄中心在视口内的源节点' };
  // 落点：与源不同、且**可见部分**的中心在视口内的节点
  const 落 = nodes.filter((n) => n.id !== 源.id).map((n) => {
    const L = Math.max(n.x, 4), R2 = Math.min(n.right, innerWidth - 4);
    const T = Math.max(n.y, 66), B2 = Math.min(n.bottom, innerHeight - 66);
    if (R2 - L < 20 || B2 - T < 20) return null;
    return { id: n.id, 标题: n.标题, 可见部分: [Math.round(L), Math.round(T), Math.round(R2), Math.round(B2)],
      落点: [Math.round((L + R2) / 2), Math.round((T + B2) / 2)] };
  }).filter(Boolean);
  // 🔴 落点要按**可见面积**降序取：节点互相重叠，60% 下大半只露一条 4–44px 的窄边
  //   （批次 135 c 轮同款坑）。窄条虽然「在视口内」，但落上去命中的是边角残片。
  落.sort((a, b) => ((b.可见部分[2] - b.可见部分[0]) * (b.可见部分[3] - b.可见部分[1]))
              - ((a.可见部分[2] - a.可见部分[0]) * (a.可见部分[3] - a.可见部分[1])));
  落.forEach((n) => { n.可见面积 = (n.可见部分[2] - n.可见部分[0]) * (n.可见部分[3] - n.可见部分[1]); });
  return { ok: true, 源: { id: 源.id, 标题: 源.标题, 手柄中心: [源.handle.cx, 源.handle.cy], 节点rect: [Math.round(源.x), Math.round(源.y), Math.round(源.w), Math.round(源.h)] },
    落点候选数: 落.length, 落点候选: 落.slice(0, 6) };
});
out.计划 = plan;
log('  ', JSON.stringify(plan));
save();
if (!plan.ok) { log('  ⛔ ', plan.原因); await b.close(); process.exit(0); }
const SRC = plan.源, TGT = plan.落点候选[0];
log('  源：', JSON.stringify(SRC), '\n  落点：', JSON.stringify(TGT));
const 落点在视口内 = TGT.落点[0] > 4 && TGT.落点[0] < 1276 && TGT.落点[1] > 4 && TGT.落点[1] < 716;
断言('落点逐字在视口内', 落点在视口内, { 落点: TGT.落点 });
const 落点命中 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y); return h ? h.tagName + '.' + String(h.className || '').split(' ')[0] + ' tid=' + h.getAttribute('data-testid') : null; }, TGT.落点);
out.落点命中 = 落点命中;
log('  落点命中：', 落点命中);
断言('落点命中的是节点子树（不是 pane）', !/react-flow__pane/.test(String(落点命中)), { 落点命中 });
断言('落点可见面积 ≥ 2000 px²（不是边角窄条）', TGT.可见面积 >= 2000, { 可见面积: TGT.可见面积, 可见部分: TGT.可见部分 });

// ---------------------------------------------------------------- ③ 起拖 → 在目标节点上松手
log('\n=== ③ 起拖 → 悬停 → 在目标节点本体上松手 ===');
const snap = async (tag) => {
  const s = await readConnect(p);
  const 多 = s.testid.filter((x) => !out.基线testids.includes(x));
  const rec = { tag, 边数: s.边数, 预览层数: s.线预览层.length, 选中: s.选中, class标记: s.节点class标记, testid增量: 多 };
  out.检查点.push(rec);
  log(`  ── ${tag} ── 边数 ${rec.边数}｜预览层 ${rec.预览层数}｜选中 ${JSON.stringify(rec.选中)}｜testid增量 ${JSON.stringify(多)}`);
  save();
  return rec;
};
await p.mouse.move(SRC.手柄中心[0], SRC.手柄中心[1]);
await p.waitForTimeout(300);
await p.mouse.down();
await p.waitForTimeout(250);
for (let i = 1; i <= 12; i++) {
  await p.mouse.move(Math.round(SRC.手柄中心[0] + ((TGT.落点[0] - SRC.手柄中心[0]) * i) / 12),
                     Math.round(SRC.手柄中心[1] + ((TGT.落点[1] - SRC.手柄中心[1]) * i) / 12));
  await p.waitForTimeout(55);
}
await p.waitForTimeout(600);
await snap('悬停在目标节点上（未松手）');
await p.mouse.up();
await p.waitForTimeout(2500);
const built = await snap('在目标节点上松手后 2.5s');
await settle(p, R);
const after = await snap('settle 后');

// ---------------------------------------------------------------- ④ 建成了吗
log('\n=== ④ 判定与撤销 ===');
out.边DOM = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__edge')).map((e) => ({
  cls: e.getAttribute('class'), testid: e.getAttribute('data-testid'), id: e.getAttribute('data-id'),
  inner: e.innerHTML.slice(0, 300), rect: (() => { const r = e.getBoundingClientRect(); return [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]; })(),
})));
out.边数 = built.边数;
log('  边数 =', built.边数, '｜边 DOM：', JSON.stringify(out.边DOM));
save();
const 建成了 = built.边数 > 0;
log(`  ${建成了 ? '🎉 建线成功' : '⛔ 仍未建出线'}`);

if (建成了) {
  const 撤销前 = built.边数;
  const g = await keyGuard(p);
  out.撤销前焦点守卫 = g;
  log('  撤销前焦点守卫：', g.safe ? '✅ 可按' : '⛔ ' + g.reason);
  save();
  if (g.safe) {
    await p.keyboard.press('Meta+z');
    await p.waitForTimeout(2500);
    await settle(p, R);
    const after2 = await readConnect(p);
    out['⌘Z后'] = { 边数: after2.边数, 状态行: await R.status() };
    log('  ⌘Z 后：', JSON.stringify(out['⌘Z后']));
    save();
    if (after2.边数 !== 撤销前) {
      log('  ✅ ⌘Z 撤销成功');
    } else {
      // 兜底：选边 → 右键菜单 → 删除
      log('  ⛔ ⌘Z 无效，走兜底：选中边 → 右键菜单 → 删除');
      const 边中心 = await p.evaluate(() => { const e = document.querySelector('.react-flow__edge'); if (!e) return null;
        const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; });
      out.边中心 = 边中心;
      if (边中心) {
        await p.mouse.click(边中心.x, 边中心.y); await p.waitForTimeout(1200);
        await p.mouse.click(边中心.x, 边中心.y, { button: 'right' }); await p.waitForTimeout(1500);
        const items = await p.evaluate(() => Array.from(document.querySelectorAll('[role=menuitem]')).map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()));
        out.边的右键菜单 = items;
        log('  边的右键菜单：', JSON.stringify(items));
        const del = await p.evaluate(() => { for (const e of document.querySelectorAll('[role=menuitem]')) {
            const t = (e.innerText || '').replace(/\s+/g, '').trim(); if (/^删除/.test(t)) { const r = e.getBoundingClientRect(); return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2), 逐字: t }; } } return null; });
        if (del) { await p.mouse.click(del.x, del.y); await p.waitForTimeout(2000); out.兜底删除 = { 逐字: del.逐字, 边数: (await readConnect(p)).边数 }; log('  兜底删除：', JSON.stringify(out.兜底删除)); }
        else { log('  ⛔ 右键菜单里没有「删除」项 —— 如实报告，不硬来'); }
      }
      save();
    }
  }
  await settle(p, R);
  const fin = await readConnect(p);
  out.撤销后 = { 边数: fin.边数, 状态行: await R.status() };
  log('  最终：', JSON.stringify(out.撤销后));
  断言('边已撤销，边数回到 0', fin.边数 === 0, { 边数: fin.边数 });
}

// ---------------------------------------------------------------- ⑤ 零副作用核对
log('\n=== ⑤ 零副作用核对 ===');
const endCanvas = await canvasPos(p);
const 移动 = Object.keys(out.基线canvas).filter((id) => JSON.stringify(out.基线canvas[id]) !== JSON.stringify(endCanvas[id]));
const end = await readConnect(p);
out.副作用 = { 边数: end.边数, 节点被移动: 移动, 节点数: Object.keys(endCanvas).length, 选中: end.选中,
  浮层: await R.overlays(), zoom: await R.zoom(), minimap: await R.minimap(), testid种类: (await R.testids()).length };
log('  ', JSON.stringify(out.副作用));
save();
断言('节点 canvas 坐标零位移', 移动.length === 0, { 移动 });
断言('浮层 0', (await R.overlays()) === 0, {});
save(); save();
log('\n✅ b 轮完成 → ./_tmp-b136b.json');
await b.close();
