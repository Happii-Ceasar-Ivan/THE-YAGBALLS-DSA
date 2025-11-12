import unittest
import os
import sys
import json
import numpy as np
from typing import List, Dict, Any


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

#Import Core Project Modules (MUST be after the sys.path modification)
try:
    from transform import compute_final_grades, assign_letter_grades, apply_grade_curve
    from analyze import compute_stats, detect_outliers
    from main import _get_next_student_id, load_config
except ImportError as e:
    print(f"FATAL ERROR: Could not import core modules. Error: {e}")
   
    raise 


class TestCoreFunctions(unittest.TestCase):

    def setUp(self):
        """
        Setup sample data and load config before each test run.
        Includes a critical check to ensure grade thresholds are loaded.
        """
        
        # 1. Load Configuration
        self.config = load_config()
        self.weights = self.config.get("grading_weights", {})
        self.thresholds = self.config.get("grade_thresholds", {})
        
        # CRITICAL CHECK: Fail test setup immediately if essential configuration is missing.
        # This prevents the NoneType error in test_02.
        if not self.thresholds:
             raise RuntimeError(
                "TEST SETUP FAILURE: Grade thresholds failed to load from config.json. "
                "Ensure config.json is present in the project root and is correctly formatted."
            )

        # 2. Base Sample Data (Base Python list for deep copying)
        base_students = [
            {"student_id": "BSIT01", "last_name": "Smith", "first_name": "Alice", "section": "BSIT",
             "quiz1": 80, "quiz2": 85, "quiz3": 90, "quiz4": 75, "quiz5": 88, 
             "midterm": 82, "final": 90, "attendance_percent": 95.0, "final_grade": None, "letter_grade": None},
            {"student_id": "BSED01", "last_name": "Jones", "first_name": "Bob", "section": "BSED",
             "quiz1": 70, "quiz2": 65, "quiz3": None, "quiz4": 72, "quiz5": 50, 
             "midterm": 60, "final": 75, "attendance_percent": 70.5, "final_grade": None, "letter_grade": None},
            {"student_id": "BSIT02", "last_name": "Chen", "first_name": "Charlie", "section": "BSIT",
             "quiz1": 95, "quiz2": 92, "quiz3": 98, "quiz4": 100, "quiz5": 90, 
             "midterm": 95, "final": None, "attendance_percent": 98.0, "final_grade": None, "letter_grade": None}
        ]

        # Use json.loads(json.dumps()) for a reliable deep copy of the students list
        self.sample_students = json.loads(json.dumps(base_students))

        # Expected Values
        self.expected_grades = [85.44, 61.81, 61.75]
        self.expected_letters = ["B", "D", "D"]


    def test_01_grade_computation(self):
        """Verifies weighted final grades are calculated correctly, handling missing scores."""
        students = compute_final_grades(self.sample_students, self.weights)
        
        self.assertIsInstance(students, list, "compute_final_grades should return a list, not None.")
        self.assertAlmostEqual(students[0]["final_grade"], self.expected_grades[0], 2)
        self.assertAlmostEqual(students[1]["final_grade"], self.expected_grades[1], 2)
        self.assertAlmostEqual(students[2]["final_grade"], self.expected_grades[2], 2)

    def test_02_letter_grade_assignment(self):
        """
        Verifies letter grades are assigned according to config thresholds.
        Includes check that the function returns a list (the core fix).
        """
        # 1. Compute grades first (required input)
        students = compute_final_grades(self.sample_students, self.weights)
        
        # 2. Then assign letters.
        students = assign_letter_grades(students, self.thresholds)
        
        # Check that 'students' is indeed a list before subscripting
        # This assertion is the point of failure if assign_letter_grades returns None.
        self.assertIsInstance(students, list, "ASSERTION FAILED: assign_letter_grades returned None. Config issue likely.")
        
        # Final checks
        self.assertEqual(students[0]["letter_grade"], self.expected_letters[0])
        self.assertEqual(students[1]["letter_grade"], self.expected_letters[1])
        self.assertEqual(students[2]["letter_grade"], self.expected_letters[2])
        
    def test_03_next_student_id_generation(self):
        """Verifies ID generation correctly finds the next sequential number based on section prefix."""
        
        next_bsit = _get_next_student_id(self.sample_students, "BSIT")
        self.assertEqual(next_bsit, "BSIT03")
        
        next_bstm = _get_next_student_id(self.sample_students, "BSTM")
        self.assertEqual(next_bstm, "BSTM01")
        
    def test_04_grade_curve_application(self):
        """Tests the grade curve feature to ensure scores shift correctly to hit the target mean."""
        target_mean = 80.0
        
        # 1. Run core computation
        students = compute_final_grades(self.sample_students, self.weights)
        
        # Calculate initial mean
        current_grades = [s["final_grade"] for s in students]
        initial_mean = sum(current_grades) / len(current_grades)

        # 2. Apply the curve
        students = apply_grade_curve(students, target_mean)
        
        # 3. Check the new mean is close to the target
        new_grades = [s["final_grade"] for s in students]
        new_mean = sum(new_grades) / len(new_grades)
        
        self.assertAlmostEqual(new_mean, target_mean, 2, msg="Final mean after curve should match target mean.")
        
    def test_05_numpy_stats_implementation(self):
        """Tests the analyze.py (NumPy) functions for correct statistical results."""
        
        # Data intentionally designed to be easy to check: [10, 20, 30, 40, 50, 100]
        test_scores = [10.0, 20.0, 30.0, 40.0, 50.0, 100.0, None]
        
        stats = compute_stats(test_scores)
        
        # Expected values calculated manually for comparison:
        # Mean: 41.67, Median: 35.0
        
        self.assertEqual(stats["count"], 6)
        self.assertAlmostEqual(stats["mean"], 41.67, 2)
        self.assertAlmostEqual(stats["median"], 35.0, 2)
        
        # Test Outlier Detection
        outliers = detect_outliers(test_scores)
        self.assertEqual(len(outliers), 1)
        self.assertAlmostEqual(outliers[0], 100.0)


if __name__ == "__main__":
    print("\n--- Running Core Feature Tests ---")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    print("--- Core Feature Tests Complete ---")