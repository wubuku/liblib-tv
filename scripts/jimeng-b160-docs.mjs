// 批次 160 文档手术 —— 全部用**行首/行尾锚**定位，不手抄原文
import fs from 'node:fs';
const 基 = 'docs/user-manual/jimeng-canvas/';
const 读 = (p) => fs.readFileSync(p, 'utf8').replace(/\n+$/, '').split('\n');
let 坏 = 0;
const 校验 = (名, ok, 详情) => { if (!ok) { 坏++; console.log('  ❌ ' + 名 + ' ' + JSON.stringify(详情)); } else console.log('  ✅ ' + 名); };
const 块 = fs.readFileSync('/tmp/b160-help-block.md', 'utf8').replace(/\n+$/, '').split('\n');

// ---------- 1. help-and-shortcuts.md ----------
{
  const P = 基 + '10-tasks/help-and-shortcuts.md';
  const L = 读(P);

  // ① 表格里「导演台」那一行
  const r = L.findIndex((x) => x.startsWith('| 导演台 | ⛔'));
  校验('导演台表格行锚', r >= 0, { r });
  console.log('  表格行 =', JSON.stringify(L[r]));
  L[r] = '| 导演台 | 🔴 **完全静默** | 与「音频」「什么都没选」**同型** —— 不导航、不提示、零变化（2026-10-05 批次 160 实测结清，见下） |';

  // ② 「为什么仍然不按 F」那一节整段换掉
  const s = L.findIndex((x) => x.startsWith('#### ⛔ 为什么「导演台」这一行仍然不按 F'));
  const e = L.findIndex((x) => x.startsWith('- **前提是先选中节点**，且 **Esc 一次即关**。'));
  校验('旧小节起锚', s >= 0, { s });
  校验('旧小节止锚', e > s, { e });
  console.log('  旧小节范围', s + 1, '..', e + 1, '共', e - s + 1, '行');
  L.splice(s, e - s + 1, ...块, '');

  // ③ 统计行
  const st = L.findIndex((x) => x.startsWith('**统计**：✅ 可用'));
  校验('统计行锚', st >= 0, { st });
  console.log('  统计行 =', JSON.stringify(L[st]).slice(0, 150));
  L[st] = L[st]
    .replace('❓ 未验证 **1**（导演台 F）', '❓ 未验证 **0**')
    .replace('🔴 无反应 **1**（V）', '🔴 无反应 **2**（视频、导演台 F）');

  fs.writeFileSync(P, L.join('\n') + '\n');
  console.log('  → 写回', P, '共', L.length, '行');
}

// ---------- 2. director-node.md：把 F 的结论并入「未执行/未验证」清单 ----------
{
  const P = 基 + '10-tasks/director-node.md';
  const L = 读(P);
  const a = L.findIndex((x) => x.startsWith('**未执行 / 未验证**'));
  校验('director-node 未验证清单锚', a >= 0, { a });
  console.log('  清单首行 =', JSON.stringify(L[a]).slice(0, 120));
  L.splice(a + 3, 0,
    '',
    '**2026-10-05 批次 160 补**：本节点上的 **F 键已测**（`scripts/jimeng-b160f.mjs`，5/5 断言通过）——',
    '**完全静默**：URL 16 帧不变、节点逐字 16 帧不变、对话框 0、「此快捷键当前不可用」提示 0 次、',
    '浮层恒 0、`body *` 元素总数恒 2368。⇒ **「进入导演台」只认那个按钮，键盘没有任何入口**，',
    '按 F 不会把你带进 3D 工作台。详见',
    '[快捷键与帮助](help-and-shortcuts.md)。');
  fs.writeFileSync(P, L.join('\n') + '\n');
  console.log('  → 写回', P, '共', L.length, '行');
}

// ---------- 3. 20-reference.md：导演台那行补一句 F 结论 ----------
{
  const P = 基 + '20-reference.md';
  const L = 读(P);
  const a = L.findIndex((x) => x.startsWith('| 导演台（Beta） |'));
  校验('20-reference 导演台行锚', a >= 0, { a });
  console.log('  原行 =', JSON.stringify(L[a]).slice(0, 200));
  if (!L[a].includes('按 F')) {
    L[a] = L[a].replace('；唯一操作「进入导演台」（会离开画布） |',
      '；唯一操作「进入导演台」（会离开画布）；🔴 **节点上按 F 完全静默**（批次 160 实测：不导航、不提示、零变化 ⇒ 键盘进不去 3D 工作台） |');
  }
  fs.writeFileSync(P, L.join('\n') + '\n');
  console.log('  → 写回', P, '共', L.length, '行');
}

console.log(坏 === 0 ? '\n✅ 手术全部锚定成功' : '\n❌ 有 ' + 坏 + ' 处锚点失败');
process.exit(坏 === 0 ? 0 : 1);
