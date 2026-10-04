// 批次 154 —— 文档落地：① 追加 SOURCE_OBSERVATIONS §4.77
//                      ② 就地改写 §4.49 分诊表那 4 行过期项
//                      ③ AUDIT.md / PROGRESS.md 各加一节
//                      ④ 台账加第 68 条
//
// 🔑 三条纪律：
//   ① **回填门是逐行匹配** ⇒ 表格行改写必须**单行 pattern**，且**订正要并进原文那一行**。
//   ② 锚点 pattern 必须**全册唯一命中**（下面每处都断言 `count === 1`）。
//   ③ 每次 replace 都要验**真生效**（比较长度差 + 反查锚点已消失）。
import fs from 'node:fs';

const DIR = new URL('../docs/user-manual/jimeng-canvas/', import.meta.url);
const 读 = (p) => fs.readFileSync(new URL(p, DIR), 'utf8');
const 存 = (p, s) => fs.writeFileSync(new URL(p, DIR), s);
let 失败 = 0;

const 改 = (路径, 锚, 新, 名) => {
  const s = 读(路径);
  const n = s.split(锚).length - 1;
  if (n !== 1) { console.log('❌ 锚点命中 ' + n + ' 次（必须恰好 1）：' + 名); 失败++; return; }
  const t = s.replace(锚, 新);
  if (t === s) { console.log('❌ replace 没生效：' + 名); 失败++; return; }
  if (t.indexOf(锚) >= 0) { console.log('❌ 旧锚点仍在：' + 名); 失败++; return; }
  存(路径, t);
  console.log('✅ ' + 名 + '（' + s.length + ' → ' + t.length + ' 字符）');
};

// ---------- ① 追加 §4.77 ----------
{
  const p = 'SOURCE_OBSERVATIONS.md';
  const s = 读(p);
  const 新段 = fs.readFileSync('/tmp/b154-so477.md', 'utf8');
  if (s.indexOf('## §4.77 批次 154') >= 0) { console.log('⏭ §4.77 已存在，跳过追加'); }
  else {
    存(p, s.replace(/\s*$/, '\n') + 新段);
    console.log('✅ 追加 §4.77（+' + 新段.length + ' 字符）→ ' + s.split('\n').length + ' 行变 ' + 读(p).split('\n').length + ' 行');
  }
}

// ---------- ② §4.49 分诊表 4 行 ----------
const 行2 = (原, 新, 名) => 改('SOURCE_OBSERVATIONS.md', 原, 新, 名);

行2(
  '| `generation-form` / `generation-mention-panel` / `generation-mention-submenu` / `generation-source-picker-chip` / `generation-source-picker-close`（5） | 打开生成流程 | **点开即进生成流程，需单独授权** |',
  '| ~~`generation-form` / `generation-mention-panel` / `generation-mention-submenu` / `generation-source-picker-chip` / `generation-source-picker-close`（5）~~ | ~~打开生成流程~~ | ~~点开即进生成流程，需单独授权~~ ✅ **2026-10-04 批次 154 验成 3 个**：`generation-form` 命中 1（`680×208`，**建完选中就默认展开，不必点「展开图片生成器」**）、`generation-mention-panel` 命中 1（🔴 **图片族是 `240×140` / 2 项，「`240×244` / 4 项」是视频族的读数，已订正**）、`generation-source-picker-chip` `145×44` + `generation-source-picker-close` `24×24`；`generation-mention-submenu` **仍为 0**（要再点类别才出，本轮未点，**保留在表里**）。**「需单独授权」已因 2026-10-04 目标更新解除**（测试帐号可做 CRUD，只要不执行真实生图/生视频）。详见 **§4.77** |',
  '§4.49 分诊表 第 2 行（生成 5 项）');

行2(
  '| `canvas-source-picker-canvas-frame` / `-mask`（2） | 同上（「从画布选择」全屏拾取模式） | 同上 |',
  '| ~~`canvas-source-picker-canvas-frame` / `-mask`（2）~~ | ~~同上（「从画布选择」全屏拾取模式）~~ | ~~同上~~ ✅ **2026-10-04 批次 154 验成**：`canvas-source-picker-canvas-frame` 与 `-mask` 各命中 1、都 `1280×720@0,0`，🆕 但**两者挂载点不同**（`renderer` vs `viewport-portal`，**盒完全一样、光看尺寸分不出来**）。**「需单独授权」已解除**。详见 **§4.77** |',
  '§4.49 分诊表 第 3 行（canvas-source-picker 2 项）');

行2(
  '| `audio-node-uploading` | 上传中态 | 批次 112 六次尝试都造不出来 |',
  '| `audio-node-uploading` | 上传中态 | ~~批次 112 六次尝试都造不出来~~ ✅ **2026-10-03 批次 109 就已验成**（`20-reference.md:1266` 逐字两段 `正在上传音频 0%` → `正在处理上传内容…`）—— 🔴 **这一行是批次 112 的旧结论，批次 109 推翻了它却没回填到本表**，属纯粹的**台账漂移**。2026-10-04 批次 154 的元审计把它挑出来，**本批未复测**（不在本轮三问范围内） |',
  '§4.49 分诊表 第 5 行（audio-node-uploading）');

行2(
  '| `workspace-project-info-dialog` | 点「积分明细」 | 跳转型，**需单独授权** |',
  '| `workspace-project-info-dialog` | 点「积分明细」 | ~~跳转型，需单独授权~~ ✅ **2026-10-04 批次 154 验成**：`800×546@240,87`、`role="dialog"`、逐字「项目信息 基础信息 积分消耗 总消耗积分 0 任务数 0 暂无数据 查看积分明细」，与 `canvas-context.md:244` 逐字一致（**第 5 次独立复现**）；🆕 逐次 `Esc` 复现「由内向外一层一层关」：第 1 次关对话框、**生成历史面板仍在**，第 2 次才关面板。**「需单独授权」已解除** |',
  '§4.49 分诊表 workspace-project-info-dialog 行');

// ---------- ③ AUDIT.md ----------
{
  const 节 = `
### 🔴 批次 154（2026-10-04）结清 §4.49 分诊表最后 4 行；**顺手发现 manifest.yml 一年没被解析过**

| 项 | 级别 | 证据 | 处理 |
|---|---|---|---|
| 🔑 **\`screenshots/manifest.yml\` 从 2026-10-01 起就不是合法 YAML，而没有任何一道门发现** | 🔴 **Major（工具链缺陷）** | \`yaml.safe_load\` 直接 \`ParserError\`；逐行追出 **10 行**坏引号、**四种坏法**（闭合单引号后多一个 \`"\` / 内部裸单引号提前终止标量 / 缺开引号 / 未加引号且含 \`: \`）。根因：\`jimeng-alt-audit.mjs\` 用 \`split(/\\n  - file: /)\` **正则切块**、\`build-site.sh\` 用 **awk**，**两者都不解析 YAML** | 收敛循环重写引号（**内容一个字节不改**，405 个长文本字段解析后**逐字相同、0 处不符**）；新增 **第 10 道门** \`jimeng-manifest-gate.mjs\`（真解析 + 必填字段 + 不重复 + 文件存在 + **sha256 逐字对上** + 正文 alt 逐字一致 + alt 无 \`**\`）。📌 **立规：找 YAML 坏行要靠解析器报错的位置，不要靠数引号**（我第一版就漏了第 4 类） |
| 🔑 **新门第一次跑就抓出 8 条历史 alt 带 \`**\`** | Minor（可访问性） | \`57\` / \`65\` / \`99\` / \`100\` / \`101\` / \`102\` / \`71\`×2。\`**\` 会**原样**进 \`<img alt>\`，读屏软件会念出「星号星号」 | 一次修干净（manifest 与正文同步，8+8 处）。📌 **必须一次修干净** —— 否则就是批次 66 说的「一道长期红的门等于没有门」 |
| 🔴 **点扫描的解构顺序错了 ⇒ 我点到了画布标题** | 🔴 **Major（自身 bug）** | 盒产出 \`[宽,高,左,上]\`，消费 \`([x,y,w,h])\` ⇒ 「点展开按钮」实际扫的是 \`x∈[42,955] y∈[2,438]\`，返回 \`(52,42)\` = \`Canvas title: 测试项目\`，而脚本**紧接着就当「点开了生成表单」往下推了两步** | 立规 6：**跨 \`page.evaluate\` 的矩形只能是具名标量，点扫描一律在页面内现取现算**，只把 \`{x,y}\` 带回。修法见 \`jimeng-b154c.mjs\` 的 \`找点\` |
| 🔴 **找点只搜 \`button,[role=button]\`，漏掉全部三个 \`role=menuitem\`** | 🔴 **Major（自身 bug，且差点造成灾难性结论）** | 「从画布选择」候选数 **0** ⇒ 差一步写成「来源选择器打不开」。手册 \`20-reference.md:710-722\` 早就写明那三项是 \`role=menuitem\` | 立规 7：**读数为 0 先怀疑「找错元素类型」，再怀疑「功能没了」** —— 与批次 153「把 \`data-testid\` 当 class」同族的第二个错 |
| 🔴 **自检两边同源 ⇒ 验不出自己造成的错** | Minor（自身 bug） | \`取alt()\` 用 python \`print()\` **多带一个换行** ⇒ 3 张新图正文 alt 多 1 字符；脚本末尾「alt 逐字一致」自检**两边都调同一个 \`取alt()\`** | 立规 10：**自检的期望值不能与被检值来自同一次有副作用的调用**；外部取值用 \`sys.stdout.write\`。是新门（⑥）先红的 |
| ✅ **\`generation-mention-panel\` 的 \`240×244\` / 4 项是「视频族」的读数** | Minor（订正） | 图片节点上实测 \`240×140@168.8,363\`、\`listbox\` 子项**只有 2 个**（主体 / 图片），祖先链换成 \`form{generation-form}\` | 就地订正 \`prepare-generation.md:196\`。📌 **面板高度与类别数随节点族变**，类别数 = 该节点能引用的资源类别数 |
| 🆕 **frame 与 mask 挂载点不同** | Minor（新读数） | 两者盒**完全一样**（都 \`1280×720@0,0\`），但祖先链分别起于 \`div.react-flow__renderer\` 与 \`div.react-flow__viewport-portal\` | 写进 \`prepare-generation.md\` 与 \`20-reference.md\`。📌 **光看尺寸分不出来** |
| 🆕 **「取消选择」是 chip 的子元素** | Minor（新读数） | \`generation-source-picker-close\` 的祖先链第一层就是 \`div{generation-source-picker-chip}.absolute\` | 同上 |
| 🆕 **那行英文辅助文案是 \`<OUTPUT>\` + \`clip\`** | Minor（新读数） | \`1×1@846,631\`，\`position:absolute\` + \`overflow:hidden\` + \`clip:rect(0px,0px,0px,0px)\` | 同上。📌 它是**被 clip 裁掉的 live region**，不是「缩小了的小字」 |
| 🆕 **生成面板是「选中常驻」不是「悬停才出现」** | Minor（新读数） | 鼠标移到 \`(8,8)\` 移出画布后，\`node-toolbar\` 仍 2 个实例、\`generation-form\` 仍 1、选中仍 1 | 写进 \`prepare-generation.md\`。📌 批次 144 记的「悬停才出现」是**文本**族，别跨族套 |
| ⛔ **零副作用** | 正面 | 没点 \`generation-submit-icon\`、没点任何「确认 / 插入 / 立即」、没输入一个字、没点对话框里的「查看积分明细」与 ✕ | 终态 \`76 nodes / 0 selected / 0 edges\`、\`Zoom options, 60%\`（实测 \`scale(0.6)\`、连读两次）、小地图开、**积分 805**、**两个自建 id 全部消失**、**其余节点 canvas 坐标零位移**、manifest **138 条 / sha256 138 对上** |
`;
  const p = 'AUDIT.md';
  const s = 读(p);
  if (s.indexOf('批次 154（2026-10-04）结清 §4.49 分诊表最后 4 行') >= 0) console.log('⏭ AUDIT 已有批次 154');
  else { 存(p, s.replace(/\s*$/, '\n') + 节); console.log('✅ AUDIT.md 加批次 154 小节（+' + 节.length + '）'); }
}

// ---------- ④ PROGRESS.md ----------
{
  const 节 = `
### 批次 154（2026-10-04）· §4.49 分诊表最后 4 行结清 + 🔴 manifest.yml 长期不是合法 YAML

- **靶子**：一次纯静态元审计（\`jimeng-b154-meta.mjs\`）逐行读 §4.49 分诊表，比对手册别处是否已验 ——
  9 行里 **4 行**是「表里说没验 / 别处早就验了」的漂移。元审计脚本自己先修了两处缺陷
  （\`node_modules\`/\`screenshots\` 污染分母；\`media-playback.md\` 里的「源站采样 batch 218」是**别的项目**的批次号）。
- **取证**：4 个脚本、**14 条断言全过**。\`jimeng-b154.mjs\`（主）→ 被自己的解构 bug 坑了 →
  \`jimeng-b154b.mjs\`（**纯只读地面真相**，一个按钮都不点）→ \`jimeng-b154c.mjs\`（Q1+Q3）→ \`jimeng-b154d.mjs\`（补 Q2）。
- **授权**：2026-10-04 目标更新解除了「需单独授权」—— 测试帐号可做有副作用的 CRUD，只要不执行真实生图/生视频。
  ⇒ 三个「点开即进生成流程」的入口当场验成。红线写进代码：绝不点 submit / 绝不点「确认·插入·立即」/ 不扣费 /
  **打开浮层后绝不调 \`settle()\`** / 不按任何字母数字键。
- **本批结论**：14 条断言全过；\`generation-mention-panel\` 🔴 **\`240×244\`/4 项是视频族**（图片族 \`240×140\`/2 项）；
  🆕 frame 与 mask 挂载点不同、「取消选择」是 chip 子元素、英文辅助文案是 \`<OUTPUT>\`+\`clip\`、生成面板是「选中常驻」。
- **工具链产出（本批最大的一笔）**：🔴 \`screenshots/manifest.yml\` **从 2026-10-01 起就不是合法 YAML**，
  **10 行坏引号、四种坏法**，而 alt-audit 用正则切块、build-site 用 awk，**两者都不解析它**。
  已修（405 个长文本字段逐字未变）+ 新增 **第 10 道门** \`jimeng-manifest-gate.mjs\`，门第一次跑就抓出 8 条 alt 带 \`**\` 并一次修净。
- **自身失误 4 个**：① 点扫描解构顺序错（点到了画布标题）② 找点漏掉 \`role=menuitem\`（读数 0 长得像「功能没了」）
  ③ 内联 python 多一个右括号 ④ 自检两边同源、验不出 \`print()\` 的换行。⇒ 立规 6 / 7 / 9 / 10。
- **截图**：批次 150–153 四批零图的欠账，本批还了 3 张（\`54\` 提及面板 / \`55\` 画布拾取 / \`56\` 积分明细），manifest 135 → **138 条**。
- **收尾**：\`76 nodes / 0 edges / 0 selected\`、\`Zoom options, 60%\`（实测 \`scale(0.6)\`、连读两次）、小地图开、**积分 805**、
  自建 id 全部消失、**其余节点 canvas 坐标零位移**、**全程零副作用**。
`;
  const p = 'PROGRESS.md';
  const s = 读(p);
  if (s.indexOf('### 批次 154（2026-10-04）· §4.49 分诊表最后 4 行结清') >= 0) console.log('⏭ PROGRESS 已有批次 154');
  else { 存(p, s.replace(/\s*$/, '\n') + 节); console.log('✅ PROGRESS.md 加批次 154 小节（+' + 节.length + '）'); }
}

console.log(失败 ? '\n⛔ 有 ' + 失败 + ' 处失败' : '\n✅ 文档落地完成');
process.exit(失败 ? 1 : 0);
