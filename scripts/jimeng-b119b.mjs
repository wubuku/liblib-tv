// 批次 119 · b 轮：读全**时间线节点内部**的 `timeline-toolbar`，并订正 a 轮的错误假设。
//
// 🔴 a 轮假设被证伪：
//   a 轮以为「时间线节点带浮动工具条」，实际那行 `00:00 / 00:00 全屏编辑`
//   和刻度 `00:00 / 00:05 / … / 00:30` **在节点内部**（testid **`timeline-toolbar`**），
//   按「归属于本节点且在节点上方」筛时**归属本节点的工具条 = 0 个**。
//
// 🔑 顺带订正**批次 118 的一处解释**（结论不变，理由要改）：
//   批次 118 b 轮按 `[class*="node-toolbar"]` 宽泛扫，命中 18 个「00:00 / 00:00 全屏编辑」
//   ＋ `导出时间线` / `全屏编辑`，当时写成「两个**时间线节点**各带一套**浮动**工具条」。
//   实际那是**时间线节点内部的工具条**（class 里含 "node-toolbar" 子串才被宽泛扫命中）。
//   ⇒ **批次 118 的结论「主体节点没有浮动工具条」不受影响** ——
//     那个结论用的是**精确 class `.react-flow__node-toolbar`**（主体 0 / 文本 1），
//     精确 class 才是浮动工具条的判据；宽泛扫是另一个东西。
//   ⇒ 本批要记的是：**「宽泛 class 扫」会把「节点内部工具条」和「浮动工具条」混在一起**，
//     判浮动工具条必须用精确 class 或 testid + 位置归属。
//
// ⛔ 只读不点：`导出时间线`（对外产出，未授权）、`全屏编辑`（未单独授权）、
//    `静音`、任何播放/导出类按钮，本轮**一个都不点**。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const SELF = process.env.SELF_ID;
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString(), round: 'b', self: SELF };
const save = () => writeFileSync(new URL('./_tmp-b119b.json', import.meta.url), JSON.stringify(out, null, 1));

const credits = () => p.evaluate(() => (document.querySelector('[data-testid="canvas-commerce-entry"]') || { getAttribute: () => null }).getAttribute('aria-label'));
const nodeN = () => p.evaluate(() => (document.body.innerText.match(/(\d+) nodes?/) || [])[1]);
const zoom = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-zoom-percent"]'); return e ? e.getAttribute('aria-label') : null; });

out.nodeExists = await p.evaluate((i) => !!document.querySelector(`.react-flow__node[data-id="${i}"]`), SELF);
log('节点存在？', out.nodeExists);
if (!out.nodeExists) { log('⛔ 中止'); await b.close(); process.exit(3); }
out.zoom0 = await zoom(); log('缩放：', out.zoom0, '｜积分：', await credits());

// ---- 逐个 testid 读全：位置、class、按钮、文字 ----
out.parts = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  const r = (e) => { const q = e.getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; };
  const map = {};
  for (const e of n.querySelectorAll('[data-testid]')) { const t = e.getAttribute('data-testid');
    (map[t] = map[t] || []).push({ rect: r(e), cls: (e.getAttribute('class') || '').toString().slice(0, 46),
      text: (e.innerText || e.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 90),
      svgs: e.querySelectorAll('svg').length,
      btns: Array.from(e.querySelectorAll('button,[role=button]')).map((x) => ({ aria: x.getAttribute('aria-label'), rect: r(x) })).filter((y) => y.aria) }); }
  return { at: Date.now(), nodeRect: r(n), inner: (n.innerText || '').replace(/\s+/g, ' ').trim(),
    allAria: Array.from(new Set(Array.from(n.querySelectorAll('[aria-label]')).map((e) => e.getAttribute('aria-label')))),
    allBtns: Array.from(n.querySelectorAll('button,[role=button]')).map((e) => ({ aria: e.getAttribute('aria-label'), rect: r(e) })).filter((x) => x.aria),
    byTid: map };
}, SELF);

log('\n=== 节点整体 ===');
log('屏上矩形：', JSON.stringify(out.parts.nodeRect));
log('innerText 逐字：', JSON.stringify(out.parts.inner));
log('\n节点里全部 aria 逐字（' + out.parts.allAria.length + '）：', JSON.stringify(out.parts.allAria));
log('\n节点里全部按钮（' + out.parts.allBtns.length + '）：');
out.parts.allBtns.forEach((x) => log(`   ${JSON.stringify(x.aria)} ${JSON.stringify(x.rect)}`));
log('\n逐 testid：');
for (const [t, arr] of Object.entries(out.parts.byTid)) {
  arr.forEach((d) => log(`   ${t.padEnd(38)} ${JSON.stringify(d.rect)}｜svg ${d.svgs}｜文字 ${JSON.stringify(d.text)}｜按钮 ${JSON.stringify(d.btns.map((x) => x.aria))}`));
}
save();

// ---- 精确 class 对照：浮动 vs 内部 ----
out.hostScan = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const nr = n.getBoundingClientRect();
  const info = (e) => { const q = e.getBoundingClientRect();
    return { tid: e.getAttribute('data-testid'), cls: (e.getAttribute('class') || '').toString().slice(0, 46),
      rect: [q.x, q.y, q.width, q.height].map(Math.round),
      在节点内: n.contains(e), 零高度: q.height === 0,
      水平重叠节点: q.right > nr.left && q.left < nr.right, 在节点上方: q.bottom <= nr.top + 60 }; };
  return {
    '精确 .react-flow__node-toolbar': Array.from(document.querySelectorAll('.react-flow__node-toolbar')).map(info),
    '精确 [data-testid=node-toolbar]': Array.from(document.querySelectorAll('[data-testid="node-toolbar"]')).map(info),
    '宽泛 [class*="node-toolbar"]': Array.from(document.querySelectorAll('[class*="node-toolbar"]')).map(info),
    '本节点内 [class*="node-toolbar"]': Array.from(n.querySelectorAll('[class*="node-toolbar"]')).map(info),
  };
}, SELF);
log('\n=== 宿主对照（精确 vs 宽泛）===');
for (const [k, v] of Object.entries(out.hostScan)) {
  log(`  ${k}：${v.length} 个`);
  v.forEach((d) => log(`      ${JSON.stringify(d)}`));
}
save();

// ---- 刻度读数：逐字 + 位置 + testid ----
out.ruler = await p.evaluate((i) => { const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return null;
  const r = (e) => { const q = e.getBoundingClientRect(); return [Math.round(q.x), Math.round(q.y), Math.round(q.width), Math.round(q.height)]; };
  const ruler = n.querySelector('[data-testid="timeline-ruler"]');
  if (!ruler) return { __err: 'no-ruler' };
  const items = Array.from(ruler.querySelectorAll('*')).filter((e) => /^\d{2}:\d{2}$/.test((e.textContent || '').trim()) && e.getBoundingClientRect().width > 1)
    .map((e) => ({ t: e.textContent.trim(), tag: e.tagName, tid: e.getAttribute('data-testid'), cls: (e.getAttribute('class') || '').toString().slice(0, 30), rect: r(e) }));
  const rr = ruler.getBoundingClientRect();
  // 刻度 x 间距（批次 111 用它判「时间线没有自己的缩放」）
  const xs = items.map((x) => x.rect[0]).sort((a, b) => a - b);
  const gaps = []; for (let k = 1; k < xs.length; k++) gaps.push(Math.round((xs[k] - xs[k - 1]) * 10) / 10);
  return { rulerRect: r(ruler), rulerText: (ruler.innerText || '').replace(/\s+/g, ' ').trim(), items, gaps,
    ext: n.querySelector('[data-testid="timeline-ruler-interaction-extension"]') ? r(n.querySelector('[data-testid="timeline-ruler-interaction-extension"]')) : null };
}, SELF);
log('\n=== 刻度 ===');
if (out.ruler.__err) log('  ', out.ruler.__err);
else {
  log('  ruler 矩形：', JSON.stringify(out.ruler.rulerRect), '｜interaction-extension：', JSON.stringify(out.ruler.ext));
  out.ruler.items.forEach((x) => log(`    ${JSON.stringify(x)}`));
  log('  刻度 x 间距：', JSON.stringify(out.ruler.gaps));
}
out.end = { nodes: await nodeN(), credits: await credits() };
log('\n终点：', JSON.stringify(out.end));
save();
log('\nDONE b');
process.exit(0);
