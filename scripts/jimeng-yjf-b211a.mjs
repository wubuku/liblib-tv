// 会话 mvs_fb62b78 · 批次 211 a 轮：**普查** —— 先摸清共享画布上「有哪些类型 × 有没有资源」的节点。
//
// 靶子（`connect-nodes.md:573`）：「带内容的图片节点只有 after ⊕、没有 before ⊕」
// —— 批次 59 / 73 两次独立观测都这样，但**机制未验证**。
// 🔴 而 `20-reference.md:309` 已经记过一次教训：「两次都错在拿不同缩放的读数互比」。
//   ⇒ 本轮先把**可用的格子**列出来（哪些类型、有没有资源），
//   下一轮再在**同一个缩放**下做受控矩阵 —— 不要在还没摸清库存时就动手。
//
// 本轮**只读**：不选中任何节点、不改缩放、不改视口。
import fs from 'node:fs';
import { openCanvas, readers } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);

const 基线 = {
  缩放: await R.zoom(), 视口: await p.evaluate(() => [innerWidth, innerHeight, devicePixelRatio]),
  状态行: await R.status(), 选中: await R.selCount(), 积分: await R.credits(),
  浮层: await R.overlays(),
};
console.log('基线：', JSON.stringify(基线));

const 清单 = await p.evaluate(() => {
  const 类型猜 = (n) => {
    const t = Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid')).join(' ');
    if (/timeline-flow-node/.test(t)) return '时间线';
    if (/director/.test(t)) return '导演台';
    if (/subject/.test(t)) return '主体';
    if (/audio/.test(t)) return '音频';
    if (/video/.test(t)) return '视频';
    if (/image/.test(t)) return '图片';
    if (/text-flow-node|text-node/.test(t)) return '文本';
    return '未识别';
  };
  // 🔴 判「有没有资源」**不能用 <img> 计数**（批次 73 自伤：缩略图不是 <img>，计数恒 0）。
  //   这里用两个互相独立的判据一起记，回头好交叉验证：
  //   ① 节点 innerText 里那句资源账 `N ready, N processing, N failed`；
  //   ② 存在 `video-node-empty` / `audio-node-empty` 这类「空态」testid。
  const 资源账 = (t) => {
    const m = /(\d+)\s*ready,\s*(\d+)\s*processing,\s*(\d+)\s*failed/.exec(t || '');
    return m ? { ready: +m[1], processing: +m[2], failed: +m[3] } : null;
  };
  return Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const t = Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid'));
    const inner = n.innerText || '';
    const 账 = 资源账(inner);
    return {
      id: n.getAttribute('data-id'),
      类型: 类型猜(n),
      标题: (n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || '',
      资源账: 账,
      有空态testid: t.filter((x) => /-empty$/.test(x || '')),
      有媒体层: t.includes('flow-node-media-stroke'),
      有audio元素: !!n.querySelector('audio'),
      有video元素: !!n.querySelector('video'),
      内文前80: inner.replace(/\s+/g, ' ').slice(0, 80),
    };
  });
});

const 汇总 = {};
for (const n of 清单) {
  const key = `${n.类型}｜${n.资源账 ? (n.资源账.ready > 0 ? 'ready' : 'ready=0') : '无资源账'}`;
  (汇总[key] = 汇总[key] || []).push(n);
}
console.log('\n=== 类型 × 资源 分布 ===');
for (const [k, v] of Object.entries(汇总)) {
  console.log(`${k}  ×${v.length}   例：${v.slice(0, 3).map((x) => `${x.标题 || x.id}(${x.有audio元素 ? 'audio' : ''}${x.有video元素 ? 'video' : ''})`).join(' / ')}`);
}

const out = { 轮次: 'b211a', 目的: '只读普查：哪些格子可做受控矩阵', 基线, 节点数: 清单.length, 汇总: {}, 清单 };
for (const [k, v] of Object.entries(汇总)) out.汇总[k] = v.map((x) => x.id);
fs.writeFileSync('scripts/_tmp-b211a.json', JSON.stringify(out, null, 1));

// 收尾复核：本轮不该留下任何状态变化
const 收尾 = { 缩放: await R.zoom(), 状态行: await R.status(), 选中: await R.selCount(), 积分: await R.credits() };
console.log('\n收尾：', JSON.stringify(收尾));
out.收尾 = 收尾;
fs.writeFileSync('scripts/_tmp-b211a.json', JSON.stringify(out, null, 1));
await b.close();
