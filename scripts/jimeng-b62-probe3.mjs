// 批次 62 探测三：「收起」到底把抽屉变成了什么？—— 三态转换矩阵。
//
// 线索：`canvas-feature-sidecar` 全文档**只有一个**（不是选择器不唯一），
// 但它现在是 `200x348@1068,360`、`text` 与 `html` **都为空**。
// 而第四轮结束时它是 `400x696@868,12`、`aria="Agent"`、里面有完整的 `canvas-agent-panel`。
//
// 🔴 也就是说：**第四轮那次「点收起 ok:true」并没有关掉抽屉** ——
// 它把抽屉压成了 `200×348` 的一个空壳。我前三轮的 `drawerDump()` 用的是
// 几何启发式 `width >= 340 && width <= 460 && right >= innerWidth-12`，
// 200 宽不满足 ⇒ 被判成「已关闭」。
//
//    **「读数没变」既可能是产品没反应，也可能是我的尺子量错了量程。**
//    这正是批次 58 给质量门做阳性对照的同一个道理，只不过这次尺子在我脑子里。
//
// 本轮要把三态分清楚，并且回答手册里那句现在可疑的话：
//   「点击头部 收起 **关闭**抽屉」—— 到底是不是「关闭」？
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport, keyGuard } from './jimeng-safe-keys.mjs';

const SHOTS = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const OUT = new URL('./_tmp-b62-probe3.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);

const statusLine = () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const credit = () => p.evaluate(() => { const m = document.body.innerText.match(/(\d[\d,]*)\s*基础会员/); return m ? parseInt(m[1].replace(/,/g, ''), 10) : null; });
// 三态读数：分「不存在 / 收起空壳 / 展开」三档，判据用**内部结构**而不是几何宽度
const state = () => p.evaluate(() => {
  const e = document.querySelector('[data-testid="canvas-feature-sidecar"]');
  if (!e) return { st: 'ABSENT', sidecar: null };
  const r = e.getBoundingClientRect();
  const box = `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`;
  if (r.width < 1) return { st: 'ZERO-SIZE', sidecar: box };
  const panel = e.querySelector('[data-testid="canvas-agent-panel"]');
  const collapse = e.querySelector('[data-testid="canvas-agent-session-collapse"]');
  const composer = e.querySelector('[data-testid="canvas-agent-session-composer"]');
  const chips = e.querySelectorAll('[data-testid="canvas-agent-mode-action"]');
  const text = (e.innerText || '').replace(/\s+/g, ' ').trim();
  // 内部有多少可见元素
  const visKids = Array.from(e.querySelectorAll('*')).filter((x) => { const b = x.getBoundingClientRect(); return b.width > 1 && b.height > 1; }).length;
  const st = panel ? 'EXPANDED' : (visKids === 0 ? 'COLLAPSED-EMPTY' : 'COLLAPSED-OTHER');
  return { st, sidecar: box, aria: e.getAttribute('aria-label'),
    hasPanel: !!panel, hasCollapseBtn: !!collapse, hasComposer: !!composer, chipCount: chips.length,
    visKids, textLen: text.length, text: text.slice(0, 90),
    pe: getComputedStyle(e).pointerEvents, z: getComputedStyle(e).zIndex };
});
// 这个空壳盖住画布吗？拿别人的「视频 1」节点做被遮挡探测
const occlusion = () => p.evaluate(() => {
  const n = document.querySelector('.react-flow__node'); if (!n) return null;
  const r = n.getBoundingClientRect();
  const pts = [[0.5, 0.5], [0.2, 0.2], [0.8, 0.8], [0.5, 0.15]];
  return { node: n.getAttribute('aria-label'), box: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)}`,
    hits: pts.map(([fx, fy]) => { const x = Math.round(r.x + r.width * fx), y = Math.round(r.y + r.height * fy);
      const t = document.elementFromPoint(x, y); if (!t) return `(${x},${y}) null`;
      const sc = t.closest('[data-testid="canvas-feature-sidecar"]');
      return `(${x},${y}) ${t.tagName}${sc ? ' <<< 被侧栏盖住' : ''}`; }) };
});
const openBtn = () => p.evaluate(() => { const e = Array.from(document.querySelectorAll('button'))
    .find((x) => /与\s*AI\s*对话/.test(x.getAttribute('aria-label') || '')); if (!e) return null; const r = e.getBoundingClientRect();
  return { cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2), box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` }; });
const clickCollapse = () => p.evaluate(() => { const e = document.querySelector('[data-testid="canvas-agent-session-collapse"]');
  if (!e || e.getBoundingClientRect().width < 1) return 'no-collapse-btn';
  const r = e.getBoundingClientRect();
  const o = (document.elementFromPoint(Math.round(r.x + r.width / 2), Math.round(r.y + r.height / 2)) || {}).closest?.('button');
  if (!o || o !== e) return 'occluded';
  e.click(); return 'clicked'; });

const out = { startedAt: new Date().toISOString(), steps: [] };
const rec = async (label) => { const s = await state(); const o = await occlusion(); const c = await credit();
  console.log(`\n--- ${label} ---`);
  console.log('  侧栏:', JSON.stringify(s));
  if (o) console.log('  被遮挡探测:', o.node, o.box, '\n    ' + o.hits.join('\n    '));
  console.log('  积分:', c);
  out.steps.push({ label, state: s, occlusion: o, credit: c }); return s; };

console.log('=== 批次 62 探测三：「收起」不是「关闭」？三态矩阵 ===');
console.log('起点:', await statusLine(), '| 积分', await credit());
console.log('「与 AI 对话」按钮:', JSON.stringify(await openBtn()));
await rec('S0 · 继承第四轮结束态（点过「收起」之后）');

// 1. 空壳状态点「与 AI 对话」按钮 → 应该重新展开
const ob = await openBtn();
if (ob) { await p.mouse.click(ob.cx, ob.cy); await p.waitForTimeout(1500); await rec('S1 · 空壳态点「与 AI 对话」'); }

// 2. 展开态点「收起」→ 落到哪一态
console.log('\n  点收起 =', await clickCollapse());
await p.waitForTimeout(1500);
const s2 = await rec('S2 · 展开态点「收起」');

// 3. 收起空壳态按 Esc / ⌘/ → 真关闭？
const g = await keyGuard(p);
console.log('\n  keyGuard:', g.reason);
if (g.safe) {
  await p.keyboard.press('Meta+Slash');
  await p.waitForTimeout(1400);
  await rec('S3 · 收起空壳态按 ⌘/');
  // 再按一次 ⌘/ 应该重新打开
  const g2 = await keyGuard(p);
  if (g2.safe) { await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1400); await rec('S4 · 再按 ⌘/'); }
  const g3 = await keyGuard(p);
  if (g3.safe) { await p.keyboard.press('Meta+Slash'); await p.waitForTimeout(1400); await rec('S5 · 再按 ⌘/（第三次）'); }
}

// 4. 空壳上截图
const cur = await state();
if (cur.st === 'COLLAPSED-EMPTY' || cur.st === 'COLLAPSED-OTHER') {
  await p.screenshot({ path: new URL('62-agent-collapsed-shell.png', SHOTS).pathname, clip: { x: 1020, y: 330, width: 260, height: 380 } });
  console.log('\n  📷 62-agent-collapsed-shell.png（收起空壳）');
}
// 展开态补一张全抽屉图
if ((await state()).st === 'EXPANDED') {
  await p.screenshot({ path: new URL('62-agent-expanded.png', SHOTS).pathname, clip: { x: 860, y: 8, width: 412, height: 700 } });
  console.log('  📷 62-agent-expanded.png（展开态）');
}

// 收尾：确保抽屉完全不在 DOM
let guard = 0;
while ((await state()).st !== 'ABSENT' && guard++ < 6) {
  const cc = await clickCollapse();
  if (cc !== 'clicked') { const ob2 = await openBtn(); if (ob2) { await p.mouse.click(ob2.cx, ob2.cy); await p.waitForTimeout(1300); continue; } break; }
  await p.waitForTimeout(1100);
}
console.log('\n收尾后侧栏:', JSON.stringify(await state()));
console.log('终态:', await statusLine(), '| 积分', await credit());
out.end = { status: await statusLine(), credit: await credit(), state: await state() };
writeFileSync(OUT, JSON.stringify(out, null, 1));
console.log('写入', OUT.pathname);
await b.close();
