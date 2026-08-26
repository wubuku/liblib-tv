# LibTV Auto Link State Contract

> Scope: the current LibTV image/video generation Prompt reference workflow. This is a source-backed research contract for later implementation, not authorization to modify `src/`.

## 1. Product Boundary

Auto Link is an assistive reference layer around the Prompt editor. It is not a single “match assets” button and it is not equivalent to a reference thumbnail row:

```text
global preference
  -> candidate pool from connected/reference assets
  -> async occurrence detection
  -> inline ghost suggestion
  -> user accept/reject
  -> structured mention badge
  -> provider ordinal projection at submit time
```

The following are separate state domains:

| Domain | Meaning | Can exist without the others? |
|---|---|---|
| Reference asset | Media deliberately included for the current generation | yes |
| Graph connection | Canvas relationship between source and target nodes | yes, for text/reference-only paths |
| Prompt mention | One inline occurrence referring to a stable source node | yes, after a connected option is committed |
| Provider ordinal | Current display/request projection such as `图片 1` | no, derived from current reference order |

Do not use an image URL or visible `图片 1` label as the media identity. The stable identity is the source node ID.

## 2. Source Evidence

- Current page: the LibTV canvas project recorded in [`LIVE_AUDIT.md`](../liblib-seedance-2.5-2026-08-25/LIVE_AUDIT.md).
- Current production chunks and field-level observations: [`LIBTV_AUTOLINK_STATE_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_AUTOLINK_STATE_MATRIX.md).
- Current selected-image toolbar/panel geometry: [`LibTVOverlayPositioning.contract.md`](LibTVOverlayPositioning.contract.md).
- Current clone implementation: [`ImageEditPanel.tsx`](../../../src/components/ImageEditPanel.tsx) and [`VideoGenerationPanel.tsx`](../../../src/components/VideoGenerationPanel.tsx).

The current source evidence is strong for state structure and interaction semantics. Exact ghost color, animation timing and all lexical stop-word rules remain unconfirmed because this research avoided typing into the shared source project.

## 3. State Model

The later clone implementation should model the following states explicitly. Names are clone design vocabulary, not claims about source TypeScript types.

```ts
type AutoLinkPreference = {
  enabled: boolean;
  tabTipSeen?: "single" | "batch";
};

type AutoLinkCandidate = {
  nodeId: string;
  mediaType: "image" | "video" | "audio";
  sourceName: string;
  ordinal: number;
  tags: string[];
};

type AutoLinkGhost = {
  candidateNodeId: string;
  start: number;
  end: number;
  text: string;
  status: "active" | "visible";
};

type PromptMention = {
  nodeId: string;
  mediaType: "image" | "video" | "audio";
  ordinal: number;
  start: number;
  end: number;
  sourceName: string;
};
```

The types above are an implementation boundary for the clone. They intentionally do not include a provider task ID, generated URL, billing amount or upload state.

## 4. Lifecycle Contract

| State/transition | Source behavior | Required clone rule later |
|---|---|---|
| Initial preference | Read `libtv:promptMentionEnabled`; missing value defaults to enabled | One shared preference for image and video panels |
| Candidate build | Read connected/reference assets; expand names, variants and tags; assign current ordinals | No fixed `陈默 / 咖啡` array; candidates derive from the current graph/reference context |
| Detection start | Use current editor text and caret/selection; async detection may be cancelled | Associate result with the exact text version and editor instance |
| Detection result | Insert non-committing ghost spans at matched occurrences | Ghost must not change the committed Prompt value or reference list |
| Active ghost | User can click it or press `Tab` | Accept only the active occurrence |
| Batch accept | `Shift+Tab` accepts current suggestions | Batch acceptance is explicit and separate from single acceptance |
| Reject | `Escape`, ordinary edit, blur or suspended editor removes ghosts | Preserve user-authored text and already committed mentions |
| Commit | Replace the accepted occurrence with a structured non-editable badge | Store node ID/media type; derive display ordinal from current references |
| Unconnected option | Attempt graph connection, then commit mention only after success | Connection failure leaves no orphan badge |
| Reference reorder | Keep node ID, recompute ordinal projection | Never use ordinal as durable identity |
| Other editor overlay | Prompt dropdown/popover suspends suggestion keyboard handling | Auto Link must not steal `Tab`/`Escape` while another editor owns focus |

## 5. Candidate And Identity Rules

1. Candidate scope is the current connected/reference asset set, subject to the user's project authorization. Do not search the whole canvas or another project just because a name matches.
2. Candidate matching may use display name, variant name, tags and ordinal syntax, but the output must resolve to a stable node ID.
3. Duplicate mentions of the same source node keep the same node ID and current ordinal.
4. Reordering the reference strip changes the visible ordinal only; it must not rewrite source identity.
5. A reference thumbnail alone does not prove that the Prompt contains a mention. The reference list and inline badge are distinct states.
6. A camera preset can share badge presentation but does not have to carry a media node ID. Do not force every badge into the media candidate type.

## 6. Editor And Race Contracts

Detection is asynchronous. A result is usable only if all of the following remain true when it resolves:

- Auto Link is still enabled;
- the editor instance is still mounted and focused or owns the current selection;
- the committed Prompt text version is unchanged;
- the caret/selection range still refers to the same editor state;
- IME composition is not active;
- no competing Prompt dropdown or modal has suspended Auto Link.

On invalidation, abort or discard the result. Never insert a stale mention into newer Chinese input. Ghost spans must carry a distinct marker from committed badges, for example `data-mention-suggest` versus `data-mention-node-id`.

The source uses an inline editor because suggestion position is a text occurrence, not a panel-level action. A clone implementation that stays on `<textarea>` cannot faithfully represent inline ghost and non-editable badges without an explicit projection layer; that limitation must be documented before coding.

## 7. Current Clone Delta

The current clone is intentionally outside this contract in several ways:

| Contract | Current clone behavior | Classification |
|---|---|---|
| Shared preference | Image and video each keep local state | fidelity gap |
| Candidate scope | Fixed `陈默` and `咖啡` entries | clone-only prototype |
| Suggestion surface | Separate panel-level confirmation popover | fidelity gap |
| Prompt editor | `<textarea>` | architectural gap for inline mentions |
| Acceptance | One button accepts both candidates | fidelity gap |
| Writeback | Prepends ordinary text tokens | fidelity gap and identity loss |
| Graph relation | Image panel only changes local references | relation gap |
| Race handling | No abort, text-version, caret or IME guard | reliability gap |

The exact current code locations are retained in [`LIBTV_AUTOLINK_STATE_MATRIX.md`](../open-canvas-2026-08-26/LIBTV_AUTOLINK_STATE_MATRIX.md#5-source--clone-差异). Do not “fix” these differences by adding more popover copy or more fixed candidates; the source contract requires a different state shape.

## 8. Authorized Implementation Slices

These are independent slices for a future authorized coding batch:

### Slice A: Preference And Visibility

- Share one local preference between image/video panels.
- Render the switch in the existing advanced-settings disclosure.
- Remove unsupported fixed-count and footer-only Auto Link entry claims.
- Verify cross-node selection and reload persistence.

### Slice B: Read-Only Ghost Prototype

- Keep the existing textarea or introduce an editor adapter deliberately.
- Show a ghost occurrence without changing committed text or references.
- Verify Escape, blur, ordinary edit and stale-result cleanup.

### Slice C: Structured Mention Editor

- Choose an editor representation that can host non-editable badges.
- Accept one ghost with click/Tab and all with Shift+Tab.
- Preserve source node ID and media type; derive ordinal from references.

### Slice D: Graph And Reference Transaction

- Connect an unconnected candidate only as part of an explicit transaction.
- Roll back the badge if connection fails.
- Recompute display ordinals after reference reorder.

Slices A and B are lower-risk UI prototype work. Slices C and D change input representation and graph semantics and require broader browser regression. None is authorized by this document alone.

## 9. Verification Contract

After explicit coding authorization, the minimum browser checks are:

1. Image and video panels read the same Auto Link preference.
2. Candidate list changes when connected/reference assets change; no fixed candidate appears without a matching source node.
3. Detection renders ghost only; committed text, references and graph counts remain unchanged.
4. Click and `Tab` accept one occurrence; `Shift+Tab` accepts all current occurrences.
5. `Escape`, blur and ordinary editing remove ghost spans but preserve real text and committed badges.
6. Chinese IME composition cannot commit a stale suggestion.
7. Duplicate mentions share node ID and ordinal; reference reorder changes ordinal only.
8. Unconnected candidate connection failure leaves no badge and no half-created edge.
9. Opening a competing Prompt menu suspends Auto Link keyboard handling.
10. Selection change, canvas pan, zoom and mobile clipping do not detach the editor from its node.

## 10. Non-Goals And Safety Boundary

- No real model generation, upload, billing, remote save or provider payload is specified here.
- No source Prompt typing, suggestion acceptance, source toggle mutation or graph connection was performed for this contract.
- No exact ghost color, animation or lexical tokenizer is asserted beyond the evidence matrix.
- No code change is implied; this file is a prerequisite for a later authorized batch.
