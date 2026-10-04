// 批次 155 文档落地：① 追加 SOURCE_OBSERVATIONS §4.78
//                      ② 就地改写 timeline-node.md 三处过期记述 + 插三张图
//                      ③ AUDIT / PROGRESS 各加一节  ④ 台账加第 69 条
//
// 🔑 纪律：每次 replace 验「真生效 + 旧锚点已消失 + 锚点全册唯一」。
//    正文 alt 一律**从 manifest 用真解析器取**，不手抄。
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';

const DIR = new URL('../docs/user-manual/jimeng-canvas/', import.meta.url);
const 读 = (p) => fs.readFileSync(new URL(p, DIR), 'utf8');
const 存 = (p, s) => fs.writeFileSync(new URL(p, DIR), s);
let 失败 = 0;
const 取alt = (file) => execFileSync('python3', ['scripts/jimeng_yaml_dump.py', new URL('screenshots/manifest.yml', DIR).pathname],
  { encoding: 'utf8' }) && JSON.parse(execFileSync('python3', ['scripts/jimeng_yaml_dump.py', new URL('screenshots/manifest.yml', DIR).pathname], { encoding: 'utf8' }))
  .find((i) => i.file === file).alt;

const 改 = (p, 锚, 新, 名) => {
  const s = 读(p);
  const n = s.split(锚).length - 1;
  if (n !== 1) { console.log('❌ ' + 名 + ' 锚点命中 ' + n + ' 次（必须恰好 1）'); 失败++; return; }
  const t = s.replace(锚, 新);
  if (t === s) { console.log('❌ ' + 名 + ' replace 未生效'); 失败++; return; }
  if (t.indexOf(锚) >= 0) { console.log('❌ ' + 名 + ' 旧锚点仍在'); 失败++; return; }
  存(p, t);
  console.log('✅ ' + 名 + '（' + s.length + ' → ' + t.length + '）');
};

// ---------- ① 追加 manifest 三条 ----------
{
  const P = 'screenshots/manifest.yml';
  const s = 读(P);
  const add = fs.readFileSync('/tmp/b155-manifest.yml', 'utf8');
  if (add.includes('�')) { console.log('⛔ manifest 片段含 U+FFFD'); 失败++; }
  else { 存(P, s + add); console.log('✅ manifest 追加 3 条（+' + add.length + '）'); }
}

// ---------- ② 追加 §4.78 ----------
{
  const p = 'SOURCE_OBSERVATIONS.md';
  const s = 读(p);
  const 段 = fs.readFileSync('/tmp/b155-so478.md', 'utf8');
  if (段.includes('�')) { console.log('⛔ §4.78 片段含 U+FFFD'); 失败++; }
  else if (s.indexOf('## §4.78 批次 155') >= 0) console.log('⏭ §4.78 已存在');
  else { 存(p, s.replace(/\s*$/, '\n') + 段); console.log('✅ 追加 §4.78（+' + 段.length + '）'); }
}

// ---------- ③ timeline-node.md 三处 ----------
const TL = '10-tasks/timeline-node.md';
const a57 = 取alt('screenshots/57-timeline-node-created-from-rail.png');
const a58 = 取alt('screenshots/58-timeline-fullscreen-from-node.png');
const a59 = 取alt('screenshots/59-timeline-export-overlay.png');
console.log('三张 alt 长度 =', a57.length, a58.length, a59.length);

改(TL,
  '入口：**空白右键 → 新建节点 → 时间线**（🔴 **左栏那个「时间线」按钮本轮仍未走通**，\n批次 107 记过「点 24 轮无新节点」；**走右键这条一定成**）。',
  '入口：**左栏第 5 枚 40×40 键（`aria="时间线"` @16,361）** 或 **空白右键 → 新建节点 → 时间线**。\n'
  + '> ✅ **2026-10-04 批次 155 订正：「左栏那个「时间线」按钮本轮仍未走通」是错的。**\n'
  + '> 带**建-删护栏**（建前 76 == 预期基线、建前 0 选中、建前无组、建后差集恰好 1、\n'
  + '> 新节点恰好 `.selected`）重做，**护栏 5/5 全过**，左栏一点就成（`76 → 77`）。\n'
  + '> 🔴 **批次 107 之所以得出相反结论**：那一轮没有护栏，判据只有「建完数一下节点」——\n'
  + '> 在 76 节点、别人也在改的**共享画布**上，「节点数没变」有太多可能（点歪、点到被压住的元素、\n'
  + '> 2.5 秒还没渲染完、别人同时删了一个）。\n'
  + '> 📌 **共享画布上判「某个操作生效了吗」不能只判总量变没变**。详见 `SOURCE_OBSERVATIONS` §4.78.1。\n\n'
  + '![' + a57 + '](../screenshots/57-timeline-node-created-from-rail.png)',
  'TL 入口段（订正左栏 + 插图 57）');

改(TL,
  '- 点击 **导出时间线** 导出整条时间线。\n- ⚠️ **本手册未执行导出**：导出属于对外产出动作，按操作规范需单独授权。\n  请确认成片无误后自行操作。',
  '🔴 **2026-10-04 批次 155 订正：点「导出时间线」不是导出，它先弹一个「选目标/选格式」菜单。**\n\n'
  + '点节点内的 **导出时间线** → 弹出 `[role=menu][aria-label="导出时间线"]` **200×292**，里面是：\n\n'
  + '| 组 | 项 | 状态 |\n|---|---|---|\n'
  + '| 格式 | `导出为 MP4` | 🔴 **空时间线禁用**（灰字） |\n'
  + '| 格式 | `导出为 XML` | 可点（批量导出时间线素材） |\n'
  + '| — | 分隔线 | — |\n'
  + '| 目标 | `导出到剪映` | 可点 |\n'
  + '| 目标 | `导出到 DaVinci Resolve` | 可点 |\n'
  + '| 目标 | `导出到 Premiere` | 可点 |\n'
  + '| 目标 | `导出到 Final Cut Pro` | 可点 |\n\n'
  + '- `Esc` **一次**即可关掉这一层。\n'
  + '- ⚠️ **本手册仍未执行最终导出**（点菜单里的任何一项会把工程文件交给外部软件、或产出成片文件，\n'
  + '  属对外产出）。⚠️ 但**理由已经不是「需单独授权」**——授权已解除；\n'
  + '  现在的边界是「**本轮只验到菜单层**」。详见 `SOURCE_OBSERVATIONS` §4.78.4。\n\n'
  + '![' + a59 + '](../screenshots/59-timeline-export-overlay.png)',
  'TL 导出段（推翻一句式 + 插图 59）');

改(TL,
  '**仍未实测**：导出时间线（属对外产出动作，需单独授权）。',
  '**导出时间线的状态（2026-10-04 批次 155 更新）**：**菜单层已验成**（`200×292`、四个导出目标 + 两个格式、\n'
  + '空时间线上 MP4 禁用、`Esc` 一次可关），**最终导出仍未执行**（会产出对外文件）。',
  'TL 末尾「仍未实测」行');

// 全屏编辑小节插图 58
{
  const 锚 = '- 退出：右上角 **✕**（aria `Close timeline editor`）或 **Esc**。';
  const s = 读(TL);
  if (s.indexOf(锚) < 0) { console.log('❌ 全屏退出行锚点没找到'); 失败++; }
  else if (s.indexOf('58-timeline-fullscreen-from-node.png') >= 0) console.log('⏭ 图 58 已插入');
  else {
    const t = s.replace(锚, 锚 + '\n\n![' + a58 + '](../screenshots/58-timeline-fullscreen-from-node.png)');
    存(TL, t); console.log('✅ 全屏编辑小节插图 58');
  }
}

// ---------- ④ AUDIT / PROGRESS ----------
{
  const 节 = fs.readFileSync('/tmp/b155-audit.md', 'utf8');
  const p = 'AUDIT.md'; const s = 读(p);
  if (s.indexOf('批次 155（2026-10-04）结清「左栏时间线键走不通」') >= 0) console.log('⏭ AUDIT 已有批次 155');
  else { 存(p, s.replace(/\s*$/, '\n') + 节); console.log('✅ AUDIT.md 加批次 155（+' + 节.length + '）'); }
}
{
  const 节 = fs.readFileSync('/tmp/b155-progress.md', 'utf8');
  const p = 'PROGRESS.md'; const s = 读(p);
  if (s.indexOf('### 批次 155（2026-10-04）') >= 0) console.log('⏭ PROGRESS 已有批次 155');
  else { 存(p, s.replace(/\s*$/, '\n') + 节); console.log('✅ PROGRESS.md 加批次 155（+' + 节.length + '）'); }
}

console.log(失败 ? '\n⛔ ' + 失败 + ' 处失败' : '\n✅ 文档落地完成');
process.exit(失败 ? 1 : 0);
