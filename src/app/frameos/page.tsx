import { redirect } from "next/navigation";

export default function FrameosRootPage() {
  // 重定向到 demo canvas 页面 (类似原 URL 的 hash 路径)
  redirect("/frameos/canvas/demo");
}
