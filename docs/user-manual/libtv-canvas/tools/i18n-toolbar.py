#!/usr/bin/env python3
"""Batch FU-3：把 FU-2 抽到的 i18n key 翻成界面上的真实中文。

为什么单独一个脚本：FU-2 给出的是 key（如 `common:imgEditorBrushTool`），
key 本身不是用户看得见的文案。而**可复算的数字不许手抄进正文**（lib.mjs 头第三条），
同一个道理：key → 文案的映射也不许手抄。

顺带校正 FQ 立的另一条口径：`i18n-canvas.json` 里的 key **被剥掉了命名空间**
（源码写 `common:imgEditorAnnotate`，抓表时存成 `imgEditorAnnotate`）。
所以查表要 `common:` 与 `canvas:` 分别去 `imgEditor*` / `canvas*` 里找。
⭐ 本脚本两处都试，并把命中的那条记下来 —— 「只试一个」就会漏。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS = os.path.join(ROOT, 'tools', '.evidence', 'i18n-canvas.json')

# FU-2 实测抽到的 key（逐字，含命名空间）
KEYS = [
    # BatchSelectionBarShell
    'common:exitBatchOperation', 'canvas:selectedCount', 'canvas:selectAllCurrentPage',
    # LayerBatchActionBar
    'common:close', 'canvas:imageLayerEditorHint', 'canvas:imageLayerMerge',
    # PortraitTextureToolbar
    'canvas:slashScenePortraitTextureAdjustment',
    'common:imgEditorPortraitAdjust', 'common:imgEditorMoodAdjust',
    # GroupNodeToolbar
    'canvas:groupNodeToolbarPromptReferenceimageGenerateConnect',
    'canvas:groupBatchGenerateVideo', 'canvas:groupUpdateToolbox',
    'canvas:groupAddToTeamToolbox', 'canvas:groupAddToToolbox',
    'canvas:groupNeedAllImageNodes', 'canvas:groupConvertToStoryboard',
    'canvas:groupUngroup', 'canvas:groupBatchDownload',
    'canvas:noDownloadableInSelection',
    # CharacterGroupToolbar
    'canvas:characterStudioEdit', 'canvas:characterStudioUpdateAvailable',
    'common:loading', 'common:loadFailedPleaseRetry',
    'canvas:characterStudioReferences', 'canvas:characterStudioReferenceNumber',
    'canvas:characterStudioSyncReference',
    # AnnotateToolbar
    'common:imgEditorCloseAnnotate', 'common:imgEditorAnnotate',
    'common:imgEditorBrushTool', 'common:imgEditorRectTool',
    'common:imgEditorTextTool', 'common:color', 'common:imgEditorLineWidth',
    'common:undo', 'common:redo', 'common:save', 'common:imgEditorSaveAnnotate',
    # AudioNodeToolbar
    'common:clipTrimTitle', 'common:clipSpeedTitle',
    'canvas:audioSmartSplitTooltip', 'canvas:audioSmartSplitTitle',
    'canvas:audioEditCustomSplitTitle', 'canvas:scriptV2FloatingToolbarDownload',
    'canvas:audioNodeSharedClose', 'canvas:audioNodeSharedSelect',
    'canvas:audioNodeSharedInput', 'canvas:audioNodeSharedConfirm',
    'canvas:audioNodeSharedClose2', 'canvas:audioNodeSharedAudioGenerate',
    'canvas:videoNodeGenerate',
]


def main():
    if not os.path.isfile(CENSUS):
        print(f'!! 找不到 {CENSUS}，先跑 i18n-census.py')
        return 1
    表 = json.load(open(CENSUS, encoding='utf-8'))
    # ⛔ 表不是平铺的 dict：顶层是 {'条数','表','来源','各文件','分组'}，
    # 真正的 key→文案在 `表` 这一层。
    # （FU-3 第一次跑就是漏了这一层 ⇒ 50 条全报「缺失」，
    #   差点被当成「这批 key 全都不存在」写进手册 —— 又一次「我的提取没命中」。）
    if '表' in 表:
        表 = 表['表']

    # 键是剥掉命名空间后存的
    无前缀 = {}
    for k, v in 表.items():
        无前缀.setdefault(k, (k, v))

    出 = []
    缺失 = []
    for full in KEYS:
        ns, _, name = full.partition(':')
        # 两种都试：`imgEditorBrushTool` 与 `canvasFoo` 都是真实形态
        cands = [name, full, name.replace('canvas', '', 1) if ns == 'canvas' else name]
        hit = None
        for c in cands:
            if c in 无前缀:
                hit = (c, 无前缀[c][1])
                break
        if hit:
            出.append((full, hit[0], hit[1]))
        else:
            缺失.append(full)

    print(f'键 {len(KEYS)} 条：命中 {len(出)}，缺失 {len(缺失)}\n')
    print(f'{"源码里的 key":<58} {"表里实际存的 key":<40} 界面文案')
    print('─' * 120)
    for full, real, val in 出:
        v = val if isinstance(val, str) else json.dumps(val, ensure_ascii=False)
        print(f'{full:<58} {real:<40} {v[:90]}')
    if 缺失:
        print('\n缺失的 key（表里查无此条，别据此断定界面上没有）：')
        for m in 缺失:
            print('  -', m)
    return 0


if __name__ == '__main__':
    sys.exit(main())
