// 批次 155 —— 台账加第 69 条
// 🔑 硬检查同批次 154：① 原文件逐字等于约定序列化 ② 加完前 68 条逐条未变。
// 📌 四个 pattern 全部锚在**订正标记那一行**，不是锚旧字 —— 因为这四处都是「整段替换型」，
//    锚旧字会立刻变幽灵（批次 74 踩过、批次 153 立过规矩）。动手前已逐条 grep 验证全册恰好 1 处。
import fs from 'node:fs';

const F = new URL('./jimeng-refuted-claims.json', import.meta.url);
const raw = fs.readFileSync(F, 'utf8');
const j = JSON.parse(raw);
if (raw !== JSON.stringify(j, null, 1) + '\n') { console.log('⛔ 序列化约定已变 —— 中止'); process.exit(1); }
console.log('✅ 硬检查①：原文件逐字等于约定序列化｜现有条数 =', j.entries.length);
const 前条数 = j.entries.length;
const 前 = JSON.stringify(j.entries);

j.entries.push({
  id: 'timeline-rail-button-and-export-oneclick',
  label: '把「左栏那个「时间线」按钮走不通（批次 107 点 24 轮无新节点）」与「点击 导出时间线 导出整条时间线（一句话一步到位）」当成事实（原文出现在 10-tasks/timeline-node.md 的「自建时间线节点的完整读数」小节、「7. 导出时间线」小节与「已验证说明」末尾），另外把批次 111 清单里那句「**20 个 testid**」的数量与「节点 266×46（60% 时）」的屏上读数当成事实',
  patterns: [
    '批次 155 订正：「左栏那个「时间线」按钮本轮仍未走通」是错的',
    '点「导出时间线」不是导出，它先弹一个「选目标/选格式」菜单',
    '下面这份清单实际是 21 个，不是 20 个',
    '导出时间线的状态（2026-10-04 批次 155 更新）',
  ],
  pattern_note: '🔑 **四处都是「整段替换型」订正** ⇒ pattern 一律锚在**订正标记那一行**（批次 74 踩过、批次 153 立过规矩：锚旧字会立刻变幽灵，回填门会误报）。四个 pattern 动手前已逐条 `grep -F` 验证**全册恰好命中 1 处**。📌 第 4 条锚的是「已验证说明」末尾那一行：它**不是**说导出已完成，而是把状态从「需单独授权」改成「菜单层已验成、最终导出仍未执行」—— 锚它是为了让「这一行的结论被改动过」这件事可被门发现。⚠️ 若将来有人把订正删掉又写回旧结论，四个 pattern 会同时变幽灵 ⇒ 门立刻报红。',
  refuted_in: '批次 155（SOURCE_OBSERVATIONS 新增 §4.78.1–§4.78.4；就地改写 10-tasks/timeline-node.md 三处 + 订正批次 111 的数量与屏上读数 + AUDIT.md 批次 155 小节 + PROGRESS.md 批次 155 小节）',
  reason: '**三条结论都被实测推翻，其中两条的错法很典型。** ① **左栏「时间线」键能建节点**：带建-删护栏重做（建前 76 == 预期基线、建前 0 选中、建前无组、建后差集恰好 1、新节点恰好 .selected），**护栏 5/5 全过**（76 → 77）。批次 107 之所以得出相反结论，是**那一轮没有护栏、判据只有「建完数一下节点」** —— 在 76 节点、别人也在改的共享画布上，「节点数没变」有太多可能。📌 **共享画布上判「某个操作生效了吗」不能只判总量变没变**。② **点「导出时间线」不是导出**：实测**没有 download 事件**、但浮层数 0 → 1；那一层是 `[role=menu][aria-label="导出时间线"]` **200×292@713,331**，画面上 6 项 —— 导出为 MP4（**空时间线禁用、灰字**）／导出为 XML／分隔线／导出到剪映／DaVinci Resolve／Premiere／Final Cut Pro，`Esc` 一次可关。⚠️ **最终导出仍未执行**（会产出对外文件），但**理由从「需单独授权」换成了「本轮只验到菜单层」** —— 前者因 2026-10-04 目标更新已不成立。③ **批次 111 的「20 个 testid」数错了**（那一行列的名字实际 21 个；本轮实测 21 个、逐条对上缺 0 多 0），且它的「节点 266×46（60% 时）」是错读 —— 同一段自己还记着节点内有个 `添加素材到时间线 512×39` 的按钮，**266 宽的容器装不下 512 宽的子元素**；用它的另一档 `552×95@46%` 算得 canvas `1200×206.5`，而 `266×46@60%` 算得 `443×76.7`，**两者差 2.7 倍**。本轮实测 `720×124.2@60%` ⇒ canvas `1200×207`，与前者逐字吻合、也与批次 119 的 `720×124` 吻合。📌 **真相是 canvas 恒 `1200×207`；批次 119 的读数是对的。**④ 顺带记一条**新读数**：时间线节点的静音钮 `aria` 逐字**恒为「静音」不变**，翻转的是 **`aria-pressed`** —— 与媒体节点（`video-node-mute-toggle` 翻 aria 文案 `Unmute video` ↔ `Mute video`）**是两套语义**，「静音了吗」不能一律看 aria 文案。',
});

const 后 = JSON.parse(JSON.stringify(j));
if (后.entries.length !== 前条数 + 1) { console.log('⛔ 条数不对'); process.exit(1); }
if (JSON.stringify(后.entries.slice(0, 前条数)) !== 前) { console.log('⛔ 前 ' + 前条数 + ' 条被改动 —— 中止'); process.exit(1); }
console.log('✅ 硬检查②：前 ' + 前条数 + ' 条逐条未变');

fs.writeFileSync(F, JSON.stringify(j, null, 1) + '\n');
const 回 = JSON.parse(fs.readFileSync(F, 'utf8'));
console.log('✅ 已写回，条数 =', 回.entries.length, '| 末条 id =', 回.entries[回.entries.length - 1].id);
console.log('   往返逐字一致 =', fs.readFileSync(F, 'utf8') === JSON.stringify(j, null, 1) + '\n');
