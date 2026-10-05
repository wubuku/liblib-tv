// 会话 mvs_fb62b78 · 批次 212：往订正台账追加 1 条**真推翻**。
//
// 纪律同批次 210：① 改前证明原文件逐字等于 `JSON.stringify(j,null,1)+'\n'`；
//   ② 改完逐条比对前 N 条没变。
import fs from 'node:fs';

const P = 'scripts/jimeng-refuted-claims.json';
const raw = fs.readFileSync(P, 'utf8');
const j = JSON.parse(raw);
const 规范 = JSON.stringify(j, null, 1) + '\n';
if (raw !== 规范) { console.error("⛔ 原文件不是规范形态 —— 拒绝改写"); process.exit(1); }
const 前 = JSON.stringify(j.entries);
const 前条数 = j.entries.length;
console.log(`✅ 格式逐字吻合（${raw.length} 字符，${前条数} 条）`);

j.entries.push({
  id: 'audio-desc-zero-ready-is-selected-state',
  label: '批次 178「音频未选中时描述 = `No resources: 0 ready, 0 processing, 0 failed. Not selected.`」被批次 212 推翻：那一句其实是**选中态**的文案；未选中时逐字是 `No resources. Current preview: 暂无音频. Not selected.`',
  patterns: ['会被替换成'],
  pattern_note: 'pattern 取批次 178 那句结论「**`Not selected.` 会被替换成 `Selected.`**」里的固定片段。选它是因为它在全册**逐字唯一**（grep 命中 1 处，就是 `20-reference.md` 那一行），不会误伤别处。命中行**下方两行**内已有批次 212 的收窄说明（含「推翻」「收窄」等标记词）⇒ 满足回填门「命中行 ±3 行内含订正标记」。串里没有 `* + ? [ ] { } | ^ $ \\ .` 任何 regex 元字符。📌 之所以不给 `No resources: 0 ready, 0 processing, 0 failed. Not selected.` 配 pattern：那句话对**导演台是逐字正确的**，拿它当 pattern 会把正确读数一起卷进来，语义反而不干净。',
  refuted_in: '批次 212（20-reference.md 批次 178 那张表的音频行就地订正 + 「会被替换成」那句下方加收窄说明 + 新增「批次 212」小节；SOURCE_OBSERVATIONS.md §4.113；AUDIT.md / PROGRESS.md 批次 211 之后的条目）',
  reason: '批次 178 用「搜索面板点结果」这条路径收口了「选中后描述会不会改」，但**音频那一行的未选中态文案写错了**：它记的是 `No resources: 0 ready, 0 processing, 0 failed. Not selected.`，而 `0 ready, 0 processing, 0 failed` 这个形状**只在选中态出现**。批次 179 当场就发现这条读数与稳定读数不符、记成「一次未能复现的读数」但没能定位原因。🔴 批次 212 用**归属判据 + 硬断言 `selected===1` 且选中集就是目标 id**（不依赖搜索路径）重测 6 臂、0 无效臂，逐字读出：未选中 `No resources. Current preview: 暂无音频. Not selected.`，选中后 `No resources: 0 ready, 0 processing, 0 failed. Selected.` ⇒ **两句都变**，不只是末句换词。📌 同一规律在**视频**上逐字复现（`暂无视频` → `0 ready, 0 processing, 0 failed`）；而**导演台**与**时间线**只变末句（它们没有「暂无 X」那种空预览占位，未选中就已经是资源账那一句）。📌 于是批次 179 那个「未能复现」的根因清楚了：它在**未选中**状态里找「`0 ready…`」，而那个形状只在选中态出现 ⇒ **不是刷新改的，是它找错了状态**。⇒ **规律不是「换一个词」，而是「未选中显示预览摘要、选中显示资源账」**。📌 判读提醒（已进手册）：判断选中态**不能只找 `Not selected.` 有没有**，因为媒体节点选中后整段都换了；可靠做法是看**末句**，末句在所有类型上稳定存在（文本节点除外，它压根没有这一句，因此描述选中前后逐字不变）。📌 本条的收获也是方法面的：**一次「未能复现」往往不是随机噪声，而是「你在错误的状态/错误的量上找」** —— 批次 179 的处理方式（记为未能复现、不去圆它）是对的，但**留了一个不该留的尾巴**，真因要等有人用受控两态去读才会暴露。',
});

const 前条 = JSON.parse(前);
if (JSON.stringify(前条) !== JSON.stringify(j.entries.slice(0, 前条数))) {
  console.error('⛔ 前 ' + 前条数 + ' 条被改动 —— 拒绝写出'); process.exit(1);
}
console.log(`✅ 前 ${前条数} 条逐条未变`);
fs.writeFileSync(P, JSON.stringify(j, null, 1) + '\n');
console.log(`✅ 已追加 ${j.entries.length - 前条数} 条 → 共 ${j.entries.length} 条`);
console.log('新增 id：', j.entries.slice(前条数).map((e) => e.id).join(', '));
