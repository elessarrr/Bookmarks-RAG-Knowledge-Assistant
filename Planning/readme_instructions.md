Instructions for README:
Write a README that demonstrates executive decision-making and product maturity, not just technical skill. Structure it as:

Opening Hook (2-3 sentences)

What problem you set out to solve
Your hypothesis about the solution


What I Built (bullets)

Architecture highlights: "Local-first RAG with adapter pattern for cloud swap"
Technical rigor: "TDD with >80% coverage, RAGAS eval framework, type-safe with mypy"
Production patterns: "DuckDB vector store, sentence-transformers, Ollama LLM"


Why I'm Archiving This (critical section)

Lead with product insight, not "ran out of time"
Example: "After building V1, I realized the core use case is flawed: people don't bookmark-then-forget because they lack search—they forget because bookmarking isn't integrated into their workflow. The real solution is a browser extension that captures context at save-time, not a post-hoc retrieval tool."
Show you validated assumptions and killed your darling when data pointed elsewhere
Mention what you'd build instead if starting over


What I Learned

2-3 bullet points on architectural decisions or eval methodology
Keep technical, avoid "learned a lot" platitudes


For Recruiters/Hiring Managers

Explicit note: "This repo demonstrates end-to-end AI product development (PRD → eval framework → shipping code) and willingness to kill projects that don't solve real problems. Available to discuss architecture decisions or pivot rationale."



Tone guidance:

Confident, not apologetic ("I'm archiving this" not "sorry this isn't finished")
Analytical, not defensive (explain the pivot reasoning like a PM presenting to stakeholders)
Forward-looking (what you'd build instead shows strategic thinking)

Avoid:

"I didn't have time" (sounds junior)
"Maybe I'll come back to this" (shows indecision)
Over-explaining technical choices (let the code speak)