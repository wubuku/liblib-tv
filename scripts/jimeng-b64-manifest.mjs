// 从 Markdown 里**逐字**抽 alt 生成 manifest 条目 ——
// alt 审计门要求 manifest 的 `alt:` 与正文 `![](...)` 内的 alt **逐字完全一致**，
// 手抄必错，所以这里反过来以正文为准。
//
// 本版（批次 64）相对 b62 版的改动：
//  ① 额外读 create-first-node.md；
//  ② **跳过 manifest 里已有的 file**（b62 版会把 62/63 批重复追加一遍）；
//  ③ 收尾打印与已有 file 的交集为空，防止静默产生孤儿/重复。
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execSync } from 'node:child_process';

const DOC = 'docs/user-manual/jimeng-canvas';
const md = [
  `${DOC}/10-tasks/create-first-node.md`,
  `${DOC}/10-tasks/ai-agent-drawer.md`,
  `${DOC}/10-tasks/prepare-generation.md`,
].map((f) => readFileSync(f, 'utf8')).join('\n');
const MAN = `${DOC}/screenshots/manifest.yml`;
const manRaw = readFileSync(MAN, 'utf8');
const already = new Set([...manRaw.matchAll(/^ {2}- file: (\S+)$/gm)].map((m) => m[1]));

const META = {
  '64-upload-node-idle.png': {
    task_id: 'create-first-node', step: 1, visible_text: 'b22-upload',
    loc: '左栏点「上传」40×40@16,543（**必须用全局 `p.on(\'filechooser\')` 监听**，用 `p.waitForEvent` 会超时）→ filechooser 触发、isMultiple=true → 对画布上**常驻的隐藏** `input[type=file]`（0×0、multiple=true、accept 长 1106 字符）setInputFiles 一张 PNG → **t=0 即出现节点** .react-flow__node-image，aria 逐字「图片 node: b22-upload」，标题 `b22-upload`（**去掉扩展名**），卡片 341×192，状态行 `7 nodes, 0 edges, 1 selected.`（**自动选中**）→ 等 6s 让缩略图换成服务端图，再点空白取消选中 → 裁切 clip={x:379,y:174,w:521,h:372}。⚠️ 图中那个「左栏」是**被上传的图片内容本身**（源文件就是一张画布截图），不是画布左栏。积分 805 未变 ⇒ 上传免费。详见 SOURCE_OBSERVATIONS §3.83',
  },
  '64-upload-node-selected.png': {
    task_id: 'create-first-node', step: 2, visible_text: '智能改图',
    loc: '选中同一节点 → 节点上方浮出 `[data-testid="node-toolbar"]` **959×40@(161,188)**，逐字 12 项：智能改图｜720 全景｜扩图｜智能超清｜抠图｜预设｜多角度｜智能打光｜工具｜AI 助手｜全屏｜下载（`智能改图`/`720 全景`/`智能打光` 带 ✦ 会员菱标；`预设`/`工具`/`AI 助手` 带 ∨ 下拉箭头）—— 与批次 22 独立记录的表格**逐项连标记都一致**（第三次独立复核）。裁切 clip={x:133,y:160,w:1015,h:324}，**按「工具条 ∪ 节点」并集算**：首轮按「节点 341×192 + padding」算，工具条两端被裁掉、图里只剩 8 项而正文写 12 项；改并集后加断言「逐个按钮中心点必须落在 clip 内」，结果 `12 项 / 裁掉 0 项`。⚠️ 页面上有**两个** `[data-testid="node-toolbar"]`，另一个是 `0×0` 常驻占位（`querySelector` 单数会撞上它）。积分 805 未变。详见 §3.83.5 / §3.83.7',
  },
};

const entries = [];
const missing = [];
const skipped = [];
for (const [file, meta] of Object.entries(META)) {
  if (already.has(`screenshots/${file}`)) { skipped.push(file + '（manifest 已有）'); continue; }
  const re = new RegExp(`!\\[([^\\]]*)\\]\\(\\.\\./screenshots/${file.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\)`);
  const m = re.exec(md);
  if (!m) { missing.push(file + '（正文里找不到 ![]() 引用）'); continue; }
  const abs = `${DOC}/screenshots/${file}`;
  if (!existsSync(abs)) { missing.push(file + '（截图文件不存在）'); continue; }
  const sha = createHash('sha256').update(readFileSync(abs)).digest('hex');
  entries.push({
    file: `screenshots/${file}`, task_id: meta.task_id, step: meta.step,
    route: '/ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f',
    viewport: '1280x720@2x', locale: 'zh-CN',
    captured_at: '2026-10-01T23:58:00+08:00', verified_locator: meta.loc,
    visible_text: meta.visible_text, alt: m[1], sha256: sha,
  });
}
if (missing.length) { console.error('ABORT: ' + missing.join(' | ')); process.exit(1); }
for (const f of skipped) console.log('  跳过:', f);

for (const e of entries) {
  // YAML plain scalar 的真正禁区：行首指示符、': '（键值对）、' #'（注释）、换行、首尾空白
  if (/^[\[\]{}#&*!|>'"%@`,]/.test(e.alt) || e.alt.includes(': ') || e.alt.includes(' #') || /[\r\n]/.test(e.alt) || e.alt !== e.alt.trim()) {
    console.error('alt 会破坏 YAML plain scalar:', e.file, JSON.stringify(e.alt.slice(0, 60))); process.exit(2);
  }
  if (e.alt.length > 400) console.warn('  ⚠️ alt 偏长:', e.file, e.alt.length);
}
if (!manRaw.endsWith('\n')) { console.error('manifest 结尾缺换行，先修'); process.exit(3); }

const yaml = entries.map((e) => `\n  - file: ${e.file}\n    task_id: ${e.task_id}\n    step: ${e.step}\n    route: ${e.route}\n    viewport: ${e.viewport}\n    locale: ${e.locale}\n    captured_at: ${e.captured_at}\n    verified_locator: '${e.verified_locator}'\n    visible_text: ${e.visible_text}\n    alt: ${e.alt}\n    sha256: ${e.sha256}\n`).join('');
writeFileSync(MAN, manRaw + yaml);
console.log('追加', entries.length, '条 →', MAN);
for (const e of entries) console.log('  ', e.file, '| alt', e.alt.length, '字 | sha', e.sha256.slice(0, 12));

const total = execSync(`grep -c "^  - file:" ${MAN}`).toString().trim();
const uniq = execSync(`grep "^  - file:" ${MAN} | sort -u | wc -l`).toString().trim();
console.log('manifest 现共', total, '条，去重后', uniq, '条', total === uniq ? '✅ 无重复' : '🔴 有重复！');
if (total !== uniq) process.exit(4);
