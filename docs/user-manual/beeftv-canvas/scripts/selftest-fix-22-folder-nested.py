import sys
# 用例 22：上游给画布库文件夹加上嵌套（给 CanvasFolder 补一个 parentId 字段）。
# 注入后 p_canvas_folders_not_nested 的 (a) 子判据失效 → 整条应失效。
# 这条用例守的是手册「文件夹是一级分组，没有嵌套」**且**「不是界面的简化，
# 而是数据结构没有嵌套的位置」这个说法：只要类型里多出一个能指向父级的字段，
# 手册就必须回走改写成「现在可以嵌套了」。
s = sys.stdin.read()
old = """export type CanvasFolder = {
    id: string;
    name: string;
    createdAt: string;"""
assert old in s, "锚点未命中"
s = s.replace(old, """export type CanvasFolder = {
    id: string;
    name: string;
    parentId?: string;
    createdAt: string;""", 1)
sys.stdout.write(s)
