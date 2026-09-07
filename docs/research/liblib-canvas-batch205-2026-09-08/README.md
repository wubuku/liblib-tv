# Batch 205 — 类型筛选菜单与列表联动

## 实施

- `AssetManagerPanel`：类型菜单选择写入既有 `filter` 状态
  （标签→NodeFilter 映射：全部→all、文本→text、图片→image、视频→video、
  智能剪辑→video-clip、导演台→script-execution、逐帧拉片→shot-breakdown、
  音频→audio、脚本→script-generator、脚本（旧版）→script），
  `matchesFilter` 扩展对应分支——列表按节点类型实时过滤。
- 触发器文案：全部时显示控件名「展示设置」（与 batch102 合同一致），
  其余显示所选类型。
- 清理：ratings/展示设置两处实装后 `setHint` 不再有调用方，
  hint 状态与渲染块移除（lint 回到 8 warnings 基线）。

## 验收

- `verify-liblib-batch205.py`：8 checks（图片筛选显示图片行隐藏视频行/
  视频筛选显示分镜视频-#9 隐藏图片行/全部恢复/触发器文案/0 page error）。
- 回归绿：102（14 checks）/ 114 / 202 / 22 / 172。
- `npm run check`：0 errors（8 warnings 基线）；docs check 通过。
- 不证明：源站类型筛选的精确过滤语义（clone 按节点类型映射实现，
  源站未逐项采样）；组节点在筛选下的父子展开细节。

## 源站测试残留清理

- 0 残留（本批无源站节点操作）。
