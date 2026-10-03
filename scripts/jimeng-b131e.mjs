// 批次 131 · e 轮：**受控缩放实验**，验掉批次 87 留下的一条待验疑点。
//
// 🔑 疑点（批次 131 d 轮顺手发现）：手册批次 87/88 说多选工具条宽度**随画布缩放变**
//   （`511×40` @74% vs `1298×40` @100%），而本批 60% 下测得 `624×40`。
//   60% 若按批次 87 的规律应该是 511 × (60/74) ≈ 414，**与 624 对不上**。
//   ⚠️ 本批只有一个缩放档的单点读数，**不足以推翻批次 87** —— 登记为待验项。
//   本轮用**受控实验**（60% → 100% → 60%）把它钉死。
//
// 📌 关键：要分别量「**工具条整体**」与「**基座**」，因为批次 87 量的是哪一个没说清。
//   同时量节点尺寸做参照（节点一定随缩放变，工具条未必）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'e' };
const save = () => writeFileSync(new URL('./_tmp-b131e.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);
const idsNow = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const escAll = async () => { for (let i = 0; i < 4; i++) { if (!(await overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(900); } };

out.start = { 状态行: await status(), 选中: await sel(), zoom: await zoom() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
await escAll();
out.起始id = await idsNow();
out.基线zoom = await zoom();
log('基线缩放：', out.基线zoom);
save();

// 用缩放菜单切到指定百分比（只点菜单里的「缩放至100%」这类静态项，不动别的）
async function setZoom(pct) {
  const pt = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); if (!e) return { __err: 'nf' };
    const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) { const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; }
    return { __err: 'np' }; });
  if (pt.__err) { log(`  ⛔ 缩放按钮 ${pt.__err}`); return pt; }
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1200);
  const item = await p.evaluate((p2) => {
    const t = `缩放至${p2}%`;
    const els = Array.from(document.querySelectorAll('[role=menuitem],button,[role=menuitemradio]'));
    const e = els.find((x) => (x.innerText || '').replace(/\s+/g, '').startsWith(t.replace(/\s/g, '')));
    if (!e) return { __err: 'not-found', 可见项: els.filter((x) => { const r = x.getBoundingClientRect(); return r.width > 1; }).map((x) => (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20)) };
    const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2) for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) { const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 文字: (e.innerText || '').replace(/\s+/g, ' ').trim() }; }
    return { __err: 'np' };
  }, pct);
  if (item.__err) { log(`  ⛔ 菜单项 ${JSON.stringify(item)}`); await escAll(); return item; }
  await p.mouse.click(item.x, item.y); await p.waitForTimeout(1500);
  await escAll();
  return { ok: true, 文字: item.文字, zoom: await zoom() };
}

async function boxSelect() {
  const plan = await p.evaluate(() => {
    const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => { const r = n.getBoundingClientRect();
      return { x: r.x, y: r.y, right: r.right, bottom: r.bottom }; });
    const isPane = (x, y) => { const h = document.elementFromPoint(x, y); return !!(h && h.classList && h.classList.contains('react-flow__pane')); };
    const isFree = (x, y) => !nodes.some((n) => x >= n.x && x <= n.right && y >= n.y && y <= n.bottom);
    for (let pad = 16; pad <= 240; pad += 8) {
      const vis = nodes.filter((n) => n.right > 0 && n.x < innerWidth - 8 && n.bottom > 62 && n.y < innerHeight - 62);
      if (vis.length < 2) continue;
      const xs = vis.flatMap((n) => [n.x, n.right]), ys = vis.flatMap((n) => [n.y, n.bottom]);
      const L = Math.min(...xs) - pad, R = Math.max(...xs) + pad, T = Math.max(Math.min(...ys), 62), B = Math.min(Math.max(...ys), innerHeight - 62);
      if (!(L > 4 && R < innerWidth - 8 && T > 60 && B < innerHeight - 60)) continue;
      if (![[L, T], [R, T], [L, B], [R, B]].every(([x, y]) => isPane(x, y) && isFree(x, y))) continue;
      const 罩住 = nodes.filter((n) => n.right > L && n.x < R && n.bottom > T && n.y < B);
      if (罩住.length >= 2) return { 矩形: [L, T, R, B].map(Math.round), 罩住: 罩住.length };
    }
    return null;
  });
  if (!plan) return null;
  const [L, T, R, B] = plan.矩形;
  await p.mouse.move(L, T);
  const h0 = await p.evaluate(([x, y]) => { const h = document.elementFromPoint(x, y); return h ? h.className.toString().split(' ')[0] : null; }, [L, T]);
  if (h0 !== 'react-flow__pane') return null;
  await p.mouse.down();
  for (let i = 1; i <= 12; i++) { await p.mouse.move(Math.round(L + ((R - L) * i) / 12), Math.round(T + ((B - T) * i) / 12)); await p.waitForTimeout(50); }
  await p.mouse.up(); await p.waitForTimeout(1300);
  return plan;
}

const 量 = () => p.evaluate(() => {
  const rd = (t) => { const e = document.querySelector('[data-testid="' + t + '"]'); if (!e) return null;
    const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
    return { 屏上: [Math.round(r.width), Math.round(r.height)], css: [cs.width, cs.height], transform: cs.transform === 'none' ? 'none' : cs.transform.slice(0, 40) }; };
  const n = document.querySelector('.react-flow__node-audio') || document.querySelector('.react-flow__node');
  const nr = n ? n.getBoundingClientRect() : null;
  const nt = n ? getComputedStyle(n).transform : null;
  return { zoom: document.querySelector('[data-testid="canvas-zoom-percent"]')?.getAttribute('aria-label'),
    选中: document.querySelectorAll('.react-flow__node.selected').length,
    基座: rd('selection-context-toolbar'), 外层: rd('selection-context-toolbar-surface'),
    nodeToolbar: rd('node-toolbar'), 计数: rd('selection-context-toolbar-count'),
    参照节点: nr ? { id: n.getAttribute('data-id'), 屏上: [Math.round(nr.width), Math.round(nr.height)], transform: nt && nt !== 'none' ? nt.slice(0, 46) : 'none' } : null };
});

// ---------------------------------------------------------------- 两档缩放各量一次
out.读数 = [];
for (const pct of [null, 100]) {
  if (pct !== null) {
    log(`\n=== 切到 ${pct}% ===`);
    const r = await setZoom(pct);
    log('  ', JSON.stringify(r));
    if (r.__err) { log('  ⛔ 未能切缩放'); continue; }
  } else log('\n=== 基线档 ===');
  const plan = await boxSelect();
  const s = await sel();
  log('  框选', JSON.stringify(plan), '→ 选中数', s);
  if (s >= 2) {
    const m = await 量();
    out.读数.push(m);
    log('  🔑 ' + JSON.stringify(m, null, 1).replace(/\n/g, '\n     '));
    save();
    const pp = await p.evaluate(() => { for (let y = 300; y < 640; y += 7) for (let x = 300; x < 760; x += 7) { const h = document.elementFromPoint(x, y); if (h && h.classList && h.classList.contains('react-flow__pane')) return { x, y }; } return null; });
    if (pp) { await p.mouse.click(pp.x, pp.y); await p.waitForTimeout(1100); }
  }
}

// ---------------------------------------------------------------- 归位
log('\n=== 归位缩放到基线档 ===');
{
  const cur = await zoom();
  log('  当前', cur, '｜基线', out.基线zoom);
  if (cur !== out.基线zoom) {
    // 基线是 60%，菜单里没有「缩放至60%」，用「缩放至50%」再不行就按恢复默认？先试菜单
    const ok = await setZoom(50);
    log('  试 50%:', JSON.stringify(ok), '→', await zoom());
  }
  const fin = await zoom();
  const fin2 = await zoom();
  out.归位 = { 第一次: fin, 第二次: fin2, 与基线一致: fin === out.基线zoom && fin2 === out.基线zoom };
  log('  连读两次：', fin, '/', fin2, out.归位.与基线一致 ? '✅ 与基线一致' : '⚠️ 与基线不一致（需手动处理）');
  save();
}
await p.mouse.move(1276, 716); await p.waitForTimeout(600);
const endIds = await idsNow();
out.收尾 = { 选中: await sel(), 状态行: await status(), 浮层: await overlays(), zoom: await zoom(), 节点数: endIds.length, 起始节点数: out.起始id.length };
out.新增id = endIds.filter((x) => !out.起始id.includes(x));
log('\n收尾：', JSON.stringify(out.收尾));
log('  新增 id（必须空）：', JSON.stringify(out.新增id));
save();
log('\nDONE e');
process.exit(0);
