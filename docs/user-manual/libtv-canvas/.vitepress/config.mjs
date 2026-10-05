import { defineConfig } from 'vitepress';

// LibTV 画布用户手册 · 静态站点配置。
//
// 构建：docs/user-manual/libtv-canvas/ 下执行 ./build-site.sh 或 npm run build
// 产物：.vitepress/dist/（纯静态，整个目录拷到任意 Web 服务器即可发布）
export default defineConfig({
  lang: 'zh-CN',
  title: 'LibTV 画布 · 用户手册',
  description: 'LibTV 画布（liblib.tv）用户手册：建画布、九类节点、连线、成组、快捷键与排障',
  // 部署到子路径时改成 base: '/manual/' 之类，然后重新构建
  base: '/',
  // 手册 README.md 作为站点首页
  rewrites: {
    'README.md': 'index.md',
  },
  // 只发布面向读者的页面。工作账本（AUDIT / PROGRESS）与发布说明不进站点。
  srcExclude: ['**/AUDIT.md', '**/PROGRESS.md', '**/PUBLISH.md'],
  ignoreDeadLinks: true,
  themeConfig: {
    siteTitle: 'LibTV 画布 · 用户手册',
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
          { text: '快速上手', link: '/00-quickstart' },
          { text: '进入画布', link: '/10-tasks/enter-canvas' },
          { text: '管理画布（新建 / 切换 / 重命名 / 复制 / 删除）', link: '/10-tasks/manage-canvases' },
        ],
      },
      {
        text: '节点与连线',
        items: [
          { text: '创建九类节点', link: '/10-tasks/create-nodes' },
          { text: '脚本节点：三个入口与全屏分镜表', link: '/10-tasks/script-node' },
          { text: '图片节点的「预设」面板', link: '/10-tasks/image-presets' },
          { text: '连接节点', link: '/10-tasks/connect-nodes' },
          { text: '生成图片 / 视频 / 音频', link: '/10-tasks/generate-media' },
        ],
      },
      {
        text: '组织与浏览',
        items: [
          { text: '整理画布：平移、缩放、小地图、资产管理', link: '/10-tasks/organize-canvas' },
          { text: '工作流与故事板两种视图', link: '/10-tasks/storyboard-mode' },
          { text: '素材库、工具箱与添加资源', link: '/10-tasks/asset-library' },
          { text: '生成历史：找回生成过的东西', link: '/10-tasks/generate-history' },
          { text: '角色造型室', link: '/10-tasks/character-studio' },
        ],
      },
      {
        text: '协作与效率',
        items: [
          { text: '用 TV Director 让 Agent 替你操作', link: '/10-tasks/agent-director' },
          { text: '发布与分享', link: '/10-tasks/share-canvas' },
          { text: '快捷键', link: '/10-tasks/shortcuts' },
        ],
      },
      {
        text: '参考与排障',
        items: [
          { text: '参考表：键位、控件、参数与名词', link: '/20-reference' },
          { text: '概念：画布、节点、连线、分组与视图', link: '/30-concepts' },
          { text: '故障排查（按症状查）', link: '/90-troubleshooting' },
        ],
      },
    ],
  },
});
