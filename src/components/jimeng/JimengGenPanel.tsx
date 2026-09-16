"use client";

import { useState } from "react";
import { ArrowUp, AtSign, ChevronDown, Maximize2, Plus } from "lucide-react";
import { NodeToolbar, Position } from "@xyflow/react";

import { useJimengStore } from "@/store/jimengStore";
import { VipDiamond } from "@/components/jimeng/icons";

/**
 * 模型列表 (Batch 41, SOURCE_FACT: 源站模型下拉提取的 8 项，名称+描述)。
 */
const MODELS = [
  { name: "即梦 Seedance 2.5", desc: "最强模型，支持 50个参考，新增视频编辑、超长生成" },
  { name: "即梦 Seedance 2.0 mini", desc: "极致性价比，相近的体验，比Fast更快的推理速度" },
  { name: "即梦 Seedance 2.0 Fast VIP", desc: "极速推理，会员专属通道，音视文图均可参考（暂不支持真人人脸）" },
  { name: "即梦 Seedance 2.0 VIP", desc: "全模态能力，会员专属通道，音视文图均可参考（暂不支持真人人脸）" },
  { name: "即梦 Seedance 1.0 Fast", desc: "Pro级表现，加量不加价" },
  { name: "MiniMax H3", desc: "开源视频生成模型" },
  { name: "HappyHorse 1.1", desc: "国产视频生成模型" },
  { name: "Wan 3.0", desc: "Wan系列最新视频模型" },
];

/**
 * 空视频节点选中后下方弹出的视频生成面板 (Batch 3；Batch 206 细节对齐)。
 *
 * 证据 (SOURCE_FACT, README §7 + 206-genpanel-detail.json):
 * - 载体 xyflow <NodeToolbar> position=bottom；面板 680×208，节点下方 20px，居中
 * - 本体 form: rgb(32,32,32) r20 内边距 16 (batch 206 复测，原 17)
 * - 三行: 素材栏 h-12 (+ 按钮) / 提示词占位区 (占位 14px，@主体为行内
 *   白/[0.08] chip，批 206；placeholder 属性保留供 a11y/验证器，视觉置透明)
 * - 底部行 h-8: 即梦 Seedance 2.0 VIP ✦∨ · 16:9·720P ✦·1∨ · 全能参考∨ · 4s∨
 *   · @ (控件 12px，批 206 复测)
 * - 底部行右组: 「Current price」标签 + ✦56.56 (白/[0.69]，70px 裁切容器，
 *   源站自身即截断显示——批 206) + 32px 圆形发送钮 bg 白/16 禁用态
 *   (sr-only "请输入提示词")
 * - 右上角 40×40 展开钮 (icon 24, white/60)
 * mock: 提示词可输入、下拉不开合 (Batch 5 接 store)。
 */
export function JimengGenPanel({
  visible,
  nodeId,
}: {
  visible: boolean;
  nodeId: string;
}) {
  // Batch 40/50: 提示词可输入；发送 → generateInto (mock 全流程)
  const [prompt, setPrompt] = useState("");
  const generateInto = useJimengStore((s) => s.generateInto);
  // Batch 41/61: 模型下拉，选择持久化到 store
  const [modelOpen, setModelOpen] = useState(false);
  const model = useJimengStore((s) => s.genModel);
  const setGenModel = useJimengStore((s) => s.setGenModel);
  // Batch 42: 比例/分辨率/数量 + 参考模式 + 时长 (SOURCE_FACT batch 42 提取)
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const [ratio, setRatio] = useState("16:9");
  const [resolution, setResolution] = useState("720P");
  const [count, setCount] = useState("1");
  const [reference, setReference] = useState("全能参考");
  const [duration, setDuration] = useState("4s");
  const pushToast = useJimengStore((s) => s.pushToast);
  const canSend = prompt.trim().length > 0;

  return (
    <NodeToolbar isVisible={visible} position={Position.Bottom} offset={20}>
      <div className="relative h-[208px] w-[680px]">
        {/* 右上角展开钮 (骑在面板顶边) */}
        <button
          type="button"
          aria-label="展开面板"
          className="absolute -top-1.5 right-0 z-[2] flex size-10 items-center justify-center"
        >
          <span className="flex size-6 items-center justify-center rounded-full text-white/60">
            <Maximize2 size={13} />
          </span>
        </button>

        <form
          className="flex h-full w-full flex-col justify-between rounded-[20px] bg-[#202020] p-4"
          onSubmit={(e) => {
            e.preventDefault();
            if (!canSend) return;
            generateInto(nodeId, prompt);
            pushToast("生成任务已提交（mock）");
            setPrompt("");
          }}
        >
          {/* 素材栏 */}
          <div className="flex h-12 w-full items-center">
            <button
              type="button"
              aria-label="上传参考图"
              className="flex size-11 items-center justify-center rounded-xl border border-white/10 bg-white/[0.06] text-white/80 hover:bg-white/10"
            >
              <Plus size={20} />
            </button>
          </div>

          {/* 提示词输入区 (Batch 40: 可编辑)。批 206: 占位 14px + @主体
              行内 chip——视觉由叠加层渲染，textarea placeholder 属性保留
              (a11y/验证器)，占位色置透明避免双重显示 */}
          <div className="relative flex w-full items-start">
            {!canSend ? (
              <div className="pointer-events-none absolute inset-0 flex items-start text-[14px] leading-[24px] text-white/35">
                <span className="whitespace-nowrap">上传参考图、输入文字或</span>
                <span className="mx-1 inline-flex shrink-0 items-center gap-0.5 self-start rounded bg-white/[0.08] px-1 text-white/55">
                  <AtSign size={10} />
                  主体
                </span>
                <span className="whitespace-nowrap">，描述你想生成的视频</span>
              </div>
            ) : null}
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="上传参考图、输入文字或 @ 主体，描述你想生成的视频"
              rows={2}
              className="w-full resize-none bg-transparent text-[13px] leading-[22px] text-white outline-none placeholder:text-transparent"
            />
          </div>

          {/* 底部控制行 */}
          <div className="flex h-8 w-full items-center justify-between gap-1">
            <div className="flex min-w-0 items-center gap-1">
              <div className="relative">
                <button
                  type="button"
                  aria-label="选择模型"
                  onClick={() => setModelOpen((v) => !v)}
                  className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08]"
                >
                  {model}
                  <VipDiamond size={12} />
                  <ChevronDown size={12} className="text-white/60" />
                </button>
                {modelOpen ? (
                  <div
                    className="absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[392px] rounded-[10px] border border-white/[0.06] p-1.5"
                    style={{ background: "rgb(38,38,38)" }}
                    role="listbox"
                    aria-label="模型列表"
                  >
                    {MODELS.map((m) => (
                      <button
                        key={m.name}
                        type="button"
                        role="option"
                        aria-selected={model === m.name}
                        onClick={() => {
                          setGenModel(m.name);
                          setModelOpen(false);
                        }}
                        className={`flex w-full flex-col items-start gap-0.5 rounded-lg px-2.5 py-2 text-left hover:bg-white/10 ${
                          model === m.name ? "bg-white/[0.08]" : ""
                        }`}
                      >
                        <span className="text-[13px] font-medium text-white">
                          {m.name}
                        </span>
                        <span className="text-[12px] leading-4 text-white/45">
                          {m.desc}
                        </span>
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
              {/* 比例/分辨率/数量 组合菜单 (SOURCE_FACT batch 42: 三组选项) */}
              <div className="relative">
                <button
                  type="button"
                  aria-label="比例分辨率数量"
                  onClick={() => setOpenMenu(openMenu === "ratio" ? null : "ratio")}
                  className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08]"
                >
                  {ratio} · {resolution}
                  <VipDiamond size={12} />
                  · {count}
                  <ChevronDown size={12} className="text-white/60" />
                </button>
                {openMenu === "ratio" ? (
                  <div
                    className="absolute bottom-[calc(100%+8px)] left-0 z-[140] flex w-[334px] gap-4 rounded-[10px] border border-white/[0.06] p-3"
                    style={{ background: "rgb(38,38,38)" }}
                    role="listbox"
                    aria-label="比例分辨率数量"
                  >
                    {[
                      { title: "选择比例", key: "ratio", options: ["21:9", "16:9", "4:3", "1:1", "3:4", "9:16"] },
                      { title: "选择分辨率", key: "resolution", options: ["720P", "1080P", "4K"] },
                      { title: "选择生成数量", key: "count", options: ["1", "2", "3", "4"] },
                    ].map((group) => (
                      <div key={group.key} className="flex flex-col gap-0.5">
                        <p className="text-[12px] text-white/40">{group.title}</p>
                        {group.options.map((opt) => (
                          <button
                            key={opt}
                            type="button"
                            role="option"
                            aria-selected={
                              (group.key === "ratio" ? ratio : group.key === "resolution" ? resolution : count) === opt
                            }
                            onClick={() => {
                              if (group.key === "ratio") setRatio(opt);
                              if (group.key === "resolution") setResolution(opt);
                              if (group.key === "count") setCount(opt);
                              setOpenMenu(null);
                            }}
                            className={`flex h-7 items-center rounded-md px-2 text-[12px] ${
                              (group.key === "ratio" ? ratio : group.key === "resolution" ? resolution : count) === opt
                                ? "bg-white/[0.12] text-white"
                                : "text-white/75 hover:bg-white/10"
                            }`}
                          >
                            {opt}
                          </button>
                        ))}
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
              {/* 全能参考切换 (SOURCE_FACT batch 42: 首尾帧/全能参考 两项) */}
              <div className="relative">
                <button
                  type="button"
                  aria-label="参考模式"
                  onClick={() => setOpenMenu(openMenu === "ref" ? null : "ref")}
                  className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08]"
                >
                  {reference}
                  <ChevronDown size={12} className="text-white/60" />
                </button>
                {openMenu === "ref" ? (
                  <div
                    className="absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[192px] rounded-[10px] border border-white/[0.06] p-1.5"
                    style={{ background: "rgb(38,38,38)" }}
                    role="listbox"
                    aria-label="参考模式"
                  >
                    {["首尾帧", "全能参考"].map((opt) => (
                      <button
                        key={opt}
                        type="button"
                        role="option"
                        aria-selected={reference === opt}
                        onClick={() => {
                          setReference(opt);
                          setOpenMenu(null);
                        }}
                        className={`flex h-10 w-full items-center rounded-lg px-2.5 text-[13px] ${
                          reference === opt ? "bg-white/[0.10] text-white" : "text-white/75 hover:bg-white/10"
                        }`}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
              {/* 时长 (Batch 42: 4s/8s/12s, CLONE_DECISION 8s/12s 推断) */}
              <div className="relative">
                <button
                  type="button"
                  aria-label="时长"
                  onClick={() => setOpenMenu(openMenu === "dur" ? null : "dur")}
                  className="flex h-8 items-center gap-1 whitespace-nowrap rounded-lg px-2 text-[12px] text-white/90 hover:bg-white/[0.08]"
                >
                  {duration}
                  <ChevronDown size={12} className="text-white/60" />
                </button>
                {openMenu === "dur" ? (
                  <div
                    className="absolute bottom-[calc(100%+8px)] left-0 z-[140] w-[120px] rounded-[10px] border border-white/[0.06] p-1.5"
                    style={{ background: "rgb(38,38,38)" }}
                    role="listbox"
                    aria-label="时长"
                  >
                    {["4s", "8s", "12s"].map((opt) => (
                      <button
                        key={opt}
                        type="button"
                        role="option"
                        aria-selected={duration === opt}
                        onClick={() => {
                          setDuration(opt);
                          setOpenMenu(null);
                        }}
                        className={`flex h-10 w-full items-center rounded-lg px-2.5 text-[13px] ${
                          duration === opt ? "bg-white/[0.10] text-white" : "text-white/75 hover:bg-white/10"
                        }`}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
              <button
                type="button"
                aria-label="提及主体"
                className="flex size-8 items-center justify-center rounded-lg text-white/80 hover:bg-white/[0.08]"
              >
                <AtSign size={15} />
              </button>
            </div>

            <div className="flex h-8 shrink-0 items-center gap-2">
              {/* 批 206 SOURCE_FACT: 「Current price」标签 + ✦56.56，
                  70px 裁切容器——源站自身即截断显示 */}
              <span className="flex h-8 w-[70px] items-center overflow-hidden whitespace-nowrap text-[12px] text-white/[0.69]">
                <span className="shrink-0 text-white/[0.6]">Current price</span>
                <VipDiamond size={9} />
                <span className="shrink-0">56.56</span>
              </span>
              <button
                type="submit"
                aria-label="生成"
                disabled={!canSend}
                className={`flex size-8 items-center justify-center rounded-full ${
                  canSend
                    ? "bg-white text-black hover:bg-white/90"
                    : "bg-white/[0.16] text-white/20"
                }`}
              >
                <ArrowUp size={15} />
              </button>
            </div>
          </div>
        </form>
      </div>
    </NodeToolbar>
  );
}
