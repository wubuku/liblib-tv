// 批次 136 · g 轮：把删除按钮的**真实可点区**量化出来（f 轮已发现 36×36 的角点不动）。
//
// 🔑 f 轮定案了两件事：
//   ① 按钮中心 `elementFromPoint` 返回的 `path` **是按钮自己的内部图标**，不是遮挡者 ——
//      祖先链 `path → svg.relative → SPAN.contents → BUTTON.inline-flex → …`，
//      `BUTTON.inline-flex` 就在链上第 4 层；按钮的子元素 `SPAN` 带 `display: contents`
//      （盒子消失、子元素直接参与布局）⇒ 返回值落在按钮**内部**是完全正常的。
//      🔴 **这条订正了我 e 轮写反的断言**（「中心命中 path ⇒ 被遮挡」—— 恰好相反）。
//      📌 正确判据不是「返回值是不是目标本身」，也不是「看它的 pointer-events」，
//      而是 **走祖先链，看目标在不在这条链上**。
//   ② 点 36×36 的**角**（离中心 6px）**删不掉** ⇒ **几何框 ≠ 可点区**。
//
// 📌 本轮用 2px 步长扫一遍按钮矩形，把「命中按钮后代」的点集取出来，
//   得到真实热区的尺寸与形状。这是用户操作需要的精度：**要删连线得点准那个 × 图标。**
import { writeFileSync } from 'node:fs';
import { openCanvas, readers, settle, keyGuard } from './jimeng-b135-lib.mjs';
import { readConnect, canvasPos } from './jimeng-b136-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'g' };
const save = () => writeFileSync(new URL('./_tmp-b136g.json', import.meta.url), JSON.stringify(out, null, 1));
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
out.基线 = { 状态行: await R.status(), 节点数: (await R.ids()).length, testid种类: (await R.testids()).length };
out.基线ids = await R.ids();
out.基线testids = await R.testids();
out.基线canvas = await canvasPos(p);
log('基线：', JSON.stringify(out.基线));
save();
if ((await 边数()) !== 0) { console.error('⛔ 起点有残留边 —— 中止'); await b.close(); process.exit(3); }

// ---------------------------------------------------------------- 建边 → 选中
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
await p.mouse.move(plan.源.手柄中心[0], plan.源.手柄中心[1]); await p.waitForTimeout(300);
await p.mouse.down(); await p.waitForTimeout(250);
for (let i = 1; i <= 12; i++) {
  await p.mouse.move(Math.round(plan.源.手柄中心[0] + ((plan.落.落点[0] - plan.源.手柄中心[0]) * i) / 12),
                     Math.round(plan.源.手柄中心[1] + ((plan.落.落点[1] - plan.源.手柄中心[1]) * i) / 12));
  await p.waitForTimeout(55);
}
await p.waitForTimeout(500);
await p.mouse.up(); await p.waitForTimeout(2500); await settle(p, R);
log('建边后边数 =', await 边数());
save();
if ((await 边数()) !== 1) { log('⛔ 没建出线'); await b.close(); process.exit(0); }
const 边中点 = await p.evaluate(() => { const e = document.querySelector('.react-flow__edge'); const r = e.getBoundingClientRect();
  return [Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)]; });
const 态 = await p.evaluate(() => { const g = document.querySelector('[data-testid="reference-edge-interaction"]'); return g ? g.getAttribute('data-state') : null; });
log('建边后 data-state «' + 态 + '»');
if (态 !== 'selected') { await p.mouse.click(边中点[0], 边中点[1]); await p.waitForTimeout(1800); }
out.按钮 = await p.evaluate(() => { const btn = document.querySelector('[data-testid="reference-edge-delete-control"]'); if (!btn) return null;
  const r = btn.getBoundingClientRect();
  return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)], aria: btn.getAttribute('aria-label'),
    子元素HTML: btn.innerHTML.slice(0, 300) }; });
log('按钮：', JSON.stringify(out.按钮 && { rect: out.按钮.rect, aria: out.按钮.aria }));
save();
断言('删除按钮存在', !!out.按钮, { 按钮: out.按钮 });

// ---------------------------------------------------------------- 2px 扫描真实热区
log('\n=== 2px 步长扫描按钮矩形：哪些点真的命中按钮的后代 ===');
const B = out.按钮.rect;
out.扫描 = await p.evaluate((b) => {
  const btn = document.querySelector('[data-testid="reference-edge-delete-control"]');
  const 命中按钮 = [];
  const 未命中 = [];
  const 其它 = {};
  for (let y = b[1]; y < b[1] + b[3]; y += 2) {
    for (let x = b[0]; x < b[0] + b[2]; x += 2) {
      const h = document.elementFromPoint(x, y);
      if (h && (h === btn || btn.contains(h))) { 命中按钮.push([x, y]); continue; }
      未命中.push([x, y]);
      if (h) { const k = h.tagName + '.' + String(h.className && h.className.baseVal !== undefined ? h.className.baseVal : h.className || '').split(' ')[0];
        其它[k] = (其它[k] || 0) + 1; }
    }
  }
  const bb = 命中按钮.length ? {
    x0: Math.min(...命中按钮.map((q) => q[0])), x1: Math.max(...命中按钮.map((q) => q[0])),
    y0: Math.min(...命中按钮.map((q) => q[1])), y1: Math.max(...命中按钮.map((q) => q[1])),
  } : null;
  return { 扫描步长: 2, 按钮rect: b, 命中点数: 命中按钮.length, 未命中点数: 未命中.length,
    总点数: 命中按钮.length + 未命中.length,
    命中区域包围盒: bb ? [bb.x0, bb.y0, bb.x1 - bb.x0 + 1, bb.y1 - bb.y0 + 1] : null,
    命中区域宽高: bb ? [bb.x1 - bb.x0 + 1, bb.y1 - bb.y0 + 1] : null,
    未命中处的元素分布: 其它,
    命中点样例: 命中按钮.slice(0, 8),
    未命中点样例: 未命中.slice(0, 8) };
}, B);
log('  按钮几何 ', JSON.stringify(B));
log('  扫描点数 ', out.扫描.总点数, '｜命中按钮后代', out.扫描.命中点数, '｜未命中', out.扫描.未命中点数);
log('  命中区域包围盒（相对按钮左上角）', JSON.stringify(out.扫描.命中区域包围盒));
log('  未命中处的元素分布', JSON.stringify(out.扫描.未命中处的元素分布));
save();
断言('真实热区小于 36×36（几何框 ≠ 可点区）', out.扫描.命中点数 < out.扫描.总点数, { 命中: out.扫描.命中点数, 总: out.扫描.总点数 });

// ---------------------------------------------------------------- 验证：点热区中心能删、点热区外不能删
log('\n=== 验证 ===');
const 框 = out.扫描.命中区域包围盒;
const 热区中心 = [Math.round((框[0] + 框[0] + 框[2] - 1) / 2), Math.round((框[1] + 框[1] + 框[3] - 1) / 2)];
const 热区外 = 未命中点(out.扫描);
out.热区中心 = 热区中心; out.热区外点 = 热区外;
log('  热区中心', JSON.stringify(热区中心), '｜热区外点', JSON.stringify(热区外));
const 前 = await 边数();
await p.mouse.click(热区外[0], 热区外[1]);
await p.waitForTimeout(2000); await settle(p, R);
const 中 = await 边数();
out.点热区外 = { 点: 热区外, 前边数: 前, 后边数: 中, 删了: 中 < 前 };
log(`  点热区外：边数 ${前} → ${中}｜${中 < 前 ? '🔉 删了' : '⛔ 没删（符合预期）'}`);
save();
await p.mouse.click(热区中心[0], 热区中心[1]);
await p.waitForTimeout(2000); await settle(p, R);
const 后 = await 边数();
out.点热区中心 = { 点: 热区中心, 前边数: 中, 后边数: 后, 删了: 后 < 中 };
log(`  点热区中心：边数 ${中} → ${后}｜${后 < 中 ? '🎉 删了' : '⛔ 没删'}`);
save();
断言('点真实热区中心能删掉连线', 后 === 0, { 边数: 后 });

// ---------------------------------------------------------------- 收尾
if ((await 边数()) > 0) { const g = await keyGuard(p); if (g.safe) { await p.keyboard.press('Meta+z'); await p.waitForTimeout(2200); await settle(p, R); } }
const endCanvas = await canvasPos(p);
const 移动 = Object.keys(out.基线canvas).filter((id) => JSON.stringify(out.基线canvas[id]) !== JSON.stringify(endCanvas[id]));
const ids = await R.ids(), t = await R.testids();
out.收尾 = { 状态行: await R.status(), 选中: await R.selCount(), 浮层: await R.overlays(), zoom: await R.zoom(),
  credits: await R.credits(), minimap: await R.minimap(), 节点数: ids.length, testid种类: t.length, 节点被移动: 移动,
  边数: await 边数(),
  节点差集: { 多: ids.filter((x) => !out.基线ids.includes(x)), 少: out.基线ids.filter((x) => !ids.includes(x)) },
  testid差集: { 多: t.filter((x) => !out.基线testids.includes(x)), 少: out.基线testids.filter((x) => !t.includes(x)) } };
log('  ', JSON.stringify(out.收尾));
save();
断言('边数回到 0', (await 边数()) === 0, { 边数: await 边数() });
断言('节点 canvas 坐标零位移', 移动.length === 0, { 移动 });
断言('节点 id 与基线逐个一致', out.收尾.节点差集.多.length === 0 && out.收尾.节点差集.少.length === 0, out.收尾.节点差集);
断言('静态 testid 与基线逐个一致', out.收尾.testid差集.多.length === 0 && out.收尾.testid差集.少.length === 0, out.收尾.testid差集);
save(); save();
log('\n✅ g 轮完成 → ./_tmp-b136g.json');
await b.close();

function 未命中点(扫) {
  // 从按钮矩形里挑一个未命中按钮的点（用元素分布里最常见的那个元素所在处反推不可靠，改成直接重扫）
  return 扫.未命中点样例 && 扫.未命中点样例[0] ? 扫.未命中点样例[0] : [0, 0];
}
