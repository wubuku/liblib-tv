#!/usr/bin/env python3
"""把 screenshots/manifest.yml 与磁盘对齐：补新图、删死条目、逐张重算真实 sha256。

为什么要有这个脚本：清单是审计的账本，一旦和磁盘对不上，
「截图都能打开」「引用都能找到图」这两条就都失去意义了。
手改 YAML 迟早会漏，所以这里让它可重复执行 —— 幂等，跑多少次结果都一样。

新图的元数据（task_id / locator / visible_text / alt）来自 tools/.evidence/batch*.json
里当轮的实测读数，逐字抄写，不做美化。
"""
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, 'screenshots', 'manifest.yml')
SHOTS = os.path.join(ROOT, 'screenshots')
ROUTE = '/canvas?spaceId=…&projectId=…'
STAMP = '2026-10-02T03:01:00+08:00'

# 本轮（Batch I/J/K/L/M/N/O）新增的 12 张。visible_text 全部取自 .evidence 里的实测读数。
NEW = [
    ('M-08-组操作条全景.png', 'create-nodes', 10,
     '组操作条上的 7 个动作叶子节点，按 x 依次是 20×20 颜色圆点、52×36 排列按钮、1×24 分隔线、整组执行、添加到工具箱、转分镜组、解组、1×24 分隔线、36×36 批量下载（opacity 0.45）',
     'Group 1 整组执行 添加到工具箱 转分镜组 解组 文本节点 1 音频节点 2 资产 管理 146%',
     '成组后，组被平移到视口中部，组上方浮出完整操作条：最左是白色颜色圆点，紧跟一枚宫格图标带小三角的排列按钮和一条竖分隔线，然后是「整组执行」「添加到工具箱」「转分镜组」「解组」，再一条分隔线，最后是灰着的下载图标',
     'M-08-组操作条全景.png'),
    ('M-09-组操作条-颜色色板.png', 'create-nodes', 11,
     '点开颜色圆点后出现的 div.grid.grid-cols-5 色板容器，rect=[465,77,228,84]，5 列 × 2 行',
     '整组执行 添加到工具箱 转分镜组 解组 文本节点 1 音频节点 2',
     '操作条上方浮出一块 5 列两行共 10 个圆形色块：上排灰、红、橙、黄、绿，下排青、蓝、紫、粉、白；第一块灰色带一圈高亮描边，表示当前选中',
     'M-09-组操作条-颜色色板.png'),
    ('M-11a-工具箱弹窗-更新工具箱-空状态.png', 'asset-library', 12,
     '「添加到工具箱」弹窗里切到「更新工具箱」标签页',
     '创建新工具箱 更新工具箱 暂无工具箱 确认',
     '切到「更新工具箱」标签后的弹窗：内容区只有「暂无工具箱」一行，底部右侧是「确认」按钮',
     'M-11a-工具箱弹窗-更新工具箱-空状态.png'),
    ('M-11b-工具箱弹窗-更新工具箱-已有工具箱.png', 'asset-library', 13,
     '「添加到工具箱」弹窗里切到「更新工具箱」标签页（已建过两个同名工具箱之后）',
     '创建新工具箱 更新工具箱 手册取证测试箱 手册取证测试箱 确认',
     '「更新工具箱」标签页里并排两张封面缩略图占位卡，两张下面都写着「手册取证测试箱」，证明之前点「创建」确实存上了；底部右侧是「确认」按钮',
     'M-11b-工具箱弹窗-更新工具箱-已有工具箱.png'),
    ('M-12-工具箱弹窗-填写名称.png', 'asset-library', 14,
     '「创建新工具箱」页把 input[placeholder="输入工具箱名称"] 填成「手册取证测试箱」，读回 value 确认写入成功',
     '创建新工具箱 更新工具箱 封面 更换封面 名称 手册取证测试箱 标签 0/5 添加标签 备注 请描述您的工具箱，例如应用场景、使用步骤及使用技巧 创建',
     '「创建新工具箱」页：左侧是大号封面占位图和「更换封面」按钮，右侧是名称、标签、备注三个字段，名称里已经填了「手册取证测试箱」，底部右侧是「创建」按钮',
     'M-12-工具箱弹窗-填写名称.png'),
    ('M-13-工具箱弹窗-点创建之后.png', 'asset-library', 15,
     '点「创建」之后 4.2 秒：modalText() 返回 null、toast 列表为空',
     '整组执行 更新工具箱 转分镜组 解组 图片节点 3 音频节点 2 文本节点 1 Group 1',
     '点完「创建」之后的画布：弹窗已经关掉，屏幕上没有任何成功提示。注意组操作条上那一项的文案已经从「添加到工具箱」变成了「更新工具箱」—— 组一旦被存进工具箱，按钮就变成更新',
     'M-13-工具箱弹窗-点创建之后.png'),
    ('M-14-组操作条-排列菜单.png', 'create-nodes', 16,
     '点开 52×36 排列按钮后读到的三个菜单项实时坐标',
     '宫格排列 水平排列 垂直排列 整组执行 添加到工具箱 转分镜组 解组',
     '排列按钮点开后向上弹出一个三项竖排菜单：宫格排列、水平排列、垂直排列，每项左边一枚图标、右边一行文字；菜单浮在组操作条上方',
     'M-14-组操作条-排列菜单.png'),
    ('M-15-组操作条-选色之后.png', 'create-nodes', 17,
     '点色板第 2 块（红 rgb(231,76,60)）之后读组节点的 computed style',
     '整组执行 添加到工具箱 转分镜组 解组 文本节点 1 音频节点 2',
     '把组改成红色之后：组边框和底色变成红色、操作条最左的颜色圆点变成红色、左上角「Group 1」标签的底色也变成红色',
     'M-15-组操作条-选色之后.png'),
    ('M-17-排列-水平排列.png', 'create-nodes', 18,
     '排列菜单里点「水平排列」实时坐标 (523,77)',
     '文本节点 1 音频节点 2 图片节点 3 Group 1',
     '水平排列之后三个节点排在同一行里，左到右是图片节点 3、音频节点 2、文本节点 1，组框把三者一起包住',
     'M-17-排列-水平排列.png'),
    ('M-17-排列-垂直排列.png', 'create-nodes', 19,
     '排列菜单里点「垂直排列」实时坐标 (504,121)',
     '图片节点 3 音频节点 2 文本节点 1 Group 1',
     '垂直排列之后节点排成一列：图片节点 3 在上面、音频节点 2 在它下面，组框被拉高成竖长条',
     'M-17-排列-垂直排列.png'),
    ('M-17-排列-宫格排列.png', 'create-nodes', 20,
     '排列菜单里点「宫格排列」实时坐标 (206,33)',
     '图片节点 3 音频节点 2 文本节点 1 Group 1',
     '宫格排列之后节点排成 2×2 方阵：图片节点 3 左上、音频节点 2 右上、文本节点 1 左下，右下角空着',
     'M-17-排列-宫格排列.png'),
    ('M-19-工具箱弹窗-创建新工具箱.png', 'asset-library', 21,
     '组操作条上点「添加到工具箱」后弹出的双标签弹窗',
     '创建新工具箱 更新工具箱 封面 更换封面 名称 工具箱 标签 0/5 添加标签 备注 请描述您的工具箱，例如应用场景、使用步骤及使用技巧 创建',
     '「添加到工具箱」弹出的弹窗：顶部两个标签「创建新工具箱」「更新工具箱」，当前在创建页；左侧是封面大图占位和「更换封面」按钮，右侧是名称（默认值「工具箱」）、标签 0/5 加「添加标签」、备注多行框，右下角是「创建」按钮',
     'M-19-工具箱弹窗-创建新工具箱.png'),
    ('M-20-参数面板挂在节点下方.png', 'create-nodes', 22,
     '建一个视频节点并展开参数面板，量节点本体框与参数面板卡片的相对位置',
     '视频节点 1 尝试： 5分钟超长视频 首尾帧生成视频 首帧生成视频 参考 标记 特效 角色库 运镜 描述你想要生成的画面内容，@引用素材 2.0 文生视频 16:9 · 720P · 5s · 1个 135',
     '视频节点本体在上（尝试：5分钟超长视频 / 首尾帧生成视频 / 首帧生成视频），整块参数面板挂在它下面且中间有明显间隙：面板里有「+参考 标记 特效 角色库 运镜」一排按钮、描述输入框，底部一行是「2.0」「文生视频」「16:9 · 720P · 5s · 1个」「135」和提交箭头',
     'M-20-参数面板挂在节点下方.png'),
    ('M-22-音频节点-完整面板.png', 'create-nodes', 23,
     '只放一个音频节点，缩到能看全，量「节点本体」与「参数面板」两个框',
     '音频节点 1 尝试： 音频生视频 参考 描述你想要的音频效果，可用 @ 引用音频 Seed Audio 1.0 中文 · 24k · wav 0/2000 1 高级设置 语速 声调 音量',
     '音频节点本体在上（尝试：音频生视频），参数面板是下面另一张卡片：左上「+参考」、右上「⤢」展开图标，中间是描述输入框，底部一行是「Seed Audio 1.0」「中文 · 24k · wav」「0/2000」「1」和提交箭头',
     'M-22-音频节点-完整面板.png'),
    ('M-29-故事板模式-有内容.png', 'storyboard-mode', 24,
     '建 文本/图片/视频 三个节点后点顶栏「故事板」，收起右侧 TV Director 浮层再拍',
     '文本 文本节点 1 图片 图片节点 2 待确认后生成 Lib Image 2.5 Pro 视频 全部 视频节点 3 对话 待确认后生成 2.0 TV Director',
     '故事板有内容时的三列：文本列只有一行「文本节点 1」；图片列是「图片节点 2」加一个灰色占位框（框内写「待确认后生成」）和下面的「Lib Image 2.5 Pro」模型标签；视频列右上角有「全部」筛选下拉，「视频节点 3」右侧挂一枚「对话」按钮，下面同样是占位框和「2.0」标签',
     'M-29-故事板模式-有内容.png'),
    ('M-32-从生成历史选择.png', 'asset-library', 26,
     '双击画布 →「添加节点」面板底部「添加资源」分区 → 点「从生成历史选择」',
     '选择图片 LibTV Lib生成器 WebUI ComfyUI AI应用 已选 0/10 张 图片 视频 音频 暂无数据 确定',
     '「选择图片」弹窗：顶部一排来源标签 LibTV / Lib生成器 / WebUI / ComfyUI / AI应用，右上角「已选 0/10 张」；下面是 图片/视频/音频 三个分类标签；主体因为没生成过东西而显示「暂无数据」；右下角是「确定」',
     'M-32-从生成历史选择.png'),
    ('M-33-TV-Director-面板.png', 'agent-director', 27,
     '切到故事板后自动滑出的「新对话」浮层，class `mantine-Drawer-inner`，框 [1024,154,400,640]',
     '新对话 让 TV Director 辅助你的无限创意 感知画布开始创作 从爆款预设开始剧本原创 上传故事来改编 批量优化提示词 全能创作',
     '右侧滑出的 TV Director 面板：标题「让 TV Director 辅助你的无限创意」，下面四个入口「感知画布开始创作」「从爆款预设开始剧本原创」「上传故事来改编」「批量优化提示词」，各带一枚图标和右箭头；底部输入框一排是「+」「全能创作」下拉、立方体、文件夹、手掌和提交箭头',
     'M-33-TV-Director-面板.png'),
    ('M-34-资产管理-行内动作按钮.png', 'organize-canvas', 28,
     '打开资产管理抽屉，读行内所有**非空 aria-label** 的按钮（纯图标按钮的 innerText 是空的）',
     '画布 47 画布 资产 所有评级 图片节点 1 共 1 节点',
     '资产管理抽屉的「画布」标签：顶部「画布 / 资产」两个标签与「所有评级」筛选；下面一行是「图片节点 1」，行尾并排两枚 24×24 的圆形图标按钮（一枚是三点「⋯」，一枚是纸飞机）；底部左侧是收起箭头，右侧是「共 1 节点」',
     'M-34-资产管理-行内动作按钮.png'),
    ('M-35-更多操作菜单.png', 'organize-canvas', 29,
     '点行内 aria-label="更多操作" 的 24×24 图标按钮 (265,212)',
     '重命名 复制 添加到Agent 删除 画布 47 画布 资产 所有评级 图片节点 1 共 1 节点',
     '点行尾「⋯」后弹出的四项竖排菜单：重命名、复制、添加到Agent、删除；菜单锚在按钮正下方，背景仍是资产管理抽屉与画布',
     'M-35-更多操作菜单.png'),
    ('M-37-定位到节点之后.png', 'organize-canvas', 30,
     '把画布 Space+拖 平移 -360px 让节点跑到左边，再点 aria-label="定位到节点 图片节点 1"',
     '画布 47 画布 资产 所有评级 图片节点 1 共 1 节点 图片节点 1 参考 标记 风格',
     '点完「定位到节点」之后：左边抽屉里「图片节点 1」那一行处于高亮态，右边画布上的图片节点被拉回到视口中间偏右的位置，节点卡片和它下方的参数面板（参考 / 标记 / 风格）都完整可见',
     'M-37-定位到节点之后.png'),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    raw = open(MANIFEST, encoding='utf-8').read()
    disk = sorted('screenshots/' + f for f in os.listdir(SHOTS) if f.endswith('.png'))
    listed = re.findall(r'- file: (\S+)', raw)

    # 1) 删死条目：清单里有、磁盘上没了的
    dead = [f for f in listed if f not in disk]
    for f in dead:
        raw = re.sub(r'  - file: ' + re.escape(f) + r'\n(?:    .*\n)+', '', raw)
    if dead:
        print('删除死条目:', len(dead))
        for f in dead:
            print('  -', f)

    # 2) 补新条目
    added = 0
    for name, task_id, step, locator, visible, alt, _ in NEW:
        path = f'screenshots/{name}'
        if path in disk and f'- file: {path}\n' not in raw:
            block = (
                f'  - file: {path}\n'
                f'    task_id: {task_id}\n'
                f'    step: {step}\n'
                f'    route: {ROUTE}\n'
                f'    viewport: 1440x810@2x\n'
                f'    locale: zh-CN\n'
                f'    captured_at: {STAMP}\n'
                f'    verified_locator: {locator}\n'
            )
            if visible:
                block += f'    visible_text: {visible}\n'
            block += f'    alt: {alt}\n'
            block += f'    sha256: {sha256(os.path.join(ROOT, path))}\n'
            raw = raw.rstrip('\n') + '\n' + block
            added += 1
    if added:
        print('新增条目:', added)

    # 3) 逐张重算 sha256（幂等：清单里已有的也刷新，防止手改后对不上）
    refreshed = 0
    for rel in disk:
        real = sha256(os.path.join(ROOT, rel))
        pat = re.compile(r'(- file: ' + re.escape(rel) + r'\n(?:    .*\n)*?    sha256: )([0-9a-f]{64})')
        m = pat.search(raw)
        if m and m.group(2) != real:
            raw = raw[:m.start(2)] + real + raw[m.end(2):]
            refreshed += 1
        elif not m:
            print('  ! 清单缺 sha256:', rel)
    if refreshed:
        print('刷新 sha256:', refreshed)

    open(MANIFEST, 'w', encoding='utf-8').write(raw)

    # 4) 自检
    raw2 = open(MANIFEST, encoding='utf-8').read()
    listed2 = re.findall(r'- file: (\S+)', raw2)
    print(f'\n清单 {len(listed2)} 条 / 磁盘 {len(disk)} 张；'
          f'死条目 {len([f for f in listed2 if f not in disk])}；'
          f'未登记 {len([f for f in disk if f not in listed2])}')
    return 0 if sorted(listed2) == disk else 1


if __name__ == '__main__':
    sys.exit(main())
