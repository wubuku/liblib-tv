# FrameOS 画布功能用户手册

本目录只覆盖 `frameos.cn` 的画布编辑功能，不覆盖账户、计费、发布或生成费用。

## 当前状态

- 目标源站：`https://www.frameos.cn/#/canvas/01M34E48BEEVEQXR93Y8N70Y5N/01M34E4AKBTXT72KFD3MCYZ6NV`
- 目标角色：已登录的普通画布创作者
- 深度：`thorough`
- 方法：由 `.agents/skills/web-studio-user-manual/` 的任务优先级、运行时取证、截图和回走审计流程管理。
- 证据边界：只有当前登录态浏览器中实际观察到的 DOM、ARIA、交互结果和安全网络证据才写入正文；早期 `docs/research/frameos/` 资料只作为候选线索。

## 入口

- [`task-inventory.yml`](task-inventory.yml)：任务范围、频率、影响和覆盖状态。
- [`PROGRESS.md`](PROGRESS.md)：探索、编写和验证进度。
- [`AUDIT.md`](AUDIT.md)：真实浏览器回走审计。
- [`screenshots/manifest.yml`](screenshots/manifest.yml)：正式截图登记与哈希。
- [`TEST_MEDIA_ASSETS.md`](TEST_MEDIA_ASSETS.md)：已获授权的本地图片、音频、视频测试输入及付费生成禁令。

手册正文按用户目标放在 `10-tasks/`；未完成 Gate A/Gate B 的任务不会写成已验证功能。
