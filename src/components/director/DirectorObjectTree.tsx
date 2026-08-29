"use client";

import { useMemo, useState } from "react";
import {
  Box,
  Camera,
  ChevronDown,
  ChevronRight,
  Eye,
  EyeOff,
  Lock,
  Search,
  Trash2,
  Unlock,
  User,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  useDirectorStore,
  type DirectorCharacterGroup,
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

function GroupIcon() {
  return <Users size={14} aria-hidden="true" />;
}

function GroupRow({
  group,
  objects,
  query,
}: {
  group: DirectorCharacterGroup;
  objects: DirectorObject[];
  query: string;
}) {
  const selectedGroupId = useDirectorStore((state) => state.selectedGroupId);
  const selectGroup = useDirectorStore((state) => state.selectGroup);
  const deleteDirectorEntity = useDirectorStore(
    (state) => state.deleteDirectorEntity,
  );
  const [expanded, setExpanded] = useState(false);
  const normalized = query.trim().toLocaleLowerCase("zh-CN");
  const members = group.characterIds
    .map((id) => objects.find((object) => object.id === id))
    .filter((object): object is DirectorObject => Boolean(object));
  const matchingMembers = normalized
    ? members.filter((member) =>
        member.name.toLocaleLowerCase("zh-CN").includes(normalized),
      )
    : members;
  if (
    normalized &&
    !group.label.toLocaleLowerCase("zh-CN").includes(normalized) &&
    matchingMembers.length === 0
  ) {
    return null;
  }
  const selected = selectedGroupId === group.id;

  return (
    <div data-director-group-id={group.id} data-director-group-selected={selected}>
      <div
        role="treeitem"
        aria-selected={selected}
        onClick={() => selectGroup(group.id)}
        className={cn(
          "group flex h-8 cursor-default items-center gap-2 border-l-2 px-2 text-xs",
          selected
            ? "border-[#09caf5] bg-[#09caf5]/10 text-white"
            : "border-transparent text-[#b8b8b8] hover:bg-white/[0.04]",
        )}
      >
        <button
          type="button"
          data-director-group-action="toggle"
          aria-label={expanded ? `收起${group.label}` : `展开${group.label}`}
          onClick={(event) => {
            event.stopPropagation();
            setExpanded((value) => !value);
          }}
          className="flex h-6 w-6 shrink-0 items-center justify-center text-[#777] hover:text-white"
        >
          {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        </button>
        <span className={selected ? "text-[#5ddcff]" : "text-[#777]"}>
          <GroupIcon />
        </span>
        <span className="min-w-0 flex-1 truncate">{group.label}</span>
        <span className="text-[10px] tabular-nums text-[#686868]">
          {members.length}
        </span>
        <button
          type="button"
          data-director-delete-group={group.id}
          aria-label={`删除分组${group.label}`}
          title="删除分组并保留成员"
          onClick={(event) => {
            event.stopPropagation();
            deleteDirectorEntity({
              kind: "DELETE_GROUP",
              groupId: group.id,
              memberPolicy: "UNGROUP",
            });
          }}
          className="flex h-6 w-6 shrink-0 items-center justify-center text-[#686868] hover:text-[#f08d8d]"
        >
          <Trash2 size={12} />
        </button>
      </div>
      {expanded ? (
        <div
          data-director-group-expanded="true"
          className="border-l border-white/[0.06] pl-4"
          role="group"
          aria-label={`${group.label}成员`}
        >
          {(normalized ? matchingMembers : members).map((member) => (
            <button
              key={member.id}
              type="button"
              data-director-group-member-id={member.id}
              onClick={() => selectGroup(group.id)}
              className={cn(
                "flex h-7 w-full items-center gap-2 px-2 text-left text-[11px]",
                selected
                  ? "text-[#d9f8ff]"
                  : "text-[#777] hover:bg-white/[0.04] hover:text-white",
              )}
            >
              <span className="text-[#626262]"><User size={12} /></span>
              <span className="min-w-0 flex-1 truncate">{member.name}</span>
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function DirectorObjectTree() {
  const objects = useDirectorStore((state) => state.objects);
  const groups = useDirectorStore((state) => state.groups);
  const selectedObjectId = useDirectorStore((state) => state.selectedObjectId);
  const selectedObjectIds = useDirectorStore((state) => state.selectedObjectIds);
  const selectedGroupId = useDirectorStore((state) => state.selectedGroupId);
  const selectObject = useDirectorStore((state) => state.selectObject);
  const toggleObjectSelection = useDirectorStore(
    (state) => state.toggleObjectSelection,
  );
  const updateObject = useDirectorStore((state) => state.updateObject);
  const toggleObjectLocked = useDirectorStore(
    (state) => state.toggleObjectLocked,
  );
  const deleteDirectorEntity = useDirectorStore(
    (state) => state.deleteDirectorEntity,
  );
  const groupSelectedCharacters = useDirectorStore(
    (state) => state.groupSelectedCharacters,
  );
  const ungroupSelectedCharacters = useDirectorStore(
    (state) => state.ungroupSelectedCharacters,
  );
  const [query, setQuery] = useState("");

  const groupedCharacterIds = useMemo(
    () => new Set(groups.flatMap((group) => group.characterIds)),
    [groups],
  );
  const visibleGroups = useMemo(
    () =>
      groups.filter((group) => {
        const normalized = query.trim().toLocaleLowerCase("zh-CN");
        return (
          !normalized ||
          group.label.toLocaleLowerCase("zh-CN").includes(normalized) ||
          group.characterIds.some((id) =>
            objects
              .find((object) => object.id === id)
              ?.name.toLocaleLowerCase("zh-CN")
              .includes(normalized),
          )
        );
      }),
    [groups, objects, query],
  );
  const normalized = query.trim().toLocaleLowerCase("zh-CN");
  const objectGroups = useMemo(
    () =>
      groupDefinitions
        .map((group) => ({
          ...group,
          objects: objects.filter(
            (object) =>
              object.kind === group.kind &&
              (group.kind !== "character" || !groupedCharacterIds.has(object.id)) &&
              (!normalized ||
                object.name.toLocaleLowerCase("zh-CN").includes(normalized)),
          ),
        }))
        .filter((group) => group.objects.length > 0),
    [groupedCharacterIds, normalized, objects],
  );
  const selectedCharacters = selectedObjectIds.filter((id) =>
    objects.some((object) => object.id === id && object.kind === "character"),
  );
  const canGroup = selectedCharacters.length >= 2 && selectedGroupId === null;

  return (
    <section data-director-tree className="flex h-full min-h-0 flex-col bg-[#191919]">
      <div className="flex h-12 shrink-0 items-center gap-1 border-b border-white/[0.07] px-3">
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
      <div className="flex h-9 shrink-0 items-center gap-1 border-b border-white/[0.06] px-2">
        <button
          type="button"
          data-director-group-action="group"
          disabled={!canGroup}
          onClick={groupSelectedCharacters}
          className="flex h-7 flex-1 items-center justify-center gap-1 rounded text-[10px] text-[#999] hover:bg-white/[0.06] hover:text-white disabled:text-[#4d4d4d]"
        >
          <Users size={12} /> 打组
        </button>
        <button
          type="button"
          data-director-group-action="ungroup"
          disabled={!selectedGroupId}
          onClick={ungroupSelectedCharacters}
          className="flex h-7 flex-1 items-center justify-center gap-1 rounded text-[10px] text-[#999] hover:bg-white/[0.06] hover:text-white disabled:text-[#4d4d4d]"
        >
          <ChevronRight size={12} /> 解组
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto py-2">
        {visibleGroups.length > 0 ? (
          <section className="mb-3" aria-label="群众分组">
            <h2 className="flex h-7 items-center gap-1 px-3 text-[11px] text-[#777]">
              <ChevronDown size={12} />
              <span>分组</span>
              <span className="ml-auto tabular-nums">{visibleGroups.length}</span>
            </h2>
            {visibleGroups.map((group) => (
              <GroupRow
                key={group.id}
                group={group}
                objects={objects}
                query={query}
              />
            ))}
          </section>
        ) : null}

        {objectGroups.length === 0 && visibleGroups.length === 0 ? (
          <div className="px-4 py-10 text-center text-xs text-[#686868]">
            未搜索到内容
          </div>
        ) : (
          objectGroups.map((group) => (
            <section key={group.kind} aria-label={`${group.label}分组`} className="mb-3">
              <h2 className="flex h-7 items-center gap-1 px-3 text-[11px] text-[#777]">
                <ChevronDown size={12} />
                <span>{group.label}</span>
                <span className="ml-auto tabular-nums">{group.objects.length}</span>
              </h2>
              <div role="tree" aria-label={`${group.label}对象`}>
                {group.objects.map((object) => {
                  const selected =
                    selectedGroupId === null &&
                    (selectedObjectIds.length > 0
                      ? selectedObjectIds.includes(object.id)
                      : selectedObjectId === object.id);
                  return (
                    <div
                      key={object.id}
                      role="treeitem"
                      aria-selected={selected}
                      data-director-object-id={object.id}
                      data-director-object-kind={object.kind}
                      data-director-object-selected={selected}
                      data-director-object-visible={object.visible}
                      onClick={(event) => {
                        if (
                          event.shiftKey &&
                          object.kind === "character"
                        ) {
                          toggleObjectSelection(object.id);
                        } else {
                          selectObject(object.id);
                        }
                      }}
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
                      <button
                        type="button"
                        data-director-object-lock={object.id}
                        data-director-object-locked={object.locked}
                        aria-label={object.locked ? `解锁${object.name}` : `锁定${object.name}`}
                        title={object.locked ? "解锁对象" : "锁定对象"}
                        onClick={(event) => {
                          event.stopPropagation();
                          toggleObjectLocked(object.id);
                        }}
                        className={cn(
                          "flex h-6 w-6 shrink-0 items-center justify-center text-[#686868] hover:text-white",
                          object.locked && "text-[#f0c776]",
                        )}
                      >
                        {object.locked ? <Lock size={13} /> : <Unlock size={13} />}
                      </button>
                      <button
                        type="button"
                        data-director-delete-object={object.id}
                        aria-label={`删除${object.name}`}
                        title="删除"
                        onClick={(event) => {
                          event.stopPropagation();
                          deleteDirectorEntity({
                            kind: "DELETE_OBJECT",
                            objectId: object.id,
                          });
                        }}
                        className="flex h-6 w-6 shrink-0 items-center justify-center text-[#686868] hover:text-[#f08d8d]"
                      >
                        <Trash2 size={13} />
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
