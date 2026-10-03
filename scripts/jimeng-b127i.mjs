// 批次 127 · i 轮：按**已验证的前置条件**重拍两张入库图。
//
// ⚠️ 为什么重拍：b 轮那张 02 号图是在点完「主体」之后立刻拍的，但画面上「全部 76」仍带下划线
//    —— 截图与它声称的状态**对不上**。这类图进了手册就是错的证据。
//    ⇒ 立规（本批）：**截图前必须把「这张图声称的状态」逐条回读断言一遍**，
//      对不上就不拍；拍完再回读一次状态，防止拍摄期间状态又变了。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'i' };
const save = () => writeFileSync(new URL('./_tmp-b127i.json', import.meta.url), JSON.stringify(out, null, 1));
const outDir = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);

const probe = () => p.evaluate(() => {
  const panel = document.querySelector('[data-testid="canvas-feature-panel"]');
  if (!panel) return { __err: 'no-panel' };
  const R = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const nav = panel.querySelector('[aria-label="Search result pages"]');
  return { 面板: R(panel), 选中页签: Array.from(panel.querySelectorAll('[role=tab]')).filter((x) => x.getAttribute('aria-selected') === 'true').map((x) => (x.innerText || '').replace(/\s+/g, ' ').trim()),
    结果行数: panel.querySelectorAll('[data-testid^="canvas-search-result-node_"]').length,
    分页: nav ? (nav.innerText || '').replace(/\s+/g, ' ').trim() : null,
    分页按钮: nav ? Array.from(nav.querySelectorAll('button')).map((e) => e.getAttribute('aria-label')) : null,
    输入值: (() => { const i = panel.querySelector('input'); return i ? i.value : null; })(),
    tablist: (() => { const l = panel.querySelector('[role=tablist]'); return l ? { scrollLeft: l.scrollLeft, scrollWidth: l.scrollWidth, clientWidth: l.clientWidth } : null; })(),
    右端圆钮: (() => { const tr = panel.querySelector('[role=tablist]').getBoundingClientRect();
      const e = Array.from(panel.querySelectorAll('button')).find((x) => { const r = x.getBoundingClientRect();
        return r.width > 1 && r.y >= tr.y - 2 && r.y + r.height <= tr.y + tr.height + 2 && !x.getAttribute('role'); });
      return e ? { rect: R(e), aria: e.getAttribute('aria-label') } : null; })() };
});

out.start = { 浮层: await overlays(), zoom: await zoom(), credits: await credits() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
for (let i = 0; i < 2; i++) { if (await overlays()) { await p.keyboard.press('Escape'); await p.waitForTimeout(1100); } }
const openPt = await p.evaluate(() => { const t = Array.from(document.querySelectorAll('[data-testid="canvas-panel-launcher"]')).find((e) => (e.getAttribute('aria-label') || '') === '搜索');
  if (!t) return null; const r = t.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
    const h = document.elementFromPoint(x, y); if (h && (h === t || t.contains(h))) return { x, y }; } return null; });
if (openPt) { await p.mouse.click(openPt.x, openPt.y); await p.waitForTimeout(2000); }

// 归位到「全部 76 / 无关键词 / 第 1 页」
const tAll = await p.evaluate(() => { const strip = (s) => (s || '').replace(/\s+/g, '').replace(/\d+$/, '');
  const t = Array.from(document.querySelectorAll('[data-testid="canvas-feature-panel"] [role=tab]')).find((e) => strip(e.innerText) === '全部');
  if (!t) return null; const r = t.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
    const h = document.elementFromPoint(x, y); if (h && h.closest('[role=tab]') === t) return { x, y }; } return null; });
if (tAll) { await p.mouse.click(tAll.x, tAll.y); await p.waitForTimeout(2000); }

out.拍109前 = await probe();
log('\n=== 拍 109 之前的断言 ===\n  ', JSON.stringify(out.拍109前));
const ok109 = out.拍109前.面板 && out.拍109前.面板.join() === '765,56,320,604'
  && out.拍109前.选中页签.join() === '全部 76' && out.拍109前.输入值 === '' && out.拍109前.分页 === '1 6' && out.拍109前.结果行数 === 10;
out.断言109 = { 通过: !!ok109, 期望: '面板 765,56,320,604 / 选中「全部 76」/ 输入框空 / 分页 innerText 逐字「1 6」（斜杠不是文本节点，是渲染出来的）/ 10 行' };
log('  断言：', ok109 ? '✅ 通过，可以拍' : '⛔ 不通过，不拍');
if (ok109) {
  await p.screenshot({ path: new URL('109-search-panel.png', outDir).pathname, clip: { x: 750, y: 40, width: 350, height: 640 } });
  out.拍109后 = await probe();
  out.拍109后与前相同 = JSON.stringify(out.拍109后) === JSON.stringify(out.拍109前);
  log('  拍完再断言：', out.拍109后与前相同 ? '✅ 状态未变' : '⛔ 状态变了');
}
save();

// 拍 110：页签行特写（含右端「Next search categories」圆钮）
out.拍110前 = await probe();
out.断言110 = { 通过: !!(out.拍110前.右端圆钮 && out.拍110前.右端圆钮.aria === 'Next search categories'
  && out.拍110前.tablist && out.拍110前.tablist.scrollWidth > out.拍110前.tablist.clientWidth) };
log('\n=== 拍 110 之前的断言 ===\n  ', JSON.stringify(out.拍110前), '\n  断言：', out.断言110.通过 ? '✅ 有溢出且右端圆钮存在' : '⛔ 不拍');
if (out.断言110.通过) {
  await p.screenshot({ path: new URL('110-search-tabs-overflow.png', outDir).pathname, clip: { x: 750, y: 100, width: 350, height: 60 } });
  out.拍110后 = await probe();
  out.拍110后与前相同 = JSON.stringify(out.拍110后) === JSON.stringify(out.拍110前);
  log('  拍完再断言：', out.拍110后与前相同 ? '✅ 状态未变' : '⛔ 状态变了');
}
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
log('\nDONE i');
process.exit(0);
