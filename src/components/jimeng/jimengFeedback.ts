/**
 * jimeng 画布的**反馈文案**唯一出处 (Batch 812)。
 *
 * ## 为什么要集中
 *
 * 散着写的时候出了三��真问题（都是实际查出来的，不是假想）：
 *
 * 1. **漏标注**。batch 807 同批新增的三个节点里，主体节点的反馈带「（mock）」，
 *    时间线的 `已添加「片段 1」到时间线` 却没带。同一个批次里就不一致。
 * 2. **零信息量**。`${label}（mock）` 这种纯拼接，用户看到的是
 *    「上传（mock）」「从画布添加（mock）」—— 只是把按钮文字复述了一遍，
 *    等于什么都没说。反馈的意义是告诉用户**发生了什么**。
 * 3. **同一动作多处硬编码**。「视频下载已开始（mock）」在三个文件里各写一遍，
 *    改文案要改三个地方，漏一个就不一致。
 *
 * ## 标注规则
 *
 * - 源站有对应文案的 → 逐字照抄源站，不加标注（如「复制画布中…」）
 * - 源站没有对应物的（本复刻自有扩展）→ 保留「（mock）」，
 *   让用户知道这是个原型动作
 * - **不要**为了标注而牺牲可读性：「会话列表：3 条（mock）」比
 *   「会话列表（mock）」有用得多
 *
 * 验收 `verify-jimeng-batch812.py` 断言：所有 mock 反馈都经由本模块产生，
 * 且同一动作在不同入口的文案完全一致。
 */

/** 追加 mock 标注。已带标注的不重复加。 */
export function mockMsg(text: string): string {
  return text.includes("（mock）") ? text : `${text}（mock）`;
}

/** 同一动作的文案只在这里写一份 */
export const FEEDBACK = {
  // ── 媒体：源站同类操作走真实下载/入库，复刻无后端 ──
  downloadVideo: () => mockMsg("视频下载已开始"),
  saveToSubjectLibrary: () => mockMsg("已保存到主体库"),
  switchProject: (name: string) => mockMsg(`已切换到「${name}」`),
  createCanvasProject: () => mockMsg("新建画布项目"),

  // ── 新增节点（batch 807/810）──
  addTimelineClip: (name: string) => mockMsg(`已添加「${name}」到时间线`),
  importSubject: (name: string) => mockMsg(`已导入「${name}」`),
  saveSubjectMeta: () => mockMsg("已保存主体描述"),
  needCanvasNodeFirst: (action: string) => mockMsg(`${action}：请先选中一个画布节点`),
  needAssetsFirst: (action: string) => mockMsg(`${action}：请先打开资产库`),
  enterDirectorStage: () => mockMsg("进入导演台"),
  exitDirectorStage: () => mockMsg("已退出导演台"),

  // ── AI 抽屉（batch 810）──
  sessionList: (n: number) => mockMsg(`会话列表：${n} 条`),
  newSession: () => mockMsg("已新建会话"),
  addReference: (kind: string) => mockMsg(`已添加参考：${kind}`),

  // ── 生成类：走 store 的任务提示 ──
  taskSubmitted: (name: string) => mockMsg(`${name}任务已提交，处理中…`),
  inferResult: () => mockMsg("提示词反推结果"),

  // ── 离线（源站无对应物）──
  offlineSynced: () => mockMsg("离线修改已同步"),
  offlineDiscarded: () => mockMsg("已丢弃离线修改"),
} as const;

/** 「来源菜单」这类动作的反馈。
 *
 *  原来写成 `pushToast(\`${src}（mock）\`)`，用户看到的是「上传（mock）」——
 *  把按钮名复述一遍，没有任何新增信息。这里补成一句有结果的反馈。
 */
export function sourcePickFeedback(src: string): string {
  switch (src) {
    case "上传":
      return mockMsg("请选择要上传的文件");
    case "从资产库添加":
      return mockMsg("请在资产库中选择素材");
    case "从画布添加":
      return mockMsg("请在画布中选择节点");
    default:
      return mockMsg(src);
  }
}
