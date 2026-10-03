// 批次 124 · a 轮（只读）：把「节点 N」小结面板**逐行**读全，并读它末行「查看项目信息」打开的东西。
//
// 🔑 靶子：`canvas-context.md:104-152` 记了面板 testid、几何、高度公式，
//   但**从没说清「计数为 0 的类型会不会出现」**。
//   而今天的画布**一个主体节点都没有**（批次 118/119 清理后），
//   面板实测 **6 行**：`图片 1 ｜ 视频 1 ｜ 文本 3 ｜ 音频 68 ｜ 时间线 2 ｜ 外部 1` —— **没有「主体」**。
//   批次 89 造过 1 个主体节点时是 **7 行**（含 `主体 1`）。
//   ⇒ 假设：**零个的类型不出现**。a 轮先把基线读全，b 轮做 A/B/A 验证。
//
// ⛔ 只打开面板并读它；「查看项目信息」也只**打开并读**（只读信息面板，未授权执行项一律不点）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b124a.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
out.start = { zoom: await zoom(), credits: await credits(), status: await status() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);

// ---- 当前画布按 class 的真实分类（用来核对面板的分组） ----
out.byClass = await p.evaluate(() => { const m = {};
  for (const n of document.querySelectorAll('.react-flow__node[data-id]')) {
    const c = (n.className || '').toString().split(' ').find((x) => x.startsWith('react-flow__node-')) || '?';
    m[c] = (m[c] || 0) + 1; }
  return { 总数: Object.values(m).reduce((a, x) => a + x, 0), 分类: m }; });
log('\n画布按 class 分类：', JSON.stringify(out.byClass));
save();

// ---- 打开面板（真实鼠标点击，落点现算 + 自检） ----
const pt = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-node-summary-trigger"]');
  const r = e.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
    const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 矩形: [r.x, r.y, r.width, r.height].map(Math.round) }; }
  return { __err: 'no-point' }; });
log('「节点 N」落点：', JSON.stringify(pt));
out.point = pt;
if (pt.__err) { log('⛔ 中止'); save(); await b.close(); process.exit(3); }
await p.mouse.click(pt.x, pt.y);
await p.waitForTimeout(1500);

out.panel = await p.evaluate(() => {
  const p = document.querySelector('[data-testid="canvas-node-summary-popover"]');
  if (!p) return { __err: 'no-panel' };
  const r = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const rows = Array.from(p.querySelectorAll('button,[role=button],[role=menuitem],li,div[data-testid]'))
    .filter((e) => { const q = e.getBoundingClientRect(); return q.height >= 20 && q.height <= 60 && q.width > 100; });
  // 去重：只留没有「同类祖先行」的
  const uniq = rows.filter((e) => !rows.some((o) => o !== e && o.contains(e)));
  return { 矩形: r(p), role: p.getAttribute('role'), 子元素数: p.children.length,
    逐字: (p.innerText || '').replace(/\s+/g, ' ').trim(),
    行: uniq.map((e) => ({ tag: e.tagName, tid: e.getAttribute('data-testid'), role: e.getAttribute('role'), 矩形: r(e),
      cls: (e.getAttribute('class') || '').toString().slice(0, 46),
      文字: (e.innerText || '').replace(/\s+/g, ' ').trim(),
      子元素: Array.from(e.children).map((k) => ({ tag: k.tagName, tid: k.getAttribute('data-testid'), 文字: (k.innerText || '').replace(/\s+/g, ' ').trim() })) })),
    内部testid: Array.from(p.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')) };
});
log('\n=== 面板 ===');
if (out.panel.__err) { log('  ', out.panel.__err); save(); await b.close(); process.exit(0); }
log('  矩形：', JSON.stringify(out.panel.矩形), '｜role：', out.panel.role, '｜内部 testid：', JSON.stringify(out.panel.内部testid));
log('  逐字：', JSON.stringify(out.panel.逐字));
out.panel.行.forEach((r, i) => log(`   行${i + 1} <${r.tag}> role=${r.role} ${JSON.stringify(r.矩形)} ${JSON.stringify(r.文字)}\n        子=${JSON.stringify(r.子元素)}`));
save();

// ---- 「查看项目信息」那一行：读它的身份，但**先不点** ----
const lastRow = out.panel.行[out.panel.行.length - 1];
out.lastRow = lastRow;
log('\n末行身份：', JSON.stringify({ tag: lastRow.tag, role: lastRow.role, tid: lastRow.tid, 文字: lastRow.文字, 矩形: lastRow.矩形 }));
save();

// ---- 打开「查看项目信息」（只读信息面板） ----
if (lastRow && /查看项目信息/.test(lastRow.文字)) {
  const hit = await p.evaluate((rect) => { for (let y = Math.ceil(rect[1]) + 2; y <= rect[1] + rect[3] - 2; y += 3)
    for (let x = Math.ceil(rect[0]) + 2; x <= rect[0] + rect[2] - 2; x += 3) { const e = document.elementFromPoint(x, y);
      if (e && e.closest('button,[role=button],[role=menuitem]') && (e.closest('button,[role=button],[role=menuitem]').innerText || '').includes('查看项目信息')) return { x, y }; }
    return null; }, lastRow.矩形);
  log('「查看项目信息」落点：', JSON.stringify(hit));
  if (hit) {
    await p.mouse.click(hit.x, hit.y);
    await p.waitForTimeout(1600);
    out.projectInfo = await p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu]'))
      .filter((m) => m.getBoundingClientRect().width > 1)
      .map((m) => { const q = m.getBoundingClientRect();
        return { role: m.getAttribute('role'), tid: m.getAttribute('data-testid'), 矩形: [q.x, q.y, q.width, q.height].map(Math.round),
          逐字: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300),
          按钮: Array.from(m.querySelectorAll('button,[role=button]')).map((x) => (x.innerText || x.getAttribute('aria-label') || '').replace(/\s+/g, ' ').trim()).filter(Boolean) }; }));
    log('\n=== 点「查看项目信息」之后的浮层 ===');
    out.projectInfo.forEach((m, i) => log(`   [${i}] role=${m.role} tid=${JSON.stringify(m.tid)} ${JSON.stringify(m.矩形)}\n       逐字=${JSON.stringify(m.逐字)}\n       按钮=${JSON.stringify(m.按钮)}`));
  }
}
save();

// ---- 收尾：Esc 关掉所有浮层，回到 0 选中 ----
await p.keyboard.press('Escape'); await p.waitForTimeout(1000);
await p.keyboard.press('Escape'); await p.waitForTimeout(1000);
out.收尾 = { 浮层数: await p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu]')).filter((m) => m.getBoundingClientRect().width > 1).length),
  选中: await p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length),
  zoom: await zoom(), status: await status() };
log('\n收尾：', JSON.stringify(out.收尾));
save();
log('\nDONE a');
process.exit(0);
