// 批次 170 c 轮：76 个节点全是同一个壳（`nopan selectable draggable` 182×324，
// 文本形如「视频 1 / No resources: 0 ready」）⇒ 分组节点。要进壳里看真实内容类型。
// 本轮只读。
import { openCanvas, readers } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);

const out = await p.evaluate(() => {
  const nodes = Array.from(document.querySelectorAll('.react-flow__node'));
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  return nodes.map((n) => {
    const r = n.getBoundingClientRect();
    // 节点的「类型签名」= 去掉通用工具类后剩下的类名 + 内部 testid 种类
    const cls = (n.getAttribute('class') || '').split(/\s+/);
    const tids = Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid'))));
    return {
      id: n.getAttribute('data-id'),
      w: Math.round(r.width), h: Math.round(r.height),
      head: (n.innerText || '').trim().split('\n').filter(Boolean).slice(0, 3),
      clsTail: cls.filter((c) => !/^(nopan|selectable|draggable|react-flow.*)$/.test(c)).join(' ').slice(0, 120),
      tids: tids.slice(0, 10),
      innerCards: Array.from(n.querySelectorAll('img,video,canvas')).filter(vis).length,
    };
  });
});

const sig = {};
for (const n of out) {
  const k = n.head[0] + ' || ' + n.clsTail;
  (sig[k] = sig[k] || []).push(n);
}
console.log(JSON.stringify({ base: { status: await R.status(), credits: await R.credits() } }, null, 1));
console.log('distinct node signatures:', Object.keys(sig).length);
for (const [k, v] of Object.entries(sig)) {
  console.log(`\n  ×${v.length}  ${k.slice(0, 130)}`);
  console.log(`     clsTail=${v[0].clsTail.slice(0, 120)}`);
  console.log(`     head=${JSON.stringify(v[0].head)}  tids=${JSON.stringify(v[0].tids)}  imgs=${v[0].innerCards}`);
}
await b.close();
