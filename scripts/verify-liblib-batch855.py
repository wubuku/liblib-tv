#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 855 门禁：导演台**组 rig 的成员语义**（锚点／成员偏移／组轨道／解组）。

## ★ 这批要守住的东西

★ 源站 chunk（`0fmehki05gkzw.js.js`）的**逐字实现**（机器提取，见
`raw/source-855-contract.json`，**8 个片段全部唯一命中**）：

```js
function O(e){…(e.members??[]).forEach(n),(e.characterIds??[]).forEach(e=>n({kind:"character",id:e})),t}
function H(e,t){var r=O(e).map(t).filter(e=>!!e);if(0===r.length)return null;
  let n=r.reduce((e,t)=>({x:e.x+t.x,…}),{x:0,y:0,z:0});
  return{x:n.x/r.length,y:n.y/r.length,z:n.z/r.length}}          // ★ 锚点＝全部成员均值
function V(e,t,r){return O(e).reduce((e,n)=>{let a=r(n);
  return a&&(e[N(n)]={x:a.x-t.x,…}),e},{})}                       // ★ 成员偏移＝全部成员
let i=t.memberOffsets??V(r,a,f);O(r).forEach(t=>{let r=i[N(t)];    // ★ 遍历 O(r)＝全部成员
  r&&A.set(N(t),{position:{x:e.position.x+r.x,y:e.position.y+r.y,z:e.position.z+r.z},
                 yaw:n?.orientToPath?e.rotation.y:void 0,moving:v.has(e.id)})})
A.forEach((e,t)=>{…if("character"===o){…}if("prop"===o){…}if("emptyObject"===o){…}})
                                                    // ★★ 分支只有三个 ⟹ **没有 camera**
case"UNGROUP_CHARACTER_GROUP":{…animation:{...e.animation,
  groupTracks:e.animation.groupTracks.filter(e=>e.targetId!==t.id)},…lQ(n),selectedGroupId:null}
```

★ ★ **三个要害**（本门禁逐条钉住）：

1. **锚点／成员偏移都按「全部成员」算**（`O(e)`，任意类别）⟹ ⟹ 机位入组后，
   锚点与偏移**都算机位**。
2. **rig 的应用块没有 camera 分支** ⟹ ⟹ **机位入组后不会被组轨道带动**
   （源站里机位靠 `followTargetId` 跟组锚点，那是另一条路径）。
3. **rig 的位置是纯平移**：`position ＝ 组采样位置 ＋ 成员偏移` ⟹ ⟹
   偏移**不参与旋转／缩放**，成员保留自己的 rotation／scale。

## ★ 判据分工（★ 各条读的字段互不重叠 ⟹ 阴性每条只翻它自己那一条）

| 判据 | 读什么 | 阴性 |
| --- | --- | --- |
| S1 | clone 源码里的**结构**（符号／逐字） | N1 |
| S2 | 契约里 **8 个片段** ＋ 关键逐字 | N2 |
| S3 | clone raw：**组成员**含机位 ＋ `characterIds` 只是派生量 | N3 |
| S4 | clone raw：**组轨道 `memberOffsets` 键集 ＝ 全部成员** | N4 |
| S5 | clone raw：**rig 是纯平移**（同点前后对比，角色精确位移） | N5 |
| S6 | clone raw：**机位不被 rig 带动** | N6 |
| S7 | clone raw：**道具跟组动**（道具与角色位移相同） | N7 |
| S8 | clone raw：**解组**（组／轨道都没了、成员都在、选中态＝全部成员） | N8 |
| S9 | **独立实现**（把纯函数抽成 JS 跑 node）：锚点／偏移／rig 三条逐字 | N9 |
| S10 | 文档层：混合组的组轨道**能建出来**（`memberOffsets` 键集按全部成员） | N10 |
| S11 | 删除规划器：删成员后**机位成员的偏移不被误删** | N11 |
| S12 | 锁定守卫：组里有**被锁的机位** ⟹ 组关键帧被拒 | N12 |
| S13 | **可达性**：根地址无参可达 ＋ 导演台可交互 | N13 |
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH = ROOT / "docs/research/liblib-canvas-batch855-2026-10-01"
RAW = BATCH / "raw"

SRC_MATH = ROOT / "src/components/director/directorGroupMath.ts"
SRC_STORE = ROOT / "src/store/directorStore.ts"
SRC_DOC = ROOT / "src/lib/directorProjectDocument.ts"
SRC_PLANNER = ROOT / "src/lib/directorDeletePlanner.ts"

NODE = pathlib.Path.home() / ".nvm/versions/node/v24.6.0/bin/node"

results = []

# ★ 四条用例：members 优先、characterIds 兜底、**去重**、members 为 null
# ★ 期望值＝源站逐字 `function O(e){…}` 的规则（members 优先／characterIds 兜底／
# ★   按 `N(e)`＝`kind:id` 去重）
RESOLVER_CASES = 4
RESOLVER_EXPECT = [
    [{"kind": "camera", "id": "cam"}, {"kind": "character", "id": "c1"}],
    [{"kind": "character", "id": "c1"}, {"kind": "character", "id": "c2"}],
    [{"kind": "character", "id": "c1"}],
    [{"kind": "character", "id": "c1"}],
]


def record(name, ok, detail):
    results.append({"判据": name, "通过": bool(ok), "详情": detail})
    print(("  PASS  " if ok else "  FAIL  ") + name + " ｜ " + detail)


# ══════════════════════════════════════════════════════════════════════════
# ★ S9 的工具：把 TS 里的纯函数**抽出来**、去掉类型标注 ⟹ 变成可执行的 JS
# ══════════════════════════════════════════════════════════════════════════
def extract_js_function(source, name, params):
    """★ 把 TS 里的纯函数**整段抽出来**、剥掉类型标注 ⟹ 变成可执行的 JS。

    ★ 参数表是**整体**替换的（类型标注逐个抠不可靠 ⟹ ⟹ 直接换成给定参数名）。
    """
    sig = "export function %s(" % name
    exported = True
    i = source.find(sig)
    if i < 0:
        # ★ 模块内私有函数（没有 `export`）
        sig = "function %s(" % name
        exported = False
        i = source.find(sig)
    if i < 0:
        raise ValueError("★ 源码里找不到函数 %s" % name)
    p0 = i + len("export function %s" % name) if exported else i + len(sig) - 1
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
    head = re.sub(
        r"(export )?function %s\([\s\S]*?\)\s*:\s*[^\{]+\{" % name,
        "function %s(%s) {" % (name, ", ".join(params)),
        head,
        count=1,
    )
    # ★ 函数体里的类型标注 ＋ 泛型实参
    # ★ ★ **顺序要紧**：带 `[]` 的必须**先**剥 ⟹ ⟹ 否则
    #   `const out: DirectorGroupMemberRef[] = []` 会被剥成 `const out[] = []`
    #   ⟹ ⟹ 语法错（node 报 "[eval]:2"）。
    head = re.sub(r":\s*DirectorGroupMemberDocumentV1\[\]", "", head)
    head = re.sub(r":\s*DirectorGroupMemberKindV1", "", head)
    head = re.sub(r":\s*DirectorSceneMemberRef\[\]", "", head)
    head = re.sub(r":\s*DirectorSceneMemberRef", "", head)
    head = re.sub(r":\s*DirectorGroupMemberRef\[\]", "", head)
    head = re.sub(r":\s*DirectorGroupMemberRef", "", head)
    head = re.sub(r":\s*DirectorObjectKind", "", head)
    head = re.sub(r":\s*string", "", head)
    head = re.sub(r":\s*number", "", head)
    head = re.sub(r":\s*boolean", "", head)
    head = re.sub(r"new Set<[^>]*>\(\)", "new Set()", head)
    return head


def extract_js_const(source, name):
    """★ 把 `export const NAME: TYPE = [...]` 抽成 `const NAME = [...]`。"""
    m = re.search(r"export const %s\s*:\s*[^=]+=" % re.escape(name), source)
    if not m:
        raise ValueError("★ 源码里找不到常量 %s" % name)
    start = m.start()
    j = source.find("[", m.end() - 1)
    depth = 0
    end = -1
    for k in range(j, len(source)):
        if source[k] == "[":
            depth += 1
        elif source[k] == "]":
            depth -= 1
            if depth == 0:
                end = k
                break
    if end < 0:
        raise ValueError("★ 常量 %s 的数组不配平" % name)
    return "const %s = %s;" % (name, source[j:end + 1])


def run_node(script):
    proc = subprocess.run(
        [str(NODE), "-e", script],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError("★ node 失败：%s" % (proc.stderr or "")[:800])
    return json.loads(proc.stdout)


def main() -> int:
    # ── 读入 ──────────────────────────────────────────────────────────
    contract_path = RAW / "source-855-contract.json"
    clone_path = RAW / "clone-855-grouprig.json"
    for p in (contract_path, clone_path):
        if not p.exists():
            print("★★ 缺产物：%s" % p)
            return 2
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    clone = json.loads(clone_path.read_text(encoding="utf-8"))

    math_src = SRC_MATH.read_text(encoding="utf-8")
    store_src = SRC_STORE.read_text(encoding="utf-8")
    doc_src = SRC_DOC.read_text(encoding="utf-8")
    planner_src = SRC_PLANNER.read_text(encoding="utf-8")

    # ══════════════════════════════════════════════════════════════════
    # S1 源码结构
    # ══════════════════════════════════════════════════════════════════
    need = [
        (math_src, "export function resolveDirectorGroupMemberRefs(",
         "权威成员列表的唯一实现"),
        (math_src, "export function getDirectorGroupMembers(",
         "组全体成员（任意类别）"),
        (math_src, "export function applyDirectorGroupRig(",
         "源站逐字的组轨道 rig"),
        (math_src, "export const DIRECTOR_GROUP_RIG_DRIVEN_KINDS",
         "rig 驱动的类别白名单"),
        (math_src, '"character",\n  "prop",',
         "rig 驱动类别＝character＋prop（**不含 camera**）"),
        (store_src, "applyDirectorGroupRig(",
         "时间轴 rig 走新实现"),
        (store_src, "function directorGroupHasLockedMember(",
         "锁定守卫按全部成员"),
        # ★ S1 只断言「**解析器被用上了**」⟹ ⟹ 具体用法归 S10／S11
        #   （否则阴性 N10／N11 会**同时**翻红 S1 ⟹ ⟹ 「恰好一条」就不成立）
        (doc_src, "export function resolveDirectorGroupMembers(",
         "文档层的权威成员列表解析器"),
        (planner_src, "  resolveDirectorGroupMembers,",
         "删除规划器接上同一个解析器"),
    ]
    missing = [desc for src, needle, desc in need if needle not in src]
    # ★ rig 的驱动类别里**不能**出现 camera
    kinds_m = re.search(
        r"DIRECTOR_GROUP_RIG_DRIVEN_KINDS[^=]*=\s*\[([^\]]*)\]", math_src
    )
    kinds_txt = kinds_m.group(1) if kinds_m else ""
    no_camera = "camera" not in kinds_txt and "character" in kinds_txt \
        and "prop" in kinds_txt
    record("S1 源码结构：权威列表／rig／守卫／文档层／规划器",
           not missing and no_camera,
           "缺 %r ｜ rig 驱动类别＝%s（无 camera＝%s）"
           % (missing, kinds_txt.replace("\n", " ").strip(), no_camera))

    # ══════════════════════════════════════════════════════════════════
    # S2 契约 8 片段
    # ══════════════════════════════════════════════════════════════════
    frags = contract.get("片段", {})
    uniq = [k for k, v in frags.items() if v.get("命中数") == 1 and v.get("原文")]
    key_verbatim = [
        ("组的锚点 H(e,t)（全部成员位置的平均值）",
         "return{x:n.x/r.length,y:n.y/r.length,z:n.z/r.length}"),
        ("成员偏移 V(e,t,r)（键 ＝ N(n) ＝ kind:id）",
         "e[N(n)]={x:a.x-t.x,y:a.y-t.y,z:a.z-t.z}"),
        ("组轨道 rig（memberOffsets 缺失时现算 ＋ 遍历全部成员 O(r)）",
         "let i=t.memberOffsets??V(r,a,f);O(r).forEach(t=>{let r=i[N(t)];"),
        ("reducer case：UNGROUP_CHARACTER_GROUP（复原成员／相机重算／过滤轨道／选择态）",
         "groupTracks:e.animation.groupTracks.filter(e=>e.targetId!==t.id)"),
    ]
    verbatim_ok = all(
        needle in frags.get(name, {}).get("原文", "")
        for name, needle in key_verbatim
    )
    arb_ok = contract.get("★任意值类名自检", {}).get("通过") is True
    record("S2 契约：8 个片段唯一命中 ＋ 4 条关键逐字 ＋ 任意值自检",
           len(uniq) == 8 and verbatim_ok and arb_ok,
           "唯一命中 %d/8 ｜ 关键逐字 %s ｜ 任意值自检 %s"
           % (len(uniq), verbatim_ok, arb_ok))

    # ══════════════════════════════════════════════════════════════════
    # S3 组成员含机位
    # ══════════════════════════════════════════════════════════════════
    d4 = clone.get("④判定", {})
    members = d4.get("组成员", [])
    kinds = sorted({m["kind"] for m in members})
    # ★★ **自己重算**「characterIds 只是派生量」⟹ ⟹ 不采信探针写好的 flag
    #   （flag 是探针的**说法**；这里是门禁**从原始读数复算**的**事实**）
    derived_ids = [m["id"] for m in members if m["kind"] == "character"]
    derived_ok = d4.get("组characterIds") == derived_ids
    has_camera = any(m["kind"] == "camera" for m in members)
    record("S3 组成员含机位 ＋ characterIds 只是派生量",
           has_camera and derived_ok,
           "组成员类别 %s ｜ characterIds %s ＝ 派生量 %s（期望 %s）"
           % (kinds, d4.get("组characterIds"), derived_ok, derived_ids))

    # ══════════════════════════════════════════════════════════════════
    # S4 组轨道 memberOffsets 键集 ＝ 全部成员
    # ══════════════════════════════════════════════════════════════════
    d5 = clone.get("⑤判定", {})
    keys = d5.get("组轨道memberOffsets键", [])
    expect_keys = sorted(m["id"] for m in members)
    record("S4 组轨道 memberOffsets 键集 ＝ 全部成员（含机位）",
           d5.get("★期望键集＝全部成员") is True
           and d5.get("★键集含机位") is True
           and sorted(keys) == expect_keys,
           "键集 %s ｜ 期望 %s" % (sorted(keys), expect_keys))

    # ══════════════════════════════════════════════════════════════════
    # S5 rig 是纯平移（★ 同一时间点的前后对比）
    # ══════════════════════════════════════════════════════════════════
    ctrl = clone.get("★数据级受控检查：rig 纯平移", {})
    rows = ctrl.get("成员", [])
    driven = [r for r in rows if r.get("★rig驱动类别")]
    trans_ok = all(
        r["后位置"] == r["★纯平移期望位置"] for r in driven
    )
    rot_ok = all(r["前rotation"] == r["后rotation"] for r in driven)
    scale_ok = all(r["前scale"] == r["后scale"] for r in driven)
    record("S5 rig 是纯平移：位置＝关键帧位置＋成员偏移，rotation／scale 不变",
           bool(driven) and trans_ok and rot_ok and scale_ok,
           "被驱动成员 %d 个 ｜ 位置逐字 %s ｜ rotation 不变 %s ｜ scale 不变 %s"
           % (len(driven), trans_ok, rot_ok, scale_ok))

    # ══════════════════════════════════════════════════════════════════
    # S6 机位不被 rig 带动
    # ══════════════════════════════════════════════════════════════════
    cams = [r for r in rows if r.get("kind") == "camera"]
    cam_still = all(r["前位置"] == r["后位置"] for r in cams)
    cam_not_moved = all(
        r["后位置"] != r["★纯平移期望位置"] for r in cams
    )
    record("S6 机位入组后不被组轨道带动（源站 rig 无 camera 分支）",
           bool(cams) and cam_still and cam_not_moved,
           "机位 %d 个 ｜ 前后位置不变 %s ｜ 与纯平移期望不同 %s"
           % (len(cams), cam_still, cam_not_moved))

    # ══════════════════════════════════════════════════════════════════
    # S7 道具跟组动（道具与角色位移相同）
    # ══════════════════════════════════════════════════════════════════
    d10 = clone.get("⑩判定", {})
    shifts = d10.get("★成员x位移", {})
    prop_shifts = [v["位移x"] for v in shifts.values() if v.get("类别") == "prop"]
    char_shifts = [v["位移x"] for v in shifts.values() if v.get("类别") == "character"]
    same = (bool(prop_shifts) and bool(char_shifts)
            and prop_shifts[0] == char_shifts[0] and abs(prop_shifts[0] or 0) > 0)
    record("S7 道具也跟组动，且与角色的位移相同（纯平移）",
           same,
           "道具位移 %s ｜ 角色位移 %s" % (prop_shifts, char_shifts))

    # ══════════════════════════════════════════════════════════════════
    # S8 解组（对齐 UNGROUP_CHARACTER_GROUP）
    # ══════════════════════════════════════════════════════════════════
    d9 = clone.get("⑨判定", {})
    ungroup_ok = (
        d9.get("组数") == 0
        and d9.get("组轨道数") == 0
        and d9.get("★成员都还在") is True
        and d9.get("★选中态＝全部成员") is True
        and d9.get("★selectedGroupId为空") is True
    )
    record("S8 解组：组／组轨道都没了、成员都在、选中态＝全部成员、selectedGroupId 空",
           ungroup_ok,
           "组数 %s ｜ 组轨道数 %s ｜ 成员都在 %s ｜ 选中态＝全部成员 %s ｜ "
           "selectedGroupId 空 %s"
           % (d9.get("组数"), d9.get("组轨道数"), d9.get("★成员都还在"),
              d9.get("★选中态＝全部成员"), d9.get("★selectedGroupId为空")))

    # ══════════════════════════════════════════════════════════════════
    # S9 ★ 独立实现：把纯函数抽成 JS 跑 node
    # ══════════════════════════════════════════════════════════════════
    try:
        js = "\n".join([
            extract_js_function(
                math_src, "roundTuple", ["tuple"]
            ),
            extract_js_function(
                math_src, "resolveDirectorGroupMemberRefs", ["group"]
            ),
            extract_js_const(math_src, "DIRECTOR_GROUP_RIG_DRIVEN_KINDS"),
            extract_js_function(
                math_src, "getDirectorGroupMembers", ["objects", "group"]
            ),
            extract_js_function(
                math_src, "getDirectorGroupAnchorTransform", ["objects", "group"]
            ),
            extract_js_function(
                math_src, "getDirectorGroupMemberOffsets", ["objects", "group"]
            ),
            extract_js_function(
                math_src, "applyDirectorGroupRig",
                ["objects", "group", "sampledTransform", "memberOffsets"]
            ),
            # ★★ **三套独立实现**：store 侧 ＋ 组数学侧 ＋ 文档层侧
            #   ⟹ ⟹ 854 的门禁 S10 验的是「store 侧 vs 文档层侧」两套；
            #   ⟹ ⟹ 本批把**组数学侧**这一套也加进来 ⟹ ⟹ 三向交叉验证。
            extract_js_function(store_src, "resolveGroupMemberRefs", ["group"]),
            extract_js_function(
                doc_src, "resolveDirectorGroupMembers", ["group"]
            ),
            r"""
const objs = [
  { id: "c1", kind: "character", transform: {
      position: [0, 0, 0], rotation: [0, 10, 0], scale: [1, 1, 1] } },
  { id: "p1", kind: "prop", transform: {
      position: [4, 0, 0], rotation: [0, 20, 0], scale: [1, 1, 1] } },
  { id: "cam1", kind: "camera", transform: {
      position: [8, 0, 0], rotation: [0, 30, 0], scale: [1, 1, 1] } },
];
const group = { id: "g1", label: "G", characterIds: ["c1"],
                members: [{ kind: "character", id: "c1" },
                          { kind: "prop", id: "p1" },
                          { kind: "camera", id: "cam1" }] };
const members = getDirectorGroupMembers(objs, group);
const anchor = getDirectorGroupAnchorTransform(objs, group);
const offsets = getDirectorGroupMemberOffsets(objs, group);
const sampled = { position: [10, 0, 0], rotation: [0, 90, 0], scale: [2, 2, 2] };
const rig = applyDirectorGroupRig(objs, group, sampled, offsets);
const legacy = { characterIds: ["c1"] };
const CASES = [
  { characterIds: ["c1"], members: [{ kind: "camera", id: "cam" }] },
  { characterIds: ["c1", "c2"] },
  { characterIds: ["c1"], members: [{ kind: "character", id: "c1" }] },
  { characterIds: ["c1"], members: null },
];
console.log(JSON.stringify({
  memberIds: members.map((m) => m.id),
  anchorPosition: anchor.position,
  offsetKeys: Object.keys(offsets),
  offsets: offsets,
  sampled: sampled,
  originals: Object.fromEntries(objs.map((o) => [o.id, o.transform])),
  rigPositions: Object.fromEntries(rig.map((o) => [o.id, o.transform.position])),
  rigRotations: Object.fromEntries(rig.map((o) => [o.id, o.transform.rotation])),
  rigScales: Object.fromEntries(rig.map((o) => [o.id, o.transform.scale])),
  legacyMemberIds: getDirectorGroupMembers(objs, legacy).map((m) => m.id),
  legacyOffsetKeys: Object.keys(getDirectorGroupMemberOffsets(objs, legacy)),
  threeWay: CASES.map((c) => [
    resolveDirectorGroupMemberRefs(c),
    resolveGroupMemberRefs(c),
    resolveDirectorGroupMembers(c),
  ]),
}));
""",
        ])
        out = run_node(js)
        # ★★ 期望值**按源站逐字公式现算**（不手打常数）：
        #    位置 ＝ 采样位置 ＋ 成员偏移（只对 rig 驱动的类别）
        #    rotation／scale ＝ 成员自己的
        #    机位（源站 rig 没有 camera 分支）⟹ ⟹ 位置保持原样
        sampled = out["sampled"]["position"]
        driven_kinds = {"character", "prop"}
        member_kinds = {m["id"]: m["kind"] for m in [{"id": "c1", "kind": "character"},
                                                      {"id": "p1", "kind": "prop"},
                                                      {"id": "cam1", "kind": "camera"}]}
        expect_pos = {}
        expect_same = {}
        for oid, orig in out["originals"].items():
            kind = member_kinds[oid]
            if kind in driven_kinds and oid in out["offsets"]:
                off = out["offsets"][oid]
                expect_pos[oid] = [round(sampled[i] + off[i], 6) for i in range(3)]
            else:
                expect_pos[oid] = list(orig["position"])
            expect_same[oid] = {
                "rotation": list(orig["rotation"]),
                "scale": list(orig["scale"]),
            }
        pos_ok = all(
            out["rigPositions"][oid] == expect_pos[oid] for oid in expect_pos
        )
        rot_ok = all(
            out["rigRotations"][oid] == expect_same[oid]["rotation"]
            for oid in expect_same
        )
        scale_ok = all(
            out["rigScales"][oid] == expect_same[oid]["scale"]
            for oid in expect_same
        )
        # ★★ **三套实现必须一致**，且都符合源站 `O(e)` 的规则
        #   （members 优先／characterIds 兜底／按 `kind:id` 去重）
        three_ok = True
        three_detail = []
        for i, triple in enumerate(out.get("threeWay", [])):
            a, b, c = triple
            same = (a == b == c)
            rule_ok = (a == RESOLVER_EXPECT[i]) if i < len(RESOLVER_EXPECT) \
                else False
            three_detail.append({
                "用例": i, "组数学侧": a, "store侧": b, "文档层侧": c,
                "三套一致": same, "符合 O(e) 规则": rule_ok,
            })
            three_ok = three_ok and same and rule_ok
        s9_ok = (
            out["memberIds"] == ["c1", "p1", "cam1"]
            and out["anchorPosition"] == [4, 0, 0]          # 全部成员均值
            and sorted(out["offsetKeys"]) == ["c1", "cam1", "p1"]
            and pos_ok and rot_ok and scale_ok
            and out["rigPositions"]["cam1"] == [8, 0, 0]    # ★ 机位不动
            and out["legacyMemberIds"] == ["c1"]
            and out["legacyOffsetKeys"] == ["c1"]
            and three_ok
        )
        detail = ("成员 %s ｜ 锚点 %s ｜ 偏移键 %s ｜ rig 位置 %s ｜ 期望 %s ｜ "
                  "rotation 不变 %s ｜ scale 不变 %s ｜ 三套实现一致 %s ｜ "
                  "老组（只有 characterIds）成员 %s"
                  % (out["memberIds"], out["anchorPosition"],
                     sorted(out["offsetKeys"]), out["rigPositions"], expect_pos,
                     rot_ok, scale_ok, three_ok, out["legacyMemberIds"]))
    except Exception as exc:  # noqa: BLE001
        s9_ok = False
        detail = "★ 独立实现跑不起来：%s" % exc
    record("S9 独立实现（抽成 JS 跑 node）：锚点／偏移／rig 逐字",
           s9_ok, detail)

    # ══════════════════════════════════════════════════════════════════
    # S10 文档层：混合组的组轨道能建出来
    # ══════════════════════════════════════════════════════════════════
    s10_src = (
        "const memberIds = new Set(\n"
        "        resolveDirectorGroupMembers(group).map((member) => member.id),\n"
        "      );"
    )
    s10_ok = s10_src in doc_src
    s10_detail = "文档层键集按全部成员 %s" % s10_ok
    if s10_ok:
        # ★ 旧写法（只按角色）必须**不再出现**在同一处
        legacy = "const memberIds = new Set(group.characterIds);"
        s10_ok = legacy not in doc_src
        s10_detail += " ｜ 旧的「只按角色」写法已移除 %s" % (
            legacy not in doc_src)
    record("S10 文档层：组轨道 memberOffsets 键集按全部成员校验", s10_ok,
           s10_detail)

    # ══════════════════════════════════════════════════════════════════
    # S11 删除规划器：删成员后机位成员的偏移不被误删
    # ══════════════════════════════════════════════════════════════════
    s11_ok = (
        "resolveDirectorGroupMembers(group)\n"
        "          .map((member) => member.id)\n"
        "          .filter((memberId) => track.memberOffsets[memberId])"
    ) in planner_src
    s11_ok = s11_ok and "group.characterIds\n          .filter((memberId)" not in planner_src
    record("S11 删除规划器：轨道 closure 按全部成员保留偏移", s11_ok,
           "按权威成员列表过滤 %s" % s11_ok)

    # ══════════════════════════════════════════════════════════════════
    # S12 锁定守卫：组里有被锁的机位 ⟹ 组关键帧被拒
    # ══════════════════════════════════════════════════════════════════
    guard = "function directorGroupHasLockedMember("
    uses = len(re.findall(r"directorGroupHasLockedMember\(state, group\)", store_src))
    legacy_guard = len(re.findall(
        r"characterIds\.some\(\(objectId\) =>\s*directorObjectIsLocked", store_src
    ))
    s12_ok = guard in store_src and uses >= 3 and legacy_guard == 0
    record("S12 锁定守卫：组关键帧按全部成员判锁（旧的「只认角色」写法清零）",
           s12_ok,
           "辅助函数在 %s ｜ 用到 %d 处 ｜ 旧写法残留 %d 处"
           % (guard in store_src, uses, legacy_guard))

    # ══════════════════════════════════════════════════════════════════
    # S13 可达性：根地址无参可达
    # ══════════════════════════════════════════════════════════════════
    reach_path = RAW / "reachability-855.json"
    if reach_path.exists():
        reach = json.loads(reach_path.read_text(encoding="utf-8"))
        path_a = reach.get("路径A_导演台", {})
        path_b = reach.get("路径B_角色大编辑器", {})
        path_c = reach.get("路径C_资产管理", {})
        s13_ok = (
            reach.get("根页URL") == "http://localhost:4317/"
            and path_a.get("点到了") is True
            and path_a.get("有场景树") is True
            and int(path_a.get("可交互元素数") or 0) > 0
            and path_b.get("编辑器开了") is True
            and path_c.get("点到了") is True
        )
        s13_detail = (
            "根URL %s ｜ 导演台点到了 %s（可交互 %s 个）｜ 角色编辑器开了 %s "
            "｜ 资产管理点到了 %s"
            % (reach.get("根页URL"), path_a.get("点到了"),
               path_a.get("可交互元素数"), path_b.get("编辑器开了"),
               path_c.get("点到了"))
        )
    else:
        s13_ok = False
        s13_detail = "★ 缺 raw/reachability-855.json"
    record("S13 可达性：根地址无参可达 ＋ 导演台可交互", s13_ok, s13_detail)

    # ══════════════════════════════════════════════════════════════════
    # S14 ★ 选中态按**全部成员**（本批修掉的第 4 个真缺陷）
    #
    # ★ 源站逐字（机器提取见 `raw/source-855-contract.json` 同源 chunk）：
    #   `case"SELECT_CHARACTER_GROUP":{…let n=lB(O(r),e.characters,e.props,
    #    e.emptyObjects,e.cameras);if(0===n.length)return e;
    #    return{...e,...lQ(n),selectedGroupId:r.id}}`
    #   `function lQ(e,t){…return{selectedId:r?.id??null,…,
    #    selectedSceneMembers:e,selectedCharacterIds:e.flatMap(角色)}}`
    #   ⟹ ⟹ **建组时选中态 ＝ 全部成员**（`selectedSceneMembers`），
    #   而 `selectedCharacterIds` 只是**派生量**（只含角色）。
    # ★ ★ 854 之前 clone 有 6 处选中态**只认角色** ⟹ ⟹ 混合组在一次删除
    #   或一次历史恢复之后，选中态会**塌成只剩角色**（机位／道具被漏掉）。
    #
    # ★ ★ 与 S12（锁定守卫）的区别：S12 读的是 `directorGroupHasLockedMember`
    #   那个**辅助函数**；S14 读的是**选中态**那几处调用点 ⟹ ⟹ 两者互不重叠。
    #
    # ★ ★★ **「群众组」那条路径不在此列**：群众组的成员**本来就全是角色**
    #   （`characterIds: characters.map(...)` ⟹ ⟹ `members` 字段压根不存在），
    #   所以那里用 `[...group.characterIds]` 是**语义正确**的 ⟹ ⟹
    #   本判据只查「一般建组路径」与「选择／恢复路径」，不误伤 crowd。
    s14_old_shapes = [
        ("repairDirectorSelectionState", "selectedGroup.characterIds.filter("),
        ("projectDirectorDeleteState", "group.characterIds.filter("),
        ("selectTimelineTrack", "[...requestedGroup.characterIds]"),
    ]
    # ★★ **只看活代码** ⟹ ⟹ 注释里**提到**旧写法是正常的（那是在解释
    #   「854 之前是什么」）⟹ ⟹ 所以先把 `//` 注释行剔掉再查。
    store_code_only = "\n".join(
        ln for ln in store_src.splitlines() if not ln.lstrip().startswith("//")
    )
    s14_present = [
        name for name, needle in s14_old_shapes if needle in store_code_only
    ]
    # ★ 新的调用点：store 侧那份 `resolveGroupMemberRefs`
    resolve_calls = len(re.findall(r"resolveGroupMemberRefs\(", store_src))
    # ★ 建组路径必须按**权威成员列表**算（源站 `lQ(n)`）
    # ★ ★ 三处都要算 ⟹ ⟹ 所以断言**出现次数**（不是「至少有一处」）
    #   ⟹ ⟹ 否则「只改一处」这种退化会蒙混过关。
    create_group_hits = len(re.findall(
        r"selectedObjectIds: members\.map\(\(member\) => member\.id\)", store_src
    ))
    create_group_ok = (
        "const selectedObjectId = members[members.length - 1]?.id ?? null;" in store_src
        and create_group_hits == 3
    )
    s14_ok = not s14_present and resolve_calls >= 6 and create_group_ok
    record("S14 选中态：按全部成员算（旧写法清零 ＋ 建组按权威成员列表）",
           s14_ok,
           "旧写法残留 %s ｜ 新解析器调用点 %d 处 ｜ 建组按 members %d 处（期望 3）"
           % (s14_present or "无", resolve_calls, create_group_hits))

    # ══════════════════════════════════════════════════════════════════
    # S15 ★ **旧门禁的判据迁移**（本批引入的一条回归 ⟹ ⟹ 必须钉住）
    #
    # ★ ★ 背景：回归清单从 76 条扩到 77 条后，`87.mjs`（batch 87 的老门禁）
    #   **变红**了 ⟹ ⟹ 定点对照证明是**本批引入**（HEAD 上绿、工作副本红）
    #   ⟹ ⟹ 根因：它硬编码了 `selectedGroup.characterIds.filter(...)`
    #   —— 那是「组里只有角色」的**旧前提**（854 已把 `characterIds` 降为派生量）。
    # ★ ★ 处理：按仓库先例（batch 854 改 `45.py` 同一性质）**迁移判据**：
    #   正向改成「按权威成员列表过滤」＋ **加一条负向断言**保证旧写法清零
    #   （否则「两条都写」就能蒙混过关）。
    # ★ ★ 本条判据钉的是「**迁移这件事本身**」⟹ ⟹ 免得以后有人
    #   把老门禁改回旧写法（那样新语义就没人守了）。
    gate87 = ROOT / "scripts/verify-liblib-batch87.mjs"
    if gate87.exists():
        g87 = gate87.read_text(encoding="utf-8")
        g87_code = "\n".join(
            ln for ln in g87.splitlines() if not ln.lstrip().startswith("//")
        )
        # ★ ★ 查的是**正则字面量本身**（活代码行）⟹ ⟹ 不是符号名 ⟹ ⟹
        #   注释里提到 `resolveGroupMemberRefs` 也不算数 ⟹ ⟹
        #   否则「把判据改回旧写法、只在注释里留个名字」就能蒙混过关。
        s15_new_pat = "resolveGroupMemberRefs\\(selectedGroup\\)" in g87_code
        s15_neg_assert = "doesNotMatch" in g87_code
        s15_neg_watches_old = "selectedGroup\\.characterIds\\.filter" in g87_code
        s15_ok = s15_new_pat and s15_neg_assert and s15_neg_watches_old
        s15_detail = ("活代码里正向正则命中新写法 %s ｜ 有负向断言 %s ｜ "
                      "负向断言盯旧写法 %s"
                      % (s15_new_pat, s15_neg_assert, s15_neg_watches_old))
    else:
        s15_ok = False
        s15_detail = "★ 缺 scripts/verify-liblib-batch87.mjs"
    record("S15 旧门禁 87.mjs：判据已迁移（旧写法清零 ＋ 有负向断言）",
           s15_ok, s15_detail)

    # ── 汇总 ──────────────────────────────────────────────────────────
    out_path = BATCH / "runtime-audit.json"
    out_path.write_text(
        json.dumps({"批次": 855, "判据": results}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    passed = sum(1 for r in results if r["通过"])
    print("\n%d/%d 条通过" % (passed, len(results)))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
