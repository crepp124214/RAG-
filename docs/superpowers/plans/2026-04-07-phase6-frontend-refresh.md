# Phase 6 Frontend Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the homepage into a desktop-first, Notion-like knowledge workspace where chat is the main stage and evidence remains continuously visible.

**Architecture:** Keep the existing Vue + Pinia data flow and API contracts intact while restructuring the page shell around a narrow left navigation rail, a wide central conversation stage, and a lighter right evidence rail. Treat this as a frontend presentation refactor, not a product-scope expansion: reuse current stores and services, move visual weight away from dashboard cards, and preserve the current document/task/chat capabilities under a new information hierarchy.

**Tech Stack:** Vue 3, Vite, Element Plus, Pinia, Vitest, TypeScript, scoped component CSS

---

## File Structure

### Files to Modify

- `frontend/src/App.vue`
  - Own the new wide desktop shell, page-level messaging hierarchy, and top-level spatial proportions.
- `frontend/src/components/chat/ChatWorkspacePanel.vue`
  - Become the visual center of the homepage, with a stronger session header, calmer message rhythm, and an editor-like composer.
- `frontend/src/components/chat/SessionSidebar.vue`
  - Shrink from an information-heavy side panel into a compact navigation rail for sessions and quick orientation.
- `frontend/src/components/documents/DocumentManagerPanel.vue`
  - Recast into a lighter support module focused on in-flow upload/recent document access instead of a dominant management panel.
- `frontend/src/components/documents/TaskStatusPanel.vue`
  - Recast into a compact supporting status module that fits the evidence rail.
- `frontend/src/__tests__/App.spec.ts`
  - Update shell expectations to reflect the new layout and lighter system messaging.
- `frontend/src/tests/chat-workspace.spec.ts`
  - Extend assertions around the redesigned chat stage so the main workspace remains functionally intact.
- `frontend/src/tests/documents.spec.ts`
  - Extend support-module expectations where homepage-accessible document/task affordances move or compress.

### Files to Create

- None expected for the first implementation pass. Prefer restructuring existing components before introducing new files.

### Verification Commands

- `cmd /c npm run test:unit -- --run src/__tests__/App.spec.ts`
- `cmd /c npm run test:unit -- --run src/tests/chat-workspace.spec.ts`
- `cmd /c npm run test:unit -- --run src/tests/documents.spec.ts`
- `cmd /c npm run test:unit -- --run`
- `cmd /c npm run typecheck`
- `cmd /c npm run lint`

---

### Task 1: Rebuild the Page Shell Around a Wide Research Workspace

**Files:**
- Modify: `frontend/src/App.vue`
- Test: `frontend/src/__tests__/App.spec.ts`

- [ ] **Step 1: Write the failing shell-layout test**

Add or replace an assertion block in `frontend/src/__tests__/App.spec.ts` that verifies the new shell language rather than the old three-column console language.

```ts
expect(wrapper.text()).toContain("知识工作台")
expect(wrapper.text()).toContain("会话导航区域")
expect(wrapper.text()).toContain("证据与上下文区域")
expect(wrapper.find(".workspace-shell").exists()).toBe(true)
expect(wrapper.find(".workspace-main-stage").exists()).toBe(true)
```

- [ ] **Step 2: Run the App test to verify it fails**

Run: `cmd /c npm run test:unit -- --run src/__tests__/App.spec.ts`

Expected: FAIL because the current `App.vue` still renders the older console copy and shell class structure.

- [ ] **Step 3: Write the minimal `App.vue` shell refactor**

Update `frontend/src/App.vue` so it:

- removes the current top-heavy control-panel framing
- introduces a wide shell with class names that match the new layout
- visually demotes health/readiness into support status instead of headline status
- treats the center stage as the dominant width
- renames the stub-friendly regions to the new information architecture

Use class structure like:

```vue
<main class="workspace-shell">
  <aside class="workspace-nav">
    <SessionSidebar />
  </aside>
  <section class="workspace-main-stage">
    <ChatWorkspacePanel />
  </section>
  <aside class="workspace-evidence-rail">
    <DocumentManagerPanel />
    <TaskStatusPanel />
  </aside>
</main>
```

- [ ] **Step 4: Run the App test to verify it passes**

Run: `cmd /c npm run test:unit -- --run src/__tests__/App.spec.ts`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.vue frontend/src/__tests__/App.spec.ts
git commit -m "feat: rebuild app shell for phase 6 workspace"
```

---

### Task 2: Turn the Chat Area Into the Dominant Knowledge Stage

**Files:**
- Modify: `frontend/src/components/chat/ChatWorkspacePanel.vue`
- Test: `frontend/src/tests/chat-workspace.spec.ts`

- [ ] **Step 1: Write the failing chat-stage test**

Add a test that captures the new workspace expectations without changing behavior:

```ts
expect(wrapper.text()).toContain("当前会话")
expect(wrapper.find(".chat-stage-header").exists()).toBe(true)
expect(wrapper.find(".chat-stage-stream").exists()).toBe(true)
expect(wrapper.find(".chat-stage-composer").exists()).toBe(true)
```

- [ ] **Step 2: Run the chat workspace test to verify it fails**

Run: `cmd /c npm run test:unit -- --run src/tests/chat-workspace.spec.ts`

Expected: FAIL because the current component uses the older panel structure and class names.

- [ ] **Step 3: Write the minimal chat-stage refactor**

Update `frontend/src/components/chat/ChatWorkspacePanel.vue` so it:

- introduces a stronger session header
- makes the message stream read like a continuous workspace rather than card stacks
- turns the composer into a calmer editor-like block
- keeps tool-call and citation rendering intact
- preserves existing send behavior and store interactions

Use class boundaries such as:

```vue
<section class="chat-stage">
  <header class="chat-stage-header">...</header>
  <div class="chat-stage-stream">...</div>
  <div class="chat-stage-composer">...</div>
</section>
```

- [ ] **Step 4: Run the chat workspace test to verify it passes**

Run: `cmd /c npm run test:unit -- --run src/tests/chat-workspace.spec.ts`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/chat/ChatWorkspacePanel.vue frontend/src/tests/chat-workspace.spec.ts
git commit -m "feat: redesign chat workspace as primary stage"
```

---

### Task 3: Compress the Session Sidebar Into a Navigation Rail

**Files:**
- Modify: `frontend/src/components/chat/SessionSidebar.vue`
- Test: `frontend/src/__tests__/App.spec.ts`

- [ ] **Step 1: Write the failing navigation-rail test**

Add an expectation in `frontend/src/__tests__/App.spec.ts` or a component-level assertion that reflects the navigation-rail copy and visual role:

```ts
expect(wrapper.text()).toContain("会话导航")
expect(wrapper.find(".session-rail").exists()).toBe(true)
```

- [ ] **Step 2: Run the App test to verify it fails**

Run: `cmd /c npm run test:unit -- --run src/__tests__/App.spec.ts`

Expected: FAIL because the current sidebar still renders as a full session panel.

- [ ] **Step 3: Write the minimal sidebar refactor**

Update `frontend/src/components/chat/SessionSidebar.vue` so it:

- adopts narrower copy and structure
- reduces descriptive noise
- preserves session creation and selection behavior
- visually supports fast switching instead of broad content display

Keep the existing store calls intact:

```ts
void chatStore.hydrate()
chatStore.createAndSelectSession()
chatStore.selectSession(session.id)
```

- [ ] **Step 4: Run the App test to verify it passes**

Run: `cmd /c npm run test:unit -- --run src/__tests__/App.spec.ts`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/chat/SessionSidebar.vue frontend/src/__tests__/App.spec.ts
git commit -m "feat: convert session panel into navigation rail"
```

---

### Task 4: Recast Document and Task Panels as Light Support Modules

**Files:**
- Modify: `frontend/src/components/documents/DocumentManagerPanel.vue`
- Modify: `frontend/src/components/documents/TaskStatusPanel.vue`
- Test: `frontend/src/tests/documents.spec.ts`

- [ ] **Step 1: Write the failing support-module test**

Add assertions that reflect the new support-module purpose without changing document-store behavior:

```ts
expect(wrapper.text()).toContain("知识库入口")
expect(wrapper.text()).toContain("最近文档")
expect(wrapper.text()).toContain("任务摘要")
```

If the current tests are store-only, add a focused component-level render test instead of overloading store tests.

- [ ] **Step 2: Run the documents-related test to verify it fails**

Run: `cmd /c npm run test:unit -- --run src/tests/documents.spec.ts`

Expected: FAIL because the current components still present heavy standalone management panels.

- [ ] **Step 3: Write the minimal support-module refactor**

Update both document-side components so they:

- visually shrink into support modules
- keep upload access available
- keep recent document visibility
- keep task summaries visible
- stop competing with the central chat stage

Preserve these behaviors:

- upload still calls `documentStore.upload(file)`
- delete remains available where appropriate
- hydration/polling behavior remains intact

- [ ] **Step 4: Run the documents-related test to verify it passes**

Run: `cmd /c npm run test:unit -- --run src/tests/documents.spec.ts`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/documents/DocumentManagerPanel.vue frontend/src/components/documents/TaskStatusPanel.vue frontend/src/tests/documents.spec.ts
git commit -m "feat: lighten document and task support modules"
```

---

### Task 5: Harmonize Status Messaging and Finish Frontend Verification

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/components/chat/ChatWorkspacePanel.vue`
- Modify: `frontend/src/components/chat/SessionSidebar.vue`
- Modify: `frontend/src/components/documents/DocumentManagerPanel.vue`
- Modify: `frontend/src/components/documents/TaskStatusPanel.vue`
- Test: `frontend/src/__tests__/App.spec.ts`
- Test: `frontend/src/tests/chat-workspace.spec.ts`
- Test: `frontend/src/tests/documents.spec.ts`

- [ ] **Step 1: Write the failing final-layout expectation**

Add one final integration-style expectation that ensures:

- blocking errors still surface clearly
- non-blocking status messaging is visually secondary
- the homepage still contains chat, evidence, and support affordances together

Example:

```ts
expect(wrapper.find(".workspace-main-stage").exists()).toBe(true)
expect(wrapper.find(".workspace-evidence-rail").exists()).toBe(true)
expect(wrapper.find(".system-status-banner").exists()).toBe(true)
```

- [ ] **Step 2: Run the focused affected tests to verify one fails**

Run:

```bash
cmd /c npm run test:unit -- --run src/__tests__/App.spec.ts src/tests/chat-workspace.spec.ts src/tests/documents.spec.ts
```

Expected: FAIL until the final shell/status polish is complete.

- [ ] **Step 3: Write the minimal final polish**

Apply the smallest remaining changes needed to:

- unify spacing, typography, and shell proportions
- keep blocking errors visible without restoring dashboard dominance
- ensure the right rail reads as evidence/context support, not a third primary column

- [ ] **Step 4: Run the focused affected tests to verify they pass**

Run:

```bash
cmd /c npm run test:unit -- --run src/__tests__/App.spec.ts src/tests/chat-workspace.spec.ts src/tests/documents.spec.ts
```

Expected: PASS

- [ ] **Step 5: Run the full frontend verification**

Run:

```bash
cmd /c npm run test:unit -- --run
cmd /c npm run typecheck
cmd /c npm run lint
```

Expected:

- unit tests: PASS
- typecheck: PASS
- lint: PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/App.vue frontend/src/components/chat/ChatWorkspacePanel.vue frontend/src/components/chat/SessionSidebar.vue frontend/src/components/documents/DocumentManagerPanel.vue frontend/src/components/documents/TaskStatusPanel.vue frontend/src/__tests__/App.spec.ts frontend/src/tests/chat-workspace.spec.ts frontend/src/tests/documents.spec.ts
git commit -m "feat: finalize phase 6 frontend refresh"
```

---

## Manual Verification Checklist

- [ ] Open the app on a wide desktop viewport
- [ ] Confirm the homepage no longer feels like a narrow centered dashboard
- [ ] Confirm chat is visually dominant
- [ ] Confirm citations remain readable and visible in the right rail
- [ ] Confirm upload still feels attached to the active analysis flow
- [ ] Confirm health/degraded/system messaging no longer steals homepage focus

## Notes for the Implementer

- Do not add backend work to this plan.
- Do not introduce new routes unless absolutely necessary to support the shell.
- Prefer adapting existing components over creating a parallel view hierarchy.
- Keep the visual direction restrained and professional; do not drift into generic AI-landing-page styling.
- Preserve current store/service contracts unless a test proves a frontend-only shape change is necessary.
