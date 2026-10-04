// 批次 154 —— 把三张新截图插进正文，并把本批的三条新读数就地补进对应小节。
//
// 🔑 三条纪律：
//   ① **每次 `String.replace` 后必须验它真生效**（比较 replace 前后的长度差），
//      否则「没插进去」和「插进去了」在日志里长得一样。
//   ② 正文 alt 必须与 manifest 逐字一致 —— 本脚本**直接从 manifest 读 alt**，
//      不手抄，从根上消灭「抄错一个字」这一类。
//   ③ 锚点用**订正标记词**而不是会被我改掉的旧字，避免留下幽灵锚点。
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';

const DIR = new URL('../docs/user-manual/jimeng-canvas/', import.meta.url);
const 读 = (p) => fs.readFileSync(new URL(p, DIR), 'utf8');
const 存 = (p, s) => fs.writeFileSync(new URL(p, DIR), s);

// alt 直接从 manifest 取（python 解析，保证与门看到的是同一份）
const 取alt = (file) => {
  const py = 'import yaml,json,sys;d=yaml.safe_load(open(sys.argv[1]));print(next(i["alt"] for i in d["screenshots"] if i["file"]==sys.argv[2]))';
  return execFileSync('python3', ['-c', py, new URL('screenshots/manifest.yml', DIR).pathname, file], { encoding: 'utf8' });
};

const 编辑 = [];
const 替换 = (路径, 锚, 插入, 名) => {
  const s = 读(路径);
  if (s.indexOf(锚) < 0) { console.log('❌ 锚点没找到：' + 名 + ' @ ' + 路径); return false; }
  const n = s.split(锚).length - 1;
  if (n !== 1) { console.log('❌ 锚点出现 ' + n + ' 次（必须恰好 1）：' + 名); return false; }
  const t = s.replace(锚, 锚 + 插入);
  if (t.length - s.length !== 插入.length) { console.log('❌ 长度差不对：' + 名); return false; }
  if (t === s) { console.log('❌ replace 没生效：' + 名); return false; }
  存(路径, t);
  编辑.push(名);
  console.log('✅ ' + 名 + '  （+' + 插入.length + ' 字符）');
  return true;
};

// ---------- 1) prepare-generation.md §3：@ 提及面板 ----------
const a54 = 取alt('screenshots/54-generation-mention-panel.png');
const 锚1 = '- 容器 `[data-testid="generation-mention-panel"]` 实测 **240×244**，内含\n  `[role="listbox"]`，aria 逐字 **`可能@的内容`**。';
替换('10-tasks/prepare-generation.md', 锚1, `

![${a54}](../screenshots/54-generation-mention-panel.png)

> 🆕 **2026-10-04 批次 154 订正：\`240×244\` / 4 个类别是「视频」节点的读数，不是通例。**
> 在**图片**节点上同一个面板实测 **\`240×140@168.8,363\`**、\`[role="listbox"]\` 的
> **子项只有 2 个**（\`主体\` / \`图片\`，没有视频与音频），
> 祖先链也换成了 \`div.generation-media-prompt-field < div.flex <
> form{**generation-form**}.generation-input-group < div.generation-input-panel-shell <
> div{node-toolbar-feature-host} < div{node-toolbar}\`。
> ⇒ 📌 **面板高度与类别数随节点族变**：类别数 = 该节点族能引用的资源类别数。
> 自动化断言「4 个 option」只在视频/音频节点上成立。详见 \`SOURCE_OBSERVATIONS\` §4.77。`,
  'prepare-generation §3 插图 54 + 图片族订正');

// ---------- 2) prepare-generation.md §3 之后的「从画布选择」小节 ----------
const a55 = 取alt('screenshots/55-source-picker-canvas-mode.png');
const 锚2 = '- **两条退出路径都实测过**：\n  - 点 chip 右侧的 **`取消选择`** → 遮罩、框、chip 全部消失，节点与提示词原样保留；\n  - 连按 **`Esc`** → 同样全部关闭。';
替换('10-tasks/prepare-generation.md', 锚2, `

![${a55}](../screenshots/55-source-picker-canvas-mode.png)

> 🆕 **2026-10-04 批次 154 补录三条此前没记的读数**（在**图片**节点上走一遍全流程，
> 6 条断言全过，全程积分 \`805 → 805\`）：
> - 🔑 **frame 与 mask 的挂载点不同**：\`canvas-source-picker-canvas-frame\` 的祖先链起于
>   \`div.react-flow__renderer\`，而 \`canvas-source-picker-canvas-mask\` 起于
>   \`div.react-flow__viewport-portal\`（再往里才是 viewport / pane / renderer）。
>   两者的盒都是 \`1280×720@0,0\`，**光看尺寸分不出来**。
> - 🔑 **「取消选择」按钮是 chip 的子元素**：\`generation-source-picker-close\` 的祖先链
>   第一层就是 \`div{generation-source-picker-chip}.absolute\`。
> - 🔑 **那行英文辅助文案是 \`<OUTPUT>\` 元素**，\`1×1@846,631\`，
>   靠 \`position:absolute\` + \`overflow:hidden\` + \`clip:rect(0px,0px,0px,0px)\` 裁掉
>   ⇒ 它是**给读屏软件用的 live region**，不是「缩小了的小字」。
> - ⚠️ **画面上左栏九个入口看不见**（被 1280×720 遮罩挡住），
>   但**本轮没有测它们在 DOM 里是否仍在**，所以「按钮仍在 DOM 里但被遮罩接管」这句**保持原样、不据此改动**。
> - 🔴 顺带记一条**找点教训**：「添加参考」菜单里的三项是 \`role="menuitem"\`，
>   **不是 \`button\`**。只搜 \`button,[role=button]\` 会得到「候选数 0」，
>   而**读数 0 长得和「功能没了」一模一样** —— 详见 \`SOURCE_OBSERVATIONS\` §4.77。`,
  'prepare-generation 从画布选择 插图 55 + 三条补录');

// ---------- 3) canvas-context.md：积分明细对话框 ----------
const a56 = 取alt('screenshots/56-workspace-project-info-dialog.png');
const 锚3 = '| 与批次 125 的关系 | 内部 testid 仍是 **`project-consumption-summary`** —— **同一个组件、同一个 testid** |';
替换('10-tasks/canvas-context.md', 锚3, `

![${a56}](../screenshots/56-workspace-project-info-dialog.png)

> 🆕 **2026-10-04 批次 154 独立复现一次**（这条读数在 \`SOURCE_OBSERVATIONS\` §4.49
> 分诊表第 4 行挂了很久，一直标着「**需单独授权**」；本轮目标更新后授权解除，当场验成）：
> 从顶栏 \`生成历史\`（\`data-testid="canvas-panel-launcher"\`、\`28×28\`、点击前
> \`aria-expanded="false"\`）→ 面板 \`320×211@797,56\`、逐字「生成历史 积分明细 全部 图片 视频 音频 文本 暂无生成历史」、
> 5 个真页签各 \`42×36\`、判选中看 \`aria-selected\`（\`data-state\` 属性根本不存在）
> → 点标题行那个**普通 BUTTON**「积分明细」\`68×36\`（无 role、无 href、无 aria-label，
> 自动化只能靠 \`innerText\` 认）⇒ 对话框 \`800×546@240,87\`、\`role="dialog"\`、
> 逐字与上表**逐字相同**。**逐次按 Esc**：第 1 次关掉对话框、**生成历史面板仍在**；
> 第 2 次才关掉面板 ⇒ 「由内向外一层一层关」复现。积分 \`805 → 805\`。`,
  'canvas-context 插图 56 + 独立复现记述');

console.log('\n完成编辑：', 编辑.length, '处');
if (编辑.length !== 3) { console.log('⛔ 数量不对'); process.exit(1); }

// ---- 收尾自检：alt 必须与 manifest 逐字一致（门会再查一次，这里先自查）----
for (const [路径, file] of [['10-tasks/prepare-generation.md', 'screenshots/54-generation-mention-panel.png'],
  ['10-tasks/prepare-generation.md', 'screenshots/55-source-picker-canvas-mode.png'],
  ['10-tasks/canvas-context.md', 'screenshots/56-workspace-project-info-dialog.png']]) {
  const s = 读(路径);
  const rel = '../' + file;
  const m = s.match(new RegExp('!\\[' + '((?:[^\\]\\\\]|\\\\.)*)' + '\\]\\(' + rel.replace(/[/.]/g, '\\$&') + '\\)'));
  const want = 取alt(file);
  console.log((m && m[1] === want ? '✅' : '❌') + ' 正文 alt 与 manifest 逐字一致：' + file);
}
