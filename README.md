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
- Claude Chat is not included — it only analyzes Cowork sessions.

## What's in this plugin

- `skills/cowork-receipts/SKILL.md` — the workflow: how to invoke it, how to read and classify sessions, and how to hand off to the renderer.
- `skills/cowork-receipts/references/data-schema.json` — the JSON shape the renderer expects, with a fully generic, illustrative example (no real names, companies, or events).
- `skills/cowork-receipts/scripts/render_receipt.py` — a deterministic renderer that turns the JSON data into both output files. This is what keeps formatting consistent across runs instead of the model hand-writing markdown/HTML each time.

## Cost note

Reading N session transcripts costs real tokens, and cost compounds across a run since later reads re-send everything gathered so far. In practice a ~15-session run has cost on the order of a few thousand tokens; scale roughly linearly for larger counts. If you ask for more than ~50 sessions in one go, expect the skill to flag the cost before proceeding.

## Installing

Once this plugin is published to Anthropic's plugin directory, install it directly:

```shell
/plugin marketplace add anthropics/claude-plugins-community
/plugin install cowork-receipts@claude-community
```

(If it's accepted into the official directory instead of the community one, the marketplace name will differ — check the plugin's listing page for the exact install command.)

### Manual install (before publishing, or without the directory)

Clone this repository, then package it as a Cowork plugin:

```bash
git clone https://github.com/Max-Levintoff/claude-cowork-receipts.git
cd claude-cowork-receipts
zip -r ../cowork-receipts.plugin . -x "*.DS_Store" -x ".git/*"
```

Drag the resulting `cowork-receipts.plugin` file into Cowork (or use your organization's plugin install flow) to add it.

If your Cowork setup supports installing plugins directly from a GitHub URL, you can skip the zip step and point it at this repository instead.

## Submitting to the directory

1. Keep this repo public — closed-source plugins aren't accepted.
2. Run `claude plugin validate .` to check structure before submitting.
3. Submit via [claude.ai/settings/plugins/submit](https://claude.ai/settings/plugins/submit) or [platform.claude.com/plugins/submit](https://platform.claude.com/plugins/submit), pointing at this GitHub repo (or uploading a zip).
4. After acceptance, pushes to `main` are picked up automatically — no need to resubmit for updates.

## License

MIT — see [LICENSE](LICENSE).
