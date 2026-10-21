#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 833 **共享读数器**：源站与 clone 用**同一条规则**读机位属性。

★ 为什么需要共享读数器（这是本批要修的第二个坑）：
  clone 的 Inspector 与源站的右栏**结构不同** ⟹
  - 源站：字段标题是 `DIV`，FOV 数值框**没有 type 属性**（⟹ `input[type=number]` 选不到它）；
  - clone：字段标题是 `LEGEND`，FOV 数值框**有 type="number"**，而且**多一行「缩放」**。
  ⟹ ★ 所以「把所有 number 输入按顺序拼起来再切片」这种读法**两边索引不同** ⟹ 不可比。
  ⟹ ★ 正确做法：**按字段标题分组** —— 标题变了，分组也跟着变，两边就永远可比。

★ ★ 规则 R（`vec` / `fov` 两步）：
  R1. 标题候选 = 「自身有文本（childElementCount===0）且可见」的 div/span/legend/label/p/…；
  R2. 向量字段（位置 / 旋转 / 注视坐标）：
      取**标题文字完全相等**的候选 ⟹ 其下方 **60px 内**的所有可见 `input[type=number]`
      ⟹ 取**最小 y**的那一组（= 同一行的三个数）⟹ **按 x 升序** ⟹ 得到 [X, Y, Z]；
      ⟹ ★ 若候选标题有多个且都带出 3 个数 ⟹ 视为**歧义**（必须报出来，不能悄悄取一个）。
  R3. FOV：取标题文字**以 `(FOV)` 结尾**的候选（源站与 clone 都是「视野角度 (FOV)」）
      ⟹ 其下方 60px 内的第一个可见 `input[type=range]` ⟹ 它的 value 就是 FOV。

★ 为什么 FOV 读 range 而不是 number：
  源站的 FOV 数值框**没有 type 属性** ⟹ `input[type=number]` 选不到 ⟹ 两边都得读 range。

★ 离线版（`group_capture`）是同一规则的 Python 镜像 ⟹ 用来把**已经采到的源站活体读数**
  （probes/presets833.py 的产物）重新分组 ⟹ 于是「源站活体采集」与「clone 活体采集」
  两边用的是同一条规则 ⟹ 可比。
"""
from __future__ import annotations

# ---------------------------------------------------------------- JS 活体读数器
READ_PROPS_JS = r"""()=>{
  const vis=(e)=>{const r=e.getBoundingClientRect();
    return r.width>0&&r.height>0&&getComputedStyle(e).display!=='none';};
  const geom=(e)=>{const r=e.getBoundingClientRect();
    return {value:(e.value!==undefined?String(e.value):''),
            x:Math.round(r.x),y:Math.round(r.y),
            w:Math.round(r.width),h:Math.round(r.height)};};
  const nums=Array.from(document.querySelectorAll('input[type="number"]')).filter(vis).map(geom);
  const ranges=Array.from(document.querySelectorAll('input[type="range"]')).filter(vis).map(geom);
  const cands=Array.from(document.querySelectorAll(
      'div,span,legend,label,p,strong,em,h1,h2,h3,h4,h5,h6'))
    .filter(e=>vis(e)&&e.childElementCount===0)
    .map(e=>({t:(e.textContent||'').trim(),y:Math.round(e.getBoundingClientRect().y)}));
  const vec=(title)=>{
    const groups=[];
    for(const c of cands.filter(c=>c.t===title)){
      const below=nums.filter(n=>n.y>c.y&&n.y-c.y<=60);
      if(!below.length) continue;
      const minY=Math.min(...below.map(n=>n.y));
      const g=below.filter(n=>Math.abs(n.y-minY)<=2).sort((a,b)=>a.x-b.x);
      groups.push({titleY:c.y,count:g.length,values:g.map(n=>n.value)});
    }
    return groups;
  };
  const fov=[];
  for(const c of cands.filter(c=>/FOV\)$/.test(c.t))){
    const below=ranges.filter(n=>n.y>c.y&&n.y-c.y<=60);
    if(below.length) fov.push({title:c.t,titleY:c.y,value:below[0].value});
  }
  return {nums:nums,ranges:ranges,candidates:cands,
          vec:{position:vec('位置'),rotation:vec('旋转'),target:vec('注视坐标')},
          fov:fov};
}"""

# 规则 R2/R3 的常量
VEC_TITLES = ("位置", "旋转", "注视坐标")
NEAR_PX = 60
SAME_ROW_PX = 2


def _num(value: str):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _vec_from(labels, nums, title):
    """规则 R2 的 Python 镜像。labels: [{t,y}]；nums: [{value,box}]。"""
    groups = []
    for cand in labels:
        if cand.get("t") != title:
            continue
        cy = cand["y"]
        below = []
        for n in nums:
            by = n["box"]["y"]
            if by > cy and by - cy <= NEAR_PX:
                below.append(n)
        if not below:
            continue
        min_y = min(n["box"]["y"] for n in below)
        row = [n for n in below if abs(n["box"]["y"] - min_y) <= SAME_ROW_PX]
        row.sort(key=lambda n: n["box"]["x"])
        groups.append({
            "titleY": cy,
            "count": len(row),
            "values": [n["value"] for n in row],
        })
    return groups


def group_capture(props: dict) -> dict:
    """把 probes/presets833.py 采到的源站活体读数按规则 R 重新分组。

    props 形如 {"labels":[{"t","y"}], "nums":[{"value","box"}], "fov":"50"}。
    ★ FOV：源站探针已经把**FOV 标题下方 60px 内的第一个 range** 读成 props["fov"]
      ⟹ 这里直接沿用 ⟹ 与 JS 规则 R3 同义（源站属性页只有 FOV 一个 range）。
    """
    labels = props.get("labels") or []
    nums = props.get("nums") or []
    out = {}
    for key, title in (("position", "位置"), ("rotation", "旋转"),
                       ("target", "注视坐标")):
        out[key] = _vec_from(labels, nums, title)
    out["fov"] = props.get("fov")
    return out


def pick_vec(groups, expect=3):
    """从分组里挑出**唯一**的、恰好 3 个数的那一组；不唯一 ⟹ 抛错（不悄悄取一个）。"""
    good = [g for g in groups if g["count"] == expect]
    if len(good) != 1:
        raise ValueError("字段分组歧义：期望恰好 1 组 %d 个数，实得 %d 组 %r"
                         % (expect, len(good), groups))
    return [_num(v) for v in good[0]["values"]]


def pick_fov(fov_groups):
    """fov_groups: JS 侧 [{"title","titleY","value"}] 或 [None] ⟹ 取唯一那一个。"""
    good = [g for g in fov_groups if g and g.get("value") not in (None, "")]
    if len(good) != 1:
        raise ValueError("FOV 分组歧义：期望恰好 1 组，实得 %d 组 %r"
                         % (len(good), fov_groups))
    return _num(good[0]["value"])


def semantics_from_capture(props: dict) -> dict:
    """源站活体采集 → 规则 R 分组 → {位置,旋转,注视,FOV}（数值型）。"""
    g = group_capture(props)
    return {
        "位置": pick_vec(g["position"]),
        "旋转": pick_vec(g["rotation"]),
        "注视": pick_vec(g["target"]),
        "FOV": _num(g["fov"]),
    }


def semantics_from_js(js: dict) -> dict:
    """clone/source 活体 JS 读数 → {位置,旋转,注视,FOV}（数值型）。"""
    return {
        "位置": pick_vec(js["vec"]["position"]),
        "旋转": pick_vec(js["vec"]["rotation"]),
        "注视": pick_vec(js["vec"]["target"]),
        "FOV": pick_fov(js["fov"]),
    }
