import sys
# 用例 15：上游给导演台场景补上后端同步。
# 注入后 p_director_scenes_not_synced 应失效。
s = sys.stdin.read()
old = "        updateProject(projectId, { directorScenes: upsertDirectorSceneById(currentDirectorScenes(projectId, directorScenes), scene) });"
assert old in s, "锚点未命中"
s = s.replace(old,
              "        updateProject(projectId, { directorScenes: upsertDirectorSceneById(currentDirectorScenes(projectId, directorScenes), scene) });\n"
              "        void scheduleLocalCanvasBackendSync(projectId);", 1)
sys.stdout.write(s)
