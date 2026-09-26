# TDCanvas 测试媒体素材登记

## 使用边界

- 这些文件仅用于 TDCanvas 画布上传、节点预览、参考图挂载、连接和编辑交互验证。
- **不得触发真实图片生成、视频生成、音频生成或其他按量计费的 Provider 调用**（Aitudou API 按量计费）；运行时探索全程不配置 API Key、不启动 ComfyUI 环境。
- 正式用户手册正文只描述产品行为，不复制这些素材；本文件是内部取证清单。
- 文件路径由用户提供；字节数来自 2026-09-26 的只读核对（与 frameos-canvas 手册共用同一批素材）。

## 图片

| 文件 | 字节数 |
|---|---:|
| `/Users/yangjiefeng/Downloads/生成蓝色手机图片-2.png` | 3918889 |
| `/Users/yangjiefeng/Downloads/55dd39e3-5024-47ec-9971-4d35be848a65.png` | 2189840 |
| `/Users/yangjiefeng/Downloads/febfe81e-88af-4cd9-8d72-580d54e8ef20.png` | 1992935 |
| `/Users/yangjiefeng/Downloads/黑白电影质感咖啡厅俯视场景生成-2.png` | 4109827 |
| `/Users/yangjiefeng/Downloads/黑白电影质感咖啡厅俯视场景生成.png` | 4205810 |
| `/Users/yangjiefeng/Downloads/53b684be-5370-487c-b366-418424c22d25.png` | 3455879 |
| `/Users/yangjiefeng/Downloads/项目资产_咖啡馆对峙/角色图片/陈默_01KT17FN.png` | 1785169 |
| `/Users/yangjiefeng/Downloads/项目资产_咖啡馆对峙/角色图片/林小婉_01KT17FN.png` | 2398875 |
| `/Users/yangjiefeng/Downloads/生成普通路人感年轻女性照片.png` | 3689429 |
| `/Users/yangjiefeng/Downloads/生成王嘉尔风格人物照片.png` | 4459317 |

## 音频

| 文件 | 字节数 |
|---|---:|
| `/Users/yangjiefeng/Downloads/voice_converted_1779790519790.wav` | 1155884 |
| `/Users/yangjiefeng/Downloads/separated_vocals_1778861280890.wav` | 2306092 |

## 视频

| 文件 | 字节数 |
|---|---:|
| `/Users/yangjiefeng/Downloads/S83·镜2.mp4` | 809635 |
| `/Users/yangjiefeng/Downloads/S109·镜2.mp4` | 1155068 |

## 注入方法备忘（IAB 环境限制的绕行）

ZCode IAB 不支持文件选择器，且 `page.evaluate` 字符串参数不传递。运行时注入真实字节的可行管线：

1. 将素材以 ASCII 文件名复制到 TDCanvas `web/public/__rt__/`（Vite 静态目录，用后删除）；
2. 页内 `locator("body").evaluate` 执行 `fetch("/__rt__/<name>")` → `File` → `DataTransfer` → `input.files` → `dispatchEvent(change)`；
3. 该路径走应用真实上传管线（`uploadImage/uploadMediaFile` → storageKey → 尺寸适配），2026-09-26 已用 `陈默_01KT17FN.png`（1785169 字节）验证成功。
