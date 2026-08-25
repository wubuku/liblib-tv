# Agent / Share Specification

## AgentDrawer

- Target: `src/components/AgentDrawer.tsx`
- Width: `340px` on desktop; hidden below `sm` to preserve the existing compact shell.
- Overlay selector: `[data-liblib-overlay="agent"]`
- When open on desktop, the fixed top navigation reserves the drawer width and hides its duplicate Agent trigger so the drawer header remains clickable.

### Structure

```text
header: 新对话 + command icons + close
body:
  Skill 就位, ready when yo... + 换一批
  2×2 skill cards
  browser notification banner
footer:
  composer textarea
  local tool buttons + send
```

### Local prototype interactions

| Action | Result |
|---|---|
| Click Skill | Selects card and writes its title to the composer |
| Click 换一批 | Switches between two local recommendation sets |
| Click 开启 | Dismisses notification banner and marks local enabled state |
| Click banner X | Dismisses notification banner |
| Type and click 发送 | Shows local-only submission feedback |
| Click close | Calls `useUIStore.toggleAgent` |

## SharePanel

- Target: nested component in `src/components/TopNavBar.tsx`
- Width/height: `360x166`
- Overlay selector: `[data-liblib-overlay="share"]`

### Source-shaped copy

- Title: `发布与分享`
- Action 1: `在LibTV上发布`
- Description: `发布你的作品和创作过程，让更多创作者看到。`
- Action 2: `分享链接`
- Description: `拥有此链接的人可以查看并复制你的画布。`

### Local prototype interactions

Clicking either action shows an explicit “本地原型，未连接服务” status in the panel. No network request or fake URL is created.

## Stable selectors

- `[data-agent-drawer]`
- `[data-agent-skill]`
- `[data-agent-refresh]`
- `[data-agent-notification]`
- `[data-agent-notification-enable]`
- `[data-agent-notification-close]`
- `[data-agent-composer]`
- `[data-agent-send]`
- `[data-agent-status]`
- `[data-share-action]`
- `[data-share-status]`
