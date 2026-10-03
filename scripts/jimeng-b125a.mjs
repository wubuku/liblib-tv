// 批次 125 · a 轮（只读 + 页签切换）：把「项目信息」面板的**两个页签**都读全。
//
// 🔑 靶子：批次 124 首次把 `workspace-project-info-dialog` 读全时，只读了**默认页签**
//   「基础信息」，而这个面板顶部还有第二个页签 **`积分消耗`**、底部还有一个
//   **`查看积分明细`** 按钮 —— **全册从未取证**。
//
// ⛔ 安全边界（先判后点，不点「看起来像按钮」的东西）：
//   · 只切**同一个对话框内部**的页签（判据：该元素的 `role="tab"` 且在对话框内）。
//   · ⛔ **绝不点 `查看积分明细`** —— 它很可能跳出到积分/充值页，
//     而本手册开头就写明「账户、充值、订阅、积分购买不在本手册范围内」。
//   · 所以本轮把它的身份、几何、可能的目标**只读**记下来，执行与否**留待授权**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b125a.json', import.meta.url), JSON.stringify(out, null, 1));
const shotDir = new URL('./_tmp-b125b-shots/', import.meta.url);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);

out.start = { zoom: await zoom(), credits: await credits(), status: await status() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);

// ---- 打开 项目信息：更多 → 项目信息 ----
async function openMore() {
  const pt = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('button')).find((x) => (x.getAttribute('aria-label') || '') === '更多');
    if (!e) return { __err: 'no-more' }; const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
      const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; }
    return { __err: 'no-point' }; });
  if (pt.__err) return pt;
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1400);
  const it = await p.evaluate(() => { for (const m of document.querySelectorAll('[role=menu]')) { if (getComputedStyle(m).visibility === 'hidden') continue;
    for (const k of m.querySelectorAll('[role=menuitem]')) { if (!/^项目信息/.test((k.innerText || '').replace(/\s+/g, ' ').trim())) continue;
      const r = k.getBoundingClientRect(); if (r.width < 1) continue;
      for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 3) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 3) {
        const e = document.elementFromPoint(x, y); if (e && (e === k || k.contains(e))) return { x, y }; } } } return null; });
  if (!it) { await p.keyboard.press('Escape'); await p.waitForTimeout(700); return { __err: 'no-item' }; }
  await p.mouse.click(it.x, it.y); await p.waitForTimeout(1700);
  return { ok: true };
}
out.open = await openMore();
log('打开「更多 → 项目信息」：', JSON.stringify(out.open));
if (out.open.__err) { log('⛔ 中止'); save(); await b.close(); process.exit(3); }

// ---- ① 面板结构 + 页签身份 ----
out.struct = await p.evaluate(() => {
  const d = document.querySelector('[data-testid="workspace-project-info-dialog"]');
  if (!d) return { __err: 'no-dialog' };
  const r = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const desc = (e) => ({ tag: e.tagName, role: e.getAttribute('role'), tid: e.getAttribute('data-testid'),
    ariaSelected: e.getAttribute('aria-selected'), ariaControls: e.getAttribute('aria-controls'),
    dataState: e.getAttribute('data-state'), aria: e.getAttribute('aria-label'),
    文字: (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 30),
    矩形: r(e), 在对话框内: d.contains(e) });
  return { 矩形: r(d), role: d.getAttribute('role'),
    页签: Array.from(d.querySelectorAll('[role=tab]')).map(desc),
    页签容器: Array.from(d.querySelectorAll('[role=tablist],[role=tabpanel]')).map(desc),
    全部可点: Array.from(d.querySelectorAll('button,[role=button],[role=tab],a')).map(desc),
    内部testid: Array.from(d.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')),
    逐字: (d.innerText || '').replace(/\s+/g, ' ').trim() };
});
log('\n=== ① 面板结构 ===');
if (out.struct.__err) { log('  ', out.struct.__err); save(); await b.close(); process.exit(3); }
log('  矩形：', JSON.stringify(out.struct.矩形), '｜role：', out.struct.role, '｜内部 testid：', JSON.stringify(out.struct.内部testid));
log('  页签（role=tab）：');
out.struct.页签.forEach((t, i) => log(`    [${i}] <${t.tag}> ${JSON.stringify(t.矩形)} 文字=${JSON.stringify(t.文字)} aria-selected=${t.ariaSelected} data-state=${t.dataState} aria-controls=${JSON.stringify(t.ariaControls)}`));
log('  全部可点元素：');
out.struct.全部可点.forEach((t) => log(`    <${t.tag}> role=${t.role} ${JSON.stringify(t.矩形)} 文字=${JSON.stringify(t.文字)} aria=${JSON.stringify(t.aria)}`));
save();
await p.screenshot({ path: new URL('00-basic-tab.png', shotDir).pathname, clip: { x: 240, y: 80, width: 800, height: 560 } });

// ---- ② 切到「积分消耗」页签（只切对话框内部的 role=tab） ----
const tab2 = out.struct.页签.find((t) => /积分消耗/.test(t.文字) && t.ariaSelected !== 'true');
out.tab2 = tab2;
if (tab2) {
  const hit = await p.evaluate((rect) => { for (let y = Math.ceil(rect[1]) + 2; y <= rect[1] + rect[3] - 2; y += 2)
    for (let x = Math.ceil(rect[0]) + 2; x <= rect[0] + rect[2] - 2; x += 2) { const e = document.elementFromPoint(x, y);
      const t = e && e.closest('[role=tab]'); if (t && /积分消耗/.test(t.innerText || '')) return { x, y }; }
    return null; }, tab2.矩形);
  log('\n切页签「积分消耗」落点：', JSON.stringify(hit));
  if (hit) {
    await p.mouse.click(hit.x, hit.y);
    await p.waitForTimeout(1700);
    out.tab2Read = await p.evaluate(() => {
      const d = document.querySelector('[data-testid="workspace-project-info-dialog"]');
      const r = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
      return { 矩形: r(d), 逐字: (d.innerText || '').replace(/\s+/g, ' ').trim(),
        页签: Array.from(d.querySelectorAll('[role=tab]')).map((e) => ({ 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), ariaSelected: e.getAttribute('aria-selected'), dataState: e.getAttribute('data-state') })),
        tabpanel: Array.from(d.querySelectorAll('[role=tabpanel]')).map((e) => ({ 矩形: r(e), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200) })),
        表格: Array.from(d.querySelectorAll('table,[role=table],[role=grid]')).map((e) => ({ 矩形: r(e), 行: Array.from(e.querySelectorAll('tr,[role=row]')).length, 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 200) })),
        内部testid: Array.from(d.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')) };
    });
    log('\n=== ② 「积分消耗」页签内容 ===');
    log('  逐字：', JSON.stringify(out.tab2Read.逐字));
    log('  页签态：', JSON.stringify(out.tab2Read.页签));
    log('  tabpanel：', JSON.stringify(out.tab2Read.tabpanel));
    log('  表格：', JSON.stringify(out.tab2Read.表格));
    log('  内部 testid：', JSON.stringify(out.tab2Read.内部testid));
    await p.screenshot({ path: new URL('01-credits-tab.png', shotDir).pathname, clip: { x: 240, y: 80, width: 800, height: 560 } });
  }
}
save();

// ---- ③ 「查看积分明细」的身份（只读，不点） ----
out.ledgerBtn = await p.evaluate(() => { const d = document.querySelector('[data-testid="workspace-project-info-dialog"]');
  const e = Array.from(d.querySelectorAll('button,[role=button],a')).find((x) => /查看积分明细/.test(x.innerText || x.getAttribute('aria-label') || ''));
  if (!e) return { __none: true };
  const r = e.getBoundingClientRect();
  return { tag: e.tagName, role: e.getAttribute('role'), tid: e.getAttribute('data-testid'), href: e.getAttribute('href'),
    target: e.getAttribute('target'), aria: e.getAttribute('aria-label'), 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(),
    矩形: [r.x, r.y, r.width, r.height].map(Math.round), 禁用: e.getAttribute('aria-disabled') === 'true' || e.hasAttribute('disabled') }; });
log('\n=== ③「查看积分明细」身份（只读，不点）===');
log('  ', JSON.stringify(out.ledgerBtn));
save();

// ---- 收尾：Esc 关掉，回到干净终态 ----
await p.keyboard.press('Escape'); await p.waitForTimeout(1100);
await p.keyboard.press('Escape'); await p.waitForTimeout(1100);
out.收尾 = { 浮层: await p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu]')).filter((m) => m.getBoundingClientRect().width > 1).length),
  选中: await sel(), zoom: await zoom(), credits: await credits(), status: await status() };
log('\n收尾：', JSON.stringify(out.收尾));
save();
log('\nDONE a');
process.exit(0);
