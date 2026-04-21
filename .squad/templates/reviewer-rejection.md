# Reviewer Rejection Protocol — Full Reference

## Basic Protocol

When a team member has a **Reviewer** role (Tester, Code Reviewer, Lead):
- Reviewers may **approve** or **reject** work.
- On **rejection**, Reviewer chooses ONE of:
  1. **Reassign:** Require a *different* agent (not original author)
  2. **Escalate:** Require a *new* agent with specific expertise
- Coordinator MUST enforce this. Original agent does NOT self-revise.

## Strict Lockout Semantics

1. **Original author is locked out.** May NOT produce next version. No exceptions.
2. **Different agent MUST own revision.** Selected per Reviewer's recommendation.
3. **Coordinator enforces mechanically.** Verify selected agent ≠ original author. If Reviewer names original author, refuse and ask for different agent.
4. **No contribution from locked-out author** — not as co-author, advisor, or pair.
5. **Lockout scope:** Only the rejected artifact. Original author can still work on unrelated artifacts.
6. **Lockout duration:** Persists for that revision cycle. If revision is also rejected, revision author is also locked out → third agent must revise.
7. **Deadlock handling:** If all eligible agents locked out, escalate to user rather than re-admitting.
