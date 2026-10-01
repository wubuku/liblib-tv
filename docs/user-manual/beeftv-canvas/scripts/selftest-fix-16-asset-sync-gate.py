import sys
# 用例 16：上游把「有没有远端同步会话」从写死 false 改成真的去问会话。
# 注入后 p_asset_sync_gated_off 的 (a) 子判据失效 → 整条应失效。
# 这条用例守的是手册「素材侧的同步出口都被写死的常量关掉了」这个**机制**说法：
# 只要常量一变，手册那句「为什么没同步过去」就必须回走重写。
s = sys.stdin.read()
old = "export function hasRemoteUserDataSyncSession() {\n    return false;\n}"
assert old in s, "锚点未命中"
s = s.replace(old,
              "export function hasRemoteUserDataSyncSession() {\n"
              "    return Boolean(window.localStorage.getItem(\"beef-remote-sync-session\"));\n"
              "}",
              1)
sys.stdout.write(s)
