import sys
# 注入「裸相对 glob」——方向十必须报。
s = sys.stdin.read()
anchor = 'MANIFEST = os.path.join(SHOT_DIR,'
assert anchor in s, "锚点未命中：找不到 MANIFEST 赋值行"
line = "\n_SELFTEST_PROBE = glob.glob(" + repr("**/*.md") + ", recursive=True)"
assert line.strip() not in s, "注入已存在"
sys.stdout.write(s.replace(anchor, anchor + line, 1))
