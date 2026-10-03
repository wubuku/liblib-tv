// 批次 127 · b 轮：搜索面板的四个未知点。
//
// 🔑 a 轮已把「搜索」面板整个挖开，得到一批全新读数：
//   · 它与「生成历史」**是同一个组件**（`ASIDE[role=dialog][canvas-feature-panel]` ＋
//     同样的 surface/content 两层包装 ＋ 同一个父级），只有内层 `SECTION` 的 testid 不同：
//     `canvas-search-panel` vs `generation-history-panel`。
//   · 🔴 **手册记的 `320×211` 是错的**：本轮实测 **`320×604@765,56`**
//     （x 也不同：765 vs 797）。旧读数测于 2026-10-01、当时结果只有 1 行 ⇒ 高度随结果行数变。
//   · 九个 `role=tab"` 的**宽度各不相同**（62/51/51/62/53/42/66/29/51，合计 **467 > 320**）
//     ⇒ **一行放不下**；面板里有 `canvas-search-tab-mask-next 32×36@1053,112`（右侧渐隐遮罩）
//     与 `canvas-search-tab-gradient` / `canvas-search-tab-solid-mask`。
//   · 结果行是 `BUTTON 304×64`，**testid 里带节点 id**：`canvas-search-result-node_<id>`，
//     行内还有一个 `canvas-search-locate-icon-node_<id>`。aria 逐字 `音频 68, 音频`。
//   · 每行里有一个 `role="status"`；另有一个独立的 `role="status"`。
//   · 底部分页器 `NAV[aria="Search result pages"] 320×52@765,608`，逐字 `1 / 6`。
//   · aria 里出现**未插值的国际化占位串**：`{num, plural, other {向前 {num} 页}}`。
//
// 本轮问四件事：① 那些 `role="status"` 是什么、屏上看得见吗；
//             ② 零计数的页签（主体 / 组）点开是什么逐字；
//             ③ 九个页签放不下时，最后几个怎么点得到；
//             ④ 分页器点「下一页」会不会换一批结果（只读，不点结果行）。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b' };
const save = () => writeFileSync(new URL('./_tmp-b127b.json', import.meta.url), JSON.stringify(out, null, 1));
const shotDir = new URL('./_tmp-b127a-shots/', import.meta.url);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);

out.start = { zoom: await zoom(), credits: await credits(), status: await status(), 浮层: await overlays() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);

const panelState = () => p.evaluate(() => {
  const panel = document.querySelector('[data-testid="canvas-feature-panel"]');
  if (!panel) return { __err: 'no-panel' };
  const R = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const vp = panel.querySelector('[data-testid="canvas-search-results-viewport"]');
  return { 面板: R(panel), 逐字: (panel.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200),
    tab: Array.from(panel.querySelectorAll('[role=tab]')).map((e) => ({ 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), sel: e.getAttribute('aria-selected'), rect: R(e) })),
    结果行: Array.from(panel.querySelectorAll('[data-testid^="canvas-search-result-node_"]')).map((e) => ({ tid: e.getAttribute('data-testid'), rect: R(e), 文字: (e.innerText || '').replace(/\s+/g, ' ').trim() })),
    分页: (() => { const n = panel.querySelector('[aria-label="Search result pages"]'); return n ? { 逐字: (n.innerText || '').replace(/\s+/g, ' ').trim(), rect: R(n), 按钮: Array.from(n.querySelectorAll('button')).map((e) => ({ rect: R(e), aria: e.getAttribute('aria-label'), 禁用: e.hasAttribute('disabled') || e.getAttribute('aria-disabled') === 'true' })) } : null; })(),
    视口: vp ? { rect: R(vp), scrollTop: vp.scrollTop, scrollHeight: vp.scrollHeight, clientHeight: vp.clientHeight } : null,
    tabs容器: (() => { const t = panel.querySelector('[data-testid="canvas-search-tabs"]'); return t ? { rect: R(t), scrollLeft: t.scrollLeft, scrollWidth: t.scrollWidth, clientWidth: t.clientWidth } : null; })() };
});

// ---- ① `role="status"` 是什么 ----
out.status元素 = await p.evaluate(() => {
  const panel = document.querySelector('[data-testid="canvas-feature-panel"]');
  if (!panel) return { __err: 'no-panel' };
  const list = Array.from(panel.querySelectorAll('[role=status]'));
  return { 数量: list.length, 明细: list.slice(0, 12).map((e) => { const r = e.getBoundingClientRect(); const st = getComputedStyle(e);
    return { tag: e.tagName, tid: e.getAttribute('data-testid'), 逐字: (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60),
      矩形: [r.x, r.y, r.width, r.height].map(Math.round), 有面积: r.width >= 1 && r.height >= 1,
      ariaLive: e.getAttribute('aria-live'), role: e.getAttribute('role'),
      屏外: st.position === 'absolute' && (st.clip || '').includes('rect'), position: st.position, clip: st.clip,
      父: e.parentElement.tagName + (e.parentElement.getAttribute('data-testid') ? '[' + e.parentElement.getAttribute('data-testid') + ']' : ''),
      兄弟逐字: (e.parentElement.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 50) }; }) };
});
log('\n=== ① 面板里的 role=status（', out.status元素.数量, '个）===');
(out.status元素.明细 || []).forEach((e, i) => log(`  [${i}] <${e.tag}> ${JSON.stringify(e.矩形)} 有面积=${e.有面积} aria-live=${e.ariaLive} 屏外=${e.屏外} 父=${e.父} «${e.逐字}»`));
log('  ---- 第 0 个的上下文 ----');
out.status元素.上下文 = await p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-feature-panel"] [role=status]');
  if (!e) return null;
  const R = (x) => { const q = x.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const chain = []; let n = e;
  for (let i = 0; i < 5 && n && n !== document.body; i++) { chain.push({ tag: n.tagName, tid: n.getAttribute('data-testid'), role: n.getAttribute('role'), rect: R(n), 逐字: (n.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40) }); n = n.parentElement; }
  return { 自身: { tag: e.tagName, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(), 矩形: R(e), 完整outerHTML: e.outerHTML.slice(0, 300) }, 祖先链: chain,
    面板内所有status逐字: Array.from(document.querySelectorAll('[data-testid="canvas-feature-panel"] [role=status]')).map((x) => (x.innerText || x.textContent || '').replace(/\s+/g, ' ').trim()) };
});
log('  自身：', JSON.stringify(out.status元素.上下文?.自身, null, 1));
log('  祖先链：', JSON.stringify(out.status元素.上下文?.祖先链, null, 1));
log('  全部 status 逐字：', JSON.stringify(out.status元素.上下文?.面板内所有status逐字));
save();

// ---- ② 零计数页签「主体」点开是什么逐字 ----
out.零计数页签 = [];
for (const name of ['主体', '组']) {
  const hit = await p.evaluate((nm) => {
    const tabs = Array.from(document.querySelectorAll('[data-testid="canvas-feature-panel"] [role=tab]'));
    const t = tabs.find((e) => (e.innerText || '').replace(/\s+/g, '').trim() === nm);
    if (!t) return { __err: 'no-tab:' + nm };
    const r = t.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2)
      for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) { const h = document.elementFromPoint(x, y);
        const c = h && h.closest('[role=tab]'); if (c === t) return { x, y, 矩形: [r.x, r.y, r.width, r.height].map(Math.round) }; }
    return { __err: 'not-visible:' + nm, 矩形: [r.x, r.y, r.width, r.height].map(Math.round) };
  }, name);
  log(`\n=== ② 零计数页签「${name}」落点：`, JSON.stringify(hit));
  if (hit.__err) { out.零计数页签.push({ 名: name, 落点: hit }); continue; }
  await p.mouse.click(hit.x, hit.y); await p.waitForTimeout(1100);
  const st = await panelState();
  out.零计数页签.push({ 名: name, 落点: hit, 状态: st });
  log('  面板：', JSON.stringify(st.面板), '｜结果行数：', st.结果行.length, '｜分页：', JSON.stringify(st.分页?.逐字));
  log('  逐字：', JSON.stringify(st.逐字));
  if (name === '主体') await p.screenshot({ path: new URL('02-tab-subject-empty.png', shotDir).pathname, clip: { x: 750, y: 40, width: 350, height: 260 } });
}
save();

// ---- ③ 九个页签放不下：tablist 的滚动/溢出状态 + 点最后一个页签「其他 1」 ----
out.溢出 = await p.evaluate(() => {
  const panel = document.querySelector('[data-testid="canvas-feature-panel"]');
  const tabs = Array.from(panel.querySelectorAll('[role=tab]'));
  const R = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const list = panel.querySelector('[role=tablist]');
  const holder = panel.querySelector('[data-testid="canvas-search-tabs"]');
  return { 面板右边界: R(panel)[0] + R(panel)[2], 视口右边界: window.innerWidth,
    tablist: { rect: R(list), scrollWidth: list.scrollWidth, clientWidth: list.clientWidth, scrollLeft: list.scrollLeft, overflowX: getComputedStyle(list).overflowX },
    容器: holder ? { tid: 'canvas-search-tabs', rect: R(holder), scrollWidth: holder.scrollWidth, clientWidth: holder.clientWidth, scrollLeft: holder.scrollLeft, overflowX: getComputedStyle(holder).overflowX } : null,
    渐隐遮罩: (() => { const m = panel.querySelector('[data-testid="canvas-search-tab-mask-next"]'); if (!m) return null;
      const st = getComputedStyle(m); return { rect: R(m), 逐字: (m.innerText || '').trim(), aria: m.getAttribute('aria-label'), background: st.background.slice(0, 90) }; })(),
    渐变: (() => { const g = panel.querySelector('[data-testid="canvas-search-tab-gradient"]'); return g ? { rect: R(g) } : null; })(),
    实底遮罩: (() => { const g = panel.querySelector('[data-testid="canvas-search-tab-solid-mask"]'); return g ? { rect: R(g) } : null; })(),
    各页签: tabs.map((e, i) => ({ i, 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), rect: R(e),
      超出面板右边界: R(e)[0] + R(e)[2] > R(panel)[0] + R(panel)[2],
      命中自身点: (() => { const r = e.getBoundingClientRect(); for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2)
        for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) { const h = document.elementFromPoint(x, y);
          if (h && h.closest('[role=tab]') === e) return [x, y]; } return null; })() })) };
});
log('\n=== ③ 九个页签的溢出情况 ===');
log('  面板：', JSON.stringify(out.溢出.tablist), '\n  容器：', JSON.stringify(out.溢出.容器));
log('  渐隐遮罩：', JSON.stringify(out.溢出.渐隐遮罩));
log('  各页签：');
out.溢出.各页签.forEach((t) => log(`    [${t.i}] «${t.文字}» ${JSON.stringify(t.rect)} 超出面板=${t.超出面板右边界} 可命中点=${JSON.stringify(t.命中自身点)}`));
save();

// 点最后一个页签「其他 1」（导演台节点）—— 只切页签，不点结果行
const last = out.溢出.各页签[out.溢出.各页签.length - 1];
if (last && last.命中自身点) {
  await p.mouse.click(last.命中自身点[0], last.命中自身点[1]);
  await p.waitForTimeout(1200);
  out.最后页签 = await panelState();
  log('\n  点最后一个页签「', last.文字, '」之后：');
  log('    面板：', JSON.stringify(out.最后页签.面板), '｜结果行数：', out.最后页签.结果行.length);
  log('    结果行：', JSON.stringify(out.最后页签.结果行));
  log('    分页：', JSON.stringify(out.最后页签.分页?.逐字));
  await p.screenshot({ path: new URL('03-tab-other.png', shotDir).pathname, clip: { x: 750, y: 40, width: 350, height: 640 } });
}
save();

// ---- ④ 分页：点「前往下一页」（只翻页，不点任何结果行） ----
const pg0 = await panelState();
out.分页前 = { 逐字: pg0.分页?.逐字, 按钮: pg0.分页?.按钮, 结果行: pg0.结果行 };
log('\n=== ④ 分页 ===\n  翻页前：', JSON.stringify(out.分页前.逐字), JSON.stringify(out.分页前.按钮));
// 回到「全部」页签，制造一个多页场景
const allHit = await p.evaluate(() => {
  const t = Array.from(document.querySelectorAll('[data-testid="canvas-feature-panel"] [role=tab]')).find((e) => (e.innerText || '').replace(/\s+/g, '').startsWith('全部'));
  if (!t) return null; const r = t.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
    const h = document.elementFromPoint(x, y); if (h && h.closest('[role=tab]') === t) return { x, y }; }
  return null;
});
if (allHit) { await p.mouse.click(allHit.x, allHit.y); await p.waitForTimeout(1200); log('  已切回「全部」页签'); }
const pgAll = await panelState();
out.全部页签 = { 分页: pgAll.分页?.逐字, 视口: pgAll.视口, 结果行数: pgAll.结果行.length };
log('  「全部」下：', JSON.stringify(out.全部页签));
const next = await p.evaluate(() => {
  const n = document.querySelector('[data-testid="canvas-feature-panel"] [aria-label="Search result pages"]');
  if (!n) return null;
  const btn = Array.from(n.querySelectorAll('button')).find((e) => /下一页/.test(e.getAttribute('aria-label') || ''));
  if (!btn) return { __err: 'no-next-btn' };
  const r = btn.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
    const h = document.elementFromPoint(x, y); if (h && (h === btn || btn.contains(h))) return { x, y, aria: btn.getAttribute('aria-label') }; }
  return { __err: 'no-point' };
});
log('  「下一页」落点：', JSON.stringify(next));
if (next && !next.__err) {
  await p.mouse.click(next.x, next.y); await p.waitForTimeout(1300);
  const pg1 = await panelState();
  out.分页后 = { 逐字: pg1.分页?.逐字, 结果行: pg1.结果行, 视口: pg1.视口 };
  log('  翻页后：', JSON.stringify(out.分页后.逐字));
  log('  结果行（前 3）：', JSON.stringify(out.分页后.结果行.slice(0, 3)));
  log('  视口 scrollTop：', JSON.stringify(out.分页后.视口));
  await p.screenshot({ path: new URL('04-page2.png', shotDir).pathname, clip: { x: 750, y: 40, width: 350, height: 640 } });
  // 选中新旧结果行做对照
  const 对照 = (await panelState()).结果行.map((r) => r.tid);
  out.翻页换了一批 = JSON.stringify(对照) !== JSON.stringify(out.全部页签.结果行.slice(0, 对照.length).map((r) => r.tid));
  log('  翻页是否换了一批结果：', out.翻页换了一批);
}
save();

out.收尾 = { 浮层: await overlays(), 选中: await sel(), zoom: await zoom(), credits: await credits(), status: await status() };
log('\n收尾（面板仍开着）：', JSON.stringify(out.收尾));
save();
log('\nDONE b');
process.exit(0);
