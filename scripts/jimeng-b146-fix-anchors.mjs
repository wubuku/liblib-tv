// 批次 146 附加工具 —— 清理订正台账里 **12 个从未被验证过的幽灵 pattern**。
//
// 🔑 起因：本批给 `jimeng-backfill-gate.mjs` 加了「逐 pattern 幽灵检测」之后，
//    门立刻抓出 **12 个 pattern 一个字都匹配不到** —— 它们在台账里躺着，
//    而旧的门只判「entry 是否至少命中一处」，于是**全部静默通过**。
//    ⇒ 那些 entry 声称覆盖的旧结论，实际**没有任何一处被检查**。
//
// 每条的处理只有三种，且都必须有据：
//   重锚（文本还在、只是写法变了） ｜ 删除锚（目标文本已全册不存在） ｜ 保留（本来就对）
// 本脚本**逐条打印 grep 证据**，不靠记忆改。
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';

const F = 'scripts/jimeng-refuted-claims.json';
const DIR = 'docs/user-manual/jimeng-canvas';
const j = JSON.parse(fs.readFileSync(F, 'utf8'));

// [entryId, 幽灵 pattern, 处理, 新 pattern 或 null（= 删除）]
const 修 = [
  ['text-node-dblclick-no-edit', '始终为 0，工具条也\\*\\*一直是选中态那三项\\*\\*', '重锚', '双击后 `contenteditable` 与 `\\.ProseMirror` 始终为 0'],
  ['zoom-button-itself-is-input', '点它\\*\\*自动全选并聚焦\\*\\*', '重锚', '\\*\\*自动全选并聚焦\\*\\*'],
  ['voice-play-aria-flips-to-pause', '点下后 \\*\\*0.9s 仍是 `Play`\\*\\*', '重锚', '点下后 aria \\*\\*就地翻成 `Pause X`\\*\\*'],
  ['bottom-dock-has-5-controls', 'canvas-sidecar-launcher` \\| `118×34@1149,673` \\| 打开 AI 侧栏', '重锚', '与 AI 对话 外框 / 按钮'],
  ['save-to-subject-library-is-node-type-exclusive', '该节点类型独有的', '重锚', '原写「该节点类型独有」已订正'],
  ['bottom-status-bar-is-not-on-screen', '以及底部状态行', '删除', null],
  ['bottom-status-bar-is-not-on-screen', '状态行的判据', '删除', null],
  ['generation-history-panel-has-no-primary-tabs', '面板分两级', '删除', null],
  ['all-ui-clamped-elements-share-one-max-template', '所有族都是.*`max', '重锚', '所有族都是 `屏上值 = max'],
  ['all-ui-clamped-elements-share-one-max-template', '同一个 `max\\(`模板', '重锚', '同一个 `max\\(\\)` 模板'],
  ['click-text-node-only-bottom-blank-is-select', '点到正文会直接进入编辑态', '重锚', '点到正文会直接进入'],
  ['multi-selection-toolbar-has-no-add-tags', 'Add\\s*tags[^|\\n]{0,30}不属于顶部工具条', '重锚', '早前版本写这里有「Add tags」'],
  // ---- 第二轮：重锚完再跑门，抓出「锚到了**正确记录**」的三个（比幽灵更隐蔽）----
  ['zoom-button-itself-is-input', '\\*\\*自动全选并聚焦\\*\\*', '删除2', null],
  ['voice-play-aria-flips-to-pause', '点下后 aria \\*\\*就地翻成 `Pause X`\\*\\*', '删除2', null],
  ['bottom-dock-has-5-controls', '与 AI 对话 外框 / 按钮', '删除2', null],
];

const walk = (d, o = []) => {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    const p = path.join(d, e.name);
    if (e.isDirectory()) walk(p, o); else if (e.name.endsWith('.md')) o.push(p);
  }
  return o;
};
const FILES = walk(DIR).map((f) => [f, fs.readFileSync(f, 'utf8')]);
const 命中 = (pat) => {
  const re = new RegExp(pat); const out = [];
  for (const [f, s] of FILES) s.split('\n').forEach((L, i) => { if (re.test(L)) out.push(`${f.split('/').pop()}:${i + 1}`); });
  return out;
};

let 改动 = 0;
for (const [id, 旧, 处理, 新] of 修) {
  const e = j.entries.find((x) => x.id === id);
  if (!e) { console.log(`❌ 找不到 entry ${id}`); process.exit(1); }
  const i = e.patterns.indexOf(旧);
  if (i < 0) { console.log(`❌ ${id} 里已无该 pattern（可能已修过）：${旧}`); 改动++; continue; }
  // 🔴 只有「重锚 / 删除幽灵」两类才要求旧 pattern **必须 0 命中** ——
  //    「删除2」处理的是**锚错了地方**的 pattern（它有命中、但命中的是正确记录），守卫不适用。
  if (处理 !== '删除2' && 命中(旧).length) { console.log(`⛔ ${id} 的「${旧}」居然有命中 —— 不该按幽灵处理，中止`); process.exit(1); }

  if (处理 === '删除' || 处理 === '删除2') {
    e.patterns.splice(i, 1);
    const 仍 = e.patterns.length;
    console.log(`🗑️  [${id}] 删除幽灵锚「${旧}」（全册 grep 无此文本）→ 余 ${仍} 个`);
  } else {
    const 试 = 命中(新);
    if (!试.length) { console.log(`❌ 新锚「${新}」也匹配不到 —— 中止`); process.exit(1); }
    // 🔴 验证 replace 真的生效（批次 146 之前的教训：replace 静默失败却报告成功）
    const 前 = JSON.stringify(e.patterns);
    e.patterns[i] = 新;
    if (JSON.stringify(e.patterns) === 前) { console.log(`❌ ${id} 替换未生效`); process.exit(1); }
    console.log(`🔁  [${id}] 重锚 →「${新}」命中 ${试.length} 处：${试.join(', ')}`);
  }
  改动++;
}

// 追加说明
const note = '\n\n🔴 **批次 146 清理**：本条原有若干个 pattern **在全册一个字都匹配不到**（幽灵锚），而旧的门只判「entry 是否至少命中一处」，因此它们**一直静默通过、实际没有覆盖任何一处**。已逐条 grep 定案：写法变了的**重锚到现形**，目标文本已全册不存在的**删除**，并把「逐 pattern 幽灵检测」加进 `jimeng-backfill-gate.mjs`（配阳性对照用例 ③\'）。';
for (const [id, , 处理] of 修) {
  const e = j.entries.find((x) => x.id === id);
  if (typeof e.pattern_note !== 'string') e.pattern_note = '';
  if (!e.pattern_note.includes('批次 146 清理')) e.pattern_note += note;
}

fs.writeFileSync(F, JSON.stringify(j, null, 1) + '\n');
console.log(`\n处理 ${改动} 条；台账现存 ${JSON.parse(fs.readFileSync(F, 'utf8')).entries.length} 条 entry`);
