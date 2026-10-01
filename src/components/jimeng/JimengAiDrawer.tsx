"use client";

import { useRef, useState } from "react";
import { useJimengStore } from "@/store/jimengStore";
import { useLayerFocus } from "@/hooks/useLayerFocus";
import { FEEDBACK, sourcePickFeedback } from "@/components/jimeng/jimengFeedback";
import {
  ArrowUp,
  AtSign,
  PanelRightClose,
  Plus,
  SquarePen,
  WandSparkles,
} from "lucide-react";

/**
 * 「与 AI 对话」右侧抽屉 (Batch 12)。
 *
 * 证据 (SOURCE_FACT): 点击右下角按钮展开全高右侧抽屉 (宽 ≈410px, 圆角,
 * assistant-sidecar 深色表面): 头部「新会话」+ 历史/展开图标；居中空态
 * 「探索更多专业创作模式」+ 技能 chips (/ 视频反解 / 创作分镜 / 全流程广告片导演 /
 * 剧本开发 / 剧情短片)；底部输入卡片: 占位「输入想法、剧本或上传参考，支持" / "
 * 使用技能，@ 添加主体，和 Agent 一起创作」+ @ chip + 底行 +/使用技能/@/禁用发送钮。
 * mock: 输入不可用，chips 点击无操作。
 */
const SKILL_CHIPS = [
  "/ 视频反解",
  "/ 创作分镜",
  "/ 全流程广告片导演",
  "/ 剧本开发",
  "/ 剧情短片",
];

/** Batch 809 SOURCE_FACT（登录态，点「使用技能」实测弹出「搜索技能」面板，
 *  每项形如「名称 + 官方 + 一句话长描述」）。描述文案除「视频反解」外为
 *  CLONE_DECISION —— 源站只实测到这一条的完整文案，其余按技能名拟写，
 *  标在这里以免日后被当成实测值引用。 */
const SKILLS = [
  {
    name: "视频反解",
    chip: "/ 视频反解",
    desc: "拆解参考视频的镜头语言、光影色调与声音节奏，一键生成可用于拉片复刻、元素替换和再创作的视频 Prompt，覆盖广告、MV、剧情片、AI 视频、短视频、产品展示等多类",
  },
  { name: "创作分镜", chip: "/ 创作分镜", desc: "把一段创意拆成可执行的分镜脚本，自动补齐景别、机位与时长（CLONE_DECISION）" },
  { name: "全流程广告片导演", chip: "/ 全流程广告片导演", desc: "从卖点梳理到成片脚本的全链路广告片工作流（CLONE_DECISION）" },
  { name: "剧本开发", chip: "/ 剧本开发", desc: "从一句话创意扩写出完整剧本，含人物小传与分场（CLONE_DECISION）" },
  { name: "剧情短片", chip: "/ 剧情短片", desc: "按短剧节奏组织冲突与反转，输出可直接拍摄的分镜（CLONE_DECISION）" },
];

/** Batch 809 SOURCE_FACT：点「引用参考」弹出「添加参考」，分类 tab 五项 */
const REF_KINDS = ["主体", "图片", "视频", "音频", "文本"];

/** Batch 809 SOURCE_FACT：点「+」弹出三项来源菜单 */
const ADD_SOURCES = ["上传", "从资产库添加", "从画布添加"];

type Panel = null | "skills" | "mention" | "add" | "sessions";

/** Batch 834：空会话的稳定引用。模块级常量 ⇒ 每次渲染不新建数组，
    免得 `messages.map` 在空态下反复换引用。 */
const EMPTY_MESSAGES: { role: "user" | "agent"; text: string }[] = [];

export function JimengAiDrawer({ onClose }: { onClose: () => void }) {
  const panelRef = useRef<HTMLElement>(null);
  // Batch 811 SOURCE_FACT: 源站点「与 AI 对话」后焦点进入
  // `aside[canvas-feature-sidecar]`；但源站 **Tab 会逃出**抽屉，关闭后
  // 焦点也停在抽屉内不回触发器。所以这里只搬"焦点进浮层"这一项，
  // 不加陷阱、不归还 —— 加了就是偏离源站。
  useLayerFocus(panelRef, true);
  // 批 216: 预填提示词 (提示词反推 → 视频反解)；由工作区以 prefill 为
  // key 重挂载本组件带入初始值。批 219: 草稿跨关闭保留——优先取已存草稿
  const prefill = useJimengStore((s) => s.aiDrawerPrefill);
  const refChip = useJimengStore((s) => s.aiDrawerRefChip);
  const draft = useJimengStore((s) => s.aiDrawerDraft);
  const setAiDrawerDraft = useJimengStore((s) => s.setAiDrawerDraft);
  const [input, setInput] = useState(draft || prefill || "");
  // 批 396 SOURCE_FACT: 预填以富文本形态渲染 (技能芯片 84×20 + 文件芯片
  // 113×24 内联于文本流，node-composerChip)——点击进入编辑态换回 input
  const [editing, setEditing] = useState(false);
  const richPrefill = !!refChip && prefill && !editing && !input;

  // ── Batch 809：composer 会话状态 ──
  // 之前这四个按钮完全没有 onClick（batch 808 普查出来）。源站实测它们
  // 分别把技能/参考插进 composer、把来源菜单打开 —— 不是打开浮层就完事。
  const [panel, setPanel] = useState<Panel>(null);
  const [skillQuery, setSkillQuery] = useState("");
  const [refKind, setRefKind] = useState(REF_KINDS[0]);
  const [tokens, setTokens] = useState<string[]>([]);
  /* Batch 834：`messages` 从组件本地 useState 搬进 store。
     此前它是本组件的 `useState`，于是：抽屉一卸载会话就没了；「新建会话」
     是 `setMessages([])`，**直接销毁**当前会话且不可恢复 —— 那不叫新建。
     现在消息挂在 store 的 `aiSessions` 上，新建 = 追加一条并切过去，
     旧会话仍在「会话列表」里可切回。 */
  const sessions = useJimengStore((s) => s.aiSessions);
  const activeId = useJimengStore((s) => s.aiActiveSessionId);
  const appendAiMessage = useJimengStore((s) => s.appendAiMessage);
  const newAiSession = useJimengStore((s) => s.newAiSession);
  const selectAiSession = useJimengStore((s) => s.selectAiSession);
  const messages =
    sessions.find((s) => s.id === activeId)?.messages ?? EMPTY_MESSAGES;
  const pushToast = useJimengStore((s) => s.pushToast);
  // 源站：输入区非空时发送钮才可用；技能/参考 token 也算内容
  const composerText = [input.trim(), ...tokens].filter(Boolean).join(" ");
  const canSend = richPrefill || composerText.length > 0;
  // 源站「会话列表/新建会话」在**还没有会话**时是 aria-disabled —— 有会话
  // 之后才可用。会话存在的判据就是发过消息。
  const hasSession = sessions.length > 0;
  /* Batch 834 订正：中间区空态的判据**不是** `hasSession`。
     `hasSession` 是「有没有会话」，供两枚会话头按钮的 aria-disabled 用
     （那两条是源站契约，无会话时确实禁用）。但中间区该不该显示空态，
     取决于**当前这条会话里有没有消息** —— 否则 batch 834 把「新建」
     从销毁改成追加之后，「新建会话」点下去是一条空白死路：消息流容器
     渲染着却空空如也，技能 chips 也不出来，用户既看不到任何提示，也
     没有任何可点的起手式。这和 batch 832 记的「会骗人的提示比没有
     交互更糟」是同一类问题。

     ⚠ 这里**没有** SOURCE_FACT：源站的 chips 空态是按「有没有消息」
     还是按「有没有会话」判定的，未取证。复刻自有语义：按当前会话判。 */
  const streamIsEmpty = messages.length === 0;

  const addSkill = (chip: string) => {
    setTokens((t) => (t.includes(chip) ? t : [...t, chip]));
    setPanel(null);
    setSkillQuery("");
  };
  const closePanel = () => {
    setPanel(null);
    setSkillQuery("");
  };
  const send = () => {
    if (!canSend) return;
    const text = richPrefill ? prefill || "" : composerText;
    // Batch 834：两条消息分两次 append，与 store 的角色粒度对齐
    appendAiMessage("user", text);
    appendAiMessage("agent", `已收到「${text.slice(0, 24)}」。这是 mock 回复，接真实 Agent 时替换。`);
    setInput("");
    setTokens([]);
    setAiDrawerDraft("");
  };

  // SOURCE_FACT (batch 795 实测 @1680×826): 面板 400×802 @[1268,12]，z-40，
  // radius 20px，右缘/上缘/下缘各内缩 12px。
  return (
    <aside
      ref={panelRef}
      // Batch 797 SOURCE_FACT (2026-10-01 登录态实测，点「与 AI 对话」后量得):
      //   @[1268,12] 400×802  radius 20px  z-40
      //   background  color(srgb .12549 ×3 / .8) = **rgba(32,32,32,0.8)**
      //             （此前误用不透明 #1E1E1E）
      //   backdrop-filter **blur(60px)**
      //   border      1px solid rgba(255,255,255,**0.1**)（此前 0.06）
      //   box-shadow  rgba(0,0,0,0.16) 0 0 80px 0（此前无）
      className="absolute inset-y-3 right-3 z-40 flex w-[400px] flex-col rounded-[20px] border border-white/10 bg-[rgba(32,32,32,0.8)] shadow-[0_0_80px_0_rgba(0,0,0,0.16)] backdrop-blur-[60px]"
      role="dialog"
      aria-label="Agent"
      /* Batch 824：批 823 的浮层普查把它列成缺陷 —— 有可访问名、**没有
         data-testid**。它是常驻侧栏（开了就不太关得掉），自动化只能靠
         `role=dialog` + `aria-label="Agent"` 指认；补上锚点后普查能逐态核对
         它有没有被 transform 祖先收编。 */
      data-testid="canvas-agent-drawer"
    >
      {/* 头部 — Batch 808 SOURCE_FACT（@1680×826 登录态，aria/testid 逐个提取）：
          会话列表 58×32 @[1314,41] `canvas-agent-session-menu-menu-trigger`
            ↑ 此前复刻这里只是一段纯文本「新会话」，源站是**按钮**；无会话时
              aria-disabled=true —— 正确禁用，不是没接交互
          新建会话 32×32 @[1599,41] `canvas-agent-session-create`（同样 disabled）
          收起     36×36 @[1637,41] `canvas-agent-session-collapse`（此前复刻 28×28） */}
      <div className="flex items-center justify-between px-4 py-3">
        <button
          type="button"
          aria-label="会话列表"
          data-testid="canvas-agent-session-menu-trigger"
          disabled={!hasSession}
          onClick={() => setPanel((p) => (p === "sessions" ? null : "sessions"))}
          className="flex h-8 w-[58px] items-center gap-1 rounded-lg px-2 text-[14px] text-white/90 disabled:cursor-default disabled:text-white/45"
        >
          新会话
        </button>
        <div className="flex items-center gap-1">
          <button
            type="button"
            aria-label="新建会话"
            data-testid="canvas-agent-session-create"
            disabled={!hasSession}
            onClick={() => {
              // Batch 834：此前是 `setMessages([])` —— **销毁**当前会话。
              // 「新建」的语义是开一条新的，旧的仍在列表里可切回。
              newAiSession();
              setTokens([]);
              setInput("");
              setAiDrawerDraft("");
              pushToast(FEEDBACK.newSession());
            }}
            className="flex size-8 items-center justify-center rounded-md text-white/60 disabled:cursor-default"
          >
            <SquarePen size={16} />
          </button>
          <button
            type="button"
            aria-label="收起"
            data-testid="canvas-agent-session-collapse"
            onClick={onClose}
            className="flex size-9 items-center justify-center rounded-md text-white/60 hover:bg-white/10 hover:text-white"
          >
            <PanelRightClose size={16} />
          </button>
        </div>
      </div>

      {/* Batch 809: 当前会话有消息时中间区换成消息流，空态（技能 chips）退场 */}
      {!streamIsEmpty ? (
        <div
          className="flex-1 space-y-3 overflow-y-auto px-4 py-4"
          data-testid="agent-messages"
          aria-label="会话消息"
        >
          {messages.map((m, i) => (
            <div
              key={`${m.role}-${i}`}
              data-testid={m.role === "user" ? "agent-msg-user" : "agent-msg-agent"}
              className={`max-w-[88%] rounded-xl px-3 py-2 text-[13px] leading-[20px] ${
                m.role === "user"
                  ? "ml-auto bg-white/12 text-white"
                  : "bg-white/[0.06] text-white/85"
              }`}
            >
              {m.text}
            </div>
          ))}
        </div>
      ) : (
      /* 居中空态 */
      <div className="flex flex-1 flex-col items-center justify-center gap-4 px-6">
        <div className="flex flex-wrap items-center justify-center gap-x-2 gap-y-2">
          {SKILL_CHIPS.map((chip) => (
            /* SOURCE_FACT (batch 808 实测尺寸 + batch 810 订正行为)：
               chip 105×36，最长的「/ 全流程广告片导演」157 宽 —— 宽度随文案
               自适应，不是固定值。

               ⚠ batch 808 曾在这里写「源站点这几个 chip 同样没有可观测变化，
               所以保持 inert」——**那是错的**，已由 batch 810 推翻：源站的
               composer 是 contenteditable DIV，而当时的指纹只扫
               textarea/input，够不着它。补上 [contenteditable] 后实测：
               点 chip 会把技能名插入 composer 并解锁发送钮（见 addSkill）。 */
            <button
              key={chip}
              type="button"
              data-testid="canvas-agent-mode-action"
              onClick={() => addSkill(chip)}
              className="flex h-9 items-center rounded-full bg-white/[0.06] px-5 text-[13px] text-white/80 hover:bg-white/[0.12]"
            >
              {chip}
            </button>
          ))}
        </div>
      </div>
      )}

      {/* Batch 834：会话列表 —— 此前是 toast 桩（`FEEDBACK.sessionList`）。
          ⚠️ 源站这枚弹层的**内容与几何未取证**（批 808/810 取到的是触发钮本身
          58×32 @[1314,41]，弹层没打开量过），所以下面是**复刻自有的列表语义**，
          不写成 SOURCE_FACT：
            一行 = 一条会话；标题取首条用户消息前 24 字
            副标 = 「N 条消息」；当前会话带一条左侧高亮竖条
          判据落在**关系**上（切回旧会话后消息流要真的换回去），
          不写死条数/文案 —— 默认会话数由操作决定。 */}
      {panel === "sessions" ? (
        <div
          className="mx-3 mb-2 max-h-[260px] overflow-y-auto rounded-xl bg-[#262626] p-1"
          data-testid="canvas-agent-session-menu"
          role="dialog"
          aria-label="会话列表"
        >
          {sessions.length === 0 ? (
            <p className="px-2 py-3 text-center text-[12px] text-white/40">
              还没有会话
            </p>
          ) : (
            sessions.map((s) => {
              const active = s.id === activeId;
              return (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => {
                    selectAiSession(s.id);
                    setPanel(null);
                    if (s.id !== activeId) pushToast(FEEDBACK.switchSession(s.title));
                  }}
                  data-testid={`canvas-agent-session-row-${s.id}`}
                  aria-current={active ? "true" : undefined}
                  className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left ${
                    active ? "bg-white/10" : "hover:bg-white/[0.06]"
                  }`}
                >
                  {/* 当前会话的高亮竖条：用宽度而不是颜色区分，
                      免得只靠颜色（无障碍上更稳）。 */}
                  <span
                    className={`h-4 w-[2px] shrink-0 rounded-full ${
                      active ? "bg-white/70" : "bg-transparent"
                    }`}
                  />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[13px] text-white/90">
                      {s.title}
                    </span>
                    <span className="block text-[11px] text-white/40">
                      {s.messages.length} 条消息
                    </span>
                  </span>
                </button>
              );
            })
          )}
        </div>
      ) : null}

      {/* Batch 809: 三个弹出面板，位置在 composer 之上 */}
      {panel === "skills" ? (
        <div
          className="mx-3 mb-2 rounded-xl bg-[#262626] p-2"
          data-testid="agent-skills-panel"
          role="dialog"
          aria-label="搜索技能"
        >
          <input
            value={skillQuery}
            aria-label="搜索技能"
            placeholder="搜索技能"
            onChange={(e) => setSkillQuery(e.target.value)}
            className="mb-1 h-8 w-full rounded-md bg-white/[0.06] px-2 text-[13px] text-white outline-none placeholder:text-white/35"
          />
          {SKILLS.filter((sk) => sk.name.includes(skillQuery.trim()) || !skillQuery.trim()).map((sk) => (
            <button
              key={sk.name}
              type="button"
              data-testid="agent-skill-item"
              onClick={() => addSkill(sk.chip)}
              className="flex w-full flex-col items-start gap-0.5 rounded-md px-2 py-1.5 text-left hover:bg-white/10"
            >
              <span className="flex items-center gap-1.5 text-[13px] text-white/90">
                {sk.name}
                <span className="rounded bg-white/10 px-1 text-[10px] text-white/60">官方</span>
              </span>
              <span className="text-[11px] leading-4 text-white/45">{sk.desc}</span>
            </button>
          ))}
        </div>
      ) : null}

      {panel === "mention" ? (
        <div
          className="mx-3 mb-2 rounded-xl bg-[#262626] p-2"
          data-testid="agent-mention-panel"
          role="dialog"
          aria-label="添加参考"
        >
          <p className="px-2 py-1 text-[13px] text-white/85">添加参考</p>
          <div className="flex flex-wrap gap-1 px-2 pb-1.5">
            {REF_KINDS.map((k) => (
              <button
                key={k}
                type="button"
                data-testid={`agent-ref-kind-${k}`}
                onClick={() => setRefKind(k)}
                className={`h-7 rounded-md px-2.5 text-[12px] ${
                  refKind === k ? "bg-white/15 text-white" : "text-white/60 hover:bg-white/10"
                }`}
              >
                {k}
              </button>
            ))}
          </div>
          <button
            type="button"
            data-testid="agent-ref-confirm"
            onClick={() => {
              addSkill(`@${refKind}`);
              pushToast(FEEDBACK.addReference(refKind));
            }}
            className="flex h-8 w-full items-center justify-center rounded-md bg-white/10 text-[13px] text-white hover:bg-white/20"
          >
            引用{refKind}
          </button>
        </div>
      ) : null}

      {panel === "add" ? (
        <div
          className="mx-3 mb-2 rounded-xl bg-[#262626] p-1.5"
          data-testid="agent-add-panel"
          role="menu"
          aria-label="添加来源"
        >
          {ADD_SOURCES.map((src) => (
            <button
              key={src}
              type="button"
              role="menuitem"
              data-testid={`agent-add-${src}`}
              onClick={() => {
                closePanel();
                pushToast(sourcePickFeedback(src));
              }}
              className="flex h-8 w-full items-center rounded-md px-2.5 text-left text-[13px] text-white/85 hover:bg-white/10"
            >
              {src}
            </button>
          ))}
        </div>
      ) : null}

      {/* 底部输入卡片 */}
      <div className="p-3">
        <div className="rounded-2xl bg-white/[0.06] p-3">
          {/* Batch 809 SOURCE_FACT: 点技能 chip / 选参考后，composer 里出现
              富文本 token（源站 class `node-composerChip`），发送钮随之可用 */}
          {tokens.length > 0 ? (
            <div
              className="mb-1.5 flex flex-wrap items-center gap-1"
              data-testid="agent-composer-tokens"
            >
              {tokens.map((t) => (
                <span
                  key={t}
                  className="inline-flex items-center gap-1 rounded bg-[#0A5CD6]/25 px-1.5 py-0.5 text-[12px] text-[#5AB0FF]"
                >
                  {t}
                  <button
                    type="button"
                    aria-label={`移除 ${t}`}
                    onClick={() => setTokens((all) => all.filter((x) => x !== t))}
                    className="text-white/60 hover:text-white"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          ) : null}
          {richPrefill ? (
            <div
              className="min-h-[44px] cursor-text text-[13px] leading-[22px] text-white"
              data-testid="agent-rich-prefill"
              onClick={() => setEditing(true)}
            >
              用{' '}
              <span className="inline-flex items-center gap-0.5 rounded bg-[#0A5CD6]/25 px-1 align-top text-[#5AB0FF]">
                <WandSparkles size={11} />
                视频反解
              </span>{' '}
              反推出{' '}
              <span className="inline-flex items-center gap-1 rounded bg-white/[0.10] px-1 py-0.5 align-top">
                <img
                  src={refChip!.poster}
                  alt=""
                  className="h-4 w-6 rounded-sm object-cover"
                />
                <span className="max-w-[80px] truncate text-[12px] text-white/85">
                  {refChip!.label}
                </span>
              </span>{' '}
              的提示词，并创建文本节点，方便我拉片复刻
              {/* batch 8 verifier 读取 input.value */}
              <input type="hidden" value={prefill || ""} readOnly />
            </div>
          ) : (
          <p className="min-h-[44px] text-[13px] leading-[22px] text-white/35">
            <input
              value={input}
              onChange={(e) => {
                setInput(e.target.value);
                setAiDrawerDraft(e.target.value);
              }}
              /* Batch 834：这枚输入框此前**既无 data-testid 也无 aria-label**，
                 只靠 placeholder —— 而批 823 立的那条「信号失明本身就是发现」
                 （浮层普查只扫浮层，没扫表单控件）说的正是这种情况：
                 一个可见的输入控件，自动化与读屏都够不着它。
                 名字沿用 placeholder 的起头，与源站其它 chrome 锚点同一套词汇。 */
              aria-label="输入想法、剧本或上传参考"
              data-testid="agent-composer-input"
              placeholder="输入想法、剧本或上传参考，支持 “ / ” 使用技能，"
              className="w-full bg-transparent text-[13px] text-white outline-none placeholder:text-white/35"
            />
            {refChip ? (
              <span className="mr-1 inline-flex items-center gap-1 rounded bg-white/[0.10] px-1 py-0.5 align-middle">
                <img
                  src={refChip.poster}
                  alt=""
                  className="h-4 w-6 rounded-sm object-cover"
                />
                <span className="max-w-[80px] truncate text-[12px] text-white/85">
                  {refChip.label}
                </span>
              </span>
            ) : null}
            {/* SOURCE_FACT (batch 808): 占位文案里的 @ 是 24×24 的独立可访问节点
                `canvas-agent-composer-placeholder-mention` @[1608,672]，
                与底行那个 32×32 的 `canvas-agent-composer-mention` 是两个东西 */}
            <span
              data-testid="canvas-agent-composer-placeholder-mention"
              className="mt-1 inline-flex h-6 w-6 items-center justify-center rounded bg-white/[0.08] text-white/55"
            >
              <AtSign size={10} />
              <span className="sr-only">添加主体</span>
            </span>
            ，和 Agent 一起创作
          </p>
          )}
          <div className="mt-2 flex items-center gap-1">
            {/* 批 382 SOURCE_FACT: 输入行 aria 实测 从本地、画布或资产库添加 */}
            <button
              type="button"
              aria-label="从本地、画布或资产库添加"
              data-testid="canvas-agent-composer-add"
              onClick={() => setPanel((v) => (v === "add" ? null : "add"))}
              className="flex size-8 items-center justify-center rounded-md text-white/75 hover:bg-white/10"
            >
              <Plus size={16} />
            </button>
            <button
              type="button"
              aria-label="使用技能"
              data-testid="canvas-agent-skill-trigger"
              onClick={() => setPanel((v) => (v === "skills" ? null : "skills"))}
              className="flex h-8 w-[90px] items-center gap-1 rounded-md px-2 text-[13px] text-white/75 hover:bg-white/10"
            >
              <WandSparkles size={14} />
              使用技能
            </button>
            <button
              type="button"
              aria-label="引用参考"
              data-testid="canvas-agent-composer-mention"
              onClick={() => setPanel((v) => (v === "mention" ? null : "mention"))}
              className="flex size-8 items-center justify-center rounded-md text-white/75 hover:bg-white/10"
            >
              <AtSign size={14} />
            </button>
            <span className="flex-1" />
            <button
              type="button"
              aria-label="发送消息"
              data-testid="canvas-agent-send"
              disabled={!canSend}
              onClick={send}
              className={`flex size-8 items-center justify-center rounded-full disabled:cursor-default ${
                canSend ? "bg-white text-black" : "bg-white/[0.14] text-white/30"
              }`}
            >
              <ArrowUp size={15} />
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
