// 批次 108 · f 轮：读「有成员」与「0 成员」两态的组工具条与背景色色板。
//
// e 轮的三条读数（都很有用）：
//   · 组 aria 逐字 **`组 node: 编组 1`**；
//     正文/可访问文本逐字 **`编组 1 Group 编组 1, 2 members. Selected.`**
//     ⇒ **组自带「成员数」读数**（`N members.`），这比「数一数里面有几个节点」可靠
//   · 组矩形 **`312×336@496,264`**，testid 八个：
//     `group-flow-node` / `group-background` / `group-body-frame` / `group-resize-outline`
//     / `group-title-hit-area` / `group-title-chrome` / `group-title-tag-chrome`
//     / `flow-node-selected-tag`
//   · 🔴 **成员节点不是组的 DOM 后代**（`querySelectorAll('.react-flow__node')` 返回 `[]`）
//     ⇒ **不能用「组里有几个 .react-flow__node」来数成员**。
//
// e 轮还犯了一个操作错：组**本来已经是选中态**（⌘G 之后），
// 我又点了它的**卡片中央** ⇒ 点在 `group-background` 上 ⇒ **把选中点没了**，
// 于是组工具条当然读不到。
// ⇒ 本轮：**已选中就读，不多点**；要点就点**标题区**（`group-title-chrome`），
//    不点卡片中央。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), mine: ['node_d6cn9z91w6', 'node_8vwsfmqc24'] };
const [A, C] = out.mine;
out.groupId = 'node_0ctj8mcr3m';
const G = out.groupId;
const save = () => writeFileSync(new URL('./_tmp-b108f.json', import.meta.url), JSON.stringify(out, null, 1));

const status = () => p.evaluate(() => { const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    edges: (t.match(/(\d+) edges?/) || [])[1] }; });
const safeEval = async (fn, arg, tries = 8) => {
  for (let k = 0; k < tries; k++) { const r = await p.evaluate(fn, arg); if (!r || !r.__err) return r; await p.waitForTimeout(700); }
  return { __err: 'gave-up' }; };

// 组的可访问文本（含 `N members.`）与选中态
const groupInfo = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  const r = n.getBoundingClientRect();
  const title = n.querySelector('[data-testid="group-title-chrome"]') || n.querySelector('[data-testid="group-title-hit-area"]');
  const tr = title ? title.getBoundingClientRect() : null;
  return { aria: n.getAttribute('aria-label'), text: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 200),
    rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
    members: (n.innerText.match(/(\d+) members/) || [])[1] || null,
    sel: n.classList.contains('selected'),
    titleBox: tr ? { tid: title.getAttribute('data-testid'), w: Math.round(tr.width), h: Math.round(tr.height),
      x: Math.round(tr.x), y: Math.round(tr.y), cx: Math.round(tr.x + tr.width / 2), cy: Math.round(tr.y + tr.height / 2) } : null };
}, G);

const readBars = async (tag) => {
  const bars = await p.evaluate(() => Array.from(document.querySelectorAll('[data-testid]'))
    .filter((e) => /toolbar/i.test(e.getAttribute('data-testid') || ''))
    .map((e) => { const q = e.getBoundingClientRect();
      return { tid: e.getAttribute('data-testid'), w: Math.round(q.width), h: Math.round(q.height),
        x: Math.round(q.x), y: Math.round(q.y), vis: getComputedStyle(e).visibility,
        items: Array.from(e.querySelectorAll('button,[role=button]')).map((x) => {
          const r = x.getBoundingClientRect();
          return { a: x.getAttribute('aria-label'), t: (x.innerText || '').trim(), w: Math.round(r.width), h: Math.round(r.height),
            cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }) }; })
    .filter((x) => x.vis !== 'hidden' && x.items.length));
  out[tag] = bars;
  log(`\n──── ${tag} ────`);
  for (const x of bars) log(`  ${x.tid} ${x.w}×${x.h}@${x.x},${x.y}：`, JSON.stringify(x.items.map((i) => i.a || i.t)));
  save();
  return bars;
};

// 色板：取「浮层里一排小圆点」——按「同一容器里有 ≥4 个等宽等高的小方块」定位
const readPalette = () => p.evaluate(() => {
  const isSw = (e) => { const r = e.getBoundingClientRect();
    return r.width >= 8 && r.width <= 44 && Math.abs(r.width - r.height) <= 1; };
  const hosts = Array.from(document.querySelectorAll('div')).filter((e) => {
    if (getComputedStyle(e).visibility === 'hidden') return false;
    const kids = Array.from(e.querySelectorAll('*')).filter(isSw);
    return kids.length >= 4; });
  return { hostCount: hosts.length, hosts: hosts.slice(0, 3).map((h) => {
    const q = h.getBoundingClientRect(); const cs = getComputedStyle(h);
    return { cls: (h.className || '').toString().slice(0, 46), w: Math.round(q.width), h: Math.round(q.height),
      x: Math.round(q.x), y: Math.round(q.y), bg: cs.backgroundColor,
      swatches: Array.from(h.querySelectorAll('*')).filter(isSw).slice(0, 12).map((x) => {
        const r = x.getBoundingClientRect(); const c2 = getComputedStyle(x);
        return { tag: x.tagName, tid: x.getAttribute('data-testid'), a: x.getAttribute('aria-label'),
          t: (x.innerText || '').trim().slice(0, 10), w: Math.round(r.width), h: Math.round(r.height),
          bg: c2.backgroundColor, border: c2.borderColor, br: c2.borderRadius,
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; }) }; }) };
});

async function ensureSelected() {
  const g0 = await groupInfo();
  if (g0.sel) { log('  组已是选中态，**不多点**'); return g0; }
  if (!g0.titleBox) { log('  🔴 没有标题区可点'); return g0; }
  const t = g0.titleBox;
  log('  点标题区', JSON.stringify(t));
  await p.mouse.move(t.cx, t.cy); await p.waitForTimeout(450);
  await p.mouse.click(t.cx, t.cy); await p.waitForTimeout(1500);
  return groupInfo();
}

// ================= A 态：有成员 =================
log('\n===== A 态：2 个成员 =====');
out.gA = await ensureSelected();
out.statusA = await status();
log('组：', JSON.stringify(out.gA));
log('状态行：', JSON.stringify(out.statusA));
out.barsA = await readBars('barsA-有成员');
const barA = (out.barsA || []).find((x) => x.items.some((i) => /背景色/.test(i.a || i.t)));
out.barA = barA || null;
log('\n含「背景色」的条：', JSON.stringify(barA && barA.items.map((i) => ({ a: i.a, t: i.t, w: i.w, h: i.h }))));
if (barA) {
  const bg = barA.items.find((i) => /背景色/.test(i.a || i.t));
  log('\n>>> 点「背景色」', JSON.stringify(bg));
  await p.mouse.move(bg.cx, bg.cy); await p.waitForTimeout(500);
  await p.mouse.click(bg.cx, bg.cy); await p.waitForTimeout(1500);
  out.paletteA = await readPalette();
  out.paletteA.raw = null;
  log('色板读数：', JSON.stringify(out.paletteA, null, 1));
  save();
}
await p.keyboard.press('Escape'); await p.waitForTimeout(900);
log('（Esc 收掉色板）');
save();
