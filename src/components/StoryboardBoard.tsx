"use client";

import Image from "next/image";
import { FileText, ImageIcon, Play, Sparkles } from "lucide-react";

const columns = [
  {
    title: "剧本",
    icon: FileText,
    items: [{ kind: "text", title: "第一集：咖啡馆对峙", body: "陈默与林小婉在咖啡馆重逢，压抑的对话逐步揭开过往。" }],
  },
  {
    title: "角色与物件",
    icon: Sparkles,
    items: [
      { kind: "image", title: "陈默", src: "/images/scene-coffee-1.png" },
      { kind: "image", title: "林小婉", src: "/images/scene-coffee-3.png" },
      { kind: "image", title: "咖啡", src: "/images/scene-coffee-2.png" },
    ],
  },
  {
    title: "分镜图",
    icon: ImageIcon,
    items: [{ kind: "image", title: "分镜 #2", src: "/images/storyboard-2.png" }],
  },
  {
    title: "视频",
    icon: Play,
    items: [{ kind: "failed", title: "分镜视频-#9", body: "生成失败" }],
  },
] as const;

export function StoryboardBoard() {
  return (
    <div className="h-full min-w-0 overflow-x-auto bg-[#141414] px-5 pb-24 pt-16">
      <div className="flex min-h-full min-w-[820px] gap-3">
        {columns.map((column) => {
          const Icon = column.icon;
          return (
            <section key={column.title} className="w-52 shrink-0 border-l border-white/[0.08] pl-3 first:border-l-0 first:pl-0">
              <header className="mb-3 flex h-7 items-center gap-2 text-xs text-[#8d8d8d]">
                <Icon size={14} />
                <span>{column.title}</span>
                <span className="ml-auto text-[#5f5f5f]">{column.items.length}</span>
              </header>
              <div className="space-y-3">
                {column.items.map((item) => (
                  <article key={item.title} className="overflow-hidden rounded-lg border border-white/[0.08] bg-[#222]">
                    {item.kind === "image" && "src" in item && (
                      <Image src={item.src} alt={item.title} width={400} height={225} className="aspect-video w-full object-cover" unoptimized />
                    )}
                    {item.kind === "failed" && (
                      <div className="flex aspect-video items-center justify-center text-xs text-[#dd5c65]">生成失败</div>
                    )}
                    <div className="p-2.5">
                      <h3 className="text-xs text-[#e4e4e4]">{item.title}</h3>
                      {"body" in item && item.kind === "text" && <p className="mt-2 text-[11px] leading-5 text-[#888]">{item.body}</p>}
                    </div>
                  </article>
                ))}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
