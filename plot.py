import matplotlib.pyplot as plt
import os
from typing import List, Dict, Any
import math # Use math for standard Python list operations if preferred, but not strictly needed here

# Ensure ensure_dir is accessible, possibly by importing it from reports
# We assume ensure_dir is available globally in the project scope.
# If not, you must include it here:
# def ensure_dir(path: str) -> None:
#     os.makedirs(path, exist_ok=True)
from reports import ensure_dir

def generate_grade_histogram(students: List[Dict[str, Any]], output_folder: str, filename_base: str) -> str:
    """
    Generates and saves a histogram of final grades for the given student data.
    
    Args:
        students: List of student records.
        output_folder: Directory to save the PNG file.
        filename_base: Base name for the output PNG file.
        
    Returns:
        The path to the generated PNG file, or an empty string if no data.
    """
    
    # 1. Collect and filter valid final grades
    grades = [s["final_grade"] for s in students if s.get("final_grade") is not None]
    
    if not grades:
        return ""

    # 2. Create the figure
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Define bins: 0 to 100 in 5-point intervals
    bins = range(0, 101, 5) 
    
    ax.hist(grades, bins=bins, edgecolor='black', color='#4CAF50')
    
    # Set titles and labels
    ax.set_title(f"Grade Distribution Histogram: {filename_base.replace('.csv', '')}", fontsize=14)
    ax.set_xlabel('Final Grade Range (Bins)', fontsize=12)
    ax.set_ylabel('Number of Students (Frequency)', fontsize=12)
    ax.set_xticks(bins)
    ax.set_xlim(0, 100) # Ensure x-axis covers the standard 0-100 range
    
    # 3. Save the plot
    ensure_dir(output_folder)
    plot_path = os.path.join(output_folder, f"{filename_base.replace('.csv', '_HISTOGRAM.png')}")
    
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close(fig) # Close the figure to free memory
    
    return plot_path