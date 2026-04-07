# Phase 6 Frontend Refresh Design

## 1. Goal

Phase 6 changes the frontend focus from an engineering-style three-column console into a product-grade knowledge workspace.

The new homepage should feel closer to a Notion-style desktop product:

- wide rather than centered and narrow
- calm and professional rather than dashboard-heavy
- centered on asking questions and reading answers
- supported by evidence, document, and system context without letting those areas dominate

This phase is a frontend-first design phase. It does not add backend capability, change API contracts, or expand product scope outside the approved interface refresh.

## 2. Scope

### In Scope

- Rebuild the homepage layout into a Notion-like dual-column research workspace
- Make chat the visual and functional center of the application
- Reduce the left side into a compact navigation rail
- Recast the right side into a lighter evidence-and-context rail
- Reframe upload and document entry points as support for the current analysis flow
- Improve visual hierarchy, spacing, typography, surface styling, and state presentation
- Fix obvious usability issues that block efficient desktop use

### Out of Scope

- Backend changes
- New API fields or protocol changes
- Authentication, authorization, tenant support
- New product modules or routes unless a minimal split becomes necessary to support the new homepage structure
- A full design system program or large abstraction project
- Mobile-first redesign

## 3. Product Direction

The chosen direction is:

- product tone: professional knowledge workspace
- change size: large homepage redesign
- homepage center: chat
- screen priority: desktop-first
- layout model: Notion-like dual-column research workspace

This means the homepage is no longer a status-heavy control panel. It becomes a workspace where the primary action is to ask, refine, and validate knowledge queries while keeping evidence visible.

## 4. Information Architecture

### Primary Structure

The new homepage is split into three functional zones:

1. Left navigation rail
2. Center conversation stage
3. Right evidence rail

### Left Navigation Rail

The left rail becomes narrow and utility-focused. It should not carry dense management UI.

Responsibilities:

- brand/home entry
- session switching
- knowledge base entry
- task/system entry
- a small number of quick actions

It should behave like a stable navigation spine, not like a full information panel.

### Center Conversation Stage

The center stage becomes the dominant surface on the page and should consume the large majority of horizontal attention.

Responsibilities:

- current session header
- recent context for the active conversation
- message stream
- input composer
- in-flow lightweight actions such as attach/upload

This area should feel like an editor-quality workspace rather than a collection of stacked cards.

### Right Evidence Rail

The right rail remains visible but lighter than the current right column.

Responsibilities:

- citations for the current answer
- source document references
- compact task status summary
- low-priority system notices such as degraded optional dependencies

This rail exists to help users verify trust and context while keeping the center stage uninterrupted.

## 5. Core Interaction Flow

The homepage should support this default loop:

1. User lands on the homepage
2. Focus goes to the active session or the new-question composer
3. User asks a question
4. The center stage renders the answer as the main artifact
5. The right rail updates with citations and source evidence
6. If the user needs more context, they add a document from the current flow instead of leaving the workspace
7. If tasks fail or optional systems degrade, those signals appear as supporting information rather than displacing the main workspace

This flow intentionally keeps document management downstream of analysis rather than making management the homepage purpose.

## 6. Visual Design Direction

### Layout Feel

The refreshed page should feel wide, open, and desktop-native.

Guidelines:

- reduce outer margins
- avoid narrow centered shells
- let the center stage breathe horizontally
- use flatter, quieter surfaces instead of thick floating cards
- use section separation through rhythm, contrast, and structure more than through heavy chrome

### Styling Principles

- restrained professional palette
- higher-quality typography and hierarchy
- fewer but more deliberate surface treatments
- stronger spacing consistency
- less “status dashboard” energy
- more “knowledge tool” energy

### Priority of Attention

Visual emphasis order:

1. active conversation
2. supporting evidence
3. navigation and management actions
4. infrastructure and health feedback

## 7. Component-Level Changes

### `frontend/src/App.vue`

This file becomes the new page shell owner.

Changes:

- replace the current equal-weight three-column framing
- introduce the new wide shell and research-workspace proportions
- reduce the prominence of global health messaging
- move toward a desktop application frame rather than a dashboard header plus stacked panels

### `frontend/src/components/chat/ChatWorkspacePanel.vue`

This component becomes the homepage anchor.

Changes:

- strengthen session header treatment
- improve message reading rhythm
- make the composer more editor-like and less utility-like
- support nearby entry points for attach/upload actions
- preserve citations and tool-result behaviors while improving presentation

### `frontend/src/components/chat/SessionSidebar.vue`

This component changes from a broader side panel into a compact navigation tool.

Changes:

- compress visual weight
- focus on switching and quick orientation
- reduce secondary text density on the homepage

### `frontend/src/components/documents/DocumentManagerPanel.vue`
### `frontend/src/components/documents/TaskStatusPanel.vue`

These stop behaving like co-equal homepage modules.

Changes:

- convert them into lighter supporting modules
- reduce homepage dominance
- keep upload and recent status accessible
- emphasize context around the active flow rather than standalone management

## 8. Data and State Impact

No backend or contract changes are required.

The refresh should primarily reuse existing frontend services and stores:

- `chat` store and services remain the conversation source of truth
- `documents` store remains the document/task source
- `system` store remains available for health/readiness messaging but visually downgraded

The goal is structural and presentation refactoring, not new business logic.

## 9. Error Handling and Status Strategy

The current interface gives backend status a strong top-level presence. The refreshed design should keep the signal but reduce visual interruption.

Rules:

- blocking failures may still surface as strong alerts
- non-blocking degraded states should move to the supporting rail or smaller contextual banners
- optional dependency degradation must not visually compete with the primary chat task
- task failures should remain easy to inspect without forcing the user into a management-first layout

## 10. Testing Strategy

### Automated Verification

Update and extend frontend tests to cover:

- new shell structure
- primary chat-first layout expectations
- continued rendering of citations/tool states after layout changes
- document/task support modules remaining accessible

Minimum checks after implementation:

- frontend unit tests
- frontend typecheck
- frontend lint

### Manual Verification

Review on desktop-first breakpoints:

- wide desktop
- standard laptop width
- narrow-but-supported fallback

Manual checks should confirm:

- page no longer feels narrow or dashboard-like
- chat is the clear homepage center
- evidence rail remains usable while less visually heavy
- upload/document actions still fit the analysis flow

## 11. Implementation Order

Recommended order:

1. Rebuild the shell in `App.vue`
2. Rework the chat stage in `ChatWorkspacePanel.vue`
3. Compress and restyle `SessionSidebar.vue`
4. Reframe document/task panels into lighter support modules
5. Update tests and run visual/manual verification

## 12. Risks

### Risk: Chat center weakens document usability

Mitigation:

- keep upload and recent document entry points within immediate reach
- keep deeper management available from navigation

### Risk: “Professional” becomes visually bland

Mitigation:

- use strong layout confidence and typography hierarchy instead of decorative effects

### Risk: Large homepage change breaks existing tests or assumptions

Mitigation:

- update tests alongside layout changes
- preserve state/store contracts

## 13. Success Criteria

Phase 6 frontend refresh is successful when:

- the homepage reads as a professional knowledge workspace rather than an engineering console
- the width and density feel closer to Notion than to a narrow centered dashboard
- chat is the unquestioned main focus
- evidence remains continuously visible and trustworthy
- document and task actions remain easy to reach without dominating the page
- the existing frontend behavior remains functionally intact
