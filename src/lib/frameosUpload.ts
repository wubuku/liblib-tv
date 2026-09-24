import { useFrameosStore } from "@/store/frameosStore";

/**
 * Batch 223: 本地上传对齐源站 (2026-09-25 探针采样, SOURCE_OBSERVATIONS):
 * 上传按 MIME 路由到 带内容 的节点 (图片→imageUrl, 音频→audioUrl, 视频→imageUrl 封面),
 * 标题 = 文件名去扩展名 (音频探针实测; 图片/视频为推断)。
 * 佐证: 源站 rail 隐藏 input accept="image/*,video/*,audio/*,.txt,.docx,.pdf"
 * 且 multiple; 文档类上传行为未采样, 暂不支持。
 */
export interface FrameosUploadPickerOpts {
  panX: number;
  panY: number;
  zoom: number;
  viewportWidth: number;
  viewportHeight: number;
}

export function openLocalUploadPicker(opts: FrameosUploadPickerOpts) {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = "image/*,video/*,audio/*";
  input.multiple = true;
  input.onchange = () => {
    const files = input.files;
    if (!files) return;
    const store = useFrameosStore.getState();
    for (const file of Array.from(files)) {
      const type = file.type.startsWith("image/")
        ? "image"
        : file.type.startsWith("video/")
        ? "video"
        : file.type.startsWith("audio/")
        ? "audio"
        : null;
      if (!type) continue;
      const url = URL.createObjectURL(file);
      const title = file.name.replace(/\.[^.]+$/, "");
      const id = store.addNode(type, opts);
      useFrameosStore.getState().updateNodeData(
        id,
        type === "audio" ? { audioUrl: url, title } : { imageUrl: url, title }
      );
    }
  };
  input.click();
}
