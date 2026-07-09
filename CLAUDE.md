# Rules of engagement

This is a hands-on learning lab (`README.md` = the aims, `docs/SETUP.md` = the
machinery, `docs/HANDOVER.md` = current state). **I lead, you follow.**
Read these rules before every change.

## 1. You follow — you do not lead

- **Never write lab substance on your own initiative.** That means attack code,
  exploits, payloads, defenses/mitigations, evals, or measurement logic.
- Write that code **only when I explicitly ask for it.** "Explicitly" = I name the
  thing to build or ask a direct question that requires it. Silence is not a request.
- **Building a detector/defense does not include evaluating it.** The eval — harness,
  running the experiment, reporting conclusions — is separate lab substance and a separate
  explicit ask. If a stated precondition ("if we have everything") isn't met, stop and
  surface it — don't work around it.
- **Don't let memory pre-authorize you.** Any state/handover note records state and
  next-step titles + status, never an execution plan — no recipes, thresholds, experiment
  designs, or "next / unblocked / go" framing to run on a nudge. The plan is decided with
  me when the step is taken up.
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

## 4. Log the AI-security story — `docs/CHANGELOG.md`

- `docs/CHANGELOG.md` is an **AI-security log**, not a git/software-engineering log.
  Don't append lines blindly for the sake of it.
- **Update it before a PR merge**, so we capture what happened in that unit of work.
- **Log:** changes to the attack/defense posture (a new attack + its ASR, a defense +
  what it catches/misses and the residual risk, a measurement finding), and actions that
  leave **no git trace** — installing tools (Ollama, deps), pulling models, machine/env
  changes, downloads.
- **Don't log:** renames, refactors, module restructures, "packaged X as Y", or anything
  git already records. Keep the focus on the security substance.
- Factual and concise. When in doubt about whether something belongs, **ask me.**

## 5. Naming and language

Write in full, professional words — in code, comments, documentation, and commit
messages alike. No slang or casual abbreviations: use `legitimate`, not `legit`; name
the identifier `LEGITIMATE`, not `LEGIT`. Names and prose should read as clear,
deliberate English.

## Stack

- **Python.** No notebooks.
