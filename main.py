import os
import csv
import json
import time
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from transform import compute_final_grades, assign_letter_grades, apply_grade_curve
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, FloatPrompt
from rich.table import Table
from rich.text import Text
from rich.progress import track
from rich.align import Align
from analyze import compute_stats, detect_outliers, analyze_section # For Analytics Support
from plot import generate_grade_histogram

# Import modules from the project structure
from ingest import ingest_student_data, _parse_and_validate_row
from transform import compute_final_grades, assign_letter_grades
# Import necessary items from reports.py
from reports import print_summary_report, group_by_section, export_section_csv, DEFAULT_FIELDS, generate_reports, ensure_dir 
from analyze import compute_stats, detect_outliers, analyze_section # For Analytics Support

# --- Global Constants and Rich Setup ---
CONSOLE = Console()
CONFIG_FILE = "config.json"
DATA_FOLDER = "." # Search in the current directory

# --- Core Logic Functions ---

def load_config() -> Dict[str, Any]:
    """Loads grading weights and thresholds from config.json."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        CONSOLE.print(f"[red]Error: Configuration file '{CONFIG_FILE}' not found.[/red]")
        return {}
    except json.JSONDecodeError:
        CONSOLE.print(f"[red]Error: Invalid JSON format in '{CONFIG_FILE}' not found.[/red]")
        return {}

def recompute_grades_for_students(students: List[Dict[str, Any]], config: Dict[str, Any]) -> None:
    """
    Recomputes all grades (final_grade and letter_grade) for a list of students.
    Includes a rich status spinner animation.
    """
    weights = config.get("grading_weights", {})
    thresholds = config.get("grade_thresholds", {})
    
    if students:
        # ANIMATION: Status Spinner for processing
        with CONSOLE.status("[magenta]Recomputing final grades and letter assignments...[/magenta]", spinner="dots"):
            time.sleep(0.3) # Slow down slightly
            # transform.py functions modify the list in-place
            compute_final_grades(students, weights)
            assign_letter_grades(students, thresholds)

def load_section_data(filepath: str, config: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """
    Loads data, validates, and computes grades.
    Includes a rich track progress animation.
    """
    
    CONSOLE.print(f"[cyan]Loading and validating data from '{filepath}'...[/cyan]")
    valid_data: List[Dict[str, Any]] = []
    skipped_data: List[Dict[str, str]] = []
    
    # ANIMATION: Track progress bar for loading (Slower/Thicker)
    for step in track(range(50), description="[cyan]Ingesting data and running validation[/cyan]", transient=True):
        if step == 0:
            # Actual ingestion happens only once in the background
            valid_data, skipped_data = ingest_student_data(filepath)
        time.sleep(0.02) # Slower sleep
    
    # 2. Transform (Grade Computation)
    if valid_data:
        recompute_grades_for_students(valid_data, config)
    
    return valid_data, skipped_data

def get_existing_csv_files(directory: str = DATA_FOLDER) -> List[str]:
    """Auto-detects and lists all existing .csv files."""
    return [f for f in os.listdir(directory) if f.endswith(".csv")]

# --- Helper for Conditional Score Styling ---
def _get_score_style(score: Optional[float]) -> str:
    """Returns a rich style string based on the score value."""
    if score is None:
        return "bold yellow"  # Highlight missing scores
    if score >= 90:
        return "bold green"    # Excellent
    if score >= 80:
        return "bold cyan"     # Good
    if score <= 69.9:
        return "bold red"      # Low/Failing
    return "white"             # Moderate

def fmt(v: Optional[float]) -> str:
    """Formats a float safely."""
    return "N/A" if v is None else f"{v:.2f}"
# --- End Score Styling Helper ---


def display_students_table(
    students: List[Dict[str, Any]], 
    title: str, 
    grade_thr: float, 
    att_thr: float,
    sort_key: str = 'last_name' # For Sorting
) -> None:
    """Displays students in a formatted Rich Table with conditional score styling."""
    if not students:
        CONSOLE.print(f"[yellow]No student records to display for {title}.[/yellow]")
        return

    # Sort students (Sorting requirement)
    sorted_students = sorted(
        students, 
        key=lambda s: (s.get('last_name', ''), s.get('first_name', ''))
    )

    # FIX APPLIED HERE: Added width=None to prevent truncation and the TypeError
    table = Table(title=title, show_lines=True, header_style="bold magenta", style="cyan", width=None)
    
    # Define Core and Score Columns
    CORE_COLS = ["ID", "Last Name", "First Name", "Section"]
    SCORE_COLS = ["quiz1", "quiz2", "quiz3", "quiz4", "quiz5", "midterm", "final", "attendance_percent"]
    FINAL_COLS = ["Final Grade", "Letter Grade", "Status"]

    # Add columns to the table
    for col in CORE_COLS + SCORE_COLS + FINAL_COLS:
        # Give numeric columns special justification
        justify = "left" if col in CORE_COLS else "center"
        table.add_column(col.replace('_', ' ').title(), justify=justify, style="white")

    # Add rows with conditional color-coding
    for student in sorted_students:
        final_grade = student.get("final_grade")
        att_percent = student.get("attendance_percent")
        
        is_at_risk = (
            (final_grade is not None and final_grade < grade_thr) or 
            (att_percent is not None and att_thr is not None and att_percent < att_thr)
        )
        
        status = Text("AT-RISK", style="bold red reverse") if is_at_risk else Text("PASSED", style="bold green")
        
        row_items = []
        
        # 1. Core Data
        row_items.append(str(student.get("student_id", "")))
        row_items.append(student.get("last_name", ""))
        row_items.append(student.get("first_name", ""))
        row_items.append(student.get("section", ""))
        
        # 2. Score Data (Styled conditionally)
        for col_key in SCORE_COLS:
            score = student.get(col_key)
            style = _get_score_style(score)
            row_items.append(Text(fmt(score), style=style))

        # 3. Final Grade Data
        final_grade_style = _get_score_style(final_grade)
        row_items.append(Text(fmt(final_grade), style=final_grade_style))
        row_items.append(student.get("letter_grade", "N/A"))
        row_items.append(status)

        # Apply a light yellow background for the entire row if AT-RISK
        row_style = "on #333300" if is_at_risk else "none"
        
        table.add_row(*row_items, style=row_style)
    
    CONSOLE.print(table)


# --- Input & Utility Functions for New Data ---

def _get_next_student_id(students: List[Dict[str, Any]], section: str) -> str:
    """Generates the next student ID based on section (e.g., 'BSIT01')."""
    prefix = "".join(filter(str.isalpha, section.upper()))
    
    # Get all existing IDs for the section and find the max number
    current_ids = [s.get('student_id', '') for s in students if s.get('section', '').upper() == section.upper()]
    
    max_num = 0
    for sid in current_ids:
        if sid.startswith(prefix):
            try:
                num = int(sid[len(prefix):])
                max_num = max(max_num, num)
            except ValueError:
                continue # Ignore malformed IDs
    
    # New ID is max_num + 1, formatted with leading zeros (e.g., 01, 02)
    next_num = max_num + 1
    return f"{prefix}{next_num:02}"

def _prompt_score(prompt_text: str, allow_none: bool = True) -> Optional[float]:
    """Prompts for a score (0-100) with validation."""
    while True:
        raw_value = Prompt.ask(f"[cyan]{prompt_text}[/cyan]", default="N/A" if allow_none else "0")
        if raw_value.upper() in ["N/A", "NONE", ""]:
            return None
        
        try:
            score = float(raw_value)
            if 0 <= score <= 100:
                return score
            else:
                CONSOLE.print("[red]Error: Score must be between 0 and 100.[/red]")
        except ValueError:
            CONSOLE.print("[red]Error: Invalid non-numeric input. Please enter a number or 'N/A'.[/red]")

def _prompt_new_student(existing_students: List[Dict[str, Any]], pre_defined_section: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Prompts for all new student details with validation."""
    CONSOLE.print(Panel("[gold1]Add New Student Record[/gold1]", border_style="gold1"))
    
    # 1. Use Pre-defined Section
    if pre_defined_section:
        section = pre_defined_section
        CONSOLE.print(f"[green]Section:[/green] [bold]{section}[/bold]")
    else:
        # This path should ideally not be hit in Menu 1, but kept for robustness
        while True:
            section = Prompt.ask("[cyan]Enter Section Name[/cyan]").strip()
            if section:
                break
            CONSOLE.print("[red]Error: Section name cannot be empty.[/red]")

    # 2. Generate ID
    student_id = _get_next_student_id(existing_students, section)
    CONSOLE.print(f"[green]Generated Student ID:[/green] [bold]{student_id}[/bold]")

    # 3. Prompt for Names
    while True:
        last_name = Prompt.ask("[cyan]Enter Last Name[/cyan]").strip()
        first_name = Prompt.ask("[cyan]Enter First Name[/cyan]").strip()
        
        # Check for numeric names (Input & Validation requirement)
        if last_name.isdigit() or first_name.isdigit():
            CONSOLE.print("[red]Error: Names cannot be purely numeric.[/red]")
            continue
            
        # Check for duplicates within the section (Input & Validation requirement)
        is_duplicate = any(
            s.get('section', '').upper() == section.upper() and
            s.get('last_name', '').upper() == last_name.upper() and
            s.get('first_name', '').upper() == first_name.upper()
            for s in existing_students
        )
        
        if is_duplicate:
            CONSOLE.print(f"[red]Warning: Duplicate name '{first_name} {last_name}' found in section '{section}'. Please verify and re-enter if needed.[/red]")
            if Prompt.ask("[cyan]Continue with this name (y/n)? [/cyan]", default="n") != 'y':
                continue

        if last_name and first_name:
            break
        CONSOLE.print("[red]Error: Last Name and First Name are required.[/red]")


    # 4. Prompt for Scores
    scores = {}
    CONSOLE.print("\n[bold]--- Enter Scores (0-100 or N/A) ---[/bold]")
    for i in range(1, 6):
        scores[f"quiz{i}"] = _prompt_score(f"New Quiz {i} Score", allow_none=True)
    
    scores["midterm"] = _prompt_score("Midterm Score", allow_none=True)
    scores["final"] = _prompt_score("Final Score", allow_none=True)
    
    # 5. Prompt for Attendance
    CONSOLE.print("\n[bold]--- Enter Attendance ---[/bold]")
    while True:
        try:
            total_days = IntPrompt.ask("[cyan]Total number of class days[/cyan]", default=100)
            if total_days <= 0:
                CONSOLE.print("[red]Error: Total class days must be greater than 0.[/red]")
                continue
            
            days_present = IntPrompt.ask("[cyan]Days present[/cyan]", default=total_days)
            
            # Validation: Days present vs Total days
            if 0 <= days_present <= total_days:
                attendance_percent = round((days_present / total_days) * 100, 2)
                scores["attendance_percent"] = attendance_percent
                CONSOLE.print(f"[green]Calculated Attendance:[/green] [bold]{attendance_percent:.2f}%[/bold]")
                break
            else:
                CONSOLE.print("[red]Error: Days present must be between 0 and total class days.[/red]")
        except Exception:
            CONSOLE.print("[red]Invalid input for days. Please enter a whole number.[/red]")
            
    # Assemble raw record
    new_record = {
        "student_id": student_id,
        "last_name": last_name,
        "first_name": first_name,
        "section": section,
        **scores
    }

    # Final validation check using ingest.py's internal validator
    try:
        # Create a raw string dictionary version for the validator
        raw_row = {k: str(v) if v is not None else '' for k, v in new_record.items()}
        # Ensure all required columns are present for the full validation
        full_row = {k: raw_row.get(k, '') for k in ['student_id', 'last_name', 'first_name', 'section', 
                                                   'quiz1', 'quiz2', 'quiz3', 'quiz4', 'quiz5', 
                                                   'midterm', 'final', 'attendance_percent']}
        _parse_and_validate_row(full_row)
        return new_record
    except ValueError as e:
        CONSOLE.print(f"[red]Critical Validation Error: {e}. Record will not be saved.[/red]")
        return None

# --- New Helper Function for saving the entire CSV (Needed for Menu 1) ---

def export_entire_csv(records: List[Dict[str, Any]], path: str) -> str:
    """
    Exports a list of student records to a single CSV file, overwriting the file.
    Uses DEFAULT_FIELDS defined in reports.py. Includes a rich track animation.
    """
    ensure_dir(os.path.dirname(path) or ".")
    
    # We rely on DEFAULT_FIELDS from reports.py
    from reports import DEFAULT_FIELDS 

    # ANIMATION: Track progress bar for saving (Slower/Thicker)
    for step in track(range(35), description=f"[green]Writing data to {os.path.basename(path)}...[/green]", transient=True):
        if step == 0:
            # The actual write operation only happens once
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=DEFAULT_FIELDS, extrasaction="ignore")
                writer.writeheader()
                for r in records:
                    # Ensure None values are written as empty strings
                    row = {k: ("" if r.get(k) is None else r.get(k)) for k in DEFAULT_FIELDS}
                    writer.writerow(row)
        time.sleep(0.02) # Slower sleep

    return path


# --- Menu Handlers (Core Functional Features) ---

def handle_enter_new_data(config: Dict[str, Any], all_students: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Menu 1: New Flow - Prompt for CSV name, then prompt for student data (in a loop), and save."""
    
    CONSOLE.print(Panel("[gold1]1. Create New/Add to Existing Data File[/gold1]", border_style="gold1"))
    
    # 1. Get CSV file name from user
    while True:
        csv_name = Prompt.ask("[cyan]Enter the name for the CSV file (e.g., Spring_2025.csv)[/cyan]").strip()
        if not csv_name:
            CONSOLE.print("[red]CSV file name cannot be empty.[/red]")
            continue
        if not csv_name.endswith(".csv"):
            csv_name += ".csv"
        filepath = os.path.join(DATA_FOLDER, csv_name)
        break

    # 2. Load existing data from the specified CSV (or start empty)
    students_in_file, _ = load_section_data(filepath, config) if os.path.exists(filepath) else ([], [])
    
    CONSOLE.print(f"[green]Loaded {len(students_in_file)} existing records from {csv_name}.[/green]")
    
    # --- 3. Student Entry Loop ---
    current_section: Optional[str] = None
    students_added_count = 0
    
    while True:
        # Prompt for section name (with 'done' and default option)
        if current_section is None:
            section_input = Prompt.ask("[cyan]Enter Section Name for new student (or type 'done' to finish)[/cyan]").strip().lower()
        else:
            section_input = Prompt.ask(f"[cyan]Enter Section Name for new student (Default: {current_section}) or type 'done' to finish[/cyan]", default=current_section).strip().lower()

        if section_input == 'done':
            break

        if not section_input:
            CONSOLE.print("[red]Error: Section name cannot be empty.[/red]")
            continue
        
        current_section = section_input # Update the current default section
        
        CONSOLE.print(f"\n[bold yellow]-- Entering data for Section: {current_section} --[/bold yellow]")
        
        # 4. Prompt for student details (pass all_students for ID/conflict checks)
        new_student = _prompt_new_student(all_students + students_in_file, pre_defined_section=current_section)
        
        if new_student:
            # Add to both lists
            students_in_file.append(new_student)
            all_students.append(new_student) # Ensure system-wide list is updated for ID checks later
            students_added_count += 1
            CONSOLE.print(f"[green]Student added to buffer! Total added: {students_added_count}.[/green]")
            # Important: Set the default section for the next loop iteration
            current_section = new_student['section'] 
    
    # --- 5. Save and Display ---
    if students_added_count > 0:
        # Re-run grade computation on the updated list for this file
        recompute_grades_for_students(students_in_file, config)
        
        # Save the entire updated list to the user-named CSV
        export_entire_csv(students_in_file, filepath)
        
        CONSOLE.print(f"\n[green]Success! {students_added_count} student(s) added and saved to {filepath}.[/green]")
        
        # Display the newly added student's section table (or the last one entered)
        sections_updated = group_by_section(students_in_file)
        if current_section in sections_updated:
            display_students_table(sections_updated[current_section], f"New/Updated Section: {current_section} (in {csv_name})", 
                                  config.get("passing_grade_threshold", 70), 
                                  config.get("at_risk_attendance_threshold", 80))
        
    else:
        CONSOLE.print("[yellow]No students added. Returning to menu.[/yellow]")

    return all_students

def handle_load_existing_csv(config: Dict[str, Any]) -> None:
    """Menu 2: Load and view existing CSV files, displaying separated tables and summaries per section."""
    files = get_existing_csv_files()
    if not files:
        CONSOLE.print("[yellow]No CSV files found in the current directory.[/yellow]")
        return
        
    CONSOLE.print(Panel("[gold1]2. Load Existing CSV (View)[/gold1]", border_style="gold1"))
    for i, file in enumerate(files):
        CONSOLE.print(f"  [bold]{i+1}[/bold]: {file}")

    while True:
        try:
            choice = IntPrompt.ask("[cyan]Select a CSV file to load (number)[/cyan]", choices=[str(i+1) for i in range(len(files))])
            filepath = files[choice - 1]
            break
        except Exception:
            CONSOLE.print("[red]Invalid choice. Please select a number from the list.[/red]")
    
    # Load and validate the data (includes animation)
    students, skipped_rows = load_section_data(filepath, config)
    
    if not students:
        CONSOLE.print(f"[yellow]File '{filepath}' contains no valid records to display.[/yellow]")
        if skipped_rows:
            CONSOLE.print(f"[yellow]Note: Skipped {len(skipped_rows)} bad rows during ingest.[/yellow]")
        return

    # Group students by section for display (Multi-section display)
    sections = group_by_section(students)

    CONSOLE.print(f"\n[bold green]Successfully loaded {len(students)} records from {filepath}, across {len(sections)} sections.[/bold green]")
    if skipped_rows:
        CONSOLE.print(f"[yellow]Note: Skipped {len(skipped_rows)} bad rows during ingest.[/yellow]")
        
    CONSOLE.print("\n[bold cyan]--- Section Details ---[/bold cyan]")
    
    # Iterate and display separate tables and summaries for each section
    grade_thr = config.get("passing_grade_threshold", 70)
    att_thr = config.get("at_risk_attendance_threshold", 80)

    for sec, recs in sections.items():
        # Display the table for this section (Table requirement)
        display_students_table(recs, f"Section: {sec} (in {os.path.basename(filepath)})", grade_thr, att_thr)
        
        # Display section summary (Reports & Summary requirement)
        stats = compute_stats([s.get("final_grade") for s in recs if s.get("final_grade") is not None])
        CONSOLE.print(Panel(
            f"[bold]Section Summary ({sec})[/bold]\n"
            f"Total Students: {stats.get('count', 0)}\n"
            f"Average Final Grade: {stats.get('mean', 0):.2f}\n"
            f"Median Final Grade: {stats.get('median', 0):.2f}\n"
            f"Std Dev: {stats.get('std_dev', 0):.2f}",
            border_style="magenta"
        ))

def handle_edit_existing_csv(config: Dict[str, Any], all_students: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Menu 3: Edit existing CSV file's records."""
    files = get_existing_csv_files()
    if not files:
        CONSOLE.print("[yellow]No CSV files found to edit.[/yellow]")
        return all_students
        
    CONSOLE.print(Panel("[gold1]3. Edit Existing CSV File[/gold1]", border_style="gold1"))
    for i, file in enumerate(files):
        CONSOLE.print(f"  [bold]{i+1}[/bold]: {file}")

    while True:
        try:
            choice = IntPrompt.ask("[cyan]Select a CSV file to edit (number)[/cyan]", choices=[str(i+1) for i in range(len(files))])
            filepath = files[choice - 1]
            break
        except Exception:
            CONSOLE.print("[red]Invalid choice. Please select a number from the list.[/red]")
    
    # Load and process the data to get the list of students for the file (includes animation)
    students_in_file, _ = load_section_data(filepath, config)

    if not students_in_file:
        CONSOLE.print(f"[yellow]File '{filepath}' contains no valid student records to edit.[/yellow]")
        return all_students

    # Display all students in the file
    display_students_table(students_in_file, f"Editing File: {os.path.basename(filepath)}", 
                           config.get("passing_grade_threshold", 70), 
                           config.get("at_risk_attendance_threshold", 80))

    while True:
        # Use a simplified list for user choice with index
        edit_list = []
        # Sort students before listing for stable choice indices
        sorted_students = sorted(students_in_file, key=lambda s: (s.get('last_name', ''), s.get('first_name', '')))
        
        CONSOLE.print("\n[bold]--- Students in File (for selection) ---[/bold]")
        for i, s in enumerate(sorted_students):
            edit_list.append((i+1, s['student_id'], s['last_name'], s['first_name']))
            CONSOLE.print(f"  [bold]{i+1}[/bold]: {s['last_name']}, {s['first_name']} ({s['student_id']}) - Section: {s['section']}")
        
        CONSOLE.print("\n[bold]Edit Options:[/bold]")
        edit_action = Prompt.ask("[cyan]Select a student number to edit/delete, or [A]dd new, [S]ave & Exit, [C]ancel[/cyan]", 
                                 choices=[str(i+1) for i in range(len(edit_list))] + ['A', 'S', 'C']).upper()
        
        if edit_action == 'C':
            CONSOLE.print("[yellow]Edit cancelled. No changes saved.[/yellow]")
            return all_students # Return original list
        
        if edit_action == 'S':
            break # Proceed to save logic
            
        if edit_action == 'A':
            # For adding, we need the union of all existing students for ID/Name conflict checks
            new_student = _prompt_new_student(all_students + students_in_file)
            if new_student:
                # Merge the new student into the full system list and the local file list
                all_students.append(new_student)
                students_in_file.append(new_student)
                recompute_grades_for_students(students_in_file, config) # Recompute all grades
                CONSOLE.print("[green]Student added. Re-displaying table...[/green]")
                display_students_table(students_in_file, f"Editing File: {os.path.basename(filepath)}", 
                                       config.get("passing_grade_threshold", 70), 
                                       config.get("at_risk_attendance_threshold", 80))
            continue
            
        try:
            student_index = int(edit_action) - 1
            # Find the actual student object to edit
            # Use the index on the sorted list to find the student
            student_to_edit = sorted_students[student_index] 
        except (ValueError, IndexError):
            CONSOLE.print("[red]Invalid selection.[/red]")
            continue

        # --- Edit/Delete Sub-Menu ---
        
        edit_options = Prompt.ask(f"[cyan]Editing {student_to_edit['last_name']}, {student_to_edit['first_name']}. [G]rade, [S]ection/Name, [D]elete, [C]ancel?[/cyan]", 
                                  choices=['G', 'S', 'D', 'C']).upper()
        
        if edit_options == 'C':
            continue
        
        if edit_options == 'D':
            if Prompt.ask(f"[red]Are you sure you want to DELETE {student_to_edit['student_id']} (y/n)?[/red]", default='n') == 'y':
                # Remove from both the local file list and the system-wide list
                students_in_file.remove(student_to_edit)
                
                # We need to find the student in all_students and remove it
                try:
                    all_students.remove(student_to_edit)
                except ValueError:
                  
                    pass

                CONSOLE.print(f"[red]Student {student_to_edit['student_id']} DELETED.[/red]")
                
                # Recompute and redisplay
                recompute_grades_for_students(students_in_file, config)
                display_students_table(students_in_file, f"Editing File: {os.path.basename(filepath)}", 
                                       config.get("passing_grade_threshold", 70), 
                                       config.get("at_risk_attendance_threshold", 80))
            continue
            
        if edit_options == 'S':
            old_section = student_to_edit['section']
            
            student_to_edit['last_name'] = Prompt.ask(f"[cyan]New Last Name ({student_to_edit['last_name']})[/cyan]", 
                                                     default=student_to_edit['last_name']).strip()
            student_to_edit['first_name'] = Prompt.ask(f"[cyan]New First Name ({student_to_edit['first_name']})[/cyan]", 
                                                      default=student_to_edit['first_name']).strip()
            student_to_edit['section'] = Prompt.ask(f"[cyan]New Section ({student_to_edit['section']})[/cyan]", 
                                                    default=student_to_edit['section']).strip()
            
            # ID System: Regenerate ID if section changes
            if old_section != student_to_edit['section']:
                 student_to_edit['student_id'] = _get_next_student_id(all_students, student_to_edit['section'])
                 CONSOLE.print(f"[green]New ID generated:[/green] [bold]{student_to_edit['student_id']}[/bold]")

        if edit_options == 'G':
            # Edit Grades/Attendance
            CONSOLE.print("\n[bold]--- Edit Grades (0-100 or N/A) ---[/bold]")
            
            # Helper to get current or default to None
            def get_current_score(key: str) -> Optional[float]:
                return student_to_edit.get(key)
                
            for i in range(1, 6):
                key = f"quiz{i}"
                current = get_current_score(key)
                current_str = f"{current:.2f}" if current is not None else "N/A"
                student_to_edit[key] = _prompt_score(f"New Quiz {i} Score ({current_str})", allow_none=True)
            
            for key in ["midterm", "final"]:
                current = get_current_score(key)
                current_str = f"{current:.2f}" if current is not None else "N/A"
                student_to_edit[key] = _prompt_score(f"New {key.capitalize()} Score ({current_str})", allow_none=True)

            # Attendance
            current_att = get_current_score("attendance_percent")
            current_att_str = f"{current_att:.2f}" if current_att is not None else "N/A"
            if Prompt.ask(f"[cyan]Edit Attendance ({current_att_str}) (y/n)?[/cyan]", default='n') == 'y':
                # For simplicity, we just ask for the new percentage directly during edit, not days/total days
                student_to_edit["attendance_percent"] = _prompt_score("New Attendance Percentage", allow_none=True)

            CONSOLE.print("[green]Grades/Attendance updated.[/green]")
        
        # After any edit (S or G), recompute grades and redisplay
        recompute_grades_for_students(students_in_file, config) # Recompute grades (Computation requirement)
        CONSOLE.print("[green]Record updated. Re-displaying table...[/green]")
        display_students_table(students_in_file, f"Editing File: {os.path.basename(filepath)}", 
                               config.get("passing_grade_threshold", 70), 
                               config.get("at_risk_attendance_threshold", 80))
                               
    # --- Save Logic (runs after 'S' is selected) ---
    
    # Save the entire file's contents (which includes all sections)
    export_entire_csv(students_in_file, filepath)
    
    CONSOLE.print(f"\n[green]Success! File '{os.path.basename(filepath)}' saved.[/green]")
    
    # Update all_students list with the final state of the edited students
    # The direct object references ensure that changes are reflected in all_students, 
    # but we recompute grades for all just to be safe.
    recompute_grades_for_students(all_students, config)
    
    return all_students

def handle_delete_csv_file() -> None:
    """Menu 4: Delete CSV files safely."""
    files = get_existing_csv_files()
    if not files:
        CONSOLE.print("[yellow]No CSV files found to delete.[/yellow]")
        return

    CONSOLE.print(Panel("[gold1]4. Delete CSV File Safely[/gold1]", border_style="gold1"))
    for i, file in enumerate(files):
        CONSOLE.print(f"  [bold]{i+1}[/bold]: {file}")

    while True:
        try:
            choice = IntPrompt.ask("[cyan]Select a CSV file to DELETE (number)[/cyan]", choices=[str(i+1) for i in range(len(files))])
            filepath = files[choice - 1]
            break
        except Exception:
            CONSOLE.print("[red]Invalid choice. Please select a number from the list.[/red]")

    # Confirmation (Delete CSV files safely requirement)
    if Prompt.ask(f"[red]Are you absolutely sure you want to DELETE '{filepath}' (y/n)?[/red]", default='n') == 'y':
        
        # ANIMATION: Status Spinner for deletion (Slower)
        with CONSOLE.status(f"[red]Deleting file {filepath}...[/red]", spinner="line"):
            time.sleep(1) # Slow down significantly
            try:
                os.remove(filepath)
            except OSError as e:
                CONSOLE.print(f"[red]Error deleting file {filepath}: {e}[/red]")
                return
        
        CONSOLE.print(f"[red]Successfully deleted file: {filepath}[/red]")
    else:
        CONSOLE.print("[yellow]File deletion cancelled.[/yellow]")
        
def handle_generate_reports(config: Dict[str, Any]) -> None:
    """Menu 5: Prompts user to select a CSV, loads only that data, and runs report generation."""
    files = get_existing_csv_files()
    if not files:
        CONSOLE.print("[yellow]No CSV files found to generate reports from.[/yellow]")
        return
        
    # NOTE: The redundant 'from transform import...' line has been removed here.
    
    CONSOLE.print(Panel("[gold1]5. Generate All Reports[/gold1]", border_style="gold1"))
    CONSOLE.print("[bold]Select a CSV file to generate reports for (Summary, Section CSVs, At-Risk List):[/bold]")
    for i, file in enumerate(files):
        CONSOLE.print(f"  [bold]{i+1}[/bold]: {file}")

    while True:
        try:
            choice = IntPrompt.ask("[cyan]Select a CSV file (number)[/cyan]", choices=[str(i+1) for i in range(len(files))])
            filepath = files[choice - 1]
            break
        except Exception:
            CONSOLE.print("[red]Invalid choice. Please select a number from the list.[/red]")

    # 1. Load data from the selected CSV only 
    report_students, _ = load_section_data(filepath, config)
    
    if not report_students:
        CONSOLE.print(f"[yellow]File '{filepath}' contains no valid records for reporting. Aborting.[/yellow]")
        return
        
    CONSOLE.print(f"[green]Successfully loaded {len(report_students)} records from {filepath}. Starting report generation...[/green]")

    # 2. Recompute grades for security
    recompute_grades_for_students(report_students, config)
    
    try:
        report_config = {
            "output_folder": config.get("output_folder", "./reports"),
            "grade_threshold": config.get("passing_grade_threshold", 70.0),
            "attendance_threshold": config.get("at_risk_attendance_threshold", 80.0)
        }
        
        # ANIMATION: Status Spinner for report generation (Slower)
        with CONSOLE.status("[magenta]Running complex report generation and analytics...[/magenta]", spinner="star"):
            time.sleep(0.4) # Slow down significantly
            summary_data = generate_reports(report_students, report_config)
            
            # --- NEW HISTOGRAM GENERATION ---
            plot_path = generate_grade_histogram(
                report_students,
                report_config["output_folder"],
                os.path.basename(filepath)
            )
            # -------------------------------
            
        CONSOLE.print(f"[green]Reports generated successfully in {report_config['output_folder']}.[/green]")

        # --- Report the plot path ---
        if plot_path:
            CONSOLE.print(f"\n[green]Histogram saved to:[/green] [cyan]{plot_path}[/cyan]")
        # -----------------------------

        # Analytics/Summary Display
        sections_stats = summary_data['sections']
        CONSOLE.print("\n[bold magenta]--- Advanced Analytics (Section Comparison) ---[/bold magenta]")
        for sec, stats in sorted(sections_stats.items()):
            CONSOLE.print(f"  [bold]{sec}[/bold]: Avg Grade: {stats.get('avg_final'):.2f}, Median: {stats.get('median_final'):.2f}")
            # Outliers (using analyze.py functions)
            section_recs = group_by_section(report_students)[sec]
            scores = [r.get("final_grade") for r in section_recs if r.get("final_grade") is not None]
            outliers = detect_outliers(scores)
            if outliers:
                CONSOLE.print(f"    [yellow]Outliers (IQR Method):[/yellow] {len(outliers)} students with scores: {sorted(outliers)}")

    except Exception as e:
        CONSOLE.print(f"[red]An error occurred during report generation: {e}[/red]")

def handle_apply_curve(config: Dict[str, Any], all_students: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Menu 7: Loads a CSV, applies a grade curve based on a target mean, and saves the result to a NEW file."""
    files = get_existing_csv_files()
    if not files:
        CONSOLE.print("[yellow]No CSV files found to apply a grade curve to.[/yellow]")
        return all_students

    CONSOLE.print(Panel("[gold1]7. Apply Grade Curve[/gold1]", border_style="gold1"))
    for i, file in enumerate(files):
        CONSOLE.print(f"  [bold]{i+1}[/bold]: {file}")

    while True:
        try:
            choice = IntPrompt.ask("[cyan]Select the CSV file to curve (number)[/cyan]", choices=[str(i+1) for i in range(len(files))])
            filepath = files[choice - 1]
            break
        except Exception:
            CONSOLE.print("[red]Invalid choice. Please select a number from the list.[/red]")

    # 1. Load data from the selected CSV
    students_in_file, _ = load_section_data(filepath, config)
    
    if not students_in_file:
        CONSOLE.print(f"[yellow]File '{filepath}' contains no valid records for curving. Aborting.[/yellow]")
        return all_students
        
    # 2. Get Target Mean
    while True:
        try:
            target_mean = FloatPrompt.ask("[cyan]Enter the Target Class Mean (e.g., 85.0 to curve to a B)[/cyan]", default=85.0)
            if 0.0 <= target_mean <= 100.0:
                break
            CONSOLE.print("[red]Target mean must be between 0 and 100.[/red]")
        except Exception:
            CONSOLE.print("[red]Invalid input. Please enter a number.[/red]")

    CONSOLE.print(f"[cyan]Applying curve to set mean of {os.path.basename(filepath)} to {target_mean:.2f}...[/cyan]")

    # ANIMATION: Status Spinner for curving
    with CONSOLE.status("[magenta]Applying curve and recalculating grades...[/magenta]", spinner="dots"):
        # 3. Apply the Curve
        students_in_file = apply_grade_curve(students_in_file, target_mean)

        # 4. Recompute Letter Grades (since final_grade changed)
        recompute_grades_for_students(students_in_file, config)
        time.sleep(0.3) # Give time for the spinner to show completion

    
    # 5. --- NEW SAVE AS LOGIC ---
    CONSOLE.print("\n[bold yellow]--- Saving Curved Grades to NEW File ---[/bold yellow]")
    while True:
        # Generate the default suggested name: [OriginalName]_CURVED.csv
        base_name = os.path.basename(filepath)
        suggested_name = base_name.replace('.csv', '_CURVED.csv')
        
        new_csv_name = Prompt.ask(f"[cyan]Enter the NEW filename to save the curved data[/cyan]", default=suggested_name).strip()
        
        if not new_csv_name.endswith(".csv"):
            new_csv_name += ".csv"
            
        new_filepath = os.path.join(DATA_FOLDER, new_csv_name)
        
        # Check if the NEW file already exists and ask for confirmation to overwrite
        if os.path.exists(new_filepath):
             if Prompt.ask(f"[red]Warning: '{new_csv_name}' already exists. Overwrite (y/n)?[/red]", default='n') != 'y':
                 continue
        
        break

    # 6. Save the updated list to the NEW CSV
    export_entire_csv(students_in_file, new_filepath)
    
    CONSOLE.print(f"\n[green]Success! Grades curved and saved to NEW file: {new_filepath}[/green]")
    
    # 7. Display results (all sections in that file)
    sections = group_by_section(students_in_file)
    grade_thr = config.get("passing_grade_threshold", 70)
    att_thr = config.get("at_risk_attendance_threshold", 80)
    
    for sec, recs in sections.items():
        CONSOLE.print(f"\n[bold cyan]--- Curved Section: {sec} ---[/bold cyan]")
        display_students_table(recs, f"Curved Section: {sec}", grade_thr, att_thr)
    
    
    return all_students
        
# --- Main Application Loop ---

def main_menu() -> None:
    """Displays the main menu and handles user choices."""
    
    # Initial load of config
    config = load_config()
    if not config:
        return # Cannot run without config

    # Placeholder for the central list of all student data loaded/added
    all_students: List[Dict[str, Any]] = []
    
    # --- STARTUP ANIMATION (Track Progress Bar) ---
    for _ in track(range(50), description="[gold1]Opening EPSILON GRADING SYSTEM...[/gold1]", transient=True):
        time.sleep(0.02) # Slower delay for a visible bar
    # --- END STARTUP ANIMATION ---


    # !MAIN LOOP!
    while True:
        CONSOLE.clear()
        
        # Display Banner (UI requirement)
        CONSOLE.print(Panel(
            Align.center("[bold cyan1 underline]🎓EPSILON GRADING SYSTEM🏫[/bold cyan1 underline]"), 
            border_style="gold1"
        ))
   
        
        # Display Menu
        menu = Table.grid(padding=(0, 2))
        menu.add_column(style="bold white")
        menu.add_column(style="bold white")
        
        menu.add_row("[gold1 bold][1][/gold1 bold]", "[green bold]Enter New Student File 📝[/green bold]")
        menu.add_row("[2]", "[green bold]Load Existing CSV 🔃[/green bold]")
        menu.add_row("[3]", "[green bold]Edit Existing CSV File (Grades, Section, Names, Delete Student) ✏️[/green bold]")
        menu.add_row("[4]", "[green bold]Delete CSV File 🚮[/green bold]")
        menu.add_row("[5]", "[green bold]Generate All Reports 📊[/green bold]")
        menu.add_row("[6]","[green bold]Apply Grade Curve 📈[/green bold]")
        menu.add_row("[7]", "[green bold]Exit 🚪[/green bold]")

        CONSOLE.print(menu)
        
        # User Choice
        choice = Prompt.ask("[cyan]Select an option[/cyan]", choices=['1', '2', '3', '4', '5', '6', '7'])

        if choice == '1':
            all_students = handle_enter_new_data(config, all_students)
        elif choice == '2':
            handle_load_existing_csv(config)
        elif choice == '3':
            # Note: handle_edit_existing_csv updates both the system list (all_students) and the disk file.
            all_students = handle_edit_existing_csv(config, all_students)
        elif choice == '4':
            handle_delete_csv_file()
        elif choice == '5':

            for _ in track(range(20), description="[green]Loading Choices[/green]", transient=True):
                time.sleep(0.03) # Small delay for animation
            handle_generate_reports(config)
        elif choice == '6':
            for _ in track(range(20), description="[green]Grade Curve Generating[/green]", transient=True):
                time.sleep(0.03) 
            all_students = handle_apply_curve(config, all_students) # NEW HANDLER
        elif choice == '7':
            # ANIMATION: Tracked exit message
            for _ in track(range(20), description="[green]System cleanup and shutting down...[/green]", transient=True):
                time.sleep(0.02) # Small delay for animation
                
            CONSOLE.print(Panel("[red bold]Exiting EPSILON GRADING SYSTEM. Goodbye! See Ya Again!![/red bold]", border_style="Red"))
            break

        Prompt.ask("[cyan]Press ENTER to return to the main menu...[/cyan]")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        CONSOLE.print(Panel("[red]Operation interrupted by user (Ctrl+C). Exiting.[/red]", border_style="red"))