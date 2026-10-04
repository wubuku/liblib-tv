import sys, json, yaml

# 取 manifest 明细。🔑 `default=str` 是必须的：`captured_at` 逐字长得像 ISO 时间戳，
# YAML 会把它解析成 **datetime 对象**，直接 json.dumps 会 TypeError。
# 这也是「必须用真解析器」的又一个理由 —— 正则切块永远看不到「这个字段其实是日期」。
d = yaml.safe_load(open(sys.argv[1], encoding='utf-8'))
print(json.dumps(d['screenshots'], ensure_ascii=False, default=str))
