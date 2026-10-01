#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""反向注入：把「动态插件入口」从菜单合并里摘掉，模拟上游把这条链改坏。

Batch 163 起，p_art_critique_entry 锚的是**动态链**而不是写死清单，
所以要证明闸门真能抓住它，注入点也必须落在这条链上——
往写死清单里塞条目（旧用例的做法）对新判据完全无效，那正是旧判据的盲区。

锚点用 assert 钉死：锚点失配会静默产出「什么都没改」的 ref，
然后用例把「闸门没报错」当成结论——那是假通过的经典形态（见 Batch 162 的空转检测）。
"""
import sys

s = sys.stdin.read()
old = "...getPluginNodeMenuCommands()"
assert old in s, "锚点未命中：resolveAddNodeMenuCommands 里没有合并插件节点菜单"
s = s.replace(old, "...[] /* 反验注入：摘掉动态插件入口 */", 1)
s = "// [反验注入] 动态插件入口被摘掉\n" + s
sys.stdout.write(s)
