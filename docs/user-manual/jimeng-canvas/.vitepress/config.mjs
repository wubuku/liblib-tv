import { defineConfig } from 'vitepress';

// 即梦画布用户手册静态站点配置。
// 构建：在 docs/user-manual/jimeng-canvas/ 下 ./build-site.sh 或 npm run build，
// 产物在 .vitepress/dist/，整个 dist 目录即可拷贝到任意静态 Web 服务器发布。
export default defineConfig({
  lang: 'zh-CN',
  title: '即梦画布 · 用户手册',
  description: '即梦智能画布用户手册：从创建节点、连线参考到生成面板与画布整理',
  // 部署到子路径时改为如 base: '/manual/'，并重新构建
  base: '/',
  // 手册 README.md 作为站点首页
  rewrites: {
    'README.md': 'index.md',
  },
  // 站点只包含面向用户的页面；Agent 工作账本与构建/发布文档不进站点
  srcExclude: [
    '**/AUDIT.md',
    '**/PROGRESS.md',
    '**/TEST_MEDIA_ASSETS.md',
    '**/SOURCE_OBSERVATIONS.md',
    '**/PUBLISH.md',
    '**/FINAL-REPORT.md',
  ],
  ignoreDeadLinks: true,
  themeConfig: {
    siteTitle: '即梦画布 · 用户手册',
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
          { text: '快速上手：五步认识即梦画布', link: '/00-quickstart' },
        ],
      },
      {
        text: '核心操作（优先阅读）',
        items: [
          { text: '创建节点（含本地上传）', link: '/10-tasks/create-first-node' },
          { text: '平移、缩放与控制画布视图', link: '/10-tasks/navigate-canvas' },
          { text: '连接节点（参考连线）', link: '/10-tasks/connect-nodes' },
          { text: '使用节点工具条', link: '/10-tasks/use-node-toolbar' },
          { text: '准备生成（发送前停止）', link: '/10-tasks/prepare-generation' },
        ],
      },
      {
        text: '节点编辑与管理',
        items: [
          { text: '创建与编辑文本节点', link: '/10-tasks/edit-text-node' },
          { text: '创建并使用主体节点（@主体 引用）', link: '/10-tasks/subject-node' },
          { text: '复制、删除与撤销', link: '/10-tasks/duplicate-delete-history' },
          { text: '使用资产库并上传素材', link: '/10-tasks/assets-and-upload' },
          { text: '编组、排列与整理画布', link: '/10-tasks/organize-group-layout' },
        ],
      },
      {
        text: '媒体与音频',
        items: [
          { text: '预览与播放视频节点', link: '/10-tasks/media-playback' },
          { text: '配置音频节点（配音与声音库）', link: '/10-tasks/audio-node-voice' },
        ],
      },
      {
        text: '辅助功能',
        items: [
          { text: '使用「与 AI 对话」智能体抽屉', link: '/10-tasks/ai-agent-drawer' },
          { text: '管理画布上下文', link: '/10-tasks/canvas-context' },
          { text: '打开帮助与使用快捷键', link: '/10-tasks/help-and-shortcuts' },
        ],
      },
      {
        text: '参考与排障',
        items: [
          { text: '参考：界面要素、菜单与参数速查', link: '/20-reference' },
          { text: '概念：即梦画布的创作模型', link: '/30-concepts' },
          { text: '排障：按症状查找', link: '/90-troubleshooting' },
        ],
      },
    ],
  },
});
