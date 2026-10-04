// 批次 159 —— 台账追加第 71 条（不改动前 70 条任何一字）
// 🔴 纪律：改之前先验证原文件**逐字**等于 `JSON.stringify(j, null, 1) + '\n'`；
//    改之后比前 70 条逐条未变；每条 pattern 先 grep -F 核过**至少命中一处**。
//    任何一条对不上就**不写回**。
import fs from 'node:fs';

const P = 'scripts/jimeng-refuted-claims.json';
const 原文 = fs.readFileSync(P, 'utf8');
const j = JSON.parse(原文);
const 条目 = j.entries;
const 前 = 条目.slice(0, 70);

console.log('原条目数 =', 条目.length);
const 规范 = JSON.stringify(j, null, 1) + '\n';
console.log('原文件逐字等于规范序列化 =', 原文 === 规范);
if (原文 !== 规范) { console.log('⛔ 序列化不一致，拒绝写入（不改别人的格式）'); process.exit(1); }
if (条目.length !== 70) { console.log('⛔ 条目数不是 70，拒绝写入（防重复追加）'); process.exit(1); }

const 新条目 = {
  id: 'blocking-one-stream-key-is-enough',
  label: '认为只要拦下「播放取流 key」并强制重新取流，卡片就会变成「音频播放失败」态；并且把「重载页面」当成必要步骤',
  patterns: [
    '卡片多半还不会变红',
    '把兜底链也拦掉',
    '同一个素材有不止一条取流 URL',
    '别加「重载页面」这一步',
    '拦满 2 条'
  ],
  pattern_note: '五条 pattern 全部避开强调标记（回填门把 pattern 直接当正则编译，见文件头），且都锚在**订正句本身**而不是旧字上 —— 整段替换型订正锚订正、不能锚旧字，否则订正一删就变幽灵。动手前五条已逐条 grep -F 核过，**各恰好命中 1 处**，且五处都在同一次订正的上下文里（三行内有「不能省」「别加」「🔴🔴」等内联标记）。',
  refuted_in: '批次 159（SOURCE_OBSERVATIONS.md §4.82；就地改写 10-tasks/media-playback.md「怎么自己造出这个状态」第 4/5 步 ＋「重试播放的两个分支」补注 ＋ 20-reference.md 三条，截图 119，manifest 148 → 149）',
  reason: '2026-10-05 批次 159 实测推翻，三处都错。① **同一个素材有不止一条取流 URL**：拦掉一条之后应用立刻换一条重发（第 1 段 32 位 hex、第 2 段 8 位 hex、末段 32 位 key 三段全变），播放被自动兜底接上，界面上毫无异常 —— 典型症状是「拦截报了 blockedReason: "inspector" 命中、界面却仍然正常播」。复现失败态必须把兜底链逐条拦干净（循环 a.load() → 采新冒出来的 type: Media URL → 把它的 key 也加进 Network.setBlockedURLs，直到不再出现新 URL），本轮拦满 2 条后失败态才出现，累计 blockedReason 3 次。② 拦截 pattern 要用 tos-cn-v-148450/ 后面那一段 32 位混合大小写 key（正是手册早已记录的「播放取流 key」），不是第一个 32 位 hex —— 批次 158 按第 1 段拦，没打中；这一条是翻批次 110 的脚本（jimeng-b110c.mjs:75 的正则）用 git 考古查出来的。③ 不要重载页面：批次 110 全程没重载，是在同一页面里 audio.load() 强制重新取流；重载后节点变成逐字「Not selected.」，而播放钮只在选中态渲染，后续取点会读出 null。复现读数与批次 110 记录逐条吻合：节点 innerText 逐字相同、audio-playback-error 192×192、内层 DIV ＋ role="alert" 的 DIV ＋ BUTTON[aria-label="重试播放音频"]、audio 元素整个从 DOM 消失、时间读数 0 个、资源账纹丝不动仍 1 ready / 0 failed；恢复分支也复现（readyState 4、duration 4.032、paused false、currentTime 0.02、按钮直接变 Pause）。探针 scripts/jimeng-b159d.mjs，6/6 断言通过。',
};

条目.push(新条目);
const 新文 = JSON.stringify(j, null, 1) + '\n';
const 核 = JSON.parse(新文).entries;
const 前未变 = 前.every((z, i) => JSON.stringify(核[i]) === JSON.stringify(前[i]));
console.log('追加后条目数 =', 核.length);
console.log('前 70 条逐条未变 =', 前未变);
if (!前未变) { console.log('⛔ 前 70 条有变动，拒绝写入'); process.exit(1); }
if (fs.readFileSync(P, 'utf8') !== 新文) fs.writeFileSync(P, 新文);
console.log('✅ 已写入第 71 条：', 核[70].id);
process.exit(0);
