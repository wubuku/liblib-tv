// 批次 120 · b 轮：a 轮撞出**大发现** —— 状态行那句文本的唯一宿主是
//   `<SPAN id=":modern-js-r1:">`，rect **`[-1,-1,1,1]`**、`position:absolute`，
//   即**屏外 1×1 的读屏 live region**，不是一条可见的状态行。
//   而全文档 171 种 testid 里**没有任何一个是底部状态行**
//   （底部只有 dock 4 项 + 侧边 launcher + 小地图 portal）。
//
// 本轮要钉死的三件事：
//   ① 屏上**到底有没有**一条可见状态行？（截图 + 逐元素枚举底部条带，两条不共享假设的旁证）
//   ② `:modern-js-r1:` 是什么？它和另外两个 1×1 屏外元素
//      （`canvas-creation-entry-feedback` / `canvas-context-menu-terminal-feedback`）
//      是不是同一族「读屏播报区」？各自播报什么？
//   ③ 手册里「状态行」这个说法到底指什么 —— 需要把 `已保存`（顶栏 `canvas-title-save-status`）
//      和「提示条」这两个**可见**东西和这条 live region 摆在一起看。
//
// ⛔ 纯只读：只截图 + 读属性，不点、不建节点、不改状态。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b' };
const save = () => writeFileSync(new URL('./_tmp-b120b.json', import.meta.url), JSON.stringify(out, null, 1));

const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });

out.start = { zoom: await zoom(), credits: await credits() };
log('起点：', JSON.stringify(out.start));

// ============================================================
// ① 截图：整屏 + 底部条带（两条独立旁证里的第一条）
// ============================================================
const dir = new URL('./_tmp-b120b-shots/', import.meta.url);
await p.screenshot({ path: new URL('full.png', dir).pathname });
await p.screenshot({ path: new URL('bottom-strip.png', dir).pathname, clip: { x: 0, y: 660, width: 1280, height: 60 } });
log('截图已存 _tmp-b120b-shots/{full,bottom-strip}.png');

// ============================================================
// ② 底部条带逐元素枚举（y ≥ 655 的、**可见**的）
// ============================================================
out.bottom = await p.evaluate(() => {
  const seen = [];
  for (const e of document.querySelectorAll('body *')) {
    const q = e.getBoundingClientRect();
    if (q.height === 0 || q.width === 0) continue;
    if (q.bottom < 655) continue;               // 完全在条带之上
    if (q.top > 719.5) continue;                  // 完全在视口之下
    const cs = getComputedStyle(e);
    const vis = cs.visibility !== 'hidden' && cs.display !== 'none' && parseFloat(cs.opacity) > 0.01;
    const 屏外1x1 = (q.width <= 2 && q.height <= 2) || (q.x < 0 && q.y < 0);
    seen.push({ tag: e.tagName, tid: e.getAttribute('data-testid'), id: e.id || null,
      cls: (e.getAttribute('class') || '').toString().slice(0, 56),
      rect: [q.x, q.y, q.width, q.height].map(Math.round),
      可见: vis, 屏外1x1,
      文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 40),
      aria: e.getAttribute('aria-label') });
  }
  // 过滤掉纯粹因为祖先链被拉高而整片覆盖的（自身无文字无 testid 且子元素多）
  return { 总数: seen.length, 明细: seen.filter((x) => x.tid || x.文字 || x.aria || x.屏外1x1) };
});
log('\n=== ② 底部条带（y≥655）可见元素：' + out.bottom.总数 + ' 个，其中带身份/文字/屏外标记的 ' + out.bottom.明细.length + ' 个 ===');
out.bottom.明细.forEach((d) => log(`   ${d.屏外1x1 ? '「屏外1×1」' : '  可见    '} <${d.tag}> tid=${JSON.stringify(d.tid)} id=${JSON.stringify(d.id)} ${JSON.stringify(d.rect)}\n        cls=${JSON.stringify(d.cls)}\n        文字=${JSON.stringify(d.文字)} aria=${JSON.stringify(d.aria)}`));
save();

// ============================================================
// ③ 读屏播报区：`:modern-js-r1:` 及同族
// ============================================================
out.live = await p.evaluate(() => {
  const r = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const desc = (e) => { const cs = getComputedStyle(e);
    return { tag: e.tagName, id: e.id || null, tid: e.getAttribute('data-testid'),
      cls: (e.getAttribute('class') || '').toString().slice(0, 56), rect: r(e), pos: cs.position, clip: cs.clip,
      role: e.getAttribute('role'), 'aria-live': e.getAttribute('aria-live'),
      'aria-atomic': e.getAttribute('aria-atomic'), 'aria-relevant': e.getAttribute('aria-relevant'),
      'aria-label': e.getAttribute('aria-label'),
      文字: (e.textContent || '').replace(/\s+/g, ' ').trim() }; };
  const r1 = document.getElementById(':modern-js-r1:');
  const chain = []; let cur = r1;
  for (let k = 0; k < 6 && cur; k++) { chain.push(desc(cur)); cur = cur.parentElement; }
  // 全文档所有 id 以 modern-js 开头的播报区 + 所有 1x1 屏外 testid
  const allModern = Array.from(document.querySelectorAll('[id^=":modern-js"]')).map(desc);
  const tiny = Array.from(document.querySelectorAll('[data-testid]')).filter((e) => {
    const q = e.getBoundingClientRect(); return (q.width <= 2 && q.height <= 2) || (q.x <= 0 && q.y <= 0 && q.width <= 2);
  }).map(desc);
  return { r1存在: !!r1, r1链: chain, 全部modern区: allModern, 全部1x1屏外testid: tiny };
});
log('\n=== ③ 读屏播报区 ===');
log('  :modern-js-r1: 存在？', out.live.r1存在);
out.live.r1链.forEach((d, k) => log(`  ${'  '.repeat(k)}${k === 0 ? '★ ' : ''}<${d.tag}> id=${JSON.stringify(d.id)} tid=${JSON.stringify(d.tid)} ${JSON.stringify(d.rect)} pos=${d.pos} clip=${JSON.stringify(d.clip)}\n  ${'  '.repeat(k)}role=${JSON.stringify(d.role)} aria-live=${JSON.stringify(d['aria-live'])} atomic=${JSON.stringify(d['aria-atomic'])} relevant=${JSON.stringify(d['aria-relevant'])}\n  ${'  '.repeat(k)}文字=${JSON.stringify(d.文字.slice(0, 90))}`));
log('\n  全文档 id^=":modern-js" 元素：' + out.live.全部modern区.length + ' 个');
out.live.全部modern区.forEach((d) => log(`     ${JSON.stringify(d.id)} ${JSON.stringify(d.rect)} live=${JSON.stringify(d['aria-live'])} 文字=${JSON.stringify(d.文字.slice(0, 70))}`));
log('\n  全文档 1×1 屏外 testid：' + out.live.全部1x1屏外testid.length + ' 个');
out.live.全部1x1屏外testid.forEach((d) => log(`     ${d.tid} ${JSON.stringify(d.rect)} 文字=${JSON.stringify(d.文字.slice(0, 70))}`));
save();

// ============================================================
// ④ 手册里当「状态行」用的另外两个**可见**东西：顶栏保存状态 + 提示条
// ============================================================
out.visible = await p.evaluate(() => {
  const r = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const g = (sel) => { const e = document.querySelector(sel); return e ? { sel, rect: r(e), 文字: (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim(), 可见: r(e)[2] > 0 && r(e)[3] > 0 } : { sel, __none: true }; };
  // 全文搜「当前视窗没有内容」「回到节点」这两个提示条串，看它们挂在哪
  const hints = [];
  for (const e of document.querySelectorAll('body *')) {
    const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
    if (!t || t.length > 40) continue;
    if (/当前视窗没有内容|回到节点|已保存|撤销|重做/.test(t)) {
      const q = e.getBoundingClientRect();
      if (q.width === 0 || q.height === 0) continue;
      if (e.children.length) continue; // 只记叶子
      hints.push({ tag: e.tagName, tid: e.getAttribute('data-testid'), cls: (e.getAttribute('class') || '').toString().slice(0, 50), rect: r(e), 文字: t });
    }
  }
  return { 顶栏保存状态: g('[data-testid="canvas-title-save-status"]'), 顶栏节点计数: g('[data-testid="canvas-node-summary-trigger"]'), 提示条叶子: hints };
});
log('\n=== ④ 可见的「状态类」元素 ===');
log('  顶栏 canvas-title-save-status：', JSON.stringify(out.visible.顶栏保存状态));
log('  顶栏 canvas-node-summary-trigger：', JSON.stringify(out.visible.顶栏节点计数));
log('  提示条类叶子元素（' + out.visible.提示条叶子.length + ' 个）：');
out.visible.提示条叶子.forEach((d) => log(`     <${d.tag}> tid=${JSON.stringify(d.tid)} ${JSON.stringify(d.rect)} 文字=${JSON.stringify(d.文字)}\n        cls=${JSON.stringify(d.cls)}`));
save();

out.end = { zoom: await zoom(), credits: await credits() };
log('\n终点：', JSON.stringify(out.end));
save();
log('\nDONE b');
process.exit(0);
