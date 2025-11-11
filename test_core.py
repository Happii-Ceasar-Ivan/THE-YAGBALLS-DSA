import unittest
import json
import os
from typing import List, Dict, Any

# Assuming all project files are in the same directory
try:
    from transform import compute_final_grades, assign_letter_grades
    from main import _get_next_student_id, load_config
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Ensure all project files (transform.py, main.py, config.json) are in the same directory.")
    exit()

class TestCoreFunctions(unittest.TestCase):

    def setUp(self):
        """Setup sample data and load config."""
        self.config = load_config()
        self.weights = self.config.get("grading_weights", {})
        self.thresholds = self.config.get("grade_thresholds", {})
        
        self.sample_students = [
            {"student_id": "BSIT01", "last_name": "Smith", "first_name": "Alice", "section": "BSIT",
             "quiz1": 80, "quiz2": 85, "quiz3": 90, "quiz4": 75, "quiz5": 88, 
             "midterm": 82, "final": 90, "attendance_percent": 95.0},
            {"student_id": "BSED01", "last_name": "Jones", "first_name": "Bob", "section": "BSED",
             "quiz1": 70, "quiz2": 65, "quiz3": None, "quiz4": 72, "quiz5": 50, 
             "midterm": 60, "final": 75, "attendance_percent": 70.5}, # Quiz average: (70+65+0+72+50)/5 = 51.4
            {"student_id": "BSIT02", "last_name": "Chen", "first_name": "Charlie", "section": "BSIT",
             "quiz1": 95, "quiz2": 92, "quiz3": 98, "quiz4": 100, "quiz5": 90, 
             "midterm": 95, "final": None, "attendance_percent": 98.0} # Final score is None (treated as 0)
        ]

    def test_grade_computation(self):
        """Tests the final weighted grade calculation (transform.py)."""
        students = compute_final_grades(self.sample_students, self.weights)
        
        # Recalculate based on config.json: Q:0.4, M:0.25, F:0.35
        # 1. Alice (AvgQ: 83.6): (83.6 * 0.4) + (82 * 0.25) + (90 * 0.35) = 33.44 + 20.5 + 31.5 = 85.44
        # 2. Bob (AvgQ: 51.4): (51.4 * 0.4) + (60 * 0.25) + (75 * 0.35) = 20.56 + 15.0 + 26.25 = 61.81
        # 3. Charlie (AvgQ: 95.0): (95.0 * 0.4) + (95 * 0.25) + (0 * 0.35) = 38.0 + 23.75 + 0.0 = 61.75
        
        self.assertAlmostEqual(students[0]["final_grade"], 85.44, 2)
        self.assertAlmostEqual(students[1]["final_grade"], 61.81, 2)
        self.assertAlmostEqual(students[2]["final_grade"], 61.75, 2)

    def test_letter_grade_assignment(self):
        """Tests the letter grade assignment (transform.py)."""
        # First compute grades
        students = compute_final_grades(self.sample_students, self.weights)
        # Then assign letters
        students = assign_letter_grades(students, self.thresholds)
        
        # Check against typical thresholds (assuming standard A=93, B=83, D=60 in config)
        
        # 1. Alice (85.44) -> Should be B
        self.assertEqual(students[0]["letter_grade"], "B")
        
        # 2. Bob (61.81) -> Should be D
        self.assertEqual(students[1]["letter_grade"], "D")
        
        # 3. Charlie (61.75) -> Should be D
        self.assertEqual(students[2]["letter_grade"], "D")

    def test_next_student_id_generation(self):
        """Tests the auto-ID generation logic (main.py)."""
        # Current data has BSIT01, BSIT02, BSED01
        
        # Next ID for BSIT section
        next_bsit = _get_next_student_id(self.sample_students, "BSIT")
        self.assertEqual(next_bsit, "BSIT03")
        
        # Next ID for BSED section
        next_bsed = _get_next_student_id(self.sample_students, "BSED")
        self.assertEqual(next_bsed, "BSED02")
        
        # First ID for a new section (BSTM)
        next_bstm = _get_next_student_id(self.sample_students, "BSTM")
        self.assertEqual(next_bstm, "BSTM01")

        # Handles malformed section names (e.g., 'BS-IT')
        next_bs_it = _get_next_student_id(self.sample_students, "BS-IT")
        self.assertEqual(next_bs_it, "BSIT03") # Should still generate BSIT03

if __name__ == '__main__':
    print("--- Running Core Feature Tests ---")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    print("--- Core Feature Tests Complete ---")