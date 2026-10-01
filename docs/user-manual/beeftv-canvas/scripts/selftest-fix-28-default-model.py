import sys
# 用例 28：上游给出厂配置预置了默认模型（channels 非空、model 非空）。
# 注入后 p_default_config_no_models 的 (a) 失效 → 整条应失效。
# 守的是 README「新装好的 BeefTV 默认一个可用模型都没有」这句**前置条件说明**——
# 一旦上游预置了模型，读者就不必先配，「先配模型挡在所有生成动作前面」这句必须删。
s = sys.stdin.read()
old = "    channels: [],"
assert old in s, "锚点未命中"
s = s.replace(old, "    channels: [{ id: \"beefapi-default\", name: \"BeefAPI\", baseUrl: \"https://api.beef.tv\", apiKey: \"preset\" }],", 1)
old2 = "    model: \"\","
assert old2 in s, "锚点 2 未命中"
s = s.replace(old2, "    model: \"preset-default-model\",", 1)
sys.stdout.write(s)
