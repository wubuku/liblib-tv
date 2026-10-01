import { defineConfig } from 'vitepress';

// BeefTV 用户手册静态站点配置。
// 构建：在 docs/user-manual/beeftv-canvas/ 下 ./build-site.sh 或 npm run build，
// 产物在 .vitepress/dist/，整个 dist 目录即可拷贝到任意静态 Web 服务器发布。
export default defineConfig({
  lang: 'zh-CN',
  title: 'BeefTV · 用户手册',
  description: 'BeefTV（AI 影视创作工作台）用户手册：画布、时间线剪辑、导演台与云端 Agent',
  base: '/',
  rewrites: {
    'README.md': 'index.md',
  },
  srcExclude: ['**/AUDIT.md', '**/AUDIT-RULES.md', '**/PROGRESS.md', '**/task-inventory.yml', '**/SOURCE_OBSERVATIONS.md', '**/PUBLISH.md', '**/FINAL-REPORT.md'],
  ignoreDeadLinks: true,
  themeConfig: {
    siteTitle: 'BeefTV · 用户手册',
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
          { text: '快速开始：第一组「素材 → 生成」', link: '/00-quickstart' },
          { text: '新建创作：三种创作模式', link: '/10-tasks/create-workspace' },
          { text: '创建各类节点', link: '/10-tasks/create-nodes' },
          { text: '平移、缩放与小地图导航', link: '/10-tasks/navigate-canvas' },
          { text: '上传本地素材', link: '/10-tasks/upload-materials' },
          { text: '素材库（资产页）', link: '/10-tasks/asset-library' },
          { text: '画布库：搜索、文件夹与导入导出', link: '/10-tasks/manage-canvases' },
        ],
      },
      {
        text: '引用与生成',
        items: [
          { text: '连线引用与快速创建', link: '/10-tasks/connect-references' },
          { text: '提示词与 @mention', link: '/10-tasks/prompts-and-mentions' },
          { text: '发起图片生成', link: '/10-tasks/generate-images' },
          { text: '发起视频生成与素材限制', link: '/10-tasks/generate-video' },
          { text: '发起音频生成：音色与语速', link: '/10-tasks/generate-audio' },
          { text: '媒体版本族与重试', link: '/10-tasks/media-versions' },
        ],
      },
      {
        text: '整理与历史',
        items: [
          { text: '整理画布、Frame 与外观', link: '/10-tasks/organize-canvas' },
          { text: '撤销重做、版本历史与回收站', link: '/10-tasks/undo-history-versions' },
          { text: '账号存储、容量与配额', link: '/10-tasks/storage-quota' },
          { text: '只读画布与画布副本', link: '/10-tasks/readonly-canvas' },
          { text: '快捷键与帮助中心', link: '/10-tasks/shortcuts-help' },
        ],
      },
      {
        text: '时间线剪辑',
        items: [
          { text: '时间线剪辑器', link: '/10-tasks/timeline-editing' },
          { text: '字幕关键词高亮与 SRT', link: '/10-tasks/subtitle-highlights' },
          { text: '导出 MP4 与白膜录制', link: '/10-tasks/timeline-export' },
        ],
      },
      {
        text: '导演台',
        items: [
          { text: '导演台入门', link: '/10-tasks/director-basics' },
          { text: '关键帧动画与白膜录制', link: '/10-tasks/director-keyframes-record' },
          { text: '角色骨骼与姿势', link: '/10-tasks/director-rig-bones' },
        ],
      },
      {
        text: 'Agent 与扩展',
        items: [
          { text: '云端 Agent', link: '/10-tasks/cloud-agent' },
          { text: 'Agent 记忆与技能', link: '/10-tasks/agent-memory-skills' },
          { text: '插件管理', link: '/10-tasks/plugins-management' },
          { text: '模型配置：渠道与默认模型', link: '/10-tasks/model-channels' },
          { text: 'AI 审美批改（当前无入口）', link: '/10-tasks/art-critique' },
          { text: '本地伴随进程', link: '/10-tasks/local-runtime' },
        ],
      },
      {
        text: '参考与排障',
        items: [
          { text: '参考：快捷键、路由与端点', link: '/20-reference' },
          { text: '概念：BeefTV 是怎么工作的', link: '/30-concepts' },
          { text: '故障排查', link: '/90-troubleshooting' },
        ],
      },
    ],
  },
});
