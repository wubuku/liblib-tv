#!/usr/bin/env bash
# ============================================================
# LibTV 画布用户手册 —— 站点一键启动（构建 + 本地预览）
#
# 用法:
#   ./serve.sh                 # 构建（必要时）并在 4189 起预览
#   ./serve.sh --port 5000     # 指定端口
#   ./serve.sh --no-build      # 跳过构建，直接用现有 dist 起服务
#   ./serve.sh --stop          # 停掉本脚本自己起过的服务
#   ./serve.sh --status        # 看本手册服务跑没跑、在哪个端口
#
# 默认端口 **4189**：这是本手册的专属端口。
#   ⛔ 不要用 4188 —— 那本 Flowable Trial 原站手册常年占着它，
#      本仓库里多本手册并存，撞端口是常态。
#   端口被占时本脚本**不会杀任何进程**，只会告诉你「谁在占」并自动往后找。
#
# 为什么用 `python3 -m http.server` 而不是 `npx vitepress preview`：
#   vite preview（也就是 build-site.sh --preview）底层是 sirv，
#   **在启动时就把文件清单缓存下来**。手册改完再刷新，看到的还是旧页面，
#   每次都得重起进程才生效 —— PUBLISH.md 里记的就是这件事。
#   `python3 -m http.server` 没有这层缓存，改完刷新就是新的。
#
# 产物: .vitepress/dist/  —— 纯静态，整体拷贝到任意 Web 服务器即可发布
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

DIST="$SCRIPT_DIR/.vitepress/dist"
PIDFILE="$SCRIPT_DIR/.vitepress/serve.pid"
PORTFILE="$SCRIPT_DIR/.vitepress/serve.port"
LOGFILE="$SCRIPT_DIR/.vitepress/serve.log"
DEFAULT_PORT=4189

TS="$(date +%H:%M:%S)"
log()  { printf '\033[1;34m[serve %s]\033[0m %s\n' "$TS" "$*"; }
ok()   { printf '\033[1;32m[  ok  %s]\033[0m %s\n' "$TS" "$*"; }
warn() { printf '\033[1;33m[ warn %s]\033[0m %s\n' "$TS" "$*"; }
fail() { printf '\033[1;31m[ FAIL %s]\033[0m %s\n' "$TS" "$*" >&2; exit 1; }

# ---------- 参数 ----------
PORT="$DEFAULT_PORT"
DO_BUILD=1
ACT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --port)      PORT="${2:?--port 后面要跟端口号}"; shift 2 ;;
    --port=*)    PORT="${1#*=}"; shift ;;
    --no-build)  DO_BUILD=0; shift ;;
    --stop)      ACT="stop"; shift ;;
    --status)    ACT="status"; shift ;;
    -h|--help)   sed -n '2,30p' "$0"; exit 0 ;;
    *) fail "不认识的参数：$1（用 --help 看用法）" ;;
  esac
done

# ---------- --status ----------
if [ "$ACT" = "status" ]; then
  if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    P="$(cat "$PORTFILE" 2>/dev/null || echo '?')"
    ok "本手册服务在跑： pid=$(cat "$PIDFILE")  端口=$P"
    log "地址: http://127.0.0.1:$P/"
  else
    warn "本手册服务没在跑。用 ./serve.sh 启动。"
  fi
  exit 0
fi

# ---------- --stop ----------
# ⛔ 只停 PIDFILE 里记着的、**本脚本自己**起过的进程。
#    绝不按端口杀 —— 那个端口上可能是别人的服务。
if [ "$ACT" = "stop" ]; then
  if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    kill "$(cat "$PIDFILE")" 2>/dev/null || true
    rm -f "$PIDFILE" "$PORTFILE"
    ok "已停掉本手册服务"
  else
    warn "没有本脚本起过的服务在跑（PID 文件不存在或进程已退出）"
  fi
  exit 0
fi

# ---------- 构建 ----------
if [ "$DO_BUILD" = "1" ]; then
  log "══════ 构建 ══════"
  ./build-site.sh
  ok "构建完成"
else
  log "跳过构建（--no-build）"
fi

[ -d "$DIST" ] || fail "没有产物目录 $DIST，先不带 --no-build 跑一次"

# ---------- 端口 ----------
# ⭐ 端口被占就往后找，**绝不杀别人的进程**
port_free() { ! lsof -ti:"$1" >/dev/null 2>&1; }

ORIG="$PORT"
TRIES=0
while ! port_free "$PORT"; do
  if [ "$TRIES" = "0" ]; then
    HOLDER="$(lsof -ti:"$PORT" 2>/dev/null | head -1 || true)"
    HCMD="$(ps -p "$HOLDER" -o command= 2>/dev/null | cut -c1-90 || true)"
    warn "端口 $PORT 已被占用 —— pid=$HOLDER  ${HCMD}"
    warn "⛔ 本脚本不会杀它（多半是本仓库另一本手册的服务）。改用下一个空闲端口。"
  fi
  PORT=$((PORT + 1))
  TRIES=$((TRIES + 1))
  [ "$TRIES" -ge 20 ] && fail "$ORIG~+$TRIES 都没找到空闲端口，请用 --port 手工指定"
done
[ "$PORT" != "$ORIG" ] && ok "改用端口 $PORT"

# ---------- 启动 ----------
mkdir -p "$(dirname "$PIDFILE")"
: > "$LOGFILE"
nohup python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$DIST" \
  >> "$LOGFILE" 2>&1 < /dev/null &
SRV_PID=$!
echo "$SRV_PID" > "$PIDFILE"
echo "$PORT"  > "$PORTFILE"
disown "$SRV_PID" 2>/dev/null || true

# ⭐ 阳性对照：必须**真的 GET 一次**才算起来，
#    光看进程活着不算（进程起来到能应答之间有窗口）。
URL="http://127.0.0.1:$PORT/"
for _ in 1 2 3 4 5 6 7 8 9 10; do
  sleep 0.4
  CODE="$(curl -s -o /dev/null -w '%{http_code}' "$URL" 2>/dev/null || echo 000)"
  [ "$CODE" = "200" ] && break
done
[ "${CODE:-000}" = "200" ] || fail "起了但 GET 不通（HTTP ${CODE:-000}），看日志：$LOGFILE"
# 再验一个真实页面，防止首页通了而子页面 404
SUB="$(curl -s -o /dev/null -w '%{http_code}' "$URL/90-troubleshooting.html" 2>/dev/null || echo 000)"
[ "$SUB" = "200" ] || warn "首页通了，但 /90-troubleshooting.html 返回 ${SUB}，先看看"

echo
ok "══════ LibTV 画布用户手册已启动 ══════"
printf '\n\033[1;32m   %s\033[0m\n' "$URL"
echo
log "几个常看的入口："
printf '   故障排查      %s90-troubleshooting.html\n' "$URL"
printf '   建节点/底栏   %s10-tasks/create-nodes.html\n' "$URL"
printf '   快捷键        %s10-tasks/shortcuts.html\n' "$URL"
printf '   故事板        %s10-tasks/storyboard-mode.html\n' "$URL"
echo
log "pid=$SRV_PID  端口=$PORT  日志=$LOGFILE"
log "停掉它： ./serve.sh --stop    看状态： ./serve.sh --status"
log "改完正文想立刻看新的： 再次 ./serve.sh --no-build（不用重起进程）"
echo
