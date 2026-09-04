# Batch 97 Spec：Agent 抽屉当前源站合同

> 证据来源：[`liblib-live-2026-09-05/README.md`](../liblib-live-2026-09-05/README.md) §5/§5.1/§5.2。
> 标签：`SF`=SOURCE_FACT，`CD`=CLONE_DECISION，`SU`=SOURCE_UNKNOWN。

## 1. 数据合同

### 1.1 Agent 模型目录（`SF`）

```ts
type AgentModelKind = "image" | "video";
interface AgentModelOption {
  id: string;          // 稳定 slug，clone 决策
  name: string;        // 源站名称
  description: string; // 源站说明
  premium: boolean;    // 💎
  kind: AgentModelKind;
}
```

图片（7）：`lib-image`(最新图片模型，长文本能力突出)、`general-image-pro`(最强图片编辑模型，一致性好)、`general-image-v2`(支持联网搜索、文字准确、速度更快)、`seedream-5-0-pro`(精准交互式编辑，支持原生多语言排版)、`style-image-v8-2`(电影感全面升级，精准还原光影、人物与真实材质)、`style-image-v8-1`(生图更连贯、细节更丰富、美学水准大幅提升)、`style-image-v7`(最佳美学、电影质感、创意能力强)。

视频（8）：`seedance-2-5`(💎最强视频模型，全能参考，30s音画同步)、`seedance-2-0-vip`(💎最强视频模型，会员专属通道，15s音画同步)、`minimax-h3`(💎全模态输入，多参数控制，多场景商用级生成)、`seedance-2-0-fast-vip`(💎最强视频模型极速快速版，会员专属通道，15s音画同步)、`wan-3-0-prime`(超快生成，全模态参考，超写实高一致性)、`wan-3-0`(全模态参考，支持文档与网页输入，超写实高一致性生成)、`kling-o3`(💎视频编辑模型、参考一致性、首尾同出、多镜头)、`kling-3-0`(💎视频生成模型，高质感、支持多镜头)。

### 1.2 生成模式（`SF`）

`manual`：手动模式 / Agent 在每次生成前询问；`auto`：自动模式 / Agent 完全自动生成。默认 `auto`（源站勾选态）。

### 1.3 Skill 推荐第一批（`SF`，id 为 `CD`）

`pixar` 皮克斯动画广告 `/pixar-animated-ad-creator`；`viral` 爆款拉片复刻 `/viral-video-replicator`；`neo-china` 新中式美学TVC `/neo-chinese-aesthetic-tvc`；`wuxia` 古典武侠电影全流程导演 `/hujinquanwuxia`。第二批维持现有 clone-shaped 填充（`CD`）。

## 2. 组件合同（`AgentDrawer`）

1. 头部（`SF`）：标题 `新对话`；按钮 aria：`当前已是新对话`(disabled)、`历史对话`、`新对话无法分享`(disabled)、`Agent 设置`、`CLI & Skill`、`关闭`。`关闭` 调用既有 `toggleAgent`；其余按钮为可见但无后端动作（`SU`/`CD`：不伪造行为，不弹菜单）。
2. Skill 区标题（`SF`）：`editorMode === "storyboard"` → `让 Skill 帮你迈出第一步`；否则 `选一个 Skill，让创作更快一步`。`换一批` 循环批次并清空选择。
3. Composer 控件（`SF`）：`添加附件`、`选择模型`、`Skill`、`生成模式`、`Send`。`选择模型`/`生成模式` 开合菜单（互斥，开一个关另一个）；`添加附件`/`Skill` 点击写 `data-agent-status` 本地提示（`CD`）。textarea placeholder 与 Send/status 行为不变。
4. 模型菜单（`SF`+`CD`）：`data-agent-model-menu`；标题 `选择模型`；锚点 tab `图片`/`视频`（aria-pressed）；单滚动列表两个分区头 `图片`/`视频`；行结构：名称 + 说明 + premium `💎` + 右侧 `+` 按钮；点击行内 `+` → 该行进入选中态（√，aria-pressed，`CD`），再点取消。打开时锚点 tab 高亮 `图片`。
5. 生成模式菜单（`SF`）：`data-agent-mode-menu`；两行带说明，当前项 √（aria-checked）；点击切换，不关闭菜单行为允许（`CD`：保持开启便于对照）。
6. 两个菜单均为抽屉内绝对定位浮层；Escape 关闭已开菜单（`CD`，不触抽屉关闭）；菜单开时不阻塞 composer 编辑。

## 3. 验证断言（`verify-liblib-batch97.py`）

desktop `1440x900`：

1. 打开 `/` → 打开 Agent；断言头部 6 按钮 aria 与两个 disabled。
2. 断言第一批 4 卡名称与 handle；点 `pixar` 卡 → textarea 值 `皮克斯动画广告`；`换一批` → 第二批出现、第一批消失。
3. 断言 composer 控件 aria 集合。
4. 开 `选择模型`：断言标题、tab `图片`/`视频`、分区头 `图片`/`视频`、7+8 行名称齐全、视频区 premium 数=6；点 `lib-image` 行 `+` → 选中态；再点取消。
5. 开 `生成模式`：断言两行与说明、`auto` aria-checked=true；点 `manual` → checked 迁移。
6. Escape 关菜单不关抽屉；`关闭` 关抽屉；全程零 console/pageerror/requestfailed。

## 4. verifier replacement（batch14）

- `textarea.input_value() == "皮克斯动画风格"` → `"皮克斯动画广告"`；
- `get_by_role("button", name="关闭 Agent")` → `name="关闭"`（exact）；
- 依据：2026-09-05 源站复核（本 spec §1.3、§2.1）。记录于 `LIBTV_VERIFIER_REPLACEMENT_MAP.md`。
