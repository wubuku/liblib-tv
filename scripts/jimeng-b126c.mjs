// 批次 126 · c 轮：抓「积分明细」按钮点出来的**第二个浮层**，并与批次 125 的
//            `project-consumption-summary` 做**跨宿主对照**。
//
// 🔑 b 轮留下的关键异常：点「积分明细」后
//   · URL **没变**（不跳走）
//   · `canvas-feature-panel` 还在、内容逐字**一个字都没变**（不是同面板换内容）
//   · 但 `[role=dialog|menu|listbox]` 计数 **1 → 2**
//   ⇒ 它开的是**另一个浮层**，压在生成历史面板上。
//   而同一份「积分」数据在「项目信息 · 积分消耗」页签里也有一份（批次 125 实测过
//   `project-consumption-summary`，逐字「总消耗积分 0 ｜ 任务数 0 ｜ 暂无数据」）。
//   **两处 UI 若共享同一 testid ⇒ 同一个组件被放进两个宿主；若不共享 ⇒ 两套实现。**
//   这是本批最值钱的一对读数：不共享同一假设。
//
// ⛔ 只读：绝不点任何充值/订阅/购买/去支付类控件；发现即只记身份。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'c' };
const save = () => writeFileSync(new URL('./_tmp-b126c.json', import.meta.url), JSON.stringify(out, null, 1));
const shotDir = new URL('./_tmp-b126b-shots/', import.meta.url);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);

// 浮层清单（带身份指纹），用来做 before/after 差集
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]'))
  .filter((m) => m.getBoundingClientRect().width > 1)
  .map((m) => { const r = m.getBoundingClientRect(); return {
    tag: m.tagName, role: m.getAttribute('role'), tid: m.getAttribute('data-testid'),
    aria: m.getAttribute('aria-label'), rect: [r.x, r.y, r.width, r.height].map(Math.round),
    指纹: (m.getAttribute('data-testid') || m.getAttribute('aria-label') || m.tagName) + '@' + Math.round(r.x) + ',' + Math.round(r.y),
    逐字: (m.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 160) }; }));

out.start = { zoom: await zoom(), credits: await credits(), status: await status(), 浮层: (await overlays()).length };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);

// ---- ① 打开生成历史面板，记录浮层清单 before ----
const open = await p.evaluate(() => {
  const e = Array.from(document.querySelectorAll('[data-testid="canvas-panel-launcher"]')).find((x) => (x.getAttribute('aria-label') || '') === '生成历史');
  if (!e) return null; const r = e.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
    const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; }
  return null;
});
if (!open) { log('⛔ 找不到生成历史启动器'); save(); await b.close(); process.exit(3); }
await p.mouse.click(open.x, open.y); await p.waitForTimeout(1500);
out.before = await overlays();
log('\n=== ① 点「积分明细」之前的浮层清单（', out.before.length, '个）===');
out.before.forEach((o, i) => log(`  [${i}] <${o.tag}> role=${o.role} tid=${o.tid} aria=${JSON.stringify(o.aria)} ${JSON.stringify(o.rect)} «${o.逐字}»`));
save();

// ---- ② 点「积分明细」（落点现算 + 自检），然后抓新浮层 ----
const hit = await p.evaluate(() => {
  const panel = document.querySelector('[data-testid="canvas-feature-panel"]');
  if (!panel) return { __err: 'no-panel' };
  const e = Array.from(panel.querySelectorAll('button')).find((x) => /积分明细/.test(x.innerText || '') && !x.getAttribute('role'));
  if (!e) return { __err: 'no-btn' };
  const r = e.getBoundingClientRect();
  for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
    const h = document.elementFromPoint(x, y); const c = h && h.closest('button');
    if (c && c === e) return { x, y, 命中tag: h.tagName, 命中tag2: (h.closest('button') || {}).tagName };
  }
  return { __err: 'no-point' };
});
log('\n=== ② 落点自检：', JSON.stringify(hit));
if (hit.__err) { save(); await b.close(); process.exit(3); }
await p.mouse.click(hit.x, hit.y);
await p.waitForTimeout(1800);

out.after = await overlays();
const beforeFp = new Set(out.before.map((o) => o.指纹));
out.新浮层 = out.after.filter((o) => !beforeFp.has(o.指纹));
log('\n=== ② 点击后的浮层清单（', out.after.length, '个）；新出现 ', out.新浮层.length, ' 个 ===');
out.after.forEach((o, i) => log(`  [${i}] ${beforeFp.has(o.指纹) ? '旧' : '🆕'} <${o.tag}> role=${o.role} tid=${o.tid} aria=${JSON.stringify(o.aria)} ${JSON.stringify(o.rect)} «${o.逐字}»`));
save();

// ---- ③ 新浮层的完整解剖 ----
out.detail = await p.evaluate(() => {
  const cands = Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1);
  const panel = document.querySelector('[data-testid="canvas-feature-panel"]');
  // 找出既不是生成历史面板、也不是它的同矩形包装的那个
  const pr = panel && panel.getBoundingClientRect();
  const target = cands.find((m) => { if (m === panel) return false; const r = m.getBoundingClientRect();
    if (pr && Math.abs(r.x - pr.x) < 1 && Math.abs(r.y - pr.y) < 1 && Math.abs(r.width - pr.width) < 1) return false;
    return true; });
  if (!target) return { __err: 'no-new-overlay' };
  const R = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  const st = getComputedStyle(target);
  return { tag: target.tagName, cls: (target.getAttribute('class') || '').slice(0, 80), role: target.getAttribute('role'),
    tid: target.getAttribute('data-testid'), aria: target.getAttribute('aria-label'),
    ariaModal: target.getAttribute('aria-modal'), ariaExpanded: target.getAttribute('aria-expanded'),
    dataState: target.getAttribute('data-state'), rect: R(target), position: st.position, zIndex: st.zIndex,
    pointerEvents: st.pointerEvents, overflow: st.overflow,
    逐字: (target.innerText || '').replace(/\s+/g, ' ').trim(),
    孩子数: target.children.length,
    内部testid: Array.from(target.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')),
    内部aria: Array.from(target.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')),
    内部role: Array.from(target.querySelectorAll('[role]')).map((e) => e.getAttribute('role') + ':' + (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24)),
    标题: Array.from(target.querySelectorAll('h1,h2,h3,h4')).map((e) => ({ tag: e.tagName, rect: R(e), 文字: (e.innerText || '').trim() })),
    可点: Array.from(target.querySelectorAll('button,a,[role=button],[role=tab]')).map((e) => ({ tag: e.tagName, role: e.getAttribute('role'),
      rect: R(e), 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), aria: e.getAttribute('aria-label'),
      禁用: e.hasAttribute('disabled') || e.getAttribute('aria-disabled') === 'true' })),
    表格: Array.from(target.querySelectorAll('table,[role=table],[role=grid],[role=row],[role=cell]')).map((e) => ({ tag: e.tagName, role: e.getAttribute('role'), rect: R(e) })),
    输入框: Array.from(target.querySelectorAll('input,textarea,select')).map((e) => ({ tag: e.tagName, type: e.getAttribute('type'), rect: R(e), 占位: e.getAttribute('placeholder') })),
    与面板关系: panel ? { 包含面板: target.contains(panel), 面板包含它: panel.contains(target), 父级: target.parentElement.tagName + '.' + (target.parentElement.getAttribute('class') || '').slice(0, 40) } : null };
});
log('\n=== ③ 新浮层解剖 ===');
if (out.detail.__err) { log('  ', out.detail.__err); save(); await b.close(); process.exit(3); }
log('  本体：', JSON.stringify({ tag: out.detail.tag, role: out.detail.role, tid: out.detail.tid, aria: out.detail.aria, ariaModal: out.detail.ariaModal, rect: out.detail.rect, position: out.detail.position, zIndex: out.detail.zIndex, pe: out.detail.pointerEvents, 孩子数: out.detail.孩子数 }));
log('  逐字：', JSON.stringify(out.detail.逐字));
log('  标题：', JSON.stringify(out.detail.标题));
log('  内部 testid：', JSON.stringify(out.detail.内部testid));
log('  内部 aria：', JSON.stringify(out.detail.内部aria));
log('  内部 role：', JSON.stringify(out.detail.内部role));
log('  可点元素（', out.detail.可点.length, '个）：');
out.detail.可点.forEach((e, i) => log(`    [${i}] <${e.tag}> role=${e.role ?? '-'} ${JSON.stringify(e.rect)} «${e.文字}» aria=${JSON.stringify(e.aria)} 禁用=${e.禁用}`));
log('  表格元素：', out.detail.表格.length, JSON.stringify(out.detail.表格.slice(0, 8)));
log('  输入框：', out.detail.输入框.length, JSON.stringify(out.detail.输入框));
log('  与生成历史面板的关系：', JSON.stringify(out.detail.与面板关系));
save();
await p.screenshot({ path: new URL('20-credits-overlay.png', shotDir).pathname, clip: { x: 640, y: 40, width: 620, height: 420 } });
await p.screenshot({ path: new URL('20-credits-overlay-full.png', shotDir).pathname });

// ---- ④ 跨宿主对照：文档里有没有 project-consumption-summary？本轮浮层里有没有？ ----
out.跨宿主对照 = {
  本浮层含projectConsumptionSummary: out.detail.内部testid.includes('project-consumption-summary'),
  本浮层含generationHistoryPanel: out.detail.内部testid.includes('generation-history-panel'),
  页面同时存在几个projectConsumptionSummary: await p.evaluate(() => document.querySelectorAll('[data-testid="project-consumption-summary"]').length),
  页面同时存在几个generationHistoryItems: await p.evaluate(() => document.querySelectorAll('#generation-history-items,[id=generation-history-items]').length),
  浮层同时存在几个generationHistoryPanel: await p.evaluate(() => document.querySelectorAll('[data-testid="generation-history-panel"]').length)
};
log('\n=== ④ 跨宿主对照 ===\n  ', JSON.stringify(out.跨宿主对照, null, 1));
save();

// ---- ⑤ Esc 一次关掉几个？两次呢？ ----
await p.keyboard.press('Escape'); await p.waitForTimeout(1200);
out.Esc1 = (await overlays()).map((o) => o.指纹);
log('\n=== ⑤ 第一次 Esc 后浮层 ===\n  ', JSON.stringify(out.Esc1));
await p.screenshot({ path: new URL('21-after-esc1.png', shotDir).pathname });
await p.keyboard.press('Escape'); await p.waitForTimeout(1200);
out.Esc2 = (await overlays()).map((o) => o.指纹);
log('  第二次 Esc 后浮层：\n  ', JSON.stringify(out.Esc2));
out.收尾 = { 浮层数: out.Esc2.length, 面板在: await p.evaluate(() => !!document.querySelector('[data-testid="canvas-feature-panel"]')),
  选中: await sel(), zoom: await zoom(), credits: await credits(), status: await status(), 浮层全清: out.Esc2.length === 0 };
log('  收尾：', JSON.stringify(out.收尾));
save();
log('\nDONE c');
process.exit(0);
