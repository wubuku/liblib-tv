// 批次 113：登记台账第 49 条。
// ⚠️ 回填门把 pattern 当**正则**（`new RegExp(pat)`）——写盘前先自检每条。
import { readFileSync, writeFileSync } from 'node:fs';

const P = new URL('./jimeng-refuted-claims.json', import.meta.url);
const j = JSON.parse(readFileSync(P, 'utf8'));

const entry = {
  id: 'handwritten-at-voice-name-is-not-recognized',
  label: '「所以「引用音色」的正确用法是照着示例手写 `@<音色名>`」—— 原写在 audio-node-voice.md「选用 `Add`」小节末尾，SOURCE_OBSERVATIONS.md §3.49.5 也复述为「真正要用，得自己照着打 `@<音色名>`」',
  patterns: ['照着示例手写', '自己照着打 .{0,3}@<音色名>'],
  refuted_in: '批次 113（SOURCE_OBSERVATIONS.md §4.33.5）',
  reason: '**手写 `@<音色名>` 不会被转成结构化引用，落地就是纯文本。** 2026-10-03 批次 113 在音频节点的提示词框里逐段打字并读 `innerHTML`：打完 `@` 会弹出 `[data-testid="generation-mention-panel"]`（`role="listbox"` `240×192`，三个 `role="option"` 各 `232×48`：**主体 / 图片 / 音频**），但**里面没有「音色」这一类**（也没有「视频」）；补上名字后面板消失，`innerHTML` 逐字 `<p>灯塔熄灭了@生动解说</p>`，**mention 元素 0 个、ProseMirror 原子节点 0 个** ⇒ `@` 走的是**引用素材**这条路，与音色库是两套 UI。⚠️ 手册示例里的 `@父亲` / `@女儿` **在音色库里不存在**（首屏 18 个音色逐个核对：生动解说、精品有声书、桃花庵主、猪猪侠、灵动女声、苏感低音、乌萨七、唐僧、厚实男声、阳光美眉、和蔼奶奶、派星星、佩奇猪、萌娃百科、磁性男主播、清醒语录、甜美软妹、小八酱）——照抄示例必须换成库里真实存在的名字。📌 判据立规：**`innerText` 区分不了「纯文本」和「已识别的 chip」**（两者逐字相同），判「有没有被识别」只能落在 `innerHTML` 的**结构**上。',
};

let bad = 0;
for (const pat of entry.patterns) {
  try { new RegExp(pat); process.stdout.write(`  正则自检 OK  ${JSON.stringify(pat)}\n`); }
  catch (e) { bad++; process.stdout.write(`  ✗ 正则非法 ${JSON.stringify(pat)} :: ${e.message}\n`); }
}
if (bad) { process.stdout.write('⛔ 有非法 pattern，未写盘\n'); process.exit(2); }

if (j.entries.some((e) => e.id === entry.id)) {
  process.stdout.write(`ℹ️ 已存在同 id 条目（${entry.id}），不重复登记\n`);
} else {
  j.entries.push(entry);
  writeFileSync(P, JSON.stringify(j, null, 1) + '\n');
  process.stdout.write(`✅ 已登记，条目总数 ${j.entries.length}\n`);
}
