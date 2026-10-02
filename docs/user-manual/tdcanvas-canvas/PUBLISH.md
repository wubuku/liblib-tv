# 发布 TDCanvas 用户手册站点（一键脚本 + 手动命令）

把本目录的 Markdown 手册构建为**纯静态网站**，`dist` 目录整体拷贝到任意
Web 服务器（nginx / 对象存储静态托管 / GitHub Pages）即可发布，
无需任何服务器端程序。

## 一键构建（推荐）

```bash
cd docs/user-manual/tdcanvas-canvas
./build-site.sh
```

| 步骤 | 内容 | 说明 |
|---|---|---|
| 1/6 | 环境检查 | node ≥ 18、npm 可用、站点配置与首页内容存在 |
| 2/6 | 依赖安装 | `node_modules/vitepress` 缺失时自动 `npm install`（已装则跳过并打印 vitepress 版本） |
| 3/6 | 内容清单 + **门禁** | 先统计 Markdown 页数与截图数（`find` 排除 AUDIT/PROGRESS/TEST_MEDIA_ASSETS/SOURCE_OBSERVATIONS，注意**未排除 PUBLISH.md 自己**，故此数比实际发布页数多 1），数量异常直接报错；随后依次跑**十六道门禁 + 一道门禁自检**，见下文「构建时的门禁」 |
| 4/6 | 清理旧产物 | 删除 `.vitepress/dist` 与 `.vitepress/cache`，保证产物干净 |
| 5/6 | 构建 | `npx vitepress build`（client + server 双端打包、页面渲染） |
| 6/6 | 产物校验 | 校验 dist 页面数、截图数（与源截图逐一比对）、总体积、是否有未改写的 `.md` 残留链接、**侧边栏完整性**（每个已发布页面都必须出现在 `config.mjs` 侧边栏中，否则报 warn） |

**可选参数**：`./build-site.sh --preview` —— 构建完成后自动启动本地预览服务
`http://localhost:4173`（Ctrl+C 结束）。

## ⚠️ 发布前注意

`screenshots/` 中的部分截图含**测试素材**（AI 生成的人物图/视频帧）。对外公开发布前，
请确认这些素材可公开，或将 `dist` 中的对应图片替换/脱敏。

## 本地预览

```bash
./build-site.sh --preview                                # 方式一：脚本内置
python3 -m http.server 4173 -d .vitepress/dist           # 方式二：任意静态服务器指向 dist
```

> **不要用 `file://` 直接打开 `dist/index.html`**：产物里的资源路径是绝对路径
> （`/assets/...`），在 `file://` 下会指向文件系统根目录，样式与脚本全部加载
> 失败。必须走 HTTP。
>
> **`python3 -m http.server` 不提供站点的 404 页**：VitePress 生成的
> `dist/404.html`（带侧边栏与导航）只会被「把 404 映射到它」的主机送出
> （GitHub Pages、Netlify 原生如此；nginx 需显式配置
> `error_page 404 /404.html;`）。简易服务器对未知路径只返回自己的裸报错，
> 读者落上去没有任何出口——**这是本地预览的已知限制，不是构建缺陷**，
> 但部署时务必确认目标主机配好了 404 映射。

## 发布到任意 Web 服务器

```bash
rsync -av --delete .vitepress/dist/ user@server:/var/www/html/manual/
```

- 站点为纯静态、资源哈希文件名、完全自包含（离线可用），可放 nginx、
  对象存储静态托管、GitHub Pages 等任意环境。
- 部署在**子路径**（如 `https://host/manual/`）时，先修改 `.vitepress/config.mjs`
  的 `base: '/'` 为 `base: '/manual/'`，再重新执行 `./build-site.sh`。

## 站点包含什么

- 侧边栏四组导航 + 右侧「本页目录」+ **中文全文搜索**（`⌘K`，本地索引，无外部服务）。
- 站点只输出面向用户的页面（README 为首页）；`config.mjs` 的 `srcExclude` 排除了 5 个文件：`AUDIT.md`、`PROGRESS.md`、`TEST_MEDIA_ASSETS.md`、`SOURCE_OBSERVATIONS.md`、**`PUBLISH.md`（本文件）**，都不会发布。另 `task-inventory.yml` 是 YAML 不是 Markdown，**本就不进 VitePress**，并非靠 `srcExclude` 排除——两种机制不要混为一谈。
- 站点结构与标题、侧边栏、搜索文案均在 `.vitepress/config.mjs` 配置
  （含 `rewrites: README.md → 站点首页`）。

## 手动命令（不用脚本时）

```bash
cd docs/user-manual/tdcanvas-canvas
npm install          # 首次
npx vitepress build  # 产物 .vitepress/dist/
```

## 目录结构与文件职责

`docs/user-manual/tdcanvas-canvas/` 内与本站点有关的文件分四类：

| 类别 | 文件 | 说明 |
|---|---|---|
| 站点工具（入库） | `build-site.sh`、`.vitepress/config.mjs`、`package.json`、`package-lock.json`、`.gitignore` | 一键构建脚本；站点配置（侧边栏、搜索、rewrites、srcExclude）；依赖锁定 |
| 手册内容（入库） | `README.md`、`00-quickstart.md`、`10-tasks/*.md`、`20-reference.md`、`30-concepts.md`、`90-troubleshooting.md`、`screenshots/*.png` | 面向最终用户的正文与截图 |
| 内部账本（入库，不发布） | `AUDIT.md`、`PROGRESS.md`、`task-inventory.yml`、`TEST_MEDIA_ASSETS.md`、`SOURCE_OBSERVATIONS.md`、`PUBLISH.md` | 回走审计结论、任务清单、素材登记、运行时观察台账、发布手册；前 5 个由 `srcExclude`（`task-inventory.yml` 因是 YAML 而天然不发布）保证不进 dist |
| 构建产物（不入库） | `.vitepress/dist/`、`.vitepress/cache/`、`node_modules/` | 已在本目录 `.gitignore` 忽略；dist 可随时由脚本从源重建 |

## 内容更新流程

1. 修改对应 md，或替换 `screenshots/` 下同名截图（文件名与 manifest 中的 task_id 保持稳定）；
2. 运行 `./build-site.sh`，确认 6 步全绿（第 6 步的截图数比对会自动发现漏图/坏链）；
3. 新增或改名页面时：同步 `.vitepress/config.mjs` 的 `sidebar`、`task-inventory.yml` 的 `manual_pages`，并运行审计脚本；
4. 重新发布 dist（rsync 整体覆盖即可，页面为哈希文件名，无缓存残留问题）。

## 手册验收（审计）流程

- 机械审计：`python3 .agents/skills/web-studio-user-manual/scripts/audit_manual.py docs/user-manual/tdcanvas-canvas --phase gate-a`（内容完成后）与 `--phase final`（发布前；要求任务全部 `verified` 或 `excluded`）。校验点：截图↔manifest 双向一致、sha256 一致、本地链接可达、标题层级、占位文本、core/flagship 任务必须有登记截图。
- 内容审计：按 `AUDIT.md` 记录的 Gate B 方法在真实浏览器逐任务回走（标签逐字核对、提交类动作止于按钮态验证），结论与修复记录进 `AUDIT.md`。
- 手册内容的事实源：真实运行界面。UI 标签变化后以浏览器 DOM 为准修正文档，不以记忆或旧文档为准。

### 构建时的门禁：十二道 + 一道自检

`./build-site.sh` 步骤 3 会依次跑**十六道门禁、再跑门禁自检**，然后才进入构建；步骤 6 回填统计并校验产物死链。**这些门禁源于实测暴露的真实缺陷，不是形式检查**：

| 门禁 | 拦什么 | 由来 |
|---|---|---|
| `check-anchors.py` | 交叉引用锚点落空 | M31 实测 4 处锚点全空 |
| `check-structure.py` | 孤儿任务页、索引/侧边栏漏条、**孤儿截图** | M42 实测孤儿页可无声混入产物；M89 实测孤儿图在七道门禁下全部通过 |
| `check-ratings.py` | 任务评级在账本/索引/首页三处不一致 | M58 实测账本与下游漂移 |
| `check-inventory-freshness.py` | 账本 screenshot_count 与 manifest 实数不符 | M59 实测 3 条数字过期 |
| `check-claims.py` | 无证据的强断言（「逐字一致」等） | M44 实测速查表与截图自相矛盾 |
| `check-retractions.py` | 已订正的错误说法复现（**含账本 `SOURCE_OBSERVATIONS.md`**） | M47 漏改、M52 补门禁；M105 移出一处豁免 |
| `check-emphasis.py` | `**` 紧邻标点导致加粗失效；**裸 `{{ }}` 被 Vue 插值吞掉** | M90 全站扫产物才发现 7 处加粗失效（跨 6 页）；M91 发现 i18n 占位符在产物里整段消失 |
| `check-render.py` | **产物侧**渲染体检：表格列数不一致、裸露管道文本、img 异常、页内锚点悬空、正文空标签 | M84 整行内容被丢弃、M91 两条死链与一处空 `<code>`，源码层八道门禁当时全过 |
| `check-tables.py` | 表格被非表格行劈开、缺表头与分隔行、**行内代码反引号不成对** | M65 实测「十三条」后 5 行渲染成原始管道文本；M84 实测单元格内竖线未转义会**让该行剩余内容从产物里消失** |
| `check-ledger-pin.py` | 锁定提交/版本号**在各声明文件之间不一致**，或与应用仓 HEAD、`package.json` 对不上 | M105 实测账本以「版本锁定」口吻陈述旧观察而无任何机制守候；M110 查出锁定 sha 其实在 `task-inventory.yml` 里**也声明了一次**而门禁只看着账本 |
| `check-publish-sync.py` | 本表与 `build-site.sh` 实际调用的门禁集合对不上 | M106 实测本表早已漂移（把一个构建从不执行的脚本列成构建门禁）|
| `check-source-refs.py` | 正文里 `file:line` 引用指向不存在的文件或越界的行 | M109 实测 4 处路径有歧义（`index.tsx` 仓内 6 个同名），且出现 7 次的 `canvas-node.tsx:1110` 实际已漂到 1111 |
| `check-inventory-yaml.py` | 账本**不是合法 YAML**、任务 id 重复、证据 `type` 不在已知集合内 | M123 实测账本第 143 行第 340 列因 note 里嵌了 `{a === "b" ? x : null}` 这类**带半角「冒号+空格」的源码片段**而整体不可解析；而此前的十四道门禁**无一 import yaml**（全是正则按行读），所以「门禁全绿」与「账本是合法 YAML」一直是两件事 |
| `check-encoding.py` | 文件里出现 **U+FFFD 替换字符**（多字节中文被截断的残骸） | M131 实测手册里已潜伏 **8 处**，分别来自 **M71 / M108 / M113** 三个几十批前的提交，`append-audit.py` 里的那处**从 M71 起就一直带着病在跑**；产物侧照渲染，读者看到的是「上传的<三个坏字节>片节点」。**此前的十六道门禁无一扫它。** ★**判据自指的坑（本门禁第一版就被自己判为不合规）**：文档里为了说明 U+FFFD 是什么而写了它的**字面量**，结果脚本自己被抓出 7 处。**修法是文档里不写字面量，不是给自己开豁免**——豁免名单会变成真实的后门 |
| `check-inventory-evidence.py` | `review_note` 声称做过实测/运行时，但 `evidence` 里**一条 `runtime` 或 `boundary` 都没有**（记账漂移） | M133 查出 `organize-canvas`（M101/M102/M103/M104 四批）与 `shortcuts-help`（M60/M78 两批）的运行时取证**全部只写在 `review_note` 里**，受校验的 `evidence` 始终只有一条 `static`——账本自己跟自己打架，**而构建与门禁输出里完全看不出来**。**光修一次没用**：下批把结论写进 `review_note` 而忘了同步 `evidence`，同样的漂移会重新长出来 |
| `selftest-gates.py` | 上面几道门禁**本身**坏了（注入 38 类故障） | M41 门禁静默错判 |
| `check-dist-links.py` | 产物里的死链 | M56 实测 README 链到未生成页面 |

> **不要用序号指代门禁**——历史条目里的「第 N 道」**不是稳定标识**：M90 把 `check-emphasis.py` 称作「第八道」、M91 把 `check-render.py` 称作「第九道」，而 M58/M59 早就把 `check-ratings.py`、`check-inventory-freshness.py` 分别叫过同样的序号；`check-structure.py` 与 `check-claims.py` 则从未被指派序号。**排查一律按上面的脚本名找。**
>
> **表里没有 `audit_manual.py`，因为它不由构建调用。** 它是共享技能脚本，需**手动**跑：`--phase gate-a`（内容完成后）与 `--phase final`（发布前），用法见上文「手册验收（审计）流程」。
>
> 2026-10-02 M106 订正：本表此前把 `audit_manual.py` 列为「构建时的门禁」，但它在 `build-site.sh` 里**只出现于注释**、从未被执行——同一份文档上一节还写着它是手动单跑的步骤，**自相矛盾**。排查的人若信了表里那行，就会跳过手动审计。`check-publish-sync.py` 现在把注释剥掉后再比对集合，正是为了守住这条。

单跑任一道（都需带 `.` 参数）：

```bash
python3 scripts/check-anchors.py .        # 锚点
python3 scripts/check-structure.py .      # 结构
python3 scripts/check-ratings.py .        # 评级一致性
python3 scripts/check-inventory-freshness.py .  # 账本新鲜度
python3 scripts/check-claims.py .         # 强断言
python3 scripts/check-retractions.py .    # 订正回归
python3 scripts/check-ledger-pin.py .    # 账本锁定提交 vs 应用仓 HEAD
python3 scripts/check-publish-sync.py .  # 发布文档门禁表 vs 构建脚本实际调用
python3 scripts/check-source-refs.py .  # 源码引用 file:line 是否指向真实存在的行
python3 scripts/check-inventory-yaml.py .  # 账本本身是不是合法 YAML
python3 scripts/check-encoding.py .     # 有没有被截断的多字节中文
python3 scripts/check-inventory-evidence.py .  # 账本的运行时结论有没有只写在 review_note 里
python3 scripts/check-tables.py .        # 表格语法
python3 scripts/check-emphasis.py .      # 渲染陷阱（强调 flanking / Vue 插值）
python3 scripts/check-render.py .        # 产物渲染体检（须在构建之后跑）
python3 scripts/selftest-gates.py .       # 门禁自检
python3 scripts/check-dist-links.py .     # 产物死链（须在构建后跑）
```

## 往账本追加记录：用 append-audit.py，别手写 `cat >>`

`AUDIT.md` 的「已知问题清单」是一张**跨批次连续**的大表，每批都要在末尾追加几行。这些行很长（每行两三句话），**"末尾漏掉收尾 ` |`"的笔误已连犯三次**（M68、M69、M70），每次都要等构建失败后回头排查一轮。`check-tables.py` 能抓到，但那是**事后**。

追加请改用：

```bash
python3 scripts/append-audit.py AUDIT.md <<'EOF'
| 级别 | 描述 | 影响 | 处置 |
EOF
```

它做三件事：逐行**自动补齐**收尾竖线并打印提示；校验「追加的表格行必须接在旧表格行后面」，**否则拒绝写入**（不造孤立块）；写盘前复用 `check-tables.py` 的判据整体复查，**不通过就回滚、文件保持原样**。

## 分析工具（不参与构建，只出候选清单）

```bash
python3 scripts/audit-trouble-to-tasks.py
```

扫 `90-troubleshooting.md` 的 36 条排障条目，抽出其中「」与双引号包裹的界面文案，统计它们在**其余 20 份页面**（任务页 / 概念页 / 参考页 / 快速上手 / 首页，**刻意不含排障页自己**）里出现过没有，分三档输出：只在排障页出现（0 处）、全站只被 1 页提到、最少被 2 页提到。

它有两层判据，都是为了让「找没找到」更贴近真实语义：

- **i18n 白名单**：先用应用的中文文案表（`zh-CN.ts`，约 1600 条）把**真界面文案**筛出来，把正文里的散文片段（`不知不觉`、`源码里有`…）滤掉。模板拼接出来的动态文案（如 `{{count}} 个节点 · {{connections}} 条连线`）靠**文字骨架**（去掉数字与分隔符）匹配上。**读不到 i18n 文件时会打印警告并跳过过滤**，不会假装已经净化。
- **骨架搜索**：同一件事两页可能一个写实例、一个写占位符——排障页写「2 个节点 · 0 条连线」、任务页写「N 个节点 · M 条连线」，二者骨架完全相同。只用字面搜索会把「任务页其实写了」误判成「零提及」。

**它不是门禁，也不该当门禁用**——判据仍是**字面/骨架出现与否**，不判断语义：「某词出现过」不等于「讲清楚了」，「没出现过」也不等于「该讲而没讲」（任务页可能用了别的说法）。输出是**候选清单**，逐条要人工确认后再决定改不改。M121 就是靠它定位到「手册内部两条记录互相矛盾」才起头的；M122 跑到零断裂，同时它自己也在这两批里出了三次偏差（见下）。

### 界面元素可发现性探针（M129 建立）

```bash
source ~/.nvm/nvm.sh
node scripts/probe-discoverability.js [画布URL]
# 默认不碰共享 profile；要用共享的显式指定：
TD_PROBE_PROFILE=/tmp/m93-profile node scripts/probe-discoverability.js
```

回答一个问题：**手册里写的某个按钮名，读者在界面上能不能找到？** 它对左侧 Dock 与节点工具条逐个读**四样东西**——`aria-label`、`title`、按钮里的可见文字、悬停浮层——并给每行一个「认得出吗」。

**它的存在理由不是省事，是止损**：M125–M128 连续四批都在这上面栽过跟头，而且**每次栽的方式不同**，所以脚本把判据连同「为什么」一起写进了文件头（M129 立 4 条，M132 补到 7 条）：

1. **DOM 里有文字 ≠ 读者看得见**。Agent 面板 7 个按钮里确实有「对话」「历史」这些文字节点，但尺寸全是 **0×0**——`opacity: 1`、`visibility: visible`、祖先链一切正常，**却占不了任何地方**。只判 `textContent` 会得出完全相反的结论。脚本一律读 `getBoundingClientRect()`。
2. **原生 `title` 提示用 JS 读不到**（浏览器渲染，不是 DOM 元素）。判「有没有提示」= `title` 非空 **OR** 自定义浮层非空。
3. **读持久化数据必须写死 key 且先 parse**。`getAllKeys()[0]` 取到的是 `asset_store`；**`canvas_store` 的值是 JSON 字符串**，不 parse 就全是 `undefined`。**这三个坑的共同点是失败时返回「空」而不是报错**——空读数长得像「产品没这个功能」。脚本在这三处一律**显式抛错**。
4. **「元素存在且有几何」≠「用户看得见」**（M117 的 `opacity:0`、M127 的 `0×0` 同族）。
5. **★ 悬停提示不能按 class 名找**（M132 第 63 次否证，代价最大的一条）。同一个左侧区域里**并存两种浮层实现**：Dock 用自研浮层（类名 `pointer-events-none absolute left-[calc(100%+8px)]`，**不含 tooltip / tip 任何字样**），视图控制与顶栏用 antd 的 `div.ant-tooltip`。**按类名找只抓得到后者**——曾据此把 Dock 全部按钮误读成「悬停无任何提示」，而截图上浮层明明写着「清空画布」。**正确判据是「悬停前后全页可见文本取差集」**，不依赖任何类名。
6. **★ 自己造的数据会被自己过滤掉**（M132）。判「有没有提示」时写了 `新文本.filter(t => t !== aria)`，把「浮层文字与 `aria-label` 相同」这个**最常见的合法情况**整个删光，8 个有浮层的按钮全被判成「无提示」。**过滤证据前先问：这条证据是不是恰恰因为「与已知值相同」才有意义？**
7. **★ 阳性对照要证明「指针真的落在目标上」，而且别把自己的对照截断**（M132 第一版）。`:hover` 链在 `length > 8` 时 `break`，而链正好 8 层，**按钮永远落在截断线之外**。且**判「指针命中」要用几何（链末端元素的 `getBoundingClientRect()`），不能用 aria**——首版拿 aria 名字匹配，把 3 个**无 aria** 的按钮全误报成「没悬停到」。**「我的判据有洞」和「产品有问题」要分开查，前者更常见。**

**它自己也被同一条判据咬过一次**（M129 第一版）：表格里把「有没有提示」写成 `Boolean(r.title || r.悬停浮层 || '(无)')`，那个占位符 `'(无)'` 是**非空字符串、truthy**，于是每行都判「能」——**而末行的汇总却正确列出了 9 个认不出的**，两行自相矛盾。**这与 M125–M128 反复栽的「把『没有』编码成 truthy 哨兵」是同一类错**，故已修并在代码里留了注释。

**它同样不是门禁**：只出读数，判定仍要人来读。M129 首轮跑出来的结果与 M125–M128 的手工读数**逐项吻合**（当时记的是「Dock 认不出 9 个、工具条 13 个全有字且悬停浮层与 `aria-label` 逐字相同」），构成阳性对照。

> ⚠️ **但那个「Dock 认不出 9 个」后来被 M132 整组否证了。** 根因就是上面第 5 条——**量具的毛病，不是产品的毛病**。M132 重写探针后首轮输出与手工读数再次逐项吻合，**这次吻合的是「Dock 8 个按钮悬停提示一个都不缺」**。**同一个脚本、同一份手册，先后「吻合」过两个互相矛盾的结论**——这说明**吻合本身不能证明对错，判据才是**。

> **这个脚本自己在 M121–M122 出过三次错，三次都是同一个家族：判据与自己宣称的口径不符。**
>
> | 批次 | 症状 | 怎么发现的 |
> |---|---|---|
> | M121 | 第二段把「被几条**排障条目**提到」错标成「只在某**页**出现」——`pages` 变量被丢弃，存进去的是条目标题，整段输出是假的 | grep 反查 `锁比例` / `复制错误` 在 `10-tasks` 全部有命中，与脚本输出直接矛盾 |
> | M122 | 提取到的词**带 markdown 星号**（`「**复制错误**」`），于是 `'**复制错误**' in '复制错误'` 恒假，**真界面文案被误判成散文**（假阴性） | 看「被滤掉的散文」清单里混着 `复制错误` / `多角度` / `更多` / `我的资产` 这些一眼就是界面文案的词 |
> | M122 | 字面搜索太窄，把「任务页写了占位符形式」误判成零提及 | 手工核对 `project-management.md:24` 明明写着「N 个节点 · M 条连线」 |
>
> **根因是同一个：过滤器和判据都有两个方向的错误——把该留的滤掉、把不该留的留下，而报告里只写了其中一面。** 教训：**每次改判据，都要同时看两个方向的清单（判为界面文案的、判为散文的），而不是只看最终那份。**

## 运维常见问题

| 症状 | 原因与处理 |
|---|---|
| `npm install` 慢或失败 | 可换镜像：`npm install --registry=https://registry.npmmirror.com`；依赖装好后构建不再访问网络 |
| 发布后子路径 404 / 资源 404 | 未改 `base`：`config.mjs` 设 `base: '/子路径/'` 后重新构建 |
| dist 截图数与源不一致 | 某截图未被任何 md 引用会被丢弃；脚本第 6 步会 warn，补正文引用即可 |
| 站点搜不到新内容 | 搜索索引在构建时生成，确认已重新 `build`；索引只含 `srcExclude` 之外的页面 |
| 4173 端口被占用 | `python3 -m http.server <其他端口> -d .vitepress/dist` 换端口预览 |

## 为什么选 VitePress（备选工具对比）

| 工具 | 一句话结论 |
|---|---|
| **VitePress**（已采用） | Node 生态现成、构建秒级、产物自包含、内置中文本地搜索；与手册的纯 Markdown 源零耦合 |
| MkDocs + Material | Python 系最成熟的方案，主题精致；需要 pip 安装依赖，中文搜索要额外配置 |
| mdBook | 单二进制最简单；但中文搜索分词弱、主题定制少 |
| Docsify | 零构建（运行时拉取 md），部署最简单；但 SEO/首屏弱、需随站点分发 md 源文件 |
| Docusaurus | 功能最全（版本化/i18n）；React 体系重，对手册规模过重 |
