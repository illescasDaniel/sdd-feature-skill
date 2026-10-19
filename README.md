# sdd-feature

Spec-Driven Development for AI coding agents, with human approval gates. The agent does not jump straight from "add
feature X" to a pile of code: it draws a wireframe, writes a spec with you, defines the interfaces, writes the tests,
implements, and then hands the result to an independent reviewer that grades it against the spec. You approve each
step in chat before the next one starts.

It is an [Agent Skill](https://agentskills.io) (a `SKILL.md` plus a spec template, a grader subagent and a small
checker script), so it works in Claude Code, Cursor and any other agent that loads skills.

## The phases

| Phase | Deliverable | Gate |
|-------|-------------|------|
| **0 — Design** | `wireframes/<screen>.html`: one self-contained HTML/CSS file you open in a browser | **Stop.** You approve the design. |
| **1 — Spec** | `specs/<feature>/SPEC.md`: four agreed design decisions, then Given/When/Then scenarios and an Out of scope list | **Stop.** You approve the spec. |
| **2 — Architecture** | Domain types and interfaces (ports) only, no adapters or UI | **Stop.** You approve the shape. |
| **3 — Tests** | One fast test per scenario, `test_given_…_when_…_then_…` | Run them. |
| **4 — Implementation** | Use cases, adapters, UI until the tests and the quality gate pass, matching the wireframe | Until green. |
| **5 — Grade** | A fresh, read-only `code-grader` subagent scores the branch against the spec | Automatic: fix FAILs (max 2 rounds), show you the scorecard. |

The four design decisions agreed at the start of Phase 1 are what turn a feature list into a real design:

- **Success criteria**: what "done" means beyond the scenarios (no data loss, idempotent re-run, …).
- **Failure handling**: what can fail, what the user sees, retry / skip / resume.
- **Performance & resource budget**: latency, memory, disk, network, size limits.
- **Trust boundary**: which input is untrusted and where it gets validated.

Every failure-handling and trust-boundary decision must have at least one scenario, so it ends up tested, not just written down.

## Why it is so useful

- **You see the feature before it exists.** A wireframe costs the agent a minute and you a glance. Catching "no, the
  button goes there" at Phase 0 is far cheaper than after the backend, the tests and the UI have been built around it.
- **The agent stops guessing at the hard parts.** Without a spec, an agent invents error handling, limits and
  security on the fly, differently each time. Here those four decisions are proposed, discussed and approved before any
  code, and then each one is traced to a scenario and a test.
- **"Implement the plan" no longer means "do everything at once".** The skill is explicit that a plan, plan-mode
  approval or a todo list is *not* design or spec approval. The agent ends its turn at each gate and waits for you.
- **The spec is the source of truth.** If implementation reveals the spec was wrong, the agent rewrites the spec and
  asks again instead of quietly patching around it. Six months later, `specs/` still describes what the code does.
- **An independent grade, not self-congratulation.** An agent reviewing its own work in the same context tends to
  approve it. Phase 5 spawns a fresh read-only subagent that maps every scenario to a test and a code location, checks
  each design decision with `path:line` evidence, and returns PASS or NEEDS WORK. The main agent fixes the FAILs (at
  most two rounds) and shows you the scorecard; you make the final call.
- **Small, reviewable steps.** Each gate produces one artifact you can read in a couple of minutes, and each lives in
  git next to the code, so reviewers can read the spec before the implementation PR.

It was extracted from a real project where it drives every feature; the rules in it exist because their absence
caused problems.

## What's in the skill

```
skills/sdd-feature/
  SKILL.md               the workflow and gates the agent follows
  templates/SPEC.md      spec skeleton (Metadata, Design decisions, scenarios, Out of scope)
  agents/code-grader.md  the Phase 5 reviewer, as a Claude Code subagent definition
  scripts/spec_check.py  structural spec checks (stdlib Python, any project language)
```

## Install

### Any agent: the `skills` CLI

```bash
npx skills add illescasDaniel/sdd-feature-skill
```

It asks which agents to install for (Claude Code, Cursor and others) and whether to install into the current project or
globally. Non-interactive: `npx skills add illescasDaniel/sdd-feature-skill -a claude-code -a cursor -y`, plus `-g` for
global.

### By hand

Copy the `skills/sdd-feature` folder into your agent's skills directory.

| | Project (shared with your team) | All your projects |
|---|---|---|
| Claude Code | `.claude/skills/sdd-feature/` | `~/.claude/skills/sdd-feature/` |
| Cursor | `.cursor/skills/sdd-feature/` | `~/.cursor/skills/sdd-feature/` |

```bash
git clone https://github.com/illescasDaniel/sdd-feature-skill
cp -r sdd-feature-skill/skills/sdd-feature your-project/.claude/skills/
```

### The grader subagent (recommended)

Phase 5 works without this step: the skill falls back to a fresh general-purpose subagent prompted with the grader's
instructions. Installing it as a named, read-only subagent is cleaner:

- **Claude Code:** copy `skills/sdd-feature/agents/code-grader.md` to `.claude/agents/code-grader.md`.
- **Cursor:** copy it to `.cursor/agents/code-grader.md` and, in its frontmatter, replace the `tools:` line with
  `readonly: true`.

If your project has code-navigation MCP servers, add them to the grader's `tools:` line so it can follow callers and
implementations instead of grepping.

### Spec checks in CI (optional)

`spec_check.py` has no dependencies, so you can run it in CI. Older specs written before you adopted the design
decisions will fail it, so either retrofit them when next touched or check only new and changed specs:

```bash
python3 .claude/skills/sdd-feature/scripts/spec_check.py specs/*/SPEC.md
```

## Add this to your AGENTS.md / CLAUDE.md

Skills are loaded when the agent judges them relevant. The gates only work if the agent knows about them from the very
first message, before it has decided whether the skill applies, so put the protocol in your `AGENTS.md` (or
`CLAUDE.md`), which is always in context:

```markdown
## Phase Gate Protocol (Spec-Driven Development)

Every feature or user-facing change goes through these phases. Full workflow: the `sdd-feature` skill.

| Phase | Deliverable | Gate |
|-------|-------------|------|
| **0 — Design** | `wireframes/<screen>.html` (self-contained HTML/CSS) | **Stop.** Ask for design approval. |
| **1 — Spec** | `specs/<feature>/SPEC.md`: agreed Design decisions (success criteria, failure handling, performance/resource budget, trust boundary), BDD scenarios, Out of scope | **Stop.** Ask for spec approval. |
| **2 — Architecture** | Domain types and interfaces only | **Stop.** Ask for approval before tests/adapters. |
| **3 — Tests** | Unit tests from the BDD scenarios | Run them. |
| **4 — Implementation** | Use cases, adapters, UI | Until tests pass; must match the approved wireframe. |
| **5 — Grade** | Read-only `code-grader` subagent scores the branch against the spec | Automatic: fix FAILs, max 2 rounds, show the scorecard. |

- **Never skip a gate.** "Implement the plan", "complete all todos", an attached plan file or plan-mode approval is
  **not** design or spec approval; approval must be explicit, in chat. One gate per approval: after the wireframe, end
  the turn and wait.
- If implementation reveals a spec flaw, rewrite the spec, get re-approval, then continue. Don't patch around a bad spec.
- No production code before spec approval. Allowed before it: `wireframes/`, `specs/` and docs.
```

Adjust the paths and the Phase 2 wording to your architecture. If your project has its own conventions (spec location,
quality-gate command, test naming), state them in the same file: the skill reads `AGENTS.md` / `CLAUDE.md` first and uses
the project's settings over its defaults.

## Use it

Ask your agent for a feature: *"add a dark mode toggle to settings"*. It should come back with a wireframe and a
question, not code. Reply *"wireframe approved"* (or what to change), then review the proposed design decisions and the
spec, then the interfaces. From there it writes the tests, implements, gets graded, and shows you the scorecard.

## Pairs well with

[memory-bank](https://github.com/illescasDaniel/memory-bank): a git-tracked `memory/` folder so a new session knows
which gate a feature is at and what the next step is. Phase 4 updates it at milestones if it is installed.

## Contributing

Issues and pull requests are welcome. The skill is deliberately short: if a change makes `SKILL.md` longer, it should
earn it.

## License

MIT, see [LICENSE](LICENSE).
