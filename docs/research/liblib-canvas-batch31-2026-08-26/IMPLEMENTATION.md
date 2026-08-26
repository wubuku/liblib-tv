# Batch 31 Implementation Log

> 状态：实现、专项验证、跨批回归和工程门禁均已完成。

## Planned Protection Points

1. source evidence、缺口排序、workflow spec 和 component spec；
2. mark 类型、PictureEditPanel、VideoNode 接线和 store graph transaction；
3. focused Playwright、clone screenshot ledger 和零浏览器错误；
4. 跨批回归、工程门禁、最终 handoff 和 commit/push。

## Core Implementation

- 新增 `PictureEditMark`、`PictureEditReplacement`、
  `PictureEditMetadata` 和 `createPictureEdit`。
- `PictureEditPanel` 共享三种主体编辑模式，使用 normalized point/box/brush
  mark 和本地撤销/重做/重置。
- 视频画面覆盖层支持点选、框选、画笔、橡皮、mark 选择、拖动和框选角点
  调整；每个 mark 保存当前 frame time 和本地候选标签。
- `主体修改` 为每个 mark 提供描述字段；`主体替换` 提供
  `本地上传 / 历史图库` 两个本地状态入口。
- submit 在校验通过后显示 `分析中`，再以一个 graph transaction 创建
  `512x288` pending video 和 direct source edge。
- pending output 记录 mode、marks、frame time、描述/替换图来源、source、
  request mode 和 edge ID；不复用 source poster。
- 开发态 `?duration=10` 仅用于测试可达 editor-only 状态；默认 30 秒 fixture
  的 source guard 保持不变，production 不读取该 override。

## Current State

- Batch 30 已完成主体菜单纠偏和智能抠像。
- 默认 ready-video fixture 为 `30s`，三项主体编辑保留 source-backed
  `视频大于15秒，暂不支持该功能`；source-compatible duration 通过测试态
  `?duration=10` 进入共享标注器。
- Batch 31 已将可实施的 mark/tool/mode contract 和实现写入：
  - [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md)
  - [`PLAN.md`](PLAN.md)
  - [`PICTURE_EDIT_WORKFLOW.spec.md`](PICTURE_EDIT_WORKFLOW.spec.md)
  - [`../components/PictureEditPanel.spec.md`](../components/PictureEditPanel.spec.md)

## Browser Smoke

2026-08-26 headless Chromium `929x874` / `390x844`：

- 默认 30 秒 source 的三项主体动作均显示精确 guard，graph 保持 `1 node /
  0 edge`；
- `subjectRemove` 通过 point、box、brush 创建 3 个 mark，eraser 删除后
  undo/redo/reset 均恢复预期计数；
- `subjectModify` 无描述时 submit disabled，填写描述后进入 `分析中`；
- `subjectReplace` 无替换图时 submit disabled，点击本地上传入口后可提交；
- 三次提交形成三个按右侧 deterministic slot 排布的 pending output，source
  保持唯一 selected；
- zero console/page errors，mobile 无 document 横向 overflow。

## Focused Playwright

新增 [`scripts/verify-liblib-batch31.py`](../../../scripts/verify-liblib-batch31.py)，
实际通过：

- 默认 duration guard 和无 graph mutation；
- 三模式标题、上限、四工具、point/box/brush/eraser；
- normalized mark、frame time、brush path、box handles；
- mark local undo/redo/reset；
- modify description 校验；
- replace upload/history replacement 状态；
- submitting spinner、pending output、mode/model/request metadata；
- direct edge、source selection、`+100` world-unit placement、重复避让；
- atomic graph undo/redo、多选隐藏、390px 自然裁切和 zero browser errors。

一次性视觉识别已写入 [`SCREENSHOT_ANALYSIS.md`](SCREENSHOT_ANALYSIS.md)；
后续先读台账，不重复识别本批 contact sheet。

## Verification Results

2026-08-26，在本地开发服务器 `http://localhost:3000` 上完成：

```text
python3 scripts/verify-liblib-batch31.py                         PASS
python3 scripts/verify-liblib-batch9.py                          PASS
python3 scripts/verify-liblib-batch15.py                         PASS
python3 scripts/verify-liblib-batch26.py                         PASS
python3 scripts/verify-liblib-batch27.py                         PASS
python3 scripts/verify-liblib-batch28.py                         PASS
python3 scripts/verify-liblib-batch29.py                         PASS
python3 scripts/verify-liblib-batch30.py                         PASS
python3 scripts/verify-liblib-batch31.py                         PASS
npm run docs:check                                                PASS
npm run check                                                      PASS
git diff --check                                                   PASS
```

`npm run check` 没有 error；lint 保留 9 个既有 warning，分布在 FrameOS、
`CustomHandle` 和既有图片渲染代码。`next build` 另提示仓库上级存在
`/Users/yangjiefeng/package-lock.json`，属于 workspace root 推断 warning，
不影响构建结果。

跨批脚本会刷新同名 clone 视觉参考文件。Batch 9、15、26、27、28、29、30
的脚本断言和零浏览器错误均通过；这些刷新后的图片是当前实现的验证产物，
不构成新的原站视觉证据，也没有重复进行截图识别。

## Final Handoff

- 本批已完成：三类主体编辑共享标注器、模式校验、分析态、pending graph、
  metadata、history 和响应式验证。
- 原站证据仍以 [`SOURCE_EVIDENCE.md`](SOURCE_EVIDENCE.md) 为准；候选标签、
  替换图入口、标记视觉和 pending media 都保持 clone-only 边界。
- 后续继续探索前先读本目录的 `README.md`、`PLAN.md`、`SOURCE_EVIDENCE.md`、
  `SCREENSHOT_ANALYSIS.md` 和本文件；不要重复识别已登记 contact sheet。
- `?duration=10` 只属于开发态专项测试设施，不是用户功能或产品能力。
