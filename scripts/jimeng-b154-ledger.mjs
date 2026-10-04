// 批次 154 —— 台账加第 68 条
//
// 🔑 动手前的两条硬检查（批次 150 踩过「台账被整份重排」）：
//   ① 原文件必须**逐字等于** `JSON.stringify(j, null, 1) + '\n'` —— 否则说明序列化约定变了，先查清再动；
//   ② 加完必须**前 67 条逐条未变**（比 JSON 序列化后的字符串，不是比对象引用）。
//
// 📌 本条**故意不含** `240×244`：那不是被推翻的结论（见 §4.77.3 自身失误 4），
//    是我把「一个族的读数」当成「通例」又反过来指责它 —— 错的是我，不是手册。
import fs from 'node:fs';

const F = new URL('./jimeng-refuted-claims.json', import.meta.url);
const raw = fs.readFileSync(F, 'utf8');
const j = JSON.parse(raw);

// ---- 硬检查 ①：序列化约定 ----
if (raw !== JSON.stringify(j, null, 1) + '\n') {
  console.log('⛔ 原文件不等于 JSON.stringify(j,null,1)+\"\\n\"，序列化约定已变 —— 中止');
  process.exit(1);
}
console.log('✅ 硬检查①：原文件逐字等于约定序列化');
const 前 = JSON.parse(raw);
const 前条数 = 前.entries.length;
const 前67 = JSON.stringify(前.entries);
console.log('   现有条数 =', 前条数);

// ---- 追加第 68 条 ----
j.entries.push({
  id: 'sec449-triage-table-4-rows-stale',
  label: '把「SOURCE_OBSERVATIONS §4.49『全灭 testid 存活率普查』分诊表」当成**当前状态**来读 —— 该表有 4 行写的是**已经过期**的结论：3 行挂着「需单独授权」（授权后来解除了），1 行挂着**已被推翻**的旧结论（原文出现在 SOURCE_OBSERVATIONS.md §4.49 主产出 C 的那张分诊表）',
  patterns: [
    '点开即进生成流程，需单独授权',
    '批次 112 六次尝试都造不出来',
    '跳转型，\\*\\*需单独授权\\*\\*',
  ],
  pattern_note: '🔑 **这一条登记的是「台账漂移」，不是「读数错」。** 三个 pattern 锚的是分诊表里**原结论的字面**：加订正时用的是「原文加删除线 + 同行写订正」的形式（批次 153 定的规矩：回填门**逐行匹配**，所以订正必须并进原文那一行，锚旧字会变幽灵）。三个 pattern 动手前已逐条 grep 验证**全册恰好命中 1 处**。📌 第 3 个 pattern 写成 `跳转型，\\*\\*需单独授权\\*\\*`（转义星号）而不是裸文本 —— 表里的 `**` 是 markdown 强调标记，回填门拿 pattern 当**正则**跑，裸 `**` 会被当成量词。⚠️ 若将来有人把订正删掉又保留旧结论，这三个 pattern 会同时变幽灵 ⇒ 门立刻报红。',
  refuted_in: '批次 154（纯静态元审计 `jimeng-b154-meta.mjs` 逐行比对分诊表与手册别处的实测记录；就地改写 SOURCE_OBSERVATIONS.md §4.49 那 4 行 + 新增 §4.77 + AUDIT.md 批次 154 小节 + PROGRESS.md 批次 154 小节）',
  reason: '**分诊表本身是有价值的工具，但它会静默过期，而没有任何机制报警。** 2026-10-04 批次 154 做了一次纯静态元审计：逐行读分诊表，再看手册**别处**是否已有这些 testid 的实测记录 —— 9 行里 **4 行**是漂移。① `generation-form` / `generation-mention-panel` / `generation-mention-submenu` / `generation-source-picker-chip` / `generation-source-picker-close`（5 项）与 `canvas-source-picker-canvas-frame` / `-mask`（2 项）都写着「点开即进生成流程，**需单独授权**」，而 `prepare-generation.md:196,230`、`20-reference.md:711,751` 早就有逐字读数；2026-10-04 目标更新（登录的是**测试帐号**，只要**不执行真实生图/生视频**就可以做有副作用的 CRUD）**解除了该授权**，本批当场验成 7 项（`generation-mention-submenu` 要再点类别才出，本轮未点，**保留在表里**）。② `workspace-project-info-dialog` 写着「跳转型，**需单独授权**」，`canvas-context.md:244,309` 早有读数，本批复现 `800×546@240,87` 并**第 5 次**与手册逐字一致。③ 🔴 `audio-node-uploading` 写着「**批次 112 六次尝试都造不出来**」，而**批次 109（早于 112）就已验成**（`20-reference.md:1266` 逐字两段 `正在上传音频 0%` → `正在处理上传内容…`）—— 这是**批次 112 的结论被批次 109 推翻却没有回填到本表**，属纯粹的台账漂移，本批未复测。📌 **立规：任何「未验 / 需授权 / 造不出来」的状态型记录都是会过期的**；写它的时候就要同时写下「什么条件下该重新分诊」，否则半年后没人知道它说的是哪一天的状态。',
});

// ---- 硬检查 ②：前 67 条逐条未变 ----
const 后 = JSON.parse(JSON.stringify(j));
if (后.entries.length !== 前条数 + 1) { console.log('⛔ 条数不对'); process.exit(1); }
if (JSON.stringify(后.entries.slice(0, 前条数)) !== 前67) {
  console.log('⛔ 前 ' + 前条数 + ' 条被改动了 —— 中止');
  process.exit(1);
}
console.log('✅ 硬检查②：前 ' + 前条数 + ' 条逐条未变');

// ---- 写回，并立刻复验能原样解析回来 ----
fs.writeFileSync(F, JSON.stringify(j, null, 1) + '\n');
const 回 = JSON.parse(fs.readFileSync(F, 'utf8'));
console.log('✅ 已写回，条数 =', 回.entries.length, '| 末条 id =', 回.entries[回.entries.length - 1].id);
console.log('   往返逐字一致 =', fs.readFileSync(F, 'utf8') === JSON.stringify(j, null, 1) + '\n');
