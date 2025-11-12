
import statistics
from typing import List, Dict, Any, Optional

def compute_final_grades(
    students: List[Dict[str, Any]], 
    weights: Dict[str, float]
) -> List[Dict[str, Any]]:
    
#pls remove po ito mr calayag, yung ff docsting from line 11 to line 31
    """
    Computes the final weighted grade for each student.

    This function iterates through each student, calculates their average quiz
    score, and then computes a final weighted grade based on the weights
    [cite_start]provided in the configuration[cite: 24, 22].

    It handles missing scores (None) by treating them as 0 for calculation
    [cite_start][cite: 16].

    The 'students' list of dictionaries is modified in-place by adding
    a new key, 'final_grade', to each student dictionary.

    Args:
        students: A list of student record dictionaries.
        weights: A dictionary from the config, e.g.:
                 { "quizzes": 0.3, "midterm": 0.3, "final": 0.4 }

    Returns:
        The same list of student dictionaries, with 'final_grade' added.
    """
    if not weights:
        print("Warning: Grade weights are missing. Cannot compute final grades.")
        return students

    # Get weights from the config, defaulting to 0.0 if a key is missing
    quiz_weight: float = weights.get("quizzes", 0.0)
    midterm_weight: float = weights.get("midterm", 0.0)
    final_weight: float = weights.get("final", 0.0)

    # Use array operations to iterate and transform.
    for student in students:
        try:
            # --- 1. Calculate Average Quiz Score ---
            quiz_keys: List[str] = [key for key in student if key.startswith("quiz")]
            quiz_scores: List[float] = []
            
            for key in quiz_keys:
                score = student.get(key)
                # Treat missing quiz scores (None) as 0.
                quiz_scores.append(float(score) if score is not None else 0.0)

            avg_quiz: float = 0.0
            if quiz_keys:
                avg_quiz = sum(quiz_scores) / len(quiz_keys)

            # --- 2. Get Midterm and Final Scores ---
            # Treat missing midterm/final (None) as 0.
            midterm_score: float = float(student.get("midterm")) \
                if student.get("midterm") is not None else 0.0
            final_score: float = float(student.get("final")) \
                if student.get("final") is not None else 0.0

            # --- 3. Compute Final Weighted Grade --- 
            total_grade: float = (
                (avg_quiz * quiz_weight) +
                (midterm_score * midterm_weight) +
                (final_score * final_weight)
            )

            # Add the new computed grade to the student's record
            student["final_grade"] = round(total_grade, 2)

        except (TypeError, ValueError) as e:
            # Handle bad data that might have slipped past ingest
            print(f"Warning: Could not compute grade for "
                  f"{student.get('student_id')}. Error: {e}")
            student["final_grade"] = None
        except Exception as e:
            print(f"An unexpected error occurred for student "
                  f"{student.get('student_id')}: {e}")
            student["final_grade"] = None

    return students

def assign_letter_grades(
    students: List[Dict[str, Any]], 
    thresholds: Dict[str, float]
) -> List[Dict[str, Any]]:
    """
    Assigns a letter grade to each student based on their 'final_grade'.

    This function uses a dictionary of thresholds (e.g., "A": 90)
    [cite_start]from the config file [cite: 24] to assign a letter grade.

    The 'students' list is modified in-place by adding a new key,
    'letter_grade', to each student dictionary.

    Args:
        students: The list of student dictionaries, which MUST have
                  the 'final_grade' key computed.
        thresholds: A dictionary from the config, e.g.:
                    { "A": 93, "A-": 90, "B+": 87, "B": 83, ... }

    Returns:
        The same list of student dictionaries, with 'letter_grade' added.
    """
    if not thresholds:
        print("Warning: Letter grade thresholds are missing. Skipping assignment.")
        return students

    # Sort thresholds from highest score to lowest to ensure correct assignment
    # e.g., [('A', 93), ('A-', 90), ('B+', 87), ...]
    sorted_thresholds = sorted(
        thresholds.items(), 
        key=lambda item: item[1], 
        reverse=True
    )

    for student in students:
        grade: Optional[float] = student.get("final_grade")

        if grade is None:
            student["letter_grade"] = "N/A"  # Or None
            continue

        assigned = False
        for letter, min_score in sorted_thresholds:
            if grade >= min_score:
                student["letter_grade"] = letter
                assigned = True
                break  # Stop at the first (highest) match

        if not assigned:
            student["letter_grade"] = "F"  # Default if below all thresholds

    return students

   #added this (caiga) for calayag (function to for grade curves)

   

def apply_grade_curve(students: List[Dict[str, Any]], target_mean: float) -> List[Dict[str, Any]]:
    """
    Adjusts final grades so that the class mean matches the target_mean.
    
    Args:
        students: List of student records with 'final_grade'.
        target_mean: The desired average grade (e.g., 85.0).
    """
    # 1. Collect all valid final grades
    valid_grades = [s["final_grade"] for s in students if s.get("final_grade") is not None]
    if not valid_grades:
        return students

    # 2. Calculate the current class mean
    current_mean = statistics.mean(valid_grades)
    
    # 3. Determine the required adjustment factor (shift)
    shift = target_mean - current_mean
    
    # 4. Apply the shift to all grades
    for student in students:
        old_grade = student.get("final_grade")
        if old_grade is not None:
            new_grade = round(old_grade + shift, 2)
            # Ensure grades remain within the 0-100 boundary
            student["final_grade"] = max(0.0, min(100.0, new_grade))
            
    return students



   