import fs from 'node:fs';
import { chromium } from 'playwright';
import { openCanvas, readers, settle, PORT } from './jimeng-b135-lib.mjs';
const browser = await chromium.connectOverCDP({ endpointURL: `http://127.0.0.1:${PORT}` });
const ctx = browser.contexts()[0];
let p = ctx.pages().find((x) => /jimeng\.jianying\.com/.test(x.url())) || ctx.pages()[0];
const R = readers(p);
await openCanvas(); await settle(p, R);
const nodes = await p.evaluate(() => Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
  const t = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)/.exec(n.style.transform || '');
  const r = n.getBoundingClientRect();
  const vp = document.querySelector('.react-flow__viewport');
  const ms = vp ? /scale\(([\d.]+)\)/.exec(vp.style.transform || '') : null;
  const s = ms ? parseFloat(ms[1]) : null;
  return { id: n.getAttribute('data-id'), aria: n.getAttribute('aria-label'),
    cx: t ? Number(t[1]) : null, cy: t ? Number(t[2]) : null, 屏上: [Math.round(r.width), Math.round(r.height)] };
}).sort((a, b) => a.cx - b.cx));
// 画布中心 = 所有节点包围盒的中心
const xs = nodes.filter(n => n.cx !== null).map(n => n.cx), ys = nodes.filter(n => n.cy !== null).map(n => n.cy);
const 包围盒 = { xmin: Math.min(...xs), xmax: Math.max(...xs), ymin: Math.min(...ys), ymax: Math.max(...ys) };
包围盒.中心 = [ (包围盒.xmin + 包围盒.xmax) / 2, (包围盒.ymin + 包围盒.ymax) / 2 ];
// 按到中心的距离排序，便于挑样本
const 带距 = nodes.map(n => ({ ...n, 到中心: n.cx === null ? null : Math.round(Math.hypot(n.cx - 包围盒.中心[0], n.cy - 包围盒.中心[1]) * 100) / 100 }))
  .sort((a, b) => a.到中心 - b.到中心);
fs.writeFileSync('/tmp/b212-dump.json', JSON.stringify({ 节点数: nodes.length, 包围盒, 按x排序: nodes, 按到中心距离排序: 带距 }, null, 1));
console.log('节点数', nodes.length);
console.log('包围盒', JSON.stringify(包围盒));
console.log('\n最靠近画布中心的 8 个：');
for (const n of 带距.slice(0, 8)) console.log(`  ${n.aria} | id=${n.id} | [${n.cx}, ${n.cy}] | 屏上${JSON.stringify(n.屏上)} | 距中心 ${n.到中心}`);
console.log('\n画布最左的 6 个：');
for (const n of nodes.slice(0, 6)) console.log(`  ${n.aria} | ${n.id} | [${n.cx}, ${n.cy}]`);
console.log('\n画布最下 / 最右的 6 个：');
const byY = nodes.slice().sort((a, b) => b.cy - a.cy);
for (const n of byY.slice(0, 4)) console.log(`  ${n.aria} | ${n.id} | [${n.cx}, ${n.cy}]`);
process.exit(0);
