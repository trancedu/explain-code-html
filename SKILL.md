---
name: explain-code-html
description: Turn source files into complete, source-grounded standalone HTML reading companions. Use when asked to explain a code file in HTML with both big picture and detailed implementation, annotated source, or a code reading guide.
---
# Explain Code in HTML

Create a reading interface that helps developers independently understand and verify implementation.

## Workflow
1. Read the entire source. Record filename, language, line count and SHA-256. Inspect relevant local dependencies when needed; disclose unresolved context. Do not modify the source.
2. Identify purpose, inputs, outputs, entry points, execution order, state and external effects. Divide the entire source into contiguous numbered blocks. Cover every line exactly once in the annotated reading view, including imports and entry-point code. Blank lines may belong to adjacent blocks.
3. Plan explanations before rendering. For every block, state its role and explain every meaningful statement, expression, branch and assumption. Explain language semantics when they affect behavior. Allocate more depth to complex code; do not mechanically translate syntax. Separate implementation facts, inferred intent and proposed changes.
4. Trace one concrete example across functions, showing actual intermediate values. Execute only safe, bounded examples without external effects. Label executed results separately from manual reasoning. Include an invalid/edge input and at least one limitation grounded in source.
5. Generate one standalone UTF-8 HTML with embedded CSS and JavaScript, no network dependencies. Include overview, navigable flow diagram, annotated blocks, example trace, self-check questions with hidden answers, full original source and provenance. Preserve exact source text and original line numbers. Escape source as text, never executable markup. Display important explanations expanded by default; fold only supplementary details.
6. Use a high-contrast light single-column layout suitable for a 10.3-inch e-ink device. Put explanation immediately next to its code vertically. Keep code font legible with horizontal overflow. Add stable block IDs, links from overview to implementation, search for blocks, expand/collapse details and a one-click copyable follow-up question containing filename, source hash, block and line range. Do not imply this sends a question to an agent.
7. Verify coverage without omissions/overlaps and byte-for-byte reconstruction of embedded original source. Check diagram links and controls. Render at desktop and narrow viewport with available local tools; report if visual verification is unavailable. Run source examples when safe. Do not claim comprehension improvements were measured by these checks.

## Required reading order: whole before parts

1. **Purpose and mental model.** Start with the problem the file solves, its place in the larger system, input/output shapes, main responsibilities and one small before/after example. Explain the overall strategy in connected prose before introducing individual functions. Keep provenance and controls secondary.
2. **Whole-file workflow diagram.** End the overview with an actual rendered workflow chart (or DAG for genuinely acyclic dependencies), before any annotated source blocks. Use connected nodes, directed arrows and labeled decisions to show successful, rejected and skipped paths where applicable. A list of cards, headings or arrows embedded in prose is not a substitute. Prefer embedded SVG with accessible title/description and links to implementation blocks; do not rely on external diagram services. Show loops truthfully rather than forcing them into a DAG. Follow the diagram with a short explanation of how to read it.
3. **Parts in context.** Only then introduce detailed code blocks. Group them under the conceptual stages from the overview. State where each part fits in the chart, its role and its relation to other parts before explaining statements. Preserve complete line coverage and provide an original-order source view even if the teaching order differs.
4. **Trace, limitations and self-check.** Retain concrete execution traces and end-of-guide questions with initially hidden answers and links back to the relevant code. Include prediction and modification questions, not only factual recall. Preserve copyable follow-up prompts.

Check the visible document order explicitly: purpose and overall strategy → rendered diagram → detailed implementation → trace and questions. Do not start with a source listing, dense function catalog or metadata wall. Maintain this hierarchy even for short files.

## Explanation contract
- Make the guide sufficient to follow implementation, not just architecture.
- Explain data shape, mutations, return values, early exits and exception handling.
- Distinguish in-file behavior from caller guarantees. Do not invent author intent or promise untested properties.
- Keep source immutable. Record proposed fixes as commentary.
- Record source hash so readers can detect stale explanations; do not claim automatic synchronization unless implemented.
- Default to the user's language, retaining original identifiers.
- Deliver the HTML and original source. Persist skill changes using the environment's skill workflow.
