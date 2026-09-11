import { redirect } from "next/navigation";

export default function JimengRootPage() {
  // 与 /frameos 一致：根路由重定向到 demo 画布
  redirect("/jimeng/canvas/demo");
}
