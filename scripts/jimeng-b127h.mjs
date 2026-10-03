// 批次 127 · h 轮：b 轮在页签行右端读到一个**没有文字、没有 aria 的 24×24 圆钮**
// （`BUTTON [1045,118,24,24]`，截图里是个「›」），c 轮证明**只有横向滚动**才能看到后三个页签。
// 那么：点这个圆钮能不能把页签翻过去？—— 这是「用户到底怎么够到「时间线 / 组 / 其他」」的最后一块。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'h' };
const save = () => writeFileSync(new URL('./_tmp-b127h.json', import.meta.url), JSON.stringify(out, null, 1));
const shotDir = new URL('./_tmp-b127a-shots/', import.meta.url);

const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);
const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);

out.start = { 浮层: await overlays(), zoom: await zoom(), credits: await credits() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
for (let i = 0; i < 2; i++) { if (await overlays()) { await p.keyboard.press('Escape'); await p.waitForTimeout(1100); } }
const openPt = await p.evaluate(() => { const t = Array.from(document.querySelectorAll('[data-testid="canvas-panel-launcher"]')).find((e) => (e.getAttribute('aria-label') || '') === '搜索');
  if (!t) return null; const r = t.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
    const h = document.elementFromPoint(x, y); if (h && (h === t || t.contains(h))) return { x, y }; } return null; });
if (openPt) { await p.mouse.click(openPt.x, openPt.y); await p.waitForTimeout(2000); }

// ---- 页签行里的「无文字按钮」是谁 ----
out.无名按钮 = await p.evaluate(() => {
  const panel = document.querySelector('[data-testid="canvas-feature-panel"]');
  const R = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const tabsRow = panel.querySelector('[role=tablist]').getBoundingClientRect();
  return Array.from(panel.querySelectorAll('button')).filter((e) => { const r = e.getBoundingClientRect();
      return r.width > 1 && r.y >= tabsRow.y - 2 && r.y + r.height <= tabsRow.y + tabsRow.height + 2 && !e.getAttribute('role'); })
    .map((e) => { const r = e.getBoundingClientRect(); const st = getComputedStyle(e);
      return { rect: R(e), 文字: (e.innerText || '').trim(), aria: e.getAttribute('aria-label'), tid: e.getAttribute('data-testid'),
        父tid: e.parentElement.getAttribute('data-testid'), 父rect: R(e.parentElement),
        borderRadius: st.borderRadius, background: st.backgroundColor, 禁用: e.hasAttribute('disabled'),
        svg: Array.from(e.querySelectorAll('svg')).map((s) => { const q = s.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); }),
        可命中: (() => { for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
          const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return [x, y]; } return null; })() }; });
});
log('\n=== ① 页签行里的无名按钮 ===\n  ', JSON.stringify(out.无名按钮, null, 1));
save();

// ---- 点它，看 scrollLeft 变不变；连点几次到头 ----
const sl = () => p.evaluate(() => { const l = document.querySelector('[data-testid="canvas-feature-panel"] [role=tablist]');
  return l ? { scrollLeft: l.scrollLeft, scrollWidth: l.scrollWidth, clientWidth: l.clientWidth } : null; });
out.点按序列 = [];
const btn = (out.无名按钮 || [])[0];
if (btn && btn.可命中) {
  for (let i = 0; i < 4; i++) {
    const before = await sl();
    await p.mouse.click(btn.可命中[0], btn.可命中[1]);
    await p.waitForTimeout(800);
    const after = await sl();
    // 按钮可能随滚动换位置，重新取一次可命中点
    const again = await p.evaluate(() => { const panel = document.querySelector('[data-testid="canvas-feature-panel"]');
      const tr = panel.querySelector('[role=tablist]').getBoundingClientRect();
      const e = Array.from(panel.querySelectorAll('button')).find((x) => { const r = x.getBoundingClientRect();
        return r.width > 1 && r.y >= tr.y - 2 && r.y + r.height <= tr.y + tr.height + 2 && !x.getAttribute('role'); });
      if (!e) return null; const r = e.getBoundingClientRect();
      for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
        const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return [x, y]; }
      return null; });
    out.点按序列.push({ 第几次: i + 1, 前: before, 后: after, 变了: after && before && after.scrollLeft !== before.scrollLeft });
    log(`  第 ${i + 1} 次点击：scrollLeft ${before && before.scrollLeft} → ${after && after.scrollLeft}  ${after && before && after.scrollLeft !== before.scrollLeft ? '✅ 有效' : '（到头/无效）'}`);
    if (again) btn.可命中 = again;
  }
}
save();
out.滚动后可命中 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid="canvas-feature-panel"] [role=tab]')).map((e) => {
  const r = e.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2)
    for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) { const h = document.elementFromPoint(x, y);
      if (h && h.closest('[role=tab]') === e) return { 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), 点: [x, y] }; }
  return { 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), 点: null }; }));
log('\n  此刻各页签可命中：');
out.滚动后可命中.forEach((t) => log(`    «${t.文字}» → ${JSON.stringify(t.点)}`));
await p.screenshot({ path: new URL('15-arrow-scrolled.png', shotDir).pathname, clip: { x: 750, y: 40, width: 350, height: 200 } });
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
log('\nDONE h');
process.exit(0);
