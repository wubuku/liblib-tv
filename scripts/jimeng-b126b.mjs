// 批次 126 · b 轮：① 逐个切 5 个二级页签，看每个空态逐字是不是同一句
//            ② 测「点面板外能不能关」（点空白必须命中 `.react-flow__pane`，批次 120 规一）
//            ③ 读清「积分明细」按钮的身份，**带 URL 守卫**地点它一次
//
// 📌 a 轮已定的关键事实（b 轮继承，不再重测）：
//   · 面板 `<ASIDE role="dialog" aria="生成历史"> 320×211@797,56`，`z-index:30`，父级是
//     `canvas-workbench-shell`（**没有 portal 到 body**）。
//   · 「生成历史 ｜ 积分明细」**不是页签**：是 `H2 56×36@813,72` + `BUTTON 68×36@1033,72`，
//     那个按钮**没有 role、没有 href、没有 aria**，只带一个 `12×12` 的 `<svg>`。
//   · 真页签只有下面那 5 个：`role="tablist" aria="History categories"` + 5 个
//     `BUTTON role="tab" 42×36`，`aria-controls` **全指向同一个** `generation-history-items`。
//   · 五个 tab 的 `data-state` 是 `null`（属性不存在）；启动器 `data-state` 恒 `closed` 而
//     `aria-expanded` 真的 false→true。
//
// ⛔ 边界：本轮**不点任何生成/扣费控件**。「积分明细」是标题行里那个按钮，
//   它可能只是同面板换内容、也可能跳到别处 ⇒ 点击前后都读 URL，一旦离开画布立刻 goBack。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b' };
const save = () => writeFileSync(new URL('./_tmp-b126b.json', import.meta.url), JSON.stringify(out, null, 1));
const shotDir = new URL('./_tmp-b126b-shots/', import.meta.url);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]')).filter((m) => m.getBoundingClientRect().width > 1).length);

out.start = { url: p.url(), zoom: await zoom(), credits: await credits(), status: await status(), 浮层: await overlays() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);

// 面板可能还开着（a 轮留在开着的状态）
const reopen = async () => {
  const open = await p.evaluate(() => !!document.querySelector('[data-testid="canvas-feature-panel"]'));
  if (open) return { 已是开: true };
  const pt = await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid="canvas-panel-launcher"]')).find((x) => (x.getAttribute('aria-label') || '') === '生成历史');
    if (!e) return null; const r = e.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2) for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
      const h = document.elementFromPoint(x, y); if (h && (h === e || e.contains(h))) return { x, y }; } return null; });
  if (!pt) return { __err: 'no-launcher' };
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1500);
  return { 重开: true, 面板在: await p.evaluate(() => !!document.querySelector('[data-testid="canvas-feature-panel"]')) };
};
out.reopen = await reopen();
log('面板准备：', JSON.stringify(out.reopen));

// 面板内读数器
const readPanel = () => p.evaluate(() => {
  const panel = document.querySelector('[data-testid="canvas-feature-panel"]');
  if (!panel) return { __err: 'no-panel' };
  const R = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
  return { 面板: R(panel), 逐字: (panel.innerText || '').replace(/\s+/g, ' ').trim(),
    tab: Array.from(panel.querySelectorAll('[role=tab]')).map((e) => ({ 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(),
      sel: e.getAttribute('aria-selected'), dstate: e.getAttribute('data-state'), ctl: e.getAttribute('aria-controls') })),
    tabpanel: Array.from(panel.querySelectorAll('[role=tabpanel]')).map((e) => ({ 矩形: R(e), 逐字: (e.innerText || '').replace(/\s+/g, ' ').trim(),
      孩子数: e.children.length, 内部: Array.from(e.querySelectorAll('*')).map((c) => c.tagName + (c.getAttribute('data-testid') ? '[' + c.getAttribute('data-testid') + ']' : '')) })),
    内部testid: Array.from(panel.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')),
    H2: Array.from(panel.querySelectorAll('h1,h2,h3')).map((e) => ({ tag: e.tagName, 矩形: R(e), 文字: (e.innerText || '').trim() })),
    标题行按钮: Array.from(panel.querySelectorAll('button')).filter((e) => !e.getAttribute('role')).map((e) => ({ 矩形: R(e), 文字: (e.innerText || '').replace(/\s+/g, ' ').trim() })) };
});

// ---- ① 逐个切 5 个二级页签 ----
out.tabs = [];
const names = ['全部', '图片', '视频', '音频', '文本'];
for (let i = 0; i < names.length; i++) {
  const hit = await p.evaluate((name) => {
    const tabs = Array.from(document.querySelectorAll('[data-testid="canvas-feature-panel"] [role=tab]'));
    const t = tabs.find((e) => (e.innerText || '').replace(/\s+/g, '').trim() === name);
    if (!t) return { __err: 'no-tab:' + name };
    const r = t.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2)
      for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
        const h = document.elementFromPoint(x, y);
        const c = h && h.closest('[role=tab]');
        if (c && c === t) return { x, y };
      }
    return { __err: 'no-point:' + name };
  }, names[i]);
  if (hit.__err) { out.tabs.push({ 名: names[i], 落点: hit }); log(`  [${names[i]}] ⛔ ${hit.__err}`); continue; }
  await p.mouse.click(hit.x, hit.y);
  await p.waitForTimeout(900);
  const rd = await readPanel();
  out.tabs.push({ 名: names[i], 落点: hit, 读数: rd });
  log(`  [${names[i]}] 面板=${JSON.stringify(rd.面板)} 逐字=${JSON.stringify(rd.逐字)}`);
  log(`         tab 态=${JSON.stringify(rd.tab.map((t) => t.文字 + '=' + t.sel + '/dstate=' + t.dstate))}`);
  log(`         tabpanel=${JSON.stringify(rd.tabpanel)}`);
  log(`         H2=${JSON.stringify(rd.H2)} 标题行按钮=${JSON.stringify(rd.标题行按钮)}`);
  if (i === 1) await p.screenshot({ path: new URL('10-tab-image.png', shotDir).pathname, clip: { x: 780, y: 40, width: 360, height: 250 } });
  if (i === 3) await p.screenshot({ path: new URL('11-tab-audio.png', shotDir).pathname, clip: { x: 780, y: 40, width: 360, height: 250 } });
}
save();

// A/B 对照：五个页签的空态逐字是否逐字相同？
const texts = out.tabs.filter((t) => t.读数).map((t) => t.读数.逐字);
out.空态对照 = { 各页签逐字: texts, 是否全部相同: new Set(texts).size === 1, 面板高度集合: [...new Set(out.tabs.filter((t) => t.读数).map((t) => JSON.stringify(t.读数.面板)))] };
log('\n=== ① 五个二级页签的空态对照 ===');
log('  ', JSON.stringify(out.空态对照, null, 1));
save();

// ---- ② 点面板外能不能关：落点必须命中 `.react-flow__pane`（批次 120 规一：点空白要反着判） ----
const pane = await p.evaluate(() => {
  const panel = document.querySelector('[data-testid="canvas-feature-panel"]');
  const pr = panel.getBoundingClientRect();
  for (let y = 300; y < 640; y += 7) for (let x = 400; x < 780; x += 7) {
    if (x > pr.x - 8 && x < pr.x + pr.width + 8 && y > pr.y - 8 && y < pr.y + pr.height + 8) continue;
    const h = document.elementFromPoint(x, y);
    if (h && h.classList && h.classList.contains('react-flow__pane')) return { x, y, tag: h.tagName, cls: h.getAttribute('class') };
  }
  return null;
});
log('\n=== ② 点面板外关闭 ===\n  空白落点（必须命中 pane）：', JSON.stringify(pane));
if (pane) {
  await p.mouse.click(pane.x, pane.y);
  await p.waitForTimeout(1100);
  out.外点 = { 点后面板在: await p.evaluate(() => !!document.querySelector('[data-testid="canvas-feature-panel"]')),
    启动器ariaExpanded: await p.evaluate(() => { const e = Array.from(document.querySelectorAll('[data-testid="canvas-panel-launcher"]')).find((x) => (x.getAttribute('aria-label') || '') === '生成历史'); return e ? e.getAttribute('aria-expanded') : null; }),
    浮层: await overlays() };
  log('  点空白后：', JSON.stringify(out.外点));
  await p.screenshot({ path: new URL('12-after-outside-click.png', shotDir).pathname });
} else log('  ⛔ 找不到安全的 pane 落点，跳过');
save();

// ---- ③ 「积分明细」按钮：先只读身份，再带 URL 守卫地点 ----
await reopen();
const credBtn = await p.evaluate(() => {
  const panel = document.querySelector('[data-testid="canvas-feature-panel"]');
  if (!panel) return { __err: 'no-panel' };
  const e = Array.from(panel.querySelectorAll('button')).find((x) => /积分明细/.test(x.innerText || ''));
  if (!e) return { __err: 'no-btn' };
  const r = e.getBoundingClientRect();
  const svgs = Array.from(e.querySelectorAll('svg')).map((s) => ({ 矩形: (() => { const q = s.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); })(),
    viewBox: s.getAttribute('viewBox'), path: Array.from(s.querySelectorAll('path,line,polyline')).map((n) => (n.getAttribute('d') || n.getAttribute('points') || '').slice(0, 40)) }));
  return { tag: e.tagName, role: e.getAttribute('role'), tid: e.getAttribute('data-testid'), cls: e.getAttribute('class'),
    href: e.getAttribute('href'), target: e.getAttribute('target'), type: e.getAttribute('type'),
    aria: e.getAttribute('aria-label'), ariaExpanded: e.getAttribute('aria-expanded'), dataState: e.getAttribute('data-state'),
    dataAttrs: Array.from(e.attributes).map((a) => a.name + '=' + a.value.slice(0, 30)),
    矩形: [r.x, r.y, r.width, r.height].map(Math.round), 文字: (e.innerText || '').replace(/\s+/g, ' ').trim(), svg: svgs,
    父: e.parentElement.tagName + '.' + (e.parentElement.getAttribute('class') || '').slice(0, 40) };
});
out.积分明细按钮 = credBtn;
log('\n=== ③ 「积分明细」按钮身份（先只读）===\n  ', JSON.stringify(credBtn, null, 1));
save();

if (credBtn && !credBtn.__err) {
  const before = p.url();
  const hit = await p.evaluate((rect) => { for (let y = Math.ceil(rect[1]) + 2; y <= rect[1] + rect[3] - 2; y += 2)
    for (let x = Math.ceil(rect[0]) + 2; x <= rect[0] + rect[2] - 2; x += 2) {
      const h = document.elementFromPoint(x, y);
      const c = h && h.closest('button');
      if (c && /积分明细/.test(c.innerText || '') && !c.getAttribute('role')) return { x, y }; }
    return null; }, credBtn.矩形);
  log('  落点：', JSON.stringify(hit));
  if (hit) {
    await p.mouse.click(hit.x, hit.y);
    await p.waitForTimeout(1600);
    out.点击积分明细后 = { url前: before, url后: p.url(), 离开画布: !p.url().includes('ai-canvas'),
      面板在: await p.evaluate(() => !!document.querySelector('[data-testid="canvas-feature-panel"]')),
      浮层: await overlays() };
    log('  点击后：', JSON.stringify(out.点击积分明细后));
    if (out.点击积分明细后.离开画布) {
      log('  ⛔ 跳走了，立即返回画布');
      await p.goBack({ waitUntil: 'domcontentloaded' }); await p.waitForTimeout(2500);
      await pinViewport(p);
      out.返回后 = { url: p.url(), zoom: await zoom(), credits: await credits() };
      log('  返回后：', JSON.stringify(out.返回后));
    } else {
      out.积分明细内容 = await readPanel();
      log('  面板内读数：', JSON.stringify(out.积分明细内容, null, 1));
      await p.screenshot({ path: new URL('13-credits-in-panel.png', shotDir).pathname, clip: { x: 780, y: 40, width: 400, height: 300 } });
      await p.screenshot({ path: new URL('13-credits-in-panel-full.png', shotDir).pathname });
    }
  }
}
save();

// ---- 收尾：Esc 关掉，回到干净终态 ----
await p.keyboard.press('Escape'); await p.waitForTimeout(1200);
out.收尾1 = { 浮层: await overlays(), 面板在: await p.evaluate(() => !!document.querySelector('[data-testid="canvas-feature-panel"]')), 选中: await sel(), zoom: await zoom() };
await p.keyboard.press('Escape'); await p.waitForTimeout(1200);
out.收尾2 = { 浮层: await overlays(), 面板在: await p.evaluate(() => !!document.querySelector('[data-testid="canvas-feature-panel"]')), 选中: await sel(), zoom: await zoom(), credits: await credits(), status: await status() };
log('\n收尾：', JSON.stringify(out.收尾2));
save();
log('\nDONE b');
process.exit(0);
