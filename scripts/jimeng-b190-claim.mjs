// 批次 190：给 scripts/jimeng-refuted-claims.json 追加第 105 条
// 靶子：duplicate-delete-history.md 那句「⌘V 粘出的是选中节点的副本（内容与被复制节点一致）」。
// 这句话是**只看了节点数**得出的 —— 批次 190 用哨兵重测，粘出来的是一个内容完全不同的文本节点。
import fs from 'node:fs';

const P = new URL('./jimeng-refuted-claims.json', import.meta.url);
const d = JSON.parse(fs.readFileSync(P, 'utf8'));

if (d.entries.some((e) => e.id === 'paste-v-is-a-copy-of-the-selected-node')) {
  console.log('已存在，跳过');
  process.exit(0);
}

d.entries.push({
  id: 'paste-v-is-a-copy-of-the-selected-node',
  label: '以为按 ⌘V 粘出来的是「当前选中节点的副本」（内容与被复制节点一致）',
  patterns: ['粘贴出的是选中节点的副本'],
  pattern_note:
    'pattern 取自 `10-tasks/duplicate-delete-history.md:257` 那句**已被删除线包住的原文**。' +
    '全册命中 1 处（`10-tasks/duplicate-delete-history.md`），命中行下一行就是 `🔴 批次 190 推翻…`，' +
    '满足回填门「±3 行内有订正标记」。串里没有 `* + ? [ ] { } | ^ $ \\ .` 任何 regex 元字符，' +
    '作为正则逐字匹配、无误撞。📌 这个 pattern 是**故意选短的**：长的版本（含括号里的「内容与被复制节点一致」）' +
    '会因为我在同页改写句式而失配，而台账要的是「指向那句错话」，不是「指向某一行」。',
  refuted_in:
    '批次 190（SOURCE_OBSERVATIONS.md §4.113.3；10-tasks/duplicate-delete-history.md 粘贴一节**就地加删除线**并换成哨兵三步读数表 + 第 177 张截图；30-concepts 新增立规 63）',
  reason:
    '2026-10-05 批次 190：原句来自批次 178 的复测，而那一轮**只比较了节点数**（5→6），' +
    '**从来没读过粘出来的东西是什么**。🔴 本轮用**哨兵**重测，结论反过来：' +
    '`navigator.clipboard.writeText(\'JIMENG-B190-SENTINEL\')` 写入成功后，选中一个视频节点按 ⌘C（剪贴板内容**不变**），' +
    '再按 ⌘V —— 节点数 `76→77`，**新节点的 aria 逐字是 `文本 node: JIMENG-B190-SENTINEL`**。' +
    '⇒ **⌘V 粘出来的是「剪贴板里的纯文本」，与当前选中了谁完全无关**。' +
    '📌 哨兵字符串逐字出现在**应用自己数据模型里**（节点 aria），比 `navigator.clipboard.read()` 更硬 —— ' +
    '后者在本轮 CDP 环境下**四次全部 3 秒超时**；按纪律记「读不到」，**没有**把超时当成「剪贴板是空的」' +
    '（这正是立规 52 的反向用法：否定读数不配正向守卫就会被当成肯定）。' +
    '⚠️ 顺带推翻另一条相邻表述：⌘C **触发 `copy` 事件却什么都不写**（批次 182/183），本轮又补上「⌘C 之后剪贴板内容不变」' +
    '这条直接读数 ⇒ **⌘C / ⌘D 都不能用来复制节点，要复制请走右键菜单的「复制副本」**。' +
    '⇒ 实操后果：本页原有的「关键操作仍建议用复制副本 ⌘D」这条建议**方向对、理由错** —— ' +
    '不是「⌘V 不稳定」，而是**⌘V 根本不是「复制节点」的等价物**。📌 另记一条**未验证现象**：三轮都观察到按 ⌘V 之后画布缩放自己变了' +
    '（26%→50% / 26%→42% / 26%→43%），**机制未验证**（三轮目标节点与落点都不同），只记现象、不下断言。',
});

fs.writeFileSync(P, JSON.stringify(d, null, 1) + '\n');
console.log('entries =', d.entries.length);
