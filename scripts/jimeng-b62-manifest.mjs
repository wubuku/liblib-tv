// 从 Markdown 里**逐字**抽 alt 生成 manifest 条目 ——
// alt 审计门要求 manifest 的 `alt:` 与正文 `![](...)` 内的 alt **逐字完全一致**，
// 手抄必错，所以这里反过来以正文为准。
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execSync } from 'node:child_process';

const DOC = 'docs/user-manual/jimeng-canvas';
const md = readFileSync(`${DOC}/10-tasks/ai-agent-drawer.md`, 'utf8');
const MAN = `${DOC}/screenshots/manifest.yml`;

// 文件 → { task_id, step, visible_text, verified_locator }
const META = {
  '62-agent-empty.png': { step: 1, visible_text: '探索更多专业创作模式',
    loc: '点右下「与 AI 对话」(aria 逐字「与 AI 对话」118×34@1149,673) → 侧栏 ASIDE[data-testid=canvas-feature-sidecar] aria="Agent" 400×696@(868,12) 展开（canvas-agent-panel 398×694@(869,13)，49 个可见元素）→ 空态：canvas-agent-session-heading「探索更多专业创作模式」338×27@(899,213) + canvas-agent-session-modes 338×140@(899,252) 内 5 个 canvas-agent-mode-action（/ 视频反解 105×36@959,260、/ 创作分镜 105×36@1072,260、/ 全流程广告片导演 157×36@933,304、/ 剧本开发 105×36@1098,304、/ 剧情短片 105×36@1016,348）→ 输入卡 canvas-agent-session-composer 390×164@(873,539) + 底部操作行四项 → 裁切 clip={x:860,y:8,w:412,h:700}。积分 805 未变' },
  '62-agent-collapsed-shell.png': { step: 3, visible_text: '与 AI 对话',
    loc: '展开态点 canvas-agent-session-collapse（aria 逐字「收起」36×36@1219,23）→ **侧栏没有消失**：变成 200×348@(1068,360)，pointer-events=none，内部可见元素 0 个、canvas-agent-panel 不存在。零成本穿透对照：取展开态同一批 5 个侧栏内坐标，elementFromPoint 展开态 5/5 命中侧栏内、折叠态 0/5 ⇒ 不遮挡画布的机制是 pointer-events:none 而非「被关掉」。裁切 clip={x:1040,y:340,w:240,h:380}，画面上只剩画布网格与右下角按钮。积分 805 未变' },
  '62-agent-skill-picker.png': { step: 5, visible_text: '搜索技能',
    loc: '空态点底部 canvas-agent-skill-trigger（aria 逐字「使用技能」90×32@926,654）→ 弹出 canvas-agent-skill-picker，**role=dialog**，360×372@(896,274)，**不在侧栏内**（挂在 canvas-agent-panel 之外）→ 搜索框 canvas-agent-skill-search 352×36@(900,278) 占位逐字「搜索技能」→ 列表 canvas-agent-skill-picker-list 356×284@(900,318)，scrollHeight 452 / clientHeight 284 ⇒ 可滚动，8 行各 348×52、行距 56 → footer canvas-agent-skill-picker-footer 352×44@(900,602) 逐字「管理技能」（**未点**，会跳技能管理页）→ 裁切 clip={x:860,y:8,w:412,h:700}。8 项中只有「剧本开发」无「官方」标签。积分 805 未变' },
  '62-agent-skill-search.png': { step: 5, visible_text: '海报设计',
    loc: '在技能选择器的搜索框里输入「海报」（先断言 elementFromPoint 落点属于该 input）→ 8 行过滤成 **1 行**「海报设计·官方」，搜索框右侧浮出圆形 ✕ 清空钮 → 退格两下复测 → 恢复 8 行。裁切 clip={x:860,y:8,w:412,h:700}。积分 805 未变' },
  '62-agent-skill-chip.png': { step: 4, visible_text: '视频反解',
    loc: '点空态 chip canvas-agent-mode-action（aria 逐字「/ 视频反解」105×36@959,260）→ **不弹任何浮层**；抽屉面板 400×696@(868,12) 全程一格未变 → 编辑器 .tiptap.ProseMirror[contenteditable=true] 内容变为「视频反解」，innerHTML 为 <p><span class="react-renderer node-composerChip …">，可见 chip 84×20@(890,556)（data-testid=agent-skill-chip）→ 同时 canvas-agent-session-heading 与 canvas-agent-session-modes **整块从 DOM 消失**（空态推荐区仅在输入卡为空时出现）→ 裁切 clip={x:860,y:8,w:412,h:700}。积分 805 未变。详见 SOURCE_OBSERVATIONS §3.81.2' },
  '62-agent-slash-menu.png': { step: 6, visible_text: '/ 视频反解',
    loc: '在空输入框按「/」（按前先断言落点在 canvas-agent-session-composer 之内 —— 输入框内 elementFromPoint 命中的是 col-start-1 占位符层，**不是** contenteditable 本身，二者是兄弟）→ 浮层 agent-skill-menu **role=listbox** 360×361@(878,187)，**与「使用技能」弹的 canvas-agent-skill-picker 不是同一个元素** → 密集采样 9 点(t=0…3600ms)：t=0 内容逐字「加载中 加载中」，t=300ms 起换成 8 条技能，全程 skill-picker 未出现 → 裁切 clip={x:860,y:8,w:412,h:700}。积分 805 未变。详见 §3.81.3 / §3.81.9' },
  '62-agent-at-menu.png': { step: 7, visible_text: '添加参考',
    loc: '在空输入框按「@」→ 浮层 **role=listbox 且无 data-testid**，240×296@(770,252)，**向左溢出到抽屉之外**（抽屉左沿 868）→ 标题逐字「添加参考」232×32@(774,256) + **5 个** role=option 各 232×48、行距 52：主体(288) aria-selected=true / 图片(340) / 视频(392) / 音频(444) / 文本(496)，每项右侧 32×32 的 ›。⚠️ 前一轮按 innerText 行数误数成 6 项（把标题当选项），且首张截图 clip 从 x=860 起把菜单左侧 90px 切掉 ⇒ 补拍 clip={x:700,y:180,w:580,h:460}。积分 805 未变。详见 §3.81.5' },
  '62-agent-expanded.png': { step: 2, visible_text: '新会话',
    loc: '折叠态点「与 AI 对话」按钮 → 侧栏恢复 400×696@(868,12)（pointer-events:auto，49 个可见元素）→ 取侧栏内 5 个坐标做 elementFromPoint 基线读数，5/5 命中侧栏内（与折叠态 0/5 构成对照）→ 裁切 clip={x:860,y:8,w:412,h:700}。积分 805 未变' },
};

const entries = [];
const missing = [];
for (const [file, meta] of Object.entries(META)) {
  const re = new RegExp(`!\\[([^\\]]*)\\]\\(\\.\\./screenshots/${file.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\)`);
  const m = re.exec(md);
  // 正文里已不再引用的图（如同字节重复、被合并掉的那张）→ 跳过，不入 manifest。
  if (!m) { console.log('  跳过（正文已不引用）:', file); continue; }
  const abs = `${DOC}/screenshots/${file}`;
  if (!existsSync(abs)) { missing.push(file + '（截图文件不存在）'); continue; }
  const sha = createHash('sha256').update(readFileSync(abs)).digest('hex');
  entries.push({ file: `screenshots/${file}`, task_id: 'ai-agent-drawer', step: meta.step,
    route: '/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f',
    viewport: '1280x720@2x', locale: 'zh-CN',
    captured_at: '2026-10-01T23:55:00+08:00', verified_locator: meta.loc,
    visible_text: meta.visible_text, alt: m[1], sha256: sha });
}
if (missing.length) { console.error('ABORT: ' + missing.join(' | ')); process.exit(1); }

// alt 里不能有会破坏 YAML 的东西；也不能带引号（审计门要求逐字、无引号）
for (const e of entries) {
  // YAML plain scalar 的真正禁区：行首指示符、': '（键值对）、' #'（注释）、换行。
  // 其余字符（@ ! * & % 等出现在行中间）在 plain scalar 里是合法的。
  if (/^[\[\]{}#&*!|>'"%@`,]/.test(e.alt) || e.alt.includes(': ') || e.alt.includes(' #') || /[\r\n]/.test(e.alt) || e.alt !== e.alt.trim()) {
    console.error('alt 会破坏 YAML plain scalar:', e.file, JSON.stringify(e.alt.slice(0, 60))); process.exit(2);
  }
  if (e.alt.length > 400) { console.error('alt 过长:', e.file, e.alt.length); }
}
const yaml = entries.map((e) => `\n  - file: ${e.file}\n    task_id: ${e.task_id}\n    step: ${e.step}\n    route: ${e.route}\n    viewport: ${e.viewport}\n    locale: ${e.locale}\n    captured_at: ${e.captured_at}\n    verified_locator: '${e.verified_locator}'\n    visible_text: ${e.visible_text}\n    alt: ${e.alt}\n    sha256: ${e.sha256}\n`).join('');
if (!readFileSync(MAN, 'utf8').endsWith('\n')) { console.error('manifest 结尾缺换行，先修'); process.exit(3); }
writeFileSync(MAN, readFileSync(MAN, 'utf8') + yaml);
console.log('追加', entries.length, '条 →', MAN);
for (const e of entries) console.log('  ', e.file, '| alt', e.alt.length, '字 | sha', e.sha256.slice(0, 12));
console.log('manifest 现共', execSync(`grep -c "^  - file:" ${MAN}`).toString().trim(), '条');
await b_close();
async function b_close() {}
