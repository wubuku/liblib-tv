import sys
s = sys.stdin.read()
s = s.replace("export const addNodeMenuCommands",
              'export const ART_CRITIQUE_NODE_TYPE = "ai-art-critique";\nexport const addNodeMenuCommands', 1)
sys.stdout.write(s)
