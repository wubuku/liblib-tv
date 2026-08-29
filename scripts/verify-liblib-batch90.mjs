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
const deskSource = fs.readFileSync(
  new URL("./src/components/director/DirectorDesk.tsx", root),
  "utf8",
);
const readmeSource = fs.readFileSync(
  new URL(
    "./docs/research/liblib-canvas-batch90-2026-08-29/README.md",
    root,
  ),
  "utf8",
);

const assertions = [
  [
    "state exposes session outcome diagnostics",
    storeSource,
    /sessionOutcome: DirectorSessionOutcome \| null/,
  ],
  [
    "session outcome records open disposition and owner transition",
    storeSource,
    /function createDirectorSessionOutcome\([\s\S]*disposition: result\.disposition[\s\S]*previousOwnerKey: result\.previousOwnerKey/,
  ],
  [
    "workspace exposes project lifecycle and session outcome",
    deskSource,
    /data-director-project-lifecycle=\{projectLifecycle \?\? ""\}[\s\S]*data-director-session-disposition/,
  ],
  [
    "scene update is a typed command result",
    storeSource,
    /updateScene: \([\s\S]*\) => DirectorCommandResult/,
  ],
  [
    "scene command rejects missing sessions",
    storeSource,
    /commandKind: "UPDATE_SCENE"[\s\S]*reason: "DIRECTOR_PROJECT_MISSING"/,
  ],
  [
    "scene command rejects invalid values",
    storeSource,
    /invalidValue[\s\S]*reason: "DIRECTOR_INVALID_VALUE"/,
  ],
  [
    "scene command detects no-op patches",
    storeSource,
    /const hasChange = sceneKeys\.some\([\s\S]*DIRECTOR_COMMAND_NO_CHANGE/,
  ],
  [
    "scene command persists and records one history entry",
    storeSource,
    /commandKind: "UPDATE_SCENE"[\s\S]*updateActiveDirectorDocument\(state, after, state\.captures\)[\s\S]*historyEntries: 1[\s\S]*createDirectorHistoryEntry/,
  ],
  [
    "scene name input uses a local draft",
    inspectorSource,
    /sceneNameInputRef[\s\S]*defaultValue=\{scene\.name\}[\s\S]*onBlur=\{\(event\) => \{/,
  ],
  [
    "scene name commits on blur and Enter",
    inspectorSource,
    /onBlur=\{\(event\) => \{[\s\S]*updateScene\(\{ name: nextName \}\)[\s\S]*onKeyDown=\{\(event\) => \{[\s\S]*event\.currentTarget\.blur\(\)/,
  ],
  [
    "scene name does not commit blank text",
    inspectorSource,
    /if \(!nextName\) \{[\s\S]*updateScene\(\{ name: "" \}\)/,
  ],
  [
    "batch records clone/source boundary",
    readmeSource,
    /LibTV 原站 exact project\/session DOM、持久化和 history 语义 \| `SOURCE_UNKNOWN`/,
  ],
];

for (const [label, source, pattern] of assertions) {
  assert.match(source, pattern, label);
}

console.log(
  `Batch 90 pure/source verification passed (${assertions.length} assertions).`,
);
