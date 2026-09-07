# Batch 201 — 换一批真实 Skill 目录对齐（四批全采）

## 源站事实（窗口 rAF ~31fps；`source-skill-batches.json` 存档）

连续四次换一批，轮换共 **4 批真实目录**（id 取自路径 slug）：

- 批 0：皮克斯动画广告 / 爆款拉片复刻 / 新中式美学TVC / 古典武侠电影全流程导演（与 Batch 97 记录一致）
- 批 1：游戏实机PV（gameplay-pv-builder）/ 精品女频短剧一键成片（xingrannvpin）/ 是枝裕和电影美学（koreeda-film-aesthetic）/ 韦斯安德森电影美学（wes-anderson-aesthetics）
- 批 2：剧情TVC广告片（narrative-tvc-creator）/ 伊斯特伍德西部片（eastwood-western-style）/ 一键爽感轰炸流汽车TVC（high-impact-car-tvc）/ 旅拍大师（cinematic-travel-vlog-maker）
- 批 3：一键海外狼人吸血鬼短剧（werewolf-vampire-short-drama）/ 宝岛浪潮电影美学（taiwan-new-wave-aesthetic）/ 无厘头喜剧（absurdist-comedy-maker）——**3 张**

## 实施

- `AgentDrawer.skillBatches`：原 clone-shaped 第二批占位移除，替换为
  直采的批 1/2/3（id=路径 slug，缩略图仍为本地占位——源图为远端图）；
  轮换共 4 批，第 4 批 3 张。

## 验收

- `verify-liblib-batch201.py`：7 checks（四批逐一出现 + 换一批 4 次后
  环绕回批 0 + 0 page error）。
- 回归绿：107 / 199 / 200 / 172。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：批 3 仅 3 张是目录尾部还是轮换截断；各 Skill 点击进入会话后
  的实际生成行为；缩略图（clone 仍为本地占位）。
- 源站测试残留清理：0 残留（本批仅抽屉内轮换，未建节点）。
