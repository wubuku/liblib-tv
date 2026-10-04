import sys
# 用例 17：上游真的把前端接上服务端的素材列表接口（GET /assets）。
# 注入后 p_asset_list_endpoint_uncalled 的「前端零处调用」子判据失效。
# 守的是手册「服务端素材列表接口闲置、前端零调用」这一句——
# 一旦有人补上这个调用，手册关于素材只有本机副本的整段说明都要回走。
#
# **Batch 272 换锚点**：上游给 `listAssetFolders` 加了可选参数
# （实测 v1.7.3 是 `export function listAssetFolders(config?: HttpRequestConfig) {`，
# 而 v1.6.22 是无参的 `export function listAssetFolders() {`），
# **旧锚点写死了无参形态，于是 `assert` 直接报「锚点未命中」，整条用例作废**。
# **修法**：锚点只取**声明的开头那段**，与参数列表无关——
# **这样上游再加参数也不用再改一次**（纪律 250：收敛之前先看能不能一步到位）。
# **注入的是新导出函数**（插在该声明之前），所以参数形态不影响注入结果。
s = sys.stdin.read()
anchor = "export function listAssetFolders("
assert anchor in s, "锚点未命中：上游已没有 listAssetFolders 这个导出"
FEATURE = 'http.get<{ assets: unknown[] }>("/assets")'
injected = ("export function listRemoteAssets() {\n"
            "    return " + FEATURE + ";\n"
            "}\n\n" + anchor)
s = s.replace(anchor, injected, 1)
assert FEATURE in s, "注入空转：str.replace 没有真的改到东西"
sys.stdout.write(s)
