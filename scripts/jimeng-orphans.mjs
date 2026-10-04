// 找出「既不在严格基线、也不在 _external_nodes、也不在临时台账」的可疑节点。
// 用途：脚本中途 ABORT 时 mine 还没赋值 ⇒ finally 清不到它 ⇒ 需要事后按 id 兜底删除。
import { chromium } from 'playwright';
import { readFileSync } from 'node:fs';
const BASE = JSON.parse(readFileSync(new URL('./jimeng-baseline-nodes.json', import.meta.url), 'utf8'));
const LED = JSON.parse(readFileSync(new URL('./jimeng-ephemeral-ledger.json', import.meta.url), 'utf8'));
const b = await chromium.connectOverCDP('http://127.0.0.1:9444');
const p = b.contexts()[0].pages().find((x) => x.url().includes('ai-canvas'));
const rows = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((e) => {
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(e.style.transform || '');
  const r = e.getBoundingClientRect();
  return { id: e.getAttribute('data-id'), title: (e.querySelector('[data-testid="flow-node-title"]') || {}).innerText || e.innerText.split('\n')[0] || '',
    canvas: m ? [Math.round(parseFloat(m[1]) * 100) / 100, Math.round(parseFloat(m[2]) * 100) / 100] : null,
    screen: `${Math.round(r.width)}x${Math.round(r.height)}@${Math.round(r.x)},${Math.round(r.y)}` };
}));
// ⚠️ 自伤修正：`_external_nodes` 是 **对象**（id → 记录），不是数组。
//    上一版按数组写 `.map` 直接 TypeError。
const ext = BASE._external_nodes || {};
const known = new Set([...Object.keys(BASE.nodes), ...Object.keys(ext)]);
const orphans = rows.filter((r) => !known.has(r.id));
console.log('总节点', rows.length, '| 基线', Object.keys(BASE.nodes).length, '| 外部', (BASE._external_nodes || []).length, '| 台账', LED.ids.length);
console.log('未知节点（既非基线、也非已登记外部）:');
for (const o of orphans) console.log('  ', o.id, '|', JSON.stringify(o.title), '| canvas', JSON.stringify(o.canvas), '| screen', o.screen,
  '| 在台账:', LED.ids.includes(o.id));
console.log('状态:', (await p.evaluate(() => (document.body.innerText.match(/[\d]+ node[s]?, [\d]+ edges?, [\d]+ selected[^\n]*/) || ['?'])[0])));
await b.close();
