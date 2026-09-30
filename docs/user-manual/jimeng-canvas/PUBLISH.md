# 发布 即梦画布 用户手册站点（一键脚本 + 手动命令）

把本目录的 Markdown 手册构建为**纯静态网站**，`dist` 目录整体拷贝到任意
Web 服务器（nginx / 对象存储静态托管 / GitHub Pages）即可发布，
无需任何服务器端程序。

## 一键构建（推荐）

```bash
cd docs/user-manual/jimeng-canvas
./build-site.sh
```

| 步骤 | 内容 | 说明 |
|---|---|---|
| 1/6 | 环境检查 | node ≥ 18、npm 可用、站点配置与首页内容存在 |
| 2/6 | 依赖安装 | `node_modules/vitepress` 缺失时自动 `npm install`（已装则跳过并打印 vitepress 版本） |
| 3/6 | 内容清单 | 统计将发布的页面数与截图数（自动排除 AUDIT/PROGRESS/TEST_MEDIA_ASSETS/SOURCE_OBSERVATIONS/PUBLISH 等内部资料），数量异常直接报错 |
| 4/6 | 清理旧产物 | 删除 `.vitepress/dist` 与 `.vitepress/cache`，保证产物干净 |
| 5/6 | 构建 | `npx vitepress build`（client + server 双端打包、页面渲染） |
| 6/6 | 产物校验 | 校验 dist 页面数、截图数（与源截图逐一比对）、总体积、是否有未改写的 `.md` 残留链接 |

**可选参数**：`./build-site.sh --preview` —— 构建完成后自动启动本地预览服务
`http://localhost:4173`（Ctrl+C 结束）。

## ⚠️ 发布前注意（截图脱敏审查）

`screenshots/` 中的截图来自用户真实画布会话：

- 部分截图含**测试视频的画面帧**（AI 生成的咖啡馆人物场景）与测试节点标题
  （`sb_…` 文件名形态）——截图制作时已裁去顶部账户/积分区域，但画面帧本身保留；
- 对外公开发布前，请逐张审查 `dist/` 内图片，确认测试素材可公开，
  或替换/脱敏（PIL 高斯模糊做法见 FrameOS 手册截图 17 先例）。

## 本地预览

```bash
./build-site.sh --preview                                # 方式一：脚本内置
python3 -m http.server 4173 -d .vitepress/dist           # 方式二：任意静态服务器指向 dist
```

> ⚠️ `vite preview` 底层 sirv 会在**启动时缓存文件清单**——重新构建后旧预览
> 进程会对新资产返回 404，必须重启预览进程；或直接用方式二（无缓存）。

## 发布到任意 Web 服务器

```bash
# nginx：把 dist/ 内容放到站点根或子路径
rsync -av --delete .vitepress/dist/ /var/www/jimeng-manual/

# 子路径部署：编辑 .vitepress/config.mjs 把 base: '/' 改为 base: '/jimeng-manual/'
# 然后重新 ./build-site.sh
```

GitHub Pages / 对象存储静态托管同理：dist 整体上传即可。

## 运维 FAQ

| 现象 | 原因与处理 |
|---|---|
| 预览页部分资源 404，但文件在磁盘上 | sirv 清单缓存认知；重启预览或改用 `python3 -m http.server` |
| dist 截图数 < 源截图数 | 有截图未被任何 md 引用，被构建静默丢弃；核对正文引用与 manifest |
| **示意图（SVG）不见了但构建不报错** | Vite 会把被引用的 SVG **内联成 base64 data URI**，不落到 `dist/assets/`；未被引用的则直接消失。两种情况在 dist 的 `.svg` 文件数上**完全一样（都是 0）**，所以「数文件」查不出来。`build-site.sh` 第 6 步因此按 **manifest 里的 alt 文本**逐个到 dist HTML 里查，能真正抓到丢失；手工新增示意图后请确认这一步输出 `示意图均已进入构建产物` |
| 页面里有 `xxx.md` 原始链接 | 对应 md 使用了 vitepress 无法改写的链接写法，改为相对路径或省略扩展名 |
| 构建时 OOM / 卡住 | 本目录 `node_modules` 损坏；删除后重跑 `./build-site.sh` |
| **首页/README 里的账本链接点了 404** | `srcExclude` 已把 `AUDIT.md`/`PROGRESS.md`/`PUBLISH.md`/`task-inventory.yml` 等内部账本排除出站点，但 README 仍以 `[文字](AUDIT.md)` 形式链接它们。VitePress 会把它改写成 `AUDIT.html`，而该文件不在 dist 中 → 死链，且 `ignoreDeadLinks: true` **不会报错**（2026-10-01 实测）。**正确写法**：对这些被排除的账本用纯文件名代码块（`` `AUDIT.md` ``）而非站内链接；面向读者的页面之间才用相对链接 |
| 站点看起来正常但其实有死链 | `ignoreDeadLinks: true` 只跳过构建期报错，不校验目标是否存在。发布前跑一次全站相对链接解析自查（遍历 dist 内 `href="./*.html"`，按各自所在目录解析并检查文件存在） |

## 选型说明（VitePress vs 其他）

| 方案 | 结论 |
|---|---|
| **VitePress（采用）** | 纯静态、内置本地中文搜索（无外部服务）、默认主题够用、构建秒级 |
| MkDocs / mdBook | 需要额外主题与搜索配置，中文搜索体验差 |
| Docsify | 运行时渲染，SEO 与离线体验差 |
| Docusaurus | 功能多但重，本手册规模不需要 |
