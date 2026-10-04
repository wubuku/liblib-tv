import fs from 'node:fs';
// 批次 151 三份证据的机械裁剪：只压掉「3 份逐字重复的 CSS 变量」，判定一个不动。
// 🔴 一次性守卫（同批次 150 立规）：脚本不幂等，检测到已裁剪即拒绝重跑。
const 目标 = [
  { 文件: 'scripts/_tmp-b151.json', 标记: '_裁剪说明' },
  { 文件: 'scripts/_tmp-b151b.json', 标记: '_裁剪说明' },
  { 文件: 'scripts/_tmp-b151c.json', 标记: '_裁剪说明' },
];
const 变量键 = [
  '--octo-canvas-node-chrome-counter-scale',
  '--octo-canvas-node-surface-stroke-counter-scale',
  '--octo-canvas-node-tag-hit-area-counter-scale',
  '--octo-canvas-selection-outline',
  '--octo-canvas-connection-stroke-world-width',
  '--octo-canvas-node-external-frame-radius',
  '--octo-canvas-node-external-frame-inset',
  '--octo-canvas-node-external-frame-stroke-width',
  '--octo-canvas-node-title-row-center',
];
const 表 = {};
let 序 = 0;
function 缩(v) {
  if (!v || typeof v !== 'object') return v;
  const out = {};
  for (const [k, val] of Object.entries(v)) {
    if (变量键.includes(k)) { 表[k] ??= ++序; out['V' + 表[k]] = val; }
    else out[k] = val;
  }
  return out;
}
function 走(v) {
  if (Array.isArray(v)) return v.map(走);
  if (!v || typeof v !== 'object') return v;
  const out = {};
  for (const [k, val] of Object.entries(v)) {
    if (k === '变量' || k === '各节点变量') { out[k + '_摘要'] = 缩(val); continue; }
    out[k] = 走(val);
  }
  return out;
}

const 字典 = Object.fromEntries(Object.entries(表).map(([k, v]) => ['V' + v, k]));

for (const { 文件, 标记 } of 目标) {
  if (!fs.existsSync(文件)) { console.log('（跳过，不存在）' + 文件); continue; }
  const orig = JSON.parse(fs.readFileSync(文件, 'utf8'));
  if (orig[标记]) { console.error('🔴 ' + 文件 + ' 已裁剪过，拒绝重跑'); process.exit(1); }
  const 前 = Buffer.byteLength(JSON.stringify(orig));
  const j = 走(orig);
  j[标记] = {
    为什么: '本文件体积主要来自「3 个节点 × 24 种元素 × 9 枚 CSS 变量」的机械重复。裁剪按**机械规则**执行，**不删任何一条读数、不改任何一个判定**。',
    规则: [
      '① 每个元素的 `变量` 字段里有 9 枚 `--octo-canvas-*` 变量逐字重复出现（12 个节点 × 数十个元素）⇒ 换成短名 `V1`…`V9`，对照见 `_变量字典`。',
      '② `屏上` / `css` / `文字` / `文字` / `节点屏上` / `节点css` / `aria` / `class` / `选中` / `删除` / `护栏` / `收尾` / `断言全过` / `表` —— **一律原样保留**。',
      '③ 判据结论（`是否全同` / `静息态是否全同` / `只在建完态出现` / `共有但尺寸变`）—— **原样保留**。',
    ],
    一次性守卫: '本脚本不幂等（第二次跑已无 `变量` 字段可压，且会把说明重写）。已加守卫：检测到 `_裁剪说明` 已存在即 exit 1。',
  };
  j._变量字典 = 字典;
  const 后 = Buffer.byteLength(JSON.stringify(j, null, 1) + '\n');
  fs.writeFileSync(文件, JSON.stringify(j, null, 1) + '\n');
  console.log(文件 + '：' + 前 + ' → ' + 后 + ' 字节（降 ' + (100 - 后 / 前 * 100).toFixed(1) + '%）');
}
console.log('变量字典 =', JSON.stringify(字典, null, 1));
