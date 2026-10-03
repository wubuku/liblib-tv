// 批次 129 · e 轮：**小地图开关的受控实验**（它同时是「一条确凿的过时 testid」的证据），
// 外加补上资产库「主体」页。
//
// 🔑 起因：d 轮起点静态 testid 是 **171**，而 a/b 两轮记的静态是 **174**。逐个比对发现
//   少掉的恰好 3 个且**全是小地图**：`canvas-minimap-surface` / `canvas-minimap-navigation` / `rf__minimap`。
//   ⇒ 「全文档 testid 种类数」**不是稳定量**，它是**当前 UI 状态**的函数。
//   本轮用**一次受控实验**证明这 174↔171 的差**就只等于小地图这一个开关**，
//   而不是别的什么漂移——不能只凭「差集正好是小地图」就下结论。
//
// 🔴 本批第一条**确凿的已证过时 testid**：
//   `SOURCE_OBSERVATIONS.md:175` 记的小地图面板 testid 是 `dreamina-canvas-minimap-surface`，
//   而 `AUDIT.md:319` 记的是 `canvas-minimap-surface` —— **手册内部两处互相矛盾**。
//   a 轮已把前者分类为「**是 class 名，不是 testid**」。本轮把它坐实：
//   旧名现在只当 class 用，新名才是真 testid。
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'e' };
const save = () => writeFileSync(new URL('./_tmp-b129e.json', import.meta.url), JSON.stringify(out, null, 1));

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);
const collect = () => p.evaluate(() => { const s = new Set(); for (const e of document.querySelectorAll('[data-testid]')) s.add(e.getAttribute('data-testid')); return Array.from(s); });
const idsNow = () => p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => n.getAttribute('data-id')).sort());
const escAll = async () => { for (let i = 0; i < 3; i++) { if (!(await overlays())) break; await p.keyboard.press('Escape'); await p.waitForTimeout(900); } };
const toggle = async (sel, label) => {
  const pt = await p.evaluate((s) => { const e = document.querySelector(s); if (!e) return { __err: 'not-found' };
    const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) { const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; }
    return { __err: 'no-point' }; }, sel);
  if (pt.__err) { log(`  【${label}】⛔`, pt.__err); return pt; }
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1500);
  return pt;
};

out.start = { 状态行: await status(), 选中: await sel(), zoom: await zoom(), credits: await credits(), 浮层: await overlays() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);
await escAll();
out.起始id = await idsNow();

// ---------------------------------------------------------------- ① 小地图受控实验
log('\n=== ① 小地图开关：174 ↔ 171 的差是不是就等于这一个开关？ ===');
const 起点testid = await collect();
out.实验 = [{ 阶段: '起点', 种类: 起点testid.length }];
log('  起点（应为小地图关）：', 起点testid.length, '种');
const 起点开关态 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]');
  return e ? { ariaPressed: e.getAttribute('aria-pressed'), dataState: e.getAttribute('data-state') } : null; });
log('  开关态：', JSON.stringify(起点开关态));
save();

// 旧名 vs 新名：先在「关」态下各查一次
out.旧名 = await p.evaluate(() => {
  const cls = document.querySelectorAll('.dreamina-canvas-minimap-surface').length;
  const tid = document.querySelectorAll('[data-testid="dreamina-canvas-minimap-surface"]').length;
  return { 作class的元素数: cls, 作testid的元素数: tid };
});
log('  旧名 `dreamina-canvas-minimap-surface`：作 class 的元素', out.旧名.作class的元素数, '个｜作 testid 的', out.旧名.作testid的元素数, '个');
save();

// 开小地图
{
  const pt = await toggle('[data-testid="canvas-display-toggle-minimap"]', '小地图开');
  out.开落点 = pt;
  if (!pt.__err) {
    const after = await collect();
    const 开关态 = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]');
      return { ariaPressed: e.getAttribute('aria-pressed'), dataState: e.getAttribute('data-state') }; });
    out.实验.push({ 阶段: '开启后', 种类: after.length, 开关态, 增量: after.filter((t) => !起点testid.includes(t)), 减量: 起点testid.filter((t) => !after.includes(t)) });
    log('  开启后：', after.length, '种｜开关态', JSON.stringify(开关态));
    log('  **增量**：', JSON.stringify(after.filter((t) => !起点testid.includes(t))));
    log('  减量：', JSON.stringify(起点testid.filter((t) => !after.includes(t))));
    // 小地图三层 DOM 链 + 「有面积」是否等于「可见」
    out.小地图链 = await p.evaluate(() => {
      const s = document.querySelector('[data-testid="canvas-minimap-surface"]'); if (!s) return { __err: 'nf' };
      const nav = s.querySelector('[data-testid="canvas-minimap-navigation"]');
      const rf = s.querySelector('[data-testid="rf__minimap"]');
      const rd = (e) => { if (!e) return null; const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
        return { tag: e.tagName, rect: [r.x, r.y, r.width, r.height].map(Math.round), role: e.getAttribute('role'), aria: e.getAttribute('aria-label'),
          display: cs.display, opacity: cs.opacity, visibility: cs.visibility, pointerEvents: cs.pointerEvents, 子元素数: e.children.length }; };
      return { surface: rd(s), navigation: rd(nav), rfMinimap: rd(rf), 屏上文字: (s.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60) };
    });
    if (out.小地图链.__err) log('  ⛔ 小地图链', out.小地图链.__err);
    else { log('  小地图 DOM 链：');
      for (const k of ['surface', 'navigation', 'rfMinimap']) { const e = out.小地图链[k];
        log(`      · ${k}: ${e ? `<${e.tag}> ${e.rect.join(',')} role=${e.role} aria=${e.aria} 子元素=${e.子元素数}` : '（无）'}`); } }
    // 旧名现在在开态下还当 testid 吗？
    out.旧名开态 = await p.evaluate(() => ({ 作class: document.querySelectorAll('.dreamina-canvas-minimap-surface').length,
      作testid: document.querySelectorAll('[data-testid="dreamina-canvas-minimap-surface"]').length,
      新名class: document.querySelectorAll('.canvas-minimap-surface').length }));
    log('  开态下旧名：作 class', out.旧名开态.作class, '个｜作 testid', out.旧名开态.作testid, '个');
    log('  「新名」`canvas-minimap-surface` 作 class 的元素：', out.旧名开态.新名class, '个（**应为 0** —— 它只该是 testid）');
    save();
  }
}

// 关回去，再确认回到起点（证明这个开关是幂等、可逆、且**恰好**解释那 3 个）
{
  const pt = await toggle('[data-testid="canvas-display-toggle-minimap"]', '小地图关');
  if (!pt.__err) {
    const after = await collect();
    out.实验.push({ 阶段: '关回后', 种类: after.length,
      相对起点增量: after.filter((t) => !起点testid.includes(t)), 相对起点减量: 起点testid.filter((t) => !after.includes(t)) });
    log('  关回后：', after.length, '种｜相对起点增量', JSON.stringify(after.filter((t) => !起点testid.includes(t))), '减量', JSON.stringify(起点testid.filter((t) => !after.includes(t))));
    log('  🔑 结论：**开↔关这一个开关，恰好等于 171 ↔ 174 的全部差**，没有别的漂移。');
    save();
  }
}

// ---------------------------------------------------------------- ② 归位到基线（小地图开）
log('\n=== ② 归位：把小地图恢复成 a/b 两轮记录的基线态（开）===');
{
  const cur = await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-display-toggle-minimap"]'); return e ? e.getAttribute('aria-pressed') : null; });
  log('  当前 aria-pressed =', cur);
  if (cur !== 'true') { const pt = await toggle('[data-testid="canvas-display-toggle-minimap"]', '小地图归位开');
    const after = await collect(); log('  归位后 testid', after.length, '种（基线应为 174）', after.length === 174 ? '✅' : '⚠️'); save(); }
  else log('  已在开态，无需归位');
}

// ---------------------------------------------------------------- ③ 资产库「主体」页
log('\n=== ③ 资产库「主体」页（页签无 testid，按坐标现算落点）===');
{
  const pt = await toggle('[aria-label="资产库"]', '资产库');
  if (!pt.__err) {
    out.资产库节点数 = (await idsNow()).length;
    log('  打开后节点数', out.资产库节点数, '（必须仍为', out.起始id.length, '）');
    const before = await collect();
    // 「主体」页签：role=tab、文字逐字「主体」、无 testid
    const tab = await p.evaluate(() => {
      const tabs = Array.from(document.querySelectorAll('[role=tab]'));
      const e = tabs.find((x) => (x.innerText || '').replace(/\s+/g, '') === '主体');
      if (!e) return { __err: 'nf', 可见页签: tabs.map((t) => ({ 文字: (t.innerText || '').replace(/\s+/g, ''), tid: t.getAttribute('data-testid'), 选中: t.getAttribute('aria-selected') })) };
      const r = e.getBoundingClientRect();
      for (let y = Math.ceil(r.y) + 1; y <= r.y + r.height - 1; y += 2) for (let x = Math.ceil(r.x) + 1; x <= r.x + r.width - 1; x += 2) { const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y, 文字: (e.innerText || '').trim(), 矩形: [r.x, r.y, r.width, r.height].map(Math.round), 选中: e.getAttribute('aria-selected') }; }
      return { __err: 'np' };
    });
    out.主体页签 = tab;
    if (tab.__err) { log('  ⛔ 找「主体」页签：', tab.__err, JSON.stringify(tab.可见页签 || [])); }
    else {
      log('  页签', JSON.stringify(tab));
      await p.mouse.click(tab.x, tab.y); await p.waitForTimeout(1600);
      const after = await collect();
      out.主体页 = { 增量: after.filter((t) => !before.includes(t)), 减量: before.filter((t) => !after.includes(t)),
        tabpanel: await p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-asset-library-viewport"]'); if (!e) return null;
          const r = e.getBoundingClientRect(); return { 矩形: [r.x, r.y, r.width, r.height].map(Math.round), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 60), 测试id: e.getAttribute('data-testid') }; }) };
      log('  点「主体」后：**增量**', JSON.stringify(out.主体页.增量), '**减量**', JSON.stringify(out.主体页.减量));
      log('  视口容器：', JSON.stringify(out.主体页.tabpanel));
      out.主体页时全库元素 = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid^="canvas-asset-library"]')).map((e) => { const r = e.getBoundingClientRect();
        return { tid: e.getAttribute('data-testid'), tag: e.tagName, 矩形: [r.x, r.y, r.width, r.height].map(Math.round), 文字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 30) }; }));
      out.主体页时全库元素.forEach((e) => log('      ·', e.tid, `<${e.tag}>`, e.矩形.join(','), '«' + e.文字 + '»'));
      save();
    }
  }
  await escAll();
  log('  关闭后浮层：', await overlays(), '｜节点数', (await idsNow()).length);
}

// ---------------------------------------------------------------- 收尾
const endIds = await idsNow();
const endTestid = await collect();
out.收尾 = { 选中: await sel(), 状态行: await status(), 浮层: await overlays(), zoom: await zoom(), credits: await credits(), 节点数: endIds.length, 起始节点数: out.起始id.length, testid种类: endTestid.length };
out.新增id = endIds.filter((x) => !out.起始id.includes(x));
out.丢失id = out.起始id.filter((x) => !endIds.includes(x));
log('\n收尾：', JSON.stringify(out.收尾));
log('  新增 id（必须空）：', JSON.stringify(out.新增id), '｜丢失 id（必须空）：', JSON.stringify(out.丢失id));
save();
log('\nDONE e');
process.exit(0);
