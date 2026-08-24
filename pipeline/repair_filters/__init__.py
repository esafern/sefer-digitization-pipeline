"""Per-engine typographic repair filters (MULTI-WITNESS-REPAIR-AND-SYNTHESIS-PLAN.md §3).

Each filter repairs ONE engine's known, systematic blind spot before its output
enters consensus alignment, so an engine artifact never becomes a dispute a human
has to adjudicate. Every filter here rewrites or annotates a witness stream and
therefore falls under §3.5: it must carry a measured rate against an INDEPENDENT
signal before it is trusted, and "it only annotates, it doesn't rewrite" is not
an exemption (Lesson 26 - a filter that hides produces silence, which is harder
to catch than a wrong rewrite).
"""
