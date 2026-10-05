#!/usr/bin/env python3
"""Batch FV-2：坐实 FQ 留下的那个死结 —— 节点标题上的数字到底是什么。

FQ-2 实测出：画布上两个 `音频节点` 都写着 `1`、两个 `图片节点` 都写着 `2`，
而 `智能剪辑 4` / `视频节点 3` / `导演台 5` 含义不明 ⇒ 当时判为「📖 未验」。

⭐ 本轮在 8189 条文案表里找到了直接答案（**逐字**）：

    defaultTextNodeName          文本节点 {index}
    defaultImageNodeName         图片节点 {index}
    defaultVideoNodeName         视频节点 {index}
    defaultAudioNodeName         音频节点 {index}
    defaultVideoClipNodeName     智能剪辑 {index}
    defaultDirectorConsoleNodeName  导演台 {index}
    defaultVideoGroupNodeName    视频组 {index}
    directorCharacterGroupAutoLabel   角色组{index}
    imgEditorGridCellNodeName    宫格分镜 {row}-{col}
    imgEditorGridHdNodeName      宫格高清 {row}-{col}

⇒ **`{index}` 确实是模板占位符**，而 FQ 那个「两个音频节点都是 1」的读数
**恰好是同一个 `index` 被复用**（不是同名实例序号，也不是类型内计数）。

⭐⭐ 本脚本要做的，是把这些模板与**手册正文里写死的那些具体读数**并排，
让人一眼看出「哪些数字是实测、哪些是模板」。

⛔ 只读、幂等。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CENSUS = os.path.join(ROOT, 'tools', '.evidence', 'i18n-canvas.json')

# 节点名模板：key → (模板, 手册里实测到的具体读数)
节点模板 = {
    'defaultTextNodeName': ('文本节点 {index}', '文本节点 1'),
    'defaultImageNodeName': ('图片节点 {index}', '图片节点 2'),
    'defaultVideoNodeName': ('视频节点 {index}', '视频节点 3'),
    'defaultAudioNodeName': ('音频节点 {index}', '音频节点 1'),
    'defaultVideoClipNodeName': ('智能剪辑 {index}', '智能剪辑 4'),
    'defaultDirectorConsoleNodeName': ('导演台 {index}', '导演台 5'),
    'defaultVideoGroupNodeName': ('视频组 {index}', '视频组（未在主画布见到）'),
    'defaultVideoGroupNodeTitle': ('视频组 {index}', '同上'),
    'directorCharacterGroupAutoLabel': ('角色组{index}', '角色组（未见到）'),
    'imgEditorGridCellNodeName': ('宫格分镜 {row}-{col}', '未见到'),
    'imgEditorGridHdNodeName': ('宫格高清 {row}-{col}', '未见到'),
}

# 智能剪辑是 video-clip，但它在 class 上也是 react-flow__node-video（BA1 记过）
特殊 = {
    'defaultShotBreakdownNodeName': '逐帧拉片（FQ 实测标题**没有数字**）',
    'defaultScriptV2NodeName': '脚本生成器（FQ 实测标题**没有数字**）',
}


def main():
    d = json.load(open(CENSUS, encoding='utf-8'))
    表 = d['表'] if '表' in d else d
    手册 = ''
    for f in os.listdir(os.path.join(ROOT, '10-tasks')):
        if f.endswith('.md'):
            手册 += open(os.path.join(ROOT, '10-tasks', f), encoding='utf-8').read()
    手册 += open(os.path.join(ROOT, '20-reference.md'), encoding='utf-8').read()

    print(f'文案表 {len(表)} 条\n')
    print(f'{"key":<34} {"模板（表里逐字）":<26} {"手册里的实测读数":<30} 正文里出现过')
    print('─' * 118)
    for k, (模板, 实测) in 节点模板.items():
        真 = 表.get(k, '⛔ 表里没有这一条')
        在 = '✅' if 实测.split('（')[0] in 手册 else '—'
        print(f'{k:<34} {真:<26} {实测:<30} {在}')
    print('\n两类「实测标题不带数字」的节点：')
    for k, v in 特殊.items():
        真 = 表.get(k, '⛔ 表里根本没有这个 key')
        print(f'  {k:<34} {v}\n    表里对应：{真}')

    # 关键验证：FQ 那个「两个音频节点都是 1」的读数，与模板是否自洽
    print('\n⭐ 结论核对（FQ-2 读数 vs 模板）：')
    print('  手册写：两个 `音频节点` 都显示 `1`，两个 `图片节点` 都显示 `2`')
    print(f'  表里  ：`{表.get("defaultAudioNodeName")}` / `{表.get("defaultImageNodeName")}`')
    print('  ⇒ 同一个类型共用同一个 index ⇒ 标题数字**不是**「同名实例序号」')
    print('  ⇒ 也**不是**类型内从 1 递增的计数（否则两个音频节点应是 1 和 2）')
    print('  ⛔ 剩下的可能：index 来自**更早的全局计数**（如建节点时的画布节点总数），')
    print('     刷新/重排后不再自增。**这仍属推断，📖 未验** —— 要复现得再建一次节点看数字变不变。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
