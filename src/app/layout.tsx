import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LibTV - 专业视频创作工具",
  description: "AI驱动的专业视频创作平台，支持分镜、脚本、素材管理",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="h-full antialiased">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="min-h-full flex flex-col bg-[#141414] text-[#f7f7f7]">
        {children}
      </body>
    </html>
  );
}
