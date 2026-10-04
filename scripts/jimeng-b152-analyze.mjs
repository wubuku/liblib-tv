import fs from 'node:fs';
const j = JSON.parse(fs.readFileSync('scripts/_tmp-b152.json', 'utf8'));
const 时点 = ['Q1', 'Q2', 'Q2b', 'Q3'].filter((t) => j[t]);
const 图 = {};
for (const t of 时点) { 图[t] = {}; for (const r of j[t].行) 图[t][r.id] = r; }

console.log('=== Q1：同一缩放下 k ≠ 2 的节点（audio 族）===');
for (const r of j.Q1.行)
  if (r.k !== 2) console.log('  ' + r.id + '  k=' + String(r.k).padEnd(20) + ' 1/k=' + (1 / r.k).toFixed(6) + ' 标签屏上=' + JSON.stringify(r.标签屏上) + ' 节点屏上=' + JSON.stringify(r.节点屏上) + ' ' + r.aria);

console.log('\n=== 逐节点追踪：k 发生过变化的节点 ===');
const ids = [...new Set(时点.flatMap((t) => Object.keys(图[t])))];
const 变的 = [];
for (const id of ids) {
  const 轨 = 时点.map((t) => (图[t][id] ? 图[t][id].k : '(不在)'));
  const 有变 = new Set(轨.filter((x) => x !== '(不在)')).size > 1;
  const 存在变化 = 轨.some((x) => x === '(不在)');
  if (有变 || 存在变化) {
    变的.push({ id, 轨, 族: (图.Q1[id] || 图.Q2[id] || {}).族, aria: (图.Q1[id] || 图.Q2[id] || {}).aria });
  }
}
for (const v of 变的) console.log('  ' + v.id + ' [' + v.族 + '] ' + JSON.stringify(v.轨) + '  ' + v.aria);
console.log('  共 ' + 变的.length + ' 个节点的 k 不是恒定');

console.log('\n=== k ≡ 2 的节点数（恒定那批）===');
for (const t of 时点) {
  const n = j[t].行.filter((r) => r.k === 2).length;
  console.log('  ' + t + '：' + n + ' / ' + j[t].行.length);
}

console.log('\n=== 每个时点：k 与「当前实测缩放的倒数」的关系 ===');
for (const t of 时点) {
  const s = j[t].实测scale;
  const 匹配 = j[t].行.filter((r) => Math.abs(r.k - 1 / s) < 1e-6).length;
  const 近 = j[t].行.filter((r) => r.k > 1 / s - 1e-6 && r.k <= 2).length;
  console.log('  ' + t + ' 实测 ' + s + ' → 1/s=' + (1 / s).toFixed(6) +
    ' | k 恰等于 1/s 的节点数 ' + 匹配 + ' | k ∈ (1/s, 2] 的节点数 ' + 近 + ' | 共 ' + j[t].行.length);
}

console.log('\n=== 标签屏上尺寸的全量取值（每时点）===');
for (const t of 时点) {
  const m = new Map();
  for (const r of j[t].行) { const k = JSON.stringify(r.标签屏上); m.set(k, (m.get(k) || 0) + 1); }
  console.log('  ' + t + '：' + [...m].map(([k, n]) => k + '×' + n).join('  '));
}

console.log('\n=== 收尾 ===', JSON.stringify(j.收尾));
console.log('断言全过:', j.断言全过);
