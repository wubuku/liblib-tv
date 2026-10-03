// 批次 126 · 一次性补两条 manifest（107 / 108）。
// 之所以用脚本而不是手贴：alt 里的 `**` 会被渲染器改写，导致构建门第 7 道的
// `grep -rqF` 锚点失效、示意图「静默消失」（批次 125 踩过，批次 125 之后修过）。
// ⇒ 这里 alt 一律不写 markdown 强调标记。
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';

const base = new URL('../docs/user-manual/jimeng-canvas/screenshots/', import.meta.url);
const man = new URL('../docs/user-manual/jimeng-canvas/screenshots/manifest.yml', import.meta.url);
let txt = readFileSync(man, 'utf8');
const sha = (f) => createHash('sha256').update(readFileSync(new URL(f, base))).digest('hex');

const entries = [
  {
    file: 'screenshots/107-generation-history-panel.png',
    task_id: 'canvas-context',
    step: 0,
    captured_at: '2026-10-03T10:39:00+08:00',
    verified_locator:
      '2026-10-03 批次 126。顶栏「生成历史」按钮落点现算 + elementFromPoint 自检（必须命中 BUTTON[aria=生成历史] 自身；同 testid 的 canvas-panel-launcher 共有 2 个，搜索与生成历史共用，所以按 aria-label 挑）→ 打开 ASIDE[role=dialog][aria=生成历史][data-testid=canvas-feature-panel] 320×211@797,56 → 逐层读 DOM：标题行 320×56 里是 H2 56×36@813,72 与一个没有 role 的 BUTTON「积分明细」68×36@1033,72（带 12×12 右箭头 svg）；下面是 role=tablist aria=History categories 320×36@797,112 与 5 个 BUTTON[role=tab] 各 42×36（x 807/853/899/945/991），aria-controls 全指向 generation-history-items；再下面是 role=tabpanel aria=History items 288×91@813,160 逐字「暂无生成历史」。裁剪 clip={x:780,y:40,w:360,h:250}',
    visible_text: '生成历史 / 积分明细 / 全部 / 图片 / 视频 / 音频 / 文本 / 暂无生成历史',
    alt: '生成历史面板：标题行左侧是标题「生成历史」、右侧是带右箭头的「积分明细」；下面一排五个类型页签「全部 图片 视频 音频 文本」，「全部」带下划线表示当前选中；列表区居中显示空态「暂无生成历史」',
  },
  {
    file: 'screenshots/108-credits-dialog-over-history.png',
    task_id: 'canvas-context',
    step: 0,
    captured_at: '2026-10-03T10:46:00+08:00',
    verified_locator:
      '2026-10-03 批次 126。在 107 那一帧的状态上（面板已开），对标题行里那个没有 role 的 BUTTON「积分明细」落点现算 + elementFromPoint 自检（要求 closest(button) === 目标本身）→ 点击 → 等 1.8s → 浮层清单由 1 个变 2 个，差集恰好 1 个：DIV[role=dialog][data-testid=workspace-project-info-dialog] 800×546@240,87（position:fixed、z-index:50、portal 到 BODY），逐字「项目信息 基础信息 积分消耗 总消耗积分 0 任务数 0 暂无数据 查看积分明细」，且已直接落在「积分消耗」页签、内部 testid 是 project-consumption-summary（与批次 125 同一个组件）。关键证据：URL 未变、生成历史面板逐字一个字都没变、浮层数 1→2。未点「查看积分明细」。整帧未裁剪（clip 为空），因为要同时看到两个浮层叠在一起',
    visible_text: '项目信息 / 基础信息 / 积分消耗 / 总消耗积分 0 / 任务数 0 / 暂无数据 / 查看积分明细 / 积分明细',
    alt: '从「生成历史」点「积分明细」之后的画面：「项目信息」对话框已经打开并停在「积分消耗」页签，而它背后的「生成历史」面板并没有关闭——画面右上角还能看到那个面板露在对话框右边的一截，右上角的「积分明细 >」完整可见',
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
