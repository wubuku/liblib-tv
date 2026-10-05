// 批次 170 b 轮：找入口。16 个视口类静止态全未挂载 ⇒ 必须逐个打开。
// 本轮只做**只读普查**：节点类型分布 + 顶部/侧边工具条上有哪些可点的入口。
// ⛔ 不点任何会生成/扣费的按钮。
import { openCanvas, readers } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);

const out = await p.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const nodes = Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const r = n.getBoundingClientRect();
    return {
      id: n.getAttribute('data-id'),
      cls: (n.getAttribute('class') || '').split(/\s+/).filter((c) => c && !c.startsWith('react-flow')).join(' '),
      w: Math.round(r.width), h: Math.round(r.height),
      text: (n.innerText || '').trim().slice(0, 40).replace(/\n/g, '⏎'),
      testids: Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')).slice(0, 8),
    };
  });
  // 按 (class 前缀, 尺寸) 归类
  const bucket = {};
  for (const n of nodes) {
    const key = n.cls.split(/\s+/).slice(0, 3).join(' ') || '(无类名)';
    (bucket[key] = bucket[key] || []).push(n);
  }
  // 顶层可点按钮（排除节点内部）
  const nodeSet = new Set(Array.from(document.querySelectorAll('.react-flow__node')));
  const btns = Array.from(document.querySelectorAll('button,[role=button]')).filter((e) => {
    if (vis(e) === false) return false;
    for (let n = e; n && n !== document.body; n = n.parentElement) if (nodeSet.has(n)) return false;
    return true;
  }).map((e) => ({
    testid: e.getAttribute('data-testid'),
    aria: e.getAttribute('aria-label') || (e.innerText || '').trim().slice(0, 24),
    title: e.getAttribute('title'),
    cls: (e.getAttribute('class') || '').split(/\s+/).filter((c) => c.startsWith('max-w-canvas') || c.startsWith('max-h-canvas') || c.includes('viewport')).join(' '),
  }));
  return {
    nodes: nodes.length,
    buckets: Object.fromEntries(Object.entries(bucket).map(([k, v]) => [k, {
      n: v.length, sample: v[0].w + '×' + v[0].h, sampleText: v[0].text,
    }])),
    btns,
  };
});

console.log(JSON.stringify({ base: { status: await R.status(), credits: await R.credits() }, ...out }, null, 1));
await b.close();
