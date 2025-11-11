# src/transform.py
# Per, this module handles computing weighted grades and letter grades.

from typing import List, Dict, Any, Optional

def compute_final_grades(
    students: List[Dict[str, Any]], 
    weights: Dict[str, float]
) -> List[Dict[str, Any]]:
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

# This block allows the file to be run directly for testing
if __name__ == "__main__":
    print("--- Running transform.py self-test ---")

    # 1. Define sample data based on project spec.
    sample_students: List[Dict[str, Any]] = [
        {
            "student_id": "s101",
            "quiz1": 80, "quiz2": 85, "quiz3": 90, "quiz4": 75, "quiz5": 88,
            "midterm": 82,
            "final": 90
        },
        {
            "student_id": "s102",
            "quiz1": 70, "quiz2": 65, "quiz3": None, "quiz4": 72, "quiz5": 50,
            "midterm": 60,
            "final": 75
        },
        {
            "student_id": "s103",
            "quiz1": 95, "quiz2": 92, "quiz3": 98, "quiz4": 100, "quiz5": 90,
            "midterm": 95,
            "final": None  # Missing final
        }
    ]

    # 2. Define sample config data.
    sample_weights: Dict[str, float] = {
        "quizzes": 0.40,  # 40%
        "midterm": 0.25,  # 25%
        "final": 0.35     # 35%
    }
    
    sample_thresholds: Dict[str, float] = {
        "A": 90,
        "B": 80,
        "C": 70,
        "D": 60
    }

    # --- Test compute_final_grades ---
    print("\n[Test] Computing final grades...")
    students_with_grades = compute_final_grades(sample_students, sample_weights)
    
    # Expected calculations:
    # s101: (avg(80,85,90,75,88) * 0.4) + (82 * 0.25) + (90 * 0.35)
    #     = (83.6 * 0.4) + 20.5 + 31.5 = 33.44 + 20.5 + 31.5 = 85.44
    # s102: (avg(70,65,0,72,50) * 0.4) + (60 * 0.25) + (75 * 0.35)
    #     = (51.4 * 0.4) + 15.0 + 26.25 = 20.56 + 15.0 + 26.25 = 61.81
    # s103: (avg(95,92,98,100,90) * 0.4) + (95 * 0.25) + (0 * 0.35)
    #     = (95.0 * 0.4) + 23.75 + 0.0 = 38.0 + 23.75 = 61.75
    
    for s in students_with_grades:
        print(f"  {s['student_id']}: {s['final_grade']}")

    # --- Test assign_letter_grades ---
    print("\n[Test] Assigning letter grades...")
    students_with_letters = assign_letter_grades(students_with_grades, sample_thresholds)
    
    # Expected calculations:
    # s101: 85.44 -> B
    # s102: 61.81 -> D
    # s103: 61.75 -> D

    for s in students_with_letters:
        print(f"  {s['student_id']}: {s['final_grade']} -> {s['letter_grade']}")

    print("\n--- Self-test complete ---")