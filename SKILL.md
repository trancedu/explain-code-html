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

## Explanation contract
- Make the guide sufficient to follow implementation, not just architecture.
- Explain data shape, mutations, return values, early exits and exception handling.
- Distinguish in-file behavior from caller guarantees. Do not invent author intent or promise untested properties.
- Keep source immutable. Record proposed fixes as commentary.
- Record source hash so readers can detect stale explanations; do not claim automatic synchronization unless implemented.
- Default to the user's language, retaining original identifiers.
- Deliver the HTML and original source. Persist skill changes using the environment's skill workflow.
