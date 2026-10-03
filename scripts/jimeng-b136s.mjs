// 批次 136 · s 轮：给「选中连线后出现的 × 删除按钮」拍一张可用的截图。
//
// 🔑 批次 136 新写进手册的「怎么删掉一条连线」指向一个**此前从未被拍过、用户也从未见过**的 UI 元素：
//   选中连线后，线中点上出现一个 `<BUTTON 36×36>`，aria 逐字 `Delete connection`。
//   只用文字描述它，用户在画布上找不到它 —— **文档要能被用上，就得让它可见**。
//
// 🛡 共享画布纪律：拍完**当场删掉这条边**，并硬断言边数回到 0、节点 id 与基线逐个一致。
//   截图脚本与取证脚本同一套护栏，不因为「只是拍张照」就放松。
//
// 📌 裁剪区域要同时装下：连线的两端节点 + 线中点的 × 按钮。
//   边是三次贝塞尔，中点是曲线上最靠上的点；按钮 `36×36` 骑在它上面。
import { writeFileSync } from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { readConnect, canvasPos } from './jimeng-b136-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 's' };
const save = () => writeFileSync(new URL('./_tmp-b136s.json', import.meta.url), JSON.stringify(out, null, 1));
const 断言 = (名, 条件, 详情) => { const ok = !!!!条件; (out.护栏 = out.护栏 || []).push({ 名, 通过: ok, 详情 });
  log(`  ${ok ? '✅' : '⛔'} 断言·${名}：${JSON.stringify(详情)}`); save(); return ok; };
const 边数 = async () => (await readConnect(p)).边数;
process.on('uncaughtException', async (e) => {
  console.error('💥 未捕获异常：', e && e.message);
  try { if ((await 边数()) > 0) { const g = await keyGuard(p); if (g.safe) { await p.keyboard.press('Meta+z'); await p.waitForTimeout(2000); } } } catch (_) {}
  await b.close(); process.exit(4);
});

await keyGuard(p);
await settle(p, R);
out.基线ids = await R.ids();
out.基线testids = await R.testids();
out.基线 = { 状态行: await R.status(), 节点数: out.基线ids.length, testid种类: out.基线testids.length };
log('基线：', JSON.stringify(out.基线));
save();
if ((await 边数()) !== 0) { console.error('⛔ 起点有残留边 —— 中止'); await b.close(); process.exit(3); }

// ---- 建边
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
    const 宽 = R2 - L, 高 = B2 - T; if (!(宽 > 20 && 高 > 20)) return null;
    return { id: n.id, 标题: n.标题, 面积: 宽 * 高, 落点: [Math.round((L + R2) / 2), Math.round((T + B2) / 2)] };
  }).filter(Boolean).sort((a, b) => b.面积 - a.面积);
  return { 源, 落: 落[0] || null };
});
out.计划 = plan;
await p.mouse.move(plan.源.手柄中心[0], plan.源.手柄中心[1]); await p.waitForTimeout(300);
await p.mouse.down(); await p.waitForTimeout(250);
for (let i = 1; i <= 12; i++) {
  await p.mouse.move(Math.round(plan.源.手柄中心[0] + ((plan.落.落点[0] - plan.源.手柄中心[0]) * i) / 12),
                     Math.round(plan.源.手柄中心[1] + ((plan.落.落点[1] - plan.源.手柄中心[1]) * i) / 12));
  await p.waitForTimeout(55);
}
await p.waitForTimeout(500); await p.mouse.up(); await p.waitForTimeout(2500); await settle(p, R);
log('建边后边数 =', await 边数());
save();
断言('边已建成', (await 边数()) === 1, { 边数: await 边数() });
if ((await 边数()) !== 1) { log('⛔ 没建出线'); await b.close(); process.exit(0); }

// ---- 选中边 → × 出现
const 边中点 = await p.evaluate(() => { const e = document.querySelector('.react-flow__edge'); const r = e.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
const 态0 = await p.evaluate(() => { const g = document.querySelector('[data-testid="reference-edge-interaction"]'); return g ? g.getAttribute('data-state') : null; });
if (态0 !== 'selected') { await p.mouse.click(边中点[0], 边中点[1]); await p.waitForTimeout(1600); }
out.选中态 = await p.evaluate(() => { const g = document.querySelector('[data-testid="reference-edge-interaction"]'); return g ? g.getAttribute('data-state') : null; });
log('选中态 data-state «' + out.选中态 + '»');
save();
断言('边已选中', out.选中态 === 'selected', { dataState: out.选中态 });
const 钮 = await p.evaluate(() => { const e = document.querySelector('[data-testid="reference-edge-delete-control"]'); if (!e) return null;
  const r = e.getBoundingClientRect(); return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], aria: e.getAttribute('aria-label') }; });
out.删除钮 = 钮;
log('删除钮：', JSON.stringify(钮));
save();
断言('× 按钮存在', !!钮, { 钮 });

// ---- 算裁剪框：两端节点 ∪ × 按钮，留 24px 余量，夹在视口内
const clip = await p.evaluate(() => {
  const e = document.querySelector('.react-flow__edge');
  const r = e.getBoundingClientRect();
  const ends = e.querySelectorAll('circle, path');
  let x0 = r.x, y0 = r.y, x1 = r.right, y1 = r.bottom;
  const btn = document.querySelector('[data-testid="reference-edge-delete-control"]');
  if (btn) { const q = btn.getBoundingClientRect(); x0 = Math.min(x0, q.x); y0 = Math.min(y0, q.y); x1 = Math.max(x1, q.right); y1 = Math.max(y1, q.bottom); }
  const M = 26;
  let cx = Math.max(0, Math.floor(x0 - M)), cy = Math.max(0, Math.floor(y0 - M));
  let cw = Math.min(innerWidth - cx, Math.ceil(x1 - x0 + M * 2)), ch = Math.min(innerHeight - cy, Math.ceil(y1 - y0 + M * 2));
  return { x: cx, y: cy, width: cw, height: ch };
});
out.clip = clip;
log('裁剪框：', JSON.stringify(clip));
save();

// ---- 拍
// 🔴 `import.meta.url` 已经指向 `scripts/`，所以只需**退一级**。
//   第一版写成 `../../` ⇒ 截图落到了**仓库外面**（`/Users/…/wubuku/docs/…`，少了一层 `liblib-tv`）。
//   ⇒ 立规：**拼仓库内路径时先确认基准目录层级**，别凭感觉数 `../`。
const 仓库根 = new URL('../', import.meta.url).pathname;
const 文件 = 仓库根 + 'docs/user-manual/jimeng-canvas/screenshots/111-edge-selected-delete-button.png';
if (!文件.startsWith(仓库根 + 'docs/')) { console.error('⛔ 截图路径跑出仓库：', 文件, '基准', 仓库根); process.exit(2); }
await p.mouse.move(clip.x + 4, clip.y + 4);
await p.waitForTimeout(900);
await p.screenshot({ path: 文件, clip: { x: clip.x, y: clip.y, width: clip.width, height: clip.height } });
out.文件 = 文件;
log('已截图 →', 文件);
save();

// ---- 拍完立刻删边归位
out.拍前复查 = await p.evaluate(() => ({
  按钮还在: !!document.querySelector('[data-testid="reference-edge-delete-control"]'),
  dataState: (() => { const g = document.querySelector('[data-testid="reference-edge-interaction"]'); return g ? g.getAttribute('data-state') : null; })(),
}));
log('拍前复查：', JSON.stringify(out.拍前复查));
await p.mouse.click(钮.rect[0] + 18, 钮.rect[1] + 18);
await p.waitForTimeout(2500); await settle(p, R);
out.拍后边数 = await 边数();
log('拍后边数 =', out.拍后边数);
save();
if (out.拍后边数 > 0) { const g = await keyGuard(p); if (g.safe) { await p.keyboard.press('Meta+z'); await p.waitForTimeout(2200); await settle(p, R); } }
const ids = await R.ids(), t = await R.testids();
out.收尾 = { 状态行: await R.status(), 边数: await 边数(), 选中: await R.selCount(), 浮层: await R.overlays(),
  zoom: await R.zoom(), credits: await R.credits(), minimap: await R.minimap(), 节点数: ids.length, testid种类: t.length,
  节点差集: { 多: ids.filter((x) => !out.基线ids.includes(x)), 少: out.基线ids.filter((x) => !ids.includes(x)) },
  testid差集: { 多: t.filter((x) => !out.基线testids.includes(x)), 少: out.基线testids.filter(x => !t.includes(x)) } };
log('  ', JSON.stringify(out.收尾));
save();
断言('边数回到 0', (await 边数()) === 0, { 边数: await 边数() });
断言('节点 id 与基线逐个一致', out.收尾.节点差集.多.length === 0 && out.收尾.节点差集.少.length === 0, out.收尾.节点差集);
断言('静态 testid 与基线逐个一致', out.收尾.testid差集.多.length === 0 && out.收尾.testid差集.少.length === 0, out.收尾.testid差集);
save(); save();
log('\n✅ s 轮完成 → ./_tmp-b136s.json');
await b.close();
