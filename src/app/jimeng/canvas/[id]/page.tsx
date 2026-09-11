"use client";

import { useParams } from "next/navigation";

import { JimengWorkspace } from "@/components/jimeng/JimengWorkspace";

/**
 * /jimeng/canvas/[id] — 画布路由。
 * 复刻范围仅 demo mock 数据；路由参数暂不区分多画布 (与 /frameos/canvas/[id] 同构)。
 */
export default function JimengCanvasPage() {
  useParams<{ id: string }>();

  return <JimengWorkspace />;
}
