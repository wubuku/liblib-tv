"use client";

import { useMemo, useState } from "react";
import {
  Box,
  Camera,
  ChevronDown,
  Eye,
  EyeOff,
  Search,
  User,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  useDirectorStore,
  type DirectorObject,
  type DirectorObjectKind,
} from "@/store/directorStore";

const groupDefinitions: Array<{
  kind: DirectorObjectKind;
  label: string;
}> = [
  { kind: "character", label: "角色" },
  { kind: "prop", label: "场景物体" },
  { kind: "camera", label: "摄像机" },
];

function ObjectIcon({ object }: { object: DirectorObject }) {
  if (object.kind === "camera") return <Camera size={14} />;
  if (object.kind === "character") return <User size={14} />;
  return <Box size={14} />;
}

export function DirectorObjectTree() {
  const objects = useDirectorStore((state) => state.objects);
  const selectedObjectId = useDirectorStore((state) => state.selectedObjectId);
  const selectObject = useDirectorStore((state) => state.selectObject);
  const updateObject = useDirectorStore((state) => state.updateObject);
  const [query, setQuery] = useState("");

  const groups = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("zh-CN");
    return groupDefinitions
      .map((group) => ({
        ...group,
        objects: objects.filter(
          (object) =>
            object.kind === group.kind &&
            (!normalized ||
              object.name.toLocaleLowerCase("zh-CN").includes(normalized)),
        ),
      }))
      .filter((group) => group.objects.length > 0);
  }, [objects, query]);

  return (
    <section data-director-tree className="flex h-full min-h-0 flex-col bg-[#191919]">
      <div className="flex h-12 shrink-0 items-center border-b border-white/[0.07] px-3">
        <label className="flex h-8 min-w-0 flex-1 items-center gap-2 rounded border border-white/[0.08] bg-[#222] px-2 text-[#777] focus-within:border-[#09caf5]/60">
          <Search size={14} />
          <input
            aria-label="搜索场景内容"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="搜索场景内容"
            className="min-w-0 flex-1 bg-transparent text-xs text-[#dedede] outline-none placeholder:text-[#666]"
          />
        </label>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto py-2">
        {groups.length === 0 ? (
          <div className="px-4 py-10 text-center text-xs text-[#686868]">未搜索到内容</div>
        ) : (
          groups.map((group) => (
            <section key={group.kind} aria-label={`${group.label}分组`} className="mb-3">
              <h2 className="flex h-7 items-center gap-1 px-3 text-[11px] text-[#777]">
                <ChevronDown size={12} />
                <span>{group.label}</span>
                <span className="ml-auto tabular-nums">{group.objects.length}</span>
              </h2>
              <div role="tree" aria-label={`${group.label}对象`}>
                {group.objects.map((object) => {
                  const selected = selectedObjectId === object.id;
                  return (
                    <div
                      key={object.id}
                      role="treeitem"
                      aria-selected={selected}
                      data-director-object-id={object.id}
                      data-director-object-kind={object.kind}
                      data-director-object-selected={selected}
                      data-director-object-visible={object.visible}
                      onClick={() => selectObject(object.id)}
                      className={cn(
                        "group flex h-8 cursor-default items-center gap-2 border-l-2 px-2 text-xs",
                        selected
                          ? "border-[#09caf5] bg-[#09caf5]/10 text-white"
                          : "border-transparent text-[#b8b8b8] hover:bg-white/[0.04]",
                      )}
                    >
                      <span className={selected ? "text-[#5ddcff]" : "text-[#777]"}>
                        <ObjectIcon object={object} />
                      </span>
                      <span className="min-w-0 flex-1 truncate">{object.name}</span>
                      <button
                        type="button"
                        aria-label={object.visible ? `隐藏${object.name}` : `显示${object.name}`}
                        title={object.visible ? "隐藏" : "显示"}
                        onClick={(event) => {
                          event.stopPropagation();
                          updateObject(object.id, { visible: !object.visible });
                        }}
                        className={cn(
                          "flex h-6 w-6 shrink-0 items-center justify-center text-[#686868] hover:text-white",
                          !object.visible && "text-[#4f4f4f]",
                        )}
                      >
                        {object.visible ? <Eye size={13} /> : <EyeOff size={13} />}
                      </button>
                    </div>
                  );
                })}
              </div>
            </section>
          ))
        )}
      </div>
    </section>
  );
}
