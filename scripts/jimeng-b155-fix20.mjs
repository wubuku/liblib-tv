import fs from 'node:fs';
const P = new URL('../docs/user-manual/jimeng-canvas/10-tasks/timeline-node.md', import.meta.url);
let s = fs.readFileSync(P, 'utf8');
const 锚 = '- **20 个 testid**：';
const 新 = '- 🔴 **2026-10-04 批次 155 订正：下面这份清单实际是 21 个，不是 20 个**（列表本身是对的，本轮实测 21 个、逐条对上、缺 0 多 0）：';
const 前 = s;
const n = 前.split(锚).length - 1;
console.log('锚点出现次数 =', n);
if (n !== 1) { console.log('⛔ 不是 1 次，不动'); process.exit(1); }
const t = 前.replace(锚, 新);
console.log('replace 长度变化 =', t.length - 前.length, '| 期望', 新.length - 锚.length);
console.log('替换后锚点还在吗 =', t.indexOf(锚) >= 0, '（在新文本里出现的位置 =', t.indexOf(锚), '）');
if (t.length - 前.length === 新.length - 锚.length && t.indexOf(锚) < 0) {
  fs.writeFileSync(P, t);
  console.log('✅ 已写回，「20 个 testid」订正为 21');
} else {
  console.log('⛔ 自检不过，未写回');
  process.exit(1);
}
