# 真实浏览器与确定性截图

## 目录

1. 浏览器工具选择
2. 环境与数据安全
3. 运行时取证
4. 截图标准
5. Manifest

## 1. 浏览器工具选择

按以下顺序使用第一个可用选项：

1. 用户明确指定的浏览器、标签页或浏览器会话；
2. 当前 Agent 运行时提供的原生计算机使用/浏览器控制工具；
3. 项目已经安装的 Playwright 与现有配置；
4. 本地 Playwright 临时脚本。

不能控制真实浏览器时停止并说明缺口。不得仅凭源码、路由或静态截图假装已经验证运行行为。

## 2. 环境与数据安全

- dev/staging 优先于 production；是否使用哪个环境由用户确认。
- 不修改 `.env`。使用命令级环境变量。
- 不读取、打印或写入 cookie、token、API key。
- 不使用真实客户数据。截图前主动检查用户名、项目名、URL、素材和网络面板。
- Mock 数据应真实可信并可复现，但必须明确为演示数据。
- 对高成本 Provider、付款、删除、发布和通知操作，在副作用发生前停止。
- 不为了截图绕过权限、强改数据库状态或调用未授权管理接口。

## 3. 运行时取证

每个步骤至少记录：

- route；
- 用户看到的入口和准确 UI 文本；
- role/name/label 等稳定 locator；
- 操作前后 DOM/ARIA 状态；
- 关键网络请求的 method、path、status 和响应业务结果；
- 成功判据；
- 失败时可恢复路径。

优先通过可访问性树和 DOM 判断状态。截图像素只用于解释界面，不用于确认按钮是否可用、请求是否成功或数据是否持久化。

## 4. 截图标准

默认：

- desktop viewport：`1280x720`；
- locale：`zh-CN`；
- 固定时区并记录实际值；
- 100% zoom；
- light/dark 只选一个，除非主题本身在范围内；
- `prefers-reduced-motion: reduce`；
- 等待 `document.fonts.ready`、网络稳定和关键 locator 可见；
- 同一批截图保持相同浏览器、viewport 和主题。

截图类型：

- **概览图**：保留导航和页面上下文；
- **步骤图**：裁剪至足以理解动作的区域；
- **结果图**：展示可识别的成功状态；
- **恢复图**：只用于高影响错误或容易误解的恢复动作。

### 目标高亮

使用 `<skill-dir>/scripts/highlight-target.js`：

1. 用 role/name/label 找到目标元素；
2. 取得元素自身的 bounding rect；
3. 在实时 DOM 中添加红框和步骤编号；
4. 截图；
5. 调用清理函数移除 overlay。

不要事后凭估计在 PNG 上画框。目标被 sticky header、滚动容器或弹窗遮挡时，先滚动和验证可见性，再计算位置。

Playwright 示例：

```javascript
await page.addScriptTag({ path: `${skillDir}/scripts/highlight-target.js` });
const target = page.getByRole("button", { name: "新建项目", exact: true });
await target.scrollIntoViewIfNeeded();
await target.evaluate((element) =>
  window.canvasUserManualHighlight.show(element, { step: 1 }),
);
await page.screenshot({ path: screenshotPath });
await page.evaluate(() => window.canvasUserManualHighlight.clear());
```

`show(...)` 是异步函数，必须 `await`。截图失败时也要在 `finally` 中调用 `clear()`，避免高亮污染后续截图。

## 5. Manifest

`screenshots/manifest.yml` 示例：

```yaml
screenshots:
  - file: screenshots/10-create-project-open-dialog.png
    task_id: create-project
    step: 1
    route: /projects
    viewport: 1280x720
    locale: zh-CN
    captured_at: 2026-09-20T12:00:00Z
    verified_locator: 'role=button name="新建项目"'
    visible_text: 新建项目
    alt: 项目列表右上角高亮显示“新建项目”按钮
    sha256: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

采集后计算真实 SHA-256，不得保留示例值或空值。后续更新先比较 route、locator、可见文本和截图哈希，只重拍受影响图片。
