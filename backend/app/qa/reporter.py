import datetime
from typing import Dict, Any, List
from backend.app.llm.base import LLMProvider


class ReportGenerator:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def generate_markdown_report(
        self,
        session_data: Dict[str, Any],
        scenarios: List[Dict[str, Any]],
        findings: List[Dict[str, Any]],
        console_logs: List[Dict[str, Any]],
        network_errors: List[Dict[str, Any]]
    ) -> str:
        """
        Generates a comprehensive Markdown QA Report following the specification standard.
        """
        # Calculate coverage statistics
        total_scenarios = len(scenarios)
        passed_scenarios = len([s for s in scenarios if s.get("status") == "PASSED"])
        failed_scenarios = len([s for s in scenarios if s.get("status") == "FAILED"])
        blocked_scenarios = len([s for s in scenarios if s.get("status") == "BLOCKED"])
        skipped_scenarios = len([s for s in scenarios if s.get("status") == "SKIPPED" or s.get("status") == "PLANNED"])

        areas: Dict[str, Dict[str, int]] = {}
        for s in scenarios:
            area = s.get("area", "General")
            if area not in areas:
                areas[area] = {"total": 0, "tested": 0}
            areas[area]["total"] += 1
            if s.get("status") in ["PASSED", "FAILED", "BLOCKED"]:
                areas[area]["tested"] += 1

        confirmed_bugs = [f for f in findings if f.get("status") == "CONFIRMED" and f.get("type") == "BUG"]
        potential_issues = [f for f in findings if f.get("status") in ["POTENTIAL", "VERIFYING"]]
        missing_funcs = [f for f in findings if f.get("type") == "MISSING_FUNCTIONALITY"]
        ux_issues = [f for f in findings if f.get("type") == "UX_ISSUE"]
        console_findings = [f for f in findings if f.get("type") == "CONSOLE_ERROR"]
        network_findings = [f for f in findings if f.get("type") == "NETWORK_ERROR"]

        md_lines = []
        md_lines.append(f"# QA Autonomous Test Report — Session #{session_data.get('id', '')}")
        md_lines.append("")
        md_lines.append(f"> **Mission**: {session_data.get('mission', '')}")
        md_lines.append(f"> **Generated at**: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        md_lines.append("")

        # 1. Summary Section
        md_lines.append("## 1. Executive Summary")
        md_lines.append("")
        md_lines.append("| Metric | Value |")
        md_lines.append("| :--- | :--- |")
        md_lines.append(f"| **Session Status** | `{session_data.get('status', 'COMPLETED')}` |")
        md_lines.append(f"| **Actions Used** | {session_data.get('actions_used', 0)} / {session_data.get('max_actions', 100)} |")
        md_lines.append(f"| **Total Scenarios** | {total_scenarios} |")
        md_lines.append(f"| **Scenarios Passed** | {passed_scenarios} |")
        md_lines.append(f"| **Scenarios Failed** | {failed_scenarios} |")
        md_lines.append(f"| **Scenarios Blocked** | {blocked_scenarios} |")
        md_lines.append(f"| **Scenarios Skipped** | {skipped_scenarios} |")
        md_lines.append(f"| **Confirmed Bugs** | {len(confirmed_bugs)} |")
        md_lines.append(f"| **Potential Issues** | {len(potential_issues)} |")
        md_lines.append(f"| **AI Calls / Cost** | {session_data.get('ai_calls_count', 0)} calls (${session_data.get('estimated_cost', 0.0):.4f}) |")
        md_lines.append("")

        # 2. Coverage Section
        md_lines.append("## 2. Application Area Coverage")
        md_lines.append("")
        md_lines.append("| Application Area | Tested / Total | Coverage % | Status |")
        md_lines.append("| :--- | :--- | :--- | :--- |")
        for area_name, stats in areas.items():
            pct = (stats["tested"] / stats["total"] * 100) if stats["total"] > 0 else 0
            badge = "✅ Complete" if pct == 100 else ("⚠️ Partial" if pct > 0 else "❌ Untested")
            md_lines.append(f"| **{area_name}** | {stats['tested']} / {stats['total']} | {pct:.1f}% | {badge} |")
        md_lines.append("")

        # 3. Confirmed Bugs
        md_lines.append("## 3. Confirmed Bugs")
        md_lines.append("")
        if confirmed_bugs:
            for b in confirmed_bugs:
                md_lines.append(f"### 🐛 {b.get('title')}")
                md_lines.append(f"- **Severity**: `{b.get('severity')}`")
                md_lines.append(f"- **Status**: `{b.get('status')}` (Verified across {b.get('reproduction_attempts', 2)} attempts)")
                md_lines.append(f"- **Description**: {b.get('description')}")
                md_lines.append(f"- **Expected Behavior**: {b.get('expected_behavior', 'N/A')}")
                md_lines.append(f"- **Actual Behavior**: {b.get('actual_behavior', 'N/A')}")
                md_lines.append("")
                md_lines.append("#### Reproduction Steps")
                md_lines.append("```text")
                md_lines.append(b.get("reproduction_steps", "1. Open app and reproduce scenario."))
                md_lines.append("```")
                md_lines.append("")
        else:
            md_lines.append("_No critical confirmed bugs were detected during this session._")
            md_lines.append("")

        # 4. Missing Functionality
        md_lines.append("## 4. Missing Functionality (PRD Gaps)")
        md_lines.append("")
        if missing_funcs:
            for m in missing_funcs:
                md_lines.append(f"- **{m.get('title')}**: {m.get('description')} (Severity: `{m.get('severity')}`)")
        else:
            md_lines.append("_No missing core functionality gaps detected against provided requirements._")
        md_lines.append("")

        # 5. UX & Usability Issues
        md_lines.append("## 5. UX & Usability Issues")
        md_lines.append("")
        if ux_issues:
            for u in ux_issues:
                md_lines.append(f"- **{u.get('title')}**: {u.get('description')} (Severity: `{u.get('severity')}`)")
        else:
            md_lines.append("_No notable UX degradation or interface state issues observed._")
        md_lines.append("")

        # 6. Console & Network Errors
        md_lines.append("## 6. Runtime Diagnostics")
        md_lines.append("")
        md_lines.append(f"- **Console Exceptions Captured**: {len(console_logs) + len(console_findings)}")
        md_lines.append(f"- **Network HTTP 4xx/5xx Failures**: {len(network_errors) + len(network_findings)}")
        md_lines.append("")
        if console_logs:
            md_lines.append("### Relevant Console Logs")
            md_lines.append("```json")
            import json
            md_lines.append(json.dumps(console_logs[:5], indent=2))
            md_lines.append("```")
            md_lines.append("")
        if network_errors:
            md_lines.append("### Relevant Network Errors")
            md_lines.append("```json")
            import json
            md_lines.append(json.dumps(network_errors[:5], indent=2))
            md_lines.append("```")
            md_lines.append("")

        # 7. Untested / Skipped Scenarios
        md_lines.append("## 7. Untested / Skipped Scenarios")
        md_lines.append("")
        skipped_list = [s for s in scenarios if s.get("status") in ["SKIPPED", "PLANNED", "BLOCKED"]]
        if skipped_list:
            for s in skipped_list:
                md_lines.append(f"- `[{s.get('status')}]` **{s.get('title')}** ({s.get('area')}): {s.get('description')}")
        else:
            md_lines.append("_All planned scenarios were executed successfully within the action budget._")
        md_lines.append("")

        return "\n".join(md_lines)
