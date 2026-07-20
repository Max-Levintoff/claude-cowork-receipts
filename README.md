# Cowork Receipts

A Cowork adaptation of Claude Code's `receipts` plugin: a personal activity report built from local session history, delivered as a markdown report and a styled, printable HTML receipt you can open, print, or export to CSV.

## What it does

Say "cowork receipts" (or "cowork receipts for the last 15 sessions", "update my receipts", etc.) and it will:

1. Pull your most recent Cowork sessions (default: last 30) from local session history.
2. Read what happened in each one.
3. Group them into a small number of topics — recurring automations get their own bucket, one-off sessions get merged into sensible themes rather than one row per session.
4. Tally what was actually produced in each topic: files, decks, skills, live artifacts, chat messages sent or drafted.
5. Render a markdown report and a matching HTML receipt from that data.

No dollar costs, no invented "hours saved" — see [Why this isn't a 1:1 port](#why-this-isnt-a-11-port) for the reasoning.

## Why this isn't a 1:1 port

Claude Code's `receipts` plugin runs as a free local script: it parses `~/.claude/projects/*.jsonl` directly and shells out to `git`, spending tokens only once, at the end, to write the narrative. Cowork has no equivalent local, freely-parseable session archive — the only way to inspect history is through the `session_info` MCP tools (`list_sessions`, `read_transcript`), which cost real tokens per session read. There's also no git/commit signal in Cowork, so "what shipped" is inferred from transcript content (files written, decks and artifacts produced, chat messages sent) rather than measured from a diffstat.

Given that, this plugin:

- Defaults to a **session count** (last 30), not a calendar window — Cowork doesn't expose session timestamps, and interpolating them from embedded links doesn't scale as a repeatable method.
- Groups sessions into a small number of **topics** by model judgment rather than by git project.
- Never computes cost or "hours saved" — no local baseline exists for either in Cowork any more than in Claude Code.
- Explicitly excludes Claude Chat (claude.ai) — no tool available in Cowork reads that conversation history.

## What's in this plugin

- `skills/cowork-receipts/SKILL.md` — the workflow: how to invoke it, how to read and classify sessions, and how to hand off to the renderer.
- `skills/cowork-receipts/references/data-schema.json` — the JSON shape the renderer expects, with a fully generic, illustrative example (no real names, companies, or events).
- `skills/cowork-receipts/scripts/render_receipt.py` — a deterministic renderer that turns the JSON data into both output files. This is what keeps formatting consistent across runs instead of the model hand-writing markdown/HTML each time.

## Cost note

Reading N session transcripts costs real tokens, and cost compounds across a run since later reads re-send everything gathered so far. In practice a ~15-session run has cost on the order of a few thousand tokens; scale roughly linearly for larger counts. If you ask for more than ~50 sessions in one go, expect the skill to flag the cost before proceeding.

## Installing

This source tree is intentionally missing `.claude-plugin/plugin.json`, the one file every Claude/Cowork plugin needs to be installable. It's left as a manual step because some Cowork sessions run under governance policies that block writing files named `plugin.json` from inside the session, so this plugin needs to be finished outside of Cowork.

Run this in your own terminal (not inside a Cowork session) from the parent of this folder:

```bash
cd cowork-receipts-src
mkdir -p .claude-plugin
cat > .claude-plugin/plugin.json << 'EOF'
{
  "name": "cowork-receipts",
  "version": "0.1.0",
  "description": "Generates a personal Cowork activity report (a markdown \"receipt\" plus a styled, printable HTML receipt) from local Cowork session transcripts, grouped by topic with a manager-ready summary.",
  "author": { "name": "Your Name" },
  "keywords": ["receipts", "cowork", "usage report", "activity report", "productivity"]
}
EOF
zip -r ../cowork-receipts.plugin . -x "*.DS_Store"
```

That produces `cowork-receipts.plugin` in the parent directory. Drag it into Cowork (or use your org's plugin install flow) to add it.

If you'd rather publish this to a GitHub repo instead of installing the `.plugin` file directly: create a new repo, copy this folder's contents in (plus the `plugin.json` from above), commit, and push with your own `git`/`gh` credentials. None of that touches a Cowork session, so it isn't affected by any governance restriction.

## License

No license file is included — add one appropriate to how you intend to share this (MIT is a common, permissive default for small utility plugins like this one).
