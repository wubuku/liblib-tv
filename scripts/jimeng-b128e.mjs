// 批次 128 · e 轮：快捷键抽屉的完整身份（它比视口高 572px 这一点值得写进手册）＋ 本批收尾。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'e' };
const save = () => writeFileSync(new URL('./_tmp-b128e.json', import.meta.url), JSON.stringify(out, null, 1));
const shotDir = new URL('./_tmp-b128a-shots/', import.meta.url);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);

out.起点 = { 状态行: await status(), 选中: await sel(), zoom: await zoom(), credits: await credits(), 浮层: await overlays() };
log('起点：', JSON.stringify(out.起点));
await keyGuard(p);
for (let i = 0; i < 3; i++) { if (!(await overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(1000); }

const clickAt = async (s, re) => {
  const pt = await p.evaluate(({ s: sel2, re: r }) => {
    const list = Array.from(document.querySelectorAll(sel2));
    const e = r ? list.find((x) => new RegExp(r).test((x.innerText || '').replace(/\s+/g, ''))) : list[0];
    if (!e) return { __err: 'not-found' };
    const q = e.getBoundingClientRect(); if (q.width < 1) return { __err: 'zero-size' };
    for (let y = Math.ceil(q.y) + 2; y <= q.y + q.height - 2; y += 2) for (let x = Math.ceil(q.x) + 2; x <= q.x + q.width - 2; x += 2) {
      const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; }
    return { __err: 'no-point' };
  }, { s, re });
  if (pt.__err) return pt;
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1900);
  return pt;
};

log('\n=== 快捷键抽屉身份 ===');
out.开菜单 = await clickAt('[data-testid="canvas-user-menu-trigger"]');
out.点快捷键 = await clickAt('[data-testid="canvas-user-menu"] [role=menuitem]', '^快捷键');
log('  菜单 / 快捷键落点：', JSON.stringify(out.开菜单), JSON.stringify(out.点快捷键));

out.抽屉解剖 = await p.evaluate(() => {
  const sc = document.querySelector('[data-testid="shortcut-help-scroll-content"]');
  if (!sc) return { __err: 'no-scroll-content' };
  const R = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const chain = []; let n = sc;
  for (let i = 0; i < 6 && n && n !== document.body; i++) { const st = getComputedStyle(n);
    chain.push({ d: i, tag: n.tagName, tid: n.getAttribute('data-testid'), role: n.getAttribute('role'),
      aria: n.getAttribute('aria-label'), rect: R(n), scrollHeight: n.scrollHeight, clientHeight: n.clientHeight,
      scrollTop: n.scrollTop, overflowY: st.overflowY, position: st.position, zIndex: st.zIndex,
      pointerEvents: st.pointerEvents, 可滚: n.scrollHeight > n.clientHeight + 1,
      文本长度: (n.innerText || '').replace(/\s+/g, '').length }); n = n.parentElement; }
  return { 滚动内容: { rect: R(sc), scrollHeight: sc.scrollHeight, clientHeight: sc.clientHeight,
      逐字前160: (sc.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160),
      组标题: Array.from(sc.querySelectorAll('h1,h2,h3,h4,[class*=group],[data-testid]')).slice(0, 12).map((e) => ({ tag: e.tagName, tid: e.getAttribute('data-testid'), 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30), rect: R(e) })) },
    祖先链: chain };
});
if (out.抽屉解剖.__err) { log('  ', out.抽屉解剖.__err); }
else {
  log('  滚动内容：', JSON.stringify({ rect: out.抽屉解剖.滚动内容.rect, scrollHeight: out.抽屉解剖.滚动内容.scrollHeight, clientHeight: out.抽屉解剖.滚动内容.clientHeight }));
  log('  逐字前160：', JSON.stringify(out.抽屉解剖.滚动内容.逐字前160));
  log('  祖先链：');
  out.抽屉解剖.祖先链.forEach((c) => log(`    ${'  '.repeat(c.d)}<${c.tag}> tid=${c.tid ?? '-'} role=${c.role ?? '-'} ${JSON.stringify(c.rect)} scrollH=${c.scrollHeight} clientH=${c.clientHeight} overflowY=${c.overflowY} 可滚=${c.可滚} 文本${c.文本长度}`));
  log('  组标题：', JSON.stringify(out.抽屉解剖.滚动内容.组标题.slice(0, 8)));
  await p.screenshot({ path: new URL('20-shortcuts-drawer.png', shotDir).pathname });
}
save();

// 抽屉开着时是否还能滚（内容 1292 > 视口 720）
out.抽屉滚动 = await p.evaluate(() => {
  const sc = document.querySelector('[data-testid="shortcut-help-scroll-content"]');
  const r = sc.getBoundingClientRect();
  return { 内容底边: Math.round(r.y + r.height), 视口高: window.innerHeight, 超出视口: r.y + r.height > window.innerHeight,
    scrollTop: sc.scrollTop, scrollHeight: sc.scrollHeight, clientHeight: sc.clientHeight };
});
log('\n  抽屉 vs 视口：', JSON.stringify(out.抽屉滚动));
for (let i = 0; i < 3; i++) { if (!(await overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(1100); }
out.关闭后 = { 浮层: await overlays(), 抽屉在: await p.evaluate(() => !!document.querySelector('[data-testid="shortcut-help-scroll-content"]')) };
log('  关闭后：', JSON.stringify(out.关闭后));
save();

// ---- 本批收尾 ----
out.收尾 = { 浮层: await overlays(), 夹具残留: await p.evaluate(() => document.querySelectorAll('[data-b128-fixture]').length),
  选中: await sel(), zoom1: await zoom(), credits: await credits(), status: await status() };
await p.waitForTimeout(1500);
out.收尾.zoom2 = await zoom();
const base = '/tmp/b120-baseline-ids.txt';
if (existsSync(base)) {
  const bset = new Set(readFileSync(base, 'utf8').split('\n').map((s) => s.trim()).filter(Boolean));
  const now = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
  out.节点 = { 基线数: bset.size, 现在数: now.length, 多出: now.filter((x) => !bset.has(x)), 少掉: [...bset].filter((x) => !now.includes(x)) };
  log('\n  节点：', JSON.stringify(out.节点));
}
log('\n收尾：', JSON.stringify(out.收尾));
save();
log('\nDONE e');
process.exit(0);
