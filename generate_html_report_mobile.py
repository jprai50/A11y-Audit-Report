import csv
import html
import re
from pathlib import Path

ROOT = Path(__file__).parent
CSV_PATH = ROOT / "issues.csv"
OUT_PATH = ROOT / "Mobile_App_Accessibility_Audit_Report.html"
IMPACT_ORDER = ["Critical", "Serious", "Moderate", "Minor"]
SUCCESS_CRITERIA_MAPPING = {
    "1.1.1": "1.1.1 Non-Text Content",
    "1.2.1": "1.2.1 Audio-Only and Video-Only",
    "1.2.2": "1.2.2 Captions (Prerecorded)",
    "1.2.3": "1.2.3 Audio Description or Media Alternative",
    "1.2.4": "1.2.4 Captions (Live)",
    "1.2.5": "1.2.5 Audio Description (Pre-Recorded)",
    "1.3.1": "1.3.1 Info and Relationships",
    "1.3.2": "1.3.2 Meaningful Sequence",
    "1.3.3": "1.3.3 Sensory Characteristics",
    "1.3.4": "1.3.4 Orientation",
    "1.3.5": "1.3.5 Identify Input Purpose",
    "1.4.1": "1.4.1 Use of Color",
    "1.4.2": "1.4.2 Audio Control",
    "1.4.3": "1.4.3 Contrast Minimum",
    "1.4.4": "1.4.4 Resize Text",
    "1.4.5": "1.4.5 Images of Text",
    "1.4.10": "1.4.10 Reflow",
    "1.4.11": "1.4.11 Non-Text Contrast",
    "1.4.12": "1.4.12 Text Spacing",
    "1.4.13": "1.4.13 Content on Hover or Focus",
    "2.1.1": "2.1.1 Keyboard",
    "2.1.2": "2.1.2 No Keyboard Trap",
    "2.1.4": "2.1.4 Character Key Shortcuts",
    "2.2.1": "2.2.1 Timing Adjustable",
    "2.2.2": "2.2.2 Pause, Stop, Hide",
    "2.3.1": "2.3.1 Three Flashes or Below",
    "2.4.1": "2.4.1 Bypass Blocks",
    "2.4.2": "2.4.2 Page Titled",
    "2.4.3": "2.4.3 Focus Order",
    "2.4.4": "2.4.4 Link Purpose (In Context)",
    "2.4.5": "2.4.5 Multiple Ways",
    "2.4.6": "2.4.6 Headings and Labels",
    "2.4.7": "2.4.7 Focus Visible",
    "2.4.11": "2.4.11 Focus Not Obscured",
    "2.5.1": "2.5.1 Pointer Gestures",
    "2.5.2": "2.5.2 Pointer Cancellation",
    "2.5.3": "2.5.3 Label in Name",
    "2.5.4": "2.5.4 Motion Actuation",
    "2.5.5": "2.5.5 Target Size",
    "2.5.7": "2.5.7 Dragging Movements",
    "2.5.8": "2.5.8 Target Size",
    "3.1.1": "3.1.1 Language of Page",
    "3.1.2": "3.1.2 Language of Parts",
    "3.2.1": "3.2.1 On Focus",
    "3.2.2": "3.2.2 On Input",
    "3.2.3": "3.2.3 Consistent Navigation",
    "3.2.4": "3.2.4 Consistent Identification",
    "3.2.6": "3.2.6 Consistent Help",
    "3.3.1": "3.3.1 Error Identification",
    "3.3.2": "3.3.2 Labels or Instruction",
    "3.3.3": "3.3.3 Error Suggestion",
    "3.3.4": "3.3.4 Error Prevention (Legal, Financial, Data)",
    "3.3.7": "3.3.7 Redundant Entry",
    "3.3.8": "3.3.8 Accessible Authentication",
    "4.1.2": "4.1.2 Name, Role, Value",
    "4.1.3": "4.1.3 Status Messages",
}


def esc(value: str) -> str:
    return html.escape((value or "").strip())


def extract_urls(text: str):
    if not text:
        return []
    return re.findall(r"https?://[^\s,]+", text)


def format_recommended_fix(text: str) -> str:
    value = (text or "").strip()
    if not value:
        return '<span class="empty">Not provided</span>'

    escaped = html.escape(value)
    escaped = re.sub(
        r"(?i)\bREFERENCE\s*:",
        '<span class="fix-section-label">REFERENCE:</span>',
        escaped,
    )
    escaped = re.sub(
        r"(?i)\bBACKGROUND\s*:",
        '<span class="fix-section-label">BACKGROUND:</span>',
        escaped,
    )
    return linkify_escaped_https(escaped)


def linkify_escaped_https(text: str) -> str:
    if not text:
        return text

    url_re = re.compile(r"https://[^\s<]+")

    def repl(match):
        url = match.group(0)
        trailing = ""
        while url and url[-1] in ".,);":
            trailing = url[-1] + trailing
            url = url[:-1]
        return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a>{trailing}'

    return url_re.sub(repl, text)


def format_success_criteria_label(code: str) -> str:
    key = (code or "").strip()
    mapped = SUCCESS_CRITERIA_MAPPING.get(key, key)
    if mapped.startswith(key + " "):
        return f"{mapped[len(key) + 1:]} ({key})"
    return mapped


def screenshot_position_label(position: int) -> str:
    labels = {
        1: "first",
        2: "second",
        3: "third",
        4: "fourth",
        5: "fifth",
        6: "sixth",
        7: "seventh",
        8: "eighth",
        9: "ninth",
        10: "tenth",
    }
    if position in labels:
        return labels[position]
    return f"{position}th"


issues_by_impact = {k: [] for k in IMPACT_ORDER}
success_criteria_counts = {}
total_issues_count = 0

with CSV_PATH.open(newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        total_issues_count += 1
        impact = (row.get("Impact") or "").strip().title()
        sc = (row.get("Success Criteria") or "").strip()
        if sc:
            success_criteria_counts[sc] = success_criteria_counts.get(sc, 0) + 1
        if impact not in issues_by_impact:
            continue
        issues_by_impact[impact].append(row)

parts = []
parts.append("<!doctype html>")
parts.append('<html lang="en">')
parts.append("<head>")
parts.append('  <meta charset="UTF-8" />')
parts.append('  <meta name="viewport" content="width=device-width, initial-scale=1.0" />')
parts.append("  <title>Welcome back | Accessibility Audit Report</title>")
parts.append("  <style>")
parts.append('    body { font-family: "Segoe UI", Arial, sans-serif; background: #f7f7f7; margin: 0; padding: 0; }')
parts.append('    .container { max-width: 980px; margin: 32px auto; background: #fff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); padding: 28px; }')
parts.append("    h1 { color: #004e9a; margin: 0 0 24px; }")
parts.append("    .accordion { margin-bottom: 16px; }")
parts.append("    .accordion-header { width: 100%; background: #e9f1fb; color: #004e9a; padding: 14px 16px; cursor: pointer; border-radius: 8px; font-size: 1.05em; font-weight: 700; border: 1px solid #014E9A; display: flex; align-items: center; gap: 10px; }")
parts.append("    .accordion-title { flex: 1; text-align: left; }")
parts.append("    .accordion-count { font-size: 0.92em; color: #5a6570; }")
parts.append("    .caret { transition: transform 0.2s; display: inline-block; }")
parts.append("    .caret.rotate { transform: rotate(90deg); }")
parts.append("    .accordion-content { display: none; margin-top: 8px; padding: 14px; border: 1px solid #c7e0f7; border-radius: 8px; background: #f5faff; }")
parts.append("    .accordion-content.open { display: block; }")
parts.append("    .severity-header { width: 100%; background: #e9f1fb; color: #004e9a; padding: 14px 16px; border-radius: 8px; font-size: 1.05em; font-weight: 700; border: 1px solid #014E9A; display: flex; align-items: center; gap: 10px; }")
parts.append("    .severity-caret { border: 0; background: transparent; color: #004e9a; cursor: pointer; padding: 0; display: inline-flex; align-items: center; }")
parts.append("    .severity-caret:focus-visible { outline: 2px solid #004e9a; outline-offset: 2px; border-radius: 4px; }")
parts.append("    .issue { margin-bottom: 20px; padding: 14px; border: 1px solid #d9e7f7; border-radius: 8px; background: #fff; }")
parts.append("    .issue:last-child { margin-bottom: 0; }")
parts.append("    .issue-number { font-size: 1.4em; line-height: 1.2; color: #003b75; font-weight: 800; margin: 2px 0 12px; padding-bottom: 6px; border-bottom: 2px solid darkgray; letter-spacing: 0.2px; }")
parts.append("    .criteria-chart-section { margin: 4px 0 28px; }")
parts.append("    .criteria-chart-title { color: #2a2a2a; font-size: 1.5em; font-weight: 700; margin: 0 0 12px; }")
parts.append("    .issue-total-label { font-size: 1em; font-weight: 700; padding-bottom: 2em; }")
parts.append("    .report-details { background: #f8fbff; border: 1px solid #c7e0f7; border-radius: 8px; padding: 12px 14px; margin: 0 0 18px; }")
parts.append("    .report-details p { margin: 6px 0; color: #2a2a2a; }")
parts.append("    .report-details strong { color: #003b75; }")
parts.append("    .criteria-chart-row { display: grid; grid-template-columns: minmax(210px, 360px) 1fr; gap: 14px; align-items: center; margin-bottom: 8px; }")
parts.append("    .criteria-chart-label { text-align: right; color: #333; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }")
parts.append("    .criteria-chart-x { display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 8px; }")
parts.append("    .criteria-chart-bar-wrap { width: 100%; background: #e6e6e6; border-radius: 3px; overflow: hidden; border: 1px solid #d1d1d1; }")
parts.append("    .criteria-chart-bar { height: 24px; background: #127ac0; }")
parts.append("    .criteria-chart-count { color: #127ac0; font-weight: 700; font-size: 1.85em; line-height: 1; min-width: 24px; text-align: right; }")
parts.append("    .criteria-chart-axis { font-size: 0.88em; color: #666; margin-top: 6px; text-align: right; }")
parts.append("    .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }")
parts.append("    .label { font-weight: 700; color: #2a2a2a; display: block; margin-top: 8px; }")
parts.append("    .source-code, .recommended-fix, .description { white-space: pre-wrap; line-height: 1.4; }")
parts.append("    .source-code { background: #202225; color: #f2f2f2; padding: 10px; border-radius: 6px; overflow-x: auto; }")
parts.append("    .recommended-fix { background: #fffbe6; border-left: 4px solid #ffe066; padding: 10px 12px; border-radius: 4px; }")
parts.append("    .recommended-fix .fix-section-label { display: block; margin-top: 12px; font-weight: 700; color: #2a2a2a; }")
parts.append("    a { color: #126fbd; text-decoration: underline; }")
parts.append("    .screenshots img { max-width: 320px; width: 100%; height: auto; margin: 8px 8px 0 0; border: 1px solid #cfd8e3; border-radius: 6px; background: #fff; }")
parts.append("    .empty { color: #606c78; font-style: italic; }")
parts.append("    .impact-issues-section { padding-top:1.5em; }")
parts.append("    .severity-section { margin-top: 28px; }")
parts.append("    .severity-table { width: 100%; border-collapse: collapse; table-layout: fixed; }")
parts.append("    .severity-table td { border: 1px solid #b8c7d6; padding: 10px; vertical-align: top; color: #2a2a2a; line-height: 1.35; }")
parts.append("    .severity-label { width: 130px; font-weight: 700; text-align: center; background: #f2f7fc; }")
parts.append("  </style>")
parts.append("</head>")
parts.append("<body>")
parts.append("<main>")
parts.append('  <div class="container">')
parts.append("    <h1>iOS- Welcome back- Accessibility Audit Report</h1>")
parts.append('    <section class="report-details" aria-label="Testing details">')
parts.append('      <p><strong>Application:</strong> <a href="https://apps.apple.com/ai/app/weather-the-weather-channel/id295646461" target="_blank" rel="noopener noreferrer">The Weather Channel iOS Mobile App</a></p>')
parts.append('      <p><strong>Scope Of Testing:</strong> Welcome back view</p>')
parts.append('      <p><strong>Accessibility Testing Standard:</strong> WCAG 2.2 Level AA</p>')
parts.append('      <p><strong>Digital asset type:</strong> iOS mobile app</p>')
parts.append('      <p><strong>Assistive technology:</strong> VoiceOver (iOS), Voice Control (iOS)</p>')
parts.append('      <p><strong>iOS Version:</strong> 18.3.1</p>')
parts.append('    </section>')
if success_criteria_counts:
    sorted_criteria = sorted(success_criteria_counts.items(), key=lambda item: (-item[1], item[0]))
    max_count = max(success_criteria_counts.values())
    parts.append('    <section class="criteria-chart-section" aria-label="Success criteria distribution">')
    parts.append('      <h2 class="criteria-chart-title">Success Criteria Distribution</h2>')
    parts.append(f'      <p class="issue-total-label">Total {total_issues_count} issues found in the audit across different success criteria</p>')
    for code, count in sorted_criteria:
        width_pct = (count / max_count) * 100 if max_count else 0
        label = esc(format_success_criteria_label(code))
        parts.append('      <div class="criteria-chart-row">')
        parts.append(f'        <div class="criteria-chart-label" title="{label}">{label}</div>')
        parts.append('        <div class="criteria-chart-x">')
        parts.append('          <div class="criteria-chart-bar-wrap">')
        parts.append(f'            <div class="criteria-chart-bar" style="width: {width_pct:.2f}%"></div>')
        parts.append('          </div>')
        parts.append(f'          <div class="criteria-chart-count" aria-label="Count {count}">{count}</div>')
        parts.append('        </div>')
        parts.append('      </div>')
    parts.append('    </section>')

parts.append('    <section class="impact-issues-section" aria-label="Issue details grouped by impact level">')
parts.append('    <h2>Issue details grouped by impact level</h2>')

for impact in IMPACT_ORDER:
    issues = issues_by_impact.get(impact, [])
    impact_id = impact.lower()
    parts.append('    <div class="accordion">')
    parts.append(
        f'      <button class="accordion-header" type="button" aria-expanded="false" aria-controls="{impact_id}-content" id="{impact_id}-header">'
    )
    parts.append(f'        <span class="accordion-title">{esc(impact)}</span>')
    parts.append(f'        <span class="accordion-count">({len(issues)} issue{"s" if len(issues) != 1 else ""})</span>')
    parts.append('        <span class="caret">&#9654;</span>')
    parts.append("      </button>")
    parts.append(f'      <div class="accordion-content" id="{impact_id}-content" aria-labelledby="{impact_id}-header">')

    if not issues:
        parts.append('        <div class="empty">No issues found for this impact level.</div>')
    else:
        for idx, issue in enumerate(issues, start=1):
            page_name = esc(issue.get("Test Unit", ""))
            summary = esc(issue.get("Summary", ""))
            description = esc(issue.get("Description", ""))
            issue_type_raw = (issue.get("Issue Type", "") or "").strip()
            digital_asset_raw = (
                issue.get("Digital asset", "")
                or issue.get("Digital asset type", "")
                or ""
            ).strip()
            success_criteria = esc(issue.get("Success Criteria", ""))
            source_code = esc(issue.get("Source Code", ""))
            recommended_fix = issue.get("Recommended to fix", "")
            page_name_html = page_name if page_name else '<span class="empty">Not provided</span>'
            summary_html = summary if summary else '<span class="empty">Not provided</span>'
            description_html = description if description else '<span class="empty">Not provided</span>'
            success_criteria_html = success_criteria if success_criteria else '<span class="empty">Not provided</span>'
            recommended_fix_html = format_recommended_fix(recommended_fix)
            summary_html = linkify_escaped_https(summary_html)
            description_html = linkify_escaped_https(description_html)
            success_criteria_html = linkify_escaped_https(success_criteria_html)
            source_code_html = linkify_escaped_https(source_code) if source_code else "Not provided"
            should_show_source_code = digital_asset_raw.lower() != "native mobile ios"
            screenshot_text = issue.get("Screenshots", "") or ""
            urls = extract_urls(screenshot_text)

            parts.append('        <div class="issue">')
            parts.append(
                f'          <div class="issue-number" role="heading" aria-level="2"><span class="sr-only">{esc(impact)} </span>Issue {idx}</div>'
            )
            parts.append('          <span class="label">Page/Component Name</span>')
            parts.append("          <div>" + page_name_html + "</div>")
            parts.append('          <span class="label">Summary</span>')
            parts.append("          <div>" + summary_html + "</div>")
            parts.append('          <span class="label">Description</span>')
            parts.append('          <div class="description">' + description_html + '</div>')
            if issue_type_raw.lower() == "best practice":
                parts.append('          <span class="label">Issue Type</span>')
                parts.append('          <div>Best Practice</div>')
            parts.append('          <span class="label">Success Criteria</span>')
            parts.append("          <div>" + success_criteria_html + "</div>")
            parts.append('          <span class="label">Screenshot</span>')
            if urls:
                parts.append('          <div class="screenshots">')
                for screenshot_index, url in enumerate(urls, start=1):
                    safe_url = esc(url)
                    screenshot_position = screenshot_position_label(screenshot_index)
                    screenshot_alt = esc(f"{impact} Issue {idx} {screenshot_position} screenshot")
                    parts.append(f'            <a href="{safe_url}" target="_blank" rel="noopener noreferrer"><img src="{safe_url}" alt="{screenshot_alt}" loading="lazy" /></a>')
                parts.append("          </div>")
            else:
                parts.append('          <div class="empty">No screenshot URL provided</div>')
            if should_show_source_code:
                parts.append('          <span class="label">Source Code</span>')
                parts.append(f'          <pre class="source-code">{source_code_html}</pre>')
            parts.append('          <span class="label">Recommended Fix</span>')
            parts.append('          <div class="recommended-fix">' + recommended_fix_html + '</div>')
            parts.append("        </div>")

    parts.append("      </div>")
    parts.append("    </div>")

parts.append('    </section>')

parts.append('    <section class="severity-section" aria-label="Severity description">')
parts.append('    <h2>Severity Description</h2>')
parts.append('      <div class="accordion">')
parts.append('        <button class="accordion-header" type="button" aria-expanded="false" aria-controls="severity-content" id="severity-header">')
parts.append('          <span class="accordion-title">User Impact</span>')
parts.append('          <span class="caret">&#9654;</span>')
parts.append('        </button>')
parts.append('        <div class="accordion-content" id="severity-content" aria-labelledby="severity-header">')
parts.append('          <table class="severity-table">')
parts.append('            <tbody>')
parts.append('              <tr>')
parts.append('                <td class="severity-label">Blocker</td>')
parts.append('                <td>These issues are showstoppers and result in catastrophic roadblocks for people with disabilities. These issues will definitely prevent people from accessing fundamental features or content, with no possible workarounds. This type of issue puts your organization at high risk. Prioritize fixing immediately, and deploy hotfixes as soon as possible. Should be extremely rare. An example of a blocker issue is a SC 2.3.1 - Three Flashes or Below Threshold which can cause seizures.</td>')
parts.append('              </tr>')
parts.append('              <tr>')
parts.append('                <td class="severity-label">Critical</td>')
parts.append('                <td>This issue results in blocked content for people with disabilities, and will definitely prevent them from accessing fundamental features or content. This type of issue puts your organization at risk. Prioritize fixing as soon as possible, within the week if possible. Remediation should be a top priority. Should be infrequent.</td>')
parts.append('              </tr>')
parts.append('              <tr>')
parts.append('                <td class="severity-label">Serious</td>')
parts.append('                <td>This issue results in serious barriers for people with disabilities, and will partially prevent them from accessing fundamental features or content. People relying on assistive technologies will experience significant frustration as a result. Issues falling under this category are major problems, and remediation should be a priority. Should be very common.</td>')
parts.append('              </tr>')
parts.append('              <tr>')
parts.append('                <td class="severity-label">Moderate</td>')
parts.append('                <td>This issue results in some barriers for people with disabilities, but will not prevent them from accessing fundamental features or content. Prioritize fixing in this release, if there are no higher-priority issues. Will get in the way of compliance if not fixed. Should be fairly common.</td>')
parts.append('              </tr>')
parts.append('              <tr>')
parts.append('                <td class="severity-label">Minor</td>')
parts.append('                <td>Considered to be a nuisance or an annoyance bug. Prioritize fixing if the fix only takes a few minutes and the developer is working on the same screen/feature at the same time, otherwise the issue should not be prioritized. Will still get in the way of compliance if not fixed. Should be very infrequent.</td>')
parts.append('              </tr>')
parts.append('            </tbody>')
parts.append('          </table>')
parts.append('        </div>')
parts.append('      </div>')
parts.append('    </section>')

parts.append("  </div>")
parts.append("</main>")
parts.append("  <script>")
parts.append('    document.querySelectorAll(".accordion-header").forEach((header) => {')
parts.append('      const content = document.getElementById(header.getAttribute("aria-controls"));')
parts.append('      const caret = header.querySelector(".caret");')
parts.append('      const toggle = () => {')
parts.append('        const expanded = header.getAttribute("aria-expanded") === "true";')
parts.append('        header.setAttribute("aria-expanded", expanded ? "false" : "true");')
parts.append('        content.classList.toggle("open", !expanded);')
parts.append('        caret.classList.toggle("rotate", !expanded);')
parts.append('      };')
parts.append('      header.addEventListener("click", toggle);')
parts.append('      header.addEventListener("keydown", (e) => {')
parts.append('        if (e.key === "Enter" || e.key === " ") {')
parts.append('          e.preventDefault();')
parts.append('          toggle();')
parts.append('        }')
parts.append('      });')
parts.append('    });')
parts.append('    const severityToggle = document.querySelector(".severity-caret");')
parts.append('    if (severityToggle) {')
parts.append('      const severityContent = document.getElementById(severityToggle.getAttribute("aria-controls"));')
parts.append('      const severityCaret = severityToggle.querySelector(".caret");')
parts.append('      severityToggle.addEventListener("click", () => {')
parts.append('        const expanded = severityToggle.getAttribute("aria-expanded") === "true";')
parts.append('        severityToggle.setAttribute("aria-expanded", expanded ? "false" : "true");')
parts.append('        severityContent.classList.toggle("open", !expanded);')
parts.append('        severityCaret.classList.toggle("rotate", !expanded);')
parts.append('      });')
parts.append('    }')
parts.append("  </script>")
parts.append("</body>")
parts.append("</html>")

OUT_PATH.write_text("\n".join(parts), encoding="utf-8")
print(f"Generated: {OUT_PATH}")
for impact in IMPACT_ORDER:
    print(f"{impact}: {len(issues_by_impact.get(impact, []))}")
