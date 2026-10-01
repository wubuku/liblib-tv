import sys
# 用例 26：上游让 workspaceCapabilities().local 不再写死 true，
# 于是「个人渠道」那个大标题分支**变得可达**。
# 注入后 p_channel_page_three_names 的 (a) 失效 → 整条应失效。
# 守的是手册「『个人渠道』作为大标题的分支**渲染不出来**」这个否定式断言：
# 一旦它可达了，手册必须改写成「换个部署形态就会看到个人渠道」。
s = sys.stdin.read()
old = "export type WorkspaceCapabilities = { local: true; localAssets: boolean; providerCalls: boolean };"
assert old in s, "锚点未命中"
s = s.replace(old, "export type WorkspaceCapabilities = { local: boolean; localAssets: boolean; providerCalls: boolean };", 1)
old2 = """    return {
        local: true,"""
assert old2 in s, "锚点 2 未命中"
s = s.replace(old2, """    return {
        local: capabilitySnapshot?.profile === "remote",""", 1)
sys.stdout.write(s)
