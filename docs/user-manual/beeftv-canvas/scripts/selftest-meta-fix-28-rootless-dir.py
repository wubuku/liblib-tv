import sys
# 注入「无根目录常量 + os.path.join」——方向十的另一条判据。
s = sys.stdin.read()
anchor = 'MANIFEST = os.path.join(SHOT_DIR,'
assert anchor in s, "锚点未命中：找不到 MANIFEST 赋值行"
extra = ("\n_SELFTEST_RELDIR = " + repr("screenshots")
         + "\n_SELFTEST_JOINED = os.path.join(_SELFTEST_RELDIR, " + repr("manifest.yml") + ")")
sys.stdout.write(s.replace(anchor, extra + "\n" + anchor, 1))
