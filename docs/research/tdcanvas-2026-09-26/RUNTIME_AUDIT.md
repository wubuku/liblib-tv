# TDCanvas 运行时审计（2026-09-26，真实素材非付费路径）

> 对象：TDCanvas web 版（锁定基线 `16b3127` 本地工作副本，`npm run dev` = Vite 7.3.6 @ localhost:3000）。
> 素材：[TEST_ASSETS.md](TEST_ASSETS.md)（10 图 / 2 音频 / 2 视频，用户提供）。
> **安全红线执行情况**：全程未配置 API Key、未点击任何生成入口、未启动 ComfyUI——零付费动作。
> 方法：ZCode 内置浏览器（IAB 1440×900）+ CUA 坐标交互 + DOM 快照 + 截图；文件注入走页面真实 `<input type=file>` 管线（见 §2 方法注记）。

## 1. 启动与首页（与静态分析逐项吻合）

- `npm run dev` 即起 Vite（748ms ready），`/canvas` 返回 200；首页结构 = banner 导航（我的画布/ComfyUI 本地/提示词库/我的资产/配置）+ hero「从一张画布开始」+ 最近画布 region + Agent complementary 面板（Codex 插件 / 本地 Agent 两种连接方式、Local URL 预填 `http://127.0.0.1:17371`、token 自动发现）——与 SOURCE_ANALYSIS §2.6/§5 一致。
- 视觉：暗色主题默认、点阵网格 + vignette、`live` 徽标、∞/2048 计数、X/Y 坐标装饰——canvasThemes + 氛围层运行时可见。

## 2. 画布创建与空态

- **`?mode=new` 自动创建项目并跳转 `/canvas/:id`**（运行时证实 index.tsx:30-41）；新项目默认标题「TDCanvas 2」（编号来源未查证，记录为观察）。
- 空态页 = 引导语「双击画布，自由创作」+ 快捷创作 5 芯片（文字/图片/视频/音频/上传素材）+ 左 Dock（新建(NEW 徽标)/搜索节点/资产/提示词库/历史/上传资产/画布外观/清空画布）+ 缩放 Dock（小地图/隐藏连线/网格吸附/重置视图/5–500% 滑杆/快捷键）——与 INTERACTION_CATALOG §5 逐项一致。

## 3. 节点创建与真实素材上传（核心成果）

1. **图片创作芯片** → 空图片节点（默认 620×350）+ 选中态（蓝框 + 左右 legacy 端口可见）+ 悬浮工具条（信息/删除/编辑/上传图片）+ **下方面板自动打开**：Aitudou 原生「文生图」面板（自动识别/未连接素材/参数 1k/2k/参考素材区「从画布连线后会自动带入参考素材」）——autoOpenPanel 与原生面板运行时证实。
2. **真实图片上传（1.7MB 陈默角色图）**：页面存在唯一全局隐藏多选 file input，其 accept 白名单与 `canvas-upload-material.ts` 的 KIND_BY_MIME 完全一致；经 DataTransfer 注入真实字节并 dispatch change → **空节点被原地替换**（replaceNodeWithMaterialFile）：节点标题变为文件名、按原图自然比例重设尺寸、悬浮工具条展开为完整图片集（信息/删除/存资产/下载/编辑/复制提示词/反推提示词/替换图片/裁剪/切图/放大/查看大图/更多）。
3. **第二张真实图片（3.9MB）** → 以**新建节点**方式入画 + 视口聚焦动画（focusNode）——「空节点原地替换、非空新建」双路径运行时证实。
4. 音频/视频：同 input 白名单包含 mp4/mov/avi/mkv/wav/flac（运行时取到 accept 属性原文）；因 IAB 不支持文件选择器，视频/音频的真实字节注入未在本轮执行（留待后续轮次），仅取证其空节点创建入口存在。

### 方法注记（自动化相关，供后续复跑）

- IAB 禁用文件选择器（`filechooser` capability_unsupported）→ 采用「复制真实素材到 `web/public/__rt__/`（ASCII 名）→ 页内 fetch 同源字节 → File+DataTransfer → input.files → change」管线，字节全程真实。
- Playwright locator 点击在本应用上普遍超时（空态引导层/画布氛围层拦截 actionability），`force:true` 亦无效；**CUA 坐标路径稳定可用**（配合截图定位）。
- `page.evaluate` 通道中途损坏（broker 响应不匹配后全部返回空对象），**`locator.evaluate` 通道完好**——页侧脚本一律经 `locator("body").evaluate` 执行；evaluate 字符串参数不被传递（arg 丢失），故采用同源 fetch 方案而非传 base64。

## 4. 画布交互运行时证实

| 交互 | 运行时结果 |
|---|---|
| 重置视图 | fit 动画后缩放 **77%**（clamp ≤100% 证实），两节点入画 |
| 节点拖拽 | CUA drag 平滑跟随，位置更新即时 |
| 连线建立 | 悬停陈默节点 → legacy 输出口可见 → 从 (802,357) 拖至 phone 输入口 (1018,383) → **贝塞尔连线即时生成**；两端节点进入 related 高亮 |
| 双击空白 | NodeCreateMenu「选择节点」= 文本/图片/视频/音频/组/ComfyUI 工作流/上传素材——注册表驱动菜单运行时证实（含内置 ComfyUI 工作流项） |
| 文本节点 | 创建即选中（520×300 默认），占位「双击编辑文字」+ 右上「生图」入口 + 悬浮工具条（编辑文字/生图/缩小/放大…）+ 下方面板「文本创作」 |

## 5. 运行时 vs 静态分析的偏差记录

1. **悬浮工具条不做视口 clamp**：节点中心偏左时工具条左溢出视口（「信息」按钮被裁切）——静态分析中「视口内 clamp」属右键菜单（canvas-context-menu.tsx:32-39），hover 工具条（canvasNodeToolbarAnchor）无 clamp；INTERACTION_CATALOG 未区分，已在此澄清。
2. **新项目默认标题「TDCanvas 2」**：0 画布时新建即为 2，编号规则未查证（可能为全局新建计数），记录为待查观察。
3. Playwright 自动化兼容性：官方操作路径全部可用（真人交互无障碍），但 aria 快照驱动的 locator 点击被画布覆盖层拦截——对任何想用 Playwright 驱动该画布的后续工作（含 clone 侧）是重要前车之鉴：应优先坐标路径或禁用氛围层。

## 6. 未覆盖（留待后续，均需用户再授权或非本轮范围）

- 视频/音频真实字节上传（V1/V2/A1/A2 已登记，方法同 §3，仅限 IAB 之外的环境或换 headless CDP）。
- 生成入口禁用态取证（未配 Key 时的报错文案）——本轮刻意未点击。
- 深色/浅色切换、i18n 切换、导出 zip、多画布切换、ComfyUI 面板空态。
