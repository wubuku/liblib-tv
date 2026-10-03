// 批次 136 · f 轮：**定案「边上的删除按钮」到底是不是按钮。**
//
// 🔴 e 轮撞出一个**必须定案的矛盾**（而且差点让我写成错的结论）：
//   `reference-edge-delete-control` 是 `<BUTTON 36×36@608,369>`、aria 逐字 `Delete connection`，
//   `pointer-events: auto`、可见 —— **可它的中心 `elementFromPoint` 返回的是 `path`（边的 SVG 路径）**。
//   我按 e 轮立的断言判它「被遮挡」，但**点那个坐标，边真的被删掉了（1 → 0）**。
//   ⇒ 「`elementFromPoint` 返回的不是它」**不等于**「它没被点到」。
//   （这是批次 133「`elementFromPoint` 返回的元素 ≠ 遮挡者」的**反向版本**：那条讲返回值不能当遮挡者，
//     这条讲返回值也不能当「谁接收了事件」。两者都不是「返回值 = 事件接收者」。）
//
// 🔑 真正要紧的问题不是机制，而是**用户该怎么点**：
//   如果「点边的任意位置都能删」 ⇒ 那个 × 不是按钮，只是长得像；
//   如果「只有 × 那一小块能删」 ⇒ 它是真按钮，只是被 SVG 压在下面。
//   判别实验（两个对照，单自变量）：
//   **A** 点**远离中点**的边位置（确保落在 `36×36` 之外）⇒ 预期只是切换选中，不删；
//   **B** 点 `36×36` 内**不在 path 上**的角落 ⇒ 若能删，说明确实是按钮的独立热区。
import { writeFileSync } from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { readConnect, canvasPos } from './jimeng-b136-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'f' };
const save = () => writeFileSync(new URL('./_tmp-b136f.json', import.meta.url), JSON.stringify(out, null, 1));
const 断言 = (名, 条件, 详情) => { const ok = !!!!条件; (out.护栏 = out.护栏 || []).push({ 名, 通过: ok, 详情 });
  log(`  ${ok ? '✅' : '⛔'} 断言·${名}：${JSON.stringify(详情)}`); save(); return ok; };
const 边数 = async () => (await readConnect(p)).边数;

async function 建一条边() {
  const plan = await p.evaluate(() => {
    const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
      const r = n.getBoundingClientRect();
      const h = n.querySelector('[data-testid="flow-node-source-handle"]');
      const hr = h ? h.getBoundingClientRect() : null;
      return { id: n.getAttribute('data-id'), x: r.x, y: r.y, right: r.right, bottom: r.bottom,
        手柄中心: hr ? [Math.round(hr.x + hr.width / 2), Math.round(hr.y + hr.height / 2)] : null };
    });
    const 源 = nodes.find((n) => n.手柄中心 && n.手柄中心[0] > 4 && n.手柄中心[0] < innerWidth - 4 && n.手柄中心[1] > 4 && n.手柄中心[1] < innerHeight - 4);
    if (!源) return null;
    const 落 = nodes.filter((n) => n.id !== 源.id).map((n) => {
      const L = Math.max(n.x, 4), R2 = Math.min(n.right, innerWidth - 4), T = Math.max(n.y, 66), B2 = Math.min(n.bottom, innerHeight - 66);
      const 宽 = R2 - L, 高 = B2 - T; if (!(宽 > 20 && 高 > 20)) return null;
      return { id: n.id, 面积: 宽 * 高, 落点: [Math.round((L + R2) / 2), Math.round((T + B2) / 2)] };
    }).filter(Boolean).sort((a, b) => b.面积 - a.面积);
    return { 源, 落: 落[0] || null };
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
  await p.mouse.up(); await p.waitForTimeout(2500); await settle(p, R);
  return plan;
}

/** 读某个点上「最顶层命中元素」+ 它的祖先链 + pointer-events。 */
const 命中 = (x, y) => p.evaluate(([px, py]) => {
  const h = document.elementFromPoint(px, py);
  if (!h) return null;
  const chain = []; for (let n = h; n && n !== document.body && chain.length < 8; n = n.parentElement) chain.push(n.tagName + '.' + String(n.className && n.className.baseVal !== undefined ? n.className.baseVal : n.className || '').split(' ')[0]);
  const s = getComputedStyle(h);
  return { tag: h.tagName, testid: h.getAttribute('data-testid'), aria: h.getAttribute('aria-label'),
    pe: s.pointerEvents, 祖先链: chain };
}, [x, y]);

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
out.起点边数 = await 边数();
if (out.起点边数 !== 0) {
  // 🔴 本轮前两次跑崩在中途，**把一条边留在了共享画布上**（状态行 `1 edge`）。
  //   护栏的正确姿势不是「记一笔继续」，而是**当场停手** ——
  //   在有残留的画布上做实验，后面每个读数都不可信。
  console.error(`⛔ 起点边数 ${out.起点边数} ≠ 0（画布有残留）—— 中止，不在有残留的画布上做实验`);
  save(); await b.close(); process.exit(3);
}
断言('起点边数 0', out.起点边数 === 0, { 边数: out.起点边数 });

// ---------------------------------------------------------------- ② 建边 + 选中
log('\n=== ② 建边 → 单击选中 ===');
// 🔴 兜底清理挂到 `process.on('uncaughtException')` 上：本轮已经崩过两次，
//   每次都把一条边留在**共享**画布上。**脚本崩了不等于画布干净了。**
process.on('uncaughtException', async (e) => {
  console.error('💥 未捕获异常：', e && e.message);
  try {
    const n = await 边数();
    if (n > 0) { const g = await keyGuard(p); if (g.safe) { await p.keyboard.press('Meta+z'); await p.waitForTimeout(2000); } }
    console.error('  兜底清理后边数 =', await 边数());
  } catch (_) { /* 清理也失败就如实说 */ }
  await b.close();
  process.exit(4);
});
const plan = await 建一条边();
out.建边计划 = plan;
断言('边已建成', (await 边数()) === 1, { 边数: await 边数() });
if ((await 边数()) !== 1) { log('  ⛔ 没建出线'); await b.close(); process.exit(0); }
const 边 = await p.evaluate(() => {
  const e = document.querySelector('.react-flow__edge');
  const r = e.getBoundingClientRect();
  const path = e.querySelector('path.react-flow__edge-path') || e.querySelector('path');
  const btn = document.querySelector('[data-testid="reference-edge-delete-control"]');
  const br = btn ? btn.getBoundingClientRect() : null;
  const ps = path ? getComputedStyle(path) : null;
  const btnChain = (() => { if (!btn) return null; const a = []; for (let n = btn; n && n !== document.body && a.length < 8; n = n.parentElement) a.push(n.tagName + '.' + String(n.className || '').split(' ')[0]); return a; })();
  const pathChain = (() => { if (!path) return null; const a = []; for (let n = path; n && n !== document.body && a.length < 8; n = n.parentElement) a.push(n.tagName + '.' + String(n.className && n.className.baseVal !== undefined ? n.className.baseVal : n.className || '').split(' ')[0]); return a; })();
  return { 边rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    边中点: [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)],
    边aria: e.getAttribute('aria-label'),
    pathPointerEvents: ps ? ps.pointerEvents : null,
    path祖先链: pathChain, 按钮祖先链: btnChain,
    按钮rect: br ? [Math.round(br.x), Math.round(br.y), Math.round(br.width), Math.round(br.height)] : null };
});
out.边 = 边;
log('  边 rect', JSON.stringify(边.边rect), '｜中点', JSON.stringify(边.边中点));
log('  path 的 pointer-events =', 边.pathPointerEvents);
log('  path  祖先链：', JSON.stringify(边.path祖先链));
log('  按钮 祖先链：', JSON.stringify(边.按钮祖先链));
save();
// 🔴 建边后边**可能已经是选中态**（上两次崩溃时画布有残留），此时再点一下会**取消选中**，
//   于是读到的 `data-state` 是 `null`、删除按钮 `不存在` —— 看起来像「按钮没了」，其实是点反了。
const 建边后态 = await p.evaluate(() => { const g = document.querySelector('[data-testid="reference-edge-interaction"]'); return g ? g.getAttribute('data-state') : null; });
out.建边后dataState = 建边后态;
log('  建边后 data-state «' + 建边后态 + '»');
if (建边后态 !== 'selected') {
  await p.mouse.click(边.边中点[0], 边.边中点[1]);
  await p.waitForTimeout(1800);
}
out.选中后 = { dataState: await p.evaluate(() => { const g = document.querySelector('[data-testid="reference-edge-interaction"]'); return g ? g.getAttribute('data-state') : null; }),
  按钮存在: !!(await p.evaluate(() => !!document.querySelector('[data-testid="reference-edge-delete-control"]'))) };
log('  选中后 data-state «' + out.选中后.dataState + '»｜删除按钮存在', out.选中后.按钮存在);
// 🔴 删除按钮**只在边被选中时存在** ⇒ 必须在**选中之后**才读得到它的 rect 与祖先链
//   （第一版在选中前读，拿到 null，后面 `B[0]` 直接抛错）。
out.删除按钮 = await p.evaluate(() => {
  const btn = document.querySelector('[data-testid="reference-edge-delete-control"]');
  if (!btn) return null;
  const r = btn.getBoundingClientRect(); const s = getComputedStyle(btn);
  const chain = []; for (let n = btn; n && n !== document.body && chain.length < 8; n = n.parentElement) chain.push(n.tagName + '.' + String(n.className || '').split(' ')[0]);
  return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
    pe: s.pointerEvents, opacity: s.opacity, zIndex: s.zIndex, position: s.position,
    aria: btn.getAttribute('aria-label'), 子元素: Array.from(btn.children).map((x) => x.tagName), 祖先链: chain };
});
out.边.按钮rect = out.删除按钮 && out.删除按钮.rect;
out.边.按钮祖先链 = out.删除按钮 && out.删除按钮.祖先链;
log('  删除按钮：', JSON.stringify(out.删除按钮));
save();

// ---------------------------------------------------------------- ③ 三个点的命中读数
log('\n=== ③ 三个点的命中读数（按钮中心 / 按钮内角 / 远离按钮的边位置） ===');
const B = out.边.按钮rect;
const 探点 = {
  按钮中心: [B[0] + 18, B[1] + 18],
  按钮左上内侧: [B[0] + 4, B[1] + 4],
  按钮右下内侧: [B[0] + 31, B[1] + 31],
};
// 远离按钮的边位置：沿边矩形取靠近 1/4 处，并确认不在按钮 rect 内
const 远 = [Math.round(out.边.边rect[0] + out.边.边rect[2] * 0.12), Math.round(out.边.边rect[1] + out.边.边rect[3] * 0.85)];
const 在按钮内 = (p2) => p2[0] >= B[0] && p2[0] <= B[0] + B[2] && p2[1] >= B[1] && p2[1] <= B[1] + B[3];
探点.远离按钮的边位置 = 在按钮内(远) ? [Math.round(out.边.边rect[0] + 8), Math.round(out.边.边rect[1] + 8)] : 远;
out.探点 = { ...探点, 按钮rect: B, 远离点是否在按钮内: 在按钮内(探点.远离按钮的边位置) };
log('  探点：', JSON.stringify(out.探点));
out.命中读数 = {};
for (const [k, v] of Object.entries(探点)) {
  if (k === '按钮rect') continue;
  const h = await 命中(v[0], v[1]);
  out.命中读数[k] = { 点: v, 命中: h };
  log(`  ${k} (${v}) → ${h ? h.tag + ' tid=' + h.testid + ' pe=' + h.pe : 'null'}`);
  log(`     祖先链 ${JSON.stringify(h && h.祖先链)}`);
}
save();

// ---------------------------------------------------------------- ④ 实验 A：点远离按钮的边位置
log('\n=== ④ 实验 A：点「远离按钮的边位置」（预期：只是切换选中，不删） ===');
const 前A = await 边数();
await p.mouse.click(探点.远离按钮的边位置[0], 探点.远离按钮的边位置[1]);
await p.waitForTimeout(2000); await settle(p, R);
const 后A = await 边数();
out.实验A = { 点: 探点.远离按钮的边位置, 前边数: 前A, 后边数: 后A, 删了: 后A < 前A,
  dataState: await p.evaluate(() => { const g = document.querySelector('[data-testid="reference-edge-interaction"]'); return g ? g.getAttribute('data-state') : null; }) };
log(`  边数 ${前A} → ${后A}｜data-state «${out.实验A.dataState}»｜${后A < 前A ? '🔉 删了（那就不是按钮，是"点边即删"）' : '⛔ 没删（说明是有热区限制的）'}`);
save();

// ---------------------------------------------------------------- ⑤ 实验 B：点按钮内不在 path 上的角
log('\n=== ⑤ 实验 B：点「按钮内、但命中元素不是 path」的角 ===');
const 角 = 探点.按钮左上内侧;
out.实验B前命中 = out.命中读数.按钮左上内侧.命中;
const 前B = await 边数();
await p.mouse.click(角[0], 角[1]);
await p.waitForTimeout(2000); await settle(p, R);
const 后B = await 边数();
out.实验B = { 点: 角, 该点命中: out.实验B前命中 && out.实验B前命中.tag, 前边数: 前B, 后边数: 后B, 删了: 后B < 前B };
log(`  边数 ${前B} → ${后B}｜${后B < 前B ? '🎉 删了' : '⛔ 没删'}`);
save();

// ---------------------------------------------------------------- ⑥ 结论与收尾
log('\n=== ⑥ 结论 ===');
out.判定 = {
  '点按钮中心会删': true,   // e 轮已验 1→0
  '点远离按钮的边位置会删': out.实验A.删了,
  '点按钮角（命中非 path）会删': out.实验B.删了,
  '按钮中心命中元素': out.命中读数.按钮中心.命中 && out.命中读数.按钮中心.命中.tag,
  '按钮角命中元素': out.命中读数.按钮左上内侧.命中 && out.命中读数.按钮左上内侧.命中.tag,
};
out.判定_删除是局部热区还是整条边 =
  out.判定['点按钮中心会删'] && !out.判定['点远离按钮的边位置会删'] ? '局部热区（是按钮）' : '整条边都能删（不是按钮）';
log('  判定：', out.判定_删除是局部热区还是整条边);
log('  明细：', JSON.stringify(out.判定));
save();
if ((await 边数()) > 0) { const g = await keyGuard(p); if (g.safe) { await p.keyboard.press('Meta+z'); await p.waitForTimeout(2200); await settle(p, R); } }
out.最终边数 = await 边数();
log('  最终边数 =', out.最终边数);
save();
const endCanvas = await canvasPos(p);
const 移动 = Object.keys(out.基线canvas).filter((id) => JSON.stringify(out.基线canvas[id]) !== JSON.stringify(endCanvas[id]));
const ids = await R.ids(), t = await R.testids();
out.收尾 = { 状态行: await R.status(), 选中: await R.selCount(), 浮层: await R.overlays(), zoom: await R.zoom(),
  credits: await R.credits(), minimap: await R.minimap(), 节点数: ids.length, testid种类: t.length, 节点被移动: 移动,
  节点差集: { 多: ids.filter((x) => !out.基线ids.includes(x)), 少: out.基线ids.filter((x) => !ids.includes(x)) },
  testid差集: { 多: t.filter((x) => !out.基线testids.includes(x)), 少: out.基线testids.filter((x) => !t.includes(x)) } };
log('  ', JSON.stringify(out.收尾));
save();
断言('边数回到 0', (await 边数()) === 0, { 边数: await 边数() });
断言('节点 canvas 坐标零位移', 移动.length === 0, { 移动 });
断言('节点 id 与基线逐个一致', out.收尾.节点差集.多.length === 0 && out.收尾.节点差集.少.length === 0, out.收尾.节点差集);
断言('静态 testid 与基线逐个一致', out.收尾.testid差集.多.length === 0 && out.收尾.testid差集.少.length === 0, out.收尾.testid差集);
save(); save();
log('\n✅ f 轮完成 → ./_tmp-b136f.json');
await b.close();
