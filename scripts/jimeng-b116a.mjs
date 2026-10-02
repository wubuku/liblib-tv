// 批次 116 · a 轮：造**空视频节点**当宿主，读出「创作类型」下拉的**全部模式选项**。
//
// 靶子（`prepare-generation.md` 文末「未验证」清单里的一条）：
//   「未验证：『首尾帧』模式与『全能参考』的行为差异」
//
// 🔑 为什么这条现在可做：
//   · 批次 63 已经证实「**改设置不扣费**」（九个模型 × 价格矩阵整轮积分 805→805）
//     ⇒ 切模式**不属于**扣费边界，不需要额外授权
//   · b114pre 只读一轮已确认画布上**没有自建节点**（68 音频全空 / 1 空视频 / 1 有资源图片），
//     宿主必须自己造（护栏三道照旧）
//
// 这一轮**只读不切**：先把下拉里有哪些模式、逐字是什么、有几个，一次读全。
// 「面板在什么状态下」本身就是判据的一部分 —— 先记基线，再切。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b116a.json', import.meta.url), JSON.stringify(out, null, 1));

const allIds = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => e.getAttribute('data-id')));
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);

// 面板控件清单：**逐个按钮/输入面**读 aria + 尺寸 + 位置
// ⚠️ 不能用 `querySelector('[data-testid="node-toolbar"]')` 取第一个 ——
//    批次 85 已记：生成面板旁边还有一个**高度恒 0** 的同 testid 元素，
//    单数 `querySelector` 会命中它。⇒ 按「有实际尺寸」筛。
const readPanel = (lbl) => p.evaluate((l) => {
  const tbs = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
    .map((e) => ({ e, r: e.getBoundingClientRect() }))
    .filter((x) => x.r.width > 1 && x.r.height > 1);
  if (!tbs.length) return { at: Date.now(), lbl: l, __err: 'no-panel', nNodeToolbarTotal: document.querySelectorAll('[data-testid="node-toolbar"]').length };
  // 取面积最大的那个当主面板
  tbs.sort((a, b) => b.r.width * b.r.height - a.r.width * a.r.height);
  const tb = tbs[0].e, r = tbs[0].r;
  const rect = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  return {
    at: Date.now(), lbl: l, nNodeToolbarTotal: document.querySelectorAll('[data-testid="node-toolbar"]').length,
    panel: { rect: [r.x, r.y, r.width, r.height].map(Math.round), text: (tb.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 300) },
    btns: Array.from(tb.querySelectorAll('button,[role=button]')).map((e) => ({ aria: e.getAttribute('aria-label'),
      exp: e.getAttribute('aria-expanded'), tid: e.getAttribute('data-testid'), rect: rect(e) })).filter((x) => x.aria),
    inputs: Array.from(tb.querySelectorAll('input,textarea,[contenteditable],[data-testid="generation-prompt-editor"]')).map((e) => ({
      tag: e.tagName, tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'),
      ph: e.getAttribute('placeholder'), rect: rect(e) })),
    svgs: tb.querySelectorAll('svg').length,
    forms: Array.from(tb.querySelectorAll('form')).map((f) => ({ tid: f.getAttribute('data-testid'), aria: f.getAttribute('aria-label') })),
  };
}, lbl);

out.start = { nodes: await nodeN(), credits: await credits() };
log('起点：', JSON.stringify(out.start));
const reloc = await p.evaluate(() => {
  const bad = (x, y) => { const el = document.elementFromPoint(x, y);
    if (!el || el.closest('.react-flow__node')) return true;
    if (x < 200 || y < 60 || y > 630 || x > 1120) return true;
    if (el.closest('button,[role=button],input,a,[contenteditable]')) return true;
    if (el.closest('[role="menu"],[data-testid="node-toolbar"]')) return true; return false; };
  for (let y = 280; y < 630; y += 12) for (let x = 260; x < 1100; x += 12) if (!bad(x, y)) return { x, y }; return null; });
if (reloc) { await p.keyboard.press('Escape'); await p.waitForTimeout(400);
  await p.mouse.click(reloc.x, reloc.y); await p.waitForTimeout(1200); }
const g0 = await keyGuard(p);
log('焦点守卫：', g0.safe ? '✅' : '⛔', g0.where || '');
if (!g0.safe) { log('⛔ 中止'); await b.close(); process.exit(2); }

// ---- 造空视频节点 ----
log('\n=== 造空视频节点 ===');
const idsBefore = await allIds();
const blank = await p.evaluate(() => {
  const bad = (x, y) => { const el = document.elementFromPoint(x, y);
    if (!el || el.closest('.react-flow__node')) return true;
    if (x < 200 || y < 60 || y > 630 || x > 1120) return true;
    if (el.closest('button,[role=button],input,a')) return true; return false; };
  for (let y = 280; y < 630; y += 12) for (let x = 260; x < 1100; x += 12) if (!bad(x, y)) return [x, y]; return null; });
log('空白落点：', JSON.stringify(blank));
if (!blank) { log('🔴 中止'); await b.close(); process.exit(3); }
await p.mouse.move(blank[0], blank[1]); await p.waitForTimeout(400);
await p.mouse.down({ button: 'right' }); await p.waitForTimeout(300); await p.mouse.up({ button: 'right' });
await p.waitForTimeout(1300);
const nj = await p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]'))
  for (const it of m.querySelectorAll('[role=menuitem]')) {
    if ((it.innerText || '').trim().startsWith('新建节点')) { const r = it.getBoundingClientRect();
      return { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }; } } return null; });
await p.mouse.move(nj.x, nj.y); await p.waitForTimeout(500);
await p.mouse.move(nj.x + 3, nj.y); await p.waitForTimeout(1500);
const target = await p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]')) {
    if (getComputedStyle(m).visibility === 'hidden') continue;
    for (const it of m.querySelectorAll('[role=menuitem]')) { if ((it.innerText || '').trim() !== '视频') continue;
      const r = it.getBoundingClientRect(); if (r.width < 1) continue;
      const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
      const h = document.elementFromPoint(cx, cy); if (!h || !(h === it || it.contains(h))) continue;
      return { rect: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)] }; } }
  return { __err: 'no-clickable' }; });
log('「视频」落点：', JSON.stringify(target));
if (target.__err) { log('⛔ 中止'); await b.close(); process.exit(3); }
await p.mouse.click(target.rect[0] + target.rect[2] / 2, target.rect[1] + target.rect[3] / 2);

let SELF = null, guard = null;
for (let k = 1; k <= 16; k++) {
  await p.waitForTimeout(1200);
  const ids = await allIds();
  const diff = ids.filter((id) => !idsBefore.includes(id));
  if (diff.length === 1) { const sel = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node.selected')).map((e) => e.getAttribute('data-id')));
    guard = { diff, sel, ok: sel.includes(diff[0]) }; if (guard.ok) { SELF = diff[0]; break; } }
  else if (diff.length > 1) { log(`  ⛔ 差集超过一个：${JSON.stringify(diff)}`); break; }
}
out.guard = guard; out.self = SELF;
log(`护栏②：${JSON.stringify(guard)} ⇒ ${SELF ? '✅ ' + SELF : '🔴'}`);
save();
if (!SELF) { log('🔴 中止'); await b.close(); process.exit(3); }

// ---- 读基线面板 ----
await p.waitForTimeout(1500);
out.baseline = await readPanel('baseline');
log('\n=== 基线面板 ===');
log('同 testid 元素总数：', out.baseline.nNodeToolbarTotal, '｜主面板：', JSON.stringify(out.baseline.panel));
log('控件：'); (out.baseline.btns || []).forEach((x) => log('   ' + JSON.stringify(x)));
log('输入面：', JSON.stringify(out.baseline.inputs));
log('svg 数：', out.baseline.svgs, '｜form：', JSON.stringify(out.baseline.forms));
save();

// ---- 展开「创作类型」下拉，读全部选项（**只读，不点任何选项**）----
log('\n=== 展开「创作类型」下拉（只读）===');
const cta = await p.evaluate(() => { for (const e of document.querySelectorAll('button,[role=button]')) {
  const a = e.getAttribute('aria-label') || ''; if (!/^创作类型/.test(a)) continue;
  const r = e.getBoundingClientRect(); if (r.width < 1) continue;
  const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
  const h = document.elementFromPoint(cx, cy); if (!h || !(h === e || e.contains(h))) continue;
  return { aria: a, x: cx, y: cy, rect: [r.x, r.y, r.width, r.height].map(Math.round), exp: e.getAttribute('aria-expanded') }; }
  return null; });
out.cta = cta;
log('「创作类型」按钮：', JSON.stringify(cta));
if (cta) {
  await p.mouse.click(cta.x, cta.y); await p.waitForTimeout(1400);
  out.ctaOpen = await readPanel('cta-open');
  out.listbox = await p.evaluate(() => { const c = []; for (const el of document.querySelectorAll('[role="listbox"]')) {
    const r = el.getBoundingClientRect(); if (r.width < 1) continue;
    c.push({ aria: el.getAttribute('aria-label'), rect: [r.x, r.y, r.width, r.height].map(Math.round),
      inTb: !!el.closest('[data-testid="node-toolbar"]'),
      options: Array.from(el.querySelectorAll('[role="option"]')).map((o) => { const q = o.getBoundingClientRect();
        return { t: (o.innerText || '').replace(/\s+/g, ' ').trim(), sel: o.getAttribute('aria-selected'),
          rect: [q.x, q.y, q.width, q.height].map(Math.round), svgs: o.querySelectorAll('svg').length }; }) }); }
    return c; });
  log('listbox：'); log(JSON.stringify(out.listbox, null, 1));
  await p.keyboard.press('Escape'); await p.waitForTimeout(800);
  out.afterEsc = await p.evaluate(() => { for (const e of document.querySelectorAll('[aria-label^="创作类型"]')) return e.getAttribute('aria-expanded'); return null; });
  log('Esc 后 expanded =', out.afterEsc);
}
out.end = { nodes: await nodeN(), credits: await credits() };
log('\n终点：', JSON.stringify(out.end), '（积分应仍为 805 —— 只读不改设置）');
save();
log('\nDONE a');
process.exit(0);
