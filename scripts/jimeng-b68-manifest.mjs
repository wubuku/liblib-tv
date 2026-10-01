// 从正文**逐字**抽 alt 追加 manifest 条目（批次 68）
// 与 jimeng-b64-manifest.mjs 同源，但只处理新图、且跳过 manifest 里已有的 file。
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execSync } from 'node:child_process';

const DOC = 'docs/user-manual/jimeng-canvas';
const body = readFileSync(`${DOC}/10-tasks/director-node.md`, 'utf8');
const MAN = `${DOC}/screenshots/manifest.yml`;
const manRaw = readFileSync(MAN, 'utf8');
const already = new Set([...manRaw.matchAll(/^ {2}- file: (\S+)$/gm)].map((m) => m[1]));

const META = {
  '68-director-node-tags.png': {
    task_id: 'director-node', step: 4, visible_text: '全部清空',
    loc: '左栏点「导演台」(aria 逐字「导演台」36×…) → 新建**自建**导演台节点 `react-flow__node-external`（canvas 恒 320×320；60% 下屏上 192×192、100% 下 320×320，**旧记 281×281 自洽于 87.8% 缩放**）→ 点节点选中（断言 `selected` 计数 1）→ 点标题行右侧 `Add tags`（24×24）→ 展开 `canvas-node-tag-selector` **224×44**，内含 **6 个 28×28 按钮**：全部清空(`data-toolbar-value=clear`)、添加“青绿色”(default-tag-1)、添加“靛蓝色”(default-tag-2)、添加“紫色”(default-tag-3)、添加“橙色”(default-tag-4)、添加“黄色”(default-tag-5) ⇒ **5 个预设标签与节点背景色色板同色但没有「无颜色」，且面板内 input/contenteditable 实测为 0 个 ⇒ 标签只能从预设里挑、不能自定义文字** → 裁切 clip={x:510,y:220,w:360,h:270}（**节点 ∪ 面板**并集，9 个关键元素断言被裁 0 个）。**只读结构后按 Esc 退出，没有真的打标签**。节点已按 id 精确删除。积分 805 未变。详见 SOURCE_OBSERVATIONS §3.87.5',
  },
};

const entries = [];
for (const [file, meta] of Object.entries(META)) {
  if (already.has(`screenshots/${file}`)) { console.log('  跳过（manifest 已有）:', file); continue; }
  const re = new RegExp(`!\\[([^\\]]*)\\]\\(\\.\\./screenshots/${file.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\)`);
  const m = re.exec(body);
  if (!m) { console.error('ABORT: 正文里找不到引用', file); process.exit(1); }
  const abs = `${DOC}/screenshots/${file}`;
  if (!existsSync(abs)) { console.error('ABORT: 文件不存在', file); process.exit(1); }
  const sha = createHash('sha256').update(readFileSync(abs)).digest('hex');
  const alt = m[1];
  if (/^[\[\]{}#&*!|>'"%@`,]/.test(alt) || alt.includes(': ') || alt.includes(' #') || /[\r\n]/.test(alt) || alt !== alt.trim()) {
    console.error('alt 会破坏 YAML:', file); process.exit(2);
  }
  entries.push({ file: `screenshots/${file}`, ...meta, alt, sha });
}
if (!manRaw.endsWith('\n')) { console.error('manifest 结尾缺换行'); process.exit(3); }
const yaml = entries.map((e) => `\n  - file: ${e.file}\n    task_id: ${e.task_id}\n    step: ${e.step}\n    route: /ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f\n    viewport: 1280x720@2x\n    locale: zh-CN\n    captured_at: 2026-10-01T13:20:00+08:00\n    verified_locator: '${e.loc}'\n    visible_text: ${e.visible_text}\n    alt: ${e.alt}\n    sha256: ${e.sha}\n`).join('');
writeFileSync(MAN, manRaw + yaml);
console.log('追加', entries.length, '条');
for (const e of entries) console.log('  ', e.file, '| alt', e.alt.length, '字 | sha', e.sha.slice(0, 12));
const total = execSync(`grep -c "^  - file:" ${MAN}`).toString().trim();
const uniq = execSync(`grep "^  - file:" ${MAN} | sort -u | wc -l`).toString().trim();
console.log('manifest 现共', total, '条，去重后', uniq, '条', total === uniq ? '✅ 无重复' : '🔴 有重复');
if (total !== uniq) process.exit(4);
