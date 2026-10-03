// 批次 127 · g 轮：查「每页 10 条结果是不是只有 7 条看得见」。
//
// 🔑 f 轮留下的一处可疑读数：
//   · 面板 `320×604` = 56(输入行) + 36(页签行) + 512(结果区)
//     结果区 512 = 视口 460 + 分页条 52（无分页时视口就是 512）
//   · 结果行 `BUTTON 304×64`，行距 **68**，**DOM 里渲染了 10 行**
//     ⇒ 10×68 = 680 ≫ 460
//   · 而 `canvas-search-results-viewport` 的 `scrollHeight === clientHeight === 460`
//     ⇒ **这个元素本身不溢出、滚不动**
//   三个假设：
//     H1「行 8/9/10 被裁掉且无法滚动到」 ⇒ 真缺陷，需报
//     H2「某个祖先在滚」 ⇒ 找出那个祖先并写明滚动手法
//     H3「行高不是 68」 ⇒ 我把「行矩形 y 的步长」当成了「行占位高度」（行 64 但步长 68）
//   判据（能区分三者）：对每一行取矩形中心做 `elementFromPoint`，
//     同时把 `canvas-search-results-viewport` → `role=list` → 结果区的**每一层祖先**的
//     `scrollHeight / clientHeight / overflow` 全读出来；再在结果区上方滚滚轮看谁动了。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'g' };
const save = () => writeFileSync(new URL('./_tmp-b127g.json', import.meta.url), JSON.stringify(out, null, 1));
const shotDir = new URL('./_tmp-b127a-shots/', import.meta.url);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);

out.start = { 浮层: await overlays(), 选中: await sel(), zoom: await zoom(), credits: await credits(), status: await status() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);

for (let i = 0; i < 2; i++) { if (await overlays()) { await p.keyboard.press('Escape'); await p.waitForTimeout(1100); } }
const openPt = await p.evaluate(() => { const t = Array.from(document.querySelectorAll('[data-testid="canvas-panel-launcher"]')).find((e) => (e.getAttribute('aria-label') || '') === '搜索');
  if (!t) return null; const r = t.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
    const h = document.elementFromPoint(x, y); if (h && (h === t || t.contains(h))) return { x, y }; } return null; });
if (openPt) { await p.mouse.click(openPt.x, openPt.y); await p.waitForTimeout(2000); }
await p.keyboard.press('Escape'); await p.waitForTimeout(1100);
await p.mouse.click(openPt.x, openPt.y); await p.waitForTimeout(2000); // 干净地开一次

// ---- 每一层祖先的滚动属性 ----
out.滚动链 = await p.evaluate(() => {
  const vp = document.querySelector('[data-testid="canvas-search-results-viewport"]');
  if (!vp) return { __err: 'no-viewport' };
  const R = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const chain = []; let n = vp;
  for (let i = 0; i < 7 && n && n !== document.body; i++) {
    const st = getComputedStyle(n);
    chain.push({ d: i, tag: n.tagName, tid: n.getAttribute('data-testid'), role: n.getAttribute('role'),
      rect: R(n), scrollHeight: n.scrollHeight, clientHeight: n.clientHeight,
      scrollTop: n.scrollTop, overflowY: st.overflowY, overflowX: st.overflowX,
      可滚: n.scrollHeight > n.clientHeight + 1 });
    n = n.parentElement;
  }
  return chain;
});
log('\n=== ① 视口往上每一层的滚动属性 ===');
out.滚动链.forEach((c) => log(`  ${'  '.repeat(c.d)}<${c.tag}> tid=${c.tid ?? '-'} role=${c.role ?? '-'} ${JSON.stringify(c.rect)} scrollH=${c.scrollHeight} clientH=${c.clientHeight} scrollTop=${c.scrollTop} overflowY=${c.overflowY} 可滚=${c.可滚}`));
save();

// ---- 逐行可见性 ----
out.逐行 = await p.evaluate(() => {
  const rows = Array.from(document.querySelectorAll('[data-testid^="canvas-search-result-node_"]'));
  const vp = document.querySelector('[data-testid="canvas-search-results-viewport"]');
  const vr = vp.getBoundingClientRect();
  return { 行数: rows.length, 视口: [vr.x, vr.y, vr.width, vr.height].map(Math.round),
    视口底: Math.round(vr.y + vr.height), 视口顶: Math.round(vr.y),
    行: rows.map((r) => { const q = r.getBoundingClientRect();
      const cx = q.x + q.width / 2, cy = q.y + q.height / 2;
      const h = document.elementFromPoint(cx, cy);
      const inVp = q.y >= vr.y && q.y + q.height <= vr.y + vr.height;
      return { tid: r.getAttribute('data-testid'), rect: [q.x, q.y, q.width, q.height].map(Math.round),
        底: Math.round(q.y + q.height), 完全在视口内: inVp,
        中心命中: h ? (h === r ? '行自身' : (r.contains(h) ? '行的后代:' + h.tagName : '别的元素:' + h.tagName + (h.getAttribute('data-testid') ? '[' + h.getAttribute('data-testid') + ']' : ''))) : 'null',
        中心是否可点: !!(h && (h === r || r.contains(h))) }; }) };
});
log('\n=== ② 逐行可见性（视口 ', JSON.stringify(out.逐行.视口), ' 底边 y=', out.逐行.视口.底, '）===');
out.逐行.行.forEach((r, i) => log(`  [${i + 1}] ${JSON.stringify(r.rect)} 底=${r.底} 完全在内=${r.完全在视口内} 中心命中=${r.中心命中}`));
out.不可见的行 = out.逐行.行.filter((r) => !r.完全在视口内).map((r, i) => r.tid);
out.看不见且点不到的行 = out.逐行.行.filter((r) => !r.中心是否可点).map((r) => r.tid);
log('  超出视口的行：', JSON.stringify(out.不可见的行));
log('  中心点不到的行：', JSON.stringify(out.看不见且点不到的行));
await p.screenshot({ path: new URL('14-rows-visibility.png', shotDir).pathname, clip: { x: 750, y: 140, width: 350, height: 480 } });
save();

// ---- 在结果区滚滚轮，看哪一层的 scrollTop 变 ----
out.滚轮 = {};
const center = [out.逐行.视口[0] + out.逐行.视口[2] / 2, out.逐行.视口[1] + 40];
await p.mouse.move(center[0], center[1]);
const before = await p.evaluate(() => { const vp = document.querySelector('[data-testid="canvas-search-results-viewport"]');
  const list = document.querySelector('[data-testid="canvas-feature-panel"] [role=list]');
  return { 视口scrollTop: vp ? vp.scrollTop : null, 列表scrollTop: list ? list.scrollTop : null, 文档scrollY: window.scrollY }; });
await p.mouse.wheel(0, 400);
await p.waitForTimeout(800);
const after = await p.evaluate(() => { const vp = document.querySelector('[data-testid="canvas-search-results-viewport"]');
  const list = document.querySelector('[data-testid="canvas-feature-panel"] [role=list]');
  return { 视口scrollTop: vp ? vp.scrollTop : null, 列表scrollTop: list ? list.scrollTop : null, 文档scrollY: window.scrollY }; });
out.滚轮 = { 落点: center, 前: before, 后: after, 有变化: JSON.stringify(before) !== JSON.stringify(after) };
log('\n=== ③ 在结果区纵向滚轮 ===\n  ', JSON.stringify(out.滚轮));
save();

// ---- 收尾 ----
await p.keyboard.press('Escape'); await p.waitForTimeout(1300);
await p.keyboard.press('Escape'); await p.waitForTimeout(1300);
out.收尾 = { 浮层: await overlays(), 面板在: await p.evaluate(() => !!document.querySelector('[data-testid="canvas-feature-panel"]')),
  选中: await sel(), zoom1: await zoom(), credits: await credits(), status: await status() };
await p.waitForTimeout(1200);
out.收尾.zoom2 = await zoom();
log('\n收尾：', JSON.stringify(out.收尾));
save();
log('\nDONE g');
process.exit(0);
