#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""反向注入（**不误伤**用例）：把 ai-art-critique 塞进「添加节点」的**写死清单**。

这一条不是要制造缺陷，而是要证明**它不该被判成缺陷**。

它同时是旧判据的反证：Batch 163 之前，p_art_critique_entry 判的就是
「写死清单里没有它」。注入之后旧闸门会立刻报失效——也就是说，
旧闸门把「上游多写了一条命令」当成了「手册说错了」。
但真正该盯的是动态链，那条链原封不动。

这也顺带说明旧判据为什么能错那么久：它对「上游往写死清单里加东西」过度敏感，
对「上游把动态入口摘掉」完全无感——敏感的方向和该敏感的方向正好相反。
"""
import sys

s = sys.stdin.read()
anchor = "export const addNodeMenuCommands"
assert anchor in s, "锚点未命中：没有找到 addNodeMenuCommands 导出"
s = s.replace(anchor, 'export const ART_CRITIQUE_NODE_TYPE = "ai-art-critique";\n' + anchor, 1)
sys.stdout.write(s)
