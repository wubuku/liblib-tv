// 批次 108 · j 轮：**有成员 vs 0 成员**两态的组工具条与背景色色板并排读。
//
// 先把 i 轮拿到的东西钉住（都是本轮新读数，**手册里没有**）：
//   · 组 aria 逐字 **`组 node: 编组 1`**；可访问文本
//     **`编组 1 Group 编组 1, 2 members. Selected.`** ⇒ **组自带成员计数 `N members.`**
//   · 组矩形 **`312×336@496,264`**；八个 testid：`group-flow-node` / `group-background`
//     / `group-body-frame` / `group-resize-outline` / `group-title-hit-area`
//     / `group-title-chrome` / `group-title-tag-chrome` / `flow-node-selected-tag`
//   · 组工具条 `node-toolbar` **`312×40@496,188`**：
//     **解除编组 `88×32` ｜ 布局 `78×32` ｜ 背景色 `75×32` ｜ 下载 `32×32`**
//   · 色板宿主 **`[data-testid="selection-context-toolbar-popup-host"]`（class
//     `react-flow__node-toolbar`）** —— 🔴 **它的盒子是 `0×0`**，
//     所以任何「按尺寸找浮层」的判据都找不到它；只能**按 testid**。
//     内部 `absolute top-[calc(100%+8px)] flex items-center` 也是 `0×0`。
//   · 色板 **6 枚**，每枚 `SPAN.pointer-events-none.block.size-canvas-color-choice-swatch…`
//     **`18×18`**、`border-radius: 4px`、`border: 1px solid rgba(255,255,255,0.1)`，
//     x 间距 **34px**，每枚各带一个 `sr-only` 标签。
//
// 🔴 i 轮的教训（第三次同族错误）：我用「正方形 + 圆角≥50% + 有背景色」找色块，
//   而色板是 **`18×18` 但圆角只有 `4px`** ⇒ 全被滤掉，读数「新增 0 / 减少 0」。
//   **截图是地面真相**：面板就在「背景色」按钮正下方，肉眼一眼可见。
//   ⇒ **「过滤条件把目标滤掉了」与「目标不存在」，在读数上长得一模一样。**
//   第三步（截图）救回了这一轮。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString() };
out.groupId = 'node_0ctj8mcr3m';
out.mine = ['node_d6cn9z91w6', 'node_8vwsfmqc24'];
const G = out.groupId;
const save = () => writeFileSync(new URL('./_tmp-b108j.json', import.meta.url), JSON.stringify(out, null, 1));

const status = () => p.evaluate(() => { const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1] }; });
const groupInfo = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  const t = n.querySelector('[data-testid="group-title-chrome"]');
  const tr = t ? t.getBoundingClientRect() : null;
  return { sel: n.classList.contains('selected'), members: (n.innerText.match(/(\d+) members/) || [])[1] || null,
    text: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 110),
    title: tr ? { cx: Math.round(tr.x + tr.width / 2), cy: Math.round(tr.y + tr.height / 2) } : null };
}, G);
const readBar = () => p.evaluate(() => {
  const bar = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
    .find((e) => { const r = e.getBoundingClientRect(); return r.width > 100 && r.y > 0 && r.y < 400 && getComputedStyle(e).visibility !== 'hidden'; });
  if (!bar) return null;
  const r = bar.getBoundingClientRect();
  return { w: Math.round(r.width), h: Math.round(r.height), x: Math.round(r.x), y: Math.round(r.y),
    items: Array.from(bar.querySelectorAll('button,[role=button]')).map((e) => { const q = e.getBoundingClientRect();
      return { t: (e.innerText || '').trim(), a: e.getAttribute('aria-label'), w: Math.round(q.width), h: Math.round(q.height),
        cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2) }; }) };
});
// 色板：按 testid 定位，不猜尺寸
const readPalette = () => p.evaluate(() => {
  const host = document.querySelector('[data-testid="selection-context-toolbar-popup-host"]');
  if (!host) return { found: false };
  const hr = host.getBoundingClientRect();
  const inner = host.querySelector('.absolute');
  const ir = inner ? inner.getBoundingClientRect() : null;
  const sw = Array.from(host.querySelectorAll('.size-canvas-color-choice-swatch, [class*=color-choice-swatch]'))
    .map((e) => { const q = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      // 找它旁边的 sr-only 标签
      let label = null;
      let n = e.parentElement;
      for (let k = 0; k < 3 && n && !label; k++, n = n.parentElement) {
        const s = n.querySelector('.sr-only'); if (s && s !== e) label = (s.innerText || '').trim();
      }
      return { tag: e.tagName, label, w: Math.round(q.width), h: Math.round(q.height),
        x: Math.round(q.x), y: Math.round(q.y), bg: cs.backgroundColor, br: cs.borderRadius,
        bdr: cs.borderColor, bw: cs.borderWidth, cx: Math.round(q.x + q.width / 2), cy: Math.round(q.y + q.height / 2) }; });
  return { found: true, hostBox: `${Math.round(hr.x)},${Math.round(hr.y)} ${Math.round(hr.width)}×${Math.round(hr.height)}`,
    hostText: (host.innerText || '').replace(/\s+/g, ' ').trim(),
    innerBox: ir ? `${Math.round(ir.x)},${Math.round(ir.y)} ${Math.round(ir.width)}×${Math.round(ir.height)}` : null,
    n: sw.length, swatches: sw };
});

async function ensureGroupSelected() {
  let g = await groupInfo();
  if (!g.sel && g.title) {
    await p.mouse.move(g.title.cx, g.title.cy); await p.waitForTimeout(550);
    await p.mouse.click(g.title.cx, g.title.cy); await p.waitForTimeout(1600);
    g = await groupInfo();
  }
  return g;
}

// ================= A 态：2 个成员 =================
log('\n########## A 态：2 个成员 ##########');
let g = await ensureGroupSelected();
out.gA = g;
out.statusA0 = await status();
log('组：', JSON.stringify(g), '状态行：', JSON.stringify(out.statusA0));
out.barA = await readBar();
log('工具条：', JSON.stringify(out.barA));
let bg = out.barA && out.barA.items.find((i) => /背景色/.test(i.t));
if (bg) {
  await p.mouse.move(bg.cx, bg.cy); await p.waitForTimeout(600);
  await p.mouse.click(bg.cx, bg.cy); await p.waitForTimeout(2000);
}
out.paletteA = await readPalette();
log('色板 A：', JSON.stringify(out.paletteA, null, 1));
await p.screenshot({ path: '/tmp/b108-j-A-两成员色板.png', clip: { x: 430, y: 150, width: 560, height: 400 } });
await p.keyboard.press('Escape'); await p.waitForTimeout(1000);
save();

// ================= 逐个删成员 → 0 成员 =================
for (const [idx, id] of out.mine.entries()) {
  log(`\n>>> 删成员 ${idx + 1}：${id}`);
  // 取消组选中，避免浮层挡路
  await p.mouse.click(8, 300); await p.waitForTimeout(1200);
  const spot = await p.evaluate((i) => {
    const n = document.querySelector(`.react-flow__node[data-id="${i}"]`);
    if (!n) return { __err: 'gone' };
    const r = n.getBoundingClientRect(); const c = [];
    for (let y = Math.ceil(r.y) + 2; y < r.y + r.height - 2; y += 4)
      for (let x = Math.ceil(r.x) + 2; x < r.x + r.width - 2; x += 4) {
        if (x < 2 || y < 2 || x > innerWidth - 2 || y > innerHeight - 2) continue;
        const el = document.elementFromPoint(x, y);
        if (el && (el === n || n.contains(el))) c.push({ x, y });
      }
    return { total: c.length, sample: c.slice(0, 4) };
  }, id);
  log('  落点：', JSON.stringify({ total: spot.total }));
  if (!spot.total) { log('  🔴 无落点，停止'); save(); await b.close(); process.exit(1); }
  const pt = spot.sample[Math.floor(spot.sample.length / 2)];
  await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(500);
  await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(1500);
  const selNow = await p.evaluate((i) => { const e = document.querySelector(`.react-flow__node[data-id="${i}"]`); return e ? e.classList.contains('selected') : null; }, id);
  log('  点击后 selected =', selNow);
  if (!selNow) { log('  🔴 没选中，停止'); save(); await b.close(); process.exit(1); }
  // 右键 → 删除
  await p.mouse.move(pt.x, pt.y); await p.waitForTimeout(450);
  await p.mouse.down({ button: 'right' }); await p.waitForTimeout(300); await p.mouse.up({ button: 'right' });
  await p.waitForTimeout(1300);
  const del = await p.evaluate(() => {
    const m = Array.from(document.querySelectorAll('div,ul,section')).find((x) => { const q = x.getBoundingClientRect();
      return q.width > 60 && q.width < 600 && q.height > 60 && getComputedStyle(x).visibility !== 'hidden'
        && (x.innerText || '').replace(/\s+/g, ' ').trim().startsWith('复制 ⌘ C'); });
    if (!m) return null;
    const btn = Array.from(m.querySelectorAll('button,[role=menuitem]')).find((e) => /^删除/.test(e.innerText.trim()));
    if (!btn) return null;
    const q = btn.getBoundingClientRect();
    return { x: Math.round(q.x + q.width / 2), y: Math.round(q.y + q.height / 2) };
  });
  log('  删除项：', JSON.stringify(del));
  if (!del) { log('  🔴 菜单里没有删除项，停止'); save(); await b.close(); process.exit(1); }
  await p.mouse.move(del.x, del.y); await p.waitForTimeout(400);
  await p.mouse.click(del.x, del.y); await p.waitForTimeout(2000);
  out['afterDel' + idx] = await status();
  const stillThere = await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), id);
  log('  该成员还在吗 =', stillThere, '｜状态行', JSON.stringify(out['afterDel' + idx]));
  g = await groupInfo();
  log('  组现在：', JSON.stringify(g));
  save();
  if (!stillThere) break;
}

// ================= B 态：0 个成员 =================
log('\n########## B 态：0 个成员 ##########');
g = await ensureGroupSelected();
out.gB = g;
out.statusB0 = await status();
log('组：', JSON.stringify(g), '状态行：', JSON.stringify(out.statusB0));
out.barB = await readBar();
log('工具条 B：', JSON.stringify(out.barB));
bg = out.barB && out.barB.items.find((i) => /背景色/.test(i.t));
out.bgBtnB = bg || null;
if (bg) {
  await p.mouse.move(bg.cx, bg.cy); await p.waitForTimeout(600);
  await p.mouse.click(bg.cx, bg.cy); await p.waitForTimeout(2000);
}
out.paletteB = await readPalette();
log('色板 B：', JSON.stringify(out.paletteB, null, 1));
await p.screenshot({ path: '/tmp/b108-j-B-零成员色板.png', clip: { x: 430, y: 150, width: 560, height: 400 } });
await p.keyboard.press('Escape'); await p.waitForTimeout(1000);

// ================= 对账 =================
const sig = (x) => x && x.found ? x.swatches.map((s) => `${s.label}|${s.bg}|${s.w}x${s.h}|${s.br}`).join(' ; ') : '(没找到色板)';
log('\n════ 对账 ════');
log('A（2 成员）工具条项：', JSON.stringify((out.barA && out.barA.items || []).map((i) => i.t || i.a)));
log('B（0 成员）工具条项：', JSON.stringify((out.barB && out.barB.items || []).map((i) => i.t || i.a)));
log('A 色板：', sig(out.paletteA));
log('B 色板：', sig(out.paletteB));
out.same = sig(out.paletteA) === sig(out.paletteB);
log('两态色板逐字相同 =', out.same ? '✅' : '🔴 不同');
save();
log('\n已落盘');
await b.close();
