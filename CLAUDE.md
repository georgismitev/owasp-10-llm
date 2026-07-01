# Rules of engagement

This is a hands-on learning lab (`PLAN.md` has the full plan). **I lead, you follow.**
Read these rules before every change.

## 1. You follow — you do not lead

- **Never write lab substance on your own initiative.** That means attack code,
  exploits, payloads, defenses/mitigations, evals, or measurement logic.
- Write that code **only when I explicitly ask for it.** "Explicitly" = I name the
  thing to build or ask a direct question that requires it. Silence is not a request.
- **No unsolicited solutions or ideas-as-code.** Don't propose exercises, don't
  sketch an attack "to be helpful," don't add the defense because the attack is done.
- If a task tempts you toward writing lab substance I didn't ask for, **stop and leave
  a TODO or ask me.** I write the attacks, defenses, and evals. You build only what I request.
- Scaffolding/platform (harness, templates, Makefiles, wiring) is fine to build **when
  I ask** — still minimal, still no attack/defense/eval logic inside it.

## 2. Minimal code — always

- Write the **minimum** code that reproduces the attack / implements the defense /
  runs the eval. Nothing beyond that.
- **No speculative edge-case handling, no over-engineering, no abstractions "for later."**
  I will tell you the edge cases that matter — don't invent them.
- Prefer **fewer files, fewer lines, plain obvious code.** A reader must see the attack,
  the defense, and the eval clearly — never get lost in code.
- When unsure whether something is needed: leave it out and ask.

## 3. The prompt is the source of truth

- Read my prompt first. Do what it asks — not more, not less.

## 4. Log every step — `docs/CHANGELOG.md`

- Keep a running build log at `docs/CHANGELOG.md`: after each meaningful step,
  append **one concise line** stating exactly what we did.
- Record especially the actions that leave **no git trace** — installing tools
  (Ollama, deps), pulling models, machine-level or environment changes, downloads.
- One line per step, factual, in order. This log is how I track progress and how a
  reader follows the build step by step. Treat it as first-class — **never skip it**.

## Stack

- **Python.** No notebooks.
