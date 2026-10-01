import sys
# 用例 17：上游真的把前端接上服务端的素材列表接口（GET /assets）。
# 注入后 p_asset_list_endpoint_uncalled 的「前端零处调用」子判据失效。
# 守的是手册「服务端素材列表接口闲置、前端零调用」这一句——
# 一旦有人补上这个调用，手册关于素材只有本机副本的整段说明都要回走。
s = sys.stdin.read()
anchor = 'export function listAssetFolders() {'
assert anchor in s, "锚点未命中"
s = s.replace(anchor,
              'export function listRemoteAssets() {\n'
              '    return http.get<{ assets: unknown[] }>("/assets");\n'
              '}\n\n'
              + anchor,
              1)
sys.stdout.write(s)
