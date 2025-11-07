import csv
from typing import List, Dict, Any, Optional, Tuple

# Define column types for validation
# student_id is treated as a special string
STRING_COLS = ['last_name', 'first_name', 'section']
NUMERIC_COLS = ['quiz1', 'quiz2', 'quiz3', 'quiz4', 'quiz5', 'midterm', 'final', 'attendance_percent']

def _parse_and_validate_row(row: Dict[str, str]) -> Dict[str, Any]:
    """
    Parses and validates a single row from the CSV.
    Applies rules from the case study:
    1. Trims spaces on string fields.
    2. Converts numeric fields, defaulting missing values to None.
    3. Validates scores are between 0 and 100.
    
    Raises:
        ValueError: If a row has missing required data (like ID) 
                    or invalid data (like out-of-range scores).
    """
    processed_row = {}
    
    # 1. Validate and process student_id (required)
    student_id = row.get('student_id', '').strip()
    if not student_id:
        raise ValueError("Missing or empty student_id")
    processed_row['student_id'] = student_id
    
    # 2. Process string columns (Rule: "Trim spaces")
    for col in STRING_COLS:
        value = row.get(col, '').strip()
        if not value:
            # We assume names and section are required for a valid record
            raise ValueError(f"Missing or empty required field: {col}")
        processed_row[col] = value
        
    # 3. Process numeric columns (Rules: "Missing -> None", "0-100 only")
    for col in NUMERIC_COLS:
        raw_value = row.get(col, '').strip()
        
        if raw_value == '':
            # Rule: "Missing numeric fields default to None"
            processed_row[col] = None
        else:
            try:
                # Use float for scores to allow for partial points
                score = float(raw_value)
            except ValueError:
                raise ValueError(f"Invalid non-numeric value '{raw_value}' for {col}")
                
            # Rule: "Scores are from 0 to 100 only"
            if not (0 <= score <= 100):
                raise ValueError(f"Score {score} for {col} is out of range (0-100)")
                
            processed_row[col] = score
            
    return processed_row

def ingest_student_data(filepath: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """
    Reads the student data CSV from the given filepath.
    
    Performs clean ingest:
    - Reads the CSV file.
    - Validates each row using _parse_and_validate_row.
    - Collects valid records and separates bad rows.
    
    Args:
        filepath: The path to the input CSV file.
        
    Returns:
        A tuple containing two lists:
        1. A list of valid student records (as dictionaries).
        2. A list of bad rows (raw strings, for reporting).
    """
    valid_records: List[Dict[str, Any]] = []
    bad_rows: List[Dict[str, str]] = []
    
    try:
        with open(filepath, mode='r', encoding='utf-8-sig') as file:
            # Use DictReader to read rows as dictionaries
            reader = csv.DictReader(file)
            
            for i, row in enumerate(reader):
                line_num = i + 2  # +1 for header, +1 for 0-indexing
                try:
                    # Apply all parsing and validation rules
                    processed_row = _parse_and_validate_row(row)
                    valid_records.append(processed_row)
                except ValueError as e:
                    # "handle bad rows" -> Log the error and save the bad row
                    print(f"[Warning] Skipping bad row #{line_num}: {e}. Data: {row}")
                    bad_rows.append(row)
                    
    except FileNotFoundError:
        print(f"[Error] File not found at path: {filepath}")
        return [], [] # Return empty lists
    except Exception as e:
        print(f"[Error] An unexpected error occurred: {e}")
        return [], [] # Return empty lists

    return valid_records, bad_rows

# --- Main execution block for testing ---
if __name__ == "__main__":
    """
    This block runs only when the script is executed directly.
    It's used for testing the ingest_student_data function.
    """
    
    # Use the provided CSV file name. 
    # Assumes it's in the same directory or a 'data/' subdirectory.
    # Update this path if your file is located elsewhere.
    csv_path = "DSA_Yagballs.csv" 
    
    print(f"Starting data ingestion from '{csv_path}'...")
    
    valid_data, skipped_data = ingest_student_data(csv_path)
    
    print("\n--- Ingestion Summary ---")
    print(f"Successfully ingested records: {len(valid_data)}")
    print(f"Skipped bad rows: {len(skipped_data)}")
    
    if valid_data:
        print("\n--- First 5 Valid Records (Sample) ---")
        for i, record in enumerate(valid_data[:5]):
            print(f"Record {i+1}: {record}")
            
    if skipped_data:
        print("\n--- Skipped Rows (Sample) ---")
        for i, row in enumerate(skipped_data[:5]):
            print(f"Skipped {i+1}: {row}")
            
    print("\nIngestion test complete.")