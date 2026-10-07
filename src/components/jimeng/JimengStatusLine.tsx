"use client";

import { useJimengStore } from "@/store/jimengStore";

/**
 * 1031 SOURCE_FACT：源站画布左下角有一行状态，登记的是**形状**不是读数：
 *
 *     76 nodes, 0 edges, 0 selected. Editable. Room connected. 已保存.
 *
 * ⚠️⚠️ **这三个数必须从 store 现算，不许硬编码。**
 *
 * `src/store/jimengStore.ts` 里有一个 `project.nodeCount: 2` —— 它是一个
 * **死字段**（全仓无人读它，顶栏用的是 `s.nodes.length + groups.size` 现算）。
 * 它今天无害只是因为没人用；谁哪天图省事改成读它，顶栏立刻开始撒谎：
 * 插三个节点它仍然显示 2。
 *
 * 这正是 1031 这一批反复撞到的那条：
 * **「印出来的读数」不等于「接了线的读数」。**
 * 一个数字如果只是被**声明**在某处而没有从**源头**算出来，它就只是一段注释。
 *
 * 为什么是「形状」而不是把 `76` 也抄过来：节点数每次跑都会变
 * （真实站这个画布就有 76 个节点，而任何一次打开都可能不同）。
 * 钉死数字的判据必然过期 —— 那正是 1014 那三条 P 的死法。
 */
export function JimengStatusLine() {
  // ⚠️⚠️⚠️⚠️⚠️ **这里必须订阅「标量」，不许订阅「现算出来的对象」。**
  //
  // 第一版写成 `useJimengStore((s) => ({ nodes: s.nodes.length, ... }))`，
  // 注释还专门解释了「为什么一次性算完，免得三个数来自不同时刻」。
  // 结果页面直接崩：`Maximum update depth exceeded` ——
  // **zustand 用 `Object.is` 比对选择器的返回值，而选择器每次都返回一个新对象
  // ⇒ 永远「变了」⇒ 每次都触发重渲染 ⇒ 无限循环。**
  //
  // 那个「不同时刻」的顾虑并不成立：`useStore` 在同一次渲染里读到的是
  // 同一个 store 快照，拆成四个标量订阅拿到的仍是**同一次**状态。
  // ⇒⇒⇒ 真正的教训不是「少订阅几次」，而是
  // **选择器的返回值必须是「可稳定比较的」，否则它就是一台永动机。**
  const nodes = useJimengStore((s) => s.nodes.length);
  const edges = useJimengStore((s) => s.edges.length);
  const selected = useJimengStore((s) => {
    let n = 0;
    for (const node of s.nodes) if (node.selected) n += 1;
    return n; // ⭐ 返回 number，Object.is 稳定
  });
  const saved = useJimengStore((s) => s.project.saved);

  // ⭐ 形状写成**一个模板字符串**而不是散在 JSX 里 ——
  //   JSX 会把「换行 + 缩进」折叠成一个空格，而契约的正则要求的是**恰好一个空格**；
  //   把形状交给 JSX 的空白折叠规则，就等于让排版细节决定判据成立与否。
  // ⚠️⚠️ 结尾那个句点**是「已保存」这一形状的一部分**（源站：`… Room connected. 已保存.`）。
  //   而「保存中…」是**另一种形状**：它自带省略号，再补一个句点就成了 `保存中….`
  //   （第一版真的写出来了，看着像「多了一个点」的排版 bug）。
  //   ⇒⇒⇒ 结论：**保存态也是形状的一部分**。契约登记的是「已保存」那一行，
  //   所以形状判据只在已保存样本上做（探针 1031d 的 `P4`），保存中样本只参与 `P5`
  //   ——「数字是否真的接在 store 上」。
  const text = `${nodes} nodes, ${edges} edges, ${selected} selected.`
    + ` Editable. Room connected. ${saved ? "已保存." : "保存中…"}`;

  return (
    <div
      data-testid="canvas-status-line"
      aria-label="Canvas status"
      className="pointer-events-none absolute bottom-2 left-2 z-10 select-none
                 font-mono text-[11px] leading-none text-white/55"
    >
      {text}
    </div>
  );
}