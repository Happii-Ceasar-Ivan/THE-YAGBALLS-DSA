# src/reports.py
"""
reports.py
Responsible for generating console summary reports and exporting CSVs for:
 - per-section processed records
 - at-risk students list (by grade and/or attendance)

Assumes each record looks like:
{
  "student_id": str,
  "last_name": str,
  "first_name": str,
  "section": str,
  "quiz1"..."quiz5": float | None,
  "midterm": float | None,
  "final": float | None,
  "attendance_percent": float | None,
  "final_grade": float | None,
  "letter_grade": str | None
}
"""

from __future__ import annotations
import csv
import os
import math
import statistics
from typing import List, Dict, Any, Optional
#inserted for designs
from rich.console import Console
from rich.panel import Panel
from rich.align import Align

Student = Dict[str, Any]
SectionStats = Dict[str, Any]
CONSOLE = Console()

# ---------- Utilities ----------
def safe_mean(values: List[float]) -> Optional[float]:
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None


def percentile(values: List[float], p: float) -> Optional[float]:
    vals = sorted([v for v in values if v is not None])
    if not vals:
        return None
    k = (len(vals) - 1) * (p / 100)
    f, c = math.floor(k), math.ceil(k)
    if f == c:
        return vals[int(k)]
    return vals[f] * (c - k) + vals[c] * (k - f)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


# ---------- Grouping ----------
def group_by_section(records: List[Student]) -> Dict[str, List[Student]]:
    sections: Dict[str, List[Student]] = {}
    for r in records:
        sec = (r.get("section") or "").strip() or "UNSPECIFIED"
        sections.setdefault(sec, []).append(r)
    return sections


# ---------- Section statistics ----------
def compute_section_stats(records: List[Student]) -> SectionStats:
    finals = [r.get("final_grade") for r in records]
    attendance = [r.get("attendance_percent") for r in records]

    stats: SectionStats = {
        "count": len(records),
        "avg_final": safe_mean(finals),
        "min_final": min((v for v in finals if v is not None), default=None),
        "max_final": max((v for v in finals if v is not None), default=None),
        "median_final": statistics.median([v for v in finals if v is not None]) if any(finals) else None,
        "p25_final": percentile(finals, 25),
        "p50_final": percentile(finals, 50),
        "p75_final": percentile(finals, 75),
        "avg_attendance": safe_mean(attendance),
        "attendance_missing": sum(1 for v in attendance if v is None),
    }

    dist: Dict[str, int] = {}
    for r in records:
        letter = r.get("letter_grade") or "N/A"
        dist[letter] = dist.get(letter, 0) + 1
    stats["letter_distribution"] = dist
    return stats


# ---------- Console printing ---------- edited na to for rich 
def print_section_summary(section_name: str, stats: SectionStats) -> None:
    """Prints a detailed, rich-formatted summary for a single section."""
    
    content = []
    
    # Header Info
    content.append(f"[bold cyan]Total Students:[/bold cyan] {stats.get('count', 0)}")
    
    # Grade Summary
    content.append("\n[bold underline magenta]Grade Performance[/bold underline magenta]")
    content.append(f"Average Final: [green]{fmt(stats['avg_final'])}[/green] | Median: [green]{fmt(stats['median_final'])}[/green]")
    content.append(f"Min: {fmt(stats['min_final'])} | Max: {fmt(stats['max_final'])}")
    
    p25 = fmt(stats['p25_final'])
    p50 = fmt(stats['p50_final'])
    p75 = fmt(stats['p75_final'])
    content.append(f"Percentiles (Q1/Median/Q3): [yellow]{p25}[/yellow] / [green]{p50}[/green] / [yellow]{p75}[/yellow]")
    
    # Attendance Summary
    avg_att = fmt(stats['avg_attendance'])
    missing_att = stats['attendance_missing']
    content.append("\n[bold underline magenta]Attendance[/bold underline magenta]")
    content.append(f"Avg Attendance: {avg_att}% ([red]Missing Data:[/red] {missing_att})")
    
    # Letter Grade Distribution
    dist_lines = ["\n[bold underline magenta]Letter Grade Distribution[/bold underline magenta]"]
    distribution = sorted(stats["letter_distribution"].items(), key=lambda item: item[0], reverse=True)
    
    for letter, count in distribution:
        dist_lines.append(f"  [bold]{letter:>3}:[/bold] {count}")

    # Combine content and print inside a rich Panel
    CONSOLE.print(
        Panel(
            "\n".join(content + dist_lines),
            title=f"[gold1]SECTION REPORT: {section_name}[/gold1]",
            border_style="cyan"
        )
    )

def fmt(v: Optional[float]) -> str:
    """Helper function to format float or return 'N/A'."""
    return "N/A" if v is None else f"{v:.2f}"

#edited na din to for rich
def print_summary_report(all_records: List[Student]) -> None:
    """Prints the overall academic analytics summary using rich formatting."""
    
    CONSOLE.print(
        Panel(
            Align.center("[bold cyan underline]ACADEMIC ANALYTICS SUMMARY REPORT[/bold cyan underline]"),
            border_style="gold1"
        )
    )
    
    sections = group_by_section(all_records)
    
    CONSOLE.print("\n[bold underline]--- Individual Section Summaries ---[/bold underline]\n")
    
    # Print summaries for individual sections
    for sec, recs in sorted(sections.items()):
        stats = compute_section_stats(recs)
        print_section_summary(sec, stats)
        CONSOLE.print("\n") # Add space between sections
        
    # Print overall summary
    CONSOLE.print("[bold underline]=== OVERALL ACADEMIC SUMMARY (ALL SECTIONS) ===[/bold underline]")
    overall_stats = compute_section_stats(all_records)
    print_section_summary("ALL SECTIONS COMBINED", overall_stats)


# ---------- CSV Export ----------
DEFAULT_FIELDS = [
    "student_id", "last_name", "first_name", "section",
    "quiz1", "quiz2", "quiz3", "quiz4", "quiz5",
    "midterm", "final", "attendance_percent",
    "final_grade", "letter_grade"
]


def export_section_csv(section_name: str, records: List[Student], folder: str) -> str:
    ensure_dir(folder)
    safe_name = "".join(ch for ch in section_name if ch.isalnum() or ch in " _-").strip()
    path = os.path.join(folder, f"section_{safe_name.replace(' ', '_')}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DEFAULT_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for r in records:
            row = {k: ("" if r.get(k) is None else r.get(k)) for k in DEFAULT_FIELDS}
            writer.writerow(row)
    return path


def export_all_sections(sections: Dict[str, List[Student]], folder: str) -> List[str]:
    ensure_dir(folder)
    return [export_section_csv(sec, recs, folder) for sec, recs in sections.items()]


# ---------- At-risk handling ----------
def identify_at_risk(records: List[Student], grade_thr: float, att_thr: float) -> List[Student]:
    at_risk = []
    for r in records:
        fg = r.get("final_grade")
        att = r.get("attendance_percent")
        if (fg is not None and fg < grade_thr) or (att is not None and att < att_thr):
            at_risk.append(r)
    return at_risk


def export_at_risk_csv(at_risk: List[Student], path: str) -> str:
    ensure_dir(os.path.dirname(path) or ".")
    fields = ["student_id", "last_name", "first_name", "section", "final_grade", "letter_grade", "attendance_percent"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for r in at_risk:
            row = {k: ("" if r.get(k) is None else r.get(k)) for k in fields}
            writer.writerow(row)
    return path


# ---------- Main entry ----------
def generate_reports(all_records: List[Student], config: Dict[str, Any]) -> Dict[str, Any]:
    out_dir = config.get("output_folder", "./reports")
    sections_dir = config.get("sections_folder", os.path.join(out_dir, "sections"))
    at_risk_file = config.get("at_risk_file", os.path.join(out_dir, "at_risk.csv"))
    grade_thr = config.get("grade_threshold", 75)
    att_thr = config.get("attendance_threshold", 80)

    ensure_dir(out_dir)
    sections = group_by_section(all_records)

    print_summary_report(all_records)

    written_sections = export_all_sections(sections, sections_dir)
    at_risk = identify_at_risk(all_records, grade_thr, att_thr)
    at_risk_path = export_at_risk_csv(at_risk, at_risk_file)

    print(f"\nGenerated {len(written_sections)} section reports and {len(at_risk)} at-risk entries.\n")

    return {
        "written_section_files": written_sections,
        "at_risk_file": at_risk_path,
        "num_at_risk": len(at_risk),
        "sections": {sec: compute_section_stats(recs) for sec, recs in sections.items()}
    }


# ---------- Demo run ----------
if __name__ == "__main__":
    # This is a demo to verify reports.py works independently.
    import json

    sample_data = [
        {"student_id": "2024001", "last_name": "Smith", "first_name": "John", "section": "A",
         "quiz1": 85, "quiz2": 78, "quiz3": 92, "quiz4": 88, "quiz5": 75,
         "midterm": 82, "final": 89, "attendance_percent": 95,
         "final_grade": 84.0, "letter_grade": "B"},
        {"student_id": "2024002", "last_name": "Johnson", "first_name": "Emily", "section": "B",
         "quiz1": 91, "quiz2": 89, "quiz3": 85, "quiz4": 94, "quiz5": 80,
         "midterm": 88, "final": 92, "attendance_percent": 98,
         "final_grade": 90.0, "letter_grade": "A"},
    ]

    demo_config = {
        "output_folder": "./demo_reports",
        "grade_threshold": 75,
        "attendance_threshold": 80
    }

    summary = generate_reports(sample_data, demo_config)
    print(json.dumps(summary, indent=2))

