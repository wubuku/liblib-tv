# Batch 31 Source Evidence

> 采样日期：2026-08-25  
> 目标页面：`https://www.liblib.tv/canvas?spaceId=670983&projectId=5f2550d0036944e2b618f494276fa1dd`

## Evidence Boundary

本批复用 Batch 30 已保存的线上 bundle 字符串和结构化研究，不重新识别
Batch 30 contact sheet。相关持久化证据：

- [`../liblib-canvas-batch30-2026-08-25/SOURCE_EVIDENCE.md`](../liblib-canvas-batch30-2026-08-25/SOURCE_EVIDENCE.md)
- [`../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json`](../liblib-seedance-2.5-2026-08-25/live-script-string-evidence.json)
- [`../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md)

## Picture Edit Store Contract

Batch 30 的 bundle extraction 已确认三项菜单动作不是临时 toast，而是进入
同一个全局 `usePictureEditStore`：

```text
onPictureEditClick(action)
  -> validate source
  -> pictureEditStore.open(action, sourceNodeId)
```

mode：

```text
subjectRemove
subjectModify
subjectReplace
```

## Tool And Mark Contract

active tools：

```text
point
box
brush
eraser
```

mark 记录至少包含：

- source frame time；
- recognition candidate；
- description；
- replacement image。

这说明标注不是只存在于画面像素上的临时选区，而是可被后续请求消费的
结构化编辑输入。

## Mode Rules

| Mode | Max marks | Required per valid mark |
|---|---:|---|
| `subjectRemove` | 4 | mark geometry |
| `subjectModify` | 4 | mark geometry + description |
| `subjectReplace` | 2 | mark geometry + replacement image |

可确认中文：

```text
点选
框选
画笔
橡皮
重置
确定
提交
分析中
描述想要如何更改画面
最多标记 {count} 处
本地上传
历史图库
```

## Recognition And Request Strings

已保存的 i18n 字符串还确认：

```text
未识别到可编辑对象，请点击主体区域重试
识别失败，请重试
```

主体编辑 prompt 语义：

```text
remove:  移除{subject}，移除后背景自然融合
modify:  将{subject}修改为：{desc}
replace: 将{subject}替换为{target}
```

本批不会把这些字符串扩展成真实服务响应。`主体 1/主体 2` 只作为 clone
本地候选标识，以便验证选中 mark 与模式校验。

## Source Validation

`validatePictureEditSourceVideo` 已在 Batch 30 记录：

- 只支持 MP4 / MOV；
- duration `<2.5s` 不支持；
- duration `>15s` 显示 `视频大于15秒，暂不支持该功能`；
- 单边分辨率范围 `700..4553px`；
- 像素面积不超过 `8294400`；
- 最大宽高比 `2.5`。

本批不改变默认 30 秒 fixture。为验证 editor-only 状态，专项脚本使用
测试页面的本地 duration override；该 override 是测试注入，不是产品新增入口。

## Unresolved Visual Questions

当前保存证据没有主体编辑器的完整登录态截图，因此以下不写成 source
geometry：

- 编辑器是节点下方 compact panel 还是更大的独立 surface；
- mark card 的确切尺寸、候选头像和识别动画；
- point/box/brush/eraser 的原始颜色与 pointer affordance；
- 替换图入口的真实弹层层级；
- submit 后原站 output 的确切选择生命周期。

本批的视觉尺寸、颜色和 output 选择规则会在 `PICTURE_EDIT_WORKFLOW.spec.md`
中标注为 clone calibration 或 inference，并在专项截图台账中单独记录。
