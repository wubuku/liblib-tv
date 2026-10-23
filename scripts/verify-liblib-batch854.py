#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 854 门禁：导演台**组模型的成员语义**。

## ★ 这批要守住的东西

★ 源站 chunk（`0fmehki05gkzw.js.js`）的**逐字实现**（机器提取，见
`raw/source-854-contract.json`，**17 个片段全部唯一命中**）：

```js
function N(e){return`${e.kind}:${e.id}`}
function O(e){let t=[],r=new Set,…(e.members??[]).forEach(n),
                (e.characterIds??[]).forEach(e=>n({kind:"character",id:e})),t}
function U(e){return O(e).filter(e=>"character"===e.kind).map(e=>e.id)}
function sg(e){return"character"===e||"prop"===e||"emptyObject"===e||"camera"===e}
expanded:!!F||!j.has(e.id)              // ★ 组默认展开
(F||!j.has(e.id))&&r.map(…{row:e,indent:!0…})   // ★ 成员是缩进子行
let r=t.shiftKey||t.metaKey||t.ctrlKey;          // ★ 树行加选：⇧／⌘／Ctrl
```

★ 源站实测（`raw/source-854-groupmembers.json`）：
- 源站的树是**平铺列表**（无节标题）
- ⌘+点击可以把**机位**和**角色**一起放进组 ⟹ 组**跨类别**
- 组员相对组行的缩进：**文本层 +16px**、**行元素层 0**（缩进做在行内）
- 未入组的行仍然平铺；⌘⇧D 解组后逐字回到基线

★ ★ **S3 是「同口径相减」**：源站与 clone 的树结构不同（源站平铺、clone 分节），
★   所以**绝对 x 不可比**；可比的是**缩进量**，而且必须**同粒度**相减：
★   「文本 x」对「文本 x」、「行元素 x」对「行元素 x」。
★   ★ 第一版探针量的是 clone 的**行元素**、源站量的是**文本 span** ⟹ 口径混了
★   ⟹ ⟹ 本门禁两边的 raw 里**都有这两层**，门禁按层分别相减。

## ★ 判据分工（★ 各条读的字段互不重叠 ⟹ 阴性每条只翻它自己那一条）

| 判据 | 读什么 | 阴性 |
| --- | --- | --- |
| S1 | clone 源码里的**结构**（符号存在性） | N1 |
| S2 | 契约里 **17 个片段** ＋ 关键逐字 | N2 |
| S3 | 源站／clone 的**缩进量**（两层各比各的） | N3／N12 |
| S4 | clone raw：**组的成员** ＝ 被选中的那些对象（id＋kind） | N4 |
| S5 | clone raw：**默认展开** | N5 |
| S6 | clone raw：**入组后成员不在类别分区** | N6 |
| S7 | clone raw：**解组逐字回到基线** | N7 |
| S8 | clone raw：**⇧ 加选**（第二个修饰键） | N8 |
| S9 | **源站** raw：跨类别成组 ＋ 缩进 ＋ 回到基线 | N9 |
| S10 | 文档层**两套独立实现**（store ＋ document）的运行结果 | N10 |
| S11 | **可达性** raw：根地址无参可达 ＋ 导演台可交互 | N11 |
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch854-2026-10-01"
RAW = BATCH / "raw"

SRC_STORE = ROOT / "src/store/directorStore.ts"
SRC_TREE = ROOT / "src/components/director/DirectorObjectTree.tsx"
SRC_DOC = ROOT / "src/lib/directorProjectDocument.ts"

NODE = pathlib.Path.home() / ".nvm/versions/node/v24.6.0/bin/node"

results = []


def record(name, ok, detail):
    results.append({"判据": name, "通过": bool(ok), "详情": detail})
    print(("  PASS  " if ok else "  FAIL  ") + name + " ｜ " + detail)


# ══════════════════════════════════════════════════════════════════════════
# ★ S10 的工具：把 TS 里的纯函数**抽出来**、去掉类型标注 ⟹ 变成可执行的 JS
# ══════════════════════════════════════════════════════════════════════════
def extract_js_function(source: str, name: str) -> str:
    """★ 把 TS 里的纯函数**整段抽出来**、剥掉类型标注 ⟹ 变成可执行的 JS。

    ★ 参数表是**整体**替换的（`group: {…}` / `group: DirectorCharacterGroup`
    ★ 两种形状都带类型 ⟹ ⟹ 逐个抠类型不可靠 ⟹ ⟹ 直接把参数表换成 `(group)`）。
    """
    sig = "export function %s(" % name
    i = source.find(sig)
    if i < 0:
        raise ValueError("★ 源码里找不到函数 %s" % name)
    # ★ 参数表：从 "(" 开始按括号深度找配对的 ")"
    p0 = i + len("export function %s" % name)
    depth = 0
    p1 = -1
    for k in range(p0, len(source)):
        if source[k] == "(":
            depth += 1
        elif source[k] == ")":
            depth -= 1
            if depth == 0:
                p1 = k
                break
    if p1 < 0:
        raise ValueError("★ 参数表括号不配平")
    j = source.find("{", p1)
    if j < 0:
        raise ValueError("★ 找不到函数体起点")
    depth = 0
    end = -1
    for k in range(j, len(source)):
        if source[k] == "{":
            depth += 1
        elif source[k] == "}":
            depth -= 1
            if depth == 0:
                end = k
                break
    if end < 0:
        raise ValueError("★ 函数体花括号不配平")
    head = source[i:end + 1]
    # ★ 参数表 ＋ 返回类型 ⟹ ⟹ 整段换成 `(group) {`
    head = re.sub(r"export function %s\([\s\S]*?\)\s*:\s*[^\{]+" % name,
                  "function %s(group) " % name, head, count=1)
    # ★ 函数体里的类型标注 ＋ 泛型实参
    head = re.sub(r":\s*DirectorGroupMemberDocumentV1\[\]", "", head)
    head = re.sub(r":\s*DirectorGroupMemberKindV1", "", head)
    head = re.sub(r":\s*DirectorSceneMemberRef\[\]", "", head)
    head = re.sub(r":\s*DirectorSceneMemberRef", "", head)
    head = re.sub(r":\s*DirectorObjectKind", "", head)
    head = re.sub(r":\s*string", "", head)
    head = re.sub(r"new Set<[^>]*>\(\)", "new Set()", head)
    return head


def run_node(script: str):
    tmp = RAW / ".gate854.tmp.js"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(script, encoding="utf-8")
    try:
        proc = subprocess.run([str(NODE), str(tmp)], capture_output=True,
                              text=True, timeout=60)
    finally:
        if tmp.exists():
            tmp.unlink()
    if proc.returncode != 0:
        return None, (proc.stderr or "")[-600:]
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1]), None
    except Exception as exc:  # noqa: BLE001
        return None, "解析 node 输出失败：%s / %r" % (exc, proc.stdout[-300:])


# ★ 四条用例：members 优先、characterIds 兜底、**去重**、members 为 null
DOC_CASES = [
    {"characterIds": ["c1"], "members": [{"kind": "camera", "id": "cam"}]},
    {"characterIds": ["c1", "c2"]},
    {"characterIds": ["c1"], "members": [{"kind": "character", "id": "c1"}]},
    {"characterIds": ["c1"], "members": None},
]
DOC_EXPECT = [
    [{"kind": "camera", "id": "cam"}, {"kind": "character", "id": "c1"}],
    [{"kind": "character", "id": "c1"}, {"kind": "character", "id": "c2"}],
    [{"kind": "character", "id": "c1"}],
    [{"kind": "character", "id": "c1"}],
]


def main() -> int:
    clone = json.loads((RAW / "clone-854-groupmembers.json").read_text(encoding="utf-8"))
    src = json.loads((RAW / "source-854-groupmembers.json").read_text(encoding="utf-8"))
    contract = json.loads((RAW / "source-854-contract.json").read_text(encoding="utf-8"))
    reach = json.loads((RAW / "clone-854-reachability.json").read_text(encoding="utf-8"))
    store_src = SRC_STORE.read_text(encoding="utf-8")
    tree_src = SRC_TREE.read_text(encoding="utf-8")
    doc_src = SRC_DOC.read_text(encoding="utf-8")
    frag = contract.get("片段", {})

    # ══ S1 结构（★ 只断言**符号存在**，不碰值 ⟹ ⟹ 值类判据能单独被变异）
    need_store = [
        "export interface DirectorSceneMemberRef",
        "export const DIRECTOR_GROUPABLE_KINDS",
        "export function resolveGroupMemberRefs",
        "resolveDirectorGroupMembers: (",
        "members?: DirectorSceneMemberRef[]",
    ]
    need_tree = [
        "data-director-group-member-id",
        "data-director-group-member-kind",
        "resolveGroupMemberRefs",
        "DIRECTOR_GROUPABLE_KINDS",
        "groupedMemberIds",
        "event.shiftKey || event.metaKey || event.ctrlKey",
    ]
    need_doc = [
        "export interface DirectorGroupMemberDocumentV1",
        "export type DirectorGroupMemberKindV1",
        "export function resolveDirectorGroupMembers",
        "expectGroupMembers",
    ]
    miss = ([k for k in need_store if k not in store_src]
            + [k for k in need_tree if k not in tree_src]
            + [k for k in need_doc if k not in doc_src])
    record(
        "S1 结构：成员类型／可分组类别／两个解析器／树侧接线都在",
        not miss,
        "缺=%s" % (miss,),
    )

    # ══ S2 契约（★ 17 个片段唯一命中 ＋ 关键逐字）
    checks = []
    for name in frag:
        checks.append(("片段唯一命中：%s" % name, frag[name].get("命中次数") == 1
                       or frag[name].get("命中数") == 1))
    f = {k: (v.get("原文") or "") for k, v in frag.items()}

    def find(sub):
        for k, v in f.items():
            if sub in k:
                return v
        return ""

    checks += [
        ("N(e) 是 kind:id 键", "return`${e.kind}:${e.id}`" in find("N(e)")),
        ("O(e) members 优先", "(e.members??[]).forEach" in find("O(e)")),
        ("O(e) characterIds 兜底成角色",
         '(e.characterIds??[]).forEach(e=>n({kind:"character",id:e}))' in find("O(e)")),
        ("O(e) 按 N(e) 去重", "r.has(n)||(r.add(n),t.push(e))" in find("O(e)")),
        ("U(e) 从 members 派生 characterIds",
         'O(e).filter(e=>"character"===e.kind)' in find("U(e)")),
        ("sg 含 camera", '"camera"===e' in find("sg(e)")),
        ("sg 含 prop", '"prop"===e' in find("sg(e)")),
        ("sg 含 character", '"character"===e' in find("sg(e)")),
        ("建组取 selectedSceneMembers（任意场景成员）",
         "e.selectedSceneMembers" in find("CREATE_CHARACTER_GROUP")),
        ("组默认展开", "expanded:!!F||!j.has(e.id)" in find("默认展开")),
        ("成员是缩进子行", "indent:!0" in find("缩进子行")),
        ("树行加选：⇧／⌘／Ctrl",
         "t.shiftKey||t.metaKey||t.ctrlKey" in find("树行的 onClick")),
        ("树行加选只对 sg 类别生效",
         "sg(e.category)?{additive:r" in find("树行的 onClick")),
        ("组名用 i18n(canvas:nodeTypeGroup)",
         '"canvas:nodeTypeGroup"' in find("组名 lT(e)")),
    ]
    bad = [n for n, v in checks if not v]
    record(
        "S2 契约：17 个片段唯一命中 ＋ 源站原文逐字对得上",
        not bad and len(frag) == 17,
        "片段数=%d 不符=%s" % (len(frag), bad),
    )

    # ══ S3 同口径几何：源站与 clone 的**缩进量**逐层相等
    s_rows = src.get("⑤⌘G后行") or []
    s_labels = src.get("⑤⌘G后标签") or []
    s_x = src.get("⑤⌘G后x") or []
    c_g = clone.get("④打组后") or {}
    c_groups = c_g.get("DOM组") or []
    c_members = c_g.get("DOM组员") or []
    s_group_i = next((i for i, lb in enumerate(s_labels) if lb not in
                       (src.get("①基线标签") or [])), None)
    s_member_i = [i for i in range(len(s_labels))
                  if s_group_i is not None and s_x[i] == s_x[s_group_i] + 16]
    s_text_delta = sorted({round(s_x[i] - s_x[s_group_i], 2) for i in s_member_i}) \
        if s_group_i is not None else []
    s_row_delta = sorted({round(s_rows[i].get("rowX") - s_rows[s_group_i].get("rowX"), 2)
                           for i in s_member_i}) \
        if s_group_i is not None and s_rows and s_rows[s_group_i].get("rowX") is not None \
        else []
    c_text_delta = sorted({round(m["文本x"] - c_groups[0]["文本x"], 2)
                            for m in c_members}) if c_groups and c_members else []
    c_row_delta = sorted({round(m["x"] - c_groups[0]["x"], 2)
                           for m in c_members}) if c_groups and c_members else []
    ok3 = (
        s_group_i is not None
        and len(s_member_i) == 2
        and s_text_delta == [16]
        and s_row_delta == [0]
        and c_text_delta == s_text_delta
        and c_row_delta == s_row_delta
    )
    record(
        "S3 几何：**同粒度**的缩进量，源站与 clone 逐层相等（文本 +16 ／ 行元素 0）",
        ok3,
        "源站文本Δ=%s 行元素Δ=%s ｜ clone文本Δ=%s 行元素Δ=%s"
        % (s_text_delta, s_row_delta, c_text_delta, c_row_delta),
    )

    # ══ S4 组的成员 ＝ 被选中的那些对象（id ＋ kind 逐个相等）
    base_rows = clone.get("①基线") or {}
    base_kind = {r["id"]: r["kind"] for r in (base_rows.get("DOM对象行") or [])}
    sel = (clone.get("③cmd加选角色后") or {}).get("store选中对象") or []
    store_members = c_g.get("store组员") or []
    dom_members = c_g.get("DOM组员") or []
    sel_map = {i: base_kind.get(i) for i in sel}
    store_map = {m["id"]: m["kind"] for m in store_members}
    dom_map = {m["id"]: m["kind"] for m in dom_members}
    # ★ 「组能装下非角色的东西」⟹ ⟹ 选中的成员里**不止一种类别**
    sel_kinds = sorted({k for k in sel_map.values() if k})
    ok4 = (
        len(sel) == 2
        and len(set(sel_map.values())) >= 2
        and store_map == sel_map
        and dom_map == sel_map
        and len(store_members) == 2
        and len(dom_members) == 2
    )
    record(
        "S4 clone：组的成员 ＝ 被选中的那两个对象（跨类别，id＋kind 逐个相等）",
        ok4,
        "选中=%s 组员(store)=%s 组员(DOM)=%s 选中类别=%s"
        % (sel_map, store_map, dom_map, sel_kinds),
    )

    # ══ S5 默认展开（★ 源站逐字 `expanded:!!F||!j.has(e.id)` ⟹ 默认展开）
    ok5 = (c_g.get("展开容器数") == 1 and len(dom_members) == 2)
    record(
        "S5 clone：组**默认展开**（成员子行直接可见）",
        ok5,
        "展开容器数=%s 成员行数=%s" % (c_g.get("展开容器数"), len(dom_members)),
    )

    # ══ S6 入组后成员**不再出现在类别分区**
    c_obj = c_g.get("DOM对象行") or []
    c_obj_ids = {r["id"] for r in c_obj}
    ok6 = (
        len(c_obj) == len(base_rows.get("DOM对象行") or []) - len(sel)
        and not (c_obj_ids & set(sel))
    )
    record(
        "S6 clone：入组后成员**从自己的类别分区里消失**",
        ok6,
        "剩余行数=%s（基线 %s − 成员 %s）剩余含成员=%s"
        % (len(c_obj), len(base_rows.get("DOM对象行") or []), len(sel),
           sorted(c_obj_ids & set(sel))),
    )

    # ══ S7 解组逐字回到基线
    u = clone.get("⑤解组后") or {}
    base_obj_rows = base_rows.get("DOM对象行") or []
    ok7 = (
        u.get("DOM组数") == 0
        and u.get("DOM组员数") == 0
        and u.get("DOM对象行数") == len(base_obj_rows)
        and sorted(r["id"] for r in (u.get("DOM对象行") or []))
        == sorted(r["id"] for r in base_obj_rows)
    )
    record(
        "S7 clone：解组后**逐字回到基线**（组没了 ＋ 对象行逐个回来）",
        ok7,
        "组数=%s 成员行=%s 对象行数=%s（基线 %s）"
        % (u.get("DOM组数"), u.get("DOM组员数"), u.get("DOM对象行数"),
           len(base_obj_rows)),
    )

    # ══ S8 ⇧ 加选（★ 第二个修饰键；源站逐字 ⇧／⌘／Ctrl 三者皆可）
    sh = clone.get("⑥shift加选道具后") or {}
    sh_sel = sh.get("store选中对象") or []
    sh_kinds = sorted({r["kind"] for r in (sh.get("DOM对象行") or [])
                       if r.get("selected") == "true"})
    ok8 = len(sh_sel) == 2 and len(sh_kinds) == 1
    record(
        "S8 clone：**⇧+点击**也能加选（第二个修饰键）",
        ok8,
        "选中=%s 类别=%s" % (sh_sel, sh_kinds),
    )

    # ══ S9 源站实测（★ 独立于 clone 各判据）
    s_labels_after = src.get("⑤⌘G后标签") or []
    s_kinds_after = src.get("⑤⌘G后类别") or []
    base_labels = src.get("①基线标签") or []
    new_labels = [x for x in s_labels_after if x not in base_labels]
    member_kinds = sorted({s_kinds_after[i] for i in s_member_i}) \
        if s_group_i is not None else []
    ungrouped_x = sorted({s_x[i] for i in range(len(s_x))
                          if s_group_i is not None and s_x[i] == s_x[s_group_i]})
    ok9 = (
        len(base_labels) == 3
        and src.get("①基线节标题") == []
        and len(new_labels) == 1
        and len(s_member_i) == 2
        and len(member_kinds) >= 2
        and "camera" in member_kinds
        and "character" in member_kinds
        and src.get("⑥回到基线") is True
        and src.get("⑦结束时标签") == base_labels
    )
    record(
        "S9 源站实测：⌘G 建出**跨类别**的组（机位＋角色）＋ 解组回到基线",
        ok9,
        "新行=%s 成员类别=%s 节标题=%s 回基线=%s 结束==基线=%s"
        % (new_labels, member_kinds, src.get("①基线节标题"),
           src.get("⑥回到基线"), src.get("⑦结束时标签") == base_labels),
    )

    # ══ S10 文档层：**两套独立实现**（store ＋ document）给出同一份成员列表
    try:
        doc_js = extract_js_function(doc_src, "resolveDirectorGroupMembers")
        store_js = extract_js_function(store_src, "resolveGroupMemberRefs")
    except Exception as exc:  # noqa: BLE001
        doc_js = store_js = None
        err10 = str(exc)
    if doc_js is None or store_js is None:
        record("S10 文档层：两套独立实现对同一输入给出同一份成员列表",
               False, "抽不出函数：%s" % err10)
    else:
        script = (
            doc_js + "\n" + store_js + "\n"
            + "const cases = " + json.dumps(DOC_CASES, ensure_ascii=False) + ";\n"
            + "const out = cases.map(c=>["
              "resolveDirectorGroupMembers(c), resolveGroupMemberRefs(c)]);\n"
            + "console.log(JSON.stringify(out));\n"
        )
        got, err = run_node(script)
        if got is None:
            record("S10 文档层：两套独立实现对同一输入给出同一份成员列表",
                   False, "node 跑不起来：%s" % err)
        else:
            mism = []
            for i, pair in enumerate(got):
                d, s = pair
                if d != s:
                    mism.append({"用例": i, "文档层": d, "store层": s,
                                 "问题": "两套实现不一致"})
                elif d != DOC_EXPECT[i]:
                    mism.append({"用例": i, "文档层": d, "期望": DOC_EXPECT[i],
                                 "问题": "与源站 O(e) 规则不符"})
            record(
                "S10 文档层：members 优先／characterIds 兜底／去重（两套实现交叉验证）",
                not mism and len(got) == len(DOC_CASES),
                "用例=%d 不符=%s" % (len(got), mism),
            )

    # ══ S11 可达性（★ 用户新目标：根目录「用户可达」）
    reachables = reach.get("③导演台可交互元素") or []
    ok11 = (
        reach.get("①根地址") == "http://localhost:4317/"
        and reach.get("①根页URL") == "http://localhost:4317/"
        and reach.get("②有脚本执行节点") is True
        and reach.get("②有打开导演台按钮") is True
        and reach.get("③导演台有树") is True
        and (reach.get("③导演台有对象树行") or 0) > 0
        and (reach.get("③导演台有rail") or 0) > 0
        and len(reachables) > 0
    )
    record(
        "S11 可达性：**从根地址无参**进入 ⟹ 打开导演台 ⟹ 树／对象行／rail／可交互元素都在",
        ok11,
        "根地址=%s 有入口=%s 树=%s 对象行=%s rail=%s 可交互=%d"
        % (reach.get("①根地址"), reach.get("②有打开导演台按钮"),
           reach.get("③导演台有树"), reach.get("③导演台有对象树行"),
           reach.get("③导演台有rail"), len(reachables)),
    )

    passed = sum(1 for r in results if r["通过"])
    total = len(results)
    report = {
        "批次": 854,
        "通过数": passed,
        "判据总数": total,
        # ★ 键名与 851／852／853 的门禁**一致**（「判据」）⟹ ⟹ 阴性脚本读同一套键
        "判据": results,
    }
    (BATCH / "runtime-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n== batch 854 门禁：%d/%d 通过 ==" % (passed, total))
    if passed != total:
        print("★ 有判据未通过")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
