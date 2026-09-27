import { defineConfig } from 'vitepress';

// TDCanvas 用户手册静态站点配置。
// 构建：在 docs/user-manual/tdcanvas-canvas/ 下 ./build-site.sh 或 npm run build，
// 产物在 .vitepress/dist/，整个 dist 目录即可拷贝到任意静态 Web 服务器发布。
export default defineConfig({
  lang: 'zh-CN',
  title: 'TDCanvas · 用户手册',
  description: 'TDCanvas（AI 无限画布）用户手册：从建画布到上传素材、连线引用与图片生成',
  // 部署到子路径时改为如 base: '/manual/'，并重新构建
  base: '/',
  // 手册 README.md 作为站点首页
  rewrites: {
    'README.md': 'index.md',
  },
  // 站点只包含面向用户的页面；Agent 工作账本与构建/发布文档不进站点
  srcExclude: ['**/AUDIT.md', '**/PROGRESS.md', '**/TEST_MEDIA_ASSETS.md', '**/SOURCE_OBSERVATIONS.md', '**/PUBLISH.md'],
  ignoreDeadLinks: true,
  themeConfig: {
    siteTitle: 'TDCanvas · 用户手册',
    outline: { level: [2, 3], label: '本页目录' },
    docFooter: { prev: '上一页', next: '下一页' },
    lastUpdated: { text: '最后更新', formatOptions: { dateStyle: 'short' } },
    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索文档', buttonAriaLabel: '搜索文档' },
          modal: {
            noResultsText: '没有找到结果',
            resetButtonTitle: '清除查询',
            displayDetails: '显示详情',
            footer: { selectText: '跳转', navigateText: '切换', closeText: '关闭' },
          },
        },
      },
    },
    sidebar: [
      {
        text: '开始使用',
        items: [
          { text: '快速上手：从建画布到第一个节点', link: '/00-quickstart' },
          { text: '创建画布项目并认识工作区', link: '/10-tasks/create-canvas-project' },
          { text: '平移、缩放与小地图导航', link: '/10-tasks/navigate-canvas' },
        ],
      },
      {
        text: '节点与素材',
        items: [
          { text: '创建各类节点', link: '/10-tasks/create-nodes' },
          { text: '上传本地素材（图片/视频/音频）', link: '/10-tasks/upload-materials' },
          { text: '编辑节点：重命名、改文字、缩放与信息面板', link: '/10-tasks/edit-nodes' },
        ],
      },
      {
        text: '引用与生成',
        items: [
          { text: '连线引用与无线引用', link: '/10-tasks/connect-references' },
          { text: '发起图片生成并理解任务状态', link: '/10-tasks/generate-images' },
          { text: '图片本地处理：裁剪、切图、放大', link: '/10-tasks/image-operations' },
        ],
      },
      {
        text: '整理与管理',
        items: [
          { text: '分组、外观与画布整理', link: '/10-tasks/organize-canvas' },
          { text: '撤销重做与自动保存', link: '/10-tasks/undo-persistence' },
          { text: '管理画布项目', link: '/10-tasks/project-management' },
          { text: '快捷键与帮助', link: '/10-tasks/shortcuts-help' },
        ],
      },
      {
        text: '参考与排障',
        items: [
          { text: '参考：键位、限制、状态与设置', link: '/20-reference' },
          { text: '概念：节点、连线、双模式与项目', link: '/30-concepts' },
          { text: '排障手册', link: '/90-troubleshooting' },
        ],
      },
    ],
  },
});
