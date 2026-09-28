# 发布 BeefTV 用户手册站点（一键脚本 + 手动命令）

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
| 3/6 | 内容清单 | 统计将发布的页面数与截图数（自动排除 AUDIT/PROGRESS/TEST_MEDIA_ASSETS/SOURCE_OBSERVATIONS 等内部资料），数量异常直接报错 |
| 4/6 | 清理旧产物 | 删除 `.vitepress/dist` 与 `.vitepress/cache`，保证产物干净 |
| 5/6 | 构建 | `npx vitepress build`（client + server 双端打包、页面渲染） |
| 6/6 | 产物校验 | 校验 dist 页面数、截图数（与源截图逐一比对）、总体积、是否有未改写的 `.md` 残留链接 |

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
- 站点只输出面向用户的页面（README 为首页）；`AUDIT.md`、`PROGRESS.md`、
  `TEST_MEDIA_ASSETS.md`、`SOURCE_OBSERVATIONS.md`、`task-inventory.yml` 等内部
  维护资料通过 `srcExclude` 排除，不会发布。
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
| 内部账本（入库，不发布） | `AUDIT.md`、`PROGRESS.md`、`task-inventory.yml`、`TEST_MEDIA_ASSETS.md`、`SOURCE_OBSERVATIONS.md` | 回走审计结论、任务清单、素材登记；由 `srcExclude` 保证不进 dist |
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
