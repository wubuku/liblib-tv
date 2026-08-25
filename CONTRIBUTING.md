# Contributing

This repository is a research-driven frontend prototype. Contributions should preserve the distinction between source-site evidence, implementation inference and local prototype decisions.

## Setup

```bash
npm install
npm run dev
```

Use `http://localhost:3000` for LibTV and `http://localhost:3000/frameos/canvas/demo` for FrameOS. Node.js 24+ is the project baseline.

## Before Editing

1. Read [`AGENTS.md`](AGENTS.md).
2. Read [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and the route-specific component spec.
3. Search [`docs/research/`](docs/research/README.md) for existing evidence and screenshot analysis.
4. Confirm whether the change belongs to LibTV, FrameOS or shared infrastructure.

## Implementation Rules

- Keep LibTV and FrameOS stores, node data and route orchestration independent.
- Use existing React Flow and Zustand patterns before adding abstractions.
- Do not infer visual behavior from memory when DOM, JSON or screenshot evidence exists.
- Record new source observations in a discoverable research document before implementation.
- Add stable selectors for new browser-verified states.
- Keep backend, authentication and persistence claims out of this frontend prototype.

## Verification

Run the narrowest relevant browser script first, then the full check:

```bash
python3 scripts/verify-liblib-batch10.py
python3 scripts/verify-liblib-batch4.py
python3 scripts/verify-liblib-batch5.py
python3 scripts/verify-liblib-batch6.py
python3 scripts/verify-liblib-batch7.py
python3 scripts/verify-liblib-batch8.py
python3 scripts/verify-liblib-batch9.py
npm run check
python3 scripts/verify-docs.py
```

If a test or screenshot changes, explain why in the relevant implementation record. Preserve console-error checks in Playwright scripts.

## Documentation Changes

- Update `docs/index.md` when adding formal documents.
- Update `docs/research/README.md` when adding research, evidence or batch records.
- Put active plans in `docs/drafts/` or a clearly named batch directory.
- Put stable architecture and workflow guidance in `docs/`.
- Put obsolete snapshots in `docs/archive/` only after updating inbound links.
- Keep screenshot recognition findings in a `SCREENSHOT_ANALYSIS.md` record so later agents do not repeat expensive inspection.

## Commits

Use concise conventional commit subjects:

```text
feat(scope): add behavior
fix(scope): correct behavior
docs(scope): update evidence or navigation
test(scope): add verification
```

Split major work into reviewable commits: planning, implementation, verification/documentation. Push key progress so another session can resume from the repository history.
