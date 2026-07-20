---
name: cowork-receipts
description: Generates a personal Cowork activity report ("receipts") from the local Cowork session history on this machine, producing a markdown report and a styled, printable HTML receipt grouped by topic. Use this whenever someone asks for their "Cowork receipts", "Cowork usage report", "what have I shipped in Cowork", "Cowork activity report", or wants to redo/update a previous receipts run. Defaults to the last 30 Cowork sessions (a session count, not a date range, since Cowork does not expose session timestamps). Does not cover Claude Chat (claude.ai) — no tool available in Cowork reads that conversation history.
---

# Cowork Receipts

## What this does

Mirrors the idea of the Claude Code `receipts` plugin (a personal impact report built from session history), adapted to Cowork. Cowork does not expose a local, freely-parseable session log the way Claude Code does (`~/.claude/projects/*.jsonl`), so this skill drives the same outcome through `session_info` tools and model judgment instead of a zero-cost local script.

## When invoked

Parse an optional session-count argument from the request (default **30**). Recognize phrasing like "cowork receipts", "cowork receipts for the last 15 sessions", "redo my receipts for 50 sessions". If the user asks for a specific date range instead of a session count, tell them upfront that Cowork doesn't expose session timestamps, so a date range can only be approximated by decoding timestamps embedded in session content (mainly Slack message links) and interpolating the rest — offer the session-count version as the reliable default.

**Cost check before reading many transcripts.** Each `read_transcript` call adds real tokens to context, and cost compounds across a run (later reads re-send everything gathered so far). Past runs have measured roughly a few hundred to ~1,500 tokens per transcript depending on session length. If the requested count is above ~50, say so and confirm before proceeding; below that, just proceed.

## Workflow

1. Call `mcp__session_info__list_sessions` with `limit` = the requested session count (default 30).
2. Read each session's transcript: call `mcp__session_info__read_transcript` with `format="auto"`, `max_wait_seconds=0`. Batch these as parallel tool calls in as few messages as possible rather than one at a time.
3. **Classify sessions into topics**, not one bucket per session. Recurring automations (a scheduled task that runs repeatedly, identifiable by a matching title like "Morning brief" across many sessions, or a `<scheduled-task>` tag in the transcript) always get their own topic bucket, however many sessions they span. Genuinely distinct one-off sessions get merged into a small number of sensible themes (e.g. "IT and access administration", "Competitive intelligence") by subject matter — a report with 20 single-session buckets is not useful to a manager. Aim for roughly 6-12 topics regardless of how many sessions were pulled.
4. **Count deliverables per topic** by reading what was actually produced in each session: files written (`Write`, `Edit` + `mcp__cowork__present_files`), decks/docs/spreadsheets, skills built or customized (`Skill` invocations followed by file creation), live artifacts installed (`mcp__cowork__create_artifact`), Slack messages sent or drafted (`slack_send_message`, `slack_send_message_draft`), scheduled tasks created. Do not double-count the same deliverable across topics.
5. **Try to establish a rough calendar span** for context (not required for the headline scope, which is session count): scan transcripts for decodable evidence — a Slack permalink of the form `/p<13-digit-number>` (decode the leading 10 digits as a Unix timestamp), or an explicit date typed in the transcript text (e.g. "Tuesday, June 30, 2026"). Report the span as approximate ("spans 2026-07-06 to 2026-07-20, ~15 days") and say plainly that it's estimated, not exact, since most sessions carry no timestamp at all.
6. **Never compute or invent a dollar cost or "hours saved" figure.** Neither has a real local baseline; both would be inferred, not measured, and would undermine the credibility of everything else in the report. If the user wants spend, point them to the Console.
7. **State plainly that Claude Chat (claude.ai) is out of scope.** No tool available in a Cowork session reads Chat conversation history — only local Cowork sessions on this machine are visible via `session_info`.
8. Assemble a single JSON data object matching `references/data-schema.json` — user name, session count, period label, headline metrics, a total/headline metric, the by-topic table rows, "what you shipped" bullets, a manager-framing paragraph, table notes, and a footer note.
9. Write that JSON to a file in the outputs folder, then run the renderer to build the actual report files:
   ```
   python3 <this skill's directory>/scripts/render_receipt.py <path-to-data.json> <output-basename>
   ```
   This produces `<output-basename>.md` and `<output-basename>.html`. Do not hand-write the markdown or HTML yourself — the script owns formatting so every run looks consistent regardless of session count or topic mix. If the script errors, fix the JSON to match the schema rather than falling back to writing the files by hand.
10. Present both output files to the user.

## Design principles (apply every run)

- **Session count, not a date window, is the default scope.** Cowork doesn't expose session timestamps, and interpolating them doesn't scale as a repeatable method — session count is deterministic and returns the same result every time.
- **Group aggressively.** Prefer 6-12 meaningful topics over one row per session.
- **No fabricated cost or hours-saved figures, ever.**
- **Be upfront about gaps** (Claude Chat not covered, spend not computed, calendar span approximate) rather than glossing over them.
- **The renderer script is the source of truth for formatting.** If the output looks wrong, fix the script or the JSON, don't patch the generated files directly.

## Files in this skill

- `references/data-schema.json` — annotated example of the JSON structure `render_receipt.py` expects.
- `scripts/render_receipt.py` — deterministic renderer; produces both the `.md` report and the styled `.html` receipt (torn-paper design, matches the Claude Code receipts aesthetic) with a working CSV export button.
