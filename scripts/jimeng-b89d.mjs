// 批次 89 · D：`flow-node-selected-tag` 到底有几种尺寸、按什么分。
//
// c 轮 P3 续查的输出里有一行非常刺眼：
//   ⚠️ [flow-node-selected-tag] 同结构多尺寸：28×28×4 ｜ 29×29×7 ｜ 24×24×9
//   **三组的 aria 全是 `Add tags`**，testid 与 class 也完全相同。
//
// ⇒ 手册里记着的是「`Add tags` **24×24**」（批次 28、批次 88 都这么写）。
//    若同一 testid/class/aria 的元素有**三种尺寸**，
//    那么「24×24」就不是契约 —— **拿尺寸当身份会认错人**。
//
// 可证伪预测 **P1d**：三种尺寸**按节点类型分配**（或按某个状态），
//   而不是随机分布。⇒ 逐节点打表：节点名 / aria 前缀 / class 里的类型段 / tag 尺寸。
import { chromium } from 'playwright';
import { writeFileSync } from 'node:fs';
import { pinViewport } from './jimeng-safe-keys.mjs';

const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
await pinViewport(p);
const log = (...a) => console.log(a.join(' '));
const out = { at: new Date().toISOString() };
const status = async () => p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0]);
const selCount = async () => p.evaluate(() => (document.body.innerText.match(/(\d+) selected/) || [])[1]);
out.start = { status: await status(), sel: await selCount() };

out.tags = await p.evaluate(() => {
  const rows = [];
  for (const n of document.querySelectorAll('.react-flow__node')) {
    const id = n.getAttribute('data-id');
    const aria = n.getAttribute('aria-label') || '';
    const typeCls = (String(n.className || '').match(/react-flow__node-([a-z]+)/) || [])[1] || '?';
    const t = n.querySelector('[data-testid="flow-node-selected-tag"]');
    if (!t) { rows.push({ id, typeCls, aria: aria.slice(0, 24), tag: '（该节点没有此元素）' }); continue; }
    const r = t.getBoundingClientRect();
    const cs = getComputedStyle(t);
    rows.push({ id, typeCls, aria: aria.slice(0, 24), tag: `${Math.round(r.width)}×${Math.round(r.height)}`,
      inline: t.getAttribute('style') || '', fontSize: cs.fontSize, pad: cs.padding, cls: String(t.className || '').slice(0, 50),
      parent: String(t.parentElement?.className || '').slice(0, 50) });
  }
  return rows;
});

const bySize = {};
for (const r of out.tags) { const k = r.tag; (bySize[k] = bySize[k] || []).push(r); }
out.bySize = Object.fromEntries(Object.entries(bySize).map(([k, v]) => [k, { n: v.length, types: [...new Set(v.map((x) => x.typeCls))], sample: v.slice(0, 3) }]));

log('══ 按尺寸分组：');
for (const [k, v] of Object.entries(out.bySize)) {
  log(`  ${k}  → ${v.n} 个｜节点类型：${v.types.join(', ')}`);
  for (const s of v.sample) log(`        ${s.aria}  style="${s.inline}"  fontSize=${s.fontSize}  pad=${s.pad}`);
  const clsSet = new Set(v.sample.map((x) => x.cls));
  log(`        class 变体 ${clsSet.size} 种：${[...clsSet].join(' || ')}`);
}
out.end = { status: await status(), sel: await selCount() };
log('终态', JSON.stringify(out.end));
writeFileSync(new URL('./_tmp-b89d.json', import.meta.url), JSON.stringify(out, null, 1));
log('已写 _tmp-b89d.json');
await b.close();
