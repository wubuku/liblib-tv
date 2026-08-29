import assert from "node:assert/strict";
import fs from "node:fs";

const root = new URL("..", import.meta.url);
const storeSource = fs.readFileSync(
  new URL("./src/store/directorStore.ts", root),
  "utf8",
);
const inspectorSource = fs.readFileSync(
  new URL("./src/components/director/DirectorInspector.tsx", root),
  "utf8",
);
const readmeSource = fs.readFileSync(
  new URL(
    "./docs/research/liblib-canvas-batch91-2026-08-29/README.md",
    root,
  ),
  "utf8",
);

const assertions = [
  [
    "shared mutation helper commits registry persistence and one history",
    storeSource,
    /function commitDirectorMutation\([\s\S]*updateActiveDirectorDocument\(state, input\.after, input\.captures\)[\s\S]*historyEntries: 1[\s\S]*createDirectorHistoryEntry/,
  ],
  [
    "object update is typed and validates patch values",
    storeSource,
    /updateObject: \(objectId, patch\) => \{[\s\S]*DIRECTOR_INVALID_VALUE[\s\S]*UPDATE_OBJECT/,
  ],
  [
    "object update persists through the shared commit boundary",
    storeSource,
    /commandKind: "UPDATE_OBJECT"[\s\S]*commitDirectorMutation\(state, \{[\s\S]*after[\s\S]*captures: state\.captures/,
  ],
  [
    "camera update is typed and validates references",
    storeSource,
    /updateCamera: \(objectId, patch\) => \{[\s\S]*DIRECTOR_REFERENCE_INVALID[\s\S]*DIRECTOR_TARGET_LOCKED/,
  ],
  [
    "camera update records an authored document and timeline keyframe",
    storeSource,
    /updateCamera: \(objectId, patch\) => \{[\s\S]*upsertTrackKeyframe[\s\S]*createDirectorProjectDocumentV1[\s\S]*commitDirectorMutation/,
  ],
  [
    "group creation has a project command boundary",
    storeSource,
    /commandKind: "GROUP_CHARACTERS"[\s\S]*createDirectorProjectDocumentV1[\s\S]*selectionResult[\s\S]*commitDirectorMutation/,
  ],
  [
    "group transform validates finite positive values",
    storeSource,
    /UPDATE_GROUP_TRANSFORM[\s\S]*invalidTransform[\s\S]*DIRECTOR_INVALID_VALUE/,
  ],
  [
    "group name uses a local draft",
    inspectorSource,
    /data-director-group-name[\s\S]*defaultValue=\{group\.label\}[\s\S]*onBlur=\{\(event\) =>[\s\S]*updateGroup\(group\.id/,
  ],
  [
    "object name uses a local draft",
    inspectorSource,
    /data-director-object-name[\s\S]*defaultValue=\{selected\.name\}[\s\S]*onBlur=\{\(event\) =>[\s\S]*updateObject\(selected\.id/,
  ],
  [
    "batch keeps source parity boundary explicit",
    readmeSource,
    /LibTV 原站 Director 的 exact object\/camera\/group command、history 和 persistence 语义 \| `SOURCE_UNKNOWN`/,
  ],
];

for (const [label, source, pattern] of assertions) {
  assert.match(source, pattern, label);
}

console.log(
  `Batch 91 pure/source verification passed (${assertions.length} assertions).`,
);
