---
name: workflow-token-optimization
description: Token-saving tools and patterns used by afrizzal — rtk, context7 MCP, custom skills, GSD phase isolation
metadata:
  type: feedback
---

User actively optimizes for token cost. Key tools/patterns:

1. **`rtk` prefix** for ALL bash/git commands — 60-90% token savings. Enforced via project-rules.md #19.
2. **context7 MCP** for library docs — always prefer over WebSearch. Project has dedicated rule [[context7]].
3. **Custom Skills** in `.claude/skills/` for repeated patterns — encapsulate so Claude doesn't re-derive each time.
4. **GSD phase isolation** — work within one phase context at a time, not the whole project, to keep context window manageable.
5. **subagent_type=Explore** for codebase searches — keeps raw search output out of main context.

**How to apply:**
- Default to `rtk` even when user doesn't mention it
- Reach for context7 MCP first when library/framework comes up
- If a pattern repeats > 3 times in conversation, suggest converting to a skill
