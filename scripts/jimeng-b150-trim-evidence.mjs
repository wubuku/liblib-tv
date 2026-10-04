import fs from 'node:fs';
const P = 'scripts/_tmp-b150.json';
const j = JSON.parse(fs.readFileSync(P, 'utf8'));

// 🔴 一次性守卫：这个脚本**不是幂等的** —— 第二次运行时规则 A 会处理 0 条
// （`各节点变量` 已被删掉），却仍会把 `处理条数` 覆盖成 0、把说明重写一遍，
// 于是证据文件里的「处理条数 = 0」会与真实值矛盾。
// 批次 150 实测：首次 44 条、误跑第二次 0 条 ⇒ **改前先查 `_裁剪说明` 是否已存在**。
if (j._裁剪说明) {
  console.error('🔴 该证据文件已裁剪过（`_裁剪说明` 已存在），本脚本是一次性的，拒绝重跑。');
  console.error('   当前记录的处理条数 =', j._裁剪说明.处理条数);
  process.exit(1);
}

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

let 处理 = 0;
// 机械规则 A：`比对` 里每个元素的「各节点变量」是 3 份逐字相同的长对象。
// 只保留**判据结论**（是否全同）与键名清单；真实取值在 `族.节点变量` 里，已单独保留。
for (const f of j.族) {
  for (const b of f.比对) {
    if (!b.各节点变量) continue;
    处理++;
    // ⚠️ 空值防护：该元素在某些节点上不存在（选中态才出现），那一项是 `null`。
    // `null` 与「有值」逐字不同 ⇒ 会被正确判成「不全同」，但不能对它调 Object.keys。
    const ser = b.各节点变量.map((v) => (v ? JSON.stringify(v) : 'null'));
    const 全同 = ser.every((s) => s === ser[0]);
    b.各节点变量_是否全同 = 全同;
    b.各节点变量_有null项 = ser.includes('null');
    b.各节点变量_键 = [...new Set(b.各节点变量.filter(Boolean).flatMap((v) => Object.keys(v)))];
    delete b.各节点变量;
  }
}

// 机械规则 B：9 枚 CSS 变量逐字出现在每个节点、每个元素上 ⇒ 换成短名 V1…V9
const 变量表 = {};
let 序 = 0;
function 缩(v) {
  if (!v || typeof v !== 'object') return v;
  const out = {};
  for (const [k, val] of Object.entries(v)) {
    if (变量键.includes(k)) { 变量表[k] ??= ++序; out['V' + 变量表[k]] = val; }
    else out[k] = val;
  }
  return out;
}
const 前 = Buffer.byteLength(JSON.stringify(j));
for (const f of j.族) {
  f.节点变量 = f.节点变量.map(缩);
  for (const b of f.量) {
    b.变量 = 缩(b.变量);
    for (const e of Object.values(b.元素)) e.变量 = 缩(e.变量);
  }
}

j._裁剪说明 = {
  为什么: '原始证据 176KB，是本项目已入库证据里最大的一份（批次 148 = 67KB、批次 149 = 21KB）。裁剪全部按**机械规则**执行，**不删任何一条读数、不改任何一个判定**。',
  规则: [
    'A. `比对` 里每个元素的 `各节点变量` 原本是 3 份逐字相同的长对象 ⇒ 只保留判据结论 `各节点变量_是否全同` 与键名清单 `各节点变量_键`。**真实取值没有被删**，它们完整保留在同族的 `节点变量` 字段里（同样 3 份，覆盖同一批节点）。',
    'B. 9 枚 CSS 变量逐字出现在每个节点、每个元素上 ⇒ 换成短名 `V1`…`V9`，对照见 `_变量字典`。',
    '未触碰：`量` / `节点屏上` / `比对.各节点屏上` / `比对.是否全同` / `删除` / `护栏` / `缩放建前` / `缩放建后` / `ids` / `起点` / `收尾` / `小地图后` / `断言全过` / `有不一致` —— **一律原样保留**。',
  ],
  处理条数: 处理,
  关键读数未被裁剪: [
    '同族三节点 `chrome-counter-scale` 逐字相同 ⇒ 各族 `节点变量`（现为 V1 短名，3 份）',
    '`flow-node-selected-tag` 12/12 恒 `24×24` ⇒ 各族 `量` 里该元素的 `屏上`',
    '`收尾.节点数 = 76` / `收尾.选中 = 0` / `收尾.zoom = "Zoom options, 60%"` / `收尾.积分`',
    '9/9 删除记录的 `消失` 集合（每族 3 条）',
    '`有不一致` 全部 23 条',
  ],
};
j._变量字典 = Object.fromEntries(Object.entries(变量表).map(([k, v]) => ['V' + v, k]));

const 后 = JSON.stringify(j, null, 1) + '\n';
fs.writeFileSync(P, 后);
console.log('原始', 前, '→ 裁剪后', Buffer.byteLength(后), '**字节**（降 ' + (100 - Buffer.byteLength(后) / 前 * 100).toFixed(1) + '%）');
console.log('规则 A 处理 比对 条数 =', 处理);
console.log('变量字典 =\n' + JSON.stringify(j._变量字典, null, 1));
// 自检：关键读数仍在
const chk = JSON.parse(fs.readFileSync(P, 'utf8'));
const tags = chk.族.flatMap((f) => f.量.map((b) => JSON.stringify(b.元素['flow-node-selected-tag']?.屏上)));
console.log('selected-tag 读数条数 =', tags.length, '取值集合 =', [...new Set(tags)].join(' '));
console.log('族数', chk.族.length, '| 收尾.节点数', chk.收尾.节点数, '| 断言全过', chk.断言全过, '| 有不一致条数', chk.有不一致.length);
