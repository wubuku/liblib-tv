// 把 c 轮的原始证据裁剪成「保留全部相关读数 + 完整计数」的版本再入库。
//
// 🔑 为什么裁：原始 `_tmp-b146c.json` 有 **1.19 MB**，体积的九成是
//    **232 个元素 × 7 个时点**的重复枚举，而那 232 个里绝大多数是节点的
//    `react-flow__handle`（class 里带 "connection" 所以被扫到）。
//    手册里关于它的**唯一**结论是一个数字 ——「全页 232 个元素的 class 含 connection」。
//
// ✅ 裁剪规则（机械、可复核，不删任何被引用到的读数）：
//    ① **凡 class 命中这四个 token 之一的元素，逐字段全留**（每个时点）：
//       `react-flow__connectionline` / `react-flow__connection` / `react-flow__connection-path`
//       / `z-canvas-connection-flow-surface`
//    ② 其余元素**只留计数**（`其余元素数`），并保留 `全量元素数`。
//    ③ 每个时点的 `edge元素数`、菜单/选中/状态行等顶层字段原样保留。
//
// 📌 原始文件未入库；重跑 `node scripts/jimeng-b146c.mjs` 可逐字复现。
//    本文件带 `_裁剪说明` 字段，读者一看就知道它不是原始 dump。
import fs from 'node:fs';

const F = 'scripts/_tmp-b146c.json';
const r = JSON.parse(fs.readFileSync(F, 'utf8'));
const 关键 = ['react-flow__connectionline', 'react-flow__connection', 'react-flow__connection-path', 'z-canvas-connection-flow-surface'];
const 时点 = ['拖前连接', '采样A', '采样B', '采样C_松手前', '松后150ms', '松后2500ms', '关菜单后', '收尾'];

const out = { ...r };
let 前 = 0, 后 = 0;
for (const k of 时点) {
  const v = k === '收尾' ? r.收尾 && r.收尾.剩余connection元素 : r[k];
  if (!v || !Array.isArray(v.元素)) continue;
  const 全 = v.元素.length;
  const 留 = v.元素.filter((e) => 关键.some((t) => (e.cls || '').includes(t)));
  前 += 全; 后 += 留.length;
  const 新 = { edge元素数: v.edge元素数, 全量元素数: 全, 保留元素数: 留.length, 其余元素数: 全 - 留.length, 元素: 留 };
  if (k === '收尾') { out.收尾.剩余connection元素 = 新; } else { out[k] = 新; }
}
out._裁剪说明 = `本文件是 \`scripts/jimeng-b146c.mjs\` 原始输出的**裁剪版**（原始约 1.19 MB，未入库；重跑该脚本可逐字复现）。裁剪规则：class 命中 ${关键.map((t) => '`' + t + '`').join(' / ')} 之一的元素**逐字段全留**，其余元素**只留计数**（\`全量元素数\` / \`其余元素数\`）。裁剪前元素枚举合计 ${前} 条 → 裁剪后 ${后} 条。手册引用的每一个读数（描边、盒、\`d\` 前 80 字符、\`d\` 长度、父 svg、\`在edge内\`、各时点的 \`edge元素数\`）都在保留集内。`;

fs.writeFileSync(F, JSON.stringify(out, null, 1) + '\n');
console.log(`裁剪完成：元素枚举 ${前} → ${后} 条；文件 ${(fs.statSync(F).size / 1024).toFixed(1)} KB`);
console.log('顶层键:', Object.keys(out).join(', '));
