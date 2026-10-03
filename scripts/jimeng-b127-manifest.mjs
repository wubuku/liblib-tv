// 批次 127 · 一次性补两条 manifest（109 / 110）。
// 沿用批次 126 的教训：alt 里**不写 markdown 强调标记**（会被渲染成 <strong>，污染无障碍朗读文本），
// 且 alt 必须与正文引用处**逐字一致**（alt 审计门会比对）。
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';

const base = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const man = new URL('../docs/user-manual/jimeng-canvas/screenshots/manifest.yml', import.meta.url);
let txt = readFileSync(man, 'utf8');
const sha = (f) => createHash('sha256').update(readFileSync(new URL(f, base))).digest('hex');

const entries = [
  {
    file: 'screenshots/109-search-panel.png',
    task_id: 'navigate-canvas',
    step: 0,
    captured_at: '2026-10-03T12:17:00+08:00',
    verified_locator:
      '2026-10-03 批次 127。落点现算 + elementFromPoint 自检打开顶栏「搜索」→ 等 2000ms → 用「去掉尾部数字后前缀匹配」点「全部」页签（逐字相等会失配，因为带计数时文字是「全部 76」）→ 等 2000ms。拍前逐条断言：面板 320×604@765,56、选中页签逐字「全部 76」、输入框 value 为空、分页 innerText「1 6」、结果行 10 行 —— 五条全过才拍，拍完再回读一次确认状态未变。裁剪 clip={x:750,y:40,w:350,h:640}（整块面板）。未点任何结果行',
    visible_text: '搜索节点... / 全部 76 / 图片 1 / 视频 1 / 音频 68 / 文本 3 / 音频 53 / 音频 / 1 / 6',
    alt: '搜索面板全貌：顶部输入框占位「搜索节点...」；下面一排分类页签「全部 76」带下划线表示当前选中，后接「图片 1」「视频 1」「音频 68」「文本 3」；结果区每行一个节点，左侧方块是序号与类型图标，右侧是节点名与类型小字，可见「音频 53 音频」到「音频 47 音频」共 7 条；最下面一条被分页条切掉一半；分页条左起是首页、上一页、页码 1 / 6、下一页、末页',
  },
  {
    file: 'screenshots/110-search-tabs-overflow.png',
    task_id: 'navigate-canvas',
    step: 0,
    captured_at: '2026-10-03T12:17:20+08:00',
    verified_locator:
      '2026-10-03 批次 127。与 109 同一帧状态，拍前断言「存在溢出且右端圆钮存在」：role=tablist 的 scrollWidth 519 > clientWidth 320，且页签行内那个无 role 的 BUTTON 24×24@1045,118 的 aria 逐字为 Next search categories。裁剪 clip={x:750,y:100,w:350,h:60}（只取页签行那一横条）。这张图的作用是把「九个页签一行放不下」拍成可见证据：右端圆钮把「文本 3」压住一半',
    visible_text: '全部 76 / 图片 1 / 视频 1 / 音频 68 / 文本',
    alt: '页签行特写：「全部 76」带下划线表示当前选中，右边依次是「图片 1」「视频 1」「音频 68」和被右端圆钮压住一半的「文本 3」；圆钮就是那个没有文字、aria 为 Next search categories 的翻页签按钮，作用是把这排放不下的页签往右翻',
  },
];

for (const e of entries) {
  if (txt.includes(e.file)) { console.log('已存在，跳过：', e.file); continue; }
  const block = [
    '',
    `  - file: ${e.file}`,
    `    task_id: ${e.task_id}`,
    `    step: ${e.step}`,
    '    route: /ai-tool/ai-canvas/64b58cd5-7b04-4312-890a-09f2d1d3399f',
    '    viewport: 1280x720@2x',
    '    locale: zh-CN',
    `    captured_at: ${e.captured_at}`,
    `    verified_locator: '${e.verified_locator}'`,
    `    visible_text: ${e.visible_text}`,
    `    alt: ${e.alt}`,
    `    sha256: ${sha(e.file.split('/').pop())}`,
  ].join('\n');
  txt = txt.replace(/\n?$/, '\n') + block;
  console.log('追加：', e.file, sha(e.file.split('/').pop()).slice(0, 12));
}
writeFileSync(man, txt);
