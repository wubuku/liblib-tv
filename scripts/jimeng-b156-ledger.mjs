// 批次 156：给 scripts/jimeng-refuted-claims.json 追加第 70 条
//
// 🔴 规矩：① 动手前先验证原文件逐字等于 JSON.stringify(j,null,1)+'\n'
//        ② 改完必须把**前 69 条逐条**与改前快照比对，确认没被碰过。
//        ③ **不许用 `git checkout <file>` 回滚**（本项目禁用清单）—— 本脚本是确定性的，
//           跑第二次就会撞上「已存在」而拒绝，所以回滚请用 write 工具或重跑本脚本。
//
// 🔴🔴 **pattern 里不能出现 `**`**：`jimeng-backfill-gate.mjs` 把 pattern 直接 `new RegExp(pat)`，
//    而 `**` 在正则里是「Nothing to repeat」—— 本轮第一版就因为抄了带 `**` 的原句，
//    **让 10 道门里的第 2 道直接 SyntaxError 崩掉**。改锚不含强调标记的片段。
//    📌 同一类「自触发」本项目已踩三次：alt 里的 `**`（manifest 门判红）、
//       跨行引用（死链门判红）、本轮的 pattern 里的 `**`（回填门崩）。
//       根因都是同一个：**把会被门扫到的字面量，逐字抄进了被扫的地方**。
import fs from 'node:fs';
const P = new URL('./jimeng-refuted-claims.json', import.meta.url);
const raw = fs.readFileSync(P, 'utf8');
const j = JSON.parse(raw);
if (raw !== JSON.stringify(j, null, 1) + '\n') { console.error('❌ 原文件序列化不符，中止'); process.exit(1); }
if (j.entries.some((e) => e.id === 'subject-save-target-account-level')) {
  console.log('ℹ️ 第 70 条已存在，跳过（幂等）'); process.exit(0);
}
const 前 = JSON.parse(JSON.stringify(j.entries));

j.entries.push({
  id: 'subject-save-target-account-level',
  label: '把「保存到主体库」当成「点一下就保存」，并把它的落地位置与阻塞原因都记错（写进项目资产库的主体页 / 因「空态」而撤不回）',
  patterns: [
    '批次 156 订正本页此前的说法',
    '「保存到主体库」不是一步，是两步；本手册只执行到第二步的「保存可用」，不点「保存」',
    '在没有单独授权前不执行',
    '批次 156 订正并部分关闭',
    '它写的不是项目资产库那个「主体」页',
  ],
  pattern_note: '五条 pattern 全部避开强调标记，因为回填门把 pattern 直接当正则编译（见文件头）。第 1、4 条锚在订正标记所在行 —— 沿用批次 155 立过的规矩：整段替换型订正要锚订正、不能锚旧字，否则订正一删就变幽灵。第 2 条是新写的两句式结论，第 3 条是旧文原样保留的折行片段（它上下三行内就有删除线与「订正并部分关闭」标记），第 5 条是新增的归因订正句。动手前五条已逐条 grep -F 核过全册各恰好命中 1 处。',
  refuted_in: '批次 156（SOURCE_OBSERVATIONS 新增 §4.79.1–§4.79.5；就地订正 10-tasks/subject-node.md 两处 + 新增第 5 小节与 4 张截图 + 20-reference.md 主体行 + 30-concepts.md 三处 + AUDIT.md / PROGRESS.md / FINAL-REPORT.md 批次 156 小节）',
  reason: '三处都错，且最关键的那处不是读错，是自己把自己测没了。① 它不在浮动工具条的「工具」菜单里 —— 那个菜单 240×204 逐字只有「编辑 / 消除笔 / 裁剪 / 宫格切分 / 标注」（第一行「编辑」是分组标题、不是 menuitem，所以数 menuitem 得 4、数 innerText 得 5，两者都不是「菜单项数」）；PROGRESS.md 两处早就写明它在 canvas-context-menu，而本批连写三个脚本都按错误前提排期、且三个都没报错。② 它不是一步，是两步：点菜单项不保存，而是弹 subject-export-confirm-dialog 548×688，名称必填（maxlength=20、计数器 0 / 20）、「保存」空态 aria-disabled 与 data-disabled 双双为 true 并附逐字原因「保存前请输入名称。」，填名后计数器变 6 / 20、两个 disabled 双双消失，所以名称是唯一必填门槛；填了名字不点保存、按 Esc 关掉则零残留。该对话框带 14 个 subject-export 前缀 testid，全册 testid 名单从 84 个增至 98 个、此前一个都没有。③ 落地对象记错了：它写的是账号级 Dreamina Subjects（对话框英文副标题逐字 Review the Subject before saving it to Dreamina Subjects.），不是项目资产库那个「主体」页 —— 后者逐字是 Import assets Choose assets from Dreamina and import them into this canvas. 开头的导入面板，是导入源。本轮对账：把对话框一路走到「保存可点」再重开项目资产库主体页，逐字完全等于基线（「没有可用主体」仍在、canvas-subject-import-empty 仍在、零 img 元素），所以共享数据未被改动、不需要撤回。④ 阻塞理由该换但没取消：没法干净撤回仍然成立，但归因从「空态」改成「本画布 UI 无管理或删除账号主体的入口」—— 已逐路排除：全局 chrome 穷举 25 个可点物里命中「主体 / 账号 / 设置」的只有左栏第 6 个（40×40@16,403，它建的是主体节点）；顶栏唯一账号口是 canvas-user-menu-trigger（aria 逐字「用户菜单」），打开后只有 6 项（帮助中心 / 使用手册 / 快捷键 / AI生成水印设置 / 即梦CLI / 新功能许愿）。📌 立规 19：判「这个按钮点了有没有反应」之前，先排除「反应被我自己的收尾动作抹掉了」—— 156-h 点完菜单项连按 3 次 Esc 把二次确认对话框关掉了，156-i 重开主体库读到基线，差点把「被自己关掉」写成「功能无效」，最后靠 156-j 的点前点后全 DOM 差分（新增 21 个元素）才把它逼出来。📌 同批附一条新读数：右键菜单里「保存到主体库」的 aria-label 逐字是「将 b22-upload 保存到主体库」，即 aria 会带节点名，所以按 aria 逐字找这一项会漏掉所有名字不同的节点。',
});

fs.writeFileSync(P, JSON.stringify(j, null, 1) + '\n');
const 后 = JSON.parse(fs.readFileSync(P, 'utf8')).entries;
const 前69 = JSON.stringify(前) === JSON.stringify(后.slice(0, 前.length));
console.log('写入后条目数:', 后.length, '| 前 ' + 前.length + ' 条逐条未变:', 前69);
if (!前69) { console.error('❌ 前序条目被动过'); process.exit(1); }
console.log('✅ 第 70 条已追加，id =', 后[后.length - 1].id);
