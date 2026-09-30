# 源站访问阻塞记录：frameos.cn 人机验证（2026-10-01）

> 状态：**BLOCKED**。所有需要 frameos.cn 登录态的增量采样在本轮全部顺延。
> 本文件的作用是避免后续 agent 重走这条已证伪的路。

## 现象

三条独立路径尝试登录 frameos.cn，均卡在「确定你不是机器人」人机验证：

| # | 尝试 | profile | CDP 端口 | 结果 |
|---|---|---|---|---|
| 1 | 新开有头浏览器（`scripts/open-frameos-login-browser.py`） | `~/frameos-login-profile`（全新） | 9333 | 弹人机验证；**用户手动点击仍判失败** |
| 2 | 探针回退路径（`scripts/probe-frameos-source.py`） | `~/libtv-cdp-profile` | — | 重定向 `/login` |
| 3 | 复用已授权的 :9222 会话开新标签（`scripts/open-frameos-in-existing-browser.py`） | `~/libtv-cdp-profile`（**已持有 liblib.tv 登录态**） | 9222 | 仍停在 `/login`，人机验证依旧 |

**关键否证**：路径 3 用的 profile 已经过长期真实使用并持有有效登录态，
但 frameos.cn 依然弹验证 → 判定**与 profile 新旧无关**，而是该站点对
**自动化启动的浏览器**（`--remote-debugging-port` / Playwright persistent
context 指纹） uniformly 拦截。人工点击无效说明校验绑定浏览器指纹而非行为。

## 为什么不继续尝试绕过

人机验证是站点的反自动化访问控制。尝试规避（指纹伪装、注入绕过、
第三方打码服务）属于绕过访问控制，**不做**。本轮据此停止源站采样。

## 环境事实（供后续参考）

- `:9222` = 项目既有取证通道，profile `libtv-cdp-profile`，持有 liblib.tv 登录态。
  属**他人/用户已在使用**的浏览器 —— 不要关闭或重启它。
- `:9444` = jimeng 手册取证通道，profile `/tmp/jimeng-manual-profile`，
  当前停在 jimeng.ai-canvas。与 frameos 无关。
- `/tmp/frameos-probe-video.webm` 是 batch225/230 依赖的探针素材，**macOS 会清理
  /tmp**。重建命令（ffmpeg 来自 runner 实际使用的 pyenv 解释器）：

  ```bash
  FF=$(~/.pyenv/versions/3.10.6/bin/python -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())")
  "$FF" -y -f lavfi -i "testsrc=size=320x180:rate=10:duration=5" \
        -c:v libvpx-vp9 -b:v 200k -an /tmp/frameos-probe-video.webm
  ```

  本轮曾因此误判 2 个验证器失败（ENOENT），重建后 batch225/230 均 PASS。
  **看到 ENOENT 先重建素材再判定回归。**

## 顺延队列（需已登录源站会话）

- 剪辑台编辑器采样
- 内容图片工具条 ⛶ 全屏查看采样
- 裁剪确认行为采样
- 分组端口提交语义采样
- 双分组小地图判定
- 规格宽高比完整清单
- 载荷级节点清单验证

## 可继续推进的方向（不需要源站）

源站阻塞**不构成停工理由**。可做的批次：

1. **克隆侧缺陷挖掘**（Batch 327 的做法）：用探针在克隆自身运行时找真实缺陷，
   修 + 加验证器 + 记录。id 碰撞就是这类，收益确定且不依赖源站。
2. **既有证据的实现补齐**：源站早期采样已给出结论、但克隆未落地/未覆盖断言的项
   （见 `COVERAGE_MATRIX.md` 的 🔵 与「克隆已实现但无专项断言」行）。
3. **文档/账本订正**：源站不可访问时无法复核，标注为待复核而非直接删行。

## 恢复条件

需要以下任一：

- 用户在**非自动化**的日常浏览器中登录 frameos.cn，并提供可复用的已登录会话；
- 或站点侧不再对该环境弹人机验证；
- 或用户明确授权改用其他取证途径（截图/录屏/手工操作后口述观察）。
