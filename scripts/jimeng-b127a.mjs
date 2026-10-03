// 批次 127 · a 轮：用**同一套仪表**读「搜索」面板与「生成历史」面板，好做结构对比。
//
// 🔑 靶子（来自批次 126 的读数）：手册把「搜索」和「生成历史」写成**两个面板**，
//   但两条记录有一个刺眼的不一致：
//     · 两者**共用同一个** `data-testid="canvas-panel-launcher"`（批次 126 已证）
//     · 两者**面板尺寸都是 `320×211`**（搜索的坐标从没记过）
//   假设 H：「它们其实是**同一个面板组件**（`canvas-feature-panel`）的两种初始内容」——
//   与批次 126 挖出的「积分明细按钮开的是项目信息对话框」是同一形状的发现。
//   判据：**把两棵 DOM 树用同一个 walker 走一遍，逐层比 tag/矩形/testid/aria。**
//
// 📌 沿用已立的规：
//   · 判「元素在不在」要扫**所有可能宿主**（testid / class / role / 结构位置），
//     不能只按 testid 查 —— 万一它换了 testid，结论会假阴性。
//   · 落点在**动作时刻现算** ＋ `elementFromPoint` 自检（`el===t || t.contains(el)`）。
//   · Radix 弹层开合只认 `aria-expanded`；`data-state` 用 `getAttribute` 回读。
//   · `data-state` 为 `null` 就是「属性不存在」，不是「没变化」。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'a' };
const save = () => writeFileSync(new URL('./_tmp-b127a.json', import.meta.url), JSON.stringify(out, null, 1));
const shotDir = new URL('./_tmp-b127a-shots/', import.meta.url);

const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });
const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const status = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || [])[0]);
const sel = () => p.evaluate(() => document.querySelectorAll('.react-flow__node.selected').length);
const overlays = () => p.evaluate(() => Array.from(document.querySelectorAll('[role=dialog],[role=menu],[role=listbox]'))
  .filter((m) => m.getBoundingClientRect().width > 1)
  .map((m) => { const r = m.getBoundingClientRect(); return { tag: m.tagName, role: m.getAttribute('role'), tid: m.getAttribute('data-testid'), aria: m.getAttribute('aria-label'), rect: [r.x, r.y, r.width, r.height].map(Math.round) }; }));

out.start = { zoom: await zoom(), credits: await credits(), status: await status(), 浮层: await overlays() };
log('起点：', JSON.stringify(out.start));
await keyGuard(p);

// ---- 通用：按 aria 找启动器并点开（落点现算 + 自检） ----
async function openLauncher(aria) {
  const before = await p.evaluate((a) => {
    const all = Array.from(document.querySelectorAll('[data-testid="canvas-panel-launcher"]'));
    const t = all.find((e) => (e.getAttribute('aria-label') || '') === a);
    if (!t) return { __err: 'no-launcher', 候选: all.map((e) => e.getAttribute('aria-label')) };
    return { 候选: all.map((e) => { const r = e.getBoundingClientRect(); return { aria: e.getAttribute('aria-label'), rect: [r.x, r.y, r.width, r.height].map(Math.round), ariaExpanded: e.getAttribute('aria-expanded'), dataState: e.getAttribute('data-state') }; }),
      目标: { tag: t.tagName, ariaExpanded: t.getAttribute('aria-expanded'), dataState: t.getAttribute('data-state') } };
  }, aria);
  if (before.__err) return before;
  const pt = await p.evaluate((a) => {
    const t = Array.from(document.querySelectorAll('[data-testid="canvas-panel-launcher"]')).find((e) => (e.getAttribute('aria-label') || '') === a);
    if (!t) return null;
    const r = t.getBoundingClientRect();
    for (let y = Math.ceil(r.y) + 2; y <= r.y + r.height - 2; y += 2)
      for (let x = Math.ceil(r.x) + 2; x <= r.x + r.width - 2; x += 2) {
        const h = document.elementFromPoint(x, y);
        if (h && (h === t || t.contains(h))) return { x, y, 命中: h.tagName + (h.getAttribute('aria-label') ? '[' + h.getAttribute('aria-label') + ']' : '') };
      }
    return null;
  }, aria);
  if (!pt) return { __err: 'no-point', before };
  await p.mouse.click(pt.x, pt.y);
  await p.waitForTimeout(1600);
  const after = await p.evaluate((a) => { const t = Array.from(document.querySelectorAll('[data-testid="canvas-panel-launcher"]')).find((e) => (e.getAttribute('aria-label') || '') === a);
    return { ariaExpanded: t ? t.getAttribute('aria-expanded') : null, dataState: t ? t.getAttribute('data-state') : null }; }, aria);
  return { 候选: before.候选, 点前: before.目标, 落点: pt, 点后: after };
}

// ---- 通用：把「画布右上角那块面板」整个挖出来（不预设 testid） ----
async function readPanel(tag) {
  return p.evaluate((label) => {
    // ① 先找 canvas-feature-panel
    // ② 若没有，按「有面积的 role=dialog 且锚在右上角」扫所有宿主，避免假阴性
    const cands = Array.from(document.querySelectorAll('[data-testid="canvas-feature-panel"]'));
    const dialogs = Array.from(document.querySelectorAll('[role=dialog]')).filter((m) => { const r = m.getBoundingClientRect(); return r.width > 1 && r.height > 1; });
    const panel = cands[0] || dialogs.find((m) => { const r = m.getBoundingClientRect(); return r.x > 600 && r.y < 200; });
    if (!panel) return { __err: 'no-panel', canvasFeaturePanel数: cands.length, dialog数: dialogs.length };
    const R = (e) => { const q = e.getBoundingClientRect(); return [q.x, q.y, q.width, q.height].map(Math.round); };
    const D = (e) => ({ tag: e.tagName, role: e.getAttribute('role'), tid: e.getAttribute('data-testid'),
      ariaSelected: e.getAttribute('aria-selected'), ariaControls: e.getAttribute('aria-controls'),
      dataState: e.getAttribute('data-state'), rect: R(e),
      文字: (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40) });
    const tree = [];
    const walk = (e, d) => { if (d > 6) return; const r = e.getBoundingClientRect();
      tree.push({ d, tag: e.tagName, cls: (e.getAttribute('class') || '').slice(0, 34), role: e.getAttribute('role'),
        tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), type: e.getAttribute('type'),
        placeholder: e.getAttribute('placeholder'), ariaSelected: e.getAttribute('aria-selected'),
        ariaControls: e.getAttribute('aria-controls'), dataState: e.getAttribute('data-state'),
        rect: R(r.width >= 1 && r.height >= 1 ? e : e), 有面积: r.width >= 1 && r.height >= 1,
        文字: (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 36) });
      Array.from(e.children).forEach((c) => walk(c, d + 1)); };
    walk(panel, 0);
    const pr = panel.getBoundingClientRect();
    const sameRect = Array.from(document.querySelectorAll('body *')).filter((e) => { const r = e.getBoundingClientRect();
      return r.width > 1 && Math.abs(r.x - pr.x) < 1 && Math.abs(r.y - pr.y) < 1 && Math.abs(r.width - pr.width) < 1 && Math.abs(r.height - pr.height) < 1; })
      .map((e) => ({ tag: e.tagName, tid: e.getAttribute('data-testid'), role: e.getAttribute('role') }));
    let chain = [], e2 = panel;
    for (let i = 0; i < 3 && e2 && e2 !== document.body; i++) { e2 = e2.parentElement; if (e2) chain.push({ tag: e2.tagName, tid: e2.getAttribute('data-testid'), cls: (e2.getAttribute('class') || '').slice(0, 34), rect: R(e2) }); }
    return { 标签: label, canvasFeaturePanel数: cands.length,
      本体: { tag: panel.tagName, role: panel.getAttribute('role'), tid: panel.getAttribute('data-testid'),
        aria: panel.getAttribute('aria-label'), rect: R(panel), 孩子数: panel.children.length },
      逐字: (panel.innerText || '').replace(/\s+/g, ' ').trim(),
      tab: Array.from(panel.querySelectorAll('[role=tab]')).map(D),
      tablist: Array.from(panel.querySelectorAll('[role=tablist]')).map(D),
      tabpanel: Array.from(panel.querySelectorAll('[role=tabpanel]')).map((x) => ({ ...D(x), 逐字: (x.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 220) })),
      button: Array.from(panel.querySelectorAll('button')).map(D),
      input: Array.from(panel.querySelectorAll('input,textarea')).map((x) => ({ ...D(x), type: x.getAttribute('type'), placeholder: x.getAttribute('placeholder'), value: x.value })),
      内部testid: Array.from(panel.querySelectorAll('[data-testid]')).map((x) => x.getAttribute('data-testid')),
      内部aria: Array.from(panel.querySelectorAll('[aria-label]')).map((x) => x.getAttribute('aria-label')),
      内部role: Array.from(panel.querySelectorAll('[role]')).map((x) => x.getAttribute('role')),
      表格: panel.querySelectorAll('table,[role=table],[role=grid],[role=row]').length,
      同矩形: sameRect, 祖先链: chain, 树: tree };
  }, tag);
}

const show = (r, title) => {
  log(`\n=== ${title} ===`);
  if (r.__err) { log('  ', JSON.stringify(r)); return; }
  log('  canvas-feature-panel 元素数：', r.canvasFeaturePanel数);
  log('  本体：', JSON.stringify(r.本体));
  log('  逐字：', JSON.stringify(r.逐字));
  log('  tablist（', r.tablist.length, '）：', JSON.stringify(r.tablist));
  log('  role=tab（', r.tab.length, '）：');
  r.tab.forEach((t, i) => log(`    [${i}] ${JSON.stringify(t.rect)} «${t.文字}» sel=${t.ariaSelected} dstate=${t.dataState} ctl=${JSON.stringify(t.ariaControls)}`));
  log('  tabpanel（', r.tabpanel.length, '）：', JSON.stringify(r.tabpanel));
  log('  button（', r.button.length, '）：', JSON.stringify(r.button));
  log('  input（', r.input.length, '）：', JSON.stringify(r.input));
  log('  内部 testid：', JSON.stringify(r.内部testid));
  log('  内部 aria：', JSON.stringify(r.内部aria));
  log('  内部 role：', JSON.stringify(r.内部role));
  log('  表格元素：', r.表格);
  log('  同矩形元素（', r.同矩形.length, '）：', JSON.stringify(r.同矩形));
  log('  祖先链：', JSON.stringify(r.祖先链));
  log('  --- 有面积的树节点 ---');
  r.树.filter((n) => n.有面积).forEach((n) => log(`  ${'  '.repeat(n.d)}<${n.tag}> ${JSON.stringify(n.rect)} role=${n.role ?? '-'} tid=${n.tid ?? '-'} aria=${JSON.stringify(n.aria)} «${n.文字}»`));
};

// ---- ① 先读「生成历史」（批次 126 已有读数，这轮作为**对照基线**重读一遍） ----
out.开生成历史 = await openLauncher('生成历史');
log('\n=== ① 打开「生成历史」===\n  ', JSON.stringify(out.开生成历史));
out.生成历史 = await readPanel('生成历史');
show(out.生成历史, '① 生成历史面板');
save();
await p.screenshot({ path: new URL('00-gen-history.png', shotDir).pathname, clip: { x: 780, y: 40, width: 360, height: 250 } });

// 关掉
await p.keyboard.press('Escape'); await p.waitForTimeout(1200);
log('  Esc 后浮层：', JSON.stringify(await overlays()));

// ---- ② 再读「搜索」 ----
out.开搜索 = await openLauncher('搜索');
log('\n=== ② 打开「搜索」===\n  ', JSON.stringify(out.开搜索));
out.搜索 = await readPanel('搜索');
show(out.搜索, '② 搜索面板');
save();
await p.screenshot({ path: new URL('01-search.png', shotDir).pathname, clip: { x: 780, y: 40, width: 360, height: 250 } });
await p.screenshot({ path: new URL('01-search-full.png', shotDir).pathname });

// ---- ③ 结构对比：逐层比 tag 序列、矩形、testid、aria ----
if (!out.搜索.__err && !out.生成历史.__err) {
  const g = out.生成历史.树.filter((n) => n.有面积);
  const s = out.搜索.树.filter((n) => n.有面积);
  out.对比 = {
    本体矩形相同: JSON.stringify(out.生成历史.本体.rect) === JSON.stringify(out.搜索.本体.rect),
    矩形: { 生成历史: out.生成历史.本体.rect, 搜索: out.搜索.本体.rect },
    同testid: out.生成历史.本体.tid === out.搜索.本体.tid,
    testid: { 生成历史: out.生成历史.本体.tid, 搜索: out.搜索.本体.tid },
    同aria: out.生成历史.本体.aria === out.搜索.本体.aria,
    aria: { 生成历史: out.生成历史.本体.aria, 搜索: out.搜索.本体.aria },
    元素数: { 生成历史: g.length, 搜索: s.length },
    深度最大: { 生成历史: Math.max(...g.map((n) => n.d)), 搜索: Math.max(...s.map((n) => n.d)) },
    tag序列逐层: { 生成历史: g.map((n) => n.d + n.tag), 搜索: s.map((n) => n.d + n.tag) },
    testid序列: { 生成历史: g.map((n) => n.tid).filter(Boolean), 搜索: s.map((n) => n.tid).filter(Boolean) },
    aria序列: { 生成历史: g.map((n) => n.aria).filter(Boolean), 搜索: s.map((n) => n.aria).filter(Boolean) },
    tablist数: { 生成历史: out.生成历史.tablist.length, 搜索: out.搜索.tablist.length },
    tab数: { 生成历史: out.生成历史.tab.length, 搜索: out.搜索.tab.length },
    内部testid: { 生成历史: out.生成历史.内部testid, 搜索: out.搜索.内部testid },
    内部aria: { 生成历史: out.生成历史.内部aria, 搜索: out.搜索.内部aria },
  };
  out.对比.tag序列相同 = JSON.stringify(out.对比.tag序列逐层.生成历史) === JSON.stringify(out.对比.tag序列逐层.搜索);
  out.对比.矩形逐层相同 = JSON.stringify(g.map((n) => n.rect)) === JSON.stringify(s.map((n) => n.rect));
  out.对比.testid逐层相同 = JSON.stringify(out.对比.testid序列.生成历史) === JSON.stringify(out.对比.testid序列.搜索);
  log('\n=== ③ 两个面板的结构对比 ===');
  Object.entries(out.对比).forEach(([k, v]) => { if (typeof v !== 'object') log(`  ${k}：${v}`); });
  log('  逐层 tag（生成历史）：', JSON.stringify(out.对比.tag序列逐层.生成历史));
  log('  逐层 tag（搜索）　：', JSON.stringify(out.对比.tag序列逐层.搜索));
  log('  testid 序列（生成历史）：', JSON.stringify(out.对比.testid序列.生成历史));
  log('  testid 序列（搜索）　：', JSON.stringify(out.对比.testid序列.搜索));
  log('  aria 序列（生成历史）：', JSON.stringify(out.对比.aria序列.生成历史));
  log('  aria 序列（搜索）　：', JSON.stringify(out.对比.aria序列.搜索));
}
save();

out.收尾 = { 浮层: await overlays(), 选中: await sel(), zoom: await zoom(), credits: await credits(), status: await status() };
log('\n收尾（搜索面板仍开着）：', JSON.stringify(out.收尾));
save();
log('\nDONE a —— 搜索面板保持打开，交 b 轮');
process.exit(0);
