# Smart Matting Workflow Specification

## Goal

复刻当前 LibTV ready-video 的主体编辑菜单纠偏和智能抠像画布 handoff：

```text
source video
  -> open smart-matting panel
  -> submit
  -> pending matting video
```

## Menu Contract

```typescript
type PictureEditAction =
  | "subjectRemove"
  | "subjectModify"
  | "subjectReplace";
```

菜单顺序：

| Key | Label | Batch 30 behavior |
|---|---|---|
| `subjectRemove` | 主体消除 | 30s source validation |
| `subjectModify` | 主体修改 | 30s source validation |
| `subjectReplace` | 主体替换 | 30s source validation |
| `matting` | 智能抠像 | open bottom panel |

trigger 显示第一项 label `主体消除` 和 chevron。

hover contract：

- pointer enter group：清除 close timer，`100ms` 后打开；
- pointer leave group：清除 open timer，`120ms` 后关闭；
- pointer 从 trigger 移到 menu 时仍在同一 wrapper，不关闭；
- click trigger 立即 toggle，支持非 hover 入口；
- click item 立即关闭。

## Subject Validation

本批只实现当前 30 秒 fixture 可达且 source-backed 的 duration guard：

```text
duration > 15
  -> 视频大于15秒，暂不支持该功能
  -> no node / edge / history change
```

完整 format、resolution、area、aspect 和 valid-duration editor transition 保留给
后续 picture editor batch。

## Panel Contract

- anchor：node bottom，offset `16px`；
- width：当前 `512px`；
- height：约 `48px`；
- shell：rounded `12px`、padding `8px`；
- left：close `32px` + `智能抠像`；
- right：power icon + `--` + generate `32px`；
- submit 中 generate button disabled，arrow 替换 spinner；
- close 返回普通 VideoGenerationPanel；
- submit success 关闭 matting panel，source 仍 selected。

## Metadata Contract

```typescript
interface SmartMattingMetadata {
  sourceNodeId: string;
  sourceLabel: string;
  sourcePosterUrl?: string;
  edgeId: string;
  provider: "volcano";
  taskType: "video";
  model: "volcano-portrait-matting";
  format: "WEBM";
  width?: number;
  height?: number;
  duration?: number;
  generatorType: "PICTURE_EDIT";
  isSmartMattingOutput: true;
}
```

## Graph Transaction

一次 store action：

1. snapshot 当前 graph；
2. resolve source absolute position；
3. parse source resolution；
4. find source-right available slot；
5. 创建 `512x288` pending video；
6. 创建 `source video -> output video` edge；
7. 保留 source selection；
8. 清空 redo stack。

首个 output：

```text
x = source absolute x + source width + 100
y = source absolute y
```

重复 output 使用现有 deterministic vertical slot search。这是 clone
approximation，不声明为原站完整 resolver。

## Result Rendering

- type：`video`；
- filename：`${sourceLabel}-智能抠像`；
- status：`pending`；
- model：`volcano-portrait-matting`；
- duration/resolution 沿用 source；
- body：`智能抠像结果 / 智能抠像 · 等待媒体资源`；
- 不复用 source poster，不声明透明通道已生成。

## Stable Selectors

- `[data-video-picture-edit-menu-trigger]`
- `[data-video-toolbar-menu="picture-edit"]`
- `[data-video-picture-edit-action]`
- `[data-video-picture-edit-feedback]`
- `[data-smart-matting-panel]`
- `[data-smart-matting-close]`
- `[data-smart-matting-power]`
- `[data-smart-matting-generate]`
- `[data-smart-matting-submitting]`
- `[data-smart-matting-output]`
- `[data-smart-matting-source-id]`
- `[data-smart-matting-edge-id]`
- `[data-smart-matting-provider]`
- `[data-smart-matting-model]`
- `[data-smart-matting-format]`

