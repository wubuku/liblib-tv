// 批次 62 探测二：画布上到底有几个 `canvas-feature-sidecar`？
//
// 第五轮全场读数是 `200x348@1068,360` —— 那是**别的侧栏**，不是 Agent 抽屉
// （Agent 抽屉实测是 `400x696@868,12`、aria 逐字 `Agent`）。
// 原因：`document.querySelector('[data-testid="canvas-feature-sidecar"]')` **取第一个**，
// 而这个 testid **不是唯一的**。
//
// 🔑 同一个坑的第四次现身，但这次**长在选择器上**：
//   批次 50–55  读数对象认错 → 批次 61 落点归属没断言 → 批次 62 第三轮 兄弟层当祖先断言
//   → 现在：**testid 以为唯一，实际不唯一**。
//   教训统一成一句：**选择器要能证明自己唯一，不能假设。**
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const OUT = new URL('./_tmp-b62-probe2.json', import.meta.url);
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
if (!p) { console.error('ABORT: 找不到画布页面'); process.exit(1); }
await pinViewport(p);

const info = await p.evaluate(() => {
  const all = Array.from(document.querySelectorAll('[data-testid="canvas-feature-sidecar"]')).map((e) => {
    const r = e.getBoundingClientRect();
    return { aria: e.getAttribute('aria-label'), role: e.getAttribute('role'),
      box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`,
      vis: r.width > 1, cls: String(e.className || '').slice(0, 60),
      text: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120),
      html: (e.innerHTML || '').slice(0, 160) }; });
  return { count: all.length, all,
    agentQualified: Array.from(document.querySelectorAll('[data-testid="canvas-feature-sidecar"][aria-label="Agent"]')).map((e) => {
      const r = e.getBoundingClientRect(); return `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`; }),
    otherTestids: Array.from(document.querySelectorAll('[data-testid*="sidecar"]')).map((e) => { const r = e.getBoundingClientRect();
      return { tid: e.getAttribute('data-testid'), aria: e.getAttribute('aria-label'), box: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}`, vis: r.width > 1 }; }) };
});
console.log('=== canvas-feature-sidecar 数量 =', info.count, '===');
for (const a of info.all) { console.log(`  aria=${JSON.stringify(a.aria)} role=${a.role} box=${a.box} 可见=${a.vis}`); console.log(`    cls=${a.cls}`); console.log(`    text=${a.text}`); console.log(`    html=${a.html}`); }
console.log('\n=== 带 aria="Agent" 限定后 ===', JSON.stringify(info.agentQualified));
console.log('\n=== 所有含 "sidecar" 的 testid ===');
for (const t of info.otherTestids) console.log(`  ${t.tid} aria=${JSON.stringify(t.aria)} box=${t.box} 可见=${t.vis}`);
writeFileSync(OUT, JSON.stringify(info, null, 1));
console.log('\n写入', OUT.pathname);
await b.close();
