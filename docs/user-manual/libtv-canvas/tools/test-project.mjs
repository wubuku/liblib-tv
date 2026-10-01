// 本手册专用的**丢弃式测试项目**。
//
// 为什么必须专用：LibTV 站点有「单画布单编辑者保护」——同一个 project 在第二处
// 打开会被遮罩挡成只读（研究记录：docs/research/liblib-canvas-sampling-2026-09-06/README.md §5）。
// 用户自己那个有头浏览器正开着另一个项目，所以取证一律用下面这个专用项目，
// 绝不碰用户正在编辑的 projectId。
//
// 创建方式：项目页 /project 点「新建项目」→ 直接进入画布（无对话框），项目名默认「未命名工作区」。
export const TEST = {
  spaceId: '10354929',
  projectId: 'a4ef3de0cdca4977ba45b373eb5165b5',
  /** 取证期间不改名，避免和用户真实项目重名混淆；名称仅用于 PROGRESS.md 台账说明。 */
  note: '由「新建项目」按钮创建的一次性取证项目，用户真实项目为 a860e1da8e9e4504bececda022386429',
};

export const CANVAS_URL = `https://www.liblib.tv/canvas?spaceId=${TEST.spaceId}&projectId=${TEST.projectId}`;
