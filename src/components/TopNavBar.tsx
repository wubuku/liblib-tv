"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { CanvasTabDropdown } from "./CanvasTabDropdown";

export function TopNavBar() {
  const [projectName, setProjectName] = useState("未命名项目");
  const [isEditing, setIsEditing] = useState(false);

  return (
    <nav className="h-12 px-4 flex items-center justify-between bg-[#141414] border-b border-[#262626]">
      {/* Left Section */}
      <div className="flex items-center gap-3">
        {/* Logo */}
        <div className="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity">
          <div className="w-6 h-6 flex items-center justify-center">
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M4 5h16v14H4V5zm2 2v10h12V7H6zm2 2h2v6H8V9zm4 0h2v6h-2V9zm4 0h2v6h-2V9z"
                fill="#f7f7f7"
              />
            </svg>
          </div>
        </div>

        {/* Separator */}
        <div className="w-px h-5 bg-[#363636]" />

        {/* Project Name */}
        {isEditing ? (
          <input
            type="text"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            onBlur={() => setIsEditing(false)}
            onKeyDown={(e) => e.key === "Enter" && setIsEditing(false)}
            className="bg-[#363636] text-[#f7f7f7] text-sm px-2 py-1 rounded border border-[#525252] focus:border-[#09caf5] outline-none w-40"
            autoFocus
          />
        ) : (
          <span
            onClick={() => setIsEditing(true)}
            className="text-sm text-[#f7f7f7] cursor-text hover:bg-[#353639] px-2 py-1 rounded transition-colors"
          >
            {projectName}
          </span>
        )}

        {/* Canvas Tab Dropdown */}
        <CanvasTabDropdown />
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-2">
        {/* Notification */}
        <button className="p-2 hover:bg-[#353639] rounded-lg transition-colors">
          <svg
            className="w-5 h-5 text-[#919191]"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
        </button>

        {/* VIP + Credits combined button (matches original) */}
        <div className="relative flex items-center">
          {/* Orange "限时37折" badge above */}
          <span className="absolute -top-2 right-3 z-10 text-[10px] px-1.5 py-0.5 bg-[#ff7d00] text-white rounded-md font-medium">
            限时 37 折
          </span>
          <button className="flex items-center gap-1.5 pl-3 pr-1 h-10 rounded-xl bg-[rgba(38,38,38,0.8)] border border-[#363636] hover:bg-[#353639] transition-colors">
            <svg
              className="w-4 h-4 text-[#FFDBA4]"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M13 2L3 14h7l-1 8 10-12h-7l1-8z" />
            </svg>
            <span className="text-sm text-[#FFDBA4]">会员特惠37折</span>
            <span className="text-[#363636]">|</span>
            <svg
              className="w-4 h-4 text-[#FFDBA4]"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M13 2L3 14h7l-1 8 10-12h-7l1-8z" />
            </svg>
            <span className="text-sm text-[#f7f7f7]">64</span>
          </button>
        </div>

        {/* FrameOS 画布入口 */}
        <Link
          href="/frameos/canvas/demo"
          className="flex items-center gap-1.5 h-9 px-3 rounded-xl bg-[rgba(38,38,38,0.8)] border border-[#363636] hover:bg-[#353639] hover:border-[#525252] transition-colors text-sm text-[#f7f7f7]"
          title="进入 FrameOS 画布"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <rect x="3" y="4" width="18" height="14" rx="2" stroke="#60A5FA" strokeWidth="1.6" />
            <circle cx="9" cy="10" r="1.5" fill="#60A5FA" />
            <path d="M5 16l3-3 4 4 3-3 4 4" stroke="#60A5FA" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span>FrameOS</span>
        </Link>

        {/* User Avatar */}
        <button className="w-8 h-8 rounded-full overflow-hidden hover:ring-2 hover:ring-[#525252] transition-all">
          <Image
            src="/images/avatar.png"
            alt="用户头像"
            width={32}
            height={32}
            className="w-full h-full object-cover"
          />
        </button>
      </div>
    </nav>
  );
}
