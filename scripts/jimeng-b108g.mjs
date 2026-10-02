// 批次 108 · g 轮：用**差分**读「背景色」色板（f 轮按「数量猜浮层」已被骗过一次）。
//
// f 轮已读到的组工具条（**有成员态**，与批次 50 的「四项」吻合）：
//   `node-toolbar` **`312×40@496,188`**
//     **解除编组 `88×32` ｜ 布局 `78×32` ｜ 背景色 `75×32` ｜ 下载 `32×32`**
//
// 🔴 f 轮的色板读数是废的：判据写「同一容器里有 ≥4 个等宽等高的小方块」，
//   结果 `hostCount = 221`，**整个 `body`、`.relative.h-screen`、顶栏全被选中**。
//   ⇒ **「按元素个数猜浮层」和「按面积猜浮层」是同一类错。**
//   本轮改用概念页早就写好的正解：**点击前后全页 DOM 签名差分**，
//   不带任何先验假设 —— 直接看多出来/少掉了什么。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => process.stdout.write(a.join(' ') + '\n');
const out = { at: new Date().toISOString() };
out.groupId = 'node_0ctj8mcr3m';
const G = out.groupId;
const save = () => writeFileSync(new URL('./_tmp-b108g.json', import.meta.url), JSON.stringify(out, null, 1));

const status = () => p.evaluate(() => { const t = document.body.innerText;
  return { nodes: (t.match(/(\d+) nodes?/) || [])[1], sel: (t.match(/(\d+) selected/) || [])[1],
    edges: (t.match(/(\d+) edges?/) || [])[1] }; });
const groupInfo = () => p.evaluate((i) => {
  const n = document.querySelector(`.react-flow__node[data-id="${i}"]`); if (!n) return { __err: 'gone' };
  return { sel: n.classList.contains('selected'), text: n.innerText.replace(/\s+/g, ' ').trim().slice(0, 120),
    members: (n.innerText.match(/(\d+) members/) || [])[1] || null,
    titleBox: (() => { const t = n.querySelector('[data-testid="group-title-chrome"]'); if (!t) return null;
      const r = t.getBoundingClientRect(); return { w: Math.round(r.width), h: Math.round(r.height), cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) }; })() };
}, G);

// 全页签名（只取「可能被浮层新增的」那些：可见、有尺寸、带标识）
const snapshot = () => p.evaluate(() => {
  const out = [];
  for (const e of document.querySelectorAll('body *')) {
    const r = e.getBoundingClientRect();
    if (r.width < 4 || r.height < 4) continue;
    if (r.x > innerWidth || r.y > innerHeight || r.x + r.width < 0 || r.y + r.height < 0) continue;
    const cs = getComputedStyle(e);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;
    out.push([e.tagName, e.getAttribute('data-testid') || '', e.getAttribute('aria-label') || '',
      (e.className || '').toString().slice(0, 50), Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height),
      (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 24)].join('|'));
  }
  return Array.from(new Set(out));
});

const diff = (a, b) => { const A = new Set(a), B = new Set(b);
  return { added: Array.from(B).filter((x) => !A.has(x)), removed: Array.from(A).filter((x) => !B.has(x)) }; };

// 确保组是选中态
let g = await groupInfo();
if (!g.sel && g.titleBox) {
  log('>>> 点标题区选中组', JSON.stringify(g.titleBox));
  await p.mouse.move(g.titleBox.cx, g.titleBox.cy); await p.waitForTimeout(450);
  await p.mouse.click(g.titleBox.cx, g.titleBox.cy); await p.waitForTimeout(1500);
  g = await groupInfo();
}
out.g = g;
log('\n组：', JSON.stringify(g));
log('状态行：', JSON.stringify(await status()));
if (!g.sel) { log('🔴 组没选中，停止'); save(); await b.close(); process.exit(1); }

// 找「背景色」钮
const bgBtn = await p.evaluate(() => {
  const bar = Array.from(document.querySelectorAll('[data-testid="node-toolbar"]'))
    .find((e) => { const r = e.getBoundingClientRect(); return r.width > 100 && r.y > 0 && r.y < 400 && getComputedStyle(e).visibility !== 'hidden'; });
  if (!bar) return null;
  const btn = Array.from(bar.querySelectorAll('button,[role=button]')).find((e) => /背景色/.test(e.innerText || ''));
  if (!btn) return { bar: bar.getAttribute('data-testid'), items: Array.from(bar.querySelectorAll('button,[role=button]')).map((e) => (e.innerText || '').trim() || e.getAttribute('aria-label')) };
  const r = btn.getBoundingClientRect();
  return { bar: bar.getAttribute('data-testid'), text: (btn.innerText || '').trim(),
    w: Math.round(r.width), h: Math.round(r.height), cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) };
});
out.bgBtn = bgBtn;
log('\n「背景色」钮：', JSON.stringify(bgBtn));
if (!bgBtn || bgBtn.cx === undefined) { log('🔴 找不到背景色钮'); save(); await b.close(); process.exit(1); }

out.before = (await snapshot()).length;
log('点击前签名数：', out.before);
await p.mouse.move(bgBtn.cx, bgBtn.cy); await p.waitForTimeout(550);
await p.mouse.click(bgBtn.cx, bgBtn.cy); await p.waitForTimeout(1600);
out.after = (await snapshot()).length;
log('点击后签名数：', out.after);

const d = diff(await snapshot(), []);   // 占位，下面用真正的两次快照
out.placeholder = true;

// ---- 真正的差分：关掉再开，拿两次快照 ----
await p.keyboard.press('Escape'); await p.waitForTimeout(1200);
const snapClosed = await snapshot();
await p.mouse.move(bgBtn.cx, bgBtn.cy); await p.waitForTimeout(500);
await p.mouse.click(bgBtn.cx, bgBtn.cy); await p.waitForTimeout(1800);
const snapOpen = await snapshot();
const dd = diff(snapClosed, snapOpen);
out.diff = dd;
log('\n差分：新增', dd.added.length, '条 / 减少', dd.removed.length, '条');
log('\n新增逐条：');
dd.added.slice(0, 60).forEach((x) => log('  +', x));
if (dd.removed.length) { log('\n减少逐条：'); dd.removed.slice(0, 20).forEach((x) => log('  -', x)); }
save();
