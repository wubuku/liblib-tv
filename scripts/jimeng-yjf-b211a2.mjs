// 会话 mvs_fb62b78 · 批次 211 a2 轮：**订正 a 轮的判据**。
//
// 🔴 a 轮用 `/(\d+)\s*ready,\s*(\d+)\s*processing,\s*(\d+)\s*failed/` 判「有没有资源」，
//   结果 76 个节点里只有导演台 1 个命中 ⇒ 看起来「全画布都没有资源」。
//   但批次 158b 用的是 **`/[\d]+ resource[s]?: …/`** —— 是**另一个句式**。
//   ⇒ a 轮那个「全都没有资源」极可能是**判据写错**造成的恒假，不是事实。
//   📌 这正是立规 42 的又一次发生：「写断言前先问它在我的输入上会不会恒假」。
//
// 本轮用**三个互相独立的判据**重读一遍，看它们是否一致：
//   ① 资源账句式 A：`N resource(s)?: N ready, N processing, N failed`
//   ② 资源账句式 B：`N ready, N processing, N failed`（a 轮用的那个）
//   ③ 空态 testid（`image-node-empty` / `video-node-empty` / `audio-node-empty` …）
//   ④ 媒体元素（<audio> / <video>）
// 只读，不选中、不改任何状态。
import fs from 'node:fs';
import { openCanvas, readers } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);

const 清单 = await p.evaluate(() => {
  const A = (t) => ((t || '').match(/(\d+)\s*resource[s]?:[^\n]*/) || [])[0] || null;
  const B = (t) => ((t || '').match(/(\d+)\s*ready,\s*(\d+)\s*processing,\s*(\d+)\s*failed/) || [])[0] || null;
  return Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const tids = Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid'));
    const inner = n.innerText || '';
    const 标题 = (n.querySelector('[data-testid="flow-node-title"]') || {}).innerText || '';
    const 类型 = /timeline-flow-node/.test(tids.join(' ')) ? '时间线'
      : /director/.test(tids.join(' ')) ? '导演台'
      : /subject/.test(tids.join(' ')) ? '主体'
      : /audio/.test(tids.join(' ')) ? '音频'
      : /video/.test(tids.join(' ')) ? '视频'
      : /image/.test(tids.join(' ')) ? '图片'
      : /text-flow-node|text-node/.test(tids.join(' ')) ? '文本' : '未识别';
    return {
      id: n.getAttribute('data-id'), 类型, 标题,
      账A: A(inner), 账B: B(inner),
      空态testid: tids.filter((x) => /-empty$/.test(x || '')),
      有audio: !!n.querySelector('audio'), 有video: !!n.querySelector('video'),
    };
  });
});

const 统计 = (f) => 清单.filter(f).length;
console.log('节点总数', 清单.length);
console.log('账A（N resources?: …）命中', 统计((x) => x.账A));
console.log('账B（N ready, N processing…）命中', 统计((x) => x.账B));
console.log('有 <audio>', 统计((x) => x.有audio), '｜ 有 <video>', 统计((x) => x.有video));
console.log('有空态 testid', 统计((x) => x.空态testid.length > 0));
console.log('\n=== 按类型：账A 命中 / 总量 ===');
const 按类型 = {};
for (const x of 清单) {
  按类型[x.类型] = 按类型[x.类型] || { 总: 0, 账A: 0, 有媒体: 0, 空态: 0, 例: [] };
  const g = 按类型[x.类型];
  g.总++; if (x.账A) g.账A++; if (x.有audio || x.有video) g.有媒体++; if (x.空态testid.length) g.空态++;
  if (g.例.length < 3) g.例.push(`${x.标题 || x.id}${x.账A ? ' ✔账' : ''}${x.有audio ? ' <audio>' : ''}${x.有video ? ' <video>' : ''}${x.空态testid.length ? ' 空态' : ''}`);
}
for (const [k, g] of Object.entries(按类型)) {
  console.log(`${k}: 总 ${g.总} ｜ 账A ${g.账A} ｜ 有媒体元素 ${g.有媒体} ｜ 空态 ${g.空态}   例: ${g.例.join(' | ')}`);
}

console.log('\n=== 所有账A 逐字 ===');
for (const x of 清单.filter((y) => y.账A)) console.log(`  [${x.类型}] ${x.标题 || x.id}  ${x.账A}`);

const out = { 轮次: 'b211a2', 订正: 'a 轮判据写错（句式不对恒假）', 账A句式: '/(\\d+)\\s*resource[s]?:[^\\n]*/', 账B句式: '/(\\d+)\\s*ready,\\s*(\\d+)\\s*processing,\\s*(\\d+)\\s*failed/',
  节点数: 清单.length, 按类型, 有账A的节点: 清单.filter((x) => x.账A).map((x) => ({ id: x.id, 类型: x.类型, 标题: x.标题, 账: x.账A })), 清单 };
fs.writeFileSync('scripts/_tmp-b211a2.json', JSON.stringify(out, null, 1));
console.log('\n收尾：', JSON.stringify({ 状态行: await R.status(), 选中: await R.selCount(), 缩放: await R.zoom() }));
await b.close();
