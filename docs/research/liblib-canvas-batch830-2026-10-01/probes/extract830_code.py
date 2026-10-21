#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从源站导演台组件 chunk 里抽取**可静态核验的锚点**，写成入库证据。

★ 为什么要有这个文件：batch 830 的核心结论（撤销是 ⌘Z、撤销栈覆盖 UPDATE_CAMERA、
  WASDQE 是裸键组）全部来自**读源站代码**，而不是靠盲测。
  ⟹ 把「原文片段 + 它在 chunk 里的偏移」存下来 ⟹ 门禁就能静态核验这些结论
  ⟹ 而不是只核验我自己的转述。
"""
import json
import pathlib

CHUNK = pathlib.Path("/tmp/liblib_srcjs2/0fmehki05gkzw.js.js")
OUT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv/docs/research/"
                    "liblib-canvas-batch830-2026-10-01/raw/"
                    "source-830-shortcut-code.json")

ANCHORS = {
    "面板_撤销行": '{label:e("canvas:directorShortcutUndo"),keys:[{id:"undo-command",icon:"command"},{id:"undo-key",label:"Z"}]}',
    "面板_打组行": '{label:e("canvas:directorShortcutGroup"),keys:[{id:"group-command",icon:"command"},{id:"group-key",label:"G"}]}',
    "面板_解组行": '{label:e("canvas:directorShortcutUngroup"),keys:[{id:"ungroup-command",icon:"command"},{id:"ungroup-shift",label:"⇧"},{id:"ungroup-key",label:"D"}]}',
    "面板_俯视行": '{label:e("canvas:directorShortcutTopView"),keys:[{id:"top-view",label:"T"}]}',
    "面板_重置行": '{label:e("canvas:directorShortcutResetView"),keys:[{id:"reset-view",label:"H"}]}',
    "面板_移动当前行": '{label:e("canvas:directorShortcutMoveCurrentView"),keys:[{id:"move-current-view",label:"WASDQE"}]}',
    "键盘集合_hY": 'hY=new Set(["escape","enter","v","r","f","h","x","t","y","c","d","g","delete","backspace","z"])',
    "键盘集合_hX": 'hX=new Set(["w","a","s","d","q","e"])',
    "撤销键条件": '("z"!==n||e.ctrlKey||e.metaKey)',
    "打组键条件": '("g"!==n||e.ctrlKey||e.metaKey)',
    "解组键条件": '("d"!==n||e.shiftKey&&(e.ctrlKey||e.metaKey))',
    "重置键条件": '("h"!==n||!e.ctrlKey&&!e.metaKey&&!e.altKey)',
    "撤销分支": 'else if("z"===n)e.shiftKey?nu():nd();',
    "可撤销动作集_lX": 'lX=new Set(["ADD_CHARACTER","ADD_CHARACTERS","ADD_EMPTY_OBJECT","ADD_CAMERA","ADD_PROP","DUPLICATE_CHARACTER","DUPLICATE_CAMERA","DUPLICATE_PROP","CREATE_CHARACTER_GROUP","UNGROUP_CHARACTER_GROUP","REMOVE","REMOVE_SCENE_MEMBERS","REMOVE_CHARACTERS","UPDATE_CHARACTER","UPDATE_CHARACTERS","UPDATE_CAMERA","UPDATE_EMPTY_OBJECT","UPDATE_PROP","ADD_ANIM_TRACK","REMOVE_ANIM_TRACK","UPDATE_ANIM_TRACK","UPSERT_KEYFRAME","REMOVE_KEYFRAME","UPDATE_TIMELINE","REMOVE_MOTION_PATH","UPDATE_ENV","IMPORT","CLEAR"])',
    "撤销栈_取栈顶": 'if("UNDO"===t.type){if(0===(e=lZ(e)).past.length)return e;let t=e.past.at(-1);return t?{past:e.past.slice(0,-1),present:t,future:[e.present,...e.future],transientPast:null}:e}',
    "撤销栈_容量": 'past:[...a.past.slice(-49),a.present]',
    "瞬时提交": 'if("COMMIT_TRANSIENT"===t.type)return lZ(e);',
    "瞬时记账": 'n=r&&"transient"===("history"in t&&t.history?t.history:"record")',
    "监听注册_捕获阶段": 'window.addEventListener("keydown",e,!0)',
    "可编辑早退": "function h5(e){if(!(e instanceof Element))return!1;let t=e.closest('input, textarea, select, [contenteditable=\"true\"]');",
    "range_豁免可编辑": '["button","checkbox","color","file","hidden","image","radio","range","reset","submit"]',
    "裸键组分支": 'if(hX.has(r)&&!(e.ctrlKey||e.metaKey)){e.preventDefault(),oo(r,e);return}',
    "俯视视角实现": 'else if("t"===n)n0.setEditorCameraPose(iK("top"));',
    "重置视角实现": 'else if("h"===n)eJ("director"),n0.setEditorCameraPose(iK("def',
}


def main():
    s = CHUNK.read_text(encoding="utf-8", errors="replace")
    anchors = {}
    missing = []
    for name, needle in ANCHORS.items():
        i = s.find(needle)
        if i < 0:
            missing.append(name)
            anchors[name] = {"found": False}
            continue
        anchors[name] = {"found": True, "offset": i, "text": needle}
    out = {
        "来源": "源站导演台组件 chunk 0fmehki05gkzw.js.js（2026-10-21 抓取）",
        "抓取方式": ("开台时录下所有 .js 请求 ⟹ 把既有缓存 /tmp/liblib_srcjs/ 里没有的 "
                 "存到 /tmp/liblib_srcjs2/（159 个）⟹ 导演台组件代码只在新缓存里"),
        "为什么必须读代码": (
            "缓存的 161 个 chunk 里，连「导演视角」按钮的 i18n 键"
            "（directorViewModeDirector）都只出现在 i18n 字典 chunk ⟹ "
            "导演台组件代码根本不在旧缓存 ⟹ 盲按快捷键测不出任何东西"),
        "chunk_bytes": len(s),
        "锚点": anchors,
        "未命中": missing,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("落盘：", OUT)
    print("锚点 %d/%d 命中；未命中：%s" % (len(ANCHORS) if False else
                                          sum(1 for v in anchors.values() if v["found"]),
                                          len(anchors), missing))


if __name__ == "__main__":
    main()
