import sys
# 用例 19：上游把任务中心重新开放（/tasks 从重定向改回真页面并 import 回来）。
# 注入后 p_retired_task_skill_pages 的 (a)/(b) 子判据失效。
# 守的是手册里那句「/tasks、/skills 旧链接会静默跳回首页」——
# 一旦重新开放，那句话必须删掉，否则手册会让用户以为功能没了。
s = sys.stdin.read()
old = '''            {
                path: "/tasks",
                // 任务页暂不开放，保留路由以避免旧链接进入半成品界面。
                element: <Navigate to="/" replace />,
            },'''
assert old in s, "锚点未命中"
s = s.replace(old,
              '            { path: "/tasks", element: deferred(<TasksPage />) },', 1)
s = s.replace('import RouteErrorPage from "@/pages/route-error";',
              'import RouteErrorPage from "@/pages/route-error";\nimport TasksPage from "@/pages/tasks";', 1)
sys.stdout.write(s)
