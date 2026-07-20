#!/usr/bin/env python3
"""Render Cowork Receipts (markdown + HTML) from a JSON data file.

Usage:
    python3 render_receipt.py data.json output_basename

Produces <output_basename>.md and <output_basename>.html in the current
directory. See references/data-schema.json for the expected JSON shape.

This script is the single source of truth for formatting. The skill fills in
a JSON data object from session analysis and calls this script rather than
hand-writing markdown or HTML, so output stays consistent run to run
regardless of session count or topic mix.
"""
import datetime
import json
import sys


def esc_html(s):
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def esc_csv_field(s):
    s = str(s)
    if any(c in s for c in [",", '"', "\n"]):
        s = '"' + s.replace('"', '""') + '"'
    return s


def render_md(data):
    lines = []
    lines.append(f"# {data['user_name']}'s Cowork Receipt\n")
    hl = " · ".join(f"**{h['label']}:** {h['value']}" for h in data["headline"] if h["label"] != "Sessions")
    lines.append(f"**Period:** {data['period_label']}")
    lines.append(f"**Total sessions:** {data['session_count']} · {hl}\n")

    lines.append("## What you shipped\n")
    for b in data["what_shipped"]:
        lines.append(f"- {b}")
    lines.append("")

    lines.append("## By topic\n")
    lines.append("| Topic | Sessions | % of Sessions | Deliverables |")
    lines.append("|---|---|---|---|")
    for t in data["topics"]:
        lines.append(f"| {t['name']} | {t['sessions']} | {t['pct']}% | {t['deliverables']} |")
    lines.append("")
    if data.get("table_notes"):
        lines.append("Notes: " + " ".join(data["table_notes"]))
        lines.append("")

    lines.append("## Framing for a manager\n")
    lines.append(data["framing"])
    lines.append("")

    lines.append("## What counts and what doesn't\n")
    lines.append(data.get(
        "what_counts",
        "This reads session transcripts and lists what was produced. It does not compute cost or "
        "\"hours saved\" — a dollar figure would be inferred from token counts rather than measured, "
        "and a saved-hours multiplier has no real baseline to compare against. Pull spend figures "
        "from the Console if you need them.",
    ))
    lines.append("")

    lines.append("## Privacy note\n")
    lines.append(data.get(
        "privacy_note",
        "Transcripts can contain real conversation content, not just file diffs, so this describes "
        "activity rather than quoting conversations back.",
    ))

    if data.get("footer_note"):
        lines.append("")
        lines.append(data["footer_note"])

    return "\n".join(lines) + "\n"


CSS = """
  :root { --ink:#1f1d1a; --paper:#fdfcf7; --muted:#8a8478; --accent:#d97757; --line:#d8d3c8; }
  * { box-sizing: border-box; }
  html, body { margin:0; padding:0; }
  body {
    min-height:100vh;
    padding: 2.5rem 1rem;
    background: #e7e3da;
    font-family: ui-monospace, "SF Mono", "Menlo", "Consolas", monospace;
    color: var(--ink);
    display:flex; justify-content:center; align-items:flex-start;
  }
  .receipt-wrap {
    width: 100%; max-width: 440px;
    filter: drop-shadow(0 10px 22px rgba(0,0,0,0.20));
  }
  .receipt {
    --tooth: 13px;
    --notch: 7px;
    background: var(--paper);
    width: 100%;
    padding: calc(1.5rem + var(--notch)) 1.75rem calc(1.25rem + var(--notch));
    --torn:
      conic-gradient(from 135deg at top, #0000, #000 1deg 89deg, #0000 90deg)
        top / var(--tooth) var(--notch) repeat-x,
      conic-gradient(from -45deg at bottom, #0000, #000 1deg 89deg, #0000 90deg)
        bottom / var(--tooth) var(--notch) repeat-x,
      linear-gradient(#000 0 0)
        center / 100% calc(100% - 2 * var(--notch)) no-repeat;
    -webkit-mask: var(--torn);
    mask: var(--torn);
  }
  h1 { text-align:center; font-size:1rem; letter-spacing:0.25em; margin:0; font-weight:700; }
  h2 { font-size:0.7rem; letter-spacing:0.15em; text-transform:uppercase; color:var(--muted); margin: 1.25rem 0 0.6rem; font-weight:700; }
  .sub { text-align:center; color:var(--muted); font-size:0.7rem; margin-top:0.35rem; letter-spacing:0.05em; }
  .stars { text-align:center; color: var(--accent); font-size:0.8rem; margin: 0.5rem 0; letter-spacing:0.4em; }
  hr { border:none; border-top:1px dashed var(--line); margin: 1.1rem 0; }
  .row { display:flex; justify-content:space-between; gap:0.75rem; font-size:0.8rem; padding:0.2rem 0; }
  .row .label { color: var(--ink); }
  .row .value { font-weight:700; font-variant-numeric: tabular-nums; }
  .total {
    display:flex; justify-content:space-between; align-items:baseline;
    font-size:1.05rem; font-weight:800; letter-spacing:0.05em;
    border-top: 2px solid var(--ink); border-bottom: 2px solid var(--ink);
    padding: 0.6rem 0; margin: 1rem 0; text-transform:uppercase;
  }
  .total .value { color: var(--accent); font-size:1.3rem; }
  table { width:100%; table-layout:fixed; border-collapse:collapse; font-size:0.65rem; }
  th, td { text-align:left; padding:0.3rem 0.2rem; border-bottom:1px dotted var(--line); overflow-wrap:break-word; }
  col.c-topic { width:24%; }
  col.c-sess  { width:12%; }
  col.c-pct   { width:14%; }
  col.c-deliv { width:50%; }
  th { font-weight:700; color: var(--muted); text-transform:uppercase; font-size:0.58rem; letter-spacing:0.02em; }
  th.num { white-space:nowrap; }
  td.num, th.num { text-align:right; }
  td.num { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .barcode {
    height: 36px; margin: 1.25rem 0 0.75rem;
    background: repeating-linear-gradient(90deg, var(--ink) 0 2px, transparent 2px 4px, var(--ink) 4px 5px, transparent 5px 9px, var(--ink) 9px 12px, transparent 12px 14px);
    opacity: 0.85;
  }
  .footer { text-align:center; font-size:0.65rem; color:var(--muted); line-height:1.6; }
  .actions { margin-top: 0.9rem; text-align: center; }
  .export {
    font: inherit; font-size: 0.62rem; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--muted); background: none; cursor: pointer;
    border: 1px dashed var(--line); border-radius: 2px; padding: 0.4rem 0.9rem;
  }
  .export:hover { color: var(--ink); border-color: var(--muted); }
  .export:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  @media print {
    body { background: #fff; padding: 0; display: block; }
    .receipt-wrap { filter: none; max-width: none; }
    .receipt { -webkit-mask: none; mask: none; padding: 0; }
    tr, .row { break-inside: avoid; }
    .actions { display: none; }
  }
  .note { font-size:0.68rem; color:var(--muted); line-height:1.5; margin-top:0.4rem; }
"""


def render_html(data, generated_at):
    headline_rows = "\n".join(
        '    <div class="row"><span class="label">%s</span><span class="value">%s</span></div>'
        % (esc_html(h["label"]), esc_html(h["value"]))
        for h in data["headline"]
    )

    table_rows = "\n".join(
        "      <tr>\n"
        "        <td>%s</td>\n"
        '        <td class="num">%s</td>\n'
        '        <td class="num">%s%%</td>\n'
        "        <td>%s</td>\n"
        "      </tr>" % (esc_html(t["name"]), t["sessions"], t["pct"], esc_html(t["deliverables"]))
        for t in data["topics"]
    )

    notes_html = ""
    for n in data.get("table_notes", []):
        notes_html += '    <div class="note">%s</div>\n' % esc_html(n)
    if data.get("footer_note"):
        notes_html += '    <div class="note">%s</div>\n' % esc_html(data["footer_note"])

    csv_lines = ["Topic,Sessions,% of Sessions,Deliverables"]
    for t in data["topics"]:
        csv_lines.append(
            ",".join([
                esc_csv_field(t["name"]),
                str(t["sessions"]),
                str(t["pct"]),
                esc_csv_field(t["deliverables"]),
            ])
        )
    csv_body = "\\r\\n".join(csv_lines)
    csv_js = csv_body.replace("\\", "\\\\").replace('"', '\\"')
    # undo the double-escape on the deliberate \r\n separators
    csv_js = csv_js.replace("\\\\r\\\\n", "\\r\\n")

    safe_period = esc_html(data["period_label"])
    safe_name = esc_html(data["user_name"])
    total = data["total_metric"]

    csv_filename = "cowork-receipt.csv"
    if "period_label" in data:
        csv_filename = "cowork-receipt.csv"

    html = []
    html.append("<!doctype html>")
    html.append('<html lang="en">')
    html.append("<head>")
    html.append('<meta charset="utf-8">')
    html.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    html.append("<title>Cowork Receipt — %s</title>" % safe_period)
    html.append("<style>%s</style>" % CSS)
    html.append("</head>")
    html.append("<body>")
    html.append('  <div class="receipt-wrap">')
    html.append('  <div class="receipt">')
    html.append("    <h1>Cowork</h1>")
    html.append('    <div class="stars">★ ★ ★ ★ ★</div>')
    html.append('    <div class="sub">USAGE RECEIPT — %s</div>' % safe_name)
    html.append('    <div class="sub">%s</div>' % safe_period)
    html.append("    <hr>")
    html.append(headline_rows)
    html.append("")
    html.append(
        '    <div class="total"><span>%s</span><span class="value">%s</span></div>'
        % (esc_html(total["label"]), esc_html(total["value"]))
    )
    if data.get("total_note"):
        html.append('    <div class="note">%s</div>' % esc_html(data["total_note"]))
    html.append("")
    html.append("    <h2>By topic</h2>")
    html.append("    <table>")
    html.append("      <colgroup>")
    html.append('        <col class="c-topic"><col class="c-sess"><col class="c-pct"><col class="c-deliv">')
    html.append("      </colgroup>")
    html.append(
        '      <thead><tr><th>Topic</th><th class="num">Sess</th>'
        '<th class="num">%</th><th>Deliverables</th></tr></thead>'
    )
    html.append("      <tbody>")
    html.append(table_rows)
    html.append("      </tbody>")
    html.append("    </table>")
    html.append(notes_html.rstrip("\n"))
    html.append("")
    html.append('    <div class="actions">')
    html.append('      <button type="button" class="export" id="export-csv">Export CSV</button>')
    html.append("    </div>")
    html.append("")
    html.append('    <div class="barcode"></div>')
    html.append('    <div class="footer">')
    html.append(
        "      Built on this machine from %s local Cowork session files —<br>"
        % data["session_count"]
    )
    html.append("      counts and topic names only, no code or conversation content.<br>")
    html.append("      %s" % generated_at)
    html.append("    </div>")
    html.append("  </div>")
    html.append("  </div>")
    html.append("<script>")
    html.append("(function () {")
    html.append('  var csv = "%s";' % csv_js)
    html.append('  var name = "%s";' % csv_filename)
    html.append("  var btn = document.getElementById('export-csv');")
    html.append("  if (!btn) return;")
    html.append("  btn.addEventListener('click', function () {")
    html.append("    var blob = new Blob(['\\ufeff' + csv], { type: 'text/csv;charset=utf-8' });")
    html.append("    var url = URL.createObjectURL(blob);")
    html.append("    var a = document.createElement('a');")
    html.append("    a.href = url;")
    html.append("    a.download = name;")
    html.append("    document.body.appendChild(a);")
    html.append("    a.click();")
    html.append("    document.body.removeChild(a);")
    html.append("    setTimeout(function () { URL.revokeObjectURL(url); }, 0);")
    html.append("  });")
    html.append("})();")
    html.append("</script>")
    html.append("</body>")
    html.append("</html>")
    return "\n".join(html) + "\n"


def main():
    if len(sys.argv) < 3:
        print("Usage: render_receipt.py data.json output_basename")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        data = json.load(f)
    base = sys.argv[2]

    generated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    with open(base + ".md", "w", encoding="utf-8") as f:
        f.write(render_md(data))

    with open(base + ".html", "w", encoding="utf-8") as f:
        f.write(render_html(data, generated_at))

    print(f"Wrote {base}.md and {base}.html")


if __name__ == "__main__":
    main()
