import sys
# 用例 20：上游给某个档位打开「声调」开关。
# 注入后 p_audio_panel_never_offers_pitch_volume 的 (b) 失效。
# 守的是手册那句「面板从不提供声调与音量」——
# 一旦有档位打开这两块，手册就必须改口（因为控件代码本来就在面板里）。
s = sys.stdin.read()
old = "        showPitch: false,"
assert old in s, "锚点未命中"
s = s.replace(old, "        showPitch: true,", 1)
sys.stdout.write(s)
